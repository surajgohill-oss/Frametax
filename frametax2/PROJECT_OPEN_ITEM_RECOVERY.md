# PROJECT OPEN-ITEM RECOVERY — US / Canada / Mexico calculation scope

Created 2026-10-10 (Claude). Code and tests for F-01..F-07 are committed as `486bd15` (engine `canonical-1.107.0`, rate rules 1.5.1, parser 1.5.1); this file and the register/ledger edits are uncommitted by instruction. The Greece reconstruction is in `docs/validation/FVD_GREECE_QPE_INDEPENDENT_RECONSTRUCTION.md` (register Q36-Q41). **Calculation acceptance: OPEN.** Nothing in this document is an acceptance claim: every status below is `FIXED_IN_CODE_UNREGENERATED`, `OPEN`, `CLARIFIED`, `DISPROVED` or `OUT_OF_SCOPE`. No production was regenerated or evaluated in this task, no served surface was re-read after the code changes, and the legal inputs are the program records already retained in the repository (no new external research). Findings are also recorded in the single issue register (`docs/validation/FOUR_ANCHOR_QPE_ISSUE_REGISTER.md`, rows Q24-Q35); this file is the working detail.

## 1. Frozen scope and constraints

- **Inventory (frozen at task start from the live canonical registry):** 45 doctrine records — 30 US (federal-state programs incl. `ca_film_30`), 14 Canada (2 federal, 12 provincial), 1 Mexico. Table in section 6. Greece (all) and New York (`ny_state_film`, `us_ny_post_production_credit`) are AG's/Codex's tracks and are listed but not re-reconciled here.
- **Budgets:** Little Utopia (LU), F#K Valentine's Day (FVD), Bad Hombres (BH), Lips Like Sugar (LLS) — original PDFs, saved generations canonical-1.106.0 (`40527fdc3adf`, `3759a2edf4b4`, `8823b547e4b6`, `0c645952931c`), read-only.
- **Hard constraints honoured:** no regeneration, no cold evaluation, no acceptance database mutation, no external research, no invented inputs; the user's uncommitted `PROJECT_RULES.md` and ledger edits untouched; the ledger is not edited (INDEPENDENT UI COMPLETION GATE rule 13: ledger only on explicit request).
- **Evidence classes:** `SAVED` = read-only saved generation (comparison only, never an expected value); `SOURCE` = original PDF text / retained citation; `ARITH` = explicit sums over source lines; `SYNTHETIC` = isolated controls with invented amounts and no database.

## 2. Four-budget trace — anchors (source category → contingency → QPE → rate/cap/uplift → incentive → NPC)

Anchors were reconciled by identity in the previous task (ledger 2026-10-10 section); the table restates them with this task's additions. QPE here is the program's confirmed base; conditional amounts are outside floor and maximum (see F-12).

| Budget (program) | Gross (declared) | Excluded | Conditional | QPE | Rate floor/max | Incentive floor / max | NPC floor / max |
|---|---|---|---|---|---|---|---|
| LU (MU EDB) | 4,364,393 (lines 4,364,395) | stated-outside editorial 9,068 | 7100 PUBLICITY 24,348 | 4,330,979 | 30% / 40% | 1,299,293.70 / 1,732,391.60 | 3,065,099.30 / 2,632,001.40 |
| FVD (GR) | 4,517,687 | contingency 362,866; finance 453,583 N/A; 80%-of-gross cap 87,088.40 | — | 3,614,149.60 | 40% / 40% | 1,445,659.84 / same | 3,072,027.16 / same |
| BH (NM) | 2,482,023 | contingency 94,382 | SAG deposit 60,000 | 2,327,641 | 25% / 40% (+10 rural, +5 facility on all QPE) | 581,910.25 / 931,056.40 | 1,900,112.75 / 1,550,966.60 |
| LLS (CA) | 11,983,654 | ATL excluded portions 2,508,031; residuals 400,000; contingency 400,000; finance 1,700,000 N/A | ATL mixed 181,739; ATL fringes 255,291; legal 150,000 | 6,388,593 | 35% / 41.859% | 2,236,007.55 / 2,674,197.00 | 9,747,646.45 / 9,309,457.00 |

**Contingency election (project fact).** Only LU carries a project election (100%, source `recovered_demo_state`, user-reviewed): it applies solely where a program's own rule says the contingency category qualifies (Mauritius), adding 301,131 to LU's MU QPE (floor +90,339.30, maximum +120,452.40; a labelled projection, not incurred cost). Every US/Canada/Mexico program, and BH/FVD/LLS everywhere, uses the canonical default (undeployed reserve excluded until deployed) — consistent, not a defect. LU's US/CA/MX alternatives therefore exclude the 301,131.

## 3. Independent source-derived expectations for the US/Canada/Mexico alternatives

Expectation = explicit sums over the original source lines and the categories the retained rules name; the engine row is the SAVED comparison.

| Alternative (program) | Budget | Independent expectation (ARITH) | SAVED engine QPE | Match |
|---|---|---|---|---|
| California 4.0 (`ca_film_30`) | LU | 4,364,395 − 301,131 contingency − 9,068 stated-outside − 141,165 ATL (1100 5,050 + 1400 136,115, mixed) = 3,913,031 | 3,913,031 | exact |
| | FVD | 4,517,687 − 453,583 finance − 362,866 contingency − 1,976,479 ATL (252,650 + 401,831 + 75,710 + 1,246,288) = 1,724,759 | 1,724,759 | exact |
| | BH | 2,482,023 − 94,382 − 1,448,902 ATL (74,531 + 267,169 + 75,000 + 1,032,202) − 60,000 residual deposit (excluded) − 24,000 legal (mixed) = 854,739 | 854,739 | exact |
| | LLS | 11,983,654 − 1,700,000 − 3,308,031 − 587,030 = 6,388,593 | 6,388,593 | exact |
| Open-default state/provincial/Mexico base (e.g. `us_nm_film_credit`, `mx_federal_film_incentive_2026`) | LU | 4,364,395 − 301,131 − 9,068 = 4,054,196 | 4,054,196 | exact |
| | FVD | 4,517,687 − 453,583 − 362,866 = 3,701,238 | 3,701,238 | exact |
| | BH | 2,482,023 − 94,382 − 60,000 (conditional) = 2,327,641 | 2,327,641 | exact |
| | LLS | 11,983,654 − 1,700,000 − 400,000 − 400,000 (residual reserve, conditional) = 9,483,654 | 9,483,654 | exact |

These match the engine's QPE; they do not establish legal QPE (territorial, payee and application facts are absent, F-13). The uplift maxima were re-derived for the anchors: BH maximum = 0.25·2,327,641 + 0.15·2,327,641 (rural 10 + facility 5, every line assumed eligible); LLS maximum = 0.35·6,388,593 + 0.05·6,388,593 + 0.10·1,167,598 (resident-wage lines 3100/4900/5900) + 0.05·40,000 (VFX), with the whole-QPE assumption for outside-zone — both are upper bounds on unevidenced line predicates.

## 4. Findings

Fields: evidence → expected vs observed → impact → owner → status → next action. "Live" impact needs a separately authorized regeneration; engine/rules versions moved (rate rules 1.5.1, parser 1.5.1) so all four fingerprints are stale by digest once the backend restarts (the running backend still holds the old digest; do not restart it before authorization).

| ID | Finding | Evidence | Expected vs observed | Impact on the four budgets | Owner | Status / next action |
|---|---|---|---|---|---|---|
| F-01 | New Brunswick 30% feature tier flagged as a discretionary band ceiling although its only condition (production type) is satisfied | SAVED CA-NB rows: segment floor 25% while structure `confirmed_incentive_floor` / NPC use 30% (`ceiling_requires_confirmation` False); doctrine comment says "not a discretionary band"; SYNTHETIC probe | one rate (30% for a feature) vs a 25% floor under a 30% confirmed figure | NPC already used 30%; segment/floor fields understated (e.g. BH 581,910 vs 698,292; LLS 2,370,914 vs 2,845,096). No NPC change | rate rules | FIXED_IN_CODE_UNREGENERATED (flag; control + mutant). NB's registry disposition is `AUTHORITY_UNRESOLVED_NON_PRICEABLE` (one secondary source): it still prices on its retained rate data but cannot be recommended or treated as knowledge-verified |
| F-02 | Connecticut and North Carolina USD thresholds had an EUR→USD factor applied | Citations quote $100,000/$500,000/$1,000,000 (CT, DECD) and $1.5 million (NC, commerce.nc.gov); stored 113,710.79 / 568,553.96 / 1,137,107.92 and 1,713,710.79 | tiers at the quoted dollars | none for the four budgets (all QPE ≥ 2.3m); latent: a 1.05m CT QPE priced 15% instead of 30% | rate rules | FIXED_IN_CODE_UNREGENERATED (control derives the figures from the citation text; recurrence guard: every `US-` threshold is a whole thousand) |
| F-03 | North Carolina "up to 25%" priced a CONFIRMED 25% floor while Maryland and South Carolina (same wording) were blocked | record's own note: "'up to 25%' is a discretionary ceiling ... same treatment as other 'up to' programs"; tier had only the satisfied min-spend gate so the floorless-ceiling guard never fired; SAVED: US-NC PRICED in all four generations | blocked as ceiling-only like MD/SC | after regeneration US-NC leaves the priced ranking for all four (saved floors LU 1,013,549; FVD 925,310; BH 581,910; LLS 2,370,914) | rate rules | FIXED_IN_CODE_UNREGENERATED. Product question left open: whether a ceiling-only program should show as a conditional opportunity rather than non-executable |
| F-04 | Rhode Island per-project cap USD 7m never applied (doctrine said "not modeled by this schema") | doctrine citation_detail "per-project cap $7,000,000"; SAVED: only the 40m annual fund reported | credits capped at 7m | none for the four (largest RI floor 2,845,096) | rate rules | FIXED_IN_CODE_UNREGENERATED (conservative cap; waiver stays an unmodeled disclosed condition) |
| F-04b | Louisiana annual fund: doctrine 150m (official page, secondary 125m explicitly rejected) vs requirements profile 125m (2025 reform) | both records argue their figure in their own notes | one figure | none (fund-level bound far above any single award) | authority research (explicit request only) | OPEN, documented; recurrence guard allow-lists exactly this conflict |
| F-05 | Mexico: per-project cap (MXN 40m), minimum spend (MXN 40m) and MXN tracking absent; profile text called the MXN 400m an envelope "not an annual appropriation" while the Decreto text read in the doctrine record says ANNUAL | doctrine citation / provenance; profile `per_project_cap`, `min_local_spend`; SAVED: MX priced uncapped, no minimum gate, MXN absent from the FX table | capped, gated, fail-closed without a rate | LLS MX floor 2,845,096 exceeds MXN 40m whenever MXN/USD > 14.06 (= 40,000,000 / 2,845,096); minimum spend met only if MXN/USD ≥ 9.87 (LU), 10.81 (FVD), 17.18 (BH), 4.22 (LLS) — no MXN rate is on file, none assumed | rate rules, FX | FIXED_IN_CODE_UNREGENERATED (native caps via the canonical FX context; unavailable rate fails closed). OPEN: the per-project figures rest on law-firm summaries (the Decreto defers them to Lineamientos not yet read); the 70% national-supply gate, per-format minimums for non-feature work and the 85% transfer valuation are unmodeled |
| F-06 | Stack candidates took qualifying spend from a register that ignored stated-outside accounts | SAVED LU: Ontario/BC stacks QPE 4,063,264 (includes the US-located editorial 9,068) vs single-program Quebec/New Brunswick 4,054,196 | one QPE for the same lines | LU Canadian stacks overstated by 9,068 of QPE (incentive effect = 9,068 × the stack's effective rate, not computed); FVD/BH/LLS carry no stated-outside accounts | canonical_evaluation | FIXED_IN_CODE_UNREGENERATED (register aligned to the allocation; synthetic `_price_candidate` control + mutant) |
| F-07 | Movie Magic detail matcher required a hyphenated parent heading; LU and BH exports use `CODE  DESCRIPTION` and an un-numbered "Total Fringes" sub-line, so zero detail was captured (Codex PAR-A01) | SOURCE replay of the four PDFs, before/after: LU 0 → 41 accounts, BH 0 → 33, LLS 41 (40 conserving, unchanged), FVD 0 (one-page topsheet; genuinely no detail); every new group's children sum to the authored `Account Total for` | detail captured and conserving | after a budget refresh the California relocation can split LU/BH ATL accounts by authored line instead of treating whole accounts as mixed (not computed here); gross, line counts and sums unchanged | budget_parser | FIXED_IN_CODE_UNREGENERATED (parser 1.5.1; 4 synthetic controls + 3 mutants). Needs the canonical refresh + authorized regeneration to reach served data |
| F-08 | Cap families for California/New Mexico (carried from the previous task) | see ledger 2026-10-10 section | — | — | — | CLARIFIED: annual fund vs project cap vs QE limit are separate fields; independent CA/NM QPE expectations match (section 3) |
| F-09 | Washington: doctrine annual fund 3.5m (secondary aggregator) vs primary Washington Filmworks PIP guidelines 15m | profile evidence (PRIMARY, rev. 2025-06-24) vs doctrine citation (greenslate.com) | primary figure | SAVED LLS US-WA maximum was clipped at 3,500,000 (clip 767,644); after the correction it is 45% × 9,483,654 = 4,267,644 — **but the 45% ceiling itself is unsupported by the primary fact sheet ("up to 30%"), recorded unresolved in the profile** | rate rules / authority research | annual fund FIXED_IN_CODE_UNREGENERATED. OPEN: 45% ceiling and the two-Washington-residents gate (writer/director/producer/lead actor) are not modeled; needs the full PIP Guidelines PDF (a bounded single-proposition retrieval, only on explicit request) |
| F-10 | Per-person limits recorded but not applied: GA USD 500,000 (salary per individual), IL USD 500,000 per worker (resident and non-resident), MA USD 1,000,000 payroll *exclusion* threshold (the employee's payroll is excluded entirely) | profile `per_person_cap_usd` and its notes; grep: only the demo state and the opportunity bridge read it; SAVED GA/IL/MA rows price every ATL account fully | per-payee treatment | upper bounds on possible overstatement (ATL amount above the cap × base rate): FVD GA 149,258 / IL 261,201 / MA 61,572; BH 106,440 / 186,271 / 8,050; LLS 255,517 / 447,155 / 103,550; LU 0 — bounds only; per-payee compensation is not in any topsheet | spend rules | OPEN: semantics differ (cap vs exclusion) so a generic implementation needs a semantic field plus payee-level evidence; design recorded, not implemented to avoid inventing a split |
| F-11 | Floorless "up to" programs: MD and SC blocked, NC (F-03) now consistent; Singapore (`sg_made_with_singapore_rebate`) has the same unconditional band tier outside this scope | SYNTHETIC probe; doctrine scan | consistent | none | rate rules | MD/SC CLARIFIED; SG OUT_OF_SCOPE follow-up |
| F-12 | Conditional (grey) accounts appear in neither the floor nor the maximum nor any served opportunity: `maximum` is defined as floor + rate-tier uplift (`ceiling_basis.note`), and LU's `legal.grey_areas_current` is empty | SAVED: LU 7100 24,348, BH 1600 60,000, LLS 587,030 of QPE only in the segment `qualification_trace` / `unresolved_usd` | headline figures that disclose conditional-account upside | bounds at maximum rates: LU ≈ 9.7k, BH ≈ 24.0k, LLS ≈ 0.25m | pricing / product owner | CLARIFIED (design definition, not a miscalculation); OPEN as a disclosure decision: surface a labelled "conditional-account upside" or leave to the trace |
| F-13 | No per-account territorial, payee-residency, withholding or application-date evidence for any project | all four budgets; register Q10 | evidence-based locality | every non-excluded account is presumed local in every program | producers | OPEN / NOT_ESTABLISHED (no placeholder supplied) |
| F-14 | Canadian stack mechanics (CPTC base net of provincial credit; QC/ON/BC pairs) | SAVED BH Quebec stack: CPTC 224,048.94 = 25% × (labour basis 1,478,106 − Quebec credit 581,910.25); Quebec credit = 25% × QPE | independent labour basis | identities hold; the Canadian labour basis (CLE) is not derivable from a topsheet | stacking / labour basis | OPEN: not independently re-derived; rules are registry-verified, not re-researched |

## 5. Verification run (this task)

- `tests/test_us_ca_mx_scope_integrity_controls.py` — 19 passed (SYNTHETIC, no database). Mutants killed: NB re-flagged band, CT tier-15 and NC thresholds re-converted, NC discretionary condition removed, RI cap dropped, MX cap dropped, MX minimum weakened, MXN untracked, stack register ignoring stated-outside, WA stale fund restored (a first CT mutant used the wrong pattern and did not bite; it was replaced by two exact ones).
- `tests/test_movie_magic_nohyphen_detail_controls.py` — 4 passed; mutants killed: hyphen-only heading, removed prefix guard, fringe amount not captured.
- Existing, DB-free: parser group (`test_budget_parser_text`, `_xlsx`, `test_movie_magic_budget_parser`, `test_budget_netting_independent_controls`) 82 passed (the group was run twice because the first summary line was cut — a green rerun, 1.3 s); `test_canonical_identity_authority_invariants` + `test_program_intelligence_population` + `test_prompt16_authority_disposition` 426 passed, 2 failed; `test_b3_formulaic_consumption` + `test_structural_archetype_generator` 65 passed, 2 failed.
- **Four failures investigated and attributed:** `test_historical_source_ids_confirmed_this_pass_cannot_price_independently` (Bulgaria alias carries survivor rate rules), `test_authority_vetoed_dormant_rules_cannot_create_guaranteed_candidates` (ae_ad_film_rebate not vetoed), `test_th_film_incentive_prices_independently_of_th_boi_incentive`, `test_za_nfvf_rebate_prices_independently_of_za_dtic_foreign_film` — all fail identically on a pristine `d0e01e2` worktree, so they are pre-existing and outside US/Canada/Mexico (OUT_OF_SCOPE, owner authority/identity owner; registered Q33).
- **Not run (hazard, per LONG-RUNNING PROCESS DISCIPLINE):** every file that evaluates or reads a real production or needs the shared database (`test_canonical_economics_integrity_repair`, `test_canonical_project_economics`, `test_canonical_authority_substrate`, `test_claude_global_optimizer_p0_remediation`, `test_copro_*`, `test_oregon_full_db_pipeline`). The F-06 change in `canonical_evaluation._price_candidate` therefore has only its new synthetic control plus the DB-free files above.
- Passing controls close nothing: Q10/Q11/Q15/Q16-Q22 and F-10/F-12/F-13/F-14 stay open.

## 6. Scoped inventory (45 programs, frozen)

Columns: registry confidence tier; registry authority disposition; tier rates (`*` = band ceiling); cap fields present; finding reference. `AUTHORITY_VERIFIED_PRICEABLE` is the registry's label and is not an independent verification. Reconciliation depth for programs with `-` in the last column: mechanical consistency only (rate vs quoted percentages, thresholds whole USD, doctrine-vs-profile caps, band-ceiling conditions, QPE arithmetic on the saved best-per-jurisdiction rows); no program-specific legal re-derivation was performed.

| Program | Jurisdiction | Tier | Authority disposition | Rate tiers % | Caps | Findings |
|---|---|---|---|---|---|---|
| ca_federal_cptc | CA | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25 | - | - |
| ca_federal_pstc | CA | PARSED | AUTHORITY_VERIFIED_PRICEABLE | 16 | - | - |
| ca_ab_fttc | CA-AB | PARSED | AUTHORITY_VERIFIED_PRICEABLE | 22/30* | - | - |
| ca_bc_dave | CA-BC | PARSED | AUTHORITY_VERIFIED_PRICEABLE | 16 | - | - |
| ca_bc_pstc | CA-BC | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 36/48* | - | - |
| ca_mb_film_video_credit | CA-MB | PARSED | AUTHORITY_UNRESOLVED_NON_PRICEABLE | 45/65* | - | - |
| ca_nb_film_tax_credit | CA-NB | PARSED | AUTHORITY_UNRESOLVED_NON_PRICEABLE | 25/30 | - | F-01 |
| ca_nl_all_spend_credit | CA-NL | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 40 | annual 20M | - |
| ca_ns_production_incentive_fund | CA-NS | PARSED | AUTHORITY_UNRESOLVED_NON_PRICEABLE | 25 | - | - |
| on_ofttc | CA-ON | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 35 | - | - |
| on_opstc | CA-ON | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 21.5 | - | - |
| ontario_computer_animation_and_special_effects_tax_credit_ocase | CA-ON | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 18 | - | - |
| ca_qc_pstc | CA-QC | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25 | - | - |
| ca_sk_creative_saskatchewan_grant | CA-SK | PARSED | AUTHORITY_UNRESOLVED_NON_PRICEABLE | 25/30* | annual 5M | - |
| mx_federal_film_incentive_2026 | MX | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 30 | native MXN 40M | F-05 |
| us_al_film_incentive | US-AL | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25/35/45* | annual 22M | - |
| us_az_motion_picture_production | US-AZ | PARSED | AUTHORITY_UNRESOLVED_NON_PRICEABLE | 15/20* | - | - |
| ca_film_30 | US-CA | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 35/40* | annual 750M, QE limit | F-08 |
| us_co_film_incentive | US-CO | PARSED | AUTHORITY_UNRESOLVED_NON_PRICEABLE | 20 | - | - |
| us_ct_film_tax_credit | US-CT | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 10/15/30 | - | F-02 |
| us_ga_film_credit | US-GA | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 20/30* | - | F-10 |
| us_hi_film_digital_media_credit | US-HI | PARSED | AUTHORITY_UNRESOLVED_NON_PRICEABLE | 22/27* | - | - |
| us_il_film_production_services_credit | US-IL | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 35 | - | F-10 |
| us_ky_keiia | US-KY | PARSED | AUTHORITY_VERIFIED_PRICEABLE | 30/35* | annual 75M | - |
| us_la_film_incentive | US-LA | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25/40* | annual 150M | F-04b |
| us_ma_film_tax_credit | US-MA | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25 | - | F-10 |
| us_md_film_production_activity_credit | US-MD | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 28*/30*/28* | annual 12M | F-11 |
| us_mn_film_production_credit | US-MN | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25 | annual 25M | - |
| us_ms_advantage_film_program | US-MS | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25 | annual 20M, proj 10M | - |
| us_nc_film_entertainment_grant | US-NC | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25* | annual 31M, proj 7M | F-02,F-03 |
| us_nm_film_credit | US-NM | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25/40* | annual 140M | - |
| us_nv_film_credit | US-NV | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 15/25* | annual 10M, native USD 6M | - |
| ny_state_film | US-NY | PARSED | AUTHORITY_VERIFIED_PRICEABLE | 30/50*/60* | - | AG |
| us_ny_post_production_credit | US-NY | PARSED | AUTHORITY_VERIFIED_PRICEABLE | 35 | - | AG |
| us_ok_film_enhancement_rebate | US-OK | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 20/30* | annual 30M | - |
| us_or_opif | US-OR | PARSED | AUTHORITY_VERIFIED_PRICEABLE | 20/25 | annual 21.2M, native USD 10.6M | - |
| us_pa_film_production_credit | US-PA | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25/30* | - | - |
| us_pr_film_incentives_act | US-PR | PARSED | AUTHORITY_VERIFIED_PRICEABLE | 20/40* | annual 38M | - |
| us_ri_film_credit | US-RI | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 30 | annual 40M, native USD 7M | F-04 |
| us_sc_film_production_credit | US-SC | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 30* | - | F-11 |
| us_tn_performance_grant | US-TN | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 25 | - | - |
| us_tx_miip | US-TX | VERIFIED | AUTHORITY_VERIFIED_PRICEABLE | 31* | annual 300M | - |
| us_ut_motion_picture_incentive | US-UT | PARSED | AUTHORITY_UNRESOLVED_NON_PRICEABLE | 20/25* | - | - |
| us_va_motion_picture_credit | US-VA | PARSED | AUTHORITY_UNRESOLVED_NON_PRICEABLE | 15 | - | - |
| us_wa_motion_picture_competitiveness | US-WA | PARSED | AUTHORITY_VERIFIED_PRICEABLE | 30/45* | annual 15M | F-09 |

## 7. Open items carried forward (not duplicating AG)

1. Authorized, bounded regeneration of the four productions (and the canonical budget refresh for parser 1.5.1) to carry F-01..F-07 and F-09 into served data; until then the saved generations show the pre-repair values listed above.
2. F-04b, F-09 (45% ceiling, residency gate), F-05 (Lineamientos), F-10 (per-payee design), F-12 (disclosure decision), F-13, F-14.
3. Out of scope, recorded: Singapore ceiling tier (F-11); the four pre-existing failures (section 5).
