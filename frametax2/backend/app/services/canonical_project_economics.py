"""
canonical_project_economics.py

The generic economic-input bridge for the CANONICAL evaluation engine.

Background — why this module exists at all:

CineGlobe served two evaluation systems. The DB-backed structures path
(`app/api/v1/structures.py` -> `run_full_analysis`, ENGINE_VERSION 0.1.0)
is project-generic but economically legacy: its call chain references
NONE of the validated canonical layers (`program_spend_rules` QPE
doctrine, `program_rate_rules` statutory rate resolution,
`authority_coverage_registry`, `qualification_model`'s account register,
`production_allocation` / `allocation_pricing`). Priced against Little
Utopia's real budget it returns $4,181,808.00 with $0.00 incentive —
$1,124,013.10 away from the accepted canonical $3,057,794.90.

The canonical engine (`app/demo/little_utopia_state.py::
build_allocated_structures` and its chain) carries every validated layer
but read its inputs from Little-Utopia-specific module constants.

Crucially, the canonical CALCULATORS were already fully generic —
`derive_qualification_register`, `derive_account_allocation` and
`price_allocated_structure` take plain data, not a LittleUtopiaState.
Only their INPUT DATA was project-specific. This module supplies that
data for any project, from persisted project evidence:

    BudgetDocument.total_budget_raw   -> authoritative gross budget
    BudgetLineItem rows               -> BudgetLine(account_code, ...)
    BudgetLineItem.spend_category     -> spend_category_by_code
    ProjectFact territorial evidence  -> accounts_outside_jurisdiction /
                                         offshore_payroll_accounts
    Project.home_jurisdiction_id      -> base jurisdiction code

Nothing here computes economics. It selects and shapes inputs, and it
refuses rather than defaulting: a project whose evidence is incomplete
returns None with a stated reason, never a partially-guessed input set.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.production_requirements import abstract_location
from app.calculators.qualification_derivation import BudgetLine, ProductionFacts
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.jurisdiction import Jurisdiction
from app.models.project import Project
from app.models.project_fact import ProjectFact

#: ProjectFact keys carrying the territorial evidence the canonical
#: territoriality guard needs. Both are LISTS OF ACCOUNT CODES stated by
#: the production's own budget document — never inferred from payer/SPV
#: (see the canonical territoriality rule), never defaulted when absent.
FACT_ACCOUNTS_OUTSIDE_JURISDICTION = "budget_accounts_outside_base_jurisdiction"
FACT_OFFSHORE_PAYROLL_ACCOUNTS = "budget_offshore_payroll_accounts"

#: Consolidated Backend Correction, Part 19-20 (CBA-009) — the EXISTING
#: generic ProjectFact model is the real project setting for a producer's
#: stated expected contingency-spend utilization (0-100, percent). A real,
#: PROJECTED, user-controlled fact, distinct from app.calculators.
#: contingency_treatment's ACTUAL/incurred deployment tracking. Absent
#: means genuinely unset -- never defaulted to 0% or 100% (see
#: qualification_derivation.derive_qualification_register's contingency
#: branch, which surfaces GREY_AREA_REQUIRES_AUTHORITY when this is None).
FACT_CONTINGENCY_EXPECTED_UTILIZATION_PCT = "contingency_expected_utilization_pct"

#: Leading account-code token on a budget line description, e.g.
#: "1400 CAST" -> ("1400", "CAST"). Film budgets are account-coded by
#: convention; a line without a code cannot participate in
#: account->jurisdiction allocation and is reported rather than guessed.
_ACCOUNT_CODE_RE = re.compile(r"^\s*(\d{3,6})\s+(.*)$")


@dataclass(frozen=True)
class ProjectEconomicInputs:
    """Everything the canonical engine needs about ONE project, in the
    plain shapes its generic calculators already accept."""

    project_id: str
    project_name: str
    jurisdiction_code: str
    production_type: str

    #: The budget document's OWN declared grand total — not the leaf-line
    #: sum. Per the SA-1.5 corpus these differ on real documents (Little
    #: Utopia: $4,364,393 declared vs $4,364,395 leaf sum, a disclosed
    #: source-document rounding variance) and the declared total is the
    #: canonical basis for rate resolution and NPC.
    gross_budget_usd: float
    leaf_account_sum_usd: float

    budget_lines: list[BudgetLine]
    spend_category_by_code: dict[str, str]
    accounts_outside_jurisdiction: frozenset[str]
    offshore_payroll_accounts: frozenset[str]

    budget_document_id: str | None = None
    unparsed_line_descriptions: list[str] = field(default_factory=list)

    #: Provenance for the two territorial fact sets above (Codex Defect 1)
    #: -- STATED means a ProjectFact row exists for this key; UNKNOWN means
    #: none was ever recorded. Disclosure only; both states still resolve
    #: to the same empty-set input for the territoriality guard.
    accounts_outside_jurisdiction_state: str = "UNKNOWN"
    offshore_payroll_accounts_state: str = "UNKNOWN"

    #: Count of real, persisted SA-1 ProductionRequirement rows for this
    #: project (Codex Defect 1) -- disclosed so the served trace never
    #: implies "derive_production_requirements({}) found nothing" when
    #: real script-derived requirements actually exist; they are not yet
    #: mapped into the environment/infrastructure capability vocabulary
    #: derive_production_requirements() consumes (a distinct, larger,
    #: separately-scoped gap -- see CANONICAL_SERVED_WIRING_REPAIR.md).
    production_requirements_on_file: int = 0

    #: Consolidated Backend Correction, Part 19-20 (CBA-009) — the
    #: producer's own stated expected contingency-spend utilization
    #: (0-100, percent), read from the generic ProjectFact model. None
    #: means genuinely unset, never defaulted.
    contingency_expected_utilization_pct: float | None = None

    @property
    def reconciliation_variance_usd(self) -> float:
        return round(self.leaf_account_sum_usd - self.gross_budget_usd, 2)


@dataclass(frozen=True)
class EconomicInputsResult:
    """Inputs, or the exact reason a project cannot yet be priced."""

    inputs: ProjectEconomicInputs | None
    blockers: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.inputs is not None


def _fact_account_set(rows: list[ProjectFact], key: str) -> frozenset[str]:
    """Read a JSON list-of-account-codes ProjectFact. An absent fact is an
    EMPTY set, which is materially different from an unknown one: absence
    means the budget states no account outside the base jurisdiction, and
    the territoriality guard treats stated-location evidence as the only
    basis for moving spend out. Nothing is inferred here either way."""
    row = next((f for f in rows if f.fact_key == key), None)
    if row is None or not row.value:
        return frozenset()
    try:
        parsed = json.loads(row.value)
    except (ValueError, TypeError):
        return frozenset()
    if not isinstance(parsed, list):
        return frozenset()
    return frozenset(str(x).strip() for x in parsed if str(x).strip())


#: Canonical served wiring repair (Codex Defect 1) — the territoriality
#: guard itself must keep treating an absent fact as "no accounts stated
#: outside the base jurisdiction" (an empty set is the only safe input a
#: calculator that needs SOME set can be given without inventing evidence).
#: What was missing downstream is HONESTY about that absence: nothing
#: previously recorded whether a ProjectFact row was ever stated at all, so
#: "no territorial facts exist yet" and "we checked and confirmed none
#: apply" were indistinguishable in the persisted trace. This reports
#: which one actually happened, for disclosure only — it changes no
#: qualification/allocation outcome.
FACT_STATE_STATED = "STATED"
FACT_STATE_UNKNOWN = "UNKNOWN"


def _fact_presence(rows: list[ProjectFact], key: str) -> str:
    row = next((f for f in rows if f.fact_key == key), None)
    return FACT_STATE_STATED if row is not None and row.value else FACT_STATE_UNKNOWN


def _fact_float(rows: list[ProjectFact], key: str) -> float | None:
    """Consolidated Backend Correction, Part 19-20 — read a scalar numeric
    ProjectFact. An absent or unparseable value stays None (a genuine
    missing project fact), never coerced to 0."""
    row = next((f for f in rows if f.fact_key == key), None)
    if row is None or row.value in (None, ""):
        return None
    try:
        return float(row.value)
    except (TypeError, ValueError):
        return None


#: Generic project.format -> the production_type vocabulary the statutory
#: rate/doctrine registries are keyed on (shared with project_evaluation).
_FORMAT_TO_PRODUCTION_TYPE = {
    "feature": "feature_film",
    "series": "tv_series",
    "documentary": "creative_documentary",
    "animation": "animation",
}


async def build_project_economic_inputs(
    session: AsyncSession, project_id
) -> EconomicInputsResult:
    """Assemble canonical economic inputs for any project from persisted
    evidence. Returns blockers rather than a degraded input set."""
    blockers: list[str] = []

    project = await session.get(Project, project_id)
    if project is None:
        return EconomicInputsResult(None, ["Project not found."])

    jurisdiction = (
        await session.get(Jurisdiction, project.home_jurisdiction_id)
        if project.home_jurisdiction_id else None
    )
    if jurisdiction is None:
        blockers.append(
            "BASE_JURISDICTION_UNKNOWN — the production's base jurisdiction is "
            "not confirmed on the project. It is not defaulted; supply it "
            "explicitly or let evaluation derive it from source evidence."
        )

    doc = (await session.execute(
        select(BudgetDocument)
        .where(BudgetDocument.project_id == project_id)
        .order_by(BudgetDocument.created_at.desc())
    )).scalars().first()
    if doc is None:
        # Fresh Project Source-Document Ingestion: before reporting
        # BUDGET_MISSING, try the SAME budget-routing implementation
        # material_routing.route_committed_material already runs
        # automatically for every NEW commit (POST /candidates/{id}/
        # commit) -- reused unchanged here as the retroactive trigger for
        # a project whose budget Document/DocumentVersion predates that
        # commit-time wiring (bulk-seeded/imported before it existed): a
        # real attached file that was simply never routed, not a missing
        # asset. Evaluate orchestrates that trigger itself rather than
        # requiring a separate manual step the product never exposes.
        # Idempotent (material_routing._route_budget's own existing-row
        # check) — never fabricates a budget when routing genuinely can't
        # run (unsupported format, no file cached, nothing extractable).
        from app.services.material_routing import ensure_current_budget_routed
        doc = await ensure_current_budget_routed(session, project_id)
    if doc is None:
        blockers.append(
            "BUDGET_MISSING — no parsed budget document is attached. The "
            "canonical engine prices an actual budget; it does not estimate one."
        )
        return EconomicInputsResult(None, blockers)

    items = (await session.execute(
        select(BudgetLineItem).where(BudgetLineItem.budget_document_id == doc.id)
    )).scalars().all()
    if not items:
        blockers.append("BUDGET_MISSING — the budget document has no parsed line items.")
        return EconomicInputsResult(None, blockers)

    lines: list[BudgetLine] = []
    spend_category_by_code: dict[str, str] = {}
    unparsed: list[str] = []
    leaf_sum = 0.0

    for item in items:
        description = item.description or ""
        match = _ACCOUNT_CODE_RE.match(description)
        if match is None:
            # Reported, never silently dropped and never assigned a
            # synthetic code — an uncoded line cannot be allocated to a
            # jurisdiction, which is a real input gap, not a rounding one.
            unparsed.append(description)
            continue
        code, label = match.group(1), match.group(2).strip()
        amount = float(item.amount_usd) if item.amount_usd is not None else 0.0
        leaf_sum += amount
        category = getattr(item.spend_category, "value", item.spend_category)
        if category:
            spend_category_by_code[code] = category
        lines.append(BudgetLine(
            account_code=code, description=label, amount_usd=amount,
            spend_category=category, is_memo=False,
        ))

    if not lines:
        blockers.append(
            "BUDGET_NOT_ACCOUNT_CODED — no budget line carries a leading account "
            "code, so account->jurisdiction allocation cannot run. Codes are read "
            "from the document, never generated."
        )

    if doc.total_budget_raw is None:
        blockers.append(
            "BUDGET_TOTAL_MISSING — the budget document states no grand total. "
            "The leaf-line sum is not substituted for it."
        )

    if blockers:
        return EconomicInputsResult(None, blockers)

    fact_rows = (await session.execute(
        select(ProjectFact).where(ProjectFact.project_id == project_id)
    )).scalars().all()

    from app.models.production_requirement import ProductionRequirement
    requirements_on_file = (await session.execute(
        select(ProductionRequirement.id).where(ProductionRequirement.project_id == project_id)
    )).scalars().all()

    return EconomicInputsResult(ProjectEconomicInputs(
        project_id=str(project_id),
        project_name=project.title,
        jurisdiction_code=jurisdiction.code,
        production_type=_FORMAT_TO_PRODUCTION_TYPE.get(
            (project.format or "").lower(), "feature_film"
        ),
        gross_budget_usd=float(doc.total_budget_raw),
        leaf_account_sum_usd=round(leaf_sum, 2),
        budget_lines=lines,
        spend_category_by_code=spend_category_by_code,
        accounts_outside_jurisdiction=_fact_account_set(
            fact_rows, FACT_ACCOUNTS_OUTSIDE_JURISDICTION
        ),
        offshore_payroll_accounts=_fact_account_set(
            fact_rows, FACT_OFFSHORE_PAYROLL_ACCOUNTS
        ),
        accounts_outside_jurisdiction_state=_fact_presence(fact_rows, FACT_ACCOUNTS_OUTSIDE_JURISDICTION),
        offshore_payroll_accounts_state=_fact_presence(fact_rows, FACT_OFFSHORE_PAYROLL_ACCOUNTS),
        production_requirements_on_file=len(requirements_on_file),
        budget_document_id=str(doc.id),
        unparsed_line_descriptions=unparsed,
        contingency_expected_utilization_pct=_fact_float(
            fact_rows, FACT_CONTINGENCY_EXPECTED_UTILIZATION_PCT
        ),
    ))


def production_facts_for(
    inputs: ProjectEconomicInputs, jurisdiction_code: str | None = None,
) -> ProductionFacts:
    """The canonical QPE ladder's own facts object, from project evidence.

    FVD canonical input assembly repair, Task 1: `jurisdiction_code` is the
    candidate being priced (the destination for a full-relocation candidate),
    not always the project's home jurisdiction. Previously this always
    reported `inputs.jurisdiction_code` (the home code) regardless of which
    candidate `_price_candidate()` was pricing, so a Qatar candidate's
    register reason text read "...outside GR" instead of "...outside QA".
    `accounts_outside_jurisdiction`/`offshore_payroll_accounts` are UNCHANGED
    by this — they remain the same project-level stated-account sets either
    way (there is no per-candidate territorial fact to select between; see
    the territoriality guard note on `_fact_account_set`). This only fixes
    which jurisdiction the qualification ladder's own reason text names."""
    return ProductionFacts(
        jurisdiction_code=jurisdiction_code or inputs.jurisdiction_code,
        accounts_outside_jurisdiction=inputs.accounts_outside_jurisdiction,
        offshore_payroll_accounts=inputs.offshore_payroll_accounts,
        contingency_expected_utilization_pct=inputs.contingency_expected_utilization_pct,
    )


# ─────────────────────────────────────────────────────────────────────────
# FVD canonical input assembly repair, Task 1/3 — reconnect
# derive_production_requirements() to SA-1's real, persisted, evidence-
# backed script data instead of the permanent {} that made every
# jurisdiction "production capable" for any requirement, hard or soft.
#
# Bridges TWO vocabularies that already exist in
# app.calculators.production_requirements but were never wired together:
#   - abstract_location() -- a generic keyword ontology over literal
#     location text, defined but never called anywhere in the codebase
#     until this repair.
#   - derive_production_requirements()'s own `location_categories` input
#     shape, keyed on a DIFFERENT (LOCATION_TAXONOMY-derived) slug
#     vocabulary via `_LOCATION_CATEGORY_TO_CAPABILITY`.
# Several of abstract_location()'s outputs already equal
# _LOCATION_CATEGORY_TO_CAPABILITY's KEYS verbatim (beach_coast,
# marine_open_water, mediterranean, island); the rest equal its CAPABILITY
# VALUES (e.g. "desert_environments") rather than its keys ("desert"). The
# table below is the purely mechanical reverse-lookup connecting those --
# no new category, no invented evidence, no AI interpretation. Real
# ontology hits with no location_categories equivalent (harbor_marina,
# village, agricultural, river, lake, town, industrial, residential,
# suburban) are dropped, never fabricated one.
# ─────────────────────────────────────────────────────────────────────────

#: abstract_location() outputs that are already valid location_categories
#: keys verbatim.
_DIRECT_LOCATION_CATEGORY_KEYS = frozenset({
    "beach_coast", "marine_open_water", "mediterranean", "island",
})
#: abstract_location() outputs that are location_categories CAPABILITY
#: VALUES -> the KEY derive_production_requirements() actually reads.
_LOCATION_CAPABILITY_TOKEN_TO_CATEGORY_KEY = {
    "coastal_environments": "beach_coast",
    "open_water_filming": "marine_open_water",
    "tropical_environments": "island_tropical",
    "island_environments": "island",
    "historic_architecture": "historic_old_world",
    "period_environments": "period_town",
    "mountain_environments": "mountain",
    "desert_environments": "desert",
    "urban_environments": "urban",
    "rural_environments": "rural_countryside",
    "forest_environments": "forest",
}


def _location_categories_from_descriptions(descriptions: list[str]) -> dict[str, dict]:
    """`location_categories` input for `derive_production_requirements()`,
    built from real scripted-location description strings (SA-1's
    persisted `ProjectLocationRequirement` rows) run through the existing,
    generic `abstract_location()` keyword ontology. Deterministic keyword
    matching only -- no inference, no LLM, no invented category."""
    out: dict[str, dict] = {}
    for desc in descriptions:
        if not desc:
            continue
        for token in abstract_location(desc):
            key = (
                token if token in _DIRECT_LOCATION_CATEGORY_KEYS
                else _LOCATION_CAPABILITY_TOKEN_TO_CATEGORY_KEY.get(token)
            )
            if key is None:
                continue
            entry = out.setdefault(key, {"effective": False, "evidence": []})
            entry["effective"] = True
            entry["evidence"].append(desc)
    return out


async def build_physical_requirements(session: AsyncSession, project_id) -> dict:
    """Real `physical_requirements` input for `derive_production_requirements()`,
    from SA-1's persisted `ProjectLocationRequirement` (scripted locations)
    and `ProductionRequirement` (PERIOD_REFERENCE presence) rows -- never
    the permanent `{}` that made every jurisdiction appear production-
    capable for any requirement. Reads the same underlying tables
    `CanonicalProductionStateBuilder` reads (SA-1's own persisted rows),
    directly and read-only -- deliberately NOT via
    `CanonicalProductionStateBuilder.build()` itself, which also performs
    an unrelated write-side budget-import fallback and a strict
    READY_FOR_OPTIMIZER gate that would block this project-agnostic
    requirements read on unrelated inputs (shoot days, base-jurisdiction
    assumption) this function does not need.

    No AI interpretation, no invented quantities -- SCRIPTED_LOCATION rows
    run through the existing keyword ontology, and PERIOD_REFERENCE
    presence reported as a plain boolean fact, exactly as evidenced."""
    from app.models.production_requirement import ProductionRequirement
    from app.models.project_location_requirement import ProjectLocationRequirement

    loc_rows = (await session.execute(
        select(ProjectLocationRequirement.description).where(
            ProjectLocationRequirement.project_id == project_id,
            ProjectLocationRequirement.location_key.isnot(None),
        )
    )).scalars().all()
    location_categories = _location_categories_from_descriptions(list(loc_rows))

    period_rows = (await session.execute(
        select(ProductionRequirement.normalized_value, ProductionRequirement.description)
        .where(
            ProductionRequirement.project_id == project_id,
            ProductionRequirement.requirement_key == "PERIOD_REFERENCE",
        )
    )).all()
    script_requirements: dict[str, dict] = {}
    if period_rows:
        normalized_value, description = period_rows[0]
        script_requirements["period"] = {
            "value": True,
            "evidence": description or normalized_value or "PERIOD_REFERENCE (SA-1 script analysis)",
        }

    return {
        "location_categories": location_categories,
        "script_requirements": script_requirements,
        # marine_required / marine_account / aerial_required / aerial_account
        # intentionally left unset: FVD's real budget has no vessel_marine
        # or aerial spend-category line, so there is no real-budget-account
        # signal to report (never fabricated). Any real script marine
        # evidence is already carried honestly via
        # location_categories["marine_open_water"] above.
    }
