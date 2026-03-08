"""Demo seed service -- populates the database with sample restaurants and data."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.engines.strategy_playbook import seed_strategies
from app.models.restaurant import Restaurant
from app.services.csv_parser import (
    parse_inventory_csv,
    parse_menu_csv,
    parse_recipe_mapping_csv,
    parse_sales_csv,
    parse_social_posts_csv,
)

SAMPLE_CSV_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sample_csvs"

DEMO_RESTAURANTS = [
    {
        "name": "The Cozy Bean",
        "cuisine_type": "Cafe",
        "location": "123 Main Street, Portland, OR",
        "description": "A warm neighborhood cafe serving artisan coffee, fresh pastries, and light bites.",
        "owner_name": "Maya Chen",
        "csv_prefix": "cafe",
    },
    {
        "name": "Stack House",
        "cuisine_type": "Burger",
        "location": "456 Oak Avenue, Austin, TX",
        "description": "Gourmet burgers with locally sourced ingredients and craft beverages.",
        "owner_name": "Jordan Rivera",
        "csv_prefix": "burger",
    },
]

CSV_TYPES = [
    ("menu", parse_menu_csv),
    ("sales", parse_sales_csv),
    ("inventory", parse_inventory_csv),
    ("recipe_mapping", parse_recipe_mapping_csv),
    ("social_posts", parse_social_posts_csv),
]


def seed_demo_data(db: Session) -> dict:
    """Seed the database with demo restaurants, CSV data, and the strategy playbook."""
    summary: dict = {"restaurants": [], "strategy_definitions_added": 0}

    summary["strategy_definitions_added"] = len(seed_strategies(db))

    existing_names = {r.name for r in db.query(Restaurant).all()}

    for rdata in DEMO_RESTAURANTS:
        prefix = rdata.pop("csv_prefix")

        if rdata["name"] in existing_names:
            restaurant = db.query(Restaurant).filter(Restaurant.name == rdata["name"]).first()
            summary["restaurants"].append({"name": rdata["name"], "id": restaurant.id, "status": "already_exists"})
            continue

        restaurant = Restaurant(**rdata)
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)

        rest_summary = {"name": restaurant.name, "id": restaurant.id, "status": "created", "csv_results": {}}

        for csv_type, parser_fn in CSV_TYPES:
            csv_path = SAMPLE_CSV_DIR / f"{prefix}_{csv_type}.csv"
            if csv_path.exists():
                content = csv_path.read_bytes()
                result = parser_fn(content, restaurant.id, db)
                rest_summary["csv_results"][csv_type] = {
                    "rows_processed": result.rows_processed,
                    "rows_failed": result.rows_failed,
                    "errors": result.errors[:5],
                }
            else:
                rest_summary["csv_results"][csv_type] = {"error": f"File not found: {csv_path}"}

        summary["restaurants"].append(rest_summary)

    return summary
