"""
structuring_opportunity_patterns.py

Final Consolidated Backend Correction + Global Structuring Intelligence
Acceptance, Parts 5-19 — the durable canonical representation of Gemini's
Global Production Structuring Intelligence Review (commit 3a12d9a,
docs/validation/GEMINI_STRUCTURING_PATTERN_LIBRARY.json). This is NOT a
second optimizer, NOT a ranking engine, NOT an NPC calculator — a
subordinate, additive PATTERN REGISTRY read by canonical_opportunity_
bridge.py (and, through it, canonical_evaluation.py's own opportunity
discovery loop) to surface real, primary-source-cited structural
opportunities, using the EXISTING candidate-generation/pricing/ranking
architecture for anything that actually needs economics.

Master architecture rule (this task's own Part 2): the opportunity
bridge owns trigger detection, missing-fact detection, structural-lever
disclosure, program/fund/route-unlock disclosure, and feasibility/timing
disclosure. It does NOT calculate QPE/incentive/NPC/stacking math/
component economics/ranking — those remain in the existing engines this
module's patterns point AT (recommended_existing_seam), never duplicate.

Provenance discipline (Part 5/18/27): every pattern keeps PRIMARY
AUTHORITY (a real statute/treaty article), PROFESSIONAL PRACTICE evidence
(industry guides/workshops), and CASE STUDY evidence (real, named
productions) in three SEPARATE, never-conflated fields. A case study
VALIDATES a pattern; it never CREATES legal doctrine — see
StructuringPattern.case_studies' own docstring. Gemini's validation
artifacts (the JSON/MD files under docs/validation/) are the RESEARCH
record, not the runtime database — this module IS that runtime database,
durably represented in source, not read from the validation files at
request time (Part 28: no live web / external-file dependency at
runtime).
"""
from __future__ import annotations

from dataclasses import dataclass, field

STRUCTURING_OPPORTUNITY_PATTERNS_VERSION = "1.0.0"

# ── Priority vocabulary (Gemini's own P0/P1 classification) ─────────────
PRIORITY_P0 = "P0"
PRIORITY_P1 = "P1"

# ── Existing-capability classification (Gemini's own audit of THIS
# codebase against each pattern — never re-derived, reused verbatim) ────
CAPABILITY_REPRESENTATION_GAP = "REPRESENTATION_GAP"
CAPABILITY_SUPPORTED_BUT_DATA_THIN = "SUPPORTED_BUT_DATA_THIN"
CAPABILITY_ALREADY_SUPPORTED_AND_CONNECTED = "ALREADY_SUPPORTED_AND_CONNECTED"
CAPABILITY_ENGINE_EXISTS_BUT_DISCONNECTED = "ENGINE_EXISTS_BUT_DISCONNECTED"
CAPABILITY_GENUINELY_NEW_OPTIMIZER_CAPABILITY_REQUIRED = "GENUINELY_NEW_OPTIMIZER_CAPABILITY_REQUIRED"

#: Opportunity types A-J (Part 7) this pattern library's 5 patterns back.
#: Not every letter has a Gemini-researched pattern behind it yet (E-J
#: beyond D are generic, program-data-driven opportunity classes already
#: served by canonical_opportunity_bridge.py's pre-existing discover_*
#: functions, not by a specific SP_* pattern) — mapped here for
#: traceability, never fabricated where no real pattern exists.
OPPORTUNITY_TYPE_A_MULTILATERAL_COPRO_ALTERNATIVE = "MULTILATERAL_COPRO_ALTERNATIVE"
OPPORTUNITY_TYPE_B_NATIONAL_TREATMENT_STRUCTURE = "NATIONAL_TREATMENT_STRUCTURE_OPPORTUNITY"
OPPORTUNITY_TYPE_C_NON_PARTY_PERSONNEL_EXCEPTION = "NON_PARTY_PERSONNEL_EXCEPTION_OPPORTUNITY"
OPPORTUNITY_TYPE_D_COMPONENT_RELOCATION = "COMPONENT_RELOCATION_OPPORTUNITY"
OPPORTUNITY_TYPE_E_COPRO_CONTRIBUTION_GAP = "COPRO_CONTRIBUTION_GAP_OPPORTUNITY"
OPPORTUNITY_TYPE_F_NATIONAL_STATUS_FUND = "NATIONAL_STATUS_FUND_OPPORTUNITY"
OPPORTUNITY_TYPE_G_QUALIFICATION_CURE = "QUALIFICATION_CURE_OPPORTUNITY"
OPPORTUNITY_TYPE_H_ATL_CAP_HEADROOM = "ATL_CAP_HEADROOM_OPPORTUNITY"
OPPORTUNITY_TYPE_I_REINVESTMENT_DEFERRED = "REINVESTMENT_DEFERRED_STRUCTURE_OPPORTUNITY"
OPPORTUNITY_TYPE_J_TIMING_FEASIBILITY = "TIMING_FEASIBILITY_OPPORTUNITY"


@dataclass(frozen=True)
class StructuringPattern:
    """One durable structuring-knowledge record. Every field Part 7's
    specification asks for; empty/None where genuinely not applicable to
    a given pattern (never fabricated to fill the shape)."""
    pattern_id: str
    name: str
    pattern_type: str              # one of OPPORTUNITY_TYPE_* above
    priority: str                  # PRIORITY_P0 / PRIORITY_P1
    trigger: str
    jurisdictions: tuple[str, ...]
    programs: tuple[str, ...] = ()
    treaties_frameworks: tuple[str, ...] = ()
    legal_prerequisites: str = ""
    required_project_facts: tuple[str, ...] = ()
    required_script_facts: tuple[str, ...] = ()
    structural_lever: str = ""
    contribution_min_pct: float | None = None
    contribution_max_pct: float | None = None
    personnel_constraints: str = ""
    ownership_constraints: str = ""
    national_treatment_effect: str = ""
    program_unlocks: tuple[str, ...] = ()
    fund_unlocks: tuple[str, ...] = ()
    component_effect: str = ""
    atl_effect: str = ""
    cashflow_effect: str = ""
    timing_constraints: str = ""
    feasibility_constraints: str = ""

    # ── Provenance — three SEPARATE, never-conflated tiers ──────────────
    #: A real statute/treaty article citation. This is what makes a
    #: pattern LEGALLY safe to disclose as a structural lever — never a
    #: practice source or case study alone.
    primary_authority: str = ""
    #: Industry practice evidence (professional guides, market/festival
    #: workshops, law-firm client notes) — corroborates that the pattern
    #: is real-world-used, but is NOT itself legal authority.
    practice_sources: tuple[str, ...] = ()
    #: Real, named productions the pattern is documented to have been
    #: used on. VALIDATES the pattern (proof it works in practice); never
    #: the SOURCE of the legal rule itself (a case study cannot create
    #: law the primary_authority doesn't already state).
    case_studies: tuple[str, ...] = ()
    confidence: str = "MEDIUM"

    # ── This codebase's own capability classification against the
    # pattern, and where its economics/pricing should be resolved — never
    # re-derived by the opportunity bridge, only disclosed. ─────────────
    existing_cineglobe_capability: str = CAPABILITY_REPRESENTATION_GAP
    gap_type: str = ""
    recommended_existing_seam: str = ""


#: The 5 real, researched patterns from Gemini's Global Production
#: Structuring Intelligence Review (commit 3a12d9a). Verbatim content,
#: reshaped into this module's typed record — no field invented, no
#: number rounded away, no jurisdiction added.
STRUCTURING_OPPORTUNITY_PATTERNS: dict[str, StructuringPattern] = {
    "SP_001_BILATERAL_TO_MULTILATERAL_UPGRADE": StructuringPattern(
        pattern_id="SP_001_BILATERAL_TO_MULTILATERAL_UPGRADE",
        name="Bilateral to Multilateral Upgrade",
        pattern_type=OPPORTUNITY_TYPE_A_MULTILATERAL_COPRO_ALTERNATIVE,
        priority=PRIORITY_P0,
        trigger="Minority contribution between 10% and 19.9%.",
        jurisdictions=("GLOBAL", "COUNCIL OF EUROPE"),
        treaties_frameworks=("european_convention",),
        legal_prerequisites=(
            "European Convention on Cinematographic Co-Production (Revised) "
            "or similar multilateral instrument."
        ),
        required_project_facts=("Existing two-party structure", "Contribution percentages"),
        required_script_facts=(),
        structural_lever="Introduce a 3rd party co-producer to satisfy multilateral status.",
        contribution_min_pct=10.0, contribution_max_pct=19.9,
        component_effect="May require shifting a small BTL component to the 3rd country to hit 10%.",
        atl_effect="Can use 3rd country ATL to satisfy the 10%.",
        national_treatment_effect="Confers national treatment in the third country, unlocking their local funding.",
        program_unlocks=("National incentives in all 3 countries",),
        fund_unlocks=("Eurimages (requires European multilateral or bilateral)",),
        cashflow_effect="Additional closing complexity; multiple financing streams.",
        timing_constraints="Must be structured before principal photography.",
        feasibility_constraints="Creative control dilution, trilateral legal fees.",
        primary_authority="European Convention on Cinematographic Co-Production (Revised) 2017, Art. 6.",
        practice_sources=("Olsberg SPI Coproduction reports", "EAVE structuring guidelines"),
        case_studies=("Triangle of Sadness (Sweden/Germany/France/UK)",),
        confidence="HIGH",
        existing_cineglobe_capability=CAPABILITY_REPRESENTATION_GAP,
        gap_type="Optimizer currently only attempts bilateral matching.",
        recommended_existing_seam=(
            "canonical_treaty_bridge.evaluate_european_convention_coproduction_opportunity() "
            "(CBA-006) — real N>=2 multilateral matching, extendable to N>=3 where the "
            "existing treaty representation supports it."
        ),
    ),
    "SP_002_SERVICE_TO_COPRO_NATIONAL_TREATMENT_ARBITRAGE": StructuringPattern(
        pattern_id="SP_002_SERVICE_TO_COPRO_NATIONAL_TREATMENT_ARBITRAGE",
        name="Service to Copro National Treatment Arbitrage",
        pattern_type=OPPORTUNITY_TYPE_B_NATIONAL_TREATMENT_STRUCTURE,
        priority=PRIORITY_P0,
        trigger="Project qualifies for service rebate but has sufficient local elements to potentially pass a cultural test.",
        jurisdictions=("GLOBAL", "EUROPE", "CANADA", "AUSTRALIA"),
        legal_prerequisites="Bilateral Audiovisual Treaty conferring National Treatment.",
        required_project_facts=("Cultural elements", "Financing gap"),
        required_script_facts=("Location", "Lead characters' nationality"),
        structural_lever="Restructure financing to make the local service company an official co-producer with equity/copyright.",
        ownership_constraints="Must share copyright/revenue with the local co-producer.",
        component_effect="May need to lock specific post/VFX components to the jurisdiction to pass the points test.",
        atl_effect="Usually requires local Director or Lead Actor to pass cultural test.",
        national_treatment_effect="Transforms foreign capital into eligible 'local' capital for matching purposes.",
        program_unlocks=("Domestic/Cultural tax credits (usually higher % than service)",),
        fund_unlocks=("Selective national/regional funds (e.g., Medienboard, Telefilm, Screen Australia)",),
        cashflow_effect=(
            "Selective funds are paid in installments (prep, wrap, delivery), improving "
            "cashflow vs tax credits (paid post-delivery)."
        ),
        timing_constraints="Must apply for provisional co-pro status at least 30-60 days before shooting.",
        feasibility_constraints="Must share copyright/revenue with the local co-producer.",
        primary_authority="Standard Article 2 (National Treatment) in bilateral treaties.",
        practice_sources=("Cannes Marché du Film finance workshops", "Dentons Film Finance Group"),
        case_studies=("Room (Canada/Ireland)",),
        confidence="HIGH",
        existing_cineglobe_capability=CAPABILITY_SUPPORTED_BUT_DATA_THIN,
        gap_type="Optimizer calculates both rebates but doesn't auto-suggest the ATL/Copyright changes needed to cross the threshold.",
        recommended_existing_seam="canonical_opportunity_bridge.py (this module's discover_service_to_copro_national_treatment_opportunity).",
    ),
    "SP_003_PDV_ONLY_TREATY_BYPASS": StructuringPattern(
        pattern_id="SP_003_PDV_ONLY_TREATY_BYPASS",
        name="PDV-Only Treaty Bypass (Component Relocation)",
        pattern_type=OPPORTUNITY_TYPE_D_COMPONENT_RELOCATION,
        priority=PRIORITY_P1,
        trigger="High VFX/Post budget (>20% of total) in a non-PDV-optimized shooting location.",
        jurisdictions=("UK", "AUSTRALIA", "NEW ZEALAND", "CANADA (PROVINCIAL)"),
        legal_prerequisites="Existence of a standalone PDV incentive with no global cultural test requirement.",
        required_project_facts=("Detailed VFX budget", "Post schedule"),
        required_script_facts=("VFX shot count/complexity",),
        structural_lever="Contract VFX to a vendor in the target PDV jurisdiction.",
        component_effect="Relocates all post/digital components.",
        program_unlocks=("Standalone PDV Rebate (e.g., UK VFX 39%, NZ 20%+5%)",),
        national_treatment_effect="None (pure service relationship).",
        cashflow_effect="Vendor may cashflow the rebate, reducing producer borrowing.",
        timing_constraints="Vendor contracts must be structured before work begins.",
        feasibility_constraints="Requires robust remote pipeline; limits director's physical presence at VFX house.",
        primary_authority="UK Finance Act 2024 (VFX uplift); NZ SPRG Guidelines.",
        practice_sources=("EP / Cast & Crew incentive guides", "Sargent-Disc"),
        case_studies=("Numerous US studio blockbusters (Shoot Aus, VFX NZ/UK)",),
        confidence="HIGH",
        existing_cineglobe_capability=CAPABILITY_ALREADY_SUPPORTED_AND_CONNECTED,
        gap_type="Currently supported but optimizer may not aggressively split budgets automatically.",
        recommended_existing_seam=(
            "app.calculators.production_allocation's existing component_relocation "
            "candidate generation (canonical_evaluation.py already generates one "
            "candidate per movable component per top target jurisdiction) — no new code."
        ),
    ),
    "SP_004_NON_PARTY_PERSONNEL_EXCEPTION": StructuringPattern(
        pattern_id="SP_004_NON_PARTY_PERSONNEL_EXCEPTION",
        name="Non-Party Personnel Exception in Coproductions",
        pattern_type=OPPORTUNITY_TYPE_C_NON_PARTY_PERSONNEL_EXCEPTION,
        priority=PRIORITY_P0,
        trigger="Official coproduction requires a US/Global star for financing/sales.",
        jurisdictions=("CANADA", "UK", "AUSTRALIA", "FRANCE"),
        legal_prerequisites="Treaty clause permitting non-party participation (e.g., Article 4).",
        required_project_facts=("Cast nationalities", "Budget breakdown"),
        required_script_facts=("Character requirements (if story dictates non-party)",),
        structural_lever="Allocate the non-party exception exclusively to the highest-paid non-party ATL.",
        personnel_constraints="Strict mathematical cap (often 20% of budget); limits other foreign hires.",
        component_effect="Limits non-party BTL crew since the % allowance is consumed by the star.",
        atl_effect="Allows attachment of A-list non-party talent.",
        national_treatment_effect="Preserves national treatment.",
        program_unlocks=("Maintains Official Copro status despite US star.",),
        fund_unlocks=("Maintains selective fund eligibility.",),
        cashflow_effect="Unlocks presales/equity tied to the star.",
        timing_constraints="Must be approved by Competent Authorities during provisional certification.",
        feasibility_constraints="Strict mathematical cap (often 20% of budget); limits other foreign hires.",
        primary_authority="Canada-UK Treaty Article 4; Aus-UK Treaty Article 4.",
        practice_sources=("BFI Co-production guidance", "Telefilm Canada Copro Guidelines"),
        case_studies=("Brooklyn (Canada/Ireland/UK with US lead)",),
        confidence="HIGH",
        existing_cineglobe_capability=CAPABILITY_ENGINE_EXISTS_BUT_DISCONNECTED,
        gap_type="CineGlobe knows nationality but fails to actively calculate the 20% exception threshold.",
        recommended_existing_seam="app.calculators.treaty_engine (bilateral TreatyData) + canonical_treaty_bridge.py.",
    ),
    "SP_005_FINANCE_ONLY_COPRODUCTION": StructuringPattern(
        pattern_id="SP_005_FINANCE_ONLY_COPRODUCTION",
        name="Financial-Only Coproduction",
        pattern_type=OPPORTUNITY_TYPE_E_COPRO_CONTRIBUTION_GAP,
        priority=PRIORITY_P1,
        trigger="Financing gap where creative/technical elements are already locked to the majority country.",
        jurisdictions=("EUROPE", "AUSTRALIA", "CANADA"),
        treaties_frameworks=("european_convention",),
        legal_prerequisites="Treaty explicitly recognizing 'financial co-productions' (e.g., European Convention Art 11).",
        required_project_facts=("Financing structure",),
        required_script_facts=(),
        structural_lever="Introduce a minority co-producer solely for cash equity.",
        component_effect="None (no physical production moves).",
        atl_effect="None.",
        national_treatment_effect="Grants national treatment for the minority financier's investment.",
        program_unlocks=("Minority co-production funds (e.g., Eurimages, NFI Minority Co-pro fund).",),
        fund_unlocks=("Specific minority selective funds.",),
        cashflow_effect="Closes financing gaps without disrupting physical production.",
        timing_constraints="Must apply before shooting.",
        feasibility_constraints=(
            "Minority funds are highly competitive; requires cultural approval in both "
            "countries despite no physical spend in minority country."
        ),
        primary_authority="European Convention on Cinematographic Co-Production (Revised) 2017, Art. 11.",
        practice_sources=("Council of Europe Explanatory Reports", "Olswang/CMS guides"),
        case_studies=("Various Eurimages-backed features.",),
        confidence="HIGH",
        existing_cineglobe_capability=CAPABILITY_GENUINELY_NEW_OPTIMIZER_CAPABILITY_REQUIRED,
        gap_type="Optimizer currently assumes contribution = spend/personnel, missing purely financial treaties.",
        recommended_existing_seam=(
            "canonical_opportunity_bridge.py, DISCLOSURE ONLY — Gemini's own "
            "classification (GENUINELY_NEW_OPTIMIZER_CAPABILITY_REQUIRED) and this "
            "task's master architecture rule (no new optimizer/pricing engine) mean this "
            "pattern is represented as durable knowledge and surfaced as a real "
            "structural-lever opportunity, but its economics are NOT computed here — "
            "a 'financial-only contribution' spend/personnel model would need to be "
            "added to treaty_engine.py's own contribution representation first, a "
            "genuine, disclosed, separately-scoped extension, not attempted this pass."
        ),
    ),
}


def get_structuring_pattern(pattern_id: str) -> StructuringPattern | None:
    return STRUCTURING_OPPORTUNITY_PATTERNS.get(pattern_id)


def patterns_by_priority(priority: str) -> tuple[StructuringPattern, ...]:
    return tuple(p for p in STRUCTURING_OPPORTUNITY_PATTERNS.values() if p.priority == priority)
