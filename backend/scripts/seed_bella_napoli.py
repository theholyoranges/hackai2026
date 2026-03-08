"""Seed the Bella Napoli Trattoria dataset into the database as restaurant ID 3."""

import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.models.restaurant import Restaurant
from app.engines.strategy_playbook import seed_strategies
from app.services.csv_parser import (
    parse_menu_csv,
    parse_sales_csv,
    parse_inventory_csv,
    parse_recipe_mapping_csv,
    parse_social_posts_csv,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "bella_napoli")

db = SessionLocal()

try:
    # 1. Create the restaurant
    existing = db.query(Restaurant).filter(Restaurant.name == "Bella Napoli Trattoria").first()
    if existing:
        print(f"Restaurant already exists with ID={existing.id}, deleting and recreating...")
        # Clean up old data
        from app.models.sales_record import SalesRecord
        from app.models.recipe_mapping import RecipeMapping
        from app.models.social_post import SocialPost
        from app.models.inventory_item import InventoryItem
        from app.models.menu_item import MenuItem
        from app.models.recommendation import Recommendation
        from app.models.strategy import StrategyHistory

        rid = existing.id
        db.query(Recommendation).filter(Recommendation.restaurant_id == rid).delete()
        db.query(StrategyHistory).filter(StrategyHistory.restaurant_id == rid).delete()
        db.query(SocialPost).filter(SocialPost.restaurant_id == rid).delete()
        db.query(SalesRecord).filter(SalesRecord.restaurant_id == rid).delete()
        db.query(RecipeMapping).filter(
            RecipeMapping.menu_item_id.in_(
                db.query(MenuItem.id).filter(MenuItem.restaurant_id == rid)
            )
        ).delete(synchronize_session=False)
        db.query(InventoryItem).filter(InventoryItem.restaurant_id == rid).delete()
        db.query(MenuItem).filter(MenuItem.restaurant_id == rid).delete()
        db.delete(existing)
        db.commit()
        print("Old data cleaned up.")

    restaurant = Restaurant(
        name="Bella Napoli Trattoria",
        cuisine_type="Italian",
        location="234 Via Roma, Downtown",
        description="Authentic Italian trattoria serving handmade pasta, wood-fired pizza, and classic dishes with imported ingredients",
        owner_name="Marco Rossi",
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    rid = restaurant.id
    print(f"Created restaurant: {restaurant.name} (ID={rid})")

    # 2. Seed strategies (if not already done)
    new_strategies = seed_strategies(db)
    if new_strategies:
        print(f"Seeded {len(new_strategies)} strategy definitions")

    # 3. Load CSVs
    csv_files = [
        ("menu.csv", parse_menu_csv, "Menu"),
        ("sales.csv", parse_sales_csv, "Sales"),
        ("inventory.csv", parse_inventory_csv, "Inventory"),
        ("recipe_mapping.csv", parse_recipe_mapping_csv, "Recipe Mapping"),
        ("social_posts.csv", parse_social_posts_csv, "Social Posts"),
    ]

    for filename, parser, label in csv_files:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP {label}: {filename} not found")
            continue

        with open(filepath, "rb") as f:
            content = f.read()

        summary = parser(content, rid, db)
        status = "OK" if not summary.errors else f"WARN ({len(summary.errors)} errors)"
        print(f"  {label}: {summary.rows_processed} rows loaded, {summary.rows_failed} failed [{status}]")
        if summary.errors[:3]:
            for err in summary.errors[:3]:
                print(f"    - {err}")

    print(f"\nDone! Bella Napoli Trattoria is restaurant ID={rid}")
    print(f"Visit: http://localhost:3000/dashboard (select restaurant {rid})")

finally:
    db.close()
