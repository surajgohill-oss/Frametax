# Global Program Final Runtime Reverification — Codex

**Workstream:** `CODEX_FINAL_CANONICAL_INCENTIVE_RUNTIME_REVERIFICATION`

**Claude commit:** `95015bbfcdf5460ebfe9a46316540f34bc29085b`

**Base:** `71d72b4066db96c16bbb71c81e3703e628735086`

**Decision:** `NOT_ACCEPTED`

**MFNI:** `PARKED_UNCHANGED`

## Decision

Claude correctly repaired the transitive B4 refusal boundary and the circular import. The four protected productions retain their accepted winner/no-winner outcomes, the integrity gate passes, all 50 protected raw rule keys remain unreachable, and the test suite is green. Final incentive wiring is nevertheless not accepted: only 3 of the 12 controlling formulaic rule rows conform, and only Australia and Iceland have independently reproduced end-to-end economic consumption.

Nine P0 program rows remain incomplete: Czechia, France, Morocco, Malta, Netherlands, Thailand, Oregon, Texas, and South Africa. The defects are bounded to the new formulaic fact/cap implementation; no research, MFNI, frontend, or unrelated optimizer work is implicated.

## Startup and delta

- Repository: `surajgohill-oss/Frametax`; branch `claude/audit-frametax-features-NZcX5`.
- Local and remote started at `95015bbfcdf5460ebfe9a46316540f34bc29085b`.
- Claude commit descends from the named base.
- Delta: 8 production files, 12 test files, 8 Claude validation artifacts, no MFNI paths.
- Tracked tree was clean; pre-existing untracked files were not consumed.

## Formulaic result

The complete record-level result is in `GLOBAL_PROGRAM_FORMULAIC_FULL_PIPELINE_ACCEPTANCE_CODEX.csv`.

- Rule conformance: **3/12** — Dubai/Abu Dhabi identity separation, Australia, Iceland.
- Strict full-pipeline economic consumption: **2/12** — Australia and Iceland.
- Australia independent runtime boundary: missing and AUD 19,999,999 reject; AUD 20,000,000 and 20,000,001 price. FVD relocation QPE is USD 3,701,238.00; 30% produces USD 1,110,371.40.
- Iceland independent runtime conjunction: missing or two of three enhanced facts stays at 25%, USD 925,309.50; all three selects 35%, USD 1,295,433.30.
- Dubai remains rejected under its own superseded identity and cannot inherit Abu Dhabi. Abu Dhabi remains a separate accepted fail-closed identity, so there is no complete automatic economic chain to count.

The principal implementation pattern causing false completion is use of caller-attested result facts in place of calculation: Czechia and South Africa ask the caller to provide the incentive value and then reject values over the cap. A cap must be applied to the engine-calculated incentive. France and Malta still use hard-coded USD conversions where the manifest requires native-currency evaluation. Morocco's numeric day boundary is replaced by a boolean whose name says “18 days”; Thailand omits preapproval/local-spend gates; Netherlands omits caps; Texas maps two booleans directly to the maximum tier; Oregon is tested by copying its rules to a synthetic unblocked slug while the real program remains B4-blocked.

## Alias and import safety

- Transitive alias/fail-closed gate: **PASS**.
- Live alias map: 11 compatibility aliases, 0 cycles, 0 orphan targets.
- Protected raw rule keys: 50/50 resolve to `None` and fail stack insertion.
- Direct, one-hop, two-hop, three-hop, raw legacy key, blocked-intermediate, mixed chain, cycle, and dangling-target attacks all fail closed.
- Fresh-process import order: **PASS**. Evaluation-first, allocation-first, conditional-first, rate-first, production-view-first, registry-first, reverse orders, and three repeated clean processes all produced 126 rule keys and 119 doctrine records.

## Test-oracle reconciliation

Claude changed 18 existing test functions. Seventeen belong to the three reported groups (8 B3 + 5 AU/TH/MT + 4 FVD); the eighteenth is the B4 strict-xfail removal.

Reproduction used the base tests against only Claude's production delta:

- 15 of the 17 grouped tests failed.
- Two B3 tests—AE identity and Texas zero-guarantee—already passed and were proactively strengthened.
- The B4 test became `XPASS(strict)`, which pytest reports as a failure.
- Therefore the exact pytest result is **16 failed**, reconciling the apparent 17-item group sum without inventing overlap.

Count changes were reproduced, but seven replacement formulaic oracles bless incomplete behavior and are blockers; see `GLOBAL_PROGRAM_TEST_ORACLE_AUDIT_CODEX.csv`. No test was deleted or skipped.

## Four-project runtime

All four actual persisted projects pass the 15-family canonical integrity gate. Candidate shrink is attributable to newly enforced fact gates and the dependent component/treaty target pool; protected economics do not move.

- Little Utopia: 243 total / 125 priced / 118 rejected; no winner remains the authority-unresolved qualification gate.
- F#K Valentine's Day: 295 / 160 / 135; no winner remains the user-fact cultural gate.
- Bad Hombres: 240 / 123 / 117; `us_nm_film_credit`; USD 596,910.25 incentive; USD 1,885,112.75 NPC.
- Lips Like Sugar: 297 / 176 / 121; `ca_film_30`; USD 3,459,278.90 incentive; USD 8,524,375.10 NPC.

## Reconciliation and regression

- Canonical matrix remains 586 rows / 586 unique IDs / 0 duplicates.
- Verified follow-up closure is **98/107**: the previously accepted 95, plus Australia, Iceland, and B4. Nine formulaic rows remain.
- Reachable stale runtime paths: 0.
- Unintended automatically priced protected programs: 0.
- Existing aliases: 0 cycles / 0 orphans.
- Modified tests: 236 passed in normal order and 236 passed reversed.
- Canonical integrity gate: 14 projects pass, including all four protected projects; 36 projects correctly skip for missing budgets.
- Full backend suite: **4,859 passed / 3 skipped / 0 failed** in a fresh process (961.60 seconds). The skips are existing declared skips, not remediation suppressions.

## Smallest bounded remediation

Implement only the nine rows in `GLOBAL_PROGRAM_FINAL_RUNTIME_REMAINING_ITEMS_CODEX.csv`, strengthen their full-pipeline tests to assert exact native boundaries, calculated caps, component bases, expected/actual dollars, candidate serialization, and optimizer consideration, then rerun this delta-only gate. Do not restart research, change MFNI, or broaden optimizer architecture.
