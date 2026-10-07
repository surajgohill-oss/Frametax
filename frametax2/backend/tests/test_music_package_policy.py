"""Music / post-VFX package policy (canonical-1.105.0) -- synthetic fixtures, no database.

Canonical rule: Music stays inside the post/VFX/music package by default; routing Music separately is
surfaced only when its canonical NPC benefit over the correct bundled counterpart is at least $25,000.
Post/VFX and Music routed to one destination are ONE priced package leg (component
``post_vfx_music_package``), never two legs or a comparison-only value.
"""
from __future__ import annotations

from app.calculators.production_allocation import (
    POST_VFX_MUSIC_PACKAGE,
    StructureSpec,
    derive_account_allocation,
)
from app.calculators.qualification_derivation import BudgetLine
from app.services import canonical_evaluation as ce
from app.services.economic_identity import canonical_economic_identity
from app.services.music_carveout import (
    MUSIC_CARVEOUT_THRESHOLD_USD,
    NOT_MUSIC_SPLIT,
    SUPPRESSED_BELOW_THRESHOLD,
    SUPPRESSED_UNPROVEN,
    SURFACED,
    apply_music_carveout,
    music_carveout_decision,
)

LINES = [
    BudgetLine("2100", "Grip", 1000.0, "btl_crew_labor"),
    BudgetLine("3100", "VFX", 300.0, "vfx"),
    BudgetLine("3200", "Post", 400.0, "post_production"),
    BudgetLine("3300", "Score", 200.0, "music"),
]


def _destinations(routes: dict[str, str], participants=("XA", "YB", "ZC")) -> dict[str, str]:
    spec = StructureSpec(
        structure_id="s", structure_type="hybrid", label="s", primary_jurisdiction="XA",
        participants=participants, incentive_programs={p: f"{p.lower()}_prog" for p in participants},
        component_routes=routes,
    )
    return {a.account_code: a.jurisdiction_code for a in derive_account_allocation(LINES, {}, spec).assignments}


def test_same_destination_post_vfx_and_music_is_one_package_leg():
    got = _destinations({POST_VFX_MUSIC_PACKAGE: "YB"})
    assert got == {"2100": "XA", "3100": "YB", "3200": "YB", "3300": "YB"}
    # a VFX split out of the package keeps Post + Music together
    assert _destinations({POST_VFX_MUSIC_PACKAGE: "YB", "vfx": "ZC"}) == {"2100": "XA", "3100": "ZC", "3200": "YB", "3300": "YB"}


def test_unrelated_routes_are_unchanged():
    # routing only the post/VFX bundle still leaves Music with the principal; full relocation untouched
    assert _destinations({"post_vfx_package": "YB"}) == {"2100": "XA", "3100": "YB", "3200": "YB", "3300": "XA"}
    assert _destinations({"music_package": "ZC", "post_vfx_package": "YB"}) == {"2100": "XA", "3100": "YB", "3200": "YB", "3300": "ZC"}
    assert _destinations({}) == {"2100": "XA", "3100": "XA", "3200": "XA", "3300": "XA"}


def test_package_unit_never_combines_with_its_own_bundles():
    assert ce._hy_subset_admissible((POST_VFX_MUSIC_PACKAGE,))
    assert ce._hy_subset_admissible((POST_VFX_MUSIC_PACKAGE, "vfx"))
    assert not ce._hy_subset_admissible(("music_package", POST_VFX_MUSIC_PACKAGE))
    assert not ce._hy_subset_admissible((POST_VFX_MUSIC_PACKAGE, "post_vfx_package"))
    assert ce._hy_subset_admissible(("music_package", "post_vfx_package", "vfx"))


def test_same_destination_collisions_map_to_the_package_route():
    # with a package unit, any same-destination collision of package members IS a searched route
    assert ce._same_destination_kind(("music_package", "post_vfx_package"), ("YB", "YB"), package_active=True) == "same_destination_nested_bundle"
    assert ce._same_destination_kind(("music_package", "post_vfx_package", "vfx"), ("YB", "YB", "ZC"), package_active=True) == "same_destination_nested_bundle"
    assert ce._same_destination_kind(("post_vfx_package", "vfx"), ("YB", "YB"), package_active=False) == "same_destination_nested_bundle"
    assert ce._same_destination_kind(("music_package", "post_vfx_package"), ("YB", "YB"), package_active=False) == "same_destination_separate_bundles"


def _split(delta: float | None, npc: float = 1_000_000.0) -> dict:
    entry = {
        "structure_type": "hybrid", "npc_with_adjustments_usd": npc,
        "component_allocations": [{"component": "principal_production"}, {"component": "post_vfx_package"}, {"component": "music_package"}],
    }
    if delta is not None:
        entry["music_carveout"] = {"bundled_npc_with_adjustments_usd": npc + delta, "host_component": "post_vfx_package",
                                   "host_jurisdiction_code": "YB", "music_jurisdiction_code": "ZC"}
    return entry


def test_music_split_threshold_boundaries_are_exact():
    assert MUSIC_CARVEOUT_THRESHOLD_USD == 25_000.0
    assert music_carveout_decision(_split(24_999.99), None)["music_carveout_status"] == SUPPRESSED_BELOW_THRESHOLD
    assert music_carveout_decision(_split(25_000.0), None)["music_carveout_status"] == SURFACED
    assert music_carveout_decision(_split(25_000.01), None)["music_carveout_status"] == SURFACED
    assert music_carveout_decision(_split(-500.0), None)["music_carveout_status"] == SUPPRESSED_BELOW_THRESHOLD


def test_missing_bundled_comparator_fails_closed_and_stays_accounted():
    entry = _split(None)
    curated, suppressed, summary = apply_music_carveout([entry], None)
    assert curated == [] and suppressed == [entry]
    assert entry["music_carveout_status"] == SUPPRESSED_UNPROVEN and entry["music_carveout_reason"]
    assert summary["scenarios_before_curation_total"] == summary["curated_scenarios_total"] + summary["suppressed_total"] == 1


def test_package_structure_is_not_a_music_split_and_has_its_own_identity():
    package = {"structure_type": "hybrid", "npc_with_adjustments_usd": 1.0,
               "component_allocations": [{"component": "principal_production"}, {"component": POST_VFX_MUSIC_PACKAGE}]}
    assert music_carveout_decision(package, None)["music_carveout_status"] == NOT_MUSIC_SPLIT

    def trace(component, order=1):
        allocs = [{"component": "principal_production", "jurisdiction_code": "XA", "program_slug": "xa_prog"},
                  {"component": component, "jurisdiction_code": "YB", "program_slug": "yb_prog"}]
        return {"structural_family": "ordinary_component_hybrid", "anchor_jurisdiction": "XA",
                "component_allocations": allocs[::order]}
    # identical economic route -> identical identity, whatever the order it was discovered in
    assert canonical_economic_identity("hybrid", trace(POST_VFX_MUSIC_PACKAGE)) == canonical_economic_identity("hybrid", trace(POST_VFX_MUSIC_PACKAGE, -1))
    # the package leg and the post/VFX-only leg to the same destination are distinct economic structures
    assert canonical_economic_identity("hybrid", trace(POST_VFX_MUSIC_PACKAGE)) != canonical_economic_identity("hybrid", trace("post_vfx_package"))
