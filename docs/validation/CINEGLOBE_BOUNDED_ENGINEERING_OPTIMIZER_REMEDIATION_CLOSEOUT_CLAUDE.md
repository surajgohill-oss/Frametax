# CineGlobe Bounded Engineering Optimizer Remediation — Claude Closeout

**Controlling document:** `docs/validation/CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_REMEDIATION_CLAUDE_PROMPT.md`
**Controlling version:** `e507f7f0677aeec427bafa437fee318ca22ec6cd`
**Prior commit under repair:** `4ea0fd832ec52d0ae3e152a404395efa3cbfffc9` (Codex NOT_ACCEPTED)
**Worktree used:** `/Users/Suraj/cineglobe-frametax-claude-remediation` on `claude/audit-frametax-features-NZcX5` (created fresh; `/Users/Suraj/cineglobe-frametax` (`ag/ui-refinement-review`) and `/Users/Suraj/ag-oregon-research` (`ag/oregon-authority-gap-research`) were never modified — confirmed untouched at both start and end via `git worktree list`)

## Overall status: `NOT_COMPLETE_WITH_EXACT_REMAINING_ITEMS`

Six of seven rows are implemented and verified. One row (`P0-SEL-ALT-001`) was attempted, produced a confirmed adverse regression on first implementation, was reverted to the safe pre-existing state, and is reported honestly incomplete rather than forced through.

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

### P0-SEL-ALT-001 (LU/FVD distinct alternative selection) — **NOT COMPLETE**

**Attempted and reverted.** The blanket `is_directly_comparable=is_baseline` copy at the single-program `STATUS_PRICED` branch (`canonical_evaluation.py`) was replaced with a structured completeness check (`is_baseline OR (pricing.is_fully_priced AND pricing.npc_with_adjustments_usd is not None)`), reasoning that travel/FX/local-cost normalization now runs generically for every candidate (per the module's own "STALE" comment on `RELOCATION_COMPARABILITY_NOTE`) and only the uniformly-undisclosed in-kind dimension remains absent.

**This was empirically wrong and was reverted.** Running the real pipeline against Bad Hombres showed six of its relocation candidates (`ca_film_30`, `us_ky_keiia`, `ny_state_film`, `my_finas_rebate`, `ro_film_office_cash_rebate`, `us_la_film_incentive`) all became `is_directly_comparable=True` with lower `npc_with_adjustments_usd` than Bad Hombres' own real baseline (`us_nm_film_credit`), and the canonical winner swapped from `us_nm_film_credit` to `ca_film_30` — a direct, confirmed violation of this task's explicit "preserve Bad Hombres/Lips Like Sugar economics exactly" requirement. The "generic normalization" is real (the fields are genuinely computed), but is not yet accurate/complete enough to trust as a true apples-to-apples comparison against a production's own home jurisdiction — real, un-modeled relocation friction (full-crew/cast travel logistics, not just the travel budget line; genuine in-kind value; production continuity risk) means a naive lower NPC does not currently establish a candidate is a genuinely comparable alternative. The change was fully reverted (`canonical_evaluation.py` now contains only the unrelated, verified P0-FX-001 fingerprint fix); all 100 tests across the 10 files touching `is_directly_comparable` pass identically to the pre-attempt state, and all four real-project recomputations below confirm byte-identical figures to the required anchors.

**What would be required to close this safely:** a genuinely reliable, currently-nonexistent per-candidate signal for "this candidate's relocation-adjusted NPC is complete and trustworthy enough to rank against the baseline" — not merely "the normalization fields were populated." Building that signal is new economic-modeling work (quantifying real relocation friction generically), not a bug fix, and is out of this bounded remediation's scope. The row is left in its pre-existing, safe state: every non-baseline candidate remains disclosed (priced, visible, with `RELOCATION_COMPARABILITY_NOTE`) but not admitted to the comparable ranking pool — the same behavior commit `4ea0fd8` shipped, now with an honest record of why a fix was attempted and reverted rather than a second unverified claim of completion.

No code changes were left in place for this row. `leading_conditional_structure`/`unlockable_alternatives` continue to work exactly as before (Little Utopia → Mauritius; F#K Valentine's Day → Greece — see recomputation table below).

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

All four match the required anchors/figures exactly. Manitoba/Romania were never hardcoded as alternate winners (P0-SEL-ALT-001 was reverted — no alternate-selection code shipped at all).

## Files changed

- `frametax2/backend/app/calculators/apply_fx_rates.py` — FX immutability + finiteness (P0-FX-001)
- `frametax2/backend/app/services/canonical_evaluation.py` — fingerprint digest only (P0-FX-001); no P0-SEL-ALT-001 changes remain
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

- No individual command, test file, or grouped test run exceeded its budgeted hard timeout during this pass.
- One pre-existing, unrelated test-ordering DB-state leak was discovered between `tests/test_canonical_served_wiring_repair.py` and `tests/test_copro_qualification_wiring.py` (neither file touched by this remediation) — reproduced in isolation with only those two files, confirming it predates and is unrelated to this pass. Not fixed (out of bounded scope); both files pass individually.
- P0-SEL-ALT-001 is the sole `INCOMPLETE` row — see above for the concrete adverse evidence and what would be required to close it safely.

## Excluded areas

No files outside the FX/NL/TX/ZA/AE/Oregon dependency cone and the frozen exclusion list were changed. No frontend, no broad worldwide research, no MFNI workstream. The full backend suite was never run.
