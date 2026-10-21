"""LangGraph Multi-Agent Orchestration Graph.

Coordinates Planner, Discovery, Financial, Research, RAG, Risk, Portfolio,
Verification, and Report Generation agents into a unified, stateful pipeline.
"""

from typing import Dict, Any
import logging
from app.agents.state import AgentWorkflowState
from app.agents.planner import run_planner_agent
from app.agents.discovery import run_discovery_agent
from app.agents.financial_analyst import run_financial_analysis_agent
from app.agents.researcher import run_research_agent
from app.agents.rag_agent import run_rag_agent
from app.agents.risk_analyst import run_risk_analyst_agent
from app.agents.portfolio_analyst import run_portfolio_analyst_agent
from app.agents.verifier import run_verification_agent
from app.agents.report_generator import run_report_generator_agent

logger = logging.getLogger(__name__)


def build_langgraph_workflow():
    """Builds and compiles the LangGraph StateGraph workflow."""
    try:
        from langgraph.graph import StateGraph, START, END

        builder = StateGraph(AgentWorkflowState)

        # Register nodes
        builder.add_node("planner", run_planner_agent)
        builder.add_node("discovery", run_discovery_agent)
        builder.add_node("financial_analyst", run_financial_analysis_agent)
        builder.add_node("researcher", run_research_agent)
        builder.add_node("rag_agent", run_rag_agent)
        builder.add_node("risk_analyst", run_risk_analyst_agent)
        builder.add_node("portfolio_analyst", run_portfolio_analyst_agent)
        builder.add_node("verifier", run_verification_agent)
        builder.add_node("report_generator", run_report_generator_agent)

        # Define edge flow
        builder.add_edge(START, "planner")
        builder.add_edge("planner", "discovery")
        builder.add_edge("discovery", "financial_analyst")
        builder.add_edge("financial_analyst", "researcher")
        builder.add_edge("researcher", "rag_agent")
        builder.add_edge("rag_agent", "risk_analyst")
        builder.add_edge("risk_analyst", "portfolio_analyst")
        builder.add_edge("portfolio_analyst", "verifier")
        builder.add_edge("verifier", "report_generator")
        builder.add_edge("report_generator", END)

        return builder.compile()
    except Exception as e:
        logger.warning(f"LangGraph compilation deferred: {e}. Sequential pipeline fallback enabled.")
        return None


# Cached compiled graph
_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_langgraph_workflow()
    return _compiled_graph


def execute_agent_workflow(initial_state: AgentWorkflowState) -> AgentWorkflowState:
    """
    Executes the multi-agent workflow.
    Uses compiled LangGraph graph if available, otherwise executes pipeline sequentially.
    """
    graph = get_compiled_graph()
    if graph is not None:
        try:
            return graph.invoke(initial_state)
        except Exception as e:
            logger.error(f"Error in LangGraph invoke: {e}. Executing sequential pipeline.")

    # Resilient sequential execution
    state = initial_state.copy()
    agent_sequence = [
        ("Planner", run_planner_agent),
        ("Discovery", run_discovery_agent),
        ("Financial", run_financial_analysis_agent),
        ("Researcher", run_research_agent),
        ("RAG", run_rag_agent),
        ("Risk", run_risk_analyst_agent),
        ("Portfolio", run_portfolio_analyst_agent),
        ("Verifier", run_verification_agent),
        ("Report", run_report_generator_agent)
    ]

    for name, agent_fn in agent_sequence:
        output = agent_fn(state)
        for k, v in output.items():
            if k == "agent_logs":
                state["agent_logs"].extend(v)
            elif k == "errors":
                state["errors"].extend(v)
            else:
                state[k] = v

    return state
