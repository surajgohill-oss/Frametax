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
from app.services.jurisdiction_disposition import (
    annotate_rows, blocked_totals, enrich_row_with_program_detail, rate_rule_fact_keys,
)
from app.services.music_carveout import apply_music_carveout
from app.services.incentive_potential import (
    assign_incentive_potential_ranks,
    build_incentive_potential,
)
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

# GLOBE_WORKSPACE_CANONICAL_WIRING_COMPLETE (2026-09-22): recommendation thresholds.
# CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md (audited at 88a0b96) found the
# prior pass's producer_optimizer_options was a HARD INCLUSION FILTER -- it removed
# every below-threshold and every 3+-jurisdiction structure from the served collection
# entirely, so producer_optimizer_options_total was 0 for all four real productions
# (every 2-jurisdiction candidate's real savings happened to be <=$100K in every one of
# them, and every 3+-jurisdiction candidate was excluded categorically regardless of its
# real savings -- Little Utopia alone had 66 real, priced, executable structures saving
# more than $200,000 that were made invisible this way). The controlling contract is
# explicit: "Recommendation thresholds affect priority, not visibility." These
# thresholds are therefore now used ONLY to ANNOTATE every entry of the complete,
# never-filtered `optimizer_scenarios` collection (see _annotate_optimizer_scenario
# below) -- never to drop a row from what is served.
#
# MATERIALITY_RECOMMENDATION_POLICY (2026-09-29): an explicit, internal CineGlobe
# product decision, not an incentive-program rule or a legal proposition -- a
# producer's own bar for how much a structure must save before the added
# coordination/legal complexity of an additional jurisdiction is "worth it," set
# by product ownership, not sourced from or contingent on any external authority.
# Replaces the prior flat two-tier rule ($100K for <=2 jurisdictions, a flat $200K
# for EVERY 3+-jurisdiction structure regardless of how many more there were) with
# a formula that scales per added jurisdiction:
#     additional_jurisdictions = max(0, jurisdiction_count - 1)
#     recommendation_threshold_usd = 100_000 * additional_jurisdictions
# Recommended when savings_vs_current_usd >= recommendation_threshold_usd (>=, not
# strictly >, per the policy's own definition -- exactly-at-threshold now
# qualifies, where the prior rule's strict `>` excluded it). A 1-jurisdiction
# candidate (no jurisdiction beyond the anchor's own single-jurisdiction baseline)
# has threshold $0 -- any non-negative savings recommends it, never a $100K bar for
# zero added complexity. This is a RECOMMENDATION-STATUS policy only: it never
# removes, suppresses, invalidates, or alters the economics of any structure, and
# it is applied by the SAME never-filtered annotation pass as the rule it replaces.
#
# CANONICAL OPTIMIZER RECOMMENDATION METHODOLOGY CLOSEOUT (2026-09-30), item 6:
# the raw dollar constant itself now lives in app/services/materiality_policy.py
# (a tiny, dependency-free leaf module) and is re-exported here unchanged, so
# every existing import of MATERIALITY_THRESHOLD_PER_ADDITIONAL_JURISDICTION_USD
# from this module keeps working -- structural_archetype_generator.py's own
# internal disclosure-only materiality_recommended field now imports the SAME
# constant directly from materiality_policy.py instead of a second, independent
# `100_000.0` literal that could silently drift from this one. See that module's
# own docstring for why the constant, not this module's served-view function, is
# what moved.
from app.services.materiality_policy import MATERIALITY_THRESHOLD_PER_ADDITIONAL_JURISDICTION_USD  # noqa: E402
from app.services.production_fit import (  # noqa: E402
    FIT_CONFIRMED_STATUSES, FIT_WEAK, classify_entry_fit, fit_actionability, fit_aware_category, fit_priority, fit_summary,
)


def materiality_recommendation_threshold_usd(jurisdiction_count: int | None) -> float:
    """The one canonical implementation of the materiality product policy --
    never re-derived inline, so the formula can never silently diverge between
    the annotation pass and a test/consumer that wants to reproduce it."""
    additional_jurisdictions = max(0, (jurisdiction_count or 0) - 1)
    return MATERIALITY_THRESHOLD_PER_ADDITIONAL_JURISDICTION_USD * additional_jurisdictions

REC_STATUS_RECOMMENDED = "RECOMMENDED"
REC_STATUS_EVALUATED_ALTERNATIVE = "EVALUATED_ALTERNATIVE"
REC_STATUS_NEUTRAL = "NEUTRAL"
REC_STATUS_COSTS_MORE = "COSTS_MORE"
REC_STATUS_BASELINE_UNRESOLVED = "BASELINE_UNRESOLVED"


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


def _best_entry_by_participant_set(entries: list[dict]) -> dict[frozenset, dict]:
    """Index the lowest-adjusted-NPC PRICED entry for every distinct participant set
    seen in `entries` (the same never-filtered optimizer_scenarios rows). Keyed by
    frozenset(participants), so it is invariant to participant order or how the caller
    iterated the set -- two entries naming the same jurisdictions in a different order
    or discovered via a different search path resolve to the same index slot. Used as
    the "best valid parent structure with jurisdiction X removed" lookup for marginal
    per-jurisdiction materiality: comparing an entry against the cheapest sibling that
    covers exactly one fewer jurisdiction, never against an arbitrary or costlier one."""
    best: dict[frozenset, dict] = {}
    for e in entries:
        npc = e.get("npc_with_adjustments_usd")
        if npc is None:
            continue
        key = frozenset(e.get("participants") or [])
        if not key:
            continue
        current = best.get(key)
        if current is None or npc < current["npc_with_adjustments_usd"]:
            best[key] = e
    return best


def _qualification_rank(entry: dict) -> int:
    """Coarse qualification strength ranking for dominance comparison (item 4's
    "equal or stronger qualification status"): 2 = admits RECOMMENDED (QUALIFIES /
    NOT_APPLICABLE), 1 = admits pricing only (a real, disclosed, still-unresolved gap
    -- CURABLE_GAP/USER_FACT_REQUIRED/SCRIPT_FACT_REQUIRED/AUTHORITY_UNRESOLVED/
    RULE_DATA_INCOMPLETE), 0 = anything else (hard-fail or absent). Reuses the SAME
    two canonical sets canonical_evaluation.py already defines and this module
    already imports -- never a third, independently-defined qualification hierarchy."""
    state = (entry.get("role_qualification") or {}).get("state")
    if state in _QUALIFICATION_ADMITS_RECOMMENDED:
        return 2
    if state in _QUALIFICATION_ADMITS_PRICING:
        return 1
    return 0


def _compute_dominance(universe: list[dict]) -> dict[str, dict]:
    """MATERIALITY_RECOMMENDATION_POLICY item 4 (strict economic dominance): a
    candidate cannot be Recommended when an executable, LOWER-COMPLEXITY structure
    (a strict subset of its jurisdictions/components -- never an equal or larger
    set, and never a structure that merely happens to be cheaper via an unrelated
    route) achieves an equal-or-lower final adjusted NPC, with equal-or-stronger
    qualification and no greater unresolved implementation risk. Computed ONCE over
    the full priced universe (never limited to optimizer-family candidates -- a
    plain single-jurisdiction full-relocation structure is a valid, and often the
    MOST common, real dominator of a needlessly complex hybrid that adds no genuine
    economic benefit over it) so a dominator never needs to itself be an "optimizer
    scenario" to count. A dominated candidate is never removed or hidden -- see the
    caller, which only ever downgrades its RECOMMENDED eligibility, matching item 8's
    "Dominated candidates remain visible as Evaluated Alternatives.\""""
    candidates = [
        e for e in universe
        if e.get("candidate_status") == "PRICED" and e.get("is_fully_priced")
        and e.get("npc_with_adjustments_usd") is not None and e.get("participants")
    ]
    result: dict[str, dict] = {}
    for x in candidates:
        x_participants = frozenset(x["participants"])
        x_npc = x["npc_with_adjustments_usd"]
        x_qual = _qualification_rank(x)
        x_risk = bool(x.get("administrative_allocation_risk"))
        best_dominator = None
        for y in candidates:
            if y["structure_id"] == x["structure_id"]:
                continue
            y_participants = frozenset(y["participants"])
            if not (y_participants < x_participants):  # strict subset only
                continue
            if y["npc_with_adjustments_usd"] > x_npc:
                continue
            if _qualification_rank(y) < x_qual:
                continue
            if bool(y.get("administrative_allocation_risk")) and not x_risk:
                continue
            if best_dominator is None or y["npc_with_adjustments_usd"] < best_dominator["npc_with_adjustments_usd"]:
                best_dominator = y
        if best_dominator is not None:
            result[x["structure_id"]] = {
                "dominance_status": "DOMINATED",
                "dominated_by_structure_id": best_dominator["structure_id"],
                "dominated_by_economic_identity": best_dominator.get("economic_identity"),
                "npc_difference_usd": round(x_npc - best_dominator["npc_with_adjustments_usd"], 2),
                "dominance_reason": (
                    "A lower-complexity executable structure "
                    f"({best_dominator.get('label') or best_dominator['structure_id']}) achieves an "
                    "equal-or-lower net production cost with equal-or-stronger qualification and no "
                    "greater unresolved implementation risk."
                ),
            }
        else:
            result[x["structure_id"]] = {
                "dominance_status": "NOT_DOMINATED",
                "dominated_by_structure_id": None,
                "dominated_by_economic_identity": None,
                "npc_difference_usd": None,
                "dominance_reason": None,
            }
    return result


def _marginal_jurisdiction_materiality(
    entry: dict, participant_set_index: dict[frozenset, dict],
) -> tuple[bool, str | None]:
    """MATERIALITY_RECOMMENDATION_POLICY item 6: every jurisdiction added beyond a
    single-jurisdiction structure must independently clear
    MATERIALITY_THRESHOLD_PER_ADDITIONAL_JURISDICTION_USD versus the best valid parent
    structure with THAT jurisdiction removed -- never the aggregate savings-vs-baseline
    check alone, which lets one jurisdiction's large savings subsidize another
    jurisdiction's immaterial addition (the LU/FVD Manitoba-relocation-subsidizing-
    music/VFX pattern this policy item exists to close). A single-jurisdiction entry
    (nothing to remove) always passes -- there is no added jurisdiction to test.
    Returns (passes, failure_reason); failure_reason is None when passes is True.

    CANONICAL OPTIMIZER RECOMMENDATION METHODOLOGY CLOSEOUT (2026-09-30), item 2
    completion: this now checks EVERY non-principal jurisdiction in the entry's own
    participant set, for any jurisdiction count (the prior pass's SCOPE NOTE
    restricting this to exactly 2 jurisdictions -- see 4925a72 -- is resolved, not
    just relaxed). Two sources, checked in order per jurisdiction:

    1. `entry["marginal_jurisdiction_benefits_usd"]` -- the real, canonically-
       repriced marginal benefit canonical_evaluation.py's counterfactual reprice
       computes ONCE at generation time for every non-principal component actually
       in an `ordinary_component_hybrid` candidate (removes that one component,
       returns its real AccountAllocation lines to the principal component, reprices
       through the SAME generate_structural_candidate + _hybrid_structure_
       normalization the candidate itself was priced with). This is the primary,
       always-correct source whenever present, for 2- AND 3+-jurisdiction hybrids
       alike -- it never depends on some OTHER candidate having been independently
       generated and priced.
    2. `participant_set_index` sibling lookup (the prior pass's only mechanism) --
       used ONLY as a fallback for jurisdictions the pre-computed dict does not
       cover (a structure family that does not yet compute it, e.g. co-production/
       stack, or a row persisted before this enrichment existed).

    FAILS CLOSED: if neither source has a real answer for one of this entry's
    jurisdictions, that jurisdiction's marginal benefit is UNVERIFIABLE and the
    candidate cannot be certified materially independent -- this never silently
    defaults to "passes"."""
    participants = frozenset(entry.get("participants") or [])
    if len(participants) <= 1:
        return True, None
    candidate_npc = entry.get("npc_with_adjustments_usd")
    if candidate_npc is None:
        return False, "MISSING_CANDIDATE_NPC_FOR_MARGINAL_CHECK"
    precomputed = entry.get("marginal_jurisdiction_benefits_usd")
    proven_bounds = entry.get("marginal_jurisdiction_bounds_usd") or {}
    primary_jurisdiction = entry.get("primary_jurisdiction")
    for jurisdiction in sorted(participants):
        if jurisdiction == primary_jurisdiction:
            continue
        if precomputed is not None and jurisdiction in precomputed:
            marginal_improvement = precomputed[jurisdiction]
            if marginal_improvement is None:
                return False, f"JURISDICTION_{jurisdiction}_MARGINAL_BENEFIT_UNCOMPUTED"
            if marginal_improvement < MATERIALITY_THRESHOLD_PER_ADDITIONAL_JURISDICTION_USD:
                return False, f"JURISDICTION_{jurisdiction}_MARGINAL_BENEFIT_BELOW_THRESHOLD"
            continue
        bound = proven_bounds.get(jurisdiction)
        if bound is not None:
            # An UPPER BOUND, not an exact benefit: the engine proved this jurisdiction's marginal
            # benefit cannot exceed `bound`. Only a bound below the hurdle is usable (it proves the
            # shortfall); a bound at/above the hurdle proves nothing and falls through to the
            # sibling lookup / fail-closed path below.
            if bound < MATERIALITY_THRESHOLD_PER_ADDITIONAL_JURISDICTION_USD:
                return False, f"JURISDICTION_{jurisdiction}_MARGINAL_BENEFIT_BELOW_THRESHOLD_PROVEN_UPPER_BOUND"
        parent_participants = participants - {jurisdiction}
        parent = participant_set_index.get(parent_participants) if parent_participants else None
        if parent is None:
            return False, f"NO_PRICED_PARENT_WITHOUT_{jurisdiction}"
        parent_npc = parent.get("npc_with_adjustments_usd")
        if parent_npc is None:
            return False, f"PARENT_WITHOUT_{jurisdiction}_MISSING_NPC"
        marginal_improvement = float(parent_npc) - float(candidate_npc)
        if marginal_improvement < MATERIALITY_THRESHOLD_PER_ADDITIONAL_JURISDICTION_USD:
            return False, f"JURISDICTION_{jurisdiction}_MARGINAL_BENEFIT_BELOW_THRESHOLD"
    return True, None


def _annotate_optimizer_scenario(
    entry: dict, baseline_npc: float | None, participant_set_index: dict[frozenset, dict] | None = None,
    dominance_by_id: dict[str, dict] | None = None,
) -> dict:
    """Annotate ONE already-canonical, already-executable `optimizer_scenarios` entry
    with its recommendation status -- never a filter, never a second identity, never a
    second dedup pass (optimizer_scenarios is already one row per economic_identity).
    jurisdiction_count reuses the same `participant_count` `_practicality_tier` already
    computes (confirmed empirically identical to a component-allocations-derived count
    across all 1,390 real optimizer_scenarios entries in the acceptance database --
    CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md), so this never introduces a
    second, potentially-disagreeing jurisdiction-count definition.

    A candidate reaches RECOMMENDED only when the aggregate savings-vs-baseline
    threshold (this function's original check), the marginal per-added-jurisdiction
    threshold (_marginal_jurisdiction_materiality, item 6), AND strict economic
    non-dominance (_compute_dominance, item 4) are ALL satisfied -- the aggregate
    check alone cannot recommend a structure whose individual jurisdictions are not
    each independently worth their own complexity, or that a genuinely simpler
    executable structure already beats outright."""
    jurisdiction_count = entry.get("participant_count") or len(set(entry.get("participants") or []))
    threshold = materiality_recommendation_threshold_usd(jurisdiction_count)
    candidate_npc = entry.get("npc_with_adjustments_usd")
    savings = (
        float(baseline_npc) - float(candidate_npc)
        if baseline_npc is not None and candidate_npc is not None else None
    )
    if savings is None:
        status, reason = REC_STATUS_BASELINE_UNRESOLVED, "MISSING_BASELINE_OR_CANDIDATE_NPC"
    elif savings >= threshold:
        # CANONICAL OPTIMIZER RECOMMENDATION METHODOLOGY CLOSEOUT (2026-09-30), item 2
        # completion: marginal-per-jurisdiction enforcement now applies at every
        # jurisdiction count. The prior pass (4925a72) scoped this to exactly 2
        # jurisdictions because its only mechanism (a sibling-candidate lookup) almost
        # never found a priced parent for a 3+-jurisdiction candidate's (n-1)-
        # jurisdiction subset. _marginal_jurisdiction_materiality now reads a real,
        # per-candidate, canonically-repriced marginal benefit computed once at
        # generation time (see canonical_evaluation.py's counterfactual reprice),
        # falling back to the sibling lookup only where that data is absent -- so this
        # is no longer scoped by jurisdiction count.
        marginal_ok, marginal_reason = _marginal_jurisdiction_materiality(entry, participant_set_index or {})
        _dominance = (dominance_by_id or {}).get(entry.get("structure_id"))
        _is_dominated = bool(_dominance) and _dominance.get("dominance_status") == "DOMINATED"
        if marginal_ok and not _is_dominated:
            status, reason = REC_STATUS_RECOMMENDED, "SAVINGS_MEETS_OR_EXCEEDS_THRESHOLD"
        elif not marginal_ok:
            status, reason = REC_STATUS_EVALUATED_ALTERNATIVE, marginal_reason
        else:
            status, reason = REC_STATUS_EVALUATED_ALTERNATIVE, "DOMINATED_BY_LOWER_COMPLEXITY_STRUCTURE"
    elif savings < 0:
        status, reason = REC_STATUS_COSTS_MORE, "NEGATIVE_SAVINGS"
    elif savings == 0:
        status, reason = REC_STATUS_NEUTRAL, "ZERO_SAVINGS"
    else:
        status, reason = REC_STATUS_EVALUATED_ALTERNATIVE, "SAVINGS_BELOW_THRESHOLD"
    # PRODUCTION-FIT GATE (2026-10-01): a candidate that passes every economic /
    # qualification / materiality / dominance test is Leading/Strong ONLY when its
    # physical-production fit is confirmed (STRONG/WORKABLE). WEAK or UNKNOWN fit keeps the
    # candidate visible with its real economics as an evaluated alternative -- never deleted,
    # never promoted by lowest NPC alone. The pre-gate canonical decision stays served
    # (canonical_recommendation_status/_reason) so the financial verdict remains auditable.
    # Entries not yet fit-classified (no production_fit_status key) are left untouched.
    canonical_status, canonical_reason = status, reason
    if status == REC_STATUS_RECOMMENDED and "production_fit_status" in entry \
            and entry["production_fit_status"] not in FIT_CONFIRMED_STATUSES:
        status = REC_STATUS_EVALUATED_ALTERNATIVE
        reason = (
            "LOCATION_FIT_WEAK" if entry["production_fit_status"] == FIT_WEAK else "LOCATION_FIT_UNCONFIRMED"
        )
    _dominance_fields = (dominance_by_id or {}).get(entry.get("structure_id")) or {
        "dominance_status": None, "dominated_by_structure_id": None,
        "dominated_by_economic_identity": None, "npc_difference_usd": None, "dominance_reason": None,
    }
    return {
        **entry,
        "jurisdiction_count": jurisdiction_count,
        "savings_vs_current_usd": savings,
        "recommendation_threshold_usd": threshold,
        "is_recommended": status == REC_STATUS_RECOMMENDED,
        "recommendation_status": status,
        "recommendation_reason": reason,
        "canonical_recommendation_status": canonical_status,
        "canonical_recommendation_reason": canonical_reason,
        **_dominance_fields,
    }

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


def _aggregate_segment_incentive_floor_ceiling(trace: dict) -> tuple[float | None, float | None, bool]:
    """LU Mauritius economics reconciliation: canonical_evaluation.py
    already prices and persists genuinely distinct per-segment
    incentive_floor_usd/incentive_ceiling_usd (and
    ceiling_requires_confirmation) inside calculation_trace_json["segments"]
    (allocation_pricing.py's SegmentEconomics) — but nothing previously
    aggregated them to a structure-level total, so the served
    total_incentive_floor_usd/total_incentive_ceiling_usd fields silently
    repeated selected_incentive_usd for both, collapsing a real, materially
    different modeled ceiling (e.g. Mauritius's discretionary "up to 40%"
    band) into the confirmed/selected floor. Sums the REAL per-segment
    values the pricing kernel already computed — never a new derivation.
    Returns (None, None, False) for any row persisted before this
    per-segment enrichment existed (graceful degradation, same established
    pattern as selected_incentive_usd above)."""
    segments = trace.get("segments") or []
    if not segments:
        return None, None, False
    floor_total = 0.0
    ceiling_total = 0.0
    any_requires_confirmation = False
    saw_any_value = False
    for seg in segments:
        f = seg.get("incentive_floor_usd")
        c = seg.get("incentive_ceiling_usd")
        if f is not None:
            floor_total += float(f)
            saw_any_value = True
        if c is not None:
            ceiling_total += float(c)
            saw_any_value = True
        if seg.get("ceiling_requires_confirmation"):
            any_requires_confirmation = True
    if not saw_any_value:
        return None, None, False
    return round(floor_total, 2), round(ceiling_total, 2), any_requires_confirmation


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

    _seg_floor, _seg_ceiling, _ceiling_requires_confirmation = _aggregate_segment_incentive_floor_ceiling(trace)

    entry = {
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
        # Multi-program QPE reconciliation: canonical_evaluation.py's
        # multi_program stack path already computes both the sum of each
        # stacked program's own reusable claim base (total_claim_bases_usd
        # -- e.g. Ontario OPSTC + OCASE both claiming against the SAME
        # underlying QPE, legitimately double-counted for per-program
        # disclosure) and the TRUE exact union of qualifying line IDs
        # (total_qualifying_spend_usd -- overlapping lines counted once).
        # Neither was ever served before this fix, so every consumer
        # (Overview/Workspace/Globe/Inspector/hero) fell back to summing
        # segments[].qpe_usd -- which equals total_claim_bases_usd, the
        # WRONG, doubled figure, for any structure whose stacked programs
        # share a spend base. "qpe_usd" is the one authoritative field
        # every consumer should read: the real total_qualifying_spend_usd
        # when this structure is a reconciled multi-program stack, else
        # the segment/component-allocation sum (correct by construction
        # for every other structure type, where segments route to
        # disjoint jurisdictions and never overlap).
        "total_claim_bases_usd": trace.get("total_claim_bases_usd"),
        "total_qualifying_spend_usd": trace.get("total_qualifying_spend_usd"),
        "qpe_usd": (
            trace.get("total_qualifying_spend_usd")
            if trace.get("total_qualifying_spend_usd") is not None
            else sum((seg.get("qpe_usd") or 0.0) for seg in (trace.get("segments") or []))
            if trace.get("segments")
            else sum((ca.get("allocated_usd") or 0.0) for ca in (trace.get("component_allocations") or []))
        ),
        # LU Mauritius economics reconciliation: floor and ceiling are the
        # REAL, distinct per-segment values aggregated above — never
        # collapsed to selected_incentive_usd. Falls back to
        # selected_incentive_usd only for rows persisted before segment-
        # level floor/ceiling existed (graceful degradation).
        "total_incentive_floor_usd": _seg_floor if _seg_floor is not None else selected_incentive_usd,
        "total_incentive_ceiling_usd": _seg_ceiling if _seg_ceiling is not None else selected_incentive_usd,
        "selected_incentive_usd": selected_incentive_usd,
        "ceiling_requires_confirmation": _ceiling_requires_confirmation,
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
        # CANONICAL OPTIMIZER RECOMMENDATION METHODOLOGY CLOSEOUT (2026-09-30),
        # item 2 completion: the real, canonically-repriced marginal benefit of
        # each non-principal jurisdiction in a hybrid, computed once at
        # generation time (canonical_evaluation.py's counterfactual reprice) --
        # never re-derived or re-estimated here. Absent (None, not {}) for any
        # structure family that does not yet compute it (single-jurisdiction,
        # co-production, stack, or a row persisted before this enrichment) --
        # _marginal_jurisdiction_materiality's own fallback distinguishes "no
        # data yet" from "empty dict, no non-principal jurisdictions to check".
        "marginal_jurisdiction_benefits_usd": trace.get("marginal_jurisdiction_benefits_usd"),
        "marginal_jurisdiction_bounds_usd": trace.get("marginal_jurisdiction_bounds_usd"),
        # MUSIC CARVE-OUT: the evaluator's repriced Music-bundled counterfactual (hybrids only).
        "music_carveout": trace.get("music_carveout"),
        "npc_verified_usd": float(result.true_net_cost_usd) if result.true_net_cost_usd is not None else None,
        "npc_with_adjustments_usd": (
            float(result.risk_adjusted_net_cost_usd) if result.risk_adjusted_net_cost_usd is not None else None
        ),
        "npc_conservative_usd": float(result.true_net_cost_usd) if result.true_net_cost_usd is not None else None,
        # LU Mauritius economics reconciliation: the counterfactual NPC at
        # the floor rate and at the (unconfirmed) ceiling rate. Adjustments
        # (travel/fx/local-cost/financing/implementation deltas already
        # baked into npc_with_adjustments_usd) are structural, not
        # incentive-rate dependent, so swapping only the incentive
        # component reconstructs each counterfactual without re-deriving
        # anything the pricing kernel didn't already compute:
        #   NPC_x = npc_with_adjustments_usd + selected_incentive_usd - incentive_x
        # None when the segment-level floor/ceiling aggregate above is
        # unavailable (pre-enrichment rows) or NPC itself is unpriced.
        "npc_floor_usd": (
            round(float(result.risk_adjusted_net_cost_usd) + selected_incentive_usd - _seg_floor, 2)
            if (result.risk_adjusted_net_cost_usd is not None and selected_incentive_usd is not None and _seg_floor is not None)
            else None
        ),
        "npc_ceiling_usd": (
            round(float(result.risk_adjusted_net_cost_usd) + selected_incentive_usd - _seg_ceiling, 2)
            if (result.risk_adjusted_net_cost_usd is not None and selected_incentive_usd is not None and _seg_ceiling is not None)
            else None
        ),
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
    # MAXIMUM-POTENTIAL INCENTIVE CONTRACT (2026-10-01): the single served definition of
    # confirmed vs. maximum-supportable economics (services/incentive_potential.py). Read
    # from the same persisted per-segment/per-component pricing values as everything above
    # -- never a second calculator; every consumer renders these fields verbatim.
    entry.update(build_incentive_potential(
        trace,
        is_priced=is_priced,
        selected_incentive_usd=selected_incentive_usd,
        npc_with_adjustments_usd=(
            float(result.risk_adjusted_net_cost_usd) if result.risk_adjusted_net_cost_usd is not None else None
        ),
        legal_review_required=bool(trace.get("legal_review_required", False)),
        administrative_allocation_risk=bool(trace.get("administrative_allocation_risk")),
    ))
    return entry


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
        "production_fit_status": entry.get("production_fit_status"),
        "production_fit_reasons": entry.get("production_fit_reasons") or [],
        "production_fit_legs": entry.get("production_fit_legs") or [],
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
    _blocked = {"disposition": {"HARD_BLOCK": 0, "NEEDS_FACTS": 0}, "causes": {}, "exact": True, "rows": 0}
    jurisdiction_accounting = None
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
            # SHARED JURISDICTION DISPOSITION: every served row carries the one HARD_BLOCK /
            # NEEDS_FACTS classification (services/jurisdiction_disposition.py).
            annotate_rows(rejection_first_page.get("results") or [])
            # EXACT PROGRAM BLOCKER: join each blocked row to its program (read from the retained trace) and the
            # project's stored facts, then serve the exact unresolved propositions (registry-derived; no new rules).
            _blk_rows = [r for r in (rejection_first_page.get("results") or [])
                         if r.get("candidate_status") not in ("CO_PRO_OPPORTUNITY", "DOMINATED_WITH_PROOF", "RULE_REJECTED")]
            if _blk_rows:
                _ids = [r["structure_id"] for r in _blk_rows]
                _slug_rows = (await session.execute(
                    select(StructureCalculationResult.structure_id,
                           StructureCalculationResult.calculation_trace_json["program_slug"].astext)
                    .where(StructureCalculationResult.structure_id.in_(_ids),
                           StructureCalculationResult.input_fingerprint == fingerprint,
                           StructureCalculationResult.engine_version == engine_version)
                )).all()
                _slug_by_id = {str(i): sl for i, sl in _slug_rows}
                _keys: set[str] = set()
                for _sl in set(_slug_by_id.values()):
                    _keys |= rate_rule_fact_keys(_sl)
                    if _sl:
                        _keys.add(f"evidenced_program_fact:{_sl}__discretionary_award_confirmed")
                _facts = {}
                if _keys:
                    _facts = {
                        k: v for k, v in (await session.execute(
                            select(ProjectFact.fact_key, ProjectFact.value)
                            .where(ProjectFact.project_id == project.id, ProjectFact.fact_key.in_(_keys))
                        )).all()
                    }
                from app.services.canonical_project_economics import _FORMAT_TO_PRODUCTION_TYPE
                _ptype = _FORMAT_TO_PRODUCTION_TYPE.get((project.format or "").lower(), "feature_film")
                for _r in _blk_rows:
                    enrich_row_with_program_detail(_r, _slug_by_id.get(_r["structure_id"]), _facts, _ptype)
            _blocked = blocked_totals(rejection_first_page.get("results") or [], generation_totals["by_reason"])
            # JURISDICTION ACCOUNTING: the complete first-exit ledger. Programs that were examined but only exist in
            # aggregate groups (or were never persisted) are served as accounted rows -- so no jurisdiction vanishes
            # before the Globe. Retained blocked rows above are NOT duplicated.
            try:
                from app.services.canonical_project_economics import _FORMAT_TO_PRODUCTION_TYPE as _F2P
                from app.services.jurisdiction_accounting import build_jurisdiction_accounting
                _ptype2 = _F2P.get((project.format or "").lower(), "feature_film")
                jurisdiction_accounting = await build_jurisdiction_accounting(
                    session, project, fingerprint, engine_version or ENGINE_VERSION, production_type=_ptype2,
                    served_blocked_rows=[r for r in (rejection_first_page.get("results") or [])
                                         if r.get("candidate_status") not in ("CO_PRO_OPPORTUNITY", "DOMINATED_WITH_PROOF")],
                )
            except Exception:  # noqa: BLE001 - the ledger is additive; a failure must never break the served view
                import logging as _lg
                _lg.getLogger(__name__).exception("jurisdiction accounting failed for %s", project.id)
                jurisdiction_accounting = None
            if jurisdiction_accounting:
                _extra = jurisdiction_accounting["rows"]
                rejection_first_page["results"] = list(rejection_first_page.get("results") or []) + _extra
                rejection_first_page["returned"] = len(rejection_first_page["results"])
                rejection_first_page["accounting_rows"] = len(_extra)
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
    # PRODUCTION-FIT (2026-10-01): classify every served entry ONCE, from the project's own
    # effective physical requirements (script-derived + producer location overrides), through
    # the canonical capability classifier. Served fields only; React renders them verbatim.
    from app.calculators.production_requirements import derive_production_requirements
    from app.services.canonical_project_economics import build_physical_requirements
    _fit_requirements = derive_production_requirements(await build_physical_requirements(session, project.id))
    _fit_cache: dict = {}
    for _fe in structure_entries:
        _fe.update(classify_entry_fit(_fe, _fit_requirements, _fit_cache))

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
        r["fit_priority"] = fit_priority(e)
        r["fit_aware_category"] = fit_aware_category(e)
        r["recommendation_category"] = REC_VERIFIED_RECOMMENDATION
        ranking.append(r)
    for e in review_required:
        e["scenario_category"] = _scenario_category(e, rank=None)
        r = _ranking_entry(e)
        r["scenario_category"] = e["scenario_category"]
        r["fit_priority"] = fit_priority(e)
        r["fit_aware_category"] = fit_aware_category(e)
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
        r["fit_priority"] = fit_priority(e)
        r["fit_aware_category"] = fit_aware_category(e)
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

    # GLOBE_WORKSPACE_CANONICAL_WIRING_COMPLETE (2026-09-22): restores the complete,
    # never-filtered optimizer_scenarios contract the audit specified. `optimizer_scenarios`
    # itself is REASSIGNED here to the same rows, same order, same count -- every entry
    # gains a recommendation annotation, none is dropped. `_baseline_entry` (the
    # canonical Current Location/anchor) is resolved once; if it cannot be resolved,
    # every entry fails closed into BASELINE_UNRESOLVED (never a fabricated savings
    # figure) rather than the collection disappearing.
    _baseline_entry = next((e for e in structure_entries if e.get("is_baseline")), None)
    _baseline_npc = (_baseline_entry or {}).get("npc_with_adjustments_usd")
    # Indexed over the FULL priced universe (_priced_entries), never just optimizer_scenarios
    # alone: a hybrid's "remove one jurisdiction" parent is very often a plain single-
    # jurisdiction full-relocation structure (e.g. LU/FVD/BH/LLS's own "Manitoba-only"
    # evidence structures), and SINGLE_JURISDICTION is deliberately excluded from
    # _OPTIMIZER_STRUCTURE_FAMILIES/optimizer_scenarios -- indexing optimizer_scenarios alone
    # would make almost every real marginal-jurisdiction lookup fail closed with no priced
    # parent found, even though the real, priced, comparable parent exists right there in
    # structure_entries. _priced_entries already covers every fully-priced candidate
    # (single-jurisdiction, hybrid, stack, co-production) regardless of optimizer-family
    # membership, so it is the correct and complete source for this lookup.
    _participant_set_index = _best_entry_by_participant_set(_priced_entries)
    # Item 4 (strict economic dominance): computed once over the SAME full priced
    # universe -- a dominator does not need to be an optimizer-family candidate
    # itself (a plain single-jurisdiction full relocation routinely dominates a
    # needlessly complex hybrid that adds no genuine economic benefit over it).
    _dominance_by_id = _compute_dominance(_priced_entries)
    optimizer_scenarios = [
        _annotate_optimizer_scenario(e, _baseline_npc, _participant_set_index, _dominance_by_id)
        for e in optimizer_scenarios
    ]
    # MUSIC CARVE-OUT: curated-surface projection (services/music_carveout.py). Every split is still
    # generated/priced/persisted; below-threshold splits move to optimizer_scenarios_music_suppressed
    # (full entries, preserved) and the totals reconcile.
    optimizer_scenarios, music_suppressed_scenarios, music_carveout_summary = apply_music_carveout(
        optimizer_scenarios, float(_baseline_npc) if _baseline_npc is not None else None,
    )
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
    producer_optimizer_baseline_npc_usd = float(_baseline_npc) if _baseline_npc is not None else None
    # FIT-AWARE PRESENTATION ORDER (2026-10-01), served explicitly and separately from the
    # canonical financial rank: (1) qualified, materially useful, fit-confirmed alternatives;
    # (2) other fit-confirmed references; (3) fit-unconfirmed; (4) weak-fit references.
    # Within a priority the established tier -> NPC order is preserved (stable sort); no
    # scenario is removed, and `rank` / NPC fields are untouched.
    for _se in optimizer_scenarios:
        _se["fit_priority"] = fit_priority(_se)
        _se["fit_aware_category"] = fit_aware_category(_se)
        _se.update(fit_actionability(_se))
    optimizer_scenarios.sort(key=lambda _se: _se["fit_priority"])
    for _i, _se in enumerate(optimizer_scenarios, start=1):
        _se["fit_aware_rank"] = _i
    # Two independent orderings over the same never-filtered list (confirmed financial vs.
    # maximum-potential opportunity); neither reorders or removes anything.
    assign_incentive_potential_ranks(optimizer_scenarios)

    recommended_optimizer_options = [e for e in optimizer_scenarios if e["recommendation_status"] == REC_STATUS_RECOMMENDED]
    evaluated_optimizer_alternatives = [e for e in optimizer_scenarios if e["recommendation_status"] != REC_STATUS_RECOMMENDED]
    # Unresolved co-production/multilateral opportunities (candidate_status ==
    # CO_PRO_OPPORTUNITY, classification == CONDITIONAL_USER_FACT_REQUIRED -- confirmed
    # the SAME rows: structural_classification.classify_structure() maps
    # candidate_status == "CO_PRO_OPPORTUNITY" directly to CLASS_CONDITIONAL_USER_FACT_REQUIRED,
    # before any structure_type check -- CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md
    # Phase 1A). These are never priced/executable and never enter optimizer_scenarios
    # (which is already scoped to PRICED candidates only) -- served as a separate,
    # clearly-labeled, non-executable collection so a real, disclosed "needs a real
    # ownership-split fact" opportunity is visible without ever being presented as a
    # leading/executable structure.
    optimizer_opportunities_requiring_facts = [
        e for e in structure_entries if e.get("classification") == "CONDITIONAL_USER_FACT_REQUIRED"
    ]

    producer_optimizer_options = recommended_optimizer_options  # backward-compatible alias; not the sole read surface
    producer_optimizer_options_total = len(recommended_optimizer_options)
    producer_optimizer_options_by_type = {
        TIER_PRACTICAL: sum(1 for e in recommended_optimizer_options if e["practicality_tier"] == TIER_PRACTICAL),
        TIER_FORMAL: sum(1 for e in recommended_optimizer_options if e["practicality_tier"] == TIER_FORMAL),
        TIER_ADVANCED: sum(1 for e in recommended_optimizer_options if e["practicality_tier"] == TIER_ADVANCED),
    }
    optimizer_executable_total = optimizer_scenarios_total
    optimizer_recommended_total = len(recommended_optimizer_options)
    optimizer_evaluated_alternatives_total = len(evaluated_optimizer_alternatives)
    optimizer_opportunities_requiring_facts_total = len(optimizer_opportunities_requiring_facts)
    _fit_counts = fit_summary(
        optimizer_scenarios,
        unavailable_total=(generation_totals["total"] if fingerprint and generation_total_rows else len(unpriced)),
    )
    optimizer_recommendation_status_counts = {
        REC_STATUS_RECOMMENDED: optimizer_recommended_total,
        REC_STATUS_EVALUATED_ALTERNATIVE: sum(1 for e in optimizer_scenarios if e["recommendation_status"] == REC_STATUS_EVALUATED_ALTERNATIVE),
        REC_STATUS_NEUTRAL: sum(1 for e in optimizer_scenarios if e["recommendation_status"] == REC_STATUS_NEUTRAL),
        REC_STATUS_COSTS_MORE: sum(1 for e in optimizer_scenarios if e["recommendation_status"] == REC_STATUS_COSTS_MORE),
        REC_STATUS_BASELINE_UNRESOLVED: sum(1 for e in optimizer_scenarios if e["recommendation_status"] == REC_STATUS_BASELINE_UNRESOLVED),
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
                "by_jurisdiction_disposition": _blocked["disposition"],
                "by_blocked_cause": _blocked["causes"],
                "by_reconciliation_class": _blocked.get("reconciliation", {}),
                "blocked_totals_exact": _blocked["exact"],
                "first_page": rejection_first_page,
                "results_route": UNPRICEABLE_RESULTS_ROUTE.format(project_id=project.id),
                "aggregates": candidate_aggregates_block(project.id, generation_totals, aggregate_groups_first_page)
                if generation_total_rows else None,
            } if fingerprint else None,
            "jurisdiction_accounting": (
                {k: jurisdiction_accounting[k] for k in ("engine_version", "production_type", "home_jurisdiction",
                                                         "gross_budget_usd", "programs", "jurisdictions", "waterfall")}
                | {"best_per_jurisdiction_count": len(best_per_jurisdiction),
                   "executable_matches_best_per_jurisdiction": (
                       {j["jurisdiction_code"] for j in jurisdiction_accounting["jurisdictions"] if j["disposition"] == "EXECUTABLE"}
                       == set(best_per_jurisdiction.keys())),
                   "representation_note": (
                       "best_per_jurisdiction shows ONE representative structure per executable jurisdiction (its "
                       "highest-priority priced structure); every other associated structure stays available "
                       "(hover / click to cycle). The other jurisdictions are accounted by their first-exit disposition."),
                   "content_gate_inventory": __import__("app.services.program_content_gates", fromlist=["x"]).content_gate_inventory()}
            ) if jurisdiction_accounting else None,
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
            # PRODUCER_OPTIMIZER_SCENARIO_CANONICALIZATION (2026-09-21): the ONE canonical,
            # COMPLETE, NEVER THRESHOLD-FILTERED producer-facing projection every UI surface
            # must read from -- see the comment above `_scenario_topology_key`'s construction
            # for the full grouping contract. Every entry carries a recommendation
            # annotation (jurisdiction_count/savings_vs_current_usd/recommendation_threshold_usd/
            # is_recommended/recommendation_status/recommendation_reason -- see
            # _annotate_optimizer_scenario) but NONE is ever dropped from this array:
            # GLOBE_WORKSPACE_CANONICAL_WIRING_COMPLETE (2026-09-22) restores this after
            # CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md found the prior pass's
            # producer_optimizer_options had become the sole thing the frontend read, and
            # was empty for all four real productions.
            "optimizer_scenarios": optimizer_scenarios,
            "optimizer_scenarios_total": optimizer_scenarios_total,
            "optimizer_scenarios_music_suppressed": music_suppressed_scenarios,
            "music_carveout": music_carveout_summary,
            "optimizer_scenarios_by_family": optimizer_scenarios_by_family,
            # PRODUCER_OPTIMIZER_PRESENTATION_CORRECTION (2026-09-22): counts for the
            # truthful "N distinct optimized scenarios / P practical / F formal
            # co-productions / A advanced" disclosure every optimizer-consuming surface
            # must show instead of the raw iteration count.
            "optimizer_scenarios_by_tier": optimizer_scenarios_by_tier,
            # Recommended (threshold-passing) subset of the SAME complete optimizer_scenarios
            # collection above -- a priority annotation split out for convenience, never a
            # narrower served universe. 2-jurisdiction: savings > $100,000. 3+-jurisdiction:
            # savings > $200,000 (controlling product contract, ordering policy).
            "recommended_optimizer_options": recommended_optimizer_options,
            "recommended_optimizer_options_total": optimizer_recommended_total,
            # Every other executable (PRICED) optimizer_scenarios entry: positive
            # below-threshold savings (EVALUATED_ALTERNATIVE), zero savings (NEUTRAL),
            # negative savings (COSTS_MORE), or an unresolved baseline (BASELINE_UNRESOLVED).
            # Real, visible, never hidden -- "Recommendation thresholds affect priority, not
            # visibility."
            "evaluated_optimizer_alternatives": evaluated_optimizer_alternatives,
            "evaluated_optimizer_alternatives_total": optimizer_evaluated_alternatives_total,
            # Real, disclosed co-production/multilateral opportunities a registered treaty
            # or multilateral framework makes possible, but which cannot be priced without a
            # real ownership-split/cultural-test fact not yet on file for this project. Never
            # executable, never included in any of the counts above, never eligible to become
            # the leading/selected structure.
            "optimizer_opportunities_requiring_facts": optimizer_opportunities_requiring_facts,
            "optimizer_opportunities_requiring_facts_total": optimizer_opportunities_requiring_facts_total,
            # Exact counts every surface should render its disclosure copy from, rather than
            # taking len() of a served array client-side.
            "optimizer_executable_total": optimizer_executable_total,
            "optimizer_recommendation_status_counts": optimizer_recommendation_status_counts,
            # PRODUCTION-FIT (2026-10-01): exact fit counts over the same served universe
            # (scenario_total == optimizer_scenarios_total; fit never removes a scenario).
            "optimizer_production_fit_counts": _fit_counts,
            "production_fit_basis": (
                "REQUIREMENTS_ON_FILE" if (_fit_requirements.environments or _fit_requirements.required_capabilities)
                else "NO_REQUIREMENTS_ON_FILE"
            ),
            # Practical producer projection -- BACKWARD-COMPATIBLE ALIAS for
            # recommended_optimizer_options ONLY (never a second, independently-filtered
            # collection). No UI surface may treat this as the sole admissible Optimizer pool.
            "producer_optimizer_options": producer_optimizer_options,
            "producer_optimizer_options_total": producer_optimizer_options_total,
            "producer_optimizer_options_by_type": producer_optimizer_options_by_type,
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
    source_incentive_estimates: list[dict] = []
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
        # Project-evidence reconciliation: the producer's own stated
        # incentive/rebate estimate line (e.g. "EDB Rebate at 35%"), never
        # counted as spend/QPE (see _REBATE_EXCLUSION_RE) but real project
        # evidence that must not be silently invisible -- see
        # budget_parser.SourceIncentiveEstimate and migration 0078.
        source_incentive_estimates = list(budget_doc.source_incentive_estimates or [])
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
            "source_incentive_estimates": source_incentive_estimates,
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

    # Program-version safeguard: CineGlobe's only California rate doctrine
    # (US_CA_DOCTRINE, program_slug "ca_film_30") is Program 4.0, whose own
    # provenance states it is effective only for "taxable years beginning
    # on or after 2025-01-01" (AB 1138, verbatim). A production holding a
    # real, dated Credit Allocation Letter from BEFORE that date (e.g.
    # Lips Like Sugar's signed Program 3.0 letter #8-053, dated 2023-03-06)
    # was never under Program 4.0 at all -- CineGlobe has no verified
    # Program 3.0 rate schedule to substitute, so the correct, honest
    # behavior is disclosure, never a silent reprice: the canonical
    # calculated incentive (necessarily computed on Program 4.0 rates,
    # since that is the only doctrine this engine has) must never be
    # presented as if it reconciles against, confirms, or supersedes the
    # production's own real reserved allocation under its own program
    # version. Keyed on jurisdiction + fact pattern, not any one
    # production's name -- applies to any current or future California
    # production carrying a dated allocation letter this way.
    allocation_date = facts["answers"].get("ca_allocation_letter_date")
    home_jurisdiction_code = None
    if allocation_date and project.home_jurisdiction_id:
        home_jurisdiction_code = await session.scalar(
            select(Jurisdiction.code).where(Jurisdiction.id == project.home_jurisdiction_id)
        )
    if allocation_date and home_jurisdiction_code == "US-CA":
        _CA_PROGRAM_4_EFFECTIVE_DATE = "2025-01-01"
        if allocation_date < _CA_PROGRAM_4_EFFECTIVE_DATE:
            facts["program_version_cautions"] = [{
                "jurisdiction_code": "US-CA",
                "fact_key": "ca_allocation_letter_date",
                "allocation_date": allocation_date,
                "allocation_program_version": facts["answers"].get("ca_allocation_program_version"),
                "canonical_doctrine_program_version": "California Film & Television Tax Credit Program 4.0",
                "canonical_doctrine_effective_date": _CA_PROGRAM_4_EFFECTIVE_DATE,
                "warning": (
                    "This production's real Credit Allocation Letter predates California "
                    "Program 4.0's effective date. CineGlobe has no verified Program 3.0 rate "
                    "schedule, so its canonical calculated incentive necessarily uses Program "
                    "4.0 rates and must never be treated as confirming, reconciling against, "
                    "or repricing this production's own reserved allocation under its actual "
                    "program version -- the reserved allocation stands as its own authoritative "
                    "evidence, separate from the canonical calculation."
                ),
            }]
        else:
            facts["program_version_cautions"] = []
    else:
        facts["program_version_cautions"] = []

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
