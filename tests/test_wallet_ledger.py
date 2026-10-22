"""Tests for virtual wallet balance integrity and append-only ledger."""

from decimal import Decimal
import pytest
from app.services.wallet_service import (
    initialize_user_wallet, debit_wallet, credit_wallet, get_wallet_ledger, InsufficientFundsError
)


def test_wallet_initialization(db_session, test_user):
    ledger_entries = get_wallet_ledger(db_session, test_user.id)
    assert len(ledger_entries) >= 1
    assert ledger_entries[0].transaction_type == "INITIAL_CREDIT"
    assert ledger_entries[0].amount == Decimal("100000.00")
    assert test_user.wallet.balance == Decimal("100000.00")


def test_wallet_debit_and_credit(db_session, test_user):
    # Debit 20,000
    wallet, ledger = debit_wallet(
        db=db_session,
        user_id=test_user.id,
        amount=Decimal("20000.00"),
        transaction_type="BUY_DEBIT",
        description="Purchased stock"
    )
    assert wallet.balance == Decimal("80000.00")
    assert ledger.amount == Decimal("-20000.00")
    assert ledger.balance_after == Decimal("80000.00")

    # Credit 5,000
    wallet2, ledger2 = credit_wallet(
        db=db_session,
        user_id=test_user.id,
        amount=Decimal("5000.00"),
        transaction_type="SELL_CREDIT",
        description="Sold stock"
    )
    assert wallet2.balance == Decimal("85000.00")
    assert ledger2.balance_after == Decimal("85000.00")


def test_overdraw_prevention(db_session, test_user):
    # Attempting to debit more than balance must raise InsufficientFundsError
    with pytest.raises(InsufficientFundsError):
        debit_wallet(
            db=db_session,
            user_id=test_user.id,
            amount=Decimal("150000.00"),
            transaction_type="BUY_DEBIT",
            description="Attempt to overdraw"
        )
    # Balance remains intact
    assert test_user.wallet.balance == Decimal("100000.00")


def test_default_zero_wallet_initialization(db_session):
    from app.db.models import User
    from app.core.security import get_password_hash
    user = User(username="zero_user", email="zero@example.com", hashed_password=get_password_hash("pass123"))
    db_session.add(user)
    db_session.commit()
    wallet, ledger = initialize_user_wallet(db_session, user.id)
    assert wallet.balance == Decimal("0.0000")
    assert ledger.transaction_type == "WALLET_OPENING"
    assert ledger.amount == Decimal("0.0000")


def test_simulated_upi_deposit(db_session, test_user):
    from app.services.wallet_service import deposit_simulated_funds
    wallet, ledger = deposit_simulated_funds(
        db=db_session,
        user_id=test_user.id,
        amount=Decimal("15000.00"),
        payment_method="UPI (Simulation)",
        upi_id="user@okhdfcbank"
    )
    assert wallet.balance == Decimal("115000.00")
    assert ledger.amount == Decimal("15000.00")
    assert ledger.transaction_type == "DEPOSIT_CREDIT"
    assert "UPI (Simulation)" in ledger.description
    assert "user@okhdfcbank" in ledger.description


def test_invalid_deposits_rejected(db_session, test_user):
    from app.services.wallet_service import deposit_simulated_funds
    with pytest.raises(ValueError) as exc:
        deposit_simulated_funds(db=db_session, user_id=test_user.id, amount=Decimal("0.00"))
    assert "strictly positive" in str(exc.value)

    with pytest.raises(ValueError) as exc2:
        deposit_simulated_funds(db=db_session, user_id=test_user.id, amount=Decimal("20000000.00"))
    assert "limit" in str(exc2.value)
