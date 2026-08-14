# CINEGLOBE SCRIPT ANALYZER + BTL BUDGET ARCHITECTURE
**Phase:** Independent Production-Domain Design Review
**Reviewer:** Gemini 3 Pro

## 1. Critique of Three-Level Framework
The three-level model is highly appropriate for progressive production planning. **Major change to prior proposal:** Level 2 and Level 3 should NOT be separate engines. They must be progressive representations of a single unified budget data model. This prevents "budget discontinuity" when a producer moves from a Level 2 estimate to a Level 3 detailed adjustment.

## 2. Level Definitions
- **Level 1 (Rapid Global Estimate):** Provides instantaneous, structurally sound cost distributions for global jurisdiction comparisons. 
  - *Inputs:* Screenplay, Genre, Page Count, Broad Scale, Approx Location Mix.
  - *Outputs:* Department-level totals with explicit P10/P50/P90 uncertainty bands based on a global template * jurisdiction indices.
- **Level 2 (Production-Informed):** Actionable departmental budgets based on explicit script breakdowns.
  - *Inputs:* Structured Scene Breakdown, Confirmed Shoot Days, Stage/Location Split.
  - *Outputs:* Sub-department budgets (Script-derived quantities * localized average rates).
- **Level 3 (Detailed Line Budget):** Line-producer approximation.
  - *Inputs:* Detailed Schedule, Crew Counts, Union Assumptions, Fringes.
  - *Outputs:* Line-item budget (Quantity * Rate * Duration) with full override capability.

## 3. Script-Breakdown Scope
Separation of extraction concerns is critical:
- **Objective Script Fact:** Scenes, Page Eighths, Sluglines, INT/EXT, Day/Night, Locations, Speaking Roles.
- **AI-Interpreted Complexity:** Stunts, VFX Intensity, Crowds, Period/Wardrobe.
- **Producer Decision (NOT AI):** Stage vs Location, Schedule Compression, Cast Identity.

## 4. Scheduling Model Recommendation
- **Deterministic:** Page Count + INT/EXT/D/N splits establish the baseline.
- **Probabilistic:** VFX, stunts, and animals reduce pages/day.
- **Producer Confirmation:** Company moves, split days, second units.

## 5. Local-Cost Data Recommendation
Cost data must be strictly categorized to prevent scaling errors:
- **Local Actual Rates:** Union minimums, payroll fringes, stage rentals.
- **Indexed Estimates:** Catering, fuel, construction materials.
- **Global Default * Multiplier:** Specialty camera packages.
- **Project Specific:** A-list cast, bond, insurance.

## 6. AI / Deterministic Split
- **AI Responsibilities:** Slugline parsing, character mapping, VFX/Stunt identification.
- **Strictly Deterministic:** Rate multiplication, schedule arithmetic, tax/fringe calculations, and cost data lookups. **AI MUST NEVER INVENT ECONOMIC RATE DATA.**

## 7. Biggest Production-Model Risks
1. **Local Multiplier Misapplication:** Applying a low-cost jurisdiction index to global fixed costs (like major cast or specialized VFX firms).
2. **Ignored Fringes:** Failing to account for massive variance in global employer tax burdens.
3. **Fake Precision:** Presenting a globally estimated L1 budget down to the dollar, disguising structural uncertainty.

## 8. Source-of-Truth Hierarchy
`ACTUAL USER BUDGET` > `USER-CONFIRMED ASSUMPTION` > `VALIDATED LOCAL RATE` > `SCRIPT EXTRACTION` > `MODEL ESTIMATE` > `GLOBAL DEFAULT`

## 9. Optimizer Handoff
The production engine hands the optimizer a clean payload:
- Jurisdiction-specific local spend
- Labor vs Non-Labor categories
- Known exclusions (e.g., US post-production)
- Territorial spend fractions

## 10. Little Utopia Future Acceptance
The existing Little Utopia project serves as the perfect fixture. Acceptance is proven by passing the LU script through the analyzer, generating an L3 budget, and comparing the structural ratios and local spend accuracy to the known $4.3M budget.

## Unresolved Architecture Questions
- How frequently should local union rate cards and payroll fringes be updated to ensure Level 3 validity without overwhelming data maintenance?
- What is the UI/UX for a producer to confirm an AI-interpreted "Stage vs Location" split without clicking through 150 scenes?
