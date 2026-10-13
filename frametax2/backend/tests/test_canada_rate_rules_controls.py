"""DB-free controls for the Canadian rate rules: which base each credit's rate applies to, and which statutory uplifts are rules on a
narrower base rather than whole-base rates. The end-to-end figures are in tests/heavy_synthetic/check_canada_labour_base_and_uplifts.py."""
from __future__ import annotations

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401  (registers the rules)
from app.data.program_rate_rules import get_subset_uplift_rules, resolve_program_rate

LABOUR_RATE_PROGRAMS = {
    "on_ofttc": ("on_ofttc_qualified_labour_usd", 0.35),
    "ca_mb_film_video_credit": ("ca_mb_qualified_labour_usd", 0.45),
    "ca_bc_pstc": ("ca_bc_pstc_qualified_labour_usd", 0.36),
}


@pytest.mark.parametrize("slug,key_rate", sorted(LABOUR_RATE_PROGRAMS.items()))
def test_labour_credits_apply_their_rate_to_the_traced_labour_basis_and_fail_closed_without_it(slug, key_rate):
    key, rate = key_rate
    r = resolve_program_rate(slug, production_type="feature_film", qpe_usd=3_000_000.0, amount_facts={key: 1_000_000.0})
    assert r is not None and r.modeled_rate == pytest.approx(rate) and r.floor_rate == pytest.approx(rate)
    assert not r.is_band_ceiling and r.has_guaranteed_floor and r.qpe_basis_used == 1_000_000.0, "the rate must be applied to the labour basis, not total QPE"
    assert resolve_program_rate(slug, production_type="feature_film", qpe_usd=3_000_000.0) is None


def test_all_spend_credits_keep_an_all_spend_base():
    for slug in ("on_opstc", "ca_nl_all_spend_credit", "ca_qc_pstc", "ca_nb_film_tax_credit", "ca_ns_production_incentive_fund"):
        r = resolve_program_rate(slug, production_type="feature_film", qpe_usd=3_000_000.0)
        assert r is not None and r.qpe_basis_used is None, slug


def test_whole_base_bonus_ceilings_are_gone_and_replaced_by_subset_rules():
    expected = {
        "ca_mb_film_video_credit": {"frequent_filming": .10, "manitoba_producer": .05, "rural_northern": .05},
        "ca_bc_pstc": {"regional": .06, "distant_location": .06},
        "on_ofttc": {"first_time_producer": .05, "regional_bonus": .10},
        "ca_qc_pstc": {"vfx_labour_enhancement": .16},
    }
    for slug, rules in expected.items():
        assert {r.uplift_id: r.rate for r in get_subset_uplift_rules(slug)} == rules, slug
    for slug in ("ca_mb_film_video_credit", "ca_bc_pstc"):
        r = resolve_program_rate(slug, production_type="feature_film", qpe_usd=3_000_000.0, amount_facts={LABOUR_RATE_PROGRAMS[slug][0]: 1_000_000.0})
        assert not r.is_band_ceiling, f"{slug}: no whole-base ceiling tier may remain"
    ftp = {r.uplift_id: r for r in get_subset_uplift_rules("on_ofttc")}["first_time_producer"]
    assert ftp.base_cap_usd == 240_000.0 and ftp.potential_requires_prerequisite, "enhanced rate is on the first $240,000 only and only by stated election"
    assert {r.uplift_id: r for r in get_subset_uplift_rules("ca_qc_pstc")}["vfx_labour_enhancement"].eligible_categories == frozenset({"vfx"})


def test_nova_scotia_prices_the_stream_ii_base_on_all_eligible_cost_not_labour_only():
    # CCTH Nova Scotia Film & Television Production Incentive Fund Guidelines (April 1, 2024) s.6.2: Stream II base 25% of "all Eligible Nova Scotia Costs" -- the earlier
    # labour-only reading came from one secondary source and is superseded; no labour fact is required and the whole segment spend is the base.
    r = resolve_program_rate("ca_ns_production_incentive_fund", production_type="feature_film", qpe_usd=3_000_000.0)
    assert r is not None and r.modeled_rate == pytest.approx(0.25) and r.floor_rate == pytest.approx(0.25) and not r.is_band_ceiling
    assert r.qpe_basis_used is None, "the rate applies to the whole qualifying Nova Scotia spend"
    from app.data.program_rate_rules import get_incentive_value_cap
    cap = get_incentive_value_cap("ca_ns_production_incentive_fund")
    assert (cap.cap_currency, cap.cap_native_amount) == ("CAD", 10_000_000.0)                       # s.3.1(e)
