"""Application configuration module using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Agentic AI Investment Advisor"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Security & Auth
    SECRET_KEY: str = "super_secret_development_key_change_in_production_min_32_chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Virtual Trading Defaults
    DEFAULT_VIRTUAL_BALANCE: float = 0.00
    DEFAULT_CURRENCY: str = "INR"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'advisor.db'}"

    # LLM Settings
    LLM_PROVIDER: str = "GEMINI"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Search & Financial APIs
    TAVILY_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    FMP_API_KEY: Optional[str] = None

    # Server Ports
    FASTAPI_HOST: str = "127.0.0.1"
    FASTAPI_PORT: int = 8000
    STREAMLIT_PORT: int = 8501
    API_BASE_URL: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings()
