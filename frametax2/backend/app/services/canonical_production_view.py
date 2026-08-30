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
from app.services.canonical_evaluation import ENGINE_VERSION, _QUALIFICATION_ADMITS_RECOMMENDED


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

    return {
        "structure_id": str(structure.id),
        "structure_type": structure_type,
        "label": structure.name,
        "primary_jurisdiction": code,
        "participants": [code] if code else [],
        "relationship_types": relationship_types,
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
        "component_allocations": trace.get("component_allocations") or [],
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
    fingerprint = (await session.execute(
        select(StructureCalculationResult.input_fingerprint)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project.id,
            StructureCalculationResult.engine_version == engine_version,
        )
        .limit(1)
    )).scalar_one_or_none()

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
    jurisdiction_name_by_code = {j.code: j.name for j in jurisdictions}

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

    from app.services.canonical_project_economics import build_ui_location_categories
    ui_location_categories = await build_ui_location_categories(session, project.id)

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
            "leaf_account_sum_usd": None,
            "variance_usd": None,
            "note": None,
        },
        "production_structure_default": None,
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
    baseline_rows = (await session.execute(
        select(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project.id,
            StructureCalculationResult.engine_version == ENGINE_VERSION,
        )
        .order_by(StructureCalculationResult.created_at.desc())
    )).scalars().all()
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

    budget_doc = (await session.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == project.id)
        .order_by(BudgetDocument.created_at.desc())
    )).scalars().first()
    if budget_doc is not None:
        filename = budget_doc.filename
        currency_code = budget_doc.currency_code
        if total_budget_usd is None and budget_doc.total_budget_raw is not None:
            total_budget_usd = float(budget_doc.total_budget_raw)
        line_item_count = (await session.execute(
            select(BudgetLineItem.id).where(BudgetLineItem.budget_document_id == budget_doc.id)
        )).scalars().all()
        line_item_count = len(line_item_count)

    pkg = {
        "production_id": str(project.id),
        "confidence": "unknown",
        "is_ready_for_downstream_engines": bool(register),
        "register": register,
        "budget": {
            "known": budget_doc is not None, "filename": filename, "currency_code": currency_code,
            "total_budget_usd": total_budget_usd,
            "line_item_count": line_item_count,
            "atl_total_usd": None, "btl_total_usd": None, "post_total_usd": None,
            "other_total_usd": None, "labor_usd": None, "non_labor_usd": None,
            "totals_by_spend_category_usd": {}, "opportunity_hints": [],
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

    economics = {
        "production_structure_default": None, "verified_cash_qpe_usd": None,
        "verified_floor_case": None, "potential_ceiling_case": None, "inkind_post_options": {},
        "financing_source": None, "controls": {}, "normalized_structures": [],
        "fx_horizons": {}, "jurisdiction_currency": {}, "alternative_jurisdictions": [],
        "available_funds": [], "structuring_advisory": None,
        "production_requirements_disclosed": requirements_disclosed,
    }

    return {"status": "OK", "pkg": pkg, "economics": economics, "people": people, "facts": facts}
