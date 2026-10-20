"""Pydantic schemas for user registration, authentication, and profile."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_.-]+$")
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    risk_tolerance: Optional[str] = "BALANCED"


class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str


class UserSettingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ai_execution_enabled: bool
    risk_tolerance: str
    default_currency: str
    updated_at: datetime


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime
    settings: Optional[UserSettingSchema] = None


class UpdateSettingsRequest(BaseModel):
    ai_execution_enabled: Optional[bool] = None
    risk_tolerance: Optional[str] = None
    default_currency: Optional[str] = None
