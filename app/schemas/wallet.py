"""Pydantic schemas for virtual wallet and ledger transactions."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    balance: float
    currency: str
    updated_at: datetime


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wallet_id: int
    order_id: Optional[int] = None
    transaction_type: str
    amount: float
    balance_after: float
    description: str
    created_at: datetime


class VirtualDepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, le=10000000, description="Amount of simulated funds to deposit")
    payment_method: str = Field(default="UPI (Simulation)", description="Simulated funding method")
    upi_id: Optional[str] = Field(default=None, description="Simulated UPI Virtual Payment Address (e.g. user@okhdfcbank)")
    idempotency_key: Optional[str] = Field(default=None, description="Client idempotency key to prevent double deposits")
    description: Optional[str] = Field(default=None, description="Optional custom deposit description")
