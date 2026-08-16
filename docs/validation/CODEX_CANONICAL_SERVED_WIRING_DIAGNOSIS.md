# Codex Canonical Data -> Served Project Output Wiring Diagnosis

Date: 2026-08-16

Active branch: `claude/audit-frametax-features-NZcX5`

HEAD reviewed: `c05b38ba5e8abf56e5a6254fa529e86d3e4b0af1`

Final gate: **CODEX_WIRING_DEFECTS_LOCALIZED**

Scope was limited to data/wiring diagnosis. No economic rule, optimizer, UI, MFNI, Script Analyzer, or production code was changed.

## Executive result

The headline jurisdiction economics are not being flattened by React. For FVD, the canonical calculator produces and persistence stores 30 priced jurisdiction results with differentiated QPE, selected incentive, and NPC. `canonical_production_view.py` preserves those headline numbers in each structure object.

The served-product break is a status/trace contract failure:

1. The FVD evaluator bypasses the existing provenance-rich `CanonicalProductionState`/`ProductionOptimizerInput` path and assembles a second, thinner input set. Missing territorial facts become empty sets, script requirements are replaced by `{}`, and every relocation receives the same nominal budget with no regional/travel/FX normalization.
2. Persistence records the 30 priced results, but its segment serializer drops cap, rate-band, floor/ceiling incentive, confirmation, statutory-basis, and account-register fields.
3. The view adapter marks 29 priced FVD alternatives as non-priceable in the **ranking entry** because they are not regionally comparable. Overview and Scenarios filter on that overloaded flag and expose only the Greece baseline as comparable.
4. Workspace and Globe instead filter/classify on the **structure entry**, where the same 29 rows remain `is_fully_priced=true`. Thus the screens consume one endpoint but disagree about the same structures.
5. Capability-only persistence flattens four distinct rejection causes into `UNPRICEABLE_AUTHORITY_INSUFFICIENT` and omits program identity, even where the actual reason is a statutory threshold failure.

This is enough evidence for a bounded repair without another audit.

## A. Actual served engine paths

All normal production routes use the mature project-scoped component tree:

`/projects/:projectId/overview|workspace|scenarios|globe`

Each calls:

`useCineGlobe(projectId)` -> `GET /api/v1/cineglobe/projects/{project_id}/state`

The backend then splits by project title.

### Little Utopia

`get_project_state()` -> title equals `The Little Utopia` -> `get_production/get_package/get_structures/get_economics/...` -> `app.demo.little_utopia_state.get_state()` and `build_allocated_structures()`.

Classification: **canonical validated in-memory/demo runtime**. Persisted `canonical-1.1.0` rows are not the served economic universe for LU.

### F#K Valentine's Day

`get_project_state()` -> non-demo branch -> `canonical_production_view.build_production_and_structures()` -> `Project.leading_structure_id` -> leading result's `input_fingerprint` + `engine_version` -> persisted `ProductionStructure` / `StructureCalculationResult` rows -> mature UI response.

Classification: **persisted canonical-1.1.0 evaluation through a generic view adapter**.

The generic FVD response substitutes `EMPTY_PKG`, `EMPTY_ECONOMICS`, `EMPTY_PEOPLE`, `EMPTY_FACTS`, and empty recommendations/legal shapes for sections not wired to the generic persisted evaluation. Therefore the structure cards have economics, but FVD's Overview Budget Rail has no `pkg.register`, production requirements are empty, and the richer QPE trace available to LU is absent.

### Split architecture finding

There is one frontend endpoint but two backend economic universes:

- LU: current in-memory canonical demo state, 177 structures.
- FVD: current persisted `canonical-1.1.0` fingerprint, 110 structures.

The old stripped `/projects/{id}/summary` page still uses `/projects/{id}/workspace`, but it is not the normal Overview/Workspace/Scenarios/Globe route and did not contaminate this trace.

## B. Little Utopia trace

Direct calculator state and served API values match because the LU project-state route calls the same functions directly.

| Jurisdiction | Canonical/served QPE | Rate treatment | Selected incentive | Served NPC | Rank/status | Result |
|---|---:|---|---:|---:|---|---|
| MU current | $4,355,327.00 | 30% floor / 40% discretionary ceiling; floor selected | $1,306,598.10 | **$3,057,794.90** | rank 1 | MATCH |
| GR relocation | $3,491,514.40 after $562,681.60 80%-cap exclusion | flat 40% | $1,396,605.76 | $4,019,127.24 | rank 24 | MATCH |
| MT relocation | $4,054,196.00 | 30% floor / 40% discretionary ceiling; floor selected | $1,216,258.80 | $3,906,254.20 | rank 23 | MATCH |
| AU relocation | $4,054,196.00 | Location Offset threshold does not resolve at this QPE | $0 | not priced | unavailable | MATCH |

LU direct-runtime and API traces retain `qpe_cap_applied_usd`, `is_band_ceiling`, `ceiling_requires_confirmation`, incentive floor/ceiling, program identity, blockers, and account traces. That field completeness is not preserved in the FVD path.

LU canonical -> served: **PASS**.

## C. FVD trace

Source gross budget: **$4,517,687.00**. Current persistence universe: fingerprint `bb48c6e76623545f7718ebff65cfd14bfd8ff47ea4c6cbd07ec6a5b7473ae79f`, engine `canonical-1.1.0`.

The table compares the canonical calculator object with persistence/API. Headline economics match; trace-detail losses are identified separately.

| Jurisdiction | Canonical eligible/QPE | Rate/cap treatment | Canonical selected incentive | Canonical NPC | Served headline | Served status |
|---|---|---|---:|---:|---|---|
| GR current | $4,154,821 eligible; **$3,614,149.60 QPE** after $540,671.40 80%-cap exclusion | flat 40% | $1,445,659.84 | **$3,072,027.16** | MATCH | comparable, rank 1 |
| CA-NL | $4,154,821.00 | 40% floor / 45% ceiling; confirmation required, floor selected | $1,661,928.40 | $2,855,758.60 | MATCH | priced structure, review ranking |
| MT | $4,154,821.00 | 30% floor / 40% ceiling; confirmation required, floor selected | $1,246,446.30 | $3,271,240.70 | MATCH | priced structure, review ranking |
| MU | **$1,132,056.00** | 30% floor / 40% ceiling; confirmation required, floor selected | $339,616.80 | $4,178,070.20 | MATCH | priced structure, review ranking |
| AU-QLD | $4,154,821.00 | flat 15% | $623,223.15 | $3,894,463.85 | MATCH | priced structure, review ranking |
| AU Location Offset | $4,154,821.00 versus current modeled minimum-QPE bound $10,000,000 | threshold unmet | none | not priced | amount/status MATCH; exact program/threshold not served | unavailable, mislabeled authority-insufficient |

FVD canonical -> served: **FAIL overall**. The surviving headline values match, but material explanation/status fields are lost and 29 real priced results are filtered out of the comparable surfaces.

## D. FVD one-comparable-option root cause

Current candidate accounting is exact:

- 110 persisted current structures
- 30 structures with real QPE/incentive/NPC
- 1 comparable baseline
- 29 priced but review-required alternatives
- 80 unpriceable candidates

Verified chain:

1. `canonical_evaluation._price_candidate()` prices 30 jurisdictions.
2. `canonical_evaluation.evaluate_project()` sets `relocation_cost_normalized=true` only for the base. Every relocation is false because generic regional/travel/in-kind replacement costs are absent.
3. `canonical_production_view.build_production_and_structures()` defines `comparable = priced && relocation_cost_normalized`, putting all 29 priced alternatives in `review_required`.
4. The adapter creates a ranking entry for each priced alternative, then overwrites that ranking entry's `is_fully_priced` to false.
5. `productionOptions.selectTopOptions()` and `Scenarios.jsx` filter on `ranking.is_fully_priced`, so only GR remains in Overview/Scenarios.

Cause classifications:

- **MISSING_PROJECT_FACT**: regional/travel/in-kind relocation inputs are absent.
- **ADAPTER_FILTER**: the adapter overloads `is_fully_priced` to mean directly comparable.
- **FRONTEND_FILTER**: Overview/Scenarios treat the overloaded ranking flag as economic priceability.

This is not an incentive/QPE failure and is not cured by pretending MFNI exists. The 29 differentiated incentive results already exist. The repair is to preserve separate `priced` and `comparable` states and display incentive-level economics consistently without claiming unmodeled savings.

## E. Repeated-value diagnosis

FVD's 30 priced current rows already contain these repeated groups before the adapter or frontend runs:

- gross budget: one value across all 30 (`$4,517,687`)
- QPE: `$4,154,821` for 28, `$3,614,149.60` for GR, `$1,132,056` for MU
- selected incentive: 9 distinct values
- NPC: 9 distinct values

Classification:

### Gross budget

**LEGITIMATELY_EQUAL** under the current canonical-evaluation input contract. Every full-relocation candidate intentionally starts from the production's same nominal budget; MFNI/travel/FX/local-cost deltas are hard-set to zero in this path.

### Repeated QPE

**CANONICAL_VALUES_NEVER_COMPUTED from differentiated territorial project facts / MISSING_QPE_RESULT INPUT**, not adapter flattening.

FVD has no `budget_accounts_outside_base_jurisdiction` or `budget_offshore_payroll_accounts` facts. `canonical_project_economics._fact_account_set()` converts an absent fact to an empty set, and `canonical_evaluation` creates empty production requirements with `derive_production_requirements({})`. The full-relocation allocator then sends the same account set to each candidate. Most current doctrines resolve to the same $4,154,821 eligible set; GR's 80% cap and MU's doctrine are the two material QPE differentiators.

This input assembly bypasses the provenance-rich canonical state that previously kept territorial location/residency UNKNOWN. It is a verified substitution boundary, not a frontend calculation.

### Repeated incentive/NPC groups

**LEGITIMATELY_EQUAL given the current canonical inputs**, but poorly explained in the FVD payload. Programs often resolve to the same effective selected rate even when their headline ceilings differ. Examples:

- CA-NL (40% selected floor), QA (40% selected floor), and SG (40% selected modeled rate) all produce $1,661,928.40.
- MT, EG, IL, MN, MX, MY, TW, and US-NY all produce $1,246,446.30 under their current selected effective treatment.

There is no `BASELINE_VALUE_COPIED`, `STALE_RESULT_REUSED`, or frontend numeric substitution in these headline fields. The defect is that the FVD trace drops the fields needed to explain why equal values are lawful/current-model outcomes.

## F. QPE / threshold / rate / cap propagation

| Field | Canonical -> persistence | Persistence -> FVD API | UI consequence |
|---|---|---|---|
| gross budget | PASS | PASS for priced rows; null on unpriceable rows | repeated nominal gross shown/fallback used |
| final QPE | PASS in segment | PASS for priced rows | cards can show differentiated QPE |
| threshold result | calculator applies | only generic reason survives | exact program/threshold unavailable for FVD AU |
| rate floor/ceiling | PASS | PASS | headline rate survives |
| cap amount/rule | calculator produces `qpe_cap_applied_usd` | **FAIL: omitted by `_segment_dicts`** | GR QPE is correct but 80%-cap derivation is invisible |
| band/discretion | calculator produces band + confirmation fields | **FAIL: omitted** | selected floor can look inconsistent with displayed ceiling |
| incentive floor/ceiling | calculator produces both | **FAIL: omitted**; only selected top-level incentive survives | uncertainty band cannot be explained |
| selected incentive | PASS | PASS | headline amount matches |
| NPC | PASS | PASS | headline amount matches |
| register/account reason | calculator produces `register_trace` | **FAIL: omitted** | FVD Budget Rail has no QPE trace |

The exact loss begins in `canonical_evaluation._segment_dicts()`. It serializes only program, account codes, QPE, excluded spend, rates, doctrine, and blockers. It omits `is_band_ceiling`, `statutory_basis`, `incentive_floor_usd`, `incentive_ceiling_usd`, `ceiling_requires_confirmation`, `qpe_cap_applied_usd`, `register_trace`, and notes before persistence.

`globeData.buildCountryHoverData()` then asks for `segment.incentive_ceiling_usd`. That field exists in LU's rich demo structures but cannot exist in FVD's generic payload, so the FVD Globe shows “Modeled Incentive: Not available” even though `selected_incentive_usd` is persisted and served at structure level.

## G. Rejection/status and program identity

All 80 current FVD unpriceable rows persist the same candidate status: `UNPRICEABLE_AUTHORITY_INSUFFICIENT`.

Their actual persisted reason text divides into:

- 75 authority-insufficient
- 3 non-guaranteed/selective
- 1 superseded
- 1 canonical-rule rejection (AU threshold/conditions unmet)

The flattening occurs in `canonical_evaluation.py`'s `classification == "capability_only"` branch, which unconditionally stores the authority-insufficient status. It also omits `program_slug` from the trace and stores no segments. Consequently the adapter/API cannot identify the program or exact threshold for the AU rejection.

Classifications:

- AU: **CANONICAL_RULE_REJECTION**, persisted incorrectly as authority-insufficient.
- 75 rows: **AUTHORITY_INSUFFICIENT**.
- selective/superseded rows: **OTHER_VERIFIED**, flattened into authority-insufficient.
- missing program slug in served unpriceable rows: **PROGRAM_IDENTITY_FAILURE at persistence**.

## H. Treaty and structure status

Current served structure metadata is honest but incomplete:

- LU: 1 current/single-country, 88 full-relocation, 88 component-relocation, 0 treaty slugs. The 88 multi-participant component structures remain Hybrid/Component because the frontend requires explicit `treaty_slug`; they are not falsely called co-productions.
- FVD: 1 current/single-country and 109 full-relocation; no split/component or treaty structure is generated.
- `canonical_production_view` hardcodes `treaty_slug=None` because the generic evaluator does not create or persist treaty structures.

Therefore current/base and full-relocation status survive. LU component status survives. No current structure is falsely promoted to official treaty status. Explicit treaty metadata cannot be proven through the FVD generic path because that path never generates it; this is a bounded generation/persistence limitation, not a current false treaty label.

## I. Stale and mixed evaluation rows

Stale/mixed rows exist:

| Project | Stored generations |
|---|---|
| FVD | 4 legacy `0.1.0`; 110 `canonical-1.0.0`; 110 `canonical-1.1.0` |
| LU | 1 `demo-runtime-2026-08-05`; 110 `canonical-1.0.0`; 110 `canonical-1.1.0`; plus the separate in-memory 177-structure served state |

Current pointers are correct:

- FVD leading structure `d349e0f1-e37c-47d7-882a-cabcbec9f4b6`, `canonical-1.1.0`, GR, NPC $3,072,027.16.
- LU leading structure `31933b5d-f66c-4631-bcbd-cd6a10f6383a`, `canonical-1.1.0`, MU, NPC $3,057,794.90.

FVD's adapter scopes rows to the leading result's fingerprint/version, so legacy and 1.0 rows do not contaminate current FVD output. LU ignores all persisted economics and serves the in-memory demo runtime. Thus:

- stale/mixed data present: **YES**
- current served numeric contamination: **NO**

LU's `production.leading_structure_id` is a persisted UUID while its served demo structure IDs are strings such as `ALLOC-BASELINE-MU`. Current UI selection falls back to rank 1 and does not use that UUID for economics, so this is a verified mixed-identity seam but not the source of the current LU NPC.

## J. Overview / Scenarios / World / Workspace consistency

Endpoint/source: **SAME SOURCE** for all four normal screens.

Interpretation: **DIVERGENT STATUS CONSUMPTION**.

- Overview: `selectTopOptions()` filters `ranking.is_fully_priced`; FVD shows 1 option.
- Scenarios: same ranking filter; FVD shows 1 comparable column and 109 Review/Needs Validation rows.
- Workspace: `visibleStructures()` ignores ranking priceability and cards use `structure.is_fully_priced`; priced FVD alternatives show numeric QPE/incentive/NPC.
- World/Globe: `structureTier()` also uses `structure.is_fully_priced`; the same 29 review candidates become Jade/alternative and expose NPC, although their ranking entries say not fully priced.

This is not a divergent backend universe. It is an overloaded contract consumed inconsistently by four frontend modules.

## K. Minimal verified defect chain

### DEFECT 1 — canonical project evidence is thinned before evaluation

**VERIFIED**

FVD canonical facts contain script-derived data but no territorial account facts -> `canonical_project_economics` bypasses `CanonicalProductionState` and converts absent territorial facts to empty sets -> `canonical_evaluation` also supplies empty production requirements -> full relocation allocates the same nominal account set to each destination -> 28 candidates share QPE $4,154,821 and many programs collapse into equal effective-rate groups.

### DEFECT 2 — priced and comparable are conflated

**VERIFIED**

29 alternatives have persisted QPE/incentive/NPC -> adapter correctly builds priced structure entries -> adapter excludes them from comparison due missing relocation normalization -> adapter rewrites ranking `is_fully_priced=false` -> Overview/Scenarios expose only baseline -> Workspace/Globe still treat the same rows as priced.

### DEFECT 3 — rich segment trace is dropped before persistence

**VERIFIED**

Canonical `SegmentEconomics` contains cap, band, confirmation, floor/ceiling incentives, and register trace -> `_segment_dicts` omits them -> DB/API cannot expose them -> FVD cap/band reasoning and Budget Rail trace disappear -> Globe asks for an omitted incentive field and shows “Not available.”

### DEFECT 4 — rejection causes and program identity are flattened

**VERIFIED**

Discovery has distinct authority, selectivity, superseded, and statutory-condition reasons -> capability-only branch stores every row as authority-insufficient and does not store its program -> adapter/API cannot state the actual program/threshold -> 80 unavailable rows appear more uniform than the canonical reasons.

### DEFECT 5 — generic project sections are replaced with empty shapes

**VERIFIED**

FVD has real budget, script, requirements, people/facts tables, and persisted segment economics -> project-state route returns empty package/economics/people/facts shapes and `physical_requirements={}` -> Overview/Workspace lose the budget-register and requirements trace even while structure headlines render.

Verified defects count: **5**.

## L. Smallest Claude repair sequence

No new engine and no UI redesign are required.

1. **`backend/app/services/canonical_project_economics.py` and `canonical_evaluation.py`**
   - Defect: evaluation bypasses existing canonical state provenance, treats absent territorial facts as empty-known sets, and supplies empty requirements.
   - Correction: reconnect the evaluator to existing canonical project-state/handoff values, or minimally preserve UNKNOWN/blocker/provisional semantics and pass the already-persisted script requirements. Do not invent territorial facts.
   - Verify: FVD evaluation input reports provenance for base/budget/requirements; absent territorial inputs remain explicit; candidate/QPE trace states which facts were unknown.

2. **`backend/app/services/canonical_evaluation.py::_segment_dicts`**
   - Defect: existing `SegmentEconomics` fields are discarded before persistence.
   - Correction: persist the existing cap, band, statutory basis, floor/ceiling incentives, confirmation, register trace, and notes fields verbatim. This is serialization only.
   - Verify: FVD GR API exposes QPE $3,614,149.60 and cap-applied $540,671.40; MT exposes 30%/40%, confirmation required, floor/ceiling dollars; account trace reconciles.

3. **`canonical_evaluation.py` capability-only persistence**
   - Defect: all unpriceable causes become authority-insufficient and program identity disappears.
   - Correction: persist `program_slug` and the actual terminal class already known from discovery/rate resolution (`RULE_REJECTED`, authority-insufficient, selective, superseded). Do not re-evaluate rules.
   - Verify: AU is a rule/threshold rejection with `au_location_offset`; the 75 authority-insufficient rows remain authority-insufficient; counts reconcile to 80.

4. **`backend/app/services/canonical_production_view.py`**
   - Defect: ranking `is_fully_priced` is overloaded to mean comparable.
   - Correction: preserve economic `is_fully_priced` and add/use an explicit existing-status field such as `is_directly_comparable`/`relocation_cost_normalized`. Never rank unnormalized savings, but do not erase priceability.
   - Verify: FVD remains 1 directly comparable + 29 priced/review + 80 unpriceable; every priced/review row retains QPE/incentive/NPC.

5. **`frontend/src/lib/productionOptions.js`, `Scenarios.jsx`, `Workspace.jsx`, and `globeData.js`**
   - Defect: screens interpret the same structure inconsistently.
   - Correction: consume the same explicit priced/comparable/status fields. Show existing incentive-level QPE/rate/incentive for priced review candidates without assigning numeric rank or savings; label them Review consistently in Workspace/Globe. Read the restored segment incentive field.
   - Verify: Overview, Scenarios, Workspace, and Globe agree on 1 comparable, 29 priced-review, 80 unavailable; the same structure has the same status and headline values everywhere.

6. **`backend/app/api/v1/cineglobe.py::get_project_state` / `canonical_production_view.py`**
   - Defect: FVD's real generic data is replaced by empty package/requirements/economics shapes.
   - Correction: adapt existing persisted budget/register/requirements fields into the already-defined response sections; do not recreate calculations.
   - Verify: FVD Budget Rail reconciles to the same segment QPE, production requirements are non-empty, and no Little Utopia package data leaks in.

7. **Targeted contract tests**
   - Add one DB -> API -> pure frontend-adapter fixture for FVD covering GR, MT, MU, AU-QLD, and AU.
   - Retain the narrow LU oracle exactly: Mauritius, NPC $3,057,794.90.
   - Assert stale `0.1.0`/`canonical-1.0.0` rows never appear in current API output.

Do not implement MFNI in this repair. Its absence must remain an explicit comparability limitation, not a reason to hide already-computed incentive economics.

## M. Runtime verification performed

- Live PostgreSQL project/evaluation/fingerprint/leading-row trace.
- In-process project-state API retrieval for LU and FVD.
- Direct bounded canonical calculator traces for FVD GR, CA-NL, MT, MU, and AU-QLD.
- Current AU Location Offset threshold-rule inspection from the repository's accepted rate registry.
- `14 passed`: `test_canonical_evaluation.py`, `test_canonical_production_view.py`, and the narrow LU baseline test.
- `14 passed`: frontend Overview/Scenarios classification-contract tests.

## Final gate

**CODEX_WIRING_DEFECTS_LOCALIZED**

The exact loss/substitution boundaries are now identified in input assembly, persistence serialization, view-adapter status mapping, and frontend status consumption. Claude can repair them in the sequence above without reopening optimizer or jurisdiction validation.
