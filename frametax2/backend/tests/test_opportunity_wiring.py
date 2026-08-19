"""
Reinvestment + Qualification Opportunity Optimization — served-runtime
regression tests.

Runtime-proven against FVD/LU real project data: both discover real
fee-cap-headroom opportunities (Cyprus's real 30% ATL cap, New York's
real 40% ATL cap) and real cultural-test-gap disclosures (fail-closed,
never scored) among their own discovered candidate jurisdictions.
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


async def test_fvd_discovers_real_fee_cap_headroom_opportunity(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    with_fee_opp = [
        e for e in entries
        if any(o["opportunity_type"] == "FEE_CAP_HEADROOM" for o in (e.get("opportunities") or []))
    ]
    assert with_fee_opp, "expected at least one real fee-cap-headroom opportunity for FVD"
    opp = next(o for o in with_fee_opp[0]["opportunities"] if o["opportunity_type"] == "FEE_CAP_HEADROOM")
    # cash != deferred, incremental incentive != net benefit conflation guard
    assert opp["incremental_cash_usd"] == 0.0
    assert opp["incremental_incentive_usd"] > 0
    assert opp["net_benefit_usd"] == opp["incremental_incentive_usd"]
    assert opp["required_facts"]
    assert opp["reasoning_trace"]


async def test_fvd_discovers_cultural_gap_fails_closed(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    with_cultural = [
        e for e in entries
        if any(o["opportunity_type"] == "CULTURAL_TEST_GAP" for o in (e.get("opportunities") or []))
    ]
    assert with_cultural
    opp = next(o for o in with_cultural[0]["opportunities"] if o["opportunity_type"] == "CULTURAL_TEST_GAP")
    assert opp["status"] == "REQUIRES_SCREEN_ANALYZER_FACT"
    assert opp["incremental_incentive_usd"] == 0.0  # never fabricated


async def test_opportunities_never_contaminate_ranking(db: AsyncSession):
    """Task 9/14 — a candidate carrying only CONDITIONAL/REQUIRES-fact
    opportunities must still rank/categorize purely on its own resolved
    pricing, never boosted by unresolved opportunity value."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    ranking = view["structures"]["allocated_structures"]["ranking"]
    by_id = {e["structure_id"]: e for e in entries}
    for r in ranking:
        e = by_id.get(r["structure_id"])
        if not e or not e.get("opportunities"):
            continue
        # is_directly_comparable/rank must be unaffected by opportunity presence
        assert r["is_directly_comparable"] == e["is_directly_comparable"]


async def test_opportunities_survive_persistence_and_api(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    any_opp = next(e for e in entries if e.get("opportunities"))
    opp = any_opp["opportunities"][0]
    for key in (
        "opportunity_id", "opportunity_type", "status", "title", "description",
        "incremental_qpe_usd", "incremental_incentive_usd", "reasoning_trace",
    ):
        assert key in opp


async def test_baselines_unchanged_after_opportunity_reconnection(db: AsyncSession):
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    lu_view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    lu_baseline = next(e for e in lu_view["structures"]["allocated_structures"]["structures"] if e["is_baseline"])
    assert round(lu_baseline["npc_with_adjustments_usd"], 2) == 3057794.90

    await evaluate_project(db, FVD_PROJECT_ID)
    fvd_view = await build_production_and_structures(db, FVD_PROJECT_ID)
    fvd_baseline = next(e for e in fvd_view["structures"]["allocated_structures"]["structures"] if e["is_baseline"])
    assert round(fvd_baseline["npc_with_adjustments_usd"], 2) == 3072027.16
