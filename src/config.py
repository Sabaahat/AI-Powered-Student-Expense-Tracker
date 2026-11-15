from pathlib import Path

# Resolve project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database paths
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "expenses.db"

# Expense categories required by the application
CATEGORIES = [
    "Food",
    "Travel",
    "Clothes",
    "Stationery",
    "Entertainment",
    "Shopping",
    "Other",
]

# Behavioural grouping for AI spending analysis
ESSENTIAL_CATEGORIES = {"Food", "Travel", "Stationery"}
DISCRETIONARY_CATEGORIES = {"Clothes", "Entertainment", "Shopping", "Other"}

BUDGET_TYPES = ["Weekly", "Monthly"]
CURRENCIES = ["₹", "$", "€", "£"]

# Color palette mapped consistently across Matplotlib charts
CATEGORY_COLORS = {
    "Food": "#4F46E5",          # Indigo
    "Travel": "#0EA5E9",        # Sky Blue
    "Clothes": "#EC4899",       # Pink
    "Stationery": "#10B981",    # Emerald
    "Entertainment": "#F59E0B", # Amber
    "Shopping": "#8B5CF6",      # Violet
    "Other": "#64748B",         # Slate
}

# Alert thresholds (in percentage of pocket money)
WARNING_THRESHOLD_PCT = 80.0
EXCEEDED_THRESHOLD_PCT = 100.0