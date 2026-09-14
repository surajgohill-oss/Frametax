# Global Incentive Final Acceptance — Codex

## Decision

**NOT_ACCEPTED.** Claude commit `2606819ffda9dc978452594dbd6e8c601e5cc0b6` safely descends from controlling audit `031f34bba9827c73c78e9bc2737fc1239dd0a4e0`, and the repository delta is limited to the declared backend rules/tests and Claude validation artifacts. MFNI and globe/frontend are untouched. The strict gate nevertheless fails: only **2/9** final rows close and only **4/12** formulaic programs have a verified full optimizer pipeline.

## Startup and scope

- Branch: `claude/audit-frametax-features-NZcX5`.
- Startup local and remote HEAD: `2606819ffda9dc978452594dbd6e8c601e5cc0b6`.
- Merge-base with the controlling audit: exactly `031f34bba9827c73c78e9bc2737fc1239dd0a4e0`; ancestry passed.
- Startup tracked tree: clean.
- Claude delta: 18 files — four production files, eight tests, six Claude artifacts. No MFNI or frontend/globe path changed.
- No research was reopened and no production code or data was modified by this audit.

## Decisive findings

1. **Oregon is not a no-change completion.** The real `us_or_opif` slug remains vetoed as `UNPRICEABLE_AUTHORITY_INSUFFICIENT`; it returns no rate even with a qualifying component amount and never constructs or compares. Claude's changed test expressly says it is not consumption proof. This directly fails the required real-slug optimizer-consumption gate.
2. **Texas still substitutes the maximum for the award.** The new crew/cast/pool gates are useful, and the `satisfied is not True` correction is sound. But once those gates and `us_tx_miip_award_confirmed` are true, the engine always selects `0.31`. It consumes no awarded rate/tier.
3. **South Africa still has no post-only economic basis.** A new boolean selects a second 25% tier, but both tiers price the same broad allocation. Claude's direct test labels a `component="production"` allocation as the post-only case. QSAPPE, additions and detailed post gates remain absent.
4. **Thailand has an untested endpoint error.** The rule text says 20% for THB100m–150m and 25% above THB150m. Both the 25% tier and 30% ceiling use inclusive `amount_fact_min=150_000_000`; an independent probe measured exactly THB150m at a 25% floor rather than 20%.
5. **FX is reused but not accepted.** The implementation does call the established snapshot table and conversion module, uses the correct local-per-USD directions, converts once and is not frozen at import. It does not accept an explicit project/snapshot context, however. It reads mutable process-global `FX_LIVE_SNAPSHOT_DATE`; missing cap rates raise `ValueError`, zero rates raise `ZeroDivisionError`, negative rates yield negative caps, and freshness state is ignored. Those are mandatory prompt failures.
6. **Malta and Netherlands remain conditional failures.** Malta's certificate makes the 40% tier resolve, but the served ceiling remains confirmation-required because separate unresolved limbs remain; Claude's test merely asserts the result is not below 30%. The Netherlands company-year cap is applied to one candidate without company-period award aggregation and inherits the unsafe FX path.

## Independently reproduced results

- Final nine: **2 PASS / 7 FAIL**. Passing rows: `fr_trip`, `ma_ccm_rebate`.
- Formulaic full pipeline: **4/12 PASS** (`au_location_offset`, `fr_trip`, `is_film_reimbursement_scheme`, `ma_ccm_rebate`).
- Follow-up closure: prior 98 plus two newly accepted rows = **100/107**.
- Canonical program matrix: **586/586**, unchanged from the controlling audit.
- Protected legacy references: **50/50 unreachable**, unchanged and targeted regression tests passed.
- Reachable stale runtime paths: **0** observed by the existing targeted integrity/import tests; this does not cure the seven economic blockers.
- Duplicate IDs / orphan aliases / alias cycles / unintended auto-priced programs: existing targeted gates passed; no delta introduced in identity/alias files.
- Boolean/floorless-ceiling change: **PASS**. True passes; explicit false, missing, malformed and unknown remain non-priceable. Canonical contradictory duplicate facts are prevented by the `(project_id, fact_key)` unique constraint.

## Thailand candidate delta and real projects

The pre/post universes were independently executed from `031f34b...` and `2606819...` against the same four persisted projects. All 14 semantic changes are attributable to `th_film_incentive`: four full-relocation candidates changed `PRICED` to `RULE_REJECTED`, and ten already-rejected Thailand component candidates disappeared because Thailand ceased to be a priceable routing target. No unrelated semantic candidate disappeared.

Current project fingerprints are freshly reconstructed values, not the stale values in Claude's recomputation CSV:

| Project | Current fingerprint | Current total / priced / rejected | Winner |
|---|---|---:|---|
| The Little Utopia | `caf4e638...ffdb9d` | 241 / 124 / 117 | none |
| F#K Valentine's Day | `f25ccb55...5c9fd` | 292 / 159 / 133 | none |
| Bad Hombres | `c3d6760d...dc12bf` | 238 / 122 / 116 | `us_nm_film_credit`; $596,910.25 incentive; $1,885,112.75 NPC |
| Lips Like Sugar | `117669d2...6c98b` | 294 / 175 / 119 | `ca_film_30`; $3,459,278.90 incentive; $8,524,375.10 NPC |

The canonical integrity gate evaluated 14 budget-bearing projects: **14 PASS, 0 FAIL, 36 SKIP**; all four named projects passed.

## Test execution

- Claude focused formulaic tests: **29 passed**.
- All eight modified test files, forward order: **202 passed**.
- All eight modified test files, reverse order: **202 passed**.
- Registry/import/authority negative set: **102 passed**.
- Canonical integrity gate: **PASS** for all 15 non-globe invariant families on 14 evaluated projects.
- Full backend suite: **not completed**. It progressed to approximately 19% and then produced no output for several minutes; it was terminated rather than falsely reported as passing. Claude's claimed 4,863-pass result is therefore not independently accepted here.
- CI: not claimed.

## Gate accounting

- P0 blockers: seven rows/areas listed in `GLOBAL_INCENTIVE_FINAL_REMAINING_ITEMS_CODEX.csv` (FX, MT, NL, TH, OR, TX, ZA).
- P1 blocker: changed test oracles certify current output rather than the required behavior in the five specified cases.
- Global incentive research remains accepted; this audit did not reopen it.
- Global incentive wiring and optimizer runtime for the current incentive scope are **not accepted**.
- It is **not safe** to begin globe consumption audit until the bounded remaining manifest is repaired and independently rerun.

The sibling CSV artifacts contain the row-level reconciliation, 12-program chain, FX cases, boolean cases, exact candidate delta, four-project runtime and bounded remaining manifest.
