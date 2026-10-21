"""Agent Workflow State definition for LangGraph orchestration."""

import operator
from typing import TypedDict, List, Dict, Any, Optional, Annotated


class AgentStepRecord(TypedDict):
    agent_name: str
    status: str
    duration_ms: int
    summary: str


class CandidateInstrument(TypedDict):
    asset_id: Optional[int]
    symbol: str
    name: str
    category: str
    current_price: float
    cagr_3y: Optional[float]
    volatility_1y: Optional[float]
    risk_level: str
    fit_score: float
    reason: str
    is_commodity_proxy: bool


class AgentWorkflowState(TypedDict):
    # Context
    session_id: int
    user_id: int
    query: str
    db: Optional[Any]
    
    # Planner outputs
    intent: str  # DISCOVERY, SPECIFIC_ANALYSIS, PORTFOLIO_REVIEW, ORDER_PROPOSAL
    time_horizon_years: float
    budget: float
    risk_tolerance: str
    target_asset_symbol: Optional[str]
    missing_info: List[str]

    # Agent specialized outputs
    discovery_candidates: List[CandidateInstrument]
    financial_metrics: Dict[str, Any]
    research_news: List[Dict[str, Any]]
    retrieved_documents: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    portfolio_impact: Dict[str, Any]
    
    # Verification & Report
    verification_passed: bool
    verification_notes: List[str]
    final_report_title: str
    final_report_markdown: str
    proposed_order: Optional[Dict[str, Any]]

    # System tracking with list reducers
    agent_logs: Annotated[List[AgentStepRecord], operator.add]
    errors: Annotated[List[str], operator.add]
