"""Served-payload projections (8 MB bounded-payload contract): coverage, economics and determinism are preserved while the three-fold duplication is removed.
DB-free: a synthetic allocated block is projected and compared with its source."""
from __future__ import annotations

import copy
import json

from app.services.served_payload_projection import (
    CANDIDATE_DETAIL_KEYS, COLLECTION_UNREAD_KEYS, UNREAD_KEYS, apply_served_projections, candidate_projection, scenario_reference)


def _entry(i, status="BELOW_THRESHOLD"):
    return {
        "structure_id": f"s{i}", "economic_identity": f"id{i}", "name": f"n{i}", "structure_type": "hybrid", "classification": "HYBRID_ANCHOR_COMPONENT",
        "practicality_tier": "PRACTICAL_HYBRID", "primary_jurisdiction": "GB", "participants": ["MU", "GB"], "claimed_program_ids": ["mu", "gb"],
        "candidate_status": "PRICED", "is_fully_priced": True, "recommendation_status": status, "is_recommended": status == "RECOMMENDED",
        "npc_verified_usd": 1_000_000.0 + i, "confirmed_npc_usd": 1_000_000.0 + i, "confirmed_incentive_floor_usd": 250_000.0, "raw_variant_count": 1,
        "raw_variant_structure_ids": [f"s{i}"], "fit_priority": 1,
        "component_allocations": [{"component": "post", "jurisdiction_code": "GB", "allocated_usd": 100.0, "line_ids": ["a", "b"], "rationale": "x" * 500}],
        "coproduction_partners": [], "segments": [{"x": "y" * 800}], "conditional_programs": [{"p": "q" * 800}], "conditional_compatibility": {"c": "d" * 800},
        "warnings": ["w" * 300], "ceiling_basis": {"k": "v" * 300}, "ceiling_missing_facts": ["m"], "participant_qualifications": [{"z": "z" * 300}],
        "raw_variant_economic_identities": [f"id{i}"], "role_qualification": {"r": "r" * 200}, "conditional_scenario": None,
    }


def _allocated(n=6):
    entries = [_entry(i, "RECOMMENDED" if i < 2 else "BELOW_THRESHOLD") for i in range(n)]
    return {
        "structures": [copy.deepcopy(entries[0])], "optimizer_scenarios": copy.deepcopy(entries), "optimizer_candidates": copy.deepcopy(entries),
        "recommended_optimizer_options": copy.deepcopy(entries[:2]), "producer_optimizer_options": copy.deepcopy(entries[:2]),
        "evaluated_optimizer_alternatives": copy.deepcopy(entries[2:]), "optimizer_opportunities_requiring_facts": [copy.deepcopy(entries[0])],
        "best_per_jurisdiction": {"GB": copy.deepcopy(entries[0])}, "top_by_structural_family": {"HYBRID_ANCHOR_COMPONENT": copy.deepcopy(entries[:2])},
        "top_by_structure_type": {"hybrid": copy.deepcopy(entries[:3])}, "unlockable_alternatives": copy.deepcopy(entries[:2]),
    }


def test_the_scenario_index_covers_exactly_the_union_of_recommended_and_evaluated_entries_with_their_economics():
    a = apply_served_projections(_allocated())
    index = {r["structure_id"]: r for r in a["optimizer_scenarios"]}
    full = {e["structure_id"]: e for e in a["recommended_optimizer_options"] + a["evaluated_optimizer_alternatives"]}
    assert set(index) == set(full) and len(a["optimizer_scenarios"]) == len(full)
    for sid, ref in index.items():
        for key in ("economic_identity", "recommendation_status", "npc_verified_usd", "confirmed_incentive_floor_usd", "raw_variant_structure_ids", "classification"):
            assert ref[key] == full[sid][key], (sid, key)
        assert "segments" not in ref and "conditional_programs" not in ref


def test_the_compact_candidate_projection_keeps_every_candidate_its_identity_topology_allocations_and_headline_economics():
    src = _allocated()
    a = apply_served_projections(copy.deepcopy(src))
    assert [c["structure_id"] for c in a["optimizer_candidates"]] == [c["structure_id"] for c in src["optimizer_candidates"]]
    for before, after in zip(src["optimizer_candidates"], a["optimizer_candidates"]):
        for key in ("economic_identity", "classification", "candidate_status", "is_fully_priced", "npc_verified_usd", "participants", "primary_jurisdiction"):
            assert after[key] == before[key]
        assert after["component_allocations"] == [{"component": "post", "jurisdiction_code": "GB", "allocated_usd": 100.0}]
        assert not (set(after) & CANDIDATE_DETAIL_KEYS)


def test_the_lists_the_frontend_reads_keep_every_entry_and_every_economics_and_detail_value_except_the_unread_keys():
    src = _allocated()
    a = apply_served_projections(copy.deepcopy(src))
    for name, dropped in (("evaluated_optimizer_alternatives", COLLECTION_UNREAD_KEYS), ("recommended_optimizer_options", COLLECTION_UNREAD_KEYS),
                          ("producer_optimizer_options", COLLECTION_UNREAD_KEYS), ("optimizer_opportunities_requiring_facts", COLLECTION_UNREAD_KEYS),
                          ("structures", UNREAD_KEYS)):
        assert a[name] == [{k: v for k, v in e.items() if k not in dropped} for e in src[name]], name
    assert a["best_per_jurisdiction"]["GB"] == {k: v for k, v in src["best_per_jurisdiction"]["GB"].items() if k not in COLLECTION_UNREAD_KEYS}
    entries = (a["structures"] + a["optimizer_candidates"] + a["recommended_optimizer_options"] + a["evaluated_optimizer_alternatives"] + a["unlockable_alternatives"]
               + a["optimizer_opportunities_requiring_facts"] + list(a["best_per_jurisdiction"].values()) + a["top_by_structural_family"]["HYBRID_ANCHOR_COMPONENT"])
    assert all("conditional_compatibility" not in e for e in entries), "the unread key is gone from every served entry"
    assert all("segments" in e and "conditional_programs" in e for e in a["evaluated_optimizer_alternatives"])


def test_the_projection_is_pure_and_deterministic_and_materially_smaller():
    src = _allocated(40)
    snapshot = copy.deepcopy(src)
    one = apply_served_projections(copy.deepcopy(src))
    two = apply_served_projections(copy.deepcopy(src))
    assert json.dumps(one, sort_keys=True) == json.dumps(two, sort_keys=True)
    assert scenario_reference(src["optimizer_scenarios"][0]) == scenario_reference(src["optimizer_scenarios"][0]) and src == snapshot
    assert candidate_projection(src["optimizer_candidates"][0]) == candidate_projection(src["optimizer_candidates"][0]) and src == snapshot
    assert len(json.dumps(one)) < 0.6 * len(json.dumps(src))
