"""
incentive_award_ledger_service.py

Codex final four-row remediation (P0-NL-001) — the ONE established
schema/service path for recording and reading real incentive award
evidence. Never a DB-only field no producer workflow can set: this is
the service layer any future route/CLI/admin action calls to record a
real award decision, and the ONLY function canonical_evaluation.py's
company/period cap resolution reads from.

Codex final three-program conservation repair (P0-NL-001, fifth pass) —
this module's real defects, from Codex's own independent adverse
reproduction against the public writer, are fixed here:

  1. record_incentive_award() previously acquired the advisory lock but
     never actually READ the current state before writing — it always
     inserted. Two concurrent EUR3,000,000 writes for the SAME triple
     both committed, producing a real EUR6,000,000 total against a
     EUR3,000,000 cap. FIXED: the lock now genuinely guards a real
     read-decide-write critical section — the current authoritative
     total is read INSIDE the lock, the prospective new total is
     computed, and the write is REJECTED (raises ValueError) if it
     would exceed the program's own registered cap.
  2. Rows had no award-event identity — an APPROVED -> GRANTED status
     transition for the SAME real award inserted a SECOND row that the
     old summary function summed alongside the first, double-counting
     one real award as two. FIXED: every row now carries a caller-
     supplied, stable award_event_id; the summary function collapses to
     exactly the NEWEST row per award_event_id before summing, so a
     status transition for one award is counted once, never twice.
  3. A USD-denominated row was numerically added to a EUR total as if
     the currencies were interchangeable. FIXED: record_incentive_award
     validates native_currency against the program's OWN registered cap
     currency at write time — a mismatched currency is REJECTED before
     it can ever enter the ledger, and company_period_program_award_summary
     additionally never sums across a mismatched currency defensively.

CONCURRENCY: record_incentive_award() takes a real, transaction-scoped
PostgreSQL advisory lock (pg_advisory_xact_lock) keyed on the exact
(production_company_identifier, award_period_year, program_slug)
triple, reads the current authoritative state, and only then decides
whether to write — all inside the SAME locked transaction. The lock is
held for the remainder of the CALLING transaction and is released
automatically on COMMIT or ROLLBACK — it can never leak across a
pooled connection. A second concurrent call for the SAME triple blocks
until the first transaction ends, then observes its committed row
before making its own cap decision — this is what makes "two concurrent
sessions cannot both consume the same remaining cap" a real, provable
database guarantee rather than an application-level race.
"""
from __future__ import annotations

import math
import zlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.models.incentive_award_ledger import (
    AWARD_STATUS_APPROVED,
    AWARD_STATUS_DENIED,
    AWARD_STATUS_GRANTED,
    AWARD_STATUS_PENDING,
    AWARD_STATUS_WITHDRAWN,
    CAP_CONSUMING_AWARD_STATUSES,
    EVIDENCE_STATE_EVIDENCED,
    EVIDENCE_STATE_UNVERIFIED,
    IncentiveAwardLedgerEntry,
)

_VALID_STATUSES = frozenset({
    AWARD_STATUS_APPROVED, AWARD_STATUS_GRANTED, AWARD_STATUS_PENDING,
    AWARD_STATUS_DENIED, AWARD_STATUS_WITHDRAWN,
})
_VALID_EVIDENCE_STATES = frozenset({EVIDENCE_STATE_EVIDENCED, EVIDENCE_STATE_UNVERIFIED})


def _advisory_lock_keys(production_company_identifier: str, award_period_year: int, program_slug: str) -> tuple[int, int]:
    """Two signed-int32 lock keys for pg_advisory_xact_lock(key1, key2) —
    Postgres's two-int32 advisory-lock form, deterministic and stable
    across processes/runs (crc32 of the same string always hashes the
    same way), so two callers naming the SAME (company, period, program)
    always contend for the SAME lock, and two callers naming a
    DIFFERENT triple essentially never collide (a genuine crc32 hash
    collision would only cause harmless extra contention between two
    unrelated triples, never an incorrect cap decision — the row query
    inside the lock is still exact-match filtered)."""
    composite = f"{production_company_identifier}\x1f{program_slug}"
    key1 = zlib.crc32(composite.encode("utf-8")) - 2_147_483_648  # -> signed int32 range
    key2 = int(award_period_year)
    return key1, key2


def _newest_row_per_event(rows: list[IncentiveAwardLedgerEntry]) -> list[IncentiveAwardLedgerEntry]:
    """Codex final three-program conservation repair (P0-NL-001, fifth
    pass): collapse an append-only status-transition history to exactly
    ONE (the newest, by created_at, tie-broken by id for determinism
    within the same instant) row per award_event_id — this is what makes
    an APPROVED -> GRANTED transition for one real award count once,
    never twice."""
    newest_by_event: dict[str, IncentiveAwardLedgerEntry] = {}
    for row in rows:
        current = newest_by_event.get(row.award_event_id)
        if current is None:
            newest_by_event[row.award_event_id] = row
            continue
        row_key = (row.created_at, str(row.id))
        current_key = (current.created_at, str(current.id))
        if row_key > current_key:
            newest_by_event[row.award_event_id] = row
    return list(newest_by_event.values())


async def company_period_program_award_summary(
    session: AsyncSession, *, production_company_identifier: str, award_period_year: int, program_slug: str,
    expected_currency: str | None = None,
) -> tuple[bool, float]:
    """Read-side: (has_any_rows, total_cap_consuming_native_amount) for
    this EXACT (company, period, program) triple. has_any_rows=False
    means no evidence has ever been recorded for this triple at all —
    the caller (canonical_evaluation._company_period_prior_award_facts)
    is responsible for distinguishing "no sibling production exists at
    all" (a real zero) from "a sibling exists but was never recorded
    here" (unresolved) — this function only reports the ledger's own
    real state, never guesses which case applies.

    Codex final four-row remediation (P0-NL-001, fourth pass): "evidence
    and status binding" — a row only CONSUMES the shared cap when BOTH
    its status is cap-consuming (APPROVED/GRANTED) AND its evidence_state
    is EVIDENCED (a real, sourced record, never a bare unverified claim).
    An UNVERIFIED row still counts toward has_any_rows (coverage was
    genuinely checked/recorded for this triple — the sibling is not
    silently unaccounted-for) but contributes $0 to the summed total
    until it is upgraded to EVIDENCED — exactly like a PENDING/DENIED
    row, never trusted to reduce another production's remaining cap on
    an unverified claim alone.

    Codex final three-program conservation repair (P0-NL-001, fifth
    pass): rows are FIRST collapsed to exactly the newest row per
    award_event_id (see _newest_row_per_event) — a status transition on
    one real award (e.g. APPROVED -> GRANTED) is counted once, never as
    two separate awards. `expected_currency`, when supplied, defensively
    excludes any row whose native_currency does not match from the sum
    (never numerically combined across currencies) — record_incentive_award
    already refuses to WRITE a mismatched-currency row in the first
    place, so this is defense in depth, not the primary guard."""
    rows = (await session.execute(
        select(IncentiveAwardLedgerEntry).where(
            IncentiveAwardLedgerEntry.production_company_identifier == production_company_identifier,
            IncentiveAwardLedgerEntry.award_period_year == award_period_year,
            IncentiveAwardLedgerEntry.program_slug == program_slug,
        )
    )).scalars().all()
    if not rows:
        return False, 0.0
    current = _newest_row_per_event(list(rows))
    total = sum(
        float(row.native_amount or 0.0) for row in current
        if row.status in CAP_CONSUMING_AWARD_STATUSES
        and row.evidence_state == EVIDENCE_STATE_EVIDENCED
        and (expected_currency is None or row.native_currency == expected_currency)
    )
    return True, round(total, 2)


async def record_incentive_award(
    session: AsyncSession, *,
    production_company_identifier: str,
    award_period_year: int,
    program_slug: str,
    award_event_id: str,
    status: str,
    native_currency: str,
    native_amount: float | None = None,
    evidence_state: str = EVIDENCE_STATE_UNVERIFIED,
    evidence_note: str | None = None,
    project_id=None,
    recorded_by_note: str | None = None,
) -> IncentiveAwardLedgerEntry:
    """Write-side: append one real, evidenced award-status row, under a
    real PostgreSQL transaction-scoped advisory lock keyed on the exact
    (company, period, program) triple — see this module's own docstring
    for the full concurrency guarantee. Append-only: a status change for
    the SAME award_event_id is always a NEW row (matching
    ProductionStructure/StructureCalculationResult's own append-only
    history convention), never an UPDATE of a prior row — but the
    READ-side (company_period_program_award_summary) collapses to the
    newest row per event before summing, so this never double-counts.

    award_event_id (Codex final three-program conservation repair,
    P0-NL-001, fifth pass): REQUIRED — a stable, caller-supplied
    identity for ONE real award decision (e.g. the producer's own
    application/reference number). Every row for this SAME event_id is
    a status transition of the SAME award, never a new one.

    Validation (all fail closed — raise ValueError, never silently
    coerce or clamp):
      - status must be a real, known award status.
      - evidence_state must be EVIDENCED or UNVERIFIED.
      - native_currency must equal the program's OWN registered cap
        currency (program_rate_rules.get_incentive_value_cap) when a
        cap is registered for this program_slug — a USD row can never
        be written against a EUR-denominated program.
      - native_amount, when provided, must be a finite, non-negative
        number.
      - CAP CONSERVATION: computed and enforced INSIDE the advisory
        lock, against the SAME program's registered
        IncentiveValueCapRule (when one exists) — the prospective total
        (every OTHER event's current EVIDENCED/cap-consuming amount,
        newest-row-per-event, PLUS this write's own amount if it would
        be cap-consuming) must not exceed the native cap. Idempotent:
        if the newest existing row for this EXACT award_event_id
        already has this EXACT status/currency/amount, the existing row
        is returned unchanged rather than inserting a duplicate.
    """
    from app.data.program_rate_rules import get_incentive_value_cap

    if status not in _VALID_STATUSES:
        raise ValueError(f"status {status!r} is not a recognized award status")
    if evidence_state not in _VALID_EVIDENCE_STATES:
        raise ValueError(f"evidence_state {evidence_state!r} is not a recognized evidence state")
    if native_amount is not None:
        if not isinstance(native_amount, (int, float)) or isinstance(native_amount, bool) or not math.isfinite(native_amount) or native_amount < 0:
            raise ValueError(f"native_amount {native_amount!r} is not a finite, non-negative number")
    if status in CAP_CONSUMING_AWARD_STATUSES:
        # A cap-consuming (APPROVED/GRANTED) award is a REAL grant of
        # money — it must carry a finite, strictly POSITIVE amount.
        # Missing or exactly-zero is not a real award record; a genuine
        # "no other productions" zero is expressed by the ABSENCE of any
        # cap-consuming row for the triple, never a $0 APPROVED row.
        if native_amount is None or native_amount <= 0:
            raise ValueError(
                f"a {status} award must carry a finite, strictly positive native_amount "
                f"(got {native_amount!r}) — zero/missing is not a real grant"
            )

    cap = get_incentive_value_cap(program_slug)
    if cap is not None and native_currency != cap.cap_currency:
        raise ValueError(
            f"native_currency {native_currency!r} does not match program {program_slug!r}'s own "
            f"registered cap currency {cap.cap_currency!r} — a mismatched-currency row can never "
            "be numerically combined with this program's other real awards."
        )

    key1, key2 = _advisory_lock_keys(production_company_identifier, award_period_year, program_slug)
    await session.execute(text("SELECT pg_advisory_xact_lock(:k1, :k2)"), {"k1": key1, "k2": key2})

    existing_rows = (await session.execute(
        select(IncentiveAwardLedgerEntry).where(
            IncentiveAwardLedgerEntry.production_company_identifier == production_company_identifier,
            IncentiveAwardLedgerEntry.award_period_year == award_period_year,
            IncentiveAwardLedgerEntry.program_slug == program_slug,
        )
    )).scalars().all()
    current = _newest_row_per_event(list(existing_rows))

    # Idempotency: an identical repeat of the newest row for this SAME
    # event is resolved to the existing row, never a duplicate insert.
    for row in current:
        if (row.award_event_id == award_event_id and row.status == status
                and row.native_currency == native_currency
                and (row.native_amount == native_amount
                     or (row.native_amount is None and native_amount is None))
                and row.evidence_state == evidence_state):
            return row

    this_write_consumes = status in CAP_CONSUMING_AWARD_STATUSES and evidence_state == EVIDENCE_STATE_EVIDENCED
    if cap is not None and this_write_consumes:
        other_events_total = sum(
            float(row.native_amount or 0.0) for row in current
            if row.award_event_id != award_event_id
            and row.status in CAP_CONSUMING_AWARD_STATUSES
            and row.evidence_state == EVIDENCE_STATE_EVIDENCED
        )
        prospective_total = round(other_events_total + float(native_amount or 0.0), 2)
        if prospective_total > cap.cap_native_amount:
            raise ValueError(
                f"recording this award would bring the total for "
                f"({production_company_identifier}, {award_period_year}, {program_slug}) to "
                f"{cap.cap_currency} {prospective_total:,.2f}, exceeding the real "
                f"{cap.cap_currency} {cap.cap_native_amount:,.2f} cap — rejected rather than "
                "silently over-committing the shared ceiling."
            )

    entry = IncentiveAwardLedgerEntry(
        production_company_identifier=production_company_identifier,
        award_period_year=award_period_year,
        program_slug=program_slug,
        award_event_id=award_event_id,
        status=status,
        native_currency=native_currency,
        native_amount=native_amount,
        evidence_state=evidence_state,
        evidence_note=evidence_note,
        project_id=project_id,
        recorded_by_note=recorded_by_note,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry
