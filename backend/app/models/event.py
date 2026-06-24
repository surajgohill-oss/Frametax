from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    artist: Mapped[str | None] = mapped_column(String(255), nullable=True)
    venue_id: Mapped[int] = mapped_column(Integer, ForeignKey("venues.id"), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="upcoming", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    spotify_artist_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    spotify_artist_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    custom_artwork_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    venue: Mapped["Venue"] = relationship("Venue", back_populates="events")
    tracked_events: Mapped[list["TrackedEvent"]] = relationship(
        "TrackedEvent", back_populates="event"
    )
    listings: Mapped[list["Listing"]] = relationship("Listing", back_populates="event")


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tracked_events: Mapped[list["TrackedEvent"]] = relationship(
        "TrackedEvent", back_populates="marketplace"
    )
    listings: Mapped[list["Listing"]] = relationship("Listing", back_populates="marketplace")


class TrackedEvent(Base):
    __tablename__ = "tracked_events"
    __table_args__ = (
        UniqueConstraint("event_id", "marketplace_id", name="uq_tracked_event_marketplace"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    marketplace_id: Mapped[int] = mapped_column(Integer, ForeignKey("marketplaces.id"), nullable=False)
    external_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    resolution_source: Mapped[str | None] = mapped_column(String(30), nullable=True)
    lifecycle_phase: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_poll_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    consecutive_zero_inventory_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event: Mapped["Event"] = relationship("Event", back_populates="tracked_events")
    marketplace: Mapped["Marketplace"] = relationship("Marketplace", back_populates="tracked_events")
