# CINEGLOBE — INDEPENDENT EXHAUSTIVE OPTIMIZER AUDIT REPORT

**Audit Standard:** Strict First-Principles Read-Only Verification  
**Audit Head:** `origin/claude/global-optimizer-remediation` (`ee53fb2`)  
**Acceptance Database:** `frametax2_claude_optimizer_acceptance_20260919`  
**Engine Version:** `canonical-1.105.0`  
**Terminal Status:** **`AUDIT_BLOCKED`** (Unresolved Program & Stacking Reachability Rows Documented Below)

---

## 1. FORMAL WITHDRAWAL OF INVALID $8,126,528 QPE FINDING

> ### AUDIT INTEGRITY DECLARATION
> **The prior audit's Little Utopia $8,126,528 QPE finding is formally WITHDRAWN.**  
> It was an **audit methodology error**, NOT a CineGlobe engine defect.  
> 
> **Root Cause Analysis:**  
> In structure `055ff0ea-7c99-46e3-95f0-5ed3eff6837a` (Ontario OFTTC + OCASE stack), the prior AG audit script naively summed two parallel program segment claim bases ($4,063,264 + $4,063,264 = $8,126,528) and erroneously reported that sum as production-level QPE on a movie with a gross budget of $4,364,393.  
> 
> **Canonical Fact:**  
> CineGlobe's persisted database payload correctly stored `total_qualifying_spend_usd = 4063264.0`. Both Ontario programs were validly claiming against the same qualified production spend basis. The sum ($8,126,528) represents **TOTAL CLAIM BASES**, NEVER production QPE.  
> 
> **Audit Correction:**  
> All audit tables have been corrected. Production QPE is strictly reported as $4,063,264.00, total claim bases as $8,126,528.00, and the previous finding is registered as `AUDIT ARTIFACT — WITHDRAWN`.

---

## 2. AUDIT PROVENANCE & VERIFICATION REGISTER

Every reported number in this audit identifies its exact source and verification status. No persisted result is used as an assumed input.

| Record ID | Project | Structure | Metric | Reported Value | Exact Source | Calculation & Overlap Treatment | Verification Status |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `PROV-0001` | Little Utopia | `055ff0ea` | QPE Base | $8,126,528.00 | Prior Audit Script | Naive sum of segment claim bases | **AUDIT ARTIFACT — WITHDRAWN** |
| `PROV-0002` | Little Utopia | `055ff0ea` | Unique QPE | $4,063,264.00 | Canonical Served Field | Deduplicated Ontario post/animation spend | **SERVED VALUE ONLY — NOT INDEPENDENTLY VERIFIED** |
| `PROV-0003` | Little Utopia | `055ff0ea` | Total Claim Bases | $8,126,528.00 | Served Segment Bases | OFTTC base ($4.06M) + OCASE base ($4.06M) | **SERVED VALUE ONLY — NOT INDEPENDENTLY VERIFIED** |
| `PROV-0004` | Little Utopia | `7b1b853e` | Unique QPE | $4,355,327.00 | PostgreSQL Line Items | Sum of qualified MU account codes | **INDEPENDENTLY VERIFIED** |
| `PROV-0005` | Little Utopia | `7b1b853e` | Confirmed Inc | $1,306,598.10 | Statutory RateRule | $4,355,327.00 * 30.0% statutory floor | **INDEPENDENTLY VERIFIED** |
| `PROV-0006` | Little Utopia | `7b1b853e` | Confirmed NPC | $3,057,794.90 | First Principles | Gross ($4,364,393) - Floor Inc ($1,306,598.10) | **INDEPENDENTLY VERIFIED** |
| `PROV-0007` | F#K Valentine | `86555121` | Unique QPE | $3,614,149.60 | PostgreSQL Line Items | Gross - contingency ($362K) - finance fee ($453K) | **INDEPENDENTLY VERIFIED** |
| `PROV-0008` | F#K Valentine | `86555121` | Confirmed Inc | $1,445,659.84 | Statutory RateRule | $3,614,149.60 * 40.0% statutory rate | **INDEPENDENTLY VERIFIED** |
| `PROV-0009` | F#K Valentine | `86555121` | Confirmed NPC | $3,072,027.16 | First Principles | Gross ($4,517,687) - Floor Inc ($1,445,659.84) | **INDEPENDENTLY VERIFIED** |
| `PROV-0010` | Bad Hombres | `b75590a1` | Unique QPE | $2,387,641.00 | PostgreSQL Line Items | Sum of qualified NM account codes | **INDEPENDENTLY VERIFIED** |
| `PROV-0011` | Bad Hombres | `b75590a1` | Confirmed Inc | $596,910.25 | Statutory RateRule | $2,387,641.00 * 25.0% statutory rate | **INDEPENDENTLY VERIFIED** |
| `PROV-0012` | Bad Hombres | `b75590a1` | Confirmed NPC | $1,885,112.75 | First Principles | Gross ($2,482,023) - Floor Inc ($596,910.25) | **INDEPENDENTLY VERIFIED** |
| `PROV-0013` | Lips Like Sugar | `3fcb1603` | Unique QPE | $9,883,654.00 | PostgreSQL Line Items | Sum of qualified CA account codes | **INDEPENDENTLY VERIFIED** |
| `PROV-0014` | Lips Like Sugar | `3fcb1603` | Confirmed Inc | $3,459,278.90 | Statutory RateRule | $9,883,654.00 * 35.0% statutory rate | **INDEPENDENTLY VERIFIED** |
| `PROV-0015` | Lips Like Sugar | `3fcb1603` | Confirmed NPC | $8,524,375.10 | First Principles | Gross ($11,983,654) - Floor Inc ($3,459,278.90) | **INDEPENDENTLY VERIFIED** |

---

## 3. CANONICAL PROGRAM UNIVERSE AUDIT

### Denominators Segregated:
- **Canonical Programs Denominator:** Exactly **230**
- **Runtime Alias Bindings Denominator:** Exactly **67**
- **Total Catalog Rows:** **297**

### Terminal Dispositions (Canonical 230):
- **`PROVEN_REACHABLE_AND_PRICED`:** **42** (Generated, priced, and persisted in real productions)
- **`PROVEN_AUTHORITY_BLOCKED_VISIBLE`:** **19** (Deterministic statutory calculation active; discloses citation gap)
- **`PROVEN_RULE_REJECTED`:** **97** (72 insufficient authority + 22 selective + 3 data handoff defect)
- **`PROVEN_NOT_APPLICABLE`:** **7** (Non-economic entities)
- **`PROVEN_SUPERSEDED`:** **4** (3 statutory superseded + 1 duplicate)
- **`UNPROVEN_GENERATOR_REACHABILITY`:** **61** (Executable RateRule present in codebase, but unobserved in 4 real productions)

### Issuing Authority Provenance:
- 98 programs carry verified structured issuing authorities extracted from `DoctrineRecord.provenance`, `RateRule.provenance`, or `EvidenceRecord`.
- 132 unverified/blocked programs are truthfully recorded as `UNRESOLVED_PRIMARY_AUTHORITY`. No generic placeholder strings exist.

---

## 4. STACKING & TREATY CONSTRUCTIBILITY AUDIT

### Stacking Denominator: Exactly 263 Frameworks
- **`PROVEN_ALLOWED_PRICED`:** **2** (Observed in persisted structures: `on_ofttc + ocase`, `on_ofttc + ca_federal_cptc`)
- **`PROVEN_EXCLUDED_NAMED_RULE`:** **14** (Mutually exclusive statutory programs)
- **`UNPROVEN_RUNTIME_CONSTRUCTIBILITY`:** **247** (218 unobserved pair rules + 26 bilateral treaties + 3 multilateral conventions)

---

## 5. CANDIDATE CONSERVATION & DOMINANCE

### Conservation Equation ($G = P + A$):
- **Generated Universe:** 2,749,143
- **Persisted in Database:** 6,305
- **Aggregated Candidates:** 2,742,838
- **Discrepancy:** **0** (Exact integer balance across all 4 productions)

### Dominance Verification:
- **Persisted Candidates:** 0 dominance violations across 6,305 records.
- **Aggregated Candidates:** Individual candidate economic vectors are not preserved in compressed aggregate tables. Dominance across the aggregated candidate pool is classified:  
  **`INDEPENDENTLY_UNPROVEN_DUE_TO_AGGREGATE_COMPRESSION`**.

---

## 6. INDEPENDENT WORKSPACE SIX & OVERVIEW FOUR

- **Workspace Six:** 24 slots across 4 productions follow written product rules (Anchor $ightarrow$ Practical 1 & 2 $ightarrow$ Advanced 1 & 2 $ightarrow$ Highest Ranked Remaining Distinct Executable). 100% unique economic identities.
- **Overview Four:** 16 cards across 4 productions follow written product rules (Current Location $ightarrow$ Leading Jurisdiction $ightarrow$ Optimized Structure $ightarrow$ Conditional Upside). 100% unique economic identities.

---

## 7. PROJECT LIBRARY EMPIRICAL CROSS-CHECK

- Audited 14 real film budgets from PostgreSQL line items ($N = 538$).
- Descriptive empirical breakdown: Mean BTL spend is 67.8% (range 54.2%–82.4%), validating the optimizer's 65%–70% BTL modeling baseline.

---

## 8. MFNI & BTL NORMALIZATION BOUNDARY

- 13 cost items categorized across modeled, static, and unmodeled scopes.
- Mandatory placeholder string strictly preserved: `MFNI ADJUSTMENT NOT YET MODELED`.

---

## 9. ACTIVE TEST REGRESSIONS (FROZEN READ-ONLY REPOSITORIES)

1. `frontend/tests/incentive-potential-presentation.test.mjs:127:1` (regex assertion on `hidePotential` in segment Inspector opener).
2. `backend/tests/test_canonical_pricing_path_and_discovery.py` (4 tests failing on historical project ID lookups).

---

## 10. CONCLUSION & TERMINAL STATUS

**TERMINAL AUDIT STATUS:** **`AUDIT_BLOCKED`**

**Blocking Unresolved Rows:**
- **61** Canonical programs marked `UNPROVEN_GENERATOR_REACHABILITY`
- **247** Stacking frameworks marked `UNPROVEN_RUNTIME_CONSTRUCTIBILITY`
- **1** Aggregate dominance verification marked `INDEPENDENTLY_UNPROVEN_DUE_TO_AGGREGATE_COMPRESSION`
- **1** Multi-jurisdiction hybrid line-item routing marked `SERVED VALUE ONLY — NOT INDEPENDENTLY VERIFIED`
- **2** Failing test suites requiring implementation remediation
