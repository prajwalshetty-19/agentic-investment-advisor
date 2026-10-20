"""Pydantic schemas for virtual wallet and ledger transactions."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    balance: Decimal
    currency: str
    updated_at: datetime


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wallet_id: int
    order_id: Optional[int] = None
    transaction_type: str
    amount: Decimal
    balance_after: Decimal
    description: str
    created_at: datetime


class VirtualDepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, le=1000000, description="Amount of virtual funds to add")
    description: Optional[str] = "Virtual Wallet Deposit"
