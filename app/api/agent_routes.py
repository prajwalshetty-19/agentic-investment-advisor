"""Multi-Agent Advisory and Chat API endpoints."""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, AnalysisSession, AgentRun, AnalysisReport
from app.core.dependencies import get_current_user, get_client_ip
from app.core.audit import record_audit_log
from app.schemas.agent import AgentQueryRequest, AgentWorkflowResponse, AgentStepLog, InvestmentOptionCandidate
from app.agents.state import AgentWorkflowState
from app.agents.graph import execute_agent_workflow

router = APIRouter(prefix="/api/agents", tags=["AI Agents"])


@router.post("/chat", response_model=AgentWorkflowResponse)
def run_agent_advisory_chat(
    req: AgentQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers the LangGraph multi-agent advisory team to research, analyze,
    verify, and report on an investment goal or asset.
    """
    # 1. Create analysis session
    session = AnalysisSession(
        user_id=current_user.id,
        query=req.query,
        status="IN_PROGRESS"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 2. Prepare initial state
    initial_state: AgentWorkflowState = {
        "session_id": session.id,
        "user_id": current_user.id,
        "query": req.query,
        "db": db,
        "intent": "DISCOVERY",
        "time_horizon_years": float(req.time_horizon_years or 3.0),
        "budget": float(req.budget or 20000.0),
        "risk_tolerance": req.risk_tolerance or (current_user.settings.risk_tolerance if current_user.settings else "BALANCED"),
        "target_asset_symbol": None,
        "missing_info": [],
        "discovery_candidates": [],
        "financial_metrics": {},
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

    # 3. Execute LangGraph workflow
    final_state = execute_agent_workflow(initial_state)

    # 4. Save agent run records
    for log in final_state.get("agent_logs", []):
        agent_run = AgentRun(
            session_id=session.id,
            agent_name=log["agent_name"],
            status=log["status"],
            duration_ms=log["duration_ms"],
            input_data=json.dumps({"query": req.query}),
            output_data=json.dumps({"summary": log["summary"]})
        )
        db.add(agent_run)

    # 5. Save final report
    report = AnalysisReport(
        session_id=session.id,
        user_id=current_user.id,
        title=final_state.get("final_report_title", "Investment Advisory Report"),
        content_markdown=final_state.get("final_report_markdown", ""),
        structured_metrics_json=json.dumps({
            "metrics": final_state.get("financial_metrics", {}),
            "risk": final_state.get("risk_assessment", {}),
            "portfolio": final_state.get("portfolio_impact", {}),
            "proposed_order": final_state.get("proposed_order")
        })
    )
    db.add(report)

    session.status = "COMPLETED"
    db.commit()

    ip = get_client_ip(request)
    record_audit_log(
        db=db,
        user_id=current_user.id,
        action="RUN_AGENT_WORKFLOW",
        entity_type="ANALYSIS_SESSION",
        entity_id=session.id,
        details={"query": req.query, "intent": final_state.get("intent")},
        ip_address=ip
    )

    # Format response candidates
    candidates_out = []
    for c in final_state.get("discovery_candidates", []):
        candidates_out.append(InvestmentOptionCandidate(
            asset_id=c.get("asset_id"),
            symbol=c["symbol"],
            name=c["name"],
            category=c["category"],
            current_price_or_nav=c["current_price"],
            historical_cagr=f"{c.get('cagr_3y', 0):.1f}%",
            risk_level=c.get("risk_level", "MEDIUM"),
            fit_score=float(c.get("fit_score", 70.0)),
            reason=c.get("reason", ""),
            is_commodity_proxy=c.get("is_commodity_proxy", False)
        ))

    agent_steps_out = [
        AgentStepLog(
            agent_name=l["agent_name"],
            status=l["status"],
            duration_ms=l["duration_ms"],
            summary=l["summary"]
        )
        for l in final_state.get("agent_logs", [])
    ]

    return AgentWorkflowResponse(
        session_id=session.id,
        intent=final_state.get("intent", "DISCOVERY"),
        report_title=final_state.get("final_report_title", "Investment Advisory Report"),
        executive_summary=f"Analysis completed across {len(candidates_out)} instruments with {len(agent_steps_out)} agent verification steps.",
        report_markdown=final_state.get("final_report_markdown", ""),
        recommended_options=candidates_out,
        proposed_order=final_state.get("proposed_order"),
        data_sources=["Authoritative Database Market Quotes", "Deterministic Math Engine", "Financial Filings Vector Store"],
        risks_identified=[rf["risk_type"] for rf in final_state.get("risk_assessment", {}).get("risk_factors", [])],
        verification_passed=final_state.get("verification_passed", True),
        agent_steps=agent_steps_out,
        created_at=datetime.now(timezone.utc)
    )


@router.get("/sessions", response_model=List[Dict[str, Any]])
def list_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists past research sessions for the authenticated user."""
    sessions = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.user_id == current_user.id)
        .order_by(AnalysisSession.created_at.desc())
        .limit(50)
        .all()
    )
    result = []
    for s in sessions:
        report = s.report
        result.append({
            "session_id": s.id,
            "query": s.query,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "report_title": report.title if report else None
        })
    return result


@router.get("/sessions/{session_id}/report", response_model=Dict[str, Any])
def get_session_report(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full analysis report for a specific session."""
    session = (
        db.query(AnalysisSession)
        .filter(AnalysisSession.id == session_id, AnalysisSession.user_id == current_user.id)
        .first()
    )
    if not session or not session.report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return {
        "session_id": session.id,
        "query": session.query,
        "title": session.report.title,
        "content_markdown": session.report.content_markdown,
        "structured_metrics": json.loads(session.report.structured_metrics_json or "{}"),
        "created_at": session.report.created_at.isoformat()
    }
