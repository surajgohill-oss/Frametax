"""
Tests for generate_structure_scenarios.py

Covers:
  - correct number of scenarios generated from candidate set
  - single-program scenarios: adjusted == raw, no stacking adjustments
  - multi-program stacking (spend_reduction): adjusted < raw
  - 3-program combination with dual spend_reduction
  - mutually exclusive synthetic case: lower program zeroed, legal_review_required
  - ranking: rank 1 has lowest true_net_cost
  - legal flag propagation
"""
from __future__ import annotations

import pytest

from app.calculators.generate_structure_scenarios import (
    ScenarioResult,
    generate_structure_scenarios,
)
from tests.fixtures.canada_validation import (
    CA_CPTC_PROGRAM,
    CA_CPTC_QUALIFYING_CATEGORIES,
    CA_FEDERAL_JURISDICTION,
    ON_OFTTC_JURISDICTION,
    ON_OFTTC_LINE_ITEMS,
    ON_OFTTC_PROGRAM,
    ON_OFTTC_QUALIFYING_CATEGORIES,
)
from tests.fixtures.canada_stacking_validation import (
    NOHFC_PROGRAM,
    NOHFC_QUALIFYING_CATEGORIES,
    STACKING_RULE_NOHFC_OFTTC,
    STACKING_RULE_NOHFC_CPTC,
)


# ---------------------------------------------------------------------------
# Candidate programs for 3-way test
# ---------------------------------------------------------------------------

_OFTTC_ENTRY = {
    "program": ON_OFTTC_PROGRAM,
    "qualifying_categories": ON_OFTTC_QUALIFYING_CATEGORIES,
    "uplifts": [],
    "jurisdiction_spend_pct": 1.0,
}

# CPTC with same qualifying categories as OFTTC (ATL + labour both qualify)
# On OFTTC line items: qualifying = 1,400,000; credit = 350,000 @ 25%
_CPTC_ON_OFTTC_LINES = {
    "program": CA_CPTC_PROGRAM,
    "qualifying_categories": CA_CPTC_QUALIFYING_CATEGORIES,
    "uplifts": [],
    "jurisdiction_spend_pct": 1.0,
}

_NOHFC_ENTRY = {
    "program": NOHFC_PROGRAM,
    "qualifying_categories": NOHFC_QUALIFYING_CATEGORIES,
    "uplifts": [],
    "jurisdiction_spend_pct": 1.0,
}

_ALL_STACKING_RULES = [STACKING_RULE_NOHFC_OFTTC, STACKING_RULE_NOHFC_CPTC]

# ---------------------------------------------------------------------------
# Expected math (annotated)
# ---------------------------------------------------------------------------
#
# Line items (from ON_OFTTC_LINE_ITEMS):
#   Director Fee       200K → atl_director (fixed_atl)
#   Lead Cast          200K → atl_cast     (fixed_atl)
#   Ontario Resident Crew 600K → btl_resident_labor  (variable_btl)
#   Ontario Crew Labor 400K → btl_crew_labor         (variable_btl)
#   Equipment Rental   200K → btl_equipment_rental   (variable_btl)
#   Post Production    200K → post_production        (post)
#   Insurance          100K → insurance              (other)
#   Completion Bond    100K → completion_bond        (other)
#
#   fixed_atl    = 400,000
#   variable_btl = 1,200,000
#
# OFTTC qualifying = atl_director+atl_cast+btl_resident+btl_crew = 1,400,000
# CPTC qualifying  = atl_director+atl_cast+btl_resident+btl_crew = 1,400,000
# (CPTC categories have same atl/labour pattern as OFTTC on these line items)
#
# OFTTC credit = 1,400,000 × 0.35 = 490,000
# CPTC credit  = 1,400,000 × 0.25 = 350,000
# NOHFC grant  = 500,000 (fixed)
#
# Single programs:
#   OFTTC alone:  raw=490K, net=400+1200-490=1,110K
#   CPTC alone:   raw=350K, net=400+1200-350=1,250K
#   NOHFC alone:  raw=500K, net=400+1200-500=1,100K
#
# Two-program combos (no stacking between OFTTC+CPTC):
#   OFTTC+CPTC:   raw=840K, adj=840K,  net=760K
#   OFTTC+NOHFC:  raw=990K, adj=815K,  net=785K  (-175K from OFTTC)
#   CPTC+NOHFC:   raw=850K, adj=725K,  net=875K  (-125K from CPTC)
#
# Three-program combo (NOHFC reduces both OFTTC and CPTC):
#   OFTTC raw=490K → NOHFC reduces: 500K×0.35=175K → adj OFTTC=315K
#   CPTC  raw=350K → NOHFC reduces: 500K×0.25=125K → adj CPTC =225K
#   NOHFC raw=500K → unchanged
#   Total adj = 315+225+500 = 1,040K
#   net = 400+1200-1040 = 560K  ← best scenario
#
# Ranking by true_net_cost ASC:
#   1. OFTTC+CPTC+NOHFC:  560K
#   2. OFTTC+CPTC:         760K
#   3. OFTTC+NOHFC:        785K
#   4. NOHFC alone:       1,100K
#   5. OFTTC alone:       1,110K
#   6. CPTC+NOHFC:         875K  ... wait, 875K < 1,100K
#
# Sorted:
#   1. OFTTC+CPTC+NOHFC: 560K
#   2. OFTTC+CPTC:        760K
#   3. OFTTC+NOHFC:       785K
#   4. CPTC+NOHFC:        875K
#   5. NOHFC alone:      1,100K
#   6. OFTTC alone:      1,110K
#   7. CPTC alone:       1,250K
# ---------------------------------------------------------------------------

EXPECTED_NET_COSTS = {
    "ca_federal_cptc+nohfc_production_fund+on_ofttc": 560_000,
    "ca_federal_cptc+on_ofttc": 760_000,
    "nohfc_production_fund+on_ofttc": 785_000,
    "ca_federal_cptc+nohfc_production_fund": 875_000,
    "nohfc_production_fund": 1_100_000,
    "on_ofttc": 1_110_000,
    "ca_federal_cptc": 1_250_000,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def three_program_scenarios() -> list[ScenarioResult]:
    return generate_structure_scenarios(
        jurisdiction=ON_OFTTC_JURISDICTION,
        line_items=ON_OFTTC_LINE_ITEMS,
        candidate_programs=[_OFTTC_ENTRY, _CPTC_ON_OFTTC_LINES, _NOHFC_ENTRY],
        stacking_rules=_ALL_STACKING_RULES,
        max_combination_size=3,
    )


def _by_id(scenarios: list[ScenarioResult], scenario_id: str) -> ScenarioResult | None:
    return next((s for s in scenarios if s.scenario_id == scenario_id), None)


# ===========================================================================
# Scenario generation
# ===========================================================================

class TestScenarioGeneration:

    def test_generates_seven_scenarios(self, three_program_scenarios):
        # C(3,1) + C(3,2) + C(3,3) = 3 + 3 + 1 = 7
        assert len(three_program_scenarios) == 7

    def test_all_scenarios_have_unique_ids(self, three_program_scenarios):
        ids = [s.scenario_id for s in three_program_scenarios]
        assert len(ids) == len(set(ids))

    def test_single_program_scenarios_present(self, three_program_scenarios):
        ids = {s.scenario_id for s in three_program_scenarios}
        assert "on_ofttc" in ids
        assert "ca_federal_cptc" in ids
        assert "nohfc_production_fund" in ids

    def test_two_program_scenarios_present(self, three_program_scenarios):
        ids = {s.scenario_id for s in three_program_scenarios}
        assert "nohfc_production_fund+on_ofttc" in ids
        assert "ca_federal_cptc+nohfc_production_fund" in ids
        assert "ca_federal_cptc+on_ofttc" in ids

    def test_three_program_scenario_present(self, three_program_scenarios):
        ids = {s.scenario_id for s in three_program_scenarios}
        assert "ca_federal_cptc+nohfc_production_fund+on_ofttc" in ids

    def test_program_count_per_scenario(self, three_program_scenarios):
        counts = {s.scenario_id: s.program_count for s in three_program_scenarios}
        assert counts["on_ofttc"] == 1
        assert counts["nohfc_production_fund+on_ofttc"] == 2
        assert counts["ca_federal_cptc+nohfc_production_fund+on_ofttc"] == 3

    def test_max_size_1_gives_single_programs_only(self):
        scenarios = generate_structure_scenarios(
            jurisdiction=ON_OFTTC_JURISDICTION,
            line_items=ON_OFTTC_LINE_ITEMS,
            candidate_programs=[_OFTTC_ENTRY, _CPTC_ON_OFTTC_LINES, _NOHFC_ENTRY],
            stacking_rules=_ALL_STACKING_RULES,
            max_combination_size=1,
        )
        assert len(scenarios) == 3
        assert all(s.program_count == 1 for s in scenarios)

    def test_empty_candidate_programs_returns_empty(self):
        scenarios = generate_structure_scenarios(
            jurisdiction=ON_OFTTC_JURISDICTION,
            line_items=ON_OFTTC_LINE_ITEMS,
            candidate_programs=[],
            stacking_rules=[],
        )
        assert scenarios == []


# ===========================================================================
# Per-scenario value correctness
# ===========================================================================

class TestScenarioValues:

    def test_ofttc_alone_raw_value(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "on_ofttc")
        assert abs(s.raw_incentive_value_usd - 490_000) <= 490_000 * 0.01

    def test_ofttc_alone_adjusted_equals_raw(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "on_ofttc")
        assert abs(s.adjusted_incentive_value_usd - s.raw_incentive_value_usd) < 0.01

    def test_ofttc_alone_no_stacking_adjustments(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "on_ofttc")
        assert s.stacking_adjustments == []

    def test_ofttc_alone_true_net(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "on_ofttc")
        expected = EXPECTED_NET_COSTS["on_ofttc"]
        assert abs(s.true_net_cost_usd - expected) <= expected * 0.01

    def test_nohfc_alone_fixed_grant(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "nohfc_production_fund")
        assert abs(s.raw_incentive_value_usd - 500_000) <= 1.0
        assert abs(s.adjusted_incentive_value_usd - 500_000) <= 1.0

    def test_ofttc_nohfc_spend_reduction(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "nohfc_production_fund+on_ofttc")
        assert abs(s.stacking_reduction_usd - 175_000) <= 175_000 * 0.01

    def test_ofttc_nohfc_adjusted_less_than_raw(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "nohfc_production_fund+on_ofttc")
        assert s.adjusted_incentive_value_usd < s.raw_incentive_value_usd

    def test_ofttc_nohfc_adjusted_value(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "nohfc_production_fund+on_ofttc")
        assert abs(s.adjusted_incentive_value_usd - 815_000) <= 815_000 * 0.01

    def test_ofttc_nohfc_true_net(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "nohfc_production_fund+on_ofttc")
        expected = EXPECTED_NET_COSTS["nohfc_production_fund+on_ofttc"]
        assert abs(s.true_net_cost_usd - expected) <= expected * 0.01

    def test_cptc_nohfc_spend_reduction(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "ca_federal_cptc+nohfc_production_fund")
        assert abs(s.stacking_reduction_usd - 125_000) <= 125_000 * 0.01

    def test_three_way_dual_spend_reduction(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "ca_federal_cptc+nohfc_production_fund+on_ofttc")
        # Two spend_reduction adjustments: NOHFC→OFTTC and NOHFC→CPTC
        assert len(s.stacking_adjustments) == 2

    def test_three_way_adjusted_value(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "ca_federal_cptc+nohfc_production_fund+on_ofttc")
        # 315K (OFTTC) + 225K (CPTC) + 500K (NOHFC) = 1,040K
        assert abs(s.adjusted_incentive_value_usd - 1_040_000) <= 1_040_000 * 0.01

    def test_three_way_true_net(self, three_program_scenarios):
        s = _by_id(three_program_scenarios, "ca_federal_cptc+nohfc_production_fund+on_ofttc")
        expected = EXPECTED_NET_COSTS["ca_federal_cptc+nohfc_production_fund+on_ofttc"]
        assert abs(s.true_net_cost_usd - expected) <= expected * 0.01

    def test_all_true_net_costs_match_expected(self, three_program_scenarios):
        for scenario_id, expected_net in EXPECTED_NET_COSTS.items():
            s = _by_id(three_program_scenarios, scenario_id)
            assert s is not None, f"Scenario {scenario_id!r} not found"
            assert abs(s.true_net_cost_usd - expected_net) <= expected_net * 0.01, (
                f"{scenario_id}: expected net ${expected_net:,.0f}, "
                f"got ${s.true_net_cost_usd:,.0f}"
            )


# ===========================================================================
# Ranking
# ===========================================================================

class TestScenarioRanking:

    def test_rank_1_has_lowest_true_net(self, three_program_scenarios):
        rank1 = three_program_scenarios[0]   # list is sorted by rank
        assert rank1.rank == 1
        expected_best = EXPECTED_NET_COSTS["ca_federal_cptc+nohfc_production_fund+on_ofttc"]
        assert abs(rank1.true_net_cost_usd - expected_best) <= expected_best * 0.01

    def test_rank_1_is_three_program_combo(self, three_program_scenarios):
        rank1 = three_program_scenarios[0]
        assert rank1.program_count == 3

    def test_rank_last_has_highest_net_cost(self, three_program_scenarios):
        last = three_program_scenarios[-1]
        expected_worst = EXPECTED_NET_COSTS["ca_federal_cptc"]
        assert abs(last.true_net_cost_usd - expected_worst) <= expected_worst * 0.01

    def test_all_scenarios_have_unique_ranks(self, three_program_scenarios):
        ranks = [s.rank for s in three_program_scenarios]
        assert len(ranks) == len(set(ranks))

    def test_rank_by_net_cost_dimension(self, three_program_scenarios):
        rank1_net = next(s for s in three_program_scenarios if s.rank_by_net_cost == 1)
        # Lowest net cost = three-program combo
        assert "ca_federal_cptc" in rank1_net.scenario_id
        assert "on_ofttc" in rank1_net.scenario_id
        assert "nohfc" in rank1_net.scenario_id

    def test_scenarios_sorted_by_rank(self, three_program_scenarios):
        ranks = [s.rank for s in three_program_scenarios]
        assert ranks == sorted(ranks)

    def test_multi_program_dominates_single_program(self, three_program_scenarios):
        single = [s for s in three_program_scenarios if s.program_count == 1]
        multi  = [s for s in three_program_scenarios if s.program_count > 1]
        best_multi_net = min(s.true_net_cost_usd for s in multi)
        worst_multi_net = max(s.true_net_cost_usd for s in multi)
        best_single_net = min(s.true_net_cost_usd for s in single)
        # Best multi-program (560K) beats best single (1,100K)
        assert best_multi_net < best_single_net


# ===========================================================================
# Mutually exclusive synthetic case
# ===========================================================================

class TestMutuallyExclusiveScenario:
    """Two programs that are mutually exclusive: lower value is zeroed by engine."""

    @pytest.fixture(scope="class")
    def me_scenarios(self):
        prog_a = {
            **ON_OFTTC_PROGRAM,
            "id": "me-prog-a",
            "slug": "credit_a",
            "base_rate": 0.35,
        }
        prog_b = {
            **ON_OFTTC_PROGRAM,
            "id": "me-prog-b",
            "slug": "credit_b",
            "base_rate": 0.20,
        }
        entries = [
            {
                "program": prog_a,
                "qualifying_categories": ON_OFTTC_QUALIFYING_CATEGORIES,
                "uplifts": [],
                "jurisdiction_spend_pct": 1.0,
            },
            {
                "program": prog_b,
                "qualifying_categories": ON_OFTTC_QUALIFYING_CATEGORIES,
                "uplifts": [],
                "jurisdiction_spend_pct": 1.0,
            },
        ]
        me_rule = {
            "program_a_id": "me-prog-a",
            "program_b_id": "me-prog-b",
            "rule_type": "mutually_exclusive",
            "condition_text": "Programs A and B cannot be claimed together",
        }
        return generate_structure_scenarios(
            jurisdiction=ON_OFTTC_JURISDICTION,
            line_items=ON_OFTTC_LINE_ITEMS,
            candidate_programs=entries,
            stacking_rules=[me_rule],
            max_combination_size=2,
        )

    def test_three_scenarios_generated(self, me_scenarios):
        # C(2,1)=2 single + C(2,2)=1 combined = 3
        assert len(me_scenarios) == 3

    def test_single_scenarios_have_no_flags(self, me_scenarios):
        singles = [s for s in me_scenarios if s.program_count == 1]
        assert all(s.legal_flags == [] for s in singles)
        assert all(not s.legal_review_required for s in singles)

    def test_combined_scenario_legal_review_required(self, me_scenarios):
        combined = next(s for s in me_scenarios if s.program_count == 2)
        assert combined.legal_review_required is True

    def test_combined_scenario_has_legal_flag(self, me_scenarios):
        combined = next(s for s in me_scenarios if s.program_count == 2)
        assert len(combined.legal_flags) >= 1

    def test_combined_scenario_lower_value_zeroed(self, me_scenarios):
        combined = next(s for s in me_scenarios if s.program_count == 2)
        # credit_a (35%) value = 490K; credit_b (20%) value = 280K
        # mutually_exclusive: credit_b zeroed → adjusted = 490K
        assert abs(combined.adjusted_incentive_value_usd - 490_000) <= 490_000 * 0.01

    def test_combined_scenario_reduction_equals_lower_value(self, me_scenarios):
        combined = next(s for s in me_scenarios if s.program_count == 2)
        # stacking_reduction = 280K (credit_b zeroed)
        assert abs(combined.stacking_reduction_usd - 280_000) <= 280_000 * 0.01

    def test_single_program_credit_a_ranks_higher_than_combined(self, me_scenarios):
        """Single credit_a alone vs combined (with one zeroed) — should tie or credit_a wins."""
        single_a = next(s for s in me_scenarios if s.scenario_id == "credit_a")
        combined = next(s for s in me_scenarios if s.program_count == 2)
        # Both have same adjusted incentive value (490K), but combined has legal flag → ranks lower
        assert single_a.rank <= combined.rank


# ===========================================================================
# Stacking rule filtering
# ===========================================================================

class TestStackingRuleFiltering:
    """Only rules relevant to the combination should be applied."""

    def test_single_program_no_stacking_rules_applied(self, three_program_scenarios):
        # Single NOHFC — stacking rules exist but no partner in combo → not applied
        s = _by_id(three_program_scenarios, "nohfc_production_fund")
        assert s.stacking_adjustments == []
        assert s.stacking_reduction_usd == 0.0

    def test_ofttc_only_no_reduction_despite_global_rules(self, three_program_scenarios):
        # OFTTC alone — NOHFC rules exist globally but NOHFC is not in this combo
        s = _by_id(three_program_scenarios, "on_ofttc")
        assert s.stacking_reduction_usd == 0.0

    def test_ofttc_cptc_no_rule_between_them(self, three_program_scenarios):
        # OFTTC + CPTC — no stacking rule between them → adjusted == raw
        s = _by_id(three_program_scenarios, "ca_federal_cptc+on_ofttc")
        assert s.stacking_reduction_usd == 0.0
        assert abs(s.adjusted_incentive_value_usd - s.raw_incentive_value_usd) < 0.01
