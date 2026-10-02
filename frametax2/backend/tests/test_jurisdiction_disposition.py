"""Shared jurisdiction disposition: RED only for a confirmed hard block; everything unresolved is AMBER.
Rows are the exact shapes the evaluator persists for the real acceptance productions."""
from __future__ import annotations

import pytest

from app.services.jurisdiction_disposition import (
    HARD_BLOCK, NEEDS_FACTS, annotate_rows, classify_jurisdiction_disposition as classify, disposition_totals,
)

TX = {"candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "rejection_reason_class": "PRICING_BLOCKED",
      "reason": "US-TX/us_tx_miip: the program states only a rate CEILING (31%) with no guaranteed floor tier, and its "
                "award condition(s) [us-tx-award-allocation-required, us-tx-resident-crew-pct] cannot be pre-evaluated."}
SK = {"candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "AUTHORITY_UNRESOLVED_NON_PRICEABLE",
      "reason": "Production-capable, incentive pending: the production's statutory conditions are unmet. Retained for capability."}


def test_texas_award_ceiling_is_amber_with_the_exact_reason():
    d = classify(TX)
    assert d["disposition"] == NEEDS_FACTS and d["disposition_kind"] == "rate_or_award_confirmation_required"
    assert "us-tx-award-allocation-required" in d["missing_facts_reason"] and d["hard_block_reason"] is None


def test_saskatchewan_unresolved_authority_is_amber_not_red():
    d = classify(SK)
    assert d["disposition"] == NEEDS_FACTS and d["disposition_kind"] == "unresolved_eligibility_or_authority"


@pytest.mark.parametrize("row", [
    {"candidate_status": "QUALIFICATION_HARD_FAIL", "reason": "Qualification state HARD_FAIL"},
    {"candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "SUPERSEDED", "reason": "superseded"},
    {"candidate_status": "RULE_REJECTED", "rejection_reason_class": "MINIMUM_SPEND_FAIL"},
    {"candidate_status": "RULE_REJECTED", "rejection_reason_class": "PAIRWISE_INCOMPATIBLE"},
])
def test_confirmed_hard_blocks_stay_red_and_always_carry_a_reason(row):
    d = classify(row)
    assert d["disposition"] == HARD_BLOCK and d["hard_block_reason"] and d["missing_facts_reason"] is None


@pytest.mark.parametrize("row", [
    {"candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "NON_GUARANTEED_SELECTIVE"},
    {"candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "rejection_reason_class": "UNPRICEABLE_AUTHORITY_INSUFFICIENT"},
    {"candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "rejection_reason_class": "PRICING_BLOCKED",
     "reason": "cap cannot be safely converted to USD (MISSING_RATE: No sourced FX rate for CZK)"},
    {"candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "rejection_reason_class": "PRICING_BLOCKED",
     "reason": "statutory rate did not resolve for this production type -- minimum-spend or eligibility conditions unmet"},
    {"candidate_status": "SOMETHING_NEW", "rejection_reason_class": None, "reason": ""},
])
def test_missing_or_unresolved_is_never_red(row):
    d = classify(row)
    assert d["disposition"] == NEEDS_FACTS and d["hard_block_reason"] is None and d["missing_facts_reason"]


def test_annotation_and_exact_totals_use_the_same_classifier():
    rows = annotate_rows([dict(TX), dict(SK), {"candidate_status": "QUALIFICATION_HARD_FAIL"}])
    assert [r["disposition"] for r in rows] == [NEEDS_FACTS, NEEDS_FACTS, HARD_BLOCK]
    by_reason = [
        {"count": 9, "candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "rejection_reason_class": "PRICING_BLOCKED"},
        {"count": 11, "candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "AUTHORITY_UNRESOLVED_NON_PRICEABLE"},
        {"count": 1, "candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "SUPERSEDED"},
        {"count": 1, "candidate_status": "QUALIFICATION_HARD_FAIL", "rejection_reason_class": None},
        {"count": 25, "candidate_status": "CO_PRO_OPPORTUNITY", "rejection_reason_class": None},
        {"count": 999, "candidate_status": "RULE_REJECTED", "rejection_reason_class": "MINIMUM_SPEND_FAIL"},
    ]
    assert disposition_totals(by_reason) == {HARD_BLOCK: 2, NEEDS_FACTS: 20}


def test_blocked_totals_use_rows_when_complete_and_causes_are_single_per_row():
    from app.services.jurisdiction_disposition import ALL_CAUSES, blocked_totals
    rows = annotate_rows([dict(TX), dict(SK), {"candidate_status": "QUALIFICATION_HARD_FAIL"},
                          {"candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "SUPERSEDED"},
                          {"candidate_status": "DOMINATED_WITH_PROOF"}])
    by_reason = [{"count": 1, "candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "rejection_reason_class": "PRICING_BLOCKED"},
                 {"count": 1, "candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "AUTHORITY_UNRESOLVED_NON_PRICEABLE"},
                 {"count": 1, "candidate_status": "QUALIFICATION_HARD_FAIL", "rejection_reason_class": None},
                 {"count": 1, "candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "SUPERSEDED"},
                 {"count": 9, "candidate_status": "DOMINATED_WITH_PROOF", "rejection_reason_class": None}]
    t = blocked_totals(rows, by_reason)
    assert t["exact"] and t["disposition"] == {"HARD_BLOCK": 2, "NEEDS_FACTS": 2}
    assert sum(t["causes"].values()) == 4 and set(t["causes"]) == set(ALL_CAUSES)
    assert t["causes"]["MISSING_PROJECT_FACT_OR_CONFIRMATION"] == 1      # Texas award/rate confirmation
    assert t["causes"]["AUTHORITY_PROVENANCE_UNCERTAINTY"] == 1          # Saskatchewan unresolved authority
    assert t["causes"]["CONFIRMED_LEGAL_PROGRAM_INELIGIBILITY"] == 2


def test_missing_capability_record_is_amber_never_a_hard_block():
    d = classify({"candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": None,
                  "reason": "required capability missing: no capability record for desert environments"})
    assert d["disposition"] == NEEDS_FACTS and d["blocked_cause"] == "MISSING_LOCATION_CAPABILITY_DATA"


def test_fit_actionability_amber_only_for_missing_capability_data():
    from app.services.production_fit import fit_actionability
    amber = fit_actionability({"production_fit_status": "UNKNOWN", "production_fit_reasons": ["DESERT_ENVIRONMENTS_NOT_ASSESSABLE"]})
    assert amber["actionability"] == "AMBER" and "DESERT" in amber["actionability_reason"]
    assert fit_actionability({"production_fit_status": "UNKNOWN", "production_fit_reasons": ["NO_REQUIREMENTS_ON_FILE"]})["actionability"] == "SLATE"
    assert fit_actionability({"production_fit_status": "WEAK", "production_fit_reasons": ["MN:MARINE_MISMATCH"]})["actionability"] == "SLATE"
    assert fit_actionability({"recommendation_status": "RECOMMENDED"})["actionability"] == "GREEN"
