# Final 19 Zero-Evidence Programs — Primary Research Committee Handoff

**Generated:** 2026-08-17
**Final gate:** `FINAL_19_PRIMARY_RESEARCH_READY_FOR_COMMITTEE`
**Full structured data:** [`FINAL_19_PRIMARY_RESEARCH_COMMITTEE_HANDOFF.json`](FINAL_19_PRIMARY_RESEARCH_COMMITTEE_HANDOFF.json)

No implementation was performed. No coverage vetoes were removed. No pricing behavior, scenario counts, or frontend code changed. This is a **research handoff** for independent Codex/Gemini committee review before any of these findings become production doctrine.

## Denominator

19 of 19 researched, 0 unexplained. Population = `GLOBAL_ECONOMIC_DATA_ZERO_EVIDENCE_21.json`'s 21 named programs minus the 2 already resolved this project (`on_ofttc`, `ocase`).

## The #84 accounting identity

Traced mechanically through three chronological artifacts (`GLOBAL_BASE_PRICEABILITY_CLOSEOUT.json` → `GLOBAL_ECONOMIC_DATA_BASE_PRICING_CLOSEOUT.json` → `GLOBAL_ECONOMIC_DATA_ZERO_EVIDENCE_21.json`) plus a direct `git show` extraction of `authority_coverage_registry.py`'s blocked-slug list at the commit that produced the original "94" figure. **Conclusion: the missing 84th identity is not recoverable and is very likely not a real missing program.** No artifact in this project's history, at any commit, ever persisted a literal name list for the 94/126-classified "formulaic" population — every count was a live, point-in-time derived number filtered against a classification that was never itself snapshotted. This is a genuine pre-existing gap in record-keeping, not a hidden identity. It does not affect this task's own 19-program denominator, which is independently and exactly enumerable. Full trace in the JSON artifact's `accounting_84_reconciliation` block.

## What the research actually found

Three recurring patterns emerged across the 19:

1. **Identity mismatches (5 programs):** `ar_incaa_incentive`, `br_ancine_incentive`, and `uy_xxi_incentive` are named after national agencies (INCAA, ANCINE, Uruguay XXI) that **do not themselves administer** any foreign-production rebate — the real formulaic mechanism sits with a different, sub-national or sector-specific body (Buenos Aires City/BAFC, Rio's RioFilme, Uruguay's ACAU). `mx_eficine_incentive` and `pt_film_incentive` reference program names/articles that appear to be outdated relative to newly-launched 2026 regimes (Mexico's EFICA decree, Portugal's RIPAC/SCRI.PT).
2. **A confirmed duplicate:** `qc_film_production` is the same program already registered in this codebase as `ca_qc_pstc` (confirmed by direct code inspection, not inference) — a straight identity-merge, not a research gap.
3. **Genuine grant/discretionary programs mislabeled as formulaic candidates:** `au_nsw_screen`, `au_qld_screen_qld`, `au_vic_vicscreen`, `dk_film_incentive`, `gb_sct_screen_fund`, and `gb_wls_screen_fund` are all real, well-documented, but explicitly **competitive/discretionary** funds — several have official-source language stating so directly ("at the discretion of the Screen Queensland Board," "highly competitive," Denmark's scored application rounds). None should be modeled as a guaranteed deterministic rate.

Two programs (`ca_federal_cptc`, `ca_nl_production_fund`) turned out to be clean, well-documented, straightforwardly formulaic federal/provincial tax credits with no complications — the strongest near-term canonicalization candidates.

## Program type counts

| Type | Count | Programs |
|---|---|---|
| FORMULAIC_DETERMINISTIC (in-scope) | 7 | ca_federal_cptc, ca_nl_production_fund, in_national_film, mx_eficine_incentive, nz_ispr_pdv_track, uy_xxi_incentive, qc_film_production (via merge) |
| FORMULAIC_DETERMINISTIC (out of scope) | 1 | bc_interactive_digital_media_tax_credit_idmtc (games/interactive media, not film/TV) |
| GRANT_FUND / SELECTIVE_DISCRETIONARY | 7 | au_nsw_screen, au_qld_screen_qld, au_vic_vicscreen, dk_film_incentive, gb_sct_screen_fund, gb_wls_screen_fund, jm_film_incentive |
| NON_ECONOMIC | 3 | ar_incaa_incentive, br_ancine_incentive, pe_film_incentive |
| DUPLICATE_ALIAS | 1 | qc_film_production |

## Proposed priceability

- **PRICEABLE_FORMULAIC:** 7 (6 new + the qc_film_production merge onto existing `ca_qc_pstc`)
- **PROJECT_FACT_DEPENDENT:** 1 (`pt_film_incentive` — two source descriptions materially conflict, needs reconciliation before a single rate is committed)
- **SELECTIVE_DISCRETIONARY:** 7
- **NON_ECONOMIC:** 4

## Authority and source access notes

Several official government domains (canada.ca, screen.nsw.gov.au, mib.gov.in, ffo.gov.in, pib.gov.in) blocked direct fetch with HTTP 403 or DNS failure. Per instruction, alternate official publications and convergent secondary corroboration were used rather than stopping — every such case is disclosed explicitly in that program's `source_provenance.citation_detail`. **No program in this artifact should be read as VERIFIED-tier** without a follow-up direct primary-source confirmation pass; most are PARSED-tier with a clear path to verification.

Material conflicts requiring committee attention: `pt_film_incentive` (two incompatible rate descriptions). Interpretation ambiguity: `mx_eficine_incentive` (rename question), `gb_wls_screen_fund` (talent-nationality gate may place it out of scope for base pricing entirely), `new_zealand_screen_production_grant_—_international_post_vfx` (mutual-exclusivity with the general NZ rebate unresolved).

## Committee routing

- **Codex challenge recommended:** `ar_incaa_incentive`, `br_ancine_incentive`, `uy_xxi_incentive` — independently verify the identity-correction reasoning before any rename/reclassification is applied.
- **Gemini tie-break recommended:** `pt_film_incentive`, `mx_eficine_incentive`.

## Explicitly not done this pass

Production economics unchanged. Frontend unchanged. No coverage vetoes removed. No canonical registry entries added or modified. No scenario/candidate counts changed. Optimizer, stacking, grants/funds, official co-production, hybrid/anchor, in-kind, and reinvestment mechanisms untouched — findings about several of these (Denmark's cultural test, Wales's talent gate) are preserved in the JSON for that later work, not acted on now.

STOP FOR CODEX COMMITTEE REVIEW.
