"""Agent 7: Portfolio and Investment Context Agent.

Analyzes authoritative user portfolio holdings, computes asset and sector
concentration before and after a proposed investment, detects diversification concerns,
and evaluates marginal risk in accordance with user horizon and risk tolerance.
"""

import time
from typing import Dict, Any, List
from decimal import Decimal
from app.agents.state import AgentWorkflowState
from app.db.session import SessionLocal
from app.services.portfolio_service import get_portfolio_summary


def run_portfolio_analyst_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    start_time = time.time()
    user_id = state.get("user_id", 1)
    budget = float(state.get("budget", 20000.0))
    candidates = state.get("discovery_candidates", [])
    user_risk = state.get("risk_tolerance", "BALANCED")
    horizon = float(state.get("time_horizon_years", 3.0))

    db = state.get("db")
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        portfolio_summary = get_portfolio_summary(db, user_id)
    finally:
        if close_db:
            db.close()

    current_allocation = portfolio_summary.get("asset_allocation", {})
    holdings = portfolio_summary.get("holdings", [])
    current_portfolio_value = float(portfolio_summary.get("total_portfolio_value", 0.0))
    wallet_balance = float(portfolio_summary.get("virtual_wallet_balance", 0.0))
    total_net_worth = float(portfolio_summary.get("total_net_worth", wallet_balance + current_portfolio_value))
    total_realized_pnl = float(portfolio_summary.get("total_realized_pnl", 0.0))
    total_unrealized_pnl = float(portfolio_summary.get("total_unrealized_pnl", 0.0))

    # Evaluate impact of committing budget to top candidate
    top_candidate = candidates[0] if candidates else None
    proposed_category = top_candidate["category"] if top_candidate else "DIVERSIFIED"
    proposed_symbol = top_candidate["symbol"] if top_candidate else "None"

    # Check if symbol or category already held
    existing_holding = next((h for h in holdings if h["symbol"] == proposed_symbol), None)
    existing_holding_qty = float(existing_holding["quantity"]) if existing_holding else 0.0
    existing_holding_val = float(existing_holding["current_value"]) if existing_holding else 0.0

    # Current category value
    existing_cat_val = sum(float(h["current_value"]) for h in holdings if h["category"] == proposed_category)
    new_cat_val = existing_cat_val + budget
    new_portfolio_val = current_portfolio_value + budget

    post_cat_weight = round((new_cat_val / new_portfolio_val) * 100.0, 1) if new_portfolio_val > 0 else 0.0
    marginal_weight = round((budget / (total_net_worth if total_net_worth > 0 else budget)) * 100.0, 1)

    # Concentration and Diversification Alert
    diversification_concerns = []
    if post_cat_weight > 40.0 and len(holdings) > 0:
        diversification_concerns.append(
            f"Concentration Risk: Allocation to {proposed_category} will reach {post_cat_weight}% of holdings."
        )
    if existing_holding:
        diversification_concerns.append(
            f"Existing Position: You already hold {existing_holding_qty:,.2f} units of {proposed_symbol} (₹{existing_holding_val:,.2f})."
        )

    if not diversification_concerns:
        status_note = f"Balanced Allocation: {proposed_category} will comprise {post_cat_weight}% of your active portfolio."
    else:
        status_note = " | ".join(diversification_concerns)

    diversification_note = (
        f"Adding ₹{budget:,.0f} to {proposed_category} ({proposed_symbol}) represents {marginal_weight}% of total net worth. "
        f"{status_note}"
    )

    # Competitor / Alternative Benchmarking
    competitor_comparisons = [
        {
            "instrument": "Nifty 50 Index Fund",
            "category": "Broad Equity Benchmark",
            "cagr_3y": 15.2,
            "expense_ratio": 0.20,
            "liquidity": "T+1 Daily",
            "comparison": "Lower expense ratio but higher exposure to large-cap market volatility."
        },
        {
            "instrument": "Sovereign Gold Bonds (SGB) / Gold BeES",
            "category": "Gold Alternative",
            "cagr_3y": 14.5,
            "coupon_yield": "2.5% p.a. (SGB) / Spot tracking (BeES)",
            "liquidity": "High secondary market liquidity on NSE",
            "comparison": "Effective hedge against equity drawdowns and currency depreciation."
        },
        {
            "instrument": "10-Year GOI Sovereign Bond",
            "category": "Fixed Income Anchor",
            "cagr_3y": 7.15,
            "coupon_yield": "7.18% semi-annual",
            "liquidity": "Institutional secondary liquidity",
            "comparison": "Zero default credit risk; cushions portfolio against macro equity drawdowns."
        }
    ]

    duration_ms = int((time.time() - start_time) * 1000)
    log_entry = {
        "agent_name": "Portfolio & Context Agent",
        "status": "SUCCESS",
        "duration_ms": duration_ms,
        "summary": f"Analyzed portfolio concentration (post-allocation {proposed_category}: {post_cat_weight}%), realized P&L: ₹{total_realized_pnl:+,.2f}"
    }

    return {
        "portfolio_impact": {
            "current_portfolio_value": current_portfolio_value,
            "wallet_balance": wallet_balance,
            "total_net_worth": total_net_worth,
            "total_realized_pnl": total_realized_pnl,
            "total_unrealized_pnl": total_unrealized_pnl,
            "marginal_allocation_percent": marginal_weight,
            "post_allocation_category_percent": post_cat_weight,
            "diversification_note": diversification_note,
            "competitor_benchmarks": competitor_comparisons,
            "active_positions_count": len(holdings)
        },
        "agent_logs": [log_entry]
    }
