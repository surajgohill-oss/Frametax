"""Served-payload projections (8 MB bounded-payload contract): coverage, economics and determinism are preserved while the three-fold duplication is removed.
DB-free: a synthetic allocated block is projected and compared with its source."""
from __future__ import annotations

import copy
import json

from app.services.served_payload_projection import (
    CANDIDATE_DETAIL_KEYS, COLLECTION_UNREAD_KEYS, UNREAD_KEYS, WINNER_OMITTED_KEYS, apply_served_projections, candidate_projection, scenario_reference)


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
    complete = apply_served_projections(copy.deepcopy(src), compact_winners=False)["best_per_jurisdiction"]["GB"]
    assert complete == {k: v for k, v in src["best_per_jurisdiction"]["GB"].items() if k not in COLLECTION_UNREAD_KEYS}, "the on-demand winner is the complete entry"
    compact = a["best_per_jurisdiction"]["GB"]
    assert {k: v for k, v in compact.items() if k != "detail_omitted"} == {k: v for k, v in complete.items() if k not in WINNER_OMITTED_KEYS}, "only the named detail is omitted"
    assert compact["detail_omitted"] == sorted(WINNER_OMITTED_KEYS & complete.keys())
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


# ── bounded pages of the optimizer lists: no unbounded initial response, every entry reachable ──────────────────────────────────────────────────────────

import random

from app.services.served_payload_projection import OPTIMIZER_LIST_PAGE_LIMIT, page_optimizer_lists


def _big(n, seed=3):
    rng = random.Random(seed)
    entries = []
    for i in range(n):
        e = _entry(i, rng.choice(["EVALUATED_ALTERNATIVE", "NEUTRAL", "COSTS_MORE"]))
        e.update(savings_vs_current_usd=rng.choice([None, rng.uniform(-5e5, 5e5)]), npc_verified_usd=rng.uniform(1e6, 3e6), fit_priority=rng.choice([1, 2, 3, None]),
                 dominance_status=rng.choice(["DOMINATED", "NON_DOMINATED"]))
        entries.append(e)
    return {"evaluated_optimizer_alternatives": entries, "optimizer_candidates": copy.deepcopy(entries), "optimizer_scenarios": copy.deepcopy(entries),
            "recommended_optimizer_options": [], "producer_optimizer_options": [], "optimizer_opportunities_requiring_facts": copy.deepcopy(entries[:120]),
            "optimizer_scenarios_music_suppressed": copy.deepcopy(entries)}


def test_the_initial_response_is_bounded_whatever_the_universe_and_every_entry_is_reachable_exactly_once():
    small, large = _big(300), _big(6000)
    p_small, p_large = page_optimizer_lists(copy.deepcopy(small), fingerprint="f" * 64), page_optimizer_lists(copy.deepcopy(large), fingerprint="f" * 64)
    assert len(p_large["evaluated_optimizer_alternatives"]) == OPTIMIZER_LIST_PAGE_LIMIT and p_large["evaluated_optimizer_alternatives_page"]["total"] == 6000
    assert len(json.dumps(p_large)) < 1.05 * len(json.dumps(p_small)), "the initial response does not grow with the universe"
    ids = []
    offset = 0
    while True:
        page = page_optimizer_lists(copy.deepcopy(large), fingerprint="f" * 64, offsets={"evaluated_optimizer_alternatives": offset})
        ids += [e["structure_id"] for e in page["evaluated_optimizer_alternatives"]]
        meta = page["evaluated_optimizer_alternatives_page"]
        if not meta["has_more"]:
            break
        offset += OPTIMIZER_LIST_PAGE_LIMIT
    assert len(ids) == 6000 and len(set(ids)) == 6000, "every entry exactly once across the pages"
    sup = p_large["optimizer_scenarios_music_suppressed"]
    assert len(sup) == OPTIMIZER_LIST_PAGE_LIMIT and p_large["optimizer_scenarios_music_suppressed_page"]["total"] == 6000, "the policy-suppressed list is paged too"
    assert [e["structure_id"] for e in sup] == [e["structure_id"] for e in large["optimizer_scenarios_music_suppressed"][:OPTIMIZER_LIST_PAGE_LIMIT]], "served order kept"


def test_the_page_order_is_the_frontends_order_so_the_first_page_is_the_head_of_what_the_producer_sees():
    entries = _big(400)["evaluated_optimizer_alternatives"]
    page = page_optimizer_lists({"evaluated_optimizer_alternatives": copy.deepcopy(entries)}, fingerprint="a" * 64)["evaluated_optimizer_alternatives"]
    inf = float("inf")
    rank = {"EVALUATED_ALTERNATIVE": 0, "NEUTRAL": 1, "COSTS_MORE": 2}
    expected = sorted(entries, key=lambda e: (e["fit_priority"] if e["fit_priority"] is not None else 2, rank[e["recommendation_status"]], 1 if e["dominance_status"] == "DOMINATED" else 0,
                                              inf if e["savings_vs_current_usd"] is None else -e["savings_vs_current_usd"], e["npc_verified_usd"], e["economic_identity"]))
    assert [e["structure_id"] for e in page] == [e["structure_id"] for e in expected[:OPTIMIZER_LIST_PAGE_LIMIT]]


def test_the_saved_leader_is_always_in_the_candidate_page_and_pages_are_deterministic_and_bound_to_a_generation():
    data = _big(500)
    leader = data["optimizer_candidates"][-1]["structure_id"]
    a = page_optimizer_lists(copy.deepcopy(data), fingerprint="b" * 64, pin_ids=frozenset({leader}))
    assert leader in {e["structure_id"] for e in a["optimizer_candidates"]} and a["optimizer_candidates_page"]["pinned"] in (0, 1)
    b = page_optimizer_lists(copy.deepcopy(data), fingerprint="b" * 64, pin_ids=frozenset({leader}))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    other = page_optimizer_lists(copy.deepcopy(data), fingerprint="c" * 64)
    assert a["evaluated_optimizer_alternatives_page"]["next_cursor"] != other["evaluated_optimizer_alternatives_page"]["next_cursor"]


def test_a_compact_winner_keeps_every_segment_value_except_the_trace_and_points_at_it():
    seg = {"jurisdiction_code": "GB", "qpe_usd": 5.0, "incentive_floor_usd": 1.0, "qualification_trace": [{"account_code": "1100", "state": "OK"}] * 3, "statutory_basis": "s. 1"}
    winner = {**_entry(0), "segments": [copy.deepcopy(seg), {"jurisdiction_code": "MU", "qpe_usd": 2.0}]}
    out = apply_served_projections({"best_per_jurisdiction": {"GB": winner}})["best_per_jurisdiction"]["GB"]
    assert "qualification_trace" in winner["segments"][0], "the source is not mutated"
    assert out["segments"][0] == {**{k: v for k, v in seg.items() if k != "qualification_trace"}, "qualification_trace_omitted": 3,
                                  "detail_ref": {"kind": "jurisdiction_winner", "code": "GB", "segment_index": 0}}
    assert out["segments"][1] == {"jurisdiction_code": "MU", "qpe_usd": 2.0}, "a segment without a trace is untouched"
    assert "segments[].qualification_trace" in out["detail_omitted"]
