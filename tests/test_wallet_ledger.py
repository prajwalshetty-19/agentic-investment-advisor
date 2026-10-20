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
