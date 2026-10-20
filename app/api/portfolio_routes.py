"""Portfolio Holdings and Analytics API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.core.dependencies import get_current_user
from app.services.portfolio_service import get_portfolio_summary
from app.schemas.portfolio import PortfolioSummaryResponse

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioSummaryResponse)
def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full portfolio holdings, valuation, P&L, and asset allocation."""
    summary = get_portfolio_summary(db, current_user.id)
    return summary
