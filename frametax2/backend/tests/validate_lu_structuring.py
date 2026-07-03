"""
validate_lu_structuring.py

Producer Structuring Advisor — Little Utopia validation report.

Run: python -m tests.validate_lu_structuring
"""
from __future__ import annotations

import sys
import os

# Make sure we can import from app/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.calculators.structuring_advisor import (
    ADVISOR_VERSION,
    LittleUtopiaParams,
    RecommendationConfidence,
    TimeHorizon,
    build_structuring_advisory,
)

# ── Output helpers ────────────────────────────────────────────────────────────

lines: list[str] = []


def P(s: str = "") -> None:
    lines.append(s)
    print(s)


def HR(char: str = "─", width: int = 72) -> None:
    P(char * width)


def header(title: str) -> None:
    HR("═")
    P(f"  {title}")
    HR("═")


def section(title: str) -> None:
    P()
    HR("─")
    P(f"  {title}")
    HR("─")


# ── Run advisor ────────────────────────────────────────────────────────────────

def main() -> None:
    p = LittleUtopiaParams()
    result = build_structuring_advisory(p)

    header("THE LITTLE UTOPIA — PRODUCER STRUCTURING ADVISORY")
    P(f"  Advisor version: {result.advisor_version}")
    P(f"  Jurisdiction:    {result.jurisdiction_code} (EDB Film Rebate 35%)")
    P(f"  Gross budget:    ${p.gross_budget_usd:,.0f}")
    P(f"  QPE base:        ${p.qpe_base_usd:,.0f}")
    P(f"  MU rebate base:  ${p.qpe_base_usd * p.mu_rebate_rate:,.0f}")
    P()
    P("  KNOWN TEAM")
    P(f"  Writer:    {p.writer_nationality} (United Kingdom)")
    P(f"  Director:  {p.director_nationality} (Australia — previously verified)")
    P(f"  Lead:      {p.lead_nationality} (Luke Evans — United Kingdom)")
    P(f"  Producers: {', '.join(p.producer_nationalities)}")

    # ── Summary ─────────────────────────────────────────────────────────────
    section("REBATE UPLIFT SUMMARY")
    P(f"  Immediate confirmed uplift:          ${result.total_immediate_rebate_uplift:>12,.0f}")
    P(f"  Medium-term confirmed uplift:        ${result.total_medium_term_rebate_uplift:>12,.0f}")
    P(f"  EDB-conditional uplift (if confirmed):${result.total_edb_conditional_rebate_uplift:>11,.0f}")
    P(f"  ─────────────────────────────────────────────────")
    P(f"  Total potential uplift:              ${result.total_potential_rebate_uplift:>12,.0f}")
    P()
    P(f"  CURRENT BASE REBATE:                 ${p.qpe_base_usd * p.mu_rebate_rate:>12,.0f}")
    P(f"  MAXIMUM REACHABLE REBATE:            ${p.qpe_base_usd * p.mu_rebate_rate + result.total_potential_rebate_uplift:>12,.0f}")

    # ── Recommendations by horizon ────────────────────────────────────────
    section("IMMEDIATE ACTIONS (no EDB approval required)")

    immediate = [r for r in result.recommendations if r.time_horizon == TimeHorizon.IMMEDIATE]
    for r in immediate:
        P()
        P(f"  [{r.recommendation_id}] {r.title}")
        P(f"  Type:       {r.transaction_type.value}")
        P(f"  Confidence: {r.confidence.value}")
        P(f"  ROI:        ${r.rebate_impact_usd:,.0f} rebate uplift "
          f"/ ${r.qualification_impact_usd:,.0f} QPE")
        P(f"  Risk:       {r.audit_risk.value}")
        P(f"  Difficulty: {r.implementation_difficulty.value}")
        P()
        P(f"  CURRENT:  {r.current_structure[:120]}...")
        P(f"  SUGGEST:  {r.suggested_structure[:120]}...")
        P(f"  REASON:   {r.reason[:140]}...")
        if r.published_support:
            P(f"  SUPPORT:  {r.published_support[:120]}...")
        P(f"  DOCS:     {', '.join(r.required_documentation[:3])}")

    section("EDB CLARIFICATION REQUIRED")

    edb_items = [r for r in result.recommendations if r.time_horizon == TimeHorizon.EDB_FIRST]
    for r in edb_items:
        P()
        P(f"  [{r.recommendation_id}] {r.title}")
        P(f"  Confidence: {r.confidence.value}")
        P(f"  Upside:     ${r.rebate_impact_usd:,.0f} (if EDB confirms)")
        P(f"  Risk:       {r.audit_risk.value}")
        P(f"  EDB Q:      {r.interpretation_question[:140] if r.interpretation_question else 'N/A'}...")
        P()
        P(f"  CURRENT:  {r.current_structure[:110]}...")
        P(f"  SUGGEST:  {r.suggested_structure[:110]}...")

    section("MEDIUM-TERM OPPORTUNITIES")

    medium = [r for r in result.recommendations if r.time_horizon == TimeHorizon.MEDIUM_TERM]
    for r in medium:
        P()
        P(f"  [{r.recommendation_id}] {r.title}")
        P(f"  Confidence: {r.confidence.value}")
        P(f"  Upside:     ${r.rebate_impact_usd:,.0f} rebate / ${r.qualification_impact_usd:,.0f} QPE")
        P(f"  Risk:       {r.audit_risk.value}")
        P(f"  Difficulty: {r.implementation_difficulty.value}")
        P()
        P(f"  CURRENT:  {r.current_structure[:110]}...")
        P(f"  SUGGEST:  {r.suggested_structure[:110]}...")

    # ── EDB Question Package ─────────────────────────────────────────────
    section("EDB QUESTION PACKAGE — SUBMIT PRE-PRODUCTION")
    P("  The following questions must be submitted to Mauritius EDB in writing")
    P("  before principal photography. All should go in a single consolidated letter.")
    P()
    for i, q in enumerate(result.edb_questions, 1):
        P(f"  Q{i}: {q}")
        P()

    # ── Ranked ROI table ─────────────────────────────────────────────────
    section("ROI RANKING (all recommendations)")
    P(f"  {'ID':<6}{'Title':<50}{'Rebate $':>12}{'Horizon':<14}{'Confidence':<26}{'Risk'}")
    P(f"  {'─'*6}{'─'*50}{'─'*12}{'─'*14}{'─'*26}{'─'*8}")
    sorted_by_roi = sorted(result.recommendations, key=lambda r: -r.rebate_impact_usd)
    for r in sorted_by_roi:
        title_short = r.title[:48]
        P(
            f"  {r.recommendation_id:<6}{title_short:<50}"
            f"{r.rebate_impact_usd:>12,.0f}"
            f"  {r.time_horizon.value:<14}"
            f"  {r.confidence.value:<24}"
            f"  {r.audit_risk.value}"
        )

    # ── Unknown items ────────────────────────────────────────────────────
    if result.unknown_items:
        section("UNKNOWN — REQUIRES OFFICIAL INTERPRETATION")
        for item in result.unknown_items:
            P(f"  • {item}")

    # ── Documentation checklist by category ─────────────────────────────
    section("IMMEDIATE ACTIONS CHECKLIST")
    P("  Before end of pre-production:")
    P("  [ ] Schedule EDB pre-production meeting (R-11)")
    P("  [ ] Submit consolidated EDB question package (Q1–Q5)")
    P("  [ ] Establish MU SPV for Frogsquad routing (R-01)")
    P("  [ ] Commission independent FMV appraisal for in-kind post (R-05)")
    P("  [ ] Appoint MU accountant for related-party compliance (R-10)")
    P()
    P("  After EDB written responses received:")
    P("  [ ] Update QPE filing to include confirmed items (R-02, R-03, R-01)")
    P("  [ ] If FMV confirmed: document in-kind post at FMV")
    P("  [ ] If FMV NOT confirmed: restructure as deferred payment (R-04)")
    P("  [ ] Expand marine schedule (R-06) and local crew (R-07)")
    P("  [ ] If EDB post ruling positive: pursue music sessions in MU (R-08)")
    P("  [ ] If ATL fees confirmable: restructure director/writer agreements (R-09)")

    # ── Financial summary ────────────────────────────────────────────────
    section("FINANCIAL SUMMARY — LITTLE UTOPIA RESTRUCTURING VALUE")
    base_rebate = p.qpe_base_usd * p.mu_rebate_rate
    bridge_base = base_rebate * p.bridge_rate * (p.mu_delay_weeks / 52)
    inkind_value = p.inkind_base_usd  # free service (base scenario)
    mu_net_today = base_rebate - bridge_base + inkind_value

    P(f"  CURRENT MU BASELINE")
    P(f"    QPE (base):                   ${p.qpe_base_usd:>12,.0f}")
    P(f"    MU rebate (35%):              ${base_rebate:>12,.0f}")
    P(f"    Bridge finance (8%×39/52wks): ${ -bridge_base:>12,.0f}")
    P(f"    In-kind post (free service):  ${inkind_value:>12,.0f}")
    P(f"    NET PRODUCER VALUE:           ${mu_net_today:>12,.0f}")
    P()

    # Best case: all EDB items confirmed
    confirmed_qpe_delta = (
        p.frogsquad_usd + p.hod_accom_usd + p.local_perdiem_usd
        + p.inkind_base_usd  # FMV confirmed
        + 112_000 + 105_000  # marine + crew expansion
        + 60_000  # music
    )
    confirmed_qpe = p.qpe_base_usd + confirmed_qpe_delta
    confirmed_rebate = confirmed_qpe * p.mu_rebate_rate
    confirmed_bridge = confirmed_rebate * p.bridge_rate * (p.mu_delay_weeks / 52)
    # Best case: FMV confirmed as QPE AND post service still received for free
    # These are not mutually exclusive — production receives free service AND
    # gets rebate on the FMV QPE amount. Include free service in net value.
    confirmed_net = confirmed_rebate - confirmed_bridge + inkind_value

    P(f"  BEST CASE (all EDB items confirmed, marine+crew expanded)")
    P(f"    QPE (optimised):              ${confirmed_qpe:>12,.0f}")
    P(f"    MU rebate (35%):              ${confirmed_rebate:>12,.0f}")
    P(f"    Bridge finance:               ${ -confirmed_bridge:>12,.0f}")
    P(f"    In-kind post (free + QPE):    ${inkind_value:>12,.0f}")
    P(f"    NET PRODUCER VALUE:           ${confirmed_net:>12,.0f}")
    P(f"    UPLIFT vs current:            ${confirmed_net - mu_net_today:>12,.0f}")
    P()

    # Conservative case: only confirmed non-EDB items
    conservative_delta = 112_000 + 105_000  # marine + crew expansion only
    conservative_qpe = p.qpe_base_usd + conservative_delta
    conservative_rebate = conservative_qpe * p.mu_rebate_rate
    conservative_bridge = conservative_rebate * p.bridge_rate * (p.mu_delay_weeks / 52)
    conservative_net = conservative_rebate - conservative_bridge + inkind_value

    P(f"  CONSERVATIVE CASE (marine+crew expansion only; no EDB needed)")
    P(f"    QPE:                          ${conservative_qpe:>12,.0f}")
    P(f"    MU rebate (35%):              ${conservative_rebate:>12,.0f}")
    P(f"    Bridge finance:               ${ -conservative_bridge:>12,.0f}")
    P(f"    In-kind post (free service):  ${inkind_value:>12,.0f}")
    P(f"    NET PRODUCER VALUE:           ${conservative_net:>12,.0f}")
    P(f"    UPLIFT vs current:            ${conservative_net - mu_net_today:>12,.0f}")
    P()
    P("  NOTE: In-kind free service is received independently of QPE treatment.")
    P("  Even if EDB confirms FMV qualifies as QPE, the production ALSO receives")
    P("  the post services at no cash cost. Best case net includes both.")

    # ── Summary verdict ──────────────────────────────────────────────────
    section("PRODUCER VERDICT")
    P("  PRIORITY ORDER FOR PRE-PRODUCTION")
    P()
    P("  1. R-11  EDB meeting → submit Q package → get written answers")
    P("           Action owner: Producers + MU accountant")
    P("           Timeline: immediately; 6-8 weeks before shoot")
    P()
    P("  2. R-10  Related-party arm's-length documentation protocol")
    P("           Action owner: MU accountant + lawyers")
    P("           Timeline: concurrent with R-11")
    P()
    P("  3. R-01  MU SPV contracts for Frogsquad")
    P("           Action owner: MU production service company")
    P("           Timeline: before marine unit contracts signed")
    P()
    P("  4. R-06  Expand marine shooting days")
    P("  + R-07  Expand local crew hiring")
    P("           Action owner: Production Manager")
    P("           Timeline: during pre-production budgeting")
    P()
    P("  5. R-05  In-kind post QPE ruling → drives all subsequent post decisions")
    P("           If YES:  proceed at FMV. Rebate uplift +$218,750.")
    P("           If NO:   restructure as deferred payment (R-04) or leave as-is.")
    P()
    P("  THE MOST IMPORTANT QUESTION:")
    P("  MU 100% beats every external post structure under all scenarios.")
    P("  The EDB meeting (R-11) is the only lever that meaningfully changes")
    P("  total producer value. Without it: $875K rebate + $625K free service.")
    P("  With it (best case): potentially $1.2M+ rebate, full certainty on audit.")

    HR("═")
    P(f"  END REPORT — ADVISOR v{ADVISOR_VERSION}")
    HR("═")

    return result


if __name__ == "__main__":
    main()
