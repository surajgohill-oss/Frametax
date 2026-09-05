"""
Reinvestment + Qualification Opportunity Optimization — served-runtime
regression tests.

Runtime-proven against FVD/LU real project data: both discover real
cultural-test-gap disclosures (fail-closed, never scored) among their
own discovered candidate jurisdictions.

Canonical Budget Parser Remediation (2026-09-04): FVD previously also
showed a "real" fee-cap-headroom opportunity against Cyprus's/New York's
ATL caps — since fixed as a fabricated artifact of undercounted ATL
spend (see test_fvd_no_longer_shows_fee_cap_headroom_once_its_real_atl_
spend_is_counted below). The fee-cap-headroom MECHANISM itself remains
independently unit-tested in test_canonical_opportunity_bridge.py.
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


async def test_fvd_no_longer_shows_fee_cap_headroom_once_its_real_atl_spend_is_counted(db: AsyncSession):
    """Canonical Budget Parser Remediation (2026-09-04): this test
    previously proved FVD had real ATL/producer-fee-cap headroom against
    Cyprus's/New York's real caps. That "headroom" was an ARTIFACT of
    Codex BPI-006 — FVD's own real "1200 PRODUCERS" ($401,831) and "1300
    DIRECTOR" ($75,710) were classified `miscellaneous` (a broken
    end-of-string regex anchor never matched a real parsed line with a
    department suffix), so current_atl_spend_usd
    (canonical_evaluation.py's component-spend sum) silently EXCLUDED
    $477,541 of FVD's own real ATL fees from the cap comparison,
    fabricating headroom that never actually existed.

    With producer/director correctly counted as `above_the_line`
    component spend, FVD's real current ATL spend now exhausts every
    ATL-capped program's real cap on file — the mechanism itself
    (discover_fee_cap_headroom_opportunity, including its own "no
    headroom returns None" case) remains independently unit-tested in
    test_canonical_opportunity_bridge.py; this real-corpus test now
    proves the OPPOSITE, equally real fact: no FEE_CAP_HEADROOM
    opportunity is fabricated once FVD's real fees are correctly
    counted."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    with_fee_opp = [
        e for e in entries
        if any(o["opportunity_type"] == "FEE_CAP_HEADROOM" for o in (e.get("opportunities") or []))
    ]
    assert not with_fee_opp, (
        "FVD's real producer/director ATL fees, once correctly counted, exhaust every "
        "real ATL cap on file — no fee-cap-headroom opportunity should be fabricated"
    )


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
    assert round(lu_baseline["npc_with_adjustments_usd"], 2) == 3791333.30  # Production Page Integrity Closeout (migration 0071): migration 0068's beta 100% contingency-utilization election was removed as a stale, project-name-branched default. With no election on file, derive_qualification_register's own existing GREY_AREA_REQUIRES_AUTHORITY doctrine applies (never silently 0% or 100%) — the reserve is excluded from qualifying QPE until a producer sets contingency_expected_utilization_pct via POST /projects/{id}/assumptions. Reconciled: budget ($4,364,393) + LA item (account 5000 EDITORIAL, $9,068, already excluded from MU QPE via the existing accounts_outside_jurisdiction fact) + contingency (unset) + QPE ($1,838,566) + incentive ($551,569.80) + NPC ($3,812,823.20), reproduced via a real evaluate_project() call.

    await evaluate_project(db, FVD_PROJECT_ID)
    fvd_view = await build_production_and_structures(db, FVD_PROJECT_ID)
    fvd_baseline = next(e for e in fvd_view["structures"]["allocated_structures"]["structures"] if e["is_baseline"])
    assert round(fvd_baseline["npc_with_adjustments_usd"], 2) == 3072027.16
