"""
canonical_stack_bridge.py — focused unit tests.

Standalone, no DB/project needed: proves the bridge's own contract in
isolation before it is exercised end-to-end through canonical_evaluation.py
(see test_canonical_authority_substrate.py's CA-ON/CA-BC assertions and
test_canonical_pricing_path_and_discovery.py's Ontario test for the
served-runtime proof).
"""
from __future__ import annotations

import itertools

from app.calculators.canonical_stack_bridge import (
    StackCandidate,
    eligible_for_combination,
    load_named_pair_rule,
    price_program_group_stack,
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
    # CA-BC PSTC repair (workstream CLAUDE_D743_REJECTED_FINDINGS_REMEDIATION):
    # this test originally used ca_bc_pstc, which a prior, separately-accepted
    # session (the canonical identity/authority cleanup, already part of the
    # starting HEAD) deliberately added to the B1 discretionary-ruling
    # FAIL_CLOSED veto list -- resolve_program_rate("ca_bc_pstc", ...) now
    # returns None unconditionally via economic_block_for_program's own B4
    # gate, a genuine, already-accepted authority decision, not a bug to
    # revert here. on_opstc + ca_federal_cptc is the REAL, currently-
    # priceable, analogous mutually_exclusive pair (Ontario's own PSTC-
    # equivalent vs. CPTC -- the SAME CPTC-vs-foreign-service-track legal
    # logic stacking_rules.py records for BC, just for Ontario instead),
    # confirmed to exercise the identical rule_type/zeroing behavior this
    # test was written to prove.
    # NA-CODEX-08 (2026-10-12): CPTC + OPSTC is NOT exclusive (Ontario Creates OPSTC Guidelines s.1.01: the OPSTC "may be claimed alone, or in addition to a
    # federal ... Production Services Tax Credit (or a Canadian Film or Video Production Tax Credit)"); the still-exclusive Ontario pair is the domestic
    # OFTTC versus the service OPSTC, so this control now uses that pair.
    a = StackCandidate("on_ofttc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    b = StackCandidate("on_opstc", "CA-ON", 330_000.0, 0.33, 1_000_000.0, "tax_credit")
    result = price_program_pair_stack(a, b)
    assert result is not None
    assert result.rule_type == "mutually_exclusive"
    assert result.per_program_adjusted_usd == {"on_ofttc": 0.0, "on_opstc": 330_000.0}
    assert result.adjusted_incentive_usd == 330_000.0
    assert result.jurisdiction_code == "CA-ON"
    assert result.disclosed_limitations == []


def test_cptc_with_the_ontario_opstc_is_allowed_and_the_provincial_credit_is_assistance_to_the_cptc():
    # generic arithmetic (no CPTC labour/cost fields supplied): CPTC reduced by min(OPSTC 330,000; qualifying 1,000,000) x 25% = 82,500
    a = StackCandidate("ca_federal_cptc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    b = StackCandidate("on_opstc", "CA-ON", 330_000.0, 0.33, 1_000_000.0, "tax_credit")
    result = price_program_pair_stack(a, b)
    assert result is not None and result.rule_type == "spend_reduction"
    assert result.per_program_adjusted_usd == {"ca_federal_cptc": 167_500.0, "on_opstc": 330_000.0}
    assert result.adjusted_incentive_usd == 497_500.0 and result.stacking_reduction_usd == 82_500.0
    # with the CRA fields: labour 800,000, cost 1,000,000 -> cap 60% x (1,000,000 - 330,000) = 402,000 < labour -> CPTC = 25% x 402,000 = 100,500
    cptc = StackCandidate("ca_federal_cptc", "CA-ON", 200_000.0, 0.25, 1_000_000.0, "tax_credit",
                          rate_basis_usd=800_000.0, production_cost_usd=1_000_000.0)
    net = price_program_pair_stack(cptc, b)
    assert net.per_program_adjusted_usd["ca_federal_cptc"] == 100_500.0 and net.adjusted_incentive_usd == 430_500.0


def test_the_ontario_opstc_nets_only_its_labour_portion_against_the_federal_pstc():
    # Ontario Creates OPSTC Guidelines s.3.02: only the labour portion of the OPSTC is assistance to the PSTC.
    # PSTC 16% on labour 600,000 = 96,000; OPSTC 21.5% on 1,000,000 = 215,000 of which labour 21.5% x 600,000 = 129,000 is assistance.
    # PSTC reduction = 129,000 x 16% = 20,640 -> 75,360 (the whole-credit reading would give 215,000 x 16% = 34,400).
    pstc = StackCandidate("ca_federal_pstc", "CA-ON", 96_000.0, 0.16, 600_000.0, "tax_credit", rate_basis_usd=600_000.0)
    opstc = StackCandidate("on_opstc", "CA-ON", 215_000.0, 0.215, 1_000_000.0, "tax_credit")
    result = price_program_pair_stack(pstc, opstc)
    assert result is not None and result.rule_type == "spend_reduction"
    assert result.per_program_adjusted_usd == {"ca_federal_pstc": 75_360.0, "on_opstc": 215_000.0}
    assert result.stacking_reduction_usd == 20_640.0 and result.adjusted_incentive_usd == 290_360.0


def test_the_two_federal_credits_remain_mutually_exclusive_and_a_zeroed_credit_is_not_assistance():
    cptc = StackCandidate("ca_federal_cptc", "CA", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    pstc = StackCandidate("ca_federal_pstc", "CA", 160_000.0, 0.16, 1_000_000.0, "tax_credit")
    both = price_program_pair_stack(cptc, pstc)
    assert both is not None and both.rule_type == "mutually_exclusive" and both.per_program_adjusted_usd == {"ca_federal_cptc": 250_000.0, "ca_federal_pstc": 0.0}


def test_price_program_pair_stack_spend_reduction_applies_ontario_interaction_correctly():
    """Ontario interaction repair: both on_ofttc and ca_federal_cptc are
    tax_credit typed, so apply_stacking_adjustments' own grant-type
    heuristic alone cannot resolve direction — but the rule's own
    condition_text already names OFTTC as the reducing side
    (canonical_stack_bridge._SPEND_REDUCTION_DIRECTION structures that
    existing prose into a "reduces" field consumed by
    apply_stacking_adjustments._apply_spend_reduction). The reduction
    must now actually apply: CPTC's basis reduces by
    min(OFTTC value, CPTC qualifying spend) x CPTC's effective rate =
    min(200_000, 1_000_000) x 0.25 = 50_000."""
    a = StackCandidate("on_ofttc", "CA-ON", 200_000.0, 0.20, 1_000_000.0, "tax_credit")
    b = StackCandidate("ca_federal_cptc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    result = price_program_pair_stack(a, b)
    assert result is not None
    assert result.rule_type == "spend_reduction"
    assert result.per_program_adjusted_usd == {"on_ofttc": 200_000.0, "ca_federal_cptc": 200_000.0}
    assert result.adjusted_incentive_usd == 400_000.0
    assert result.stacking_reduction_usd == 50_000.0
    assert result.disclosed_limitations == []  # no longer an unresolved case


def test_price_program_pair_stack_spend_reduction_discloses_when_direction_genuinely_unknown():
    """A spend_reduction pair with NO entry in _SPEND_REDUCTION_DIRECTION
    and neither program typed as a grant/fund must still disclose rather
    than silently reporting an unreduced sum — the safety net for any
    future _SLUG_PAIR_RULES entry this table hasn't been extended to
    cover yet."""
    import app.calculators.canonical_stack_bridge as bridge

    # Monkeypatch a synthetic spend_reduction rule with no direction data,
    # exercising _build_group_result's disclosure branch directly.
    rule = {
        "program_a_id": "x_credit_one", "program_b_id": "x_credit_two",
        "rule_type": "spend_reduction", "condition_text": "synthetic test rule",
    }
    a = StackCandidate("x_credit_one", "ZZ", 100_000.0, 0.10, 1_000_000.0, "tax_credit")
    b = StackCandidate("x_credit_two", "ZZ", 100_000.0, 0.10, 1_000_000.0, "tax_credit")
    result = bridge._build_group_result([a, b], [rule])
    assert result.disclosed_limitations
    assert "does not have a resolved reduction direction" in result.disclosed_limitations[0] or (
        "no reduction was applied" in result.disclosed_limitations[0]
    )
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


def test_n_way_group_stack_all_pairs_covered():
    """Codex correctness classification, N-way reconnection: a triple
    where every pairwise sub-combination has an explicit named rule must
    price as one combined structure."""
    a = StackCandidate("ca_federal_cptc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    b = StackCandidate("ca_on_opstc", "CA-ON", 330_000.0, 0.33, 1_000_000.0, "tax_credit")
    c = StackCandidate("on_ofttc", "CA-ON", 200_000.0, 0.20, 1_000_000.0, "tax_credit")
    result = price_program_group_stack([a, b, c])
    assert result is not None
    assert set(result.program_slugs) == {"ca_federal_cptc", "ca_on_opstc", "on_ofttc"}
    # OFTTC (domestic) is mutually exclusive with OPSTC (service); OPSTC has the higher raw value and survives, so OFTTC is zeroed and, no longer
    # claimed, is not assistance to the CPTC. The OPSTC is allowed with the CPTC and reduces it: 250,000 - min(330,000; 1,000,000) x 25% = 167,500.
    assert result.per_program_adjusted_usd == {
        "ca_federal_cptc": 167_500.0, "ca_on_opstc": 330_000.0, "on_ofttc": 0.0,
    }


def test_n_way_group_stack_partial_coverage_refused():
    """A 4th, unrelated program with no coverage against the other three
    must refuse the whole group — never a partially-trusted combination."""
    a = StackCandidate("ca_federal_cptc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    b = StackCandidate("ca_on_opstc", "CA-ON", 330_000.0, 0.33, 1_000_000.0, "tax_credit")
    c = StackCandidate("on_ofttc", "CA-ON", 200_000.0, 0.20, 1_000_000.0, "tax_credit")
    d = StackCandidate("sa_film_commission_rebate", "CA-ON", 10.0, 0.1, 100.0, "cash_rebate")
    assert price_program_group_stack([a, b, c, d]) is None


def test_n_way_group_stack_order_invariant_under_permutation():
    """Codex optimizer-correctness classification, point 4: the reused
    apply_stacking_adjustments engine applies rules sequentially and its
    per-program values can depend on which rule touches a shared program
    first — a confirmed order-sensitivity. price_program_group_stack
    must canonicalize order so every permutation of the same candidate
    set produces a byte-identical result."""
    a = StackCandidate("ca_federal_cptc", "CA-ON", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    b = StackCandidate("ca_on_opstc", "CA-ON", 330_000.0, 0.33, 1_000_000.0, "tax_credit")
    c = StackCandidate("on_ofttc", "CA-ON", 200_000.0, 0.20, 1_000_000.0, "tax_credit")

    distinct_results = set()
    for perm in itertools.permutations([a, b, c]):
        result = price_program_group_stack(list(perm))
        assert result is not None
        distinct_results.add((
            tuple(sorted(result.per_program_adjusted_usd.items())),
            result.adjusted_incentive_usd,
            tuple(result.program_slugs),
        ))
    assert len(distinct_results) == 1, (
        f"expected identical economics under every permutation, got {len(distinct_results)} distinct results"
    )


def test_conditional_rule_type_fails_closed_never_publishes():
    """Codex optimizer-correctness classification, point 1: a pair with a
    KNOWN but UNRESOLVED (conditional) rule must never be published as a
    priced combined structure — the legal fact is known, but automatic
    economic resolution is not. ca_federal_cptc + ca_qc_qprdp is a real
    'conditional' entry in _SLUG_PAIR_RULES (legal review required, no
    automatic adjustment)."""
    rule = load_named_pair_rule("ca_federal_cptc", "ca_qc_qprdp")
    assert rule is not None
    assert rule["rule_type"] == "conditional"

    a = StackCandidate("ca_federal_cptc", "CA-QC", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
    b = StackCandidate("ca_qc_qprdp", "CA-QC", 100_000.0, 0.10, 1_000_000.0, "tax_credit")
    assert price_program_group_stack([a, b]) is None
    assert price_program_pair_stack(a, b) is None
