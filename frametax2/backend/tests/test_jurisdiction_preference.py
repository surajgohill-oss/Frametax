"""
Consolidated UI/ingestion/permission closeout (2026-09-03), Batch 6 —
generic PROJECT-LEVEL candidate-jurisdiction inclusion/exclusion.

Read/idempotent against the real F#K Valentine's Day project row (same
precedent as test_canonical_evaluation.py) — evaluate_project is
idempotent per input fingerprint, and this file cleans up any
jurisdiction_preference ProjectFact rows it creates.

REGRESSION THIS FILE EXISTS TO CATCH (a real bug found and fixed while
building this feature, not hypothetical): _compute_fingerprint() has
THREE independent call sites — evaluate_project() (canonical_evaluation.
py), build_production_and_structures() (canonical_production_view.py),
and the equivalent reader in project_workspace_view.py. Adding
excluded_jurisdiction_codes as a fingerprint input and wiring it into
ONLY the first call site made evaluate_project() persist rows under a
NEW fingerprint the moment any exclusion was on file, while the other
two readers kept computing the OLD (excluded_jurisdiction_codes=None)
fingerprint — their row-selection query then matched nothing, and the
served production/structures payload silently rendered completely
empty (jurisdiction_code=null, structures=[]) for any project with an
exclusion set. Confirmed live before the fix; the fix was to fetch and
pass excluded_jurisdiction_codes at all three sites identically.
"""
from __future__ import annotations

import pytest
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.project_fact import ProjectFact
from app.services.canonical_evaluation import (
    JURISDICTION_PREFERENCE_FACT_PREFIX,
    _excluded_jurisdiction_codes,
    evaluate_project,
)
from app.services.canonical_production_view import build_production_and_structures

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
    # Clean up any exclusion facts this file wrote, and re-evaluate once
    # more so later tests see the real project back in its default
    # (Saudi included) state — never leave test-only DB mutations behind.
    async with AsyncSession(engine, expire_on_commit=False) as cleanup:
        await cleanup.execute(
            sa_delete(ProjectFact).where(
                ProjectFact.project_id == FVD_PROJECT_ID,
                ProjectFact.fact_key.like(f"{JURISDICTION_PREFERENCE_FACT_PREFIX}%"),
            )
        )
        await cleanup.commit()
        await evaluate_project(cleanup, FVD_PROJECT_ID)


async def _set_excluded(db: AsyncSession, code: str, excluded: bool):
    fact_key = f"{JURISDICTION_PREFERENCE_FACT_PREFIX}{code}"
    existing = (await db.execute(
        select(ProjectFact).where(ProjectFact.project_id == FVD_PROJECT_ID, ProjectFact.fact_key == fact_key)
    )).scalar_one_or_none()
    if excluded:
        if existing is not None:
            existing.value = "excluded"
        else:
            db.add(ProjectFact(
                project_id=FVD_PROJECT_ID, fact_key=fact_key, value="excluded",
                value_type="string", source_type="user_override",
            ))
    elif existing is not None:
        await db.delete(existing)
    await db.commit()


async def test_excluded_jurisdiction_codes_reads_the_generic_fact(db: AsyncSession):
    await _set_excluded(db, "SA", True)
    excluded = await _excluded_jurisdiction_codes(db, FVD_PROJECT_ID)
    assert "SA" in excluded


async def test_excluded_jurisdiction_is_removed_from_evaluate_project_candidates(db: AsyncSession):
    await _set_excluded(db, "SA", True)
    result = await evaluate_project(db, FVD_PROJECT_ID)
    assert result["status"] not in ("PROJECT_NOT_FOUND", "BLOCKED_INCOMPLETE_INPUTS")
    rows = (await db.execute(
        select(ProjectFact).where(ProjectFact.project_id == FVD_PROJECT_ID)
    )).scalars().all()  # sanity: fact still present after evaluate
    assert any(f.fact_key == f"{JURISDICTION_PREFERENCE_FACT_PREFIX}SA" for f in rows)


async def test_regression_all_fingerprint_readers_agree_when_an_exclusion_is_set(db: AsyncSession):
    """The exact bug: excluding Saudi must not make the served
    production/structures payload go empty. build_production_and_
    structures (the real /state read path) must return a real,
    non-empty result — never PROJECT_NOT_FOUND-shaped emptiness caused
    by a fingerprint mismatch against what evaluate_project persisted."""
    await _set_excluded(db, "SA", True)
    await evaluate_project(db, FVD_PROJECT_ID)

    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    assert view["status"] == "OK"
    assert view["production"]["jurisdiction_code"] is not None, (
        "production.jurisdiction_code went null -- the exact symptom of the "
        "fingerprint-divergence bug this test guards against"
    )
    structures = view["structures"]["allocated_structures"]["structures"]
    assert len(structures) > 0, (
        "structures list went empty -- the exact symptom of the "
        "fingerprint-divergence bug this test guards against"
    )
    sa_structures = [s for s in structures if s.get("primary_jurisdiction") == "SA"]
    assert sa_structures == [], "Saudi Arabia must not appear in the candidate universe while excluded"


async def test_reincluding_restores_the_candidate_with_unchanged_economics(db: AsyncSession):
    """Saudi ON restores participation while preserving its real
    conditional/discretionary economics — never a re-derived or
    different NPC than before exclusion."""
    await _set_excluded(db, "SA", True)
    await evaluate_project(db, FVD_PROJECT_ID)
    view_excluded = await build_production_and_structures(db, FVD_PROJECT_ID)
    assert not any(
        s.get("primary_jurisdiction") == "SA"
        for s in view_excluded["structures"]["allocated_structures"]["structures"]
    )

    await _set_excluded(db, "SA", False)
    await evaluate_project(db, FVD_PROJECT_ID)
    view_included = await build_production_and_structures(db, FVD_PROJECT_ID)
    sa_structures = [
        s for s in view_included["structures"]["allocated_structures"]["structures"]
        if s.get("primary_jurisdiction") == "SA"
    ]
    assert len(sa_structures) >= 1, "Saudi Arabia must be restored to the candidate universe"
    sa = sa_structures[0]
    assert sa.get("npc_with_adjustments_usd") is not None
    # Discretionary/preapproval disclosure must survive re-inclusion —
    # exclusion/inclusion is a modeling preference, never a change to
    # the real doctrine the structure carries.
    assert any(
        (w or "").startswith("Administrative/allocation risk") for w in (sa.get("warnings") or [])
    ), "re-included Saudi structure must still carry its real discretionary/preapproval disclosure"


async def test_home_jurisdiction_cannot_be_excluded_from_its_own_candidate_universe(db: AsyncSession):
    """Excluding a project's own base/home jurisdiction would remove its
    anchor structure entirely -- never allowed, regardless of what
    preference is set for it."""
    await _set_excluded(db, "GR", True)
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    assert view["status"] == "OK"
    structures = view["structures"]["allocated_structures"]["structures"]
    home = [s for s in structures if s.get("primary_jurisdiction") == "GR" and s.get("structure_type") == "single_country"]
    assert home, "the production's own home/base jurisdiction structure must never be excludable"
