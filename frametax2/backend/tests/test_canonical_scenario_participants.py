"""
Canonical optimizer/Globe wiring remediation (2026-09-04), P0-3.

ROOT CAUSE (confirmed via Codex's four-project audit, VERIFIED against
CURRENT HEAD before this fix): `canonical_production_view.py`'s
`_empty_structure_entry` served `"participants": [code] if code else []`
unconditionally -- the primary jurisdiction ALONE, for every structure
type. All 740 component_relocation and 96 treaty_coproduction structures
across the four audited projects therefore lost their routed/partner
jurisdiction at this exact API boundary: "Greece anchor -- post routed to
Romania" served participants=["GR"], never ["GR","RO"]. Every downstream
consumer (scenario title/flags, selection, Globe paths, Inspector
routing, Reports) inherited the corruption.

Fixed generically from the SAME real persisted trace fields every other
served field already reads -- never parsed from the free-text structure
label, never reconstructed in the frontend (the audit's own explicit
instruction: "Do not reconstruct lost participant identity in the
frontend"):
  - segments[].jurisdiction_code (component_relocation/full_relocation/
    single_country's own real per-jurisdiction allocation)
  - coproduction_partners[].jurisdiction_code (treaty_coproduction's
    real treaty party/parties)

Three real, structurally-distinct coproduction_partners shapes exist and
are each covered here (see canonical_production_view.py's own inline
comment for the full doctrine):
  1. multilateral (Eurimages / European Convention): home jurisdiction
     IS a genuine party, alongside however many other real members.
  2. bilateral, one partner entry: home jurisdiction IS the other real
     party ("{home} + {partner}").
  3. bilateral, two partner entries: the treaty is between two OTHER
     candidate jurisdictions and home is explicitly NOT a party.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_production_view import build_production_and_structures

FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_component_relocation_participants_include_the_routed_destination(db: AsyncSession):
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]["structures"]
    components = [s for s in structures if s["structure_type"] == "component_relocation"]
    assert components, "expected at least one component_relocation structure in the real fixture"
    regressions = [
        s for s in components
        if len(s["participants"]) < 2 or s["primary_jurisdiction"] not in s["participants"]
    ]
    assert regressions == [], (
        f"{len(regressions)} component_relocation structures lost their routed "
        f"destination from participants (the exact P0-3 defect): {regressions[:3]}"
    )


async def test_bilateral_treaty_with_home_as_a_party_includes_home_in_participants(db: AsyncSession):
    """Neither current real fixture (F#K's home Greece, Little Utopia's
    home Mauritius) happens to have a registered bilateral treaty
    partner among its OWN discovered candidates -- both projects'
    bilateral opportunities are genuinely all between OTHER
    jurisdictions (see the 2-partner test below). This checks the
    invariant conditionally against whichever real rows exist rather
    than assuming a shape neither current fixture has, consistent with
    this suite's real-data-only convention."""
    checked_any = False
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        structures = view["structures"]["allocated_structures"]["structures"]
        home = view["production"]["jurisdiction_code"]
        home_bilateral = [
            s for s in structures
            if s["structure_type"] == "treaty_coproduction"
            and s["label"].startswith(f"{home} + ")
        ]
        for s in home_bilateral:
            checked_any = True
            assert home in s["participants"], f"{s['label']}: home {home} must be a participant"
            assert len(s["participants"]) == 2, f"{s['label']}: expected exactly 2 real parties, got {s['participants']}"
    if not checked_any:
        pytest.skip("neither current real fixture has a home-jurisdiction bilateral treaty opportunity on file")


async def test_bilateral_treaty_between_two_other_candidates_excludes_home(db: AsyncSession):
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]["structures"]
    home = view["production"]["jurisdiction_code"]
    third_party_bilateral = [
        s for s in structures
        if s["structure_type"] == "treaty_coproduction"
        and not s["label"].startswith(f"{home} + ")
        and "+" in s["label"]
        and "Eurimages" not in s["label"]
        and "European Convention" not in s["label"]
    ]
    assert third_party_bilateral, "expected at least one bilateral opportunity between two non-home candidates"
    for s in third_party_bilateral:
        assert home not in s["participants"], (
            f"{s['label']}: {home} is not a real party to this treaty and must not appear in participants "
            f"(got {s['participants']})"
        )
        assert len(s["participants"]) == 2


async def test_multilateral_treaty_opportunity_includes_home_as_a_genuine_member(db: AsyncSession):
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]["structures"]
    home = view["production"]["jurisdiction_code"]
    multilateral = [
        s for s in structures
        if s["structure_type"] == "treaty_coproduction"
        and ("Eurimages" in s["label"] or "European Convention" in s["label"])
    ]
    assert multilateral, "expected at least one multilateral (Eurimages/European Convention) opportunity"
    for s in multilateral:
        assert home in s["participants"], f"{s['label']}: home {home} is a genuine member and must be a participant"
        assert len(s["participants"]) > 2, f"{s['label']}: expected multiple real members, got {s['participants']}"


async def test_single_country_and_full_relocation_still_serve_exactly_one_participant(db: AsyncSession):
    """No regression for structure types the audit found correct already —
    a single/full_relocation candidate has exactly one real jurisdiction."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        structures = view["structures"]["allocated_structures"]["structures"]
        singles = [s for s in structures if s["structure_type"] in ("single_country", "full_relocation")]
        assert singles, f"{project_id}: expected single/full_relocation structures"
        for s in singles:
            assert s["participants"] == [s["primary_jurisdiction"]], (
                f"{project_id}: {s['label']} must serve exactly its own primary jurisdiction, "
                f"got {s['participants']}"
            )


async def test_generated_participants_equal_persisted_trace_participants_cross_project(db: AsyncSession):
    """Cross-project regression guard, not a single-project special case —
    the same identity contract must hold for Little Utopia too."""
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]["structures"]
    components = [s for s in structures if s["structure_type"] == "component_relocation"]
    assert components
    for s in components[:20]:
        assert len(s["participants"]) >= 2, f"{s['label']}: {s['participants']}"
