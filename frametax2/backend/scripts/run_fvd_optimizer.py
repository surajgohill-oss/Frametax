import json
import os

from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.data.program_spend_rules import get_program_doctrine
from app.calculators.production_discovery import discover_executable_jurisdictions
from app.calculators.production_requirements import ProductionRequirements
from app.calculators.production_allocation import StructureSpec, derive_account_allocation, MOVABLE_COMPONENTS
from app.calculators.allocation_pricing import price_allocated_structure, rank_allocated_structures
from app.calculators.production_normalization import compute_travel_normalization, compute_fx_normalization, TravelInputs, FXInputs, FXRateSource, TravelPricingMode

def main():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "validation", "SCRIPT_ANALYZER_REAL_BUDGET_FIXTURE_001.json")
    with open(fixture_path) as f:
        data = json.load(f)
    
    oi_data = data["optimizer_input"]["optimizer_input"]
    gross_budget_usd = oi_data["gross_production_cost_usd"]
    
    lines = []
    category_by_code = {}
    for bl in oi_data["budget_lines"]:
        ac = bl["line_id"]
        lines.append(BudgetLine(
            account_code=ac,
            description=bl["description"],
            amount_usd=bl["amount_usd"],
            spend_category=bl["spend_category"],
            is_memo=False
        ))
        category_by_code[ac] = bl["spend_category"]

    facts = ProductionFacts(jurisdiction_code="MU", accounts_outside_jurisdiction=set(), offshore_payroll_accounts=set())
    mu_rate = 0.40
    doctrine = get_program_doctrine("mu_edb_incentive")
    register = derive_qualification_register(
        line_items=lines,
        program_slug="mu_edb_incentive",
        facts=facts,
        rate=mu_rate,
        doctrine=doctrine
    )

    reqs = ProductionRequirements(
        environments=frozenset(),
        infrastructure=frozenset(),
        required_capabilities=frozenset(),
        evidence={}
    )
    discovery = discover_executable_jurisdictions(
        requirements=reqs,
        production_type="feature_film",
        qpe_usd=gross_budget_usd * 0.5,
        home_code="MU"
    )
    alts = discovery.accepted_alternatives("MU")
    
    specs = []
    specs.append(StructureSpec(
        structure_id="ALLOC-BASELINE-MU",
        structure_type="single_country",
        label="Baseline: MU",
        primary_jurisdiction="MU",
        participants=("MU",),
        incentive_programs={"MU": "mu_edb_incentive"}
    ))

    for code, slug in alts:
        specs.append(StructureSpec(
            structure_id=f"ALLOC-RELOC-{code}",
            structure_type="full_relocation",
            label=f"Full Relocation: {code}",
            primary_jurisdiction=code,
            participants=(code,),
            incentive_programs={code: slug}
        ))
        
        specs.append(StructureSpec(
            structure_id=f"ALLOC-COMPONENT-POST-{code}",
            structure_type="component_relocation",
            label=f"Component Reloc (Post): {code}",
            primary_jurisdiction="MU",
            participants=("MU", code),
            incentive_programs={"MU": "mu_edb_incentive", code: slug},
            component_routes={c: code for c in MOVABLE_COMPONENTS}
        ))
        
        specs.append(StructureSpec(
            structure_id=f"ALLOC-TREATY-{code}",
            structure_type="treaty_coproduction",
            label=f"Treaty: MU + {code}",
            primary_jurisdiction="MU",
            participants=("MU", code),
            incentive_programs={"MU": "mu_edb_incentive", code: slug}
        ))

    travel_inputs = TravelInputs(
        origin_city="LA", business_travelers=1, economy_travelers=0,
        rotations_per_year=4, hotel_nights=14, per_diem_days=14,
        pricing_mode=TravelPricingMode.BENCHMARK_ESTIMATE
    )
    budgeted_travel = sum(l.amount_usd for l in lines if category_by_code.get(l.account_code) == "travel_and_living")
    fx_inputs = FXInputs(rate_source=FXRateSource.LIVE, scenario_fx_delta_pct=0.0)

    pricings = []
    for spec in specs:
        allocation = derive_account_allocation(
            lines=lines,
            spend_category_by_code=category_by_code,
            spec=spec,
            stated_outside_accounts=set(),
            stated_location_authority={},
            routing_rationales={}
        )
        travel = compute_travel_normalization(
            spec.primary_jurisdiction, travel_inputs, budgeted_travel, "MU"
        )
        pricing = price_allocated_structure(
            spec=spec, allocation=allocation,
            spend_category_by_code=category_by_code,
            offshore_payroll_accounts=set(),
            gross_budget_usd=gross_budget_usd,
            travel_incremental_delta_usd=travel.incremental_delta_usd,
            fx_delta_usd=None,
            inkind_replacement_delta_usd=0.0,
            contingency_allocations={}
        )
        if pricing.is_fully_priced:
            fx = compute_fx_normalization(spec.primary_jurisdiction, fx_inputs, pricing.npc_verified_usd)
            pricing = price_allocated_structure(
                spec=spec, allocation=allocation,
                spend_category_by_code=category_by_code,
                offshore_payroll_accounts=set(),
                gross_budget_usd=gross_budget_usd,
                travel_incremental_delta_usd=travel.incremental_delta_usd,
                fx_delta_usd=fx.delta_usd if fx else 0.0,
                fx_basis={
                    "jurisdiction_code": fx.jurisdiction_code,
                    "local_currency": fx.local_currency,
                    "rate_used": fx.rate_used,
                    "rate_source": fx.rate_source,
                    "rate_date": fx.rate_date,
                    "note": fx.note,
                } if fx else None,
                inkind_replacement_delta_usd=0.0,
                contingency_allocations={}
            )
        pricings.append(pricing)

    ranks = rank_allocated_structures(pricings)
    
    generated_count = len(specs)
    priced_count = sum(1 for p in pricings if p.is_fully_priced)
    rejected_count = generated_count - priced_count
    
    baseline = next(p for p in pricings if p.structure_id == "ALLOC-BASELINE-MU")
    baseline_npc = baseline.npc_with_adjustments_usd
    
    priced_ranks = [r for r in ranks if r["rank"] is not None]
    top_10 = priced_ranks[:10]
    best = priced_ranks[0] if priced_ranks else None
    
    reasons = {}
    for p in pricings:
        if not p.is_fully_priced:
            for b in p.blockers:
                reasons[b] = reasons.get(b, 0) + 1
                
    output = {
        "generated_candidates": generated_count,
        "priced_candidates": priced_count,
        "rejected_candidates": rejected_count,
        "baseline_actual_production_structure": "ALLOC-BASELINE-MU",
        "gross_production_cost": gross_budget_usd,
        "baseline_qualifying_spend": next(s for s in baseline.segments if s.jurisdiction_code == "MU").qpe_usd,
        "baseline_incentive": next(s for s in baseline.segments if s.jurisdiction_code == "MU").incentive_floor_usd,
        "baseline_adjusted_incentive": next(s for s in baseline.segments if s.jurisdiction_code == "MU").incentive_floor_usd,
        "baseline_npc": baseline_npc,
        "winning_structure": best["structure_id"] if best else None,
        "winning_npc": best["npc_with_adjustments_usd"] if best else None,
        "savings_vs_base": baseline_npc - best["npc_with_adjustments_usd"] if best else 0,
        "top_10_structures": [r["structure_id"] for r in top_10],
        "important_rejected_candidate_reasons": reasons
    }
    
    out_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "validation", "SCRIPT_ANALYZER_SA1_5_REAL_PROJECT_ACCEPTANCE.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Done. Wrote to {out_path}")

if __name__ == "__main__":
    main()
