"""
run_full_analysis.py

Orchestrates all deterministic calculator modules for a single production structure.
Inputs are plain dicts (ORM models serialized by the service layer).
Output is a fully-traced StructureAnalysisResult.

No LLM calls. All math is in downstream modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.calculators.apply_caps_floors_exclusions import apply_caps_and_exclusions
from app.calculators.apply_fx_rates import convert_to_usd
from app.calculators.apply_union_fringe_rules import apply_union_fringes
from app.calculators.calculate_incentive_value import calculate_incentive_value
from app.calculators.calculate_net_budget import calculate_key_crew_travel, calculate_net_budget
from app.calculators.calculate_qualified_spend import calculate_qualified_spend
from app.calculators.calculate_risk_adjusted_net_budget import calculate_risk_adjusted_net
from app.calculators.classify_budget_line_items import classify_atl_btl_split
from app.calculators.evaluate_legal_stacking import evaluate_legal_stacking
from app.calculators.evaluate_qualification_tests import score_qualification_test
from app.calculators.rank_production_structures import RankedStructure, rank_structures

ENGINE_VERSION = "0.1.0"


@dataclass
class StructureAnalysisResult:
    structure_id: str
    jurisdiction_id: str
    jurisdiction_name: str

    # Budget split
    fixed_atl_usd: float
    variable_btl_usd: float
    post_usd: float
    other_usd: float
    total_input_budget_usd: float

    # Qualified spend per program
    qualified_spend_results: list[dict]

    # Incentive values per program
    incentive_results: list[dict]
    total_incentive_economic_value_usd: float

    # Net budget
    rebase_btl_usd: float
    travel_cost_usd: float
    true_net_cost_usd: float
    savings_vs_no_incentive_usd: float

    # Risk
    risk_adjusted_net_cost_usd: float
    risk_level: str
    risk_discounts_applied: list[dict]

    # Legal stacking
    stacking_legal_review_required: bool
    stacking_violations: list[dict]
    stacking_conditionals: list[dict]

    # Qualification test scores
    qualification_scores: list[dict]

    # Calculation trace (full dict for audit)
    calculation_trace: dict

    engine_version: str = ENGINE_VERSION


def run_full_analysis(
    structure_id: str,
    jurisdiction: dict,
    line_items: list[dict],
    programs_with_categories: list[dict],
    # ^^ list of {program: IncentiveProgram dict,
    #              qualifying_categories: [QualifyingSpendCategory dicts],
    #              uplifts: [ProgramUplift dicts],
    #              jurisdiction_spend_pct: float}
    stacking_rules: list[dict],
    qualification_tests_with_rules: list[dict],
    # ^^ list of {test: QualificationTest dict, rules: [QualificationTestRule dicts]}
    cost_benchmark: dict | None,
    union_fringe_rules: list[dict],
    fx_rates: dict | None,
    production_details: dict | None,
    home_jurisdiction_id: str | None = None,
    shooting_days: int = 20,
    key_crew_count: int = 12,
    daily_travel_usd: float = 0.0,
) -> StructureAnalysisResult:
    """
    Run the full deterministic analysis for a production structure.

    Parameters
    ----------
    structure_id            UUID of the ProductionStructure record
    jurisdiction            Jurisdiction-shaped dict for this structure's filming location
    line_items              BudgetLineItem-shaped dicts (description, amount_usd, etc.)
    programs_with_categories  Each entry bundles a program with its qualifying categories,
                              uplifts, and the assumed jurisdiction_spend_pct for that program
    stacking_rules          LegalStackingRule dicts for any pair of claimed programs
    qualification_tests_with_rules  Each entry bundles a test with its scoring rules
    cost_benchmark          LocalCostBenchmark dict for this jurisdiction (or None)
    union_fringe_rules      UnionFringeRule dicts (empty list = no fringes)
    fx_rates                {currency_code: rate_vs_USD} (or None = no conversion needed)
    production_details      Arbitrary details dict for uplift/qualification conditions
    home_jurisdiction_id    Project's home jurisdiction (travel = 0 if same)
    """
    production_details = production_details or {}
    fx_rates = fx_rates or {}
    trace: dict = {"steps": []}

    def _trace(step: str, data: dict) -> None:
        trace["steps"].append({"step": step, **data})

    # -------------------------------------------------------------------------
    # Step 1: Classify line items
    # -------------------------------------------------------------------------
    classification = classify_atl_btl_split(line_items)
    fixed_atl_usd = classification["totals"]["fixed_atl_usd"]
    variable_btl_usd = classification["totals"]["variable_btl_usd"]
    post_usd = classification["totals"]["post_total_usd"]
    other_usd = classification["totals"]["other_total_usd"]
    total_input = fixed_atl_usd + variable_btl_usd + post_usd + other_usd
    classified_items = classification["classified_items"]

    _trace("classify_budget", {
        "fixed_atl_usd": fixed_atl_usd,
        "variable_btl_usd": variable_btl_usd,
        "post_usd": post_usd,
        "other_usd": other_usd,
        "total_input_usd": total_input,
    })

    # -------------------------------------------------------------------------
    # Step 2: Apply union fringes to labor items
    # -------------------------------------------------------------------------
    labor_items = [i for i in classified_items if i.get("is_labor")]
    fringed_labor = apply_union_fringes(labor_items, union_fringe_rules)
    _trace("apply_union_fringes", {
        "gross_labor_usd": fringed_labor.gross_labor_usd,
        "total_fringe_usd": fringed_labor.total_fringe_usd,
        "fully_loaded_labor_usd": fringed_labor.fully_loaded_labor_usd,
    })

    # -------------------------------------------------------------------------
    # Step 3: FX conversion (if jurisdiction currency != USD)
    # -------------------------------------------------------------------------
    jurisdiction_currency = jurisdiction.get("currency_code", "USD")
    if jurisdiction_currency != "USD" and fx_rates:
        rate = fx_rates.get(jurisdiction_currency)
        if rate:
            fixed_atl_usd = convert_to_usd(fixed_atl_usd, jurisdiction_currency, fx_rates).target_amount
            variable_btl_usd = convert_to_usd(variable_btl_usd, jurisdiction_currency, fx_rates).target_amount
            _trace("fx_conversion", {
                "from_currency": jurisdiction_currency,
                "rate_to_usd": rate,
            })

    # -------------------------------------------------------------------------
    # Step 4: Apply incentive programs
    # -------------------------------------------------------------------------
    qualified_spend_results: list[dict] = []
    incentive_results: list[dict] = []
    total_incentive_economic_value = 0.0

    for entry in programs_with_categories:
        program = entry["program"]
        qualifying_categories = entry.get("qualifying_categories", [])
        uplifts = entry.get("uplifts", [])
        jurisdiction_spend_pct = float(entry.get("jurisdiction_spend_pct", 1.0))
        prog_id = str(program.get("id", ""))

        # 4a. Calculate qualifying spend
        qs_result = calculate_qualified_spend(
            line_items=classified_items,
            qualifying_categories=qualifying_categories,
            jurisdiction_spend_pct=jurisdiction_spend_pct,
            program_id=prog_id,
            program_slug=program.get("slug", ""),
            spend_cap_pct=program.get("spend_cap_pct"),
            total_budget_usd=total_input,
        )
        qualified_spend_results.append({
            "program_id": prog_id,
            "program_slug": program.get("slug"),
            "qualifying_spend_usd": qs_result.total_qualifying_capped_usd,
            "cap_applied": qs_result.cap_applied,
            "cap_description": qs_result.cap_description,
            "category_breakdown": qs_result.category_breakdown,
        })

        # 4b. Apply caps and exclusions
        capped = apply_caps_and_exclusions(
            qualifying_spend_usd=qs_result.total_qualifying_capped_usd,
            total_budget_usd=total_input,
            atl_spend_usd=fixed_atl_usd,
            atl_cap_pct=program.get("atl_cap_pct"),
            individual_salary_cap_usd=program.get("individual_salary_cap_usd"),
            individual_high_earners=production_details.get("high_earners"),
            program_annual_cap_usd=float(program["annual_cap_local"]) if program.get("annual_cap_local") else None,
        )

        # 4c. Calculate incentive economic value
        cb = qs_result.category_breakdown
        iv_result = calculate_incentive_value(
            qualifying_spend_usd=capped.adjusted_qualifying_spend_usd,
            program=program,
            uplifts=uplifts,
            production_details=production_details,
            vfx_spend_usd=float(cb.get("vfx", 0.0)),
            music_spend_usd=float(cb.get("music", 0.0)),
            resident_labor_usd=float(cb.get("btl_resident_labor", 0.0)),
        )
        iv_dict = iv_result.__dict__.copy()
        iv_dict["confidence_tier"] = program.get("confidence_tier", "DISCOVERY")
        iv_dict["is_competitive"] = program.get("is_competitive", False)
        incentive_results.append(iv_dict)
        total_incentive_economic_value += iv_result.economic_value_usd

    _trace("incentive_programs", {
        "programs_evaluated": len(programs_with_categories),
        "total_incentive_economic_value_usd": total_incentive_economic_value,
    })

    # -------------------------------------------------------------------------
    # Step 5: Net budget
    # -------------------------------------------------------------------------
    jurisdiction_id = str(jurisdiction.get("id", ""))
    travel_cost = calculate_key_crew_travel(
        jurisdiction_id=jurisdiction_id,
        home_jurisdiction_id=home_jurisdiction_id or jurisdiction_id,
        shooting_days=shooting_days,
        key_crew_count=key_crew_count,
        daily_travel_usd=daily_travel_usd,
    )

    net_result = calculate_net_budget(
        fixed_atl_usd=fixed_atl_usd,
        variable_btl_usd=variable_btl_usd,
        cost_benchmark=cost_benchmark,
        travel_cost_usd=travel_cost,
        total_incentive_economic_value_usd=total_incentive_economic_value,
    )
    _trace("net_budget", net_result.__dict__)

    # -------------------------------------------------------------------------
    # Step 6: Risk-adjusted net
    # -------------------------------------------------------------------------
    risk_result = calculate_risk_adjusted_net(
        true_net_cost_usd=net_result.true_net_cost_usd,
        total_incentive_value_usd=total_incentive_economic_value,
        program_results=incentive_results,
        has_qualification_gaps=False,
    )
    _trace("risk_adjusted", risk_result.__dict__)

    # -------------------------------------------------------------------------
    # Step 7: Legal stacking check
    # -------------------------------------------------------------------------
    claimed_program_ids = [str(e["program"].get("id", "")) for e in programs_with_categories]
    stacking_result = evaluate_legal_stacking(
        claimed_program_ids=claimed_program_ids,
        stacking_rules=stacking_rules,
    )
    _trace("legal_stacking", {
        "legal_review_required": stacking_result.legal_review_required,
        "violation_count": len(stacking_result.violations),
    })

    # -------------------------------------------------------------------------
    # Step 8: Qualification tests
    # -------------------------------------------------------------------------
    qualification_scores: list[dict] = []
    for entry in qualification_tests_with_rules:
        test = entry["test"]
        rules = entry.get("rules", [])
        score = score_qualification_test(
            test_rules=rules,
            production_details=production_details,
            minimum_pass_points=int(test.get("minimum_pass_points", 0)),
            section_minimums=test.get("section_minimums_json"),
            test_slug=test.get("slug", "unknown"),
            total_available_points=test.get("total_available_points"),
        )
        qualification_scores.append(score.__dict__)
    _trace("qualification_tests", {"tests_scored": len(qualification_tests_with_rules)})

    trace["engine_version"] = ENGINE_VERSION
    trace["structure_id"] = structure_id

    return StructureAnalysisResult(
        structure_id=structure_id,
        jurisdiction_id=jurisdiction_id,
        jurisdiction_name=jurisdiction.get("name", ""),
        fixed_atl_usd=fixed_atl_usd,
        variable_btl_usd=variable_btl_usd,
        post_usd=post_usd,
        other_usd=other_usd,
        total_input_budget_usd=total_input,
        qualified_spend_results=qualified_spend_results,
        incentive_results=incentive_results,
        total_incentive_economic_value_usd=total_incentive_economic_value,
        rebase_btl_usd=net_result.rebase_btl_usd,
        travel_cost_usd=travel_cost,
        true_net_cost_usd=net_result.true_net_cost_usd,
        savings_vs_no_incentive_usd=net_result.savings_vs_no_incentive_usd,
        risk_adjusted_net_cost_usd=risk_result.risk_adjusted_net_cost_usd,
        risk_level=risk_result.overall_risk_level,
        risk_discounts_applied=risk_result.risk_adjustments,
        stacking_legal_review_required=stacking_result.legal_review_required,
        stacking_violations=[v.__dict__ for v in stacking_result.violations],
        stacking_conditionals=[c.__dict__ for c in stacking_result.conditionals],
        qualification_scores=qualification_scores,
        calculation_trace=trace,
    )


def rank_multiple_structures(analyses: list[StructureAnalysisResult]) -> list[RankedStructure]:
    """Convert StructureAnalysisResult list to ranked RankedStructure list."""
    score_inputs = [
        {
            "structure_id": a.structure_id,
            "name": a.jurisdiction_name,
            "true_net_cost_usd": a.true_net_cost_usd,
            "risk_adjusted_net_cost_usd": a.risk_adjusted_net_cost_usd,
            "total_incentive_value_usd": a.total_incentive_economic_value_usd,
            "optimization_opportunities": [],
        }
        for a in analyses
    ]
    return rank_structures(score_inputs)
