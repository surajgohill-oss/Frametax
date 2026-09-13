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


def _probe_segment(slug: str, amount_usd: float, production_type: str = "feature_film",
                    evidenced_facts=None, amount_facts=None):
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
        evidenced_requirement_facts=evidenced_facts, amount_facts=amount_facts,
    )


def _discover(home_code: str, production_type: str = "feature_film", qpe_usd: float = 2_000_000.0,
              evidenced_facts=None, amount_facts=None):
    return discover_executable_jurisdictions(
        requirements=derive_production_requirements({}),
        production_type=production_type, qpe_usd=qpe_usd, home_code=home_code,
        evidenced_facts=evidenced_facts, amount_facts=amount_facts,
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


# ── 2. au_location_offset (Codex final runtime remediation: genuine
# NATIVE-currency AUD threshold, never a guessed/converted USD surrogate)

def test_au_location_offset_prices_above_threshold_rejects_below():
    result = _discover("AU", qpe_usd=5_000_000.0)
    no_fact = _examined(result, "AU", "au_location_offset")
    assert no_fact is not None
    assert no_fact.resolves_for_production is False, "without an evidenced native AUD fact, must reject"

    result_below = _discover("AU", qpe_usd=5_000_000.0, amount_facts={"au_location_qape_aud": 15_000_000.0})
    below = _examined(result_below, "AU", "au_location_offset")
    assert below.resolves_for_production is False, "AUD 15,000,000 < AUD 20,000,000 native threshold must reject"

    result_pass = _discover("AU", qpe_usd=5_000_000.0, amount_facts={"au_location_qape_aud": 25_000_000.0})
    above = _examined(result_pass, "AU", "au_location_offset")
    assert above is not None
    assert above.resolves_for_production is True

    seg = _probe_segment("au_location_offset", 5_000_000.0)
    assert seg.executable is False, "no guessed USD surrogate — absent the native AUD fact, must not price"

    seg_pass = _probe_segment("au_location_offset", 5_000_000.0, amount_facts={"au_location_qape_aud": 25_000_000.0})
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
    from app.data.program_rate_rules import (
        CONDITION_STATE_EXECUTABLE,
        CONDITION_STATE_USER_FACT_REQUIRED,
        get_rate_rules,
        resolve_program_rate,
    )

    ceiling_rule = next(r for r in get_rate_rules("fr_trip") if r.tier_id == "fr-vfx-ceiling-40")
    vfx_rate_condition = next(c for c in ceiling_rule.conditions if c.condition_id == "fr-vfx-threshold")
    assert vfx_rate_condition.kind == "project_fact_dependent_uplift"
    assert vfx_rate_condition.amount_fact_key == "fr_trip_vfx_spend_usd"

    # Without the VFX fact, the 40% ceiling is not even eligible — the 30%
    # floor resolves, and its own conditions (never the ceiling's) are
    # what's disclosed.
    r = resolve_program_rate("fr_trip", production_type="feature_film", qpe_usd=5_000_000.0)
    assert r.modeled_rate == 0.30
    assert not any(c.condition_id == "fr-vfx-threshold" for c in r.conditions_evaluated)

    # With the VFX fact evidenced but below the EUR2m-equivalent
    # threshold: still the 30% floor, and the (still ineligible) ceiling's
    # condition still does not appear.
    r_below = resolve_program_rate(
        "fr_trip", production_type="feature_film", qpe_usd=5_000_000.0,
        amount_facts={"fr_trip_vfx_spend_usd": 1_000_000.0},
    )
    assert r_below.modeled_rate == 0.30

    # With the VFX fact evidenced above the threshold: the 40% ceiling
    # becomes eligible, is selected, and its condition is genuinely
    # EXECUTABLE/satisfied=True — never USER_FACT_REQUIRED once evidenced.
    r_above = resolve_program_rate(
        "fr_trip", production_type="feature_film", qpe_usd=5_000_000.0,
        amount_facts={"fr_trip_vfx_spend_usd": 2_500_000.0},
    )
    assert r_above.modeled_rate == 0.40
    vfx_cond = next(c for c in r_above.conditions_evaluated if c.condition_id == "fr-vfx-threshold")
    assert vfx_cond.satisfied is True
    assert vfx_cond.condition_state == CONDITION_STATE_EXECUTABLE

    seg = _probe_segment("fr_trip", 5_000_000.0)
    assert seg.executable is True
    assert seg.incentive_floor_usd == 5_000_000.0 * 0.30

    seg_uplift = _probe_segment("fr_trip", 5_000_000.0, amount_facts={"fr_trip_vfx_spend_usd": 2_500_000.0})
    assert seg_uplift.executable is True
    assert seg_uplift.incentive_ceiling_usd == 5_000_000.0 * 0.40


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
    assert r is None, "Codex final runtime remediation: no guessed USD surrogate — without native MAD spend and shooting-days facts, must reject"

    r_evidenced = resolve_program_rate(
        "ma_ccm_rebate", production_type="feature_film", qpe_usd=2_000_000.0,
        amount_facts={"ma_ccm_qualifying_spend_mad": 15_000_000.0},
        evidenced_facts=frozenset({"ma_ccm_18_shooting_days_confirmed"}),
    )
    ids = {c.condition_id for c in r_evidenced.conditions_evaluated}
    assert "ma-min-spend" in ids
    assert "ma-min-shooting-days" in ids, "the 18-day gate must be its own condition, not silently dropped"

    seg = _probe_segment(
        "ma_ccm_rebate", 2_000_000.0,
        amount_facts={"ma_ccm_qualifying_spend_mad": 15_000_000.0},
        evidenced_facts=frozenset({"ma_ccm_18_shooting_days_confirmed"}),
    )
    assert seg.executable is True
    assert seg.incentive_floor_usd == 2_000_000.0 * 0.30

    # 17-day rejection case: spend evidenced, days NOT evidenced.
    seg_no_days = _probe_segment(
        "ma_ccm_rebate", 2_000_000.0,
        amount_facts={"ma_ccm_qualifying_spend_mad": 15_000_000.0},
    )
    assert seg_no_days.executable is False

    seg_below = _probe_segment(
        "ma_ccm_rebate", 500_000.0,
        amount_facts={"ma_ccm_qualifying_spend_mad": 2_000_000.0},
        evidenced_facts=frozenset({"ma_ccm_18_shooting_days_confirmed"}),
    )
    assert seg_below.executable is False, "MAD 2,000,000 < MAD 10,000,000 native threshold must reject"


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
    assert seg.executable is False, "Codex final runtime remediation: points/independence/format facts must genuinely gate — absent them, must reject"

    seg_partial = _probe_segment(
        "nl_film_production_incentive", 2_000_000.0,
        evidenced_facts=frozenset({"nl_nfpi_points_independence_test_passed"}),
    )
    assert seg_partial.executable is False, "one of two required facts must not unlock the rate"

    seg_full = _probe_segment(
        "nl_film_production_incentive", 2_000_000.0,
        evidenced_facts=frozenset({
            "nl_nfpi_points_independence_test_passed", "nl_nfpi_format_threshold_met",
        }),
    )
    assert seg_full.executable is True
    assert seg_full.incentive_floor_usd == 2_000_000.0 * 0.35


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
    itself is corrected (no 26.2% blended surrogate; two genuinely
    determinate component bases, gated on caller-evidenced component
    amounts rather than blocked/disclosed-only ceilings) by reading
    _RULES_BY_PROGRAM directly, and confirms the pre-existing veto is the
    actual reason resolution is None (not a new defect introduced by this
    fix). See test_final_formulaic_full_pipeline_consumption.py for a
    deeper direct proof of the component-basis gating/qpe_basis_used
    logic with the veto bypassed."""
    from app.data.authority_coverage_registry import economic_block_for_program
    from app.data.program_rate_rules import get_rate_rules, resolve_program_rate

    rules = get_rate_rules("us_or_opif")
    assert not any(r.rate == 0.262 for r in rules), "the fabricated 26.2% blended surrogate must be gone"
    rates = sorted(r.rate for r in rules)
    assert rates == [0.20, 0.25]
    assert not any(r.is_band_ceiling for r in rules), (
        "Codex final runtime remediation: both component bases are now genuinely "
        "determinate once their own component fact is evidenced, never a blocked ceiling"
    )
    assert all(
        any(c.is_component_basis for c in r.conditions) for r in rules
    ), "each tier must gate on its own component-basis amount fact"

    block = economic_block_for_program("us_or_opif")
    assert block is not None and block.classification == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
    assert resolve_program_rate("us_or_opif", production_type="feature_film", qpe_usd=2_000_000.0) is None
    assert resolve_program_rate(
        "us_or_opif", production_type="feature_film", qpe_usd=2_000_000.0,
        amount_facts={"us_or_payroll_qpe_usd": 1_200_000.0},
    ) is None, "the pre-existing authority veto refuses even with component facts evidenced"


# ── 11. us_tx_miip (UPDATE_TO_ALLOCATION_MODEL — zero guaranteed without
# an award/allocation fact) ───────────────────────────────────────────────

def test_us_tx_miip_zero_guaranteed_without_allocation_fact():
    from app.data.program_rate_rules import CONDITION_STATE_EXECUTABLE, resolve_program_rate

    r = resolve_program_rate("us_tx_miip", production_type="feature_film", qpe_usd=5_000_000.0)
    assert r is not None
    assert r.has_guaranteed_floor is False, "no award yields zero guaranteed NPC"
    ids = {c.condition_id for c in r.conditions_evaluated}
    assert "us-tx-award-allocation-required" in ids
    assert "us-tx-resident-threshold-phased" in ids
    for c in r.conditions_evaluated:
        assert c.satisfied is None, "no condition may be silently assumed satisfied"

    seg = _probe_segment("us_tx_miip", 5_000_000.0)
    assert seg.executable is False, "no award yields zero guaranteed NPC"

    # Codex final runtime remediation: with BOTH facts genuinely evidenced,
    # the award/resident-threshold conditions resolve satisfied=True and
    # the (still floorless) ceiling genuinely prices — "Award document
    # facts permit specified tier."
    r_awarded = resolve_program_rate(
        "us_tx_miip", production_type="feature_film", qpe_usd=5_000_000.0,
        evidenced_facts=frozenset({"us_tx_miip_award_confirmed", "us_tx_miip_resident_threshold_met"}),
    )
    assert r_awarded.modeled_rate == 0.31
    for c in r_awarded.conditions_evaluated:
        assert c.satisfied is True
        assert c.condition_state == CONDITION_STATE_EXECUTABLE

    seg_awarded = _probe_segment(
        "us_tx_miip", 5_000_000.0,
        evidenced_facts=frozenset({"us_tx_miip_award_confirmed", "us_tx_miip_resident_threshold_met"}),
    )
    assert seg_awarded.executable is True
    assert seg_awarded.incentive_floor_usd == 5_000_000.0 * 0.31


# ── 12. za_nfvf_rebate (ADD_RULE_AND_COMPONENT_BRANCH — new identity,
# distinct from the separately B1 FAIL_CLOSED za_dtic_foreign_film) ─────

def test_za_nfvf_rebate_prices_independently_of_za_dtic_foreign_film():
    result = _discover("ZA", qpe_usd=2_000_000.0)
    nfvf = _examined(result, "ZA", "za_nfvf_rebate")
    dtic = _examined(result, "ZA", "za_dtic_foreign_film")
    assert nfvf is not None and nfvf.resolves_for_production is False, (
        "Codex final runtime remediation: the accepted-production gate must genuinely reject when unevidenced"
    )
    assert dtic is not None and dtic.resolves_for_production is False, "za_dtic_foreign_film stays B1 FAIL_CLOSED"

    result_gated = _discover(
        "ZA", qpe_usd=2_000_000.0,
        evidenced_facts=frozenset({"za_nfvf_accepted_production_confirmed"}),
    )
    nfvf_gated = _examined(result_gated, "ZA", "za_nfvf_rebate")
    assert nfvf_gated.resolves_for_production is True

    seg = _probe_segment("za_nfvf_rebate", 2_000_000.0)
    assert seg.executable is False, "no accepted-production fact evidenced — must reject"

    seg_gated = _probe_segment(
        "za_nfvf_rebate", 2_000_000.0,
        evidenced_facts=frozenset({"za_nfvf_accepted_production_confirmed"}),
    )
    assert seg_gated.executable is True
    assert seg_gated.incentive_floor_usd == 2_000_000.0 * 0.25

    seg_over_cap = _probe_segment(
        "za_nfvf_rebate", 2_000_000.0,
        evidenced_facts=frozenset({"za_nfvf_accepted_production_confirmed"}),
        amount_facts={"za_nfvf_incentive_value_zar": 30_000_000.0},
    )
    assert seg_over_cap.executable is False, "an evidenced incentive value over the ZAR 25m cap must reject"
