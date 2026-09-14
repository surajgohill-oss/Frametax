"""
test_final_wiring_nl_company_period_conservation.py

Codex final four-row remediation (P0-NL-001, fourth pass) — independent
proof that the Netherlands company/award-period cap (EUR 3,000,000 per
production company per year) is now bound to a REAL, durable,
append-only incentive award ledger (app.models.incentive_award_ledger.
IncentiveAwardLedgerEntry / app.services.incentive_award_ledger_service),
never a StructureCalculationResult/ProductionStructure pseudo-ledger
summing the optimizer's own PRICED CANDIDATE estimates as if they were
real awards.

Codex's exact rejection of the prior (third) pass: "Do not read
StructureCalculationResult or any candidate/scenario output as a prior
award... Sibling existence with unknown award evidence remains
unresolved and no full cap is asserted." This file proves, against a
real PostgreSQL database and real, separately-persisted canonical
Project rows:

  1. A production with genuinely no sibling Project on file prices at
     the full company-period cap (a real, vacuous "alone" state).
  2. A production with a sibling Project on file but NO recorded ledger
     entry for that (company, period, program) triple is UNRESOLVED —
     never a silent full cap.
  3. Once a real ledger entry is recorded (an explicit, evidenced act —
     never auto-populated from optimizer output), the sibling's
     APPROVED/EVIDENCED native amount correctly reduces the remaining
     cap.
  4. A recorded DENIED (or PENDING/unevidenced-APPROVED) award is a
     real, evidenced ZERO consumption — genuinely distinct from the
     "no ledger row at all" unresolved case, yet numerically equal to
     the "alone" full-cap outcome (proving the two paths are distinct
     mechanisms that happen to agree on this particular figure).
  5. A different company, or a different award period, or a different
     program, is fully isolated from another company's/period's/
     program's recorded awards.
  6. Two REAL, concurrent async database sessions, each performing a
     genuine read-decide-write critical section against the SAME
     (company, period, program) triple, can never both walk away
     believing they consumed the full remaining cap — proven via
     PostgreSQL's own transaction-scoped advisory lock
     (pg_advisory_xact_lock), never a sequential local-variable stand-in.
"""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import fitz
import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.core.config import get_settings
from app.db.session import engine
from app.models.enums import ProjectFactSourceType
from app.models.incentive_award_ledger import (
    AWARD_STATUS_APPROVED,
    AWARD_STATUS_DENIED,
    AWARD_STATUS_GRANTED,
    AWARD_STATUS_PENDING,
    EVIDENCE_STATE_EVIDENCED,
    EVIDENCE_STATE_UNVERIFIED,
    IncentiveAwardLedgerEntry,
)
from app.models.jurisdiction import Jurisdiction
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_fact import ProjectFact
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures
from app.services.incentive_award_ledger_service import (
    _advisory_lock_keys,
    company_period_program_award_summary,
    record_incentive_award,
)
from app.services.material_routing import ensure_current_budget_routed

#: A large, single-line Dutch production budget -- large enough that the
#: uncapped 35% incentive comfortably exceeds the EUR3,000,000 cap alone
#: (so cap conservation is actually observable), entirely production-
#: category spend (no travel/contingency noise).
_BUDGET_USD = 20_000_000.0

#: The independently-established literal EUR3,000,000 -> USD conversion
#: figure this whole suite's prior passes already anchored on. Never
#: recomputed from the production helper under test -- an independent,
#: previously-verified oracle value.
_FULL_CAP_USD = 3_421_571.87


def _write_budget_pdf(path: Path, label: str) -> None:
    doc = fitz.open()
    doc.new_page().insert_text(
        (50, 50),
        f"{label}\nAccount\nDescription\nTotal\n2000\nPRODUCTION\n${_BUDGET_USD:,.0f}",
        fontsize=10,
    )
    doc.save(str(path))
    doc.close()


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def _make_nl_project(
    db: AsyncSession, *, label: str, company_identifier: str | None, award_period_year: int | None,
) -> Project:
    """A brand-new Dutch production created through the ordinary generic
    ingestion path (Organization -> Project -> budget Document/
    DocumentVersion on disk -> material_routing), home-jurisdictioned
    directly at NL (bypassing PDF-based jurisdiction inference, exactly
    as build_project_economic_inputs's own _resolve_home_jurisdiction
    docstring says is safe: "Never overrides an already-confirmed
    project.home_jurisdiction_id")."""
    nl = (await db.execute(select(Jurisdiction).where(Jurisdiction.code == "NL"))).scalars().first()
    assert nl is not None, "fixture assumption: NL jurisdiction is seeded"

    suffix = uuid.uuid4().hex[:8]
    org = Organization(name=f"NL Conservation Org {suffix}", slug=f"nl-conservation-{suffix}")
    db.add(org)
    await db.flush()

    project = Project(
        id=uuid.uuid4(), organization_id=org.id,
        title=f"NL Conservation Production {suffix}",
        home_jurisdiction_id=nl.id,
        production_company_identifier=company_identifier,
        # Codex final three-program conservation repair (P0-NL-001,
        # fifth pass): the real, explicit award_period_year column,
        # never target_shoot_year (a production-planning fact, not a
        # statement of the statutory award period).
        award_period_year=award_period_year,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    project_id = project.id

    settings = get_settings()
    storage_dir = Path(settings.LOCAL_STORAGE_PATH) / f"nl-conservation-{project_id}"
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = "NL Conservation Budget.pdf"
    _write_budget_pdf(storage_dir / filename, label)

    document = Document(id=uuid.uuid4(), project_id=project_id, category="budget", title=f"{project.title} — Budget")
    db.add(document)
    await db.flush()
    version = DocumentVersion(
        id=uuid.uuid4(), document_id=document.id, original_filename=filename,
        storage_path=f"nl-conservation-{project_id}/{filename}", is_current=True,
    )
    db.add(version)
    await db.flush()
    document.current_version_id = version.id
    await db.commit()

    await ensure_current_budget_routed(db, project_id)

    # The two real, already-accepted NL rate-eligibility facts (points/
    # independence test + format threshold) -- required for the 35% rate
    # tier to resolve at all, independent of the company/period cap
    # mechanism this test targets.
    for fact_key in ("nl_nfpi_points_independence_test_passed", "nl_nfpi_format_threshold_met"):
        db.add(ProjectFact(
            id=uuid.uuid4(), project_id=project_id,
            fact_key=f"evidenced_program_fact:{fact_key}",
            value="true", value_type="boolean",
            source_type=ProjectFactSourceType.USER_OVERRIDE,
        ))
    await db.commit()

    return project


async def _teardown(db: AsyncSession, *project_ids) -> None:
    for project_id in project_ids:
        remaining = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if remaining is not None:
            await db.execute(sa_delete(Project).where(Project.id == project_id))
    await db.commit()


async def _teardown_ledger(db: AsyncSession, company: str) -> None:
    await db.execute(sa_delete(IncentiveAwardLedgerEntry).where(
        IncentiveAwardLedgerEntry.production_company_identifier == company,
    ))
    await db.commit()


def _nl_entry(view: dict) -> dict | None:
    entries = view["structures"]["allocated_structures"]["structures"]
    return next(
        (e for e in entries if e.get("is_baseline") and e.get("program_slug") == "nl_film_production_incentive"),
        None,
    )


# ── 1. Genuinely alone: no sibling Project at all ──────────────────────

async def test_project_alone_no_siblings_prices_full_cap(db: AsyncSession):
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2031
    project = await _make_nl_project(db, label="NL ALONE", company_identifier=company, award_period_year=year)
    try:
        await evaluate_project(db, project.id)
        view = await build_production_and_structures(db, project.id)
        entry = _nl_entry(view)
        assert entry is not None and entry["is_fully_priced"] is True
        assert entry["selected_incentive_usd"] == pytest.approx(_FULL_CAP_USD, abs=1.0), (
            "a production with no sibling Project on file at all must price at the "
            f"full company-period cap; observed {entry['selected_incentive_usd']}"
        )
    finally:
        await _teardown(db, project.id)
        await _teardown_ledger(db, company)


# ── 2. Sibling Project exists, ledger has never been checked ──────────

async def test_sibling_project_exists_with_no_ledger_row_remains_unresolved(db: AsyncSession):
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2032
    project_a = await _make_nl_project(db, label="NL UNRESOLVED A", company_identifier=company, award_period_year=year)
    project_b = await _make_nl_project(db, label="NL UNRESOLVED B", company_identifier=company, award_period_year=year)
    try:
        # Project B now has a real sibling Project (A) on file, but the
        # incentive award ledger has NEVER been checked/recorded for
        # this (company, year, nl_film_production_incentive) triple —
        # this must be unresolved, never a silent full cap.
        await evaluate_project(db, project_b.id)
        view_b = await build_production_and_structures(db, project_b.id)
        entry_b = _nl_entry(view_b)
        assert entry_b is not None, "NL baseline candidate must still be constructed (disclosed, never dropped)"
        assert entry_b["is_fully_priced"] is False, (
            "a sibling Project existing with NO recorded ledger evidence must leave "
            "the company-period cap unresolved/non-priceable, never an affirmative "
            "full-cap price"
        )
    finally:
        await _teardown(db, project_a.id, project_b.id)
        await _teardown_ledger(db, company)


# ── 3. Recorded APPROVED+EVIDENCED award reduces the remaining cap ────

async def test_sibling_recorded_approved_evidenced_award_reduces_remaining_cap(db: AsyncSession):
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2033
    project_a = await _make_nl_project(db, label="NL CONSUME A", company_identifier=company, award_period_year=year)
    project_b = await _make_nl_project(db, label="NL CONSUME B", company_identifier=company, award_period_year=year)
    try:
        # An explicit, evidenced act recording project A's REAL award —
        # never auto-populated from A's own priced candidate structures.
        await record_incentive_award(
            db,
            production_company_identifier=company, award_period_year=year,
            program_slug="nl_film_production_incentive",
            award_event_id=f"evt-{uuid.uuid4().hex[:10]}",
            status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=1_200_000.0,
            evidence_state=EVIDENCE_STATE_EVIDENCED, evidence_note="test: real grant letter on file",
            project_id=project_a.id,
        )

        await evaluate_project(db, project_b.id)
        view_b = await build_production_and_structures(db, project_b.id)
        entry_b = _nl_entry(view_b)
        assert entry_b is not None and entry_b["is_fully_priced"] is True
        # Literal arithmetic (independent oracle, never the production
        # helper): remaining = EUR3,000,000 - EUR1,200,000 = EUR1,800,000
        # = 60% of the full cap -> 60% of the already-established full-cap
        # USD figure.
        expected_usd = round(_FULL_CAP_USD * 0.6, 2)
        assert entry_b["selected_incentive_usd"] == pytest.approx(expected_usd, abs=1.0), (
            f"remaining cap after a real EUR1,200,000 recorded award must price at "
            f"{expected_usd}; observed {entry_b['selected_incentive_usd']}"
        )
    finally:
        await _teardown(db, project_a.id, project_b.id)
        await _teardown_ledger(db, company)


# ── 4. Recorded DENIED award is a real evidenced zero, not unresolved ─

async def test_sibling_recorded_denied_award_is_evidenced_zero_not_unresolved(db: AsyncSession):
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2034
    project_a = await _make_nl_project(db, label="NL DENIED A", company_identifier=company, award_period_year=year)
    project_b = await _make_nl_project(db, label="NL DENIED B", company_identifier=company, award_period_year=year)
    try:
        await record_incentive_award(
            db,
            production_company_identifier=company, award_period_year=year,
            program_slug="nl_film_production_incentive",
            award_event_id=f"evt-{uuid.uuid4().hex[:10]}",
            status=AWARD_STATUS_DENIED, native_currency="EUR", native_amount=None,
            evidence_state=EVIDENCE_STATE_EVIDENCED, evidence_note="test: application denied, on file",
            project_id=project_a.id,
        )

        await evaluate_project(db, project_b.id)
        view_b = await build_production_and_structures(db, project_b.id)
        entry_b = _nl_entry(view_b)
        assert entry_b is not None and entry_b["is_fully_priced"] is True, (
            "a DENIED award record still means sibling coverage is genuinely COMPLETE "
            "(the ledger was checked; the sibling's status is known) -- this must "
            "price deterministically, never remain unresolved like the no-ledger-row case"
        )
        assert entry_b["selected_incentive_usd"] == pytest.approx(_FULL_CAP_USD, abs=1.0), (
            "a DENIED sibling award consumes $0 of the shared cap -- a real, "
            f"evidenced zero; observed {entry_b['selected_incentive_usd']}"
        )
    finally:
        await _teardown(db, project_a.id, project_b.id)
        await _teardown_ledger(db, company)


# ── 4b. An UNVERIFIED (unevidenced) APPROVED row never consumes cap ───

async def test_unverified_approved_award_never_consumes_cap(db: AsyncSession):
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2035
    project_a = await _make_nl_project(db, label="NL UNVERIFIED A", company_identifier=company, award_period_year=year)
    project_b = await _make_nl_project(db, label="NL UNVERIFIED B", company_identifier=company, award_period_year=year)
    try:
        # A claimed APPROVED award with NO real evidence on file yet --
        # coverage is checked (a row exists) but this unverified claim
        # must NOT reduce project B's remaining cap.
        await record_incentive_award(
            db,
            production_company_identifier=company, award_period_year=year,
            program_slug="nl_film_production_incentive",
            award_event_id=f"evt-{uuid.uuid4().hex[:10]}",
            status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=3_000_000.0,
            evidence_state=EVIDENCE_STATE_UNVERIFIED, evidence_note="test: unverified claim, no grant letter on file",
            project_id=project_a.id,
        )

        await evaluate_project(db, project_b.id)
        view_b = await build_production_and_structures(db, project_b.id)
        entry_b = _nl_entry(view_b)
        assert entry_b is not None and entry_b["is_fully_priced"] is True
        assert entry_b["selected_incentive_usd"] == pytest.approx(_FULL_CAP_USD, abs=1.0), (
            "an UNVERIFIED APPROVED claim must never reduce another production's "
            f"remaining cap; observed {entry_b['selected_incentive_usd']}"
        )
    finally:
        await _teardown(db, project_a.id, project_b.id)
        await _teardown_ledger(db, company)


# ── 5. Isolation: different company / different period / different program

async def test_different_company_same_year_remains_isolated(db: AsyncSession):
    year = 2036
    company_a = f"kvk-{uuid.uuid4().hex[:10]}"
    company_c = f"kvk-{uuid.uuid4().hex[:10]}"
    project_a = await _make_nl_project(db, label="NL ISOLATION A", company_identifier=company_a, award_period_year=year)
    project_c = await _make_nl_project(db, label="NL ISOLATION C", company_identifier=company_c, award_period_year=year)
    try:
        await record_incentive_award(
            db,
            production_company_identifier=company_a, award_period_year=year,
            program_slug="nl_film_production_incentive",
            award_event_id=f"evt-{uuid.uuid4().hex[:10]}",
            status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=3_000_000.0,
            evidence_state=EVIDENCE_STATE_EVIDENCED, project_id=project_a.id,
        )

        # A DIFFERENT production company, same award period -- no sibling
        # Project exists for company C at all, so C prices at the FULL
        # cap, entirely unaffected by company A's own recorded award.
        await evaluate_project(db, project_c.id)
        view_c = await build_production_and_structures(db, project_c.id)
        incentive_c = _nl_entry(view_c)["selected_incentive_usd"]
        assert incentive_c == pytest.approx(_FULL_CAP_USD, abs=1.0), (
            f"a DIFFERENT production company in the same award period must remain "
            f"isolated from company A's own recorded award; observed {incentive_c}"
        )
    finally:
        await _teardown(db, project_a.id, project_c.id)
        await _teardown_ledger(db, company_a)
        await _teardown_ledger(db, company_c)


async def test_wrong_period_isolation_at_ledger_service_level(db: AsyncSession):
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    await record_incentive_award(
        db, production_company_identifier=company, award_period_year=2040,
        program_slug="nl_film_production_incentive",
        award_event_id=f"evt-{uuid.uuid4().hex[:10]}",
        status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=3_000_000.0,
        evidence_state=EVIDENCE_STATE_EVIDENCED,
    )
    try:
        has_rows, total = await company_period_program_award_summary(
            db, production_company_identifier=company, award_period_year=2041,
            program_slug="nl_film_production_incentive",
        )
        assert has_rows is False and total == 0.0, (
            "a row recorded for award_period_year=2040 must never be visible to a "
            "query for award_period_year=2041 -- exact triple isolation"
        )
    finally:
        await _teardown_ledger(db, company)


async def test_wrong_program_isolation_at_ledger_service_level(db: AsyncSession):
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    await record_incentive_award(
        db, production_company_identifier=company, award_period_year=2040,
        program_slug="nl_film_production_incentive",
        award_event_id=f"evt-{uuid.uuid4().hex[:10]}",
        status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=3_000_000.0,
        evidence_state=EVIDENCE_STATE_EVIDENCED,
    )
    try:
        has_rows, total = await company_period_program_award_summary(
            db, production_company_identifier=company, award_period_year=2040,
            program_slug="some_other_program_slug",
        )
        assert has_rows is False and total == 0.0, (
            "a row recorded for nl_film_production_incentive must never be visible "
            "to a query for a different program_slug -- exact triple isolation"
        )
    finally:
        await _teardown_ledger(db, company)


async def test_wrong_company_isolation_at_ledger_service_level(db: AsyncSession):
    company_a = f"kvk-{uuid.uuid4().hex[:10]}"
    company_b = f"kvk-{uuid.uuid4().hex[:10]}"
    await record_incentive_award(
        db, production_company_identifier=company_a, award_period_year=2040,
        program_slug="nl_film_production_incentive",
        award_event_id=f"evt-{uuid.uuid4().hex[:10]}",
        status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=3_000_000.0,
        evidence_state=EVIDENCE_STATE_EVIDENCED,
    )
    try:
        has_rows, total = await company_period_program_award_summary(
            db, production_company_identifier=company_b, award_period_year=2040,
            program_slug="nl_film_production_incentive",
        )
        assert has_rows is False and total == 0.0, (
            "a row recorded for company A must never be visible to a query for "
            "company B -- exact triple isolation"
        )
    finally:
        await _teardown_ledger(db, company_a)


# ── 6. Unknown identity remains conditional/non-priceable ─────────────

async def test_unknown_company_or_period_remains_conditional_non_priceable(db: AsyncSession):
    project = await _make_nl_project(db, label="NL UNKNOWN IDENTITY", company_identifier=None, award_period_year=None)
    try:
        await evaluate_project(db, project.id)
        view = await build_production_and_structures(db, project.id)
        entries = view["structures"]["allocated_structures"]["structures"]
        nl_entry = next(
            (e for e in entries if e.get("is_baseline") and e.get("program_slug") == "nl_film_production_incentive"),
            None,
        )
        assert nl_entry is not None, "NL baseline candidate must still be constructed (disclosed, never dropped)"
        assert nl_entry["is_fully_priced"] is False, (
            "unknown company/period must leave the company-period cap conditional/"
            "non-priceable, never an affirmative full-cap price"
        )
    finally:
        await _teardown(db, project.id)


# ── 7. Evaluation order / repetition stability ─────────────────────────

async def test_repeated_evaluation_is_stable(db: AsyncSession):
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2037
    project_a = await _make_nl_project(db, label="NL STABLE A", company_identifier=company, award_period_year=year)
    project_b = await _make_nl_project(db, label="NL STABLE B", company_identifier=company, award_period_year=year)
    try:
        await record_incentive_award(
            db, production_company_identifier=company, award_period_year=year,
            program_slug="nl_film_production_incentive",
            award_event_id=f"evt-{uuid.uuid4().hex[:10]}",
            status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=1_500_000.0,
            evidence_state=EVIDENCE_STATE_EVIDENCED, project_id=project_a.id,
        )
        # Re-evaluating project B repeatedly (creating multiple
        # StructureCalculationResult candidate rows for B itself) must
        # never change the result -- the ledger, not accumulated
        # candidate history, is the sole source of the sibling amount.
        await evaluate_project(db, project_b.id)
        view_1 = await build_production_and_structures(db, project_b.id)
        incentive_1 = _nl_entry(view_1)["selected_incentive_usd"]

        await evaluate_project(db, project_b.id)
        view_2 = await build_production_and_structures(db, project_b.id)
        incentive_2 = _nl_entry(view_2)["selected_incentive_usd"]

        await evaluate_project(db, project_b.id)
        view_3 = await build_production_and_structures(db, project_b.id)
        incentive_3 = _nl_entry(view_3)["selected_incentive_usd"]

        assert incentive_1 == pytest.approx(incentive_2, abs=0.01) == pytest.approx(incentive_3, abs=0.01), (
            f"repeated evaluation of the SAME project must be stable; observed "
            f"{incentive_1}, {incentive_2}, {incentive_3}"
        )
        expected_usd = round(_FULL_CAP_USD * (1_500_000.0 / 3_000_000.0), 2)
        assert incentive_1 == pytest.approx(expected_usd, abs=1.0)
    finally:
        await _teardown(db, project_a.id, project_b.id)
        await _teardown_ledger(db, company)


async def test_reversed_evaluation_order_produces_symmetric_conservation(db: AsyncSession):
    """Evaluating B before A (reversed from every other test in this
    file) must reach the SAME joint-conservation outcome once both
    real awards are recorded -- proving the mechanism has no order
    dependency on which sibling was evaluated first."""
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2038
    project_a = await _make_nl_project(db, label="NL REVERSED A", company_identifier=company, award_period_year=year)
    project_b = await _make_nl_project(db, label="NL REVERSED B", company_identifier=company, award_period_year=year)
    try:
        # Record BOTH real awards up front (as if both were already
        # decided), then evaluate in reverse (B, then A).
        await record_incentive_award(
            db, production_company_identifier=company, award_period_year=year,
            program_slug="nl_film_production_incentive",
            award_event_id=f"evt-a-{uuid.uuid4().hex[:10]}",
            status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=1_000_000.0,
            evidence_state=EVIDENCE_STATE_EVIDENCED, project_id=project_a.id,
        )
        await record_incentive_award(
            db, production_company_identifier=company, award_period_year=year,
            program_slug="nl_film_production_incentive",
            award_event_id=f"evt-b-{uuid.uuid4().hex[:10]}",
            status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=500_000.0,
            evidence_state=EVIDENCE_STATE_EVIDENCED, project_id=project_b.id,
        )

        # Both A and B now see each other as a sibling with real ledger
        # coverage AND each other's own recorded award, plus their own
        # recorded row (the ledger reads by company/period/program, not
        # by "excluding self" -- each production's own real award is
        # part of the same shared triple's total, exactly as a real
        # incentive office would track it).
        await evaluate_project(db, project_b.id)
        view_b = await build_production_and_structures(db, project_b.id)
        incentive_b = _nl_entry(view_b)["selected_incentive_usd"]

        await evaluate_project(db, project_a.id)
        view_a = await build_production_and_structures(db, project_a.id)
        incentive_a = _nl_entry(view_a)["selected_incentive_usd"]

        # Literal arithmetic: total recorded = EUR1,500,000; remaining
        # for EACH is cap(EUR3,000,000) - total_recorded(EUR1,500,000)
        # = EUR1,500,000 = 50% of the full cap, symmetric regardless of
        # evaluation order (the recorded amounts are fixed facts, not a
        # sequential running deduction).
        expected_usd = round(_FULL_CAP_USD * 0.5, 2)
        assert incentive_a == pytest.approx(expected_usd, abs=1.0)
        assert incentive_b == pytest.approx(expected_usd, abs=1.0)
    finally:
        await _teardown(db, project_a.id, project_b.id)
        await _teardown_ledger(db, company)


# ── 8. Pure, DB-free adverse cases against the resolver directly ───────

def test_resolver_rejects_unknown_identity_directly():
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
    from app.calculators.production_normalization import build_fx_context

    fx = build_fx_context()
    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx,
        {"nl_nfpi_company_period_prior_awards_eur": 2_000_000.0},
        frozenset({
            "nl_nfpi_company_period_has_other_productions",
            "nl_nfpi_company_period_sibling_coverage_complete",
        }),
    )
    assert cap is None and unresolved is not None and "identity" in unresolved.lower(), (
        "identity unknown must fail closed FIRST, even with a 'helpful' caller-"
        "supplied amount fact and every other fact evidenced"
    )


def test_resolver_vacuous_coverage_with_identity_known_prices_full_cap_directly():
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
    from app.calculators.production_normalization import build_fx_context

    fx = build_fx_context()
    # Identity known, coverage explicitly confirmed complete (the
    # vacuous "no siblings at all" case), has_other_productions never
    # evidenced -- correctly treated as a real "no claim", full cap.
    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx, {},
        frozenset({
            "nl_nfpi_company_period_identity_known",
            "nl_nfpi_company_period_sibling_coverage_complete",
        }),
    )
    assert unresolved is None and cap == pytest.approx(_FULL_CAP_USD, abs=0.01)


def test_resolver_identity_known_but_coverage_incomplete_is_unresolved_directly():
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
    from app.calculators.production_normalization import build_fx_context

    fx = build_fx_context()
    # Identity known, but sibling_coverage_complete NOT evidenced (the
    # NEW gate this pass adds) -- must fail closed as unresolved, never
    # silently default to the full cap.
    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx, {},
        frozenset({"nl_nfpi_company_period_identity_known"}),
    )
    assert cap is None and unresolved is not None and "sibling" in unresolved.lower(), (
        "identity known but sibling coverage NOT confirmed complete must be "
        "unresolved -- the exact defect Codex named ('sibling existence with "
        "unknown award evidence remains unresolved')"
    )


def test_resolver_evidenced_zero_after_coverage_confirmed_prices_full_cap_directly():
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
    from app.calculators.production_normalization import build_fx_context

    fx = build_fx_context()
    # Coverage confirmed complete AND has_other_productions evidenced
    # with an explicit amount of EUR0.00 (a real evidenced zero, e.g.
    # every sibling award was DENIED) -- must price the full cap, via a
    # DIFFERENT path than the vacuous-coverage case above, landing on
    # the same number only because the recorded consumption is zero.
    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx,
        {"nl_nfpi_company_period_prior_awards_eur": 0.0},
        frozenset({
            "nl_nfpi_company_period_identity_known",
            "nl_nfpi_company_period_sibling_coverage_complete",
            "nl_nfpi_company_period_has_other_productions",
        }),
    )
    assert unresolved is None and cap == pytest.approx(_FULL_CAP_USD, abs=0.01)


def test_resolver_rejects_negative_and_over_cap_aggregates_directly():
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
    from app.calculators.production_normalization import build_fx_context

    fx = build_fx_context()
    base_evidenced = frozenset({
        "nl_nfpi_company_period_identity_known",
        "nl_nfpi_company_period_sibling_coverage_complete",
        "nl_nfpi_company_period_has_other_productions",
    })

    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx,
        {"nl_nfpi_company_period_prior_awards_eur": -100.0}, base_evidenced,
    )
    assert cap is None and unresolved is not None, "a negative aggregate must be rejected, never clamped to 0"

    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx,
        {"nl_nfpi_company_period_prior_awards_eur": 3_000_000.01}, base_evidenced,
    )
    assert cap is None and unresolved is not None, "an aggregate exceeding the native cap must be rejected"

    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx,
        {"nl_nfpi_company_period_prior_awards_eur": float("nan")}, base_evidenced,
    )
    assert cap is None and unresolved is not None, "a non-finite aggregate must be rejected"

    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx, {}, base_evidenced,
    )
    assert cap is None and unresolved is not None, (
        "has_other_productions evidenced with NO amount at all must fail closed, "
        "never treated as zero"
    )


# ── 9. Real concurrency: two genuine async DB sessions, PUBLIC writer ──
# Codex final three-program conservation repair (P0-NL-001, fifth pass):
# "Claude's prior concurrency test bypassed the public writer and
# implemented its own safe read-decide-write sequence." This section
# calls record_incentive_award() ITSELF, from two real, independent,
# concurrent AsyncSession connections -- proving the PUBLIC writer's own
# advisory-locked cap enforcement (not a test-local reimplementation of
# it) is what prevents the cap from being exceeded.

async def _public_writer_full_award(company: str, year: int, program: str, event_id: str, amount: float) -> IncentiveAwardLedgerEntry | Exception:
    """Calls the REAL, PUBLIC record_incentive_award() from its OWN,
    independent AsyncSession/connection -- a genuine second database
    session, never a shared session. Returns the written entry on
    success or the caught exception on rejection (so both concurrent
    outcomes can be inspected without one coroutine's exception
    cancelling the other via asyncio.gather)."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            return await record_incentive_award(
                session,
                production_company_identifier=company, award_period_year=year, program_slug=program,
                award_event_id=event_id,
                status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=amount,
                evidence_state=EVIDENCE_STATE_EVIDENCED, evidence_note="concurrency test — public writer",
            )
        except Exception as exc:  # noqa: BLE001 - deliberately captured, not re-raised, for gather()
            return exc


async def test_two_concurrent_public_writer_sessions_cannot_exceed_cap(db: AsyncSession):
    """Two REAL, independent, concurrent calls to the PUBLIC
    record_incentive_award() for the SAME triple, each claiming the
    FULL EUR3,000,000 cap as a DISTINCT award event. Without the public
    writer's own real read-decide-write cap enforcement (inside the
    advisory lock), both would commit and the real ledger total would
    reach EUR6,000,000 — exactly Codex's own reproduced defect. With the
    fix, the lock serializes the two calls; whichever commits SECOND
    must see the first's already-committed EUR3,000,000 and reject
    itself (its own prospective total, EUR6,000,000, exceeds the cap)."""
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2039
    program = "nl_film_production_incentive"
    cap_native = 3_000_000.0
    try:
        result_1, result_2 = await asyncio.gather(
            _public_writer_full_award(company, year, program, f"evt-race-1-{uuid.uuid4().hex[:6]}", cap_native),
            _public_writer_full_award(company, year, program, f"evt-race-2-{uuid.uuid4().hex[:6]}", cap_native),
        )
        outcomes = [result_1, result_2]
        successes = [r for r in outcomes if isinstance(r, IncentiveAwardLedgerEntry)]
        rejections = [r for r in outcomes if isinstance(r, Exception)]
        assert len(successes) == 1 and len(rejections) == 1, (
            f"exactly ONE of two concurrent EUR3,000,000 claims for the SAME cap must "
            f"succeed and the other must be rejected by the public writer's own cap "
            f"enforcement; observed successes={len(successes)} rejections={len(rejections)} "
            f"({outcomes!r})"
        )
        assert "exceed" in str(rejections[0]).lower() or "cap" in str(rejections[0]).lower()

        # Independent verification: the REAL total now on file for this
        # triple, read through the SAME public summary function, must
        # equal exactly the cap -- never double-booked.
        _has_rows, total = await company_period_program_award_summary(
            db, production_company_identifier=company, award_period_year=year, program_slug=program,
        )
        assert total == pytest.approx(cap_native, abs=0.01), (
            f"the real, committed ledger total for this triple must equal the shared cap "
            f"exactly ({cap_native:,.2f}), never exceed it; observed {total}"
        )
    finally:
        await _teardown_ledger(db, company)


async def test_approved_to_granted_transition_counts_once():
    """Codex's exact finding: 'APPROVED -> GRANTED can count one award
    twice.' A single real award's status transition (recorded as a NEW
    append-only row, same award_event_id) must be summed as ONE award,
    never two."""
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2050
    event_id = f"evt-transition-{uuid.uuid4().hex[:8]}"
    async with AsyncSession(engine, expire_on_commit=False) as db:
        try:
            await record_incentive_award(
                db, production_company_identifier=company, award_period_year=year,
                program_slug="nl_film_production_incentive", award_event_id=event_id,
                status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=2_000_000.0,
                evidence_state=EVIDENCE_STATE_EVIDENCED,
            )
            await record_incentive_award(
                db, production_company_identifier=company, award_period_year=year,
                program_slug="nl_film_production_incentive", award_event_id=event_id,
                status=AWARD_STATUS_GRANTED, native_currency="EUR", native_amount=2_000_000.0,
                evidence_state=EVIDENCE_STATE_EVIDENCED,
            )
            _has_rows, total = await company_period_program_award_summary(
                db, production_company_identifier=company, award_period_year=year,
                program_slug="nl_film_production_incentive",
            )
            assert total == pytest.approx(2_000_000.0, abs=0.01), (
                f"one real award's APPROVED -> GRANTED transition (same award_event_id) must "
                f"sum to EUR2,000,000 once, never EUR4,000,000; observed {total}"
            )

            # A genuinely SECOND, distinct award (different event_id) for
            # the SAME triple correctly adds on top.
            await record_incentive_award(
                db, production_company_identifier=company, award_period_year=year,
                program_slug="nl_film_production_incentive", award_event_id=f"evt-second-{uuid.uuid4().hex[:8]}",
                status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=500_000.0,
                evidence_state=EVIDENCE_STATE_EVIDENCED,
            )
            _has_rows, total_2 = await company_period_program_award_summary(
                db, production_company_identifier=company, award_period_year=year,
                program_slug="nl_film_production_incentive",
            )
            assert total_2 == pytest.approx(2_500_000.0, abs=0.01)
        finally:
            await _teardown_ledger(db, company)


async def test_duplicate_award_event_insertion_is_idempotent():
    """Codex requirement: 'Duplicate award-event insertion is rejected
    or idempotently resolved.' An identical repeat of the newest row for
    the SAME award_event_id must not create a second row / inflate the
    total."""
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2051
    event_id = f"evt-dup-{uuid.uuid4().hex[:8]}"
    async with AsyncSession(engine, expire_on_commit=False) as db:
        try:
            for _ in range(3):
                await record_incentive_award(
                    db, production_company_identifier=company, award_period_year=year,
                    program_slug="nl_film_production_incentive", award_event_id=event_id,
                    status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=1_000_000.0,
                    evidence_state=EVIDENCE_STATE_EVIDENCED,
                )
            _has_rows, total = await company_period_program_award_summary(
                db, production_company_identifier=company, award_period_year=year,
                program_slug="nl_film_production_incentive",
            )
            assert total == pytest.approx(1_000_000.0, abs=0.01), (
                f"three identical inserts for the SAME award_event_id must never inflate the "
                f"total beyond the one real award's amount; observed {total}"
            )
            row_count = (await db.execute(
                select(IncentiveAwardLedgerEntry).where(
                    IncentiveAwardLedgerEntry.production_company_identifier == company,
                    IncentiveAwardLedgerEntry.award_period_year == year,
                    IncentiveAwardLedgerEntry.award_event_id == event_id,
                )
            )).scalars().all()
            assert len(row_count) == 1, (
                f"an identical repeat of the newest row for one award_event_id must be resolved "
                f"idempotently (no duplicate row), observed {len(row_count)} rows"
            )
        finally:
            await _teardown_ledger(db, company)


async def test_wrong_currency_rejected():
    """Codex's exact finding: 'A USD row is numerically added as though
    it were EUR.' A USD-denominated write against nl_film_production_incentive
    (a EUR-capped program) must be REJECTED at write time, never accepted
    into the ledger at all."""
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    async with AsyncSession(engine, expire_on_commit=False) as db:
        try:
            with pytest.raises(ValueError, match="(?i)currency"):
                await record_incentive_award(
                    db, production_company_identifier=company, award_period_year=2052,
                    program_slug="nl_film_production_incentive", award_event_id=f"evt-usd-{uuid.uuid4().hex[:8]}",
                    status=AWARD_STATUS_APPROVED, native_currency="USD", native_amount=1_000_000.0,
                    evidence_state=EVIDENCE_STATE_EVIDENCED,
                )
            _has_rows, total = await company_period_program_award_summary(
                db, production_company_identifier=company, award_period_year=2052,
                program_slug="nl_film_production_incentive",
            )
            assert _has_rows is False and total == 0.0, "a rejected write must leave no trace in the ledger"
        finally:
            await _teardown_ledger(db, company)


async def test_nonfinite_zero_and_negative_amounts_rejected():
    """Codex requirement: 'NaN, infinity, zero and negative amounts are
    rejected.' An APPROVED/GRANTED award is a real grant of money — it
    must carry a finite, strictly positive amount."""
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    async with AsyncSession(engine, expire_on_commit=False) as db:
        try:
            for bad_amount in (float("nan"), float("inf"), float("-inf"), 0.0, -1.0):
                with pytest.raises(ValueError):
                    await record_incentive_award(
                        db, production_company_identifier=company, award_period_year=2053,
                        program_slug="nl_film_production_incentive",
                        award_event_id=f"evt-bad-{uuid.uuid4().hex[:8]}",
                        status=AWARD_STATUS_APPROVED, native_currency="EUR", native_amount=bad_amount,
                        evidence_state=EVIDENCE_STATE_EVIDENCED,
                    )
            _has_rows, total = await company_period_program_award_summary(
                db, production_company_identifier=company, award_period_year=2053,
                program_slug="nl_film_production_incentive",
            )
            assert _has_rows is False and total == 0.0, "every rejected write must leave no trace in the ledger"
        finally:
            await _teardown_ledger(db, company)


async def test_missing_award_period_fails_closed(db: AsyncSession):
    """A project with a real company identity but NO explicit
    award_period_year on file must leave the company-period cap
    conditional/non-priceable — never inferred from target_shoot_year
    (removed) or defaulted to any value."""
    project = await _make_nl_project(
        db, label="NL MISSING PERIOD", company_identifier=f"kvk-{uuid.uuid4().hex[:10]}", award_period_year=None,
    )
    try:
        await evaluate_project(db, project.id)
        view = await build_production_and_structures(db, project.id)
        entries = view["structures"]["allocated_structures"]["structures"]
        nl_entry = next(
            (e for e in entries if e.get("is_baseline") and e.get("program_slug") == "nl_film_production_incentive"),
            None,
        )
        assert nl_entry is not None
        assert nl_entry["is_fully_priced"] is False, (
            "a real company identity with NO explicit award_period_year must remain "
            "conditional/non-priceable, never inferred from any other date field"
        )
    finally:
        await _teardown(db, project.id)
