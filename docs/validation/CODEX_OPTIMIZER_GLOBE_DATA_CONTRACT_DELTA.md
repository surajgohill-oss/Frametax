# Codex Optimizer Globe Data Contract Delta

**Audit date:** 2026-09-20

**Audited SHA:** `08060f99e7c0faa036bd5ad3fb9e13ec75f885a3`

**Branch:** `claude/global-optimizer-remediation`

**Engine:** `canonical-1.91.0`

**Database:** `frametax2_claude_optimizer_acceptance_20260919` (read-only)

**Status:** `GLOBE_DATA_CONTRACT_NOT_ACCEPTED`

## Delta decision

The bounded current-generation contract is fresh, exactly accounted, numerically reconstructable, selection-consistent, disposition-complete, and free of legacy calculation lineage. It is not yet truthful enough for Optimizer Globe wiring because the canonical production view drops routed hybrid participants and assigns those same multi-jurisdiction structures the classification `SINGLE_JURISDICTION`. In addition, combined co-production and multilateral subfamilies are persisted under the broad type `hybrid`, while retention and the served `top_by_structure_type` block have no structural-family-specific lane. A Globe consumer therefore cannot reliably distinguish or select every required family from the served contract.

No evaluator was called. All runtime evidence came from existing `canonical-1.91.0` generations through read-only transactions and the existing view builders.

## Six-item matrix

| ID | Area | Result | Delta evidence |
|---|---|---|---|
| GD-1 | Freshness | **PASS** | Both `build_production_and_structures()` and `build_project_workspace_view()` returned `canonical-1.91.0` and the exact current fingerprint for all four projects. Their queries require both engine and fingerprint. Historical rows may remain for provenance but are outside the served predicates. |
| GD-2 | Canonical family/type | **FAIL** | Current retained rows have non-null persisted `structure_type`, but every ordinary component hybrid is classified `SINGLE_JURISDICTION`. Combined pair, combined multi-component, and combined multilateral candidates are also persisted as broad type `hybrid`; `_structure_classification()` recognizes only `combined_coproduction_component_stack`, not the other combined family values. |
| GD-3 | Participants and routed economics | **FAIL** | Component routes, line IDs, programs, and allocated dollars are complete and disjoint in trace, but `_empty_structure_entry()` adds routed claiming jurisdictions to `participants` only for `component_relocation`, not for `hybrid`. All four productions therefore serve sampled three-jurisdiction ordinary hybrids with only their CA-MB anchor in `participants`. |
| GD-4 | Canonical selection | **FAIL** | Baseline, canonical selection, workspace top result, best-per-jurisdiction, and retained top-per-`structure_type` agree. Proof incumbents are retained and aggregate dominators are valid. However, retention/top blocks are keyed by broad `structure_type`; no top lane/block exists for `structural_family`, so a combined or multilateral family sharing `hybrid` is not guaranteed a retained family winner. |
| GD-5 | Dispositions | **PASS** | Retained rows plus aggregate counts equal generated totals exactly for all four projects. `PRICED`, `DOMINATED_WITH_PROOF`, `CO_PRO_OPPORTUNITY`, `FEASIBILITY_REVIEW_REQUIRED`, `UNPRICEABLE_AUTHORITY_INSUFFICIENT`, qualification failures, and `RULE_REJECTED` remain separate statuses. |
| GD-6 | Lineage purity | **PASS** | Globe-facing generic state is built from canonical production/evaluation views backed by `production_structures`, `structure_calculation_results`, `evaluation_generation_summaries`, and `evaluation_candidate_aggregates`. The legacy calculation route remains HTTP 410. No demo, alternate calculator, stale engine, or `project_evaluation` row feeds these builders. |

## Four-production evidence

| Production | Current fingerprint | Generated = retained + aggregated | Canonical selection | Globe-contract defect observed |
|---|---|---:|---|---|
| The Little Utopia | `43bb90d67f49c44fbed8025d458c9072340ce0f3acea5bd724616c6ceb823285` | `7,531 = 386 + 7,145` | No verified winner; leading conditional `39153e8e-a905-42c7-9ebc-af237cdc92f9`; workspace top is null | Hybrid `3c8c3dd3-b289-4972-b3c5-d832b7d70c7c` routes CA-MB principal + CA-NL post + IT VFX, but serves `participants=["CA-MB"]` and `classification="SINGLE_JURISDICTION"`. |
| Bad Hombres | `9e9b597c35cb617da107372c0c037b4d6e2207c1ea7ed6907ea6f7a57fcad652` | `7,545 = 482 + 7,063` | `f17a2be4-74e0-406a-9573-093ec0adee55`; workspace agrees | Hybrid `203023ac-42b8-4361-9a77-898edbefd2a7` routes CA-MB principal + CA-NL music + IT post, but serves only CA-MB and `SINGLE_JURISDICTION`. |
| F#K Valentine's Day | `59de46becc1d9ad67b2a0595413a5468aed7bcde6bb940bce1e6ded9f6d020a4` | `526,155 = 864 + 525,291` | No verified winner; leading conditional `ccdd1cd2-6cb5-427a-bfeb-af04a820e9b3`; workspace top is null | Hybrid `e134844f-71a9-43c9-b1ea-5136654c24fc` routes CA-MB principal + CA-NL music + IT VFX, but serves only CA-MB and `SINGLE_JURISDICTION`. |
| Lips Like Sugar | `a38435fe3f73d09b0441e81573af56789100e98297ccaa2b7e9ecd2941a9edd6` | `707,128 = 992 + 706,136` | `a8ee3536-df16-4a9d-baa0-a2d81f1a567d`; workspace agrees | Hybrid `987e9417-b0a8-43c8-adc7-9bf16491ee35` routes CA-MB principal + CA-NL music + IT VFX, but serves only CA-MB and `SINGLE_JURISDICTION`. |

The stored baseline amounts remain unchanged and were compared, not recalculated: Little Utopia `$573,059.70 / $3,791,333.30`, Bad Hombres `$596,910.25 / $1,885,112.75`, F#K Valentine's Day `$1,445,659.84 / $3,072,027.16`, and Lips Like Sugar `$3,459,278.90 / $8,524,375.10` (incentive / NPC).

## Family/type mapping delta

| Required Globe distinction | Current contract | Result |
|---|---|---|
| Full relocation / anchor | `full_relocation` / `single_country` | PASS |
| Local stack | `multi_program`, `same_jurisdiction_distinct_cost_pool_stack`, `same_jurisdiction_group_stack` | PASS |
| Component relocation | `component_relocation`, classified `HYBRID_ANCHOR_COMPONENT` | PASS |
| Ordinary component hybrid | `structure_type="hybrid"`, `structural_family="ordinary_component_hybrid"`, but classified `SINGLE_JURISDICTION` | **FAIL** |
| Official treaty co-production | `treaty_coproduction`, classified `OFFICIAL_COPRODUCTION`; treaty identity remains in trace | PASS |
| Combined co-production hybrid | Broad type `hybrid`; only exact discovery value `combined_coproduction_component_stack` maps to `COMBINED_COPRO_HYBRID_STACK`. Pair and multi-component variants do not. | **FAIL** |
| Multi-principal / multilateral | Broad type `hybrid`; `combined_coproduction_pair_stack` and `combined_multilateral_coproduction_stack` are not mapped to a dedicated canonical classification | **FAIL** |
| Conditional grant/fund opportunity | `conditional_programs` plus `relationship_types += ["conditional_fund"]`; remains zero-guaranteed | PASS |

The four real current generations exercise single, full relocation, local stack, component relocation, ordinary hybrid, and treaty-opportunity rows. They do not contain a fact-complete combined or multilateral priced row; the missing mappings above are established statically at the current persistence/view construction sites and must be corrected before those families can be wired generically to Globe.

## Routed-economics reconciliation

All retained priced ordinary hybrids were checked set-wise:

| Production | Retained priced hybrids | Maximum allocated-spend variance | Post-adjustment incentive mismatches | NPC mismatches | Cross-component line overlap |
|---|---:|---:|---:|---:|---:|
| The Little Utopia | 78 | `$2.00` documented source rounding | 0 | 0 | 0 |
| Bad Hombres | 173 | `$0.00` | 0 | 0 | 0 |
| F#K Valentine's Day | 308 | `$0.00` | 0 | 0 | 0 |
| Lips Like Sugar | 408 | `$0.00` | 0 | 0 | 0 |

The trace retains `component_allocations` with component, jurisdiction, program, allocated dollars, and source line IDs; `raw_component_incentives_usd`; `stacking_adjustments`; and `post_adjustment_component_incentives_usd`. Those fields reconstruct the retained result incentive and NPC. The defect is the served participant/classification projection, not the routed economic calculation.

## Disposition and retention accounting

| Production | Generated priced | Generated unpriced | Proof rows | Accounting result |
|---|---:|---:|---:|---|
| The Little Utopia | 258 | 7,273 | 78 | exact |
| Bad Hombres | 7,290 | 255 | 77 | exact |
| F#K Valentine's Day | 542 | 525,613 | 308 | exact |
| Lips Like Sugar | 705,466 | 1,662 | 312 | exact |

All retained result rows have a non-null `structure_type`; all retained `PRICED` rows have an `economic_identity`; and `budget - incentive = true NPC` for every retained priced row. Every aggregated priced group has a current retained dominating structure and no group has a minimum NPC below that dominator. Proof rows identify an incumbent generator identity, and the current retention contract keeps the referenced incumbent.

## Actionable defects

### GDC-001 — hybrid participants and classification are false at the served boundary

**Affected productions:** all four.

**Affected family:** `ordinary_component_hybrid`; the same projection logic also affects combined hybrid families.

Exact missing contract behavior:

1. `canonical_production_view._empty_structure_entry()` must derive `participants` from every claiming `component_allocations[].jurisdiction_code` for `structure_type="hybrid"`, not only from the anchor and `coproduction_partners`.
2. `_structure_classification()` must map `structural_family="ordinary_component_hybrid"` to `HYBRID_ANCHOR_COMPONENT`, not the default `SINGLE_JURISDICTION`.
3. Combined pair, component, multi-component, and multilateral family values must map explicitly to stable backend-owned classifications; the frontend must not infer them from labels.

### GDC-002 — bounded retention has no structural-family winner lane

**Affected productions:** latent for the four current projects because none has a fact-complete combined/multilateral priced row; immediately affects any project that does.

**Affected families:** `combined_coproduction_pair_stack`, `combined_coproduction_component_stack`, `combined_coproduction_multi_component_stack`, `combined_multilateral_coproduction_stack`, and any future distinct family persisted as broad `hybrid`.

Exact missing contract fields/behavior:

1. Retention must preserve the top candidate for each canonical structural family, not only each broad `structure_type`.
2. The served contract needs a `top_by_structural_family` block (or equivalent canonical-family block) with stable family identity, structure ID, economic identity, participants, routes, incentive, and NPC.
3. Aggregate groups already retain `structural_family`; their best identity/dominator metadata must be reconciled against the family winner so bounded persistence cannot erase the detailed row needed by Globe.

## Read-only execution record

- Repository, branch, SHA, upstream, clean worktree, engine, and database routing matched before any data query.
- Read the current handoff, capability ledger, retention/aggregation services, canonical production/workspace view builders, and evaluation paging routes first.
- Used bounded read-only transactions and existing view builders only.
- No `evaluate_project()` call, regeneration, cold run, benchmark, maintenance task, broad suite, authority research, or frontend/Globe execution occurred.
- No code, migration, test, frontend, project row, evaluation row, or database was modified.

**Terminal status: `GLOBE_DATA_CONTRACT_NOT_ACCEPTED`**
