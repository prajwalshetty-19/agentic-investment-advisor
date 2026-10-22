"""Virtual Wallet and Transaction Ledger API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.core.dependencies import get_current_user, get_client_ip
from app.core.audit import record_audit_log
from app.services.wallet_service import get_user_wallet, get_wallet_ledger, credit_wallet, deposit_simulated_funds
from app.schemas.wallet import WalletResponse, LedgerEntryResponse, VirtualDepositRequest

router = APIRouter(prefix="/api/wallet", tags=["Wallet"])


@router.get("", response_model=WalletResponse)
def get_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves the authenticated user's wallet balance."""
    wallet = get_user_wallet(db, current_user.id)
    return wallet


@router.get("/ledger", response_model=List[LedgerEntryResponse])
def get_ledger(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves the immutable audit ledger of all simulated credits and debits."""
    entries = get_wallet_ledger(db, current_user.id, limit=limit, offset=offset)
    return entries


@router.post("/deposit", response_model=WalletResponse)
def deposit_virtual_funds(
    req: VirtualDepositRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adds simulated funds to the wallet via simulated UPI.
    Strictly simulated: No real money, payment gateway, or bank transfer occurs.
    """
    wallet, ledger = deposit_simulated_funds(
        db=db,
        user_id=current_user.id,
        amount=req.amount,
        payment_method=req.payment_method,
        upi_id=req.upi_id,
        description=req.description
    )
    db.commit()
    db.refresh(wallet)

    ip = get_client_ip(request)
    record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SIMULATED_DEPOSIT",
        entity_type="WALLET",
        entity_id=wallet.id,
        details={
            "amount": str(req.amount),
            "payment_method": req.payment_method,
            "upi_id": req.upi_id
        },
        ip_address=ip
    )
    return wallet
