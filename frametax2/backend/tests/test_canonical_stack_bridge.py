"""
canonical_stack_bridge.py — focused unit tests.

Standalone, no DB/project needed: proves the bridge's own contract in
isolation before it is exercised end-to-end through canonical_evaluation.py
(see test_canonical_authority_substrate.py's CA-ON/CA-BC assertions and
test_canonical_pricing_path_and_discovery.py's Ontario test for the
served-runtime proof).
"""
from __future__ import annotations

from app.calculators.canonical_stack_bridge import (
    StackCandidate,
    eligible_for_combination,
    load_named_pair_rule,
    price_program_pair_stack,
)


def test_eligible_for_combination_same_exact_jurisdiction():
    assert eligible_for_combination("CA-ON", "CA-ON") is True


def test_eligible_for_combination_federal_plus_one_province():
    assert eligible_for_combination("CA", "CA-BC") is True
    assert eligible_for_combination("CA-ON", "CA") is True


def test_eligible_for_combination_two_different_provinces_refused():
    """The exact case Codex/the reconnection spec calls out: multiple
    provinces must never automatically become one combined structure."""
    assert eligible_for_combination("CA-BC", "CA-ON") is False


def test_eligible_for_combination_different_countries_refused():
    assert eligible_for_combination("US-CA", "US-NY") is False
    assert eligible_for_combination("US", "CA") is False


def test_load_named_pair_rule_known_pair():
    rule = load_named_pair_rule("ca_federal_cptc", "ca_bc_pstc")
    assert rule is not None
    assert rule["rule_type"] == "mutually_exclusive"


def test_load_named_pair_rule_unknown_pair_returns_none_never_default_allowed():
    """The single most important invariant of this module: an unmapped
    pair must return None, never a fabricated 'allowed' rule."""
    assert load_named_pair_rule("sa_film_commission_rebate", "il_film_incentive") is None


def test_price_program_pair_stack_mutually_exclusive_zeroes_lower_value():
    a = StackCandidate("ca_federal_cptc", "CA-BC", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    b = StackCandidate("ca_bc_pstc", "CA-BC", 330_000.0, 0.33, 1_000_000.0, "tax_credit")
    result = price_program_pair_stack(a, b)
    assert result is not None
    assert result.rule_type == "mutually_exclusive"
    assert result.per_program_adjusted_usd == {"ca_federal_cptc": 0.0, "ca_bc_pstc": 330_000.0}
    assert result.adjusted_incentive_usd == 330_000.0
    assert result.jurisdiction_code == "CA-BC"
    assert result.disclosed_limitations == []


def test_price_program_pair_stack_spend_reduction_discloses_unresolved_direction():
    """Both on_ofttc and ca_federal_cptc are tax_credit typed, so the
    reused apply_stacking_adjustments spend_reduction heuristic (which
    only recognizes grant/regional_fund/discretionary_fund as the
    reducing side) cannot apply the real statutory reduction. This must
    be disclosed, never silently reported as a verified net figure."""
    a = StackCandidate("on_ofttc", "CA-ON", 200_000.0, 0.20, 1_000_000.0, "tax_credit")
    b = StackCandidate("ca_federal_cptc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    result = price_program_pair_stack(a, b)
    assert result is not None
    assert result.rule_type == "spend_reduction"
    assert result.adjusted_incentive_usd == 450_000.0  # unreduced — disclosed, not silent
    assert len(result.disclosed_limitations) == 1
    assert "spend_reduction calculator only recognizes" in result.disclosed_limitations[0]


def test_price_program_pair_stack_returns_none_for_unresolvable_pair():
    a = StackCandidate("sa_film_commission_rebate", "SA", 100.0, 0.1, 1_000.0, "cash_rebate")
    b = StackCandidate("ca_federal_cptc", "SA", 100.0, 0.1, 1_000.0, "tax_credit")
    assert price_program_pair_stack(a, b) is None


def test_price_program_pair_stack_returns_none_for_different_provinces():
    a = StackCandidate("ca_bc_pstc", "CA-BC", 330_000.0, 0.33, 1_000_000.0, "tax_credit")
    b = StackCandidate("on_ofttc", "CA-ON", 200_000.0, 0.20, 1_000_000.0, "tax_credit")
    # Even if a (hypothetical) named rule existed for this slug pair, two
    # different provinces are never the same physical shoot jurisdiction.
    assert price_program_pair_stack(a, b) is None
