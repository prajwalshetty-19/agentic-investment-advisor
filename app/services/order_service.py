"""Simulated Paper-Trading and Order Execution Engine.

Enforces strict double-gate authorization, atomic portfolio updates,
non-negative virtual balances, and idempotent order execution.
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import Order, OrderApproval, Trade, Holding, Asset, User, UserSetting
from app.services.wallet_service import debit_wallet, credit_wallet, get_user_wallet, InsufficientFundsError
from app.services.pricing_service import get_latest_quote, fetch_live_or_simulated_quote
from app.core.audit import record_audit_log


class OrderExecutionError(Exception):
    """Raised when an order fails business rule validation during execution."""
    pass


def propose_order(
    db: Session,
    user_id: int,
    asset_id: int,
    side: str,
    quantity: Decimal,
    order_type: str = "MARKET",
    limit_price: Optional[Decimal] = None
) -> Order:
    """
    Creates a proposed virtual order in PENDING_APPROVAL status.
    Calculates estimated price, total amount, fees, and checks wallet impact.
    """
    side = side.upper()
    if side not in ("BUY", "SELL"):
        raise ValueError("Order side must be BUY or SELL")

    if quantity <= Decimal("0"):
        raise ValueError("Order quantity must be strictly positive")

    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.is_active == True).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found or inactive")

    quote = fetch_live_or_simulated_quote(db, asset)
    execution_price = limit_price if (order_type == "LIMIT" and limit_price) else quote.price

    # 0.1% virtual brokerage fee (minimum ₹5)
    raw_fee = execution_price * quantity * Decimal("0.001")
    fee = max(raw_fee, Decimal("5.0000")) if execution_price * quantity > 0 else Decimal("0.0000")
    total_amount = (execution_price * quantity) + (fee if side == "BUY" else -fee)

    idempotency_key = f"ORD-{user_id}-{asset_id}-{uuid.uuid4().hex[:12].upper()}"

    order = Order(
        user_id=user_id,
        asset_id=asset_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=execution_price,
        total_amount=total_amount,
        estimated_fee=fee,
        status="PENDING_APPROVAL",
        idempotency_key=idempotency_key
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    record_audit_log(
        db=db,
        user_id=user_id,
        action="PROPOSE_ORDER",
        entity_type="ORDER",
        entity_id=order.id,
        details={
            "symbol": asset.symbol,
            "side": side,
            "quantity": str(quantity),
            "price": str(execution_price),
            "total_amount": str(total_amount)
        }
    )
    return order


def approve_or_reject_order(
    db: Session,
    user_id: int,
    order_id: int,
    action: str,  # APPROVE or REJECT
    approved_quantity: Optional[Decimal] = None,
    approved_price: Optional[Decimal] = None,
    approved_total_amount: Optional[Decimal] = None,
    ip_address: Optional[str] = None
) -> Tuple[Order, OrderApproval]:
    """
    Records the user's explicit order authorization decision.
    Validates that the approved values strictly match the proposed order parameters.
    """
    action = action.upper()
    if action not in ("APPROVE", "REJECT"):
        raise ValueError("Action must be APPROVE or REJECT")

    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or access denied")

    if order.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be modified. Current status is {order.status}"
        )

    # If approving, verify that proposed details were not altered
    if action == "APPROVE":
        if approved_quantity is not None and approved_quantity != order.quantity:
            order.status = "REJECTED"
            db.commit()
            raise OrderExecutionError("Approval rejected: Quantity does not match proposed order.")
        if approved_price is not None and approved_price != order.price:
            order.status = "REJECTED"
            db.commit()
            raise OrderExecutionError("Approval rejected: Price does not match proposed order.")
        if approved_total_amount is not None and approved_total_amount != order.total_amount:
            order.status = "REJECTED"
            db.commit()
            raise OrderExecutionError("Approval rejected: Total amount does not match proposed order.")

    approval = OrderApproval(
        order_id=order.id,
        user_id=user_id,
        approved_quantity=approved_quantity or order.quantity,
        approved_price=approved_price or order.price,
        approved_total_amount=approved_total_amount or order.total_amount,
        approval_status="APPROVED" if action == "APPROVE" else "REJECTED",
        approved_at=datetime.now(timezone.utc),
        ip_address=ip_address
    )
    db.add(approval)
    order.status = "APPROVED" if action == "APPROVE" else "REJECTED"
    db.commit()
    db.refresh(order)
    db.refresh(approval)

    record_audit_log(
        db=db,
        user_id=user_id,
        action=f"ORDER_{action}",
        entity_type="ORDER_APPROVAL",
        entity_id=approval.id,
        details={"order_id": order.id, "action": action},
        ip_address=ip_address
    )
    return order, approval


def execute_approved_order(
    db: Session,
    user_id: int,
    order_id: int,
    ip_address: Optional[str] = None
) -> Tuple[Trade, Order]:
    """
    Executes an approved simulated order inside an atomic transaction.
    Enforces Gate 1 (Account permission) and Gate 2 (Explicit order approval).
    """
    # 1. Gate 1: Check account-level AI execution setting
    user_setting = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    if not user_setting or not user_setting.ai_execution_enabled:
        raise OrderExecutionError(
            "Account-level AI-assisted execution permission is disabled. Please enable it in Settings before executing orders."
        )

    # 2. Retrieve order with row-level lock
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status == "EXECUTED":
        raise OrderExecutionError(f"Order #{order_id} has already been executed (Idempotency violation).")

    if order.status != "APPROVED":
        raise OrderExecutionError(
            f"Gate 2 Check Failed: Order is in status '{order.status}'. Explicit user approval is required."
        )

    # 3. Verify approval record exists and is APPROVED
    approval = db.query(OrderApproval).filter(OrderApproval.order_id == order.id).first()
    if not approval or approval.approval_status != "APPROVED":
        raise OrderExecutionError("Gate 2 Check Failed: No valid approval record found for this order.")

    asset = db.query(Asset).filter(Asset.id == order.asset_id).first()
    if not asset:
        raise OrderExecutionError("Asset for this order no longer exists.")

    try:
        if order.side == "BUY":
            # Check wallet balance and debit
            debit_wallet(
                db=db,
                user_id=user_id,
                amount=order.total_amount,
                transaction_type="BUY_DEBIT",
                description=f"Simulated BUY {order.quantity} of {asset.symbol} @ ₹{order.price:,.2f}",
                order_id=order.id
            )

            # Update or create holding
            holding = db.query(Holding).filter(
                Holding.user_id == user_id,
                Holding.asset_id == order.asset_id
            ).first()

            if holding:
                new_quantity = holding.quantity + order.quantity
                new_invested = holding.total_invested + (order.price * order.quantity)
                holding.average_buy_price = new_invested / new_quantity
                holding.quantity = new_quantity
                holding.total_invested = new_invested
            else:
                holding = Holding(
                    user_id=user_id,
                    asset_id=order.asset_id,
                    quantity=order.quantity,
                    average_buy_price=order.price,
                    total_invested=order.price * order.quantity
                )
                db.add(holding)

        elif order.side == "SELL":
            # Verify user holds enough quantity
            holding = db.query(Holding).filter(
                Holding.user_id == user_id,
                Holding.asset_id == order.asset_id
            ).first()

            if not holding or holding.quantity < order.quantity:
                available = holding.quantity if holding else Decimal("0")
                raise OrderExecutionError(
                    f"Insufficient holdings to sell {order.quantity} {asset.symbol}. Available: {available}"
                )

            # Calculate realized profit/loss
            cost_basis = holding.average_buy_price * order.quantity
            sale_gross = order.price * order.quantity
            realized_pnl = sale_gross - cost_basis - order.estimated_fee

            # Credit wallet with sale proceeds minus fee
            credit_wallet(
                db=db,
                user_id=user_id,
                amount=order.total_amount,
                transaction_type="SELL_CREDIT",
                description=f"Simulated SELL {order.quantity} of {asset.symbol} @ ₹{order.price:,.2f}",
                order_id=order.id
            )

            # Update holding
            new_quantity = holding.quantity - order.quantity
            if new_quantity == Decimal("0"):
                holding.quantity = Decimal("0")
                holding.average_buy_price = Decimal("0")
                holding.total_invested = Decimal("0")
            else:
                cost_of_sold = holding.average_buy_price * order.quantity
                holding.total_invested = max(Decimal("0"), holding.total_invested - cost_of_sold)
                holding.quantity = new_quantity

        # Create trade record
        trade = Trade(
            order_id=order.id,
            user_id=user_id,
            asset_id=order.asset_id,
            executed_quantity=order.quantity,
            executed_price=order.price,
            fee=order.estimated_fee,
            realized_pnl=realized_pnl if order.side == "SELL" else Decimal("0.0000"),
            executed_at=datetime.now(timezone.utc)
        )
        db.add(trade)

        order.status = "EXECUTED"
        db.commit()
        db.refresh(trade)
        db.refresh(order)

        record_audit_log(
            db=db,
            user_id=user_id,
            action="EXECUTE_ORDER",
            entity_type="TRADE",
            entity_id=trade.id,
            details={
                "order_id": order.id,
                "asset_symbol": asset.symbol,
                "executed_qty": str(order.quantity),
                "executed_price": str(order.price)
            },
            ip_address=ip_address
        )
        return trade, order

    except Exception as e:
        db.rollback()
        order.status = "FAILED"
        db.commit()
        raise e
