# Little Utopia Worldwide Runtime Acceptance

Date: 2026-08-14
Branch: `claude/audit-frametax-features-NZcX5`
Entry gate: `GO_FOR_LITTLE_UTOPIA_WORLDWIDE` (verified from `docs/validation/GLOBAL_DATA_APPLICATION_VERIFICATION.json` on `origin`)
Companion artifact: `LITTLE_UTOPIA_WORLDWIDE_ACCEPTANCE.json`

## Project & runtime identity

Production: **The Little Utopia** — gross budget **$4,364,393** (authoritative top-sheet total; the 44-account leaf sum is $4,364,395, a pre-existing $2.00 rounding variance, disclosed in-runtime). Served path: `frontend → app/api/v1/cineglobe.py → little_utopia_state.build_allocated_structures() → production_discovery → production_allocation → allocation_pricing.price_segment → rank_allocated_structures → bridge/package_builder`. In-memory, DB-free, zero mocks.

## Global universe integrity

| | Count |
|---|---:|
| Canonical remediation records | 176 |
| Coverage registry rows | 249 (grew from 247 during this run — see AC-1/AC-2) |
| Priceable-validated runtime programs | 33 |
| Authority-insufficient | 212 |
| Non-guaranteed selective | 25 |
| Non-economic | 5 |
| Superseded | 3 |
| Duplicate | 1 |
| Canonical data handoff defect | 3 |
| Executable runtime profiles (total) | 110 |
| Treaty instruments (bilateral / multilateral) | 26 / 3 |
| Generated structures | 177 |
| Priced structures | 48 (post-fix; was 50 before AC-1/AC-2 blocked Japan and Kazakhstan) |

**Forbidden intersections — all empty**: authority-insufficient ∩ priced = ∅; authority-insufficient ∩ ranked = ∅; non-economic ∩ priced = ∅; superseded ∩ priced = ∅; duplicate ∩ priced = ∅; non-guaranteed-selective ∩ priced = ∅.

## Candidate accounting

177 generated = 48 priced + 129 rejected. Every rejection carries a recorded reason: 120 on canonical coverage (a program the completed corpus disabled), 9 on a minimum-spend/QPE gate. Structure families: `single_country` (1), `full_relocation` (88), `component_relocation` (88) — the currently-supported worldwide universe, no deferred engine invoked.

Ranking is strictly ascending by `npc_with_adjustments_usd` and rank-contiguous across all 48 priced structures.

## Top 20 (post-fix)

| Rank | Structure | Type | Programs | Gross cost | QPE | Gross incentive | NPC | Savings vs MU |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 1 | `ALLOC-BASELINE-MU` | single country | MU · `mu_edb_incentive` | $4,364,393 | $4,355,327 | $1,306,598 | **$3,057,794.90** | $0 |
| 2 | `ALLOC-COMPONENT-POST-CA-NL` | component relocation | CA-NL · `ca_nl_all_spend_credit`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,315,475 | $3,673,917.70 | −$616,123 |
| 3 | `ALLOC-COMPONENT-POST-SG` | component relocation | MU · `mu_edb_incentive`, SG · `sg_made_with_singapore_rebate` | $4,364,393 | $4,364,395 | $1,315,475 | $3,673,917.70 | −$616,123 |
| 4 | `ALLOC-COMPONENT-POST-QA` | component relocation | MU · `mu_edb_incentive`, QA · `qa_screen_production_incentive` | $4,364,393 | $4,364,395 | $1,315,475 | $3,673,917.70 | −$616,123 |
| 5 | `ALLOC-COMPONENT-POST-MX` | component relocation | MU · `mu_edb_incentive`, MX · `mx_federal_film_incentive_2026` | $4,364,393 | $4,364,395 | $1,309,318 | $3,680,074.50 | −$622,280 |
| 6 | `ALLOC-COMPONENT-POST-TW` | component relocation | MU · `mu_edb_incentive`, TW · `tw_bamid_rebate` | $4,364,393 | $4,364,395 | $1,309,318 | $3,680,074.50 | −$622,280 |
| 7 | `ALLOC-COMPONENT-POST-EG` | component relocation | EG · `eg_empc_cashback`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,309,318 | $3,680,074.50 | −$622,280 |
| 8 | `ALLOC-COMPONENT-POST-IL` | component relocation | IL · `il_foreign_production_fund`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,309,318 | $3,680,074.50 | −$622,280 |
| 9 | `ALLOC-COMPONENT-POST-CA-QC` | component relocation | CA-QC · `ca_qc_pstc`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,306,240 | $3,683,152.90 | −$625,358 |
| 10 | `ALLOC-COMPONENT-POST-PT` | component relocation | MU · `mu_edb_incentive`, PT · `pt_scri_pt_cash_rebate` | $4,364,393 | $4,364,395 | $1,306,240 | $3,683,152.90 | −$625,358 |
| 11 | `ALLOC-COMPONENT-POST-DK` | component relocation | DK · `dk_production_rebate`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,306,240 | $3,683,152.90 | −$625,358 |
| 12 | `ALLOC-COMPONENT-POST-UA` | component relocation | MU · `mu_edb_incentive`, UA · `ua_cash_rebate` | $4,364,393 | $4,364,395 | $1,306,240 | $3,683,152.90 | −$625,358 |
| 13 | `ALLOC-COMPONENT-POST-ZA` | component relocation | MU · `mu_edb_incentive`, ZA · `za_dtic_foreign_film` | $4,364,393 | $4,364,395 | $1,306,240 | $3,683,152.90 | −$625,358 |
| 14 | `ALLOC-COMPONENT-POST-CH` | component relocation | CH · `ch_pics_national_rebate`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,303,162 | $3,686,231.30 | −$628,436 |
| 15 | `ALLOC-COMPONENT-POST-GE` | component relocation | GE · `ge_film_rebate`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,303,162 | $3,686,231.30 | −$628,436 |
| 16 | `ALLOC-COMPONENT-POST-GH` | component relocation | GH · `gh_film_tax_incentive`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,303,162 | $3,686,231.30 | −$628,436 |
| 17 | `ALLOC-COMPONENT-POST-PH` | component relocation | MU · `mu_edb_incentive`, PH · `ph_fdcp_flip` | $4,364,393 | $4,364,395 | $1,303,162 | $3,686,231.30 | −$628,436 |
| 18 | `ALLOC-COMPONENT-POST-AU-QLD` | component relocation | AU-QLD · `au_qld_pdv_rebate`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,300,083 | $3,689,309.70 | −$631,515 |
| 19 | `ALLOC-COMPONENT-POST-CR` | component relocation | CR · `cr_tax_return_incentive`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,298,052 | $3,691,341.44 | −$633,547 |
| 20 | `ALLOC-COMPONENT-POST-AU-NSW` | component relocation | AU-NSW · `au_nsw_pdv_rebate`, MU · `mu_edb_incentive` | $4,364,393 | $4,364,395 | $1,297,005 | $3,692,388.10 | −$634,593 |

Effective rates across all 48 priced structures cluster tightly at **29.7%–30.1%** — no outlier, no impossible rate, no ranking discontinuity.

## Winner

**`ALLOC-BASELINE-MU`**, Mauritius single-jurisdiction baseline, **NPC $3,057,794.90** — the worldwide optimizer independently confirms the calibrated baseline as the lowest defensible net cost; it was not forced.

## Mauritius regression

Byte-identical to the established figure. QPE $4,355,327 (register total $4,364,395 minus the $9,068 intentionally non-claiming US/LA post segment — `program_slug=None`, `claims_incentive=False`, `qpe_usd=0`). Rate: 30% guaranteed floor, 40% discretionary ceiling (`is_band_ceiling=True`, `ceiling_requires_confirmation=True`) — floor prices. $4,355,327 × 30% = $1,306,598.10; $4,364,393 − $1,306,598.10 = **$3,057,794.90**.

The $2,846,357 pre-remediation QPE reference is explained, not a regression: it predates the canonical default-inclusion fix (silence is not exclusion) that this project's own rules require.

## QPE / territoriality / hard-gate / conditional acceptance

- **QPE**: every budget line included unless authority expressly excludes it; zero conservative engine-convention exclusions applied to Little Utopia's 44 accounts (35 qualify, 7 excluded — all US/LA post — 2 grey-area).
- **Territoriality**: the $9,068 US post spend is excluded from MU's QPE even though the structure is a single MU-anchored entity — foreign spend does not qualify by virtue of the anchor, and local-SPV/payment routing alone was proven insufficient in the preceding phase.
- **Hard gates**: Australia's A$20M QAPE gate correctly blocks at Little Utopia's $4.36M QPE and correctly resolves at a $12M QPE fixture — the threshold binds on QPE, not on absent data.
- **Conditional/discretionary**: 24–25 `NON_GUARANTEED_SELECTIVE` programs contribute zero guaranteed value; Mauritius's and (post-fix) Thailand's discretionary ceilings require confirmation and never price as guaranteed.

## Treaty / co-production acceptance

Mauritius has **zero** reachable treaty partners — proven exhaustively at runtime (no bilateral treaty with any profiled jurisdiction; not a European Convention signatory, Eurimages member, or Ibermedia member), not assumed. `treaty_coproduction` candidates are auto-enumerated from the real registry with no manual election required; the empty MU set is a genuine zero, surfaced with a stated reason in the coverage report, not a generation defect. The three-way separation (treaty exists / valid co-production structure / domestic incentive eligibility) is preserved throughout.

## API / Bridge acceptance

For the top 10 ranked structures: `optimizer npc_with_adjustments_usd == ranking npc == Bridge economics.npc_usd`, 0 mismatches. No pre-adjustment field leaks into external output (`npc_verified_usd` is exported separately, clearly named).

## Defects found and fixed (all VERIFIED)

| ID | Severity | Defect | Fix |
|---|---|---|---|
| **AC-1** | P0 | Japan's competitive, capped half-subsidy (`jp_vipo_location_incentive`) priced as a guaranteed flat 50%, ranking #2 with a $2.03M incentive — 55% larger than any other candidate — because it shared its 50% figure with a different canonical slug (`jp_film_incentive`, explicitly marked competitive/selective/not-guaranteed) that the runtime program was never bound to. | Bound both spellings via `authority_coverage_registry.CANONICAL_RUNTIME_SLUG_BINDINGS`; `jp_vipo_location_incentive` now `NON_GUARANTEED_SELECTIVE`, blocked from pricing. |
| **AC-2** | P0 | Kazakhstan (`kz_investment_subsidy`) priced a flat 30% sourced to a single uncorroborated secondary source, while the canonical adjudication for the same program (`kz_film_incentive`) is authority-insufficient on directly conflicting sources. | Bound both spellings; `kz_investment_subsidy` now `UNPRICEABLE_AUTHORITY_INSUFFICIENT`. |
| **AC-3** | P1 | Thailand (`th_boi_incentive`) priced its canonical **maximum** (30%) as a flat guaranteed rate; the canonical record states a 15% base with 30% reachable only via non-summable uplift criteria. | Split `TH_DOCTRINE` into a 15% guaranteed floor and a 30% `discretionary_band` ceiling requiring confirmation — the same mechanism already proven for Mauritius and Malta. |

All three share one root cause: a headline maximum encoded as guaranteed. A generalized regression test (`test_no_still_priceable_program_encodes_an_up_to_maximum_as_a_flat_rate`) now scans every still-priceable program for the same pattern.

## Anomaly review

Impossible effective rate: **none after fixes** (all 48 priced structures 29.7%–30.1%). Benefit exceeding eligible spend, missing cap, unsupported uplift, blocked/superseded/duplicate leakage, treaty misuse, foreign-spend misqualification, zero/negative NPC, duplicate structure aliasing: **none found**. The large rank-1-to-2 discontinuity present before the fix (driven entirely by the Japan anomaly) is gone. Absence of Ireland, UK, France, Italy, Spain, Germany, Canada-federal, California, Georgia and others from the ranked set is explained — the completed canonical corpus adjudicated them authority-insufficient in the preceding phase, not a generation defect.

## Regression protection

`tests/optimization/test_little_utopia_worldwide_acceptance.py` (12 tests): the three named defects, the generalized "up to X as flat rate" class check, blocked-program non-leakage, candidate accounting reconciliation, ranking monotonicity, the full Mauritius regression (including the non-claiming US segment), the Australia hard gate at both sides of its threshold, the Mauritius treaty proven-zero, Bridge/optimizer/ranking consistency for the top 10, and an impossible-effective-rate guard.

Full backend suite: **4031 passed, 1 skipped, 1 pre-existing unrelated failure** (frontend `Workspace.jsx` title-formatter guard, zero local diff on that file).

## Remaining blockers

- **P1** (carried forward, unaffected by this run): 3 `CANONICAL_DATA_HANDOFF_DEFECT` records (BC FIBC, German GMPF, India NFDC) still need a canonical identity binding. Fails safe; none appears in the Little Utopia candidate set.
- **P2** (partially resolved): the two identity ambiguities that materially contaminated the ranking (Japan, Kazakhstan) are fixed. A small remainder (Denmark, Portugal, Panama, Costa Rica, Mexico, Thailand PRD) is not in the top 20 and could not be adjudicated from the payload without inventing an equivalence.

Neither is a P0 deterministic correctness defect.

## Gate

**`GLOBAL_OPTIMIZER_RUNTIME_ACCEPTED`**
