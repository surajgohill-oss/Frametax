from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Numeric, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_listings_event_marketplace", "event_id", "marketplace_id"),
        Index("ix_listings_event_section", "event_id", "section_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    marketplace_id: Mapped[int] = mapped_column(Integer, ForeignKey("marketplaces.id"), nullable=False)
    external_listing_id: Mapped[str] = mapped_column(String(255), nullable=False)
    section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    section_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    row: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fees: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    all_in_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    listing_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    event: Mapped["Event"] = relationship("Event", back_populates="listings")
    marketplace: Mapped["Marketplace"] = relationship("Marketplace", back_populates="listings")
    snapshots: Mapped[list["ListingSnapshot"]] = relationship("ListingSnapshot", back_populates="listing")


class ListingSnapshot(Base):
    __tablename__ = "listing_snapshots"
    __table_args__ = (
        Index("ix_snapshots_event_ts", "event_id", "snapshot_at"),
        Index("ix_snapshots_event_mp_ts", "event_id", "marketplace_id", "snapshot_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("listings.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    marketplace_id: Mapped[int] = mapped_column(Integer, ForeignKey("marketplaces.id"), nullable=False)
    section_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fees: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    all_in_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    listing: Mapped["Listing"] = relationship("Listing", back_populates="snapshots")


class PollRun(Base):
    __tablename__ = "poll_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tracked_event_id: Mapped[int] = mapped_column(Integer, ForeignKey("tracked_events.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    listings_found: Mapped[int] = mapped_column(Integer, default=0)
    new_listings: Mapped[int] = mapped_column(Integer, default=0)
    disappeared_listings: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="running")
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
