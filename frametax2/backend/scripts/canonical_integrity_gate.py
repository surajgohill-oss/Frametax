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
from app.services.canonical_evaluation import _is_discretionary_program
from app.services.canonical_production_view import build_production_and_structures
from app.services.canonical_evaluation import evaluate_project
from app.services.program_onboarding_conformance import (
    CONFORMANT,
    NONCONFORMANT,
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

        # TREATY ALLOCATION — Optimizer P0 wiring remediation, P0-3.
        # Checked BEFORE the is_fully_priced continue below: a treaty
        # opportunity's conditional_scenario is nested trace data, never
        # reflected on the structure's own top-level is_fully_priced
        # (these rows are disclosure-only opportunities, not priced
        # candidates). Asserts the exact invariant Codex's audit demands:
        # a resolved conditional scenario's participant allocation must
        # sum to exactly 100% (one source budget, never independently
        # priced per participant), and fully_priced may only be True when
        # that allocation is genuinely complete.
        conditional = s.get("conditional_scenario")
        if conditional and conditional.get("status") == "CONDITIONAL_PROJECT_FACT_DEPENDENT":
            alloc = conditional.get("participant_allocation_pct")
            if conditional.get("fully_priced") is True:
                if not alloc:
                    result["failures"].append(
                        f"TREATY ALLOCATION: {label} fully_priced=True but no "
                        "participant_allocation_pct is disclosed — cannot prove one budget was allocated"
                    )
                elif abs(sum(alloc.values()) - 100.0) > 0.01:
                    result["failures"].append(
                        f"TREATY ALLOCATION: {label} participant_allocation_pct={alloc} sums to "
                        f"{sum(alloc.values())}, not 100 — the same double-counting/under-allocation "
                        "defect Codex found on LU GB/IE (186.2% of gross)"
                    )
                gross_budget = declared_gross
                combined_incentive = conditional.get("conditional_incentive_usd")
                if gross_budget and combined_incentive is not None and combined_incentive > gross_budget * 2.0:
                    result["failures"].append(
                        f"TREATY ALLOCATION: {label} combined conditional_incentive_usd="
                        f"{combined_incentive} implausibly exceeds 2x the declared gross budget "
                        f"{gross_budget} — likely double-counted, not allocated"
                    )
            elif (
                alloc and abs(sum(alloc.values()) - 100.0) < 0.01
                and not conditional.get("canonical_data_gaps")
            ):
                # A feasible (100%-summing) allocation with NO real
                # canonical_data_gaps should have produced fully_priced=
                # True. If canonical_data_gaps IS non-empty, fully_priced=
                # False is genuinely correct (a real, unrelated missing-
                # rate-rule disclosure, e.g. ca_cmf) and must never be
                # flagged as a P0-3 allocation defect.
                result["failures"].append(
                    f"TREATY ALLOCATION: {label} allocation sums to 100 (feasible) but "
                    "fully_priced is not True — a resolved, complete allocation must be reported "
                    "as fully priced, not silently left conditional"
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

        # PARTICIPANTS — Optimizer P0 wiring remediation P0-2, strengthened
        # by Optimizer FINAL P0 remediation (P0-PART-001, Codex broader-
        # corpus audit dcc6dde/8890cc8): exact claiming-participant
        # identity, never a count floor and never an unconditional
        # {primary} seed. Codex found this gate's PRIOR version
        # unconditionally added `primary_jurisdiction` to the expected
        # set before applying the claims filter — the EXACT SAME bug as
        # the production code it was meant to guard, so it reproduced
        # rather than detected P0-PART-001 whenever a project's own
        # primary segment does not claim an incentive (confirmed live:
        # 1,878 of 2,585 component rows across nine US-primary projects).
        # The expected set must be derived purely from segments whose OWN
        # claims_incentive is True — the primary jurisdiction included
        # ONLY if its own segment claims. A non-claiming stated-location
        # segment (claims_incentive=False, e.g. a real US segment) must
        # never appear in participants; it stays visible in segments.
        participants = s.get("participants") or []
        if s["structure_type"] == "component_relocation":
            expected_participants = {
                seg["jurisdiction_code"] for seg in (s.get("segments") or [])
                if seg.get("claims_incentive") is True and seg.get("jurisdiction_code")
            }
            if set(participants) != expected_participants:
                result["failures"].append(
                    f"PARTICIPANTS: {label} component_relocation participants={participants} "
                    f"!= expected claiming set {sorted(expected_participants)} "
                    "(a non-claiming stated-location segment must never appear; every real "
                    "claiming segment must)"
                )
        elif s["structure_type"] in ("single_country", "full_relocation"):
            if participants != [s["primary_jurisdiction"]]:
                result["failures"].append(
                    f"PARTICIPANTS: {label} {s['structure_type']} participants={participants} "
                    f"(expected exactly [{s['primary_jurisdiction']}])"
                )

        # STATUS (Section 5)
        if "administrative_allocation_risk" not in s:
            result["failures"].append(f"STATUS: {label} missing administrative_allocation_risk field")

        # PROGRAM CERTAINTY (Section 4 / Item generic) — a discretionary
        # program's structure must disclose administrative_allocation_risk.
        program_slugs = _program_slugs_of(s)
        if any(_is_discretionary_program(slug) for slug in program_slugs):
            if s.get("administrative_allocation_risk") is not True:
                result["failures"].append(
                    f"PROGRAM CERTAINTY: {label} uses discretionary program(s) {program_slugs} "
                    "but administrative_allocation_risk is not True — deterministic-vs-potential "
                    "separation is not actually wired at the structure level"
                )

        # PROGRAM ONBOARDING / CONFORMANCE — cross-check against the
        # global program classification (Item C — passed in by the
        # caller, computed once for the whole run, never per-project).
        for slug in program_slugs:
            classification = conformance_by_slug.get(slug)
            if classification == NONCONFORMANT:
                result["failures"].append(
                    f"PROGRAM ONBOARDING: {label} is PRICED using program {slug!r}, which is "
                    "classified NONCONFORMANT — a program with no resolvable jurisdiction and/or "
                    "no rate rule must never silently reach optimizer output"
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
    n_conditional = len(program_conformance) - n_conformant - n_nonconformant

    print(f"Canonical Integrity Gate — {len(projects)} library project record(s) discovered")
    print(
        f"Program onboarding conformance — {len(program_conformance)} optimizer-visible program(s): "
        f"{n_conformant} CONFORMANT, {n_conditional} CONDITIONAL, {n_nonconformant} NONCONFORMANT\n"
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

    print()
    if any_failures:
        print(f"CANONICAL INTEGRITY GATE ({len(_TESTED_INVARIANTS)} non-Globe invariants): FAIL")
        return 1
    print(f"CANONICAL INTEGRITY GATE ({len(_TESTED_INVARIANTS)} non-Globe invariants): PASS — GLOBE remains separately DEFERRED BY SEQUENCING")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
