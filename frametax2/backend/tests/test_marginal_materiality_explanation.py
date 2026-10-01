"""Marginal-materiality explanation contract (canonical-1.99.0).

A proven UPPER BOUND below the $100,000 hurdle is disclosed as such (never "unverified");
genuinely missing evidence stays unverified and fail-closed; the aggregate saving can never
subsidize an immaterial added jurisdiction; lazy enrichment covers every added jurisdiction."""
from __future__ import annotations

import pytest

from app.services import canonical_evaluation as ce
from app.services.canonical_production_view import (
    REC_STATUS_EVALUATED_ALTERNATIVE, _annotate_optimizer_scenario, _marginal_jurisdiction_materiality,
)
from tests.test_canonical_production_view import _projection_candidate

BELOW = "_MARGINAL_BENEFIT_BELOW_THRESHOLD_PROVEN_UPPER_BOUND"


def test_proven_upper_bound_below_threshold_is_not_labelled_unverified():
    entry = _projection_candidate(
        "h", npc=700_000.0, participants=["GR", "CA-MB"],
        marginal_jurisdiction_benefits_usd={}, marginal_jurisdiction_bounds_usd={"CA-MB": 42_000.0})
    ok, reason = _marginal_jurisdiction_materiality(entry, {})
    assert ok is False
    assert reason == f"JURISDICTION_CA-MB{BELOW}"
    assert not reason.startswith("NO_PRICED_PARENT_WITHOUT_")


def test_genuinely_missing_evidence_stays_unverified_and_fail_closed():
    for extra in ({}, {"marginal_jurisdiction_benefits_usd": {}},
                  {"marginal_jurisdiction_benefits_usd": {}, "marginal_jurisdiction_bounds_usd": {}}):
        entry = _projection_candidate("h", npc=700_000.0, participants=["GR", "CA-MB"], **extra)
        ok, reason = _marginal_jurisdiction_materiality(entry, {})
        assert ok is False and reason == "NO_PRICED_PARENT_WITHOUT_CA-MB"
    # an explicit None (reconstruction failed) is "uncomputed", also fail-closed
    entry = _projection_candidate("h", npc=700_000.0, participants=["GR", "CA-MB"],
                                  marginal_jurisdiction_benefits_usd={"CA-MB": None})
    assert _marginal_jurisdiction_materiality(entry, {}) == (False, "JURISDICTION_CA-MB_MARGINAL_BENEFIT_UNCOMPUTED")


def test_bound_at_or_above_hurdle_proves_nothing_and_does_not_pass():
    entry = _projection_candidate(
        "h", npc=700_000.0, participants=["GR", "CA-MB"],
        marginal_jurisdiction_benefits_usd={}, marginal_jurisdiction_bounds_usd={"CA-MB": 100_000.0})
    ok, reason = _marginal_jurisdiction_materiality(entry, {})
    assert ok is False and reason == "NO_PRICED_PARENT_WITHOUT_CA-MB", "a bound can never promote a candidate"


def test_exact_repriced_benefit_takes_precedence_over_a_bound():
    entry = _projection_candidate(
        "h", npc=700_000.0, participants=["GR", "CA-MB"],
        marginal_jurisdiction_benefits_usd={"CA-MB": 250_000.0}, marginal_jurisdiction_bounds_usd={"CA-MB": 10.0})
    assert _marginal_jurisdiction_materiality(entry, {}) == (True, None)


def test_aggregate_savings_cannot_subsidize_an_immaterial_added_jurisdiction():
    entry = _projection_candidate(
        "triple", npc=400_000.0, participants=["GR", "CA-MB", "NL"],
        marginal_jurisdiction_benefits_usd={"CA-MB": 600_000.0},
        marginal_jurisdiction_bounds_usd={"NL": 30_000.0})
    annotated = _annotate_optimizer_scenario(entry, 1_000_000.0, {})
    assert annotated["savings_vs_current_usd"] == pytest.approx(600_000.0)   # aggregate clears the bar
    assert annotated["is_recommended"] is False
    assert annotated["recommendation_status"] == REC_STATUS_EVALUATED_ALTERNATIVE
    assert annotated["recommendation_reason"] == f"JURISDICTION_NL{BELOW}"   # visible, with the true reason


def test_lazy_enrichment_persists_every_added_jurisdiction_and_marks_lost_reconstruction_unverified():
    from app.calculators.qualification_derivation import BudgetLine
    from tests.test_structural_archetype_generator import _economic_inputs

    cats = [("1", "principal photography", "production", 2_000_000.0), ("2", "post sound", "post_production", 400_000.0),
            ("3", "vfx work", "vfx", 300_000.0)]
    lines = [BudgetLine(account_code=c, description=d, amount_usd=a, spend_category=cat, is_memo=False,
                        line_id=f"BL-{c}") for c, d, cat, a in cats]
    inputs = _economic_inputs(
        jurisdiction_code="GR", gross_budget_usd=2_700_000.0, leaf_account_sum_usd=2_700_000.0,
        budget_lines=lines, spend_category_by_code={c: cat for c, _, cat, _ in cats})
    progs = {"US-GA": "us_ga_film_credit", "NZ": "new_zealand_screen_production_grant_—_international_post_vfx",
             "IE": "ie_section_481"}
    # two routed components -> two added jurisdictions
    _, comps = ce._build_hybrid_route(inputs, "US-GA", "us_ga_film_credit", ("post", "vfx"), ["NZ", "IE"], progs)
    exact = ce._hybrid_marginal_jurisdiction_benefits(comps, "US-GA", 2_700_000.0, inputs, 2_000_000.0)
    expected = {"NZ", "IE"}
    assert set(exact) <= expected and exact, "counterfactual reprice produced entries"

    result = ce._complete_marginal_map(sorted(expected), exact)
    assert set(result) == expected, "every added jurisdiction is present (exact value or explicit None)"
    assert all(result[j] == exact[j] for j in exact)
    # a route that reconstructs to <2 components (computed empty) yields explicit None per jurisdiction
    lost = ce._complete_marginal_map(sorted(expected), {})
    assert lost == {"IE": None, "NZ": None}


def test_engine_version_advanced_past_the_shared_pre_repair_stamp():
    assert ce.ENGINE_VERSION == "canonical-1.99.0"
