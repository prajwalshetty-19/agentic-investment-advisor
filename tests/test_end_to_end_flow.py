"""End-to-end integration test demonstrating the full lifecycle:
1. User registration with initial ₹100,000 virtual balance.
2. Discovery & research query executed by multi-agent team.
3. Verification Agent checks arithmetic and grounding.
4. Proposed order generated.
5. Gate 1 check: fails when account execution is disabled.
6. User enables AI execution in account settings.
7. User explicitly approves exact order proposal (Gate 2).
8. Order executes atomically with virtual ledger debit and portfolio position creation.
9. Portfolio and transaction ledger reflect accurate balances.
"""

from decimal import Decimal
import pytest
from app.db.models import User, UserSetting, Asset, MarketQuote, Order, Trade, Holding, WalletLedger
from app.services.wallet_service import get_user_wallet, get_wallet_ledger
from app.services.portfolio_service import get_portfolio_summary


def test_full_investment_lifecycle(db_session, client):
    # 1. Register User
    reg_res = client.post("/api/auth/register", json={
        "username": "e2e_investor",
        "email": "e2e@example.com",
        "password": "SecurePassword#2026",
        "risk_tolerance": "GROWTH"
    })
    assert reg_res.status_code == 201
    auth_data = reg_res.json()
    token = auth_data["access_token"]
    user_id = auth_data["user_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify initial wallet balance is ₹100,000
    wallet_res = client.get("/api/wallet", headers=headers)
    assert wallet_res.status_code == 200
    assert float(wallet_res.json()["balance"]) == 100000.0

    # 2. Seed an asset for discovery
    asset = Asset(
        symbol="GOLDBEES.NS",
        name="Nippon India ETF Gold BeES",
        category="COMMODITY",
        currency="INR",
        metadata_json='{"commodity_type": "GOLD", "cagr_3y": 14.5, "volatility_1y": 12.0}',
        is_active=True
    )
    db_session.add(asset)
    db_session.flush()

    quote = MarketQuote(
        asset_id=asset.id,
        price=Decimal("60.00"),
        source="TEST_FEED",
        is_simulated=True
    )
    db_session.add(quote)
    db_session.commit()

    # 3. User asks Multi-Agent AI Advisor
    chat_res = client.post(
        "/api/agents/chat",
        json={
            "query": "Analyze gold as an investment and suggest the best available options for a ₹20,000 virtual investment over 3 years.",
            "budget": 20000.0,
            "time_horizon_years": 3.0,
            "risk_tolerance": "GROWTH"
        },
        headers=headers
    )
    assert chat_res.status_code == 200
    report_data = chat_res.json()
    assert report_data["verification_passed"] is True
    assert len(report_data["agent_steps"]) >= 8
    assert "report_markdown" in report_data

    # 4. Propose Order based on Discovery
    prop_res = client.post(
        "/api/orders/propose",
        json={
            "asset_id": asset.id,
            "side": "BUY",
            "quantity": 100.0,
            "order_type": "MARKET"
        },
        headers=headers
    )
    assert prop_res.status_code == 200
    order_data = prop_res.json()
    order_id = order_data["order_id"]
    assert order_data["status"] == "PENDING_APPROVAL"
    assert float(order_data["price"]) == 60.0
    total_cost = float(order_data["total_amount"])

    # 5. Gate 1 Test: Attempting execution before enabling account permission must fail
    # Note: AI execution is disabled by default on registration
    appr_res1 = client.post(
        f"/api/orders/{order_id}/approval",
        json={
            "order_id": order_id,
            "action": "APPROVE",
            "approved_quantity": 100.0,
            "approved_price": 60.0,
            "approved_total_amount": total_cost
        },
        headers=headers
    )
    assert appr_res1.status_code == 200

    exec_fail_res = client.post(f"/api/orders/{order_id}/execute", headers=headers)
    assert exec_fail_res.status_code == 400
    assert "Account-level AI-assisted execution permission is disabled" in exec_fail_res.json()["detail"]

    # 6. User enables AI execution in account settings
    settings_res = client.patch(
        "/api/auth/settings",
        json={"ai_execution_enabled": True},
        headers=headers
    )
    assert settings_res.status_code == 200
    assert settings_res.json()["ai_execution_enabled"] is True

    # 7. Execute Approved Order (Gates 1 and 2 pass)
    exec_success_res = client.post(f"/api/orders/{order_id}/execute", headers=headers)
    assert exec_success_res.status_code == 200
    exec_data = exec_success_res.json()
    assert exec_data["success"] is True
    assert exec_data["status"] == "EXECUTED"

    # 8. Verify virtual wallet was debited accurately
    expected_balance = 100000.0 - total_cost
    wallet_after_res = client.get("/api/wallet", headers=headers)
    assert abs(float(wallet_after_res.json()["balance"]) - expected_balance) < 0.01

    # 9. Verify portfolio holdings and valuation
    portfolio_res = client.get("/api/portfolio", headers=headers)
    assert portfolio_res.status_code == 200
    port_data = portfolio_res.json()
    assert len(port_data["holdings"]) == 1
    h = port_data["holdings"][0]
    assert h["symbol"] == "GOLDBEES.NS"
    assert float(h["quantity"]) == 100.0
    assert float(h["current_value"]) == 6000.0

    # 10. Verify audit ledger
    ledger_res = client.get("/api/wallet/ledger", headers=headers)
    assert ledger_res.status_code == 200
    entries = ledger_res.json()
    assert len(entries) >= 2  # INITIAL_CREDIT and BUY_DEBIT
    assert any(e["transaction_type"] == "BUY_DEBIT" for e in entries)
