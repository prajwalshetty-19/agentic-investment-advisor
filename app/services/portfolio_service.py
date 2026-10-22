"""Portfolio Valuation and Holdings Analytics Service.

Aggregates positions from the database, computes current market valuations,
unrealized and realized profit/loss, and portfolio asset allocation weights.
"""

from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Holding, Asset, Wallet, Trade
from app.services.pricing_service import fetch_live_or_simulated_quote
from app.services.wallet_service import get_user_wallet


def get_portfolio_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Computes a comprehensive portfolio summary for the user,
    including individual holdings metrics, totals, and category allocation weights.
    """
    wallet = get_user_wallet(db, user_id)
    holdings = (
        db.query(Holding)
        .filter(Holding.user_id == user_id, Holding.quantity > Decimal("0"))
        .all()
    )

    total_portfolio_value = Decimal("0.0000")
    total_invested = Decimal("0.0000")
    holding_details = []
    category_totals: Dict[str, Decimal] = {}

    for h in holdings:
        asset = db.query(Asset).filter(Asset.id == h.asset_id).first()
        if not asset:
            continue

        quote = fetch_live_or_simulated_quote(db, asset)
        current_price = quote.price
        current_value = h.quantity * current_price
        unrealized_pnl = current_value - h.total_invested
        pnl_pct = (
            (unrealized_pnl / h.total_invested) * Decimal("100.0")
            if h.total_invested > Decimal("0")
            else Decimal("0.0")
        )

        total_portfolio_value += current_value
        total_invested += h.total_invested

        cat = asset.category.upper()
        category_totals[cat] = category_totals.get(cat, Decimal("0.0000")) + current_value

        holding_details.append({
            "holding_id": h.id,
            "asset_id": asset.id,
            "symbol": asset.symbol,
            "name": asset.name,
            "category": asset.category,
            "quantity": round(h.quantity, 4),
            "average_buy_price": round(h.average_buy_price, 2),
            "total_invested": round(h.total_invested, 2),
            "current_price": round(current_price, 2),
            "current_value": round(current_value, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pnl_percent": round(pnl_pct, 2),
            "weight_percent": Decimal("0.0")  # Updated below
        })

    # Calculate portfolio weights
    for item in holding_details:
        if total_portfolio_value > Decimal("0"):
            item["weight_percent"] = round((item["current_value"] / total_portfolio_value) * Decimal("100.0"), 2)

    # Calculate asset allocation percentages
    asset_allocation: Dict[str, Decimal] = {}
    if total_portfolio_value > Decimal("0"):
        for cat, cat_val in category_totals.items():
            asset_allocation[cat] = round((cat_val / total_portfolio_value) * Decimal("100.0"), 2)

    total_unrealized_pnl = total_portfolio_value - total_invested
    total_pnl_pct = (
        (total_unrealized_pnl / total_invested) * Decimal("100.0")
        if total_invested > Decimal("0")
        else Decimal("0.0")
    )
    total_net_worth = total_portfolio_value + wallet.balance

    # Calculate cumulative realized profit/loss across user's trades
    realized_query = (
        db.query(func.coalesce(func.sum(Trade.realized_pnl), Decimal("0.0000")))
        .filter(Trade.user_id == user_id)
        .scalar()
    )
    total_realized_pnl = Decimal(str(realized_query or "0.0000"))

    return {
        "total_portfolio_value": round(total_portfolio_value, 2),
        "total_invested": round(total_invested, 2),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
        "total_unrealized_pnl_percent": round(total_pnl_pct, 2),
        "total_realized_pnl": round(total_realized_pnl, 2),
        "virtual_wallet_balance": round(wallet.balance, 2),
        "available_balance": round(wallet.balance, 2),
        "total_net_worth": round(total_net_worth, 2),
        "asset_allocation": asset_allocation,
        "holdings": holding_details
    }
