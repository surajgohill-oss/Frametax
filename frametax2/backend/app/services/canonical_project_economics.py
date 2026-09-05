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
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.production_requirements import abstract_location
from app.calculators.qualification_derivation import BudgetLine, ProductionFacts
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.enums import ProjectFactSourceType
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

#: Producer Display Names + Budget Rail User Assumptions closeout — the
#: SAME generic ProjectFact model, same USER_OVERRIDE precedence, as
#: contingency_expected_utilization_pct above. A producer's stated
#: financing/bridge cost for this production, in USD. This is NOT a
#: budget line item (it does not rewrite the imported source PDF or any
#: normalized BudgetLineItem) and it is NOT QPE (it never enters any
#: jurisdiction's qualifying-spend register) — it flows only into
#: allocation_pricing.price_allocated_structure's existing
#: `financing_cost_usd` parameter, which already adds it to NPC
#: (npc_verified_usd / npc_with_adjustments_usd) exactly as documented
#: there ("Financing... default to zero — explicit inputs only, never a
#: silent assumption"). Absent means genuinely unset — treated as 0.0 by
#: price_allocated_structure's own default, never defaulted here.
FACT_FINANCING_COST_USD = "financing_cost_usd"

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

    #: Producer Display Names + Budget Rail User Assumptions closeout —
    #: see FACT_FINANCING_COST_USD above. None means genuinely unset.
    financing_cost_usd: float | None = None

    #: FINANCE SEMANTICS (settled doctrine). financing_cost_usd means
    #: INCREMENTAL / OFF-BUDGET financing NOT already inside the source gross
    #: budget. This is the other half of that contract: the financing already
    #: CLASSIFIED in the source budget (SpendCategory.FINANCE_COSTS -- Lips'
    #: FINANCING FEES + BRIDGE + BANKING FEE = $1,700,000). It is part of
    #: gross and is therefore ALREADY in NPC; it must never be added again.
    #: Serving both figures is what makes the distinction checkable rather
    #: than a convention someone has to remember.
    source_budget_finance_usd: float = 0.0

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

#: Fresh Project Ingestion, base-jurisdiction derivation: currency evidence
#: -> canonical jurisdiction code. Only currencies with ONE unambiguous
#: issuing jurisdiction are mapped -- EUR is deliberately absent (shared by
#: many Eurozone countries; never guessed). An explicit 3-letter code
#: (e.g. "CAD" appearing in the document) is unambiguous on its own. A bare
#: currency SYMBOL is only trusted when it is the ONLY symbol/code present
#: anywhere in the document -- "$" alone (no other currency marker) is
#: read as USD, the same default this codebase's own parsers already use
#: everywhere a currency isn't otherwise stated (see budget_parser.py).
_CURRENCY_CODE_TO_JURISDICTION_CODE = {"USD": "US", "CAD": "CA", "GBP": "GB", "AUD": "AU"}
_CURRENCY_SYMBOL_TO_MARKER = {"$": "USD", "£": "GBP", "€": None}  # None = deliberately ambiguous
_CURRENCY_CODE_RE = re.compile(r"\b(USD|CAD|GBP|AUD|EUR)\b")


def _infer_jurisdiction_code_from_currency(raw_text: str) -> str | None:
    """Deterministic, never-fabricated currency->jurisdiction inference
    from a budget document's own extracted text. Returns None (never a
    guess) whenever more than one currency marker is present, or the only
    marker present (EUR / "€") is shared by multiple real jurisdictions."""
    if not raw_text:
        return None
    codes_found = {m.group(1) for m in _CURRENCY_CODE_RE.finditer(raw_text)}
    if len(codes_found) == 1:
        code = next(iter(codes_found))
        return _CURRENCY_CODE_TO_JURISDICTION_CODE.get(code)  # None for EUR — ambiguous
    if len(codes_found) > 1:
        return None  # more than one currency code stated — genuinely ambiguous

    markers_found = {
        marker for symbol, marker in _CURRENCY_SYMBOL_TO_MARKER.items() if symbol in raw_text
    }
    if len(markers_found) == 1:
        only = next(iter(markers_found))
        return _CURRENCY_CODE_TO_JURISDICTION_CODE.get(only) if only else None
    return None  # no marker, or more than one distinct symbol present


async def _resolve_home_jurisdiction(
    session: AsyncSession, project: Project, budget_doc: BudgetDocument,
    *, persist: bool = True,
) -> Jurisdiction | None:
    """The ONE canonical base-jurisdiction resolver for the live Evaluate
    path. Precedence (never fabricated, never overrides an explicit value):

      1. An already-confirmed project.home_jurisdiction_id (explicit
         project-level fact/override — highest precedence, untouched).
      2. A real jurisdiction NAME stated in the project's own budget
         document filename(s) — reuses project_evaluation._derive_home_
         jurisdiction's existing, already-built, deterministic matcher
         unchanged (the same generic logic that already resolves F#K
         Valentine's Day's real "...Greece..." budget filename); never a
         second, competing name-matching implementation.
      3. The currency the budget document is itself denominated in —
         genuinely new (no existing currency-detection capability was
         found), deliberately minimal, and only ever resolves when
         unambiguous (see _infer_jurisdiction_code_from_currency).

    Only reached once a BudgetDocument is guaranteed to exist (the caller
    ingests it first) — a Jurisdiction resolved here is persisted onto
    project.home_jurisdiction_id plus a ProjectFact (source_type=EXTRACTED,
    linked to the budget's own DocumentVersion for provenance) so the
    derivation is never silently re-run or lost, and is clearly
    distinguishable from a real user-confirmed answer."""
    # BASELINE PROVENANCE. A CONFIRMED baseline fact outranks the stored
    # column. project.home_jurisdiction_id can hold a low-confidence EXTRACTED
    # derivation -- notably the currency fallback, which resolves USD to the
    # COUNTRY "US". A federal country whose production incentives are
    # subnational can never itself be a real production baseline, so that
    # value both mis-states the baseline AND, once persisted, short-circuited
    # this resolver forever so better evidence could never supersede it.
    # A producer-stated home_jurisdiction_code fact (USER_OVERRIDE, the
    # same precedence contingency and financing assumptions already use) is
    # authoritative and may name a SUBNATIONAL jurisdiction.
    confirmed = (await session.execute(
        select(ProjectFact).where(
            ProjectFact.project_id == project.id,
            ProjectFact.fact_key == "home_jurisdiction_code",
            # source_type is stored in mixed representations across the
            # corpus (the enum member, its NAME, and its value all occur), so
            # match every spelling rather than silently missing a real
            # producer-stated fact.
            ProjectFact.source_type.in_((
                ProjectFactSourceType.USER_OVERRIDE,
                ProjectFactSourceType.USER_OVERRIDE.name,
                ProjectFactSourceType.USER_OVERRIDE.value,
            )),
        )
    )).scalars().first()
    if confirmed is not None and confirmed.value:
        confirmed_jurisdiction = (await session.execute(
            select(Jurisdiction).where(Jurisdiction.code == confirmed.value)
        )).scalars().first()
        if confirmed_jurisdiction is not None:
            if persist and project.home_jurisdiction_id != confirmed_jurisdiction.id:
                project.home_jurisdiction_id = confirmed_jurisdiction.id
                await session.commit()
                await session.refresh(project)
            return confirmed_jurisdiction

    if project.home_jurisdiction_id is not None:
        return await session.get(Jurisdiction, project.home_jurisdiction_id)

    from app.services.project_evaluation import _derive_home_jurisdiction as _match_by_filename

    resolved = await _match_by_filename(session, project)
    source_label = "budget_filename" if resolved is not None else None

    if resolved is None:
        from pathlib import Path

        from app.core.config import get_settings
        from app.ingestion.pdf_extractor import extract_text_from_pdf

        settings = get_settings()
        local_path = Path(settings.LOCAL_STORAGE_PATH) / (budget_doc.storage_path or "")
        if budget_doc.file_type == "pdf" and local_path.exists():
            raw_text = extract_text_from_pdf(local_path).raw_text
            code = _infer_jurisdiction_code_from_currency(raw_text)
            if code:
                resolved = (await session.execute(
                    select(Jurisdiction).where(Jurisdiction.code == code)
                )).scalars().first()
                source_label = "budget_currency" if resolved is not None else None

    if resolved is None:
        return None

    # READ PURITY: a GET/read may reconstruct the derivation in memory to
    # rebuild an input fingerprint, but must never persist it. Assigning
    # project.home_jurisdiction_id would mark the ORM object dirty and let
    # an unrelated later commit flush it, so the assignment itself is
    # skipped -- not merely the commit.
    if not persist:
        return resolved

    project.home_jurisdiction_id = resolved.id
    # ProjectFact holds exactly ONE current row per (project_id, fact_key)
    # by its own documented design (and a real DB unique constraint) —
    # update an existing derivation fact in place rather than blindly
    # inserting a second one (which would violate that constraint if a
    # prior derivation, or a since-reverted one, already wrote this key).
    existing_fact = (await session.execute(
        select(ProjectFact).where(
            ProjectFact.project_id == project.id, ProjectFact.fact_key == "home_jurisdiction_code",
        )
    )).scalars().first()
    if existing_fact is not None:
        existing_fact.value = resolved.code
        existing_fact.source_type = ProjectFactSourceType.EXTRACTED
        existing_fact.source_document_version_id = budget_doc.document_version_id
        existing_fact.source_location = f"derived from {source_label}"
    else:
        session.add(ProjectFact(
            id=uuid.uuid4(), project_id=project.id, fact_key="home_jurisdiction_code",
            value=resolved.code, value_type="string",
            source_type=ProjectFactSourceType.EXTRACTED,
            source_document_version_id=budget_doc.document_version_id,
            source_location=f"derived from {source_label}",
        ))
    await session.commit()
    await session.refresh(project)
    return resolved


async def build_project_economic_inputs(
    session: AsyncSession, project_id, *, read_only: bool = False,
) -> EconomicInputsResult:
    """Assemble canonical economic inputs for any project from persisted
    evidence. Returns blockers rather than a degraded input set.

    read_only=True makes this builder SIDE-EFFECT FREE, for callers that
    serve a GET/read (canonical_production_view, project_workspace_view).
    Those views reconstruct the current input fingerprint on read; before
    this flag existed they reached the same write-capable recovery this
    function performs for the evaluation path, so a page load could route a
    budget, set project.home_jurisdiction_id, insert/update a ProjectFact
    and commit. A read must never mutate project state.

    Under read_only the two recovery steps are skipped rather than
    silently substituted: an unrouted budget yields the honest
    BUDGET_MISSING blocker instead of being routed and persisted, and home
    jurisdiction is resolved in memory only. Write-time normalization
    still happens exactly where it belongs -- the explicit
    evaluate/write workflow, which calls this with the default
    read_only=False."""
    blockers: list[str] = []

    project = await session.get(Project, project_id)
    if project is None:
        return EconomicInputsResult(None, ["Project not found."])

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
        if not read_only:
            from app.services.material_routing import ensure_current_budget_routed
            doc = await ensure_current_budget_routed(session, project_id)
    if doc is None:
        blockers.append(
            "BUDGET_MISSING — no parsed budget document is attached. The "
            "canonical engine prices an actual budget; it does not estimate one."
        )
        return EconomicInputsResult(None, blockers)

    # Fresh Project Ingestion, base-jurisdiction derivation: the jurisdiction
    # in which the production budget is set is the canonical base
    # jurisdiction unless an explicit project-level fact overrides it. Run
    # AFTER the budget doc above is guaranteed to exist (ingested if
    # necessary), so the derivation always has real budget evidence to read
    # rather than racing ahead of it. Never overrides an already-confirmed
    # project.home_jurisdiction_id.
    jurisdiction = await _resolve_home_jurisdiction(
        session, project, doc, persist=not read_only,
    )
    if jurisdiction is None:
        blockers.append(
            "BASE_JURISDICTION_UNKNOWN — the production's base jurisdiction is "
            "not confirmed on the project. It is not defaulted; supply it "
            "explicitly or let evaluation derive it from source evidence."
        )

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
        if match is not None:
            code, label = match.group(1), match.group(2).strip()
        else:
            # Canonical Budget Parser Remediation (Codex BPI-001): a real,
            # unnumbered top-sheet loaded-cost line (e.g. Bad Hombres' own
            # "CONTINGENCY : 5.0%" -> persisted description "CONTINGENCY")
            # has no leading numeric account code by construction — see
            # budget_parser.py's _LOADED_COST_PCT_RE, which registers it
            # under its own real label text, never a synthetic code. The
            # parser correctly preserves this line; excluding it HERE was
            # the exact downstream handoff defect Codex found — gross
            # budget included it, but allocation/evaluation never saw it.
            # Fixed by using the line's own stable label text as its
            # account_code (identical convention the parser itself already
            # uses to register it) — never invented, never merged with a
            # numeric code, and the line's real persisted UUID (line_id)
            # remains its true per-line identity either way.
            if not description.strip():
                unparsed.append(description)
                continue
            code, label = description.strip(), description.strip()
        amount = float(item.amount_usd) if item.amount_usd is not None else 0.0
        leaf_sum += amount
        category = getattr(item.spend_category, "value", item.spend_category)
        # Codex BPI-002: account_code is a CLASSIFICATION field, never a
        # unique key (real budgets legitimately reuse a code across
        # distinct lines — see BudgetLine's own docstring). A later row
        # sharing an earlier row's code must never overwrite this shared
        # fallback map — first-registered wins here; the AUTHORITATIVE
        # per-line category is always the one carried on this line's own
        # BudgetLine.spend_category (see line_id-keyed usage downstream),
        # this dict is only ever a fallback for a line with none of its
        # own.
        if category and code not in spend_category_by_code:
            spend_category_by_code[code] = category
        lines.append(BudgetLine(
            account_code=code, description=label, amount_usd=amount,
            spend_category=category, is_memo=False, line_id=str(item.id),
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
        financing_cost_usd=_fact_float(fact_rows, FACT_FINANCING_COST_USD),
        # Financing ALREADY inside the source gross budget. Derived from the
        # normalized lines' own canonical category, so it follows the source
        # document rather than a per-production assumption.
        source_budget_finance_usd=round(sum(
            float(line.amount_usd or 0.0)
            for line in items
            if str(getattr(line, "spend_category", "") or "").lower().endswith("finance_costs")
        ), 2),
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


# ─────────────────────────────────────────────────────────────────────────
# Script Analyzer Full Production Breakdown — UI-facing location category
# chips (ProductionDetails.jsx's "Major Location Requirements").
#
# canonical_production_view.py's generic (non-demo) `production` dict
# hardcoded `physical_requirements: {}` for every project — Overview
# showed "No script analysis available yet" regardless of how many real
# ProjectLocationRequirement rows a project actually has. The demo-only
# `little_utopia_state._derive_location_categories()` produces the exact
# shape ProductionDetails.jsx needs ({slug: {label, script_value,
# evidence, override, effective, source}}) but reads LU's own hardcoded
# fixture data. This is the generic, per-project counterpart: same output
# CONTRACT, same LOCATION_TAXONOMY vocabulary and label text (imported,
# never redefined — one taxonomy, not a second one), but every value
# comes from this project's own real, persisted SA-1 rows.
#
# abstract_location()'s own raw keyword-ontology output (beach_coast,
# marine_open_water, island, tropical_environments, forest_environments,
# desert_environments, mountain_environments, snow_environments,
# urban_environments, town, village, rural_environments,
# historic_architecture, ...) uses a DIFFERENT slug vocabulary than the
# UI's LOCATION_TAXONOMY (13 producer-facing category labels) — the SAME
# kind of small, explicit translation table
# _LOCATION_CAPABILITY_TOKEN_TO_CATEGORY_KEY above already uses to bridge
# abstract_location() into derive_production_requirements()'s own
# vocabulary. This is that same precedented pattern, not a new ontology:
# bridging two ALREADY-EXISTING vocabularies, never inventing a category
# concept that doesn't already exist in one of them.
_LOCATION_ONTOLOGY_TOKEN_TO_TAXONOMY_SLUG: dict[str, str] = {
    "beach_coast": "beach_coast",
    "marine_open_water": "marine_open_water",
    "island": "island_tropical",
    "tropical_environments": "island_tropical",
    "forest_environments": "forest_woodland",
    "desert_environments": "desert_arid",
    "mountain_environments": "mountains_alpine",
    "snow_environments": "snow_arctic",
    "urban_environments": "urban_major_city",
    "town": "small_town_suburban",
    "village": "small_town_suburban",
    "rural_environments": "rural_countryside",
    "historic_architecture": "historic_old_world",
    # harbor_marina, river, lake, mediterranean, coastal_environments,
    # open_water_filming, tropical (alone), agricultural, industrial,
    # residential, period_environments: no LOCATION_TAXONOMY slug exists
    # for these — correctly excluded, never forced into an unrelated
    # category.
}


async def build_ui_location_categories(session: AsyncSession, project_id) -> dict[str, dict]:
    """The real, per-project `location_categories` shape
    ProductionDetails.jsx renders — same contract as the demo's
    `_derive_location_categories()`, same `LOCATION_TAXONOMY` labels
    (imported unchanged), built from this project's own persisted SA-1
    `ProjectLocationRequirement` (scripted locations) rows and any real
    producer-confirmed category overrides already persisted on the SAME
    table (`category_key`/`override` rows — Phase C's existing override
    write path, `POST /locations`). Every taxonomy slug is always
    present (matching the demo's own always-13-slugs contract) —
    `effective=False`/`evidence=None` for a category the script genuinely
    never evidences, never omitted."""
    # Shared, non-demo home (app.calculators.production_requirements) — never
    # app.demo.little_utopia_state; this module must stay project-agnostic.
    from app.calculators.production_requirements import LOCATION_TAXONOMY
    from app.models.project_location_requirement import ProjectLocationRequirement

    rows = (await session.execute(
        select(ProjectLocationRequirement).where(ProjectLocationRequirement.project_id == project_id)
    )).scalars().all()
    scripted_descriptions = [r.description for r in rows if r.category_key is None and r.description]
    overrides = {r.category_key: r.override for r in rows if r.category_key is not None}

    evidence_by_slug: dict[str, list[str]] = {}
    for desc in scripted_descriptions:
        for token in abstract_location(desc):
            slug = _LOCATION_ONTOLOGY_TOKEN_TO_TAXONOMY_SLUG.get(token)
            if slug is None:
                continue
            evidence_by_slug.setdefault(slug, []).append(desc)

    out: dict[str, dict] = {}
    for slug, label in LOCATION_TAXONOMY.items():
        evidence_list = evidence_by_slug.get(slug)
        script_value = bool(evidence_list) if evidence_list else None
        override = overrides.get(slug)
        effective = override if override is not None else bool(script_value)
        out[slug] = {
            "label": label,
            "script_value": script_value,
            "evidence": (
                ", ".join(sorted(set(evidence_list))[:3]) if evidence_list
                else "Not described in the material read."
            ),
            "override": override,
            "effective": effective,
            "source": "user_override" if override is not None else "script_analysis",
        }
    return out
