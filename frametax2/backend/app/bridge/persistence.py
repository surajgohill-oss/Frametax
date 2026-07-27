"""
Bridge persistence — a dedicated local SQLite database, NOT the app's
existing Postgres schema (app/db/, app/models/). That schema is a
separate, dormant, unrelated domain (production/budget/incentive/talent
records for a different feature) with its own Alembic migration chain;
grafting bridge tables onto it would mean either standing up Postgres+
Redis just to run a local audit (this environment has neither reachable
— see architecture-discovery notes) or migrating an unrelated schema for
no shared-domain benefit. SQLAlchemy itself (the ORM) IS reused — same
library, same declarative-model pattern the rest of the app already
uses — only the physical database is separate. Moving this to Postgres
later is a one-line DATABASE_URL change plus a `create_all()`/Alembic
pass; no model redesign required (see BridgeSettings.BRIDGE_DB_PATH).

Tables are append-only by convention: rows are inserted, never updated
or deleted, except dispositions (which record an explicit new human
decision as a new row referencing the prior one — see
ReconciliationDispositionRecord.supersedes_id) and the ledger (which
marks an entry SUPERSEDED via a new row, never edits the old one).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.bridge.config import BridgeSettings, get_bridge_settings


class BridgeBase(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PackageRecord(BridgeBase):
    __tablename__ = "bridge_packages"
    package_id: Mapped[str] = mapped_column(String, primary_key=True)
    package_schema_version: Mapped[str] = mapped_column(String)
    production_or_scenario_id: Mapped[str] = mapped_column(String, index=True)
    operation: Mapped[str] = mapped_column(String, index=True)
    confidentiality: Mapped[str] = mapped_column(String)
    repository_commit: Mapped[str | None] = mapped_column(String, nullable=True)
    generated_at: Mapped[str] = mapped_column(String)
    package_json: Mapped[str] = mapped_column(Text)  # full AuditPackage, exact bytes considered for sending
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ProviderResponseRecord(BridgeBase):
    __tablename__ = "bridge_provider_responses"
    response_id: Mapped[str] = mapped_column(String, primary_key=True)
    package_id: Mapped[str] = mapped_column(String, index=True)
    provider: Mapped[str] = mapped_column(String, index=True)
    model_id: Mapped[str] = mapped_column(String)
    operation: Mapped[str] = mapped_column(String)
    request_json: Mapped[str] = mapped_column(Text)          # normalized request payload (no secrets)
    response_text: Mapped[str] = mapped_column(Text)
    parsed_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    usage_json: Mapped[str] = mapped_column(Text)
    provider_request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_category: Mapped[str] = mapped_column(String)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fallback_used: Mapped[bool] = mapped_column(default=False)
    request_content_hash: Mapped[str] = mapped_column(String, index=True)  # duplicate-request detection
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ReconciliationClusterRecord(BridgeBase):
    __tablename__ = "bridge_reconciliation_clusters"
    cluster_id: Mapped[str] = mapped_column(String, primary_key=True)
    package_id: Mapped[str] = mapped_column(String, index=True)
    jurisdiction_or_program: Mapped[str | None] = mapped_column(String, nullable=True)
    agreement_kind: Mapped[str] = mapped_column(String)
    cluster_json: Mapped[str] = mapped_column(Text)  # full ReconciledCluster
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class DispositionRecord(BridgeBase):
    __tablename__ = "bridge_dispositions"
    disposition_id: Mapped[str] = mapped_column(String, primary_key=True)
    cluster_id: Mapped[str] = mapped_column(String, index=True)
    disposition: Mapped[str] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispositioned_by: Mapped[str] = mapped_column(String)
    implementation_task_id: Mapped[str | None] = mapped_column(String, nullable=True)
    supersedes_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class LedgerEntryRecord(BridgeBase):
    __tablename__ = "bridge_ledger_entries"
    row_id: Mapped[str] = mapped_column(String, primary_key=True)  # unique per row (versioned)
    entry_id: Mapped[str] = mapped_column(String, index=True)      # stable across versions
    kind: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    entry_json: Mapped[str] = mapped_column(Text)  # full LedgerEntry
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class UsageLedgerRecord(BridgeBase):
    """Section 13's per-provider/model/operation usage ledger — one row
    per completed (successful or failed) request, append-only."""
    __tablename__ = "bridge_usage_ledger"
    row_id: Mapped[str] = mapped_column(String, primary_key=True)
    provider: Mapped[str] = mapped_column(String, index=True)
    model_id: Mapped[str] = mapped_column(String, index=True)
    operation: Mapped[str] = mapped_column(String, index=True)
    input_tokens: Mapped[int | None] = mapped_column(nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_category: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


_engine = None
_SessionLocal: sessionmaker | None = None


def _engine_and_session(settings: BridgeSettings | None = None):
    global _engine, _SessionLocal
    settings = settings or get_bridge_settings()
    if _engine is None:
        db_path = settings.BRIDGE_DB_PATH
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        _engine = create_engine(f"sqlite:///{db_path}", future=True)
        BridgeBase.metadata.create_all(_engine)
        _SessionLocal = sessionmaker(bind=_engine, future=True)
    return _engine, _SessionLocal


def get_session(settings: BridgeSettings | None = None) -> Session:
    _, session_local = _engine_and_session(settings)
    return session_local()


def reset_persistence_cache() -> None:
    """Test-only: force re-creation of the engine (e.g. after pointing
    BRIDGE_DB_PATH at a fresh temp file)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
