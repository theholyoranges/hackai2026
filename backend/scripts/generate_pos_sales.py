"""Generate a realistic POS-export style sales CSV for Spice Garden."""

import csv
import random
from datetime import datetime, timedelta

random.seed(99)

ITEMS = {
    "Chicken Tikka Masala": (16.99, 1.8),
    "Lamb Biryani": (18.99, 1.3),
    "Butter Naan": (3.99, 2.5),
    "Garlic Naan": (4.49, 2.0),
    "Paneer Tikka": (12.99, 1.1),
    "Samosa": (6.99, 1.5),
    "Mango Lassi": (4.99, 1.7),
    "Masala Chai": (3.49, 1.9),
    "Dal Makhani": (13.99, 1.0),
    "Palak Paneer": (14.99, 0.9),
    "Tandoori Chicken": (15.99, 1.2),
    "Fish Curry": (17.99, 0.6),
    "Aloo Gobi": (9.99, 0.8),
    "Raita": (3.99, 1.4),
    "Gulab Jamun": (5.99, 1.3),
    "Kheer": (5.49, 0.7),
}

# Common combos
COMBOS = [
    (["Chicken Tikka Masala", "Butter Naan", "Mango Lassi"], 0.12),
    (["Lamb Biryani", "Raita", "Masala Chai"], 0.08),
    (["Paneer Tikka", "Garlic Naan", "Mango Lassi"], 0.06),
    (["Samosa", "Masala Chai"], 0.10),
    (["Dal Makhani", "Butter Naan", "Raita"], 0.06),
    (["Tandoori Chicken", "Garlic Naan", "Mango Lassi", "Gulab Jamun"], 0.05),
    (["Fish Curry", "Butter Naan", "Masala Chai"], 0.04),
    (["Palak Paneer", "Garlic Naan", "Kheer"], 0.04),
]

START = datetime(2026, 2, 5, 0, 0)
DAYS = 30

rows = []
txn = 1001

for day in range(DAYS):
    dt = START + timedelta(days=day)
    is_weekend = dt.weekday() >= 4

    # Lunch 11:30-14:00, Dinner 17:30-21:30
    for service, hours in [("lunch", range(1130, 1400, 15)), ("dinner", range(1730, 2130, 15))]:
        base = 6 if service == "lunch" else 10
        if is_weekend:
            base = int(base * 1.5)
        num_orders = base + random.randint(-2, 3)

        for _ in range(num_orders):
            h = random.choice(list(hours))
            hour = h // 100
            minute = h % 100 + random.randint(0, 14)
            if minute >= 60:
                hour += 1
                minute -= 60
            order_time = dt.replace(hour=hour, minute=minute)
            txn_id = f"TXN{txn}"
            txn += 1

            # Build order
            if random.random() < 0.40:
                combo = random.choices(COMBOS, weights=[c[1] for c in COMBOS], k=1)[0]
                items = list(combo[0])
            else:
                names = list(ITEMS.keys())
                weights = [ITEMS[n][1] for n in names]
                n = random.choices([1, 2, 3, 4], weights=[0.1, 0.35, 0.35, 0.2])[0]
                items = list(set(random.choices(names, weights=weights, k=n)))

            # Add naan if ordering a main without bread
            mains = {"Chicken Tikka Masala", "Lamb Biryani", "Dal Makhani", "Palak Paneer", "Tandoori Chicken", "Fish Curry"}
            breads = {"Butter Naan", "Garlic Naan"}
            if any(i in mains for i in items) and not any(i in breads for i in items) and random.random() < 0.6:
                items.append(random.choice(["Butter Naan", "Garlic Naan"]))

            # Add drink
            drinks = {"Mango Lassi", "Masala Chai"}
            if not any(i in drinks for i in items) and random.random() < 0.35:
                items.append(random.choice(["Mango Lassi", "Masala Chai"]))

            for item_name in items:
                price = ITEMS[item_name][0]
                qty = 1 if item_name not in breads else random.choices([1, 2], weights=[0.6, 0.4])[0]
                total = round(price * qty, 2)

                # POS-style columns (different from our internal format)
                rows.append({
                    "Transaction ID": txn_id,
                    "Date": order_time.strftime("%m/%d/%Y"),
                    "Time": order_time.strftime("%I:%M %p"),
                    "Item Name": item_name,
                    "Qty": qty,
                    "Unit Price": f"{price:.2f}",
                    "Line Total": f"{total:.2f}",
                    "Payment Method": random.choice(["Card", "Card", "Card", "Cash", "UPI"]),
                    "Server": random.choice(["Priya", "Rahul", "Anita", "Dev"]),
                })

out = "/Users/tushar/Documents/hackai2026/backend/data/sample_upload/pos_sales.csv"
with open(out, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["Transaction ID", "Date", "Time", "Item Name", "Qty", "Unit Price", "Line Total", "Payment Method", "Server"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} POS sales rows, {txn - 1001} transactions → {out}")
