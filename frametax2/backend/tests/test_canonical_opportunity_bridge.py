"""
canonical_opportunity_bridge.py — focused unit tests.

Reinvestment + Qualification Opportunity Optimization. Proves the
mandatory prevention invariants: cash != deferred, qualifying spend !=
gross invoice, unused cap != automatic savings, incremental incentive !=
net benefit, and fail-closed behavior for unknown facts.
"""
from __future__ import annotations

from app.calculators.canonical_opportunity_bridge import (
    STATUS_REQUIRES_SCREEN_ANALYZER_FACT,
    discover_cultural_test_gap_opportunity,
    discover_fee_cap_headroom_opportunity,
    discover_per_person_cap_headroom_opportunity,
    discover_qualification_gap_opportunity,
    discover_reinvestment_opportunity,
    opportunity_to_dict,
)


def test_fee_cap_headroom_uses_real_canonical_cap_never_invented():
    """cy_film_rebate's 30% ATL cap is real, primary-source-cited
    canonical data (program_requirements.py) -- a program with no cap on
    file must return None, never a guessed percentage."""
    opp = discover_fee_cap_headroom_opportunity(
        "CY", "cy_film_rebate", current_atl_spend_usd=200_000, total_budget_usd=2_000_000, effective_rate=0.35,
    )
    assert opp is not None
    assert opp.incremental_qpe_usd == 400_000.0  # (2_000_000 * 0.30) - 200_000

    no_cap = discover_fee_cap_headroom_opportunity(
        "ZZ", "no_such_program", current_atl_spend_usd=1.0, total_budget_usd=1.0, effective_rate=0.1,
    )
    assert no_cap is None


def test_fee_cap_headroom_no_headroom_returns_none():
    """Already at or above the cap must never report negative/zero
    headroom as an opportunity."""
    opp = discover_fee_cap_headroom_opportunity(
        "CY", "cy_film_rebate", current_atl_spend_usd=900_000, total_budget_usd=2_000_000, effective_rate=0.35,
    )
    assert opp is None


def test_incremental_incentive_never_equals_net_benefit_in_new_cash_scenario():
    """Task 8's core invariant: the reasoning trace must explicitly
    disclose that a NEW-CASH funding scenario nets a LOSS (spending $1 to
    get back less than $1 of credit) -- incentive growth alone is never
    reported as costless benefit. The structured net_benefit_usd field
    reflects only the reallocation (budget-neutral) scenario; the
    new-cash figure is disclosed in trace, never silently equated."""
    opp = discover_fee_cap_headroom_opportunity(
        "CY", "cy_film_rebate", current_atl_spend_usd=200_000, total_budget_usd=2_000_000, effective_rate=0.35,
    )
    assert opp.incremental_incentive_usd == 140_000.0
    assert opp.net_benefit_usd == 140_000.0  # reallocation scenario only
    joined_trace = " ".join(opp.reasoning_trace)
    assert "LOSS" in joined_trace
    assert "NOT recommended" in joined_trace or "not recommended" in joined_trace.lower()


def test_unused_cap_headroom_is_not_automatically_recommended():
    """status must be CONDITIONAL (requires a real funding-source fact),
    never RESOLVED_PRICEABLE -- an unused cap is not automatic savings."""
    opp = discover_fee_cap_headroom_opportunity(
        "CY", "cy_film_rebate", current_atl_spend_usd=200_000, total_budget_usd=2_000_000, effective_rate=0.35,
    )
    assert opp.status == "CONDITIONAL_PROJECT_FACT_DEPENDENT"
    assert opp.required_facts


def test_per_person_cap_headroom_is_disclosure_only_zero_opportunity():
    opp = discover_per_person_cap_headroom_opportunity(
        "CY", "cy_film_rebate", high_earner_amounts_usd=[650_001.0], effective_rate=0.35,
    )
    # cy_film_rebate has per_project_cap_usd, not per_person_cap_usd -- expect None
    assert opp is None


def test_qualification_gap_reports_measurable_curable_shortfall():
    gaps = discover_qualification_gap_opportunity(
        "MU", "mu_edb_incentive", actual_local_spend_usd=800_000, actual_total_budget_usd=None,
    )
    assert len(gaps) == 1
    g = gaps[0]
    assert g.gap_amount_usd == 200_000.0
    assert g.gap_measure == "min_local_spend_usd"
    assert g.incremental_cash_usd == 200_000.0  # real cash, not free


def test_qualification_gap_no_shortfall_returns_empty():
    gaps = discover_qualification_gap_opportunity(
        "MU", "mu_edb_incentive", actual_local_spend_usd=2_000_000, actual_total_budget_usd=None,
    )
    assert gaps == []


def test_cultural_gap_fails_closed_on_unknown_facts():
    """Codex/Task 7's fail-closed requirement: a real cultural-test
    threshold must NEVER be silently scored -- it must be explicitly
    marked as requiring facts this system does not (yet) have."""
    opp = discover_cultural_test_gap_opportunity("MT", "mt_mfc_rebate")
    assert opp is not None
    assert opp.status == STATUS_REQUIRES_SCREEN_ANALYZER_FACT
    assert opp.required_facts
    assert "never" in " ".join(opp.risk_notes).lower() or "Never" in " ".join(opp.risk_notes)


def test_cultural_gap_none_when_no_threshold_on_file():
    assert discover_cultural_test_gap_opportunity("ZZ", "no_such_program") is None


def test_reinvestment_cash_never_equals_deferred_consideration():
    """The canonical $600k/$400k/$200k example: face value, cash paid,
    and deferred/reinvested amount must all be tracked as three distinct
    numbers, never conflated."""
    opp = discover_reinvestment_opportunity(
        "MU", "mu_edb_incentive", "post",
        face_value_usd=600_000.0, cash_paid_usd=400_000.0,
        effective_rate=0.30, base_qpe_usd=1_000_000.0,
    )
    assert opp is not None
    assert opp.current_amount_usd == 600_000.0       # gross/face value
    assert opp.proposed_amount_usd == 400_000.0        # cash paid
    assert opp.deferred_or_reinvested_usd == 200_000.0  # neither equals the other


def test_reinvestment_qualifying_spend_never_assumed_to_equal_gross_invoice():
    """The conservative (Scenario B, cash-paid-only) treatment must never
    silently assume the full face value qualifies."""
    opp = discover_reinvestment_opportunity(
        "MU", "mu_edb_incentive", "post",
        face_value_usd=600_000.0, cash_paid_usd=400_000.0,
        effective_rate=0.30, base_qpe_usd=1_000_000.0,
    )
    trace_text = " ".join(opp.reasoning_trace)
    assert "QPE=$400,000" in trace_text  # cash-paid scenario
    assert "QPE=$600,000" in trace_text  # FMV scenario, shown but not assumed
    assert opp.net_benefit_usd is None   # never asserted while authority is unresolved


def test_reinvestment_fully_cash_transaction_returns_none():
    """No deferred portion -- nothing to model as a reinvestment
    opportunity."""
    opp = discover_reinvestment_opportunity(
        "MU", "mu_edb_incentive", "post",
        face_value_usd=400_000.0, cash_paid_usd=400_000.0,
        effective_rate=0.30, base_qpe_usd=1_000_000.0,
    )
    assert opp is None


def test_opportunity_provenance_survives_serialization():
    opp = discover_fee_cap_headroom_opportunity(
        "CY", "cy_film_rebate", current_atl_spend_usd=200_000, total_budget_usd=2_000_000, effective_rate=0.35,
    )
    d = opportunity_to_dict(opp)
    assert d["opportunity_id"] == opp.opportunity_id
    assert d["reasoning_trace"] == list(opp.reasoning_trace)
    assert d["required_facts"] == list(opp.required_facts)
    assert d["authority_basis"] is not None
