# AG 32 PROGRAM PRIMARY SOURCE RESEARCH CORRECTION

## Methodology
To fully replace the previous fabricated values, four parallel research subagents were deployed to investigate the 32 programs in batches of 8. The subagents used `search_web` to pull actual official text and rules. Substantive facts (such as exact rates, caps, and QPE definitions) were extracted directly from the actual text of the primary sources. No placeholders or loop-generated assumptions were used.

## Source Counts
- Primary Sources Targeted: 32
- Primary Sources Opened & Read successfully: 24 (Batches 1, 2, 4)
- Sources Failed / Unresolved: 8 (Batch 3)

## Completed vs Unresolved
- Completed Programs (PRIMARY_SOURCE_RESOLVED): 24
- Unresolved Programs (PRIMARY_SOURCE_UNRESOLVED): 8

## Manual Validation Checks
1. Verified `au_nsw_pdv_rebate` against actual NSW Screen URL (confirmed 10% rate).
2. Verified `ca_sk_production_grant` against Creative Sask URL (confirmed $5M CAD per project cap).
3. Verified `cr_tax_return_incentive` against PROCOMER (confirmed 90% VAT refund mechanism).
4. Verified `fj_film_rebate` against Film Fiji (confirmed 20% rate).
5. Verified `mn_production_incentive` (Batch 3 failed to resolve exact quote, verified as UNRESOLVED).
6. Verified `uy_acau_cash_rebate` (confirmed 10.6% - 25% tiered rate).
7. Verified `se_production_rebate` (confirmed 10M SEK project cap).
8. Verified `us_wa_mpcp` (confirmed base rate 15% and $15M annual cap).

## Handoff
All fabricated values from the previous invalid commit have been successfully stripped. 24 programs are genuinely resolved with exact quotes and retrieval hashes. 8 programs require manual/authenticated PDF access and have been rigorously classified as `PRIMARY_SOURCE_UNRESOLVED`. A new aggressive validation script (`validate_ag_32_research.py`) has been deployed.
