"""
incentive_award_ledger.py

Codex final four-row remediation (P0-NL-001): "Do not read
StructureCalculationResult or any candidate/scenario output as a prior
award." A ProductionStructure/StructureCalculationResult row is the
optimizer's own PRICED ESTIMATE for a candidate structure — never a
real-world grant, approval, or contract. The prior implementation summed
these hypothetical rows as if they were awards, which is wrong by
construction: it could count zero, one, or many candidate structures for
the SAME real production as though each were a separate award, and it
had no way to represent "this production applied and was denied" or
"this production has not yet been decided" as anything other than
silent absence.

IncentiveAwardLedgerEntry is the canonical, durable record of a REAL
award event for one (production-company, award-period, program) triple.
It is written ONLY by an explicit act recording real-world evidence
(a grant letter, an approval notice, a denial) — never inferred from
optimizer output, never auto-populated from evaluate_project(). Every
row is additive/append-only history, exactly like ProductionStructure/
StructureCalculationResult's own append-only convention: a status
change (e.g. PENDING -> APPROVED) is a NEW row, not a mutation, so the
full decision history is always reconstructable.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


#: Only these two statuses represent a real, confirmed, cap-consuming
#: award. PENDING/DENIED/WITHDRAWN rows are real, evidenced ledger
#: entries too (they are what makes a company/period's "sibling
#: coverage" complete — see canonical_evaluation._company_period_
#: prior_award_facts) but contribute $0 to the summed prior-award
#: amount.
AWARD_STATUS_APPROVED = "APPROVED"
AWARD_STATUS_GRANTED = "GRANTED"
AWARD_STATUS_PENDING = "PENDING"
AWARD_STATUS_DENIED = "DENIED"
AWARD_STATUS_WITHDRAWN = "WITHDRAWN"
CAP_CONSUMING_AWARD_STATUSES = frozenset({AWARD_STATUS_APPROVED, AWARD_STATUS_GRANTED})

#: Distinguishes a real, sourced record from a placeholder — mirrors the
#: SourceProvenance/evidence-state convention already used throughout
#: program_rate_rules.py (never a bare boolean masquerading as proof).
EVIDENCE_STATE_EVIDENCED = "EVIDENCED"
EVIDENCE_STATE_UNVERIFIED = "UNVERIFIED"


class IncentiveAwardLedgerEntry(Base):
    """One real, evidenced award-status record for one production company
    under one program in one award period. Program-agnostic (program_slug
    is just a column) so any future company/period-scoped cap can reuse
    this SAME table — never a program-specific side ledger.

    Conservation semantics (canonical_evaluation._company_period_prior_
    award_facts): for a given (production_company_identifier,
    award_period_year, program_slug), the sum of native_amount across
    every row whose status is in CAP_CONSUMING_AWARD_STATUSES is the
    real, evidenced prior-award total for that company/period/program —
    summed ONCE in native currency, converted to USD exactly once by the
    caller. A company/period/program with NO rows at all is distinct
    from one with only non-cap-consuming rows (PENDING/DENIED): the
    former can mean "genuinely no other productions" (when no sibling
    Project exists) or "unresolved" (when a sibling Project exists but
    was never recorded here) — see the service-layer resolution logic;
    this model itself only stores the real, append-only facts."""
    __tablename__ = "incentive_award_ledger_entries"

    # Codex: "stable production-company legal-entity identity with
    # evidence/provenance state" — the SAME string identity Project.
    # production_company_identifier already uses (not a separate FK
    # table; a normalized entity table is a larger, separately-scoped
    # change this bounded repair does not require — the identity STRING
    # itself, plus this row's own evidence_state below, is the smallest
    # canonical persistence that satisfies the requirement).
    production_company_identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Codex: "explicit award period/year distinct from target_shoot_year"
    # — this ledger entry's OWN award period, never inferred from any
    # project's target_shoot_year. A project's target_shoot_year is only
    # used (by the read-side resolver) to know WHICH period to query
    # this ledger for; the ledger itself is the source of truth for the
    # period an award was actually granted under.
    award_period_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    program_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Codex final three-program conservation repair (P0-NL-001, fifth
    # pass): "no award-event identity/supersession... one real award
    # counted once." A stable, caller-supplied identity for ONE real
    # award decision (e.g. the producer's own application/reference
    # number) — every row sharing the SAME award_event_id is a STATUS
    # TRANSITION of the SAME real award (PENDING -> APPROVED -> GRANTED),
    # never a second, additional award. Read-side conservation
    # (company_period_program_award_summary) collapses to exactly the
    # NEWEST row per award_event_id before summing, so an
    # APPROVED->GRANTED transition for one award is counted once, never
    # twice. NOT NULL: every real award must have a real, stable
    # identity — an anonymous row can never be reconciled against a
    # future status update, so it would either be silently ignored on
    # supersession or double-counted as a second award.
    award_event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Codex: "native-EUR approved/granted award amount" — generic
    # (native_currency is a real column, not hardcoded EUR) so this
    # table is reusable for any future native-currency company/period
    # cap, but every current caller (Netherlands) writes EUR. NULL is
    # permitted only for non-cap-consuming statuses (PENDING/DENIED/
    # WITHDRAWN) that carry no real award amount at all.
    native_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    native_currency: Mapped[str] = mapped_column(String(10), nullable=False)

    # Codex: "award status and evidence/provenance"
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence_state: Mapped[str] = mapped_column(String(20), nullable=False, default=EVIDENCE_STATE_UNVERIFIED)
    evidence_note: Mapped[str | None] = mapped_column(Text)

    # Optional traceability to the real project this award was granted
    # for — NEVER read by the cap-conservation query itself (which is
    # keyed purely by company+period+program, exactly matching how a
    # real-world incentive-office ledger is organized), but useful for
    # audit/display. SET NULL on project deletion: the award record is
    # independent, durable history, not owned by the project row.
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True,
    )

    recorded_by_note: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index(
            "ix_award_ledger_company_period_program",
            "production_company_identifier", "award_period_year", "program_slug",
        ),
        # Codex final three-program conservation repair (P0-NL-001, fifth
        # pass): every status-transition row for the SAME real award
        # shares this triple + award_event_id — used by the read-side
        # newest-row-per-event collapse.
        Index(
            "ix_award_ledger_event",
            "production_company_identifier", "award_period_year", "program_slug", "award_event_id",
        ),
    )
