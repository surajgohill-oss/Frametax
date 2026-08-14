# Codex SA-1.5 Independent Verification — F#K Valentine's Day

Generated: 2026-08-14T22:10:18Z

Branch: `claude/audit-frametax-features-NZcX5`

Final gate: **CODEX_REJECTS_SA1_5**

Master state: **SA-1.5 not closed; SA-2 remains HOLD.**

The real FVD screenplay, Greece budget, deck, deterministic parse, and persisted requirements are genuine. The rejection is architectural and runtime-specific: canonical state does not propagate the evidenced production base, shoot duration, currency, travel, or territorial facts, yet labels the project optimizer-ready. The worldwide ranking is produced by a project-specific runner that constructs the missing economics itself. The claimed UI proof and held-out calibration boundary also do not exist.

## HEAD reviewed

- Current remote HEAD at verification start: `242226d350b1b931fbc1ff68c37cbe38750e3970` — `Script Analyzer SA-1: generic script parse + CanonicalProductionState vertical slice`.
- Local Antigravity tip reviewed: `9d2fa9dd950d3f10c6a1b102f6d47c291b139bb5`.
- Antigravity commits reviewed: `fe59612`, `174cd82`, and `9d2fa9d`.
- Handoff finding: at verification start, the current remote branch lacked all three claimed SA-1.5 commits. The local branch was three commits ahead, so the Antigravity work was reviewed as a pending local diff from current remote HEAD.

## Exact 15-gate accounting

| # | Gate | Status | Independent basis |
|---:|---|---|---|
| 1 | real FVD budget | PASS | Current FVD `DocumentVersion` is the real `V-BRAT_V8_Greece_041224 TOPSHEET.pdf`, with exact file identity and FVD/Greece content. |
| 2 | budget reconciliation | PASS | PDF Grand Total $4,517,687.00 = parsed raw total = parsed USD total across 34 lines; $0.00 variance. |
| 3 | Greece provenance | PASS | **SOURCE FACT: Greece.** The actual budget says `PRELIMINARY BUDGET - GREECE`, `Location: Greece`, and `Greek Estimate Cash Rebate (40%)`. |
| 4 | full project-material discovery | PASS | Filesystem and staging ledger reconcile: all four top-level files and three nested Underwater files were discovered; relevant FVD materials were processed/stored. |
| 5 | semantic routing | PASS | FVD script, budget, deck, and deck-cover artwork were routed correctly; Underwater documents were stored under the separate Underwater project. |
| 6 | UI runtime | **FAIL** | **API_ONLY_VERIFIED.** Acceptance uses `httpx.ASGITransport`; no frontend caller or browser → frontend → network → backend → persistence trace exists. |
| 7 | canonical project state | **FAIL** | Live state is `READY_FOR_OPTIMIZER` and accepted while base jurisdiction and shoot days are null, currency is omitted, locations/territoriality are unknown, and no generic worldwide executor is called. |
| 8 | no generic Little Utopia contamination | PASS | No executable LU/MU/default-Mauritius dependency was found in the inspected generic state/handoff path. Comments and separate regression fixtures are not runtime contamination. |
| 9 | FVD runner is thin/generic | **FAIL** | Runner is **PROJECT_SPECIFIC_ORCHESTRATION (B)**: it constructs Greece facts/rate/doctrine, candidates, allocations, travel/FX, pricing, and ranking itself. |
| 10 | project facts provenance | **FAIL** | Script facts are version-linked, but evidenced Greece/18 days are not canonical assumptions; LA/1 traveler/4 rotations/14 nights/14 per-diems are arbitrary runner values. |
| 11 | actual-vs-modeled separation | PASS | Persisted Greece budget remains historical truth. Alternative allocation/pricing does not rewrite the actual `BudgetDocument` or lines. |
| 12 | held-out calibration fixture | **FAIL** | Fixture has no `SCRIPT_DERIVED_STATE` / `HELD_OUT_ACTUAL_PRODUCTION_STATE` boundary and embeds the actual budget in canonical state and optimizer input. |
| 13 | script-only architecture preserved | PASS | `BUDGET_MISSING` remains an explicit honest state and the architecture reserves later Level-1 estimation; FVD's budget was not encoded as a universal prediction feature. |
| 14 | genericity probe | **FAIL** | CA, budget, and shoot days map through the handoff, but source currency is not a first-class field and the handoff does not execute the optimizer. A new real project still needs custom orchestration. |
| 15 | Little Utopia regression | PASS | Targeted regression passed: `ALLOC-BASELINE-MU`, Mauritius rank 1, NPC **$3,057,794.90**. |

Failed gates: **6, 7, 9, 10, 12, 14**. No gate was blocked.

## FVD budget identity

| Field | Verified value |
|---|---|
| Source file | `/Users/Suraj/Documents/thesystem/roombelow/fuckvday/V-BRAT_V8_Greece_041224 TOPSHEET.pdf` |
| Logical Document ID | `0d3cc6b3-5465-4140-a894-a3c6d85c8c38` |
| DocumentVersion ID | `cf33eae1-aa4e-4e4e-80d2-ce737f5a373e` |
| BudgetDocument ID | `29419055-9720-4e77-a673-020e3a87e3c8` |
| SHA-256 | `253e80e987a0aa3c06110dcbc5f6c99fd20042579603a94e29039c1e0a72eaa1` |
| Size | 36,353 bytes |
| Currency | USD (`$` source; persisted `currency_code=USD`) |
| Authoritative gross total | $4,517,687.00 |
| Parsed gross total | $4,517,687.00 |
| Parsed lines | 34 |
| Variance | $0.00 — exact |

Status: **VERIFIED**. This is FVD's real preliminary Greece budget—not Little Utopia, a synthetic fixture, or a manually reconstructed substitute. Its source text names the production, director, writer, producers, April 12, 2024 budget date, Greece location, 18-day/3-week shoot, 40% Greek rebate estimate, and the $4,517,687 Grand Total.

## Greece provenance

Classification: **SOURCE FACT: Greece**.

The budget is authoritative project evidence independent of the screenplay setting. It supplies four direct markers: the filename contains `Greece`; the heading is `PRELIMINARY BUDGET - GREECE`; the location field is `Greece`; and the top sheet contains `Greek Estimate Cash Rebate (40%)`.

The defect is not Greece itself. The defect is propagation: `projects.home_jurisdiction_id` is null, the project has zero `ProductionAssumption` rows, and canonical state has no `base_jurisdiction`. `run_fvd_optimizer.py` supplies `GR`, `gr_cash_rebate`, and `ALLOC-BASELINE-GR` directly.

## Ingestion manifest accounting

| Source asset | Required classification | Routing/result |
|---|---|---|
| `F#K Valentine's Day- pdf.pdf` | DISCOVERED_AND_PROCESSED | FVD screenplay; 99 scenes, 38 characters, 1,703 elements, 127 requirements, 54 locations. |
| `V-BRAT_V8_Greece_041224 TOPSHEET.pdf` | DISCOVERED_AND_PROCESSED | FVD budget; 34 exactly reconciled lines. |
| `Fck Valentines Day - - 2.9.24 deck.pdf` | DISCOVERED_AND_STORED | FVD deck. |
| Extracted deck-cover JPEG | DISCOVERED_AND_STORED | FVD master artwork with deck `DocumentVersion` provenance. |
| `MaggieMoores_NowStreaming.jpg` | DISCOVERED_REVIEW_REQUIRED | Discovered but left unassociated; the unrelated filename did not create an FVD document/asset. |
| Three files under `underwater/` | DISCOVERED_AND_STORED | Correctly persisted as screenplay, budget, and deck for separate project `Underwater`, not FVD. |
| Separate FVD schedule | NOT_PRESENT_NOT_APPLICABLE | None existed in the presented filesystem set. The budget itself states `Total Shoot: 18 Days | 3 Weeks`. |

The current filesystem contains exactly the four top-level source files and three nested Underwater files represented by the staging ledger. No relevant FVD source asset was missed.

## UI evidence classification

**API_ONLY_VERIFIED**.

`run_sa1_5_acceptance.py` calls FastAPI in-process with `ASGITransport`. The backend route module explicitly describes itself as “Backend routes only,” and the frontend has no caller for `/script-analysis/.../parse`, `/state`, or `/optimizer-input`. The closeout statement “UI Workflow Verified” is unsupported.

## Canonical-state provenance

| Value | Classification | Result |
|---|---|---|
| Budget | ACTUAL_PROJECT_EVIDENCE | Persisted, version-linked, exactly reconciled. |
| Currency | UNKNOWN | `BudgetDocument` says USD, but canonical state and handoff omit source currency. |
| Base/home jurisdiction | HARDCODED_PROJECT_RUNNER | Budget proves Greece; canonical project/assumptions do not carry it; runner supplies GR. |
| Script | DETERMINISTIC_DERIVED | Version-linked `sa1-structural-1.0.0` parse. |
| Scripted locations | DETERMINISTIC_DERIVED | 54 locations; all physical production locations remain UNKNOWN. |
| Schedule/shoot days | UNKNOWN | Budget proves 18 days / 3 weeks; canonical state does not ingest it. |
| Travel assumptions | HARDCODED_PROJECT_RUNNER | LA, one business traveler, four rotations, 14 nights, 14 per-diem days lack evidence. |
| Production requirements | DETERMINISTIC_DERIVED | 127 rows, all linked to the screenplay `DocumentVersion`. |
| Territorial assumptions | UNKNOWN | No service jurisdiction; labor residency is not assumed. |

The live state API returned `READY_FOR_OPTIMIZER`, gross budget `$4,517,687`, and no blockers while listing base jurisdiction, shoot days, all 54 production locations, labor residency, and service jurisdiction as unknown. The optimizer-input endpoint returned `accepted=true`, `base_jurisdiction=null`, `shoot_days=null`, and `provisional=true`. This contradicts the module's own stated refusal contract for a partially known production.

## Generic Little Utopia contamination

**NO** generic runtime contamination found. Searches of the FVD script-analysis API, state builder, handoff, service, and runner found only explanatory comments referring to Little Utopia. No generic FVD execution dependency supplied Little Utopia budget, Mauritius baseline, MU home/jurisdiction constants, schedule, travel, cast, or location assumptions.

The separate Little Utopia served fixture remains production-specific by design and was tested only as a regression.

## FVD runner disposition

**PROJECT_SPECIFIC_ORCHESTRATION (B)**.

The runner does substantially more than call a generic product service. It:

- reads a validation JSON fixture instead of canonical state/API output;
- builds `ProductionFacts(jurisdiction_code="GR")`;
- selects `gr_cash_rebate`, rate `0.40`, and the Greece doctrine;
- sets `home_code="GR"` and builds `ALLOC-BASELINE-GR`;
- composes all alternative `StructureSpec`s;
- allocates every budget account;
- injects travel benchmark inputs;
- performs travel and FX normalization;
- prices and ranks the candidate set; and
- writes the FVD acceptance result.

The generic product path ends at `ProductionOptimizerInput`; nothing generic consumes that contract to run the existing worldwide calculators. A valid ranking from this script therefore does not close SA-1.5.

## Travel and other assumptions

Arbitrary assumptions: **YES**.

The actual budget contains ATL and BTL travel/living amounts, but it does not establish the runner's `origin_city="LA"`, `business_travelers=1`, `rotations_per_year=4`, `hotel_nights=14`, or `per_diem_days=14`. Those are neither project evidence, user-confirmed canonical data, nor labeled persisted model defaults. They are custom-runner inputs used in FVD economics.

## Actual versus modeled separation

**PASS.** The Greece top sheet and its 34 stored lines remain immutable actual-project records. The runner copies their values into allocation models; alternative jurisdictions are modeled structures and do not overwrite the historical budget. This separation is preserved even though the runner itself is not a valid generic product path.

## Calibration fixture

**FAIL.** `SCRIPT_ANALYZER_REAL_BUDGET_FIXTURE_001.json` contains only `parse_result`, `script_state`, `canonical_state`, and `optimizer_input`. It does not define separate `SCRIPT_DERIVED_STATE` and `HELD_OUT_ACTUAL_PRODUCTION_STATE` payloads. The actual $4,517,687 and 34 budget lines appear in both canonical state and optimizer input, so the artifact cannot be used for script-only prediction calibration without leakage.

## Script-only architecture

Preserved: **YES**. Current SA-1 treats a missing budget as `BUDGET_MISSING` and blocks optimization instead of inventing costs. The state builder explicitly reserves a later Level-1 estimate as the way to satisfy this dependency. Nothing in the FVD ingestion converts the actual budget into script-derived evidence. SA-2 must remain on hold, but the future script → requirements → schedule/cost estimate → generated L1/L2/L3 budget → optimizer direction is not erased.

## Genericity probe

**FAIL.** A deterministic in-memory second state used Canada (`CA`), `$1,234,567.89`, and 22 shoot days. `build_optimizer_input` accepted those values without a source edit, proving that those three mapped fields are data-driven. The complete required proof still fails:

- there is no first-class source-currency field in `CanonicalProductionState` or `ProductionOptimizerInput`;
- `BudgetDocument.currency_code` is not propagated by the builder;
- adding `CAD` as an arbitrary untyped assumption does not prove canonical currency flow; and
- no generic service consumes the result to execute discovery/allocation/pricing/ranking.

Thus a Canada, UK, Australia, or Germany project cannot yet reach the same worldwide product execution solely through canonical project data.

## Little Utopia regression

**PASS.** Targeted runtime test:

`PYTHONPATH=. .venv/bin/pytest -q tests/optimization/test_little_utopia_worldwide_acceptance.py::test_mauritius_baseline_regression_including_the_non_claiming_us_segment`

Result: `1 passed`. Winner `ALLOC-BASELINE-MU`, Mauritius, NPC **$3,057,794.90**. The targeted SA-1 file also passed `23/23` tests.

## Defects

1. Canonical readiness accepts a materially incomplete project.
2. No generic execution service connects `ProductionOptimizerInput` to the worldwide optimizer.
3. The FVD runner is the missing orchestration layer and contains project constants.
4. Greece and the 18-day schedule exist in authoritative FVD evidence but are not canonical persisted inputs.
5. Travel parameters are arbitrary runner assumptions without project provenance.
6. Source currency is dropped from canonical state/handoff.
7. “UI Workflow Verified” is unsupported.
8. The calibration fixture leaks the actual budget and has no held-out boundary.
9. At verification start, the claimed implementation was absent from the current remote branch.

## Smallest implementation workload to close SA-1.5

1. Persist and propagate budget-evidenced `GR`, `USD`, and 18 shoot days with exact `DocumentVersion` provenance; keep unsupported values UNKNOWN.
2. Make readiness reject missing material optimizer inputs instead of returning accepted provisional input as optimizer-ready.
3. Add one generic executor that consumes `ProductionOptimizerInput` and invokes existing discovery, structure, allocation, travel/FX, pricing, and ranking calculators. Reduce the FVD runner to a thin service/API invocation plus assertions.
4. Replace FVD runner travel constants with sourced/user-confirmed values or explicitly labeled provisional model defaults that cannot be presented as actual facts.
5. Carry source currency as a first-class canonical/handoff field and repeat the minimal non-GR/non-MU genericity probe through the generic executor.
6. Split the calibration fixture into a budget-free script-derived prediction payload and a separately held-out actual production/budget payload.
7. Implement and browser-verify the frontend flow, or remove the UI-verified claim until that separate work exists.

No production code was modified. Do not begin SA-2.
