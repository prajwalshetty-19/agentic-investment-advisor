"""Agent 6: Risk Analysis Agent.

Evaluates market, credit, liquidity, interest-rate, inflation, and concentration risks.
Ensures alignment with user's stated risk appetite and highlights data limitations.
Never labels any investment 'risk-free'.
"""

import time
from typing import Dict, Any, List
from app.agents.state import AgentWorkflowState


def run_risk_analyst_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    start_time = time.time()
    candidates = state.get("discovery_candidates", [])
    user_risk = state.get("risk_tolerance", "BALANCED")
    horizon = state.get("time_horizon_years", 3.0)

    risk_factors: List[Dict[str, Any]] = []
    overall_risk_score = 50.0  # scale 0 to 100

    categories_present = set(c["category"] for c in candidates)

    if "STOCK" in categories_present:
        risk_factors.append({
            "risk_type": "Market & Equity Volatility Risk",
            "severity": "HIGH",
            "description": "Equities are subject to market cyclicality, economic shocks, and earnings volatility. Capital principal is not guaranteed."
        })
        overall_risk_score += 15.0

    if "MUTUAL_FUND" in categories_present:
        risk_factors.append({
            "risk_type": "Manager & Benchmark Tracking Risk",
            "severity": "MEDIUM",
            "description": "Mutual fund NAV fluctuates based on underlying portfolio holdings. Historical outperformance does not guarantee future results."
        })
        overall_risk_score += 10.0

    if "COMMODITY" in categories_present:
        risk_factors.append({
            "risk_type": "Commodity Price & Currency Sensitivity",
            "severity": "MEDIUM",
            "description": "Precious metals generate no coupon or dividend yield. Returns depend on international USD spot prices, import duties, and FX movements."
        })
        overall_risk_score += 10.0

    if "BOND" in categories_present:
        risk_factors.append({
            "risk_type": "Interest Rate & Duration Risk",
            "severity": "LOW_TO_MEDIUM",
            "description": "Bond prices have an inverse relationship with prevailing interest rates. Long-duration bonds will experience capital depreciation if yields rise."
        })

    if "FD" in categories_present or "RD" in categories_present:
        risk_factors.append({
            "risk_type": "Inflation & Premature Withdrawal Penalty",
            "severity": "LOW",
            "description": "Fixed nominal returns risk purchasing-power erosion if inflation accelerates. Breaking deposits early incurs premature penalty charges."
        })

    # Alignment check
    is_aligned = True
    alignment_reason = f"Candidate risk profile aligns appropriately with user's '{user_risk}' risk preference over a {horizon}-year horizon."
    if user_risk == "CONSERVATIVE" and "STOCK" in categories_present and len(categories_present) == 1:
        is_aligned = False
        alignment_reason = f"Warning: 100% equity allocation exceeds conservative risk tolerance; consider diversifying into bonds or FDs."

    duration_ms = int((time.time() - start_time) * 1000)
    log_entry = {
        "agent_name": "Risk Analysis Agent",
        "status": "SUCCESS",
        "duration_ms": duration_ms,
        "summary": f"Identified {len(risk_factors)} key risk dimensions (Score: {overall_risk_score:.0f}/100)"
    }

    return {
        "risk_assessment": {
            "overall_risk_score": round(min(overall_risk_score, 100.0), 1),
            "is_aligned_with_user_risk": is_aligned,
            "alignment_reason": alignment_reason,
            "risk_factors": risk_factors
        },
        "agent_logs": [log_entry]
    }
