"""NA-RECONCILIATION-12: the seven coverage-only US programs now have rate records. Every expectation is hand arithmetic from the figure the official source states
(Ohio Revised Code 122.85; WVDED page; NJ Division of Taxation; Missouri Film Office; AEDC; MCA 15-31-1007 and Commerce; Tax Law 24-D; Virginia Taxation; Utah Film Commission FAQ)."""
from __future__ import annotations

import pytest

from tests.test_us_ca_mx_scope_integrity_controls import _price
import app.data.program_rate_rules_worldwide  # noqa: F401


def test_ohio_pays_30_percent_only_when_the_base_exceeds_300000():
    assert _price("US-OH", "us_oh_motion_picture_tax_credit", 1_000_000.0).incentive_floor_usd == pytest.approx(300_000.0)      # 30% x 1,000,000
    below = _price("US-OH", "us_oh_motion_picture_tax_credit", 300_000.0)
    assert not below.executable or (below.incentive_floor_usd or 0) == 0                                                          # "less than or equal to three hundred thousand dollars, no credit"


def test_west_virginia_guarantees_27_percent_and_shows_31_as_an_unconfirmed_planning_ceiling():
    seg = _price("US-WV", "us_wv_film_production_tax_credit", 500_000.0)
    assert seg.incentive_floor_usd == pytest.approx(135_000.0)                                                                    # 27% x 500,000
    assert seg.ceiling_requires_confirmation or seg.is_band_ceiling or (seg.incentive_ceiling_usd or 0) >= pytest.approx(155_000.0)   # 31% x 500,000 needs the 10-resident hire fact


def test_new_jersey_guarantees_the_30_percent_location_rate_and_needs_a_fact_for_35():
    seg = _price("US-NJ", "us_nj_garden_state_film_credit", 2_000_000.0)
    assert seg.incentive_floor_usd == pytest.approx(600_000.0)                                                                    # 30% x 2,000,000 (35% only outside the 30-mile radius, stated)


def test_missouri_guarantees_20_percent_above_the_minimum_spend():
    assert _price("US-MO", "us_mo_motion_media_production_tax_credit", 1_000_000.0).incentive_floor_usd == pytest.approx(200_000.0)   # 20% x 1,000,000


def test_new_york_independent_guarantees_30_percent():
    assert _price("US-NY", "us_ny_empire_state_independent_film_credit", 1_000_000.0).incentive_floor_usd == pytest.approx(300_000.0)  # Tax Law 24-D(a)(2)(i)


@pytest.mark.parametrize("jur,slug,rate", [("US-AR", "us_ar_digital_motion_picture_incentive", 0.30), ("US-MT", "us_mt_media_act_tax_credit", 0.20), ("US-CO", "us_co_film_income_tax_credit", 0.22)])
def test_discretionary_or_paused_programs_show_potential_with_a_zero_guaranteed_floor(jur, slug, rate):
    seg = _price(jur, slug, 1_000_000.0)
    assert seg.executable and seg.incentive_floor_usd == 0.0 and seg.ceiling_requires_confirmation
    assert seg.incentive_ceiling_usd == pytest.approx(rate * 1_000_000.0)                  # the stated ceiling x 1,000,000, never guaranteed


def test_virginia_and_utah_keep_their_thresholds_after_the_official_pages_were_read():
    assert _price("US-VA", "us_va_motion_picture_credit", 1_000_000.0).incentive_floor_usd == pytest.approx(150_000.0)               # 15% x 1,000,000, qualified spend of at least 250,000
    assert _price("US-UT", "us_ut_motion_picture_incentive", 1_000_000.0).incentive_floor_usd == pytest.approx(200_000.0)             # 20% base over 500,000


def test_each_new_program_has_a_profile_with_a_cited_primary_source_and_binds_its_proposal_identity():
    from app.data import authority_coverage_registry as acr
    from app.data.program_requirements import get_program_requirements
    bound = {"proposed_united_states_ohio_ohio_motion_picture_tax_credit": "us_oh_motion_picture_tax_credit",
             "proposed_united_states_west_virginia_west_virginia_film_production_tax_credit": "us_wv_film_production_tax_credit",
             "proposed_united_states_missouri_motion_media_production_tax_credit": "us_mo_motion_media_production_tax_credit",
             "proposed_united_states_montana_media_tax_credit": "us_mt_media_act_tax_credit",
             "proposed_united_states_arkansas_digital_product_and_motion_picture_industry_incentive": "us_ar_digital_motion_picture_incentive",
             "proposed_united_states_new_jersey_garden_state_film_and_digital_media_jobs_act_film_credit": "us_nj_garden_state_film_credit",
             "proposed_united_states_new_york_empire_state_independent_film_production_credit": "us_ny_empire_state_independent_film_credit"}
    for proposal, slug in bound.items():
        assert acr.CANONICAL_RUNTIME_SLUG_BINDINGS[proposal] == slug
        prof = get_program_requirements(slug)
        assert prof is not None and prof.evidence is not None and prof.evidence.source_url and prof.evidence.access_date == "2026-10-13"
