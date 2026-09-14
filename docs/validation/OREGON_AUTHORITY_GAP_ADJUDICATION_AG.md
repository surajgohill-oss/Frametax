# OREGON AUTHORITY GAP ADJUDICATION

## WORKSTREAM
OREGON_EXACT_AUTHORITY_GAP_ADJUDICATION_AG

## CONTROLLING CONTRACT
- Codex audit commit: a8a1d43dfb1f6e5d69d8b4144023515357f42242
- Engineering review commit: e507f7f0677aeec427bafa437fee318ca22ec6cd
- Bounded target: `us_or_opif` (Oregon Production Investment Fund)

## OBJECTIVE
Resolve the exact authoritative-evidence gap keeping `us_or_opif` fail-closed (UNPRICEABLE_AUTHORITY_INSUFFICIENT), specifically the missing exact primary statutory evidence for rates, bases, minimum spend, caps, discretion, and stackability.

## BATCH EXECUTION

### 1. Identify
- **Canonical program identity:** `us_or_opif` (Oregon Production Investment Fund - OPIF).
- **Exact authority veto:** Missing primary statutory authority for rates, threshold, cap propositions, discretion, and stacking (which were previously sourced from secondary pages/invented effective dates).
- **Missing fields:** `rate_payroll`, `rate_local_spend`, `minimum_spend`, `compensation_cap`, `per_project_cap`, `award_discretion`, `stacking_treatment`, `regional_uplift`.

### 2. Independent Retrieval of Primary Authority
- **Statute:** Oregon Revised Statutes (ORS) Chapter 284.368
- **Administrative Rules:** Oregon Secretary of State Administrative Rules, Chapter 951, Division 2 (OAR 951-002-0010)
- **Program Guidelines:** Oregon Film Official Guidelines (for stacking verification).

### 3. Separation of Findings
- **What authoritative sources prove:** 
  - 20% rate on Oregon employee salaries/wages/benefits (ORS 284.368(1)(b)(A)).
  - 25% rate on other actual Oregon expenses (ORS 284.368(1)(b)(B)).
  - $1,000,000 minimum actual Oregon expenses (ORS 284.368(1)(d)).
  - Compensation cap of $1,000,000 per individual/company (OAR 951-002-0010(1)).
  - Project cap of 50% of the entire OPIF annual fund (OAR 951-002-0010(5)).
  - 10% uplift if shooting outside Portland metropolitan zone (ORS 284.368(4)(b)).
  - Stackable with Greenlight Oregon Labor Rebate for an effective labor rate of 26.2%.
- **What remains conditional:**
  - The award itself is strictly conditional upon fund availability and a discretionary approval matrix by OFVO and OBDD. An award is *not* a guaranteed statutory entitlement just by hitting the formula (OAR 951-002-0010(3) and (4)).
- **What remains unsupported:** Nothing. All exact propositions now map to a specific primary ORS or OAR section.
- **Is the existing fail-closed disposition justified?** Yes, until Codex verifies this primary evidence. Even after verification, the program must be priced as a `CONDITIONAL` component rather than an unconditional entitlement due to the fund exhaustion rules and discretionary OFVO approval.

### 4. Proposed Correction
Update `us_or_opif` authority coverage from `UNPRICEABLE_AUTHORITY_INSUFFICIENT` to `PRICEABLE` but with an explicit `CONDITIONAL` flag mapped to the availability of funds/discretionary contract execution. Add the verified statutory rates (20%/25%), $1M individual compensation cap, 50% fund project cap, and $1M minimum spend base to `authority_coverage_registry.py` and `program_rate_rules.py`. *Do not apply this correction; wait for Codex.*

## COMPLETION STANDARD
EVIDENCE_COMPLETE_READY_FOR_CODEX_REVIEW
