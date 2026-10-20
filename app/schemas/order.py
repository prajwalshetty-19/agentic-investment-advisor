"""Pydantic schemas for order proposals, user approvals, and trade execution."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class OrderProposalRequest(BaseModel):
    asset_id: int
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: Decimal = Field(..., gt=0)
    order_type: str = Field("MARKET", pattern="^(MARKET|LIMIT)$")
    limit_price: Optional[Decimal] = Field(None, gt=0)


class OrderProposalResponse(BaseModel):
    order_id: int
    asset_id: int
    asset_symbol: str
    asset_name: str
    asset_category: str
    side: str
    quantity: Decimal
    price: Decimal
    total_amount: Decimal
    estimated_fee: Decimal
    current_wallet_balance: Decimal
    expected_balance_after: Decimal
    status: str
    idempotency_key: str
    simulation_notes: str
    requires_approval: bool = True


class OrderApprovalRequest(BaseModel):
    order_id: int
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    approved_quantity: Decimal
    approved_price: Decimal
    approved_total_amount: Decimal


class OrderExecutionResult(BaseModel):
    success: bool
    order_id: int
    trade_id: Optional[int] = None
    status: str
    message: str
    executed_quantity: Optional[Decimal] = None
    executed_price: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    fee: Optional[Decimal] = None
    remaining_wallet_balance: Decimal
    timestamp: datetime
