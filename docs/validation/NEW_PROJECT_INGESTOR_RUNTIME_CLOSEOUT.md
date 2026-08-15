# New Project Ingestor — Runtime Closeout

Date: 2026-08-14
Branch: `claude/audit-frametax-features-NZcX5`
Companion: none — this phase produces exactly one artifact.

## The defect

The New Project/Import Material product flow (folder discovery → classification → `POST /candidates/{id}/commit`) already created canonical `Document`/`DocumentVersion` records for every material category. But `_commit_candidate_impl` (`app/api/v1/ingestion.py`) has a documented, intentional contract: it never touches facts, requirements, or optimizer state. Nothing downstream of it ever turned a committed budget or screenplay `DocumentVersion` into a parsed `BudgetDocument`/`BudgetLineItem` row or an SA-1 script breakdown — for any project, automatically.

F#K Valentine's Day's Project Record showed a fully reconciled $4,517,687 budget and a 99-scene script breakdown only because prior sessions ran ad-hoc scratch scripts (`ingest_fvd.py`, `dump_fvd_budget.py`, etc.) directly against the database. That is the exact anti-pattern this phase's own SA-1.5 closeout forbade going forward: project-specific orchestration standing in for the real product mechanism. Every other project in the 52-item Library — including any project a user creates today through the actual UI — got neither.

## The fix

Two changes, both generic — no project ever named in code, only in prose explaining what is deliberately *not* special-cased.

**1. `app/services/material_routing.py` (new).** `route_committed_material(session, project_id, category, document_version_id)` — for `category == "budget"`, reuses the existing `budget_parser.parse_budget_csv` / `parse_budget_from_text` → `classify_parsed_items` pipeline (the same one `POST /projects/{id}/budgets/import` already uses) to create a `BudgetDocument` + `BudgetLineItem` rows via the already-existing-but-previously-unwired `document_version_id` bridge FK, and sets `Project.total_budget_usd` from the parser's own declared total — never a leaf-line sum, per the SA-1.5 corpus's own finding that declared totals reconcile exactly where leaf sums under-cover. For `category == "screenplay"`, it calls the existing `analyze_project_script` — `resolve_active_screenplay`'s already-built fallback bootstraps the `ScreenplayDocument` from the current screenplay `DocumentVersion` on its own; routing only needed to be the trigger nothing was previously calling. Every other category (deck, schedule, artwork, ...) is a deliberate no-op: the generic commit already fully serves them.

**2. `app/api/v1/ingestion.py::commit_candidate`.** The thin route handler now calls `_commit_candidate_impl` unchanged, then — only after a successful commit, only when a `document_version_id` exists — calls `route_committed_material`. `_commit_candidate_impl`'s own contract is untouched; routing is a separate step layered after it, exactly as the architecture note in its docstring anticipates.

**3. `app/api/v1/projects.py::get_project_record`** (read-time fallback, not a mutation). Projects whose `BudgetDocument` predates this fix — F#K Valentine's Day's, specifically — never got `Project.total_budget_usd` set and never got `document_version_id` backfilled. Rather than a database edit or a re-import, `get_project_record` now falls back to the most recent `BudgetDocument.total_budget_raw` for the project when the column itself is `None`. Verified this never writes to the row: `project.total_budget_usd` stays `None` in the database after the read (see `test_project_record_falls_back_to_budget_document_total_when_unset`).

## Test 1–4: F#K Valentine's Day, real browser, existing Project Record page

Navigated to `http://localhost:5173/company/library/6c6f1c13-2d49-4bbc-bafb-2a12efa93112` (no new page — the existing `ProjectRecord.jsx` at the existing `/company/library/:projectId` route).

| Check | Before | After | Evidence |
|---|---|---|---|
| Budget total | `BUDGET —` | **`BUDGET $4,517,687`** | Screenshot; `GET /api/v1/projects/.../record` → `total_budget_usd: 4517687.00`, confirmed distinct from Little Utopia's $4,364,393 |
| Budget provenance | n/a | `V-BRAT_V8_Greece_041224 TOPSHEET.pdf` still shown in Materials | Screenshot |
| Script breakdown | present from a prior manual parse | still present, now reachable via the same generic Facts tab with no new UI | 20 `ProjectFact` rows (scene counts, character burden, explicit-element flags, etc.), unchanged from SA-1.5 |
| Supporting materials | Artwork/Deck preserved | unchanged | Materials panel: Artwork, Budget, Deck, Screenplay all present, Schedule correctly "Not held" |
| Geography (Greece) | shown only if genuinely derived | **N/A — no "project geography" field exists in the UI at all.** 54 real scripted locations (including Temples of Apollo, Mediterranean Sea Shore/Clifftop Village) are visible on the Locations tab as genuine script evidence, but there is no dedicated geography display to assert against. Reported as an honest capability gap, not built (out of this phase's "fix wiring defects only" scope) | Locations tab content |

`Begin Evaluation` stays disabled with its existing tooltip ("Little Utopia only") — a pre-existing, intentional, already-documented limitation confirmed correct, not a routing defect.

## Test 5–6: script-only project, real "+ New Project" UI, zero project-specific code

Used the actual New Project modal → **Local Folder** → pointed at a scratch folder containing only `sa1_sample_screenplay.txt` (the existing SA-1 fixture, copied alone into an isolated directory — no budget file present).

1. Discover found 1 file, classified `screenplay` (high confidence) — the same classifier every project uses.
2. **Create Project & Continue** committed successfully: `sa1_sample_screenplay.txt` → category `screenplay` → status `Committed`. No failure.
3. Opened the resulting Project Record (the same generic page, no new code): `BUDGET —` (correctly reported missing — never a fabricated figure, never treated as a failure), Script Analyzer already ran automatically, and **Known production information → Locations already showed COASTAL HIGHWAY, HARBOUR, ROADSIDE DINER, TRUCK CAB** — live proof the new commit-time routing triggered the SA-1 pipeline for a project that has nothing to do with F#K Valentine's Day or Little Utopia.
4. Facts tab: 20 real `ProjectFact` rows, deterministically parsed from the fixture text — `script_total_scenes = 5`, `script_speaking_character_count = 3`, `script_unique_scripted_locations = 4`, matching the fixture's actual structure exactly.
5. Confirmed via direct API: `GET /record` → `total_budget_usd: None` — genuinely missing, not `0`, not fabricated.
6. `grep` across `material_routing.py`, the changed `ingestion.py`/`projects.py` sections: no project name, no per-project function, no per-project branch. The one automated regression test for this (`test_material_routing_module_contains_no_project_specific_code`) asserts the same at the source level.

The test project and its scratch fixture folder were removed after verification via the app's own **Delete Project** control (task-built in an earlier phase) — not a database edit — to keep the Library at its real 52 productions.

## Fix policy — what was and wasn't touched

- `_commit_candidate_impl`'s documented "never touches facts/optimizer state" contract: **preserved**. Routing is a separate call, made only by the thin route handler, only after commit succeeds.
- No new page, no navigation redesign: **confirmed**. `ProjectRecord.jsx` and its route were unchanged; the disabled `Begin Evaluation` state for non-served projects was confirmed correct, not fixed.
- No project-specific code path: **confirmed** by grep and by the regression test, across both the new module and the two changed files.
- No manual database edits, no re-import of FVD's corpus: **confirmed**. FVD's existing `BudgetDocument`/`ProjectFact` rows were left exactly as SA-1.5 reconciled them; only a read-time fallback was added.
- SA-2, MFNI, budget estimation, another Company Library audit, another worldwide-optimizer validation, another corpus reconciliation: **not started**, per the prompt's explicit stop condition.

## Test policy — what was added

One new file, `tests/test_material_routing.py`, six focused tests, all against the real Postgres dev DB with the same disposable-project isolation pattern as `test_ingestion_api.py`:

1. `test_budget_commit_routes_to_budget_document_and_sets_project_total`
2. `test_budget_commit_is_idempotent_on_recommit`
3. `test_screenplay_commit_triggers_sa1_pipeline_and_persists_facts`
4. `test_deck_commit_has_no_processor_and_is_a_no_op`
5. `test_project_record_falls_back_to_budget_document_total_when_unset`
6. `test_material_routing_module_contains_no_project_specific_code`

```
tests/test_material_routing.py .......                                    [100%]
6 passed
```

## Verification

- **New tests**: 6/6 passed.
- **Full backend suite**: `4086 passed, 1 skipped, 1 failed` — the one failure (`test_global_discovery.py::TestRecommendationTitles::test_scenarios_and_workspace_both_use_the_canonical_title_formatter`) is a pre-existing, unrelated frontend-content assertion about `Workspace.jsx`'s scenario-title formatter, present before this phase's changes and touching no file this phase modified. Confirmed via `git status` that no frontend file was touched in this phase.
- **Ingestion/Project Library/SA-1/SA-1.5 suites specifically**: `test_ingestion_api.py`, `test_ingestion_classifier.py`, `test_ingestion_phase_f.py`, `test_project_library_phase_b.py`, `test_project_library_phase_c.py`, `test_script_analyzer_sa1.py`, `test_real_production_corpus.py` — all green, no regressions from the two wiring changes.
- **Real browser, real backend, real Postgres** for both acceptance paths — no API-only simulation. Full browser → network (`/api/v1/ingestion/candidates/{id}/commit`, `/api/v1/projects/{id}/record`) → backend → persistence → UI chain traced and confirmed for both.

## Gate

**`NEW_PROJECT_INGESTOR_RUNTIME_ACCEPTED`**

Both acceptance paths (A: existing real production with full materials; B: script-only ingestion with no failure and honestly-missing budget) verified end-to-end through the real UI. No SA-2, MFNI, or budget-estimation work was started.
