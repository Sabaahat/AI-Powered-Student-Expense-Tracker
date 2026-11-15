import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.config import CATEGORIES, DATA_DIR, DB_PATH


class DatabaseError(Exception):
    """Custom exception raised for SQLite database failures."""


def _get_connection() -> sqlite3.Connection:
    """Create and return a SQLite connection with row dictionary access."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite tables and ensure a default student profile exists."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()

            # Single-row student profile table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS student_profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT NOT NULL,
                    budget_type TEXT NOT NULL CHECK (budget_type IN ('Weekly', 'Monthly')),
                    pocket_money REAL NOT NULL CHECK (pocket_money >= 0),
                    currency TEXT NOT NULL DEFAULT '₹',
                    updated_at TEXT NOT NULL
                )
                """
            )

            # Persistent expenses table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL CHECK (amount > 0),
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    expense_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            # Create index on expense_date for faster history & analytical queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_expenses_date
                ON expenses (expense_date)
                """
            )

            # Insert default profile on first launch so app works out-of-the-box
            cursor.execute("SELECT COUNT(*) FROM student_profile WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                now = datetime.now().isoformat(timespec="seconds")
                cursor.execute(
                    """
                    INSERT INTO student_profile (id, name, budget_type, pocket_money, currency, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?)
                    """,
                    ("College Student", "Monthly", 5000.0, "₹", now),
                )

            conn.commit()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Failed to initialize SQLite database: {exc}") from exc


def get_profile() -> Dict[str, Any]:
    """Fetch the student profile from SQLite."""
    try:
        with _get_connection() as conn:
            row = conn.execute("SELECT * FROM student_profile WHERE id = 1").fetchone()
            if row is None:
                init_db()
                row = conn.execute("SELECT * FROM student_profile WHERE id = 1").fetchone()
            return dict(row)
    except sqlite3.Error as exc:
        raise DatabaseError(f"Failed to fetch student profile: {exc}") from exc


def update_profile(
    name: str, budget_type: str, pocket_money: float, currency: str = "₹"
) -> Tuple[bool, str]:
    """Validate and persist student profile changes."""
    cleaned_name = name.strip()
    if not cleaned_name:
        return False, "Student name cannot be empty."
    if budget_type not in ("Weekly", "Monthly"):
        return False, "Budget type must be either Weekly or Monthly."
    if pocket_money < 0:
        return False, "Pocket money cannot be negative."

    try:
        now = datetime.now().isoformat(timespec="seconds")
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO student_profile (id, name, budget_type, pocket_money, currency, updated_at)
                VALUES (1, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    budget_type = excluded.budget_type,
                    pocket_money = excluded.pocket_money,
                    currency = excluded.currency,
                    updated_at = excluded.updated_at
                """,
                (cleaned_name, budget_type, float(pocket_money), currency, now),
            )
            conn.commit()
        return True, "Student profile updated successfully."
    except sqlite3.Error as exc:
        return False, f"Database error while updating profile: {exc}"


def add_expense(
    amount: float, category: str, description: str, expense_date: str
) -> Tuple[bool, str]:
    """Validate and insert a new expense record into SQLite."""
    if amount <= 0:
        return False, "Expense amount must be greater than zero."
    if category not in CATEGORIES:
        return False, f"Invalid category selected: {category}."

    cleaned_desc = description.strip()
    if not cleaned_desc:
        return False, "Please provide a short description for the expense."

    try:
        datetime.strptime(expense_date, "%Y-%m-%d")
    except ValueError:
        return False, "Invalid date format. Expected YYYY-MM-DD."

    try:
        now = datetime.now().isoformat(timespec="seconds")
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO expenses (amount, category, description, expense_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (round(float(amount), 2), category, cleaned_desc, expense_date, now, now),
            )
            conn.commit()
        return True, "Expense saved permanently."
    except sqlite3.Error as exc:
        return False, f"Database error while adding expense: {exc}"


def get_all_expenses() -> List[Dict[str, Any]]:
    """Retrieve all expenses ordered from newest to oldest."""
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, amount, category, description, expense_date, created_at, updated_at
                FROM expenses
                ORDER BY expense_date DESC, id DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        raise DatabaseError(f"Failed to retrieve expenses: {exc}") from exc


def update_expense(
    expense_id: int, amount: float, category: str, description: str, expense_date: str
) -> Tuple[bool, str]:
    """Update an existing expense record in SQLite."""
    if amount <= 0:
        return False, "Expense amount must be greater than zero."
    if category not in CATEGORIES:
        return False, f"Invalid category selected: {category}."

    cleaned_desc = description.strip()
    if not cleaned_desc:
        return False, "Expense description cannot be empty."

    try:
        datetime.strptime(expense_date, "%Y-%m-%d")
    except ValueError:
        return False, "Invalid date format. Expected YYYY-MM-DD."

    try:
        now = datetime.now().isoformat(timespec="seconds")
        with _get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE expenses
                SET amount = ?, category = ?, description = ?, expense_date = ?, updated_at = ?
                WHERE id = ?
                """,
                (round(float(amount), 2), category, cleaned_desc, expense_date, now, expense_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, f"No expense found with ID #{expense_id}."
        return True, f"Expense #{expense_id} updated successfully."
    except sqlite3.Error as exc:
        return False, f"Database error while updating expense: {exc}"


def delete_expense(expense_id: int) -> Tuple[bool, str]:
    """Delete an expense record permanently from SQLite."""
    try:
        with _get_connection() as conn:
            cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return False, f"No expense found with ID #{expense_id}."
        return True, f"Expense #{expense_id} deleted permanently."
    except sqlite3.Error as exc:
        return False, f"Database error while deleting expense: {exc}"


def clear_all_expenses() -> Tuple[bool, str]:
    """Delete all expense records (useful for resetting demo data)."""
    try:
        with _get_connection() as conn:
            conn.execute("DELETE FROM expenses")
            conn.commit()
        return True, "All expense records have been cleared."
    except sqlite3.Error as exc:
        return False, f"Database error while clearing expenses: {exc}"