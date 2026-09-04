# CineGlobe — Script Analyzer existing-engine forensic audit

Date: 2026-09-03. Scope: repository/history archaeology, read-only database and API probes. No implementation, external research, ingestion, re-analysis of stored scripts, or broad tests. The sole new file is this report.

## Identity and evidence gate

| Identity | Evidence |
|---|---|
| Expected repository | `surajgohill-oss/Frametax` |
| Actual origin | `https://github.com/surajgohill-oss/Frametax.git` |
| Git root | `/Users/Suraj/cineglobe-frametax` |
| Application root | `/Users/Suraj/cineglobe-frametax/frametax2` — not the sibling event/ticketing application at root `backend/` |
| Branch | `claude/audit-frametax-features-NZcX5` |
| HEAD inspected | `e42e28d7af7dd6af00d3f7518215e14f36b720b2` |
| Working tree | Dirty on arrival; existing frontend edits and unrelated untracked files preserved. Backend analysis below is against HEAD; frontend inspection includes the existing uncommitted overlay. |
| Runtime identity | Current checkout imported in-process through mounted FastAPI routes, against local PostgreSQL with `SET TRANSACTION READ ONLY`, followed by rollback. No deployed-server/browser claim. |

Requested command results: `git branch --show-current` and `git rev-parse HEAD` are the branch/SHA above. `git status --short` on arrival, relative to the application directory:

```text
 M frontend/src/components/IncentiveIntelligence.jsx
 M frontend/src/lib/productionOptions.js
 M frontend/src/screens/production/Overview.jsx
 M frontend/src/screens/production/Workspace.jsx
 M frontend/src/styles/screens.css
 M frontend/src/styles/shell.css
RM frontend/tests/overview-top-four.test.mjs -> frontend/tests/overview-anchor-scenarios.test.mjs
?? ../.claude/
?? ../evaluate_19.py
?? backend/fvd_budget.txt
?? backend/scripts/dump_fvd_budget.py
?? backend/scripts/find_fvd_budget.py
?? backend/scripts/ingest_fvd.py
?? backend/scripts/ingest_fvd_v2.py
?? backend/scripts/inspect_budget.py
?? backend/scripts/test_parse_fvd_budget.py
?? ../generate_actual_mfni.py
?? ../generate_delta.py
?? ../generate_intelligence_review.py
?? ../generate_mfni.py
```

### Status convention

- **ACTIVE + SERVED**: implementation reaches a mounted API or current production consumer. Does not imply a dedicated editor, browser verification, or professional accuracy.
- **IMPLEMENTED BUT NOT SERVED**: executable or persisted capability exists, but the relevant generic product consumer does not receive it.
- **PARTIAL**: a meaningful subset exists; the professional function is incomplete.
- **DORMANT**: retained legacy/demo/helper implementation, not the canonical generic analyzer path.
- **ABSENT**: no implementation found in current tracked application code or reachable Git history searched; documentation, enum names and empty fields do not count.
- **UNKNOWN**: insufficient evidence to establish the behavior.
- Evidence suffixes: **S** = STATIC VERIFIED; **R** = RUNTIME VERIFIED in this audit; **H** = historical implementation/artifact evidence, not a current-runtime claim; **N** = negative repository/history search.

### Bounded findings

| Finding | Conclusion | Evidence |
|---|---|---|
| Preserve SA-1/SA-1.5 | Real document-linked structural parser, persistence, facts, requirements, API and optimizer connections exist. Do not rebuild them. | E01–E15; R1–R3 |
| Professional breakdown | Current parser emits a 12-key deterministic taxonomy. It does not quantify production work or interpret the full breakdown taxonomy. | E05/E06; R1 |
| SA-2 | Architecture and reserved Bridge operation exist; no implemented ScriptAnalysisPackage/Response, material interpretation/confirmation workflow, or second-model scene analysis found. | E24; H3; N1 |
| Scheduling | No film schedule/stripboard/ShootDay engine found. `schedule` documents, constraint enums and default crew days are not one. | E20/E21/E22/E28; N1 |
| Immediate extension risks | Eighths are not page-geometric; cue false positives; draft selector/consumer scoping; generic UI and cultural taxonomy disconnects; no scene/element correction workflow. | R2–R4; defects D1–D9 below |
| Existing cost engineering | Generic component routing and travel/FX/local-cost normalization were reconnected at `380ecd9`; these are existing-budget geography/routing calculations, not screenplay-driven estimates. | E12/E22; H8 |

## Evidence register

Each matrix references these exact files/functions. Shared references avoid repeating long paths in every row.

| ID | Canonical implementation evidence |
|---|---|
| E01 | [library_document.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/models/library_document.py): `Document`, `DocumentVersion`, `DocumentVersionSource`; checksum, current-version pointer, sources, nullable supersession. |
| E02 | [ingestion.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/api/v1/ingestion.py:288): `commit_candidate`, `_commit_candidate_impl`; review/categorization, checksum dedup, durable copy, document/version creation, post-commit routing. [ingestion_classifier.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/ingestion_classifier.py): `classify_document`. |
| E03 | [material_routing.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/material_routing.py:197): `_route_screenplay`, `route_committed_material`; calls existing analyzer, no second parse. |
| E04 | [pdf_extractor.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/ingestion/pdf_extractor.py): `extract_text_from_pdf`/`extract_text_from_bytes`; PyMuPDF page text, then `"\n\n".join(pages)`; no OCR, geometry retention or FDX XML parsing. |
| E05 | [screenplay_structural_parser.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/ingestion/screenplay_structural_parser.py): `parse_structure`, `_HEADING_RE`, `_is_character_cue`, `_build_page_index`, `_find_terms`, `_PERIOD_RE`, `SA1_TAXONOMY`; version `sa1-structural-1.1.0`. |
| E06 | [script_analysis_service.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/script_analysis_service.py): `resolve_active_screenplay` (86), `ensure_screenplay_projection` (156), `parse_and_persist` (205), `derive_core_facts` (335), `persist_derived_facts` (385), `build_requirements` (507), `analyze_project_script` (607). |
| E07 | [screenplay.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/models/screenplay.py): `ScreenplayDocument`, `Scene`, `Character`, `ExtractedScriptElement`, legacy `ScreenplayChunk`; scene offsets/hash and element evidence fields. |
| E08 | [production_requirement.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/models/production_requirement.py): `ProductionRequirement`, `ProductionAssumption`; [project_location_requirement.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/models/project_location_requirement.py): `ProjectLocationRequirement`. Schema installed by [0067_script_analyzer_sa1.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/alembic/versions/0067_script_analyzer_sa1.py). |
| E09 | [canonical_production_state.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/canonical_production_state.py): `CanonicalProductionStateBuilder`, `_apply_script`, `_apply_requirements`, `_apply_assumptions`, `compute_fingerprint`; state version `sa1-canonical-production-state-1.0.0`. |
| E10 | [optimizer_handoff.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/optimizer_handoff.py): `build_optimizer_input`, `ProductionOptimizerInput`; contract `sa1-1.0.0`. Retained contract API, not the live evaluator's orchestration owner. |
| E11 | [script_analysis.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/api/v1/script_analysis.py): `parse_project_script`, `get_project_script`, `get_canonical_state`, `get_optimizer_input`; mounted in [main.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/main.py:43). |
| E12 | [canonical_evaluation.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/canonical_evaluation.py): `evaluate_project`, `_compute_fingerprint`, `_relocation_normalization`, `_price_component_relocation_candidate`; [evaluation.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/api/v1/evaluation.py) is the canonical evaluation API wrapper. |
| E13 | [canonical_project_economics.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/canonical_project_economics.py:659): `build_physical_requirements`, `_location_categories_from_descriptions`, `build_ui_location_categories`; reads persisted script requirements directly. |
| E14 | [production_requirements.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/production_requirements.py): `abstract_location`, `derive_production_requirements`, `match_capability`, shared 13-category `LOCATION_TAXONOMY`; [production_discovery.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/production_discovery.py): `discover_executable_jurisdictions`. |
| E15 | [canonical_role_qualification_bridge.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/canonical_role_qualification_bridge.py:285): `_SCRIPT_ELEMENT_TYPES_BY_CATEGORY`, `script_facts_from_project`, `evaluate_point_table_qualification`, `evaluate_role_qualification`; role/nationality sources use real `ProjectPerson`/`TalentProfile`. |
| E16 | [project_workspace_view.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/project_workspace_view.py:208): script summary; [workspace.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/api/v1/workspace.py): mounted GET; [ProjectWorkspace.jsx](/Users/Suraj/cineglobe-frametax/frametax2/frontend/src/screens/project/ProjectWorkspace.jsx:154): `ScriptTab`; [App.jsx](/Users/Suraj/cineglobe-frametax/frametax2/frontend/src/App.jsx:59) mounts `/projects/:projectId/summary`. |
| E17 | [canonical_production_view.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/canonical_production_view.py:1018): `build_generic_pkg_and_economics` sets `pkg.script.known=False`; requirements separately disclosed. [QualificationPanel.jsx](/Users/Suraj/cineglobe-frametax/frametax2/frontend/src/components/QualificationPanel.jsx:163) renders language/setting/countries from that package. |
| E18 | [ProductionDetails.jsx](/Users/Suraj/cineglobe-frametax/frametax2/frontend/src/components/ProductionDetails.jsx:121), [api.js](/Users/Suraj/cineglobe-frametax/frametax2/frontend/src/api.js:81), [cineglobe.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/api/v1/cineglobe.py:858): category edit calls singleton `POST /locations`, which resolves LU by title; generic people edits have a separate project-scoped endpoint. |
| E19 | [production_package_intelligence.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/production_package_intelligence.py:393): `SCRIPT_ATTRIBUTE_KEYS`, `build_script_intelligence`, `build_production_package`, `generate_missing_inputs`; supplied attributes only. Legacy [screenplay_parser.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/ingestion/screenplay_parser.py:63): coarse `parse_screenplay_text`, chunking. |
| E20 | [production_constraint_engine.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/production_constraint_engine.py): `ConstraintKind`, `check_candidate_against_constraints`; only jurisdiction-required and budget-ceiling have checkers. Other kinds return unverifiable. |
| E21 | [production_scenario_engine.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/production_scenario_engine.py): `run_scenario`; `SHIFT_SCHEDULE` only filters existing structuring opportunities. [creative_qualification_engine.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/creative_qualification_engine.py:200): `analyze_creative_qualification_paths`, minimal unmet-criteria combinations, not screenplay rewrites. |
| E22 | [production_adjustment.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/production_adjustment.py:88): `CrewManifest`, `ProductionBudgetParams`, `calculate_production_adjustment`; [production_normalization.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/production_normalization.py:488): `compute_local_cost_normalization`; [travel_model.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/travel_model.py): `estimate_travel_cost`. Budget/manifest/default based, not scene-scheduled. |
| E23 | [program_requirements.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/data/program_requirements.py), [cultural_point_tables.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/data/cultural_point_tables.py), [canonical_requirements_gate_bridge.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/canonical_requirements_gate_bridge.py), [canonical_treaty_bridge.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/calculators/canonical_treaty_bridge.py): existing program requirements/qualification/treaty layer; not content extraction. |
| E24 | [bridge/schema.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/bridge/schema.py:39): `SCRIPT_PRODUCTION_ANALYSIS` is in `RESERVED_FUTURE_OPERATIONS`; manual package/provider/reconciliation infrastructure exists, but no script-specific schema/workflow. |
| E25 | [test_script_analyzer_sa1.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/tests/test_script_analyzer_sa1.py), [test_script_analyzer_location_normalization.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/tests/test_script_analyzer_location_normalization.py), [test_evaluate_triggers_script_ingestion.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/tests/test_evaluate_triggers_script_ingestion.py), [test_fvd_canonical_input_assembly_repair.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/tests/test_fvd_canonical_input_assembly_repair.py): regression protection, not proof of UI execution. |
| E26 | [real_production_corpus.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/validation/real_production_corpus.py), [holdout_guard.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/validation/holdout_guard.py): explicit script-side versus actual-side fixture separation; `PredictionSession` guard exists; not a prediction engine. |
| E27 | E06 `derive_title_page_credits`/`persist_title_page_credits`; [talent_nationality_resolution.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/talent_nationality_resolution.py): actual-person metadata enrichment called by analyzer, not character nationality inference. No enrichment call was made by this audit. |
| E28 | [models/ingestion.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/models/ingestion.py): `IngestionJob` schema; no analyzer queue consumer found. [models/cost.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/models/cost.py): cost/fringe schemas, not Schedule/ShootDay. |
| E29 | [script_parse_status.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/services/script_parse_status.py): parse statuses; `SCRIPT_PARSE_STALE_NEW_VERSION` is defined but has no assignment consumer in application code. |
| E30 | [cineglobe.py](/Users/Suraj/cineglobe-frametax/frametax2/backend/app/api/v1/cineglobe.py:1237): project state GET now calls FX refresh and `evaluate_project`; intentionally NOT executed by this audit because it can write/reprice/enrich. |

## History: approval, implementation and connection are separate

| ID / checkpoint | Actual implementation transition | Disposition now |
|---|---|---|
| H1 — `50c476f`, `fe5b8b8` (2026-07-09) | ProductionPackage translation/question engine, creative qualification path search, constraint checker and geography-shaped scenario functions built. Script attributes are caller-supplied/UNKNOWN, not extracted. | Retained helpers; package/scenario/constraint endpoints remain legacy LU-oriented. Not professional breakdown or scheduling. |
| H2 — `8f4e70b`, `04bb530` (2026-08-14) | Existing-capability reconciliation and canonical architecture define reuse, scene/evidence spine, schedule/cost phases and SA-2 manual Bridge. | Design evidence; not implementation proof. |
| H3 — `242226d` (2026-08-14) | SA-1 structural parser, scenes/characters/elements, requirement persistence, state/handoff and API. SA-1 closeout explicitly defers full taxonomy, AI/Bridge, scheduling, budget estimation and correction UX. | CURRENT ACTIVE core. No later implemented SA-2 package/schema found. |
| H4 — `fe59612`, `9d2fa9d`, `dd7ca86`, `df10621` (2026-08-14) | Library projection/extraction, real FVD acceptance work, held-out corpus/guard, material-routing trigger. | Preserve SA-1.5. Historical GO document exists; contemporaneous Codex verification also records handoff/UI issues. Neither is treated as automatic current truth. |
| H5 — `87440df`, `ccb24eb`, `034c8de`, `3665c52` (2026-08-14–17) | Generic evaluation/workspace, real requirements consumption, then canonical evaluator cutover. | `project_evaluation.py` retained but superseded. Live evaluator directly reads shared script tables rather than consuming the old `ProductionOptimizerInput` adapter. |
| H6 — `5935225`, `8ccf30a` (2026-08-19); `d2106b2` (2026-08-23) | Role/cultural fact consumption; Evaluate retroactively triggers SA-1 for existing documents. | CURRENT ACTIVE, with taxonomy/version gaps below. |
| H7 — `3855071`, `325274e`, `e811d18`, `87a8bb9` (2026-08-29–30) | Title credits, person nationality enrichment, SAME/clock-time location normalization, location-category UI exposure, ontology recovery. | CURRENT ACTIVE SA-1 extensions; no full interpreted taxonomy. |
| H8 — `380ecd9` (2026-09-02), through current HEAD | Generic component-target enumeration expanded; co-pro discovery and existing relocation normalization reconnected. | CURRENT ACTIVE economic capabilities. Do not repeat yesterday's claim that generic travel/local-cost normalization is absent. They do not read a screenplay schedule. |

**N1 search boundary:** current tracked code, `git log --all` commit messages and changed paths, and content-change searches across all reachable branches for `stripboard`, `ShootDay`, `Schedule`, schedule generation/optimization, cast availability, turnaround/meal constraints, `ScriptAnalysisPackage`, `ScriptAnalysisResponse`, and material-analysis vocabulary. No film scheduling implementation or SA-2 package implementation found. Root `backend/app/scheduler.py` schedules event/marketplace polling (`TrackedEvent`, `Listing`, `PollRun`), not film work. Unknown/unreachable commits or external workspaces are not claimed searched.

## Active chain and failure boundaries

```text
Company Library / Project Record
  -> discover + category/project review (IngestionCandidate)
  -> commit: Document -> DocumentVersion -> durable file + source/checksum
  -> material_routing._route_screenplay
  -> resolve_active_screenplay / ensure_screenplay_projection
  -> text extraction (PDF text or raw text; no OCR/semantic FDX)
  -> parse_structure
  -> ScreenplayDocument + Scene + Character + ExtractedScriptElement
  -> script_* ProjectFacts + ProductionRequirement + ProjectLocationRequirement
       |
       +-> /script-analysis/.../script: scene/character summary
       +-> /projects/.../workspace -> ProjectWorkspace.ScriptTab: counts/locations
       +-> build_ui_location_categories -> Overview location chips
       +-> /script-analysis/.../state -> old CanonicalProductionState / handoff API
       +-> canonical_evaluation.evaluate_project (active economics owner)
             -> build_physical_requirements -> feasibility DISCLOSURE
             -> script_facts_from_project -> role/cultural qualification
             -> existing allocation/QPE/incentive/structure/ranking pipeline
```

| Stage | Canonical owner / persistence | Actual behavior and failure boundary |
|---|---|---|
| Source/project identity | E01/E02; Project → Document → DocumentVersion/Source | Checksum dedup and current flags exist. Ambiguous sibling draft is stored non-current instead of guessed current. This is correct uncertainty handling, not automatic revision promotion. |
| File routing | E02/E03 | Commit synchronously awaits analyzer. Evaluate also invokes it. No analyzer background worker was found. |
| Text extraction | E04/E06 | PDFs: up to 300 pages in this path, text only. Page strings joined without form-feed/geometry. TXT read directly. FDX extension read as XML text, not decoded as screenplay paragraphs. Missing file/extraction failure may collapse into scan-only status. |
| Parse/persistence | E05/E06/E07 | Text hash + parser version skip unchanged work. Forced/changed parse replaces this screenplay's scenes/characters/deterministic elements. Distinct screenplay rows preserve separate versions, but active-version selection is incomplete. |
| Facts/requirements | E06/E08 | 20 aggregate facts; grouped presence requirements and recurring locations. All derived quantities/unit fields remain null. ProjectFact USER_OVERRIDE survives derivation; scene/element approval does not have equivalent protection. |
| API | E11/E16 | Detailed script GET exposes selected scene and character fields, not all stored fields or an element-review API. State/handoff remains accessible but is not the live economics orchestrator. |
| UI | E16/E17/E18 | Summary Script tab shows scene/character counts and first 40 raw locations. Main production UI shows category chips; generic QualificationPanel receives empty `pkg.script`. No professional scene/element grid/editor exists. |
| Optimizer | E12/E13/E14 | Reads persisted requirements directly; physical feasibility is separate disclosure, not wholesale economic rejection. Budget-derived component routing, not screenplay-derived work packages. |
| Eligibility | E15/E23 | Existing deterministic tests/role/treaty bridges. Script category names are mismatched for story-setting consumption; missing facts remain progressive. |
| Jobs | E28/N1 | IngestionJob schema only; no parser worker or job progress mechanism. Synchronous calls can also trigger person enrichment in normal operation. |

## Current runtime evidence

| ID | Read-only observation | Verification boundary |
|---|---|---|
| R1 | FVD project `6c6f1c13-2d49-4bbc-bafb-2a12efa93112`; screenplay `02858959-0858-4d01-bd9c-ff65c1ff8d67`; current DocumentVersion `d25b035b-dc6f-471a-a611-6ed397444889`; parser `sa1-structural-1.1.0`; 99 scenes, 38 characters, 1,703 elements, 20 `script_*` facts, 127 production requirements, 54 normalized location requirements. | SQL READ ONLY and mounted script API GET 200. Existing persisted result, not an ingestion/re-analysis run. |
| R2 | `/script` returns 99/38; workspace GET returns same counts and 55 raw location strings; normalized location requirements are 54. Generic package builder simultaneously returns `script.known=false`, null filename and empty attributes. | Current-code API/consumer probes, not browser proof. The 55/54 split is raw-string versus normalized-key identity. |
| R3 | `/state` says `READY_FOR_OPTIMIZER`; `/optimizer-input` accepts with `base_jurisdiction=null`, `shoot_days=null`, `provisional=true`. Database has zero ProductionAssumption rows. | Retained handoff API behavior only; do not confuse this with current canonical economics readiness, which resolves its own project inputs. |
| R4 | Current FVD character row `A DOUBLE WEDDING`, speaking=true, 1 dialogue block / 23 words. Exact source context is action describing the altar/wedding, followed later by the actual cue `PRIEST`. | Concrete false positive, not a claim that all 38 characters are correct. |
| R5 | Pure parser probe: two form-feed-delimited pages with uneven text density produce scene `(page_start=1,page_end=1,eighths=16)` and `(2,2,1)`. `INT-EXT. CAR - DAY` parses as `INT`, location `EXT. CAR`; `INT./EXT.` works. Standalone MONTAGE produces no scene. | Focused in-memory execution of current parser; no files or DB writes. Not a broad test run. |
| R6 | Lips Like Sugar: current parser 1.1.0, 145 scenes / 37 characters / 1,577 elements / 150 requirements / 76 locations. LU: persisted `SCRIPT_PARSE_BLOCKED_SCAN_ONLY`, no scenes/elements. | SQL READ ONLY. LU's older manual/demo script signals are not evidence of a full canonical LU parse. |
| R7 | All 3,280 persisted elements from the two parsed scripts are `DETERMINISTIC_PARSE`; zero quantified elements, zero confidence values, all review_state null. All 277 requirements have null quantity; 72 require confirmation. | SQL READ ONLY. Presence/review markers are stored, but no completed breakdown-confirmation flow is demonstrated. |
| R8 | FVD emitted element types include `scripted_location`, `period_reference`, `character`, explicit vehicle/animal/weapon/minor. Cultural bridge expects `location`/`environment`, `language`, `cultural_reference`/`character_nationality`. | Direct read-only invocation of current query + inspection of consumer mapping. Existing SA-1 story locations do not match that vocabulary. |

## Matrix A — professional breakdown capability

Model abbreviations: **Sc** Scene; **Ch** Character; **El** ExtractedScriptElement; **PR** ProductionRequirement; **LR** ProjectLocationRequirement; **PF** ProjectFact; **PA** ProductionAssumption. “No model” means no dedicated representation/producer was found, not that arbitrary raw text could not mention it. For ABSENT rows E05/E07/E08 + N1 are the checked extraction/schema/history boundary.

### Scene structure

| Capability | Expected professional function | Existing CineGlobe implementation | Canonical file/module | Data model | Downstream consumer | Status | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| Scene number | Stable source production number | Sequential order plus optional printed number incl. suffix | E05 `parse_structure` | Sc.sequence/source_scene_number | Script API | ACTIVE + SERVED | S/R1 | Not stable cross-draft identity |
| Slugline | Preserve/normalize heading | Raw and uppercase/whitespace-normalized heading | E05 | Sc | Script API | ACTIVE + SERVED | S/R2 | Restricted heading grammar |
| INT / EXT / INT-EXT | Correct combined forms | Slash/I-E forms work; literal INT-EXT misclassifies | E05 `_HEADING_RE` | Sc.int_ext, El | API, PF/LR | PARTIAL | R5 | Add supported syntax to existing parser, not a replacement |
| Scripted location | Source setting per scene | Heading location + recurrence key | E05/E06 | Sc, LR, PR | API/UI/feasibility | ACTIVE + SERVED | R1/R2 | Aliases/subsets not a real location catalog |
| Story geography | Resolve country/city/region evidence | Literal location text, small keyword environment ontology | E13/E14 | Sc/LR | Feasibility; cultural mapping mismatched | PARTIAL | S/R8 | No structured geographic disambiguation |
| DAY / NIGHT / other time | Normalize and retain temporal context | DAY/NIGHT/DAWN/DUSK/CONTINUOUS/LATER/UNKNOWN; SAME→CONTINUOUS; clock stripped without guess | E05 | Sc.time_of_day | API/PF/LR | ACTIVE + SERVED | S/R2 | Literal clock value only remains in raw heading; no inherited clock/day state |
| Page start/end | Physical screenplay page bounds | Offset lookup from form-feeds or page markers | E05/E07 | Sc.page_start/page_end | Start in API; end stored only | PARTIAL | S/R5 | PDF extraction discards explicit page boundaries; no page_end API field |
| Page count | Real page extent | Marker count or words//200 estimate | E04/E05 | ScreenplayDocument.page_count/page_basis | API/state | PARTIAL | R1 | Marker heuristics and approximation, not guaranteed physical page count |
| Eighths | Scene length on actual page layout | Character-span / global average characters per page, rounded min 1 | E05 `parse_structure` | Sc.eighths, total_eighths | API/Ch/LR aggregates | PARTIAL | R5 | Even LAYOUT mode is density estimate; no geometric eighths |
| Scene synopsis | Reviewed scene summary | No synopsis field/producer | E05/E07 | No model | None | ABSENT | N1 | Full function missing |
| Chronology | Narrative timeline vs script order | Script sequence only | E05/E07 | Sc.sequence | API | PARTIAL | S | No story-day/date/order model |
| Flashback/flash-forward | Temporal segment/relationship | FLASHBACK excluded from character cues only | E05 `_NOT_A_CHARACTER` | No temporal relation | None | ABSENT | S/N1 | Cue rejection is not flashback parsing |
| Continuous/intercut/montage/series-of-shots | Parent/child sequences and continuity | CONTINUOUS/SAME token; transition words excluded from cues | E05 | Sc time token only | API | PARTIAL | R5 | No intercut/montage/series structure or continuity propagation |
| Scene relationships | Links, dependencies, continuity | Sequence; Ch/LR scene-sequence arrays | E07/E08 | Denormalized arrays | Aggregates | PARTIAL | S | No typed scene relationship graph |

### Cast / performers

| Capability | Expected professional function | Existing CineGlobe implementation | Canonical file/module | Data model | Downstream consumer | Status | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| Characters | All appearing fictional characters | Dialogue-cue names only | E05/E06 | Ch + CHARACTER El/PR | API/state | PARTIAL | R1/R4 | Non-speaking appearances missed; action capitals can be false positives |
| Speaking characters | Identify genuine dialogue roles | Cue-followed-by-text heuristic, counts words/blocks | E05 | Ch + DIALOGUE_ROLE El | Script API | PARTIAL | R4 | No reliable action/dialogue separation or review |
| Principal cast | Assign production role tier | Top-10 dialogue burden; no principal classification | E06 `derive_core_facts` | PF top burden | State | PARTIAL | S | Burden is not a casting tier |
| Supporting | Supporting-role classification | Real ProjectPerson cast bucket exists, not Ch classification | E15/E27 | ProjectPerson, separate Ch | Personnel qualification | PARTIAL | S | No character→cast/tier link |
| Day players | Classify workday roles | Not generated | E05/E07 | No model | None | ABSENT | N1 | Tier/workday assignment |
| Background | Scene crowd roles/counts | Not generated | E05 | No model | None | ABSENT | N1 | Presence/count/action extraction |
| Featured background | Distinguish featured extras | Not generated | E05 | No model | None | ABSENT | N1 | Classification/quantities |
| Stand-ins | Stand-in needs and days | Not generated | E05 | No model | None | ABSENT | N1 | Cast-linked requirements |
| Doubles | Photo/body doubles | Not generated | E05 | No model | None | ABSENT | N1 | Role/type/scene linkage |
| Stunt doubles | Stunt performer assignments | Not generated | E05 | No model | None | ABSENT | N1 | Stunt/performer linkage |
| Minors | Identify under-age performers and restrictions | Literal child/kid/baby/teen etc. hits | E05 lexicon/E06 | EXPLICIT_MINOR El/PR/PF | Requirement disclosure | PARTIAL | R7 | Not age, actor identity, count, work limits or confirmed appearance |
| Specialty performers | Skills and staffing | Not generated | E05 | No model | None | ABSENT | N1 | Skills/counts/days |
| Cast scene count | All appearance counts | Speaking-scene count | E05/E06 | Ch.scene_sequences/scene_count | API | PARTIAL | R1/R4 | Silent appearances and false cues |
| Cast page count | Workload pages per performer | Sum of whole speaking-scene estimated eighths | E06 | Ch.eighths_burden | API | PARTIAL | R5 | Not actual appearance-page count or workdays |
| Cast/location relationships | Appearance graph | Ch scene sequences can join Sc.location_key | E07 | Arrays + Sc | No dedicated relationship view | IMPLEMENTED BUT NOT SERVED | S | No typed join model, schedule or cast-location API |

### Production elements

| Capability | Expected professional function | Existing CineGlobe implementation | Canonical file/module | Data model | Downstream consumer | Status | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| Props | Identify specific required objects | Narrow phrases only: hero prop/picture vehicle/practical/prop gun/prop knife | E05 `_PROP_HERO_TERMS` | EXPLICIT_PROP El/PR | Requirement disclosure | PARTIAL | S/R7 | No general prop extraction or count; literal 'practical' is noisy |
| Hero props | Story-critical prop identity | Literal phrase hit only | E05 | Generic EXPLICIT_PROP | Requirement disclosure | PARTIAL | S | No hero significance or continuity |
| Wardrobe | Costume changes/looks | Not generated | E05 | No model | None | ABSENT | N1 | Looks, multiples, cast/scene continuity |
| Specialty wardrobe | Period/wet/fire/stunt costumes | Not generated | E05 | No model | None | ABSENT | N1 | Requirements and safety classification |
| Hair | Character looks and work | Not generated | E05 | No model | None | ABSENT | N1 | Looks/days |
| Makeup | Character looks/work | Not generated | E05 | No model | None | ABSENT | N1 | Looks/days |
| Prosthetics | Special makeup appliances | Not generated | E05 | No model | None | ABSENT | N1 | Builds/applications/continuity |
| Vehicles | Scene vehicle presence | Literal vehicle term per scene | E05 `_VEHICLE_TERMS` | EXPLICIT_VEHICLE El/PR | Requirement disclosure | PARTIAL | R7 | No count, hero/background split, safety or duration |
| Picture vehicles | Production-use vehicle identification | Literal 'picture vehicle' recorded as prop | E05 | EXPLICIT_PROP | Requirement disclosure | PARTIAL | S | Wrong granularity for vehicle planning |
| Animals | Scene animal presence | Literal animal term per scene | E05 `_ANIMAL_TERMS` | EXPLICIT_ANIMAL El/PR/PF | Requirement disclosure | PARTIAL | R7 | No trained/live/CG choice, handler, counts or days |
| Weapons | Weapon presence | Literal weapon/explosive terms | E05 `_WEAPON_TERMS` | EXPLICIT_WEAPON El/PR/PF | Requirement disclosure | PARTIAL | R7 | No safe prop/live/blank/replica or legal classification |
| Stunts | Action/stunt breakdown | Attribute slot `stunt_intensity` only in old package | E19 | AttributeFact supplied by caller | Legacy package | DORMANT | S/H1 | No SA extraction, coordinator, shots, days |
| SFX | Practical effects work | No SA producer | E05 | No model | None | ABSENT | N1 | Type/count/scale/safety |
| Practical effects | Physical effect vs VFX | Generic word 'practical' can be prop hit | E05 | EXPLICIT_PROP only | Disclosure | PARTIAL | S | Not an effect interpretation or plan |
| VFX | Shots/tasks/complexity | Old supplied `vfx_intensity`; budget VFX category is separate | E19/E12 | AttributeFact / budget line | Budget component routing | PARTIAL | S | No scene/shot VFX breakdown |
| Greenscreen | Stage/compositing requirements | Not generated | E05 | No model | None | ABSENT | N1 | Scene/shot/space requirements |
| Virtual production | Volume/LED/previs needs | Not generated | E05 | No model | None | ABSENT | N1 | Method, asset and stage requirements |
| Specialty equipment | Technical rentals | Generic equipment cost inputs only | E22 | Adjustment input, not script fact | Normalization | PARTIAL | S | No screenplay equipment list/quantity/duration |
| Camera requirements | Setups/lenses/rigs | Not generated | E05 | No model | None | ABSENT | N1 | Technical interpretation/AD/DoP confirmation |
| Marine | Marine work requirement | Boat/sea/open-water location ontology; vehicle hits | E05/E13/E14 | LR/El/capability sets | Feasibility disclosure | PARTIAL | S/R8 | No operational marine unit/vessels/count/days |
| Aerial | Aircraft/flight photography | Helicopter/plane lexical presence; old aviation slot | E05/E19 | EXPLICIT_VEHICLE | Disclosure | PARTIAL | S | Aircraft presence ≠ aerial photography |
| Underwater | Water-camera work | Capability token and old supplied attribute exist | E14/E19 | Capability/AttributeFact | Legacy or caller-supplied path | PARTIAL | S | Generic SA builder does not derive underwater signal |
| Intimacy | Closed-set/intimacy requirements | Not generated | E05 | No model | None | ABSENT | N1 | Context/consent/coordinator implications |
| Crowds | Background scale/action | Not generated | E05 | No model | None | ABSENT | N1 | Explicit counts and modeled ranges |
| Music/playback | On-set playback/song needs | Old supplied music-heavy slot; budget music separately | E19/E12 | AttributeFact/budget | Legacy/package and routing | PARTIAL | S | No cues, playback days or rights |
| Choreography | Dance/fight/action choreography | Not generated | E05 | No model | None | ABSENT | N1 | Performers/rehearsal/workdays |
| Specialty personnel | Wranglers/armorers/coordinators | Not derived from detected elements | E05/E08 | No linked staffing model | None | ABSENT | N1 | Requirement→crew derivation |
| Miscellaneous elements | Reviewed extensible categories | String taxonomy columns exist; parser limited to 12 keys | E05/E07 | El/PR | Disclosed requirements | PARTIAL | S | No supported producer taxonomy editing |

### Locations / sets

| Capability | Expected professional function | Existing CineGlobe implementation | Canonical file/module | Data model | Downstream consumer | Status | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| Scripted location | Preserve source setting | Sc location aggregated by normalized key | E05/E06 | Sc/LR | API/UI/feasibility | ACTIVE + SERVED | R1/R2 | Raw UI list not normalized LR list |
| Set | Set identity distinct from place | No dedicated set; heading location proxy | E07/E08 | LR only | Location list | PARTIAL | S | Set/subset identity and set dressing |
| Practical location | Confirm actual shooting venue | `production_location` + approach fields exist, default unknown | E08 | LR | State API | PARTIAL | R3 | No location-selection/edit workflow |
| Stage candidate | Assess stage alternative | `production_approach` storage and stage capability/cost exist | E08/E14/E22 | LR + cost input | State/normalization | PARTIAL | S | No candidate derivation or scenario linkage |
| Build candidate | Assess construction alternative | Not generated | E05/E08 | No model | None | ABSENT | N1 | Set dimensions/build scope |
| Location category | Abstract environments | Shared keyword ontology and 13 UI categories | E13/E14 | Derived maps | UI/feasibility | ACTIVE + SERVED | S/R2 | Substring heuristic; UI and feasibility mappings differ |
| Geography | Setting vs production location | Literal setting + unknown production_location | E08/E13 | LR | State/feasibility | PARTIAL | S | Geocoding, story country/region and actual venue missing |
| Interior/exterior | Count environment load | Counts aggregate Sc.int_ext | E06 | LR.int_count/ext_count | State API | ACTIVE + SERVED | S/R1 | Combined syntax limitation above |
| Recurring location | Consolidate repeated settings | Key-grouped scenes/eighths/counts, recurring flag | E06 | LR | State API | ACTIVE + SERVED | R1 | Alias resolution and production-location identity absent |
| Company move implications | Distance/time/load between units/sets | No scene/location movement model | E08/E22 | No move entity | None | ABSENT | N1 | Generic travel costs are not company moves |
| Difficult access | Access/transport constraints | Not classified | E05/E14 | No model | None | ABSENT | N1 | Access/safety/logistics assessment |
| Controlled/sensitive location | Recognize regulated venues | Literal setting only | E05/E14 | Sc/LR text | None for regulation | PARTIAL | S | No controlled-location classification |
| Location substitution potential | Story-compatible alternatives | Environment matching of jurisdictions | E14 | CapabilityMatch | Feasibility disclosure | PARTIAL | S | No specific replacement venue or story-invariant check |

### Physical production

| Capability | Expected professional function | Existing CineGlobe implementation | Canonical file/module | Data model | Downstream consumer | Status | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| Night work | Night scene load/workdays | Night scene/location counts | E05/E06 | Sc/PF/LR | API | PARTIAL | R1 | Generic requirements builder does not forward night count; no shift rules |
| Exterior work | Exterior workload | EXT/INT_EXT counts | E05/E06 | Sc/PF/LR | API | PARTIAL | R1 | No exterior days, exposure or weather plan |
| Weather | Production weather requirements | Snow/desert environmental keywords only | E14 | Capability sets | Feasibility | PARTIAL | S | No scene weather or forecast/calendar system |
| Rain/snow | Physical effects/natural conditions | Snow location ontology; no rain action extraction | E14 | LR-derived capability | Feasibility | PARTIAL | S | No wet-down/rain rigs/snow scope |
| Water work | Surface/underwater/tank operations | Open-water locations, old supplied underwater signal | E13/E14 | Capabilities | Feasibility | PARTIAL | S | No water unit, safety or quantity plan |
| Road work | Traffic control/driving/closures | Vehicle/location strings only | E05 | El/LR | Disclosure only | PARTIAL | S | No road-work classification |
| Airports | Airport operation/access | May retain airport in literal heading | E05 | Sc/LR text | Location list | PARTIAL | S | No airport restriction model |
| Hospitals | Medical-location operations | May retain hospital heading | E05 | Sc/LR text | Location list | PARTIAL | S | No controlled facility/medical support inference |
| Schools | School location/child implications | Literal heading and minor terms separately | E05 | LR/EXPLICIT_MINOR | Disclosure | PARTIAL | S | No joined school/child-performer constraints |
| Government facilities | Sensitive venue operations | Literal heading only | E05 | LR text | Location list | PARTIAL | S | Classification/permission rules missing |
| Crowds | Background logistics | Not generated | E05 | No model | None | ABSENT | N1 | Counts/days/holding/catering |
| Closures | Roads/business/site closure | Not generated | E05 | No model | None | ABSENT | N1 | Closure type/duration |
| Permits | Activity/location authorization | Generic visa/work-permit costing exists, not scene permits | E22/E23 | Cost/program requirements | Cost/rule disclosure | PARTIAL | S | Permit inventory and jurisdiction-sensitive activity linkage |
| Second unit | Separate unit scope/workdays | No script-derived unit planning | E05/E08 | No ProductionUnit | None | ABSENT | N1 | Assignments/calendar/crew |
| Construction | Set/scenic builds | Existing budget category only | E19/E22 | Budget spend category | Cost/qualification | PARTIAL | S | No script-derived build scope |
| Stage requirements | Stage size/days/features | Generic stage costs/capability, LR approach unknown | E08/E22 | LR/cost inputs | State/normalization | PARTIAL | S | Script→stage plan missing |
| Specialty crew | Required skills/roles | Generic manifest defaults; no element-to-crew mapping | E22 | CrewManifest | Normalization | PARTIAL | S | Measured staffing |
| Specialty equipment | Required rentals/support | Generic equipment-value/cost inputs | E22 | ProductionBudgetParams | Normalization | PARTIAL | S | Itemized rentals and workdays |

### Post

| Capability | Expected professional function | Existing CineGlobe implementation | Canonical file/module | Data model | Downstream consumer | Status | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| VFX burden | Shot counts/tasks/complexity | Old supplied intensity slot; existing budget VFX spend | E19/E12 | AttributeFact/budget | Component routing | PARTIAL | S | No script-to-shot work scope |
| Editing implications | Coverage/time/structural burden | Scene/word counts only | E05/E06 | Aggregate facts | API | PARTIAL | S | No editorial plan or duration model |
| Sound post | Sound design/mix requirements | Budget sound category/movable concept | E19/E21 | Budget/package | Existing routing helpers | PARTIAL | S | No screenplay sound breakdown |
| ADR | ADR requirements | No extraction | E05 | No model | None | ABSENT | N1 | Dialogue/environment ADR decisions |
| Music | Score/source/playback/rights | Caller-supplied music-heavy; budget music routes | E19/E12 | AttributeFact/budget | Component routing | PARTIAL | S | Cue sheet/durations/rights |
| DI/color | Finish workflow/deliverables | No script-derived DI model | E05/E08 | No model | None | ABSENT | N1 | Post scope/format/finish assumptions |
| Animation | Animation workload | Old supplied animation attribute | E19 | AttributeFact | Legacy package | DORMANT | S | No asset/shot/style/work-volume extraction |
| Virtual production | Asset/previs/on-set/post split | No implemented analysis | E05/E08 | No model | None | ABSENT | N1 | Work packages and dependencies |
| Post/VFX relocation potential | Move suitable work without moving shoot | Generic budget-component routing + program pricing | E12 `_price_component_relocation_candidate` | Structures/allocation/budget | Served optimizer | ACTIVE + SERVED | S/H8 | Not derived from screenplay shots or schedule; retain existing engine |

## Matrix B — commercial breakdown domains

| Commercial breakdown domain | Existing coverage | Quality | Missing capability | Reuse/extend/build |
|---|---|---|---|---|
| Source ingestion/versioning | Library documents, checksums, typed projection, text extraction | Real and persisted; revision-selection edge incomplete | Active-draft promotion/resolution, immutable storage edge checks, supported format boundaries | REUSE E01–E04; EXTEND revision handling |
| Scene structure | Headings, sequence, setting, time, page signals | Useful first pass; professional paging and alternate heading forms incomplete | Geometric eighths, zero-scene failure classification, temporal scene groups | EXTEND E05/E07 |
| Cast breakdown | Cue names, dialogue and speaking-scene burden | Heuristic; confirmed FVD false positive | Non-speaking appearances, tier/age/skills, performer links, corrections | EXTEND Ch/El, not ProjectPerson as fictional character |
| Physical elements | Explicit vehicles/animals/weapons/minors/limited props/period | Presence-only lexical observations; no measured precision/recall | Full taxonomy, contextual detection, quantities, complexity, human confirmation | EXTEND El/PR and existing Bridge |
| Locations/sets | Normalized scripted locations/recurrence and environment ontology | Useful seed; aliases and production decisions unresolved | Set/location identity, build/stage/practical alternatives, access/permits, moves | EXTEND LR and shared ontology |
| Physical production | Night/exterior counts and coarse environment feasibility | Partial, not a shooting plan | Crew/equipment/activity workload, weather, units, safety/logistics | EXTEND requirements; BUILD missing planning behavior |
| Post | Budget-driven post/VFX/music routing | Existing economic machinery, not script breakdown | Shots/assets/edit/sound/music/DI scope and schedule | REUSE routing; EXTEND upstream work requirements |
| Scheduling | No film schedule engine; stored schedule document category only | Not implemented | Schedule/ShootDay/units/calendar/constraint solver/import | BUILD on current Sc/Ch/LR/PR; no parser replacement |
| Budget estimation | Existing budget parser and cost adjustment formulas | Not screenplay cost estimation | Requirement/schedule→quantity/rate/duration drivers; uncertainty and source precedence | REUSE budget/cost/holdout owners; BUILD drivers |
| Global content/regulatory | Program/treaty/cultural knowledge plus limited script-fact interface | Rules exist; content extraction largely absent | Sensitive-content findings, source spans, jurisdiction-specific review and progressive warnings | EXTEND existing facts/rule consumption |
| Human correction/version comparison | Project-level overrides and evidence fields | Not a breakdown correction product | Scene/element edit/review/locks, cross-draft correspondence, dependency deltas | EXTEND evidence/version spine |

## Matrix C — scheduling capabilities

Statuses refer to filmmaking scheduling, never job schedulers or incentive timing. N1 found no scheduling implementation in reachable code history.

| Scheduling capability | Existing implementation | Status | Reuse/extend/build |
|---|---|---|---|
| Stripboard | No stripboard representation/view | ABSENT — N1 | BUILD using Sc |
| Scene strips | Sc fields could populate strips, but none rendered | PARTIAL — E07/E11 S | EXTEND existing scenes into schedule view/model |
| Shoot-day construction | No ShootDay table or assignment function | ABSENT — N1/R1 schema query | BUILD |
| Schedule generation | No function assembling shoot days | ABSENT — N1 | BUILD |
| Schedule optimization | No objective/constraint solver over scenes/days | ABSENT — N1 | BUILD after confirmed schedule inputs |
| Cast availability | ProjectPerson identity only; no calendar | ABSENT — E07/E15/N1 | EXTEND personnel with confirmed availability |
| Location availability | LR location text/approach only | ABSENT — E08/N1 | EXTEND location decisions |
| Location grouping | `build_requirements` groups by location_key and records scenes | PARTIAL — E06 S/R1 | REUSE aggregation; EXTEND into shoot-day grouping |
| Cast grouping | Ch.scene_sequences groups speaking scenes | PARTIAL — E05/E07 S | REUSE after appearance accuracy correction |
| Day/night grouping | Time tokens and aggregate counts | PARTIAL — E05/E06 S | REUSE; BUILD scheduling assignment |
| INT/EXT grouping | Scene enum and LR counts | PARTIAL — E05/E06 S | REUSE; BUILD scheduling assignment |
| Company moves | Travel movement/crew manifest inputs, no scene-to-scene moves | ABSENT as scheduling — E19/E22/N1 | REUSE travel arithmetic; BUILD moves |
| Page/eighth totals per day | Scene eighths only; no days | PARTIAL — E05/R5 | Correct eighths then BUILD day totals |
| Estimated scene duration | No duration field/estimator | ABSENT — N1 | BUILD with explicit assumptions |
| Estimated shoot complexity | Old `stunt_intensity`/`vfx_intensity` slots, no estimator | ABSENT as computation — E19/N1 | EXTEND reviewed requirements |
| Estimated setup burden | No shots/setups/time model | ABSENT — N1 | BUILD |
| Crew/equipment constraints | Default CrewManifest and costs, not resource calendars | ABSENT as scheduling — E22 | REUSE input conventions; BUILD resource constraints |
| Turnaround | No scheduling rule/checker | ABSENT — N1 | BUILD with sourced applicable rule inputs |
| Meal/rest constraints | No scheduling rule/checker | ABSENT — N1 | BUILD |
| Child-performer constraints | EXPLICIT_MINOR presence only | PARTIAL precursor — E05/E08 | EXTEND age/performer linkage, then BUILD constraints |
| Night-work constraints | Night scene counts only | PARTIAL precursor — E06 | EXTEND into confirmed shift/rule constraints |
| Weekends | No production calendar | ABSENT — N1 | BUILD |
| Travel days | TravelInputs has nights/per-diems/rotations; no scene calendar | PARTIAL precursor — E19/E22 | REUSE movement model, EXTEND source days |
| Weather | Static geography/capability signals, no calendar/weather plan | ABSENT as scheduling — E14/N1 | BUILD |
| Location restrictions | LR flexibility unknown; LOCATION_FIXED kind has no checker | PARTIAL schema — E08/E20 | EXTEND confirmed restrictions and implement checks |
| Actor workdays | Speaking-scene burden, no day assignment | ABSENT as workdays — E07 | BUILD from corrected appearances + schedule |
| Hold days | No hold calendar | ABSENT — N1 | BUILD |
| Second unit | No unit entity/assignment/calendar | ABSENT — N1 | BUILD |
| Splinter unit | No unit entity/assignment/calendar | ABSENT — N1 | BUILD |
| Schedule alternatives | `ScenarioKind.SHIFT_SCHEDULE` filters existing financial structuring opportunities, creates no schedule | DORMANT adjacent helper — E21 S | REUSE economic scenario comparison; BUILD planning alternatives |
| Schedule comparison | Existing scenario NPC delta is not schedule delta | ABSENT as scheduling — E21/N1 | BUILD over versioned schedules |

## Matrix D — global script intelligence

The existing rule database was inspected only to identify consumers, not to re-research or revalidate jurisdictions. Textual program guidance is not a screenplay-content scanner.

| Global script intelligence | Existing implementation | Downstream wiring | Status | Gap |
|---|---|---|---|---|
| Cultural tests | Deterministic role/point/discretionary rule engines | E15/E23 → evaluation qualification trace/admission | ACTIVE + SERVED for rule engine; PARTIAL for script inputs — S/R8 | SA story-setting taxonomy mismatch; unextracted criteria remain missing facts |
| Nationality | Title-page real-person credit recovery + linked personnel enrichment/confirmed values | E27 → ProjectPerson/TalentProfile → E15 qualification | ACTIVE + SERVED, not script character inference — S | Character nationality not extracted; author nationality not inferred from story |
| Story geography | Sc/LR settings and environment keyword ontology | E13→feasibility; E15 expects different element names | PARTIAL — R8 | No canonical disambiguated story-country/region facts |
| Language | Supplied AttributeFact slot; cultural consumer accepts `language` | Legacy E19; generic package empty; no SA emitter | IMPLEMENTED BUT NOT SERVED as script extraction — S/R8 | Extract/confirm actual language evidence and connect existing consumer |
| Local-content requirements | Existing cultural/national-status program rules | E15/E23 qualification/opportunity trace | PARTIAL — S | Requires actual people/spend/production/content facts; no automatic script proof |
| Treaty/co-production characteristics | Nationality/ownership/cultural fact bridges | E12/E23 → conditional treaty opportunities | ACTIVE + SERVED for structure rules — S/H8 | No script-owned treaty determination; real project agreements/shares required |
| Censorship | Some program profiles retain content/script-approval notes | Requirements disclosure, not scene analysis | PARTIAL knowledge only — E23 S | No content→jurisdiction classifier or adjudication |
| Content restrictions | Stored program exclusions/approval facts | Program guidance where exposed | PARTIAL knowledge only — E23 S | No screenplay finding pipeline |
| Regulatory restrictions | Compliance/preapproval/entity/permit facts | Existing program requirements and normalization | PARTIAL — E22/E23 S | No activity/location-specific screenplay compliance model |
| Political content | No extractor/taxonomy | None | ABSENT — N1 | Evidence-backed detection and jurisdiction review |
| Religious content | Cultural subject-matter rule text may mention topics; no extraction | No screenplay content signal | ABSENT as analysis — E05/E23/N1 | Subject/context evidence |
| Sexual content/nudity | No extractor/taxonomy | None | ABSENT — N1 | Context, intimacy/consent/closed-set review |
| LGBTQ content | No extractor/taxonomy | None | ABSENT — N1 | Context-sensitive advisory review, never identity-based generic exclusion |
| Violence | Weapon terms only | EXPLICIT_WEAPON requirement disclosure | PARTIAL — E05/R7 | Depiction/severity/action context not extracted |
| Drugs | No extractor/taxonomy | None | ABSENT — N1 | Depiction/prop/activity distinction |
| Weapons | Literal terms with source evidence | PR disclosure; not regulatory gates | PARTIAL — E05/R7 | Safe prop/replica/firearm/legal context |
| Gambling | No extractor/taxonomy | None | ABSENT — N1 | Activity/depiction context |
| Minors | Literal minor terms | PR confirmation flag; no labor/content rule evaluation | PARTIAL — E05/R7 | Fictional age vs real performer age, work/consent rules |
| Animals | Literal animal terms | PR disclosure/confirmation flag | PARTIAL — E05/R7 | Real animal vs dialogue/CG; welfare/import/handler requirements |
| Intimacy | No extractor/taxonomy | None | ABSENT — N1 | Activity/performer safeguards and confirmed plan |
| Government/military portrayal | Old supplied `military` attribute; no interpreted content | Legacy package only | DORMANT — E19 S | No portrayal/context classifier |
| Historical figures | First period/year match per scene | PERIOD_REFERENCE disclosure; not person recognition | PARTIAL — E05 S | Entity identity/depiction and rights review |
| Defamation/privacy | No script assessment | None | ABSENT — N1 | Legal-review issue spotting, not automatic legal conclusion |
| Controlled locations | Literal setting text | Location list/ontology only | PARTIAL — E05/E14 S | Sensitive-site classification and venue-specific restrictions |
| Permit restrictions | Program compliance metadata and work-permit costing | E22/E23, not script-derived permits | PARTIAL — S | Link activity/location/territory to permit requirements |
| Import restrictions | Freight/carnet cost formulas; no weapon/animal imports analysis | E22 normalization | PARTIAL adjacent economics — S | Import admissibility, permits, timing and evidence |
| Other jurisdiction-sensitive material | Extensible strings and program rule owners exist | No generic scene-sensitive-material pipeline | PARTIAL infrastructure — E07/E23 | Full taxonomy, provenance/review, progressive per-rule mapping |

| Consumer category | Actual current behavior |
|---|---|
| Warnings | Parser warnings, physical feasibility reasons, qualification missing facts, and program requirements are available in APIs/traces. No general content/censorship warning engine. |
| Eligibility | Cultural/role/treaty rules consume recognized project facts. SA-1 `scripted_location` is not recognized by the story-setting mapping. |
| Hard exclusions | Current economic discovery is separated from physical feasibility. Real qualification HARD_FAIL can block applicable economics; mere missing script facts should not be upgraded to failure. No censorship scanner currently hard-excludes jurisdictions. |
| Conditional eligibility | Existing missing-script/user/role and treaty states are progressive. Preserve those distinctions when adding content interpretation. |
| Optimizer opportunities | Treaty, component and national-status opportunities exist, primarily from program/project/budget inputs, not a professional scene graph. |
| Jurisdiction recommendations | Physical feasibility reasons are disclosed alongside economics; there is no story-preserving content/regulatory recommendation engine. |

## Matrix E — story-preserving cost engineering

| Cost-engineering capability | Existing implementation | Status | Gap |
|---|---|---|---|
| Location substitution | E14 keyword abstraction + jurisdiction capability matching | PARTIAL, ACTIVE disclosure — S | Does not propose a specific visual double or validate story invariants |
| Location consolidation | LR recurrence groups identical normalized setting | PARTIAL precursor — E06 | No combining distinct sets/venues or tradeoff proposal |
| Set consolidation | No set entity/alternative generation | ABSENT — N1 | Set identity, scene demands, approved substitutions |
| Company-move reduction | No scene travel graph/schedule | ABSENT — N1 | Locations/distances, move duration and schedule objective |
| Cast-day consolidation | Ch scene lists only | PARTIAL precursor — E07 | No all-appearance/availability/day calendar |
| Schedule optimization | No scheduling optimizer | ABSENT — N1 | Capacity and constraints, then alternative schedules |
| Night-to-day alternatives | No transformation/proposal | ABSENT — N1 | Story/lighting continuity and producer approval |
| Practical vs stage | LR approach field UNKNOWN; stage cost calculator | PARTIAL — E08/E22 | No paired production-method scenario or suitability comparison |
| Stage vs location | Same storage/cost ingredients | PARTIAL — E08/E22 | Stage scope, practical venue, calendar and cost drivers |
| Build vs practical | Construction spend category, no alternative generator | PARTIAL precursor — E19 | Build design/area/duration vs location costs |
| Regional doubles | Geography-to-environment ontology | PARTIAL — E14 | A coarse country capability is not a verified visual double |
| Local sourcing | Movable/fixed budget categories; structure/allocation routing | PARTIAL — E12/E19 | No vendor inventory or scene-item sourcing plan |
| Crew localization | Cost indices/local-hire premiums + nationality/role opportunities | ACTIVE + SERVED economics, PARTIAL plan — E12/E22 | Uses cost assumptions, not screenplay-derived departments/workdays |
| Equipment localization | Equipment index/freight/carnet adjustment | ACTIVE + SERVED economics, PARTIAL plan — E12/E22 | No equipment package/availability/quantity/schedule |
| Second-unit alternatives | No work-unit planner | ABSENT — N1 | Scene delegation, cost, continuity and staffing |
| Post/VFX relocation | `_price_component_relocation_candidate` and existing allocation/pricing | ACTIVE + SERVED — E12/H8 | Budget-based amount, not shot/task-derived demand |
| Virtual production | No VP analysis/scenario | ABSENT — N1 | Asset/previs/volume/crew/post model |
| Production component relocation | Generic movable component loop; six-target prefilter removed at `380ecd9` | ACTIVE + SERVED — E12/H8 | Uses independently priced targets and existing nonzero budget components; no script work-package planner |
| Other cost-reduction recommendations | Legacy production recommendations, qualification path combinations, financial structuring scenarios | DORMANT/PARTIAL for screenplay engineering — E19/E21 | No story-quality preservation test or scene-level rewrite acceptance |
| Travel/FX/local-cost economics | Reconnected generic normalization and existing cost/travel formulas | ACTIVE + SERVED — E12/E22/H8 | Inputs include benchmark/default crew/days, not a generated schedule; do not relabel as measured screenplay demand |
| In-kind replacement | LU-specific historical calculation remains; generic derivation absent | DORMANT/PARTIAL — E12 `_relocation_normalization` | Needs actual production-specific contribution evidence, not a universal default |

## Matrix F — budget-estimator precursor readiness

All script-derived Sc/Ch/El/PR/LR outputs are structured and carry screenplay/parser lineage at storage level. Aggregate ProjectFacts are effective project-level values, not a complete immutable per-draft history. “Consumable” below means accessible structured input, not that an implemented Budget Estimator already uses it.

| Script Analyzer output | Budget-estimator readiness | Current consumer | Missing information |
|---|---|---|---|
| Scene count / ordering | Consumable count; R1 real; zero-scene success and boundary limitations require guards | Script API/state/UI | Validated scene segmentation, alternate scene syntax |
| Pages / eighths | Structured but NOT production-grade quantities; R5 proves density-estimate issue | Ch/LR burden, API/state | Preserved physical layout and reliable eighths |
| Shoot days | Not generated. PA schema exists; zero live PA rows; old handoff returns null | E10 optional shoot_days; E22 defaults independent | Schedule/confirmed days, pages/day, constraints and uncertainty |
| Cast days | Speaking-scene/eighth counts are usable precursor only | Script API | All appearances, casting links, work/hold/travel/rehearsal days |
| Background days/count | No output | None | Scene headcount/ranges, featured/background distinction, days |
| Crew requirements | No script-derived staffing; generic manifest defaults exist elsewhere | Normalization | Departments, unit size, skills, prep/shoot/wrap duration |
| Location days | LR scene/eighth/INT/EXT/day/night recurrence is structured | State/feasibility/UI | Actual venue, daily capacity, holds/prep/wrap/moves |
| Stage days | LR production_approach UNKNOWN | State | Stage decision/area/occupancy/calendar |
| Company moves | No output | None | Venue graph, distances, load/strike/transport duration |
| Vehicle days | Lexical type presence only; PR quantity null | Requirement disclosure | Picture/background type, count, rental days, drivers, stunts |
| Equipment days | No item/day output | Existing-budget cost normalization | Equipment package/quantity, prep/shoot/wrap, rental terms |
| Stunt days | No output | Old supplied intensity slot only | Action/stunt plan, coordinator/doubles/rehearsal/days |
| SFX days | No output | None | Effect type/scale, preparation, safety, rigs/days |
| VFX counts/complexity | No script-derived shots; existing budget VFX amount is different evidence | Component routing | Shot/task/asset counts, complexity, revisions and post duration |
| Construction requirements | Not derived | Budget category only | Sets/area/materials/labor/prep/strike |
| Wardrobe | Not derived | None | Character looks, changes, multiples, rentals/builds and days |
| Hair/makeup | Not derived | None | Looks/prosthetics/continuity, artists and days |
| Animals | Structured terms/scene evidence, no scale; requires confirmation | PR disclosure | Live/CG choice, trained animals, handlers, welfare, days |
| Weapons | Structured terms/scene evidence, no safety/legal inference | PR disclosure | Prop/live/replica classification, armorer, permits/days |
| Marine/aerial | Location/vehicle evidence plus capability vocabulary | Feasibility disclosure | Actual photography method, craft/unit/crew/safety/days |
| Travel implications | Source settings exist; crew movement inputs/formulas exist separately | Normalization | Confirmed production locations/origins, people, itineraries, travel days/nights |
| Post requirements | No full post breakdown; budget categories and routing work | Optimizer | Editorial/sound/ADR/music/DI/VFX scope and work durations |
| Period reference | First lexical year/period hit per scene; structured but noisy | Physical period environment + PR | Confirmed story era, affected costumes/sets/vehicles and scale |
| Confidence/review | Evidence states and confirmation flags exist; confidence/review fields unpopulated in R7 | Disclosure only | Calibrated confidence, producer review and effective approved quantities |
| Cost/benchmark primitives | Existing quantities×rates/durations, fringe/equipment/stage/travel formulas | E22 normalization | Real script/schedule driver mapping; defaults must remain labeled defaults |
| Calibration corpus | Versioned code fixtures separate script inputs from held-out actual budgets/days | E26 validation tooling | Actual prediction engine and measured error; fixture truth is not a generated estimate |

## Canonical graph, editability and versioning

### One source representation: present but incomplete

| Entity/relationship | Existing implementation | Reuse boundary / gap |
|---|---|---|
| Scene | Version-scoped Sc with source text offsets and scene_hash | Reuse. No cross-draft stable UUID, chronology graph or synopsis. |
| Character | Version-scoped fictional Ch; speaking scene sequences stored as JSON | Reuse. Not an actor; no casting link/all-appearance relation. |
| Location | Sc string/location_key plus aggregated LR | Extend. No independent canonical Location/Set entity or alias identity. Raw UI strings and normalized requirements already differ 55/54 for FVD. |
| Element | Sc→El FK, taxonomy/value/evidence span/hash | Reuse. No material interpretation, quantity producer or review workflow. |
| Production requirement | PR aggregates `(requirement_key, normalized_value)` with source sequence arrays | Reuse. No typed edge to individual supporting El IDs; quantities null. |
| Constraint | E20 in-memory production-structure constraints | Adjacent capability, not a persisted scene/schedule constraint graph. |
| Relationship | FKs plus Ch/LR/PR sequence arrays | Partial graph; relationships are reconstructed differently by downstream readers. |
| Canonical state | E09 snapshot exists; current evaluator directly queries related tables through E12/E13/E15 | Not one universally consumed state contract. Preserve tables; align effective active-version selection and adapters instead of adding another state store. |

For the example “EXT. CITY STREET — NIGHT; 300 background; rain; stunt driving; four principals,” current SA-1 can store heading/EXT/NIGHT/location and recover speaking cues/selected literal vehicle terms. It does **not** produce 300 background, rain effects, a stunt-driving requirement, a reliable principal-cast count, or their workdays. Scheduling, content review and budget estimation therefore cannot consume that full example once today; those facts have not yet been modeled.

### Human-in-the-loop matrix

| Capability | Existing behavior | Status / evidence | Missing boundary |
|---|---|---|---|
| Edit extracted scene | No scene PATCH/PUT UI/API | ABSENT — E11/N1 | Reviewed scene edits with source preservation |
| Change element classification | Taxonomy string field only | PARTIAL schema — E07 | Classification edit command/history |
| Merge/split elements | No operation | ABSENT — N1 | Identity and provenance-aware merge/split |
| Add missing element | No supported command/UI | ABSENT — E11/N1 | Human-created element with source/method |
| Delete false positive | No supported review/delete command | ABSENT — E11/N1 | Suppression/tombstone that survives reparse |
| Override location | Category-level UI control exists; singleton write resolves LU, not viewed project | PARTIAL/DEFECT — E18 S | Project-scoped script/set/location decisions and consumer alignment |
| Override cast classification | Real personnel names/nationality editable; fictional role tier is not | PARTIAL — E18/E27 | Character-role classification and actor linkage |
| Lock approved fact | `ProjectFact.USER_OVERRIDE` skips automatic derived overwrite | PARTIAL — E06 | Not scene/element/PR review locking; approval alone is not the skip criterion |
| Confidence | El.extraction_confidence schema; all live SA values null | PARTIAL schema — R7 | Per-observation calibrated confidence/limitations |
| Source provenance | DocumentVersion, parser, text span/hash, requirement source sequences | ACTIVE + SERVED partly — E06/E07/R1 | Detailed source spans/elements not in current script GET UI |
| AI vs human-authored | extraction_method/evidence_state/is_interpretation fields | PARTIAL — E07/R7 | Only deterministic producer implemented; human/AI effective-value workflow absent |
| Version history | Source DocumentVersions retained; parse result per ScreenplayDocument | PARTIAL — E01/E06 | Same-draft parser re-run replaces rows, not versioned analysis history |
| Re-analysis preserves approvals | ProjectFact USER_OVERRIDE and separately authored requirement rows survive some paths | PARTIAL, unsafe for future element edits — E06 | Reparse deletes scenes and screenplay-generated PR/LR; cascades can delete linked non-deterministic elements; no approval exclusion |

### r5 → r6 behavior

| Question | Existing answer | Verification |
|---|---|---|
| Can a new source draft be stored without deleting r5? | Yes. New checksum produces a DocumentVersion. Ambiguous order is left non-current and disclosed, not guessed. | E01/E02 S |
| Is r6 automatically made current? | No for an ambiguous sibling; explicit resolution is needed. No complete current-draft promotion UI/API was found in the inspected library routes. | E02 / project document read model S |
| Once r6 is current but unprojected, does generic routing reliably parse it? | No. `_route_screenplay` ignores its version argument for parse selection; `resolve_active_screenplay` returns an existing older row before the current DocumentVersion bootstrap when any row exists. | E03/E06 S; no write-based reproduction performed |
| Is stale-new-version status actively assigned? | No assignment found; constant/text only. | E29 + application search S |
| Does an independently projected r6 retain r5 scenes? | Yes, distinct screenplay rows scope parser replacement. | E06 S |
| Do consumers then read only r6? | Not consistently. E09 requirements, E13 physical/UI requirements, E15 script facts and E17 requirement disclosure query the whole project without an active-screenplay filter. | S; current DB has no two-parsed-draft case to runtime-verify contamination |
| New/deleted/modified scene detection? | No draft correspondence/diff implementation. scene_hash is sequence + normalized heading + source offset, not body-content identity. | E05/E07 S/N1 |
| Changed cast/location/element detection? | Whole-text hash notices a changed parse input, but there is no semantic change ledger or cross-draft reconciliation. | E05/E06 S |
| Are identities stable? | Scene hash stable for identical text; force parse recreates DB UUIDs. Character identity is `(screenplay_id, canonical_name)`; element evidence hash is not a durable cross-draft ID. | E05/E06/E07 S |
| Analysis version? | Parser version/text fingerprint/parsed_at fields; no separate immutable analysis-run entity or prompt/model version for SA-2. | E06/E07 S |
| Downstream invalidation? | Old state fingerprint includes script metadata; live evaluator hashes a set of script element values plus economic/personnel/ruleset inputs. It does not hash full script text, source draft ID, scene frequency/order/eighths, or approved breakdown revisions. | E09/E12 S |
| Only affected calculations recomputed? | No dependency graph/selective invalidation. Existing generic evaluation recomputes the evaluation on relevant fingerprint change, otherwise reuses it. | E12 S |

## Material defects and disconnected behavior to address before expansion

| ID | Exact evidence / behavior | Consequence | Smallest extension/repair boundary, not implementation |
|---|---|---|---|
| D1 — paging/eighths | E04 joins pages without explicit boundaries; E05 uses global text density even in layout mode. R5: a one-page scene receives 16 eighths. | Existing eighths cannot safely drive professional pages/day, cast burden or quantities. | Preserve page mapping/geometry through E04→E05; correct existing calculation and disclose approximation. |
| D2 — character and heading precision | R4 actual FVD action phrase becomes speaking character; R5 literal INT-EXT misparses. E05 scans all scene text for element terms without action/dialogue/negation context. | Reported character/element counts are not validated professional breakdown counts. | Extend current parser's block segmentation/grammar and add producer correction, not another parser. |
| D3 — new-draft selection | E06 returns an old projection when no current projection exists; E03 does not pass the committed version into projection creation. | Revision can be stored/current while analyzer continues using old draft. | Resolve canonical current DocumentVersion first; project/parse that exact version. Preserve ambiguous-version handling. |
| D4 — multi-version consumers | E09/E13/E15/E17 query project-wide historical rows. | Once multiple drafts are parsed, removed locations/elements can persist as active requirements/qualification inputs. | One shared active-script selection used by all consumers; do not delete historical evidence. |
| D5 — cultural taxonomy disconnect | R8: producer emits `scripted_location`; consumer accepts `location`/`environment`. | Current SA-1 settings never reach the existing story-setting cultural criterion through this mapping. | Extend the existing adapter with explicit semantic/provenance mapping; do not equate every location string with qualifying domestic content. |
| D6 — generic package/UI disconnect | R2: detailed script API has 99/38 but generic `pkg.script` is empty/unknown. | Main production QualificationPanel shows unknown story/language regardless of available structural data; rich scene detail not exposed by UI. | Adapt persisted current-script data into existing package/UI contracts; keep unextracted language/cultural attributes unknown. |
| D7 — location correction wrong target/consumer | E18 posts no project ID and backend finds LU by title. E13 physical requirements ignores category override rows although UI builder reads them. | A generic project's location correction can write the wrong project and not alter its feasibility inputs. | Project-scope existing location write; share effective override selection and invalidation between UI and feasibility. No new location registry. |
| D8 — no durable breakdown approval | E06 replacement deletes this draft's scene/character/derived PR/LR rows; no approval/lock guard. | Future producer element corrections would be overwritten or cascaded away. | Add review/effective-value protection on existing entities before AI quantities become cost inputs. |
| D9 — success/readiness and fingerprint boundaries | Empty/no-heading result is still persisted as SCRIPT_PARSED; old state can accept missing assumptions (R3). Current evaluator uses set-valued script facts, not draft/review identity. | Parse success is not professional readiness; changed frequency/order may not invalidate downstream state. | Separate parse quality/analysis readiness/planning readiness, and include effective draft/analysis/review dependencies in existing fingerprints. Do not block independent incentive economics merely because scheduling facts are missing. |

No broad jurisdiction, incentive-rate, authority-residual, or optimizer correctness audit was performed. Findings above concern the Script Analyzer's inputs, representation and consumers only.

## Regression protection and verification limits

| Surface | Existing protection | Status / limitations |
|---|---|---|
| Structural parser | E25: heading/INT_EXT/TOD, cue exclusions, aliases, taxonomy, no inferred quantities, page-basis, fingerprints, no-headings warnings | STATIC VERIFIED. Tests do not establish real-script precision/recall; R4/R5 reveal uncovered cases. No suite run. |
| Location normalization | E25: clock/SAME, distinct sublocations, parser bump, real-row UI category derivation | STATIC VERIFIED; current persisted 1.1.0 FVD/LLS outputs R1/R6 verified. |
| Library/routing | `test_ingestion_api.py`, `test_ingestion_phase_f.py`, `test_evaluate_triggers_script_ingestion.py` | STATIC VERIFIED. Existing tests cover first ingestion/duplicates/retroactive trigger, not a complete current-r6-with-old-projection transition. |
| Generic workspace | `test_project_workspace_view.py`; current GET R2 | RUNTIME VERIFIED API summary. Browser rendering/navigation not executed; frontend is a dirty working-tree overlay. |
| Requirements→feasibility | `test_fvd_canonical_input_assembly_repair.py`, `test_canonical_ingestion_propagation.py` and E12 callsites | STATIC VERIFIED; current DB requirements real. Did not re-run optimizer or modify stored evaluation. |
| Cultural facts | Existing role-qualification tests and actual R8 query | RUNTIME VERIFIED query shape; S-verified mismatch with consumer vocabulary. No new jurisdiction validation. |
| Revision/approval | Text hash/idempotency and source-version models | PARTIAL; no scene delta/review-preservation protection found. Multi-draft mutation deliberately untested. |
| Calibration | E26 and `test_real_production_corpus.py` | STATIC VERIFIED guard/tools. Not scheduling/budget-prediction accuracy evidence. |
| Full served deployment | No browser/server deployment probe | UNVERIFIED. Current-checkout read-only ASGI calls do not establish deployed process SHA or UI runtime. |

## Final architectural map

| Category | Exact disposition |
|---|---|
| **EXISTING AND PRESERVE** | Universal Document/DocumentVersion/source identity; SA-1 structural parser; Sc/Ch/El/PR/LR storage; source spans/parser hash; 20 derived facts; real FVD/LLS parsed data; mounted script and summary APIs; physical feasibility/qualification rule owners; canonical budget/incentive/NPC engine; current generic component routing/relocation normalization; manual Bridge; held-out corpus. |
| **EXISTING BUT EXTEND** | Page handling/heading and cue accuracy; objective element taxonomy; active-script selection; effective review/override precedence; requirement quantities/work drivers; character appearances and actor linkage; location/set/alias decisions; state/fingerprint dependencies; existing UI/package adapters. |
| **EXISTING BUT DISCONNECTED** | SA-1 story locations versus cultural-test element vocabulary; full persisted script versus generic `pkg.script`; category overrides versus generic feasibility reader; rich ProductionPackage question/attribute tooling versus per-project DB assembly; creative qualification path helper versus scene-aware recommendations. |
| **DUPLICATED / SHOULD CONSOLIDATE** | Legacy coarse parser/result/chunks versus SA-1 structural output; obsolete CanonicalProductionState→ProductionOptimizerInput executor contract versus current direct-table evaluator; raw UI locations versus normalized LR identities; UI/physical/cultural consumers selecting facts independently; legacy LU manual script attributes alongside canonical parsed script. Consolidate selection/adapters and mark legacy callers—do not replace functioning owners. |
| **MISSING** | Interpreted material breakdown/SA-2 package and response/evidence validation; professional scene/element edits/locks; complete appearance and relationship graph; immutable analysis/review history and cross-draft semantic diff; film Schedule/ShootDay/ProductionUnit; measured quantities/durations/cost drivers; screenplay Budget Estimator; general content/censorship/regulatory interpretation; scene-level story-preserving cost alternatives. |
| **UNKNOWN / REQUIRES RUNTIME VERIFICATION** | Browser behavior at the dirty frontend snapshot; deployed server revision; actual revised-draft/approval preservation after bounded fixes; complete precision/recall against professionally marked breakdown; schedule/estimate accuracy once implementations exist. No hidden SA-2 implementation was found in reachable repository history. |

### Minimum incremental path — no replacement architecture

| Order | Bounded work | Reuse owner | Acceptance boundary |
|---|---|---|---|
| 1 | Close D1–D9 within existing analyzer: reliable page/heading/cue behavior, exact current draft selection, active-only consumers, project-scoped corrections, taxonomy/UI adapters, review-safe persistence and fingerprints. | E01–E18 | Current FVD/LLS survive; a controlled r5→r6 example changes only current effective facts; known false positive is correctable without being resurrected. Do not reopen SA-1/SA-1.5 wholesale. |
| 2 | Extend existing El/PR evidence spine to material breakdown using the already-specified SA-2 manual Bridge contract; retain deterministic observations separately from proposed interpretations. | E07/E08/E24 | Every material proposal has source scene/span, method/version and review state; quantities are explicit or labeled estimates; unknown is not satisfied and not an indiscriminate hard failure. |
| 3 | Add confirmed production decisions and the minimum film schedule from those same scenes/requirements: real locations/sets, appearances, units, work capacity, moves, restricted work, actual-schedule precedence. | Sc/Ch/LR/PR/PA + E19/E20/E22 | Workday/cast/location/equipment quantities reconcile to the scene graph and constraints. A stored schedule document or default 30 days is not acceptance. |
| 4 | Connect schedule/requirement quantities into existing budget/cost owners; keep actual source budgets separate from generated estimates and source every quantity×rate×duration. | Existing Budget/BudgetLine, E22/E26 | No held-out leakage; estimates retain assumptions/ranges and reuse the canonical downstream evaluator, not a second calculator. |
| 5 | Add jurisdiction-sensitive content review and story-preserving production alternatives over the same reviewed graph; reuse existing feasibility, treaty, cultural and component-routing consumers. | E12–E15/E20–E24 | Proposed change identifies affected scenes, cost/schedule delta, uncertainty and producer decision. No speculative censorship flag silently removes independent economics. |

This is a reuse/extension map for master-engineer reconciliation, not approval to implement or a UI redesign. Architecture/build-discipline skills informed the reuse-first, end-to-end verification boundary; historical standalone-rendering instructions were not applied to this read-only repository audit.

Production code changed: **NO**. Frontend changed by this audit: **NO**. Database changed: **NO**. External research: **NO**. Broad tests: **NO**. Commit/push: **NOT REQUESTED / NOT PERFORMED**.
