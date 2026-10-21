"""Tests for Agent 8: Verification Agent."""

from app.agents.state import AgentWorkflowState
from app.agents.verifier import run_verification_agent


def test_verification_agent_passes_consistent_math():
    state: AgentWorkflowState = {
        "session_id": 1,
        "user_id": 1,
        "query": "Test query",
        "intent": "DISCOVERY",
        "time_horizon_years": 3.0,
        "budget": 20000.0,
        "risk_tolerance": "BALANCED",
        "target_asset_symbol": None,
        "missing_info": [],
        "discovery_candidates": [],
        "financial_metrics": {
            "SBI_FD_1Y": {
                "type": "FIXED_DEPOSIT",
                "principal": 20000.0,
                "annual_rate_percent": 7.0,
                "tenure_years": 3.0,
                # Exact formula value: 20000 * (1 + 0.07/4)^12 = 24628.79
                "estimated_maturity_value": 24628.79,
                "total_interest_earned": 4628.79
            }
        },
        "research_news": [],
        "retrieved_documents": [
            {
                "title": "SBI Term Deposit Terms",
                "page": 3,
                "excerpt": "Quarterly compounding interest rates apply."
            }
        ],
        "risk_assessment": {},
        "portfolio_impact": {},
        "verification_passed": False,
        "verification_notes": [],
        "final_report_title": "",
        "final_report_markdown": "",
        "proposed_order": None,
        "agent_logs": [],
        "errors": []
    }

    result = run_verification_agent(state)
    assert result["verification_passed"] is True
    assert any("VERIFIED: FD arithmetic exactly matches" in note for note in result["verification_notes"])


def test_verification_agent_flags_arithmetic_mismatch():
    state: AgentWorkflowState = {
        "session_id": 1,
        "user_id": 1,
        "query": "Test query",
        "intent": "DISCOVERY",
        "time_horizon_years": 3.0,
        "budget": 20000.0,
        "risk_tolerance": "BALANCED",
        "target_asset_symbol": None,
        "missing_info": [],
        "discovery_candidates": [],
        "financial_metrics": {
            "BOGUS_FD": {
                "type": "FIXED_DEPOSIT",
                "principal": 20000.0,
                "annual_rate_percent": 7.0,
                "tenure_years": 3.0,
                # False fabricated number: 35000 (hallucinated)
                "estimated_maturity_value": 35000.00,
                "total_interest_earned": 15000.00
            }
        },
        "research_news": [],
        "retrieved_documents": [],
        "risk_assessment": {},
        "portfolio_impact": {},
        "verification_passed": False,
        "verification_notes": [],
        "final_report_title": "",
        "final_report_markdown": "",
        "proposed_order": None,
        "agent_logs": [],
        "errors": []
    }

    result = run_verification_agent(state)
    assert result["verification_passed"] is False
    assert any("REJECTED: FD maturity calculation mismatch" in note for note in result["verification_notes"])
