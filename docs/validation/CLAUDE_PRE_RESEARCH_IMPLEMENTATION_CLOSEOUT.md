# CLAUDE_EXECUTABLE_PROGRAM_RECONCILIATION — Pre-Research Implementation Closeout

**Canonical branch:** `claude/optimizer-policy-finalization`
**Minimum required ancestor:** `bc5f19bc135b35c1304df5e60c703a8504b646df`
**Resolved starting SHA:** `bc5f19bc135b35c1304df5e60c703a8504b646df` (branch was already exactly at the minimum ancestor — no newer descendant existed)

## Objective

Reconcile the complete program population and prove that every program labeled executable is actually consumed and priced by the optimizer under qualifying facts, before AG research or Codex acceptance.

## Result: zero implementation defects found among the 126 executable programs

Every one of the 126 executable-labeled programs (a real registered `RateRule`) was run through an isolated qualifying canonical control (compatible production type, sufficient qualifying spend, cultural tests/producer-controlled requirements assumed satisfied). Outcome:

- **79 → `PRICED_RUNTIME_VERIFIED`** immediately under a generic qualifying budget.
- **8 more → `PRICED_RUNTIME_VERIFIED`** once their own specific, real, producer-controlled `evidenced_facts`/`amount_facts` were supplied (e.g. `us_or_opif` needs `us_or_opif_award_confirmed`/`us_or_opif_fund_amount_current_confirmed` plus payroll/other QPE amounts; `cz_film_incentive_animation` simply needed `production_type="animation"`, which the initial generic sweep hadn't tried). **No code changes were required** — every one of these 8 already resolves correctly through the existing `resolve_program_rate()` path; the initial "needs review" flag was a limitation of the generic sweep's fact vocabulary, not a defect in the pricing engine.
- **47 → `MISLABELED_NON_EXECUTABLE`**, each with a substantive, individually-reasoned justification (43 via `_B1_DISCRETIONARY_RULING`, 4 via `COVERAGE_REGISTRY`) — see `CLAUDE_47_EXECUTABLE_GAP_RECONCILIATION.csv` and `CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv`.

**No program remains merely blocked without a corrected disposition or a substantive reason.** No implementation defect was found requiring a code fix this pass (the 4 Canadian-program B1 misclassifications were already fixed in the prior workstream at this same branch, ancestor of this HEAD).

## The 47-record gap, resolved exactly

126 executable − 79 priced = 47. Breakdown (`CLAUDE_47_EXECUTABLE_GAP_RECONCILIATION.csv`):

- **43** blocked via `_B1_DISCRETIONARY_RULING` (of the 45 remaining B1 entries post-prior-workstream, 43 have a registered `RateRule` and therefore appear in the executable population; the other 2 — `ag-us-pr-puerto-rico-...`, `ca_sk_production_grant`, `th_boi_incentive` — have no rate rule at all and are correctly absent from the 126).
- **4** blocked purely via `COVERAGE_REGISTRY` (not B1): `ae_dxb_dpip` (SUPERSEDED), `jp_vipo_location_incentive` and `kr_kofic_location_incentive` (NON_GUARANTEED_SELECTIVE — confirmed genuinely selective/competitive award programs), `kz_investment_subsidy` (UNPRICEABLE_AUTHORITY_INSUFFICIENT — genuine evidence gap, included in the AG queue).

One identity-resolution nuance found and documented (not a defect): the executable slug `us_wa_motion_picture_competitiveness` alias-resolves to the canonical id `us_wa_mpcp`, which is the spelling registered in `_B1_DISCRETIONARY_RULING` — both a prior CSV pass and this reconciliation correctly attribute the block to the same underlying canonical identity.

## Artifact integrity repaired

`CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv` was malformed (25 of 49 rows had 25–30 fields against a 24-column header, from unquoted embedded commas). Rebuilt via `csv.writer` with `QUOTE_MINIMAL`, preserving the exact same 49 programs and substantive content. See `CLAUDE_CSV_VALIDATION_REPORT.md` for the full parser-validation results across all 5 delivered/repaired CSVs — all pass.

`CLAUDE_659_PHYSICAL_RECORD_IDENTITY_LEDGER.csv` (new, this workstream) provides one parseable row per physical record — no aggregate placeholder rows — superseding the prior workstream's aggregate-only `CLAUDE_FINAL_UNIQUE_PROGRAM_CENSUS.csv`/`CLAUDE_FINAL_UNPRICED_PROGRAM_LEDGER.csv` for record-level proof purposes (those two files are left in place, unmodified, as historical taxonomy summaries).

## Stacking dispositions (Section E)

Re-ran the focused controls specified: NY principal + NY post-production (`test_b4_authority_exhaustion_gate.py`'s named mutual-exclusivity test), Canadian federal + provincial stacking (`test_stacking_engine.py`), an ordinary hybrid and a combined co-production hybrid (`test_claude_global_optimizer_p0_remediation.py::test_comb_001_*`). **108/108 passed** — no regressions, spend conservation and no-duplicate-incentive-base already proven by this existing suite and unaffected by this workstream (no pricing code was touched).

## AG research handoff: 31 vs. expected 32

31 genuinely open, evidence-backed research questions identified (30 from B1's `INSUFFICIENT_SUBSTANTIVE_EVIDENCE`/`FLAGGED` rows + `kz_investment_subsidy`). The delta from the expected 32 is disclosed, not papered over — see `CLAUDE_CSV_VALIDATION_REPORT.md`'s explicit explanation: 74 additional coverage-registry programs also carry an evidence gap, but none has enough existing repository evidence to form a specific, answerable primary-source question distinct from "start worldwide research from zero," which is explicitly out of scope for a targeted handoff.

## Four-production regression (Section G)

Current-engine cache invalidated for exactly the four acceptance productions; one fresh evaluation run for each. All four returned `EVALUATION_COMPLETE` with fingerprints identical to the pre-workstream state (expected — no pricing/registry code changed this pass, only documentation/CSV artifacts). Anchor incentives unchanged for all four: Little Utopia $573,059.70 (MU), F#K Valentine's Day $1,445,659.84 (GR), Bad Hombres $596,910.25 (US-NM), Lips Like Sugar $3,459,278.90 (US-CA). Structure-family counts (single-jurisdiction, `treaty_coproduction`, `component_relocation`, `full_relocation`, `multi_program`) unchanged from the prior workstream's committed state for all four productions.

## Out of scope, correctly not touched

No AU–UK/other treaty research performed. No MU/GR/US treaty sweep. No Globe work. No separate reinvestment/in-kind workstream (this workstream makes no reinvestment/in-kind completion claims — the prior workstream's language on that subject was scoped to its own phase and is unaffected here). Ohio, Nevada, Bulgaria, Underwater untouched.

## Status

`READY_FOR_AG_RESEARCH` — all 659 physical records appear individually, all 126 executable labels have a deterministic disposition, no executable program remains blocked without a substantive reason or correction, every delivered CSV parses under its declared schema, and the branch is committed, pushed, and clean.

This is not a claim of Codex acceptance. Codex runs only after AG research is implemented by Claude.

---

## Addendum — CLAUDE_PRE_AG_HANDOFF_CORRECTION (this workstream)

Three specific ambiguities in the above were corrected before AG research begins, without repeating the 659-record census or re-running broad suites.

### 1. The eight fact-dependent programs — one real implementation defect found and fixed

Full detail: `CLAUDE_EIGHT_FACT_DEPENDENCY_RESOLUTION.csv` (18 fact-rows across the 8 programs: `au_location_offset`, `ca_bc_dave`, `cz_film_incentive_animation`, `ma_ccm_rebate`, `nl_film_production_incentive`, `th_film_incentive`, `us_or_opif`, `za_nfvf_rebate`).

**Real defect found**: none of these programs' `PRODUCER_CONTROLLED_ASSUMPTION`-class boolean facts (preapproval confirmation, registration/acceptance, self-attested activity type, fund-currency confirmation) were ever supplied anywhere in the real `canonical_evaluation.py` pipeline — grepping the entire file for each fact key returned zero hits. This meant these conditions could **never** be satisfied by a real `evaluate_project()` call regardless of real qualifying spend, silently suppressing conditional pricing for otherwise-eligible candidates. This is exactly the class of defect the project's global assumption policy forbids.

**Fix**: added `_PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS` (a `frozenset` of exactly 6 fact keys, each individually verified administrative-not-discretionary) to `canonical_evaluation.py`, unioned into `evidenced_facts` at all three real pricing call sites (`_price_candidate`, `_price_component_relocation_candidate`, `_price_combined_coproduction_component_candidate`). `ENGINE_VERSION` bumped `1.61.0 → 1.62.0` to invalidate stale cached rows.

**Deliberately excluded** from auto-assumption (kept as real, unassumed gates): `us_or_opif_award_confirmed` (its own condition text names "agency comparative/discretionary approval" — genuinely discretionary), `nl_nfpi_points_independence_test_passed` (a substantive content/independence test), `nl_nfpi_format_threshold_met` (a spend/format test). Three focused prevention tests added and passing, plus 111 further directly-affected tests across 7 test files (`test_ca_bc_dave_component.py`, `test_final_wiring_oregon_conditional_formula.py`, `test_final_wiring_nl_company_period_conservation.py`, `test_incentive_optimizer_core_closeout.py`, `test_oregon_full_db_pipeline.py`, `test_b3_formulaic_consumption.py`, `test_copro_conditional_pricing_data_reconnection.py`, `test_national_cultural_status.py`).

`cz_film_incentive_animation` and `au_location_offset`/Oregon's own already-correct QPE-probe pattern required **no code change** — genuine spend/QPE/scope conditions, correctly left as real gates.

### 2. The 47 executable-gap programs — corrected terminology

`MISLABELED_NON_EXECUTABLE` is no longer applied merely for appearing in `_B1_DISCRETIONARY_RULING`/`COVERAGE_REGISTRY` or lacking evidence. Of the 47:

- **11 `MISLABELED_NON_EXECUTABLE` (conclusive)** — existing authoritative evidence already proves the category: `ae_ad_film_rebate`, `be_tax_shelter`, `qa_screen_production_incentive`, `sa_film_commission_rebate` (negotiated/discretionary — two are the codebase's own canonical worked examples); `ch_pics_national_rebate`, `no_film_incentive`, `tw_bamid_rebate`, `ph_fdcp_flip`, `jp_vipo_location_incentive`, `kr_kofic_location_incentive` (selective/competitive, explicit language or COVERAGE_REGISTRY's own confirmed selective state); `ae_dxb_dpip` (inactive/superseded).
- **5 `FORMULAIC_AND_PRICEABLE`** — `de_dfff`, `dk_production_rebate`, `in_national_film`, `lu_filmfund_tax_shelter_rebate`, `sg_made_with_singapore_rebate`. These are real, named, separate funds with a determinable formula — not conclusively non-executable at all. **Disclosed gap**: full separate-from-QPE fund-pricing infrastructure was not built this pass (a distinct, larger feature; out of scope for a terminology-correction workstream) — these remain `DISPLAY_ONLY_ZERO_GUARANTEED` in runtime disposition pending that infrastructure, correctly relabeled in taxonomy only.
- **31 `RESEARCH_PENDING_EXECUTABILITY_DETERMINATION`** — no existing authoritative evidence yet conclusively proves any of the 6 allowed non-executable categories. Handed to AG research (see below). 79 + 11 + 5 + 31 = 126 — the reconciliation is exact, with no demotion performed merely to make totals match.

### 3. 31 vs. 32 — reconciled exactly

The prior handoff's filter logic had a real bug: it matched B1's `corrected_disposition` column against two hardcoded strings that didn't exactly match two real rows' actual stored text (`eg_empc_cashback`'s disposition was the differently-worded `GENUINE_SCOPE_MISMATCH`; `se_production_rebate`'s was `STATUTORY_PRODUCTION_INCENTIVE (flagged, not blocked)`, not the literal `"FLAGGED -- ..."` string the filter checked for) — both were silently dropped. Separately, `kz_investment_subsidy` was added to the prior 31 but is **not** part of the canonical 32-program set the workstream defines.

**Exact diff**: `expected − current = {eg_empc_cashback, se_production_rebate}` (both restored); `current − expected = {kz_investment_subsidy}` (removed — not a canonical alias of anything in the 32, simply out of scope for this specific handoff; it remains correctly disclosed as `UNPRICEABLE_AUTHORITY_INSUFFICIENT` in `CLAUDE_659_PHYSICAL_RECORD_IDENTITY_LEDGER.csv`, just not part of this particular 32-program AG queue). `eg_empc_cashback`'s reclassification from `GENUINE_SCOPE_MISMATCH` to `RESEARCH_PENDING` reflects a real reconsideration: its "anchor day" facility requirement may be a producer-controlled operational choice (shoot ≥1 day inside the EMPC facility) rather than a hard, non-curable scope mismatch — genuinely worth AG confirming rather than treating as conclusively closed. `CLAUDE_AG_32_RESEARCH_HANDOFF.csv` now contains exactly the 32 specified program IDs.

### Validation

All three updated/created CSVs (`CLAUDE_EIGHT_FACT_DEPENDENCY_RESOLUTION.csv`, `CLAUDE_126_EXECUTABLE_PRICING_PROOF.csv`, `CLAUDE_47_EXECUTABLE_GAP_RECONCILIATION.csv`, `CLAUDE_AG_32_RESEARCH_HANDOFF.csv`) parse cleanly under Python's `csv` module with the declared row/column counts and zero malformed rows.

## CORRECTION ADDENDUM (2026-09-15, CLAUDE_GENERIC_AMOUNT_GATED_DISCOVERY_REPAIR)

This closeout's original methodology for verifying the 8 fact-dependent programs (`au_location_offset`, `ca_bc_dave`, `ma_ccm_rebate`, `th_film_incentive`, and four others) relied on manually supplying `evidenced_facts`/`amount_facts` directly to an isolated `resolve_program_rate()` call, not a genuine run of the served `discover_executable_jurisdictions()`/`_price_candidate()` pipeline. A real pipeline run at the time would have rejected all four of the amount-gated programs before pricing ever ran, because their `amount_fact_key` values were never populated anywhere in the real discovery/preflight path. This was a real, since-fixed implementation defect, not merely a documentation gap — see `CLAUDE_AMOUNT_GATED_DISCOVERY_REPAIR.csv`, `CLAUDE_AMOUNT_GATED_RUNTIME_PROOF.csv`, and `CLAUDE_AMOUNT_DISCOVERY_REPAIR_CLOSEOUT.md` for the fix and genuine, fresh, real-pipeline proof against all 4 acceptance productions.
