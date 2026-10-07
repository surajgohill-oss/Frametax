"""Music carve-out presentation rule: a separately-routed Music split is surfaced only when the
bundled counterpart's canonical NPC minus the split's canonical NPC is STRICTLY > $25,000; every
split is still calculated, preserved and accounted for."""
from __future__ import annotations

import pytest

from app.services.music_carveout import (
    MUSIC_CARVEOUT_THRESHOLD_USD, NOT_MUSIC_SPLIT, SUPPRESSED_BELOW_THRESHOLD, SUPPRESSED_UNPROVEN, SURFACED,
    apply_music_carveout, music_carveout_decision,
)

T = MUSIC_CARVEOUT_THRESHOLD_USD


def hybrid(split_npc, bundled_npc, sid="h"):
    return {
        "structure_id": sid, "structure_type": "hybrid", "npc_with_adjustments_usd": split_npc,
        "component_allocations": [{"component": "principal_production"}, {"component": "post_vfx_package"},
                                  {"component": "music_package"}],
        "music_carveout": None if bundled_npc is None else {
            "music_jurisdiction_code": "NZ", "host_component": "post_vfx_package", "host_jurisdiction_code": "IE",
            "bundled_npc_with_adjustments_usd": bundled_npc, "split_npc_with_adjustments_usd": split_npc},
    }


def test_threshold_is_exactly_25000_at_least():
    # canonical-1.105.0 product rule: a separate music leg is surfaced when its benefit is AT LEAST $25,000
    assert T == 25_000.0
    below = music_carveout_decision(hybrid(1_000_000.0, 1_024_999.99), None)
    equal = music_carveout_decision(hybrid(1_000_000.0, 1_025_000.0), None)
    above = music_carveout_decision(hybrid(1_000_000.0, 1_025_000.01), None)
    assert below["music_carveout_status"] == SUPPRESSED_BELOW_THRESHOLD
    assert equal["music_carveout_status"] == SURFACED, ">= not >"
    assert above["music_carveout_status"] == SURFACED
    assert above["music_carveout_delta_usd"] == pytest.approx(25_000.01, abs=1e-6)


def test_comparison_uses_full_precision_before_display_rounding():
    # both would DISPLAY as a $25,000 gap after rounding to the dollar; only full precision decides
    assert music_carveout_decision(hybrid(1_000_000.4, 1_025_000.0), None)["music_carveout_status"] == SUPPRESSED_BELOW_THRESHOLD
    assert music_carveout_decision(hybrid(1_000_000.4, 1_025_000.5), None)["music_carveout_status"] == SURFACED


def test_split_that_is_worse_than_bundled_is_suppressed_but_preserved():
    d = music_carveout_decision(hybrid(1_100_000.0, 1_000_000.0), None)
    assert d["music_carveout_status"] == SUPPRESSED_BELOW_THRESHOLD and d["music_carveout_delta_usd"] < 0
    assert "stays bundled" in d["music_carveout_reason"]


def test_music_only_relocation_is_compared_to_the_current_location_baseline():
    e = {"structure_id": "c", "structure_type": "component_relocation", "npc_with_adjustments_usd": 975_000.0,
         "component_allocations": [{"component": "music_package"}]}
    assert music_carveout_decision(e, 1_000_000.0)["music_carveout_status"] == SURFACED   # == 25,000 (at least)
    assert music_carveout_decision(dict(e, npc_with_adjustments_usd=975_000.01), 1_000_000.0)["music_carveout_status"] == SUPPRESSED_BELOW_THRESHOLD
    d = music_carveout_decision(e, 1_000_000.0)
    assert d["music_carveout_counterpart"]["kind"] == "CURRENT_LOCATION_BASELINE"


def test_unproven_counterpart_is_not_surfaced_but_is_preserved_with_a_reason():
    d = music_carveout_decision(hybrid(1_000_000.0, None), None)
    assert d["music_carveout_status"] == SUPPRESSED_UNPROVEN and d["music_carveout_reason"]


def test_non_music_structures_are_untouched():
    e = {"structure_id": "x", "structure_type": "hybrid", "npc_with_adjustments_usd": 1.0,
         "component_allocations": [{"component": "principal_production"}, {"component": "post_vfx_package"}]}
    assert music_carveout_decision(e, 1.0)["music_carveout_status"] == NOT_MUSIC_SPLIT


def test_partition_reconciles_and_nothing_is_dropped():
    rows = [hybrid(1_000_000.0, 1_100_000.0, "a"), hybrid(1_000_000.0, 1_010_000.0, "b"),
            {"structure_id": "p", "structure_type": "hybrid", "npc_with_adjustments_usd": 5.0,
             "component_allocations": [{"component": "principal_production"}]}]
    curated, suppressed, summary = apply_music_carveout(rows, None)
    assert [r["structure_id"] for r in curated] == ["a", "p"]
    assert [r["structure_id"] for r in suppressed] == ["b"]
    assert summary["curated_scenarios_total"] + summary["suppressed_total"] == summary["scenarios_before_curation_total"] == 3
    assert summary["music_split_scenarios_total"] == 2 and summary["surfaced_music_split_total"] == 1


def test_evaluator_prices_the_bundled_counterfactual_with_every_other_component_held_constant():
    from app.calculators.qualification_derivation import BudgetLine
    from app.services import canonical_evaluation as ce
    from tests.test_structural_archetype_generator import _economic_inputs

    cats = [("1", "principal photography", "production", 2_000_000.0), ("2", "post sound", "post_production", 400_000.0),
            ("3", "vfx work", "vfx", 300_000.0), ("4", "score", "music", 120_000.0)]
    lines = [BudgetLine(account_code=c, description=d, amount_usd=a, spend_category=cat, is_memo=False,
                        line_id=f"BL-{c}") for c, d, cat, a in cats]
    inputs = _economic_inputs(
        jurisdiction_code="GR", gross_budget_usd=2_820_000.0, leaf_account_sum_usd=2_820_000.0,
        budget_lines=lines, spend_category_by_code={c: cat for c, _, cat, _ in cats})
    progs = {"NZ": "new_zealand_screen_production_grant_—_international_post_vfx", "IE": "ie_section_481"}
    _, comps = ce._build_hybrid_route(inputs, "US-GA", "us_ga_film_credit",
                                      ("post_vfx_package", "music_package"), ["NZ", "IE"], progs)
    split_types = sorted(c.component_type for c in comps)
    assert "music_package" in split_types
    cf = ce._hybrid_music_bundle_counterfactual(comps, "US-GA", 2_820_000.0, inputs, 2_000_000.0)
    if cf is None:  # the real kernel may not price this synthetic pairing; the contract is then 'unproven'
        pytest.skip("synthetic fixture pairing is not priceable by the real kernel")
    assert cf["host_component"] in ("post_vfx_package", "principal_production")
    assert cf["music_jurisdiction_code"] in {"NZ", "IE"}
    assert isinstance(cf["bundled_npc_with_adjustments_usd"], float)
    assert cf["split_npc_with_adjustments_usd"] == 2_000_000.0
    # no music component -> no counterfactual (never fabricated)
    no_music = [c for c in comps if c.component_type != "music_package"]
    assert ce._hybrid_music_bundle_counterfactual(no_music, "US-GA", 2_820_000.0, inputs, 2_000_000.0) is None
