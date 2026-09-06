# CineGlobe Optimizer Final Acceptance — Codex

**Audit date:** 2026-09-06  
**Repository:** `surajgohill-oss/Frametax`  
**Branch:** `claude/audit-frametax-features-NZcX5`  
**Audited application commit:** `e7574050daa8d76c01d2302abaa8d7b3bd22b039`  
**Mode:** independent read-only runtime, persistence, gate, and test audit

## 1. Executive verdict

**OPTIMIZER CURRENT CORE — NOT ACCEPTED**

The implemented runtime core is economically coherent on the current 14-project ready corpus, and P0-SEL-001, P0-PART-001, P1-FRESH-001, P1-REJ-001, and P1-CONF-001 reproduce correctly. The full backend suite also exactly reproduces Claude's reported result.

Acceptance is nevertheless blocked by one open P1, **P1-GATE-001**. The canonical gate does not independently protect all eight acceptance classes required by this audit. It has no generation/fingerprint-freshness invariant, no rejection-accounting invariant, does not independently recompute treaty participant QPE, and does not actually invoke its nested conditional-program conformance check for treaty opportunity rows because that call is below the top-level `is_fully_priced` early-continue. It also omits rejected component rows from the participant invariant for the same reason. The current data happens to be correct; the permanent gate is not yet capable of detecting several regressions in that data.

Open P0: **0**. Open P1: **1** (`P1-GATE-001`).

## 2. Repository/history gate

The repository, remote, and branch are correct. The shared branch advanced during this audit from `f06367c690b5b3c38bb00a276960cf648701f3e6` to `e7574050daa8d76c01d2302abaa8d7b3bd22b039` through concurrent AG validation-ledger commits. The final audit was rebound to the later tip.

| Commit | Result |
|---|---|
| `aa8229eb9ec056f8c64a075da0ef335e9e798b68` | Ancestor of audited HEAD |
| `9874ff8` | Ancestor of audited HEAD |
| `25e1c4d` | Ancestor of audited HEAD |
| `7e5ed4bc8f209a75fb7e6776dc98a4f80b3f588e` | Object retrievable; not ancestral (orphaned audit artifact) |

The optimizer backend, gate, tests, and frontend are byte-unchanged from `25e1c4d` through the audited tip. The intervening commits only update AG validation artifacts. No destructive history loss or overwritten optimizer implementation was found.

## 3. Current corpus

Dynamic discovery returned **50 project rows: 14 optimizer-ready and 36 non-ready**. Non-ready status was 35 `BUDGET_REQUIRED_FOR_CURRENT_EVALUATION` and one `BLOCKED_INCOMPLETE_INPUTS`.

Ready projects:

1. 10 Double Zero
2. 5 LBS OF PRESSURE
3. Bad Hombres
4. Baron Samedi
5. F#K Valentine's Day
6. Going Places
7. Interference
8. Lips Like Sugar
9. Rocky Mountain
10. The Cure
11. The Little Utopia
12. The System
13. Twilight of the Dead
14. Underwater

The ready count remains 14; there is no corpus delta to explain.

## 4. P0 selection acceptance

Every ready project was evaluated, then compared across evaluator `top_result`, persisted `Project.leading_structure_id`, and served `canonical_selected_structure_id`.

| Metric | Result |
|---|---:|
| Selection divergences | 0 |
| Non-comparable persisted leaders | 0 |
| Server-invented winners | 0 |
| Persistence-invented winners | 0 |

Three projects currently have a comparable selected winner (5 LBS OF PRESSURE, Bad Hombres, and Lips Like Sugar). The remaining 11 consistently return no winner across all three layers. **P0-SEL-001: CLOSED.**

## 5. P0 participant acceptance

The live corpus now contains **3,474 component attempts**, correctly split into **2,585 priced** and **889 `RULE_REJECTED`** rows. Expected participants were independently derived only from segments with `claims_incentive == True`.

| Metric | Result |
|---|---:|
| Participant mismatches | 0 / 3,474 |
| Extra non-claiming participants | 0 |
| Missing claiming participants | 0 |
| Duplicate participants | 0 |

Rejected attempts correctly carry no claiming economic participants and are not treated as priced candidates. **P0-PART-001: CLOSED at runtime.** Gate coverage of rejected rows remains part of the P1-GATE-001 blocker in Section 9.

## 6. P1 freshness acceptance

The audit reconstructed the current input fingerprint independently for all 14 ready projects and compared it with evaluator state, every served current-engine result, both canonical view builders, and package/structure budget identity.

| Metric | Result |
|---|---:|
| Cross-generation divergences | 0 |
| Stale current-engine rows served | 0 |
| Package/structure generation divergences | 0 |
| Wrong engine versions among served rows | 0 |

F#K Valentine's Day currently has five distinct `canonical-1.54.0` fingerprints and Lips Like Sugar has two. On those two projects, the old newest-created-row helper differs from the reconstructed current fingerprint, while both canonical views and every served row use the reconstructed fingerprint. This directly reproduces the historical reverted-facts condition and verifies that `current_generation_fingerprint()` prevents the stale cross-view read. **P1-FRESH-001: CLOSED at runtime/persistence.**

## 7. P1 rejection acceptance

The audit independently rebuilt movable-component spend, current target/program candidates, and pricing results for every ready project. It compared semantic `(project, component, target, program)` identities with the served current-generation ledger.

| Metric | Result |
|---|---:|
| Expected component attempts | 3,474 |
| Persisted component attempts | 3,474 |
| Expected rejections | 889 |
| Persisted rejections | 889 |
| Missing rejections | 0 |
| Unexpected rejections | 0 |
| Duplicate rejection identities | 0 |
| Rejected as priced | 0 |
| Rejected as comparable | 0 |
| Rejected as rankable | 0 |
| Missing rejection identity/reason fields | 0 |

Each rejection is linked through `ProductionStructure.project_id`, has a stable structure ID, current engine/fingerprint, target program, component allocation, `candidate_status=RULE_REJECTED`, `rejection_reason_class`, and detailed `reason`. A second evaluator pass returned `EVALUATION_REUSED` on every ready project and left all per-project rejection counts unchanged. **P1-REJ-001: CLOSED at runtime/persistence.**

## 8. P1 conformance acceptance

`au_producer_offset` has one optimizer-visible canonical slug, two rate rules, no ordinary doctrine, no ordinary requirements profile, and reverse-resolves to jurisdiction `AU` through the confirmed separate pathway registry. Its current classification is exactly **`PATHWAY_SPECIFIC`**. It is not exposed as ordinary discovery, remains valid in conditional treaty pricing (55 current priced-component occurrences), and creates no conformance/execution contradiction. **P1-CONF-001: CLOSED at runtime.**

## 9. P1 gate-depth acceptance

**P1-GATE-001 remains OPEN.** The live canonical gate passes, but it does not independently protect all required classes.

| Required protection | Current state | Acceptance |
|---|---|---|
| A. Selection consistency | Integrated evaluator/persisted/served comparison | PASS |
| B. Participant exactness | Correct helper, but called only after top-level `is_fully_priced`; 889 rejected component rows are skipped | PARTIAL |
| C. Participant duplicate detection | Correct helper and synthetic negative test for priced rows; rejected rows skipped | PARTIAL |
| D. Treaty allocation conservation | Integrated before the early-continue; malformed 200% allocation fails | PASS |
| E. Independent participant-QPE recomputation | Not implemented. The gate computes only `allocated gross × modeled rate` as an incentive upper bound | FAIL |
| F. Onboarding/pathway semantics | Helper is correct in isolation, but nested conditional check is unreachable for treaty opportunity rows because invocation is after the top-level `is_fully_priced` continue | FAIL |
| G. Generation/fingerprint freshness | No gate invariant and no malformed negative oracle | FAIL |
| H. Rejection accounting/observability | No gate invariant and no malformed negative oracle | FAIL |

The decisive code evidence is in `frametax2/backend/scripts/canonical_integrity_gate.py`: `_TESTED_INVARIANTS` declares 13 families without freshness or rejection accounting; treaty checking at lines 248–257 uses allocated gross and modeled rate without rebuilding participant inputs or QPE; and the `if not s["is_fully_priced"]: continue` at lines 446–447 precedes participant and program-onboarding invocation at lines 514 and 538–540.

The treaty-QPE gap was also reproduced directly. A deliberately malformed treaty participant with `qpe_usd=100,000` and `selected_incentive_usd=900,000` passed `_check_treaty_allocation_invariant` with an empty failure list because the selected incentive stayed below the much looser full allocated-share × rate ceiling. This is not independent QPE recomputation.

The negative-test file contains **12 tests: eight malformed cases expected to fail and four valid/regression-control cases expected to pass**. Malformed classes exercised are participant duplicate/extra/missing, treaty allocation non-conservation, gross-share-rate incentive overflow, feasible-but-unpriced allocation, and top-level/nested nonconformant program use. There is no malformed selection test, no low-QPE/corresponding-incentive treaty test, no integration test proving the nested conditional helper is reached by `_gate_one_project`, no stale-generation gate test, and no missing/duplicate/rankable rejection-ledger gate test.

Passing positive runtime regressions for freshness and rejection persistence is useful but is not a substitute for the explicitly required independent canonical-gate protections. Because gate depth is itself a named P1 acceptance item, these are real P1 blockers, not P2 test polish.

## 10. Treaty regression

| Metric | Result |
|---|---:|
| Treaty rows | 325 |
| Deterministically solvable/eligible | 282 |
| Fully priced conditional scenarios | 123 |
| Non-conserving allocations | 0 |
| Double-counted QPE | 0 |
| Unexplained incentive recomputation mismatches | 0 |

For every feasible priced component, the audit independently scaled canonical project budget lines by participant allocation, reran the pricing kernel, rebuilt qualifying spend from the qualification register, recomputed participant incentive, and reconciled stacking adjustments to the conditional total. Current treaty runtime economics match the accepted baseline.

## 11. Program consumption

The current optimizer-visible universe is **125 programs**, classified as 65 `CONFORMANT`, 59 `CONDITIONAL`, one `PATHWAY_SPECIFIC`, and zero `NONCONFORMANT`.

Each visible slug was assigned exactly one current outcome:

| Outcome | Programs |
|---|---:|
| Executed/priced | 107 |
| Candidate but not priced with reason | 13 |
| Valid nonformulaic | 2 |
| Blocked authority/rule | 2 |
| Pathway-specific | 1 |
| Silently omitted | 0 |

`SILENT_EXECUTABLE_PROGRAM_OMISSIONS = 0` and `CONFORMANCE_EXECUTION_CONTRADICTIONS = 0`. Presence alone was not treated as consumption; outcomes were derived from current structures, nested conditional components, disclosed reasons, authority dispositions, and conformance state.

## 12. Engine/fingerprint persistence

`ENGINE_VERSION` is **`canonical-1.54.0`**. The version bump correctly invalidated the pre-rejection-ledger row shape. Every served row on every ready project uses 1.54.0 and the reconstructed current fingerprint. The second pass reused the current generation without appending rejection rows. No 1.53 row masked or contaminated a 1.54 served result.

## 13. Canonical gates

| Gate | Result |
|---|---|
| Canonical Budget Integrity Gate | PASS — 4/4 locked budgets; all 16 invariant families |
| Non-Globe Canonical Integrity Gate | PASS on live data — 14 PASS, 0 FAIL, 36 SKIP; all 13 declared families |

The non-Globe gate's live PASS does not close P1-GATE-001 because the gate's declared/tested family set and integration path omit required acceptance protections described in Section 9. Globe remained explicitly out of scope and was not counted as passed.

## 14. Focused tests

Command:

`PYTHONPATH=. .venv/bin/pytest -q tests/test_canonical_generation_freshness.py tests/test_component_rejection_persistence.py tests/test_program_onboarding_conformance.py tests/test_canonical_integrity_gate_negative.py tests/test_canonical_selection_consistency.py tests/test_canonical_scenario_participants.py tests/test_copro_conditional_pricing_bridge.py`

Result: **55 passed, 2 skipped, 0 failed** in 576.20 seconds.

## 15. Full backend suite

Command: `PYTHONPATH=. .venv/bin/pytest -q`

Result: **4,774 passed, 3 skipped, 0 failed, 12 warnings** in 287.05 seconds. This exactly reproduces Claude's count. No frontend source or shared frontend contract changed after the audited implementation, so a frontend suite was not required by the task.

## 16. Claude claim reconciliation

| Claude claim | Independent result | Classification |
|---|---|---|
| Zero served fingerprint divergence | 0 across all 14; FVD/LLS exercise real multi-generation state | VERIFIED |
| 889 current-generation rejections | Independently derived and persisted count both 889 | VERIFIED |
| Zero rejection duplicates | 0 semantic duplicates; rerun idempotent | VERIFIED |
| Zero rejected-as-priced | 0 priced, comparable, or rankable | VERIFIED |
| `au_producer_offset` pathway-specific | One AU identity; two rules; valid nested pathway | VERIFIED |
| Zero conformance/execution contradictions | 0 across 125 programs | VERIFIED |
| Zero selection divergence | 0 across 14 | VERIFIED |
| Zero participant mismatch | 0 across 3,474 component attempts | VERIFIED |
| Treaty 325 / 282 / 123 and conserved | Counts reproduced; independent QPE/incentive reconciliation has 0 mismatch | VERIFIED |
| 125 optimizer-visible programs | 125; no silent omission | VERIFIED |
| Canonical gates pass live data | Budget and non-Globe gates pass live data | VERIFIED |
| Gate materially protects all P1 recurrence classes | Missing E/G/H; F is not integrated for treaty rows; rejected participants are skipped | CONTRADICTED |
| Full backend 4,774 passed / 3 skipped | Exact reproduction | VERIFIED |
| Engine 1.54.0 safely serves current shape | Version/fingerprint/reuse checks pass | VERIFIED |

## 17. Remaining findings by severity

| Finding | Severity | Status |
|---|---|---|
| P0-SEL-001 runtime/persistence | NOT_A_DEFECT | Closed |
| P0-PART-001 runtime/persistence | NOT_A_DEFECT | Closed |
| P1-FRESH-001 runtime/persistence | NOT_A_DEFECT | Closed |
| P1-REJ-001 runtime/persistence | NOT_A_DEFECT | Closed |
| P1-CONF-001 runtime/pathway behavior | NOT_A_DEFECT | Closed |
| P1-GATE-001 incomplete gate and negative-oracle coverage | **P1** | **Open; acceptance blocker** |
| Globe, MFNI, SA-2, and future structure families | FUTURE_SCOPE | Not audited and not blockers here |

Bounded remediation for `P1-GATE-001`:

1. Move/call participant and onboarding checks before the top-level priced-row continue, with semantics appropriate to `RULE_REJECTED` rows and nested conditional scenarios.
2. Add a pure treaty oracle that reconstructs each participant's allocated canonical inputs and qualification register, independently recomputes QPE and incentive, and reconciles the conditional combined/stacked total. Add a malformed low-QPE-but-under-gross-rate-bound test.
3. Add a dynamic all-ready-project freshness invariant comparing reconstructed current generation with evaluator, persisted current-engine rows, package view, structure view, and served rows. Add a synthetic or injected stale-current-engine negative case.
4. Add a dynamic rejection-ledger invariant that independently derives expected `(project, component, target, program)` attempts/rejections for the current generation and checks exact persistence, reason identity, non-priceability, non-comparability, non-rankability, duplicates, and rerun idempotency. Add missing, duplicate, and improperly priced/ranked negative cases.
5. Add an integration negative test through `_gate_one_project` proving a nonconformant program nested in a top-level-unpriced treaty opportunity is caught; add an equivalent rejected-component participant corruption case.

No economics, optimizer, program, authority, MFNI, Globe, or SA-2 implementation change is required by this audit finding; the repair is bounded to the canonical gate and its regression tests.

## 18. Final current-core acceptance decision

The current runtime and persistence output is correct on the entire ready corpus, but the named final gate-depth P1 is not closed. Under the task's mandatory criterion `OPEN P0 = 0` and `OPEN P1 = 0`, the current implemented optimizer core cannot be certified 100% accepted.

**OPTIMIZER CURRENT CORE — NOT ACCEPTED**

