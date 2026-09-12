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

from app.data.authority_coverage_registry import economic_block_for_program
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
    slug = "ae_ad_film_rebate"  # B1 FAIL_CLOSED
    assert economic_block_for_program(slug) is not None
    _inject_stale_rule(slug)
    assert resolve_program_rate(slug, production_type="feature_film", qpe_usd=5_000_000) is None
    assert classify_rate_resolution_failure(slug, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED


# ── Negative control 2: same corruption reached through a legacy alias
# whose canonical target is blocked. ────────────────────────────────────

def test_negative_2_stale_rule_reached_via_legacy_alias_still_refused(restore_rules_by_program):
    # al_cash_rebate (B1 FAIL_CLOSED) has a known legacy alias spelling.
    canonical = "al_cash_rebate"
    alias = "al_film_incentive"  # CANONICAL_RUNTIME_SLUG_BINDINGS: al_film_incentive -> al_cash_rebate
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
    """Uses be_tax_shelter (B1 DISPLAY_ONLY_ZERO_GUARANTEED) paired with
    eu_eurimages -- a REAL, _SLUG_PAIR_RULES-covered combination
    (frozenset({"be_tax_shelter", "eu_eurimages"})) that would otherwise be
    a legitimate, named, stackable pair. Same jurisdiction_code ("BE") for
    both candidates makes the group trivially eligible_for_combination, so
    a None result here is attributable ONLY to the B4 gate, not to
    jurisdiction incompatibility."""
    from app.calculators.canonical_stack_bridge import (
        StackCandidate, price_program_group_stack, price_program_pair_stack,
    )

    blocked = StackCandidate(
        program_slug="be_tax_shelter", jurisdiction_code="BE",
        selected_incentive_usd=0.0, effective_rate=0.0,
        qualifying_spend_usd=1_000_000.0, incentive_type="tax_credit",
    )
    clean = StackCandidate(
        program_slug="eu_eurimages", jurisdiction_code="BE",
        selected_incentive_usd=100_000.0, effective_rate=0.10,
        qualifying_spend_usd=1_000_000.0, incentive_type="grant",
    )
    assert economic_block_for_program("be_tax_shelter") is not None
    assert economic_block_for_program("eu_eurimages") is None
    assert price_program_pair_stack(blocked, clean) is None
    assert price_program_group_stack([blocked, clean]) is None
    # A three-way group with the blocked member in a different list position.
    third = StackCandidate(
        program_slug="be_vlg_vaf", jurisdiction_code="BE",
        selected_incentive_usd=50_000.0, effective_rate=0.05,
        qualifying_spend_usd=1_000_000.0, incentive_type="grant",
    )
    assert price_program_group_stack([clean, third, blocked]) is None
    # Sanity: the SAME real pair WITHOUT the blocked member actually stacks
    # (proves the None above is caused by the block, not by some unrelated
    # gap in the pair-rule/eligibility machinery).
    assert price_program_group_stack([clean, third]) is not None


# ── Negative control 4: a display-only discretionary candidate remains
# visible but contributes zero guaranteed value. ────────────────────────

async def test_negative_4_display_only_candidate_visible_zero_guaranteed(db):
    from app.services.canonical_evaluation import evaluate_project
    from app.services.canonical_production_view import build_production_and_structures

    fvd_project_id = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
    await evaluate_project(db, fvd_project_id)
    view = await build_production_and_structures(db, fvd_project_id)
    entries = view["structures"]["allocated_structures"]["structures"]
    de = next(e for e in entries if e["primary_jurisdiction"] == "DE")  # de_dfff, B1 DISPLAY_ONLY_ZERO_GUARANTEED
    assert de is not None, "DE must remain visible/discovered"
    assert de["is_fully_priced"] is False
    assert not de.get("selected_incentive_usd")


@pytest.fixture
async def db():
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import engine
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── Negative control 5: an unrelated verified rule still prices. ────────

def test_negative_5_unrelated_verified_rule_still_prices():
    r = resolve_program_rate("ca_federal_cptc", production_type="feature_film", qpe_usd=5_000_000)
    assert r is not None
    assert r.modeled_rate == 0.25
    assert economic_block_for_program("ca_federal_cptc") is None


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

    slug = "de_dfff"
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

def test_all_46_b1_canonical_ids_are_blocked():
    from app.data.authority_coverage_registry import _B1_DISCRETIONARY_RULING

    assert len(_B1_DISCRETIONARY_RULING) == 46
    for slug, expected_classification in _B1_DISCRETIONARY_RULING.items():
        block = economic_block_for_program(slug)
        assert block is not None, f"{slug} must be B4-blocked"
        assert block.classification == expected_classification


def test_retired_and_keep_separate_identities_are_blocked():
    for slug in (
        "iceland_post_production_visual_effects_and_animation_incentive",
        "us_ny_post_production_credit",
    ):
        block = economic_block_for_program(slug)
        assert block is not None, f"{slug} must be B4-blocked"
        assert resolve_program_rate(slug, production_type="feature_film", qpe_usd=5_000_000) is None
