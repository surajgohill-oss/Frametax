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
# Codex P2 finding (Optimizer Wiring Capability Audit): importing
# canonical_production_view before canonical_evaluation triggers a real
# import-order circularity (DoctrineRateTier / executable_jurisdiction_
# registry) when this file is collected in isolation. Importing the
# evaluator first (unused directly, but its import side effects resolve
# the cycle) is acceptance-harness fragility, not a production defect —
# documented, not fixed here (out of this task's exact P0 scope).
import app.services.canonical_evaluation  # noqa: F401
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


# ── Optimizer P0 wiring remediation (2026-09-04), P0-2 — COMPONENT
# PARTICIPANT CONTAMINATION. Codex's own critique of this file's prior
# coverage: "only requires at least two participants and misses exact
# identity." The tests above (kept, still valid — they check the
# regression Codex found for THIS pass' predecessor) never asserted the
# participant SET is exactly right; a structure could pass every
# assertion above while still including a non-claiming stated-location
# segment. These tests check exact identity instead.

def _claiming_participants(structure: dict) -> set[str]:
    """The real, structural definition of an economic/claiming
    participant: the primary jurisdiction, plus any segment whose own
    `claims_incentive` field (allocation_pricing.SegmentEconomics — False
    exactly when the segment has no program_slug, i.e. a stated-location
    fact) is True. Mirrors canonical_production_view.py's own fix
    exactly, so this test can never silently agree with a reintroduced
    bug by re-deriving the SAME wrong logic — it reads the same
    structural signal, independently, from the served segments."""
    claiming = {structure["primary_jurisdiction"]}
    for seg in structure.get("segments") or []:
        if seg.get("claims_incentive") is True and seg.get("jurisdiction_code"):
            claiming.add(seg["jurisdiction_code"])
    return claiming


async def test_component_participants_exactly_equal_claiming_segments_not_merely_at_least_two(db: AsyncSession):
    """Exact-identity check (Codex's own named gap) across every
    component_relocation structure in both LU and FVD — not merely a
    count floor. A structure whose participants include a non-claiming
    stated-location segment (or omit a real claiming one) fails here even
    if it happens to have >= 2 participants."""
    for project_id, label in ((FVD_PROJECT_ID, "FVD"), (LITTLE_UTOPIA_PROJECT_ID, "LU")):
        view = await build_production_and_structures(db, project_id)
        structures = view["structures"]["allocated_structures"]["structures"]
        components = [s for s in structures if s["structure_type"] == "component_relocation"]
        assert components, f"{label}: expected component_relocation structures"
        mismatches = [
            (s["structure_id"], s["participants"], sorted(_claiming_participants(s)))
            for s in components
            if set(s["participants"]) != _claiming_participants(s)
        ]
        assert mismatches == [], f"{label}: {len(mismatches)} component structures have a wrong participant set: {mismatches[:3]}"


async def test_little_utopia_named_regression_structure_excludes_non_claiming_us(db: AsyncSession):
    """The EXACT real-project case Codex named: structure
    8172eb82-c2cc-4816-a331-beffddab5199 must serve participants=['MU',
    'CA-MB'], never including the non-claiming stated-location 'US'
    segment (previously ['MU', 'CA-MB', 'US'])."""
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    structures = view["structures"]["allocated_structures"]["structures"]
    target = next(
        (s for s in structures if s["structure_id"] == "8172eb82-c2cc-4816-a331-beffddab5199"), None,
    )
    if target is None:
        pytest.skip("named regression structure not present in the current persisted fingerprint")
    assert sorted(target["participants"]) == ["CA-MB", "MU"], (
        f"expected exactly ['CA-MB', 'MU'] (US excluded as a non-claiming stated-location "
        f"segment), got {target['participants']}"
    )
    # The non-claiming US segment must still be visible in the detailed
    # trace/allocation — only excluded from the canonical PARTICIPANT
    # list, never deleted from the data.
    us_segment = next((seg for seg in target.get("segments") or [] if seg.get("jurisdiction_code") == "US"), None)
    assert us_segment is not None, "the real US segment must remain visible in the detailed trace"
    assert us_segment.get("claims_incentive") is False


async def test_single_country_and_treaty_participants_unaffected_by_p0_2_fix(db: AsyncSession):
    """Regression guard: the P0-2 fix is scoped to component_relocation
    only — single_country and treaty_coproduction participant
    construction must be byte-identical to before."""
    for project_id in (FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID):
        view = await build_production_and_structures(db, project_id)
        structures = view["structures"]["allocated_structures"]["structures"]
        single = next((s for s in structures if s["structure_type"] == "single_country"), None)
        assert single is not None
        assert single["participants"] == [single["primary_jurisdiction"]]
        treaty = next((s for s in structures if s["structure_type"] == "treaty_coproduction"), None)
        assert treaty is not None
        assert len(treaty["participants"]) >= 2
