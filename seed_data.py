"""
Optional demo data generator for testing charts, filters, ML forecasting, and Gemini AI.
Run with: python seed_data.py
"""

from datetime import date, timedelta
import random

from src.database import add_expense, init_db, update_profile


SAMPLE_EXPENSES = [
    ("Food", "College canteen masala dosa & tea", (45, 95)),
    ("Food", "Evening momos and cold coffee with friends", (90, 180)),
    ("Food", "Weekend biryani delivery", (220, 380)),
    ("Travel", "Metro card recharge", (150, 300)),
    ("Travel", "Auto rickshaw from hostel to station", (40, 110)),
    ("Stationery", "Project spiral binding & printouts", (60, 190)),
    ("Stationery", "Notebooks and gel pens", (80, 160)),
    ("Entertainment", "Movie ticket & popcorn", (250, 480)),
    ("Entertainment", "Spotify / OTT monthly student plan", (59, 149)),
    ("Shopping", "Online order phone case & cable", (199, 450)),
    ("Clothes", "Casual cotton t-shirt from sale", (399, 799)),
    ("Other", "Laundry & hostel supplies", (80, 180)),
]


def seed_demo_data(days: int = 25, count: int = 28) -> None:
    """Populate realistic student profile and sample expense entries."""
    init_db()
    update_profile(
        name="Aarav Sharma",
        budget_type="Monthly",
        pocket_money=6000.0,
        currency="₹",
    )

    today = date.today()
    random.seed(42)

    for _ in range(count):
        category, desc, (low, high) = random.choice(SAMPLE_EXPENSES)
        amount = round(random.uniform(low, high), 0)
        offset = random.randint(0, max(1, days - 1))
        exp_date = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        add_expense(amount=amount, category=category, description=desc, expense_date=exp_date)

    print(f"Successfully seeded {count} sample student expenses.")


if __name__ == "__main__":
    seed_demo_data()