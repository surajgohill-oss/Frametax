# MFNI GLOBAL RESEARCH REPORT — AG DISCOVERY

## 1. REPOSITORY IDENTIFICATION
- **Absolute working path:** `/Users/Suraj/cineglobe-frametax`
- **Git remote:** `origin https://github.com/surajgohill-oss/Frametax.git`
- **Branch:** `claude/audit-frametax-features-NZcX5`
- **HEAD SHA:** `0f3898b19366d2b8f217b1daca8c3d7200a9294a`
- **Canonical Status:** Confirmed operating in canonical repository.

## 2. EXISTING MFNI ARCHITECTURE DISCOVERED
I inspected the application code, specifically `frametax2/backend/app/data/location_cost_benchmarks.py`.
The current MFNI architecture is a static dictionary of `JurisdictionCostProfile` dataclasses. It maps jurisdiction `iso2` codes to fixed numerical multipliers, cost indices (relative to LA = 1.0), and USD dollar amounts. There are regional fallbacks configured. It does NOT use a single macroeconomic multiplier, adhering to CineGlobe principles.

## 3. EXISTING MFNI TAXONOMY
The implemented taxonomy contains the following cost drivers:
- **Travel/Airfare:** `airfare_lax_business_usd`, `airfare_lax_economy_usd`, `airfare_jfk_delta_usd`
- **Accommodation:** `hotel_rate_usd`, `apartment_monthly_usd`
- **Per Diem:** `per_diem_atl_usd`, `per_diem_btl_usd`
- **Labor / Crew:** `crew_rate_index`
- **Equipment:** `equipment_rental_index`
- **Stages / Facilities:** `stage_facility_index`
- **Post Production / VFX:** `post_production_index`, `vfx_index`
- **Permits / Visas:** `work_permit_cost_usd`, `visa_cost_usd`
- **Local Transport:** `local_transport_daily_usd`
- **Logistics / Cargo:** `freight_carnet_pct`
- **Payroll / Fringes:** `payroll_fringe_pct`, `payroll_overhead_pct`
- **Professional Services:** `legal_accounting_index`
- **Local vs Imported Crew:** `local_hire_min_pct`
- **Unit / Catering:** `catering_daily_usd`
- **Risk Multipliers:** `fx_risk_pct`, `contingency_adj_pct`, `schedule_risk_multiplier`

*Delta Additions Required by Prompt:* Workday/OT rules, Statutory/Contractual Fringes breakdown, Stage rental pricing/capacity, Location/permit fees, Art/Construction materials.

## 4. EXISTING BENCHMARK INVENTORY & PROVENANCE
- **Current Coverage:** 44 National Jurisdictions.
- **Provenance / Sources:** The `data_sources` field exists in the dataclass but is **empty** for all 44 records.
- **Currentness:** There are no `effective_date` stamps. All 44 records are **DATE UNKNOWN** and **SOURCE MISSING**.
- **Confidence:** Assigned broadly as "HIGH", "MEDIUM", or "LOW" but lacking primary commercial or statutory verification (heuristics detected).

## 5. DETERMINISTIC GLOBAL JURISDICTION QUEUE
Total Universe: 124 canonical jurisdictions (114 base + 10 material subnationals).

**Status Legend:**
A — STRONG CURRENT COVERAGE
B — PARTIAL COVERAGE / MATERIAL GAPS
C — PROVISIONAL / WEAK-SOURCE COVERAGE
D — NO MEANINGFUL MFNI COVERAGE
E — RESEARCH BLOCKED / INCOMPLETE

*Top of Queue:*
1. **US (United States)** - Status C (Baseline, lacks authoritative provenance)
2. **GB (United Kingdom)** - Status E (Research started)
3. **CA (Canada)** - Status C
4. **FR (France)** - Status C
5. **DE (Germany)** - Status C
...*(Full 124-jurisdiction queue tracking logged in system)*

## 6. JURISDICTION × CATEGORY RESEARCH: GB (UNITED KINGDOM)

### Labor / Workday Research
- **Local Crew Labor:** RESEARCHED (Partial)
- **Workday / OT Structure:** RESEARCHED (Partial)
- **Findings:** Pact/Bectu TV Drama Agreement updated Jan 1, 2024, separates productions into 4 budget bands (e.g., Band 1 up to £1.25M, Band 4 over £8M). Rate cards are recommended by BECTU branches (Camera, Art, Costume), not set industry-wide by Pact.
- **Source:** BECTU Official Website, Pact Agreements (Tier 1/Tier 3)
- **Confidence:** STRONG for structure, PROVISIONAL for exact scale (depends on branch).

### Gaps / Incomplete (Next Execution Needed)
- Fringes / Payroll (Employer NI, Pension)
- Stages / Facilities
- Equipment 
- Locations / Permits
- Travel / Accommodation
- Construction / Materials
- Catering / Unit
- Post / VFX
- Local vs Imported Crew

## 7. GLOBAL COVERAGE ACCOUNTING
- **Canonical jurisdictions requiring MFNI coverage:** 124
- **Researched:** 1 (GB - Partial)
- **Strong/current data:** 0
- **Partial data:** 1 (GB)
- **Provisional (heuristic):** 44 (Existing baseline)
- **No useful data:** 79 (Subnationals and remaining)
- **Blocked:** 0
- **Subnational jurisdictions researched:** 0
- **Stale/unprovenanced existing records:** 44

## 8. REQUIRED SEARCH / CONNECTOR AUDIT TRAIL
- **Tools Available:** `default_api:run_command` (grep, fd, cat), `default_api:search_web`.
- **Tools Used:** `run_command` (discovered `location_cost_benchmarks.py`), `search_web` (searched BECTU 2024 agreements).
- **Domains reached:** BECTU.org.uk.
- **Local-language searches:** 0.

## 9. STOP CONDITION
**STATUS: PARTIAL — CONTINUATION REQUIRED**

**Exact Next Jurisdiction/Category:** 
Resume **GB (United Kingdom)**. Specifically, research UK Employer National Insurance (NI) rates, statutory pension requirements, and union fringes. Then proceed to Stage/Facility pricing in the UK.
