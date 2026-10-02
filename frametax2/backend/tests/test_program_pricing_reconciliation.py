"""Four-project program pricing reconciliation (2026-10-02). DB-free: registries + the shared owners."""
from __future__ import annotations

import dataclasses

import pytest

from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.data.authority_coverage_registry import _B1_DISCRETIONARY_RULING, coverage_state, economic_block_for_program
from app.data.program_rate_rules import _RULES_BY_PROGRAM, get_rate_rules, resolve_program_rate
from app.services.jurisdiction_disposition import annotate_rows, enrich_row_with_program_detail
from app.services.program_pricing_crosswalk import (
    APPROVED_CAUSES, CAUSE_THRESHOLD, CAUSE_UNATTRIBUTED, T_DETERMINISTIC, T_DISCRETIONARY, T_MECHANICS_INCOMPLETE,
    T_PROVENANCE, T_SUPERSEDED_NA, TREATMENTS, all_program_treatments, build_single_jurisdiction_contract,
    program_treatment, reconcile_project_differences,
)
from app.services.scenario_local_labour import apply_scenario_crew_inference, inferred_crew_resident_pct

SA = "sa_film_commission_rebate"
REMOVED_FROM_B1 = (
    "ae_ad_film_rebate", "al_cash_rebate", "be_tax_shelter", "ch_pics_national_rebate", "de_dfff", "dk_production_rebate",
    "eg_empc_cashback", "gh_film_tax_incentive", "il_foreign_production_fund", "in_national_film", "pa_film_rebate",
    "ph_fdcp_flip", "qa_screen_production_incentive", "us_wa_mpcp", "uy_acau_cash_rebate",
)


# ── crosswalk: exactly one treatment per rate-bearing program ──────────────────────────────────────────────────────
def test_every_rate_bearing_program_has_exactly_one_treatment():
    rows = all_program_treatments()
    assert len(rows) == len(_RULES_BY_PROGRAM) and len({r["program_slug"] for r in rows}) == len(rows)
    assert {r["treatment"] for r in rows} <= set(TREATMENTS)


def test_control_programs_land_in_the_expected_treatment():
    assert program_treatment(SA)["treatment"] == T_DISCRETIONARY
    assert program_treatment("us_tx_miip")["treatment"] == T_DISCRETIONARY            # ceiling-only, no guaranteed floor
    assert program_treatment("ca_sk_creative_saskatchewan_grant")["treatment"] == T_DISCRETIONARY
    assert program_treatment("cz_film_incentive_animation")["treatment"] == T_SUPERSEDED_NA   # production-type exclusion
    assert program_treatment("ae_dxb_dpip")["treatment"] == T_SUPERSEDED_NA                   # superseded
    assert program_treatment("kz_investment_subsidy")["treatment"] == T_MECHANICS_INCOMPLETE
    assert program_treatment("al_cash_rebate")["treatment"] == T_PROVENANCE                  # PARSED, priceable, warning only
    assert program_treatment("us_tn_performance_grant")["treatment"] == T_DETERMINISTIC      # formulaic, VERIFIED


# ── repaired central blocking ───────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("slug", REMOVED_FROM_B1)
def test_floor_supported_programs_are_no_longer_blocked_and_price_their_floor(slug):
    """A supported guaranteed floor prices even when a higher tier is conditional (two-axis rule)."""
    assert slug not in _B1_DISCRETIONARY_RULING and economic_block_for_program(slug) is None
    rules = get_rate_rules(slug)
    floors = [r for r in rules if not r.is_band_ceiling]
    assert floors, "a guaranteed floor tier exists"
    assert not any(c.kind in ("discretionary_band", "material_funding_risk_not_modeled") for c in floors[0].conditions) or slug in ("eg_empc_cashback",)


def test_what_remains_in_the_b1_ruling_is_genuinely_discretionary_or_has_no_rate_rule():
    for slug, cls in _B1_DISCRETIONARY_RULING.items():
        rules = get_rate_rules(slug)
        if not rules:
            continue
        assert program_treatment(slug)["treatment"] == T_DISCRETIONARY, slug


def test_alias_spelling_never_changes_economic_treatment():
    assert [r.rate for r in get_rate_rules("sa_sfc_rebate")] == [r.rate for r in get_rate_rules(SA)] == [0.6]
    assert economic_block_for_program("sa_sfc_rebate").classification == economic_block_for_program(SA).classification


# ── Saudi recurrence control ────────────────────────────────────────────────────────────────────────────────────────
def test_saudi_verified_60_percent_potential_survives_any_authority_block_or_alias():
    t = program_treatment(SA)
    assert t["treatment"] == T_DISCRETIONARY and t["supported_maximum_rate"] == 0.6
    assert t["authority_block"] == "DISPLAY_ONLY_ZERO_GUARANTEED" and t["minimum_spend_usd"] == 200_000.0
    for slug in (SA, "sa_sfc_rebate"):                      # canonical and alias spelling
        row = {"candidate_status": "RULE_REJECTED", "rejection_reason_class": "STATUTORY_CONDITIONS_UNMET", "reason": "x"}
        annotate_rows([row])
        enrich_row_with_program_detail(row, slug, {}, "feature_film")
        assert row["blocker_detail"]["potential_ceiling_rate"] == 0.6, slug
        assert row["blocker_detail"]["reconciliation_class"] == "DISCRETIONARY_AWARD_ZERO_GUARANTEED"
        assert row["blocker_detail"]["guaranteed_floor"].startswith("none")
    # the block keeps the confirmed floor at zero: the resolver refuses to price it
    assert resolve_program_rate(SA, "feature_film", 5_000_000.0, 6_000_000.0) is None


def test_saudi_conditional_alternative_leads_potential_but_never_confirmed():
    ledger = {
        "jurisdictions": [{"jurisdiction_code": "SA", "disposition": "NEEDS_FACTS", "first_exit_stage": "AUTHORITY_BLOCKED"},
                          {"jurisdiction_code": "GR", "disposition": "EXECUTABLE", "first_exit_stage": "PRICED"}],
        "rows": [{"primary_jurisdiction": "SA", "disposition": "NEEDS_FACTS", "program_slug": SA,
                  "incentive_potential": {"confirmed_incentive_floor_usd": 0.0, "maximum_supported_incentive_usd": 2_220_742.8,
                                          "potential_npc_usd": 2_296_944.2, "economics_certainty": "CONDITIONAL"},
                  "blocker_detail": {"unresolved_propositions": [{"description": "award confirmation"}], "provenance_axis": "x"}}],
    }
    bpj = {"GR": {"primary_jurisdiction": "GR", "confirmed_npc_usd": 3_183_389.9, "confirmed_incentive_floor_usd": 1_000_000.0,
                  "potential_npc_usd": 3_000_000.0, "maximum_supported_incentive_usd": 1_100_000.0, "economics_certainty": "CONDITIONAL"}}
    out = {r["jurisdiction_code"]: r for r in build_single_jurisdiction_contract(ledger, bpj)}
    assert out["SA"]["category"] == "CONDITIONAL_ALTERNATIVE" and out["SA"]["potential_rank"] == 1
    assert out["SA"]["confirmed_rank"] is None and out["SA"]["confirmed_npc_usd"] is None
    assert out["GR"]["confirmed_rank"] == 1 and out["GR"]["category"] == "LEADING_ALTERNATIVE"
    assert out["SA"]["missing_conditions"] == ["award confirmation"]


# ── SCENARIO local-BTL default ──────────────────────────────────────────────────────────────────────────────────────
def _lines():
    return [
        BudgetLine("1100", "Director", 100_000.0, "atl_director"),
        BudgetLine("1200", "Cast", 300_000.0, "atl_cast"),
        BudgetLine("2100", "Grip crew", 200_000.0, "btl_nonresident_labor"),
        BudgetLine("2200", "Camera crew", 200_000.0, "btl_crew_labor"),
    ]


def test_relocated_btl_is_local_by_default_and_a_project_override_restores_non_local():
    from app.services.canonical_project_economics import ProjectEconomicInputs, production_facts_for

    lines = _lines()
    src = [dataclasses.replace(l) for l in lines]
    base = ProjectEconomicInputs(
        project_id="p", project_name="n", jurisdiction_code="GR", production_type="feature_film", gross_budget_usd=900_000.0,
        leaf_account_sum_usd=900_000.0, budget_lines=lines, spend_category_by_code={}, accounts_outside_jurisdiction=frozenset(),
        offshore_payroll_accounts=frozenset({"2100"}),
    )
    for dest in ("US-TX", "CA-SK"):                                   # identical behaviour across jurisdictions
        assert production_facts_for(base, jurisdiction_code=dest).scenario_local_btl is True
    assert production_facts_for(base, jurisdiction_code="GR").scenario_local_btl is False   # the home jurisdiction is not a scenario
    override = dataclasses.replace(base, scenario_btl_nonlocal=True)
    assert production_facts_for(override, jurisdiction_code="US-TX").scenario_local_btl is False
    assert lines == src, "the source budget is never rewritten"


def test_routed_offshore_btl_payroll_is_cleared_for_btl_only_and_cast_stays_unchanged():
    f_local = ProductionFacts(jurisdiction_code="US-TX", offshore_payroll_accounts=frozenset({"2100", "1200"}), scenario_local_btl=True)
    f_src = ProductionFacts(jurisdiction_code="US-TX", offshore_payroll_accounts=frozenset({"2100", "1200"}), scenario_local_btl=False)
    assert f_src.routed_offshore("2100", "btl_crew_labor") is True and f_local.routed_offshore("2100", "btl_crew_labor") is False
    assert f_local.routed_offshore("1200", "atl_cast") is True, "cast residency is a separate fact, never defaulted local"
    assert f_local.work_outside("2100", "btl_crew_labor") is False


def test_nonresident_btl_category_is_treated_resident_only_under_the_scenario_default():
    rules_slug = next(s for s in _RULES_BY_PROGRAM if s)  # any program: the category mapping is what is asserted
    kw = dict(program_slug=rules_slug, rate=0.0)
    reg_local = derive_qualification_register(_lines(), facts=ProductionFacts(jurisdiction_code="US-TX", scenario_local_btl=True), **kw)
    reg_src = derive_qualification_register(_lines(), facts=ProductionFacts(jurisdiction_code="US-TX", scenario_local_btl=False), **kw)
    assert len(reg_local) == len(reg_src) == 4
    assert [a.amount_usd for a in reg_local] == [a.amount_usd for a in reg_src], "amounts (source residency) are untouched"


def test_texas_crew_percentage_is_inferred_from_btl_while_cast_stays_unresolved():
    pct = inferred_crew_resident_pct(_lines())
    assert pct == 100.0                                              # BTL crew is locally hired; cast excluded; ATL separately evidenced
    assert inferred_crew_resident_pct([BudgetLine("1100", "Director", 1.0, "atl_director")]) is None
    row = {"candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "rejection_reason_class": "PRICING_BLOCKED", "reason": "x"}
    annotate_rows([row])
    enrich_row_with_program_detail(row, "us_tx_miip", {}, "feature_film")
    detail = apply_scenario_crew_inference(row["blocker_detail"], _lines())
    keys = {p["fact_key"] for p in detail["unresolved_propositions"]}
    assert "us_tx_miip_resident_crew_pct" not in keys, "inferred >= 35% under the scenario default"
    assert "us_tx_miip_resident_cast_pct" in keys and "us_tx_miip_award_confirmed" in keys and "us_tx_miip_awarded_rate_pct" in keys
    assert detail["scenario_assumptions"][0]["fact_key"] == "us_tx_miip_resident_crew_pct"
    assert detail["scenario_assumptions"][0]["inferred_value"] == 100.0


def test_a_stored_producer_value_always_wins_over_the_inference():
    row = {"candidate_status": "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "rejection_reason_class": "PRICING_BLOCKED", "reason": "x"}
    annotate_rows([row])
    enrich_row_with_program_detail(row, "us_tx_miip", {"amount_fact:us_tx_miip_resident_crew_pct": "10"}, "feature_film")
    detail = apply_scenario_crew_inference(row["blocker_detail"], _lines())
    assert "scenario_assumptions" not in detail
    assert any(p["fact_key"] == "us_tx_miip_resident_crew_pct" and p["stored_value"] == "10" for p in detail["unresolved_propositions"])


# ── four-project difference reconciliation ──────────────────────────────────────────────────────────────────────────
def _rec(code, slug, disposition, stage, reason=""):
    return {"jurisdiction_code": code, "program_slug": slug, "disposition": disposition, "stage": stage, "exit_reason": reason}


def test_every_cross_project_difference_names_one_approved_cause_and_unattributed_ones_are_flagged():
    L = {
        "A": {"programs": [_rec("US-NY", "ny_post", "HARD_BLOCK", "CONDITIONS_UNMET", "requires at least $1,000,000 of qualifying spend"),
                           _rec("SA", SA, "NEEDS_FACTS", "AUTHORITY_BLOCKED", "x")]},
        "B": {"programs": [_rec("US-NY", "ny_post", "EXECUTABLE", "PRICED"), _rec("SA", SA, "NEEDS_FACTS", "AUTHORITY_BLOCKED", "x")]},
    }
    diffs = reconcile_project_differences(L, production_types={"A": "feature_film", "B": "feature_film"})
    assert [d["program_slug"] for d in diffs] == ["ny_post"] and diffs[0]["cause"] == CAUSE_THRESHOLD and diffs[0]["cause"] in APPROVED_CAUSES
    L["B"]["programs"][1] = _rec("SA", SA, "EXECUTABLE", "PRICED")
    bad = {d["program_slug"]: d for d in reconcile_project_differences(L, production_types={"A": "feature_film", "B": "feature_film"})}
    assert bad[SA]["cause"] == CAUSE_UNATTRIBUTED and bad[SA]["attributed"] is False


def test_cultural_and_composition_differences_are_attributed():
    from app.services.program_pricing_crosswalk import CAUSE_COMPOSITION, CAUSE_CULTURAL

    L = {"A": {"programs": [_rec("CA", "ca_federal_cptc", "HARD_BLOCK", "CONDITIONS_UNMET", "A mandatory qualification gate failed (HARD_FAIL).")]},
         "B": {"programs": [_rec("CA", "ca_federal_cptc", "EXECUTABLE", "PRICED")]}}
    d = reconcile_project_differences(L, production_types={"A": "feature_film", "B": "feature_film"})
    assert d[0]["cause"] == CAUSE_CULTURAL
    ocase = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
    L2 = {"A": {"programs": [_rec("CA-ON", ocase, "NEEDS_FACTS", "PRICING_BLOCKED", "needs project facts")]},
          "B": {"programs": [_rec("CA-ON", ocase, "EXECUTABLE", "PRICED")]}}
    d2 = reconcile_project_differences(L2, production_types={"A": "feature_film", "B": "feature_film"},
                                       category_spend={"A": {"btl_crew_labor": 5.0}, "B": {"vfx": 9.0}})
    assert d2[0]["cause"] == CAUSE_COMPOSITION and d2[0]["attributed"]


def test_contract_carries_names_and_never_labels_a_production_type_exclusion_not_suitable():
    ledger = {"programs": [{"jurisdiction_code": "CZ", "jurisdiction_name": "Czech Republic"}],
              "jurisdictions": [{"jurisdiction_code": "CZ", "disposition": "NOT_APPLICABLE", "first_exit_stage": "NOT_APPLICABLE"}],
              "rows": [{"primary_jurisdiction": "CZ", "disposition": "NOT_APPLICABLE", "program_slug": "x", "program_name": "Czech Animation"}]}
    r = build_single_jurisdiction_contract(ledger, {})[0]
    assert r["category"] == "UNAVAILABLE" and r["jurisdiction_name"] == "Czech Republic" and r["program_name"] == "Czech Animation"
    assert r["headline"] == "Not applicable to this production type."
