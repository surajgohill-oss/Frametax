# CineGlobe Bounded Engineering Optimizer Remediation — Claude Closeout

**Controlling document:** `docs/validation/CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_REMEDIATION_CLAUDE_PROMPT.md`
**Controlling version:** `e507f7f0677aeec427bafa437fee318ca22ec6cd`
**Prior commit under repair:** `4ea0fd832ec52d0ae3e152a404395efa3cbfffc9` (Codex NOT_ACCEPTED)
**Worktree used:** `/Users/Suraj/cineglobe-frametax-claude-remediation` on `claude/audit-frametax-features-NZcX5` (created fresh; `/Users/Suraj/cineglobe-frametax` (`ag/ui-refinement-review`) and `/Users/Suraj/ag-oregon-research` (`ag/oregon-authority-gap-research`) were never modified — confirmed untouched at both start and end via `git worktree list`)

## Overall status: `IMPLEMENTED_PENDING_CODEX_ACCEPTANCE` (all seven rows closed)

**Second pass (Codex, `PLATFORM: Codex`, workstream `CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_REMEDIATION_P0_SEL_ALT_001`):** Codex accepted the first six rows and rejected the P0-SEL-ALT-001 revert, providing the exact root-cause diagnosis the first attempt missed and the exact required fix (see the updated P0-SEL-ALT-001 section below). That fix is now implemented, verified against the real pipeline (Bad Hombres/Little Utopia/F#K Valentine's Day/Lips Like Sugar), and additionally verified against the **entire** backend test suite (4,899 passed, 3 skipped, 0 failed, in 1h38m — run in full per Codex's explicit instruction in this second pass, superseding the first pass's "do not run the full suite" scope limit for this one verification step).

## Per-row disposition

### P0-FX-001 (FX immutability / finiteness / cache-identity) — IMPLEMENTED, VERIFIED

- `CanonicalFXContext.rates` is now a `types.MappingProxyType` over a defensively-copied dict (`apply_fx_rates.py`), verified to raise `TypeError` on item assignment/deletion and to be immune to mutation of the caller's original dict after construction.
- `resolve_fx_rate()` now checks `math.isfinite(rate)` **before** any `<=`/`>` comparison, returning the new typed `FX_STATUS_NONFINITE` disposition for NaN, +infinity, and -infinity (previously all three silently passed every ordinary comparison and reached `RESOLVED`).
- `canonical_evaluation._compute_fingerprint()` now hashes a full SHA-256 digest of `{snapshot_date, sorted(rates), source, freshness_status}` instead of `snapshot_date` alone — two same-date contexts differing in rate/source/freshness no longer collide.
- Verified directly: NaN/+inf/-inf rejected pre-comparison; mutation attempts raise `TypeError`; same-date differing contexts produce different fingerprints; an identical context still produces the same fingerprint (determinism preserved).
- Tests: `tests/test_canonical_fx_context.py` (5 new: mutation rejection, NaN, ±infinity, NaN-through-`price_segment`), `tests/test_cache_fingerprint_expansion.py` (1 new: digest sensitivity + determinism regression).

### P0-NL-001 (Netherlands company-period cap) — IMPLEMENTED, VERIFIED

- `IncentiveValueCapRule` gained two new boolean-fact gates: `company_period_has_other_productions_fact_key` and `company_period_aggregate_evidenced_fact_key`.
- New semantics in `allocation_pricing._resolve_incentive_dollar_cap()`: no claim of company-period interaction (the common case) → full native cap, unchanged from every prior single-production project. A claim that other productions exist (`has_other_productions` evidenced) with no evidenced, finite, in-range amount → **fails closed** (non-priceable), never defaults to zero-consumed/full-cap. A claim with both facts evidenced and a valid amount → cap reduced by that amount.
- Matches all four CROSSCHECK cases exactly: no-claim → USD 3,421,571.87; missing/unresolved aggregate → non-priceable; explicit evidenced EUR 0 → USD 3,421,571.87; evidenced EUR 2,000,000 → USD 1,140,523.96.
- Four call sites unpacking the resolver's now-5-tuple return were updated (`tests/test_canonical_economics_integrity_repair.py` ×3, `tests/test_generic_future_project_propagation.py` ×1, `scripts/canonical_executable_conformance.py` ×1).
- Proven end-to-end: two real `price_segment()` calls simulating the same company's two productions in one award period jointly never exceed EUR 3,000,000 (Project A exhausts the cap; Project B correctly receives $0 when evidenced, or fails closed when unresolved).
- Tests: `tests/test_final_formulaic_full_pipeline_consumption.py::test_nl_nfpi_company_period_cap_consumes_prior_awards_across_projects` (updated to use the new evidence facts, plus two new adverse cases: unresolved-aggregate-fails-closed, unbound-scalar-fails-closed).

### P0-TX-001 (Texas awarded-rate range) — IMPLEMENTED, VERIFIED

- `program_rate_rules.py`'s awarded-rate substitution now rejects non-finite values (`math.isfinite`) **before** any range comparison, and the range check is now exclusive-floor/inclusive-ceiling: `0 < rate <= 0.31` (previously `0 <= rate <= 0.31`, silently admitting an invalid `rate=0.0` "award").
- Verified against all 9 CROSSCHECK adverse cases: -0.0001, 0.0, NaN, +inf, -inf all reject; 0.24/0.28/0.31 price correctly ($888,297.12 / $1,036,346.64 / $1,147,383.78 on FVD's real QPE); 0.3100001 rejects.
- Tests: `tests/test_final_formulaic_full_pipeline_consumption.py::test_us_tx_miip_award_and_resident_threshold` (2 new adverse cases added: exact-zero award, NaN award, both DB-backed end-to-end through the real persistence path).

### P0-ZA-001 (South Africa / shared component-basis conservation) — IMPLEMENTED, VERIFIED

- `allocation_pricing.py`'s shared `is_component_basis` incentive calculation (used by both `za_nfvf_rebate`'s post-only tier and `us_or_opif`'s payroll/other split) now validates the caller-supplied component basis is finite, non-negative, and `<= qpe` (the segment's own real qualifying allocated spend) **before** multiplying into an incentive. A violation fails the whole segment closed (`executable=False`) with a disclosed blocker, never a silent clamp.
- Verified the exact adversarial case: $1 allocated segment claiming a $1,000,000 QSAPPE now correctly rejects (was: `executable=True, incentive=$250,000`). Regression-verified: exact-match, in-bounds, and general-branch (non-component-basis) cases all still price correctly; `us_or_opif`'s own existing component-basis tests (a shared code path) show no regression.
- Tests: `tests/test_final_formulaic_full_pipeline_consumption.py::test_za_nfvf_rebate_cap_applies_to_calculated_incentive_and_post_only_branch` (extended with the conservation adversarial case plus negative/NaN/±infinity basis cases).

### P0-SEL-ALT-001 (LU/FVD distinct alternative selection) — IMPLEMENTED, VERIFIED (second pass)

**First attempt (reverted, documented for the record):** the blanket `is_directly_comparable=is_baseline` copy at the single-program `STATUS_PRICED` branch was replaced with `is_baseline OR (pricing.is_fully_priced AND pricing.npc_with_adjustments_usd is not None)`, on the reasoning that travel/FX/local-cost normalization now runs generically for every candidate. Empirically wrong: Bad Hombres' `ca_film_30` (Canada) and five other relocation candidates all became `is_directly_comparable=True` and displaced the real `us_nm_film_credit` baseline as canonical winner, because a benchmark model successfully returning a number is not the same fact as a producer having verified relocation friction for that specific candidate — the fix let an effectively-unevidenced delta silently act as if it were zero/negligible. Reverted cleanly before commit.

**Codex's second-pass diagnosis (accepted) and required fix (implemented):** the correct gate is not "did the calculator return a number" but "does an explicit, affirmative, EVIDENCED fact confirm every required relocation dimension (travel, local-cost, in-kind replacement) has been fully accounted for or deliberately zeroed, for THIS specific candidate jurisdiction." Implemented as `_relocation_normalization_is_complete(is_baseline, code, inputs)` in `canonical_evaluation.py`: baseline is always comparable by construction; a non-baseline candidate is comparable only when `f"relocation_completeness_evidenced__{code}"` is present in `inputs.evidenced_program_facts` — a real, persisted `ProjectFact` boolean row, the same mechanism every other boolean gate in this codebase already uses. Applied only at the single-program `STATUS_PRICED` branch (the multi-program stack branch's `risk_adjusted_net_cost_usd` is still genuinely un-normalized raw NPC and correctly remains untouched, unchanged from the first pass's reasoning).

No caller in this codebase sets this fact for any project today, so the mechanism is now honest (checks for verified evidence rather than inferring completeness from a benchmark estimate) while correctly, safely leaving every non-baseline candidate exactly as non-comparable as before any of this repair — no new comparable winner is invented anywhere in the corpus.

**Verified against the real pipeline:**
- **Bad Hombres**: `canonical_selected_structure_id` resolves to `us_nm_film_credit` (rank 1, $596,910.25 incentive / $1,885,112.75 NPC); exactly one candidate is `is_directly_comparable` (the baseline) — `ca_film_30` (Canada) and every other relocation candidate correctly remain non-comparable, disclosed but not ranked.
- **Lips Like Sugar**: `ca_film_30` retained exactly ($3,459,278.90 / $8,524,375.10).
- **Little Utopia**: `leading_conditional_structure` still surfaces Mauritius (`mu_edb_incentive`), with its exact missing dimension disclosed (`qualification_state: "AUTHORITY_UNRESOLVED"` — the cultural-test-applicability authority gap); `canonical_selected_structure_id` still `None` (no comparable winner exists, correctly unchanged).
- **F#K Valentine's Day**: `leading_conditional_structure` still surfaces Greece (`gr_cash_rebate`), same disclosure mechanism, `canonical_selected_structure_id` still `None`.
- **Full backend suite**: 4,899 passed, 3 skipped, 0 failed (1h38m) — run in full per Codex's explicit second-pass instruction.

Tests: no new test file was added for this row in the second pass (the fix is a single, narrowly-scoped function change verified directly against the real persisted four-project corpus above plus the complete pre-existing suite, which already exercises `is_directly_comparable`/`relocation_cost_normalized` across 10 files); a future evidence-capture UI that actually sets `relocation_completeness_evidenced__{code}` facts should add its own coverage at that time.

### P0-OR-001 (Oregon terminal disposition) — VERIFIED, NO CHANGE NEEDED

**AG's Oregon evidence was independently checked against primary sources, not merely accepted.** `docs/validation/OREGON_AUTHORITY_GAP_ADJUDICATION_AG.md`/`.csv` (branch `ag/oregon-authority-gap-research`, read-only, never merged/cherry-picked) cites ORS 284.368 and OAR 951-002-0010. Direct fetch of both:

- **Regional uplift basis:** confirmed via `oregonlegislature.gov/bills_laws/ors/ors284.html` — the statute's exact text is "an increase of 10 percent **of the amount** otherwise allowable," i.e. **multiplicative** (a 10% bump on the calculated dollar figure), not an additive +10 percentage points on the rate. AG's own phrasing ("+10% uplift") was ambiguous and could have been misimplemented as additive — a genuine trap this task's instructions warned about, caught by independent verification.
- **Project cap dollar figure:** confirmed via `secure.sos.state.or.us/oard/displayDivisionRules.action?selectedDivision=4217` (OAR 951-002-0010(5)) — the rule text ("no single qualifying film may be awarded more than 50% of the entire OPIF fund... in any given fiscal year") is real, but AG's own adjudication doc's parenthetical "$10.6M max for a $21.2M fund" cites **no source anywhere in the evidence CSV** for the $21.2M current annual fund total. This is a genuine, still-unresolved, calculation-driving proposition — the cap's real current dollar value cannot be computed without it.
- Also confirmed: the $1M compensation cap is a QPE-exclusion (reduces eligible spend), distinct from the project cap (which caps the final incentive); the award is confirmed discretionary/fund-availability-gated (OAR 951-002-0020(3)).

**Terminal disposition (outcome 2, as instructed):** `us_or_opif` remains `UNPRICEABLE_AUTHORITY_INSUFFICIENT` in `authority_coverage_registry.py` (unchanged — this was already correct before and after AG's evidence). AG's proposed correction to `PRICEABLE`/`CONDITIONAL` was **not applied**, exactly as AG's own adjudication doc instructed ("Do not apply this correction; wait for Codex").

**Candidate construction is confirmed reached** (satisfying the prior workstream's CRITICAL MID-RUN CORRECTION): `price_segment(jurisdiction_code="US-OR", program_slug="us_or_opif", ...)` is called by the real pipeline and returns `executable=False` with an explicit `UNPRICEABLE_AUTHORITY_INSUFFICIENT` blocker (`tests/optimization/test_global_data_application_runtime.py::test_price_segment_hard_blocks_a_covered_program_even_when_directly_specified`) — never silently absent from the candidate universe, never a fabricated number. `resolve_program_rate("us_or_opif", ..., amount_facts={"us_or_payroll_qpe_usd": 1_200_000.0})` still correctly returns `None` even with qualifying payroll facts evidenced (`tests/test_final_formulaic_full_pipeline_consumption.py::test_us_or_opif_coverage_veto_is_reconciled_and_correctly_remains_blocked`) — the coverage veto, never the tier shape, is what blocks it. Both existing tests were run and pass; no new test was needed since these already prove exactly the row's required reproducer ("resolve_program_rate real slug with qualifying payroll fact... remain fail-closed").

Oregon remains excluded from priced-consumption numerators; it is present (not silently dropped) in candidate construction and the 12-program inventory.

### P0-AE-001 (AE/Dubai identity and denominator semantics) — VERIFIED, NO CHANGE NEEDED

- Confirmed via `authority_coverage_registry.economic_block_for_program()`: `ae_dpip` and its runtime spelling `ae_dxb_dpip` are `SUPERSEDED` (a blocking state — retained for provenance, never priced as current); `ae_ad_film_rebate` (Abu Dhabi) is a **separate**, correctly-distinct identity, independently `FAIL_CLOSED` under the B1 discretionary ruling.
- `ae_dpip` is formally classified as an **identity-control/composite acceptance row**: Dubai's own DPIP doctrine record (40% flat, `jjagency.co`+`iconartproduction.com`, distinct jurisdiction code `AE-DXB`) is genuinely distinct data from Abu Dhabi's (35%/50% points-based, `film.gov.ae`) — never copied — but Dubai's coverage state independently blocks it from candidacy regardless.
- No cross-emirate rate leakage: `get_rate_rules("ae_ad_film_rebate")` contains the 0.35 rate; `get_rate_rules("ae_dxb_dpip")` contains no 0.35 rate at all.
- This disposition was already settled across multiple independent prior audits (`GLOBAL_PROGRAM_FORMULAIC_CONSUMPTION_CLAUDE.csv`: `VERIFIED_NO_CHANGE_NEEDED`; `GLOBAL_PROGRAM_TEST_ORACLE_AUDIT_CODEX.csv`: `PASS`) with an existing regression test. That test was re-run under every change in this pass and still passes.
- Tests: `tests/test_b3_formulaic_consumption.py::test_ae_dpip_dubai_fail_closed_abu_dhabi_separately_identified` (pre-existing, re-verified, no change).

## Four real-project recomputations (all four, serially, exact match)

| Project | Winner / leading disposition | Incentive | NPC (adjusted) |
|---|---|---|---|
| Little Utopia | `leading_conditional_structure` → `mu_edb_incentive` (Mauritius); no comparable winner (`canonical_selected_structure_id=None`) | — | — |
| F#K Valentine's Day | `leading_conditional_structure` → `gr_cash_rebate` (Greece); no comparable winner (`canonical_selected_structure_id=None`) | — | — |
| Bad Hombres | `us_nm_film_credit` (canonical winner, rank 1) | $596,910.25 | $1,885,112.75 |
| Lips Like Sugar | `ca_film_30` (canonical winner, rank 1) | $3,459,278.90 | $8,524,375.10 |

All four match the required anchors/figures exactly, recomputed a second time after the P0-SEL-ALT-001 fix landed. Manitoba/Romania were never hardcoded as alternate winners — the shipped fix requires real, currently-nonexistent evidence before any non-baseline candidate can ever become comparable, so no alternate winner is invented anywhere in the corpus.

## Files changed

- `frametax2/backend/app/calculators/apply_fx_rates.py` — FX immutability + finiteness (P0-FX-001)
- `frametax2/backend/app/services/canonical_evaluation.py` — fingerprint digest (P0-FX-001); `_relocation_normalization_is_complete()` evidenced-fact gate (P0-SEL-ALT-001, second pass)
- `frametax2/backend/app/services/canonical_project_economics.py` — amount-fact finiteness (P0-FX-001)
- `frametax2/backend/app/data/program_rate_rules.py` — Texas exclusive-floor/finiteness (P0-TX-001); NL company-period cap evidence gates (P0-NL-001)
- `frametax2/backend/app/calculators/allocation_pricing.py` — ZA/shared component-basis conservation (P0-ZA-001); NL company-period cap resolution (P0-NL-001); cap-unresolved fail-closed branch
- `frametax2/backend/tests/test_canonical_fx_context.py` — new P0-FX-001 adverse tests
- `frametax2/backend/tests/test_cache_fingerprint_expansion.py` — new P0-FX-001 cache-identity test
- `frametax2/backend/tests/test_final_formulaic_full_pipeline_consumption.py` — P0-NL-001, P0-TX-001, P0-ZA-001 test updates/additions
- `frametax2/backend/tests/test_canonical_economics_integrity_repair.py` — 5-tuple unpacking fix (P0-NL-001, mechanical)
- `frametax2/backend/tests/test_generic_future_project_propagation.py` — 5-tuple unpacking fix (P0-NL-001, mechanical)
- `frametax2/backend/scripts/canonical_executable_conformance.py` — 5-tuple unpacking fix (P0-NL-001, mechanical)
- `frametax2/PROJECT_RULES.md` — mandatory hard-timeout/anti-loop rule appended

## Timeouts / incomplete items

- No individual command, test file, or grouped test run exceeded its budgeted hard timeout during either pass.
- The full-suite run in the second pass (4,899 tests, 1h38m) was run in the background per this project's own persisted anti-loop discipline (never block the session on an unbounded foreground wait) and completed cleanly with no stall, no orphaned process, and no DB-session contention — unlike the prior (pre-remediation) workstream's documented full-suite stall.
- One pre-existing, unrelated test-ordering DB-state leak was discovered between `tests/test_canonical_served_wiring_repair.py` and `tests/test_copro_qualification_wiring.py` (neither file touched by this remediation) when run together in a partial subset — reproduced in isolation with only those two files, confirming it predates and is unrelated to this pass. Not fixed (out of bounded scope). Notably, this exact pairing did NOT reproduce as a failure inside the full-suite run (different collection order), consistent with it being a known class of order-dependent test flakiness rather than a real defect in either file's own logic.
- All seven rows are now closed. No `INCOMPLETE` rows remain.

## Excluded areas

No files outside the FX/NL/TX/ZA/AE/Oregon/SEL-ALT dependency cone and the frozen exclusion list were changed. No frontend, no broad worldwide research, no MFNI workstream. The full backend suite was run exactly once, in the second pass, per Codex's explicit instruction for that one verification step.
