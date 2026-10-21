"""Agent 5: Document and RAG Agent.

Retrieves factual passages from company annual reports, mutual fund Scheme
Information Documents (SIDs), bond term sheets, and regulatory disclosures.
Grounds claims in source citations with page numbers.
"""

import time
from typing import Dict, Any, List
from app.agents.state import AgentWorkflowState
from app.services.rag_service import query_rag_documents


def run_rag_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    start_time = time.time()
    query = state.get("query", "")
    target = state.get("target_asset_symbol", "")
    candidates = state.get("discovery_candidates", [])

    search_query = query
    if target:
        search_query = f"{target} financials debt capital expenditure business risks"
    elif candidates:
        top_symbol = candidates[0]["symbol"]
        search_query = f"{top_symbol} investment strategy returns risk factor disclosures"

    retrieved = query_rag_documents(search_query, top_k=3)

    formatted_docs: List[Dict[str, Any]] = []
    for r in retrieved:
        formatted_docs.append({
            "title": r.get("document_title", "Financial Disclosure Document"),
            "doc_type": r.get("document_type", "FILING"),
            "page": r.get("page", 1),
            "excerpt": r.get("content", ""),
            "relevance_score": r.get("score", 0.0)
        })

    duration_ms = int((time.time() - start_time) * 1000)
    log_entry = {
        "agent_name": "Document & RAG Agent",
        "status": "SUCCESS",
        "duration_ms": duration_ms,
        "summary": f"Retrieved {len(formatted_docs)} cited document passages from vector store"
    }

    return {
        "retrieved_documents": formatted_docs,
        "agent_logs": [log_entry]
    }
