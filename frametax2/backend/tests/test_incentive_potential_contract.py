"""Focused tests for the served confirmed-floor / maximum-potential incentive contract
(app/services/incentive_potential.py). Pure: hand-built traces in the EXACT shape the
evaluator persists (canonical_evaluation._segment_dicts and hybrid component_allocations);
no DB, no evaluation."""
from __future__ import annotations

import random

from app.services.incentive_potential import (
    CEILING_CONDITIONAL,
    CEILING_CONFIRMED,
    CEILING_NOT_ESTABLISHED,
    CERTAINTY_CONDITIONAL,
    CERTAINTY_CONFIRMED,
    CERTAINTY_REFERENCE_ONLY,
    assign_incentive_potential_ranks,
    build_incentive_potential,
)

MB_CONDITIONS = [
    {"condition_id": "mb-frequent-filming", "description": "Frequent Filming Bonus (10%)",
     "kind": "regional_bonus", "condition_state": "USER_FACT_REQUIRED", "satisfied": None, "note": "n"},
    {"condition_id": "mb-edb-approval", "description": "Approval of the up-to rate by the authority",
     "kind": "discretionary_band", "condition_state": "AUTHORITY_UNRESOLVED", "satisfied": None, "note": "n"},
    {"condition_id": "mb-exclusive", "description": "Mutually exclusive alternative program",
     "kind": "mutually_exclusive_alternative_program", "condition_state": "DISCLOSURE_ONLY",
     "satisfied": None, "note": "n"},
]


def seg(code, slug, floor, ceiling, conditional, conditions=()):
    return {
        "jurisdiction_code": code, "program_slug": slug, "claims_incentive": True,
        "rate_floor": 0.45, "rate_ceiling": 0.65,
        "incentive_floor_usd": floor, "incentive_ceiling_usd": ceiling,
        "ceiling_requires_confirmation": conditional, "ceiling_conditions": list(conditions),
    }


def build(trace, selected, npc, **kw):
    return build_incentive_potential(
        trace, is_priced=True, selected_incentive_usd=selected, npc_with_adjustments_usd=npc, **kw
    )


def test_known_facts_produce_the_confirmed_floor_and_no_upside():
    # ceiling tier fully confirmed (ceiling_requires_confirmation False): the evaluator prices
    # the ceiling, so it IS the confirmed incentive and there is nothing conditional.
    t = {"segments": [seg("GR", "gr_cash_rebate", 1_000_000.0, 1_000_000.0, False)]}
    c = build(t, 1_000_000.0, 3_000_000.0)
    assert c["confirmed_incentive_floor_usd"] == 1_000_000.0
    assert c["maximum_supported_incentive_usd"] == 1_000_000.0
    assert c["ceiling_status"] == CEILING_CONFIRMED
    assert c["ceiling_missing_facts"] == []
    assert c["economics_certainty"] == CERTAINTY_CONFIRMED
    assert c["potential_npc_usd"] == c["confirmed_npc_usd"] == 3_000_000.0


def test_confirmed_band_ceiling_is_priced_at_the_ceiling_not_the_lower_tier():
    # band ceiling whose conditions are all satisfied: the evaluator selects the ceiling.
    t = {"segments": [seg("MU", "mu", 1_306_598.10, 1_742_130.80, False)]}
    c = build(t, 1_742_130.80, 2_000_000.0)
    assert c["confirmed_incentive_floor_usd"] == 1_742_130.80
    assert c["ceiling_status"] == CEILING_CONFIRMED


def test_missing_facts_cannot_enter_the_floor():
    t = {"segments": [seg("CA-MB", "ca_mb_film_video_credit", 27_705.6, 40_019.2, True, MB_CONDITIONS)]}
    c = build(t, 27_705.6, 500_000.0)
    assert c["confirmed_incentive_floor_usd"] == 27_705.6      # floor tier only
    assert c["maximum_supported_incentive_usd"] == 40_019.2    # conditional ceiling
    assert c["confirmed_incentive_floor_usd"] < c["maximum_supported_incentive_usd"]
    assert c["confirmed_npc_usd"] == 500_000.0                 # untouched by the ceiling


def test_supported_upper_tier_is_a_visibly_conditional_ceiling_with_specific_facts():
    t = {"segments": [seg("CA-MB", "ca_mb_film_video_credit", 27_705.6, 40_019.2, True, MB_CONDITIONS)]}
    c = build(t, 27_705.6, 500_000.0)
    assert c["ceiling_status"] == CEILING_CONDITIONAL
    assert c["economics_certainty"] == CERTAINTY_CONDITIONAL
    facts = c["ceiling_missing_facts"]
    # actionable facts first, disclosure-only noise excluded while actionable ones exist
    assert [f["fact_id"] for f in facts] == ["mb-frequent-filming", "mb-edb-approval"]
    assert [f["state"] for f in facts] == ["USER_FACT_REQUIRED", "AUTHORITY_UNRESOLVED"]
    assert all(f["program_slug"] == "ca_mb_film_video_credit" and f["jurisdiction_code"] == "CA-MB" for f in facts)
    assert all(f["unlocks_incentive_usd"] == round(40_019.2 - 27_705.6, 2) for f in facts)
    assert c["ceiling_basis"]["method"] == "SEGMENT_TIERS"
    assert c["ceiling_basis"]["legs"][0]["conditional"] is True


def test_conditional_leg_without_persisted_conditions_discloses_generically_never_invents():
    t = {"segments": [seg("MU", "mu", 100.0, 150.0, True, [])]}
    f = build(t, 100.0, 900.0)["ceiling_missing_facts"]
    assert len(f) == 1 and f[0]["fact_id"] == "CEILING_TIER_NOT_CONFIRMED"


def test_unsupported_ceilings_remain_absent():
    # no per-leg data persisted at all
    c = build({"segments": [], "component_allocations": []}, 100.0, 900.0)
    assert c["ceiling_status"] == CEILING_NOT_ESTABLISHED
    assert c["maximum_supported_incentive_usd"] is None and c["potential_npc_usd"] is None
    assert c["confirmed_incentive_floor_usd"] == 100.0 and c["confirmed_npc_usd"] == 900.0
    # hybrid component that persisted no ceiling (pre-contract generation)
    legacy = {"component_allocations": [{"program_slug": "x", "jurisdiction_code": "GR",
                                          "guaranteed_incentive_usd": 100.0}]}
    c = build(legacy, 100.0, 900.0)
    assert c["ceiling_status"] == CEILING_NOT_ESTABLISHED and c["maximum_supported_incentive_usd"] is None
    # legs that do not reconstruct the incentive priced into NPC AND carry conditional upside
    # (a structure-level adjustment whose effect on that upside is not persisted): fail closed
    c = build({"segments": [seg("GR", "gr", 50.0, 60.0, True, MB_CONDITIONS)]}, 100.0, 900.0)
    assert c["ceiling_status"] == CEILING_NOT_ESTABLISHED and c["maximum_supported_incentive_usd"] is None
    assert "do not reconcile" in c["ceiling_basis"]["note"]


def test_structure_level_adjustment_without_conditional_legs_cannot_move_the_maximum():
    # e.g. a federal credit reduced by a provincial stacking adjustment: legs sum to 414,459.70 but
    # 414,022.20 was priced; every leg is already at its ceiling, so the priced incentive is the max.
    t = {"component_allocations": [
        {"program_slug": "ca_federal_cptc", "jurisdiction_code": "CA", "guaranteed_incentive_usd": 369_526.5,
         "incentive_floor_usd": 369_526.5, "incentive_ceiling_usd": 369_526.5, "ceiling_requires_confirmation": False},
        {"program_slug": "on_ofttc", "jurisdiction_code": "CA-ON", "guaranteed_incentive_usd": 1_750.0,
         "incentive_floor_usd": 1_750.0, "incentive_ceiling_usd": 1_750.0, "ceiling_requires_confirmation": False},
        {"program_slug": "it", "jurisdiction_code": "IT", "guaranteed_incentive_usd": 43_183.2,
         "incentive_floor_usd": 43_183.2, "incentive_ceiling_usd": 43_183.2, "ceiling_requires_confirmation": False},
    ]}
    c = build(t, 414_022.2, 2_571_810.59)
    assert c["ceiling_status"] == CEILING_CONFIRMED
    assert c["maximum_supported_incentive_usd"] == c["confirmed_incentive_floor_usd"] == 414_022.2
    assert c["potential_npc_usd"] == c["confirmed_npc_usd"]


def test_unpriced_structure_is_reference_only_with_no_economics():
    c = build_incentive_potential({}, is_priced=False, selected_incentive_usd=None, npc_with_adjustments_usd=None)
    assert c["economics_certainty"] == CERTAINTY_REFERENCE_ONLY
    assert c["confirmed_incentive_floor_usd"] is None and c["maximum_supported_incentive_usd"] is None


def test_unresolved_legal_or_administrative_risk_is_conditional_never_confirmed():
    t = {"segments": [seg("GR", "gr", 100.0, 100.0, False)]}
    assert build(t, 100.0, 900.0, legal_review_required=True)["economics_certainty"] == CERTAINTY_CONDITIONAL
    assert build(t, 100.0, 900.0, administrative_allocation_risk=True)["economics_certainty"] == CERTAINTY_CONDITIONAL


def test_floor_is_never_greater_than_the_maximum_property():
    rng = random.Random(7)
    for _ in range(500):
        floor = round(rng.uniform(0, 1_000_000), 2)
        ceiling = round(floor + rng.choice([0.0, rng.uniform(0, 500_000)]), 2)
        cond = rng.random() < 0.5
        sel = floor if cond else ceiling
        c = build({"segments": [seg("XX", "p", floor, ceiling, cond)]}, sel, 5_000_000.0)
        assert c["confirmed_incentive_floor_usd"] <= c["maximum_supported_incentive_usd"]
        assert c["potential_npc_usd"] <= c["confirmed_npc_usd"]


def test_even_a_ceiling_below_the_floor_cannot_produce_a_maximum_below_the_floor():
    c = build({"segments": [seg("XX", "p", 200.0, 150.0, True)]}, 200.0, 900.0)
    assert c["maximum_supported_incentive_usd"] == 200.0 and c["ceiling_status"] == CEILING_CONFIRMED


def test_confirmed_and_potential_npc_reconstruct_from_the_same_identity():
    t = {"segments": [seg("CA-MB", "mb", 27_705.6, 40_019.2, True, MB_CONDITIONS),
                      seg("GR", "gr", 1_600_678.4, 1_600_678.4, False)]}
    sel = 27_705.6 + 1_600_678.4
    npc = 3_775_139.3
    c = build(t, sel, npc)
    gross_less_adjustments = npc + sel                       # NPC = X - incentive  =>  X = NPC + incentive
    assert c["confirmed_npc_usd"] == round(gross_less_adjustments - c["confirmed_incentive_floor_usd"], 2)
    assert c["potential_npc_usd"] == round(gross_less_adjustments - c["maximum_supported_incentive_usd"], 2)
    assert c["potential_upside_usd"] == round(c["maximum_supported_incentive_usd"] - c["confirmed_incentive_floor_usd"], 2)


def test_segment_aggregation_adds_only_conditional_upside_and_never_double_counts():
    # one conditional leg and one CONFIRMED leg that happens to have floor < ceiling: only the
    # conditional leg's uplift may be added; the confirmed leg stays at its priced value.
    t = {"segments": [seg("A", "a", 100.0, 160.0, True, MB_CONDITIONS),
                      seg("B", "b", 200.0, 260.0, False)]}
    c = build(t, 100.0 + 260.0, 10_000.0)
    assert c["confirmed_incentive_floor_usd"] == 360.0
    assert c["maximum_supported_incentive_usd"] == 420.0
    assert [l["conditional"] for l in c["ceiling_basis"]["legs"]] == [True, False]


def test_shared_qpe_stack_legs_use_adjusted_values_so_nothing_is_double_counted():
    # stack segments persist the stack engine's de-duplicated per-program adjusted values
    # (floor == ceiling); the maximum can never exceed what was priced.
    t = {"segments": [
        {"jurisdiction_code": "CA-ON", "program_slug": "on_ofttc", "incentive_floor_usd": 300.0,
         "incentive_ceiling_usd": 300.0},
        {"jurisdiction_code": "CA-ON", "program_slug": "on_ocase", "incentive_floor_usd": 80.0,
         "incentive_ceiling_usd": 80.0},
    ]}
    c = build(t, 380.0, 1_000.0)
    assert c["maximum_supported_incentive_usd"] == 380.0 and c["ceiling_status"] == CEILING_CONFIRMED


def test_hybrid_components_aggregate_from_actual_component_segments():
    t = {"component_allocations": [
        {"component": "vfx", "jurisdiction_code": "CA-MB", "program_slug": "ca_mb_film_video_credit",
         "guaranteed_incentive_usd": 23_625.0, "conditional_incentive_usd": 0.0,
         "incentive_floor_usd": 23_625.0, "incentive_ceiling_usd": 34_125.0,
         "ceiling_requires_confirmation": True, "ceiling_conditions": MB_CONDITIONS},
        {"component": "principal_production", "jurisdiction_code": "GR", "program_slug": "gr_cash_rebate",
         "guaranteed_incentive_usd": 1_600_678.4, "conditional_incentive_usd": 0.0,
         "incentive_floor_usd": 1_600_678.4, "incentive_ceiling_usd": 1_600_678.4,
         "ceiling_requires_confirmation": False, "ceiling_conditions": []},
    ]}
    sel = 23_625.0 + 1_600_678.4
    c = build(t, sel, 3_000_000.0)
    assert c["ceiling_basis"]["method"] == "COMPONENT_SEGMENT_TIERS"
    assert c["confirmed_incentive_floor_usd"] == round(sel, 2)
    assert c["maximum_supported_incentive_usd"] == round(sel + 10_500.0, 2)
    assert c["ceiling_status"] == CEILING_CONDITIONAL
    assert {f["jurisdiction_code"] for f in c["ceiling_missing_facts"]} == {"CA-MB"}


def test_confirmed_rank_is_distinct_from_potential_opportunity_rank():
    a = {"structure_id": "a", "economic_identity": "a", "confirmed_npc_usd": 100.0, "potential_npc_usd": 95.0}
    b = {"structure_id": "b", "economic_identity": "b", "confirmed_npc_usd": 110.0, "potential_npc_usd": 60.0}
    c = {"structure_id": "c", "economic_identity": "c", "confirmed_npc_usd": 120.0, "potential_npc_usd": None}
    scen = [a, b, c]
    assign_incentive_potential_ranks(scen)
    assert (a["confirmed_financial_rank"], b["confirmed_financial_rank"], c["confirmed_financial_rank"]) == (1, 2, 3)
    assert (b["potential_opportunity_rank"], a["potential_opportunity_rank"]) == (1, 2)
    assert c["potential_opportunity_rank"] is None
    assert [e["structure_id"] for e in scen] == ["a", "b", "c"]  # no scenario reordered or removed


def _fvd_hybrid(co_ceiling=4_000.0, adjusted_pair=("ca_federal_cptc", "on_ofttc")):
    # The real FVD shape: CPTC 502,327.25 + OFTTC 3,570 are reduced by a canonical stacking
    # adjustment (-892.50, persisted as post_adjustment_component_incentives_usd); Colombia has a
    # conditional ceiling (3,500 -> 4,000); Italy is plain.
    return {
        "component_allocations": [
            {"component": "principal_production", "jurisdiction_code": "CA", "program_slug": "ca_federal_cptc",
             "guaranteed_incentive_usd": 502_327.25, "incentive_floor_usd": 502_327.25,
             "incentive_ceiling_usd": 502_327.25, "ceiling_requires_confirmation": False},
            {"component": "music_package", "jurisdiction_code": "CA-ON", "program_slug": "on_ofttc",
             "guaranteed_incentive_usd": 3_570.0, "incentive_floor_usd": 3_570.0,
             "incentive_ceiling_usd": 3_570.0, "ceiling_requires_confirmation": False},
            {"component": "x", "jurisdiction_code": "CO", "program_slug": "co_film_in_colombia",
             "guaranteed_incentive_usd": 3_500.0, "incentive_floor_usd": 3_500.0,
             "incentive_ceiling_usd": co_ceiling, "ceiling_requires_confirmation": True,
             "ceiling_conditions": MB_CONDITIONS[:1]},
            {"component": "post_vfx_package", "jurisdiction_code": "IT", "program_slug": "it_tax_credit_foreign",
             "guaranteed_incentive_usd": 58_578.4, "incentive_floor_usd": 58_578.4,
             "incentive_ceiling_usd": 58_578.4, "ceiling_requires_confirmation": False},
        ],
        "post_adjustment_component_incentives_usd": {
            "ca_federal_cptc": 502_327.25, "on_ofttc": 2_677.5, "co_film_in_colombia": 3_500.0,
            "it_tax_credit_foreign": 58_578.4,
        },
        "stacking_adjustments": [{"program_a_id": adjusted_pair[0], "program_b_id": adjusted_pair[1],
                                  "rule_type": "spend_reduction", "adjustment_usd": -892.5}],
    }


def test_persisted_stacking_adjustment_makes_the_fvd_hybrid_reconcile():
    c = build(_fvd_hybrid(), 567_083.15, 2_500_000.0)
    assert c["ceiling_status"] == CEILING_CONDITIONAL
    assert c["confirmed_incentive_floor_usd"] == 567_083.15
    assert c["maximum_supported_incentive_usd"] == 567_583.15   # + Colombia's own 500 uplift only
    assert [f["jurisdiction_code"] for f in c["ceiling_missing_facts"]] == ["CO"]


def test_conditional_leg_touched_by_an_adjustment_is_not_established_with_the_exact_leg():
    t = _fvd_hybrid(adjusted_pair=("on_ofttc", "co_film_in_colombia"))
    c = build(t, 567_083.15, 2_500_000.0)
    assert c["ceiling_status"] == CEILING_NOT_ESTABLISHED and c["maximum_supported_incentive_usd"] is None
    assert c["ceiling_basis"]["blocked_legs"] == [
        {"jurisdiction_code": "CO", "program_slug": "co_film_in_colombia", "component": "x"}]
    assert "CO/co_film_in_colombia" in c["ceiling_basis"]["note"]
