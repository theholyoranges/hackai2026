"""Strategy Playbook: master list of all reusable strategy templates.

Each strategy defines applicability rules, cooldown, confidence thresholds,
and expected KPI targets so the recommendation engine can match them
against live analytics.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.strategy import StrategyDefinition

# ---------------------------------------------------------------------------
# Playbook data
# ---------------------------------------------------------------------------

STRATEGY_PLAYBOOK: list[dict[str, Any]] = [
    # ── pricing ──────────────────────────────────────────────────────────
    {
        "code": "PRICE_INCREASE_HIGH_DEMAND",
        "name": "Increase price on high-demand items",
        "category": "pricing",
        "description": "Raise price 5-15% on items with high popularity and strong demand",
        "applicability_rules": {"min_popularity_score": 0.7, "min_margin_pct": 0.3},
        "blocked_conditions": {"max_recent_price_changes": 2},
        "expected_evidence_fields": [
            "item_name",
            "current_price",
            "suggested_price",
            "popularity_score",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.6,
        "expected_kpi_targets": {"revenue_increase_pct": 5},
    },
    {
        "code": "PRICE_DECREASE_LOW_DEMAND",
        "name": "Decrease price on low-demand items",
        "category": "pricing",
        "description": "Lower price 5-10% on underperforming items to stimulate demand",
        "applicability_rules": {"max_popularity_score": 0.3, "min_margin_pct": 0.4},
        "blocked_conditions": {"max_recent_price_changes": 2},
        "expected_evidence_fields": [
            "item_name",
            "current_price",
            "suggested_price",
            "popularity_score",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"order_volume_increase_pct": 10},
    },
    # ── bundling ─────────────────────────────────────────────────────────
    {
        "code": "BUNDLE_COMPLEMENTARY",
        "name": "Bundle complementary items together",
        "category": "bundling",
        "description": "Create a combo from items frequently purchased together at a small discount",
        "applicability_rules": {"min_pair_frequency": 5, "min_pair_confidence": 0.3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_a_name",
            "item_b_name",
            "pair_frequency",
            "suggested_bundle_price",
        ],
        "cooldown_days": 21,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"avg_order_value_increase_pct": 8},
    },
    {
        "code": "BUNDLE_MEAL_DEAL",
        "name": "Create meal deal bundle",
        "category": "bundling",
        "description": "Offer a starter + main + drink combo at a bundled price to increase AOV",
        "applicability_rules": {"min_categories_available": 3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "items",
            "individual_total",
            "bundle_price",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"avg_order_value_increase_pct": 12},
    },
    # ── upsell ───────────────────────────────────────────────────────────
    {
        "code": "UPSELL_PREMIUM_VARIANT",
        "name": "Upsell to premium variant",
        "category": "upsell",
        "description": "Suggest a higher-margin premium version of popular items",
        "applicability_rules": {"min_popularity_score": 0.6, "min_margin_gap": 0.15},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "base_item_name",
            "premium_item_name",
            "margin_difference",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"revenue_increase_pct": 6},
    },
    # ── menu_simplification ──────────────────────────────────────────────
    {
        "code": "REMOVE_UNDERPERFORMER",
        "name": "Remove underperforming menu item",
        "category": "remove_underperformer",
        "description": "Retire items with low sales and low margin to simplify menu and cut waste",
        "applicability_rules": {"max_popularity_score": 0.15, "max_margin_pct": 0.25},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name",
            "weekly_orders",
            "margin_pct",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.65,
        "expected_kpi_targets": {"waste_reduction_pct": 10},
    },
    {
        "code": "SIMPLIFY_MENU_CATEGORY",
        "name": "Simplify an overcrowded menu category",
        "category": "menu_simplification",
        "description": "Reduce the number of items in a category that has too many low-performers",
        "applicability_rules": {"min_category_items": 8, "max_avg_popularity": 0.35},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "category",
            "current_item_count",
            "suggested_removals",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.6,
        "expected_kpi_targets": {"waste_reduction_pct": 8, "ops_efficiency_increase_pct": 5},
    },
    # ── cost_optimization ────────────────────────────────────────────────
    {
        "code": "RENEGOTIATE_SUPPLIER",
        "name": "Renegotiate high-cost ingredient supplier",
        "category": "cost_optimization",
        "description": "Flag ingredients whose unit cost is high relative to revenue contribution",
        "applicability_rules": {"min_ingredient_cost_share": 0.15},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name",
            "current_unit_cost",
            "cost_share_pct",
        ],
        "cooldown_days": 60,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"cost_savings_pct": 5},
    },
    # ── reorder ──────────────────────────────────────────────────────────
    {
        "code": "REORDER_ALERT",
        "name": "Reorder ingredient approaching stockout",
        "category": "reorder",
        "description": "Trigger a reorder when inventory falls near or below the reorder threshold",
        "applicability_rules": {"max_days_of_stock": 3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name",
            "quantity_on_hand",
            "reorder_threshold",
            "days_of_stock_remaining",
        ],
        "cooldown_days": 7,
        "confidence_threshold": 0.7,
        "expected_kpi_targets": {"stockout_risk_reduction_pct": 80},
    },
    # ── reduce_overstock ─────────────────────────────────────────────────
    {
        "code": "REDUCE_OVERSTOCK",
        "name": "Reduce overstocked ingredient",
        "category": "reduce_overstock",
        "description": "Promote dishes that use an overstocked ingredient to draw down inventory",
        "applicability_rules": {"min_overstock_ratio": 2.0},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name",
            "quantity_on_hand",
            "normal_weekly_usage",
            "suggested_items_to_promote",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"waste_reduction_pct": 15},
    },
    # ── reduce_waste ─────────────────────────────────────────────────────
    {
        "code": "REDUCE_WASTE",
        "name": "Reduce waste from near-expiry ingredients",
        "category": "reduce_waste",
        "description": "Push specials or discounts using ingredients nearing their expiry date",
        "applicability_rules": {"max_days_to_expiry": 5},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name",
            "expiry_date",
            "quantity_on_hand",
            "suggested_special",
        ],
        "cooldown_days": 7,
        "confidence_threshold": 0.7,
        "expected_kpi_targets": {"waste_reduction_pct": 20},
    },
    # ── social_promote ───────────────────────────────────────────────────
    {
        "code": "PROMOTE_HIGH_MARGIN_SOCIAL",
        "name": "Promote high-margin item on social media",
        "category": "social_promote",
        "description": "Create a social post featuring a high-margin item that lacks recent promotion",
        "applicability_rules": {"min_margin_pct": 0.5, "max_recent_posts": 1},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name",
            "margin_pct",
            "last_promoted_days_ago",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"social_engagement_increase_pct": 15},
    },
    {
        "code": "PROMOTE_TRENDING_SOCIAL",
        "name": "Promote trending item on social media",
        "category": "social_promote",
        "description": "Amplify a menu item whose sales are trending upward with a social push",
        "applicability_rules": {"min_sales_trend_slope": 0.1, "min_popularity_score": 0.5},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name",
            "sales_trend_slope",
            "current_weekly_orders",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"social_engagement_increase_pct": 20, "revenue_increase_pct": 5},
    },
    # ── social_timing ────────────────────────────────────────────────────
    {
        "code": "OPTIMIZE_POST_TIMING",
        "name": "Optimize social media post timing",
        "category": "social_timing",
        "description": "Schedule posts at times that historically receive the highest engagement",
        "applicability_rules": {"min_post_count": 10},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "best_day",
            "best_hour",
            "avg_engagement_at_best_time",
            "avg_engagement_overall",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"social_engagement_increase_pct": 25},
    },
    # ── highlight_margin ─────────────────────────────────────────────────
    {
        "code": "HIGHLIGHT_MARGIN_ITEM",
        "name": "Highlight high-margin item on menu",
        "category": "highlight_margin",
        "description": "Add visual emphasis (badge, top placement) to high-margin items on the menu",
        "applicability_rules": {"min_margin_pct": 0.55, "max_popularity_score": 0.5},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name",
            "margin_pct",
            "current_popularity_score",
        ],
        "cooldown_days": 21,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"revenue_increase_pct": 7},
    },
    # ── scale_campaign ───────────────────────────────────────────────────
    {
        "code": "SCALE_SUCCESSFUL_CAMPAIGN",
        "name": "Scale a successful past strategy",
        "category": "scale_campaign",
        "description": "Re-apply or expand a strategy that previously delivered strong results",
        "applicability_rules": {"min_past_success_count": 1},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "original_strategy_code",
            "past_impact",
            "suggested_expansion",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.6,
        "expected_kpi_targets": {"revenue_increase_pct": 10},
    },
    # ── reorder (bulk) ───────────────────────────────────────────────────
    {
        "code": "BULK_REORDER_DISCOUNT",
        "name": "Place bulk reorder to capture supplier discount",
        "category": "reorder",
        "description": "Order in larger quantities for high-turnover ingredients to lower unit cost",
        "applicability_rules": {"min_weekly_usage_units": 50, "min_margin_pct": 0.3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name",
            "current_unit_cost",
            "estimated_bulk_unit_cost",
            "weekly_usage",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"cost_savings_pct": 8},
    },
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_playbook() -> list[dict[str, Any]]:
    """Return the full strategy playbook."""
    return STRATEGY_PLAYBOOK


def get_strategy_by_code(code: str) -> dict[str, Any] | None:
    """Look up a single strategy dict by its unique code."""
    for strategy in STRATEGY_PLAYBOOK:
        if strategy["code"] == code:
            return strategy
    return None


def seed_strategies(db: Session) -> list[StrategyDefinition]:
    """Insert all playbook strategies into the StrategyDefinition table.

    Strategies that already exist (matched by ``code``) are skipped so the
    function is safe to call repeatedly (idempotent).

    Returns the list of StrategyDefinition rows that were newly created.
    """
    existing_codes: set[str] = {
        row[0]
        for row in db.query(StrategyDefinition.code).all()
    }

    created: list[StrategyDefinition] = []

    for entry in STRATEGY_PLAYBOOK:
        if entry["code"] in existing_codes:
            continue

        sd = StrategyDefinition(
            code=entry["code"],
            name=entry["name"],
            category=entry.get("category"),
            description=entry.get("description"),
            applicability_rules=entry.get("applicability_rules"),
            blocked_conditions=entry.get("blocked_conditions"),
            expected_evidence_fields=entry.get("expected_evidence_fields"),
            cooldown_days=entry.get("cooldown_days", 14),
            confidence_threshold=entry.get("confidence_threshold", 0.5),
            expected_kpi_targets=entry.get("expected_kpi_targets"),
            is_active=True,
        )
        db.add(sd)
        created.append(sd)

    if created:
        db.commit()
        for sd in created:
            db.refresh(sd)

    return created
