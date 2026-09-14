# CINEGLOBE — FINAL WIRING REMEDIATION, SINGLE BOUNDED CLOSEOUT

**PLATFORM:** Claude Code — canonical local repository

**ENGINE:** strongest available Claude coding/reasoning engine

**EFFORT:** High

**MODE:** implementation + targeted verification

## Objective

Repair **all and only** the four remaining items in Codex artifact `docs/validation/CINEGLOBE_FINAL_WIRING_REMAINING_ITEMS_CODEX.csv` at the current target branch. Do not stop after one repair. Do not declare completion while any row or required adverse oracle is incomplete.

Remaining scope:

1. `P0-SEL-ALT-001` — safe distinct conditional selection and complete blocker/participant aggregation.
2. `P0-NL-001` — canonical Netherlands company/award-period cap binding and conservation.
3. `P0-ZA-001` — South Africa post-only QSAPPE line-level basis conservation.
4. `P0-OR-001` — Oregon conditional formula opportunity from the already-verified official sources.

## Controlling state

- Repository: `surajgohill-oss/Frametax`
- Branch: `claude/audit-frametax-features-NZcX5`
- Audited commit: `67fbc30d9e006663ec739256424dace303d16605`
- Codex acceptance report and CSVs: `docs/validation/CINEGLOBE_FINAL_WIRING_*_CODEX.*`
- Preserve all unrelated tracked/untracked work. Never force-push.

Before editing, fetch, record local/remote tips and ancestry, inspect all existing changes, and use an isolated worktree if ownership is unclear. If the remote advanced, inspect and integrate only non-conflicting in-scope work; do not reset or overwrite it.

## Frozen exclusions

Do not:

- Research new jurisdictions or restart global validation.
- Add, remove, or reclassify unrelated programs.
- Change MFNI, reinvestment, frontend/globe/UI, Script Analyzer, ingestion, or unrelated optimizer behavior.
- Change the four real projects' canonical data or facts merely to make tests pass.
- Alter expected values to match defective output.
- Treat catalog presence, candidate construction, descriptive comments, or broad-suite success as consumption/acceptance.
- Create parallel pricing, FX, eligibility, or ranking paths.
- Run the full backend suite.
- Merge the branch or force-push.

## Repair 1 — selection

Replace the unsafe `67fbc30` predicate behavior generically.

Required invariants:

- A baseline anchor is never the distinct-alternative slot.
- `qualification_state=None`, `QUALIFIES`, or `NOT_APPLICABLE` does not, by itself, prove that a **non-comparable** row is a valid conditional. Non-comparability must have an explicit, machine-readable cause.
- A row enters the conditional pool only when every blocker is enumerated and every blocker belongs to an approved curable/unresolved category. Any hard legal, authority veto, identity, retired/superseded, failed requirement, or unknown-unclassified cause excludes it.
- Do not use one jurisdiction boolean as a substitute for travel, local-cost, in-kind, FX, and other candidate-specific inputs. Represent and evaluate each applicable dimension; non-applicable dimensions must be explicit, not silently zero.
- Component, group-stack, and treaty structures aggregate qualification and blocker state for **every program and participant**. One hard-failing member blocks the structure. No absent aggregate state may be emitted as an actionable conditional.
- Stable IDs, not display labels, determine identity/distinctness.
- A fully complete eligible distinct candidate enters the existing executable ranking. A conditional never displaces a verified winner.
- Preserve Bad Hombres and Lips Like Sugar exact winners. Do not force Manitoba or Romania; they must earn their positions from complete current facts.

Independent tests—write the expected outcomes literally, without calling the predicate to build them:

1. Baseline excluded.
2. Explicitly curable comparable candidate admitted.
3. Non-comparable `None` excluded.
4. Non-comparable `QUALIFIES`/`NOT_APPLICABLE` excluded unless a complete explicit curable blocker set exists.
5. Hard legal/authority/identity failure excluded.
6. Multiple missing dimensions produce the exact full blocker set.
7. Component/treaty with one hard-failing participant excluded and all participant blockers retained.
8. Complete eligible distinct candidate ranks normally.
9. Verified winner suppresses conditional presentation.
10. Same label/different ID and same ID/changed label preserve identity semantics.
11. Real LU and FVD never expose `qualification_state=None` as leading conditional.

## Repair 2 — Netherlands

Do not rename booleans or comments and call that identity binding. The cap calculation must consume explicit canonical:

- production-company identity;
- award period/year;
- evidence/provenance state for the aggregate;
- prior awards for that exact program + company + period.

Unknown company, period, or aggregate remains conditional/non-priceable. Absence must not mean affirmative zero. A valid explicit zero is permitted only when bound to that company/period with evidence. Compute the remaining EUR cap first, then convert once using the project-selected FX context. Two projects for the same company/year must jointly remain at or below EUR3,000,000; a different company or year must remain isolated. Reject negative, nonfinite, over-cap, wrong-company, and wrong-period aggregates.

Use canonical project/fact storage and the shared evaluation path; do not add an NL-only side ledger or infer identity from project title. If current schema cannot express the binding, make the smallest canonical model/fact-contract change and migration necessary, then thread it through the existing input/fingerprint path.

Independent tests must use two actual canonical project-input identities, not two local names around identical direct helper calls. Expected cap arithmetic must be literal.

## Repair 3 — South Africa

For the post-production-only tier, derive QSAPPE from, or reconcile it to, the exact canonical allocated line IDs classified as qualifying post/VFX spend. Broad production QPE is not a valid upper-bound oracle. Enforce:

`0 <= claimed/derived QSAPPE <= exact qualifying allocated post/VFX subtotal <= allocated/project spend`.

Reject an untraced scalar, duplicated line IDs, a production-only allocation with no post lines, negative/nonfinite values, and one cent above the traced subtotal. An exact traced subtotal must price at 25%, with the ZAR25m final incentive cap applied after rate calculation and one FX conversion. Preserve the general production branch.

## Repair 4 — Oregon

Do not research. Use only the already-verified sources recorded by Codex:

- ORS 284.368: `https://www.oregonlegislature.gov/bills_laws/ors/ors284.html`
- OAR Chapter 951 Division 2: `https://secure.sos.state.or.us/oard/displayDivisionRules.action?selectedDivision=4217`
- Oregon Film OPIF: `https://oregonfilm.org/article/oregon-production-investment-fund-opif/`

Implement disposition **B: conditional formula opportunity**, never unconditional entitlement:

- 20% Oregon payroll/wages/benefits basis.
- 25% other actual Oregon expenses basis.
- USD1,000,000 actual Oregon-expense minimum.
- USD1,000,000 per individual/company QPE exclusion, separate from final award cap.
- Final project award <= 50% of dated annual OPIF fund; current official page says USD21.2m, so current nominal maximum is literal USD10.6m. Keep the fund amount/date explicit and fail conditional if missing/stale; never treat missing cap as unlimited.
- Regional increase = 10% **of the otherwise allowable amount** (multiply eligible incentive by 1.10), never +10 percentage points.
- Application before production, agency comparison/discretion, contract, allocation, and fund availability remain explicit gates.
- Before actual award/contract/fund facts, show provisional economics only and exclude from verified winner/rank 1.
- Preserve payroll/other bases separately. Preserve Greenlight assistance/stack treatment from the verified official program page; do not invent calculation order beyond evidence.

Tests: literal split-basis arithmetic; below/at USD1m threshold; per-payee exclusion; 50%-fund boundary; multiplicative regional uplift; missing/stale fund; no-award conditional never rank 1; awarded complete case may enter only its authorized state.

## Shared correctness requirements

- Generic shared paths only. No project title/ID exceptions, no Manitoba/Romania special cases, and no display-label matching.
- Include every calculation-driving new field in the canonical fingerprint/cache identity.
- Preserve transaction cleanup and import-order determinism.
- Preserve current FX immutability/finiteness and Texas exact-award behavior.
- Preserve all other 586 manifest identities and the original 12-row denominator.
- Preserve exact controls:
  - Bad Hombres `us_nm_film_credit`: incentive USD596,910.25; NPC USD1,885,112.75.
  - Lips Like Sugar `ca_film_30`: incentive USD3,459,278.90; NPC USD8,524,375.10.
  - LU Mauritius anchor: incentive USD573,059.70; NPC USD3,791,333.30.
  - FVD Greece anchor: incentive USD1,445,659.84; NPC USD3,072,027.16.
- Candidate-count changes must be fully attributed to specific candidate identities and rules. Do not force old counts when a legitimate repair changes them.

## Execution order and hard timeouts

Work continuously through all independent items. A failure in one item does not authorize stopping before independent items are completed.

1. Startup/ownership/lineage: 120 seconds per command.
2. Add independent failing oracles for all four rows before claiming a repair.
3. Implement selection, Netherlands, South Africa, Oregon in that order; after each repair run its focused file within 300 seconds.
4. Run four real projects serially, 300 seconds maximum each.
5. Run one grouped delta suite, 900 seconds maximum. Do not run the full backend suite.
6. Commit/push/remote verification, 120 seconds per operation.

Enforce actual wall-clock termination using the available process controller. On timeout: capture command/elapsed/log/process state; stop only the owned process; roll back its owned DB transaction; mark only that check incomplete; continue the other rows; retry once only after a documented causal correction. No indefinite polls, unchanged repeated commands, or scope expansion.

Minimum grouped suite:

- canonical FX and fingerprint tests;
- final formulaic full-pipeline/B3 tests for NL/TX/ZA/Oregon;
- leading-conditional and canonical-selection consistency tests;
- alias/authority-exhaustion/import-order gates;
- four-project runtime controls;
- every new independent oracle above.

## Acceptance and stop conditions

Do not stop or publish “complete” unless:

- all four remaining rows have production-path repairs;
- all independent expected-value/adversarial tests pass;
- LU/FVD expose no actionable conditional with absent aggregate qualification or incomplete blockers;
- NL proves actual company/year conservation and isolation;
- ZA proves exact post/VFX line conservation;
- Oregon is provisional/conditional until real award gates and uses the correct split bases, caps, and multiplicative uplift;
- all four real anchors are recomputed and attributable;
- focused suite passes with zero failures/timeouts, or any timeout is explicitly `INCOMPLETE` and completion is not claimed;
- diff contains only task-owned code/tests/migration/artifact changes;
- no frozen exclusion changed.

If one row remains blocked after exhausting its bounded implementation path, document the exact blocker and continue all other rows. Final status must remain `IMPLEMENTED_PENDING_CODEX_ACCEPTANCE` or `INCOMPLETE`; never self-authorize merge.

## Closeout, commit, push, remote proof

Create one closeout artifact: `docs/validation/CINEGLOBE_FINAL_WIRING_REMEDIATION_CLOSEOUT_CLAUDE.md`. It must contain a four-row matrix, exact files/functions, independent expected vs observed values, focused test totals/times, four-project values/counts/fingerprints, timeouts, and diff scope.

Commit only task-owned implementation, migrations if strictly necessary, focused tests, and the closeout artifact. Commit message:

`fix: close final wiring acceptance defects`

Push without force to `origin/claude/audit-frametax-features-NZcX5`. Verify local and remote SHA equality and retrieve the closeout artifact from the remote commit. Do not merge.

Return short:

- status
- four rows repaired / remaining
- focused tests
- four-project controls
- files changed
- commit SHA
- branch
- pushed
- remote verified
- ready for independent Codex acceptance: YES/NO

STOP.
