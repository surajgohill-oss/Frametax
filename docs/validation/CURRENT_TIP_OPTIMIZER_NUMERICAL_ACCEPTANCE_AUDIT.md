# Current-Tip Optimizer Numerical Acceptance Audit

**Audit date:** 2026-09-18

**Repository:** `surajgohill-oss/Frametax`

**Branch:** `claude/global-optimizer-remediation`

**Audited SHA:** `ec01556ffe80ed462e428b157b1cee07986e17af`

**Engine:** `canonical-1.81.0`

**Database:** `frametax2_claude_generic_discovery_audit_20260917` only

**Decision:** `OPTIMIZER_NOT_ACCEPTED`

## Scope and evidence standard

This is an independent, documentation-only audit of the current canonical optimizer for Little Utopia, F#K Valentine's Day, Bad Hombres, and Lips Like Sugar. Historical Claude/Codex artifacts were treated as leads and reconciled against current source, current persisted rows, and real `evaluate_project()` execution. No production code, project data, authority data, or shared-database data was changed.

- `STATIC_VERIFIED`: established directly from current source or immutable persisted trace.
- `RUNTIME_VERIFIED`: established by current-engine execution or a set-based query against the isolated audit database.
- `BLOCKED`: the current persisted or served contract lacks evidence needed for an independent conclusion.

## Environment proof

| Check | Evidence | Result |
|---|---|---|
| Worktree | `/Users/Suraj/cineglobe-claude-global-optimizer-remediation` | `STATIC_VERIFIED` |
| Branch | `claude/global-optimizer-remediation` | `STATIC_VERIFIED` |
| Local/remote start | local and `origin/claude/global-optimizer-remediation` both `ec01556ffe80ed462e428b157b1cee07986e17af` | `STATIC_VERIFIED` |
| Initial worktree | clean | `STATIC_VERIFIED` |
| Engine | `canonical-1.81.0` from `canonical_evaluation.py` | `STATIC_VERIFIED` |
| DB routing | `postgresql+psycopg`, `localhost:5432`, database `frametax2_claude_generic_discovery_audit_20260917` | `RUNTIME_VERIFIED` |
| Shared DB | no command in this audit routed to or wrote `frametax2` | `RUNTIME_VERIFIED` |

## Four-project current result table

All four evaluations returned `EVALUATION_REUSED` under the fingerprints below. Incentive and NPC recomputation variance is `$0.00`. Little Utopia has a known `$2.00` source/leaf allocation-rounding variance, but its selected incentive and NPC arithmetic reconcile exactly.

| Production | Current fingerprint | Evaluator-selected structure | Programs / segment QPE | Incentive | NPC | Independent variance | Evidence |
|---|---|---|---|---:|---:|---:|---|
| Little Utopia | `7e53bafd7435c04d8a4665d766fa15ab988cc573df69e932d1927dba1d50f31a` | **None**; baseline `7797227c-350c-4fcf-9600-1c741e0082bd` is priced but role qualification is `AUTHORITY_UNRESOLVED` | `mu_film_rebate`; MU QPE `$1,910,199.00` at 30%; US `$9,068.00` unclaimed | `$573,059.70` | `$3,791,333.30` | `$0.00` | `RUNTIME_VERIFIED` |
| F#K Valentine's Day | `d000fb05346e1f8dcfc49a59190c324bccb1546ecd4524959bd37b226c6830b1` | **None**; baseline `dd2348e5-f9b2-4b37-807e-e1f319574c51` is priced but role qualification is `USER_FACT_REQUIRED` | `gr_cash_rebate`; GR capped QPE `$3,614,149.60` at 40% | `$1,445,659.84` | `$3,072,027.16` | `$0.00` | `RUNTIME_VERIFIED` |
| Bad Hombres | `f1ee76316ba815e980368b8342c33e3bc023cd4ef0eaa73baaa8ad99e8e82d85` | `b43e05e6-b2b8-47d8-83d0-f8da98e0ff36` | `us_nm_film_credit`; US-NM QPE `$2,387,641.00` at 25% | `$596,910.25` | `$1,885,112.75` | `$0.00` | `RUNTIME_VERIFIED` |
| Lips Like Sugar | `0c9358beedb172e73215fb2a3d82998ee35284755858d0825791b6870195451e` | `c35798d1-9a57-4a3f-a6d9-7e139f765c87` | `us_ca_film_tv_credit`; US-CA QPE `$9,883,654.00` at 35% | `$3,459,278.90` | `$8,524,375.10` | `$0.00` | `RUNTIME_VERIFIED` |

Baseline result IDs, respectively: `c257d827-8382-437a-991e-0f32a8eea59b`, `b8deed3e-9f93-4342-af81-e5ff084ff9aa`, `c4720a49-5d1b-4ccc-87e8-eb1820cba5f9`, and `3256aabe-1b22-475a-a0ec-1160fbc9fc7e`.

### Material-alternative recomputation sample

| Production | Structure | Allocation and recomputation | Result |
|---|---|---|---|
| Little Utopia | `1b091ca1...` MU anchor + CA-MB VFX | MU `$4,302,827` + CA-MB `$52,500` + US `$9,068`; CA-MB 15% plus MU 30%; source/leaf difference `$2` | `RUNTIME_VERIFIED` |
| F#K Valentine's Day | `158efc82...` GR anchor + CA-MB post | CA-MB `$146,446` × 45% = `$65,900.70`; GR `$3,554,792` × 40% = `$1,421,916.80`; total `$1,487,817.50` | `RUNTIME_VERIFIED` |
| Bad Hombres | `a2048cba...` US-NM anchor + CA-MB post | CA-MB `$107,958` × 45% = `$48,581.10`; US-NM `$2,279,683` × 25% = `$569,920.75`; total `$618,501.85` | `RUNTIME_VERIFIED` |
| Lips Like Sugar | `ca3148c9...` US-CA anchor + CA-MB post | CA-MB `$611,230` × 45% = `$275,053.50`; US-CA `$9,272,424` × 35% = `$3,245,348.40`; total `$3,520,401.90` | `RUNTIME_VERIFIED` |

## Candidate-family completeness

The table distinguishes executable families from families not applicable to these four current project fact sets. Absence of a priced official co-production, multi-principal structure, or award-funded overlay is therefore not itself a discovery defect.

| Family | Current runtime evidence | Completeness result |
|---|---|---|
| Single jurisdiction | One current `single_country` priced baseline per project | `RUNTIME_VERIFIED` |
| Same-jurisdiction stacking | `multi_program` and `same_jurisdiction_group_stack` rows present; explicit priced/rejected dispositions | `RUNTIME_VERIFIED` |
| Component relocation | 93/145/94/168 priced rows for LU/FVD/BH/LLS, plus explicit rejections | `RUNTIME_VERIFIED` |
| Ordinary hybrid | 78/308/153/937 priced rows and 78/308/77/312 proof-dominated groups | `RUNTIME_VERIFIED`, subject to trace defect NUM-003 |
| Official co-production/treaty | 25/27/25/25 `CO_PRO_OPPORTUNITY` rows; required participant/contribution/personnel facts are absent | `RUNTIME_VERIFIED` as opportunity-only for these inputs |
| Multi-principal | Generic current code path exists; no applicable complete treaty allocation facts in these four projects | `STATIC_VERIFIED`; not runtime-applicable here |
| Grants/funds | Conditional programs remain zero-guaranteed metadata and do not reduce NPC without award facts | `RUNTIME_VERIFIED` |
| Combined structures | Generic combined paths exist; no applicable complete treaty/component facts in these four projects | `STATIC_VERIFIED`; not runtime-applicable here |

Current-row totals are 949 (LU), 6,983 (FVD), 591 (BH), and 1,689 (LLS). Every current row has a persisted `structure_type` and `candidate_status`.

## Allocation, QPE, rates, caps, and NPC

Set-based checks over every current `PRICED` ordinary hybrid found:

| Project | Priced hybrids | Maximum allocation variance | Structures with overlapping source line IDs | Result |
|---|---:|---:|---:|---|
| Little Utopia | 78 | `$2.00` source rounding | 0 | `RUNTIME_VERIFIED` |
| F#K Valentine's Day | 308 | `$0.00` | 0 | `RUNTIME_VERIFIED` |
| Bad Hombres | 153 | `$0.00` | 0 | `RUNTIME_VERIFIED` |
| Lips Like Sugar | 937 | `$0.00` | 0 | `RUNTIME_VERIFIED` |

The selected baselines and sampled component structures reconstruct from source lines, qualification registers, rates, caps, incentives, and budget-minus-incentive NPC. However, adjusted multi-component hybrid totals do not always reconstruct from the persisted trace: the maximum difference between the sum of persisted component incentives and the persisted structure total is `$892.50` for FVD and `$18,092.72` for LLS. The engine applies stacking adjustments, but the persisted trace omits the adjustment rows and post-adjustment per-program values. This is defect NUM-003.

The canonical integrity gate also flags per-program QPE sums above budget for lawful same-cost `multi_program` stacks. That check is a stale oracle: a shared eligible-cost base may lawfully support more than one credit, so summing per-claim QPE is not a spend-conservation test. Source-line allocation—not the arithmetic sum of claim-specific QPE—is the correct invariant.

## Eligibility, treaty gates, rejection, and dominance

- Little Utopia remains unresolved on Mauritius cultural-test applicability; the evaluator correctly returns no recommendation.
- F#K Valentine's Day remains conditional on a Greek aggregate cultural-content/personnel fact; the evaluator correctly returns no recommendation.
- Bad Hombres and Lips Like Sugar have `NOT_APPLICABLE` role qualification and current baseline selections.
- Treaty structures remain opportunities where participant/contribution/personnel facts are absent; they are not promoted to guaranteed NPC.
- All 775 current `DOMINATED_WITH_PROOF` rows identify exact candidate windows and incumbent structures. The trace does not persist an explicit numeric upper bound and proof inequality, so an auditor cannot validate the stopping inequality solely from the row. This is defect NUM-004.
- The canonical integrity gate exposed current hybrid rows containing discretionary programs while `administrative_allocation_risk` remains false. This is defect NUM-002.

## Ranking and served-state identity

For Bad Hombres and Lips Like Sugar, the selected baseline is the lowest-NPC candidate admitted to the directly comparable current universe. Lower raw-NPC relocation candidates are intentionally not directly comparable because relocation costs are not normalized.

For Little Utopia and F#K Valentine's Day, `evaluate_project()` returns `top_result = null`, and `Project.leading_structure_id` is null, because unresolved qualification blocks recommendation. The canonical workspace endpoint nevertheless publishes each priced baseline as `evaluation.top_result` because `project_workspace_view.py::_summarize_evaluation` chooses `comparable[0]` without applying the evaluator's qualification-admission predicate. This is defect NUM-001.

| Project | Evaluator recommendation | Persisted leading ID | `/workspace` top result | Result |
|---|---|---|---|---|
| Little Utopia | none | none | `7797227c-350c-4fcf-9600-1c741e0082bd` | `BLOCKED` — served contradiction |
| F#K Valentine's Day | none | none | `dd2348e5-f9b2-4b37-807e-e1f319574c51` | `BLOCKED` — served contradiction |
| Bad Hombres | `b43e05e6-b2b8-47d8-83d0-f8da98e0ff36` | same | same | `RUNTIME_VERIFIED` |
| Lips Like Sugar | `c35798d1-9a57-4a3f-a6d9-7e139f765c87` | same | same | `RUNTIME_VERIFIED` |

The workspace endpoint is internally scoped to the current fingerprint and engine, and its served IDs were verified as subsets of the matching persisted generation. It does not return the engine version or input fingerprint to the consumer, preventing downstream independent identity verification (NUM-005).

## Freshness, persistence, deduplication, and determinism

- All four projects returned `EVALUATION_REUSED` with stable current fingerprints and stable baseline structure/result IDs.
- Current summaries excluded other engine versions and fingerprints.
- Duplicate economic-route prevention tests passed in the focused regression portion.
- Current trace rows carry `canonical-1.81.0` and the current project fingerprint.
- No project input was mutated during this audit. Changed-input isolation was not rerun because the instruction required current real records and audit-only operation; the current code's changed-input contract remains covered by the existing focused tests included in the consolidated batch before its time limit.

## Historical-finding reconciliation

| Historical finding(s) | Current classification | Evidence |
|---|---|---|
| S-01 unknown pair fails closed | `CURRENTLY_FIXED` | Current bridge and rejection rows remain fail-closed. |
| S-02–S-14 legacy scenario/stacking defaults | `OBSOLETE` for canonical evaluation | Canonical `evaluate_project()` does not use the retired draft scenario path as its production evaluator. |
| S-15 conserving allocator | `CURRENTLY_FIXED` | Zero overlapping source IDs; exact conservation except documented `$2` LU source rounding. |
| S-16 default principal routing | `STILL_PRESENT` | `component_for` retains default principal classification for unmapped categories; current selected traces do not prove all service-location facts independently. |
| S-17 typed multi-claim representation | `CURRENTLY_FIXED` for current canonical families | Current structures persist explicit claims/components; same-jurisdiction stacking remains a dedicated bridge. |
| S-18 conditional funds zero NPC | `CURRENTLY_FIXED` | Conditional nodes do not enter guaranteed NPC. |
| S-19–S-20 estimated legacy grants/structures | `OBSOLETE` / isolated legacy | Not consumed by canonical `evaluate_project()`. |
| S-21–S-25 treaty eligibility/composition | `CURRENTLY_FIXED` for canonical orchestration | Missing facts produce opportunities/rejections rather than priced official structures in these projects. |
| S-26 in-kind zero-QPE discipline | `CURRENTLY_FIXED` | No free-FMV QPE promotion observed. |
| S-27 frozen in-kind precedents | `OBSOLETE` for canonical decisions | Not used as current general authority. |
| S-28 NPC-first ranker | `REGRESSED` at workspace adapter | Evaluator remains qualification-aware; workspace top-result selection is not (NUM-001). |
| S-29 admission predicate | `STILL_PRESENT` at workspace adapter | Workspace independently promotes first comparable row without the canonical qualification predicate. |
| P1-GATE-001 incomplete integrity-gate coverage | `CURRENTLY_FIXED` as negative-test coverage, but new runtime failures remain | Gate now checks freshness/rejection/participant classes; current run exposed NUM-002 and a stale same-cost-QPE oracle. |
| Historical 159/133 candidate-count oracle | `OBSOLETE` | Current valid discovery is 949/6,983/591/1,689 rows; no valid candidates were removed to satisfy old cardinality. |
| Historical shared-DB stale/missing projects | `OBSOLETE` for this isolated audit | This audit used current isolated rows only and did not mutate shared `frametax2`. |

### Historical four-project/Globe audit findings

Globe rendering itself was out of scope, but the historical audit's backend and served-contract findings were reconciled because they materially affect later Globe consumption.

| Historical finding | Current classification | Current evidence |
|---|---|---|
| P0 mandatory minimum-spend failures persisted as priced | `CURRENTLY_FIXED` | Current unpriced/rejected rows carry null incentive/NPC; current priced samples satisfy their persisted eligibility gates. |
| P0 component verified/risk-normalized NPC collapse and missing adjustment trace | `STILL_PRESENT` in narrower form | Component NPC fields are now distinct, but adjusted ordinary-hybrid totals still omit the stacking-adjustment bridge (NUM-003). |
| P0 multi-jurisdiction participants destroyed at API boundary | `CURRENTLY_FIXED` for current persisted/served structures | Current structures retain exact structure ID, routed allocations, and participant codes under the current fingerprint. |
| P0 Saudi maximum treated as guaranteed 60% | `CURRENTLY_FIXED` | Current authority/discretionary controls do not admit the historical deterministic-guarantee behavior into a selected recommendation. |
| P1 Globe not scenario-complete | `OBSOLETE` for this backend-only audit | No Globe visual or point-density acceptance claim is made here. |
| P1 status-bearing jurisdictions non-interactive | `OBSOLETE` for this backend-only audit | UI hit targets are explicitly outside this audit. |
| P1 hover/click selector divergence | `OBSOLETE` for this backend-only audit | UI interaction is explicitly outside this audit. |
| P1 Reports false empty state for LU/FVD | `REGRESSED` as a backend served-selection inconsistency | The inverse presentation error now occurs: evaluator correctly selects none, while workspace promotes the baseline (NUM-001). |
| P1 conditional/admin risk not cross-surface complete | `STILL_PRESENT` in canonical trace | Current hybrid rows can omit administrative allocation risk before any UI rendering (NUM-002). |
| Earlier split served architecture and stale/mixed rows | `CURRENTLY_FIXED` for generation filtering | Workspace reads current engine/fingerprint rows; NUM-005 remains a response-provenance gap, not stale-row leakage. |

## Numbered defect ledger

### NUM-001 — P1 — Workspace publishes recommendations the evaluator rejects

- **Actual:** LU and FVD have `evaluate_project().top_result = null` and null `leading_structure_id`, but `/workspace` publishes the priced baseline as `top_result`.
- **Location:** `backend/app/services/project_workspace_view.py`, workspace summary selection (`top_result = comparable[0]`).
- **Impact:** served consumers can present a recommendation despite unresolved mandatory qualification.
- **Smallest correction:** consume the same canonical selection/admission predicate used by `_summarize_evaluation()`/canonical production view; add endpoint tests for unresolved role qualification and exact structure identity.

### NUM-002 — P1 — Hybrid discretionary-program risk is not persisted

- **Actual:** current hybrid rows containing discretionary programs have `administrative_allocation_risk = false`; the integrity gate detects them across all four projects.
- **Location:** hybrid persistence path in `backend/app/services/canonical_evaluation.py` around the `ordinary_component_hybrid` trace construction.
- **Impact:** selective/administrative receipt risk is understated in persisted and served optimizer state.
- **Smallest correction:** derive risk from every component program using the canonical authority/administration disclosure helper, persist it and its reasons, and regression-test current hybrid rows.

### NUM-003 — P1 — Stacking-adjusted hybrid totals are not trace-reconstructable

- **Actual:** component incentives sum to a value different from the persisted adjusted total (up to `$892.50` FVD and `$18,092.72` LLS), but adjustment rows and post-adjustment values are absent.
- **Location:** `backend/app/calculators/structural_archetype_generator.py::generate_structural_candidate` and hybrid trace persistence in `backend/app/services/canonical_evaluation.py`.
- **Impact:** an independent auditor cannot reproduce incentive/NPC from persisted inputs even when the engine's internal adjustment may be correct.
- **Smallest correction:** persist raw per-program values, each ordered stacking adjustment with rule identity/base/delta, and post-adjustment values; assert the persisted bridge sums exactly to the structure total.

### NUM-004 — P2 — Dominance rows omit the numeric stopping inequality

- **Actual:** rows persist candidate windows, incumbent identity, window size, and dominated count, but no explicit next-candidate upper bound or stored inequality.
- **Location:** `DOMINATED_WITH_PROOF` trace builders in `backend/app/services/canonical_evaluation.py`.
- **Impact:** the exact proof cannot be checked from persisted evidence without rerunning implementation logic.
- **Smallest correction:** persist the cutoff marginal bound, interaction-safe total upper bound, incumbent value, and explicit inequality for each represented candidate set.

### NUM-005 — P2 — Workspace omits generation identity

- **Actual:** workspace filtering uses the current engine/fingerprint internally but does not expose either value.
- **Location:** `backend/app/services/project_workspace_view.py` response contract.
- **Impact:** a later Globe consumer cannot independently verify that structure IDs and rankings belong to the expected generation.
- **Smallest correction:** include `engine_version` and `input_fingerprint` at evaluation level; add exact endpoint assertions.

## Test execution (single pass per requested class)

| Execution | Result | Duration / bound |
|---|---|---|
| Four current-project `evaluate_project()` batch | 4 `EVALUATION_REUSED`; fingerprints and anchor economics above | bounded sequential run |
| Set-based allocation/QPE/status/identity queries | All priced-hybrid source pools conserved; zero overlapping line IDs; defects NUM-002/003/004 reproduced | bounded foreground queries |
| Four-project canonical integrity gate | Failed on stale same-cost QPE-sum oracle and current discretionary-risk omissions | bounded targeted run |
| Consolidated relevant regression batch (11 files) | **169 passed, 0 failed, 7 warnings before stop**; manually stopped at repository ceiling, exit 2 from `KeyboardInterrupt` | 13m27s; no rerun |

The interrupted regression is not represented as a passing full suite. It produced no test failure before the enforced stop, but it does not supply complete regression acceptance.

## Acceptance decision

The current engine reproduces all four baseline economics exactly, conserves routed source spend in the sampled and set-based hybrid checks, and preserves current generation identity. It is **not ready for independent numerical acceptance** because:

1. served recommendation identity disagrees with the canonical evaluator for two of four productions;
2. discretionary-risk metadata is wrong on current hybrid rows;
3. stacking-adjusted hybrid economics cannot be independently reconstructed from persisted traces; and
4. the consolidated relevant regression did not complete within the repository time ceiling.

**Terminal status: `OPTIMIZER_NOT_ACCEPTED`**
