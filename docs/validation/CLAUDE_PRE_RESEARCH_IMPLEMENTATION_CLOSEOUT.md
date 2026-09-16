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
