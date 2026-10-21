"""Agent 1: Planner Agent.

Analyzes natural language queries, classifies user intent, extracts budget,
investment horizon, risk profile, and targets, and schedules downstream agent tasks.
"""

import re
import time
from typing import Dict, Any
from app.agents.state import AgentWorkflowState


def run_planner_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    start_time = time.time()
    query = state.get("query", "").lower()
    
    # 1. Intent Classification
    intent = "DISCOVERY"
    target_asset = None
    
    order_keywords = ["buy", "sell", "purchase", "invest in order", "place order", "transact"]
    portfolio_keywords = ["my portfolio", "current holdings", "asset allocation", "rebalance", "net worth"]
    specific_keywords = ["reliance", "tcs", "hdfc", "tatamotors", "infosys", "parag parikh", "nippon", "sbi"]

    if any(k in query for k in order_keywords) and ("execute" in query or "confirm" in query or "order" in query):
        intent = "ORDER_PROPOSAL"
    elif any(k in query for k in portfolio_keywords):
        intent = "PORTFOLIO_REVIEW"
    elif any(k in query for k in specific_keywords):
        intent = "SPECIFIC_ANALYSIS"
        for k in specific_keywords:
            if k in query:
                target_asset = k.upper()
                break
    elif "gold" in query or "silver" in query or "best option" in query or "suggest" in query or "discover" in query or "compare" in query:
        intent = "DISCOVERY"

    # 2. Extract Budget (e.g. "₹20,000", "20000", "50k", "50000")
    budget = state.get("budget", 20000.0)
    budget_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:k|thousand|lakh|crore)?', query)
    if budget_match:
        try:
            raw_val = budget_match.group(1).replace(",", "")
            val = float(raw_val)
            if "k" in query[budget_match.end() - 1:budget_match.end() + 2]:
                val *= 1000
            elif "lakh" in query:
                val *= 100000
            if val > 100:
                budget = val
        except Exception:
            pass

    # 3. Extract Time Horizon (e.g. "3 years", "5-year", "10 months")
    time_horizon = state.get("time_horizon_years", 3.0)
    horizon_match = re.search(r'(\d+)\s*(?:-| )?(year|yr|month|m)', query)
    if horizon_match:
        num = float(horizon_match.group(1))
        unit = horizon_match.group(2)
        if "m" in unit:
            time_horizon = round(num / 12.0, 2)
        else:
            time_horizon = num

    # 4. Extract Risk Tolerance
    risk = state.get("risk_tolerance", "BALANCED")
    if "conservative" in query or "safe" in query or "low risk" in query:
        risk = "CONSERVATIVE"
    elif "aggressive" in query or "high return" in query or "high risk" in query:
        risk = "AGGRESSIVE"
    elif "growth" in query:
        risk = "GROWTH"

    duration_ms = int((time.time() - start_time) * 1000)
    log_entry = {
        "agent_name": "Planner Agent",
        "status": "SUCCESS",
        "duration_ms": duration_ms,
        "summary": f"Classified intent as {intent} (Horizon: {time_horizon}y, Budget: ₹{budget:,.0f}, Risk: {risk})"
    }

    return {
        "intent": intent,
        "target_asset_symbol": target_asset,
        "budget": budget,
        "time_horizon_years": time_horizon,
        "risk_tolerance": risk,
        "agent_logs": [log_entry]
    }
