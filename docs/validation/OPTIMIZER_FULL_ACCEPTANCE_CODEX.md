# CineGlobe Optimizer Full Program-Consumption + Behavioral Wiring Acceptance — Codex

Audit date: 2026-09-05  
Mode: read-only forensic audit; no external research; no implementation  
Audited application HEAD: `cf7bf7cba423ec8edb32afcf46855f1480aec9be`

## 1. EXECUTIVE VERDICT

`NO_GO_FOR_OPTIMIZER_FINAL_BEHAVIORAL_CLOSEOUT`

The three named Claude P0 repairs reproduce on the four-project subset, and treaty budget conservation is correct across all 325 current treaty opportunities. The broader 14-project runtime corpus exposes two remaining P0 defects:

1. Nine projects have an evaluator-written `Project.leading_structure_id` pointing to a non-comparable relocation while the canonical served selection is null.
2. 1,878 component structures include a non-claiming `US` anchor in the served economic `participants` list.

The required current-family and program-universe acceptance therefore is not earned. The defects are localized; no broad audit or new jurisdiction research is required.

## 2. AUDITED REPOSITORY STATE

- Repository: `surajgohill-oss/Frametax`
- Branch: `claude/audit-frametax-features-NZcX5`
- Audited HEAD: `cf7bf7cba423ec8edb32afcf46855f1480aec9be`
- Required ancestors verified: `dcc6dde0a5ef4576ccf6da1582458f5d1354fb41`, `136936f8`, and `0f1c8d30ebbd6e926eaad8d198781c3b1a8ae5ef`.
- Later commits are documentation/MFNI artifacts only: `cb396c6`, `e5bb6f2`, `a639171`, `1ff54ea`, `cf7bf7c`.
- P0 source edits remain present in `canonical_evaluation.py`, `canonical_production_view.py`, and `bestPricedCandidate.js`.
- Unrelated pre-existing untracked files were not touched or staged.

## 3. CANONICAL PROGRAM UNIVERSE

The repository has layered inventories; conflating them produces false counts.

| Layer | Current count | Meaning |
|---|---:|---|
| `global_inventory.ALL_PROGRAMS` | 303 | Discovery/catalog records across 211 jurisdiction codes; none carries a populated `program_slug`, so this is not the executable identity set. |
| Doctrine records | 118 | Canonical executable doctrine records. |
| Jurisdiction profiles | 113 | Capability/comparison profiles. |
| Ordinary discovery program union | 124 | Distinct doctrine/profile slugs reached by `production_discovery`. |
| Rate-rule registry / optimizer-visible | 125 | Exact structural definition in `all_optimizer_visible_program_slugs()`. |
| Authority-coverage registry | 145 | Includes non-economic, duplicate, superseded, and non-runtime records beyond the 125 rate-bearing programs. |

Optimizer-visible economic states: 111 `DETERMINISTIC_PRICEABLE`, 11 `CONDITIONAL_NONDETERMINISTIC`, 2 `MATERIAL_ECONOMIC_RULE_UNRESOLVED`, and 1 `SUPERSEDED`.

Conformance states: 65 `CONFORMANT`, 59 `CONDITIONAL`, 1 `NONCONFORMANT`. The sole nonconformant slug is `au_producer_offset`; despite its absent ordinary discovery identity/profile, it is consumed and priced only through official-treaty unlocks.

Coverage states: 89 `PRICEABLE_VALIDATED`, 31 `AUTHORITY_UNRESOLVED_NON_PRICEABLE` (provenance-only disclosure; economics still price under the project’s two-axis rule), 2 `NON_GUARANTEED_SELECTIVE`, 2 `UNPRICEABLE_AUTHORITY_INSUFFICIENT`, and 1 `SUPERSEDED`.

Allocation classifications among the 125: 104 unset/ordinary, 9 competitive, 6 first-come-first-served, and 6 discretionary.

## 4. PROGRAM CONSUMPTION SUMMARY

The program CSV accounts for all 125 optimizer-visible programs exactly once:

| Disposition | Count |
|---|---:|
| `EXECUTED_AND_PRICED` | 100 |
| `EXECUTED_CONDITIONALLY` | 8 |
| `CANDIDATE_BUT_NOT_PRICED` | 12 |
| `VALIDLY_NONFORMULAIC` | 2 |
| `VALIDLY_BLOCKED_BY_AUTHORITY_OR_RULE_DATA` | 2 |
| `VALIDLY_NONCONFORMANT` | 1 |
| `SILENTLY_EXCLUDED` | 0 |

124 programs enter ordinary discovery. `au_producer_offset` is the only exception; it reaches eligibility, conditional pricing, persistence, and serving through treaty unlocks. All 125 appear in a generated/persisted current trace. 108 price in at least one current runtime example; 17 have explicit project/rule/authority dispositions.

## 5. AUTHORITY / READINESS GATE

Five programs are economically blocked by the coverage registry:

- `ae_dxb_dpip` — superseded.
- `jp_vipo_location_incentive`, `kr_kofic_location_incentive` — non-guaranteed selective.
- `kz_investment_subsidy`, `us_or_opif` — authority insufficient for deterministic economics.

Those blocks are semantically supported by current canonical data. The 31 provenance-incomplete rate-bearing programs are not silently blocked and do price, consistent with `PROJECT_RULES.md`’s two-axis rule.

Answer to the required question: **No otherwise deterministic ordinary-discovery program is suppressed by stale authority metadata despite sufficient canonical pricing data.** `au_producer_offset` is a separate identity/conformance inconsistency, not an economic suppression: the treaty path uses it while ordinary discovery does not.

## 6. CANDIDATE COMPLETENESS

- Every one of the 124 ordinary discovery programs produces a full/single candidate in at least one current project.
- `au_producer_offset` produces treaty conditional components, bringing generated program coverage to 125/125.
- Component routing persists 2,585 fully priced routes. A further 889 current target/component attempts fail their segment-level threshold and are intentionally not persisted; this audit reconstructs each in the rejection ledger.
- No priceable supported component target is removed by the former top-six pruning rule.
- Thirteen multi-program candidates are generated. Every one is the current Ontario `ca_on_opstc + on_ofttc` mutually-exclusive pair and is correctly rejected.
- Other named pairs do not yield a missing positive stack: their necessary member is unpriceable in this corpus, or the pair is cross-jurisdiction treaty economics rather than a same-location stack.

The remaining candidate-accounting problem is observability: the 889 failed component attempts have explicit transient pricing blockers but no persisted/served per-instance rejection row.

## 7. P0-1 DELTA

The named four-project results reproduce:

- Little Utopia: evaluator/served canonical selection null.
- F#K Valentine’s Day: evaluator/served canonical selection null.
- Bad Hombres: evaluator leader and served canonical leader both `143828b1-b5ad-49d7-8831-dd12fc12efad`.
- Lips Like Sugar: evaluator leader and served canonical leader both `270ec887-f15a-416f-9ca0-f5dd64992e6a`.

The corpus-wide acceptance fails. These nine projects have no current baseline row, so `_summarize_evaluation()` executes `top_pair = priced[0] if priced else None` and writes a non-comparable relocation to `Project.leading_structure_id`; `build_production_and_structures()` correctly finds no comparable rank-1 and serves `canonical_selected_structure_id = null`:

`10 Double Zero`, `Baron Samedi`, `Going Places`, `Interference`, `Rocky Mountain`, `The Cure`, `The System`, `Twilight of the Dead`, `Underwater`.

This is the first divergence. The state endpoint serves both values, and frontend active/manual-leading paths can consume `production.leading_structure_id`; canonical selection is therefore not a single semantic source of truth corpus-wide.

## 8. P0-2 DELTA

The four-project subset reproduces Claude’s 707 component rows with 0 participant mismatches. The historical LU structure `8172eb82-c2cc-4816-a331-beffddab5199` is a retained `canonical-1.52.0` row, not a current served structure. Its current equivalent examples include `05b645a4-9d5a-41bb-912d-8b1dc1853b7c` and `f4a67ca6-5c25-4a08-9863-65db6dd560a0`; both correctly serve `['MU', 'CA-MB']`, while any non-claiming geography remains only in segments/allocation.

The broader corpus fails: 1,878 of 2,585 current component rows include non-claiming `US` as a served economic participant. Counts are:

| Project | Contaminated / component rows |
|---|---:|
| 10 Double Zero | 250 / 250 |
| Baron Samedi | 203 / 203 |
| Going Places | 221 / 221 |
| Interference | 205 / 205 |
| Rocky Mountain | 258 / 258 |
| The Cure | 140 / 140 |
| The System | 203 / 203 |
| Twilight of the Dead | 154 / 154 |
| Underwater | 244 / 244 |

Root cause: `_empty_structure_entry()` initializes `_participant_codes = [code]` before its component-specific `claims_incentive is True` filter. For a project whose primary `US` geography has no home incentive program, `US` therefore survives despite a segment with `claims_incentive=False` and `program_slug=None`.

## 9. P0-3 DELTA

Verified fixed.

- Current treaty rows: 325 total.
- Deterministically solvable/eligible conditional scenarios: 282.
- Fully priced conditional scenarios: 123.
- Non-conserving allocations: 0.
- Double-counted combined QPE: 0.
- Independent incentive recomputation mismatches: 0.
- Unexplained: 0.

LU GB/IE current result `b51582a8-4a86-4f5b-95a5-aa902fc959d1`: GB 80%, IE 20%, gross $4,364,393.00, independently recomputed combined QPE $4,063,264.00, incentive $970,257.91, NPC $3,394,135.09.

## 10. SINGLE COUNTRY

`WIRED_AND_EXECUTED`. Six baseline rows exist; five are fully priced and directly comparable. The sixth, the 5 LBS OF PRESSURE IFTC ceiling-only variant, is explicitly unpriced. Budget allocation, QPE, incentive, NPC, persistence, and serving reconcile.

## 11. FULL RELOCATION

`PARTIALLY_WIRED`. All 1,730 rows persist and serve: 1,438 priced/review-only, 51 statutory rejects, 181 pricing/authority blocks, and 60 feasibility/coverage review rows. Economics reconcile, but the evaluator’s no-baseline fallback selects non-comparable relocations for nine projects (P0-SEL-001).

## 12. COMPONENT / ANCHOR

`PARTIALLY_WIRED`. Allocation, routed QPE, incentive, adjustment, NPC, persistence, and serving reconcile for 2,585 priced rows. All supported current targets are attempted. Two defects remain:

- 1,878 served participant lists contain a non-claiming primary geography (P0-PART-001).
- 889 threshold-failed attempts have no persisted/served per-instance disposition (P1-REJ-001).

Anchor remains a role inside `component_relocation`, not a standalone structure type.

## 13. MULTI-PROGRAM / STACKING

`WIRED_BUT_VALIDLY_BLOCKED` for this corpus. Thirteen Ontario pair candidates reach the named stacking rule and are explicitly `RULE_REJECTED` as mutually exclusive. Unknown pairs fail closed. No verified, same-location, fully-priceable stackable pair is available in the present corpus but omitted by generation.

## 14. TREATY CO-PRODUCTION

`WIRED_BUT_VALIDLY_BLOCKED`. Discovery, treaty lookup, contribution allocation, participant pricing, QPE, incentive, NPC, persistence, and serving are present. All 325 rows remain disclosure-only top-level opportunities until project contribution facts are confirmed; 159 of the 282 solvable scenarios also retain explicit canonical program-data gaps. No double-counting remains.

## 15. DISCRETIONARY / SELECTIVE

The six optimizer-visible discretionary programs are `lu_filmfund_tax_shelter_rebate`, `mu_edb_incentive`, `sa_film_commission_rebate`, `sg_made_with_singapore_rebate`, `us_ky_keiia`, and `us_or_opif`. The project policy mechanism is generic by `allocation_type`, program override, and default fact; it is not Saudi-specific. Formulaic floors remain separate from administrative certainty, and served structures disclose `administrative_allocation_risk`.

The two non-guaranteed selective programs (`jp_vipo_location_incentive`, `kr_kofic_location_incentive`) remain unpriced. Competitive and preapproval programs retain modeled economics only where a deterministic floor exists, with administrative risk disclosed.

## 16. PROGRAM ECONOMIC RECOMPUTATION

Representative canonical checks all satisfy `NPC = gross budget - selected incentive + total adjustments` exactly:

| Project / family | Structure | QPE | Incentive | Adjustments | Served NPC | Variance |
|---|---|---:|---:|---:|---:|---:|
| LU single / `mu_edb_incentive` | `bf179f4e-3ddd-4c93-a44d-485c64901186` | $1,910,199.00 | $573,059.70 | $0.00 | $3,791,333.30 | $0.00 |
| FVD single / `gr_cash_rebate` | `bef9f9d9-3463-40c5-8a2d-4c7a4128d66c` | $3,614,149.60 | $1,445,659.84 | $0.00 | $3,072,027.16 | $0.00 |
| BH single / `us_nm_film_credit` | `143828b1-b5ad-49d7-8831-dd12fc12efad` | $2,387,641.00 | $596,910.25 | $0.00 | $1,885,112.75 | $0.00 |
| LLS single / `us_ca_film_credit` | `270ec887-f15a-416f-9ca0-f5dd64992e6a` | $9,883,654.00 | $3,459,278.90 | $0.00 | $8,524,375.10 | $0.00 |
| LU full relocation / `me_cash_rebate` | `4ba8d160-714f-4117-b6f7-61fabe8e72be` | $4,054,196.00 | $1,013,549.00 | $729,300.00 | $4,080,144.00 | $0.00 |
| FVD component / GR + CA-MB | `d6623f45-588c-46d2-be4a-816b3ac46447` | $3,624,349.60 | $1,450,249.84 | $331,260.00 | $3,398,697.16 | $0.00 |

Persisted result fields and canonical served fields match for these samples. No unexplained material economic variance was found.

## 17. REJECTION ACCOUNTING

The rejection ledger contains 5,543 rows: 4,654 current persisted/served rows that are unpriced or non-comparable, plus 889 nonpersisted component attempts reconstructed from the current generator and pricing kernel.

| Rejection class | Count |
|---|---:|
| `OTHER_EXPLICIT` (priced but non-comparable) | 4,023 |
| `MINIMUM_SPEND_FAIL` | 940 |
| `TREATY_CONTRIBUTION_FAIL` | 325 |
| `RATE_RULE_GAP` | 154 |
| `NONFORMULAIC` | 28 |
| `AUTHORITY_DATA_GAP` | 28 |
| `PROJECT_INELIGIBLE` | 18 |
| `NONCONFORMANT` | 14 |
| `STACK_RULE_REJECTED` | 13 |

No unexplained bucket was used. The 889 component attempts are explicit in transient `SegmentEconomics.blockers`, but the runtime intentionally drops them before persistence; this is an auditability gap, not a hidden economic winner.

## 18. SILENT OMISSIONS

- Optimizer-visible program never touched by ordinary discovery: `au_producer_offset` only. It is not silently absent from economics; treaty unlocks generate, price, persist, and serve it conditionally.
- Discovered but never eligibility-tested without an explicit block: 0.
- Eligible program with no supported-family candidate: 0.
- Priced structure not persisted: 0.
- Current persisted structure not served by the main allocated-structures view: 0.
- Silently omitted deterministic executable programs: 0.

The separate 889 component threshold failures are not persisted per instance and are therefore invisible to ordinary runtime rejection reporting. They are fully enumerated in this audit’s rejection ledger.

## 19. PERSISTENCE / SERVED CONSISTENCY

The current true-input generations contain 4,659 structures, and the allocated-structures API view serves all 4,659. Main structure economics match their persisted rows.

A stale-generation helper defect remains: `current_result_fingerprint()` returns the most recently created current-engine fingerprint, not necessarily the fingerprint matching current inputs after an input is reverted. Current mismatches:

- FVD: true current `c19a35ed1b3c…`; helper returns `e295712ec80a…`.
- LLS: true current `2c20c3ef2744…`; helper returns `0e7df02bb04c…`.

`build_production_and_structures()` reconstructs the true fingerprint and is correct. `build_generic_pkg_and_economics()` still uses the newest-row helper for its baseline register, so one `/projects/{id}/state` response can mix structure and package generations. The sampled economics happen to be numerically identical, but the provenance/generation identity is not. Classified P1-FRESH-001.

## 20. CANONICAL SELECTION SINGLE SOURCE

Not achieved. `canonical_production_view` correctly selects only comparable rank-1 structures; `_summarize_evaluation` separately promotes the cheapest priced relocation when no baseline row exists and persists that result into `Project.leading_structure_id`. The project-state API exposes both fields, while frontend `activeStructure` permits a leading-ID override. P0-SEL-001 is therefore a real semantic split, not a display-only discrepancy.

## 21. ENGINE VERSION / STALE RESULTS

- Engine constant: `canonical-1.53.0`.
- Every main allocated-structure row served in this audit uses `canonical-1.53.0` and the recomputed current-input fingerprint.
- The historical LU component ID named in the prompt remains only as `canonical-1.52.0` history and is not served as current.
- Engine version prevents 1.52 results from masquerading as current.
- Same-version reverted-fingerprint selection is not fully safe in `current_result_fingerprint()` / generic package serving (P1-FRESH-001).

## 22. REAL PROJECT CORPUS

Four projects were audited deeply: Little Utopia, F#K Valentine’s Day, Bad Hombres, and Lips Like Sugar. The full optimizer-ready corpus is 14 projects:

`10 Double Zero`, `5 LBS OF PRESSURE`, `Bad Hombres`, `Baron Samedi`, `F#K Valentine’s Day`, `Going Places`, `Interference`, `Lips Like Sugar`, `Rocky Mountain`, `The Cure`, `The Little Utopia`, `The System`, `Twilight of the Dead`, `Underwater`.

Current family totals: 6 `single_country`, 1,730 `full_relocation`, 2,585 `component_relocation`, 13 `multi_program`, and 325 `treaty_coproduction` = 4,659 structures.

## 23. CANONICAL GATES

Executed results:

- Canonical Budget Integrity Gate: PASS, four locked budgets, 16/16 invariant families.
- Non-Globe Canonical Integrity Gate: PASS, 14 projects, 13/13 reported invariant families; 36 budgetless projects skipped.
- Backend suite: 4,750 passed, 3 skipped.
- Frontend suite: 169 passed, 0 failed.

The non-Globe gate does not materially protect all repaired behavior:

1. Selection checks `canonical_selected_structure_id` against served rank 1 only; it never compares evaluator `top_result` or `Project.leading_structure_id`, so it misses all nine P0-SEL-001 divergences.
2. Component participant expected-set logic unconditionally adds `primary_jurisdiction`, reproducing rather than detecting P0-PART-001 when the primary segment claims no incentive.
3. Treaty allocation checks a 100% allocation sum and a very loose incentive plausibility bound; it does not independently recompute combined QPE from participant shares. This audit performed that missing recomputation.
4. Program onboarding checks only fully-priced top-level structure program IDs, so it does not catch `au_producer_offset` being classified nonconformant while pricing inside a conditional treaty scenario.

Gate exit status is therefore not acceptance proof for the requested full scope.

## 24. CLAUDE CLAIM RECONCILIATION

| Claim | Result | Evidence |
|---|---|---|
| LU canonical null | VERIFIED | Current served canonical null. |
| FVD canonical null | VERIFIED | Current served canonical null. |
| BH leader preserved | VERIFIED | Same ID in evaluator/project/served rank 1. |
| LLS leader preserved | VERIFIED | Same ID in evaluator/project/served rank 1. |
| 707 component structures / 0 mismatches | PARTIALLY_VERIFIED | Exact for the four-project subset; broader corpus has 1,878 mismatches in 2,585 rows. |
| LU participants `['MU','CA-MB']` | VERIFIED | Current equivalent rows reproduce; named ID is retained 1.52 history. |
| LU treaty 80/20 | VERIFIED | Current GB/IE scenario. |
| LU combined QPE about $4.063m | VERIFIED | $4,063,264.00 independently recomputed. |
| 82 resolved treaty scenarios / 0 non-conserving | VERIFIED | Exact for the four-project subset; corpus-wide 282 resolved, 0 non-conserving. |
| Frontend 169/169 | VERIFIED | Reproduced. |
| Backend 4,750 passed / 3 skipped | VERIFIED | Reproduced. |
| Budget Gate 16/16 | VERIFIED | Reproduced. |
| Non-Globe Gate 13 families / 14 projects | PARTIALLY_VERIFIED | Counts/pass reproduced, but assertions miss the two live P0 defects and do not recompute treaty QPE. |

## 25. CURRENT CAPABILITY BOUNDARY

Current implemented persisted families remain exactly: `single_country`, `full_relocation`, `component_relocation`, `multi_program`, and `treaty_coproduction`.

Roadmap-only, not failed by this audit: non-treaty split/combination, separate majority/minority family, multi-party co-production, distinct service-production family, grants/funds economic structures, hybrid economics, reinvestment economics, and in-kind economics. No current runtime claim was found that these are complete canonical economic families.

MFNI, Travel/Post expansion, Globe, SA-2, and new authority research were not performed.

## 26. REMAINING P0

### P0-SEL-001 — evaluator/canonical selection divergence

- **Programs:** multiple priced relocation programs.
- **Projects:** 10 Double Zero; Baron Samedi; Going Places; Interference; Rocky Mountain; The Cure; The System; Twilight of the Dead; Underwater.
- **Family/stage:** full relocation → ranking/selection/persistence/serving.
- **Expected:** no evaluator/project canonical winner when every priced candidate is non-comparable.
- **Observed:** `_summarize_evaluation()` writes its cheapest priced relocation to `Project.leading_structure_id`; canonical view returns null.
- **Root cause:** no-baseline fallback ignores `is_directly_comparable`.
- **Bounded remediation:** make `_summarize_evaluation` use the same comparable/qualification admission contract as `canonical_production_view`, and add a gate assertion comparing evaluator top result, project pointer semantics, and served canonical ID on every optimizer-ready project.

### P0-PART-001 — non-claiming primary contaminates component participants

- **Programs:** component targets across the ordinary rate universe.
- **Projects:** the nine `US`-home projects listed in section 8.
- **Family/stage:** component relocation → canonical view/API participant identity.
- **Expected:** served economic participants equal the distinct segment jurisdictions with `claims_incentive=True`; non-claiming geography remains in allocation/segments only.
- **Observed:** 1,878 rows additionally serve `US`, whose segment has `claims_incentive=False` and no program.
- **Root cause:** `_empty_structure_entry()` pre-seeds primary jurisdiction before applying the claims filter.
- **Bounded remediation:** for component rows, build participants only from claiming segments; preserve primary geography separately in `primary_jurisdiction` and allocation. Correct the gate’s expected-set logic and sweep all 2,585 current component rows.

## 27. REMAINING P1

- **P1-FRESH-001:** `current_result_fingerprint()` selects newest current-engine history rather than recomputing current inputs; FVD and LLS generic package/register reads can use a different generation from their structure view.
- **P1-REJ-001:** 889 component threshold-failed attempts carry explicit transient blockers but are deliberately not persisted/served per instance; runtime rejection accounting cannot reproduce this ledger without rerunning generation.
- **P1-CONF-001:** `au_producer_offset` is classified `NONCONFORMANT` due missing ordinary doctrine/requirements identity while the treaty path prices it in 123 fully-priced conditional scenarios. Classification and special treaty-only relevance need one canonical representation.
- **P1-GATE-001:** the non-Globe gate’s selection, participant, treaty-QPE, and conditional-program assertions do not protect the semantics claimed by its labels.

## 28. FINAL VERDICT

`NO_GO_FOR_OPTIMIZER_FINAL_BEHAVIORAL_CLOSEOUT`

The current optimizer program universe is fully dispositioned and its pricing/allocation core is largely connected, but the broader corpus still violates canonical selection and participant-identity requirements. Repair only P0-SEL-001 and P0-PART-001, strengthen their exact gate assertions, then rerun this bounded acceptance corpus. Do not reopen jurisdiction research or future-family design.
