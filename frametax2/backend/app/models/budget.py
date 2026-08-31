import uuid
from sqlalchemy import String, Text, ForeignKey, Numeric, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import (
    ATLBTLCategory, SpendCategory, CompensationType, ConfidenceTier
)


class BudgetDocument(Base):
    """
    An uploaded budget file associated with a project.
    Raw text stored here; parsed line items in budget_line_items.
    """
    __tablename__ = "budget_documents"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # "pdf", "csv", "xlsx", "txt"
    storage_path: Mapped[str | None] = mapped_column(String(1024))
    raw_text: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    currency_code: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    total_budget_raw: Mapped[float | None] = mapped_column(Numeric(18, 2))
    origin_city: Mapped[str | None] = mapped_column(String(255))
    rate_base: Mapped[str | None] = mapped_column(String(255))
    # e.g. "US union rates IATSE", "UK BECTU rates"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")
    notes: Mapped[str | None] = mapped_column(Text)
    # Canonical Ingestion/Analysis Propagation: the budget_parser.py /
    # classify_budget_line_items version this row was parsed under —
    # nullable so a pre-existing row (parsed before this column existed)
    # is honestly NULL, never backfilled with a guessed version. Mirrors
    # screenplay_structural_parser.PARSER_VERSION's own convention.
    parser_version: Mapped[str | None] = mapped_column(String(40))

    # Additive Phase B link into the universal Document/DocumentVersion
    # layer. Nullable — this rich typed table is preserved as-is; a
    # DocumentVersion may optionally point to its parsed BudgetDocument
    # representation once ingestion (Phase E) creates one.
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="budget_documents")
    line_items: Mapped[list["BudgetLineItem"]] = relationship(back_populates="budget_document")
    document_version: Mapped["DocumentVersion | None"] = relationship()


class BudgetLineItem(Base):
    """
    Individual line item from a budget document.
    Supports both cash and non-cash compensation types.
    """
    __tablename__ = "budget_line_items"

    budget_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("budget_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Classification
    department: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    atl_btl: Mapped[ATLBTLCategory] = mapped_column(
        String(10), nullable=False, default=ATLBTLCategory.BTL
    )
    spend_category: Mapped[SpendCategory | None] = mapped_column(String(50), index=True)
    is_labor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_resident_labor: Mapped[bool | None] = mapped_column(Boolean)
    # null = unknown; True = local resident labor; False = non-resident
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # True for ATL elements with fixed fees; False for BTL variable costs

    # Amounts
    amount_raw: Mapped[float | None] = mapped_column(Numeric(18, 2))
    # As extracted from document
    amount_normalized: Mapped[float | None] = mapped_column(Numeric(18, 2))
    # In document currency, after normalization
    currency_code: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    amount_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    # Converted to USD
    cash_amount_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    # Economic cash value only (excludes deferments / equity)
    accounting_amount_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    # Full accounting value

    # Compensation type
    compensation_type: Mapped[CompensationType] = mapped_column(
        String(20), nullable=False, default=CompensationType.CASH
    )
    deferred_amount_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    equity_amount_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    in_kind_amount_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))

    # Qualification candidates
    is_qualifying_spend_candidate: Mapped[bool] = mapped_column(Boolean, default=True)
    qualifying_amount_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    # Set by calculate_qualified_spend

    # Provenance
    source_row: Mapped[int | None] = mapped_column(Integer)
    source_page: Mapped[int | None] = mapped_column(Integer)
    extraction_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    # 0.0–1.0 from LLM extraction
    review_status: Mapped[str] = mapped_column(String(20), default="pending")
    llm_extracted_raw: Mapped[dict | None] = mapped_column(JSONB)
    # Raw LLM output before normalization

    # Relationships
    budget_document: Mapped["BudgetDocument"] = relationship(back_populates="line_items")
