"""Multi-Asset Catalog and Market Quote API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Asset
from app.services.pricing_service import list_all_assets_with_quotes, fetch_live_or_simulated_quote, get_latest_quote

router = APIRouter(prefix="/api/assets", tags=["Asset Catalog"])


@router.get("", response_model=List[Dict[str, Any]])
def get_assets(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieves the asset catalog with latest quotes, metadata, and data-source indicators.
    Filters by category (STOCK, MUTUAL_FUND, BOND, COMMODITY, FD, RD) or search term.
    """
    items = list_all_assets_with_quotes(db, category=category)
    if search:
        search_lower = search.lower()
        items = [
            it for it in items
            if search_lower in it["symbol"].lower() or search_lower in it["name"].lower()
        ]
    return items


@router.get("/{asset_id}", response_model=Dict[str, Any])
def get_asset_detail(asset_id: int, db: Session = Depends(get_db)):
    """Retrieves detailed information for a single asset, including historical metrics."""
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.is_active == True).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    quote = fetch_live_or_simulated_quote(db, asset)
    return {
        "id": asset.id,
        "symbol": asset.symbol,
        "name": asset.name,
        "category": asset.category,
        "currency": asset.currency,
        "metadata": asset.get_metadata(),
        "latest_price": quote.price,
        "nav": quote.nav,
        "quote_source": quote.source,
        "is_simulated": quote.is_simulated,
        "quote_timestamp": quote.timestamp.isoformat()
    }
