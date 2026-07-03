"""
inkind_contribution.py

Deterministic model for in-kind / non-cash production contribution treatment.

Determines how free or discounted services (post-production in-kind deals,
vendor discounts, government-supplied facilities, sponsor contributions) should
be classified for purposes of qualifying production expenditure (QPE) under
film incentive programs.

Source research summary — Mauritius EDB Film Rebate:
────────────────────────────────────────────────────
No explicit public guidance found in EDB Act summaries or Investment Promotion
(Film Production) Regulations excerpts on in-kind / non-cash qualifying spend.
The program term "production expenditure" is used without a statutory definition
available from open sources at time of analysis.

Comparable program precedents (applied as analogs):
  UK AVEC (HM Treasury / HMRC CTM89600):
    "qualifying expenditure" = amounts ACTUALLY PAID; in-kind excluded unless
    invoiced at arm's-length and settled in cash. Related-party FMV rules apply.
  New Zealand SPGF (NZSPG Guidelines 2023):
    In-kind contributions DO NOT qualify unless converted to cash equivalent
    through an invoiced, arm's-length transaction that is actually paid.
  Australia QAPE (Screen Australia / ATO):
    In-kind contributions: excluded from QAPE. Only amounts "incurred and paid"
    qualify. FMV documentation required for related-party transactions.
  France TRIP (CNC Circular 2022):
    "dépenses effectivement engagées et payées" — only incurred AND paid.
    Vendor discounts / barter: excluded unless invoiced at full rate and paid.
  Ireland Section 481 (Revenue eBrief 078/23):
    Qualifying Irish expenditure must be "actually paid" to an Irish qualifying
    person. In-kind / barter transactions excluded.
  Greece Production Rebate (Enterprise Greece 2023):
    Qualifying spend must be "actual expenditure incurred and paid in Greece".
    Donations, barter, in-kind: excluded from qualifying base.

CONCLUSION (Mauritius-specific): UNKNOWN. No explicit EDB rule available from
public sources. Conservative treatment follows international standard practice:
in-kind services do NOT qualify at FMV unless EDB explicitly confirms otherwise.

No LLM calls. No DB access. Deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

CALCULATOR_VERSION = "1.0.0"

# ── Enumerations ─────────────────────────────────────────────────────────────

class ContributionType(str, Enum):
    IN_KIND_SERVICE       = "in_kind_service"       # free/discounted services
    VENDOR_DISCOUNT       = "vendor_discount"        # below-market rate from vendor
    SPONSOR_CONTRIBUTION  = "sponsor_contribution"   # 3rd-party sponsor value
    GOVERNMENT_GRANT      = "government_grant"       # government-funded facilities/services
    PRODUCTION_SVC_REBATE = "production_service_rebate"  # post-production rebate/subsidy
    CASH_REINVESTMENT     = "cash_reinvestment"      # cash paid then returned to production


class QualifyingTreatment(str, Enum):
    QUALIFIES_AT_CASH_PAID = "qualifies_at_cash_paid"  # only cash actually paid qualifies
    QUALIFIES_AT_FMV       = "qualifies_at_fmv"        # FMV qualifies (requires documentation)
    EXCLUDED               = "excluded"                 # explicitly excluded from QPE
    REDUCES_QPE            = "reduces_qpe"              # reduces gross QPE (govt assistance offset)
    UNKNOWN                = "unknown"                  # requires program authority ruling


class AuditRisk(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class SourceConfidence(str, Enum):
    HIGH    = "HIGH"     # confirmed from primary statutory source
    MEDIUM  = "MEDIUM"   # confirmed from official program guidance
    LOW     = "LOW"      # inferred from comparable programs
    UNKNOWN = "UNKNOWN"  # no source found; EDB ruling required


# ── Core dataclasses ─────────────────────────────────────────────────────────

@dataclass
class InKindContribution:
    """
    Describes one in-kind / non-cash production contribution.

    face_value_usd        — stated / notional value (what provider says it's worth)
    cash_paid_usd         — actual cash the production hands over (may be $0)
    fair_market_value_usd — arm's-length market value (may equal face_value or differ)
    """
    contribution_type: ContributionType
    description: str
    face_value_usd: float
    cash_paid_usd: float
    fair_market_value_usd: float
    qualifying_treatment: QualifyingTreatment
    requires_invoice: bool
    requires_payment_proof: bool
    requires_fmv_support: bool
    requires_related_party_disclosure: bool
    source_confidence: SourceConfidence
    notes: str = ""

    @property
    def discount_usd(self) -> float:
        """Amount the production saved vs paying market rate."""
        return max(0.0, self.fair_market_value_usd - self.cash_paid_usd)

    @property
    def is_fully_free(self) -> bool:
        return self.cash_paid_usd == 0.0


@dataclass
class QPEScenario:
    """
    One treatment scenario for a given in-kind contribution against a program's QPE rules.

    scenario_id   — e.g. "A", "B", "C", "D", "E"
    scenario_name — human label
    qpe_amount_usd — the dollar amount that enters QPE under this scenario
                     (may be 0 if excluded, or negative if reduces QPE)
    """
    scenario_id: str
    scenario_name: str
    treatment: QualifyingTreatment
    qpe_amount_usd: float       # enters QPE: 0 if excluded, <0 if reduces QPE
    rebate_impact_usd: float    # qpe_amount_usd × program_rate
    audit_risk: AuditRisk
    documentation_required: list[str]
    edb_questions: list[str]
    notes: str


@dataclass
class InKindImpactResult:
    """
    Full analysis of one in-kind contribution across all scenarios.
    """
    contribution: InKindContribution
    program_rate: float
    base_qpe_usd: float             # QPE before this contribution is considered
    scenarios: list[QPEScenario]
    international_precedents: list[str]
    recommended_scenario: str       # scenario_id that best reflects international standard
    edb_ruling_required: bool
    required_edb_questions: list[str]
    documentation_checklist: list[str]


# ── International precedent database ─────────────────────────────────────────

INTERNATIONAL_PRECEDENTS: list[str] = [
    "UK AVEC (HMRC CTM89600): Only 'actually paid' expenditure qualifies. "
    "In-kind excluded unless invoiced at arm's length and settled in cash.",

    "New Zealand SPGF (2023 Guidelines): In-kind contributions do NOT qualify "
    "unless converted via invoiced arm's-length cash transaction.",

    "Australia QAPE (ATO / Screen Australia): In-kind excluded from QAPE. "
    "Only amounts 'incurred and paid' count. Related-party FMV rules apply.",

    "France TRIP (CNC 2022): Only 'dépenses effectivement engagées et payées' "
    "(incurred AND paid). Vendor discounts / barter excluded.",

    "Ireland S481 (Revenue eBrief 078/23): Must be 'actually paid' to qualifying "
    "Irish person. In-kind / barter excluded.",

    "Greece Rebate (Enterprise Greece 2023): 'Actual expenditure incurred and paid'. "
    "Donations, barter, in-kind excluded.",

    "Mauritius EDB: NO EXPLICIT RULE FOUND in public sources. "
    "Treatment classified UNKNOWN. EDB ruling required.",
]

# ── Scenario definitions ──────────────────────────────────────────────────────

def _scenario_a_excluded(
    contrib: InKindContribution,
    program_rate: float,
) -> QPEScenario:
    """A: Excluded — in-kind services do not qualify (standard international practice)."""
    return QPEScenario(
        scenario_id="A",
        scenario_name="Excluded from QPE (standard practice)",
        treatment=QualifyingTreatment.EXCLUDED,
        qpe_amount_usd=0.0,
        rebate_impact_usd=0.0,
        audit_risk=AuditRisk.LOW,
        documentation_required=[
            "Document the in-kind arrangement in co-production/service agreement",
            "Confirm no cash changed hands via signed declaration",
            "Record provider relationship and arm's-length determination",
        ],
        edb_questions=[
            "Please confirm whether in-kind post-production services provided by a "
            "Mauritius entity at zero cash cost qualify as 'production expenditure' "
            "under the EDB Film Rebate Scheme.",
        ],
        notes=(
            "Follows international standard. Most comparable programs exclude "
            "in-kind services where no cash consideration was paid. "
            "Zero QPE impact. Zero rebate impact. Lowest audit risk."
        ),
    )


def _scenario_b_cash_paid(
    contrib: InKindContribution,
    program_rate: float,
) -> QPEScenario:
    """B: Qualifies only at cash actually paid (e.g. $0 if fully free)."""
    qpe = contrib.cash_paid_usd
    rebate = qpe * program_rate
    docs = [
        "Bank statement / payment confirmation for cash paid",
        "Invoice from service provider at agreed (discounted) rate",
        "Explanation of discount basis in production agreement",
    ]
    if contrib.requires_related_party_disclosure:
        docs.append("Related-party disclosure and arm's-length certification")

    return QPEScenario(
        scenario_id="B",
        scenario_name=f"Qualifies at cash paid only (${contrib.cash_paid_usd:,.0f})",
        treatment=QualifyingTreatment.QUALIFIES_AT_CASH_PAID,
        qpe_amount_usd=qpe,
        rebate_impact_usd=rebate,
        audit_risk=AuditRisk.MEDIUM if contrib.cash_paid_usd > 0 else AuditRisk.LOW,
        documentation_required=docs,
        edb_questions=[
            "Does the EDB scheme allow qualifying production expenditure to include "
            "discounted-rate vendor services where only the net cash paid is claimed "
            "(not the full market rate)?",
        ],
        notes=(
            f"Cash paid = ${contrib.cash_paid_usd:,.0f}. "
            f"If fully free (cash = $0), QPE contribution is $0. "
            "Aligns with 'cash paid' interpretation common in UK/AU/FR/IE programs."
        ),
    )


def _scenario_c_fmv(
    contrib: InKindContribution,
    program_rate: float,
) -> QPEScenario:
    """C: Qualifies at fair market value (requires FMV documentation and EDB confirmation)."""
    qpe = contrib.fair_market_value_usd
    rebate = qpe * program_rate
    docs = [
        "Independent fair market value appraisal from qualified third party",
        "Arm's-length market comparables for same or similar services",
        "Written agreement stating FMV used as basis for QPE claim",
        "Provider acknowledgment of FMV for services rendered",
    ]
    if contrib.requires_related_party_disclosure:
        docs.append(
            "Related-party disclosure: provider relationship, ownership structure, "
            "transfer pricing analysis"
        )
    docs.append(
        "EDB written confirmation that FMV-based in-kind services qualify as QPE"
    )

    return QPEScenario(
        scenario_id="C",
        scenario_name=f"Qualifies at FMV (${contrib.fair_market_value_usd:,.0f})",
        treatment=QualifyingTreatment.QUALIFIES_AT_FMV,
        qpe_amount_usd=qpe,
        rebate_impact_usd=rebate,
        audit_risk=AuditRisk.HIGH,
        documentation_required=docs,
        edb_questions=[
            "Does the EDB Film Rebate Scheme allow in-kind post-production services "
            "to qualify as production expenditure at their fair market value, even "
            "where no cash was paid by the production?",
            "What documentation does EDB require to substantiate FMV for in-kind "
            "services (e.g. independent valuation, market comparables, signed declaration)?",
            "Are there specific related-party or arm's-length requirements that apply "
            "when the in-kind service provider is connected to the production company "
            "or to the Mauritius EDB incentive structure?",
        ],
        notes=(
            f"FMV = ${contrib.fair_market_value_usd:,.0f}. "
            "Highest QPE impact but requires EDB explicit confirmation and independent "
            "FMV appraisal. High audit risk if claimed without written EDB approval. "
            "No comparable international program confirmed to allow this treatment."
        ),
    )


def _scenario_d_reduces_qpe(
    contrib: InKindContribution,
    program_rate: float,
    base_qpe_usd: float,
) -> QPEScenario:
    """
    D: Reduces QPE — treated as government/vendor assistance offset.

    Some programs require that government grants or subsidized services
    reduce the qualifying spend base (similar to GAAP 'government assistance'
    netting). Under this treatment, the FMV of the free service is DEDUCTED
    from gross QPE.
    """
    reduction = contrib.fair_market_value_usd
    adjusted_qpe = max(0.0, base_qpe_usd - reduction)
    rebate_on_adjusted = adjusted_qpe * program_rate
    rebate_on_base = base_qpe_usd * program_rate
    rebate_impact = rebate_on_adjusted - rebate_on_base  # will be negative

    return QPEScenario(
        scenario_id="D",
        scenario_name=f"Reduces QPE (government/vendor assistance offset)",
        treatment=QualifyingTreatment.REDUCES_QPE,
        qpe_amount_usd=-reduction,          # negative: QPE is reduced
        rebate_impact_usd=rebate_impact,    # negative: rebate falls
        audit_risk=AuditRisk.MEDIUM,
        documentation_required=[
            "Documentation of in-kind value received (provider declaration)",
            "Accounting treatment: record at FMV, offset against production costs",
            "Auditor confirmation of grant/assistance accounting under IFRS/GAAP",
            "EDB written confirmation of offset requirement",
        ],
        edb_questions=[
            "Does the EDB Film Rebate Scheme require that in-kind or vendor-subsidized "
            "services be deducted from qualifying production expenditure as a form of "
            "government assistance or vendor contribution offset?",
            "Is there a 'net of subsidies' rule that reduces the QPE base by the value "
            "of any free or discounted services provided by Mauritius-based entities?",
        ],
        notes=(
            f"Base QPE: ${base_qpe_usd:,.0f}. "
            f"Deduct in-kind FMV: -${reduction:,.0f}. "
            f"Adjusted QPE: ${adjusted_qpe:,.0f}. "
            "This is the most conservative numeric treatment — worse than excluded "
            "because it actively REDUCES the rebate base. "
            "Would apply if EDB treats the in-kind as a government assistance offset."
        ),
    )


def _scenario_e_unknown(
    contrib: InKindContribution,
    program_rate: float,
) -> QPEScenario:
    """E: Unknown — EDB ruling required before any treatment can be assumed."""
    return QPEScenario(
        scenario_id="E",
        scenario_name="Unknown — EDB ruling required",
        treatment=QualifyingTreatment.UNKNOWN,
        qpe_amount_usd=0.0,          # cannot model: use $0 as placeholder
        rebate_impact_usd=0.0,
        audit_risk=AuditRisk.CRITICAL,
        documentation_required=[
            "SUBMIT EDB QUERY: Written ruling on in-kind post-production treatment",
            "Do NOT claim in-kind services in QPE submission without written EDB approval",
            "Maintain all in-kind agreements and communications for audit trail",
        ],
        edb_questions=[
            "Please provide written guidance on whether post-production services "
            "provided in-kind by a Mauritius entity (with zero cash consideration "
            f"from the production) qualify as 'production expenditure' under the "
            "EDB Film Rebate Scheme, and if so, at what value (cash paid, FMV, or other).",
            "Is a fair market value appraisal required? If so, what methodology does "
            "EDB accept?",
            "Are there related-party rules that affect treatment where the in-kind "
            "service provider has a financial relationship with the production?",
            "Does EDB require any government assistance offset or netting treatment?",
            "What is the standard audit documentation EDB expects for in-kind "
            "contribution claims?",
        ],
        notes=(
            "This is the correct treatment until written EDB guidance is received. "
            "Claiming in-kind at FMV without EDB confirmation creates CRITICAL "
            "audit risk. QPE shown as $0 placeholder — actual impact is UNKNOWN."
        ),
    )


# ── Main calculation entry point ──────────────────────────────────────────────

def analyse_inkind_contribution(
    contribution: InKindContribution,
    program_rate: float,
    base_qpe_usd: float,
) -> InKindImpactResult:
    """
    Run all five treatment scenarios for an in-kind contribution.

    Parameters
    ----------
    contribution  : The in-kind contribution to analyse
    program_rate  : Decimal rebate/credit rate (e.g. 0.35 for 35%)
    base_qpe_usd  : QPE before this contribution is considered

    Returns
    -------
    InKindImpactResult with all scenarios, documentation checklist, EDB questions
    """
    scenarios = [
        _scenario_a_excluded(contribution, program_rate),
        _scenario_b_cash_paid(contribution, program_rate),
        _scenario_c_fmv(contribution, program_rate),
        _scenario_d_reduces_qpe(contribution, program_rate, base_qpe_usd),
        _scenario_e_unknown(contribution, program_rate),
    ]

    # Collect all unique EDB questions across scenarios
    all_questions: list[str] = []
    seen: set[str] = set()
    for s in scenarios:
        for q in s.edb_questions:
            if q not in seen:
                all_questions.append(q)
                seen.add(q)

    # Master documentation checklist (union of all scenario requirements)
    all_docs: list[str] = []
    seen_docs: set[str] = set()
    for s in scenarios:
        for d in s.documentation_required:
            if d not in seen_docs:
                all_docs.append(d)
                seen_docs.add(d)

    return InKindImpactResult(
        contribution=contribution,
        program_rate=program_rate,
        base_qpe_usd=base_qpe_usd,
        scenarios=scenarios,
        international_precedents=INTERNATIONAL_PRECEDENTS,
        recommended_scenario="E",  # always UNKNOWN until EDB confirms
        edb_ruling_required=True,
        required_edb_questions=all_questions,
        documentation_checklist=all_docs,
    )


# ── Convenience constructors ──────────────────────────────────────────────────

def make_post_inkind_contribution(
    face_value_usd: float,
    description: str = "Mauritius in-kind post-production services",
) -> InKindContribution:
    """
    Factory for the standard Little Utopia in-kind post scenario.

    The services are provided by a Mauritius entity at zero cash cost
    to the production. Face value = FMV (assumed equal; no discount to
    a discount — the whole amount is free).
    """
    return InKindContribution(
        contribution_type=ContributionType.IN_KIND_SERVICE,
        description=description,
        face_value_usd=face_value_usd,
        cash_paid_usd=0.0,                     # fully free
        fair_market_value_usd=face_value_usd,  # FMV = face (assume arm's length value)
        qualifying_treatment=QualifyingTreatment.UNKNOWN,
        requires_invoice=True,
        requires_payment_proof=False,           # no payment made
        requires_fmv_support=True,
        requires_related_party_disclosure=True,  # MU entity relationship to EDB program
        source_confidence=SourceConfidence.UNKNOWN,
        notes=(
            "In-kind post-production services — Mauritius provider, zero cash. "
            "Treatment unknown under EDB Film Rebate Scheme. "
            "No explicit public rule found. EDB ruling required."
        ),
    )


# ── Budget modification opportunity model ────────────────────────────────────

@dataclass
class BudgetModificationOpportunity:
    """
    A candidate budget line that could be restructured or expanded to
    increase qualifying production expenditure under the program's rules.
    """
    account_code: str
    description: str
    current_amount_usd: float
    candidate_additional_usd: float
    why_qualifies: str
    depends_on_edb_confirmation: bool
    incremental_rebate_at_rate: float       # computed by caller
    production_value_impact: str           # qualitative
    audit_risk: AuditRisk
    notes: str


def build_lu_budget_modifications(
    program_rate: float,
    edb_confirms_post_as_qpe: bool = False,
    edb_confirms_accommodation: bool = False,
) -> list[BudgetModificationOpportunity]:
    """
    Return candidate budget modification opportunities for The Little Utopia
    that could increase MU QPE within program guidelines.

    These are ADDITIONAL spend opportunities, not free confirmations.
    Each one requires actual production expenditure.

    Parameters
    ----------
    program_rate                  : MU rebate rate (e.g. 0.35)
    edb_confirms_post_as_qpe      : If True, include MU post services expansion
    edb_confirms_accommodation    : If True, accommodation already in base; skip
    """
    opportunities: list[BudgetModificationOpportunity] = []

    def add(code, desc, current, candidate, why, needs_edb, value_impact, risk, notes=""):
        incremental_rebate = candidate * program_rate
        opportunities.append(BudgetModificationOpportunity(
            account_code=code,
            description=desc,
            current_amount_usd=current,
            candidate_additional_usd=candidate,
            why_qualifies=why,
            depends_on_edb_confirmation=needs_edb,
            incremental_rebate_at_rate=incremental_rebate,
            production_value_impact=value_impact,
            audit_risk=risk,
            notes=notes,
        ))

    # ── Post-production in Mauritius (if EDB confirms post as QPE) ──────────
    if edb_confirms_post_as_qpe:
        add("54-00", "VFX — route to MU VFX vendor (add scope in MU)",
            current=95_000, candidate=150_000,
            why="If EDB confirms post qualifies, MU-based VFX work generates 35% rebate. "
                "Expand VFX scope to include additional underwater/CGI water shots.",
            needs_edb=True, value_impact="Improved CGI water sequences",
            risk=AuditRisk.MEDIUM,
            notes="Depends on EDB post confirmation. MU has limited VFX infrastructure "
                  "but remote delivery to MU entity possible.")

        add("51-00", "Color grading — MU lab or MU-supervised (add grading days)",
            current=45_000, candidate=35_000,
            why="If post qualifies, additional grading days in/routed through MU post house.",
            needs_edb=True, value_impact="Higher color quality for theatrical delivery",
            risk=AuditRisk.MEDIUM,
            notes="MU has limited DI facilities. May need to document MU entity involvement.")

        add("52-00", "Sound design / additional MU sound work",
            current=62_000, candidate=40_000,
            why="Expand sound edit scope; route additional sound through MU-based sound editor.",
            needs_edb=True, value_impact="Richer underwater sound design",
            risk=AuditRisk.MEDIUM)

        add("53-00", "Music recording in Mauritius (score recording sessions)",
            current=55_000, candidate=60_000,
            why="If post qualifies, live orchestral recording sessions in MU qualify. "
                "MU has recording studios (and associated local musician costs qualify).",
            needs_edb=True, value_impact="Local MU musical talent, authentic regional score",
            risk=AuditRisk.LOW,
            notes="MU musicians/studios are genuinely local spend. "
                  "Strong qualifying argument even independent of post ruling.")

    # ── Marine and underwater unit expansion (always qualifies in MU) ────────
    add("31-00", "Marine Unit — additional vessel charter days",
        current=165_000, candidate=40_000,
        why="Vessel chartered from MU operator; confirmed MU qualifying spend. "
            "Additional shooting days generate more MU QPE at full 35%.",
        needs_edb=False, value_impact="Additional exterior water coverage, establishing shots",
        risk=AuditRisk.LOW,
        notes="Strongest incremental QPE category. Already confirmed. "
              "Every $1 of additional MU vessel charter = $0.35 rebate.")

    add("32-00", "Marine Unit — additional safety/support boats",
        current=35_000, candidate=15_000,
        why="MU-based safety boat operators; confirmed qualifying. "
            "Expanded unit for deeper-water shooting.",
        needs_edb=False, value_impact="Better safety coverage for underwater sequences",
        risk=AuditRisk.LOW)

    add("34-00", "Marine equipment rental — additional underwater housing/rigging",
        current=93_163, candidate=45_000,
        why="Equipment from MU/regional supplier; treated as qualifying. "
            "Additional camera housings, underwater sleds, rigging hardware.",
        needs_edb=False, value_impact="Additional camera angles in underwater sequences",
        risk=AuditRisk.LOW)

    add("35-00", "Marine fuel and consumables — additional shooting days",
        current=22_000, candidate=12_000,
        why="Fuel purchased in Mauritius; confirmed qualifying BTL spend.",
        needs_edb=False, value_impact="Supports extended marine schedule",
        risk=AuditRisk.LOW)

    # ── Local crew expansion ─────────────────────────────────────────────────
    add("40-00", "Supporting artists and extras — expand local casting",
        current=42_000, candidate=30_000,
        why="MU local talent; confirmed qualifying. More background artists for "
            "port/market/beach scenes increases MU BTL spend.",
        needs_edb=False, value_impact="More authentic MU background; adds production value",
        risk=AuditRisk.LOW)

    add("41-00", "Payroll / PAYE on expanded local crew",
        current=68_000, candidate=20_000,
        why="MU employer contributions on additional local crew all qualify. "
            "Direct consequence of any local crew expansion.",
        needs_edb=False, value_impact="Part of local crew expansion",
        risk=AuditRisk.LOW)

    add("20-00", "Additional production staff — MU-resident crew",
        current=155_000, candidate=35_000,
        why="MU-resident production management routed through MU entity; confirmed qualifying. "
            "Additional shoot days or pre-production days generate more qualifying payroll.",
        needs_edb=False, value_impact="Extended pre-production period in MU; better location prep",
        risk=AuditRisk.LOW)

    # ── Location / logistics in MU ────────────────────────────────────────────
    add("29-00", "Location fees and permits — additional MU locations",
        current=95_000, candidate=25_000,
        why="Paid to MU authorities; confirmed qualifying. "
            "Additional location permits for alternative coastal/port locations.",
        needs_edb=False, value_impact="More location variety; production design flexibility",
        risk=AuditRisk.LOW)

    add("30-00", "MU transport and ground vehicles — extended schedule",
        current=112_000, candidate=20_000,
        why="Local MU vehicle hire; confirmed qualifying. "
            "Extended shooting days require more vehicle days.",
        needs_edb=False, value_impact="Supports any schedule extension",
        risk=AuditRisk.LOW)

    # ── Frogsquad re-routing (ALREADY IN BASE; confirmed path, not additional spend)
    # Not an 'additional spend' opportunity — already in base if routed through SPV.
    # Documented separately as routing opportunity, not budget modification.

    # ── Accommodation / per diem (depends on EDB confirmation) ───────────────
    if not edb_confirms_accommodation:
        add("37-00", "HOD accommodation — confirm qualifying / extend hotel block",
            current=159_783, candidate=30_000,
            why="Accommodation in MU; qualifies in base scenario pending EDB confirmation. "
                "If EDB confirms, extending HOD hotel block for additional prep days qualifies.",
            needs_edb=True, value_impact="Allows longer pre-production period for HODs",
            risk=AuditRisk.MEDIUM,
            notes="Primary action: EDB confirmation on current $159K before adding more. "
                  "Additional $30K only makes sense once base is confirmed.")

        add("38-00", "Local crew per diems — extend qualifying days",
            current=114_130, candidate=20_000,
            why="MU local per diems; qualifies base pending EDB confirmation. "
                "Extended shoot days add more per diem qualifying days.",
            needs_edb=True, value_impact="Extended shoot schedule",
            risk=AuditRisk.MEDIUM)

    # ── Art department / production design ───────────────────────────────────
    add("26-00", "Art department — additional MU materials/construction",
        current=168_000, candidate=40_000,
        why="MU-sourced materials and labour; confirmed qualifying. "
            "Expanded set construction for underwater base set or dock sequences.",
        needs_edb=False, value_impact="Higher production value set construction",
        risk=AuditRisk.LOW)

    # ── Wardrobe / costume in MU ─────────────────────────────────────────────
    add("27-00", "Wardrobe — additional MU sourcing",
        current=72_000, candidate=20_000,
        why="Local MU sourcing and MU seamstresses; confirmed qualifying. "
            "Additional period/hero costumes sourced and made in MU.",
        needs_edb=False, value_impact="Better costuming for principal cast; local authenticity",
        risk=AuditRisk.LOW)

    # ── Catering ─────────────────────────────────────────────────────────────
    add("36-00", "Catering — extended MU catering contract",
        current=88_000, candidate=15_000,
        why="Local MU catering company; confirmed MU spend. "
            "Extended shooting schedule increases catering days.",
        needs_edb=False, value_impact="Directly tied to any schedule extension",
        risk=AuditRisk.LOW)

    return opportunities


# ── Net value comparison: MU vs Malta ────────────────────────────────────────

@dataclass
class PostJurisdictionComparison:
    """
    Net producer value comparison for two post scenarios given an in-kind treatment.
    """
    scenario_id: str
    inkind_treatment: QualifyingTreatment
    inkind_qpe_amount: float

    # MU figures
    mu_base_qpe: float
    mu_qpe_with_inkind: float
    mu_rebate: float
    mu_finance_cost: float
    mu_inkind_service_value: float   # value of service to producer (0 if loses it)
    mu_net_value: float              # rebate - finance + service_value

    # Malta post figures
    malta_mu_rebate: float           # MU production rebate (unchanged)
    malta_post_qpe: float
    malta_post_rebate: float
    malta_finance_cost: float
    malta_inkind_lost: float         # cash cost of what was free
    malta_overhead: float            # entity + travel
    malta_net_value: float

    winner: str
    margin: float                    # absolute difference
    notes: str


def compare_mu_vs_malta_post(
    scenario: QPEScenario,
    inkind_fmv: float,
    mu_base_qpe: float,
    mu_rate: float = 0.35,
    mu_delay_weeks: int = 39,
    mu_bridge_rate: float = 0.08,
    post_in_budget: float = 363_000,
    malta_rate: float = 0.40,
    malta_delay_weeks: int = 20,
    malta_overhead: float = 23_000,
) -> PostJurisdictionComparison:
    """
    Compare MU 100% vs MU production + Malta post, given one in-kind treatment scenario.

    For MU 100%: in-kind is either a service (free), reduces QPE, excluded, or adds to QPE.
    For Malta post: in-kind is gone (production now PAYS for equivalent post).
    """
    def fc(rebate, weeks):
        return rebate * mu_bridge_rate * (weeks / 52)

    total_post_scope = post_in_budget + inkind_fmv  # $363K + $625K

    # ── MU side ──────────────────────────────────────────────────────────────
    if scenario.treatment == QualifyingTreatment.QUALIFIES_AT_FMV:
        mu_qpe = mu_base_qpe + inkind_fmv
        mu_inkind_service_value = 0.0     # counted as QPE, not as free service
    elif scenario.treatment == QualifyingTreatment.QUALIFIES_AT_CASH_PAID:
        mu_qpe = mu_base_qpe + 0.0        # cash paid = 0
        mu_inkind_service_value = inkind_fmv  # still get the free service
    elif scenario.treatment == QualifyingTreatment.REDUCES_QPE:
        mu_qpe = max(0.0, mu_base_qpe - inkind_fmv)
        mu_inkind_service_value = inkind_fmv  # still get the service, but QPE falls
    elif scenario.treatment == QualifyingTreatment.EXCLUDED:
        mu_qpe = mu_base_qpe
        mu_inkind_service_value = inkind_fmv  # excluded: still get free service
    else:  # UNKNOWN
        mu_qpe = mu_base_qpe
        mu_inkind_service_value = inkind_fmv  # UNKNOWN: model as free service (conservative)

    mu_rebate = mu_qpe * mu_rate
    mu_finance = fc(mu_rebate, mu_delay_weeks)
    mu_net = mu_rebate - mu_finance + mu_inkind_service_value

    # ── Malta side ───────────────────────────────────────────────────────────
    # MU production rebate unchanged (post never in MU QPE regardless)
    malta_mu_rebate = mu_base_qpe * mu_rate
    malta_mu_finance = fc(malta_mu_rebate, mu_delay_weeks)

    malta_post_qpe = total_post_scope
    malta_post_rebate = malta_post_qpe * malta_rate
    malta_post_finance = malta_post_rebate * mu_bridge_rate * (malta_delay_weeks / 52)
    malta_inkind_lost = inkind_fmv      # must pay cash for what was free
    malta_net = (
        malta_mu_rebate - malta_mu_finance  # MU production rebate
        + malta_post_rebate - malta_post_finance  # Malta post rebate
        - malta_inkind_lost                   # lose the free service
        - malta_overhead                      # entity + travel
    )

    if mu_net >= malta_net:
        winner = "MU_100_PCT"
        margin = mu_net - malta_net
    else:
        winner = "MU_PRODUCTION_MALTA_POST"
        margin = malta_net - mu_net

    return PostJurisdictionComparison(
        scenario_id=scenario.scenario_id,
        inkind_treatment=scenario.treatment,
        inkind_qpe_amount=scenario.qpe_amount_usd,
        mu_base_qpe=mu_base_qpe,
        mu_qpe_with_inkind=mu_qpe,
        mu_rebate=mu_rebate,
        mu_finance_cost=mu_finance,
        mu_inkind_service_value=mu_inkind_service_value,
        mu_net_value=mu_net,
        malta_mu_rebate=malta_mu_rebate,
        malta_post_qpe=malta_post_qpe,
        malta_post_rebate=malta_post_rebate,
        malta_finance_cost=malta_post_finance,
        malta_inkind_lost=malta_inkind_lost,
        malta_overhead=malta_overhead,
        malta_net_value=malta_net,
        winner=winner,
        margin=margin,
        notes=scenario.notes,
    )
