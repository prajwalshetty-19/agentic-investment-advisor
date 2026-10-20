"""Simulated Order Placement, Approval, and Execution API endpoints."""

from decimal import Decimal
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Order, Asset
from app.core.dependencies import get_current_user, get_client_ip
from app.services.order_service import (
    propose_order, approve_or_reject_order, execute_approved_order, OrderExecutionError
)
from app.services.wallet_service import get_user_wallet
from app.schemas.order import (
    OrderProposalRequest, OrderProposalResponse, OrderApprovalRequest, OrderExecutionResult
)

router = APIRouter(prefix="/api/orders", tags=["Orders & Simulated Trading"])


@router.post("/propose", response_model=OrderProposalResponse)
def create_order_proposal(
    req: OrderProposalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a proposed virtual order card in PENDING_APPROVAL status.
    Calculates estimated price, fee, and wallet impact.
    """
    order = propose_order(
        db=db,
        user_id=current_user.id,
        asset_id=req.asset_id,
        side=req.side,
        quantity=req.quantity,
        order_type=req.order_type,
        limit_price=req.limit_price
    )
    wallet = get_user_wallet(db, current_user.id)
    asset = db.query(Asset).filter(Asset.id == req.asset_id).first()

    expected_balance = (
        wallet.balance - order.total_amount
        if order.side == "BUY"
        else wallet.balance + order.total_amount
    )

    return OrderProposalResponse(
        order_id=order.id,
        asset_id=asset.id,
        asset_symbol=asset.symbol,
        asset_name=asset.name,
        asset_category=asset.category,
        side=order.side,
        quantity=order.quantity,
        price=order.price,
        total_amount=order.total_amount,
        estimated_fee=order.estimated_fee,
        current_wallet_balance=wallet.balance,
        expected_balance_after=expected_balance,
        status=order.status,
        idempotency_key=order.idempotency_key,
        simulation_notes=f"Simulated {order.side} execution. Real funds are never used.",
        requires_approval=True
    )


@router.post("/{order_id}/approval")
def handle_order_approval(
    order_id: int,
    req: OrderApprovalRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits user's explicit authorization (APPROVE or REJECT) for a proposed order.
    Re-verifies that quantity, price, and total amount were not altered.
    """
    ip = get_client_ip(request)
    try:
        order, approval = approve_or_reject_order(
            db=db,
            user_id=current_user.id,
            order_id=order_id,
            action=req.action,
            approved_quantity=req.approved_quantity,
            approved_price=req.approved_price,
            approved_total_amount=req.approved_total_amount,
            ip_address=ip
        )
        return {
            "success": True,
            "order_id": order.id,
            "status": order.status,
            "decision": approval.approval_status,
            "approved_at": approval.approved_at.isoformat()
        }
    except OrderExecutionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{order_id}/execute", response_model=OrderExecutionResult)
def execute_order_endpoint(
    order_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes an approved virtual order in the internal simulation engine.
    Enforces account AI-execution permission (Gate 1) and explicit order approval (Gate 2).
    """
    ip = get_client_ip(request)
    try:
        trade, order = execute_approved_order(
            db=db,
            user_id=current_user.id,
            order_id=order_id,
            ip_address=ip
        )
        wallet = get_user_wallet(db, current_user.id)
        return OrderExecutionResult(
            success=True,
            order_id=order.id,
            trade_id=trade.id,
            status=order.status,
            message="Simulated order executed successfully.",
            executed_quantity=trade.executed_quantity,
            executed_price=trade.executed_price,
            total_cost=order.total_amount,
            fee=trade.fee,
            remaining_wallet_balance=wallet.balance,
            timestamp=trade.executed_at
        )
    except OrderExecutionError as e:
        wallet = get_user_wallet(db, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[Dict[str, Any]])
def list_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists orders belonging to the authenticated user."""
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .limit(100)
        .all()
    )
    result = []
    for o in orders:
        asset = db.query(Asset).filter(Asset.id == o.asset_id).first()
        result.append({
            "id": o.id,
            "asset_id": o.asset_id,
            "symbol": asset.symbol if asset else "UNKNOWN",
            "name": asset.name if asset else "UNKNOWN",
            "side": o.side,
            "order_type": o.order_type,
            "quantity": o.quantity,
            "price": o.price,
            "total_amount": o.total_amount,
            "estimated_fee": o.estimated_fee,
            "status": o.status,
            "idempotency_key": o.idempotency_key,
            "created_at": o.created_at.isoformat()
        })
    return result
