"""Jurisdiction accounting (2026-10-02): content gates, program-level maximum potential, exact blockers for the
previously unaccounted programs, and Globe coordinate coverage. DB-free (pure registries + the shared owners)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.services.incentive_potential import CEILING_CONDITIONAL, CEILING_NOT_ESTABLISHED, build_program_maximum_potential
from app.services.jurisdiction_disposition import (
    HARD_BLOCK, NEEDS_FACTS, annotate_rows, enrich_row_with_program_detail, rate_rule_fact_keys,
)
from app.services.program_content_gates import (
    ADVISORY, CONFIRMED_MANDATORY, KIND_FILMING_NON_OBJECTION, KIND_SCRIPT_CONTENT_CLEARANCE, content_gate_inventory,
    content_gates_for_program, gate_fact_key,
)

SA = "sa_film_commission_rebate"


def _row(status="RULE_REJECTED", cls="STATUTORY_CONDITIONS_UNMET"):
    return {"candidate_status": status, "rejection_reason_class": cls, "reason": "engine sentence"}


# ── Saudi: stored rate, exact blocker, maximum potential ────────────────────────────────────────────────────────
def test_saudi_stored_rate_is_a_verified_60_percent_flat_tier_not_the_stale_40():
    from app.data.program_rate_rules import get_rate_rules

    rules = get_rate_rules(SA)
    assert [(r.tier_id, r.rate, r.confidence_tier, r.is_band_ceiling) for r in rules] == [("sa-flat-60", 0.6, "VERIFIED", False)]
    # the DISCOVERY-tier catalog's 40% is the stale figure the RateRule supersedes
    from app.data import global_inventory as gi

    assert {p.max_rate for p in gi.ALL_PROGRAMS if p.jurisdiction_code == "SA" and p.max_rate} == {0.4}


def test_saudi_is_a_discretionary_award_needs_facts_with_the_exact_unresolved_propositions():
    row = _row()
    annotate_rows([row])
    enrich_row_with_program_detail(row, SA, {}, "feature_film")
    assert row["disposition"] == NEEDS_FACTS
    d = row["blocker_detail"]
    assert d["reconciliation_class"] == "DISCRETIONARY_AWARD_ZERO_GUARANTEED"
    assert d["canonical_disposition"] == "DISPLAY_ONLY_ZERO_GUARANTEED"
    ids = [p["condition_id"] for p in d["unresolved_propositions"]]
    assert ids == ["discretionary-award"], "no rate-rule condition exists; the award itself is the open proposition"
    assert d["unresolved_propositions"][0]["fact_key"] == f"{SA}__discretionary_award_confirmed"
    from app.services.jurisdiction_disposition import discretionary_award_fact_key

    assert discretionary_award_fact_key(SA) == f"evidenced_program_fact:{SA}__discretionary_award_confirmed"


def test_a_stored_award_confirmation_is_read_not_ignored():
    row = _row()
    annotate_rows([row])
    key = f"evidenced_program_fact:{SA}__discretionary_award_confirmed"
    enrich_row_with_program_detail(row, SA, {key: "true"}, "feature_film")
    assert row["blocker_detail"]["unresolved_propositions"][0]["stored_value"] == "true"


def test_program_maximum_potential_is_ceiling_times_qpe_never_guaranteed():
    p = build_program_maximum_potential(program_name="SA", ceiling_rate=0.6, qpe_usd=3_701_238.0, gross_budget_usd=4_517_687.0)
    assert p["confirmed_incentive_floor_usd"] == 0.0 and p["confirmed_npc_usd"] is None
    assert p["maximum_supported_incentive_usd"] == pytest.approx(2_220_742.8)
    assert p["potential_npc_usd"] == pytest.approx(4_517_687.0 - 2_220_742.8)
    assert p["ceiling_status"] == CEILING_CONDITIONAL and p["economics_certainty"] == "CONDITIONAL"
    assert "NOT guaranteed" in p["ceiling_basis"]["note"]


def test_program_maximum_potential_honours_cap_minimum_and_missing_inputs():
    capped = build_program_maximum_potential(program_name="X", ceiling_rate=0.5, qpe_usd=10_000_000.0,
                                             gross_budget_usd=12_000_000.0, per_project_cap_usd=1_000_000.0)
    assert capped["maximum_supported_incentive_usd"] == 1_000_000.0 and capped["ceiling_basis"]["legs"][0]["cap_applied"] is True
    below = build_program_maximum_potential(program_name="X", ceiling_rate=0.5, qpe_usd=100.0, gross_budget_usd=1_000.0, min_qpe_usd=500.0)
    assert below["ceiling_status"] == CEILING_NOT_ESTABLISHED and below["maximum_supported_incentive_usd"] is None
    none = build_program_maximum_potential(program_name="X", ceiling_rate=None, qpe_usd=1.0, gross_budget_usd=1.0)
    assert none["ceiling_status"] == CEILING_NOT_ESTABLISHED


# ── Mandatory thresholds are hard blocks with the exact numbers; fact-dependent tiers stay amber ───────────────
def test_minimum_qpe_not_reached_is_a_hard_block_with_exact_numbers_and_fact_dependent_tiers_stay_amber():
    es = _row()
    annotate_rows([es])
    enrich_row_with_program_detail(
        es, "es_tax_credit_foreign", {}, "feature_film", qpe_usd=825_505.0,
        threshold_unreachable_reason="requires at least $1,140,523.96 of qualifying spend; this production's canonical qualifying spend is $825,505.00.",
    )
    assert es["disposition"] == HARD_BLOCK and "1,140,523.96" in es["hard_block_reason"] and es["missing_facts_reason"] is None
    nl = _row()
    annotate_rows([nl])
    enrich_row_with_program_detail(nl, "nl_film_production_incentive", {}, "feature_film", qpe_usd=3_700_000.0)
    assert nl["disposition"] == NEEDS_FACTS
    assert {p["fact_key"] for p in nl["blocker_detail"]["unresolved_propositions"]} >= {"nl_nfpi_points_independence_test_passed"}


# ── Content / censorship / cultural gates ────────────────────────────────────────────────────────────────────
def test_saudi_content_gates_come_from_the_canonical_profile_and_are_unresolved_not_inferred():
    gates = {g["kind"]: g for g in content_gates_for_program(SA)}
    assert KIND_SCRIPT_CONTENT_CLEARANCE in gates and KIND_FILMING_NON_OBJECTION in gates
    assert gates[KIND_SCRIPT_CONTENT_CLEARANCE]["category"] == CONFIRMED_MANDATORY
    for g in gates.values():
        assert g["status"] == "NOT_ON_FILE" and g["effect"] == "NEEDS_FACTS", "missing approval is amber, never red"
        assert g["consumed_by_optimizer"] is False, "present in the registry but not evaluated by pricing -- disclosed honestly"


def test_only_an_explicit_refusal_is_a_hard_effect_and_a_confirmation_clears_the_gate():
    key = "evidenced_program_fact:" + gate_fact_key(SA, KIND_SCRIPT_CONTENT_CLEARANCE)
    assert {g["kind"]: g["effect"] for g in content_gates_for_program(SA, {key: "refused"})}[KIND_SCRIPT_CONTENT_CLEARANCE] == "HARD_BLOCK"
    assert {g["kind"]: g["status"] for g in content_gates_for_program(SA, {key: "true"})}[KIND_SCRIPT_CONTENT_CLEARANCE] == "CONFIRMED"


def test_no_content_profile_never_discards_or_infers_a_failure():
    assert content_gates_for_program("not_a_program") == [] and content_gates_for_program(None) == []
    assert ADVISORY == "ADVISORY_BUSINESS_RISK"


def test_content_gate_census_is_derived_from_the_registry_and_discloses_unconsumed_gates():
    inv = content_gate_inventory()
    assert inv["gates_total"] == inv["gates_consumed_by_optimizer"] + inv["gates_present_but_not_consumed"]
    assert inv["gates_consumed_by_optimizer"] >= 1 and inv["gates_present_but_not_consumed"] > inv["gates_consumed_by_optimizer"]
    assert inv["programs_with_content_related_gates"] <= inv["programs_with_requirements_profile"]


# ── Globe coordinate coverage ───────────────────────────────────────────────────────────────────────────────────
def test_every_two_letter_accounted_jurisdiction_has_a_globe_coordinate():
    from app.calculators import jurisdiction_comparison as jc
    from app.data import global_inventory as gi
    from app.data.executable_jurisdiction_registry import all_doctrine_records

    js = (Path(__file__).resolve().parents[2] / "frontend/src/lib/jurisdictions.js").read_text()
    have = set(re.findall(r'^\s*"?([A-Za-z][A-Za-z0-9 \-]*)"?:\s*\{\s*lat', js, re.M))
    universe = {p.jurisdiction_code for p in gi.ALL_PROGRAMS} | set(jc.ALL_PROFILES) | {r.jurisdiction_code for r in all_doctrine_records()}
    missing = sorted(c for c in universe if len(c) == 2 and c not in have and c != "EU")  # EU: supranational aggregate, not a place
    assert missing == [], f"accounted ISO jurisdictions without a Globe coordinate: {missing}"
