"""Virtual Wallet and Transaction Ledger API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.core.dependencies import get_current_user, get_client_ip
from app.core.audit import record_audit_log
from app.services.wallet_service import get_user_wallet, get_wallet_ledger, credit_wallet
from app.schemas.wallet import WalletResponse, LedgerEntryResponse, VirtualDepositRequest

router = APIRouter(prefix="/api/wallet", tags=["Virtual Wallet"])


@router.get("", response_model=WalletResponse)
def get_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves the authenticated user's virtual wallet balance."""
    wallet = get_user_wallet(db, current_user.id)
    return wallet


@router.get("/ledger", response_model=List[LedgerEntryResponse])
def get_ledger(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves the immutable audit ledger of all virtual credits and debits."""
    entries = get_wallet_ledger(db, current_user.id, limit=limit, offset=offset)
    return entries


@router.post("/deposit", response_model=WalletResponse)
def deposit_virtual_funds(
    req: VirtualDepositRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adds simulated virtual funds to the wallet (faucet feature for demo testing)."""
    wallet, ledger = credit_wallet(
        db=db,
        user_id=current_user.id,
        amount=req.amount,
        transaction_type="DEPOSIT_CREDIT",
        description=req.description or "User-initiated virtual demo deposit"
    )
    db.commit()
    db.refresh(wallet)

    ip = get_client_ip(request)
    record_audit_log(
        db=db,
        user_id=current_user.id,
        action="VIRTUAL_DEPOSIT",
        entity_type="WALLET",
        entity_id=wallet.id,
        details={"amount": str(req.amount)},
        ip_address=ip
    )
    return wallet
