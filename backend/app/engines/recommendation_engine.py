"""Recommendation Engine: gathers restaurant analytics, sends data + strategy
guidelines to GPT-4o, and persists the LLM-generated recommendations.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.engines.strategy_history_engine import StrategyHistoryEngine
from app.engines.strategy_playbook import get_playbook
from app.models.inventory_item import InventoryItem
from app.models.menu_item import MenuItem
from app.models.recommendation import Recommendation, RecommendationStatus
from app.models.recipe_mapping import RecipeMapping
from app.models.sales_record import SalesRecord
from app.models.social_post import SocialPost
from app.models.strategy import StrategyDefinition

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are BistroBrain, a restaurant growth advisor AI. You analyze restaurant data and generate
actionable, localized recommendations for the owner.

You MUST follow these rules:
1. Only recommend strategies from the provided strategy playbook — do not invent new strategy types.
2. Only reference data that is explicitly provided — never fabricate numbers or metrics.
3. Each recommendation must cite specific evidence from the data.
4. Be practical and specific — tell the owner exactly what to do.
5. Prioritize high-impact, time-sensitive actions (e.g., stockouts, expiring inventory, weather, local events) first.
6. Do NOT recommend strategies that are in the blocked list.
7. EVERY recommendation must be UNIQUE — do not repeat the same strategy code with the same item. Each recommendation should address a different opportunity.
8. Factor in the local context (weather, nearby events, location demographics) when making recommendations.
9. Do NOT fabricate percentages, confidence scores, or estimated impact numbers. Only cite real data.

Respond ONLY with a valid JSON array. Each element must have these exact fields:
{
  "strategy_code": "<code from playbook>",
  "title": "<short action title>",
  "description": "<2-3 sentence explanation of what to do and why, citing specific numbers>",
  "evidence": {<key data points that support this recommendation>},
  "urgency": "<low|medium|high|critical>",
  "menu_item_name": "<item name if applicable, else null>"
}

Return 8-12 diverse recommendations covering different strategy categories, ordered by urgency. Return ONLY the JSON array, no markdown."""


class RecommendationEngine:
    """Generates recommendations by sending restaurant data to GPT-4o."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                from app.core.config import settings
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.error("Failed to create OpenAI client: %s", e)
                self._client = None
        return self._client

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate_recommendations(
        self, db: Session, restaurant_id: int
    ) -> list[Recommendation]:
        """Run the full LLM-powered recommendation pipeline."""
        analytics = self._gather_analytics(db, restaurant_id)
        blocked_codes = StrategyHistoryEngine.get_blocked_strategy_codes(
            db, restaurant_id
        )

        # Build strategy definition lookup
        sd_map: dict[str, StrategyDefinition] = {
            sd.code: sd
            for sd in db.query(StrategyDefinition)
            .filter(StrategyDefinition.is_active.is_(True))
            .all()
        }

        # Build the user prompt with all data
        user_prompt = self._build_prompt(analytics, blocked_codes)

        # Call GPT-4o
        raw_recommendations = self._call_llm(user_prompt)

        if not raw_recommendations:
            logger.warning("LLM returned no recommendations, falling back to rule-based")
            return self._fallback_rule_based(db, restaurant_id, analytics, blocked_codes, sd_map)

        # Clear old pending recommendations before generating new ones
        db.query(Recommendation).filter(
            Recommendation.restaurant_id == restaurant_id,
            Recommendation.status == RecommendationStatus.pending,
        ).delete()
        db.flush()

        # Parse and persist
        menu_item_map = {
            mi.name.lower(): mi
            for mi in db.query(MenuItem)
            .filter(MenuItem.restaurant_id == restaurant_id)
            .all()
        }

        recommendations: list[Recommendation] = []
        seen_keys: set[str] = set()  # Dedup by (strategy_code, menu_item_name)

        for rec_data in raw_recommendations[:12]:
            code = rec_data.get("strategy_code", "")
            sd = sd_map.get(code)
            if sd is None:
                continue

            if code in blocked_codes:
                continue

            # Dedup: same strategy + same item = duplicate
            mi_name = rec_data.get("menu_item_name")
            dedup_key = f"{code}:{(mi_name or '').lower()}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            # Resolve menu item if referenced
            menu_item_id = None
            if mi_name and mi_name.lower() in menu_item_map:
                menu_item_id = menu_item_map[mi_name.lower()].id

            rec = Recommendation(
                restaurant_id=restaurant_id,
                strategy_definition_id=sd.id,
                menu_item_id=menu_item_id,
                title=rec_data.get("title", sd.name),
                evidence=rec_data.get("evidence", {}),
                confidence=None,
                urgency=rec_data.get("urgency", "medium"),
                expected_impact=None,
                explanation_text=rec_data.get("description", ""),
                status=RecommendationStatus.pending,
            )
            db.add(rec)
            recommendations.append(rec)

        if recommendations:
            db.commit()
            for rec in recommendations:
                db.refresh(rec)

        return recommendations

    # ------------------------------------------------------------------
    # LLM interaction
    # ------------------------------------------------------------------

    def _build_prompt(
        self, analytics: dict[str, Any], blocked_codes: set[str]
    ) -> str:
        """Build the data prompt for GPT-4o."""

        # Summarize playbook strategies
        playbook_summary = []
        for s in get_playbook():
            playbook_summary.append({
                "code": s["code"],
                "name": s["name"],
                "category": s["category"],
                "description": s["description"],
                "expected_kpi_targets": s.get("expected_kpi_targets", {}),
            })

        # Summarize menu data (top 20 items by sales)
        menu_items = sorted(
            analytics.get("menu_items", []),
            key=lambda x: x.get("monthly_orders", 0),
            reverse=True,
        )[:20]
        menu_summary = []
        for mi in menu_items:
            menu_summary.append({
                "name": mi["name"],
                "category": mi.get("category"),
                "price": mi["price"],
                "cost": mi.get("ingredient_cost", 0),
                "margin_pct": round(mi.get("margin_pct", 0) * 100, 1),
                "monthly_orders": mi.get("monthly_orders", 0),
                "weekly_orders": mi.get("weekly_orders", 0),
                "popularity_score": round(mi.get("popularity_score", 0), 3),
            })

        # Pair associations (top 10)
        pairs = analytics.get("pair_associations", [])[:10]
        pair_summary = [
            {
                "items": f"{p['item_a']} + {p['item_b']}",
                "frequency": p["frequency"],
            }
            for p in pairs
        ]

        # Inventory alerts
        inv_alerts = analytics.get("inventory_alerts", [])
        overstock = analytics.get("overstock_items", [])
        expiry = analytics.get("expiry_alerts", [])
        ingredient_costs = analytics.get("ingredient_costs", [])

        # Social data
        social = analytics.get("social_timing", {})

        # Category stats
        cat_stats = analytics.get("category_stats", {})

        # Local context (hardcoded for now — can be replaced with real weather/events API later)
        local_context = analytics.get("local_context", {
            "weather": "rainy, cool evening expected",
            "nearby_events": "HackUTD hackathon happening nearby — large student crowd expected",
            "location": "Richardson, TX",
            "demographics": "Mix of college students, young professionals, and suburban families",
            "time_of_day": "evening",
            "day_of_week": datetime.now().strftime("%A"),
        })

        prompt = f"""## Restaurant Data Analysis

### Local Context (IMPORTANT — factor this into recommendations)
- Weather: {local_context.get("weather", "unknown")}
- Nearby Events: {local_context.get("nearby_events", "none")}
- Location: {local_context.get("location", "unknown")}
- Demographics: {local_context.get("demographics", "general")}
- Current Day: {local_context.get("day_of_week", "unknown")}

### Menu Items (top 20 by sales)
{json.dumps(menu_summary, indent=2)}

### Frequently Paired Items
{json.dumps(pair_summary, indent=2)}

### Category Statistics
{json.dumps(cat_stats, indent=2, default=str)}

### Inventory — Stockout Risks (≤3 days of stock)
{json.dumps(inv_alerts, indent=2, default=str)}

### Inventory — Expiring Soon (≤5 days)
{json.dumps(expiry, indent=2, default=str)}

### Inventory — Overstocked
{json.dumps(overstock, indent=2, default=str)}

### Inventory — High-Cost Ingredients
{json.dumps(ingredient_costs, indent=2, default=str)}

### Social Media Performance
{json.dumps(social, indent=2, default=str)}

### Past Successful Strategies
{json.dumps(analytics.get("successful_strategies", []), indent=2, default=str)}

---

### Strategy Playbook (ONLY use these strategy codes)
{json.dumps(playbook_summary, indent=2)}

### Blocked Strategies (DO NOT recommend these)
{json.dumps(list(blocked_codes))}

---

Generate 8-12 diverse, actionable recommendations using ONLY the strategies from the playbook above.
IMPORTANT:
- Each recommendation must target a DIFFERENT opportunity. Do not repeat the same strategy for the same item.
- Include at least 2 recommendations driven by local context (weather, events, demographics).
- Cover multiple categories: menu, inventory, marketing, operations, pricing.
Return a JSON array."""

        return prompt

    def _call_llm(self, user_prompt: str) -> list[dict[str, Any]] | None:
        """Call GPT-4o and parse the JSON response."""
        if self.client is None:
            logger.error("OpenAI client not available")
            return None

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=4096,
            )
            content = response.choices[0].message.content.strip()

            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            result = json.loads(content)
            if isinstance(result, list):
                return result
            logger.warning("LLM returned non-list JSON: %s", type(result))
            return None
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response: %s", e)
            logger.debug("Raw response: %s", content if 'content' in dir() else "N/A")
            return None
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            return None

    # ------------------------------------------------------------------
    # Fallback: simple rule-based (if LLM fails)
    # ------------------------------------------------------------------

    def _fallback_rule_based(
        self,
        db: Session,
        restaurant_id: int,
        analytics: dict[str, Any],
        blocked_codes: set[str],
        sd_map: dict[str, StrategyDefinition],
    ) -> list[Recommendation]:
        """Simple fallback that creates recommendations from obvious signals."""
        recommendations: list[Recommendation] = []

        # Stockout alerts → REORDER_ALERT
        if "REORDER_ALERT" not in blocked_codes and "REORDER_ALERT" in sd_map:
            for alert in analytics.get("inventory_alerts", [])[:3]:
                rec = Recommendation(
                    restaurant_id=restaurant_id,
                    strategy_definition_id=sd_map["REORDER_ALERT"].id,
                    title=f"Reorder {alert['ingredient_name']} — {alert['days_of_stock_remaining']} days left",
                    evidence=alert,
                    confidence=None,
                    urgency="critical" if alert["days_of_stock_remaining"] <= 1 else "high",
                    expected_impact=None,
                    explanation_text=f"{alert['ingredient_name']} has only {alert['days_of_stock_remaining']} days of stock remaining. Reorder immediately to avoid running out.",
                    status=RecommendationStatus.pending,
                )
                db.add(rec)
                recommendations.append(rec)

        # Expiry alerts → REDUCE_WASTE
        if "REDUCE_WASTE" not in blocked_codes and "REDUCE_WASTE" in sd_map:
            for alert in analytics.get("expiry_alerts", [])[:2]:
                rec = Recommendation(
                    restaurant_id=restaurant_id,
                    strategy_definition_id=sd_map["REDUCE_WASTE"].id,
                    title=f"Use up {alert['ingredient_name']} before it expires",
                    evidence=alert,
                    confidence=None,
                    urgency="high",
                    expected_impact=None,
                    explanation_text=f"{alert['ingredient_name']} expires on {alert.get('expiry_date', 'soon')}. Create a daily special to use it up.",
                    status=RecommendationStatus.pending,
                )
                db.add(rec)
                recommendations.append(rec)

        if recommendations:
            db.commit()
            for rec in recommendations:
                db.refresh(rec)

        return recommendations

    # ------------------------------------------------------------------
    # Analytics gathering
    # ------------------------------------------------------------------

    def _gather_analytics(self, db: Session, restaurant_id: int) -> dict[str, Any]:
        """Aggregate data from menu, inventory, sales, and social tables."""
        analytics: dict[str, Any] = {}

        # ── Menu items with popularity & margin ──────────────────────
        menu_items_raw = (
            db.query(MenuItem)
            .filter(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_active.is_(True),
            )
            .all()
        )

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        sales_totals = dict(
            db.query(SalesRecord.menu_item_id, func.sum(SalesRecord.quantity))
            .filter(
                SalesRecord.restaurant_id == restaurant_id,
                SalesRecord.sale_date >= thirty_days_ago,
            )
            .group_by(SalesRecord.menu_item_id)
            .all()
        )

        weekly_sales = dict(
            db.query(SalesRecord.menu_item_id, func.sum(SalesRecord.quantity))
            .filter(
                SalesRecord.restaurant_id == restaurant_id,
                SalesRecord.sale_date >= seven_days_ago,
            )
            .group_by(SalesRecord.menu_item_id)
            .all()
        )

        max_sales = max(sales_totals.values(), default=1) or 1

        social_counts = dict(
            db.query(SocialPost.menu_item_id, func.count(SocialPost.id))
            .filter(
                SocialPost.restaurant_id == restaurant_id,
                SocialPost.menu_item_id.isnot(None),
                SocialPost.posted_at >= thirty_days_ago,
            )
            .group_by(SocialPost.menu_item_id)
            .all()
        )

        menu_items: list[dict[str, Any]] = []
        categories_set: set[str] = set()
        category_items: dict[str, list[dict]] = {}

        for mi in menu_items_raw:
            total_qty = sales_totals.get(mi.id, 0) or 0
            weekly_qty = weekly_sales.get(mi.id, 0) or 0
            popularity = total_qty / max_sales if max_sales else 0
            cost = float(mi.ingredient_cost) if mi.ingredient_cost else 0
            price = float(mi.price)
            margin_pct = (price - cost) / price if price > 0 else 0

            item_data = {
                "id": mi.id,
                "name": mi.name,
                "category": mi.category,
                "price": price,
                "ingredient_cost": cost,
                "margin_pct": margin_pct,
                "popularity_score": popularity,
                "weekly_orders": int(weekly_qty),
                "monthly_orders": int(total_qty),
                "recent_social_posts": social_counts.get(mi.id, 0),
            }
            menu_items.append(item_data)

            if mi.category:
                categories_set.add(mi.category)
                category_items.setdefault(mi.category, []).append(item_data)

        analytics["menu_items"] = menu_items
        analytics["menu_categories"] = sorted(categories_set)

        # Category stats
        cat_stats: dict[str, dict] = {}
        for cat, items in category_items.items():
            pops = [i["popularity_score"] for i in items]
            cat_stats[cat] = {
                "item_count": len(items),
                "avg_popularity": round(sum(pops) / len(pops), 3) if pops else 0,
                "total_monthly_orders": sum(i["monthly_orders"] for i in items),
            }
        analytics["category_stats"] = cat_stats

        # ── Pair associations ─────────────────────────────────────────
        pair_associations: list[dict] = []
        order_items: dict[str, list[int]] = {}
        sales_rows = (
            db.query(SalesRecord.order_id, SalesRecord.menu_item_id)
            .filter(
                SalesRecord.restaurant_id == restaurant_id,
                SalesRecord.sale_date >= thirty_days_ago,
                SalesRecord.order_id.isnot(None),
            )
            .all()
        )
        for order_id, item_id in sales_rows:
            order_items.setdefault(order_id, []).append(item_id)

        pair_counts: dict[tuple[int, int], int] = {}
        item_name_map = {mi.id: mi.name for mi in menu_items_raw}
        item_price_map = {mi.id: float(mi.price) for mi in menu_items_raw}
        for items_in_order in order_items.values():
            unique = sorted(set(items_in_order))
            for i in range(len(unique)):
                for j in range(i + 1, len(unique)):
                    key = (unique[i], unique[j])
                    pair_counts[key] = pair_counts.get(key, 0) + 1

        total_orders = len(order_items) or 1
        for (a, b), freq in sorted(pair_counts.items(), key=lambda x: -x[1])[:20]:
            pair_associations.append({
                "item_a": item_name_map.get(a, str(a)),
                "item_b": item_name_map.get(b, str(b)),
                "frequency": freq,
                "confidence": round(freq / total_orders, 3),
                "suggested_bundle_price": round(
                    (item_price_map.get(a, 0) + item_price_map.get(b, 0)) * 0.9, 2
                ),
            })
        analytics["pair_associations"] = pair_associations

        # ── Inventory ─────────────────────────────────────────────────
        inventory_rows = (
            db.query(InventoryItem)
            .filter(InventoryItem.restaurant_id == restaurant_id)
            .all()
        )

        daily_usage: dict[str, float] = {}
        recipe_rows = (
            db.query(RecipeMapping)
            .join(MenuItem, RecipeMapping.menu_item_id == MenuItem.id)
            .filter(MenuItem.restaurant_id == restaurant_id)
            .all()
        )
        for rm in recipe_rows:
            daily_qty = (sales_totals.get(rm.menu_item_id, 0) or 0) / 30.0
            daily_usage[rm.ingredient_name] = daily_usage.get(rm.ingredient_name, 0) + (
                daily_qty * float(rm.quantity_needed)
            )

        inventory_alerts: list[dict] = []
        overstock_items: list[dict] = []
        expiry_alerts: list[dict] = []
        high_usage_ingredients: list[dict] = []
        ingredient_costs: list[dict] = []

        total_ingredient_cost = sum(
            float(inv.unit_cost or 0) * float(inv.quantity_on_hand)
            for inv in inventory_rows
        ) or 1.0

        for inv in inventory_rows:
            qty = float(inv.quantity_on_hand)
            usage = daily_usage.get(inv.ingredient_name, 0)
            days_remaining = qty / usage if usage > 0 else 999
            weekly_usage = usage * 7

            inv_data = {
                "ingredient_name": inv.ingredient_name,
                "quantity_on_hand": qty,
                "unit": inv.unit,
                "reorder_threshold": float(inv.reorder_threshold) if inv.reorder_threshold else None,
                "days_of_stock_remaining": round(days_remaining, 1),
                "weekly_usage": round(weekly_usage, 2),
                "unit_cost": float(inv.unit_cost) if inv.unit_cost else 0,
            }

            if days_remaining <= 3:
                inventory_alerts.append(inv_data)

            if weekly_usage > 0 and qty / weekly_usage >= 2.0:
                inv_data["overstock_ratio"] = round(qty / weekly_usage, 2)
                overstock_items.append(inv_data)

            if inv.expiry_date:
                from datetime import date
                days_to_expiry = (inv.expiry_date - date.today()).days
                if days_to_expiry <= 5:
                    inv_data["days_to_expiry"] = days_to_expiry
                    inv_data["expiry_date"] = str(inv.expiry_date)
                    expiry_alerts.append(inv_data)

            if weekly_usage >= 50:
                high_usage_ingredients.append(inv_data)

            cost_val = float(inv.unit_cost or 0) * qty
            if cost_val / total_ingredient_cost >= 0.15:
                ingredient_costs.append({
                    "name": inv.ingredient_name,
                    "unit_cost": float(inv.unit_cost or 0),
                    "cost_share_pct": round(cost_val / total_ingredient_cost, 3),
                })

        analytics["inventory_alerts"] = inventory_alerts
        analytics["overstock_items"] = overstock_items
        analytics["expiry_alerts"] = expiry_alerts
        analytics["high_usage_ingredients"] = high_usage_ingredients
        analytics["ingredient_costs"] = ingredient_costs

        # ── Social timing ────────────────────────────────────────────
        social_posts = (
            db.query(SocialPost)
            .filter(SocialPost.restaurant_id == restaurant_id)
            .all()
        )
        total_posts = len(social_posts)
        if total_posts > 0:
            engagement_by_day_hour: dict[tuple, list[int]] = {}
            total_engagement = 0
            for sp in social_posts:
                eng = (sp.likes or 0) + (sp.comments or 0) + (sp.shares or 0)
                total_engagement += eng
                if sp.posted_at:
                    key = (sp.posted_at.strftime("%A"), sp.posted_at.hour)
                    engagement_by_day_hour.setdefault(key, []).append(eng)

            best_key = max(
                engagement_by_day_hour,
                key=lambda k: sum(engagement_by_day_hour[k]) / len(engagement_by_day_hour[k]),
                default=("Saturday", 12),
            )
            best_eng = engagement_by_day_hour.get(best_key, [0])
            analytics["social_timing"] = {
                "total_posts": total_posts,
                "best_day": best_key[0] if isinstance(best_key, tuple) else "Saturday",
                "best_hour": best_key[1] if isinstance(best_key, tuple) else 12,
                "best_engagement": round(sum(best_eng) / len(best_eng), 2) if best_eng else 0,
                "avg_engagement": round(total_engagement / total_posts, 2),
            }
        else:
            analytics["social_timing"] = {"total_posts": 0}

        # ── Successful past strategies ────────────────────────────────
        successes = StrategyHistoryEngine.get_successful_strategies(db, restaurant_id)
        analytics["successful_strategies"] = [
            {
                "code": sh.strategy_definition.code if sh.strategy_definition else "unknown",
                "actual_impact": sh.actual_impact,
            }
            for sh in successes
        ]

        return analytics
