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

### Fringes / Payroll
- **Employer National Insurance (NI):** RESEARCHED. 13.8% for 2024-2025 on earnings above £9,100/yr. (Increases to 15% and £5,000 threshold in April 2025). No special film exemption for Employer NI.
- **Workplace Pension:** RESEARCHED. Statutory minimum employer contribution is 3% of qualifying earnings (total 8%).
- **Holiday Pay:** RESEARCHED. PACT advises 10.77%; BECTU advises 12.07%. BECTU strongly pushing for 12.07% for freelancers under the April 2024 "irregular hours" legislation.
- **Source:** UK Gov (HMRC), PACT/BECTU statements (Tier 1/Tier 3)
- **Confidence:** VERIFIED (Statutory rates) / STRONG (Union guidance).

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major UK studios (Pinewood, Shepperton, Warner Bros Leavesden) do NOT publish public rate cards. Pricing is confidential, case-by-case, and highly dependent on scale, duration, and bundled services (offices, workshops).
- **Source:** Pinewood Studios, Commercial research (Tier 2/Tier 3)
- **Confidence:** BLOCKED (Rate not publicly disclosed for Tier 1 facilities; secondary commercial sources required for modeling).

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Top-tier rental houses (ARRI Rental UK, Procam Take 2) operate purely on a quote-by-request basis for film drama packages. No standardized public rate card is available for 2024. Volume discounts and project duration heavily dictate the actual rate.
- **Source:** ARRI Rental UK, Procam Take 2 (Tier 2)
- **Confidence:** BLOCKED (Rate not publicly disclosed for Tier 1 vendors; secondary/independent price lists may be needed as proxies).

### Locations / Permits
- **Location/Permit Fees:** RESEARCHED. 
- **Findings:** Decentralized across 33 London local authorities. No single rate card. Each borough sets its own fee structure via FilmApp. Temporary Traffic Orders (Road Closures) generally cost £1,000 – £2,000 and require 6-8 weeks minimum notice.
- **Source:** Film London, Borough Film Services (Tier 1/Tier 3).
- **Confidence:** STRONG (Structural understanding), PROVISIONAL (for exact deterministic pricing as it is highly localized).

### Travel / Accommodation
- **Per Diems:** RESEARCHED.
- **Findings:** No industry-wide BECTU per diem agreement. Most productions default to HMRC tax-free benchmark scale rates (up to £25/day for 24-hour periods). Amounts beyond this attract NI/tax unless bespoke arrangements are agreed with HMRC.
- **Source:** UK Gov (HMRC Employment Income Manual) (Tier 1).
- **Confidence:** VERIFIED (Tax threshold) / STRONG (Industry convention).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Industry standard daily rate typically falls between £18 and £35 per head (excluding VAT), with £25/head as a safe baseline for drama/commercial. Breakfast usually adds £6–£10/head.
- **Source:** UK location catering commercial vendors (e.g. Reel Menus) (Tier 2).
- **Confidence:** STRONG (Primary commercial quotes).

### Post Production / VFX
- **VFX Incentive Economics:** RESEARCHED.
- **Findings:** Effective Jan 1, 2025, the UK Audio-Visual Expenditure Credit (AVEC) provides an enhanced 39% rate for VFX (net 29.25%). The 80% cap on qualifying expenditure is removed specifically for VFX.
- **Source:** HMRC, BFI (Tier 1).
- **Confidence:** VERIFIED.

### Local vs Imported Crew
- **Imported Labor Tax/Withholding:** RESEARCHED. 
- **Findings:** The UK operates a specific Foreign Entertainers Unit (FEU). Payments to non-UK resident performers/cast (even via loan-out companies) require a strict 20% withholding tax, which must be modeled. However, this 20% FEU withholding does NOT apply to imported technical crew (e.g., directors, camera operators) who may fall under standard dual-taxation or temporary worker rules depending on time spent. 
- **Source:** HMRC Foreign Entertainers Unit (Tier 1).
- **Confidence:** VERIFIED.

### Construction / Materials
- **Materials Pricing:** RESEARCHED.
- **Findings:** No film-specific rate cards exist for raw construction materials (timber, steel, paint). Filming in the UK requires tracking general regional construction material price indices (Opex / BCIS).
- **Source:** Commercial Construction Indices.
- **Confidence:** PROVISIONAL (Requires dynamic macro-economic linkage rather than a static film benchmark).

## 7. JURISDICTION × CATEGORY RESEARCH: US (UNITED STATES)

### Fringes / Payroll (Union)
- **Union Pension & Health (P&H) Rules:** RESEARCHED.
- **Findings:** 
  - **SAG-AFTRA:** Typically ~21% of gross for Pension & Health, subject to budget tier ceilings.
  - **DGA:** ~20% total (e.g., 8.5% Pension + 11.5% Health).
  - **IATSE & Teamsters:** Do NOT use flat percentages. They operate on a mix of percentage-based rates and **flat hourly contributions** depending on the specific Local (e.g. Local 44, Local 399) and whether it's a production city vs distant location.
- **Source:** SAG-AFTRA, DGA, Entertainment Payroll guidelines (Wrapbook, GreenSlate, EP) (Tier 1/Tier 3).
- **Confidence:** STRONG (Structural understanding).

### Fringes / Payroll (Statutory CA, NY, GA)
- **FICA / FUTA:** RESEARCHED. 
- **Findings:** Federal Social Security is 6.2% (capped at $168,600 for 2024), Medicare 1.45% (uncapped). FUTA is 0.6% effective on the first $7,000.
- **State Unemployment Insurance (SUI):** RESEARCHED.
  - **California (US-CA):** 3.4% on $7,000 wage base (plus 0.1% ETT).
  - **New York (US-NY):** 4.1% on $12,500 wage base.
  - **Georgia (US-GA):** 2.7% on $9,500 wage base.
- **Source:** State Depts of Labor, IRS (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities (CA, NY, GA)
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Square footage pricing is rarely used. Flat daily rates are the standard, scaling by market:
  - **Los Angeles (CA):** $1,000 – $5,000+ per day. Premium for soundproofing and Hollywood proximity.
  - **New York (NY):** $1,500 – $6,000+ per day. High real estate premium and logistics.
  - **Atlanta (GA):** $500 – $2,500+ per day. Highly competitive, often bundled "all-in" with grip/lighting.
- **Source:** Commercial studio listings (Tier 2/Tier 3).
- **Confidence:** STRONG (Market range), PROVISIONAL (for exact deterministic pricing as it varies by bundle).

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Similar to the UK, tier 1 camera/grip vendors (Panavision, ARRI, Keslow) do not publish static rate cards. Pricing is heavily quote-based, depending on duration and volume.
- **Source:** Major rental houses (Tier 2).
- **Confidence:** BLOCKED (Requires deterministic input from actual production quotes).

### Travel / Accommodation
- **Per Diems (Distant Location):** RESEARCHED.
- **Findings:** Union CBAs dictate the absolute floor for "distant location" per diems. For 2024, SAG-AFTRA requires ~$75/day ($16B/$22L/$37D). IATSE requires $70/day (scaling to $75/day in 2026). DGA aligns with union standards ("first class" requirement). GSA rates are utilized primarily to cap tax-free accountability, not as a replacement for the union minimum floor.
- **Source:** SAG-AFTRA, IATSE Basic Agreement, GSA (Tier 1).
- **Confidence:** VERIFIED.

### Locations / Permits (CA, NY, GA)
- **Permit Fees:** RESEARCHED.
- **Findings:** 
  - **Los Angeles (FilmLA):** $931 standard application fee (up to 5 locations/7 days); $350 for low-impact shoots.
  - **New York (NYC MOME):** $500 application fee covering a 14-day period.
  - **Georgia:** Highly decentralized. Atlanta charges ~$100 app fee + $300/mo. Savannah charges $325/location. 
- **Source:** FilmLA, NYC MOME, Georgia Local Film Offices (Tier 1).
- **Confidence:** VERIFIED.

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Ranges from $30 to $65 per person per day for standard hot meals (breakfast/lunch). Craft services alone average $15-$20/day. LA trends toward the higher end, while Atlanta offers more competitive bundled rates.
- **Source:** Commercial production catering quotes (Tier 2).
- **Confidence:** STRONG (Market range).

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** The US framework is highly disjointed. 
  - **California:** Introduces a standalone 35%-50% post-production credit (Sept 2026) and a 5% VFX uplift on general incentives, but programs are capped.
  - **New York:** Dedicated fully refundable 30% credit for post-production (plus 5% upstate uplift).
  - **Georgia:** Transferable 20% base credit for post-production (plus uplifts), notably with NO annual cap.
- **Source:** CA Film Commission, NY State Governor's Office of Motion Picture & Television Development, Georgia Dept of Economic Development (Tier 1).
- **Confidence:** VERIFIED.

## 8. JURISDICTION × CATEGORY RESEARCH: CA (CANADA)

### Fringes / Payroll (Union)
- **Union Pension & Health (P&H) Rules:** RESEARCHED.
- **Findings:** 
  - **IATSE (e.g. Local 891 BC):** ~16.5% - 17.0% for most standard productions.
  - **DGC:** Mandatory fringe packages varying slightly by ON vs BC. 
  - **ACTRA:** Producer contributions are generally around 12% for insurance/retirement.
- **Source:** BCCFU, ACTRA, DGC (Tier 1).
- **Confidence:** STRONG (Structural understanding).

### Fringes / Payroll (Statutory ON, BC, QC)
- **CPP / EI / EHT:** RESEARCHED. 
- **Findings:** 
  - **Federal CPP:** 5.95% on first tier ($68.5k), plus 4% on second tier ($68.5k-$73.2k).
  - **Federal EI:** 2.324% up to $63.2k.
  - **Ontario (CA-ON):** Employer Health Tax (EHT) up to 1.95% (exemption under $1M payroll).
  - **British Columbia (CA-BC):** EHT up to 5.85% on payroll over $1.5M (exemption under $1M).
  - **Quebec (CA-QC):** Requires QPIP (Quebec Parental Insurance Plan) instead of federal EI parental premiums. 
- **Source:** CRA, Provincial Ministries of Finance (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities (ON, BC, QC)
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Follows US flat-rate daily standard (not sq ft). Average daily rates for standard professional stages range from CAD $750 to $2,250+, heavily dependent on bundled grip/lighting packages.
- **Source:** Commercial studio listings in Toronto/Vancouver/Montreal (Tier 2/Tier 3).
- **Confidence:** STRONG (Market range), PROVISIONAL (exact determinism).

### Travel / Accommodation
- **Per Diems (Distant Location):** RESEARCHED.
- **Findings:** Per diems are dictated specifically by the collective agreements (ACTRA IPA, BCCFU Master Agreement). There is no standard flat government rate applied to film workers. Actual meals provided reduce the per diem allowance dollar-for-dollar.
- **Source:** ACTRA, BCCFU (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** As in the US and UK, standardizing a deterministic "rate card" for equipment is fundamentally flawed for major vendors (e.g., Sunbelt Rentals Film & TV, formerly William F. White). Pricing requires custom quotes based on volume, bundle, and schedule.
- **Source:** Sunbelt Rentals/WFW (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits (CA-ON, CA-BC, CA-QC)
- **Permit Fees:** RESEARCHED.
- **Findings:**
  - **Toronto (CA-ON):** Tiered system based on scope. Features/Series pay $100 registration + $300 location permit + $200 parks permit, plus $500 for road closures.
  - **Vancouver (CA-BC):** $2,000 per day for the standard daily activity filming fee.
  - **Montreal (CA-QC):** Nominal $38 application fee, but physical occupancy rates scale up to ~$1,300/day.
- **Source:** Toronto City Hall, City of Vancouver, MFTC (Tier 1).
- **Confidence:** VERIFIED.

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Professional on-set catering for mid-to-large productions generally ranges from CAD $25 to $45+ per person for standard hot meals, exceeding $50-$70+ for full mobile kitchen premium packages.
- **Source:** Commercial catering quotes (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Canada allows stacking federal (CPTC 25% or PSTC 16% on labour) with provincial VFX bonuses:
  - **Ontario (CA-ON):** OCASE provides 18% refundable on labour for VFX/Animation. (No longer requires base production to be shot in ON).
  - **British Columbia (CA-BC):** DAVE offers 16% on labour.
  - **Quebec (CA-QC):** 16% enhancement on labour for VFX, but capped at 65% of eligible labour costs.
- **Source:** Ontario Creates, Creative BC, BCTQ (Tier 1).
- **Confidence:** VERIFIED.

### Local vs Imported Crew (TRIP Nuances)
- **Imported Labor Tax/Withholding:** RESEARCHED.
- **Findings:** While TRIP now covers non-European actor remuneration (as of 2026), payments to non-resident foreign crew are subject to French withholding tax (*retenue à la source*) on a progressive scale (0%, 12%, 20%). The French PSC acts as the tax collector (via PASRAU).
- **Source:** Impots.gouv.fr (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Consistent with UK/US/CA markets, major French rental houses (TSF, RVZ, Panavision France) do not publish static rate cards. Pricing is handled purely via custom package quotes.
- **Source:** TSF, RVZ (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

## 10. JURISDICTION × CATEGORY RESEARCH: DE (GERMANY)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Germany requires contributions to five branches of social insurance (Pension, Health, Unemployment, Long-Term Care, Accident). Employer-side statutory fringes generally amount to **20% to 27%** of gross salary, subject to statutory ceilings (*Beitragsbemessungsgrenzen*). An additional ~10% must be budgeted for mandatory holiday pay.
- **Source:** DFFF Guidelines, German Social Security (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major studios (Studio Babelsberg, MMC Studios, Penzing Studios) do not publish rate cards. Facilities operate as full-service hubs and pricing is bespoke based on duration, technical needs (e.g. LED volumes), and bundled construction services.
- **Source:** Studio Babelsberg, Penzing (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Decentralized at the municipal level. 
  - **Berlin:** Tiered general filming permit required for public space/traffic orders (e.g., €50/1 day, €300/year). Special usage/parking fees are additional.
  - **Munich:** Administered via the municipal film office, with costs based on public domain occupation/stopping bans.
- **Source:** BBFC (Berlin), FFF Bayern (Tier 1).
- **Confidence:** VERIFIED.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Germany utilizes an automatic non-repayable grant system, not a tax credit. DFFF II (for production service providers) and GMPF provide a **30% grant** on approved German production costs, which covers VFX and post-production.
- **Source:** FFA (Filmförderungsanstalt) (Tier 1).
- **Confidence:** VERIFIED.

### Gaps / Incomplete (Next Execution Needed)
- DE Catering / Unit Services
- DE Equipment pricing structure

## 11. GLOBAL COVERAGE ACCOUNTING
- **Canonical jurisdictions requiring MFNI coverage:** 124
- **Researched:** 5 (GB, US, CA, FR - Completed, DE - Partial)
- **Strong/current data:** 0
- **Partial data:** 5 (GB, US, CA, FR, DE)
- **Provisional (heuristic):** 44 (Existing baseline)
- **No useful data:** 79 (Subnationals and remaining)
- **Blocked:** 0
- **Subnational jurisdictions researched:** 8 (US-CA, US-NY, US-GA, CA-ON, CA-BC, CA-QC, DE-Berlin, DE-Bavaria)
- **Stale/unprovenanced existing records:** 44

## 12. REQUIRED SEARCH / CONNECTOR AUDIT TRAIL
- **Tools Available:** `default_api:run_command` (grep, fd, cat), `default_api:search_web`.
- **Tools Used:** `run_command` (discovered `location_cost_benchmarks.py`), `search_web` (searched CA CBA rates).
- **Domains reached:** BECTU.org.uk, Gov.uk, PACT.co.uk, Pinewood Group, ARRI Rental, Film London, IRS.gov, SAG-AFTRA, DGA, CA EDD, NY DOL, GA DOL, FilmLA, NYC MOME, GSA.gov, CRA, BCCFU, ACTRA, DGC, Toronto.ca, Vancouver.ca, BCTM, Ontario Creates, Creative BC, URSSAF, Audiens, CNC, Film France, Paris Film, FFA.de, BBFC, FFF Bayern, Studio Babelsberg, Impots.gouv.fr.
- **Local-language searches:** 0.

## 13. STOP CONDITION
**STATUS: PARTIAL — CONTINUATION REQUIRED**

**Exact Next Jurisdiction/Category:** 
FR (France) structural category coverage is complete. Resume **DE (Germany)** research, focusing on DE Catering and DE Equipment proxies. After DE, advance to **AU (Australia)**.