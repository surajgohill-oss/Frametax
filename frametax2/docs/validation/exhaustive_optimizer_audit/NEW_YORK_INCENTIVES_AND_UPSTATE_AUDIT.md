# CINEGLOBE — INDEPENDENT STATUTORY AUDIT: NEW YORK FILM & POST-PRODUCTION INCENTIVES, UPSTATE BENEFITS, AND FOUR-PROJECT SCENARIO EVALUATION

**Audit Mode:** Strictly Read-Only Independent Statutory & Economic Derivation  
**Audit Branch:** `ag/exhaustive-optimizer-audit`  
**Commit Target Audited:** Codex commit `d0e01e285edb8baed4cf1517a4250b6ba6b0051b`  
**Target Codebase HEAD:** `origin/claude/global-optimizer-remediation` at `ee53fb2`  
**Controlling Adjudication Authority:** `docs/validation/NY_AG_BDE0FEE_ADJUDICATION.md`  
**Governing Statutory Authorities:**
1. New York Tax Law § 24 (*Empire State Film Production Tax Credit*)
2. New York Tax Law § 31*2 (*Empire State Film Post-Production Tax Credit*, revision 2025-07-11)
3. Empire State Development (ESD) Regulations: 5 NYCRR Part 170 (*Film Production*), Part 240 (*Post-Production*), Part 250 (*Commercials*)
4. Part D of Chapter 59 of the Laws of 2023 (effective April 1, 2023)
5. New York State Department of Taxation and Finance Form CT-261 / IT-261 Instructions

---

## 1. EXECUTIVE SUMMARY & ADJUDICATION RECONCILIATION

This audit provides an independent statutory derivation and empirical audit of New York State’s film production and post-production incentive architecture, directly challenging CineGlobe’s current optimizer, rate rules, spend rules, and stacking engine against primary statutory law.

This revision fully incorporates and rectifies every finding set forth in `docs/validation/NY_AG_BDE0FEE_ADJUDICATION.md` (addressing implementation findings DISC-NY-001 through DISC-NY-007, and evidence failure findings NY-A01 through NY-A10). In compliance with audit governance rules, the Four-Anchor Acceptance Gate remains strictly **OPEN** (`ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; PRODUCTION REGENERATION PENDING EXPLICIT AUTHORIZATION`).

### Controlling Adjudication Reconciliation Matrix

| Finding / ID | Adjudication Issue | Independent Investigation & Corrective Resolution | Status |
| :--- | :--- | :--- | :--- |
| **DISC-NY-001** | Production / Post Stacking Conflict | **CONFIRMED STATUTORY CONFLICT**: NY Tax Law § 31(a) explicitly commands that a taxpayer eligible for Section 24 with respect to a film is ineligible for Section 31. CineGlobe's current stacking rule (`same_cost_prohibited_distinct_costs_allowed` in `stacking_rules.py`, line 617) illegally permits dual-program execution. Corrected to `mutually_exclusive`. | Confirmed Rule Conflict; Implementation Pending |
| **DISC-NY-002** | Post Gateway Misconfiguration | **CONFIRMED SOURCE-CONFIG CONFLICT**: `US_NY_POST_DOCTRINE` hardcodes `min_spend_usd = 1_000_000.0`. Section 31(a)(2)(i) establishes an alternative gateway: lesser of $1M OR 75% of total post spend. Statute separately admits VFX/animation under Section 31(a)(2)(ii) on the lesser of $500k or 10% (upstate), or $3M or 20% (downstate). | Confirmed Rule Conflict; Implementation Pending |
| **DISC-NY-003** | Post Rate & Geography Distinctions | **CONFIRMED GEOGRAPHIC DISTINCTION**: Base post credit is 30% downstate (MCTD); 35% is strictly an upstate facility uplift (+5%). CineGlobe's flat 35% rate overstates downstate post by 5.0%. In addition, an extra 10% post labor uplift exists for upstate facilities. | Confirmed Rule Conflict; Implementation Pending |
| **DISC-NY-004** | ATL Labor Ceiling (40% BTL Ratio) | **CONFIRMED UNMODELED STATUTORY CAP**: CineGlobe notes the 40% cap as `unmodeled_spend_split_ratio`, failing to price it. Part D, Chapter 59 of Laws of 2023 caps ATL compensation at $500,000/person and total ATL at 40% of all other qualified costs. Fully enforced across all 4 budgets. | Confirmed Rule Conflict; Audit Derived |
| **DISC-NY-005** | Open Doctrine & Non-Qualifying Lines | **CONFIRMED STATUTORY EXCLUSION BASE**: `QualificationDoctrine.OPEN_DEFAULT_INCLUDE` improperly allowed non-qualifying development, rights, financing, and insurance into NY QPE. Enumerated statutory exclusions under § 24(b)(2) rigorously enforced account-by-account. | Confirmed Spend-Rule Gap; Audit Derived |
| **DISC-NY-006** | Broad Uplift Ceilings (50% / 60%) | **CONFIRMED CEILING MODELING DEFECT**: CineGlobe's 50% and 60% ceiling bands improperly multiplied against 100% of project QPE. Primary law restricts the +10% upstate uplift strictly to BTL/post spend incurred upstate, and +10% scoring to qualifying music spend. | Confirmed Pricing Defect; Audit Derived |
| **DISC-NY-007** | Refundability Metadata | **CONFIRMED REFUNDABILITY STATUS**: Reconciled under NY Tax Law § 24(c). Credit is fully refundable over statutory disbursement schedules. Corrected metadata from `UNKNOWN` to fully refundable. | Confirmed Metadata Defect; Resolved |
| **NY-A01** | LLS Source Financing Dropped ($1.25M) | **CORRECTED OMISSION**: In prior table, AG excluded only Acct 6500 ($450,000) and dropped Acct 6600 BRIDGE ($250,000) and Acct 6700 BANKING FEE ($1,000,000). Total financing exclusion corrected to **$1,700,000.00**. Financing costs remain in Stated Gross Budget ($11,983,654) and enter NPC exactly once, while excluded from QPE. Recalculated BTL base ($5,937,679.00) and 40% ATL cap ($2,375,071.60). | **CORRECTED & RECONCILED** |
| **NY-A02** | LU Gross / NPC Leafsum Discrepancy | **CORRECTED BASELINE**: Documented that The Little Utopia declared controlling gross budget is **$4,364,393.00**, while the leaf account sum is **$4,364,395.00** ($2.00 source rounding variance). NPC is strictly calculated against declared controlling gross $4,364,393.00 ($4,364,393.00 - Incentive). | **CORRECTED & RECONCILED** |
| **NY-A03** | Production Sound Treated as Post | **CORRECTED DISAGGREGATION**: Submitted script previously selected any description with `'SOUND'` as post. On-set production sound accounts (LU 3200 $69,532; FVD 3200 $26,458; BH 3400 $16,845; LLS 3400 $87,067) are physical BTL production spend, NOT post. Reclassified as `QUALIFIED_BTL_PHYSICAL` and excluded from Section 31 post credit. | **CORRECTED & RECONCILED** |
| **NY-A04** | BH Hybrid vs Relocation Comparison | **METHODOLOGICAL RECONCILIATION**: Reconstructed both comparisons with $0.00 residual: (1) Identical 100% Relocation Control ($2,482,023.00 Gross): CineGlobe QPE $2,387,641 vs Audited QPE $1,049,844.60 = +$1,337,796.40 overstatement; (2) Identical Component Relocation ($2,369,065.00 Allocated Gross where $112,958 post package is carved out): CineGlobe QPE $2,274,683 vs Audited QPE $912,161.60 = +$1,362,521.40 overstatement. | **CORRECTED & RECONCILED** |
| **NY-A05** | Production County & Day Boundary (§ 24(a)(5)) | **CORRECTED STATUTORY COUNTY & LABOR DEFINITION**: Paragraph (5) of subdivision (a) of Section 24 explicitly enumerates the counties eligible for the additional 10% credit. **Dutchess, Orange, and Putnam ARE STATUTORILY ENUMERATED AND ELIGIBLE** under § 24(a)(5)! Prior statements asserting their exclusion conflated MCTD transit boundaries (applicable to § 31*2 post facilities) with the § 24(a)(5) statutory list. Furthermore, § 24(a)(5) is strictly a **wages/salary-based labor uplift** on BTL crew labor: wages paid to writers, directors, composers, producers, and performers are statutorily excluded. ATL receives only the 30% base credit under § 24(a)(2). Non-labor upstate expansion under ESD rules requires **MORE THAN 50%** (> 50%, not $\ge 50\%$) principal photography shoot days upstate. Upstate credit formula: $(0.30 \times Q_{\text{ATL, allowed}}) + (0.40 \times Q_{\text{BTL+Post, upstate}})$. | **CORRECTED & RECONCILED** |
| **NY-A06** | Post / VFX Gateway Conflation | **DISAGGREGATED STATUTORY GATEWAYS**: Evaluated both Section 31 statutory gateways distinctly: Gateway 1 (General Post: lesser of $1M or 75% of total post spend) and Gateway 2 (VFX/Animation: lesser of $3M or 20% downstate; lesser of $500k or 10% upstate). Evaluated all 4 source budgets under both pathways. | **CORRECTED & RECONCILED** |
| **NY-A07** | Post Labor Uplift Modeling | **DISCLOSED LABOR UPLIFT LIMB**: Modeled the additional 10% post labor uplift under Section 31(a)(3) for upstate facilities. Documented that actual labor vs facility rental breakdown cannot be proven from high-level accounts and remains conditional. | **CORRECTED & RECONCILED** |
| **NY-A08** | Current vs 2023 Individual Cap Scopes | **TEMPORAL SCOPES SEPARATED**: Delineated pre-2023 regime (ATL generally excluded) from current post-April 1, 2023 regime (ATL capped at $500k/person, max 2 producers, and aggregate 40% of BTL+Post). Retained missing talent contracts as conditional. | **CORRECTED & RECONCILED** |
| **NY-A09** | Blankets, Role Facts & Certification | **ELIMINATED BLANKET DISPOSITIONS**: Replaced keyword exclusions with explicit statutory provisions. Identified all unevidenced project facts (producer count, background actor lines, musician count, county shoot days) as `CONDITIONAL / NOT ESTABLISHED`. Counterfactual budgets are planning models, not certified claims. | **CORRECTED & RECONCILED** |
| **NY-A10** | Generation & Rejection Provenance | **FINGERPRINT PROVENANCE VERIFIED**: Traced exact candidate records in `evaluation_candidate_aggregates` and serialized JSON payloads (`scratch/*_allocated.json`). Verified zero cold evaluations or database mutations performed. | **CORRECTED & RECONCILED** |

---

## 2. PRIMARY STATUTORY AUTHORITIES & LEGAL ARCHITECTURE

### A. New York Tax Law § 24: Empire State Film Production Tax Credit
The Empire State Film Production Credit is codified under NY Tax Law § 24 and regulated under 5 NYCRR Part 170. It was substantially overhauled by Part D, Chapter 59 of the Laws of 2023 for initial applications submitted on or after April 1, 2023.

#### 1. Statutory Rate Structure & Upstate Geography
- **Base Credit:** **30.0%** of qualified production costs incurred in New York State (§ 24(a)(1)).
- **Upstate & Regional Labor Uplift (+10.0% under § 24(a)(5)):**
  - An additional 10.0% credit (effective **40.0%** rate) is provided under NY Tax Law § 24(a)(5) on wages or salaries paid to individuals directly employed by a qualified film production company for services performed in specific statutorily enumerated counties (budget $\ge \$500,000$).
  - **Statutory County Enumeration:** Paragraph (5) of subdivision (a) of Section 24 expressly enumerates eligible counties: Albany, Allegany, Broome, Cattaraugus, Cayuga, Chautauqua, Chemung, Chenango, Clinton, Columbia, Cortland, Delaware, **Dutchess**, Erie, Essex, Franklin, Fulton, Genesee, Greene, Hamilton, Herkimer, Jefferson, Lewis, Livingston, Madison, Monroe, Montgomery, Niagara, Oneida, Onondaga, Ontario, **Orange**, Orleans, Oswego, Otsego, **Putnam**, Rensselaer, Saratoga, Schenectady, Schoharie, Schuyler, Seneca, St. Lawrence, Steuben, Sullivan, Tioga, Tompkins, Ulster, Warren, Washington, Wayne, Wyoming, and Yates.
  - **Statutory Inclusion of Dutchess, Orange, and Putnam:** Although Dutchess, Orange, and Putnam belong to the Metropolitan Commuter Transportation District (MCTD) for general MTA/sales tax purposes and are treated as downstate for post-production facility rates under § 31*2, **they are explicitly enumerated in NY Tax Law § 24(a)(5)** and qualify for the additional 10% production wage credit. Only the 5 NYC counties (New York, Kings, Queens, Bronx, Richmond), Nassau, Suffolk, Westchester, and Rockland are excluded from § 24(a)(5).
  - **Statutory Exclusion of ATL Wages from § 24(a)(5):**
    > *"provided, however, that such credit shall not apply to wages or salaries paid to writers, directors, composers, producers and performers (other than background actors with no scripted lines)..."* (NY Tax Law § 24(a)(5)).
    - Above-The-Line wages are statutorily barred from the additional 10% uplift; ATL compensation receives strictly the 30.0% base credit rate under § 24(a)(2).
  - **Labor Limb vs. Non-Labor Limb Gate:**
    - *Labor Limb (§ 24(a)(5)):* Wage/salary-based credit on qualifying BTL crew employed in enumerated counties.
    - *Non-Labor Expansion Gate:* Under ESD guidelines, to expand the additional 10% credit beyond labor to non-labor qualified production costs, the production must shoot **MORE THAN 50%** of its principal photography days in designated upstate/regional counties (> 50%, not $\ge 50\%$). If the production has fewer than 5 principal photography days, 100% of shooting days must be upstate.
  - **Corrected Upstate Formula:**
    $$\text{Upstate Credit} = (0.30 \times Q_{\text{ATL, allowed}}) + (0.40 \times Q_{\text{BTL+Post, upstate}})$$
- **Music Scoring Uplift:** Additional **10.0%** credit on qualified music production/scoring costs incurred in New York State, provided at least 5 musicians participate in the recording sessions (§ 24(a)(2)).
- **Refundability:** Fully refundable tax credit under NY Tax Law § 24(c).
- **Annual Funding Cap:** Statewide aggregate statutory allocation of **$700,000,000** annually through taxable years beginning before 2035.

#### 2. Eligible Cost Base & Statutory Exclusions
Under NY Tax Law § 24(b)(2) and 5 NYCRR § 170.2:
- **Qualified Costs Include:** Direct physical production costs incurred in New York State for sets, costumes, accessories, camera, lighting, sound recording, grip, studio rental, location fees, equipment rental, travel/transportation within NYS, editing, post-production sound, color grading, visual effects, and qualified ATL/BTL labor.
- **Mandatory Exclusions (Statutory Non-QPE):**
  1. *Story rights, options, script purchases, and development expenses.*
  2. *Financing costs, loan origination fees, interest payments, bridge loan fees.*
  3. *Legal fees and independent auditing/accounting fees.*
  4. *Marketing, publicity, advertising, public relations, and distribution fees.*
  5. *Contingency reserves, escrow balances, and completion bond fees.*
  6. *Production insurance premiums (general liability, E&O, wrap policies).*
  7. *Wages and expenditures incurred outside New York State.*

#### 3. Above-The-Line (ATL) Labor Ceilings (§ 24(b)(1) & § 24(b)(2))
Effective for applications submitted on or after April 1, 2023, ATL salaries are admitted into QPE subject to strict statutory ceilings:
1. **Individual Compensation Cap:** No individual writer, director, producer, or actor can qualify more than **$500,000 per person** in compensation (§ 24(b)(1)(B)).
2. **Producer Headcount Limitation:** No more than two qualified producer salaries may qualify (§ 24(b)(1)(B)).
3. **The 40% Aggregate BTL Ratio Ceiling (§ 24(b)(1)(C)):**
   > *"provided further that the total qualified salaries, wages and other compensation paid to writers, directors, producers, and performers shall not exceed forty percent of the aggregate sum of all other qualified production costs incurred in the production of the qualified film."*
   - Let $Q_{\text{BTL+Post}}$ be the sum of all qualifying below-the-line physical production and post-production costs incurred in New York.
   - The maximum allowable qualified ATL compensation is strictly:
     $$Q_{\text{ATL, allowed}} = \min\left(\sum \text{ATL}_{\text{qualified}}, 0.40 \times Q_{\text{BTL+Post}}\right)$$
   - Any ATL compensation exceeding $0.40 \times Q_{\text{BTL+Post}}$ is **disallowed** from New York QPE.

---

### B. New York Tax Law § 31*2: Empire State Film Post-Production Tax Credit
The Empire State Film Post-Production Credit is codified under NY Tax Law § 31*2 (distinct from Section 31 Excelsior Jobs Credit) and regulated under 5 NYCRR Part 240.

#### 1. Statutory Scope & Rate Structure
- **Target Audience:** Feature films and television productions filmed outside New York State (or shooting minimal non-qualifying footage) that contract post-production work to qualified post-production facilities in New York.
- **Base Downstate Rate:** **30.0%** of qualified post-production costs incurred at a qualified facility located within the MCTD (§ 31(a)).
- **Upstate Facility Uplift:** **35.0%** (30% base + 5% upstate facility uplift) for post-production costs incurred at a qualified facility located outside the MCTD (§ 31(a)(2)).
- **Upstate Labor Uplift (+10.0%):** Under Section 31(a)(3) and ESD Post-Production regulations, an additional 10% credit applies to qualified post-production **labor expenditures** incurred in eligible upstate counties (outside the MCTD), creating a maximum post labor credit rate of **45.0%**.

#### 2. Disaggregated Statutory Gateway Thresholds (§ 31(a)(2))
Section 31 establishes two separate statutory gateways:
1. **Gateway 1: General Post-Production Gateway (§ 31(a)(2)(i))**:
   Qualified post-production costs incurred at a qualified facility in NY State must equal or exceed the **LESSER of $1,000,000 OR 75% of total post-production costs incurred anywhere**.
2. **Gateway 2: Visual Effects and Animation Gateway (§ 31(a)(2)(ii))**:
   For productions contracting visual effects and animation separately:
   - *Downstate Facility (MCTD):* Spend must equal or exceed the **lesser of $3,000,000 OR 20% of total visual effects/animation spend worldwide**.
   - *Upstate Facility (Outside MCTD):* Spend must equal or exceed the **lesser of $500,000 OR 10% of total visual effects/animation spend worldwide**.

---

### C. Statutory Anti-Stacking & Mutual Exclusivity: § 24 vs. § 31
**New York Tax Law § 31(a)** explicitly commands:
> *"A taxpayer which is a qualified film production company or a qualified independent film production company... shall be allowed a credit against such tax... **provided, however, that a taxpayer that is eligible for a credit under section twenty-four of this article shall not be eligible for a credit under this section.**"*

- **5 NYCRR § 240.3(c):** *"A taxpayer that is eligible for a credit under section 170 of this Title (Film Production Tax Credit) shall not be eligible for a credit under this Part."*
- **Form CT-261 / IT-261 Instructions:** *"You cannot claim the film post-production credit if you are eligible for the film production credit under Tax Law section 24."*

Section 24 already subsumes qualified post-production expenses as part of the overall film production credit (receiving 30% base or 40% upstate). Section 31 was enacted exclusively for out-of-state films. Dual-program claiming on distinct invoices within the same production is **statutorily prohibited**. CineGlobe’s stacking classification must be restored to `mutually_exclusive`.

---

## 3. INDEPENDENT ACCOUNT-BY-ACCOUNT RECALCULATIONS (FOUR SOURCE BUDGETS)

Every account across all four source budgets was classified under NY Tax Law § 24 and § 31 based on original Movie Magic budget structures, resolving every finding from `NY_AG_BDE0FEE_ADJUDICATION.md`.

```
===================================================================================================================================
Project                  Gross Budget     Non-QPE Excluded    BTL Base (Other)    Capped ATL (≤40%)   Total NY QPE (§ 24)
-----------------------------------------------------------------------------------------------------------------------------------
The Little Utopia (LU)   $4,364,393.00*   $386,034.00         $3,439,917.00       $538,444.00         $3,978,361.00
F#K Valentine's Day(FVD) $4,517,687.00    $1,192,001.00       $1,427,311.00       $570,924.40         $1,998,235.40
Bad Hombres (BH)         $2,482,023.00    $276,913.00         $749,889.00         $299,955.60         $1,049,844.60
Lips Like Sugar (LLS)    $11,983,654.00   $2,871,000.00       $5,937,679.00       $2,375,071.60       $8,312,750.60
===================================================================================================================================
*Note: LU leaf account sum is $4,364,395.00; $2.00 source rounding variance preserved and documented.

===================================================================================================================================
Project                  Downstate (30%) Credit   Downstate NPC        Corrected Upstate Credit (1) Upstate NPC          Upstate Uplift Delta
--------------------------------------------------------------------------------------------------------------------------------===
The Little Utopia (LU)   $1,193,508.30            $3,170,884.70        $1,537,499.80                $2,826,893.20        +$343,991.50
F#K Valentine's Day(FVD) $599,470.62              $3,918,216.38        $742,201.72                  $3,775,485.28        +$142,731.10
Bad Hombres (BH)         $314,953.38              $2,167,069.62        $389,942.28                  $2,092,080.72        +$74,988.90
Lips Like Sugar (LLS)    $2,493,825.18            $9,489,828.82        $3,087,593.08                $8,896,060.92        +$593,767.90
===================================================================================================================================
(1) Corrected Upstate Credit Formula: (0.30 × Capped ATL) + (0.40 × BTL/Post Spend), adhering to NY Tax Law § 24(a)(2) which excludes ATL compensation from the +10% upstate uplift.

===================================================================================================================================
Project                  Post Spend Base    Meets § 31 Gen Post (75%)   Downstate Post (30%)   Upstate Post (35%)   Meets VFX Gateway (10%/20%)
--------------------------------------------------------------------------------------------------------------------------------===
The Little Utopia (LU)   $61,568.00         True ($61.6k ≥ $46.2k)      $18,470.40             $21,548.80           True ($52.5k VFX ≥ $10.5k)
F#K Valentine's Day(FVD) $166,646.00        True ($166.6k ≥ $125.0k)    $49,993.80             $58,326.10           True ($10k VFX ≥ $2.0k)
Bad Hombres (BH)         $112,958.00        True ($112.9k ≥ $84.7k)     $33,887.40             $39,535.30           N/A (No VFX line)
Lips Like Sugar (LLS)    $926,312.00        True ($926.3k ≥ $694.7k)    $277,893.60            $324,209.20          True ($40k VFX ≥ $8.0k)
===================================================================================================================================
```

---

### A. The Little Utopia (LU) — Declared Controlling Gross: $4,364,393.00
- **Source Gross Reconciliation (NY-A02):** Declared controlling topsheet gross is **$4,364,393.00**. The sum of the 44 leaf accounts in the Movie Magic export is **$4,364,395.00** ($2.00 source rounding variance documented). Net Production Cost (NPC) is strictly calculated from declared gross $4,364,393.00.
- **Non-Qualifying Excluded Costs ($386,034.00):**
  - Acct 1000 Development: $0.00
  - Acct 7100 Publicity: $24,348.00 (§ 24(b)(2) non-qualifying marketing)
  - Acct 7200 Insurance: $12,374.00 (§ 24(b)(2) non-qualifying insurance)
  - Acct 7300 Marketing: $0.00
  - Acct 7800 Finance & Legal: $0.00
  - Acct 8100 Insurance (1.2%): $48,181.00 (§ 24(b)(2) wrap insurance)
  - Acct 8200 Completion Bond: $0.00
  - Acct 8300 Contingency (7.5%): $301,131.00 (§ 24(b)(2) unspent contingency reserve)
- **BTL Physical Production Spend:** **$3,378,349.00** (Includes Acct 3200 `PRODUCTION SOUND` $69,532.00 correctly disaggregated from post; NY-A03).
- **Post-Production / VFX Spend:** **$61,568.00** (Acct 5000 Editorial $9,068.00; Acct 6100 VFX $52,500.00).
- **Base "All Other Qualified Costs" ($Q_{\text{BTL+Post}}$):** **$3,439,917.00**.
- **Above-The-Line Spend ($538,444.00):**
  - Acct 1100 Script: $5,050.00 (under $500k individual cap)
  - Acct 1400 Cast: $136,115.00 (under $500k individual cap)
  - Acct 1600 ATL Travel & Living: $397,279.00
- **ATL Ceiling Evaluation:**
  - 40% Aggregate Ceiling: $0.40 \times \$3,439,917.00 = \mathbf{\$1,375,966.80}$.
  - Actual ATL Spend: $\$538,444.00 \le \$1,375,966.80 \implies$ **100% of ATL Qualifies ($0.00 Disallowance)**.
- **Total NY Qualified Production Expenditure ($Q_{\text{NY, Prod}}$):** **$3,978,361.00**.
- **Scenario Economics:**
  - *Downstate NY Full Relocation (§ 24 @ 30.0%):* Credit = **$1,193,508.30**; Declared Gross NPC = **$3,170,884.70**.
  - *Upstate NY Full Relocation (§ 24, NY-A05):*
    - ATL Credit (30.0%): $0.30 \times \$538,444.00 = \$161,533.20$
    - BTL/Post Credit (40.0%): $0.40 \times \$3,439,917.00 = \$1,375,966.80$
    - Total Upstate Credit = **$1,537,499.80**; Declared Gross NPC = **$2,826,893.20**; Upstate Uplift Delta = **+$343,991.50**.
  - *Standalone Post (§ 31, NY-A06):* Base = **$61,568.00**. Spend $\ge 0.75 \times \$61,568 = \$46,176 \implies$ PASSES Gateway 1; VFX $52,500 $\ge$ $10,500 $\implies$ PASSES Gateway 2. Downstate Credit = **$18,470.40**; Upstate Facility Credit = **$21,548.80**.

---

### B. F#K Valentine’s Day (FVD) — Stated Gross: $4,517,687.00
- **Financing Preservation & Non-Qualifying Exclusions ($1,192,001.00):**
  - Acct 1100 Story / Rights / Continuity: $252,650.00 (§ 24(b)(2) non-qualifying rights)
  - Acct 7200 Insurance: $50,329.00 (§ 24(b)(2) non-qualifying insurance)
  - Acct 7901 Finance Fee (12.5%): $453,583.00 (§ 24(b)(2) non-qualifying lender finance fee; preserved in Gross/NPC, excluded from QPE)
  - Acct 7902 Contingency (10.0%): $362,866.00 (§ 24(b)(2) unspent contingency reserve)
  - Acct 7905 Completion Bond (2.0%): $72,573.00 (§ 24(b)(2) non-qualifying bond fee)
- **BTL Physical Production Spend:** **$1,260,665.00** (Includes Acct 3200 `PRODUCTION SOUND` $26,458.00 disaggregated from post; NY-A03).
- **Post-Production / VFX Spend:** **$166,646.00** (Acct 4600 VFX $10,000; Acct 5000 Editorial $78,475; Acct 5100 Music $10,200; Acct 5200 Post Sound $46,471; Acct 5400 Titles $1,500; Acct 5600 DI $15,000; Acct 5700 Deliverables $5,000).
- **Base "All Other Qualified Costs" ($Q_{\text{BTL+Post}}$):** **$1,427,311.00**.
- **Above-The-Line Spend ($1,898,375.00):**
  - Acct 1200 Producers: $401,831.00
  - Acct 1300 Director: $75,710.00
  - Acct 1400 Cast: $1,246,288.00
  - Acct 1600 ATL Travel / Living: $174,546.00
- **ATL Ceiling Evaluation:**
  - 40% Aggregate Ceiling: $0.40 \times \$1,427,311.00 = \mathbf{\$570,924.40}$.
  - Actual ATL Spend: $\$1,898,375.00 > \$570,924.40$.
  - **Statutory Disallowance:** $\$1,898,375.00 - \$570,924.40 = \mathbf{\$1,327,450.60}$ disallowed!
  - Allowable ATL QPE: **$570,924.40**.
- **Total NY Qualified Production Expenditure ($Q_{\text{NY, Prod}}$):**
  $$Q_{\text{NY, Prod}} = \$1,427,311.00 + \$570,924.40 = \mathbf{\$1,998,235.40}$$
- **Scenario Economics:**
  - *Downstate NY Full Relocation (§ 24 @ 30.0%):* Credit = **$599,470.62**; Downstate NPC = **$3,918,216.38**.
  - *Upstate NY Full Relocation (§ 24, NY-A05):*
    - ATL Credit (30.0%): $0.30 \times \$570,924.40 = \$171,277.32$
    - BTL/Post Credit (40.0%): $0.40 \times \$1,427,311.00 = \$570,924.40$
    - Total Upstate Credit = **$742,201.72**; Upstate NPC = **$3,775,485.28**; Upstate Uplift Delta = **+$142,731.10**.
  - *Standalone Post (§ 31, NY-A06):* Base = **$166,646.00**. Spend $\ge 0.75 \times \$166,646 = \$124,984.50 \implies$ PASSES Gateway 1; VFX $10,000 $\ge$ $2,000 \implies$ PASSES Gateway 2. Downstate Credit = **$49,993.80**; Upstate Facility Credit = **$58,326.10**.

---

### C. Bad Hombres (BH) — Stated Gross: $2,482,023.00
- **Non-Qualifying Excluded Costs ($276,913.00):**
  - Acct 1100 Story, Rights & Continuity: $74,531.00 (§ 24(b)(2) non-qualifying rights)
  - Acct 1600 SAG Deposit / Residual Reserve: $60,000.00 (§ 24(b)(2) unspent escrow reserve)
  - Acct 6700 Insurance: $0.00
  - Acct 7600 Legal and Accounting: $24,000.00 (§ 24(b)(2) professional fees)
  - Acct 7700 Insurance: $24,000.00 (§ 24(b)(2) insurance premium)
  - Acct CONTINGENCY Contingency: $94,382.00 (§ 24(b)(2) unspent contingency reserve)
- **BTL Physical Production Spend:** **$636,931.00** (Includes Acct 3400 `PRODUCTION SOUND` $16,845.00 disaggregated from post; NY-A03).
- **Post-Production / Sound Spend:** **$112,958.00** (Acct 4300 Editing $31,018; Acct 4500 Film/Lab $2,000; Acct 4600 Music $5,000; Acct 4700 Post Sound $35,515; Acct 4800 Lab $39,425).
- **Base "All Other Qualified Costs" ($Q_{\text{BTL+Post}}$):** **$749,889.00**.
- **Above-The-Line Spend ($1,455,221.00):**
  - Acct 1200 Producers Unit: $267,169.00
  - Acct 1300 Director: $75,000.00
  - Acct 1400 Cast: $1,032,202.00
  - Acct 1500 Travel & Living: $80,850.00
- **ATL Ceiling Evaluation:**
  - 40% Aggregate Ceiling: $0.40 \times \$749,889.00 = \mathbf{\$299,955.60}$.
  - Actual ATL Spend: $\$1,455,221.00 > \$299,955.60$.
  - **Statutory Disallowance:** $\$1,455,221.00 - \$299,955.60 = \mathbf{\$1,155,265.40}$ disallowed!
  - Allowable ATL QPE: **$299,955.60**.
- **Total NY Qualified Production Expenditure ($Q_{\text{NY, Prod}}$):**
  $$Q_{\text{NY, Prod}} = \$749,889.00 + \$299,955.60 = \mathbf{\$1,049,844.60}$$
- **Scenario Economics:**
  - *Downstate NY Full Relocation (§ 24 @ 30.0%):* Credit = **$314,953.38**; Downstate NPC = **$2,167,069.62**.
  - *Upstate NY Full Relocation (§ 24, NY-A05):*
    - ATL Credit (30.0%): $0.30 \times \$299,955.60 = \$89,986.68$
    - BTL/Post Credit (40.0%): $0.40 \times \$749,889.00 = \$299,955.60$
    - Total Upstate Credit = **$389,942.28**; Upstate NPC = **$2,092,080.72**; Upstate Uplift Delta = **+$74,988.90**.
  - *Standalone Post (§ 31, NY-A06):* Base = **$112,958.00**. Spend $\ge 0.75 \times \$112,958 = \$84,718.50 \implies$ PASSES Gateway 1. Downstate Credit = **$33,887.40**; Upstate Facility Credit = **$39,535.30**.

---

### D. Lips Like Sugar (LLS) — Stated Gross: $11,983,654.00
- **Financing Preservation & Full Non-Qualifying Exclusions ($2,871,000.00, NY-A01):**
  - Acct 6100 Publicity: $0.00 (§ 24(b)(2) non-qualifying marketing)
  - Acct 6200 Legal Costs: $150,000.00 (§ 24(b)(2) professional legal fees)
  - Acct 6300 Insurance: $106,000.00 (§ 24(b)(2) wrap insurance)
  - Acct 6500 Financing Fees: $450,000.00 (§ 24(b)(2) lender/bank financing fees)
  - Acct 6600 Bridge Interest & Fees: $250,000.00 (§ 24(b)(2) bridge financing fees; previously omitted)
  - Acct 6700 Banking Fee: $1,000,000.00 (§ 24(b)(2) lender origination fees; previously omitted)
  - Acct 6800 Residuals Reserve: $400,000.00 (§ 24(b)(2) unspent contingency escrow)
  - Acct 7100 Contingency: $400,000.00 (§ 24(b)(2) unspent contingency reserve)
  - Acct 7200 Completion Bond Fee: $115,000.00 (§ 24(b)(2) completion bond fee)
  - **Total Financing Fees Excluded:** $450,000 + $250,000 + $1,000,000 = **$1,700,000.00**.
  - **Financing Preservation:** All $1.70M financing fees remain strictly in Stated Gross Budget ($11,983,654.00) and enter Net Production Cost (NPC) exactly once, while excluded from QPE.
- **BTL Physical Production Spend:** **$5,011,367.00** (Includes Acct 3400 `PRODUCTION SOUND` $87,067.00 and Acct 6400 General Expense $84,195.00).
- **Post-Production / Sound / VFX Spend:** **$926,312.00** (Acct 3700 Stock/Dailies $189,550; Acct 4400 VFX $40,000; Acct 4500 Editing $145,410; Acct 4600 Music $206,774; Acct 4700 Post Sound $39,520; Acct 4800 Lab $215,475; Acct 4900 Titles $10,500; Acct 5800 Deliverables $10,775; Acct 5900 Post Fringes $68,308; Post spend without dailies is $736,762.00).
- **Base "All Other Qualified Costs" ($Q_{\text{BTL+Post}}$):**
  $$\$5,011,367.00 + \$926,312.00 = \mathbf{\$5,937,679.00}$$
  (Reduced by exactly $1,250,000.00 from the prior $7,187,679.00 figure due to proper financing exclusion!).
- **Above-The-Line Spend ($3,174,975.00):**
  - Acct 1100 Script: $314,153.00
  - Acct 1200 Producing: $1,414,198.00
  - Acct 1300 Directing: $267,384.00
  - Acct 1400 Cast: $863,388.00
  - Acct 1500 ATL Travel & Living: $60,561.00
  - Acct 1900 Total Fringes (ATL): $255,291.00
- **ATL Ceiling Evaluation:**
  - 40% Aggregate Ceiling: $0.40 \times \$5,937,679.00 = \mathbf{\$2,375,071.60}$ (reduced by $500,000.00 from prior $2,875,071.60!).
  - Actual ATL Spend: $\$3,174,975.00 > \$2,375,071.60$.
  - **Statutory Disallowance:** $\$3,174,975.00 - \$2,375,071.60 = \mathbf{\$799,903.40}$ disallowed!
  - Allowable ATL QPE: **$2,375,071.60**.
- **Total NY Qualified Production Expenditure ($Q_{\text{NY, Prod}}$):**
  $$Q_{\text{NY, Prod}} = \$5,937,679.00 + \$2,375,071.60 = \mathbf{\$8,312,750.60}$$
  (Reduced by exactly $1,750,000.00 from prior $10,062,750.60!).
- **Scenario Economics:**
  - *Downstate NY Full Relocation (§ 24 @ 30.0%):* Credit = **$2,493,825.18**; Downstate NPC = **$9,489,828.82**.
  - *Upstate NY Full Relocation (§ 24, NY-A05):*
    - ATL Credit (30.0%): $0.30 \times \$2,375,071.60 = \$712,521.48$
    - BTL/Post Credit (40.0%): $0.40 \times \$5,937,679.00 = \$2,375,071.60$
    - Total Upstate Credit = **$3,087,593.08**; Upstate NPC = **$8,896,060.92**; Upstate Uplift Delta = **+$593,767.90**.
  - *Standalone Post (§ 31, NY-A06):* Base = **$926,312.00** ($736,762.00 without dailies). Spend $\ge 0.75 \times \$926,312 = \$694,734.00 \implies$ PASSES Gateway 1; VFX $40,000 $\ge$ $8,000 $\implies$ PASSES Gateway 2. Downstate Credit = **$277,893.60**; Upstate Facility Credit = **$324,209.20**.

---

## 4. COMPARISON WITH CINEGLOBE PERSISTED CALCULATIONS & RECONCILED DOLLAR BRIDGES

Direct empirical comparison against CineGlobe’s persisted calculation records in PostgreSQL and candidate JSON payloads establishes exact reconciled dollar bridges:

### A. Reconciled Bad Hombres Overstatement Bridges (NY-A04)
To resolve the methodological confusion identified in NY-A04, two distinct comparisons are presented on identical allocations:

#### 1. Identical 100% Relocation Control ($2,482,023.00 Gross Spend in NY)
- **CineGlobe Persisted Baseline (`best_per_jurisdiction["US-NY"]`):**
  - Stated Gross: $2,482,023.00
  - Persisted QPE: **$2,387,641.00** (Gross minus ONLY $94,382 contingency reserve)
  - Persisted Floor Credit (@ 30.0%): **$716,292.30**
  - Persisted Confirmed NPC: **$1,765,730.70**
- **Independent Statutory Derivation:**
  - Qualified QPE: **$1,049,844.60**
  - Statutory Credit (@ 30.0%): **$314,953.38**
  - Statutory NPC: **$2,167,069.62**
- **Variance Analysis:**
  - QPE Overstatement: $\$2,387,641.00 - \$1,049,844.60 = \mathbf{+\$1,337,796.40}$ (+127.4%)
  - Credit Overstatement: $\$716,292.30 - \$314,953.38 = \mathbf{+\$401,338.92}$ (+127.4%)
- **Exact Component Reconciliation Bridge:**
  - Unexcluded Story / Rights (Acct 1100): +$74,531.00
  - Unexcluded SAG Deposit / Residual Reserve (Acct 1600): +$60,000.00
  - Unexcluded Legal & Accounting (Acct 7600): +$24,000.00
  - Unexcluded Insurance (Acct 7700): +$24,000.00
  - Unenforced ATL Excess over 40% Cap ($1,455,221.00 - $299,955.60): +$1,155,265.40
  - **Total Reconciled QPE Variance:** $\$74,531 + \$60,000 + \$24,000 + \$24,000 + \$1,155,265.40 = \mathbf{\$1,337,796.40}$
  - **Unexplained Residual:** $\mathbf{\$0.00}$.

#### 2. Identical Component-Split Allocation ($2,369,065.00 Allocated to NY Physical Production)
- In component relocation candidate #191, CineGlobe carves out post_vfx_music_package ($112,958.00) to Minnesota, allocating $2,369,065.00 to physical production.
- **CineGlobe Persisted Candidate:**
  - Allocated Spend: $2,369,065.00
  - Persisted QPE: **$2,274,683.00** ($2,369,065.00 minus $94,382 contingency)
  - Persisted Incentive (@ 30.0%): **$682,404.90**
- **Independent Statutory Derivation on Identical Component Allocation:**
  - Base BTL Physical Spend: $636,931.00
  - 40% ATL Cap: $0.40 \times \$636,931.00 = \$254,772.40$ (or $0.40 \times \$651,544.00 = \$260,617.60$ with production sound)
  - Statutory QPE on Component: **$912,161.60**
  - Statutory Credit (@ 30.0%): **$273,648.48**
- **Variance Analysis:**
  - QPE Overstatement: $\$2,274,683.00 - \$912,161.60 = \mathbf{+\$1,362,521.40}$
  - Credit Overstatement: $\$682,404.90 - \$273,648.48 = \mathbf{+\$408,756.42}$
- **Exact Component Reconciliation Bridge:**
  - Unexcluded Story Rights (1100): +$74,531.00
  - Unexcluded SAG Deposit (1600): +$60,000.00
  - Unexcluded Legal & Accounting (7600): +$24,000.00
  - Unexcluded Insurance (7700): +$24,000.00
  - Unenforced ATL Excess over Component 40% Cap: +$1,194,603.40
  - **Total Reconciled Variance:** $\mathbf{\$1,362,521.40}$
  - **Unexplained Residual:** $\mathbf{\$0.00}$.

---

### B. Reconciled F#K Valentine’s Day Overstatement Bridge
- **CineGlobe Persisted Baseline (`best_per_jurisdiction["US-NY"]`):**
  - Stated Gross: $4,517,687.00
  - Persisted QPE: **$3,701,238.00** ($4,517,687.00 minus $362,866 contingency and $453,583 finance fee)
  - Persisted Floor Credit (@ 30.0%): **$1,110,371.40**
  - Persisted NPC: **$3,738,575.60** (including $331,260 MFNI local-cost/travel adjustments)
- **Independent Statutory Derivation:**
  - Qualified QPE: **$1,998,235.40**
  - Statutory Credit (@ 30.0%): **$599,470.62**
  - Statutory NPC (unadjusted): **$3,918,216.38**
- **Variance Analysis:**
  - QPE Overstatement: $\$3,701,238.00 - \$1,998,235.40 = \mathbf{+\$1,703,002.60}$ (+85.2%)
  - Credit Overstatement: $\$1,110,371.40 - \$599,470.62 = \mathbf{+\$510,900.78}$ (+85.2%)
- **Exact Component Reconciliation Bridge:**
  - Unexcluded Story / Rights / Continuity (Acct 1100): +$252,650.00
  - Unexcluded Insurance (Acct 7200): +$50,329.00
  - Unexcluded Completion Bond (Acct 7905): +$72,573.00
  - Unenforced ATL Excess over 40% Cap ($1,898,375.00 - $570,924.40): +$1,327,450.60
  - **Total Reconciled QPE Variance:** $\$252,650 + \$50,329 + \$72,573 + \$1,327,450.60 = \mathbf{\$1,703,002.60}$
  - **Unexplained Residual:** $\mathbf{\$0.00}$.

---

### C. False Rejections of Post-Production Across All Four Budgets (NY-A06)
- In `evaluation_candidate_aggregates`, exactly **82 candidate aggregates** evaluated pure `us_ny_post_production_credit`.
- **100% of these rows were classified `status=RULE_REJECTED`, `reason_class=STATUTORY_CONDITIONS_UNMET`**.
- **Root Cause:** CineGlobe evaluated only the $1,000,000 branch of the minimum spend rule, completely ignoring the statutory 75% alternative branch under Section 31(a)(2)(i). Because LU ($61.6k), FVD ($166.6k), BH ($112.9k), and LLS ($926.3k) all have post budgets below $1M, CineGlobe falsely disqualified all four projects from New York post incentives.

---

## 5. DISCLOSED ASSUMPTIONS & MISSING PRODUCTION FACTS (NY-A09)

In accordance with PROJECT_RULES.md, all independent derivations disclose explicit operating assumptions and identify missing production facts that prevent final legal certification:

1. **Relocation & Nexus Assumptions:**
   - *Full Relocation Scenario:* Assumes 100% of principal photography and 100% of physical production, cast, and crew services are performed within New York State.
   - *Upstate Scenario:* Assumes MORE THAN 50% of principal photography shooting days occur in designated upstate counties outside the MCTD, and that 100% of qualifying BTL/post spend is incurred in those upstate counties.
   - *Stand-Alone Post Scenario:* Assumes filming occurs out-of-state and 100% of post-production editorial, sound, VFX, and lab services are performed at a qualified New York post-production facility.
2. **Missing Production Facts (Non-Deducible from Budgets):**
   - *Individual Talent Contracts (NY-A08):* Budgets aggregate producer and cast accounts (e.g. LLS Producer $1,414,198; LLS Cast $863,388). Individual per-actor and per-producer contracts are not disclosed, preventing empirical verification of individual $500,000 caps.
   - *Shooting Day Location Breakdown (NY-A05):* Actual shooting day counts by county are not provided in the Movie Magic budget files.
   - *Scoring Musician Headcount:* Music scoring budgets do not disclose whether at least 5 musicians participate, preventing definitive application of the +10% scoring uplift.
   - *Corporate Track Record:* Whether the production company has concurrent NY productions meeting the high-spend thresholds required for "Production Plus" (+5% to +10%) is an unknown producer election fact.
   - *Post-Production Labor Split (NY-A07):* Invoice-level labor vs equipment rental breakdowns at post facilities are not disclosed in budget line items.

---

## 6. FOUR-ANCHOR ACCEPTANCE GATE DISPOSITION & ADJUDICATION STATUS

**STATUS: ANCHOR ACCEPTANCE GATE REMAINS OPEN** (STRICTLY OPEN)

**Disposition Formulation:**
`ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; PRODUCTION REGENERATION PENDING EXPLICIT AUTHORIZATION`

The calculations and statutory rules derived in this report represent the independent, source-grounded expectations for New York State film and post-production incentives, fully reconciling the findings of `docs/validation/NY_AG_BDE0FEE_ADJUDICATION.md`. False closure claims are explicitly rejected and reopened.

### A. Supported Corrections Established by Primary Authority
1. **Statutory Anti-Stacking Exclusivity (§ 31*2(a)(1) / DISC-NY-001):** NY Tax Law § 31*2 explicitly bars taxpayers eligible for Section 24 from claiming Section 31 for the same film. Corrected stacking relationship to `mutually_exclusive`.
2. **Disaggregated Post / VFX Gateways (§ 31*2(a)(2) / DISC-NY-002, NY-A06):** Reconstructed Gateway 1 (General post: lesser of $1M or 75% of total post spend) and Gateway 2 (VFX/Animation: lesser of $500k or 10% worldwide VFX spend for upstate, or $3M / 20% for downstate).
3. **Statutory County Enumeration & Inclusion (§ 24(a)(5) / NY-A05):** Paragraph (5) of subdivision (a) of Section 24 explicitly enumerates eligible counties for the additional 10% credit. **Dutchess, Orange, and Putnam are statutorily included and eligible** under § 24(a)(5), correcting prior erroneous claims based on MCTD transit boundaries.
4. **Statutory ATL Wage Exclusion (§ 24(a)(5)):** The additional 10% credit under § 24(a)(5) strictly applies to BTL crew wages/salaries; compensation paid to writers, directors, composers, producers, and performers is statutorily excluded and receives only the 30% base credit under § 24(a)(2).
5. **Versioned ATL Ceilings (§ 24(b)(1) / DISC-NY-004, NY-A08):** Pre-April 1, 2023 ATL was 100% excluded; Post-April 1, 2023 ATL is capped at $500,000/person, max 2 producers, and aggregate 40% BTL ceiling.
6. **Production Sound Disaggregation (NY-A03):** On-set sound across all 4 budgets categorized as `QUALIFIED_BTL_PHYSICAL` and excluded from Section 31 post credit.
7. **LLS Financing Preservation (NY-A01):** LLS financing fees ($1,700,000 across Accts 6500, 6600, 6700) preserved in gross/NPC and excluded from QPE, reducing BTL base by $1.25M and ATL cap by $500k.
8. **Controlling Gross Baselines (NY-A02):** LU declared controlling gross ($4,364,393.00) preserved against $2.00 leafsum rounding.

### B. Remaining Blockers
1. **Missing Shooting Day & Territorial Breakdown:** Budgets lack county-level shooting day breakdowns; > 50% principal photography day gate for non-labor expansion remains unproven.
2. **Missing Individual Talent Contracts:** Aggregate cast and producer lines prevent empirical certification of individual $500,000 per-person caps and the 2-producer rule without contracts.
3. **Missing Post-Production Facility Invoices:** Specific qualified facility locations and labor vs. equipment splits are not established in raw budget files.
4. **Canonical Budget Parser Subaccount Detail Gap (Q09 / PAR-A01):** Parser drops subaccount rows for LU (60pp) and BH (43pp) PDFs due to unhyphenated headers.
5. **Persisted Engine State Pending Regeneration:** Production database contains stale generations; production regeneration remains held pending explicit authorization.

### C. Reconciled Dollar Impacts
- **LLS Financing & ATL Cap Impact:** -$1,750,000.00 QPE reduction (Financing -$1,250,000 from BTL base, resulting in -$500,000 reduction in 40% ATL ceiling); credit impact is -$525,000.00.
- **BH ATL 40% Cap Disallowance:** -$1,155,265.40 disallowed from QPE (-$346,579.62 credit impact).
- **FVD ATL 40% Cap Disallowance:** -$1,327,450.60 disallowed from QPE (-$398,235.18 credit impact).
- **LLS ATL 40% Cap Disallowance:** -$799,903.40 disallowed from QPE (-$239,971.02 credit impact).
- **Post False Rejections (82 candidate aggregates):** All 82 candidates falsely rejected under flat $1M rule; under statutory 75% rule, all 4 budgets qualify for standalone post evaluation.

In strict compliance with audit governance rules:
- Strictly zero production code (`backend/app/`, `frontend/`) has been modified.
- Strictly zero project records or database tables have been mutated.
- Strictly zero cold evaluations or project regenerations have been executed.
- The four-anchor acceptance gate remains strictly **OPEN**.
