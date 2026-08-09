# CINEGLOBE: FINAL UNRESOLVED RULE RESOLUTION

This document provides final authoritative resolutions for the remaining high-value jurisdiction-rule questions identified in `docs/validation/UNRESOLVED_JURISDICTION_RULES.md`.

---

## 1. MAURITIUS
**Rule/question:** Is the 40% tier additionally conditioned on 90% local filming? What is the current authoritative relationship between 30% / 35% / 40%? Is the production-specific 35% assumption merely a project assumption or supported by official program authority?
**Authoritative answer:** The statutory tiers are strictly **30%** and **40%**. There is no official 35% statutory rate; any 35% figure is a project-specific blended assumption. The 40% tier is explicitly conditioned on minimum spend thresholds (USD 1,000,000 for feature films) AND a requirement that at least 90% of the production's filming schedule takes place in Mauritius. Projects failing these criteria fall back to the 30% base rate.
**Exact source:** Economic Development Board (EDB) Mauritius Film Rebate Scheme Guidelines.
**Effective date/version if known:** Current (post-July 2023 updates).
**Status:** RESOLVED
**Required CineGlobe rule implication:** Remove the 35% statutory rate. Hard-code the 40% uplift to a 90% local-filming condition and USD 1M QPE threshold.
**Project-specific vs canonical rule:** Canonical rule.

---

## 2. GREECE
**Rule/question:** Does the current cash rebate impose an 80%-of-total-production-budget eligible-spend cap? If yes, quote the exact current official rule and identify the base to which 80% applies. Confirm current minimum spend / total budget thresholds.
**Authoritative answer:** Yes. The eligible production costs in Greece **cannot exceed 80% of the total production budget**. The base is the *global* total production budget of the project. Current minimum eligible spend for feature films (fiction) is €200,000.
**Exact source:** Creative Greece (formerly EKOME) Cash Rebate Guidelines (Law 4487/2017 and subsequent amendments).
**Effective date/version if known:** Current.
**Status:** RESOLVED
**Required CineGlobe rule implication:** Enforce an 80% cap on eligible Greek spend relative to the total global budget. Update feature minimum spend to €200,000.
**Project-specific vs canonical rule:** Canonical rule.

---

## 3. UNITED KINGDOM
**Rule/question:** Confirm whether IFTC exists as a distinct current program/treatment from standard AVEC. Confirm current IFTC rate, eligibility, budget threshold, cultural/co-production requirements. Confirm standard AVEC / VFX rates and 80% core-expenditure cap.
**Authoritative answer:** IFTC (Independent Film Tax Credit) is a distinct enhanced tier of AVEC. 
- **IFTC Rate:** 53% on qualifying expenditure (effective ~39.75% after tax).
- **IFTC Eligibility/Threshold:** Total core expenditure must be £23.5M or less. Claims are capped at a maximum of £15M core expenditure. Must meet a "Modified Creative Connection" (UK writer, director, or official co-production) plus the standard BFI cultural test.
- **Standard AVEC:** 34% (39% for VFX/animation).
- **AVEC/IFTC 80% Cap:** Eligible qualifying costs are strictly capped at 80% of the *total* core expenditure.
**Exact source:** HMRC Creative Industries Expenditure Credit Manual / BFI Guidelines.
**Effective date/version if known:** Applicable to principal photography starting on or after 1 April 2024.
**Status:** RESOLVED
**Required CineGlobe rule implication:** Implement bifurcated AVEC vs IFTC logic. Apply the 80% cap on eligible core expenditure and £23.5M threshold for IFTC.
**Project-specific vs canonical rule:** Canonical rule.

---

## 4. MALTA
**Rule/question:** Determine whether any official source provides objective criteria/points for the uplift from 30% to 40%. If the uplift remains Commissioner-discretionary, say so clearly.
**Authoritative answer:** The uplift is structured on objective criteria, not purely arbitrary discretion, though final certification remains subject to Commissioner approval. The base is 30%. A 35% uplift requires portraying Malta as Malta OR utilizing specific local infrastructure (e.g., Malta Film Studios water tanks). The 40% maximum requires maximizing the use of local resources and meeting specific qualifying local crew levels and department targets.
**Exact source:** Malta Film Commission (MFC) Financial Incentive Guidelines.
**Effective date/version if known:** Current.
**Status:** RESOLVED
**Required CineGlobe rule implication:** The 40% rate cannot be assumed automatically; requires gating logic tied to specific local crew/infrastructure targets.
**Project-specific vs canonical rule:** Canonical rule.

---

## 5. TERRITORIALITY
**Rule/question:** For MU / MT / GR / GB / AU, identify the authoritative test for local/qualifying expenditure: payer/SPV? vendor? place service performed? goods used/consumed? residency? Do not assume local-SPV payment alone qualifies foreign spend.
**Authoritative answer:** Payment through a local SPV is **insufficient** on its own in all five jurisdictions.
- **AU (Location Offset):** Goods or services must be *provided in Australia*, or land *located in Australia* must be used.
- **GB (AVEC):** Goods or services must be *used or consumed in the UK*.
- **GR (Creative Greece):** Costs must be incurred in Greece and billed by Greek tax residents (companies or individuals) or foreign companies with a Greek permanent establishment for services *performed in Greece*.
- **MT (Malta Film Commission):** Services and goods must be *provided in Malta*.
- **MU (EDB Mauritius):** Costs must be incurred in Mauritius (e.g., local transport, accommodation, and services physically rendered on the island).
**Exact source:** Statutory guidelines for all respective programs (HMRC, EDB, MFC, EKOME, Australian Arts Dept).
**Effective date/version if known:** Current.
**Status:** RESOLVED
**Required CineGlobe rule implication:** Ensure non-local spend paid through an SPV is rigorously excluded from QPE in these jurisdictions unless a specific treaty co-production rule bypasses it.
**Project-specific vs canonical rule:** Canonical rule.
