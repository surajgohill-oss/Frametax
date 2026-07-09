"""
qualification_model.py

Structured qualification-state model for CineAtlas.

Replaces the implicit "unknown == excluded" behavior of the binary
QPEAccount.conservative/base/optimistic_qualifies flags with an explicit
five-state classification that distinguishes:

  - deterministic exclusion (explicit authority: statute, territorial
    nexus, or structural non-spend)
  - deterministic inclusion (explicit authority)
  - a structuring problem (no rule bars it; the blocker is production
    structure — routing, employer-of-record, vendor location)
  - a genuine authority gap (no rule exists either direction — must never
    silently collapse to Excluded)
  - a non-qualification question entirely (placeholder/unfunded line)

This module does not replace calculate_qpe() / QPEAccount — the
three-scenario (conservative/base/optimistic) calculator remains the
filing-facing arithmetic engine and is unchanged. This module adds a
richer, human-facing classification layer on top of the same fixture
data, used to drive the Optimization Engine and Question Stack.

No LLM calls. No invented authority — every GREY_AREA_REQUIRES_AUTHORITY
and STRUCTURING_OPPORTUNITY entry cites the absence of a rule, never a
fabricated one.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from app.calculators.evidence_graph import AbsenceOfAuthority, AuthorityTier, EvidenceGraph


QUALIFICATION_MODEL_VERSION = "1.0.0"


# ── Canonical qualification states ─────────────────────────────────────────

class QualificationState(str, enum.Enum):
    QUALIFIES = "qualifies"
    EXCLUDED = "excluded"
    STRUCTURING_OPPORTUNITY = "structuring_opportunity"
    GREY_AREA_REQUIRES_AUTHORITY = "grey_area_requires_authority"
    NOT_APPLICABLE = "not_applicable"


class AuthorityBasis(str, enum.Enum):
    """What kind of evidence backs this account's state."""
    EXPLICIT_STATUTE = "explicit_statute"                # cited program text
    TERRITORIAL_NEXUS = "territorial_nexus"               # QPE must be MU-incurred; spend is not
    STRUCTURAL_DEFINITION = "structural_definition"        # e.g. unspent reserve isn't "incurred" spend
    CROSS_PROGRAM_CONVENTION = "cross_program_convention"  # near-universal industry practice, not MU-cited
    STRUCTURING_DEPENDENT = "structuring_dependent"        # blocked by production structure, not by rule
    ABSENCE_OF_AUTHORITY = "absence_of_authority"          # no rule found, either direction
    NOT_A_QUALIFICATION_QUESTION = "not_a_qualification_question"  # placeholder/non-spend line


class QualificationConfidence(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class AccountQualification:
    """
    The qualification-state record for a single budget account.

    financial_impact_usd is always the account's own amount — what state
    it carries determines what that dollar *means* (certain QPE, certain
    exclusion, or a quantified upside).
    """
    account_code: str
    description: str
    amount_usd: float
    state: QualificationState
    confidence: QualificationConfidence
    authority_basis: AuthorityBasis
    reason: str
    financial_impact_usd: float
    structuring_mechanism: Optional[str] = None
    resolving_evidence: Optional[str] = None
    incentive_upside_usd: Optional[float] = None  # at the modeled program rate, if state is upside-bearing


# ── Reinvestment intelligence model (data structures only) ─────────────────

class ReinvestmentCategory(str, enum.Enum):
    NOT_PERMITTED = "not_permitted"
    PERMITTED = "permitted"
    VENDOR_REINVESTMENT = "vendor_reinvestment"
    EQUITY_SUBSTITUTION = "equity_substitution"
    SPV_PARTICIPATION = "spv_participation"
    GOVERNMENT_APPROVAL_REQUIRED = "government_approval_required"
    UNKNOWN = "unknown"


@dataclass
class ReinvestmentProfile:
    """
    Per-jurisdiction reinvestment intelligence. UNKNOWN is a first-class,
    distinct value from NOT_PERMITTED — absence of evidence must never be
    conflated with an authoritative "no."
    """
    jurisdiction_code: str
    category: ReinvestmentCategory
    evidence: Optional[str]
    notes: str


REINVESTMENT_REGISTRY: dict[str, ReinvestmentProfile] = {
    "MU": ReinvestmentProfile(
        jurisdiction_code="MU",
        category=ReinvestmentCategory.UNKNOWN,
        evidence=None,
        notes=(
            "No reinvestment, vendor-credit, equity-substitution, or SPV-participation "
            "provision has been located in EDB Film Rebate Scheme guidance. This is an "
            "absence-of-authority UNKNOWN, not a determination of NOT_PERMITTED. "
            "Do not assume either direction until EDB guidance is reviewed."
        ),
    ),
}


def get_reinvestment_profile(jurisdiction_code: str) -> ReinvestmentProfile:
    """Returns the registered profile, or an explicit UNKNOWN if unregistered."""
    return REINVESTMENT_REGISTRY.get(
        jurisdiction_code,
        ReinvestmentProfile(
            jurisdiction_code=jurisdiction_code,
            category=ReinvestmentCategory.UNKNOWN,
            evidence=None,
            notes="No reinvestment profile registered for this jurisdiction.",
        ),
    )


# ── Little Utopia (Mauritius) qualification register ────────────────────────

def build_little_utopia_qualification_register(
    mu_rate: float = 0.40,
) -> list[AccountQualification]:
    """
    The account-by-account qualification-state register for The Little
    Utopia under the Mauritius EDB Film Rebate Scheme, replacing the
    "unknown collapses to excluded" behavior with explicit state.

    Every account here corresponds 1:1 to an account in
    tests/fixtures/little_utopia_sanitized.py. Amounts are taken directly
    from that fixture (not recomputed) so this register can be tested for
    exact reconciliation against calculate_qpe()'s gross budget.
    """
    reg: list[AccountQualification] = []

    def qualifies(code, desc, amt):
        reg.append(AccountQualification(
            account_code=code, description=desc, amount_usd=amt,
            state=QualificationState.QUALIFIES,
            confidence=QualificationConfidence.HIGH,
            authority_basis=AuthorityBasis.EXPLICIT_STATUTE,
            reason="MU-sourced BTL spend within confirmed qualifying scope.",
            financial_impact_usd=amt,
        ))

    def grey_area(code, desc, amt, reason, evidence):
        reg.append(AccountQualification(
            account_code=code, description=desc, amount_usd=amt,
            state=QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
            confidence=QualificationConfidence.LOW,
            authority_basis=AuthorityBasis.ABSENCE_OF_AUTHORITY,
            reason=reason,
            financial_impact_usd=amt,
            resolving_evidence=evidence,
            incentive_upside_usd=round(amt * mu_rate, 2),
        ))

    def structuring(code, desc, amt, mechanism, evidence):
        reg.append(AccountQualification(
            account_code=code, description=desc, amount_usd=amt,
            state=QualificationState.STRUCTURING_OPPORTUNITY,
            confidence=QualificationConfidence.MEDIUM,
            authority_basis=AuthorityBasis.STRUCTURING_DEPENDENT,
            reason="No rule bars qualification — blocked by current payroll/vendor routing, not by authority.",
            financial_impact_usd=amt,
            structuring_mechanism=mechanism,
            resolving_evidence=evidence,
            incentive_upside_usd=round(amt * mu_rate, 2),
        ))

    def excluded(code, desc, amt, reason, basis=AuthorityBasis.EXPLICIT_STATUTE, confidence=QualificationConfidence.HIGH):
        reg.append(AccountQualification(
            account_code=code, description=desc, amount_usd=amt,
            state=QualificationState.EXCLUDED,
            confidence=confidence,
            authority_basis=basis,
            reason=reason,
            financial_impact_usd=amt,
        ))

    def not_applicable(code, desc, amt, reason):
        reg.append(AccountQualification(
            account_code=code, description=desc, amount_usd=amt,
            state=QualificationState.NOT_APPLICABLE,
            confidence=QualificationConfidence.NOT_APPLICABLE,
            authority_basis=AuthorityBasis.NOT_A_QUALIFICATION_QUESTION,
            reason=reason,
            financial_impact_usd=amt,
        ))

    # ── ATL: absence of authority — was silently excluded, now explicit grey area ──
    grey_area("10-00", "Story & Screenplay Development", 85_000.0,
        "ATL qualifying scope is an unresolved unknown_field on the MU jurisdiction record — "
        "no EDB guidance located confirming or denying ATL eligibility.",
        "EDB written clarification on whether writer/director/producer fees are within QPE scope.")
    grey_area("11-00", "Director Fee", 175_000.0,
        "Same absence-of-authority gap as 10-00 — ATL scope is undefined in available EDB guidance.",
        "EDB written clarification on ATL qualifying scope.")
    grey_area("12-00", "Producer Fees", 148_444.0,
        "Same absence-of-authority gap as 10-00/11-00.",
        "EDB written clarification on ATL qualifying scope.")

    # ── Cast fees: absence of MU authority, but cross-program convention supports exclusion ──
    excluded("13-00", "Lead Cast Agreements", 130_000.0,
        "No MU-specific rule located, but above-scale cast fees are excluded from QPE under "
        "near-universal incentive-program convention; treated as excluded pending contrary evidence.",
        basis=AuthorityBasis.CROSS_PROGRAM_CONVENTION, confidence=QualificationConfidence.MEDIUM)

    # ── Imported crew: structuring problem, not an authority gap ──
    structuring("21-00", "Director of Photography", 95_000.0,
        "Route through MU employer-of-record or existing production SPV, arm's-length invoicing.",
        "Documented MU employer/SPV routing agreement for the DP, mirroring the 33-00 Frogsquad precedent.")
    structuring("23-00", "Sound Department", 65_000.0,
        "Route through MU employer-of-record or existing production SPV.",
        "Documented MU employer/SPV routing agreement for the sound team.")
    structuring("42-00", "Stunts & Physical Special Effects", 48_000.0,
        "Route through MU employer-of-record or existing production SPV.",
        "Documented MU employer/SPV routing agreement for the stunt team.")

    # ── Deterministic exclusions: explicit territorial nexus ──
    excluded("39-00", "International Travel & Airfares", 143_000.0,
        "International airfares are not spend incurred in Mauritius — territorial nexus fails. "
        "EDB program text requires QPE to be 'incurred and spent in Mauritius.'",
        basis=AuthorityBasis.TERRITORIAL_NEXUS)
    for code, desc, amt in [
        ("50-00", "Editing — Offline Cut", 78_000.0),
        ("51-00", "Color Grading & Mastering", 45_000.0),
        ("52-00", "Sound Design & Final Mix", 62_000.0),
        ("53-00", "Music Score & Licensing", 55_000.0),
        ("54-00", "VFX / Digital Effects", 95_000.0),
        ("55-00", "Deliverables & DCP Mastering", 28_000.0),
    ]:
        excluded(code, desc, amt,
            "Post-production work performed outside Mauritius — territorial nexus fails.",
            basis=AuthorityBasis.TERRITORIAL_NEXUS)

    # ── Deterministic exclusions: cross-program convention (not MU-cited, but near-universal) ──
    excluded("60-00", "Production Insurance (E&O + Liability)", 185_000.0,
        "Insurance premiums excluded from QPE under near-universal incentive-program convention; "
        "no MU-specific citation located.",
        basis=AuthorityBasis.CROSS_PROGRAM_CONVENTION, confidence=QualificationConfidence.MEDIUM)
    excluded("70-00", "Legal & Accounting", 78_000.0,
        "Finance/legal costs excluded under cross-program convention; no MU-specific citation located.",
        basis=AuthorityBasis.CROSS_PROGRAM_CONVENTION, confidence=QualificationConfidence.MEDIUM)
    excluded("71-00", "Audit & Incentive Submission Fees", 35_000.0,
        "Submission/audit fees excluded under cross-program convention; no MU-specific citation located.",
        basis=AuthorityBasis.CROSS_PROGRAM_CONVENTION, confidence=QualificationConfidence.MEDIUM)
    excluded("80-00", "Completion Bond Premium", 145_000.0,
        "Completion bond premiums excluded under cross-program convention; no MU-specific citation located.",
        basis=AuthorityBasis.CROSS_PROGRAM_CONVENTION, confidence=QualificationConfidence.MEDIUM)

    # ── Structural exclusion: not an authority question at all ──
    excluded("81-00", "Contingency Reserve", 596_597.0,
        "QPE requires spend to be incurred. An unspent contingency reserve is not incurred cost "
        "until drawn down against an actual line item.",
        basis=AuthorityBasis.STRUCTURAL_DEFINITION)

    # ── Not applicable: no cost booked, modeled separately as a cashflow item ──
    not_applicable("82-00", "Finance Costs / Bridge Interest on Rebate Receivable", 0.0,
        "Budget shows $0 — not a qualification question. Real bridge-finance cost is modeled "
        "separately as a cashflow item, not as QPE-account spend.")
    not_applicable("44-00", "Non-Recoverable VAT @ 15% (Mauritius — Memo)", 92_439.0,
        "Memo line — non-recoverable VAT is embedded in gross budget for reporting but is not "
        "a production spend qualification question.")

    # ── Qualifying accounts: explicit MU-sourced BTL spend ──
    for code, desc, amt in [
        ("20-00", "Production Manager & Production Staff", 155_000.0),
        ("22-00", "Camera Department & Equipment Rental", 185_000.0),
        ("24-00", "Lighting & Electrical", 145_000.0),
        ("25-00", "Grip Department", 82_000.0),
        ("26-00", "Art Department / Production Design", 168_000.0),
        ("27-00", "Wardrobe & Costume", 72_000.0),
        ("28-00", "Hair & Makeup", 55_000.0),
        ("29-00", "Location Fees & Permits (Mauritius)", 95_000.0),
        ("30-00", "Transport & Ground Vehicles (Mauritius)", 112_000.0),
        ("31-00", "Marine Unit — Vessel Charter", 165_000.0),
        ("32-00", "Marine Unit — Safety & Support Boats", 35_000.0),
        ("33-00", "Marine Unit — Frogsquad (SA Dive Package)", 99_837.0),
        ("34-00", "Marine Equipment Rental (incl. underwater camera housing)", 93_163.0),
        ("35-00", "Marine Fuel & Consumables", 22_000.0),
        ("36-00", "Catering & Craft Services (Mauritius unit)", 88_000.0),
        ("37-00", "HOD & International Crew Accommodation (Mauritius)", 159_783.0),
        ("38-00", "Local Crew Accommodation & Per Diems (Mauritius)", 114_130.0),
        ("40-00", "Supporting Artists (Extras) — Mauritius", 42_000.0),
        ("41-00", "Payroll Services & PAYE / Employer Contributions", 68_000.0),
        ("43-00", "Unit Publicist & Production Stills", 24_000.0),
    ]:
        qualifies(code, desc, amt)

    return reg


# ── Off-budget in-kind: explicitly never part of the register above ────────

LITTLE_UTOPIA_INKIND_FMV_USD = 625_000.0
LITTLE_UTOPIA_INKIND_NOTE = (
    "The $625,000 in-kind post-production FMV is off-budget (cash_paid_usd=0.0) and is "
    "intentionally absent from build_little_utopia_qualification_register() — it is not an "
    "account, has no account_code, and must never be deducted from gross budget. It is modeled "
    "exclusively as conditional additive QPE via app.calculators.inkind_contribution, contingent "
    "on an EDB ruling that in-kind FMV qualifies (Q1)."
)


# ── Grey area lifecycle ──────────────────────────────────────────────────────

class GreyAreaStatus(str, enum.Enum):
    OPEN = "open"
    RULING_REQUESTED = "ruling_requested"
    RESOLVED_INCLUDE = "resolved_include"
    RESOLVED_EXCLUDE = "resolved_exclude"
    RESOLVED_CONDITIONAL = "resolved_conditional"


RESOLVED_STATUSES = frozenset({
    GreyAreaStatus.RESOLVED_INCLUDE,
    GreyAreaStatus.RESOLVED_EXCLUDE,
    GreyAreaStatus.RESOLVED_CONDITIONAL,
})


@dataclass
class GreyAreaItem:
    """
    The intelligence object mandated by the core principle: every
    GREY_AREA_REQUIRES_AUTHORITY account (or off-budget item, e.g. in-kind
    FMV) is escalated here, never left as a silent exclusion.

    off_budget=True marks items (like in-kind FMV) that are not register
    accounts — resolving them adds to QPE additively rather than
    reclassifying an existing account.

    graph_absence_id / graph_rule_id are Evidence Graph references
    (P3 migration): an OPEN item should link to an AbsenceOfAuthority
    node (graph_absence_id) proving the absence was actually searched,
    not assumed. A RESOLVED item additionally carries graph_rule_id once
    resolve_grey_area() has validated a fully-chained Rule against it.
    The free-text authority_to_ask/resolving_evidence/ruling_citation
    fields are preserved unchanged for backward compatibility and as a
    human-readable summary — the graph fields are the provenance layer
    on top, not a replacement.
    """
    item_id: str
    account_codes: tuple[str, ...]
    amount_usd: float
    jurisdiction_code: str
    authority_to_ask: str
    resolving_evidence: str
    status: GreyAreaStatus = GreyAreaStatus.OPEN
    ruling_citation: Optional[str] = None
    off_budget: bool = False
    linked_question_ids: tuple[str, ...] = field(default_factory=tuple)
    graph_absence_id: Optional[str] = None
    graph_rule_id: Optional[str] = None


def build_little_utopia_grey_areas() -> list[GreyAreaItem]:
    """
    The two Little Utopia grey areas requiring escalation: ATL scope
    (on-budget, register accounts 10-00/11-00/12-00) and in-kind post FMV
    (off-budget, not a register account).

    Each links (via graph_absence_id) to the matching AbsenceOfAuthority
    node in build_little_utopia_evidence_graph() — call that function to
    get the actual graph these IDs resolve against.
    """
    return [
        GreyAreaItem(
            item_id="GA-ATL-SCOPE",
            account_codes=("10-00", "11-00", "12-00"),
            amount_usd=408_444.0,
            jurisdiction_code="MU",
            authority_to_ask="Economic Development Board Mauritius (EDB) / Mauritius Film Development Corp.",
            resolving_evidence="EDB written clarification on whether writer/director/producer fees are within QPE scope.",
            linked_question_ids=("Q-ATL-SCOPE",),
            graph_absence_id="ABS-ATL-SCOPE",
        ),
        GreyAreaItem(
            item_id="GA-INKIND-FMV",
            account_codes=(),
            amount_usd=LITTLE_UTOPIA_INKIND_FMV_USD,
            jurisdiction_code="MU",
            authority_to_ask="Economic Development Board Mauritius (EDB) / Mauritius Film Development Corp.",
            resolving_evidence="Written EDB ruling that in-kind post-production FMV qualifies as QPE (Q1).",
            off_budget=True,
            linked_question_ids=("Q1",),
            graph_absence_id="ABS-INKIND-FMV",
        ),
    ]


def build_little_utopia_evidence_graph() -> EvidenceGraph:
    """
    An EvidenceGraph pre-seeded with the AbsenceOfAuthority nodes that
    build_little_utopia_grey_areas()'s graph_absence_id fields reference.
    Kept separate from the GreyAreaItem builder so qualification_model.py
    can construct grey areas without requiring a graph (backward
    compatibility) while still offering a real, resolvable graph for
    callers that want full provenance.
    """
    graph = EvidenceGraph()
    graph.add_absence_of_authority(AbsenceOfAuthority(
        absence_id="ABS-ATL-SCOPE",
        jurisdiction_code="MU",
        question="Does ATL (writer/director/producer) spend qualify as QPE?",
        searched_tiers=(
            AuthorityTier.PRIMARY_LEGISLATION, AuthorityTier.REGULATIONS,
            AuthorityTier.OFFICIAL_GUIDANCE, AuthorityTier.OFFICIAL_FAQ,
        ),
        notes="No guidance located across four tiers searched.",
    ))
    graph.add_absence_of_authority(AbsenceOfAuthority(
        absence_id="ABS-INKIND-FMV",
        jurisdiction_code="MU",
        question="Does in-kind post-production FMV qualify as additive QPE?",
        searched_tiers=(
            AuthorityTier.PRIMARY_LEGISLATION, AuthorityTier.REGULATIONS,
            AuthorityTier.OFFICIAL_GUIDANCE,
        ),
        notes="No published EDB rule on in-kind treatment.",
    ))
    return graph


def grey_area_terminus(item: GreyAreaItem, graph: EvidenceGraph) -> str:
    """
    Terminal-node discipline check (mirrors EvidenceGraph's own rule,
    applied to a GreyAreaItem): returns "rule" if the item resolves to a
    fully-chained Rule, "absence_of_authority" if it resolves to a real
    AbsenceOfAuthority node in `graph`, or "unlinked" if neither
    reference is valid — the state P3 exists to make impossible to reach
    silently.
    """
    if item.graph_rule_id and graph.rule_is_fully_chained(item.graph_rule_id):
        return "rule"
    if item.graph_absence_id:
        try:
            graph.get_absence_of_authority(item.graph_absence_id)
            return "absence_of_authority"
        except ValueError:
            return "unlinked"
    return "unlinked"


def resolve_grey_area(
    item: GreyAreaItem,
    outcome: GreyAreaStatus,
    ruling_citation: Optional[str] = None,
    graph: Optional[EvidenceGraph] = None,
    resolving_rule_id: Optional[str] = None,
) -> GreyAreaItem:
    """
    Pure state transition. Any RESOLVED_* outcome is a counsel/authority
    hard gate: it requires a ruling citation as bound evidence. Approval
    alone is never sufficient — this is what prevents a grey area from
    being waved into Base/Conservative without documentation.

    P3: when `graph` is supplied, resolution requires evidence-backed
    authority, not just a citation string — `resolving_rule_id` must
    name a Rule in `graph` that is fully chained (Evidence -> Citation ->
    AuthoritySource -> DocumentVersion, all resolving). A rule that
    isn't fully chained cannot resolve a grey area, exactly as it
    cannot be linked to a Recommendation in the Evidence Graph itself.

    Without `graph` (the pre-P3 signature), behavior is unchanged: a
    ruling_citation string alone is sufficient. This keeps every
    existing caller working exactly as before.

    Raises ValueError if a resolution is attempted without evidence.
    """
    if outcome in RESOLVED_STATUSES:
        if not ruling_citation:
            raise ValueError(
                f"Grey area '{item.item_id}' cannot resolve to {outcome.value} "
                "without a ruling_citation — resolution requires bound evidence, "
                "not approval alone."
            )
        if graph is not None:
            if not resolving_rule_id:
                raise ValueError(
                    f"Grey area '{item.item_id}' cannot resolve to {outcome.value} "
                    "with a graph supplied but no resolving_rule_id — evidence-backed "
                    "authority requires a specific Rule in the Evidence Graph."
                )
            if not graph.rule_is_fully_chained(resolving_rule_id):
                raise ValueError(
                    f"Rule '{resolving_rule_id}' is not fully chained to an authority "
                    f"source in the Evidence Graph — cannot resolve grey area "
                    f"'{item.item_id}' against it."
                )
    new_graph_rule_id = resolving_rule_id if (graph is not None and outcome in RESOLVED_STATUSES) else item.graph_rule_id
    return GreyAreaItem(
        item_id=item.item_id,
        account_codes=item.account_codes,
        amount_usd=item.amount_usd,
        jurisdiction_code=item.jurisdiction_code,
        authority_to_ask=item.authority_to_ask,
        resolving_evidence=item.resolving_evidence,
        status=outcome,
        ruling_citation=ruling_citation,
        off_budget=item.off_budget,
        linked_question_ids=item.linked_question_ids,
        graph_absence_id=item.graph_absence_id,
        graph_rule_id=new_graph_rule_id,
    )


def apply_grey_area_resolution(
    register: list[AccountQualification],
    item: GreyAreaItem,
) -> list[AccountQualification]:
    """
    Given a RESOLVED GreyAreaItem, return a NEW register (the input is
    never mutated) with the affected accounts reclassified and their
    authority_basis upgraded to EXPLICIT_STATUTE — the ruling is now the
    citable authority, replacing the prior ABSENCE_OF_AUTHORITY basis.

    Off-budget items (in-kind FMV) never reclassify any register account
    — resolving them has no effect here by design; their value is
    applied additively by the optimizer (inkind_fmv_usd), never by
    rewriting a QUALIFIES/EXCLUDED account. This is what keeps in-kind
    "off-budget additive only" even after resolution.

    Raises ValueError if the item is not actually resolved.
    """
    if item.status not in RESOLVED_STATUSES:
        raise ValueError(
            f"Grey area '{item.item_id}' is not resolved (status={item.status.value}) — "
            "cannot apply it to the qualification register."
        )
    if item.off_budget or not item.account_codes:
        return list(register)

    if item.status == GreyAreaStatus.RESOLVED_INCLUDE:
        new_state, new_reason = QualificationState.QUALIFIES, "included"
    elif item.status == GreyAreaStatus.RESOLVED_EXCLUDE:
        new_state, new_reason = QualificationState.EXCLUDED, "excluded"
    else:
        new_state, new_reason = None, None  # RESOLVED_CONDITIONAL: leave account states untouched here

    updated: list[AccountQualification] = []
    for a in register:
        if a.account_code in item.account_codes and new_state is not None:
            updated.append(AccountQualification(
                account_code=a.account_code, description=a.description, amount_usd=a.amount_usd,
                state=new_state, confidence=QualificationConfidence.HIGH,
                authority_basis=AuthorityBasis.EXPLICIT_STATUTE,
                reason=f"Resolved {new_reason} via {item.ruling_citation}: {item.resolving_evidence}",
                financial_impact_usd=a.amount_usd,
            ))
        else:
            updated.append(a)
    return updated


# ── Reinvestment treatment table (data only — no arithmetic) ───────────────

@dataclass
class ReinvestmentTreatment:
    npc_effect: str
    requires_evidence: bool
    evidence_request: Optional[str]


REINVESTMENT_TREATMENT: dict[ReinvestmentCategory, ReinvestmentTreatment] = {
    ReinvestmentCategory.UNKNOWN: ReinvestmentTreatment(
        npc_effect="No effect on Conservative or Base. Not asserted in Optimistic arithmetic "
                   "— appears only as a bounded intelligence gap pending evidence.",
        requires_evidence=True,
        evidence_request="Review EDB Film Rebate Scheme guidance for any reinvestment, "
                          "vendor-credit, equity-substitution, or SPV-participation provision.",
    ),
    ReinvestmentCategory.NOT_PERMITTED: ReinvestmentTreatment(
        npc_effect="No effect — closed, authority cited.",
        requires_evidence=False,
        evidence_request=None,
    ),
    ReinvestmentCategory.PERMITTED: ReinvestmentTreatment(
        npc_effect="Financing benefit: rebate redeployment reduces bridge/capital cost, "
                   "improving NPC in Base once approved.",
        requires_evidence=True,
        evidence_request="Program text confirming unconditional reinvestment permission.",
    ),
    ReinvestmentCategory.VENDOR_REINVESTMENT: ReinvestmentTreatment(
        npc_effect="Timing improvement (skip remittance delay) plus/minus effective-rate delta; "
                   "enters Base on approval and a bound vendor agreement.",
        requires_evidence=True,
        evidence_request="Vendor agreement documenting rebate-as-credit terms.",
    ),
    ReinvestmentCategory.EQUITY_SUBSTITUTION: ReinvestmentTreatment(
        npc_effect="Financing-structure effect (cost-of-capital line), not a QPE change. Counsel-gated.",
        requires_evidence=True,
        evidence_request="Counsel review of equity-substitution mechanics under program rules.",
    ),
    ReinvestmentCategory.SPV_PARTICIPATION: ReinvestmentTreatment(
        npc_effect="Primarily an enabler for StructuringPath prerequisites; independent value only "
                   "if program text grants one.",
        requires_evidence=True,
        evidence_request="Program text confirming SPV participation carries independent value.",
    ),
    ReinvestmentCategory.GOVERNMENT_APPROVAL_REQUIRED: ReinvestmentTreatment(
        npc_effect="Treated as a grey area whose resolving evidence is the approval itself; "
                   "weight capped until granted.",
        requires_evidence=True,
        evidence_request="Government approval application and decision.",
    ),
}


def get_reinvestment_evidence_request(jurisdiction_code: str) -> Optional[str]:
    """Returns the evidence request for this jurisdiction's reinvestment
    category, or None if the category is closed/no evidence is needed."""
    profile = get_reinvestment_profile(jurisdiction_code)
    treatment = REINVESTMENT_TREATMENT[profile.category]
    return treatment.evidence_request if treatment.requires_evidence else None


# ── Aggregation helpers ──────────────────────────────────────────────────────

def summarize_register(register: list[AccountQualification]) -> dict:
    """Aggregate totals by state, plus upside totals for actionable states."""
    totals: dict[str, float] = {s.value: 0.0 for s in QualificationState}
    upside_totals: dict[str, float] = {
        QualificationState.STRUCTURING_OPPORTUNITY.value: 0.0,
        QualificationState.GREY_AREA_REQUIRES_AUTHORITY.value: 0.0,
    }
    for a in register:
        totals[a.state.value] += a.financial_impact_usd
        if a.incentive_upside_usd is not None:
            upside_totals[a.state.value] += a.incentive_upside_usd
    return {"amounts_by_state": totals, "incentive_upside_by_state": upside_totals}
