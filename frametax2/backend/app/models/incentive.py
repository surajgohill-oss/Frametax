import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import (
    ProgramType, CreditBasis, ConfidenceTier, ReviewStatus,
    RuleType, FailAction, StackingRuleType, SpendCategory
)


class IncentiveProgram(Base):
    """
    A specific tax credit, rebate, or grant program offered by a jurisdiction.
    Rates and rules are in child tables — not stored as flat columns.
    """
    __tablename__ = "incentive_programs"

    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    program_type: Mapped[ProgramType] = mapped_column(String(30), nullable=False, index=True)
    credit_basis: Mapped[CreditBasis] = mapped_column(String(30), nullable=False)
    base_rate: Mapped[float | None] = mapped_column(Numeric(7, 6))      # null = not yet verified
    max_rate: Mapped[float | None] = mapped_column(Numeric(7, 6))
    is_refundable: Mapped[bool | None] = mapped_column(Boolean)
    is_transferable: Mapped[bool | None] = mapped_column(Boolean)
    transferable_value_pct: Mapped[float | None] = mapped_column(Numeric(7, 6))
    is_competitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    annual_cap_local: Mapped[float | None] = mapped_column(Numeric(18, 2))
    fixed_grant_amount_usd: Mapped[float | None] = mapped_column(Numeric(18, 2))
    requires_cultural_test: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cultural_test_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("qualification_tests.id"), nullable=True
    )
    requires_local_entity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    effective_from: Mapped[str | None] = mapped_column(String(20))
    effective_until: Mapped[str | None] = mapped_column(String(20))
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        String(20), nullable=False, default=ReviewStatus.PENDING
    )
    authority_url: Mapped[str | None] = mapped_column(String(2048))
    last_verified_date: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    jurisdiction: Mapped["Jurisdiction"] = relationship(back_populates="incentive_programs")
    source_document: Mapped["SourceDocument | None"] = relationship(
        back_populates="incentive_programs", foreign_keys=[source_document_id]
    )
    cultural_test: Mapped["QualificationTest | None"] = relationship(
        foreign_keys=[cultural_test_id]
    )
    rules: Mapped[list["IncentiveRule"]] = relationship(back_populates="program")
    qualifying_spend_categories: Mapped[list["QualifyingSpendCategory"]] = relationship(
        back_populates="program"
    )
    uplifts: Mapped[list["ProgramUplift"]] = relationship(back_populates="program")


class IncentiveRule(Base):
    """
    Hard threshold rules that produce pass/fail/reduce decisions for a program.
    """
    __tablename__ = "incentive_rules"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incentive_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=True
    )
    rule_type: Mapped[RuleType] = mapped_column(String(50), nullable=False, index=True)
    threshold_numeric: Mapped[float | None] = mapped_column(Numeric(20, 8))
    threshold_text: Mapped[str | None] = mapped_column(String(512))
    fail_action: Mapped[FailAction] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_page: Mapped[int | None] = mapped_column(Integer)
    source_excerpt: Mapped[str | None] = mapped_column(Text)
    statutory_reference: Mapped[str | None] = mapped_column(String(255))
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )

    # Relationships
    program: Mapped["IncentiveProgram"] = relationship(back_populates="rules")
    source_document: Mapped["SourceDocument | None"] = relationship(back_populates="incentive_rules")


class QualifyingSpendCategory(Base):
    """
    Which spend categories count toward the credit base for each program.
    """
    __tablename__ = "qualifying_spend_categories"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incentive_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    spend_category: Mapped[SpendCategory] = mapped_column(String(50), nullable=False)
    qualifies: Mapped[bool] = mapped_column(Boolean, nullable=False)
    jurisdiction_spend_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # If true, only amounts actually spent IN the jurisdiction count
    notes: Mapped[str | None] = mapped_column(Text)
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )

    # Relationships
    program: Mapped["IncentiveProgram"] = relationship(back_populates="qualifying_spend_categories")


class ProgramUplift(Base):
    """
    Additional credit rates that stack on the base when conditions are met.
    """
    __tablename__ = "program_uplifts"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incentive_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    additional_rate: Mapped[float] = mapped_column(Numeric(7, 6), nullable=False)
    applies_to: Mapped[str] = mapped_column(String(50), nullable=False)
    # "same_qualifying_spend" | "vfx_spend_only" | "music_spend_only"
    condition_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition_threshold: Mapped[float | None] = mapped_column(Numeric(10, 6))
    condition_text: Mapped[str | None] = mapped_column(String(512))
    is_stackable_with_other_uplifts: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )

    # Relationships
    program: Mapped["IncentiveProgram"] = relationship(back_populates="uplifts")


class QualificationTest(Base):
    """
    Named multi-criteria test (e.g. UK BFI Cultural Test, Canadian CAVCO test).
    """
    __tablename__ = "qualification_tests"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    jurisdiction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=True
    )
    total_available_points: Mapped[int | None] = mapped_column(Integer)
    minimum_pass_points: Mapped[int | None] = mapped_column(Integer)
    has_section_minimums: Mapped[bool] = mapped_column(Boolean, default=False)
    section_minimums_json: Mapped[dict | None] = mapped_column(JSONB)
    # e.g. {"C+D": 4} for UK BFI test
    authority_url: Mapped[str | None] = mapped_column(String(2048))
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )

    # Relationships
    rules: Mapped[list["QualificationTestRule"]] = relationship(back_populates="test")


class QualificationTestRule(Base):
    """
    Individual criterion within a qualification test (e.g. UK BFI A1: "Set in UK" = 4 points).
    """
    __tablename__ = "qualification_test_rules"

    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("qualification_tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    criterion_code: Mapped[str] = mapped_column(String(20), nullable=False)
    section: Mapped[str | None] = mapped_column(String(10))
    section_name: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    max_points: Mapped[int] = mapped_column(Integer, nullable=False)
    input_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # "boolean" | "percentage" | "count" | "select"
    input_key: Mapped[str] = mapped_column(String(100), nullable=False)
    # field name in production_details / project intake
    threshold_value: Mapped[float | None] = mapped_column(Numeric(10, 6))
    # for percentage inputs: minimum value to score full points
    scoring_logic: Mapped[str] = mapped_column(Text, nullable=False)
    # human-readable rule for awarding points
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )

    # Relationships
    test: Mapped["QualificationTest"] = relationship(back_populates="rules")


class LegalStackingRule(Base):
    """
    Defines which programs can/cannot be combined for the same production.
    Prevents illegal double-counting recommendations.
    """
    __tablename__ = "legal_stacking_rules"

    program_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incentive_programs.id"), nullable=False, index=True
    )
    program_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incentive_programs.id"), nullable=False, index=True
    )
    rule_type: Mapped[StackingRuleType] = mapped_column(String(20), nullable=False)
    condition_text: Mapped[str | None] = mapped_column(Text)
    statutory_reference: Mapped[str | None] = mapped_column(String(255))
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_documents.id"), nullable=True
    )
    confidence_tier: Mapped[ConfidenceTier] = mapped_column(
        String(20), nullable=False, default=ConfidenceTier.DISCOVERY
    )
    notes: Mapped[str | None] = mapped_column(Text)
