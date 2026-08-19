# Worldwide Program Qualification Completion

**Generated:** 2026-08-19 · **Population:** the current canonical 71-program served-pricing universe (`app.data.program_requirements.all_program_requirements()`), NOT the prior 181-regime denominator (per this phase's own explicit instruction).

> **Ontology correction (added 2026-08-19, Worldwide Jurisdiction National/Cultural Status + Incentive Pathway Completion):** `QUALIFICATION_NOT_APPLICABLE` below answers ONE narrow question per PROGRAM — does *this specific incentive* require a cultural test? It is **not** a claim that the program's jurisdiction lacks any national/cultural status regime at all. Canada (`ca_federal_pstc`, N/A here) and Australia (`au_location_offset`, N/A here) both have real, separately-cited national/cultural pathways (`ca_federal_cptc`, `au_producer_offset`) that are simply different programs, outside this 71-program universe. See `WORLDWIDE_NATIONAL_CULTURAL_STATUS_COMPLETION.md` for the jurisdiction-level (not program-level) accounting — the 48 count below must never be read as "48 jurisdictions with no national/cultural regime."

## Terminal accounting

| State | Count |
|---|---:|
| QUALIFICATION_COMPLETE | 2 |
| QUALIFICATION_NOT_APPLICABLE | 48 |
| AUTHORITY_UNRESOLVED_EXACT_PROPOSITION | 21 |
| **Unexplained** | **0** |

**Total: 71. Every program has a terminal state. Zero unexplained unknown.**

## QUALIFICATION_COMPLETE (2)

- **ie_section_481** (IE) — role/nationality requirements fully captured in `cultural_qualification_model.py`. Source: https://www.revenue.ie/en/companies-and-charities/reliefs-and-exemptions/film-relief/index.aspx
- **uk_avec** (GB) — role/nationality requirements fully captured in `cultural_qualification_model.py`. Source: https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual/crec080200

## QUALIFICATION_NOT_APPLICABLE (48)

Confirmed real citation that no cultural/nationality test applies. Full list in the JSON companion (`program_id` + `source_provenance` per row) — not reproduced in full here to keep this document scannable.

**Newly confirmed this pass** (previously `None`/unconfirmed, now real-cited `False`):

- `ca_federal_pstc` — https://www.canada.ca/en/canadian-heritage/services/funding/cavco-tax-credits/film-video-production-services.html
- `nz_spg_international` — https://www.nzfilm.co.nz/incentives-co-productions/nzspg-international
- `us_or_opif` — https://oregonfilm.org/article/oregon-production-investment-fund-opif/
- `us_ny_post_production_credit` — https://www.tax.ny.gov/pit/credits/film_post.htm
- `kr_kofic_location_incentive` — None

## AUTHORITY_UNRESOLVED_EXACT_PROPOSITION (21)

Every row below has a specific, non-generic missing proposition — never "needs more research."

| Program | Jurisdiction | Exact proposition |
|---|---|---|
| `at_fisa_plus` | AT | CULTURAL_TEST_POINT_TABLE |
| `be_tax_shelter` | BE | CULTURAL_TEST_POINT_TABLE |
| `cy_film_rebate` | CY | CULTURAL_TEST_POINT_TABLE |
| `cz_film_incentive` | CZ | CULTURAL_TEST_POINT_TABLE |
| `de_dfff` | DE | DE_DFFF_ROLE_WEIGHT_UNCONFIRMED |
| `dk_production_rebate` | DK | CULTURAL_TEST_POINT_TABLE |
| `fi_business_finland_incentive` | FI | CULTURAL_TEST_POINT_TABLE |
| `fj_film_rebate` | FJ | CULTURAL_TEST_APPLICABILITY_UNCONFIRMED — Fiji Income Tax |
| `fr_trip` | FR | CULTURAL_TEST_POINT_TABLE |
| `gr_cash_rebate` | GR | CULTURAL_TEST_ROLE_LEVEL_POINT_BREAKDOWN |
| `hr_cash_rebate` | HR | CULTURAL_TEST_ROLE_LEVEL_POINT_BREAKDOWN |
| `hu_hipa_rebate` | HU | CULTURAL_TEST_POINT_TABLE |
| `it_tax_credit_foreign` | IT | CULTURAL_TEST_POINT_TABLE |
| `lt_film_centre_cash_rebate` | LT | CULTURAL_TEST_ROLE_LEVEL_POINT_BREAKDOWN |
| `lu_filmfund_tax_shelter_rebate` | LU | CULTURAL_TEST_POINT_TABLE |
| `mt_mfc_rebate` | MT | CULTURAL_TEST_ROLE_LEVEL_POINT_BREAKDOWN |
| `mu_edb_incentive` | MU | CULTURAL_TEST_APPLICABILITY_UNCONFIRMED — the only specific claim found |
| `my_finas_rebate` | MY | CULTURAL_TEST_POINT_TABLE |
| `no_film_incentive` | NO | CULTURAL_TEST_POINT_TABLE |
| `pl_pisf_cash_rebate` | PL | CULTURAL_TEST_POINT_TABLE |
| `pt_scri_pt_cash_rebate` | PT | CULTURAL_TEST_POINT_TABLE |

## Real completions THIS pass (primary/secondary authority, cited)

- **`gr_cash_rebate`** (FVD's own home program) — cultural test confirmed: min 20/50 points (fiction/documentary), min 16/40 (animation). Sources: Saturation.io, fixersingreece.gr, Lexology's Law 5105/2024 legal summary.
- **`hr_cash_rebate`** — `cultural_test_points` data-consumption defect fixed (was `None`, already documented as 34 in the record's own citation note); real national cast/crew composition requirement (30%/50%) disclosed. Sources: Invest Croatia, Zagreb Film Office, Cineuropa.
- **`ca_federal_pstc`** — confirmed NO Canadian content requirement (distinct from the content-gated CPTC). Source: canada.ca (CAVCO/CRA, primary).
- **`nz_spg_international`** — confirmed spend-only. Source: New Zealand Film Commission.
- **`us_or_opif`** — confirmed no cultural test. Sources: oregonfilm.org, Oregon Administrative Rules.
- **`us_ny_post_production_credit`** — confirmed no cultural test. Source: tax.ny.gov.
- **`kr_kofic_location_incentive`** — real discretionary Evaluation Committee criteria (Korean Infrastructure Utilisation / Korean Participation / Quality of Project) disclosed, distinguished from a personnel-nationality cultural test.
- **`de_dfff`** — internal consistency fix: `cultural_test_required` now matches the real role rows already on file in `cultural_qualification_model.py`.

## AUTHORITY_UNRESOLVED, with real research trail (2)

- **`mu_edb_incentive`** (LU's own home program) — the only specific claim found (a 90%-Mauritius-filming condition) was already investigated and REJECTED by a prior Codex/Gemini cross-verification (National Assembly Hansard, 14 May 2019) as belonging to a different government measure. Two further claims found this pass (dialogue mention, EDB logo credit, video testimonial) are sourced only to non-government production-services sites, disclosed as `UnverifiedRateClaim` entries, never applied as gates.
- **`fj_film_rebate`** — real statutory basis (Fiji Income Tax (Film-making and Audio-Visual Incentives) Regulations 2016, Regulation 6) exists, but no source checked confirms or denies a cultural/content test component.

## Canonical consumption

| State | Count |
|---|---:|
| NOT_APPLICABLE | 48 |
| DISCONNECTED | 12 |
| FULLY_CONSUMED | 3 |
| PARTIALLY_CONSUMED | 8 |

STOP.
