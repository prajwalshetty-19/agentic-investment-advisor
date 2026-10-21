"""Agent 9: Report Generation Agent.

Synthesizes verified findings into a transparent, executive investment report.
Presents comparative tables, deterministic formulas, citations, risk disclosures,
and prepares a proposed virtual order draft for user approval.
"""

import time
from typing import Dict, Any, List
from app.agents.state import AgentWorkflowState


def run_report_generator_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    start_time = time.time()
    query = state.get("query", "")
    intent = state.get("intent", "DISCOVERY")
    candidates = state.get("discovery_candidates", [])
    financial_metrics = state.get("financial_metrics", {})
    news = state.get("research_news", [])
    documents = state.get("retrieved_documents", [])
    risk = state.get("risk_assessment", {})
    portfolio = state.get("portfolio_impact", {})
    notes = state.get("verification_notes", [])
    budget = state.get("budget", 20000.0)
    horizon = state.get("time_horizon_years", 3.0)

    report_title = f"AI Investment Advisory Report: {query[:60].title()}"
    
    # Build Markdown Content
    md_lines = []
    md_lines.append(f"# {report_title}\n")
    md_lines.append("> **Disclaimer**: *All investments and portfolios shown are 100% virtual and simulated. This platform does not connect to real financial markets, real brokers, or transfer actual funds. Historical returns are not guarantees of future performance.*\n")
    
    # 1. Executive Summary
    md_lines.append("## 1. Executive Summary")
    top_cand = candidates[0] if candidates else None
    if top_cand:
        md_lines.append(
            f"Based on your target budget of **₹{budget:,.0f}**, investment horizon of **{horizon} years**, and stated risk tolerance, "
            f"the multi-agent analysis recommends **{top_cand['name']} ({top_cand['symbol']})** as the leading option (Fit Score: **{top_cand['fit_score']}/100**). "
            f"{top_cand['reason']}\n"
        )
    else:
        md_lines.append(f"Analysis completed for query: *'{query}'* across available virtual multi-asset categories.\n")

    # 2. Comparative Asset Screening Table
    if candidates:
        md_lines.append("## 2. Ranked Instrument Comparison")
        md_lines.append("| Rank | Instrument | Category | Latest Price / NAV | Est. 3Y CAGR / Rate | Fit Score | Instrument Type |")
        md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for i, c in enumerate(candidates, 1):
            proxy_badge = "Physical / Spot Proxy" if c["is_commodity_proxy"] else "Direct / Fund"
            md_lines.append(f"| {i} | **{c['name']}** (`{c['symbol']}`) | {c['category']} | ₹{c['current_price']:,.2f} | {c.get('cagr_3y', 0):.1f}% | **{c['fit_score']}** | {proxy_badge} |")
        md_lines.append("")

    # 3. Deterministic Financial Analytics
    if financial_metrics:
        md_lines.append("## 3. Quantitative Evidence & Financial Metrics")
        md_lines.append("| Instrument | Metric Type | Key Numerical Results | Pricing & Math Model |")
        md_lines.append("| :--- | :--- | :--- | :--- |")
        for sym, q in financial_metrics.items():
            qtype = q.get("type")
            if qtype == "FIXED_DEPOSIT":
                details = f"Maturity: ₹{q['estimated_maturity_value']:,.2f} (Interest: ₹{q['total_interest_earned']:,.2f})"
                model = "Deterministic Compound Interest Formula (Quarterly)"
            elif qtype == "RECURRING_DEPOSIT":
                details = f"Maturity: ₹{q['estimated_maturity_value']:,.2f} on monthly ₹{q['monthly_contribution']:,.2f}"
                model = "Deterministic RD Indian Banking Standard"
            elif qtype == "BOND":
                details = f"Yield to Maturity: {q['yield_to_maturity_percent']:.2f}% | Coupon: {q['coupon_rate_percent']:.2f}%"
                model = "Newton-Raphson YTM Engine"
            else:
                details = f"Volatility: {q.get('annualized_volatility_percent', 0):.1f}% | Sharpe: {q.get('sharpe_ratio', 0):.2f} | Max DD: {q.get('max_drawdown_percent', 0):.1f}%"
                model = "Logarithmic Return Variance & Sharpe Analytics"
            md_lines.append(f"| `{sym}` | {qtype} | {details} | {model} |")
        md_lines.append("")

    # 4. Document Passages & Regulatory Filings (RAG)
    if documents:
        md_lines.append("## 4. Regulatory Disclosures & Document Citations")
        for doc in documents:
            md_lines.append(f"- **[{doc['title']}] (Page {doc['page']})**:")
            md_lines.append(f"  > *\"{doc['excerpt']}\"*")
        md_lines.append("")

    # 5. Market Research & Macro News
    if news:
        md_lines.append("## 5. Market Context & Verified Developments")
        for n in news:
            md_lines.append(f"- **{n['headline']}** ({n['source']} — {n['date']})")
            md_lines.append(f"  - *Summary*: {n['summary']}")
            md_lines.append(f"  - *Provenance*: `{n['fact_vs_opinion']}`")
        md_lines.append("")

    # 6. Risk Profile & Alignment
    if risk:
        md_lines.append("## 6. Risk Assessment & Alignment")
        md_lines.append(f"- **Overall Risk Score**: **{risk.get('overall_risk_score', 50)}/100**")
        md_lines.append(f"- **Suitability Check**: {risk.get('alignment_reason', 'Aligned with user profile.')}")
        md_lines.append("\n**Key Risk Disclosures:**")
        for rf in risk.get("risk_factors", []):
            md_lines.append(f"- **{rf['risk_type']}** [{rf['severity']}]: {rf['description']}")
        md_lines.append("")

    # 7. Portfolio Impact
    if portfolio:
        md_lines.append("## 7. Portfolio Impact & Allocation")
        md_lines.append(f"- {portfolio.get('diversification_note', '')}")
        md_lines.append(f"- Marginal Allocation Weight: **{portfolio.get('marginal_allocation_percent', 0)}%** of virtual net worth.")
        md_lines.append("")

    # 8. Verification Audit Summary
    md_lines.append("## 8. Verification Agent Audit")
    for note in notes:
        md_lines.append(f"- [x] {note}")
    md_lines.append("")

    # Prepare Proposed Order Draft if top candidate exists
    proposed_order = None
    if top_cand:
        price = top_cand["current_price"]
        qty = round(budget / price, 4) if price > 0 else 1.0
        if top_cand["category"] == "STOCK":
            qty = max(1.0, float(int(qty)))  # Integer shares for equities
        total_amt = round(qty * price, 2)
        
        proposed_order = {
            "asset_id": top_cand.get("asset_id"),
            "symbol": top_cand["symbol"],
            "name": top_cand["name"],
            "category": top_cand["category"],
            "side": "BUY",
            "quantity": qty,
            "price": price,
            "total_amount": total_amt,
            "estimated_fee": max(5.0, round(total_amt * 0.001, 2)),
            "status": "DRAFT_PROPOSAL",
            "requires_explicit_user_approval": True,
            "note": "AI-generated order proposal. Must be explicitly approved before execution."
        }

    duration_ms = int((time.time() - start_time) * 1000)
    log_entry = {
        "agent_name": "Report Generation Agent",
        "status": "SUCCESS",
        "duration_ms": duration_ms,
        "summary": "Synthesized comprehensive multi-agent report with verified evidence and proposed order draft"
    }

    full_markdown = "\n".join(md_lines)

    return {
        "final_report_title": report_title,
        "final_report_markdown": full_markdown,
        "proposed_order": proposed_order,
        "agent_logs": [log_entry]
    }
