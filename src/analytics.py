import calendar
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression

from src.config import DISCRETIONARY_CATEGORIES, ESSENTIAL_CATEGORIES


EXPENSE_COLUMNS = [
    "id",
    "amount",
    "category",
    "description",
    "expense_date",
    "created_at",
    "updated_at",
]


def expenses_to_dataframe(expenses: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert raw SQLite expense rows into a clean, typed Pandas DataFrame."""
    if not expenses:
        df = pd.DataFrame(columns=EXPENSE_COLUMNS)
        df["amount"] = df["amount"].astype(float)
        df["expense_date"] = pd.to_datetime(df["expense_date"])
        return df

    df = pd.DataFrame(expenses)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["expense_date"] = pd.to_datetime(df["expense_date"], errors="coerce")
    df = df.dropna(subset=["expense_date"]).sort_values(
        by=["expense_date", "id"], ascending=[False, False]
    )
    return df


def get_active_budget_period(
    budget_type: str, reference_date: Optional[date] = None
) -> Dict[str, Any]:
    """Calculate start/end dates and elapsed days for Weekly or Monthly cycle."""
    today = reference_date or date.today()

    if budget_type == "Weekly":
        start_dt = today - timedelta(days=today.weekday())
        end_dt = start_dt + timedelta(days=6)
        label = f"Current Week ({start_dt.strftime('%d %b')} – {end_dt.strftime('%d %b %Y')})"
    else:
        _, last_day = calendar.monthrange(today.year, today.month)
        start_dt = today.replace(day=1)
        end_dt = today.replace(day=last_day)
        label = f"Current Month ({today.strftime('%B %Y')})"

    days_total = (end_dt - start_dt).days + 1
    days_elapsed = max(1, (today - start_dt).days + 1)
    days_remaining = max(0, (end_dt - today).days + 1)

    return {
        "start_date": start_dt,
        "end_date": end_dt,
        "label": label,
        "days_total": days_total,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
    }


def filter_expenses(
    df: pd.DataFrame,
    search_query: str = "",
    categories: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    """Filter expense DataFrame by keyword, categories, and date window."""
    if df.empty:
        return df.copy()

    filtered = df.copy()

    if categories:
        filtered = filtered[filtered["category"].isin(categories)]

    if start_date is not None:
        filtered = filtered[filtered["expense_date"].dt.date >= start_date]

    if end_date is not None:
        filtered = filtered[filtered["expense_date"].dt.date <= end_date]

    if search_query.strip():
        query = search_query.strip()
        mask = filtered["description"].str.contains(query, case=False, na=False) | filtered[
            "category"
        ].str.contains(query, case=False, na=False)
        filtered = filtered[mask]

    return filtered


def calculate_spending_summary(
    df: pd.DataFrame, profile: Dict[str, Any]
) -> Dict[str, Any]:
    """Compute core KPIs, active period spend, balance, and category breakdown."""
    pocket_money = float(profile.get("pocket_money", 0.0))
    budget_type = profile.get("budget_type", "Monthly")
    period = get_active_budget_period(budget_type)

    period_df = filter_expenses(
        df, start_date=period["start_date"], end_date=period["end_date"]
    )

    total_spent = float(period_df["amount"].sum()) if not period_df.empty else 0.0
    all_time_spent = float(df["amount"].sum()) if not df.empty else 0.0
    remaining_balance = pocket_money - total_spent

    if pocket_money > 0:
        usage_pct = (total_spent / pocket_money) * 100.0
    else:
        usage_pct = 100.0 if total_spent > 0 else 0.0

    safe_daily_allowance = (
        max(0.0, remaining_balance) / max(1, period["days_remaining"])
    )

    category_summary = get_category_breakdown(period_df)
    if not category_summary.empty:
        top_row = category_summary.iloc[0]
        top_category = str(top_row["Category"])
        top_category_amount = float(top_row["Amount"])
    else:
        top_category = "N/A"
        top_category_amount = 0.0

    return {
        "pocket_money": pocket_money,
        "total_spent": total_spent,
        "all_time_spent": all_time_spent,
        "remaining_balance": remaining_balance,
        "usage_pct": usage_pct,
        "safe_daily_allowance": safe_daily_allowance,
        "top_category": top_category,
        "top_category_amount": top_category_amount,
        "transaction_count": len(period_df),
        "all_time_count": len(df),
        "period": period,
        "period_df": period_df,
        "category_summary": category_summary,
    }


def get_category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total spend, transaction count, and percentage share per category."""
    columns = ["Category", "Amount", "Transactions", "Share (%)"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    grouped = (
        df.groupby("category", as_index=False)
        .agg(Amount=("amount", "sum"), Transactions=("id", "count"))
        .rename(columns={"category": "Category"})
        .sort_values(by="Amount", ascending=False)
        .reset_index(drop=True)
    )
    total = grouped["Amount"].sum()
    grouped["Share (%)"] = (
        (grouped["Amount"] / total * 100.0).round(2) if total > 0 else 0.0
    )
    return grouped


def get_time_series_summary(df: pd.DataFrame, mode: str = "Daily") -> pd.DataFrame:
    """Group expenses into Daily or Monthly series for bar-chart visualization."""
    if df.empty:
        return pd.DataFrame(columns=["Label", "Amount"])

    temp = df.copy()
    if mode == "Monthly":
        temp["period_key"] = temp["expense_date"].dt.to_period("M")
        grouped = (
            temp.groupby("period_key", as_index=False)["amount"]
            .sum()
            .sort_values("period_key")
        )
        grouped["Label"] = grouped["period_key"].dt.strftime("%b %Y")
        return grouped[["Label", "amount"]].rename(columns={"amount": "Amount"})

    temp["day_key"] = temp["expense_date"].dt.date
    grouped = (
        temp.groupby("day_key", as_index=False)["amount"]
        .sum()
        .sort_values("day_key")
        .tail(30)
    )
    grouped["Label"] = pd.to_datetime(grouped["day_key"]).dt.strftime("%d %b")
    return grouped[["Label", "amount"]].rename(columns={"amount": "Amount"})


def run_ml_spending_analysis(
    df: pd.DataFrame, summary: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Offline Machine Learning & Statistical Analysis:
    1. Scikit-Learn LinearRegression for 7-day future spending forecast.
    2. Scikit-Learn IsolationForest + Z-score for high-expense anomaly detection.
    3. Essential vs Discretionary spending behavior split.
    4. Weekday vs Weekend pattern analysis.
    """
    period = summary["period"]
    period_df = summary["period_df"]
    pocket_money = summary["pocket_money"]

    if df.empty:
        return {
            "has_data": False,
            "avg_daily_spend": 0.0,
            "projected_period_spend": 0.0,
            "projected_balance": pocket_money,
            "trend_direction": "Insufficient data",
            "daily_slope": 0.0,
            "next_7_days_forecast": 0.0,
            "anomalies": [],
            "peak_weekday": "N/A",
            "weekend_share_pct": 0.0,
            "essential_pct": 0.0,
            "discretionary_pct": 0.0,
            "essential_amt": 0.0,
            "discretionary_amt": 0.0,
        }

    # 1. Active Cycle Burn Rate & End-of-Cycle Projection
    days_elapsed = period["days_elapsed"]
    days_total = period["days_total"]
    active_spent = summary["total_spent"]

    avg_daily_active = active_spent / max(1, days_elapsed)
    projected_period_spend = avg_daily_active * days_total
    projected_balance = pocket_money - projected_period_spend

    # 2. Scikit-Learn LinearRegression on Daily Time Series
    daily_totals = (
        df.assign(day=df["expense_date"].dt.floor("D"))
        .groupby("day")["amount"]
        .sum()
        .sort_index()
    )

    if len(daily_totals) >= 3:
        full_range = pd.date_range(
            daily_totals.index.min(), daily_totals.index.max(), freq="D"
        )
        dense_series = daily_totals.reindex(full_range, fill_value=0.0)
        X = np.arange(len(dense_series)).reshape(-1, 1)
        y = dense_series.values.astype(float)

        reg = LinearRegression()
        reg.fit(X, y)
        slope = float(reg.coef_[0])

        future_X = np.arange(len(dense_series), len(dense_series) + 7).reshape(-1, 1)
        future_preds = np.maximum(0.0, reg.predict(future_X))
        next_7_days_forecast = float(future_preds.sum())

        if slope > 5:
            trend_direction = "Increasing"
        elif slope < -5:
            trend_direction = "Decreasing"
        else:
            trend_direction = "Stable"
    else:
        slope = 0.0
        mean_daily = float(daily_totals.mean()) if len(daily_totals) > 0 else 0.0
        next_7_days_forecast = mean_daily * 7.0
        trend_direction = "Stable (limited history)"

    # 3. ML Anomaly Detection (IsolationForest + Z-Score)
    anomalies: List[Dict[str, Any]] = []
    mean_amt = float(df["amount"].mean())
    std_amt = float(df["amount"].std(ddof=1)) if len(df) > 1 else 0.0

    if len(df) >= 6 and df["amount"].nunique() >= 3:
        iso = IsolationForest(contamination=0.15, random_state=42)
        preds = iso.fit_predict(df[["amount"]])
        temp_anom = df.copy()
        temp_anom["iso_flag"] = preds
        # Flag high-side anomalies (above average spend)
        high_outliers = (
            temp_anom[(temp_anom["iso_flag"] == -1) & (temp_anom["amount"] > mean_amt)]
            .sort_values(by="amount", ascending=False)
            .head(5)
        )
        for _, row in high_outliers.iterrows():
            z_val = ((float(row["amount"]) - mean_amt) / std_amt) if std_amt > 0 else 0.0
            anomalies.append(
                {
                    "id": int(row["id"]),
                    "date": row["expense_date"].strftime("%Y-%m-%d"),
                    "category": row["category"],
                    "description": row["description"],
                    "amount": float(row["amount"]),
                    "z_score": round(z_val, 2),
                }
            )
    elif len(df) >= 4 and std_amt > 0:
        z_scores = (df["amount"] - mean_amt) / std_amt
        outlier_df = df[z_scores >= 1.5].sort_values(by="amount", ascending=False).head(5)
        for _, row in outlier_df.iterrows():
            z_val = (float(row["amount"]) - mean_amt) / std_amt
            anomalies.append(
                {
                    "id": int(row["id"]),
                    "date": row["expense_date"].strftime("%Y-%m-%d"),
                    "category": row["category"],
                    "description": row["description"],
                    "amount": float(row["amount"]),
                    "z_score": round(z_val, 2),
                }
            )

    # 4. Essential vs Discretionary Split (on active period if available, else all data)
    ref_df = period_df if not period_df.empty else df
    ref_total = float(ref_df["amount"].sum())
    essential_amt = float(
        ref_df.loc[ref_df["category"].isin(ESSENTIAL_CATEGORIES), "amount"].sum()
    )
    discretionary_amt = float(
        ref_df.loc[ref_df["category"].isin(DISCRETIONARY_CATEGORIES), "amount"].sum()
    )
    essential_pct = (essential_amt / ref_total * 100.0) if ref_total > 0 else 0.0
    discretionary_pct = (discretionary_amt / ref_total * 100.0) if ref_total > 0 else 0.0

    # 5. Weekday vs Weekend pattern
    temp = df.copy()
    temp["weekday"] = temp["expense_date"].dt.day_name()
    weekday_totals = temp.groupby("weekday")["amount"].sum()
    peak_weekday = str(weekday_totals.idxmax()) if not weekday_totals.empty else "N/A"

    is_weekend = temp["expense_date"].dt.dayofweek >= 5
    weekend_spend = float(temp.loc[is_weekend, "amount"].sum())
    total_hist_spend = float(temp["amount"].sum())
    weekend_share_pct = (
        (weekend_spend / total_hist_spend * 100.0) if total_hist_spend > 0 else 0.0
    )

    return {
        "has_data": True,
        "avg_daily_spend": round(avg_daily_active, 2),
        "projected_period_spend": round(projected_period_spend, 2),
        "projected_balance": round(projected_balance, 2),
        "trend_direction": trend_direction,
        "daily_slope": round(slope, 2),
        "next_7_days_forecast": round(next_7_days_forecast, 2),
        "anomalies": anomalies,
        "peak_weekday": peak_weekday,
        "weekend_share_pct": round(weekend_share_pct, 1),
        "essential_pct": round(essential_pct, 1),
        "discretionary_pct": round(discretionary_pct, 1),
        "essential_amt": round(essential_amt, 2),
        "discretionary_amt": round(discretionary_amt, 2),
    }