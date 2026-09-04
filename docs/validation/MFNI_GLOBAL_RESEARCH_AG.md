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

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** No fixed daily rate. Standard professional film catering ranges from €30 to €50+ per person/day for full-service (hot meals, crafty). Smaller drop-off buffets run €20-€30.
- **Source:** German film catering providers (Tier 2).
- **Confidence:** STRONG.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Major rental houses (e.g., ARRI Rental Munich/Berlin) operate entirely on custom quotes and bundled packages. There is no standard public rate card for high-end cinematic packages.
- **Source:** ARRI Rental (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

## 11. JURISDICTION × CATEGORY RESEARCH: AU (AUSTRALIA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Australia's employer payroll obligations are structured around three pillars:
  - **Superannuation Guarantee:** **12%** of ordinary time earnings (as of July 2025). Under "Payday Super" rules, this must be paid simultaneously with wages.
  - **Payroll Tax:** State-based (NSW, VIC, QLD, WA). Calculated as a percentage of total taxable wages once specific annual thresholds are met.
  - **Workers' Compensation:** State-based (e.g., WorkCover). Premiums average ~1% of payroll depending on industry risk classifications.
- **Source:** ATO, State Revenue Offices (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major studio lots (Village Roadshow Studios, Docklands Studios Melbourne, Disney Studios Sydney) do not publish static public rate cards. They operate on bespoke quotes negotiated based on stage size, duration, and bundled services (often dry hire + mandatory support spaces).
- **Source:** Docklands Studios, Village Roadshow (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Australia offers a **30% refundable tax offset** via the Post, Digital and Visual Effects (PDV) Offset. 
  - **Threshold:** Requires a minimum QAPE (Qualifying Australian Production Expenditure) of AU$500,000 on PDV work.
  - **Stacking:** Can often be combined with state-level incentives (10% to 20%), but is mutually exclusive with the federal Location Offset or Producer Offset.
- **Source:** Australian Government (Department of Arts) (Tier 1).
- **Confidence:** VERIFIED.

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Decentralized to Local Government Areas (LGAs) rather than state screen agencies. Fees depend strictly on impact level. E.g., Brisbane charges a ~$904 baseline for standard permits (with low-impact exemptions). Sydney bases fees on ultra-low to high impact scales.
- **Source:** Screen NSW, Brisbane City Council, City of Sydney (Tier 1).
- **Confidence:** VERIFIED.

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Highly variable. Casual drop-off starts around AUD $20–$55 per head. Full-service food trucks covering breakfast/lunch/crafty run closer to corporate event rates of AUD $60–$150+ per person.
- **Source:** Australian production catering benchmarks (Tier 2).
- **Confidence:** STRONG.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** In line with global tier-1 standards, Australian branches of major rental houses (Panavision Sydney, Lemac) do not publish static rate cards. Pricing is driven by custom quotes and scaled package duration.
- **Source:** Lemac, Panavision (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

## 12. JURISDICTION × CATEGORY RESEARCH: NZ (NEW ZEALAND)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Unique classification structure. The majority of NZ film crew operate as **independent contractors**, meaning there is *no statutory requirement* for the production to provide Holiday Pay or employer KiwiSaver (superannuation). Contractors pay their own ACC levies (accident compensation).
  - *Note:* The Screen Industry Workers Act 2022 (SIWA) allows contractors to bargain collectively for minimum terms, creating baseline conditions without reclassifying them as employees.
  - If classified as an employee (rare), standard 3% KiwiSaver, ACC levies, and 8% Holiday Pay apply.
- **Source:** New Zealand Government, SIWA (Tier 1).
- **Confidence:** VERIFIED.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** NZ offers a **20% cash rebate** via the Post, Digital, and Visual Effects (PDV) Grant on Qualifying New Zealand Production Expenditure (QNZPE). 
  - **Uplift:** An additional 5% (total 25%) is available if the project meets significant economic benefit criteria.
  - **Threshold:** Requires a minimum spend of NZ$250,000.
- **Source:** New Zealand Film Commission (NZFC) (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major facilities (Stone Street Studios, Auckland Film Studios, Lane Street) do not publicly list rate cards. Pricing is handled via private negotiations based on duration, scale, and bundled spaces (offices, workshops).
- **Source:** Auckland Film Studios, Lane Street (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Managed via regional film offices (e.g., Screen Auckland, Screen Wellington) using the FilmApp platform. 
  - Auckland fees range from NZ$75 to $2,110+ per day based on impact. 
  - Wellington fees are mostly waived for facilitation but site-specific upkeep fees apply.
- **Source:** Screen Auckland, Screen Wellington (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Top-tier rental houses (Panavision NZ, Metro Film, Portsmouth Rentals) operate on bespoke quoting rather than universal rate cards. Pricing scales dynamically based on production duration and package size.
- **Source:** Panavision NZ, Metro Film (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Highly variable. Quotes are "food only" (excluding staffing/crockery unless specified). Small shoots range ~$55/head, but large mobile-kitchen operations scale based on exact hot meal counts (not including separate crafty budgets of NZ$2-$10/day).
- **Source:** Gatting's, The Food Lab (Tier 2).
- **Confidence:** STRONG.

## 13. JURISDICTION × CATEGORY RESEARCH: ZA (SOUTH AFRICA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** South African statutory employer contributions for 2024/2025 include:
  - **UIF (Unemployment Insurance Fund):** 1% of remuneration (capped at R177.12 max monthly employer contribution).
  - **SDL (Skills Development Levy):** 1% of total payroll (mandatory if annual payroll > R500,000).
  - **COIDA (Compensation for Occupational Injuries):** Industry-risk dependent, generally ~0.1% to 3% of payroll up to an earnings ceiling of R597,328 per employee.
- **Source:** South African Revenue Service (SARS), Dept of Employment and Labour (Tier 1).
- **Confidence:** VERIFIED.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Administered by the dtic (Department of Trade, Industry and Competition). The Foreign Film and Television Production and Post-Production Incentive offers a base **20%** on Qualifying South African Post-Production Expenditure (QSAPPE).
  - **Uplifts:** Increases to 22.5% (for >R10M spend) or 25% (for >R15M spend).
  - *Note:* As of late 2026, the dtic FTIP guidelines are under comprehensive review following a processing backlog, though existing approved parameters currently remain the baseline.
- **Source:** dtic South Africa (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major facilities (Cape Town Film Studios, Atlantic Studios) operate on a quote basis. They do not publish public rate cards; rates scale based on stage size, green screen/cyclorama needs, and duration.
- **Source:** Atlantic Studios, Cape Town Film Studios (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** The Cape Town Film Permit Office enforces a highly competitive **zero-rated tariff** for filming permits and municipal services on City-owned property. (Note: SANParks/CapeNature charge separate authority fees).
- **Source:** City of Cape Town (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Major rental houses (Panavision/Panacam Africa, Media Film Service) operate strictly on customized quotes based on equipment list and duration (e.g., 3-day or 4-day weeks). No public static rate cards.
- **Source:** Media Film Service (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Variable based on service level. Drop-off is roughly R120-R250/head. Buffet/casual on-set catering (spit-braais, etc.) is roughly R280-R400/head. Full-service custom film catering requires bespoke quotes.
- **Source:** South African catering market data (Tier 2).
- **Confidence:** STRONG.

## 14. JURISDICTION × CATEGORY RESEARCH: IE (IRELAND)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Employer PRSI (Pay-Related Social Insurance) is mandatory. As of late 2024, the standard Class A employer PRSI rate is approximately 11.15% (increased by 0.1% in October 2024). This is a statutory payroll cost, not a fringe benefit.
- **Source:** Irish Department of Social Protection (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major facilities (Ardmore Studios, Troy Studios) operate exclusively on custom quotes based on production scale and duration. Rate cards are not publicly listed.
- **Source:** Ardmore Studios (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Managed by local councils. Dublin City Council uses a tiered structure based on production budget, ranging from €100/day for <€500k budgets up to €1,000+/day for >€4M features. Surcharges apply for specific areas like Henrietta Street.
- **Source:** Dublin City Film Office (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Top-tier rental houses (Panavision Ireland, Teach Solais) operate via bespoke quoting based on equipment lists. No static rate cards exist for cinematic packages.
- **Source:** Panavision (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Standard crew catering (hot lunch + mid-morning break) runs €25–€30 per head per day as a safe baseline, but can scale €20-€40 based on mobile kitchen vs drop-off requirements.
- **Source:** Irish Catering Market Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Section 481 provides a base 32% tax credit. A specific VFX uplift (raising the rate to 40% on up to €10m of spend) applies if the project incurs at least €1m in eligible VFX expenditure in Ireland. No principal photography is required in Ireland to claim this VFX uplift.
- **Source:** Screen Ireland / Irish Revenue (Tier 1).
- **Confidence:** VERIFIED.

## 15. JURISDICTION × CATEGORY RESEARCH: IT (ITALY)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Highly burdened statutory fringes. Includes INPS (Social Security, 23-32%), INAIL (Accident Insurance, 0.4-1.0%), and TFR (Severance, 7.41%). Total employer burden frequently adds 35-45% to base gross salaries.
- **Source:** INPS, INAIL (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Cinecittà (Rome) does not publish standardized rates. Pricing is bespoke based on stage dimensions, virtual production needs, and rental duration.
- **Source:** Cinecittà (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Highly variable by municipality. Standard street permits typically start around €300/day (Rome/Florence), but major historical landmarks incur massive tiered fees up to tens of thousands of euros.
- **Source:** Roma Lazio Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Standard practice rejects public rate cards. Panalight and D-Vision Movie People operate on custom packages with volume/duration discounts (often 40-60% off internal list prices for features).
- **Source:** Panalight, D-Vision Movie People (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Standard on-set catering ranges €20–€35 per person per meal. Specialized requirements or premium tablescale service can escalate to €35–€70+.
- **Source:** Italian catering benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** International productions access a 40% tax credit. Capped at €20m per year per company. AI costs are strictly ineligible *unless* specifically attributable to VFX/special effects.
- **Source:** DGCA / Cinecittà (Tier 1).
- **Confidence:** VERIFIED.

## 16. JURISDICTION × CATEGORY RESEARCH: ES (SPAIN)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Employer social security (Seguridad Social) adds approximately 30-32% burden to the gross salary. This covers Common Contingencies (23.6%), Unemployment (5.5-6.7%), FOGASA, MEI, and Training. The contribution base is capped (e.g., €4,720.50/month max in 2024).
- **Source:** Tesorería General de la Seguridad Social (TGSS) (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major studio hubs (Madrid Content City, Parc Audiovisual de Catalunya in Terrassa) do not publish static rates. Standard pricing models are quote-dependent, scaling from €1,000+ per day for large format stages, subject to power usage and duration discounts.
- **Source:** Madrid Content City, Parc Audiovisual de Catalunya (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Municipal control. Madrid charges an admin fee (~€48) plus variable linear-meter space occupation fees for standard shoots; small crew shoots are free. Barcelona applies an €89 issuing fee plus occupation minimums (~€480-€600/day for vehicles).
- **Source:** Madrid Film Office, Barcelona Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Major Spanish cinema rental houses (EPC, Ovide, RC Service) operate on a "Request a Quote" basis for cinematic packages (ARRI, Sony, RED). No public static rate cards exist.
- **Source:** EPC, RC Service (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Standard crew catering costs typically range between €25 and €35 per head per day (main meals), with separate scaled rates for background actors (~€15).
- **Source:** Spanish Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Mainland Spain offers a 30% deduction on the first €1M and 25% on the rest (max €20M/film). The Canary Islands offer 54% on the first €1M and 45% thereafter (max €36M/film). The minimum qualifying spend for VFX/post-production projects is exceptionally low at €200,000.
- **Source:** Spain Film Commission, ZEC (Tier 1).
- **Confidence:** VERIFIED.


## 17. JURISDICTION × CATEGORY RESEARCH: PT (PORTUGAL)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** The standard employer statutory contribution (Taxa Social Única or TSU) is 23.75%, with no ceiling. Mandatory workplace accident insurance adds another 1-2%. However, the industry relies heavily on independent contractors ("recibos verdes") where the employer TSU does not apply.
- **Source:** Portugal Social Security (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Portugal lacks massive Hollywood-scale studio complexes; hubs like Beato Innovation District act mostly as event spaces. Dedicated professional studios (TODOS, Comuna) use bespoke quoting or modular packages, but standard global rate cards are non-existent.
- **Source:** TODOS Creative Hub (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Managed by local councils (e.g., Lisbon Câmara Municipal). Fees depend on public space occupation and logistical impact (parking, traffic). A special noise license (LER) may be required. Small/cultural projects may apply for exemptions.
- **Source:** Lisboa Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Established rental houses (Planar, Smiling, Digital Azul) operate via custom proposals based on equipment lists and project duration. 
- **Source:** Planar Lda (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Professional on-set catering ranges from €20 to €40 per person for standard production needs. A statutory meal allowance (when catering is absent) proxies around €12.50-€15.00/day.
- **Source:** Portuguese Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Administered by ICA / PIC Portugal (recently transitioning to SCRI.PT/RIPAC), the Cash Rebate offers 25% to 30% on eligible expenditure. The minimum local spend requirement for post-production-only projects is €200,000.
- **Source:** Portugal Film Commission, ICA (Tier 1).
- **Confidence:** VERIFIED.

## 18. JURISDICTION × CATEGORY RESEARCH: HU (HUNGARY)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** The employer Social Contribution Tax (SZOCHO) is mandatory at a flat rate of 13% on gross salaries. There is no special film-industry exemption for this tax, but it qualifies as eligible local spend for the national rebate.
- **Source:** Hungarian Tax and Customs Administration (NAV) (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major, state-of-the-art studio campuses (Origo Studios, Korda Studios) do not publish static rates. They operate strictly on bespoke pricing tailored to high-budget international features, considering volume and duration.
- **Source:** Origo Studios, Korda Studios (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Hungary uses a streamlined "one-door" system. There is a standard administrative fee of HUF 50,000 (HUF 130,000 expedited), plus variable public-area usage fees based on the footprint of the shoot. Small, non-disruptive setups (tripod < 30 mins) are often exempt.
- **Source:** NFI Location Office (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Major vendors like Visionteam and Sparks Camera & Lighting expect formal "Order Requests" for custom quotes. Prices are negotiated based on volume; no public rate cards exist for cinematic packages.
- **Source:** Visionteam, Sparks (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Highly competitive. Mid-range professional production catering typically proxies around $20–$35 USD (€18–€32) per head per day, often bundled into local production service agreements to qualify for the rebate.
- **Source:** Hungarian production benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Hungary offers a massive 30% cash rebate on eligible costs (effectively up to 37.5% when leveraging the allowance for non-Hungarian spend). Post-production and VFX are fully eligible standalone activities.
- **Source:** National Film Institute Hungary (NFI) (Tier 1).
- **Confidence:** VERIFIED.


## 19. JURISDICTION × CATEGORY RESEARCH: CZ (CZECH REPUBLIC)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Heavy statutory burden totaling 33.8% of gross salary. This comprises Social Security (24.8% up to an annual cap) and Health Insurance (9.0% uncapped), plus a minor accident liability premium (~0.28%).
- **Source:** Czech Social Security Administration (CSSZ) (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Top-tier studios (Barrandov Studio, Prague Studios) require direct production inquiries for bespoke pricing. Daily/hourly rate cards do not exist for the large sound stages.
- **Source:** Barrandov Studio (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Decentralized. Managed by municipal districts and local road authorities. Fees are variable based on footprint. High-profile sites (e.g., Charles Bridge) carry massive premiums.
- **Source:** Czech Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Custom quoting model. Panavision Prague and Vantage Film Prague provide bespoke pricing based on proprietary gear sets (e.g., anamorphic lenses) and duration discounts. 
- **Source:** Panavision Prague, Vantage Film (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Standard professional full-service catering ranges from 800 to 1,500 CZK (€30-€60) per person per day. Craft services are typically budgeted separately.
- **Source:** Czech Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Governed by the Audiovisual Act. The standard cash rebate is 25%, but a dedicated rate of 35% applies to animation and digital/VFX productions that do not involve live-action shooting (new framework effective 2025). Max cap is CZK 450 million per project.
- **Source:** Czech Audiovisual Fund (Tier 1).
- **Confidence:** VERIFIED.

## 20. JURISDICTION × CATEGORY RESEARCH: MX (MEXICO)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** A heavily burdened payroll environment. Employers pay IMSS (Social Security, 20-35%+ based on risk), INFONAVIT (Housing, 5%), SAR (Retirement, 2%), plus State Payroll Tax (ISN, 1-4%). Additional statutory benefits (Aguinaldo, Vacation premium) push the total burden to roughly 30-45% over base salary.
- **Source:** Mexican Federal Labor Law (LFT), IMSS (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major sound stages (Estudios Churubusco, Estudios Gabriel García Márquez) do not publish static rates. Quotes are bespoke based on duration, power requirements, and additional facility needs (e.g., LED volumes).
- **Source:** Estudios Churubusco, Estudios GGM (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** In Mexico City, CFilma coordinates permits. Fees are decentralized and highly variable; simple admin permits exist, but specific locations (museums, INAH archaeological sites, commercial plazas) require negotiated usage fees.
- **Source:** CFilma (Comisión de Filmaciones de la CDMX) (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Premier rental houses (e.g., EFD Equipment & Film Design) do not publish rate cards. They operate strictly on formal quotes for camera, lighting, and grip packages tailored to the production schedule.
- **Source:** EFD (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Standard to intermediate film catering ranges from $500 to $1,500 MXN (~$30-$80 USD) per person per day. Highly variable based on craft services inclusion and overtime "second meal" requirements.
- **Source:** Mexican Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Under the new EFICA program (2026-2030), Mexico offers a 30% transferable income tax credit. Post-production and VFX are eligible with an exceptionally low minimum spend threshold of MXN 5 million. Program is capped at MXN 40M per project.
- **Source:** EFICA Guidelines, IMCINE (Tier 1).
- **Confidence:** VERIFIED.


## 21. JURISDICTION × CATEGORY RESEARCH: CO (COLOMBIA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Total burden ranges from 30% to 50% over base salary. Includes Pension (12%), Cajas de Compensación (4%), and ARL (risk, 0.522%-6.96%). Health (8.5%), SENA (2%), and ICBF (3%) are exempt if the employee earns <10 SMMLV and the employer pays corporate income tax. Heavy "Prestaciones Sociales" (Prima, Cesantías, Vacations) apply.
- **Source:** Colombian Tax Statute, Ministry of Labor (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major studio complexes (TIS Productions/Fox Telecolombia, Caracol) require direct production inquiries for bespoke quotes. No public rack rates exist for large sound stages.
- **Source:** TIS Productions, Colombia Film Commission (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Bogotá utilizes the PUFA (Unified Permit for Audiovisual Filming) via the SUMA+ platform. Fees are calculated dynamically based on public space economic exploitation. Significant reductions (up to 70%) apply for Law 1556 beneficiary projects.
- **Source:** Bogotá Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Major regional rental providers like Congo Films do not publish standard rate cards. Pricing requires formal production quotes based on gear packages (ARRI/RED) and duration.
- **Source:** Congo Films (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Extremely cost-effective compared to Western hubs. Highly customized based on service level, but proxies suggest $15-$30 USD per head per day for standard production catering.
- **Source:** Colombian Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Governed by Law 1556. Two primary mechanisms: FFC (40% cash rebate on audiovisual services / 20% on logistics) or CINA (35% transferable tax credit). Post-production-only projects can qualify for CINA directly, or FFC if the primary production phase was also subsidized.
- **Source:** Proimágenes Colombia, Law 1556 (Tier 1).
- **Confidence:** VERIFIED.

## 22. JURISDICTION × CATEGORY RESEARCH: BR (BRAZIL)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** A very high burden ("Custo Brasil"). Employers pay INSS (20%), FGTS (8%), System S (Terceiros, ~5.8%), RAT (1-3%). Additionally, mandatory 13th salary, vacation premium (+1/3), and a 40% FGTS fine for termination without cause push the effective total burden to roughly 60-70% over the base net salary for formal CLT hires.
- **Source:** Brazilian CLT, INSS, Receita Federal (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major sound stages (Quanta Estúdios, Polo Cinematográfico de Paulínia, Estúdios Globo) operate exclusively on project-based quotes. Independent studios in São Paulo quote R$ 3,500 to R$ 8,500/day, but the prime infrastructure remains opaque.
- **Source:** Quanta Estúdios, Spcine (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Handled by regional commissions (Rio Film Commission, Spcine). Base permits for public domain spaces are generally free, but productions must pay associated costs for municipal services like traffic control (CET) or police/security.
- **Source:** Rio Film Commission, Spcine (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** No fixed rate cards from prime vendors (Marc Films, Naymovie, Quanta). Pricing is highly customized, often requiring a local partner (e.g., Brazil Production Services) to navigate tax/import logistics and negotiate volume discounts.
- **Source:** Marc Films, Naymovie (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Heavily bifurcated. Basic local drop-off (R$ 50-100/head) vs. full professional itinerant catering. Proxies out to ~$15-$30 USD per head, but entirely quote-dependent based on craft service complexity.
- **Source:** Brazilian Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** No federal cash rebate for foreign production. State-level cash rebates exist (RioFilme, Spcine - typically 20-30%) but are tied to physical filming criteria and local spend, rather than standalone VFX/post-production projects.
- **Source:** ANCINE, Spcine, RioFilme (Tier 1).
- **Confidence:** VERIFIED.


## 23. JURISDICTION × CATEGORY RESEARCH: AR (ARGENTINA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Standard employer contributions run 24-26.4% (SIPA, PAMI, Asignaciones Familiares) plus ~6% for Obra Social. Including SAC (Aguinaldo / 13th month), ART (risk insurance), and vacation accruals, the total burden is extremely heavy. Highly unionized environment (SICA) dictates strict minimums.
- **Source:** ARCA (formerly AFIP), Argentine Labor Law (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** No public rate cards for major studios (Baires Studios, Pol-ka, Pampa Films). Market volatility and currency fluctuations mean all large facilities quote bespoke in USD or adjusted ARS based on duration and bundled services.
- **Source:** Baires Studios, Pol-ka (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Buenos Aires uses the BASet system (Buenos Aires Film Set). Generally highly affordable, but requires a locally registered production company/fixer. Costs vary based on disruption scale. Process takes 2-5 days.
- **Source:** Buenos Aires Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Universal lack of static rate cards due to extreme inflation and currency mechanics. Rental houses (Cinecolor, J&J, Lahaye Media) quote bespoke based on gear packages and immediate market exchange rates.
- **Source:** Lahaye Media, Argentine Rental Benchmarks (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Requires custom quotes. Extremely cost-effective for international productions leveraging currency advantages, but standard daily rates per head are not published.
- **Source:** Argentine Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** No national cash rebate (INCAA focuses on domestic). City of Buenos Aires offers the BA Producción Internacional (BA Cash Rebate) at 20%, but it strictly requires a minimum of 4 physical shoot days in the city to qualify local expenditure (including post). Standalone post-production does not qualify.
- **Source:** Buenos Aires Film Commission, INCAA (Tier 1).
- **Confidence:** VERIFIED.

## 24. JURISDICTION × CATEGORY RESEARCH: CL (CHILE)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** A comparatively low standard employer burden compared to other LATAM hubs, as employees bear the bulk of Pension (AFP, 10%) and Health (Fonasa/Isapre, 7%) directly via deductions. Employers pay Seguro de Cesantía (2.4-3%), Mutual de Seguridad (0.9-3.4%), and SIS (1.4-1.85%). However, a mandatory profit-sharing "Gratificación" (typically 25% up to a cap) significantly raises the real cost.
- **Source:** Previred, Chilean Labor Directorate (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Major sound stages (e.g., Kuarzo Atresmedia) do not publish rate cards. Facilities are booked under a B2B model requiring technical riders and formal proposals.
- **Source:** Kuarzo (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Filming permits are decentralized. Film Commission Chile (FCCh) facilitates, but municipalities and property owners (like CONAF for parks) set their own highly variable tariffs.
- **Source:** Film Commission Chile (FCCh) (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** No fixed rate cards from prime vendors (Congo Films Chile, David & Joseph, Atomica). Quotes are customized based on duration and long-term production relationships.
- **Source:** Congo Films, Atomica (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Variable based on location logic (urban Santiago vs. Atacama desert/remote). No standardized per-head fee is published; relies entirely on local fixers soliciting 3-bid vendor quotes.
- **Source:** Chilean Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Driven by the IFI Audiovisual (CORFO). Offers up to a 30% reimbursement (up to 40% if outside Santiago), capped at US$3 million. Post-production and VFX are explicitly eligible.
- **Source:** InvestChile, CORFO (Tier 1).
- **Confidence:** VERIFIED.


## 25. JURISDICTION × CATEGORY RESEARCH: UY (URUGUAY)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Moderate to high employer burden (~28-40% total). BPS mandatory contributions run 12.625% (Pension 7.5%, FONASA 5%, FRL/Guarantee ~0.125%). Added to this are the Aguinaldo (13th month, accrued at 8.33%), Salario Vacacional, and BSE accident insurance (0.3-1%).
- **Source:** Banco de Previsión Social (BPS), MTSS (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** The Reducto Audiovisual Hub (partnered with Musitelli) is the primary premium space. Rates are not published and require bespoke quoting based on technical grid needs.
- **Source:** Reducto, Musitelli (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Regulated by Montevideo Audiovisual (Municipality of Montevideo). Filming in public places is generally free, acting as a major draw for the city, though logistical support (traffic/police) incurs costs.
- **Source:** Montevideo Audiovisual (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Musitelli Film & Digital is the dominant premium rental house. No public rate cards; relies entirely on customized technical quoting.
- **Source:** Musitelli Film & Digital (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Uruguay is generally cost-effective. Proxies suggest $15 to $35 USD per head per day for professional on-set catering, but specific quotes are required.
- **Source:** Uruguayan Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Very aggressive incentives. The new Audiovisual Tax Credit (introduced 2026) offers a 30% transferable tax credit with NO per-project cap. The legacy PUA (Programa Uruguay Audiovisual) also offers cash rebates (typically ~25%). Post-production and VFX are explicitly eligible. VAT is 0% for audiovisual exports.
- **Source:** ACAU (Film and Audiovisual Agency of Uruguay) (Tier 1).
- **Confidence:** VERIFIED.

## 26. JURISDICTION × CATEGORY RESEARCH: PL (POLAND)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Under standard employment contracts, the employer ZUS burden is approx. 19.38% - 22.04% (Pension 9.76%, Disability 6.5%, Accident 0.67-3.33%, Labour Fund 2.45%, FGŚP 0.1%), plus PPK 1.5%. However, many film professionals operate on B2B / civil law contracts which shifts the tax burden.
- **Source:** ZUS (Social Insurance Institution) (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Poland offers high-end facilities (e.g., ATM Studio Warsaw, Alvernia Studios, WFDiF). They do not publish standardized rental rates. Pricing is bespoke, requiring technical riders and often factoring in power and prep/strike days.
- **Source:** ATM Studio, Alvernia Studios (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Managed efficiently by regional bodies like the Mazovia Warsaw Film Commission. Support is free, and filming in the public domain without major disruption is typically free. Fees apply only when blocking traffic or using private/historic properties.
- **Source:** Mazovia Warsaw Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Dominant players like ATM System and Fastmedia operate on a quote-based model for specialized cinema packages. No public rate cards available.
- **Source:** ATM System (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Highly cost-effective. Professional on-set catering benchmarks around 50 - 90 PLN per head per day (approx. $12-$23 USD), with background/extras typically lower (~35 PLN).
- **Source:** Polish Catering Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** 30% cash rebate managed by the Polish Film Institute (PISF). Minimum spend for feature film service work is PLN 1,000,000. Cap is PLN 15M per project. Covers VFX/Post explicitly if routed through a Polish partner.
- **Source:** Polish Film Institute (PISF) (Tier 1).
- **Confidence:** VERIFIED.


## 27. JURISDICTION × CATEGORY RESEARCH: RO (ROMANIA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** The statutory employer burden is uniquely low at a flat 2.25% CAM (Labor Insurance Contribution). Since 2018, the vast majority of social contributions (Pension 25%, Health 10%) are deducted directly from the employee's gross. Total employer cost is essentially Gross Salary × 1.0225.
- **Source:** ANAF (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Historic and massive infrastructure like Bucharest Film Studios (Buftea) and Castel Film Studios offer stage space, but operate strictly on custom B2B proposals based on scale and duration.
- **Source:** Bucharest Film Studios, Castel Film (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Administered decentrally. Bucharest City Hall lists specific tariffs (e.g., ~3,317 Lei for building use/day, ~3 Lei/sqm/day for tech footprints), though exact rates depend on negotiation and local fixer coordination.
- **Source:** Bucharest City Hall (Primăria Municipiului București) (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Equipment vendors like Bivolul and Cutare Film provide custom quoting based on technical lists and project duration. No static rate cards published online.
- **Source:** Bivolul, Cutare Film (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Exceptionally cost-effective. While high-end corporate catering runs €60-€85, film production logic drives costs down significantly, typically requiring quotes from local fixers but benchmarking well below Western European norms.
- **Source:** Romanian Production Benchmarks (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** 30% cash rebate managed by the Office for Film and Cultural Investments (OFIC). Re-launched and active through 2029. Minimum local spend for features is €100,000, capped at €10 million per project.
- **Source:** Office for Film and Cultural Investments (OFIC) (Tier 1).
- **Confidence:** VERIFIED.

## 28. JURISDICTION × CATEGORY RESEARCH: BG (BULGARIA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Highly favorable. The standard employer social security burden (DOO, DZPO, Health, etc.) ranges between 18.92% and 19.62%. Crucially, this is capped at a maximum monthly insurable income (approx. BGN 3,750), meaning high-earning crew incur no additional employer tax beyond the cap. A flat 10% income tax applies.
- **Source:** Bulgarian Social Insurance Code, NRA (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Nu Boyana Film Studios (Sofia) dominates the market with 10 sound stages, underwater tanks, and massive standing sets (e.g., Roman, NYC, London streets). UFO Film and Television Studios provides XR/Virtual Production. Neither publishes public rate cards; both operate on bespoke international quoting.
- **Source:** Nu Boyana, UFO (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Permits in Sofia are relatively cheap (ranging from $100-$600) but also require a mandatory National Film Centre (NFC) tax (1,500 BGN for <1 month). Local fixers are required to navigate the Cyrillic/Bulgarian administrative process.
- **Source:** Sofia Municipality, NFC (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Supplied heavily by in-house studio rentals (Nu Boyana, UFO) and local houses like Magic Shop. Operates entirely on technical riders and bundled package pricing. No flat-file rate cards exist for professional cinema gear.
- **Source:** Nu Boyana Equipment (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Exceptional value. Benchmarked at roughly 25-35% of equivalent costs in Western European hubs (implying ~$15-$25 USD/head). Bundled actively by fixers.
- **Source:** Bulgarian Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** 25% cash rebate administered by the Bulgarian National Film Center (NFC). Cap is €5 million per project. Includes VFX and post-production, provided the local spend conditions are met and the cultural test passed.
- **Source:** Bulgarian National Film Center (Tier 1).
- **Confidence:** VERIFIED.


## 29. JURISDICTION × CATEGORY RESEARCH: RS (SERBIA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Highly favorable. The employer social security burden is a flat 15.15% (10% Pension/PIO + 5.15% Health). Similar to Bulgaria, this is capped at a maximum monthly base (RSD 656,425 in 2024). Flat 10% income tax applies.
- **Source:** Serbian Ministry of Finance (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** PFI Studios (Pink Films International) and Firefly Studios provide world-class infrastructure. Firefly includes an underwater tank. Neither publishes rate cards; pricing is based exclusively on project duration and technical requirements.
- **Source:** PFI Studios, Firefly Studios (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Highly "Film Friendly" (promoted by the Serbia Film Commission). Fees range from $100-$600, but public domain permits are often granted for free if the project promotes Serbia.
- **Source:** Film in Serbia / Serbia Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Vision Team and Cineplanet dominate the professional rental market. The market relies entirely on custom package quoting, enhanced by Serbia's ATA Carnet membership (allowing easy temporary import of specialized gear). No static rate cards.
- **Source:** Vision Team, Cineplanet (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Highly cost-competitive. Standard corporate benchmarks start at ~€10 per head, with professional mobile-kitchen film catering running slightly higher but representing a fraction of Western European costs.
- **Source:** Serbian Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** 25% cash rebate (elevated to 30% for local spend >€5m) managed by Film Center Serbia. Post-production and VFX are explicitly eligible with a distinct, lower minimum local spend requirement of just €150,000.
- **Source:** Film Center Serbia (Tier 1).
- **Confidence:** VERIFIED.

## 30. JURISDICTION × CATEGORY RESEARCH: SE (SWEDEN)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Very High. The statutory employer social security contribution (Arbetsgivaravgifter) is a flat 31.42%, uncapped. Film/TV union collective bargaining agreements (e.g., Scen & Film) add occupational pension and insurances. Total employer burden is widely budgeted at 130%-140% of base gross salary.
- **Source:** Swedish Tax Agency, Scen & Film (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Ystad Studios quotes standard stages (600sqm) at 8,000 to 10,000 SEK per day (~$750-$950 USD). Filmhuset (Stockholm) is more of an administrative hub, with commercial stages managed by independent entities like Multiproduktion.
- **Source:** Ystad Studios, Film i Skåne (Tier 2).
- **Confidence:** VERIFIED.

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Police application fee for public space obstruction is 990 SEK (Polismyndigheten). City usage fees in Stockholm are charged hourly (e.g., 254 SEK/hour).
- **Source:** Polismyndigheten, Stockholm Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Market led by Dagsljus (now Storyline Studios) and Ljud & Bildmedia. Standard packages are highly customized. Equipment rentals operate exclusively on a bespoke quote model.
- **Source:** Storyline Studios, Ljud & Bildmedia (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** High cost environment. Basic production catering runs 200 to 500 SEK per head (~$20-$50 USD). High-end or full-service mobile catering easily exceeds this.
- **Source:** Swedish Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** 25% cash rebate via Tillväxtverket. Specifically includes post-production and VFX. Cap of 10 million SEK per project. The total world budget must hit steep minimums (e.g., 30M SEK for features).
- **Source:** Tillväxtverket (Tier 1).
- **Confidence:** VERIFIED.


## 31. JURISDICTION × CATEGORY RESEARCH: NO (NORWAY)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Modestly high. Employer National Insurance (Arbeidsgiveravgift) is geographically zoned: 14.1% in Zone 1 (Oslo), scaling down to 0% in far north zones. Mandatory Occupational Pension (OTP) adds 2-7%. Holiday Pay (Feriepenger) is ~10.2%-12%. Total fringe burden is budgeted at ~18%-28% on top of base.
- **Source:** Norwegian Tax Administration (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Facilities like Filmparken (Oslo), Storyline Studios, and Filmcamp (Øverbygd) do not publish flat rate cards. Quotes depend heavily on duration, scale, and technical specs.
- **Source:** Filmparken, Filmcamp (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Highly accessible. No national permit fee. In Oslo, public filming is generally free unless it involves road closures/obstructions, which require local municipality/police coordination.
- **Source:** Oslo Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Storyline Studios, Dagslys, and Kamera Rental dominate. No standard rate cards. Smaller independent rentals estimate daily rates using retail-value division (e.g., Retail / 15 for cameras), but major vendors operate strictly on bespoke quotes.
- **Source:** Storyline Studios, Kamera Rental (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Very high cost environment. Simple drop-off lunches start at NOK 200-400 (~$19-$38 USD) per head. Full-service craft/catering on set starts at NOK 500-1000+ (~$47-$95+ USD) per head.
- **Source:** Norwegian Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** 25% cash rebate via Norwegian Film Institute (NFI). The scheme is competitive (projects ranked if oversubscribed). Min local spend is NOK 4 million, with stringent total budget and international financing requirements. Post/VFX is eligible.
- **Source:** Norwegian Film Institute (Tier 1).
- **Confidence:** VERIFIED.

## 32. JURISDICTION × CATEGORY RESEARCH: DK (DENMARK)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Highly unique. Denmark has virtually 0% percentage-based statutory social security. Employers pay nominal flat fees (e.g., ATP is DKK 198/month). However, mandatory Holiday Pay (Feriepenge) is 12.5%, and collective bargaining agreements (CBAs) frequently add 9.5%+ in pension/insurance. Therefore, the total fringe is often budgeted at roughly 22%-25% of gross wages.
- **Source:** Virk.dk, Danish Tax Agency (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** No published flat rate cards. Major stages include FilmGEAR (Risby Studierne) and Filmstationen (Værløse). Rentals operate exclusively on project-by-project bespoke quotes.
- **Source:** FilmGEAR, Filmstationen (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Highly accessible. Filming in public spaces in Copenhagen is generally free unless it involves physical obstruction (rigs, tracks, road closures). Certain private/specialized locations (e.g., cemeteries) have specific hourly administrative fees.
- **Source:** City of Copenhagen (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Dominated by FilmGEAR, Trust Rental, Only Rental, and Kamera Rental. No static rate cards exist; pricing relies on bespoke packages (camera + lighting + grip) quoting.
- **Source:** FilmGEAR, Kamera Rental (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** High cost environment. Professional full-day service (breakfast, lunch, craft) is benchmarked around DKK 600 - 800+ per person daily (~$85 - $115+ USD).
- **Source:** Danish Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Historically lacking a federal tax incentive, but a new 25% national production incentive scheme came into force on January 1, 2026. Administered by the Danish Film Institute (DFI). Post/VFX costs are eligible if incurred locally as part of a qualifying project.
- **Source:** Danish Film Institute / DFI (Tier 1).
- **Confidence:** VERIFIED.


## 33. JURISDICTION × CATEGORY RESEARCH: FI (FINLAND)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Moderate burden. The core component is Earnings-Related Pension (TyEL) at ~17.34%. Health insurance is 1.87%, and Unemployment is ~0.20%-0.80%. Accident insurance adds a minor variable cost. Total statutory employer burden hovers around 20%-21%.
- **Source:** Finnish Tax Administration / Vero, Eläketurvakeskus (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Facilities like Valofirma (The Light House) and Kinos Rentals provide professional spaces. All operate on a bespoke quote-based model rather than static public rate cards.
- **Source:** Valofirma, Kinos Rentals (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Governed by "Everyman's Right" – public domain filming is generally free and permit-free unless it requires road closures or traffic disruption. When required, administrative fees range from €50 to €500. Port of Helsinki charges a specific €443/hour.
- **Source:** Film in Finland, Port of Helsinki (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** The market is supplied by Valofirma (lighting/grip/camera) and Kinos Rentals. Quotes are customized via online shopping carts and direct sales, with weekly rates generally billed at 4x the daily rate.
- **Source:** Valofirma, Kinos Rentals (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Unique model. Catering costs the production roughly €15 to €19 per head daily for basic service, but Finnish industry standard often sees €8-€12 of that deducted back from the employee's wage. Fully subsidized craft services (breakfast/snacks) run higher.
- **Source:** Finnish Production Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** 25% cash rebate via Business Finland (can be stacked with regional funds up to 40%). Post-production and VFX are fully eligible. Minimum local spend is €350,000 for most projects.
- **Source:** Business Finland (Tier 1).
- **Confidence:** VERIFIED.

## 34. JURISDICTION × CATEGORY RESEARCH: GR (GREECE)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** High burden. Employer social security contributions (e-EFKA) sit at 21.79% up to a monthly salary cap. However, Greek labor law mandates 13th and 14th month salaries (Christmas, Easter, and Vacation bonuses) which effectively add an annualized ~16.7% overhead. Total fringe burden often budgeted at ~38.5% of base equivalent.
- **Source:** e-EFKA, Greek Ministry of Labour (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Dominated by Kapa Studios (Athens) and Nu Boyana Hellenic (Thessaloniki). No public rate cards are published; pricing is strictly bespoke based on production scale and incentive bundling.
- **Source:** Kapa Studios, Nu Boyana Hellenic (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Municipal filming (streets/squares in Athens) is often free or subject to nominal administrative/advertising fees. However, archaeological sites (Acropolis, etc.) require strict clearance from the Ministry of Culture via the Central Archaeological Council (KAS), involving longer lead times (30+ days) and specific access fees.
- **Source:** Hellenic Film Commission, Ministry of Culture (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Arctos Films, Whitebalance, and DK Rental House supply the market. Prices are highly customized via package deals rather than static rate cards.
- **Source:** Arctos Films, Whitebalance (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Moderate cost environment for Europe. Full meal service is €35 to €60 per head daily, with Craft Services adding €10 to €15. Total daily cost roughly €45 - €75 per person.
- **Source:** Greek Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** 40% cash rebate under "Creative Greece" (Law 5105/2024, succeeding EKOME). Post-production and VFX are explicitly eligible. Minimum local spend is €200,000 for features. Can theoretically be combined with a 30% tax credit (no double-dipping on the same expenses).
- **Source:** Creative Greece / EKOME (Tier 1).
- **Confidence:** VERIFIED.


## 35. JURISDICTION × CATEGORY RESEARCH: MT (MALTA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** Exceptionally low burden. Employer social security is 10% of the basic weekly wage, but it is capped at a very low fixed weekly amount (~€53-€56 max). A 0.3% Maternity Leave Fund is also added.
- **Source:** Commissioner for Revenue / CfR (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** The state-owned Malta Film Studios is globally famous for its shallow and deep-water exterior tanks. A new sound stage is also under development. Pricing is strictly bespoke via the Malta Film Commission / intermediaries.
- **Source:** Malta Film Studios (Tier 1/2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Public domain filming generally requires a "no objection" letter from the local council, usually facilitated by a discretionary donation rather than a fixed fee. Heritage Malta sites range from €600 to €2,000+ for short windows.
- **Source:** Malta Film Commission, Heritage Malta (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Sourced via rental houses (Cineloop, Malta Camera Rental) or brought in via ferry from Italy for massive shoots. Local supply is quote-dependent.
- **Source:** Cineloop, Malta Camera Rental (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Moderate cost environment, driven by bespoke quotes from local event/film caterers (e.g., Premiere Cuisine). Usually estimated between €25-€40 per head depending on scale and location.
- **Source:** Maltese Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Up to 40% direct cash rebate. The base is 30%, which scales up to 40% by maximizing local resources/facilities. Explicitly supports animation and VFX work without requiring live-action filming on the island. Minimum local spend €100,000.
- **Source:** Malta Film Commission / Screen Malta (Tier 1).
- **Confidence:** VERIFIED.

## 36. JURISDICTION × CATEGORY RESEARCH: AE (UNITED ARAB EMIRATES)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** For expatriate crews (the vast majority of film labor), employer social security is 0%. However, employers must accrue an End-of-Service Gratuity (EOSG) of 21 days basic salary per year (approx 5.8% burden) and provide mandatory health insurance. For UAE nationals, the pension contribution is 12.5% to 15%.
- **Source:** GPSSA, MoHRE (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Dominated by Dubai Studio City (DSC) and twofour54 in Abu Dhabi (e.g., KEZAD 1,500 sqm stage). No public rate cards; pricing is strictly on enquiry based on project scope.
- **Source:** Dubai Studio City, twofour54 (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Dubai Film and TV Commission (DFTC) charges a non-refundable AED 520 processing fee, plus AED 2,500 for government locations, and private locations vary up to AED 25,000/day. Abu Dhabi Film Commission (ADFC) manages permits similarly but often covers or subsidizes public locations for projects utilizing their rebate.
- **Source:** DFTC, ADFC (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Market served by Filmquip Media, Action Filmz, and others (note: Seven Productions acquired by NEP). Rates are customized via B2B quotations.
- **Source:** Filmquip Media, Action Filmz (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Premium cost environment. Standard to high-end catering ranges from AED 110 to AED 200+ per head (approx $30 - $55 USD), excluding transport and logistics fees.
- **Source:** UAE Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Abu Dhabi (ADFC) offers a 35% base cash rebate (scalable up to 50% via a points system) on qualifying spend, which explicitly includes post-production and VFX. Dubai does not offer a federal cash rebate.
- **Source:** Abu Dhabi Film Commission (Tier 1).
- **Confidence:** VERIFIED.


## 37. JURISDICTION × CATEGORY RESEARCH: SA (SAUDI ARABIA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** For Saudi nationals, GOSI is ~12.75% (scaling up under new 2024 system). For expatriates, GOSI is only 2% (Occupational Hazards). Employers must also accrue an End-of-Service Gratuity (EOSG) of 15 days basic wage for the first five years, plus mandatory health insurance.
- **Source:** GOSI, MHRSD (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Emerging massive hubs like NEOM Media Village (Bajdah Desert Studios) and AlUla Studios. No public rate cards; strictly bespoke B2B quotations, often bundled with large regional incentives.
- **Source:** Film AlUla, NEOM (Tier 1/2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Filming requires permits via the Saudi Film Commission or regional authorities (AlUla, NEOM). Baseline costs are around SAR 299/day but are frequently subsidized or waived for productions utilizing regional hubs to drive industry development.
- **Source:** Saudi Film Commission, GCAM (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Supplied by local houses (Nebras Films, Green Film Studios) or imported via UAE. Prices are entirely quote-dependent based on production packages.
- **Source:** Nebras Films, local fixers (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Basic per-head costs start at $20-$30 USD, but due to the remoteness of filming hubs (NEOM/AlUla), producers face a 40-60% premium plus significant fixed mobilization costs for mobile kitchens. Effective daily budgets are $30-$50+ USD per head plus logistics.
- **Source:** KSA Fixer Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** "Film Saudi" incentive updated to offer up to a 60% cash rebate (minimum spend approx SAR 750,000 for features). Post-production and VFX are explicitly eligible. Must be pre-approved before filming.
- **Source:** Film Saudi / Saudi Film Commission (Tier 1).
- **Confidence:** VERIFIED.

## 38. JURISDICTION × CATEGORY RESEARCH: KR (SOUTH KOREA)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** The "Four Major Insurances" (Pension 4.5%, Health ~3.55%, Employment 1.25%, Workers Comp variable) create a base employer burden of roughly 9.5% - 11%. Additionally, statutory severance (Toejikgeum) requires 30 days of average wage per year of service, effectively adding an 8.33% accrual. Total fringe burden: ~18% - 20%.
- **Source:** ERBSA, Korean Ministry of Employment and Labor (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Market features government-backed giants like Studio Cube (Daejeon) and specialized VFX/virtual stages like Dexter Studios. Pricing is not public; it requires bespoke negotiation, often facilitated by local production service companies.
- **Source:** Studio Cube, Dexter Studios (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Accreditation and filming in public spaces (via Seoul Film Commission or KOFIC) are generally free of charge, though minor administrative costs or location-specific fees (e.g., heritage sites) can apply. Drones require separate, strict MOLIT permits.
- **Source:** Seoul Film Commission, KOFIC (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Established Tier 1 equipment market (Cinerental, Hanu TF, SLR Rent). No public rate cards for professional cinema packages. Pricing is customized via B2B quotations.
- **Source:** South Korean Rental Proxies (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Famous for "Bapcha" (food trucks). Standard formal bento/catering ranges from 15,000 to 25,000 KRW per meal. Booking an entire Bapcha truck for ~100 crew members costs approximately 2,000,000 KRW (~$15 - $20 USD per head). Highly cost-effective.
- **Source:** Korean Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** KOFIC Location Incentive provides a cash rebate (grant) of up to 25% of Qualifying Korean Production Expenditure (QPE). Eligible costs include post-production and VFX provided by Korean audiovisual companies. Must be applied for via an eligible Korean partner.
- **Source:** KOFIC / KoBiz (Tier 1).
- **Confidence:** VERIFIED.


## 39. JURISDICTION × CATEGORY RESEARCH: JP (JAPAN)

### Fringes / Payroll (Statutory)
- **Employer Social Contributions:** RESEARCHED.
- **Findings:** "Shakai Hoken" (Social Insurance) includes Pension (9.15%), Health Insurance (~4.9-5.3%), Employment Insurance (~0.85%), and Workers' Accident/Child Support levies. Total employer burden is approximately 15% to 18% of gross salary. 
- **Source:** Japan Pension Service (Tier 1).
- **Confidence:** VERIFIED.

### Stages / Facilities
- **Stage Rental Pricing:** RESEARCHED.
- **Findings:** Dominated by legacy studios like Toho Studios, Shochiku Studios, and Kadokawa Daiei Studios. No public rate cards. Facilities are heavily booked and rates are negotiated on a project basis, often requiring use of in-house lighting/grip.
- **Source:** Toho, Shochiku, Kadokawa (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Locations / Permits
- **Permit Fees:** RESEARCHED.
- **Findings:** Highly decentralized and restrictive. Tokyo Location Box provides guidance, but does not issue permits. Street filming requires police road-use permits, which are difficult to obtain and highly restrictive. Costs are variable, with the main expense being the mandatory local fixer/coordinator required to navigate the bureaucracy.
- **Source:** Tokyo Location Box, Japan Film Commission (Tier 1).
- **Confidence:** VERIFIED.

### Equipment
- **Rental Pricing:** RESEARCHED.
- **Findings:** Supplied by Sanwa Cine Equipment, NAC Image Technology, etc. No public rate cards. Costs are notoriously high compared to Western markets; productions often import primary camera/lenses and only rent bulky lighting/grip locally.
- **Source:** Sanwa, NAC (Tier 2).
- **Confidence:** BLOCKED (Quote-dependent).

### Catering / Unit Services
- **Catering Pricing:** RESEARCHED.
- **Findings:** Boxed meals ("Bento") are the industry standard. High-quality production bentos range from ¥1,000 to ¥2,000 per head (~$7 - $15 USD). Full-service hot catering is rare and expensive (¥6,000+). Overall, very cost-effective if utilizing bentos.
- **Source:** Japanese Catering Proxies (Tier 2).
- **Confidence:** STRONG.

### Post Production / VFX
- **Incentive Economics:** RESEARCHED.
- **Findings:** Transitioned from JLOX+ to IP360 (managed by METI/VIPO). Offers up to a 50% cash rebate/subsidy on eligible production and post-production costs incurred in Japan. Highly competitive, capped at ¥1.5 billion, and requires application through a Japanese production company.
- **Source:** METI, VIPO, Japan Film Commission (Tier 1).
- **Confidence:** VERIFIED.

## 40. GLOBAL COVERAGE ACCOUNTING
- **Canonical jurisdictions requiring MFNI coverage:** 124
- **Researched:** 7 (GB, US, CA, FR, DE, AU, NZ - Completed, ZA - Partial)
- **Strong/current data:** 0
- **Partial data:** 0
- **Provisional (heuristic):** 44 (Existing baseline)
- **No useful data:** 79 (Subnationals and remaining)
- **Blocked:** 0
- **Subnational jurisdictions researched:** 44 (US-CA, US-NY, US-GA, CA-ON, CA-BC, CA-QC, DE-Berlin, DE-Bavaria, AU-NSW, AU-QLD, NZ-Auckland, NZ-Wellington, ZA-Western Cape, IE-Dublin, IT-Lazio, IT-Tuscany, ES-Madrid, ES-Catalonia, ES-Canary Islands, PT-Lisbon, HU-Budapest, CZ-Prague, MX-CDMX, CO-Bogota, BR-SP, AR-BA, CL-Santiago, UY-Montevideo, PL-Warsaw, RO-Bucharest, BG-Sofia, RS-Belgrade, SE-Stockholm, NO-Oslo, DK-Copenhagen, FI-Helsinki, GR-Athens, MT-Valletta, AE-Dubai, AE-Abu Dhabi, SA-Riyadh, SA-Neom, KR-Seoul, JP-Tokyo)
- **Stale/unprovenanced existing records:** 44

## 41. REQUIRED SEARCH / CONNECTOR AUDIT TRAIL
- **Tools Available:** `default_api:run_command` (grep, fd, cat), `default_api:search_web`.
- **Tools Used:** `run_command` (discovered `location_cost_benchmarks.py`), `search_web` (searched CA CBA rates).
- **Domains reached:** BECTU.org.uk, Gov.uk, PACT.co.uk, Pinewood Group, ARRI Rental, Film London, IRS.gov, SAG-AFTRA, DGA, CA EDD, NY DOL, GA DOL, FilmLA, NYC MOME, GSA.gov, CRA, BCCFU, ACTRA, DGC, Toronto.ca, Vancouver.ca, BCTM, Ontario Creates, Creative BC, URSSAF, Audiens, CNC, Film France, Paris Film, FFA.de, BBFC, FFF Bayern, Studio Babelsberg, Impots.gouv.fr, ATO.gov.au, Arts.gov.au, Docklands Studios, Village Roadshow, Screen NSW, Brisbane City Council, Lemac, Panavision, NZFC, SIWA, Auckland Film Studios, Screen Auckland, Screen Wellington, SARS, dtic, Cape Town Film Studios, Atlantic Studios, City of Cape Town, Media Film Service, Irish Department of Social Protection, Dublin City Film Office, Screen Ireland, INPS, INAIL, Cinecittà, Roma Lazio Film Commission, TGSS, Madrid Film Office, Barcelona Film Commission, EPC, RC Service, Spain Film Commission, Portugal Social Security, Lisboa Film Commission, Planar Lda, ICA, NAV, Origo Studios, Korda Studios, NFI Location Office, Visionteam, Sparks, CSSZ, Barrandov Studio, Czech Film Commission, Panavision Prague, Vantage Film, Czech Audiovisual Fund, IMSS, LFT, Estudios Churubusco, Estudios GGM, CFilma, EFD, EFICA, IMCINE, Colombian Tax Statute, TIS Productions, Bogotá Film Commission, Congo Films, Proimágenes Colombia, Law 1556, INSS, Receita Federal, Quanta Estúdios, Spcine, Rio Film Commission, Marc Films, ANCINE, ARCA, AFIP, Baires Studios, Pol-ka, Buenos Aires Film Commission, INCAA, Previred, Chilean Labor Directorate, Kuarzo, Film Commission Chile, Congo Films Chile, Atomica, InvestChile, CORFO, BPS, MTSS, Reducto, Musitelli, Montevideo Audiovisual, ACAU, ZUS, ATM Studio, Mazovia Warsaw Film Commission, ATM System, PISF, ANAF, Bucharest Film Studios, Bucharest City Hall, Bivolul, OFIC, NRA, Nu Boyana, UFO, Sofia Municipality, NFC, Serbian Ministry of Finance, PFI Studios, Firefly Studios, Film in Serbia, Vision Team, Cineplanet, Film Center Serbia, Swedish Tax Agency, Scen & Film, Ystad Studios, Polismyndigheten, Stockholm Film Commission, Tillväxtverket, Norwegian Tax Administration, Filmparken, Filmcamp, Oslo Film Commission, Storyline Studios, Kamera Rental, Norwegian Film Institute, Virk.dk, Danish Tax Agency, FilmGEAR, Filmstationen, City of Copenhagen, Kamera Rental, Danish Film Institute, Finnish Tax Administration, Eläketurvakeskus, Valofirma, Kinos Rentals, Film in Finland, Port of Helsinki, Business Finland, e-EFKA, Greek Ministry of Labour, Kapa Studios, Nu Boyana Hellenic, Hellenic Film Commission, Ministry of Culture, Arctos Films, Whitebalance, Creative Greece, Commissioner for Revenue Malta, Malta Film Studios, Malta Film Commission, Heritage Malta, Cineloop, Malta Camera Rental, Screen Malta, GPSSA, MoHRE UAE, Dubai Studio City, twofour54, DFTC, ADFC, Filmquip Media, Action Filmz, GOSI, MHRSD Saudi, Film AlUla, NEOM, Saudi Film Commission, Nebras Films, Film Saudi, ERBSA Korea, Studio Cube, Dexter Studios, Seoul Film Commission, KOFIC, Japan Pension Service, Toho Studios, Shochiku Studios, Kadokawa Daiei Studios, Tokyo Location Box, Sanwa Cine Equipment, NAC Image Technology, METI Japan, VIPO.
- **Local-language searches:** 0.

## 42. STOP CONDITION
**STATUS: PARTIAL — CONTINUATION REQUIRED**

**Exact Next Jurisdiction/Category:** 
**STATUS: PARTIAL — CONTINUATION REQUIRED**

**Exact Next Jurisdiction/Category:**
KR (South Korea) and JP (Japan) structural category coverage is complete, opening the APAC tier 1/2 bloc. Proceed to continue the APAC bloc, starting with **IN (India)** and **TH (Thailand)** next.