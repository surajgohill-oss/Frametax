# MFNI Database / Research Reconciliation Audit — Codex

Audit date: 2026-09-05. Repository: `surajgohill-oss/Frametax`. Branch: `claude/audit-frametax-features-NZcX5`. Audited source commit: `a6883eb`; application engine: `canonical-1.52.0`.

Scope: current local canonical database, current repository code, and remotely tracked AG research. Database probes used explicit read-only transactions; no evaluation, ingestion, migration, external research, production modification, or optimizer P0 remediation was performed. Only the three requested audit artifacts are delivered.

## 1. EXECUTIVE VERDICT

**NO_GO_FOR_CONSOLIDATED_MFNI_INTEGRATION**

AG research is recoverable, and the current storage/consumption gaps are identified. However, the final certification cannot be ingested as fully researched, economically usable data: its field statuses were broadly assigned, its post/VFX evidence describes incentives rather than costs, and its geographic rows include duplicate and multi-region service-area identities.

This is a bounded ingestion-quality gate. It does not authorize or require a new worldwide research sweep. Claude can preserve the recovered observations and build explicit unresolved/quote-input states in one authorized pass, but must not turn the certification's unsupported cells into facts or numerical factors.

## 2. DID AG ACTUALLY POPULATE THE MFNI DATABASE?

**NO_RESEARCH_ARTIFACTS_ONLY**

This answer describes AG's research sweep, not the absence of all older application data.

- Database `local_cost_benchmarks`: **131 rows**, one per jurisdiction, all `DISCOVERY`, all `as_of_date=2025-06`. All creation/update timestamps are 2026-08-05. Their sources explicitly say production-market knowledge, unverified against primary labour-cost surveys.
- Database `union_fringe_rules`: **0 rows**.
- Active static store `location_cost_benchmarks._PROFILES`: **44 profiles**, all with empty `data_sources`, no field-level effective dates; version `1.0.0`. Git history attributes that file to `cbe84e4`, the original production-adjustment implementation, not AG's research closeout.
- AG final jurisdiction and certification files: **207 rows each**. No production loader imports them.
- AG `MFNI_ACTUAL_WORLDWIDE_OBSERVATIONS.json`: **10 raw observations**, not database rows.
- No `mfni_raw_observation`, `mfni_normalization_index`, or `mfni_jurisdiction_factor` table exists in the inspected public schema. Those table names occur in a schema-recommendation artifact.
- Database jurisdiction metadata contains no additional MFNI/cost-benchmark population.

The database rows and source constants predate the AG sweep and differ from its observations. Neither their existence nor a coincidentally matching number proves AG ingestion.

## 3. CANONICAL MFNI DATA ARCHITECTURE

There is **no single consolidated MFNI truth store today**.

| Layer | Exact owner | Current role |
|---|---|---|
| Research | `docs/validation/MFNI_*.md/.csv/.json` | Documentary recovery inputs; no runtime loader |
| Jurisdiction identity | `backend/app/models/jurisdiction.py::Jurisdiction`, table `jurisdictions` | 187 rows; 177 exact AG code matches |
| Broad program identity | `backend/app/data/global_inventory.py::ALL_PROGRAMS` and imported inventory modules | 211 jurisdiction codes: AG's 207 plus ACP/EU/IBERO/NORDIC |
| Relational benchmarks | `backend/app/models/cost.py::LocalCostBenchmark`, table `local_cost_benchmarks` | 131 legacy benchmark rows; disconnected from canonical evaluator |
| Relational fringe model | `backend/app/models/cost.py::UnionFringeRule`, table `union_fringe_rules` | Schema exists; zero data |
| Seed definitions | `global_inventory.py::ALL_BENCHMARKS`, `global_inventory_extended.py`, migrations 0012/0015/0026/0029 | Current imported ALL_BENCHMARKS has 60 entries; later migrations explain additional DB rows |
| Active cost profiles | `backend/app/data/location_cost_benchmarks.py::JurisdictionCostProfile/_PROFILES` | 44 direct numeric profiles consumed by production adjustment |
| Active travel benchmarks | `backend/app/calculators/travel_model.py::_BASE_FARES_USD/_HOTEL_RATES_USD/_PER_DIEM_USD` | Separate fare tables; hotel/per-diem coverage 39 countries |
| FX | `production_normalization.py::FX_RATE_SNAPSHOTS` and `fx_refresh.py` | Existing local-cost conversion/scenario overlay; not a new MFNI program |
| Served economics | `canonical_evaluation.py::_relocation_normalization` → `production_normalization.py` → `allocation_pricing.py` | Reads static calculators, then adds deltas to NPC |

All application paths above are relative to `frametax2/`. The relational model's statement that it “drives BTL rebasing” is not proof of current consumption: the canonical evaluator never loads `LocalCostBenchmark`. The legacy structure-calculation helper supplies `cost_benchmark=None`; its public calculate endpoint is retired.

Example of conflicting stores: GB database crew multiplier **0.90**, stage **0.88**, lodging **280 USD**; active static profile crew **0.80**, stage **0.78**, hotel **350 USD**. MU database crew **0.35**, stage **null**, lodging **110 USD**; static profile crew **0.50**, stage **0.55**, hotel **200 USD**. A bulk copy must not silently overwrite or conflate these distinct legacy estimates.

## 4. AG RESEARCH CORPUS INVENTORY

All eight MFNI files listed here are tracked and retrievable from the shared remote branch.

| Artifact | Exact content inventory | Treatment |
|---|---|---|
| `MFNI_GLOBAL_RESEARCH_AG.md` | 231,533 bytes; 118 explicit jurisdiction research headings | Narrative evidence; inconsistent closing counts and incomplete indexing |
| `MFNI_CANONICAL_JURISDICTION_RECONCILIATION_AG.csv` | 207 unique codes; 151 empty `mfni_section` pointers | Research universe and identity claims |
| `MFNI_CANONICAL_COVERAGE_CERTIFICATION_AG.csv` | 207 unique codes × 10 category statuses | Derived closeout statuses, not stored facts |
| `MFNI_GLOBAL_COVERAGE_MATRIX_AG.csv` | 193 unique exact-code rows; six category columns | Underlying structured content; final column is explicitly incentive economics |
| `MFNI_ACTUAL_WORLDWIDE_OBSERVATIONS.json` | 7 sources, 10 observations, 2 normalization indices, 5 crew-capacity records, 8 coverage records, 3 gaps | Actual observation-shaped recovery inputs; not independently reverified in this audit |
| `MFNI_DATABASE_SCHEMA_AND_DATA.json` | Recommendation for 3 tables; 4 sources; 2 sample observations; 2 sample normalization rows | Samples/design, not production population |
| `MFNI_GLOBAL_PRODUCTION_COST_RESEARCH.md` | Methodology, proposed category factors and assumptions | Earlier proposal; not current calculation authority |
| `MFNI_WORLDWIDE_RESEARCH_REPORT.md` | Revises the earlier import-ratio/confidence-band proposal | Preserve supersession; do not implement the rejected arbitrary bands |

Also inspected: MFNI portions of `AG_GLOBAL_RESEARCH_CERTIFICATION_FINAL.md`, `AG_GLOBAL_RESEARCH_CLOSEOUT_FINAL.md`, and `PHASE2_TARGETED_BACKFILL_FINAL_REPORT_AG.md`.

The earlier final certification explicitly calls coverage partial because labor/OT, travel/living, construction, and security columns are absent. The later closeout calls all rows complete with quote-dependent fields. The local, untracked `final_certification_builder.py:28-82` explains that transition: it assigns seven categories quote-dependent for every jurisdiction, payroll/permits “authority”, labor by country-prefix/subnational classification, primary-sources-present true, and remaining-gap none. It does not read underlying source observations for those decisions. This script is corroborating local evidence only and is not part of the committed handoff.

The tracked certification itself independently demonstrates the synthetic pattern: **7** quote-dependent cells per row, while `quote_dependent_fields` says **6** for all 207 rows. Therefore actual generated quote-status cells total **1,449**, versus the recorded **1,242**. None is a canonical typed quote record.

The main narrative contains only one URL occurrence (the Git remote); source names and tier labels are usually free text. Preserve them as source identifiers, not as independently verified field-level evidence. The missing FR heading also leaves French TRIP/withholding text under CA's section. Do not ingest by nearest heading alone.

## 5. 207-JURISDICTION RECONCILIATION

AG total **207 = 124 sovereign-labelled + 83 subnational-labelled**. These are AG's code-format labels, not a new geopolitical determination: its builder classifies codes containing a hyphen as subnational.

All 207 codes exactly match a current global-inventory identity. The database contains 177 exact matches and lacks 30. The 187 database rows reconcile as **177 AG matches + 10 outside this fixed AG corpus** (ACP, EU, FO, GL, IBERO, IM, NORDIC, PK, PY, XK). No extra jurisdiction was inserted into the 207-row audit.

- Relational MFNI benchmark matches: **131**.
- Direct static profile matches: **44**.
- Overlap: **42**.
- Union with actual numerical MFNI values: **133** (CH and SI are static-only).
- Full ten-category MFNI records: **0**.
- Partial legacy numeric records: **133**.
- Neither a DB nor a direct static MFNI record: **74**.
- Evidence of AG-origin canonical numeric ingestion: **0**.
- Identity/scope blockers: **13** (specified in section 13).

The output population statuses partition exactly:

| Status | Rows |
|---|---:|
| FULLY_POPULATED | 0 |
| POPULATED_WITH_QUOTE_DEPENDENT_FIELDS | 0 |
| PARTIALLY_POPULATED | 133 |
| NO_CANONICAL_MFNI_RECORD | 36 |
| RESEARCH_ONLY_NOT_INGESTED | 25 |
| IDENTITY_BLOCKED | 13 |
| Total | 207 |

“Research-only” in the strict matrix partition is 25 rows: inventory identity exists, DB/static MFNI does not, and there is no additional identity blocker. **All 207 AG research records remain documentary and un-ingested**; the 133 older numeric records are not exceptions to that conclusion.

The required artifact-match classification also reconciles: PARTIAL_CANONICAL_MATCH 133; CANONICAL_ROW_EXISTS_BUT_MFNI_MISSING 36; RESEARCH_ONLY_NOT_INGESTED 25; IDENTITY_MISMATCH 12; DUPLICATE_CANONICAL_TARGET 1; EXACT_CANONICAL_MATCH 0; NO_CANONICAL_TARGET 0. Here “partial match” means overlapping categories/identity, not agreement between AG facts and legacy numbers.

## 6. CATEGORY DATABASE COVERAGE

The accompanying category CSV includes all ten requested categories plus eight additional modeled fields. Counts distinguish numeric benchmark presence from verified research and actual category completeness.

AG counts below use **exact-key, structured content** in the six-column matrix and ten raw observations, excluding the final generated certification. They are a reproducible structured-ingestion count, not a claim that narrative-only research is absent. For example, GB has narrative labor/travel/construction material not represented by a keyed cost observation; US/CA contain embedded subnational material. Such evidence must retain its location/context when extracted.

“Populated” means an explicit numerical index/value exists for that category, even if DISCOVERY/unprovenanced. “Partial” means only part of the requested category exists (e.g. crew index without OT; generic fringe without tax bases/caps). Neither means authoritative or calculation-ready. Each category's populated + partial + quote-dependent + missing = 207.

| Category | AG keyed content | Numeric populated | Partial | Typed quote | Missing | Direct static consumer coverage | Observed target coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| labor_ot | 5 | 0 | 133 | 0 | 74 | 44 | 35 |
| fringes | 196 | 0 | 44 | 0 | 163 | 44 | 35 |
| stages | 193 | 133 | 0 | 0 | 74 | 44 | 35 |
| locations_permits | 193 | 0 | 131 | 0 | 76 | 0 | 0 |
| equipment | 193 | 133 | 0 | 0 | 74 | 44 | 35 |
| catering | 193 | 133 | 0 | 0 | 74 | 0 | 0 |
| travel_living | 0 | 0 | 133 | 0 | 74 | 39 | 31 |
| construction_materials | 0 | 0 | 0 | 0 | 207 | 0 | 0 |
| security_safety | 0 | 0 | 0 | 0 | 207 | 0 | 0 |
| post_vfx_cost | 0 | 133 | 0 | 0 | 74 | 0 | 0 |

Every category has **0 relational DB rows consumed by the canonical optimizer**. The CSV notes give exact non-null DB counts and stored-but-unused counts. Direct static consumer coverage is the number of jurisdictions with a direct usable lookup, not all jurisdictions for which a fallback can return a number. Observed target coverage intersects those direct lookups with the current persisted normalization destinations; the trace does not retain a per-field execution log.

For post/VFX cost, the AG six-column “Post/VFX Incentive Economics” field is excluded from cost evidence. For fringes, the 193-row matrix plus raw US-CA, CA-BC, and AU-NSW observations yields 196 exact-key jurisdictions. The five raw labor locations are US-CA, CA-BC, GB-LON, AU-NSW, and HU (Budapest scope must remain attached).

## 7. QUOTE-DEPENDENT DATA MODEL SUPPORT

**No canonical typed representation of PRESENT_QUOTE_DEPENDENT exists in the active model.**

`JurisdictionCostProfile` requires numeric floats and has only profile-level confidence, notes, and data_sources. It cannot distinguish field-level authoritative values, commercial benchmarks, quote-dependent variables, missing evidence, or not applicable.

`LocalCostBenchmark` has nullable numbers, free-form JSON overrides, source/date/confidence fields. A null cannot distinguish quote dependency from missing data or not applicable; generic JSON could hold a string but no typed contract, validation, or consumer enforces it. `UnionFringeRule` cannot represent hourly contributions, tiered taxable bases, or overtime schedules through its single rate field alone.

Required statuses must be separate from the value: authoritative structured observation, industry benchmark, quote-dependent, missing research, not material/not applicable. Quote-dependent must permit a null amount and carry scope, source evidence, requested input, and quote validity. No guessed numerical replacement is authorized.

## 8. OPTIMIZER CONSUMPTION TRACE

Exact executable path:

`canonical_evaluation._price_candidate / _price_component_relocation_candidate`
→ `_relocation_normalization(inputs, target_code, allocated_usd)`
→ `production_normalization.compute_local_cost_normalization(target, original, gross_budget)`
→ `production_adjustment.calculate_production_adjustment`
→ `location_cost_benchmarks.get_profile_or_fallback(code)`
→ `allocation_pricing.price_allocated_structure(local_cost_delta_usd=...)`.

Direct profiles: AE, AR, AT, AU, BE, BG, BR, CA, CH, CL, CO, CZ, DE, DK, ES, FI, FR, GB, GR, HR, HU, IE, IL, IN, IT, JP, KR, MA, MT, MU, MX, NL, NO, NZ, PL, PT, RO, RS, SE, SG, SI, TH, US, ZA.

There is no parent lookup. The canonical caller supplies no region, so the regional-fallback map is not used on this path. All **163** AG codes without a direct profile receive copied US baseline values with LOW confidence, not their country's profile. Subnational codes such as US-NM and CA-MB therefore bypass existing, more specific DB benchmark rows.

Active non-travel cost categories: freight/carnet, visa/work permit, payroll fringe and overhead, local transport, legal/accounting, local-hire premium, equipment, stage/facility, contingency. Labor uses crew index/local-hire assumptions, not workday/OT rules.

Disconnected categories: DB location fees, catering, post/VFX indices, marine override, construction, and security. Airline/hotel/per-diem use the separate travel-model tables, with generic fallback fare USD4,200, hotel USD200/night, and per diem USD80/day where lookup data is absent.

## 9. RUNTIME CONSUMPTION TRACE

A read-only query mirrored `current_result_fingerprint`: newest persisted fingerprint per project under `canonical-1.52.0`. It retrieved **4,659 structures across 14 projects**, not all historical generations.

- **4028** current result traces contain an adjustments object.
- **1786** contain a nonzero local-cost delta.
- **100** distinct normalization destination codes are observed; **99** are in the frozen AG corpus.
- Of those 99, **35** resolve a direct cost profile; **64** use US-placeholder fallback.
- The additional runtime code is **AE-AD (Abu Dhabi)**. It is absent from both AG's 207-code universe and the DB jurisdiction table; runtime doctrine identifies it. This is an observed coverage delta, not an added audit row.
- The trace stores aggregate adjustments, but not a complete per-field MFNI source/version record.

Read-only pure-function probes of the same normalization code:

| Destination / origin | Local-cost delta | Evidence |
|---|---:|---|
| US-NM / US-CA | USD0.00 | Both codes fall back to the same US profile despite New Mexico DB data |
| CA-MB / MU | USD729,300.00 | Manitoba receives US fallback: fringe/overhead 400,000; transport 1,800; legal 52,500; equipment 140,000; stages 135,000 |
| RO / GR | USD13,900.00 | Freight 7,500 + permits 6,400 under default crew/equipment assumptions |
| GB / MU | USD481,960.00 | Direct static profiles; still based on generic category budgets |

These probes supplied only destination, origin, and a USD4,364,393 gross budget. They did not alter DB state or claim real production quotes.

## 10. MFNI ECONOMIC PIPELINE

Current behavior:

Source budget → canonical line classification → source-amount jurisdiction/component allocation → incentive QPE/rate/caps → base NPC → additive benchmark local-cost/travel/FX deltas → adjusted NPC/ranking/persistence.

This is **not category-level destination repricing before QPE**. The local-cost bridge receives the actual total gross budget but no budget lines or scoped component quantities. It constructs default `ProductionAdjustmentInput` and overrides only `budget.total_budget_usd`.

Retained defaults: BTL USD3,000,000; gross payroll USD2,000,000; equipment shipment value USD500,000; legal/accounting USD150,000; equipment rental USD400,000; stages USD300,000; 32 traveling crew, 60 local crew, 30 shoot days. Most cost adjustments consequently do not reflect the actual project category totals. The source travel amount is reported for comparison but the active travel delta compares two modeled itineraries.

For a component relocation, the caller passes the target country and the whole project gross budget into the same bridge. It does not scope local-cost normalization to that component. FVD's Romania post allocation is USD146,446, but the normalization path still carries default production freight/permits rather than vendor/scope/post-rate economics.

The calculation is explicit in `allocation_pricing.py:936-950`:

`npc_verified = gross_budget - selected_incentive + financing_cost + implementation_cost`

`npc_adjusted = npc_verified + travel_delta + fx_delta + in_kind_delta + local_cost_delta`

Thus MFNI changes adjusted NPC and ranking today, but not the allocated amounts or incentive QPE. A future integration must state whether a cost is additive implementation overhead or a replacement production cost before it can safely change QPE.

## 11. FX BOUNDARY

No standalone FX jurisdiction/program family was found. The local-cost bridge disables its own profile FX-risk add-on, avoiding duplicate FX charges. The existing normalization service uses currency snapshots and an optional scenario conversion; canonical evaluation passes default zero scenario movement.

The raw AG observations preserve local currency, while active benchmark profiles are already USD at 2024–2025 reference rates. There is no current path converting those raw observations into category-local costs at the applied snapshot. Accordingly, the architecture partially respects the boundary but does not yet implement local-currency MFNI repricing.

Keep FX inside that existing conversion/repricing boundary. Preserve source currency, unit, observation date and applied snapshot; do not add a separate FX optimization layer or apply a second generic FX multiplier.

## 12. POST/VFX BOUNDARY

AG's six-column matrix explicitly labels its final column **Post/VFX Incentive Economics**. The narrative repeatedly reports tax-credit/rebate rates and uplifts. Those are incentive facts, not studio/vendor/labor cost observations.

The static profile has `post_production_index` and `vfx_index`; the DB has `post_production_multiplier` and `vfx_multiplier`. The current production-adjustment calculator has no post/VFX category and does not read these fields. Component routing correctly changes program allocation elsewhere, but its local-cost overlay is generic production overhead.

Preserve incentive eligibility/uplifts in existing program-rule owners. MFNI post/VFX needs project vendor, scope, workflow, local/imported labor, currency and quote data; “eligible for VFX credit” supplies none of those.

## 13. IDENTITY / DUPLICATE / PARENT-CHILD ISSUES

No duplicate jurisdiction codes or duplicate benchmark jurisdiction IDs were found in the inspected DB. No duplicate code appears in either 207-row AG CSV.

**13 blocked rows**, with no silent normalization:

1. **SA-KSA**: global inventory names Saudi Arabia, parent SA, “subnational”; its program is national selective support. Physical cost geography must resolve to existing SA, preserving separate program identity. Do not create a second Saudi economy.
2. **FR-IDF, FR-NAQ, FR-ARA, FR-OCC, BE-WAL, BE-VLG, BE-BRU, DE-NI**: exact DB rows exist but parent_id is null, while AG/inventory state FR/BE/DE. The proposed target is recorded; implementation must establish parent relationships explicitly.
3. **DE-MDM, DE-BB, DE-HH, NO-ROG**: names describe multi-region funding/service territories (Saxony/Saxony-Anhalt/Thuringia; Berlin-Brandenburg; Hamburg/Schleswig-Holstein; Rogaland/Vestland). They are not interchangeable with one atomic filming-cost market. DE-NI also describes Lower Saxony/Bremen and is already counted in the parent group. Preserve coverage-area identity separately from physical cost assignment.

The 30 AG codes without a DB row are:
GB-NIR, DE-MDM, IT-APU, IT-PIE, ES-EUS, AU-WA, AU-SA, DE-BB, DE-HH, DE-BW, IT-LAZ, IT-SIC, IT-CAM, IT-TOS, ES-CAT, ES-AND, ES-GAL, ES-VAL, GB-YRK, BF, SA-KSA, SE-SK, SE-AB, NO-ROG, NO-TRO, DK-CPH, AU-TAS, AU-NT, GB-LON, CA-PE.

All have inventory references; they are not proof of nonexistent jurisdictions. Apart from the blocked duplicate/service-area cases, an implementation can create/attach identity records from the known inventory in a controlled mapping.

The underlying six-column matrix lacks exact rows for these 14 AG codes:
AU-NSW, AU-QLD, US-GA, US-NY, DE-BY, CA-BC, CA-ON, CA-QC, US-CA, IT-LAZ, IT-TOS, ES-CAT, SE-AB, DK-CPH.

Some appear embedded in country narratives. Record explicit subnational scope when recovering them; do not inherit every parent value automatically.

Runtime AE-AD is outside the AG universe. The older research builder mentions the alias AE-AZ, but neither appears in AG's final 207 rows; AE is not proof that an Abu Dhabi-specific cost record exists. Preserve that known runtime coverage gap without expanding this audit.

## 14. RESEARCH-ONLY VS CANONICAL DATA

Use four separate axes:

- **SOURCE-RESEARCHED FIELD:** a located observation/narrative proposition with retained source and scope; not independently verified by this no-research audit.
- **DERIVED STATUS FIELD:** a classification derived from evidence, retained with the derivation.
- **GENERIC CLOSEOUT ASSUMPTION:** a blanket label such as the final certification's security quote dependency. It cannot be promoted to researched truth.
- **ACTUAL CANONICAL VALUE:** persisted benchmark/typed observation loaded by a defined consumer. The present legacy values are not AG data.

The ten raw observation records all resolve their seven-source register, but source linkage alone does not validate the claimed rate. For example, OBS_US_CA_001 is a camera-operator hourly wage linked to a source titled a global payroll-fringes matrix. Scope suitability must be checked against retained material before numeric promotion. The two sample observations in the earlier schema proposal must stay samples.

## 15. REQUIRED DATA INGESTION

One consolidated recovery/ingestion manifest must use the exact 207-row audit keys, preserve the 13 identity blockers, and retain record-level provenance.

Ingest documentary evidence as evidence first: ten observation-shaped rows and their source register; the 193 keyed matrix rows; applicable narrative fragments with stable section/line references and explicit jurisdiction/category scope. Retain the certification as a derived claim, not a source.

Do not load grant/rebate percentages from the post/VFX column into cost factors. Do not infer amount, currency, date, unit, coverage, or quote dependency when absent. Mark these unresolved. Preserve old DISCOVERY benchmarks alongside their actual lineage until an explicit supersession rule selects a supported replacement.

## 16. REQUIRED SCHEMA/MODEL CHANGES

Extend the existing cost domain (`models/cost.py` and its canonical repository/adapter), rather than creating a second pricing registry:

- Field-level evidence/status/value contract, including nullable quote-dependent values and missing/not-applicable states.
- Observation unit/currency, location/parent/coverage area, production scale, local/imported status, validity dates, source ID, citation location, and confidence basis.
- Separate raw observation from derived normalized factor; retain baseline, derivation and evidence inputs.
- Labor workday/OT schedules and structured fringe bases/caps/hourly contributions.
- Categories missing from the active schema: construction/materials, security/medical/safety, location permit scope, post/VFX vendor/scope.
- Quote input linked to project/component/vendor/scope and expiration; no global numeric placeholder.
- Data revision and per-result source references that invalidate persisted evaluation fingerprints.

No schema or data changes were implemented in this audit.

## 17. REQUIRED OPTIMIZER WIRING

Choose and document one owner: existing relational cost domain plus a validated adapter consumed by the current normalization path. Retire conflicting duplicate reads through that adapter only after parity/provenance tests; do not introduce a parallel optimizer.

Pass canonical classified budget lines, component scope, crew/schedule inputs and local/imported assignments into the existing cost adjustment path. Replace fixed USD2m payroll/USD400k equipment/USD300k stages assumptions when real scoped values exist. Preserve baseline-zero behavior.

Apply actual category repricing to allocated eligible costs before incentive computation where economically appropriate; keep non-QPE overhead additive and explicitly classified. Handle quote-dependent/missing data as conditional cost coverage, never zero-cost certainty or a copied US observation.

Wire location/catering/post/VFX/construction/security and field-level uncertainty. Persist exact data IDs/version, used values, assumptions and scope, then rank only under the existing admissibility contract. This does not remediate the separate optimizer P0s from the previous audit.

MFNI freshness is currently missing from `canonical_runtime_attribution._SEMANTIC_PRICING_MODULES`: the digest includes neither location-cost profiles nor production-adjustment/normalization/travel modules. Add canonical MFNI data revision and quote-input revision to the existing fingerprint when integration is authorized.

## 18. NO-ACTION ITEMS

Keep existing program identity/rate/QPE/stacking owners, canonical budget classification, baseline budget values, and existing FX conversion service. Existing deterministic calculators are reuse points. Do not rerun global incentive/MFNI research, import secondary-program economics, or modify optimizer P0/Globe work during this handoff.

The research proposal's abandoned fixed import percentages and arbitrary confidence bands are not requirements. No data value should be invented to fill a coverage count.

## 19. IMPLEMENTATION HANDOFF MANIFEST

| ID | Class | Exact change / owner | Deterministic acceptance |
|---|---|---|---|
| M01 | IDENTITY_RECONCILIATION | 13 blocked rows in reconciliation CSV; DB Jurisdiction parent/coverage mappings | SA cost geography counted once; eight parents explicit; multi-region coverage never masquerades as a single cost market |
| M02 | IDENTITY_RECONCILIATION | Remaining inventory-only IDs and runtime AE-AD coverage mapping | No automatic parent/alias numerical inheritance; missing cost coverage stays visible |
| M03 | DATA_ONLY | Preserve legacy 131 DB/44 static values and source history in reconciliation inputs | No unsupported overwrite; all old values remain visibly DISCOVERY/unprovenanced |
| M04 | SCHEMA_CHANGE | Existing cost-domain tables: typed observations/statuses/provenance/quotes | Quote-dependent null differs from missing/not-applicable; source/currency/unit required before numeric use |
| M05 | MODEL_CHANGE | JurisdictionCostProfile/cost adapter and structured labor/fringe models | No required float for quote-only state; tax caps/OT/unit semantics preserved |
| M06 | INGESTION_CHANGE | Exact-key source mapper for AG observation/matrix/narrative inputs | Idempotent input hashes; samples/certification assumptions quarantined; all 207 rows receive a recorded disposition |
| M07 | INGESTION_CHANGE | Evidence suitability and supersession checks | Existing source lineage resolves every promoted value; unsupported observations remain non-numeric/unresolved |
| M08 | OPTIMIZER_WIRING | _relocation_normalization → compute_local_cost_normalization → production_adjustment | Reads selected canonical cost records, not independent copied dictionaries |
| M09 | OPTIMIZER_WIRING | Component/category cost inputs → allocation/pricing | Scoped account amounts conserve budget; no full-shoot costs applied to a post-only relocation |
| M10 | OPTIMIZER_WIRING | Category consumers for currently disconnected fields | Location/catering/post/VFX etc. change only their real scoped costs; incentive uplift not used as a cost factor |
| M11 | RUNTIME_INPUT_SUPPORT | Project/component quotes and crew/schedule inputs | Explicit input-required condition; no invented quote/default crew presented as project fact |
| M12 | MODEL_CHANGE | Local-currency normalized observation → existing FX service | Exactly one conversion with snapshot/date; no standalone FX optimization |
| M13 | OPTIMIZER_WIRING | canonical_runtime_attribution and served trace | MFNI data/quote revision invalidates old result; trace identifies used category evidence |
| M14 | NO_ACTION | Incentive doctrine, parser, optimizer P0 remediation, Globe, secondary programs | No unrelated modification or re-audit |

**Before full numeric ingestion**, resolve the bounded blockers: source-backed dispositions for generated statuses, the 13 identity/scope rows, and field mapping/unit/validity conflicts for proposed promoted observations. If retained evidence cannot settle a field, the terminal disposition is unresolved or input-required with no invented value. That completes accounting, but does not certify fully researched or fully priceable global coverage.

## 20. EXACT COUNTS

- AG records: **207**; sovereign-labelled **124**; subnational-labelled **83**.
- Global inventory codes: **211**; exact AG identity matches **207**; excluded non-geographic groups **4**.
- DB jurisdictions: **187**; AG exact matches **177**; AG DB misses **30**; DB rows outside AG **10**.
- DB cost records: **131**; DB union-fringe records **0**.
- Static profiles: **44**; overlap DB/static **42**; union numeric coverage **133**; neither **74**.
- Complete ten-category records **0**; partial numeric **133**; typed quote-dependent records **0**.
- Pure canonical-row/no-cost cases **36**; inventory-only research cases **25**; identity-blocked **13**.
- AG numeric ingestion evidenced **0**; legacy numeric records with sourced AG lineage **0**.
- Source matrix **193**; final certification **207**; missing exact matrix rows **14**; missing section pointers **151**.
- Narrative jurisdiction headings **118**; raw observation rows **10**; sample observation rows **2** (not production data).
- Generated quote-status cells **1,449**; reported quote-field tally **1,242**.
- Current persisted runtime structures **4,659**, projects **14**, traces with adjustments **4028**, nonzero local-cost adjustments **1786**.
- Runtime normalization destination codes **100** = **99 AG + AE-AD**; AG direct-profile destinations **35**, AG placeholder destinations **64**.
- All numeric category counts and exact DB record IDs are in the accompanying CSVs. No fallback result is counted as stored population.

## 21. RISKS

**P0 — promotion risks, not claims that AG has already changed production:** blanket certification statuses or incentive percentages ingested as researched MFNI facts; SA duplicated as a second geography; multi-region fund scopes collapsed to an atomic cost market; conflicting legacy values overwritten without a selected source.

**P0 — current economic-consumption risk:** active cost data is disconnected from specific DB benchmarks and uses default project bases. CA-MB is priced from US placeholders despite a Manitoba DB record; component normalization is not restricted to the moved component. These figures affect adjusted NPC. No new remedy was implemented.

**P1:** missing quote schema, zero union-fringe population, disconnected cost categories, incomplete evidence/currentness, absent MFNI data/quote fingerprint and field-level trace.

**P2:** inconsistent narrative closeout counts, 6-versus-7 quote count, 151 empty section pointers, a misleading DB model consumption description, and “sovereign” labels derived from code punctuation.

## 22. FINAL GO / NO-GO

**NO_GO_FOR_CONSOLIDATED_MFNI_INTEGRATION**

The exact blockers are: **13 geographic identity/scope rows**, **generated category statuses without field-level research support**, and **unresolved source/unit/scope/currentness mappings needed before numerical promotion**. The 207-row artifacts cannot presently support an unqualified one-pass conversion into fully researched, economically usable MFNI data.

The handoff above is sufficient for a bounded, source-preserving integration with explicit unresolved/input-required outcomes. It is not permission for new research, silent defaults, secondary-program integration, or optimizer P0 remediation. Audit complete; implementation not started.
