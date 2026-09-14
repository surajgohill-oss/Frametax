"""
test_final_wiring_nl_company_period_conservation.py

Codex final wiring remediation (P0-NL-001, third pass) — independent
proof that the Netherlands company/award-period cap (EUR 3,000,000 per
production company per year) is now bound to REAL canonical identity
(Project.production_company_identifier / Project.target_shoot_year) and
conserved across REAL, separately-persisted canonical projects, never
two local variable names wrapped around one unbound helper call.

Codex's exact finding on the prior pass: "Independent reproducer: two
identical calls using the EUR2,000,000 prior-awards scalar both execute
and each return USD1,140,523.96. The pricing API accepts zero company-ID
and zero period fields... Independent tests must use two actual
canonical project-input identities, not two local names around identical
direct helper calls." This file creates real, separately-persisted
Project rows (through the ordinary generic ingestion path, the SAME
pattern test_generic_future_project_propagation.py already established
for a brand-new production) and evaluates each with evaluate_project(),
never a bare price_segment() call standing in for identity.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import fitz
import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import engine
from app.models.jurisdiction import Jurisdiction
from app.models.library_document import Document, DocumentVersion
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_fact import ProjectFact
from app.models.enums import ProjectFactSourceType
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures
from app.services.material_routing import ensure_current_budget_routed

#: A large, single-line Dutch production budget -- large enough that the
#: uncapped 35% incentive comfortably exceeds the EUR3,000,000 cap alone
#: (so cap conservation is actually observable), entirely production-
#: category spend (no travel/contingency noise).
_BUDGET_USD = 20_000_000.0


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
        target_shoot_year=award_period_year,
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


async def _teardown(db: AsyncSession, project_id) -> None:
    remaining = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if remaining is not None:
        await db.execute(sa_delete(Project).where(Project.id == project_id))
        await db.commit()


def _nl_entry(view: dict) -> dict | None:
    entries = view["structures"]["allocated_structures"]["structures"]
    return next(
        (e for e in entries if e.get("is_baseline") and e.get("program_slug") == "nl_film_production_incentive"),
        None,
    )


async def test_two_real_projects_same_company_same_year_jointly_conserve_cap(db: AsyncSession):
    company = f"kvk-{uuid.uuid4().hex[:10]}"
    year = 2027
    project_a = await _make_nl_project(db, label="NL COMPANY-YEAR A", company_identifier=company, award_period_year=year)
    project_b = await _make_nl_project(db, label="NL COMPANY-YEAR B", company_identifier=company, award_period_year=year)
    try:
        # Project A: first (and, at evaluation time, only) production on
        # file for this company/year -- a real, evidenced ZERO siblings
        # result, so the FULL EUR3,000,000-equivalent cap applies.
        await evaluate_project(db, project_a.id)
        view_a = await build_production_and_structures(db, project_a.id)
        entry_a = _nl_entry(view_a)
        assert entry_a is not None and entry_a["is_fully_priced"] is True
        cap_usd_a = entry_a["npc_with_adjustments_usd"]
        gross_a = _BUDGET_USD
        incentive_a = entry_a["selected_incentive_usd"]
        assert incentive_a == pytest.approx(3_421_571.87, abs=1.0), (
            f"Project A alone, no siblings on file, must price at the full EUR3m-equivalent "
            f"cap; observed {incentive_a}"
        )

        # Project B: the SAME company, the SAME award period -- a real
        # cross-project query must now find Project A's own persisted
        # award and reduce B's remaining cap accordingly. Literal
        # arithmetic: EUR3,000,000 - (incentive_a converted back to EUR)
        # ~= 0, since A alone already consumed the full cap.
        await evaluate_project(db, project_b.id)
        view_b = await build_production_and_structures(db, project_b.id)
        entry_b = _nl_entry(view_b)
        assert entry_b is not None and entry_b["is_fully_priced"] is True
        incentive_b = entry_b["selected_incentive_usd"]
        assert incentive_b == pytest.approx(0.0, abs=1.0), (
            f"Project B (same company/year, evaluated AFTER Project A already consumed the "
            f"full cap) must receive ~$0, never a second fresh EUR3,000,000-equivalent cap; "
            f"observed {incentive_b}"
        )
        # Joint total across both real, separately-persisted projects
        # must never exceed the single company-year cap.
        assert incentive_a + incentive_b <= 3_421_571.87 + 1.0, (
            f"joint total {incentive_a + incentive_b} exceeds the single company-year cap"
        )
    finally:
        await _teardown(db, project_a.id)
        await _teardown(db, project_b.id)


async def test_different_company_same_year_remains_isolated(db: AsyncSession):
    year = 2028
    project_a = await _make_nl_project(
        db, label="NL ISOLATION A", company_identifier=f"kvk-{uuid.uuid4().hex[:10]}", award_period_year=year,
    )
    project_c = await _make_nl_project(
        db, label="NL ISOLATION C", company_identifier=f"kvk-{uuid.uuid4().hex[:10]}", award_period_year=year,
    )
    try:
        await evaluate_project(db, project_a.id)
        view_a = await build_production_and_structures(db, project_a.id)
        incentive_a = _nl_entry(view_a)["selected_incentive_usd"]
        assert incentive_a == pytest.approx(3_421_571.87, abs=1.0)

        # A DIFFERENT company, same award period -- must be fully
        # isolated from A's own consumption; C also prices at the FULL
        # cap, never inheriting A's remaining-zero state.
        await evaluate_project(db, project_c.id)
        view_c = await build_production_and_structures(db, project_c.id)
        incentive_c = _nl_entry(view_c)["selected_incentive_usd"]
        assert incentive_c == pytest.approx(3_421_571.87, abs=1.0), (
            f"a DIFFERENT production company in the same award period must remain isolated "
            f"from company A's own consumption; observed {incentive_c}"
        )
    finally:
        await _teardown(db, project_a.id)
        await _teardown(db, project_c.id)


async def test_unknown_company_or_period_remains_conditional_non_priceable(db: AsyncSession):
    """A project with NO canonical company identity or award period on
    file must leave the NL company/period cap conditional/non-priceable
    -- never an affirmative zero (full cap) or an affirmative full cap
    without verification."""
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


# ── Pure, DB-free adverse cases against the resolver directly ───────────

def test_resolver_rejects_wrong_company_and_wrong_period_aggregates_directly():
    """Direct proof (no DB, literal arithmetic) that the resolver never
    trusts a caller-supplied scalar without BOTH identity_known and
    has_other_productions engine-evidenced -- the exact free-scalar
    defect this whole mechanism exists to close."""
    from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap
    from app.calculators.production_normalization import build_fx_context

    fx = build_fx_context()

    # Identity unknown at all -- even with a "helpful" caller-supplied
    # amount fact and a has_other_productions claim, the cap must fail
    # closed on the identity gate FIRST.
    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx,
        {"nl_nfpi_company_period_prior_awards_eur": 2_000_000.0},
        frozenset({"nl_nfpi_company_period_has_other_productions"}),
    )
    assert cap is None and unresolved is not None and "identity" in unresolved.lower()

    # Identity known, has_other_productions FALSE (never evidenced) --
    # correctly treated as "no claim", full cap, not an error.
    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx, {},
        frozenset({"nl_nfpi_company_period_identity_known"}),
    )
    assert unresolved is None and cap == pytest.approx(3_421_571.87, abs=0.01)

    # Identity known, has_other_productions TRUE, but no amount --
    # unresolved aggregate, must fail closed.
    cap, kind, basis, fx_err, unresolved = _resolve_incentive_dollar_cap(
        "nl_film_production_incentive", fx, {},
        frozenset({"nl_nfpi_company_period_identity_known", "nl_nfpi_company_period_has_other_productions"}),
    )
    assert cap is None and unresolved is not None
