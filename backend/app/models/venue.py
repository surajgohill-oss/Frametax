from sqlalchemy import (
    String, Integer, Float, JSON, SmallInteger, Boolean,
    UniqueConstraint, ForeignKey, Numeric, DateTime
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), default="Los Angeles")
    state: Mapped[str] = mapped_column(String(2), default="CA")
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="America/Los_Angeles")
    # kept for backward compat with existing map route
    map_width: Mapped[int] = mapped_column(Integer, default=700)
    map_height: Mapped[int] = mapped_column(Integer, default=500)

    sections: Mapped[list["VenueSection"]] = relationship(
        "VenueSection", back_populates="venue", cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship("Event", back_populates="venue")


class VenueSection(Base):
    """Canonical venue section — venue geometry, not event-specific."""
    __tablename__ = "venue_sections"
    __table_args__ = (UniqueConstraint("venue_id", "section_id", name="uq_venue_section"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue_id: Mapped[int] = mapped_column(Integer, ForeignKey("venues.id"), nullable=False)

    # ── Identity ──────────────────────────────────────────────────────────────
    section_id: Mapped[str] = mapped_column(String(50), nullable=False)   # canonical key: "101", "M32", "FLOOR_A"
    display_name: Mapped[str] = mapped_column(String(100), nullable=False) # "Section 101"

    # ── Physical classification ───────────────────────────────────────────────
    tier: Mapped[str] = mapped_column(String(50), nullable=False)
    # level: lower | club | upper_mid | upper_top | floor | suite | arcade
    level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # zone: sideline_west | sideline_east | endzone_north | endzone_south |
    #        corner_nw | corner_ne | corner_sw | corner_se | floor | suite
    zone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # side: west | east | north | south | center
    side: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    row_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    seat_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # ── Quality ───────────────────────────────────────────────────────────────
    quality_score: Mapped[int] = mapped_column(Integer, default=50)

    # ── Future map support ────────────────────────────────────────────────────
    future_map_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    width: Mapped[float] = mapped_column(Float, default=40.0)
    height: Mapped[float] = mapped_column(Float, default=30.0)
    shape: Mapped[str] = mapped_column(String(20), default="rect")
    shape_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ── Legacy per-marketplace JSON aliases (deprecated, use VenueSectionAlias) ──
    stubhub_aliases: Mapped[list | None] = mapped_column(JSON, nullable=True)
    seatgeek_aliases: Mapped[list | None] = mapped_column(JSON, nullable=True)

    venue: Mapped["Venue"] = relationship("Venue", back_populates="sections")
    aliases: Mapped[list["VenueSectionAlias"]] = relationship(
        "VenueSectionAlias", back_populates="section", cascade="all, delete-orphan"
    )
    metrics: Mapped[list["VenueSectionMetrics"]] = relationship(
        "VenueSectionMetrics", back_populates="section", cascade="all, delete-orphan"
    )


class VenueSectionAlias(Base):
    """
    Marketplace-agnostic section alias registry.

    Maps every raw section string a marketplace sends to a canonical VenueSection.
    To support a new marketplace, insert alias rows — no schema changes needed.

    alias             = raw string from marketplace (e.g. "CLUB INFIELD 207")
    alias_normalized  = lowercase+stripped version for fast lookup
    marketplace_id    = NULL means alias applies across all marketplaces
    event_type        = NULL means alias applies across all event types;
                        set to 'nfl', 'concert', 'soccer' when naming differs by event type
    """
    __tablename__ = "venue_section_aliases"
    __table_args__ = (
        UniqueConstraint(
            "venue_section_id", "marketplace_id", "alias_normalized",
            name="uq_vsa_section_mp_alias"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue_section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("venue_sections.id", ondelete="CASCADE"), nullable=False
    )
    marketplace_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("marketplaces.id", ondelete="SET NULL"), nullable=True
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    alias_normalized: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at = mapped_column(DateTime, nullable=False, server_default=func.now())

    section: Mapped["VenueSection"] = relationship("VenueSection", back_populates="aliases")


class VenueSectionMetrics(Base):
    """Per-event intelligence metrics rolled up to canonical section level."""
    __tablename__ = "venue_section_metrics"
    __table_args__ = (
        UniqueConstraint("venue_section_id", "event_id", name="uq_vsm_section_event"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue_section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("venue_sections.id", ondelete="CASCADE"), nullable=False
    )
    event_id: Mapped[int] = mapped_column(Integer, nullable=False)
    computed_at = mapped_column(DateTime, nullable=False, server_default=func.now())

    # Price stats
    low_ask: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    median_ask: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    high_ask: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    p25_ask: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    p75_ask: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Inventory
    inventory: Mapped[int | None] = mapped_column(Integer, nullable=True)
    listing_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ticket_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Trends (24h deltas)
    inventory_delta_24h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_delta_24h: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_delta_pct_24h: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)

    # Computed intelligence scores (1-100)
    deal_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    demand_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    seller_pressure: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    value_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # Relative to venue and tier medians
    price_vs_tier_median: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    price_vs_venue_median: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)

    section: Mapped["VenueSection"] = relationship("VenueSection", back_populates="metrics")
