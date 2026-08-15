# FVD Evaluation Runtime Closeout

Date: 2026-08-15
Branch: `claude/audit-frametax-features-NZcX5`
FVD project ID: `6c6f1c13-2d49-4bbc-bafb-2a12efa93112`

## Initial failure

Opened FVD's Project Record and clicked **Begin Evaluation**. Classification: **DEAD_BUTTON**. `ProjectRecord.jsx` rendered it `disabled` unconditionally for every non-served project, with a static tooltip ("Evaluation is not yet wired to arbitrary Library projects — Little Utopia only") and no `onClick` handler at all — no request, no route, nothing to trace past the button itself.

## Root cause

The "existing worldwide optimizer" turned out to be two separate things:

1. **The served path** (`/api/v1/cineglobe/*` → `app/demo/little_utopia_state.py::build_allocated_structures()`) — the one Little Utopia's UI actually calls. Reading it end to end showed it is not generically callable: it imports `app.data.little_utopia_real_budget`'s hand-classified account tables directly and reads a module-level singleton `LittleUtopiaState`. Building an FVD-specific equivalent of that hand-classified register would itself be exactly the "detailed budget estimation" this task's own scope excludes.
2. **A second, fully generic, DB-backed path** — `Jurisdiction` / `IncentiveProgram` / `QualifyingSpendCategory` / `ProductionStructure` / `StructureCalculationResult` tables plus `app/api/v1/structures.py`'s `generate_structure` / `calculate_structure` (→ `run_full_analysis`) — already populated (187 jurisdictions, 262 programs, 406 qualifying-spend categories) and already project-agnostic (`project_id`-parameterized throughout), but never called from anywhere in the frontend. `get_project_record`'s existing "Analysis" panel (`evaluation_begun` / `structures_available` / `leading_structure_name`) already reads from exactly these tables — it was built to receive this data and never had a writer.

Begin Evaluation's job was therefore to connect three already-existing pieces that had never been wired together: SA-1's `CanonicalProductionState`/`ProductionOptimizerInput`, Phase 6's generic `production_discovery.discover_executable_jurisdictions`, and this dormant DB-backed structures pipeline.

## Files changed

- `app/services/project_evaluation.py` (new) — the orchestrator. `begin_evaluation(session, project_id)`: builds `CanonicalProductionState` → `ProductionOptimizerInput` (existing, unchanged); if accepted, derives the production's base jurisdiction generically from budget-document filename evidence (only when not already confirmed); runs `derive_production_requirements` + `discover_executable_jurisdictions` (existing, unchanged) to get a candidate jurisdiction set; creates one `ProductionStructure` per candidate and calls the existing calculation logic; ranks by `true_net_cost_usd`; sets `Project.leading_structure_id`. Idempotent per `CanonicalProductionState.input_fingerprint`.
- `app/api/v1/structures.py` — `calculate_structure`'s body factored into an importable `calculate_structure_impl`, with three additive optional parameters (`extra_warnings`, `has_unverified_inputs_override`, `input_fingerprint`) so the orchestrator can attach provenance without duplicating the assembly/persistence logic. The route itself is now a one-line wrapper; behavior for existing callers is unchanged.
- `app/api/v1/evaluation.py` (new) — `POST /api/v1/projects/{id}/evaluation/begin`, a thin wrapper with no project ever named in it.
- `app/api/v1/projects.py` — `get_project_record`'s existing `analysis` payload gains three read-only fields sourced from the already-persisted leading structure's latest result: `leading_true_net_cost_usd`, `has_unverified_inputs`, `limitation_note`.
- `app/main.py` — registers the new router.
- `frontend/src/api.js` — `beginEvaluation(projectId)`.
- `frontend/src/screens/company/ProjectRecord.jsx` — the button is enabled for non-served projects, calls `beginEvaluation`, reloads the record on success, and surfaces a blocker message inline on `BUDGET_REQUIRED_FOR_CURRENT_EVALUATION` / `BLOCKED_INCOMPLETE_INPUTS`. The existing `AnalysisPanel` gains two lines (net production cost, limitation note) reading the three new fields above — no new page, no redesign.

## Budget provenance — PASS

`CanonicalProductionState.gross_budget_usd` for FVD resolves to **$4,517,687.00**, traced `DocumentVersion → BudgetDocument → BudgetLineItem → CanonicalProductionState.budget_lines → ProductionOptimizerInput.gross_production_cost_usd`. Confirmed distinct from Little Utopia's $4,364,393. No synthetic or hardcoded figure anywhere in the path.

## Geography provenance — PASS

`_derive_home_jurisdiction` matches every active `Jurisdiction.name` (word-boundary, case-insensitive) against the project's own budget document filenames. FVD's budget is `V-BRAT_V8_Greece_041224 TOPSHEET.pdf` — genuinely evidenced, matching SA-1.5's own prior finding that Greece is "established by the source budget itself, not inferred." (First attempt at this regex failed silently: `\bGreece\b` never matches `_Greece_` because `_` is a `\w` character in Python regex, so no boundary exists between `_` and a letter. Fixed by normalizing all non-alphanumeric runs to spaces before matching — caught by direct testing before the browser run, not left in.) `Project.home_jurisdiction_id` was previously `NULL` for FVD; it is now set to the real `Jurisdiction` row for Greece, written once, never overwritten on repeat evaluations.

**Genericity proof:** a focused test (`test_begin_evaluation_derives_home_jurisdiction_from_budget_filename_and_prices_it`) uses a *different* jurisdiction — Malta, named nowhere in FVD's data — via a filename `"Production Budget - Malta Shoot.csv"` on a disposable test project, and confirms the same code path derives Malta, not Greece. The derivation is generic; only the evidence differs.

## Canonical state — PASS

`build_optimizer_input` accepted FVD's state (`READY_FOR_OPTIMIZER`): script parsed, budget present, gross budget positive. `intended_shoot_days` and `base_jurisdiction` assumption rows remain genuinely `UNKNOWN` (recorded as `unknowns`, not blockers, not defaulted) — SA-1's own designed behavior, unchanged.

## Discovery / pricing summary

- **Jurisdictions examined:** 213 (the full canonical incentive-program + jurisdiction-profile catalog — never a hand-picked list)
- **Incentive-ready (accepted):** 30
- **Capability-only (incentive pending):** 80
- **Rejected:** 103
- **Priced:** 4 — Greece, Malta, New York, Mauritius. The remaining 26 accepted candidates were honestly skipped with an explicit reason each (`"no DB program record for <slug>"` — the in-memory discovery catalog and the DB-backed program registry have not yet been fully cross-slugged; disclosed in the run's own `skipped_candidates`, never silently dropped or faked).

| Structure | True net cost (USD) | Total incentive value (USD) |
|---|---:|---:|
| **Greece — production's current base** | **$3,627,135.60** | $284,252.40 |
| Full relocation to Malta | $3,733,730.25 | $177,657.75 |
| Full relocation to New York | $3,911,388.00 | $0.00 |
| Full relocation to Mauritius | $3,911,388.00 | $0.00 |

**Baseline NPC:** $3,627,135.60 (Greece, the production's own confirmed base). **Top ranked result:** the same — Greece wins on its own merits (a real, sourced 40% Greek cash rebate applied against FVD's real classified budget lines), not because it was assumed to. The engine was free to rank any candidate first; three others were priced and none beat it.

## MFNI limitation — shown: YES

Every structure's `StructureCalculationResult.warnings` carries: *"Regional production-cost normalization is not yet applied to this comparison — figures use this production's own nominal budget amounts, not jurisdiction-adjusted local costs."* This is the same message `calculate_structure_impl`'s pre-existing (unused) `cost_benchmark=None` parameter already implied — the orchestrator did not add a new gap, it disclosed an existing one. It renders in the real UI, in the Analysis panel, directly under "Net production cost."

## Persistence — PASS

`ProductionStructure` + `StructureCalculationResult` rows are real, committed database records (not derived at request time) — the same tables `get_project_record`'s Analysis panel already read from before this phase. Repeat calls check `StructureCalculationResult.input_fingerprint` against the current `CanonicalProductionState.input_fingerprint` and return `EVALUATION_REUSED` without creating a second set. Verified live: a second `Begin Evaluation` click against unchanged inputs left the structure count at 4.

## Browser / UI proof — PASS

Full browser → network → backend → persistence → UI chain traced live, not simulated:

1. Navigated to `http://localhost:5173/company/library/6c6f1c13-2d49-4bbc-bafb-2a12efa93112` — button read **enabled** ("Begin Evaluation"), not the prior disabled state.
2. Clicked it for real. `POST /api/v1/projects/.../evaluation/begin` fired (confirmed in backend logs, `200 OK`).
3. Page reloaded the record; Analysis panel updated live to: Evaluation **In progress**, Structures generated **4**, Leading structure **"Greece — production's current base"**, Net production cost **$3,627,136**, and the MFNI limitation sentence.
4. Full page reload (`navigate` with `force: true`) — identical values rendered from the database, confirming persistence survives refresh.
5. Zero console errors throughout.

## Little Utopia contamination — NO

`grep` across every new/changed runtime file (`project_evaluation.py`, `evaluation.py`, `structures.py`) for Little Utopia project IDs, Mauritius defaults, or `MU_PRODUCTION_TYPE` returns no matches. A focused regression test (`test_project_evaluation_module_contains_no_project_specific_code`) locks this in by scanning the module source for hardcoded jurisdiction-code branches. Mauritius does appear once in FVD's own **result data** — as one of four genuinely-discovered, genuinely-priced candidates, on equal footing with Greece/Malta/New York — which is the opposite of contamination.

## Genericity — YES

No project is named anywhere in `project_evaluation.py`, `evaluation.py`, or the `structures.py` refactor. The Malta-derived test above proves the exact same code path with different input evidence produces a different, correct result. `Begin Evaluation` will work for Lips Like Sugar, The System, Underwater, or any future project without a source change, provided each has a parsed screenplay and a parsed budget (the same `READY_FOR_OPTIMIZER` gate FVD passed) — not run in this task, per its own scope.

## Script-only behavior — verified, not re-tested end-to-end

Per this task's own instruction not to repeat Test 5/6's full ingestion run, `test_begin_evaluation_reports_budget_required_when_no_budget` confirms directly at the orchestrator level: a script-only project with no budget returns `BUDGET_REQUIRED_FOR_CURRENT_EVALUATION` with the real blocker text, creates zero `ProductionStructure` rows, and never crashes or fabricates a figure.

## Tests

Four new focused tests in `tests/test_project_evaluation.py`:

1. `test_begin_evaluation_reports_budget_required_when_no_budget`
2. `test_begin_evaluation_derives_home_jurisdiction_from_budget_filename_and_prices_it`
3. `test_begin_evaluation_is_idempotent_on_repeat_calls`
4. `test_project_evaluation_module_contains_no_project_specific_code`

Because `app/api/v1/structures.py` and `app/api/v1/projects.py` are shared core services, the full backend suite was also run: **4090 passed, 1 skipped, 1 pre-existing unrelated failure** (`test_global_discovery.py`'s `Workspace.jsx` scenario-title-formatter content check — a frontend file untouched by this phase, confirmed via `git status` and present before this phase's changes).

## Gate

**`FVD_EVALUATION_RUNTIME_ACCEPTED`**
