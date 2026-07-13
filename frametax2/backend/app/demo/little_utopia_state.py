"""
little_utopia_state.py

The single canonical production state the CineGlobe API serves: THE
LITTLE UTOPIA (Mauritius). The register is built from the ACTUAL parsed
production budget (app.data.little_utopia_real_budget ->
qualification_model.build_little_utopia_real_register()) — not the
sanitized fixture (tests/fixtures/little_utopia_sanitized.py ->
build_little_utopia_qualification_register()), which remains a distinct,
still-tested capability but is no longer the primary served data.

This module introduces NO new production, NO fabricated people, NO
invented screenplay. Every input here is either:
  - the real, parsed Little Utopia budget/facts/grey-areas (see
    app.data.little_utopia_real_budget's own docstring for exactly how
    to reproduce the parse from the source PDF),
  - a production fact the user has explicitly supplied through the
    facts API (apply_fact_answers), or
  - honestly absent (no screenplay on file, no cast/crew intake on
    file) — Package Intelligence's own "unknown stays unknown"
    discipline handles this correctly; it is not a bug or a stub.

The flow (Engine Integration Phase 1, with the mock-contamination
regression fix restoring the original primary/research separation):

    production facts (defaults + user answers)
      -> derived qualification register (qualification_derivation)
      -> ONE opportunity-discovery + composition + recommendation +
         scenario-ranking pass over the RAW statutory register
      -> API (primary production surfaces)

    SEPARATELY, research-only:
      -> Legal Engine acquisition/commit cycle over ITS OWN copy of the
         grey areas (MockConnector — self-labeled mock retrieval)
      -> legal_* fields consumed by /legal only

MockConnector output is research display, not evidence: it must never
reclassify an account on the primary register, add to served QPE, or be
classified as authoritative. A real (non-mock) authoritative resolution
would enter the primary pipeline only through the statutory knowledge
base (program_spend_rules) after provenance validation — not through
this demo cycle.

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
from app.data.program_rate_rules import RateResolution, resolve_program_rate
from app.calculators.qualification_model import (
    AccountQualification,
    GreyAreaItem,
    GreyAreaStatus,
    QualificationState,
    build_little_utopia_real_evidence_graph,
    build_little_utopia_real_grey_areas,
    build_little_utopia_real_register,
)
from app.data.little_utopia_real_budget import (
    AUTHORITATIVE_GROSS_BUDGET_USD,
    LEAF_ACCOUNT_SUM_USD,
    LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
    LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
    RECONCILIATION_NOTE,
    RECONCILIATION_VARIANCE_USD,
    SOURCE_PDF_FILENAME,
)
from app.ingestion.budget_parser import BudgetParseResult, ParsedLineItem

PRODUCTION_ID = "LITTLE-UTOPIA"
PRODUCTION_NAME = "The Little Utopia"
JURISDICTION_CODE = "MU"
# The modeled incentive rate. NOT taken from the production budget (whose
# own 'EDB Rebate at 35%' line is ignored per the permanent rate-authority
# rules — see app.data.program_rate_rules): 0.40 is the ceiling of the
# EDB Film Rebate Scheme's 'up to 40%' feature-film band (min QPE USD 1M,
# satisfied). _build_state() re-resolves this via resolve_program_rate()
# against the derived QPE and records the full RateResolution (basis,
# condition evaluations, floor rate, budget-rate conflict report) on the
# state; a mismatch between this constant and the resolver is surfaced as
# a warning rather than silently absorbed.
MU_RATE = 0.40
MU_PRODUCTION_TYPE = "feature_film"
# The production's controlling gross budget: the source PDF's own stated
# Grand Total (AUTHORITATIVE_GROSS_BUDGET_USD), not the sum of the 44
# parsed leaf accounts (LEAF_ACCOUNT_SUM_USD) — the two differ by
# RECONCILIATION_VARIANCE_USD ($2.00), an accepted source-document
# rounding variance (see app.data.little_utopia_real_budget's docstring
# for the full diagnosis). Using the authoritative figure here means
# build_risk_cases()'s own existing reconciliation-warning mechanism
# surfaces the $2 gap on every computed case rather than it being hidden.
MU_GROSS_BUDGET_USD = AUTHORITATIVE_GROSS_BUDGET_USD
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
    """The production's real current facts (from the actual budget's own
    header text — see app.data.little_utopia_real_budget), overlaid with
    any answers the user has supplied through the facts API."""
    return ProductionFacts(
        jurisdiction_code=JURISDICTION_CODE,
        accounts_outside_jurisdiction=LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU,
        offshore_payroll_accounts=LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL,
        post_work_in_jurisdiction=_fact_answers.get("post_work_in_jurisdiction"),
        payroll_routing_localized=_fact_answers.get("payroll_routing_localized"),
        treaty_partner_code=_fact_answers.get("treaty_partner_code"),
    )


def _register_to_budget_parse_result(register: list[AccountQualification]) -> BudgetParseResult:
    """The register IS Little Utopia's real, parsed account-level budget
    data (app.data.little_utopia_real_budget). This reshapes it into the
    ParsedLineItem shape build_budget_intelligence() already accepts —
    no new budget data, no re-parsing, no invented department field.
    Real PDF page provenance is looked up by account code and preserved."""
    from app.data.little_utopia_real_budget import LITTLE_UTOPIA_REAL_BUDGET_LINES
    page_by_code = {code: page for code, _desc, _amt, page in LITTLE_UTOPIA_REAL_BUDGET_LINES}
    line_items = [
        ParsedLineItem(
            description=account.description,
            department=None,
            amount_raw=str(account.amount_usd),
            amount_usd=account.amount_usd,
            currency_code="USD",
            source_row=None,
            source_page=page_by_code.get(account.account_code),
        )
        for account in register
    ]
    return BudgetParseResult(
        filename=SOURCE_PDF_FILENAME,
        currency_code="USD",
        total_budget_raw=MU_GROSS_BUDGET_USD,
        origin_note=(
            f"Parsed from the real Movie Magic budget PDF via "
            f"app.ingestion.budget_parser + app.data.little_utopia_real_budget. "
            f"{RECONCILIATION_NOTE}"
        ),
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
    rate_resolution: RateResolution | None = None
    rate_warnings: list[str] = field(default_factory=list)
    scenario_structures: list[ProductionStructure] = field(default_factory=list)
    scenario_ranking: StructureRankingResult = None
    legal_engine: LegalEngine = None
    legal_cycle: AcquisitionCycleResult = None
    legal_commit: CommitResult = None
    legal_rerun_before: RerunResult = None
    legal_rerun: RerunResult = None
    # Real-budget reconciliation (see app.data.little_utopia_real_budget):
    # the source PDF's own stated Grand Total vs. the sum of its 44 parsed
    # leaf accounts, and the accepted $2 source-document rounding variance
    # between them — preserved and served, never hidden or balanced away.
    budget_authoritative_gross_usd: float = AUTHORITATIVE_GROSS_BUDGET_USD
    budget_leaf_account_sum_usd: float = LEAF_ACCOUNT_SUM_USD
    budget_reconciliation_variance_usd: float = RECONCILIATION_VARIANCE_USD
    budget_reconciliation_note: str = RECONCILIATION_NOTE


def get_state() -> LittleUtopiaState:
    """Current state under the current fact answers. Cached per
    fact-state; apply_fact_answers()/reset_fact_answers() invalidate."""
    return _build_state(tuple(sorted(_fact_answers.items())))


@lru_cache(maxsize=4)
def _build_state(_fact_key: tuple) -> LittleUtopiaState:
    facts = _production_facts()
    graph_default = build_jurisdiction_graph(mu_rate=MU_RATE)  # facts-independent world model

    # Facts -> derived qualification register (Seam A+B), from the REAL
    # parsed production budget (app.data.little_utopia_real_budget) — the
    # sanitized fixture no longer contributes to the primary register.
    register = build_little_utopia_real_register(mu_rate=MU_RATE, facts=facts)
    grey_areas = build_little_utopia_real_grey_areas()
    graph = build_jurisdiction_graph(mu_rate=MU_RATE, register=register)

    # Permanent rate-authority rules (app.data.program_rate_rules): the
    # rate is resolved from the statutory rate database against the
    # DERIVED qualifying spend — never from the budget document's own
    # rebate line (Rules 1-3). Conflicts are reported, never absorbed
    # (Rule 5). A divergence between the resolver and the MU_RATE
    # constant used to build the register is a warning, not silence.
    _verified_qpe = sum(
        a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
    )
    rate_resolution = resolve_program_rate(
        "mu_edb_incentive", production_type=MU_PRODUCTION_TYPE, qpe_usd=_verified_qpe,
    )
    rate_warnings: list[str] = []
    if rate_resolution is None:
        rate_warnings.append(
            "No statutory rate rule found for mu_edb_incentive — MU_RATE constant "
            "is running without database backing."
        )
    elif abs(rate_resolution.modeled_rate - MU_RATE) > 1e-9:
        rate_warnings.append(
            f"Statutory rate database resolves {rate_resolution.modeled_rate:.0%} "
            f"but the pipeline is built at {MU_RATE:.0%} — reconcile before "
            "trusting incentive figures."
        )

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

    # ── PRIMARY PRODUCTION PIPELINE — authoritative data only ──────────
    # Everything served as primary production state (register, discovery,
    # composition, recommendations, scenarios) is computed from the RAW
    # statutory register and pristine grey areas. The MockConnector legal
    # cycle below runs over ITS OWN copies and feeds only the legal_*
    # research fields — mock/demo research must never alter the primary
    # production calculations. (This restores the separation that existed
    # before commit dee6c2b, whose "Seam C" rewiring let a MockConnector
    # resolution silently add $113,000 to served QPE — the confirmed
    # mock-contamination regression.)

    collection = discover_all_opportunities(
        baseline_jurisdiction=JURISDICTION_CODE, mu_rate=MU_RATE, graph=graph,
        movable_spend_usd=movable_spend_usd,
        register=register, grey_areas=grey_areas,
    )

    # Seam B: an elected treaty partner is an engine input to structure
    # composition (an extra jurisdiction set), not a display string.
    extra_sets: list[tuple[str, ...]] = []
    if facts.treaty_partner_code:
        extra_sets.append((JURISDICTION_CODE, facts.treaty_partner_code))

    composition = compose_production_structures(
        collection, graph, register=register, gross_budget_usd=MU_GROSS_BUDGET_USD,
        rate=MU_RATE, grey_areas=grey_areas,
        extra_jurisdiction_sets=extra_sets or None,
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

    # ── LEGAL / RESEARCH VIEW — explicitly labeled, mock-sourced ───────
    # One acquisition cycle through the sole shipped connector
    # (MockConnector — every excerpt self-labels "MOCK CONNECTOR — no
    # live retrieval performed"). It operates on its OWN fresh copy of
    # the grey areas and feeds ONLY the legal_* fields consumed by
    # /legal — never the primary register/composition above.
    legal_grey_areas = build_little_utopia_real_grey_areas()
    legal_engine = LegalEngine(connectors={
        ConnectorClass.TAX_AUTHORITY_GUIDANCE: MockConnector(ConnectorClass.TAX_AUTHORITY_GUIDANCE),
    })
    # Baseline rerun BEFORE any resolution — a fresh LegalEngine over a
    # fresh copy of the grey areas, so the "before" figure reflects zero
    # commits, exactly like any other direct build_risk_cases() caller.
    legal_rerun_before = LegalEngine().rerun(
        register=register, gross_budget_usd=MU_GROSS_BUDGET_USD, rate=MU_RATE,
        grey_areas=build_little_utopia_real_grey_areas(), graph=graph_default,
        jurisdiction_code=JURISDICTION_CODE,
    )

    legal_cycle = legal_engine.run_acquisition_cycle(AS_OF_DATE, grey_areas=legal_grey_areas, graph=graph_default)

    # Demonstrate the acquisition -> verify -> approve -> commit loop over
    # the sole genuine grey work item (GA-INKIND-FMV — off-budget in-kind
    # post FMV). Off-budget, so apply_resolutions is a no-op on the primary
    # register (no contamination); this only populates the /legal research
    # view. The MockConnector citation stays non-authoritative throughout.
    legal_commit = None
    if "STG-TASK-GA-INKIND-FMV" in legal_cycle.awaiting_verification:
        legal_engine.record_verification(
            "STG-TASK-GA-INKIND-FMV", verified_by="counsel@littleutopia.example",
            outcome="authority_found", notes="Research view only — EDB ruling on in-kind "
                                              "post-production FMV treatment (mock retrieval).",
        )
        legal_engine.record_approval("STG-TASK-GA-INKIND-FMV", approved_by="producer@littleutopia.example")
        ga = next(g for g in legal_grey_areas if g.item_id == "GA-INKIND-FMV")
        legal_commit = legal_engine.commit_and_score(
            "STG-TASK-GA-INKIND-FMV", target_jurisdiction_code=JURISDICTION_CODE, as_of_date=AS_OF_DATE,
            rule_text="In-kind post-production FMV qualifies as additive QPE.",
            tier=AuthorityTier.OFFICIAL_GUIDANCE, authority_body="Mauritius Revenue Authority",
            resolves_grey_area=ga, grey_area_outcome=GreyAreaStatus.RESOLVED_INCLUDE,
        )

    legal_rerun = legal_engine.rerun(
        register=register, gross_budget_usd=MU_GROSS_BUDGET_USD, rate=MU_RATE,
        grey_areas=legal_grey_areas, graph=graph_default, jurisdiction_code=JURISDICTION_CODE,
        as_of_date=AS_OF_DATE,
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
        rate_resolution=rate_resolution,
        rate_warnings=rate_warnings,
        fact_answers=current_fact_answers(),
        scenario_structures=scenario_structures,
        scenario_ranking=scenario_ranking,
        legal_engine=legal_engine,
        legal_cycle=legal_cycle,
        legal_commit=legal_commit,
        legal_rerun_before=legal_rerun_before,
        legal_rerun=legal_rerun,
    )
