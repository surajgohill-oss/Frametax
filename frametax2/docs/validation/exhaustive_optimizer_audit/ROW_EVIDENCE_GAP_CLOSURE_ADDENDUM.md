# Evidence-Gap Closure Addendum (NA + ROW) — FINAL AUDIT ADJUDICATION

Engine baseline frozen: `canonical-1.122.0` (`59566fd1`). No canonical code changed.
This addendum incorporates Codex's `CODEX_NA_PACKAGE_ADJUDICATION_20261011.md` and supersedes conflicting statements in prior audit documents.

---

## 1. Obligation-by-Obligation Status Matrix

| Obligation ID | Area | Prior Finding / Claim | Verified Evidence & Pinpoint Authority | Audit Status | Final Adjudication & Disposition |
|:---|:---|:---|:---|:---:|:---|
| **OBL-NA-01** | NA / California Gate | Rejected CA whenever local spend share <75% (`ca_film_30`). | [CFC Program 4.0 Guidelines (Jan 1, 2026) § II.A.1](https://film.ca.gov) & Cal. Rev. & Tax. Code § 17053.98(b)(3)(A): requires >=75% spend OR >=75% principal photography days. | **COMPLETE** | **ORACLE CORRECTED:** Principal photography partitions cannot be rejected by dollar share alone (<75%) because topsheet lacks day facts. Non-principal post/VFX/music slices with 0% CA photography remain rejected; principal partitions are conditionally modeled subject to claim follow-up. |
| **OBL-NA-02** | NA / Alberta Minimum | Rejected $200k local slice by comparing slice to CAD 499,999 (~$365k USD). | [Alberta FTTC Act, S.A. 2019, c. F-13.5, s. 4](https://www.alberta.ca/film-television-tax-credit): minimum spend is CAD 499,999 of TOTAL production costs, not local slice. | **COMPLETE** | **ORACLE CORRECTED:** Slice denominator corrected to project gross cost (`gross_usd >= $353k`). All 4 anchor projects satisfy total cost; photography in Alberta is kept as a separate claim follow-up. |
| **OBL-NA-03** | NA / BC Temporal Rate | Branched basic PSTC rate by project title (LU 36.28%, LLS 36%, FVD 28%). | [CRA BC Production Services Tax Credit](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/corporations/provincial-territorial-corporation-tax/british-columbia-provincial-corporation-tax/british-columbia-production-services-tax-credit.html) & BC Income Tax Act s. 81.2. | **COMPLETE** | **ORACLE CORRECTED:** Common prospective planning regime applies uniform 28% basic PSTC rate. Project title rate branching withdrawn; regional/distant uplifts kept separate. |
| **OBL-NA-04** | NA / NY Post Gateway | Claimed 100% post/VFX qualifies at 30% based solely on program_requirements $1M defect. | [NY Tax Law § 31(a)(2)–(3)](https://www.tax.ny.gov) & 5 NYCRR Part 240: gateway is lesser of $1M or 75% worldwide post; VFX is lesser of $500k or 10% worldwide VFX. | **COMPLETE** | **ORACLE CORRECTED:** Dual statutory lesser-of percentage gateways evaluated explicitly. Defect confirmed: `program_requirements.py` L337 hardcodes `min_local_spend_usd = 1_000_000.0`, omitting percentage gateways. |
| **OBL-NA-05** | NA / Ontario Stacking | Asserted `ca_federal_cptc + on_opstc` is mutually exclusive. | [Ontario Creates OPSTC Guidelines (May 2025) § 1.01](https://www.ontariocreates.ca/tax-incentives/opstc/opstc-guidelines): "The OPSTC may be claimed alone, or in addition to a federal Film or Video Production Services Tax Credit (or a Canadian Film or Video Production Tax Credit)." | **COMPLETE** | **ORACLE CORRECTED (NA-CODEX-08):** CPTC + OPSTC is LAWFUL. Provincial OPSTC (21.5%) reduces net production cost for CPTC 60% cap under ITA § 125.4(1). Prior AG mutual exclusion claim withdrawn; engine defect `NA-CODEX-08` logged. |
| **OBL-NA-06** | NA / Federal PSTC Stacks | Claimed all 4 provincial PSTC pairs (ON, BC, QC, MB) are established code defects. | [Ontario Creates § 1.01, § 1.05(E)](https://www.ontariocreates.ca); BC/QC/MB require separate individual statutory netting authority. | **COMPLETE** | **DISPOSITION REFINED:** Ontario PSTC stack (`ca_federal_pstc + on_opstc`) is independently supported; BC, QC, and MB pairs remain **OPEN** pending individual statutory netting dispositions. 3-way OCASE stacks unproven. |
| **OBL-NA-07** | NA / Component Gates | Asserted 12 US state + 4 Canadian province component gate omissions wholesale. | [Codex Structural Probes (20261011)](https://revisor.mn.gov/statutes/cite/116U.27): MN $50k below $1M local; PA $50k 10% vs 60%; MA $50k non-payroll; AL $70k 35% payroll applied to non-payroll. | **COMPLETE** | **DISPOSITION REFINED:** The 4 structural counterexamples confirmed; remaining 12-state / 4-province list unproven individually and retained as **OPEN** pending whole-structure tracing. |
| **OBL-NA-08** | NA / Universe Coverage | 45-program universe derived from snapshot keys; 15 hardcoded treaty specs; 696k combination count. | Engine snapshot keys vs official state/provincial directories. | **OPEN** | **DISPOSITION:** Reconciled internally against snapshot legs; external statutory universe reconciliation against all North American sub-jurisdictions remains **OPEN** (not 100% verified). |
| **OBL-ROW-01** | AU / Queensland PDV Rate | Claimed Screen Queensland PDV rate is 15% (stale at 10% in engine). | [Screen Queensland PDV Guidelines (effective 4/9/2026)](https://screenqueensland.com.au/investment-support/incentives/post-digital-vfx/): maximum incentive rate reduced from 15% to 10% cap; min AUD 250,000. | **COMPLETE** | **CLAIM WITHDRAWN — ENGINE CONFIRMED:** 10% cap applies prospectively. Affected single PDV rows (`FVD` $16,664.60, `LLS` $73,676.20) and stack rows (`au_pdv_offset + au_qld_pdv_rebate` at 40% combined = $294,704.80) recalculated and synchronized. |
| **OBL-ROW-02** | AU / Producer Offset Cap | Asserted Australia Producer Offset has an 80% QAPE cap / 20% ATL cap (`ROW-DEF-006`). | [Screen Australia Producer Offset Guidelines](https://screenaustralia.gov.au/funding-and-support/producer-offset): 40% feature / 30% TV; min AUD 500k; SAC test / co-pro. No 80% cap. | **COMPLETE** | **CLAIM WITHDRAWN:** 80% QAPE cap and 20% ATL cap removed from calculator and register. Qualitative defect stands: orphan `RateRule` slug not wired to canonical comparison and missing SAC gate. |
| **OBL-ROW-03** | ROW / Universal 80% Caps | Asserted engine enforces 80% territorial caps across DE, FR, GR, HU, IE, IT, UK, etc. | Engine `QPE_CAP_RULES` contains only `uk_avec`, `gr_cash_rebate`, `ca_federal_cptc`, `cz_film_incentive(_animation)`. | **COMPLETE** | **CLAIM WITHDRAWN:** Universal 80% caps withdrawn. Engine snapshot confirms programs run uncapped. Primary authority for foreign territorial caps remains **OPEN**. |
| **OBL-ROW-04** | Spain / Category 2 Spend | Identified Category 2 BTL from department labels (`miscellaneous`, `sound`, `general_admin`). | [Ley 27/2014 Art. 36.2 LIS (BOE-A-2014-12328)](https://boe.es): eligibility based on Spanish supplier/technical spend, not department labels. | **COMPLETE** | **DOWNGRADED TO CONDITIONAL:** Department totals bundle mixed expenses; FVD Category 2 eligibility ($1,724,759) is conditional on supplier residency/location split. Registered as coverage observation pending invoice facts. |
| **OBL-ROW-05** | ROW / PDV Category Spend | Derived PDV eligibility from topsheet department labels across all 5 programs. | [ITAA 1997 Div 376](https://ausfilm.com.au) & SAFC/Screen Queensland/NZSPR guidelines: activity-based and location-based. | **COMPLETE** | **DOWNGRADED TO CONDITIONAL:** Music, titles, deliverables and post fringes inclusion are bounds, not proven expectations. Qualitative defect (all-production spend base applied to PDV programs) stands. |
| **OBL-ROW-06** | ROW / Unverified Foreign Rules | Asserted Cyprus 30% ATL cap, Morocco 90% cap, Greece Annex B.3, Hungary 50% payroll, Italy 30% EU ATL. | Retained engine citation text only; primary statutory texts not retrieved independently. | **OPEN** | **DISPOSITION: OPEN / UNVERIFIED:** Kept as hypotheses pending primary statutory retrieval. Not claimed as verified. |
| **OBL-ROW-07** | ROW / Program Inventory | 81 RateRules and 90 canonical identities derived from engine files. | Engine registries vs independent international film commission directories. | **OPEN** | **DISPOSITION: OPEN / UNVERIFIED:** Internal reconciliation between RateRules and canonical identities completed; independent official program inventory reconciliation remains **OPEN**. |

---

## 2. Quantitative Resynchronization Summary

Following the corrections above, all affected calculators, matrices, and discrepancy registers have been fully resynchronized:

1. **North American Audit (`independent_na_hybrid_audit.py`):**
   - Rerun time: **5.47s** (well within the 12-minute foreground watchdog limit).
   - Reconciled **2,742 manifest rows** (`NORTH_AMERICAN_COVERAGE_MANIFEST.csv`) representing all **696,213 expected combinations**.
   - Generated **1,601 matrix rows** (`NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv`).
   - CPTC + OPSTC stack (`CA-ON`) evaluated as lawful with assistance netting (`NA-CODEX-08`).
   - BC PSTC basic rate evaluated at 28% without project-title contamination.
   - California gate models principal photography conditionally and rejects only non-principal slices.
   - Alberta minimum spend evaluated against project total cost (`gross_usd`).

2. **ROW Single-Jurisdiction Audit (`independent_row_single_jurisdiction_audit.py`):**
   - Rerun time: **0.96s**.
   - Reconciled **376 matrix rows** (`ROW_SINGLE_JURISDICTION_COVERAGE_MATRIX.csv`) and **772 manifest rows** (`ROW_SINGLE_JURISDICTION_COVERAGE_MANIFEST.csv`).
   - Queensland PDV evaluated at **10% cap** across all four anchors (`FVD` $16,664.60, `LLS` $73,676.20).
   - Queensland stack evaluated at **40% combined cap** (`$294,704.80` on `LLS`).
   - Australia Producer Offset evaluated without the unsupported 80% cap.
   - All 5 PDV programs evaluated on strict PDV spend bounds (`ROW-DEF-002`).

---

## 3. Honest Disclosure of Genuinely Open Items

In strict accordance with project rules, **100% verification is NOT claimed**. The following items remain explicitly **OPEN**:
1. **Federal PSTC Provincial Pair Rules:** Beyond Ontario OPSTC (§1.01), statutory assistance netting rules for BC PSTC, Quebec QPSTC, and Manitoba remain unretrieved and unproven.
2. **Comprehensive NA / ROW External Inventories:** Independent inventories outside engine snapshot keys remain open.
3. **Foreign Country Specific Sub-Caps:** Primary statutory texts for Cyprus 30% ATL, Morocco 90% QPE, Greece Annex B.3, Hungary 50% payroll, and Italy 30% EU ATL remain unretrieved independently.
4. **Producer Incurred Facts:** Talent deal memos, Canadian T4 residency ledgers, CAVCO certificates, and contingency allocation schedules remain claim-level follow-ups.
