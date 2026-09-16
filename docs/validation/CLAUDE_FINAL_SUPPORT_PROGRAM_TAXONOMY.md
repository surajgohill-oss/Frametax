# CLAUDE_FINAL_PROGRAM_TAXONOMY_UNPRICED_LEDGER_AND_SUPPORT_CLOSEOUT — Support Program Taxonomy

## 1. STATUTORY_PRODUCTION_INCENTIVE

79 programs (up from 75 before this workstream) — every executable program with `economic_block_for_program() is None`. Calculated, included in candidate economics, ranked. Allocation/application flags are **disclosed, never suppressive** (see Section E proof below).

**This workstream's correction**: `ca_bc_pstc`, `ca_federal_pstc`, `ca_qc_pstc`, `ca_nl_all_spend_credit` — four real, standard, non-discretionary Canadian tax credits, genuinely misclassified as `AUTHORITY_EXHAUSTED_FAIL_CLOSED`. Each has a directly-sourced official rate and a guaranteed non-band-ceiling floor tier; none carries selection/committee language. See `CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv`.

**California positive control** (Section E requirement): `ca_film_30` — `allocation_type=COMPETITIVE`, `preapproval_mandatory=True` (Credit Allocation Letter required before principal photography). Confirmed this workstream:
- `_is_discretionary_program("ca_film_30")` → `False`
- Prices normally: Lips Like Sugar's real baseline structure uses `ca_film_30`, NPC = $8,524,375.10
- The `administrative_allocation_risk` flag reaches the served structure output (`True` for California)
- The program is never labeled discretionary

This proves the existing allocation-flag mechanism (`program_requirements.AllocationType` enum: `ENTITLEMENT`/`FIRST_COME_FIRST_SERVED`/`COMPETITIVE`/`DISCRETIONARY`/`SUBJECT_TO_APPROPRIATION`, consumed by `canonical_evaluation._competitive_allocation_disclosure` and `_is_discretionary_program`) already correctly implements Section A/E's rule: only `DISCRETIONARY` suppresses guaranteed candidate generation; `COMPETITIVE`/`FIRST_COME_FIRST_SERVED`/preapproval requirements are disclosed risk, never blockers.

## 2. FORMULAIC_GRANT_OR_FUND

Real, separate, determinable-formula grants/funds distinct from QPE-based tax credits. Reclassified this workstream from a generic "discretionary" label to this more precise type (disposition — never entering guaranteed NPC — is unchanged): `de_dfff` (German federal DFFF, 30%, EUR 25M cap), `dk_production_rebate` (Denmark, 25%, DKK 125M pool), `in_national_film` (India, 30% base + uplifts), `lu_filmfund_tax_shelter_rebate` (Luxembourg, 30%/40%), `sg_made_with_singapore_rebate` (Singapore, S$10M fund cap). Plus 177 catalog-only entries whose `program_type` is fund-shaped (`direct_grant`/`development_fund`/`co_production_fund`/`broadcaster_fund`/`regional_fund`) — already correctly surfaced as `conditional_programs` disclosure on every real treaty/hybrid structure (BFI Film Fund, Eurimages, Creative England, etc.), never double-counted with QPE.

## 3. SELECTIVE_OR_COMPETITIVE_GRANT_FUND

Programs with explicit selection/competitive-round language, regardless of a published maximum: `no_film_incentive` (Norway — explicit: "five film and TV series projects" sharing a fixed pool, "not a guaranteed per-production entitlement"), `tw_bamid_rebate` (Taiwan — explicit: "a highly selective cash rebate"), `ch_pics_national_rebate` (Switzerland — range-assessed, hard cap), `ph_fdcp_flip` (Philippines — range-assessed, hard cap). Correctly shown as disclosed upside only, never determining the recommended structure, never entering verified NPC.

## 4. NEGOTIATED_OR_DISCRETIONARY_SUPPORT

`ae_ad_film_rebate` (Abu Dhabi) and `sa_film_commission_rebate` (Saudi Arabia) are the codebase's own **canonical worked examples** of this category (`canonical_evaluation.py`'s `_is_discretionary_program` documentation names both directly). `be_tax_shelter` (Belgium) is investor-intermediated financing — the net amount to the producer depends on negotiated investor/broker/insurance terms, not a government-paid formula. `qa_screen_production_incentive`'s 10% uplift is explicitly discretionary on its own terms.

## 5. REINVESTMENT_OR_IN_KIND_SUPPORT

**Existing mechanism, verified this workstream, not rebuilt.**

- **Reinvested qualifying/nonqualifying expenditure**: `app/calculators/canonical_opportunity_bridge.py`'s `discover_reinvestment_opportunity`/`discover_potential_reinvestment_candidates` (Task 3 of the reinvestment phase spec) — `ContributionType.CASH_REINVESTMENT`, `deferred_or_reinvested_usd` field. Regression coverage: `tests/test_canonical_opportunity_bridge.py` (62 tests, all passing this workstream). The module's own docstring states the core discipline directly: "NEVER conflate" the underlying expenditure with a second, duplicate economic entry.
- **Travel in-kind**: `AllocatedStructurePricing.inkind_replacement_delta_usd` + `inkind_note`. Regression coverage: `tests/test_inkind_contribution.py` (real Little Utopia Mauritius-anchor scenarios). **Isolated runtime control this workstream** (no real candidate among the four productions currently carries a nonzero delta, so an isolated control was used per this workstream's own Section F fallback rule): a real `StructureSpec`/`AllocationResult` priced via `price_allocated_structure` with `inkind_replacement_delta_usd=150,000.0` confirms:
  - `npc_verified_usd` (the pure statutory-formula figure) is **unchanged** — the in-kind delta never touches the base incentive calculation
  - `npc_with_adjustments_usd`/`npc_conservative_usd` correctly increase by **exactly** $150,000 (reflected once, not twice)
  - `selected_incentive_usd` is **identical** with or without the delta — confirming no automatic tax-credit gross-up on in-kind value
  - This is architecturally the same disclosed-adjustment pattern already used for travel and FX deltas (`travel_incremental_delta_usd`, `fx_delta_usd`)
- **Disclosed gap** (not an implementation defect — see `CLAUDE_FINAL_EXTERNAL_EVIDENCE_GAPS.csv`-equivalent note below): every current call site in `canonical_evaluation.py` passes `inkind_replacement_delta_usd=0.0` — no production currently has an evidenced off-budget in-kind contribution requiring a nonzero value, so 0.0 is the correct, honest default, not a stub. A future workstream that adds a real project-fact source for in-kind FMV could wire a nonzero value through the same, already-correct arithmetic.

## 6. INACTIVE_SUPERSEDED_DUPLICATE_ALIAS

`iceland_post_production_visual_effects_and_animation_incentive` (B4, retired/superseded), plus 4 `SUPERSEDED` + 1 `DUPLICATE` COVERAGE_REGISTRY entries. Unchanged this workstream.

## 7. INFORMATIONAL_ONLY

7 `NON_ECONOMIC` COVERAGE_REGISTRY entries (no dollar benefit to model) + 128 catalog-only `production_support`-type entries (generic label, not individually re-classified into a finer bucket this pass — see `CLAUDE_FINAL_UNIQUE_PROGRAM_CENSUS.csv` methodology note).

## 8. INSUFFICIENT_SUBSTANTIVE_EVIDENCE

**Administrative requirements never justify this classification.** Every row so classified in `CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv` and `CLAUDE_FINAL_UNPRICED_PROGRAM_LEDGER.csv` carries one of: an unresolved/modeled-not-confirmed formula (`au_nsw_pdv_rebate`'s rate is explicitly "modeled" by analogy), a genuine current-status gap (`gh_film_tax_incentive`: "2026 operational status not independently confirmed"; new/transitional programs like `al_cash_rebate`, `pt_scri_pt_cash_rebate`), a genuine scope/facility-nexus condition (`eg_empc_cashback`'s anchor-day gate), an unmodeled tiered-formula-application gap (`tt_production_expenditure_rebate`, `ua_cash_rebate`), or single-source/uncorroborated citation risk (`cr_tax_return_incentive`, `fj_film_rebate`, `pa_film_rebate`).

## Flagged for future review (not corrected this pass)

Four programs show real signs of the same B1 misclassification pattern as the four promoted Canadian programs, but were **not** promoted this pass out of deliberate time/scope discipline (bundling only the highest-confidence, independently real-world-verifiable corrections):

- `se_production_rebate` (Sweden) — explicitly first-come-first-served, a `FIRST_COME_AVAILABILITY` flag under Section A, not grounds for discretionary exclusion
- `us_il_film_production_services_credit` (Illinois) — VERIFIED-tier direct official citation, reads as a standard automatic entitlement
- `us_tn_performance_grant` (Tennessee) — VERIFIED-tier direct official citation, explicitly named a statutory "grant" formula
- `uy_tax_credit_2026` (Uruguay) — the single **strongest** primary citation in the entire 49-row B1 set (Uruguay's own official legal gazette, Decree 153/026), reads as a standard entitlement with a minimum-spend threshold

These are documented, not deferred silently, per `CLAUDE_FINAL_B1_49_RECLASSIFICATION.csv`'s `code_change_required` column.
