"""Tests for modular pricing service and fallback market quote generation."""

from decimal import Decimal
import pytest
from app.db.models import Asset, MarketQuote
from app.services.pricing_service import (
    get_latest_quote, update_asset_quote, fetch_live_or_simulated_quote, list_all_assets_with_quotes
)


def test_update_and_get_latest_quote(db_session, test_asset):
    quote = update_asset_quote(
        db=db_session,
        asset_id=test_asset.id,
        price=Decimal("2650.00"),
        source="TEST_PRICE_UPDATE",
        is_simulated=True
    )
    latest = get_latest_quote(db_session, test_asset.id)
    assert latest is not None
    assert latest.price == Decimal("2650.00")
    assert latest.source == "TEST_PRICE_UPDATE"
    assert latest.is_simulated is True


def test_list_all_assets_with_quotes(db_session, test_asset):
    items = list_all_assets_with_quotes(db_session, category="STOCK")
    assert len(items) >= 1
    found = next((i for i in items if i["symbol"] == test_asset.symbol), None)
    assert found is not None
    assert found["name"] == test_asset.name
    assert float(found["latest_price"]) == 2500.0


def test_indicative_commodity_proxy_distinction(db_session):
    # Spot Gold Proxy
    spot = Asset(
        symbol="GOLD_SPOT_TEST",
        name="Physical 24K Gold Spot",
        category="COMMODITY",
        currency="INR",
        metadata_json='{"commodity_type": "GOLD", "proxy_type": "INDICATIVE_SPOT"}',
        is_active=True
    )
    # ETF Gold Proxy
    etf = Asset(
        symbol="GOLDBEES_TEST",
        name="Gold BeES ETF",
        category="COMMODITY",
        currency="INR",
        metadata_json='{"commodity_type": "GOLD", "proxy_type": "EXCHANGE_TRADED_FUND"}',
        is_active=True
    )
    db_session.add_all([spot, etf])
    db_session.commit()

    meta_spot = spot.get_metadata()
    meta_etf = etf.get_metadata()

    assert meta_spot["proxy_type"] == "INDICATIVE_SPOT"
    assert meta_etf["proxy_type"] == "EXCHANGE_TRADED_FUND"
    assert meta_spot["proxy_type"] != meta_etf["proxy_type"]
