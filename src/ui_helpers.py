import streamlit as st
from src.config import EXCEEDED_THRESHOLD_PCT, WARNING_THRESHOLD_PCT


def inject_custom_css() -> None:
    """Apply clean, modern student dashboard CSS enhancements."""
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
        }
        .kpi-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.05rem 1.2rem;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            height: 100%;
        }
        .kpi-label {
            font-size: 0.82rem;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.35rem;
        }
        .kpi-value {
            font-size: 1.65rem;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.2;
        }
        .kpi-sub {
            font-size: 0.8rem;
            color: #475569;
            margin-top: 0.35rem;
        }
        .kpi-accent-indigo { border-top: 4px solid #4F46E5; }
        .kpi-accent-emerald { border-top: 4px solid #10B981; }
        .kpi-accent-amber { border-top: 4px solid #F59E0B; }
        .kpi-accent-rose { border-top: 4px solid #EF4444; }
        .kpi-accent-sky { border-top: 4px solid #0EA5E9; }

        .section-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0F172A;
            margin-top: 0.5rem;
            margin-bottom: 0.75rem;
        }
        .badge-pill {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            background-color: #EEF2FF;
            color: #4338CA;
            margin-bottom: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(
    label: str, value: str, subtext: str, accent: str = "indigo"
) -> None:
    """Render a clean styled KPI summary card."""
    st.markdown(
        f"""
        <div class="kpi-card kpi-accent-{accent}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_budget_alerts(summary: dict, currency: str) -> None:
    """Display dynamic 80% warning, >100% exceeded alert, and remaining balance."""
    usage_pct = summary["usage_pct"]
    remaining = summary["remaining_balance"]
    pocket_money = summary["pocket_money"]
    safe_daily = summary["safe_daily_allowance"]
    days_left = summary["period"]["days_remaining"]

    if pocket_money <= 0:
        st.warning(
            "Pocket money is currently set to 0. Go to **Student Profile** in the sidebar to enter your pocket money.",
            icon="⚠️",
        )
        return

    if usage_pct > EXCEEDED_THRESHOLD_PCT:
        overspent = abs(remaining)
        st.error(
            f"🚨 **Budget Exceeded Alert!** You have used **{usage_pct:.1f}%** of your pocket money and overspent by **{currency}{overspent:,.2f}**. Remaining pocket money: **{currency}0.00**.",
            icon="🚨",
        )
    elif usage_pct >= WARNING_THRESHOLD_PCT:
        st.warning(
            f"⚠️ **80% Budget Warning!** You have already used **{usage_pct:.1f}%** of your pocket money. Remaining pocket money: **{currency}{remaining:,.2f}** (Safe daily limit for next {days_left} day(s): **{currency}{safe_daily:,.2f}/day**).",
            icon="⚠️",
        )
    else:
        st.success(
            f"✅ **Budget On Track ({usage_pct:.1f}% used).** Remaining pocket money: **{currency}{remaining:,.2f}** — you can safely spend up to **{currency}{safe_daily:,.2f}/day** for the remaining {days_left} day(s).",
            icon="✅",
        )