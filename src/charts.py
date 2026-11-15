from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from src.config import CATEGORY_COLORS


def _empty_figure(message: str) -> plt.Figure:
    """Create a clean placeholder Matplotlib figure when no data is available."""
    fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        fontsize=11,
        color="#64748B",
        fontweight="medium",
    )
    ax.axis("off")
    fig.tight_layout()
    return fig


def plot_category_pie_chart(
    category_df: pd.DataFrame, currency: str = "₹"
) -> plt.Figure:
    """Generate a modern Matplotlib Donut/Pie chart for category-wise expenses."""
    if category_df.empty or category_df["Amount"].sum() <= 0:
        return _empty_figure("No expenses in the current budget period yet.")

    labels = category_df["Category"].tolist()
    values = category_df["Amount"].tolist()
    colors = [CATEGORY_COLORS.get(cat, "#64748B") for cat in labels]
    total_spent = sum(values)

    fig, ax = plt.subplots(figsize=(6.8, 4.6), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    wedges, _, autotexts = ax.pie(
        values,
        labels=None,
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 4.5 else "",
        pctdistance=0.77,
        startangle=140,
        colors=colors,
        wedgeprops={"width": 0.44, "edgecolor": "#FFFFFF", "linewidth": 2.2},
    )

    for autotext in autotexts:
        autotext.set_color("#FFFFFF")
        autotext.set_fontsize(8.5)
        autotext.set_fontweight("bold")

    ax.text(
        0,
        0.07,
        "Total Spent",
        ha="center",
        va="center",
        fontsize=9,
        color="#64748B",
    )
    ax.text(
        0,
        -0.11,
        f"{currency}{total_spent:,.0f}",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color="#0F172A",
    )

    legend_labels = [
        f"{cat} ({currency}{amt:,.0f})" for cat, amt in zip(labels, values)
    ]
    ax.legend(
        wedges,
        legend_labels,
        title="Categories",
        title_fontsize=9.5,
        fontsize=8.5,
        loc="center left",
        bbox_to_anchor=(0.95, 0.5),
        frameon=False,
    )
    ax.set_title(
        "Category-Wise Expense Distribution",
        fontsize=12,
        fontweight="bold",
        color="#0F172A",
        pad=12,
    )

    fig.tight_layout()
    return fig


def plot_time_bar_chart(
    time_df: pd.DataFrame, mode: str = "Daily", currency: str = "₹"
) -> plt.Figure:
    """Generate a Matplotlib Bar chart for Daily or Monthly spending."""
    if time_df.empty or time_df["Amount"].sum() <= 0:
        return _empty_figure(f"No {mode.lower()} expense data available yet.")

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    labels = time_df["Label"].tolist()
    amounts = time_df["Amount"].tolist()
    avg_val = sum(amounts) / len(amounts)

    bars = ax.bar(
        labels,
        amounts,
        color="#4F46E5",
        alpha=0.9,
        width=0.58,
        zorder=3,
        edgecolor="#4338CA",
        linewidth=0.6,
    )

    max_idx = amounts.index(max(amounts))
    bars[max_idx].set_color("#F59E0B")
    bars[max_idx].set_edgecolor("#D97706")

    ax.axhline(
        avg_val,
        color="#10B981",
        linestyle="--",
        linewidth=1.5,
        zorder=4,
        label=f"Average: {currency}{avg_val:,.0f}",
    )

    if len(bars) <= 15:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(amounts) * 0.02,
                f"{currency}{height:,.0f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                color="#334155",
                fontweight="medium",
            )

    ax.set_title(
        f"{mode} Spending Overview",
        fontsize=12,
        fontweight="bold",
        color="#0F172A",
        pad=14,
    )
    ax.set_ylabel(f"Amount ({currency})", fontsize=9.5, color="#475569")
    ax.grid(axis="y", linestyle=":", alpha=0.5, color="#CBD5E1", zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")

    rotation = 40 if len(labels) > 7 else 0
    ha = "right" if rotation > 0 else "center"
    plt.setp(ax.get_xticklabels(), rotation=rotation, ha=ha, fontsize=8.5, color="#334155")
    plt.setp(ax.get_yticklabels(), fontsize=8.5, color="#334155")
    ax.set_ylim(0, max(amounts) * 1.18)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")

    fig.tight_layout()
    return fig


def plot_cumulative_budget_chart(
    period_df: pd.DataFrame,
    pocket_money: float,
    period_start,
    period_end,
    currency: str = "₹",
) -> plt.Figure:
    """Plot cumulative spend against pocket money limit & ideal linear budget pace."""
    if period_df.empty:
        return _empty_figure("Add expenses in the active cycle to see budget burn-rate.")

    fig, ax = plt.subplots(figsize=(9.5, 3.6), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    date_index = pd.date_range(period_start, period_end, freq="D")
    daily = (
        period_df.assign(day=period_df["expense_date"].dt.floor("D"))
        .groupby("day")["amount"]
        .sum()
        .reindex(date_index, fill_value=0.0)
    )

    today_ts = pd.Timestamp.today().floor("D")
    actual_daily = daily[daily.index <= today_ts]
    cumulative_actual = actual_daily.cumsum()

    ax.plot(
        cumulative_actual.index,
        cumulative_actual.values,
        color="#4F46E5",
        linewidth=2.4,
        marker="o",
        markersize=4,
        label="Actual Cumulative Spend",
        zorder=4,
    )
    ax.fill_between(
        cumulative_actual.index,
        cumulative_actual.values,
        color="#4F46E5",
        alpha=0.10,
        zorder=2,
    )

    if pocket_money > 0:
        ideal_pace = [
            pocket_money * (i + 1) / len(date_index) for i in range(len(date_index))
        ]
        ax.plot(
            date_index,
            ideal_pace,
            color="#10B981",
            linestyle="--",
            linewidth=1.5,
            label="Ideal Linear Pace",
            zorder=3,
        )
        ax.axhline(
            pocket_money,
            color="#EF4444",
            linestyle="-.",
            linewidth=1.5,
            label=f"Pocket Money Limit ({currency}{pocket_money:,.0f})",
            zorder=3,
        )
        ax.axhline(
            pocket_money * 0.8,
            color="#F59E0B",
            linestyle=":",
            linewidth=1.3,
            label=f"80% Warning ({currency}{pocket_money * 0.8:,.0f})",
            zorder=3,
        )

    ax.set_title(
        "Cumulative Budget Burn-Rate vs. Pocket Money Limit",
        fontsize=11.5,
        fontweight="bold",
        color="#0F172A",
        pad=10,
    )
    ax.set_ylabel(f"Cumulative ({currency})", fontsize=9, color="#475569")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
    ax.set_xlim(period_start - timedelta(days=0.3), period_end + timedelta(days=0.3))
    ax.grid(axis="y", linestyle=":", alpha=0.5, color="#CBD5E1", zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")
    plt.setp(ax.get_xticklabels(), fontsize=8.5, color="#334155")
    plt.setp(ax.get_yticklabels(), fontsize=8.5, color="#334155")
    ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)

    fig.tight_layout()
    return fig