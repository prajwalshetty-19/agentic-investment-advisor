"""Tests for simulated order placement, double-gate authorization, and execution."""

from decimal import Decimal
import pytest
from app.services.order_service import (
    propose_order, approve_or_reject_order, execute_approved_order, OrderExecutionError
)
from app.db.models import UserSetting, Holding


def test_order_proposal(db_session, test_user, test_asset):
    order = propose_order(
        db=db_session,
        user_id=test_user.id,
        asset_id=test_asset.id,
        side="BUY",
        quantity=Decimal("10.0000"),
        order_type="MARKET"
    )
    assert order.status == "PENDING_APPROVAL"
    assert order.quantity == Decimal("10.0000")
    assert order.price == Decimal("2500.00")
    assert order.total_amount > Decimal("25000.00")  # includes fee


def test_reject_execution_if_account_ai_disabled(db_session, test_user, test_asset):
    # Disable AI execution in account settings
    setting = db_session.query(UserSetting).filter(UserSetting.user_id == test_user.id).first()
    setting.ai_execution_enabled = False
    db_session.commit()

    order = propose_order(
        db=db_session,
        user_id=test_user.id,
        asset_id=test_asset.id,
        side="BUY",
        quantity=Decimal("5.0000")
    )
    approve_or_reject_order(db=db_session, user_id=test_user.id, order_id=order.id, action="APPROVE")

    # Gate 1 check failure
    with pytest.raises(OrderExecutionError) as exc_info:
        execute_approved_order(db=db_session, user_id=test_user.id, order_id=order.id)
    assert "Account-level AI-assisted execution permission is disabled" in str(exc_info.value)


def test_reject_execution_without_explicit_approval(db_session, test_user, test_asset):
    order = propose_order(
        db=db_session,
        user_id=test_user.id,
        asset_id=test_asset.id,
        side="BUY",
        quantity=Decimal("2.0000")
    )
    # Order is still in PENDING_APPROVAL, not APPROVED
    with pytest.raises(OrderExecutionError) as exc_info:
        execute_approved_order(db=db_session, user_id=test_user.id, order_id=order.id)
    assert "Explicit user approval is required" in str(exc_info.value)


def test_successful_buy_and_sell_order_execution(db_session, test_user, test_asset):
    # 1. Propose BUY order for 10 units @ 2,500 = 25,000 + 25 fee = 25,025
    order = propose_order(
        db=db_session,
        user_id=test_user.id,
        asset_id=test_asset.id,
        side="BUY",
        quantity=Decimal("10.0000")
    )
    approve_or_reject_order(db=db_session, user_id=test_user.id, order_id=order.id, action="APPROVE")

    trade, executed_order = execute_approved_order(
        db=db_session,
        user_id=test_user.id,
        order_id=order.id
    )
    assert executed_order.status == "EXECUTED"
    assert trade.executed_quantity == Decimal("10.0000")

    # Wallet balance debited
    assert test_user.wallet.balance == Decimal("100000.00") - executed_order.total_amount

    # Holding created
    holding = db_session.query(Holding).filter(
        Holding.user_id == test_user.id,
        Holding.asset_id == test_asset.id
    ).first()
    assert holding is not None
    assert holding.quantity == Decimal("10.0000")

    # 2. Attempt duplicate execution (Idempotency) -> must fail
    with pytest.raises(OrderExecutionError):
        execute_approved_order(db=db_session, user_id=test_user.id, order_id=order.id)

    # 3. Propose and execute SELL order for 4 units
    sell_order = propose_order(
        db=db_session,
        user_id=test_user.id,
        asset_id=test_asset.id,
        side="SELL",
        quantity=Decimal("4.0000")
    )
    approve_or_reject_order(db=db_session, user_id=test_user.id, order_id=sell_order.id, action="APPROVE")
    sell_trade, executed_sell = execute_approved_order(
        db=db_session,
        user_id=test_user.id,
        order_id=sell_order.id
    )
    assert executed_sell.status == "EXECUTED"

    # Holding reduced to 6 units
    db_session.refresh(holding)
    assert holding.quantity == Decimal("6.0000")
    assert holding.average_buy_price == Decimal("2500.00")
    assert sell_trade.realized_pnl is not None

    # 4. Sell remaining 6 units (Complete position closure)
    sell_all = propose_order(
        db=db_session,
        user_id=test_user.id,
        asset_id=test_asset.id,
        side="SELL",
        quantity=Decimal("6.0000")
    )
    approve_or_reject_order(db=db_session, user_id=test_user.id, order_id=sell_all.id, action="APPROVE")
    final_trade, _ = execute_approved_order(db=db_session, user_id=test_user.id, order_id=sell_all.id)
    db_session.refresh(holding)
    assert holding.quantity == Decimal("0.0000")
    assert holding.total_invested == Decimal("0.0000")


def test_cannot_sell_more_than_held(db_session, test_user, test_asset):
    sell_order = propose_order(
        db=db_session,
        user_id=test_user.id,
        asset_id=test_asset.id,
        side="SELL",
        quantity=Decimal("50.0000")
    )
    approve_or_reject_order(db=db_session, user_id=test_user.id, order_id=sell_order.id, action="APPROVE")

    with pytest.raises(OrderExecutionError) as exc_info:
        execute_approved_order(db=db_session, user_id=test_user.id, order_id=sell_order.id)
    assert "Insufficient holdings to sell" in str(exc_info.value)
