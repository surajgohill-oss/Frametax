"""NA-RECONCILIATION-09 (2026-10-12): the authority persisted this pass is connected to runtime and recorded with its source. DB-free and isolated; expectations are independent arithmetic from the
cited statutes, never copied from the implementation.

Sources (each also recorded in its canonical owner: the DoctrineRecord provenance, the requirements EvidenceRecord, or the stacking rule text):
  * Colorado: C.R.S. 24-48.5-116(1) as amended by Session Laws 2022 ch. 355: 20% of qualified local expenditures; USD 1,000,000 for a company that does not originate production in Colorado.
  * Hawaii: HRS 235-17(a), (d)(2): 22% (county over 700,000) / 27% (other counties); qualified production costs of at least USD 100,000.
  * Arizona: A.R.S. 43-1165(A)(1): 15% up to USD 10,000,000 spend, 17.5% above 10,000,000 and below 35,000,000, 20% above 35,000,000; +2.5% facility, +2.5% long-term tenant; no minimum.
  * Federal PSTC: ITA 125.5(1)(b) and CRA RC4385: provincial credits are assistance reasonably in respect of labour; BC Income Tax Act s.79(1) and Revenu Québec CO-1029.8.36.SP note 7: the federal
    PSTC is not assistance to the BC or Quebec credit."""
from __future__ import annotations

import pytest

from app.data import program_authority_provenance as pa
from app.data import program_requirements as pr
from app.data.program_rate_rules import get_rate_rules, resolve_program_rate
from app.calculators.structural_archetype_generator import generate_structural_candidate
from tests.test_structural_archetype_generator import _comp


def _rate(slug, qpe):
    r = resolve_program_rate(slug, "feature_film", qpe)
    return None if r is None else (round(r.floor_rate, 4), round(r.modeled_rate, 4))


def test_colorado_prices_only_at_or_above_one_million_of_qualified_local_expenditures():
    assert _rate("us_co_film_incentive", 999_999.0) is None
    assert _rate("us_co_film_incentive", 1_000_000.0) == (0.20, 0.20)


def test_hawaii_is_22_percent_with_the_27_percent_neighbor_island_ceiling_from_one_hundred_thousand():
    assert _rate("us_hi_film_digital_media_credit", 99_999.0) is None
    assert _rate("us_hi_film_digital_media_credit", 100_000.0) == (0.22, 0.27)


@pytest.mark.parametrize("spend,expected", [(1_000_000.0, (0.15, 0.20)), (10_000_000.0, (0.15, 0.20)), (10_000_001.0, (0.175, 0.225)), (34_999_999.0, (0.175, 0.225)),
                                            (35_000_001.0, (0.20, 0.25))])
def test_arizona_tiers_are_set_by_total_qualified_spend_with_no_minimum(spend, expected):
    assert _rate("us_az_motion_picture_production", spend) == expected
    assert _rate("us_az_motion_picture_production", 1.0) == (0.15, 0.20), "no minimum spend exists in A.R.S. 43-1165 or 41-1517"


_PROFILED_THIS_PASS = ["us_co_film_incentive", "us_hi_film_digital_media_credit", "us_az_motion_picture_production", "ca_nl_all_spend_credit",
                       "ontario_computer_animation_and_special_effects_tax_credit_ocase", "ca_federal_cptc"]
_RATE_PROVENANCE_THIS_PASS = ["us_co_film_incentive", "us_hi_film_digital_media_credit", "us_az_motion_picture_production", "ca_federal_pstc", "ca_federal_cptc", "ca_qc_pstc",
                              "ontario_computer_animation_and_special_effects_tax_credit_ocase"]


@pytest.mark.parametrize("slug", _RATE_PROVENANCE_THIS_PASS)
def test_every_rate_doctrine_closed_this_pass_is_verified_with_a_primary_source_and_pinpoint(slug):
    assert pa.authority_disposition(slug) == pa.AUTHORITY_VERIFIED_PRICEABLE
    for rule in get_rate_rules(slug):
        prov = rule.provenance
        assert prov is not None and prov.source_url.startswith("https://") and prov.citation_detail


@pytest.mark.parametrize("slug", _PROFILED_THIS_PASS)
def test_every_requirements_profile_registered_this_pass_is_primary_verified_and_dated(slug):
    profile = pr.get_program_requirements(slug)
    assert profile is not None and pr.verification_state(slug) == pr.VerificationState.PRIMARY_VERIFIED
    assert profile.evidence.source_url.startswith("https://") and profile.evidence.access_date in ("2026-10-12", "2026-10-13") and len(profile.evidence.notes) > 200


def test_the_evidence_records_name_their_retrieval_failures_and_contradictions():
    assert "coloradofilm.org" in pr.get_program_requirements("us_co_film_incentive").evidence.notes
    assert "SB 2580" in pr.get_program_requirements("us_hi_film_digital_media_credit").evidence.notes
    assert "USD 250,000" in pr.get_program_requirements("us_az_motion_picture_production").evidence.notes
    assert "10 million" in pr.get_program_requirements("ca_nl_all_spend_credit").evidence.notes


def _pstc_with(partner_slug, partner_jur, partner_amount, partner_category="atl_director", pstc_amount=1_000_000.0, gross=3_000_000.0):
    return generate_structural_candidate(
        [_comp("ca_federal_pstc", "CA", pstc_amount, line_id="PSTC", spend_category="atl_director"),
         _comp(partner_slug, partner_jur, partner_amount, line_id="PARTNER", spend_category=partner_category)], gross_budget_usd=gross)


def test_the_bc_credit_is_a_labour_credit_and_nets_the_federal_pstc_in_full():
    res = _pstc_with("ca_bc_pstc", "CA-BC", 600_000.0)
    assert res.executable is True, res.rejection_reason
    # PSTC 16% x 1,000,000 = 160,000; BC 36% x 600,000 = 216,000, wholly labour: min(216,000; 36% x 1,000,000) = 216,000 x 16% = 34,560 -> 125,440; BC unchanged.
    assert res.post_adjustment_component_incentives_usd == {"ca_federal_pstc": 125_440.0, "ca_bc_pstc": 216_000.0}
    assert not any("Apportionment assumption" in n for n in res.disclosed_limitations)


def test_the_quebec_credit_nets_its_labour_share_and_discloses_the_whole_credit_lower_bound():
    res = _pstc_with("ca_qc_pstc", "CA-QC", 1_000_000.0, pstc_amount=500_000.0, gross=1_500_000.0)
    assert res.executable is True, res.rejection_reason
    # PSTC 16% x 500,000 = 80,000; Quebec 25% x 1,000,000 = 250,000 on all-spend cost; labour portion min(250,000; 25% x 500,000 = 125,000) = 125,000 x 16% = 20,000 -> 60,000.
    assert res.post_adjustment_component_incentives_usd == {"ca_federal_pstc": 60_000.0, "ca_qc_pstc": 250_000.0}
    # whole-credit lower bound: min(250,000; 500,000) x 16% = 40,000 -> 40,000 (stated in the disclosure)
    assert any("Apportionment assumption" in n and "$40,000" in n for n in res.disclosed_limitations)


def test_the_federal_pstc_never_reduces_the_bc_or_quebec_credit():
    for slug, jur in (("ca_bc_pstc", "CA-BC"), ("ca_qc_pstc", "CA-QC")):
        res = _pstc_with(slug, jur, 1_000_000.0, pstc_amount=500_000.0, gross=1_500_000.0)
        before = res.post_adjustment_component_incentives_usd[slug]
        rate = 0.36 if slug == "ca_bc_pstc" else 0.25
        assert before == pytest.approx(rate * 1_000_000.0), (slug, "the partner keeps its full credit")


# ── NA-RECONCILIATION-10: a missing producer fact reaches qualification state and economics certainty, not only warning text ──────────────────────────────────────────────────
from app.calculators.allocation_pricing import presumed_facts_from_resolution
from app.services.canonical_evaluation import _QUALIFICATION_ADMITS_RECOMMENDED, _rate_condition_qualification_impact

_PRODUCER_FACT_CASES = [
    # slug, qpe, amount facts, (evidenced fact ids), the conditions they clear. The CPTC certificate/control, the NL Part I registration, the Colorado pre-approval and the OCASE permanent
    # establishment are the Inspector's CONTENT-GATE keys (one persistence owner: POST /projects/{id}/content-gates); the rest are program-facts keys.
    ("ca_federal_cptc", 1_000_000.0, {"ca_federal_cptc_qualified_labour_usd": 300_000.0},
     ("ca_federal_cptc__cultural_test_confirmed", "ca_federal_cptc__local_entity_or_partner_confirmed"),
     {"ca-cptc-content-certification-required", "ca-cptc-canadian-controlled-corporation"}),
    ("on_opstc", 2_000_000.0, {}, ("on_opstc_ontario_labour_25pct_confirmed",), {"ca-on-labour-ratio-gate"}),
    ("ontario_computer_animation_and_special_effects_tax_credit_ocase", 1_000_000.0, {"on_ocase_qualifying_vfx_labour_usd": 100_000.0},
     ("ontario_computer_animation_and_special_effects_tax_credit_ocase__local_entity_or_partner_confirmed", "on_ocase_ontario_labour_over_cad_25000_stated"),
     {"on-ocase-permanent-establishment", "on-ocase-labour-over-cad-25000"}),
    ("ca_nl_all_spend_credit", 2_000_000.0, {}, ("ca_nl_all_spend_credit__agency_preapproval_confirmed",), {"ca-nl-part1-registration-required"}),
    ("us_co_film_incentive", 2_000_000.0, {}, ("us_co_film_incentive__agency_preapproval_confirmed", "us_co_workforce_50pct_and_cpa_review_stated"),
     {"us-co-preapproval-before-production", "us-co-workforce-and-cpa-review"}),
]


@pytest.mark.parametrize("slug,qpe,amounts,facts,conditions", _PRODUCER_FACT_CASES)
def test_a_missing_producer_fact_holds_the_program_at_user_fact_required_and_a_stated_one_clears_it(slug, qpe, amounts, facts, conditions):
    bare = resolve_program_rate(slug, "feature_film", qpe, amount_facts=amounts)
    stated = resolve_program_rate(slug, "feature_film", qpe, amount_facts=amounts, evidenced_facts=frozenset(facts))
    assert bare is not None and stated is not None, "the conditions are non-gating: the planning figure prices either way"
    assert bare.modeled_rate == stated.modeled_rate and bare.floor_rate == stated.floor_rate
    state, culprits = _rate_condition_qualification_impact(bare)
    assert state == "USER_FACT_REQUIRED" and state not in _QUALIFICATION_ADMITS_RECOMMENDED and conditions <= set(culprits)
    assert conditions <= {p["condition_id"] for p in presumed_facts_from_resolution(bare)}, "feeds claim_base_missing_facts and so economics_certainty"
    assert _rate_condition_qualification_impact(stated) is None
    assert not presumed_facts_from_resolution(stated)


def test_every_producer_fact_has_exactly_one_persistence_owner():
    """A proposition that is a content/approval gate is written ONLY through the content-gate control; every other fact only through program-facts. No key is in both."""
    from app.services.ny_producer_facts import NY_EVIDENCED_FACTS
    from app.services.program_content_gates import GATE_FACT_PREFIX, gate_control_whitelist
    gate_keys = {k for k in gate_control_whitelist()}
    assert not (gate_keys & set(NY_EVIDENCED_FACTS)), "a fact must not have two writers"
    for *_x, facts, _c in _PRODUCER_FACT_CASES:
        for f in facts:
            assert (f in NY_EVIDENCED_FACTS) != (f in gate_keys), f"{f}: exactly one owner"
    assert GATE_FACT_PREFIX == "evidenced_program_fact:"


def test_no_boolean_fact_referenced_by_a_north_american_rate_rule_lacks_a_producer_writer():
    from app.data.program_rate_rules import SUBSET_UPLIFT_RULES, get_rate_rules
    from app.services import na_canonical_reconciliation as na
    from app.services.ny_producer_facts import NY_EVIDENCED_FACTS
    from app.services.program_content_gates import gate_control_whitelist
    writers = set(NY_EVIDENCED_FACTS) | set(gate_control_whitelist())
    missing: dict[str, set[str]] = {}
    for slug in na.frozen_universe()["rate_bearing"]:
        keys = set()
        for rule in get_rate_rules(slug):
            for c in rule.conditions:
                keys |= {k for k in (c.required_boolean_fact_key, c.superseded_by_boolean_fact_key, c.regional_uplift_multiplier_fact_key, *c.blocked_by_boolean_fact_keys) if k}
        for up in SUBSET_UPLIFT_RULES.get(slug, ()):
            keys |= {k for k in (up.prerequisite_fact, up.whole_base_fact, up.excluded_fact) if k}
        for k in keys - writers:
            missing.setdefault(k, set()).add(slug)
    assert missing == {}, missing


def test_texas_award_numbers_have_a_validated_numeric_writer():
    from app.services.ny_producer_facts import PROGRAM_AMOUNT_FACTS
    assert set(PROGRAM_AMOUNT_FACTS) == {"us_tx_miip_awarded_rate_pct", "us_tx_miip_resident_crew_pct", "us_tx_miip_resident_cast_pct"}
    assert PROGRAM_AMOUNT_FACTS["us_tx_miip_awarded_rate_pct"] == (0.0, 0.31), "a fraction within the 31% ceiling, as the RateRule validates it"
    assert PROGRAM_AMOUNT_FACTS["us_tx_miip_resident_crew_pct"] == (0.0, 100.0)


def test_pennsylvania_aggregate_cast_cap_excludes_only_the_excess_above_fifteen_million():
    from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register

    def run(slug, c1, c2):
        lines = [BudgetLine("2000", "CAST A", c1, spend_category="atl_cast", line_id="c1"), BudgetLine("2100", "CAST B", c2, spend_category="atl_cast", line_id="c2"),
                 BudgetLine("3000", "CREW", 1_000_000.0, spend_category="btl_crew_labor", line_id="k1")]
        reg = derive_qualification_register(lines, slug, ProductionFacts("US-PA"), 0.25)
        q = sum(e.amount_usd for e in reg if getattr(e.state, "value", e.state) == "qualifies" and e.line_id in ("c1", "c2"))
        x = sum(e.amount_usd for e in reg if getattr(e.state, "value", e.state) == "excluded")
        crew = sum(e.amount_usd for e in reg if e.line_id == "k1" and getattr(e.state, "value", e.state) == "qualifies")
        return q, x, crew
    assert run("us_pa_film_production_credit", 9_000_000.0, 6_000_000.0) == (15_000_000.0, 0.0, 1_000_000.0), "exactly at the cap: unchanged"
    assert run("us_pa_film_production_credit", 12_000_000.0, 8_000_000.0) == (15_000_000.0, 5_000_000.0, 1_000_000.0), "20,000,000 cast: 5,000,000 excluded, crew untouched"
    assert run("us_ga_film_credit", 12_000_000.0, 8_000_000.0)[1] == 0.0, "no other program is affected"
    # 25% x 5,000,000 = 1,250,000 of credit that the cap removes
    assert round(0.25 * run("us_pa_film_production_credit", 12_000_000.0, 8_000_000.0)[1], 2) == 1_250_000.0


def test_the_pennsylvania_cap_record_corrects_the_per_person_misstatement_and_names_the_open_interpretation():
    facts = pr.get_program_requirements("us_pa_film_production_credit").additional_facts
    assert "not a per-person limit" in facts["compensation_cap"] and "wpdmdl=75431" in facts["compensation_cap"]
    assert "OPEN interpretation" in facts["compensation_cap_statute_contradiction"] and "wpdmdl=75381" in facts["compensation_cap_statute_contradiction"]


def test_manitoba_now_carries_structured_primary_provenance_and_is_no_longer_an_unresolved_residual():
    from app.data.authority_coverage_registry import coverage_state
    assert pa.authority_disposition("ca_mb_film_video_credit") == pa.AUTHORITY_VERIFIED_PRICEABLE
    assert coverage_state("ca_mb_film_video_credit") != "AUTHORITY_UNRESOLVED_NON_PRICEABLE"
    prov = get_rate_rules("ca_mb_film_video_credit")[0].provenance
    assert prov.source_url == "https://www.gov.mb.ca/finance/business/ccredits.html" and prov.verified_date == "2026-10-13" and "s.7.5" in prov.citation_detail


def test_newfoundland_regulation_31_23_is_the_recorded_authority_and_the_federal_credits_do_not_reduce_the_nl_base():
    prov = get_rate_rules("ca_nl_all_spend_credit")[0].provenance
    assert "Regulation 31/23" in prov.interpretation_note and "s.2(m)" in prov.interpretation_note and prov.verified_date == "2026-10-13"
    from app.calculators.canonical_stack_bridge import NL_SLUG, PSTC_APPORTIONED_SLUGS, PSTC_ASSISTING_SLUGS, _SPEND_REDUCTION_DIRECTION
    assert NL_SLUG in PSTC_ASSISTING_SLUGS and NL_SLUG in PSTC_APPORTIONED_SLUGS
    assert _SPEND_REDUCTION_DIRECTION[frozenset({"ca_federal_pstc", NL_SLUG})] == NL_SLUG, "the NL credit is the reducing (assistance) program, never the federal credit"
    assert _SPEND_REDUCTION_DIRECTION[frozenset({"ca_federal_cptc", NL_SLUG})] == NL_SLUG


def test_the_nl_credit_nets_the_federal_pstc_by_its_labour_share_only():
    res = _pstc_with("ca_nl_all_spend_credit", "CA-NL", 1_000_000.0, pstc_amount=500_000.0, gross=1_500_000.0)
    assert res.executable is True, res.rejection_reason
    # PSTC 16% x 500,000 of labour = 80,000. NL 40% x 1,000,000 = 400,000 on all-spend cost;
    # its labour share = min(400,000; 40% x PSTC labour basis 500,000 = 200,000) = 200,000 -> PSTC reduced by 200,000 x 16% = 32,000 -> 48,000; NL unchanged.
    assert res.post_adjustment_component_incentives_usd["ca_nl_all_spend_credit"] == pytest.approx(400_000.0)
    assert res.post_adjustment_component_incentives_usd["ca_federal_pstc"] == pytest.approx(80_000.0 - 0.16 * 200_000.0)
    assert any("Apportionment assumption" in n and "Newfoundland and Labrador" in n for n in res.disclosed_limitations)


def test_california_prospective_planning_is_dated_and_the_historical_letter_is_reference_only():
    from app.calculators.allocation_pricing import CALIFORNIA_REGIME_NOTE, _PLANNING_ASSUMPTION_NOTES
    assert _PLANNING_ASSUMPTION_NOTES["ca_film_30"] == (CALIFORNIA_REGIME_NOTE,)
    assert "January 1, 2026" in CALIFORNIA_REGIME_NOTE and "July 1, 2025" in CALIFORNIA_REGIME_NOTE
    assert "historical reference" in CALIFORNIA_REGIME_NOTE and "never repriced" in CALIFORNIA_REGIME_NOTE and "none is established" in CALIFORNIA_REGIME_NOTE


def test_the_nl_cad_20_million_cap_binds_as_a_native_currency_cap_not_a_par_usd_figure():
    from tests.test_us_ca_mx_scope_integrity_controls import _price
    from app.data.program_rate_rules import get_incentive_value_cap
    from app.data.executable_jurisdiction_registry import get_doctrine
    assert get_doctrine("ca_nl_all_spend_credit").annual_cap_usd is None, "the old CAD-USD par annual cap is gone"
    cap = get_incentive_value_cap("ca_nl_all_spend_credit")
    assert cap.cap_currency == "CAD" and cap.cap_native_amount == 20_000_000.0
    big = _price("CA-NL", "ca_nl_all_spend_credit", 60_000_000.0)       # 40% x 60,000,000 = 24,000,000 before the cap
    small = _price("CA-NL", "ca_nl_all_spend_credit", 10_000_000.0)     # 4,000,000: untouched
    assert small.incentive_floor_usd == pytest.approx(4_000_000.0)
    assert big.incentive_cap_type == "per_project_native" and big.incentive_floor_usd == pytest.approx(big.incentive_cap_usd)
    assert big.incentive_floor_usd < 24_000_000.0 and big.incentive_uncapped_usd == pytest.approx(24_000_000.0)


def test_colorado_wage_cap_is_one_million_per_identified_payee_and_nothing_else_is_touched():
    from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
    lines = [BudgetLine("2000", "LEAD", 1_500_000.0, spend_category="atl_cast", line_id="c1"), BudgetLine("3000", "CREW", 400_000.0, spend_category="btl_crew_labor", line_id="k1")]

    def amounts(payees):
        reg = derive_qualification_register(lines, "us_co_film_incentive", ProductionFacts("US-CO", ny_atl_payee_by_line=payees), 0.20)
        state = lambda e: getattr(e.state, "value", e.state)
        return (sum(e.amount_usd for e in reg if state(e) == "qualifies"), sum(e.amount_usd for e in reg if state(e) == "excluded"))
    # C.R.S. 24-48.5-114(7)(i): wages up to one million dollars per employee or contractor, any excess excluded - applied only to an identified payee
    assert amounts({"c1": 1}) == (1_400_000.0, 500_000.0)
    assert amounts({}) == (1_900_000.0, 0.0), "an unidentified account is carried as a planning figure, never silently capped or uncapped as certain"
    assert round(0.20 * 500_000.0, 2) == 100_000.0
