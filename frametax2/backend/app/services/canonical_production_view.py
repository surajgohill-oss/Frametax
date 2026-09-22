"""
canonical_production_view.py

The view adapter behind the RESTORED mature CineGlobe production UI
(Overview/Workspace/Scenarios/ProjectGlobe/Reports/Knowledge — the rich
pre-regression component tree, /projects/{id}/overview etc.), generalized
to any project_id.

Reshapes ProductionStructure / StructureCalculationResult — the SAME
canonical-1.1.0 persisted rows canonical_evaluation.py commits, already
proven to reproduce Little Utopia's exact accepted NPC ($3,057,794.90) —
into the `production` / `structures.allocated_structures` shape those
mature components already read (built against
`app/demo/little_utopia_state.py::build_allocated_structures` /
`get_production`). Computes NO economics; every number here is read
straight off an already-committed StructureCalculationResult row.

Fields the persisted engine does not compute generically yet (per-account
allocation assignments, conditional funding programs, structure
compatibility, a written recommendation) are served as honest empty
values (`[]` / `{}` / `null`), never fabricated — the same "if data is
absent, show the appropriate empty state" principle already established
for the Script/Documents tabs in project_workspace_view.py. This is a
disclosed, structural gap (deep per-segment drill-downs render fewer
details generically than Little Utopia's own richer, unchanged
/api/v1/cineglobe/production|structures endpoints), not a defect.
"""
from __future__ import annotations

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.executable_jurisdiction_registry import get_doctrine
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.jurisdiction import Jurisdiction
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.production_requirement import ProductionRequirement
from app.models.project import Project
from app.models.project_asset import ProjectAsset
from app.models.project_fact import ProjectFact
from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile
from app.services.economic_identity import canonical_economic_identity
from app.services.canonical_evaluation import (
    ENGINE_VERSION,
    UNPRICEABLE_PAGE_DEFAULT_LIMIT,
    UNPRICEABLE_PAGE_ORDER,
    UNPRICEABLE_RESULTS_ROUTE,
    _QUALIFICATION_ADMITS_PRICING,
    _QUALIFICATION_ADMITS_RECOMMENDED,
    _RELOCATION_DIMENSIONS,
    GenerationSummaryUnavailable,
    load_generation_summary,
    load_retained_rows,
    candidate_aggregates_block,
    candidate_groups_page,
    summary_totals,
    unpriceable_page,
)

from app.services.candidate_retention import (  # noqa: E402
    GLOBAL_TOP,
    LOCAL_STACK_TYPES,
    TYPE_TOP,
)

RETENTION_POLICY_NOTE = (
    "Enumeration cardinality never defines persistence cardinality: every candidate is evaluated, but only "
    "the bounded decision set is a detailed row. Counts are exact (retained rows + aggregate groups)."
)

# Producer-facing optimizer projection.  The exhaustive optimizer collections remain
# untouched for auditability; ordinary UI surfaces receive only executable, bilateral
# decisions that improve the production's own persisted current-location NPC by more
# than this amount.
MIN_PRODUCER_SAVINGS_USD = 100_000.0


def _economic_jurisdictions(entry: dict) -> set[str]:
    """Return the jurisdictions that participate in this candidate's economics."""
    jurisdictions = {c for c in (entry.get("participants") or []) if c}
    jurisdictions.update(
        r.get("jurisdiction_code")
        for r in (entry.get("component_allocations") or [])
        if r.get("jurisdiction_code")
    )
    if entry.get("primary_jurisdiction"):
        jurisdictions.add(entry["primary_jurisdiction"])
    return jurisdictions


def _single_jurisdiction_winners(entries: list[dict], identity_by_structure: dict[str, str]) -> dict[str, dict]:
    """Choose one lowest-verified-NPC priced candidate per economic jurisdiction."""
    eligible = []
    for entry in entries:
        primary = entry.get("primary_jurisdiction")
        if (
            entry.get("candidate_status") != "PRICED"
            or not entry.get("is_fully_priced")
            or entry.get("structure_type") not in LOCAL_STACK_TYPES
            or not primary
            or _economic_jurisdictions(entry) != {primary}
        ):
            continue
        eligible.append(entry)
    eligible.sort(key=lambda e: (
        e.get("npc_verified_usd") if e.get("npc_verified_usd") is not None else float("inf"),
        identity_by_structure.get(e.get("structure_id"), ""),
    ))
    winners: dict[str, dict] = {}
    for entry in eligible:
        winners.setdefault(
            entry["primary_jurisdiction"],
            {**entry, "economic_identity": identity_by_structure.get(entry["structure_id"])},
        )
    return winners


def _producer_decision_key(entry: dict) -> tuple:
    routes = {
        (
            row.get("component") or row.get("category"),
            row.get("jurisdiction_code"),
            row.get("program_slug"),
        )
        for row in (entry.get("component_allocations") or [])
    }
    return (
        entry.get("primary_jurisdiction"),
        tuple(sorted(routes, key=lambda r: tuple(v or "" for v in r))),
        entry.get("treaty_slug") if entry.get("classification") == "OFFICIAL_COPRODUCTION" else None,
    )


def _build_producer_optimizer_projection(
    optimizer_scenarios: list[dict], baseline_entry: dict | None,
) -> tuple[list[dict], dict[str, int], float | None]:
    """Filter exhaustive scenarios into practical, material producer decisions."""
    baseline_npc = (baseline_entry or {}).get("npc_with_adjustments_usd")
    excluded: dict[str, int] = {}

    def reject(reason: str) -> None:
        excluded[reason] = excluded.get(reason, 0) + 1

    if baseline_npc is None:
        if optimizer_scenarios:
            excluded["MISSING_CANONICAL_BASELINE"] = len(optimizer_scenarios)
        return [], excluded, None

    candidates: list[dict] = []
    for entry in optimizer_scenarios:
        classification = entry.get("classification")
        jurisdictions = _economic_jurisdictions(entry)
        candidate_npc = entry.get("npc_with_adjustments_usd")
        if entry.get("candidate_status") != "PRICED" or not entry.get("is_fully_priced") or candidate_npc is None:
            reject("NOT_FULLY_PRICED_EXECUTABLE")
            continue
        if len(jurisdictions) != 2:
            reject("NOT_BILATERAL")
            continue
        if classification == "HYBRID_ANCHOR_COMPONENT":
            option_type = "PRACTICAL_HYBRID"
            routes = entry.get("component_allocations") or []
            if not routes or any(
                not row.get("component") or not row.get("jurisdiction_code") or not row.get("program_slug")
                for row in routes
            ):
                reject("INCOMPLETE_CANONICAL_IDENTITY")
                continue
        elif classification == "OFFICIAL_COPRODUCTION":
            option_type = "FORMAL_COPRODUCTION"
            if (
                not entry.get("treaty_slug")
                or entry.get("treaty_resolution_state") != "ELIGIBLE"
                or entry.get("treaty_disqualification_reasons")
                or (entry.get("treaty_cultural_test_required") and not entry.get("treaty_cultural_test_resolved"))
                or entry.get("personnel_gate_state") not in (None, "QUALIFIES", "NOT_APPLICABLE")
            ):
                reject("FORMAL_COPRODUCTION_NOT_FULLY_QUALIFIED")
                continue
        else:
            reject("UNSUPPORTED_PRODUCER_STRUCTURE")
            continue
        if not entry.get("structure_id") or not entry.get("economic_identity") or not entry.get("primary_jurisdiction"):
            reject("INCOMPLETE_CANONICAL_IDENTITY")
            continue
        savings = float(baseline_npc) - float(candidate_npc)
        if savings <= MIN_PRODUCER_SAVINGS_USD:
            reject("SAVINGS_NOT_ABOVE_100K")
            continue
        candidates.append({
            **entry,
            "producer_optimizer_baseline_npc_usd": float(baseline_npc),
            "producer_optimizer_candidate_npc_usd": float(candidate_npc),
            "savings_vs_current_usd": savings,
            "producer_optimizer_jurisdiction_count": 2,
            "producer_optimizer_option_type": option_type,
        })

    candidates.sort(key=lambda e: (
        0 if e["producer_optimizer_option_type"] == "PRACTICAL_HYBRID" else 1,
        -e["savings_vs_current_usd"],
        e["producer_optimizer_candidate_npc_usd"],
        e.get("economic_identity") or "",
    ))
    unique: dict[tuple, dict] = {}
    for entry in candidates:
        key = _producer_decision_key(entry)
        if key in unique:
            reject("DUPLICATE_PRODUCER_DECISION")
            continue
        unique[key] = entry
    return list(unique.values()), excluded, float(baseline_npc)

#: Codex final P0 (GLOBAL_INCENTIVE_FINAL_REMAINING_ITEMS_CODEX.csv,
#: PART C / leading conditional recommendation) -- the qualification
#: states that are BOTH priced (_QUALIFICATION_ADMITS_PRICING) AND NOT
#: already resolved (_QUALIFICATION_ADMITS_RECOMMENDED): CURABLE_GAP,
#: USER_FACT_REQUIRED, SCRIPT_FACT_REQUIRED, AUTHORITY_UNRESOLVED,
#: RULE_DATA_INCOMPLETE. Each of these names a real, evidence-based,
#: genuinely UNLOCKABLE reason a candidate cannot yet be recommended --
#: never a hard ineligibility (QUAL_HARD_FAIL is excluded entirely from
#: _QUALIFICATION_ADMITS_PRICING and so never reaches this set) and never
#: the SEPARATE, permanent, program-level authority-insufficient veto
#: (candidate_status STATUS_UNPRICEABLE_AUTHORITY_INSUFFICIENT is
#: is_fully_priced=False, structurally excluded from this pool already --
#: see _recommendation_category's own docstring for why that is a
#: DIFFERENT "authority" concept from QUAL_AUTHORITY_UNRESOLVED).
_CONDITIONAL_ELIGIBLE_QUALIFICATION_STATES = frozenset(
    _QUALIFICATION_ADMITS_PRICING - _QUALIFICATION_ADMITS_RECOMMENDED
)

REC_VERIFIED_RECOMMENDATION = "VERIFIED_RECOMMENDATION"
REC_LEADING_CONDITIONAL = "LEADING_CONDITIONAL"
REC_UNLOCKABLE_ALTERNATIVE = "UNLOCKABLE_ALTERNATIVE"
REC_REJECTED = "REJECTED"
REC_AUTHORITY_UNRESOLVED_FAIL_CLOSED = "AUTHORITY_UNRESOLVED_FAIL_CLOSED"

# Production Page Integrity: the SAME leading-account-code convention
# canonical_project_economics.py's own _ACCOUNT_CODE_RE already uses to
# derive the priced register's line identity — reused here unchanged so
# the budget-composition drill-down's account codes are never a second,
# differently-parsed identity for the same real line.
_ACCOUNT_CODE_RE = re.compile(r"^\s*(\d{3,6})\s+(.*)$")


def _anchor_and_stacked(trace: dict) -> tuple[str | None, list[str]]:
    """Rich structure semantics: which claimed program is the ANCHOR
    (principal program for the structure) vs which are STACKED (compatible
    additional programs combined with it) — never a flat, order-
    ambiguous list. Single-program structures have one program and no
    stack. For a canonical_stack_bridge combination, the anchor is
    whichever program retained the greater post-stacking value
    (per_program_adjusted_usd, already computed by apply_stacking_
    adjustments — no new economics here); the other is the stacked
    program. This is a display ordering only; both remain in
    claimed_program_ids/program_slugs regardless of which is anchor."""
    slugs = trace.get("program_slugs") or ([trace.get("program_slug")] if trace.get("program_slug") else [])
    if not slugs:
        return None, []
    if len(slugs) == 1:
        return slugs[0], []
    per_program = trace.get("per_program_adjusted_usd") or {}
    ranked = sorted(slugs, key=lambda s: per_program.get(s, 0.0), reverse=True)
    return ranked[0], ranked[1:]


def _with_component_display_names(
    component_allocations: list, jurisdiction_name_by_code: dict[str, str] | None,
) -> list:
    """Backfill a component allocation's producer-facing jurisdiction name at
    serve time. A persisted trace can carry None (the target jurisdiction had
    no seeded Jurisdiction row when it was written); the producer must still
    never see a raw code."""
    from app.services.canonical_program_identity import canonical_jurisdiction_name

    names = jurisdiction_name_by_code or {}
    healed = []
    for allocation in component_allocations:
        if not isinstance(allocation, dict):
            healed.append(allocation)
            continue
        if allocation.get("jurisdiction_display_name"):
            healed.append(allocation)
            continue
        code = allocation.get("jurisdiction_code")
        resolved = names.get(code) or canonical_jurisdiction_name(code)
        healed.append({**allocation, "jurisdiction_display_name": resolved} if resolved else allocation)
    return healed


def _humanize_structure_label(
    name: str | None, jurisdiction_name_by_code: dict[str, str] | None,
) -> str | None:
    """Producer-facing structure label. Backend-authored ProductionStructure
    names embed raw jurisdiction codes and program slugs -- "Full relocation to
    CA-MB", "US anchor - post routed to CA-MB", "CA-ON - ca_federal_cptc +
    on_ofttc (combined)". Those reach the Inspector and sidebars verbatim.

    Rewritten at SERVE time from the SAME canonical display metadata the rest
    of the view uses (jurisdiction names resolved canonically, program names
    from the doctrine registry), so nothing is hand-maintained and rows
    persisted before this heal too. Codes/slugs with no canonical name are
    left exactly as they are rather than prettified into a guess.
    """
    if not name:
        return name
    names = jurisdiction_name_by_code or {}
    out = name
    # Program slugs first (they can contain characters that also look like
    # jurisdiction codes), longest first so a prefix never shadows a longer id.
    for slug in sorted(set(re.findall(r"[a-z][a-z0-9_]{3,}", out)), key=len, reverse=True):
        display = _program_display_name(slug)
        if display:
            out = out.replace(slug, display)
    for code in sorted(names, key=len, reverse=True):
        display = names.get(code)
        if display and code in out:
            out = re.sub(rf"(?<![A-Za-z0-9-]){re.escape(code)}(?![A-Za-z0-9-])", display, out)
    return out


def _jurisdiction_names_by_code(jurisdictions) -> dict[str, str]:
    """Producer-facing jurisdiction names, DB first with a CANONICAL
    fallback -- never a raw code on a producer surface.

    The Jurisdiction table is the primary source, but a jurisdiction can be
    canonically modeled (a DoctrineRecord and rate rules exist, so it is
    discovered and priced) without ever having been seeded as a row -- AE-AD,
    AE-DXB and AU-SA are the current instances. Those codes then reached
    producer surfaces raw, e.g. a component/split candidate routing post to
    "AE-AD". jurisdiction_comparison.ALL_PROFILES already carries the real
    display name for exactly these codes, so this reads the existing
    canonical metadata rather than introducing a second hand-maintained
    name map (which is what PROJECT_RULES.md forbids and what would drift).
    """
    from app.calculators import jurisdiction_comparison as jc
    from app.services.canonical_program_identity import canonical_jurisdiction_name

    names = {}
    for code in jc.ALL_PROFILES:
        resolved = canonical_jurisdiction_name(code)
        if resolved:
            names[code] = resolved
    # A seeded Jurisdiction row is authoritative and always wins.
    names.update({j.code: j.name for j in jurisdictions if j.name})
    # F#K Valentine's Day economic/semantic regression fix (2026-09-03),
    # item 4a: both sources above can carry a composite "Country —
    # Subnational" registry name (e.g. "Canada — Manitoba") -- the real,
    # correct registry identity, but never the producer-facing form. A
    # structure's own name-substitution in _humanize_structure_label
    # embedded this raw composite string verbatim ("Full relocation to
    # Canada — Manitoba"), duplicating the same defect the frontend's
    # bestJurisdictionName already fixed for its own callers (see
    # lib/format.jsx) -- but this backend map feeds a DIFFERENT surface
    # (Project Globe's structure list) that never routes through the
    # frontend helper. Trimming to the most specific (last) segment HERE,
    # at the one canonical name-resolution point every code substitution
    # in a structure's label goes through, fixes it everywhere at once --
    # never a per-string patch, never a per-jurisdiction special case.
    return {code: (name.split(" — ")[-1] if name else name) for code, name in names.items()}


def _program_display_name(program_slug: str | None) -> str | None:
    """The real, human-readable program name from the canonical doctrine
    registry (executable_jurisdiction_registry.get_doctrine) — never a
    frontend-hardcoded map, never the raw slug. None for no slug or a
    slug with no registered doctrine record (never fabricated)."""
    if not program_slug:
        return None
    doctrine = get_doctrine(program_slug)
    return doctrine.program_name if doctrine else None


#: GD-2 (Globe data contract remediation, 2026-09-20): the classification
#: constants and derivation formerly lived only in this module. They are
#: now canonically owned by app/services/structural_classification.py
#: (imported by canonical_evaluation.py at candidate-creation time too, so
#: the value is part of the persisted contract, not solely serve-time
#: projection logic) -- re-exported here under the SAME names so every
#: existing `cpv.CLASS_*` / `cpv.STRUCTURE_CLASSIFICATIONS` reference in
#: this module and in tests is unaffected.
from app.services.structural_classification import (  # noqa: E402
    CLASS_AUTHORITY_LOCKED,
    CLASS_COMBINED_COPRO_HYBRID_STACK,
    CLASS_CONDITIONAL_USER_FACT_REQUIRED,
    CLASS_HYBRID_ANCHOR_COMPONENT,
    CLASS_MULTI_PRINCIPAL_MULTILATERAL,
    CLASS_OFFICIAL_COPRODUCTION,
    CLASS_REJECTED_FOR_PROJECT,
    CLASS_RULE_DATA_INCOMPLETE,
    CLASS_SINGLE_JURISDICTION,
    CLASS_STACKED_PROGRAMS,
    OPTIMIZER_STRUCTURE_FAMILIES as _OPTIMIZER_STRUCTURE_FAMILIES,
    PRICED_STRUCTURE_FAMILIES as _PRICED_STRUCTURE_FAMILIES,
    STRUCTURE_CLASSIFICATIONS,
    classify_structure as _classify_structure,
)


def _structure_classification(
    trace: dict, structure_type: str, is_priced: bool,
) -> str:
    """Serves the canonical classification. GD-2: prefers the value
    app/services/canonical_evaluation.py already stamped onto
    calculation_trace_json["structural_classification"] at candidate-
    creation time (the SAME value retention's per-family lane and
    aggregation's per-family dominator reconciliation consume) -- only
    calling the shared live derivation (app.services.structural_
    classification.classify_structure, identical logic) for the small
    number of historical rows generated before this field existed, the
    same graceful-degradation precedent already used throughout this
    module for structure_type/selected_incentive_usd/etc."""
    persisted = trace.get("structural_classification")
    if persisted in STRUCTURE_CLASSIFICATIONS:
        return persisted
    return _classify_structure(trace, structure_type, is_priced)


def _empty_structure_entry(
    structure, result, jurisdiction_code_by_id: dict[str, str],
    jurisdiction_name_by_code: dict[str, str] | None = None,
) -> dict:
    trace = result.calculation_trace_json or {}
    is_priced = trace.get("candidate_status") == "PRICED"
    allocs = structure.jurisdiction_allocations or []
    code = trace.get("primary_jurisdiction") or (
        jurisdiction_code_by_id.get(allocs[0].get("jurisdiction_id")) if allocs else None
    )
    if code is None and structure.name and structure.name.startswith("Full relocation to "):
        # Unpriceable candidates never get a jurisdiction_allocations row
        # (no allocation is built for an authority-insufficient jurisdiction)
        # — same gap and same display-only fix as project_workspace_view.py.
        code = structure.name.removeprefix("Full relocation to ").strip() or None
    # Ingestion acceptance closeout, structure_type persistence (2026-09-17):
    # prefer the real, persisted StructureCalculationResult.structure_type
    # column (backfilled via migration 0075 for every pre-existing row, and
    # written by evaluate_project() at the same construction site as the
    # trace's own value on every row since) — never a second, independently
    # re-derived value. Falls back to the trace_json field, then the
    # is_baseline-derived guess, ONLY for the small number of historical
    # rows from engine versions that predate both migration 0075's backfill
    # source data and the trace_json "structure_type" key ever existing
    # (confirmed live: exactly the retired canonical-1.0.0/0.1.0/demo-
    # runtime rows, never the current engine_version) — same graceful-
    # degradation precedent as selected_incentive_usd immediately below.
    structure_type = result.structure_type or trace.get("structure_type") or (
        "single_country" if trace.get("is_baseline") else "full_relocation"
    )
    # selected_incentive_usd: prefer the persisted StructureCalculationResult
    # column (total_incentive_value_usd — always populated for a priced
    # result, on every engine_version) over the trace_json field (only
    # present on rows generated since the segments/incentive enrichment
    # added below) so this renders correctly without requiring every
    # already-evaluated project to be re-evaluated first.
    selected_incentive_usd = (
        float(result.total_incentive_value_usd) if result.total_incentive_value_usd is not None
        else trace.get("selected_incentive_usd")
    ) if is_priced else None
    # Existing Optimizer/Stacker Reconnection, Task C (hybrid/anchor) —
    # HYBRID does not inherently mean TREATY: every structure's real
    # relationship composition is represented as independent flags,
    # computed from data already present on this SAME trace (no new
    # generation, no second taxonomy). A structure may carry more than
    # one simultaneously (e.g. a treaty_coproduction opportunity that
    # ALSO has conditional_programs attached is "coproduction" +
    # "conditional_fund" at once) — the frontend never has to infer this
    # from structure_type alone.
    relationship_types: list[str] = []
    if (trace.get("program_slugs") or []).__len__() > 1 and structure_type == "multi_program":
        relationship_types.append("stack")
    if trace.get("component_allocations"):
        relationship_types.append("component")
    if trace.get("treaty_slug"):
        relationship_types.append("coproduction")
    if trace.get("conditional_programs"):
        relationship_types.append("conditional_fund")

    # Canonical optimizer/Globe wiring remediation (2026-09-04), P0-3:
    # `participants` used to be hardcoded to the primary jurisdiction
    # alone -- confirmed by the Codex four-project audit as a defect
    # affecting all 836 component/treaty structures (740 component + 96
    # treaty), collapsing e.g. "Greece + Romania" to bare "Greece" at
    # this exact API boundary and corrupting every downstream consumer
    # (title/flags, selection, Globe, Inspector, Reports). Fixed
    # generically from the SAME real persisted trace data every other
    # field on this entry already reads -- never parsed from the
    # free-text label, never derived in the frontend (which cannot see
    # data this API boundary already dropped):
    #   - segments[].jurisdiction_code: the real per-jurisdiction
    #     allocation for single/full_relocation/component_relocation
    #     structures (a component's routed destination is its own real
    #     segment).
    #   - coproduction_partners[].jurisdiction_code: the real treaty
    #     partner for treaty_coproduction opportunities (which persist
    #     jurisdiction_allocations=[] at generation time and so have no
    #     segments to read).
    # Order preserved (primary first), deduplicated, never fabricated --
    # a structure with no additional real jurisdiction on file still
    # participates as [primary] alone, exactly as before.
    # coproduction_partners carries THREE distinct real shapes (see
    # canonical_evaluation.py's treaty-opportunity generation and its
    # own "LU Co-Pro Opportunity Trace" history comment):
    #   - multilateral (treaty_slug is a real multilateral MECHANISM
    #     identity -- "eurimages" / "european-convention-coproduction",
    #     never a jurisdiction code): home_code is always a genuine
    #     member/party ("{home_code} is a Eurimages member"), alongside
    #     however many other discovered member candidates are shown.
    #   - bilateral, ONE partner entry: home_code IS the other real
    #     treaty party ("{home_code} + {partner_code}" opportunities).
    #   - bilateral, TWO partner entries: the treaty is between two
    #     OTHER candidate jurisdictions and home_code (served here only
    #     as production context) is explicitly NOT a party ("neither of
    #     which is {home_code}" -- the trace's own warning text).
    # The distinguishing signal is the treaty MECHANISM (multilateral
    # slug) and partner-list cardinality -- both real, structural facts
    # about the treaty record itself, never a hardcoded jurisdiction
    # comparison.
    _coprod_partners = trace.get("coproduction_partners") or []
    _MULTILATERAL_TREATY_SLUGS = {"eurimages", "european-convention-coproduction"}
    _home_is_party = (
        trace.get("treaty_slug") in _MULTILATERAL_TREATY_SLUGS
        or len(_coprod_partners) < 2
    )
    # Scoped to component_relocation only: the audit confirmed single_
    # country/full_relocation's existing bare-primary participants
    # ("already correct — do not reopen") -- their segments can carry a
    # real but INCIDENTAL account allocated outside the primary
    # jurisdiction (e.g. a few post-production accounts genuinely
    # incurred abroad, claiming no incentive there) that is not this
    # structure's OWN identity the way a component's routed destination
    # is. Only a component_relocation structure's routed segment is the
    # structure's defining second territory.
    # Optimizer P0 wiring remediation (2026-09-04), P0-2: a segment's
    # OWN real `claims_incentive` field (allocation_pricing.py's
    # SegmentEconomics -- False exactly when the segment has no
    # program_slug at all, i.e. it is a stated-location fact where spend
    # is disclosed but no incentive is claimed there) is the real,
    # structural signal of economic/claiming participation -- never a
    # jurisdiction-code special case. Confirmed live: LU's
    # component_relocation structure 8172eb82... carries a real US
    # segment with claims_incentive=False, program_slug=None (spend
    # physically located in the US, claims nothing there); its MU/CA-MB
    # segments both carry claims_incentive=True with a real program_slug.
    # A non-claiming segment's geography remains fully visible in
    # trace["segments"] (never removed there) -- only the canonical
    # PARTICIPANT list, which downstream consumers (title, Globe,
    # Inspector, Reports) treat as "who actually participates
    # economically," excludes it.
    #
    # Optimizer FINAL P0 remediation (P0-PART-001, Codex broader-corpus
    # audit dcc6dde/8890cc8): the P0-2 fix above only ever ADDED claiming
    # segments on top of an unconditional `_participant_codes = [code]`
    # seed. For a project whose PRIMARY jurisdiction is itself a
    # non-claiming, stated-location-only segment (confirmed live: 1,878
    # of 2,585 component rows across nine US-primary projects, e.g.
    # `05b645a4-...`), the seed alone left the primary's own
    # non-claiming code in the served list even though no filter would
    # ever have added it there directly. The seed must apply the SAME
    # claims_incentive test as every other component participant --
    # never a special case for the primary jurisdiction, and never a
    # jurisdiction-code/project-name special case. `code`'s own presence
    # in `trace["segments"]` (never removed there) is untouched; only
    # its membership in the canonical PARTICIPANT list is now gated.
    # GD-3 (Globe data contract remediation, 2026-09-20): the ordinary and
    # combined component-hybrid families (structural_archetype_generator's
    # `structure_type="hybrid"`, `structural_family in {ordinary_component_
    # hybrid, combined_coproduction_pair_stack, combined_coproduction_
    # component_stack, combined_coproduction_multi_component_stack,
    # combined_multilateral_coproduction_stack}`) route real, separately
    # allocated components to real distinct jurisdictions exactly the same
    # way component_relocation does -- confirmed by the Codex Globe data
    # contract delta audit (GDC-001), which found every one of these
    # structures served only its single anchor jurisdiction in
    # `participants`, even though `component_allocations` already carries
    # every routed leg's own real jurisdiction_code. Scoped to these two
    # structure_type values only -- single_country/full_relocation/
    # multi_program/treaty_coproduction's own existing bare/coproduction-
    # partner participant derivation is unchanged ("already correct -- do
    # not reopen", per the same audit).
    if structure_type in ("component_relocation", "hybrid"):
        _primary_claims = next(
            (
                _seg.get("claims_incentive") is True
                for _seg in trace.get("segments") or []
                if _seg.get("jurisdiction_code") == code
            ),
            False,
        )
        # A hybrid structure built by the structural generator (ordinary or
        # combined) never carries a `segments` trace at all -- only
        # `component_allocations`, whose real presence (with a genuine
        # anchor program on file) IS the structure's claim of economic
        # participation for its own primary jurisdiction. Never a
        # jurisdiction-code special case, and never inferred for a
        # rejected/unpriced row (a rejected candidate's component_
        # allocations describe an ATTEMPTED route, not a real claim).
        if not trace.get("segments") and trace.get("component_allocations") and is_priced:
            _primary_claims = bool(trace.get("anchor_program") or trace.get("program_slug"))
        _participant_codes = [code] if (code and _home_is_party and _primary_claims) else []
        for _seg in trace.get("segments") or []:
            _c = _seg.get("jurisdiction_code")
            if _c and _seg.get("claims_incentive") is True and _c not in _participant_codes:
                _participant_codes.append(_c)
        if is_priced:
            for _comp_alloc in trace.get("component_allocations") or []:
                _c = _comp_alloc.get("jurisdiction_code")
                if _c and _c not in _participant_codes:
                    _participant_codes.append(_c)
    else:
        _participant_codes = [code] if (code and _home_is_party) else []
    for _partner in _coprod_partners:
        _c = _partner.get("jurisdiction_code")
        if _c and _c not in _participant_codes:
            _participant_codes.append(_c)

    return {
        "structure_id": str(structure.id),
        "structure_type": structure_type,
        "label": _humanize_structure_label(structure.name, jurisdiction_name_by_code),
        "primary_jurisdiction": code,
        "participants": _participant_codes,
        "relationship_types": relationship_types,
        # Canonical optimizer/Globe wiring remediation (2026-09-04),
        # Section 5: MODELED POTENTIAL RATE vs AWARD/EXECUTION CERTAINTY.
        # Generically derived (canonical_evaluation.py's
        # _competitive_allocation_disclosure, keyed only on program_
        # requirements.allocation_type/preapproval_mandatory — never a
        # per-jurisdiction check) and served here as a real structured
        # boolean, not only as prose inside `warnings` a consumer would
        # otherwise have to pattern-match. False (never fabricated True)
        # for any row persisted before this field existed.
        "administrative_allocation_risk": bool(trace.get("administrative_allocation_risk")),
        # Existing Optimizer/Stacker Reconnection, Task 7 — read straight
        # off calculation_trace_json's conditional_programs/
        # conditional_compatibility (canonical_evaluation._conditional_
        # data()); [] / the old empty default for any row persisted before
        # this enrichment existed, same backward-compat pattern used
        # throughout this file.
        "conditional_programs": trace.get("conditional_programs") or [],
        "conditional_compatibility": trace.get("conditional_compatibility") or {
            "pursuable_count": 0, "counts_by_verdict": {}, "gate_kinds": [],
        },
        # Reinvestment + Qualification Opportunity Optimization — read
        # straight off calculation_trace_json's opportunities
        # (canonical_opportunity_bridge.py, wired in canonical_evaluation.
        # py's per-candidate loop). Never entered into NPC/ranking above;
        # [] for any row persisted before this enrichment existed.
        "opportunities": trace.get("opportunities") or [],
        # Canonical Co-production Qualification Reconnection — read
        # straight off calculation_trace_json's role_qualification
        # (canonical_role_qualification_bridge.py). Disclosure only,
        # never an admission/pricing gate for this already-priced
        # candidate; None for any row persisted before this enrichment
        # existed or for a program with no role/nationality rule data.
        "role_qualification": trace.get("role_qualification"),
        # Codex final four-row remediation (P0-SEL-ALT-001): the full
        # per-participant qualification/gate aggregate for component/
        # stack structures (empty list for single-program candidates,
        # which already retain their own complete role_qualification
        # dict directly — see _blocking_requirements' fallback below).
        "participant_qualifications": trace.get("participant_qualifications") or [],
        "is_fully_priced": is_priced,
        # P1-CLASS-001: one backend-owned, mutually exclusive classification
        # for every emitted structure -- see _structure_classification's
        # own docstring for the derivation order. A frontend consumer never
        # has to infer this from structure_type + candidate_status +
        # relationship_types combinations on its own.
        "classification": _structure_classification(trace, structure_type, is_priced),
        "candidate_status": trace.get("candidate_status"),
        # Codex Defect 4 — the actual terminal cause (never flattened to a
        # single generic reason) and the program identity, both already
        # persisted verbatim by canonical_evaluation.py; None for priced
        # rows and for pre-1.2.0 rows that predate this enrichment.
        "rejection_reason_class": trace.get("rejection_reason_class"),
        "program_slug": trace.get("program_slug"),
        # Workspace Top-6/Data Truthfulness: the real, human-readable
        # program name (e.g. "Australia PDV Offset (Post, Digital and
        # Visual Effects)" vs "Australia Location Offset") already exists
        # in the canonical doctrine registry (executable_jurisdiction_
        # registry.get_doctrine) but was never exposed on a structure —
        # the UI had only the opaque program_slug and the bare
        # jurisdiction, so two real, economically distinct programs in
        # the same country rendered as identical cards. None when no
        # program_slug is set (e.g. an unpriceable candidate) or the
        # slug has no registered doctrine record.
        "program_display_name": _program_display_name(trace.get("program_slug")),
        "program_display_names": [
            n for n in (_program_display_name(s) for s in (trace.get("program_slugs") or [])) if n
        ],
        "blockers": [] if is_priced else [trace.get("reason")] if trace.get("reason") else [],
        "gross_budget_usd": trace.get("gross_budget_usd"),
        "total_incentive_floor_usd": selected_incentive_usd,
        "total_incentive_ceiling_usd": selected_incentive_usd,
        "selected_incentive_usd": selected_incentive_usd,
        # Task 3 (canonical pricing path + discovery repair) — read the
        # REAL per-adjustment fields canonical_evaluation.py now persists
        # (calculation_trace_json["adjustments"]) instead of hardcoding
        # None/0.0. Falls back to the pre-1.15.0 static defaults for rows
        # persisted before this enrichment existed, same established
        # backward-compat pattern used throughout this file (e.g.
        # selected_incentive_usd above).
        "travel_incremental_delta_usd": (trace.get("adjustments") or {}).get("travel_incremental_delta_usd"),
        "fx_delta_usd": (trace.get("adjustments") or {}).get("fx_delta_usd"),
        "local_cost_delta_usd": (trace.get("adjustments") or {}).get("local_cost_delta_usd", 0.0),
        "inkind_replacement_delta_usd": (trace.get("adjustments") or {}).get("inkind_replacement_delta_usd", 0.0),
        "financing_cost_usd": (trace.get("adjustments") or {}).get("financing_cost_usd", 0.0),
        "implementation_cost_usd": (trace.get("adjustments") or {}).get("implementation_cost_usd", 0.0),
        "total_adjustments_usd": (trace.get("adjustments") or {}).get("total_adjustments_usd", 0.0),
        "npc_verified_usd": float(result.true_net_cost_usd) if result.true_net_cost_usd is not None else None,
        "npc_with_adjustments_usd": (
            float(result.risk_adjusted_net_cost_usd) if result.risk_adjusted_net_cost_usd is not None else None
        ),
        "npc_conservative_usd": float(result.true_net_cost_usd) if result.true_net_cost_usd is not None else None,
        # Existing Optimizer/Stacker Reconnection, Task B (treaty/co-pro):
        # populated for a treaty_coproduction structure
        # (canonical_treaty_bridge.CoproOpportunity, wired in
        # canonical_evaluation.py); None for every other structure type,
        # unchanged.
        "treaty_slug": trace.get("treaty_slug"),
        "coproduction_partners": trace.get("coproduction_partners") or [],
        "treaty_resolution_state": trace.get("treaty_resolution_state"),
        "treaty_cultural_test_required": trace.get("treaty_cultural_test_required"),
        "treaty_cultural_test_resolved": trace.get("treaty_cultural_test_resolved"),
        "treaty_disqualification_reasons": trace.get("treaty_disqualification_reasons") or [],
        # PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING — the real
        # creative-personnel gate's served contract (canonical_evaluation.
        # py's home-anchored/non-home-anchored bilateral loops, treaty_
        # engine.PersonnelRequirement + canonical_role_qualification_
        # bridge.evaluate_treaty_personnel_gate). None/[] for any row
        # persisted before this wiring existed, same backward-compat
        # pattern used throughout this file.
        "personnel_gate_state": trace.get("personnel_gate_state"),
        "personnel_satisfied_requirements": trace.get("personnel_satisfied_requirements") or [],
        "personnel_failed_requirements": trace.get("personnel_failed_requirements") or [],
        "personnel_missing_facts": trace.get("personnel_missing_facts") or [],
        "personnel_curable_levers": trace.get("personnel_curable_levers") or [],
        "personnel_next_question": trace.get("personnel_next_question"),
        # COPRO_OPPORTUNITY_RELEVANCE_AND_CLOSEOUT_VALIDATION — surfaces
        # exactly how this opportunity entered the candidate set and how
        # it classifies under the AVAILABLE/COMPATIBLE/CONDITIONAL/
        # EXECUTABLE/EXCLUDED/AUTHORITY_OR_RULE_DATA_INCOMPLETE contract
        # (canonical_evaluation._classify_opportunity_relevance), so a
        # consumer never has to re-derive project relevance from raw
        # resolution_state/conditional_scenario shape, or mistake a
        # globally-enumerated third-country treaty pair for a claim that
        # this project is itself compatible with it. None/None for any
        # row persisted before this field existed.
        "opportunity_inclusion_source": trace.get("opportunity_inclusion_source"),
        "project_anchored": trace.get("project_anchored"),
        "opportunity_relevance": trace.get("opportunity_relevance"),
        # Co-Pro Conditional Pricing Bridge — populated only for an
        # UNRESOLVED_FACTS treaty_coproduction structure where a
        # deterministic minimum-contribution scenario could be
        # constructed and (where canonical rate data exists) priced. None
        # for a resolved (ELIGIBLE/INELIGIBLE) opportunity or any other
        # structure type. See canonical_evaluation._build_conditional_
        # bilateral_scenario for the full disclosure shape.
        "conditional_scenario": trace.get("conditional_scenario"),
        "ownership_shares": None,
        # Existing Optimizer/Stacker Reconnection — rich multi-program pass-
        # through. claimed_program_ids is [] for every pre-existing single-
        # program structure (unchanged) and the two combined slugs for a
        # canonical_stack_bridge-generated structure. stacking_note reads
        # the SAME condition_text apply_stacking_adjustments/
        # evaluate_legal_stacking already computed — never re-derived here.
        "claimed_program_ids": list(structure.claimed_program_ids or []),
        "program_slugs": trace.get("program_slugs") or ([trace.get("program_slug")] if trace.get("program_slug") else []),
        # Rich structure semantics (explicit, never a flattened list of
        # look-alike programs): anchor_jurisdiction/anchor_program identify
        # the lead jurisdiction+program; stacked_programs are compatible
        # additional programs combined under that SAME anchor by an
        # explicit named compatibility rule (never invented). component_
        # allocations pass through directly from calculation_trace_json
        # (canonical_evaluation._price_component_relocation_candidate)
        # once component/split generation exists for a project.
        # coproduction_partners stays an honest empty list until treaty
        # candidate generation is reconnected — its presence here as a
        # named, typed field (not an absent key) is itself the pass-
        # through contract a later reconnection pass fills in.
        "jurisdiction_display_name": (jurisdiction_name_by_code or {}).get(code) if code else None,
        "anchor_jurisdiction": code,
        "anchor_jurisdiction_display_name": (jurisdiction_name_by_code or {}).get(code) if code else None,
        # component_relocation structures set anchor_program explicitly
        # (the target program belongs under component_allocations, never
        # flattened into stacked_programs); multi_program (stack)
        # structures derive anchor/stacked from per_program_adjusted_usd.
        "anchor_program": trace.get("anchor_program") or _anchor_and_stacked(trace)[0],
        "stacked_programs": (
            _anchor_and_stacked(trace)[1] if structure_type == "multi_program" else []
        ),
        # Display metadata is resolved at SERVE time, never trusted from the
        # frozen calculation trace: a row persisted before a jurisdiction had
        # a resolvable name would otherwise show the producer a raw code
        # (AE-AD) forever. Economics stay persisted; presentation heals.
        "component_allocations": _with_component_display_names(
            trace.get("component_allocations") or [], jurisdiction_name_by_code,
        ),
        "stacking_rule_type": trace.get("stacking_rule_type"),
        "stacking_note": trace.get("stacking_condition_text"),
        "stacking_reduction_usd": trace.get("stacking_reduction_usd"),
        "per_program_adjusted_usd": trace.get("per_program_adjusted_usd") or {},
        "legal_review_required": bool(trace.get("legal_review_required", False)),
        "stacking_violations": trace.get("stacking_violations") or [],
        "stacking_conditionals": trace.get("stacking_conditionals") or [],
        "disclosed_limitations": trace.get("disclosed_limitations") or [],
        "inkind_note": None,
        "notes": [],
        "segments": trace.get("segments") or [],
        "allocation": {
            "allocation_version": None, "is_complete": None, "conserves": None,
            "total_allocated_usd": None, "total_budget_lines_usd": None,
            "allocated_by_jurisdiction": {}, "unallocated_account_codes": [],
            "duplicate_account_codes": [], "notes": [], "assignments": [],
        },
        "recommendation": None,
        "is_baseline": bool(trace.get("is_baseline")),
        "relocation_cost_normalized": bool(trace.get("relocation_cost_normalized")),
        # Codex Defect 2 — the SAME fact under an explicit, unambiguous
        # name (falls back to relocation_cost_normalized for rows
        # persisted before this field existed). Comparability, not
        # priceability; is_fully_priced above is never derived from this.
        "is_directly_comparable": bool(trace.get("is_directly_comparable", trace.get("relocation_cost_normalized"))),
        # Codex final wiring remediation (P0-SEL-ALT-001): the EXACT,
        # per-dimension causes of non-comparability (never a single
        # blanket flag), plus the jurisdiction they were evaluated
        # against (the component's TARGET code for a component/split
        # structure, never the anchor). Empty list for the baseline and
        # for a fully-evidenced candidate; absent on rows persisted
        # before this field existed (pre-repair rows), which is handled
        # as an empty/unknown-cause list by the admission gate below —
        # never silently treated as "no cause needed".
        "relocation_missing_dimensions": list(trace.get("relocation_missing_dimensions") or []),
        "relocation_completeness_jurisdiction": trace.get("relocation_completeness_jurisdiction") or code,
        "reason": trace.get("reason"),
        "warnings": result.warnings or [],
        # Canonical authority substrate + feasibility boundary repair,
        # Task 1/2 — production feasibility, independent of is_fully_priced/
        # candidate_status by design (a candidate can be PRICED and
        # feasibility WEAK, or UNPRICEABLE and feasibility STRONG). None
        # for pre-1.4.0 rows that predate this field.
        "feasibility_status": trace.get("feasibility_status"),
        "feasibility_reasons": trace.get("feasibility_reasons") or [],
    }


#: Existing Optimizer/Stacker Reconnection, Task 12 — thin scenario-
#: category mapper. Maps EXISTING rank/priceability/comparability/treaty/
#: feasibility signals (all already computed above, none new) onto the
#: five intended categories. This is display-layer classification only —
#: it never changes is_fully_priced, is_directly_comparable, rank, or any
#: economics field; it only labels what those fields already mean.
SCENARIO_RECOMMENDED = "RECOMMENDED"
SCENARIO_ALTERNATIVE = "ALTERNATIVE"
SCENARIO_CO_PRO_OPPORTUNITIES = "CO_PRO_OPPORTUNITIES"
SCENARIO_PRICED_LOW_FIT = "PRICED_LOW_FIT"
SCENARIO_NOT_AVAILABLE = "NOT_AVAILABLE"


def _qualification_admits_recommended(entry: dict) -> bool:
    """NUM-001: thin, entry-dict-shaped wrapper over the one shared
    predicate (canonical_evaluation.qualification_admits_recommended) —
    never a second, independently-maintained copy of the rule itself.
    See that function's own docstring for the full rationale."""
    from app.services.canonical_evaluation import qualification_admits_recommended
    return qualification_admits_recommended(entry.get("role_qualification"))


def _blocking_requirements(entry: dict) -> list[str]:
    """Codex final four-row remediation (P0-SEL-ALT-001): "Replace
    state-only component/stack/treaty aggregation with one generic
    structured aggregate... the union of blockers must never be
    discarded." For a component/stack structure, unions EVERY
    participant's own missing_facts/curable_requirements/
    failed_requirements (see participant_qualifications, built by
    canonical_evaluation._participant_qualification_aggregate) —
    never just the worst-state string. A single-program candidate
    (no participants) falls back to its own, already-complete
    role_qualification dict, UNCHANGED except for one real fix:
    reasoning_trace is now also read when the three requirement
    lists are all empty — the ONLY place a RULE_DATA_INCOMPLETE/
    NOT_APPLICABLE state's real explanation lives (e.g. Manitoba's
    "cultural_qualification_model.py has no NationalityRequirement
    rows" note), previously silently dropped.

    A pure, module-level function (extracted from a nested closure with
    no captured state) specifically so it is independently unit-
    testable with hand-built entry dicts — Codex's exact requirement:
    "Assert the aggregate contract directly.\""""
    reqs: list[str] = []
    participants = entry.get("participant_qualifications") or []
    if participants:
        for p in participants:
            missing = list(p.get("missing_facts") or [])
            curable = list(p.get("curable_requirements") or [])
            failed = list(p.get("failed_requirements") or [])
            reqs.extend(missing)
            reqs.extend(curable)
            reqs.extend(failed)
            if not (missing or curable or failed):
                for trace in p.get("reasoning_trace") or []:
                    reqs.append(f"{p.get('program_slug')}: {trace}")
            if p.get("administrative_allocation_disclosure"):
                reqs.append(p["administrative_allocation_disclosure"])
        rq_state = (entry.get("role_qualification") or {}).get("state")
    else:
        rq = entry.get("role_qualification") or {}
        missing = list(rq.get("missing_facts") or [])
        curable = list(rq.get("curable_requirements") or [])
        failed = list(rq.get("failed_requirements") or [])
        reqs = missing + curable + failed
        if not reqs:
            for trace in rq.get("reasoning_trace") or []:
                reqs.append(trace)
        rq_state = rq.get("state")

    # Codex final wiring remediation (P0-SEL-ALT-001): disclose EVERY
    # actual missing relocation dimension by name, against the
    # CORRECT jurisdiction (relocation_completeness_jurisdiction —
    # the component's TARGET code for a component/split structure,
    # never the anchor primary_jurisdiction the prior pass used).
    # Never one blanket jurisdiction boolean standing in for travel/
    # FX/local-cost/in-kind.
    if not entry.get("is_baseline") and not entry.get("is_directly_comparable"):
        code = entry.get("relocation_completeness_jurisdiction") or entry.get("primary_jurisdiction", "")
        for dim in entry.get("relocation_missing_dimensions") or []:
            reqs.append(f"relocation_{dim}_evidenced__{code}")

    if not reqs:
        reqs = [
            f"Qualification state '{rq_state}' must be resolved before this "
            "structure can become a verified recommendation."
        ]
    return reqs


def _conditional_entry(entry: dict, next_alternative: dict | None) -> dict:
    """Also extracted to module level (see _blocking_requirements above)
    for direct unit-testability; no behavior change."""
    rq = entry.get("role_qualification") or {}
    why_ranked_first = (
        (f"Lower estimated NPC (${entry['npc_with_adjustments_usd']:,.2f}) than the next "
         f"unlockable alternative (${next_alternative['npc_with_adjustments_usd']:,.2f}) "
         "under the same optimizer ranking objective used for verified winners.")
        if next_alternative is not None and entry["npc_with_adjustments_usd"] is not None
        and next_alternative["npc_with_adjustments_usd"] is not None
        else "No other unlockable alternative currently exists in this project's candidate universe."
    )
    return {
        "structure_id": entry["structure_id"],
        "label": entry["label"],
        "structure_type": entry.get("structure_type"),
        "program_slug": entry.get("program_slug"),
        "program_slugs": entry.get("program_slugs"),
        "primary_jurisdiction": entry.get("primary_jurisdiction"),
        # Named "estimated", never "verified"/"guaranteed" — Requirement 9.
        "estimated_incentive_usd": entry["selected_incentive_usd"],
        "estimated_npc_usd": entry["npc_with_adjustments_usd"],
        "qualification_state": rq.get("state"),
        "qualification_route": rq.get("qualification_route"),
        "blocking_requirements": _blocking_requirements(entry),
        "why_ranked_first": why_ranked_first,
        "risk_disclosure": (
            "LEADING CONDITIONAL recommendation, not a verified winner. Its incentive is "
            "an ESTIMATE, never guaranteed or verified, until every blocking requirement "
            "above is resolved. Recomputes automatically when this project's facts change."
        ),
    }


def _is_conditional_eligible(entry: dict) -> bool:
    """Codex final wiring remediation (P0-SEL-ALT-001, third pass) — the
    exact predicate for membership in the LEADING_CONDITIONAL/UNLOCKABLE_
    ALTERNATIVE pool. Replaces the `67fbc30` intervention Codex's delta
    audit rejected: "accepts every fully priced non-baseline non-
    comparable entry whose role state is None, QUALIFIES,
    NOT_APPLICABLE, or any conditional state. It does not inspect why
    the row is non-comparable."

    True only for a candidate that is:
      1. is_fully_priced (calculable, evidence-supported economics) —
         a HARD_FAIL candidate never reaches is_fully_priced=True at all
         (QUAL_HARD_FAIL is excluded from _QUALIFICATION_ADMITS_PRICING
         in canonical_evaluation.py), so this alone already excludes
         every hard legal/authority/identity/retired veto.
      2. NOT the baseline (the baseline must never be the distinct
         leading conditional alternative).
      3a. Directly comparable AND its role_qualification.state is a
          genuine, explicit, still-unresolved-but-priced state (the
          SAME rule this predicate always used for comparable rows) — OR
      3b. NOT directly comparable, but ONLY because of an explicit,
          fully-enumerated, exclusively-curable cause:
            - role_qualification.state must NOT be None ("no absent
              aggregate state may be emitted as an actionable
              conditional" — this task's own controlling invariant;
              None means no qualification signal was ever computed for
              this candidate/its participants, which is never, by
              itself, proof of curability).
            - state must be QUALIFIES/NOT_APPLICABLE (already admits
              Recommended) or a genuine curable-unresolved state —
              never anything else (defensive; HARD_FAIL structurally
              cannot reach here, but this never assumes that silently).
            - entry["relocation_missing_dimensions"] must be non-empty
              (a complete, real cause was enumerated — never an absent/
              unknown cause) AND every listed cause must be one of the
              approved curable relocation dimensions
              (_RELOCATION_DIMENSIONS: travel/fx/local_cost/inkind) —
              a structural, non-curable cause (e.g. a multi-program
              stack's un-normalized NPC, carrying the
              _STACK_NORMALIZATION_NOT_COMPUTED sentinel) is NEVER a
              dimension name and therefore always excludes the row.
    Component/treaty structures' role_qualification.state is already the
    WORST-of-all-participants aggregate (canonical_evaluation.py's
    _component_qual_state/_combo_qual_state) — a single hard-failing
    participant therefore blocks the WHOLE structure here via the same
    state check, never silently admitted through one clean member."""
    if not entry.get("is_fully_priced"):
        return False
    if entry.get("is_baseline"):
        return False

    state = (entry.get("role_qualification") or {}).get("state")

    if entry.get("is_directly_comparable"):
        return state in _CONDITIONAL_ELIGIBLE_QUALIFICATION_STATES

    # Non-comparable: an absent aggregate qualification state is never,
    # by itself, proof of curability — excluded outright.
    if state is None:
        return False
    if state not in _CONDITIONAL_ELIGIBLE_QUALIFICATION_STATES and state not in _QUALIFICATION_ADMITS_RECOMMENDED:
        return False

    missing = entry.get("relocation_missing_dimensions") or []
    if not missing:
        return False  # no enumerated cause at all — unknown/unclassified, excluded
    return all(dim in _RELOCATION_DIMENSIONS for dim in missing)


def _scenario_category(entry: dict, rank: int | None) -> str:
    """Deterministic, single-signal-source category. Precedence:
    1. A registered treaty co-production instrument is attached
       (treaty_slug) -> CO-PRO OPPORTUNITIES, checked BEFORE the
       is_fully_priced gate: a real treaty/multilateral opportunity
       (canonical_treaty_bridge.CoproOpportunity) is disclosed as an
       opportunity precisely BECAUSE it is not (yet) priced/qualified
       economics — see Task B's fail-closed doctrine (registry presence
       is real and worth surfacing; it is never conflated with qualified,
       priced, or comparable economics, so it correctly has
       is_fully_priced=False and would otherwise be flattened into
       NOT AVAILABLE, losing exactly the distinction this category
       exists to preserve).
    2. Not fully priced (capability_only/rule_rejected/authority_
       insufficient, and not a treaty opportunity) -> NOT AVAILABLE.
    3. rank == 1 -> RECOMMENDED (the served numeric winner — only
       reachable when qualification is resolved; see
       _qualification_admits_recommended, enforced upstream in the
       comparable-pool filter so an unresolved candidate can never
       reach rank 1 in the first place).
    4. Fully priced + directly comparable + not rank 1 -> ALTERNATIVE
       (this also covers a directly-comparable candidate whose
       qualification is unresolved — disclosed with real economics,
       correctly excluded from Recommended).
    5. Everything else fully priced (not directly comparable, e.g. a
       relocation candidate, a component/split candidate, or a multi-
       program stack whose combined economics are real but not yet
       regionally normalized; or feasibility WEAK) -> PRICED-LOW-FIT: an
       economically valid figure that is a weak production/logistical/
       comparability fit, not a priceability failure.
    """
    if entry.get("treaty_slug"):
        return SCENARIO_CO_PRO_OPPORTUNITIES
    if not entry["is_fully_priced"]:
        return SCENARIO_NOT_AVAILABLE
    if rank == 1:
        return SCENARIO_RECOMMENDED
    if entry["is_directly_comparable"]:
        return SCENARIO_ALTERNATIVE
    return SCENARIO_PRICED_LOW_FIT


def _ranking_entry(entry: dict) -> dict:
    """Codex Defect 2 — is_fully_priced on a ranking entry must always mean
    what it says (this candidate has a real, priced NPC/incentive), never
    'and is also directly comparable'. Comparability is its OWN explicit
    field. A priced-but-not-comparable candidate therefore keeps its real
    numeric fields here AND is_fully_priced=True; it is excluded from the
    numeric RANK (see caller) and from a savings claim, never from having
    its own economics visible."""
    base = {
        "rank": None,  # filled in by caller only for the numerically-ranked (comparable) set
        "structure_id": entry["structure_id"],
        "label": entry["label"],
        "is_fully_priced": entry["is_fully_priced"],
        "is_directly_comparable": entry["is_directly_comparable"],
        "candidate_status": entry.get("candidate_status"),
        "rejection_reason_class": entry.get("rejection_reason_class"),
        "program_slug": entry.get("program_slug"),
    }
    if entry["is_fully_priced"]:
        base.update({
            "selected_incentive_usd": entry["selected_incentive_usd"],
            "inkind_replacement_delta_usd": entry["inkind_replacement_delta_usd"],
            "npc_verified_usd": entry["npc_verified_usd"],
            "npc_with_adjustments_usd": entry["npc_with_adjustments_usd"],
            "npc_conservative_usd": entry["npc_conservative_usd"],
            "conditional_pursuable_count": 0,
        })
        if not entry["is_directly_comparable"]:
            base["excluded_from_ranking_because"] = [
                "Priced from a real statutory rate, but this candidate's relocation-specific "
                "costs (travel, in-kind replacement) are not yet modeled generically — its NPC "
                "is not a fair comparison against the base jurisdiction yet. Regional cost "
                "normalization pending."
            ]
    else:
        base["excluded_from_ranking_because"] = entry["blockers"] or [entry.get("reason") or "Not fully priced."]
    return base


async def _load_baseline_results(session: AsyncSession, project_id, fingerprint: str) -> list[tuple]:
    """(StructureCalculationResult, structure name) for the current generation's BASELINE row(s),
    newest first -- WITHOUT reading the generation.

    A baseline is always among the generation summary's retained ordinals (the summary keeps every
    non-RULE_REJECTED row plus any baseline whatever its status), so it is fetched by
    generation_ordinal through the (fingerprint, engine, ordinal) index and filtered on
    is_baseline inside that small set. The previous form loaded every row of the generation as an
    ORM object (526,155 for F#K Valentine's Day) to find that one row. A generation with no summary
    (never one written by canonical-1.88.0+) has no served baseline."""
    try:
        summary = await load_generation_summary(session, project_id, fingerprint, engine_version=ENGINE_VERSION)
    except GenerationSummaryUnavailable:
        return []
    scr = StructureCalculationResult
    ordinals = list(summary.non_rejected_ordinals)
    found: list[tuple] = []
    for i in range(0, len(ordinals), 5000):
        found.extend((await session.execute(
            select(scr, ProductionStructure.name)
            .join(ProductionStructure, ProductionStructure.id == scr.structure_id)
            .where(
                ProductionStructure.project_id == project_id,
                scr.input_fingerprint == fingerprint,
                scr.engine_version == ENGINE_VERSION,
                scr.generation_ordinal.in_(ordinals[i:i + 5000]),
                scr.calculation_trace_json["is_baseline"].astext == "true",
            )
        )).all())
    found.sort(key=lambda pair: pair[0].created_at, reverse=True)
    return [tuple(pair) for pair in found]


async def compute_anchor_budget_contract(session: AsyncSession, project_id) -> dict:
    """CLAUDE_CORRECT_FAILED_OPTIMIZER_CLOSEOUT, Section A — the Anchor
    Budget Contract. THIS FUNCTION IS A THIN PRESENTATION READER, NOT THE
    SOURCE: the actual calculation (gross budget, supplied-incentive
    query, canonical calculated incentive, variance, financing adjustment,
    anchor NPC) is computed and PERSISTED inside the optimizer's own
    evaluation path (`canonical_evaluation.evaluate_project()`, the
    `anchor_contract` field on the real anchor candidate's own
    `calculation_trace_json`, written at the same point every other real
    field on that candidate is written). This function only reads that
    already-computed, already-persisted field back — it recomputes
    nothing. If a caller ever finds this field absent on a current-
    fingerprint baseline row, that is a genuine evaluator defect (the
    baseline candidate did not reach the PRICED branch that writes it),
    not something this reader silently papers over by recalculating —
    it returns status NO_ANCHOR_CONTRACT_PERSISTED instead.

    Returns a dict with: gross_budget_usd, supplied_incentive_usd (None if
    no such budget line exists — genuinely absent, never guessed),
    calculated_anchor_incentive_usd, variance_usd (None when no supplied
    figure exists to vary against — never a fabricated 100% variance),
    financing_adjustment_usd, anchor_npc_usd, anchor_jurisdiction_code,
    anchor_candidate_status, and anchor_role_qualification_state (the
    baseline's own real cultural-test/qualification state — the exact
    reason a project may have no verified recommendation)."""
    from app.services.canonical_evaluation import ENGINE_VERSION, current_generation_fingerprint

    fingerprint = await current_generation_fingerprint(session, project_id)
    if not fingerprint:
        return {"status": "NO_CURRENT_EVALUATION", "project_id": str(project_id)}

    baseline_rows = await _load_baseline_results(session, project_id, fingerprint)
    baseline_row = baseline_rows[0] if baseline_rows else None
    if baseline_row is None:
        return {"status": "NO_BASELINE_STRUCTURE", "project_id": str(project_id)}
    scr, sname = baseline_row
    trace = scr.calculation_trace_json or {}
    engine_contract = trace.get("anchor_contract")
    if engine_contract is None:
        # Real, disclosed gap: the baseline exists but did not reach the
        # PRICED persist branch that writes anchor_contract (e.g. a
        # blocked/unpriced baseline). Never recomputed here — that would
        # make this reader a second source of truth, exactly what this
        # workstream's own correction forbids.
        return {
            "status": "NO_ANCHOR_CONTRACT_PERSISTED",
            "project_id": str(project_id),
            "anchor_candidate_status": trace.get("candidate_status"),
            "anchor_role_qualification_state": (trace.get("role_qualification") or {}).get("state"),
        }

    return {
        "status": "OK",
        "project_id": str(project_id),
        "anchor_structure_name": sname,
        "anchor_jurisdiction_code": trace.get("primary_jurisdiction"),
        "gross_budget_usd": engine_contract.get("gross_budget_usd"),
        "supplied_incentive_usd": engine_contract.get("supplied_incentive_usd"),
        "calculated_anchor_incentive_usd": engine_contract.get("calculated_anchor_incentive_usd"),
        "variance_usd": engine_contract.get("variance_usd"),
        "financing_adjustment_usd": engine_contract.get("financing_adjustment_usd"),
        "anchor_npc_usd": engine_contract.get("anchor_npc_usd"),
        "anchor_candidate_status": trace.get("candidate_status"),
        "anchor_role_qualification_state": (trace.get("role_qualification") or {}).get("state"),
        "state_fingerprint": fingerprint,
        "engine_version": ENGINE_VERSION,
    }


#: The production view serves at most this many DETAILED candidates per response (a served
#: candidate entry is ~6-50 KB: segments, conditional programs/compatibility, warnings ...).
#: Counts, the selected structure, the leading conditional structure and the baseline are always
#: exact and always on the first page; the remainder is reached with candidate_offset (or the
#: opaque next_cursor via GET /projects/{id}/evaluation/candidates). Every row stays in storage.
CANDIDATE_PAGE_DEFAULT_LIMIT = 100
CANDIDATE_PAGE_MAX_LIMIT = 100
CANDIDATES_ROUTE = "/api/v1/projects/{project_id}/evaluation/candidates"
_CANDIDATE_ORDER = (
    "selected structure, leading conditional structure and baseline first; then ranking order "
    "(comparable by rank, then review-required by NPC, then unpriced), equal NPCs by canonical "
    "economic identity"
)


def encode_candidate_cursor(fingerprint: str, offset: int) -> str:
    """Opaque cursor bound to ONE generation: a cursor minted for another fingerprint is refused."""
    import base64
    import json
    raw = json.dumps([fingerprint[:16], int(offset)], separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_candidate_cursor(cursor: str) -> tuple[str, int]:
    import base64
    import json

    from app.services.canonical_evaluation import InvalidPageCursor
    try:
        fp16, offset = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        if not isinstance(fp16, str) or isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise ValueError("bad cursor parts")
        return fp16, offset
    except Exception as exc:  # noqa: BLE001 -- any malformed cursor is one client error
        raise InvalidPageCursor("invalid pagination cursor") from exc


async def build_production_and_structures(
    session: AsyncSession, project_id, *,
    candidate_limit: int = CANDIDATE_PAGE_DEFAULT_LIMIT, candidate_offset: int = 0,
) -> dict:
    """Generic, project_id-driven replacement for GET /cineglobe/production
    + GET /cineglobe/structures, sourced from canonical_evaluation.py's
    persisted rows instead of the Little-Utopia-only in-memory get_state().

    BOUNDED: ``structures.allocated_structures.structures`` / ``ranking`` carry at most
    ``candidate_limit`` (<= 100) detailed candidates -- a deterministic page (see
    ``candidates_page``) -- never the whole candidate set, and never the rejection universe.
    Selection, ranking, conditional pooling and every count are still computed over ALL served
    (non-rejected) candidates, so they are exact; only the DETAIL returned is paged.
    """
    project = await session.get(Project, project_id)
    if project is None:
        return {"status": "PROJECT_NOT_FOUND"}

    # Final Consolidated Backend Correction + Global Structuring
    # Intelligence Acceptance, Part 4/CBA-001 (and in the spirit of
    # Codex's CBA-008): which rows are "this project's current
    # evaluation" must never depend on leading_structure_id — that field
    # is correctly None whenever no candidate currently admits
    # Recommended (a real, disclosed, priced baseline can still exist
    # with no recommended winner; see canonical_evaluation.py's
    # _summarize_evaluation). The current fingerprint/engine_version is
    # instead read directly off ANY current-engine result row for this
    # project — every row from one evaluation run shares one fingerprint
    # by construction (_compute_fingerprint is a pure function of the
    # project's inputs, not of any individual candidate).
    engine_version = ENGINE_VERSION
    # Producer Display Names + Budget Rail User Assumptions closeout —
    # correctness fix, not a doctrine change. Rows are never deleted when
    # a new evaluation runs (evaluate_project's own idempotent-per-
    # fingerprint cache accumulates one row set per distinct fingerprint
    # ever seen), so once a producer changes any assumption that
    # participates in the fingerprint (contingency_expected_utilization_
    # pct, financing_cost_usd, ...) and later changes it back, TWO (or
    # more) real fingerprints legitimately coexist for this project — an
    # older one is not necessarily stale; "most recently CREATED" is not
    # the same fact as "matches the CURRENT persisted inputs" (reverting
    # an assumption can make an older row current again). The only
    # correct source for "this project's current fingerprint" is the
    # SAME computation evaluate_project() itself uses — never a guess
    # (an unordered `.limit(1)`, tried first here and confirmed wrong;
    # ordering by created_at DESC, tried second, also confirmed wrong on
    # the revert case) over the calculation-result table. evaluate_project
    # is READ-ONLY and side-effect-free (same queries evaluate_project()
    # itself runs to decide REUSED vs. recompute) — this function must
    # never trigger evaluate_project()'s own mutating steps (script
    # analysis, artwork extraction, new-row persistence) merely because a
    # producer loaded a page; calling the full entry point here was tried
    # and reverted — it caused duplicate/extra StructureCalculationResult
    # rows by invoking evaluate_project() far more often than the
    # explicit "Begin Evaluation" action ever did, breaking the very
    # idempotency this fix depends on.
    # Optimizer FINAL closeout, P1-FRESH-001 — this reconstruction (recompute
    # the fingerprint from the project's ACTUAL current facts, the exact
    # same computation evaluate_project() itself uses, falling back to the
    # newest-row helper only when a fresh computation is impossible) is now
    # the ONE shared canonical generation identity, extracted to
    # canonical_evaluation.current_generation_fingerprint() so this view and
    # build_generic_pkg_and_economics() below can never key off two
    # different real generations for the same project. See that function's
    # own docstring for the full root-cause history (Codex, final P0 delta
    # reaudit: FVD and Lips Like Sugar could previously diverge).
    from app.services.canonical_evaluation import current_generation_fingerprint
    fingerprint = await current_generation_fingerprint(session, project.id)

    # Bounded read (2026-09-19): this view previously built a structure entry for EVERY
    # row of the current generation -- 526,155 for F#K Valentine's Day, 99.9% of them
    # RULE_REJECTED -- and served every one in structures/ranking. The evaluation's one
    # summary row (accumulated while it ran) now names the rows that are NOT plain
    # RULE_REJECTED (priced, dominated, co-pro, feasibility, unpriceable-authority, plus
    # any baseline), which are fetched by generation_ordinal; the rejected mass is
    # summarized (exact totals, counts by disposition/reason, one bounded first page +
    # cursor) under structures["rejection_universe"]. Nothing is dropped: every row stays
    # in the database and behind GET /projects/{id}/evaluation/unpriceable. Only rows of
    # THIS (fingerprint, engine_version) generation are ever read: stale fingerprints and
    # older engine versions are excluded by construction.
    rows: list[tuple] = []
    generation_totals = {"total": 0, "priced": 0, "by_disposition": {}, "by_reason": []}
    generation_total_rows = 0
    rejection_first_page = {
        "limit": UNPRICEABLE_PAGE_DEFAULT_LIMIT, "returned": 0, "has_more": False,
        "next_cursor": None, "order": UNPRICEABLE_PAGE_ORDER, "results": [],
    }
    aggregate_groups_first_page = {
        "limit": 0, "returned": 0, "has_more": False, "next_cursor": None, "order": "group_ordinal", "results": [],
    }
    if fingerprint:
        try:
            _summary = await load_generation_summary(session, project.id, fingerprint, engine_version=engine_version)
        except GenerationSummaryUnavailable:
            # A fingerprint can be computed for a project with no evaluation persisted
            # under it (yet): no rows, exactly as before.
            _summary = None
        if _summary is not None:
            rows = await load_retained_rows(session, project.id, fingerprint, _summary, engine_version=engine_version)
            generation_totals = summary_totals(_summary)
            generation_total_rows = _summary.total_rows
            rejection_first_page = await unpriceable_page(
                session, project.id, fingerprint, engine_version=engine_version,
            )
            # Bounded candidate retention (canonical-1.90.0): every candidate outside the retained
            # decision set is counted exactly and served as aggregate GROUPS, never as rows.
            aggregate_groups_first_page = await candidate_groups_page(
                session, project.id, fingerprint, engine_version=engine_version,
            )

    jurisdiction_ids = set()
    for structure, _ in rows:
        for alloc in structure.jurisdiction_allocations or []:
            if alloc.get("jurisdiction_id"):
                jurisdiction_ids.add(alloc["jurisdiction_id"])
    jurisdictions = (
        (await session.execute(select(Jurisdiction).where(Jurisdiction.id.in_(jurisdiction_ids)))).scalars().all()
        if jurisdiction_ids else []
    )
    jurisdiction_code_by_id = {str(j.id): j.code for j in jurisdictions}
    jurisdiction_name_by_code = _jurisdiction_names_by_code(jurisdictions)

    structure_entries = [
        _empty_structure_entry(s, r, jurisdiction_code_by_id, jurisdiction_name_by_code) for s, r in rows
    ]

    # CLAUDE_FINAL_ACTIVE_OPTIMIZER_IMPLEMENTATION_AND_RUNTIME_CLOSEOUT,
    # Section A/B/E — the Anchor Budget Contract's own required comparison:
    # "Every alternative's net benefit must use the same anchor: anchor NPC
    # minus alternative NPC" and the $100,000 hybrid-recommendation
    # threshold ("Net benefit >= $100,000: eligible for recommendation.
    # Net benefit < $100,000: retain as valid but mark
    # ECONOMICALLY_NON_MATERIAL / NOT_RECOMMENDED. The $100,000 rule
    # controls recommendation -- not generation or calculation.").
    # Computed HERE, once, post-hoc over the already-priced served
    # entries -- never inside candidate generation/pricing itself, so no
    # existing calculation, eligibility, or ranking code is touched. The
    # anchor is this project's own real is_baseline row's true_net_cost_
    # usd (the SAME anchor every existing net-benefit computation in this
    # codebase already uses for treaty conditional scenarios -- see
    # _build_conditional_bilateral_scenario's own baseline_incentive_usd
    # parameter); applies uniformly to every OTHER structure's own real
    # true_net_cost_usd (component_relocation/full_relocation/hybrid) or,
    # where the structure itself is never priced on its own row (a
    # treaty_coproduction opportunity), its nested conditional_scenario's
    # own conditional_npc_usd -- never a verified recommendation either
    # way (Section D/E: conditional structures never outrank verified
    # ones; this label is disclosure only, read by nothing that ranks).
    HYBRID_MATERIALITY_THRESHOLD_USD = 100_000.0
    _anchor_npc = next(
        (float(e["npc_verified_usd"]) for e in structure_entries
         if e.get("is_baseline") and e.get("npc_verified_usd") is not None),
        None,
    )
    for _e in structure_entries:
        if _anchor_npc is None or _e.get("is_baseline"):
            _e["net_benefit_vs_anchor_usd"] = None
            _e["hybrid_recommendation_status"] = "NOT_APPLICABLE"
            continue
        _candidate_npc = _e.get("npc_verified_usd")
        _via_conditional = False
        if _candidate_npc is None:
            _cs = _e.get("conditional_scenario") or {}
            _candidate_npc = _cs.get("conditional_npc_usd")
            _via_conditional = _candidate_npc is not None
        if _candidate_npc is None:
            _e["net_benefit_vs_anchor_usd"] = None
            _e["hybrid_recommendation_status"] = "NOT_APPLICABLE"
            continue
        _net_benefit = round(_anchor_npc - float(_candidate_npc), 2)
        _e["net_benefit_vs_anchor_usd"] = _net_benefit
        if _via_conditional:
            # A modeled/conditional structure's net benefit is real
            # disclosure, never a recommendation signal on its own --
            # Section D/E's own "never auto-award / never outrank a
            # verified candidate" rule.
            _e["hybrid_recommendation_status"] = (
                "CONDITIONAL_MATERIAL" if _net_benefit >= HYBRID_MATERIALITY_THRESHOLD_USD
                else "CONDITIONAL_ECONOMICALLY_NON_MATERIAL"
            )
        else:
            _e["hybrid_recommendation_status"] = (
                "ELIGIBLE_FOR_RECOMMENDATION" if _net_benefit >= HYBRID_MATERIALITY_THRESHOLD_USD
                else "ECONOMICALLY_NON_MATERIAL_NOT_RECOMMENDED"
            )

    # Ranking (Part K — never invent regional savings): only structures
    # whose cost is actually comparable on the SAME basis participate in
    # numeric RANK. A relocation candidate's lower NPC omits real
    # relocation costs (travel, in-kind replacement) no project has
    # generic data for yet — a lower number there is not a cheaper
    # option, just an incomplete one. is_directly_comparable is False
    # for every candidate except the production's own base jurisdiction
    # (which needs no such adjustment by construction), so this mirrors
    # canonical_evaluation.py's own _summarize_evaluation top_pair rule:
    # the baseline is the winner whenever it is priced, never a relocation
    # candidate on a merely-lower raw number.
    #
    # Codex Defect 2 — comparability gates the RANK, never priceability
    # itself: every priced candidate (comparable or review_required) keeps
    # is_fully_priced=True and its real QPE/incentive/NPC on its ranking
    # entry (see _ranking_entry). Only genuinely unpriced candidates get
    # is_fully_priced=False. Overview/Scenarios/Workspace/Globe all read
    # the same explicit is_directly_comparable field to decide what to
    # rank vs. what to show as priced-but-review, never overloading
    # is_fully_priced to mean both things.
    # Equal-NPC ties are ordered by the run-independent canonical economic identity (the same
    # tie-breaker evaluate_project's ranking uses), never by database row order or the
    # per-generation random structure uuid -- so a ranking is reproducible across
    # regenerations of the same economics.
    _identity_by_structure = {
        str(s.id): (r.economic_identity or canonical_economic_identity(r.structure_type, r.calculation_trace_json))
        for s, r in rows
    }
    # FOUR_PRODUCTION_GLOBE_RUNTIME_CORRECTION (2026-09-21): the same
    # canonical economic_identity every retention-summary block
    # (best_per_jurisdiction, top_by_structural_family) already attaches
    # individually now stamps EVERY served structure entry generically, here,
    # once -- so the served `structures[]` page (the bounded candidates_page
    # Globe/Workspace consume for ordinary, non-backstop candidates) carries
    # the real identity too, not only the two retention-summary projections.
    # Confirmed live: an Optimizer structure sourced from the bounded page
    # (the common case -- a family with real page representation) served
    # `economic_identity: null` even though `_identity_by_structure` already
    # computed a real value for that exact structure_id here; only the
    # SEPARATE compact summaries re-attached it. No new computation, no
    # second identity formula -- `_identity_by_structure` is unchanged, this
    # only stops discarding it before `structure_entries` is built out.
    for _e in structure_entries:
        _e["economic_identity"] = _identity_by_structure.get(_e["structure_id"])
    _rank_key = lambda e: (
        e["npc_with_adjustments_usd"] if e["npc_with_adjustments_usd"] is not None else float("inf"),
        _identity_by_structure.get(e["structure_id"], ""),
    )
    comparable = sorted(
        (e for e in structure_entries
         if e["is_fully_priced"] and e["is_directly_comparable"] and _qualification_admits_recommended(e)),
        key=_rank_key,
    )
    # Workspace Top-6/Data Truthfulness: review_required carries NO rank
    # (comparability, not priceability, gates numeric rank — see above),
    # but its SERVED ORDER was arbitrary (structure_entries' own DB/
    # trace-generation order), so a UI's "first N" slice was showing
    # whichever candidates happened to be generated/persisted first, not
    # the cheapest-modeled ones. Sorting here is presentation order only,
    # using the same real NPC field comparable's own sort already uses —
    # it grants no rank, no recommendation, no comparability; a consumer
    # must still read is_directly_comparable to know these are NOT
    # canonical-ranked outcomes.
    review_required = sorted(
        (e for e in structure_entries
         if e["is_fully_priced"] and not (e["is_directly_comparable"] and _qualification_admits_recommended(e))),
        key=_rank_key,
    )
    unpriced = [e for e in structure_entries if not e["is_fully_priced"]]

    # Codex final P0 (leading conditional recommendation) — a project
    # with MANY priced candidates but NO verified winner (comparable is
    # empty) previously exposed nothing beyond "no recommendation exists"
    # even when a real, priced, is_directly_comparable candidate is
    # blocked ONLY by an explicitly-identified, genuinely unlockable
    # qualification state (a user fact, a curable gap, an authority-
    # research residual — never a hard ineligibility, a retired/fail-
    # closed/authority-vetoed program, or a merely-not-yet-regionally-
    # normalized relocation candidate). This pool uses the EXACT SAME
    # comparability gate (`is_directly_comparable`) and the EXACT SAME
    # ranking objective (`npc_with_adjustments_usd` ascending) `comparable`
    # itself uses — the only thing relaxed is `_qualification_admits_
    # recommended`, replaced with the qualification states that are both
    # priced AND still genuinely unresolved
    # (_CONDITIONAL_ELIGIBLE_QUALIFICATION_STATES). Deliberately surfaced
    # ONLY when no verified winner exists (`not comparable`) — Bad
    # Hombres/Lips Like Sugar, which DO have a verified winner, must never
    # also show a competing "leading conditional" option.
    conditional_pool = (
        sorted(
            (e for e in structure_entries if _is_conditional_eligible(e)),
            key=_rank_key,
        )
        if not comparable else []
    )
    _leading_conditional_id = conditional_pool[0]["structure_id"] if conditional_pool else None
    _unlockable_alternative_ids = {e["structure_id"] for e in conditional_pool[1:]}

    ranking: list[dict] = []
    for i, e in enumerate(comparable, start=1):
        e["scenario_category"] = _scenario_category(e, rank=i)
        r = _ranking_entry(e)
        r["rank"] = i
        r["scenario_category"] = e["scenario_category"]
        r["recommendation_category"] = REC_VERIFIED_RECOMMENDATION
        ranking.append(r)
    for e in review_required:
        e["scenario_category"] = _scenario_category(e, rank=None)
        r = _ranking_entry(e)
        r["scenario_category"] = e["scenario_category"]
        r["recommendation_category"] = (
            REC_LEADING_CONDITIONAL if e["structure_id"] == _leading_conditional_id
            else REC_UNLOCKABLE_ALTERNATIVE if e["structure_id"] in _unlockable_alternative_ids
            else None  # ALTERNATIVE/PRICED_LOW_FIT for a reason outside this 5-category scheme
        )
        ranking.append(r)
    for e in unpriced:
        e["scenario_category"] = _scenario_category(e, rank=None)
        r = _ranking_entry(e)
        r["scenario_category"] = e["scenario_category"]
        r["recommendation_category"] = (
            REC_AUTHORITY_UNRESOLVED_FAIL_CLOSED
            if e.get("candidate_status") == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
            else REC_REJECTED
        )
        ranking.append(r)

    leading_conditional_structure = (
        _conditional_entry(conditional_pool[0], conditional_pool[1] if len(conditional_pool) > 1 else None)
        if conditional_pool else None
    )
    unlockable_alternatives = [
        _conditional_entry(e, conditional_pool[i + 2] if i + 2 < len(conditional_pool) else None)
        for i, e in enumerate(conditional_pool[1:])
    ]

    # Final non-Globe closeout, Item A — canonical scenario-selection
    # source. Codex found Reports.jsx reading ONLY rank==1 while
    # Overview/Workspace additionally fell back to a client-side
    # "bestPricedCandidate" re-derivation when rank 1 was absent (a real,
    # common state: comparable_count==0). Two independent selection
    # algorithms living in two places is exactly the inconsistency risk
    # the closeout brief calls out — this field removes it by computing
    # the ONE canonical answer here, once, server-side, and serving it
    # explicitly. Every consumer (frontend lib/globeData.js::
    # activeStructure, lib/bestPricedCandidate.js, Reports.jsx) now reads
    # THIS field rather than each recomputing its own fallback; a
    # producer's manual "leading structure" pick (client-only, ephemeral
    # UI selection state, never persisted or treated as project truth)
    # still overrides it at the call site, exactly as before.
    #
    # Optimizer P0 wiring remediation (2026-09-04), P0-1 — CANONICAL
    # SELECTION DIVERGENCE (Codex): the ORIGINAL algorithm here fell back
    # to "the lowest-NPC structure among ALL is_fully_priced structures"
    # whenever `comparable` was empty — including PRICED_LOW_FIT,
    # is_directly_comparable=False candidates. That directly contradicted
    # canonical_evaluation.py::_summarize_evaluation, which deliberately
    # returns NO top_result and CLEARS Project.leading_structure_id in
    # this exact state (no candidate is both is_directly_comparable and
    # qualification-admits-Recommended — see _qualification_admits_
    # recommended, the same two gates `comparable` itself already
    # applies). Confirmed live: Little Utopia and F#K Valentine's Day
    # both have leading_structure_id=None and comparable_count=0, yet
    # this field was silently promoting each production's own
    # PRICED_LOW_FIT Saudi full-relocation candidate as "the" canonical
    # selection — a candidate the evaluator itself never selected.
    #
    # Fixed by removing the non-comparable fallback entirely: the
    # evaluator's own accepted/comparable semantics are the ONLY source
    # of truth here, never a second, independently-invented ranking.
    #   1. rank 1 (comparable[0]) if a numerically-ranked, comparable,
    #      Recommended-admitting candidate exists — unchanged.
    #   2. else None — no comparable winner exists, so there is no
    #      canonical selection, exactly matching _summarize_evaluation's
    #      own top_result=None / leading_structure_id=None state.
    # (The one theoretical case this diverges from _summarize_evaluation
    # — a baseline structure ROW never existing at all, a genuine hard
    # structural failure distinct from "no candidate is comparable" —
    # does not occur for any current real project: every project's own
    # generic evaluation always generates a baseline candidate row.)
    canonical_selected_structure_id = (
        comparable[0]["structure_id"] if comparable else None
    )

    base_code = jurisdiction_code_by_id.get(str(project.home_jurisdiction_id)) if project.home_jurisdiction_id else None
    if base_code is None:
        baseline_entry = next((e for e in structure_entries if e["is_baseline"]), None)
        base_code = baseline_entry["primary_jurisdiction"] if baseline_entry else None

    budget_doc = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project.id)
        .order_by(BudgetDocument.created_at.desc())
    )).scalars().first()
    gross_budget_usd = (
        float(project.total_budget_usd) if project.total_budget_usd is not None
        else (float(budget_doc.total_budget_raw) if budget_doc and budget_doc.total_budget_raw is not None else None)
    )

    # Production Page Integrity: leaf_account_sum_usd/variance_usd/note
    # were hardcoded None for every generic project — the SAME "designed
    # field, never wired" pattern this session keeps finding. Populated
    # from the real, persisted BudgetLineItem rows (never a second budget
    # model). A genuine, MATERIAL gap (as opposed to the ~$2 immaterial
    # rounding LU's own real document carries) is disclosed here, never
    # silently balanced away and never force-redistributed into the
    # displayed category breakdown — the declared document total remains
    # the authoritative gross_budget_usd either way (existing, unchanged
    # doctrine: "the document's own declared total governs").
    leaf_account_sum_usd = None
    variance_usd = None
    reconciliation_note = None
    source_budget_finance_usd = 0.0
    if budget_doc is not None:
        leaf_rows = (await session.execute(
            select(BudgetLineItem.amount_usd, BudgetLineItem.spend_category).where(
                BudgetLineItem.budget_document_id == budget_doc.id
            )
        )).all()
        leaf_account_sum_usd = round(sum(float(a) for a, _ in leaf_rows if a is not None), 2)
        # Financing ALREADY inside the source budget. Read off the SAME
        # classified lines the priced register uses, so this can never
        # disagree with the classification that produced gross.
        source_budget_finance_usd = round(sum(
            float(a) for a, category in leaf_rows
            if a is not None and str(getattr(category, "value", category) or "").endswith("finance_costs")
        ), 2)
        if gross_budget_usd is not None:
            variance_usd = round(gross_budget_usd - leaf_account_sum_usd, 2)
            if abs(variance_usd) > 5:
                reconciliation_note = (
                    f"The document's own declared grand total (${gross_budget_usd:,.2f}) differs from "
                    f"the sum of its own extracted leaf account lines (${leaf_account_sum_usd:,.2f}) by "
                    f"${variance_usd:,.2f} — a real gap in the source document itself (e.g. a category "
                    "reported only as part of the stated total, not broken into its own leaf line), not "
                    "a parsing loss. The declared total remains authoritative; never redistributed into "
                    "the displayed category breakdown to force a match."
                )

    from app.services.canonical_project_economics import build_ui_location_categories
    ui_location_categories = await build_ui_location_categories(session, project.id)

    # Item B (Final non-Globe closeout, 2026-09-04) -- served, read-only
    # view of this project's own resolved discretionary/selective-program
    # policy (see canonical_evaluation.py's DISCRETIONARY_POLICY_* facts
    # and _discretionary_policy_resolve). Inspectable generically for any
    # project/program; per-program overrides are reported only for
    # programs that actually appear in this project's own served
    # structures, so this can never invent a policy row for a program the
    # project has no candidate for.
    from app.services.canonical_evaluation import (
        _discretionary_policy_facts, _discretionary_policy_resolve, _is_discretionary_program,
    )
    _raw_policy_facts = await _discretionary_policy_facts(session, project.id)
    _served_program_slugs = sorted({
        slug
        for e in structure_entries
        for slug in ([e["program_slug"]] if e.get("program_slug") else []) + (e.get("program_slugs") or [])
        if slug
    })
    # program_overrides reports every REAL persisted per-program fact,
    # never scoped to currently-served structures: a program a producer
    # has excluded is, BY DESIGN, no longer a served structure (that's
    # the whole point of the exclusion), so scoping this to served slugs
    # would make an active override invisible/unreadable the moment it
    # takes effect -- exactly the wrong direction for something a
    # producer needs to be able to see and toggle back. resolved_by_
    # program instead unions served discretionary programs with any
    # program that has an explicit override on file, so both "on and
    # visible" and "off and still visible" programs are represented.
    _program_override_slugs = sorted({
        fact_key[len("discretionary_policy_program:"):]
        for fact_key, value in _raw_policy_facts.items()
        if fact_key.startswith("discretionary_policy_program:") and value in ("include", "exclude")
    })
    _resolved_scope_slugs = sorted(set(_served_program_slugs) | set(_program_override_slugs))
    discretionary_policy_view = {
        "project_default": (
            _raw_policy_facts.get("discretionary_policy_default")
            if _raw_policy_facts.get("discretionary_policy_default") in ("include", "exclude")
            else "include"
        ),
        "program_overrides": {
            slug: _raw_policy_facts[f"discretionary_policy_program:{slug}"]
            for slug in _program_override_slugs
        },
        "resolved_by_program": {
            slug: _discretionary_policy_resolve(slug, _raw_policy_facts)
            for slug in _resolved_scope_slugs
            if _is_discretionary_program(slug)
        },
    }

    has_master_artwork = await session.scalar(
        select(ProjectAsset.id).where(
            ProjectAsset.project_id == project.id,
            ProjectAsset.is_master.is_(True),
        ).limit(1)
    )

    production = {
        "production_id": str(project.id),
        "production_name": project.title,
        "jurisdiction_code": base_code,
        "project_id": str(project.id),
        "artwork_url": (
            f"/api/v1/projects/{project.id}/artwork" if has_master_artwork else None
        ),
        "lifecycle": project.lifecycle,
        "leading_structure_id": str(project.leading_structure_id) if project.leading_structure_id else None,
        "gross_budget_usd": gross_budget_usd,
        "rate": None,
        "rate_resolution": None,
        "rate_warnings": [],
        "budget_reconciliation": {
            "authoritative_gross_usd": gross_budget_usd,
            "leaf_account_sum_usd": leaf_account_sum_usd,
            "variance_usd": variance_usd,
            "note": reconciliation_note,
        },
        # FINANCE SEMANTICS (settled doctrine), served so the distinction is
        # checkable rather than a convention someone has to remember:
        #   source_budget_finance_usd -- financing ALREADY inside the source
        #     gross budget (classified SpendCategory.FINANCE_COSTS). It is
        #     part of gross, therefore already in NPC, and must NEVER be
        #     added again.
        #   financing_cost_usd (the producer assumption, elsewhere) means
        #     INCREMENTAL / OFF-BUDGET financing NOT already in gross.
        # Bridge PRINCIPAL is not a production cost and a monetization
        # haircut is not this field; neither is represented here.
        "finance_semantics": {
            "source_budget_finance_usd": source_budget_finance_usd,
            "producer_assumption_scope": "INCREMENTAL_OFF_BUDGET",
            "note": (
                "Financing already inside the source budget is part of gross and is "
                "already reflected in NPC. The producer's financing assumption is "
                "ADDITIONAL to this amount, never a restatement of it."
            ),
        },
        "production_structure_default": None,
        # Item B (Final non-Globe closeout, 2026-09-04) — see the
        # discretionary_policy_view build immediately above.
        "discretionary_policy": discretionary_policy_view,
        # Script Analyzer Full Production Breakdown: was hardcoded {} for
        # every generic project, so ProductionDetails.jsx's "Major
        # Location Requirements" panel always showed "No script analysis
        # available yet" regardless of real persisted
        # ProjectLocationRequirement rows. build_ui_location_categories
        # reads this project's own real SA-1 rows through the existing
        # abstract_location() ontology, same LOCATION_TAXONOMY/label
        # contract the demo's own _derive_location_categories() uses.
        "physical_requirements": {"location_categories": ui_location_categories},
        "territory_physical_match": {},
        "as_of_date": None,
        "computation": {"version": engine_version or ENGINE_VERSION, "computed_at": None},
    }

    comparable_count = len(comparable)
    # Bounded candidate retention (canonical-1.90.0): ``review_required`` above holds only the RETAINED
    # priced candidates; the EXACT count of priced non-comparable candidates comes from the generation
    # summary (retained + aggregated), never from the length of a bounded list.
    retained_review_required_count = len(review_required)
    review_required_count = (
        generation_totals["priced"] - comparable_count
        if fingerprint and generation_total_rows else retained_review_required_count
    )

    # Frozen Jurisdictions Globe: the best single/local-stack candidate per primary jurisdiction. Optimizer
    # Globe: the retained top candidates of each canonical structure_type. Both are read from the retained
    # decision set (candidate_retention.py), ordered by the verified NPC, ties by the canonical identity.
    def _retention_sort_key(e):
        return (
            e["npc_verified_usd"] if e["npc_verified_usd"] is not None else float("inf"),
            _identity_by_structure.get(e["structure_id"], ""),
        )

    def _retention_compact(e, rank=None):
        return {
            "structure_id": e["structure_id"], "structure_type": e["structure_type"],
            "primary_jurisdiction": e["primary_jurisdiction"], "label": e["label"],
            "npc_verified_usd": e["npc_verified_usd"], "npc_with_adjustments_usd": e["npc_with_adjustments_usd"],
            "selected_incentive_usd": e["selected_incentive_usd"], "is_baseline": e["is_baseline"],
            "economic_identity": _identity_by_structure.get(e["structure_id"]),
            **({"rank_in_type": rank} if rank is not None else {}),
        }

    _priced_entries = sorted((e for e in structure_entries if e["is_fully_priced"]), key=_retention_sort_key)
    # WORKSPACE_CANONICAL_JURISDICTION_WINNERS (2026-09-21): best_per_
    # jurisdiction now stores the FULL structure entry (the exact same
    # shape every `structures[]` array element already carries, plus its
    # real economic_identity -- never a second, compacted shape) instead
    # of the earlier _retention_compact() summary. Root cause this
    # corrects: Workspace's Single Jurisdiction cards were being
    # reconstructed client-side from the bounded, overall-rank-ordered
    # `structures[]` PAGE (candidates_page, limit 100) -- for a
    # production whose page is dominated by a different family (e.g. F#K
    # Valentine's Day's real page: 93 of the first 100 candidates by
    # OVERALL rank are HYBRID_ANCHOR_COMPONENT), only 5 of the real 76
    # jurisdiction winners this block already computes ever appeared in
    # that page, so the frontend's own per-jurisdiction reconstruction
    # necessarily saw duplicates/gaps that were never present in the
    # canonical retained set -- only in what got serialized onto page 1.
    # `structure_entries` (this loop's own source, built before ANY
    # pagination) already covers every RETAINED candidate, including
    # every jurisdiction's real winner (retention explicitly keeps "the
    # best single/local-stack candidate per jurisdiction" -- see
    # PROJECT_RULES.md's PERSISTENCE CARDINALITY RULE), so serving the
    # full entry here requires no new query, no new retention, no
    # discovery/pricing change -- only NOT throwing detail away before
    # this dict is populated.
    best_per_jurisdiction = _single_jurisdiction_winners(_priced_entries, _identity_by_structure)
    top_by_structure_type: dict[str, list] = {}
    for e in _priced_entries:
        _bucket = top_by_structure_type.setdefault(e["structure_type"], [])
        if len(_bucket) < TYPE_TOP:
            _bucket.append(_retention_compact(e, rank=len(_bucket) + 1))

    # GD-4 (Globe data contract remediation, 2026-09-20): `top_by_structure_
    # type` above buckets by the broad, persisted `structure_type` column,
    # which collapses every hybrid family (ordinary, combined-pair,
    # combined-component, combined-multi-component, multilateral) into one
    # `"hybrid"` bucket -- so a combined or multilateral winner could be
    # silently displaced by an unrelated ordinary hybrid competing for the
    # same TYPE_TOP slots. `top_by_structural_family` pins the canonical
    # best candidate for EVERY canonical family (using `classification`,
    # the same GD-2 backend-owned enum every served structure already
    # carries -- never a second, independently-derived family signal) from
    # the SAME already-computed, already-ranked `_priced_entries` list
    # (`_retention_sort_key`'s canonical NPC ranking, ties by canonical
    # economic identity -- no new ranking). Every priced-eligible family is
    # pre-seeded with an empty list so a production with no candidate in a
    # given family serves an honest `[]`, never a missing key.
    top_by_structural_family: dict[str, list] = {family: [] for family in _PRICED_STRUCTURE_FAMILIES}

    def _family_top_entry(e, rank):
        return {
            "structure_id": e["structure_id"],
            "structural_family": e["classification"],
            "structure_type": e["structure_type"],
            "label": e["label"],
            "primary_jurisdiction": e["primary_jurisdiction"],
            "participants": e["participants"],
            "npc_verified_usd": e["npc_verified_usd"],
            "npc_with_adjustments_usd": e["npc_with_adjustments_usd"],
            "selected_incentive_usd": e["selected_incentive_usd"],
            "candidate_status": e["candidate_status"],
            "is_baseline": e["is_baseline"],
            "economic_identity": _identity_by_structure.get(e["structure_id"]),
            "engine_version": engine_version or ENGINE_VERSION,
            "input_fingerprint": fingerprint,
            "rank_in_family": rank,
        }

    for e in _priced_entries:
        _family_bucket = top_by_structural_family.setdefault(e["classification"], [])
        if len(_family_bucket) < TYPE_TOP:
            _family_bucket.append(_family_top_entry(e, rank=len(_family_bucket) + 1))

    # COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21): the served candidate PAGE
    # (`structures[]`, below) and `top_by_structural_family` (just above, capped at
    # TYPE_TOP=100 per family) are both lossy views over `_priced_entries` -- confirmed live
    # for F#K Valentine's Day: 411 real PRICED HYBRID_ANCHOR_COMPONENT rows exist in
    # `_priced_entries`, of which the served page carried only 93 and
    # `top_by_structural_family` only 100, so a frontend built from either one silently
    # dropped the majority of real, priced, producer-selectable optimizer candidates. Root
    # cause: `admissibleForMode()` (workspaceScenarioMode.js) read only those two lossy views,
    # with a "family entirely absent" backstop that never helps a PARTIALLY-represented family
    # like this one.
    #
    # `optimizer_candidates` is the ONE authoritative, complete, canonical optimizer
    # projection every UI surface (Workspace rack/dropdown, Overview's count, Full Globe's
    # side list, Map, Split) must read from instead: every PRICED candidate whose
    # classification is in OPTIMIZER_STRUCTURE_FAMILIES (HYBRID_ANCHOR_COMPONENT,
    # OFFICIAL_COPRODUCTION, COMBINED_COPRO_HYBRID_STACK, MULTI_PRINCIPAL_MULTILATERAL --
    # never SINGLE_JURISDICTION or STACKED_PROGRAMS, which stay Single-Jurisdiction-mode-only
    # per the existing, unchanged admissibleForMode() contract), uncapped, in the same
    # already-computed `_priced_entries` NPC order, each carrying full economics/participant/
    # component detail (the exact same shape as every `structures[]` element -- no new query,
    # no re-derivation, no economics/discovery/pruning change, no ENGINE_VERSION bump: this
    # reads what candidate_retention.py already retained and canonical_evaluation.py already
    # priced). `structure_entries` rows are already one-per-`economic_identity` by
    # construction (confirmed live: 0 duplicate economic_identity values across FVD's full
    # 855-row retained set), so no additional dedup pass is required -- `dict.fromkeys` below
    # is a defensive belt-and-suspenders guard, not a correction of an observed defect.
    _optimizer_entries_raw = [e for e in _priced_entries if e["classification"] in _OPTIMIZER_STRUCTURE_FAMILIES]
    _optimizer_by_identity = {
        (_identity_by_structure.get(e["structure_id"]) or e["structure_id"]): e for e in _optimizer_entries_raw
    }
    optimizer_candidates = list(_optimizer_by_identity.values())
    optimizer_candidates_total = len(optimizer_candidates)
    optimizer_candidates_by_family = {
        family: sum(1 for e in optimizer_candidates if e["classification"] == family)
        for family in sorted(_OPTIMIZER_STRUCTURE_FAMILIES)
    }

    # PRODUCER_OPTIMIZER_PRESENTATION_CORRECTION (2026-09-22) -- corrects the prior pass's
    # `_scenario_topology_key`, which built its (jurisdiction, program) pairs from
    # `segments` when present and otherwise `component_allocations`, and reduced the
    # component/category to a bare `is_principal` boolean. Confirmed live this was WRONG on
    # two counts: (1) every optimizer_candidates row has non-empty `component_allocations`
    # (0/411 empty across F#K Valentine's Day; the same holds for all four productions),
    # so that field -- never `segments`, which for "component/split" structures carries no
    # per-component label at all -- is the one reliable source of which real category was
    # routed where; (2) collapsing the real component label to a bare principal/non-
    # principal boolean silently merged materially different producer decisions -- e.g.
    # Greece-anchor structures routing $146,446 of POST-production spend to Manitoba
    # (component "post") vs routing only $10,200 of MUSIC spend (component "music") vs
    # $10,000 of VFX spend (component "vfx") previously collapsed into one scenario despite
    # being three different real allocation decisions with three different dollar amounts.
    #
    # `optimizer_scenarios` is the ONE canonical producer-facing projection: one entry per
    # materially distinct route, keyed by (classification, primary_jurisdiction, sorted
    # participants, sorted (jurisdiction_code, program_slug, component) triples read
    # EXCLUSIVELY from component_allocations, treaty_slug) -- explicitly excluding only
    # structure_id, economic_identity, search/enumeration order, and immaterial rounding.
    # The routed component/category is now a first-class, load-bearing part of the key (not
    # reduced to a boolean): two candidates whose component differs for the same
    # (jurisdiction, program) pair are two different scenarios, never merged. Confirmed live
    # against all four productions with this corrected key: 0 of the 411/171/267/541 raw
    # candidates currently collapse -- every raw candidate this generation really is a
    # materially distinct route once the component is respected correctly. The grouping
    # logic itself still collapses a genuine byte-identical duplicate discovery path (same
    # classification/jurisdiction/participants/component-triples) when one exists -- pinned
    # with a synthetic fixture in the test suite since none occurs in this live generation.
    # The lowest-verified-NPC member of each group is the representative (a shallow copy,
    # annotated with raw_variant_count/raw_variant_structure_ids/
    # raw_variant_economic_identities for audit traceability) -- optimizer_candidates itself
    # is never mutated.
    def _scenario_topology_key(e):
        rows = e.get("component_allocations") or []
        triples = {
            (r.get("jurisdiction_code"), r.get("program_slug"), r.get("component")) for r in rows
        }
        return (
            e.get("classification"),
            e.get("primary_jurisdiction"),
            tuple(sorted(e.get("participants") or [])),
            tuple(sorted(triples, key=lambda t: (t[0] or "", t[1] or "", t[2] or ""))),
            e.get("treaty_slug"),
        )

    def _npc_sort_key(e):
        return (
            e["npc_verified_usd"] if e.get("npc_verified_usd") is not None else float("inf"),
            _identity_by_structure.get(e["structure_id"], ""),
        )

    # PRODUCER_PRACTICALITY_TIER (2026-09-22): a presentation-only ordering signal derived
    # entirely from facts the structure already carries (classification, distinct
    # participant count) -- never a new dollar figure, never a change to canonical NPC or
    # any economics. PRACTICAL_HYBRID (exactly two distinct jurisdictions, one principal +
    # one routed leg) is what most producers can operationally execute with the least legal/
    # administrative overhead; FORMAL_COPRODUCTION (an official treaty/co-production, even
    # at two jurisdictions -- treaty machinery is its own overhead regardless of jurisdiction
    # count) and ADVANCED_MULTI_JURISDICTION (three or more distinct jurisdictions, or a
    # combined/multilateral structure) carry progressively more real coordination burden.
    # Ties within a tier still break by ascending canonical NPC -- economics are never
    # overridden, only grouped.
    TIER_PRACTICAL = "PRACTICAL_HYBRID"
    TIER_FORMAL = "FORMAL_COPRODUCTION"
    TIER_ADVANCED = "ADVANCED_MULTI_JURISDICTION"
    _TIER_RANK = {TIER_PRACTICAL: 0, TIER_FORMAL: 1, TIER_ADVANCED: 2}

    def _practicality_tier(e):
        if e.get("classification") == "OFFICIAL_COPRODUCTION":
            return TIER_FORMAL
        n_participants = len(set(e.get("participants") or []))
        if e.get("classification") == "HYBRID_ANCHOR_COMPONENT" and n_participants == 2:
            return TIER_PRACTICAL
        return TIER_ADVANCED

    def _scenario_sort_key(e):
        return (_TIER_RANK[e["practicality_tier"]], *_npc_sort_key(e))

    _scenario_groups: dict[tuple, list[dict]] = {}
    for _e in optimizer_candidates:
        _scenario_groups.setdefault(_scenario_topology_key(_e), []).append(_e)

    optimizer_scenarios = []
    for _group in _scenario_groups.values():
        _group_sorted = sorted(_group, key=_npc_sort_key)
        _rep = dict(_group_sorted[0])
        _rep["raw_variant_count"] = len(_group_sorted)
        _rep["raw_variant_structure_ids"] = [g["structure_id"] for g in _group_sorted]
        _rep["raw_variant_economic_identities"] = [
            _identity_by_structure.get(g["structure_id"]) for g in _group_sorted
        ]
        _rep["practicality_tier"] = _practicality_tier(_rep)
        _rep["participant_count"] = len(set(_rep.get("participants") or []))
        optimizer_scenarios.append(_rep)
    # Producer-facing order: Practical -> Formal -> Advanced, ascending NPC within each tier.
    # Every UI surface (Workspace rack/dropdown, Overview, Full Globe, Map, Split) consumes
    # this array verbatim and in THIS order -- no separate client-side re-sort.
    optimizer_scenarios.sort(key=_scenario_sort_key)
    optimizer_scenarios_total = len(optimizer_scenarios)
    optimizer_scenarios_by_family = {
        family: sum(1 for e in optimizer_scenarios if e["classification"] == family)
        for family in sorted(_OPTIMIZER_STRUCTURE_FAMILIES)
    }
    optimizer_scenarios_by_tier = {
        TIER_PRACTICAL: sum(1 for e in optimizer_scenarios if e["practicality_tier"] == TIER_PRACTICAL),
        TIER_FORMAL: sum(1 for e in optimizer_scenarios if e["practicality_tier"] == TIER_FORMAL),
        TIER_ADVANCED: sum(1 for e in optimizer_scenarios if e["practicality_tier"] == TIER_ADVANCED),
    }

    _baseline_entry = next((e for e in structure_entries if e.get("is_baseline")), None)
    (
        producer_optimizer_options,
        producer_optimizer_excluded_counts,
        producer_optimizer_baseline_npc_usd,
    ) = _build_producer_optimizer_projection(optimizer_scenarios, _baseline_entry)
    producer_optimizer_options_total = len(producer_optimizer_options)
    producer_optimizer_options_by_type = {
        TIER_PRACTICAL: sum(
            1 for e in producer_optimizer_options
            if e["producer_optimizer_option_type"] == TIER_PRACTICAL
        ),
        TIER_FORMAL: sum(
            1 for e in producer_optimizer_options
            if e["producer_optimizer_option_type"] == TIER_FORMAL
        ),
    }

    # ── Bounded candidate page ────────────────────────────────────────────────────────────
    # Everything above (selection, ranking, conditional pool, accounting) ran over ALL served
    # candidates. What is RETURNED in detail is one deterministic page of them: the headline
    # candidates (selected structure, leading conditional structure, baseline) first, then the
    # ranking order. Pages partition that sequence, so following next_cursor returns every
    # served candidate exactly once.
    _page_limit = max(1, min(int(candidate_limit), CANDIDATE_PAGE_MAX_LIMIT))
    _page_offset = max(0, int(candidate_offset))
    _entry_by_id = {e["structure_id"]: e for e in structure_entries}
    _ranking_by_id = {r["structure_id"]: r for r in ranking}
    _pinned = [
        i for i in dict.fromkeys([
            canonical_selected_structure_id,
            _leading_conditional_id,
            next((e["structure_id"] for e in structure_entries if e["is_baseline"]), None),
        ]) if i
    ]
    _pinned_set = set(_pinned)
    _sequence = _pinned + [r["structure_id"] for r in ranking if r["structure_id"] not in _pinned_set]
    _page_ids = _sequence[_page_offset:_page_offset + _page_limit]
    _has_more = _page_offset + _page_limit < len(_sequence)
    candidates_page = {
        "limit": _page_limit,
        "offset": _page_offset,
        "returned": len(_page_ids),
        "total": len(_sequence),
        "has_more": _has_more,
        "next_cursor": (
            encode_candidate_cursor(fingerprint, _page_offset + _page_limit) if _has_more and fingerprint else None
        ),
        "order": _CANDIDATE_ORDER,
        "results_route": CANDIDATES_ROUTE.format(project_id=project.id),
    }
    page_entries = [_entry_by_id[i] for i in _page_ids]
    page_ranking = [_ranking_by_id[i] for i in _page_ids]
    _alternatives_total = len(unlockable_alternatives)
    page_alternatives = unlockable_alternatives[:CANDIDATE_PAGE_MAX_LIMIT]

    structures = {
        "candidates": [],
        "pruned": [],
        "allocated_structures": {
            "version": engine_version or ENGINE_VERSION,
            "note": (
                "Generic canonical evaluation (any project) — regional "
                "production-cost normalization (MFNI) and generic travel/FX "
                "normalization are not yet applied; see each structure's "
                "own relocation_cost_normalized flag."
            ),
            "coverage": {
                # distinct, first-seen order: bounded by the number of jurisdictions
                "executable_jurisdictions": list(dict.fromkeys(
                    e["primary_jurisdiction"] for e in structure_entries if e["primary_jurisdiction"]
                )),
                "catalog_only_excluded": None,
                "reachable_treaty_partners": [],
                "categories": [],
                "note": None,
            },
            "discovery": {
                "metrics": {},
                "generated_structures": generation_total_rows or len(structure_entries),
                "optimized_structures": len(comparable) + len(review_required),
                "final_ranked_structures": len(comparable),
                "production_requirements": {"environments": [], "infrastructure": [], "required_capabilities": []},
                "examinations": [],
            },
            "structures": page_entries,
            "candidates_page": candidates_page,
            # Every unpriced (no-number) candidate of this evaluation -- the RULE_REJECTED
            # universe included -- as exact totals + a bounded first page. The remainder is
            # paged from results_route; has_more/next_cursor make that explicit.
            "rejection_universe": {
                "total_count": generation_totals["total"],
                "by_disposition": generation_totals["by_disposition"],
                "by_reason": generation_totals["by_reason"],
                "first_page": rejection_first_page,
                "results_route": UNPRICEABLE_RESULTS_ROUTE.format(project_id=project.id),
                "aggregates": candidate_aggregates_block(project.id, generation_totals, aggregate_groups_first_page)
                if generation_total_rows else None,
            } if fingerprint else None,
            "contingency": {},
            "ranking": page_ranking,
            # Item A (canonical scenario-selection consistency) — see the
            # long comment above where this is computed. The single
            # authoritative structure_id every non-Globe surface (Overview,
            # Workspace, Reports) must resolve to when no producer override
            # is active. None only when no structure is fully priced yet.
            "canonical_selected_structure_id": canonical_selected_structure_id,
            # Codex final P0 (leading conditional recommendation) — see
            # the conditional_pool comment above `ranking`'s own build
            # loop. None whenever a verified winner already exists
            # (canonical_selected_structure_id is not None) or no
            # is_directly_comparable priced candidate is blocked only by
            # a genuinely unlockable qualification state.
            "leading_conditional_structure": leading_conditional_structure,
            "unlockable_alternatives": page_alternatives,
            "unlockable_alternatives_total": _alternatives_total,
            "unlockable_alternatives_has_more": _alternatives_total > len(page_alternatives),
            "stack_combinations": {},
            "advisor_routing_decisions_input": {},
            # Restoration-phase candidate accounting, matching the earlier
            # generic Workspace's own classification (Part J/K/L/N) so both
            # UIs agree: PRICED + relocation_cost_normalized -> comparable
            # (own base jurisdiction); PRICED, not normalized -> review
            # required (a real economics figure, just not regionally
            # comparable yet); UNPRICEABLE -> authority insufficient.
            "best_per_jurisdiction": best_per_jurisdiction,
            "top_by_structure_type": top_by_structure_type,
            "top_by_structural_family": top_by_structural_family,
            # COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21): the ONE authoritative,
            # uncapped, deduplicated-by-economic_identity optimizer projection -- see the
            # comment above `_optimizer_entries_raw`'s construction for the full root-cause
            # narrative. Every optimizer-consuming UI surface must read this field, never
            # reconstruct a pool from `structures[]` or `top_by_structural_family`.
            "optimizer_candidates": optimizer_candidates,
            "optimizer_candidates_total": optimizer_candidates_total,
            "optimizer_candidates_by_family": optimizer_candidates_by_family,
            # PRODUCER_OPTIMIZER_SCENARIO_CANONICALIZATION (2026-09-21): the ONE canonical
            # producer-facing projection every UI surface must read from -- see the comment
            # above `_scenario_topology_key`'s construction for the full grouping contract.
            "optimizer_scenarios": optimizer_scenarios,
            "optimizer_scenarios_total": optimizer_scenarios_total,
            "optimizer_scenarios_by_family": optimizer_scenarios_by_family,
            # PRODUCER_OPTIMIZER_PRESENTATION_CORRECTION (2026-09-22): counts for the
            # truthful "N distinct optimized scenarios / P practical / F formal
            # co-productions / A advanced" disclosure every optimizer-consuming surface
            # must show instead of the raw iteration count.
            "optimizer_scenarios_by_tier": optimizer_scenarios_by_tier,
            # Practical producer projection.  Exhaustive optimizer_candidates/
            # optimizer_scenarios above remain unchanged as audit evidence.
            "producer_optimizer_options": producer_optimizer_options,
            "producer_optimizer_options_total": producer_optimizer_options_total,
            "producer_optimizer_options_by_type": producer_optimizer_options_by_type,
            "producer_optimizer_excluded_counts": producer_optimizer_excluded_counts,
            "producer_optimizer_baseline_npc_usd": producer_optimizer_baseline_npc_usd,
            "retention": {
                "policy": {
                    "global_top": GLOBAL_TOP, "per_structure_type_top": TYPE_TOP,
                    "best_local_candidate_per_jurisdiction": True,
                    "all_proof_and_opportunity_rows_capped": True, "note": RETENTION_POLICY_NOTE,
                },
                "retained_rows": len(rows),
                "generated_candidates": generation_totals.get("generated", len(rows)),
                "aggregated_candidates": generation_totals.get("aggregated_candidates", 0),
            },
            "candidate_accounting": {
                "comparable_count": comparable_count,
                "review_required_count": review_required_count,
                "retained_review_required_count": retained_review_required_count,
                "unpriceable_count": generation_totals["total"] if fingerprint and generation_total_rows else len(unpriced),
            },
        },
    }

    return {"status": "OK", "production": production, "structures": structures}


# ─────────────────────────────────────────────────────────────────────────
# Codex Defect 5 — generic project sections (pkg/economics/people/facts)
# ─────────────────────────────────────────────────────────────────────────
#
# get_project_state()'s generic (non-Little-Utopia) branch previously
# substituted EMPTY_PKG/EMPTY_ECONOMICS/EMPTY_PEOPLE/EMPTY_FACTS for every
# project, even when real budget/requirement/people/fact data exists —
# Overview's Budget Rail and Production Facts panel therefore rendered
# empty even though the structure cards above them had real economics.
# This adapts EXISTING persisted rows into the same shapes those two
# components already read; it computes no economics and recreates no
# calculation, reusing the leading structure's OWN already-persisted
# register_trace (Codex Defect 3) for pkg.register.

#: ProjectPerson.role -> the EMPTY_PEOPLE bucket key (mirrors
#: frontend/src/lib/personRoles.js's PERSON_ROLES exactly, so the same
#: role vocabulary UI edits write is the one this reads back).
_PEOPLE_ROLE_TO_BUCKET = {
    "writer": "writers", "director": "directors", "producer": "producers",
    "lead_cast": "cast", "lead_cast_2": "lead_cast_2", "lead_cast_3": "lead_cast_3",
    "dop": "dop", "editor": "editor", "composer": "composer",
}


async def build_generic_pkg_and_economics(session: AsyncSession, project_id) -> dict:
    """Real pkg/economics/people/facts for a generic (non-demo) project,
    from persisted data only. Honest empty values where nothing exists —
    never fabricated, never Little Utopia's."""
    project = await session.get(Project, project_id)
    if project is None:
        return {"status": "PROJECT_NOT_FOUND"}

    # ── register + budget totals: the production's own BASELINE
    # structure's already-persisted segments (Codex Defect 3 restored
    # qualification_trace). Final Consolidated Backend Correction +
    # Global Structuring Intelligence Acceptance, Part 4/CBA-001: reads
    # the baseline directly (is_baseline trace flag, current
    # ENGINE_VERSION), never leading_structure_id — that field is
    # correctly None whenever no candidate currently admits Recommended,
    # but the baseline's own real, priced register must still be
    # disclosed either way.
    register: list[dict] = []
    line_item_count = 0
    total_budget_usd = None
    currency_code = None
    filename = None
    # STALE-STATE PREVENTION (item 8). ENGINE_VERSION alone is NOT a
    # freshness filter: a rule or pricing-source change now invalidates the
    # fingerprint on its own, so several superseded generations legitimately
    # coexist under one engine version. Reading them all and taking the first
    # is_baseline row served a register computed from inputs that are no
    # longer true. Pin the read to the CURRENT generation.
    #
    # Optimizer FINAL closeout, P1-FRESH-001 (Codex, full optimizer audit +
    # final P0 delta reaudit) — this previously called
    # current_result_fingerprint() directly: the newest current-engine ROW,
    # not necessarily the fingerprint matching the project's CURRENT facts
    # after a reverted assumption. build_production_and_structures() above
    # already reconstructed the true current fingerprint from live facts;
    # this function used the cheaper-but-wrong newest-row read instead,
    # so the two views could genuinely diverge onto different real,
    # legitimately-persisted generations for the same project. Confirmed
    # live for F#K Valentine's Day and Lips Like Sugar. Both views now call
    # the SAME shared reconstruction (current_generation_fingerprint) —
    # never a second freshness architecture.
    from app.services.canonical_evaluation import current_generation_fingerprint
    current_fingerprint = await current_generation_fingerprint(session, project.id)
    # Bounded read (2026-09-19): this previously loaded EVERY row of the current generation
    # (526,155 ORM objects for F#K Valentine's Day) only to pick out the baseline. The baseline
    # is fetched directly (see _load_baseline_results); the generation is never read.
    baseline_rows = (
        [r for r, _ in await _load_baseline_results(session, project.id, current_fingerprint)]
        if current_fingerprint else []
    )
    leading_result = next(
        (r for r in baseline_rows if (r.calculation_trace_json or {}).get("is_baseline")), None,
    )
    if leading_result is not None:
        trace = leading_result.calculation_trace_json or {}
        for seg in trace.get("segments") or []:
            for a in seg.get("qualification_trace") or []:
                register.append({
                    "account_code": a.get("account_code"),
                    "description": a.get("description"),
                    "amount_usd": a.get("amount_usd"),
                    "state": a.get("state"),
                    # LU's richer register carries confidence/grey_reason/
                    # structuring_mechanism/incentive_upside — not yet
                    # computed generically; honest nulls, not invented.
                    "confidence": "unknown",
                    "authority_basis": a.get("authority_basis"),
                    "reason": a.get("reason"),
                    "grey_reason": None,
                    "financial_impact_usd": None,
                    "structuring_mechanism": None,
                    "resolving_evidence": None,
                    "incentive_upside_usd": None,
                })
        total_budget_usd = (
            float(leading_result.total_budget_usd) if leading_result.total_budget_usd is not None else None
        )

    # Production Page Integrity: the compact producer-facing budget
    # COMPOSITION breakdown (Section 5/6's "what the production costs")
    # is intentionally sourced from the raw, real, persisted
    # BudgetLineItem rows — never from `register` above, which requires
    # a fully-priced, is_baseline StructureCalculationResult (a
    # jurisdiction-pricing outcome) and is legitimately empty for a
    # project whose own home jurisdiction isn't priced (Lips Like
    # Sugar's/Bad Hombres' own real state). The real budget composition
    # exists and is knowable regardless of whether ANY jurisdiction
    # pricing succeeded — the two were previously conflated by having
    # the ONLY breakdown source be pricing-dependent. Grouped by the
    # SAME generic classify_budget_line_items.py spend_category/
    # atl_btl taxonomy every project's real ingestion already assigns
    # per line — never a second/invented category vocabulary.
    line_items_for_breakdown: list[BudgetLineItem] = []
    budget_doc = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project.id)
        .order_by(BudgetDocument.created_at.desc())
    )).scalars().first()
    if budget_doc is not None:
        filename = budget_doc.filename
        currency_code = budget_doc.currency_code
        if total_budget_usd is None and budget_doc.total_budget_raw is not None:
            total_budget_usd = float(budget_doc.total_budget_raw)
        line_items_for_breakdown = (await session.execute(
            select(BudgetLineItem).where(BudgetLineItem.budget_document_id == budget_doc.id)
        )).scalars().all()
        line_item_count = len(line_items_for_breakdown)

    atl_total = btl_total = post_total = other_total = labor_total = non_labor_total = 0.0
    totals_by_spend_category: dict[str, float] = {}
    # Production Overview + Project Globe UI regression repair, Section 4:
    # `department` is a SECOND real, already-imported field on every
    # BudgetLineItem (parsed by budget_parser.py's own _dept_for_acct — the
    # source document's own top-sheet section headers, e.g. "Above The
    # Line" / "Production" / "Post Production" / "Other" — never invented
    # here). Exposed alongside spend_category rather than replacing it:
    # spend_category is the finer, canonical taxonomy but a project whose
    # real budget skews heavily into categories the classifier maps to
    # "miscellaneous" reads as an unhelpful single bucket at that
    # granularity; department is the coarser grouping the source document
    # itself already uses, and every bucket it produces is a real section
    # name, never a generic catch-all.
    totals_by_department: dict[str, float] = {}
    for item in line_items_for_breakdown:
        amt = float(item.amount_usd) if item.amount_usd is not None else 0.0
        bucket = getattr(item.atl_btl, "value", item.atl_btl)
        if bucket == "atl":
            atl_total += amt
        elif bucket == "btl":
            btl_total += amt
        elif bucket == "post":
            post_total += amt
        else:
            other_total += amt
        if item.is_labor:
            labor_total += amt
        else:
            non_labor_total += amt
        category = getattr(item.spend_category, "value", item.spend_category) or "miscellaneous"
        totals_by_spend_category[category] = round(totals_by_spend_category.get(category, 0.0) + amt, 2)
        department = item.department or "Other"
        totals_by_department[department] = round(totals_by_department.get(department, 0.0) + amt, 2)

    pkg = {
        "production_id": str(project.id),
        "confidence": "unknown",
        "is_ready_for_downstream_engines": bool(register),
        "register": register,
        "budget": {
            "known": budget_doc is not None, "filename": filename, "currency_code": currency_code,
            "total_budget_usd": total_budget_usd,
            "line_item_count": line_item_count,
            "atl_total_usd": round(atl_total, 2) if line_items_for_breakdown else None,
            "btl_total_usd": round(btl_total, 2) if line_items_for_breakdown else None,
            "post_total_usd": round(post_total, 2) if line_items_for_breakdown else None,
            "other_total_usd": round(other_total, 2) if line_items_for_breakdown else None,
            "labor_usd": round(labor_total, 2) if line_items_for_breakdown else None,
            "non_labor_usd": round(non_labor_total, 2) if line_items_for_breakdown else None,
            "totals_by_spend_category_usd": totals_by_spend_category,
            "totals_by_department_usd": totals_by_department,
            "opportunity_hints": [],
            # Drill-down (Section 7): real line identity, never dropped —
            # account code parsed from the SAME leading-code convention
            # canonical_project_economics.py's own _ACCOUNT_CODE_RE
            # already uses to build the priced register, so a producer
            # sees the identical code either way.
            "line_items": [
                {
                    "line_id": str(item.id),
                    "account_code": (m.group(1) if (m := _ACCOUNT_CODE_RE.match(item.description or "")) else None),
                    "description": item.description,
                    "amount_usd": float(item.amount_usd) if item.amount_usd is not None else None,
                    "spend_category": getattr(item.spend_category, "value", item.spend_category),
                    "department": item.department,
                    "atl_btl": getattr(item.atl_btl, "value", item.atl_btl),
                }
                for item in line_items_for_breakdown
            ],
        },
        "script": {
            "known": False, "filename": None, "page_count": None, "word_count": None,
            "locations_mentioned": [], "character_names": [], "attributes": {},
        },
        "package_people_count": 0, "package_entities_count": 0, "location_count": 0,
        "missing_inputs": [],
    }

    # ── people: real ProjectPerson + TalentProfile rows, bucketed by the
    # same role vocabulary PERSON_ROLES/ProductionDetails.jsx already use ──
    people_rows = (await session.execute(
        select(ProjectPerson, TalentProfile)
        .join(TalentProfile, ProjectPerson.talent_id == TalentProfile.id)
        .where(ProjectPerson.project_id == project.id)
    )).all()
    people: dict = {
        "writers": [], "directors": [], "cast": [], "producers": [],
        "lead_cast_2": [], "lead_cast_3": [], "dop": [], "editor": [], "composer": [],
        "overrides": {}, "missing_inputs": [],
    }
    for pp, tp in people_rows:
        bucket = _PEOPLE_ROLE_TO_BUCKET.get(pp.role)
        if bucket is None:
            continue
        people[bucket].append({
            "person_id": str(tp.id), "name": tp.name,
            "nationality": tp.primary_nationality,
            "confirmed": pp.is_confirmed,
            "nationality_resolution_status": tp.nationality_resolution_status,
        })

    # Production Overview Truthfulness: pkg["missing_inputs"] (what
    # ProjectHeader.jsx's "Questions Remaining", Workspace.jsx's
    # QuestionStack, Reports.jsx, and Today.jsx's onboarding all actually
    # read — never people["missing_inputs"], a same-named but unconsumed
    # sibling field) was hardcoded to [] for every generic (non-demo)
    # project, so the metric read 0 even when Production Facts visibly
    # showed unresolved personnel. Real, generic definition — not the
    # heavyweight Question Engine in production_package_intelligence.py,
    # which needs a full PackageIntelligence assembly not yet wired to
    # per-project data (a separate, larger capability, not invented
    # here): a PRIMARY role (writer/director/producer/lead_cast — the
    # roles discovery can realistically fill) with no name at all is a
    # missing input; any role WITH a name but no resolved nationality is
    # also a missing input, mirroring exactly the two states
    # ProductionDetails.jsx's own `pd-missing` styling already flags
    # visually. The optional recurring slots (lead_cast_2/3, dop, editor,
    # composer) are open-by-design until a producer fills them and do not
    # count merely for being empty, but DO count once named without a
    # resolved nationality. Shaped like production_package_intelligence.
    # py's own MissingInput (identifier/question/blocking/...) so every
    # existing consumer (QuestionStack included) renders it correctly
    # with no special-casing.
    _PRIMARY_ROLE_BUCKETS = ("writers", "directors", "producers", "cast")
    _ROLE_LABEL = {
        "writers": "writer", "directors": "director", "producers": "producer(s)",
        "cast": "lead cast", "lead_cast_2": "lead cast (2)", "lead_cast_3": "lead cast (3)",
        "dop": "director of photography", "editor": "editor", "composer": "composer",
    }
    pkg_missing_inputs: list[dict] = []
    for role_bucket, entries in people.items():
        if role_bucket in ("overrides", "missing_inputs"):
            continue
        label = _ROLE_LABEL.get(role_bucket, role_bucket)
        if not entries:
            if role_bucket in _PRIMARY_ROLE_BUCKETS:
                pkg_missing_inputs.append({
                    "identifier": f"MISSING-{role_bucket.upper()}-NAME",
                    "question": f"Who is the production's {label}?",
                    "why_it_matters": (
                        "Personnel identity is a qualification input for treaty "
                        "co-production, cultural tests, and national-status tests."
                    ),
                    "downstream_engines": [],
                    "optimizer_value": "unknown",
                    "blocking": False,
                    "discovery_hooks": [],
                })
            continue
        for entry in entries:
            if entry.get("name") and not entry.get("nationality"):
                pkg_missing_inputs.append({
                    # PROJECT_UI_DATA_INTEGRITY (2026-09-21): the
                    # identifier used to be bare MISSING-{ROLE}-
                    # NATIONALITY, with no per-person component --
                    # harmless while a role bucket never held more than
                    # one real name, but a real, confirmed defect once
                    # document-person extraction (app/ingestion/document_
                    # person_ingestion.py) can attach several real people
                    # to the SAME role bucket (e.g. four producers):
                    # every one of their questions collided on the
                    # identical identifier, which QuestionStack.jsx keys
                    # its list by -- a live "duplicate key" React error,
                    # confirmed in the browser against F#K Valentine's
                    # Day's own real producers. person_id is already a
                    # real, stable identity (TalentProfile.id) -- never
                    # fabricated.
                    "identifier": f"MISSING-{role_bucket.upper()}-NATIONALITY-{entry['person_id']}",
                    "question": f"What is {entry['name']}'s ({label}) nationality?",
                    "why_it_matters": (
                        "Nationality is a qualification input for treaty co-production, "
                        "cultural tests, and national-status tests."
                    ),
                    "downstream_engines": [],
                    "optimizer_value": "unknown",
                    "blocking": False,
                    "discovery_hooks": [],
                })
    pkg["missing_inputs"] = pkg_missing_inputs

    # ── facts: real ProjectFact rows, verbatim ──
    fact_rows = (await session.execute(
        select(ProjectFact).where(ProjectFact.project_id == project.id).order_by(ProjectFact.fact_key)
    )).scalars().all()
    facts = {
        "answers": {f.fact_key: f.value for f in fact_rows},
        "answerable": {},
    }

    # ── production requirements: real SA-1 ProductionRequirement rows,
    # disclosed as their own real requirement_key/normalized_value pairs
    # (NOT mapped into the environment/infrastructure capability
    # vocabulary derive_production_requirements() consumes — see the
    # canonical_evaluation.py comment on that boundary; this is a
    # DIFFERENT, honest shape, not a substitute for that mapping) ──
    requirement_rows = (await session.execute(
        select(ProductionRequirement).where(ProductionRequirement.project_id == project.id)
    )).scalars().all()
    requirements_disclosed = [
        {
            "requirement_key": r.requirement_key,
            "normalized_value": r.normalized_value,
            "authority": r.evidence_state,
            "requires_confirmation": r.requires_confirmation,
        }
        for r in requirement_rows
    ]

    # Workspace Data Completeness: fx_horizons/jurisdiction_currency were
    # hardcoded to {} here for every generic project (the SAME "served
    # placeholder never wired to real data" pattern as physical_requirements
    # before it) even though the real, sourced FX snapshot data
    # (production_normalization.py's fx_rate_snapshot()/FX_RATE_SNAPSHOTS —
    # genuinely fetched from ECB via frankfurter.dev and open.er-api.com,
    # never fabricated) and the real jurisdiction->currency identity map
    # (_JURISDICTION_CURRENCY) already existed and were already correctly
    # wired into the legacy cineglobe.py _economics_payload() for the old
    # Little Utopia-only /production route. Reused verbatim here — same
    # currency set, same function, same source — so every project (this
    # generic path now serves Little Utopia too, per get_project_state's
    # own "no production title may select economic logic" contract) gets
    # the same real FX data the legacy route already proved correct.
    import app.calculators.production_normalization as _fx_doctrine
    from app.calculators.production_normalization import (
        fx_rate_snapshot, _JURISDICTION_CURRENCY, FX_HORIZON_DATES, FX_RATES_VERSION,
    )
    fx_codes = sorted({"MUR", "EUR", "GBP", "CAD"} | set(_JURISDICTION_CURRENCY.values()))
    fx_horizons = {c: fx_rate_snapshot(c) for c in fx_codes}

    economics = {
        "production_structure_default": None, "verified_cash_qpe_usd": None,
        "verified_floor_case": None, "potential_ceiling_case": None, "inkind_post_options": {},
        "financing_source": None, "controls": {}, "normalized_structures": [],
        "fx_horizons": fx_horizons, "jurisdiction_currency": dict(_JURISDICTION_CURRENCY),
        # Provenance for the snapshot above (Workspace Data Completeness):
        # real retrieval dates per horizon, real source, real snapshot
        # version — read live off production_normalization.py's module
        # state (Overview FX Strip Freshness Architecture), never a
        # hardcoded string frozen at whatever the source happened to say
        # when this file was last edited — so a live refresh's real
        # source/date is what actually reaches the UI, never a stale
        # literal.
        "fx_horizon_dates": dict(FX_HORIZON_DATES),
        "fx_source": _fx_doctrine.FX_LIVE_SNAPSHOT_SOURCE,
        "fx_snapshot_version": FX_RATES_VERSION,
        # Truthful freshness disclosure (never silently upgraded to
        # "fresh" on a failed refresh) — "fresh" | "stale_fallback" |
        # "never_refreshed". See app/services/fx_refresh.py.
        "fx_freshness_status": _fx_doctrine.FX_FRESHNESS_STATUS,
        "fx_last_refresh_error": _fx_doctrine.FX_LAST_REFRESH_ERROR,
        "alternative_jurisdictions": [],
        "available_funds": [], "structuring_advisory": None,
        "production_requirements_disclosed": requirements_disclosed,
    }

    return {"status": "OK", "pkg": pkg, "economics": economics, "people": people, "facts": facts}
