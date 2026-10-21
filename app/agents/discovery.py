"""Agent 2: Investment Discovery Agent.

Screens across Stocks, Mutual Funds, Bonds, Commodities (Gold/Silver),
FDs, and RDs based on budget, risk appetite, and time horizon.
Distinguishes between commodity physical holding vs exchange-traded instruments.
"""

import time
from typing import Dict, Any, List
from decimal import Decimal
from app.agents.state import AgentWorkflowState
from app.db.session import SessionLocal
from app.db.models import Asset
from app.services.pricing_service import list_all_assets_with_quotes


def run_discovery_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    start_time = time.time()
    query = state.get("query", "").lower()
    budget = state.get("budget", 20000.0)
    risk = state.get("risk_tolerance", "BALANCED")
    horizon = state.get("time_horizon_years", 3.0)

    db = state.get("db")
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        all_assets = list_all_assets_with_quotes(db)
    finally:
        if close_db:
            db.close()

    candidates: List[Dict[str, Any]] = []

    # Filter based on query commodity or asset class
    is_gold_query = "gold" in query
    is_silver_query = "silver" in query
    is_fixed_income = "bond" in query or "fd" in query or "deposit" in query or "safe" in query

    for item in all_assets:
        symbol = item["symbol"]
        cat = item["category"]
        price = float(item["latest_price"])
        meta = item["metadata"]
        name = item["name"]

        # Commodity matching:
        if is_gold_query:
            if "GOLD" not in symbol and "gold" not in name.lower():
                continue
        elif is_silver_query:
            if "SILVER" not in symbol and "silver" not in name.lower():
                continue
        elif is_fixed_income:
            if cat not in ("BOND", "FD", "RD"):
                continue

        # Fit score calculation based on risk and horizon
        cagr = meta.get("cagr_3y") or meta.get("coupon_rate") or meta.get("interest_rate") or 10.0
        cagr = float(cagr)
        volatility = meta.get("volatility_1y", 15.0)

        fit_score = 70.0
        if risk == "CONSERVATIVE":
            if cat in ("BOND", "FD", "RD"):
                fit_score += 20.0
            elif volatility < 15.0:
                fit_score += 10.0
            else:
                fit_score -= 15.0
        elif risk in ("GROWTH", "AGGRESSIVE"):
            if cagr > 15.0:
                fit_score += 20.0
            if cat in ("STOCK", "MUTUAL_FUND"):
                fit_score += 10.0

        if horizon >= 3.0 and cat in ("STOCK", "MUTUAL_FUND", "COMMODITY"):
            fit_score += 5.0

        is_proxy = False
        reason = f"Offers {cagr:.1f}% estimated annual return profile."
        if "SPOT" in symbol:
            is_proxy = True
            reason += " Physical indicative spot price for asset ownership."
        elif "BEES" in symbol or "ETF" in name:
            is_proxy = True
            reason += " High-liquidity exchange-traded proxy with fractional units."

        candidates.append({
            "asset_id": item["id"],
            "symbol": symbol,
            "name": name,
            "category": cat,
            "current_price": price,
            "cagr_3y": cagr,
            "volatility_1y": volatility,
            "risk_level": "LOW" if cat in ("BOND", "FD", "RD") else ("MEDIUM" if cat == "COMMODITY" else "HIGH"),
            "fit_score": round(fit_score, 1),
            "reason": reason,
            "is_commodity_proxy": is_proxy
        })

    # Sort candidates by fit_score descending
    candidates.sort(key=lambda x: x["fit_score"], reverse=True)
    top_candidates = candidates[:5]

    duration_ms = int((time.time() - start_time) * 1000)
    log_entry = {
        "agent_name": "Investment Discovery Agent",
        "status": "SUCCESS",
        "duration_ms": duration_ms,
        "summary": f"Discovered {len(top_candidates)} matching instruments across asset classes"
    }

    return {
        "discovery_candidates": top_candidates,
        "agent_logs": [log_entry]
    }
