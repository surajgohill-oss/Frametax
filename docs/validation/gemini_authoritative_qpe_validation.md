# CINEGLOBE INDEPENDENT AUTHORITATIVE QPE VALIDATION REPORT

## Executive Summary
This report validates CineGlobe's current QPE (Qualifying Production Expenditure) treatment for the *Little Utopia* project across five jurisdictions: Mauritius, Malta, Greece, United Kingdom, and Australia. The validation compares CineGlobe's `budget_qpe_trace` against current, authoritative, publicly available tax incentive guidelines for each jurisdiction. 

Major discrepancies were found in how CineGlobe handles **Development (1000)**, **Marketing (7300)**, and **Contingency (8300)**. 

---

## A. Mauritius (MU)

**Program:** Mauritius Film Rebate Scheme (Economic Development Board)
**General Rule:** Only actual, documented, and audited production expenses incurred in Mauritius qualify. 

| Category | CineGlobe Treatment | Authoritative Rule | Status | Official Source | Required Change | Financial Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1000 DEVELOPMENT** | Included | Pre-production/development costs incurred before principal photography are generally excluded unless directly tied to local production activities. | **INCORRECT** | [EDB Film Rebate Guidelines](https://www.edbmauritius.org/film-rebate-scheme) | Exclude | Decrease QPE |
| **7300 MARKETING** | Excluded | Marketing is non-qualifying as it is not a direct production cost. | **CORRECT** | [EDB Film Rebate Guidelines](https://www.edbmauritius.org/film-rebate-scheme) | None | None |
| **8300 CONTINGENCY** | Included | Unspent contingency is a budget provision, not an incurred cost, and is strictly ineligible for a cash rebate. | **INCORRECT** | [EDB Film Rebate Guidelines](https://www.edbmauritius.org/film-rebate-scheme) | Exclude | Decrease QPE |

---

## B. Malta (MT)

**Program:** Malta Film Commission Cash Rebate
**General Rule:** Eligible expenditure must be incurred on production activities in Malta. Marketing and contingency provisions are explicitly excluded.

| Category | CineGlobe Treatment | Authoritative Rule | Status | Official Source | Required Change | Financial Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1000 DEVELOPMENT** | Included | Early development is excluded. Only active pre-production and production costs are eligible. | **INCORRECT** | [MFC Financial Incentive Guidelines](https://maltafilmcommission.com/cash-rebate/) | Exclude | Decrease QPE |
| **7300 MARKETING** | Included | Marketing and distribution are explicitly ineligible. | **INCORRECT** | [MFC Financial Incentive Guidelines](https://maltafilmcommission.com/cash-rebate/) | Exclude | Decrease QPE |
| **8300 CONTINGENCY** | Excluded | Contingency is a reserve and not an incurred cost; therefore ineligible. | **CORRECT** | [MFC Financial Incentive Guidelines](https://maltafilmcommission.com/cash-rebate/) | None | None |

---

## C. Greece (GR)

**Program:** Hellenic Film and Audiovisual Center / Creative Greece (formerly EKOME) Cash Rebate
**General Rule:** Marketing is strictly ineligible. Development and Contingency have specific conditional inclusions.

| Category | CineGlobe Treatment | Authoritative Rule | Status | Official Source | Required Change | Financial Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1000 DEVELOPMENT** | Included | Production development costs are eligible under Greek rules. | **CORRECT** | [Greek Law / Creative Greece Guidelines](https://www.ekome.media/audiovisual-production-invest/cash-rebate/) | None | None |
| **7300 MARKETING** | Included | Marketing, promotion, and communication expenses are strictly ineligible. | **INCORRECT** | [Creative Greece Guidelines](https://www.ekome.media/audiovisual-production-invest/cash-rebate/) | Exclude | Decrease QPE |
| **8300 CONTINGENCY** | Excluded | Contingency costs are generally eligible under "Action A" of the cash rebate scheme. | **CONDITIONAL** | [Creative Greece Guidelines](https://www.ekome.media/audiovisual-production-invest/cash-rebate/) | Include if Action A | Increase QPE (Potentially) |

---

## D. United Kingdom (GB)

**Program:** HMRC Audio-Visual Expenditure Credit (AVEC)
**General Rule:** Only "Core Expenditure" (pre-production, principal photography, post-production) is eligible. Speculative development and marketing are excluded.

| Category | CineGlobe Treatment | Authoritative Rule | Status | Official Source | Required Change | Financial Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1000 DEVELOPMENT** | Included | Speculative development is generally excluded from core expenditure. | **INCORRECT** | [HMRC CREC Manual](https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual) | Exclude | Decrease QPE |
| **7300 MARKETING** | Included | Distribution, marketing, and publicity are explicitly excluded from core expenditure. | **INCORRECT** | [HMRC CREC Manual](https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual) | Exclude | Decrease QPE |
| **8300 CONTINGENCY** | Excluded | May be included in projected core expenditure if ultimately spent on qualifying core activities. | **CONDITIONAL** | [HMRC CREC Manual](https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual) | Reassess | Increase QPE (Potentially) |

---

## E. Australia (AU)

**Program:** Australian Location Offset (Qualifying Australian Production Expenditure - QAPE)
**General Rule:** Expenditure must relate to the making of the film in Australia. Marketing is excluded. Contingency is excluded unless realized.

| Category | CineGlobe Treatment | Authoritative Rule | Status | Official Source | Required Change | Financial Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1000 DEVELOPMENT** | Included | Eligible if directly related to the making of the film and incurred in Australia, subject to timing rules. | **CONDITIONAL** | [Location Offset Guidelines](https://www.arts.gov.au/funding-and-support/tax-rebates-film-and-television-producers) | Verify timing | None (if verified) |
| **7300 MARKETING** | Included | Marketing, promotion, and distribution are specifically excluded from QAPE. | **INCORRECT** | [Income Tax Assessment Act (Div 376)](https://www.arts.gov.au/funding-and-support/tax-rebates-film-and-television-producers) | Exclude | Decrease QPE |
| **8300 CONTINGENCY** | Excluded | Contingency amounts not yet spent are ineligible for QAPE. | **CORRECT** | [Location Offset Guidelines](https://www.arts.gov.au/funding-and-support/tax-rebates-film-and-television-producers) | None | None |

---

## F. Conclusion & Recommendations
The current CineGlobe `budget_qpe_trace` structure improperly applies a blanket inclusion for **Marketing (7300)** across MT, GR, GB, and AU, despite it being universally excluded by authoritative sources. **Development (1000)** is also widely included but should be excluded in MU, MT, and GB due to strict "production-only" or "core expenditure" rules. Conversely, **Contingency (8300)** is included in MU (which is incorrect) and excluded everywhere else, missing potential conditional inclusions in GR and GB. 

**Recommendation:** Update the CineGlobe QPE engine to apply jurisdiction-specific flags for Development, Marketing, and Contingency rather than relying on uniform baseline mappings.
