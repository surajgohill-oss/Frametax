# Worldwide Qualification, Cultural Test + Official Co-production Completion — Closeout

**Generated:** 2026-08-19
**Branch:** claude/audit-frametax-features-NZcX5
**Final gate:** partial — see honest scope statement below. NOT `WORLDWIDE_QUALIFICATION_CULTURAL_AND_OFFICIAL_COPRO_CANONICALLY_COMPLETED` in the exhaustive sense the gate name implies.

## Honest scope statement

The requesting instruction asked for near-exhaustive primary-authority completion of qualification/cultural-test doctrine across the current worldwide incentive universe (~150 programs) plus official co-production doctrine across all represented treaty routes (~38), in one pass. That is genuinely a multi-week research effort. This pass performed **real, cited, bounded** research and encoding — not a repeat of the 181-regime audit, not fabricated completions — and is reported exactly as completed, with the remainder disclosed as an unchanged residual rather than silently claimed closed.

## What changed (real, cited, tested)

1. **`hr_cash_rebate`** — fixed a genuine `DATA_EXISTS_BUT_STILL_NOT_CONSUMED` defect (`cultural_test_points` was `None` despite being documented in the record's own note as 34), re-confirmed via 2 additional real sources; disclosed a real, newly-found national cast/crew percentage requirement without misusing the role-gate engine to enforce it incorrectly.
2. **`nz_spg_international`** — confirmed and encoded as spend-only via a real NZFC citation.
3. **`canonical_qualification_result.py`** — added `QUAL_AUTHORITY_UNRESOLVED`, distinct from `RULE_DATA_INCOMPLETE`, available for future passes; not yet emitted by live code (disclosed, not silently claimed wired).
4. **Zero new treaty/co-production doctrine** — explicitly, honestly reported as not researched this pass (`OFFICIAL_COPRODUCTION_DOCTRINE_COMPLETION.md`).

## Runtime proof

LU baseline $3,057,794.90 and FVD baseline $3,072,027.16 both re-verified byte-identical after an `ENGINE_VERSION` bump forced a full recompute with this pass's data changes. Real control cases (mandatory-role satisfied/violated, missing-user-fact, point-bearing-never-mandatory, registry-presence-never-qualification, missing-rule-data-never-hard-fail, new spend-only classification) all proven — see `QUALIFICATION_OPTIMIZER_RUNTIME_ACCEPTANCE.md`.

## Tests

5 new (`test_worldwide_qualification_completion.py`). Full backend suite: 4291 passed, 1 pre-existing unrelated frontend failure, 1 skipped.

## True remaining residual

Unchanged from `COPRO_TRUE_AUTHORITY_RESIDUAL.json` (`5935225`) except the 2 programs above, which move from Class D/partial-C to a more complete C. ~106 of 108 Class-D regimes and all 37 Class-C bilateral/Eurimages entries remain exactly as `5935225` localized them — not reproduced here to avoid a redundant audit artifact.

## Guards preserved

Worldwide economic database not reopened. No new optimizer, no new cultural engine, no new treaty engine. No superseded 0.1.0 path touched. Script Analyzer and Budget Estimator untouched. LU/FVD accepted baselines unchanged.

STOP.
