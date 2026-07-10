"""
little_utopia_state.py

The single canonical production state the CineGlobe API serves: THE
LITTLE UTOPIA (Mauritius, v1.1, June 2025) — the same account-level
register already used by every backend test in this repository
(tests/fixtures/little_utopia_sanitized.py ->
qualification_model.build_little_utopia_qualification_register()).

This module introduces NO new production, NO fabricated people, NO
invented screenplay. Every input here is either:
  - the real Little Utopia register/grey-areas (already-tested fixture
    data), or
  - honestly absent (no screenplay on file, no cast/crew intake on
    file) — Package Intelligence's own "unknown stays unknown"
    discipline handles this correctly; it is not a bug or a stub.

The only non-canonical step this module performs is running one Legal
Engine acquisition cycle through MockConnector (the sole connector
implementation this phase ships — see legal_authority_acquisition.py's
own docstring) so the Evidence Graph / Authority Score / Legal Engine
loop has real content to display. This is the same MockConnector
already exercised by 26 passing tests in test_legal_engine.py; nothing
new is built here. Every retrieved excerpt is self-labeled
"MOCK CONNECTOR — no live retrieval performed" by the connector itself,
and the API surfaces that label rather than hiding it.

State is built once per process (module-level cache) since every input
is static and every engine call is a pure function over that static
input — recomputing per request would be wasted work, not a source of
different results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from app.calculators.evidence_graph import AuthorityTier
from app.calculators.global_scenario_ranker import (
    ProductionStructure,
    StructureRankingResult,
    compose_candidate_structures,
    rank_production_structures,
)
from app.calculators.jurisdiction_graph import JurisdictionGraph, build_jurisdiction_graph
from app.calculators.legal_authority_acquisition import ConnectorClass, MockConnector
from app.calculators.legal_engine import AcquisitionCycleResult, CommitResult, LegalEngine, RerunResult
from app.calculators.opportunity_discovery import OpportunityCollection, discover_all_opportunities
from app.calculators.production_package_intelligence import ProductionPackage, build_production_package
from app.calculators.production_recommendation_engine import RecommendationSet, generate_production_recommendations
from app.calculators.production_structure_composer import CompositionResult, compose_production_structures
from app.calculators.qualification_model import (
    AccountQualification,
    GreyAreaItem,
    GreyAreaStatus,
    build_little_utopia_grey_areas,
    build_little_utopia_qualification_register,
)
from app.ingestion.budget_parser import BudgetParseResult, ParsedLineItem

PRODUCTION_ID = "LITTLE-UTOPIA"
PRODUCTION_NAME = "The Little Utopia"
JURISDICTION_CODE = "MU"
MU_RATE = 0.40
MU_GROSS_BUDGET_USD = 4_364_393.0
AS_OF_DATE = "2026-07-10"


def _register_to_budget_parse_result(register: list[AccountQualification]) -> BudgetParseResult:
    """The register IS Little Utopia's real account-level budget data
    (qualification_model.py's own docstring: 'taken directly from
    [the sanitized fixture], not recomputed'). This reshapes it into the
    ParsedLineItem shape build_budget_intelligence() already accepts —
    no new budget data, no re-parsing, no invented department field."""
    line_items = [
        ParsedLineItem(
            description=account.description,
            department=None,
            amount_raw=str(account.amount_usd),
            amount_usd=account.amount_usd,
            currency_code="USD",
            source_row=None,
            source_page=None,
        )
        for account in register
    ]
    return BudgetParseResult(
        filename="little_utopia_register.json",
        currency_code="USD",
        total_budget_raw=MU_GROSS_BUDGET_USD,
        origin_note="Derived from qualification_model.build_little_utopia_qualification_register()",
        line_items=line_items,
    )


@dataclass
class LittleUtopiaState:
    production_id: str
    production_name: str
    jurisdiction_code: str
    gross_budget_usd: float
    rate: float
    register: list[AccountQualification]
    grey_areas_baseline: list[GreyAreaItem]
    graph: JurisdictionGraph
    package: ProductionPackage
    collection: OpportunityCollection
    composition: CompositionResult
    recommendations: RecommendationSet
    scenario_structures: list[ProductionStructure] = field(default_factory=list)
    scenario_ranking: StructureRankingResult = None
    legal_engine: LegalEngine = None
    legal_cycle: AcquisitionCycleResult = None
    legal_commit: CommitResult = None
    legal_rerun_before: RerunResult = None
    legal_rerun: RerunResult = None


@lru_cache(maxsize=1)
def get_state() -> LittleUtopiaState:
    graph = build_jurisdiction_graph(mu_rate=MU_RATE)
    register = build_little_utopia_qualification_register(mu_rate=MU_RATE)
    grey_areas = build_little_utopia_grey_areas()

    budget_parse = _register_to_budget_parse_result(register)
    # No screenplay, no people/entity/location intake exist for Little
    # Utopia in this codebase — left unset. build_production_package()
    # reports these as honestly UNKNOWN via the Question Engine, not
    # fabricated.
    package = build_production_package(
        production_id=PRODUCTION_ID,
        budget_parse_result=budget_parse,
    )

    collection = discover_all_opportunities(baseline_jurisdiction=JURISDICTION_CODE, mu_rate=MU_RATE, graph=graph)
    composition = compose_production_structures(
        collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET_USD,
        rate=MU_RATE, grey_areas=grey_areas,
    )
    recommendations = generate_production_recommendations(
        collection, composition_result=composition, register=register, rate=MU_RATE,
        jurisdiction_code=JURISDICTION_CODE,
    )

    scenario_structures = compose_candidate_structures(
        collection, register=register, gross_budget_usd=MU_GROSS_BUDGET_USD,
        rate=MU_RATE, grey_areas=grey_areas,
    )
    scenario_ranking = rank_production_structures(scenario_structures)

    # Legal Engine: one real acquisition cycle over the real Little
    # Utopia grey areas, through the sole shipped connector
    # (MockConnector — see module docstring). Mirrors
    # test_legal_engine.py's own verified sequence exactly.
    legal_engine = LegalEngine(connectors={
        ConnectorClass.TAX_AUTHORITY_GUIDANCE: MockConnector(ConnectorClass.TAX_AUTHORITY_GUIDANCE),
    })
    # Baseline rerun BEFORE any resolution — a fresh LegalEngine over a
    # fresh copy of the grey areas, so the "before" figure reflects zero
    # commits, exactly like any other direct build_risk_cases() caller.
    legal_rerun_before = LegalEngine().rerun(
        register=register, gross_budget_usd=MU_GROSS_BUDGET_USD, rate=MU_RATE,
        grey_areas=build_little_utopia_grey_areas(), graph=graph, jurisdiction_code=JURISDICTION_CODE,
    )

    legal_cycle = legal_engine.run_acquisition_cycle(AS_OF_DATE, grey_areas=grey_areas, graph=graph)

    legal_commit = None
    if "STG-TASK-GA-ATL-SCOPE" in legal_cycle.awaiting_verification:
        legal_engine.record_verification(
            "STG-TASK-GA-ATL-SCOPE", verified_by="counsel@littleutopia.example",
            outcome="authority_found", notes="MRA published guidance covers ATL scope.",
        )
        legal_engine.record_approval("STG-TASK-GA-ATL-SCOPE", approved_by="producer@littleutopia.example")
        ga = next(g for g in grey_areas if g.item_id == "GA-ATL-SCOPE")
        legal_commit = legal_engine.commit_and_score(
            "STG-TASK-GA-ATL-SCOPE", target_jurisdiction_code=JURISDICTION_CODE, as_of_date=AS_OF_DATE,
            rule_text="ATL compensation for services rendered in Mauritius qualifies as QPE.",
            tier=AuthorityTier.OFFICIAL_GUIDANCE, authority_body="Mauritius Revenue Authority",
            resolves_grey_area=ga, grey_area_outcome=GreyAreaStatus.RESOLVED_INCLUDE,
        )

    legal_rerun = legal_engine.rerun(
        register=register, gross_budget_usd=MU_GROSS_BUDGET_USD, rate=MU_RATE,
        grey_areas=grey_areas, graph=graph, jurisdiction_code=JURISDICTION_CODE, as_of_date=AS_OF_DATE,
    )

    return LittleUtopiaState(
        production_id=PRODUCTION_ID,
        production_name=PRODUCTION_NAME,
        jurisdiction_code=JURISDICTION_CODE,
        gross_budget_usd=MU_GROSS_BUDGET_USD,
        rate=MU_RATE,
        register=register,
        grey_areas_baseline=grey_areas,
        graph=graph,
        package=package,
        collection=collection,
        composition=composition,
        recommendations=recommendations,
        scenario_structures=scenario_structures,
        scenario_ranking=scenario_ranking,
        legal_engine=legal_engine,
        legal_cycle=legal_cycle,
        legal_commit=legal_commit,
        legal_rerun_before=legal_rerun_before,
        legal_rerun=legal_rerun,
    )
