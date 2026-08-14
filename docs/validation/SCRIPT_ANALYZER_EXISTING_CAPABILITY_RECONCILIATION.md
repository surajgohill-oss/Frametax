# CineGlobe Script Analyzer / Production Cost Engine

## Existing-capability reconciliation

**Repository:** `surajgohill-oss/Frametax`

**Branch:** `claude/audit-frametax-features-NZcX5`

**As of:** 2026-08-14

**Scope:** repository and served-runtime reconciliation only; no implementation, optimizer review, incentive research, or UI work.

## Final gate

`SCRIPT_ANALYZER_RECONCILIATION_COMPLETE`

The evidence is sufficient to distinguish `REUSE`, `EXTEND`, `CONNECT`, `REPLACE`, and `BUILD_NEW` for the next phase.

## Controlling conclusions

1. **Script ingestion is not an active analysis path.** A useful deterministic raw-text parser exists, but only a demo and tests call it. The mounted ingestion system stores and classifies documents without producing screenplay chunks/elements or feeding production planning.
2. **Production Package Intelligence is active, but it is a translation layer.** It reshapes supplied budget, people, script-attribute, location and travel facts; it deliberately extracts nothing. The served Little Utopia package has `script.known=false`, although eight attributes were manually supplied from a one-time read.
3. **There is no production schedule engine.** Schedule is only a classified material category. Fixed `shoot_days=30` and hotel/per-diem days of 35 in a generic crew manifest are cost assumptions, not a schedule.
4. **Budget parsing is the strongest reusable upstream capability.** CSV import is mounted; Movie Magic/EP PDF-text parsing is robust but not connected to that endpoint. XLSX is accepted but incorrectly sent through the CSV parser. Native MBD and semantic FDX parsing do not exist.
5. **The served optimizer uses a Little Utopia-specific 44-account budget snapshot.** Generic uploaded project budgets do not become canonical `/api/v1/cineglobe` inputs.
6. **Local-cost normalization actively affects NPC/ranking, but its input data is not actual rate data.** It uses 44 unsourced static country profiles, generic indices and default crew/budget assumptions. There are no job-specific crew scales, union/CBA rules, equipment packages, stage inventories, location fees or construction/material rate cards.
7. **The manual Bridge should be reused, not rebuilt.** Export/import, provider identity, content hashes, validation, persistence, reconciliation and human disposition are working. Script operation names are reserved but unsupported; script packages, response schemas, evidence spans and element-level reconciliation require extension.
8. **The existing optimizer remains the downstream authority.** The missing work is upstream analysis, scheduling, estimation, generalized input authority and handoff—not another incentive or structure engine.

## Runtime verification

The frontend default API base is `frametax2/frontend/src/api.js -> /api/v1/cineglobe`. Those routes read the single cached state built by `frametax2/backend/app/demo/little_utopia_state.py`, not the generic project/document calculation route.

Direct runtime inspection produced:

| Observation | Value |
|---|---:|
| Production | The Little Utopia |
| Budget known | yes |
| Budget line items | 44 |
| Authoritative gross | $4,364,393 |
| Script known | no |
| Script filename in package | none |
| Manually supplied script attributes marked known | 8 |
| Missing package inputs | 11 |
| Generated production structures | 177 |

Targeted verification covered budget text/PDF parsing, Production Package Intelligence, production adjustment, manual Bridge runs and reconciliation: **183 tests passed**. The full suite was intentionally not run.

## Classification key

| Status | Meaning |
|---|---|
| `ACTIVE_RUNTIME` | Demonstrably consumed by a mounted endpoint and/or served CineGlobe production path. |
| `IMPLEMENTED_NOT_ACTIVE` | Executable implementation exists but the served path does not consume it. |
| `PARTIAL` | Useful behavior exists, but the stated capability or handoff is incomplete. |
| `LEGACY` | Superseded by or disconnected from the canonical served path. |
| `TEST_ONLY` | Only test/demo use is evidenced. |
| `SCHEMA_ONLY` | Persistence/transport shape exists without an active producer/consumer path. |
| `DOCUMENTATION_ONLY` | Described but not implemented. |
| `UNKNOWN` | Evidence is insufficient. |

## Exact active paths

### Script

```text
Upload/discover
  -> universal document classification
  -> review/commit
  -> Document + DocumentVersion
  -> STOP
```

There is no automatic path from a committed screenplay to `ScreenplayDocument.raw_text`, `ScreenplayChunk`, `ExtractedScriptElement`, `ScreenplayParseResult`, ProductionPackage, schedule, cost estimate or optimizer.

Little Utopia is a production-specific exception:

```text
one-time human read of opening scenes + synopsis/look-book
  -> hardcoded SCRIPT_REQUIREMENTS + eight known attributes
  -> build_production_package
  -> known/unknown facts and selected discovery/qualification inputs
```

This is not a reusable screenplay analysis runtime. Source comments explicitly preserve `script.known=false` because no full page-by-page parse exists.

### Budget

Generic mounted path:

```text
POST /documents/upload
  -> BudgetDocument
POST /projects/{id}/budgets/import
  -> parse_budget_csv
  -> deterministic classification
  -> BudgetLineItem persistence
  -> STOP before canonical /cineglobe state
```

Canonical Little Utopia path:

```text
verified 44-account budget snapshot
  -> BudgetIntelligence
  -> account allocation / movable-spend hints
  -> production structures
  -> incentive + travel + FX + local-cost pricing
  -> NPC ranking
```

The legacy mounted DB calculation path loads the latest budget document into `run_full_analysis`, but supplies no cost benchmark, no fringe rules and no FX rates; stacking and qualification integrations remain TODO. It is not the frontend's canonical structures path.

### Schedule

```text
Upload/discover
  -> category = schedule
  -> Document material-presence flag
  -> STOP
```

No schedule model, parser, stripboard, day estimator, grouping, duration calculation or schedule-to-cost handoff was found.

### Known production variables

For Little Utopia, facts, people, location and economics controls can hydrate/recompute the in-memory state and then affect package questions, discovery, qualification, allocation and pricing. This is partly fixture/process-local and partly DB-aware. A generic project's `ProjectFact` records do not instantiate an equivalent canonical optimizer state.

## Relevant component inventory

| Component | Classification | Existing capability | Controlling limitation |
|---|---|---|---|
| `app/ingestion/screenplay_parser.py` | `IMPLEMENTED_NOT_ACTIVE` | Raw-text chunks; approximate pages; headings; character cues; heading locations; confidence/origin flags | Demo/test callers only; no LLM pass despite designed fields |
| `app/models/screenplay.py` | `SCHEMA_ONLY` | Document, chunk and extracted-element tables with confidence/confirmation | No parser-to-table or table-to-optimizer path |
| `app/calculators/production_package_intelligence.py` | `ACTIVE_RUNTIME` | Budget/script/location/travel translation, hints, unknowns, questions | Extracts nothing; depends on caller inputs |
| universal ingestion and classifier | `PARTIAL` | Discover/classify/dedup/review/commit screenplay, budget and schedule documents | Content is not converted into production facts |
| `app/api/v1/documents.py` | `PARTIAL` | PDF/CSV/XLSX/TXT/FDX storage and PDF/text extraction | Semantically creates BudgetDocument; canonical state disconnected |
| `app/ingestion/budget_parser.py` | `PARTIAL` | CSV, generic text, Movie Magic/EP account parsing and reconciliation | PDF parser not in mounted import; XLSX/native MBD absent |
| budget line classifier | `ACTIVE_RUNTIME` | Broad deterministic ATL/BTL/department/labor/compensation/QPE-candidate taxonomy | Unmatched lines default to BTL/MISC/nonlabor/cash |
| `app/api/v1/budgets.py` | `PARTIAL` | Persists parsed CSV line items | XLSX defect; no PDF path; no canonical handoff |
| `little_utopia_real_budget.py` | `ACTIVE_RUNTIME` | Real 44-account fixture with source pages and $2 variance | Production-specific snapshot, not a live import |
| static local-cost profiles | `ACTIVE_RUNTIME` | Country cost/travel/risk indices and regional fallbacks | Unsourced assumptions, not rate cards |
| `production_adjustment.py` | `ACTIVE_RUNTIME` | GREENFIELD/EXISTING_BUDGET quantity-rate/index delta trace | Served use retains generic default quantities and bases |
| `production_normalization.py` | `ACTIVE_RUNTIME` | Travel, FX and non-travel local cost deltas | Static data; no schedule-derived quantities |
| `LocalCostBenchmark`, `UnionFringeRule`, `FXRate` models | `SCHEMA_ONLY` | DB shapes include source/as-of/confidence | Canonical path uses Python snapshots; real datasets absent |
| union/fringe calculator | `IMPLEMENTED_NOT_ACTIVE` | Applies supplied rules deterministically | Only dormant path calls it and passes an empty list |
| DB `structures.py` calculation | `LEGACY` | Budget lines to immutable calculation result | Not canonical; key inputs absent/TODO |
| generic `optimization.py` | `LEGACY` | Generic optimization endpoints | Current UI uses `/cineglobe`, which bypasses it |
| `little_utopia_state.py` | `ACTIVE_RUNTIME` | State, discovery, allocation, structures, pricing and ranking | Single-production, fixture-based and Mauritius-anchored |
| universal Document/Version/Source | `ACTIVE_RUNTIME` | Source, checksum, version and provenance | Typed analysis handoffs disconnected |
| `ProjectFact` | `ACTIVE_RUNTIME` | Source type/version/location, confidence, review state | No centralized value-precedence service |
| production structure/calculation schemas | `PARTIAL` | Components, constraints, scenarios and input snapshots | Canonical structures are primarily in-memory |
| Bridge manual run/reconciliation/persistence | `ACTIVE_RUNTIME` | Offline provider workflow and human disposition | Current contracts are economics/audit-oriented |
| Bridge script/prebudget operation enums | `SCHEMA_ONLY` | Names reserved | Explicitly unsupported |
| synthetic production demo | `TEST_ONLY` | Shows parser + CSV + package composition | Not served and not authoritative |

The complete machine-readable inventory is in the companion JSON.

## Script Analyzer gap matrix

| Capability | Existing component | Status | Runtime output | Provenance/confidence | Gap | Decision |
|---|---|---|---|---|---|---|
| Upload/versioning | universal ingestion | Partial | Document/Version | strong | no semantic script dispatch | `REUSE + CONNECT` |
| PDF screenplay extraction | PDF utilities | Partial | budget raw text only | document source | no screenplay routing/layout model | `EXTEND + CONNECT` |
| FDX | extension accepted | Missing | none | file only | no XML parser | `BUILD_NEW` |
| Pages/eighths | parser rough page count | Partial/inactive | `page_count` | approximate | no page-layout/eighth model | `EXTEND + CONNECT` |
| Scenes/sluglines | regex parser | Partial/inactive | scene heading element | context/confidence | no stable scene graph/body/page eighths | `EXTEND + CONNECT` |
| INT/EXT and day/night | heading string | Partial/inactive | unnormalized text | deterministic | no normalized fields/variants | `EXTEND` |
| Locations/recurrence | heading-derived location | Partial/inactive | location element | context/confidence | no canonicalization, recurrence, stage/practical | `EXTEND + CONNECT` |
| Characters | ALL-CAPS cue heuristic | Partial/inactive | character element | context/confidence | false positives; no scene/dialogue linkage | `EXTEND + CONNECT` |
| Dialogue/speaking roles | none | Missing | none | none | no dialogue blocks or burden | `BUILD_NEW` |
| Cast burden/availability | people facts only | Partial | person/fact | source/review | not scene-derived; no availability model | `EXTEND` |
| Background/extras/crowds | none | Missing | none | none | no extraction or quantities | `BUILD_NEW` |
| Props/wardrobe/makeup/prosthetics | budget taxonomy only | Missing for script | budget categories | budget source | no scene elements/complexity | `BUILD_NEW`, reuse names |
| Vehicles/animals/minors | budget fragment or none | Missing | none | none | no counts, links or compliance flags | `BUILD_NEW` |
| Stunts/weapons/intimacy | stunt attribute placeholder | Missing | caller-supplied AttributeFact only | state/confidence | no extraction/per-scene safety facts | `EXTEND schema + BUILD extraction` |
| VFX/SFX | VFX attribute + budget lines | Partial | AttributeFact/BudgetIntelligence | manual/budget source | no shot/scene counts or practical/digital split | `EXTEND` |
| Period/design/set builds | manual period + budget categories | Partial | facts/requirements | manual/budget source | no script-based complexity | `EXTEND` |
| Marine/aerial/weather | attribute placeholders; manual marine fact | Partial | AttributeFact/fixture | manual evidence | most categories and scene logistics absent | `EXTEND` |
| Specialty equipment/construction | budget categories | Partial | requirements from spend | budget source | no script-to-quantity derivation | `REUSE downstream + BUILD upstream` |
| Music/performance | attribute + music budget | Partial | facts/budget | supported | no performance/playback/licensing extraction | `EXTEND` |
| Travel/units/company moves | location/travel shapes | Partial | movements/roles | known/unknown | caller supplied, not script/schedule derived | `REUSE + CONNECT` |
| Safety/logistics | free-form manual requirements | Partial | fixture/questions | manual notes | no systematic taxonomy/extractor | `EXTEND` |
| AI chunking | screenplay parser | Implemented/inactive | chunk records | indices/text | no persistence/redaction/model workflow | `REUSE + EXTEND` |

## Scheduling gap matrix

| Capability | Status | Evidence | Decision |
|---|---|---|---|
| Schedule upload/classification | Partial | Document category and project material flag | reuse document pipeline; build semantic parser |
| Schedule model/stripboard | Missing | no schedule entity or scene-day assignment | `BUILD_NEW` |
| Shoot-day/pages-per-day estimate | Missing | generic 30-day cost default only | `BUILD_NEW` |
| Location/day-night grouping | Missing | no grouping engine | `BUILD_NEW` |
| Company moves/unit splits | Partial shape only | caller-supplied travel/location roles | reuse shapes; build scheduler |
| Cast availability | Missing for scheduling | people facts have no scheduling consumer | `EXTEND` |
| Prep/wrap calendars | Partial assumption only | 35 travel days vs 30 shoot days | replace with confirmed/modelled durations |
| Schedule-to-cost handoff | Missing | no quantity/duration producer | `BUILD_NEW` |

**Active scheduling capabilities: none beyond document classification/material presence.**

## Budget and cost capability matrix

| Capability | Support | Runtime truth |
|---|---|---|
| CSV parsing | Supported | mounted generic API, not canonical optimizer |
| Movie Magic/EP PDF-text parsing | Supported but disconnected | strong parser used in tests/data preparation |
| XLSX | Missing/defective | binary content is passed to CSV parser |
| Native MBD | Missing | no parser |
| Budget taxonomy | Supported | broad deterministic categories; unsafe catch-all default |
| ATL/BTL/post/department totals | Supported | active for supplied Little Utopia budget |
| Local labor | Partial | country crew index/payroll percent, not actual role rates |
| Local crew rate cards | Missing | no roles/scales/overtime/CBA data |
| Fringes | Partial | generic active percentage; real union calculator inactive and empty |
| Equipment/stage | Partial | LA-index multipliers, not packages/facilities/rates |
| Location costs | Partial | permits/transport/legal indices, no location fees/quantities |
| Travel/lodging/per diem | Supported with assumptions | quantity-rate traces; defaults unless supplied |
| Vehicles/construction/materials | Partial | actual-budget categories only; no estimator datasets |
| Insurance/bond/finance/post | Partial | actual-budget categories; no complete estimate formulas |
| FX | Partial | active static snapshot; DB schema inactive |
| Jurisdiction multipliers | Supported with limitations | 44 static profiles plus fallbacks, unsourced |
| Schedule-sensitive costs | Missing | only supplied/default day counts |
| Quantity × rate × duration | Partial | calculation pattern exists, actual inputs do not |
| Actual-budget supersession | Partial/disconnected | schema/legacy route support it; canonical state does not |

## Three-level readiness

### Level 1 — rapid/global estimate: `PARTIALLY_SUPPORTED`

Reusable:

- 44 explicit jurisdiction cost profiles and regional fallback;
- travel, FX and non-travel local-cost delta calculators;
- global production structure comparison and ranking;
- actual-budget category aggregation.

Missing:

- screenplay-to-production-scale inference;
- shoot-day/schedule estimate;
- cited/validated cost indices;
- a generic project state builder;
- an estimate that works from a script when no actual budget exists.

Decision: **extend/connect** existing normalization and ranking; **build** upstream script/scale/schedule estimate inputs.

### Level 2 — production-informed estimate: `PARTIALLY_SUPPORTED`

Reusable:

- department/spend taxonomy;
- ProductionPackage known/unknown variables and questions;
- location/travel role shapes;
- CrewManifest and ProductionBudgetParams input shapes;
- deterministic quantity-rate adjustment traces.

Missing:

- full structured breakdown;
- breakdown/schedule-to-quantity conversion;
- departmental crew, equipment, stage and location assumptions;
- prep/shoot/wrap durations;
- actual local cost data.

Decision: **reuse/extend** package, taxonomy and calculator contracts; **build** breakdown and scheduling logic.

### Level 3 — detailed line-budget estimate: `MISSING`

Reusable foundations are actual-budget parsing/persistence, classification and some line-item trace shapes. There is no detailed budget generator, crew-role/department model, rates/overtime/CBA dataset, departmental duration engine, equipment/stage/location/construction/material rate data, or full estimate-line authority model.

Decision: **build new** detailed-estimate capability while reusing parsing, taxonomy, provenance and actual-budget supersession concepts.

## Existing local-cost data

### Controlling classification

`HARDCODED ASSUMPTION + GENERIC MULTIPLIER`, **not actual rate data**.

`frametax2/backend/app/data/location_cost_benchmarks.py` contains 44 explicit profiles:

`AE AR AT AU BE BG BR CA CH CL CO CZ DE DK ES FI FR GB GR HR HU IE IL IN IT JP KR MA MT MU MX NL NO NZ PL PT RO RS SE SG SI TH US ZA`

It also provides regional fallback and ultimately a US-shaped LOW-confidence placeholder.

| Property | Evidence |
|---|---|
| Currency/basis | USD values; indices use Los Angeles = 1.0 |
| Effective date | module-wide “2024-2025 reference rates”; no record-level dates |
| Stated confidence | 30 HIGH, 14 MEDIUM explicit profiles |
| Source citations | 0 of 44 records populate `data_sources` |
| Granularity | one country/country-hub profile; no city, role, union, seniority, vendor, season or package dimension |
| Runtime | active in every canonical structure through local-cost normalization |
| Served inputs | gross budget only; generic crew/sub-budget defaults remain |

Categories include airfare, hotel/apartment, per diem, crew/equipment/stage/post/VFX indices, permits/visas, local transport, freight/carnet, payroll/fringe/overhead, legal/accounting, local-hire percentage, catering and risk adjustments.

Missing are validated sources, per-field dates, actual crew rates, union/CBA/fringe rules, equipment packages, stage/facility inventories, location fees, construction/material rates, city/region variation and schedule/project-specific quantities.

The repository's description of these profiles as “real” does not override the record evidence: no sources are populated, and the values are static broad assumptions.

## Bridge reuse

**Status: `REUSE_CORE_EXTEND_CONTRACTS`.** The workflow supports independent offline model work without paid API calls.

Reuse unchanged:

- manual self-contained package folders;
- provider identity and content hashes;
- response import and schema validation boundary;
- ProviderResponse persistence;
- multi-provider reconciliation framework;
- human disposition and provenance patterns.

Extend:

- script-specific package builder;
- screenplay/chunk confidentiality and redaction rules;
- stable scene/chunk/element IDs;
- production-breakdown taxonomy;
- evidence-span and element-confidence response schema;
- element-level reconciliation keys;
- persistence into staged and then user-confirmed elements/facts.

The existing `script_production_analysis` and `prebudget_structure_generation` operations are reserved but explicitly unsupported. The current audit `ReviewResponse/Finding` contract and Little Utopia economics package are not script-analysis contracts.

## Deterministic, AI and authority responsibilities

| Task | Controlling role | Guardrail |
|---|---|---|
| file type, checksum, versioning | Deterministic | user resolves ambiguous classification |
| FDX structure and PDF text/layout | Deterministic | AI only for malformed/ambiguous text |
| page/eighth count, scene number, slugline parsing | Deterministic | preserve source spans |
| character/dialogue linkage and recurrence | Deterministic first | AI only for format ambiguity |
| element mentions (props, wardrobe, vehicles, animals, crowds, etc.) | AI extraction | evidence span + user confirmation |
| stunt/VFX/design/logistics complexity | AI interpretation | rationale/confidence + user confirmation |
| grouping, moves and schedule calculation | Deterministic | producer constraints control |
| availability, locations, crew/stage decisions | User confirmed | store as sourced assumptions |
| local rates and market data | External validated data | negotiated quote overrides |
| quantity × rate × duration, fringes, FX, totals | Deterministic | AI must not invent economics |
| actual budget and schedule | User confirmed | deterministic parse/reconciliation |
| incentives, structures, NPC and ranking | Existing deterministic optimizer | do not rebuild |

## Source-of-truth compatibility

Target hierarchy:

```text
ACTUAL USER BUDGET / SCHEDULE / KNOWN VARIABLE
  > CONFIRMED PRODUCTION ASSUMPTION
  > STRUCTURED SCRIPT EXTRACTION
  > ESTIMATED MODEL DEFAULT
```

Current compatibility is **partial**.

Reusable foundations:

- Document/Version/Source store origin, version and checksum;
- typed budget/screenplay records can link to DocumentVersion;
- ProjectFact stores source type, source version/location, confidence and review status;
- ExtractedScriptElement supports confidence and confirmation;
- StructureCalculationResult stores document version, fingerprint and immutable input snapshot;
- ingestion commit is human-gated.

Missing/disconnected:

- no central precedence resolver implements the hierarchy;
- no schedule authority model;
- no source tier/override model for estimated lines;
- generic project facts and budgets do not rebuild the canonical state;
- Little Utopia mixes fixture, process-local override and DB-hydration patterns.

Recommendation at reconciliation level: reuse the existing document/fact/version provenance and extend it with controlling-source resolution; do not create a parallel authority system.

## Little Utopia fixture availability

| Fixture | Availability | What is actually present |
|---|---|---|
| Script | Partial | Migration metadata for screenplay PDF; pending extraction; one-time opening/synopsis/look-book read; eight manual attributes; no full parse/chunks/elements |
| Budget | Strong | 44 accounts; $4,364,393 authoritative gross; $4,364,395 leaf sum; $2 documented variance; category/page/territorial mappings |
| Schedule | None | no content, parse, stripboard or shoot-day derivation |
| Known variables | Partial/strong | people, facts, location requirements, economics controls, overrides; important questions remain unknown |
| Parsed data | Budget only | no full script or schedule parse |
| Breakdown | Weak/manual | requirements derived from budget spend and manual notes, not screenplay analysis |
| Estimated data | Coarse | travel/FX/local-cost assumptions, not screenplay-derived estimate |

Safe future fixture reuse includes the real budget/reconciliation, version provenance, manual script facts as comparison labels, known/unknown question behavior, and downstream structure compatibility. The manual facts must not be treated as proof of automated extraction.

## Major disconnected components

1. Screenplay DocumentVersion → typed screenplay/chunks/elements.
2. Coarse screenplay parser → ingestion/API/project runtime.
3. ScreenplayParseResult → active ProductionPackage.
4. Script breakdown → schedule.
5. Schedule → cost quantities and durations.
6. Generic uploaded budget → canonical CineGlobe state.
7. Movie Magic PDF parser → mounted import API.
8. XLSX import → valid parser.
9. FDX upload → semantic parser.
10. Cost/fringe/FX DB schemas → canonical pricing.
11. Reserved Bridge script operation → script contracts and element reconciliation.
12. Project provenance → a central controlling-value resolver.

## Reuse map

| Component | Decision |
|---|---|
| universal document ingestion/version/provenance | `REUSE + CONNECT` |
| deterministic screenplay coarse pass | `EXTEND + CONNECT` |
| screenplay typed schemas | `EXTEND + CONNECT` |
| ProductionPackage known/unknown/question model | `REUSE + EXTEND` |
| budget/Movie Magic parser | `REUSE + CONNECT` |
| budget taxonomy/intelligence | `REUSE`, harden catch-all behavior |
| production adjustment trace/toggles | `REUSE` with validated inputs |
| travel/FX/local-cost separation | `REUSE` |
| ProjectFact/calculation provenance | `REUSE + EXTEND` |
| manual Bridge core | `REUSE`; extend script contracts |
| production structures/optimizer | `CONNECT ONLY`; do not rebuild |
| XLSX-as-CSV import | `REPLACE` |
| schedule engine | `BUILD_NEW` |
| full breakdown and Level 3 generator | `BUILD_NEW` |

## Legacy/obsolete paths for this phase

- Generic `app/api/v1/optimization.py`: mounted but superseded for the current UI by `/api/v1/cineglobe`.
- DB `app/api/v1/structures.py` full-analysis route: mounted but not canonical and missing critical supplied inputs.
- `scripts/run_production_demo.py`: useful example only, not a served runtime or production architecture.

## Unresolved architecture questions

These are decisions for the next design phase, not evidence gaps that block this reconciliation:

1. Which screenplay formats are mandatory first: FDX, screenplay PDF, Fountain, or a bounded subset?
2. Does `ScreenplayDocument` remain the typed canonical root, or become a projection from universal DocumentVersion?
3. How are stable scene/element IDs maintained across draft revisions?
4. Which extracted facts require confirmation before affecting schedule/cost?
5. Which schedule interchange formats and user schedule source are canonical?
6. Do estimates use BudgetLineItem or a distinct estimate-line model so estimated and actual values cannot be confused?
7. Which licensed/authoritative datasets replace static local-cost assumptions?
8. How do city/region/union/season/vendor rates resolve beneath country profiles?
9. Where does the universal source-precedence resolver live?
10. How is a generic multi-project state builder connected without reopening optimizer logic?
11. What screenplay confidentiality, retention and redaction rules govern Bridge export?

## Evidence index

- `frametax2/backend/app/api/v1/cineglobe.py`
- `frametax2/backend/app/demo/little_utopia_state.py`
- `frametax2/backend/app/ingestion/screenplay_parser.py`
- `frametax2/backend/app/calculators/production_package_intelligence.py`
- `frametax2/backend/app/ingestion/budget_parser.py`
- `frametax2/backend/app/calculators/classify_budget_line_items.py`
- `frametax2/backend/app/data/little_utopia_real_budget.py`
- `frametax2/backend/app/data/location_cost_benchmarks.py`
- `frametax2/backend/app/calculators/production_adjustment.py`
- `frametax2/backend/app/calculators/production_normalization.py`
- `frametax2/backend/app/api/v1/documents.py`
- `frametax2/backend/app/api/v1/budgets.py`
- `frametax2/backend/app/api/v1/structures.py`
- `frametax2/backend/app/models/screenplay.py`
- `frametax2/backend/app/models/budget.py`
- `frametax2/backend/app/models/cost.py`
- `frametax2/backend/app/models/fx.py`
- `frametax2/backend/app/models/project_fact.py`
- `frametax2/backend/app/models/library_document.py`
- `frametax2/backend/app/bridge/schema.py`
- `frametax2/backend/app/bridge/manual_run.py`
- `frametax2/backend/app/bridge/package_builder.py`
- `frametax2/backend/app/bridge/reconciliation.py`
- `frametax2/backend/alembic/versions/0063_migrate_little_utopia.py`
- `frametax2/frontend/src/api.js`
- `frametax2/frontend/src/lib/ingestion.js`
- `frametax2/docs/architecture/CAPABILITY_LEDGER.md` (corroboration only; runtime/source inspection controls)
