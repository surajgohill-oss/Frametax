"""
test_coproduction_optimizer_preservation.py

CO-PRODUCTION OPTIMIZER PRESERVATION GATE.

This is a REGRESSION gate, not new product work. The canonical economics +
wiring integrity repair made several programs fail closed (authority
unresolved, unconfirmable rate ceilings, labour-only qualifying bases). A
fail-closed CONSTITUENT must remove only its own economic leg -- it must never
remove, bypass or degrade the generic treaty / co-production capability
itself.

Asserted here, against the live corpus:

  * treaty / co-production candidate generation still executes;
  * co-production structures remain available wherever their constituent
    programs are legitimately reachable;
  * a blocked constituent fails closed WITHOUT destroying the capability --
    the other pairs survive;
  * conditional co-productions keep their conditional, non-deterministic
    treatment (never priced, never carrying NPC, never ranked as comparable);
  * multi-program stacking and component routing still generate.

Nothing here redesigns the optimizer; it pins the behavior that already
existed so a later repair cannot silently erode it.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- import-order guard
from app.db.session import engine
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import build_production_and_structures

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LIPS_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"

ALL_FIXTURES = (FVD_PROJECT_ID, LIPS_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID)


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def _structures(session: AsyncSession, project_id: str) -> list[dict]:
    # Evaluate first: reads are PURE (cluster 13), so a project whose rows
    # predate the current engine version has nothing current to serve. The
    # other served-runtime suites use the same pattern.
    await evaluate_project(session, project_id)
    view = await build_production_and_structures(session, project_id)
    return view["structures"]["allocated_structures"]["structures"]


@pytest.mark.parametrize("project_id", ALL_FIXTURES)
async def test_treaty_coproduction_generation_still_executes(
    db: AsyncSession, project_id: str,
):
    """The capability itself must survive the fail-closed repairs."""
    treaty = [
        e for e in await _structures(db, project_id)
        if e["structure_type"] == "treaty_coproduction"
    ]
    assert treaty, "treaty/co-production candidate generation stopped producing"
    assert len(treaty) > 1, "co-production capability collapsed to a single case"


@pytest.mark.parametrize("project_id", ALL_FIXTURES)
async def test_conditional_coproductions_stay_conditional(
    db: AsyncSession, project_id: str,
):
    """Uncertain co-productions must never acquire deterministic economics:
    real ownership/cultural-test facts are not on file, so they are
    opportunities, not priced structures."""
    treaty = [
        e for e in await _structures(db, project_id)
        if e["structure_type"] == "treaty_coproduction"
    ]
    for entry in treaty:
        assert entry["scenario_category"] == "CO_PRO_OPPORTUNITIES"
        assert entry["treaty_resolution_state"] == "UNRESOLVED_FACTS"
        assert entry["is_fully_priced"] is False
        assert not entry.get("selected_incentive_usd")
        assert entry.get("npc_with_adjustments_usd") is None, (
            "a conditional co-production must not carry an NPC"
        )
        assert entry["is_directly_comparable"] is False


@pytest.mark.parametrize("project_id", ALL_FIXTURES)
async def test_coproduction_partners_are_named_not_raw_codes(
    db: AsyncSession, project_id: str,
):
    treaty = [
        e for e in await _structures(db, project_id)
        if e["structure_type"] == "treaty_coproduction"
    ]
    partners = [p for e in treaty for p in (e.get("coproduction_partners") or [])]
    assert partners, "co-production structures carry no partners"
    for partner in partners:
        assert partner.get("jurisdiction_display_name"), (
            f"partner {partner.get('jurisdiction_code')} served as a raw code"
        )


async def test_a_blocked_constituent_does_not_destroy_the_capability(db: AsyncSession):
    """THE preservation invariant. ch_pics_national_rebate became
    AUTHORITY_UNRESOLVED_NON_PRICEABLE, so Switzerland lost its economic leg
    and the single ca-ch bilateral pair correctly dropped out. Every OTHER
    bilateral pair must remain -- a fail-closed constituent removes its own
    leg, never the generic capability."""
    from app.data.authority_coverage_registry import blocks_economic_candidacy

    assert blocks_economic_candidacy("ch_pics_national_rebate"), (
        "precondition: this test is about a genuinely blocked constituent"
    )

    treaty = [
        e for e in await _structures(db, FVD_PROJECT_ID)
        if e["structure_type"] == "treaty_coproduction"
    ]
    slugs = {e.get("treaty_slug") for e in treaty}
    assert "ca-ch-bilateral" not in slugs, (
        "a pair whose constituent is authority-blocked must not be offered"
    )
    bilateral = [
        e for e in treaty
        if e.get("treaty_slug") not in ("eurimages", "european-convention-coproduction")
    ]
    # The universe legitimately shrinks as constituents fail closed -- Canada
    # appears in many bilateral pairs and its CPTC/PSTC family is now withheld
    # on a labour-only qualifying base (cluster 5). What must NOT happen is
    # collapse: a substantial, multi-partner bilateral universe has to remain,
    # which is the capability this gate protects. Asserted as a property, not
    # a frozen count, so a later legitimate disposition change cannot force a
    # misleading edit here.
    assert len(bilateral) >= 5, (
        f"blocking constituents collapsed the bilateral universe to {len(bilateral)}"
    )
    distinct_partners = {
        p["jurisdiction_code"]
        for e in bilateral for p in (e.get("coproduction_partners") or [])
    }
    assert len(distinct_partners) >= 5, (
        f"bilateral co-production reduced to {len(distinct_partners)} partner(s)"
    )


@pytest.mark.parametrize("project_id", ALL_FIXTURES)
async def test_multi_program_stacking_and_component_routing_still_generate(
    db: AsyncSession, project_id: str,
):
    """The other two additive optimizer capabilities must also survive."""
    structures = await _structures(db, project_id)
    multi = [e for e in structures if e["structure_type"] == "multi_program"]
    component = [e for e in structures if e["structure_type"] == "component_relocation"]
    assert multi, "multi-program stacking stopped generating"
    assert component, "component/split routing stopped generating"


async def test_multilateral_frameworks_are_still_discovered(db: AsyncSession):
    """Eurimages and the European Convention are membership-proven
    multilateral frameworks; both must still surface for a Greek production."""
    treaty = [
        e for e in await _structures(db, FVD_PROJECT_ID)
        if e["structure_type"] == "treaty_coproduction"
    ]
    slugs = {e.get("treaty_slug") for e in treaty}
    assert {"eurimages", "european-convention-coproduction"} <= slugs
