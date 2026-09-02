# CINEGLOBE MFNI GLOBAL PRODUCTION-COST RESEARCH REPORT
**ENGINE:** GEMINI
**PLATFORM:** CINEGLOBE DEEP RESEARCH
**DATE:** 2026-09-02

## A. EXECUTIVE FINDINGS
1. **Defensibility:** Production cost variations can be defensibly modeled only by unbundling budgets into structural BTL categories (Labor, Fringes, Materials, Equipment, Facilities) and indexing against localized primary data (Guild rates, payroll taxes, PPI/CPI). 
2. **The "Import Penalty":** Nominal labor savings in emerging jurisdictions (e.g., Serbia, Mauritius) are frequently erased by the cost of importing Heads of Department (HODs) and specialized equipment. An effective MFNI must apply an "Import Ratio" scalar based on local crew depth.
3. **Excluded Variables:** Travel and Incentives are strictly excluded. Above-the-Line (ATL) is held constant, as star/director quotes do not discount based on shooting location.
4. **Currency Dynamics:** The most significant volatility in international production costs stems from FX fluctuations, not local inflation. MFNI must store all raw observations in local currency and dynamically convert using CineGlobe's real-time FX engine.

## B. MFNI METHODOLOGY RECOMMENDATION
To evaluate cost differences independently of incentives, CineGlobe should adopt a **Category-Weighted Multiplier Approach**:
1. Map the Source Budget into standard CineGlobe BTL categories.
2. For each category, query the `mfni_jurisdiction_factor` for the target jurisdiction.
3. Apply the **Local/Import Ratio**: 
   `Adjusted_Factor = (Local_Capacity_%) * Local_Factor + (Imported_%) * Source_Factor`.
4. Apply dynamic FX conversion to the Adjusted_Factor.
5. Multiply the Source Budget Category by the Adjusted_Factor to yield the Normalized Category Cost.

## C. COST-CATEGORY MATRIX
| Category | Normalize? | Why? | Best Data Source(s) | Update Freq | Geo Granularity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CREW LABOR** | YES | Huge variance in base rates & overtime rules | Guild Agreements (IATSE, BECTU), EP | Annual | State/Province/City |
| **FRINGES** | YES | Statutory variance (e.g., UK 13.8% NIC vs US ~22%+) | Payroll providers (EP, Cast & Crew) | Annual | State/Country |
| **STAGES** | YES | Real estate markets dictate pricing | Film Commission rate sheets, Studio published rates | Bi-Annual | City/Hub |
| **EQUIPMENT** | PARTIAL | Cameras are global; Grip/Lighting is local | Panavision/ARRI local rate cards | Annual | Country |
| **LOCATIONS** | YES | Municipal fee structures vary | Film Commissions | Annual | City/State |
| **CONSTRUCTION** | YES | Material and local labor costs vary heavily | National PPI (Lumber/Steel), Local wage indices | Quarterly | Country |
| **HOTEL/PER DIEM** | YES | Local cost of living | GSA/State Dept Per Diem rates, Corporate indices | Quarterly | City |
| **CATERING** | YES | Local food costs | National CPI (Food) | Quarterly | Country |
| **POST/VFX** | YES (If moved) | Highly localized labor & fringe markets | Local VFX association rate cards | Annual | Country/State |
| **ATL / TRAVEL / INS.**| **NO** | Excluded by definition or invariant | N/A | N/A | N/A |

## D. JURISDICTION COVERAGE MATRIX
| Jurisdiction | Evidence | Source Quality | Recommended Granularity | Crew Depth / Import Needs |
| :--- | :--- | :--- | :--- | :--- |
| United States | SUFFICIENT | Tier 1 (IATSE, EP) | State / Hub (LA/NY/ATL) | 100% Local capable |
| Canada | SUFFICIENT | Tier 1 (DGC, IATSE) | Province (BC, ON, QC) | 100% Local capable |
| United Kingdom | SUFFICIENT | Tier 1 (BECTU) | London vs Nations/Regions | 100% Local capable |
| Australia | SUFFICIENT | Tier 1/2 (MEAA) | State | 95% Local capable |
| New Zealand | SUFFICIENT | Tier 2 (SIGZ) | Country | 90% Local capable (some HODs imported) |
| Western Europe | SUFFICIENT | Tier 2 (Local guilds) | Country | 80-95% Local capable |
| Central/East EU | PARTIAL | Tier 2/3 (Service Co.) | Country (Hungary, Czech) | 70% Local (HODs often imported) |
| South Africa | PARTIAL | Tier 2 (Service Co.) | Country | 80% Local |
| Latin America | PARTIAL | Tier 3 | Country (Mexico, Colombia) | 60-80% Local |
| Mauritius/Middle East| INSUFFICIENT| Tier 4 | Country | High Import Requirement |

## H. CONSOLIDATED ADJUSTMENT METHODOLOGY
MFNI rolls individual adjustments into a single producer-facing percentage:
1. `Sum(Normalized BTL Categories) = Target_BTL`
2. `Sum(Source BTL Categories) = Source_BTL`
3. `Consolidated_Adjustment_$ = Target_BTL - Source_BTL`
4. `Consolidated_Adjustment_% = (Consolidated_Adjustment_$ / Source_BTL) * 100`

This ensures the adjustment is budget-weighted. A budget with 50% stage costs will skew toward the Stage multiplier, whereas a location-heavy indie will skew toward Location/Hotel multipliers.

## I. CONFIDENCE / RANGE MODEL
The system must generate a range based on source quality:
* **Tier 1 Data (High Confidence):** Base Factor ± 3%
* **Tier 2 Data (Med Confidence):** Base Factor ± 7%
* **Tier 3 Data (Low Confidence):** Base Factor ± 15%
* **Import Volatility:** Add ± 5% if Crew Depth < 80% (accounting for unpredictable import costs).
The UI should present the recommendation as: `Recommended: -8.4% (Range: -5.5% to -11.3%) [Confidence: MEDIUM]`.

## J. DATA UPDATE STRATEGY
* **Dynamic (Real-Time):** FX Rates (Applied at calculation runtime).
* **Quarterly:** Construction/Materials (PPI), Hotels/Per Diem (Gov indices), Catering (CPI).
* **Annually:** Labor Rates (Guild master agreements), Fringes (Statutory tax year changes).
* **Bi-Annually (Every 2 Years):** Stage rates, general location municipal fees.

## K. GAPS & INSUFFICIENT DATA
1. **Emerging Markets:** Jurisdictions like Mauritius, Saudi Arabia, and parts of Latin America lack transparent, centralized rate cards. Quotes rely heavily on proprietary production service company estimates (Tier 3/4).
2. **Non-Union Buyouts:** In markets without strict guild structures (e.g., parts of Eastern Europe), crew rates are often negotiated as flat weeklies without standardized overtime. This makes strict apples-to-apples comparison with IATSE hourly+penalty structures mathematically difficult without empirical historical data.
3. **Specialized Equipment:** Extreme specialty gear (Technocranes, specific anamorphic lenses) often must be shipped from London/LA, incurring freight and carnet costs that are difficult to index generically.
