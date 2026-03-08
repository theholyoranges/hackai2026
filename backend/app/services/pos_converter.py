"""Convert standard POS-export CSV to our internal sales format."""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem
from app.models.sales_record import SalesRecord


@dataclass
class ConversionSummary:
    rows_processed: int = 0
    rows_failed: int = 0
    errors: list[str] = field(default_factory=list)


# Common POS column name variants → our internal names
_COL_ALIASES = {
    # Transaction / Order ID
    "transaction_id": "order_id",
    "transaction id": "order_id",
    "txn_id": "order_id",
    "order_id": "order_id",
    "order_number": "order_id",
    "receipt_number": "order_id",
    "receipt_id": "order_id",
    # Item name
    "item_name": "item_name",
    "item name": "item_name",
    "product_name": "item_name",
    "product": "item_name",
    "menu_item": "item_name",
    "description": "item_name",
    # Quantity
    "qty": "quantity",
    "quantity": "quantity",
    "count": "quantity",
    # Price
    "unit_price": "unit_price",
    "unit price": "unit_price",
    "price": "unit_price",
    "item_price": "unit_price",
    # Line total
    "line_total": "line_total",
    "line total": "line_total",
    "total": "line_total",
    "amount": "line_total",
    "subtotal": "line_total",
    # Date
    "date": "date",
    "sale_date": "date",
    "order_date": "date",
    "transaction_date": "date",
    # Time
    "time": "time",
    "order_time": "time",
    "transaction_time": "time",
}


def _map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map POS column names to our standard names."""
    # Lowercase + strip
    df.columns = [c.strip().lower() for c in df.columns]

    rename = {}
    for original_col in df.columns:
        normalized = original_col.replace(" ", "_")
        if normalized in _COL_ALIASES:
            rename[original_col] = _COL_ALIASES[normalized]
        elif original_col in _COL_ALIASES:
            rename[original_col] = _COL_ALIASES[original_col]

    df = df.rename(columns=rename)
    return df


def convert_pos_csv(file_content: bytes, restaurant_id: int, db: Session) -> ConversionSummary:
    """Accept a POS-style CSV and insert as SalesRecords."""
    summary = ConversionSummary()

    try:
        df = pd.read_csv(io.BytesIO(file_content))
        df = _map_columns(df)
    except Exception as exc:
        summary.errors.append(f"Failed to read CSV: {exc}")
        return summary

    # We need at minimum: item_name and (quantity or line_total) and date
    if "item_name" not in df.columns:
        summary.errors.append(
            f"Could not find an item name column. Found columns: {list(df.columns)}"
        )
        return summary

    if "date" not in df.columns:
        summary.errors.append(
            f"Could not find a date column. Found columns: {list(df.columns)}"
        )
        return summary

    # Build menu item lookup
    menu_items = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()
    item_lookup: dict[str, MenuItem] = {mi.name.lower().strip(): mi for mi in menu_items}

    if not item_lookup:
        summary.errors.append("No menu items found. Please upload the menu CSV first.")
        return summary

    for idx, row in df.iterrows():
        try:
            raw_name = str(row["item_name"]).strip()
            mi = item_lookup.get(raw_name.lower())
            if mi is None:
                raise ValueError(f"Menu item '{raw_name}' not found in uploaded menu")

            # Parse date (handles MM/DD/YYYY, YYYY-MM-DD, etc.)
            sale_dt = pd.to_datetime(row["date"])

            # Parse time if available and merge into sale_dt
            if "time" in df.columns and pd.notna(row.get("time")):
                try:
                    time_str = str(row["time"]).strip()
                    parsed_time = pd.to_datetime(time_str).time()
                    sale_dt = sale_dt.replace(
                        hour=parsed_time.hour,
                        minute=parsed_time.minute,
                        second=parsed_time.second,
                    )
                except Exception:
                    pass  # keep date-only

            # Quantity
            qty = int(row["quantity"]) if "quantity" in df.columns and pd.notna(row.get("quantity")) else 1

            # Total price: prefer line_total, else unit_price * qty, else menu price * qty
            if "line_total" in df.columns and pd.notna(row.get("line_total")):
                total_price = float(row["line_total"])
            elif "unit_price" in df.columns and pd.notna(row.get("unit_price")):
                total_price = float(row["unit_price"]) * qty
            else:
                total_price = float(mi.price) * qty

            order_id = str(row["order_id"]).strip() if "order_id" in df.columns and pd.notna(row.get("order_id")) else None
            day_of_week = sale_dt.strftime("%A")
            hour_of_day = sale_dt.hour

            record = SalesRecord(
                restaurant_id=restaurant_id,
                menu_item_id=mi.id,
                quantity=qty,
                total_price=total_price,
                order_id=order_id,
                sale_date=sale_dt,
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
