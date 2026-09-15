# Codex 305-Program Delta Wiring and Optimizer Audit

**Status: NOT ACCEPTED**  
**Base:** `3b5c3f5ea7c16358b8fe9ed64f0f5f2181d05ae5`  
**Mode:** isolated, read-only production behavior; tests and validation artifacts only.

## Deterministic population

The reconciliation ledger contains 586 unique identities. Exactly 305 are in scope: 119 AG-only, 166 Codex-only, and 20 material conflicts. The other 281 remain frozen. Every one of the 305 has exactly one row and one terminal audit disposition in `CODEX_305_PROGRAM_DELTA_AUDIT.csv`. No row silently disappears: absent executable identities retain an explicit final-manifest non-entry disposition.

## Result

| Disposition | Count |
|---|---:|
| `ALIAS_MERGED` | 1 |
| `AUTHORITY_EXHAUSTED_FAIL_CLOSED` | 156 |
| `CONDITIONAL_AND_RUNTIME_VERIFIED` | 4 |
| `DEFECTIVE_OR_INCOMPLETE` | 53 |
| `DISPLAY_ONLY_ZERO_GUARANTEED_VALUE` | 83 |
| `NON_ECONOMIC_DISPLAY_ONLY` | 7 |
| `SUPERSEDED_OR_RETIRED` | 1 |

There are **53 defective or incomplete rows**. The largest class is a direct contract conflict: programs the final manifest requires to be display-only or fail-closed still resolve through live intrinsic priceability, so stale RateRules/doctrines can reactivate them. Those rows cannot be accepted merely because the prior Claude result called them non-priced.

## Intended priceable delta

The current final manifest designates 12 delta rows as authority-verified priceable: one automatic and 11 conditional. Four have complete independent real-pipeline evidence in this acceptance run: `mt_mfc_rebate`, `mu_edb_incentive`, `nl_film_production_incentive` (`nl_nfpi` manifest identity), and `us_or_opif`. Eight remain incomplete: six have only rate/discovery or kernel-level proof, `ca_bc_dave` lacks a canonical identity binding, and the proposed Ohio identity has no RateRule/discovery implementation. Exact arithmetic and gaps are in the executable and numerical matrices.

## Mandatory 12-program overlay

The prompt's statement that all named 12 are “within the 305” is not literally true in the reconciliation CSV. They were audited as a mandatory overlay without changing the 305 denominator. Netherlands, South Africa, and Oregon now pass their hostile cases. The matrix is **11/12 accepted**: the Czech animation identity remains fail-closed in the final manifest while live runtime treats it as executable, so the controlling artifacts conflict.

## Three repaired programs

- **Netherlands — PASS.** Public-writer concurrency, stable event identity, APPROVED→GRANTED collapse, EUR-only cap, explicit period, unverified evidence, isolation, persistence stability, and invalid amount/currency cases passed.
- **South Africa — PASS.** Exact line-derived QSAPPE, under/over scalar rejection, excluded/untraced/contingent handling, and rate/cap recomputation passed.
- **Oregon — PASS.** The real DB-backed path produced exactly $814,000, persisted one result, reused it identically, enforced disjoint payroll/other bases and the per-payee cap, rejected the $50m/$50m hostile facts, and never produced negative NPC. The Oregon-specific probe enables discovery only; strict downstream line reconciliation determines economics.

## Four project controls

All four remain exact: Little Utopia $573,059.70 / $3,791,333.30; F#K Valentine's Day $1,445,659.84 / $3,072,027.16; Bad Hombres $596,910.25 / $1,885,112.75; Lips Like Sugar $3,459,278.90 / $8,524,375.10.

## Stack and hybrid interactions

Only two named relationships touch the 12 intended priceable delta rows: Malta + Eurimages (`allowed`) and Jordan rebate + tourism (`conditional`, therefore not publishable as an automatic stack). Every other pair remains ungenerated absent an accepted named rule. No automatic unknown stack was found.

## Claude engineering delta

The NL/ZA/OR changes are bounded root-cause repairs or valid supporting changes. The two Oregon pre-pricing probes are justified special cases only because the real DB test proves they cannot determine the priced basis. Migration 0074's `award_event_id NOT NULL` addition assumes an empty existing ledger; deployment requires the stated preflight because a populated environment would fail loudly. No evidence supports labeling every earlier failure as a Claude implementation fault: weak helper-level oracles and missing real-pipeline coverage materially contributed, while the 300-second test ceiling is an environmental constraint recorded below.

## Test execution

The initial combined test command hit the hard 300-second timeout after 29 passing progress markers; no aggregate pass count is claimed. Per the one permitted split, the remaining Netherlands slice passed 17/17. Oregon plus selection passed 38/38; authority/knowledge runtime tests passed 34/34; the new deterministic audit harness passed 21/21. One timed-out command is reported, not hidden or rerun.

## Gate

- Global delta wiring accepted: **NO**
- Global delta optimizer accepted: **NO**
- Safe for AG/Codex reconciliation: **NO**
- Remaining P0/P1 rows: **53**

The next step is one bounded implementation pass driven only by `CODEX_305_PROGRAM_REMAINING_ITEMS.csv`: reconcile the final manifest with live authority veto/identity/runtime state, add the missing BC DAVE and Ohio bindings or correct their accepted dispositions, and supply real persisted-pipeline oracles for every intended priceable delta program. Do not reopen jurisdiction research.
