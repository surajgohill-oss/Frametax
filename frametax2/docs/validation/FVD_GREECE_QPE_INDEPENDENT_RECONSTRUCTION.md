# F#K Valentine's Day — Greece QPE independent reconstruction (Claude, 2026-10-10)

**Status: EXACT GREEK QPE NOT_ESTABLISHED. Calculation acceptance: OPEN.** Sections 1-6 are the reconstruction; section 7 records the resolution of register Q36-Q41 and the implementation in commit `6cd2bbe` (engine `canonical-1.108.0`). This is a rule-derived reconstruction from the original budget, the canonical Greek records and the retained primary texts. It produces bounds, not a certified QPE: no per-account Greek-incurred schedule, payee/residency evidence, application date or applicable regime exists in any retained record, and none is supplied here. No production was regenerated or evaluated; the saved generation (`3759a2edf4b4`, canonical-1.106.0) is read-only comparison.

## 1. Evidence used

| Class | Source | Check |
|---|---|---|
| Original budget | `V-BRAT_V8_Greece_041224 TOPSHEET.pdf` (one-page topsheet, budget dated Apr 12, 2024; header "PRELIMINARY BUDGET - GREECE, Location: Greece, Total Shoot 18 Days, SAG (7 roles), Non Union Crew") | All 34 account amounts found in the PDF text and equal to the persisted lines; sum 4,517,687; line 8004 "Greek Estimate Cash Rebate (40%)" −518,804 below the cost total (net 3,998,883). Printed ATL+BTL total 3,628,664; finance 12.5%, contingency 10%, bond 2% are percentages of that total (453,583 / 362,866 / 72,573) |
| Historical primary text | Law 4487/2017 (`ekkomed.gr`, 15 pp.) Art. 26 on PDF p.6 | SHA-256 `deabc311…` equals the retained manifest entry `GR2021` |
| Current primary text | KYA 607434 (Gazette B' 87/14.01.2026, 102 pp.) Arts. 4–5, 11, 23; Annex I; Annex II; Annex B | SHA-256 `9b16095c…` equals manifest entry `GR2026`; read in Greek |
| Canonical records | `gr_cash_rebate` rate rule (40% flat, min EUR 200,000 Greek spend and EUR 400,000 total budget), `QpeCapRule` 80% of worldwide total, `IncentiveValueCapRule` EUR 8m / EUR 10m, requirements profile, `PROGRAM_DOCTRINE` open-default-include, cultural point table | read directly; the program has zero entries in `program_spend_rules` |
| Comparison only | Saved FVD generation; AG `FVD_GREECE_34_ACCOUNT_RECONSTRUCTION.csv` and `FOUR_ANCHOR_QPE_ISSUE_REGISTER_RECONCILIATION.md` at AG commit `59c116f` | never used as an expected value |

## 2. What the primary texts say (paraphrased; article references)

- **Eligible expenses (Law 4487 Art. 26(1); KYA Art. 5(1)):** production expenses incurred in the Greek territory, not exceeding 80% of the total production cost of the work; KYA adds that the total production cost is not limited to the kinds of cost incurred in Greece.
- **Caps on the capped total (Art. 26(2)(a)-(b); KYA Annex B.3(i)-(ii)):** insurance premiums and guarantee costs count up to 5% of the total eligible cost. Historical: screenplay and music fees plus the fees of the director, the screenwriter, **the two leading actors and the producer** (all capacities) up to 35%. Current: music rights, director, screenwriter and the two leading actors up to 30% — the producer is **not** in the current list; Annex II lists the producer fee (1.3) as an ordinary eligible ATL category.
- **Excluded (Art. 26(2)(c)-(d); Annex B.3(iii)-(iv)):** financial and fixed assets and depreciation, lending cost, bank expenses (current text adds interest, FX differences, taxes, duties, customs-broker fees); marketing, promotion and communication.
- **Other current-text rules (Annex B.2):** travel to/from and within Greece recognised (i); own pre-existing equipment ineligible (ii); employee/foreign-employee fees follow Greek law (iii); executive production company fee up to 10% (iv); fuel up to 2% (v); foreign invoices for the director and the two leads permitted (vi — but Art. 5(2) and Law Art. 26(3) tie foreign invoices to works with eligible expenses above EUR 8,000,000; FVD's eligible expenses are far below); music copyright costs and licences on pre-existing works ineligible (vii); **contingency categories are eligible only for Action A** (viii) — Action A is the large and foreign-company action — with per-category contingency allowances (max 10% of the category) listed in Annex II, settled only on incurred, paid, invoiced cost (B.1).
- **Timing (KYA Art. 5(3)):** eligibility starts on the date the funding application is submitted; if the works start before that date the whole plan is ineligible (preparatory production work excepted). **Cultural test (Art. 11(2)(δ); Annex I Table A):** a fiction work needs at least **23 of 50** points.
- **Grant cap (Art. 23(1)):** EUR 8,000,000 per work; up to EUR 10,000,000 only by joint ministerial decision for strategic plans — matches the canonical value cap.

## 3. Account classification (34 accounts, sums over the original lines)

| Class | Accounts | USD | Treatment |
|---|---|---|---|
| Finance | 7901 | 453,583 | Excluded in both regimes (lending/bank cost) — firm |
| Contingency | 7902 | 362,866 | Not an incurred expense until deployed; **not** statutorily excluded: current Action A lists contingency allowances as eligible categories, historical text is silent — CONDITIONAL on deployment |
| Insurance / guarantee | 7200 + 7905 | 50,329 + 72,573 = 122,902 | Eligible category, ≤ 5% of total eligible cost (both regimes) |
| Principal-fee bundle | 1100 252,650; 1300 75,710; 1400 1,246,288 (two leads inside the bundle, the rest outside — split unknown); 1200 401,831 (bundle only in the historical regime); 5100 10,200 | 1,986,679 | ≤ 35% (historical, incl. producer and music) or ≤ 30% (current, excl. producer; music rights listed in B.3(ii) yet ineligible under B.2(vii) — unresolved inside the text); story-rights licences on pre-existing works ineligible (current) |
| Other eligible categories | 1600, 2000–3900, 4600, 5000, 5200–5700, 7000 | 1,591,657 | Annex II categories 2–7 (production office, accounting, legal, insurance, travel, post etc.) — eligible if incurred in Greece |
| **Total** | 34 accounts | **4,517,687** | |

Locality (incurred in Greece) is **unevidenced for every account**: the header states a Greek shoot location only.

## 4. Rule-derived envelope (hypothetical: every non-excluded account presumed Greek-incurred)

Q solves Q = other + min(insurance/guarantee, 5%·Q) + min(bundle, cap·Q), then Q ≤ 80% of total cost. The low end puts all principal-fee accounts and all cast inside the capped bundle; the high end puts cast outside the bundle.

| Regime / contingency | QPE low | QPE high | Incentive at 40% low | high |
|---|---|---|---|---|
| Historical 35% bundle, contingency excluded | 2,637,783.08 | 3,614,149.60 | 1,055,113.23 | 1,445,659.84 |
| Historical, contingency deployed | 3,196,038.46 | 3,614,149.60 | 1,278,415.38 | 1,445,659.84 |
| Current 30% bundle (Action A), contingency excluded | 3,037,985.71 | 3,614,149.60 | 1,215,194.29 | 1,445,659.84 |
| Current, contingency deployed | 3,556,365.71 | 3,614,149.60 | 1,422,546.29 | 1,445,659.84 |

- The engine's served QPE (3,614,149.60) and floor/maximum incentive (1,445,659.84) are exactly the **top of every envelope**: pre-cap 3,701,238 (gross − finance − contingency, no category cap binding) clamped by 80% of the 4,517,687 gross. The engine reports this theoretical maximum as the confirmed floor and as the maximum.
- **Producer-implied base 1,297,010** (518,804 ÷ 0.40, 28.71% of gross) lies below the lowest envelope (49.2% of 2,637,783.08): it can only arise if a large share of the budget is not Greek-incurred. No grouping of accounts reproduces it (closest: BTL 2000–3900 plus post 4600–5700 = 1,256,776, 40,234 or 3.1% short — a coincidence-level match, not an explanation).
- **The 80% denominator is ambiguous in the text** ("total production cost"): gross 4,517,687 → 3,614,149.60; gross − finance 4,064,104 → 3,251,283.20; ATL+BTL printed total 3,628,664 → 2,902,931.20 (incentive ceiling 1,445,659.84 / 1,300,513.28 / 1,161,172.48). The engine uses the largest.
- EUR 8m grant cap (≈ USD 9.1m at the repository's static EUR/USD basis) is not binding anywhere.

## 5. Comparison with AG (59c116f) and the engine — every discrepancy

| ID | AG / engine statement | Primary-text reading | Disposition |
|---|---|---|---|
| G-01 | AG 1200: producer fees "statutorily non-qualifying (Art. 26(2)(c); Annex B)" | 26(2)(c) concerns financial/fixed assets and lending cost; 26(2)(b) puts the producer inside the 35% bundle; the current Annex II lists the producer fee as an eligible category and the 30% list omits the producer | AG statement UNSUPPORTED; its own CSV also applies the bundle cap to 1200 in the same row. Producer fee is conditional on locality and regime |
| G-02 | AG cites Law 4487 "Art. 20" for the financing exclusion, administrative restriction and contingency exclusion | Art. 20 is the definitions article; the real bases are Art. 26(2)(c)/(d) and Annex B.3(iii)/(iv) | Citation defect; finance conclusion correct |
| G-03 | AG 7000: general overhead excluded, only audit/accounting qualifies | Annex II category 7 lists production-office lease, utilities, supplies, telephones, courier, legal and consultant fees, accounting and insurance as eligible | AG restriction UNSUPPORTED; 7000 is conditional on locality (no itemisation available) |
| G-04 | AG 7902: contingency EXCLUDED_STATUTORY_NON_ELIGIBLE (also "because the utilisation percentage is unset") | Action A lists contingency allowances; settlement only on incurred cost. The utilisation percentage is a CineGlobe product fact, not a statutory test | AG label overstated → CONDITIONAL on deployment. The engine's default exclusion is a product definition (undeployed reserve is not incurred spend), consistent in result but not statutory |
| G-05 | AG 1100 "Greek author nexus" | not in either text; current B.2(vii) excludes licences on pre-existing works | nexus claim UNSUPPORTED; rights portion conditional |
| G-06 | AG foreign ATL cast ineligible unless performed in Greece under Greek withholding | Law Art. 26(3) and KYA Art. 5(2) permit foreign invoices for the director and two leads only for works above EUR 8,000,000 of eligible expenses; Annex B.2(vi) repeats the permission (Action A: ≤ 20% of eligible expenses) without restating the threshold, so the texts are in tension. Under the conservative reading FVD (eligible expenses far below EUR 8m) cannot use foreign-invoiced ATL fees; Greek-law treatment of foreign employees (B.2(iii)) remains open | AGREE in direction; AG omitted the EUR 8m gate and the internal tension. Still unevidenced |
| G-07 | AG insurance/bond 5% cap; finance excluded; 35%/30% bundle caps; 80% ceiling model; $1,297,010 estimate-implied only; $926,855.84 an unresolved planning variance; exact QPE NOT_ESTABLISHED | all CONFIRMED by the texts and by this reconstruction | accepted |
| G-08 | Engine: no Greek spend rules at all | the texts define 5% insurance/guarantee, 35%/30% bundle, foreign-invoice, own-equipment, music-rights, promotion, tax/duty exclusions | CANONICAL_DATA_MISSING / OPTIMIZER_CAPABILITY_MISSING (a cap expressed as a share of the capped total needs a fixed-point mechanism). No effect on the current FVD number (no cap binds in the maximum model); will matter once a Greek schedule exists |
| G-09 | Engine floor = maximum = 1,445,659.84, ceiling status CONFIRMED | the figure is the top of the envelope with locality presumed | presentation defect (register Q19): a presumption is shown as a confirmed floor |
| G-10 | Engine 80% cap base = gross incl. financing | text ambiguous (three plausible bases, above) | OPEN interpretation; engine uses the most favourable |
| G-11 | Canonical rate citation says "no cultural test"; points table threshold 20 of 50 from secondary sources | KYA Art. 11(2)(δ) and Annex I require ≥ 23 of 50 for fiction (2026 text); the 2024-era threshold for the applicable regime is not established | canonical contradiction recorded; engine gate is USER_FACT_REQUIRED (0 of 20), so no pricing effect today; table needs Annex I and regime selection |
| G-12 | Regime and timing | budget dated Apr 12, 2024; applicable law (4487/2017, 5105/2024 with earlier KYAs, or KYA 607434) depends on an application date nobody has; Art. 5(3) can void the whole plan if works start before application | NOT_ESTABLISHED (Q11) |

## 6. Remaining facts and blockers

1. Per-account Greek-incurred schedule with payee residency and Greek tax/withholding evidence (needed for every class above).
2. Application submission date versus start of works, and the regime/KYA edition that governs.
3. Whether the producer's $518,804 estimate was built on a Greek local-spend schedule (the supporting working is not in any retained record).
4. Interpretation of the 80% denominator; contingency deployment; lead-cast split inside account 1400.
5. Cultural-criteria evidence against Annex I Table A (23/50).

Nothing above is a certified QPE. The only established facts are the 34 source amounts, the firm finance exclusion, the 5%/35%/30%/80% rule structure and the envelope arithmetic.

## 7. Resolution of Q36-Q41 (commit `6cd2bbe`; nothing regenerated)

**Dated authority used.** Law 4487/2017 (A' 116/2017) Art. 26; Law 5043/2023 Arts. 61-63 (A' 91/13.04.2023, SHA-256 `791b5992…` = manifest `GR2023`) amending Art. 26(3); Law 5105/2024 Part C (A' 61; cited by the KYA, **text not retained**); KYA 6376/2025 (16.01.2025; cited, **text not retained**); KYA 607434 (B' 87/14.01.2026, `9b16095c…`). The 6-page KYA amendment (`GR2026AMEND`, `e206ae95…`) has no text layer and was **not read**. Canonical Greek rules are current-text rules (JMD 607434), so the implementation follows the current text and documents where the historical text differs.

| Item | Resolution | Implemented | Still missing (exact) |
|---|---|---|---|
| Q36 AG statements (G-01/02/03/05) | Disproved against the texts (section 5). Owner AG to correct before any acceptance claim | documentary only | — |
| Q37 contingency deployment | Not statutorily excluded: Action A lists contingency allowances (max 10% per category), settled only on incurred, paid, invoiced cost; historical text silent. Explicit rule `gr_cash_rebate` contingency `qualifies=True`, so the reserve is conditional until the producer's expected-utilization fact is set (100% → ordinary eligible cost; 50% → half, the rest excluded) | spend rule + synthetic controls | deployment percentage or actual contingency spend; confirmation that the beneficiary is an Action A applicant (large/foreign) |
| Q38 foreign invoices | Dated: Law 5043/2023 Art. 61 (13.04.2023) limits foreign invoices to the director and two leads, only for works above EUR 8,000,000 of eligible cost, at most 20% of eligible cost, subsidy at most EUR 12,000,000; KYA Art. 5(2) keeps the EUR 8m gate; Annex B.2(vi) (Action A, ≤ 20%) restates the permission without the threshold; Annex IV evidence rules accept foreign documents for Action A only if the work was performed entirely in Greece, and retail receipts only up to 0.5% | disclosed through `presumed_facts` (`gr-local-incurrence-schedule`); no payee-level rule coded (no payee data exists) | invoice issuer and residency per account; Greek tax/withholding evidence; whether the EUR 8m gate applies to Annex B.2(vi) |
| Q39 category/fee rules | Current-text share caps implemented: insurance + completion bond ≤ 5%, director + screenwriter + cast ≤ 30% of the TOTAL eligible cost (producer outside, per Annex II 1.3 and B.3(ii)), solved as a fixed point with the 80% limit; the excess is conditional (payee split unknown), never dropped | `QpeShareCapRule`, solver in `price_segment`, trace fields `qpe_share_cap_groups` | historical 35% group (producer and music inside, Law 4487 Art. 26(2)(b)) is documented but not coded; unmodeled because no FVD account carries them: executive-production-company fee ≤ 10% (B.2(iv)), fuel ≤ 2% (B.2(v)), own pre-existing equipment (B.2(ii)), pre-existing-works licences and music copyright (B.2(vii), in tension with B.3(ii)), promotion/tax/duty lines (B.3(iii)-(iv)), retail receipts 0.5% |
| Q40 presentation / 80% denominator | The text defines the denominator only as "total production cost of the work" (Law Art. 26(1); KYA Art. 5(1); GBER-style definition at KYA p.101) and scopes the lending-cost, bank, tax, duty and promotion exclusions to the **eligible** total (Art. 26(2)(c)-(d); Annex B.3(iii)-(iv)); the Annex II budget template has no financing category. The text does not settle whether financing is in the denominator: the canonical base stays the full budget total (the widest), and the narrower bases are documented sensitivities (gross − finance 3,251,283.20; printed ATL+BTL 2,902,931.20) | cap description records the reading; the unevidenced Greek-incurrence presumption and the application-date/regime presumption are now disclosed by `presumed_facts` | the beneficiary's own total-cost computation in the application; ruling or form guidance on whether financing counts |
| Q41 cultural threshold / regime | Primary current text (KYA Annex I Table A, Art. 11(2)(δ)): at least **23 of 50** (script 20 max, personnel 15 max, production/post in Greece 15 max); the earlier 20 was secondary-sourced. Rate citation corrected (it said "no cultural test") | table + profile threshold 23 with primary source note | Annex I criteria are not encoded as executable facts (aggregate user fact stays); threshold under Law 5105/2024 / KYA 6376/2025 and the earlier regime is NOT_ESTABLISHED; application date and governing text |

**Replay of the four original budgets under the repaired Greek rules** (pure-function `price_segment`, synthetic classification, not served; saved generation values are comparison only):

| Budget (Greece) | QPE saved → repaired | Incentive floor saved → repaired | Conditional (unresolved) repaired |
|---|---|---|---|
| FVD (baseline) | 3,614,149.60 → 3,037,985.72 | 1,445,659.84 → 1,215,194.29 | 1,026,118.28 = fee-cap excess 663,252.29 + contingency 362,866 |
| LU (relocation) | 3,491,514.40 → 3,491,514.40 (80% limit binds) | 1,396,605.76 → unchanged | 301,131 contingency (was excluded) |
| BH (relocation) | 1,985,618.40 → 1,637,011.43 | 794,247.36 → 654,804.57 | 845,011.57 = fee-cap excess 690,629.57 + contingency 94,382 + SAG deposit 60,000 |
| LLS (relocation) | 9,483,654 → unchanged | 3,793,461.60 → unchanged | 800,000 = contingency 400,000 + residuals reserve 400,000 |

The repaired FVD QPE 3,037,985.72 reproduces the section-4 independent closed-form low end (current regime, contingency excluded, every account presumed Greek-incurred) to the cent. It is still a presumed-locality figure: the producer-implied base 1,297,010 and the $926,855.84 difference remain an unresolved planning variance, and exact Greek QPE stays NOT_ESTABLISHED.

**Remaining missing facts, exactly:** (1) per-account Greek-incurrence schedule with invoice issuer, payee residency and Greek tax/withholding evidence; (2) application submission date versus start of works, and the governing text (Law 4487/2017 as amended, Law 5105/2024 with KYA 6376/2025, or KYA 607434) — the texts of Law 5105/2024 Part C and KYA 6376/2025 and the content of the scanned KYA amendment are not retained/read; (3) Action A beneficiary status and contingency deployment; (4) lead-cast split inside account 1400 and the composition of 1100, 5100 and 7000; (5) the producer's estimate working behind line 8004; (6) Annex I Table A scoring evidence; (7) the application's own total-cost computation for the 80% denominator.

