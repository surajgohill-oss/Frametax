"""Served-payload projections: the production view carried the same executable entries up to four times (optimizer_scenarios, optimizer_candidates,
evaluated_optimizer_alternatives and the recommended options), plus per-entry detail no reader uses, which put a synthetic production at 14.8 MB against the
8 MB bounded-payload contract. Consumers were traced before anything was removed:

* ``evaluated_optimizer_alternatives`` / ``recommended_optimizer_options`` / ``producer_optimizer_options`` / ``structures`` / ``best_per_jurisdiction`` /
  ``optimizer_opportunities_requiring_facts`` / ``top_by_structural_family`` are read by the frontend: they stay full entries.
* ``optimizer_scenarios`` is read by no code. It is the exact union of the recommended and evaluated lists (the evaluated list is "every scenario that is not
  recommended"), so it is served as a REFERENCE INDEX: structure id, identity and the recommendation annotation, the full entry living in those two lists.
* ``optimizer_candidates`` is read only to look a user-chosen leader up by id and to build the Globe snapshot, both of which use identity, topology, allocations and
  headline economics. It is served as a COMPACT projection (the bulky per-entry detail below is omitted; the same entry is complete in the lists above).
* ``top_by_structure_type`` has no reader; it is served as references.
* ``conditional_compatibility`` has no reader in the frontend or in any serve-time backend consumer; it is omitted from the served copies (it remains in the persisted
  trace the producer of each entry reads).

Nothing here changes an economics value, a count, the pagination (``candidates_page``), the ranking, or which candidates exist; a deterministic pure function of its input.
"""
from __future__ import annotations

#: Per-entry detail omitted from the COMPACT candidate projection (complete in the recommended / evaluated entries and the structures page).
CANDIDATE_DETAIL_KEYS = frozenset({
    "conditional_programs", "conditional_compatibility", "ceiling_basis", "ceiling_missing_facts", "warnings", "segments", "role_qualification",
    "opportunities", "conditional_scenario", "disclosed_limitations", "feasibility_reasons", "claim_base_missing_facts", "participant_qualifications",
    "raw_variant_economic_identities", "raw_variant_structure_ids", "dominance_reason", "allocation", "blockers",
})
#: Served nowhere: no frontend or serve-time reader.
UNREAD_KEYS = frozenset({"conditional_compatibility"})
#: Additionally omitted from the COLLECTION copies (not from the structures page, which stays the complete per-candidate record): no frontend reader and no serve-time
#: backend reader (only the entry's own producer and tests).
COLLECTION_UNREAD_KEYS = UNREAD_KEYS | frozenset({"participant_qualifications", "raw_variant_economic_identities", "conditional_scenario"})
_SCENARIO_REFERENCE_KEYS = (
    "structure_id", "economic_identity", "name", "label", "structure_type", "classification", "practicality_tier", "primary_jurisdiction", "anchor_jurisdiction",
    "participants", "claimed_program_ids", "candidate_status", "is_baseline", "is_fully_priced", "is_recommended", "recommendation_status", "recommendation_reason",
    "recommendation_threshold_usd", "jurisdiction_count", "participant_count", "savings_vs_current_usd", "confirmed_npc_usd", "npc_with_adjustments_usd",
    "raw_variant_structure_ids", "fit_priority", "scenario_category",
    "npc_verified_usd", "confirmed_incentive_floor_usd", "selected_incentive_usd", "raw_variant_count", "production_fit_status",
)
_CANDIDATE_EXTRA_KEYS = frozenset({
    "name", "label", "program_slugs", "claimed_program_ids", "classification", "candidate_status", "component_allocations", "coproduction_partners", "participants",
    "primary_jurisdiction", "anchor_jurisdiction", "practicality_tier", "recommendation_status", "recommendation_reason", "is_recommended", "savings_vs_current_usd",
    "jurisdiction_count", "recommendation_threshold_usd", "npc_verified_usd", "relocation_cost_normalized", "is_directly_comparable", "scenario_category",
})
_REFERENCE_NOTE = "reference row: the complete entry is in recommended_optimizer_options / evaluated_optimizer_alternatives (same structure_id)"


def _without(entry: dict, keys) -> dict:
    return {k: v for k, v in entry.items() if k not in keys}


def scenario_reference(entry: dict) -> dict:
    out = {k: entry[k] for k in _SCENARIO_REFERENCE_KEYS if k in entry}
    out["detail"] = _REFERENCE_NOTE
    return out


def candidate_projection(entry: dict) -> dict:
    """Identity, topology, allocations and headline economics: the fields a leader lookup and the Globe snapshot use (portfolio_globe_view.compact_structure's set), plus
    the recommendation annotation. Everything else is in the complete entries of the lists above."""
    from app.services.portfolio_globe_view import _STRUCTURE_FIELDS
    keep = set(_STRUCTURE_FIELDS) | _CANDIDATE_EXTRA_KEYS
    out = {k: v for k, v in entry.items() if k in keep and k not in CANDIDATE_DETAIL_KEYS}
    if isinstance(out.get("component_allocations"), list):      # the three fields compact_structure (the Globe snapshot) and a leader lookup use
        out["component_allocations"] = [{k: c.get(k) for k in ("component", "jurisdiction_code", "allocated_usd")} for c in out["component_allocations"] if isinstance(c, dict)]
    out["detail"] = _REFERENCE_NOTE
    return out


def apply_served_projections(allocated: dict) -> dict:
    """In place on the assembled allocated_structures block; returns it."""
    def strip(coll, keys=COLLECTION_UNREAD_KEYS):
        return [_without(e, keys) for e in coll]
    for key in ("evaluated_optimizer_alternatives", "recommended_optimizer_options", "producer_optimizer_options", "optimizer_opportunities_requiring_facts"):
        if isinstance(allocated.get(key), list):
            allocated[key] = strip(allocated[key])
    if isinstance(allocated.get("structures"), list):
        allocated["structures"] = strip(allocated["structures"], UNREAD_KEYS)
    if isinstance(allocated.get("unlockable_alternatives"), list):
        allocated["unlockable_alternatives"] = [candidate_projection(e) for e in allocated["unlockable_alternatives"]]
    if isinstance(allocated.get("best_per_jurisdiction"), dict):
        allocated["best_per_jurisdiction"] = {k: (_without(v, COLLECTION_UNREAD_KEYS) if isinstance(v, dict) else v) for k, v in allocated["best_per_jurisdiction"].items()}
    if isinstance(allocated.get("top_by_structural_family"), dict):
        allocated["top_by_structural_family"] = {k: strip(v) for k, v in allocated["top_by_structural_family"].items()}
    if isinstance(allocated.get("optimizer_scenarios"), list):
        allocated["optimizer_scenarios"] = [scenario_reference(e) for e in allocated["optimizer_scenarios"]]
    if isinstance(allocated.get("optimizer_candidates"), list):
        allocated["optimizer_candidates"] = [candidate_projection(e) for e in allocated["optimizer_candidates"]]
    if isinstance(allocated.get("top_by_structure_type"), dict):
        allocated["top_by_structure_type"] = {k: [scenario_reference(e) for e in v] for k, v in allocated["top_by_structure_type"].items()}
    allocated["served_projection"] = {
        "optimizer_scenarios": "reference index (full entries in recommended_optimizer_options + evaluated_optimizer_alternatives)",
        "optimizer_candidates": "compact projection (identity, topology, allocations and headline economics; bulky per-entry detail omitted)",
        "top_by_structure_type": "reference rows",
        "unlockable_alternatives": "compact projection",
        "omitted_from_served_copies": sorted(UNREAD_KEYS),
        "omitted_from_collection_copies": sorted(COLLECTION_UNREAD_KEYS),
    }
    return allocated
