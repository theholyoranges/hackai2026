"""Chat service -- AI-powered conversational copilot grounded in restaurant data."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.engines.menu_analytics import MenuAnalyticsEngine
from app.models.inventory_item import InventoryItem
from app.models.recommendation import Recommendation, RecommendationStatus
from app.models.restaurant import Restaurant
from app.models.social_post import SocialPost
from app.models.strategy import StrategyHistory, StrategyStatus


def _gather_context(db: Session, restaurant_id: int) -> dict[str, Any]:
    """Collect analytics, strategy history, and recommendations into a context dict."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    # Menu analytics
    menu_data = MenuAnalyticsEngine.get_full_analysis(db, restaurant_id)

    # Inventory snapshot
    inventory = db.query(InventoryItem).filter(InventoryItem.restaurant_id == restaurant_id).all()
    low_stock = [
        {"ingredient": i.ingredient_name, "qty": float(i.quantity_on_hand), "threshold": float(i.reorder_threshold) if i.reorder_threshold else None}
        for i in inventory
        if i.reorder_threshold and float(i.quantity_on_hand) <= float(i.reorder_threshold)
    ]

    # Social summary
    posts = db.query(SocialPost).filter(SocialPost.restaurant_id == restaurant_id).all()
    total_engagement = sum((p.likes or 0) + (p.comments or 0) + (p.shares or 0) for p in posts)
    social_summary = {
        "total_posts": len(posts),
        "total_engagement": total_engagement,
        "avg_engagement": round(total_engagement / len(posts), 1) if posts else 0,
    }

    # Strategy history
    active_statuses = [StrategyStatus.accepted, StrategyStatus.active, StrategyStatus.evaluating]
    active_strategies = (
        db.query(StrategyHistory)
        .filter(
            StrategyHistory.restaurant_id == restaurant_id,
            StrategyHistory.status.in_(active_statuses),
        )
        .all()
    )
    strategy_entries = [
        {"id": s.id, "status": s.status.value, "expected_impact": s.expected_impact, "notes": s.notes}
        for s in active_strategies
    ]

    # Pending recommendations
    pending_recs = (
        db.query(Recommendation)
        .filter(
            Recommendation.restaurant_id == restaurant_id,
            Recommendation.status == RecommendationStatus.pending,
        )
        .all()
    )
    rec_entries = [
        {"id": r.id, "title": r.title, "urgency": r.urgency, "expected_impact": r.expected_impact}
        for r in pending_recs
    ]

    return {
        "restaurant_name": restaurant.name if restaurant else "Unknown",
        "cuisine_type": restaurant.cuisine_type if restaurant else None,
        "top_sellers": menu_data.get("top_sellers", [])[:5],
        "bottom_sellers": menu_data.get("bottom_sellers", [])[:5],
        "margin_analysis": menu_data.get("margin_analysis", [])[:10],
        "menu_engineering": menu_data.get("menu_engineering", [])[:10],
        "low_stock_items": low_stock,
        "social_summary": social_summary,
        "active_strategies": strategy_entries,
        "pending_recommendations": rec_entries,
    }


def _build_system_prompt(context: dict[str, Any]) -> str:
    """Build the system prompt with restaurant context."""
    return f"""You are the Restaurant Growth Copilot, an AI assistant helping restaurant owners
make data-driven decisions to grow their business. You have access to the following real-time
data for {context['restaurant_name']} ({context.get('cuisine_type', 'restaurant')}):

TOP SELLERS: {json.dumps(context['top_sellers'], default=str)}

BOTTOM SELLERS: {json.dumps(context['bottom_sellers'], default=str)}

MARGIN ANALYSIS (top items): {json.dumps(context['margin_analysis'][:5], default=str)}

MENU ENGINEERING CLASSIFICATION: {json.dumps(context['menu_engineering'][:5], default=str)}

LOW STOCK ALERTS: {json.dumps(context['low_stock_items'], default=str)}

SOCIAL MEDIA SUMMARY: {json.dumps(context['social_summary'], default=str)}

ACTIVE STRATEGIES: {json.dumps(context['active_strategies'], default=str)}

PENDING RECOMMENDATIONS: {json.dumps(context['pending_recommendations'], default=str)}

INSTRUCTIONS:
- Answer concisely and ground every claim in the data above.
- When suggesting actions, reference specific menu items, numbers, or metrics.
- If the user asks about something not in the data, say so honestly.
- Use a friendly, professional tone appropriate for a restaurant owner.
- When relevant, reference the pending recommendations or active strategies.
"""


def _call_openai(system_prompt: str, user_message: str) -> str | None:
    """Attempt to call the OpenAI API. Returns None on failure."""
    try:
        from openai import OpenAI

        from app.core.config import settings

        if not settings.OPENAI_API_KEY:
            return None

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception:
        return None


def _fallback_response(context: dict[str, Any], message: str) -> str:
    """Generate a structured fallback response when OpenAI is unavailable."""
    msg_lower = message.lower()
    lines = [f"Here's what I can share about {context['restaurant_name']}:\n"]

    if any(kw in msg_lower for kw in ("top", "best", "popular", "seller")):
        if context["top_sellers"]:
            lines.append("**Top Sellers:**")
            for item in context["top_sellers"][:3]:
                lines.append(f"  - {item['item']}: {item['qty_sold']} sold, ${item['revenue']:.2f} revenue")
        else:
            lines.append("No sales data available yet.")

    elif any(kw in msg_lower for kw in ("worst", "bottom", "underperform", "low")):
        if context["bottom_sellers"]:
            lines.append("**Underperformers:**")
            for item in context["bottom_sellers"][:3]:
                lines.append(f"  - {item['item']}: {item['qty_sold']} sold, ${item['revenue']:.2f} revenue")

    elif any(kw in msg_lower for kw in ("margin", "profit", "cost")):
        if context["margin_analysis"]:
            lines.append("**Margin Analysis:**")
            for item in context["margin_analysis"][:5]:
                lines.append(f"  - {item['item']}: {item['margin_pct']}% margin (${item['margin']:.2f})")

    elif any(kw in msg_lower for kw in ("inventory", "stock", "reorder")):
        if context["low_stock_items"]:
            lines.append("**Low Stock Alerts:**")
            for item in context["low_stock_items"]:
                lines.append(f"  - {item['ingredient']}: {item['qty']} on hand (threshold: {item['threshold']})")
        else:
            lines.append("All inventory levels are above reorder thresholds.")

    elif any(kw in msg_lower for kw in ("social", "engagement", "post")):
        s = context["social_summary"]
        lines.append(f"**Social Media:** {s['total_posts']} posts, {s['total_engagement']} total engagement, {s['avg_engagement']} avg per post")

    elif any(kw in msg_lower for kw in ("recommend", "suggestion", "action", "strategy")):
        if context["pending_recommendations"]:
            lines.append("**Pending Recommendations:**")
            for rec in context["pending_recommendations"]:
                lines.append(f"  - [{rec['urgency']}] {rec['title']}")
        if context["active_strategies"]:
            lines.append("\n**Active Strategies:**")
            for s in context["active_strategies"]:
                lines.append(f"  - {s['status']}: {s.get('expected_impact', 'N/A')}")

    else:
        # General overview
        if context["top_sellers"]:
            top = context["top_sellers"][0]
            lines.append(f"Your top seller is **{top['item']}** with {top['qty_sold']} units sold.")
        if context["low_stock_items"]:
            lines.append(f"You have **{len(context['low_stock_items'])}** items below reorder threshold.")
        if context["pending_recommendations"]:
            lines.append(f"There are **{len(context['pending_recommendations'])}** pending recommendations to review.")
        lines.append("\nAsk me about top sellers, margins, inventory, social media, or recommendations!")

    return "\n".join(lines)


def process_chat(db: Session, restaurant_id: int, message: str) -> str:
    """Process a chat message and return an AI response grounded in analytics data.

    Tries OpenAI first, falls back to a structured response if unavailable.
    """
    context = _gather_context(db, restaurant_id)
    system_prompt = _build_system_prompt(context)

    # Try OpenAI
    ai_response = _call_openai(system_prompt, message)
    if ai_response:
        return ai_response

    # Fallback
    return _fallback_response(context, message)
