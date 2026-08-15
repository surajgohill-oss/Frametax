# Real Production Validation Corpus

Date: 2026-08-14
Phase: Script Analyzer SA-1.5
Companion: `REAL_PRODUCTION_VALIDATION_CORPUS.json`
Registry: `frametax2/backend/app/validation/real_production_corpus.py`

CineGlobe's Company Library already holds real productions with real screenplays, real actual budgets, and — for one project — a real shooting schedule and Day Out of Days. This document makes that corpus formal, so SA-2 and the future L1/L2/L3 cost engine have something honest to be measured against.

## What this corpus is, and what it deliberately is not

It is a **registry of references**. Every fixture points at authoritative `DocumentVersion` records that already exist. No source document is duplicated, no actual budget is modified, and no figure is invented to fill a gap.

It is **data, not code paths**. There is no `run_lips_like_sugar_optimizer.py` and no per-project branching anywhere in the registry — a fixture is a record, and the generic pipeline consumes it. A test asserts this directly.

It is **internal infrastructure**. No user-facing "Fixture Registry" UI was added.

## Resolution: five of six

| Project | Project ID | Script | Budget | Schedule | DOOD | Other |
|---|---|:--:|:--:|:--:|:--:|---|
| The Little Utopia | `fa5cade5…` | ✅ | ✅ | ✖ | ✖ | deck, lookbook, artwork |
| F#K Valentine's Day | `6c6f1c13…` | ✅ parsed | ✅ | ✖ | ✖ | deck, artwork |
| Lips Like Sugar | `ab10b319…` | ✅ | ✅ | ✖ | ✖ | — |
| Underwater | `f1292c56…` | ✅ | ✅ | ✖ | ✖ | deck, artwork |
| **The System** | `e1f2444d…` | ✅ | ✅ | ✅ | ✅ | 2 superseded schedule versions |
| Tetrad | — | — | — | — | — | **UNRESOLVED** |

**Tetrad is genuinely absent.** A bounded search across all 52 Company Library projects, all document titles and all `DocumentVersion` filenames returned zero matches. Its externally-declared figures (gross $3,700,593, Sydney, QAPE $3,306,143, 40% rebate $1,322,457) are recorded so the fixture completes the moment its materials are imported — but they are explicitly **not** treated as reconciled, and no data was manufactured.

## Budget reconciliation — oracles read from source, never written in

This was the point of Part C, so it is worth being precise about what "reconciled" means for each project.

| Project | Oracle | Source declares | Parsed leaf sum | Gap | Status |
|---|---:|---:|---:|---:|---|
| F#K Valentine's Day | $4,517,687 | $4,517,687 | $4,517,687 | $0 | **RECONCILED_EXACT** |
| The Little Utopia | $4,364,393 | $4,364,393 | $4,364,395 | +$2 | **RECONCILED_SOURCE_ROUNDING** |
| Underwater | $7,998,944 | $7,998,944 | $7,086,368 | −$912,576 | **DECLARED_TOTAL_LEAF_GAP** |
| Lips Like Sugar | $11,983,654 | $11,983,654 | $9,638,143 | −$2,345,511 | **DECLARED_TOTAL_LEAF_GAP** |
| The System | $4,324,058 | $4,324,058 | $4,079,890 | −$244,168 | **DECLARED_TOTAL_LEAF_GAP** |

In **every** case the document's own declared grand total independently equals the acceptance oracle. Nothing was back-filled.

**Underwater reconciles completely from its own components**, which is the strongest evidence in the corpus:

```
Total Above-The-Line   $2,731,485
Total Below-The-Line   $3,319,416
                       ──────────
                       $6,050,901   ← equals the document's own
                                      "Total Above and Below-The-Line"
+ Total Fringes        $1,025,143
+ contingency            $727,800
+ completion bond        $195,100
                       ──────────
                       $7,998,944   ← exactly the oracle
```

Lips Like Sugar and The System reconcile the same way at the section level (ATL + BTL equals each document's own "Total Above and Below-The-Line", leaving a $515,000 and $342,071 fringe/contingency/bond residual respectively).

### The leaf gap is a named parser limit, not a disagreement

On the three detailed multi-page budgets, flat leaf-line extraction under-covers. The cause is specific: these are top-sheet-plus-detail documents whose PDFs extract column-wise (a label and its amount land on separate lines), and the parser sums a mixed population of top-sheet category rows and detail rows without applying the budget's ATL / BTL / fringes / contingency / bond hierarchy. The fringe, contingency and bond blocks appear as *section totals*, not as account-code rows, so they are simply not picked up.

This belongs to the deferred L1/L2/L3 budget work. It is quantified per fixture rather than smoothed over, and a test asserts `parsed_leaf_sum + gap == oracle` so the number cannot drift silently.

## The System — the deep fixture

The only project carrying **script + schedule + DOOD + actual budget** together, and therefore the future held-out target for `script → production requirements → schedule` prediction.

Confirmed at runtime: the current schedule version is a genuine *"Day Out of Days Report for Cast Members"* dated 06/21 onward; two superseded schedule versions are retained (`THE SYSTEM PROD SCHEDULE .xlsx`, `The System HorC_Schedule.pdf` with its cast list); the budget states 20 shooting days and carries "Jackson", corroborating the Mississippi basis.

Schedule and DOOD are the **same** `DocumentVersion` serving two roles — recorded as such rather than duplicated. No separate finance-plan document exists in the library for this project, so `finance_plan` is `MISSING` and the known Mississippi QPE figure is **not** written into the fixture.

SA-1.5 establishes the linkage only. It does not attempt to reproduce the schedule from the screenplay.

## F#K Valentine's Day — verified, not reopened

`FVD_REAL_PROJECT_FIXTURE = VERIFIED`. Budget reconciles exactly to $4,517,687; the screenplay is linked and structurally parsed (99 scenes, 38 characters); Greece is established by the source budget itself (`V-BRAT_V8_Greece_041224 TOPSHEET.pdf`), not inferred by the optimizer. Greece appearing in a runtime result is therefore supported by source evidence and is not a defect.

## Held-out separation and the leakage guard

Each fixture is split into two halves that cannot be confused:

- **`ScriptSideInputs`** — what a predictor may see. Screenplay-derived facts only.
- **`HeldOutActuals`** — the answers. Gross budget, department totals, fringes, contingency, bond, shoot days, geography, schedule/DOOD references, incentive/QPE.

`holdout_guard.PredictionSession` enforces the ordering mechanically: `reveal_actuals()` raises until `close_prediction()` has been called, and reading any held-out field raises unless that specific field was explicitly declared a producer-supplied input for that evaluation. `assert_no_leakage()` scans a prediction payload for the fixture's *actual values* — recursively, and by value rather than by field name — so a leak survives being renamed or nested.

Little Utopia and Tetrad are **not** holdout-eligible and raise if used for prediction evaluation: Little Utopia is the optimizer regression anchor and its assumptions must not leak into other projects.

## Validation modes

| Fixture | Modes today |
|---|---|
| The Little Utopia | `OPTIMIZER_REGRESSION`, `INGESTION_VALIDATION` |
| F#K Valentine's Day | `INGESTION_VALIDATION`, `SCRIPT_BREAKDOWN_VALIDATION` |
| Lips Like Sugar | `INGESTION_VALIDATION`, `SCRIPT_BREAKDOWN_VALIDATION` |
| Underwater | `INGESTION_VALIDATION`, `SCRIPT_BREAKDOWN_VALIDATION` |
| The System | `INGESTION_VALIDATION`, `SCRIPT_BREAKDOWN_VALIDATION` |
| Tetrad | none — unresolved |

`SCHEDULE_VALIDATION` and `BUDGET_ESTIMATION_VALIDATION` are typed but claimed by **no** fixture, because their engines do not exist yet. A test asserts both sets are empty, so a future phase cannot quietly claim a capability it has not built.
