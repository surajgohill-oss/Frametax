# Codex D743 Combined Delta Acceptance

## Decision

**STATUS: REMEDIATION_REQUIRED.** The bounded delta is not accepted for Claude integration because `P0-COMB-001` remains functionally incorrect. `P1-TRACE-001` does not provide exact unique allocated spend, and the 500-row acceptance helper is not evaluation-scoped. V-BRAT also lacks an independent application production record, so the required four-production acceptance corpus cannot be completed.

This decision covers exactly `3b5c3f5ea7c16358b8fe9ed64f0f5f2181d05ae5...d743fab55622f82fca24f27635344b83c3642900`, using `cdaf1968fe38e64af873ac9c4c6da53d03687446` as the audit contract. No external research or production modification was performed.

## Repository and isolation proof

- Canonical remote: `https://github.com/surajgohill-oss/Frametax.git`.
- Claude head: exact `d743fab55622f82fca24f27635344b83c3642900`; parent exact `0c97a6a692bcfb5d1344bd1c2f1ffc3db112cae2`; baseline `3b5c3f5...` is an ancestor.
- Audit worktree/branch: clean dedicated worktree at `/Users/Suraj/cineglobe-codex-d743-acceptance`, branch `codex/d743-combined-delta-acceptance-20260915`.
- Before worktree: detached exact `0c97a6a...` at `/Users/Suraj/cineglobe-codex-d743-before`.
- Both sides were restored from the same 537 MB `pg_dump` snapshot of `frametax2` into separate temporary databases. Each contained 59 projects. Current-engine result rows for each target project were deleted before calling the real `evaluate_project`; all six calls returned `EVALUATION_COMPLETE`, never `EVALUATION_REUSED`.

## Acceptance matrix

| Finding | Result | Evidence class | Conclusion |
|---|---|---|---|
| P0-CAND-001 | ACCEPT | RUNTIME_VERIFIED | All bilateral opportunities are enumerated before presentation limits. |
| P0-CAND-002 | ACCEPT | STATIC_VERIFIED | Full multilateral participants reach evaluation; only presentation is limited. |
| P0-CAND-003 | ACCEPT | RUNTIME_VERIFIED | Conditional treaty identities persist without priced legs. |
| P0-QUAL-001 | ACCEPT | STATIC_VERIFIED | Treaty facts are scoped by treaty slug and ordered participant identities. |
| P0-STACK-001 | ACCEPT | RUNTIME_VERIFIED | Unknown stackability yields null economics and cannot rank. |
| P0-COMB-001 | **REJECT** | RUNTIME_VERIFIED | The helper does not allocate any spend to its treaty partner and no real fresh project generated a hybrid. |
| P1-CLASS-001 | ACCEPT | RUNTIME_VERIFIED | Every served structure has one exclusive backend classification. |
| P1-TRACE-001 | **REJECT** | STATIC_VERIFIED | `max(per_program_qpe)` is a lower bound, not exact unique allocated spend. |

P0 accepted/rejected: **5 / 1**. P1 accepted/rejected: **1 / 1**, plus one rejected P1 test-oracle repair (`P1-TEST-500`).

## P0-COMB-001: first failing behavior

`_price_combined_coproduction_component_candidate` constructs three participants and three claimed programs, but supplies only `component_routes`; `ownership_shares` and `account_splits` remain empty (`canonical_evaluation.py:1641-1660`). The allocator consequently routes the selected movable component to the third jurisdiction and defaults every other account to the primary jurisdiction (`production_allocation.py:250-269, 332-430`). Nothing assigns spend to the treaty partner.

An independent synthetic probe used $2.0M cast plus $1.0M VFX and called the production helper for MU + GB with VFX routed to CA-BC. The exact allocation was:

| Participant | Allocated USD |
|---|---:|
| MU (primary) | 2,000,000 |
| GB (treaty partner) | 0 |
| CA-BC (component target) | 1,000,000 |

The total conserves $3.0M, but conservation alone does not make this a co-production. Moreover, generation attempts only the highest-spend movable component and first best remaining target (`canonical_evaluation.py:4422-4445`), and post-pricing stacking is attempted on the anchor side only (`canonical_evaluation.py:4500-4512`). Claude's helper test uses noncanonical component string `post_vfx`; the canonical movable set is `post`, `vfx`, `music`, so that test does not actually exercise component routing and asserts only conservation.

No `hybrid` structure appeared in any of the three fresh runtime populations. The new path is gated on already-`ELIGIBLE` treaty facts; the three real projects have none. Thus the real served runtime does not provide a positive end-to-end proof.

## P1-TRACE-001: mislabeled lower bound

The delta correctly adds `total_claim_bases_usd = sum(per_program_qpe)`. It then assigns `total_qualifying_spend_usd = max(per_program_qpe)` (`canonical_evaluation.py:3786-3819`) and describes that value as a conservative lower bound because line-level union data is unavailable. For overlapping-but-not-identical or disjoint program bases, the union of unique underlying spend may exceed the maximum single base. The field therefore is not exact unique allocated spend as required. The associated test derives the same `max` expression and only proves `max <= sum`; it has no independent line-level union oracle.

## Fresh structure delta

The exact row-level summary is in `CODEX_D743_STRUCTURE_DELTA.csv`.

| Production | Before → after | Priced | Conditional | Rejected | Net semantic change | Baseline economics |
|---|---:|---:|---:|---:|---:|---|
| The Little Utopia | 243 → 259 | 125 → 125 | 30 → 46 | 88 → 88 | +16 treaty | Exact unchanged |
| F#K Valentine's Day | 295 → 312 | 160 → 160 | 31 → 48 | 104 → 104 | +17 treaty | Exact unchanged |
| Underwater | 300 → 316 | 187 → 187 | 30 → 46 | 83 → 83 | +16 treaty | No baseline on either side |

Here `conditional` is `CO_PRO_OPPORTUNITY + FEASIBILITY_REVIEW_REQUIRED`; `rejected` is `RULE_REJECTED + UNPRICEABLE_AUTHORITY_INSUFFICIENT`. The delta introduced no priced candidate and no hybrid candidate in these runs. Every new bilateral identity is a conditional opportunity with null economics, so none can rank.

There was no verified winner or runner-up on either side for any of the three productions. The leading conditional remained exact:

- LU: Full relocation to Manitoba, estimated incentive $1,824,388.20, NPC $3,269,304.80.
- FVD: Greece anchor with post routed to Romania, estimated incentive $1,465,850.60, NPC $3,062,526.40.
- Underwater: Full relocation to Manitoba, estimated incentive $2,810,700.45, NPC $5,187,333.55.

Protected baseline economics remained exact:

- LU `mu_edb_incentive`: incentive $573,059.70; NPC $3,791,333.30.
- FVD `gr_cash_rebate`: incentive $1,445,659.84; NPC $3,072,027.16.

## Special gates

### V-BRAT — `BLOCKED_NOT_PRESENT_IN_APPLICATION`

No independent V-BRAT project or alias exists among the 59 project records. A versioned file does exist: `V-BRAT_V8_Greece_041224 TOPSHEET.pdf`, active/current with checksum and document-version lineage, but it is the budget document attached to F#K Valentine's Day and its source path is under the FVD corpus. It is not a distinct V-BRAT production record. The audit did not create or substitute a project, so separate V-BRAT evaluation remains blocked.

### Underwater baseline — explained, invalid as acceptance case

Underwater's home jurisdiction is the bare national code `US`. The candidate library's executable US programs are state-specific; no priced candidate uses exact code `US`. The evaluator marks a baseline only when a candidate matches the project's exact home jurisdiction. Consequently both versions produced zero `single_country` structures, no `is_baseline=True` row, no canonical winner, and no runner-up. The result is internally explainable, but without a current-anchor baseline it cannot validate winner/economic preservation.

### 500-row helper — rejected

`tests/test_codex_final_optimizer_health_audit.py::_current_rows` selects all historical results for a project, orders by creation time, and applies `.limit(500)` without scoping to engine version, fingerprint, or evaluation/run identity. The fresh result generations in this audit were 259, 312, and 316 rows, so the limit did not hide any of these three generations. It can nevertheless truncate a future current generation above 500 and cannot prove generation completeness. This fails the explicit acceptance requirement for run/evaluation-scoped retrieval.

The health-audit file itself completed in 7.97 seconds with **4 passed / 5 failed**. The five failures cascade from a shared asyncpg connection being attached to a different event loop / operation already in progress. Those are concrete test-harness defects, not evidence of optimizer-value regressions.

### `ca_bc_pstc` failures — pre-existing confirmed

The same two tests fail at both exact `0c97a6a` and exact `d743fab`:

- `test_canonical_stack_bridge.py::test_price_program_pair_stack_mutually_exclusive_zeroes_lower_value` returns `None`.
- `test_copro_conditional_pricing_bridge.py::test_conditional_scenario_routes_same_jurisdiction_multi_slug_through_stack_engine` reports `ca_bc_pstc` in canonical data gaps.

This is confirmed pre-existing behavior, not a d743 regression. It remains a separate unresolved test/data-contract issue.

### Performance

All six fresh evaluations completed without a timeout. Per-project evaluator time ranged from 1.405 to 9.443 seconds after candidate caps were removed. Complete candidate enumeration was therefore performant for the bounded real corpus.

## Earlier `0c97a6a` cleanup

**Accepted for this bounded contract**, with the already-disclosed Nevada limitations preserved:

- Bulgaria: authority-provenance unresolved candidates retain visible economics but are downgraded out of Recommended.
- BC DAVE: 16% is bound to exact traced eligible-labor categories and an eligible-activity fact; the four focused tests passed.
- Ohio: exactly one current display-only, authority-locked identity; no executable duplicate.
- Nevada: the $6M incentive cap is implemented and its four focused tests passed. The $750k per-person limit, 60% spend ratio, and 12% nonresident-ATL basis remain explicitly unimplemented/disclosed; this audit does not upgrade them.
- Czech: feature and animation rows remain mutually exclusive by production type and reconcile to one statutory program for identity/counting, without simultaneous double pricing.

The focused Claude remediation/cleanup suite completed **40 passed**. The two `ca_bc_pstc` failures above were separately reproduced on both commits and are not attributed to this delta.

## Required remediation

1. Build the combined topology from scoped, evidenced treaty contributions so every treaty party receives a valid nonzero allocation and contribution gates are enforced; route only canonical components and prove one real served hybrid end to end.
2. Enumerate viable component targets and authorized same-jurisdiction stacks without the current one-component/one-target/anchor-only semantic truncation, while retaining fail-closed pricing.
3. Compute exact unique allocated spend from line identities, or rename the `max` value as a lower bound; test overlapping and disjoint bases against independent expected unions.
4. Replace `_current_rows().limit(500)` with exact evaluation-generation retrieval and repair async engine/session loop isolation.

Until item 1 passes, this delta has an unresolved P0 and must not be integrated as complete.
