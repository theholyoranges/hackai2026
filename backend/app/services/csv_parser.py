"""CSV parsing service for ingesting restaurant data from uploaded files."""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.menu_item import MenuItem
from app.models.recipe_mapping import RecipeMapping
from app.models.sales_record import SalesRecord
from app.models.social_post import SocialPost


@dataclass
class IngestionSummary:
    """Result of a CSV parsing operation."""

    rows_processed: int = 0
    rows_failed: int = 0
    errors: list[str] = field(default_factory=list)


# ------------------------------------------------------------------
# Column name normalisation helpers
# ------------------------------------------------------------------

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and strip whitespace from column names."""
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _read_csv_bytes(file_content: bytes) -> pd.DataFrame:
    """Read CSV bytes into a pandas DataFrame."""
    return pd.read_csv(io.BytesIO(file_content))


# ------------------------------------------------------------------
# Menu items
# ------------------------------------------------------------------

MENU_REQUIRED_COLS = {"name", "category", "price"}


def parse_menu_csv(file_content: bytes, restaurant_id: int, db: Session) -> IngestionSummary:
    """Parse a menu items CSV and bulk-insert into the database."""
    summary = IngestionSummary()
    try:
        df = _normalize_columns(_read_csv_bytes(file_content))
    except Exception as exc:
        summary.errors.append(f"Failed to read CSV: {exc}")
        return summary

    missing = MENU_REQUIRED_COLS - set(df.columns)
    if missing:
        summary.errors.append(f"Missing required columns: {missing}")
        return summary

    for idx, row in df.iterrows():
        try:
            name = str(row["name"]).strip()
            if not name or name.lower() == "nan":
                raise ValueError("Empty name")

            price = float(row["price"])
            ingredient_cost = float(row["ingredient_cost"]) if pd.notna(row.get("ingredient_cost")) else None
            is_active = str(row.get("is_active", "true")).strip().lower() in ("true", "1", "yes")

            item = MenuItem(
                restaurant_id=restaurant_id,
                name=name,
                category=str(row.get("category", "")).strip() or None,
                price=price,
                ingredient_cost=ingredient_cost,
                description=str(row.get("description", "")).strip() or None,
                is_active=is_active,
            )
            db.add(item)
            summary.rows_processed += 1
        except Exception as exc:
            summary.rows_failed += 1
            summary.errors.append(f"Row {idx + 1}: {exc}")

    if summary.rows_processed > 0:
        db.commit()

    return summary


# ------------------------------------------------------------------
# Sales records
# ------------------------------------------------------------------

SALES_REQUIRED_COLS = {"menu_item_name", "quantity", "total_price", "sale_date"}


def parse_sales_csv(file_content: bytes, restaurant_id: int, db: Session) -> IngestionSummary:
    """Parse a sales records CSV and bulk-insert into the database."""
    summary = IngestionSummary()
    try:
        df = _normalize_columns(_read_csv_bytes(file_content))
    except Exception as exc:
        summary.errors.append(f"Failed to read CSV: {exc}")
        return summary

    missing = SALES_REQUIRED_COLS - set(df.columns)
    if missing:
        summary.errors.append(f"Missing required columns: {missing}")
        return summary

    # Build menu item lookup
    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()
    item_lookup: dict[str, int] = {mi.name.lower().strip(): mi.id for mi in menu_items}

    for idx, row in df.iterrows():
        try:
            item_name = str(row["menu_item_name"]).strip().lower()
            menu_item_id = item_lookup.get(item_name)
            if menu_item_id is None:
                raise ValueError(f"Menu item '{row['menu_item_name']}' not found")

            sale_date = pd.to_datetime(row["sale_date"])
            quantity = int(row["quantity"])
            total_price = float(row["total_price"])

            day_of_week = sale_date.strftime("%A") if pd.notna(row.get("day_of_week")) is False or pd.isna(row.get("day_of_week")) else str(row.get("day_of_week", "")).strip()
            if not day_of_week or day_of_week.lower() == "nan":
                day_of_week = sale_date.strftime("%A")

            hour_of_day = int(row["hour_of_day"]) if pd.notna(row.get("hour_of_day")) else sale_date.hour

            record = SalesRecord(
                restaurant_id=restaurant_id,
                menu_item_id=menu_item_id,
                quantity=quantity,
                total_price=total_price,
                order_id=str(row.get("order_id", "")).strip() or None,
                sale_date=sale_date,
                day_of_week=day_of_week,
                hour_of_day=hour_of_day,
            )
            db.add(record)
            summary.rows_processed += 1
        except Exception as exc:
            summary.rows_failed += 1
            summary.errors.append(f"Row {idx + 1}: {exc}")

    if summary.rows_processed > 0:
        db.commit()

    return summary


# ------------------------------------------------------------------
# Inventory items
# ------------------------------------------------------------------

INVENTORY_REQUIRED_COLS = {"ingredient_name", "unit", "quantity_on_hand"}


def parse_inventory_csv(file_content: bytes, restaurant_id: int, db: Session) -> IngestionSummary:
    """Parse an inventory items CSV and bulk-insert into the database."""
    summary = IngestionSummary()
    try:
        df = _normalize_columns(_read_csv_bytes(file_content))
    except Exception as exc:
        summary.errors.append(f"Failed to read CSV: {exc}")
        return summary

    missing = INVENTORY_REQUIRED_COLS - set(df.columns)
    if missing:
        summary.errors.append(f"Missing required columns: {missing}")
        return summary

    for idx, row in df.iterrows():
        try:
            ingredient_name = str(row["ingredient_name"]).strip()
            if not ingredient_name or ingredient_name.lower() == "nan":
                raise ValueError("Empty ingredient name")

            expiry_date = None
            if pd.notna(row.get("expiry_date")):
                raw = str(row["expiry_date"]).strip()
                if raw and raw.lower() != "nan":
                    expiry_date = pd.to_datetime(raw).date()

            item = InventoryItem(
                restaurant_id=restaurant_id,
                ingredient_name=ingredient_name,
                unit=str(row["unit"]).strip(),
                quantity_on_hand=float(row["quantity_on_hand"]),
                reorder_threshold=float(row["reorder_threshold"]) if pd.notna(row.get("reorder_threshold")) else None,
                unit_cost=float(row["unit_cost"]) if pd.notna(row.get("unit_cost")) else None,
                expiry_date=expiry_date,
                supplier=str(row.get("supplier", "")).strip() or None,
            )
            db.add(item)
            summary.rows_processed += 1
        except Exception as exc:
            summary.rows_failed += 1
            summary.errors.append(f"Row {idx + 1}: {exc}")

    if summary.rows_processed > 0:
        db.commit()

    return summary


# ------------------------------------------------------------------
# Recipe mappings
# ------------------------------------------------------------------

RECIPE_REQUIRED_COLS = {"menu_item_name", "ingredient_name", "quantity_needed", "unit"}


def parse_recipe_mapping_csv(file_content: bytes, restaurant_id: int, db: Session) -> IngestionSummary:
    """Parse a recipe mapping CSV and bulk-insert into the database."""
    summary = IngestionSummary()
    try:
        df = _normalize_columns(_read_csv_bytes(file_content))
    except Exception as exc:
        summary.errors.append(f"Failed to read CSV: {exc}")
        return summary

    missing = RECIPE_REQUIRED_COLS - set(df.columns)
    if missing:
        summary.errors.append(f"Missing required columns: {missing}")
        return summary

    # Build menu item lookup
    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()
    item_lookup: dict[str, int] = {mi.name.lower().strip(): mi.id for mi in menu_items}

    for idx, row in df.iterrows():
        try:
            item_name = str(row["menu_item_name"]).strip().lower()
            menu_item_id = item_lookup.get(item_name)
            if menu_item_id is None:
                raise ValueError(f"Menu item '{row['menu_item_name']}' not found")

            mapping = RecipeMapping(
                menu_item_id=menu_item_id,
                ingredient_name=str(row["ingredient_name"]).strip(),
                quantity_needed=float(row["quantity_needed"]),
                unit=str(row["unit"]).strip(),
            )
            db.add(mapping)
            summary.rows_processed += 1
        except Exception as exc:
            summary.rows_failed += 1
            summary.errors.append(f"Row {idx + 1}: {exc}")

    if summary.rows_processed > 0:
        db.commit()

    return summary


# ------------------------------------------------------------------
# Social posts
# ------------------------------------------------------------------

SOCIAL_REQUIRED_COLS = {"platform", "posted_at"}


def parse_social_posts_csv(file_content: bytes, restaurant_id: int, db: Session) -> IngestionSummary:
    """Parse a social posts CSV and bulk-insert into the database."""
    summary = IngestionSummary()
    try:
        df = _normalize_columns(_read_csv_bytes(file_content))
    except Exception as exc:
        summary.errors.append(f"Failed to read CSV: {exc}")
        return summary

    missing = SOCIAL_REQUIRED_COLS - set(df.columns)
    if missing:
        summary.errors.append(f"Missing required columns: {missing}")
        return summary

    # Optional menu item lookup
    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()
    item_lookup: dict[str, int] = {mi.name.lower().strip(): mi.id for mi in menu_items}

    for idx, row in df.iterrows():
        try:
            menu_item_id = None
            if pd.notna(row.get("menu_item_name")):
                name = str(row["menu_item_name"]).strip().lower()
                menu_item_id = item_lookup.get(name)

            posted_at = pd.to_datetime(row["posted_at"])

            post = SocialPost(
                restaurant_id=restaurant_id,
                menu_item_id=menu_item_id,
                platform=str(row["platform"]).strip(),
                post_type=str(row.get("post_type", "")).strip() or None,
                content_summary=str(row.get("content_summary", "")).strip() or None,
                posted_at=posted_at,
                likes=int(row["likes"]) if pd.notna(row.get("likes")) else 0,
                comments=int(row["comments"]) if pd.notna(row.get("comments")) else 0,
                shares=int(row["shares"]) if pd.notna(row.get("shares")) else 0,
                reach=int(row["reach"]) if pd.notna(row.get("reach")) else 0,
            )
            db.add(post)
            summary.rows_processed += 1
        except Exception as exc:
            summary.rows_failed += 1
            summary.errors.append(f"Row {idx + 1}: {exc}")

    if summary.rows_processed > 0:
        db.commit()

    return summary
