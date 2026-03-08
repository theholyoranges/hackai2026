"""Menu analytics engine -- computes factual metrics from sales and menu data."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem
from app.models.sales_record import SalesRecord


class MenuAnalyticsEngine:
    """Pure-analytics helper: every public method returns JSON-serializable data."""

    # ------------------------------------------------------------------
    # Top / bottom sellers
    # ------------------------------------------------------------------

    @staticmethod
    def get_top_sellers(
        db: Session, restaurant_id: int, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Return the *limit* best-selling items by quantity sold."""
        rows = (
            db.query(
                MenuItem.name,
                func.coalesce(func.sum(SalesRecord.quantity), 0).label("qty_sold"),
                func.coalesce(func.sum(SalesRecord.total_price), 0).label("revenue"),
            )
            .join(SalesRecord, SalesRecord.menu_item_id == MenuItem.id)
            .filter(SalesRecord.restaurant_id == restaurant_id)
            .group_by(MenuItem.name)
            .order_by(func.sum(SalesRecord.quantity).desc())
            .limit(limit)
            .all()
        )
        return [
            {"item": r.name, "qty_sold": int(r.qty_sold), "revenue": float(r.revenue)}
            for r in rows
        ]

    @staticmethod
    def get_bottom_sellers(
        db: Session, restaurant_id: int, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Return the *limit* worst-selling items by quantity sold."""
        rows = (
            db.query(
                MenuItem.name,
                func.coalesce(func.sum(SalesRecord.quantity), 0).label("qty_sold"),
                func.coalesce(func.sum(SalesRecord.total_price), 0).label("revenue"),
            )
            .join(SalesRecord, SalesRecord.menu_item_id == MenuItem.id)
            .filter(SalesRecord.restaurant_id == restaurant_id)
            .group_by(MenuItem.name)
            .order_by(func.sum(SalesRecord.quantity).asc())
            .limit(limit)
            .all()
        )
        return [
            {"item": r.name, "qty_sold": int(r.qty_sold), "revenue": float(r.revenue)}
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Revenue breakdown
    # ------------------------------------------------------------------

    @staticmethod
    def get_revenue_by_item(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Revenue per item with percentage of total."""
        rows = (
            db.query(
                MenuItem.name,
                func.coalesce(func.sum(SalesRecord.total_price), 0).label("revenue"),
            )
            .join(SalesRecord, SalesRecord.menu_item_id == MenuItem.id)
            .filter(SalesRecord.restaurant_id == restaurant_id)
            .group_by(MenuItem.name)
            .order_by(func.sum(SalesRecord.total_price).desc())
            .all()
        )
        total_revenue = sum(float(r.revenue) for r in rows)
        return [
            {
                "item": r.name,
                "revenue": float(r.revenue),
                "pct_of_total": round(float(r.revenue) / total_revenue * 100, 2)
                if total_revenue
                else 0.0,
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Margin analysis
    # ------------------------------------------------------------------

    @staticmethod
    def get_margin_analysis(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Per-item price, ingredient cost, margin, and margin percentage."""
        items = (
            db.query(MenuItem)
            .filter(MenuItem.restaurant_id == restaurant_id, MenuItem.is_active.is_(True))
            .all()
        )
        results: list[dict[str, Any]] = []
        for item in items:
            price = float(item.price)
            cost = float(item.ingredient_cost) if item.ingredient_cost is not None else 0.0
            margin = price - cost
            margin_pct = round(margin / price * 100, 2) if price else 0.0
            results.append(
                {
                    "item": item.name,
                    "price": price,
                    "cost": cost,
                    "margin": round(margin, 2),
                    "margin_pct": margin_pct,
                }
            )
        return results

    # ------------------------------------------------------------------
    # Menu engineering (BCG-style matrix)
    # ------------------------------------------------------------------

    @staticmethod
    def get_menu_engineering(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Classify each item as Star / Plow Horse / Puzzle / Dog.

        * Star        – above-median popularity AND above-median margin
        * Plow Horse  – above-median popularity, below-median margin
        * Puzzle      – below-median popularity, above-median margin
        * Dog         – both below median
        """
        rows = (
            db.query(
                MenuItem.name,
                MenuItem.price,
                MenuItem.ingredient_cost,
                func.coalesce(func.sum(SalesRecord.quantity), 0).label("qty_sold"),
            )
            .outerjoin(SalesRecord, SalesRecord.menu_item_id == MenuItem.id)
            .filter(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_active.is_(True),
            )
            .group_by(MenuItem.id, MenuItem.name, MenuItem.price, MenuItem.ingredient_cost)
            .all()
        )
        if not rows:
            return []

        df = pd.DataFrame(
            [
                {
                    "item": r.name,
                    "price": float(r.price),
                    "cost": float(r.ingredient_cost) if r.ingredient_cost is not None else 0.0,
                    "qty_sold": int(r.qty_sold),
                }
                for r in rows
            ]
        )
        df["margin"] = df["price"] - df["cost"]

        median_qty = df["qty_sold"].median()
        median_margin = df["margin"].median()

        def _classify(row: pd.Series) -> str:
            high_pop = row["qty_sold"] >= median_qty
            high_margin = row["margin"] >= median_margin
            if high_pop and high_margin:
                return "Star"
            if high_pop and not high_margin:
                return "Plow Horse"
            if not high_pop and high_margin:
                return "Puzzle"
            return "Dog"

        df["classification"] = df.apply(_classify, axis=1)

        return df[["item", "qty_sold", "margin", "classification"]].to_dict(orient="records")

    # ------------------------------------------------------------------
    # Market-basket / pair analysis  (mlxtend)
    # ------------------------------------------------------------------

    @staticmethod
    def get_pair_analysis(
        db: Session,
        restaurant_id: int,
        min_support: float = 0.01,
        min_confidence: float = 0.1,
    ) -> list[dict[str, Any]]:
        """Association-rule mining on order-level basket data using mlxtend."""
        rows = (
            db.query(SalesRecord.order_id, MenuItem.name)
            .join(MenuItem, MenuItem.id == SalesRecord.menu_item_id)
            .filter(
                SalesRecord.restaurant_id == restaurant_id,
                SalesRecord.order_id.isnot(None),
            )
            .all()
        )
        if not rows:
            return []

        # Build baskets: list of sets
        baskets: dict[str, set[str]] = {}
        for order_id, item_name in rows:
            baskets.setdefault(order_id, set()).add(item_name)

        transactions = list(baskets.values())
        if len(transactions) < 2:
            return []

        try:
            from mlxtend.frequent_patterns import apriori, association_rules
            from mlxtend.preprocessing import TransactionEncoder

            te = TransactionEncoder()
            te_array = te.fit(transactions).transform(transactions)
            basket_df = pd.DataFrame(te_array, columns=te.columns_)

            frequent = apriori(basket_df, min_support=min_support, use_colnames=True)
            if frequent.empty:
                return []

            rules = association_rules(frequent, metric="confidence", min_threshold=min_confidence)
            if rules.empty:
                return []

            results: list[dict[str, Any]] = []
            for _, rule in rules.iterrows():
                results.append(
                    {
                        "antecedents": sorted(rule["antecedents"]),
                        "consequents": sorted(rule["consequents"]),
                        "support": round(float(rule["support"]), 4),
                        "confidence": round(float(rule["confidence"]), 4),
                        "lift": round(float(rule["lift"]), 4),
                    }
                )
            return results
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Demand trends
    # ------------------------------------------------------------------

    @staticmethod
    def get_demand_trends(
        db: Session, restaurant_id: int
    ) -> dict[str, Any]:
        """Aggregate sales by day_of_week and hour_of_day."""
        rows = (
            db.query(
                SalesRecord.day_of_week,
                SalesRecord.hour_of_day,
                func.sum(SalesRecord.quantity).label("qty"),
                func.sum(SalesRecord.total_price).label("revenue"),
            )
            .filter(SalesRecord.restaurant_id == restaurant_id)
            .group_by(SalesRecord.day_of_week, SalesRecord.hour_of_day)
            .all()
        )
        if not rows:
            return {"by_day_of_week": [], "by_hour_of_day": []}

        df = pd.DataFrame(
            [
                {
                    "day_of_week": r.day_of_week,
                    "hour_of_day": r.hour_of_day,
                    "qty": int(r.qty),
                    "revenue": float(r.revenue),
                }
                for r in rows
            ]
        )

        by_day = (
            df.groupby("day_of_week")[["qty", "revenue"]]
            .sum()
            .reset_index()
            .to_dict(orient="records")
            if "day_of_week" in df.columns and df["day_of_week"].notna().any()
            else []
        )

        by_hour = (
            df.groupby("hour_of_day")[["qty", "revenue"]]
            .sum()
            .reset_index()
            .to_dict(orient="records")
            if "hour_of_day" in df.columns and df["hour_of_day"].notna().any()
            else []
        )

        return {"by_day_of_week": by_day, "by_hour_of_day": by_hour}

    # ------------------------------------------------------------------
    # Category performance
    # ------------------------------------------------------------------

    @staticmethod
    def get_category_performance(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Revenue and average margin by menu category."""
        rows = (
            db.query(
                MenuItem.category,
                func.sum(SalesRecord.total_price).label("revenue"),
                func.avg(MenuItem.price - MenuItem.ingredient_cost).label("avg_margin"),
            )
            .join(SalesRecord, SalesRecord.menu_item_id == MenuItem.id)
            .filter(
                SalesRecord.restaurant_id == restaurant_id,
                MenuItem.category.isnot(None),
            )
            .group_by(MenuItem.category)
            .order_by(func.sum(SalesRecord.total_price).desc())
            .all()
        )
        return [
            {
                "category": r.category,
                "revenue": float(r.revenue) if r.revenue else 0.0,
                "avg_margin": round(float(r.avg_margin), 2) if r.avg_margin else 0.0,
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Full analysis (convenience aggregator)
    # ------------------------------------------------------------------

    @classmethod
    def get_full_analysis(
        cls, db: Session, restaurant_id: int
    ) -> dict[str, Any]:
        """Run every menu-analytics method and return a combined dict."""
        return {
            "top_sellers": cls.get_top_sellers(db, restaurant_id),
            "bottom_sellers": cls.get_bottom_sellers(db, restaurant_id),
            "revenue_by_item": cls.get_revenue_by_item(db, restaurant_id),
            "margin_analysis": cls.get_margin_analysis(db, restaurant_id),
            "menu_engineering": cls.get_menu_engineering(db, restaurant_id),
            "pair_analysis": cls.get_pair_analysis(db, restaurant_id),
            "demand_trends": cls.get_demand_trends(db, restaurant_id),
            "category_performance": cls.get_category_performance(db, restaurant_id),
        }
