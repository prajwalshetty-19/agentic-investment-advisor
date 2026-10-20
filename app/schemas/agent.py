"""Pydantic schemas for multi-agent workflows, reports, and discovery."""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    asset_id: Optional[int] = None
    time_horizon_years: Optional[float] = 3.0
    budget: Optional[Decimal] = None
    risk_tolerance: Optional[str] = None


class AgentStepLog(BaseModel):
    agent_name: str
    status: str
    duration_ms: int
    summary: str


class InvestmentOptionCandidate(BaseModel):
    asset_id: Optional[int] = None
    symbol: str
    name: str
    category: str
    current_price_or_nav: Decimal
    historical_cagr: Optional[str] = None
    risk_level: str
    fit_score: float
    reason: str
    is_commodity_proxy: bool = False


class AgentWorkflowResponse(BaseModel):
    session_id: int
    intent: str
    report_title: str
    executive_summary: str
    report_markdown: str
    recommended_options: List[InvestmentOptionCandidate] = []
    proposed_order: Optional[Dict[str, Any]] = None
    data_sources: List[str] = []
    risks_identified: List[str] = []
    verification_passed: bool
    agent_steps: List[AgentStepLog] = []
    created_at: datetime
