"""NA-RECONCILIATION-12: the ten NA pairs that had no named stacking rule. Synthetic components only; every expectation is hand arithmetic from the stated rates, not read from the code under test.
Rates used: PSTC 16%, CPTC 25% of min(labour, 60% x (cost - assistance)), Alberta 22%, BC DAVE 16% (labour credit), Nova Scotia 25% (modeled base)."""
from __future__ import annotations

import pytest

from app.calculators.canonical_stack_bridge import load_named_pair_rule
from tests.test_na_stack_and_gate_repairs_controls import _alloc, _comp, _run

CPTC, PSTC = "ca_federal_cptc", "ca_federal_pstc"
AB, DAVE, NB, NS, SK, OFTTC = "ca_ab_fttc", "ca_bc_dave", "ca_nb_film_tax_credit", "ca_ns_production_incentive_fund", "ca_sk_creative_saskatchewan_grant", "on_ofttc"

EXPECTED_RULES = {
    (AB, CPTC): "spend_reduction", (AB, PSTC): "spend_reduction", (DAVE, PSTC): "spend_reduction", (DAVE, CPTC): "conditional",
    (NB, CPTC): "spend_reduction", (NB, PSTC): "spend_reduction", (NS, CPTC): "spend_reduction", (NS, PSTC): "spend_reduction",
    (SK, PSTC): "spend_reduction", (OFTTC, PSTC): "conditional",
}


def _pair(federal, fed_amt, jur, slug, prov_amt, gross):
    return _run([_comp("principal_production", "CA", federal, [_alloc("1", fed_amt, "principal_production", "CA", "L0", "btl_crew_labor")]),
                 _comp("principal_production", jur, slug, [_alloc("2", prov_amt, "principal_production", jur, "L1", "btl_crew_labor")])], gross)


@pytest.mark.parametrize("pair,rule_type", sorted(EXPECTED_RULES.items()))
def test_every_formerly_unruled_pair_now_has_a_named_rule_of_the_audited_type(pair, rule_type):
    rule = load_named_pair_rule(*pair)
    assert rule is not None and rule["rule_type"] == rule_type
    assert rule["condition_text"].strip()


def test_the_two_pairs_without_primary_text_stay_unresolved_and_block_rather_than_price_as_stacked():
    for slug, jur, fed in ((DAVE, "CA-BC", CPTC), (OFTTC, "CA-ON", PSTC)):
        res = _pair(fed, 600_000.0, jur, slug, 600_000.0, 1_200_000.0)
        assert res.executable is False and "conditional" in (res.rejection_reason or "") and fed in res.rejection_reason


def test_alberta_credit_nets_the_pstc_by_its_labour_share_and_discloses_the_assumption():
    res = _pair(PSTC, 600_000.0, "CA-AB", AB, 600_000.0, 1_200_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.raw_component_incentives_usd[AB] == pytest.approx(0.22 * 600_000.0)                         # 132,000
    # labour share = 22% x PSTC labour 600,000 = 132,000 (inside the credit); PSTC reduction = 132,000 x 16% = 21,120; PSTC 96,000 - 21,120
    assert res.post_adjustment_component_incentives_usd[PSTC] == pytest.approx(74_880.0)
    assert res.post_adjustment_component_incentives_usd[AB] == pytest.approx(132_000.0)                    # the federal credit never reduces Alberta
    assert any("Apportionment assumption" in n and "Alberta" in n for n in res.disclosed_limitations)


def test_alberta_credit_lowers_the_cptc_cost_cap_only_when_the_cap_binds():
    loose = _pair(CPTC, 600_000.0, "CA-AB", AB, 600_000.0, 1_200_000.0)
    assert loose.post_adjustment_component_incentives_usd[CPTC] == pytest.approx(150_000.0)               # cap 60% x (1,200,000 - 132,000) = 640,800 > labour 600,000: unchanged
    tight = _pair(CPTC, 900_000.0, "CA-AB", AB, 600_000.0, 1_500_000.0)
    assert tight.raw_component_incentives_usd[CPTC] == pytest.approx(225_000.0)                           # 25% x min(900,000; 60% x 1,500,000 = 900,000)
    # cap 60% x (1,500,000 - 132,000) = 820,800 < labour 900,000 -> 25% x 820,800 = 205,200; labour itself is not reduced
    assert tight.post_adjustment_component_incentives_usd[CPTC] == pytest.approx(205_200.0)


def test_dave_labour_credit_nets_the_pstc_in_full():
    res = _pair(PSTC, 600_000.0, "CA-BC", DAVE, 600_000.0, 1_200_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.raw_component_incentives_usd[DAVE] == pytest.approx(96_000.0)                              # 16% x 600,000
    assert res.post_adjustment_component_incentives_usd[PSTC] == pytest.approx(96_000.0 - 96_000.0 * 0.16)  # 80,640: the whole DAVE credit is labour assistance
    assert not any("Apportionment" in n for n in res.disclosed_limitations)                                 # a labour-only credit is not apportioned


def test_nova_scotia_awarded_amount_nets_the_pstc_and_never_the_cptc_labour():
    res = _pair(PSTC, 600_000.0, "CA-NS", NS, 600_000.0, 1_200_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.post_adjustment_component_incentives_usd[PSTC] == pytest.approx(96_000.0 - 150_000.0 * 0.16)  # 25% x 600,000 = 150,000 labour share; 72,000
    cptc = _pair(CPTC, 600_000.0, "CA-NS", NS, 600_000.0, 1_200_000.0)
    assert cptc.post_adjustment_component_incentives_usd[CPTC] == pytest.approx(150_000.0)                 # cap 60% x (1,200,000 - 150,000) = 630,000 > labour: unchanged


@pytest.mark.parametrize("fed,jur,slug", [(PSTC, "CA-NB", NB), (CPTC, "CA-NB", NB), (PSTC, "CA-SK", SK), (CPTC, "CA-SK", SK)])
def test_discretionary_ceilings_carry_no_guaranteed_value_so_nothing_is_netted_and_nothing_is_unresolved(fed, jur, slug):
    res = _pair(fed, 600_000.0, jur, slug, 600_000.0, 1_200_000.0)
    assert "no named" not in (res.rejection_reason or "").lower() and "UNRESOLVED_NO_AUTHORITY" not in (res.rejection_reason or "")
    assert res.executable is False and slug in (res.rejection_reason or "")


def test_nova_scotia_all_cost_base_is_apportioned_to_labour_as_an_assumption_and_the_whole_credit_lower_bound_is_disclosed():
    # Nova Scotia now prices 25% of ALL eligible cost (CCTH Guidelines s.6.2): 25% x (600,000 labour + 400,000 equipment) = 250,000. PSTC labour basis 600,000 (16% = 96,000).
    res = _run([_comp("principal_production", "CA", PSTC, [_alloc("1", 600_000.0, "principal_production", "CA", "L0", "btl_crew_labor")]),
                _comp("principal_production", "CA-NS", NS, [_alloc("2", 600_000.0, "principal_production", "CA-NS", "L1", "btl_crew_labor"),
                                                            _alloc("3", 400_000.0, "principal_production", "CA-NS", "L2", "btl_equipment_rental")])], 1_600_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.raw_component_incentives_usd[NS] == pytest.approx(250_000.0)
    # ASSUMED labour share = 25% x 600,000 = 150,000 -> PSTC reduction 150,000 x 16% = 24,000 -> 72,000; whole-credit lower bound: 250,000 x 16% = 40,000 -> 56,000
    assert res.post_adjustment_component_incentives_usd[PSTC] == pytest.approx(72_000.0)
    note = next(n for n in res.disclosed_limitations if "Nova Scotia" in n and "Apportionment assumption" in n)
    assert "$56,000" in note and "$150,000" in note
    adj = next(a for a in res.stacking_adjustments if {a.program_a_id, a.program_b_id} == {NS, PSTC})
    assert "ASSUMED ALLOCATION" in adj.description and "assumed allocation $150,000" in adj.description and "verified $0" in adj.description


def test_a_labour_only_credit_is_labelled_verified_netting_and_an_apportioned_one_is_labelled_assumed():
    from app.calculators.canonical_stack_bridge import netting_basis_label
    assert netting_basis_label(DAVE).startswith("VERIFIED NETTING") and netting_basis_label("on_opstc").startswith("VERIFIED NETTING")
    for slug in (AB, NB, NS, SK, "ca_mb_film_video_credit", "ca_qc_pstc", "ca_nl_all_spend_credit"):
        assert netting_basis_label(slug).startswith("ASSUMED ALLOCATION"), slug
    res = _pair(PSTC, 600_000.0, "CA-BC", DAVE, 600_000.0, 1_200_000.0)
    adj = next(a for a in res.stacking_adjustments if {a.program_a_id, a.program_b_id} == {DAVE, PSTC})
    assert "VERIFIED NETTING" in adj.description and "verified $96,000; assumed allocation $0" in adj.description
