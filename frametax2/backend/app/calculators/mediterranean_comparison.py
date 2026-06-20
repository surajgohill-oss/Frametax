"""
mediterranean_comparison.py

Tier 1 Mediterranean jurisdiction comparison engine.

Runs any QPEAccount list (e.g. the Little Utopia sanitized fixture) through
Mauritius / Malta / Greece / Cyprus qualification rules and returns a
structured comparison matrix.

Jurisdiction qualification rules are deterministic and traceable to the
profile data in jurisdiction_comparison.py.  Every rule that differs between
MU and the other three is marked with a confidence note.

No LLM calls.  All arithmetic is deterministic and testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.calculators.qpe_calculator import (
    QPEAccount,
    QPECalculationResult,
    calculate_qpe,
    get_scenario,
)

COMPARISON_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Jurisdiction program configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TierOneProgram:
    jurisdiction_code: str
    program_name: str
    confidence_tier: str        # PARSED or DISCOVERY
    base_rate: Optional[float]
    max_rate: Optional[float]
    finance_delay_weeks: int    # weeks from wrap to rebate receipt
    finance_annual_rate: float  # bridge finance rate
    rate_verified: bool         # True only if confirmed from statute text
    notes: str


TIER1_PROGRAMS: dict[str, TierOneProgram] = {
    "MU": TierOneProgram(
        jurisdiction_code="MU",
        program_name="Mauritius EDB Production Incentive (Budget-Evidenced 35%)",
        confidence_tier="PARSED",
        base_rate=0.35,
        max_rate=0.35,
        finance_delay_weeks=39,
        finance_annual_rate=0.08,
        rate_verified=False,
        notes=(
            "Rate inferred from budget line 'EDB Rebate at 35%' — not from EDB statute. "
            "ATL scope unknown. Frogsquad routing creates ±$100K QPE swing. "
            "Accommodation/per-diem qualifying treatment unconfirmed. "
            "VAT 15% non-recoverable ($92,439 in gross budget). "
            "Finance timing unknown — estimated 39 weeks based on comparable programs."
        ),
    ),
    "MT": TierOneProgram(
        jurisdiction_code="MT",
        program_name="Malta Film Commission Cash Rebate",
        confidence_tier="PARSED",
        base_rate=0.25,
        max_rate=0.40,
        finance_delay_weeks=20,
        finance_annual_rate=0.08,
        rate_verified=False,
        notes=(
            "25% base; up to 40% with uplifts: +3% MFC cultural, +3% Malta VFX/post, "
            "+7% small budget (<EUR 3M), +2% Maltese element. "
            "All ATL and BTL spend explicitly qualifying. "
            "Mediterranean Film Studios: 750,000-gal outdoor water tank + indoor. "
            "VAT recoverable (EU). WHT on cast: 0% standard. "
            "Finance delay: ~60 working days from audit submission (estimated)."
        ),
    ),
    "GR": TierOneProgram(
        jurisdiction_code="GR",
        program_name="Greece Cash Rebate for International Productions",
        confidence_tier="PARSED",
        base_rate=0.40,
        max_rate=0.40,
        finance_delay_weeks=39,
        finance_annual_rate=0.08,
        rate_verified=False,
        notes=(
            "40% flat rate on all qualifying Greek expenditure. "
            "ATL and BTL including marine spend stated as qualifying. "
            "Greek payroll burden ~22-24% on local crew. "
            "WHT on international cast: 20% standard (treaty may reduce). "
            "Cashflow: 9-12 months typical per market reports (no official SLA). "
            "Annual program allocation exists; budget oversubscription is a risk. "
            "VAT recoverable (EU). 16,000+ km coastline for open-water filming."
        ),
    ),
    "CY": TierOneProgram(
        jurisdiction_code="CY",
        program_name="Cyprus Film Production Rebate",
        confidence_tier="DISCOVERY",
        base_rate=0.35,
        max_rate=0.35,
        finance_delay_weeks=26,
        finance_annual_rate=0.08,
        rate_verified=False,
        notes=(
            "DISCOVERY tier: 35% rate not verified from statute. "
            "Qualification scope less certain than Malta or Greece. "
            "ATL: optimistic scenario only (DISCOVERY). "
            "Marine/vessel expected to qualify. "
            "VAT recoverable (EU, 19%). WHT: 0%. Payroll burden ~8%. "
            "Low crew depth — substantial BTL import required. "
            "Cashflow: ~26 weeks estimated."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Per-jurisdiction QPE qualification rules
# ---------------------------------------------------------------------------

def _jur_flags(acc: QPEAccount, jur_code: str) -> tuple[bool, bool, bool]:
    """
    Return (conservative, base, optimistic) QPE flags for one account in one jurisdiction.

    Rules:
      MU — use account's own fixture flags (Mauritius-specific analysis)
      MT — all ATL and BTL production spend qualifies (MFC confirmed)
      GR — ATL stated qualifying; all BTL + marine; cast optimistic only
      CY — DISCOVERY: ATL optimistic only; accommodation/foreign crew base+
    """
    T, F = True, False

    # Universal exclusions (same for all jurisdictions)
    if acc.is_memo_line:
        return (F, F, F)
    dept = acc.department.lower()
    if "other" in dept:
        return (F, F, F)
    if "post" in dept:
        return (F, F, F)
    if acc.account_code == "39-00":   # international travel
        return (F, F, F)

    if jur_code == "MU":
        return (acc.conservative_qualifies, acc.base_qualifies, acc.optimistic_qualifies)

    is_atl = "above the line" in dept
    is_btl_prod = "production" in dept
    code = acc.account_code or ""

    # ── Malta ───────────────────────────────────────────────────────────────
    # All ATL and all BTL production spend explicitly qualifies (MFC guidelines).
    # No routing requirement, no cultural test, no WHT on standard payments.
    if jur_code == "MT":
        if is_atl or is_btl_prod:
            return (T, T, T)
        return (F, F, F)

    # ── Greece ──────────────────────────────────────────────────────────────
    # ATL stated qualifying (Enterprise Greece overview, PARSED).
    # Cast (13-00) most uncertain: optimistic only.
    # Frogsquad (33-00) needs Greek-entity routing: base+.
    # All other BTL: qualifies conservatively (any Greek-routed spend).
    if jur_code == "GR":
        if code == "13-00":                     # Cast — most uncertain ATL item
            return (F, F, T)
        if is_atl:                              # Director, producer, writer (10-12)
            return (F, T, T)
        if code == "33-00":                     # Frogsquad — Greek entity routing needed
            return (F, T, T)
        if is_btl_prod:
            return (T, T, T)
        return (F, F, F)

    # ── Cyprus ──────────────────────────────────────────────────────────────
    # DISCOVERY tier — higher uncertainty on ATL and contested items.
    # ATL (excl cast): optimistic only.
    # Cast: excluded all scenarios (too uncertain for DISCOVERY program).
    # Accommodation / imported crew / Frogsquad: base+.
    # Clear BTL (marine, local crew, locations, transport, catering): conservative.
    if jur_code == "CY":
        if code == "13-00":                     # Cast — excluded
            return (F, F, F)
        if is_atl:                              # Director, producer, writer
            return (F, F, T)
        if code == "33-00":                     # Frogsquad — Cyprus entity routing needed
            return (F, T, T)
        if code in ("37-00", "38-00"):          # Accommodation/per-diem — unconfirmed
            return (F, T, T)
        if code in ("21-00", "23-00", "28-00", "42-00"):  # Imported crew
            return (F, T, T)
        if is_btl_prod:
            return (T, T, T)
        return (F, F, F)

    return (F, F, F)


def _apply_jur_rules(
    accounts: list[QPEAccount],
    jur_code: str,
) -> list[QPEAccount]:
    """
    Return a new account list with jurisdiction-specific QPE flags applied.
    Original accounts are not mutated.
    """
    import dataclasses

    result = []
    for acc in accounts:
        c, b, o = _jur_flags(acc, jur_code)
        result.append(dataclasses.replace(acc,
            conservative_qualifies=c,
            base_qualifies=b,
            optimistic_qualifies=o,
        ))
    return result


# ---------------------------------------------------------------------------
# Comparison matrix dimensions
# ---------------------------------------------------------------------------

COMPARISON_DIMENSIONS = [
    "rate_verified",
    "atl_treatment",
    "director_treatment",
    "producer_treatment",
    "cast_treatment",
    "foreign_labor_treatment",
    "marine_vessel_treatment",
    "accommodation_per_diem",
    "insurance_treatment",
    "contingency_treatment",
    "finance_monetisation",
    "payment_timing",
    "grants_support",
    "vat_treatment",
]

# Per-dimension values for each Tier 1 jurisdiction.
# True = confirmed qualifying, False = confirmed excluded, None = unknown,
# str = descriptive note where bool is insufficient.
COMPARISON_MATRIX: dict[str, dict[str, object]] = {
    "MU": {
        "rate_verified":          False,
        "atl_treatment":          None,    # Scope unknown — EDB statute not reviewed
        "director_treatment":     None,    # Director fee qualifying scope unknown
        "producer_treatment":     None,    # Producer fee qualifying scope unknown
        "cast_treatment":         None,    # Cast qualifying scope unknown
        "foreign_labor_treatment": None,   # International crew routing rules unconfirmed
        "marine_vessel_treatment": True,   # Confirmed in budget QPE (Groups report)
        "accommodation_per_diem": None,    # Mauritius spend but EDB treatment unconfirmed
        "insurance_treatment":    False,   # Standard exclusion assumed; not confirmed
        "contingency_treatment":  False,   # Standard exclusion assumed
        "finance_monetisation":   None,    # Rebate assignability to gap lender unconfirmed
        "payment_timing":         None,    # No confirmed EDB processing SLA
        "grants_support":         None,    # MFDC permit/location facilitation; no confirmed grant
        "vat_treatment":          "15pct_non_recoverable",  # Confirmed $92,439 in gross budget
    },
    "MT": {
        "rate_verified":          False,   # 25-40% from MFC summary; statute not reviewed
        "atl_treatment":          True,    # Confirmed qualifying (MFC published guidelines)
        "director_treatment":     True,    # Confirmed (ATL explicitly eligible)
        "producer_treatment":     True,    # Confirmed (ATL explicitly eligible)
        "cast_treatment":         True,    # Confirmed (ATL explicitly eligible in MFC)
        "foreign_labor_treatment": True,   # Any Malta expenditure qualifies; no restriction
        "marine_vessel_treatment": True,   # Vessel charter and marine logistics confirmed
        "accommodation_per_diem": True,    # Qualifying Malta expenditure includes accommodation
        "insurance_treatment":    False,   # Standard exclusion per MFC
        "contingency_treatment":  False,   # Standard exclusion per MFC
        "finance_monetisation":   None,    # Rebate assignability not confirmed from primary source
        "payment_timing":         "20_weeks_estimated",  # ~60 working days; not SLA-confirmed
        "grants_support":         None,    # No confirmed supplementary grant programme
        "vat_treatment":          "recoverable_eu",  # EU VAT registration available
    },
    "GR": {
        "rate_verified":          False,   # 40% from Enterprise Greece overview; statute not reviewed
        "atl_treatment":          True,    # ATL stated qualifying (Enterprise Greece programme overview)
        "director_treatment":     True,    # Director fee stated qualifying
        "producer_treatment":     True,    # Producer fee stated qualifying
        "cast_treatment":         None,    # ATL cast qualifying stated but verification pending
        "foreign_labor_treatment": None,   # Foreign crew qualifying through Greek entity — routing rules unverified
        "marine_vessel_treatment": True,   # Vessel and marine support stated as qualifying Greek spend
        "accommodation_per_diem": None,    # Greek accommodation spend probable; not confirmed from primary source
        "insurance_treatment":    False,   # Standard exclusion
        "contingency_treatment":  False,   # Standard exclusion
        "finance_monetisation":   None,    # Rebate assignability to financier unconfirmed
        "payment_timing":         "39_weeks_estimated",  # 9-12 months per market reports; no official SLA
        "grants_support":         None,    # Annual allocation cap exists; competitive risk unquantified
        "vat_treatment":          "recoverable_eu",  # EU VAT registration available
    },
    "CY": {
        "rate_verified":          False,   # 35% from DISCOVERY sources; statute not reviewed
        "atl_treatment":          None,    # Stated qualifying but DISCOVERY tier
        "director_treatment":     None,    # Probable; not confirmed from CIPA primary source
        "producer_treatment":     None,    # Probable; not confirmed from CIPA primary source
        "cast_treatment":         None,    # Unknown; excluded from CY comparison scenarios
        "foreign_labor_treatment": None,   # Cyprus entity routing required; rules unconfirmed
        "marine_vessel_treatment": True,   # Expected qualifying; not confirmed from programme text
        "accommodation_per_diem": None,    # Cyprus spend probable; treatment unconfirmed
        "insurance_treatment":    False,   # Standard exclusion
        "contingency_treatment":  False,   # Standard exclusion
        "finance_monetisation":   None,    # Programme maturity insufficient to confirm assignability
        "payment_timing":         "26_weeks_estimated",
        "grants_support":         None,
        "vat_treatment":          "recoverable_eu",  # EU VAT registration available (19%)
    },
}


# ---------------------------------------------------------------------------
# Per-jurisdiction Little Utopia QPE runner
# ---------------------------------------------------------------------------

@dataclass
class JurisdictionQPEResult:
    jurisdiction_code: str
    program: TierOneProgram
    qpe_result: QPECalculationResult
    rebate_base: float       # at base_rate, base scenario
    rebate_max: float        # at max_rate, base scenario (same if no uplifts)
    finance_cost_base: float # on base rebate, at configured delay + rate
    net_benefit_base: float  # rebate_max - finance_cost_base
    net_benefit_pct: float   # net_benefit_base / gross_budget_usd
    comparison_matrix: dict  # per-dimension data for this jurisdiction


def run_tier1_comparison(
    accounts: list[QPEAccount],
) -> dict[str, JurisdictionQPEResult]:
    """
    Run the provided accounts through all four Tier 1 jurisdictions.

    Returns a dict keyed by jurisdiction code containing QPE results,
    rebate estimates, finance costs, and net producer benefit.
    """
    results: dict[str, JurisdictionQPEResult] = {}

    for jur_code, program in TIER1_PROGRAMS.items():
        rates = [program.base_rate]
        if program.max_rate != program.base_rate:
            rates.append(program.max_rate)
        rates = [r for r in rates if r is not None]

        jur_accounts = _apply_jur_rules(accounts, jur_code)
        qpe_result = calculate_qpe(
            jur_accounts,
            rebate_rates=rates,
            jurisdiction_code=jur_code,
            finance_cost_delay_weeks=program.finance_delay_weeks,
            finance_cost_annual_rate=program.finance_annual_rate,
        )

        base_s = get_scenario(qpe_result, "base")
        base_qpe = base_s.qpe_usd
        rebate_base = base_s.rebate_amounts.get(program.base_rate, 0.0)
        rebate_max = base_s.rebate_amounts.get(program.max_rate, rebate_base)

        # Finance cost: from the finance_cost_estimates for max_rate, base scenario
        # estimates are ordered: per-scenario × per-rate, so index depends on scenario order
        # and rate order.  Extract by matching rebate_usd.
        finance_cost_base = 0.0
        for fc in qpe_result.finance_cost_estimates:
            if abs(fc.rebate_usd - rebate_max) < 1.0:
                finance_cost_base = fc.finance_cost_usd
                break

        net_benefit_base = rebate_max - finance_cost_base
        net_benefit_pct = (
            net_benefit_base / qpe_result.gross_budget_usd
            if qpe_result.gross_budget_usd > 0 else 0.0
        )

        results[jur_code] = JurisdictionQPEResult(
            jurisdiction_code=jur_code,
            program=program,
            qpe_result=qpe_result,
            rebate_base=rebate_base,
            rebate_max=rebate_max,
            finance_cost_base=finance_cost_base,
            net_benefit_base=net_benefit_base,
            net_benefit_pct=net_benefit_pct,
            comparison_matrix=COMPARISON_MATRIX[jur_code],
        )

    return results


def rank_by_net_benefit(
    results: dict[str, JurisdictionQPEResult],
) -> list[tuple[str, JurisdictionQPEResult]]:
    """Return jurisdictions sorted by net_benefit_base descending."""
    return sorted(results.items(), key=lambda x: x[1].net_benefit_base, reverse=True)


def build_gap_summary(
    results: dict[str, JurisdictionQPEResult],
) -> dict[str, list[str]]:
    """
    Return per-jurisdiction list of remaining unknowns preventing VERIFIED status.
    An unknown is any dimension where value is None in the comparison matrix
    OR where rate_verified is False.
    """
    gaps: dict[str, list[str]] = {}
    for code, r in results.items():
        jur_gaps = []
        if not r.program.rate_verified:
            jur_gaps.append(
                f"base_rate={r.program.base_rate} not verified from statute text "
                f"(confidence_tier={r.program.confidence_tier})"
            )
        for dim, val in r.comparison_matrix.items():
            if val is None:
                jur_gaps.append(f"{dim}: unknown")
        gaps[code] = jur_gaps
    return gaps
