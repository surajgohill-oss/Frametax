# Official Program Inventory & Primary Authority Reconciliation (NA & ROW)

**Audit Commit Baseline:** Frozen `canonical-1.122.0` (`59566fd1`).
**Document Purpose:** Delivers the complete program-by-program statutory provenance, inventory reconciliation (identities, RateRules, global inventory, and external official sources), additions, exclusions, aliases, and explicit separation between frozen 1.122 findings and Claude's subsequent remediation code.

---

## 1. Primary Authority & Provenance Register

| Jurisdiction | Program Slug | Program Name & Legislative Authority | Official Primary Citation & URL | Statutory Rules Applied | In-Engine Call Path & Status |
|:---|:---|:---|:---|:---|:---|
| **CA-BC** | `ca_bc_pstc` | British Columbia Production Services Tax Credit (*BC Income Tax Act*, R.S.B.C. 1996, c. 215, Part 5 ss. 79(1), 82.1) | [BC Laws RSBC 1996 c. 215 Part 5](https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/96215_00), [CRA Form T1177 / Guide RC4385](https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4385/film-video-production-services-tax-credit.html), and [Federal Income Tax Act § 125.5(1)](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-125.5.html) | **36% basic labour rate** for shoots commencing post-2024-12-31 (increased from 28% pre-2025). **Dual Assistance Treatment Checked:** (1) **Provincial Treatment (*BC ITA* s. 79(1)):** BC PSTC is calculated on *accredited qualified BC labour expenditure* (AQBCLE) net of government/non-government assistance. Crucially, *BC ITA* s. 79(1) excludes the federal PSTC from being deemed assistance against BC labour. (2) **Federal Treatment (*ITA* § 125.5(1)(b)):** Federal QCLE is Canadian labour expenditure less assistance reasonably considered in respect of that expenditure. Because BC PSTC is paid strictly on accredited BC labour, 100% of the BC credit constitutes labour assistance, reducing federal labour to $(1 - 0.36) = 64\%$ (yielding $16\% 	imes 64\% = 10.24\%$ federal PSTC; combined $46.24\%$ on qualifying BC labour). | `program_rate_rules_worldwide.py:530`; evaluated independently on BC labour lines. |
| **CA-AB** | `ca_ab_fttc` | Alberta Film and Television Tax Credit (*Alberta FTTC Act*, S.A. 2019, c. F-13.5, s. 4) | [Alberta Film and Television Tax Credit](https://www.alberta.ca/film-television-tax-credit) | **22% all-spend base rate**. Minimum total project production cost **CAD 499,999** (\$353,731.16 USD at 1.4135 CAD/USD). | `program_rate_rules_worldwide.py:534`; slice denominator corrected to project gross. |
| **CA-ON** | `on_opstc` | Ontario Production Services Tax Credit (*Ontario Taxation Act, 2007*, S.O. 2007, c. 11, Sched. A, § 43.4) | [Ontario Creates OPSTC Guidelines (May 2025) § 1.01, § 1.05(E)](https://www.ontariocreates.ca/tax-incentives/opstc/opstc-guidelines) | **21.5% all-spend service credit**. Lawful stack with CPTC or federal PSTC. Reduces CPTC net cost for 60% cap. | `program_rate_rules_worldwide.py:540`; `stacking_rules.py` L161. |
| **US-CA** | `ca_film_30` | California Film & Television Tax Credit 4.0 (*Cal. Rev. & Tax. Code* § 17053.98(b)(3)(A)) | [CFC Program 4.0 Guidelines (Jan 1, 2026) § II.A.1](https://film.ca.gov) | **35% non-ATL credit**. Gateway: $\ge 75\%$ total budget in CA **OR** $\ge 75\%$ principal photography days in CA; \$1M min budget. | `program_rate_rules.py:102`; principal photography partitions conditionally modeled. |
| **US-NY** | `us_ny_post_production_credit` | Empire State Film Post-Production Credit (*NY Tax Law* § 31) | [NY Dept of Taxation & Finance (NY Tax Law § 31)](https://www.tax.ny.gov) | **30% post/VFX credit**. Gateway: lesser of \$1M or 75% worldwide post; or lesser of \$500k or 10% worldwide VFX. | `program_requirements.py:337` hardcodes \$1M min spend, omitting percentage alternatives (`NA-HYB-DEF-06`). |
| **AU-QLD** | `au_qld_pdv_rebate` | Screen Queensland Post, Digital & VFX Incentive | [Screen Queensland PDV Guidelines (eff. 4/9/2026)](https://screenqueensland.com.au/investment-support/incentives/post-digital-vfx/) | **10% capped rebate** (reduced from 15% effective Sept 4, 2026). Min AUD 250,000 QLD PDV QAPE. Discretionary ceiling. | `program_rate_rules_worldwide.py:7559-7583`; engine models 10% correctly. |
| **AU-FED** | `au_producer_offset` | Australian Producer Offset (*Income Tax Assessment Act 1997 (Cth)* Div 376) | [Screen Australia Producer Offset Guidelines](https://screenaustralia.gov.au/funding-and-support/producer-offset) | **40% feature / 30% TV on QAPE**. Min AUD 500k feature; Significant Australian Content (SAC) or Official Treaty Co-production required. No 80% cap. | `program_rate_rules.py:1395` (orphan RateRule slug; unlinked from `jurisdiction_comparison`). |
| **AU-FED** | `au_pdv_offset` | Australian Federal PDV Offset (*ITAA 1997 (Cth)* Div 376-35) | [Ausfilm / Screen Australia PDV Offset](https://ausfilm.com.au) | **30% of QAPE on post, digital and visual effects**. Min AUD 500,000 PDV QAPE. Additive with State PDV incentives (NSW/QLD/SA). | `program_spend_rules.py:170`; engine misclassifies as `OPEN_DEFAULT_INCLUDE` (`ROW-DEF-002`). |
| **ES-FED** | `es_tax_credit_foreign` | Spain Foreign Production Incentive (*Ley 27/2014 del Impuesto sobre Sociedades* Art. 36.2) | [Boletín Oficial del Estado (BOE-A-2014-12328)](https://boe.es) | **30% first EUR 1M + 25% excess; EUR 20M cap**. Category 2: technical industries & production suppliers. Min EUR 1M eligible spend. | `program_spend_rules.py:782-795` omits sound, miscellaneous, and general administration (`ROW-DEF-001`). |

---

## 2. Rest-of-World Program Inventory Reconciliation

> [!IMPORTANT]
> **Distinction Between Internal Engine Inventory Reconciliation vs. Independent Official Coverage:**
> - **Internal Inventory Reconciliation (DELIVERED):** Confirms exact 1:1 mathematical conservation between the engine's internal structures (164 Canonical Program Identities in `canonical_program_identity.py`, 81 RateRules in `program_rate_rules_worldwide.py`, 347 Global Inventory entries in `global_inventory*.py`, and 13 Same-Jurisdiction Stack pairs).
> - **Independent Official Coverage (OPEN):** External reconciliation against primary legislation and film commission directories across all 190+ sovereign and sub-national jurisdictions is **NOT 100% complete**. Disclosing the engine catalogue structure does NOT prove external statutory completeness.

### 2.1 Universe Dimensions in Frozen Engine 1.122
- **Canonical Identities (`row_identities`):** **164 total entries** registered in `canonical_program_identity.py` / `canonical_program_consolidation.py`.
  - `CURRENT` Priceable Validated: **48**
  - `CURRENT` Authority Insufficient / Unpriceable: **60**
  - `CURRENT` Non-Guaranteed Selective: **22**
  - `CURRENT` Authority Unresolved / Non-Priceable: **22**
  - `CURRENT` Non-Economic / Informational: **6**
  - `CURRENT` Data Handoff Defect: **2** (`au_nsw_screen`, `ie_regional_uplift`)
  - `SUPERSEDED` / Inactive: **3** (`ae_dxb_dpip`, `iceland_post_production_visual_effects_and_animation_incentive`, `uy_xxi_incentive`)
  - `DUPLICATE`: **1** (`ccm_tourism_film_facilitation`)
- **Active Pricing RateRules (`row_rate_programs`):** **81 programs** with executable rate curves in `program_rate_rules_worldwide.py` / `program_rate_rules.py`.
- **Global Inventory Entries (`row_gi_entries`):** **347 entries** in `global_inventory*.py`.

### 2.2 Reconciliation of RateRules vs. Canonical Identities
**74 RateRules** map 1:1 to Current Canonical Identities.
**7 RateRules** represent orphan or specialized track slugs that differ from the primary identity slug:
1. `au_producer_offset` -> Canonical identity `proposed_australia_producer_offset_separate_statutory_program` (orphan in RateRules).
2. `au_pdv_offset` -> Specialized sub-track of `au_location_offset` family.
3. `gb_iftc_enhanced_avec` -> Specialized enhanced AVEC track for certified UK independent films under £15M.
4. `new_zealand_screen_production_grant_—_international_post_vfx` -> Specialized PDV track of `nz_spg_international`.
5. `pt_scri_pt_medium_budget` -> Medium-budget tier of `pt_scri_pt_cash_rebate`.
6. `uy_acau_cash_rebate` -> Specialized PUA rebate distinct from `uy_tax_credit_2026`.
7. `za_nfvf_rebate` -> Specialized cultural rebate distinct from `za_dtic_foreign_film`.

### 2.3 Explicit Dispositions for Omitted and Regional Programs
- **Spanish Foral & Island Regimes (Canary Islands 54%/45%, Basque Country, Navarra):** These regional foral regimes exist in Spanish territorial tax law (Canary REF Ley 19/1994, Concierto Económico País Vasco, Convenio Económico Navarra). They are **omitted from the executable 81-RateRule engine catalogue**. In our audit, they are marked as **`EXTERNAL_REGIONAL_REGIME_OMITTED_FROM_CATALOGUE`** and kept distinct from standard Art. 36.2 Spanish Foreign Production Tax Credit (`es_tax_credit_foreign`).
- **Discretionary / Selective ROW Funds:** Programs like `jp_vipo_location_incentive` (Japan VIPO), `kr_kofic_location_incentive` (Korea KOFIC), `no_film_incentive` (Norway), `lu_filmfund_tax_shelter_rebate` (Luxembourg), `sa_film_commission_rebate` (Saudi Arabia), and `tw_bamid_rebate` (Taiwan) are confirmed to have **\$0.00 guaranteed statutory floor** and are classified as `NON_DETERMINISTIC_SELECTIVE_OR_AUTHORITY_UNRESOLVED`.

---

## 3. Separation of Frozen 1.122 Engine Findings vs. Remediation Commit History

To preserve rigorous audit provenance, findings must be strictly attributed to their origin, and remediation claims must cite exact commits in the remediation checkout (`/Users/Suraj/cineglobe-claude-global-optimizer-remediation/frametax2`):

| Defect / Feature ID | Frozen Engine `canonical-1.122.0` (`59566fd1`) State | Verified Remediation Commit | Audit Adjudication & Scope Boundary |
|:---|:---|:---|:---|
| **`NA-CODEX-08`** (Ontario CPTC + OPSTC) | `stacking_rules.py` line 161 hardcodes `("ca_federal_cptc", "on_opstc")` as `mutually_exclusive`. `check_all_pairs` rejects the stack. | **Commit `3a8f7370`** (engine 1.125.0): rewrote OPSTC stacking rules, removed false exclusivity, and implemented assistance netting. | Confirmed as an **active engine defect in frozen 1.122**. Independent audit calculator correctly prices the pair under Ontario Creates Guidelines § 1.01. |
| **`NA-HYB-DEF-02` / `NA-HYB-DEF-07`** (Manitoba Federal Stacks & Gates) | Manitoba 30% Cost-of-Production credit blocked on zero-labour segments; missing federal PSTC stack pair in `_SLUG_PAIR_RULES`. | **Commit `29740f70`** (engine 1.127.0) & **Commit `c52e2cd7`** (engine 1.128.0): resolved Manitoba federal stacks, disclosed PSTC reduction as a conservative bound. | Confirmed as an **active engine defect in frozen 1.122**. Modeled as conservative planning bound in audit calculator. |
| **`NA-HYB-DEF-06`** (NY § 31 Post Gate) | `program_requirements.py` line 337 hardcodes `min_local_spend_usd = 1_000_000.0`. Omits statutory 75% post / 10% VFX percentage gateways. | **Commit `a9362921`** (engine 1.124.0): rewrote NY post credit per Tax Law § 31(a)(3) across all paths (kernel, allocated-structure path, generator, and cost-pool path), testing post and VFX against the lesser of dollar floor or worldwide cost share. | Prior claim that NY was unrepaired in the remediation checkout is **WITHDRAWN**. Confirmed repaired in remediation checkout `a9362921` (`1.124.0`); remains an **active engine defect in frozen baseline 1.122.0**. Standalone post/VFX slices meeting percentage thresholds are validly priced outside the 1.122 engine. |
| **`ROW-DEF-001`** (Spain Category 2 Base) | `program_spend_rules.py:782-795` omits `miscellaneous`, `production_sound`, and `general_administration`. | **UNREPAIRED IN REMEDIATION CHECKOUT** (no commit exists in remediation branch modifying `ES_RULES` in `program_spend_rules.py`). | Prior claim that Claude repaired Spain is **WITHDRAWN**. Stans as an active frozen 1.122 coverage observation; dollar impact is conditional on Spanish supplier spend split. |
| **`ROW-DEF-002`** (ROW PDV Spending Base) | `program_spend_rules.py:169-172` places all 5 ROW PDV programs in `OPEN_DEFAULT_INCLUDE`, pricing on full production. | **UNREPAIRED IN REMEDIATION CHECKOUT** (no commit exists in remediation branch moving ROW PDV programs to `POST_VFX_ONLY`). | Prior claim that Claude repaired PDV programs is **WITHDRAWN**. Remains an active frozen 1.122 engine classification defect (`ROW-DEF-002`). |
| **`ROW-DEF-004`** (ROW Same-Jurisdiction Stacks) | `canonical_stack_bridge.py` has zero rules for 13 ROW pairs, falsely rejecting lawful AU Federal+State stacks as `UNRESOLVED_NO_AUTHORITY`. | **UNREPAIRED IN REMEDIATION CHECKOUT** (no commit exists in remediation branch wiring ROW same-jurisdiction pairs). | Prior claim that Claude repaired ROW stacks is **WITHDRAWN**. Remains an active frozen 1.122 engine defect (`ROW-DEF-004`). |
| **Project Visibility Regression** | Freshness predicate in `canonical_evaluation.py` hides FVD, BH, and LU from Project Library and Company Globe. | **Commit `9d29ecb6`**: retained evaluation history controls stage, navigation, and actions; opening retained results never evaluates. | Engine served-layer repair; outside audit scope. |

---

## 4. Honest Disclosure of Genuinely Open Items

> [!CAUTION]
> **NO BLANKET "ALL RESOLVED" CLAIM IS MADE.**
> While all executable calculators and matrices have been resynchronized and audit findings attributed to exact commits, the following substantive legal and empirical items remain **GENUINELY OPEN**:

1. **Quebec & Manitoba Federal PSTC Netting Dispositions (OPEN — Modeled Under Planning Assumptions / Conservative Lower-Incentive Bounds):**
   - **Source-Established Rule:** *ITA* § 125.5(1)(b) requires deducting assistance reasonably considered to be in respect of Canadian labour expenditure.
   - **Retained Official Sources & URLs for Reverse Netting:**
     - *Quebec:* *Loi sur les impôts* art. 1029.8.36.0.0.4 ([LégisQuébec c. I-3](https://www.legisquebec.gouv.qc.ca/fr/document/lc/I-3#se:1029_8_36_0_0_4)), Revenu Québec Form **CO-1029.8.36.SP** (Section 3 Lignes 36–42), and SODEC Mesures fiscales. Deemed corporate tax installments (federal PSTC) do not grind the provincial base.
     - *Manitoba:* *The Income Tax Act* (Manitoba) C.C.S.M. c. I10 ss. 7.5(1), 7.6(6) ([Manitoba Laws c. I10](https://web2.gov.mb.ca/laws/statutes/ccsm/i010.php)) and Manitoba Film & Music (MFM) Film & Video Production Tax Credit Form TC-2 Guidelines (Revised June 2024 § 4.2). The s. 7.5(1) statutory exclusion ("other than a tax credit under this section") refers strictly to Manitoba's own credit, but MFM Guidelines § 4.2 confirm that federal PSTC does not grind Manitoba eligible expenditures.
   - **Separate Spend vs. Labour Bases & Contingency Planned Cost Formula:**
     - A reserve amount is not an election. Planned production cost follows $\text{planned\_cost\_usd} = \text{gross\_budget\_usd} - \text{contingency\_reserve\_usd} \times (1 - \text{inclusion\_fraction})$.
     - When `contingency_expected_utilization_pct` is unset (NOT_STATED), `planned_cost_usd = gross_budget_usd`, preserving the verified app baseline. A hypothetical 0% inclusion scenario yields $\text{planned\_cost\_usd} = \text{gross\_budget\_usd} - \text{contingency\_reserve\_usd}$.
     - Combined rates like "37%" or "41.2%" are withdrawn as mathematically invalid. All stacks are calculated as separate dollar streams:
       - **Quebec Stack Dollars:** QPSTC = $0.25 \times \text{open\_base\_usd}$; Federal PSTC = $0.16 \times \text{net\_labour}$.
       - **Manitoba Stack Dollars:** Manitoba = $0.30 \times \text{open\_base\_usd}$; Federal PSTC = $0.16 \times \text{net\_labour}$.
   - **Assumed Planning Scenario:** Proportional allocation to labour (net labour = 75% for QC; 70% for MB) is modeled strictly as an assumed planning scenario, not a proven upper bound.
   - **Conservative Lower-Incentive / Higher-NPC Bound:** Deducting the whole provincial credit dollars directly from Canadian labour constitutes a conservative lower-incentive / higher-NPC bound (Codex `c52e2cd7`).
   - **Engine Status:** `ca_federal_pstc + ca_qc_pstc` is unruled in `_SLUG_PAIR_RULES` and blocked by absence in `canonical_stack_bridge.py`. The exact statutory allocation rule remains **OPEN**.
2. **External Sovereign & Sub-National Statutory Inventories (OPEN):**
   - Exact mathematical 1:1 conservation between the engine's internal structures (164 Canonical Identities, 81 RateRules, 347 GI entries, 13 ROW pairs) is fully delivered.
   - However, independent statutory verification against complete external legislative compendia for all 190+ sovereign and sub-national jurisdictions worldwide remains **OPEN**.
3. **Foreign Country Specific Sub-Caps (OPEN / UNVERIFIED):**
   - Primary statutory texts for Cyprus 30% ATL cap, Morocco 90% QPE cap, Greece Annex B.3 category share caps, Hungary 50% payroll cap, and Italy 30% EU ATL cap remain unretrieved independently and are tracked as unverified hypotheses.
4. **Claim-Level Production Evidence (OPEN Claim Follow-Ups):**
   - T4 employee payroll ledgers, provincial residency certifications, CAVCO Part A/B and T1177 accreditation certificates, and individual actor/director deal memos remain claim-level follow-ups.
