"""Authentication and user profile endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, UserSetting
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_current_user, get_client_ip
from app.core.audit import record_audit_log
from app.services.wallet_service import initialize_user_wallet
from app.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, UserProfileResponse, UpdateSettingsRequest
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    req: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Registers a new user, creates their virtual wallet, and returns an access token."""
    # Check for existing username or email
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    hashed_pw = get_password_hash(req.password)
    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hashed_pw
    )
    db.add(user)
    db.flush()

    # Create user settings with AI execution disabled by default for safety
    user_settings = UserSetting(
        user_id=user.id,
        ai_execution_enabled=False,
        risk_tolerance=req.risk_tolerance or "BALANCED",
        default_currency="INR"
    )
    db.add(user_settings)
    db.flush()

    # Initialize simulated wallet with ₹0 default balance and opening ledger record
    initialize_user_wallet(db, user.id)

    db.commit()
    db.refresh(user)

    ip = get_client_ip(request)
    record_audit_log(
        db=db,
        user_id=user.id,
        action="USER_REGISTER",
        entity_type="USER",
        entity_id=user.id,
        ip_address=ip
    )

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        email=user.email
    )


@router.post("/login", response_model=TokenResponse)
def login_user(
    req: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticates credentials and returns a JWT access token."""
    user = (
        db.query(User)
        .filter((User.username == req.username_or_email) | (User.email == req.username_or_email))
        .first()
    )
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )

    ip = get_client_ip(request)
    record_audit_log(
        db=db,
        user_id=user.id,
        action="USER_LOGIN",
        entity_type="USER",
        entity_id=user.id,
        ip_address=ip
    )

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        email=user.email
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the authenticated user's profile and settings."""
    return current_user


@router.patch("/settings")
def update_user_settings(
    req: UpdateSettingsRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates user settings, such as enabling/disabling AI-assisted execution."""
    settings = db.query(UserSetting).filter(UserSetting.user_id == current_user.id).first()
    if not settings:
        settings = UserSetting(user_id=current_user.id)
        db.add(settings)

    if req.ai_execution_enabled is not None:
        settings.ai_execution_enabled = req.ai_execution_enabled
    if req.risk_tolerance is not None:
        settings.risk_tolerance = req.risk_tolerance
    if req.default_currency is not None:
        settings.default_currency = req.default_currency

    db.commit()
    db.refresh(settings)

    ip = get_client_ip(request)
    record_audit_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE_SETTINGS",
        entity_type="USER_SETTING",
        entity_id=settings.id,
        details={
            "ai_execution_enabled": settings.ai_execution_enabled,
            "risk_tolerance": settings.risk_tolerance
        },
        ip_address=ip
    )
    return {
        "success": True,
        "ai_execution_enabled": settings.ai_execution_enabled,
        "risk_tolerance": settings.risk_tolerance,
        "default_currency": settings.default_currency
    }
