"""
Existing Optimizer/Stacker Reconnection, Task A (component/split) —
focused regression tests.

Runtime-proven against FVD's real budget (post $172,904, vfx $10,000,
music $10,200 — see canonical_evaluation._price_component_relocation_
candidate and its wiring in evaluate_project). No synthetic project is
built here; these assertions read the SAME persisted rows the served
API/UI reads.
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


async def test_fvd_component_relocation_candidates_exist_and_are_typed(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    comp = [e for e in entries if e["structure_type"] == "component_relocation"]
    assert len(comp) > 0, "expected at least one component/split candidate for FVD"
    for e in comp:
        assert e["anchor_jurisdiction"] == "GR"
        assert e["anchor_program"] == "gr_cash_rebate"
        assert e["stacked_programs"] == [], "a routed component program must never be flattened into stacked_programs"
        assert len(e["component_allocations"]) == 1
        ca = e["component_allocations"][0]
        assert ca["component"] in ("post", "vfx", "music")
        assert ca["jurisdiction_code"] != "GR"
        assert ca["jurisdiction_display_name"], "component allocation must carry a human-readable jurisdiction name"
        assert ca["program_slug"]
        assert ca["allocated_usd"] > 0
        assert e["is_directly_comparable"] is False
        assert e["scenario_category"] == "PRICED_LOW_FIT"


async def test_fvd_component_relocation_traces_real_budget_spend_not_invented(db: AsyncSession):
    """The routed component's allocated_usd must equal the REAL project
    budget spend for that component — never a fabricated or rounded
    amount. post=$172,904, vfx=$10,000, music=$10,200 are FVD's own real
    budget totals."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    comp = [e for e in entries if e["structure_type"] == "component_relocation"]

    expected_by_component = {"post": 172_904.0, "vfx": 10_000.0, "music": 10_200.0}
    seen_components = set()
    for e in comp:
        ca = e["component_allocations"][0]
        component = ca["component"]
        seen_components.add(component)
        assert ca["allocated_usd"] == pytest.approx(expected_by_component[component], abs=0.01), (
            f"{component} routed spend must equal FVD's own real budget total, never invented"
        )
    assert seen_components == {"post", "vfx", "music"}, "expected all three movable components to be attempted"


async def test_fvd_component_relocation_allocation_conserves_gross_budget(db: AsyncSession):
    """No dollar may be invented or dropped: every component_relocation
    candidate's segments must sum back to the production's gross budget."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    comp = [e for e in entries if e["structure_type"] == "component_relocation"]
    assert comp
    for e in comp:
        total_allocated = sum(s["allocated_usd"] for s in e["segments"])
        assert total_allocated == pytest.approx(e["gross_budget_usd"], abs=1.00), (
            f"{e['structure_id']}: allocation must conserve the full gross budget "
            f"(got {total_allocated}, expected {e['gross_budget_usd']})"
        )


async def test_component_relocation_never_uses_default_domicile_for_routed_spend(db: AsyncSession):
    """The routed component's jurisdiction must be the explicitly chosen
    target, never silently defaulted back to the home/anchor jurisdiction
    (which would defeat the entire candidate)."""
    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    comp = [e for e in entries if e["structure_type"] == "component_relocation"]
    assert comp
    for e in comp:
        ca = e["component_allocations"][0]
        assert ca["jurisdiction_code"] != e["anchor_jurisdiction"]
        matching_segment = next(s for s in e["segments"] if s["jurisdiction_code"] == ca["jurisdiction_code"])
        assert matching_segment["allocated_usd"] == pytest.approx(ca["allocated_usd"], abs=0.01)


async def test_little_utopia_baseline_unchanged_by_component_relocation(db: AsyncSession):
    """Component/split candidates are additive only — the calibrated
    Mauritius baseline must remain byte-identical."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    baseline = next(e for e in entries if e["is_baseline"])
    assert round(baseline["npc_with_adjustments_usd"], 2) == 3057794.90  # CBA-009 Part 19-21: LU's own persisted 100% contingency-utilization project election (migration 0068) reproduces the historical $3,057,794.90 baseline through the generic pipeline
    comp = [e for e in entries if e["structure_type"] == "component_relocation"]
    assert len(comp) > 0
