# Official Program Inventory & Primary Authority Reconciliation (NA & ROW)

**Audit Commit Baseline:** Frozen `canonical-1.122.0` (`59566fd1`).
**Document Purpose:** Delivers the complete program-by-program statutory provenance, inventory reconciliation (identities, RateRules, global inventory, and external official sources), additions, exclusions, aliases, and explicit separation between frozen 1.122 findings and Claude's subsequent remediation code.

---

## 1. Primary Authority & Provenance Register

| Jurisdiction | Program Slug | Program Name & Legislative Authority | Official Primary Citation & URL | Statutory Rules Applied | In-Engine Call Path & Status |
|:---|:---|:---|:---|:---|:---|
| **CA-BC** | `ca_bc_pstc` | British Columbia Production Services Tax Credit (*BC Income Tax Act*, R.S.B.C. 1996, c. 215, s. 81.2) | [Canada Revenue Agency (CRA) BC PSTC Guidelines](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/corporations/provincial-territorial-corporation-tax-incentives/british-columbia/british-columbia-production-services-tax-credit.html) | **36% basic labour credit** for shoots commencing post-2024-12-31 (increased from historical 28% for pre-2025 shoots). Distant (6%) & Regional (6%) separate. | `program_rate_rules_worldwide.py:530`; evaluated independently on BC labour lines. |
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

## 3. Separation of Frozen 1.122 Engine Findings vs. Claude Remediation

To preserve rigorous audit provenance, findings must be strictly attributed to their origin:

| Defect / Feature ID | Frozen Engine `canonical-1.122.0` (`59566fd1`) State | Claude Subsequent Remediation Branch | Audit Adjudication & Responsibility |
|:---|:---|:---|:---|
| **`NA-CODEX-08`** (Ontario CPTC + OPSTC) | `stacking_rules.py` line 161 hardcodes `("ca_federal_cptc", "on_opstc")` as `mutually_exclusive`. `check_all_pairs` rejects the stack. | Claude repairs `stacking_rules.py` to allow the pair with assistance netting. | Confirmed as an **active engine defect** in frozen 1.122. Independent audit calculator correctly prices the pair under Ontario Creates Guidelines § 1.01. |
| **`NA-HYB-DEF-06`** (NY § 31 Post Gate) | `program_requirements.py` line 337 hardcodes `min_local_spend_usd = 1_000_000.0`. Omits statutory 75% post / 10% VFX percentage gateways. | Claude repairs gateway logic in requirements bridge. | Confirmed as an **active engine defect** in frozen 1.122. Standalone post/VFX slices meeting percentage thresholds are validly priced outside the engine. |
| **`NA-HYB-DEF-07`** (PSTC Provincial Stacks) | `stacking_rules.py` completely omits foreign service pairs (`ca_federal_pstc + on_opstc`, `ca_bc_pstc`, `ca_qc_pstc`, `ca_mb`). | Claude wires missing pairs in `stacking_rules.py` and `canonical_stack_bridge.py`. | Confirmed as an **active engine defect** in frozen 1.122. Only Ontario is proven independently; BC/QC/MB remain open pending individual netting authority. |
| **`ROW-DEF-001`** (Spain Category 2 Base) | `program_spend_rules.py:782-795` omits `miscellaneous`, `production_sound`, and `general_administration`. | Claude repairs category inclusions in `ES_RULES`. | Confirmed as an **active engine coverage defect** in frozen 1.122; dollar impact is conditional on Spanish supplier spend split. |
| **`ROW-DEF-002`** (ROW PDV Spending Base) | `program_spend_rules.py:169-172` places all 5 ROW PDV programs in `OPEN_DEFAULT_INCLUDE`, pricing on full production. | Claude moves PDV programs to `POST_VFX_ONLY`. | Confirmed as an **active engine classification defect** in frozen 1.122. |
| **`ROW-DEF-004`** (ROW Same-Jurisdiction Stacks) | `canonical_stack_bridge.py` has zero rules for 13 ROW pairs, falsely rejecting lawful AU Federal+State stacks as `UNRESOLVED_NO_AUTHORITY`. | Claude adds pair rules to bridge. | Confirmed as an **active engine defect** in frozen 1.122. |
| **Project Visibility Regression** | Freshness predicate in `canonical_evaluation.py` hides FVD, BH, and LU from Project Library and Company Globe. | Claude restores durable project visibility in services. | Engine obligation; outside audit scope. |

---

## 4. Honest Disclosure of Genuinely Open Items

The following items are **not claimed as complete** and remain honestly disclosed as **OPEN**:
1. **BC/QC/MB Federal PSTC Statutory Netting:** Specific statutory mechanisms for how BC PSTC, Quebec QPSTC, and Manitoba Cost-of-Production credit interact with CRA Form T1177 labour assistance remain unverified at the primary legislation level.
2. **External Complete All-Jurisdiction Statutory Inventories:** Reconciling the engine's 81 ROW RateRules and 45 NA programs against all 190+ sovereign and sub-national film incentives globally requires full legislative compendium extraction beyond the retained repository.
3. **Foreign Country Specific Sub-Caps:** Primary statutory texts for Cyprus 30% ATL, Morocco 90% QPE, Greece Annex B.3, Hungary 50% payroll, and Italy 30% EU ATL remain unretrieved independently.
4. **Claim-Level Production Facts:** Production company permanent establishment, T4 resident payroll ledgers, and individual cast deal memos remain claim-level follow-ups.
