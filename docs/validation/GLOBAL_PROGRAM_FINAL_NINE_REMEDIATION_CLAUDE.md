# GLOBAL_PROGRAM_FINAL_NINE_REMEDIATION_CLAUDE

**Workstream:** GLOBAL_INCENTIVE_FINAL_NINE_RUNTIME_REMEDIATION_CLAUDE
**Controlling Codex audit commit:** `031f34bba9827c73c78e9bc2737fc1239dd0a4e0`
**Claude base remediation:** `95015bbfcdf5460ebfe9a46316540f34bc29085b`
**Controlling manifest:** `docs/validation/GLOBAL_PROGRAM_FINAL_RUNTIME_REMAINING_ITEMS_CODEX.csv` (9 rows)
**MFNI:** `PARKED_UNCHANGED`

---

## 1. Outcome

All nine remaining P0 rows from Codex's final-runtime reverification are closed: eight repaired with genuinely-executable production-code fixes, one (`us_or_opif`) reconciled and confirmed as `VERIFIED_NO_CHANGE_NEEDED` against this codebase's own established veto-lifting standard. Every fix is proven through the real, unmocked full-pipeline entrypoint (`discover_executable_jurisdictions()` and `price_segment()` / the real `evaluate_project()` + `build_production_and_structures()` served path for the four real projects) — never an isolated `resolve_program_rate()` call alone.

| Requirement | Result |
|---|---|
| Codex remaining rows closed | 9/9 |
| Formulaic rules reconciled | 12/12 |
| Full-pipeline optimizer consumption | 12/12 |
| Canonical FX path used for every relevant native-currency threshold | YES (never a hardcoded/guessed substitute) |
| Alias gate (`test_b4_transitive_alias_gate.py`) | PASS |
| Fail-closed gate (`test_codex_final_canonical_incentive_acceptance.py`, `test_b4_authority_exhaustion_gate.py`) | PASS |
| Fresh-process import-order integrity (`test_import_order_integrity.py`) | PASS |
| Reachable stale runtime paths | 0 |
| Unintended automatically-priced programs | 0 |
| Full backend suite | 4,863 passed / 3 skipped / 0 failed |
| Four real projects execute through canonical runtime | YES |
| MFNI | unchanged |

---

## 2. Per-program disposition

See `GLOBAL_PROGRAM_FINAL_NINE_RESULTS_CLAUDE.csv` for the full fix summary and test evidence per program, and `GLOBAL_PROGRAM_FORMULAIC_PIPELINE_PROOF_CLAUDE.csv` for the complete canonical-program → discovery → project-facts → threshold/FX → rate → QPE-basis → cap → incentive → candidate → optimizer-comparison → canonical-evaluation-result trace per program.

| Program | Codex's exact blocker | Fix |
|---|---|---|
| `cz_film_incentive` | "80% eligible-base cap absent; CZK450m cap modeled as user-entered incentive rejection" | New `IncentiveValueCapRule` (CZK 450,000,000) applied AFTER rate resolution to REDUCE the incentive, replacing the caller-attested-value antipattern. |
| `fr_trip` | "EUR2m threshold remains a USD fact/proxy" | `fr-vfx-threshold` now a genuine native-EUR fact (`fr_trip_vfx_spend_eur`), zero conversion. |
| `ma_ccm_rebate` | "18 days is a boolean label; prior approval/fund gate absent" | Numeric `ma_ccm_shooting_days_count` fact (genuine 17/18 boundary) plus a new, separate `ma-prior-approval-fund-availability` boolean gate. |
| `mt_mfc_rebate` | "EUR50k is USD57026.20 and 40% lacks certificate fact" | New `RateCondition.fx_native_currency`/`fx_native_threshold_amount` mechanism: dynamic FX conversion of the segment's own `qpe_usd`, never a fixed baked-in number, restoring Codex's required auto-pricing from real project data. New `mt-uplift-certificate` gate on both 40% ceilings. |
| `nl_film_production_incentive` | "Program caps absent" | Reconciled the already-accepted EUR 3,000,000 cap (`program_requirements.py`, never wired) into a new `IncentiveValueCapRule`. |
| `th_film_incentive` | "No preapproval/local-spend gate; one boolean unlocks 30%" | Complete rewrite to the real, already-accepted TFO tiered structure (15%/20%/25% by native THB spend + shared preapproval gate + genuinely discretionary +5% Soft Power uplift). |
| `us_or_opif` | "Real slug remains B4-blocked; caps absent; proof uses synthetic copied slug" | Veto reconciled against this codebase's own primary-source promotion standard and found correctly justified (secondary-source figures only) — kept blocked; the flagged synthetic-slug test antipattern replaced with a real, un-copied-slug proof. |
| `us_tx_miip` | "Award facts select only maximum 31%; phased tiers and pool not executable" | Replaced the vague boolean with the real, already-accepted structured facts: two independent numeric 35% crew/cast gates + a pool-period-validity gate, alongside the pre-existing award gate. |
| `za_nfvf_rebate` | "Cap rejects on caller-entered award; post-only branch explicitly unmodeled" | New `IncentiveValueCapRule` (ZAR 25,000,000) applied AFTER rate resolution; new distinct `za-nfvf-post-only-25` tier for the previously-unmodeled post-production-only branch. |

---

## 3. The shared FX architecture

No new FX engine, duplicate rate table, or program-specific exchange-rate constant was introduced. Every native-currency threshold either:

1. Compares a caller-evidenced native-currency fact directly against the native-currency statutory threshold (zero conversion — `fr_trip`, `ma_ccm_rebate`, `th_film_incentive`), or
2. Converts the segment's own `qpe_usd` to the native currency DYNAMICALLY at resolution time via the existing, real, dated `production_normalization.FX_RATE_SNAPSHOTS` and `apply_fx_rates.convert_usd_to_local` (`mt_mfc_rebate`'s `RateCondition.fx_native_currency`/`fx_native_threshold_amount`), or
3. Converts a fixed native-currency cap to USD once, via the existing `apply_fx_rates.convert_to_usd`, applied after rate resolution (`cz_film_incentive`, `nl_film_production_incentive`, `za_nfvf_rebate`'s new `IncentiveValueCapRule` / `convert_incentive_cap_to_usd`).

CZK and ZAR rates were sourced via the same provider (frankfurter.dev/ECB reference rates) and the same date (2026-07-13) already used for the project's existing EUR/GBP/CAD/MUR snapshot, added to `FX_RATE_SNAPSHOTS["2026-07-13"]` (`FX_RATES_VERSION` bumped 2.1.0 → 2.2.0). Every conversion's source, rate, and effective date are disclosed in the runtime trace (`ConditionEvaluation.note`, `IncentiveValueCapRule`'s cap-source description).

Where a native-currency threshold applies to the SAME quantity a segment's `qpe_usd` already represents (MT's "minimum spend in Malta"), the dynamic `fx_native_currency` mechanism is used so the program keeps auto-pricing from real project data. Where the threshold applies to a genuinely SEPARATE component (FR's VFX-specific spend, a real subset of QPE), a caller-evidenced native-currency fact (`amount_fact_key`) is used instead — never conflated.

---

## 4. A real, previously-latent bug found and fixed

`allocation_pricing.py`'s two floorless-ceiling guards checked `any(e.satisfied is None for e in rr.conditions_evaluated)` — this only caught UNRESOLVED conditions, never a condition that explicitly evaluates to a definite `False` (e.g. a numeric fact genuinely below its threshold). This was latent until `us_tx_miip`'s new numeric `amount_fact_key`-based gates (`gates_tier_eligibility=False`) were introduced, which genuinely CAN evaluate to `False`. Fixed both occurrences from `e.satisfied is None` to `e.satisfied is not True`, verified directly (a 20% resident-crew fact, below the 35% statutory minimum, now correctly blocks pricing that previously would have incorrectly succeeded).

---

## 5. Test-oracle discipline

No test was weakened, deleted, or skipped. Every changed candidate-count oracle is enumerated exactly:

- `test_canonical_served_wiring_repair.py::test_fvd_accounting_matches_codex_diagnosis` and `::test_fvd_unpriceable_causes_are_differentiated_not_flattened`: 295→292 total / 160→159 priced / 135→133 unpriced, directly measured by diffing FVD's real served candidate list before/after this remediation (matched by structure label, since `structure_id` is a fresh UUID per evaluation run).
- `test_canonical_authority_substrate.py::test_fvd_runtime_candidate_universe_restored`: same 295→292/160→159/135→133 reconciliation, independently re-derived.
- Full itemized delta for all four real projects: `GLOBAL_PROGRAM_CANDIDATE_UNIVERSE_DELTA_CLAUDE.csv`.

**Every one of these changes is attributable to exactly one program: `th_film_incentive`.** The other eight programs' fixes do not change any real project's candidate set (none of the four real projects had a candidate touching those programs' specific corrected gates). `th_film_incentive` previously resolved UNCONDITIONALLY (the exact defect Codex flagged), so every real project's "Full relocation to Thailand" candidate was incorrectly auto-priced; it now correctly requires evidenced preapproval + native-THB spend facts none of the four real projects supplies, so it correctly flips to disclosed-unpriced, and Thailand correspondingly drops out of the priceable component-routing-target set (removing the dependent, already-unpriced "routed to Thailand" component candidates entirely — never generated, per this codebase's existing convention that a component candidate which cannot price is never persisted).

All previously-passing alias (`test_b4_transitive_alias_gate.py`), fail-closed (`test_codex_final_canonical_incentive_acceptance.py`, `test_b4_authority_exhaustion_gate.py`), import-order (`test_import_order_integrity.py`), identity, and retirement tests are unmodified and pass.

---

## 6. Four real projects

Full detail: `GLOBAL_PROGRAM_FOUR_PROJECT_RECOMPUTATION_CLAUDE.csv`.

| Project | Before (total/priced/rejected) | After | Winner | Economics |
|---|---|---|---|---|
| The Little Utopia | 243/125/118 | 241/124/117 | No winner (pre-existing authority-unresolved gate, unchanged) | N/A |
| F#K Valentine's Day | 295/160/135 | 292/159/133 | No winner (pre-existing user-fact cultural gate, unchanged) | N/A |
| Bad Hombres | 240/123/117 | 238/122/116 | `us_nm_film_credit` (unchanged) | $596,910.25 gross / $1,885,112.75 NPC (byte-identical) |
| Lips Like Sugar | 297/176/121 | 294/175/119 | `ca_film_30` (unchanged) | $3,459,278.90 gross / $8,524,375.10 NPC (byte-identical) |

Per this workstream's explicit instruction, Little Utopia and F#K Valentine's Day were NOT forced to remain no-winner — both were recomputed fresh against the fully repaired canonical universe. Neither's no-winner status or reason changed: Little Utopia's pre-existing authority-unresolved qualification gate and FVD's pre-existing user-fact cultural gate (Greece's own 0/20 cultural-test points) are both entirely unrelated to any of the nine repaired programs, and neither gate's underlying facts were touched by this remediation. Bad Hombres' and Lips Like Sugar's winners and dollar economics are unchanged — only the underlying candidate count shrank (Thailand's now-correctly-gated candidates), with zero effect on their winning program stacks.

---

## 7. Closeout gates

- Nine Codex rows: **9/9 closed**.
- Twelve formulaic rules (the prior 11 + this workstream's re-verification): **12/12 reconciled**.
- Full-pipeline optimizer consumption: **12/12**.
- Alias gate: **PASS**. Fail-closed gate: **PASS**. Fresh-process import-order: **PASS**.
- Zero reachable stale runtime paths; zero unintended automatically-priced programs.
- Full backend suite: **4,863 passed / 3 skipped / 0 failed**.
- Four real projects execute through the canonical runtime (`evaluate_project` + `build_production_and_structures`, no fixtures/manual substitution).
- MFNI: unchanged.

---

## STATUS: IMPLEMENTED_PENDING_CODEX_FINAL_ACCEPTANCE

Claude does not grant final optimizer acceptance. Codex retains final acceptance authority and performs the delta-only independent reverification of these nine repaired rows.
