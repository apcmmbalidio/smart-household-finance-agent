"""Smart Household Finance Agent — Main Application"""
import streamlit as st
from datetime import datetime
import pandas as pd
from PIL import Image
import io, os, tempfile

from config import EXPENSE_CATEGORIES, PAYMENT_METHODS, DEFAULT_BUDGET
from expense_manager import ExpenseManager
from vision_agent import VisionAgent
from charts import (render_pie_chart, render_monthly_bar, render_payment_chart,
                    render_price_tracker, render_payment_category_heatmap)

st.set_page_config(page_title="Household Finance Tracker", page_icon="P", layout="wide", initial_sidebar_state="expanded")

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.block-container{padding-top:1.5rem;max-width:960px}
h1,h2,h3,h4{color:#1B2A4A!important}

/* Sidebar */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1628,#132238);min-width:260px!important}
section[data-testid="stSidebar"] *{color:#c8d6e5!important}
section[data-testid="stSidebar"] .stRadio>div{gap:2px}
section[data-testid="stSidebar"] .stRadio>div[role="radiogroup"] label>div:first-child{display:none!important}
section[data-testid="stSidebar"] .stRadio label{
    padding:11px 18px;border-radius:10px;transition:all .15s;cursor:pointer;
    font-size:13px;font-weight:500;letter-spacing:.2px;
}
section[data-testid="stSidebar"] .stRadio label:hover{background:rgba(255,255,255,.07)!important;color:#fff!important}
section[data-testid="stSidebar"] .stRadio label[data-checked="true"]{background:rgba(255,107,53,.12)!important;color:#FF6B35!important;font-weight:600}
.sidebar-brand{padding:8px 0 18px;border-bottom:1px solid rgba(255,255,255,.08);margin-bottom:14px}
.sidebar-brand h3{color:#fff!important;font-size:17px;font-weight:700;margin:0}
.sidebar-brand .tag{font-size:11px;color:#3d5a7a!important;margin-top:2px}
.sb-budget{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:14px 16px;margin-top:18px;margin-bottom:16px}
.sb-budget .lbl{font-size:10px;text-transform:uppercase;letter-spacing:.8px;color:#3d5a7a!important;margin-bottom:3px}
.sb-budget .val{font-size:20px;font-weight:800;color:#FF6B35!important}

/* Cards */
.hero-card{background:linear-gradient(135deg,#1B2A4A,#2d4373);border-radius:16px;padding:28px 32px;color:#fff;margin-bottom:20px;box-shadow:0 8px 32px rgba(27,42,74,.25)}
.hero-card .label{font-size:12px;font-weight:500;color:#8fa5c4;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.hero-card .amount{font-size:36px;font-weight:800;color:#fff;letter-spacing:-.5px}
.budget-card{background:#fff;border:1px solid #e5e9ef;border-radius:14px;padding:18px 22px;margin-bottom:20px}
.budget-card .label{font-size:11px;font-weight:600;color:#7a8b9e;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.section-title{font-size:15px;font-weight:700;color:#1B2A4A;margin:24px 0 12px}

/* Transactions */
.txn-row{display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid #f0f2f5}
.txn-row:last-child{border-bottom:none}
.txn-left{display:flex;align-items:center;gap:12px}
.txn-icon{width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:700;flex-shrink:0}
.txn-icon.blue{background:#eef2f9;color:#1B2A4A}
.txn-icon.orange{background:#fff3ec;color:#FF6B35}
.txn-desc{font-size:13px;font-weight:600;color:#1B2A4A}
.txn-date{font-size:11px;color:#97a3b4;margin-top:1px}
.txn-amount{font-size:14px;font-weight:700;color:#e74c3c;white-space:nowrap}

/* Stats */
.stat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.stat-box{background:#fff;border:1px solid #e8ecf1;border-radius:14px;padding:16px 14px;text-align:center}
.stat-box .val{font-size:20px;font-weight:800;color:#1B2A4A}
.stat-box .lbl{font-size:10px;font-weight:500;color:#8a96a6;margin-top:3px;text-transform:uppercase;letter-spacing:.3px}
.stat-box.accent .val{color:#FF6B35}.stat-box.warn .val{color:#e74c3c}.stat-box.ok .val{color:#27ae60}
.progress-wrap{background:#f0f2f5;border-radius:8px;height:10px;margin:8px 0 4px;overflow:hidden}
.progress-fill{height:100%;border-radius:8px;transition:width .6s}

/* Alerts */
.alert-warn{background:#fff8f0;border-left:4px solid #FF6B35;border-radius:8px;padding:12px 16px;font-size:13px;color:#5a4028;margin-bottom:16px}
.alert-ok{background:#f0faf4;border-left:4px solid #27ae60;border-radius:8px;padding:12px 16px;font-size:13px;color:#1a5632;margin-bottom:16px}
.alert-over{background:#fef0f0;border-left:4px solid #e74c3c;border-radius:8px;padding:12px 16px;font-size:13px;color:#6b2020;margin-bottom:16px}

/* Welcome */
.welcome-hero{background:linear-gradient(135deg,#0a1628,#1B2A4A);border-radius:24px;padding:56px 40px;text-align:center;margin-bottom:32px;box-shadow:0 12px 40px rgba(10,22,40,.3)}
.welcome-hero .logo{width:64px;height:64px;background:linear-gradient(135deg,#FF6B35,#e8913a);border-radius:16px;display:inline-flex;align-items:center;justify-content:center;margin-bottom:24px;box-shadow:0 6px 24px rgba(255,107,53,.3)}
.welcome-hero .logo span{font-size:28px;font-weight:800;color:#fff}
.welcome-hero h1{font-size:28px;font-weight:800;color:#fff!important;margin-bottom:10px;letter-spacing:-.5px}
.welcome-hero p{font-size:14px;color:#8fa5c4;max-width:420px;margin:0 auto;line-height:1.7}
.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px}
.feature-card{background:#fff;border:1px solid #e8ecf1;border-radius:14px;padding:24px 20px;text-align:center}
.feature-card .fc-icon{width:44px;height:44px;border-radius:12px;display:inline-flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;margin-bottom:12px}
.feature-card .fc-icon.blue{background:#eef2f9;color:#1B2A4A}
.feature-card .fc-icon.orange{background:#fff3ec;color:#FF6B35}
.feature-card .fc-icon.green{background:#f0faf4;color:#27ae60}
.feature-card h4{font-size:14px;font-weight:700;color:#1B2A4A!important;margin-bottom:6px}
.feature-card p{font-size:12px;color:#7a8b9e;line-height:1.5;margin:0}
.setup-section{max-width:440px;margin:0 auto}
.setup-section .label{font-size:12px;font-weight:600;color:#7a8b9e;text-transform:uppercase;letter-spacing:.8px;margin-bottom:16px;text-align:center}

/* Buttons */
.stButton>button{background:linear-gradient(135deg,#1B2A4A,#2d4373);color:#fff;border:none;border-radius:10px;padding:10px 24px;font-weight:600;font-size:14px;transition:all .2s;box-shadow:0 4px 14px rgba(27,42,74,.2)}
.stButton>button:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(27,42,74,.35)}

/* File uploader cleanup */
div[data-testid="stFileUploader"]{border:2px dashed #c8d6e5;border-radius:14px;padding:16px;background:#fafbfc}
div[data-testid="stFileUploader"] section{border:none!important}
div[data-testid="stFileUploader"] button{font-size:13px!important}

/* Hide Streamlit chrome */
footer{visibility:hidden}
.stDeployButton{display:none}
header[data-testid="stHeader"]{background:transparent}
</style>
""", unsafe_allow_html=True)

# ── Init ──
if "em" not in st.session_state:
    st.session_state.em = ExpenseManager()
if "va" not in st.session_state:
    try: st.session_state.va = VisionAgent()
    except ValueError: st.session_state.va = None
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "user_ready" not in st.session_state:
    s = st.session_state.em.get_user_settings()
    if s:
        st.session_state.nickname = s.get("nickname", "User")
        st.session_state.monthly_budget = float(s.get("monthly_budget", DEFAULT_BUDGET))
        st.session_state.user_ready = True
    else:
        st.session_state.user_ready = False
        st.session_state.nickname = ""
        st.session_state.monthly_budget = DEFAULT_BUDGET

em = st.session_state.em
va = st.session_state.va

# ── Welcome ──
if not st.session_state.user_ready:
    st.markdown("""
    <div class="welcome-hero">
        <div class="logo"><span>F</span></div>
        <h1>Household Finance Tracker</h1>
        <p>Track every peso, scan your receipts, and gain insights into your spending habits. Start by setting up your profile below.</p>
    </div>
    <div class="feature-grid">
        <div class="feature-card">
            <div class="fc-icon blue">S</div>
            <h4>Smart Scanning</h4>
            <p>Scan receipts with AI to automatically extract and categorize every item.</p>
        </div>
        <div class="feature-card">
            <div class="fc-icon orange">A</div>
            <h4>Analytics</h4>
            <p>Visualize spending trends, track prices, and compare across payment methods.</p>
        </div>
        <div class="feature-card">
            <div class="fc-icon green">B</div>
            <h4>Budget Control</h4>
            <p>Set monthly limits and get alerts when you are approaching your budget cap.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="setup-section"><div class="label">Create your profile</div></div>', unsafe_allow_html=True)
    _l, col, _r = st.columns([1, 1.4, 1])
    with col:
        with st.form("setup"):
            nick = st.text_input("What should we call you?", placeholder="e.g. Sophie")
            bgt = st.number_input("Monthly budget (PHP)", min_value=100.0, step=500.0, value=5000.0)
            if st.form_submit_button("Continue", use_container_width=True) and nick.strip():
                em.save_user_settings(nick.strip(), bgt)
                st.session_state.nickname = nick.strip()
                st.session_state.monthly_budget = bgt
                st.session_state.user_ready = True
                st.rerun()
    st.stop()

nickname = st.session_state.nickname
budget = st.session_state.monthly_budget

# ── Sidebar ──
with st.sidebar:
    st.markdown(f'<div class="sidebar-brand"><h3>{nickname}\'s Tracker</h3><div class="tag">Household Finance Manager</div></div>', unsafe_allow_html=True)
    page = st.radio("Nav", ["Dashboard", "Add Expense", "Scan Receipt", "Analytics", "History", "Settings"], label_visibility="collapsed")

    pct_sb = min(budget and (em.get_expense_summary(budget)["total_spent"] / budget * 100) or 0, 100)
    bar_c = "#27ae60" if pct_sb < 70 else "#FF6B35" if pct_sb < 90 else "#e74c3c"
    st.markdown(f"""<div class="sb-budget"><div class="lbl">Monthly Budget</div><div class="val">P {budget:,.0f}</div>
    <div style="margin-top:6px"><div class="progress-wrap"><div class="progress-fill" style="width:{pct_sb:.0f}%;background:{bar_c}"></div></div>
    <div style="font-size:10px;color:#3d5a7a;margin-top:2px">{pct_sb:.0f}% used this month</div></div></div>""", unsafe_allow_html=True)

def _greet():
    h = datetime.now().hour
    return "Good Morning" if h < 12 else "Good Afternoon" if h < 17 else "Good Evening"

# ════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════
if page == "Dashboard":
    st.markdown(f"## {_greet()}, {nickname}")
    summary = em.get_expense_summary(budget)
    remaining = summary["remaining_budget"]
    spent = summary["total_spent"]
    pct = min(spent / budget * 100, 100) if budget > 0 else 0
    bar_color = "#27ae60" if pct < 70 else "#FF6B35" if pct < 90 else "#e74c3c"

    st.markdown(f'<div class="hero-card"><div class="label">Remaining Budget</div><div class="amount">P {remaining:,.2f}</div></div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="budget-card"><div class="label">Budget Usage</div>
    <div style="display:flex;justify-content:space-between;font-size:13px;color:#1B2A4A;font-weight:600"><span>P {spent:,.2f} spent</span><span>P {budget:,.2f} limit</span></div>
    <div class="progress-wrap"><div class="progress-fill" style="width:{pct:.1f}%;background:{bar_color}"></div></div>
    <div style="text-align:right;font-size:11px;color:#8a96a6">{pct:.0f}% used</div></div>""", unsafe_allow_html=True)

    if spent > budget:
        st.markdown(f'<div class="alert-over"><b>Over Budget</b> — Exceeded by P {spent-budget:,.2f}.</div>', unsafe_allow_html=True)
    elif remaining < budget * 0.2:
        st.markdown(f'<div class="alert-warn"><b>Low Budget</b> — Only P {remaining:,.2f} left.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-ok"><b>On Track</b> — P {remaining:,.2f} remaining.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Recent Transactions</div>', unsafe_allow_html=True)
    expenses = summary.get("expenses_list", [])
    if expenses:
        colors = ["blue","orange"]
        rows = ""
        for i, e in enumerate(expenses[:8]):
            c = colors[i%2]; ini = e.get("category","O")[0]; desc = e.get("description","")
            try: d = datetime.strptime(e.get("bill_date","")[:10],"%Y-%m-%d").strftime("%b %d, %Y")
            except: d = e.get("bill_date","")
            amt = float(e.get("amount",0))
            brand = e.get("brand","")
            label = f"{brand} {desc}".strip() if brand else desc
            rows += f'<div class="txn-row"><div class="txn-left"><div class="txn-icon {c}">{ini}</div><div><div class="txn-desc">{label}</div><div class="txn-date">{d}</div></div></div><div class="txn-amount">-P {amt:,.2f}</div></div>'
        st.markdown(rows, unsafe_allow_html=True)
    else:
        st.info("No transactions this month.")

# ════════════════════════════════════════════════════
#  ADD EXPENSE
# ════════════════════════════════════════════════════
elif page == "Add Expense":
    st.markdown("## Add Expense")
    with st.form("manual", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            m_desc = st.text_input("Description", placeholder="e.g. Electric Bill")
            m_amt = st.number_input("Amount (PHP)", min_value=0.01, step=0.01)
            m_date = st.date_input("Date", value=datetime.now())
            m_brand = st.text_input("Brand (optional)", placeholder="e.g. Meralco")
        with c2:
            m_cat = st.selectbox("Category", EXPENSE_CATEGORIES)
            m_pay = st.selectbox("Payment Method", PAYMENT_METHODS)
            m_pay_other = ""
            if m_pay == "Other":
                m_pay_other = st.text_input("Specify payment method")
            m_store = st.text_input("Store / Vendor (optional)")
            m_notes = st.text_area("Notes (optional)", height=68)
        if st.form_submit_button("Save Expense", use_container_width=True):
            if m_desc and m_amt > 0:
                ok, msg = em.add_expense(description=m_desc, amount=m_amt, category=m_cat,
                    bill_date=str(m_date), brand=m_brand, store_name=m_store,
                    payment_method=m_pay, payment_method_other=m_pay_other, notes=m_notes)
                st.success(msg) if ok else st.error(msg)
            else:
                st.warning("Enter a description and amount.")

# ════════════════════════════════════════════════════
#  SCAN RECEIPT
# ════════════════════════════════════════════════════
elif page == "Scan Receipt":
    st.markdown("## Scan Receipt")
    st.caption("Upload a receipt. Gemini AI extracts every item with brand and category.")
    if va is None:
        st.error("Vision AI unavailable. Set GEMINI_API_KEY in .env."); st.stop()

    uploaded = st.file_uploader("Upload image", type=["jpg","jpeg","png","webp"])
    if uploaded:
        st.image(Image.open(uploaded), caption="Uploaded receipt", use_container_width=True)
        if st.button("Extract Items with Gemini AI", use_container_width=True):
            with st.spinner("Analyzing receipt..."):
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1])
                tmp.write(uploaded.getbuffer()); tmp.close()
                st.session_state.extracted_data = va.extract_bill_data(tmp.name)
                try: os.unlink(tmp.name)
                except: pass

    if st.session_state.extracted_data:
        data = st.session_state.extracted_data
        if not data.get("success"):
            st.error(f"Extraction failed: {data.get('error')}")
        else:
            items = data.get("items", [])
            # Editable receipt-level fields
            st.markdown('<div class="section-title">Receipt Details</div>', unsafe_allow_html=True)
            rc1, rc2, rc3 = st.columns(3)
            with rc1: r_store = st.text_input("Store Name", value=data.get("store_name",""))
            with rc2: r_total = st.number_input("Receipt Total", value=float(data.get("total_amount",0)), min_value=0.0)
            with rc3: r_date = st.date_input("Receipt Date", value=datetime.now())

            rc4, rc5 = st.columns(2)
            with rc4: r_pay = st.selectbox("Payment Method", PAYMENT_METHODS, key="scan_pay")
            with rc5:
                r_pay_other = ""
                if r_pay == "Other":
                    r_pay_other = st.text_input("Specify payment", key="scan_pay_o")

            if items:
                st.markdown('<div class="section-title">Extracted Items</div>', unsafe_allow_html=True)
                hc = st.columns([0.4, 2, 1.2, 1.2, 1.8, 0.6])
                for h, t in zip(hc, ["", "Item", "Brand", "Amount", "Category", "Qty"]): h.markdown(f"**{t}**")

                edited = []
                for i, it in enumerate(items):
                    cols = st.columns([0.4, 2, 1.2, 1.2, 1.8, 0.6])
                    with cols[0]: inc = st.checkbox(".", True, key=f"i{i}", label_visibility="collapsed")
                    with cols[1]: nm = st.text_input("n", it.get("name",""), key=f"n{i}", label_visibility="collapsed")
                    with cols[2]: br = st.text_input("b", it.get("brand",""), key=f"b{i}", label_visibility="collapsed")
                    with cols[3]: am = st.number_input("a", min_value=0.0, value=float(it.get("total",0)), step=0.01, key=f"a{i}", label_visibility="collapsed")
                    with cols[4]:
                        ic = it.get("category","Other")
                        ci = EXPENSE_CATEGORIES.index(ic) if ic in EXPENSE_CATEGORIES else len(EXPENSE_CATEGORIES)-1
                        ca = st.selectbox("c", EXPENSE_CATEGORIES, ci, key=f"c{i}", label_visibility="collapsed")
                    with cols[5]: st.markdown(f'<div style="padding-top:8px;font-size:11px;color:#8a96a6">x{it.get("quantity",1)}</div>', unsafe_allow_html=True)
                    edited.append({"name":nm,"brand":br,"total":am,"category":ca,"include":inc})

                sel_total = sum(x["total"] for x in edited if x["include"])
                sel_count = sum(1 for x in edited if x["include"])
                st.markdown(f'<div style="text-align:right;font-size:14px;color:#1B2A4A;font-weight:700;margin:8px 0 14px">Selected: {sel_count} items — P {sel_total:,.2f}</div>', unsafe_allow_html=True)

                if st.button("Save All Selected Items", use_container_width=True):
                    saved = 0
                    for x in edited:
                        if x["include"] and x["total"] > 0:
                            ok, _ = em.add_expense(description=x["name"], amount=x["total"],
                                category=x["category"], bill_date=str(r_date), brand=x["brand"],
                                store_name=r_store, payment_method=r_pay, payment_method_other=r_pay_other,
                                notes=f"From receipt: {r_store}")
                            if ok: saved += 1
                    if saved:
                        st.success(f"{saved} item(s) saved.")
                        st.session_state.extracted_data = None
                        st.balloons()
            else:
                st.warning("No items extracted. Try a clearer photo.")

# ════════════════════════════════════════════════════
#  ANALYTICS
# ════════════════════════════════════════════════════
elif page == "Analytics":
    st.markdown("## Analytics")
    all_exp = em.get_all_expenses()
    summary = em.get_expense_summary(budget)

    tab1, tab2, tab3, tab4 = st.tabs(["Spending Breakdown", "Monthly Trends", "Payment Insights", "Price Tracker"])

    with tab1:
        if summary["by_category"]:
            render_pie_chart(summary["by_category"], summary["total_spent"])
        else:
            st.info("No data yet.")

    with tab2:
        render_monthly_bar(all_exp, budget)

    with tab3:
        if summary["by_payment"]:
            st.markdown('<div class="section-title">Spend by Payment Method</div>', unsafe_allow_html=True)
            render_payment_chart(summary["by_payment"])
            st.markdown('<div class="section-title">Payment Method vs Category</div>', unsafe_allow_html=True)
            render_payment_category_heatmap(summary["expenses_list"])
        else:
            st.info("No data yet.")

    with tab4:
        render_price_tracker(all_exp)

# ════════════════════════════════════════════════════
#  HISTORY
# ════════════════════════════════════════════════════
elif page == "History":
    st.markdown("## History")
    hc1, hc2 = st.columns(2)
    with hc1: h_month = st.selectbox("Month", range(1,13), index=datetime.now().month-1, format_func=lambda m: datetime(2000,m,1).strftime("%B"))
    with hc2: h_year = st.selectbox("Year", range(2024, datetime.now().year+1), index=max(0,datetime.now().year-2024))

    summary = em.get_expense_summary(budget, h_year, h_month)
    spent = summary["total_spent"]; rem = summary["remaining_budget"]; cnt = summary["count"]
    sc = "ok" if rem > budget*.2 else ("accent" if rem > 0 else "warn")

    st.markdown(f"""<div class="stat-grid">
    <div class="stat-box accent"><div class="val">P {spent:,.0f}</div><div class="lbl">Total Spent</div></div>
    <div class="stat-box {sc}"><div class="val">P {rem:,.0f}</div><div class="lbl">Remaining</div></div>
    <div class="stat-box"><div class="val">{cnt}</div><div class="lbl">Transactions</div></div></div>""", unsafe_allow_html=True)

    expenses_h = summary.get("expenses_list", [])
    if expenses_h:
        df = pd.DataFrame(expenses_h)
        df["bill_date"] = pd.to_datetime(df["bill_date"]).dt.strftime("%Y-%m-%d")
        show_cols = [c for c in ["bill_date","description","brand","category","amount","payment_method","store_name","notes"] if c in df.columns]
        st.dataframe(df[show_cols].sort_values("bill_date", ascending=False), use_container_width=True, hide_index=True)

        # CSV Export
        csv = df[show_cols].to_csv(index=False).encode("utf-8")
        period = datetime(h_year, h_month, 1).strftime("%B_%Y")
        st.download_button(f"Export {period} to CSV", csv, f"expenses_{period}.csv", "text/csv", use_container_width=True)

        # Delete (collapsible)
        with st.expander("Manage Expenses"):
            opts = [(e["id"], f"{e['bill_date']} - {e['description']} (P {e['amount']})") for e in expenses_h]
            sel = st.selectbox("Select expense to remove", opts, format_func=lambda x: x[1])
            _,dc = st.columns([3,1])
            with dc:
                if st.button("Remove", use_container_width=True):
                    ok, msg = em.delete_expense(sel[0])
                    if ok: st.success(msg); st.rerun()
                    else: st.error(msg)
    else:
        st.info(f"No expenses for {datetime(h_year,h_month,1).strftime('%B %Y')}.")

# ════════════════════════════════════════════════════
#  SETTINGS
# ════════════════════════════════════════════════════
elif page == "Settings":
    st.markdown("## Settings")
    s = em.get_user_settings() or {}
    with st.form("settings"):
        n = st.text_input("Nickname", value=s.get("nickname", nickname))
        b = st.number_input("Monthly Budget (PHP)", min_value=100.0, step=500.0, value=float(s.get("monthly_budget", budget)))
        if st.form_submit_button("Save Changes", use_container_width=True) and n.strip():
            em.save_user_settings(n.strip(), b)
            st.session_state.nickname = n.strip()
            st.session_state.monthly_budget = b
            st.success("Settings updated."); st.rerun()
    st.markdown("---")
    st.markdown('<p style="text-align:center;color:#97a3b4;font-size:11px">Household Finance Tracker v2.0</p>', unsafe_allow_html=True)