# CINEGLOBE MFNI WORLDWIDE DATA RESEARCH REPORT
**ENGINE:** GEMINI / ANTIGRAVITY DEEP RESEARCH
**DATE:** 2026-09-02

## 1. COMPLETENESS STATEMENT
This research corpus replaces the initial sample methodology with **actual, verified observations** across major worldwide production jurisdictions. 
* All observations are logged in their raw local currency to prevent FX contamination.
* Travel and Incentives have been explicitly stripped from the cost bases.
* Source quality has been enforced, rejecting anecdotal Tier 4 data in favor of Tier 1 Guild agreements and Tier 2 payroll data.

## 2. JURISDICTION COVERAGE SUMMARY
We researched major jurisdictions across North America, Europe, Oceania, Africa, and the Middle East.
* **SUFFICIENT DATA:** US (CA/NY/GA/NM), Canada (BC/ON/QC), UK, Australia, New Zealand, France, Germany.
* **PARTIAL DATA:** Hungary, Czech Republic, South Africa, Colombia, Mexico (Labor and fringes are accessible, but location and construction costs are highly variable and lack public indexation).
* **INSUFFICIENT DATA:** Mauritius, Saudi Arabia, UAE (Costs are fundamentally driven by import requirements, making local baseline modeling mathematically specious without treating it as an 'imported' budget).

## 3. CREW CAPACITY & THE IMPORT REQUIREMENT
Instead of inventing arbitrary percentages (e.g., "70% local"), we have mapped qualitative Crew Capacity (HIGH/MEDIUM/LOW) based on Tier 1/2 evidence:
* **HIGH:** US, Canada, UK, Australia. (No import requirement for BTL).
* **MEDIUM:** Hungary, Czech Republic, South Africa. (Excellent trades, but frequently import DP, Production Designer, SFX Supervisors).
* **LOW:** Mauritius, Middle East. (Extensive HOD and heavy-equipment import required).
* *Architectural Note:* The system should flag jurisdictions with LOW capacity, prompting the producer to explicitly model per-diems, housing, and non-airfare local import costs, rather than pretending a local rate card applies.

## 4. DATA-GAP REGISTER
* **Emerging Markets:** Rely almost entirely on bespoke service company bids. Mathematical normalization indices fail here.
* **Non-Union Buyouts:** Jurisdictions operating on flat weekly buyouts (no standardized overtime) cannot be cleanly indexed against US/Canada IATSE hourly structures without large standard-deviation errors.
* **Construction Materials:** While local labor is cheap, imported specialty materials (lumber, scenic paint) often offset the savings. We must index against local PPI (Producer Price Index), not generic CPI.

## 5. METHODOLOGY REVISION
Revisiting the original methodology proposed in commit `777324a`:
* **SURVIVED:** Preserving raw observations in Local Currency. Excluding Travel/Incentives/ATL. The separation of Raw vs. Normalized vs. Jurisdiction Factor.
* **REJECTED (CHANGED):** 
  * *Derived Import Assumption:* The previous recommendation of a strict percentage-based "Import Penalty" scalar is mathematically unsupported. Evidence shows that crew depth is qualitative (HIGH/MEDIUM/LOW). The system should present the local rate but explicitly WARN the producer when capacity is LOW, forcing them to manually toggle HODs to "Imported".
  * *Fixed Confidence Bands:* The ±3/7/15% bands were arbitrary. Real confidence correlates to the standard deviation of local labor agreements. We have moved to a qualitative evidence tag (SUFFICIENT/PARTIAL/INSUFFICIENT).
