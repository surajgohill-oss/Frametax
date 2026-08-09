# CINEGLOBE INDEPENDENT AUTHORITATIVE QPE VALIDATION REPORT (FULL SECOND PASS)

## Executive Summary
This report provides a comprehensive, independent validation of CineGlobe's QPE (Qualifying Production Expenditure) treatment for the *Little Utopia* project across Mauritius, Malta, Greece, United Kingdom, and Australia. The validation compares CineGlobe's current internal logic (`budget_qpe_trace` and `qualification` constraints) against current, authoritative, publicly available tax incentive guidelines for each jurisdiction.

Major systemic errors were found in how CineGlobe handles **Development**, **Marketing**, and **Contingency**, alongside several significant qualification gating failures (e.g., missing the A$20M Location Offset threshold in Australia while still pricing the jurisdiction).

---

## 1. AUSTRALIA (AU)
**Program:** Australian Location Offset (Div 376 of Income Tax Assessment Act 1997)
**Authority:** [Department of Infrastructure, Transport, Regional Development, Communications and the Arts](https://www.arts.gov.au/funding-and-support/tax-rebates-film-and-television-producers)

### A. QPE / Expenditure Treatment
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **Development (1000)** | Included | Only eligible if incurred *in Australia* and directly related to the making of the film. General/speculative development is excluded. | **CONDITIONAL** | Verify timing and Australian incurrence. |
| **Marketing (7300)** | Included | Marketing, publicity, and distribution are specifically excluded from QAPE under statutory definition. | **INCORRECT** | Exclude 7300 entirely. |
| **Contingency (8300)** | Excluded | Unspent contingency is excluded. | **CORRECT** | None. |
| **Non-local spend** | Not specified | QAPE is strictly limited to goods/services provided in Australia or the use of land located in Australia. | **CONDITIONAL** | Enforce territorial limitation. |

### B. Program Economics & Qualification (Gating)
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **QAPE Threshold** | **Not Enforced** (Priced) | Location Offset requires a minimum A$20M QAPE. *Little Utopia* budget is a few million USD, falling far short of this hard gate. | **INELIGIBLE** | Block pricing if QAPE < A$20M. |
| **Training Obligations** | Not Enforced | Location Offset requires meeting specific capacity building/training obligations for the 30% rate. | **INCORRECT** | Add training obligation gate. |

**Estimated Financial Impact:** **Massive Overstatement.** The project is fundamentally ineligible for the Location Offset due to the A$20M threshold. Treating it as a valid, priced scenario creates a 100% variance.

---

## 2. UNITED KINGDOM (GB)
**Program:** HMRC Audio-Visual Expenditure Credit (AVEC) / Independent Film Tax Credit (IFTC)
**Authority:** [HMRC Creative Industries Expenditure Credit Manual](https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual) / [BFI Guidelines](https://www.bfi.org.uk)

### A. QPE / Expenditure Treatment
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **Development (1000)** | Included | Speculative development is generally excluded from core expenditure. | **INCORRECT** | Exclude. |
| **Marketing (7300)** | Included | Distribution, marketing, and publicity are explicitly excluded from AVEC core expenditure. | **INCORRECT** | Exclude 7300. |
| **Contingency (8300)** | Excluded | May be included in projected core expenditure if ultimately spent on qualifying core activities. | **CONDITIONAL** | Apportion based on projected spend. |
| **UK Use Rule** | Not specified | AVEC replaced "UK spend" with "used or consumed in the UK". Requires strict territorial nexus. | **CONDITIONAL** | Enforce UK Use rule. |

### B. Program Economics & Qualification (Gating)
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **Rates & Caps** | No 80% cap logic apparent | AVEC is capped at 80% of total core expenditure. Standard rate is 34%; IFTC is 53% (for budgets < £15M). Credit is taxable. | **INCORRECT** | Apply 80% core expenditure cap and taxable credit math. Apply 53% IFTC rate if qualified. |
| **Cultural Test** | Acknowledged | Film must pass BFI Cultural Test or qualify as a co-production. | **CORRECT** | None. |

**Estimated Financial Impact:** High. Failure to exclude Marketing and Development inflates the eligible base, while failure to cap eligible spend at 80% of total core expenditure further overstates the credit. If IFTC applies, the rate shifts from 34% to 53%.

---

## 3. GREECE (GR)
**Program:** Hellenic Film and Audiovisual Center / Creative Greece Cash Rebate
**Authority:** [Creative Greece / EKOME Guidelines (Law 4487/2017)](https://www.ekome.media/audiovisual-production-invest/cash-rebate/)

### A. QPE / Expenditure Treatment
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **Development (1000)** | Included | Pre-production/development costs are eligible if directly related to the Greek production. | **CORRECT** | None. |
| **Marketing (7300)** | Included | Marketing, promotion, and communication expenses are strictly ineligible. | **INCORRECT** | Exclude 7300. |
| **Contingency (8300)** | Excluded | Contingency costs are generally eligible under specific actions (e.g., Action A) if justified. | **CONDITIONAL** | Conditionally include. |

### B. Program Economics & Qualification (Gating)
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **Base Rate / Caps** | Not checked for 80% cap | 40% cash rebate. Eligible spend cannot exceed 80% of the total production budget. | **INCORRECT** | Apply 80% total budget cap. |
| **Min Spend / Quals** | Acknowledged | Minimum spend of €100,000 for feature films. Cultural test required. | **CORRECT** | None. |

**Estimated Financial Impact:** Medium. Marketing inclusion overstates QPE. Missing the 80% cap on total budget may result in overclaiming if Greek spend is highly concentrated.

---

## 4. MALTA (MT)
**Program:** Malta Film Commission Cash Rebate
**Authority:** [MFC Financial Incentive Guidelines](https://maltafilmcommission.com/cash-rebate/)

### A. QPE / Expenditure Treatment
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **Development (1000)** | Included | Early development is excluded. Only active pre-production and production costs are eligible. | **INCORRECT** | Exclude early development. |
| **Marketing (7300)** | Included | Marketing and distribution are explicitly ineligible. | **INCORRECT** | Exclude 7300. |
| **Contingency (8300)** | Excluded | Contingency is a reserve and not an incurred cost; therefore ineligible. | **CORRECT** | None. |

### B. Program Economics & Qualification (Gating)
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **Base vs Uplift Rate** | Assumes flat rate | Base rate is typically 30%. Reaching the maximum 40% is discretionary and requires hitting specific cultural/local resource uplift thresholds. | **INCORRECT** | Separate 30% base from 10% conditional uplift. |
| **Timing / Local SPV** | Acknowledged | Provisional approval required at least 30 working days prior to principal photography. Local SPV required. | **CORRECT** | None. |

**Estimated Financial Impact:** High. Marketing and development overstate the base. Assuming a flat 40% rate without verifying uplift conditions overstates the rebate yield by 25%.

---

## 5. MAURITIUS (MU)
**Program:** Mauritius Film Rebate Scheme
**Authority:** [Economic Development Board (EDB) Guidelines](https://www.edbmauritius.org/film-rebate-scheme)

### A. QPE / Expenditure Treatment
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **Development (1000)** | Included | Pre-production/development costs incurred before principal photography are generally excluded unless directly tied to local activities. | **INCORRECT** | Exclude general development. |
| **Marketing (7300)** | Excluded | Marketing is non-qualifying. | **CORRECT** | None. |
| **Contingency (8300)** | Included | Unspent contingency is a budget provision, not an incurred local cost. | **INCORRECT** | Exclude 8300. |

### B. Program Economics & Qualification (Gating)
| Category | CineGlobe Treatment | Authoritative Rule | Status | Required Change |
| :--- | :--- | :--- | :--- | :--- |
| **Base vs Uplift Rate** | Not distinguished | Rebate is 30%. The 40% rate is conditional (requires $1M QPE for features or 90% filming in Mauritius). | **INCORRECT** | Apply conditional rules for 40% tier. |
| **Approval / SPV** | Acknowledged | Application at least 4 weeks before filming. Local SPV required. | **CORRECT** | None. |

**Estimated Financial Impact:** Medium-High. Blanket inclusion of contingency (7.5% of budget) overstates the base. Failure to validate the 40% tier criteria could result in a 33% overstatement of the final rebate.

---

## SUMMARY OF FINDINGS

### A. CONFIRMED QPE RULE ERRORS
1. **Marketing (7300):** Systemically included in AU, GB, GR, and MT despite being universally ineligible. 
2. **Development (1000):** Systemically included globally, violating exclusions in MU, MT, and GB.
3. **Contingency (8300):** Included in MU (incorrect) and excluded globally elsewhere, missing conditional inclusions in GB and GR.

### B. CONFIRMED RATE/CAP/THRESHOLD ERRORS
1. **GB 80% Cap & IFTC:** Fails to cap eligible spend at 80% of total core expenditure and does not dynamically apply the 53% IFTC rate.
2. **GR 80% Cap:** Fails to cap eligible spend at 80% of total production budget.
3. **MT & MU Rates:** Assumes maximum 40% rates without testing for the mandatory uplift (MT) or minimum thresholds (MU).

### C. CONFIRMED QUALIFICATION/GATING DEFECTS
1. **AU Location Offset Minimum:** CineGlobe prices Australia despite the project falling massively short of the A$20M QAPE hard gate threshold.
2. **AU Training Obligations:** Missing checks for statutory training/PDV capacity building requirements.

### D. TERRITORIAL/SPV RULE CORRECTIONS
All jurisdictions require strict territorial incurrence (or "UK Use" for GB). CineGlobe must ensure cross-border spend is strictly excluded unless explicitly permitted by treaty/co-pro.

### E. UNRESOLVED AUTHORITY QUESTIONS
- Exact mechanism for prorating Contingency in GB if partially spent on core vs non-core items.
- Specific points scored on MT cultural test to guarantee the 10% uplift above the 30% base.

### F. CONFIRMED-CORRECT / NO-CHANGE ITEMS
- Cast, Crew, Equipment, Locations, Post-Production, and VFX are correctly flagged as core eligible expenditures across all analyzed jurisdictions (subject to local incurrence).
- Pre-approval timing and local SPV entity requirements are correctly modeled for MU, MT, GR, and GB.
