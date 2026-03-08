"""Generate recipe mappings from standard recipes (no LLM call needed).

Pulls from the static standard_recipes module. Falls back to GPT-4o only
if a menu item has no standard recipe on file.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem
from app.models.recipe_mapping import RecipeMapping
from app.services.standard_recipes import STANDARD_RECIPES

logger = logging.getLogger(__name__)


@dataclass
class RecipeGenSummary:
    recipes_created: int = 0
    menu_items_processed: int = 0
    menu_items_skipped: int = 0
    errors: list[str] = field(default_factory=list)


def generate_recipes_for_menu(restaurant_id: int, db: Session) -> RecipeGenSummary:
    """Create recipe mappings for all menu items using the standard recipe book."""
    summary = RecipeGenSummary()

    menu_items = (
        db.query(MenuItem)
        .filter(MenuItem.restaurant_id == restaurant_id, MenuItem.is_active == True)
        .all()
    )

    if not menu_items:
        summary.errors.append("No menu items found for this restaurant")
        return summary

    # Delete existing recipe mappings for this restaurant's menu items
    item_ids = [mi.id for mi in menu_items]
    db.query(RecipeMapping).filter(
        RecipeMapping.menu_item_id.in_(item_ids)
    ).delete(synchronize_session=False)

    for mi in menu_items:
        recipe = STANDARD_RECIPES.get(mi.name)
        if recipe is None:
            # Try case-insensitive match
            for key, val in STANDARD_RECIPES.items():
                if key.lower().strip() == mi.name.lower().strip():
                    recipe = val
                    break

        if recipe is None:
            summary.menu_items_skipped += 1
            summary.errors.append(
                f"No standard recipe for '{mi.name}' — skipped"
            )
            continue

        summary.menu_items_processed += 1

        for ing in recipe:
            mapping = RecipeMapping(
                menu_item_id=mi.id,
                ingredient_name=ing["name"],
                quantity_needed=float(ing["quantity"]),
                unit=ing["unit"],
            )
            db.add(mapping)
            summary.recipes_created += 1

    db.commit()
    return summary
