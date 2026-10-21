"""Pydantic schemas for portfolio holdings, performance, and allocation."""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class HoldingDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    holding_id: int
    asset_id: int
    symbol: str
    name: str
    category: str
    quantity: float
    average_buy_price: float
    total_invested: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    weight_percent: float


class PortfolioSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_portfolio_value: float
    total_invested: float
    total_unrealized_pnl: float
    total_unrealized_pnl_percent: float
    virtual_wallet_balance: float
    total_net_worth: float
    asset_allocation: Dict[str, float]  # e.g., {"STOCK": 45.0, "MUTUAL_FUND": 30.0, "GOLD": 25.0}
    holdings: List[HoldingDetail]
