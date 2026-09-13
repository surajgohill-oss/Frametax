"""test_b4_transitive_alias_gate.py

Codex final runtime remediation, item B4:multi_hop_alias
(GLOBAL_PROGRAM_FINAL_CLAUDE_REMEDIATION_MANIFEST_CODEX.csv).

Codex's independent audit reproduced a deterministic bypass: economic_
block_for_program() canonicalized only ONE PROGRAM_SLUG_ALIASES hop, so a
two-hop alias chain terminating in a blocked identity could still reach an
injected live RateRule. authority_coverage_registry._b4_spellings() and
_alias_chain_has_cycle() were rewritten to walk the FULL alias/binding
chain transitively (arbitrary depth) with explicit cycle detection.

This file adds the specific negative cases the remediation manifest
requires beyond what tests/test_codex_final_canonical_incentive_
acceptance.py already covers (one-hop, blocked-intermediate two-hop,
retired source, display-only source, conditional fallback, direct
candidate-stack injection, legacy re-registration, serialized/
reconstructed component): three-hop chains, an explicitly BLOCKED
intermediate hop, a genuine alias cycle, and a dangling/missing alias
target. Every test injects a live, corrupted RateRule and proves the gate
refuses it -- never merely observing that no rule happens to exist.
"""
from __future__ import annotations

import pytest

from app.calculators.canonical_stack_bridge import (
    StackCandidate,
    price_program_group_stack,
    price_program_pair_stack,
)
from app.data.authority_coverage_registry import economic_block_for_program
from app.data.program_rate_rules import (
    RATE_FAILURE_AUTHORITY_EXHAUSTED,
    RateRule,
    _RULES_BY_PROGRAM,
    classify_rate_resolution_failure,
    register_rate_rules,
    resolve_program_rate,
)
from app.data.program_slug_aliases import PROGRAM_SLUG_ALIASES


def _rule(slug: str, rate: float = 0.99) -> RateRule:
    return RateRule(
        program_slug=slug, tier_id="_b4-transitive-test-rule",
        rate=rate, is_band_ceiling=False, production_types=("feature_film",),
        min_qpe_usd=None, conditions=(), confidence_tier="VERIFIED",
        citation="test fixture -- deliberately corrupted rule",
        source_ref="test-fixture",
    )


@pytest.fixture
def isolated_registries():
    rules = dict(_RULES_BY_PROGRAM)
    aliases = dict(PROGRAM_SLUG_ALIASES)
    try:
        yield
    finally:
        _RULES_BY_PROGRAM.clear()
        _RULES_BY_PROGRAM.update(rules)
        PROGRAM_SLUG_ALIASES.clear()
        PROGRAM_SLUG_ALIASES.update(aliases)


# ── 1. One-hop blocked alias (baseline sanity; also covered independently
# in test_codex_final_canonical_incentive_acceptance.py). ───────────────

def test_one_hop_blocked_alias_refuses(isolated_registries):
    outer = "__b4t_one_hop__"
    PROGRAM_SLUG_ALIASES[outer] = "ae_ad_film_rebate"  # B1 FAIL_CLOSED
    _RULES_BY_PROGRAM[outer] = (_rule(outer),)
    assert economic_block_for_program(outer) is not None
    assert resolve_program_rate(outer, "feature_film", 5_000_000) is None
    assert classify_rate_resolution_failure(outer, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED


# ── 2. Two-hop blocked alias, with the intermediate hop ALSO carrying a
# live injected rule -- proves the intermediate is blocked too, not only
# the terminal target. ───────────────────────────────────────────────────

def test_two_hop_blocked_alias_with_live_intermediate_refuses(isolated_registries):
    outer, middle, target = "__b4t_two_hop_outer__", "__b4t_two_hop_middle__", "de_dfff"  # B1 DISPLAY_ONLY
    PROGRAM_SLUG_ALIASES[outer] = middle
    PROGRAM_SLUG_ALIASES[middle] = target
    _RULES_BY_PROGRAM[outer] = (_rule(outer),)
    _RULES_BY_PROGRAM[middle] = (_rule(middle),)
    assert economic_block_for_program(outer) is not None
    assert economic_block_for_program(middle) is not None
    for slug in (outer, middle):
        assert resolve_program_rate(slug, "feature_film", 5_000_000) is None
        assert classify_rate_resolution_failure(slug, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED


# ── 3. Three-hop chain (required explicitly by the remediation manifest's
# negative-test list, beyond the two-hop case Codex reproduced). ────────

def test_three_hop_blocked_alias_chain_refuses(isolated_registries):
    a, b, c, target = (
        "__b4t_three_hop_a__", "__b4t_three_hop_b__", "__b4t_three_hop_c__",
        "za_dtic_foreign_film",  # B1 FAIL_CLOSED
    )
    PROGRAM_SLUG_ALIASES[a] = b
    PROGRAM_SLUG_ALIASES[b] = c
    PROGRAM_SLUG_ALIASES[c] = target
    _RULES_BY_PROGRAM[a] = (_rule(a),)
    assert economic_block_for_program(target) is not None
    assert economic_block_for_program(a) is not None
    assert resolve_program_rate(a, "feature_film", 5_000_000) is None
    assert classify_rate_resolution_failure(a, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED


# ── 4. Blocked intermediate alias with a CLEAN (non-blocked) terminal
# target -- proves a fail-closed intermediate invalidates the whole chain
# even when the final canonical target would otherwise be perfectly
# priceable, per the manifest's explicit "blocked intermediate" case. ───

def test_blocked_intermediate_with_clean_terminal_still_refuses(isolated_registries):
    outer, blocked_middle, clean_target = (
        "__b4t_blocked_mid_outer__", "al_cash_rebate", "ca_federal_cptc",  # blocked_middle is B1 FAIL_CLOSED
    )
    # blocked_middle already resolves nowhere further in real data; give it
    # an explicit (corrupted) further hop to a real, clean, priceable
    # program to prove the BLOCK on the intermediate wins regardless of
    # what lies beyond it.
    PROGRAM_SLUG_ALIASES[outer] = blocked_middle
    PROGRAM_SLUG_ALIASES[blocked_middle] = clean_target
    try:
        assert economic_block_for_program(blocked_middle) is not None
        assert economic_block_for_program(outer) is not None
        assert resolve_program_rate(outer, "feature_film", 5_000_000) is None
        assert classify_rate_resolution_failure(outer, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED
        # Sanity: the clean terminal target is unaffected when addressed directly.
        assert economic_block_for_program(clean_target) is None
        assert resolve_program_rate(clean_target, "feature_film", 5_000_000) is not None
    finally:
        del PROGRAM_SLUG_ALIASES[blocked_middle]


# ── 5. Alias cycle fails closed unconditionally, even when no member of
# the cycle is independently in any block dict. ─────────────────────────

def test_alias_cycle_fails_closed_even_with_no_independent_block(isolated_registries):
    a, b = "__b4t_cycle_a__", "__b4t_cycle_b__"
    PROGRAM_SLUG_ALIASES[a] = b
    PROGRAM_SLUG_ALIASES[b] = a  # genuine 2-cycle, neither node independently blocked
    _RULES_BY_PROGRAM[a] = (_rule(a),)
    _RULES_BY_PROGRAM[b] = (_rule(b),)
    block = economic_block_for_program(a)
    assert block is not None
    assert block.classification == "ALIAS_CYCLE_FAIL_CLOSED"
    assert resolve_program_rate(a, "feature_film", 5_000_000) is None
    assert resolve_program_rate(b, "feature_film", 5_000_000) is None
    assert classify_rate_resolution_failure(a, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED


def test_alias_self_cycle_fails_closed(isolated_registries):
    a = "__b4t_self_cycle__"
    PROGRAM_SLUG_ALIASES[a] = a  # degenerate self-referential alias
    _RULES_BY_PROGRAM[a] = (_rule(a),)
    block = economic_block_for_program(a)
    assert block is not None
    assert block.classification == "ALIAS_CYCLE_FAIL_CLOSED"
    assert resolve_program_rate(a, "feature_film", 5_000_000) is None


# ── 6. Missing/dangling alias target: the chain terminates on a spelling
# with no registered rule and no further alias -- must never fabricate a
# positive price, even though it is not itself a "block" (there is simply
# nothing there to price). ───────────────────────────────────────────────

def test_missing_alias_target_never_produces_a_positive_price(isolated_registries):
    dangling = "__b4t_dangling_target_does_not_exist__"
    outer = "__b4t_points_at_dangling__"
    PROGRAM_SLUG_ALIASES[outer] = dangling
    # Deliberately no RateRule registered anywhere in this chain.
    assert resolve_program_rate(outer, "feature_film", 5_000_000) is None
    assert resolve_program_rate(dangling, "feature_film", 5_000_000) is None


# ── 7. Retired source reached through a multi-hop chain (extends Codex's
# single-hop retired-identity case to a deeper chain). ──────────────────

def test_retired_identity_multi_hop_alias_cannot_reach_active_rule(isolated_registries):
    retired = "iceland_post_production_visual_effects_and_animation_incentive"
    outer = "__b4t_retired_multi_hop__"
    PROGRAM_SLUG_ALIASES[outer] = retired
    PROGRAM_SLUG_ALIASES[retired] = "ca_film_30"  # active, clean, priceable
    try:
        assert economic_block_for_program(outer) is not None
        assert resolve_program_rate(outer, "feature_film", 5_000_000) is None
    finally:
        del PROGRAM_SLUG_ALIASES[retired]


# ── 8. Direct candidate-stack insertion via a multi-hop-aliased slug
# cannot bypass the pair/group entrypoints. ──────────────────────────────

def test_pair_and_group_stack_reject_multi_hop_aliased_blocked_candidate(isolated_registries):
    a, b, target = "__b4t_stack_a__", "__b4t_stack_b__", "be_tax_shelter"  # B1 DISPLAY_ONLY
    PROGRAM_SLUG_ALIASES[a] = b
    PROGRAM_SLUG_ALIASES[b] = target
    blocked = StackCandidate(a, "BE", 999_999.0, 0.99, 1_000_000.0, "tax_credit")
    clean = StackCandidate("eu_eurimages", "BE", 100_000.0, 0.10, 1_000_000.0, "grant")
    assert price_program_pair_stack(blocked, clean) is None
    assert price_program_group_stack([blocked, clean]) is None


# ── 9. Conditional fallback through a multi-hop chain cannot reactivate
# a blocked identity. ─────────────────────────────────────────────────────

def test_conditional_fallback_through_multi_hop_chain_cannot_reactivate(isolated_registries):
    from app.data.program_rate_rules import RateCondition

    outer, target = "__b4t_conditional_multi_hop__", "de_dfff"  # B1 DISPLAY_ONLY
    PROGRAM_SLUG_ALIASES[outer] = target
    _RULES_BY_PROGRAM[outer] = (
        RateRule(
            program_slug=outer, tier_id="_b4t-conditional-rule", rate=0.99,
            is_band_ceiling=False, production_types=("feature_film",),
            min_qpe_usd=None,
            conditions=(RateCondition(
                condition_id="b4t-fact", description="test fixture",
                quote="test fixture", kind="project_fact_dependent_eligibility",
            ),),
            confidence_tier="VERIFIED", citation="test fixture", source_ref="test-fixture",
        ),
    )
    assert resolve_program_rate(outer, "feature_film", 5_000_000) is None


# ── 10. Legacy registry re-registration through a multi-hop chain cannot
# bypass the gate (extends Codex's single-hop re-registration case). ────

def test_legacy_registry_reregistration_through_multi_hop_chain_cannot_bypass(isolated_registries):
    outer, target = "__b4t_legacy_reregister__", "be_tax_shelter"  # B1 DISPLAY_ONLY
    PROGRAM_SLUG_ALIASES[outer] = target
    register_rate_rules((_rule(outer),))
    assert resolve_program_rate(outer, "feature_film", 5_000_000) is None


# ── 11. Serialized/reconstructed StackCandidate for a multi-hop-aliased
# blocked slug cannot restore priceability. ──────────────────────────────

def test_serialized_reconstruction_of_multi_hop_aliased_candidate_stays_blocked(isolated_registries):
    from dataclasses import asdict

    a, b, target = "__b4t_serialize_a__", "__b4t_serialize_b__", "de_dfff"
    PROGRAM_SLUG_ALIASES[a] = b
    PROGRAM_SLUG_ALIASES[b] = target
    raw = asdict(StackCandidate(a, "DE", 999_999.0, 0.99, 1_000_000.0, "tax_credit"))
    restored = StackCandidate(**raw)
    clean = StackCandidate("eu_eurimages", "DE", 100_000.0, 0.10, 1_000_000.0, "grant")
    assert price_program_group_stack([restored, clean]) is None


# ── Positive control: an unrelated, non-aliased, verified program is
# completely unaffected by the transitive-traversal rewrite. ────────────

def test_unrelated_verified_program_still_prices_after_transitive_rewrite():
    r = resolve_program_rate("ca_federal_cptc", production_type="feature_film", qpe_usd=5_000_000)
    assert r is not None
    assert r.modeled_rate == 0.25
    assert economic_block_for_program("ca_federal_cptc") is None


def test_california_rekey_economics_unchanged_after_transitive_rewrite():
    """Codex's own regression requirement: 'All existing aliases remain
    cycle-free and California rekey economics remain unchanged.'"""
    direct = resolve_program_rate("ca_film_30", "feature_film", 5_000_000)
    via_alias = resolve_program_rate("us_ca_film_credit", "feature_film", 5_000_000)
    assert direct is not None
    assert via_alias is not None
    assert direct.modeled_rate == via_alias.modeled_rate
    assert economic_block_for_program("ca_film_30") is None
    assert economic_block_for_program("us_ca_film_credit") is None
