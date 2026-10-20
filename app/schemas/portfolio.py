"""Pydantic schemas for portfolio holdings, performance, and allocation."""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class HoldingDetail(BaseModel):
    holding_id: int
    asset_id: int
    symbol: str
    name: str
    category: str
    quantity: Decimal
    average_buy_price: Decimal
    total_invested: Decimal
    current_price: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    weight_percent: Decimal


class PortfolioSummaryResponse(BaseModel):
    total_portfolio_value: Decimal
    total_invested: Decimal
    total_unrealized_pnl: Decimal
    total_unrealized_pnl_percent: Decimal
    virtual_wallet_balance: Decimal
    total_net_worth: Decimal
    asset_allocation: Dict[str, Decimal]  # e.g., {"STOCK": 45.0, "MUTUAL_FUND": 30.0, "GOLD": 25.0}
    holdings: List[HoldingDetail]
