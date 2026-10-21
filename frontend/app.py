"""Agentic AI Investment Advisor — Streamlit Web Application."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from decimal import Decimal
from typing import Dict, Any, Optional

from frontend.api_client import ApiClient

st.set_page_config(
    page_title="Agentic AI Investment Advisor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
with open("frontend/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Session State
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"
if "active_order" not in st.session_state:
    st.session_state["active_order"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

api = ApiClient(token=st.session_state.get("token"))


# ==========================================
# AUTHENTICATION SCREEN
# ==========================================
def render_auth_page():
    st.markdown("<h1 style='text-align: center;'>📈 Agentic AI Investment Advisor</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='simulation-banner' style='text-align: center; max-width: 600px; margin: 0 auto 30px auto;'>"
        "⚠️ <strong>VIRTUAL PAPER TRADING SIMULATION PLATFORM</strong><br>"
        "All assets, orders, balances, and returns are strictly virtual. No real money or real brokers are used."
        "</div>",
        unsafe_allow_html=True
    )

    tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Virtual Account"])

    with tab_login:
        st.subheader("Welcome Back")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                login_user = st.text_input("Username or Email", placeholder="e.g. investor_one")
                login_pwd = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In", use_container_width=True)

                if submit:
                    try:
                        res = api.login(login_user, login_pwd)
                        st.session_state["token"] = res["access_token"]
                        # Refresh client with token
                        new_api = ApiClient(token=res["access_token"])
                        st.session_state["user"] = new_api.get_me()
                        st.success("Authentication successful! Loading dashboard...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {e}")

    with tab_register:
        st.subheader("Open Virtual Demo Account (₹100,000 Initial Funds)")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("register_form"):
                reg_user = st.text_input("Choose Username", placeholder="e.g. trader_pro")
                reg_email = st.text_input("Email Address", placeholder="trader@example.com")
                reg_pwd = st.text_input("Password (min 6 characters)", type="password")
                reg_risk = st.selectbox("Your Risk Appetite", ["CONSERVATIVE", "BALANCED", "GROWTH", "AGGRESSIVE"], index=1)
                submit_reg = st.form_submit_button("Register & Receive ₹100,000 Virtual Funds", use_container_width=True)

                if submit_reg:
                    try:
                        res = api.register(reg_user, reg_email, reg_pwd, reg_risk)
                        st.session_state["token"] = res["access_token"]
                        new_api = ApiClient(token=res["access_token"])
                        st.session_state["user"] = new_api.get_me()
                        st.success("Account created with ₹100,000 virtual demo money! Redirecting...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Registration failed: {e}")


# ==========================================
# AUTHENTICATED APP SHELL
# ==========================================
if not st.session_state["token"]:
    render_auth_page()
    st.stop()

# Refresh User Profile & Settings
try:
    current_user = api.get_me()
    st.session_state["user"] = current_user
    wallet_info = api.get_wallet()
except Exception:
    st.session_state["token"] = None
    st.rerun()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("### 📈 **Agentic Advisor**")
    st.markdown(
        f"<div style='background: rgba(59, 130, 246, 0.15); padding: 10px; border-radius: 8px; border-left: 4px solid #3B82F6; margin-bottom: 15px;'>"
        f"<strong>User:</strong> {current_user['username']}<br>"
        f"<strong>Virtual Balance:</strong> ₹{wallet_info['balance']:,.2f}<br>"
        f"<strong>AI Execution:</strong> {'🟢 Enabled' if current_user['settings']['ai_execution_enabled'] else '🔴 Disabled'}"
        f"</div>",
        unsafe_allow_html=True
    )

    page_selection = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "🤖 AI Investment Chat",
            "🔍 Investment Explorer",
            "📑 Advisory Reports",
            "👛 Virtual Wallet",
            "💼 Portfolio Holdings",
            "⚡ Order Confirmation",
            "⚙️ Settings & Security"
        ],
        index=[
            "Dashboard", "AI Investment Chat", "Investment Explorer",
            "Advisory Reports", "Virtual Wallet", "Portfolio Holdings",
            "Order Confirmation", "Settings & Security"
        ].index(st.session_state["page"]) if st.session_state["page"] in [
            "Dashboard", "AI Investment Chat", "Investment Explorer",
            "Advisory Reports", "Virtual Wallet", "Portfolio Holdings",
            "Order Confirmation", "Settings & Security"
        ] else 0
    )
    # Strip icon
    st.session_state["page"] = page_selection.split(" ", 1)[1]

    st.markdown("---")
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["token"] = None
        st.session_state["user"] = None
        st.session_state["page"] = "Dashboard"
        st.rerun()


# Top Simulation Disclaimer Banner
st.markdown(
    "<div class='simulation-banner'>"
    "⚠️ <strong>SIMULATED VIRTUAL PLATFORM</strong>: All balances, orders, and returns are virtual and non-monetary. "
    "Orders require explicit user authorization before simulation execution."
    "</div>",
    unsafe_allow_html=True
)

current_page = st.session_state["page"]


# ==========================================
# PAGE 1: DASHBOARD
# ==========================================
if current_page == "Dashboard":
    st.title("📊 Virtual Investment Dashboard")

    try:
        portfolio = api.get_portfolio()
    except Exception as e:
        st.error(f"Error loading portfolio: {e}")
        portfolio = {
            "total_portfolio_value": 0, "virtual_wallet_balance": 100000,
            "total_net_worth": 100000, "total_unrealized_pnl": 0,
            "total_unrealized_pnl_percent": 0, "asset_allocation": {}, "holdings": []
        }

    # Top KPI Metrics Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>Total Net Worth</div>"
            f"<div class='kpi-value'>₹{portfolio['total_net_worth']:,.2f}</div>"
            f"<div class='kpi-subtext neutral-val'>Holdings + Cash</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    with kpi2:
        st.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>Simulated Holdings Value</div>"
            f"<div class='kpi-value'>₹{portfolio['total_portfolio_value']:,.2f}</div>"
            f"<div class='kpi-subtext neutral-val'>{len(portfolio['holdings'])} Active Positions</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    with kpi3:
        st.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>Available Virtual Cash</div>"
            f"<div class='kpi-value'>₹{portfolio['virtual_wallet_balance']:,.2f}</div>"
            f"<div class='kpi-subtext neutral-val'>Ready to allocate</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    with kpi4:
        pnl = portfolio['total_unrealized_pnl']
        pnl_pct = portfolio['total_unrealized_pnl_percent']
        cls = "positive-val" if pnl >= 0 else "negative-val"
        st.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>Unrealized P&L</div>"
            f"<div class='kpi-value {cls}'>₹{pnl:+,.2f}</div>"
            f"<div class='kpi-subtext {cls}'>{pnl_pct:+.2f}% total return</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    # Charts and Recent Activity
    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("Asset Allocation Breakdown")
        allocation = portfolio.get("asset_allocation", {})
        if allocation and sum(allocation.values()) > 0:
            labels = list(allocation.keys())
            values = [float(v) for v in allocation.values()]
            fig = px.pie(
                names=labels,
                values=values,
                hole=0.55,
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No active holdings yet. 100% of your funds are in liquid virtual cash. Use the AI Chat or Explorer to invest!")

    with c2:
        st.subheader("Recent Virtual Transactions")
        try:
            ledger = api.get_ledger(limit=5)
            if ledger:
                df = pd.DataFrame(ledger)[["created_at", "transaction_type", "amount", "balance_after", "description"]]
                df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.write("No transactions recorded yet.")
        except Exception:
            st.write("No recent transactions.")

    st.markdown("---")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("🤖 Ask AI Advisor for Investment Recommendations", use_container_width=True):
            st.session_state["page"] = "AI Investment Chat"
            st.rerun()
    with b2:
        if st.button("🔍 Explore Asset Catalog & Rates", use_container_width=True):
            st.session_state["page"] = "Investment Explorer"
            st.rerun()


# ==========================================
# PAGE 2: AI INVESTMENT CHAT
# ==========================================
elif current_page == "AI Investment Chat":
    st.title("🤖 Multi-Agent AI Investment Advisor")
    st.markdown("Ask our team of 10 specialized agents to research, verify, and simulate multi-asset investments.")

    # Quick Prompts
    st.markdown("**Quick Preset Queries:**")
    qp1, qp2, qp3 = st.columns(3)
    preset_query = None
    with qp1:
        if st.button("🌟 Compare Gold & Silver options for ₹20,000 (3Y)"):
            preset_query = "Analyze gold as an investment and suggest the best available options for a ₹20,000 virtual investment over three years."
    with qp2:
        if st.button("📈 Analyze Reliance Industries stock (5Y)"):
            preset_query = "Analyze Reliance Industries stock for a five-year investment horizon."
    with qp3:
        if st.button("🛡️ Safe Fixed Deposit options for ₹50,000"):
            preset_query = "Compare fixed deposits and safe recurring deposits for ₹50,000 over 3 years."

    with st.form("chat_query_form"):
        user_query = st.text_area("Your Investment Question / Objective", value=preset_query or "", height=80, placeholder="e.g. Analyze gold as an investment and suggest the best available options for a ₹20,000 virtual investment over three years.")
        col_b, col_h, col_r = st.columns(3)
        with col_b:
            budget_input = st.number_input("Virtual Budget (₹)", value=20000.0, step=5000.0, min_value=100.0)
        with col_h:
            horizon_input = st.number_input("Horizon (Years)", value=3.0, step=0.5, min_value=0.5)
        with col_r:
            risk_input = st.selectbox("Risk Preference", ["CONSERVATIVE", "BALANCED", "GROWTH", "AGGRESSIVE"], index=1)

        run_btn = st.form_submit_button("🚀 Run Multi-Agent Analysis Team", use_container_width=True)

    if run_btn and user_query:
        with st.spinner("Multi-Agent Team Coordinating (Planner ➔ Discovery ➔ Financial ➔ News ➔ RAG ➔ Risk ➔ Verifier ➔ Report)..."):
            try:
                res = api.chat_advisors(
                    query=user_query,
                    budget=budget_input,
                    horizon_years=horizon_input,
                    risk_tolerance=risk_input
                )

                # Show Step Execution Pipeline
                st.subheader("Agent Execution Pipeline & Verification Status")
                for step in res.get("agent_steps", []):
                    st.markdown(
                        f"<div class='agent-step'>"
                        f"<strong>{step['agent_name']}</strong> ({step['duration_ms']}ms) — <code>{step['status']}</code><br>"
                        f"<span style='color: #CBD5E1;'>{step['summary']}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # Render Full Markdown Report
                st.markdown("---")
                st.markdown(res.get("report_markdown", ""))

                # Proposed Order Card
                proposed = res.get("proposed_order")
                if proposed:
                    st.markdown("---")
                    st.subheader("⚡ Proposed Simulated Order Draft")
                    st.markdown(
                        f"<div class='kpi-card' style='border-left: 4px solid #10B981;'>"
                        f"<h4>{proposed['side']} {proposed['quantity']} {proposed['name']} ({proposed['symbol']})</h4>"
                        f"<strong>Price:</strong> ₹{proposed['price']:,.2f} | <strong>Total Cost:</strong> ₹{proposed['total_amount']:,.2f} (Est. Fee: ₹{proposed['estimated_fee']:,.2f})<br>"
                        f"<em>{proposed['note']}</em>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    if st.button("Proceed to Order Confirmation Screen ➔"):
                        # Propose order through API
                        prop_res = api.propose_order(
                            asset_id=proposed["asset_id"],
                            side=proposed["side"],
                            quantity=float(proposed["quantity"])
                        )
                        st.session_state["active_order"] = prop_res
                        st.session_state["page"] = "Order Confirmation"
                        st.rerun()

            except Exception as e:
                st.error(f"Error during agent workflow execution: {e}")


# ==========================================
# PAGE 3: INVESTMENT EXPLORER
# ==========================================
elif current_page == "Investment Explorer":
    st.title("🔍 Multi-Asset Investment Explorer")
    st.markdown("Discover and compare verified instruments across Indian equities, mutual funds, sovereign bonds, commodities, and deposits.")

    cat_filter = st.selectbox(
        "Filter Asset Category",
        ["ALL", "STOCK", "MUTUAL_FUND", "BOND", "COMMODITY", "FD", "RD"]
    )
    search_term = st.text_input("Search by Name or Symbol", placeholder="e.g. Reliance, Gold, SBI, HDFC...")

    try:
        assets = api.get_assets(category=cat_filter, search=search_term)
        if assets:
            for item in assets:
                with st.expander(f"{item['symbol']} — {item['name']} (₹{float(item['latest_price']):,.2f})", expanded=False):
                    c1, c2, c3 = st.columns([1, 1, 1])
                    with c1:
                        st.markdown(f"**Category:** <span class='badge badge-stock'>{item['category']}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Latest Quote:** ₹{float(item['latest_price']):,.2f}")
                        st.markdown(f"**Quote Source:** `{item['quote_source']}`")
                        st.markdown(f"**Simulated Feed:** {'Yes' if item['is_simulated'] else 'Live API'}")
                    with c2:
                        meta = item.get("metadata", {})
                        for k, v in meta.items():
                            st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
                    with c3:
                        st.markdown("**Simulated Actions:**")
                        buy_qty = st.number_input(f"Units for {item['symbol']}", value=1.0, min_value=0.01, key=f"qty_{item['id']}")
                        if st.button(f"Propose BUY {item['symbol']}", key=f"buy_btn_{item['id']}"):
                            prop = api.propose_order(
                                asset_id=item["id"],
                                side="BUY",
                                quantity=buy_qty
                            )
                            st.session_state["active_order"] = prop
                            st.session_state["page"] = "Order Confirmation"
                            st.rerun()
        else:
            st.info("No matching assets found.")
    except Exception as e:
        st.error(f"Error loading assets: {e}")


# ==========================================
# PAGE 4: ADVISORY REPORTS
# ==========================================
elif current_page == "Advisory Reports":
    st.title("📑 Saved Advisory Reports & Evidence")
    try:
        sessions = api.get_sessions()
        if sessions:
            for s in sessions:
                with st.expander(f"Session #{s['session_id']}: {s.get('report_title') or s['query']} ({s['created_at'][:10]})"):
                    rep = api.get_session_report(s["session_id"])
                    st.markdown(rep["content_markdown"])
        else:
            st.info("No saved reports yet. Run an analysis in the AI Investment Chat to generate reports!")
    except Exception as e:
        st.error(f"Error loading reports: {e}")


# ==========================================
# PAGE 5: VIRTUAL WALLET
# ==========================================
elif current_page == "Virtual Wallet":
    st.title("👛 Virtual Wallet & Transaction Ledger")

    w = api.get_wallet()
    w1, w2 = st.columns([1, 1])
    with w1:
        st.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>Available Virtual Balance</div>"
            f"<div class='kpi-value'>₹{w['balance']:,.2f}</div>"
            f"<div class='kpi-subtext neutral-val'>Currency: {w['currency']} (100% Simulated)</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    with w2:
        st.subheader("Virtual Faucet (Demo Funds)")
        with st.form("deposit_form"):
            dep_amt = st.number_input("Add Simulated Funds (₹)", value=25000.0, step=5000.0, min_value=100.0)
            if st.form_submit_button("Credit Virtual Balance"):
                api.deposit_virtual_funds(dep_amt, description="Manual Virtual Faucet Refill")
                st.success(f"Credited ₹{dep_amt:,.2f} to your virtual wallet!")
                st.rerun()

    st.subheader("Immutable Transaction Ledger")
    ledger = api.get_ledger(limit=50)
    if ledger:
        df = pd.DataFrame(ledger)
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(df[["id", "created_at", "transaction_type", "amount", "balance_after", "description"]], use_container_width=True, hide_index=True)
    else:
        st.info("No ledger entries yet.")


# ==========================================
# PAGE 6: PORTFOLIO HOLDINGS
# ==========================================
elif current_page == "Portfolio Holdings":
    st.title("💼 Simulated Portfolio & Positions")
    port = api.get_portfolio()

    st.markdown(
        f"**Total Portfolio Value:** ₹{port['total_portfolio_value']:,.2f} | "
        f"**Total Invested:** ₹{port['total_invested']:,.2f} | "
        f"**Unrealized P&L:** ₹{port['total_unrealized_pnl']:+,.2f} ({port['total_unrealized_pnl_percent']:+.2f}%)"
    )

    holdings = port.get("holdings", [])
    if holdings:
        df = pd.DataFrame(holdings)
        st.dataframe(
            df[["symbol", "name", "category", "quantity", "average_buy_price", "current_price", "current_value", "unrealized_pnl", "weight_percent"]],
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Portfolio Weight Distribution")
        fig = px.bar(
            df,
            x="symbol",
            y="current_value",
            color="category",
            text="weight_percent",
            title="Position Value by Asset (₹)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("You currently hold no simulated assets. Use Explorer or AI Chat to allocate your virtual funds.")


# ==========================================
# PAGE 7: ORDER CONFIRMATION
# ==========================================
elif current_page == "Order Confirmation":
    st.title("⚡ Double-Gate Order Authorization Screen")

    active = st.session_state.get("active_order")
    if not active:
        st.info("No pending order proposal selected. Propose an order from the Explorer or AI Advisor Chat.")
        if st.button("Explore Assets"):
            st.session_state["page"] = "Investment Explorer"
            st.rerun()
        st.stop()

    order_id = active["order_id"]
    ai_enabled = current_user["settings"]["ai_execution_enabled"]

    # Gate 1 Check Indicator
    if not ai_enabled:
        st.error("⛔ **Gate 1 Blocked**: Account-level AI-assisted order execution is disabled in your Settings. You must enable it before approving orders.")
    else:
        st.success("✅ **Gate 1 Verified**: Account-level AI-assisted execution permission is active.")

    # Order Details Card
    st.markdown(
        f"<div class='kpi-card' style='border-left: 4px solid #3B82F6;'>"
        f"<h3>Order Proposal #{order_id}</h3>"
        f"<strong>Instrument:</strong> {active['asset_name']} (<code>{active['asset_symbol']}</code>)<br>"
        f"<strong>Side:</strong> <code>{active['side']}</code> | <strong>Quantity:</strong> {float(active['quantity']):,.4f}<br>"
        f"<strong>Execution Price:</strong> ₹{float(active['price']):,.2f}<br>"
        f"<strong>Estimated Brokerage Fee:</strong> ₹{float(active['estimated_fee']):,.2f}<br>"
        f"<strong>Total Order Impact:</strong> ₹{float(active['total_amount']):,.2f}<br><hr style='border-color: rgba(255,255,255,0.1);'>"
        f"<strong>Current Wallet Balance:</strong> ₹{float(active['current_wallet_balance']):,.2f}<br>"
        f"<strong>Expected Wallet Balance After Fill:</strong> ₹{float(active['expected_balance_after']):,.2f}<br>"
        f"<em>Note: {active.get('simulation_notes', 'Virtual simulation execution')}</em>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown("### Gate 2: Explicit Order Confirmation")
    st.markdown("Any alteration to the asset, side, quantity, or limit price invalidates previous approvals. Do you authorize this transaction?")

    btn_approve, btn_reject, _ = st.columns([1, 1, 2])
    with btn_approve:
        if st.button("✅ EXPLICITLY APPROVE & EXECUTE", type="primary", use_container_width=True, disabled=not ai_enabled):
            try:
                # 1. Submit explicit user approval
                api.approve_order(
                    order_id=order_id,
                    action="APPROVE",
                    approved_qty=float(active["quantity"]),
                    approved_price=float(active["price"]),
                    approved_total=float(active["total_amount"])
                )
                # 2. Trigger paper-trading execution
                exec_res = api.execute_order(order_id)
                st.success(f"🎉 Trade Executed! Trade ID: #{exec_res.get('trade_id')}. Remaining Balance: ₹{exec_res['remaining_wallet_balance']:,.2f}")
                st.session_state["active_order"] = None
                if st.button("View Portfolio"):
                    st.session_state["page"] = "Portfolio Holdings"
                    st.rerun()
            except Exception as e:
                st.error(f"Execution Error: {e}")

    with btn_reject:
        if st.button("❌ REJECT ORDER", use_container_width=True):
            try:
                api.approve_order(
                    order_id=order_id,
                    action="REJECT",
                    approved_qty=float(active["quantity"]),
                    approved_price=float(active["price"]),
                    approved_total=float(active["total_amount"])
                )
                st.warning("Order rejected. No virtual funds or holdings were changed.")
                st.session_state["active_order"] = None
            except Exception as e:
                st.error(f"Error: {e}")


# ==========================================
# PAGE 8: SETTINGS & SECURITY AUDIT
# ==========================================
elif current_page == "Settings & Security":
    st.title("⚙️ Account Settings & Security Audit")

    st.subheader("AI-Assisted Execution Control (Gate 1)")
    is_ai_on = current_user["settings"]["ai_execution_enabled"]

    new_ai_setting = st.toggle(
        "Enable Account-Level AI-Assisted Order Execution",
        value=is_ai_on,
        help="Disabling this prevents any agent-assisted orders from executing, even if approved individually."
    )

    new_risk = st.selectbox(
        "Default Risk Tolerance",
        ["CONSERVATIVE", "BALANCED", "GROWTH", "AGGRESSIVE"],
        index=["CONSERVATIVE", "BALANCED", "GROWTH", "AGGRESSIVE"].index(current_user["settings"]["risk_tolerance"])
    )

    if st.button("Save Settings"):
        api.update_settings(ai_execution_enabled=new_ai_setting, risk_tolerance=new_risk)
        st.success("Settings updated successfully!")
        st.rerun()

    st.markdown("---")
    st.subheader("Immutable Security & Authorization Audit Trail")
    try:
        logs = api.get_audit_logs(limit=50)
        if logs:
            df = pd.DataFrame(logs)[["id", "timestamp", "action", "entity_type", "entity_id", "details"]]
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No audit logs found.")
    except Exception as e:
        st.error(f"Error loading audit trail: {e}")
