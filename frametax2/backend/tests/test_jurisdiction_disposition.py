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


# ── exact program blocker (registry-derived) ────────────────────────────────────────────────────
from app.services.jurisdiction_disposition import (  # noqa: E402
    AMOUNT_PREFIX, EVIDENCED_PREFIX, NOT_APPLICABLE, enrich_row_with_program_detail, rate_rule_fact_keys,
)


def _row(status, cls, reason=""):
    return annotate_rows([{"candidate_status": status, "rejection_reason_class": cls, "reason": reason}])[0]


def test_stored_fact_prefixes_match_the_evaluator_constants():
    from app.services import canonical_project_economics as econ
    assert EVIDENCED_PREFIX == econ.FACT_EVIDENCED_PROGRAM_FACT_PREFIX
    assert AMOUNT_PREFIX == econ.FACT_AMOUNT_FACT_PREFIX


def test_texas_serves_every_required_proposition_and_the_stored_value_search_uses_the_evaluators_keys():
    keys = rate_rule_fact_keys("us_tx_miip")
    assert {EVIDENCED_PREFIX + "us_tx_miip_award_confirmed", AMOUNT_PREFIX + "us_tx_miip_resident_crew_pct",
            AMOUNT_PREFIX + "us_tx_miip_resident_cast_pct", EVIDENCED_PREFIX + "us_tx_miip_pool_period_valid",
            AMOUNT_PREFIX + "us_tx_miip_awarded_rate_pct"} == keys
    row = enrich_row_with_program_detail(_row("UNPRICEABLE_AUTHORITY_INSUFFICIENT", "PRICING_BLOCKED", TX["reason"]), "us_tx_miip", {})
    d = row["blocker_detail"]
    assert d["kind"] == "RATE_CEILING_WITH_NO_GUARANTEED_FLOOR" and d["reconciliation_class"] == "CONDITIONAL_CEILING_NO_VALID_FLOOR"
    assert d["potential_ceiling_rate"] == 0.31 and d["guaranteed_floor"].startswith("none")
    assert len(d["unresolved_propositions"]) == 5 and all(p["stored_value"] is None for p in d["unresolved_propositions"])
    assert d["stored_facts_found"] == []
    # facts that DO exist are found and shown with their stored value (nothing is claimed missing)
    stored = {EVIDENCED_PREFIX + "us_tx_miip_award_confirmed": "true", AMOUNT_PREFIX + "us_tx_miip_resident_crew_pct": "41"}
    d2 = enrich_row_with_program_detail(_row("UNPRICEABLE_AUTHORITY_INSUFFICIENT", "PRICING_BLOCKED", TX["reason"]), "us_tx_miip", stored)["blocker_detail"]
    found = {p["fact_key"]: p["stored_value"] for p in d2["unresolved_propositions"] if p["stored_value"] is not None}
    assert found == {"us_tx_miip_award_confirmed": "true", "us_tx_miip_resident_crew_pct": "41"}
    assert len(d2["stored_facts_found"]) == 2


def test_saskatchewan_is_a_discretionary_award_not_provenance_and_not_statutory_conditions_unmet():
    row = enrich_row_with_program_detail(_row("FEASIBILITY_REVIEW_REQUIRED", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", SK["reason"]),
                                         "ca_sk_creative_saskatchewan_grant", {})
    d = row["blocker_detail"]
    assert d["kind"] == "DISCRETIONARY_AWARD_NOT_CONFIRMED" and d["canonical_disposition"] == "DISPLAY_ONLY_ZERO_GUARANTEED"
    assert row["disposition"] == NEEDS_FACTS and row["blocked_cause"] == "MISSING_PROJECT_FACT_OR_CONFIRMATION"
    assert "discretionary" in row["missing_facts_reason"] and "statutory conditions are unmet" not in row["missing_facts_reason"]
    assert d["stated_rates"]["stated_ceiling_rate"] == 0.30 and d["stated_rates"]["program_cap_usd"] == 5_000_000.0
    assert "NOT what blocks" in d["provenance_axis"]
    assert row["engine_reason"] == SK["reason"], "the engine sentence is preserved verbatim"


def test_authority_exhausted_programs_keep_their_rate_rule_and_are_amber_with_the_exact_ruling():
    row = enrich_row_with_program_detail(_row("FEASIBILITY_REVIEW_REQUIRED", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "x"), "al_cash_rebate", {})
    assert row["blocker_detail"]["kind"] == "AUTHORITY_EXHAUSTED_FAIL_CLOSED" and row["disposition"] == NEEDS_FACTS
    assert row["blocked_cause"] == "AUTHORITY_PROVENANCE_UNCERTAINTY"


def test_a_program_scoped_to_another_production_type_is_not_applicable_never_red_or_amber():
    r = enrich_row_with_program_detail(_row("FEASIBILITY_REVIEW_REQUIRED", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "x"),
                                       "cz_film_incentive_animation", {}, "feature_film")
    assert r["disposition"] == NOT_APPLICABLE and r["blocker_detail"]["reconciliation_class"] == "NOT_APPLICABLE_PRODUCTION_TYPE"
    assert r["hard_block_reason"] is None and r["missing_facts_reason"] is None
    # the same program IS applicable to an animation production
    r2 = enrich_row_with_program_detail(_row("FEASIBILITY_REVIEW_REQUIRED", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "x"),
                                        "cz_film_incentive_animation", {}, "animation")
    assert r2["disposition"] != NOT_APPLICABLE


def test_hard_failures_keep_a_specific_program_reason():
    r = enrich_row_with_program_detail(_row("FEASIBILITY_REVIEW_REQUIRED", "SUPERSEDED", "x"), "ae_dxb_dpip", {})
    assert r["disposition"] == HARD_BLOCK and r["blocker_detail"]["kind"] == "PROGRAM_SUPERSEDED"
    q = enrich_row_with_program_detail(_row("QUALIFICATION_HARD_FAIL", None, "Qualification state HARD_FAIL"), "ca_federal_cptc", {})
    assert q["disposition"] == HARD_BLOCK and q["blocker_detail"]["kind"] == "MANDATORY_QUALIFICATION_GATE_FAILED"


def test_totals_count_not_applicable_and_reconciliation_classes_from_the_enriched_rows():
    from app.services.jurisdiction_disposition import blocked_totals
    rows = [
        enrich_row_with_program_detail(_row("UNPRICEABLE_AUTHORITY_INSUFFICIENT", "PRICING_BLOCKED", TX["reason"]), "us_tx_miip", {}, "feature_film"),
        enrich_row_with_program_detail(_row("FEASIBILITY_REVIEW_REQUIRED", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", SK["reason"]), "ca_sk_creative_saskatchewan_grant", {}, "feature_film"),
        enrich_row_with_program_detail(_row("FEASIBILITY_REVIEW_REQUIRED", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "x"), "cz_film_incentive_animation", {}, "feature_film"),
        enrich_row_with_program_detail(_row("FEASIBILITY_REVIEW_REQUIRED", "SUPERSEDED", "x"), "ae_dxb_dpip", {}, "feature_film"),
    ]
    by_reason = [{"count": 1, "candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "rejection_reason_class": "PRICING_BLOCKED"},
                 {"count": 2, "candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "AUTHORITY_UNRESOLVED_NON_PRICEABLE"},
                 {"count": 1, "candidate_status": "FEASIBILITY_REVIEW_REQUIRED", "rejection_reason_class": "SUPERSEDED"}]
    t = blocked_totals(rows, by_reason)
    assert t["disposition"] == {"HARD_BLOCK": 1, "NEEDS_FACTS": 2, "NOT_APPLICABLE": 1}
    assert t["reconciliation"] == {"CONDITIONAL_CEILING_NO_VALID_FLOOR": 1, "DISCRETIONARY_AWARD_ZERO_GUARANTEED": 1,
                                   "NOT_APPLICABLE_PRODUCTION_TYPE": 1, "GENUINE_HARD_FAILURE": 1}
