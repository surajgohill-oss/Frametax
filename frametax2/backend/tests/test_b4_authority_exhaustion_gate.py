"""
test_b4_authority_exhaustion_gate.py

Codex bounded remediation, B4 central authority-exhaustion gate
(GLOBAL_PROGRAM_FAIL_CLOSED_GATE_SPEC_CODEX.md).

Proves the explicit, active refusal gate implemented in
authority_coverage_registry.economic_block_for_program() and wired into
program_rate_rules.resolve_program_rate() / classify_rate_resolution_
failure() and canonical_stack_bridge.price_program_group_stack(): an
authority-exhausted, discretionary-display-only, retired, or duplicate
identity cannot resolve to an automatic priced rate, cannot inherit a
stale rule through an alias, cannot enter an automatic stack, and cannot
contribute positive guaranteed incentive value -- regardless of what a
stale RateRule, DoctrineRecord, project reference, or stacking edge says.

These are adversarial STATE-CORRUPTION tests (per the gate spec's own
instruction: "Absence of a slug is not acceptance evidence") -- each one
deliberately injects a live RateRule for a fail-closed identity and proves
the gate refuses it anyway, never merely observing that no rule happens to
exist.
"""
from __future__ import annotations

import pytest

from app.data.authority_coverage_registry import _B1_DISCRETIONARY_RULING, economic_block_for_program
from app.data.program_rate_rules import (
    RATE_FAILURE_AUTHORITY_EXHAUSTED,
    RateCondition,
    RateRule,
    _RULES_BY_PROGRAM,
    classify_rate_resolution_failure,
    resolve_program_rate,
)


def _inject_stale_rule(slug: str, rate: float = 0.99) -> None:
    """Registers an obviously-wrong, clearly-fake RateRule directly into
    _RULES_BY_PROGRAM for `slug` -- simulating a stale/corrupted rule that
    somehow survived under a fail-closed identity. The gate must refuse
    this regardless of what the rule itself says."""
    _RULES_BY_PROGRAM[slug] = (
        RateRule(
            program_slug=slug, tier_id="_test-stale-injected-rule",
            rate=rate, is_band_ceiling=False, production_types=("feature_film",),
            min_qpe_usd=None, conditions=(), confidence_tier="VERIFIED",
            citation="test fixture -- deliberately corrupted stale rule",
            source_ref="test-fixture",
        ),
    )


@pytest.fixture
def restore_rules_by_program():
    """Snapshots and restores _RULES_BY_PROGRAM so an injected stale rule
    never leaks into another test."""
    snapshot = dict(_RULES_BY_PROGRAM)
    try:
        yield
    finally:
        _RULES_BY_PROGRAM.clear()
        _RULES_BY_PROGRAM.update(snapshot)


# ── Negative control 1: stale RateRule injected directly under a fail-
# closed canonical ID -- resolution returns None, classification returns
# AUTHORITY_EXHAUSTED_FAIL_CLOSED. ──────────────────────────────────────

def test_negative_1_stale_rate_rule_injected_under_fail_closed_id_refused(restore_rules_by_program):
    slug = "cr_tax_return_incentive"  # B1 FAIL_CLOSED
    assert economic_block_for_program(slug) is not None
    _inject_stale_rule(slug)
    assert resolve_program_rate(slug, production_type="feature_film", qpe_usd=5_000_000) is None
    assert classify_rate_resolution_failure(slug, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED


# ── Negative control 2: same corruption reached through a legacy alias
# whose canonical target is blocked. ────────────────────────────────────

def test_negative_2_stale_rule_reached_via_legacy_alias_still_refused(restore_rules_by_program):
    # sa_film_commission_rebate (B1 FAIL_CLOSED) has a known legacy alias spelling.
    canonical = "sa_film_commission_rebate"
    alias = "sa_sfc_rebate"  # CANONICAL_RUNTIME_SLUG_BINDINGS: sa_sfc_rebate -> sa_film_commission_rebate
    assert economic_block_for_program(canonical) is not None
    assert economic_block_for_program(alias) is not None
    _inject_stale_rule(canonical)
    _inject_stale_rule(alias)
    for slug in (canonical, alias):
        assert resolve_program_rate(slug, production_type="feature_film", qpe_usd=5_000_000) is None
        assert classify_rate_resolution_failure(slug, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED


# ── Negative control 3: pair and group stacks containing a blocked
# identity reject with the same explicit reason. ────────────────────────

def test_negative_3_pair_and_group_stacks_with_blocked_member_reject():
    """Uses no_film_incentive (B1 DISPLAY_ONLY_ZERO_GUARANTEED) paired with
    no_mro_film3 -- a REAL, _SLUG_PAIR_RULES-covered combination
    (frozenset({"no_film_incentive", "no_mro_film3"})) that would otherwise be
    a legitimate, named, stackable pair. Same jurisdiction_code ("NO") for
    both candidates makes the group trivially eligible_for_combination, so
    a None result here is attributable ONLY to the B4 gate, not to
    jurisdiction incompatibility."""
    from app.calculators.canonical_stack_bridge import (
        StackCandidate, price_program_group_stack, price_program_pair_stack,
    )

    blocked = StackCandidate(
        program_slug="no_film_incentive", jurisdiction_code="NO",
        selected_incentive_usd=0.0, effective_rate=0.0,
        qualifying_spend_usd=1_000_000.0, incentive_type="tax_credit",
    )
    clean = StackCandidate(
        program_slug="no_mro_film3", jurisdiction_code="NO",
        selected_incentive_usd=100_000.0, effective_rate=0.10,
        qualifying_spend_usd=1_000_000.0, incentive_type="grant",
    )
    assert economic_block_for_program("no_film_incentive") is not None
    assert economic_block_for_program("no_mro_film3") is None
    assert price_program_pair_stack(blocked, clean) is None
    assert price_program_group_stack([blocked, clean]) is None
    # (The three-way positive control was removed with 1.10.0: it relied on be_tax_shelter's pair rules; the
    # remaining B1 programs have only this one named pair, so the two-member refusal above is the full control.)


# ── Negative control 4: a display-only discretionary candidate remains
# visible but contributes zero guaranteed value. ────────────────────────

async def test_negative_4_display_only_candidate_visible_zero_guaranteed():
    """Synthetic, rolled-back records only. This control used to evaluate the real F#K Valentine's Day production and expected
    de_dfff to be display-only, but de_dfff left the discretionary ruling in 1.10.0 (supported guaranteed floor). The behavior is
    pinned on a program that is STILL display-only in the ruling and is discovered for the synthetic budget."""
    from tests.isolated_records import create_synthetic_project, isolated_session, served_structures
    from app.services.canonical_evaluation import evaluate_project

    slug = "sg_made_with_singapore_rebate"
    assert _B1_DISCRETIONARY_RULING[slug] == "DISPLAY_ONLY_ZERO_GUARANTEED"
    async with isolated_session() as session:
        pid = await create_synthetic_project(session, home_code="MU")
        await evaluate_project(session, pid)
        entries = await served_structures(session, pid)
    shown = [e for e in entries if slug in (e.get("program_slugs") or [e.get("program_slug")])]
    assert shown, "the display-only candidate must remain visible/discovered"
    assert all(e["is_fully_priced"] is False for e in shown)
    assert not any(e.get("selected_incentive_usd") for e in shown), "a display-only program contributes zero guaranteed value"
    assert not any(e.get("confirmed_incentive_floor_usd") for e in shown)

# ── Negative control 5: an unrelated verified rule still prices. ────────

def test_negative_5_unrelated_verified_rule_still_prices():
    # The CPTC rate applies to qualified Canadian LABOUR (Task 4 labour-only base), so it prices only when that basis is evidenced.
    r = resolve_program_rate("ca_federal_cptc", production_type="feature_film", qpe_usd=5_000_000,
                             amount_facts={"ca_federal_cptc_qualified_labour_usd": 2_000_000.0})
    assert r is not None
    assert r.modeled_rate == 0.25
    assert r.has_guaranteed_floor is True and r.qpe_basis_used == 2_000_000.0
    assert economic_block_for_program("ca_federal_cptc") is None
    # No labour basis evidenced: fail closed (no rate), never the whole QPE.
    assert resolve_program_rate("ca_federal_cptc", production_type="feature_film", qpe_usd=5_000_000) is None


# ── Negative control 6: no loader or registry-import order can reactivate
# the corrupted rule. ────────────────────────────────────────────────────

def test_negative_6_reregistering_a_blocked_slugs_rate_rule_cannot_reactivate_it(restore_rules_by_program):
    """Simulates a loader/registry-import-order corruption WITHOUT
    importlib.reload() -- reloading program_rate_rules/authority_coverage_
    registry in-process would re-execute their module bodies and reset
    _RULES_BY_PROGRAM to empty without re-running every OTHER module's
    module-level register_rate_rules() calls (they are only ever executed
    once, at first import, and stay cached in sys.modules), corrupting
    global state for the rest of the test session. Registering a fresh,
    real-shaped RateRule for an already-blocked slug (the actual mechanism
    a stray re-registration/loader could exercise) is the safe, faithful
    simulation: the gate must still refuse it."""
    from app.data.program_rate_rules import register_rate_rules

    slug = "sa_film_commission_rebate"
    assert economic_block_for_program(slug) is not None
    register_rate_rules((
        RateRule(
            program_slug=slug, tier_id="_test-reregistered-rule",
            rate=0.99, is_band_ceiling=False, production_types=("feature_film",),
            min_qpe_usd=None, conditions=(), confidence_tier="VERIFIED",
            citation="test fixture -- simulated loader re-registration",
            source_ref="test-fixture",
        ),
    ))
    assert economic_block_for_program(slug) is not None
    assert economic_block_for_program(slug).classification == "DISPLAY_ONLY_ZERO_GUARANTEED"
    assert resolve_program_rate(slug, production_type="feature_film", qpe_usd=5_000_000) is None
    assert classify_rate_resolution_failure(slug, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED


# ── Positive controls: the gate returns a structured, non-empty result
# for every one of the 46 B1 canonical ids, and for the pre-existing
# authority-exhausted/retired/duplicate states it also covers. ─────────

#: The 45-entry ruling was reconciled down to 10: 20 earlier STATUTORY_FORMULAIC removals plus the 15 floor-supported programs of
#: AUTHORITY_COVERAGE_REGISTRY_VERSION 1.10.0 (see the comment above _B1_DISCRETIONARY_RULING). The 35 removed ids are pinned here.
_B1_REMOVED_BY_RECONCILIATION = (
    "ae_ad_film_rebate", "al_cash_rebate", "au_nsw_pdv_rebate", "au_pdv_offset", "au_qld_pdv_rebate", "au_sa_pdv_rebate",
    "be_tax_shelter", "ch_pics_national_rebate", "de_dfff", "dk_production_rebate", "eg_empc_cashback", "fj_film_rebate",
    "ge_film_rebate", "gh_film_tax_incentive", "il_foreign_production_fund", "in_national_film", "me_cash_rebate",
    "mk_cash_rebate", "mn_production_incentive", "mx_federal_film_incentive_2026", "pa_film_rebate", "ph_fdcp_flip",
    "pt_scri_pt_cash_rebate", "pt_scri_pt_medium_budget", "qa_screen_production_incentive", "si_cash_rebate",
    "tt_production_expenditure_rebate", "ua_cash_rebate", "us_il_film_production_services_credit", "us_tn_performance_grant",
    "us_wa_mpcp", "uy_acau_cash_rebate", "uy_tax_credit_2026", "uz_film_rebate", "za_dtic_foreign_film",
)


def test_all_remaining_b1_canonical_ids_are_blocked():
    assert len(_B1_DISCRETIONARY_RULING) == 10
    assert not set(_B1_DISCRETIONARY_RULING) & set(_B1_REMOVED_BY_RECONCILIATION)
    for slug, expected_classification in _B1_DISCRETIONARY_RULING.items():
        block = economic_block_for_program(slug)
        assert block is not None, f"{slug} must be B4-blocked"
        assert block.classification == expected_classification


def test_every_id_removed_from_the_ruling_is_unblocked_and_never_guarantees_without_a_floor():
    assert len(_B1_REMOVED_BY_RECONCILIATION) == 35
    for slug in _B1_REMOVED_BY_RECONCILIATION:
        assert economic_block_for_program(slug) is None, f"{slug} left the ruling and must not be B4-blocked"
        rr = resolve_program_rate(slug, production_type="feature_film", qpe_usd=5_000_000.0)
        if rr is None:
            assert classify_rate_resolution_failure(slug, "feature_film", 5_000_000.0) != RATE_FAILURE_AUTHORITY_EXHAUSTED, slug
        elif not rr.has_guaranteed_floor:
            assert rr.is_band_ceiling is True, slug     # a lone ceiling is consumed fail-closed by allocation_pricing

def test_four_canadian_pstc_programs_no_longer_b1_blocked():
    # CLAUDE_FINAL_PROGRAM_TAXONOMY_UNPRICED_LEDGER_AND_SUPPORT_CLOSEOUT:
    # ca_bc_pstc, ca_federal_pstc, ca_qc_pstc, ca_nl_all_spend_credit each
    # carry a directly-sourced official rate, an explicit guaranteed
    # non-band-ceiling floor tier, and no stated selection/competitive
    # process -- real, standard, non-discretionary Canadian tax credits.
    expected_floor = {
        "ca_bc_pstc": 0.36,
        "ca_federal_pstc": 0.16,
        "ca_qc_pstc": 0.25,
        "ca_nl_all_spend_credit": 0.40,
    }
    # CPTC-style labour basis: BC, federal and Quebec PSTC rates apply to qualified labour, so their rate resolves only when
    # that basis is evidenced (Task 4); NL and Quebec carry no such gate.
    labour_fact = {"ca_bc_pstc": "ca_bc_pstc_qualified_labour_usd", "ca_federal_pstc": "ca_federal_pstc_qualified_labour_usd"}
    for slug, floor in expected_floor.items():
        assert economic_block_for_program(slug) is None, f"{slug} must NOT be B4-blocked"
        facts = {labour_fact[slug]: 1_000_000.0} if slug in labour_fact else None
        rr = resolve_program_rate(slug, production_type="feature_film", qpe_usd=2_000_000.0, amount_facts=facts)
        assert rr is not None, f"{slug} must resolve a real rate"
        assert rr.floor_rate == pytest.approx(floor)
        assert rr.has_guaranteed_floor is True
    # Without the labour basis the federal credit fails closed, and BC offers only its ceiling with NO guaranteed floor.
    assert resolve_program_rate("ca_federal_pstc", production_type="feature_film", qpe_usd=2_000_000.0) is None


def test_ca_bc_pstc_regional_uplift_remains_a_disclosed_ceiling_not_guaranteed():
    # The 48% regional/distant-location uplift tier is a real, correctly-modeled is_band_ceiling=True discretionary_band
    # condition -- only the 36% labour-basis floor is guaranteed. Removing the B1 veto must not promote the uplift.
    rr = resolve_program_rate("ca_bc_pstc", production_type="feature_film", qpe_usd=2_000_000.0,
                              amount_facts={"ca_bc_pstc_qualified_labour_usd": 1_000_000.0})
    assert rr is not None
    assert rr.modeled_rate == pytest.approx(0.48)
    assert rr.is_band_ceiling is True
    assert rr.floor_rate == pytest.approx(0.36)
    assert rr.has_guaranteed_floor is True
    assert "guaranteed floor tier is 36%" in rr.basis
    # Labour basis not evidenced: the base tier is ineligible, only the ceiling remains, and nothing may read as guaranteed.
    bare = resolve_program_rate("ca_bc_pstc", production_type="feature_film", qpe_usd=2_000_000.0)
    assert bare is not None and bare.is_band_ceiling is True and bare.has_guaranteed_floor is False
    assert "guaranteed floor tier is 48%" not in bare.basis, "a ceiling must never be described as the guaranteed floor"
    assert "NO guaranteed floor tier is eligible" in bare.basis


def test_retired_identity_is_blocked():
    slug = "iceland_post_production_visual_effects_and_animation_incentive"
    block = economic_block_for_program(slug)
    assert block is not None, f"{slug} must be B4-blocked"
    assert resolve_program_rate(slug, production_type="feature_film", qpe_usd=5_000_000) is None


def test_ny_post_production_credit_no_longer_blanket_blocked():
    # CLAUDE_GLOBAL_ASSUMPTION_POLICY_AND_PRICEABLE_PROGRAM_FINALIZATION:
    # the blanket KEEP_SEPARATE_POST_PROGRAM_FAIL_CLOSED veto was removed
    # (real, sufficient canonical rate/threshold/mutual-exclusivity
    # evidence exists in US_NY_POST_DOCTRINE). The gate must no longer
    # block this identity, and a real rate must resolve above its own
    # documented $1,000,000 minimum spend.
    slug = "us_ny_post_production_credit"
    assert economic_block_for_program(slug) is None, f"{slug} must NOT be B4-blocked"
    rr = resolve_program_rate(slug, production_type="feature_film", qpe_usd=1_200_000.0)
    assert rr is not None
    assert rr.modeled_rate == pytest.approx(0.35)


def test_ny_post_and_ny_principal_are_named_mutually_exclusive_not_blanket_blocked():
    # The real, substantive same-cost non-double-dipping rule survives the
    # veto's removal: a single structure can never claim both ny_state_film
    # and us_ny_post_production_credit for the same cost base.
    from app.optimization.stacking_rules import _SLUG_PAIR_RULES

    rule = _SLUG_PAIR_RULES.get(frozenset({"ny_state_film", "us_ny_post_production_credit"}))
    assert rule is not None
    assert rule["rule_type"] == "mutually_exclusive"
