from datetime import date, timedelta
import streamlit as st

from src.ai_advisor import ask_ai_chatbot, generate_financial_analysis
from src.analytics import (
    calculate_spending_summary,
    expenses_to_dataframe,
    filter_expenses,
    get_time_series_summary,
    run_ml_spending_analysis,
)
from src.charts import (
    plot_category_pie_chart,
    plot_cumulative_budget_chart,
    plot_time_bar_chart,
)
from src.config import BUDGET_TYPES, CATEGORIES, CURRENCIES
from src.database import (
    DatabaseError,
    add_expense,
    clear_all_expenses,
    delete_expense,
    get_all_expenses,
    get_profile,
    init_db,
    update_expense,
    update_profile,
)
from src.ui_helpers import inject_custom_css, render_budget_alerts, render_kpi_card
from seed_data import seed_demo_data

st.set_page_config(
    page_title="AI-Powered Student Expense Tracker",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()


def _init_session_state() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi! I'm **PocketPulse AI**, your built-in offline finance assistant. "
                    "Ask me anything about your spending habits, categories, daily allowance, or predictions!"
                ),
            }
        ]
    if "ai_report" not in st.session_state:
        st.session_state.ai_report = None


def _load_app_data():
    init_db()
    profile = get_profile()
    expenses = get_all_expenses()
    df = expenses_to_dataframe(expenses)
    summary = calculate_spending_summary(df, profile)
    return profile, expenses, df, summary


def render_dashboard_page(profile, df, summary) -> None:
    currency = profile.get("currency", "₹")
    period = summary["period"]

    st.title("🎓 AI-Powered Student Expense Tracker")
    st.markdown(
        f'<span class="badge-pill">👤 {profile["name"]} &nbsp;|&nbsp; 📅 {period["label"]} &nbsp;|&nbsp; 🔄 {profile["budget_type"]} Budget</span>',
        unsafe_allow_html=True,
    )

    render_budget_alerts(summary, currency)
    st.write("")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card(
            "Pocket Money",
            f"{currency}{summary['pocket_money']:,.2f}",
            f"{profile['budget_type']} allowance",
            accent="indigo",
        )
    with col2:
        render_kpi_card(
            "Total Spent",
            f"{currency}{summary['total_spent']:,.2f}",
            f"{summary['transaction_count']} txn(s) this cycle",
            accent="sky",
        )
    with col3:
        rem = summary["remaining_balance"]
        render_kpi_card(
            "Remaining Balance",
            f"{currency}{rem:,.2f}",
            f"Safe cap: {currency}{summary['safe_daily_allowance']:,.0f}/day",
            accent="emerald" if rem > 0 else "rose",
        )
    with col4:
        pct = summary["usage_pct"]
        pct_accent = "rose" if pct > 100 else ("amber" if pct >= 80 else "emerald")
        render_kpi_card(
            "Budget Used",
            f"{pct:.1f}%",
            f"{period['days_remaining']} day(s) left in cycle",
            accent=pct_accent,
        )
    with col5:
        render_kpi_card(
            "Top Category",
            summary["top_category"],
            f"{currency}{summary['top_category_amount']:,.2f} spent",
            accent="amber",
        )

    st.write("")
    progress_val = min(max(summary["usage_pct"] / 100.0, 0.0), 1.0)
    st.progress(
        progress_val,
        text=f"Budget Usage: {currency}{summary['total_spent']:,.2f} / {currency}{summary['pocket_money']:,.2f} ({summary['usage_pct']:.1f}%)",
    )

    st.divider()

    left_col, right_col = st.columns([1, 1.1], gap="large")
    with left_col:
        st.markdown('<div class="section-title">Category-Wise Breakdown</div>', unsafe_allow_html=True)
        pie_fig = plot_category_pie_chart(summary["category_summary"], currency=currency)
        st.pyplot(pie_fig, width="stretch")

    with right_col:
        hdr_col, toggle_col = st.columns([1.4, 1])
        with hdr_col:
            st.markdown('<div class="section-title">Spending Trend</div>', unsafe_allow_html=True)
        with toggle_col:
            bar_mode = st.radio(
                "View mode",
                options=["Daily", "Monthly"],
                horizontal=True,
                label_visibility="collapsed",
            )
        time_df = get_time_series_summary(df, mode=bar_mode)
        bar_fig = plot_time_bar_chart(time_df, mode=bar_mode, currency=currency)
        st.pyplot(bar_fig, width="stretch")

    st.write("")
    burn_col, table_col = st.columns([1.35, 1], gap="large")
    with burn_col:
        st.markdown('<div class="section-title">Budget Pace & Burn-Rate</div>', unsafe_allow_html=True)
        burn_fig = plot_cumulative_budget_chart(
            summary["period_df"],
            summary["pocket_money"],
            period["start_date"],
            period["end_date"],
            currency=currency,
        )
        st.pyplot(burn_fig, width="stretch")

    with table_col:
        st.markdown('<div class="section-title">Category Spending Summary</div>', unsafe_allow_html=True)
        cat_df = summary["category_summary"]
        if cat_df.empty:
            st.info("No expenses recorded in the active period yet.")
        else:
            display_cat = cat_df.copy()
            display_cat["Amount"] = display_cat["Amount"].map(lambda x: f"{currency}{x:,.2f}")
            display_cat["Share (%)"] = display_cat["Share (%)"].map(lambda x: f"{x:.1f}%")
            st.dataframe(display_cat, hide_index=True, width="stretch")


def render_add_expense_page(profile, df) -> None:
    currency = profile.get("currency", "₹")
    st.title("➕ Add New Expense")
    st.caption("Log your daily spending. Records are permanently saved in SQLite.")

    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input(
                f"Expense Amount ({currency})",
                min_value=0.0,
                step=10.0,
                format="%.2f",
            )
            category = st.selectbox("Category", options=CATEGORIES)
        with col2:
            expense_date = st.date_input(
                "Expense Date",
                value=date.today(),
                max_value=date.today() + timedelta(days=365),
            )
            description = st.text_input(
                "Description",
                placeholder="e.g., College canteen lunch, Metro recharge, Notebook",
                max_chars=120,
            )

        submitted = st.form_submit_button("💾 Save Expense", type="primary", width="stretch")

        if submitted:
            if amount <= 0:
                st.error("Please enter an expense amount greater than 0.")
            elif not description.strip():
                st.error("Please enter a brief description of the expense.")
            else:
                ok, msg = add_expense(
                    amount=amount,
                    category=category,
                    description=description,
                    expense_date=expense_date.strftime("%Y-%m-%d"),
                )
                if ok:
                    st.success(f"{msg} ({category}: {currency}{amount:,.2f})")
                    st.session_state.ai_report = None
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()
    st.subheader("🕒 Recent 5 Expenses")
    if df.empty:
        st.info("No expenses added yet. Add your first expense above!")
    else:
        recent = df.head(5)[["id", "expense_date", "category", "amount", "description"]].copy()
        recent["expense_date"] = recent["expense_date"].dt.strftime("%Y-%m-%d")
        recent["amount"] = recent["amount"].map(lambda x: f"{currency}{x:,.2f}")
        recent.columns = ["ID", "Date", "Category", "Amount", "Description"]
        st.dataframe(recent, hide_index=True, width="stretch")


def render_history_page(profile, expenses, df) -> None:
    currency = profile.get("currency", "₹")
    st.title("📋 Expense History, Edit & Delete")
    st.caption("Search, filter, export, edit, or delete any saved expense record.")

    if df.empty:
        st.info("Your expense history is empty. Go to **Add Expense** to record transactions.")
        return

    with st.expander("🔍 Search & Filter Expenses", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.5, 1, 1])
        with f_col1:
            search_query = st.text_input(
                "Search Description / Keyword",
                placeholder="e.g., coffee, metro, book...",
            )
        with f_col2:
            selected_categories = st.multiselect(
                "Filter by Category",
                options=CATEGORIES,
                default=CATEGORIES,
            )
        min_date = df["expense_date"].dt.date.min()
        max_date = df["expense_date"].dt.date.max()
        with f_col3:
            start_date = st.date_input("From Date", value=min_date, min_value=min_date, max_value=max_date)
        with f_col4:
            end_date = st.date_input("To Date", value=max_date, min_value=min_date, max_value=max_date)

    if start_date > end_date:
        st.error("'From Date' cannot be later than 'To Date'.")
        return

    filtered_df = filter_expenses(
        df,
        search_query=search_query,
        categories=selected_categories,
        start_date=start_date,
        end_date=end_date,
    )

    m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
    m_col1.metric("Matching Transactions", len(filtered_df))
    m_col2.metric(
        "Filtered Total",
        f"{currency}{filtered_df['amount'].sum():,.2f}" if not filtered_df.empty else f"{currency}0.00",
    )
    with m_col3:
        if not filtered_df.empty:
            csv_export = filtered_df[["id", "expense_date", "category", "amount", "description"]].copy()
            csv_export["expense_date"] = csv_export["expense_date"].dt.strftime("%Y-%m-%d")
            st.download_button(
                "⬇️ Download Filtered CSV",
                data=csv_export.to_csv(index=False).encode("utf-8"),
                file_name="student_expenses.csv",
                mime="text/csv",
                width="stretch",
            )

    if filtered_df.empty:
        st.warning("No expenses match the selected filters.")
    else:
        display_df = filtered_df[["id", "expense_date", "category", "amount", "description"]].copy()
        display_df["expense_date"] = display_df["expense_date"].dt.strftime("%Y-%m-%d")
        display_df["amount"] = display_df["amount"].map(lambda x: f"{currency}{x:,.2f}")
        display_df.columns = ["ID", "Date", "Category", "Amount", "Description"]
        st.dataframe(display_df, hide_index=True, width="stretch")

    st.divider()
    st.subheader("✏️ Edit or 🗑️ Delete an Expense")
    expense_map = {
        exp["id"]: f"#{exp['id']} | {exp['expense_date']} | {exp['category']} | {currency}{exp['amount']:,.2f} — {exp['description']}"
        for exp in expenses
    }
    selected_id = st.selectbox(
        "Select Expense Record",
        options=list(expense_map.keys()),
        format_func=lambda eid: expense_map[eid],
    )
    selected_record = next(item for item in expenses if item["id"] == selected_id)

    edit_tab, delete_tab = st.tabs(["✏️ Edit Selected Expense", "🗑️ Delete Selected Expense"])

    with edit_tab:
        with st.form("edit_expense_form"):
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                new_amount = st.number_input(
                    f"Amount ({currency})",
                    min_value=0.01,
                    value=float(selected_record["amount"]),
                    step=10.0,
                    format="%.2f",
                )
                cat_idx = CATEGORIES.index(selected_record["category"]) if selected_record["category"] in CATEGORIES else 0
                new_category = st.selectbox("Category", options=CATEGORIES, index=cat_idx)
            with e_col2:
                parsed_dt = date.fromisoformat(selected_record["expense_date"])
                new_date = st.date_input("Date", value=parsed_dt)
                new_desc = st.text_input("Description", value=selected_record["description"], max_chars=120)

            save_changes = st.form_submit_button("💾 Update Expense", type="primary")
            if save_changes:
                ok, msg = update_expense(
                    expense_id=selected_id,
                    amount=new_amount,
                    category=new_category,
                    description=new_desc,
                    expense_date=new_date.strftime("%Y-%m-%d"),
                )
                if ok:
                    st.success(msg)
                    st.session_state.ai_report = None
                    st.rerun()
                else:
                    st.error(msg)

    with delete_tab:
        st.warning(f"You are about to permanently delete: **{expense_map[selected_id]}**")
        confirm_delete = st.checkbox("Confirm permanent deletion of this expense record")
        if st.button("🗑️ Delete Expense Permanently", type="primary", disabled=not confirm_delete):
            ok, msg = delete_expense(selected_id)
            if ok:
                st.success(msg)
                st.session_state.ai_report = None
                st.rerun()
            else:
                st.error(msg)


def render_ai_advisor_page(profile, df, summary) -> None:
    currency = profile.get("currency", "₹")
    st.title("🤖 AI Financial Advisor & Chatbot")
    st.caption("100% Offline AI/ML Engine — Powered by Scikit-Learn (LinearRegression, IsolationForest & TF-IDF NLP)")

    ml_metrics = run_ml_spending_analysis(df, summary)

    tab_insights, tab_chat = st.tabs(["📊 AI Insights & ML Forecast", "💬 Ask AI Expense Chatbot"])

    with tab_insights:
        st.subheader("📈 Data Science & ML Spending Forecast")
        if not ml_metrics["has_data"]:
            st.info("Add a few expenses to unlock ML trend forecasting and anomaly detection.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Avg Daily Spend", f"{currency}{ml_metrics['avg_daily_spend']:,.2f}")
            m2.metric(
                "Projected Cycle Spend",
                f"{currency}{ml_metrics['projected_period_spend']:,.2f}",
                delta=f"Est. Bal: {currency}{ml_metrics['projected_balance']:,.0f}",
                delta_color="normal" if ml_metrics["projected_balance"] >= 0 else "inverse",
            )
            m3.metric("Next 7 Days (LinearRegression)", f"{currency}{ml_metrics['next_7_days_forecast']:,.2f}")
            m4.metric("Spending Trend", ml_metrics["trend_direction"], delta=f"Peak: {ml_metrics['peak_weekday']}")

            if ml_metrics["anomalies"]:
                with st.expander(f"🔎 {len(ml_metrics['anomalies'])} ML Outlier(s) Detected (IsolationForest)"):
                    st.dataframe(ml_metrics["anomalies"], hide_index=True, width="stretch")

        st.divider()
        st.subheader("✨ Smart AI Financial Report")
        col_btn, col_info = st.columns([1, 2.2])
        with col_btn:
            run_ai = st.button(
                "🚀 Generate AI Spending Report",
                type="primary",
                disabled=df.empty,
                width="stretch",
            )
        with col_info:
            st.caption(
                "Analyses spending habits, flags unnecessary expenses, predicts future spend, "
                "and builds a personalised budget plan — no API key required."
            )

        if run_ai or (st.session_state.ai_report is None and not df.empty):
            st.session_state.ai_report = generate_financial_analysis(
                profile, summary, ml_metrics, df
            )

        if st.session_state.ai_report:
            st.markdown(st.session_state.ai_report)

    with tab_chat:
        top_c1, top_c2 = st.columns([3, 1])
        with top_c1:
            st.write("Chat with the built-in NLP assistant about your live SQLite expenses.")
        with top_c2:
            if st.button("🧹 Clear Chat", width="stretch"):
                st.session_state.chat_messages = [
                    {
                        "role": "assistant",
                        "content": "Chat cleared! What would you like to know about your expenses?",
                    }
                ]
                st.rerun()

        st.caption("Try asking:")
        q_cols = st.columns(3)
        quick_prompts = [
            "Where am I overspending?",
            "How much can I safely spend per day?",
            "Give me ways to save money",
        ]
        selected_quick_prompt = None
        for idx, q_text in enumerate(quick_prompts):
            if q_cols[idx].button(q_text, key=f"quick_q_{idx}", width="stretch"):
                selected_quick_prompt = q_text

        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask about your budget, food spend, forecast, or saving tips...")
        active_question = selected_quick_prompt or user_input

        if active_question:
            st.session_state.chat_messages.append({"role": "user", "content": active_question})
            with st.chat_message("user"):
                st.markdown(active_question)

            reply = ask_ai_chatbot(
                user_question=active_question,
                profile=profile,
                summary=summary,
                ml_metrics=ml_metrics,
                all_df=df,
            )
            with st.chat_message("assistant"):
                st.markdown(reply)

            st.session_state.chat_messages.append({"role": "assistant", "content": reply})


def render_profile_page(profile, summary) -> None:
    currency = profile.get("currency", "₹")
    st.title("👤 Student Profile & Settings")
    st.caption("Configure your name, budget cycle, pocket money, and demo dataset.")

    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card("Active Student", profile["name"], f"Cycle: {profile['budget_type']}", "indigo")
    with c2:
        render_kpi_card(
            "Pocket Money Set",
            f"{currency}{summary['pocket_money']:,.2f}",
            summary["period"]["label"],
            "sky",
        )
    with c3:
        rem = summary["remaining_balance"]
        render_kpi_card(
            "Available Balance",
            f"{currency}{rem:,.2f}",
            f"Spent: {currency}{summary['total_spent']:,.2f}",
            "emerald" if rem >= 0 else "rose",
        )

    st.write("")
    with st.form("profile_form"):
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            name = st.text_input("Student Name", value=profile["name"], max_chars=80)
            budget_idx = BUDGET_TYPES.index(profile["budget_type"]) if profile["budget_type"] in BUDGET_TYPES else 1
            budget_type = st.selectbox("Budget Type", options=BUDGET_TYPES, index=budget_idx)
        with p_col2:
            pocket_money = st.number_input(
                "Actual Pocket Money Received",
                min_value=0.0,
                value=float(profile["pocket_money"]),
                step=100.0,
                format="%.2f",
            )
            curr_idx = CURRENCIES.index(currency) if currency in CURRENCIES else 0
            selected_currency = st.selectbox("Currency Symbol", options=CURRENCIES, index=curr_idx)

        save_profile = st.form_submit_button("💾 Save Student Profile", type="primary")
        if save_profile:
            ok, msg = update_profile(
                name=name,
                budget_type=budget_type,
                pocket_money=pocket_money,
                currency=selected_currency,
            )
            if ok:
                st.success(msg)
                st.session_state.ai_report = None
                st.rerun()
            else:
                st.error(msg)

    st.divider()
    st.subheader("🧪 Demo & Testing Data Manager")
    st.caption("Quickly load realistic college expenses for testing/presentation, or reset your database.")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        if st.button("📥 Load Sample Student Expenses", width="stretch"):
            seed_demo_data()
            st.session_state.ai_report = None
            st.success("Loaded 28 sample student expense records!")
            st.rerun()
    with d_col2:
        if st.button("🗑️ Clear All Expenses", width="stretch"):
            ok, msg = clear_all_expenses()
            if ok:
                st.session_state.ai_report = None
                st.warning(msg)
                st.rerun()
            else:
                st.error(msg)


def main() -> None:
    _init_session_state()

    try:
        profile, expenses, df, summary = _load_app_data()
    except DatabaseError as exc:
        st.error(f"Critical Database Error: {exc}")
        st.stop()

    currency = profile.get("currency", "₹")

    with st.sidebar:
        st.markdown("## 🎓 PocketPulse AI")
        st.caption("Student Expense & Budget Tracker")

        page = st.radio(
            "Navigation",
            options=[
                "🏠 Dashboard",
                "➕ Add Expense",
                "📋 Expense History",
                "🤖 AI Advisor & Chat",
                "👤 Student Profile",
            ],
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown(f"**Student:** {profile['name']}")
        st.markdown(f"**Cycle:** {profile['budget_type']}")
        st.metric(
            "Available Balance",
            f"{currency}{summary['remaining_balance']:,.2f}",
            delta=f"{summary['usage_pct']:.1f}% used",
            delta_color="inverse",
        )

        if summary["usage_pct"] > 100:
            st.error("🚨 Budget Exceeded!")
        elif summary["usage_pct"] >= 80:
            st.warning("⚠️ 80%+ Budget Used")

        st.divider()
        st.caption("AI/ML Engine: 🟢 Built-in Offline")
        st.caption("Storage: SQLite (Persistent)")

    if page == "🏠 Dashboard":
        render_dashboard_page(profile, df, summary)
    elif page == "➕ Add Expense":
        render_add_expense_page(profile, df)
    elif page == "📋 Expense History":
        render_history_page(profile, expenses, df)
    elif page == "🤖 AI Advisor & Chat":
        render_ai_advisor_page(profile, df, summary)
    elif page == "👤 Student Profile":
        render_profile_page(profile, summary)


if __name__ == "__main__":
    main()