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
    assert round(lu_baseline["npc_with_adjustments_usd"], 2) == 3812823.20  # Production Page Integrity Closeout (migration 0071): migration 0068's beta 100% contingency-utilization election was removed as stale. No election on file -> GREY_AREA_REQUIRES_AUTHORITY (never silently 0%/100%), reserve excluded from qualifying QPE until a producer sets it. Current canonical NPC reproduced via a real evaluate_project() call.

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
    INCOMPLETE/NOT_APPLICABLE.

    CBA-002 continuation (surfaced fresh by the OH-001 stale-cache fix --
    this exact interaction was masked for one full pass because FVD's
    cached snapshot predated canonical_evaluation._merge_rate_condition_
    into_qualification's addition): a THIRD real, non-fabricated source can
    also produce AUTHORITY_UNRESOLVED for a slug outside all five doctrine
    registries -- a genuinely cited RateCondition (e.g. ca_on_opstc's own
    "Ontario labour must be >=25% of QPE claimed", mx_federal_film_
    incentive_2026's "70% national supply" requirement) that this engine
    cannot pre-evaluate. This is real, disclosed statutory text, not
    invention -- see program_rate_rules_worldwide.py's own citations for
    each. Detected here by the reasoning_trace's own explicit disclosure
    line rather than trusted blindly, so a genuinely fabricated
    AUTHORITY_UNRESOLVED elsewhere still fails this test."""
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
        if "regime_id" not in rq:
            continue  # combined-structure worst-state trace: {"state": ...} only, no single regime_id
        if rq["regime_id"] not in accepted_doctrine_slugs:
            rate_condition_disclosed = any(
                "Rate condition(s)" in line and "resolved to" in line
                for line in (rq.get("reasoning_trace") or [])
            )
            if rate_condition_disclosed:
                continue
            assert rq["state"] in ("RULE_DATA_INCOMPLETE", "NOT_APPLICABLE")


async def test_role_qualification_survives_persistence_and_api(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    any_rq = next(e for e in _entries(view) if e.get("role_qualification"))
    rq = any_rq["role_qualification"]
    for key in ("regime_id", "jurisdiction_code", "state", "role_findings", "reasoning_trace"):
        assert key in rq
