"""End-to-end integration test demonstrating the full lifecycle:
1. User registration with initial ₹0 default balance.
2. Simulated deposit via UPI (Simulation).
3. Discovery & research query executed by multi-agent team.
4. Verification Agent checks arithmetic and grounding.
5. Proposed BUY order generated.
6. Gate 1 check: fails when account execution is disabled.
7. User enables AI execution in account settings.
8. User explicitly approves exact order proposal (Gate 2).
9. Order executes atomically with ledger debit and portfolio holding creation.
10. User sells part of holding (Partial Sell).
11. Portfolio, realized P&L, and transaction ledger reflect accurate balances.
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

    # Verify initial balance is strictly ₹0.00
    wallet_res = client.get("/api/wallet", headers=headers)
    assert wallet_res.status_code == 200
    assert float(wallet_res.json()["balance"]) == 0.0

    # 2. Deposit simulated funds via UPI (Simulation)
    dep_res = client.post(
        "/api/wallet/deposit",
        json={
            "amount": 50000.0,
            "payment_method": "UPI (Simulation)",
            "upi_id": "e2e_investor@okhdfcbank"
        },
        headers=headers
    )
    assert dep_res.status_code == 200
    assert float(dep_res.json()["balance"]) == 50000.0

    # 3. Seed an asset for discovery
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

    # 4. User asks Multi-Agent AI Advisor
    chat_res = client.post(
        "/api/agents/chat",
        json={
            "query": "Analyze gold as an investment and suggest the best available options for a ₹20,000 investment over 3 years.",
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
    assert "Disclaimer" in report_data["report_markdown"]

    # 5. Propose Order based on Discovery
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
    fill_price = float(order_data["price"])
    assert fill_price > 0.0
    total_cost = float(order_data["total_amount"])

    # 6. Gate 1 Test: Attempting execution before enabling account permission must fail
    appr_res1 = client.post(
        f"/api/orders/{order_id}/approval",
        json={
            "order_id": order_id,
            "action": "APPROVE",
            "approved_quantity": 100.0,
            "approved_price": fill_price,
            "approved_total_amount": total_cost
        },
        headers=headers
    )
    assert appr_res1.status_code == 200

    exec_fail_res = client.post(f"/api/orders/{order_id}/execute", headers=headers)
    assert exec_fail_res.status_code == 400
    assert "Account-level AI-assisted execution permission is disabled" in exec_fail_res.json()["detail"]

    # 7. User enables AI execution in account settings
    settings_res = client.patch(
        "/api/auth/settings",
        json={"ai_execution_enabled": True},
        headers=headers
    )
    assert settings_res.status_code == 200
    assert settings_res.json()["ai_execution_enabled"] is True

    # 8. Execute Approved Order (Gates 1 and 2 pass)
    exec_success_res = client.post(f"/api/orders/{order_id}/execute", headers=headers)
    assert exec_success_res.status_code == 200
    exec_data = exec_success_res.json()
    assert exec_data["success"] is True
    assert exec_data["status"] == "EXECUTED"

    # 9. Verify wallet was debited accurately
    expected_balance = 50000.0 - total_cost
    wallet_after_res = client.get("/api/wallet", headers=headers)
    assert abs(float(wallet_after_res.json()["balance"]) - expected_balance) < 0.01

    # 10. Verify portfolio holdings and valuation
    portfolio_res = client.get("/api/portfolio", headers=headers)
    assert portfolio_res.status_code == 200
    port_data = portfolio_res.json()
    assert len(port_data["holdings"]) == 1
    h = port_data["holdings"][0]
    assert h["symbol"] == "GOLDBEES.NS"
    assert float(h["quantity"]) == 100.0
    assert abs(float(h["current_value"]) - round(100.0 * fill_price, 2)) < 0.05

    # 11. Partial Sale: User sells 40 units of held position
    sell_prop = client.post(
        "/api/orders/propose",
        json={
            "asset_id": asset.id,
            "side": "SELL",
            "quantity": 40.0,
            "order_type": "MARKET"
        },
        headers=headers
    )
    assert sell_prop.status_code == 200
    sell_data = sell_prop.json()
    sell_id = sell_data["order_id"]

    # Approve SELL (Gate 2)
    client.post(
        f"/api/orders/{sell_id}/approval",
        json={
            "order_id": sell_id,
            "action": "APPROVE",
            "approved_quantity": 40.0,
            "approved_price": float(sell_data["price"]),
            "approved_total_amount": float(sell_data["total_amount"])
        },
        headers=headers
    )

    # Execute SELL
    exec_sell_res = client.post(f"/api/orders/{sell_id}/execute", headers=headers)
    assert exec_sell_res.status_code == 200
    assert exec_sell_res.json()["status"] == "EXECUTED"

    # 12. Verify holding reduced to 60 units and portfolio reports realized P&L
    port_after_sell = client.get("/api/portfolio", headers=headers).json()
    assert len(port_after_sell["holdings"]) == 1
    assert float(port_after_sell["holdings"][0]["quantity"]) == 60.0
    assert "total_realized_pnl" in port_after_sell

    # 13. Verify audit ledger includes deposit, buy, and sell transactions
    ledger_res = client.get("/api/wallet/ledger", headers=headers)
    assert ledger_res.status_code == 200
    entries = ledger_res.json()
    assert len(entries) >= 3
    tx_types = [e["transaction_type"] for e in entries]
    assert "DEPOSIT_CREDIT" in tx_types
    assert "BUY_DEBIT" in tx_types
    assert "SELL_CREDIT" in tx_types
