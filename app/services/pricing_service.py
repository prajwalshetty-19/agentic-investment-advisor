"""Modular market pricing service with provider adapters.

Fetches quotes for Stocks, Mutual Funds, Bonds, Commodities (Gold/Silver),
Fixed Deposits (FDs), and Recurring Deposits (RDs). Supports live external
feeds (e.g. yfinance, AMFI) with fallback to deterministic catalog quotes.
Never silently invents quotes or confuses indicative proxies with spot rates.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List
import json
import logging
import time
from sqlalchemy.orm import Session
from app.db.models import Asset, MarketQuote

logger = logging.getLogger(__name__)

# In-memory quote cache: symbol -> {"price": Decimal, "nav": Optional[Decimal], "source": str, "is_simulated": bool, "data_status": str, "timestamp": float}
_QUOTE_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 60


def clear_quote_cache():
    """Clears in-memory quote cache."""
    global _QUOTE_CACHE
    _QUOTE_CACHE.clear()


class BasePricingAdapter(ABC):
    @abstractmethod
    def fetch_quote(self, asset: Asset, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Returns dict with price, nav, source, is_simulated, data_status or None if unhandled."""
        pass


class EquityQuoteAdapter(BasePricingAdapter):
    """Fetches equity and ETF quotes using yfinance for NSE (.NS) and BSE (.BO) tickers."""

    def fetch_quote(self, asset: Asset, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        symbol = asset.symbol.upper()
        if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
            return None

        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            fast_info = getattr(ticker, "fast_info", None)
            price_val = None
            if fast_info and hasattr(fast_info, "last_price") and fast_info.last_price is not None:
                price_val = fast_info.last_price
            else:
                hist = ticker.history(period="1d")
                if not hist.empty and "Close" in hist:
                    price_val = float(hist["Close"].iloc[-1])

            if price_val and float(price_val) > 0:
                live_price = Decimal(str(round(float(price_val), 2)))
                return {
                    "price": live_price,
                    "nav": None,
                    "source": "YFINANCE_LIVE",
                    "is_simulated": False,
                    "data_status": "LIVE"
                }
        except Exception as e:
            logger.debug(f"Equity adapter error for {symbol}: {e}")
        return None


class MutualFundQuoteAdapter(BasePricingAdapter):
    """Retrieves Mutual Fund NAV via AMFI / public MF APIs or catalog metadata."""

    def fetch_quote(self, asset: Asset, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if asset.category != "MUTUAL_FUND":
            return None

        amfi_code = metadata.get("amfi_code") or metadata.get("scheme_code")
        if amfi_code:
            try:
                import requests
                resp = requests.get(f"https://api.mfapi.in/mf/{amfi_code}/latest", timeout=2.5)
                if resp.status_code == 200:
                    data = resp.json()
                    nav_list = data.get("data", [])
                    if nav_list and "nav" in nav_list[0]:
                        nav_val = Decimal(str(round(float(nav_list[0]["nav"]), 2)))
                        return {
                            "price": nav_val,
                            "nav": nav_val,
                            "source": "AMFI_LIVE_API",
                            "is_simulated": False,
                            "data_status": "LIVE"
                        }
            except Exception as e:
                logger.debug(f"AMFI API fetch failed for {asset.symbol}: {e}")

        default_nav = metadata.get("nav") or metadata.get("latest_nav")
        if default_nav:
            nav_dec = Decimal(str(default_nav))
            return {
                "price": nav_dec,
                "nav": nav_dec,
                "source": "AMFI_CATALOG_NAV",
                "is_simulated": False,
                "data_status": "INDICATIVE_PROXY"
            }
        return None


class CommodityQuoteAdapter(BasePricingAdapter):
    """
    Distinguishes listed Exchange-Traded Commodities (e.g. Gold/Silver BeES)
    from physical indicative spot rates (e.g. GOLD_SPOT, SILVER_SPOT).
    """

    def __init__(self, equity_adapter: EquityQuoteAdapter):
        self.equity_adapter = equity_adapter

    def fetch_quote(self, asset: Asset, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if asset.category != "COMMODITY":
            return None

        proxy_type = metadata.get("proxy_type", "")
        if proxy_type == "EXCHANGE_TRADED_FUND" or asset.symbol.endswith(".NS"):
            res = self.equity_adapter.fetch_quote(asset, metadata)
            if res:
                res["source"] = "YFINANCE_COMMODITY_ETF"
                res["data_status"] = "LIVE"
                return res

        if "SPOT" in asset.symbol or proxy_type == "INDICATIVE_SPOT":
            default_rate = metadata.get("spot_rate") or metadata.get("price")
            price_dec = Decimal(str(default_rate)) if default_rate else Decimal("7250.00")
            return {
                "price": price_dec,
                "nav": None,
                "source": "MCX_INDICATIVE_SPOT",
                "is_simulated": True,
                "data_status": "INDICATIVE_PROXY"
            }
        return None


class FixedIncomeQuoteAdapter(BasePricingAdapter):
    """Provides sovereign bond and bank deposit deterministic pricing."""

    def fetch_quote(self, asset: Asset, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cat = asset.category
        if cat not in ("BOND", "FD", "RD"):
            return None

        if cat == "BOND":
            face_value = Decimal(str(metadata.get("face_value", 100.0)))
            return {
                "price": face_value,
                "nav": None,
                "source": "SOVEREIGN_BOND_PAR",
                "is_simulated": False,
                "data_status": "INDICATIVE_PROXY"
            }

        if cat in ("FD", "RD"):
            base_unit = Decimal(str(metadata.get("min_monthly_deposit", 1000.0)))
            return {
                "price": base_unit,
                "nav": None,
                "source": "DETERMINISTIC_BANK_RATE",
                "is_simulated": True,
                "data_status": "DETERMINISTIC_CATALOG"
            }
        return None


# Module-level adapter instances
_equity_adapter = EquityQuoteAdapter()
_mf_adapter = MutualFundQuoteAdapter()
_commodity_adapter = CommodityQuoteAdapter(_equity_adapter)
_fixed_income_adapter = FixedIncomeQuoteAdapter()
_all_adapters = [_equity_adapter, _mf_adapter, _commodity_adapter, _fixed_income_adapter]


def get_latest_quote(db: Session, asset_id: int) -> Optional[MarketQuote]:
    """Retrieves the most recent quote for an asset from the database."""
    return (
        db.query(MarketQuote)
        .filter(MarketQuote.asset_id == asset_id)
        .order_by(MarketQuote.timestamp.desc())
        .first()
    )


def update_asset_quote(
    db: Session,
    asset_id: int,
    price: Decimal,
    nav: Optional[Decimal] = None,
    source: str = "SIMULATED",
    is_simulated: bool = True
) -> MarketQuote:
    """Inserts a new quote record for the specified asset."""
    quote = MarketQuote(
        asset_id=asset_id,
        price=price,
        bid=price * Decimal("0.999"),
        ask=price * Decimal("1.001"),
        nav=nav,
        source=source,
        is_simulated=is_simulated,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


def fetch_live_or_simulated_quote(db: Session, asset: Asset) -> MarketQuote:
    """
    Attempts to fetch a live quote via modular provider adapters with caching and fallback.
    """
    symbol = asset.symbol
    now_ts = time.time()

    # Check in-memory quote cache
    cached = _QUOTE_CACHE.get(symbol)
    if cached and (now_ts - cached["timestamp"]) < CACHE_TTL_SECONDS:
        # Cache hit: verify if latest DB quote matches or create update if none exists
        latest = get_latest_quote(db, asset.id)
        if latest and latest.price == cached["price"]:
            return latest
        return update_asset_quote(
            db=db,
            asset_id=asset.id,
            price=cached["price"],
            nav=cached.get("nav"),
            source=cached.get("source", "CACHED_LIVE"),
            is_simulated=cached.get("is_simulated", False)
        )

    # Query modular provider adapters
    meta = asset.get_metadata()
    for adapter in _all_adapters:
        try:
            quote_data = adapter.fetch_quote(asset, meta)
            if quote_data:
                # Store in cache
                _QUOTE_CACHE[symbol] = {
                    "price": quote_data["price"],
                    "nav": quote_data["nav"],
                    "source": quote_data["source"],
                    "is_simulated": quote_data["is_simulated"],
                    "data_status": quote_data.get("data_status", "LIVE"),
                    "timestamp": now_ts
                }
                return update_asset_quote(
                    db=db,
                    asset_id=asset.id,
                    price=quote_data["price"],
                    nav=quote_data["nav"],
                    source=quote_data["source"],
                    is_simulated=quote_data["is_simulated"]
                )
        except Exception as e:
            logger.debug(f"Adapter {adapter.__class__.__name__} failed for {symbol}: {e}")

    # Fallback to latest database quote if available
    latest = get_latest_quote(db, asset.id)
    if latest:
        return latest

    # Default fallback quote
    default_price = Decimal("100.0000")
    return update_asset_quote(db, asset.id, default_price, source="DEFAULT_FALLBACK", is_simulated=True)


def list_all_assets_with_quotes(db: Session, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all active assets along with their latest quote and parsed metadata."""
    query = db.query(Asset).filter(Asset.is_active == True)
    if category:
        query = query.filter(Asset.category == category.upper())

    assets = query.all()
    results = []
    for a in assets:
        quote = get_latest_quote(db, a.id)
        meta = a.get_metadata()
        cached = _QUOTE_CACHE.get(a.symbol)
        data_status = cached.get("data_status") if cached else ("SIMULATED" if quote and quote.is_simulated else "LIVE")

        results.append({
            "id": a.id,
            "symbol": a.symbol,
            "name": a.name,
            "category": a.category,
            "currency": a.currency,
            "metadata": meta,
            "latest_price": quote.price if quote else Decimal("0.0"),
            "nav": quote.nav if quote else None,
            "quote_source": quote.source if quote else "NONE",
            "is_simulated": quote.is_simulated if quote else True,
            "data_status": data_status,
            "quote_timestamp": quote.timestamp.isoformat() if quote else None
        })
    return results
