import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import JurisdictionLevel


class Jurisdiction(Base):
    """
    Geographic jurisdiction at any level (country, state, province, region, city).
    Self-referential: a state's parent_id points to its country row.
    """
    __tablename__ = "jurisdictions"

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # e.g. "US", "US-CA", "US-GA", "CA", "CA-ON", "GB"
    iso_code: Mapped[str | None] = mapped_column(String(20), unique=True)
    level: Mapped[JurisdictionLevel] = mapped_column(String(20), nullable=False, index=True)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    # ISO 3166-1 alpha-2 of the containing country
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    # Self-referential relationship
    parent: Mapped["Jurisdiction | None"] = relationship("Jurisdiction", remote_side="Jurisdiction.id")
    children: Mapped[list["Jurisdiction"]] = relationship("Jurisdiction", back_populates="parent")

    # Programs in this jurisdiction
    incentive_programs: Mapped[list["IncentiveProgram"]] = relationship(back_populates="jurisdiction")
    local_cost_benchmarks: Mapped[list["LocalCostBenchmark"]] = relationship(
        back_populates="jurisdiction"
    )
