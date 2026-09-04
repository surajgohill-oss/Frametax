"""
Canonical optimizer/Globe wiring remediation (2026-09-04), P0-2.

ROOT CAUSE (confirmed via Codex's four-project audit, VERIFIED against
CURRENT HEAD before this fix): canonical_evaluation.py's component-
relocation persistence path wrote the SAME adjusted value
(`npc = pricing.npc_with_adjustments_usd`) into BOTH
`true_net_cost_usd` and `risk_adjusted_net_cost_usd`, while the row's
own `calculation_trace_json` already correctly carried the real
verified figure (`npc_verified_usd`) -- only the top-level served DB
column mislabeled adjusted-as-verified. The trace also never carried
an `"adjustments"` breakdown at all (unlike single/full_relocation's
trace, which always has one), so canonical_production_view.py's
`(trace.get("adjustments") or {}).get(...)` reads silently returned
null/0.0 for every served delta on a component structure -- the
adjusted NPC could not be reconstructed from its own served fields.

Fixed by reading pricing.npc_verified_usd (already correctly computed
by the SAME price_allocated_structure kernel every structure type
uses) into true_net_cost_usd, and by adding the SAME "adjustments"
dict shape the single/full_relocation path already serves.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"

_DELTA_FIELDS = (
    "travel_incremental_delta_usd", "fx_delta_usd", "inkind_replacement_delta_usd",
    "local_cost_delta_usd", "financing_cost_usd", "implementation_cost_usd",
)


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_component_npc_verified_and_adjusted_are_independent_real_values(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]["structures"]
    components = [
        s for s in structures
        if s["structure_type"] == "component_relocation" and s["is_fully_priced"]
    ]
    assert components, "expected priced component_relocation structures in the real fixture"
    collapsed = [
        s for s in components
        if s["npc_verified_usd"] is not None
        and s["npc_verified_usd"] == s["npc_with_adjustments_usd"]
        and any((s.get(f) or 0) != 0 for f in _DELTA_FIELDS)
    ]
    # A structure with genuinely zero adjustments legitimately has
    # verified == adjusted; the defect was verified being FORCED equal
    # to adjusted even when real, non-zero deltas existed. Assert none
    # of the sampled components exhibit that specific contradiction.
    assert collapsed == [], f"npc_verified_usd collapsed into npc_with_adjustments_usd despite real deltas: {collapsed[:3]}"


async def test_component_adjusted_npc_reconstructs_exactly_from_verified_plus_deltas(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]["structures"]
    components = [
        s for s in structures
        if s["structure_type"] == "component_relocation" and s["is_fully_priced"]
    ]
    assert components
    for s in components[:25]:
        reconstructed = round((s["npc_verified_usd"] or 0.0) + sum((s.get(f) or 0.0) for f in _DELTA_FIELDS), 2)
        assert reconstructed == round(s["npc_with_adjustments_usd"], 2), (
            f"{s['label']}: verified {s['npc_verified_usd']} + deltas {[s.get(f) for f in _DELTA_FIELDS]} "
            f"= {reconstructed}, but served adjusted NPC is {s['npc_with_adjustments_usd']}"
        )


async def test_single_and_full_relocation_npc_reconstruction_still_holds(db: AsyncSession):
    """Regression guard for the path that was ALREADY correct — must
    still reconstruct after this fix, for both projects."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        await evaluate_project(db, project_id)
        view = await build_production_and_structures(db, project_id)
        structures = view["structures"]["allocated_structures"]["structures"]
        singles = [
            s for s in structures
            if s["structure_type"] in ("single_country", "full_relocation") and s["is_fully_priced"]
        ]
        assert singles, f"{project_id}: expected priced single/full_relocation structures"
        for s in singles[:10]:
            reconstructed = round((s["npc_verified_usd"] or 0.0) + sum((s.get(f) or 0.0) for f in _DELTA_FIELDS), 2)
            assert reconstructed == round(s["npc_with_adjustments_usd"], 2), (
                f"{project_id}: {s['label']}: reconstruction mismatch"
            )
