"""
Proactive Opportunity Discovery Reconciliation — focused unit tests.

Covers discover_potential_reinvestment_candidates (Task 3, proactive,
budget-triggered, no known deal terms) and
discover_qualification_lever_opportunities (Task 5, real movable-component
budget amounts as candidate levers). Both must never fabricate a fact and
must always require explicit user/production confirmation before any
economics are asserted.
"""
from __future__ import annotations

from app.calculators.canonical_opportunity_bridge import (
    FACT_PROPOSED_CHANGE,
    FACT_USER_CONFIRMATION_REQUIRED,
    STATUS_CONDITIONAL,
    STATUS_REQUIRES_USER_FACT,
    TYPE_POTENTIAL_REINVESTMENT,
    TYPE_QUALIFICATION_LEVER,
    discover_potential_reinvestment_candidates,
    discover_qualification_gap_opportunity,
    discover_qualification_lever_opportunities,
)


def test_potential_reinvestment_triggers_on_real_material_component_spend():
    """A real post-production spend of $172,904 (FVD's own real number)
    clears the materiality floor and must surface as a candidate — with
    NO assumed cash/deferred split (Task 3: 'do not fabricate an
    agreement')."""
    opps = discover_potential_reinvestment_candidates(
        "MU", "mu_edb_incentive", {"post": 172_904.0, "vfx": 10_000.0},
    )
    assert len(opps) == 1  # vfx below materiality floor
    opp = opps[0]
    assert opp.opportunity_type == TYPE_POTENTIAL_REINVESTMENT
    assert opp.status == STATUS_REQUIRES_USER_FACT
    assert opp.fact_classification == FACT_USER_CONFIRMATION_REQUIRED
    assert opp.current_amount_usd == 172_904.0
    assert opp.proposed_amount_usd is None          # never invented
    assert opp.deferred_or_reinvested_usd is None    # never invented
    assert opp.incremental_incentive_usd == 0.0
    assert opp.required_facts
    assert "willing" in " ".join(opp.required_facts).lower()


def test_potential_reinvestment_below_materiality_floor_returns_nothing():
    opps = discover_potential_reinvestment_candidates("MU", "mu_edb_incentive", {"post": 1_000.0})
    assert opps == []


def test_potential_reinvestment_only_scans_real_movable_component_categories():
    """A component_for() output not in the recognized proactive category
    set (e.g. 'overhead') must never surface a candidate — no invented
    category is ever scanned."""
    opps = discover_potential_reinvestment_candidates("MU", "mu_edb_incentive", {"overhead": 500_000.0})
    assert opps == []


def test_qualification_lever_requires_real_movable_spend_covering_the_gap():
    """The canonical Mauritius min-local-spend gap example: real post
    spend of $172,904 does NOT clear a $200,000 gap -- no lever should be
    proposed. A larger real amount does."""
    gaps = discover_qualification_gap_opportunity(
        "MU", "mu_edb_incentive", actual_local_spend_usd=800_000, actual_total_budget_usd=None,
    )
    assert gaps and gaps[0].gap_amount_usd == 200_000.0

    too_small = discover_qualification_lever_opportunities(
        "MU", "mu_edb_incentive", gaps, {"post": 172_904.0},
    )
    assert too_small == []

    sufficient = discover_qualification_lever_opportunities(
        "MU", "mu_edb_incentive", gaps, {"post": 250_000.0},
    )
    assert len(sufficient) == 1
    lever = sufficient[0]
    assert lever.opportunity_type == TYPE_QUALIFICATION_LEVER
    assert lever.status == STATUS_CONDITIONAL
    assert lever.fact_classification == FACT_PROPOSED_CHANGE
    assert lever.source_component == "post"
    assert lever.gap_amount_usd == 200_000.0
    # Never auto-applies -- always requires explicit operational confirmation.
    assert "confirm" in " ".join(lever.required_facts).lower()


def test_qualification_lever_never_invents_a_component_not_in_real_budget():
    gaps = discover_qualification_gap_opportunity(
        "MU", "mu_edb_incentive", actual_local_spend_usd=800_000, actual_total_budget_usd=None,
    )
    levers = discover_qualification_lever_opportunities("MU", "mu_edb_incentive", gaps, {})
    assert levers == []


def test_qualification_lever_no_gap_no_lever():
    levers = discover_qualification_lever_opportunities("MU", "mu_edb_incentive", [], {"post": 500_000.0})
    assert levers == []
