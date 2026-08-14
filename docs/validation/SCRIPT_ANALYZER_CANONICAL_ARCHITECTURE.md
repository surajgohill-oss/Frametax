# CineGlobe Script Analyzer + Production Cost Engine

## Canonical architecture and implementation specification

**Repository:** `surajgohill-oss/Frametax`

**Branch:** `claude/audit-frametax-features-NZcX5`

**As of:** 2026-08-14

**Mode:** architecture synthesis only; no implementation.

## Final gate

`GO_FOR_SCRIPT_ANALYZER_IMPLEMENTATION_PLANNING`

This specification is concrete enough to implement without independently redesigning the domain, source hierarchy, progressive budget, schedule boundary, Bridge contract, generic project state, or optimizer handoff.

## Canonical product boundary

CineGlobe's Script Analyzer is a **production-planning engine**:

```text
SCRIPT + KNOWN VARIABLES + OPTIONAL BUDGET + OPTIONAL SCHEDULE
  -> evidence-backed production facts
  -> production requirements
  -> minimum cost-driver schedule
  -> one progressive production budget
  -> generic Canonical Production State
  -> existing production structures and optimizer
  -> NPC / ranking
```

It is not story coverage, screenplay scoring, an incentive qualification model, Movie Magic Budgeting, Movie Magic Scheduling, or a replacement optimizer.

The existing optimizer remains authoritative downstream. New work stops at producing structured, versioned production inputs.

## Resolved architecture decisions

1. There is **one evidence-progressive production model**. L1, L2 and L3 are maturity states of one Budget and line lineage, not separate engines.
2. `DocumentVersion` is the immutable physical-source authority. `ScreenplayDocument` and `BudgetDocument` remain typed projections linked to a version.
3. Parsed actual rows and calculated canonical lines are distinct. `BudgetLineItem` remains an immutable source observation; a new `BudgetLine` selects the effective value and preserves lineage.
4. AI cannot overwrite deterministic facts, decide production approaches, or provide rates and economics.
5. A minimum cost-driver schedule is new. It provides duration/quantity inputs and does not attempt full scheduling operations.
6. Current static local-cost profiles remain only Tier C indexed/default inputs until cited, dated data replaces them.
7. The manual Bridge core is reused with provider-neutral script contracts.
8. A new generic `CanonicalProductionStateBuilder` replaces only Little Utopia's project-specific upstream assembly role. It feeds the unchanged downstream optimizer.
9. The first implementation is a bounded end-to-end vertical slice for any Project, not a parser-only milestone.

## 1. Canonical domain model

| Entity | Decision | Existing module reused | Canonical responsibility |
|---|---|---|---|
| ProductionProject | `EXTEND` | `frametax2/backend/app/models/project.py::Project` | Root aggregate for documents, facts, scenarios, schedules, budgets, estimates, components and optimizer results |
| ScriptDocument | `EXTEND` | `app/models/screenplay.py::ScreenplayDocument` | Typed parse projection for exactly one screenplay `DocumentVersion` |
| Scene | `BUILD_NEW` | extend output of `app/ingestion/screenplay_parser.py` | Version-scoped scene, page/eighths, normalized heading and exact source span |
| SceneElement | `EXTEND` | `ExtractedScriptElement` | Taxonomy-controlled objective assertion or interpretation attached to a Scene, with evidence |
| Character | `BUILD_NEW` | none; `ProjectPerson` is not a fictional character | Character identity, aliases, appearances, dialogue and derived burden per script version |
| LocationRequirement | `EXTEND` | `ProjectLocationRequirement` | Scripted need, recurrence, flexibility, stage/practical state, scene sources and chosen production location |
| ProductionRequirement | `BUILD_NEW` | ProductionPackage is its reusable consumer | Normalized production need linked to scenes, departments, components and schedule/cost drivers |
| ProjectFact | `EXTEND` | `ProjectFact` | Current effective simple project fact selected through precedence |
| ProductionAssumption | `BUILD_NEW` | reuse `CrewManifest`/`ProductionBudgetParams` concepts | Versioned, scenario-scoped pages/day, crew, scale, prep/wrap and production assumptions |
| Schedule | `BUILD_NEW` | none | Versioned estimated or actual cost-driver calendar |
| ShootDay | `BUILD_NEW` | none | Scene grouping, unit, location/stage, day/night, moves, cast and special-work burden |
| ProductionUnit | `BUILD_NEW` | reuse LocationRole/Travel concepts | Principal, second, splinter, aerial, marine or other unit and its crew/location/day range |
| Budget | `BUILD_NEW` | connect, do not repurpose, `BudgetDocument` | Versioned progressive working budget for one planning Scenario |
| BudgetLine | `BUILD_NEW` | connect `BudgetLineItem`; reuse budget enums | Active leaf or inactive aggregate carrying quantity/rate/duration, locality, range, evidence and lineage |
| CostDriver | `BUILD_NEW` | reuse quantity/rate trace patterns | Formula/version mapping requirements, schedules and assumptions into budget lines |
| Rate | `BUILD_NEW` | connect `LocalCostBenchmark`, `UnionFringeRule`, `FXRate` | Normalized rate/range with applicability, geography, currency, source tier and dates |
| RateSource | `EXTEND` | `app/models/document.py::SourceDocument` | Published agreement, official/market benchmark or project quote provenance |
| CostEstimate | `BUILD_NEW` | reuse calculation trace/snapshot patterns | Reproducible estimate run with fingerprint, seed, ranges, warnings and blockers |
| EstimateEvidence | `BUILD_NEW` | reuse ProjectFact, DocumentVersion and Bridge provenance concepts | Immutable observation or derivation supporting any effective value |
| Override | `BUILD_NEW` | reuse `ProjectActivity` for audit history | User selection that changes the effective value without destroying prior evidence |
| Scenario | `BUILD_NEW` | connects to downstream `ProductionScenario`; does not reuse it | Named production-planning alternative; one Scenario may generate many ProductionStructures |
| ProductionComponent | `BUILD_NEW` | reuse LocationRole, movable-category and allocation concepts | Principal photography, unit, post, VFX, music, sound, DI, animation or virtual-production work package |
| CanonicalProductionState | `BUILD_NEW` | reuses ProductionPackage and all downstream optimizer modules | Immutable, fingerprinted effective input snapshot for any project |
| OptimizerHandoff | `CONNECT` | ProductionPackage, composer, allocation, normalization, optimizer and ranking | Typed adapter payload containing production facts and costs, never AI prose |

### Required extensions

`ScreenplayDocument` remains the typed projection, while `DocumentVersion` is the source authority. The active analysis must require a `document_version_id`, store parser version and input fingerprint, and never select a screenplay by filename alone.

`Scene` IDs are stable within a specific screenplay version using the version checksum, sequence and normalized heading fingerprint. Cross-draft matching is explicit through a nullable lineage link; a fuzzy match cannot silently assert that two revised scenes are the same.

`ExtractedScriptElement` gains a scene relationship, controlled taxonomy, normalized value, quantity/range/unit, evidence offsets/hash, extraction method, evidence state, interpretation flag, review state and version/supersession fields.

`ProjectLocationRequirement` gains source-scene links, recurrence, production-approach state, chosen city/jurisdiction, mobility and scenario scope.

`ProjectFact` remains the current project-wide value, not a store for scenes, schedules or budget lines. Its selection must point to evidence/override records; `ProjectActivity` retains history.

### Relationships

```text
Project
  -> Document -> DocumentVersion -> ScriptDocument -> Scene -> SceneElement
                                            |          -> Character appearances/dialogue
                                            -> ProductionRequirement
                                            -> LocationRequirement

Project -> planning Scenario
           -> ProductionAssumption
           -> Schedule -> ShootDay -> ProductionUnit / Scenes
           -> Budget -> active BudgetLines
                         ^
Requirement / Schedule / Assumption -> CostDriver -> Rate

Scenario + effective evidence -> CanonicalProductionState
  -> OptimizerHandoff
  -> existing ProductionStructures / optimizer / NPC ranking
```

Only active budget leaves roll up. An aggregate parent and its expanded children can never both count.

## 2. Script Analyzer pipeline

1. **Upload and version — deterministic.** Universal ingestion creates `Document`/`DocumentVersion` with checksum, source and confidentiality. Semantic dispatch creates the screenplay projection; it must not create `BudgetDocument` for every supported extension.
2. **Text/layout extraction — deterministic.** Phase 1 supports plain text and text-based screenplay PDF. Preserve page boundaries, offsets and raw-text hash. A scan-only/failed PDF is blocked, not guessed.
3. **Structural parse — deterministic.** Extend `screenplay_parser.py` to produce scene boundaries, page eighths, source scene numbers, normalized sluglines, INT/EXT, day/night, character cues and dialogue linkage.
4. **Objective persistence — deterministic.** Persist version-scoped Scene, Character and objective SceneElement records with exact source spans and parser version.
5. **Element extraction — AI extraction.** The Bridge proposes production elements not reliably encoded by format. These are staged observations.
6. **Complexity interpretation — AI interpretation.** The model may propose scale/range/alternatives with evidence. It may not provide rates, dollars or production decisions.
7. **Reconciliation — deterministic.** Validate spans, merge identical assertions, apply precedence and expose conflicts. Models do not vote.
8. **Material confirmation — user decision.** Ask grouped questions only for material low-confidence choices unresolved by source/deterministic logic.
9. **Canonical facts — deterministic.** Select effective ProjectFacts, LocationRequirements and ProductionRequirements while retaining every original observation.

AI cannot silently change a deterministic scene, infer false from absence of evidence, choose stage versus practical, choose cast or salary, supply rates, or promote its own output to actual/confirmed.

## 3. Canonical script-breakdown taxonomy

The taxonomy separates the fact in the script from its production interpretation. For example, a boat on the page is objective; open water versus tank is a producer decision.

| Capability | Primary class | Canonical rule |
|---|---|---|
| Scenes | `OBJECTIVE_SCRIPT_FACT` | deterministic boundary and source span |
| Page eighths | `DERIVED_DETERMINISTIC` | derived from preserved page layout; do not use word-count approximation when layout exists |
| INT/EXT | `OBJECTIVE_SCRIPT_FACT` | normalize the heading; ambiguous stays unknown |
| Day/night | `OBJECTIVE_SCRIPT_FACT` | preserve CONTINUOUS/LATER and ambiguity explicitly |
| Locations | `OBJECTIVE_SCRIPT_FACT` | scripted place is objective; real production place is a decision |
| Recurring locations | `DERIVED_DETERMINISTIC` | normalized recurrence across scenes |
| Characters | `OBJECTIVE_SCRIPT_FACT` | cue/name/appearance; performer is separate |
| Dialogue/speaking roles | `DERIVED_DETERMINISTIC` | dialogue blocks linked to cues |
| Cast burden | `DERIVED_DETERMINISTIC` | pages, scenes, workdays, night/location burden; cast identity/salary are decisions |
| Extras | `OBJECTIVE_SCRIPT_FACT` | explicit evidence/count; inferred quantity is interpreted |
| Crowds | `AI_INTERPRETED` | evidence plus size/logistics range; material result is confirmed |
| Minors | `OBJECTIVE_SCRIPT_FACT` | scripted age/role; performer age/work plan external/confirmed |
| Animals | `OBJECTIVE_SCRIPT_FACT` | presence is objective; trained-animal plan/quantity is interpreted |
| Vehicles | `OBJECTIVE_SCRIPT_FACT` | presence; fleet quantity is interpreted |
| Picture vehicles | `AI_INTERPRETED` | visible/specific treatment; fleet/period approach confirmed |
| Weapons | `OBJECTIVE_SCRIPT_FACT` | presence/action; armorer/replica/practical approach confirmed |
| Stunts | `AI_INTERPRETED` | action evidence plus performer/rehearsal/day range |
| Intimacy | `AI_INTERPRETED` | confidential evidence-backed flag; handling plan confirmed |
| VFX | `AI_INTERPRETED` | potential shots/complexity; methodology/count confirmed |
| Practical SFX | `AI_INTERPRETED` | effect/reset/safety range; execution confirmed |
| Wardrobe | `AI_INTERPRETED` | evidence plus change/period complexity; exact looks/multiples confirmed |
| Hair/makeup | `AI_INTERPRETED` | complexity and turnaround range |
| Prosthetics | `AI_INTERPRETED` | presence/application complexity; design confirmed |
| Period | `OBJECTIVE_SCRIPT_FACT` | story period is objective; execution complexity is interpreted |
| Props | `OBJECTIVE_SCRIPT_FACT` | explicit hero/recurring items; fabrication/quantity interpreted |
| Construction | `AI_INTERPRETED` | likely need/scope from environment; scope confirmed |
| Set builds | `PRODUCER_DECISION` | stage/build versus practical is never selected by AI |
| Specialty equipment | `AI_INTERPRETED` | candidate crane/underwater/process/motion-control needs; package confirmed |
| Marine | `AI_INTERPRETED` | water/boat evidence; tank/open-water/unit/safety decisions confirmed |
| Aerial | `AI_INTERPRETED` | candidate aerial/drone need; platform/unit confirmed |
| Weather | `AI_INTERPRETED` | scripted weather evidence; practical/VFX/cover decision confirmed |
| Music/performance | `AI_INTERPRETED` | performance/playback evidence; musicians/recording/licensing confirmed |
| Company moves | `DERIVED_DETERMINISTIC` | derive from ordered days and confirmed locations; producer may regroup |
| Travel | `DERIVED_DETERMINISTIC` | derive from confirmed bases/locations; travel policy confirmed |
| Additional units | `PRODUCER_DECISION` | AI may flag an opportunity but cannot create a unit plan |
| Safety/logistics | `AI_INTERPRETED` | evidence-backed issue; qualified human controls the plan |

## 4. Minimum schedule architecture

The schedule exists to generate reliable cost quantities and component timing. It is not a full Movie Magic Scheduling replacement.

Inputs:

- scenes and page eighths;
- normalized locations and confirmed stage/practical decisions;
- day/night;
- character appearances and confirmed availability constraints;
- material elements and complexity;
- production scale, unit decisions and pages/day ranges;
- an actual schedule when supplied.

Deterministic process:

1. Compute scene work units from page eighths and explicit complexity modifiers, retaining every modifier source.
2. Group by confirmed production location/stage, unit and day/night, then apply cast and special-element constraints.
3. Apply pages/day ranges by scale/work type; never hide a single 30-day default.
4. Pack scenes into reproducible estimated ShootDays and identify moves, split/special-unit days and unresolved constraints.
5. Derive department prep/wrap/rental/holding ranges from the resulting work.
6. If an actual schedule exists, preserve the estimate for comparison but select actual values by precedence.

Required cost outputs:

- shoot days P10/P50/P90 and actual;
- unit days by type and jurisdiction;
- scene-day assignments;
- stage occupancy and practical-location days;
- company moves and night/exterior days;
- cast work/hold/travel days;
- crowd/extras/minor/animal days;
- stunt, SFX and VFX-plate days;
- marine/aerial/special-unit days;
- prep/shoot/wrap weeks by department;
- crew and equipment weeks;
- hotel nights, per diem days and travel movements;
- assumptions and conflicts.

Capacity must reconcile: scene work units must fit scheduled capacity. Moves, night work, restricted child/animal work, stunt/SFX and special units cannot silently contribute zero.

Explicit non-goals are call sheets, timesheets, daily production reports, dispatch, operational day-out-of-days UI and full resource-level scheduling optimization.

## 5. One progressive L1/L2/L3 budget

### Invariants

- Every Budget belongs to one planning Scenario and has a maturity state.
- `line_key` identifies the same economic concept across versions.
- Expansion replaces an aggregate parent with child lines; only active leaves count.
- Before new evidence, child P50 values reconcile to the parent's P50. Evidence-driven deltas are recorded separately.
- Every line preserves amount range, authority state and original value.
- Actual imported lines supersede matched estimates. Unmatched residual estimates remain visible and inactive/active only by explicit merge rule.

### Level 1 — Rapid Global Estimate

Purpose: fast worldwide comparison.

Inputs:

- text-based script parse;
- page, scene, location, cast and day/night counts;
- high-impact interpreted requirements or explicit unknowns;
- format/genre and producer-selected broad scale;
- baseline stage/location/unit assumptions;
- Tier B/C benchmarks and jurisdiction indices.

Output is department-level P10/P50/P90, coarse component/territorial spend, schedule range, material unknowns and a P50 optimizer payload with uncertainty warnings.

Allowed assumptions are explicit crew-size bands, pages/day bands, department-share templates, Tier C indices and labeled/widened global defaults.

L1 must not fake role-level rates, union/fringe applicability, overtime, location/stage/vendor quotes, exact shoot days, exact travel party or model-generated rates. Presentation is rounded and range-based, not fake dollar-and-cent precision.

### Level 2 — Production-Informed Estimate

L2 expands the same lines using confirmed material elements, the cost-driver Schedule, crew/equipment/stage/location/travel assumptions, components and validated local data where available.

Granularity is department, subdepartment and material account. Quantities/durations derive from requirements and schedule. Each labor line must expose fringe and overtime state; every line has localization policy, rate tier/effective date and L1 parent lineage.

### Level 3 — Detailed Line Budget

L3 further expands the same lineage using a detailed schedule, role/crew counts, prep/shoot/wrap, agreements/fringes, validated or quoted rates, equipment/stage/location packages, travel policies and insurance/bond/finance inputs.

Each active line contains quantity, unit, rate, duration, prep/shoot/wrap, overtime, fringe, rental period, allowance, currency, jurisdiction, component and evidence.

A jurisdiction cannot be called L3-valid while material labor/rate/fringe inputs are Tier C/global default, hard-stale or unknown.

### Continuity and uncertainty

An L1 aggregate is never discarded. It becomes an inactive parent of L2 children. L2 lines become parents or stable peers for L3 lines. The version records why the total changed: new quantity, schedule, rate, scope or user override.

Each uncertain quantity/rate/duration stores low/base/high and a distribution class. A deterministic seeded simulation uses shared correlation groups—shoot days, crew scale, location count, FX—rather than adding independent line percentiles. Actual values collapse P10=P50=P90. Every estimate stores seed, engine version and input fingerprint.

## 6. Authoritative input precedence

```text
ACTUAL_PROJECT_VALUE
  > USER_CONFIRMED
  > VALIDATED_LOCAL_DATA
  > DETERMINISTIC_DERIVED
  > AI_INFERRED
  > INDEXED_ESTIMATE
  > GLOBAL_DEFAULT
  > UNKNOWN
```

An accepted project quote is `ACTUAL_PROJECT_VALUE`. An unaccepted quote is candidate evidence only.

Higher authority wins only for the same scoped field and effective period. A newer low-authority inference cannot replace an actual value. Conflicting same-rank observations remain unresolved until scope/date/source or the user resolves them.

Every effective value stores:

- effective value and original observation;
- unit/type;
- authority state and confidence;
- source plus page/row/span;
- effective dates;
- parser/model/formula/version;
- override, selection reason and selection time.

An override creates an immutable Override record and ProjectActivity event. Original evidence remains available.

## 7. Budget upload integration

Phase 1 supports:

- CSV with explicit description/amount columns;
- text-based Movie Magic/EP PDF through the existing extractor and account parser.

Canonical path:

```text
Document / DocumentVersion
  -> semantic BudgetDocument projection
  -> parse_budget_csv OR parse_budget_from_text
  -> immutable BudgetLineItem source rows
  -> classification + top-sheet/leaf/currency/duplicate reconciliation
  -> canonical Budget/BudgetLine actual observations
  -> precedence merge with active estimate
  -> CanonicalProductionState
  -> existing optimizer
```

`parse_budget_csv` and the existing Movie Magic/EP parser are connected, not rebuilt. Default MISC classifications enter review rather than silently becoming safe BTL/nonlabor lines.

The current XLSX-as-CSV path is replaced before XLSX is claimed as structured. Native MBD is deferred until a supported parse/export strategy and fixtures exist.

A checksum + document version + account/source-row key can produce only one source observation. An actual line and its matched estimate cannot both count unless an explicit split/residual relationship says why.

## 8. Script/schedule/budget merge rules

| Conflict | Resolution |
|---|---|
| Script has 20 locations; budget has 8 location accounts | Keep both because they measure different things. Actual amounts control cost; script locations control requirements. Raise a coverage discrepancy if material. |
| Actual/confirmed schedule says 35 days; model assumed 30 | Select 35, preserve 30, recompute every duration-driven line and report the delta. |
| Actual budget has crew; model expects a larger crew | Actual amount remains effective. Produce an undercoverage warning and non-counting shadow delta; add cost only after user authorization. |
| AI contradicts deterministic slugline/dialogue parse | Deterministic parse controls; AI remains disputed evidence unless the source is malformed and material. |
| Two files claim to be current | User/Document.current_version selection is required; canonical rebuild blocks until resolved. |
| Actual budget omits a script-derived department | Do not auto-add to the actual budget. Flag coverage; estimate stays a shadow line until authorized. |
| Actual budget contains unmatched lines | Retain every line exactly once; classify or mark unknown/MISC for review. |

Discrepancy intelligence never silently mutates actual producer data.

## 9. Local-cost data architecture

### Rate authority classes

| Class | Use |
|---|---|
| Project quote | Actual only after producer acceptance; exact scope/currency/validity |
| Actual local rate | Published/current exact unit and period |
| Validated agreement/union rate | Applies only when agreement/applicability facts match |
| Validated market benchmark | Range with sample/region basis |
| Indexed estimate | Reviewed baseline adjusted by a category-specific index; wider uncertainty |
| Global default × local multiplier | Last fallback; explicit and widest uncertainty, or unknown when unsafe |

### Localization policies

| Policy | Examples | Rule |
|---|---|---|
| `GLOBAL_FIXED` | A-list cast, rights, fixed creative deals | Never multiply by shoot-country index without an explicit project change |
| `PROJECT_SPECIFIC` | Accepted quote, negotiated bond/insurance/vendor | Use the scoped project value only |
| `LOCAL_LABOR` | Crew wages, payroll, fringes | Role/agreement/region × schedule; crew index only for L1 fallback |
| `LOCAL_GOODS_SERVICES` | locations, catering, local transport, construction materials | local rate/benchmark or category-specific index |
| `ROUTABLE_VENDOR` | VFX, post, sound, music, specialty equipment | Rate follows selected vendor/work location |
| `TRAVEL_DEPENDENT` | flights, lodging, per diem, freight | Origin/destination/people/days; no broad country multiplier |
| `FX_ONLY` | fixed local-currency contract | Convert currency without changing the real local amount |
| `NON_SCALABLE` | contingency policy, finance structure | explicit formula/terms only |

The existing `location_cost_benchmarks.py` profiles become Tier C `INDEXED_ESTIMATE`/`GLOBAL_DEFAULT` inputs. Their HIGH/MEDIUM labels are not data validation because all 44 source lists are empty.

Minimum Rate fields are item/category/role, jurisdiction/region/city, union/vendor, low/base/high amount, unit/minimum/overtime, currency, fringe/tax inclusion, source, effective/retrieved/verified dates, tier, license, staleness and fallback parent.

## 10. Rate-data maintenance

### Tier A — real producer jurisdictions

Maintain at most 12–15 high-value/active jurisdictions selected by active-project use, recommendation frequency and material spend. The initial candidate queue is MU, MT, GR, GB, AU, US, CA, IE and NZ; this is a maintenance priority, not a claim that those rates are already populated.

Tier A includes agreement/fringe/crew tables and key stage, equipment, location and travel benchmarks. Agreements/statutory rates are checked on publication and at least quarterly. Volatile travel/FX data is checked monthly or near the estimate date. Material hard-expired data cannot support L3.

### Tier B — validated market benchmarks

Maintain reviewed category/region ranges for recurring comparison jurisdictions. Refresh at least semiannually and on known market events. Tier B supports L1/L2 but is not presented as role-level actual.

### Tier C — worldwide indexed coverage

Maintain category-specific indices/global defaults annually or semiannually. Tier C supports L1 by default and always widens uncertainty.

Every rate has effective dates and `last_verified_at`. Soft stale data downgrades and widens; hard-expired data is excluded and falls back to the next permitted tier or unknown. The fallback label never changes. Estimate snapshots retain the exact rate version used.

This prioritizes high-material, high-use data rather than hand-maintaining arbitrary thousands of rates.

## 11. AI Bridge architecture

Decision: **reuse the manual Bridge core and extend provider-neutral contracts**.

Beta remains:

```text
export ScriptAnalysisPackage
  -> independent provider analysis in subscription UI
  -> responses/{provider}.json
  -> schema validation/import
  -> evidence reconciliation
  -> material human confirmation
  -> persisted canonical facts
```

`ScriptAnalysisPackage` contains package/schema version, project, screenplay DocumentVersion/checksum, confidentiality/redaction policy, deterministic scenes/characters, stable chunks/page/offset hashes, requested taxonomy, known producer facts, unknowns/materiality hints and the required response schema.

It excludes incentive conclusions and rates. Cost targets are excluded unless a later bounded materiality review specifically requires them, preventing extraction bias.

`ScriptAnalysisResponse` contains provider/model/operation, version/package hash and ElementAssertions with scene, taxonomy, normalized value, extraction/interpretation kind, quantity/range/unit, evidence spans/hash, confidence, rationale/alternatives and unresolved questions. There are no economic-rate fields.

Reconciliation key:

```text
script_version_id + scene_id + taxonomy_key + normalized_value
```

Imported assertions create staged `EstimateEvidence`/`SceneElement` observations. Provider adapters transport one contract; provider-specific business logic is prohibited.

## 12. Multi-model policy

Deterministic facts run first. The default is at most one model for unresolved extraction/interpretation.

A second model is used only when:

- an AI result is low-confidence and material;
- providers conflict on a material element;
- the evidence span fails or supports multiple material interpretations;
- a material category remains unknown.

Default materiality is potential P50 impact of at least `max($25,000, 0.5% of budget or L1 P50)`, one shoot day, or a material component/location-routing change.

The reconciler compares evidence to the script. Stronger evidence and scope win; model counts do not. Unresolved cases remain disputed/unknown and reach the user only if material. Only triggered scenes/elements are sent to a second provider.

## 13. Confidence and uncertainty

Field evidence states:

- `ACTUAL`
- `USER_CONFIRMED`
- `VALIDATED_RATE`
- `DETERMINISTIC_DERIVED`
- `AI_HIGH_CONFIDENCE`
- `AI_LOW_CONFIDENCE`
- `INDEXED_ESTIMATE`
- `GLOBAL_DEFAULT`
- `UNKNOWN`

Evidence state is authority. Confidence is uncertainty. Neither is a project-risk score.

`UNKNOWN` has no numeric effective value unless a separately labeled fallback is selected. Absence is not false or zero.

P10/P50/P90 describe estimate distributions, not legal/project success probability. Correlated inputs roll up through the reproducible simulation; confidence labels are never averaged into an opaque score.

## 14. Human confirmation

Prompt only when all three are true:

1. the potential cost, schedule or routing impact is material;
2. evidence is insufficient or conflicting;
3. deterministic/source logic cannot resolve it.

Group by production decision and show all affected scenes, such as “These 23 scenes appear to require practical locations rather than stage builds.” Do not ask scene-by-scene.

Sort by impact band, downstream dependencies and confidence—never an opaque risk number. An answer creates `USER_CONFIRMED` evidence/Override, recomputes dependent schedule/budget/state and keeps prior AI/model values.

Do not ask about high-confidence deterministic facts, immaterial ambiguity, inactive drivers or questions resolved by validated sources.

## 15. Generic project state

`CanonicalProductionStateBuilder` is the required integration layer. It replaces only Little Utopia's upstream input assembly for generic projects.

Inputs:

- Project and current DocumentVersions;
- effective ProjectFacts;
- active ScriptDocument/Scenes/Elements;
- ProductionRequirements and LocationRequirements;
- planning Scenario and Assumptions;
- active Schedule;
- canonical Budget/CostEstimate;
- ProductionComponents;
- rate/FX versions and Overrides.

Snapshot includes state ID/version/fingerprint/as-of, source versions, effective facts/authority, budget total/range/active lines, component and territorial allocations, production/post/VFX locations, shoot/unit/prep/wrap/travel days, resident/nonresident labor, goods/services, mobility, constraints, unknowns/blockers and engine/rate versions.

The builder fails closed on ambiguous current versions and unreconciled totals, counts active leaves once, snapshots inputs immutably and labels low-authority material states as provisional.

```text
CanonicalProductionState
  -> OptimizerHandoffAdapter
  -> existing discovery
  -> existing structure composition/allocation
  -> existing travel/FX/local normalization
  -> existing incentive evaluation
  -> existing NPC/ranking
```

No optimizer rewrite is authorized or required.

## 16. Optimizer handoff contract

`ProductionOptimizerInput` contains:

- project/scenario/state version, fingerprint and as-of;
- script, schedule, budget and estimate version IDs;
- gross production cost effective/P50 plus P10/P90 sensitivity;
- active budget lines with account/category/ATL-BTL, amount, cash/accounting and compensation;
- labor flag, resident/nonresident/unknown, services/goods territorial basis and jurisdiction;
- components with type, location, amount, mobility and authority;
- production, unit, post, VFX, music and sound locations;
- shoot/unit/prep/wrap/travel quantities;
- labor, goods/services, post, VFX and travel totals by jurisdiction/component;
- localization policy;
- constraints, unknowns, provisional blockers and user exclusions;
- material-field provenance.

The adapter creates existing `BudgetParseResult`/`ProductionPackage`-compatible inputs and allocation inputs. It passes effective/P50 values into the point optimizer and retains P10/P90 for deterministic sensitivity runs. The input fingerprint is written into the existing calculation-result snapshot fields.

The optimizer receives data, never AI prose.

Payer/SPV alone never establishes territorial spend. Each line separately tracks service-performed location, goods-use location, worker residency where relevant, payer and selected territorial basis.

## 17. Phased implementation plan

### SA-1 — Generic deterministic end-to-end vertical slice

Reuse universal ingestion/versioning, coarse parser logic, screenplay/budget schemas, CSV and Movie Magic PDF parsers, budget taxonomy, ProductionPackage, quantity-rate patterns and the existing optimizer.

Build Scene/Character extensions, minimal objective elements/requirements, precedence/evidence/override spine, minimum Schedule estimator, progressive L1 Budget/BudgetLine, CanonicalProductionState and optimizer adapter.

Runtime acceptance: any Project can upload a supported script and optional supported budget, persist/reload identical analysis, produce versioned schedule/cost ranges and reach existing optimizer structures with a traceable fingerprint.

Stop when LittleUtopiaState is not an input dependency, unchanged inputs reproduce identical results, and no silent AI/rate invention is possible.

### SA-2 — Material production breakdown and Bridge

Build the full taxonomy, ScriptAnalysisPackage/Response, evidence validation, targeted multi-model triggers and grouped confirmation.

Stop when no unreferenced AI assertion can become effective and confirmation recomputes all dependents.

### SA-3 — Production-informed schedule

Add constraint grouping, moves/units/night/special-work days, departmental prep/wrap and actual schedule import.

Stop when every duration-driven line has a schedule source/assumption and capacity/omission guards pass.

### SA-4 — Level 2 localized estimate

Add subdepartment drivers, Tier A/B rate ingestion, fringe/overtime applicability, component localization and correlated uncertainty.

Stop when broad multipliers cannot touch fixed/project-specific costs and material labor lines expose fringe/OT state.

### SA-5 — Level 3 detailed line budget

Add role/package/allowance lines, detailed durations, quote/agreement terms, line freeze/override and L3 validity gating.

Stop when active material lines trace quantity × rate × duration, OT, fringe, FX and reconciliation.

### SA-6 — Format and data expansion

Add real XLSX parsing, a supported MBD/export strategy, schedule formats and more Tier A/B jurisdictions only where measured demand and licensing justify them.

## 18. First implementation scope

The first implementation is SA-1, a useful vertical slice—not just persistence.

Included:

- generic project/current-version selection;
- text-based screenplay PDF and plain text;
- deterministic scenes, eighths, INT/EXT, day/night, characters/dialogue and locations;
- versioned persistence/reload;
- minimal objective requirements and explicit producer scale/stage/location assumptions;
- reproducible schedule range;
- single progressive L1 department budget with P10/P50/P90;
- optional CSV and Movie Magic/EP text-PDF actual budget merge;
- CanonicalProductionState and adapter to the existing optimizer;
- input fingerprint and explicit failure/status reporting.

Deferred are full AI taxonomy/multi-model, deeper schedule/import formats, L2/L3, XLSX, native MBD, UI redesign and every optimizer/incentive change.

Acceptance chain:

```text
supported script + minimum producer inputs + optional supported budget
  -> persisted structured scenes
  -> minimum requirements
  -> schedule and cost ranges
  -> CanonicalProductionState
  -> existing structures / NPC ranking
```

It must work after reload for an arbitrary Project, not only a fixture.

## 19. Little Utopia acceptance strategy

Available truth is a 44-line actual budget with $4,364,393 authoritative gross and a documented $2 leaf variance, partial/manual script facts and no actual schedule.

| Stage | Acceptance |
|---|---|
| Script structure | ≥98% sampled scene/slugline structural accuracy; ≥95% character/dialogue-link precision and recall; valid source spans |
| Requirements | all known material marine/period/night/VFX facts found or queued; zero unsupported high-material positives; no absence converted to false |
| L1 blind estimate | actual lies in P10–P90; P50 within ±35%; department P50 within ±50% for departments covering ≥80% of spend or explained exception |
| L2 blind estimate | P50 within ±20%; top departments within ±25% or explained by project deal; ≥90% actual spend maps without duplicates |
| L3 blind estimate | P50 within ±10% excluding disclosed unavailable project-specific ATL/financing terms; material departments within ±15–20%; all labor/rates/quotes disclose authority |
| Schedule | deferred until actual schedule supplied; then within max(3 days, 10%) and no missed marine/night/special-unit burden |
| Optimizer impact | same optimizer; estimated top-five set overlaps actual-budget baseline by ≥4/5 at L2/L3; actual leader appears in estimated top three; input-driven ranking changes are traceable |

Exact line equality is not required. Structural coverage, honest uncertainty, useful cost accuracy and stable downstream decisions are.

## 20. Failure-prevention controls

| Failure | Architectural control |
|---|---|
| False AI extraction | source spans/hash, staged evidence, deterministic lock, reconciliation and material confirmation |
| Rate hallucination | calculators accept persisted Rate IDs or explicit project values; Bridge has no rate fields |
| Cost-index misuse | mandatory localization policy and category-specific allowlist |
| Fixed-cost localization | major cast/rights/fixed deals default `GLOBAL_FIXED`; explicit override required |
| Fake precision | L1 rounding/ranges, authority labels and reproducible distributions |
| Schedule underestimation | scene-work capacity, pages/day bounds and explicit move/night/restricted/special-unit checks |
| Missing prep/wrap | L2/L3 material department requires duration source or blocker |
| Fringe omission | labor lines require applicability/value/unknown; L3 blocks on material unknown |
| Overtime omission | schedule/work pattern creates OT assumption; line requires rule or disclosed range |
| Duplicate budget lines | immutable import key, stable lineage, active-leaf rollup and source-total reconciliation |
| Script/budget disagreement | typed discrepancy plus shadow delta; actual stays effective until authorized |
| Stale local rates | effective/verified dates, soft/hard stale policy and immutable estimate snapshots |
| Low-confidence high-cost input | material queue plus provisional-state blocker |
| Silent source replacement | precedence, Override, ProjectActivity and source-version fingerprint |
| Territoriality by payer | separate service, goods-use, residency and payer fields; payer alone never qualifies |

## Major deferred scope

- full scheduling operations, call sheets and production reporting;
- creative/story coverage;
- provider-specific or paid-API-required AI logic;
- XLSX/native MBD until real parsers and fixtures exist;
- worldwide role-level rate maintenance before Tier A/B is sustainable;
- production UI redesign;
- any incentive-rule or optimizer change;
- any claim of Little Utopia schedule accuracy before a real schedule exists.

## Reconciliation basis

Existing/runtime truth comes from:

- `SCRIPT_ANALYZER_EXISTING_CAPABILITY_RECONCILIATION.json/.md`
- referenced served runtime, parser, model, budget, cost and Bridge modules.

Production-domain recommendations come from:

- `GEMINI_SCRIPT_ANALYZER_BTL_ARCHITECTURE.json/.md`.

Where they differed, repository evidence controlled what exists. Production-domain logic controlled what is required. The architecture does not average conflicting recommendations: for example, sluglines are deterministic first because a deterministic parser already exists, while AI remains an exception for malformed/ambiguous source text.
