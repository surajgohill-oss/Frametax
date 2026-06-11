"""
Canonical inventory persistence models.

CanonicalInventorySnapshot: event-level summary captured after each poll run.
CanonicalBlockHistory: per-block record within each snapshot.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Numeric, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CanonicalInventorySnapshot(Base):
    __tablename__ = "canonical_inventory_snapshots"
    __table_args__ = (
        Index("ix_canonical_snapshots_event_ts", "event_id", "snapshot_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    triggered_by_poll_run_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Aggregate metrics
    total_canonical_blocks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_raw_listings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    global_duplicate_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    mirrored_block_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mirrored_ratio: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    mean_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    high_confidence_blocks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_confidence_blocks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_ask: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    by_marketplace: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Seat intelligence metrics
    exact_seat_blocks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inferred_seat_blocks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exact_seat_mirrored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    blocks: Mapped[list["CanonicalBlockHistory"]] = relationship(
        "CanonicalBlockHistory", back_populates="snapshot", cascade="all, delete-orphan"
    )


class CanonicalBlockHistory(Base):
    __tablename__ = "canonical_block_history"
    __table_args__ = (
        Index("ix_canonical_block_history_event_block", "event_id", "block_id"),
        Index("ix_canonical_block_history_snapshot", "snapshot_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("canonical_inventory_snapshots.id", ondelete="CASCADE"), nullable=False)
    block_id: Mapped[str] = mapped_column(String(12), nullable=False)
    section_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    row: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    low_ask: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    high_ask: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    median_ask: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    seller_count: Mapped[int] = mapped_column(Integer, nullable=False)
    marketplace_slugs: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False)
    confidence_v2: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_mirrored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_exact_seats: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    freshness_label: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    snapshot: Mapped["CanonicalInventorySnapshot"] = relationship(
        "CanonicalInventorySnapshot", back_populates="blocks"
    )


class CanonicalBlockLifecycle(Base):
    """
    One row per unique (event_id, block_id).
    Upserted on every canonical snapshot — tracks full lifetime of a canonical block:
    price evolution, market exposure, churn, persistence.
    """
    __tablename__ = "canonical_block_lifecycle"
    __table_args__ = (
        Index("ix_lifecycle_event_id",    "event_id"),
        Index("ix_lifecycle_block_id",    "block_id"),
        Index("ix_lifecycle_disappeared", "event_id", "disappeared_at",
              postgresql_where=sa.text("disappeared_at IS NOT NULL")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    block_id: Mapped[str] = mapped_column(String(12), nullable=False)

    # Identity (denormalized for fast reads without joining back to history)
    section_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    row: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_identity: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)   # exact|inferred|positional
    has_exact_seats: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Lifecycle timestamps
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    disappeared_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # NULL = still active
    reappeared_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    snapshot_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Price evolution
    initial_low_ask: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    current_low_ask: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_low_ask: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_low_ask: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Market exposure
    marketplace_ever: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # all slugs ever seen on

    # Current state (updated on every snapshot)
    current_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False, default=0)
    current_is_mirrored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    current_seller_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
