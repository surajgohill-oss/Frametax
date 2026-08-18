# Final 19 — Codex Independent Committee Review

**Final gate:** `CODEX_FINAL_19_COMMITTEE_REVIEW_COMPLETE`  
**Reviewed:** 19/19  
**Unreviewed:** 0  
**Structured record:** `FINAL_19_CODEX_COMMITTEE_REVIEW.json`

This is an adversarial review of Claude's 19-program primary-research handoff. It does not change production code, canonical economics, coverage state, confidence tiers, optimizer behavior, or frontend behavior.

## Verdicts

| Verdict | Count |
|---|---:|
| AGREE | 8 |
| CORRECT | 11 |
| CONFLICT | 0 |
| NEEDS_SECOND_OPINION | 0 |
| **Total** | **19** |

## Program decisions

| Program | Verdict | Codex type | Priceability | Committee conclusion |
|---|---|---|---|---|
| `ar_incaa_incentive` | CORRECT | NON_ECONOMIC | NO | Keep INCAA unpriceable, but do not attach unverified Buenos Aires City figures to this national-agency identity. |
| `au_nsw_screen` | CORRECT | GRANT_FUND | NO | Selective grant is correct; Production Finance, Made in NSW and Regional Film Fund must be separate stream identities. |
| `au_qld_screen_qld` | AGREE | GRANT_FUND | NO | Board-discretionary, funding-dependent PAS grant; AUD3.5m Queensland QPE gate. |
| `au_vic_vicscreen` | CORRECT | GRANT_FUND | NO | Selective treatment is right, but VSI and the Victorian Production Fund are distinct programs with different minimum/cap mechanics. |
| `bc_interactive_digital_media_tax_credit_idmtc` | AGREE | OTHER | NO | Deterministic 25% payroll credit for interactive media, outside current film/TV production types. |
| `br_ancine_incentive` | CORRECT | FINANCING_SUPPORT | NO | ANCINE does administer tax-incentive financing; it is not a foreign-production QPE rebate and is not non-economic. RioFilme remains separate. |
| `ca_federal_cptc` | AGREE | FORMULAIC_DETERMINISTIC | PROJECT_FACT_DEPENDENT | 25% qualified labour with 60% net-cost ceiling; Canadian certification/treaty and labour facts required. |
| `ca_nl_production_fund` | AGREE | FORMULAIC_DETERMINISTIC | PROJECT_FACT_DEPENDENT | 40% all-spend credit, net of assistance, CAD20m annual per-project cap; registration and eligible-cost facts required. |
| `dk_film_incentive` | AGREE | SELECTIVE_DISCRETIONARY | NO | Operative 2026 scheme: 25% of approved Danish cost, DKK20m cap, competitive scored rounds. |
| `gb_sct_screen_fund` | AGREE | GRANT_FUND | NO | GBP200k–500k selective grant with 10:1 Scottish-spend ratio and Scottish-residence rules for ATL. |
| `gb_wls_screen_fund` | AGREE | GRANT_FUND | NO | Selective fund, up to GBP600k, usually GBP150k–400k, ordinarily at most 50% of budget and 6:1 Welsh spend. |
| `in_national_film` | CORRECT | FORMULAIC_DETERMINISTIC | PROJECT_FACT_DEPENDENT | Correct formula is 30% base plus applicable 5-point Indian-crew and SIC conditions, maximum 40%—not 50%. |
| `jm_film_incentive` | CORRECT | FINANCING_SUPPORT | NO | No official general production rebate; split PAYE-based ETC, bond waiver and duty/import relief mechanisms. |
| `mx_eficine_incentive` | CORRECT | FORMULAIC_DETERMINISTIC | PROJECT_FACT_DEPENDENT | EFICA is a new, separate 2026 identity; do not rename/overwrite EFICINE. EFICA is up to 30%, capped MXN40m, transferable under stated limits. |
| `new_zealand_screen_production_grant_—_international_post_vfx` | CORRECT | FORMULAIC_DETERMINISTIC | PROJECT_FACT_DEPENDENT | Current 2026 PDV treatment is 20% baseline / 25% conditional uplift; the 20%/18% bracket is historical. |
| `pe_film_incentive` | CORRECT | FORMULAIC_DETERMINISTIC | PROJECT_FACT_DEPENDENT | CIPA is enacted and regulated by Supreme Decree 099-2026-EF; investor, approved-investment, utilization and administrative-readiness facts remain material. |
| `pt_film_incentive` | CORRECT | OTHER | PROJECT_FACT_DEPENDENT | June 2026 RIPAC law resolves the stale-source conflict; large and medium tracks have different rates, caps and allocation methods. |
| `qc_film_production` | AGREE | DUPLICATE_ALIAS | PROJECT_FACT_DEPENDENT | Bind only to `ca_qc_pstc`: 25% Québec all-spend plus 16% qualifying VFX/animation labour, subject to current gates. |
| `uy_xxi_incentive` | CORRECT | OTHER | PROJECT_FACT_DEPENDENT | Reattribute to ACAU and split current cash-rebate calls from the July 2026 30% tax credit; do not implement the unverified generic three-tier table. |

## Material corrections

1. India: replace the proposed 50% structure with 30% base plus applicable 5-point crew/SIC conditions, capped at 40%.
2. New Zealand: replace the historical 20%/18% PDV bracket with the current 20% baseline / 25% conditional uplift for activity starting on or after 1 January 2026.
3. Peru: reclassify CIPA as enacted and regulated as of June 2026, with operational and investor-structure gates.
4. Portugal: use Portaria 265-A/2026 as amended—EUR200k documentary/no-filming minimum, EUR1.5m medium cap, and separate large/medium allocation paths.
5. Brazil: ANCINE is economic financing support under tax-incentive laws; RioFilme is a distinct municipal rebate.
6. Uruguay: separate ACAU cash-rebate calls from Decree 153/026's 30% tax credit; the same project cannot receive both.
7. Mexico: create EFICA separately; EFICINE remains distinct.
8. Jamaica: remove the unsupported general production-rebate claim and split the official relief mechanisms.
9. NSW and Victoria: do not collapse multiple selective funds/incentives into one rate/cap record.
10. Argentina: do not use unverified Buenos Aires City figures as INCAA doctrine.

## Program-type changes

- `br_ancine_incentive`: NON_ECONOMIC → FINANCING_SUPPORT
- `jm_film_incentive`: OTHER_SUPPORTED_TYPE → FINANCING_SUPPORT
- `pt_film_incentive`: FORMULAIC_DETERMINISTIC → OTHER because the umbrella contains differently allocated tracks
- `uy_xxi_incentive`: FORMULAIC_DETERMINISTIC → OTHER pending separation of distinct ACAU instruments

## Targeted checks

Targeted authority checks were performed for all 19 handoff records, limited to disputed identity, currentness, program-type, rate/base, QPE/territoriality, thresholds/caps, uplift, monetization, selection and priceability propositions. The JSON supplies the exact official source at each proposition.

## Historical #84 accounting

`CLAUDE_84_ACCOUNTING_CONFIRMED`

Independent git-object inspection confirms that the 94 and 84 populations were persisted only as counts, not complete literal identity sets. The later 21-program artifact is exactly enumerable, but the historical missing identity cannot be reconstructed because the formulaic source population was never snapshotted. No denominator correction is supported.

## Integrity

- Programs reviewed: 19
- Programs unreviewed: 0
- Production code changed: NO
- Canonical economics changed: NO
- Frontend changed: NO
- Optimizer changed: NO
