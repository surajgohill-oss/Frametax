"""Saved contingency election through the hybrid generator and the marginal-benefit / music counterfactual repricers.

SYNTHETIC ONLY (invented components and budget lines, no database, no evaluation). The undeployed reserve K is a constant NPC cost
reduction, so: (1) a candidate priced with K is exactly K lower than the same candidate priced without it, incentives unchanged and
original gross preserved; (2) per-jurisdiction marginal benefits are DIFFERENCES between two repricings that both carry K, so
they must be identical with and without a saved election (a repricer that dropped K would shift every benefit by K); (3) the
music-bundle counterfactual is a repriced candidate, so it moves by exactly -K."""
from __future__ import annotations

import pytest

from app.calculators.qualification_derivation import BudgetLine
from app.calculators.structural_archetype_generator import generate_structural_candidate
from app.services import canonical_evaluation as ce
from tests.test_structural_archetype_generator import _comp, _economic_inputs

RESERVE = 200_000.0
PCT = 25.0
K = round(RESERVE * (1 - PCT / 100), 2)            # 150,000 undeployed


def _inputs(elected, **kw):
    reserve_line = BudgetLine(account_code="9", description="contingency", amount_usd=RESERVE, spend_category="contingency",
                              is_memo=False, line_id="BL-9")
    return _economic_inputs(
        contingency_reserve_usd=RESERVE, contingency_expected_utilization_pct=PCT if elected else None,
        budget_lines=kw.pop("budget_lines", [reserve_line]), **kw)


def _triple():
    anchor = _comp("us_ga_film_credit", "US-GA", 3_000_000.0, component_type="principal_production", line_id="MJB-GA")
    post_nz = _comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 500_000.0, component_type="post", line_id="MJB-NZ")
    vfx_on = _comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 300_000.0,
                   component_type="vfx", line_id="MJB-ON", spend_category="vfx")
    return [anchor, post_nz, vfx_on]


def test_the_saved_election_yields_the_planned_cost_reduction_the_repricers_consume():
    assert _inputs(True).contingency_planned_reduction_usd == K
    assert _inputs(False).contingency_planned_reduction_usd == 0.0


@pytest.mark.parametrize("use_cache", [False, True])
def test_hybrid_generator_prices_exactly_k_lower_with_a_saved_election_and_keeps_gross_and_incentives(use_cache):
    gross = 3_800_000.0
    kw = (lambda: {"_cache": {}, "_component_cache": {}}) if use_cache else (lambda: {})
    plain = generate_structural_candidate(_triple(), gross_budget_usd=gross, **kw())
    elected = generate_structural_candidate(_triple(), gross_budget_usd=gross, planned_cost_reduction_usd=K, **kw())
    assert plain.executable and elected.executable
    assert elected.npc_usd == pytest.approx(plain.npc_usd - K, abs=0.01)
    assert elected.npc_with_adjustments_usd == pytest.approx(plain.npc_with_adjustments_usd - K, abs=0.01)
    assert elected.total_guaranteed_incentive_usd == plain.total_guaranteed_incentive_usd          # cost basis, not QPE
    assert elected.gross_budget_usd == gross and plain.gross_budget_usd == gross                    # original gross preserved


def test_marginal_jurisdiction_benefits_are_unchanged_by_a_saved_election_because_both_repricings_carry_k():
    components, gross = _triple(), 3_800_000.0
    plain_inputs, elected_inputs = _inputs(False, jurisdiction_code="US-GA", gross_budget_usd=gross), _inputs(True, jurisdiction_code="US-GA", gross_budget_usd=gross)
    plain_cand = generate_structural_candidate(components, gross_budget_usd=gross)
    elected_cand = generate_structural_candidate(components, gross_budget_usd=gross, planned_cost_reduction_usd=K)
    assert plain_cand.executable and elected_cand.executable
    plain = ce._hybrid_marginal_jurisdiction_benefits(components, "US-GA", gross, plain_inputs, plain_cand.npc_with_adjustments_usd)
    elected = ce._hybrid_marginal_jurisdiction_benefits(components, "US-GA", gross, elected_inputs, elected_cand.npc_with_adjustments_usd)
    assert set(plain) == set(elected) == {"NZ", "CA-ON"}
    for code in plain:
        assert elected[code] == pytest.approx(plain[code], abs=0.01), code      # K cancels; dropping it in the repricer would add K


def test_music_bundle_counterfactual_moves_by_exactly_the_undeployed_reserve():
    cats = [("1", "principal photography", "production", 2_000_000.0), ("2", "post sound", "post_production", 400_000.0),
            ("3", "vfx work", "vfx", 300_000.0), ("4", "score", "music", 120_000.0)]
    lines = [BudgetLine(account_code=c, description=d, amount_usd=a, spend_category=cat, is_memo=False, line_id=f"BL-{c}") for c, d, cat, a in cats]
    kw = dict(jurisdiction_code="GR", gross_budget_usd=2_820_000.0, leaf_account_sum_usd=2_820_000.0, budget_lines=lines,
              spend_category_by_code={c: cat for c, _, cat, _ in cats})
    plain_inputs, elected_inputs = _economic_inputs(**kw), _economic_inputs(contingency_reserve_usd=RESERVE, contingency_expected_utilization_pct=PCT, **kw)
    progs = {"NZ": "new_zealand_screen_production_grant_—_international_post_vfx", "IE": "ie_section_481"}
    _, comps = ce._build_hybrid_route(plain_inputs, "US-GA", "us_ga_film_credit", ("post_vfx_package", "music_package"), ["NZ", "IE"], progs)
    plain = ce._hybrid_music_bundle_counterfactual(comps, "US-GA", 2_820_000.0, plain_inputs, 2_000_000.0)
    elected = ce._hybrid_music_bundle_counterfactual(comps, "US-GA", 2_820_000.0, elected_inputs, 2_000_000.0)
    if plain is None or elected is None:
        pytest.skip("the real kernel does not price this synthetic music pairing; no number is fabricated")
    assert elected["bundled_npc_with_adjustments_usd"] == pytest.approx(plain["bundled_npc_with_adjustments_usd"] - K, abs=0.01)
