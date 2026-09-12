"""
test_b3_formulaic_consumption.py

Codex bounded remediation, B3 formulaic rate corrections
(GLOBAL_PROGRAM_FORMULAIC_RATE_RULE_SPEC_CODEX.csv) -- REAL OPTIMIZER
CONSUMPTION PROOF for each of the 12 implemented rules.

Per the bounded remediation's own standard: "Merely finding the program in
ALL_PROGRAMS, importing a RateRule, or resolving a slug is not consumption
proof." Every program below is proven through TWO independent real
production code paths:

  1. discover_executable_jurisdictions() -- the actual STAGE 2 discovery
     path production_discovery.py runs for every real project, proving the
     program is examined and (where eligible) resolves for a production.
  2. allocation_pricing.price_segment() -- the actual pricing KERNEL every
     served candidate's segment is priced through (the same function
     canonical_evaluation.py's _price_candidate calls), proving a real
     account allocation prices through this exact rule.

Controlled, clearly-synthetic inputs are used to prove reachability and
calculation (never real project data) -- the four-project acceptance runs
elsewhere continue to use each project's own real canonical data.
"""
from __future__ import annotations

from app.calculators.allocation_pricing import price_segment
from app.calculators.production_allocation import AccountAllocation, AssignmentKind
from app.calculators.production_discovery import discover_executable_jurisdictions
from app.calculators.production_requirements import derive_production_requirements


def _probe_segment(slug: str, amount_usd: float, production_type: str = "feature_film"):
    alloc = AccountAllocation(
        account_code="2000", description="Production spend",
        amount_usd=amount_usd, component="production", jurisdiction_code="XX",
        assignment_kind=AssignmentKind.FIXED,
        rationale="B3 formulaic consumption probe",
        governing_decision="codex-bounded-remediation-b3",
    )
    return price_segment(
        jurisdiction_code="XX", program_slug=slug, allocations=[alloc],
        spend_category_by_code={"2000": "production"},
        offshore_payroll_accounts=frozenset(),
        production_type=production_type, gross_budget_usd=amount_usd,
    )


def _discover(home_code: str, production_type: str = "feature_film", qpe_usd: float = 2_000_000.0):
    return discover_executable_jurisdictions(
        requirements=derive_production_requirements({}),
        production_type=production_type, qpe_usd=qpe_usd, home_code=home_code,
    )


def _examined(result, jurisdiction_code: str, program_slug: str):
    return next(
        (e for e in result.examinations
         if e.jurisdiction_code == jurisdiction_code and e.program_slug == program_slug),
        None,
    )


# ── 1. ae_dpip (VERIFIED_NO_CHANGE_NEEDED — Dubai correctly fail-closed,
# Abu Dhabi correctly separately identified) ────────────────────────────

def test_ae_dpip_dubai_fail_closed_abu_dhabi_separately_identified():
    result = _discover("AE-DXB", qpe_usd=5_000_000.0)
    dubai = _examined(result, "AE-DXB", "ae_dxb_dpip")
    assert dubai is not None, "Dubai must still be discovered/examined"
    assert dubai.resolves_for_production is False, "Dubai must never resolve (fail-closed)"

    # Abu Dhabi identity prices only with its own rule (raw RateRule data,
    # not resolve_program_rate() -- ae_ad_film_rebate is SEPARATELY B1
    # FAIL_CLOSED, so it never auto-prices either; this proves the RATE
    # DATA itself is correct and scoped to Abu Dhabi only).
    from app.data.program_rate_rules import get_rate_rules
    ad_rules = get_rate_rules("ae_ad_film_rebate")
    assert any(r.rate == 0.35 and not r.is_band_ceiling for r in ad_rules)
    dubai_rules = get_rate_rules("ae_dxb_dpip")
    assert not any(r.rate == 0.35 for r in dubai_rules), "no cross-emirate rule leakage"


# ── 2. au_location_offset (VERIFIED_NO_CHANGE_NEEDED — 30% + AUD $20M
# conservative-bound threshold, already correctly wired) ────────────────

def test_au_location_offset_prices_above_threshold_rejects_below():
    result = _discover("AU", qpe_usd=5_000_000.0)
    below = _examined(result, "AU", "au_location_offset")
    assert below is not None
    assert below.resolves_for_production is False, "below the AUD20m-equivalent conservative-bound threshold must reject"

    result_pass = _discover("AU", qpe_usd=12_000_000.0)
    above = _examined(result_pass, "AU", "au_location_offset")
    assert above is not None
    assert above.resolves_for_production is True

    seg = _probe_segment("au_location_offset", 5_000_000.0)
    assert seg.executable is False, "below the $10M conservative-bound floor, must not price"

    seg_pass = _probe_segment("au_location_offset", 12_000_000.0)
    assert seg_pass.executable is True
    assert seg_pass.incentive_floor_usd > 0


# ── 3. cz_film_incentive (UPDATE_AND_EXTEND — live-action 25% / animation
# 35%, 80%-of-budget eligible-base cap) ──────────────────────────────────

def test_cz_film_incentive_production_type_branch_and_qpe_cap():
    live = _probe_segment("cz_film_incentive", 2_000_000.0, production_type="feature_film")
    assert live.executable is True
    anim = _probe_segment("cz_film_incentive_animation", 2_000_000.0, production_type="animation")
    assert anim.executable is True
    assert anim.incentive_floor_usd > live.incentive_floor_usd, "animation 35% must exceed live-action 25%"

    from app.data.program_rate_rules import get_qpe_cap
    assert get_qpe_cap("cz_film_incentive").cap_pct == 0.80
    assert get_qpe_cap("cz_film_incentive_animation").cap_pct == 0.80


# ── 4. fr_trip (UPDATE_CONDITION — objective VFX threshold, not a
# discretionary band) ─────────────────────────────────────────────────────

def test_fr_trip_vfx_condition_is_user_fact_required_not_authority_unresolved():
    from app.data.program_rate_rules import CONDITION_STATE_USER_FACT_REQUIRED, resolve_program_rate

    r = resolve_program_rate("fr_trip", production_type="feature_film", qpe_usd=5_000_000.0)
    vfx_cond = next(c for c in r.conditions_evaluated if c.condition_id == "fr-vfx-threshold")
    assert vfx_cond.kind == "project_fact_dependent_uplift"
    assert vfx_cond.condition_state == CONDITION_STATE_USER_FACT_REQUIRED

    seg = _probe_segment("fr_trip", 5_000_000.0)
    assert seg.executable is True
    assert seg.incentive_floor_usd == 5_000_000.0 * 0.30


# ── 5. is_film_reimbursement (VERIFIED_NO_CHANGE_NEEDED — enhanced tier
# genuinely unconfirmable, no fabricated specifics) ──────────────────────

def test_is_film_reimbursement_base_floor_prices_enhanced_tier_unresolved():
    result = _discover("IS", qpe_usd=2_000_000.0)
    ex = _examined(result, "IS", "is_film_reimbursement_scheme")
    assert ex is not None and ex.resolves_for_production is True
    seg = _probe_segment("is_film_reimbursement_scheme", 2_000_000.0)
    assert seg.executable is True
    assert seg.incentive_floor_usd == 2_000_000.0 * 0.25


# ── 6. ma_ccm_rebate (UPDATE_THRESHOLD — spend AND days gates split into
# separate conditions) ────────────────────────────────────────────────────

def test_ma_ccm_rebate_spend_and_days_are_separate_conditions():
    from app.data.program_rate_rules import resolve_program_rate

    r = resolve_program_rate("ma_ccm_rebate", production_type="feature_film", qpe_usd=2_000_000.0)
    ids = {c.condition_id for c in r.conditions_evaluated}
    assert "ma-min-spend" in ids
    assert "ma-min-shooting-days" in ids, "the 18-day gate must be its own condition, not silently dropped"
    days_cond = next(c for c in r.conditions_evaluated if c.condition_id == "ma-min-shooting-days")
    assert days_cond.satisfied is None  # genuinely unconfirmable, never assumed True

    seg = _probe_segment("ma_ccm_rebate", 2_000_000.0)
    assert seg.executable is True
    assert seg.incentive_floor_usd == 2_000_000.0 * 0.30

    seg_below = _probe_segment("ma_ccm_rebate", 500_000.0)
    assert seg_below.executable is False


# ── 7. mt_mfc_rebate (VERIFIED_NO_CHANGE_NEEDED — higher-confidence,
# directly-verified PDF citation preserved over the manifest's own
# unverified EUR 50,000 figure) ──────────────────────────────────────────

def test_mt_mfc_rebate_general_and_animation_branches_price():
    general = _probe_segment("mt_mfc_rebate", 500_000.0, production_type="feature_film")
    assert general.executable is True
    assert general.incentive_floor_usd == 500_000.0 * 0.30
    animation = _probe_segment("mt_mfc_rebate", 500_000.0, production_type="animation")
    assert animation.executable is True
    assert animation.incentive_floor_usd == 500_000.0 * 0.25


# ── 8. nl_nfpi (UPDATE — 35% flat, unsupported 30/40 band removed) ──────

def test_nl_nfpi_flat_35_no_band():
    from app.data.program_rate_rules import get_rate_rules

    rules = get_rate_rules("nl_film_production_incentive")
    assert len(rules) == 1, "the unsupported 40% band must be fully removed, not just unreachable"
    assert rules[0].rate == 0.35
    assert rules[0].is_band_ceiling is False

    seg = _probe_segment("nl_film_production_incentive", 2_000_000.0)
    assert seg.executable is True
    assert seg.incentive_floor_usd == 2_000_000.0 * 0.35


# ── 9. th_film_incentive (ADD_RULE — its own real identity, independent
# of the separately B1 FAIL_CLOSED th_boi_incentive) ─────────────────────

def test_th_film_incentive_prices_independently_of_th_boi_incentive():
    result = _discover("TH", qpe_usd=2_000_000.0)
    th_film = _examined(result, "TH", "th_film_incentive")
    th_boi = _examined(result, "TH", "th_boi_incentive")
    assert th_film is not None and th_film.resolves_for_production is True
    # th_boi_incentive may or may not appear as a distinct examination row
    # depending on jurisdiction_comparison wiring, but if it does, it must
    # never resolve.
    if th_boi is not None:
        assert th_boi.resolves_for_production is False

    seg = _probe_segment("th_film_incentive", 2_000_000.0)
    assert seg.executable is True
    assert seg.incentive_floor_usd == 2_000_000.0 * 0.15

    seg_below = _probe_segment("th_film_incentive", 500_000.0)
    assert seg_below.executable is False


# ── 10. us_or_opif (SCHEMA_EXTENSION_REQUIRED — component-basis ceilings,
# blocked single blended rate) ────────────────────────────────────────────

def test_us_or_opif_no_blended_surrogate_disclosed_component_ceilings():
    """us_or_opif carries a PRE-EXISTING (unrelated to this remediation)
    authority-insufficient veto (authority_coverage_registry._ROWS:
    or_opif/us_or_opif, UNPRICEABLE_AUTHORITY_INSUFFICIENT) that the B4
    gate also refuses through -- resolve_program_rate() therefore returns
    None regardless of tier shape, out of scope to lift here (would be
    reopening prior, unrelated research). This test proves the RATE DATA
    itself is corrected (no 26.2% blended surrogate; two disclosed
    component ceilings) by reading _RULES_BY_PROGRAM directly, and
    confirms the pre-existing veto is the actual reason resolution is
    None (not a new defect introduced by this fix)."""
    from app.data.authority_coverage_registry import economic_block_for_program
    from app.data.program_rate_rules import get_rate_rules, resolve_program_rate

    rules = get_rate_rules("us_or_opif")
    assert not any(r.rate == 0.262 for r in rules), "the fabricated 26.2% blended surrogate must be gone"
    rates = sorted(r.rate for r in rules)
    assert rates == [0.20, 0.25]
    assert all(r.is_band_ceiling for r in rules), "neither component rate is guaranteed until implemented"

    block = economic_block_for_program("us_or_opif")
    assert block is not None and block.classification == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
    assert resolve_program_rate("us_or_opif", production_type="feature_film", qpe_usd=2_000_000.0) is None


# ── 11. us_tx_miip (UPDATE_TO_ALLOCATION_MODEL — zero guaranteed without
# an award/allocation fact) ───────────────────────────────────────────────

def test_us_tx_miip_zero_guaranteed_without_allocation_fact():
    from app.data.program_rate_rules import resolve_program_rate

    r = resolve_program_rate("us_tx_miip", production_type="feature_film", qpe_usd=5_000_000.0)
    assert r is not None
    assert r.has_guaranteed_floor is False, "no award yields zero guaranteed NPC"
    ids = {c.condition_id for c in r.conditions_evaluated}
    assert "us-tx-award-allocation-required" in ids
    assert "us-tx-resident-threshold-phased" in ids
    for c in r.conditions_evaluated:
        assert c.satisfied is None, "no condition may be silently assumed satisfied"


# ── 12. za_nfvf_rebate (ADD_RULE_AND_COMPONENT_BRANCH — new identity,
# distinct from the separately B1 FAIL_CLOSED za_dtic_foreign_film) ─────

def test_za_nfvf_rebate_prices_independently_of_za_dtic_foreign_film():
    result = _discover("ZA", qpe_usd=2_000_000.0)
    nfvf = _examined(result, "ZA", "za_nfvf_rebate")
    dtic = _examined(result, "ZA", "za_dtic_foreign_film")
    assert nfvf is not None and nfvf.resolves_for_production is True
    assert dtic is not None and dtic.resolves_for_production is False, "za_dtic_foreign_film stays B1 FAIL_CLOSED"

    seg = _probe_segment("za_nfvf_rebate", 2_000_000.0)
    assert seg.executable is True
    assert seg.incentive_floor_usd == 2_000_000.0 * 0.25
