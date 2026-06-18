import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import ConfidenceTier


class TalentProfile(Base):
    """
    Director, writer, producer, or cast member with known attributes
    that affect qualification tests and incentive eligibility.
    """
    __tablename__ = "talent_profiles"

    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # "director" | "writer" | "producer" | "lead_cast" | "cast"
    imdb_id: Mapped[str | None] = mapped_column(String(50), unique=True)
    primary_nationality: Mapped[str | None] = mapped_column(String(100))
    # ISO 3166-1 alpha-2 country code
    known_residencies: Mapped[list | None] = mapped_column(JSONB)
    # [{"jurisdiction_code": "GB", "confirmed": true}]
    guild_memberships: Mapped[list | None] = mapped_column(JSONB)
    # ["SAG-AFTRA", "DGA"]
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    qualification_attributes: Mapped[list["TalentQualificationAttribute"]] = relationship(
        back_populates="talent"
    )


class TalentQualificationAttribute(Base):
    """
    Specific jurisdiction-level qualification attributes for a talent profile.
    e.g. "is_uk_resident=True for UK AVEC cultural test scoring"
    """
    __tablename__ = "talent_qualification_attributes"

    talent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=False, index=True
    )
    attribute_key: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. "is_resident", "is_citizen", "qualifies_for_local_labor_credit"
    attribute_value: Mapped[bool | None] = mapped_column(Boolean)
    attribute_text: Mapped[str | None] = mapped_column(String(255))
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    talent: Mapped["TalentProfile"] = relationship(back_populates="qualification_attributes")
