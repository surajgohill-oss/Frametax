import uuid
from sqlalchemy import String, Text, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import DocumentType, ConfidenceTier, ReviewStatus


class SourceDocument(Base):
    """
    Authoritative source documents for rules, rates, treaties, guides.
    Each incentive rule must trace back to a source_document row.
    """
    __tablename__ = "source_documents"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(String(50), nullable=False, index=True)
    jurisdiction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=True, index=True
    )
    authority_name: Mapped[str | None] = mapped_column(String(255))   # "Film Georgia", "DCMS"
    source_url: Mapped[str | None] = mapped_column(String(2048))
    publication_date: Mapped[str | None] = mapped_column(String(20))  # ISO date string
    effective_from: Mapped[str | None] = mapped_column(String(20))
    effective_until: Mapped[str | None] = mapped_column(String(20))
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        String(20), nullable=False, default=ReviewStatus.PENDING
    )
    storage_path: Mapped[str | None] = mapped_column(String(1024))    # local path or S3 key
    raw_text: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    jurisdiction: Mapped["Jurisdiction | None"] = relationship()
    incentive_programs: Mapped[list["IncentiveProgram"]] = relationship(
        back_populates="source_document", foreign_keys="IncentiveProgram.source_document_id"
    )
    incentive_rules: Mapped[list["IncentiveRule"]] = relationship(back_populates="source_document")
