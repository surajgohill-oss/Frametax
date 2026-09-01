"""
test_canonical_economics_integrity_repair.py

Regression coverage for the CineGlobe economics + wiring integrity repair.

Each test below pins one ROOT CAUSE from the reconciliation/external-control
audits of bb4b6a2, so a later change cannot silently reopen it:

  * CLUSTER 1  -- AUTHORITY must fail closed. An
    AUTHORITY_UNRESOLVED_NON_PRICEABLE program contributes no incentive, NPC,
    stack or ranking value (PROJECT_RULES.md final authority-safety gate),
    while remaining DISCOVERED and disclosed -- withheld, never erased.

  * CLUSTER 13 -- READ PATH MUST BE PURE. A GET/read may reconstruct the
    canonical input fingerprint, but must produce ZERO inserts, ZERO updates,
    ZERO project-fact mutations and ZERO commits.

These walk the LIVE registry and the LIVE database; none asserts a
hard-coded historical economic total as if it were production law.
"""
from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard
from app.db.session import engine
from app.models.project import Project
from app.models.project_fact import ProjectFact
from app.services.canonical_production_view import build_production_and_structures
from app.services.project_workspace_view import build_project_workspace_view

LIPS_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"

#: The read-purity control that actually EXERCISES the recovery path.
#: Lips and FVD already have a routed BudgetDocument and a resolved home
#: jurisdiction, so nothing would fire for them and a purity assertion on
#: those two alone would pass vacuously. "All My Friends Are Dead" has a
#: committed budget document but NO BudgetDocument row and NO
#: home_jurisdiction_id, so the pre-repair read path reached
#: ensure_current_budget_routed and committed a BudgetDocument plus 29
#: BudgetLineItems on a GET. That is the regression this guards.
UNROUTED_PROJECT_ID = "e3f50d06-68c5-4d36-8b3a-e1f87e5c7a44"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── CLUSTER 1 — authority fails closed ───────────────────────────────────

def test_unresolved_authority_is_a_blocking_state():
    """The registry-level gate. NON_PRICEABLE is the disposition, so it must
    block deterministic economics."""
    from app.data.authority_coverage_registry import BLOCKING_STATES

    assert "AUTHORITY_UNRESOLVED_NON_PRICEABLE" in BLOCKING_STATES


def test_every_authority_unresolved_program_is_barred_from_economics():
    from app.data.authority_coverage_registry import (
        COVERAGE_REGISTRY,
        blocks_economic_candidacy,
    )

    unresolved = [
        slug for slug, rec in COVERAGE_REGISTRY.items()
        if rec.state == "AUTHORITY_UNRESOLVED_NON_PRICEABLE"
    ]
    assert unresolved, "expected real authority-unresolved programs in the registry"
    for slug in unresolved:
        assert blocks_economic_candidacy(slug), f"{slug} still economically priceable"


def test_authority_unresolved_program_cannot_price_via_direct_price_segment():
    """The route that bypasses discovery entirely must also fail closed, and
    must still ALLOCATE and DISCLOSE the segment rather than erase it."""
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind
    from app.data.authority_coverage_registry import COVERAGE_REGISTRY

    slug = next(
        s for s, rec in COVERAGE_REGISTRY.items()
        if rec.state == "AUTHORITY_UNRESOLVED_NON_PRICEABLE"
    )
    alloc = AccountAllocation(
        account_code="2000", description="Production spend",
        amount_usd=5_000_000.0, component="production", jurisdiction_code="XX",
        assignment_kind=AssignmentKind.FIXED,
        rationale="authority fail-closed probe",
        governing_decision="cineglobe-economics-integrity-repair",
    )
    seg = price_segment(
        jurisdiction_code="XX", program_slug=slug, allocations=[alloc],
        spend_category_by_code={"2000": "production"},
        offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=5_000_000.0,
    )
    assert seg.executable is False
    assert seg.blockers, "a withheld segment must explain itself"
    # Withheld, not erased: the spend is still located and disclosed.
    assert seg.allocated_usd == pytest.approx(5_000_000.0)


async def test_authority_unresolved_program_is_served_but_unpriced(db: AsyncSession):
    """End to end, on a real project: Manitoba is authority-unresolved, so it
    must appear in the served universe carrying its authority reason and
    contribute no deterministic incentive."""
    view = await build_production_and_structures(db, LIPS_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]

    mb = [e for e in entries if e["primary_jurisdiction"] == "CA-MB"]
    assert mb, "CA-MB must remain discovered and disclosed, never erased"
    for entry in mb:
        assert entry["is_fully_priced"] is False
        assert not entry.get("selected_incentive_usd")


# ── CLUSTER 13 — the read path must be pure ──────────────────────────────

async def _mutation_snapshot(session: AsyncSession) -> dict:
    """Everything a read was previously able to mutate."""
    facts = (await session.execute(
        select(ProjectFact.id, ProjectFact.value, ProjectFact.fact_key)
    )).all()
    homes = (await session.execute(
        select(Project.id, Project.home_jurisdiction_id)
    )).all()
    counts = {}
    for table in ("project_facts", "budget_documents", "budget_line_items",
                  "structure_calculation_results", "production_structures"):
        counts[table] = (await session.execute(
            select(func.count()).select_from(__import__("sqlalchemy").text(table))
        )).scalar()
    return {
        "facts": sorted((str(f[0]), f[1], f[2]) for f in facts),
        "homes": sorted((str(h[0]), str(h[1])) for h in homes),
        "counts": counts,
    }


@pytest.mark.parametrize(
    "project_id", [LIPS_PROJECT_ID, FVD_PROJECT_ID, UNROUTED_PROJECT_ID]
)
async def test_production_view_get_performs_zero_writes(db: AsyncSession, project_id):
    before = await _mutation_snapshot(db)
    try:
        await build_production_and_structures(db, project_id)
    except Exception:
        # A project with no priceable inputs may legitimately raise or
        # report blockers. Purity is asserted either way -- a read must not
        # mutate even on the failure path.
        await db.rollback()
    after = await _mutation_snapshot(db)

    assert after["counts"] == before["counts"], (
        "a GET inserted or deleted rows: " f"{before['counts']} -> {after['counts']}"
    )
    assert after["facts"] == before["facts"], "a GET mutated ProjectFact state"
    assert after["homes"] == before["homes"], "a GET mutated Project.home_jurisdiction_id"


@pytest.mark.parametrize(
    "project_id", [LIPS_PROJECT_ID, FVD_PROJECT_ID, UNROUTED_PROJECT_ID]
)
async def test_workspace_view_get_performs_zero_writes(db: AsyncSession, project_id):
    before = await _mutation_snapshot(db)
    try:
        await build_project_workspace_view(db, project_id)
    except Exception:
        await db.rollback()
    after = await _mutation_snapshot(db)

    assert after["counts"] == before["counts"], (
        "a GET inserted or deleted rows: " f"{before['counts']} -> {after['counts']}"
    )
    assert after["facts"] == before["facts"], "a GET mutated ProjectFact state"
    assert after["homes"] == before["homes"], "a GET mutated Project.home_jurisdiction_id"


def test_read_only_builder_never_reaches_write_capable_recovery():
    """Structural guard: the two GET builders must call the economic-input
    builder in read-only mode. A future edit that drops the flag reopens the
    exact regression bb4b6a2 introduced."""
    import inspect

    from app.services import canonical_production_view, project_workspace_view

    for module in (canonical_production_view, project_workspace_view):
        src = inspect.getsource(module)
        assert "build_project_economic_inputs(session, project.id, read_only=True)" in src, (
            f"{module.__name__} must build economic inputs read-only on a GET"
        )
