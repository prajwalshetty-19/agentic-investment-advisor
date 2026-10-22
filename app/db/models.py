"""SQLAlchemy declarative models for all platform entities."""

from datetime import datetime, timezone
import json
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    settings = relationship("UserSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    ai_execution_enabled = Column(Boolean, default=False, nullable=False)
    risk_tolerance = Column(String(32), default="BALANCED", nullable=False)  # CONSERVATIVE, BALANCED, GROWTH, AGGRESSIVE
    default_currency = Column(String(8), default="INR", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="settings")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance = Column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    currency = Column(String(8), default="INR", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="wallet")
    ledger_entries = relationship("WalletLedger", back_populates="wallet", cascade="all, delete-orphan", order_by="desc(WalletLedger.id)")


class WalletLedger(Base):
    __tablename__ = "wallet_ledger"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_type = Column(String(32), nullable=False)  # INITIAL_CREDIT, BUY_DEBIT, SELL_CREDIT, INTEREST_CREDIT, MATURITY_CREDIT
    amount = Column(Numeric(18, 4), nullable=False)
    balance_after = Column(Numeric(18, 4), nullable=False)
    description = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    wallet = relationship("Wallet", back_populates="ledger_entries")
    order = relationship("Order")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False, index=True)
    category = Column(String(32), nullable=False, index=True)  # STOCK, MUTUAL_FUND, BOND, COMMODITY, FD, RD
    currency = Column(String(8), default="INR", nullable=False)
    metadata_json = Column(Text, default="{}", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    quotes = relationship("MarketQuote", back_populates="asset", cascade="all, delete-orphan", order_by="desc(MarketQuote.timestamp)")
    financial_data = relationship("FinancialData", back_populates="asset", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="asset")
    orders = relationship("Order", back_populates="asset")

    def get_metadata(self) -> dict:
        try:
            return json.loads(self.metadata_json or "{}")
        except Exception:
            return {}

    def set_metadata(self, data: dict):
        self.metadata_json = json.dumps(data)


class MarketQuote(Base):
    __tablename__ = "market_quotes"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Numeric(18, 4), nullable=False)
    bid = Column(Numeric(18, 4), nullable=True)
    ask = Column(Numeric(18, 4), nullable=True)
    nav = Column(Numeric(18, 4), nullable=True)
    source = Column(String(64), default="SIMULATED", nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    asset = relationship("Asset", back_populates="quotes")


class FinancialData(Base):
    __tablename__ = "financial_data"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String(64), nullable=False, index=True)
    metric_value = Column(Numeric(18, 4), nullable=False)
    period = Column(String(32), default="TTM", nullable=False)
    source = Column(String(64), default="CALCULATED", nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    asset = relationship("Asset", back_populates="financial_data")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    doc_type = Column(String(64), nullable=False)  # ANNUAL_REPORT, SCHEME_INFO, BOND_TERM_SHEET, MACRO_NOTE
    file_path = Column(String(512), nullable=True)
    source_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_id = Column(String(128), nullable=True)
    page_number = Column(Integer, default=1, nullable=False)

    document = relationship("Document", back_populates="chunks")


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="analysis_sessions")
    agent_runs = relationship("AgentRun", back_populates="session", cascade="all, delete-orphan")
    report = relationship("AnalysisReport", back_populates="session", uselist=False, cascade="all, delete-orphan")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False)
    input_data = Column(Text, default="{}", nullable=False)
    output_data = Column(Text, default="{}", nullable=False)
    status = Column(String(32), default="SUCCESS", nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    session = relationship("AnalysisSession", back_populates="agent_runs")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    content_markdown = Column(Text, nullable=False)
    structured_metrics_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    session = relationship("AnalysisSession", back_populates="report")
    user = relationship("User")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    side = Column(String(8), nullable=False)  # BUY, SELL
    order_type = Column(String(16), default="MARKET", nullable=False)  # MARKET, LIMIT
    quantity = Column(Numeric(18, 4), nullable=False)
    price = Column(Numeric(18, 4), nullable=False)
    total_amount = Column(Numeric(18, 4), nullable=False)
    estimated_fee = Column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    status = Column(String(32), default="PENDING_APPROVAL", nullable=False, index=True)  # PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED, CANCELLED, FAILED
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="orders")
    asset = relationship("Asset", back_populates="orders")
    approval = relationship("OrderApproval", back_populates="order", uselist=False, cascade="all, delete-orphan")
    trade = relationship("Trade", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderApproval(Base):
    __tablename__ = "order_approvals"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    approved_quantity = Column(Numeric(18, 4), nullable=False)
    approved_price = Column(Numeric(18, 4), nullable=False)
    approved_total_amount = Column(Numeric(18, 4), nullable=False)
    approval_status = Column(String(16), nullable=False)  # APPROVED, REJECTED
    approved_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    ip_address = Column(String(45), nullable=True)

    order = relationship("Order", back_populates="approval")
    user = relationship("User")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    executed_quantity = Column(Numeric(18, 4), nullable=False)
    executed_price = Column(Numeric(18, 4), nullable=False)
    fee = Column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    realized_pnl = Column(Numeric(18, 4), default=Decimal("0.0000"), nullable=True)
    executed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    order = relationship("Order", back_populates="trade")
    user = relationship("User")
    asset = relationship("Asset")


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint("user_id", "asset_id", name="uq_user_asset_holding"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    average_buy_price = Column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    total_invested = Column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="holdings")
    asset = relationship("Asset", back_populates="holdings")


class Watchlist(Base):
    __tablename__ = "watchlists"
    __table_args__ = (
        UniqueConstraint("user_id", "asset_id", name="uq_user_asset_watchlist"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    added_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="watchlists")
    asset = relationship("Asset")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)  # LOGIN, TOGGLE_AI_EXECUTION, PROPOSE_ORDER, APPROVE_ORDER, EXECUTE_ORDER, REJECT_ORDER
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details_json = Column(Text, default="{}", nullable=False)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
