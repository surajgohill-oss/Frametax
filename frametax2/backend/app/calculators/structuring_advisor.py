"""
structuring_advisor.py

Producer Structuring Advisor — deterministic advisory layer.

The optimizer selects the best jurisdiction.
This module teaches the system HOW to legally structure the production
to maximise qualification within that jurisdiction's published rules.

Not tax avoidance. Every recommendation must be:
  (a) commercially realistic
  (b) legally supportable, and
  (c) consistent with published incentive rules OR clearly identified as
      requiring official program interpretation.

Each recommendation is classified:
  EXPLICITLY_PERMITTED     — permitted by published statutory guidance
  INDUSTRY_STANDARD        — accepted commercial structure; no rule prohibits it
  REQUIRES_INTERPRETATION  — permitted only if program authority confirms
  UNKNOWN                  — cannot be classified from available public sources

No LLM calls. No DB access. Deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

ADVISOR_VERSION = "1.0.0"


# ── Classification enumerations ───────────────────────────────────────────────

class RecommendationConfidence(str, Enum):
    EXPLICITLY_PERMITTED    = "explicitly_permitted"
    INDUSTRY_STANDARD       = "industry_standard"
    REQUIRES_INTERPRETATION = "requires_interpretation"
    UNKNOWN                 = "unknown"


class ImplementationDifficulty(str, Enum):
    LOW    = "low"     # no external approvals; production decision only
    MEDIUM = "medium"  # minor restructuring, advisors needed
    HIGH   = "high"    # significant structural change; legal/accounting required


class TimeHorizon(str, Enum):
    IMMEDIATE   = "immediate"    # implement now; no approvals required
    MEDIUM_TERM = "medium_term"  # plan during prep; some lead time
    EDB_FIRST   = "edb_first"    # obtain EDB written ruling before acting
    LONG_TERM   = "long_term"    # next production or series


class TransactionType(str, Enum):
    SPV_ROUTING               = "spv_routing"
    ARM_LENGTH_INVOICE        = "arm_length_invoice"
    DEFERRED_PAYMENT          = "deferred_payment"
    FMV_DOCUMENTATION         = "fmv_documentation"
    EQUITY_CONTRIBUTION       = "equity_contribution"
    VENDOR_FINANCING          = "vendor_financing"
    LOCAL_HIRE_EXPANSION      = "local_hire_expansion"
    ADDITIONAL_LOCAL_SPEND    = "additional_local_spend"
    SERVICE_AGREEMENT         = "service_agreement"
    INDEPENDENT_VALUATION     = "independent_valuation"
    RELATED_PARTY_DISCLOSURE  = "related_party_disclosure"
    POST_RELOCATION           = "post_relocation"
    VFX_RELOCATION            = "vfx_relocation"
    MUSIC_RELOCATION          = "music_relocation"
    EDITORIAL_RELOCATION      = "editorial_relocation"
    BROADCASTER_ATTACHMENT    = "broadcaster_attachment"
    REGIONAL_COPRODUCER       = "regional_coproducer"
    PRODUCER_ADVANCE          = "producer_advance"
    EDB_RULING_REQUEST        = "edb_ruling_request"


class AuditRisk(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


# ── Core recommendation dataclass ─────────────────────────────────────────────

@dataclass
class StructuringRecommendation:
    """
    One producer structuring recommendation.

    financial_impact_usd         — direct cash value (rebate uplift, savings, etc.)
    qualification_impact_usd     — additional QPE this creates (pre-rate)
    rebate_impact_usd            — qualification_impact × program_rate
    """
    recommendation_id: str
    title: str
    time_horizon: TimeHorizon
    transaction_type: TransactionType
    current_structure: str
    suggested_structure: str
    reason: str
    financial_impact_usd: float           # net producer cash value (positive = benefit)
    qualification_impact_usd: float       # additional QPE created
    rebate_impact_usd: float              # rebate uplift from qualification_impact
    required_documentation: list[str]
    audit_risk: AuditRisk
    confidence: RecommendationConfidence
    implementation_difficulty: ImplementationDifficulty
    published_support: Optional[str]           # citation if explicitly permitted
    requires_official_interpretation: bool
    interpretation_body: Optional[str]         # e.g. "Mauritius EDB"
    interpretation_question: Optional[str]     # exact question to ask
    notes: str = ""


# ── Advisory result container ─────────────────────────────────────────────────

@dataclass
class StructuringAdvisoryResult:
    production_title: str
    jurisdiction_code: str
    program_rate: float
    advisor_version: str

    # Aggregates by horizon
    total_immediate_rebate_uplift: float      # sum of IMMEDIATE confirmed rebate gains
    total_medium_term_rebate_uplift: float    # sum of MEDIUM_TERM confirmed rebate gains
    total_edb_conditional_rebate_uplift: float  # sum if EDB confirms (REQUIRES_INTERPRETATION)
    total_potential_rebate_uplift: float      # all of the above combined

    recommendations: list[StructuringRecommendation]

    # Items that cannot be determined without official clarification
    unknown_items: list[str]
    edb_questions: list[str]   # deduplicated list of questions to submit to EDB


# ── Little Utopia production parameters ──────────────────────────────────────

@dataclass
class LittleUtopiaParams:
    """
    Production parameters for The Little Utopia (Mauritius baseline).
    All amounts USD.
    """
    gross_budget_usd: float = 4_364_393.0
    atl_total_usd: float = 538_444.0
    # QPE figures are calculator-verified (calculate_qpe() against the real
    # little_utopia_sanitized.py fixture, 40 non-memo accounts) — not plugs.
    # qpe_base_usd = the CONSERVATIVE scenario ($1,551,163): frogsquad/HOD
    # accommodation/local per-diems are NOT yet counted here, consistent with
    # frogsquad_usd/hod_accom_usd/local_perdiem_usd below being modeled as
    # incremental upside pending SPV routing / EDB confirmation.
    qpe_conservative_usd: float = 1_551_163.0
    qpe_base_usd: float = 1_551_163.0
    qpe_optimistic_usd: float = 2_596_357.0
    mu_rebate_rate: float = 0.40  # EDB official programme page: "up to 40%" (edbmauritius.org)
    mu_delay_weeks: int = 39
    bridge_rate: float = 0.08

    # Key contested accounts
    frogsquad_usd: float = 99_837.0      # 33-00 — excluded conservative; base if SPV routed
    hod_accom_usd: float = 159_783.0     # 37-00 — excluded conservative; base if EDB confirms
    local_perdiem_usd: float = 114_130.0 # 38-00 — excluded conservative; base if EDB confirms
    post_in_budget_usd: float = 363_000.0  # 50-55 — excluded all scenarios

    # In-kind post-production
    inkind_low_usd: float = 500_000.0
    inkind_base_usd: float = 625_000.0
    inkind_high_usd: float = 750_000.0

    # Marine cluster (confirmed qualifying)
    marine_cluster_usd: float = 415_000.0

    # Team
    writer_nationality: str = "GB"
    director_nationality: str = "AU"   # previously verified
    lead_nationality: str = "GB"       # Luke Evans
    producer_nationalities: list[str] = field(
        default_factory=lambda: ["GB", "CA", "US"]
    )


# ── Finance cost helper ───────────────────────────────────────────────────────

def _finance_cost(rebate: float, weeks: int, rate: float) -> float:
    return rebate * rate * (weeks / 52.0)


# ── Recommendation builders ───────────────────────────────────────────────────

def _r_spv_frogsquad(p: LittleUtopiaParams) -> StructuringRecommendation:
    """Route Frogsquad (SA dive team) payments through MU local SPV."""
    qpe_delta = p.frogsquad_usd
    rebate_delta = qpe_delta * p.mu_rebate_rate
    return StructuringRecommendation(
        recommendation_id="R-01",
        title="Frogsquad SA dive team — route payment through MU SPV",
        time_horizon=TimeHorizon.IMMEDIATE,
        transaction_type=TransactionType.SPV_ROUTING,
        current_structure=(
            "Frogsquad SA (South Africa) invoiced directly by UK production company. "
            "Payment made to SA entity. No MU entity in the chain. "
            "Conservative QPE: excluded ($0 MU-qualifying)."
        ),
        suggested_structure=(
            "Frogsquad SA contracted by the MU local production service company (SPV). "
            "MU SPV sub-contracts Frogsquad; production pays the MU SPV in MUR/USD. "
            "MU SPV invoices production at arm's length for marine/dive services. "
            "No economic substance changed — same dive team, same work — but the "
            "contractual counterparty is the MU entity."
        ),
        reason=(
            "The EDB Film Rebate Scheme qualifies expenditure incurred by or through "
            "the qualifying MU production entity. If Frogsquad's services are "
            "contracted by the MU SPV and the production's cash flows through the MU "
            "entity, the expenditure has a MU nexus. This is the industry-standard "
            "local production services company structure used worldwide to channel "
            "international vendor spend through the qualifying local entity."
        ),
        financial_impact_usd=rebate_delta,
        qualification_impact_usd=qpe_delta,
        rebate_impact_usd=rebate_delta,
        required_documentation=[
            "MU SPV service agreement covering all marine/dive services",
            "Frogsquad SA sub-contract from MU SPV at arm's-length rate",
            "MU SPV invoices to production company at agreed fee",
            "Bank records: production → MU SPV → Frogsquad SA payment chain",
            "MU SPV board resolution authorising sub-contracting arrangement",
        ],
        audit_risk=AuditRisk.MEDIUM,
        confidence=RecommendationConfidence.INDUSTRY_STANDARD,
        implementation_difficulty=ImplementationDifficulty.MEDIUM,
        published_support=(
            "EDB Film Rebate: qualifying spend must be incurred by the approved "
            "MU production entity. Local service company structures are the standard "
            "mechanism for this in international productions (UK HETV, Australia, "
            "NZ, Ireland all accept SPV routing for international vendor payments)."
        ),
        requires_official_interpretation=True,
        interpretation_body="Mauritius EDB",
        interpretation_question=(
            "Does sub-contracting a non-MU vendor (e.g. SA dive team) through the "
            "MU local production service company qualify the full payment amount as "
            "MU production expenditure under the EDB Film Rebate Scheme, provided "
            "the MU entity invoices the production at arm's length and payment flows "
            "through the MU entity?"
        ),
        notes=(
            f"QPE uplift: ${qpe_delta:,.0f} (conservative→base swing). "
            f"Rebate uplift: ${rebate_delta:,.0f}. "
            "Already modelled as qualifying in base scenario — this recommendation "
            "formalises the structure and obtains EDB confirmation before filing."
        ),
    )


def _r_edb_confirm_accommodation(p: LittleUtopiaParams) -> StructuringRecommendation:
    """Obtain EDB written confirmation that HOD accommodation in MU qualifies as QPE."""
    qpe_delta = p.hod_accom_usd
    rebate_delta = qpe_delta * p.mu_rebate_rate
    return StructuringRecommendation(
        recommendation_id="R-02",
        title="HOD accommodation in MU — obtain EDB written QPE confirmation",
        time_horizon=TimeHorizon.EDB_FIRST,
        transaction_type=TransactionType.EDB_RULING_REQUEST,
        current_structure=(
            f"${p.hod_accom_usd:,.0f} HOD accommodation invoiced from MU hotels. "
            "Spent in Mauritius. Excluded from conservative QPE scenario pending EDB "
            "confirmation. Included in base scenario as plausible MU qualifying spend."
        ),
        suggested_structure=(
            "Submit written EDB query to confirm accommodation costs for imported "
            "HODs staying in Mauritius qualify as production expenditure under the "
            "EDB Film Rebate Scheme. Once confirmed: include at full $159,783 in QPE "
            "submission with hotel invoices and payment confirmations."
        ),
        reason=(
            "MU hotel accommodation is paid to MU hotel operators — it is genuine "
            "MU expenditure. Most comparable programs (UK, Ireland, Canada, Australia) "
            "allow accommodation costs paid within the qualifying jurisdiction. "
            "However, without EDB written confirmation the conservative treatment "
            "excludes it. EDB confirmation converts this from base-scenario to "
            "confirmed qualifying spend, reducing audit risk from MEDIUM to LOW."
        ),
        financial_impact_usd=rebate_delta,
        qualification_impact_usd=qpe_delta,
        rebate_impact_usd=rebate_delta,
        required_documentation=[
            "EDB written ruling confirming accommodation qualifies as QPE",
            "Hotel invoices for all HOD accommodation (MU hotel, USD/MUR)",
            "Crew list matching accommodation bookings to production crew",
            "Payment confirmation from production entity to hotel",
        ],
        audit_risk=AuditRisk.MEDIUM,
        confidence=RecommendationConfidence.REQUIRES_INTERPRETATION,
        implementation_difficulty=ImplementationDifficulty.LOW,
        published_support=None,
        requires_official_interpretation=True,
        interpretation_body="Mauritius EDB",
        interpretation_question=(
            "Do accommodation costs paid to Mauritius hotels for imported HODs and "
            "cast during principal photography in Mauritius qualify as 'production "
            "expenditure' under the EDB Film Rebate Scheme?"
        ),
        notes=(
            f"QPE at stake: ${qpe_delta:,.0f}. "
            f"Rebate at stake: ${rebate_delta:,.0f}. "
            "Lowest effort, highest certainty path — submit EDB query in pre-production."
        ),
    )


def _r_edb_confirm_perdiem(p: LittleUtopiaParams) -> StructuringRecommendation:
    """Obtain EDB written confirmation that local crew per diems in MU qualify as QPE."""
    qpe_delta = p.local_perdiem_usd
    rebate_delta = qpe_delta * p.mu_rebate_rate
    return StructuringRecommendation(
        recommendation_id="R-03",
        title="Local crew per diems in MU — obtain EDB written QPE confirmation",
        time_horizon=TimeHorizon.EDB_FIRST,
        transaction_type=TransactionType.EDB_RULING_REQUEST,
        current_structure=(
            f"${p.local_perdiem_usd:,.0f} per diems paid to 50 local MU crew over 42 shoot days "
            "(2,500 MUR/day). Paid in MUR to MU residents. Excluded conservative scenario. "
            "Included base/optimistic as plausible MU qualifying spend."
        ),
        suggested_structure=(
            "Submit written EDB query confirming per diems paid to MU-resident crew "
            "qualify as production expenditure. Once confirmed: include in QPE "
            "submission with signed per-diem schedules and payment records."
        ),
        reason=(
            "Per diems paid to local MU crew are genuine MU labour costs — paid to "
            "MU residents, in MUR, for work performed in Mauritius. The question is "
            "whether the EDB program classifies per diems as qualifying labour cost "
            "or as a living allowance (which some programs exclude). EDB written "
            "confirmation eliminates audit risk at low cost."
        ),
        financial_impact_usd=rebate_delta,
        qualification_impact_usd=qpe_delta,
        rebate_impact_usd=rebate_delta,
        required_documentation=[
            "EDB written ruling confirming per diems to local MU crew qualify",
            "Per-diem schedule signed by MU crew members",
            "Payroll records showing per-diem component separately from base salary",
            "MU resident status confirmation for all per-diem recipients",
        ],
        audit_risk=AuditRisk.MEDIUM,
        confidence=RecommendationConfidence.REQUIRES_INTERPRETATION,
        implementation_difficulty=ImplementationDifficulty.LOW,
        published_support=None,
        requires_official_interpretation=True,
        interpretation_body="Mauritius EDB",
        interpretation_question=(
            "Do per diem payments to Mauritius-resident crew members for days worked "
            "on the production in Mauritius qualify as 'production expenditure' under "
            "the EDB Film Rebate Scheme?"
        ),
        notes=(
            f"QPE at stake: ${qpe_delta:,.0f}. "
            f"Rebate at stake: ${rebate_delta:,.0f}. "
            "Combined with HOD accommodation (R-02), these two EDB queries together "
            f"represent ${(qpe_delta + p.hod_accom_usd) * p.mu_rebate_rate:,.0f} "
            "in potential rebate — the highest-ROI pre-production task."
        ),
    )


def _r_inkind_fmv_structure(p: LittleUtopiaParams) -> StructuringRecommendation:
    """
    Structure in-kind post-production as an arm's-length invoiced deferred
    payment arrangement if EDB will not recognise pure in-kind at FMV.
    """
    fmv = p.inkind_base_usd
    rebate_if_qualifies = fmv * p.mu_rebate_rate
    return StructuringRecommendation(
        recommendation_id="R-04",
        title="In-kind post-production — structure as arm's-length invoiced deferred payment",
        time_horizon=TimeHorizon.EDB_FIRST,
        transaction_type=TransactionType.DEFERRED_PAYMENT,
        current_structure=(
            f"${fmv:,.0f} MU post-production services provided in-kind at zero cash. "
            "No cash flows from production to MU post provider. "
            "QPE treatment: UNKNOWN under EDB rules. Conservative/base/optimistic "
            "all exclude post from QPE (services not modelled as QPE in any scenario)."
        ),
        suggested_structure=(
            "If EDB confirms in-kind at FMV does NOT qualify: restructure as a "
            "deferred payment agreement. MU post provider invoices production at "
            f"arm's-length market rate (${fmv:,.0f}). Production acknowledges "
            "liability. Payment deferred to post rebate receipt. Provider accepts "
            "deferred consideration; rebate covers the payment. This converts a "
            "gratuitous service into a qualifying invoiced transaction."
        ),
        reason=(
            "A deferred payment is a legally binding obligation — production "
            "owes the debt; it is just timed to the rebate receipt. This structure "
            "is used in Ireland (S481 deferred payment tax credit), UK (HETV tax "
            "credit cashflow), Australia (PDV offset financing) — all recognise "
            "invoiced amounts as qualifying even when cash payment is deferred. "
            "The key requirement: arm's-length rate, genuine commercial service, "
            "legally binding invoice with payment obligation. No EDB rule has been "
            "found that PROHIBITS this — but EDB confirmation is required."
        ),
        financial_impact_usd=rebate_if_qualifies,
        qualification_impact_usd=fmv,
        rebate_impact_usd=rebate_if_qualifies,
        required_documentation=[
            "Arm's-length FMV appraisal of post-production services (independent valuer)",
            "Invoiced service agreement: MU post provider → production entity",
            "Deferred payment schedule tied to EDB rebate receipt date",
            "Signed acknowledgment of payment obligation by production",
            "Related-party disclosure (if MU post provider is connected to EDB structure)",
            "EDB written ruling confirming invoiced deferred post services qualify",
            "Bank confirmation when deferred payment is settled",
        ],
        audit_risk=AuditRisk.HIGH,
        confidence=RecommendationConfidence.REQUIRES_INTERPRETATION,
        implementation_difficulty=ImplementationDifficulty.HIGH,
        published_support=None,
        requires_official_interpretation=True,
        interpretation_body="Mauritius EDB",
        interpretation_question=(
            "Does the EDB Film Rebate Scheme recognise an invoiced but deferred "
            "payment obligation for post-production services performed by a "
            "Mauritius entity as qualifying production expenditure, where the "
            "invoice is at arm's-length fair market value and payment is deferred "
            "to the point of rebate receipt?"
        ),
        notes=(
            f"Base FMV: ${fmv:,.0f}. Rebate if qualifies: ${rebate_if_qualifies:,.0f}. "
            "IMPORTANT: this recommendation only applies if EDB says pure in-kind "
            "at FMV does NOT qualify. If EDB says FMV-in-kind DOES qualify (R-05), "
            "this restructuring is unnecessary. Pursue R-05 first."
        ),
    )


def _r_inkind_fmv_ruling(p: LittleUtopiaParams) -> StructuringRecommendation:
    """Request EDB ruling on whether in-kind post at FMV qualifies."""
    fmv = p.inkind_base_usd
    rebate_if_qualifies = fmv * p.mu_rebate_rate
    return StructuringRecommendation(
        recommendation_id="R-05",
        title="In-kind post-production at FMV — request EDB written ruling",
        time_horizon=TimeHorizon.EDB_FIRST,
        transaction_type=TransactionType.EDB_RULING_REQUEST,
        current_structure=(
            f"${fmv:,.0f} MU post-production in-kind. No EDB public rule on treatment. "
            "International standard: in-kind at FMV does NOT qualify. "
            "Engine treatment: UNKNOWN. QPE contribution: $0 (conservative)."
        ),
        suggested_structure=(
            "Submit formal EDB written query before filing QPE submission. "
            "Request ruling on: (a) does in-kind qualify at FMV, (b) does in-kind "
            "qualify at cash paid ($0), (c) does in-kind REDUCE QPE as government "
            "assistance offset, or (d) is treatment neutral (excluded, no impact). "
            "Base further structuring decisions (R-04 deferred payment) on EDB response."
        ),
        reason=(
            "This is THE critical unanswered question for the production. "
            "If EDB rules FMV qualifies: +$218,750 rebate, no restructuring needed. "
            "If EDB rules cash paid: +$0 rebate but no audit risk. "
            "If EDB rules reduces QPE: -$218,750 — the worst outcome. "
            "The only way to eliminate CRITICAL audit risk is a written EDB ruling "
            "BEFORE filing the QPE submission. No comparable program allows FMV "
            "in-kind at QPE without explicit statutory authority."
        ),
        financial_impact_usd=rebate_if_qualifies,   # upside if FMV ruling obtained
        qualification_impact_usd=fmv,
        rebate_impact_usd=rebate_if_qualifies,
        required_documentation=[
            "Written EDB query letter describing the in-kind arrangement in full",
            "Description of MU post provider relationship to production",
            "Independent FMV appraisal to support the ruling request",
            "Copy of the in-kind service agreement",
            "Related-party relationship disclosure",
        ],
        audit_risk=AuditRisk.CRITICAL,  # if filed without ruling
        confidence=RecommendationConfidence.UNKNOWN,
        implementation_difficulty=ImplementationDifficulty.LOW,
        published_support=None,
        requires_official_interpretation=True,
        interpretation_body="Mauritius EDB",
        interpretation_question=(
            "Please provide written guidance on whether post-production services "
            "provided to the production in-kind by a Mauritius entity at zero cash "
            "consideration qualify as 'production expenditure' under the EDB Film "
            "Rebate Scheme, and if so, at what value: (a) fair market value, "
            "(b) cash actually paid, (c) no value (excluded), or "
            "(d) reduces gross qualifying expenditure as a form of government assistance?"
        ),
        notes=(
            "This is Question #1 to submit to EDB. The answer determines whether "
            "R-04 (deferred payment restructuring) is necessary. Submit this first."
        ),
    )


def _r_marine_expansion(p: LittleUtopiaParams) -> StructuringRecommendation:
    """Expand marine unit spend — confirmed MU qualifying, no EDB required."""
    candidate_additional = 112_000.0   # vessel + safety + equipment + fuel (see inkind_contribution)
    rebate_delta = candidate_additional * p.mu_rebate_rate
    return StructuringRecommendation(
        recommendation_id="R-06",
        title="Marine unit expansion — additional confirmed-qualifying MU spend",
        time_horizon=TimeHorizon.IMMEDIATE,
        transaction_type=TransactionType.ADDITIONAL_LOCAL_SPEND,
        current_structure=(
            f"Marine cluster: ${p.marine_cluster_usd:,.0f} (vessels, safety boats, "
            "equipment, fuel) — all confirmed MU-qualifying. "
            "Current schedule: estimated 28 marine unit days."
        ),
        suggested_structure=(
            "Expand marine shooting schedule by additional days. "
            "Additional charter days (31-00: +$40K), additional safety boats (32-00: +$15K), "
            "additional underwater equipment (34-00: +$45K), additional fuel (35-00: +$12K). "
            f"Total additional: ${candidate_additional:,.0f}. "
            "No EDB confirmation required — marine/vessel costs are confirmed qualifying."
        ),
        reason=(
            "Marine unit expenditure paid to MU vessel operators is the strongest "
            "confirmed QPE category for this production. Every additional dollar of "
            "MU vessel charter generates $0.35 in rebate with LOW audit risk. "
            "Expanding the marine schedule also produces genuine production value: "
            "additional establishing shots, more underwater coverage, larger safety margin."
        ),
        financial_impact_usd=rebate_delta,
        qualification_impact_usd=candidate_additional,
        rebate_impact_usd=rebate_delta,
        required_documentation=[
            "Updated vessel charter agreement with additional shooting days",
            "Amended production schedule showing extended marine days",
            "Invoices from MU vessel operator for all additional days",
            "Safety boat charter agreements for expanded dates",
            "Equipment rental invoices from MU supplier",
        ],
        audit_risk=AuditRisk.LOW,
        confidence=RecommendationConfidence.EXPLICITLY_PERMITTED,
        implementation_difficulty=ImplementationDifficulty.LOW,
        published_support=(
            "Marine/vessel expenditure incurred from MU operators confirmed in budget "
            "QPE analysis as MU-qualifying spend. No EDB interpretation required for "
            "direct MU vendor payments for services performed in Mauritius."
        ),
        requires_official_interpretation=False,
        interpretation_body=None,
        interpretation_question=None,
        notes=(
            f"Incremental rebate: ${rebate_delta:,.0f}. "
            "Best ROI of any budget expansion with zero EDB dependency. "
            "Requires production decision to expand shooting schedule."
        ),
    )


def _r_local_crew_expansion(p: LittleUtopiaParams) -> StructuringRecommendation:
    """Expand local MU crew — confirmed qualifying, no EDB required."""
    candidate_additional = 105_000.0  # extras + payroll + staff + art dept + wardrobe + catering
    rebate_delta = candidate_additional * p.mu_rebate_rate
    return StructuringRecommendation(
        recommendation_id="R-07",
        title="Local MU crew and production services expansion",
        time_horizon=TimeHorizon.IMMEDIATE,
        transaction_type=TransactionType.LOCAL_HIRE_EXPANSION,
        current_structure=(
            "Local MU crew: extras ($42K), payroll/PAYE ($68K), production staff ($155K), "
            "art dept ($168K), wardrobe ($72K), catering ($88K). "
            "All confirmed MU-qualifying. Fixed by current production schedule."
        ),
        suggested_structure=(
            "Expand local crew-dependent spend: additional MU extras/background (+$30K), "
            "additional payroll on expanded crew (+$20K), additional MU-resident "
            "production staff (+$35K), additional art dept MU materials (+$40K). "
            f"Total additional: ${candidate_additional:,.0f}. No EDB approval needed."
        ),
        reason=(
            "Local MU crew and production services are the core qualifying spend "
            "for the MU Film Rebate. Wages paid to MU-resident crew, materials "
            "sourced from MU suppliers, and catering from MU companies all clearly "
            "qualify under any reasonable interpretation. Expanding these categories "
            "directly increases QPE with zero EDB risk."
        ),
        financial_impact_usd=rebate_delta,
        qualification_impact_usd=candidate_additional,
        rebate_impact_usd=rebate_delta,
        required_documentation=[
            "Expanded crew list with MU-resident crew members identified",
            "Updated payroll records for all additional MU crew",
            "MU business registration/receipt for art department suppliers",
            "Catering invoices from MU company for extended days",
        ],
        audit_risk=AuditRisk.LOW,
        confidence=RecommendationConfidence.EXPLICITLY_PERMITTED,
        implementation_difficulty=ImplementationDifficulty.LOW,
        published_support=(
            "MU crew wages and MU supplier payments confirmed as core qualifying "
            "expenditure for MU Film Rebate (standard BTL qualifying spend)."
        ),
        requires_official_interpretation=False,
        interpretation_body=None,
        interpretation_question=None,
        notes=(
            f"Incremental rebate: ${rebate_delta:,.0f}. "
            "Combines naturally with marine expansion (R-06) — extended schedule "
            "drives both more marine days and more crew days."
        ),
    )


def _r_music_recording_mu(p: LittleUtopiaParams) -> StructuringRecommendation:
    """Score recording sessions in Mauritius — qualifies if post QPE confirmed."""
    candidate = 60_000.0
    rebate = candidate * p.mu_rebate_rate
    return StructuringRecommendation(
        recommendation_id="R-08",
        title="Score recording in Mauritius — local musician sessions",
        time_horizon=TimeHorizon.MEDIUM_TERM,
        transaction_type=TransactionType.MUSIC_RELOCATION,
        current_structure=(
            "Music budget: $55,000 (53-00). Post-production — excluded from MU QPE "
            "in all scenarios. Score recording location not specified."
        ),
        suggested_structure=(
            "Record orchestral/score sessions in Mauritius with MU musicians. "
            "MU has recording studios. MU musician fees are paid in MUR to "
            "MU residents — this is a direct MU labour payment independent of "
            "post-production QPE ruling. Studio rental paid to MU facility. "
            f"Candidate additional: ${candidate:,.0f}."
        ),
        reason=(
            "MU musician fees and MU studio rental are direct MU payments — "
            "they are NOT post-production in the traditional sense (no digital "
            "edit/colour/VFX); they are performance services rendered in Mauritius. "
            "This may qualify as production BTL spend (music dept) rather than "
            "as post-production, depending on EDB account classification. "
            "Strongest qualifying argument independent of the post-QPE ruling."
        ),
        financial_impact_usd=rebate,
        qualification_impact_usd=candidate,
        rebate_impact_usd=rebate,
        required_documentation=[
            "MU studio rental agreement",
            "MU musician contracts (MU-resident performers)",
            "Session producer invoices from MU entity",
            "Recording schedule documenting MU location",
        ],
        audit_risk=AuditRisk.LOW,
        confidence=RecommendationConfidence.INDUSTRY_STANDARD,
        implementation_difficulty=ImplementationDifficulty.MEDIUM,
        published_support=(
            "Music recording sessions with local performers in the qualifying "
            "jurisdiction accepted as qualifying local spend in UK, Ireland, "
            "Canada, Australia, New Zealand incentive programs."
        ),
        requires_official_interpretation=True,
        interpretation_body="Mauritius EDB",
        interpretation_question=(
            "Do music recording session fees paid to Mauritius-resident musicians "
            "and to a Mauritius recording studio qualify as production expenditure "
            "under the EDB Film Rebate Scheme, independent of whether post-production "
            "in general qualifies?"
        ),
        notes=(
            f"Rebate: ${rebate:,.0f}. Low audit risk even without post ruling "
            "because musician fees are a direct local labour payment."
        ),
    )


def _r_atl_edb_ruling(p: LittleUtopiaParams) -> StructuringRecommendation:
    """
    Request EDB ruling on ATL fee qualifying scope — could unlock
    $538K of additional QPE if routed through MU entity.
    """
    atl = p.atl_total_usd
    rebate_potential = atl * p.mu_rebate_rate
    return StructuringRecommendation(
        recommendation_id="R-09",
        title="ATL fees — EDB ruling on qualifying scope when paid through MU entity",
        time_horizon=TimeHorizon.MEDIUM_TERM,
        transaction_type=TransactionType.SERVICE_AGREEMENT,
        current_structure=(
            f"ATL total: ${atl:,.0f} (story/screenplay $85K, director fee $175K, "
            "producer fees $148K, lead cast $130K). "
            "Currently excluded conservative/base; included optimistic only for "
            "director + writer fees. Lead cast excluded all scenarios. "
            "No EDB guidance found on ATL qualifying scope."
        ),
        suggested_structure=(
            "Route director and writer service fees through MU entity (production "
            "service company). Director and writer contracted by MU SPV; "
            "MU SPV invoices UK production entity. If EDB accepts: director fee "
            "($175K) and writer fee ($85K) qualify — incremental $260K QPE. "
            "Producer fees ($148K) potentially qualify via same routing. "
            "Cast ($130K) — excluded even optimistic; no comparables support cast "
            "fee qualification in MU for non-resident cast."
        ),
        reason=(
            "Director and writer are the creative services most commonly included "
            "in qualifying spend by international programs. UK, Ireland, Canada, "
            "Australia all include creative fees paid through the qualifying entity. "
            "MU SPV routing makes the contractual counterparty the MU entity, "
            "which is the standard qualification mechanism. "
            "This is a medium-term opportunity — implement if EDB post-production "
            "confirmation (R-05) is favourable."
        ),
        financial_impact_usd=rebate_potential * 0.5,  # conservative: only dir+writer
        qualification_impact_usd=260_000.0,           # director + writer fees
        rebate_impact_usd=260_000.0 * p.mu_rebate_rate,
        required_documentation=[
            "MU SPV service agreement for director and writer services",
            "Director service contract with MU SPV as counterparty",
            "Writer service contract with MU SPV as counterparty",
            "EDB written confirmation that ATL creative fees qualify",
            "Immigration records confirming work performed in relation to MU production",
        ],
        audit_risk=AuditRisk.MEDIUM,
        confidence=RecommendationConfidence.REQUIRES_INTERPRETATION,
        implementation_difficulty=ImplementationDifficulty.MEDIUM,
        published_support=None,
        requires_official_interpretation=True,
        interpretation_body="Mauritius EDB",
        interpretation_question=(
            "Do director and writer service fees paid through the approved MU "
            "production entity qualify as production expenditure under the EDB "
            "Film Rebate Scheme when the creative services relate to a production "
            "principally shot in Mauritius?"
        ),
        notes=(
            "Conservative estimate: director + writer only = $260K QPE, "
            f"${260_000 * p.mu_rebate_rate:,.0f} rebate. Full ATL (ex-cast) = "
            f"${(atl - 130_000) * p.mu_rebate_rate:,.0f}. "
            "Lower priority than R-02/R-03/R-05 — pursue after EDB post ruling."
        ),
    )


def _r_related_party_disclosure(p: LittleUtopiaParams) -> StructuringRecommendation:
    """Ensure all related-party transactions are documented at arm's length."""
    return StructuringRecommendation(
        recommendation_id="R-10",
        title="Related-party transactions — arm's-length documentation protocol",
        time_horizon=TimeHorizon.IMMEDIATE,
        transaction_type=TransactionType.RELATED_PARTY_DISCLOSURE,
        current_structure=(
            "No formal arm's-length documentation protocol in place. "
            "Related-party risk highest for: MU SPV arrangements (R-01), "
            "in-kind post provider relationship (R-05), ATL fee routing (R-09)."
        ),
        suggested_structure=(
            "Establish arm's-length documentation for all transactions between "
            "connected entities: (a) MU SPV ↔ UK production — transfer pricing "
            "analysis, (b) in-kind post provider ↔ production — independent FMV "
            "appraisal, (c) any shared services — market rate benchmarking. "
            "Appoint independent MU accountant to certify arm's-length compliance."
        ),
        reason=(
            "EDB Film Rebate claims are subject to audit. Any transaction between "
            "connected parties that is NOT at arm's length creates CRITICAL audit "
            "risk — the EDB may disallow the expenditure or require repayment. "
            "Proactive arm's-length documentation is required by virtually all "
            "film incentive programs and is standard industry practice."
        ),
        financial_impact_usd=0.0,   # no direct rebate impact
        qualification_impact_usd=0.0,
        rebate_impact_usd=0.0,
        required_documentation=[
            "Transfer pricing analysis for all MU SPV transactions",
            "Independent FMV appraisal for in-kind services",
            "Market rate benchmarking for all shared services",
            "MU accountant certification of arm's-length compliance",
            "Board resolution confirming arm's-length policy",
        ],
        audit_risk=AuditRisk.LOW,     # LOW if done proactively; CRITICAL if not done
        confidence=RecommendationConfidence.EXPLICITLY_PERMITTED,
        implementation_difficulty=ImplementationDifficulty.MEDIUM,
        published_support=(
            "Related-party arm's-length documentation is a standard requirement "
            "of all film incentive programs globally (UK HMRC CTM89600, ATO TR2014/6, "
            "CRA IC 87-2R). EDB Film Rebate subject to audit; proper documentation "
            "is prerequisite to any QPE claim involving connected parties."
        ),
        requires_official_interpretation=False,
        interpretation_body=None,
        interpretation_question=None,
        notes=(
            "Zero rebate impact on its own — but failure to implement this "
            "jeopardises ALL other recommendations. This is not optional. "
            "Implement immediately, in parallel with all other actions."
        ),
    )


def _r_edb_pre_production_meeting(p: LittleUtopiaParams) -> StructuringRecommendation:
    """Pre-production EDB meeting to obtain binding clarifications."""
    edb_runnable = (
        (p.hod_accom_usd + p.local_perdiem_usd + p.frogsquad_usd) * p.mu_rebate_rate
        + p.inkind_base_usd * p.mu_rebate_rate  # if FMV confirmed
    )
    return StructuringRecommendation(
        recommendation_id="R-11",
        title="Pre-production EDB meeting — obtain binding written clarifications",
        time_horizon=TimeHorizon.IMMEDIATE,
        transaction_type=TransactionType.EDB_RULING_REQUEST,
        current_structure=(
            "No formal EDB pre-production engagement. Multiple REQUIRES_INTERPRETATION "
            "items (R-01 through R-05) pending. Combined upside: "
            f"~${edb_runnable:,.0f} additional rebate if all confirmed."
        ),
        suggested_structure=(
            "Schedule formal pre-production meeting with EDB Investment Division. "
            "Submit written query package covering: (1) in-kind post QPE treatment "
            "(R-05), (2) accommodation qualifying (R-02), (3) per diem qualifying "
            "(R-03), (4) SPV routing for international vendor payments (R-01), "
            "(5) ATL fee scope (R-09). Request written responses. "
            "Minimum lead time: 6-8 weeks before principal photography."
        ),
        reason=(
            "EDB pre-production engagement is standard practice for qualifying "
            "productions. It eliminates audit risk on contested items, provides "
            "a clear QPE filing framework, and in some programs creates estoppel — "
            "the program cannot disallow items it has previously confirmed in writing. "
            f"The combined upside of confirmed answers: ~${edb_runnable:,.0f}."
        ),
        financial_impact_usd=edb_runnable,   # maximum if all confirmed
        qualification_impact_usd=p.hod_accom_usd + p.local_perdiem_usd + p.frogsquad_usd + p.inkind_base_usd,
        rebate_impact_usd=edb_runnable,
        required_documentation=[
            "EDB query letter package (all 5 questions as above)",
            "Production schedule and budget summary for EDB review",
            "MU SPV corporate documents",
            "Description of in-kind post-production arrangement",
            "Draft accounting treatment for all contested items",
        ],
        audit_risk=AuditRisk.LOW,
        confidence=RecommendationConfidence.INDUSTRY_STANDARD,
        implementation_difficulty=ImplementationDifficulty.LOW,
        published_support=(
            "Pre-production engagement with incentive authorities is industry standard "
            "worldwide (UK BFI confirmation process, Screen Australia advance rulings, "
            "Ireland Revenue pre-production guidance). Most programs encourage or "
            "require early engagement for complex structures."
        ),
        requires_official_interpretation=False,  # the meeting itself is always permitted
        interpretation_body="Mauritius EDB",
        interpretation_question=None,
        notes=(
            "Highest ROI action available: one meeting, potentially unlocks "
            f"~${edb_runnable:,.0f} in additional confirmed rebate. No cost other "
            "than advisory fees for the query preparation. Must be done BEFORE "
            "principal photography commences."
        ),
    )


# ── Main advisory function ─────────────────────────────────────────────────────

def build_structuring_advisory(
    params: Optional[LittleUtopiaParams] = None,
) -> StructuringAdvisoryResult:
    """
    Build the complete producer structuring advisory for The Little Utopia.

    Returns a StructuringAdvisoryResult with all recommendations ranked by
    financial impact, separated by time horizon, and with all EDB questions
    collated for submission.

    Parameters
    ----------
    params : LittleUtopiaParams (optional; uses defaults if None)
    """
    p = params or LittleUtopiaParams()

    recs: list[StructuringRecommendation] = [
        _r_edb_pre_production_meeting(p),   # R-11: umbrella action (highest first)
        _r_spv_frogsquad(p),                # R-01: $34,943 rebate
        _r_edb_confirm_accommodation(p),    # R-02: $55,924 rebate
        _r_edb_confirm_perdiem(p),          # R-03: $39,946 rebate
        _r_inkind_fmv_ruling(p),            # R-05: $218,750 rebate (upside)
        _r_inkind_fmv_structure(p),         # R-04: fallback if FMV ruling fails
        _r_marine_expansion(p),             # R-06: $39,200 confirmed
        _r_local_crew_expansion(p),         # R-07: $36,750 confirmed
        _r_music_recording_mu(p),           # R-08: $21,000
        _r_atl_edb_ruling(p),               # R-09: $91,000 potential
        _r_related_party_disclosure(p),     # R-10: $0 direct; protective
    ]

    # Sort by time horizon priority, then financial impact descending
    horizon_order = {
        TimeHorizon.IMMEDIATE:   0,
        TimeHorizon.EDB_FIRST:   1,
        TimeHorizon.MEDIUM_TERM: 2,
        TimeHorizon.LONG_TERM:   3,
    }
    recs.sort(key=lambda r: (horizon_order[r.time_horizon], -r.financial_impact_usd))

    # Aggregate by horizon
    immediate = sum(
        r.rebate_impact_usd for r in recs
        if r.time_horizon == TimeHorizon.IMMEDIATE
        and r.confidence in (
            RecommendationConfidence.EXPLICITLY_PERMITTED,
            RecommendationConfidence.INDUSTRY_STANDARD,
        )
    )
    medium = sum(
        r.rebate_impact_usd for r in recs
        if r.time_horizon == TimeHorizon.MEDIUM_TERM
        and r.confidence in (
            RecommendationConfidence.EXPLICITLY_PERMITTED,
            RecommendationConfidence.INDUSTRY_STANDARD,
        )
    )
    edb_cond = sum(
        r.rebate_impact_usd for r in recs
        if r.requires_official_interpretation
        and r.time_horizon == TimeHorizon.EDB_FIRST
    )

    # Collect EDB questions
    seen: set[str] = set()
    edb_qs: list[str] = []
    for r in recs:
        if r.interpretation_question and r.interpretation_question not in seen:
            edb_qs.append(r.interpretation_question)
            seen.add(r.interpretation_question)

    # Unknown items
    unknowns = [
        r.title for r in recs
        if r.confidence == RecommendationConfidence.UNKNOWN
    ]

    return StructuringAdvisoryResult(
        production_title="The Little Utopia",
        jurisdiction_code="MU",
        program_rate=p.mu_rebate_rate,
        advisor_version=ADVISOR_VERSION,
        total_immediate_rebate_uplift=round(immediate, 2),
        total_medium_term_rebate_uplift=round(medium, 2),
        total_edb_conditional_rebate_uplift=round(edb_cond, 2),
        total_potential_rebate_uplift=round(immediate + medium + edb_cond, 2),
        recommendations=recs,
        unknown_items=unknowns,
        edb_questions=edb_qs,
    )
