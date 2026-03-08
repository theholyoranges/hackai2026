"""Recommendation Engine: matches playbook strategies against live analytics,
filters out blocked strategies, scores candidates, and persists the top
recommendations.
"""

from __future__ import annotations

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


class RecommendationEngine:
    """Generates and persists strategy recommendations for a restaurant."""

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def generate_recommendations(
        self, db: Session, restaurant_id: int
    ) -> list[Recommendation]:
        """Run the full recommendation pipeline and return the top 10.

        Steps:
        1. Gather analytics (menu, inventory, social, sales).
        2. For each playbook strategy check applicability.
        3. Filter out blocked strategies.
        4. Score remaining candidates.
        5. Persist top 10 as Recommendation rows.
        """
        analytics = self._gather_analytics(db, restaurant_id)
        blocked_codes = StrategyHistoryEngine.get_blocked_strategy_codes(
            db, restaurant_id
        )

        # Resolve strategy definition ids by code
        sd_map: dict[str, StrategyDefinition] = {
            sd.code: sd
            for sd in db.query(StrategyDefinition).filter(
                StrategyDefinition.is_active.is_(True)
            ).all()
        }

        candidates: list[dict[str, Any]] = []

        for strategy in get_playbook():
            code = strategy["code"]

            # Skip blocked
            if code in blocked_codes:
                continue

            # Skip if no DB definition
            sd = sd_map.get(code)
            if sd is None:
                continue

            matches, evidence, confidence = self._match_strategy(strategy, analytics)
            if not matches:
                continue

            impact = self._calculate_impact(strategy, evidence)
            recency_penalty = self._recency_penalty(db, restaurant_id, code)
            score = impact * confidence * (1.0 - recency_penalty)

            candidates.append(
                {
                    "strategy_def": strategy,
                    "sd": sd,
                    "evidence": evidence,
                    "confidence": confidence,
                    "impact": impact,
                    "score": score,
                }
            )

        # Sort by score descending and take top 10
        candidates.sort(key=lambda c: c["score"], reverse=True)
        top = candidates[:10]

        recommendations: list[Recommendation] = []
        for cand in top:
            explanation_input = self._build_explanation_input(
                cand["strategy_def"], cand["evidence"]
            )
            rec = Recommendation(
                restaurant_id=restaurant_id,
                strategy_definition_id=cand["sd"].id,
                menu_item_id=cand["evidence"].get("menu_item_id"),
                title=cand["strategy_def"]["name"],
                evidence=cand["evidence"],
                confidence=round(cand["confidence"], 4),
                urgency=self._urgency_label(cand["score"]),
                expected_impact=str(cand["strategy_def"].get("expected_kpi_targets", {})),
                explanation_input=explanation_input,
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
    # Strategy matching (rule-based)
    # ------------------------------------------------------------------

    def _match_strategy(
        self, strategy_def: dict[str, Any], analytics: dict[str, Any]
    ) -> tuple[bool, dict[str, Any], float]:
        """Check whether *strategy_def* applies given current *analytics*.

        Returns (matches, evidence_dict, confidence).
        """
        code = strategy_def["code"]
        rules = strategy_def.get("applicability_rules", {})

        # Dispatch to specific matchers
        matcher = getattr(self, f"_match_{code.lower()}", None)
        if matcher is not None:
            return matcher(rules, analytics)

        # Fallback: generic rule check (always returns no match)
        return False, {}, 0.0

    # ---- Individual matchers ------------------------------------------

    def _match_price_increase_high_demand(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        min_pop = rules.get("min_popularity_score", 0.7)
        min_margin = rules.get("min_margin_pct", 0.3)
        for item in analytics.get("menu_items", []):
            pop = item.get("popularity_score", 0)
            margin = item.get("margin_pct", 0)
            if pop >= min_pop and margin >= min_margin:
                suggested_increase = min(0.15, 0.05 + (pop - 0.7) * 0.2)
                suggested_price = round(item["price"] * (1 + suggested_increase), 2)
                return True, {
                    "item_name": item["name"],
                    "menu_item_id": item["id"],
                    "current_price": item["price"],
                    "suggested_price": suggested_price,
                    "popularity_score": round(pop, 3),
                    "margin_pct": round(margin, 3),
                }, min(0.9, 0.6 + pop * 0.3)
        return False, {}, 0.0

    def _match_price_decrease_low_demand(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        max_pop = rules.get("max_popularity_score", 0.3)
        min_margin = rules.get("min_margin_pct", 0.4)
        for item in analytics.get("menu_items", []):
            pop = item.get("popularity_score", 0)
            margin = item.get("margin_pct", 0)
            if pop <= max_pop and margin >= min_margin:
                decrease = 0.05 + (max_pop - pop) * 0.1
                suggested_price = round(item["price"] * (1 - min(decrease, 0.10)), 2)
                return True, {
                    "item_name": item["name"],
                    "menu_item_id": item["id"],
                    "current_price": item["price"],
                    "suggested_price": suggested_price,
                    "popularity_score": round(pop, 3),
                }, 0.55
        return False, {}, 0.0

    def _match_bundle_complementary(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        min_freq = rules.get("min_pair_frequency", 5)
        min_conf = rules.get("min_pair_confidence", 0.3)
        for pair in analytics.get("pair_associations", []):
            if pair.get("frequency", 0) >= min_freq and pair.get("confidence", 0) >= min_conf:
                return True, {
                    "item_a_name": pair["item_a"],
                    "item_b_name": pair["item_b"],
                    "pair_frequency": pair["frequency"],
                    "suggested_bundle_price": pair.get("suggested_bundle_price"),
                }, min(0.85, 0.5 + pair["confidence"] * 0.5)
        return False, {}, 0.0

    def _match_bundle_meal_deal(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        categories = analytics.get("menu_categories", [])
        if len(categories) >= rules.get("min_categories_available", 3):
            return True, {
                "categories_available": len(categories),
                "items": categories[:3],
            }, 0.5
        return False, {}, 0.0

    def _match_upsell_premium_variant(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        min_pop = rules.get("min_popularity_score", 0.6)
        min_gap = rules.get("min_margin_gap", 0.15)
        items = analytics.get("menu_items", [])
        for i, base in enumerate(items):
            if base.get("popularity_score", 0) < min_pop:
                continue
            for premium in items:
                if premium["id"] == base["id"]:
                    continue
                margin_diff = premium.get("margin_pct", 0) - base.get("margin_pct", 0)
                if margin_diff >= min_gap and premium.get("category") == base.get("category"):
                    return True, {
                        "base_item_name": base["name"],
                        "premium_item_name": premium["name"],
                        "margin_difference": round(margin_diff, 3),
                        "menu_item_id": premium["id"],
                    }, 0.55
        return False, {}, 0.0

    def _match_remove_underperformer(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        max_pop = rules.get("max_popularity_score", 0.15)
        max_margin = rules.get("max_margin_pct", 0.25)
        for item in analytics.get("menu_items", []):
            pop = item.get("popularity_score", 0)
            margin = item.get("margin_pct", 0)
            if pop <= max_pop and margin <= max_margin:
                return True, {
                    "item_name": item["name"],
                    "menu_item_id": item["id"],
                    "weekly_orders": item.get("weekly_orders", 0),
                    "margin_pct": round(margin, 3),
                }, 0.65
        return False, {}, 0.0

    def _match_simplify_menu_category(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        category_stats = analytics.get("category_stats", {})
        for cat, stats in category_stats.items():
            if (
                stats.get("item_count", 0) >= rules.get("min_category_items", 8)
                and stats.get("avg_popularity", 1.0) <= rules.get("max_avg_popularity", 0.35)
            ):
                return True, {
                    "category": cat,
                    "current_item_count": stats["item_count"],
                    "suggested_removals": stats.get("low_performers", []),
                }, 0.6
        return False, {}, 0.0

    def _match_renegotiate_supplier(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        for ing in analytics.get("ingredient_costs", []):
            if ing.get("cost_share_pct", 0) >= rules.get("min_ingredient_cost_share", 0.15):
                return True, {
                    "ingredient_name": ing["name"],
                    "current_unit_cost": ing["unit_cost"],
                    "cost_share_pct": round(ing["cost_share_pct"], 3),
                }, 0.5
        return False, {}, 0.0

    def _match_reorder_alert(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        max_days = rules.get("max_days_of_stock", 3)
        for inv in analytics.get("inventory_alerts", []):
            if inv.get("days_of_stock_remaining", 999) <= max_days:
                return True, {
                    "ingredient_name": inv["ingredient_name"],
                    "quantity_on_hand": inv["quantity_on_hand"],
                    "reorder_threshold": inv.get("reorder_threshold"),
                    "days_of_stock_remaining": inv["days_of_stock_remaining"],
                }, 0.8
        return False, {}, 0.0

    def _match_reduce_overstock(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        min_ratio = rules.get("min_overstock_ratio", 2.0)
        for inv in analytics.get("overstock_items", []):
            if inv.get("overstock_ratio", 0) >= min_ratio:
                return True, {
                    "ingredient_name": inv["ingredient_name"],
                    "quantity_on_hand": inv["quantity_on_hand"],
                    "normal_weekly_usage": inv.get("weekly_usage", 0),
                    "suggested_items_to_promote": inv.get("related_menu_items", []),
                }, 0.55
        return False, {}, 0.0

    def _match_reduce_waste(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        max_days = rules.get("max_days_to_expiry", 5)
        for inv in analytics.get("expiry_alerts", []):
            if inv.get("days_to_expiry", 999) <= max_days:
                return True, {
                    "ingredient_name": inv["ingredient_name"],
                    "expiry_date": str(inv.get("expiry_date")),
                    "quantity_on_hand": inv["quantity_on_hand"],
                    "suggested_special": inv.get("suggested_special", "Daily special"),
                }, 0.75
        return False, {}, 0.0

    def _match_promote_high_margin_social(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        min_margin = rules.get("min_margin_pct", 0.5)
        max_posts = rules.get("max_recent_posts", 1)
        for item in analytics.get("menu_items", []):
            if (
                item.get("margin_pct", 0) >= min_margin
                and item.get("recent_social_posts", 999) <= max_posts
            ):
                return True, {
                    "item_name": item["name"],
                    "menu_item_id": item["id"],
                    "margin_pct": round(item["margin_pct"], 3),
                    "last_promoted_days_ago": item.get("last_promoted_days_ago", 30),
                }, 0.55
        return False, {}, 0.0

    def _match_promote_trending_social(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        min_slope = rules.get("min_sales_trend_slope", 0.1)
        min_pop = rules.get("min_popularity_score", 0.5)
        for item in analytics.get("menu_items", []):
            slope = item.get("sales_trend_slope", 0)
            pop = item.get("popularity_score", 0)
            if slope >= min_slope and pop >= min_pop:
                return True, {
                    "item_name": item["name"],
                    "menu_item_id": item["id"],
                    "sales_trend_slope": round(slope, 3),
                    "current_weekly_orders": item.get("weekly_orders", 0),
                }, 0.6
        return False, {}, 0.0

    def _match_optimize_post_timing(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        social = analytics.get("social_timing", {})
        if social.get("total_posts", 0) >= rules.get("min_post_count", 10):
            return True, {
                "best_day": social.get("best_day", "Saturday"),
                "best_hour": social.get("best_hour", 12),
                "avg_engagement_at_best_time": social.get("best_engagement", 0),
                "avg_engagement_overall": social.get("avg_engagement", 0),
            }, 0.55
        return False, {}, 0.0

    def _match_highlight_margin_item(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        min_margin = rules.get("min_margin_pct", 0.55)
        max_pop = rules.get("max_popularity_score", 0.5)
        for item in analytics.get("menu_items", []):
            margin = item.get("margin_pct", 0)
            pop = item.get("popularity_score", 0)
            if margin >= min_margin and pop <= max_pop:
                return True, {
                    "item_name": item["name"],
                    "menu_item_id": item["id"],
                    "margin_pct": round(margin, 3),
                    "current_popularity_score": round(pop, 3),
                }, 0.55
        return False, {}, 0.0

    def _match_scale_successful_campaign(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        successes = analytics.get("successful_strategies", [])
        if len(successes) >= rules.get("min_past_success_count", 1):
            best = successes[0]
            return True, {
                "original_strategy_code": best.get("code"),
                "past_impact": best.get("actual_impact"),
                "suggested_expansion": "Repeat at larger scope or across more items",
            }, 0.6
        return False, {}, 0.0

    def _match_bulk_reorder_discount(
        self, rules: dict, analytics: dict
    ) -> tuple[bool, dict, float]:
        min_usage = rules.get("min_weekly_usage_units", 50)
        for inv in analytics.get("high_usage_ingredients", []):
            if inv.get("weekly_usage", 0) >= min_usage:
                return True, {
                    "ingredient_name": inv["ingredient_name"],
                    "current_unit_cost": inv.get("unit_cost", 0),
                    "estimated_bulk_unit_cost": round(inv.get("unit_cost", 0) * 0.9, 2),
                    "weekly_usage": inv["weekly_usage"],
                }, 0.5
        return False, {}, 0.0

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_impact(strategy_def: dict[str, Any], evidence: dict[str, Any]) -> float:
        """Estimate a 0-1 impact score from the strategy's KPI targets."""
        targets = strategy_def.get("expected_kpi_targets", {})
        if not targets:
            return 0.5
        # Sum up all target percentages, cap at 100
        total_pct = sum(targets.values())
        return min(total_pct / 100.0, 1.0)

    @staticmethod
    def _recency_penalty(db: Session, restaurant_id: int, strategy_code: str) -> float:
        """Return 0-0.5 penalty based on how recently this strategy was suggested."""
        from app.models.strategy import StrategyHistory, StrategyDefinition

        row = (
            db.query(StrategyHistory.created_at)
            .join(
                StrategyDefinition,
                StrategyHistory.strategy_definition_id == StrategyDefinition.id,
            )
            .filter(
                StrategyHistory.restaurant_id == restaurant_id,
                StrategyDefinition.code == strategy_code,
            )
            .order_by(StrategyHistory.created_at.desc())
            .first()
        )
        if row is None:
            return 0.0
        days_ago = (datetime.utcnow() - row[0]).days
        if days_ago < 7:
            return 0.5
        if days_ago < 14:
            return 0.3
        if days_ago < 30:
            return 0.1
        return 0.0

    @staticmethod
    def _urgency_label(score: float) -> str:
        if score >= 0.15:
            return "high"
        if score >= 0.08:
            return "medium"
        return "low"

    @staticmethod
    def _build_explanation_input(
        strategy_def: dict[str, Any], evidence: dict[str, Any]
    ) -> dict[str, Any]:
        """Build a dict that the LLM explanation layer will consume."""
        return {
            "strategy_code": strategy_def["code"],
            "strategy_name": strategy_def["name"],
            "category": strategy_def.get("category"),
            "description": strategy_def.get("description"),
            "evidence": evidence,
            "expected_kpi_targets": strategy_def.get("expected_kpi_targets", {}),
        }

    # ------------------------------------------------------------------
    # Analytics gathering
    # ------------------------------------------------------------------

    def _gather_analytics(self, db: Session, restaurant_id: int) -> dict[str, Any]:
        """Aggregate data from menu, inventory, sales, and social tables."""
        analytics: dict[str, Any] = {}

        # ── Menu items with popularity & margin ──────────────────────
        menu_items_raw = (
            db.query(MenuItem).filter(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_active.is_(True),
            ).all()
        )

        # Calculate total sales per item in last 30 days
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

        # Recent social posts per menu item (last 30 days)
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
                "last_promoted_days_ago": 30,  # simplified
                "sales_trend_slope": 0.0,  # placeholder
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
            low = [i["name"] for i in items if i["popularity_score"] < 0.2]
            cat_stats[cat] = {
                "item_count": len(items),
                "avg_popularity": sum(pops) / len(pops) if pops else 0,
                "low_performers": low,
            }
        analytics["category_stats"] = cat_stats

        # ── Pair associations (simplified: co-occurrence in same order) ─
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
            pair_associations.append(
                {
                    "item_a": item_name_map.get(a, str(a)),
                    "item_b": item_name_map.get(b, str(b)),
                    "frequency": freq,
                    "confidence": freq / total_orders,
                    "suggested_bundle_price": round(
                        (item_price_map.get(a, 0) + item_price_map.get(b, 0)) * 0.9, 2
                    ),
                }
            )
        analytics["pair_associations"] = pair_associations

        # ── Inventory alerts ─────────────────────────────────────────
        inventory_rows = (
            db.query(InventoryItem)
            .filter(InventoryItem.restaurant_id == restaurant_id)
            .all()
        )

        # Estimate daily usage from recipe mappings + sales
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
                "reorder_threshold": float(inv.reorder_threshold) if inv.reorder_threshold else None,
                "days_of_stock_remaining": round(days_remaining, 1),
                "weekly_usage": round(weekly_usage, 2),
                "unit_cost": float(inv.unit_cost) if inv.unit_cost else 0,
            }

            # Low stock alert
            if days_remaining <= 3:
                inventory_alerts.append(inv_data)

            # Overstock
            if weekly_usage > 0 and qty / weekly_usage >= 2.0:
                inv_data["overstock_ratio"] = round(qty / weekly_usage, 2)
                inv_data["related_menu_items"] = []
                overstock_items.append(inv_data)

            # Expiry
            if inv.expiry_date:
                from datetime import date

                days_to_expiry = (inv.expiry_date - date.today()).days
                if days_to_expiry <= 5:
                    inv_data["days_to_expiry"] = days_to_expiry
                    inv_data["expiry_date"] = str(inv.expiry_date)
                    expiry_alerts.append(inv_data)

            # High usage
            if weekly_usage >= 50:
                high_usage_ingredients.append(inv_data)

            # Ingredient cost share
            cost_val = float(inv.unit_cost or 0) * qty
            if cost_val / total_ingredient_cost >= 0.15:
                ingredient_costs.append(
                    {
                        "name": inv.ingredient_name,
                        "unit_cost": float(inv.unit_cost or 0),
                        "cost_share_pct": cost_val / total_ingredient_cost,
                    }
                )

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

        # ── Successful past strategies ───────────────────────────────
        successes = StrategyHistoryEngine.get_successful_strategies(db, restaurant_id)
        analytics["successful_strategies"] = [
            {
                "code": sh.strategy_definition.code if sh.strategy_definition else "unknown",
                "actual_impact": sh.actual_impact,
            }
            for sh in successes
        ]

        return analytics
