# CINEGLOBE STRUCTURING INTELLIGENCE IMPLEMENTATION HANDOFF
**ENGINE:** GEMINI

## CONSOLIDATED ENGINEERING REQUIREMENTS

### 1. REUSE EXISTING
* **Canonical Economic Calculators:** Do not build new calculators for the structures discovered. The existing calculators for Service and Copro rebates perfectly handle the math once the structure is qualified.
* **Stacking Engine:** Reuse the existing logic for stacking federal and regional incentives.

### 2. EXTEND EXISTING
* **Treaty Matching Engine:** Extend to iterate through N=3 combinations (Multilateral) when N=2 (Bilateral) fails the minimum contribution threshold.
* **Cultural Qualification Engine:** Extend to actively calculate the "Non-Party Personnel Exception" (e.g., 20% of budget) and highlight unused headroom for US talent.

### 3. CONNECT EXISTING
* **Component Allocation -> PDV Rebates:** Connect the component allocator to actively evaluate decoupling Post/VFX into jurisdictions with standalone PDV rebates whenever the primary shoot location lacks a competitive VFX incentive.

### 4. DATA / KNOWLEDGE ADDITION
* **Structuring Pattern Database:** Ingest the `GEMINI_STRUCTURING_PATTERN_LIBRARY.json` as a new persistent data layer that acts as a "playbook" for the optimizer.
* **Financial-Only Copro Flags:** Update canonical treaty data to flag which treaties allow 0% physical/creative contribution (financial-only).

### 5. GENUINELY NEW CAPABILITY
* **Opportunity Generator / Structuring Recommender:** A new heuristic engine that sits *before* the economic calculators. It looks at near-misses (e.g., 18% contribution vs 20% required) and recommends specific, lawful cures (e.g., "Shift $500k of BTL to Country B" or "Add Country C for Multilateral status").
* **Risk-Adjusted Feasibility Score:** A new lightweight tagging system for structures (e.g., identifying that a 3-way copro introduces high administrative and cashflow complexity).

### 6. DO NOT BUILD
* Do NOT build a new "Creative Scoring Engine" to guess discretionary competent authority approvals.
* Do NOT build complex tax-avoidance logic for deferred fees (assume deferrals are non-qualifying unless strictly proven as unconditional debt).
