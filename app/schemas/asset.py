"""Pydantic schemas for assets and market quotes."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class MarketQuoteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    price: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    nav: Optional[Decimal] = None
    source: str
    is_simulated: bool
    timestamp: datetime


class FinancialDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_name: str
    metric_value: Decimal
    period: str
    source: str
    timestamp: datetime


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    category: str
    currency: str
    metadata: Dict[str, Any] = {}
    is_active: bool
    latest_quote: Optional[MarketQuoteSchema] = None


class AssetFilterParams(BaseModel):
    category: Optional[str] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0
