# Script Analyzer SA-1.5 — Corpus Closeout

Date: 2026-08-14
Branch: `claude/audit-frametax-features-NZcX5`
Companions: `SA1_5_CORPUS_CLOSEOUT.json`, `REAL_PRODUCTION_VALIDATION_CORPUS.{json,md}`

## What this phase finished

SA-1 built the generic structural screenplay pipeline. F#K Valentine's Day then exercised it against a real project. SA-1.5 closes the loop by making the *set* of real productions a first-class, reusable thing — a validation corpus with a held-out harness — so SA-2 has something honest to be measured against before it starts predicting anything.

## A branch divergence, resolved first

The branch had diverged: 4 local commits ahead, 1 on origin. Local and remote had each committed a **byte-identical** `CODEX_SA1_5_INDEPENDENT_VERIFICATION` artifact from concurrent sessions, but origin was missing the three SA-1.5 implementation commits (`fe59612`, `174cd82`, `9d2fa9d`).

Both sides' file contents were confirmed identical by sha256 before acting, then merged — no force-push, nothing discarded. Worth flagging: had this been resolved by force-pushing either side, real implementation work would have been lost.

## Five of six projects resolved

| Project | Script | Budget | Schedule | DOOD | Other |
|---|:--:|:--:|:--:|:--:|---|
| The Little Utopia | ✅ | ✅ | ✖ | ✖ | deck, lookbook, artwork |
| F#K Valentine's Day | ✅ parsed | ✅ | ✖ | ✖ | deck, artwork |
| Lips Like Sugar | ✅ | ✅ | ✖ | ✖ | — |
| Underwater | ✅ | ✅ | ✖ | ✖ | deck, artwork |
| **The System** | ✅ | ✅ | ✅ | ✅ | 2 superseded schedules |
| Tetrad | — | — | — | — | **UNRESOLVED** |

**Tetrad is genuinely not in the Company Library.** A bounded search across all 52 projects, all document titles and all `DocumentVersion` filenames found nothing. Rather than quietly dropping it or inventing a record, it is registered `UNRESOLVED` with its externally-declared figures held as *expectations only* — explicitly not reconciled — so it completes the moment its materials are imported.

## Budget reconciliation — the part that mattered most

The instruction was blunt: the oracles are acceptance values, not something to write into parser output. So every oracle here was **read out of the source document's own declared grand total** and then cross-checked against that document's own section hierarchy.

All five resolved projects pass that test: the document independently declares the oracle in every case.

The interesting finding is what happens *below* the grand total. On the three detailed multi-page budgets, flat leaf-line extraction under-covers:

| Project | Oracle | Source declares | Leaf sum | Gap |
|---|---:|---:|---:|---:|
| F#K Valentine's Day | $4,517,687 | $4,517,687 | $4,517,687 | $0 |
| The Little Utopia | $4,364,393 | $4,364,393 | $4,364,395 | +$2 |
| The System | $4,324,058 | $4,324,058 | $4,079,890 | −$244,168 |
| Underwater | $7,998,944 | $7,998,944 | $7,086,368 | −$912,576 |
| Lips Like Sugar | $11,983,654 | $11,983,654 | $9,638,143 | −$2,345,511 |

**Underwater reconciles completely from its own components** — the strongest evidence in the corpus that the oracle is real and not asserted:

```
ATL $2,731,485 + BTL $3,319,416 = $6,050,901
        ↑ equals the document's own "Total Above and Below-The-Line"
+ fringes $1,025,143 + contingency $727,800 + bond $195,100
                                = $7,998,944  ← exactly the oracle
```

Lips Like Sugar and The System reconcile identically at the section level, leaving $515,000 and $342,071 of contingency/bond/fringes respectively.

**Root cause of the leaf gap (VERIFIED):** these are top-sheet-plus-detail PDFs that extract column-wise — a label and its amount land on separate lines. The parser sums a mixed population of top-sheet category rows and detail rows without applying the ATL/BTL/fringes/contingency/bond hierarchy, and the fringe/contingency/bond blocks appear as *section totals* rather than account-code rows, so they are never picked up.

That is deferred L1/L2/L3 work. It is quantified per fixture and guarded by a test asserting `leaf_sum + gap == oracle`, so it cannot drift silently — and Little Utopia's $2 remains what it always was: a disclosed source-document rounding artefact, not a parser defect.

## The System — the deep fixture

The only project carrying script + schedule + DOOD + actual budget together, and therefore the eventual held-out target for `script → requirements → schedule`.

Confirmed at runtime: the current schedule version is a genuine *"Day Out of Days Report for Cast Members"*; two superseded schedule versions are retained; the budget states 20 shooting days and contains "Jackson", corroborating Mississippi.

Two details recorded precisely rather than conveniently: schedule and DOOD are the **same** `DocumentVersion` serving two roles (referenced twice, not duplicated), and there is **no** separate finance-plan document — so the known Mississippi QPE figure was *not* written into the fixture.

SA-1.5 establishes the linkage only. No attempt was made to reproduce the schedule from the screenplay.

## Held-out separation and the leakage guard

Every fixture splits into `ScriptSideInputs` (screenplay-derived, predictor-visible) and `HeldOutActuals` (the answers). `PredictionSession` makes the ordering mechanical rather than conventional: `reveal_actuals()` raises until a prediction is recorded, and any held-out field raises on read unless explicitly declared a producer-supplied input for that evaluation.

`assert_no_leakage()` scans payloads recursively **by value**, so a leaked actual survives being renamed or nested — checking field names would have been trivially defeatable.

Little Utopia and Tetrad are not holdout-eligible and raise if used for prediction evaluation. Little Utopia stays the optimizer regression anchor precisely so its assumptions cannot leak into other projects.

## Verification

- **Little Utopia regression**: winner Mauritius, NPC **$3,057,794.90** — unchanged. No global validation rerun.
- **Tests**: 26 new focused tests; full backend suite **4080 passed, 1 skipped, 1 pre-existing unrelated failure**.
- **No SA-2 leaked in**: no AI interpretation, no L1/L2/L3 generation, no learned coefficients, no schedule prediction.
- **Generic execution**: a test greps the registry module to assert no per-project runner functions exist. Two diagnostic scripts from a prior session (`run_fvd_optimizer.py`, `run_sa1_5_acceptance.py`) remain on disk but nothing in the corpus or guard depends on them — they are not part of this architecture.

## Remaining blockers

- **P2** — Tetrad awaits import.
- **P2** — leaf-line budget extraction under-covers on detailed budgets (quantified; declared totals reconcile exactly, so no fixture is blocked).
- **P3** — Lips Like Sugar, Underwater and The System screenplays are linked but not yet structurally parsed; that is an SA-2 activity.

None blocks SA-2.

## Gate

**`GO_FOR_SCRIPT_ANALYZER_SA2`**
