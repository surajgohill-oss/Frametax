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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.executable_jurisdiction_registry import get_doctrine
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.jurisdiction import Jurisdiction
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.production_requirement import ProductionRequirement
from app.models.project import Project
from app.models.project_fact import ProjectFact
from app.models.project_person import ProjectPerson
from app.models.talent import TalentProfile
from app.services.canonical_evaluation import (
    ENGINE_VERSION,
    _QUALIFICATION_ADMITS_RECOMMENDED,
)

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
    # structure_type: rows generated before the 1.1.0 enrichment don't carry
    # this in trace_json — derive the same value generically from is_baseline
    # (present on every engine_version since Phase 2) rather than requiring
    # every already-evaluated project to be re-evaluated first. Display-only,
    # same fact the label itself already encodes ("X — production's current
    # base" vs "Full relocation to X").
    structure_type = trace.get("structure_type") or (
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
    if structure_type == "component_relocation":
        _primary_claims = next(
            (
                _seg.get("claims_incentive") is True
                for _seg in trace.get("segments") or []
                if _seg.get("jurisdiction_code") == code
            ),
            False,
        )
        _participant_codes = [code] if (code and _home_is_party and _primary_claims) else []
        for _seg in trace.get("segments") or []:
            _c = _seg.get("jurisdiction_code")
            if _c and _seg.get("claims_incentive") is True and _c not in _participant_codes:
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
        "is_fully_priced": is_priced,
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
    """Final Consolidated Backend Correction + Global Structuring
    Intelligence Acceptance, Part 4/CBA-001 — a candidate whose
    qualification is real but genuinely UNRESOLVED (Curable Gap/User
    Fact Required/Script Fact Required/Authority Unresolved/Rule Data
    Incomplete) is priced normally (canonical_evaluation.py admits it to
    STATUS_PRICED; see _QUALIFICATION_ADMITS_PRICING there) and
    disclosed with real economics, but must never be presented as the
    comparable, rankable, RECOMMENDED winner — truthful unresolved
    status is preferable to false recommendation, even when that leaves
    a project with no Recommended scenario at all. Absent role_
    qualification (a program the bridge has genuinely no data for at
    all) is treated as admitting — there is no unresolved STATE to gate
    on, as distinct from a real, resolved-to-unresolved state."""
    state = ((entry.get("role_qualification") or {}).get("state"))
    return state is None or state in _QUALIFICATION_ADMITS_RECOMMENDED


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


async def build_production_and_structures(session: AsyncSession, project_id) -> dict:
    """Generic, project_id-driven replacement for GET /cineglobe/production
    + GET /cineglobe/structures, sourced from canonical_evaluation.py's
    persisted rows instead of the Little-Utopia-only in-memory get_state().
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

    rows: list[tuple] = []
    if fingerprint:
        rows = (await session.execute(
            select(ProductionStructure, StructureCalculationResult)
            .join(StructureCalculationResult, StructureCalculationResult.structure_id == ProductionStructure.id)
            .where(
                ProductionStructure.project_id == project.id,
                StructureCalculationResult.input_fingerprint == fingerprint,
                StructureCalculationResult.engine_version == engine_version,
            )
        )).all()

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
    comparable = sorted(
        (e for e in structure_entries
         if e["is_fully_priced"] and e["is_directly_comparable"] and _qualification_admits_recommended(e)),
        key=lambda e: e["npc_with_adjustments_usd"] if e["npc_with_adjustments_usd"] is not None else float("inf"),
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
        key=lambda e: e["npc_with_adjustments_usd"] if e["npc_with_adjustments_usd"] is not None else float("inf"),
    )
    unpriced = [e for e in structure_entries if not e["is_fully_priced"]]

    ranking: list[dict] = []
    for i, e in enumerate(comparable, start=1):
        e["scenario_category"] = _scenario_category(e, rank=i)
        r = _ranking_entry(e)
        r["rank"] = i
        r["scenario_category"] = e["scenario_category"]
        ranking.append(r)
    for e in review_required:
        e["scenario_category"] = _scenario_category(e, rank=None)
        r = _ranking_entry(e)
        r["scenario_category"] = e["scenario_category"]
        ranking.append(r)
    for e in unpriced:
        e["scenario_category"] = _scenario_category(e, rank=None)
        r = _ranking_entry(e)
        r["scenario_category"] = e["scenario_category"]
        ranking.append(r)

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

    production = {
        "production_id": str(project.id),
        "production_name": project.title,
        "jurisdiction_code": base_code,
        "project_id": str(project.id),
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
    review_required_count = len(review_required)

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
                "executable_jurisdictions": [e["primary_jurisdiction"] for e in structure_entries if e["primary_jurisdiction"]],
                "catalog_only_excluded": None,
                "reachable_treaty_partners": [],
                "categories": [],
                "note": None,
            },
            "discovery": {
                "metrics": {},
                "generated_structures": len(structure_entries),
                "optimized_structures": len(comparable) + len(review_required),
                "final_ranked_structures": len(comparable),
                "production_requirements": {"environments": [], "infrastructure": [], "required_capabilities": []},
                "examinations": [],
            },
            "structures": structure_entries,
            "contingency": {},
            "ranking": ranking,
            # Item A (canonical scenario-selection consistency) — see the
            # long comment above where this is computed. The single
            # authoritative structure_id every non-Globe surface (Overview,
            # Workspace, Reports) must resolve to when no producer override
            # is active. None only when no structure is fully priced yet.
            "canonical_selected_structure_id": canonical_selected_structure_id,
            "stack_combinations": {},
            "advisor_routing_decisions_input": {},
            # Restoration-phase candidate accounting, matching the earlier
            # generic Workspace's own classification (Part J/K/L/N) so both
            # UIs agree: PRICED + relocation_cost_normalized -> comparable
            # (own base jurisdiction); PRICED, not normalized -> review
            # required (a real economics figure, just not regionally
            # comparable yet); UNPRICEABLE -> authority insufficient.
            "candidate_accounting": {
                "comparable_count": comparable_count,
                "review_required_count": review_required_count,
                "unpriceable_count": len(unpriced),
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
    baseline_rows = (await session.execute(
        select(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project.id,
            StructureCalculationResult.engine_version == ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == current_fingerprint,
        )
        .order_by(StructureCalculationResult.created_at.desc())
    )).scalars().all() if current_fingerprint else []
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
                    "identifier": f"MISSING-{role_bucket.upper()}-NATIONALITY",
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
