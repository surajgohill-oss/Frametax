"""
run_production_demo.py

End-to-end CineGlobe backend demonstration on a previously unseen
production package ("Coral Kingdom" — a marine adventure feature).

Chain demonstrated, every arrow an existing engine:

    Production Package
      -> Package Intelligence        (production_package_intelligence)
      -> Budget Intelligence          (classify_budget_line_items reuse)
      -> Script Intelligence          (screenplay_parser reuse)
      -> Creative Qualification       (creative_qualification_engine)
      -> Opportunity Discovery        (opportunity_discovery)
      -> Production Structure Composer(production_structure_composer)
      -> Recommendation Engine        (production_recommendation_engine)
      -> Scenario Ranker              (global_scenario_ranker)
      -> Optimizer                    (optimization_engine.build_risk_cases)
      -> Constraint filter            (production_constraint_engine)
      -> Legal Engine                 (legal_engine: detect -> acquire ->
                                       verify -> commit -> score -> rerun)

Run:  .venv/bin/python scripts/run_production_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.calculators.creative_qualification_engine import analyze_creative_qualification_paths
from app.calculators.evidence_graph import AuthorityTier
from app.calculators.global_scenario_ranker import compose_candidate_structures, rank_production_structures
from app.calculators.jurisdiction_graph import build_jurisdiction_graph
from app.calculators.legal_authority_acquisition import ConnectorClass, MockConnector
from app.calculators.legal_engine import LegalEngine
from app.calculators.opportunity_discovery import discover_all_opportunities
from app.calculators.optimization_engine import RiskCase
from app.calculators.production_constraint_engine import (
    ConstraintKind,
    ProductionConstraint,
    build_constraint_set,
    filter_candidates_by_constraints,
)
from app.calculators.production_package_intelligence import (
    CrewMovementIntake,
    EntityIntake,
    LocationIntake,
    LocationRole,
    PersonIntake,
    PersonRole,
    build_production_package,
    production_package_to_cultural_test_inputs,
    production_package_to_relevant_cultural_test_slugs,
)
from app.calculators.production_recommendation_engine import (
    RecommendationCategory,
    generate_production_recommendations,
)
from app.calculators.production_structure_composer import compose_production_structures
from app.calculators.qualification_model import (
    GreyAreaStatus,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
)
from app.ingestion.budget_parser import parse_budget_csv
from app.ingestion.screenplay_parser import parse_screenplay_text

MU_RATE = 0.40
MU_GROSS_BUDGET = 4_364_393.0
AS_OF = "2026-07-10"

BUDGET_CSV = """description,amount,department
Director fee,220000,ATL
Writer fee,90000,ATL
Producer fee,180000,ATL
Lead cast fee,350000,ATL
Underlying rights option,45000,ATL
Crew labor,780000,PRODUCTION
Resident labor local hire,410000,PRODUCTION
Camera rental,140000,GRIP
Marine unit vessel charter,260000,MARINE
Underwater camera housing,55000,MARINE
Stage rental,120000,STAGES
Location fees,95000,LOCATIONS
Set construction,210000,ART
Transportation,88000,TRANSPO
Catering,72000,CATERING
Travel airfare,130000,TRAVEL
Hotel and lodging,160000,TRAVEL
VFX shots,420000,POST
Sound mix,85000,POST
Music score composer,95000,POST
Editing and color grade,110000,POST
Payroll fringes,240000,PAYROLL
Insurance,65000,OTHER
Completion bond,54393,OTHER
Contingency,175000,OTHER
"""

SCRIPT_TEXT = """INT. RESEARCH VESSEL - GALLEY - DAY
DR. AMARA KEMP studies coral samples under lamplight.

EXT. INDIAN OCEAN REEF - UNDERWATER - DAY
A kaleidoscope of fish scatter as a shadow passes overhead.

EXT. PORT LOUIS HARBOR - DUSK
The vessel eases into its berth. AMARA watches the shore.

INT. MARINE INSTITUTE - LAB - NIGHT
Rows of tanks glow. TEO, the institute director, waits.
"""


def hr(title: str) -> None:
    print()
    print("=" * 74)
    print(title)
    print("=" * 74)


def main() -> None:
    # ── 1. Production Package -> Package / Budget / Script Intelligence ──
    hr("1. PRODUCTION PACKAGE INTELLIGENCE — 'Coral Kingdom'")
    budget_parse = parse_budget_csv(BUDGET_CSV, filename="coral_kingdom_budget.csv")
    script_parse = parse_screenplay_text(SCRIPT_TEXT, filename="coral_kingdom.fdx")

    package = build_production_package(
        production_id="CORAL-KINGDOM",
        budget_parse_result=budget_parse,
        screenplay_parse_result=script_parse,
        script_known_attributes={
            "language": "English", "marine_usage": "extensive", "underwater": "yes",
            "setting": "Indian Ocean / Mauritius", "period_classification": "contemporary",
        },
        people=[
            PersonIntake(person_id="P1", name="Camille Roux", role=PersonRole.DIRECTOR, nationality="FR"),
            PersonIntake(person_id="P2", name="Dev Naidoo", role=PersonRole.WRITER),  # nationality unknown
            PersonIntake(person_id="P3", name="Anna Kemp", role=PersonRole.CAST, residency="GB",
                         residency_verification_required=True),
        ],
        production_companies=[EntityIntake(entity_id="E1", name="Reef Line Pictures",
                                           entity_type="production_company", registered_jurisdiction="FR")],
        vendors=[EntityIntake(entity_id="V1", name="Lagoon VFX", entity_type="vfx_vendor")],
        locations=[
            LocationIntake(location_id="L1", role=LocationRole.PRINCIPAL_PHOTOGRAPHY, jurisdiction_code="MU"),
            LocationIntake(location_id="L2", role=LocationRole.VFX),  # jurisdiction open
            LocationIntake(location_id="L3", role=LocationRole.POST, jurisdiction_code="FR"),
        ],
        crew_movements=[CrewMovementIntake(movement_id="M1", home_base="LA", destination_jurisdiction="MU",
                                           business_class_seats=2, hotel_nights=45, per_diem_days=45)],
    )
    print(f"budget: {package.budget.line_item_count} items, "
          f"ATL ${package.budget.atl_total_usd:,.0f} / BTL ${package.budget.btl_total_usd:,.0f} / "
          f"POST ${package.budget.post_total_usd:,.0f}")
    print(f"budget opportunity hints: {len(package.budget.opportunity_hints)}")
    for h in package.budget.opportunity_hints[:4]:
        print(f"  - {h.hint_id}: {h.description[:88]}")
    print(f"script locations: {package.script.locations_mentioned}")
    print(f"missing inputs (question engine): {len(package.missing_inputs)} "
          f"({len(package.blocking_missing_inputs)} blocking)")
    for m in package.missing_inputs[:4]:
        print(f"  - {m.identifier} [{'BLOCKING' if m.blocking else 'open'}]: {m.question[:70]}")

    # ── 2. Creative Qualification ────────────────────────────────────────
    hr("2. CREATIVE QUALIFICATION")
    slugs = production_package_to_relevant_cultural_test_slugs(package)
    inputs = production_package_to_cultural_test_inputs(package)
    print(f"relevant cultural tests (derived from known jurisdictions): {slugs}")
    for slug in slugs:
        if slug in inputs:
            analysis = analyze_creative_qualification_paths(slug, inputs[slug])
            status = "PASSES" if analysis.currently_passes else "does not pass yet"
            print(f"  {slug}: {status}; "
                  f"minimal paths: {[p.criterion_codes for p in analysis.lowest_impact_paths[:3]]}; "
                  f"non-creative alternative: {analysis.has_non_creative_alternative}")

    # ── 3-5. Discovery -> Composer -> Recommendations ────────────────────
    hr("3. OPPORTUNITY DISCOVERY -> 4. STRUCTURE COMPOSER -> 5. RECOMMENDATIONS")
    graph = build_jurisdiction_graph(mu_rate=MU_RATE)
    register = build_little_utopia_qualification_register(mu_rate=MU_RATE)
    grey_areas = build_little_utopia_grey_areas()
    collection = discover_all_opportunities(baseline_jurisdiction="MU", mu_rate=MU_RATE, graph=graph)
    print(f"opportunities discovered: {len(collection.opportunities)}")

    composition = compose_production_structures(
        collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET,
        rate=MU_RATE, grey_areas=grey_areas,
    )
    print(f"candidate structures composed: {len(composition.candidates)} (pruned: {len(composition.pruned)})")

    recommendations = generate_production_recommendations(
        collection, composition_result=composition, register=register, rate=MU_RATE,
        jurisdiction_code="MU", cultural_test_inputs=inputs, relevant_cultural_test_slugs=slugs,
    )
    print(f"recommendations: {len(recommendations.recommendations)} total")
    for cat in RecommendationCategory:
        subset = recommendations.of_category(cat)
        print(f"  {cat.value}: {len(subset)}")
    print("top 3 by rank score:")
    for r in recommendations.recommendations[:3]:
        print(f"  - {r.recommendation_id}: {r.title[:64]} (${r.estimated_value_usd:,.0f})"
              if r.estimated_value_usd else f"  - {r.recommendation_id}: {r.title[:64]}")

    # ── 6. Scenario Ranker + Optimizer ───────────────────────────────────
    hr("6. SCENARIO RANKER + OPTIMIZER")
    structures = compose_candidate_structures(
        collection, register=register, gross_budget_usd=MU_GROSS_BUDGET,
        rate=MU_RATE, grey_areas=grey_areas,
    )
    ranking = rank_production_structures(structures)
    for rank in ranking.ranks[:5]:
        npc = f"${rank.risk_adjusted_npc_usd:,.2f}" if rank.risk_adjusted_npc_usd else "unpriced"
        print(f"  #{rank.rank} {rank.label}: Risk-Adjusted NPC = {npc}")
    best = ranking.best()
    print(f"best priceable structure: {best.label}")

    # ── 7. Constraint filter ─────────────────────────────────────────────
    hr("7. PRODUCTION CONSTRAINTS")
    constraints = build_constraint_set([
        ProductionConstraint(constraint_id="C1", kind=ConstraintKind.JURISDICTION_REQUIRED, value="MU"),
        ProductionConstraint(constraint_id="C2", kind=ConstraintKind.DIRECTOR_FIXED, value="Camille Roux"),
    ])
    compatible, checks = filter_candidates_by_constraints(composition.candidates, constraints)
    print(f"candidates compatible with producer constraints: {len(compatible)}/{len(composition.candidates)}")
    print(f"unverifiable constraints surfaced honestly: "
          f"{sorted(set(sum((list(c.unverifiable_constraint_ids) for c in checks), [])))}")

    # ── 8. Legal Engine: full authority acquisition loop ─────────────────
    hr("8. LEGAL ENGINE — automatic uncertainty -> authority -> rerun")
    engine = LegalEngine(connectors={
        ConnectorClass.TAX_AUTHORITY_GUIDANCE: MockConnector(ConnectorClass.TAX_AUTHORITY_GUIDANCE),
    })
    cycle = engine.run_acquisition_cycle(AS_OF, grey_areas=grey_areas, graph=graph)
    print(f"legal questions auto-detected: {len(cycle.questions)}")
    print(f"auto-executed (commitment-grade w/ connector): {cycle.executed_task_ids}")
    print(f"scenario-grade held per policy: {len([q for q in cycle.questions if not q.auto_executable]) - 0}")
    print(f"staged awaiting human verification: {cycle.awaiting_verification}")

    sid = "STG-TASK-GA-ATL-SCOPE"
    engine.record_verification(sid, verified_by="counsel@reefline.example", outcome="authority_found",
                               notes="MRA published guidance covers ATL scope.")
    engine.record_approval(sid, approved_by="producer@reefline.example")
    ga = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
    commit = engine.commit_and_score(
        sid, target_jurisdiction_code="MU", as_of_date=AS_OF,
        rule_text="ATL compensation for services rendered in Mauritius qualifies as QPE.",
        tier=AuthorityTier.OFFICIAL_GUIDANCE, authority_body="Mauritius Revenue Authority",
        resolves_grey_area=ga, grey_area_outcome=GreyAreaStatus.RESOLVED_INCLUDE,
    )
    print(f"committed: {commit.committed_id} | Authority Score: {commit.score.composite} "
          f"({commit.score.confidence.value})")

    trace = engine.evidence_graph.trace_rule(commit.committed_id)
    link = trace[0]
    print("evidence trace: Rule -> Evidence -> Citation -> "
          f"{link['authority_source'].title} [{link['authority_source'].tier.name}] -> "
          f"{link['document'].title} ({link['document_version'].retrieved_date})")

    baseline_engine = LegalEngine()
    before = baseline_engine.rerun(register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE,
                                   grey_areas=build_little_utopia_grey_areas(), graph=graph)
    after = engine.rerun(register=register, gross_budget_usd=MU_GROSS_BUDGET, rate=MU_RATE,
                         grey_areas=grey_areas, graph=graph, as_of_date=AS_OF)
    b = before.optimization.cases[RiskCase.CONSERVATIVE].net_production_cost_usd
    a = after.optimization.cases[RiskCase.CONSERVATIVE].net_production_cost_usd
    print(f"Conservative NPC before resolution: ${b:,.2f}")
    print(f"Conservative NPC after resolution:  ${a:,.2f}  (improvement ${b - a:,.2f})")

    # ── 9. Final worldwide recommendation + genuine grey areas ───────────
    hr("9. FINAL RECOMMENDATION")
    final_best = after.composition.candidates[0]
    print(f"best structure: {final_best.label} "
          f"(Risk-Adjusted NPC ${final_best.npc(RiskCase.RISK_ADJUSTED):,.2f}, "
          f"priceable {final_best.priceable_pct:.0%})")
    print(f"gross budget: ${MU_GROSS_BUDGET:,.0f} | incentive rate: {MU_RATE:.0%}")
    remaining = [g for g in after.grey_areas_used if g.status == GreyAreaStatus.OPEN]
    print(f"remaining genuine grey areas: {[g.item_id for g in remaining]}")
    for g in remaining:
        print(f"  - {g.item_id}: ${g.amount_usd:,.0f} at stake | ask: {g.authority_to_ask[:60]} "
              f"| LAAE task: TASK-{g.item_id}")
    print(f"authority scores on committed rules: "
          f"{ {k: v.composite for k, v in after.authority_scores.items()} }")
    print()
    print("END-TO-END CHAIN COMPLETE.")


if __name__ == "__main__":
    main()
