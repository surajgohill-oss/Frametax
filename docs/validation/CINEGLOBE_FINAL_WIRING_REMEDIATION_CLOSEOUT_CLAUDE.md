# CineGlobe Final Wiring Remediation — Claude Closeout

**Controlling document:** `docs/validation/CINEGLOBE_FINAL_WIRING_REMEDIATION_CLAUDE_PROMPT.md`
**Controlling commit:** `ea5fc9a2587f6e5659005e04ce437dcd8f98533c`
**Audited target commit:** `67fbc30d9e006663ec739256424dace303d16605`
**Status:** `IMPLEMENTED_PENDING_CODEX_ACCEPTANCE`

Startup/lineage: local and remote tips were both exactly `ea5fc9a2587f6e5659005e04ce437dcd8f98533c` at start. The shared worktree contained pre-existing modified/untracked probe files of unknown ownership (`tests/test_canonical_economics_integrity_repair.py`'s appended `test_print_projects`, `test_four_projects*.py`, `tests/test_four_projects_print.py`, `test_conditional.py`) — none were modified, staged, deleted, or committed; all are preserved exactly as found.

## Four-row matrix

| Row | Disposition | Files/functions | Independent expected vs observed |
|---|---|---|---|
| P0-SEL-ALT-001 | **IMPLEMENTED** | `canonical_evaluation.py`: `_relocation_completeness()`, per-tier `_component_qual_state` aggregation; `canonical_production_view.py`: `_is_conditional_eligible()`, `_blocking_requirements()` | 10/10 literal predicate cases pass (was 7/10); real FVD leading conditional `qualification_state` = `USER_FACT_REQUIRED` (was `None`) |
| P0-NL-001 | **IMPLEMENTED** | `models/project.py`: `production_company_identifier`; `canonical_evaluation.py`: `_company_period_prior_award_facts()`; `program_rate_rules.py`/`allocation_pricing.py`: identity-known gate | Two real, separately-persisted Project rows, same company/year: Project A prices USD3,421,571.87 alone; Project B (evaluated after) prices USD0.00 (was: both independently priced USD1,140,523.96) |
| P0-ZA-001 | **IMPLEMENTED** | `program_rate_rules.py`: `RateCondition.component_basis_line_components`; `allocation_pricing.py`: traced-line-subtotal bound | Codex's exact reproducer (USD1m production-only alloc, USD400k QSAPPE claim, 0 traced post/VFX lines) now rejects (was: executable, USD100,000) |
| P0-OR-001 | **IMPLEMENTED** | `authority_coverage_registry.py`: veto lifted; `program_rate_rules_worldwide.py`: `US_OR_DOCTRINE` real gates + uplift; `program_rate_rules.py`: `IncentiveValueCapRule` for `us_or_opif` | Was: entirely fail-closed (`UNPRICEABLE_AUTHORITY_INSUFFICIENT`). Now: 20%/25% split-basis prices literally, x1.10 multiplicative uplift confirmed, USD10,600,000 fund cap boundary confirmed, provisional until `us-or-award-contract-fund-confirmed` is evidenced |

## P0-SEL-ALT-001 — selection

**Root cause (`67fbc30`):** `_is_conditional_eligible()` admitted any fully-priced, non-baseline, non-comparable candidate whose `role_qualification.state` was `None`/`QUALIFIES`/`NOT_APPLICABLE`/curable, without checking WHY it was non-comparable, without aggregating component/stack participant qualification, and disclosing only one blanket jurisdiction fact.

**Fix:**
- `canonical_evaluation._relocation_completeness(is_baseline, code, inputs)` — PER-DIMENSION completeness (`travel`, `fx`, `local_cost`, `inkind`), each gated by its own `relocation_{dim}_evidenced__{code}` / `relocation_{dim}_not_applicable__{code}` evidenced fact. Applied at the single-program `STATUS_PRICED` branch and the `component_relocation` branch (bound to the TARGET jurisdiction, not the anchor — fixing the exact "only `relocation_completeness_evidenced__GR`, never the routed-to `RO`" defect). The multi-program stack branch keeps its structural `_STACK_NORMALIZATION_NOT_COMPUTED` sentinel (never a curable dimension — its `risk_adjusted_net_cost_usd` is still genuinely un-normalized).
- `component_relocation` structures now carry a real, worst-of-participants `role_qualification` (`_component_qual_state`, mirroring the existing stack `_combo_qual_state` pattern) instead of `None`.
- `canonical_production_view._is_conditional_eligible()` rewritten: baseline excluded; comparable rows use the original curable-state rule; non-comparable rows require `state is not None`, `state` in the admitted set, AND every entry in `relocation_missing_dimensions` to be an approved curable dimension name (never the stack sentinel, never an empty/unknown cause).
- `_blocking_requirements()` now discloses every real missing dimension by name, against the correct jurisdiction.

**Independent tests:** `tests/test_final_wiring_selection_predicate.py` — 10 literal predicate cases (baseline excluded; curable comparable admitted; non-comparable `None` excluded; non-comparable `QUALIFIES`/`NOT_APPLICABLE` excluded-unless-complete-curable-cause / admitted-with-cause; hard-fail excluded; multi-dimension full set; component/treaty one-hard-failing-participant excluded; stack sentinel never curable; mixed curable+structural cause excluded), `_relocation_completeness()` unit cases (baseline trivially complete; no facts → all four dimensions missing; partial evidence → exact remaining set; all evidenced/N-A → complete; wrong-jurisdiction evidence never counts), and real LU/FVD/Bad Hombres/Lips Like Sugar assertions. Pre-existing `tests/test_leading_conditional_recommendation.py` (previously 2/11 failing against `67fbc30`) now passes 11/11 unmodified — it already encoded the correct expected values (`USER_FACT_REQUIRED`, non-`None`) this fix produces.

## P0-NL-001 — Netherlands

**Root cause:** `ProjectEconomicInputs` carried no canonical company identity or award period; two independent `price_segment()` calls sharing a caller-supplied `prior_awards_eur` scalar both priced identically (USD1,140,523.96 each) — not a real cross-project ledger.

**Fix:**
- Migration `0072_project_production_company_identifier`: additive, nullable `projects.production_company_identifier` (a producer-supplied stable string identity — never the project's own title/id, never inferred). `target_shoot_year` (pre-existing column) is reused as the award period.
- `canonical_project_economics.ProjectEconomicInputs` gains `production_company_identifier`/`award_period_year`, read directly from the `Project` row.
- `IncentiveValueCapRule` gains `company_period_identity_known_fact_key` (evidenced ONLY by `evaluate_project()`, from the real Project columns — no caller can set it directly) alongside the existing `company_period_has_other_productions_fact_key`.
- `canonical_evaluation._company_period_prior_award_facts()`: a REAL cross-project database query — every other Project row sharing the exact same identifier+year (self excluded) is queried; each sibling's own persisted USD incentive for the same program is converted back to the cap's native currency via THIS evaluation's own canonical FX context and summed. Computed once in `evaluate_project()` and unioned into `evidenced_program_facts`/`amount_facts` **before** the fingerprint is computed; `current_generation_fingerprint()` (the read-only reconstruction) performs the identical union, or the two would diverge (confirmed and fixed — this produced a real infinite-recursion bug on first implementation, resolved by keying sibling lookups off `current_result_fingerprint`, a non-recursive newest-row read, never the recursive `current_generation_fingerprint`).
- `allocation_pricing._resolve_incentive_dollar_cap()`: unknown company/period (identity fact absent) fails the segment closed with an explicit unresolved detail — never an affirmative full cap.

**Independent tests:** `tests/test_final_wiring_nl_company_period_conservation.py` — creates real, separately-persisted `Project` rows (through the ordinary generic ingestion path, `Organization → Project → Document/DocumentVersion → material_routing`, the same pattern `test_generic_future_project_propagation.py` established) with real `production_company_identifier`/`target_shoot_year` values, evaluates each with the real `evaluate_project()`. Same-company-same-year: Project A (no siblings yet) prices USD3,421,571.87; Project B (evaluated after) correctly reads A's real persisted award and prices USD0.00 (jointly ≤ the cap). Different-company-same-year: fully isolated, both price the full cap. Unknown identity: `is_fully_priced=False`. Plus a pure, DB-free resolver-level adverse test (wrong/missing identity, unresolved aggregate).

## P0-ZA-001 — South Africa

**Root cause:** the shared component-basis conservation check bounded the claimed QSAPPE only by the segment's own broad `qpe_usd` (any component), not by the exact classified post/VFX line subtotal — Codex's exact reproducer (a `component="production"` allocation with a claimed `za_nfvf_post_qsappe_usd` inside its own broad QPE) still wrongly priced.

**Fix:**
- `RateCondition.component_basis_line_components: tuple[str, ...] | None` — names which `AccountAllocation.component` values form the traced subtotal. Set to `("post", "vfx")` on ZA's `za-nfvf-post-qsappe-basis` condition; `None` (unchanged) for `us_or_opif`'s payroll/other split, which keeps the prior, coarser `qpe_usd` bound (out of this row's scope).
- `RateResolution.qpe_basis_line_components` carries this through `resolve_program_rate()`.
- `allocation_pricing.price_segment()`: when set, sums this segment's own real `AccountAllocation` lines whose `component` is in the tuple (deduplicated by `line_id`; duplicates reject outright), and bounds the claimed/derived basis by that EXACT traced subtotal, never the broad segment QPE.

**Independent tests:** extended `tests/test_final_formulaic_full_pipeline_consumption.py::test_za_nfvf_rebate_cap_applies_to_calculated_incentive_and_post_only_branch` — Codex's exact adverse reproducer now rejects; a real traced post line matching the claim prices 25% of it; post+vfx lines combine; one cent above the traced subtotal rejects; duplicate `line_id`s reject; the `$1`/`$1,000,000` conservation case and negative/NaN/±infinity cases still reject; the general (non-post-only) branch is unaffected (still prices `min(qpe*.25, cap)`).

## P0-OR-001 — Oregon

**Root cause:** current official ORS 284.368 / OAR Chapter 951 Division 2 / Oregon Film OPIF page sources (independently re-verified via direct fetch during this pass) resolve rate bases, minimum spend, fund/project cap, and regional uplift, but the coverage registry still carried a blanket `UNPRICEABLE_AUTHORITY_INSUFFICIENT` veto (both `us_or_opif` and its canonical alias `or_opif`).

**Fix (disposition B — conditional formula opportunity, never unconditional entitlement):**
- `authority_coverage_registry.py`: both rows removed from `COVERAGE_REGISTRY`'s blocking set.
- `program_rate_rules_worldwide.US_OR_DOCTRINE`: the prior disclosure-only `discretionary_band` condition is replaced with two REAL `project_fact_dependent_eligibility` gates — `us-or-award-contract-fund-confirmed` (bundles application-before-production, agency discretion, contract execution, fund availability, and confirmation that submitted QPE figures already respect the USD1,000,000 per-individual/company exclusion) and `us-or-fund-amount-current` — each with `gates_tier_eligibility=False` (so the tier still prices provisionally rather than blocking outright) but IS one of `canonical_evaluation._RATE_CONDITION_ELIGIBILITY_KINDS`, so an unresolved instance downgrades `qualification_state` to `USER_FACT_REQUIRED`, excluded from `_qualification_admits_recommended`/rank-1 via the existing, unmodified mechanism.
- A new, generic `RateCondition.regional_uplift_multiplier_fact_key`/`regional_uplift_multiplier` + `RateResolution.incentive_uplift_multiplier`, applied in `allocation_pricing.price_segment()` AFTER the base rate×basis calculation and BEFORE the final dollar cap — Oregon's `us-or-regional-uplift` condition sets `regional_uplift_multiplier=1.10` (confirmed multiplicative — ORS 284.368's exact text, "10 percent OF THE AMOUNT otherwise allowable" — never additive).
- `IncentiveValueCapRule["us_or_opif"]`: USD10,600,000 (50% of the current, independently-verified USD21,200,000 annual fund), applied unconditionally like every other program's cap — a real, dated, sourced figure, never an invented "unlimited" default.
- Payroll (20%) and other-expense (25%) bases remain genuinely separate `is_component_basis` tiers (unchanged architecture); a **pre-existing, out-of-scope** characteristic of `resolve_program_rate()` selects one winning tier per call rather than summing both simultaneously — each base independently prices its own literal arithmetic correctly; this row's required corrections (veto lift, uplift, cap/QPE-exclusion separation) do not depend on combining them, and combining is not one of Codex's named required corrections for this row.

**Independent tests:** `tests/test_final_wiring_oregon_conditional_formula.py` — veto lifted (both spellings); literal split-basis arithmetic (20%×2M=400,000; 25%×2M=500,000); below/at the USD1,000,000 threshold; multiplicative uplift (500,000×1.10=550,000, proven distinct from the wrong additive 35%×2,000,000 figure); 50%-fund boundary (USD10,600,000, confirmed un-clipped just below it); missing-facts rejects; a DB-backed real-pipeline check that an unconfirmed Oregon candidate's `role_qualification.state` is never `None`/`QUALIFIES`/`NOT_APPLICABLE` and never reaches rank 1 (skips honestly — no real anchor project currently has Oregon-specific `us_or_payroll_qpe_usd`/`us_or_other_qpe_usd` facts evidenced, since this is a brand-new fact-key convention no caller has adopted yet); FVD's own Greece baseline confirmed byte-identical after lifting the veto. `tests/test_final_formulaic_full_pipeline_consumption.py::test_us_or_opif_conditional_formula_opportunity_lifted_veto` and `tests/test_b3_formulaic_consumption.py::test_us_or_opif_no_blended_surrogate_disclosed_component_ceilings` (both previously asserted "correctly stays blocked" — rewritten to assert the new, correct lifted disposition). `tests/optimization/test_global_data_application_runtime.py::test_price_segment_hard_blocks_a_covered_program_even_when_directly_specified` re-fixtured onto `kz_investment_subsidy` (the one remaining program that is both genuinely `UNPRICEABLE_AUTHORITY_INSUFFICIENT` and holds real `RateRule` data, confirmed via a live registry scan) since Oregon can no longer prove that generic invariant.

## Shared correctness requirements — confirmed

- Generic shared paths only: no project title/ID exceptions; `component_basis_line_components`/`regional_uplift_multiplier`/`cap_requires_evidence_fact_key` are all generic `RateCondition`/`IncentiveValueCapRule` fields usable by any program, not ZA/OR-specific branches.
- New calculation-driving fields in the fingerprint: `production_company_identifier`/`award_period_year` added explicitly to `_compute_fingerprint()`'s payload (on top of already being implicitly covered via `evidenced_program_facts`/`amount_facts`); `current_generation_fingerprint()` performs the identical company-period union `evaluate_project()` does (fixed a real divergence/recursion bug during implementation — see P0-NL-001 above).
- FX immutability/finiteness and Texas exact-award behavior: unchanged, re-verified via `tests/test_canonical_fx_context.py` (regression, all passing).
- All other 586 manifest identities and the original 12-row denominator: unchanged; no new canonical program identity was added, removed, or reclassified.
- Preserved exact controls (all reconfirmed by direct recomputation below): Bad Hombres `us_nm_film_credit` USD596,910.25/USD1,885,112.75; Lips Like Sugar `ca_film_30` USD3,459,278.90/USD8,524,375.10; LU Mauritius anchor USD573,059.70/USD3,791,333.30; FVD Greece anchor USD1,445,659.84/USD3,072,027.16.

## Four-project runtime (serial, all four)

| Project | Fingerprint (first 16) | Candidates (total/priced) | Anchor result | Leading conditional |
|---|---|---:|---|---|
| Little Utopia | `6b9a0acd0594ae51…` | 241 / 124 | `mu_edb_incentive`, USD573,059.70 / USD3,791,333.30; no verified winner | Manitoba `ca_mb_film_video_credit`, `RULE_DATA_INCOMPLETE` (was `None`-adjacent blanket disclosure) |
| F#K Valentine's Day | `61c454216aaaf9f0…` | 292 / 159 | `gr_cash_rebate`, USD1,445,659.84 / USD3,072,027.16; no verified winner | Greece+Romania component, `USER_FACT_REQUIRED` (was `None` — the exact defect this pass fixes) |
| Bad Hombres | `6c414686ff4945c5…` | 238 / 122 | `us_nm_film_credit`, USD596,910.25 / USD1,885,112.75; **rank 1** | None (verified winner suppresses it, unchanged) |
| Lips Like Sugar | `abf70bd0fdf125bb…` | 294 / 175 | `ca_film_30`, USD3,459,278.90 / USD8,524,375.10; **rank 1** | None (verified winner suppresses it, unchanged) |

All four anchor economics are byte-identical to the controlling prompt's required exact controls. Candidate counts are unchanged from the prior audit (the repair changes presentation/selection and NL/ZA/OR economics, not candidate construction).

## Focused verification

- Grouped suite (canonical FX/fingerprint, final formulaic full-pipeline/B3 for NL/TX/ZA/Oregon, leading-conditional/canonical-selection consistency, treaty/opportunity/served-wiring/qualification/coproduction/component-relocation/national-cultural-status, economics-integrity/generic-future-project, global-data-application-runtime, worldwide-qualification-completion, program-intelligence-population, prompt16-authority-disposition, and every new independent oracle for all four rows): **682 passed, 1 skipped (honest — no real project fixture currently supplies Oregon's brand-new component-basis facts), 0 failed, 107.18s.**
- No full backend suite was run.
- No command, test file, or project recomputation exceeded its budgeted hard timeout; none were left running.

## Timeouts / incomplete items

None. All four rows have production-path repairs, real independent tests, and pass. The one pre-existing, out-of-scope characteristic (Oregon's payroll/other bases are selected as alternatives rather than additively combined by `resolve_program_rate()`'s single-winning-tier architecture) is documented above, is not one of this row's required corrections, and does not block any of the required literal test cases (each base's own arithmetic is independently exact).

## Diff scope

Task-owned implementation, one migration, focused tests, and this closeout artifact only:

- `frametax2/backend/app/calculators/allocation_pricing.py`
- `frametax2/backend/app/data/authority_coverage_registry.py`
- `frametax2/backend/app/data/program_rate_rules.py`
- `frametax2/backend/app/data/program_rate_rules_worldwide.py`
- `frametax2/backend/app/models/project.py`
- `frametax2/backend/app/services/canonical_evaluation.py`
- `frametax2/backend/app/services/canonical_production_view.py`
- `frametax2/backend/app/services/canonical_project_economics.py`
- `frametax2/backend/alembic/versions/0072_project_production_company_identifier.py` (new)
- `frametax2/backend/tests/optimization/test_global_data_application_runtime.py`
- `frametax2/backend/tests/test_b3_formulaic_consumption.py`
- `frametax2/backend/tests/test_copro_qualification_wiring.py`
- `frametax2/backend/tests/test_final_formulaic_full_pipeline_consumption.py`
- `frametax2/backend/tests/test_final_wiring_nl_company_period_conservation.py` (new)
- `frametax2/backend/tests/test_final_wiring_oregon_conditional_formula.py` (new)
- `frametax2/backend/tests/test_final_wiring_selection_predicate.py` (new)

No frozen exclusion changed: no new jurisdiction research, no unrelated program add/remove/reclassify, no MFNI/reinvestment/frontend/globe/UI/Script Analyzer/ingestion change, no parallel pricing/FX/eligibility/ranking path, no full backend suite run, no merge, no force-push. Pre-existing unrelated tracked/untracked work (`tests/test_canonical_economics_integrity_repair.py`'s appended debug test, `test_four_projects*.py`, `tests/test_four_projects_print.py`, `test_conditional.py`) is preserved untouched and excluded from this commit.
