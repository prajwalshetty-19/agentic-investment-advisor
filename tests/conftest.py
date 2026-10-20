"""Pytest fixtures for database, test clients, and test authentication."""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.db.models import User, UserSetting, Asset, MarketQuote
from app.services.wallet_service import initialize_user_wallet

# Test SQLite in-memory engine with StaticPool to keep schema across connections
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh in-memory database schema for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient overriding the get_db dependency."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Creates a standard test user with a virtual wallet."""
    user = User(
        username="investor_one",
        email="investor1@example.com",
        hashed_password=get_password_hash("password123")
    )
    db_session.add(user)
    db_session.flush()

    setting = UserSetting(
        user_id=user.id,
        ai_execution_enabled=True,
        risk_tolerance="GROWTH",
        default_currency="INR"
    )
    db_session.add(setting)
    initialize_user_wallet(db_session, user.id, initial_balance=Decimal("100000.00"))
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Returns valid Bearer token headers for test_user."""
    token = create_access_token({"sub": str(test_user.id), "username": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_asset(db_session):
    """Creates a test stock asset with a quote."""
    asset = Asset(
        symbol="TEST_RELIANCE",
        name="Test Reliance Corp",
        category="STOCK",
        currency="INR",
        metadata_json='{"sector": "Energy", "pe_ratio": 25.0}',
        is_active=True
    )
    db_session.add(asset)
    db_session.flush()

    quote = MarketQuote(
        asset_id=asset.id,
        price=Decimal("2500.00"),
        source="TEST_FEED",
        is_simulated=True
    )
    db_session.add(quote)
    db_session.commit()
    db_session.refresh(asset)
    return asset
