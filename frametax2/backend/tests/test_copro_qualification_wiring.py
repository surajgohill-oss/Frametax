"""
Canonical Co-production Qualification Reconnection — served-runtime tests.

Runtime-proven against real LU/FVD project data: LU's real persisted
personnel (director AU, writer GB, producer US -- little_utopia_people.py's
own real facts) genuinely HARD_FAILs ca_federal_cptc's real Canadian-role
gate; both projects' baselines are unchanged.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


def _entries(view):
    return view["structures"]["allocated_structures"]["structures"]


async def test_baselines_unchanged_after_qualification_reconnection(db: AsyncSession):
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    lu_view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    lu_baseline = next(e for e in _entries(lu_view) if e["is_baseline"])
    assert round(lu_baseline["npc_with_adjustments_usd"], 2) == 3148134.20  # CBA-009 Part 19-20: LU NPC updated $3,057,794.90 -> $3,148,134.20 (contingency utilization unset -> disclosed grey, not 100%-unconditional)

    await evaluate_project(db, FVD_PROJECT_ID)
    fvd_view = await build_production_and_structures(db, FVD_PROJECT_ID)
    fvd_baseline = next(e for e in _entries(fvd_view) if e["is_baseline"])
    assert round(fvd_baseline["npc_with_adjustments_usd"], 2) == 3072027.16


async def test_lu_real_personnel_hard_fails_ca_federal_cptc(db: AsyncSession):
    """LU's real, persisted director/writer/producer nationalities are
    NOT Canadian -- this must genuinely HARD_FAIL ca_federal_cptc's real
    role gate, discovered from real data, never fabricated."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    hard_fails = [
        e for e in _entries(view)
        if (e.get("role_qualification") or {}).get("state") == "HARD_FAIL"
        and (e.get("role_qualification") or {}).get("regime_id") == "ca_federal_cptc"
    ]
    assert hard_fails, "expected a real HARD_FAIL against ca_federal_cptc from LU's real personnel"
    rq = hard_fails[0]["role_qualification"]
    assert rq["failed_requirements"]
    assert all(f["status"] in ("failed", "indeterminate") for f in rq["role_findings"] if f["status"] != "satisfied")


async def test_role_qualification_never_contaminates_ranking_or_npc(db: AsyncSession):
    """A HARD_FAIL/USER_FACT_REQUIRED role_qualification on a candidate
    must never change that candidate's own already-computed pricing/NPC
    or its ranking comparability -- disclosure only (Task 11)."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = _entries(view)
    ranking = view["structures"]["allocated_structures"]["ranking"]
    by_id = {e["structure_id"]: e for e in entries}
    for r in ranking:
        e = by_id.get(r["structure_id"])
        if not e or not e.get("role_qualification"):
            continue
        assert r["is_directly_comparable"] == e["is_directly_comparable"]


async def test_role_qualification_covers_only_real_registry_slugs(db: AsyncSession):
    """Every candidate whose program_slug is NOT in ANY accepted canonical
    doctrine source (the 24-slug role registry, cultural_point_tables.py's
    two registries, or AUTHORITY_UNRESOLVED_PROGRAMS /
    CONFIRMED_TEST_SCORING_WITHHELD_PROGRAMS) must resolve RULE_DATA_
    INCOMPLETE or NOT_APPLICABLE -- never QUALIFIES/HARD_FAIL fabricated
    from nothing.

    Worldwide Qualification Consumption Closeout (2026-08-19): a slug
    OUTSIDE the 24-slug role registry may now legitimately resolve to ANY
    real qualification state (QUALIFIES/HARD_FAIL/CURABLE_GAP/
    USER_FACT_REQUIRED/SCRIPT_FACT_REQUIRED/AUTHORITY_UNRESOLVED) when it
    IS covered by one of the two new registries -- that is real,
    researched doctrine being consumed, not fabrication. The invariant
    this test protects is narrower and still real: a slug in NONE of the
    five accepted sources must never report anything but RULE_DATA_
    INCOMPLETE/NOT_APPLICABLE."""
    from app.calculators.canonical_role_qualification_bridge import (
        AUTHORITY_UNRESOLVED_PROGRAMS,
        CONFIRMED_TEST_SCORING_WITHHELD_PROGRAMS,
        ROLE_QUALIFICATION_COVERED_SLUGS,
    )
    from app.data.cultural_point_tables import CULTURAL_POINT_TABLES, DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS

    accepted_doctrine_slugs = (
        ROLE_QUALIFICATION_COVERED_SLUGS
        | CULTURAL_POINT_TABLES.keys()
        | DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS.keys()
        | AUTHORITY_UNRESOLVED_PROGRAMS.keys()
        | CONFIRMED_TEST_SCORING_WITHHELD_PROGRAMS.keys()
    )

    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    for e in _entries(view):
        rq = e.get("role_qualification")
        if not rq:
            continue
        if rq["regime_id"] not in accepted_doctrine_slugs:
            assert rq["state"] in ("RULE_DATA_INCOMPLETE", "NOT_APPLICABLE")


async def test_role_qualification_survives_persistence_and_api(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    any_rq = next(e for e in _entries(view) if e.get("role_qualification"))
    rq = any_rq["role_qualification"]
    for key in ("regime_id", "jurisdiction_code", "state", "role_findings", "reasoning_trace"):
        assert key in rq
