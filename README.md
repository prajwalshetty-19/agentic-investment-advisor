# Agentic AI Investment Advisor 📈🤖

An enterprise-grade, multi-agent AI-powered virtual investment platform and portfolio simulator built with **FastAPI**, **LangGraph**, and **Streamlit**.

> ⚠️ **IMPORTANT DISCLAIMER**: This application is strictly an educational virtual simulation and paper-trading research platform. All funds, portfolios, orders, and returns are 100% simulated and use virtual currency (INR ₹). The platform does **not** connect to real bank accounts, real brokers, or execute actual financial transactions.

---

## 🌟 Key Features

- **10 Specialized LangGraph Agents**:
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

- **Multi-Asset Categories Supported**:
  - **Stocks**: US & Indian equities, historical price series, valuation ratios, simulated order book.
  - **Mutual Funds**: NAV-based pricing, expense ratio, category benchmarks, scheme search.
  - **Bonds**: Sovereign & corporate bonds, face value, coupon schedule, clean/dirty price, YTM.
  - **Gold & Silver**: Spot proxy pricing, fractional unit simulated trades.
  - **Fixed Deposits (FDs)**: Compounding schedules, tenure selection, deterministic maturity calculation.
  - **Recurring Deposits (RDs)**: Monthly simulated debits, compound interest formulas, missed deposit handling.

- **Zero-Risk Simulated Wallet & Double-Gate Authorization**:
  - ₹0 initial default balance upon registration.
  - Realistic simulated funding via **UPI (Simulation)** with preset amounts and custom VPAs.
  - Full **Buy and Sell** workflows with partial sales and realized P&L tracking.
  - Strict append-only transaction ledger with atomic database transactions.
  - **Gate 1**: Account-level AI toggle (`ai_execution_enabled`). If disabled, all agent-assisted orders are blocked.
  - **Gate 2**: Explicit, immutable order-level confirmation. Any price/quantity modification invalidates previous approval.

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone and Setup Environment
```bash
git clone https://github.com/prajwalshetty-19/agentic-investment-advisor.git
cd agentic-investment-advisor

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize Database & Seed Multi-Asset Catalog
```bash
python -m app.db.init_db
```
This sets up SQLite in Write-Ahead Logging (WAL) mode and seeds initial stocks, mutual funds, sovereign bonds, gold/silver spot/ETFs, and bank term deposit rate sheets.

### 4. Run the Automated Test Suite
```bash
pytest tests/ -v
```

### 5. Launch the Platform

In terminal 1 (FastAPI Backend):
```bash
python run_backend.py
```
Backend API will be accessible at `http://127.0.0.1:8000` (Swagger docs at `http://127.0.0.1:8000/docs`).

In terminal 2 (Streamlit Web UI):
```bash
python run_frontend.py
```
Web dashboard will open automatically at `http://localhost:8501`.

---

## 🔒 Security & Data Integrity Architecture

- **No IEEE 754 Floating-Point Inaccuracies**: All money and ledger transactions use integer minor units or `Numeric(18, 4)` with strict `ROUND_HALF_UP` currency quantizing.
- **Append-Only Ledger**: Balances are calculated through audited ledger entries with database row-level locking.
- **Cross-User Data Isolation**: Foreign-key checks and authenticated JWT token identity enforcement prevent unauthorized access to other users' portfolios.
