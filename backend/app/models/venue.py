from sqlalchemy import String, Integer, Float, JSON, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), default="Los Angeles")
    state: Mapped[str] = mapped_column(String(2), default="CA")
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    map_width: Mapped[int] = mapped_column(Integer, default=700)
    map_height: Mapped[int] = mapped_column(Integer, default=500)

    sections: Mapped[list["VenueSection"]] = relationship(
        "VenueSection", back_populates="venue", cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship("Event", back_populates="venue")


class VenueSection(Base):
    __tablename__ = "venue_sections"
    __table_args__ = (UniqueConstraint("venue_id", "section_id", name="uq_venue_section"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue_id: Mapped[int] = mapped_column(Integer, ForeignKey("venues.id"), nullable=False)
    section_id: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, default=50)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, default=40.0)
    height: Mapped[float] = mapped_column(Float, default=30.0)
    shape: Mapped[str] = mapped_column(String(20), default="rect")
    shape_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    stubhub_aliases: Mapped[list | None] = mapped_column(JSON, nullable=True)
    seatgeek_aliases: Mapped[list | None] = mapped_column(JSON, nullable=True)

    venue: Mapped["Venue"] = relationship("Venue", back_populates="sections")
