"""Generate a comprehensive, realistic restaurant dataset for Bella Napoli Trattoria."""

import csv
import os
import random
from datetime import datetime, timedelta, date

random.seed(42)
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "bella_napoli")
os.makedirs(OUT_DIR, exist_ok=True)

# =====================================================================
# 1. MENU — 35 items across 7 categories
# =====================================================================
MENU = [
    # Antipasti
    {"name": "Bruschetta Trio", "category": "Antipasti", "price": 12.50, "ingredient_cost": 3.80, "description": "Tomato basil, mushroom truffle, and nduja spread on grilled ciabatta"},
    {"name": "Burrata Caprese", "category": "Antipasti", "price": 16.00, "ingredient_cost": 5.50, "description": "Creamy burrata with heirloom tomatoes, basil oil, and aged balsamic"},
    {"name": "Calamari Fritti", "category": "Antipasti", "price": 14.00, "ingredient_cost": 4.20, "description": "Crispy fried calamari with marinara and lemon aioli"},
    {"name": "Arancini", "category": "Antipasti", "price": 11.00, "ingredient_cost": 2.80, "description": "Golden risotto balls stuffed with mozzarella and peas"},
    {"name": "Carpaccio di Manzo", "category": "Antipasti", "price": 17.00, "ingredient_cost": 6.50, "description": "Thinly sliced beef tenderloin with arugula, capers, and shaved Parmigiano"},

    # Pasta
    {"name": "Spaghetti Carbonara", "category": "Pasta", "price": 19.00, "ingredient_cost": 4.50, "description": "Classic Roman carbonara with guanciale, egg yolk, and Pecorino Romano"},
    {"name": "Penne Arrabbiata", "category": "Pasta", "price": 16.00, "ingredient_cost": 3.20, "description": "Penne in spicy tomato sauce with garlic and fresh chili"},
    {"name": "Fettuccine Alfredo", "category": "Pasta", "price": 18.00, "ingredient_cost": 4.00, "description": "House-made fettuccine in creamy Parmigiano butter sauce"},
    {"name": "Linguine alle Vongole", "category": "Pasta", "price": 22.00, "ingredient_cost": 7.80, "description": "Linguine with fresh clams, white wine, garlic, and parsley"},
    {"name": "Rigatoni Bolognese", "category": "Pasta", "price": 20.00, "ingredient_cost": 5.50, "description": "Slow-simmered beef and pork ragu with San Marzano tomatoes"},
    {"name": "Cacio e Pepe", "category": "Pasta", "price": 17.00, "ingredient_cost": 3.00, "description": "Tonnarelli pasta with Pecorino Romano and cracked black pepper"},
    {"name": "Lobster Ravioli", "category": "Pasta", "price": 28.00, "ingredient_cost": 11.00, "description": "House-made ravioli filled with Maine lobster in saffron cream"},

    # Pizza
    {"name": "Margherita Pizza", "category": "Pizza", "price": 16.00, "ingredient_cost": 3.50, "description": "San Marzano tomato, fresh mozzarella, basil, extra virgin olive oil"},
    {"name": "Diavola Pizza", "category": "Pizza", "price": 18.00, "ingredient_cost": 4.50, "description": "Spicy salami, mozzarella, roasted peppers, and chili oil"},
    {"name": "Quattro Formaggi", "category": "Pizza", "price": 19.00, "ingredient_cost": 5.50, "description": "Mozzarella, gorgonzola, fontina, and Parmigiano Reggiano"},
    {"name": "Prosciutto e Rucola", "category": "Pizza", "price": 20.00, "ingredient_cost": 6.00, "description": "Prosciutto di Parma, arugula, shaved Parmigiano, truffle oil"},
    {"name": "Pizza Bianca", "category": "Pizza", "price": 17.00, "ingredient_cost": 4.00, "description": "White pizza with ricotta, roasted garlic, spinach, and mozzarella"},

    # Secondi (Mains)
    {"name": "Chicken Parmigiana", "category": "Secondi", "price": 24.00, "ingredient_cost": 6.50, "description": "Breaded chicken breast with marinara, mozzarella, and spaghetti"},
    {"name": "Veal Piccata", "category": "Secondi", "price": 29.00, "ingredient_cost": 10.00, "description": "Pan-seared veal medallions in lemon-caper butter sauce"},
    {"name": "Branzino al Forno", "category": "Secondi", "price": 32.00, "ingredient_cost": 12.50, "description": "Oven-roasted whole Mediterranean sea bass with herbs and lemon"},
    {"name": "Osso Buco", "category": "Secondi", "price": 34.00, "ingredient_cost": 13.00, "description": "Braised veal shank with saffron risotto and gremolata"},
    {"name": "Eggplant Parmigiana", "category": "Secondi", "price": 18.00, "ingredient_cost": 4.00, "description": "Layers of fried eggplant, marinara, mozzarella, and basil"},

    # Insalate
    {"name": "Caesar Salad", "category": "Insalate", "price": 13.00, "ingredient_cost": 3.00, "description": "Romaine hearts, house-made Caesar dressing, croutons, shaved Parmigiano"},
    {"name": "Insalata Mista", "category": "Insalate", "price": 11.00, "ingredient_cost": 2.50, "description": "Mixed greens, cherry tomatoes, cucumber, red onion, balsamic vinaigrette"},
    {"name": "Panzanella", "category": "Insalate", "price": 14.00, "ingredient_cost": 3.50, "description": "Tuscan bread salad with tomatoes, cucumber, red onion, and basil"},

    # Dolci (Desserts)
    {"name": "Tiramisu", "category": "Dolci", "price": 12.00, "ingredient_cost": 3.50, "description": "Classic layered mascarpone, espresso-soaked ladyfingers, cocoa"},
    {"name": "Panna Cotta", "category": "Dolci", "price": 10.00, "ingredient_cost": 2.20, "description": "Vanilla bean panna cotta with seasonal berry compote"},
    {"name": "Cannoli", "category": "Dolci", "price": 9.00, "ingredient_cost": 2.00, "description": "Crispy shells filled with sweet ricotta, chocolate chips, pistachios"},
    {"name": "Affogato", "category": "Dolci", "price": 8.00, "ingredient_cost": 1.80, "description": "Vanilla gelato drowned in a shot of hot espresso"},
    {"name": "Chocolate Lava Cake", "category": "Dolci", "price": 13.00, "ingredient_cost": 3.80, "description": "Warm dark chocolate fondant with vanilla gelato"},

    # Bevande (Drinks)
    {"name": "Espresso", "category": "Bevande", "price": 4.00, "ingredient_cost": 0.40, "description": "Double shot of house-roasted espresso"},
    {"name": "Cappuccino", "category": "Bevande", "price": 5.50, "ingredient_cost": 0.80, "description": "Double espresso with steamed milk foam"},
    {"name": "Aperol Spritz", "category": "Bevande", "price": 14.00, "ingredient_cost": 3.50, "description": "Aperol, prosecco, soda water, orange slice"},
    {"name": "House Red Wine", "category": "Bevande", "price": 12.00, "ingredient_cost": 3.00, "description": "Glass of Montepulciano d'Abruzzo"},
    {"name": "Limoncello", "category": "Bevande", "price": 9.00, "ingredient_cost": 1.50, "description": "Chilled house-made limoncello digestivo"},
]

# Popularity weights (higher = more ordered)
POPULARITY = {
    "Margherita Pizza": 1.8, "Spaghetti Carbonara": 1.6, "Chicken Parmigiana": 1.5,
    "Fettuccine Alfredo": 1.3, "Tiramisu": 1.4, "Bruschetta Trio": 1.2,
    "Caesar Salad": 1.3, "Penne Arrabbiata": 1.1, "Rigatoni Bolognese": 1.2,
    "Diavola Pizza": 1.3, "Aperol Spritz": 1.5, "House Red Wine": 1.4,
    "Espresso": 1.6, "Cappuccino": 1.3, "Calamari Fritti": 1.1,
    "Burrata Caprese": 1.0, "Prosciutto e Rucola": 0.9, "Cannoli": 1.1,
    "Arancini": 0.8, "Cacio e Pepe": 1.0, "Affogato": 0.9,
    "Panna Cotta": 0.8, "Quattro Formaggi": 0.7, "Pizza Bianca": 0.6,
    "Lobster Ravioli": 0.5, "Linguine alle Vongole": 0.6, "Veal Piccata": 0.4,
    "Branzino al Forno": 0.35, "Osso Buco": 0.3, "Eggplant Parmigiana": 0.7,
    "Insalata Mista": 0.6, "Panzanella": 0.4, "Chocolate Lava Cake": 0.8,
    "Limoncello": 0.9, "Carpaccio di Manzo": 0.5,
}

# Weekend boost factor
WEEKEND_BOOST = 1.6
# Time-of-day weights (lunch 11-14, dinner 17-22)
HOUR_WEIGHTS = {
    11: 0.6, 12: 1.0, 13: 1.0, 14: 0.7,
    17: 0.5, 18: 1.0, 19: 1.3, 20: 1.3, 21: 1.0, 22: 0.5,
}

# Write menu CSV
with open(os.path.join(OUT_DIR, "menu.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "category", "price", "ingredient_cost", "description", "is_active"])
    writer.writeheader()
    for item in MENU:
        writer.writerow({**item, "is_active": "true"})

print(f"Menu: {len(MENU)} items")

# =====================================================================
# 2. SALES — Full month (Feb 5 - Mar 6, 2026) — ~15,000 transactions
# =====================================================================
START_DATE = date(2026, 2, 5)
END_DATE = date(2026, 3, 6)
DAYS = (END_DATE - START_DATE).days + 1

# Items commonly ordered together (for realistic order_ids)
PAIR_AFFINITIES = [
    (["Bruschetta Trio", "Spaghetti Carbonara", "House Red Wine"], 0.08),
    (["Caesar Salad", "Chicken Parmigiana", "Espresso"], 0.07),
    (["Margherita Pizza", "Aperol Spritz"], 0.10),
    (["Calamari Fritti", "Linguine alle Vongole", "House Red Wine"], 0.04),
    (["Burrata Caprese", "Rigatoni Bolognese", "Tiramisu"], 0.05),
    (["Diavola Pizza", "Aperol Spritz", "Cannoli"], 0.06),
    (["Fettuccine Alfredo", "Caesar Salad", "Cappuccino"], 0.06),
    (["Penne Arrabbiata", "Insalata Mista", "Affogato"], 0.04),
    (["Prosciutto e Rucola", "House Red Wine", "Panna Cotta"], 0.04),
    (["Cacio e Pepe", "Bruschetta Trio", "Limoncello"], 0.04),
    (["Chicken Parmigiana", "House Red Wine", "Tiramisu"], 0.05),
    (["Margherita Pizza", "Caesar Salad"], 0.06),
]

sales_rows = []
order_counter = 1

for day_offset in range(DAYS):
    current_date = START_DATE + timedelta(days=day_offset)
    is_weekend = current_date.weekday() >= 4  # Fri, Sat, Sun
    day_name = current_date.strftime("%A")

    # Generate orders for each service hour
    for hour, hour_weight in HOUR_WEIGHTS.items():
        base_orders = int(8 * hour_weight * (WEEKEND_BOOST if is_weekend else 1.0))
        num_orders = max(1, base_orders + random.randint(-2, 3))

        for _ in range(num_orders):
            order_id = f"ORD-{order_counter:05d}"
            order_counter += 1

            # Decide items in this order: 1-4 items
            order_items = []

            # Check if this order follows a common pattern
            if random.random() < 0.35:
                # Pick an affinity group
                chosen_pair = random.choices(
                    PAIR_AFFINITIES,
                    weights=[p[1] for p in PAIR_AFFINITIES],
                    k=1
                )[0]
                order_items = list(chosen_pair[0])
            else:
                # Random items weighted by popularity
                num_items = random.choices([1, 2, 3, 4], weights=[0.15, 0.40, 0.30, 0.15])[0]
                candidates = list(POPULARITY.keys())
                weights = [POPULARITY[c] for c in candidates]
                chosen = random.choices(candidates, weights=weights, k=num_items)
                order_items = list(set(chosen))  # deduplicate

            # Maybe add a drink if not already present
            drinks = {"Espresso", "Cappuccino", "Aperol Spritz", "House Red Wine", "Limoncello"}
            if not any(i in drinks for i in order_items) and random.random() < 0.4:
                drink = random.choices(
                    list(drinks),
                    weights=[1.6, 1.3, 1.5, 1.4, 0.9],
                    k=1
                )[0]
                order_items.append(drink)

            # Maybe add a dessert
            desserts = {"Tiramisu", "Panna Cotta", "Cannoli", "Affogato", "Chocolate Lava Cake"}
            if not any(i in desserts for i in order_items) and random.random() < 0.25:
                dessert = random.choices(
                    list(desserts),
                    weights=[1.4, 0.8, 1.1, 0.9, 0.8],
                    k=1
                )[0]
                order_items.append(dessert)

            # Write sales records
            menu_lookup = {m["name"]: m for m in MENU}
            for item_name in order_items:
                item = menu_lookup[item_name]
                qty = 1 if random.random() < 0.85 else 2
                total = round(item["price"] * qty, 2)
                minute = random.randint(0, 59)
                sale_dt = datetime(current_date.year, current_date.month, current_date.day, hour, minute)

                sales_rows.append({
                    "menu_item_name": item_name,
                    "quantity": qty,
                    "total_price": total,
                    "sale_date": sale_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "order_id": order_id,
                    "day_of_week": day_name,
                    "hour_of_day": hour,
                })

with open(os.path.join(OUT_DIR, "sales.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["menu_item_name", "quantity", "total_price", "sale_date", "order_id", "day_of_week", "hour_of_day"])
    writer.writeheader()
    writer.writerows(sales_rows)

print(f"Sales: {len(sales_rows)} transaction rows, {order_counter - 1} orders across {DAYS} days")

# =====================================================================
# 3. INVENTORY — 40 ingredients with realistic stock levels
# =====================================================================
INVENTORY = [
    # Produce
    {"ingredient_name": "San Marzano Tomatoes", "unit": "cans", "quantity_on_hand": 48, "reorder_threshold": 20, "unit_cost": 3.50, "expiry_date": "2026-09-15", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Fresh Mozzarella", "unit": "kg", "quantity_on_hand": 6.0, "reorder_threshold": 8, "unit_cost": 12.00, "expiry_date": "2026-03-12", "supplier": "DeLuca Dairy"},
    {"ingredient_name": "Burrata", "unit": "pieces", "quantity_on_hand": 8, "reorder_threshold": 10, "unit_cost": 5.50, "expiry_date": "2026-03-10", "supplier": "DeLuca Dairy"},
    {"ingredient_name": "Fresh Basil", "unit": "bunches", "quantity_on_hand": 5, "reorder_threshold": 8, "unit_cost": 2.50, "expiry_date": "2026-03-09", "supplier": "Local Farm Co-op"},
    {"ingredient_name": "Arugula", "unit": "kg", "quantity_on_hand": 2.0, "reorder_threshold": 3, "unit_cost": 8.00, "expiry_date": "2026-03-10", "supplier": "Local Farm Co-op"},
    {"ingredient_name": "Romaine Lettuce", "unit": "heads", "quantity_on_hand": 12, "reorder_threshold": 10, "unit_cost": 2.00, "expiry_date": "2026-03-12", "supplier": "Local Farm Co-op"},
    {"ingredient_name": "Heirloom Tomatoes", "unit": "kg", "quantity_on_hand": 3.5, "reorder_threshold": 5, "unit_cost": 6.00, "expiry_date": "2026-03-11", "supplier": "Local Farm Co-op"},
    {"ingredient_name": "Lemons", "unit": "pieces", "quantity_on_hand": 25, "reorder_threshold": 15, "unit_cost": 0.50, "expiry_date": "2026-03-20", "supplier": "Local Farm Co-op"},
    {"ingredient_name": "Eggplant", "unit": "pieces", "quantity_on_hand": 8, "reorder_threshold": 6, "unit_cost": 2.00, "expiry_date": "2026-03-13", "supplier": "Local Farm Co-op"},
    {"ingredient_name": "Garlic", "unit": "heads", "quantity_on_hand": 30, "reorder_threshold": 15, "unit_cost": 0.80, "expiry_date": "2026-04-01", "supplier": "Local Farm Co-op"},

    # Proteins
    {"ingredient_name": "Chicken Breast", "unit": "kg", "quantity_on_hand": 8.0, "reorder_threshold": 10, "unit_cost": 9.50, "expiry_date": "2026-03-10", "supplier": "Prime Meats"},
    {"ingredient_name": "Guanciale", "unit": "kg", "quantity_on_hand": 3.0, "reorder_threshold": 2, "unit_cost": 22.00, "expiry_date": "2026-03-25", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Veal Shank", "unit": "pieces", "quantity_on_hand": 4, "reorder_threshold": 3, "unit_cost": 18.00, "expiry_date": "2026-03-11", "supplier": "Prime Meats"},
    {"ingredient_name": "Fresh Calamari", "unit": "kg", "quantity_on_hand": 3.5, "reorder_threshold": 4, "unit_cost": 14.00, "expiry_date": "2026-03-09", "supplier": "Harbor Seafood"},
    {"ingredient_name": "Fresh Clams", "unit": "kg", "quantity_on_hand": 2.0, "reorder_threshold": 3, "unit_cost": 16.00, "expiry_date": "2026-03-09", "supplier": "Harbor Seafood"},
    {"ingredient_name": "Branzino", "unit": "whole fish", "quantity_on_hand": 3, "reorder_threshold": 4, "unit_cost": 15.00, "expiry_date": "2026-03-09", "supplier": "Harbor Seafood"},
    {"ingredient_name": "Beef Tenderloin", "unit": "kg", "quantity_on_hand": 2.5, "reorder_threshold": 3, "unit_cost": 35.00, "expiry_date": "2026-03-12", "supplier": "Prime Meats"},
    {"ingredient_name": "Prosciutto di Parma", "unit": "kg", "quantity_on_hand": 2.0, "reorder_threshold": 2, "unit_cost": 28.00, "expiry_date": "2026-04-15", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Lobster Meat", "unit": "kg", "quantity_on_hand": 1.5, "reorder_threshold": 2, "unit_cost": 45.00, "expiry_date": "2026-03-09", "supplier": "Harbor Seafood"},

    # Dairy & Cheese
    {"ingredient_name": "Parmigiano Reggiano", "unit": "kg", "quantity_on_hand": 5.0, "reorder_threshold": 3, "unit_cost": 25.00, "expiry_date": "2026-06-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Pecorino Romano", "unit": "kg", "quantity_on_hand": 3.0, "reorder_threshold": 2, "unit_cost": 20.00, "expiry_date": "2026-05-15", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Ricotta", "unit": "kg", "quantity_on_hand": 4.0, "reorder_threshold": 3, "unit_cost": 8.00, "expiry_date": "2026-03-14", "supplier": "DeLuca Dairy"},
    {"ingredient_name": "Mascarpone", "unit": "kg", "quantity_on_hand": 2.5, "reorder_threshold": 2, "unit_cost": 10.00, "expiry_date": "2026-03-15", "supplier": "DeLuca Dairy"},
    {"ingredient_name": "Heavy Cream", "unit": "liters", "quantity_on_hand": 6.0, "reorder_threshold": 5, "unit_cost": 4.50, "expiry_date": "2026-03-14", "supplier": "DeLuca Dairy"},
    {"ingredient_name": "Eggs", "unit": "dozen", "quantity_on_hand": 8, "reorder_threshold": 6, "unit_cost": 4.00, "expiry_date": "2026-03-20", "supplier": "Local Farm Co-op"},
    {"ingredient_name": "Gorgonzola", "unit": "kg", "quantity_on_hand": 1.5, "reorder_threshold": 1, "unit_cost": 18.00, "expiry_date": "2026-03-18", "supplier": "Italian Imports Co"},

    # Dry goods
    {"ingredient_name": "Spaghetti Pasta", "unit": "kg", "quantity_on_hand": 20, "reorder_threshold": 10, "unit_cost": 3.00, "expiry_date": "2027-01-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Penne Pasta", "unit": "kg", "quantity_on_hand": 15, "reorder_threshold": 8, "unit_cost": 3.00, "expiry_date": "2027-01-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Fettuccine Pasta", "unit": "kg", "quantity_on_hand": 12, "reorder_threshold": 8, "unit_cost": 3.50, "expiry_date": "2027-01-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Pizza Dough", "unit": "balls", "quantity_on_hand": 15, "reorder_threshold": 20, "unit_cost": 1.50, "expiry_date": "2026-03-10", "supplier": "In-house"},
    {"ingredient_name": "Arborio Rice", "unit": "kg", "quantity_on_hand": 8, "reorder_threshold": 4, "unit_cost": 5.00, "expiry_date": "2027-06-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Breadcrumbs", "unit": "kg", "quantity_on_hand": 5, "reorder_threshold": 3, "unit_cost": 2.50, "expiry_date": "2026-08-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Ciabatta Bread", "unit": "loaves", "quantity_on_hand": 6, "reorder_threshold": 8, "unit_cost": 3.00, "expiry_date": "2026-03-09", "supplier": "In-house"},
    {"ingredient_name": "Ladyfingers", "unit": "packs", "quantity_on_hand": 10, "reorder_threshold": 5, "unit_cost": 4.00, "expiry_date": "2026-05-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Cannoli Shells", "unit": "pieces", "quantity_on_hand": 24, "reorder_threshold": 15, "unit_cost": 1.00, "expiry_date": "2026-04-01", "supplier": "Italian Imports Co"},

    # Beverages & Other
    {"ingredient_name": "Espresso Beans", "unit": "kg", "quantity_on_hand": 5.0, "reorder_threshold": 3, "unit_cost": 18.00, "expiry_date": "2026-06-01", "supplier": "Caffè Roma"},
    {"ingredient_name": "Whole Milk", "unit": "liters", "quantity_on_hand": 10, "reorder_threshold": 8, "unit_cost": 1.50, "expiry_date": "2026-03-13", "supplier": "DeLuca Dairy"},
    {"ingredient_name": "Aperol", "unit": "bottles", "quantity_on_hand": 4, "reorder_threshold": 3, "unit_cost": 18.00, "expiry_date": "2027-01-01", "supplier": "Wine & Spirits Dist"},
    {"ingredient_name": "Prosecco", "unit": "bottles", "quantity_on_hand": 12, "reorder_threshold": 8, "unit_cost": 8.00, "expiry_date": "2027-03-01", "supplier": "Wine & Spirits Dist"},
    {"ingredient_name": "Montepulciano Wine", "unit": "bottles", "quantity_on_hand": 18, "reorder_threshold": 10, "unit_cost": 6.00, "expiry_date": "2028-01-01", "supplier": "Wine & Spirits Dist"},
    {"ingredient_name": "Limoncello", "unit": "bottles", "quantity_on_hand": 6, "reorder_threshold": 3, "unit_cost": 12.00, "expiry_date": "2027-06-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Extra Virgin Olive Oil", "unit": "liters", "quantity_on_hand": 8, "reorder_threshold": 5, "unit_cost": 12.00, "expiry_date": "2026-12-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Dark Chocolate", "unit": "kg", "quantity_on_hand": 3, "reorder_threshold": 2, "unit_cost": 14.00, "expiry_date": "2026-09-01", "supplier": "Italian Imports Co"},
    {"ingredient_name": "Vanilla Gelato", "unit": "liters", "quantity_on_hand": 5, "reorder_threshold": 4, "unit_cost": 8.00, "expiry_date": "2026-04-01", "supplier": "Gelato Fresco"},
    {"ingredient_name": "Saffron", "unit": "grams", "quantity_on_hand": 5, "reorder_threshold": 3, "unit_cost": 8.00, "expiry_date": "2027-01-01", "supplier": "Italian Imports Co"},
]

with open(os.path.join(OUT_DIR, "inventory.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["ingredient_name", "unit", "quantity_on_hand", "reorder_threshold", "unit_cost", "expiry_date", "supplier"])
    writer.writeheader()
    writer.writerows(INVENTORY)

print(f"Inventory: {len(INVENTORY)} ingredients")

# =====================================================================
# 4. RECIPE MAPPING — ingredients per menu item
# =====================================================================
RECIPES = {
    "Bruschetta Trio": [("Ciabatta Bread", 0.5, "loaves"), ("Heirloom Tomatoes", 0.15, "kg"), ("Fresh Basil", 0.1, "bunches"), ("Extra Virgin Olive Oil", 0.03, "liters"), ("Garlic", 0.5, "heads")],
    "Burrata Caprese": [("Burrata", 1, "pieces"), ("Heirloom Tomatoes", 0.2, "kg"), ("Fresh Basil", 0.1, "bunches"), ("Extra Virgin Olive Oil", 0.02, "liters")],
    "Calamari Fritti": [("Fresh Calamari", 0.25, "kg"), ("Breadcrumbs", 0.05, "kg"), ("Lemons", 1, "pieces"), ("San Marzano Tomatoes", 0.2, "cans")],
    "Arancini": [("Arborio Rice", 0.15, "kg"), ("Fresh Mozzarella", 0.05, "kg"), ("Breadcrumbs", 0.03, "kg"), ("Eggs", 0.08, "dozen")],
    "Carpaccio di Manzo": [("Beef Tenderloin", 0.12, "kg"), ("Arugula", 0.05, "kg"), ("Parmigiano Reggiano", 0.03, "kg"), ("Lemons", 0.5, "pieces"), ("Extra Virgin Olive Oil", 0.02, "liters")],
    "Spaghetti Carbonara": [("Spaghetti Pasta", 0.15, "kg"), ("Guanciale", 0.08, "kg"), ("Pecorino Romano", 0.04, "kg"), ("Eggs", 0.17, "dozen")],
    "Penne Arrabbiata": [("Penne Pasta", 0.15, "kg"), ("San Marzano Tomatoes", 0.3, "cans"), ("Garlic", 0.3, "heads"), ("Extra Virgin Olive Oil", 0.02, "liters")],
    "Fettuccine Alfredo": [("Fettuccine Pasta", 0.15, "kg"), ("Parmigiano Reggiano", 0.05, "kg"), ("Heavy Cream", 0.1, "liters"), ("Eggs", 0.08, "dozen")],
    "Linguine alle Vongole": [("Spaghetti Pasta", 0.15, "kg"), ("Fresh Clams", 0.3, "kg"), ("Garlic", 0.5, "heads"), ("Extra Virgin Olive Oil", 0.03, "liters"), ("Lemons", 0.5, "pieces")],
    "Rigatoni Bolognese": [("Penne Pasta", 0.15, "kg"), ("San Marzano Tomatoes", 0.4, "cans"), ("Parmigiano Reggiano", 0.03, "kg")],
    "Cacio e Pepe": [("Spaghetti Pasta", 0.15, "kg"), ("Pecorino Romano", 0.06, "kg")],
    "Lobster Ravioli": [("Lobster Meat", 0.12, "kg"), ("Fettuccine Pasta", 0.12, "kg"), ("Heavy Cream", 0.08, "liters"), ("Saffron", 0.1, "grams"), ("Eggs", 0.17, "dozen")],
    "Margherita Pizza": [("Pizza Dough", 1, "balls"), ("San Marzano Tomatoes", 0.25, "cans"), ("Fresh Mozzarella", 0.15, "kg"), ("Fresh Basil", 0.1, "bunches"), ("Extra Virgin Olive Oil", 0.02, "liters")],
    "Diavola Pizza": [("Pizza Dough", 1, "balls"), ("San Marzano Tomatoes", 0.25, "cans"), ("Fresh Mozzarella", 0.12, "kg")],
    "Quattro Formaggi": [("Pizza Dough", 1, "balls"), ("Fresh Mozzarella", 0.1, "kg"), ("Gorgonzola", 0.05, "kg"), ("Parmigiano Reggiano", 0.04, "kg")],
    "Prosciutto e Rucola": [("Pizza Dough", 1, "balls"), ("Fresh Mozzarella", 0.1, "kg"), ("Prosciutto di Parma", 0.06, "kg"), ("Arugula", 0.03, "kg"), ("Parmigiano Reggiano", 0.03, "kg")],
    "Pizza Bianca": [("Pizza Dough", 1, "balls"), ("Ricotta", 0.1, "kg"), ("Fresh Mozzarella", 0.1, "kg"), ("Garlic", 0.3, "heads")],
    "Chicken Parmigiana": [("Chicken Breast", 0.25, "kg"), ("Breadcrumbs", 0.05, "kg"), ("San Marzano Tomatoes", 0.3, "cans"), ("Fresh Mozzarella", 0.1, "kg"), ("Spaghetti Pasta", 0.12, "kg"), ("Eggs", 0.08, "dozen")],
    "Veal Piccata": [("Veal Shank", 0.5, "pieces"), ("Lemons", 1, "pieces"), ("Heavy Cream", 0.05, "liters")],
    "Branzino al Forno": [("Branzino", 1, "whole fish"), ("Lemons", 1, "pieces"), ("Extra Virgin Olive Oil", 0.03, "liters"), ("Fresh Basil", 0.1, "bunches")],
    "Osso Buco": [("Veal Shank", 1, "pieces"), ("Arborio Rice", 0.15, "kg"), ("Saffron", 0.15, "grams"), ("San Marzano Tomatoes", 0.3, "cans"), ("Lemons", 0.5, "pieces")],
    "Eggplant Parmigiana": [("Eggplant", 1, "pieces"), ("San Marzano Tomatoes", 0.3, "cans"), ("Fresh Mozzarella", 0.12, "kg"), ("Breadcrumbs", 0.04, "kg"), ("Fresh Basil", 0.05, "bunches")],
    "Caesar Salad": [("Romaine Lettuce", 0.5, "heads"), ("Parmigiano Reggiano", 0.03, "kg"), ("Eggs", 0.08, "dozen"), ("Ciabatta Bread", 0.2, "loaves")],
    "Insalata Mista": [("Arugula", 0.05, "kg"), ("Heirloom Tomatoes", 0.1, "kg"), ("Extra Virgin Olive Oil", 0.02, "liters")],
    "Panzanella": [("Ciabatta Bread", 0.3, "loaves"), ("Heirloom Tomatoes", 0.15, "kg"), ("Fresh Basil", 0.05, "bunches"), ("Extra Virgin Olive Oil", 0.02, "liters")],
    "Tiramisu": [("Mascarpone", 0.1, "kg"), ("Ladyfingers", 0.2, "packs"), ("Espresso Beans", 0.02, "kg"), ("Eggs", 0.08, "dozen"), ("Dark Chocolate", 0.02, "kg")],
    "Panna Cotta": [("Heavy Cream", 0.15, "liters"), ("Vanilla Gelato", 0.05, "liters")],
    "Cannoli": [("Cannoli Shells", 2, "pieces"), ("Ricotta", 0.08, "kg"), ("Dark Chocolate", 0.02, "kg")],
    "Affogato": [("Vanilla Gelato", 0.12, "liters"), ("Espresso Beans", 0.02, "kg")],
    "Chocolate Lava Cake": [("Dark Chocolate", 0.08, "kg"), ("Eggs", 0.17, "dozen"), ("Heavy Cream", 0.05, "liters"), ("Vanilla Gelato", 0.08, "liters")],
    "Espresso": [("Espresso Beans", 0.02, "kg")],
    "Cappuccino": [("Espresso Beans", 0.02, "kg"), ("Whole Milk", 0.15, "liters")],
    "Aperol Spritz": [("Aperol", 0.06, "bottles"), ("Prosecco", 0.1, "bottles")],
    "House Red Wine": [("Montepulciano Wine", 0.17, "bottles")],
    "Limoncello": [("Limoncello", 0.05, "bottles")],
}

recipe_rows = []
for item_name, ingredients in RECIPES.items():
    for ing_name, qty, unit in ingredients:
        recipe_rows.append({
            "menu_item_name": item_name,
            "ingredient_name": ing_name,
            "quantity_needed": qty,
            "unit": unit,
        })

with open(os.path.join(OUT_DIR, "recipe_mapping.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["menu_item_name", "ingredient_name", "quantity_needed", "unit"])
    writer.writeheader()
    writer.writerows(recipe_rows)

print(f"Recipe mapping: {len(recipe_rows)} ingredient links across {len(RECIPES)} items")

# =====================================================================
# 5. SOCIAL POSTS — 60 posts over the last month across 3 platforms
# =====================================================================
PLATFORMS = ["instagram", "facebook", "tiktok"]
POST_TYPES = ["photo", "video", "reel", "story", "carousel"]

# Which items get featured in social posts
SOCIAL_ITEMS = [
    "Margherita Pizza", "Spaghetti Carbonara", "Tiramisu", "Burrata Caprese",
    "Aperol Spritz", "Lobster Ravioli", "Chicken Parmigiana", "Calamari Fritti",
    "Cannoli", "Osso Buco", "Prosciutto e Rucola", "Chocolate Lava Cake",
    "Bruschetta Trio", "Diavola Pizza", "Cacio e Pepe",
]

CONTENT_TEMPLATES = [
    "Fresh out of the kitchen! Our {item} is calling your name 🍝",
    "Weekend vibes start with {item} 🎉",
    "Chef's special today: {item} — made with love and the finest ingredients",
    "Nothing beats a classic {item} on a {day} evening",
    "New on the menu spotlight: {item}! Come taste the difference",
    "Your table is waiting. {item} is served ✨",
    "Behind the scenes: making our famous {item} from scratch",
    "Happy hour special featuring {item} — don't miss out!",
    "{item} + good company = perfect evening 🥂",
    "Our {item} has been getting rave reviews! Have you tried it yet?",
]

social_rows = []
for i in range(60):
    day_offset = random.randint(0, 29)
    post_date = START_DATE + timedelta(days=day_offset)
    hour = random.choices([10, 11, 12, 13, 17, 18, 19, 20], weights=[0.5, 0.8, 1.2, 1.0, 0.8, 1.5, 1.3, 0.9])[0]
    minute = random.randint(0, 59)
    posted_at = datetime(post_date.year, post_date.month, post_date.day, hour, minute)

    platform = random.choices(PLATFORMS, weights=[0.5, 0.3, 0.2])[0]
    post_type = random.choices(POST_TYPES, weights=[0.3, 0.2, 0.25, 0.15, 0.1])[0]
    item = random.choice(SOCIAL_ITEMS)
    template = random.choice(CONTENT_TEMPLATES)
    content = template.format(item=item, day=post_date.strftime("%A"))

    # Engagement varies by platform and post type
    base_likes = {"instagram": 180, "facebook": 45, "tiktok": 350}[platform]
    base_comments = {"instagram": 15, "facebook": 8, "tiktok": 25}[platform]
    base_shares = {"instagram": 8, "facebook": 12, "tiktok": 40}[platform]
    type_mult = {"photo": 1.0, "video": 1.4, "reel": 1.8, "story": 0.6, "carousel": 1.2}[post_type]

    # Time-of-day multiplier
    time_mult = {10: 0.7, 11: 0.8, 12: 1.2, 13: 1.1, 17: 0.9, 18: 1.3, 19: 1.4, 20: 1.1}[hour]

    likes = int(base_likes * type_mult * time_mult * random.uniform(0.5, 1.5))
    comments = int(base_comments * type_mult * time_mult * random.uniform(0.3, 2.0))
    shares = int(base_shares * type_mult * time_mult * random.uniform(0.2, 2.0))
    reach = int(likes * random.uniform(3, 8))

    social_rows.append({
        "platform": platform,
        "post_type": post_type,
        "content_summary": content,
        "menu_item_name": item,
        "posted_at": posted_at.strftime("%Y-%m-%d %H:%M:%S"),
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "reach": reach,
    })

with open(os.path.join(OUT_DIR, "social_posts.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["platform", "post_type", "content_summary", "menu_item_name", "posted_at", "likes", "comments", "shares", "reach"])
    writer.writeheader()
    writer.writerows(social_rows)

print(f"Social posts: {len(social_rows)} posts across {len(set(r['platform'] for r in social_rows))} platforms")

print(f"\nAll files written to: {OUT_DIR}")
