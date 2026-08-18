"""
Existing Optimizer/Stacker Reconnection, Task B (treaty/official
co-production) — served-runtime regression tests.

Runtime-proven against FVD's real project: Greece is a real Eurimages
member and 36 of FVD's own discovered candidate jurisdictions are also
members (see canonical_treaty_bridge.py). Little Utopia's Mauritius has
zero bilateral treaties and is not a Eurimages member (proven-zero,
established in earlier sessions) -- both are real, honest facts, not
fabricated to force a proof.
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


async def test_fvd_eurimages_opportunity_reaches_co_pro_opportunities_category(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    treaty = [e for e in entries if e["structure_type"] == "treaty_coproduction"]
    assert len(treaty) == 1
    e = treaty[0]
    assert e["treaty_slug"] == "eurimages"
    assert e["scenario_category"] == "CO_PRO_OPPORTUNITIES"
    assert e["treaty_resolution_state"] == "UNRESOLVED_FACTS"
    assert e["treaty_cultural_test_required"] is True
    assert e["treaty_cultural_test_resolved"] is False
    assert len(e["coproduction_partners"]) > 0
    for p in e["coproduction_partners"]:
        assert p["jurisdiction_display_name"] != p["jurisdiction_code"], (
            "co-pro partners must expose human-readable names, not raw codes"
        )


async def test_unresolved_treaty_opportunity_cannot_rank_as_recommended(db: AsyncSession):
    """Ranking admission gate: an unresolved co-pro opportunity must never
    compete as the numeric RECOMMENDED winner -- it is not fully priced
    and never enters comparable ranking."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    ranking = view["structures"]["allocated_structures"]["ranking"]
    treaty_ranked = [r for r in ranking if r.get("scenario_category") == "CO_PRO_OPPORTUNITIES"]
    assert treaty_ranked
    for r in treaty_ranked:
        assert r["rank"] is None
        assert r["is_fully_priced"] is False


async def test_unresolved_treaty_opportunity_never_enters_npc(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    treaty = next(e for e in entries if e["structure_type"] == "treaty_coproduction")
    assert treaty["npc_with_adjustments_usd"] is None
    assert treaty["selected_incentive_usd"] is None


async def test_little_utopia_has_no_treaty_coproduction_opportunity_proven_zero(db: AsyncSession):
    """Mauritius has zero bilateral treaties and is not a Eurimages
    member -- a real, honest zero, not a missing wire-up. Baseline
    remains unaffected."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    treaty = [e for e in entries if e["structure_type"] == "treaty_coproduction"]
    assert treaty == []
    baseline = next(e for e in entries if e["is_baseline"])
    assert round(baseline["npc_with_adjustments_usd"], 2) == 3057794.90
