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
    # Final Consolidated Backend Correction + Global Structuring
    # Intelligence Acceptance, Part 3/CBA-006: FVD's Greece is also a
    # real European Convention on Cinematographic Co-Production
    # signatory (treaty_engine's own real registry) — a second, genuine
    # multilateral treaty_coproduction opportunity now generates
    # alongside Eurimages, the same fail-closed pattern.
    #
    # LU Co-Pro Opportunity Trace: treaty structures grew again, 2 -> 25,
    # with the same generic fix that surfaces LU's real GB+AU opportunity
    # (see test_lu_australia_uk_bilateral_opportunity_surfaces_
    # independent_of_mauritius) — 23 real registered bilateral treaties
    # exist between pairs of FVD's own independently-discovered candidate
    # jurisdictions, none of which require Greece (FVD's home) to be a
    # party. This assertion is narrowed to the two HOME-ANCHORED
    # multilateral opportunities it always covered; the new bilateral
    # growth is verified separately below.
    multilateral = [e for e in treaty if e["treaty_slug"] in ("eurimages", "european-convention-coproduction")]
    assert len(multilateral) == 2
    by_slug = {e["treaty_slug"]: e for e in multilateral}
    assert set(by_slug) == {"eurimages", "european-convention-coproduction"}
    for e in multilateral:
        assert e["scenario_category"] == "CO_PRO_OPPORTUNITIES"
        assert e["treaty_resolution_state"] == "UNRESOLVED_FACTS"
        assert e["treaty_cultural_test_required"] is True
        assert e["treaty_cultural_test_resolved"] is False
        assert len(e["coproduction_partners"]) > 0
        for p in e["coproduction_partners"]:
            assert p["jurisdiction_display_name"] != p["jurisdiction_code"], (
                "co-pro partners must expose human-readable names, not raw codes"
            )

    bilateral_among_candidates = [e for e in treaty if e["treaty_slug"] not in by_slug]
    assert len(bilateral_among_candidates) == 23
    assert all(not e["is_directly_comparable"] for e in bilateral_among_candidates)
    assert all(e.get("npc_with_adjustments_usd") is None for e in bilateral_among_candidates)
    assert all("GR" not in [p["jurisdiction_code"] for p in e["coproduction_partners"]] for e in bilateral_among_candidates), (
        "these must be the candidate-pair opportunities (neither party is FVD's own "
        "home Greece) -- a GR-anchored pair belongs to the home-anchored loop, never here"
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
    treaty = [e for e in entries if e["structure_type"] == "treaty_coproduction"]
    assert treaty
    for t in treaty:
        assert t["npc_with_adjustments_usd"] is None
        assert t["selected_incentive_usd"] is None


async def test_little_utopia_home_anchored_treaty_opportunity_is_still_honestly_zero(db: AsyncSession):
    """Mauritius itself has zero bilateral treaties and is not a Eurimages
    member -- a real, honest zero for any HOME-ANCHORED treaty opportunity
    (i.e. one requiring Mauritius itself to be a treaty party), not a
    missing wire-up. Baseline remains unaffected.

    LU Co-Pro Opportunity Trace: this test used to assert `treaty == []`
    for ALL treaty_coproduction structures. That was itself a real, generic
    wiring defect: bilateral discovery only ever considered a treaty where
    the production's CURRENT service/location jurisdiction (Mauritius) was
    one of the two parties -- CineGlobe's product model is production-
    centric, not current-jurisdiction-centric, and a real registered treaty
    between two OTHER genuine candidate jurisdictions (e.g. GB+AU, matching
    this production's own real director/writer nationalities -- see
    test_lu_australia_uk_bilateral_opportunity_surfaces_independent_of_
    mauritius below) is a real structuring opportunity even when Mauritius
    is party to neither. Fixed generically in canonical_evaluation.py /
    canonical_treaty_bridge.find_bilateral_treaty_pairs_among_candidates --
    never an LU-specific branch. This test is narrowed to what remains
    genuinely, honestly zero: any structure requiring MAURITIUS ITSELF to
    be a treaty party."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    treaty = [e for e in entries if e["structure_type"] == "treaty_coproduction"]
    home_anchored = [
        e for e in treaty
        if "MU" in [p.get("jurisdiction_code") for p in (e.get("coproduction_partners") or [])]
    ]
    assert home_anchored == []
    baseline = next(e for e in entries if e["is_baseline"])
    assert round(baseline["npc_with_adjustments_usd"], 2) == 3812823.20  # Production Page Integrity Closeout (migration 0071): migration 0068's beta 100% contingency-utilization election was removed as stale. No election on file -> GREY_AREA_REQUIRES_AUTHORITY (never silently 0%/100%), reserve excluded from qualifying QPE until a producer sets it. Current canonical NPC reproduced via a real evaluate_project() call.


async def test_lu_australia_uk_bilateral_opportunity_surfaces_independent_of_mauritius(db: AsyncSession):
    """LU Co-Pro Opportunity Trace — the actual, verified defect: Little
    Utopia's real, persisted creative personnel are director=Kim Farrant
    (AU) and writer=Clara Salaman (GB) — a genuine UK/Australia creative
    combination. A real, registered uk-au-bilateral treaty exists in
    treaty_engine.py, and both GB and AU are independently discovered as
    real candidate jurisdictions for LU (relocation targets). The bilateral
    discovery function must surface this treaty as a real, disclosed
    (never priced, never fabricated-eligible) opportunity even though
    Mauritius — LU's current production/service jurisdiction — is party to
    neither side of the treaty. Genuine ownership-share facts are not on
    file, so eligibility correctly resolves UNRESOLVED_FACTS, never
    ELIGIBLE — this proves the STRUCTURE is considered, not that it
    qualifies."""
    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    treaty = [e for e in entries if e["structure_type"] == "treaty_coproduction"]
    uk_au = next((e for e in treaty if e.get("treaty_slug") == "uk-au-bilateral"), None)
    assert uk_au is not None, "GB+AU bilateral co-production opportunity did not surface for LU"
    partner_codes = {p.get("jurisdiction_code") for p in (uk_au.get("coproduction_partners") or [])}
    assert partner_codes == {"GB", "AU"}
    assert uk_au["treaty_resolution_state"] == "UNRESOLVED_FACTS"
    assert uk_au.get("npc_with_adjustments_usd") is None  # disclosed, never priced
    ranking = view["structures"]["allocated_structures"]["ranking"]
    uk_au_ranked = next((r for r in ranking if r["structure_id"] == uk_au["structure_id"]), None)
    assert uk_au_ranked is None or uk_au_ranked["rank"] is None  # never Recommended
