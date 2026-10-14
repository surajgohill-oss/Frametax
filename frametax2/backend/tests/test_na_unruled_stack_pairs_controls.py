"""NA-RECONCILIATION-12/13: the ten NA pairs that had no named stacking rule (the three that stayed conditional were ruled in NA-RECONCILIATION-13 from primary text). Synthetic components only; every expectation is hand arithmetic from the stated rates, not read from the code under test.
Rates used: PSTC 16%, CPTC 25% of min(labour, 60% x (cost - assistance)), Alberta 22%, BC DAVE 16% (labour credit), Nova Scotia 25% (modeled base)."""
from __future__ import annotations

import pytest

from app.calculators.canonical_stack_bridge import load_named_pair_rule
from tests.test_na_stack_and_gate_repairs_controls import _alloc, _comp, _run

CPTC, PSTC = "ca_federal_cptc", "ca_federal_pstc"
AB, DAVE, NB, NS, SK, OFTTC = "ca_ab_fttc", "ca_bc_dave", "ca_nb_film_tax_credit", "ca_ns_production_incentive_fund", "ca_sk_creative_saskatchewan_grant", "on_ofttc"

EXPECTED_RULES = {
    (AB, CPTC): "spend_reduction", (AB, PSTC): "spend_reduction", (DAVE, PSTC): "spend_reduction", (DAVE, CPTC): "spend_reduction",
    (NB, CPTC): "spend_reduction", (NB, PSTC): "spend_reduction", (NS, CPTC): "spend_reduction", (NS, PSTC): "spend_reduction",
    (SK, PSTC): "spend_reduction", (OFTTC, PSTC): "spend_reduction", ("ca_bc_film_tv_tax_credit", PSTC): "spend_reduction",
}


def _pair(federal, fed_amt, jur, slug, prov_amt, gross, category="btl_crew_labor"):
    return _run([_comp("principal_production", "CA", federal, [_alloc("1", fed_amt, "principal_production", "CA", "L0", "btl_crew_labor")]),
                 _comp("principal_production", jur, slug, [_alloc("2", prov_amt, "principal_production", jur, "L1", category)])], gross)


BCDOM = "ca_bc_film_tv_tax_credit"

def _dave_trio(federal, fed_amt, gross, vfx=600_000.0, host_labour=100_000.0, vfx_category="vfx"):
    """federal credit + the BC domestic credit (DAVE's host, s.81.2(1)(a)) on 100,000 of BC labour + DAVE on VFX labour."""
    return _run([_comp("principal_production", "CA", federal, [_alloc("1", fed_amt, "principal_production", "CA", "L0", "btl_crew_labor")]),
                 _comp("principal_production", "CA-BC", BCDOM, [_alloc("2", host_labour, "principal_production", "CA-BC", "L1", "btl_crew_labor")]),
                 _comp("vfx", "CA-BC", DAVE, [_alloc("3", vfx, "vfx", "CA-BC", "L2", vfx_category)])], gross)

@pytest.mark.parametrize("pair,rule_type", sorted(EXPECTED_RULES.items()))
def test_every_formerly_unruled_pair_now_has_a_named_rule_of_the_audited_type(pair, rule_type):
    rule = load_named_pair_rule(*pair)
    assert rule is not None and rule["rule_type"] == rule_type
    assert rule["condition_text"].strip()


def test_ofttc_and_the_bc_domestic_credit_net_the_pstc_by_their_whole_labour_credit_and_the_pstc_never_reduces_them():
    # OFTTC 35% x 600,000 Ontario labour = 210,000; BC domestic 35% x 600,000 BC labour = 210,000; PSTC 16% x 600,000 = 96,000. Both provincial credits are computed on labour only, so the
    # whole credit is assistance to the PSTC (VERIFIED NETTING): 96,000 - 210,000 x 16% = 62,400. The PSTC is not assistance to either (O. Reg. 37/09 s.29(4); ITA (BC) s.79(1)).
    for jur, slug in (("CA-ON", OFTTC), ("CA-BC", BCDOM)):
        res = _pair(PSTC, 600_000.0, jur, slug, 600_000.0, 1_200_000.0)
        assert res.executable is True, res.rejection_reason
        assert res.raw_component_incentives_usd[slug] == pytest.approx(210_000.0)
        assert res.post_adjustment_component_incentives_usd[PSTC] == pytest.approx(62_400.0)
        assert res.post_adjustment_component_incentives_usd[slug] == pytest.approx(210_000.0)
        adj = next(a for a in res.stacking_adjustments if {a.program_a_id, a.program_b_id} == {slug, PSTC})
        assert "VERIFIED NETTING" in adj.description and "verified $210,000; assumed allocation $0" in adj.description
        assert not any("Apportionment" in n for n in res.disclosed_limitations)


def test_dave_without_its_host_credit_is_not_a_lawful_structure_and_names_the_statute():
    # Income Tax Act (BC) s.81.2(1)(a) / s.82.3(1)(a): DAVE needs eligibility for, and an application for, the s.80 (or s.82.1) credit for the same production.
    for fed in (PSTC, CPTC):
        res = _pair(fed, 600_000.0, "CA-BC", DAVE, 600_000.0, 1_200_000.0, category="vfx")
        assert res.executable is False and "claimable only alongside its host credit" in (res.rejection_reason or "") and "s.81.2(1)(a)" in res.rejection_reason
    alone = _run([_comp("vfx", "CA-BC", DAVE, [_alloc("3", 600_000.0, "vfx", "CA-BC", "L2", "vfx")])], 600_000.0)
    assert alone.executable is False and "claimable only alongside its host credit" in alone.rejection_reason


def test_dave_with_the_production_services_host_is_lawful_and_with_both_hosts_is_not():
    # s.83.1: the s.80-82 credits and the s.82.1-82.3 credits are alternatives for one production.
    ps = _run([_comp("principal_production", "CA-BC", "ca_bc_pstc", [_alloc("2", 100_000.0, "principal_production", "CA-BC", "L1", "btl_crew_labor")]),
               _comp("vfx", "CA-BC", DAVE, [_alloc("3", 600_000.0, "vfx", "CA-BC", "L2", "vfx")])], 700_000.0)
    assert ps.executable is True, ps.rejection_reason
    assert ps.raw_component_incentives_usd[DAVE] == pytest.approx(96_000.0)                                  # 16% x 600,000 VFX labour
    both = _run([_comp("principal_production", "CA-BC", "ca_bc_pstc", [_alloc("2", 100_000.0, "principal_production", "CA-BC", "L1", "btl_crew_labor")]),
                 _comp("principal_production", "CA-BC", BCDOM, [_alloc("4", 100_000.0, "principal_production", "CA-BC", "L3", "btl_crew_labor")]),
                 _comp("vfx", "CA-BC", DAVE, [_alloc("3", 600_000.0, "vfx", "CA-BC", "L2", "vfx")])], 800_000.0)
    assert both.executable is False and "mutually_exclusive" in (both.rejection_reason or "")


def test_dave_with_the_cptc_lowers_the_cptc_cost_cap_only_when_the_cap_binds():
    # Loose: host 35% x 100,000 = 35,000; DAVE 16% x 600,000 VFX = 96,000; assistance 131,000. Gross 600,000 + 100,000 + 600,000 = 1,300,000.
    # CPTC cap 60% x (1,300,000 - 131,000) = 701,400 > labour 600,000, so CPTC stays 25% x 600,000 = 150,000.
    loose = _dave_trio(CPTC, 600_000.0, 1_300_000.0)
    assert loose.executable is True, loose.rejection_reason
    assert loose.raw_component_incentives_usd[DAVE] == pytest.approx(96_000.0) and loose.raw_component_incentives_usd[BCDOM] == pytest.approx(35_000.0)
    assert loose.post_adjustment_component_incentives_usd[CPTC] == pytest.approx(150_000.0)
    # Tight: CPTC labour 900,000, gross 900,000 + 100,000 + 600,000 = 1,600,000. Raw cap 60% x 1,600,000 = 960,000 > 900,000 so CPTC raw = 225,000.
    # Net of assistance 131,000: cap 60% x (1,600,000 - 131,000) = 881,400 < 900,000, so CPTC = 25% x 881,400 = 220,350; the labour itself is not reduced.
    tight = _dave_trio(CPTC, 900_000.0, 1_600_000.0)
    assert tight.raw_component_incentives_usd[CPTC] == pytest.approx(225_000.0)
    assert tight.post_adjustment_component_incentives_usd[CPTC] == pytest.approx(220_350.0)
    assert tight.post_adjustment_component_incentives_usd[DAVE] == pytest.approx(96_000.0)                  # the CPTC never reduces DAVE (ITA (BC) s.79(1))


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
    # DAVE's base is BC labour directly attributable to digital animation or visual effects (ITA (BC) s.81.2(8) ALE): the 600,000 here is VFX-category labour. Host: BC domestic 35% x 100,000 = 35,000.
    res = _dave_trio(PSTC, 600_000.0, 1_300_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.raw_component_incentives_usd[DAVE] == pytest.approx(96_000.0)                              # 16% x 600,000 (11% + 5% prescribed, B.C. Reg. 4/99 s.13)
    # both BC credits are labour credits wholly in respect of Canadian labour: PSTC 96,000 - (35,000 + 96,000) x 16% = 75,040
    assert res.post_adjustment_component_incentives_usd[PSTC] == pytest.approx(75_040.0)
    assert not any("Apportionment" in n for n in res.disclosed_limitations)                                 # a labour-only credit is not apportioned


def test_nova_scotia_awarded_amount_nets_the_pstc_and_never_the_cptc_labour():
    res = _pair(PSTC, 600_000.0, "CA-NS", NS, 600_000.0, 1_200_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.post_adjustment_component_incentives_usd[PSTC] == pytest.approx(96_000.0 - 150_000.0 * 0.16)  # 25% x 600,000 = 150,000 labour share; 72,000
    cptc = _pair(CPTC, 600_000.0, "CA-NS", NS, 600_000.0, 1_200_000.0)
    assert cptc.post_adjustment_component_incentives_usd[CPTC] == pytest.approx(150_000.0)                 # cap 60% x (1,200,000 - 150,000) = 630,000 > labour: unchanged


@pytest.mark.parametrize("fed,guaranteed", [(PSTC, 96_000.0), (CPTC, 150_000.0)])
def test_new_brunswick_potential_rides_beside_the_federal_credit_and_nets_nothing(fed, guaranteed):
    # The LIFT grant is discretionary: guaranteed ZERO, the 35% ceiling x 600,000 = 210,000 shown as conditional potential; the federal credit keeps its own value (PSTC 16% x 600,000 = 96,000;
    # CPTC 25% x min(600,000, 60% x 1,200,000) = 150,000) and nothing is netted until an award is stated.
    res = _pair(fed, 600_000.0, "CA-NB", NB, 600_000.0, 1_200_000.0)
    assert res.executable is True, res.rejection_reason
    assert res.total_guaranteed_incentive_usd == pytest.approx(guaranteed) and res.total_conditional_incentive_usd == pytest.approx(0.35 * 600_000.0)
    assert not [a for a in res.stacking_adjustments if a.adjustment_usd]


@pytest.mark.parametrize("fed", [PSTC, CPTC])
def test_saskatchewan_is_display_only_so_it_never_prices_and_is_never_unruled(fed):
    # The existing discretionary ruling (B1 DISPLAY_ONLY_ZERO_GUARANTEED) keeps the grant out of the pricing kernel; its pair is ruled, so the reason is the ruling, not a missing rule.
    res = _pair(fed, 600_000.0, "CA-SK", SK, 600_000.0, 1_200_000.0)
    assert "no named" not in (res.rejection_reason or "").lower() and "UNRESOLVED_NO_AUTHORITY" not in (res.rejection_reason or "")
    assert res.executable is False and SK in (res.rejection_reason or "")


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
    res = _dave_trio(PSTC, 600_000.0, 1_300_000.0)
    adj = next(a for a in res.stacking_adjustments if {a.program_a_id, a.program_b_id} == {DAVE, PSTC})
    assert "VERIFIED NETTING" in adj.description and "assumed allocation $0" in adj.description


def test_dave_has_no_base_when_the_budget_holds_no_animation_or_effects_labour():
    # ITA (BC) s.81.2(2): ALE is BC labour "directly attributable to prescribed digital animation or visual effects activities"; ordinary crew labour is never DAVE labour.
    res = _dave_trio(PSTC, 600_000.0, 1_300_000.0, vfx_category="btl_crew_labor")
    assert res.executable is False or res.raw_component_incentives_usd.get(DAVE, 0.0) == 0.0
