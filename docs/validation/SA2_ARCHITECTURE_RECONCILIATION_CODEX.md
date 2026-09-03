# CineGlobe SA-2 Architecture Reconciliation — Codex

Date: 2026-09-03. Status: PROPOSED; independent architecture recommendation, not implementation acceptance.

Repository: surajgohill-oss/Frametax. Branch: claude/audit-frametax-features-NZcX5. Application inspected: frametax2/. Code baseline: e42e28d7af7dd6af00d3f7518215e14f36b720b2. The working tree already contained unrelated frontend changes, a staged test rename, and untracked material; none is part of this handoff.

Scope: repository/history inspection, bounded read-only database inspection, official Movie Magic documentation research, and this document only. No application changes, migrations, database population, test execution, browser/UI interaction, incentive research, or optimizer audit. The FrameTax build-discipline skill informed reuse and end-to-end evidence checks; the architecture skill informed alternatives and trade-offs. Their generic templates do not override this task's scope.

## 1. Executive conclusion

**CineGlobe needs a reviewable production-plan input layer, not a second optimizer and not a Movie Magic clone.** Its downstream engine already prices account-coded budgets, allocates expenditure, evaluates program rules, composes structures, normalizes costs, and calculates NPC. Its upstream analyzer currently supplies structural observations and limited physical/cultural signals—not a production schedule or quantity-driven budget.

The minimum credible architecture has three separate truths: what the script depicts; how the producer elects to make it; and what that plan costs and qualifies for. Link these through versioned IDs and evidence. Never convert a narrative location directly into a shooting jurisdiction, an animal mention into paid animal-days, or a speaking character into an employed performer.

Recommended SA-2: material production breakdown, evidence/review protection, current-version selection, effective assumption resolution, and a thin schedule/quantity-to-existing-budget contract with a bounded end-to-end proof. Accept imported or producer-confirmed planning inputs; do not add automatic scheduling, a full budget authoring system, or global rate acquisition. Full production-informed scheduling remains SA-3; broad L2/L3 estimating remains later work.

Five architectural decisions:

1. Reuse existing Scene, Character, ExtractedScriptElement, ProductionRequirement, ProjectLocationRequirement, ProjectFact, ProductionAssumption, BudgetDocument/BudgetLineItem, ProductionStructure, and StructureCalculationResult. Extend their relationships; do not make parallel canonical inventories.
2. A production plan needs day/unit/scene-resource assignments and constrained durations internally, even if Movie Magic supplies them. A stripboard UI is optional; internal plan semantics are not optional when claiming schedule-aware execution.
3. Preserve imported budget amounts. Add a traceable calculation basis only where supplied or approved; no decomposition of an opaque total into invented rates and quantities.
4. Reuse the canonical evaluator and its eligibility/economic distinction. Uncertain script interpretation must not silently remove jurisdictions or invent qualifying dollars.
5. Incrementally invalidate upstream dependencies; publish a coherent economic generation. Do not implement partial candidate-result reuse until its dependency coverage is proven.

Independent conclusion was recorded before opening the Gemini/AG proposal. Section 15 compares the remotely retrieved historical review and identifies its age; no newly published SA-2-specific AG proposal was found on the inspected shared branch.

## 2. Verified current implementation state

Evidence labels are scoped, not interchangeable: IMPLEMENTED means executable code exists; TESTED identifies retained historical execution evidence, not a current pass; TEST COVERAGE PRESENT means test bodies exist and were inspected but were not executed here; RUNTIME VERIFIED means the stated local read-only observation occurred; DOCUMENTED ONLY means a proposal/claim without that implementation; PROPOSED means this report's recommendation; ABSENT means no matching implementation was found in the inspected application and relevant history. A historical green gate does not prove current runtime correctness.

### Source register

Links pin the reviewed code, so this report remains auditable after the shared branch moves.

| ID | Canonical source and relevant owner |
|---|---|
| R01 | [Document and DocumentVersion](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/models/library_document.py), [ingestion commit](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/api/v1/ingestion.py), [material routing](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/services/material_routing.py) |
| R02 | [Structural parser](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/ingestion/screenplay_structural_parser.py), [PDF extraction](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/ingestion/pdf_extractor.py) |
| R03 | [Script analysis service](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/services/script_analysis_service.py): resolve_active_screenplay, parse_and_persist, persist_derived_facts, build_requirements |
| R04 | [Screenplay/Scene/Character/Element models](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/models/screenplay.py), [requirements/assumptions](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/models/production_requirement.py), [location requirements](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/models/project_location_requirement.py) |
| R05 | [ProjectFact](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/models/project_fact.py), [ProjectActivity](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/models/project_activity.py) |
| R06 | [SA-1 state builder](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/services/canonical_production_state.py), [handoff adapter](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/services/optimizer_handoff.py) |
| R07 | [Budget models](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/models/budget.py), [budget parser](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/ingestion/budget_parser.py) |
| R08 | [Canonical economic input assembly](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/services/canonical_project_economics.py): ProjectEconomicInputs, build_project_economic_inputs, build_physical_requirements |
| R09 | [Served evaluator](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/services/canonical_evaluation.py): ENGINE_VERSION canonical-1.52.0; evaluate_project, _compute_fingerprint, _relocation_normalization |
| R10 | [Account allocation](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/calculators/production_allocation.py), [allocation pricing](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/calculators/allocation_pricing.py), [qualification ladder](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/calculators/qualification_derivation.py) |
| R11 | [Production normalization](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/calculators/production_normalization.py), [production adjustment](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/calculators/production_adjustment.py) |
| R12 | [Cost/fringe models](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/models/cost.py), [legacy fringe helper](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/calculators/apply_union_fringe_rules.py) |
| R13 | [Role/cultural adapter](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/calculators/canonical_role_qualification_bridge.py), [physical requirements](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/calculators/production_requirements.py) |
| R14 | [ProductionPackage/question engine](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/calculators/production_package_intelligence.py), [Bridge schema](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/bridge/schema.py) |
| R15 | [Production structures/results](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/models/production.py), [served view](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/services/canonical_production_view.py), [workspace view](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/services/project_workspace_view.py) |
| R16 | [SA-1 tests](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/tests/test_script_analyzer_sa1.py), [canonical evaluator tests](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/tests/test_canonical_evaluation.py), [Movie Magic parser tests](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/tests/test_movie_magic_budget_parser.py) |
| R17 | [Held-out guard](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/validation/holdout_guard.py), [real-production corpus](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/frametax2/backend/app/validation/real_production_corpus.py) |

### Implementation matrix

| Capability | Evidence status | What is actually present / limit |
|---|---|---|
| Library versioning and typed projections | IMPLEMENTED; relevant tests exist; local current-version relationships RUNTIME VERIFIED | Documents/checksums/current flags/supersession links, screenplay and budget projections. Version selection is not consistent across every consumer. R01/R03/R08. |
| Structural SA-1 | IMPLEMENTED; TESTED historically in the SA-1 closeout; persisted FVD output RUNTIME VERIFIED | Parser sa1-structural-1.1.0, scenes/cues/limited lexical elements; not professional semantic interpretation. Current test coverage inspected, not rerun. R02–R04/R16. |
| Production Record | IMPLEMENTED as related models and assembled views | Not a single authoritative ProductionRecord table. ProjectFact owns current scalar facts; ProjectActivity owns history; source documents, requirements, people, budgets and results are separate domain owners. R01/R04–R06/R15. |
| Budget intake and classification | IMPLEMENTED; TEST COVERAGE PRESENT; FVD stored amounts RUNTIME VERIFIED | Amount/account-oriented CSV and Movie Magic-style PDF/text parsing; no complete MMB calculation graph. R07. |
| Generic optimizer execution | IMPLEMENTED; TEST COVERAGE PRESENT | Live route uses canonical_evaluation, not the old project-specific runner or SA-1 handoff dataclass. No re-evaluation executed in this audit. R08–R10/R16. |
| Physical script signal | IMPLEMENTED, limited | Scripted-location keyword abstraction plus period presence. Feasibility disclosure is separate from economic discovery. R08/R09/R13. |
| Rich cultural facts from SA-1 | EXISTS BUT DISCONNECTED / ABSENT by field | Adapter expects location/environment/language/cultural_reference; SA-1 emits scripted_location and does not extract the latter semantics. R13. |
| Production assumptions | IMPLEMENTED schema/scaffold; not active planning engine | Local table has zero rows. Presence of intended_shoot_days/unit fields is not schedule implementation. R04/R06. |
| Rate/quantity adjustment patterns | IMPLEMENTED; test coverage exists | Existing travel/local-cost adjustments have quantities and rate traces, but generic normalization instantiates crew/budget defaults; not script-derived staffing. R11. |
| Union/fringe support | PARTIALLY IMPLEMENTED | Rule model and legacy percentage helper exist. Helper reads a cap but does not apply it. Neither is evidence of a live per-person contract/payroll engine. R12. |
| Schedule, ShootDay, ProductionUnit, DOOD/availability engine | ABSENT in filmmaking application; DOCUMENTED ONLY in prior architecture | No matching live public database tables; source/history searches found no filmmaking scheduler. Root sibling scheduler concerns event-marketplace polling, not production. |
| L1/L2/L3 script-to-budget estimator | DOCUMENTED ONLY | Current evaluator explicitly requires a real parsed budget; it does not estimate one. R08. |
| AI material breakdown and script Bridge | DOCUMENTED ONLY / reserved | Existing Bridge reserves SCRIPT_PRODUCTION_ANALYSIS; a reservation is not an implemented ScriptAnalysisPackage/Response workflow. R14. |
| Review/lock/delta propagation for breakdown | PARTIAL fields, ABSENT complete workflow | Review fields exist; reparse deletes this projection's scenes and derived requirements. No complete durable review/scene-line dependency system. R03/R04. |

Read-only runtime observation, 2026-09-03: SQL transaction explicitly set READ ONLY and rolled back. FVD project 6c6f1c13-2d49-4bbc-bafb-2a12efa93112 has current screenplay 02858959-0858-4d01-bd9c-ff65c1ff8d67, source version d25b035b-dc6f-471a-a611-6ed397444889, 99 scenes, 38 character rows, 1,703 elements, 100 reported pages and 796 eighths. These are parser outputs, not independently approved production counts. Across the local element table, all 3,280 rows were DETERMINISTIC_PARSE; none had quantity or review_state populated. ProductionAssumption count was zero; no schedule/shoot-day/production-unit tables were found.

FVD's current budget projection 29419055-9720-4e77-a673-020e3a87e3c8 links source version cf33eae1-aa4e-4e4e-80d2-ce737f5a373e. It stores USD 4,517,687 across 34 rows with the same summed USD amount; parser budget-1.3.0+rules.896907b5f1b3. This verifies stored budget reconciliation, not its original detailed quantities or a schedule-derived estimate. No mutating parse/evaluate/state endpoint was invoked.

Relevant history: 242226d introduced SA-1; fe59612 connected Library routing; 034c8de reconnected generic script physical inputs; 3665c52 cut over served pricing; d2106b2 connected retrospective analysis to Evaluate; e811d18 normalized locations; 380ecd9 restored co-production/component enumeration and connected relocation economics. Do not repeat the obsolete claim that the generic downstream path is absent.

## 3. Existing SA-1/SA-1.5 contract

The [canonical architecture](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/docs/validation/SCRIPT_ANALYZER_CANONICAL_ARCHITECTURE.md) proposed a larger initial slice than shipped. The [SA-1 closeout](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/docs/validation/SCRIPT_ANALYZER_SA1_CLOSEOUT.md) explicitly deferred scheduling, estimating, rates, AI and confirmation UX. The [SA-1.5 closeout](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/docs/validation/SCRIPT_ANALYZER_SA1_5_CLOSEOUT.md) claims a generic FVD gate; the [contemporary independent rejection](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/docs/validation/CODEX_SA1_5_INDEPENDENT_VERIFICATION.md) identified then-missing wiring. Later code supersedes several rejection findings. Neither historic gate creates a current scheduling capability or requires restarting SA-1.5 wholesale.

| Existing output | Useful present consumer | Boundary / missing link |
|---|---|---|
| ScreenplayDocument: source version, parser version, input hash, parse state, page basis | Parse idempotency, script/workspace summaries | Not stable cross-revision scene identity. Successful parse is not professional breakdown acceptance. |
| Scene: sequence/source number, heading, INT/EXT, TOD, scripted location/key, span/pages/eighths | Summary/structural API, element provenance, location aggregation | No work assignment, shooting day, physical site, or schedule duration. Eighths use text density, not reliable geometric fractions. |
| Character: name/aliases, speaking flag, scene sequences, dialogue blocks/words/burden | Cast-like script inventory, summary | Fictional character, not hired actor. Non-speaking presence and cue false positives need review; burden is not paid days. |
| ExtractedScriptElement: 12-key objective subset and evidence span/hash | Requirement aggregation; some cultural lookup infrastructure | Taxonomy: SCENE, INT_EXT, DAY_NIGHT, SCRIPTED_LOCATION, CHARACTER, DIALOGUE_ROLE, EXPLICIT_VEHICLE, EXPLICIT_ANIMAL, EXPLICIT_WEAPON, EXPLICIT_MINOR, EXPLICIT_PROP, PERIOD_REFERENCE. No inferred stunt/VFX staffing or operational scale. |
| Quantity/range/unit/confidence/review/supersession fields | Scaffold | Unpopulated in observed SA-1 output. Do not call them delivered quantity intelligence or a review system. |
| Twenty script_* ProjectFacts | Canonical state and disclosure | Aggregates copy derived information; treat as projections, never competing scene truth. USER_OVERRIDE protected; general confirmed-value precedence needs stronger handling. |
| ProductionRequirement | Evidence aggregation by taxonomy/value, scene sequences/count/sample | Quantity/unit null; no cost-driver-to-budget-line relation. Use as canonical requirement/resource identity, not another inventory. |
| ProjectLocationRequirement | Recurrence/INT-EXT/TOD/eighth summaries, physical keyword bridge | production_approach UNKNOWN and production_location null; unrelated category override rows share table. Do not duplicate as a third location taxonomy. |
| ProductionAssumption | Old state/handoff reads key/value/unit/range | No populated producer planning workflow in inspected local runtime; scope/version uniqueness must be established before globals use. |
| CanonicalProductionState / ProductionOptimizerInput sa1-1.0.0 | Script-analysis API contract | Carries budget lines, requirements, assumptions, versions and provisional flag; no first-class currency. Not the object orchestrating current canonical evaluation. |

Dead/disconnected means no effective consumer in the relevant current calculation path, not permission to delete: quantity/review scaffolding, schedule assumptions in the old handoff, cultural vocabulary mismatch, and generic ProductionPackage script attributes are distinct cases. The older coarse screenplay parser and ProductionPackage remain compatibility infrastructure; replacing the structural parser with another model would add a third interpretation path.

## 4. Existing downstream engine contract

Current route: evaluation/begin → canonical_evaluation.evaluate_project → build_project_economic_inputs → real project budget/facts → canonical discovery/composition/allocation/qualification/pricing → StructureCalculationResult → canonical_production_view. Evaluate can trigger script analysis before reading script facts; it reuses matching fingerprint + engine-version results or persists a new generation. R08/R09/R15.

ProjectEconomicInputs contains project identity/type/base jurisdiction, declared gross budget and separate leaf sum, BudgetLine list, category mapping, stated outside-jurisdiction/offshore-payroll account sets and their knowledge states, budget document ID, contingency utilization, incremental financing and source-budget financing. BudgetLine contains line_id, account_code, description, amount_usd, spend_category, is_memo. It does **not** contain resource quantity, unit rate, work dates, shoot-day IDs, scene IDs, or approved plan revision.

| Budget capability | Actual current representation | SA-2 implication |
|---|---|---|
| Quantity | Not a BudgetLineItem/ParsedLineItem first-class field | Extend calculation basis; reuse requirement quantity fields. Do not equate amount_raw with quantity. |
| Rate | No line unit-rate/formula field; BudgetDocument.rate_base is descriptive | Preserve source/quote rate and unit separately from monetary total. |
| Units | Currency exists, physical/time units do not exist on budget lines | Add dimension-checked basis and rate unit; unit conversions must be explicit. |
| Globals | No budget expression/global graph; ProjectFact/ProductionAssumption scaffolds exist | Use scoped/versioned effective assumption references, not a second generic global fact table. |
| Fringes | PAYROLL_FRINGES category, cost benchmark fields, UnionFringeRule and old helper | Preserve already-loaded fringe dollars. Do not add another flat percentage; existing helper is not cap-correct payroll proof. |
| Contract terms | Compensation CASH/deferred/equity/in-kind and fixed/labor/residency flags | These are not hold/drop, overtime, minimum-call, turnaround or per-employee aggregation rules. |
| Qualifying status | Candidate bool and qualifying amount fields; authoritative current result comes from per-program qualification register/segment trace | No universal line-level qualifies flag can replace program + territory + date + treatment context. |
| Jurisdiction allocation | StructureSpec routes/splits; AccountAllocation has line_id, amount, component, destination, assignment kind/reason | Reuse allocator. Account code is classification, not identity; splits and future sublines must retain line lineage and conserve dollars. |
| Scenario changes | ProductionStructure, StructureSpec, persisted economic snapshots/traces | Already exists for economic structures; lacks script-plan edits and duration-dependent budget propagation. Add plan/basis references, not a rival scenario engine. |
| Parser fidelity | CSV description/amount/department; film PDF account totals and loaded totals | R07 does not retain MMB globals, multipliers or formulas. Generic material routing handles CSV/PDF/text; the legacy budget API's .xlsx suffix acceptance still calls the CSV parser, not a real workbook importer. |

The allocation path uses the existing qualification ladder for each partition, then the existing rate/cap/requirements, stack and treaty interfaces. Its fields include selected_incentive_usd, total_incentive_floor_usd, npc_verified_usd, npc_with_adjustments_usd, segment register_trace and requirement_trace. The selected incentive is the modeled figure, not necessarily the floor; do not copy stale module comments as calculation authority.

Current allocated-structure formula (R10, price_allocated_structure):

~~~text
npc_verified = gross_budget - selected_incentive
               + incremental_financing + implementation_cost
npc_with_adjustments = npc_verified + travel_delta + FX_delta
                      + in_kind_replacement_delta + local_cost_delta
~~~

Schedule-driven costs must enter either a scenario's budget basis or a clearly non-overlapping incremental adjustment—not both. Finance already in source gross is not added again. These are interface constraints, not a new review of the incentive math.

The current physical requirement pass is deliberately advisory; economic discovery uses a separate empty-physical-requirements pass. Existing cultural/treaty/requirements bridges consume typed facts, not prose. SA-2 must feed those owners, not build a new worldwide country filter.

## 5. Missing production primitives

| Primitive | Why it matters | Minimum delivery boundary |
|---|---|---|
| Stable logical identity plus revision occurrences | Inserted/renumbered/split/merged scenes cannot preserve identity by sequence/offset hash alone | SA-2: stable references, explicit cross-draft mapping/ambiguity and review-safe reparsing. |
| Typed scene-resource membership | One recurring animal/prop/location is not a new purchased resource each mention | SA-2: reuse requirements/characters; link scene evidence by ID and record quantity semantics. |
| Execution approach | Same script may be practical, stage, tank, plate, VFX or hybrid | SA-2: producer-elected, scenario-scoped assumption; alternative suggestions are not facts. |
| Unit/day/work assignment | Paid workdays, shared resources, moves and date feasibility depend on grouping | SA-2 thin import/confirmed-plan contract; SA-3 robust planning and generation. |
| Availability/events and work rules | Cast, sites and crew cannot be assumed available; time windows change feasibility | SA-2 capture/source/validate supplied constraints; SA-3 scheduling solution. |
| Shoot time versus story time versus paid time | Pages, screen minutes, elapsed shoot time and contractual paid hours differ | SA-2 explicit units/basis/unknowns; no fixed pages-to-days conversion. |
| Budget calculation basis and coverage | Cost impact requires quantity/rate provenance and knowledge of what source totals already include | SA-2 narrow mapped drivers; later broad estimator. |
| Effective review state and dependency manifest | Unreviewed interpretation must not silently become executable economics | SA-2 prerequisite; extend current evidence/fingerprint path. |
| Correlated uncertainty/calibration | A range is not automatically a statistical quantile | Carry alternatives and bounded assumptions now; probability calibration later with held-out evidence. |

## 6. Movie Magic benchmark matrix

Official EP manuals/product guidance accessed 2026-09-03. These describe production-software semantics, not legal labor/incentive authority. Software defaults must never become worldwide legal or production defaults.

| Concept | Verified benchmark | CineGlobe architectural inference / scope |
|---|---|---|
| Scene breakdown | Headers distinguish set, physical location, script day, pages, shoot time and unit. [MMS scene header](https://mms-docs.ep.com/Breakdown/SceneHeaderInformation.html) | Preserve those distinctions; retain existing Scene identity and source spans. |
| Elements | Breakdown import links detected/tagged elements to sheets. [MMS import](https://mms-docs.ep.com/Breakdown/ImportingBreakdownSheets.html) | Canonical resource plus scene-occurrence relations; no mention-count payroll. |
| Stripboard | Boards/sub-boards arrange scheduled work; separate calendars support units. [MMS support](https://www.ep.com/support/movie-magic-scheduling/) | Ordered assignments are needed internally; graphical board design is not SA-2. |
| Shooting days/calendars | Calendar expresses planned work, off-days and events. [MMS calendar](https://mms-docs.ep.com/Calendars/Calendar.html) | Date or relative day, working week and exceptions; unknown dates stay unknown. |
| Multiple units | Independent sub-board start dates support concurrent units. [MMS product](https://www.ep.com/movie-magic-scheduling/) | Unit reference required; two unit-days are not necessarily two elapsed production days. |
| Cast/resource availability | Red flags and scheduling constraints are distinct from resource conflicts. [MMS conflicts](https://mms-docs.ep.com/Calendars/ConflictHandling.html) | Store sourced availability windows; unknown availability is not confirmed available. |
| DOOD | Day/resource usage distinguishes work, hold, drop/pickup and event types. [MMS DOOD](https://mms-docs.ep.com/DayOutofDays/DayOutofDays.html) | Need reproducible resource-day exposure for costs; defer full report parity and unsupported contractual pay rules. |
| Conflicts | Current detailed manual defines cross-sub-board same-day active-element conflicts; events do not themselves trigger that conflict type. [MMS conflicts](https://mms-docs.ep.com/Calendars/ConflictHandling.html) | Do not infer full labor-compliance enforcement from marketing. CineGlobe checks declared constraints independently. |
| Company moves | Company travel days alter available shooting dates. [MMS travel days](https://mms-docs.ep.com/Calendars/CompanyTravelDays.html) | Separate full travel days from intra-day moves; carry time/cost evidence, not a generic penalty. |
| Day length | Shoot Time differs from Screen Time; estimated day length is exposed on calendar/report. [MMS headers](https://mms-docs.ep.com/Breakdown/SceneHeaderInformation.html), [release notes](https://mms-docs.ep.com/ReleaseNotes.html) | Require typed minutes/hours and setup/move/break components; a script page count is not a duration guarantee. |
| Quantity/rate/multipliers | Detail columns carry amount, multipliers, rate, units and currency. [MMB columns](https://mmb-docs.ep.com/Budget_Navigation/columns.html) | Add line basis to existing budget objects, not a replacement ledger. |
| Globals | Named values/expressions propagate to dependent calculations. [MMB globals](https://mmb-docs.ep.com/Setup/globals.html) | Reuse scoped assumptions; explicit dependencies and cycle checks. |
| Fringes/units | Fringes have rate/unit/cutoff; time-unit equivalence affects flat fringes. [MMB fringes](https://mmb-docs.ep.com/Setup/fringes.html), [MMB units](https://mmb-docs.ep.com/Setup/units.html) | Preserve rate base, employee/group scope, caps and unit conversion. MMB's example day-hours are not CineGlobe defaults. |
| Contractual charges | MMB charges may be flat or percentage-based with exclusions. [MMB charges](https://mmb-docs.ep.com/Setup/charges.html) | Distinguish budget charges from CBA employment terms; do not claim one implements the other. |
| Schedule-budget propagation | Active-sub-board export supplies element worked-day quantities to MMB. [MMS export](https://mms-docs.ep.com/ScheduleFiles/ExportingScheduleData.html) | Transfer quantities with provenance; no evidence here of arbitrary bidirectional CineGlobe live synchronization. |
| Scenario budgets/revisions | Comparison operates on matching accounts; versions create separate budget copies. [MMB comparison](https://mmb-docs.ep.com/Comparison/Comparison_Overview.html), [MMB versions](https://mmb-docs.ep.com/History_Versions/versions.html) | Preserve source revisions and compare derived overlays; CineGlobe need not copy MMB's UI or whole-budget duplication strategy. |

## 7. Proposed canonical data model

PROPOSED logical model, not a migration specification. The complete internal target below can be delivered in stages; Section 16 fixes the SA-2 subset. Relationships with real identity/constraints need typed references, not name matching or arrays of duplicated scene payloads.

~~~text
DocumentVersion -> AnalysisRevision -> Scene occurrence / Character occurrence
                              |         | evidence
                              +-> ExtractedScriptElement -> ProductionRequirement
                                                           |
ProjectFact + ProductionAssumption -> ProductionPlanRevision|
                                      |                    |
                                      +-> Unit -> Day -> WorkAssignment
                                      |              \\-> ResourceEvent / constraint
                                      +-> BudgetLine basis <-> source BudgetLineItem
                                                    |
                              same ProjectEconomicInputs / StructureSpec
                                                    |
                              same allocation -> QPE -> incentive -> NPC
                                                    |
                              same persisted result generation/recommendation
~~~

| Owner | Reuse/extension or necessary new concept | Identity and minimum content |
|---|---|---|
| Document/DocumentVersion | REUSE | Source checksum and current pointer; imported script/budget/schedule remain distinct documents. Never duplicate original files as separate truths. |
| AnalysisRevision | NEW thin run manifest | Source version ID; parser/model/schema/taxonomy versions; input hash; completion/validation state. Needed to preserve multiple analyses of the same draft without destructive replacement. Not another script table. |
| Scene/Character | EXTEND | Stable logical ID plus analysis-specific occurrence, source number/span/content hash; explicit one-to-many split/merge/continuation mapping. Unknown cross-draft correspondence stays unresolved. |
| ExtractedScriptElement | EXTEND existing scene-observation owner | Analysis/scene/resource references; fact versus interpretation, span/hash, proposal alternatives, quantity semantics and review provenance. Append observations; no provider-specific competing truth tables. |
| ProductionRequirement | EXTEND as reusable requirement/resource identity | Typed resource, scope and linked supporting observations; distinguish resource count, occurrence count, concurrent maximum and resource-days. Add joins to scenes/evidence rather than another ProductionElement inventory. Character remains its own entity; link instead of copying. |
| ProjectLocationRequirement | EXTEND | Script setting/requirements retained here. Scenario-scoped execution assignment references this ID, chosen approach, existing jurisdiction ID and a plan-local physical-site identity. No global location catalog required in SA-2. |
| ProjectPerson/TalentProfile | REUSE; small casting relation when supplied | Explicit fictional-character-to-real-performer assignment. Employment/residency evidence remains personnel truth, not a Character attribute. |
| ProjectFact/ProjectActivity | REUSE | One current project-level fact plus append-only change audit. Do not repurpose as an immutable full historical graph. |
| ProductionAssumption | EXTEND | Typed value/unit/range; subject and plan-revision scope; source/reviewer; replacement link. Effective uniqueness per key/subject/scope. Globals alias these IDs. |
| ProductionPlanRevision | NEW thin immutable selection manifest | Project, parent revision, selected script analysis, budget version, optional schedule source, selected assumptions/reviews and dependency digest. No duplicate budget/scene arrays as independently editable truth. Link from existing ProductionStructure/results. |
| Unit / Day / WorkAssignment | NEW minimal schedule concepts | Unit identity; relative day and optional local date/timezone; work/off/travel classification; ordered assignment referencing scene or scene-part, physical assignment, duration basis and required resources. Separate narrative sequence from work order. |
| ResourceEvent/Constraint | NEW scoped relation, not a second fact registry | Resource/person/site/unit reference, availability or event window, capacity, precedence/hardness, applicable term/evidence reference. Same event shape for rehearsal/fitting/travel/hold/release; never infer paid status just from presence. |
| BudgetLineItem + calculation basis | EXTEND budget domain | Existing source line ID, optional parent/detail identity, monetary amount/currency, fixed/imported/calculated mode. A CostDriver/basis record links quantity/unit/duration/rate/term/FX references and versioned deterministic formula. Source-only opaque totals remain intact. |
| Cost/fringe/contract references | REUSE cost domain, extend supported terms | Reference existing benchmark/rule or versioned quote/contract source. Missing terms remain unknown; do not make a second worldwide rate registry. |
| Dependency/effective selection metadata | SMALL shared infrastructure | Input IDs + revisions + calculation version/hash; review state and invalidation reason. Existing observations, ProjectActivity and result snapshots remain owners, not a new duplicate EstimateEvidence warehouse. |
| ProductionStructure/StructureCalculationResult | REUSE | Scenario structure and result generation, plan/budget basis IDs and manifest, segment traces and current economic fields. |

Normalized identities do not prohibit immutable calculation snapshots. Snapshots record exactly what was used for reproducibility; they are read-only evidence, not editable second sources. A single plan revision may feed many worldwide structures, avoiding copies of the screenplay for every jurisdiction.

## 8. Scheduling-engine boundary

**Own a small plan validator and quantity projector; initially import or accept the plan.** A no-schedule project can still receive existing budget-based economic comparisons, explicitly not schedule-verified executable options. Missing dates do not prevent relative-day arithmetic; they do prevent date-specific availability/timing claims.

| Feature | Required internally? | Build versus import |
|---|---|---|
| Complete stripboard UI | No for SA-2 or the pricing contract | Defer; receive ordered assignments and expose an auditable structured result later. |
| Strip/work ordering | Yes | Preserve imported/confirmed order; validate it. Automatic reorder/packing belongs SA-3. |
| Day grouping | Yes for day-dependent estimates | Source day/unit grouping or approved plan, never divide all pages by one constant and call it a schedule. |
| DOOD | Minimal day-use derivation yes; full payroll/report engine no | Distinct resource workdays and first/last use can be derived. Hold/release/travel/fitting require explicit events/terms; unknown paid-hold policy is a cost gap. |
| Availability | Yes for execution qualification | Sourced windows and conflicts; do not invent availability. Leave unsupported contracts to producer/imported result. |
| Company-move penalties | Yes when moves alter the compared plan | Store estimated/imported duration and cost separately, travel versus setup versus idle time. No universal move surcharge. |
| Multi-unit constraints | Yes in the contract | Sum unit-days separately from elapsed days; shared resource conflict checks. Do not silently flatten an imported second unit. |
| Estimated day lengths | Yes for schedule-aware feasibility/cost | Sum evidenced work/setup/move/break durations; explicit uncertainty. Later scheduler may propose alternatives. |

For a resource appearing in several scenes on one day, count the applicable workday once, not once per scene. Distinct simultaneous requirements may require additional physical resources, but a second named appearance does not prove that concurrency. A scene spanning two days/units needs work-part identity and coverage, not an accidental duplicate scene.

No magic duration inference: a quoted fee may be flat, day, week, guaranteed minimum, or packaged. The contract selects the basis; DOOD alone cannot decide payment. No union limits, minor-hours rules, overtime or turnaround rules are invented or researched in this task. Capture their sourced applicability; run only supported deterministic checks.

## 9. Script→budget propagation

Proposed chain: reviewed scene evidence → reusable requirement → selected production approach → approved/imported work assignments → resource/day quantity → existing budget line's calculation basis → scenario budget view → current economic input adapter. An observation proposes an impact; it does not directly write a cost.

Use three line modes in the same budget domain: SOURCE_FIXED_AMOUNT; CALCULATED_FROM_SUPPORTED_BASIS; UNKNOWN_BASIS. An opaque imported account can be compared financially but cannot be rescaled by schedule without decomposition/confirmation. A producer can elect a new scenario amount while preserving the source amount.

Before adding a driver, record coverage: source line already includes this resource; this replaces part/all of that line; or this is genuinely additional work. Parent/detail roll-up is counted once. A script-detected vehicle does not add a vehicle line if its cost is already inside transportation or an approved package.

Bounded example, illustrative arithmetic only—not a project estimate: a confirmed rental basis of two units × three chargeable days × 100 currency-units per unit-day yields 600. Reassigning several scenes within those same three days changes no cost. Adding one approved chargeable day changes the basis to 800, a 200 delta. No qualifying fraction or payroll fringe follows unless the existing program/territorial/contract inputs support it.

Reuse R11's quantity/rate traces and travel interfaces but supply real selected manifests instead of relying on their defaults. Record what a source total already includes; suppress overlapping travel/local-cost/fringe adjustments when the scenario budget already contains those amounts. Fixed cast and global package costs remain fixed unless the producer changes the actual contract basis.

Unknown rate or duration yields a missing-driver statement or explicitly labeled bounded option, not zero, not a fabricated money amount, and not a statistical P50. This does not erase known source-budget dollars from ordinary economic comparison.

## 10. Script→jurisdiction propagation

Keep four axes separate: narrative setting; required production capability; elected place/method of production; legal qualifying-expenditure facts. They may correlate but are not synonyms.

1. Current reviewed requirements → existing physical capability adapter. A marine narrative scene can lead to practical, tank, stage or VFX alternatives; it is not proof that all production must occur in a coastal jurisdiction.
2. Selected physical/post work assignments → existing StructureSpec component/account routes and allocations, with line identity and conservation. Dollar fractions derive from approved work/cost assignments or explicit producer elections, not scene percentages assumed to equal budget percentages.
3. Territorial facts → existing program_spend_rules and qualification_derivation. Separate service-performed geography, goods-use geography, relevant worker residency, contracting/vendor entity and payer. A plan's SPV/payment route is not proof of actual qualifying expenditure.
4. Reviewed story/language/cultural assertions → canonical_role_qualification_bridge through explicit vocabulary mapping and source IDs. Existing SA-1 scripted_location must not be mechanically relabeled as a verified cultural qualification answer. Fictional character nationality never becomes actor nationality.
5. Employment, entity, ownership, production dates and certificates → existing role/requirements/treaty bridges. Narrative extraction cannot attest corporate residence or official approval.

Preserve current canonical program/rate/spend/requirements/stack/treaty owners from PROJECT_RULES. No new incentive database. Preserve the INCLUDE default for existing spend unless canonical program authority limits it; missing evidence for newly invented expenditure is a different issue. Separate economic candidacy from plan feasibility and production acceptance. An unknown capability profile or ambiguous script cue must not recreate the jurisdiction-count collapse by removing otherwise evaluable candidates.

For executable-plan recommendation, a confirmed hard conflict or material unresolved assumption is an explicit plan-level gate. Retain the economic comparison and show why that plan is not execution-cleared; do not represent this as a program becoming legally non-priceable.

## 11. AI/deterministic boundary

Improve the preferred rule to: **AI proposes interpretations; source validation and authorized review select effective facts; canonical records retain evidence; deterministic engines calculate.** Canonical persistence alone must not promote an assertion to truth.

| Operation | Owner / containment |
|---|---|
| Known-format extraction, IDs, spans, checksums, basic structure | Deterministic parser. AI fallback may propose difficult segmentation, never silently replace a sound parse. |
| Contextual stunts/VFX/crowds/period/vehicles/animals/minors/production burden | AI may propose typed, source-grounded observations and alternatives. Distinguish depicted action from dialogue, negation, metaphor, off-screen events and possible execution methods. |
| Scene/resource identity matching | Deterministic candidates plus AI suggestions for ambiguity; review split/merge mappings that affect material dependents. |
| Quantities stated in script | Extract with units/context and evidence; stated crowd size is not automatically background hires. |
| Shoot days, staffing, equipment quantities | Source/import or explicit assumptions. AI may suggest a scenario, not claim these are objective facts. |
| Rates, FX, QPE, cultural points, treaty shares, caps, incentive, NPC and rank | Existing deterministic owners using supported inputs; AI cannot invent values or certify legal qualification. |
| Story-preserving practical/VFX alternatives | AI proposal only, producer approval before plan selection. No silent rewriting of creative intent. |

Extend the existing Bridge contract, if used, with exact project/source/analysis hashes, typed assertions, scene/evidence references, alternatives and parser/model/prompt/schema versions. Reject cross-project IDs, unsupported fields, invalid spans, stale packages and economic-rate assertions. Store rejected/conflicting proposals for audit without activating them. Multi-model agreement is not authority and should be requested only for material disputed interpretation; do not run every provider on every scene by default.

Prompt injection in screenplay text or imported budget notes is data, not an instruction to alter rules, contact providers, or execute formulas. Budget expressions use a restricted arithmetic representation, never eval, macros or arbitrary code.

## 12. Human-confirmation model

Reuse ProductionPackage's MissingInput/question concepts and ProjectFact/ProductionAssumption persistence; add materiality and dependency references. Do not create another standalone intake questionnaire.

Questions arise only when an unresolved input can change feasibility, required schedule/work, qualifying spend, incentive, NPC or recommended structure. First attempt resolution from selected source documents, existing confirmed values and deterministic relationships. Then evaluate bounded alternatives using existing calculations where inputs are supported.

Ask in this order: a hard feasibility/eligibility conflict; an uncertainty capable of changing the preferred structure; a material spend/time/qualification difference; remaining useful detail. Deduplicate by resource/decision across scenes and jurisdictions. Group identical scene decisions only when the producer can inspect the affected set and exceptions.

Question record: subject ID; disputed assertion; source references; affected scenes/lines/structures; alternatives; explainable impact or UNKNOWN impact; answer scope; reviewer; revision. No dollar impact should be fabricated merely to prioritize a question. Safety/feasibility questions remain material even when monetization is unknown.

Example: “For these linked water scenes, is the intended approach practical sea work, controlled tank/stage, or VFX/hybrid?” Once approved, use the single scoped assumption for all covered dependencies. Follow-up asks location or quantity only if still necessary. Do not ask the producer to confirm every lexical mention or every high-confidence structural heading.

Proposed review lifecycle: PROPOSED → ACCEPTED / REJECTED / CONFLICTED; changed source → NEEDS_REVIEW for affected assertions. Approved scenario assumptions are still assumptions, not actual expenditure or legal approvals. Locks preserve the original selected value; source changes create a visible conflict and stale-dependent status instead of silently overriding the lock.

## 13. Version/change propagation

Reuse source versioning, ProjectActivity, result input snapshots and existing fingerprints. Do not replace them with a parallel event store or a full general-purpose graph service.

Current concrete gaps, requiring bounded fixes before material AI drives costs:

- R03 resolve_active_screenplay returns a prior projection when rows exist but none links a current version, before looking for the actual current unprojected document. R08 budget selection orders typed documents by creation time rather than filtering the canonical active version.
- R06, R08 physical inputs and R13 script facts read project-wide requirements/elements rather than one selected analysis. Old drafts can contribute effective facts.
- R03 reparse deletes scenes/characters and derived requirements; scene-linked observations can cascade away. It is not durable reviewed-state preservation.
- R09 fingerprints economic lines and set-valued script facts, versions/digests and FX snapshot date, but not selected analysis/plan identity, scene frequency/order, review revisions, complete typed personnel evidence or schedule dependencies. Existing freshness is real but insufficient for proposed new inputs.

Proposed dependency sequence:

~~~text
new source version -> mapped scene changes -> affected assertions/resources
 -> affected approach/availability/plan assignments -> affected line bases
 -> changed scenario monetary/territorial inputs -> affected program evaluations
 -> coherent new candidate generation -> current recommendation
~~~

Prefer local invalidation, not indiscriminate new analysis: scene-text edits invalidate that scene's interpretations; formatting-only changes need no rate lookup; changing a rental rate does not reparse scripts; FX changes revalue money without rerunning AI; a rejected proposal does not invalidate effective economics. Shared resource/day/global dependencies may expand the affected set beyond one scene.

Each node records input IDs/revisions and computation version. Derived nodes compare effective hashes; an audit-only provenance update need not rerun unchanged arithmetic, but must refresh the result's evidence manifest. Distinguish semantic calculation fingerprint from immutable source-lineage fingerprint.

At first, reuse the current whole economic-generation recomputation after material changed inputs. Caps, thresholds, stacking and ranking are not independent per line; invalidating a line requires re-evaluating its relevant program/structure dependencies. Only introduce segment-level memoization after proving equivalent results to full evaluation for the selected manifest. Publish atomically; never show a new incentive with old NPC or an old recommendation labeled current.

Asynchronous analysis, if later added, must be idempotent on source+analysis version, resumable, and compare the current manifest before activation. A job finishing for revision A after revision B was selected must not become current. No queue infrastructure is required merely to describe this contract.

## 14. Movie Magic interoperability

This is a documentary feasibility assessment, not a tested importer. Export availability is verified; fidelity on a producer-supplied sample remains to be tested. All source files must be authorized exports, versioned in the existing Library.

| Path | Classification | Evidence / practical boundary |
|---|---|---|
| MMB10 JSON or XML Advanced → CineGlobe | TECHNICALLY POSSIBLE | Official exports contain detail data and tool associations, including groups/fringes/sets/locations/globals. Prefer this over PDF; map to the existing budget domain. Exact schema/fidelity needs sample acceptance. [MMB import/export](https://mmb-docs.ep.com/Projects_and_Budgets/importexport.html) |
| MMB XML Basic or tab-delimited → CineGlobe | TECHNICALLY POSSIBLE | Published machine-readable/basic and tab-delimited paths; fewer semantics may survive. Mark absent basis as unknown. [MMB import/export](https://mmb-docs.ep.com/Projects_and_Budgets/importexport.html) |
| MMS one-line XLSX/report PDF → CineGlobe plan | TECHNICALLY POSSIBLE extraction; LIKELY POSSIBLE full chosen mapping | One-line XLSX/PDF export is documented. Reports are projections, not proof that availability, every unit or all DOOD rules are included. Define required columns and verify completeness. [MMS product](https://www.ep.com/movie-magic-scheduling/) |
| MMS → MMB .mbl → supported MMB export | TECHNICALLY POSSIBLE vendor workflow | .mbl exports the active sub-board's categories/elements/worked-day quantities. It is not a full schedule graph or automatic live recalculation. [MMS export](https://mms-docs.ep.com/ScheduleFiles/ExportingScheduleData.html), [MMB schedule import](https://mmb-docs.ep.com/Setup/mms6_import.html) |
| FDX / Scheduling Export .sex → MMS | TECHNICALLY POSSIBLE in MMS; LIKELY POSSIBLE CineGlobe adapter | Vendor supports script headers/characters/tagged elements. CineGlobe currently treats FDX as raw text, not validated semantic XML. A future narrow importer requires fixtures/specification; not implemented now. [MMS import](https://mms-docs.ep.com/Breakdown/ImportingBreakdownSheets.html) |
| Native .mmbx/.mbd budgeting or .mmsx/.msd scheduling → direct custom decoder | PROPRIETARY/UNKNOWN | Extensions and vendor compatibility are documented; no reviewed public native schema/license establishes a safe complete custom round trip. Do not confuse the two file families. [MMB formats](https://mmb-docs.ep.com/Projects_and_Budgets/importexport.html), [MMS support](https://www.ep.com/support/movie-magic-scheduling/) |
| CineGlobe JSON/XML → native editable Movie Magic file | PROPRIETARY/UNKNOWN | Outbound machine-readable support does not establish reciprocal arbitrary JSON/XML import. Request vendor-supported documentation before promising it. |
| Live two-way synchronization / EP private API | PROPRIETARY/UNKNOWN | No public supported API contract was established in the inspected manuals. Do not access private endpoints or scrape authenticated product internals. |
| Native-format reverse engineering, screen automation to maintain sync, full report/stripboard clone | NOT WORTH BUILDING for SA-2 | Explicit source-export adapters solve the scoped need with less corruption/version risk. This is a design judgment, not a claim that the task is technically impossible. |

The MMB import/export page's compatibility notes contain .msd references inconsistent with its stated budgeting import extensions; do not infer format support from those ambiguous notes. The MMS-specific documentation establishes its .msd legacy scheduling context. Sample import certification must resolve any ambiguity before a supported-format claim.

Recommended first boundary: choose one producer-authorized structured MMB export and one schedule report format for an explicitly versioned adapter contract. Missing schedule dates/resources are recorded, not reconstructed from report typography. Return a validation/mapping report with source totals, row identities, unmapped fields, formulas supported/opaque and reconciliation variance. Full round-trip fidelity is not an SA-2 promise.

## 15. AG comparison

Order of review: independent code/runtime/history conclusion was recorded first. Then the canonical remote head was checked as e42e28d7af7dd6af00d3f7518215e14f36b720b2, its tree searched for SA-2/script architecture artifacts, and the [Gemini Markdown review](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/docs/validation/GEMINI_SCRIPT_ANALYZER_BTL_ARCHITECTURE.md) retrieved directly using the GitHub Contents API. Its [JSON companion](https://github.com/surajgohill-oss/Frametax/blob/e42e28d7af7dd6af00d3f7518215e14f36b720b2/docs/validation/GEMINI_SCRIPT_ANALYZER_BTL_ARCHITECTURE.json) was read from the remote-tracking Git tree. Artifact commit: f4a873e473d71ca908f91af4810ef22d58a05027, 2026-08-14, reviewer Gemini 3 Pro.

**This is a historical AG/Gemini proposal, not evidence of a newer SA-2 design or implementation.** No SA2_ARCHITECTURE_RECONCILIATION_AG or equivalent new artifact was found in the shared branch tree. Do not attribute unstated stripboard/API decisions to AG.

| Issue in retrieved proposal | Classification | Reconciliation |
|---|---|---|
| One model progressively refined from L2 to L3 | EQUIVALENT | Agree; extend current budget domain. Extend this principle to L1 source/estimate states too. |
| Explicit fixed/project-specific costs; no AI rates | EQUIVALENT | Preserve. Avoid geography multipliers on fixed cast/packages or double-loaded fringe/travel. |
| A node at any budget level can be frozen/overridden | AG BETTER | Its explicit departmental scope usefully strengthens the initial line-level focus. Adopt hierarchical locks with child roll-up/conflict semantics, not a total-only overwrite that fabricates detailed allocations. |
| AI owns routine slugline parsing/character extraction | CODEX BETTER | Current deterministic parser already owns supported structure. Use AI for evidenced ambiguity/material semantics, not a replacement intake path. |
| Page count/INT-EXT/TOD baseline with complexity reducing pages/day | CODEX BETTER | Useful rough proxy, insufficient for an executable plan. Require work grouping, resource availability, moves, units and terms before schedule-sensitive claims. Current eighths are not reliable enough for precision planning. |
| P10/P50/P90 labels for template/model budgets | NEEDS LEAD DECISION | Require a calibrated probabilistic model and holdouts first. Until then use explicitly bounded assumptions/scenario ranges, not unsupported percentile labels. |
| One source-of-truth ranking across budget, assumptions, rates and script | CODEX BETTER | Different domains answer different questions. Select within field/scope/version; source budget wins historical cost, not the intended script or an elected future approach. |
| Ask only the top 20% of cost drivers (JSON) | CODEX BETTER | A low-dollar fact may determine feasibility, qualification or a winning structure. Use material dependency/decision impact, not a fixed percentile of costs. |
| “Known US post exclusion” and territorial spend fractions as handoff | NEEDS LEAD DECISION | Preserve work-geography facts and program-specific outcomes. US post is not a universal exclusion; producer fractions are elections, not verified actual territorial compliance. |
| LU L3 budget-ratio matching as proof of acceptance | INCOMPATIBLE | LU is a regression fixture, not sufficient independent predictive acceptance. Current script is scan-blocked; matching known budget totals risks leakage. Use R17 holdout separation and additional generic productions. |
| Bringing thin schedule/driver proof into SA-2 instead of only SA-3/4 | NEEDS LEAD DECISION | This report recommends a small interface proof, not full scheduling/estimating. The older canonical phase split puts production scheduling in SA-3 and local L2 estimation in SA-4. Approve the boundary explicitly. |

No disagreement is manufactured about a full Movie Magic UI or live synchronization: the retrieved AG review does not specify those. A later AG SA-2 artifact should be compared as a new revision, without reopening settled code recovery or worldwide incentive research.

## 16. SA-2 exact recommended scope

The following is a bounded implementation proposal for a subsequent authorized task, not work performed here. It does not quietly absorb all SA-3/4 functionality.

1. **Safe existing spine.** Correct active-document/analysis selection, preserve source page basis and review identities, reject zero-scene “success” as sufficient breakdown readiness, and ensure all relevant consumers use the same selected analysis. Fix only the confirmed blockers to the SA-2 contract, not every unrelated analyzer limitation.
2. **Material semantic breakdown.** Extend the existing taxonomy/observations for stunts, practical effects, VFX/animation, crowds, special vehicles/animals/minors, period/art/wardrobe and relevant environment/language/cultural signals. Each domain distinguishes explicit source evidence, inference, alternatives and UNKNOWN; no automatic staffing or cost.
3. **Review and normalized links.** Analysis revision + stable resource/scene references, evidence-grounded proposals, durable accept/reject/override with ProjectActivity; minimal grouped-question data/API contract. No new standalone authoring UI in this scope.
4. **Thin plan contract.** Represent/import or accept producer-confirmed day/unit/work assignments and availability/events needed for one bounded proof. Compute distinct resource-day quantities and detect declared conflicts. No automatic strip packing or optimal calendar search. No silent multi-unit flattening; unsupported plan features produce precise limitations.
5. **Thin cost-driver contract.** Extend existing line basis/assumptions for supported quantity × duration × sourced rate and selected already-supported fringe/charge behavior. Demonstrate coverage/replacement against an existing budget. Unmapped opaque lines remain original amounts with unknown basis. No full script-only budget estimator.
6. **One effective adapter and dependency manifest.** Feed selected plan/budget inputs to R08/R09/R10; update existing input snapshots/fingerprints. Expose materiality and execution-readiness separately from priceability. Do not route through the old handoff while canonical evaluation reads something else.
7. **Bounded acceptance.** Complete the Section 18 contract tests and reviewed generic-fixture proof when implementation is commissioned. Compare outputs through the actual served canonical route; no project-specific runner.

SA-2 exit means reviewed, version-safe production information can demonstrably change a supported quantity/plan/qualification input and propagate coherently through the existing engine—or explicitly remain an unresolved proposal. It does **not** mean worldwide schedule/cost estimates are calibrated or every option is production-ready.

If the lead elects strict historical phasing, items 4–5 remain validated interface/fixture contracts in SA-2 and implementation moves to SA-3/4. In that case, explicitly label SA-2 “breakdown ready,” not “schedule-aware executable optimization.” There must be one chosen exit definition before the implementation prompt.

## 17. Explicitly deferred scope

- Automatic scene packing, global scheduling optimization, full multi-episode coordination and sophisticated resource-constrained search: SA-3.
- Complete stripboard, calendar editing, call sheets, DOOD report design, collaborative production scheduling UI: separate product scope.
- Broad local rate/union/CBA acquisition, universal overtime/minimum-call/turnaround compliance, and production payroll: later cost-domain work; capture applicable source terms now without pretending to execute unsupported ones.
- Complete L1 template estimator, L2/L3 budget authoring and statistical calibration: later estimating phases. Script-only input remains useful for breakdown and bounded planning, not a fabricated total budget.
- Photoreal location matching, live weather/permit logistics, creative script rewriting and shot-level optimization: not SA-2.
- Native Movie Magic decoders, write-back and live cloud sync: deferred pending supported format/API authority and product value.
- Global incentive revalidation, provenance backfill, optimizer redesign and program-count reconciliation: explicitly outside this architecture phase.

Deferred means not built and not claimed. A result that requires a deferred capability cannot be labeled execution-verified by substituting an undocumented default. Existing independent budget economics remains usable with its own disclosures.

## 18. Acceptance-test proposal

No tests were run in this analysis. These are prospective acceptance criteria for the bounded implementation, not new mandatory research loops. Freeze fixture IDs/versions and expected evidence before implementation; use existing tests/corpus and add narrowly missing cases.

| Gate | Required proof |
|---|---|
| Current version | New current draft with no projection cannot serve the old draft as current; ambiguous revisions require selection, not filename guessing. Current budget selection follows the same source authority. |
| Stable scene/evidence identity | Insert/renumber/split/merge scenes; unaffected logical resources and approvals survive, changed memberships are explicit, historical observations remain queryable. |
| Structural quality | Correct known false cue and INT-EXT cases; preserve page maps; flag approximation. Empty/no-heading/scan input cannot claim professional breakdown readiness. |
| Source-grounded semantics | Negation, dialogue-only action, off-screen events, metaphors and alternative VFX/practical approaches do not become asserted resource quantities. Validate per-category precision/recall against an independently marked sample, not parser counts alone. |
| Review safety | Reparse cannot resurrect rejected assertions or erase approved choices; stale evidence creates a review conflict. Unreviewed interpretation cannot silently enter selected-plan money. |
| Resource quantities | Three scenes using one resource on one day yield one applicable resource-day, not three. Multi-day scene parts and simultaneous units conserve work coverage and identify conflicts. |
| Schedule limitations | Relative dates allowed; unknown actual dates/availability remain unresolved. Off/travel days, per-unit calendars and supplied hard constraints are respected or explicitly flagged. |
| Budget integrity | Imported totals/FX/source amounts preserved; formula mapping reconciles; unsupported formulas are opaque. A detail expansion or approved replacement never counts both parent and children. |
| Fringe/contract boundary | A fully loaded source line is not fringed again. Supported caps/aggregation/units behave as stated; unsupported employee-level terms are reported, not approximated silently. |
| One line-delta proof | An approved quantity change affects only dependent bases initially, then the same canonical QPE/incentive/NPC path. Demonstrate unchanged cost when scenes move within the same paid duration. |
| Territory/cultural distinction | Payer-only change cannot attest work location; narrative place cannot attest filming place or nationality. Source-backed facts use the existing adapters and program-specific rules. |
| No country-universe collapse | Soft/unknown script feasibility does not remove economically evaluable programs. A plan conflict changes execution status with exact reason, not legal priceability by proxy. |
| Invalidation/replay | Script-only edit, quantity edit, source-rate edit, review change and FX edit each invalidate their true dependents. Same selected inputs reproduce results; stale AI completion cannot publish. |
| Served-generation coherence | Actual canonical API returns one manifest/engine generation for budget, incentives, NPC and recommendation; never mix persisted old economics with new planning inputs. |
| Genericity and holdouts | At least two non-LU productions plus LU regression. Use a script+schedule+budget corpus fixture such as The System in source-driven mode; for predictive accuracy, quarantine actual schedule/budget using R17 before freezing predictions. Do not use source-budget totals as hidden estimate targets. |
| Format interoperability | One real authorized MMB structured export and one chosen schedule export: ingest/map/reload/reconcile all required semantics; disclose omitted fields, units and unsupported terms. No unsupported round-trip claim. |

Numerical error bounds, semantic accuracy thresholds and materiality tolerances need lead/production-domain agreement before testing. Do not invent an acceptance percentage after seeing the answers. Exact invariants—identity, source scoping, conservation, no double count, rejection of invalid evidence—must pass without tolerance-based excuses.

## 19. Risks/blockers

Highest-risk chain: false script cue → unreviewed resource → inflated days/headcount → new cost → changed territorial allocation → overstated incentive → apparently lower NPC → wrong recommendation. Evidence, approval, line-coverage and plan gates must interrupt it before money changes.

Immediate engineering blockers to that expansion are the current-version/read scoping, destructive reparse/review behavior, absent line-basis model, missing plan constraints, and incomplete new-input fingerprint coverage documented above. Current parser density-based eighths and lexical counts must not be treated as professionally calibrated scheduling inputs. None requires a new jurisdiction audit.

The present generic normalization's default crew/budget manifest is a modeled assumption path, not production-record truth. Merely inserting an AI crew count without addressing cost coverage, rates, original-versus-destination basis and adjustment overlap would make the trace look richer while worsening double-count risk.

Detailed source/export fixtures, producer-approved execution assumptions and explicit contract applicability are prerequisites for the corresponding import/cost claims. Their absence blocks those claims, not this architecture document and not unrelated source-budget incentive calculation.

Local runtime observations prove the queried database state only. No deployed-server or browser verification occurred. Existing dirty frontend files were not modified or included. Relevant tests were inspected but not executed; historical suite totals are not represented as this task's results. The retrieved AG review predates SA-1 implementation and must not be mistaken for current agreement.

## 20. Lead-architect decisions required

1. Approve the SA-2 exit boundary: recommended thin plan/driver implementation proof versus strict historical SA-2 contract-only handoff to SA-3/4. Do not commission full scheduling by accident.
2. Approve one effective production-plan manifest feeding the existing canonical evaluator, with the old SA-1 handoff retained only as a compatible projection of the same selected inputs.
3. Approve field/scope/version evidence precedence, hierarchical locks and explicit separation of source history, producer scenario elections, inferred interpretations and legal authority.
4. Approve plan-level execution readiness separate from existing priceability/qualification/knowledge-quality states. Define who may approve material assumptions and hard conflicts.
5. Choose the first authorized MMB and schedule export samples and the exact supported semantic subset. Do not promise native round trip or live sync.
6. Define materiality thresholds and professional reference annotations; decide whether uncertainty is bounded scenario analysis only (recommended initially) or a separately validated probabilistic model.
7. Resolve the historical AG differences in Section 15—especially LU-only acceptance, cost-percentile questions and page-based scheduling—before writing the implementation prompt.

Final architecture disposition: **reuse the existing economic engine; add the smallest version-safe, reviewable production-plan and cost-basis connection.** No application implementation or production acceptance is claimed by publication of this artifact.
