# Final pre-Codex acceptance handoff (Claude, 2026-10-07)

- **Branch:** `claude/global-optimizer-remediation`.
- **Start:** `36844e6e9a110de7cb85df2a84bbb649e5a31351`.
- **Commit range for Codex to audit:** `611fb723daac05d5d91265172d334c61a37deb9f..CURRENT_HEAD` (the head is the commit that adds this file). It contains two commits:
  - `36844e6`: location-capability Codex remediation.
  - this closeout: the integration tests, this handoff, the ledger and the account handoff.

  The range base `611fb72` is the optimizer package / retention closure (see `OPTIMIZER_SCENARIO_UNIVERSE_ACCOUNTING_CLAUDE.md`). Its predecessors back to `dac1514` carry the scenario-accounting work recorded in that document.

No real production was evaluated, regenerated or edited in this closeout. The integration proofs ran only on the isolated database `frametax2_pytest`, with disposable projects that the test deletes. The test refuses to run against any other database.

## 1. Project-scoped location toggle: real integration proof

The test is `backend/tests/test_final_pre_codex_integration.py::test_project_scoped_location_toggle_real_integration`. It ran once and passed.

**Path exercised.** Requests are made with `httpx` against the real ASGI app, as the frontend does:

1. `POST /api/v1/cineglobe/projects/{id}/locations`;
2. persisted `ProjectLocationRequirement.override`;
3. `physical_requirement_fingerprint_facts` before/after;
4. the **real** `evaluate_project` (counted by a pass-through wrapper);
5. `build_production_and_structures` served fit.

**Fixture.** A disposable US-NM project with a $5M structured budget (ATL writer, BTL crew labor, general administration; no movable post/VFX/music, so evaluations are fast). It is evaluated once beforehand and then toggled.

| Case | Result |
|---|---|
| Unknown category `not_a_category` | HTTP 422, nothing persisted, 0 evaluations |
| HARD `desert_arid` ON | `changed`, `evaluation_triggered`, exactly **1** evaluation, row `override = true` |
| … where the census cell is verified SUPPORTED | every such jurisdiction is STRONG or WORKABLE, with no desert reason |
| … where it is verified NOT_SUPPORTED | WEAK, with `*_DESERT_ENVIRONMENTS_NOT_SUPPORTED` |
| … where it is AUTHORITY_UNRESOLVED_NEUTRAL | UNKNOWN (Conditional), with `*_DESERT_ENVIRONMENTS_NOT_ASSESSABLE` |
| Identical save (`desert_arid` ON again) | `changed = false`, `evaluation_triggered = false`, **0** evaluations |
| Fresh session (restart / reload) | `build_ui_location_categories` still reports `desert_arid` effective |
| HARD `desert_arid` OFF | 1 evaluation; no desert reason remains on any jurisdiction |
| SOFT `urban_major_city` ON, then OFF | 1 evaluation each; no WEAK fit and no urban reason (soft is disclosure-only) |
| Economics after every toggle | identical map economic_identity → (QPE, incentive, NPC) to the pre-toggle baseline |
| Second disposable project | no location rows, no evaluation, same current fingerprint, same generation count |

Fit, status and order may change. QPE, incentive, NPC and economic identity did not.

## 2. Parsed-budget persistence: non-reparse proof

The test is `…::test_parsed_budget_is_persisted_and_never_reparsed_by_state_or_evaluation`. It passed. Its first run failed on a fixture omission: the disposable project had no home jurisdiction, so evaluation returned `BLOCKED_INCOMPLETE_INPUTS`. I added the home jurisdiction and reran only that node.

**Fixture.** A disposable project with a real `Document` / `DocumentVersion` pointing at a 3-line CSV budget. The parser (`material_routing.parse_budget_csv`) is wrapped with a counter.

| Check | Result |
|---|---|
| First routing (`ensure_current_budget_routed`) | 1 parse; 1 `BudgetDocument` on the same `DocumentVersion`; 3 `BudgetLineItem`; current `BUDGET_PARSER_VERSION` |
| 2 × `CanonicalProductionStateBuilder.build`, `evaluate_project` (COMPLETE) then `evaluate_project` (REUSED), `build_production_and_structures` | **0 parses** |
| BudgetDocument id, DocumentVersion id, row count, line ids, categories, amounts, checksum | identical before and after |
| DocumentVersion count | 1 (the unchanged upload is reused) |
| Parser-version drift (`parser_version = "0-stale"`), then state build, evaluation and view | **0 parses**; rows and checksum identical; the stale version is left as it is |

**Why reads never reparse.** Both readers call `ensure_current_budget_routed` only when **no** `BudgetDocument` exists for the project:

- `canonical_production_state.py:326`;
- `canonical_project_economics.py:584`, which additionally only when not `read_only`.

A persisted parse is therefore never reparsed by state or evaluation, whatever its parser version.

**Documented exception (current behaviour; pinned by the test, not endorsed).** `material_routing._route_budget`, reached through `route_committed_material` (committed-material routing) or a direct `ensure_current_budget_routed` call, refreshes a BudgetDocument whose `parser_version` is stale **in place**. It keeps the same BudgetDocument and DocumentVersion, but replaces the line items and parser version.

- **Classification:** an **INGESTION_ACCEPTANCE_REQUIRED** product decision; I did not change it here.
- **Preferred future rule:** reparse only on an explicit user-authorized action or a new document version, and preserve the prior parse as an audit trail instead of replacing it silently.

## 3. Current generation / served snapshot (read-only; no regeneration)

The four persisted `canonical-1.105.0` generations, read via SQL and the served state:

| Project | 1.105.0 generations | Generated = persisted + aggregated | Curated + music-suppressed = pre-curation | Duplicate identities | Single-jurisdiction rows (unique) | Winners | Identities shared with accepted 1.104.0 / economic diffs |
|---|---:|---|---|---:|---|---:|---|
| Little Utopia | 1 | 223,058 = 977 + 222,081 | 557 + 0 = 557 | 0 | 217 (217) | 92 | 649 / 0 |
| F#K Valentine's Day | 1 | 1,215,900 = 2,108 + 1,213,792 | 646 + 498 = 1,144 | 0 | 217 (217) | 91 | 972 / 0 |
| Bad Hombres | 1 | 11,851 = 1,126 + 10,725 | 275 + 345 = 620 | 0 | 217 (217) | 91 | 577 / 0 |
| Lips Like Sugar | 1 | 1,298,334 = 2,094 + 1,296,240 | 680 + 442 = 1,122 | 0 | 217 (217) | 92 | 1,007 / 0 |

**Economic diffs.** The compared fields are verified NPC, adjusted NPC, total incentive, confirmed floor and maximum, by economic identity, served at 1.104.0 (the accepted pre-package state) and now.

**Location remediation (`36844e6`).** The served economics hash was identical before and after for all four projects; that commit changed only fit, status and evidence. The only served fit change is in Lips Like Sugar's hard-desert requirement: Single-Jurisdiction conditional 51 → 49 and reference 25 → 27, and fit-confirmed scenarios 227 → 325.

**Workspace and API agreement.** The Workspace headers (LU 557, FVD 646, BH 275, LLS 680 executable options; winners 92 / 91 / 91 / 92) were checked in the browser in the two preceding passes against these same generations. No optimizer test family was rerun here.

## 4. Ledger: every remaining item classified

| Item | Classification | Evidence / note |
|---|---|---|
| Optimizer scenario generation, accounting, retention equivalence, music / post-VFX package policy | **READY_FOR_CODEX_ACCEPTANCE** | `OPTIMIZER_SCENARIO_UNIVERSE_ACCOUNTING_CLAUDE.md` (1.104.0 + 1.105.0 residual closure) |
| Location controls and capability wiring (13 controls → persistence → fingerprint → evaluation → fit → served → Workspace / Globe / hover / Inspector) | **READY_FOR_CODEX_ACCEPTANCE** | §1 above; `CLAUDE_LOCATION_CAPABILITY_CODEX_REMEDIATION.md` |
| Location-capability census evidence (826 supported / 90 not supported) | **READY_FOR_CODEX_ACCEPTANCE** | same remediation document; trail JSON |
| 224 AUTHORITY_UNRESOLVED_NEUTRAL capability cells | **TERMINAL_NEUTRAL** | bounded official-source sequence completed and recorded; runtime-neutral |
| Explicit parsed-budget reparse / version policy | **INGESTION_ACCEPTANCE_REQUIRED** | §2 exception |
| New-project ingestion acceptance | **INGESTION_ACCEPTANCE_REQUIRED** | not exercised in this phase |
| Company Globe | **COMPANY_GLOBE_REQUIRED** | not started |
| Build Your Own | **DEFERRED_PRODUCT_WORK** | suppressed references are preserved for it |
| Final Globe categories / colours / atmosphere | **DEFERRED_PRODUCT_WORK** | not started |
| Real executable official co-production browser example | **DEFERRED_PRODUCT_WORK**: no real production reaches a priced official co-production | all four projects serve co-productions only as opportunities needing facts (25 / 27 / 25 / 25); executable co-production is covered by fixtures only |
| Same-destination music + post/VFX as a priced structure | READY_FOR_CODEX_ACCEPTANCE | closed at 1.105.0 (package unit) |

All UI work is `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION`. The browser evidence in these documents comes from the implementing agent's local browser and is not independent acceptance.

## 5. Tests run in this closeout

`backend/tests/test_final_pre_codex_integration.py`: 2 tests on `frametax2_pytest`.

- The location-toggle test passed on its first run.
- The budget test passed after the one fixture correction above; only the failed node was rerun.

No other family was rerun.
