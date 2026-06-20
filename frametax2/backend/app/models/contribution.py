"""
contribution.py — ProductionContribution ORM model.

Tracks every form of value entering a production: cash, deferred fees,
equity deals, in-kind goods/services, sponsorships, government support,
and vendor financing arrangements.

Each contribution records:
  - face value (amount)
  - fair market value (FMV) — what it's worth at arm's-length market price
  - replacement cost — what the production would pay if the contribution were
    withdrawn and replaced with market-rate equivalents
  - incentive qualifying flag — whether the contribution counts toward QPE
    in the linked jurisdiction's programme
"""
import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ContributionType, ConfidenceTier


class ProductionContribution(Base):
    __tablename__ = "production_contributions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    jurisdiction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=True, index=True,
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=True,
    )

    contribution_type: Mapped[ContributionType] = mapped_column(
        String(30), nullable=False, index=True,
    )
    provider: Mapped[str] = mapped_column(String(512), nullable=False)

    # Monetary values
    amount: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False,
        comment="Face / stated value of the contribution in USD",
    )
    fair_market_value: Mapped[float | None] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="Arm's-length market value; may differ from amount for equity/in-kind",
    )
    replacement_cost: Mapped[float | None] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="Cost to replace this contribution at open-market rates if withdrawn",
    )

    # Jurisdiction and incentive linkage
    jurisdiction_specific: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="True if this contribution is tied to spend in a specific jurisdiction",
    )
    qualifies_for_incentive: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True,
        comment="Whether this contribution counts toward qualifying spend in the linked programme",
    )

    # Conditionality
    is_conditional: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="True if this contribution only materialises upon a condition (delivery, etc.)",
    )
    condition_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provenance
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY,
    )
    effective_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="contributions")
    jurisdiction: Mapped["Jurisdiction | None"] = relationship()
    source_document: Mapped["SourceDocument | None"] = relationship()
