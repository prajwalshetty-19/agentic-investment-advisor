# Agentic AI Investment Advisor 📈🤖

An enterprise-grade, multi-agent AI-powered virtual investment platform and portfolio simulator built with **FastAPI**, **LangGraph**, and **Streamlit**.

> **IMPORTANT DISCLAIMER**: This application is strictly a virtual simulation and paper-trading research platform. All funds, portfolios, orders, and returns are 100% simulated and use virtual currency (INR ₹). The platform does **not** connect to real bank accounts, real brokers, or execute actual financial transactions.

---

## Key Features

- **Multi-Agent AI Analysis**: Orchestrated using LangGraph with 10 specialized agents:
  1. **Planner Agent**: User intent classification, multi-step goal formulation, agent routing.
  2. **Investment Discovery Agent**: Multi-asset screening & ranking (Stocks, Mutual Funds, Bonds, Gold/Silver, FDs, RDs).
  3. **Financial Analysis Agent**: Deterministic quantitative analysis (CAGR, Volatility, Sharpe, Drawdown, YTM, compound interest).
  4. **Research & News Agent**: Real-time market context, macroeconomic factors, sentiment synthesis.
  5. **Document & RAG Agent**: PyMuPDF extraction, semantic embeddings, FAISS vector search, and citation grounding.
  6. **Risk Analysis Agent**: Market, credit, liquidity, interest-rate, and concentration risk profiling.
  7. **Portfolio & Competitor Agent**: Portfolio impact analysis, diversification check, competitor benchmarking.
  8. **Verification Agent**: Mathematical fact-checking, hallucination detection, unit/currency validation.
  9. **Report Generation Agent**: Structured executive summary, numeric tables, disclosures, proposed order draft.
  10. **Order Execution Agent**: Multi-gate simulated paper-trading engine (strict user authorization & validation).

- **Supported Asset Classes**:
  - **Stocks**: US & Indian equities, historical price series, valuation ratios, simulated order book.
  - **Mutual Funds**: NAV-based pricing, expense ratio, category benchmarks, scheme search.
  - **Bonds**: Sovereign & corporate bonds, face value, coupon schedule, clean/dirty price, YTM.
  - **Gold & Silver**: Spot proxy pricing, fractional unit simulated trades.
  - **Fixed Deposits (FDs)**: Compounding schedules, tenure selection, deterministic maturity calculation.
  - **Recurring Deposits (RDs)**: Monthly simulated debits, compound interest formulas, missed deposit handling.

- **Zero-Risk Virtual Wallet**:
  - ₹100,000 initial virtual balance.
  - Strict append-only transaction ledger with atomic database transactions.
  - Double-authorization order execution: Account-level AI toggle + Explicit order approval.

---

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Pydantic v2
- **Agent Orchestration**: LangGraph, Google Gemini API / Free LLM fallback
- **Frontend**: Streamlit, Plotly
- **RAG & Vector Search**: PyMuPDF, Sentence-Transformers, FAISS
- **Database**: SQLite (WAL mode, Foreign Keys, Decimal precision)
- **Testing**: pytest
