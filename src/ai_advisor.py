from typing import Any, Dict, List, Tuple
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import CATEGORIES, DISCRETIONARY_CATEGORIES


# Training phrases for offline NLP Intent Classification (TF-IDF + Cosine Similarity)
INTENT_EXAMPLES: List[Tuple[str, str]] = [
    ("where am i overspending excessive unnecessary waste money", "overspend"),
    ("which expense was too high outlier unusual big purchase", "outliers"),
    ("how much can i safely spend per day daily limit allowance", "daily_limit"),
    ("predict my future spending end of month week balance forecast", "predict"),
    ("how can i save money saving tips cut costs reduce expenses", "save_tips"),
    ("what is my highest top spending category breakdown", "top_category"),
    ("give me summary of my budget remaining balance spent", "summary"),
    ("weekend weekday spending habit pattern behaviour", "behaviour"),
    ("hello hi hey who are you help", "greeting"),
]

_VECTORIZER = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
_INTENT_MATRIX = _VECTORIZER.fit_transform([phrase for phrase, _ in INTENT_EXAMPLES])
_INTENT_LABELS = [label for _, label in INTENT_EXAMPLES]


def generate_financial_analysis(
    profile: Dict[str, Any],
    summary: Dict[str, Any],
    ml_metrics: Dict[str, Any],
    all_df: pd.DataFrame,
) -> str:
    """
    Generate a comprehensive 5-section AI Financial Report locally using
    Pandas analytics, Scikit-Learn LinearRegression, and IsolationForest outputs.
    """
    currency = profile.get("currency", "₹")
    if all_df.empty:
        return "Add a few expense records first so the AI/ML engine can analyze your spending behaviour."

    pocket_money = summary["pocket_money"]
    total_spent = summary["total_spent"]
    remaining = summary["remaining_balance"]
    usage_pct = summary["usage_pct"]
    safe_daily = summary["safe_daily_allowance"]
    days_left = summary["period"]["days_remaining"]
    cat_df = summary["category_summary"]

    # --- Section 1: Spending Behaviour Analysis ---
    pace_status = (
        "exceeded your budget"
        if usage_pct > 100
        else ("entered the high-usage zone (80%+)" if usage_pct >= 80 else "maintained a healthy spending pace")
    )
    behaviour_lines = [
        f"- You have spent **{currency}{total_spent:,.2f}** out of **{currency}{pocket_money:,.2f}** (**{usage_pct:.1f}%**) and **{pace_status}**.",
        f"- **Essential vs. Discretionary Split:** **{ml_metrics['essential_pct']:.1f}%** ({currency}{ml_metrics['essential_amt']:,.2f}) went to essentials (Food, Travel, Stationery), while **{ml_metrics['discretionary_pct']:.1f}%** ({currency}{ml_metrics['discretionary_amt']:,.2f}) went to lifestyle/discretionary categories.",
        f"- **Peak Spending Day:** Your highest spending typically happens on **{ml_metrics['peak_weekday']}**, with **{ml_metrics['weekend_share_pct']:.1f}%** of total spend occurring on weekends.",
    ]
    if not cat_df.empty:
        behaviour_lines.append(
            f"- **Dominant Category:** **{summary['top_category']}** accounts for **{cat_df.iloc[0]['Share (%)']:.1f}%** ({currency}{summary['top_category_amount']:,.2f}) of your active cycle spending."
        )

    # --- Section 2: Unnecessary or Excessive Expenses ---
    excess_lines: List[str] = []
    anomalies = ml_metrics.get("anomalies", [])
    if anomalies:
        excess_lines.append("Our **IsolationForest / Z-Score ML model** flagged these high-value outlier transactions:")
        for a in anomalies[:4]:
            excess_lines.append(
                f"- **{a['date']}** — *{a['category']}*: **{a['description']}** (**{currency}{a['amount']:,.2f}**)"
            )
    else:
        excess_lines.append("- No extreme single-transaction statistical outliers were detected.")

    if not cat_df.empty:
        disc_rows = cat_df[cat_df["Category"].isin(DISCRETIONARY_CATEGORIES)]
        if not disc_rows.empty:
            top_disc = disc_rows.iloc[0]
            if top_disc["Share (%)"] >= 15:
                excess_lines.append(
                    f"- High discretionary concentration in **{top_disc['Category']}** (**{top_disc['Share (%)']:.1f}%** of active spend = **{currency}{top_disc['Amount']:,.2f}**)."
                )

    # --- Section 3: Personalised Money-Saving Suggestions ---
    tips: List[str] = []
    if not cat_df.empty:
        cat_map = {
            row["Category"]: (float(row["Amount"]), float(row["Share (%)"]))
            for _, row in cat_df.iterrows()
        }
        if "Food" in cat_map and cat_map["Food"][1] >= 30:
            save_est = cat_map["Food"][0] * 0.20
            tips.append(
                f"**Optimize Food & Outings (Est. Save: {currency}{save_est:,.0f}):** Food takes **{cat_map['Food'][1]:.1f}%** of your spend. Replacing 2 restaurant/delivery meals per week with hostel mess or tiffin saves ~20%."
            )
        if any(c in cat_map for c in ("Entertainment", "Shopping", "Clothes")):
            disc_sum = sum(cat_map[c][0] for c in ("Entertainment", "Shopping", "Clothes") if c in cat_map)
            save_est = disc_sum * 0.25
            tips.append(
                f"**Apply the 48-Hour Rule on Lifestyle Purchases (Est. Save: {currency}{save_est:,.0f}):** Wait 48 hours before non-urgent Shopping/Clothes/Entertainment spends to cut impulsive buying by ~25%."
            )
        if "Travel" in cat_map and cat_map["Travel"][1] >= 15:
            save_est = cat_map["Travel"][0] * 0.15
            tips.append(
                f"**Use Student Passes for Travel (Est. Save: {currency}{save_est:,.0f}):** Switching short auto/cab rides to metro/bus student passes can trim travel costs by ~15%."
            )

    if ml_metrics["weekend_share_pct"] >= 35:
        tips.append(
            f"**Cap Weekend Spending:** **{ml_metrics['weekend_share_pct']:.1f}%** of your money is spent on weekends. Pre-decide a fixed Saturday–Sunday cash/UPI limit."
        )

    if not tips:
        tips.append(
            f"**Automate Micro-Savings:** Try setting aside **10% ({currency}{pocket_money * 0.10:,.0f})** of your pocket money on Day 1 before spending."
        )

    # --- Section 4: Future Spending Prediction (ML) ---
    proj_spend = ml_metrics["projected_period_spend"]
    proj_bal = ml_metrics["projected_balance"]
    risk_label = (
        "🔴 High Overspend Risk"
        if proj_bal < 0
        else ("🟡 Tight Margin" if proj_bal < pocket_money * 0.15 else "🟢 Safe Surplus Track")
    )
    forecast_lines = [
        f"- **Risk Assessment:** {risk_label}",
        f"- **ML Linear Trend:** Spending trend is **{ml_metrics['trend_direction']}** (daily slope: `{ml_metrics['daily_slope']:+.2f}/day`).",
        f"- **Next 7 Days ML Forecast:** Expected spend is **{currency}{ml_metrics['next_7_days_forecast']:,.2f}**.",
        f"- **End-of-Cycle Projection:** At your current burn rate of **{currency}{ml_metrics['avg_daily_spend']:,.2f}/day**, total cycle spend will reach **{currency}{proj_spend:,.2f}** (Projected ending balance: **{currency}{proj_bal:,.2f}**).",
    ]

    # --- Section 5: Smart Budget Management Plan ---
    plan_lines = [
        f"- **Strict Daily Spending Cap:** Keep daily expenses under **{currency}{safe_daily:,.2f}/day** for the remaining **{days_left} day(s)**.",
        f"- **Recommended Pocket Money Split:** Target **60% Essentials ({currency}{pocket_money * 0.60:,.0f})**, **25% Lifestyle/Outings ({currency}{pocket_money * 0.25:,.0f})**, and **15% Emergency Savings ({currency}{pocket_money * 0.15:,.0f})**.",
        f"- **Current Liquid Buffer:** Remaining balance right now is **{currency}{max(0.0, remaining):,.2f}**.",
    ]

    return (
        "### 1. Spending Behaviour Analysis\n"
        + "\n".join(behaviour_lines)
        + "\n\n### 2. Unnecessary or Excessive Expenses Detected\n"
        + "\n".join(excess_lines)
        + "\n\n### 3. Personalised Money-Saving Suggestions\n"
        + "\n".join(f"- {t}" for t in tips)
        + "\n\n### 4. Future Spending Prediction (Scikit-Learn ML)\n"
        + "\n".join(forecast_lines)
        + "\n\n### 5. Budget Management Plan\n"
        + "\n".join(plan_lines)
    )


def _match_category_entity(question_lower: str) -> str | None:
    """Check if the student is asking about a specific expense category."""
    for cat in CATEGORIES:
        if cat.lower() in question_lower:
            return cat
    return None


def ask_ai_chatbot(
    user_question: str,
    profile: Dict[str, Any],
    summary: Dict[str, Any],
    ml_metrics: Dict[str, Any],
    all_df: pd.DataFrame,
) -> str:
    """
    Offline NLP Chatbot powered by TF-IDF + Cosine Similarity and live SQLite data.
    """
    currency = profile.get("currency", "₹")
    q_clean = user_question.strip().lower()

    if not q_clean:
        return "Please type a question about your budget, categories, or saving tips!"

    # 1. Check if user specifically asked about a category (e.g., "Food", "Travel")
    matched_cat = _match_category_entity(q_clean)
    if matched_cat:
        period_df = summary["period_df"]
        cat_period = period_df[period_df["category"] == matched_cat]
        cat_all = all_df[all_df["category"] == matched_cat]
        p_sum = float(cat_period["amount"].sum()) if not cat_period.empty else 0.0
        a_sum = float(cat_all["amount"].sum()) if not cat_all.empty else 0.0
        pct = (p_sum / summary["total_spent"] * 100.0) if summary["total_spent"] > 0 else 0.0

        recent = cat_all.head(3)
        recent_str = (
            "\n".join(
                f"- {r['expense_date'].strftime('%Y-%m-%d')}: {r['description']} (**{currency}{r['amount']:,.2f}**)"
                for _, r in recent.iterrows()
            )
            if not recent.empty
            else "- No transactions in this category yet."
        )
        return (
            f"### 📂 {matched_cat} Spending Breakdown\n"
            f"- **Active Cycle Spend:** {currency}{p_sum:,.2f} (**{pct:.1f}%** of current spend)\n"
            f"- **All-Time {matched_cat} Spend:** {currency}{a_sum:,.2f} ({len(cat_all)} transaction(s))\n\n"
            f"**Latest {matched_cat} Transactions:**\n{recent_str}"
        )

    # 2. Match Intent via TF-IDF Cosine Similarity
    q_vec = _VECTORIZER.transform([q_clean])
    sims = cosine_similarity(q_vec, _INTENT_MATRIX).flatten()
    best_idx = int(sims.argmax())
    best_score = float(sims[best_idx])
    intent = _INTENT_LABELS[best_idx] if best_score >= 0.12 else "fallback"

    if intent == "greeting":
        return (
            f"Hi **{profile['name']}**! I'm your built-in **Offline AI Finance Assistant**. "
            "Ask me things like:\n"
            "- *Where am I overspending?*\n"
            "- *How much can I safely spend per day?*\n"
            "- *Predict my end-of-cycle balance*\n"
            "- *How much did I spend on Food?*"
        )

    if intent == "daily_limit":
        days_left = summary["period"]["days_remaining"]
        return (
            f"📅 You have **{currency}{max(0.0, summary['remaining_balance']):,.2f}** remaining for the next **{days_left} day(s)**.\n\n"
            f"👉 **Safe Daily Limit:** **{currency}{summary['safe_daily_allowance']:,.2f}/day** "
            f"(your current average burn rate is **{currency}{ml_metrics['avg_daily_spend']:,.2f}/day**)."
        )

    if intent == "predict":
        proj_bal = ml_metrics["projected_balance"]
        status = (
            f"you may **overspend by {currency}{abs(proj_bal):,.2f}**"
            if proj_bal < 0
            else f"you are projected to finish with **{currency}{proj_bal:,.2f} remaining**"
        )
        return (
            f"📈 **ML Spending Forecast:**\n"
            f"- **Next 7 Days Predicted Spend:** {currency}{ml_metrics['next_7_days_forecast']:,.2f} (Trend: *{ml_metrics['trend_direction']}*)\n"
            f"- **Projected End-of-Cycle Total:** {currency}{ml_metrics['projected_period_spend']:,.2f}\n"
            f"- At your current pace, {status}."
        )

    if intent in ("overspend", "outliers"):
        anomalies = ml_metrics.get("anomalies", [])
        lines = [
            f"🔎 **Overspending & High-Spend Check:**",
            f"- **Top Category:** {summary['top_category']} ({currency}{summary['top_category_amount']:,.2f})",
            f"- **Discretionary Share:** {ml_metrics['discretionary_pct']:.1f}% ({currency}{ml_metrics['discretionary_amt']:,.2f})",
        ]
        if anomalies:
            lines.append("\n**Flagged High-Value Outliers (IsolationForest ML):**")
            for a in anomalies[:3]:
                lines.append(
                    f"- {a['date']} | *{a['category']}* — {a['description']} (**{currency}{a['amount']:,.2f}**)"
                )
        else:
            lines.append("- No abnormal outlier transactions were flagged in your history.")
        return "\n".join(lines)

    if intent == "save_tips":
        target_cut = summary["total_spent"] * 0.15
        return (
            f"💡 **Top 3 Ways to Save ~{currency}{target_cut:,.0f} This Cycle:**\n"
            f"1. **Trim {summary['top_category']} by 15%:** It's currently your #1 expense ({currency}{summary['top_category_amount']:,.2f}).\n"
            f"2. **Watch {ml_metrics['peak_weekday']}s & Weekends:** {ml_metrics['weekend_share_pct']:.1f}% of your spend happens on weekends.\n"
            f"3. **Follow Your Daily Cap:** Stick strictly to **{currency}{summary['safe_daily_allowance']:,.2f}/day** for the remaining {summary['period']['days_remaining']} day(s)."
        )

    if intent == "top_category":
        cat_df = summary["category_summary"]
        if cat_df.empty:
            return "You haven't added any expenses in the active cycle yet."
        top_lines = "\n".join(
            f"- **{r['Category']}**: {currency}{r['Amount']:,.2f} ({r['Share (%)']:.1f}%)"
            for _, r in cat_df.head(5).iterrows()
        )
        return f"📊 **Top Categories ({summary['period']['label']}):**\n{top_lines}"

    if intent == "behaviour":
        return (
            f"🧠 **Spending Behaviour Snapshot:**\n"
            f"- **Essentials vs. Lifestyle:** {ml_metrics['essential_pct']:.1f}% Essential / {ml_metrics['discretionary_pct']:.1f}% Discretionary\n"
            f"- **Peak Spending Weekday:** {ml_metrics['peak_weekday']}\n"
            f"- **Weekend Spend Share:** {ml_metrics['weekend_share_pct']:.1f}%"
        )

    if intent == "summary":
        return (
            f"💼 **Current Budget Summary ({summary['period']['label']}):**\n"
            f"- **Pocket Money:** {currency}{summary['pocket_money']:,.2f}\n"
            f"- **Total Spent:** {currency}{summary['total_spent']:,.2f} ({summary['usage_pct']:.1f}%)\n"
            f"- **Remaining Balance:** {currency}{summary['remaining_balance']:,.2f}\n"
            f"- **Top Category:** {summary['top_category']}"
        )

    # Fallback response when query doesn't closely match an intent
    return (
        f"Here is a quick snapshot for **{profile['name']}**: you've spent **{currency}{summary['total_spent']:,.2f}** "
        f"(**{summary['usage_pct']:.1f}%** of {currency}{summary['pocket_money']:,.2f}), with **{currency}{summary['remaining_balance']:,.2f}** remaining.\n\n"
        "Try asking specifically about:\n"
        "- *\"Where am I overspending?\"*\n"
        "- *\"How much can I safely spend per day?\"*\n"
        "- *\"Predict my balance\"*\n"
        "- *\"How much did I spend on Food / Travel / Shopping?\"*"
    )