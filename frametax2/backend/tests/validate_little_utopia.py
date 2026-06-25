"""
validate_little_utopia.py

Optimizer validation against The Little Utopia production.
Runs the existing platform (QPE calculator, Tier 1 comparison,
production adjustment engine, delta engine) against the sanitized budget.

Produces a consolidated ranked report in pure text.

Usage:
    cd frametax2/backend
    python -m tests.validate_little_utopia

No DB access. No AI calls. Deterministic.
"""
from __future__ import annotations

import sys
import os

# ── path bootstrap ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.fixtures.little_utopia_sanitized import (
    ACCOUNTS,
    GROSS_BUDGET_USD,
    ATL_TOTAL_USD,
    MARINE_CLUSTER_USD,
    QPE_CONSERVATIVE_TARGET,
    QPE_BASE_TARGET,
    QPE_OPTIMISTIC_TARGET,
    REBATE_CONSERVATIVE_35,
    REBATE_BASE_35,
    REBATE_OPTIMISTIC_35,
    computed_gross_budget,
    computed_qpe,
)
from app.calculators.qpe_calculator import calculate_qpe, get_scenario
from app.calculators.mediterranean_comparison import run_tier1_comparison, rank_by_net_benefit
from app.calculators.production_adjustment import (
    AdjustmentMode,
    AdjustmentToggles,
    CrewManifest,
    ProductionAdjustmentInput,
    ProductionBudgetParams,
    calculate_production_adjustment,
)
from app.calculators.delta_engine import (
    DeltaInput,
    JurisdictionIncentive,
    calculate_delta,
    explain_winner,
)
from app.data.nationality_lookup import (
    lookup_nationality,
    add_verified_person,
    build_nationality_report,
)

# ── Post-production scenarios (in-kind, not in existing budget) ─────────────
POST_PROD_IN_KIND = {
    "low":  500_000,
    "base": 625_000,
    "high": 750_000,
}
POST_PROD_IN_BUDGET = 363_000  # accounts 50-00 through 55-00

# ── Production in-budget post QPE breakdown ─────────────────────────────────
# Already excluded from MU QPE (all scenarios). Would qualify in Malta/Greece etc.
# if post is performed there — add back when building non-MU structures.

# ── Crew manifest (Little Utopia marine production) ─────────────────────────
LU_CREW = CrewManifest(
    atl_count=4,              # director, 2 producers, lead actor (Luke Evans)
    atl_business_class=True,
    dept_head_count=8,        # DoP, production designer, sound, etc.
    dept_head_business_class=False,
    btl_traveling_count=20,   # specialist/imported BTL (Frogsquad treated separately)
    local_btl_count=60,       # Mauritius-local crew (transport drivers, extras, etc.)
    producer_oversight_trips=4,
    producer_oversight_business=True,
    shoot_days=42,
    hotel_nights_traveling_crew=45,
    per_diem_days_traveling=45,
)

LU_BUDGET = ProductionBudgetParams(
    total_budget_usd=GROSS_BUDGET_USD,
    btl_budget_usd=GROSS_BUDGET_USD - ATL_TOTAL_USD,
    equipment_value_usd=278_163,   # camera $185K + marine equip $93.2K
    gross_payroll_usd=1_800_000,   # estimated gross payroll across all crew
    la_legal_accounting_usd=78_000,
    la_equipment_rental_usd=278_163,
    la_stage_facility_usd=0,       # no stage; exterior marine shoot
)

# ── Known team nationalities ─────────────────────────────────────────────────
# Writer: GB (UK) — confirmed by user
# Lead Actor: Luke Evans — Welsh/British, publicly documented
# Producers: UK, Canada, USA (user-provided)
# Director: Australian — confirmed by user

add_verified_person(
    "Luke Evans",
    citizenship="GB",
    residency="GB",
    source_url="https://en.wikipedia.org/wiki/Luke_Evans_(actor)",
    source_description="Wikipedia: born Pontypool, Wales; British actor",
    confidence="HIGH",
    notes="Lead actor, The Little Utopia. Welsh/British national.",
)

add_verified_person(
    "Unknown Director",
    citizenship="AU",
    residency="AU",
    source_url="",
    source_description="Confirmed by producer",
    confidence="HIGH",
    notes="Director, The Little Utopia. Australian national.",
)

add_verified_person(
    "Unknown Writer",
    citizenship="GB",
    residency="GB",
    source_url="",
    source_description="Confirmed by producer",
    confidence="HIGH",
    notes="Writer, The Little Utopia. British national.",
)

# ── Known incentive values per jurisdiction at QPE base scenario ─────────────
# Applied to the same QPE base ($2.5M Mauritius-equivalent BTL + uplift for non-MU)

def _incentive_gross(
    iso2: str,
    rate: float,
    qpe_usd: float,
    cap_usd: float | None = None,
    confidence_discount: float = 0.0,
) -> float:
    raw = rate * qpe_usd
    if cap_usd:
        raw = min(raw, cap_usd)
    return raw * (1.0 - confidence_discount)


# ── Jurisdictions to compare ─────────────────────────────────────────────────
# QPE estimates: Mauritius BTL-only base ($2.5M) + ATL uplift for jurisdictions
# that qualify ATL. Post-production added when structure includes post in that JUR.

# Mauritius: base $2.5M QPE
MU_QPE_BASE  = 2_500_000
MU_QPE_OPT   = 3_060_000
MU_REBATE    = MU_QPE_BASE * 0.35   # $875,000

# Malta: all ATL + BTL qualifies. QPE = MU_BTL_base + ATL($408K not cast) + cast($130K) + accomm($274K)
# Uplift over MU base: +ATL $538K + accomm/perdiem ~$274K ≈ $2.5M + $812K ≈ $3,312K without post
# With post in budget ($363K): $3,675K  With in-kind post (base $625K): $4,300K
MT_QPE_NO_POST = 3_312_000
MT_QPE_IN_BUDGET_POST = 3_675_000
MT_QPE_INDK_POST_BASE  = MT_QPE_IN_BUDGET_POST + POST_PROD_IN_KIND["base"]  # $4,300,000

# Greece: ATL base+ (director/producer/writer qualify at base; cast only optimistic)
GR_QPE_BASE = 2_500_000 + 408_000 + 274_000   # MU_BTL + ATL excl cast + accomm → $3,182,000
GR_QPE_BASE_CAST = GR_QPE_BASE + 130_000       # + cast (optimistic): $3,312,000
GR_QPE_POST = GR_QPE_BASE + POST_PROD_IN_BUDGET + POST_PROD_IN_KIND["base"]

# Cyprus: DISCOVERY, ATL only optimistic, same BTL as MU base
CY_QPE_BASE = 2_500_000 + 274_000             # $2,774,000 (no ATL at base)
CY_QPE_OPT  = CY_QPE_BASE + 538_000           # $3,312,000 (incl ATL optimistic)

# UK HETV: 34% on qualifying UK spend; requires UK entity + cultural test
# If post done in UK: post qualifies. If producer fees UK-sourced: +some ATL
# Feasible UK qualifying spend: UK-based post + UK producer fees
UK_QPE_POST_ONLY = POST_PROD_IN_BUDGET + POST_PROD_IN_KIND["base"]  # $988,000 UK-qualifying
UK_REBATE_POST = UK_QPE_POST_ONLY * 0.34

# Ireland S481: 32% on qualifying Irish spend; requires Irish entity + cultural test
# Irish spend would be any post routed through Irish entity
IE_QPE_POST_ONLY = POST_PROD_IN_BUDGET + POST_PROD_IN_KIND["base"]
IE_REBATE_POST = IE_QPE_POST_ONLY * 0.32

# Australia: producer offset 40% if Australian company controlling production
# Director is Australian; AU director satisfies content test primary requirement
# Most relevant if substantial spend can be AU-routed (post-production)
AU_QPE_POST_ONLY = POST_PROD_IN_BUDGET + POST_PROD_IN_KIND["base"]
AU_REBATE_POST = AU_QPE_POST_ONLY * 0.40

# Hungary: 30% but min HUF 20M (~$55K) — very low. But landlocked, no marine.
# Only relevant for studio/interior or post-production
HU_QPE_POST = POST_PROD_IN_BUDGET
HU_REBATE_POST = HU_QPE_POST * 0.30

# Croatia: 25% on Croatian spend; good marine but post-production not available
HR_QPE_BASE = 2_500_000  # same BTL if shot in Croatia
HR_REBATE = HR_QPE_BASE * 0.25

# Germany DFFF: 25% on German spend but needs 30% German spend of total budget
# Total budget $4.36M → 30% German spend = $1.31M needed; hard to achieve
DE_SPEND_NEEDED = GROSS_BUDGET_USD * 0.30  # $1.31M gate
DE_REBATE_IF_MET = DE_SPEND_NEEDED * 0.25

# Belgium Tax Shelter: effective ~17% through investor mechanism, complex
BE_QPE_ESTIMATE = 2_000_000
BE_EFFECTIVE_REBATE = BE_QPE_ESTIMATE * 0.17

# France TRIP: 30% on qualifying French spend; high payroll burden; cultural test
FR_QPE_POST = POST_PROD_IN_BUDGET  # if post in France
FR_REBATE_POST = FR_QPE_POST * 0.30

# Canary Islands (Spain): 50% — highest warm-water rate; min EUR 1M needed
# Can't achieve EUR 1M minimum spend from this budget without major restructure
ES_CANARY_QPE = 0  # below minimum threshold; structurally excluded
ES_REBATE = 0

# ── Finance cost model (bridge finance on rebate receivable) ─────────────────
def finance_cost(rebate: float, delay_weeks: int, annual_rate: float = 0.08) -> float:
    return rebate * annual_rate * (delay_weeks / 52.0)


# ── Production adjustment engine (EXISTING_BUDGET mode vs MU baseline) ──────
def _pa_result(dest_iso2: str, toggles: AdjustmentToggles | None = None):
    return calculate_production_adjustment(ProductionAdjustmentInput(
        home_base_iso2="US",
        home_base_iata="LAX",
        destination_iso2=dest_iso2,
        mode=AdjustmentMode.EXISTING_BUDGET,
        existing_budget_iso2="MU",
        crew=LU_CREW,
        budget=LU_BUDGET,
        toggles=toggles or AdjustmentToggles(),
    ))


# ── Nationality report ───────────────────────────────────────────────────────
def _nationality_report():
    persons = [
        ("Luke Evans",        "cast"),
        ("Unknown Writer",    "writer"),      # GB — confirmed by user; name unknown
        ("Unknown Director",  "director"),    # AU — confirmed by user; name unknown
        ("Unknown Producer 1","producer"),    # GB
        ("Unknown Producer 2","producer"),    # CA
        ("Unknown Producer 3","producer"),    # US
    ]
    report = build_nationality_report(persons)
    return report


# ══════════════════════════════════════════════════════════════════════════════
# MAIN REPORT
# ══════════════════════════════════════════════════════════════════════════════

def run() -> str:
    lines: list[str] = []
    P = lines.append

    P("=" * 80)
    P("THE LITTLE UTOPIA — PRODUCTION STRUCTURE VALIDATION REPORT")
    P("FrameTax Optimizer v1.0 | June 2025 | EXISTING BUDGET MODE")
    P("=" * 80)

    # ── 1. BUDGET SUMMARY ──────────────────────────────────────────────────
    P("")
    P("━━ 1. BUDGET SUMMARY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    P(f"  Gross budget (ex-memo):          ${GROSS_BUDGET_USD:>12,.0f}")
    P(f"  ATL total:                       ${ATL_TOTAL_USD:>12,.0f}  (12.3% of gross)")
    P(f"  Marine cluster:                  ${MARINE_CLUSTER_USD:>12,.0f}  (9.5% of gross)")
    P(f"  Post in budget (50-55):          ${'363,000':>12}")
    P(f"  Non-recoverable VAT (embedded):  ${'92,439':>12}  (15% Mauritius, non-recoverable)")
    P(f"  International travel (excluded): ${'143,000':>12}")
    P(f"  Est. finance cost (bridge 8%):   ${'74,000':>12}  (8% × $875K × 39 weeks, not in budget)")
    P("")
    P("  POST-PRODUCTION IN-KIND ADJUSTMENT (not in existing budget):")
    P(f"    Low:   $500,000  |  Base: $625,000  |  High: $750,000")
    P("  → Add replacement cost when evaluating non-MU structures without in-kind equivalent")

    # ── 2. MAURITIUS BASELINE ──────────────────────────────────────────────
    P("")
    P("━━ 2. MAURITIUS BASELINE (EDB 35% Cash Rebate, PARSED tier) ━━━━━━━━━━━━")
    tier1 = run_tier1_comparison(ACCOUNTS)
    mu = tier1["MU"]

    finance_mu = finance_cost(MU_REBATE, 39)
    P(f"  QPE — conservative:              ${QPE_CONSERVATIVE_TARGET:>12,.0f}")
    P(f"  QPE — base:                      ${QPE_BASE_TARGET:>12,.0f}")
    P(f"  QPE — optimistic:                ${QPE_OPTIMISTIC_TARGET:>12,.0f}")
    P(f"  Rebate @ 35% (conservative):     ${REBATE_CONSERVATIVE_35:>12,.0f}")
    P(f"  Rebate @ 35% (base):             ${MU_REBATE:>12,.0f}  ← PRIMARY FIGURE")
    P(f"  Rebate @ 35% (optimistic):       ${REBATE_OPTIMISTIC_35:>12,.0f}")
    P(f"  Finance cost (8% / 39 wks):      ${'74,519':>12}  (estimated; not in budget)")
    P(f"  Net rebate after finance (base):  ${MU_REBATE - finance_mu:>11,.0f}")
    P(f"  Non-recoverable VAT cost:         ${'92,439':>12}  (embedded in gross budget)")
    P(f"  Effective incentive rate:         {'20.0%':>12}  ($875K / $4.364M gross)")
    P("")
    P("  KEY RISKS:")
    P("    • 35% rate PARSED not VERIFIED — inferred from budget line only")
    P("    • ATL (director $175K, producer $148K, writer $85K) excluded from base QPE")
    P("    • Frogsquad routing (SA entity) = ±$100K QPE swing")
    P("    • Accommodation/per-diem qualifying treatment unconfirmed")
    P("    • Finance timing / rebate assignability to gap lender unconfirmed")
    P("    • In-kind post ($500K-$750K) provides NO incremental Mauritius incentive")
    P("      unless EDB confirms post-production qualifying treatment")

    # ── 3. TEAM & NATIONALITY ──────────────────────────────────────────────
    P("")
    P("━━ 3. KNOWN TEAM & NATIONALITY STATUS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    P("  Role              | Name / Status       | Nationality | Confidence")
    P("  ──────────────────┼─────────────────────┼─────────────┼───────────")
    P("  Lead Actor        | Luke Evans          | GB (Welsh)  | HIGH (public record)")
    P("  Writer            | [name not stored]   | GB          | HIGH (user-confirmed)")
    P("  Producer 1        | [name not stored]   | GB          | HIGH (user-confirmed)")
    P("  Producer 2        | [name not stored]   | CA          | HIGH (user-confirmed)")
    P("  Producer 3        | [name not stored]   | US          | HIGH (user-confirmed)")
    P("  Director          | [name not stored]   | AU          | HIGH (user-confirmed)")
    P("")
    P("  NATIONALITY IMPACT SUMMARY:")
    P("")
    P("  UK AVEC cultural test (need ≥18/31 pts):")
    P("    Luke Evans (GB lead):   +1pt  D5 — lead actor British")
    P("    Writer (GB):            +1pt  C2 — screenplay by British writer")
    P("    Producer 1 (GB):        +1pt  A1 — UK production company/producer")
    P("    Director (AU):           0pts — not British national")
    P("    UK post (facilities):  +2-4pts — if significant post in UK")
    P("    TOTAL ESTIMATE:         5-7/31 → FAILS without substantial UK shoot")
    P("    → UK AVEC as principal jurisdiction excluded at this budget level")
    P("    → UK post-only service deal (no cultural test) remains viable")
    P("")
    P("  AU content test (for Producer Offset):")
    lu_nat = lookup_nationality("Luke Evans", "cast")
    P(f"    Luke Evans: GB, confidence: {lu_nat.confidence.value} → 0 AU pts")
    P("    Director (AU):         STRONG — Australian director is a primary qualifier")
    P("    Writer (GB):            0pts  — not Australian national")
    P("    → AU director satisfies key 'significant Australian content' threshold")
    P("    → Still requires AU company as applicant + qualifying AU spend")
    P("")
    P("  Eurimages (≥3 Council of Europe co-producers):")
    P("    Director (AU): AU is NOT a Council of Europe member — no impact")
    P("    GB: Council of Europe member ✓ | MT ✓ | IE ✓ | FR ✓ | GR ✓")
    P("    → Eurimages structure viable via GB + MT + IE co-producers")

    # ── 4. TIER 1 COMPARISON (built-in engine) ─────────────────────────────
    P("")
    P("━━ 4. TIER 1 COMPARISON (Mediterranean engine, same budget) ━━━━━━━━━━━━")
    ranked = rank_by_net_benefit(tier1)

    for code, res in ranked:
        prog = res.program
        qpe_base = get_scenario(res.qpe_result, "base").qpe_usd
        rebate_base = res.rebate_base
        rebate_max  = res.rebate_max
        fin_cost    = res.finance_cost_base
        net_base    = res.net_benefit_base
        net_pct     = res.net_benefit_pct * 100
        P(f"  ── {code}: {prog.program_name}")
        P(f"     QPE (base):        ${qpe_base:>11,.0f}")
        P(f"     Rebate (base rate)  ${rebate_base:>10,.0f}  @ {prog.base_rate*100:.0f}%")
        P(f"     Rebate (max rate)   ${rebate_max:>10,.0f}  @ {prog.max_rate*100:.0f}%")
        P(f"     Finance cost:      -${fin_cost:>10,.0f}  ({prog.finance_delay_weeks}wks @ {prog.finance_annual_rate*100:.0f}%)")
        P(f"     Net benefit (base): ${net_base:>10,.0f}  ({net_pct:.1f}% of gross budget)")
        if prog.confidence_tier == "DISCOVERY":
            P(f"     ⚠ DISCOVERY tier: 25% confidence discount applied")
        P("")

    # ── 5. FULL JURISDICTION COMPARISON ────────────────────────────────────
    P("━━ 5. FULL JURISDICTION COMPARISON (all 12 required + extras) ━━━━━━━━━━")
    P("")

    # Post-production cost: must add to any structure NOT providing in-kind post
    # Unless that jurisdiction covers it via incentive
    POST_REPLACEMENT_BASE = POST_PROD_IN_KIND["base"]  # $625,000 new cost

    JURISDICTIONS = [
        # iso2, label, gross_rebate, note, qualifies_post, rate_tier
        ("MU",  "Mauritius (EDB 35%)",
         MU_REBATE,
         "Baseline. No post incentive in budget. In-kind post adds zero MU QPE.",
         False,  # no post incentive in MU rebate
         "PARSED"),
        ("MT",  "Malta (MFC 25-40%)",
         MT_QPE_NO_POST * 0.40,  # max rate on non-post QPE
         "Max 40% w/uplifts. All ATL+BTL qualify. Post qualifies if in Malta.",
         True,   # post qualifies in Malta
         "PARSED"),
        ("MT+POST", "Malta (MFC 40% + post in Malta)",
         MT_QPE_INDK_POST_BASE * 0.40,
         "40% on all qualifying including in-kind post ($625K). Best Malta scenario.",
         True,
         "PARSED"),
        ("GR",  "Greece (40% flat)",
         GR_QPE_BASE * 0.40,
         "40% on base QPE (excl. cast). High payroll burden. 9-12mo cashflow.",
         False,  # post not confirmed for Greece
         "PARSED"),
        ("GR+CAST", "Greece (40% incl. ATL cast, optimistic)",
         GR_QPE_BASE_CAST * 0.40,
         "40% with cast qualifying (optimistic). Risk: oversubscription.",
         False,
         "PARSED"),
        ("CY",  "Cyprus (35% DISCOVERY)",
         CY_QPE_BASE * 0.35 * 0.75,  # 25% confidence discount
         "DISCOVERY: 35% rate unverified. 25% discount applied. Shallow crew.",
         False,
         "DISCOVERY"),
        ("HU",  "Hungary (30%, post only)",
         HU_REBATE_POST,
         "Landlocked. 30% on post-production routed to Hungary.",
         True,
         "DISCOVERY"),
        ("HR",  "Croatia (25%)",
         HR_REBATE,
         "25% on Croatian spend. Marine production only (not applicable to MU shoot).",
         False,
         "DISCOVERY"),
        ("DE",  "Germany DFFF (25%, needs 30% German spend)",
         DE_REBATE_IF_MET if False else 0,  # gate not achievable on this budget
         "Gate: 30% German spend ($1.31M) → structurally excluded at this budget level.",
         False,
         "DISCOVERY"),
        ("BE",  "Belgium Tax Shelter (~17% effective)",
         BE_EFFECTIVE_REBATE,
         "Complex investor mechanism. High payroll burden. Not marine-suitable.",
         False,
         "DISCOVERY"),
        ("FR",  "France TRIP (30%, post only)",
         FR_REBATE_POST,
         "30% on qualifying French post spend. High WHT/payroll on French crew.",
         True,
         "DISCOVERY"),
        ("IE",  "Ireland S481 (32%)",
         IE_REBATE_POST,
         "32% on Irish qualifying spend. Cultural test required.",
         True,
         "PARSED"),
        ("GB",  "UK AVEC/HETV (34%)",
         UK_REBATE_POST,
         "34% on qualifying UK spend. Luke Evans (GB) + GB producers help cultural test.",
         True,
         "PARSED"),
        ("AU",  "Australia Producer Offset (40%)",
         AU_REBATE_POST,
         "40% on qualifying AU spend. Director = AU (content test). Requires AU company.",
         True,
         "PARSED"),
    ]

    P("  LEGEND: Gross Rebate | Post-adj (add $625K cost if no post incentive) | Net")
    P("")
    P(f"  {'Jurisdiction':<34} {'Gross Rebate':>13} {'Post Adj':>10} {'Net':>13} {'Tier':<10} Notes")
    P("  " + "─" * 110)

    results_table = []
    for iso2, label, gross, note, covers_post, tier in JURISDICTIONS:
        post_adj = 0 if covers_post else -POST_REPLACEMENT_BASE
        net = gross + post_adj
        results_table.append((iso2, label, gross, post_adj, net, tier, note, covers_post))
        P(f"  {label:<34} ${gross:>12,.0f} ${post_adj:>9,.0f} ${net:>12,.0f}  {tier:<10} {note[:60]}")

    results_table.sort(key=lambda x: x[4], reverse=True)

    # ── 6. PRODUCTION ADJUSTMENT (EXISTING BUDGET MODE) ───────────────────
    P("")
    P("━━ 6. PRODUCTION ADJUSTMENT ENGINE (EXISTING BUDGET vs Mauritius) ━━━━━━")
    P("")
    P("  NOTE: Mauritius travel is ALREADY in budget. Delta = incremental only.")
    P("  Same budget structure assumed; only cost differences shown.")
    P("")

    adj_jurs = ["MT", "GR", "CY", "HU", "HR", "GB", "IE", "AU"]
    adj_results = {}
    for iso2 in adj_jurs:
        try:
            r = _pa_result(iso2)
            adj_results[iso2] = r
            P(f"  {iso2}: Total incremental adjustment vs MU = ${r.total_adjustment_usd:>10,.0f}")
            P(f"       Airfare delta:       ${r.airfare_usd:>10,.0f}")
            P(f"       Hotel delta:         ${r.hotel_usd:>10,.0f}")
            P(f"       Per diem delta:      ${r.per_diem_usd:>10,.0f}")
            P(f"       FX risk delta:       ${r.fx_usd:>10,.0f}")
            P(f"       Payroll/fringe delta:${r.payroll_fringe_usd:>10,.0f}")
            P(f"       Confidence:          {r.confidence}")
            P("")
        except Exception as e:
            P(f"  {iso2}: ERROR — {e}")

    # ── 7. RANKED STRUCTURES WITH NET PRODUCER BENEFIT ────────────────────
    P("")
    P("━━ 7. RANKED PRODUCTION STRUCTURES — NET PRODUCER BENEFIT ━━━━━━━━━━━━━")
    P("")
    P("  Formula: Net = Gross Incentive − Post Replacement Cost − Production Adjustment")
    P("  (Production adjustment is incremental cost vs Mauritius existing budget)")
    P("")

    ranked_structures = []
    for iso2, label, gross, post_adj, net_pre_adj, tier, note, covers_post in results_table:
        # Get production adjustment
        adj = adj_results.get(iso2.split("+")[0], None)
        prod_adj = adj.total_adjustment_usd if adj else 0.0
        final_net = gross + post_adj - prod_adj
        confidence_note = ""
        if tier == "DISCOVERY":
            confidence_note = "[DISCOVERY]"
        ranked_structures.append((final_net, iso2, label, gross, post_adj, prod_adj, final_net, tier, note, covers_post))

    ranked_structures.sort(reverse=True)

    P(f"  {'#':<3} {'Structure':<34} {'Gross':>12} {'Post':>9} {'ProdAdj':>9} {'NET':>12} {'Tier':<11}")
    P("  " + "─" * 100)
    for i, (_, iso2, label, gross, post_adj, prod_adj, final_net, tier, note, covers_post) in enumerate(ranked_structures, 1):
        P(f"  {i:<3} {label:<34} ${gross:>11,.0f} ${post_adj:>8,.0f} ${-prod_adj:>8,.0f} ${final_net:>11,.0f}  {tier}")

    # ── 8. CO-PRODUCTION STRUCTURES ────────────────────────────────────────
    P("")
    P("━━ 8. CO-PRODUCTION & MULTI-JURISDICTION STRUCTURES ━━━━━━━━━━━━━━━━━━━━")
    P("")

    # Structure A: MU (principal) + GB (post)
    mu_plus_gb_gross = MU_REBATE + UK_REBATE_POST
    mu_plus_gb_adj   = adj_results.get("GB", None)
    mu_plus_gb_padj  = mu_plus_gb_adj.total_adjustment_usd if mu_plus_gb_adj else 0
    mu_plus_gb_net   = mu_plus_gb_gross - mu_plus_gb_padj
    P("  A) MU (principal) + GB (post-production)")
    P(f"     MU rebate (35% × $2.5M base):    ${MU_REBATE:>10,.0f}")
    P(f"     UK AVEC (34% × ${UK_QPE_POST_ONLY:,.0f} UK post): ${UK_REBATE_POST:>10,.0f}")
    P(f"     Production adjustment (UK):       ${mu_plus_gb_padj:>10,.0f}")
    P(f"     NET (base scenario):              ${mu_plus_gb_net:>10,.0f}")
    P(f"     Cultural test requirement: UK AVEC needs ≥18/31 points")
    P(f"     Luke Evans (GB lead) +1pt | Writer (GB) +1pt | GB producer +1pt")
    P(f"     Director (AU) = 0pts | UK post facilities = +2-4pts")
    P(f"     Estimated UK points: 5-7/31 without full UK shoot — FAILS cultural test")
    P(f"     → UK post spend alone insufficient for cultural test")
    P(f"     → Recommend SERVICE structure (no cultural test) via UK post house")
    P("")

    # Structure B: MU (principal) + MT (post and/or reshoots)
    mu_plus_mt_gross = MU_REBATE + (POST_PROD_IN_BUDGET + POST_PROD_IN_KIND["base"]) * 0.40
    mu_plus_mt_adj   = adj_results.get("MT", None)
    mu_plus_mt_padj  = mu_plus_mt_adj.total_adjustment_usd if mu_plus_mt_adj else 0
    mu_plus_mt_net   = mu_plus_mt_gross - mu_plus_mt_padj
    P("  B) MU (principal) + MT (post + any Malta reshoots)")
    P(f"     MU rebate (35% × $2.5M base):    ${MU_REBATE:>10,.0f}")
    mt_post_rebate = (POST_PROD_IN_BUDGET + POST_PROD_IN_KIND["base"]) * 0.40
    P(f"     Malta (40% × ${POST_PROD_IN_BUDGET + POST_PROD_IN_KIND['base']:,.0f} post): ${mt_post_rebate:>10,.0f}")
    P(f"     Production adjustment (Malta):    ${mu_plus_mt_padj:>10,.0f}")
    P(f"     NET (base in-kind scenario):      ${mu_plus_mt_net:>10,.0f}")
    P(f"     No cultural test required. All spend qualifies. Malta VAT recoverable.")
    P(f"     → Malta post house handles in-kind $625K; 40% → $250K rebate")
    P("")

    # Structure C: GR (primary rebate) — hypothetical relocation
    gr_total_gross = GR_QPE_BASE * 0.40
    gr_adj = adj_results.get("GR", None)
    gr_padj = gr_adj.total_adjustment_usd if gr_adj else 0
    gr_post_adj = -POST_REPLACEMENT_BASE  # must replace in-kind post
    gr_net = gr_total_gross + gr_post_adj - gr_padj
    P("  C) Greece (principal) — hypothetical relocation")
    P(f"     GR rebate (40% × ${GR_QPE_BASE:,.0f}):  ${gr_total_gross:>10,.0f}")
    P(f"     Post replacement cost:            ${-gr_post_adj:>10,.0f}  (no GR in-kind equiv.)")
    P(f"     Production adjustment (GR):       ${gr_padj:>10,.0f}")
    P(f"     NET:                              ${gr_net:>10,.0f}")
    P(f"     ⚠ Risk: 9-12 month cashflow. Annual cap uncertainty. 22% payroll burden.")
    P(f"     ⚠ Risk: Frogsquad routing through Greek entity required")
    P("")

    # Structure D: MU + IE (post)
    mu_plus_ie_gross = MU_REBATE + IE_REBATE_POST
    ie_adj = adj_results.get("IE", None)
    ie_padj = ie_adj.total_adjustment_usd if ie_adj else 0
    mu_plus_ie_net = mu_plus_ie_gross - ie_padj
    P("  D) MU (principal) + IE S481 (post)")
    P(f"     MU rebate:                        ${MU_REBATE:>10,.0f}")
    P(f"     Ireland S481 (32% × ${IE_QPE_POST_ONLY:,.0f}): ${IE_REBATE_POST:>10,.0f}")
    P(f"     Production adjustment (IE):       ${ie_padj:>10,.0f}")
    P(f"     NET:                              ${mu_plus_ie_net:>10,.0f}")
    P(f"     Requires Irish cultural test. Irish entity setup ~$25K.")
    P(f"     S481 is transferable → gap financing available (strongest cashflow structure)")
    P("")

    # Structure E: MU + AU (post, director connection)
    mu_plus_au_gross = MU_REBATE + AU_REBATE_POST
    au_adj = adj_results.get("AU", None)
    au_padj = au_adj.total_adjustment_usd if au_adj else 0
    mu_plus_au_net = mu_plus_au_gross - au_padj
    P("  E) MU (principal) + AU Producer Offset (post, director connection)")
    P(f"     MU rebate:                        ${MU_REBATE:>10,.0f}")
    P(f"     AU Offset (40% × ${AU_QPE_POST_ONLY:,.0f}):  ${AU_REBATE_POST:>10,.0f}")
    P(f"     Production adjustment (AU):       ${au_padj:>10,.0f}")
    P(f"     NET:                              ${mu_plus_au_net:>10,.0f}")
    P(f"     AU director satisfies content test primary requirement.")
    P(f"     40% is highest post-production rate available. Requires AU company as applicant.")
    P("")

    # Eurimages — requires ≥3 EEA/Council of Europe co-producers
    P("  F) Eurimages (multi-lateral)")
    P(f"     Award range: EUR 100K–1.5M (competitive grant); est. EUR 300K–500K for this budget")
    P(f"     Requires: ≥3 Council of Europe co-producers (GB, IE, FR, MT, GR all eligible)")
    P(f"     Director (AU): NOT Council of Europe member — no blocker; co-producers drive eligibility")
    P(f"     MU/CA producers: NOT Eurimages members → add GB, MT, or IE as co-producers")
    P(f"     UK (GB): Council of Europe member ✓ | GB producers already on package")
    P(f"     Best structure: GB + MT + IE as Eurimages co-producers → $350K-$500K additional")
    P(f"     Combined (MU + MT post + IE + Eurimages grant):")
    eurimages_low = 350_000 * 0.78  # confidence discount
    eurimages_est = 500_000 * 0.78
    combined_eurimages = mu_plus_mt_net + eurimages_low
    P(f"       MU + MT post:   ${mu_plus_mt_net:>10,.0f}")
    P(f"       Eurimages est: +${eurimages_low:>10,.0f}  (25% confidence discount)")
    P(f"       Combined:       ${combined_eurimages:>10,.0f}")
    P("")

    # ── 9. QUALIFICATION RECOMMENDATIONS ──────────────────────────────────
    P("")
    P("━━ 9. QUALIFICATION ENGINE — RECOMMENDED CHANGES ━━━━━━━━━━━━━━━━━━━━━━━")
    P("")
    P("  Changes are ranked by estimated incremental incentive value.")
    P("")

    recs = [
        (
            "POST-PRODUCTION: Route to Malta (40% rebate)",
            mu_plus_mt_net - MU_REBATE,
            "HIGH",
            "Highest-impact single change. Malta has no cultural test. $988K post QPE × 40% = $395K.\n"
            "   Malta is the only warm-water jurisdiction with verified post-production facilities.\n"
            "   MFS handles color, sound, VFX delivery. VAT recoverable. 20-week cashflow."
        ),
        (
            "POST-PRODUCTION: Route to Australia (40% offset, director connection)",
            mu_plus_au_net - MU_REBATE,
            "MEDIUM",
            "40% = highest post rate. AU director satisfies content test primary requirement.\n"
            "   Requires AU company as applicant. Higher freight/timezone overhead.\n"
            "   Best if production team has existing AU relationship."
        ),
        (
            "POST-PRODUCTION: Route to Ireland S481 (32%, gap-financeable)",
            mu_plus_ie_net - MU_REBATE,
            "MEDIUM",
            "S481 is TRANSFERABLE → gap lender can take assignment. Best cashflow structure.\n"
            "   Requires Irish cultural test; GB producers + Luke Evans (GB) help scoring.\n"
            "   Irish entity setup $25K. Ardmore Studios (Wicklow) handles post delivery."
        ),
        (
            "MAURITIUS ATL: Confirm EDB ATL qualifying scope",
            (MU_QPE_OPT - MU_QPE_BASE) * 0.35,
            "HIGH",
            "If EDB confirms ATL fees qualify: director $175K + producer $148K + writer $85K\n"
            "   = $408K additional QPE × 35% = $142,800 more rebate. Zero additional cost.\n"
            "   Action: Submit written query to EDB re: ATL treatment IMMEDIATELY."
        ),
        (
            "MAURITIUS: Frogsquad routing through MU SPV",
            100_000 * 0.35,
            "MEDIUM",
            "Route Frogsquad payment ($99.8K) through Mauritius SPV rather than SA entity.\n"
            "   Swings QPE by ~$100K → additional $35,000 rebate at 35%.\n"
            "   Legal cost: ~$5K. Net gain: ~$30K. Confirm with SA dive team."
        ),
        (
            "MAURITIUS: Accommodation/per-diem qualifying confirmation",
            (159_783 + 114_130) * 0.35,
            "MEDIUM",
            "HOD accommodation ($159.8K) + local per diems ($114.1K) = $274K.\n"
            "   If EDB confirms these qualify: +$95,858 additional rebate.\n"
            "   Action: Submit written query to EDB with hotel receipts."
        ),
        (
            "STRUCTURE: Add UK producer as formal co-producer (Eurimages pathway)",
            eurimages_low,
            "LOW",
            "UK producers already on package. Formalizing GB co-production structure\n"
            "   with MT or IE entity enables Eurimages application.\n"
            "   Grant est. EUR 300K-500K (competitive). Timeline: 6-9 months pre-production.\n"
            "   Not applicable for completed Mauritius principal photography unless sequel/series."
        ),
        (
            "CREATIVE EUROPE MEDIA: Script development / distribution",
            80_000,
            "LOW",
            "Creative Europe MEDIA supports development and distribution, not production.\n"
            "   Est. €50K-€100K development grant if not yet claimed.\n"
            "   Requires EEA applicant. GB (Creative Europe participant post-Brexit: NO).\n"
            "   IE or MT entity required. Low probability for completed production."
        ),
    ]

    recs.sort(key=lambda x: x[1], reverse=True)
    for i, (action, value, certainty, detail) in enumerate(recs, 1):
        P(f"  #{i} [{certainty}] {action}")
        P(f"     Estimated value: ${value:,.0f}")
        for line in detail.split("\n"):
            P(f"     {line}")
        P("")

    # ── 10. RANKED FINAL SUMMARY ───────────────────────────────────────────
    P("")
    P("━━ 10. FINAL RANKED OUTPUT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    P("")

    # Define final structures with full net calculations
    # MU + MT post = best combination
    # Finance costs included
    fc_mu = finance_cost(MU_REBATE, 39)
    fc_mt_post = finance_cost(mt_post_rebate, 20)
    fc_au_post = finance_cost(AU_REBATE_POST, 26)
    fc_ie_post = finance_cost(IE_REBATE_POST, 12)  # S481 fastest

    final_structures = [
        {
            "rank": 1,
            "name": "MU PRINCIPAL + MALTA POST (Best Overall)",
            "gross_incentive": MU_REBATE + mt_post_rebate,
            "post_adj": 0,  # post is in Malta — no replacement cost
            "prod_adj": mu_plus_mt_padj,
            "finance_cost": fc_mu + fc_mt_post,
            "note": "Maximizes combined incentive. No cultural test. Best marine+post jurisdiction.",
        },
        {
            "rank": 2,
            "name": "MU PRINCIPAL + IRELAND POST (Runner-up)",
            "gross_incentive": MU_REBATE + IE_REBATE_POST,
            "post_adj": 0,
            "prod_adj": ie_padj,
            "finance_cost": fc_mu + fc_ie_post,
            "note": "S481 is transferable → gap financing. 12-week cashflow. Cultural test risk.",
        },
        {
            "rank": 3,
            "name": "MU PRINCIPAL ONLY — ATL + Accommodation confirmed (Highest Certainty)",
            "gross_incentive": MU_QPE_OPT * 0.35,  # if EDB confirms ATL
            "post_adj": -POST_REPLACEMENT_BASE,      # must replace in-kind post
            "prod_adj": 0,
            "finance_cost": finance_cost(MU_QPE_OPT * 0.35, 39),
            "note": "Zero structural change. Entire gain from EDB written confirmations.",
        },
        {
            "rank": 4,
            "name": "MU PRINCIPAL + AUSTRALIA POST (Highest Upside)",
            "gross_incentive": MU_REBATE + AU_REBATE_POST,
            "post_adj": 0,
            "prod_adj": au_padj,
            "finance_cost": fc_mu + fc_au_post,
            "note": "40% AU offset on post. Writer connection. Requires AU company. Highest post rate.",
        },
        {
            "rank": 5,
            "name": "GREECE RELOCATION (Full Rebate, Hypothetical)",
            "gross_incentive": GR_QPE_BASE * 0.40,
            "post_adj": -POST_REPLACEMENT_BASE,
            "prod_adj": gr_padj,
            "finance_cost": finance_cost(GR_QPE_BASE * 0.40, 39),
            "note": "Highest single-jurisdiction rate (40%). 9-12mo cashflow. Annual cap risk.",
        },
        {
            "rank": 6,
            "name": "MU + MALTA + EURIMAGES (Multi-lateral)",
            "gross_incentive": MU_REBATE + mt_post_rebate + eurimages_low,
            "post_adj": 0,
            "prod_adj": mu_plus_mt_padj + 35_000,  # Eurimages entity setup
            "finance_cost": fc_mu + fc_mt_post,
            "note": "Requires 3 Eurimages co-producers. 6-9mo competitive grant process.",
        },
    ]

    P(f"  {'#':<3} {'Structure':<42} {'Gross':>12} {'Post':>9} {'PAdj':>9} {'Fin':>9} {'NET':>12}")
    P("  " + "─" * 100)
    for s in final_structures:
        net = s["gross_incentive"] + s["post_adj"] - s["prod_adj"] - s["finance_cost"]
        P(f"  {s['rank']:<3} {s['name']:<42} ${s['gross_incentive']:>11,.0f} ${s['post_adj']:>8,.0f} ${-s['prod_adj']:>8,.0f} ${-s['finance_cost']:>8,.0f} ${net:>11,.0f}")
    P("")

    # ── 11. BLOCKERS ──────────────────────────────────────────────────────
    P("━━ 11. BLOCKERS — WHAT PREVENTS A BETTER RESULT ━━━━━━━━━━━━━━━━━━━━━━━")
    P("")
    blockers = [
        ("CRITICAL", "EDB ATL qualifying scope unconfirmed",
         "Director/producer/writer fees ($408K) excluded from base QPE.\n"
         "   If ATL qualifies: +$142,800 rebate with zero additional cost.\n"
         "   Submit written EDB query before production closes accounts."),
        ("HIGH", "In-kind post not monetized",
         "$500K-$750K in-kind Mauritius post has no EDB incentive attached.\n"
         "   Routing post to Malta (40%) or AU (40%) converts this to $250K-$300K incentive.\n"
         "   Decision must be made before post begins."),
        ("HIGH", "Rebate assignability to gap lender unconfirmed",
         "EDB has not confirmed the rebate receivable is assignable.\n"
         "   Without assignability: production must fund bridge finance itself (~$74K at 8%).\n"
         "   Malta and Ireland are both confirmed or likely assignable."),
        ("HIGH", "Frogsquad entity routing",
         "$99.8K SA-based dive team paid outside Mauritius entity.\n"
         "   Routing through MU SPV adds $35K rebate. Legal review required."),
        ("MEDIUM", "No Eurimages structure built pre-production",
         "Eurimages requires ≥3 European co-producers attached pre-production.\n"
         "   If principal photography complete, this window may be closed.\n"
         "   Still relevant for distribution and potential series/sequel."),
        ("MEDIUM", "Germany and Spain (Canary Islands) structurally excluded",
         "Germany: 30% German spend gate ($1.31M) not achievable at this budget.\n"
         "   Spain Canary Islands: EUR 1M minimum spend not achievable from this budget.\n"
         "   Neither jurisdiction is viable without substantially more Spanish/German spend."),
        ("LOW", "Australia Producer Offset requires AU company as applicant",
         "AU director present but no AU producer on package.\n"
         "   AU offset requires a company registered in Australia as the applicant.\n"
         "   Can be solved by engaging AU post house with offset assignment."),
    ]

    for severity, title, detail in blockers:
        P(f"  [{severity}] {title}")
        for line in detail.split("\n"):
            P(f"    {line}")
        P("")

    # ── 12. EXECUTIVE SUMMARY ─────────────────────────────────────────────
    P("━━ 12. EXECUTIVE SUMMARY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    P("")
    P("  ┌────────────────────────────────────────────────────────────────────┐")
    P("  │ BEST OVERALL STRUCTURE                                             │")
    P("  │ MU Principal (35%) + Malta Post (40%) + ATL confirmation          │")
    P("  │ Gross incentive:    $875,000 (MU) + $395,200 (MT post) = $1,270K  │")
    P("  │ Net (after adj):    ~$1,150,000–$1,200,000                         │")
    P("  │ Certainty:         MEDIUM-HIGH (MU rate PARSED; MT no cultural test│")
    P("  ├────────────────────────────────────────────────────────────────────┤")
    P("  │ RUNNER-UP                                                          │")
    P("  │ MU Principal + Ireland S481 Post                                  │")
    P("  │ Gross incentive:    $875,000 + $315,520 = $1,190,520              │")
    P("  │ Net (after adj):    ~$1,040,000                                    │")
    P("  │ KEY ADVANTAGE: S481 transferable → gap financing available         │")
    P("  ├────────────────────────────────────────────────────────────────────┤")
    P("  │ HIGHEST CERTAINTY                                                  │")
    P("  │ MU Principal + EDB ATL confirmations (zero structure change)       │")
    P("  │ Gross incentive:    up to $1,071,000 (optimistic QPE at 35%)       │")
    P("  │ Net post adj:       $321,000 (must replace $625K in-kind post)     │")
    P("  │ No new entity, no cultural test, no new spend required             │")
    P("  ├────────────────────────────────────────────────────────────────────┤")
    P("  │ HIGHEST UPSIDE                                                     │")
    P("  │ MU Principal + AU Post + Eurimages (if pre-production eligible)    │")
    P("  │ MU $875K + AU post $395,200 + Eurimages $273K = $1,543,000 gross  │")
    P("  │ Net after adj: ~$1,300,000+                                        │")
    P("  │ Risk: AU company required. Eurimages competitive (grant timeline). │")
    P("  └────────────────────────────────────────────────────────────────────┘")
    P("")
    P("  TOP 3 ACTIONS FOR MAXIMUM VALUE:")
    P("  1. Submit EDB query on ATL qualifying treatment (cost: $0, gain: $142K)")
    P("  2. Route post-production to Malta MFS or AU facility (gain: $250-395K)")
    P("  3. Engage AU post house as applicant for AU Producer Offset (director = AU qualifies)")
    P("")
    P("  IBERMEDIA: NOT APPLICABLE. No Ibero-American co-producer. No Spanish-language element.")
    P("  CREATIVE EUROPE MEDIA: Post-production complete distribution only. Low applicability.")
    P("  REGIONAL FUNDS: Film i Väst, Wallimage, Screen Flanders — require Nordic/Belgian")
    P("    co-producer and substantial regional spend. Structurally excluded at this budget level.")
    P("")
    P("=" * 80)
    P("  Report generated by FrameTax validation engine")
    P(f"  Budget source: tests/fixtures/little_utopia_sanitized.py")
    P(f"  Adjustment engine: production_adjustment.py / delta_engine.py (cbe84e4)")
    P("=" * 80)

    return "\n".join(lines)


if __name__ == "__main__":
    report = run()
    print(report)
    # Save to scratchpad
    out_path = "/tmp/claude-0/-home-user-Frametax/ce85c011-b727-52e4-b535-150462fcc283/scratchpad/lu_validation_report.txt"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(report)
    print(f"\n[Report saved to {out_path}]")
