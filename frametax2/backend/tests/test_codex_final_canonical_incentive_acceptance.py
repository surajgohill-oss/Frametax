"""Independent Codex adversarial checks for the final incentive-runtime audit.

These tests do not alter production behavior.  Nine assert the current B4
refusal boundary.  The strict xfail records the independently reproduced
multi-hop-alias bypass that blocks final acceptance.
"""
from __future__ import annotations

from dataclasses import asdict

import pytest

from app.calculators.canonical_stack_bridge import (
    StackCandidate,
    price_program_group_stack,
)
from app.data.authority_coverage_registry import economic_block_for_program
from app.data.program_rate_rules import (
    RATE_FAILURE_AUTHORITY_EXHAUSTED,
    RateCondition,
    RateRule,
    _RULES_BY_PROGRAM,
    classify_rate_resolution_failure,
    resolve_program_rate,
)
from app.data.program_slug_aliases import PROGRAM_SLUG_ALIASES


def _rule(slug: str, *, conditional: bool = False) -> RateRule:
    conditions = (
        RateCondition(
            condition_id="audit-required-fact",
            description="Injected conditional fallback",
            quote="audit fixture",
            kind="project_fact_dependent_eligibility",
        ),
    ) if conditional else ()
    return RateRule(
        program_slug=slug,
        tier_id="audit-injected-positive",
        rate=0.99,
        is_band_ceiling=False,
        production_types=("feature_film",),
        min_qpe_usd=None,
        conditions=conditions,
        confidence_tier="VERIFIED",
        citation="independent audit fixture",
        source_ref="codex-final-runtime-audit",
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


@pytest.mark.parametrize("slug", ["ae_ad_film_rebate", "de_dfff"])
def test_direct_blocked_slug_refuses_injected_positive_rule(isolated_registries, slug):
    _RULES_BY_PROGRAM[slug] = (_rule(slug),)
    assert economic_block_for_program(slug)
    assert resolve_program_rate(slug, "feature_film", 5_000_000) is None
    assert classify_rate_resolution_failure(slug, "feature_film", 5_000_000) == RATE_FAILURE_AUTHORITY_EXHAUSTED


def test_known_alias_to_blocked_identity_refuses(isolated_registries):
    alias, canonical = "fj_film_incentive", "fj_film_rebate"
    _RULES_BY_PROGRAM[alias] = (_rule(alias),)
    _RULES_BY_PROGRAM[canonical] = (_rule(canonical),)
    assert economic_block_for_program(alias)
    assert resolve_program_rate(alias, "feature_film", 5_000_000) is None


def test_retired_identity_cannot_be_aliased_to_active_rule(isolated_registries):
    retired = "iceland_post_production_visual_effects_and_animation_incentive"
    PROGRAM_SLUG_ALIASES[retired] = "ca_film_30"
    assert economic_block_for_program(retired)
    assert resolve_program_rate(retired, "feature_film", 5_000_000) is None


def test_conditional_fallback_rule_cannot_reactivate_blocked_identity(isolated_registries):
    slug = "de_dfff"
    _RULES_BY_PROGRAM[slug] = (_rule(slug, conditional=True),)
    assert resolve_program_rate(slug, "feature_film", 5_000_000) is None


def test_alternate_rule_registration_cannot_reactivate_blocked_identity(isolated_registries):
    from app.data.program_rate_rules import register_rate_rules

    slug = "be_tax_shelter"
    register_rate_rules((_rule(slug),))
    assert resolve_program_rate(slug, "feature_film", 5_000_000) is None


def _candidate(slug: str, value: float = 999_999.0) -> StackCandidate:
    return StackCandidate(slug, "BE", value, 0.99, 1_000_000.0, "tax_credit")


def test_positive_blocked_candidate_cannot_enter_group_stack():
    clean = StackCandidate("eu_eurimages", "BE", 100_000.0, 0.10, 1_000_000.0, "grant")
    assert price_program_group_stack([_candidate("be_tax_shelter"), clean]) is None


def test_serialized_reconstruction_cannot_restore_blocked_component():
    raw = asdict(_candidate("be_tax_shelter"))
    restored = StackCandidate(**raw)
    clean = StackCandidate("eu_eurimages", "BE", 100_000.0, 0.10, 1_000_000.0, "grant")
    assert price_program_group_stack([restored, clean]) is None


def test_display_only_program_with_positive_value_is_rejected_from_stack():
    assert economic_block_for_program("be_tax_shelter")
    clean = StackCandidate("eu_eurimages", "BE", 100_000.0, 0.10, 1_000_000.0, "grant")
    assert price_program_group_stack([_candidate("be_tax_shelter"), clean]) is None


@pytest.mark.xfail(
    strict=True,
    reason="B4 canonicalization follows only one PROGRAM_SLUG_ALIASES hop",
)
def test_duplicate_alias_chain_cannot_reach_injected_live_rule(isolated_registries):
    """Required corruption case: a two-hop alias must inherit the terminal block."""
    outer = "__codex_audit_two_hop_alias__"
    PROGRAM_SLUG_ALIASES[outer] = "fj_film_incentive"
    _RULES_BY_PROGRAM[outer] = (_rule(outer),)
    assert economic_block_for_program(outer)
    assert resolve_program_rate(outer, "feature_film", 5_000_000) is None


def test_active_control_still_prices():
    result = resolve_program_rate("ca_film_30", "feature_film", 5_000_000)
    assert result is not None
    assert result.modeled_rate > 0
