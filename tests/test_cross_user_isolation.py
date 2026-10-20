"""Tests for cross-user data isolation and authorization security."""

from decimal import Decimal
import pytest
from app.db.models import User, UserSetting, Order
from app.core.security import get_password_hash, create_access_token
from app.services.wallet_service import initialize_user_wallet
from app.services.order_service import propose_order


def test_cross_user_isolation(db_session, client, test_user, test_asset):
    # Create User B
    user_b = User(
        username="user_bob",
        email="bob@example.com",
        hashed_password=get_password_hash("password123")
    )
    db_session.add(user_b)
    db_session.flush()

    setting_b = UserSetting(user_id=user_b.id, ai_execution_enabled=True)
    db_session.add(setting_b)
    initialize_user_wallet(db_session, user_b.id, initial_balance=Decimal("50000.00"))
    db_session.commit()

    # User B creates an order
    order_b = propose_order(
        db=db_session,
        user_id=user_b.id,
        asset_id=test_asset.id,
        side="BUY",
        quantity=Decimal("1.0000")
    )

    # User A tries to approve or execute User B's order
    token_a = create_access_token({"sub": str(test_user.id), "username": test_user.username})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    res = client.post(
        f"/api/orders/{order_b.id}/approval",
        json={
            "order_id": order_b.id,
            "action": "APPROVE",
            "approved_quantity": 1.0,
            "approved_price": float(order_b.price),
            "approved_total_amount": float(order_b.total_amount)
        },
        headers=headers_a
    )
    # Must be 404 Not Found (or 403 Forbidden)
    assert res.status_code in (404, 403)
