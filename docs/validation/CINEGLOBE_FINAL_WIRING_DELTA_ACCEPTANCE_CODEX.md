# CineGlobe Final Wiring and New-Program Delta Acceptance — Codex

**Status:** `NOT_ACCEPTED`

**Target audited:** `67fbc30d9e006663ec739256424dace303d16605`

**Branch:** `claude/audit-frametax-features-NZcX5`

**Audit date:** 2026-09-14

**Scope:** delta-only, read-only production/code/data audit. No production, canonical-data, optimizer, UI, MFNI, or reinvestment changes.

## Executive result

The branch is not merge-safe. The FX and Texas repairs pass independent adverse verification, the four real-project anchor economics remain stable, and the 586-program canonical manifest is unchanged. Four bounded items remain:

1. `P0-SEL-ALT-001`: commit `67fbc30` broadly admits any fully priced non-baseline non-comparable candidate when qualification is absent or otherwise recommendation-admitting. It does not prove that evidenced relocation completeness is the only blocker, does not retain all component/treaty participant gates, and does not enumerate actual missing relocation dimensions.
2. `P0-NL-001`: the Netherlands shared company/year cap is still controlled by two booleans and a scalar with no canonical company ID or award-period binding.
3. `P0-ZA-001`: South Africa post-only QSAPPE is bounded by broad QPE, not reconciled to classified allocated post/VFX spend.
4. `P0-OR-001`: current official sources now support a conditional formula opportunity, but the canonical program remains entirely vetoed as authority-insufficient.

The independently accepted original-12 result is therefore **8 executable/runtime-consumed + 1 valid identity-control disposition + 3 still defective**. No denominator was removed.

## Startup and lineage gate

- Canonical remote: `https://github.com/surajgohill-oss/Frametax.git`.
- Remote target tip and detached audit HEAD were both exactly `67fbc30d9e006663ec739256424dace303d16605` at audit start.
- The tip descends all controlling commits: rejected implementation `4ea0fd832ec52d0ae3e152a404395efa3cbfffc9`, prior Codex audit `a8a1d43dfb1f6e5d69d8b4144023515357f42242`, and process contract `e507f7f0677aeec427bafa437fee318ca22ec6cd`.
- Exact commits after the process contract: `ee63cace` (bounded repairs), `923cf122` (evidenced relocation gate), and `67fbc30d` (conditional-pool intervention).
- The shared Claude worktree contained pre-existing modified test files and five untracked print/probe scripts. Ownership was unknown, so none was modified, deleted, staged, or committed. Audit work ran from an isolated detached worktree.
- Runtime target: local PostgreSQL database `frametax2` on `localhost:5432`, using the target branch's async SQLAlchemy/psycopg backend and canonical persisted project records. API/browser/UI were not run.

## Canonical identity and version gate

- `CANONICAL_PROGRAM_IMPLEMENTATION_MANIFEST_FINAL_CODEX.csv`: 587 lines, exactly 586 program rows plus header.
- Manifest SHA-256 at prior audit `a8a1d43` and current target `67fbc30`: identical, `c2f7bcdf6a7e353f1ae26a16d2d265ed8d3c8c1d048c2a98ec8c08059113f830`.
- No identity registry, worldwide rate table, executable-jurisdiction registry, authority-coverage registry, requirements registry, spend registry, or stacking registry changed after the last independent audit. **New canonical program identities: 0.**
- Directly economically changed program paths after `a8a1d43`: `nl_film_production_incentive`, `us_tx_miip`, and `za_nfvf_rebate`. Shared FX/fingerprint changes also required dependency rechecks for native-currency caps/thresholds; shared selection changes affected presentation/selection but did not add program identities.
- Engine/data versions: canonical evaluation `canonical-1.54.0`; executable registry `1.2.0`; rate rules `1.4.0`; requirements `1.0.0`; spend rules `1.0.0`; provenance `1.0.0`; authority coverage `1.5.0`; stacking `1.0.0`.
- Dated FX identity used by all four recomputations: 2026-07-13, freshness `never_refreshed`; MUR 47.053589, EUR 0.87679, GBP 0.74699, CAD 1.4135, CZK 21.238, ZAR 16.3636; source recorded in runtime as ECB reference rates via frankfurter.dev / open.er-api.com.

## Batch A — Claude engineering delta

### FX — PASS

`CanonicalFXContext` defensively copies the supplied rates and wraps them in `MappingProxyType`; item mutation/deletion and mutation through the caller's original dictionary cannot alter the context. `resolve_fx_rate()` checks finiteness and positivity and returns typed missing/nonpositive/nonfinite/stale dispositions. USD resolves to 1.0 before foreign-FX freshness validation, so Texas USD-to-USD arithmetic does not depend on stale or missing foreign rates. One explicit context is attached to `ProjectEconomicInputs` for an evaluation. The fingerprint hashes the date, complete sorted rates, source, and freshness state; it also retains derived rules/source digests.

Independent/focused evidence:

- `tests/test_canonical_fx_context.py`: 22 passed.
- `tests/test_cache_fingerprint_expansion.py`: 8 passed.
- A stale-fallback context with irrelevant EUR data still allowed valid Texas USD `.24` to price exactly USD240,000 on USD1,000,000 QPE, while all malformed award values failed before economics.
- Literal current cap controls remain CZK450,000,000 / 21.238 = USD21,188,435.82 and ZAR25,000,000 / 16.3636 = USD1,527,781.17. No second conversion was observed.

### Netherlands — FAIL

The new missing-aggregate behavior is safer than the rejected state: when `has_other_productions` is asserted but the aggregate/evidence flag is absent, pricing fails closed; nonfinite, negative, and over-cap amounts reject. But it does not implement the controlling requirement.

`ProjectEconomicInputs` contains generic `evidenced_program_facts` and `amount_facts`, not a canonical production-company identity or award period. `IncentiveValueCapRule` names only three generic keys. `_resolve_incentive_dollar_cap()` receives no company/period identity and trusts the booleans and amount. The test's “Project A” and “Project B” are local variable names around direct `price_segment()` calls, not two canonical projects bound to a shared company/year ledger.

Independent reproducer: two identical calls using the EUR2,000,000 prior-awards scalar both execute and each return USD1,140,523.96. The pricing API accepts zero company-ID and zero period fields. The literal rule is a single EUR3,000,000 annual ceiling for one production company, not a caller-local scalar ceiling. The result remains partially wired.

### Texas — PASS

The exact awarded rate replaces the 31% ceiling only when all other gates are satisfied. Independent values on USD1,000,000 QPE:

- `.24` -> executable, USD240,000.
- `.31` -> executable, USD310,000.
- `0`, `.3100001`, `NaN`, `+inf`, and `-inf` -> non-executable.

Generic persisted amount parsing also drops nonfinite values. A deliberately stale foreign-FX context did not block the two valid USD cases and did not rescue an invalid case. The maximum is not substituted as the production's award.

### South Africa — FAIL

The new shared component-basis guard correctly rejects nonfinite, negative, or component amounts above broad qualifying QPE. It still does not satisfy the post-only rule. At `allocation_pricing.py:779-837`, the supplied `qpe_basis_used` is checked only against the segment's total `qpe`; there is no post/VFX line-set subtotal or line-identity reconciliation.

Independent reproducer: a USD1,000,000 allocation classified only as `production`, with **USD0 classified post/VFX spend**, accepts `za_nfvf_post_qsappe_usd=400000`, returns `executable=True`, and pays USD100,000. Literal conserved post-only economics are USD0. The existing test has the same weak oracle: it calls its broad allocation “post-only” but never supplies classified post/VFX lines.

### Alternative selection — FAIL

The baseline exclusion and verified-winner precedence work. Hard-failing and unpriced literal candidates do not enter. The rest of the contract does not.

`_is_conditional_eligible()` at `canonical_production_view.py:582-605` accepts every fully priced non-baseline non-comparable entry whose role state is `None`, `QUALIFIES`, `NOT_APPLICABLE`, or any conditional state. It does not inspect why the row is non-comparable. A single jurisdiction boolean from `_relocation_normalization_is_complete()` is treated as a blanket assertion for travel, local cost, and in-kind replacement. `_blocking_requirements()` then generates only that blanket key. It does not disclose the missing dimensions. Component/treaty entries do not aggregate every member's qualification.

Independent literal predicate table: **7/10 expected cases passed**. The three unsafe admissions were non-comparable candidates with `None`, `QUALIFIES`, and `NOT_APPLICABLE`; none proved that the only missing item was curable relocation evidence. The real FVD Greece/Romania component became leading conditional with `qualification_state=None` and no Romania/member gate in its blocker list.

## Batch B — `67fbc30` case matrix

| Required case | Result | Evidence |
|---|---|---|
| Baseline anchor excluded | PASS | `_is_baseline` returns false before pool admission; LU/FVD anchors are not selected as the new conditional. |
| Non-baseline blocked only by evidenced relocation completeness may appear | PARTIAL | Such a literal row appears, but the predicate does not prove that this is its only blocker. |
| `qualification_state=None` alone must not prove valid/curable | **FAIL** | Literal non-comparable `None` returns true; FVD runtime serves exactly this state. |
| Hard legal/authority/identity failure excluded | PASS for explicit `HARD_FAIL`; INCOMPLETE for all veto classes | Hard-fail literal returns false, but the function relies on upstream priceability rather than asserting the complete veto taxonomy. |
| Multiple dimensions disclose all gaps | **FAIL** | Only `relocation_completeness_evidenced__{primary code}` is generated. |
| Component/treaty retains every participant gate | **FAIL** | FVD `gr_cash_rebate + ro_film_office_cash_rebate` has no aggregate qualification/participant blocker. |
| Complete eligible distinct candidate ranks normally | PASS in generic existing ranking path | Comparable, qualification-admitting rows enter `comparable`; no real LU/FVD distinct candidate currently has complete evidence. |
| Conditional never displaces verified winner | PASS | Bad Hombres/Lips have rank 1 and no leading conditional. |
| Identity stable, not display-label matched | PASS | Pool uses stable `structure_id`; no label lookup. |
| Alternative materially distinct from anchor | PASS for surfaced LU/FVD identities | Manitoba differs from Mauritius; Greece+Romania differs from Greece-only. Their **admission quality** still fails. |

The intervention broadly admits priced non-comparable candidates; it is not limited to candidates blocked only by curable gaps. Manitoba and Greece+Romania cannot be accepted as the “strongest actionable” choices because their modeled NPC order is valid only within an incompletely normalized/qualified pool. They are the lowest modeled adjusted NPCs among the rows the defective predicate admits, nothing more.

## Original 12 programs

The complete row-by-row disposition is in `CINEGLOBE_FINAL_WIRING_12_PROGRAM_MATRIX_CODEX.csv`.

- Independently accepted executable/runtime-consumed: **8** — Australia, Czechia, France, Iceland, Morocco, Malta, Thailand, Texas.
- Independently accepted non-consumption identity control: **1** — Dubai `ae_dpip` / `ae_dxb_dpip` remains superseded and separate from Abu Dhabi.
- Still defective: **3** — Netherlands, Oregon, South Africa.
- Total denominator: **12**.

## Oregon disposition — B

**Decision: B — conditional formula opportunity with provisional economics, explicit cap/discretion, and exclusion from verified-winner ranking until award facts are evidenced.** Current complete fail-closed treatment is now stale; unconditional executable treatment would also be wrong.

Independently checked official authority:

- [ORS 284.368](https://www.oregonlegislature.gov/bills_laws/ors/ors284.html): 20% of payroll/benefits for work performed in Oregon; 25% of other actual Oregon expenses; USD1,000,000 Oregon-expense minimum; a regional increase equal to 10% **of the amount otherwise allowable**; statutory fund-availability/award structure.
- [Oregon Film OPIF program page](https://oregonfilm.org/article/oregon-production-investment-fund-opif/): the same 20%/25% bases and USD1m minimum, current USD21.2m annual fund, no single project over 50% of the fund in a fiscal year, and Greenlight labor stacking summarized at 26.2%.
- [OAR Chapter 951 Division 2](https://secure.sos.state.or.us/oard/displayDivisionRules.action?selectedDivision=4217): application before production, comparative/discretionary approval and contract gates, fund availability, USD1m-per-individual/company QPE exclusion, and the 50%-of-fund project limit.

Required separation:

- Payroll 20% and other Oregon expense 25% are distinct bases.
- The USD1m per-payee rule excludes QPE above the limit; it is not the final project cap.
- The 50% annual-fund rule caps the award. At the currently published USD21.2m fund, the nominal ceiling is USD10.6m, but the dated fund amount must remain explicit rather than treated as timeless.
- The regional provision multiplies the otherwise allowable incentive by 1.10; it is not +10 percentage points.
- Application, comparative allocation, contract, and fund availability mean modeled economics are provisional and may not become a verified winner before award evidence.

## Dubai disposition

Closed and unchanged. `ae_dpip` and runtime alias `ae_dxb_dpip` are superseded/blocked identity-control records. `ae_ad_film_rebate` is a separate Abu Dhabi identity and separately fail-closed. Only the Abu Dhabi rule contains 35%; no Abu Dhabi economics leak to Dubai. No Dubai research was reopened.

## New/changed-program inventory

There are **0 new canonical identities** after the last independent baseline. Three program-specific economic paths changed and were audited: Netherlands (not accepted), Texas (accepted), and South Africa (not accepted). The exact chain/status is recorded in `CINEGLOBE_FINAL_WIRING_PROGRAM_DELTA_CODEX.csv`. Shared FX dependency checks passed; shared selection failed. No alias, legacy loader, or transitive alias was found to reactivate a blocked program in the focused alias/import gates.

## Four-project runtime

All runs used real canonical project IDs and persisted budget/project facts, serially. Candidate counts are unchanged from the prior audit; only fingerprints changed as expected because the repaired fingerprint now includes the complete FX context.

| Project | Candidates priced/unpriced | Anchor result | Leading conditional | Verdict |
|---|---:|---|---|---|
| Little Utopia | 241 / 124 / 117 | `mu_edb_incentive`; USD573,059.70; NPC USD3,791,333.30; no verified selection | Manitoba; USD1,824,388.20; adjusted NPC USD3,269,304.80; `RULE_DATA_INCOMPLETE`; only blanket CA-MB blocker | Anchor stable; conditional not accepted |
| F#K Valentine's Day | 292 / 159 / 133 | `gr_cash_rebate`; USD1,445,659.84; NPC USD3,072,027.16; no verified selection | Greece + Romania post; USD1,465,850.60; adjusted NPC USD3,062,526.40; state `None`; only blanket GR blocker | Anchor stable; conditional not accepted |
| Bad Hombres | 238 / 122 / 116 | `us_nm_film_credit`; USD596,910.25; NPC USD1,885,112.75; rank 1 | None | PASS unchanged |
| Lips Like Sugar | 294 / 175 / 119 | `ca_film_30`; USD3,459,278.90; NPC USD8,524,375.10; rank 1 | None | PASS unchanged |

Literal arithmetic matches served values. Detailed fingerprints and blockers are in `CINEGLOBE_FINAL_WIRING_FOUR_PROJECT_RUNTIME_CODEX.csv`.

## Focused verification

- Current delta-focused group: **168 passed, 2 failed**, 5 warnings, 61.06s. The two failures are both in `test_leading_conditional_recommendation.py`.
- Current individual selection file rerun: **9 passed, 2 failed**, 5 warnings, 9.14s:
  - expected FVD leading conditional `USER_FACT_REQUIRED`, observed `None`;
  - expected non-null qualification, observed `None`.
- Independent literal/adverse selection probe: **7/10**.
- FX file: **22 passed**; cache/fingerprint file: **8 passed**.
- Formulaic real-pipeline, B3, alias, authority-exhaustion, import-order, selection-consistency, and four-project regression files in the focused group passed except for the two selection failures above.
- No full backend suite was run. Claude's historical `4,899 passed` is not current delta acceptance evidence.
- No command or project recomputation timed out. The environment lacks GNU `timeout`; real operations were bounded through the execution controller and all completed well inside their specified limits. No owned process or transaction was left running.

## Reachable stale/parallel paths

No alternate FX, alias, or legacy economic path was found reachable through the focused dependency cone. `REACHABLE_STALE_PATHS = 0`. The Oregon authority disposition is stale data in the **current canonical path**, not a parallel path. The `67fbc30` selection defect is likewise the live served path.

## Engineering process review

Repeated remediation was not caused by one actor or one cause:

| Cause class | Concrete evidence |
|---|---|
| Implementation defect | Netherlands comments claim canonical company/period binding, but the public inputs carry neither. South Africa implements only a broad-QPE inequality. `67fbc30` broadens the predicate without proving the cause of non-comparability. The prior prompt explicitly required all three invariants, so these are not instruction omissions. |
| Weak test oracle | Netherlands tests name two local variables “projects” but call an identity-free helper. South Africa labels a production-category allocation “post-only.” Both tests call production helpers for observed economics and omit independent source-identity/line-subtotal oracles. |
| Incorrect audit assumption | Claude's closeout inferred all rows closed from broad-suite success and descriptive comments; current focused tests fail, and adverse values contradict those claims. AG's unsourced USD10.6m Oregon figure was initially treated as unresolved, but the current official Oregon Film page supplies the USD21.2m fund input. |
| Stale/parallel path | No parallel runtime path was demonstrated. Oregon is a stale authority disposition on the canonical path; treating every regression as a path-fork problem would be unsupported. |
| Environmental/tooling constraint | The target worktree was dirty with unknown-owner test edits/probes and macOS lacks GNU `timeout`. An isolated worktree and bounded process controller preserved ownership and avoided conflating those files with target evidence. These constraints did not cause the three implementation defects. |

At most five instruction/process improvements:

1. Require each economic invariant to name its source identity fields and conservation boundary; comments or boolean “evidenced” labels cannot substitute for data binding.
2. Require at least one independent literal or line-identity oracle per repair and prohibit expected values manufactured by the production helper under test.
3. Keep a fixed acceptance matrix and denominator in every closeout; classify each row as catalogued, dispositioned, executable, consumed, and independently accepted.
4. Run the smallest adverse test set first under hard wall-clock bounds; broad-suite success may be regression evidence only after the adverse gates pass.
5. Start in an isolated worktree when the target checkout contains unknown-owner changes; record but preserve them, and never force-push.

What worked and should remain: canonical-repository-first recovery, frozen exclusions, serial database checks, stable program IDs, explicit fail-closed states, full FX-context fingerprints, and independent four-project controls.

## Acceptance gate

- Claude engineering delta: **PARTIAL — NOT ACCEPTED**.
- P0-SEL-ALT-001: **FAIL**.
- Original 12: **9/12 accepted dispositions; 8/12 executable and independently runtime-consumed; 3 defective**.
- New/changed programs audited: **3/3**; accepted **1**, partial **2**.
- Ready to merge: **NO**.
- MFNI: parked unchanged.
- Reinvestment: parked unchanged.
- UI: unchanged/deferred.
- Next step: execute the single bounded replacement Claude prompt in `CINEGLOBE_FINAL_WIRING_REMEDIATION_CLAUDE_PROMPT.md`, then perform one delta-only Codex acceptance pass.
