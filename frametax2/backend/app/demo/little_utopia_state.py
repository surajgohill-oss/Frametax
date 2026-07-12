"""
little_utopia_state.py

The single canonical production state the CineGlobe API serves: THE
LITTLE UTOPIA (Mauritius, v1.1, June 2025) — the same account-level
register already used by every backend test in this repository
(tests/fixtures/little_utopia_sanitized.py ->
qualification_model.build_little_utopia_qualification_register()).

This module introduces NO new production, NO fabricated people, NO
invented screenplay. Every input here is either:
  - the real Little Utopia budget/facts/grey-areas (already-tested
    fixture data),
  - a production fact the user has explicitly supplied through the
    facts API (apply_fact_answers), or
  - honestly absent (no screenplay on file, no cast/crew intake on
    file) — Package Intelligence's own "unknown stays unknown"
    discipline handles this correctly; it is not a bug or a stub.

Engine Integration Phase 1 changes the flow from "hardcoded register ->
optimizer" to the designed chain:

    production facts (defaults + user answers)
      -> derived qualification register (qualification_derivation)
      -> Legal Engine acquisition/commit cycle
      -> post-resolution register (apply_resolutions — the same
         qualification_model.apply_grey_area_resolution reclassification
         the Legal Engine has always owned)
      -> ONE opportunity-discovery + composition + recommendation +
         scenario-ranking pass over the POST-RESOLUTION register
      -> API

so /structures, /recommendations, and /scenarios all serve the same
evidence state /legal reports, instead of a stale pre-resolution
composition.

The only non-canonical step this module performs is running one Legal
Engine acquisition cycle through MockConnector (the sole connector
implementation this phase ships — see legal_authority_acquisition.py's
own docstring) so the Evidence Graph / Authority Score / Legal Engine
loop has real content to display. Every retrieved excerpt is
self-labeled "MOCK CONNECTOR — no live retrieval performed" by the
connector itself, and the API surfaces that label rather than hiding it.

State is built once per fact-state (module-level cache, cleared whenever
a fact answer changes) since every input is static between answers and
every engine call is a pure function over that input.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from functools import lru_cache

from app.calculators import jurisdiction_comparison as jc
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
from app.calculators.qualification_derivation import ProductionFacts
from app.calculators.qualification_model import (
    LITTLE_UTOPIA_ACCOUNTS_OUTSIDE_MU,
    LITTLE_UTOPIA_OFFSHORE_PAYROLL,
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


# ── Production facts (Seam B: Question Engine answers are engine inputs) ────
#
# Each answerable fact maps to (a) a ProductionFacts field consumed by
# qualification derivation or structure composition, and (b) the Question
# Engine missing-input it answers — so an answered question stops being
# asked AND changes the engines' inputs. Facts not answered stay at the
# production's real current defaults; nothing is fabricated.

ANSWERABLE_FACTS: dict[str, dict] = {
    "payroll_routing_localized": {
        "type": bool,
        "answers_question": "MISSING-PAYROLL-STRUCTURE",
        "description": (
            "Is cast/crew payroll routed through a local employer-of-record / "
            "production SPV in the baseline jurisdiction? true = local routing "
            "plan in place; false = current offshore routing stands."
        ),
    },
    "post_work_in_jurisdiction": {
        "type": bool,
        "answers_question": None,
        "description": (
            "Will post-production (edit/grade/sound/music/VFX/deliverables) be "
            "performed in the baseline jurisdiction? Overrides the current "
            "known post location for the post spend categories."
        ),
    },
    "treaty_partner_code": {
        "type": str,
        "answers_question": "MISSING-TREATY-PARTNER",
        "description": (
            "Elected co-production treaty partner country (ISO alpha-2). Adds "
            "that jurisdiction set to structure composition."
        ),
    },
}

_fact_answers: dict[str, object] = {}


def apply_fact_answers(answers: dict[str, object]) -> None:
    """Record user-supplied production facts and invalidate the cached
    state so every engine recomputes from them. A value of None clears a
    previously-given answer (the fact returns to 'unknown/default')."""
    for key, value in answers.items():
        spec = ANSWERABLE_FACTS.get(key)
        if spec is None:
            raise ValueError(
                f"'{key}' is not an answerable production fact. "
                f"Answerable: {sorted(ANSWERABLE_FACTS)}."
            )
        if value is None:
            _fact_answers.pop(key, None)
            continue
        if not isinstance(value, spec["type"]):
            raise ValueError(
                f"Fact '{key}' expects {spec['type'].__name__}, got {type(value).__name__}."
            )
        if key == "treaty_partner_code":
            code = str(value).upper()
            if code == JURISDICTION_CODE or code not in jc.ALL_PROFILES:
                raise ValueError(
                    f"'{code}' is not a modeled partner jurisdiction "
                    f"(known: {sorted(c for c in jc.ALL_PROFILES if c != JURISDICTION_CODE)})."
                )
            value = code
        _fact_answers[key] = value
    _build_state.cache_clear()


def current_fact_answers() -> dict[str, object]:
    return dict(_fact_answers)


def reset_fact_answers() -> None:
    _fact_answers.clear()
    _build_state.cache_clear()


def _production_facts() -> ProductionFacts:
    """The production's real current facts, overlaid with any answers the
    user has supplied through the facts API."""
    return ProductionFacts(
        jurisdiction_code=JURISDICTION_CODE,
        accounts_outside_jurisdiction=LITTLE_UTOPIA_ACCOUNTS_OUTSIDE_MU,
        offshore_payroll_accounts=LITTLE_UTOPIA_OFFSHORE_PAYROLL,
        post_work_in_jurisdiction=_fact_answers.get("post_work_in_jurisdiction"),
        payroll_routing_localized=_fact_answers.get("payroll_routing_localized"),
        treaty_partner_code=_fact_answers.get("treaty_partner_code"),
    )


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
    fact_answers: dict = field(default_factory=dict)
    scenario_structures: list[ProductionStructure] = field(default_factory=list)
    scenario_ranking: StructureRankingResult = None
    legal_engine: LegalEngine = None
    legal_cycle: AcquisitionCycleResult = None
    legal_commit: CommitResult = None
    legal_rerun_before: RerunResult = None
    legal_rerun: RerunResult = None


def get_state() -> LittleUtopiaState:
    """Current state under the current fact answers. Cached per
    fact-state; apply_fact_answers()/reset_fact_answers() invalidate."""
    return _build_state(tuple(sorted(_fact_answers.items())))


@lru_cache(maxsize=4)
def _build_state(_fact_key: tuple) -> LittleUtopiaState:
    facts = _production_facts()
    graph_default = build_jurisdiction_graph(mu_rate=MU_RATE)  # facts-independent world model

    # Facts -> derived qualification register (Seam A+B).
    register = build_little_utopia_qualification_register(mu_rate=MU_RATE, facts=facts)
    grey_areas = build_little_utopia_grey_areas()
    graph = build_jurisdiction_graph(mu_rate=MU_RATE, register=register)

    budget_parse = _register_to_budget_parse_result(register)
    # No screenplay, no people/entity/location intake exist for Little
    # Utopia in this codebase — left unset. build_production_package()
    # reports these as honestly UNKNOWN via the Question Engine, not
    # fabricated.
    package = build_production_package(
        production_id=PRODUCTION_ID,
        budget_parse_result=budget_parse,
    )
    # Seam B: an answered fact resolves its question — the answer is now
    # an engine input above, so the question is no longer open.
    answered_question_ids = {
        spec["answers_question"]
        for key, spec in ANSWERABLE_FACTS.items()
        if key in _fact_answers and spec["answers_question"]
    }
    if answered_question_ids:
        package = dataclasses.replace(
            package,
            missing_inputs=tuple(
                m for m in package.missing_inputs if m.identifier not in answered_question_ids
            ),
        )

    # HINT-MOVABLE-SPEND is production_package_intelligence.py's own
    # already-computed figure for routable (VFX/music/sound/post/creative
    # fee) spend not physically tied to the shoot location — reused
    # as-is, not recomputed, so opportunity discovery's relocation
    # candidates can price a real jurisdiction-specific upside instead
    # of leaving it uncomputed.
    movable_hint = next(
        (h for h in package.budget.opportunity_hints if h.category == "movable_spend"), None,
    )
    movable_spend_usd = movable_hint.amount_usd if movable_hint else None

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
        grey_areas=build_little_utopia_grey_areas(), graph=graph_default,
        jurisdiction_code=JURISDICTION_CODE,
    )

    legal_cycle = legal_engine.run_acquisition_cycle(AS_OF_DATE, grey_areas=grey_areas, graph=graph_default)

    legal_commit = None
    if "STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT" in legal_cycle.awaiting_verification:
        legal_engine.record_verification(
            "STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", verified_by="counsel@littleutopia.example",
            outcome="authority_found", notes="Production accounting provided an itemized breakdown "
                                              "of accounts 70-00/71-00.",
        )
        legal_engine.record_approval("STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", approved_by="producer@littleutopia.example")
        ga = next(g for g in grey_areas if g.item_id == "GA-LEGAL-ACCOUNTING-SPLIT")
        legal_commit = legal_engine.commit_and_score(
            "STG-TASK-GA-LEGAL-ACCOUNTING-SPLIT", target_jurisdiction_code=JURISDICTION_CODE, as_of_date=AS_OF_DATE,
            rule_text="The accounting/audit portion of accounts 70-00/71-00 qualifies as QPE "
                      "under 'Professional services (such as insurance and accounting services)'.",
            tier=AuthorityTier.OFFICIAL_GUIDANCE, authority_body="Mauritius Revenue Authority",
            resolves_grey_area=ga, grey_area_outcome=GreyAreaStatus.RESOLVED_INCLUDE,
        )

    legal_rerun = legal_engine.rerun(
        register=register, gross_budget_usd=MU_GROSS_BUDGET_USD, rate=MU_RATE,
        grey_areas=grey_areas, graph=graph_default, jurisdiction_code=JURISDICTION_CODE,
        as_of_date=AS_OF_DATE,
    )

    # Seam C: the CANONICAL pipeline pass runs over the POST-RESOLUTION
    # register — the same qualification_model.apply_grey_area_resolution
    # reclassification the Legal Engine has always applied, now actually
    # served by /structures, /recommendations, and /scenarios instead of
    # being computed and discarded.
    register_final, greys_final = legal_engine.apply_resolutions(register, grey_areas)

    collection = discover_all_opportunities(
        baseline_jurisdiction=JURISDICTION_CODE, mu_rate=MU_RATE, graph=graph,
        movable_spend_usd=movable_spend_usd,
        register=register_final, grey_areas=greys_final,
    )

    # Seam B: an elected treaty partner is an engine input to structure
    # composition (an extra jurisdiction set), not a display string.
    extra_sets: list[tuple[str, ...]] = []
    if facts.treaty_partner_code:
        extra_sets.append((JURISDICTION_CODE, facts.treaty_partner_code))

    composition = compose_production_structures(
        collection, graph, register=register_final, gross_budget_usd=MU_GROSS_BUDGET_USD,
        rate=MU_RATE, grey_areas=greys_final,
        extra_jurisdiction_sets=extra_sets or None,
    )
    recommendations = generate_production_recommendations(
        collection, composition_result=composition, register=register_final, rate=MU_RATE,
        jurisdiction_code=JURISDICTION_CODE,
    )

    scenario_structures = compose_candidate_structures(
        collection, register=register_final, gross_budget_usd=MU_GROSS_BUDGET_USD,
        rate=MU_RATE, grey_areas=greys_final,
    )
    scenario_ranking = rank_production_structures(scenario_structures)

    return LittleUtopiaState(
        production_id=PRODUCTION_ID,
        production_name=PRODUCTION_NAME,
        jurisdiction_code=JURISDICTION_CODE,
        gross_budget_usd=MU_GROSS_BUDGET_USD,
        rate=MU_RATE,
        register=register_final,
        grey_areas_baseline=greys_final,
        graph=graph,
        package=package,
        collection=collection,
        composition=composition,
        recommendations=recommendations,
        fact_answers=current_fact_answers(),
        scenario_structures=scenario_structures,
        scenario_ranking=scenario_ranking,
        legal_engine=legal_engine,
        legal_cycle=legal_cycle,
        legal_commit=legal_commit,
        legal_rerun_before=legal_rerun_before,
        legal_rerun=legal_rerun,
    )
