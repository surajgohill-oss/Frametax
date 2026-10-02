"""MUSIC CARVE-OUT PRESENTATION RULE (2026-10-01) -- a CURATED-SURFACE projection, never a change
to what is generated, priced, retained or accounted for.

Every Music-split scenario is still calculated and persisted. A scenario that routes Music to a
separate jurisdiction is surfaced in the curated optimizer output only when

    canonical NPC of the otherwise-identical structure with Music BUNDLED with Post/VFX
  - canonical NPC of the Music-split structure                       >  $25,000   (strictly greater)

Both NPCs are the full-precision canonical ``npc_with_adjustments_usd`` (travel, FX, local cost,
stacking, financing and structural adjustments included); the comparison happens before any display
rounding. A split that does not clear the bar is not deleted: it moves to the served
``optimizer_scenarios_music_suppressed`` list (full entries, for later Build-Your-Own matching by
stable economic identity) and the totals reconcile (curated + suppressed == scenarios before).

Counterparts, all read from persisted canonical values:
  * hybrid with a music_package component  -> trace["music_carveout"] (the evaluator's repriced
    bundled counterfactual; see canonical_evaluation._hybrid_music_bundle_counterfactual)
  * component_relocation that routes ONLY music -> the anchor baseline (nothing routed), i.e. the
    production's current-location NPC
  * any other family -> not a music split; untouched.
A music split whose bundled counterpart cannot be established is NOT surfaced (the rule admits a
split only on proof) but is preserved, with the exact reason.
"""
from __future__ import annotations

MUSIC_CARVEOUT_THRESHOLD_USD = 25_000.0

NOT_MUSIC_SPLIT = "NOT_MUSIC_SPLIT"
SURFACED = "SURFACED"
SUPPRESSED_BELOW_THRESHOLD = "SUPPRESSED_BELOW_THRESHOLD"
SUPPRESSED_UNPROVEN = "SUPPRESSED_COUNTERPART_NOT_ESTABLISHED"


def _components(entry: dict) -> list[str]:
    return [c.get("component") for c in (entry.get("component_allocations") or [])]


def music_carveout_decision(entry: dict, baseline_npc_usd: float | None) -> dict:
    comps = _components(entry)
    base = {
        "music_carveout_status": NOT_MUSIC_SPLIT,
        "music_carveout_delta_usd": None,
        "music_carveout_threshold_usd": MUSIC_CARVEOUT_THRESHOLD_USD,
        "music_carveout_counterpart": None,
        "music_carveout_reason": None,
    }
    if "music_package" not in comps:
        return base
    split_npc = entry.get("npc_with_adjustments_usd")
    stype = entry.get("structure_type")
    counterpart = None
    bundled_npc = None
    if stype == "hybrid":
        cf = entry.get("music_carveout")
        if isinstance(cf, dict) and cf.get("bundled_npc_with_adjustments_usd") is not None:
            bundled_npc = float(cf["bundled_npc_with_adjustments_usd"])
            counterpart = {
                "kind": "BUNDLED_REPRICED_COUNTERFACTUAL",
                "host_component": cf.get("host_component"),
                "host_jurisdiction_code": cf.get("host_jurisdiction_code"),
                "music_jurisdiction_code": cf.get("music_jurisdiction_code"),
                "bundled_npc_with_adjustments_usd": bundled_npc,
            }
    elif stype == "component_relocation" and set(comps) == {"music_package"}:
        if baseline_npc_usd is not None:
            bundled_npc = float(baseline_npc_usd)
            counterpart = {
                "kind": "CURRENT_LOCATION_BASELINE",
                "bundled_npc_with_adjustments_usd": bundled_npc,
            }
    else:
        return base
    if split_npc is None or bundled_npc is None:
        base.update({
            "music_carveout_status": SUPPRESSED_UNPROVEN,
            "music_carveout_reason": (
                "The otherwise-identical Music-bundled structure's canonical NPC is not established for this "
                "split, so it is not surfaced as a separate default leg (the scenario is preserved)."
            ),
        })
        return base
    delta = bundled_npc - float(split_npc)
    surfaced = delta > MUSIC_CARVEOUT_THRESHOLD_USD       # strictly greater; no rounding before compare
    base.update({
        "music_carveout_status": SURFACED if surfaced else SUPPRESSED_BELOW_THRESHOLD,
        "music_carveout_delta_usd": delta,
        "music_carveout_counterpart": counterpart,
        "music_carveout_reason": None if surfaced else (
            f"Splitting Music into its own jurisdiction improves canonical NPC by ${delta:,.2f}, which does not "
            f"exceed the ${MUSIC_CARVEOUT_THRESHOLD_USD:,.0f} carve-out threshold; Music stays bundled with Post/VFX."
        ),
    })
    return base


def apply_music_carveout(scenarios: list[dict], baseline_npc_usd: float | None) -> tuple[list[dict], list[dict], dict]:
    """Annotate every scenario and partition it into (curated, suppressed, summary). Order within each
    list is preserved; nothing is dropped."""
    curated: list[dict] = []
    suppressed: list[dict] = []
    split_total = 0
    for e in scenarios:
        d = music_carveout_decision(e, baseline_npc_usd)
        e.update(d)
        if d["music_carveout_status"] != NOT_MUSIC_SPLIT:
            split_total += 1
        (suppressed if d["music_carveout_status"] in (SUPPRESSED_BELOW_THRESHOLD, SUPPRESSED_UNPROVEN) else curated).append(e)
    summary = {
        "threshold_usd": MUSIC_CARVEOUT_THRESHOLD_USD,
        "comparison": "strictly_greater_than",
        "music_split_scenarios_total": split_total,
        "surfaced_music_split_total": split_total - len(suppressed),
        "suppressed_total": len(suppressed),
        "scenarios_before_curation_total": len(scenarios),
        "curated_scenarios_total": len(curated),
    }
    return curated, suppressed, summary
