"""LLM Explanation Engine: generates owner-friendly text using OpenAI,
with graceful fallback to simple templates when the API is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

RECOMMENDATION_PROMPT = """You are a restaurant growth advisor writing a short, friendly explanation
for a restaurant owner about a recommended strategy.

Only use the data provided. Do not invent metrics or strategies.

Strategy: {strategy_name}
Category: {category}
Description: {description}
Evidence: {evidence}
Expected KPI targets: {expected_kpi_targets}

Write 2-3 sentences explaining:
1. What the data shows
2. What the owner should do
3. What outcome to expect

Keep it conversational and actionable. Use specific numbers from the evidence."""

WEEKLY_SUMMARY_PROMPT = """You are a restaurant growth advisor preparing a concise weekly summary
for a restaurant owner.

Only use the data provided. Do not invent metrics or strategies.

Recommendations this week:
{recommendations_text}

Analytics highlights:
{analytics_text}

Write a brief weekly summary (4-6 sentences) covering:
1. Top opportunities identified
2. Key metrics to watch
3. Suggested priorities for the coming week

Be specific, data-driven, and encouraging."""

SOCIAL_CAPTION_PROMPT = """You are a social media copywriter for a restaurant.

Only use the data provided. Do not invent metrics or strategies.

Item: {item_name}
Item description: {item_description}
Price: ${price}
Strategy context: {strategy_context}

Write a short, engaging social media caption (1-2 sentences) that:
1. Highlights what makes this item special
2. Includes a call to action
3. Is suitable for Instagram or Facebook

Do NOT use hashtags. Keep it under 150 characters."""

ACTION_CHECKLIST_PROMPT = """You are a restaurant operations advisor creating a simple action checklist.

Only use the data provided. Do not invent metrics or strategies.

Recommendations:
{recommendations_text}

Create a numbered checklist of specific actions the restaurant owner should take this week.
Each action item should be:
- Concrete and specific
- Achievable within a week
- Tied to a recommendation above

Format as a numbered list. Keep each item to one sentence."""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class LLMExplanationEngine:
    """Generates natural-language explanations via OpenAI with template fallback."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._client = None

    @property
    def client(self):
        """Lazy-load the OpenAI client so import doesn't fail without the key."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI()
            except Exception:
                self._client = None
        return self._client

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def explain_recommendation(self, recommendation_data: dict[str, Any]) -> str:
        """Generate an owner-friendly explanation for a single recommendation."""
        prompt = RECOMMENDATION_PROMPT.format(
            strategy_name=recommendation_data.get("strategy_name", ""),
            category=recommendation_data.get("category", ""),
            description=recommendation_data.get("description", ""),
            evidence=json.dumps(recommendation_data.get("evidence", {}), default=str),
            expected_kpi_targets=json.dumps(
                recommendation_data.get("expected_kpi_targets", {}), default=str
            ),
        )

        try:
            return self._call_llm(prompt)
        except Exception as exc:
            logger.warning("LLM call failed for explain_recommendation: %s", exc)
            return self._format_recommendation_without_llm(recommendation_data)

    def generate_weekly_summary(
        self, recommendations: list[dict[str, Any]], analytics: dict[str, Any]
    ) -> str:
        """Generate a weekly report summarising recommendations and analytics."""
        rec_lines = []
        for i, rec in enumerate(recommendations, 1):
            rec_lines.append(
                f"{i}. {rec.get('strategy_name', 'Strategy')}: {rec.get('description', '')}"
            )
        recommendations_text = "\n".join(rec_lines) if rec_lines else "No new recommendations."

        analytics_text = json.dumps(analytics, indent=2, default=str)[:2000]

        prompt = WEEKLY_SUMMARY_PROMPT.format(
            recommendations_text=recommendations_text,
            analytics_text=analytics_text,
        )

        try:
            return self._call_llm(prompt)
        except Exception as exc:
            logger.warning("LLM call failed for generate_weekly_summary: %s", exc)
            return self._format_weekly_summary_without_llm(recommendations, analytics)

    def generate_social_caption(
        self, item_data: dict[str, Any], strategy_data: dict[str, Any]
    ) -> str:
        """Draft a social media caption for a menu item."""
        prompt = SOCIAL_CAPTION_PROMPT.format(
            item_name=item_data.get("name", ""),
            item_description=item_data.get("description", ""),
            price=item_data.get("price", ""),
            strategy_context=strategy_data.get("description", ""),
        )

        try:
            return self._call_llm(prompt)
        except Exception as exc:
            logger.warning("LLM call failed for generate_social_caption: %s", exc)
            return self._format_social_caption_without_llm(item_data)

    def generate_action_checklist(self, recommendations: list[dict[str, Any]]) -> str:
        """Generate a numbered checklist of actions from recommendations."""
        rec_lines = []
        for i, rec in enumerate(recommendations, 1):
            evidence_str = json.dumps(rec.get("evidence", {}), default=str)
            rec_lines.append(
                f"{i}. [{rec.get('category', 'general')}] "
                f"{rec.get('strategy_name', 'Strategy')}: {evidence_str}"
            )
        recommendations_text = "\n".join(rec_lines) if rec_lines else "No recommendations."

        prompt = ACTION_CHECKLIST_PROMPT.format(
            recommendations_text=recommendations_text,
        )

        try:
            return self._call_llm(prompt)
        except Exception as exc:
            logger.warning("LLM call failed for generate_action_checklist: %s", exc)
            return self._format_checklist_without_llm(recommendations)

    # ------------------------------------------------------------------
    # LLM call helper
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str) -> str:
        """Send a prompt to OpenAI and return the response text."""
        if self.client is None:
            raise RuntimeError("OpenAI client is not available")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()

    # ------------------------------------------------------------------
    # Fallback template formatters
    # ------------------------------------------------------------------

    @staticmethod
    def _format_without_llm(data: dict[str, Any]) -> str:
        """Generic fallback: return a simple key-value summary."""
        lines = []
        for key, value in data.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "No data available."

    @staticmethod
    def _format_recommendation_without_llm(data: dict[str, Any]) -> str:
        """Fallback explanation for a single recommendation."""
        name = data.get("strategy_name", "this strategy")
        desc = data.get("description", "")
        evidence = data.get("evidence", {})
        targets = data.get("expected_kpi_targets", {})

        evidence_parts = []
        for k, v in evidence.items():
            evidence_parts.append(f"{k.replace('_', ' ')}: {v}")
        evidence_text = ", ".join(evidence_parts) if evidence_parts else "N/A"

        target_parts = []
        for k, v in targets.items():
            target_parts.append(f"{k.replace('_', ' ')}: {v}%")
        target_text = ", ".join(target_parts) if target_parts else "positive impact"

        return (
            f"Recommendation: {name}\n"
            f"{desc}\n\n"
            f"Based on: {evidence_text}\n"
            f"Expected outcome: {target_text}"
        )

    @staticmethod
    def _format_weekly_summary_without_llm(
        recommendations: list[dict[str, Any]], analytics: dict[str, Any]
    ) -> str:
        """Fallback weekly summary."""
        lines = ["Weekly Growth Summary", "=" * 40, ""]
        if recommendations:
            lines.append(f"This week we identified {len(recommendations)} opportunity(ies):")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"  {i}. {rec.get('strategy_name', 'Strategy')}")
            lines.append("")
        else:
            lines.append("No new recommendations this week.")
            lines.append("")

        menu_count = len(analytics.get("menu_items", []))
        alerts = len(analytics.get("inventory_alerts", []))
        lines.append(f"Menu items tracked: {menu_count}")
        if alerts:
            lines.append(f"Inventory alerts: {alerts} ingredient(s) near stockout")

        return "\n".join(lines)

    @staticmethod
    def _format_social_caption_without_llm(item_data: dict[str, Any]) -> str:
        """Fallback social media caption."""
        name = item_data.get("name", "our special")
        price = item_data.get("price", "")
        price_text = f" for just ${price}" if price else ""
        return f"Try our {name}{price_text}! Come visit us today."

    @staticmethod
    def _format_checklist_without_llm(recommendations: list[dict[str, Any]]) -> str:
        """Fallback action checklist."""
        if not recommendations:
            return "No action items this week."
        lines = ["Action Checklist", "-" * 30]
        for i, rec in enumerate(recommendations, 1):
            name = rec.get("strategy_name", "Action")
            category = rec.get("category", "general")
            lines.append(f"{i}. [{category}] {name}")
        return "\n".join(lines)
