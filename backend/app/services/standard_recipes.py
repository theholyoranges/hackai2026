"""Standard recipe mappings for common restaurant dishes.

Each recipe lists ingredients needed for ONE serving with quantity and unit.
The recipe generator pulls from here instead of calling GPT-4o.
"""

STANDARD_RECIPES: dict[str, list[dict]] = {
    # ── Mains ──────────────────────────────────────────────────────
    "Chicken Tikka Masala": [
        {"name": "Chicken Breast", "quantity": 0.20, "unit": "kg"},
        {"name": "Yogurt", "quantity": 0.05, "unit": "liters"},
        {"name": "Tomatoes", "quantity": 0.15, "unit": "kg"},
        {"name": "Heavy Cream", "quantity": 0.06, "unit": "liters"},
        {"name": "Onions", "quantity": 0.08, "unit": "kg"},
        {"name": "Ginger-Garlic Paste", "quantity": 0.01, "unit": "kg"},
        {"name": "Butter", "quantity": 0.02, "unit": "kg"},
        {"name": "Garam Masala", "quantity": 3.0, "unit": "grams"},
        {"name": "Turmeric Powder", "quantity": 2.0, "unit": "grams"},
        {"name": "Cumin Seeds", "quantity": 2.0, "unit": "grams"},
        {"name": "Basmati Rice", "quantity": 0.10, "unit": "kg"},
        {"name": "Cooking Oil", "quantity": 0.02, "unit": "liters"},
    ],
    "Lamb Biryani": [
        {"name": "Lamb Leg", "quantity": 0.20, "unit": "kg"},
        {"name": "Basmati Rice", "quantity": 0.15, "unit": "kg"},
        {"name": "Onions", "quantity": 0.10, "unit": "kg"},
        {"name": "Yogurt", "quantity": 0.04, "unit": "liters"},
        {"name": "Ginger-Garlic Paste", "quantity": 0.01, "unit": "kg"},
        {"name": "Saffron", "quantity": 0.10, "unit": "grams"},
        {"name": "Ghee", "quantity": 0.03, "unit": "liters"},
        {"name": "Garam Masala", "quantity": 3.0, "unit": "grams"},
        {"name": "Cumin Seeds", "quantity": 2.0, "unit": "grams"},
        {"name": "Mint Leaves", "quantity": 0.10, "unit": "bunches"},
        {"name": "Green Chillies", "quantity": 2.0, "unit": "pieces"},
    ],
    "Dal Makhani": [
        {"name": "Black Lentils", "quantity": 0.08, "unit": "kg"},
        {"name": "Butter", "quantity": 0.03, "unit": "kg"},
        {"name": "Heavy Cream", "quantity": 0.05, "unit": "liters"},
        {"name": "Tomatoes", "quantity": 0.10, "unit": "kg"},
        {"name": "Onions", "quantity": 0.06, "unit": "kg"},
        {"name": "Ginger-Garlic Paste", "quantity": 0.01, "unit": "kg"},
        {"name": "Garam Masala", "quantity": 2.0, "unit": "grams"},
        {"name": "Cumin Seeds", "quantity": 2.0, "unit": "grams"},
        {"name": "Cooking Oil", "quantity": 0.01, "unit": "liters"},
    ],
    "Palak Paneer": [
        {"name": "Fresh Spinach", "quantity": 0.15, "unit": "kg"},
        {"name": "Paneer", "quantity": 0.10, "unit": "kg"},
        {"name": "Onions", "quantity": 0.06, "unit": "kg"},
        {"name": "Tomatoes", "quantity": 0.05, "unit": "kg"},
        {"name": "Ginger-Garlic Paste", "quantity": 0.01, "unit": "kg"},
        {"name": "Heavy Cream", "quantity": 0.03, "unit": "liters"},
        {"name": "Cumin Seeds", "quantity": 2.0, "unit": "grams"},
        {"name": "Garam Masala", "quantity": 2.0, "unit": "grams"},
        {"name": "Cooking Oil", "quantity": 0.02, "unit": "liters"},
        {"name": "Green Chillies", "quantity": 1.0, "unit": "pieces"},
    ],
    "Tandoori Chicken": [
        {"name": "Chicken Breast", "quantity": 0.25, "unit": "kg"},
        {"name": "Yogurt", "quantity": 0.06, "unit": "liters"},
        {"name": "Ginger-Garlic Paste", "quantity": 0.01, "unit": "kg"},
        {"name": "Turmeric Powder", "quantity": 2.0, "unit": "grams"},
        {"name": "Garam Masala", "quantity": 3.0, "unit": "grams"},
        {"name": "Lemon", "quantity": 0.50, "unit": "pieces"},
        {"name": "Cooking Oil", "quantity": 0.02, "unit": "liters"},
        {"name": "Onions", "quantity": 0.05, "unit": "kg"},
    ],
    "Fish Curry": [
        {"name": "Fish Fillets", "quantity": 0.18, "unit": "kg"},
        {"name": "Coconut Milk", "quantity": 0.50, "unit": "cans"},
        {"name": "Tomatoes", "quantity": 0.10, "unit": "kg"},
        {"name": "Onions", "quantity": 0.08, "unit": "kg"},
        {"name": "Ginger-Garlic Paste", "quantity": 0.01, "unit": "kg"},
        {"name": "Turmeric Powder", "quantity": 2.0, "unit": "grams"},
        {"name": "Cumin Seeds", "quantity": 2.0, "unit": "grams"},
        {"name": "Cooking Oil", "quantity": 0.02, "unit": "liters"},
        {"name": "Curry Leaves", "quantity": 3.0, "unit": "pieces"},
    ],
    # ── Starters ───────────────────────────────────────────────────
    "Paneer Tikka": [
        {"name": "Paneer", "quantity": 0.12, "unit": "kg"},
        {"name": "Yogurt", "quantity": 0.03, "unit": "liters"},
        {"name": "Bell Peppers", "quantity": 0.05, "unit": "kg"},
        {"name": "Onions", "quantity": 0.05, "unit": "kg"},
        {"name": "Ginger-Garlic Paste", "quantity": 0.005, "unit": "kg"},
        {"name": "Garam Masala", "quantity": 2.0, "unit": "grams"},
        {"name": "Cooking Oil", "quantity": 0.02, "unit": "liters"},
        {"name": "Lemon", "quantity": 0.25, "unit": "pieces"},
    ],
    "Samosa": [
        {"name": "All-Purpose Flour", "quantity": 0.06, "unit": "kg"},
        {"name": "Potatoes", "quantity": 0.08, "unit": "kg"},
        {"name": "Green Peas", "quantity": 0.03, "unit": "kg"},
        {"name": "Cumin Seeds", "quantity": 2.0, "unit": "grams"},
        {"name": "Garam Masala", "quantity": 1.0, "unit": "grams"},
        {"name": "Cooking Oil", "quantity": 0.10, "unit": "liters"},
        {"name": "Green Chillies", "quantity": 1.0, "unit": "pieces"},
    ],
    # ── Breads ─────────────────────────────────────────────────────
    "Butter Naan": [
        {"name": "All-Purpose Flour", "quantity": 0.08, "unit": "kg"},
        {"name": "Yogurt", "quantity": 0.02, "unit": "liters"},
        {"name": "Butter", "quantity": 0.015, "unit": "kg"},
        {"name": "Whole Milk", "quantity": 0.02, "unit": "liters"},
        {"name": "Cooking Oil", "quantity": 0.005, "unit": "liters"},
    ],
    "Garlic Naan": [
        {"name": "All-Purpose Flour", "quantity": 0.08, "unit": "kg"},
        {"name": "Yogurt", "quantity": 0.02, "unit": "liters"},
        {"name": "Butter", "quantity": 0.015, "unit": "kg"},
        {"name": "Garlic", "quantity": 0.01, "unit": "kg"},
        {"name": "Whole Milk", "quantity": 0.02, "unit": "liters"},
        {"name": "Cilantro", "quantity": 3.0, "unit": "grams"},
    ],
    # ── Sides ──────────────────────────────────────────────────────
    "Aloo Gobi": [
        {"name": "Cauliflower", "quantity": 0.25, "unit": "heads"},
        {"name": "Potatoes", "quantity": 0.10, "unit": "kg"},
        {"name": "Onions", "quantity": 0.05, "unit": "kg"},
        {"name": "Tomatoes", "quantity": 0.05, "unit": "kg"},
        {"name": "Turmeric Powder", "quantity": 2.0, "unit": "grams"},
        {"name": "Cumin Seeds", "quantity": 2.0, "unit": "grams"},
        {"name": "Cooking Oil", "quantity": 0.02, "unit": "liters"},
        {"name": "Green Chillies", "quantity": 1.0, "unit": "pieces"},
    ],
    "Raita": [
        {"name": "Yogurt", "quantity": 0.10, "unit": "liters"},
        {"name": "Cucumber", "quantity": 0.50, "unit": "pieces"},
        {"name": "Mint Leaves", "quantity": 0.05, "unit": "bunches"},
        {"name": "Cumin Seeds", "quantity": 1.0, "unit": "grams"},
    ],
    # ── Drinks ─────────────────────────────────────────────────────
    "Mango Lassi": [
        {"name": "Yogurt", "quantity": 0.10, "unit": "liters"},
        {"name": "Mango Pulp", "quantity": 0.08, "unit": "liters"},
        {"name": "Whole Milk", "quantity": 0.05, "unit": "liters"},
        {"name": "Sugar", "quantity": 10.0, "unit": "grams"},
        {"name": "Cardamom", "quantity": 1.0, "unit": "grams"},
    ],
    "Masala Chai": [
        {"name": "Black Tea", "quantity": 0.005, "unit": "kg"},
        {"name": "Whole Milk", "quantity": 0.15, "unit": "liters"},
        {"name": "Sugar", "quantity": 10.0, "unit": "grams"},
        {"name": "Cardamom", "quantity": 1.0, "unit": "grams"},
        {"name": "Ginger-Garlic Paste", "quantity": 0.003, "unit": "kg"},
    ],
    # ── Desserts ───────────────────────────────────────────────────
    "Gulab Jamun": [
        {"name": "Whole Milk", "quantity": 0.05, "unit": "liters"},
        {"name": "All-Purpose Flour", "quantity": 0.02, "unit": "kg"},
        {"name": "Sugar", "quantity": 30.0, "unit": "grams"},
        {"name": "Cardamom", "quantity": 1.0, "unit": "grams"},
        {"name": "Rose Water", "quantity": 5.0, "unit": "ml"},
        {"name": "Ghee", "quantity": 0.02, "unit": "liters"},
        {"name": "Cooking Oil", "quantity": 0.05, "unit": "liters"},
    ],
    "Kheer": [
        {"name": "Whole Milk", "quantity": 0.20, "unit": "liters"},
        {"name": "Basmati Rice", "quantity": 0.03, "unit": "kg"},
        {"name": "Sugar", "quantity": 25.0, "unit": "grams"},
        {"name": "Cardamom", "quantity": 1.0, "unit": "grams"},
        {"name": "Saffron", "quantity": 0.05, "unit": "grams"},
        {"name": "Pistachios", "quantity": 5.0, "unit": "grams"},
    ],
}


def get_recipe_for_item(menu_item_name: str) -> list[dict] | None:
    """Return standard recipe for a menu item, or None if not found."""
    return STANDARD_RECIPES.get(menu_item_name)


def get_all_ingredient_names() -> set[str]:
    """Return the set of all unique ingredient names across all recipes."""
    names: set[str] = set()
    for ingredients in STANDARD_RECIPES.values():
        for ing in ingredients:
            names.add(ing["name"])
    return names
