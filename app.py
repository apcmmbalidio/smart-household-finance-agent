# ============================================================
# Smart Household Finance Agent — Main Streamlit Application
# ============================================================

import io
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

import os
from config import EXPENSE_CATEGORIES, MONTHLY_BUDGET
from expense_manager import expense_manager
from vision_agent import vision_agent

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="Smart Household Finance Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29, #302b63, #24243e);
        color: #fff;
    }
    section[data-testid="stSidebar"] * { color: #fff !important; }

    /* ── Metric Cards ── */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1rem 1.25rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    div[data-testid="metric-container"] label { color: #a0a0c0 !important; font-size: 0.8rem; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #c084fc !important;
    }

    /* ── Upload Area ── */
    div[data-testid="stFileUploader"] {
        border: 2px dashed #7c3aed;
        border-radius: 12px;
        padding: 1rem;
        background: rgba(124, 58, 237, 0.05);
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
        color: #fff;
        border: none;
        border-radius: 10px;
        padding: 0.55rem 1.4rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.35);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(124, 58, 237, 0.5);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helper: Format Currency ───────────────────────────────

def fmt_currency(amount: float, currency: str = "USD") -> str:
    return f"{currency} {amount:,.2f}"


# ── Sidebar Navigation ────────────────────────────────────

with st.sidebar:
    st.markdown("## 💰 Finance Agent")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["📸 Scan Receipt", "📊 Dashboard", "📋 Expenses", "🤖 AI Insights"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption(f"Model: `{os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20240620')}`")
    st.caption(f"Budget: `${MONTHLY_BUDGET:,.2f}`")


# ═══════════════════════════════════════════════════════════
# PAGE 1 — Scan Receipt
# ═══════════════════════════════════════════════════════════

if page == "📸 Scan Receipt":
    st.title("📸 Scan a Receipt")
    st.markdown("Upload a photo of your receipt and let Claude extract the details automatically.")

    col_upload, col_preview = st.columns([1, 1], gap="large")

    with col_upload:
        uploaded_file = st.file_uploader(
            "Drop your receipt here",
            type=["jpg", "jpeg", "png", "webp"],
            help="Supports JPG, PNG, and WebP formats.",
        )
        extra_context = st.text_input(
            "Optional context",
            placeholder="e.g. Grocery run at Tesco KL, paid with Grab Pay",
        )
        analyse_btn = st.button("✨ Analyse Receipt", use_container_width=True)

    if uploaded_file:
        image = Image.open(io.BytesIO(uploaded_file.read()))
        with col_preview:
            st.image(image, caption="Uploaded Receipt", use_container_width=True)

    if analyse_btn and uploaded_file:
        with st.spinner("Claude is reading your receipt…"):
            try:
                result = vision_agent.analyse_receipt(image, extra_context or None)
                st.success("✅ Receipt analysed successfully!")

                # ── Display extracted data ──────────────────
                st.markdown("### Extracted Details")
                info_col1, info_col2, info_col3 = st.columns(3)
                info_col1.metric("Store", result.get("store_name") or "—")
                info_col2.metric(
                    "Total",
                    fmt_currency(
                        result.get("total_amount") or 0,
                        result.get("currency") or "USD",
                    ),
                )
                info_col3.metric("Category", result.get("category") or "Other")

                if result.get("items"):
                    st.markdown("#### Line Items")
                    items_df = pd.DataFrame(result["items"])
                    st.dataframe(items_df, use_container_width=True, hide_index=True)

                # ── Save to database ────────────────────────
                st.markdown("### Save to Database")
                with st.form("save_expense_form"):
                    s_store = st.text_input("Store Name", value=result.get("store_name") or "")
                    s_date = st.date_input("Date", value=date.fromisoformat(result["date"]) if result.get("date") else date.today())
                    s_amount = st.number_input("Total Amount", value=float(result.get("total_amount") or 0), step=0.01)
                    s_currency = st.text_input("Currency", value=result.get("currency") or "USD")
                    # Safely get index for the extracted category
                    default_cat = result.get("category", "Other")
                    if default_cat not in EXPENSE_CATEGORIES:
                        default_cat = "Other"
                    default_index = EXPENSE_CATEGORIES.index(default_cat)

                    s_category = st.selectbox(
                        "Category",
                        EXPENSE_CATEGORIES,
                        index=default_index,
                    )
                    s_payment = st.text_input("Payment Method", value=result.get("payment_method") or "")
                    s_notes = st.text_area("Notes", value=result.get("notes") or "")
                    submitted = st.form_submit_button("💾 Save Expense")

                if submitted:
                    expense_manager.add_expense(
                        total_amount=s_amount,
                        category=s_category,
                        store_name=s_store or None,
                        expense_date=str(s_date),
                        currency=s_currency,
                        items=result.get("items") or [],
                        payment_method=s_payment or None,
                        notes=s_notes or None,
                    )
                    st.success("Expense saved! 🎉")

            except Exception as exc:
                st.error(f"❌ Analysis failed: {exc}")
    elif analyse_btn:
        st.warning("Please upload a receipt image first.")


# ═══════════════════════════════════════════════════════════
# PAGE 2 — Dashboard
# ═══════════════════════════════════════════════════════════

elif page == "📊 Dashboard":
    st.title("📊 Spending Dashboard")

    expenses = expense_manager.get_all_expenses()

    if not expenses:
        st.info("No expenses recorded yet. Scan a receipt to get started!")
        st.stop()

    df = pd.DataFrame(expenses)
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ── KPI Row ───────────────────────────────────────────
    total_spent = df["total_amount"].sum()
    avg_expense = df["total_amount"].mean()
    num_expenses = len(df)
    top_category = df.groupby("category")["total_amount"].sum().idxmax()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Spent", f"${total_spent:,.2f}")
    k2.metric("Avg per Transaction", f"${avg_expense:,.2f}")
    k3.metric("Total Transactions", str(num_expenses))
    k4.metric("Top Category", top_category)

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        cat_totals = df.groupby("category")["total_amount"].sum().reset_index()
        fig_pie = px.pie(
            cat_totals,
            names="category",
            values="total_amount",
            title="Spending by Category",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Purples_r,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0e0",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        df["month"] = df["date"].dt.to_period("M").astype(str)
        monthly = df.groupby("month")["total_amount"].sum().reset_index()
        fig_bar = px.bar(
            monthly,
            x="month",
            y="total_amount",
            title="Monthly Spending",
            color="total_amount",
            color_continuous_scale="Purples",
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0e0",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE 3 — Expenses Table
# ═══════════════════════════════════════════════════════════

elif page == "📋 Expenses":
    st.title("📋 Expense History")

    # ── Filters ───────────────────────────────────────────
    f1, f2, f3 = st.columns([2, 2, 1])
    with f1:
        start = st.date_input("From", value=date.today() - timedelta(days=30))
    with f2:
        end = st.date_input("To", value=date.today())
    with f3:
        category_filter = st.selectbox(
            "Category",
            ["All"] + EXPENSE_CATEGORIES,
        )

    expenses = expense_manager.get_expenses_by_date_range(str(start), str(end))

    if category_filter != "All":
        expenses = [e for e in expenses if e.get("category") == category_filter]

    if not expenses:
        st.info("No expenses found for the selected filters.")
    else:
        df = pd.DataFrame(expenses)
        display_cols = [c for c in ["date", "store_name", "category", "total_amount", "currency", "payment_method", "notes"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        # ── Quick delete ──────────────────────────────────
        with st.expander("🗑️ Delete an Expense"):
            del_id = st.text_input("Expense UUID to delete")
            if st.button("Delete", type="primary") and del_id:
                success = expense_manager.delete_expense(del_id)
                st.success("Deleted!") if success else st.error("Not found.")


# ═══════════════════════════════════════════════════════════
# PAGE 4 — AI Insights
# ═══════════════════════════════════════════════════════════

elif page == "🤖 AI Insights":
    st.title("🤖 AI Spending Insights")
    st.markdown("Let Claude analyse your recent expenses and give personalised advice.")

    expenses = expense_manager.get_all_expenses(limit=50)

    if not expenses:
        st.info("No expenses to analyse yet.")
        st.stop()

    df = pd.DataFrame(expenses)
    st.markdown(f"**Analysing your last {len(df)} transactions…**")

    if st.button("✨ Generate Insights", use_container_width=True):
        with st.spinner("Claude is crunching your numbers…"):
            try:
                summary = vision_agent.summarise_expenses(expenses)
                st.markdown("---")
                st.markdown(summary)
            except Exception as exc:
                st.error(f"❌ Insight generation failed: {exc}")
