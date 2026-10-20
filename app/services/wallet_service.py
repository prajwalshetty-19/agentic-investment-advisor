"""Virtual Wallet and Append-Only Ledger Service.

Enforces zero negative balances, immutable transaction auditing,
and atomic database transactions for all virtual fund movements.
"""

from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from app.db.models import Wallet, WalletLedger, User
from app.config import get_settings

settings = get_settings()


class InsufficientFundsError(Exception):
    """Raised when an order or debit exceeds available virtual wallet balance."""
    pass


def initialize_user_wallet(
    db: Session,
    user_id: int,
    initial_balance: Optional[Decimal] = None
) -> Tuple[Wallet, WalletLedger]:
    """
    Initializes a new virtual wallet for a registered user and writes
    the initial credit transaction to the append-only ledger.
    """
    balance = initial_balance if initial_balance is not None else Decimal(str(settings.DEFAULT_VIRTUAL_BALANCE))
    
    # Check if wallet already exists
    existing = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if existing:
        return existing, None

    wallet = Wallet(
        user_id=user_id,
        balance=balance,
        currency=settings.DEFAULT_CURRENCY
    )
    db.add(wallet)
    db.flush()

    ledger = WalletLedger(
        wallet_id=wallet.id,
        order_id=None,
        transaction_type="INITIAL_CREDIT",
        amount=balance,
        balance_after=balance,
        description=f"Initial virtual demo funds credited ({settings.DEFAULT_CURRENCY} {balance:,.2f})"
    )
    db.add(ledger)
    db.commit()
    db.refresh(wallet)
    return wallet, ledger


def get_user_wallet(db: Session, user_id: int) -> Wallet:
    """Retrieves user wallet. Auto-initializes if missing."""
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        wallet, _ = initialize_user_wallet(db, user_id)
    return wallet


def debit_wallet(
    db: Session,
    user_id: int,
    amount: Decimal,
    transaction_type: str,
    description: str,
    order_id: Optional[int] = None
) -> Tuple[Wallet, WalletLedger]:
    """
    Debits funds atomically from the user's virtual wallet.
    Guarantees balance >= 0. Raises InsufficientFundsError if balance is inadequate.
    """
    if amount <= Decimal("0"):
        raise ValueError("Debit amount must be strictly positive")

    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).with_for_update().first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User wallet not found")

    if wallet.balance < amount:
        raise InsufficientFundsError(
            f"Insufficient virtual balance. Required: {wallet.currency} {amount:,.2f}, Available: {wallet.currency} {wallet.balance:,.2f}"
        )

    new_balance = wallet.balance - amount
    wallet.balance = new_balance

    ledger = WalletLedger(
        wallet_id=wallet.id,
        order_id=order_id,
        transaction_type=transaction_type,
        amount=-amount,
        balance_after=new_balance,
        description=description
    )
    db.add(ledger)
    db.flush()
    return wallet, ledger


def credit_wallet(
    db: Session,
    user_id: int,
    amount: Decimal,
    transaction_type: str,
    description: str,
    order_id: Optional[int] = None
) -> Tuple[Wallet, WalletLedger]:
    """
    Credits funds atomically to the user's virtual wallet and appends
    an entry to the ledger.
    """
    if amount <= Decimal("0"):
        raise ValueError("Credit amount must be strictly positive")

    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).with_for_update().first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User wallet not found")

    new_balance = wallet.balance + amount
    wallet.balance = new_balance

    ledger = WalletLedger(
        wallet_id=wallet.id,
        order_id=order_id,
        transaction_type=transaction_type,
        amount=amount,
        balance_after=new_balance,
        description=description
    )
    db.add(ledger)
    db.flush()
    return wallet, ledger


def get_wallet_ledger(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[WalletLedger]:
    """Fetches the immutable transaction history for the user's wallet."""
    wallet = get_user_wallet(db, user_id)
    return (
        db.query(WalletLedger)
        .filter(WalletLedger.wallet_id == wallet.id)
        .order_by(WalletLedger.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
