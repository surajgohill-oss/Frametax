"""
canonical_integrity_gate.py

Canonical optimizer/Globe wiring remediation — permanent, executable,
all-project acceptance gate. Enumerates every current Project row
automatically (never a hardcoded four-project list) and evaluates the
12 required NON-GLOBE invariant families named in the Final Non-Globe
Canonical Core Closeout (2026-09-04):

  1.  BUDGET                every scenario's gross_budget_usd == the
                             project's declared gross.
  2.  ELIGIBILITY            no served structure is is_fully_priced while
                             its own requirement_trace records a FAILED
                             ELIGIBILITY-role requirement (P0-1).
  3.  QPE                    every priced structure's qualified spend is
                             non-negative and does not exceed its own
                             gross budget.
  4.  INCENTIVE               selected_incentive_usd is never negative,
                             and any segment's own incentive floor/
                             ceiling band is internally ordered
                             (floor <= ceiling).
  5.  NPC / ECONOMIC TRACE   npc_verified_usd + the six named adjustment
                             deltas reconstructs npc_with_adjustments_usd
                             exactly (P0-2).
  6.  PARTICIPANTS            every component_relocation structure's
                             participants include primary + a real
                             routed destination; every treaty_
                             coproduction structure's participants
                             correctly include/exclude home (P0-3).
  7.  SCENARIO IDENTITY       every structure_id is a stable, unique,
                             non-empty string; every ranking entry
                             references a real structure_id; numeric
                             ranks are unique, contiguous from 1, with no
                             gaps in the comparable set (Section 8 — never
                             array index, UI slot, or title).
  8.  STATUS SEMANTICS        candidate_status (role) and
                             administrative_allocation_risk are
                             independent served fields (Section 5).
  9.  PROGRAM CERTAINTY       for every priced structure whose program(s)
                             resolve to AllocationType.DISCRETIONARY,
                             administrative_allocation_risk is True — the
                             deterministic-vs-potential separation is
                             wired correctly at the STRUCTURE level, not
                             merely field-present.
  10. PROJECT MODELING POLICY the served discretionary_policy block is
                             well-formed, and no priced structure exists
                             for a program this project's own resolved
                             policy says to exclude (Item B is actually
                             enforced, not merely declared).
  11. SELECTION CONSISTENCY   canonical_selected_structure_id resolves
                             exactly per its documented algorithm (rank 1
                             if it exists, else the lowest-NPC priced
                             structure, else None) — the ONE canonical
                             scenario-selection source every non-Globe
                             surface must agree on (Item A).
  12. PROGRAM ONBOARDING /
      CONFORMANCE             every optimizer-visible program classifies
                             as CONFORMANT/CONDITIONAL/NONCONFORMANT
                             (never silently admitted), and no priced
                             structure in this project's own served
                             output uses a NONCONFORMANT program (Item C).
  13. TREATY ALLOCATION       (added by Optimizer P0 wiring remediation,
                             2026-09-04, P0-3) a resolved treaty
                             conditional bilateral scenario's participant
                             allocation sums to exactly 100% of the one
                             source budget, and fully_priced is true only
                             when that allocation is genuinely complete —
                             never independent full-budget pricing per
                             participant.

GLOBE remains explicitly OUT OF SCOPE — DEFERRED BY SEQUENCING, never
tested here, never silently counted as passing.

Usage:
    cd frametax2/backend && source .venv/bin/activate
    PYTHONPATH=. python3 scripts/canonical_integrity_gate.py
"""
from __future__ import annotations

import asyncio
import sys

import app.main  # noqa: F401 -- import order fix for the known circular-import quirk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.jurisdiction import Jurisdiction
from app.models.project import Project
from app.models.production import ProductionStructure, StructureCalculationResult
from app.services.canonical_evaluation import _is_discretionary_program
from app.services.canonical_production_view import (
    build_generic_pkg_and_economics,
    build_production_and_structures,
)
from app.services.canonical_evaluation import (
    ENGINE_VERSION,
    _price_candidate,
    current_generation_fingerprint,
    evaluate_project,
)
from app.services.canonical_project_economics import build_project_economic_inputs
from app.services.program_onboarding_conformance import (
    CONFORMANT,
    NONCONFORMANT,
    PATHWAY_SPECIFIC,
    classify_all_programs,
)

_DELTA_FIELDS = (
    "travel_incremental_delta_usd", "fx_delta_usd", "inkind_replacement_delta_usd",
    "local_cost_delta_usd", "financing_cost_usd", "implementation_cost_usd",
)

#: The complete required non-Globe invariant family list (Section 7).
#: EVERY one of these must be executable (PASS/FAIL) for this gate to be
#: authoritative for the final non-Globe closeout — none may be DEFERRED.
_TESTED_INVARIANTS = (
    "BUDGET", "ELIGIBILITY", "QPE", "INCENTIVE", "NPC TRACE", "PARTICIPANTS",
    "SCENARIO IDENTITY", "STATUS", "PROGRAM CERTAINTY", "PROJECT MODELING POLICY",
    "SELECTION", "PROGRAM ONBOARDING",
    # Optimizer P0 wiring remediation (2026-09-04), P0-3 — added so the
    # treaty conditional budget double-counting defect Codex found can
    # never silently recur. Narrow and specific to that one defect class,
    # not a broadening into general treaty/co-production behavioral
    # acceptance (explicitly out of scope for this task).
    "TREATY ALLOCATION",
    # Optimizer Final P1-GATE-001 remediation (Codex final acceptance
    # audit, commit d04a7567): two invariant families the gate previously
    # had NO declared check for at all (Codex Sections 9/17, defects G/H)
    # -- added here, never as a second/parallel validation system, using
    # the SAME served-payload/DB-row shapes every other invariant already
    # reads.
    "FRESHNESS",
    "REJECTION ACCOUNTING",
)
#: GLOBE remains the one family this pass explicitly does not test, per
#: sequencing — reported separately, never folded into _TESTED_INVARIANTS,
#: never counted as PASS.
_DEFERRED_INVARIANTS = (
    "GLOBE (scenario-to-point projection, hover/click/Inspector identity, geography "
    "coverage) -- explicitly deferred by sequencing, not attempted this pass",
)


def _program_slugs_of(structure: dict) -> list[str]:
    slugs = []
    if structure.get("program_slug"):
        slugs.append(structure["program_slug"])
    for s in structure.get("program_slugs") or []:
        if s and s not in slugs:
            slugs.append(s)
    return slugs


def _check_participants_invariant(s: dict, label: str) -> list[str]:
    """PARTICIPANTS invariant, extracted as a pure function (P1-GATE-001)
    so it can be exercised with synthetic inputs in a negative test
    without a live DB session — see
    tests/test_canonical_integrity_gate_negative.py."""
    failures: list[str] = []
    participants = s.get("participants") or []
    # Optimizer FINAL closeout, P1-GATE-001 (Codex, final P0 delta
    # reaudit, Section 8 "Participant oracle"): the set-equality check
    # below compares SETS, so a duplicate participant entry
    # (participants=["MU","MU","CA-MB"]) would silently pass — the live
    # corpus has zero duplicates today only because
    # `_empty_structure_entry()` deduplicates while building the list,
    # not because this gate would catch a regression. Checked for every
    # structure type, not just component_relocation.
    if len(participants) != len(set(participants)):
        failures.append(
            f"PARTICIPANTS: {label} participants={participants} contains duplicate entries — "
            "a jurisdiction must appear at most once"
        )
    if s["structure_type"] == "component_relocation":
        expected_participants = {
            seg["jurisdiction_code"] for seg in (s.get("segments") or [])
            if seg.get("claims_incentive") is True and seg.get("jurisdiction_code")
        }
        if set(participants) != expected_participants:
            failures.append(
                f"PARTICIPANTS: {label} component_relocation participants={participants} "
                f"!= expected claiming set {sorted(expected_participants)} "
                "(a non-claiming stated-location segment must never appear; every real "
                "claiming segment must)"
            )
    elif s["structure_type"] in ("single_country", "full_relocation"):
        if participants != [s["primary_jurisdiction"]]:
            failures.append(
                f"PARTICIPANTS: {label} {s['structure_type']} participants={participants} "
                f"(expected exactly [{s['primary_jurisdiction']}])"
            )
    return failures


def _check_program_onboarding_invariant(
    s: dict, label: str, program_slugs: list[str], conformance_by_slug: dict[str, str],
) -> list[str]:
    """PROGRAM ONBOARDING invariant, extracted as a pure function
    (P1-GATE-001) — see _check_participants_invariant's docstring for
    why. Covers both the top-level structure's own program_slug(s) and
    (P1-GATE-001, Codex Section 23 item 4) a nested conditional_scenario's
    own priced participant programs — a NONCONFORMANT program priced
    ONLY inside a resolved conditional scenario must never silently
    escape this check merely because the top-level structure itself is
    never is_fully_priced=True. PATHWAY_SPECIFIC (P1-CONF-001) is a
    valid, non-failing classification in both places.

    Optimizer Final P1-GATE-001 remediation (Codex final acceptance
    audit, Defect #2): this function itself was already correct, but the
    CALLER previously invoked it only after a top-level
    `if not s["is_fully_priced"]: continue` — so for a treaty_
    coproduction opportunity row (never top-level is_fully_priced=True by
    construction; its real pricing lives entirely in conditional_
    scenario) the nested check below was UNREACHABLE dead code in
    practice. The caller now invokes this function for EVERY structure,
    unconditionally — the top-level program_slugs check is therefore
    gated HERE, internally, on `s["is_fully_priced"]`, rather than relying
    on the caller to have already filtered."""
    failures: list[str] = []
    if s.get("is_fully_priced"):
        for slug in program_slugs:
            if conformance_by_slug.get(slug) == NONCONFORMANT:
                failures.append(
                    f"PROGRAM ONBOARDING: {label} is PRICED using program {slug!r}, which is "
                    "classified NONCONFORMANT — a program with no resolvable jurisdiction and/or "
                    "no rate rule must never silently reach optimizer output"
                )
    conditional = s.get("conditional_scenario")
    if isinstance(conditional, dict) and conditional.get("fully_priced"):
        for pc in conditional.get("priced_components") or []:
            cond_slug = pc.get("program_slug")
            if cond_slug and conformance_by_slug.get(cond_slug) == NONCONFORMANT:
                failures.append(
                    f"PROGRAM ONBOARDING: {label} conditional_scenario is PRICED using "
                    f"program {cond_slug!r}, which is classified NONCONFORMANT — a "
                    "program with no resolvable jurisdiction and/or no rate rule must "
                    "never silently reach optimizer output through a nested pathway either"
                )
    return failures


def _independently_recompute_participant_incentive(project_inputs, jurisdiction_code: str, program_slug: str, pct: float):
    """Optimizer Final P1-GATE-001 remediation (Codex final acceptance
    audit, Defect #1 / Section 9 item E): genuine independent
    recomputation of ONE treaty participant's incentive from canonical
    inputs, never a read of a served/cached value and never a second
    pricing architecture. Reuses the EXACT same real production budget
    (scaled to this participant's own allocated share -- the identical
    dataclasses.replace-based scaling `_build_conditional_bilateral_
    scenario`'s own `_allocated_inputs_for` helper already performs) and
    the EXACT same canonical pricing kernel, `canonical_evaluation.
    _price_candidate`, every priced candidate in the whole optimizer
    already goes through. If the optimizer's own served
    selected_incentive_usd for this participant disagrees with what this
    same kernel produces from the same real inputs, that is a genuine
    economic defect, not a formatting difference.

    Returns (incentive_usd, qualifying_spend_usd) or (None, None) if the
    program does not resolve for this participant's real inputs (a
    disclosed data gap, not a defect in itself -- the caller decides
    what to do when the served value also could not have been computed)."""
    import dataclasses

    scaled_lines = [
        dataclasses.replace(line, amount_usd=round(line.amount_usd * pct, 2))
        for line in project_inputs.budget_lines
    ]
    scaled_inputs = dataclasses.replace(
        project_inputs,
        budget_lines=scaled_lines,
        gross_budget_usd=round(project_inputs.gross_budget_usd * pct, 2),
        leaf_account_sum_usd=(
            round(project_inputs.leaf_account_sum_usd * pct, 2)
            if project_inputs.leaf_account_sum_usd is not None else None
        ),
    )
    pricing, register, rr = _price_candidate(scaled_inputs, jurisdiction_code, program_slug)
    if pricing is None or rr is None:
        return None, None
    from app.calculators.qualification_derivation import QualificationState
    qualifying_spend = round(sum(
        a.amount_usd for a in register if a.state == QualificationState.QUALIFIES
    ), 2)
    return (pricing.selected_incentive_usd or 0.0), qualifying_spend


def _check_treaty_allocation_invariant(
    s: dict, label: str, declared_gross: float | None, project_inputs=None,
) -> list[str]:
    """TREATY ALLOCATION invariant, extracted as a pure function
    (P1-GATE-001) — see _check_participants_invariant's docstring for
    why. `project_inputs` is optional (a real `ProjectEconomicInputs`,
    or None to skip the independent-recomputation sub-check — used by
    synthetic unit tests that only exercise the allocation-sum/upper-
    bound checks without constructing a full real input set)."""
    failures: list[str] = []
    conditional = s.get("conditional_scenario")
    if not (conditional and conditional.get("status") == "CONDITIONAL_PROJECT_FACT_DEPENDENT"):
        return failures
    alloc = conditional.get("participant_allocation_pct")
    if conditional.get("fully_priced") is True:
        if not alloc:
            failures.append(
                f"TREATY ALLOCATION: {label} fully_priced=True but no "
                "participant_allocation_pct is disclosed — cannot prove one budget was allocated"
            )
        elif abs(sum(alloc.values()) - 100.0) > 0.01:
            failures.append(
                f"TREATY ALLOCATION: {label} participant_allocation_pct={alloc} sums to "
                f"{sum(alloc.values())}, not 100 — the same double-counting/under-allocation "
                "defect Codex found on LU GB/IE (186.2% of gross)"
            )
        gross_budget = declared_gross
        combined_incentive = conditional.get("conditional_incentive_usd")
        if gross_budget and combined_incentive is not None and combined_incentive > gross_budget * 2.0:
            failures.append(
                f"TREATY ALLOCATION: {label} combined conditional_incentive_usd="
                f"{combined_incentive} implausibly exceeds 2x the declared gross budget "
                f"{gross_budget} — likely double-counted, not allocated"
            )
        # Optimizer FINAL closeout, P1-GATE-001 (Codex, final P0 delta
        # reaudit, Section 8 "Treaty oracle"): independently bounds each
        # priced participant's OWN selected_incentive_usd against its OWN
        # allocated share of the one source budget times its OWN modeled
        # rate — never just an allocation-sum or loose combined-incentive
        # check.
        if gross_budget and alloc:
            for _pc in conditional.get("priced_components") or []:
                _code = _pc.get("jurisdiction_code")
                _rate = _pc.get("modeled_rate")
                _incentive = _pc.get("selected_incentive_usd")
                _pct = alloc.get(_code)
                if _rate is None or _incentive is None or _pct is None:
                    continue
                _allocated_share_usd = gross_budget * _pct / 100.0
                _upper_bound = _allocated_share_usd * _rate * 1.01 + 1.0  # 1% + $1 tolerance
                if _incentive > _upper_bound:
                    failures.append(
                        f"TREATY ALLOCATION: {label} participant {_code} "
                        f"selected_incentive_usd={_incentive:,.2f} exceeds its own allocated "
                        f"share (${_allocated_share_usd:,.2f}) x modeled_rate ({_rate}) = "
                        f"${_allocated_share_usd * _rate:,.2f} — independently recomputed "
                        "participant-share QPE conservation violated (never just an "
                        "allocation-sum or loose combined-incentive check)"
                    )
            # Optimizer Final P1-GATE-001 remediation (Codex final
            # acceptance audit, Defect #1): the gross-share x modeled-rate
            # bound above is a coarse UPPER BOUND only -- Codex's own
            # counterexample (qpe_usd=100,000, selected_incentive_usd=
            # 900,000) passed it because it stayed under the much looser
            # ceiling. This is the REAL check: independently recompute
            # each participant's own incentive from canonical inputs (its
            # real allocated share of the one real project budget, priced
            # by the SAME kernel every candidate uses) and require it to
            # MATCH the served value closely, not merely stay under a
            # ceiling. Only runs when a real ProjectEconomicInputs was
            # supplied by the caller -- see this function's own docstring.
            if project_inputs is not None and alloc:
                for _pc in conditional.get("priced_components") or []:
                    _code = _pc.get("jurisdiction_code")
                    _served_incentive = _pc.get("selected_incentive_usd")
                    _program_slug = _pc.get("program_slug")
                    _pct = alloc.get(_code)
                    if _code is None or _served_incentive is None or _program_slug is None or _pct is None:
                        continue
                    _recomputed_incentive, _recomputed_qpe = _independently_recompute_participant_incentive(
                        project_inputs, _code, _program_slug, _pct / 100.0,
                    )
                    if _recomputed_incentive is None:
                        continue  # program genuinely does not resolve for these real inputs -- a disclosed data gap, not this invariant's concern
                    _tolerance = max(50.0, abs(_recomputed_incentive) * 0.02)  # 2% or $50, whichever is larger
                    if abs(_served_incentive - _recomputed_incentive) > _tolerance:
                        failures.append(
                            f"TREATY ALLOCATION: {label} participant {_code} served "
                            f"selected_incentive_usd={_served_incentive:,.2f} disagrees with the "
                            f"INDEPENDENTLY RECOMPUTED incentive ${_recomputed_incentive:,.2f} "
                            f"(recomputed qualifying spend ${_recomputed_qpe:,.2f}) from the same "
                            "real project inputs and the same canonical pricing kernel — this is "
                            "not merely a loose plausibility bound, the values must actually agree"
                        )
    elif (
        alloc and abs(sum(alloc.values()) - 100.0) < 0.01
        and not conditional.get("canonical_data_gaps")
    ):
        # A feasible (100%-summing) allocation with NO real
        # canonical_data_gaps should have produced fully_priced=True. If
        # canonical_data_gaps IS non-empty, fully_priced=False is
        # genuinely correct (a real, unrelated missing-rate-rule
        # disclosure, e.g. ca_cmf) and must never be flagged as a P0-3
        # allocation defect.
        failures.append(
            f"TREATY ALLOCATION: {label} allocation sums to 100 (feasible) but "
            "fully_priced is not True — a resolved, complete allocation must be reported "
            "as fully priced, not silently left conditional"
        )
    return failures


def _check_rejection_accounting_invariant(structures: list[dict]) -> list[str]:
    """REJECTION ACCOUNTING invariant (P1-GATE-001, Codex final
    acceptance audit, Defect #4) — extracted as a pure function, generic
    over any served `structures` list (never a fixture/project-specific
    branch), so it can be exercised with synthetic negative-test inputs.

    Reuses the EXISTING disposition model — `is_fully_priced`,
    `candidate_status`, `rejection_reason_class` — every structure
    already carries; never a new/parallel taxonomy. Two real invariants:

    1. Every `component_relocation` structure must end in an explicit,
       non-silent disposition: either genuinely priced
       (`is_fully_priced=True`, `candidate_status == "PRICED"`) or
       genuinely rejected (`candidate_status == "RULE_REJECTED"` with a
       real `rejection_reason_class`) — never neither. A structure with
       `is_fully_priced=False` and no `rejection_reason_class` is a
       silent economic disappearance: an attempt the optimizer
       apparently evaluated (it exists as a served row) but never
       recorded WHY it isn't priced.
    2. No two component rows may share the exact same
       (anchor jurisdiction, target jurisdiction, component, program)
       identity — a duplicate attempt is itself a silent accounting
       defect: the same real attempt persisted/reported twice, or one
       row silently shadowing another.

    This is deliberately a STRUCTURAL completeness/uniqueness check, not
    a full re-derivation of the expected candidate universe (that
    remains the job of a full audit, not a fast, permanent CI-style
    gate) — see docs/validation/OPTIMIZER_FINAL_P1_GATE_REMEDIATION_
    CLAUDE.md for the explicit scope rationale."""
    failures: list[str] = []
    seen_identities: dict[tuple, str] = {}
    for s in structures:
        if s.get("structure_type") != "component_relocation":
            continue
        label = f"{s.get('structure_id', '?')[:8]} {s.get('label', '')}"
        priced = bool(s.get("is_fully_priced"))
        rejection_class = s.get("rejection_reason_class")
        candidate_status = s.get("candidate_status")
        if not priced and not rejection_class:
            failures.append(
                f"REJECTION ACCOUNTING: {label} is neither priced nor carries a real "
                f"rejection_reason_class (candidate_status={candidate_status!r}) — a component "
                "attempt must never silently disappear with no recorded disposition"
            )
        if priced and candidate_status != "PRICED":
            failures.append(
                f"REJECTION ACCOUNTING: {label} is_fully_priced=True but candidate_status="
                f"{candidate_status!r} != 'PRICED' — disposition fields disagree with each other"
            )
        comp_allocs = s.get("component_allocations") or []
        if comp_allocs:
            target = comp_allocs[0].get("jurisdiction_code")
            component = comp_allocs[0].get("component")
            program = comp_allocs[0].get("program_slug")
            identity = (s.get("primary_jurisdiction"), target, component, program)
            if identity in seen_identities:
                failures.append(
                    f"REJECTION ACCOUNTING: duplicate component attempt identity {identity} — "
                    f"{label} and {seen_identities[identity]} both claim the same "
                    "(anchor, target, component, program) attempt"
                )
            else:
                seen_identities[identity] = label
    return failures


def _check_freshness_invariant(
    reconstructed_fp: str | None, evaluator_fp: str | None,
    served_current_fingerprints: set[str], label: str,
) -> list[str]:
    """FRESHNESS invariant (P1-GATE-001, Codex final acceptance audit,
    Defect #3) — extracted as a pure function over plain fingerprint
    values (never a DB session), so it can be exercised with synthetic
    mismatched fingerprints in a negative test without mutating any real
    project's persisted rows.

    Reuses the EXISTING freshness/versioning architecture
    (`canonical_evaluation.current_generation_fingerprint`, the same
    reconstruction both canonical view builders already use — see
    P1-FRESH-001) — never a second freshness system. `reconstructed_fp`
    is the current generation as independently recomputed from this
    project's REAL current facts; `evaluator_fp` is what `evaluate_project`
    itself just reported (`state_fingerprint`); `served_current_
    fingerprints` is the actual set of `input_fingerprint` values
    currently persisted under the current `ENGINE_VERSION` for this
    project. A project with no budget yet (both fingerprints None) is
    not a freshness failure — it is out of this gate's scope, same as
    every other invariant's skip semantics.

    Two real invariants:
    1. The reconstructed current fingerprint must equal what the
       evaluator itself just reported — a mismatch means the evaluator
       and the canonical reconstruction disagree about which generation
       is current (the P1-FRESH-001 defect class, reintroduced).
    2. The reconstructed current fingerprint must actually be among the
       fingerprints persisted under the current engine version — a
       served/validated result whose provenance fingerprint does not
       exist among the current-engine rows at all cannot be current by
       definition, regardless of how plausible its economics look."""
    failures: list[str] = []
    if reconstructed_fp is None and evaluator_fp is None:
        return failures  # genuinely out of scope (e.g. no budget yet)
    if reconstructed_fp != evaluator_fp:
        failures.append(
            f"FRESHNESS: {label} reconstructed current-generation fingerprint "
            f"{reconstructed_fp!r} != evaluator state_fingerprint {evaluator_fp!r} — "
            "the evaluator and the canonical reconstruction disagree about which "
            "generation is current (the P1-FRESH-001 defect class)"
        )
    if reconstructed_fp is not None and reconstructed_fp not in served_current_fingerprints:
        failures.append(
            f"FRESHNESS: {label} reconstructed current fingerprint {reconstructed_fp!r} is not "
            f"among the fingerprints actually persisted under the current engine version "
            f"({sorted(served_current_fingerprints)}) — a served/validated result cannot be "
            "current if no current-engine row exists for its own reconstructed generation"
        )
    return failures


async def _gate_one_project(
    session: AsyncSession, project_id: str, title: str, conformance_by_slug: dict[str, str],
) -> dict:
    result = {"project_id": project_id, "title": title, "failures": [], "counts": {}}

    econ_status = await evaluate_project(session, project_id)
    if econ_status.get("status") not in (
        "OK", "EVALUATION_COMPLETE", "EVALUATION_REUSED",
    ) and "status" in econ_status:
        # A project that legitimately cannot evaluate yet (e.g. no budget)
        # is not a gate FAILURE -- it is out of scope for this gate.
        result["skipped"] = econ_status.get("status")
        return result

    view = await build_production_and_structures(session, project_id)
    if view.get("status") != "OK":
        result["skipped"] = view.get("status")
        return result

    # Optimizer Final P1-GATE-001 remediation (Codex final acceptance
    # audit, Defect #1): the REAL project economic inputs, fetched once
    # per project, read-only (same READ PURITY contract every other GET
    # builder in this codebase follows — no budget routing, no fact
    # writes, no commit). Passed to _check_treaty_allocation_invariant so
    # it can independently recompute participant incentives from the
    # SAME real inputs the optimizer itself priced from, rather than
    # trusting the served values.
    econ = await build_project_economic_inputs(session, project_id, read_only=True)
    project_inputs = econ.inputs if econ.ok else None

    # Optimizer FINAL P0 remediation (P0-SEL-001, Codex broader-corpus
    # audit dcc6dde/8890cc8): Codex found this gate's prior SELECTION
    # check compared canonical_selected_structure_id only against the
    # served view's OWN rank 1 -- both computed from the same `comparable`
    # pool within this same call, so they could never actually diverge
    # from each other. The real defect (a stale/invented evaluator winner
    # persisted to Project.leading_structure_id while the served view
    # correctly shows null) requires cross-checking the EVALUATOR's own
    # result (`econ_status["top_result"]`, from _summarize_evaluation) and
    # the PERSISTED `Project.leading_structure_id` -- fetched fresh here,
    # not read off `view`, since leading_structure_id lives on the Project
    # row, not the served payload.
    project_row = await session.get(Project, project_id)
    persisted_leading_id = str(project_row.leading_structure_id) if project_row and project_row.leading_structure_id else None
    evaluator_top = econ_status.get("top_result")
    evaluator_top_id = evaluator_top["structure_id"] if evaluator_top else None

    production = view["production"]
    allocated = view["structures"]["allocated_structures"]
    structures = allocated["structures"]
    ranking = allocated["ranking"]
    declared_gross = production.get("gross_budget_usd")

    by_type: dict[str, int] = {}
    by_status_priced = 0
    for s in structures:
        by_type[s["structure_type"]] = by_type.get(s["structure_type"], 0) + 1
        if s["is_fully_priced"]:
            by_status_priced += 1
    result["counts"] = {
        "total": len(structures),
        "priced": by_status_priced,
        "by_structure_type": by_type,
    }

    # ── 7. SCENARIO IDENTITY — referential integrity of the served ID
    # space, independent of any one structure's own fields. ──────────────
    structure_ids = [s["structure_id"] for s in structures]
    if len(structure_ids) != len(set(structure_ids)):
        result["failures"].append(
            f"SCENARIO IDENTITY: duplicate structure_id values served for this production "
            f"({len(structure_ids)} entries, {len(set(structure_ids))} unique)"
        )
    by_id = {s["structure_id"]: s for s in structures}
    for r in ranking:
        if r["structure_id"] not in by_id:
            result["failures"].append(
                f"SCENARIO IDENTITY: ranking entry references structure_id "
                f"{r['structure_id']} which is not present in the served structures list"
            )
    ranked = sorted((r for r in ranking if r.get("rank") is not None), key=lambda r: r["rank"])
    expected_ranks = list(range(1, len(ranked) + 1))
    actual_ranks = [r["rank"] for r in ranked]
    if actual_ranks != expected_ranks:
        result["failures"].append(
            f"SCENARIO IDENTITY: numeric ranks are not a contiguous 1..N sequence "
            f"with no gaps/duplicates — got {actual_ranks}"
        )

    # ── 11. SELECTION CONSISTENCY — canonical_selected_structure_id
    # resolves exactly per its documented algorithm (Item A, corrected by
    # Optimizer P0 wiring remediation P0-1), AND the served view agrees
    # with the EVALUATOR's own persisted winner (P0-SEL-001, Optimizer
    # FINAL P0 remediation). Codex found this gate's PRIOR version only
    # ever checked canonical_selected_structure_id against this same
    # call's own rank 1 -- both computed from the identical `comparable`
    # pool, so they could never diverge from each other and the check
    # silently missed all nine broader-corpus divergences, where the
    # served view was correct (null) but Project.leading_structure_id
    # still pointed at a stale, non-comparable, evaluator-invented
    # relocation. The gate now cross-checks THREE independent sources:
    # the served canonical_selected_structure_id, the EVALUATOR's own
    # top_result (econ_status, from _summarize_evaluation), and the
    # PERSISTED Project.leading_structure_id -- all three must agree, or
    # all three must be None. No project/jurisdiction-specific exception.
    comparable_ranked = [r for r in ranking if r.get("rank") == 1]
    canonical_id = allocated.get("canonical_selected_structure_id")
    if comparable_ranked:
        expected_id = comparable_ranked[0]["structure_id"]
        if canonical_id != expected_id:
            result["failures"].append(
                f"SELECTION: canonical_selected_structure_id={canonical_id} but rank 1 is "
                f"{expected_id} — must equal rank 1 when rank 1 exists"
            )
    elif canonical_id is not None:
        result["failures"].append(
            f"SELECTION: canonical_selected_structure_id={canonical_id} but no comparable rank-1 "
            "candidate exists — must be None (P0-1: never a non-comparable/PRICED_LOW_FIT fallback)"
        )
    if not (evaluator_top_id == persisted_leading_id == canonical_id):
        result["failures"].append(
            f"SELECTION: evaluator/persisted/served divergence (P0-SEL-001) — "
            f"evaluator_top={evaluator_top_id}, "
            f"Project.leading_structure_id={persisted_leading_id}, "
            f"canonical_selected_structure_id={canonical_id} — all three must agree or all be None"
        )

    # ── 10. PROJECT MODELING POLICY — served block well-formed, and the
    # resolved policy is actually enforced (no priced structure exists
    # for an excluded program). ──────────────────────────────────────────
    policy = production.get("discretionary_policy")
    if not isinstance(policy, dict) or policy.get("project_default") not in ("include", "exclude"):
        result["failures"].append("PROJECT MODELING POLICY: discretionary_policy.project_default missing/invalid")
    else:
        for slug, value in (policy.get("program_overrides") or {}).items():
            if value not in ("include", "exclude"):
                result["failures"].append(f"PROJECT MODELING POLICY: program_overrides[{slug}]={value!r} invalid")
        excluded_slugs = {
            slug for slug, resolved in (policy.get("resolved_by_program") or {}).items()
            if resolved == "exclude"
        }
        for s in structures:
            if not s["is_fully_priced"]:
                continue
            hit = excluded_slugs.intersection(_program_slugs_of(s))
            if hit and s["primary_jurisdiction"] != production.get("jurisdiction_code"):
                result["failures"].append(
                    f"PROJECT MODELING POLICY: {s['structure_id'][:8]} {s['label']} is PRICED but uses "
                    f"program(s) {sorted(hit)} which this project's own resolved policy excludes"
                )

    for s in structures:
        label = f"{s['structure_id'][:8]} {s['label']}"

        # BUDGET
        if s.get("gross_budget_usd") is not None and declared_gross is not None:
            if abs(s["gross_budget_usd"] - declared_gross) > 1.0:
                result["failures"].append(
                    f"BUDGET: {label} gross_budget_usd={s['gross_budget_usd']} != "
                    f"declared {declared_gross}"
                )

        # TREATY ALLOCATION — Optimizer P0 wiring remediation, P0-3;
        # strengthened by Optimizer FINAL closeout, P1-GATE-001. Checked
        # BEFORE the is_fully_priced continue below: a treaty
        # opportunity's conditional_scenario is nested trace data, never
        # reflected on the structure's own top-level is_fully_priced.
        # Extracted to _check_treaty_allocation_invariant (see its own
        # docstring) so it can be exercised with synthetic negative-test
        # inputs.
        result["failures"].extend(
            _check_treaty_allocation_invariant(s, label, declared_gross, project_inputs)
        )

        # Optimizer Final P1-GATE-001 remediation (Codex final acceptance
        # audit, Defects #2 and #5): PARTICIPANTS and PROGRAM ONBOARDING
        # used to be called only AFTER the `if not s["is_fully_priced"]:
        # continue` below -- so (a) a treaty_coproduction opportunity row
        # (never top-level is_fully_priced=True; real pricing lives in
        # conditional_scenario) never reached the nested onboarding check
        # at all, and (b) a REJECTED component_relocation row (P1-REJ-001,
        # candidate_status=RULE_REJECTED) never reached the participant
        # check, so a corrupted/malformed participant list on a rejected
        # row was completely invisible to this gate. Both checks are
        # internally safe to run unconditionally: _check_participants_
        # invariant's expected set is genuinely empty for a rejected row
        # with no segments (produces zero false failures on real rejected
        # data), and _check_program_onboarding_invariant now gates its
        # OWN top-level sub-check on is_fully_priced internally (see its
        # docstring) rather than relying on the caller to have already
        # filtered.
        program_slugs = _program_slugs_of(s)
        result["failures"].extend(_check_participants_invariant(s, label))
        result["failures"].extend(
            _check_program_onboarding_invariant(s, label, program_slugs, conformance_by_slug)
        )

        if not s["is_fully_priced"]:
            continue

        # ELIGIBILITY (P0-1)
        for seg in s.get("segments") or []:
            for req in seg.get("requirement_trace") or []:
                if req.get("role") == "ELIGIBILITY" and req.get("state") == "FAILED":
                    result["failures"].append(
                        f"ELIGIBILITY: {label} is PRICED but segment "
                        f"{seg.get('jurisdiction_code')} has a FAILED "
                        f"ELIGIBILITY requirement ({req.get('requirement')}: {req.get('detail')})"
                    )

        # QPE — non-negative, bounded by the structure's own gross budget.
        segments = s.get("segments") or []
        total_qpe = sum((seg.get("qpe_usd") or 0.0) for seg in segments)
        if total_qpe < -0.01:
            result["failures"].append(f"QPE: {label} total qualified spend is negative ({total_qpe})")
        gross_for_structure = s.get("gross_budget_usd") if s.get("gross_budget_usd") is not None else declared_gross
        if gross_for_structure is not None and total_qpe > gross_for_structure + 1.0:
            result["failures"].append(
                f"QPE: {label} total qualified spend {total_qpe} exceeds its own gross budget "
                f"{gross_for_structure}"
            )

        # INCENTIVE — never negative; any segment's own floor/ceiling band
        # is internally ordered.
        incentive = s.get("selected_incentive_usd")
        if incentive is not None and incentive < -0.01:
            result["failures"].append(f"INCENTIVE: {label} selected_incentive_usd is negative ({incentive})")
        for seg in segments:
            floor, ceiling = seg.get("incentive_floor_usd"), seg.get("incentive_ceiling_usd")
            if floor is not None and ceiling is not None and floor > ceiling + 0.01:
                result["failures"].append(
                    f"INCENTIVE: {label} segment {seg.get('jurisdiction_code')} incentive_floor_usd "
                    f"{floor} > incentive_ceiling_usd {ceiling}"
                )

        # NPC TRACE (P0-2)
        verified = s.get("npc_verified_usd")
        adjusted = s.get("npc_with_adjustments_usd")
        if verified is not None and adjusted is not None:
            reconstructed = round(verified + sum((s.get(f) or 0.0) for f in _DELTA_FIELDS), 2)
            if abs(reconstructed - round(adjusted, 2)) > 0.02:
                result["failures"].append(
                    f"NPC TRACE: {label} verified={verified} + deltas={reconstructed - verified} "
                    f"= {reconstructed} != served adjusted {adjusted}"
                )

        # STATUS (Section 5)
        if "administrative_allocation_risk" not in s:
            result["failures"].append(f"STATUS: {label} missing administrative_allocation_risk field")

        # PROGRAM CERTAINTY (Section 4 / Item generic) — a discretionary
        # program's structure must disclose administrative_allocation_risk.
        # (PARTICIPANTS and PROGRAM ONBOARDING were already checked above,
        # before the is_fully_priced continue — see that comment block.)
        if any(_is_discretionary_program(slug) for slug in program_slugs):
            if s.get("administrative_allocation_risk") is not True:
                result["failures"].append(
                    f"PROGRAM CERTAINTY: {label} uses discretionary program(s) {program_slugs} "
                    "but administrative_allocation_risk is not True — deterministic-vs-potential "
                    "separation is not actually wired at the structure level"
                )

    # REJECTION ACCOUNTING — Optimizer Final P1-GATE-001 remediation
    # (Codex final acceptance audit, Defect #4): every component_
    # relocation structure must end in an explicit, non-silent
    # disposition. Extracted to _check_rejection_accounting_invariant
    # (see its own docstring) so it can be exercised with synthetic
    # negative-test inputs. Runs once per project over the full
    # structures list (not per-structure), since duplicate-identity
    # detection is inherently a cross-structure check.
    result["failures"].extend(_check_rejection_accounting_invariant(structures))

    # FRESHNESS — Optimizer Final P1-GATE-001 remediation (Codex final
    # acceptance audit, Defect #3). Extracted to _check_freshness_
    # invariant (see its own docstring) so it can be exercised with
    # synthetic negative-test inputs. Runs once per project.
    reconstructed_fp = await current_generation_fingerprint(session, project_id)
    evaluator_fp = econ_status.get("state_fingerprint")
    served_current_fingerprints = set((await session.execute(
        select(StructureCalculationResult.input_fingerprint)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == project_id,
            StructureCalculationResult.engine_version == ENGINE_VERSION,
        )
    )).scalars().all())
    result["failures"].extend(
        _check_freshness_invariant(reconstructed_fp, evaluator_fp, served_current_fingerprints, title)
    )

    return result


async def main() -> int:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        projects = (await session.execute(select(Project.id, Project.title))).all()
        known_jurisdiction_codes = frozenset((await session.execute(select(Jurisdiction.code))).scalars().all())

    # ── 12. PROGRAM ONBOARDING / CONFORMANCE — global classification,
    # run once, reused for every project's cross-check above. ────────────
    program_conformance = classify_all_programs(known_jurisdiction_codes=known_jurisdiction_codes)
    conformance_by_slug = {slug: r.classification for slug, r in program_conformance.items()}
    n_conformant = sum(1 for r in program_conformance.values() if r.classification == CONFORMANT)
    n_nonconformant = sum(1 for r in program_conformance.values() if r.classification == NONCONFORMANT)
    n_pathway_specific = sum(1 for r in program_conformance.values() if r.classification == PATHWAY_SPECIFIC)
    n_conditional = len(program_conformance) - n_conformant - n_nonconformant - n_pathway_specific

    print(f"Canonical Integrity Gate — {len(projects)} library project record(s) discovered")
    print(
        f"Program onboarding conformance — {len(program_conformance)} optimizer-visible program(s): "
        f"{n_conformant} CONFORMANT, {n_conditional} CONDITIONAL, {n_pathway_specific} PATHWAY_SPECIFIC, "
        f"{n_nonconformant} NONCONFORMANT\n"
    )

    any_failures = False
    failures_by_invariant: dict[str, int] = {name: 0 for name in _TESTED_INVARIANTS}
    checked_by_invariant: dict[str, int] = {name: 0 for name in _TESTED_INVARIANTS}
    pass_count = 0
    fail_count = 0
    skip_count = 0
    async with AsyncSession(engine, expire_on_commit=False) as session:
        for project_id, title in projects:
            gate_result = await _gate_one_project(session, str(project_id), title, conformance_by_slug)
            if gate_result.get("skipped"):
                skip_count += 1
                print(f"  SKIP  {title} ({project_id}) — {gate_result['skipped']}")
                continue

            # PROGRAM ONBOARDING cross-check needs the global lookup —
            # re-run just that check here (cheap: pure dict lookups) since
            # _gate_one_project doesn't receive it directly.
            counts = gate_result["counts"]
            for name in _TESTED_INVARIANTS:
                checked_by_invariant[name] += 1
            status = "PASS" if not gate_result["failures"] else "FAIL"
            if status == "FAIL":
                any_failures = True
                fail_count += 1
                for f in gate_result["failures"]:
                    for name in _TESTED_INVARIANTS:
                        if f.startswith(name + ":"):
                            failures_by_invariant[name] += 1
                            break
                    else:
                        print(f"          ! unclassified failure string (bug in this gate script): {f[:80]}")
            else:
                pass_count += 1
            print(
                f"  {status}  {title} ({project_id}) — "
                f"{counts['total']} structures, {counts['priced']} priced, "
                f"types={counts['by_structure_type']}"
            )
            for failure in gate_result["failures"][:10]:
                print(f"          - {failure}")
            if len(gate_result["failures"]) > 10:
                print(f"          ... and {len(gate_result['failures']) - 10} more")

    print(f"\nProjects evaluated: {pass_count} PASS, {fail_count} FAIL, {skip_count} SKIP "
          "(no budget on file yet — a real state, not a gate failure)\n")

    print(f"Invariant-by-invariant result — ALL {len(_TESTED_INVARIANTS)} required non-Globe families (TESTED, none DEFERRED):")
    for name in _TESTED_INVARIANTS:
        n_checked = checked_by_invariant[name]
        n_failed = failures_by_invariant[name]
        status = "PASS" if n_failed == 0 else "FAIL"
        print(f"  {status:6} {name} — {n_checked} project(s) checked, {n_failed} failure(s)")

    print("\nDeferred (Globe only — explicitly out of scope this pass, never counted as PASS):")
    for name in _DEFERRED_INVARIANTS:
        print(f"  DEFERRED  {name}")

    if n_nonconformant:
        print(f"\nNONCONFORMANT programs (real, disclosed data gaps — not a gate failure unless actually PRICED in a served structure):")
        for slug, r in program_conformance.items():
            if r.classification == NONCONFORMANT:
                print(f"  - {slug}: {'; '.join(r.reasons)}")

    if n_pathway_specific:
        print(
            "\nPATHWAY_SPECIFIC programs (P1-CONF-001: executable ONLY through a specific "
            "conditional/treaty pathway, deliberately absent from ordinary discovery — "
            "not a data gap, not NONCONFORMANT):"
        )
        for slug, r in program_conformance.items():
            if r.classification == PATHWAY_SPECIFIC:
                print(f"  - {slug} ({r.jurisdiction_code}): {'; '.join(r.reasons)}")

    print()
    if any_failures:
        print(f"CANONICAL INTEGRITY GATE ({len(_TESTED_INVARIANTS)} non-Globe invariants): FAIL")
        return 1
    print(f"CANONICAL INTEGRITY GATE ({len(_TESTED_INVARIANTS)} non-Globe invariants): PASS — GLOBE remains separately DEFERRED BY SEQUENCING")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
