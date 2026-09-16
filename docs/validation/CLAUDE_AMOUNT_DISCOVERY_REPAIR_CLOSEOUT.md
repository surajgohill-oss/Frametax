# CLAUDE_GENERIC_AMOUNT_GATED_DISCOVERY_REPAIR

**Canonical branch:** `claude/optimizer-policy-finalization`
**Minimum required ancestor:** `12a0b7060c2fbb07622f65f24fbfd99c4348425e`
**Engine version:** `canonical-1.63.0` -> `canonical-1.64.0`

## The real defect, confirmed

`discover_executable_jurisdictions()` and `_price_candidate`'s own early preflight gate both required an `amount_fact_key`-gated numeric fact (e.g. `au_location_qape_aud`, `ma_ccm_qualifying_spend_mad`, `th_film_incentive_qualifying_spend_thb`) to already be present in `amount_facts` before a candidate was ever constructed. For every executable program in this defect class except `us_or_opif` (which had its own two-key special case), that fact was **never populated at all** — an absence, not a measured shortfall — so `resolve_program_rate()` always returned `None` at discovery, and the real per-candidate pricing pass (which correctly derives real amounts from real allocated spend) never ran.

Earlier artifacts in this program (`CLAUDE_126_EXECUTABLE_PRICING_PROOF.csv`, `CLAUDE_EIGHT_PROGRAM_THRESHOLD_MATRIX.csv`, `CLAUDE_THRESHOLD_ANCHOR_CLOSEOUT.md`) called `au_location_offset`/`ca_bc_dave`/`ma_ccm_rebate`/`th_film_incentive` `PRICED_RUNTIME_VERIFIED` or documented the gap as "not built this pass." Both were wrong in different ways: the "verified" label was based on manually injecting facts into an isolated `resolve_program_rate()` call, never the real pipeline; the "not built this pass" label incorrectly treated a real, fixable architecture defect as out-of-scope research. Both are corrected below.

## The fix, and why it is generic

1. **`app/data/program_rate_rules.py`** — new `build_discovery_amount_probe(slug, qpe_usd, amount_facts, fx_context)`. For every `amount_fact_key` referenced by a program's own rate rules that the caller hasn't already supplied, it seeds a generous, discovery-only probe from `qpe_usd`: currency-suffixed keys (`_aud`, `_mad`, `_thb`, `_usd`, ...) are converted via the canonical FX path (`_fx_native_amount`); a key with no recognizable currency (a day-count fact) gets a generic non-monetary placeholder, never a fabricated real value. A condition with `amount_fact_max` is skipped (a generous probe could spuriously violate an unknown cap). This function is keyed entirely off each program's own `RateRule.conditions` — it required **zero per-program code** to also fix `fr_trip` (discovered via the full-population census, not one of the four named programs).
2. **`app/calculators/production_discovery.py`** — `discover_executable_jurisdictions()`'s old `if slug == "us_or_opif": ...` special case is replaced by a call to `build_discovery_amount_probe()`, applied to every program uniformly. A new `fx_context` parameter is threaded through from both call sites in `canonical_evaluation.py`.
3. **`app/services/canonical_evaluation.py`** — the same generic probe replaces `_price_candidate`'s old `us_or_opif`-only preflight special case, seeded from `qpe` (this function's own real, per-jurisdiction qualifying total, already derived from the production's real budget lines — never a guess). Both `discover_executable_jurisdictions()` call sites (`feasibility_discovery`, `discovery`) now thread `fx_context=inputs.fx_context`.
4. **`app/calculators/allocation_pricing.py`** (`price_segment`) — the existing, pre-existing, already-correct `component_basis_line_components`/`component_basis_spend_categories` derivation (which already generically derives `ca_bc_dave_qualified_labour_usd`, `us_or_opif`'s two keys, and `za_nfvf_post_qsappe_usd` from real traced lines) is extended with a new `else` branch: a non-component-basis, currency-suffixed `amount_fact_key` is now derived from **this segment's own real `qpe`** (the same qualifying total the segment is about to be priced against) via the canonical FX path. A non-currency key (a day count) is deliberately left to a real caller-supplied `ProjectFact` — never guessed, so a genuine rejection stays genuine.
5. **`app/calculators/production_normalization.py`** — AUD, MAD, and THB were **entirely absent** from `_JURISDICTION_CURRENCY` (and therefore from `ALL_TRACKED_CURRENCIES` and `FX_RATE_SNAPSHOTS`), which is a separate, real, disclosed gap: the "canonical FX path" Task D explicitly asked for could not evaluate a THB threshold at all without it. `AU`/`MA`/`TH` -> `AUD`/`MAD`/`THB` added to `_JURISDICTION_CURRENCY`; static reference rates (disclosed as such, same pattern as the five pre-existing currencies) added to `FX_RATE_SNAPSHOTS` for all four existing snapshot dates.

No per-program branch was added for `au_location_offset`, `ca_bc_dave`, `ma_ccm_rebate`, or `th_film_incentive` individually — every one of the nine numbered required-architectural-behavior points is satisfied by the same generic mechanism, confirmed by `fr_trip` being fixed as a side effect with no code written for it.

## Per-program control disposition (Controls A-D)

- **A. `au_location_offset`**: the prior "already-correct QPE-probe" claim referred only to `us_or_opif`'s own special case — `au_location_offset` had no probe at all before this fix (confirmed, not assumed, by reading `production_discovery.py` directly). Now generically probed and priced; canonical AU QPE/threshold rules (`amount_fact_min=20,000,000` AUD) unchanged. None of the 4 real productions naturally clears the AUD 20,000,000 minimum (closest: Lips Like Sugar at ~AUD 18.2M); a controlled candidate at 2x that budget prices at $5,930,192.40 (30%).
- **B. `ca_bc_dave`**: DAVE's program classification/external authority status was not reopened. Its pre-existing `component_basis_spend_categories` derivation and dedicated stacking/base-interaction behavior are untouched. `tests/test_ca_bc_dave_component.py` re-run: 4/4 passing. Now PRICED for all 4 real productions (see runtime proof CSV).
- **C. `ma_ccm_rebate`**: both the MAD spend leg and the 18-shooting-day leg are treated as substantive structure requirements, never merged. The candidate is now genuinely constructed and evaluated for all 4 real productions (previously never attempted) and correctly reports `UNPRICEABLE_AUTHORITY_INSUFFICIENT` with a disclosed real reason, since none of the 4 productions' source schedules evidence >=18 Moroccan days — this is a real, disclosed rejection, not a phantom discovery-stage one. A controlled candidate with a real, caller-supplied `ma_ccm_shooting_days_count=20` `ProjectFact` prices at $2,965,096.20 (30%), proving the modeled-structure path works once the real fact is evidenced.
- **D. `th_film_incentive`**: THB tiers are tested via the canonical FX path (now that THB is a tracked currency). Guaranteed formulaic tier priced for all 4 real productions ($358,146.15-$2,470,913.50 depending on the tier reached); the committee-assessed Soft Power uplift remains a separate, disclosed, non-guaranteed ceiling, unaffected by this fix.

## Full-population prevention check

`CLAUDE_EXECUTABLE_AMOUNT_FACT_CENSUS.csv` lists all 11 `(program_slug, amount_fact_key)` pairs across every executable program's rate rules. Beyond the 4 named programs: `fr_trip_vfx_spend_eur` (fr_trip) is the same whole-segment-currency defect class, fixed generically with no extra code. `ma_ccm_shooting_days_count` and `us_tx_miip`'s two resident-percentage facts are non-monetary and correctly remain deferred to a real caller-supplied `ProjectFact` at pricing (discovery no longer blocks on their absence, but pricing never fabricates them). `ca_bc_dave_qualified_labour_usd`, `us_or_opif`'s two keys, and `za_nfvf_post_qsappe_usd` are component-basis facts already correctly derived by the pre-existing `price_segment` mechanism.

## Prior artifact corrections

- `CLAUDE_126_EXECUTABLE_PRICING_PROOF.csv`: the `PRICED_RUNTIME_VERIFIED` label for `au_location_offset`/`ca_bc_dave`/`ma_ccm_rebate`/`th_film_incentive` was based on a manually-supplied-fact isolated `resolve_program_rate()` call, never genuine pipeline proof — corrected via `CLAUDE_126_PROOF_CORRECTION_ADDENDUM_2026_09_15.md` rather than silently rewriting the original CSV's history.
- `CLAUDE_EIGHT_PROGRAM_THRESHOLD_MATRIX.csv` / `CLAUDE_THRESHOLD_ANCHOR_CLOSEOUT.md`: the `DISCOVERY_STAGE_AMOUNT_NOT_PROBED` / "not built this pass" language is superseded by this workstream's actual fix — a correction note is appended to the closeout file.
- `CLAUDE_PRE_RESEARCH_IMPLEMENTATION_CLOSEOUT.md`: its original "8 programs resolve correctly, no code changes required" claim (based on the same flawed manual-fact-injection methodology) is superseded by the real, genuine-pipeline proof in this workstream.

Corrections are appended as dated addenda to each file rather than rewriting the original text, so the history of what was claimed and when remains auditable.

## Regression proof

275 tests re-run across the directly-relevant suites, zero regressions, zero pre-existing failures introduced:

| Suite | Result |
|---|---|
| `tests/test_canonical_economics_integrity_repair.py` (+4 new prevention tests this workstream) | 53 passed |
| `tests/test_ca_bc_dave_component.py` | 4 passed |
| `tests/test_au_uk_copro_overview_wiring_claude.py` + `tests/test_canada_validation.py` + `tests/test_component_rejection_persistence.py` + `tests/test_ny_nm_or_validation.py` | 132 passed |
| `tests/test_hybrid_anchor_relationship_types.py` + `tests/test_coproduction_optimizer_preservation.py` + `tests/test_treaty_coproduction.py` + `tests/test_treaty_coproduction_wiring.py` | 86 passed |

Anchor economics: not touched by this workstream's code changes (no anchor-contract code was edited); the four real productions' anchor figures are computed by a code path (`compute_anchor_budget_contract`) entirely separate from `discover_executable_jurisdictions`/`price_segment`.

## Fresh evaluation of the 4 real productions

All 4 re-evaluated fresh at `canonical-1.64.0` (cache invalidated for the prior version, `EVALUATION_COMPLETE`/`EVALUATION_REUSED` at the new fingerprint). Full detail in `CLAUDE_AMOUNT_GATED_RUNTIME_PROOF.csv`. V-BRAT was not evaluated (not a production); Underwater was not touched (out of scope).

## Status

`READY_FOR_INDEPENDENT_STACKING_AND_CALCULATION_AUDIT` — all four named programs now reach real candidate allocation and threshold evaluation via one generic mechanism (proven by `fr_trip` being fixed as a side effect); no executable amount-gated program is rejected merely because its post-allocation amount was unavailable during discovery; DAVE's established behavior is unchanged and re-verified; prior overstated verification language is corrected via dated addenda; 275 focused regression tests pass; branch committed, pushed, and clean.
