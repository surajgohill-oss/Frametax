"""
real_production_corpus.py

Script Analyzer SA-1.5 — the canonical REAL PRODUCTION VALIDATION CORPUS.

CineGlobe's Company Library already holds real productions with real
screenplays, real actual budgets and (for one project) a real schedule and
Day Out of Days. Those are not test files: they are the calibration and
validation corpus for the Script Analyzer and the future production-cost
engine. This module makes that corpus explicit and reusable.

Design decisions, and why:

  * This is a REGISTRY, not a copy. Every fixture references authoritative
    `DocumentVersion` ids that already exist in the Company Library. No
    source document is duplicated, and no actual budget is modified.

  * It is a code+artifact registry rather than a new database table. The
    corpus is internal validation infrastructure with no user-facing
    surface (SA-1.5 Part P), it must be reviewable in version control, and
    a new table would be parallel architecture for no gain. Fixture records
    point AT the canonical data; they never become a second source of it.

  * Project identity is DATA. Nothing here requires per-project source code.
    There is deliberately no `run_lips_like_sugar_optimizer.py` equivalent —
    a fixture is a record, and the generic pipeline consumes it.

The single most important thing this module encodes is the SEPARATION
between what a predictor may see and what it may not. See `ScriptSideInputs`
/ `HeldOutActuals` below and the guard in `holdout_guard.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MaterialStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNSUPPORTED = "UNSUPPORTED"
    UNRESOLVED = "UNRESOLVED"


class ValidationMode(str, Enum):
    """What a fixture is fit to validate, given the materials it actually has."""
    INGESTION_VALIDATION = "INGESTION_VALIDATION"
    SCRIPT_BREAKDOWN_VALIDATION = "SCRIPT_BREAKDOWN_VALIDATION"
    SCHEDULE_VALIDATION = "SCHEDULE_VALIDATION"
    BUDGET_ESTIMATION_VALIDATION = "BUDGET_ESTIMATION_VALIDATION"
    OPTIMIZER_REGRESSION = "OPTIMIZER_REGRESSION"


class ReconciliationStatus(str, Enum):
    #: Source independently declares a grand total equal to the oracle AND the
    #: parsed leaf lines sum to it.
    RECONCILED_EXACT = "RECONCILED_EXACT"
    #: Leaf sum differs from the source's own declared total by a documented,
    #: immaterial source-document rounding variance.
    RECONCILED_SOURCE_ROUNDING = "RECONCILED_SOURCE_ROUNDING"
    #: The source independently declares the oracle AND its own section
    #: hierarchy reconciles to it, but flat leaf-line extraction under-covers.
    #: The gap is a known parser-coverage limit, not a disagreement with the
    #: source. Quantified per fixture.
    RECONCILED_DECLARED_TOTAL_LEAF_GAP = "RECONCILED_DECLARED_TOTAL_LEAF_GAP"
    NOT_RECONCILED = "NOT_RECONCILED"
    NO_BUDGET = "NO_BUDGET"


@dataclass(frozen=True)
class SourceMaterial:
    """A pointer to an authoritative Company Library record. Never a copy."""
    category: str
    status: MaterialStatus
    document_version_id: str | None = None
    filename: str | None = None
    checksum_prefix: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class ScriptSideInputs:
    """What a Script Analyzer prediction path MAY see.

    Screenplay-derived facts only. Nothing here reveals what the production
    actually cost, how long it actually shot, or where it actually went.
    """
    screenplay_document_version_id: str | None
    screenplay_available: bool
    parsed: bool = False
    scene_count: int | None = None
    character_count: int | None = None
    speaking_character_count: int | None = None
    scripted_location_count: int | None = None
    page_count: int | None = None


@dataclass(frozen=True)
class HeldOutActuals:
    """What a prediction path MUST NOT see.

    These are the answers. They exist so an evaluator can score a prediction
    AFTER it has been made — never so a predictor can read them. Enforced by
    holdout_guard.py, not by convention.
    """
    gross_budget_usd: float | None = None
    declared_total_source_usd: float | None = None
    atl_total_usd: float | None = None
    btl_total_usd: float | None = None
    fringes_usd: float | None = None
    contingency_usd: float | None = None
    completion_bond_usd: float | None = None
    shoot_days: int | None = None
    production_geography: str | None = None
    incentive_modeled_usd: float | None = None
    net_after_incentive_usd: float | None = None
    qpe_usd: float | None = None
    cast_role_count: int | None = None
    schedule_document_version_id: str | None = None
    dood_document_version_id: str | None = None


@dataclass(frozen=True)
class BudgetReconciliation:
    status: ReconciliationStatus
    acceptance_oracle_usd: float | None
    source_declared_total_usd: float | None
    parsed_leaf_sum_usd: float | None
    leaf_gap_usd: float | None
    basis: str
    evidence: str


@dataclass(frozen=True)
class ProductionFixture:
    fixture_key: str
    display_name: str
    project_id: str | None
    resolved: bool
    materials: tuple[SourceMaterial, ...]
    script_side: ScriptSideInputs
    held_out: HeldOutActuals
    budget_reconciliation: BudgetReconciliation
    validation_modes: tuple[ValidationMode, ...]
    holdout_eligible: bool
    provenance: str
    notes: str = ""

    def material(self, category: str) -> SourceMaterial | None:
        for m in self.materials:
            if m.category == category:
                return m
        return None

    def status_of(self, category: str) -> MaterialStatus:
        m = self.material(category)
        return m.status if m else MaterialStatus.MISSING

    def supports(self, mode: ValidationMode) -> bool:
        return mode in self.validation_modes


# ══════════════════════════════════════════════════════════════════════════
# The corpus. Every value below was resolved from live Company Library
# records and, for budgets, read out of the source documents themselves —
# never written in to satisfy an oracle.
# ══════════════════════════════════════════════════════════════════════════

_LITTLE_UTOPIA = ProductionFixture(
    fixture_key="little_utopia",
    display_name="The Little Utopia",
    project_id="fa5cade5-0669-4816-bfe6-72146f8d3bae",
    resolved=True,
    materials=(
        SourceMaterial("screenplay", MaterialStatus.AVAILABLE,
                       "7a1b15ff-341b-441f-919a-f1e0afb59d6b",
                       "The Little Utopia 1_30_26.pdf", "c5213c9ced713e07",
                       "A superseded earlier version also exists and is retained."),
        SourceMaterial("budget", MaterialStatus.AVAILABLE,
                       "ee810c4f-8af3-4bdd-ba00-c5989c104172",
                       "The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf",
                       "4b98f8236a4a6029", "Parsed: 44 leaf line items."),
        SourceMaterial("schedule", MaterialStatus.MISSING),
        SourceMaterial("dood", MaterialStatus.MISSING),
        SourceMaterial("deck", MaterialStatus.AVAILABLE,
                       "a9349662-1d7e-4c83-81a8-623a54a4986f", "TheLittleUtopia_Slide.pptx",
                       "4f6d0d54d5323161"),
        SourceMaterial("lookbook", MaterialStatus.AVAILABLE,
                       "2965f692-7db6-44bd-abdb-59e5fadfe198",
                       "THE LITTLE UTOPIA LOOK BOOK .pdf", "6a42245486712a01"),
        SourceMaterial("artwork", MaterialStatus.AVAILABLE,
                       "b345b116-4f65-4d3d-a96b-d96ce7139e35", "utopia.png",
                       "a6df89962c92588f"),
    ),
    script_side=ScriptSideInputs(
        screenplay_document_version_id="7a1b15ff-341b-441f-919a-f1e0afb59d6b",
        screenplay_available=True, parsed=False,
    ),
    held_out=HeldOutActuals(
        gross_budget_usd=4364393.0, declared_total_source_usd=4364393.0,
        production_geography="Mauritius",
    ),
    budget_reconciliation=BudgetReconciliation(
        status=ReconciliationStatus.RECONCILED_SOURCE_ROUNDING,
        acceptance_oracle_usd=4364393.0,
        source_declared_total_usd=4364393.0,
        parsed_leaf_sum_usd=4364395.0,
        leaf_gap_usd=2.0,
        basis="Authoritative top-sheet grand total vs the sum of 44 parsed leaf accounts.",
        evidence=("The $2.00 variance is a pre-existing, already-disclosed "
                  "source-document rounding artefact (two independent $1 "
                  "discrepancies in the source), surfaced in-runtime by "
                  "budget_reconciliation_variance_usd. Not a parser defect."),
    ),
    validation_modes=(ValidationMode.OPTIMIZER_REGRESSION,
                      ValidationMode.INGESTION_VALIDATION),
    holdout_eligible=False,
    provenance="Company Library import; canonical worldwide-optimizer regression fixture.",
    notes=("Reserved as the optimizer regression anchor (winner Mauritius, NPC "
           "$3,057,794.90). Deliberately NOT the primary Script Analyzer "
           "calibration fixture — its assumptions must not leak into other projects."),
)

_FVD = ProductionFixture(
    fixture_key="fvd",
    display_name="F#K Valentine's Day",
    project_id="6c6f1c13-2d49-4bbc-bafb-2a12efa93112",
    resolved=True,
    materials=(
        SourceMaterial("screenplay", MaterialStatus.AVAILABLE,
                       "d25b035b-dc6f-471a-a611-6ed397444889",
                       "F#K Valentine's Day- pdf.pdf", "4caea6619bcadf93",
                       "Parsed by the SA-1 structural parser: 99 scenes, 38 characters."),
        SourceMaterial("budget", MaterialStatus.AVAILABLE,
                       "cf33eae1-aa4e-4e4e-80d2-ce737f5a373e",
                       "V-BRAT_V8_Greece_041224 TOPSHEET.pdf", "253e80e987a0aa3c",
                       "Parsed: 34 leaf line items."),
        SourceMaterial("schedule", MaterialStatus.MISSING),
        SourceMaterial("dood", MaterialStatus.MISSING),
        SourceMaterial("deck", MaterialStatus.AVAILABLE,
                       "cb0faa80-4a62-4e93-95e1-3f30cc6bda5b",
                       "Fck Valentines Day - - 2.9.24 deck.pdf", "09913b6899fd743b"),
        SourceMaterial("artwork", MaterialStatus.AVAILABLE,
                       "8e13f3b1-3ec2-4696-8543-af93a0099e43",
                       "Fck Valentines Day - - 2.9.24 deck (cover).jpeg", "fa74b427c97cbd86"),
    ),
    script_side=ScriptSideInputs(
        screenplay_document_version_id="d25b035b-dc6f-471a-a611-6ed397444889",
        screenplay_available=True, parsed=True, scene_count=99, character_count=38,
    ),
    held_out=HeldOutActuals(
        gross_budget_usd=4517687.0, declared_total_source_usd=4517687.0,
        shoot_days=18, production_geography="Greece",
        incentive_modeled_usd=518804.0, net_after_incentive_usd=3998883.0,
    ),
    budget_reconciliation=BudgetReconciliation(
        status=ReconciliationStatus.RECONCILED_EXACT,
        acceptance_oracle_usd=4517687.0,
        source_declared_total_usd=4517687.0,
        parsed_leaf_sum_usd=4517687.0,
        leaf_gap_usd=0.0,
        basis="Top-sheet grand total vs the sum of 34 parsed leaf accounts.",
        evidence=("Exact. The source is a top-sheet, so leaf accounts and the "
                  "declared grand total are the same population."),
    ),
    validation_modes=(ValidationMode.INGESTION_VALIDATION,
                      ValidationMode.SCRIPT_BREAKDOWN_VALIDATION),
    holdout_eligible=True,
    provenance=("Company Library import. Greece is established by the source budget "
                "itself (filename and content: V-BRAT_V8_Greece), not inferred by "
                "the optimizer."),
    notes=("FVD_REAL_PROJECT_FIXTURE = VERIFIED. Greece appearing in a runtime "
           "result is supported by source evidence and is not a defect. "
           "BUDGET_ESTIMATION_VALIDATION becomes available once an estimator exists."),
)

_LIPS_LIKE_SUGAR = ProductionFixture(
    fixture_key="lips_like_sugar",
    display_name="Lips Like Sugar",
    project_id="ab10b319-978e-44d3-9331-af2a5f2cccc2",
    resolved=True,
    materials=(
        SourceMaterial("screenplay", MaterialStatus.AVAILABLE,
                       "a55c5a35-1e55-4003-b68b-716be946cc01", "LIPS OFFICIAL.pdf",
                       "c6735c1a3826e6b4", "Not yet structurally parsed."),
        SourceMaterial("budget", MaterialStatus.AVAILABLE,
                       "f2333b72-fcf7-4437-943f-4765357fe20e",
                       "v7LLS_RevBudget_T1B_27days_022524.pdf", "37814d8b33358fd7",
                       "52-page detailed budget (crew, prep/shoot/wrap, rates, fringes)."),
        SourceMaterial("schedule", MaterialStatus.MISSING),
        SourceMaterial("dood", MaterialStatus.MISSING),
    ),
    script_side=ScriptSideInputs(
        screenplay_document_version_id="a55c5a35-1e55-4003-b68b-716be946cc01",
        screenplay_available=True, parsed=False,
    ),
    held_out=HeldOutActuals(
        gross_budget_usd=11983654.0, declared_total_source_usd=11983654.0,
        atl_total_usd=3174975.0, btl_total_usd=8293679.0,
        shoot_days=27, production_geography="Los Angeles and surrounding",
        incentive_modeled_usd=1503074.0, net_after_incentive_usd=10480580.0,
    ),
    budget_reconciliation=BudgetReconciliation(
        status=ReconciliationStatus.RECONCILED_DECLARED_TOTAL_LEAF_GAP,
        acceptance_oracle_usd=11983654.0,
        source_declared_total_usd=11983654.0,
        parsed_leaf_sum_usd=9638143.0,
        leaf_gap_usd=2345511.0,
        basis=("The source's own declared grand total, cross-checked against its "
               "own section hierarchy: Total Above-The-Line $3,174,975 + Total "
               "Below-The-Line $8,293,679 = Total Above and Below-The-Line "
               "$11,468,654, leaving a $515,000 contingency/bond block to the "
               "$11,983,654 grand total."),
        evidence=("The oracle was READ FROM the document, not written in. Flat "
                  "leaf-line extraction under-covers by $2,345,511 on this "
                  "52-page detailed budget because the parser sums a mixed "
                  "population of top-sheet category rows and detail rows and "
                  "does not apply the budget's ATL/BTL/fringe/contingency "
                  "hierarchy. A known parser-coverage limit belonging to the "
                  "deferred L1/L2/L3 budget work — NOT a disagreement with the source."),
    ),
    validation_modes=(ValidationMode.INGESTION_VALIDATION,
                      ValidationMode.SCRIPT_BREAKDOWN_VALIDATION),
    holdout_eligible=True,
    provenance=("Company Library import. 27-day shoot is corroborated by the budget "
                "filename and content. The Los Angeles basis is an externally "
                "declared production fact; this bounded pass found only a weak "
                "'CA' token in the budget text and does not claim document confirmation."),
    notes="High-value detailed budget: crew, prep/shoot/wrap, rates, equipment, transport, fringes.",
)

_UNDERWATER = ProductionFixture(
    fixture_key="underwater",
    display_name="Underwater",
    project_id="f1292c56-0288-4575-91ec-1f00081f07a0",
    resolved=True,
    materials=(
        SourceMaterial("screenplay", MaterialStatus.AVAILABLE,
                       "fd10435d-8298-4143-97ca-1e381d2eb951",
                       "Underwater 3CC Draft 1.5.21 (319) (2).pdf", "2546fd9cf3a7560a",
                       "Not yet structurally parsed."),
        SourceMaterial("budget", MaterialStatus.AVAILABLE,
                       "d2a9bbf7-5ea9-4dad-b97f-dfecf283600f",
                       "Underwater Budget 9-3 (1).pdf", "9edafd1b17db1766",
                       "31-page detailed budget."),
        SourceMaterial("schedule", MaterialStatus.MISSING),
        SourceMaterial("dood", MaterialStatus.MISSING),
        SourceMaterial("deck", MaterialStatus.AVAILABLE,
                       "e295556d-0598-4d63-94ae-321413712ba3",
                       "Underwater Presentation.pptx (1) (1) (1).pdf", "b7c77f7fece30e0f"),
        SourceMaterial("artwork", MaterialStatus.AVAILABLE,
                       "f292973c-0979-4496-995d-1a04c6522781",
                       "Underwater Presentation.pptx (1) (1) (1) (cover).jpeg",
                       "1fb6ee925d5bade6"),
    ),
    script_side=ScriptSideInputs(
        screenplay_document_version_id="fd10435d-8298-4143-97ca-1e381d2eb951",
        screenplay_available=True, parsed=False,
    ),
    held_out=HeldOutActuals(
        gross_budget_usd=7998944.0, declared_total_source_usd=7998944.0,
        atl_total_usd=2731485.0, btl_total_usd=3319416.0,
        fringes_usd=1025143.0, contingency_usd=727800.0, completion_bond_usd=195100.0,
        shoot_days=30,
    ),
    budget_reconciliation=BudgetReconciliation(
        status=ReconciliationStatus.RECONCILED_DECLARED_TOTAL_LEAF_GAP,
        acceptance_oracle_usd=7998944.0,
        source_declared_total_usd=7998944.0,
        parsed_leaf_sum_usd=7086368.0,
        leaf_gap_usd=912576.0,
        basis=("FULLY reconciled from the document's own section totals: "
               "ATL $2,731,485 + BTL $3,319,416 = $6,050,901 (equals the "
               "document's own 'Total Above and Below-The-Line'); + Fringes "
               "$1,025,143 + contingency $727,800 + bond $195,100 = $7,998,944, "
               "exactly the acceptance oracle."),
        evidence=("The strongest reconciliation in the corpus: every component "
                  "of the oracle is independently present in the source. The "
                  "$912,576 leaf-sum gap is purely a flat-extraction coverage "
                  "limit (the fringe/contingency/bond blocks are section totals "
                  "in a column-extracted layout, not account-code rows)."),
    ),
    validation_modes=(ValidationMode.INGESTION_VALIDATION,
                      ValidationMode.SCRIPT_BREAKDOWN_VALIDATION),
    holdout_eligible=True,
    provenance=("Company Library import. The budget's own top sheet states "
                "Shoot: 30 Days (6x 5-Day Weeks), Pre-Production 5 Weeks, Post 24 Weeks."),
    notes="Independent actual-budget fixture with a fully component-reconcilable oracle.",
)

_THE_SYSTEM = ProductionFixture(
    fixture_key="the_system",
    display_name="The System",
    project_id="e1f2444d-4eac-410e-9c92-45637b8f2ae0",
    resolved=True,
    materials=(
        SourceMaterial("screenplay", MaterialStatus.AVAILABLE,
                       "7eebb8f5-2296-43d3-a878-09c22b384191",
                       "The System - 2021 - production  draft black.pdf", "8987953664ea190e",
                       "Not yet structurally parsed."),
        SourceMaterial("budget", MaterialStatus.AVAILABLE,
                       "37c6f745-616d-4b0e-8df4-6f666207566d", "The System Budget v2.8.pdf",
                       "6c0eb888cad40eba", "37-page detailed budget."),
        SourceMaterial("schedule", MaterialStatus.AVAILABLE,
                       "5e5faef7-a43b-4c80-8a48-e4397f124c2f",
                       "The System DOOD Schedule v1.0.pdf", "6c059dab801916c4",
                       "Current. Two superseded versions retained: "
                       "THE SYSTEM PROD SCHEDULE .xlsx and The System HorC_Schedule.pdf."),
        SourceMaterial("dood", MaterialStatus.AVAILABLE,
                       "5e5faef7-a43b-4c80-8a48-e4397f124c2f",
                       "The System DOOD Schedule v1.0.pdf", "6c059dab801916c4",
                       "Genuine 'Day Out of Days Report for Cast Members', dated 06/21 onward. "
                       "Same DocumentVersion as the schedule — one artefact, two roles."),
        SourceMaterial("finance_plan", MaterialStatus.MISSING,
                       note="No separate finance-plan document is present in the Company "
                            "Library for this project in this bounded pass."),
    ),
    script_side=ScriptSideInputs(
        screenplay_document_version_id="7eebb8f5-2296-43d3-a878-09c22b384191",
        screenplay_available=True, parsed=False,
    ),
    held_out=HeldOutActuals(
        gross_budget_usd=4324058.0, declared_total_source_usd=4324058.0,
        atl_total_usd=2370132.0, btl_total_usd=1611855.0,
        shoot_days=20, production_geography="Mississippi (Jackson)",
        schedule_document_version_id="5e5faef7-a43b-4c80-8a48-e4397f124c2f",
        dood_document_version_id="5e5faef7-a43b-4c80-8a48-e4397f124c2f",
    ),
    budget_reconciliation=BudgetReconciliation(
        status=ReconciliationStatus.RECONCILED_DECLARED_TOTAL_LEAF_GAP,
        acceptance_oracle_usd=4324058.0,
        source_declared_total_usd=4324058.0,
        parsed_leaf_sum_usd=4079890.0,
        leaf_gap_usd=244168.0,
        basis=("The source's own declared grand total, cross-checked against its "
               "own hierarchy: TOTAL ABOVE-THE-LINE $2,370,132 + Total "
               "Below-The-Line $1,611,855 = $3,981,987 (equals the document's own "
               "'Total Above and Below-The-Line'), leaving $342,071 of "
               "fringes/contingency/bond to the $4,324,058 grand total."),
        evidence=("Oracle read from the document. The $244,168 leaf gap is the "
                  "same flat-extraction coverage limit seen on the other detailed "
                  "budgets."),
    ),
    validation_modes=(ValidationMode.INGESTION_VALIDATION,
                      ValidationMode.SCRIPT_BREAKDOWN_VALIDATION),
    holdout_eligible=True,
    provenance=("Company Library import. Mississippi is evidenced by 'Jackson' in the "
                "budget; 20 shooting days is corroborated in the budget text; the DOOD "
                "is a genuine Day Out of Days cast report."),
    notes=("THE DEEP FIXTURE. The only project in the corpus carrying "
           "SCRIPT + SCHEDULE + DOOD + ACTUAL BUDGET together. This is the future "
           "held-out target for script -> requirements -> schedule prediction. "
           "SA-1.5 establishes the linkage ONLY; it does not attempt to reproduce "
           "the schedule from the screenplay."),
)

_TETRAD = ProductionFixture(
    fixture_key="tetrad",
    display_name="Tetrad",
    project_id=None,
    resolved=False,
    materials=(
        SourceMaterial("screenplay", MaterialStatus.UNRESOLVED),
        SourceMaterial("budget", MaterialStatus.UNRESOLVED),
        SourceMaterial("schedule", MaterialStatus.UNRESOLVED),
        SourceMaterial("dood", MaterialStatus.UNRESOLVED),
    ),
    script_side=ScriptSideInputs(screenplay_document_version_id=None,
                                 screenplay_available=False),
    held_out=HeldOutActuals(
        gross_budget_usd=3700593.0, production_geography="Sydney, Australia",
        qpe_usd=3306143.0, incentive_modeled_usd=1322457.0,
    ),
    budget_reconciliation=BudgetReconciliation(
        status=ReconciliationStatus.NO_BUDGET,
        acceptance_oracle_usd=3700593.0,
        source_declared_total_usd=None,
        parsed_leaf_sum_usd=None,
        leaf_gap_usd=None,
        basis="No source document available to reconcile against.",
        evidence=("Tetrad is NOT present in the Company Library. A bounded search "
                  "across all 52 projects, all document titles and all "
                  "DocumentVersion filenames returned zero matches. The known "
                  "figures are recorded as externally-declared expectations so the "
                  "fixture can be completed the moment its materials are imported; "
                  "they are NOT treated as reconciled."),
    ),
    validation_modes=(),
    holdout_eligible=False,
    provenance="Externally declared by the master engineer; not yet imported.",
    notes="UNRESOLVED — awaiting import. No data was manufactured to fill the gap.",
)

CORPUS: tuple[ProductionFixture, ...] = (
    _LITTLE_UTOPIA, _FVD, _LIPS_LIKE_SUGAR, _UNDERWATER, _THE_SYSTEM, _TETRAD,
)

FIXTURES: dict[str, ProductionFixture] = {f.fixture_key: f for f in CORPUS}


def get_fixture(key: str) -> ProductionFixture | None:
    return FIXTURES.get(key)


def resolved_fixtures() -> tuple[ProductionFixture, ...]:
    return tuple(f for f in CORPUS if f.resolved)


def fixtures_for_mode(mode: ValidationMode) -> tuple[ProductionFixture, ...]:
    return tuple(f for f in CORPUS if f.supports(mode))


def deep_fixtures() -> tuple[ProductionFixture, ...]:
    """Fixtures carrying script + budget + schedule + DOOD together."""
    return tuple(
        f for f in CORPUS
        if all(f.status_of(c) == MaterialStatus.AVAILABLE
               for c in ("screenplay", "budget", "schedule", "dood"))
    )
