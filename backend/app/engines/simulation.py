"""Simulation Engine: lightweight what-if estimators for pricing, bundling,
reorder, and social timing scenarios.

All methods use historical averages and basic arithmetic rather than
sophisticated statistical models, keeping predictions fast and transparent.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.menu_item import MenuItem
from app.models.recipe_mapping import RecipeMapping
from app.models.sales_record import SalesRecord
from app.models.social_post import SocialPost


class SimulationEngine:
    """Provides simple simulation / estimation helpers."""

    # ------------------------------------------------------------------
    # Price change simulation
    # ------------------------------------------------------------------

    @staticmethod
    def simulate_price_change(
        db: Session, restaurant_id: int, item_id: int, new_price: float
    ) -> dict[str, Any]:
        """Estimate weekly revenue impact of changing an item's price.

        Uses a simple constant price-elasticity approximation:
            %ΔQ ≈ elasticity * %ΔP
        Default elasticity = -1.2 (moderately elastic restaurant item).

        Returns a dict with current vs projected revenue estimates and
        confidence level.
        """
        item = (
            db.query(MenuItem)
            .filter(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id)
            .first()
        )
        if item is None:
            return {"error": "Item not found", "confidence": 0.0}

        current_price = float(item.price)
        if current_price == 0:
            return {"error": "Current price is zero", "confidence": 0.0}

        # Historical weekly quantity
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        result = (
            db.query(func.sum(SalesRecord.quantity))
            .filter(
                SalesRecord.restaurant_id == restaurant_id,
                SalesRecord.menu_item_id == item_id,
                SalesRecord.sale_date >= seven_days_ago,
            )
            .scalar()
        )
        weekly_qty = float(result) if result else 0.0

        if weekly_qty == 0:
            return {
                "item_name": item.name,
                "current_price": current_price,
                "new_price": new_price,
                "note": "No recent sales data to base estimate on",
                "confidence": 0.1,
            }

        elasticity = -1.2
        pct_price_change = (new_price - current_price) / current_price
        pct_qty_change = elasticity * pct_price_change
        projected_qty = max(0, weekly_qty * (1 + pct_qty_change))

        current_revenue = current_price * weekly_qty
        projected_revenue = new_price * projected_qty
        revenue_change = projected_revenue - current_revenue
        revenue_change_pct = (revenue_change / current_revenue * 100) if current_revenue else 0

        # Confidence decreases for larger price swings
        abs_change = abs(pct_price_change)
        confidence = max(0.3, 0.85 - abs_change * 2)

        return {
            "item_name": item.name,
            "current_price": current_price,
            "new_price": new_price,
            "current_weekly_qty": round(weekly_qty, 1),
            "projected_weekly_qty": round(projected_qty, 1),
            "current_weekly_revenue": round(current_revenue, 2),
            "projected_weekly_revenue": round(projected_revenue, 2),
            "revenue_change": round(revenue_change, 2),
            "revenue_change_pct": round(revenue_change_pct, 2),
            "elasticity_used": elasticity,
            "confidence": round(confidence, 2),
        }

    # ------------------------------------------------------------------
    # Bundle opportunity scoring
    # ------------------------------------------------------------------

    @staticmethod
    def score_bundle_opportunity(
        db: Session, restaurant_id: int, item_ids: list[int]
    ) -> dict[str, Any]:
        """Score a potential bundle based on co-purchase frequency.

        Looks at orders from the last 30 days that contain ALL of the
        specified items, divided by total orders.
        """
        if len(item_ids) < 2:
            return {"error": "Need at least 2 items", "confidence": 0.0}

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Get all order_ids in the period
        all_order_ids = {
            row[0]
            for row in db.query(SalesRecord.order_id)
            .filter(
                SalesRecord.restaurant_id == restaurant_id,
                SalesRecord.sale_date >= thirty_days_ago,
                SalesRecord.order_id.isnot(None),
            )
            .distinct()
            .all()
        }
        total_orders = len(all_order_ids) or 1

        # Find orders containing ALL requested items
        matching_orders = set(all_order_ids)
        for iid in item_ids:
            orders_with_item = {
                row[0]
                for row in db.query(SalesRecord.order_id)
                .filter(
                    SalesRecord.restaurant_id == restaurant_id,
                    SalesRecord.menu_item_id == iid,
                    SalesRecord.sale_date >= thirty_days_ago,
                    SalesRecord.order_id.isnot(None),
                )
                .all()
            }
            matching_orders &= orders_with_item

        pair_frequency = len(matching_orders)
        co_purchase_rate = pair_frequency / total_orders

        # Individual prices
        items = (
            db.query(MenuItem)
            .filter(MenuItem.id.in_(item_ids), MenuItem.restaurant_id == restaurant_id)
            .all()
        )
        individual_total = sum(float(i.price) for i in items)
        suggested_discount = 0.10  # 10 %
        suggested_bundle_price = round(individual_total * (1 - suggested_discount), 2)

        # Score: 0-1 based on co-purchase rate
        score = min(1.0, co_purchase_rate * 5)  # 20% co-purchase → score 1.0
        confidence = min(0.9, 0.4 + pair_frequency / 50)

        return {
            "item_ids": item_ids,
            "item_names": [i.name for i in items],
            "pair_frequency": pair_frequency,
            "total_orders": total_orders,
            "co_purchase_rate": round(co_purchase_rate, 4),
            "individual_total": round(individual_total, 2),
            "suggested_bundle_price": suggested_bundle_price,
            "bundle_score": round(score, 3),
            "confidence": round(confidence, 2),
        }

    # ------------------------------------------------------------------
    # Reorder impact estimation
    # ------------------------------------------------------------------

    @staticmethod
    def estimate_reorder_impact(
        db: Session,
        restaurant_id: int,
        ingredient_name: str,
        order_qty: float,
    ) -> dict[str, Any]:
        """Estimate how many additional days of stock an order would provide."""
        inv = (
            db.query(InventoryItem)
            .filter(
                InventoryItem.restaurant_id == restaurant_id,
                InventoryItem.ingredient_name == ingredient_name,
            )
            .first()
        )
        if inv is None:
            return {"error": "Ingredient not found", "confidence": 0.0}

        # Estimate daily usage from recipe mappings + sales
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recipes = (
            db.query(RecipeMapping)
            .join(MenuItem, RecipeMapping.menu_item_id == MenuItem.id)
            .filter(
                MenuItem.restaurant_id == restaurant_id,
                RecipeMapping.ingredient_name == ingredient_name,
            )
            .all()
        )

        daily_usage = 0.0
        for rm in recipes:
            total_qty = (
                db.query(func.sum(SalesRecord.quantity))
                .filter(
                    SalesRecord.menu_item_id == rm.menu_item_id,
                    SalesRecord.sale_date >= thirty_days_ago,
                )
                .scalar()
            ) or 0
            daily_usage += (float(total_qty) / 30.0) * float(rm.quantity_needed)

        current_qty = float(inv.quantity_on_hand)
        new_qty = current_qty + order_qty

        if daily_usage <= 0:
            return {
                "ingredient_name": ingredient_name,
                "current_days_of_stock": 999,
                "new_days_of_stock": 999,
                "days_added": 999,
                "note": "No measurable daily usage",
                "confidence": 0.2,
            }

        current_days = current_qty / daily_usage
        new_days = new_qty / daily_usage
        days_added = new_days - current_days

        return {
            "ingredient_name": ingredient_name,
            "current_quantity": round(current_qty, 2),
            "order_quantity": round(order_qty, 2),
            "new_quantity": round(new_qty, 2),
            "daily_usage_estimate": round(daily_usage, 3),
            "current_days_of_stock": round(current_days, 1),
            "new_days_of_stock": round(new_days, 1),
            "days_added": round(days_added, 1),
            "confidence": 0.7,
        }

    # ------------------------------------------------------------------
    # Stockout risk reduction
    # ------------------------------------------------------------------

    @staticmethod
    def estimate_stockout_risk_reduction(
        db: Session,
        restaurant_id: int,
        ingredient_name: str,
        order_qty: float,
    ) -> dict[str, Any]:
        """Estimate the percentage reduction in stockout risk from ordering.

        Uses a simple heuristic: risk = max(0, 1 - days_of_stock / 7).
        """
        inv = (
            db.query(InventoryItem)
            .filter(
                InventoryItem.restaurant_id == restaurant_id,
                InventoryItem.ingredient_name == ingredient_name,
            )
            .first()
        )
        if inv is None:
            return {"error": "Ingredient not found", "confidence": 0.0}

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recipes = (
            db.query(RecipeMapping)
            .join(MenuItem, RecipeMapping.menu_item_id == MenuItem.id)
            .filter(
                MenuItem.restaurant_id == restaurant_id,
                RecipeMapping.ingredient_name == ingredient_name,
            )
            .all()
        )

        daily_usage = 0.0
        for rm in recipes:
            total_qty = (
                db.query(func.sum(SalesRecord.quantity))
                .filter(
                    SalesRecord.menu_item_id == rm.menu_item_id,
                    SalesRecord.sale_date >= thirty_days_ago,
                )
                .scalar()
            ) or 0
            daily_usage += (float(total_qty) / 30.0) * float(rm.quantity_needed)

        current_qty = float(inv.quantity_on_hand)
        new_qty = current_qty + order_qty

        if daily_usage <= 0:
            return {
                "ingredient_name": ingredient_name,
                "current_risk_pct": 0.0,
                "new_risk_pct": 0.0,
                "risk_reduction_pct": 0.0,
                "note": "No measurable daily usage",
                "confidence": 0.2,
            }

        current_days = current_qty / daily_usage
        new_days = new_qty / daily_usage

        current_risk = max(0.0, 1.0 - current_days / 7.0) * 100
        new_risk = max(0.0, 1.0 - new_days / 7.0) * 100
        reduction = current_risk - new_risk

        return {
            "ingredient_name": ingredient_name,
            "current_days_of_stock": round(current_days, 1),
            "new_days_of_stock": round(new_days, 1),
            "current_risk_pct": round(current_risk, 1),
            "new_risk_pct": round(new_risk, 1),
            "risk_reduction_pct": round(reduction, 1),
            "confidence": 0.65,
        }

    # ------------------------------------------------------------------
    # Social timing scoring
    # ------------------------------------------------------------------

    @staticmethod
    def score_social_timing(
        db: Session, restaurant_id: int, day_of_week: str, hour: int
    ) -> dict[str, Any]:
        """Score a proposed social-media posting time based on historical engagement.

        Returns an expected engagement score (likes + comments + shares)
        and a confidence level.
        """
        posts = (
            db.query(SocialPost)
            .filter(SocialPost.restaurant_id == restaurant_id)
            .all()
        )

        if not posts:
            return {
                "day_of_week": day_of_week,
                "hour": hour,
                "expected_engagement": 0,
                "note": "No historical social data",
                "confidence": 0.1,
            }

        # Bucket engagement by (day, hour)
        bucket: dict[tuple[str, int], list[int]] = {}
        all_engagements: list[int] = []

        for sp in posts:
            eng = (sp.likes or 0) + (sp.comments or 0) + (sp.shares or 0)
            all_engagements.append(eng)
            if sp.posted_at:
                key = (sp.posted_at.strftime("%A"), sp.posted_at.hour)
                bucket.setdefault(key, []).append(eng)

        avg_overall = sum(all_engagements) / len(all_engagements) if all_engagements else 0

        target_key = (day_of_week, hour)
        if target_key in bucket:
            vals = bucket[target_key]
            expected = sum(vals) / len(vals)
            confidence = min(0.9, 0.4 + len(vals) / 20)
        else:
            # Fall back to day-level average
            day_vals = [
                v for (d, _h), vs in bucket.items() if d == day_of_week for v in vs
            ]
            if day_vals:
                expected = sum(day_vals) / len(day_vals)
                confidence = min(0.7, 0.3 + len(day_vals) / 30)
            else:
                expected = avg_overall
                confidence = 0.2

        score_ratio = expected / avg_overall if avg_overall else 1.0

        return {
            "day_of_week": day_of_week,
            "hour": hour,
            "expected_engagement": round(expected, 2),
            "avg_engagement_overall": round(avg_overall, 2),
            "score_ratio": round(score_ratio, 3),
            "confidence": round(confidence, 2),
        }
