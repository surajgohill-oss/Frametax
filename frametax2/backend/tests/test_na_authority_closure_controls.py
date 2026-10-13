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
    assert profile.evidence.source_url.startswith("https://") and profile.evidence.access_date == "2026-10-12" and len(profile.evidence.notes) > 200


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
