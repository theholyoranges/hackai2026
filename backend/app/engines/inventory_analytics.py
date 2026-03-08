"""Inventory analytics engine -- computes factual stock and usage metrics."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.menu_item import MenuItem
from app.models.recipe_mapping import RecipeMapping
from app.models.sales_record import SalesRecord


class InventoryAnalyticsEngine:
    """Pure-analytics helper for inventory / ingredient data."""

    # ------------------------------------------------------------------
    # Ingredient usage
    # ------------------------------------------------------------------

    @staticmethod
    def get_ingredient_usage(
        db: Session, restaurant_id: int, days: int = 30
    ) -> list[dict[str, Any]]:
        """Compute average daily usage per ingredient over the last *days* days.

        Usage = sum(sales.quantity * recipe.quantity_needed) / days
        """
        cutoff = date.today() - timedelta(days=days)

        rows = (
            db.query(
                RecipeMapping.ingredient_name,
                RecipeMapping.unit,
                func.sum(SalesRecord.quantity * RecipeMapping.quantity_needed).label(
                    "total_used"
                ),
            )
            .join(MenuItem, MenuItem.id == RecipeMapping.menu_item_id)
            .join(SalesRecord, SalesRecord.menu_item_id == MenuItem.id)
            .filter(
                SalesRecord.restaurant_id == restaurant_id,
                SalesRecord.sale_date >= cutoff,
            )
            .group_by(RecipeMapping.ingredient_name, RecipeMapping.unit)
            .all()
        )

        return [
            {
                "ingredient": r.ingredient_name,
                "unit": r.unit,
                "total_used": round(float(r.total_used), 4),
                "daily_usage": round(float(r.total_used) / max(days, 1), 4),
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Projected days left
    # ------------------------------------------------------------------

    @staticmethod
    def get_projected_days_left(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """For each ingredient, quantity_on_hand / daily_usage."""
        usage = InventoryAnalyticsEngine.get_ingredient_usage(db, restaurant_id, days=30)
        usage_map: dict[str, float] = {
            u["ingredient"]: u["daily_usage"] for u in usage
        }

        items = (
            db.query(InventoryItem)
            .filter(InventoryItem.restaurant_id == restaurant_id)
            .all()
        )

        results: list[dict[str, Any]] = []
        for item in items:
            daily = usage_map.get(item.ingredient_name, 0.0)
            qty = float(item.quantity_on_hand)
            days_left = round(qty / daily, 1) if daily > 0 else None
            results.append(
                {
                    "ingredient": item.ingredient_name,
                    "unit": item.unit,
                    "quantity_on_hand": qty,
                    "daily_usage": daily,
                    "projected_days_left": days_left,
                }
            )
        return results

    # ------------------------------------------------------------------
    # Reorder alerts
    # ------------------------------------------------------------------

    @staticmethod
    def get_reorder_alerts(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Items where projected_days_left < 7 or quantity < reorder_threshold."""
        projections = InventoryAnalyticsEngine.get_projected_days_left(db, restaurant_id)
        proj_map = {p["ingredient"]: p for p in projections}

        items = (
            db.query(InventoryItem)
            .filter(InventoryItem.restaurant_id == restaurant_id)
            .all()
        )

        alerts: list[dict[str, Any]] = []
        for item in items:
            proj = proj_map.get(item.ingredient_name, {})
            days_left = proj.get("projected_days_left")
            qty = float(item.quantity_on_hand)
            threshold = float(item.reorder_threshold) if item.reorder_threshold is not None else None

            reasons: list[str] = []
            if days_left is not None and days_left < 7:
                reasons.append(f"projected_days_left={days_left}")
            if threshold is not None and qty < threshold:
                reasons.append(f"qty={qty} < reorder_threshold={threshold}")

            if reasons:
                alerts.append(
                    {
                        "ingredient": item.ingredient_name,
                        "quantity_on_hand": qty,
                        "projected_days_left": days_left,
                        "reorder_threshold": threshold,
                        "reasons": reasons,
                    }
                )
        return alerts

    # ------------------------------------------------------------------
    # Overstock risks
    # ------------------------------------------------------------------

    @staticmethod
    def get_overstock_risks(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Items with projected_days_left > 60."""
        projections = InventoryAnalyticsEngine.get_projected_days_left(db, restaurant_id)
        return [
            p
            for p in projections
            if p["projected_days_left"] is not None and p["projected_days_left"] > 60
        ]

    # ------------------------------------------------------------------
    # Stockout risks
    # ------------------------------------------------------------------

    @staticmethod
    def get_stockout_risks(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Items with projected_days_left < 3."""
        projections = InventoryAnalyticsEngine.get_projected_days_left(db, restaurant_id)
        return [
            p
            for p in projections
            if p["projected_days_left"] is not None and p["projected_days_left"] < 3
        ]

    # ------------------------------------------------------------------
    # Expiry risks
    # ------------------------------------------------------------------

    @staticmethod
    def get_expiry_risks(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Items expiring within 7 days."""
        threshold_date = date.today() + timedelta(days=7)
        items = (
            db.query(InventoryItem)
            .filter(
                InventoryItem.restaurant_id == restaurant_id,
                InventoryItem.expiry_date.isnot(None),
                InventoryItem.expiry_date <= threshold_date,
            )
            .all()
        )
        return [
            {
                "ingredient": item.ingredient_name,
                "quantity_on_hand": float(item.quantity_on_hand),
                "unit": item.unit,
                "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
                "days_until_expiry": (item.expiry_date - date.today()).days
                if item.expiry_date
                else None,
            }
            for item in items
        ]

    # ------------------------------------------------------------------
    # Waste-prone items
    # ------------------------------------------------------------------

    @staticmethod
    def get_waste_prone(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Items that are overstocked AND near expiry, or have very low usage rate."""
        overstock = {
            item["ingredient"] for item in InventoryAnalyticsEngine.get_overstock_risks(db, restaurant_id)
        }
        expiry = {
            item["ingredient"] for item in InventoryAnalyticsEngine.get_expiry_risks(db, restaurant_id)
        }
        projections = InventoryAnalyticsEngine.get_projected_days_left(db, restaurant_id)

        waste_prone: list[dict[str, Any]] = []
        for p in projections:
            reasons: list[str] = []
            name = p["ingredient"]
            if name in overstock and name in expiry:
                reasons.append("overstocked_and_near_expiry")
            elif name in overstock:
                # Check if also near expiry via the set
                pass
            if p["daily_usage"] == 0.0 and p["quantity_on_hand"] > 0:
                reasons.append("zero_usage_with_stock")
            elif p["daily_usage"] > 0 and p["projected_days_left"] is not None and p["projected_days_left"] > 90:
                reasons.append("extremely_low_usage_rate")

            if reasons:
                waste_prone.append({**p, "waste_reasons": reasons})
        return waste_prone

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------

    @classmethod
    def get_full_analysis(
        cls, db: Session, restaurant_id: int
    ) -> dict[str, Any]:
        """Run every inventory-analytics method and return a combined dict."""
        return {
            "ingredient_usage": cls.get_ingredient_usage(db, restaurant_id),
            "projected_days_left": cls.get_projected_days_left(db, restaurant_id),
            "reorder_alerts": cls.get_reorder_alerts(db, restaurant_id),
            "overstock_risks": cls.get_overstock_risks(db, restaurant_id),
            "stockout_risks": cls.get_stockout_risks(db, restaurant_id),
            "expiry_risks": cls.get_expiry_risks(db, restaurant_id),
            "waste_prone": cls.get_waste_prone(db, restaurant_id),
        }
