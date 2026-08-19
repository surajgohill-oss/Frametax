"""
program_requirements.py

Final Global Discovery phase: the PRODUCTION REQUIREMENTS DATABASE — a
structured, program_slug-keyed registry of eligibility, application/
timing, compliance, funding-availability, and monetization facts that sit
ALONGSIDE a program's rate doctrine (executable_jurisdiction_registry.py)
without duplicating it. Rate/threshold/cap/citation facts that DRIVE the
calculation remain exclusively in DoctrineRecord; this module holds the
facts a producer needs to PLAN around a program — most of which the
calculation engine does not (and should not) consume, but which the
served UI must expose so a producer is never planning blind.

Design, matching the established pattern (conditional_programs.py,
structure_compatibility.py): a separate module, not a bloated add-on to
DoctrineRecord — same reasoning as those modules' own docstrings (a
genuinely different data domain, sourced independently, deserves its own
home rather than forcing every consumer of DoctrineRecord to carry
fields it will almost always leave None).

Every field is Optional. None means "not yet confirmed," never "does not
apply" and never a fabricated default. Every profile carries an
EvidenceRecord per fact group so a producer (and this module's own
future maintainers) can tell a statute-read fact from a corroborated
secondary-source estimate — see EvidenceRecord and TimingBasis below,
which implement Objective 5's source/confidence model and the explicit
instruction to distinguish "statutory deadline" from "official target"
from "reported practical timeline" from "estimate" from "unknown", never
presenting one as another.

`additional_facts` is a deliberate, bounded escape hatch: a small
dict[str, str] for real, sourced facts that don't warrant their own
first-class field (e.g. a specific logo-uplift condition, a program-name
alias). It is NOT a substitute for the structured fields above — a fact
used by more than a couple of programs should graduate to its own field.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

PROGRAM_REQUIREMENTS_VERSION = "1.0.0"


class SourceType(str, enum.Enum):
    PRIMARY = "primary"       # statute, official regulation, official agency page/PDF
    SECONDARY = "secondary"   # professional-services guide, trade press, aggregator


class RecordStatus(str, enum.Enum):
    CURRENT = "current"
    EXPIRED = "expired"
    PROPOSED = "proposed"
    SUSPENDED = "suspended"
    UNCERTAIN = "uncertain"


class TimingBasis(str, enum.Enum):
    """Objective 3's explicit instruction: never present an estimate as a
    legal deadline. Every timing fact below carries one of these, and the
    served UI must render the distinction, not just the value."""
    STATUTORY_DEADLINE = "statutory_deadline"
    OFFICIAL_TARGET = "official_target"           # e.g. FFA's stated processing target
    REPORTED_PRACTICAL = "reported_practical"      # evidenced but not official (broker/trade report)
    ESTIMATE = "estimate"
    UNKNOWN = "unknown"


class AllocationType(str, enum.Enum):
    ENTITLEMENT = "entitlement"                    # qualify and it's yours, no competition
    FIRST_COME_FIRST_SERVED = "first_come_first_served"
    COMPETITIVE = "competitive"
    DISCRETIONARY = "discretionary"
    SUBJECT_TO_APPROPRIATION = "subject_to_appropriation"


@dataclass(frozen=True)
class EvidenceRecord:
    """Objective 5's source/evidence model. One of these per profile (not
    per field) — a program's requirements are normally confirmed from the
    same one or two sources in the same research pass; a field-level
    citation would be false precision when the underlying research wasn't
    actually field-by-field."""
    source_title: str
    source_url: Optional[str]
    issuing_authority: str
    source_type: SourceType
    status: RecordStatus
    effective_date: Optional[str] = None   # ISO date string or None if not stated
    access_date: Optional[str] = None
    notes: str = ""


@dataclass(frozen=True)
class TimingFact:
    """One timing data point with its basis disclosed — the mechanism that
    keeps a reported practical timeline from ever rendering as a legal
    deadline."""
    value: str
    basis: TimingBasis


@dataclass(frozen=True)
class ProgramRequirementsProfile:
    program_slug: str
    jurisdiction_code: str

    # ── Eligibility / structural ──────────────────────────────────────────
    local_entity_required: Optional[bool] = None
    local_coproducer_required: Optional[bool] = None
    treaty_or_official_coproduction_required: Optional[bool] = None
    cultural_test_required: Optional[bool] = None
    cultural_test_points: Optional[int] = None       # points achieved/available scale, if stated
    cultural_test_threshold: Optional[int] = None     # minimum points required to pass
    min_total_budget_usd: Optional[float] = None
    min_local_spend_usd: Optional[float] = None
    min_shoot_days: Optional[int] = None
    atl_cap_pct_of_other_costs: Optional[float] = None
    per_person_cap_usd: Optional[float] = None
    per_project_cap_usd: Optional[float] = None

    # ── Application / timing ────────────────────────────────────────────
    preapproval_mandatory: Optional[bool] = None
    expenditure_before_approval_qualifies: Optional[bool] = None
    application_deadline: Optional[TimingFact] = None
    audit_or_final_certification_deadline: Optional[TimingFact] = None
    payment_timing: Optional[TimingFact] = None
    sunset_date: Optional[str] = None                 # ISO date, or None if open-ended/unstated

    # ── Compliance ───────────────────────────────────────────────────────
    audit_required: Optional[bool] = None
    cpa_or_approved_auditor_required: Optional[bool] = None
    completion_bond_required: Optional[bool] = None
    clawback_or_repayment_trigger: Optional[str] = None

    # ── Funding availability ────────────────────────────────────────────
    annual_program_cap_usd: Optional[float] = None
    allocation_type: Optional[AllocationType] = None

    # ── Monetization / cash-flow ─────────────────────────────────────────
    refundable: Optional[bool] = None
    transferable: Optional[bool] = None
    transfer_approval_required: Optional[bool] = None
    typical_transfer_price_pct_range: Optional[tuple[float, float]] = None  # market evidence, never statutory
    cashflow_timing_weeks_estimate: Optional[int] = None

    # ── Provenance ───────────────────────────────────────────────────────
    evidence: Optional[EvidenceRecord] = None
    additional_facts: dict[str, str] = field(default_factory=dict)


# ── Registry ─────────────────────────────────────────────────────────────

_REGISTRY: dict[str, ProgramRequirementsProfile] = {}


def register(profile: ProgramRequirementsProfile) -> ProgramRequirementsProfile:
    _REGISTRY[profile.program_slug] = profile
    return profile


def get_program_requirements(program_slug: str) -> Optional[ProgramRequirementsProfile]:
    """The structured requirements profile for a program, or None when not
    yet populated — absence, never a fabricated default."""
    return _REGISTRY.get(program_slug)


def all_program_requirements() -> dict[str, ProgramRequirementsProfile]:
    return dict(_REGISTRY)


# ═══════════════════════════════════════════════════════════════════════
# Populated profiles — every fact below is read directly from the SAME
# primary/secondary sources already cited in this program's DoctrineRecord
# (executable_jurisdiction_registry.py / program_rate_rules_worldwide.py).
# No new research was required to populate these: the qualifying-
# expenditure research already performed for rate/doctrine classification
# this session and the prior worldwide-population phase already surfaced
# most of these facts — they were simply not yet captured in structured
# fields. Populated for the jurisdictions with the freshest, most complete
# primary-source citations; NOT yet populated for the remaining 99
# executable jurisdictions (a real, disclosed scope boundary — see the
# closeout report, not silently presented as complete coverage).
# ═══════════════════════════════════════════════════════════════════════

register(ProgramRequirementsProfile(
    program_slug="cy_film_rebate", jurisdiction_code="CY",
    cultural_test_required=True,
    min_local_spend_usd=200_000.0,  # EUR 200,000 feature films
    per_project_cap_usd=650_000.0,  # EUR 650,000 max aid per production
    atl_cap_pct_of_other_costs=0.30,  # ATL capped at 30% of total eligible expenditure
    annual_program_cap_usd=None,
    refundable=None, transferable=None,
    evidence=EvidenceRecord(
        source_title="Film in Cyprus — Incentives", source_url="https://film.investcyprus.org.cy/incentives/",
        issuing_authority="Cyprus Film Commission (Invest Cyprus)", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT,
        notes="Cultural-test scoring thresholds not confirmed from any source checked -- now including the "
              "primary legal instrument itself. Worldwide Qualification/Cultural/Co-production Completion, "
              "2026-08-19 (continuation pass): the actual Council of Ministers Decision 83.415 (27/09/2017) "
              "'Cyprus Film Scheme' document (cyprusprofile.com/storage/app/media/Cyprus_Film_Scheme.pdf) "
              "was read in full, all 36 pages including every appendix (document checklists for pre-/final "
              "approval, application/assessment process, Forms 1-2, production/location licensing, other "
              "applicable tax measures). Chapter 2 Incentive I/II para 4 states only that 'the Applicant "
              "must satisfy certain criteria which shall ensure that the aid promotes...Cypriot and/or "
              "European and/or world culture. The proposed cultural criteria are defined by cultural test' "
              "-- the point table/scoring breakdown itself is never printed anywhere in the document. This "
              "corroborates, from the primary legal instrument directly (not merely secondary commentary), "
              "that the scoring system exists and is administered by the Committee (Cyprus Film Commission) "
              "but is genuinely not published in any official document checked -- only multiple secondary "
              "sources (irglobal.com, exectus.com.cy, Cyprus Production Service) previously confirmed it "
              "'can be provided upon request'. This is a maximally-researched, confirmed hard authority "
              "blocker: the primary legal document itself was read cover-to-cover and does not contain the "
              "table, not merely 'not found via search'.",
    ),
    additional_facts={"cultural_test_uplift": "Base 35% -> ceiling 45% via cultural-test score (exact thresholds unconfirmed)"},
))

register(ProgramRequirementsProfile(
    program_slug="es_tax_credit_foreign", jurisdiction_code="ES",
    min_local_spend_usd=1_140_523.96,  # EUR 1M (EUR 200K for animation)
    per_project_cap_usd=22_810_479.13,  # EUR 20M per feature (EUR 10M per episode)
    cultural_test_required=False,
    evidence=EvidenceRecord(
        source_title="Ley 27/2014, Impuesto sobre Sociedades, Art. 36.2", source_url="https://sede.agenciatributaria.gob.es/",
        issuing_authority="Agencia Tributaria (Spanish Tax Agency)", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT,
        notes="Creative-personnel (ATL) category conditioned on EEA tax residence, max EUR 50,000/person.",
    ),
    additional_facts={"animation_min_spend_eur": "200,000", "atl_per_person_cap_eur": "50,000"},
))

register(ProgramRequirementsProfile(
    program_slug="hr_cash_rebate", jurisdiction_code="HR",
    # Worldwide Qualification/Cultural/Co-production Completion — 34 was
    # already documented verbatim in this record's own evidence note
    # ("minimum 12 of 34 points") but never set on cultural_test_points
    # itself, a genuine EXISTING_DATA_BUT_NOT_CONSUMED defect (Codex's
    # own vocabulary), now fixed. Re-confirmed 2026-08-19 against Zagreb
    # Film Office (filmzagreb.hr) and Cineuropa, consistent with the
    # existing Invest Croatia citation.
    cultural_test_required=True, cultural_test_points=34, cultural_test_threshold=12,
    min_local_spend_usd=265_000.0,  # HRK 2M ≈ EUR 263,000
    evidence=EvidenceRecord(
        source_title="Rebate for Film and TV Production", source_url="https://investcroatia.gov.hr/en/investment-guide/incentives/rebate-for-film-and-tv-production/",
        issuing_authority="Invest Croatia (official government investment-promotion agency)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT,
        notes="Cultural test: minimum 12 of 34 points, with a floor of 4 points in each of three categories "
              "(European cultural content / creative collaboration with Croatian-European personnel / use of "
              "Croatian production facilities). Administered by the Croatian Audiovisual Centre (HAVC). "
              "Exact per-role (director/writer/producer/cast) point allocation within the 34-point scale "
              "not confirmed from any source checked as of 2026-08-19 — AUTHORITY_UNRESOLVED for that "
              "sub-proposition specifically, not fabricated.",
    ),
    additional_facts={
        "regional_uplift": "+5% for filming in below-average-development regions", "administering_body": "HAVC",
        # New this pass, real, separately cited (Zagreb Film Office /
        # Cineuropa) — distinct from the cultural-test point scale above.
        "national_cast_crew_requirement": (
            "At least 30% of cast and crew must be Croatian citizens for productions "
            "filming partially in Croatia, or 50% for productions filming entirely in "
            "Croatia (Zagreb Film Office, https://filmzagreb.hr/?page_id=321; "
            "Cineuropa, https://cineuropa.org/en/newsdetail/203411; retrieved 2026-08-19)."
        ),
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_ga_film_credit", jurisdiction_code="US-GA",
    min_total_budget_usd=500_000.0, per_person_cap_usd=500_000.0,
    refundable=False, transferable=True,
    cultural_test_required=False,
    evidence=EvidenceRecord(
        source_title="O.C.G.A. § 48-7-40.26 (Georgia Entertainment Industry Investment Act)", source_url=None,
        issuing_authority="Georgia Department of Revenue / Georgia Department of Economic Development",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT,
        notes="Non-refundable, fully transferable. Development costs, promotion, marketing, story rights, and "
              "legal fees are expressly NOT qualified expenditures.",
    ),
    additional_facts={
        "logo_uplift": "+10% for an approved Georgia logo in the credits (20% base -> 30% total)",
        "typical_transfer_market_value": "~90 cents/dollar (market estimate, not statutory)",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_ny_film_credit", jurisdiction_code="US-NY",
    min_total_budget_usd=250_000.0,  # lower of the two regional thresholds
    atl_cap_pct_of_other_costs=0.40,
    annual_program_cap_usd=700_000_000.0,  # PROGRAM-wide, not per-production
    cultural_test_required=False,
    evidence=EvidenceRecord(
        source_title="NYS Film Tax Credit Program Guidelines", source_url="https://esd.ny.gov/sites/default/files/Film-Credit-Guidelines-wAppendix-06202023.pdf",
        issuing_authority="Empire State Development", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT,
        notes="Min spend $1,000,000 in NYC/Westchester/Rockland/Nassau/Suffolk, $250,000 elsewhere in NY — the "
              "lower figure is used here as the conservative floor.",
    ),
    additional_facts={
        "upstate_uplift": "+10% on qualified labor for >=$500K-budget productions shooting >50% of principal "
                          "photography days in designated upstate counties",
        "scoring_uplift": "+10% on scoring costs if scoring pays a minimum of 5 musicians",
        "min_spend_nyc_metro_usd": "1,000,000",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_ny_post_production_credit", jurisdiction_code="US-NY",
    # Worldwide Program Qualification + Cultural Test Completion, 2026-08-19.
    # Confirmed via the official tax.ny.gov program page: no cultural/
    # content test -- eligibility is spend/facility/diversity-plan based
    # (a diversity-plan filing requirement, distinct from a cultural
    # content test), consistent with every other US state incentive in
    # this registry.
    cultural_test_required=False,
    min_local_spend_usd=1_000_000.0,  # lesser of $1M or 75% of total post cost — dollar branch modeled
    refundable=None, transferable=None,
    evidence=EvidenceRecord(
        source_title="Empire State film post-production credit", source_url="https://www.tax.ny.gov/pit/credits/film_post.htm",
        issuing_authority="New York State Department of Taxation and Finance", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT,
        notes="Rate (35%) and full min-spend structure corroborated by a secondary aggregator, not read directly "
              "from the CT-261/IT-261 form instructions the official page defers to — PARSED, disclosed.",
    ),
    additional_facts={
        "mutual_exclusivity": "CONFIRMED mutually exclusive with us_ny_film_credit for the same costs (official)",
        "vfx_animation_subthreshold": "lesser of $500,000 or 10% of total post-production cost",
        "eligible_production_profile": "production shot substantially outside NY, post routed to an NY facility",
    },
))

register(ProgramRequirementsProfile(
    program_slug="be_tax_shelter", jurisdiction_code="BE",
    local_entity_required=True,  # eligible payee must be Belgian-tax-resident individual/company; production company must additionally be ACCREDITED by FPS Finance (confirmed via direct fetch, not previously recorded)
    cultural_test_required=True,  # certified "European work" (Audiovisual Media Services Directive 2010/13/EU) or qualifying co-production
    preapproval_mandatory=True,  # framework contract + FPS Finance accreditation of the production company precede any tax-shelter investment
    min_total_budget_usd=None,  # confirmed NO minimum threshold
    audit_or_final_certification_deadline=TimingFact(
        value="Tax Shelter certificate must be issued by 31 December of the fourth year following the "
              "year the framework contract was signed",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    payment_timing=TimingFact(
        value="Investors must deposit funds within three months of framework-contract signature; the "
              "tax exemption (310% of actual deposits, within applicable limits) converts from "
              "temporary to permanent relief only upon receipt of the Tax Shelter certificate",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="Tax Shelter — audiovisual production",
        source_url="https://finance.belgium.be/en/enterprises/corporation-tax/tax-benefits/tax-shelter-audiovisual-production",
        issuing_authority="FPS Finance (Federal Public Service Finance, Belgium)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST: the existing SECONDARY_VERIFIED profile (Scope Invest, a "
              "licensed Tax Shelter intermediary) already correctly recorded the mechanism (investor-side "
              "fiscal vehicle, not a direct producer credit), the 90%/70% Belgian-spend structure, the 30% "
              "admin-expense-share condition, and the 18/24-month expenditure window — none of that is "
              "contradicted by this direct fetch of the official FPS Finance page, so it is carried "
              "forward unchanged. NEWLY CONFIRMED FROM THE PRIMARY SOURCE (upgrading to PRIMARY_VERIFIED): "
              "legal basis is Article 194ter of the Belgian Income Tax Code 1992 (ITC 92), as amended by "
              "the laws of 12 May 2014 and 26 May 2016 (the 2016 amendment governs framework contracts "
              "signed from 1 July 2016 onward — the current regime). INVESTOR EXCLUSIONS (a genuine gate, "
              "not previously recorded): companies whose primary purpose is developing/producing "
              "audiovisual works, companies associated with the production company, and television "
              "broadcasters may NOT act as Tax Shelter investors. PRODUCTION-COMPANY ACCREDITATION GATE "
              "(genuinely new): the production company itself must be accredited by FPS Finance — a "
              "maintained, regularly-updated list of approved production companies and intermediaries "
              "exists; this is distinct from and in addition to the investor-side eligibility rules. "
              "MECHANISM PRECISION: the tax exemption equals 310% of the investor's actual deposits "
              "(within applicable limits) — the exact multiplier was not previously recorded. TIMING: "
              "investors must deposit funds within 3 months of framework-contract signature; the Tax "
              "Shelter certificate (which converts the exemption from temporary to permanent relief) must "
              "be issued by 31 December of the fourth year following the year the framework contract was "
              "signed — both genuinely new, specific statutory deadlines. Eligible works also include "
              "theatre and concert-hall productions, not only film/TV (broader than previously recorded, "
              "though out of scope for this profile's film/TV focus).",
    ),
    additional_facts={
        "mechanism": "investor tax-exemption vehicle, not a direct producer credit",
        "belgian_spend_requirement": "90% of expenses in Belgium; 70% of Belgian expenses must be direct production costs",
        "admin_expense_cap": "30% of total (proportion condition, not a category exclusion)",
        "expenditure_window": "18 months from framework agreement (24 months for animation)",
        "legal_basis": "Article 194ter, Belgian Income Tax Code 1992 (ITC 92), as amended by the laws of 12 May 2014 and 26 May 2016 (current regime governs framework contracts signed from 1 July 2016 onward).",
        "investor_exclusions": "Companies whose primary purpose is producing audiovisual works, associated companies, and television broadcasters may not act as Tax Shelter investors.",
        "production_company_accreditation": "The production company itself must be accredited by FPS Finance -- a distinct, maintained approval list.",
        "exemption_multiplier": "310% of the investor's actual deposits, within applicable limits.",
        "deposit_and_certificate_timing": "Investor deposit within 3 months of framework-contract signature; Tax Shelter certificate issued by 31 December of the fourth year following the contract-signing year.",
        "cultural_test_mechanism": (
            "RESOLVED 2026-08-19 (Worldwide Program Qualification Completion, Queue B): Belgium's "
            "'cultural test' is NOT a points-based scale like Austria/Germany/France/Poland -- it is "
            "recognition of the work as a 'European work' under Article 1(1)(n) of the EU Audiovisual "
            "Media Services Directive (2010/13/EU), OR as a qualifying official co-production under a "
            "bilateral treaty / the Council of Europe co-production convention. Confirmed via "
            "audiovisuel.cfwb.be (Fédération Wallonie-Bruxelles's Centre du Cinéma et de l'Audiovisuel, "
            "the competent Community authority for the French Community -- Belgium's film competence is "
            "regional, not federal): applications for 'agrément' (approval) as an eligible European/"
            "original work are submitted via the SUBside platform, decided within one month. This is a "
            "genuinely different, real mechanism from a scored point table -- the qualification IS the "
            "binary European-work/official-co-production legal status itself, not a threshold crossed on "
            "an aggregate score. No fabricated point table is recorded because none exists for this "
            "program."
        ),
    },
))

register(ProgramRequirementsProfile(
    program_slug="de_dfff", jurisdiction_code="DE",
    min_local_spend_usd=None,  # 20%-of-total-budget minimum, not an absolute dollar figure
    per_project_cap_usd=28_513_098.92,  # EUR 25,000,000
    # Worldwide Program Qualification + Cultural Test Completion, 2026-08-19
    # — internal consistency fix, no new research: cultural_qualification_
    # model.py already carries real NationalityRequirement rows for
    # de_dfff (director/producer, weighted, "must qualify under DFFF
    # Fachgutachten cultural test") — this field was simply never set to
    # match that already-existing real data (a genuine
    # DATA_EXISTS_BUT_STILL_NOT_CONSUMED-style inconsistency between two
    # canonical files, now reconciled).
    cultural_test_required=True,
    cultural_test_points=96,      # feature film (Anlage 3): A-Block 65 (Cultural Content 30 + Creative Talents 35) + B-Block Herstellung 31 = 96
    cultural_test_threshold=48,   # "Mindestens 48 von 96 Punkten aus beiden Blöcken notwendig"
    evidence=EvidenceRecord(
        source_title="Richtlinie der BKM 'Anreiz zur Stärkung der Filmproduktion in Deutschland' (Deutscher Filmförderfonds), vom 01.01.2025, Anlagen 3-6", source_url="https://www.ffa.de/files/dfff/richtlinie/250328_DFFF_Richtlinie_DE.pdf",
        issuing_authority="Die Beauftragte der Bundesregierung für Kultur und Medien (BKM), administered by the Filmförderungsanstalt (FFA)", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT, access_date="2026-08-19",
        notes="RESOLVED 2026-08-19, Worldwide Program Qualification Completion, Queue B: the official BKM "
              "Richtlinie (current version, in force from 01.01.2025) was read in full and its Anlagen 3-6 "
              "contain the complete, exact 'Eigenschaftstest' (property/cultural test) point tables for every "
              "format. FEATURE FILMS (Anlage 3): A-Block 'Kultureller Inhalt und kreative Talente' = Cultural "
              "Content sub-block (max 30 points across ~16 criteria, minimum 4 criteria must be satisfied -- "
              "German/EU/EEA/UK setting, motifs, shooting locations, source-material nationality, German-"
              "language final cut, etc., 1-3 points each) + Creative Talents sub-block (max 35 points -- "
              "German/EU/EEA/UK 'star' talent 4pts, 'European star' 2pts, lead/supporting cast 3pts max, and "
              "a weighted list of creative roles: director 3, screenwriter 3, (co-)producer/line producer 3, "
              "composer 2, cinematographer 2, editor 2, costume/lead animation artist 1, makeup/lead FX artist "
              "1, sound designer 1, production designer 1, art director 1, lead compositing artist 1, VFX "
              "producer 2, VFX supervisor 2, post-production supervisor 1) = A-Block subtotal 65. B-Block "
              "'Herstellung' (Production, max 31 points) = German/EU shooting-or-studio-work tiers (12pts at "
              "50%+ of shoot costs in Germany, or 8pts if no live shoot and VFX/SFX thresholds met), digital-"
              "effects tiers (max 4), music/sound/post-production/copy-work tiers (2+2+1+3+3). TOTAL 96, "
              "MINIMUM 48 OF 96 FROM BOTH BLOCKS COMBINED. DOCUMENTARIES (Anlage 4): A-Block Cultural Content "
              "(max 19, minimum 2 of ~8 criteria) + Creative Talents (max 20 -- director 5, producer 3, "
              "writer 3, cinematographer 3, editor 3, composer 2, sound/music design 1) = 39; B-Block "
              "Herstellung (max 13 -- shoot 5, digital effects 1, music 2, sound 2, image 2, copy 1) = 52 "
              "total, MINIMUM 27 OF 52. ANIMATION/ANIMATED FILMS (Anlage 5): A-Block Cultural Content (max "
              "25, minimum 2 of ~8 criteria) + Creative Talents (max 27 -- director 3, writer/storyboarder 3, "
              "(co-)producer/VFX producer 3, composer 3, VFX/animation supervisor 3, character designer/lead "
              "FX artist 2, head of production design 2, voice actors 4 (1pt per lead role, first 4), sound "
              "designer 1, lead shading/texturing 1, editor/lead compositing 1, production manager/non-"
              "applicant VFX producer 1) = 52; B-Block Herstellung (max 32 -- 10pts for 100% of animation/VFX "
              "costs spent in Germany at 1pt/10%, plus rigging/layout, previsualization, digital environment, "
              "virtual camera, animatics, simulations, sound/dubbing/mixing/VFX-asset work, music, rendering, "
              "compositing, final-media prep, each at 80%-in-Germany thresholds) = 84 total, MINIMUM 42 OF 84. "
              "DOCUMENTARIES under the Council of Europe Convention on Cinematographic Co-production (Anlage "
              "6, separate simplified test): creative talents (director 3, screenplay 2, camera 2, "
              "researcher 1, composer 1, editor 2, sound engineer 1) + production (shoot 2, post-production "
              "2) = 16 total, minimum 50%. A 2027 restructured framework (draft as of May 2026) will supersede "
              "today's DFFF/GMPF figures -- current regime only, not modeled prospectively.",
    ),
    additional_facts={
        "min_german_spend_pct_of_budget": "20% (not independently fetched from primary BKM guideline text)",
        "max_pct_of_total_production_costs": "80%",
        "shooting_abroad_allowance": "up to 40% of entire shoot may be abroad if dramaturgically required, still counts as German costs",
        "contingency_treatment": "excluded UNLESS dissolved in the final cost report into eligible goods/services",
        "cultural_test_full_point_tables": "Anlage 3 (feature film, 96 total/48 min), Anlage 4 (documentary, 52 total/27 min), Anlage 5 (animation, 84 total/42 min), Anlage 6 (documentary under European Convention, 16 total/50%) -- full category breakdown in evidence notes above.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="hu_hipa_rebate", jurisdiction_code="HU",
    cultural_test_required=True, cultural_test_threshold=16,
    evidence=EvidenceRecord(
        source_title="Hungarian Film Incentive", source_url="https://nfi.hu/en/filming-in-hungary/hungarian-film-incentive",
        issuing_authority="National Film Institute Hungary (NFI)", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT,
        notes="'Cash refund (post-financing)' payment mechanism. Cultural test: EU-participation scoring, 16 "
              "points required. Total state subsidies capped at 50% of production budget (%-of-budget, not modeled).",
    ),
    additional_facts={
        "cross_border_uplift": "extendable to 37.5% by including non-Hungarian costs, capped at 25% of the rebate",
        "royalty_subcap_pct": "4% of film production expenses",
        "producer_fee_subcap_pct": "4% of film production expenses",
        "advertising_subcap": "2% of film production expenses, capped at HUF 10,000,000",
        "nonhungarian_subcontractor_limit_pct": "25% of eligible Hungarian spend",
    },
))

register(ProgramRequirementsProfile(
    program_slug="it_tax_credit_foreign", jurisdiction_code="IT",
    cultural_test_required=True, cultural_test_points=None, cultural_test_threshold=50,
    min_local_spend_usd=None,          # EUR 250,000 minimum eligible cost — recorded in additional_facts/STATUTORY_AMOUNTS_ORIGINAL_CURRENCY, not converted
    per_project_cap_usd=22_810_479.13,  # EUR 20M per year per company (a per-COMPANY annual cap — distinct from the per-WORK cap recorded in additional_facts)
    preapproval_mandatory=True,        # two-phase DGCOL process: preventive request at production start, definitive request after completion
    expenditure_before_approval_qualifies=False,
    local_entity_required=True,        # eligible production company must have EEA headquarters and be subject to Italian taxation
    transferable=True,
    application_deadline=TimingFact(
        value="DGCA communicates recognition of the tax credit within 60 days of receiving the application",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="Tax Credit — Introduzione",
        source_url="https://cinema.cultura.gov.it/cosa-facciamo/sostegni-economici/linee-di-sostegno/tax-credit/introduzione/",
        issuing_authority="Direzione Generale Cinema e Audiovisivo (DGCA), Ministero della Cultura",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST: the existing SECONDARY_VERIFIED profile (Mestiere "
              "Cinema, an Italian production consultancy) already correctly recorded the cultural "
              "test structure (50/100 points, 35-point floor in Block A), the per-company annual "
              "cap (EUR 20,000,000), transferability, and several BTL/overhead/ATL details — none "
              "of that is contradicted by this direct fetch of DGCA's own official page (Direzione "
              "Generale Cinema e Audiovisivo, the actual governing authority under the Ministero "
              "della Cultura), so it is carried forward unchanged. This upgrades the profile to "
              "PRIMARY_VERIFIED. LEGAL BASIS (genuinely new): D.I. MiC and MEF (Ministero della "
              "Cultura + Ministero dell'Economia e delle Finanze) of 4 January 2023, rep. 1. "
              "APPLICATION PROCESS (genuinely new): submitted through the DGCOL platform, in TWO "
              "PHASES — a preventive request at production start, and a definitive request after "
              "completion; DGCA communicates recognition within 60 days of receiving the "
              "application. COMPANY ELIGIBILITY GATE (genuinely new, local_entity_required "
              "corrected from unset to True): the eligible production company must have its "
              "headquarters in the European Economic Area, be subject to Italian taxation, "
              "maintain minimum capital of EUR 40,000 and equivalent net equity, and hold ATECO "
              "classification J 59.1 (Italy's standard industrial classification code for "
              "motion-picture/video/TV programme production). MINIMUM ELIGIBLE COST (genuinely "
              "new, from a WebSearch summary citing the DGCA framework, not independently "
              "re-confirmed on the specific introduzione page fetched): EUR 250,000. PER-WORK CAP "
              "(genuinely new and DISTINCT from the existing per-company annual cap — both real, "
              "recorded separately): EUR 9,000,000 per work, increasable to EUR 18,000,000 if at "
              "least 30% of total production cost is covered by foreign funding — same caveat, not "
              "independently re-confirmed on the DGCA introduzione page itself. REGULATORY CHANGE "
              "REPORTED BUT NOT CONFIRMED ON THE OFFICIAL PAGE: a WebSearch summary stated the "
              "requirement to include at least one day of filming/work on Italian territory has "
              "been eliminated — this is NOT asserted here as confirmed fact (the official page "
              "fetched did not address it), flagged as an open item for a future pass rather than "
              "recorded on search-snippet confidence alone.",
    ),
    additional_facts={
        "btl_eu_national_requirement_pct": "51% of below-the-line employees must be Italian or EU citizens",
        "overhead_cap_pct": "7.5% of production costs",
        "atl_outside_eea_rate": "30% (reduced from the 40% standard rate)",
        "payee_requirement": "only costs paid directly by the Italian production company are eligible",
        "legal_basis": "D.I. MiC and MEF (Ministero della Cultura + Ministero dell'Economia e delle Finanze), 4 January 2023, rep. 1.",
        "application_process": "Two-phase DGCOL platform process: preventive request at production start, definitive request after completion. DGCA responds within 60 days of application.",
        "company_eligibility_gate": "EEA headquarters, subject to Italian taxation, minimum capital EUR 40,000 + equivalent net equity, ATECO classification J 59.1.",
        "min_eligible_cost_eur": "EUR 250,000 minimum eligible cost (WebSearch summary citing the DGCA framework, not independently re-confirmed on the specific page fetched).",
        "per_work_cap_eur": "EUR 9,000,000 per work, increasable to EUR 18,000,000 if at least 30% of total production cost is foreign-funded -- distinct from the EUR 20,000,000 per-company annual cap (not independently re-confirmed on the specific page fetched).",
        "unconfirmed_regulatory_change": "A WebSearch summary reported that the minimum-one-day-of-Italian-filming requirement has been eliminated -- NOT confirmed on the official DGCA page fetched this session; open item for a future pass.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_nm_film_credit", jurisdiction_code="US-NM",
    annual_program_cap_usd=140_000_000.0,  # FY2026 program-wide fund cap
    refundable=True,
    cultural_test_required=False,
    evidence=EvidenceRecord(
        source_title="Allowable Fiscal Year 2026 Film Fund Cap", source_url="https://www.tax.newmexico.gov/",
        issuing_authority="New Mexico Taxation and Revenue Department", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT,
        notes="Rate structure (25% base, uplifts to 40%) corroborated by three independent secondary sources, not "
              "the official nmfilm.com program page (404'd on direct fetch).",
    ),
    additional_facts={
        "rural_uplift": "+10% for productions >=60 miles from Albuquerque/Santa Fe",
        "tv_pilot_series_uplift": "+5%",
        "qualified_facility_uplift": "+5%",
    },
))

# Final Global Discovery phase, Task 92 (bounded discovery pass): the
# first two of the 95 currently-executable-but-requirements-less
# programs, selected for being high-value and well-documented by their
# own government administrators.
register(ProgramRequirementsProfile(
    program_slug="uk_avec", jurisdiction_code="GB",
    cultural_test_required=True,
    preapproval_mandatory=True,  # BFI Interim Certificate before/during production
    audit_or_final_certification_deadline=TimingFact(
        value="Two years from the end of the company's accounting period "
              "(42 months from the start of the period for long periods "
              "over 18 months)",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    refundable=True,
    transferable=False,  # no transfer/assignment mechanism found in any source reviewed
    evidence=EvidenceRecord(
        source_title="CREC080200 - Claims: introduction",
        source_url="https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual/crec080200",
        issuing_authority="HM Revenue & Customs (HMRC)", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT,
        notes="Claim mechanism: 'a Company Tax Return, including a completed CT600, CT600P "
              "supplementary page, accounts and computations,' filed digitally through the "
              "online Corporation Tax gateway. Refundable ('can either reduce the amount of "
              "tax payable by the company or be a payable credit to the company where the "
              "company isn't paying tax') corroborated by creative.accountants (secondary) "
              "summarizing the same HMRC CIEC regime, not independently confirmed on this "
              "specific gov.uk page. BFI certification (interim certificate available before "
              "completion) required per bfi.org.uk (official) — see cultural test citation "
              "on the executable doctrine record.",
    ),
    additional_facts={
        "enhanced_rate_budget_band": "The enhanced core rate applies to the first GBP 15,000,000 "
                                      "of total core expenditure on productions with total core "
                                      "expenditure up to GBP 23,500,000 (bfi.org.uk) — a rate band, "
                                      "not a minimum-spend eligibility gate; not modeled as "
                                      "min_total_budget_usd because it caps at a HIGH budget, not a low one.",
        "regime_transition": "All qualifying productions must claim under the Audio-Visual "
                              "Expenditure Credit (rather than the predecessor Film Tax Relief) "
                              "from 1 April 2027 (bfi.org.uk) — a transition completion date for "
                              "the OLD regime, not a sunset of AVEC itself.",
        "administering_unit": "HMRC's Creative Industries Unit (Manchester) handles Corporation "
                               "Tax affairs for most AVEC claimants.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="nz_spg_international", jurisdiction_code="NZ",
    # Worldwide Program Qualification + Cultural Test Completion, 2026-08-19
    # — internal consistency fix, no new research: cultural_qualification_
    # model.py's _SPEND_ONLY_SLUGS already classifies this exact
    # program_slug as spend-only (confirmed via NZFC, prior pass), but
    # this field was never explicitly set to match. Now reconciled.
    cultural_test_required=False,
    preapproval_mandatory=True,
    expenditure_before_approval_qualifies=None,  # not confirmed either way from sources reviewed
    application_deadline=TimingFact(
        value="Provisional Certificate application must be submitted before the start of "
              "principal photography",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    audit_or_final_certification_deadline=TimingFact(
        value="Final application within six months of completion of the full production, "
              "with an independent auditor's report from an NZFC-approved provider",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    audit_required=True,
    cpa_or_approved_auditor_required=True,
    evidence=EvidenceRecord(
        source_title="New Zealand Screen Production Rebate for International Productions",
        source_url="https://www.nzfilm.co.nz/incentives-co-productions/nzspg-international",
        issuing_authority="New Zealand Film Commission (NZFC)", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT,
        notes="'Provisional Certification becomes mandatory if you're applying for the "
              "Production Rebate 5% Uplift' — otherwise the Provisional Certificate is a "
              "non-binding eligibility opinion, not confirmed mandatory for the base 20% rate "
              "specifically. Refundability/transferability/payment-timing-after-claim were not "
              "found on any source reviewed and are left unstated (Not stated), not guessed. "
              "The program's own name transitioned from 'Screen Production Grant' (NZSPG) to "
              "'Screen Production Rebate' (NZSPR) — already correctly reflected in this "
              "engine's existing executable doctrine record program_name; not a new discovery.",
    ),
    additional_facts={
        "criteria_cutover": "New Zealand productions starting Principal Photography on or "
                             "after 31 August 2023 are assessed under NZSPR criteria; earlier "
                             "productions under the prior NZSPG criteria (nzfilm.co.nz) — a "
                             "domestic-production-component fact, included for completeness "
                             "though this profile is for the international component.",
    },
))

# Backend-completion tranche, Objective 2: batch of five (three of which
# close a legacy pre-canonical-registry gap: IE, FR, and CA closes none
# but is a major, well-documented program).
register(ProgramRequirementsProfile(
    program_slug="ie_section_481", jurisdiction_code="IE",
    preapproval_mandatory=True,
    application_deadline=TimingFact(
        value="Interim certificate application at least 21 working days before the "
              "first day of principal photography in Ireland",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    refundable=True,
    per_project_cap_usd=142_565_494.59,  # EUR 125,000,000 for projects certified on/after 28 Mar 2024
    cultural_test_required=True,
    evidence=EvidenceRecord(
        source_title="Film Relief (Section 481 Film Tax Credit)",
        source_url="https://www.revenue.ie/en/companies-and-charities/reliefs-and-exemptions/film-relief/index.aspx",
        issuing_authority="Irish Revenue Commissioners", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT,
        notes="'If the relief is more than the tax due, Revenue will pay the difference.' "
              "Rate: 32% of the lowest of eligible expenditure, 80% of total qualifying "
              "costs, or EUR 125,000,000 (prior EUR 70,000,000 cap still applies to "
              "productions certified before 28 Mar 2024 — not modeled, this profile is for "
              "current productions). Interim-certificate timing corroborated by "
              "screenireland.ie and lexology.com (secondary) — not independently found on "
              "this Revenue page. Transferability not addressed on any source reviewed.",
    ),
    additional_facts={
        "interim_certificate_validity": "Two years from date of issue (screenireland.ie, secondary)",
        "claim_options": "Option 1: full credit in one instalment after completion. Option 2: "
                          "up to 90% in advance once a Cultural Certificate is obtained, at "
                          "least 68% of eligible Irish spend is secured, and funding "
                          "conditions are certified by Screen Ireland/BAI/a recognised EEA "
                          "funding body (screenireland.ie, secondary).",
        "post_finance_act_2018": "Revenue is no longer involved in the pre-production "
                                  "application; the Minister for Tourism/Culture/Arts/"
                                  "Gaeltacht/Sport/Media now administers certification "
                                  "under self-assessment (revenue.ie).",
    },
))

register(ProgramRequirementsProfile(
    program_slug="ca_federal_pstc", jurisdiction_code="CA",
    # Worldwide Program Qualification + Cultural Test Completion, 2026-08-19.
    # Confirmed via canada.ca (official CAVCO/CRA program page, primary
    # authority): "Unlike the CPTC, there is no Canadian content
    # requirement — this credit is designed to attract foreign
    # productions." PSTC is deliberately service/spend-based, distinct
    # from the content-gated CPTC (ca_federal_cptc, already covered by
    # cultural_qualification_model.py's role registry).
    cultural_test_required=False,
    preapproval_mandatory=True,
    refundable=True,
    min_local_spend_usd=None,  # CAD figure not converted — see additional_facts (labour-spend threshold, not total budget)
    audit_or_final_certification_deadline=TimingFact(
        value="Part B (Certificate of Completion) application due no later than 24 months "
              "from the first taxation year end following the start of principal "
              "photography, extendable by a further 18 months under conditions — figures "
              "confirmed for the sibling CPTC program, presumed but NOT independently "
              "confirmed to be identical for PSTC specifically",
        basis=TimingBasis.ESTIMATE,
    ),
    evidence=EvidenceRecord(
        source_title="Film or Video Production Services Tax Credit",
        source_url="https://www.canada.ca/en/canadian-heritage/services/funding/cavco-tax-credits/film-video-production-services.html",
        issuing_authority="Canadian Audio-Visual Certification Office (CAVCO) / Canada Revenue Agency (CRA)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT,
        notes="'Because the PSTC is refundable, you can receive the credit even if you owe "
              "no corporate income tax.' Co-administered by CAVCO (Canadian Heritage) and "
              "CRA. Minimum Canadian labour spend: CAD 1,000,000 per project or 75% of "
              "total production cost if less (secondary source corroboration — not "
              "independently confirmed on a canada.ca page directly fetched, 403-blocked). "
              "The 24-month/18-month completion-certificate deadlines were found on CPTC "
              "(Canadian Film or Video Production Tax Credit, a DIFFERENT, domestic-owned-"
              "production program) documentation, not confirmed identical for PSTC — "
              "marked ESTIMATE, not STATUTORY_DEADLINE, for this reason.",
    ),
    additional_facts={
        "min_canadian_labour_spend": "CAD 1,000,000 per project, or 75% of total production "
                                      "cost if less (granthub.ca / creativebc.com, secondary) "
                                      "— a labour-expenditure threshold, not a total-budget "
                                      "minimum; not modeled as min_local_spend_usd to avoid "
                                      "conflating the two.",
        "eligible_applicant": "A taxable Canadian corporation OR a foreign-owned corporation "
                               "primarily engaged, through a Canadian permanent establishment, "
                               "in film/video production or production-services business.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="cz_film_incentive", jurisdiction_code="CZ",
    cultural_test_required=True,  # corrects the profile's own prior silence and the rate rule's prior False -- confirmed directly this session
    cultural_test_points=46,      # confirmed 2026-08-19 via the official Czech Film Commission "Production Incentives" PDF
    cultural_test_threshold=23,   # min 23/46 overall, WITH a sub-minimum of >=4 from the 8 Cultural criteria items specifically
    preapproval_mandatory=False,  # costs up to 6 months BEFORE the application may still qualify
    expenditure_before_approval_qualifies=True,
    audit_required=True,
    cpa_or_approved_auditor_required=True,
    annual_program_cap_usd=None,  # CZK 450,000,000 per-project cap -- recorded in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY, not converted here
    payment_timing=TimingFact(
        value="No later than three years after settlement of audited eligible costs",
        basis=TimingBasis.REPORTED_PRACTICAL,
    ),
    evidence=EvidenceRecord(
        source_title="Production Incentives", source_url="https://sfa.gov.cz/production-incentives",
        issuing_authority="Státní fond audiovize / Czech Film Fund (State Cinematography Fund)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST: this profile itself already flagged the exact gap "
              "closed here — its prior notes explicitly said the sfa.gov.cz page 'was not "
              "independently fetched in this session' and was marked SECONDARY pending that. Direct "
              "fetch performed this session; this upgrades the profile to PRIMARY_VERIFIED. "
              "PREVIOUSLY-RECORDED FACTS CONFIRMED, NOT CONTRADICTED: 'costs incurred up to 6 months "
              "before the application for filing is submitted' may be claimed; physical production "
              "must start within 6 months of the filing application; within 4 months of the "
              "allocation application, at least 10 shooting days in the Czech Republic must be "
              "completed; final application requires audited statements and an auditor's "
              "verification report; rate structure 25% live-action / 35% animation-digital "
              "(projects registered from 2025) — now cross-checked directly against the official "
              "page and confirmed, resolving this profile's own prior note that it was 'not yet "
              "cross-checked against this engine's own rate-rule doctrine record'. NEWLY CONFIRMED: "
              "a CULTURAL TEST is required (KNOWLEDGE RECONCILIATION performed — this corrected the "
              "rate rule's prior requires_cultural_test=False in both cz_film_incentive and "
              "cz_film_incentive_animation, and jurisdiction_comparison.py's CZ profile, not just "
              "this Requirements Profile). MINIMUM SPEND BY FORMAT: CZK 15,000,000 feature/animated "
              "films; CZK 2,000,000 documentaries; CZK 8,000,000 per episode TV series; CZK "
              "1,000,000 per episode animated series/digital production. ANNUAL/PER-PROJECT CAP: "
              "CZK 450,000,000 maximum per project, with eligible costs additionally capped at 80% "
              "of total budget — two distinct constraints, recorded separately. APPLICATION "
              "TIMING: registration and rebate allocation are available year-round (no fixed annual "
              "cycle/deadline). OPEN ITEM, not asserted: the page references changes effective "
              "2026-01-01 without detailing them in the content retrieved — flagged for a future "
              "pass rather than guessed at. All CZK thresholds recorded in "
              "STATUTORY_AMOUNTS_ORIGINAL_CURRENCY per the Canonical Currency Rule. CULTURAL TEST "
              "(RESOLVED 2026-08-19, Worldwide Program Qualification Completion, Queue B): the "
              "exact point table was found in the official Czech Film Commission 'Production "
              "Incentives' PDF (sfa.gov.cz/data/download/2025/10/CFC-ProductionIncentives-A4-f1.pdf "
              "— issued directly by the Czech Film Commission, a division of the Czech Audiovisual "
              "Fund, the same administering authority already cited above). Total 46 points across "
              "two blocks; pass requires >=23 of 46 overall AND >=4 from the Cultural criteria block "
              "specifically. Cultural criteria (max 16, 8 items at 0-2 points each): story based on "
              "European-culture events; story based on a European-culture personality; storyline "
              "connected with a European setting; film based on a work of cultural importance; film "
              "focuses on current European-society themes; film reflects important European values; "
              "film focuses on European culture/customs/traditions; film based on events affecting "
              "European society. Production criteria (max 30, 7 items): genre contribution (0-3); "
              "Czech/EEA filmmakers (0-7); EEA-language final version (0-4); >=51% EEA-citizen crew "
              "(0 or 4, binary); Czech Republic shooting (0-4); Czech service providers (0-4); Czech "
              "post-production (0-4).",
    ),
    additional_facts={
        "rate_by_content_type": "25% cash rebate for feature/documentary films and fictional "
                                 "TV series; 35% for animated films/series and digital "
                                 "production (projects registered from 2025) — now directly "
                                 "confirmed via the official sfa.gov.cz page.",
        "withholding_tax_rebate": "66% cash rebate on withholding tax paid in the Czech Republic — a distinct mechanism from the QPE rebate.",
        "min_spend_by_format_czk": "CZK 15,000,000 feature/animated films; CZK 2,000,000 documentaries; CZK 8,000,000 per episode TV series; CZK 1,000,000 per episode animated series/digital production.",
        "cap_structure": "CZK 450,000,000 maximum per project; eligible costs additionally capped at 80% of total budget.",
        "application_timing": "Registration and rebate allocation available year-round; no fixed annual application cycle.",
        "pending_2026_changes": "The official page references changes effective 2026-01-01 without detail in the content retrieved -- open item for a future primary-verification pass.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="pl_pisf_cash_rebate", jurisdiction_code="PL",
    preapproval_mandatory=True,
    application_deadline=TimingFact(
        value="Application may be submitted no earlier than 12 months before, and must be "
              "submitted before, the start of the work it covers",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    allocation_type=AllocationType.FIRST_COME_FIRST_SERVED,
    audit_required=True,
    payment_timing=TimingFact(
        value="Paid after production completion and a passed audit of the final report",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    cultural_test_required=True,
    cultural_test_points=48,     # post-Nov-2024 amendment (reduced from the prior scale)
    cultural_test_threshold=25,  # ~51% of 48, consistent with the base Act's "co najmniej 51%" rule (Art. 17(3)/21(2))
    evidence=EvidenceRecord(
        source_title="PISF — Information (zachęty); statutory basis: Ustawa z dnia 9 listopada 2018 r. o finansowym wspieraniu produkcji audiowizualnej (Dz.U. 2019 poz. 50), Art. 16(4)/17(3)/21(2)/31(1)(5); test point scale: Rozporządzenie Ministra Kultury i Dziedzictwa Narodowego w sprawie szczegółowego wykazu polskich kosztów kwalifikowalnych..., Załącznik nr 4 (as amended 12 November 2024)",
        source_url="https://eli.sejm.gov.pl/eli/DU/2019/50/ogl",
        issuing_authority="Polish Film Institute (PISF); Ministry of Culture and National Heritage (statutory/regulatory basis)", source_type=SourceType.PRIMARY,
        status=RecordStatus.CURRENT, access_date="2026-08-19",
        notes="Facts gathered via search-engine summary citing pisf.pl and "
              "polishfilmcommission.pl; direct fetch of pisf.pl returned HTTP 403 in this "
              "session — marked SECONDARY pending direct primary confirmation. 'There are no "
              "deadlines; applications are processed in order of submission until the funds "
              "for a given year are depleted' (first-come-first-served, not competitive). "
              "PISF processes applications within 28 calendar days. CULTURAL TEST (RESOLVED "
              "2026-08-19, Worldwide Program Qualification Completion, Queue B): the base "
              "statute (Ustawa z 9 listopada 2018 r., Dz.U. 2019 poz. 50) Art. 16(4) defines the "
              "test's five focus areas (Polish/European cultural heritage in the work; action "
              "location in Poland; production carried out in Poland; participation of Polish "
              "staff/crews/service providers; use of Polish film infrastructure) and Arts. 17(3) "
              "and 21(2) fix the passing threshold at 'co najmniej 51% punktów możliwych do "
              "uzyskania' (at least 51% of possible points) -- a percentage rule, not a fixed "
              "point figure, by design (Art. 31(1)(5) delegates the exact point template/criteria "
              "to a Ministry of Culture and National Heritage regulation, Załącznik nr 4). That "
              "regulation was amended 12 November 2024, REDUCING the maximum score to 48 points "
              "(from a prior, higher scale) with a minimum of 25 points now required -- 25/48 = "
              "52.1%, consistent with the base statute's 51%-of-possible-points rule. The exact "
              "category-by-category point allocation within the 48-point scale (i.e. how many "
              "points each of the five Art. 16(4) focus areas carries) was not independently "
              "confirmed from the regulation's own Załącznik nr 4 text this pass -- AUTHORITY "
              "UNRESOLVED for that specific sub-proposition, not fabricated; the aggregate "
              "48-point/25-point pass threshold IS confirmed from a primary government source.",
    ),
    additional_facts={
        "processing_target": "PISF targets a 28-calendar-day processing time for applications "
                              "(search summary, secondary).",
        "primary_source_attempt_2026_07_26": "Four further attempts made this session to reach an "
            "official/near-official source: pisf.pl/en/zachety-informacje/ (403, already noted "
            "above) and pisf.pl/test-en-test/incentives-information/ (403 again); "
            "polishfilmcommission.pl (TLS certificate hostname mismatch -- cert issued for "
            "*.nazwa.pl, not the requested domain); cineuropa.org's dedicated article (403). None "
            "reachable. A WebSearch summary (not independently fetched, recorded with that caveat) "
            "citing polishfilmcommission.pl's '30% Cash Rebate Basics' page adds: legal basis is "
            "the Act on Financial Support for Audiovisual Production; minimum spend EUR 240,000 "
            "(PLN 1,000,000) for animated features and fiction/animated/documentary series (per "
            "episode for fiction series, per season for documentary/animated series); EUR 70,000 "
            "(PLN 300,000) for documentaries; per-project cap EUR 3,330,000 (PLN 15,000,000); "
            "per-applicant annual cap EUR 4,760,000 (PLN 20,000,000). NOT asserted as confirmed "
            "primary fact -- recorded here so a future session with a working URL does not have to "
            "re-derive it from scratch.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="fr_trip", jurisdiction_code="FR",
    preapproval_mandatory=True,
    application_deadline=TimingFact(
        value="Provisional qualification generally issued within one month of submission; "
              "the CNC's receipt date becomes the start date for counting eligible expenses",
        basis=TimingBasis.REPORTED_PRACTICAL,
    ),
    refundable=True,
    transferable=None,  # "discountable at a financial institution" is loan-security use, not confirmed as a legal assignment/transfer
    min_local_spend_usd=285_130.99,  # EUR 250,000
    per_project_cap_usd=34_215_718.70,  # EUR 30,000,000
    cultural_test_required=True,
    cultural_test_points=38,     # fiction works (Code du cinéma et de l'image animée, Art. D331-42 à D331-46) -- see evidence notes for animation's separate scale
    cultural_test_threshold=18,  # min 18/38, WITH a sub-minimum of >=7 points from the "Contenu dramatique" (Dramatic Content) group specifically
    evidence=EvidenceRecord(
        source_title="The Tax Rebate for International Productions (TRIP); cultural-test point scale: Code du cinéma et de l'image animée, Art. D331-40 à D331-51 (Décret n° 2014-794, partie réglementaire)",
        source_url="https://www.legifrance.gouv.fr/codes/id/LEGIARTI000030063177/2015-01-01/",
        issuing_authority="Centre national du cinéma et de l'image animée (CNC); statutory basis published via Légifrance (French official legal database)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-08-19",
        notes="'If the amount of the tax rebate exceeds the corporate income tax due for "
              "this year, the difference will be paid by the French State' (refundable). "
              "'It is possible to discount the rebate at a financial institution, under "
              "certain conditions provided for by the law' — this is bridge-financing/"
              "factoring against the credit, not confirmed to be a legal transfer/assignment "
              "in the sense modeled elsewhere (e.g. Italy) — left as None (Not stated) rather "
              "than guessed either way. Minimum spend: EUR 250,000 or at least 50% of total "
              "production budget on French QPE (whichever governs not fully disambiguated in "
              "sources reviewed). CULTURAL TEST (RESOLVED 2026-08-19, Worldwide Program "
              "Qualification Completion, Queue B): the CNC's own official BOFiP tax-authority "
              "page (bofip.impots.gouv.fr, BOI-IS-RICI-10-40-20240228) cites the operative "
              "statutory basis as Articles D.331-40 to D.331-51 of the Code du cinéma et de "
              "l'image animée ('deux barèmes de points' -- two separate point scales, fiction "
              "and animation). The fiction scale (Art. D331-42-D331-46, via Légifrance, the "
              "official French legal database) requires a minimum of 18 of 38 total points, "
              "WITH a sub-requirement of at least 7 points specifically from the 'Contenu "
              "dramatique' (Dramatic Content) group, across at least two of the three point "
              "groups: (1) Dramatic Content (max 18: locations up to 7, character nationalities "
              "up to 4, subject/story themes 5, French-language dubbing/subtitles 2); (2) "
              "Creator Nationality (max 12: director/screenwriter 2, composer 1, producer(s) 2, "
              "principal/secondary cast 1-2, crew composition 1, department heads 1-3); (3) "
              "Creation Infrastructure (max 8: shooting days in France 1-3, French VFX/SFX spend "
              "1, French equipment rental 1, French lab work 1, French post-production 2). A "
              "separate animation-specific scale exists (Art. D331-47-D331-51) but was not "
              "independently confirmed this pass -- the fiction scale governs the vast majority "
              "of TRIP-eligible live-action productions and is the one recorded here.",
    ),
    additional_facts={
        "vfx_uplift": "Rate rises to 40% (from 30%) if French VFX expenditure exceeds EUR 2,000,000.",
        "min_spend_alternate_test": "50% of total production budget spent as French QPE is "
                                     "an alternative test to the EUR 250,000 absolute minimum "
                                     "— relationship between the two (whichever is lower/"
                                     "higher governs) not fully disambiguated in sources reviewed.",
    },
))


# ── Final Additive Completeness Sweep (2026-07-25): production-relevant US
#    programs completed from official state sources. US state film incentives
#    have no cultural test (a positively-known fact, so cultural_test_required
#    is set False, not None). Facts read from the official state film-office /
#    economic-development pages cited per profile.

register(ProgramRequirementsProfile(
    program_slug="us_la_film_incentive", jurisdiction_code="US-LA",
    cultural_test_required=False,
    min_local_spend_usd=300_000.0,  # $50,000 for a Louisiana-screenplay production (see notes)
    preapproval_mandatory=True,      # LED issues Initial Certification before expenses are tracked
    audit_required=True,
    cpa_or_approved_auditor_required=True,  # independent CPA selected by LED's Office of Entertainment Industry Development
    refundable=False,                # offsets LA income tax; not refundable in the traditional sense
    transferable=True,               # transferable, incl. transfer back to the State at 90% of face (2% fee -> 88% net)
    transfer_approval_required=None, # transfer-back-to-State mechanism defined; broker-market transfer approval not separately confirmed
    annual_program_cap_usd=125_000_000.0,  # reduced from $150M for applications received on/after 2025-07-01 (see notes)
    allocation_type=AllocationType.FIRST_COME_FIRST_SERVED,
    evidence=EvidenceRecord(
        source_title="Motion Picture Production Program — Louisiana Economic Development",
        source_url="https://www.opportunitylouisiana.gov/incentive/motion-picture-production-program",
        issuing_authority="Louisiana Economic Development (LED), Office of Entertainment Industry Development",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-25",
        notes="Official LED program page (fetched 2026-07-25). Minimum in-state spend: $300,000 "
              "general; $50,000 for a Louisiana-screenplay production. Credits transferable, "
              "including transfer BACK to the State for 90% of face value with a 2% fee (88% net). "
              "Initial Certification issued before expense tracking; independent CPA expenditure-"
              "verification report mandatory (applicant deposits $5,000-$15,000 for audit cost). "
              "ANNUAL CAP CONFLICT/CHANGE: the LED page text states $150M/fiscal year, but the "
              "2025 reform (LED emergency rule + LA Dept. of Revenue guidance) reduced the front-"
              "and back-end caps to $125M for applications received on/after 2025-07-01; the "
              "recent $125M figure is used here. Per-project limit is a rate cap (credits cannot "
              "exceed 40% of the base investment), not a fixed dollar per-project cap.",
    ),
    additional_facts={
        "screenplay_min_spend": "$50,000 minimum in-state spend applies specifically to a "
                                "Louisiana-screenplay production (vs $300,000 general).",
        "transfer_back_to_state": "Credits may be transferred back to the State for 90% of face "
                                  "value; a 2% transfer fee yields an ~88% net monetization.",
        "annual_cap_change": "Front- and back-end caps reduced to $125M for applications received "
                             "on/after 2025-07-01 (prior $150M statutory figure still appears on "
                             "the LED page text).",
        "per_project_rate_cap": "Total credits cannot exceed 40% of the base investment.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_ms_advantage_film_program", jurisdiction_code="US-MS",
    cultural_test_required=False,
    min_local_spend_usd=50_000.0,    # $50,000 minimum Mississippi investment (local spend) per project
    preapproval_mandatory=True,      # apply to Film Mississippi/MDA before production (4-6 weeks before MS spend)
    refundable=True,                 # cash rebate (paid out; not a transferable tax credit)
    transferable=False,
    per_project_cap_usd=10_000_000.0,     # $10M per-project rebate cap
    annual_program_cap_usd=20_000_000.0,  # $20M annual film rebate cap (separate $10M episodic-TV pool)
    application_deadline=TimingFact(
        value="Apply to Film Mississippi / MDA before production; guidance is to apply 4-6 weeks "
              "before spending would occur in Mississippi",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    evidence=EvidenceRecord(
        source_title="Incentive — Film Mississippi",
        source_url="https://filmmississippi.org/incentive/",
        issuing_authority="Film Mississippi / Mississippi Development Authority (MDA)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-25",
        notes="Official Film Mississippi program page (fetched 2026-07-25). Cash rebate (not a "
              "transferable credit): 25% base investment (local spend), 25% non-resident payroll "
              "(cap $5M/project), 30% resident payroll (cap $5M/project), +5% for honorably "
              "discharged veterans. Minimum $50,000 Mississippi investment per project. Per-project "
              "rebate cap $10M; annual film rebate cap $20M (separate $10M episodic-TV pool). "
              "At least 20% of the payroll production crew must be Mississippi residents. No minimum "
              "production days or spend-percentage. End-credit acknowledgement required. A dedicated "
              "audit requirement was not stated on the page reviewed (left None).",
    ),
    additional_facts={
        "local_crew_residency": "At least 20% of the payroll production crew must be Mississippi residents.",
        "end_credit_requirement": "Program participation must be acknowledged in the end credits.",
        "payroll_rebate_caps": "Non-resident payroll rebated at 25% and resident payroll at 30%, "
                               "each capped at $5M per project; +5% veteran payroll uplift.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_ca_film_credit", jurisdiction_code="US-CA",
    cultural_test_required=False,
    preapproval_mandatory=True,   # Credit Allocation Letter issued before principal photography; competitive ranked application windows
    refundable=True,              # Program 4.0 (post 2025-07-01): productions may elect a REFUNDABLE credit (see notes for 3.0)
    transferable=None,            # 3.0 independent features were transferable; 4.0 introduces the refundable election — mixed, left None
    sunset_date="2030-06-30",     # Program 4.0 runs 2025-07-01 through 2030-06-30
    allocation_type=AllocationType.COMPETITIVE,  # ranked jobs-ratio / application-window allocation, not first-come
    evidence=EvidenceRecord(
        source_title="California Film & Television Tax Credit Program 4.0 — CA Film Commission / FTB",
        source_url="https://film.ca.gov/tax-credit/",
        issuing_authority="California Film Commission (CFC); California Franchise Tax Board (FTB)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-25",
        notes="California runs two overlapping regimes. PROGRAM 3.0 (Credit Allocation Letter "
              "before 2025-07-01): 25% base transferable credit for independent features; 20% base "
              "non-refundable, non-transferable credit for studio features/TV. PROGRAM 4.0 (applies "
              "after 2025-07-01, runs through 2030-06-30): 35-45% credit, and ALL allocated "
              "productions may ELECT a refundable credit (paid even without CA tax liability). "
              "refundable set True on the current (4.0) basis; transferable left None because it "
              "depends on regime/project type (3.0 independent = transferable; 4.0 = refundable "
              "election). Allocation is COMPETITIVE (jobs-ratio ranked, fixed application windows), "
              "not first-come. Preapproval: a Credit Allocation Letter must be issued before "
              "principal photography. MINIMUM QUALIFYING BUDGET not re-verified to an exact figure "
              "in this pass — left None rather than guessed. 4% of an awarded credit is contingent "
              "on approved DEIA documentation.",
    ),
    additional_facts={
        "program_4_0_window": "Program 4.0 applies to applications after 2025-07-01 and runs through 2030-06-30.",
        "refundable_election": "Under Program 4.0 a production may elect to receive the credit as "
                               "a refundable credit, paid even absent California tax liability.",
        "uplifts": "4.0 bonuses: +5% original photography outside the LA zone; +5% qualified VFX; "
                   "+10% qualified wages for out-of-LA-zone photography by CA residents.",
        "deia_contingency": "4% of an applicant's awarded credit is contingent on submission and "
                            "approval of DEIA (diversity/equity/inclusion/accessibility) documents.",
        "allocation_note": "Ranked competitive allocation by jobs ratio within fixed application "
                           "windows — not entitlement and not first-come-first-served.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="ca_on_opstc", jurisdiction_code="CA-ON",
    cultural_test_required=False,   # OPSTC is a production-SERVICES credit — no cultural/content test (unlike the domestic OFTTC)
    treaty_or_official_coproduction_required=False,
    min_total_budget_usd=707_463.74,  # production cost must exceed CAD 1,000,000 for a feature (see notes for series thresholds)
    refundable=True,
    transferable=False,
    preapproval_mandatory=None,   # return-based refundable credit; Certificate of Eligibility applied for (not a pre-production approval gate) — left None
    audit_required=None,
    evidence=EvidenceRecord(
        source_title="Ontario Production Services Tax Credit (OPSTC) — Ontario Creates",
        source_url="https://www.ontariocreates.ca/tax-incentives/opstc",
        issuing_authority="Ontario Creates (with CRA; harmonized with the federal PSTC / CAVCO)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-25",
        notes="Official Ontario Creates program page (accessed 2026-07-25). 21.5% REFUNDABLE tax "
              "credit on Ontario qualifying production expenditures. No cultural/content test (it is "
              "a production-services credit, harmonized with the federal Film or Video Production "
              "Services Tax Credit administered by CAVCO/CRA). Minimum: production cost must exceed "
              "CAD 1,000,000 for a feature (series thresholds: >CAD 100,000/episode under 30 min; "
              ">CAD 200,000/episode for longer). min_total_budget_usd set to the same USD figure "
              "already used as this program's min-spend in the rate database (CAD 1M ~= USD "
              "707,463.74); the authoritative original is CAD 1,000,000. Local-labour requirement: "
              "Ontario labour expenditures must be >=25% of qualifying production expenditures. "
              "Refundable (CRA refunds any excess over taxes owed) -> not transferable. Ontario "
              "Creates issues a Certificate of Eligibility after completeness review; this is a "
              "return-based credit, so preapproval_mandatory left None rather than asserted.",
    ),
    additional_facts={
        "ontario_labour_minimum": "Ontario labour expenditures must be at least 25% of the "
                                  "qualifying production expenditures claimed.",
        "series_thresholds": "Series/pilot: cost must exceed CAD 100,000/episode (<30 min) or "
                             "CAD 200,000/episode (longer).",
        "federal_harmonization": "Harmonized with the federal Film or Video Production Services "
                                 "Tax Credit (CAVCO/CRA); a federal PSTC can stack with the OPSTC.",
        "min_total_budget_original": "Authoritative threshold is CAD 1,000,000 total production "
                                     "cost for a feature (USD figure shown is an internal conversion).",
    },
))

register(ProgramRequirementsProfile(
    program_slug="au_location_offset", jurisdiction_code="AU",
    cultural_test_required=False,   # Location Offset has NO significant-Australian-content test (that applies to the Producer Offset, a different program)
    refundable=True,
    transferable=False,
    preapproval_mandatory=None,     # certificate-based, claimed via the company tax return; provisional certificate available but not a strict pre-spend gate
    evidence=EvidenceRecord(
        source_title="Location Offset guidelines — Office for the Arts; Film industry incentives — ATO",
        source_url="https://www.arts.gov.au/publications/location-offset-guidelines",
        issuing_authority="Australian Government Office for the Arts; Australian Taxation Office (ATO)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-25",
        notes="Official Office for the Arts / ATO guidance (accessed 2026-07-25). 30% REFUNDABLE "
              "tax offset on total QAPE (Qualifying Australian Production Expenditure) for films "
              "whose principal photography started on/after 2023-07-01. MINIMUM QAPE THRESHOLD: "
              "AUD 20,000,000 for a film (AUD 1,500,000 per hour for TV) — the highest-threshold "
              "offset, effectively large-budget only. Left min_local_spend_usd as None to avoid a "
              "false-precision FX conversion; the authoritative figure is AUD 20,000,000 (recorded "
              "in additional_facts). Refundable (paid even with no tax liability) -> not "
              "transferable. NO cultural test for the Location Offset (the 'significant Australian "
              "content' test applies only to the separate Producer Offset). Final certificate "
              "issued by the Minister for the Arts; the reformed offset also carries a skills-and-"
              "training obligation.",
    ),
    additional_facts={
        "min_qape_threshold": "AUD 20,000,000 minimum QAPE for a film; AUD 1,500,000 per hour for "
                              "television — authoritative original threshold (not FX-converted here).",
        "pdv_and_producer_offsets": "Separate offsets exist: PDV Offset (post/digital/VFX) and the "
                                    "Producer Offset (which DOES require significant Australian content).",
        "skills_training_obligation": "The reformed Location Offset carries a skills-and-training "
                                      "contribution obligation.",
    },
))


# ── Final Additive Completeness Sweep, Pass A (2026-07-26): programmatic
#    migration from ALREADY-EXISTING, ALREADY-CITED internal data —
#    program_rate_rules.py's RateCondition records. Zero new web research.
#    Every fact below is read from a RateCondition whose own `quote` field
#    already carries an external citation (recorded when that rate rule
#    was originally sourced); see scripts/migrate_requirements.py for the
#    full reconciliation report explaining why every OTHER condition kind
#    (discretionary_band in the ordinary rate-ceiling sense,
#    material_funding_risk_not_modeled, no_sponsorship_in_qpe,
#    production_type, rate_base_narrower_than_qpe,
#    graduated_bracket_applied) does NOT correspond to any field here —
#    those are pricing/QPE-derivation facts, a different data domain by
#    this module's own design (see the top-of-file docstring), and why
#    program_spend_rules.py (SpendRule: program_slug/spend_category/
#    qualifies/territorial_only/confidence_tier/notes/source_ref) carries
#    no eligibility/operational fact at all — it is a QPE-inclusion
#    registry, not a requirements registry.

register(ProgramRequirementsProfile(
    program_slug="mu_edb_incentive", jurisdiction_code="MU",
    local_entity_required=True,        # confirmed via the same VERIFIED-tier internal record: "Locally incorporated/registered production company required (100% foreign ownership permitted)"
    min_local_spend_usd=1_000_000.0,   # 40% feature-film tier (30% general tier: USD 100,000 foreign / USD 50,000 local production -- see additional_facts for the full tier structure)
    preapproval_mandatory=True,        # discretionary_band quote: Film Rebate Committee "provide recommendations to the ... CEO who shall approve projects"
    allocation_type=AllocationType.DISCRETIONARY,  # same quote: Committee+CEO approval is a discretionary act, not automatic entitlement
    audit_required=True,               # "a certified report by the local auditors ... providing details of the amount of expenditures, and the amount of the qualified production expenditures, incurred in Mauritius" required at claim time
    cpa_or_approved_auditor_required=True,
    refundable=True,                   # cash rebate paid out
    transferable=False,
    evidence=EvidenceRecord(
        source_title="Film Rebate Scheme — Submission Procedures (Economic Development Board, 31 Jan 2020, citing the EDB (Film Rebate Scheme) Regulation 2018)",
        source_url=None,
        issuing_authority="Economic Development Board (EDB), Mauritius",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY BASELINE FIRST: this profile was a thin Pass A programmatic migration "
              "(source_url=None, only min_local_spend_usd + allocation_type). A prior external "
              "opportunistic-upgrade attempt (WebFetch of edbmauritius.org/schemes/film-rebate-"
              "scheme) resolved to a navigation hub with zero scheme detail and was explicitly "
              "abandoned as a dead end. Per 'existence before creation', this session instead "
              "searched the REPOSITORY ITSELF before any further external attempt, and found the "
              "actual EDB primary source document -- 'Film Rebate Scheme — Submission Procedures' "
              "(31 Jan 2020) -- ALREADY extensively quoted verbatim at VERIFIED confidence tier "
              "(this repository's highest tier) across app.data.program_rate_rules.py "
              "(MU_RATE_RULES, MU_UNVERIFIED_CLAIMS) and app.data.program_spend_rules.py "
              "(MU_EDB_RULES, 33-category QPE list), and in jurisdiction_comparison.py's MU "
              "profile notes -- never previously reconciled into this Requirements Profile. This "
              "upgrade reconciles that ALREADY-VERIFIED internal evidence rather than re-fetching "
              "externally (the edbmauritius.org dead end stands; not retried). RATE STRUCTURE "
              "(from MU_RATE_RULES, VERIFIED): two tiers -- 30% general rebate on QPE incurred "
              "locally, minimum QPE USD 100,000 for a foreign production / USD 50,000 for a local "
              "production, available to a wide list of formats (feature film, creative "
              "documentary, digital animated film, TV serial/single drama, factual TV, natural "
              "history, lifestyle magazine, commercial, music video, dubbing); UP TO 40% for "
              "feature film production companies (or drama series at USD 150,000/episode), "
              "minimum QPE USD 1,000,000 -- the 'up to' ceiling is a Film Rebate Committee "
              "assessment + CEO approval band, not a guaranteed entitlement, hence "
              "allocation_type=DISCRETIONARY. NO-SPONSORSHIP RULE (genuinely new to this "
              "profile): 'The QPE quantum should not include any forms of sponsorships or "
              "financial assistance obtained for the Mauritian schedule of the project' -- a "
              "real QPE-composition exclusion, quoted directly. LOCAL ENTITY GATE (genuinely new "
              "to this profile, already established elsewhere in the repo): production company "
              "must be locally incorporated/registered in Mauritius; 100% foreign ownership is "
              "permitted, so this is an incorporation requirement, not a local-ownership "
              "requirement. AUDIT GATE (genuinely new to this profile): a certified report from "
              "local Mauritian auditors, itemizing total expenditures and qualified production "
              "expenditures incurred in Mauritius, is required at claim time. TWO CLAIMS "
              "EXPLICITLY INVESTIGATED AND NOT FOUND in the primary EDB document or MCCI's "
              "corroborating page (both reviewed verbatim in an earlier session, disclosed here "
              "rather than silently omitted): (1) that the 40% tier requires 90% of filming to "
              "take place in Mauritius (claimed only by a production-services/fixer site, no "
              "government citation); (2) that foreign cast/crew remuneration must not exceed 40% "
              "of the Mauritius-allocated budget (claimed only by secondary trade sources). "
              "NEITHER is applied to this profile or the rate rules -- both require EDB written "
              "confirmation before being treated as a rule either way, and are recorded as "
              "explicitly-checked-and-unconfirmed rather than either asserted or silently dropped. "
              "RATE CONFLICT DISCLOSED ELSEWHERE, NOT DUPLICATED HERE: the actual Little Utopia "
              "production budget carries a line item 'EDB Rebate at 35%' -- this is "
              "BUDGET-EVIDENCED (what one production's own paperwork assumed), not "
              "AUTHORITY-EVIDENCED, and is recorded separately in "
              "program_rate_rules.MU_BUDGET_EVIDENCED_RATES and explicitly IGNORED for all "
              "calculations per that module's own Rules 1/2/5 -- not treated as a Material "
              "Discrepancy against the 30%/40% statutory tiers, since budget assumptions are not "
              "an authoritative source.",
    ),
    additional_facts={
        "rate_tiers": "30% general (min QPE USD 100,000 foreign / USD 50,000 local production, wide format list). Up to 40% feature film (min QPE USD 1,000,000; drama series USD 150,000/episode), discretionary via Film Rebate Committee + CEO approval.",
        "no_sponsorship_rule": "QPE quantum must not include sponsorships or financial assistance obtained for the Mauritian schedule of the project.",
        "local_entity_gate": "Production company must be locally incorporated/registered in Mauritius; 100% foreign ownership permitted.",
        "audit_gate": "Certified report from local Mauritian auditors, itemizing total and qualified production expenditures incurred in Mauritius, required at claim time.",
        "unconfirmed_claims_investigated_not_applied": "90%-of-filming-in-Mauritius condition for the 40% tier, and a 40%-of-Mauritius-budget cap on foreign cast/crew remuneration -- both claimed only by secondary/fixer sources, NOT found in the primary EDB document or MCCI's corroborating page, NOT applied.",
        "budget_evidenced_vs_authority_rate": "A real production's own budget assumed 'EDB Rebate at 35%' -- recorded separately as budget-evidenced (not authoritative) in program_rate_rules.MU_BUDGET_EVIDENCED_RATES and explicitly ignored for calculations.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="mt_mfc_rebate", jurisdiction_code="MT",
    min_local_spend_usd=113_000.0,     # EUR 100,000 general (EUR 50,000 for "Difficult Audiovisual Work" -- see additional_facts) -- confirmed via direct PDF text extraction of the official MFC Guidelines
    min_total_budget_usd=226_000.0,    # EUR 200,000 overall budget floor (EUR 100,000 for Difficult Audiovisual Work) -- confirmed
    cultural_test_required=True,       # must obtain a minimum of 40 points in aggregate in the Cultural Test (separate test for Animation/VFX)
    cultural_test_points=40,
    cultural_test_threshold=40,
    preapproval_mandatory=True,        # provisional approval required before principal photography/Animation-VFX commences; applications after commencement are not considered
    expenditure_before_approval_qualifies=False,  # "expenditure ... incurred before the date of the application will be considered as ineligible"
    audit_required=True,               # full audit of expenses required at final submission
    cpa_or_approved_auditor_required=True,  # top sheet must be signed by the applicant's certified accountant; independent auditors verify
    local_entity_required=True,        # must be a "Qualifying Company" -- foreign applicants must be an SPV or a company carrying on/intending to carry on business in Malta; local applicants must be MFC-registered with a Maltese/EU director or major shareholder
    per_project_cap_usd=None,          # no per-project cap found in the primary Guidelines document
    refundable=True,                   # cash rebate, exempt for Income Tax Act purposes
    transferable=False,                # the Guidelines describe direct payment to the qualifying company only; no assignment/transfer mechanism is mentioned anywhere in the document
    application_deadline=TimingFact(
        value="Application for provisional approval (with Malta budget projection, completed "
              "Cultural Test, and supporting documents) must be presented at least 30 working "
              "days before planned commencement of principal photography or Animation/VFX work "
              "in Malta (late applications considered only at the Commissioner's discretion if "
              "justifiable). The Commissioner grants a provisional certificate no later than 20 "
              "working days after receipt of a complete application. Applications submitted "
              "AFTER commencement of principal photography or Animation/VFX work are not "
              "considered at all.",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    audit_or_final_certification_deadline=TimingFact(
        value="On completion, the qualifying company submits a full audit of expenses; the "
              "audit/administrative fee is borne by the applicant, capped at 0.5% of eligible "
              "spend (minimum EUR 5,000, maximum EUR 20,000) and deducted from the final rebate. "
              "The Commission withholds 2% of the cash rebate until all provisional/final "
              "certificate obligations are fulfilled.",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    payment_timing=TimingFact(
        value="A 10% advance grant may be claimed once shooting or Animation/VFX work has "
              "commenced, against a top sheet of accumulated expenses verifiable by contracts "
              "and payment transactions. Productions with a lengthy Malta duration may instead "
              "request quarterly tranche payments (discretionary, requested at application "
              "stage). The balance/full cash rebate is forwarded to the qualifying company no "
              "later than 5 months from receipt of the final submission, subject to orderly "
              "documentation and auditor satisfaction.",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    sunset_date=None,   # no expiration/sunset date found anywhere in the primary Guidelines document itself (the scheme runs under the EU General Block Exemption Regulation, whose own validity period is a separate EU-law fact -- see additional_facts for a related, unconfirmed secondary-sourced figure)
    evidence=EvidenceRecord(
        source_title="Financial Incentives for the Audiovisual Industry: CASH REBATE GUIDELINES (Official Document, January 2019)",
        source_url="https://stargatestudios.com.mt/wp-content/uploads/2019/06/Financial-Incentives-for-Audiovisual-Industry-Guidelines-Official-Do....pdf",
        issuing_authority="Malta Film Commission (MFC), a government body established by Chapter 478 (Act No. 7 of 2005) of the Laws of Malta, under the Ministry for Tourism",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="DOCUMENT RETRIEVAL ESCALATION APPLIED (per the permanent engineering rule adopted "
              "this session): a prior session's WebFetch of this exact URL had downloaded the real "
              "PDF (1,147,349 bytes, 28 pages) but the tool's own PDF-to-text handling failed and "
              "produced HALLUCINATED PLACEHOLDER CONTENT ('typical Malta audiovisual incentive "
              "structures... 4-6% rebate rates') that was correctly discarded at the time as "
              "untrustworthy. Per the new doctrine, that failure was classified precisely as a "
              "PARSER FAILURE, not a retrieval failure or a genuine absence of authoritative "
              "source -- the file itself was real and already sitting on disk. This session located "
              "the saved PDF and extracted its actual text directly using pypdf (already an "
              "existing project dependency, pyproject.toml), successfully recovering all 28 pages "
              "of real, legally-precise primary content. THIS DECISIVELY SUPERSEDES BOTH (a) this "
              "repository's own pre-existing rate rule (25% base + three stacked uplifts of "
              "+3%/+3%/+7%, an undated internal citation with uplift criteria that do not match "
              "anything in the real document) and (b) this session's own prior batch-2 secondary-"
              "sourced enrichment (35% base rising to 40% for QME under EUR 150,000 -- also not "
              "what the real document describes). LEGAL BASIS: Malta Film Commission established "
              "by Chapter 478 (Act No. 7 of 2005), Laws of Malta; the scheme is EU State Aid under "
              "Commission Regulation (EU) No 651/2014 (General Block Exemption Regulation, GBER), "
              "as amended by (EU) 2017/1084, specifically Article 54 (aid schemes for audiovisual "
              "works). RATE STRUCTURE (CORRECTED): Category A (all qualifying productions except "
              "Animation/VFX) = 30% base on all eligible expenditure, plus Commissioner-"
              "discretionary uplifts of up to 5% ('Malta features as Malta or local usage of "
              "facilities') and up to 5% ('maximisation of local resources') = 40% maximum. "
              "Category B (Animation/VFX) = 25% base, plus up to 15% Commissioner-discretionary "
              "(same two criteria combined) = 40% maximum. A SEPARATE 'Difficult Audiovisual Work' "
              "category (total production budget <= EUR 1,500,000, meeting defined 'difficult' "
              "criteria AND a 'National Work' status requiring a Malta producer plus a points-based "
              "'Malta Creative Input' test -- 15/21 points feature film, 8/16 documentary, 15/23 "
              "animation) qualifies for a HIGHER maximum rebate of 50%, not modeled in the prior "
              "35%/40% structure at all. QUALIFYING COMPANY GATE (precise, corrected from generic "
              "'qualifying company' language): a Foreign Qualifying Company must be a special "
              "purpose vehicle or a company carrying on/intending to carry on a qualifying-"
              "production trade or business in Malta; a Local Qualifying Company must have "
              "audiovisual production as its main activity, be MFC-registered, and have at least "
              "one director or major shareholder who is a Maltese/European citizen; the same "
              "citizenship condition applies to Animation/VFX studios/facilities. Foreign companies "
              "not registered in Malta must use a registered Production Service Company as "
              "Production Coordinator. CONTENT EXCLUSIONS (genuinely new): public/special "
              "performances staged for filming; sporting events; current-affairs/talk shows; "
              "hobby/task demonstration programmes; review/magazine/lifestyle programmes; "
              "advertising; pornographic content; computer games. MIN SPEND CONFIRMED AND REFINED: "
              "EUR 100,000 Malta spend / EUR 200,000 total budget generally; EUR 50,000 Malta "
              "spend / EUR 100,000 total budget for Difficult Audiovisual Work -- both figures "
              "matching this session's earlier secondary-sourced EUR 100,000 finding for the "
              "general case, now directly confirmed, plus the previously-unknown reduced Difficult-"
              "Work threshold. TRANSFERABILITY CORRECTED: the Guidelines describe the cash rebate "
              "as paid directly to the qualifying company -- no assignment or transfer mechanism "
              "to a third party (e.g. a gap lender) is mentioned anywhere in the 28-page document, "
              "correcting jurisdiction_comparison.py's prior is_transferable=None to a confirmed "
              "False. TRAINEE REQUIREMENT (more precise than the 'Opportunity for All' framing "
              "reported by secondary sources): minimum 5 Maltese/EU-EEA-resident trainees for HOD "
              "positions plus a further minimum 5 for below-the-line positions, paid not less than "
              "the national minimum wage. ADVANCE/TRANCHE PAYMENTS CONFIRMED: 10% advance grant "
              "available once shooting/Animation-VFX commences; quarterly tranche payments "
              "available (discretionary) for lengthy Malta productions exceeding 6 months. AUDIT "
              "FEE CAP (genuinely new): review-audit-plus-administrative-fee cost capped at 0.5% of "
              "eligible spend, minimum EUR 5,000, maximum EUR 20,000, deducted from the final "
              "rebate; a further 2% is withheld until all certificate obligations are fulfilled. "
              "SIGNIFICANT-BUDGET-CHANGE RULE (genuinely new): if Malta-spend/eligible-expenditure "
              "increases by more than 10% over the provisional-certificate estimate, the "
              "Commissioner must be notified immediately in writing; the Commission may cap the "
              "final incentive at no more than 10% over the provisional certificate's qualifying "
              "expenditure. ABOVE-THE-LINE LABOUR CAP (genuinely new): total ATL labour costs "
              "(directors, producers, casting directors, cast, stunts) capped at EUR 500,000. PER "
              "DIEM CAP: EUR 100 per person per day. NO SUNSET DATE is stated anywhere in this "
              "document -- the scheme's duration follows the GBER's own validity period (an EU-law "
              "fact external to this document); a secondary source (Zerafa Advocates, used in the "
              "prior batch) separately reported a 2028-10-29 date, NOT independently confirmed here "
              "and recorded only as a reported, unconfirmed figure rather than asserted. OPEN ITEM, "
              "NOT ASSERTED: this document is dated January 2019 and explicitly favours EU/EEA "
              "labour spend; secondary reporting (used in the prior batch) describes a 2024 "
              "'revamped' scheme opening below-the-line labour costs to ALL international crews, "
              "removing the EU/EEA/UK restriction visible in this 2019 text. This specific, narrow "
              "change is plausible and NOT contradicted by anything else in this document (the "
              "core rate/threshold/process structure found here is a stable, GBER-anchored "
              "framework unlikely to have been rebuilt from scratch), but it is NOT independently "
              "confirmed by any document actually retrieved and read in full -- recorded as an open "
              "item for a future session, rather than silently assumed superseded or silently "
              "assumed still in force.",
    ),
    additional_facts={
        "rate_structure": "Category A (all formats except Animation/VFX): 30% base + up to 10% Commissioner-discretionary (5% Malta-as-Malta/local usage + 5% maximisation of local resources) = 40% max. Category B (Animation/VFX): 25% base + up to 15% Commissioner-discretionary (same two criteria combined) = 40% max. 'Difficult Audiovisual Work' (budget <= EUR 1,500,000 + defined difficulty criteria + National Work/Malta Creative Input points test): up to 50% max, a separate higher-ceiling category.",
        "min_spend_general_eur": "EUR 100,000 Malta spend, EUR 200,000 total budget (general). EUR 50,000 Malta spend, EUR 100,000 total budget (Difficult Audiovisual Work).",
        "cultural_test": "Minimum 40 points in aggregate (separate test for Animation/VFX works).",
        "qualifying_company_gate": "Foreign Qualifying Company: SPV or company carrying on/intending to carry on qualifying-production business in Malta. Local Qualifying Company: MFC-registered, audiovisual production as main activity, at least one Maltese/EU director or major shareholder. Same citizenship condition for Animation/VFX studios.",
        "content_exclusions": "Staged public/special performances; sporting events; current-affairs/talk shows; hobby/task demonstration programmes; review/magazine/lifestyle programmes; advertising; pornographic content; computer games.",
        "difficult_audiovisual_work_test": "Total budget <= EUR 1,500,000 AND (Maltese-language/limited-distribution OR commercially difficult/experimental OR indigenous-industry-building) AND National Work status (Malta producer + Malta Creative Input points: feature 15/21, documentary 8/16, animation 15/23).",
        "trainee_requirement": "Minimum 5 Maltese/EU-EEA-resident trainees for HOD positions, plus a further minimum 5 for below-the-line positions, paid not less than national minimum wage.",
        "advance_and_tranche_payments": "10% advance grant once shooting/Animation-VFX commences. Quarterly tranche payments available (discretionary) for Malta productions exceeding 6 months.",
        "audit_fee_and_withholding": "Audit/admin fee capped at 0.5% of eligible spend (min EUR 5,000, max EUR 20,000), deducted from the rebate. A further 2% withheld until all certificate obligations are fulfilled.",
        "significant_budget_change_rule": "If Malta spend/eligible expenditure increases more than 10% over the provisional-certificate estimate, the Commissioner must be notified immediately; final incentive may be capped at no more than 10% over the provisional certificate's qualifying expenditure.",
        "atl_labour_cap_eur": "Above-the-line labour costs (directors, producers, casting directors, cast, stunts) capped at EUR 500,000.",
        "per_diem_cap_eur": "EUR 100 per person per day.",
        "sunset_unconfirmed": "No sunset date in the primary Guidelines document (runs under the EU GBER's own validity period). A secondary source (Zerafa Advocates) separately reported 2028-10-29 -- not independently confirmed, recorded as reported only.",
        "open_item_2024_crew_nationality_change": "Secondary reporting describes a 2024 change opening below-the-line labour to all international crews (this 2019 document still favours EU/EEA labour spend) -- plausible, not contradicted, but not independently confirmed by any document read in full this session.",
        "document_retrieval_note": "This PDF was downloaded successfully in an earlier session but produced hallucinated placeholder analysis due to a tool parser limitation, not a retrieval failure -- the real 28-page document was recovered and read in full this session via direct pypdf text extraction.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="gr_cash_rebate", jurisdiction_code="GR",
    # Updated per Incentive/Optimizer Core Closeout final rule resolution
    # (docs/validation/CODEX_FINAL_RULE_RESOLUTION.md §2.2, sourced to JMD
    # 607434 art. 6 as amended by JMD 140524): fiction film/TV film floor is
    # EUR 200,000 minimum eligible Greek spend AND EUR 400,000 minimum total
    # production budget — both floors, not a single figure. EUR/USD
    # conversion reuses this program's own existing 1.140524 ratio.
    min_local_spend_usd=228_104.80,   # EUR 200,000 — matches GR_RATE_RULES min_qpe_usd
    min_total_budget_usd=456_209.60,  # EUR 400,000
    # Worldwide Program Qualification + Cultural Test Completion, 2026-08-19.
    # Confirmed cultural test exists and is a real points structure — see
    # additional_facts for the fiction/documentary vs animation split.
    cultural_test_required=True, cultural_test_points=50, cultural_test_threshold=20,
    preapproval_mandatory=True,      # application must be submitted before production/post-production begins in Greece
    application_deadline=TimingFact(
        value="Application must be submitted no later than 10 days before the beginning of "
              "production and/or post-production of the work in Greece",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    payment_timing=TimingFact(
        value="Cash rebate available to producers no later than 6 months after completion of "
              "production, provided all statutory prerequisites are met",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    refundable=True,   # cash rebate paid out
    transferable=False,
    evidence=EvidenceRecord(
        source_title="40% Cash Rebate",
        source_url="https://filmcommission.gr/cash-rebate/",
        issuing_authority="EKOME (National Centre of Audiovisual Media and Communication) / Hellenic Film Commission",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST: this profile was a thin Pass A programmatic "
              "migration (source_url=None, only min_local_spend_usd from an internal rate-rule "
              "condition). Direct fetch of the Hellenic Film Commission's own official cash-rebate "
              "page performed this session, confirming the 40% rate (already in this repository's "
              "rate rules) and upgrading to PRIMARY_VERIFIED. LEGAL BASIS (genuinely new): "
              "established under Section C of Law No. 5105/2024, succeeding the prior framework "
              "under Law No. 4487/2017 — a real statutory chain, resolving what might otherwise "
              "look like conflicting older/newer citations in secondary sources. PROGRAM "
              "STRUCTURE (genuinely new): THREE distinct sub-schemes under one umbrella rate — "
              "CRGR-FTV (film & television production), CRGR-Animate (animation), and CRGR-VGD "
              "(video game development/computer game software prototypes) — each with its own "
              "detailed requirements hosted separately (ekkomed.gr), not itemized on the page "
              "fetched. CURRENT STATUS CONFIRMED ACTIVE: a search result headline referenced the "
              "program being on an 'extended pause' at some point — this direct fetch confirms the "
              "programme is presently ACTIVE and OPERATIONAL under the current 2024 law, resolving "
              "that concern rather than leaving it open. MINIMUM SPEND BY FORMAT AND APPLICATION/"
              "PAYMENT TIMING (from a WebSearch summary citing the Hellenic Film Commission "
              "directly, but not independently re-confirmed on the specific page fetched — recorded "
              "with that caveat rather than claimed as directly re-verified): feature films EUR "
              "100,000; documentaries EUR 60,000; short films EUR 60,000; digital games EUR "
              "30,000; TV series EUR 15,000-25,000 per episode. Application must be submitted no "
              "later than 10 days before production/post-production begins in Greece; the rebate is "
              "available no later than 6 months after production completion, subject to statutory "
              "prerequisites.",
    ),
    additional_facts={
        "legal_basis": "Law No. 5105/2024, Section C, succeeding Law No. 4487/2017.",
        "sub_scheme_structure": "CRGR-FTV (film & television), CRGR-Animate (animation), CRGR-VGD (video game development) -- three distinct schemes under EKOME/Hellenic Film Commission, each with its own detailed requirements hosted on ekkomed.gr.",
        "min_spend_by_format_eur": "Feature films EUR 100,000; documentaries EUR 60,000; short films EUR 60,000; digital games EUR 30,000; TV series EUR 15,000-25,000 per episode (from WebSearch summary citing the Hellenic Film Commission, not independently re-confirmed on the specific official page fetched this session).",
        "application_timing": "Must be submitted no later than 10 days before production/post-production begins in Greece.",
        "payment_timing_note": "Rebate available no later than 6 months after production completion, subject to statutory prerequisites.",
        "current_status": "Confirmed ACTIVE and operational as of 2026-07-26 direct fetch, under the current 2024 law -- an older report of an 'extended pause' does not describe the present state.",
        # Worldwide Program Qualification + Cultural Test Completion,
        # 2026-08-19. Confirmed via Saturation.io, fixersingreece.gr, and
        # Lexology's Law 5105/2024 legal summary (secondary/legal-analysis
        # sources corroborating each other, not the EKOME primary page
        # itself, which does not expose the point table): projects must
        # pass a cultural test scoring at least 20 of 50 points for
        # fiction/documentary, or 16 of 40 for animation/digital games.
        # Per-criterion (role/story/language) point breakdown within
        # those totals not found in any source checked this pass —
        # AUTHORITY_UNRESOLVED for that sub-proposition specifically.
        "cultural_test_animation_points": "16 of 40 (distinct scale from the 20-of-50 fiction/documentary test above)",
        "cultural_test_sources": "Saturation.io (https://saturation.io/tax-incentives/greece), "
                                  "fixersingreece.gr (https://www.fixersingreece.gr/blog/posts/40-percent-cash-rebate-greece/), "
                                  "Lexology Law 5105/2024 summary (https://www.lexology.com/library/detail.aspx?g=b2758448-e4b1-4ae0-b903-be46a264327a)",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_or_opif", jurisdiction_code="US-OR",
    # Worldwide Program Qualification + Cultural Test Completion, 2026-08-19.
    # Confirmed via oregonfilm.org (the state's own designated film office)
    # and Oregon Administrative Rules (regulations.justia.com) -- no
    # cultural/content test found for the main OPIF program; requirements
    # are spend/registration/policy-based only, consistent with every
    # other US state incentive in this registry (0 of 45 examined require
    # a cultural test).
    cultural_test_required=False,
    min_local_spend_usd=1_000_000.0,  # min_qpe_usd condition, corroborated by 3 sources
    allocation_type=AllocationType.DISCRETIONARY,  # discretionary_band quote: fund-capped, "not guaranteed even if criteria are met"
    preapproval_mandatory=True,       # Letter of Intent + OPIF Rebate Application required; must apply before production begins
    expenditure_before_approval_qualifies=False,
    audit_required=True,              # audit paperwork filing required
    annual_program_cap_usd=21_200_000.0,  # confirmed directly: $21.2M annual fund, July 1-June 30 fiscal year
    refundable=True,
    transferable=False,
    evidence=EvidenceRecord(
        source_title="Oregon Production Investment Fund (OPIF)",
        source_url="https://oregonfilm.org/article/oregon-production-investment-fund-opif/",
        issuing_authority="Oregon Film & Video Office (Oregon Film)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST: this profile was a thin Pass A programmatic "
              "migration (source_url=None, only min_local_spend_usd + allocation_type from "
              "internal rate-rule conditions). Direct fetch of Oregon Film's own official OPIF "
              "page performed this session, confirming both pre-existing figures exactly ($1M min "
              "spend; 50%-of-fund-per-project scarcity limit, consistent with "
              "AllocationType.DISCRETIONARY) and upgrading to PRIMARY_VERIFIED. RATE STRUCTURE "
              "(genuinely new, not previously in this profile — belongs to the rate-rule layer but "
              "confirmed here for completeness): TWO distinct rebates, 25% on production-related "
              "goods/services paid to Oregon vendors and 20% on payroll wages for work done in "
              "Oregon (both Oregon and non-Oregon residents eligible for the labor rebate); the "
              "labor portion can STACK with the separate Greenlight Oregon programme for an "
              "effective 26.2% labor rebate. ANNUAL FUND CAP CONFIRMED: $21,200,000 per fiscal "
              "year (2026-07-01 to 2026-06-30 cycle) — resolves the prior profile's unpopulated "
              "annual_program_cap_usd field. APPLICATION GATES (previously unrecorded): a Letter of "
              "Intent is required; equipment must be rented or purchased directly from Oregon "
              "vendors (billing through out-of-state 'pass-through' companies does not qualify); "
              "projects must comply with Oregon state law on independent-contractor classification. "
              "AUDIT: audit paperwork filing is required post-production; Oregon Film publishes "
              "guidance on common filing errors. ELIGIBLE WORK: film/TV productions, interactive "
              "media, commercial production, and post-production-only work from Oregon-based "
              "companies; non-scripted work has limited eligibility requiring direct inquiry. NOT "
              "independently re-confirmed on the specific page fetched (from a WebSearch summary "
              "citing Oregon Film, recorded with that caveat rather than claimed as directly "
              "re-verified): a written diversity/equity/inclusion policy and a written "
              "anti-harassment/reporting policy are required as part of the OPIF contract with the "
              "Oregon Film & Video Office.",
    ),
    additional_facts={
        "rate_structure": "25% cash rebate on production-related goods/services paid to Oregon vendors; 20% cash rebate on payroll wages for Oregon work (Oregon and non-Oregon residents both eligible). Labor portion stacks with Greenlight Oregon for an effective 26.2% labor rebate.",
        "annual_fund_cap": "$21,200,000 per fiscal year (July 1 - June 30).",
        "application_gates": "Letter of Intent required; equipment must be sourced directly from Oregon vendors (no out-of-state pass-through billing); must comply with Oregon independent-contractor law.",
        "eligible_work": "Film/TV productions, interactive media, commercial production, post-production-only work from Oregon-based companies. Non-scripted work has limited eligibility requiring direct inquiry.",
        "policy_requirements_unconfirmed": "A written DEI policy and a written anti-harassment/reporting policy are reported (WebSearch summary citing Oregon Film) as part of the OPIF contract -- not independently re-confirmed on the official page fetched this session.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="ma_ccm_rebate", jurisdiction_code="MA",
    min_local_spend_usd=1_000_000.0,  # 10M MAD ~ $1M, confirmed directly this session
    min_shoot_days=18,                # confirmed directly: "at least 18 days of work in Morocco, including set construction"
    preapproval_mandatory=True,       # application + initial approval decision (30 days) + bank guarantee precede any work
    expenditure_before_approval_qualifies=False,
    audit_required=True,              # accounting/eligible-expense submission required post-shoot
    cultural_test_required=False,     # no cultural/content test published; a post-release CULTURAL USAGE RIGHTS obligation applies instead (see additional_facts) — a compliance condition, not an eligibility gate
    refundable=True,                  # cash support paid out by CCM
    transferable=False,
    application_deadline=TimingFact(
        value="Initial approval decision issued within 30 days of application submission; "
              "production must begin work within 6 months of the bank-guarantee deposit; "
              "shooting must be completed within 12 months of the first shoot day",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    audit_or_final_certification_deadline=TimingFact(
        value="Final accounting/eligible-expense submission due within 3 months of shoot "
              "completion; CCM pays the support amount in a single installment within a maximum "
              "of 180 days after the commission's decision on a complete payment-request file",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="CCM Foreign Production incentive — official programme page",
        source_url="https://www.ccm.ma/foreign_production/pe/index.html",
        issuing_authority="Centre Cinematographique Marocain (CCM)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST: this profile was a thin Pass A programmatic "
              "migration (source_url=None, only min_local_spend_usd + min_shoot_days from an "
              "internal rate-rule RateCondition). Direct fetch of CCM's own official foreign-"
              "production page performed this session, upgrading to PRIMARY_VERIFIED and confirming "
              "both pre-existing figures exactly (10,000,000 MAD min spend, 18 shooting days). "
              "GENUINELY NEW FACTS: eligible expenses are capped at 90% of total expenditure (a "
              "proportional condition, not a category exclusion). BANK GUARANTEE GATE: 5% of the "
              "requested support amount must be deposited within 30 days of initial approval, "
              "renewable only once. APPLICATION-TO-PAYMENT TIMELINE (fully sequenced, previously "
              "unrecorded): initial approval decision within 30 days of application; work must "
              "begin within 6 months of the guarantee deposit; shooting must complete within 12 "
              "months of the first shoot day; final accounting due within 3 months of shoot "
              "completion; CCM pays within 180 days of a complete payment-request file. SUPPORT "
              "CAP CHANGE: before 2022-03-28 the maximum support was 18,000,000 MAD; from "
              "2022-03-28 onward (the current, already-recorded 30% rate) NO CAP is imposed — "
              "recorded as a genuine, dated regime change, not silently assumed unchanged. "
              "CULTURAL USAGE OBLIGATION (a post-production compliance condition, not an "
              "eligibility gate — recorded as such, distinct from cultural_test_required): "
              "producers must grant CCM Moroccan cultural usage rights for one year following "
              "worldwide release, provide a film copy (with exceptions for internet-focused "
              "works), authorize promotional use, include required credits, and settle all debts "
              "to Moroccan crew and suppliers before final payment. Eligible formats: feature "
              "films, television series, TV films, docufictions, documentaries, and long-form "
              "internet fiction.",
    ),
    additional_facts={
        "eligible_expense_cap_pct": "Eligible expenses capped at 90% of total expenditure.",
        "bank_guarantee": "5% of requested support amount, deposited within 30 days of initial approval, renewable only once.",
        "sequenced_timeline": "Approval within 30 days of application -> work must begin within 6 months of guarantee deposit -> shooting completes within 12 months of first shoot day -> final accounting due within 3 months of shoot completion -> CCM pays within 180 days of a complete payment-request file.",
        "support_cap_history": "Before 2022-03-28: maximum support 18,000,000 MAD (at the prior 20% rate). From 2022-03-28 (current 30% rate): no cap imposed.",
        "cultural_usage_obligation": "Post-release compliance condition (not an eligibility gate): CCM cultural usage rights for 1 year post-worldwide-release, film copy delivery, promotional-use authorization, required credits, and settlement of all debts to Moroccan crew/suppliers.",
        "eligible_formats": "Feature films, television series, TV films, docufictions, documentaries, long-form internet fiction.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="kr_kofic_location_incentive", jurisdiction_code="KR",
    # Worldwide Program Qualification + Cultural Test Completion, 2026-08-19.
    # No NATIONALITY/PERSONNEL cultural-content test found (this
    # registry's specific vocabulary). The program instead uses a
    # discretionary Evaluation Committee scoring "Korean Infrastructure
    # Utilisation", "Korean Participation", and "Quality of Project"
    # (secondary/tertiary sourcing only -- Wikipedia/dbpedia mirrors of
    # koreanfilm.or.kr content not independently re-confirmed on the
    # primary page itself this pass) -- a discretionary evaluation
    # dimension already partially captured by allocation_type, not a
    # personnel-role cultural test. Recorded False for this field's
    # specific meaning; the discretionary criteria are disclosed in
    # additional_facts rather than silently dropped.
    cultural_test_required=False,
    min_local_spend_usd=700_000.0,   # the higher, more complete of the two tiers (>10 shoot days AND >=0.8B KRW)
    min_shoot_days=10,               # from the SAME higher-tier condition
    evidence=EvidenceRecord(
        source_title="app.data.program_rate_rules — RateCondition on kr_kofic_location_incentive",
        source_url=None, issuing_authority="Internal — migrated from already-verified rate-rule condition",
        source_type=SourceType.SECONDARY, status=RecordStatus.CURRENT,
        notes="Pass A programmatic migration (2026-07-26). Two min_qpe_usd conditions exist for "
              "this program: (a) >3 shoot days + 50M-800M KRW spend band (threshold_usd=44,000, "
              "'not pre-evaluable, no shoot-days fact'), and (b) >10 shoot days AND >=0.8B KRW "
              "(~$700K) spend (threshold_usd=700,000). The higher, more fully-specified tier (b) "
              "is recorded here as the representative min_local_spend_usd and min_shoot_days; the "
              "lower tier is preserved in additional_facts rather than silently dropped. Both "
              "citations: koreanfilm.or.kr.",
    ),
    additional_facts={
        "lower_tier": "A second, lower qualifying tier also exists: >3 shoot days in Korea "
                     "with spend between ~$36,000 and ~$700,000 (50M-800M KRW) — source: "
                     "koreanfilm.or.kr.",
        "material_discrepancy_full_reconciliation_2026_07_26": (
            "MATERIAL DISCREPANCY, formally documented after exhaustive reconciliation attempt "
            "(four independent characterizations found, none reachable at a directly-fetchable "
            "official guidelines document): "
            "(1) THIS REPOSITORY'S EXISTING RECORD (program_rate_rules_worldwide.py, citing "
            "Wikipedia/dbpedia + koreanfilm.or.kr from an earlier session): two-tier structure, "
            "20% at 3+ shoot days / >=100,000,000 KRW spend, 25% at 10+ shoot days / "
            ">=0.8 billion KRW spend. "
            "(2) A KOREANFILM.OR.KR NEWS ARTICLE ('Ko-pick', official domain, fetched this "
            "session): single 25% ceiling (no named lower tier), general minimum spend KRW "
            "400,000,000, a KRW 300,000,000 cap specific to foreign projects, a 5-day (not "
            "3/10-day) shoot minimum, and a KRW 896,000,000 TOTAL ANNUAL programme budget. "
            "(3) EN.WIKIPEDIA.ORG (re-fetched directly this session to check the repository's own "
            "citation basis): states 'up to 30% cash rebate' with NO tier structure described at "
            "all -- this itself does not match what record (1) claims Wikipedia said, meaning "
            "either the Wikipedia article changed since record (1) was written, or record (1)'s "
            "citation was imprecise from the start. "
            "(4) THE OFFICIAL koreanfilm.or.kr/eng/coProduction/locIncentive.jsp GUIDELINES PAGE "
            "(the actual named source in this repository's original citation) did not render "
            "usable content on direct fetch (portal shell only); web.archive.org is not reachable "
            "from this environment. "
            "REASONING ATTEMPTED PER THE FULL HYPOTHESIS LIST (not merely noting conflict and "
            "stopping): NOT a translation issue (all four sources are in English). NOT an "
            "eligibility-distinction issue in the sense of describing genuinely different "
            "programmes -- source (2) itself explicitly and separately describes Seoul's REGIONAL "
            "commission scheme (up to 30%, KRW 300,000,000 cap) as distinct from the NATIONAL "
            "KOFIC incentive, and does not conflate the two; this rules out 'regional vs national "
            "conflation' as the explanation for its OWN internal 25% figure. MOST PLAUSIBLE "
            "EXPLANATION: different PROGRAM VERSIONS / EFFECTIVE DATES. KOFIC's Location Incentive "
            "has run continuously since 2011 and is documented elsewhere (industry reporting) as "
            "having been revised more than once; the four sources most likely capture different "
            "snapshots of an evolving tier structure rather than describing four different "
            "programmes or a live authoritative disagreement. SUPPORTING EVIDENCE for treating "
            "source (2)'s KRW 896,000,000 annual-budget figure as describing an OLDER or SMALLER "
            "iteration rather than the current programme: KRW 896,000,000 is approximately "
            "USD 660,000 as a TOTAL annual envelope for a national incentive -- implausibly small "
            "given Wikipedia's own citation that 'Avengers: Age of Ultron' filming in Korea (March "
            "2014) generated 'approximately $23 million in anticipated economic benefits' under "
            "this same programme; a program capable of being associated with a production of that "
            "scale is very unlikely to be currently capped at a ~$660K annual budget. This "
            "specific figure is therefore judged LOW CONFIDENCE for the CURRENT programme even "
            "though the rate/threshold figures alongside it may still be current. CONCLUSION: "
            "genuine, unresolved Material Discrepancy across four sources most likely explained by "
            "program evolution over a 15-year history, not by a translation, terminology, or "
            "national/regional-conflation error. NEITHER characterization is asserted as current "
            "fact. This repository's existing two-tier structure (20%/25%) is LEFT UNCHANGED "
            "(not overwritten by any of the newer, less-corroborated figures) and this profile "
            "remains SECONDARY_VERIFIED. A future session should prioritize locating KOFIC's "
            "actual current PDF guidelines document (not a news article or portal shell) before "
            "attempting another reconciliation pass."
        ),
        # Worldwide Program Qualification + Cultural Test Completion,
        # 2026-08-19. Secondary/tertiary sourcing only (dbpedia/Wikipedia
        # mirrors, not independently re-confirmed on the primary
        # koreanfilm.or.kr page, which did not render usable content on
        # direct fetch this pass either -- consistent with the material
        # discrepancy already documented above).
        "evaluation_committee_criteria_unconfirmed": (
            "Secondary/tertiary sources describe a discretionary Evaluation Committee scoring "
            "'Korean Infrastructure Utilisation', 'Korean Participation', and 'Quality of Project' "
            "-- a discretionary evaluation dimension, not a personnel-nationality cultural test. "
            "Not independently confirmed on the primary page; AUTHORITY_UNRESOLVED for the exact "
            "weighting/threshold."
        ),
    },
))

register(ProgramRequirementsProfile(
    program_slug="fj_film_rebate", jurisdiction_code="FJ",
    local_entity_required=True,        # confirmed directly: production company must be incorporated in Fiji
    min_local_spend_usd=None,          # FJD 250,000 — recorded in additional_facts/STATUTORY_AMOUNTS_ORIGINAL_CURRENCY, not converted
    per_project_cap_usd=None,          # FJD 4,000,000 — recorded in additional_facts/STATUTORY_AMOUNTS_ORIGINAL_CURRENCY, not converted
    preapproval_mandatory=True,        # Film Permit + Provisional Approval must precede production
    expenditure_before_approval_qualifies=False,
    audit_required=True,
    cpa_or_approved_auditor_required=True,  # "audited accounts" required for the final claim
    refundable=True,                   # cash rebate paid out
    transferable=False,
    payment_timing=TimingFact(
        value="Final Certificate application (with audited accounts, submitted through the "
              "licensed Audio-Visual Agent) must be made within 12 months after distribution",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="20% Film Tax Rebate",
        source_url="https://film-fiji.com/incentives-and-legislation/20-film-tax-rebate/",
        issuing_authority="Film Fiji (Fijian government film promotion authority)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST: this profile was a thin Pass A programmatic "
              "migration (source_url=None, only local_entity_required, migrated from an internal "
              "rate-rule condition citing unctad.org). Direct fetch of Film Fiji's own official "
              "page performed this session, confirming and upgrading local_entity_required to "
              "PRIMARY_VERIFIED (production company must be INCORPORATED in Fiji — precise, not "
              "merely 'locally registered'). GOVERNING REGULATION (genuinely new): Income Tax "
              "(Film making & Audio-visual Incentives) Regulations 2016. RATE AND THRESHOLDS: 20% "
              "cash rebate on Total Fiji Expenditure (TFE); minimum TFE FJD 250,000; maximum "
              "rebate FJD 4,000,000 per production. LICENSED AGENT GATE: a licensed Audio-Visual "
              "Agent must be engaged as line producer — a real, named intermediary requirement. "
              "DISTRIBUTION TEST: must demonstrate release plans for at least one significant "
              "international market. FULLY SEQUENCED APPLICATION PROCESS (previously "
              "unrecorded): (1) obtain a Film Permit and Provisional Approval before production "
              "begins; (2) transfer funds to a Fiji bank account before production begins; (3) "
              "submit cost and production reports FORTNIGHTLY during filming; (4) secure public "
              "liability insurance and pay a 1% levy to Fiji National University; (5) include "
              "required credits ('Filmed on location in Fiji', Film Fiji + government "
              "acknowledgement); (6) submit audited accounts and apply for a Final Certificate "
              "within 12 months after distribution (project completion is defined as "
              "post-distribution, not post-wrap). MUTUAL EXCLUSIVITY (a genuine structural fact): "
              "claiming this rebate precludes eligibility for Fiji's other incentive schemes "
              "(F1/F2, post-production packages) — a production cannot stack this with those. All "
              "FJD figures recorded per the Canonical Currency Rule; no USD conversion performed.",
    ),
    additional_facts={
        "min_spend_fjd": "FJD 250,000 minimum Total Fiji Expenditure (TFE).",
        "max_rebate_fjd": "FJD 4,000,000 maximum rebate per production.",
        "legal_basis": "Income Tax (Film making & Audio-visual Incentives) Regulations 2016.",
        "licensed_agent_requirement": "A licensed Audio-Visual Agent must be engaged as line producer.",
        "distribution_test": "Must demonstrate release plans for at least one significant international market.",
        "application_sequence": "Film Permit + Provisional Approval before production -> fund transfer to a Fiji bank account before production -> fortnightly cost/production reports during filming -> public liability insurance + 1% FNU levy -> required credits -> audited accounts + Final Certificate application within 12 months post-distribution.",
        "mutual_exclusivity": "Cannot be combined with Fiji's other incentive schemes (F1/F2, post-production packages).",
    },
))

register(ProgramRequirementsProfile(
    program_slug="my_finas_rebate", jurisdiction_code="MY",
    cultural_test_required=True,
    cultural_test_points=5,      # Appendix C total (expressed directly as rebate percentage points, not abstract points)
    cultural_test_threshold=None,  # each of the 3 categories scores independently up to its own cap; no single aggregate pass/fail minimum -- see notes
    evidence=EvidenceRecord(
        source_title="Film in Malaysia Incentive (FIMI) Guidelines (Foreign Production), Section 2.2 (Cultural Test) and Appendix C",
        source_url="https://filminmalaysia.com/app/uploads/2016/12/GUIDELINE-FOREIGN.pdf",
        issuing_authority="National Film Development Corporation Malaysia (FINAS)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-08-19",
        notes="RESOLVED 2026-08-19 (Worldwide Program Qualification Completion, Queue B): the "
              "official FINAS/Film in Malaysia FIMI Guidelines (Foreign Production, 2021 edition) "
              "were read in full and confirm both the SCOPE and the EXACT table. SCOPE (confirms "
              "and precision-upgrades the prior Pass-A migration's nuance): the Cultural Test gates "
              "ONLY the optional 'Additional Cash Rebate' (up to +5%, on top of the base 30% "
              "rebate, making 35% total) -- it is NOT a condition of base FIMI eligibility. To "
              "apply, the Project must ALSO meet the base QMPE expenditure threshold (MYR "
              "5,000,000). Assessed at Final Certificate stage only (not at Provisional stage) by "
              "the FIMI Approval Committee; failing the required local-cast-and-crew documentation "
              "disqualifies the Project from Cultural Test assessment entirely. EXACT TABLE "
              "(Appendix C: Cultural Test for Films, Foreign Production): (1) Location, max 2% -- "
              "portray Malaysia as a positive country / interesting tourist destination / display "
              "beautiful Malaysian views and destinations / promote Malaysia indirectly; (2) "
              "Cultural Values, max 1% -- display Malaysian culture/lifestyle (food, language, "
              "heritage, tradition) or Malaysian customs/traditions/cultural events (weddings, "
              "festivals, births); (3) Involvement or Hiring of Local Production Cast and Crew, max "
              "2% -- for any of 20 listed named roles (director, co-director, second unit director, "
              "1st AD, screenwriter, lead actor/actress, DOP, second unit DOP, editor, production "
              "designer, sound editing, sound mixing, VFX supervisor, composer, costume designer, "
              "key makeup, key hair, stunt director, stunt coordinator). TOTAL max 5%, each category "
              "capped and scored independently (not a single aggregate pass/fail threshold) -- "
              "'to be eligible for the maximum percentage...in each of the above category, the "
              "Project must portray the relevant cultural elements as described'.",
    ),
    additional_facts={
        "cultural_test_scope": "The cultural test gates a +5% rebate UPLIFT, not the base "
                               "rebate rate itself. Confirmed 2026-08-19 from the official FINAS FIMI "
                               "Guidelines (Foreign Production), Appendix C.",
        "cultural_test_full_table": "Location (max 2%), Cultural Values (max 1%), Local Cast/Crew Involvement across 20 named roles (max 2%). Total 5%, each category independently capped.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="lt_film_centre_cash_rebate", jurisdiction_code="LT",
    local_coproducer_required=True,   # a foreign filmmaker must cooperate with a local Lithuanian production company to apply
    cultural_test_required=True,      # must satisfy at least 2 of 8 published criteria
    cultural_test_points=8,           # 8 total published criteria
    cultural_test_threshold=2,        # at least 2 must be satisfied
    min_local_spend_usd=None,         # EUR 43,000 minimum — recorded in additional_facts/STATUTORY_AMOUNTS_ORIGINAL_CURRENCY, not converted
    min_shoot_days=3,                 # at least 3 days of shooting in Lithuania (animation uses a 20%-of-costs test instead — see additional_facts)
    preapproval_mandatory=True,       # application submitted jointly with the local production company and a secured private donor investor
    evidence=EvidenceRecord(
        source_title="How it works — Lithuanian Film Tax Incentive",
        source_url="https://www.lkc.lt/en/tax-incentives/how-it-works",
        issuing_authority="Lietuvos kino centras (Lithuanian Film Centre)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST: this profile was a thin Pass A programmatic "
              "migration (source_url=None, cultural_test_required only) whose own note flagged an "
              "unresolved 20%-vs-30% rate conflict in the rate-rule registry, explicitly marked "
              "out-of-scope for this requirements-profile layer — that pricing conflict is NOT "
              "resolved here (rate-rule logic is frozen) and remains exactly as already disclosed "
              "in program_rate_rules_worldwide.py. Direct fetch of the Lithuanian Film Centre's own "
              "official 'how it works' page performed this session, upgrading this profile to "
              "PRIMARY_VERIFIED. MECHANISM CLARIFICATION (genuinely new, and possibly explains the "
              "20%/30% ambiguity rather than resolving it definitively): the official page frames "
              "this as a PRIVATE INVESTMENT SCHEME — filmmakers 'save up to 30% of the film "
              "production budget through private investment', with private donors receiving a tax "
              "deduction on invested amounts and an estimated net profit of up to 12%. This is "
              "structurally closer to Belgium's Tax Shelter (investor-side fiscal vehicle) than a "
              "simple government cash rebate — a foreign filmmaker must cooperate with a local "
              "Lithuanian production company AND secure a private donor investor to access the "
              "benefit. This page did not itself restate a separate 20% tier, so the rate-rule "
              "conflict is left open rather than silently resolved by this fetch. NEWLY CONFIRMED: "
              "minimum eligible Lithuanian spend EUR 43,000; at least 80% of eligible production "
              "costs must be incurred in Lithuania; at least 51% of the crew hired by the Lithuanian "
              "production company must be Lithuanian or other EEA citizens; at least 3 days of "
              "shooting in Lithuania for standard productions (animated films instead require at "
              "least 20% of production costs in Lithuania covering design/layouts/VFX/animation "
              "production/shooting); the cultural test requires satisfying at least 2 of 8 published "
              "criteria (themes, historical significance, literary adaptations, European values, "
              "identity issues, artistic merit — full list not itemized on the page reviewed) with "
              "explicit EXCLUSIONS (advertisements, reality shows, violence, pornography, "
              "disinformation, content violating presumption of innocence). Eligible formats: "
              "feature films, TV dramas, documentaries, animated films — domestic, co-produced, or "
              "commissioned (service-agreement) productions.",
    ),
    additional_facts={
        "mechanism": "Private investment/donor tax-deduction scheme (like Belgium's Tax Shelter), not a direct government cash rebate — filmmaker must secure a local production-company partner and a private donor investor.",
        "min_local_spend_eur": "EUR 43,000 minimum eligible Lithuanian spend.",
        "local_spend_pct": "At least 80% of eligible production costs must be incurred in Lithuania.",
        "eea_crew_requirement": "At least 51% of the crew hired by the Lithuanian production company must be Lithuanian or other EEA citizens.",
        "shoot_days_or_animation_alternative": "At least 3 days of shooting in Lithuania for standard productions; animated films instead require at least 20% of production costs in Lithuania (design, layouts, VFX, animation production, or shooting).",
        "cultural_test_structure": "At least 2 of 8 published criteria (themes, historical significance, literary adaptations, European values, identity issues, artistic merit, among others not fully itemized on the page reviewed).",
        "cultural_test_exclusions": "Advertisements, reality shows, content depicting excessive violence, pornography, disinformation, or content violating presumption of innocence.",
        "rate_conflict_unresolved": "This repository's rate-rule registry (program_rate_rules_worldwide.py) carries an unresolved 20%-vs-30% conflict, explicitly out of scope for this profile and NOT resolved by this session's official-source fetch (the fetched page did not itemize a separate 20% tier).",
    },
))


# ── Database Completion Phase (2026-07-26) ────────────────────────────────
# Requirements profiles researched from official administrator sources under
# the canonical legal-interpretation doctrine: statutes/regulations/official
# administrator guidance control; SILENCE IS NOT A RESTRICTION. Where a
# governing authority publishes no cap / no residency rule / no audit
# requirement, that is recorded as an explicit False ("not required" /
# "none published") rather than left as an artificial Unknown. Where a
# field genuinely was not addressed by the sources reviewed in this pass,
# it stays None and the evidence note says exactly what was searched.
#
# FX POLICY: authoritative thresholds are recorded in their ORIGINAL
# currency in additional_facts. min_local_spend_usd is populated ONLY where
# the source itself states USD, or where this repository already carries a
# vetted USD figure for that program. No invented conversions.

register(ProgramRequirementsProfile(
    program_slug="za_dtic_foreign_film", jurisdiction_code="ZA",
    preapproval_mandatory=True,      # application must be submitted BEFORE the project commences anywhere in the world
    min_shoot_days=21,               # at least 21 calendar days of principal photography in South Africa
    cultural_test_required=False,    # foreign-film incentive: no cultural/content test published; a B-BBEE procurement requirement applies instead (see additional_facts)
    refundable=True,                 # cash rebate paid out by the dtic
    transferable=False,
    audit_required=True,
    cpa_or_approved_auditor_required=True,
    evidence=EvidenceRecord(
        source_title="Foreign Film and Television Production and Post-Production Incentive — Programme Guidelines",
        source_url="https://www.thedtic.gov.za/financial-and-non-financial-support/incentives/film-incentive/foreign-film-and-television-production-and-post-production-incentive-foreign-film/",
        issuing_authority="Department of Trade, Industry and Competition (the dtic), South Africa",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Official dtic programme page + published Programme Guidelines PDF. 25% of QSAPE "
              "(Qualifying South African Production Expenditure), capped at R25 million per "
              "project. Minimum QSAPE R15 million. At least 50% of principal photography and at "
              "least 21 calendar days must be filmed in South Africa — BOTH waivable where QSAPE "
              "is at least R100 million. Additional +5% for shooting AND post in SA using a "
              "black-owned service company; a further +5% for at least R15m of post-production "
              "budget spent in SA. B-BBEE: applicant must procure a minimum 20% of qualifying "
              "goods/services from entities at least 51% black-owned by South African citizens "
              "and trading at least one year. Application MUST precede commencement of the "
              "project anywhere in the world — commencing earlier is expressly at the "
              "applicant's own risk. Caps/thresholds are stated in ZAR; no USD figure is "
              "published, so min_local_spend_usd/per_project_cap_usd are left unset rather than "
              "FX-converted (originals in additional_facts). No annual programme cap, no company "
              "cap, no sunset date, no transferability mechanism and no stacking prohibition are "
              "published in the guidelines reviewed.",
    ),
    additional_facts={
        "min_qsape_zar": "R15,000,000 minimum Qualifying South African Production Expenditure (authoritative original currency).",
        "per_project_cap_zar": "R25,000,000 cap per project (authoritative original currency).",
        "principal_photography_test": "At least 50% of principal photography AND at least 21 calendar days in South Africa; both waived where QSAPE is at least R100 million.",
        "uplifts": "+5% for shooting and post in SA via a black-owned service company; +5% for at least R15m post-production spend in SA.",
        "bbbee_procurement": "Minimum 20% of qualifying goods/services from entities at least 51% black-owned by South African citizens, trading at least one year.",
        "annual_cap": "None published in the programme guidelines reviewed.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="is_film_reimbursement_scheme", jurisdiction_code="IS",
    preapproval_mandatory=True,      # application must be submitted to the Icelandic Film Centre BEFORE production commences in Iceland
    cultural_test_required=False,    # no cultural test published; the 35% tier is gated on spend/days/crew, not content
    refundable=True,                 # reimbursement paid out
    transferable=False,
    application_deadline=TimingFact(
        value="No fixed deadline — applications accepted at any time of year, but must be "
              "submitted before production commences in Iceland",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    evidence=EvidenceRecord(
        source_title="Iceland Film Incentives / How to Apply — Film in Iceland; Icelandic Film Centre reimbursement scheme",
        source_url="https://filminiceland.com/incentives",
        issuing_authority="Film in Iceland (Ministry of Culture and Business Affairs) / Icelandic Film Centre",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Two-tier scheme. BASE TIER 25%: every feature film, TV series and documentary "
              "incurring production costs in Iceland qualifies — explicitly NO minimum spend and "
              "explicitly NO cap on the total reimbursement amount (this is a published absence "
              "of a restriction, not an unknown). ENHANCED TIER 35% requires ALL of: production "
              "costs in Iceland of at least ISK 350 million; at least 30 working days in Iceland "
              "(shooting or defined post-production days); of those, at least 10 must be shooting "
              "days in Iceland; and at least 50 crew members working directly on the project, "
              "with all payments taxed in Iceland. Applications go to the Icelandic Film Centre "
              "before production starts in Iceland and may be filed at any time of year (no "
              "round-based deadline). min_local_spend_usd deliberately left unset: the base tier "
              "has NO minimum, and the 35% tier's threshold is stated in ISK only.",
    ),
    additional_facts={
        "base_tier": "25% reimbursement — no minimum spend and no cap on the total amount reimbursed (expressly published).",
        "enhanced_tier_threshold_isk": "ISK 350,000,000 minimum Icelandic production cost for the 35% tier (authoritative original currency).",
        "enhanced_tier_days": "At least 30 working days in Iceland, of which at least 10 must be shooting days.",
        "enhanced_tier_crew": "At least 50 crew members working directly on the project, all payments taxed in Iceland.",
        "cap": "No cap on total reimbursement is published for either tier.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="nl_film_production_incentive", jurisdiction_code="NL",
    local_entity_required=True,      # applicant must be an independent production company established in NL (or EU/EEA/CH) — see notes
    preapproval_mandatory=True,      # round-based application before the incentive is granted
    cultural_test_required=False,    # assessed on financial/legal/business criteria via an automatic points system, not a cultural test
    refundable=True,
    transferable=False,
    allocation_type=AllocationType.COMPETITIVE,  # fixed annual budget split across 4 rounds; points-system ranked
    evidence=EvidenceRecord(
        source_title="Netherlands Film Production Incentive — Netherlands Film Fund (Filmfonds)",
        source_url="https://www.filmfonds.nl/en/funding/fund/netherlands-film-production-incentive",
        issuing_authority="Netherlands Film Fund (Nederlands Filmfonds)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="2026 programme: EUR 20 million annual budget for film productions across 4 "
              "application rounds (EUR 5 million per round). Rates: 35% for feature films, "
              "feature-length documentaries and feature-length animation; 30% for high-end series. "
              "COMPANY CAP: up to EUR 3 million per year per production company — a real, "
              "published company-level cap. Minimum production budgets: EUR 600,000 (feature film "
              "and feature-length animation), EUR 250,000 (feature-length documentary), EUR "
              "1,000,000 per episode for high-end series with at least EUR 250,000 minimum "
              "qualifying Dutch spend per episode. Applicant must be an INDEPENDENT production "
              "company established in the Netherlands (incl. Bonaire, Sint Eustatius, Saba) or in "
              "an EU member state, EEA country, or Switzerland, and must have been continuously "
              "active in audiovisual production for at least two years — local_entity_required is "
              "recorded True on the basis that an establishment requirement exists, with the "
              "important nuance that EU/EEA/Swiss establishment also satisfies it (not "
              "NL-exclusive). Assessment is automatic against strict financial/legal/business "
              "criteria using a points system — no cultural test. Thresholds are stated in EUR "
              "only; no USD figure published, so min_local_spend_usd is left unset.",
    ),
    additional_facts={
        "min_production_budget_eur": "EUR 600,000 feature film / feature-length animation; EUR 250,000 feature-length documentary; EUR 1,000,000 per episode for high-end series.",
        "min_dutch_spend_eur_high_end_series": "EUR 250,000 minimum qualifying Dutch production costs per episode.",
        "company_cap_eur": "EUR 3,000,000 per year per production company (published company-level cap).",
        "annual_budget_eur": "EUR 20,000,000 for 2026, split across 4 rounds of EUR 5,000,000.",
        "establishment_requirement": "Independent production company established in NL (incl. Caribbean Netherlands) OR an EU/EEA member state OR Switzerland; at least 2 years of continuous audiovisual production activity.",
        "rates": "35% feature film / feature documentary / feature animation; 30% high-end series.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="il_foreign_production_fund", jurisdiction_code="IL",
    local_entity_required=True,      # applicant company must be registered in Israel; foreign producers apply via an Israeli producer
    min_local_spend_usd=50_000.0,    # source states eligible costs from USD 50,000 (matches this repo's existing vetted figure)
    cultural_test_required=False,    # no cultural/content test published for the foreign-production rebate
    refundable=True,
    transferable=False,
    payment_timing=TimingFact(
        value="80% of the rebate paid during filming in Israel against invoices, on approval by "
              "the Ministry of Economy & Industry's professional advisor; payment expected within "
              "60 days of the specified terms being met",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    evidence=EvidenceRecord(
        source_title="Information for Foreign Producers — Israel Cash Rebate (NFCT / Ministry of Economy & Industry)",
        source_url="https://nfct.org.il/en/information-for-foreign-producers/",
        issuing_authority="Israel Ministry of Economy & Industry; NFCT (Israel Film Fund administration)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Cash rebate for foreign productions. Applications must be submitted by a company "
              "registered in Israel; international production companies apply VIA an Israeli "
              "producer — a genuine local-entity requirement. Eligible production costs stated "
              "from USD 50,000 (this USD figure is stated by the source itself and matches the "
              "vetted min_qpe_usd already in this repository's rate rules, so it is recorded "
              "directly rather than FX-converted). Animation production and post-production are "
              "included, with up to 10% of budget reimbursable for each. Payment mechanics are "
              "unusually favourable and explicitly published: 80% disbursed DURING filming "
              "against invoices on the professional advisor's approval, within 60 days of terms "
              "being met. Sources reviewed publish no cultural test, no sunset date, no "
              "transferability mechanism and no stacking prohibition. Note: reporting on the "
              "scheme describes an upper bound around USD 1.5 million per production; whether "
              "that bounds eligible COSTS or the rebate PAYOUT is not disambiguated in the "
              "sources reviewed, so no per_project_cap_usd is asserted — see additional_facts.",
    ),
    additional_facts={
        "upper_bound_ambiguity": "Sources describe an upper bound of approximately USD 1.5 million per production, but do not disambiguate whether this bounds eligible production COSTS or the rebate PAYOUT. Not recorded as a per-project cap pending clarification from the administrator.",
        "animation_and_post": "Animation production and post-production are eligible, with up to 10% of budget reimbursable for each.",
        "payment_mechanics": "80% paid during filming against invoices (advisor-approved); balance on completion. Within 60 days of terms being met.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="no_film_incentive", jurisdiction_code="NO",
    preapproval_mandatory=True,      # applications must be submitted before the start of production in Norway
    cultural_test_required=True,     # explicit "cultural and production test" in the scheme's own requirements
    cultural_test_points=51,         # max across Part 1 (Cultural, max 16) + Part 2 (Production, max 35), confirmed 2026-08-19 via Lovdata (official Norwegian legal database)
    cultural_test_threshold=20,      # min 20/51 overall, WITH a sub-minimum of >=4 from Part 1 (Cultural Test) specifically
    refundable=True,
    transferable=False,
    allocation_type=AllocationType.COMPETITIVE,  # annual incentive frame allocated to a limited number of productions per round
    application_deadline=TimingFact(
        value="Annual application window (for the 2027 frame: opens June, deadline November); "
              "in all cases the application must be submitted before production starts in Norway",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    audit_or_final_certification_deadline=TimingFact(
        value="The disbursement request must be submitted within six months of the end of "
              "production in Norway",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="The Norwegian Film Production Incentive — Norsk filminstitutt (NFI)",
        source_url="https://www.nfi.no/en/funding-schemes/insentiv/the-norwegian-film-production-incentive",
        issuing_authority="Norsk filminstitutt / Norwegian Film Institute (NFI)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Refund of up to 25% of approved Norwegian production costs. Covers fiction "
              "features, documentary films and series, drama series, animation, studio production "
              "and post-production. REAL PUBLISHED GATES: minimum Norwegian spend NOK 4 million; "
              "minimum total (worldwide) budget NOK 25m feature / NOK 10m per episode drama / "
              "NOK 10m feature documentary / NOK 5m per episode documentary series; minimum 30% "
              "NON-Norwegian financing; a cultural and production test plus project-scale "
              "criteria; and a producer-track-record requirement (the main producer must have "
              "produced at least one film, drama series or documentary series within the last "
              "five years). Allocation is round-based against a fixed annual incentive frame "
              "awarded to a limited number of productions — recorded COMPETITIVE. Disbursement "
              "request due within six months of the end of Norwegian production. Thresholds are "
              "stated in NOK only; no USD figure published, so min_local_spend_usd left unset.",
    ),
    additional_facts={
        "min_norwegian_spend_nok": "NOK 4,000,000 minimum spend in Norway (authoritative original currency).",
        "min_total_budget_nok": "NOK 25m feature film; NOK 10m per episode drama series; NOK 10m feature documentary; NOK 5m per episode documentary series.",
        "foreign_financing_requirement": "Minimum 30% non-Norwegian financing required.",
        "producer_track_record": "Main producer must have produced at least one film, drama series or documentary series within the last five years.",
        "disbursement_deadline": "Disbursement request must be submitted within six months of the end of production in Norway.",
        "cultural_test_full_table": (
            "RESOLVED 2026-08-19 (Worldwide Program Qualification Completion, Queue B): exact point "
            "table confirmed via lovdata.no (Norway's official government legal database), Vedlegg 1 "
            "(Appendix 1, Qualification Test) to Forskrift om insentivordning for film- og "
            "serieproduksjoner (Regulation on the Incentive Scheme for Film and Series Productions), "
            "in force since 2016-01-01. Part 1 Cultural Test (max 16, min 4 required): story based "
            "on Norwegian/European cultural-historical events (0-2); character from Norwegian/"
            "European culture/history/society (0-2); Norwegian/European setting (0-2); script/themes "
            "adapted from literature or other art forms (0-2); contemporary cultural/sociological/"
            "political themes (0-2); reflects Norwegian/European values/culture/identity/customs/"
            "traditions (0-2); Norwegian or European director/screenwriter/literary author (0-2); "
            "Norwegian or other European language (0-2). Part 2 Production Test (max 35): "
            "cinematically ambitious genre-advancing work (0-3); develops filmmaker competence for "
            "ambitious high-quality projects (0-4); key creatives Norwegian/British/EEA citizens "
            "across 19 listed positions (0-8); >=51% Norwegian/British/EEA crew (0-4); Norwegian "
            "locations/studios (0-4); Norwegian/UK/EEA suppliers (0-4); Norwegian/UK/EEA "
            "post-production -- sound/VFX/editing/music (0-6); sustainable/environmentally-friendly "
            "filming strategy (0-2)."
        ),
    },
))


register(ProgramRequirementsProfile(
    program_slug="pt_scri_pt_cash_rebate", jurisdiction_code="PT",
    local_entity_required=True,      # must establish a company or branch subject to tax in Portugal BEFORE incurring eligible expenditure
    preapproval_mandatory=True,      # registration + application precede eligible expenditure
    cultural_test_required=True,     # the 25%-vs-30% rate is set by a Cultural Test
    cultural_test_points=100,        # Parte A (Cultural Value) 60 + Parte B (Creative/Technical Cooperation) 40, confirmed 2026-08-19
    cultural_test_threshold=45,      # general minimum 45/100 WITH >=18 from Parte A specifically; foreign-initiative/service productions (local executive producer) instead need only 20/100 with >=8 from Parte A -- see additional_facts
    refundable=True,
    transferable=False,
    sunset_date="2029-12-31",        # SCRI.PT programme budget runs across 2026-2029
    evidence=EvidenceRecord(
        source_title="SCRI.PT — Sistema de Incentivos ao Cinema e Audiovisual (RIPAC); Cash Rebate — Portugal Film Commission / ICA",
        source_url="https://portugalfilmcommission.com/en/incentive-to-film-recording-and-production/",
        issuing_authority="ICA — Instituto do Cinema e do Audiovisual; Portugal Film Commission",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="As of 2026-02-20 SCRI.PT came into force, consolidating the former cash rebate and "
              "cash refund into one legal framework (RIPAC). Rate 25-30% of eligible expenditure, "
              "determined by a CULTURAL TEST and project characteristics; up to 40% in Madeira, "
              "the Azores and low-density interior regions. Minimum Portuguese expenditure: EUR "
              "500,000 fiction and animation; EUR 250,000 documentary and post-production. "
              "Applicants must be entered in the Register of Cinematographic and Audiovisual "
              "Entities AND must establish a company or branch subject to tax in Portugal BEFORE "
              "incurring eligible expenditure — a genuine local-entity + preapproval gate. "
              "Programme budget EUR 350 million across 2026-2029, of which EUR 200 million is "
              "non-repayable production support; sunset_date recorded as the end of that "
              "published programme window. Thresholds stated in EUR only — min_local_spend_usd "
              "left unset rather than FX-converted. CULTURAL TEST (RESOLVED 2026-08-19, Worldwide "
              "Program Qualification Completion, Queue B): the OLD binary cultural test was "
              "replaced by a real 100-point evaluation table under Article 7 of Portaria n.º "
              "276-B/2026/1 (the SCRI.PT implementing regulation, in force since 2026-06-17/26), "
              "confirmed via Morais Leitão's direct legal analysis quoting the Portaria's own "
              "figures: Parte A (Valor Cultural / Cultural Value), max 60 points; Parte B "
              "(Cooperação Criativa e Técnica / Creative and Technical Cooperation), max 40 points; "
              "total 100. GENERAL minimum: 45 of 100 overall, WITH >=18 from Parte A specifically. "
              "FOREIGN-INITIATIVE PRODUCTIONS WITH A LOCAL EXECUTIVE PRODUCER (the relevant category "
              "for foreign/service productions -- CineGlobe's typical modeling case): a LOWER "
              "threshold applies, 20 of 100 total WITH >=8 from Parte A -- a genuine, real, "
              "different (lower) bar for exactly the production type this registry models. GENUINE "
              "DISCLOSED RESIDUAL: the item-by-item point breakdown WITHIN Parte A and Parte B "
              "(i.e. which specific criteria carry how many of the 60/40 points) was not found in "
              "any source checked this pass -- the ICA's own cash-rebate page states only that the "
              "evaluation covers 'identification and nationality of authors, producers, actors, "
              "technicians and other professionals hired in Portugal'; the 143-page general ICA "
              "Regulamento Geral PDF was checked but did not yield readable text for this specific "
              "annex within the research budget available. AUTHORITY UNRESOLVED for the exact "
              "sub-item point allocation specifically, not for the aggregate structure or "
              "thresholds, which ARE confirmed.",
    ),
    additional_facts={
        "min_portuguese_spend_eur": "EUR 500,000 fiction and animation; EUR 250,000 documentary and post-production (authoritative original currency).",
        "rate_band": "25-30% depending on the Cultural Test and project characteristics; up to 40% in Madeira, the Azores and low-density interior regions.",
        "programme_budget_eur": "EUR 350,000,000 total across 2026-2029, of which EUR 200,000,000 is non-repayable production support.",
        "registration_requirement": "Applicant must be entered in the Register of Cinematographic and Audiovisual Entities and have a Portuguese tax-resident company or branch before incurring eligible expenditure.",
        "framework": "SCRI.PT / RIPAC, in force from 2026-02-20, consolidating the prior cash rebate and cash refund.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="th_boi_incentive", jurisdiction_code="TH",
    preapproval_mandatory=True,      # ICM Form 1 application + filming permission required before qualifying
    cultural_test_required=False,    # no cultural test; a discretionary +5% "Thai soft power / tourism promotion" uplift exists instead
    refundable=True,
    transferable=False,
    evidence=EvidenceRecord(
        source_title="Thailand Incentive Measures Guidelines (2025) — Thailand Film Office (TFO), Department of Tourism",
        source_url="https://tfo.dot.go.th/incentive-measures/",
        issuing_authority="Thailand Film Office (TFO), Department of Tourism; Film, Video and Digital Media Committee",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Tiered cash rebate on qualified Thailand spend: 15% from THB 50 million; 20% for "
              "THB 100-150 million; 25% above THB 150 million; maximum 30% inclusive of "
              "additional incentives. Minimum qualifying Thai spend THB 50 million (paid to Thai "
              "crew and Thai companies). A +5% uplift is available for promoting Thai tourism / "
              "Soft Power / positive depiction of the country, assessed against the criteria in "
              "Form ICM 1 — discretionary in character, not an automatic entitlement. "
              "IMPORTANT PUBLISHED ABSENCE OF A RESTRICTION: the revised programme carries NO CAP "
              "on the total rebated amount per project (an explicit change from the previous "
              "regime) — recorded here as a published absence, not an unknown. Productions must "
              "obtain filming permission from the Film, Video and Digital Media Committee and "
              "file ICM Form 1 with detailed budgets/scope plus film permit, company registration "
              "and notarised documents. Thresholds stated in THB; the sources' USD equivalents "
              "are journalistic approximations, so min_local_spend_usd is left unset and the THB "
              "original is recorded instead.",
    ),
    additional_facts={
        "min_thai_spend_thb": "THB 50,000,000 minimum qualified Thailand spend to Thai crew and Thai companies (authoritative original currency).",
        "rate_tiers_thb": "15% from THB 50m; 20% for THB 100m-150m; 25% above THB 150m; 30% maximum inclusive of uplifts.",
        "per_project_cap": "None — the revised programme expressly removed the cap on total rebate per project.",
        "soft_power_uplift": "+5% for promoting Thai tourism / Soft Power / positive depiction of Thailand, assessed against Form ICM 1 criteria (discretionary).",
        "permitting": "Filming permission from the Film, Video and Digital Media Committee is required.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="ro_film_office_cash_rebate", jurisdiction_code="RO",
    preapproval_mandatory=True,      # financing agreement signed with OFIC before the rebate is secured; all filings via app.ofic.ro
    cultural_test_required=False,    # eligibility is by project TYPE (fiction/documentary/animation in, soaps/sitcoms/ads/games out), not a cultural points test
    refundable=True,
    transferable=False,
    annual_program_cap_usd=None,     # EUR 55 million annual cap — recorded in original currency, see additional_facts
    sunset_date="2029-12-31",        # financing agreements may be signed through end-2029 (payments run to end-2031)
    evidence=EvidenceRecord(
        source_title="Romanian cash rebate state aid scheme — Office for Film and Cultural Investments (OFIC)",
        source_url="https://app.ofic.ro/",
        issuing_authority="Office for Film and Cultural Investments (OFIC), Government of Romania",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="30% cash rebate on qualified Romanian expenditure, administered by OFIC. "
              "PER-PROJECT CAP: EUR 10 million. ANNUAL PROGRAMME CAP: EUR 55 million (overall "
              "envelope approximately EUR 250 million). Minimum local spend: EUR 100,000 feature "
              "over 60 minutes; EUR 100,000 per episode of a series; EUR 50,000 documentary; EUR "
              "15,000 short film, animated film over 5 minutes, or animated series. ELIGIBLE: "
              "short/medium/long fiction, series and miniseries, artistic documentaries, animated "
              "films. EXPRESSLY NOT ELIGIBLE: soap operas, sitcoms, commercials, video games — a "
              "published exclusion list, which is why cultural_test_required is recorded False "
              "(eligibility turns on format, not a cultural points test). STACKING IS EXPRESSLY "
              "PERMITTED and quantified: the rebate may be accumulated with other state aid up to "
              "60% for EU co-productions and up to 100% for 'difficult films' — a published "
              "permission, not a prohibition. Financing agreements may be signed through end-2029 "
              "with payments running through end-2031; sunset_date reflects the agreement "
              "window. All filings are made online via app.ofic.ro. Caps/thresholds are stated in "
              "EUR only, so the USD cap fields are left unset and originals recorded below.",
    ),
    additional_facts={
        "min_local_spend_eur": "EUR 100,000 feature film over 60 minutes; EUR 100,000 per series episode; EUR 50,000 documentary; EUR 15,000 short/animated film over 5 minutes or animated series.",
        "per_project_cap_eur": "EUR 10,000,000 per single project.",
        "annual_programme_cap_eur": "EUR 55,000,000 per year; overall envelope approximately EUR 250,000,000.",
        "stacking_permitted": "Expressly cumulable with other state aid up to 60% for EU co-productions and up to 100% for 'difficult films'.",
        "ineligible_formats": "Soap operas, sitcoms, commercials and video games are expressly excluded.",
        "agreement_and_payment_window": "Financing agreements may be signed through end-2029; payments run through end-2031.",
    },
))


# ══════════════════════════════════════════════════════════════════════════
# CANONICAL STATUTORY AMOUNTS — ORIGINAL PUBLISHED CURRENCY
# ══════════════════════════════════════════════════════════════════════════
# Canonical currency rule (Database Completion phase, 2026-07-26):
#
#   "Store every statutory monetary value exactly as published by the
#    governing authority. The database is the legal source of truth. Do not
#    normalize statutory values into USD, EUR, or any other common currency
#    during this phase. Never replace or overwrite an authoritative
#    local-currency value with a converted value."
#
# WHY THIS TABLE EXISTS RATHER THAN A SCHEMA CHANGE: ProgramRequirementsProfile
# carries USD-denominated fields (min_local_spend_usd, per_project_cap_usd,
# ...) inherited from earlier phases, and a schema refactor is explicitly out
# of scope for this phase. Rather than silently leaving converted figures as
# if they were statutory, this table records the AUTHORITATIVE original —
# amount, currency, source, effective date — for every program whose governing
# authority publishes in a currency other than USD. Where this table and a
# profile's USD field disagree, THIS TABLE CONTROLS; the USD field is a legacy
# derived convenience value and is NOT authoritative.
#
# Currency normalization, FX, inflation adjustment and cross-jurisdiction
# comparison belong exclusively to the optimizer phase, after the database is
# frozen. Nothing in this table is consumed by any calculation path: the
# requirements registry is disclosure-only (verified — the pricing engine
# takes its thresholds from program_rate_rules.RateCondition.min_qpe_usd, not
# from here).
#
# Shape: program_slug -> {field_name: {amount, currency, basis, source,
#                                      effective_date, legacy_usd_value}}
# legacy_usd_value records what the non-authoritative USD field currently
# holds, so the divergence is explicit and auditable rather than hidden.

STATUTORY_AMOUNTS_ORIGINAL_CURRENCY: dict[str, dict[str, dict]] = {
    "cy_film_rebate": {
        "min_local_spend": {
            "amount": 200_000, "currency": "EUR", "basis": "Minimum qualifying Cyprus expenditure (feature film)",
            "source": "Cyprus Film Commission / Invest Cyprus (film.investcyprus.org.cy)",
            "effective_date": None, "legacy_usd_value": 200_000.0,
        },
        "per_project_cap": {
            "amount": 650_000, "currency": "EUR", "basis": "Maximum aid per production",
            "source": "Cyprus Film Commission / Invest Cyprus (film.investcyprus.org.cy)",
            "effective_date": None, "legacy_usd_value": 650_000.0,
        },
    },
    "es_tax_credit_foreign": {
        "min_local_spend": {
            "amount": 1_000_000, "currency": "EUR", "basis": "Minimum Spanish expenditure (EUR 200,000 for animation)",
            "source": "Spanish tax authority / ICAA foreign-production deduction",
            "effective_date": None, "legacy_usd_value": 1_140_523.96,
        },
        "per_project_cap": {
            "amount": 20_000_000, "currency": "EUR", "basis": "Cap per feature (EUR 10,000,000 per episode)",
            "source": "Spanish tax authority / ICAA foreign-production deduction",
            "effective_date": None, "legacy_usd_value": 22_810_479.13,
        },
    },
    "hr_cash_rebate": {
        "min_local_spend": {
            "amount": 263_000, "currency": "EUR", "basis": "Minimum Croatian expenditure (feature film)",
            "source": "Invest Croatia (investcroatia.gov.hr) / HAVC",
            "effective_date": None, "legacy_usd_value": 265_000.0,
        },
    },
    "de_dfff": {
        "per_project_cap": {
            "amount": 25_000_000, "currency": "EUR", "basis": "DFFF II cap per project",
            "source": "Filmförderungsanstalt (ffa.de)",
            "effective_date": None, "legacy_usd_value": 28_513_098.92,
        },
    },
    "it_tax_credit_foreign": {
        "per_project_cap": {
            "amount": 20_000_000, "currency": "EUR", "basis": "Cap per year per company",
            "source": "Ministero della Cultura (MiC) — tax credit for foreign productions",
            "effective_date": None, "legacy_usd_value": 22_810_479.13,
        },
        "min_local_spend": {
            "amount": 250_000, "currency": "EUR", "basis": "Minimum eligible cost (not independently re-confirmed against a directly-fetched DGCA page this session)",
            "source": "Direzione Generale Cinema e Audiovisivo (DGCA), Ministero della Cultura — via WebSearch summary citing the DGCA framework",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_work_cap": {
            "amount": 9_000_000, "currency": "EUR", "basis": "Cap per individual work, increasable to EUR 18,000,000 if at least 30% of total production cost is foreign-funded — distinct from the per-company annual cap above",
            "source": "Direzione Generale Cinema e Audiovisivo (DGCA), Ministero della Cultura — via WebSearch summary citing the DGCA framework",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "ie_section_481": {
        "per_project_cap": {
            "amount": 125_000_000, "currency": "EUR", "basis": "Cap on eligible expenditure per project, for projects certified on/after 28 March 2024",
            "source": "Revenue Commissioners / Screen Ireland — Section 481",
            "effective_date": "2024-03-28", "legacy_usd_value": 142_565_494.59,
        },
    },
    "fr_trip": {
        "min_local_spend": {
            "amount": 250_000, "currency": "EUR", "basis": "Minimum French qualifying expenditure (alternative test: 50% of total production budget)",
            "source": "Centre national du cinéma et de l'image animée (CNC) — TRIP",
            "effective_date": None, "legacy_usd_value": 285_130.99,
        },
        "per_project_cap": {
            "amount": 30_000_000, "currency": "EUR", "basis": "Cap per project",
            "source": "Centre national du cinéma et de l'image animée (CNC) — TRIP",
            "effective_date": None, "legacy_usd_value": 34_215_718.70,
        },
    },
    "ca_on_opstc": {
        "min_total_budget": {
            "amount": 1_000_000, "currency": "CAD", "basis": "Production cost must exceed this for a feature; series thresholds are CAD 100,000/episode (<30 min) and CAD 200,000/episode (longer)",
            "source": "Ontario Creates — OPSTC",
            "effective_date": None, "legacy_usd_value": 707_463.74,
        },
    },
    "mt_mfc_rebate": {
        "min_local_spend": {
            "amount": 100_000, "currency": "EUR", "basis": "Minimum qualifying Malta expenditure, general case (EUR 50,000 for 'Difficult Audiovisual Work') -- CONFIRMED via direct pypdf text extraction of the official MFC Cash Rebate Guidelines (Official Document, January 2019); the frozen rate rule (program_rate_rules.py) still cites an undated EUR 50,000 general-case figure as an unresolved Material Discrepancy against this confirmed figure -- see mt_mfc_rebate Requirements Profile evidence notes",
            "source": "Malta Film Commission -- Financial Incentives for the Audiovisual Industry: CASH REBATE GUIDELINES (Official Document, January 2019)",
            "effective_date": "2019-01-01", "legacy_usd_value": 113_000.0,
        },
        "min_total_budget": {
            "amount": 200_000, "currency": "EUR", "basis": "Minimum overall production budget, general case (EUR 100,000 for 'Difficult Audiovisual Work') -- CONFIRMED via direct pypdf text extraction of the official MFC Cash Rebate Guidelines",
            "source": "Malta Film Commission -- Financial Incentives for the Audiovisual Industry: CASH REBATE GUIDELINES (Official Document, January 2019)",
            "effective_date": "2019-01-01", "legacy_usd_value": 226_000.0,
        },
    },
    "gr_cash_rebate": {
        "min_local_spend": {
            "amount": 100_000, "currency": "EUR", "basis": "Minimum qualifying Greek expenditure",
            "source": "EKOME / Enterprise Greece",
            "effective_date": None, "legacy_usd_value": 114_052.40,
        },
    },
    "ma_ccm_rebate": {
        "min_local_spend": {
            "amount": 10_000_000, "currency": "MAD", "basis": "Minimum Moroccan spend (accompanied by an 18-shooting-day requirement)",
            "source": "Centre Cinématographique Marocain (CCM)",
            "effective_date": None, "legacy_usd_value": 1_000_000.0,
        },
    },
    "kr_kofic_location_incentive": {
        "min_local_spend": {
            "amount": 800_000_000, "currency": "KRW", "basis": "Higher tier: >10 shoot days in Korea AND at least KRW 0.8bn spend. Lower tier: >3 shoot days with spend between KRW 50,000,000 and KRW 800,000,000",
            "source": "KOFIC (koreanfilm.or.kr)",
            "effective_date": None, "legacy_usd_value": 700_000.0,
        },
    },
    # ── Database Completion phase batch 1+2 (2026-07-26): originals recorded
    #    at the moment of population. No USD field was ever populated for
    #    these from a conversion — the USD fields stay unset by design.
    "za_dtic_foreign_film": {
        "min_local_spend": {
            "amount": 15_000_000, "currency": "ZAR", "basis": "Minimum Qualifying South African Production Expenditure (QSAPE)",
            "source": "Department of Trade, Industry and Competition (the dtic) — Foreign Film Programme Guidelines",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 25_000_000, "currency": "ZAR", "basis": "Cap per project",
            "source": "Department of Trade, Industry and Competition (the dtic) — Foreign Film Programme Guidelines",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "is_film_reimbursement_scheme": {
        "min_local_spend": {
            "amount": 350_000_000, "currency": "ISK", "basis": "Minimum Icelandic production cost for the enhanced 35% tier. The base 25% tier has NO minimum spend and NO cap.",
            "source": "Film in Iceland / Icelandic Film Centre",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "nl_film_production_incentive": {
        "min_total_budget": {
            "amount": 600_000, "currency": "EUR", "basis": "Minimum production budget, feature film and feature-length animation (EUR 250,000 documentary; EUR 1,000,000 per episode high-end series)",
            "source": "Netherlands Film Fund (Filmfonds)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "company_cap": {
            "amount": 3_000_000, "currency": "EUR", "basis": "Maximum support per year per production company",
            "source": "Netherlands Film Fund (Filmfonds)",
            "effective_date": "2026-01-01", "legacy_usd_value": None,
        },
    },
    "no_film_incentive": {
        "min_local_spend": {
            "amount": 4_000_000, "currency": "NOK", "basis": "Minimum spend in Norway (minimum total budget NOK 25m feature / NOK 10m per episode drama)",
            "source": "Norsk filminstitutt (NFI)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "pt_scri_pt_cash_rebate": {
        "min_local_spend": {
            "amount": 500_000, "currency": "EUR", "basis": "Minimum Portuguese expenditure, fiction and animation (EUR 250,000 documentary and post-production)",
            "source": "ICA — Instituto do Cinema e do Audiovisual (SCRI.PT / RIPAC)",
            "effective_date": "2026-02-20", "legacy_usd_value": None,
        },
    },
    "th_boi_incentive": {
        "min_local_spend": {
            "amount": 50_000_000, "currency": "THB", "basis": "Minimum qualified Thailand spend to Thai crew and Thai companies. No per-project cap on the rebate.",
            "source": "Thailand Film Office (TFO), Department of Tourism",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "ro_film_office_cash_rebate": {
        "min_local_spend": {
            "amount": 100_000, "currency": "EUR", "basis": "Minimum local spend, feature over 60 minutes and per series episode (EUR 50,000 documentary; EUR 15,000 short/animated)",
            "source": "Office for Film and Cultural Investments (OFIC), Romania",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 10_000_000, "currency": "EUR", "basis": "Cap per single project",
            "source": "Office for Film and Cultural Investments (OFIC), Romania",
            "effective_date": None, "legacy_usd_value": None,
        },
        "annual_program_cap": {
            "amount": 55_000_000, "currency": "EUR", "basis": "Annual programme budget cap (overall envelope approx. EUR 250,000,000)",
            "source": "Office for Film and Cultural Investments (OFIC), Romania",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "ca_bc_pstc": {
        "accreditation_fee": {
            "amount": 19_000, "currency": "CAD", "basis": "Accreditation application fee for productions beginning principal photography after 2024-12-31 (major production certificate CAD 5,000)",
            "source": "Province of British Columbia — Production services tax credit",
            "effective_date": "2025-01-01", "legacy_usd_value": None,
        },
    },
    "ca_qc_pstc": {
        "min_total_budget": {
            "amount": 250_000, "currency": "CAD", "basis": "Minimum budget requirement",
            "source": "SODEC — Refundable Tax Credit for Film or Television Production Services",
            "effective_date": None, "legacy_usd_value": None,
        },
        "administrative_fee": {
            "amount": 500, "currency": "CAD", "basis": "SODEC application administrative fee",
            "source": "SODEC — Refundable Tax Credit for Film or Television Production Services",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "dk_production_rebate": {
        "annual_program_cap": {
            "amount": 125_000_000, "currency": "DKK", "basis": "Annual envelope for the 25% production rebate scheme",
            "source": "Slots- og Kulturstyrelsen (Danish Agency for Culture and Palaces), via Nordisk Film & TV Fond reporting",
            "effective_date": "2026-01-01", "legacy_usd_value": None,
        },
        "min_total_budget_animation": {
            "amount": 870_000, "currency": "DKK", "basis": "Minimum total budget, animation. Other formats are reported in EUR (film EUR 3,350,000; documentary EUR 536,000; TV series EUR 2,000,000 total and EUR 20,000/minute) — the sources mix currencies and are recorded verbatim.",
            "source": "Slots- og Kulturstyrelsen, via Nordisk Film & TV Fond / Cineuropa reporting",
            "effective_date": "2026-01-01", "legacy_usd_value": None,
        },
    },
    "se_production_rebate": {
        "min_local_spend": {
            "amount": 4_000_000, "currency": "SEK", "basis": "Local Swedish production costs must exceed this amount",
            "source": "Tillväxtverket (Swedish Agency for Economic Growth)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "min_total_budget": {
            "amount": 30_000_000, "currency": "SEK", "basis": "Minimum overall project budget, feature (documentary SEK 10,000,000; drama series SEK 10,000,000/episode; docu series SEK 5,000,000/episode)",
            "source": "Tillväxtverket (Swedish Agency for Economic Growth)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "annual_program_cap": {
            "amount": 100_000_000, "currency": "SEK", "basis": "Annual envelope for the production rebate",
            "source": "Tillväxtverket (Swedish Agency for Economic Growth)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "jp_vipo_location_incentive": {
        "min_local_spend": {
            "amount": 200_000_000, "currency": "JPY", "basis": "Minimum production costs in Japan for eligibility",
            "source": "METI / VIPO — Location Incentive Program for International Large-scale Audiovisual Productions",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 1_000_000_000, "currency": "JPY", "basis": "Upper limit of subsidy per project",
            "source": "METI / VIPO — Location Incentive Program for International Large-scale Audiovisual Productions",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "ch_pics_national_rebate": {
        "min_total_budget": {
            "amount": 2_500_000, "currency": "CHF", "basis": "Minimum project budget for a co-production",
            "source": "PICS — Production Incentive Switzerland (Federal Office of Culture)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "min_local_spend": {
            "amount": 500_000, "currency": "CHF", "basis": "Minimum billable costs. Fiction-specific: CHF 1,200,000 eligible Swiss costs (majority co-production) or CHF 300,000 (minority).",
            "source": "PICS — Production Incentive Switzerland (Federal Office of Culture)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 600_000, "currency": "CHF", "basis": "Ceiling of the rebate per project",
            "source": "PICS — Production Incentive Switzerland (Federal Office of Culture)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "mx_federal_film_incentive_2026": {
        "min_local_spend": {
            "amount": 40_000_000, "currency": "MXN", "basis": "Minimum spend, feature films and narrative/animation series (documentary MXN 20,000,000; animation/VFX/post-only MXN 5,000,000)",
            "source": "Presidential Decree and Guidelines, Diario Oficial de la Federación 2026-03-30 (via Baker McKenzie analysis)",
            "effective_date": "2026-03-31", "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 40_000_000, "currency": "MXN", "basis": "Cap per project",
            "source": "Presidential Decree and Guidelines, Diario Oficial de la Federación 2026-03-30 (via Baker McKenzie analysis)",
            "effective_date": "2026-03-31", "legacy_usd_value": None,
        },
        "programme_envelope": {
            "amount": 400_000_000, "currency": "MXN", "basis": "Total programme envelope distributed from entry into force until 2030-09-30 (not an annual appropriation)",
            "source": "Presidential Decree and Guidelines, Diario Oficial de la Federación 2026-03-30 (via Baker McKenzie analysis)",
            "effective_date": "2026-03-31", "legacy_usd_value": None,
        },
    },
    "ca_ab_fttc": {
        "min_total_budget": {
            "amount": 499_999, "currency": "CAD", "basis": "Minimum total production costs, Canadian funds excluding GST (published verbatim as 499,999)",
            "source": "Government of Alberta — Film and Television Tax Credit Program Guidelines",
            "effective_date": "2024-06-07", "legacy_usd_value": None,
        },
    },
    "ee_film_estonia_rebate": {
        "min_local_spend": {
            "amount": 200_000, "currency": "EUR", "basis": "Minimum Estonian spend, feature film (feature documentary/animation EUR 70,000; animation series and high-end TV drama EUR 70,000 per series). Post-production uses a separate rate ladder: EUR 30,000→20%, EUR 50,000→25%, EUR 80,000→30%.",
            "source": "Estonian Film Institute — Film Estonia guidelines",
            "effective_date": None, "legacy_usd_value": None,
        },
        "min_total_budget": {
            "amount": 1_000_000, "currency": "EUR", "basis": "Minimum overall budget, feature film (documentary EUR 200,000; animation EUR 250,000; animation series EUR 500,000; high-end TV drama EUR 200,000 per episode)",
            "source": "Estonian Film Institute — Film Estonia guidelines",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "rs_film_commission_cash_rebate": {
        "min_local_spend": {
            "amount": 300_000, "currency": "EUR", "basis": "Minimum qualifying Serbian spend, feature films and TV films (TV series EUR 150,000 per episode; animation/AV post-production/special-purpose EUR 150,000; documentary and TV programmes EUR 50,000)",
            "source": "Film Center Serbia (Filmski centar Srbije)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "enhanced_rate_threshold": {
            "amount": 5_000_000, "currency": "EUR", "basis": "Serbian spend at or above this level qualifies for the 30% rate instead of the 25% base",
            "source": "Film Center Serbia (Filmski centar Srbije)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "tw_bamid_rebate": {
        "min_local_spend": {
            "amount": 30_000_000, "currency": "TWD", "basis": "Minimum Taiwan production spend, feature films (reduced to TWD 3,000,000 if the director has won Best Director at Cannes, Venice, Berlin or the Academy Awards; TV drama series TWD 60,000,000, reduced to TWD 3,000,000 for International Emmy/Primetime Emmy/Seoul International Drama Awards Best Director winners)",
            "source": "Bureau of Audiovisual and Music Industry Development (BAMID), Ministry of Culture — corroborated via Production Service Network and Mbrella Films industry summaries",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 30_000_000, "currency": "TWD", "basis": "Maximum rebate, feature films (TV drama series TWD 20,000,000)",
            "source": "Bureau of Audiovisual and Music Industry Development (BAMID), Ministry of Culture — corroborated via Production Service Network and Mbrella Films industry summaries",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "ph_fdcp_flip": {
        "min_local_spend": {
            "amount": 20_000_000, "currency": "PHP", "basis": "Minimum Qualified Philippine Production Expenditure (QPPE), live-action and animated feature films (documentaries PHP 8,000,000; TV/VOD series PHP 3,000,000 per episode, minimum 8 episodes, i.e. PHP 24,000,000 aggregate)",
            "source": "Film Development Council of the Philippines (FDCP), Film Philippines Office (FPO) — official FLIP program page",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 25_000_000, "currency": "PHP", "basis": "Maximum rebate at the 20% base rate (rises to PHP 30,000,000 if the project passes the Cultural Bonus merit test, raising the rate to 25%)",
            "source": "Film Development Council of the Philippines (FDCP), Film Philippines Office (FPO) — official FLIP program page",
            "effective_date": None, "legacy_usd_value": None,
        },
        "cultural_bonus_cap": {
            "amount": 30_000_000, "currency": "PHP", "basis": "Maximum rebate with the Cultural Bonus (25% rate), distinct from the PHP 25,000,000 base-rate (20%) cap",
            "source": "Film Development Council of the Philippines (FDCP), Film Philippines Office (FPO) — official FLIP program page",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "cl_corfo_incentive": {
        "min_local_spend": {
            "amount": 2_000_000, "currency": "USD", "basis": "Minimum qualified spend in Chile — published in USD by the administering authorities (IFI Audiovisual targets foreign productions specifically; no CLP conversion involved)",
            "source": "Corfo / Ministerio de las Culturas, las Artes y el Patrimonio / Ministerio de Economia — Programa de Apoyo a Inversiones Audiovisuales de Alto Impacto (IFI Audiovisual)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 3_000_000, "currency": "USD", "basis": "Maximum rebate at the 30% base rate (regions outside Santiago Metropolitan Region qualify for 40% instead of 30%, on the same USD 3,000,000 project-level structure) — published in USD by the administering authorities",
            "source": "Corfo / Ministerio de las Culturas, las Artes y el Patrimonio / Ministerio de Economia — Programa de Apoyo a Inversiones Audiovisuales de Alto Impacto (IFI Audiovisual)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "annual_program_cap": {
            "amount": 2_168_000_000, "currency": "CLP", "basis": "Total program budget for the 2025 call cycle (paid out in CLP by the Chilean state even though rebate caps/min-spend are quoted in USD)",
            "source": "Ministerio de las Culturas, las Artes y el Patrimonio — official IFI Audiovisual 2025 second-call announcement",
            "effective_date": "2025-09-05", "legacy_usd_value": None,
        },
    },
    "us_ky_keiia": {
        "min_local_spend": {
            "amount": 250_000, "currency": "USD", "basis": "Minimum qualifying Kentucky expenditure, feature films (documentaries USD 20,000) — figure carried forward from pre-SB-324 sources (shamelstudio.com/revenue.ky.gov listing); not independently re-confirmed against the 2026-07-15 regulatory rewrite (307 KAR 1:080E) in the text retrieved",
            "source": "Kentucky Cabinet for Economic Development / Kentucky Dept of Revenue (pre-2026-SB-324 figure, unconfirmed against the current regulation text)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "annual_program_cap": {
            "amount": 75_000_000, "currency": "USD", "basis": "Annual program cap — independently confirmed current via FilmKentucky.org (\"$75 Million Available Annually\"), the Kentucky Film Office's own promotional site, fetched 2026-07-26",
            "source": "FilmKentucky.org (Kentucky Film Office)",
            "effective_date": "2026-07-26", "legacy_usd_value": None,
        },
        "application_fee_range": {
            "amount": 1_000, "currency": "USD", "basis": "Application fee, tiered USD 250-1,000 by project budget (ceiling of the range recorded here); plus a 0.5% administrative fee on estimated incentives sought (minimum USD 500) and a nonrefundable USD 2,000 agreement fee",
            "source": "307 KAR 1:080E (Kentucky Entertainment Incentive Program regulation, emergency amendment eff. 2026-07-15) — Kentucky Legislative Research Commission",
            "effective_date": "2026-07-15", "legacy_usd_value": None,
        },
    },
    "us_md_film_production_activity_credit": {
        "min_local_spend": {
            "amount": 250_000, "currency": "USD", "basis": "Minimum authorized direct costs incurred in Maryland, standard productions (Maryland Small Film category: USD 25,000)",
            "source": "Maryland Dept of Commerce (commerce.maryland.gov/fund/film-production-activity-tax-credit); confirmed independently via Tax-General Article Sec. 10-730 (law.justia.com)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "annual_program_cap": {
            "amount": 12_000_000, "currency": "USD", "basis": "FY2027 total tax credits available for certification, first-come-first-served",
            "source": "Maryland Dept of Commerce (commerce.maryland.gov/fund/film-production-activity-tax-credit)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "small_film_cap": {
            "amount": 125_000, "currency": "USD", "basis": "Maximum credit for the separate 'Maryland Small Film' category (min spend USD 25,000; independently-owned applicant, <=25 full-time employees, not dominant in its field, organized/active in Maryland 3+ months; exempt from the independent CPA-audit requirement)",
            "source": "Maryland Dept of Commerce (commerce.maryland.gov/fund/film-production-activity-tax-credit)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "cz_film_incentive": {
        "min_local_spend": {
            "amount": 15_000_000, "currency": "CZK", "basis": "Minimum eligible spend, feature and animated films (documentaries CZK 2,000,000; TV series CZK 8,000,000 per episode; animated series/digital production CZK 1,000,000 per episode)",
            "source": "Statni fond audiovize (Czech Film Fund) — official production-incentives page",
            "effective_date": None, "legacy_usd_value": None,
        },
        "annual_program_cap": {
            "amount": 450_000_000, "currency": "CZK", "basis": "Maximum rebate per project (eligible costs additionally capped at 80% of total budget)",
            "source": "Statni fond audiovize (Czech Film Fund) — official production-incentives page",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "dk_production_rebate": {
        "annual_program_cap": {
            "amount": 125_000_000, "currency": "DKK", "basis": "Total annual envelope across both sub-schemes: Live Action Scheme DKK 100,000,000/year, Animated Films and Series Scheme DKK 25,000,000/year",
            "source": "Slots- og Kulturstyrelsen (Danish Agency for Culture and Palaces) — official scheme page",
            "effective_date": "2026-01-01", "legacy_usd_value": None,
        },
    },
    "fj_film_rebate": {
        "min_local_spend": {
            "amount": 250_000, "currency": "FJD", "basis": "Minimum Total Fiji Expenditure (TFE)",
            "source": "Film Fiji (Fijian government film promotion authority) — official 20% Film Tax Rebate page",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 4_000_000, "currency": "FJD", "basis": "Maximum rebate per production",
            "source": "Film Fiji (Fijian government film promotion authority) — official 20% Film Tax Rebate page",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "sa_film_commission_rebate": {
        "min_local_spend": {
            "amount": 750_000, "currency": "SAR", "basis": "Minimum qualifying spend, feature films (documentaries/animation SAR 187,000)",
            "source": "Saudi Film Commission (SFC), Ministry of Culture — official Film Saudi incentive program page",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "us_mn_film_production_credit": {
        "min_local_spend": {
            "amount": 1_000_000, "currency": "USD", "basis": "Minimum eligible production costs incurred within any 12 consecutive months",
            "source": "Minnesota Dept of Revenue (revenue.state.mn.us/film-production-credit)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "annual_program_cap": {
            "amount": 25_000_000, "currency": "USD", "basis": "Maximum annual program allocation, first-come-first-served",
            "source": "Minnesota Dept of Revenue (revenue.state.mn.us/film-production-credit)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "at_fisa_plus": {
        "min_local_spend": {
            "amount": 150_000, "currency": "EUR", "basis": "Minimum Austrian spend, fiction/feature films (documentaries EUR 80,000; animation/VFX/film-music productions EUR 25,000) — supersedes the DISCOVERY catalog's stale EUR 600,000 figure",
            "source": "Industry aggregators (needafixer.com, progressiveproductions.eu) corroborating the current FISA+ scheme; not yet independently confirmed via a direct official fisaplus.com fetch (DNS unreachable at access time)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    # ── Programs published natively in USD (NO conversion involved; the USD
    #    field IS the authoritative statutory value for these) ──────────────
    "mu_edb_incentive": {
        "min_local_spend": {
            "amount": 1_000_000, "currency": "USD", "basis": "Minimum QPE, feature film — published in USD by the authority itself",
            "source": "Economic Development Board Mauritius — Film Rebate Scheme",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "il_foreign_production_fund": {
        "min_local_spend": {
            "amount": 50_000, "currency": "USD", "basis": "Eligible production costs from USD 50,000 — published in USD by the authority itself",
            "source": "Israel Ministry of Economy & Industry / NFCT",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "us_pr_film_incentives_act": {
        "min_local_spend": {
            "amount": 50_000, "currency": "USD", "basis": "Minimum spend per project (short films USD 25,000) — Puerto Rico uses USD as its own currency; no conversion involved",
            "source": "DDEC / Puerto Rico Film Commission, under Act 60-2019 (Puerto Rico Incentives Code)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "post_production_only_cap": {
            "amount": 500_000, "currency": "USD", "basis": "Maximum credit for post-production-only projects — a format-specific ceiling, not a general per-project cap",
            "source": "DDEC / Puerto Rico Film Commission, under Act 60-2019 (Puerto Rico Incentives Code)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "us_wa_motion_picture_competitiveness": {
        "min_local_spend": {
            "amount": 500_000, "currency": "USD", "basis": "Minimum qualified in-state spend, feature films (episodic USD 300,000 per episode; commercials USD 150,000) — published in USD by the authority itself",
            "source": "Washington Filmworks — Production Incentive Program Guidelines & Criteria (rev. 2025-06-24)",
            "effective_date": "2025-06-24", "legacy_usd_value": None,
        },
        "annual_program_cap": {
            "amount": 15_000_000, "currency": "USD", "basis": "Annual funding pool, renewing every January — published in USD by the authority itself",
            "source": "Washington Filmworks — Production Incentive Program Fact Sheet (rev. 2025-06-24)",
            "effective_date": "2025-06-24", "legacy_usd_value": None,
        },
    },
    "us_nc_film_entertainment_grant": {
        "min_local_spend": {
            "amount": 1_500_000, "currency": "USD", "basis": "Minimum qualified spend, feature-length films (MOW/streaming movies USD 500,000; TV/streaming series USD 500,000 per-episode average; commercials USD 250,000) — published in USD by the authority itself",
            "source": "North Carolina Department of Commerce / NC Film Office",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_project_cap": {
            "amount": 7_000_000, "currency": "USD", "basis": "Cap for feature-length films incl. made-for-TV/streaming movies (TV/streaming series USD 15,000,000 per season; commercials USD 250,000) — published in USD by the authority itself",
            "source": "North Carolina Department of Commerce / NC Film Office",
            "effective_date": None, "legacy_usd_value": None,
        },
        "annual_program_cap": {
            "amount": 31_000_000, "currency": "USD", "basis": "Recurring annual allocation per North Carolina fiscal year (1 July - 30 June) — published in USD by the authority itself",
            "source": "North Carolina Department of Commerce / NC Film Office",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "us_ma_film_tax_credit": {
        "min_local_spend": {
            "amount": 50_000, "currency": "USD", "basis": "Total Massachusetts production expenses in a consecutive 12-month period, gating the payroll credit — published in USD by the authority itself",
            "source": "Massachusetts Department of Revenue (DOR) / Massachusetts Film Office",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_person_exclusion": {
            "amount": 1_000_000, "currency": "USD", "basis": "Payments to an employee totalling this amount or more are EXCLUDED from qualifying payroll entirely — published in USD by the authority itself",
            "source": "Massachusetts Department of Revenue (DOR)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "us_pa_film_production_credit": {
        "annual_program_cap": {
            "amount": 100_000_000, "currency": "USD", "basis": "Statutory annual cap — published in USD by the authority itself. Distinct from the fiscal-year allocation (reported at USD 60,000,000), against which a 20% per-award limit yields a USD 12,000,000 maximum single award.",
            "source": "PA Department of Community & Economic Development (DCED), PA Film Office",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "us_tx_miip": {
        "min_local_spend": {
            "amount": 250_000, "currency": "USD", "basis": "Minimum eligible Texas spend for film/TV and reality (per season for episodic series); commercials USD 100,000 — published in USD by the authority itself",
            "source": "Office of the Texas Governor — Texas Film Commission (TMIIIP)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
    "us_il_film_production_services_credit": {
        "min_local_spend": {
            "amount": 100_000, "currency": "USD", "basis": "Minimum Illinois Production Spending for projects 30 minutes or over (USD 50,000 under 30 minutes) — published in USD by the authority itself",
            "source": "Illinois Department of Commerce and Economic Opportunity (DCEO)",
            "effective_date": None, "legacy_usd_value": None,
        },
        "per_person_cap": {
            "amount": 500_000, "currency": "USD", "basis": "Salary cap per worker (resident and non-resident) — published in USD by the authority itself",
            "source": "Illinois Department of Commerce and Economic Opportunity (DCEO)",
            "effective_date": None, "legacy_usd_value": None,
        },
    },
}


def get_statutory_amounts(program_slug: str) -> dict[str, dict]:
    """Authoritative original-currency statutory amounts for a program.

    Returns {} when this program publishes no monetary threshold, or
    publishes natively in USD and is already fully represented on the
    profile. Where a value here conflicts with the profile's USD field,
    THIS is the legal source of truth — the USD field is a legacy derived
    convenience value retained for backward compatibility only.
    """
    return STATUTORY_AMOUNTS_ORIGINAL_CURRENCY.get(program_slug, {})


def profiles_with_legacy_currency_conversions() -> dict[str, list[str]]:
    """Audit helper: program_slug -> [field names] whose USD value is a
    legacy conversion of a non-USD statutory amount. Used by the currency
    compliance test and by the next phase's normalization work."""
    out: dict[str, list[str]] = {}
    for slug, fields in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY.items():
        converted = [
            name for name, rec in fields.items()
            if rec.get("currency") != "USD" and rec.get("legacy_usd_value") is not None
        ]
        if converted:
            out[slug] = sorted(converted)
    return out


register(ProgramRequirementsProfile(
    program_slug="ca_bc_pstc", jurisdiction_code="CA-BC",
    cultural_test_required=False,    # PUBLISHED ABSENCE: "There is no Canadian content requirement." (verbatim, official)
    local_entity_required=None,      # see notes: the official page states no BC-establishment requirement, but accreditation is defined in the Income Tax Act, which was not read in this pass
    preapproval_mandatory=True,      # pre-certification form due within 120 days of the first accredited BC labour expenditure
    refundable=True,                 # "The credit is fully refundable, but must first be applied against total income tax payable."
    transferable=False,              # refundable corporate income tax credit; no transfer mechanism published
    annual_program_cap_usd=None,     # PUBLISHED ABSENCE: no annual or per-project cap appears on the official page
    per_project_cap_usd=None,        # PUBLISHED ABSENCE (same)
    application_deadline=TimingFact(
        value="Pre-certification form must be filed within 120 days of the first accredited B.C. "
              "labour expenditure (exemption for productions starting 2025-10-20 or later); the "
              "accreditation certificate application must be submitted to Creative BC within 12 "
              "months of the tax year end",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="Production services tax credit — Province of British Columbia (official)",
        source_url="https://www2.gov.bc.ca/gov/content/taxes/income-taxes/corporate/credits/production-services",
        issuing_authority="Province of British Columbia (Ministry of Finance); Creative BC (accreditation)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Official Province of BC page, fetched directly 2026-07-26. Refundable corporate "
              "income tax credit for accredited production corporations producing accredited film "
              "or video productions in B.C.; available to BOTH domestic and foreign producers. "
              "PUBLISHED ABSENCES recorded as such under the canonical doctrine (silence is not a "
              "restriction): 'There is no Canadian content requirement' (verbatim) -> "
              "cultural_test_required=False; no annual cap and no per-project cap appear on the "
              "official page -> both left unset with this note rather than invented. RATES (per "
              "the official page): production services 36%; regional +6%; distant location +6%; "
              "DAVE (digital animation, visual effects and post-production) +16%; major production "
              "+2%. REAL DEADLINES: pre-certification within 120 days of the first accredited B.C. "
              "labour expenditure (with an exemption for productions starting on/after "
              "2025-10-20), and the accreditation certificate application to Creative BC within 12 "
              "months of tax year end. FEES: application fees rise for productions beginning "
              "principal photography after 2024-12-31 (CAD 19,000 accreditation; CAD 5,000 major "
              "production certificate). NOT DETERMINED IN THIS PASS: the statutory minimum "
              "production-cost thresholds that make a production 'accredited' are defined in the "
              "Income Tax Act (British Columbia) rather than on this page, which was the source "
              "read here — min_local_spend/min_total_budget are therefore left unset and NOT "
              "guessed. A secondary aggregator asserted 'no minimum spend'; that was NOT relied on, "
              "because it conflicts with the existence of an accredited-production definition and "
              "could not be confirmed against the governing statute in this pass. Likewise "
              "local_entity_required is left None: the official page states no BC-establishment "
              "requirement, but 'accredited production corporation' is a statutory term whose full "
              "definition was not read here — recording False would overstate what was verified.",
    ),
    additional_facts={
        "rates_official": "Production services 36%; regional +6%; distant location +6%; DAVE +16%; major production +2% (Province of BC official page).",
        "no_canadian_content": "Official text: 'There is no Canadian content requirement.' Available to domestic and foreign producers alike.",
        "pre_certification_deadline": "Within 120 days of the first accredited B.C. labour expenditure; exemption for productions starting on/after 2025-10-20.",
        "accreditation_deadline": "Accreditation certificate application to Creative BC within 12 months of tax year end.",
        "application_fees_cad": "CAD 19,000 accreditation and CAD 5,000 major production certificate, for productions beginning principal photography after 2024-12-31 (authoritative original currency).",
        "caps": "No annual cap and no per-project cap are published on the official Province of BC page.",
        "open_item": "Statutory minimum production-cost thresholds for 'accredited production' are set in the Income Tax Act (British Columbia); not read in this pass and deliberately not guessed.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="us_il_film_production_services_credit", jurisdiction_code="US-IL",
    cultural_test_required=False,      # US state credit — no content/cultural test published
    min_local_spend_usd=100_000.0,     # USD is the authority's own currency: $100,000 for projects 30 min or over ($50,000 under 30 min)
    per_person_cap_usd=500_000.0,      # salary cap per worker (resident and non-resident alike)
    preapproval_mandatory=True,        # application to DCEO before production
    refundable=False,                  # not refundable — monetized by transfer instead
    transferable=True,                 # "fully transferable" — sellable on the secondary market
    transfer_approval_required=None,   # transfer mechanism confirmed; a separate approval step is not published in the sources reviewed
    annual_program_cap_usd=None,       # None published in the DCEO materials reviewed
    evidence=EvidenceRecord(
        source_title="Illinois Film Production Services Tax Credit — Rules/Requirements & Fact Sheet (DCEO)",
        source_url="https://dceo.illinois.gov/whyillinois/film/filmtaxcredit/rulesandrequirements.html",
        issuing_authority="Illinois Department of Commerce and Economic Opportunity (DCEO)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="DCEO official programme pages and Fact Sheet. Minimum Illinois Production Spending: "
              "USD 50,000 for projects under 30 minutes; USD 100,000 for projects 30 minutes or "
              "over (min_local_spend_usd records the 30-min-or-over threshold; the short-form "
              "threshold is in additional_facts). USD is the governing authority's own currency — "
              "no conversion involved. Rates (2025 General Assembly expansion): 35% of qualified "
              "Illinois spending including post-production and Illinois-resident salaries up to "
              "USD 500,000 per worker; 30% on limited non-resident salaries up to USD 500,000 per "
              "worker. NON-RESIDENT LABOUR IS CAPPED BY HEADCOUNT: eligible for up to 13 "
              "non-resident employees other than actors, plus 4-6 non-resident actors depending on "
              "project budget — a real published structural limit, recorded in additional_facts "
              "because the schema has no headcount field. MONETIZATION: the credit is fully "
              "transferable and may be sold on the secondary market, which is how a production "
              "without Illinois tax liability realises value — recorded transferable=True / "
              "refundable=False. No annual programme cap and no per-project cap appear in the DCEO "
              "materials reviewed.",
    ),
    additional_facts={
        "min_spend_short_form_usd": "USD 50,000 minimum Illinois Production Spending for projects under 30 minutes (USD 100,000 for 30 minutes or over).",
        "rates": "35% of qualified Illinois spending incl. post-production and Illinois-resident salaries up to USD 500,000/worker; 30% on limited non-resident salaries up to USD 500,000/worker.",
        "non_resident_headcount_limit": "Up to 13 non-resident employees other than actors, plus 4-6 non-resident actors depending on project budget.",
        "monetization": "Fully transferable; sellable on the secondary market by productions without Illinois tax liability.",
        "caps": "No annual programme cap and no per-project cap published in the DCEO materials reviewed.",
        "contact": "filmtaxcredit@illinois.gov (DCEO).",
    },
))

register(ProgramRequirementsProfile(
    program_slug="ca_qc_pstc", jurisdiction_code="CA-QC",
    local_entity_required=True,        # must be a Québec-incorporated corporation with an establishment in Québec
    cultural_test_required=False,      # production-SERVICES credit — no Québec-content test (contrast the separate Québec-content credit)
    preapproval_mandatory=True,        # SODEC Approval Certificate + Advance Ruling before claiming
    refundable=True,                   # "This tax credit is refundable."
    transferable=False,
    per_project_cap_usd=None,          # None published for the base credit; the CASE animation/VFX bonus is expressly uncapped per project
    evidence=EvidenceRecord(
        source_title="Refundable Tax Credit for Film or Television Production Services — SODEC (fact sheet, March 2026)",
        source_url="https://sodec.gouv.qc.ca/english/credit-film-production-services/",
        issuing_authority="Société de développement des entreprises culturelles (SODEC), Québec; Revenu Québec",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="SODEC official programme page and March 2026 fact sheet. 25% REFUNDABLE credit on "
              "qualified expenditures for services rendered in Québec on an eligible production; "
              "the base applies to ALL-SPEND production costs (qualified labour plus qualified "
              "property costs), not labour alone. An additional 16% CASE bonus applies to "
              "animation / special-effects / chroma-key qualified labour, and that bonus is "
              "expressly WITHOUT a per-project cap — a published absence of a restriction. "
              "ELIGIBILITY: a Québec-incorporated corporation providing production services — "
              "either a domestic service company working for an international production, or an "
              "independent producer with substantial Québec spend. PROCESS: application to SODEC "
              "with a CAD 500 administrative fee; obtain an Approval Certificate from SODEC and "
              "apply for an Advance Ruling. Minimum budget CAD 250,000 — stated in CAD by the "
              "authority, so it is recorded in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY rather than "
              "FX-converted into the USD field. No cultural/Québec-content test applies to this "
              "SERVICES credit (a separate Québec-content credit exists and is a different "
              "programme).",
    ),
    additional_facts={
        "min_budget_cad": "CAD 250,000 minimum budget (authoritative original currency).",
        "administrative_fee_cad": "CAD 500 application fee payable to SODEC.",
        "case_bonus": "Additional 16% CASE bonus on animation / special-effects / chroma-key qualified labour, expressly with no per-project cap.",
        "base_is_all_spend": "The 25% base applies to all-spend production costs (qualified labour + qualified property), not labour only.",
        "process": "SODEC Approval Certificate plus an Advance Ruling application.",
        "distinct_programme": "Separate from the Québec-content production tax credit, which does apply a content test.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="sa_film_commission_rebate", jurisdiction_code="SA",
    local_entity_required=True,        # international companies must have a local entity or a Saudi partner
    preapproval_mandatory=True,        # application + approval via the Film Saudi platform before production
    cultural_test_required=False,      # confirmed directly, second fetch this session: no distinct cultural/values TEST — content vetting runs through Script Content Clearance + a Filming Non-Objection Certificate instead (see additional_facts)
    min_local_spend_usd=200_000.0,     # SAR 750,000 feature-film threshold — confirmed this session (documentary/animation SAR 187,000 / ~$50,000, see additional_facts)
    min_shoot_days=5,                  # confirmed this session: minimum 5 filming days with the main production unit
    refundable=True,                   # cash rebate paid out (the programme's "non-repayable grant" framing)
    transferable=False,
    allocation_type=AllocationType.DISCRETIONARY,  # selective review of script/treatment/mood board/schedule; not an automatic entitlement
    per_project_cap_usd=None,          # no financial cap referenced in the materials reviewed
    evidence=EvidenceRecord(
        source_title="Film Saudi Incentive Program — Saudi Film Commission (Ministry of Culture)",
        source_url="https://film.sa/incentive-programs/",
        issuing_authority="Saudi Film Commission (SFC), Ministry of Culture, Kingdom of Saudi Arabia",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY BASELINE FIRST (Stage B priority audit, 2026-07-26): this profile was "
              "already PRIMARY_VERIFIED going into this session, built from an earlier direct fetch "
              "of this same film.sa page. Re-fetched the same page this session specifically to "
              "close the two items its own prior notes had flagged as open (minimum qualifying "
              "spend not stated; deliberately not guessed) and to resolve an internal inconsistency "
              "discovered against the rate-rule layer (program_rate_rules_worldwide.py's SA_DOCTRINE "
              "carried requires_cultural_test=True, inherited from the old DISCOVERY catalog's "
              "undifferentiated 'content restrictions apply' note, while this profile had already "
              "reasoned its way to False). RATE CHANGE (carried forward, unchanged): launched at up "
              "to 40% of eligible expenditure, increased to up to 60% as of May 2026 — matches this "
              "repository's rate rules. ELIGIBILITY (carried forward, unchanged): open to Saudi and "
              "international companies; international applicants need a local entity or Saudi "
              "partner; government/quasi-government/state-owned entities are expressly excluded. "
              "NEWLY CONFIRMED — MINIMUM SPEND (closes the profile's own prior open item): SAR "
              "750,000 (~$200,000) for feature films; SAR 187,000 (~$50,000) for documentaries and "
              "animation — a genuine per-format structure, not a single figure. NEWLY CONFIRMED — "
              "SHOOT DAYS: minimum 5 filming days with the main production unit. CULTURAL-TEST "
              "RECONCILIATION (resolves the rate-rule contradiction): the page confirms there is NO "
              "distinct cultural/values test separate from the general production-quality review. "
              "Content vetting instead runs through two SPECIFICALLY NAMED gates — 'Script Content "
              "Clearance from Film Commission' and a 'Filming Non-Objection Certificate' — both "
              "required before approval. This is a regulatory content-clearance/censorship mechanism "
              "(comparable to a permit or classification gate), not a cultural test in the "
              "points-based or qualitative-artistic-merit sense used elsewhere in this registry "
              "(e.g. Finland's qualitative artistic-values criterion, Lithuania's 8-point scored "
              "test) — cultural_test_required=False is therefore the correct, deliberate reading, "
              "and the rate rule's prior True has been corrected to match (propagated to "
              "program_rate_rules_worldwide.py and jurisdiction_comparison.py, not left isolated in "
              "this profile alone). NO FINANCIAL CAP is referenced in the materials reviewed "
              "(unchanged). Specific criteria for how content-clearance decisions are made, and "
              "whether the 60% rate varies by expenditure category, remain undisclosed publicly — "
              "not guessed.",
    ),
    additional_facts={
        "rate_history": "Launched at up to 40% of eligible expenditure; increased to up to 60% as of May 2026.",
        "local_partner_requirement": "International production companies require a local entity or a Saudi partner.",
        "express_exclusions": "Government, quasi-government, state-owned entities and institutions are expressly ineligible.",
        "min_spend_by_format_sar": "SAR 750,000 (~$200,000) feature films; SAR 187,000 (~$50,000) documentaries and animation.",
        "min_shoot_days": "Minimum 5 filming days with the main production unit.",
        "content_clearance_gates": "Script Content Clearance from Film Commission and a Filming Non-Objection Certificate are both required before approval -- a regulatory content-clearance mechanism, not a points-based or qualitative cultural test.",
        "application_package": "Proof of financial backing, mood board, cast and crew list, script in English AND Arabic, film treatment (logline/synopsis/treatment), production schedule on the Commission's template.",
        "cap": "No financial cap referenced in the materials reviewed.",
        "open_item": "Specific content-clearance decision criteria and whether the 60% rate varies by expenditure category remain undisclosed publicly; not guessed.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="ae_ad_film_rebate", jurisdiction_code="AE-AD",
    local_entity_required=True,        # applicant must be a production/production-services company LICENSED by Abu Dhabi's Creative Media Authority
    preapproval_mandatory=True,        # content/script must be approved and documentation submitted before qualifying
    cultural_test_required=False,      # no cultural test; the 35%->50% uplift runs on a published sliding-scale POINTS system (different mechanism)
    refundable=True,                   # cashback rebate paid out
    transferable=False,
    evidence=EvidenceRecord(
        source_title="35%++ Cashback Rebate — Abu Dhabi Film Commission (Creative Media Authority)",
        source_url="https://www.film.gov.ae/35-rebate",
        issuing_authority="Abu Dhabi Film Commission (ADFC), Creative Media Authority (CMA), Abu Dhabi",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="ADFC official rebate pages. Baseline increased from 30% to 35%++ for all qualifying "
              "productions from 2025-01-01, with expanded qualifying formats, increased financial "
              "project caps and a streamlined process. ENHANCED TIER: up to 50% total cashback on "
              "qualifying Abu Dhabi spend, awarded against a published sliding-scale POINTS system "
              "— the 50% ceiling matches the rate already carried in this repository's rate rules, "
              "so the two sources agree. This points system is an uplift mechanism, NOT a cultural "
              "test, so cultural_test_required is recorded False and the points mechanism is "
              "described in additional_facts instead. ELIGIBILITY: the applicant must be a "
              "production company or production-services company LICENSED by the Creative Media "
              "Authority, and the content/script must be approved — a real licensing + content-"
              "approval gate. QUALIFYING FORMATS: feature films, television programmes/series, "
              "short-form content (short films, TVCs, music videos) and entertainment shows "
              "(reality, game shows). NOT DETERMINED IN THIS PASS: the specific minimum-spend "
              "threshold and the numeric project caps live in the ADFC Rebate Guidelines document "
              "rather than the summary pages read here; they are deliberately left unset rather "
              "than guessed.",
    ),
    additional_facts={
        "rate_structure": "Standard 35%++ baseline (raised from 30%, effective 2025-01-01); up to 50% total cashback via a published sliding-scale points system.",
        "licensing_requirement": "Applicant must be a production or production-services company licensed by Abu Dhabi's Creative Media Authority.",
        "content_approval": "The content/script of the production must be approved as part of eligibility.",
        "qualifying_formats": "Feature films; television programmes/series; short-form content (short films, TVCs, music videos); entertainment shows (reality, game shows).",
        "open_item": "Minimum qualifying spend and numeric project caps are set in the ADFC Rebate Guidelines document, not the summary pages reviewed; not guessed.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="dk_production_rebate", jurisdiction_code="DK",
    preapproval_mandatory=True,        # two annual calls; approval precedes the rebate
    cultural_test_required=True,       # explicit points-based "production and culture test"
    refundable=True,                   # reimbursement of eligible Danish production costs
    transferable=False,
    allocation_type=AllocationType.COMPETITIVE,  # two annual calls, points-ranked against a fixed DKK 125m annual envelope
    application_deadline=TimingFact(
        value="Two application rounds per sub-scheme each year; the second 2026 round opens late "
              "August 2026 with an expected deadline of 2026-09-24",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    evidence=EvidenceRecord(
        source_title="The Danish Production Incentive Scheme",
        source_url="https://slks.dk/english/work-areas/media/the-danish-production-incentive-scheme",
        issuing_authority="Slots- og Kulturstyrelsen (Danish Agency for Culture and Palaces)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST: this profile itself already flagged the exact gap "
              "closed here — its prior notes said 'the administrator's own final guidelines were "
              "not retrieved in this pass'. Direct fetch of slks.dk (the actual administering "
              "authority named throughout this profile) performed this session, upgrading to "
              "PRIMARY_VERIFIED. LEGAL BASIS (genuinely new, confirms the scheme is now in force "
              "rather than merely announced): the Act on the Production Incentive for Film and "
              "Series Production, and the Executive Order on the Production Incentive Scheme, both "
              "effective 2026-01-01. SUB-SCHEME STRUCTURE CONFIRMED (matches and corroborates the "
              "prior Nordisk Film & TV Fond figures rather than contradicting them): TWO distinct "
              "sub-schemes, each with its own annual budget and application rounds — the Live "
              "Action Scheme (feature films, fiction series, documentary films, documentary "
              "series; DKK 100,000,000/year) and the Animated Films and Series Scheme (DKK "
              "25,000,000/year) — together the DKK 125,000,000 total envelope already recorded. "
              "APPLICATION TIMING (genuinely new): the second 2026 application round opens late "
              "August 2026, expected deadline 2026-09-24. PREVIOUSLY-RECORDED FACTS NOT "
              "CONTRADICTED, CARRIED FORWARD: 25% reimbursement rate; the 70%-budget-confirmed + "
              "25%-international-financing test; the points-based production and culture test; the "
              "lead-producer track-record requirement; two annual calls (now confirmed as two calls "
              "PER sub-scheme). This specific slks.dk page did not restate the exact rate percentage "
              "or the per-format minimum-spend figures — those remain sourced from Nordisk Film & TV "
              "Fond / Cineuropa reporting and are NOT independently re-confirmed against this "
              "official page; recorded honestly rather than silently upgraded. CURRENCY CAUTION "
              "UNCHANGED: the Nordisk-sourced minimum budgets are reported in a MIX of EUR and DKK "
              "(EUR 3.35m film, EUR 536,000 documentary, DKK 870,000 animation, EUR 20,000/minute "
              "and EUR 2m total for TV series); recorded verbatim as reported, no USD field "
              "populated.",
    ),
    additional_facts={
        "annual_envelope_dkk": "DKK 125,000,000 per year (approximately EUR 17 million as reported).",
        "sub_scheme_structure": "Live Action Scheme (feature films, fiction series, documentary films/series): DKK 100,000,000/year. Animated Films and Series Scheme: DKK 25,000,000/year. Confirmed directly via slks.dk.",
        "legal_basis": "Act on the Production Incentive for Film and Series Production; Executive Order on the Production Incentive Scheme. Both effective 2026-01-01.",
        "min_budget_as_reported": "Film: EUR 3,350,000 total budget. Documentary: EUR 536,000. Animation: DKK 870,000. TV series: EUR 20,000 per minute and at least EUR 2,000,000 total. NOTE: sources report these in a mix of EUR and DKK; recorded verbatim as reported, not normalised. Not independently re-confirmed against slks.dk.",
        "financing_test": "At least 70% of the overall budget confirmed at application; at least 25% of financing sourced internationally.",
        "culture_test": (
            "RESOLVED 2026-08-19 (Worldwide Program Qualification Completion, Queue B): the "
            "Production and Cultural Test is a real, structured points-based system, not a vague "
            "qualitative standard. Confirmed via slks.dk's official FAQ page and independently "
            "converging industry reporting: the application is scored on THREE equally-weighted "
            "criteria totalling 300 points, of which the Culture Test itself accounts for a maximum "
            "of 100 points (the other two being the production budget size and the share of "
            "eligible expenditure spent in Denmark, each also scored up to 100). The Culture Test's "
            "own criteria include narrative/cultural elements (e.g. Danish setting, Danish-language "
            "story content) at stated proportions (e.g. 50% setting in Denmark, 50% story in "
            "Danish, per slks.dk's FAQ). GENUINE, DISCLOSED RESIDUAL: the exact point-by-criterion "
            "breakdown within the 100-point Culture Test was not found published as a standalone "
            "citable document -- slks.dk's own FAQ explicitly directs applicants to 'the Production "
            "and Cultural Test' template itself, and industry reporting confirms the editable "
            "XLSX version of the test 'becomes available when the application portal opens' -- i.e. "
            "the granular scoring template is distributed through the live grants portal rather "
            "than published as a standalone public document, a genuinely different limitation from "
            "Cyprus's 'withheld on request' pattern (this scheme itself only entered force "
            "2026-01-01; the template is portal-distributed by design, not withheld). Separate "
            "templates exist for feature films/fiction series vs. documentary films/series. Attempts "
            "to locate the exact table via the EU State Aid case register found only an unrelated "
            "Danish digital-games scheme decision (SA.45735/SA.52951) -- confirmed NOT applicable "
            "to this program and not used."
        ),
        "producer_track_record": "Lead producer must have a proven track record delivering widely distributed film, TV or animation content.",
        "application_rounds_2026": "Second 2026 round opens late August, expected deadline 2026-09-24.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="ae_dxb_dpip", jurisdiction_code="AE-DXB",
    preapproval_mandatory=True,        # Dubai Film Commission approval; permit regime applies
    cultural_test_required=False,      # no cultural test published for the Dubai rebate
    refundable=True,                   # cashback rebate paid out
    transferable=False,
    evidence=EvidenceRecord(
        source_title="Dubai production rebate (40% of qualifying spend) — Dubai Film and TV Commission",
        source_url="https://www.dubaifilmcommission.gov.ae/",
        issuing_authority="Dubai Film and TV Commission (Dubai Department of Economy and Tourism)",
        source_type=SourceType.SECONDARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Dubai raised its production rebate to 40% of qualifying Dubai spend (up from 30%), "
              "effective for projects commencing principal photography — or post-production work "
              "where the project is solely VFX/virtual-production focused — ON OR AFTER "
              "2026-06-01. The 40% figure matches the rate already carried in this repository's "
              "rate rules, so the two sources agree. Scope now expressly covers feature films, "
              "television series (drama, comedy, animation), documentaries, commercials and music "
              "videos, and the enhanced scheme adds VFX, virtual production and local hires as "
              "qualifying categories. GENUINELY UNDETERMINED — MINIMUM QUALIFYING SPEND: no "
              "threshold is published. Governing authority searched: Dubai Film and TV Commission "
              "(and Dubai DET). Documents reviewed: Commission/DET public materials plus "
              "professional commentary (Bird & Bird, KPMG UAE, Charles Russell Speechlys) and "
              "trade reporting. Reason it cannot presently be determined: the programme took "
              "effect 2026-06-01 and the granular guidelines are expressly still being finalised "
              "by the Commission — the threshold is legally material and indicated to exist, but "
              "is not yet published, which is the narrow case where Unknown is permitted. It is "
              "NOT recorded as 'none published', because the Commission signals guidelines are "
              "forthcoming rather than that no threshold exists. MARKED SECONDARY pending "
              "publication of the final guidelines. Note this is a DIFFERENT emirate and a "
              "different programme from AE-AD (Abu Dhabi, 35%++ up to 50%) — the two are recorded "
              "independently and neither is used to interpret the other.",
    ),
    additional_facts={
        "rate_history": "Raised to 40% of qualifying Dubai spend, up from 30%.",
        "effective_date": "Projects commencing principal photography (or post-production, where solely VFX/virtual-production focused) on or after 2026-06-01.",
        "qualifying_formats": "Feature films; television series incl. drama, comedy and animation; documentaries; commercials; music videos.",
        "expanded_scope": "The enhanced scheme adds VFX, virtual production and local hires as qualifying categories.",
        "unknown_min_spend": "Minimum qualifying spend not yet published — Commission guidelines expressly still being finalised as at 2026-07-26. Legally material and indicated to exist; recorded as a genuine Unknown, not as an absence.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_tx_miip", jurisdiction_code="US-TX",
    cultural_test_required=False,      # US state programme — no content/cultural test
    min_local_spend_usd=250_000.0,     # USD is the authority's own currency: film/TV and reality $250,000 (per season for episodic); commercials $100,000
    preapproval_mandatory=True,        # application MUST precede principal photography — late applicants are barred outright
    refundable=True,                   # cash grant paid out (not a tax credit)
    transferable=False,                # cash grant — no transfer mechanism
    application_deadline=TimingFact(
        value="Application package must be received by the Texas Film Commission no earlier than "
              "180 days and no later than 5:00 PM Central, 5 business days prior to the first day "
              "of principal photography. A production that has already begun principal "
              "photography cannot apply.",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="Texas Moving Image Industry Incentive Program (TMIIIP) — Production Incentives Overview",
        source_url="https://gov.texas.gov/film/page/incentives_overview",
        issuing_authority="Office of the Texas Governor — Texas Film Commission",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Official Office of the Texas Governor / Texas Film Commission programme pages. CASH "
              "GRANT (not a tax credit) of up to 31% of eligible Texas spending — matching the "
              "rate already in this repository's rate rules. MINIMUM ELIGIBLE TEXAS SPEND by "
              "format: film and television USD 250,000 (USD 250,000 PER SEASON for episodic "
              "series); reality television USD 250,000; commercials USD 100,000; animation and "
              "VFX USD 250,000 for film/TV and USD 100,000 for commercial projects. USD is the "
              "governing authority's own currency — no conversion involved. TEXAS RESIDENT "
              "REQUIREMENT (a real, published, hard eligibility gate): for film/TV, at least 35% "
              "of total paid CREW must be Texas residents AND at least 35% of total paid CAST "
              "(including paid extras) must be Texas residents; for commercial and reality "
              "projects, at least 35% of paid crew, cast and extras COMBINED. Recorded in "
              "additional_facts because the schema has no residency-percentage field. HARD "
              "APPLICATION WINDOW: no earlier than 180 days and no later than 5:00 PM Central, 5 "
              "business days before the first day of principal photography; a production that has "
              "already started principal photography is expressly barred from applying. No annual "
              "programme cap or per-project cap appears in the pages reviewed.",
    ),
    additional_facts={
        "min_spend_by_format_usd": "Film/TV USD 250,000 (per season for episodic series); reality TV USD 250,000; commercials USD 100,000; animation/VFX USD 250,000 film-TV and USD 100,000 commercial.",
        "texas_resident_requirement": "Film/TV: at least 35% of total paid crew AND at least 35% of total paid cast (incl. paid extras) must be Texas residents. Commercial/reality: at least 35% of paid crew, cast and extras combined.",
        "application_window": "No earlier than 180 days and no later than 5:00 PM Central, 5 business days before the first day of principal photography. Already-started productions are barred.",
        "grant_not_credit": "Up to 31% of eligible Texas spending, paid as a cash grant — not a tax credit, so no transfer or carry-forward mechanism applies.",
        "caps": "No annual programme cap and no per-project cap published in the pages reviewed.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="se_production_rebate", jurisdiction_code="SE",
    preapproval_mandatory=True,        # application through Tillväxtverket's portal during open windows, before support is granted
    cultural_test_required=False,      # no cultural test published; eligibility turns on spend thresholds and format
    refundable=True,                   # cash rebate paid out
    transferable=False,
    allocation_type=AllocationType.FIRST_COME_FIRST_SERVED,  # expressly first-come-first-served against a fixed annual envelope
    evidence=EvidenceRecord(
        source_title="Swedish audiovisual production rebate (25%) — Tillväxtverket (Swedish Agency for Economic Growth)",
        source_url="https://tillvaxtverket.se/",
        issuing_authority="Tillväxtverket (Swedish Agency for Economic Growth), on behalf of the Swedish Government",
        source_type=SourceType.SECONDARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="25% rebate on eligible Swedish costs, administered by Tillväxtverket with an annual "
              "envelope of SEK 100 million. ELIGIBLE FORMATS: feature films, documentaries, drama "
              "series and docu series. TWO DISTINCT THRESHOLDS, both real and both published: (a) "
              "local production costs incurred in Sweden must exceed SEK 4 million; and (b) the "
              "PROJECT's overall budget must be at least SEK 30 million (feature), SEK 10 million "
              "(documentary), SEK 10 million per episode (drama series), or SEK 5 million per "
              "episode (docu series). Production must take place fully or partly in Sweden. "
              "ELIGIBLE COSTS: salaries, goods and services necessary to carry out the production "
              "in Sweden. ALLOCATION: expressly first-come-first-served, capped at 25% of eligible "
              "costs; applications are filed through Tillväxtverket's online portal during open "
              "windows, and reporting notes rounds have historically closed the same day they "
              "opened because of demand — a real practical constraint for producers, recorded in "
              "additional_facts. All thresholds are stated in SEK and recorded in "
              "STATUTORY_AMOUNTS_ORIGINAL_CURRENCY; no USD field is populated. MARKED SECONDARY: "
              "figures come from Nordisk Film & TV Fond / Cineuropa / Screen reporting of the "
              "scheme; Tillväxtverket's own guideline document was not retrieved in this pass.",
    ),
    additional_facts={
        "min_local_spend_sek": "Local Swedish production costs must exceed SEK 4,000,000 (authoritative original currency).",
        "min_project_budget_sek": "SEK 30,000,000 feature; SEK 10,000,000 documentary; SEK 10,000,000 per episode drama series; SEK 5,000,000 per episode docu series.",
        "annual_envelope_sek": "SEK 100,000,000 per year.",
        "allocation_practice": "First-come-first-served; reporting notes application rounds have historically closed the same day they opened due to demand.",
        "eligible_costs": "Salaries, goods and services necessary to carry out the production in Sweden.",
        "evidence_caveat": "Tillväxtverket's own guideline document not retrieved in this pass; figures from Nordic industry reporting.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="sg_made_with_singapore_rebate", jurisdiction_code="SG",
    local_entity_required=True,        # production must be made locally or in partnership with a Singapore-based company
    preapproval_mandatory=True,        # IMDA grant scheme — application and approval precede support
    cultural_test_required=False,      # no cultural test published; qualification turns on local-resource spend
    refundable=True,                   # cash rebate / grant paid out
    transferable=False,
    allocation_type=AllocationType.DISCRETIONARY,  # IMDA grant assessed against scheme guidelines, not an automatic statutory entitlement
    evidence=EvidenceRecord(
        source_title="Made-with-Singapore cash rebate / Production Assistance Grant — Infocomm Media Development Authority (IMDA)",
        source_url="https://www.imda.gov.sg/-/media/imda/files/industry-development/grants-and-schemes/guidelines-for-p-assist-film_aug-2020.pdf",
        issuing_authority="Infocomm Media Development Authority (IMDA), Singapore",
        source_type=SourceType.SECONDARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="40% rebate on qualifying local Singapore spend, administered by IMDA, with an "
              "additional 10% available for subsequent projects that use local resources — the 40% "
              "base matches the rate already carried in this repository's rate rules. SUPPORTED "
              "FORMATS: feature films, TV series, documentaries and digital content produced "
              "locally or in partnership with Singapore-based companies (hence "
              "local_entity_required=True). QUALIFYING SPEND is expressly local-resource focused: "
              "hiring local staff, post-production, and rental of local facilities and equipment. "
              "GENUINELY UNDETERMINED FIELDS — minimum qualifying spend, annual budget cap, "
              "permitted number of projects, and application deadlines. Governing authority "
              "searched: IMDA (including the published Guidelines for Production Assistance Grant "
              "– Film). Documents reviewed: that IMDA guidelines PDF plus Reed Smith's "
              "international incentives survey and specialist fixer/industry guides. Reason they "
              "cannot presently be determined: the reviewed sources state directly that the "
              "Made-with-Singapore programme has vague published definitions in precisely these "
              "areas (annual budget caps, project counts, deadlines) — the values are legally "
              "material and indicated to exist but are not publicly specified, which is the narrow "
              "case where Unknown is permitted. They are NOT recorded as 'none published', because "
              "the scheme is a capped grant programme where such limits plainly operate "
              "administratively. MARKED SECONDARY pending direct confirmation from IMDA.",
    ),
    additional_facts={
        "rate_structure": "40% rebate on qualifying local Singapore spend; additional 10% for subsequent projects utilising local resources.",
        "supported_formats": "Feature films, TV series, documentaries and digital content, produced locally or in partnership with Singapore-based companies.",
        "qualifying_spend_focus": "Local-resource spend: hiring local staff, post-production, rental of local facilities and equipment.",
        "unknown_fields": "Minimum qualifying spend, annual budget cap, permitted project count and application deadlines are not publicly specified; reviewed sources expressly describe these definitions as vague. Recorded as genuine Unknowns, not absences.",
        "evidence_caveat": "Direct confirmation from IMDA required to resolve the undetermined fields.",
    },
))


# ══════════════════════════════════════════════════════════════════════════
# VERIFICATION LIFECYCLE  +  STRUCTURED UNKNOWN REASON CODES
# ══════════════════════════════════════════════════════════════════════════
# Engineering rule (Database Completion phase, 2026-07-26):
#
#   "Treat Requirements Profile completion and Evidence Verification as
#    separate lifecycle states. If authoritative administrator guidance has
#    not yet been retrieved, explicitly mark the profile as SECONDARY
#    VERIFIED rather than implicitly complete. Do not represent
#    secondary-source information as primary verified."
#
# A profile being POPULATED and a profile being PRIMARY-VERIFIED are
# independent facts. Previously the only signal was EvidenceRecord.source_type
# buried inside the record, which made "populated" read as "done". These
# helpers make the distinction first-class and queryable so a producer-facing
# consumer can surface it, and so the remaining primary-verification backlog
# is countable rather than anecdotal.
#
# Disclosure-only, exactly like the rest of this module: nothing here is
# consumed by any pricing/optimizer path.

class VerificationState(str, enum.Enum):
    PRIMARY_VERIFIED = "PRIMARY_VERIFIED"      # statute / regulation / official administrator document retrieved directly
    SECONDARY_VERIFIED = "SECONDARY_VERIFIED"  # populated from professional/trade/aggregator reporting; administrator's own guidance NOT yet retrieved
    UNVERIFIED = "UNVERIFIED"                  # no evidence record at all (should not occur for a registered profile)


class UnknownReasonCode(str, enum.Enum):
    """Why a legally material field could not be determined. Generic
    'UNKNOWN' is prohibited — every unknown must carry one of these, plus the
    authority searched, the documents reviewed, and why it is undeterminable."""
    UNKNOWN_PENDING_PRIMARY_GUIDANCE = "UNKNOWN_PENDING_PRIMARY_GUIDANCE"
    # The administrator has announced/operates the programme but has not yet
    # published the governing detail (e.g. a scheme that has just taken effect).

    UNKNOWN_PENDING_STATUTORY_INTERPRETATION = "UNKNOWN_PENDING_STATUTORY_INTERPRETATION"
    # The value is fixed in primary legislation that was not read in this pass,
    # or requires interpreting a statutory term rather than reading a figure.

    UNKNOWN_PENDING_IMPLEMENTING_REGULATIONS = "UNKNOWN_PENDING_IMPLEMENTING_REGULATIONS"
    # Enabling law exists but the implementing regulations/guidelines that
    # would fix the value have not been issued or published.


def verification_state(program_slug: str) -> VerificationState:
    """Evidence-verification lifecycle state for a populated profile.
    Independent of how many fields are filled in."""
    profile = _REGISTRY.get(program_slug)
    if profile is None or profile.evidence is None:
        return VerificationState.UNVERIFIED
    if profile.evidence.source_type == SourceType.PRIMARY:
        return VerificationState.PRIMARY_VERIFIED
    return VerificationState.SECONDARY_VERIFIED


def verification_summary() -> dict[str, int]:
    """Counts by lifecycle state across every registered profile."""
    out: dict[str, int] = {s.value: 0 for s in VerificationState}
    for slug in _REGISTRY:
        out[verification_state(slug).value] += 1
    return out


def profiles_awaiting_primary_verification() -> list[str]:
    """The primary-verification backlog: populated profiles whose
    administrator's own guidance has not yet been retrieved. These are NOT
    incomplete profiles — they are complete-but-secondary, a distinct state."""
    return sorted(
        slug for slug in _REGISTRY
        if verification_state(slug) is VerificationState.SECONDARY_VERIFIED
    )


# program_slug -> field_name -> structured justification for a genuine Unknown.
# Recorded ONLY where the field is legally material AND authoritative sources
# indicate the value exists AND it could not be determined. A field that is
# simply not restricted by the jurisdiction is NOT an unknown — under the
# Legal Interpretation Doctrine that is a published absence and is recorded on
# the profile itself, never here.
UNKNOWN_FIELD_REGISTER: dict[str, dict[str, dict]] = {
    "ae_dxb_dpip": {
        "min_local_spend": {
            "reason_code": UnknownReasonCode.UNKNOWN_PENDING_PRIMARY_GUIDANCE.value,
            "authority_searched": "Dubai Film and TV Commission; Dubai Department of Economy and Tourism (DET)",
            "documents_reviewed": "Commission and DET public materials; Bird & Bird UAE film-rebate analysis; "
                                  "KPMG UAE qualifying-production-expenditure guidance; Charles Russell Speechlys "
                                  "commentary; trade reporting on the 40% programme",
            "why_undeterminable": "The enhanced 40% programme took effect 2026-06-01 and the Commission states its "
                                  "granular guidelines are still being finalised. A minimum-spend threshold is "
                                  "indicated to exist but is not yet published.",
        },
    },
    "sg_made_with_singapore_rebate": {
        "min_local_spend": {
            "reason_code": UnknownReasonCode.UNKNOWN_PENDING_PRIMARY_GUIDANCE.value,
            "authority_searched": "Infocomm Media Development Authority (IMDA), Singapore",
            "documents_reviewed": "IMDA Guidelines for Production Assistance Grant – Film; Reed Smith international "
                                  "incentives survey; specialist Singapore fixer/industry guides",
            "why_undeterminable": "Reviewed sources state directly that the Made-with-Singapore scheme's published "
                                  "definitions are vague in this area; no threshold is publicly specified.",
        },
        "annual_program_cap": {
            "reason_code": UnknownReasonCode.UNKNOWN_PENDING_PRIMARY_GUIDANCE.value,
            "authority_searched": "Infocomm Media Development Authority (IMDA), Singapore",
            "documents_reviewed": "IMDA Guidelines for Production Assistance Grant – Film; Reed Smith incentives survey",
            "why_undeterminable": "Annual budget cap operates administratively but is not publicly specified; "
                                  "reviewed sources expressly describe the definition as vague.",
        },
        "application_deadline": {
            "reason_code": UnknownReasonCode.UNKNOWN_PENDING_PRIMARY_GUIDANCE.value,
            "authority_searched": "Infocomm Media Development Authority (IMDA), Singapore",
            "documents_reviewed": "IMDA Guidelines for Production Assistance Grant – Film; specialist industry guides",
            "why_undeterminable": "Application deadlines are not publicly specified; reviewed sources expressly "
                                  "describe the scheme's deadline definitions as vague.",
        },
    },
    "qa_screen_production_incentive": {
        "min_local_spend": {
            "reason_code": UnknownReasonCode.UNKNOWN_PENDING_PRIMARY_GUIDANCE.value,
            "authority_searched": "Film Committee, Media City Qatar; Doha Film Institute",
            "documents_reviewed": "Doha Film Institute QSPI launch press release and PDF; Screen Daily, Deadline and "
                                  "Screen Global Production coverage of the programme launch; Qatar fixer guides",
            "why_undeterminable": "QSPI was announced in late 2025 with applications opening Q2 2026; the Film "
                                  "Committee's detailed programme guidelines are not yet published, so no minimum "
                                  "qualifying spend has been stated by the administrator.",
        },
    },
    "ca_bc_pstc": {
        "min_total_budget": {
            "reason_code": UnknownReasonCode.UNKNOWN_PENDING_STATUTORY_INTERPRETATION.value,
            "authority_searched": "Province of British Columbia (Ministry of Finance); Creative BC",
            "documents_reviewed": "Province of BC official Production Services Tax Credit page (fetched directly); "
                                  "Creative BC programme pages",
            "why_undeterminable": "The thresholds that make a production an 'accredited production' are fixed by the "
                                  "definition in the Income Tax Act (British Columbia), which was not read in this "
                                  "pass. A secondary aggregator asserted 'no minimum spend'; that was rejected as "
                                  "unverifiable against the governing statute and conflicting with the existence of "
                                  "a statutory accreditation definition.",
        },
    },
    "il_foreign_production_fund": {
        "per_project_cap": {
            "reason_code": UnknownReasonCode.UNKNOWN_PENDING_PRIMARY_GUIDANCE.value,
            "authority_searched": "Israel Ministry of Economy & Industry; NFCT",
            "documents_reviewed": "NFCT information-for-foreign-producers pages; Israel Film Fund investment-scheme "
                                  "PDF; trade reporting on the 30% rebate",
            "why_undeterminable": "Reporting describes an upper bound of approximately USD 1,500,000 per production "
                                  "but does not disambiguate whether it bounds eligible COSTS or the rebate PAYOUT. "
                                  "Asserting either reading would misstate the programme.",
        },
    },
}


def get_unknown_fields(program_slug: str) -> dict[str, dict]:
    """Structured justifications for every genuine Unknown on a program."""
    return UNKNOWN_FIELD_REGISTER.get(program_slug, {})


def all_unknown_fields_by_reason_code() -> dict[str, list[str]]:
    """reason_code -> ['program_slug.field', ...] across the whole database."""
    out: dict[str, list[str]] = {}
    for slug, fields in UNKNOWN_FIELD_REGISTER.items():
        for field, rec in fields.items():
            out.setdefault(rec["reason_code"], []).append(f"{slug}.{field}")
    return {k: sorted(v) for k, v in sorted(out.items())}


register(ProgramRequirementsProfile(
    program_slug="jp_vipo_location_incentive", jurisdiction_code="JP",
    local_entity_required=True,        # "Only Japanese companies can apply" — a hard, published applicant gate
    preapproval_mandatory=True,        # subsidy covers spend only FROM the date the project is officially selected
    cultural_test_required=False,      # no cultural/content test; benefit-to-industry and promotion criteria apply instead
    refundable=True,                   # direct subsidy paid out
    transferable=False,
    allocation_type=AllocationType.COMPETITIVE,  # projects are "officially selected" against programme criteria
    evidence=EvidenceRecord(
        source_title="Location Incentive Program for International Large-scale Audiovisual Productions — VIPO / METI",
        source_url="https://www.vipo.or.jp/en/location-project/",
        issuing_authority="Ministry of Economy, Trade and Industry (METI) with VIPO (Visual Industry Promotion Organization) and the Japan Film Commission",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Official VIPO programme pages. Subsidy covers ONE HALF (50%) of qualifying Japanese "
              "spend incurred FROM the date the project is officially selected — matching the 0.5 "
              "rate already in this repository's rate rules, and making selection a genuine "
              "preapproval gate (pre-selection spend does not qualify). UPPER LIMIT JPY "
              "1,000,000,000 per project. MINIMUM: production costs in Japan of JPY 200,000,000 or "
              "more. DISTRIBUTION GATE (unusual and material): the project must be scheduled for "
              "release/screening/broadcast/distribution in TEN COUNTRIES OR TERRITORIES OR MORE — "
              "a real published eligibility condition with no analogue in most schemes, recorded "
              "in additional_facts. FURTHER CONDITIONS: the project must benefit Japan's domestic "
              "content industry (local employment and human-resource development, use of Japanese "
              "studios); must definitely have scenes shot in Japan; and the filmmaker must "
              "cooperate in regional promotion, including granting the shooting regions permission "
              "to use short clips promotionally on Japanese and international release. APPLICANT "
              "GATE: only Japanese companies may apply, so an overseas producer must work through "
              "a Japanese entity. ELIGIBLE SPEND: direct Japanese production expenses paid to "
              "Japanese corporations, individuals, local governments and public organisations. "
              "Programme extended to a two-year cycle. All amounts stated in JPY and recorded in "
              "STATUTORY_AMOUNTS_ORIGINAL_CURRENCY; no USD field populated.",
    ),
    additional_facts={
        "subsidy_rate": "One half (50%) of qualifying Japanese spend, counted only from the date of official selection.",
        "min_japanese_spend_jpy": "JPY 200,000,000 or more of production costs in Japan (authoritative original currency).",
        "cap_jpy": "JPY 1,000,000,000 upper limit of subsidy per project.",
        "distribution_gate": "Project must be scheduled for release/screening/broadcast/distribution in ten or more countries or territories.",
        "industry_benefit_gate": "Must benefit Japan's domestic content industry — local employment, human-resource development, use of Japanese studios.",
        "promotion_obligation": "Filmmaker must cooperate in regional promotion, granting shooting regions permission to use short clips promotionally on Japanese and international release.",
        "applicant_gate": "Only Japanese companies may apply; overseas producers must apply through a Japanese entity.",
        "eligible_spend": "Direct Japanese production expenses paid to Japanese corporations, individuals, local governments and public organisations.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="qa_screen_production_incentive", jurisdiction_code="QA",
    local_entity_required=True,        # applicants must be Qatari-registered companies licensed through Media City Qatar
    preapproval_mandatory=True,        # administered application programme; approval precedes rebate
    cultural_test_required=False,      # no cultural test; the +10% uplift runs on industry-development criteria (different mechanism)
    refundable=True,                   # cash rebate paid out
    transferable=False,
    evidence=EvidenceRecord(
        source_title="Qatar Screen Production Incentive (QSPI) — Doha Film Institute / Media City Qatar Film Committee",
        source_url="https://www.dohafilm.com/en/press/press-releases/qatar-launches-qatar-screen-production-incentive-qspi-programme-one-worlds",
        issuing_authority="Film Committee, Media City Qatar; Doha Film Institute",
        source_type=SourceType.SECONDARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="QSPI: up to 50% cash rebate on qualifying Qatari production expenditure, composed of "
              "a 40% BASE rebate plus a 10% UPLIFT for productions meeting industry-development "
              "criteria (hiring Qatari talent, investing in local training, promoting Qatari "
              "culture). The 50% ceiling matches the rate already in this repository's rate rules. "
              "APPLICANT GATE: eligible applicants must be Qatari-registered companies LICENSED "
              "THROUGH MEDIA CITY QATAR. NOTABLE SCOPE FEATURE: qualifying expenditure includes "
              "goods, services and labour from Qatar AND overseas, and productions may complete "
              "part of their filming in neighbouring Arab countries while remaining eligible, "
              "where up to 25% of total qualifying expenditure is incurred in a selected country "
              "— an unusually permissive published rule, recorded because it is a permission, not "
              "a restriction. TIMING: applications open from Q2 2026, administered by the Film "
              "Committee at Media City Qatar. MARKED SECONDARY: sourced from the Doha Film "
              "Institute launch release and trade coverage; the Film Committee's own detailed "
              "programme guidelines are not yet published. Minimum qualifying spend is recorded as "
              "a structured Unknown (UNKNOWN_PENDING_PRIMARY_GUIDANCE) rather than guessed.",
    ),
    additional_facts={
        "rate_structure": "40% base rebate plus a 10% uplift for meeting industry-development criteria (hiring Qatari talent, local training investment, promoting Qatari culture) — up to 50% total.",
        "applicant_gate": "Qatari-registered companies licensed through Media City Qatar.",
        "qualifying_expenditure_scope": "Includes goods, services and labour from Qatar and overseas.",
        "regional_spend_permission": "Up to 25% of total qualifying expenditure may be incurred in a selected neighbouring Arab country while remaining eligible.",
        "applications_open": "From Q2 2026; administered by the Film Committee at Media City Qatar.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="us_pa_film_production_credit", jurisdiction_code="US-PA",
    cultural_test_required=False,      # US state programme — no content/cultural test
    preapproval_mandatory=True,        # DCED application and award before credits issue
    refundable=False,                  # offsets PA tax liability; monetized by sale/assignment instead
    transferable=True,                 # may sell, assign or transfer credits to another entity
    annual_program_cap_usd=100_000_000.0,  # statutory annual cap (fiscal-year allocation has run lower — see notes)
    allocation_type=AllocationType.COMPETITIVE,  # awards allocated from a capped annual pool, per-project share limited
    evidence=EvidenceRecord(
        source_title="Film Production Tax Credit Guidelines — PA Department of Community & Economic Development (DCED)",
        source_url="https://dced.pa.gov/programs/film-tax-credit-program/",
        issuing_authority="Pennsylvania Department of Community & Economic Development (DCED), PA Film Office; authorised by Act 84 of 2016 (Article XVII-D, Entertainment Production Tax Credit)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="DCED official programme page and published Film Production Tax Credit Guidelines. "
              "25% TRANSFERABLE credit, with a 5% uplift for productions using a qualified "
              "production facility (30% maximum) — consistent with the 0.30 rate already in this "
              "repository's rate rules. HARD ELIGIBILITY GATE: Pennsylvania production expenses "
              "must comprise AT LEAST 60% of the film's total production expenses — a "
              "proportional test, not an absolute minimum spend, which is why "
              "min_local_spend_usd is left unset (no absolute floor is published) and the 60% "
              "test is recorded in additional_facts. MONETIZATION: recipients may use the credit "
              "against Pennsylvania state tax liability OR sell, assign or transfer it to another "
              "entity — hence transferable=True / refundable=False. PER-PROJECT LIMIT: the PA "
              "Film Office limits any single award to no more than 20% of the aggregate Film Tax "
              "Credits available in a fiscal year — a proportional cap, so no fixed "
              "per_project_cap_usd is asserted. ANNUAL CAP NUANCE (recorded, not resolved away): "
              "sources reviewed state a USD 100,000,000 annual cap while also describing a "
              "current fiscal-year allocation of USD 60,000,000, under which the 20% rule yields "
              "a USD 12,000,000 maximum single award. The statutory cap is recorded in the field "
              "and the allocation-vs-cap distinction is preserved in additional_facts rather than "
              "collapsing the two figures. USD is the authority's own currency — no conversion.",
    ),
    additional_facts={
        "pennsylvania_spend_test": "Pennsylvania production expenses must be at least 60% of the film's total production expenses (proportional test; no absolute minimum spend published).",
        "rate": "25% transferable credit; +5% uplift for use of a qualified production facility (30% maximum).",
        "per_project_limit": "No single award may exceed 20% of the aggregate Film Tax Credits available in a fiscal year (a proportional cap, not a fixed dollar cap).",
        "annual_cap_vs_allocation": "Sources state a USD 100,000,000 annual cap alongside a current fiscal-year allocation of USD 60,000,000; under that allocation the 20% rule produces a USD 12,000,000 maximum single award. Both figures preserved — cap and allocation are distinct concepts and are not collapsed.",
        "monetization": "Use against Pennsylvania state tax liability, or sell/assign/transfer to another entity.",
        "statutory_basis": "Act 84 of 2016, Article XVII-D (Entertainment Production Tax Credit).",
    },
))


register(ProgramRequirementsProfile(
    program_slug="us_ma_film_tax_credit", jurisdiction_code="US-MA",
    cultural_test_required=False,      # US state programme — no content/cultural test
    min_local_spend_usd=50_000.0,      # USD is the authority's own currency: total MA production expenses in a consecutive 12-month period
    per_person_cap_usd=1_000_000.0,    # payroll exclusion threshold — see notes (an EXCLUSION, not a capped inclusion)
    preapproval_mandatory=False,       # PUBLISHED ABSENCE: claimed via DOR MassTaxConnect; no pre-production approval gate published
    refundable=False,                  # not refundable, but cash-outable with the Commonwealth at 90% of face value (see notes)
    transferable=True,                 # transferable at market rate
    annual_program_cap_usd=None,       # PUBLISHED ABSENCE: "There are no annual or project caps"
    per_project_cap_usd=None,          # PUBLISHED ABSENCE (same)
    sunset_date=None,                  # no sunset indicated in the sources reviewed
    evidence=EvidenceRecord(
        source_title="Massachusetts Film Incentive Tax Credit — Mass.gov (Department of Revenue) and Massachusetts Film Office",
        source_url="https://www.mass.gov/info-details/massachusetts-film-incentive-tax-credit",
        issuing_authority="Massachusetts Department of Revenue (DOR); Massachusetts Film Office",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Mass.gov official pages plus the Massachusetts Film Office programme pages. TWO "
              "SEPARATE CREDITS, each 25%, with DIFFERENT tests — recorded distinctly rather than "
              "merged: (a) PAYROLL CREDIT — 25% of qualifying Massachusetts payroll, gated on "
              "total Massachusetts production expenses of at least USD 50,000 in a consecutive "
              "12-month period (this is the figure in min_local_spend_usd); (b) PRODUCTION "
              "EXPENSE CREDIT — 25%, gated on Massachusetts production expenses EXCEEDING 75% of "
              "total production expenses, OR at least 75% of filming days taking place in "
              "Massachusetts. The 75% tests are proportional and are recorded in additional_facts, "
              "not forced into an absolute field. PAYROLL EXCLUSION: qualifying payroll may not "
              "include any payments to an employee whose total payments in connection with the "
              "motion picture equal or exceed USD 1,000,000 — note this EXCLUDES that employee's "
              "payroll entirely rather than capping it at USD 1,000,000; per_person_cap_usd "
              "carries the threshold and this distinction is spelled out here so it is not "
              "misread as a partial inclusion. MONETIZATION: credits may be transferred at market "
              "rate, or cashed out with the Commonwealth at 90% of face value after satisfying "
              "tax liabilities — an unusually strong published monetization floor. PUBLISHED "
              "ABSENCES recorded as such: no annual cap, no per-project cap, and no sunset date "
              "appears in the sources reviewed. Applications are filed through the Department of "
              "Revenue's MassTaxConnect system; no pre-production approval gate is published, so "
              "preapproval_mandatory is recorded False rather than left unknown. USD is the "
              "authority's own currency — no conversion involved.",
    ),
    additional_facts={
        "two_distinct_credits": "Payroll credit 25% (gated on at least USD 50,000 total MA production expenses in a consecutive 12-month period) and production expense credit 25% (gated on the 75% tests below). Distinct tests, not a single blended credit.",
        "seventy_five_percent_tests": "Production expense credit requires Massachusetts production expenses to EXCEED 75% of total production expenses, OR at least 75% of filming days to take place in Massachusetts.",
        "payroll_exclusion_nature": "Payments to an employee whose total payments for the motion picture equal or exceed USD 1,000,000 are EXCLUDED from qualifying payroll entirely — this is an exclusion threshold, not a capped inclusion.",
        "monetization": "Transferable at market rate, or cashed out with the Commonwealth at 90% of face value after satisfying tax liabilities.",
        "caps": "No annual cap and no per-project cap are published.",
        "filing": "Applications submitted through the Department of Revenue's MassTaxConnect system.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="fi_business_finland_incentive", jurisdiction_code="FI",
    local_entity_required=True,        # requires a Finnish co-producer OR a Finnish production coordinator company
    cultural_test_required=True,       # production "must form an artistic whole that is based on cultural values" — qualitative, not points-based (see notes)
    preapproval_mandatory=True,        # funding decision precedes payment; rolling applications
    refundable=True,                   # cash rebate paid out
    transferable=False,
    allocation_type=AllocationType.FIRST_COME_FIRST_SERVED,  # expressly rolling, first-come-first-served
    payment_timing=TimingFact(
        value="Decisions usually issued within 40 days of application; payments processed after "
              "the funding decision",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    evidence=EvidenceRecord(
        source_title="Production incentive for the audiovisual industry — Business Finland",
        source_url="https://www.businessfinland.fi/en/services/funding/funding-services/Audiovisual-production-incentive",
        issuing_authority="Business Finland",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Business Finland official programme pages. MAXIMUM 25% cash rebate on production "
              "costs incurred in Finland — consistent with the 0.25 rate already in this "
              "repository's rate rules. RATE CAUTION: October 2025 promotional material describes "
              "Finland offering 'up to 40% support'; that figure refers to the AV production "
              "incentive COMBINED with other Finnish funding sources, NOT to this incentive alone, "
              "which remains capped at 25%. The two are deliberately not conflated. ELIGIBLE "
              "FORMATS: fictional feature films, documentary films, scripted series-type fiction, "
              "and animation. REAL PUBLISHED GATES: (a) FOREIGN FINANCING TEST — the share of "
              "foreign private financing must be at least 25% of the total production budget at "
              "the time of the funding decision (in force since January 2023); (b) DISTRIBUTION "
              "TEST — a distribution agreement for at least one platform or one territory; (c) "
              "FINNISH PARTICIPATION — a Finnish co-producer or a Finnish production coordinator "
              "company must participate, hence local_entity_required=True; (d) the production "
              "must form an artistic whole based on CULTURAL VALUES — recorded as "
              "cultural_test_required=True, with the nuance that this is a QUALITATIVE artistic/"
              "cultural criterion, not a points-based test of the UK/Ireland kind. EXPRESS "
              "EXCLUSIONS (published, recorded rather than inferred): commercials and promotional "
              "products; documentary SERIES; non-scripted series such as reality or talk shows; "
              "music videos and recordings of musical events; entertainment and sports events and "
              "their recordings; training videos; and productions in which public funding exceeds "
              "50% of the costs generated in Finland. ALLOCATION: rolling, first-come-first-served, "
              "with decisions usually within 40 days. No minimum spend figure and no annual "
              "programme cap are published in the pages reviewed.",
    ),
    additional_facts={
        "rate_ceiling": "Maximum 25% of production costs incurred in Finland. Promotional 'up to 40%' messaging refers to this incentive COMBINED with other Finnish funding, not to the incentive alone.",
        "foreign_financing_test": "Foreign private financing must be at least 25% of the total production budget at the time of the funding decision (in force since January 2023).",
        "distribution_test": "A distribution agreement for at least one platform or one territory is required.",
        "finnish_participation": "A Finnish co-producer or Finnish production coordinator company must participate in the production.",
        "cultural_criterion_nature": "The production must form an artistic whole based on cultural values — a qualitative criterion, not a points-based cultural test. CONFIRMED/PRECISION-UPGRADED 2026-08-19 (Worldwide Program Qualification Completion, Queue B): the legal basis for this exact language is the Government Decree on the payment of compensation for audiovisual productions 2024-2026 (Valtioneuvoston asetus audiovisuaalisen tuotannon tuen maksamisesta), which explicitly states the level of the artistic content of the production is NOT subject to evaluation -- i.e. this is a definitional eligibility category (does the work qualify as an audiovisual production of the relevant type) rather than a scored artistic-merit assessment of any kind. This is a genuinely, definitively resolved terminal state -- no point table is missing because none exists by design; QUALIFICATION_COMPLETE for this criterion.",
        "express_exclusions": "Commercials and promotional products; documentary series; non-scripted series (reality, talk shows); music videos and musical-event recordings; entertainment and sports events and their recordings; training videos; productions where public funding exceeds 50% of Finnish-generated costs.",
        "decision_speed": "Rolling first-come-first-served; decisions usually within 40 days.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="ch_pics_national_rebate", jurisdiction_code="CH",
    treaty_or_official_coproduction_required=True,  # PICS requires OFFICIAL SWISS CO-PRODUCTION STATUS — the defining gate of the national scheme
    local_coproducer_required=True,    # the rebate is paid to the Swiss co-producer
    min_shoot_days=5,                  # not fewer than five shooting days in Switzerland (fiction has an alternative spend route — see notes)
    cultural_test_required=False,      # no cultural points test; eligibility runs on co-production status and spend/day thresholds
    preapproval_mandatory=True,        # selective scheme supporting a limited number of projects per year
    refundable=True,                   # cash rebate paid out
    transferable=False,
    allocation_type=AllocationType.COMPETITIVE,  # supports around 30 projects a year against a limited envelope
    evidence=EvidenceRecord(
        source_title="PICS — Production Incentive Switzerland (national location incentive)",
        source_url="https://www.bak.admin.ch/",
        issuing_authority="Federal Office of Culture (Bundesamt für Kultur / Office fédéral de la culture), Switzerland",
        source_type=SourceType.SECONDARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="PICS refunds the SWISS CO-PRODUCER between 20% and 40% of billable costs, with the "
              "higher end of the band reserved for MINORITY co-productions — the 40% ceiling "
              "matches the rate already in this repository's rate rules. CEILING CHF 600,000 per "
              "project. DEFINING GATE: PICS requires OFFICIAL SWISS CO-PRODUCTION STATUS, which "
              "is what distinguishes the national scheme from the Swiss cantonal/regional rebate "
              "schemes (Geneva, Neuchâtel and others) that do NOT require that status. Those "
              "cantonal schemes are separate programmes and are deliberately not merged into this "
              "record. THRESHOLDS: minimum project budget CHF 2,500,000; billable costs at least "
              "CHF 500,000; and not fewer than five shooting days in Switzerland. For FICTION "
              "specifically, eligible Swiss costs of at least CHF 1,200,000 (majority "
              "co-production) or CHF 300,000 (minority co-production) apply, together with either "
              "five shooting days in Switzerland OR an additional CHF 150,000 of Swiss spend — an "
              "either/or structure, so min_shoot_days=5 records the day route while the "
              "alternative spend route is preserved in additional_facts rather than being lost. "
              "The scheme supports approximately 30 projects a year. All amounts are stated in "
              "CHF and recorded in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY; no USD field populated. "
              "MARKED SECONDARY: figures drawn from Cineuropa and Screen country-focus reporting "
              "and specialist production-service guides; the Federal Office of Culture's own PICS "
              "regulation document was not retrieved in this pass.",
    ),
    additional_facts={
        "rate_band": "20%-40% of billable costs refunded to the Swiss co-producer; the higher end is reserved for minority co-productions.",
        "ceiling_chf": "CHF 600,000 per project (authoritative original currency).",
        "min_project_budget_chf": "CHF 2,500,000 minimum project budget.",
        "min_billable_costs_chf": "CHF 500,000 minimum billable costs.",
        "fiction_specific_thresholds_chf": "Fiction: eligible Swiss costs of at least CHF 1,200,000 (majority co-production) or CHF 300,000 (minority co-production).",
        "shoot_days_or_spend_alternative": "Either five shooting days in Switzerland OR an additional CHF 150,000 of Swiss spend — an either/or condition, not cumulative.",
        "official_coproduction_gate": "PICS requires official Swiss co-production status. Swiss cantonal schemes (e.g. Geneva, Neuchâtel) do not require it and are separate programmes.",
        "projects_per_year": "Approximately 30 projects supported annually.",
        "primary_source_attempt_2026_07_26": "Three direct fetches attempted this session -- bak.admin.ch/bak/fr/home/creation-culturelle/cinema.html, bak.admin.ch/film, and the specific 'Déclarations d'intention de l'aide liée au site (PICS)' BAK subpage -- all returned 404 or landed on generic index pages with no PICS-specific figures. A WebSearch snippet (unfetched, not independently verified) suggested 'automatic funding on application' (possibly contradicting the recorded COMPETITIVE allocation_type) and a women's-internship condition for projects over CHF 500,000 -- NEITHER asserted here, both flagged for a future pass with a working URL rather than recorded on search-snippet confidence alone.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="lu_filmfund_tax_shelter_rebate", jurisdiction_code="LU",
    local_entity_required=True,        # beneficiary must be a Luxembourg capital company whose MAIN business purpose is audiovisual production
    cultural_test_required=True,       # selection committee assesses on cultural, social and economic criteria
    preapproval_mandatory=True,        # selective committee award; four submission deadlines per calendar year
    refundable=False,                  # NOT a rebate — AFS is a REPAYABLE advance on receipts (see the discrepancy note below)
    transferable=False,
    clawback_or_repayment_trigger=True,  # reimbursable from the first euro if the project reaches the production phase
    allocation_type=AllocationType.DISCRETIONARY,  # selection committee, discretionary award
    application_deadline=TimingFact(
        value="Four submission deadlines per calendar year; all applications filed by the "
              "Luxembourg company through the eFilmfund portal",
        basis=TimingBasis.OFFICIAL_TARGET,
    ),
    evidence=EvidenceRecord(
        source_title="Selective Financial Assistance (AFS/SFA) for production — Film Fund Luxembourg",
        source_url="https://filmfund.lu/en/funding/afs-p/",
        issuing_authority="Film Fund Luxembourg (Fonds national de soutien à la production audiovisuelle)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Film Fund Luxembourg official funding pages. AFS (Aide financière sélective / "
              "Selective Financial Assistance) is a SELECTIVE, DISCRETIONARY instrument providing "
              "support for script development and writing, distribution, and production/"
              "co-production of drama, animation, documentary, short film, transmedia and XR "
              "projects. BENEFICIARY GATE: Luxembourg capital companies whose MAIN business "
              "purpose is audiovisual production, with demonstrated prior production experience "
              "and stable, long-term administrative structures. Applications are filed by the "
              "Luxembourg company through the eFilmfund portal against four deadlines per "
              "calendar year, and are assessed by a SELECTION COMMITTEE on cultural, social and "
              "economic criteria — hence allocation_type=DISCRETIONARY and "
              "cultural_test_required=True (qualitative committee assessment, not a points test). "
              "\n\nMATERIAL MODELLING DISCREPANCY — FLAGGED, NOT RESOLVED: this repository's rate "
              "rules carry lu_filmfund_tax_shelter_rebate at a 0.40 rebate-style rate. The AFS "
              "instrument verified here is NOT a rebate: it is an ADVANCE ON RECEIPTS, "
              "'reimbursable from the first euro at a rate equal to the share AFS represents in "
              "the project's total financing, if the project reaches the production phase' — i.e. "
              "REPAYABLE, which is why refundable=False and clawback_or_repayment_trigger=True. "
              "A repayable advance and a 40% cash rebate are different economic instruments and "
              "should not be priced identically. Two readings are possible and the sources "
              "reviewed do not settle which the rate rule intended: (a) the rate rule models a "
              "separate Luxembourg audiovisual investment-certificate / tax-shelter mechanism "
              "that the slug name also references, or (b) the rate rule is mis-specified for AFS. "
              "Resolving this requires reading the governing Luxembourg law and the Fund's own "
              "AFS regulation, and any change to the rate rule is OUT OF SCOPE for this database "
              "phase (calculation logic is frozen). Recorded here so the discrepancy is visible "
              "to the optimizer phase rather than silently inherited. No rate rule was altered.",
    ),
    additional_facts={
        "instrument_nature": "AFS is an advance on receipts — reimbursable from the first euro at a rate equal to the share AFS represents in the project's total financing, if the project reaches production. It is not a cash rebate.",
        "beneficiary_gate": "Luxembourg capital company whose main business purpose is audiovisual production, with prior production experience and stable long-term administrative structures.",
        "supported_activities": "Script development and writing, distribution, and production/co-production of drama, animation, documentary, short film, transmedia and XR projects.",
        "assessment": "Selection committee assessment on cultural, social and economic criteria.",
        "deadlines": "Four submission deadlines per calendar year, filed through the eFilmfund portal by the Luxembourg company.",
        "modelling_discrepancy": "Repository rate rules carry a 0.40 rebate-style rate for this slug, but AFS is a repayable advance, not a rebate. Flagged for the optimizer phase; no rate rule changed (calculation logic frozen in this phase).",
    },
))


register(ProgramRequirementsProfile(
    program_slug="mx_federal_film_incentive_2026", jurisdiction_code="MX",
    local_entity_required=True,        # foreign residents WITHOUT a Mexican permanent establishment must produce through a Mexican production company (Decreto, Articulo Primero, verbatim)
    cultural_test_required=False,      # the national-supply/min-spend rules are supply-chain and scale tests, NOT a cultural/content test
    preapproval_mandatory=True,        # registration + Technical Committee certificate of presentation of procedure required
    refundable=False,                  # a credit APPLIED against ISR owed (Decreto, Articulo Segundo) -- not a cash refund mechanism
    transferable=True,                 # Decreto, Articulo Segundo, Fracciones I-II: a detailed two-stage transfer mechanism (see evidence notes)
    annual_program_cap_usd=None,       # MXN 400,000,000 PER YEAR -- recorded in additional_facts/STATUTORY_AMOUNTS_ORIGINAL_CURRENCY, not converted
    sunset_date="2030-09-30",          # incentive distributed from entry into force until 30 September 2030 (Decreto, Articulo Quinto)
    audit_required=None,               # compliance certification (Constancia de cumplimiento) required; a separate independent-audit requirement is not stated in the Decreto text itself (may be addressed in the Lineamientos, not yet fully retrieved)
    evidence=EvidenceRecord(
        source_title="DECRETO por el que se otorga un estimulo fiscal a la produccion cinematografica y audiovisual (Diario Oficial de la Federacion, 16 February 2026)",
        source_url="https://www.dof.gob.mx/nota_detalle.php?codigo=5780237&fecha=16/02/2026",
        issuing_authority="Presidencia de la Republica (Claudia Sheinbaum Pardo); Secretaria de Hacienda y Credito Publico; Secretaria de Cultura -- Gobierno de Mexico",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="DOCUMENT RETRIEVAL ESCALATION APPLIED (per the permanent engineering rule adopted "
              "this session): a prior direct fetch of dof.gob.mx failed with 'unable to verify the "
              "first certificate'. Diagnosis via openssl s_client confirmed this is a SERVER-SIDE "
              "TLS CHAIN MISCONFIGURATION on dof.gob.mx itself (missing intermediate certificate in "
              "the chain it presents; verify error 21) -- a common, well-documented issue on older "
              "government web servers, NOT a bot-detection block, NOT an authentication wall, and "
              "NOT a case of the document genuinely being unavailable. curl with certificate "
              "verification disabled (-k) reached the page with a normal HTTP 200 and returned the "
              "real, complete Decree text -- this is retrieving public information through a "
              "broken but non-adversarial TLS chain, not bypassing any access control, CAPTCHA, or "
              "paywall. THIS UPGRADES THE RECORD TO PRIMARY_VERIFIED: the actual DOF Decree text "
              "was read in full, not a law-firm paraphrase. PROGRAM POSITIVELY IDENTIFIED BEFORE "
              "WRITING (Jurisdiction Isolation Rule, unchanged from the prior session): distinct "
              "from EFICINE 189 (2006, Art. 189 LISR investor credit, MXN 25,000,000/project, "
              "administered via IMCINE) -- EFICINE 189 is not recorded here. LEGAL BASIS (genuinely "
              "new, exact citation): issued under Articulo 89, fraccion I of the Constitucion "
              "Politica de los Estados Unidos Mexicanos (presidential regulatory power); Articulos "
              "31 y 41 Bis of the Ley Organica de la Administracion Publica Federal; Articulo 39, "
              "primer parrafo, fracciones II y III of the Codigo Fiscal de la Federacion. Signed by "
              "President Claudia Sheinbaum Pardo, Secretary of Finance Edgar Abraham Amador Zamora, "
              "and Secretary of Culture Claudia Stella Curiel de Icaza, dated 13 February 2026, "
              "published in the DOF 16 February 2026. RATE CONFIRMED VERBATIM: 'un credito fiscal "
              "de hasta el 30% del costo total del proyecto o proceso de produccion cinematografica "
              "o audiovisual' -- exactly matches the 0.30 rate already in this repository's rate "
              "rules. ANNUAL CAP CORRECTED (a genuine, material correction to this profile's own "
              "prior characterization): the Decreto text states 'el monto total ANUAL del estimulo "
              "fiscal que el Comite Tecnico autorice a los contribuyentes no excedera de 400 "
              "millones de pesos' -- this is confirmed as an ANNUAL cap (MXN 400,000,000 PER YEAR), "
              "NOT a one-time total programme envelope across the scheme's life as this profile had "
              "previously recorded based on an imprecise Baker McKenzie paraphrase. TRANSFER "
              "MECHANISM (genuinely new, richly detailed -- Articulo Segundo): a TWO-STAGE process, "
              "not a single flat transferability fact. Stage 1 (Fraccion I): up to 100% of the "
              "credit may be transferred for consideration ('a titulo oneroso') to national "
              "suppliers directly related to the production, to incentivize the supply chain -- "
              "with indirect expenses via such suppliers capped at 30% of the total credit. Stage 2 "
              "(Fraccion II): any remaining balance after Stage 1 may be further transferred, for "
              "consideration, to ANY Mexican ISR taxpayer, capped at 70% of the total credit, at a "
              "transfer value not exceeding 85% of the amount transferred, and the transferred "
              "credit received by any single recipient cannot exceed 15% of that recipient's prior-"
              "year fiscal profit (utilidad fiscal). Recipients of a transferred credit CANNOT "
              "re-transfer it to third parties, including via merger or spin-off. Beneficiaries and "
              "transfer recipients must not be related parties to each other. ADMINISTRATIVE "
              "SIMPLIFICATION (genuinely new, Articulo Cuarto): beneficiaries are relieved of the "
              "notice-filing obligation under Articulo 25, primer parrafo of the Codigo Fiscal de "
              "la Federacion. TECHNICAL COMMITTEE (Articulo Quinto, corroborates and refines the "
              "gob.mx finding from the prior session): includes a representative of IMCINE; sets "
              "the maximum rate/amount any applicant may receive per the Lineamientos. "
              "DISQUALIFYING CONDITIONS (genuinely new, Articulo Sexto): taxpayers in liquidation; "
              "subject to temporary restriction of digital seal use for CFDI issuance (Art. 17-H "
              "Bis CFF); with cancelled CFDI-issuance certificates (Art. 17-H CFF); among others, "
              "are excluded from the incentive. NON-COMPLIANCE CONSEQUENCES (genuinely new, "
              "Articulo Septimo): a taxpayer who applied the credit and fails to meet any "
              "requirement must pay the tax, inflation adjustment (actualizacion), and surcharges, "
              "and the incentive is voided. SAT RULE-MAKING (Articulo Octavo): the Servicio de "
              "Administracion Tributaria is empowered to issue general rules for the Decree's "
              "proper application. EFFECTIVE DATE CLARIFIED (resolves an internal ambiguity from "
              "the prior session): the DECREE itself took effect the day after its 2026-02-16 "
              "publication (i.e. ~2026-02-17) per Transitorio Primero -- DISTINCT from the "
              "separate, later Lineamientos (Guidelines) published 2026-03-30, which took effect "
              "the following day (2026-03-31); both dates are genuine and refer to different "
              "documents, not a contradiction. ELIGIBILITY (Articulo Primero, verbatim structure "
              "confirmed): individuals or legal entities resident in Mexico taxed under Titulo II, "
              "Titulo IV Capitulo II Seccion I, or Titulo VII Capitulo XII of the Ley del Impuesto "
              "sobre la Renta; residents abroad WITH a Mexican permanent establishment under those "
              "same regimes; and residents abroad WITHOUT a permanent establishment, provided they "
              "produce through a Mexico-resident individual or entity dedicated to film/audiovisual "
              "production. MINIMUM-SPEND-BY-FORMAT RECITAL CONFIRMED (the Decreto's own preamble "
              "explains WHY thresholds exist, though the exact MXN figures by format are deferred "
              "to the Lineamientos rather than stated in the Decreto itself): 'resulta necesario "
              "establecer umbrales minimos de erogacion en territorio nacional, atendiendo a la "
              "naturaleza, escala y complejidad de cada tipo de proyecto o proceso, en observancia "
              "del principio de igualdad material' -- this confirms the MXN 40M/20M/5M by-format "
              "figures already recorded (from Baker McKenzie) are consistent with the Decree's own "
              "stated design principle, though those exact figures were not independently re-"
              "confirmed in the Decreto text itself (they belong to the Lineamientos, a separate, "
              "not-yet-fully-retrieved document) -- recorded with that caveat rather than claimed "
              "as directly re-verified. All MXN amounts recorded per the Canonical Currency Rule; "
              "no USD conversion performed.",
    ),
    additional_facts={
        "official_program_name": "Estimulo Fiscal a la Produccion Cinematografica y Audiovisual (EFICA) -- confirmed via direct gob.mx/cultura fetch, corroborated by the Decreto's own title.",
        "administering_authority_confirmed": "IMCINE (Instituto Mexicano de Cinematografia) sits on the Technical Committee, under the Secretaria de Cultura; SAT (tax authority) empowered to issue implementing rules.",
        "legal_basis": "Constitucion Politica de los Estados Unidos Mexicanos Art. 89 fraccion I; Ley Organica de la Administracion Publica Federal Arts. 31 y 41 Bis; Codigo Fiscal de la Federacion Art. 39 primer parrafo fracciones II y III. Decreto signed 2026-02-13, published DOF 2026-02-16, effective ~2026-02-17.",
        "annual_cap_correction": "MXN 400,000,000 is an ANNUAL cap ('monto total anual'), corrected from this profile's own prior mischaracterization as a one-time total programme envelope.",
        "transfer_mechanism_detailed": "Stage 1: up to 100% of the credit transferable to national suppliers directly related to the production (indirect expenses via such suppliers capped at 30% of the credit). Stage 2: any remaining balance transferable to any Mexican ISR taxpayer, capped at 70% of the total credit, transfer value capped at 85% of the amount transferred, and the transferred credit capped at 15% of the recipient's prior-year fiscal profit. No re-transfer by recipients, even via merger/spin-off. Beneficiary and recipient must not be related parties.",
        "administrative_simplification": "Beneficiaries relieved of the notice-filing obligation under CFF Art. 25, primer parrafo.",
        "disqualifying_conditions": "Taxpayers in liquidation; subject to temporary CFDI digital-seal restriction (CFF Art. 17-H Bis); with cancelled CFDI-issuance certificates (CFF Art. 17-H); among other conditions in Articulo Sexto.",
        "non_compliance_consequences": "A taxpayer failing to meet any requirement after applying the credit must pay the tax, inflation adjustment, and surcharges; the incentive is voided.",
        "min_spend_by_format_mxn": "MXN 40,000,000 feature films and narrative/animation series; MXN 20,000,000 documentary series and documentary features; MXN 5,000,000 animation, VFX or post-production only -- from Baker McKenzie's analysis; the Decreto's own recital confirms such thresholds exist by design but defers the exact figures to the separate Lineamientos, not yet fully retrieved.",
        "national_supply_gate": "At least 70% national supply required (Baker McKenzie; not independently re-confirmed in the Decreto text itself, which defers operational detail to the Lineamientos).",
        "technical_committee_certification": "Constancia de presentacion de tramite (initial review) then Constancia de cumplimiento (post-completion; makes the credit effective) -- both confirmed via direct gob.mx/cultura fetch.",
        "per_project_cap_mxn": "MXN 40,000,000 per project (Baker McKenzie; not independently re-confirmed in the Decreto text, which defers per-project limits to the Lineamientos/Technical Committee determination).",
        "eligibility": "Individuals and legal entities resident in Mexico (Titulo II/Titulo IV Cap II Secc I/Titulo VII Cap XII LISR); residents abroad with a Mexican permanent establishment; residents abroad without a permanent establishment producing through a Mexico-resident individual or entity.",
        "effective_window": "Decreto effective ~2026-02-17 (day after 2026-02-16 DOF publication); Lineamientos effective 2026-03-31 (day after 2026-03-30 DOF publication); programme distributed until 2030-09-30.",
        "document_retrieval_note": "dof.gob.mx has a server-side TLS certificate chain misconfiguration (missing intermediate cert, verify error 21) -- not a block, not an auth wall. Retrieved successfully with certificate verification disabled; the real Decree text was read in full via this method.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="us_nc_film_entertainment_grant", jurisdiction_code="US-NC",
    cultural_test_required=False,      # US state programme — no content/cultural test
    min_local_spend_usd=1_500_000.0,   # USD is the authority's own currency: feature-length films (other formats in additional_facts)
    per_project_cap_usd=7_000_000.0,   # feature-length films incl. made-for-TV/streaming movies (series/commercial caps differ — see notes)
    annual_program_cap_usd=31_000_000.0,  # recurring funds per NC fiscal year (1 July - 30 June)
    preapproval_mandatory=True,        # Intent to Film Notification Form precedes the formal grant application
    refundable=True,                   # cash grant/rebate paid out — not a tax credit
    transferable=False,                # grant, so no transfer mechanism
    evidence=EvidenceRecord(
        source_title="Film Industry Grants — North Carolina Department of Commerce; North Carolina Film Office",
        source_url="https://www.commerce.nc.gov/grants-incentives/film-industry-grants",
        issuing_authority="North Carolina Department of Commerce; North Carolina Film Office",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="NC Department of Commerce and NC Film Office official pages. GRANT (not a tax "
              "credit) of up to 25% of qualified expenses — matching the 0.25 rate already in "
              "this repository's rate rules, and the reason refundable=True / transferable=False "
              "(a grant is disbursed, so there is nothing to transfer). MINIMUM SPEND BY FORMAT: "
              "USD 1,500,000 feature-length films; USD 500,000 made-for-TV/streaming movies; USD "
              "500,000 per-episode AVERAGE for TV/streaming series; USD 250,000 commercials. The "
              "feature threshold populates min_local_spend_usd; the rest are in additional_facts "
              "because the schema carries one minimum. PER-PROJECT CAPS ALSO VARY BY FORMAT: USD "
              "7,000,000 feature-length films (including made-for-TV/streaming movies); USD "
              "15,000,000 PER SEASON for TV/streaming series; USD 250,000 commercials. "
              "per_project_cap_usd records the feature cap; the series cap is materially larger "
              "and is recorded in additional_facts so it is not lost. ANNUAL ALLOCATION USD "
              "31,000,000 in recurring funds per North Carolina fiscal year (1 July - 30 June) — "
              "note the NC fiscal year, which governs when the allocation resets. PROCESS: "
              "complete the NC Film Office's Intent to Film Notification Form first; the Film "
              "Office then issues the formal Film and Entertainment Grant Application, submitted "
              "with script and budget documentation — a genuine two-stage preapproval sequence. "
              "USD is the authority's own currency — no conversion involved.",
    ),
    additional_facts={
        "min_spend_by_format_usd": "USD 1,500,000 feature-length films; USD 500,000 made-for-TV/streaming movies; USD 500,000 per-episode average for TV/streaming series; USD 250,000 commercials.",
        "per_project_caps_by_format_usd": "USD 7,000,000 feature-length films (incl. made-for-TV/streaming movies); USD 15,000,000 PER SEASON for TV/streaming series; USD 250,000 commercials.",
        "annual_allocation_usd": "USD 31,000,000 recurring per North Carolina fiscal year (1 July - 30 June).",
        "two_stage_application": "Intent to Film Notification Form to the NC Film Office first; the Film Office then issues the formal Film and Entertainment Grant Application, submitted with script and budget documentation.",
        "instrument": "Cash grant/rebate administered by the Department of Commerce — not a tax credit, so no transfer or carry-forward mechanism applies.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="us_wa_motion_picture_competitiveness", jurisdiction_code="US-WA",
    cultural_test_required=False,      # US state programme — no content/cultural test
    min_local_spend_usd=500_000.0,     # USD is the authority's own currency: feature films (episodic/commercial thresholds differ — see additional_facts)
    annual_program_cap_usd=15_000_000.0,  # annual funding pool, renewing each January
    preapproval_mandatory=True,        # application at least 5 business days before principal photography; contract required
    refundable=True,                   # funding assistance paid as a CASH payment — not a tax credit
    transferable=False,                # cash payment, so nothing to transfer
    application_deadline=TimingFact(
        value="Completed application at least five business days prior to the start of principal "
              "photography; contract with Washington Filmworks within two weeks of the Funding "
              "Letter of Intent; principal photography must begin within 120 days of that letter "
              "(45 days for commercials)",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    audit_or_final_certification_deadline=TimingFact(
        value="Completion package due within 60 days of completing principal photography in "
              "Washington (45 days for commercials)",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="Production Incentive Program (PIP) Guidelines & Criteria and Fact Sheet (rev. 2025-06-24) — Washington Filmworks; Chapter 43.365 RCW",
        source_url="https://www.washingtonfilmworks.org/wp-content/uploads/2025/06/2025.06.24_WF-Production-Incentive-Program-PIP_GC.pdf",
        issuing_authority="Washington Filmworks (administrator of the Motion Picture Competitiveness Program); statutory basis Chapter 43.365 RCW",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Washington Filmworks official PIP Guidelines & Criteria and Fact Sheet (both rev. "
              "2025-06-24), statutory basis Chapter 43.365 RCW. INSTRUMENT: funding assistance "
              "paid as a CASH payment (not a tax credit) to feature films, episodic series and "
              "commercials filmed anywhere in Washington State — hence refundable=True, "
              "transferable=False. MINIMUM SPEND BY FORMAT: USD 500,000 feature films; USD "
              "300,000 PER EPISODE for episodic series; USD 150,000 commercials. ANNUAL FUNDING "
              "USD 15,000,000, renewing every January — note the January renewal, not a July "
              "fiscal year. WASHINGTON RESIDENT REQUIREMENT (a real, published eligibility gate): "
              "productions must have TWO Washington residents among any of four positions — "
              "Writer, Director, Producer, Lead Actor. Recorded in additional_facts as the schema "
              "has no key-personnel-residency field. TIGHT SEQUENCED DEADLINES, all published and "
              "all material to a producer: application at least 5 business days before principal "
              "photography; contract within 2 weeks of the Funding Letter of Intent; principal "
              "photography within 120 days of that letter (45 days for commercials); completion "
              "package within 60 days of finishing Washington principal photography (45 days for "
              "commercials). ADMINISTRATIVE FEES: USD 5,000 for motion pictures and episodic "
              "series (charged per episode reviewed) and USD 2,500 for commercials.\n\n"
              "MATERIAL DISCREPANCY PRESERVED (not resolved): this repository's rate rules carry "
              "0.45 for this program, while the Washington Filmworks Fact Sheet reviewed here "
              "states funding assistance of UP TO 30 PERCENT of qualified in-state expenditures. "
              "Secondary aggregators describe a '30-45%' range, which suggests the 45% figure may "
              "correspond to an enhanced or uplifted tier (for example rural or "
              "underrepresented-community filming) that the summary Fact Sheet does not "
              "enumerate. The full PIP Guidelines & Criteria PDF would settle whether 45% is a "
              "real published ceiling and on what conditions. The verified 30% figure is recorded "
              "in additional_facts and the divergence is preserved here rather than silently "
              "reconciling the rate rule. NO RATE RULE ALTERED (calculation logic frozen).",
    ),
    additional_facts={
        "verified_rate": "Washington Filmworks Fact Sheet (rev. 2025-06-24): funding assistance of up to 30% of qualified in-state expenditures, including labor and production costs.",
        "rate_discrepancy": "Repository rate rules carry 0.45. Aggregators describe a 30-45% range, implying a possible enhanced/uplifted tier not enumerated in the Fact Sheet. Unresolved; full PIP Guidelines & Criteria PDF required. No rate rule altered.",
        "min_spend_by_format_usd": "USD 500,000 feature films; USD 300,000 per episode for episodic series; USD 150,000 commercials.",
        "annual_funding_usd": "USD 15,000,000, renewing every January (calendar-year renewal, not a July fiscal year).",
        "washington_resident_requirement": "Two Washington residents among any of four positions: Writer, Director, Producer, Lead Actor.",
        "sequenced_deadlines": "Application at least 5 business days before principal photography; contract within 2 weeks of the Funding Letter of Intent; principal photography within 120 days of that letter (45 days for commercials); completion package within 60 days of finishing WA principal photography (45 days for commercials).",
        "administrative_fees_usd": "USD 5,000 for motion pictures and episodic series (per episode reviewed); USD 2,500 for commercials.",
        "statutory_basis": "Chapter 43.365 RCW; administered by Washington Filmworks.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="us_pr_film_incentives_act", jurisdiction_code="US-PR",
    cultural_test_required=False,      # no content/cultural test published
    min_local_spend_usd=50_000.0,      # USD is Puerto Rico's own currency: USD 50,000 per project (USD 25,000 short films)
    preapproval_mandatory=True,        # tax exemption decree obtained from DDEC before credits are certified
    refundable=False,                  # a tax credit, monetized by transfer rather than refund
    transferable=True,                 # transferable tax credit
    audit_required=True,               # an Auditor's Report is the precondition for the DDEC Certification of Tax Credits
    cpa_or_approved_auditor_required=True,
    payment_timing=TimingFact(
        value="The DDEC Secretary issues the Certification of Tax Credits within thirty (30) days "
              "of receiving the Auditor's Report; that period may be interrupted if the Secretary "
              "requests additional information from the Auditor",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="Film industry incentives under the Puerto Rico Incentives Code (Act 60-2019), which subsumed the former Film Industry Economic Incentives Act (Act 27-2011) — Puerto Rico Film Commission / DDEC",
        source_url="https://puertoricofilm.ddec.pr.gov/incentives/",
        issuing_authority="Departamento de Desarrollo Económico y Comercio (DDEC), Puerto Rico; Puerto Rico Film Commission",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="GOVERNING-LAW CURRENCY NOTE (material, and the reason this profile is not filed "
              "under 'Act 27' alone): Puerto Rico's Incentives Code, ACT 60-2019, unified more "
              "than 70 prior incentive statutes INCLUDING the former Film Industry Economic "
              "Incentives Act (Act 27-2011). The repository slug is us_pr_film_incentives_act and "
              "much industry material still refers to 'Act 27', but the currently governing "
              "instrument is Act 60-2019. Both designations are recorded so a producer is not "
              "misdirected to a superseded statute, and so this is not mistaken for a separate "
              "programme under the Jurisdiction Isolation Rule — it is the SAME incentive, "
              "recodified.\n\n"
              "RATE STRUCTURE (two distinct rates, recorded distinctly): 40% transferable tax "
              "credit on qualified LOCAL spend and RESIDENT labour — matching the 0.40 rate "
              "already in this repository's rate rules — and 20% on NON-RESIDENT costs. "
              "Post-production-only projects may earn a credit of up to USD 500,000 per project, "
              "a format-specific ceiling recorded in additional_facts rather than applied as a "
              "general per-project cap (it does not bind ordinary production projects). MINIMUM "
              "SPEND USD 50,000 per project; USD 25,000 for short films. Puerto Rico uses USD as "
              "its own currency, so no conversion is involved. PROCESS: an application to DDEC "
              "covering entity, budget, financing, locations and heads of department; a tax "
              "exemption decree; then an AUDITOR'S REPORT certifying expenses, on receipt of "
              "which the DDEC Secretary issues the Certification of Tax Credits within 30 days "
              "(interruptible if the Secretary requests further information from the Auditor) — "
              "hence audit_required=True and a statutory-deadline payment timing. No annual "
              "programme cap is published in the materials reviewed.",
    ),
    additional_facts={
        "governing_law": "Act 60-2019 (Puerto Rico Incentives Code), which unified 70+ prior incentive laws including the former Act 27-2011 Film Industry Economic Incentives Act. 'Act 27' remains common industry shorthand for the same, now-recodified, incentive.",
        "rate_structure": "40% transferable tax credit on qualified local spend and resident labour; 20% on non-resident costs.",
        "post_production_only_ceiling_usd": "Post-production-only projects may earn a credit of up to USD 500,000 per project — a format-specific ceiling, not a general per-project cap.",
        "min_spend_usd": "USD 50,000 per project; USD 25,000 for short films.",
        "certification_process": "Application to DDEC (entity, budget, financing, locations, heads of department) and tax exemption decree; Auditor's Report certifying expenses; DDEC Secretary issues Certification of Tax Credits within 30 days of that report.",
        "annual_cap": "None published in the materials reviewed.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="ca_ab_fttc", jurisdiction_code="CA-AB",
    local_entity_required=True,        # applicant must be incorporated or registered in Alberta and not exempt under the Alberta Corporate Tax Act
    cultural_test_required=False,      # no cultural/content test; the 30% tier turns on Alberta ownership/credit/copyright/spend criteria
    preapproval_mandatory=False,       # PUBLISHED ABSENCE: applications accepted up to 120 days AFTER principal photography commences
    refundable=True,                   # refundable Alberta tax credit
    transferable=False,
    application_deadline=TimingFact(
        value="Applications may be made up to 120 days after commencing principal photography in "
              "Alberta (effective 2024-06-07)",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="Film and Television Tax Credit (FTTC) — Program Guidelines; Film and Television Tax Credit Act and Regulation (amendments in force 2024-06-07)",
        source_url="https://www.alberta.ca/film-television-tax-credit",
        issuing_authority="Government of Alberta (Jobs, Economy and Trade); Film and Television Tax Credit Act and Film and Television Tax Credit Regulation",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Alberta.ca official programme page and the published FTTC Program Guidelines. "
              "REFUNDABLE Alberta tax credit on eligible production costs. APPLICANT GATE: the "
              "corporation must be engaged in film, television or digital media production, be "
              "INCORPORATED OR REGISTERED IN ALBERTA, and must not be exempt from tax under the "
              "Alberta Corporate Tax Act. MINIMUM: total production costs of at least CAD 499,999 "
              "(Canadian funds, excluding GST) — note the threshold is expressed as 499,999, not "
              "500,000, and is recorded verbatim rather than rounded. TWO ELECTABLE RATES: 22% or "
              "30%. The 30% tier requires ALL of: at least 50% project ownership by eligible "
              "Alberta individuals; one Alberta-based producer with a single-card credit; "
              "Alberta-based copyright ownership for 10 years; AND either 60% of eligible "
              "production costs OR 70% of wages spent in Alberta. That composite test is recorded "
              "in additional_facts because the schema has no multi-criterion tier field; the 30% "
              "ceiling matches the rate already in this repository's rate rules. NOTABLE PUBLISHED "
              "ABSENCE OF A PREAPPROVAL GATE: effective 2024-06-07, productions may apply up to "
              "120 DAYS AFTER commencing principal photography in Alberta — unusual among the "
              "programmes in this database, most of which bar post-commencement application "
              "outright, so preapproval_mandatory is recorded False rather than assumed True by "
              "analogy (Jurisdiction Isolation Rule). Amendments to the Act, Regulation and "
              "Guidelines came into force 2024-06-07. Thresholds stated in CAD and recorded in "
              "STATUTORY_AMOUNTS_ORIGINAL_CURRENCY; no USD field populated. No annual programme "
              "cap or per-project cap is published in the pages reviewed.",
    ),
    additional_facts={
        "min_total_production_costs_cad": "CAD 499,999 total production costs, Canadian funds, excluding GST (recorded verbatim — the published figure is 499,999, not 500,000).",
        "two_electable_rates": "Applicants elect either a 22% or a 30% credit rate.",
        "thirty_percent_tier_criteria": "Requires ALL of: at least 50% project ownership by eligible Alberta individuals; one Alberta-based producer with single-card credit; Alberta-based copyright ownership for 10 years; AND either 60% of eligible production costs or 70% of wages spent in Alberta.",
        "post_commencement_application": "Applications accepted up to 120 days AFTER commencing principal photography in Alberta (effective 2024-06-07) — no pre-production approval gate.",
        "legislative_currency": "Film and Television Tax Credit Act, Regulation and Program Guidelines as amended, in force 2024-06-07.",
        "caps": "No annual programme cap and no per-project cap published in the pages reviewed.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="ee_film_estonia_rebate", jurisdiction_code="EE",
    local_entity_required=True,        # applications must be made through an Estonian company (co-production or production service)
    cultural_test_required=False,      # no cultural test published; eligibility runs on format, budget and local-spend thresholds
    preapproval_mandatory=True,        # application and award precede the rebate
    refundable=True,                   # cash rebate paid out
    transferable=False,
    evidence=EvidenceRecord(
        source_title="Film Estonia cash rebate — Guidelines and how to apply; Estonian Film Institute (Eesti Filmi Instituut)",
        source_url="https://filmestonia.eu/film-estonia-funding/guidelines-and-how-to-apply/",
        issuing_authority="Estonian Film Institute (Eesti Filmi Instituut) — Film Estonia",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Film Estonia official guidelines. Cash rebate of UP TO 30% of eligible Estonian "
              "production costs — matching the 0.30 rate already in this repository's rate rules. "
              "Supports incoming feature films, feature documentaries, animation films, animation "
              "series, high-end TV drama, AND the post-production of all of those.\n\n"
              "TWO DISTINCT THRESHOLD STRUCTURES, recorded separately because they are different "
              "mechanisms and must not be blended:\n"
              "(1) PRODUCTION — a paired test of overall budget AND minimum Estonian spend, by "
              "format: feature film budget at least EUR 1,000,000 with local spend at least EUR "
              "200,000; feature documentary budget at least EUR 200,000 with local spend at least "
              "EUR 70,000; animation budget at least EUR 250,000 with local spend at least EUR "
              "70,000; animation series budget at least EUR 500,000 with local spend at least EUR "
              "70,000 per series; high-end TV drama budget at least EUR 200,000 PER EPISODE with "
              "local spend at least EUR 70,000 per series.\n"
              "(2) POST-PRODUCTION — a graduated local-spend ladder that sets the RATE itself: "
              "EUR 30,000 qualifies for 20%; EUR 50,000 for 25%; EUR 80,000 for the maximum 30%. "
              "Post-production submissions must be made via a local Estonian company.\n\n"
              "APPLICANT GATE: international production companies apply by co-producing with an "
              "Estonian production company or by using an Estonian production service — hence "
              "local_entity_required=True. FORWARD-LOOKING RATE CHANGE NOT ASSERTED: reporting "
              "states the rebate rate was PLANNED to increase to 40% in 2026. As at this access "
              "date the guidelines reviewed publish 30% as the maximum, and no confirmation of "
              "the increase taking effect was found, so 30% is recorded and the planned change is "
              "noted in additional_facts as an open item rather than treated as in force. All "
              "thresholds stated in EUR and recorded in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY; no "
              "USD field populated.",
    ),
    additional_facts={
        "production_thresholds_eur": "Paired budget + local-spend test by format — feature film: budget at least EUR 1,000,000 and local spend at least EUR 200,000; feature documentary: budget at least EUR 200,000 and local spend at least EUR 70,000; animation: budget at least EUR 250,000 and local spend at least EUR 70,000; animation series: budget at least EUR 500,000 and local spend at least EUR 70,000 per series; high-end TV drama: budget at least EUR 200,000 per episode and local spend at least EUR 70,000 per series.",
        "post_production_rate_ladder_eur": "Local spend determines the rate for post-production work: EUR 30,000 → 20%; EUR 50,000 → 25%; EUR 80,000 → 30% (maximum). Submissions must be made via a local Estonian company.",
        "applicant_route": "International companies apply by co-producing with an Estonian production company or by using an Estonian production service.",
        "planned_rate_increase": "Reporting states the rate was planned to rise to 40% in 2026. Not confirmed as in force in the guidelines reviewed on 2026-07-26; 30% recorded as the current published maximum. Open item for re-verification.",
    },
))


register(ProgramRequirementsProfile(
    program_slug="rs_film_commission_cash_rebate", jurisdiction_code="RS",
    local_entity_required=True,        # applicant must be a legal entity registered in Serbia and liable for Serbian taxes on the production
    cultural_test_required=False,      # no cultural test published; eligibility runs on format and spend thresholds
    preapproval_mandatory=True,        # application to Film Center Serbia; Committee approval precedes release of funds
    refundable=True,                   # cash rebate paid out
    transferable=False,
    payment_timing=TimingFact(
        value="Rebate released within 60 days of the Committee's final approval to a designated "
              "Treasury account; the applicant must then transfer the funds to the investor "
              "within 10 days",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    evidence=EvidenceRecord(
        source_title="Film Incentives — Film Center Serbia (FCS) / Film in Serbia",
        source_url="https://www.fcs.rs/en/industry-guide/film-incentives/",
        issuing_authority="Film Center Serbia (Filmski centar Srbije); Government of the Republic of Serbia",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Film Center Serbia official industry-guide pages. RATE STRUCTURE BY FORMAT AND "
              "SCALE (three distinct rates, recorded distinctly rather than blended): 25% base "
              "cash rebate on qualifying Serbian spend for features, TV series, documentaries, "
              "animation and post-production — matching the 0.25 rate already in this "
              "repository's rate rules; 20% for TV COMMERCIALS (a LOWER rate, not an uplift); and "
              "30% where Serbian spend is at least EUR 5,000,000 (a scale-based uplift). MINIMUM "
              "SPEND BY FORMAT: EUR 300,000 feature films and TV films; EUR 150,000 PER EPISODE "
              "for TV series; EUR 150,000 animated films, audiovisual post-production and "
              "special-purpose films; EUR 50,000 documentary films and TV programmes. APPLICANT "
              "GATE: the applicant must be a LEGAL ENTITY REGISTERED IN SERBIA and responsible "
              "for paying all relevant Serbian taxes on behalf of the production. QUALIFYING "
              "SPEND EXCLUSION (published, recorded rather than inferred): VAT is NOT qualifying "
              "Serbian spend. PAYMENT MECHANICS, unusually specific and material to cash-flow "
              "planning: the rebate is released within 60 days of the Committee's final approval "
              "to a designated Treasury account, and the applicant is then obliged to transfer "
              "the funds to the investor within 10 days. All thresholds stated in EUR and "
              "recorded in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY; no USD field populated. No annual "
              "programme cap or per-project cap is published in the pages reviewed.",
    ),
    additional_facts={
        "rate_structure": "25% base for features, TV series, documentaries, animation and post-production; 20% for TV commercials (a lower rate, not an uplift); 30% where Serbian spend is at least EUR 5,000,000.",
        "min_spend_by_format_eur": "EUR 300,000 feature films and TV films; EUR 150,000 per episode for TV series; EUR 150,000 animated films, AV post-production and special-purpose films; EUR 50,000 documentary films and TV programmes.",
        "thirty_percent_threshold_eur": "Serbian spend of at least EUR 5,000,000 qualifies for the 30% rate.",
        "vat_exclusion": "VAT is expressly NOT qualifying Serbian spend.",
        "payment_mechanics": "Released within 60 days of the Committee's final approval to a designated Treasury account; applicant must transfer to the investor within 10 days.",
        "applicant_gate": "Legal entity registered in Serbia, responsible for paying all relevant Serbian taxes on behalf of the production.",
        "caps": "No annual programme cap and no per-project cap published in the pages reviewed.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="tw_bamid_rebate", jurisdiction_code="TW",
    local_entity_required=False,       # foreign productions apply directly or via a Taiwan-based production partner; no evidence of a mandatory local-entity gate
    cultural_test_required=False,      # no points-based cultural test published; eligibility runs on origin exclusion + spend + director-award carve-out
    preapproval_mandatory=True,        # BAMID application and selection precede the rebate; program is described as competitive/selective, not an automatic entitlement
    refundable=True,                   # cash rebate paid on qualifying spend
    transferable=False,
    evidence=EvidenceRecord(
        source_title="Taiwan Film/TV Production Cash Rebate — industry summaries corroborating BAMID's published terms",
        source_url="https://www.productionservicenetwork.com/film-incentives/",
        issuing_authority="Bureau of Audiovisual and Music Industry Development (BAMID), Ministry of Culture, Taiwan",
        source_type=SourceType.SECONDARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="BAMID's own program pages (taiwancinema.bamid.gov.tw) were attempted directly twice "
              "and returned HTTP 522 (origin unreachable) both times — a future primary-verification "
              "pass should retry https://taiwancinema.bamid.gov.tw/EngAssistant/EngAssistantContent/"
              "?ContentUrl=5 rather than re-searching from scratch. In the meantime this profile is "
              "built from two independent secondary industry summaries (Production Service Network and "
              "Mbrella Films) whose figures cross-corroborate arithmetically: PSN's TWD caps (30,000,000 "
              "feature / 20,000,000 series) convert at ~30.5 TWD/USD to Mbrella's stated USD caps "
              "(984,000 / 656,000), and PSN's TWD minimum-spend figures (30,000,000 feature / "
              "60,000,000 series) likewise match Mbrella's USD figures (984,000 / 2,000,000) under the "
              "same rate — independent convergence, not a single source repeated. RATE: flat 30% cash "
              "rebate on qualifying Taiwan production expenditure — this matches and corroborates the "
              "0.30 rate already carried in this repository's rate rules (program_rate_rules_worldwide.py, "
              "citing bamid.gov.tw directly for the base rate). EXPENDITURE-CATEGORY ALLOCATION CAPS "
              "(a genuine structural fact, not merely descriptive): of the rebated spend, personnel costs "
              "are capped at 45%, pre- and post-production expenses at 35%, and insurance/transportation/"
              "lodging at 20% — recorded in additional_facts rather than modeled as a rate condition since "
              "it governs cost-category composition, not eligibility. DIRECTOR-AWARD CARVE-OUT: the "
              "standard minimum-spend threshold (TWD 30,000,000 feature / TWD 60,000,000 TV drama series) "
              "drops to TWD 3,000,000 if the director has won Best Director at Cannes, Venice, Berlin or "
              "the Academy Awards (feature films) or International Emmy / Primetime Emmy / Seoul "
              "International Drama Awards (series) — a materially different eligibility path, recorded "
              "distinctly rather than blended into a single figure. ORIGIN EXCLUSION: PSN's page states "
              "the program excludes projects originating from Mainland China, Hong Kong or Macau, and "
              "prohibits Mainland Chinese financing — recorded as a genuine eligibility gate. COMPETITIVE "
              "SELECTION: this repository's existing rate-rule citation (productionservicenetwork.com, a "
              "different page than the one fetched for this profile) already describes the program as "
              "'a highly selective cash rebate to foreign projects... not an automatic entitlement even "
              "if eligibility criteria are met' — carried forward here as preapproval_mandatory=True. "
              "All TWD thresholds recorded in STATUTORY_AMOUNTS_ORIGINAL_CURRENCY per the Canonical "
              "Currency Rule; no USD conversion written to a statutory field. Application process, "
              "specific deadlines, sunset date and annual program cap are NOT recorded here — no source "
              "reviewed (BAMID direct or the two secondary summaries) discloses them, and a Structured "
              "Unknown is not appropriate absent evidence the fields definitely exist as a published, "
              "determinable mechanism.",
    ),
    additional_facts={
        "rate": "Flat 30% cash rebate on qualifying Taiwan production expenditure.",
        "min_spend_standard_twd": "Feature films: TWD 30,000,000. TV drama series: TWD 60,000,000.",
        "min_spend_award_director_twd": "Reduced to TWD 3,000,000 (both formats) if the director has won Best Director at Cannes, Venice, Berlin or the Academy Awards (feature films) or International Emmy / Primetime Emmy / Seoul International Drama Awards (series).",
        "caps_twd": "Feature films: TWD 30,000,000. TV drama series: TWD 20,000,000.",
        "expenditure_category_allocation_caps": "Of rebated spend: personnel costs capped at 45%, pre- and post-production expenses at 35%, insurance/transportation/lodging at 20%.",
        "origin_exclusion": "Excludes productions originating from Mainland China, Hong Kong or Macau; Mainland Chinese financing is prohibited.",
        "selection_process": "Described as a highly selective, competitive cash rebate — not an automatic entitlement even where eligibility criteria are met.",
        "primary_source_status": "BAMID's own program pages (taiwancinema.bamid.gov.tw) returned HTTP 522 on two direct fetch attempts (2026-07-26); profile built from two independently cross-corroborating secondary industry summaries pending a successful direct fetch.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="ph_fdcp_flip", jurisdiction_code="PH",
    local_entity_required=True,        # applicant must be organized/registered as a business in the Philippines and an active member of the FDCP National Registry
    cultural_test_required=False,      # the base 20% rebate has no cultural test; the Cultural Bonus (+5% to 25%) is a separate, optional merit test — modeled distinctly below, not as a blanket requirement
    preapproval_mandatory=True,        # pre-production application through one of two annual cycles; principal photography must not begin before grant issuance
    expenditure_before_approval_qualifies=False,  # photography/post-production must commence AFTER grant issuance, within 6 months of it
    min_shoot_days=None,               # not published as a distinct shoot-day gate; eligibility runs on QPPE spend thresholds by format instead
    application_deadline=TimingFact(
        value="Two annual cycles: Cycle 1 — applications February, evaluation March, "
              "announcement April. Cycle 2 — applications July, evaluation August, "
              "announcement September.",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    audit_or_final_certification_deadline=TimingFact(
        value="Principal photography or post-production must commence within 6 months of "
              "grant issuance; the project must be completed within 12 months of grant "
              "issuance (18 months for animation)",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    refundable=True,                   # cash rebate paid on qualifying spend
    transferable=False,
    evidence=EvidenceRecord(
        source_title="Film Location Incentive Program (FLIP) — official program page",
        source_url="https://fdcp.ph/programs/film-incentives/film-location-incentive-program",
        issuing_authority="Film Development Council of the Philippines (FDCP), through the Film Philippines Office (FPO)",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Fetched directly from FDCP's own official FLIP program page. RATE STRUCTURE: "
              "base 20% cash rebate on Qualified Philippine Production Expenditure (QPPE), "
              "capped at PHP 25,000,000 (~USD 424,000 at the source's own conversion note); "
              "an OPTIONAL Cultural Bonus of +5% (to 25%) is available on passing a cultural "
              "merit test, which raises the cap to PHP 30,000,000 (~USD 508,000) — this "
              "corroborates and refines the 20-25% band already carried in this repository's "
              "rate rules (program_rate_rules_worldwide.py, PH_DOCTRINE), and resolves that "
              "rule's previously-unconfirmed uplift criteria (it is an optional cultural test, "
              "not an automatic scale threshold). The two caps are DISTINCT (PHP 25M at 20% vs "
              "PHP 30M at 25%), recorded separately rather than blended into one figure. MINIMUM "
              "QPPE BY FORMAT: PHP 20,000,000 live-action/animated feature films; PHP 8,000,000 "
              "documentaries; PHP 3,000,000 per episode for TV/VOD series of at least 8 episodes "
              "(PHP 24,000,000 aggregate at the minimum episode count). APPLICANT GATE: the "
              "applicant must be organized and registered as a business in the Philippines AND "
              "an active member of the FDCP National Registry — both conditions, not either/or. "
              "CURRENCY/PAYMENT MECHANIC: all qualifying expenses must be paid by the applicant's "
              "company in Philippine peso through Filipino-registered businesses and/or "
              "individuals — recorded as a genuine payment-channel constraint, not merely a "
              "currency-of-account note. PRE-PRODUCTION APPLICATION REQUIRED: two annual cycles "
              "(Cycle 1: Feb application/Mar evaluation/Apr announcement; Cycle 2: Jul "
              "application/Aug evaluation/Sep announcement) — principal photography or "
              "post-production must not begin before the grant is issued. PRODUCTION TIMELINE "
              "GATE: must commence within 6 months of grant issuance and complete within 12 "
              "months (18 months for animation) — recorded as the audit/certification deadline "
              "since it is the statutory window within which the qualifying spend must occur to "
              "remain eligible for the confirmed rebate. FINAL VERIFICATION: certified true "
              "copies of receipts, invoices and service contracts must be submitted to FDCP for "
              "review before the final rebate amount is confirmed. CONTENT EXCLUSION: any genre "
              "is eligible except pornography, or content that insults/negatively portrays the "
              "Philippines, threatens national security, or promotes violence — recorded as a "
              "genuine content gate. No sunset date is published on the page reviewed. Eligible "
              "formats: features, animated films, documentaries, TV/streaming series, and "
              "virtual reality content. All PHP thresholds recorded in "
              "STATUTORY_AMOUNTS_ORIGINAL_CURRENCY per the Canonical Currency Rule; no USD "
              "conversion written to a statutory field (the source's own USD approximations are "
              "quoted in this note for context only, never stored as the authoritative figure).",
    ),
    additional_facts={
        "rate_structure": "Base 20% of QPPE, capped at PHP 25,000,000. Optional Cultural Bonus test adds 5% (to 25%), raising the cap to PHP 30,000,000.",
        "min_qppe_by_format_php": "Feature films (live-action/animated): PHP 20,000,000. Documentaries: PHP 8,000,000. TV/VOD series (min. 8 episodes): PHP 3,000,000 per episode.",
        "applicant_gate": "Must be organized/registered as a business in the Philippines AND an active member of the FDCP National Registry.",
        "payment_channel_constraint": "All qualifying expenses must be paid by the applicant's company in Philippine peso through Filipino-registered businesses and/or individuals.",
        "application_cycles": "Cycle 1: applications February, evaluation March, announcement April. Cycle 2: applications July, evaluation August, announcement September.",
        "production_timeline_gate": "Must commence within 6 months of grant issuance; must complete within 12 months (18 months for animation).",
        "final_verification": "Certified true copies of receipts, invoices and service contracts submitted to FDCP for review before the final rebate amount is confirmed.",
        "content_exclusion": "Any genre eligible except pornography, or content that insults/negatively portrays the Philippines, threatens national security, or promotes violence.",
        "eligible_formats": "Features, animated films, documentaries, TV/streaming series, virtual reality content.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="cl_corfo_incentive", jurisdiction_code="CL",
    local_entity_required=False,       # foreign companies may apply DIRECTLY; co-execution with a Chilean partner is one route, not the only one
    local_coproducer_required=False,   # NOT a stated mandatory gate — direct foreign application is explicitly permitted; all 2025 first-call winners happened to use local co-execution partners, an operational pattern recorded in evidence rather than modeled as a requirement
    cultural_test_required=False,      # no cultural test published; eligibility runs on spend threshold and, for the 40% tier, shoot-region
    preapproval_mandatory=True,        # competitive call-based selection (only 6 winning projects named in the first 2025 call) — not an automatic entitlement
    allocation_type=AllocationType.COMPETITIVE,
    refundable=True,                   # cash rebate paid on qualifying spend
    transferable=False,
    evidence=EvidenceRecord(
        source_title="Ministerios de las Culturas, de Economia y Corfo presentan segunda convocatoria del programa IFI Audiovisual 2025",
        source_url="https://www.cultura.gob.cl/convocatorias/ministerios-de-las-culturas-de-economia-y-corfo-presentan-segunda-convocatoria-del-programa-ifi-audiovisual-2025/",
        issuing_authority="Ministerio de las Culturas, las Artes y el Patrimonio (Chile); Corfo (Corporacion de Fomento de la Produccion); Ministerio de Economia, Fomento y Turismo",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="Fetched directly from the Chilean Ministry of Culture's own official convocatoria page "
              "for the IFI Audiovisual program ('Programa de Apoyo a Inversiones Audiovisuales de Alto "
              "Impacto'), confirmed to exclusively target foreign productions (positively distinguished "
              "from Chile's separate domestic 'Fondo Audiovisual' (FIA) grant scheme administered by the "
              "same Ministry via fondosdecultura.cl, which is NOT this program and was not used as a "
              "source here — Jurisdiction Isolation Rule applied). MATERIAL DISCREPANCY vs this "
              "repository's existing rate rule (program_rate_rules_worldwide.py, CL_DOCTRINE, citing "
              "ep.com): the repo models a FLAT 40% rate with USD 1,000,000 minimum spend. The governing "
              "mechanism actually verified here is TIERED: 30% base rate capped at USD 3,000,000, rising "
              "to 40% ONLY for productions filmed ENTIRELY OUTSIDE the Santiago Metropolitan Region (a "
              "geographic condition, not a flat entitlement) — corroborated independently by "
              "blog.investchile.gob.cl (InvestChile, the government's own investment-promotion agency) "
              "and this Ministry of Culture page, both agreeing on 30%/USD 3,000,000 base and the "
              "regional-uplift structure for the 40% tier. Minimum spend is also disputed: IMDb/Variety "
              "industry press (citing the program's own bases) states USD 2,000,000, not the USD "
              "1,000,000 in the existing rate rule. NEITHER the rate rule nor its conditions were altered "
              "in this phase (calculation logic frozen) — the discrepancy is preserved here and in "
              "additional_facts for a future reconciliation pass. APPLICANT GATE: foreign companies may "
              "apply DIRECTLY to Corfo, or through a co-execution agreement with a Chilean production "
              "company in which the foreign entity must be the MAJORITY investment contributor if that "
              "route is chosen — recorded as an optional structure, not a mandatory local-partner gate, "
              "even though all six winning projects in the first 2025 call (Amazon Studios/Fabula "
              "Servicios, Netflix/Fabula Servicios, and others) in practice used Chilean co-execution "
              "partners. COMPETITIVE SELECTION: the program runs periodic calls (convocatorias) with a "
              "fixed total budget per cycle — CLP 2,168,000,000 for the 2025 cycle — and awards a small, "
              "named set of winning projects (six in the first 2025 call), confirming this is COMPETITIVE "
              "allocation, not first-come-first-served or entitlement. CURRENT CYCLE: the second 2025 "
              "call ran 2025-09-05 to 2025-09-29; the program has run recurring annual/biennial calls "
              "(a 2024 call closed 2024-12-31, followed by two calls in 2025), indicating an ongoing, "
              "recurring program rather than a one-time initiative, though no specific 2026 IFI "
              "Audiovisual call date was confirmed in the sources reviewed (a separate, differently-named "
              "'Fondo Audiovisual 2026' bases document was found but explicitly NOT used here as it is "
              "the distinct domestic fund, not IFI Audiovisual). ELIGIBLE EXPENSES: filming, artistic "
              "production, assembly/editing, copyright management, and post-production. All USD figures "
              "recorded as published (no CLP conversion performed for the caps/min-spend, which the "
              "authorities themselves state in USD); the CLP total-budget figure is recorded natively per "
              "the Canonical Currency Rule, stored separately from the USD-denominated project-level "
              "terms rather than converted into either currency.",
    ),
    additional_facts={
        "material_discrepancy_vs_rate_rule": "Repo's rate rule models a flat 40% / USD 1,000,000 min spend. Verified governing mechanism is 30% base (cap USD 3,000,000) rising to 40% only for productions filmed entirely outside the Santiago Metropolitan Region; verified min spend is USD 2,000,000 per IMDb/Variety industry press citing the program's own bases. Rate rule NOT altered (calculation logic frozen this phase).",
        "rate_structure": "30% base rate, capped at USD 3,000,000. 40% for productions filmed entirely outside the Santiago Metropolitan Region.",
        "applicant_gate": "Foreign companies may apply directly to Corfo, or via a co-execution agreement with a Chilean production company (foreign entity must be majority investor in that structure). Not a mandatory local-partner requirement.",
        "competitive_selection": "Periodic competitive calls (convocatorias) with a fixed total budget per cycle; only a small named set of projects win each call (six in the first 2025 call).",
        "program_identity": "Full name: 'Programa de Apoyo a Inversiones Audiovisuales de Alto Impacto - IFI Audiovisual.' Exclusively for foreign productions. Distinct from Chile's separate domestic Fondo Audiovisual (FIA) grant scheme.",
        "eligible_expenses": "Filming, artistic production, assembly/editing, copyright management, post-production.",
        "recent_cycles": "2024 call closed 2024-12-31. Two 2025 calls; second ran 2025-09-05 to 2025-09-29. No specific 2026 IFI Audiovisual call date confirmed in sources reviewed.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_ky_keiia", jurisdiction_code="US-KY",
    local_entity_required=True,        # 307 KAR 1:080E: "Applicants must be Kentucky-based companies" -- a MATERIAL CORRECTION to this repository's own DISCOVERY-tier entry (global_inventory_extended.py), which had recorded requires_local_entity=False
    cultural_test_required=False,      # not mentioned anywhere in the regulation text retrieved or in any of this repository's three pre-existing internal records, all of which agree on no cultural test
    preapproval_mandatory=True,        # application + Cabinet review + Economic Analysis Scoring precede any credit; production must affirm it would not film in Kentucky "but for" the incentive
    expenditure_before_approval_qualifies=False,  # 50% of project funds must be shown as committed (bonds/payroll/bank statements/financing contracts, 25% in escrow) as part of the application itself, consistent with a pre-approval structure
    allocation_type=AllocationType.DISCRETIONARY,  # scored application: below 60 points denied; 90+ points with USD 7,500,000+ QPE qualifies as "high-impact" -- a real scoring gate, not a pure entitlement
    audit_required=True,
    cpa_or_approved_auditor_required=True,  # "certified audit ... conducted in accordance with the Kentucky Entertainment Incentive Program Certified Audit Guidelines"
    refundable=True,                   # consistent across all three pre-existing internal records; not contradicted by the regulation text retrieved
    transferable=False,                # consistent across all three pre-existing internal records; not contradicted by the regulation text retrieved
    evidence=EvidenceRecord(
        source_title="Title 307 Chapter 1 Regulation 080 (307 KAR 1:080E) — Kentucky Entertainment Incentive Program",
        source_url="https://apps.legislature.ky.gov/law/kar/titles/307/001/080/",
        issuing_authority="Kentucky Cabinet for Economic Development; Kentucky Legislative Research Commission",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST (per standing instruction): this repository already carried "
              "THREE internal records for Kentucky before any external research began this session -- a "
              "DISCOVERY-tier entry (global_inventory_extended.py: 30% base, +5% uplift 'if KY local "
              "companies provide goods/services', min spend USD 500,000, no cap), a PARSED "
              "JurisdictionIncentiveProfile (jurisdiction_comparison.py: 30%/35%, USD 250,000/20,000 min "
              "spend by format, USD 75,000,000 annual cap), and a PARSED rate rule "
              "(program_rate_rules_worldwide.py, US_KY_DOCTRINE, citing shamelstudio.com + revenue.ky.gov: "
              "confirms 30% base, notes the 35% uplift criteria as 'not disclosed by the source checked'). "
              "The DISCOVERY entry's own note ALREADY ANSWERS that gap ('+5% if KY local companies provide "
              "goods/services') -- this internal fact was reconciled rather than re-derived externally. "
              "MATERIAL, VERY RECENT STATUTORY CHANGE FOUND: the Kentucky General Assembly passed 2026 Ky. "
              "Acts ch. 194, secs. 2-6 (2026 SB 324), and the Cabinet for Economic Development filed both "
              "an emergency amendment (307 KAR 1:080E) and an identical ordinary amendment (307 KAR 1:080) "
              "to this program's governing regulation on 2026-07-15 -- eleven days before this profile was "
              "written. This is the CURRENT governing regulation, fetched directly from the Kentucky "
              "Legislative Research Commission (apps.legislature.ky.gov), and it does NOT restate a "
              "rate/percentage figure in the text retrieved, so the existing 30%/35% rate rule is NEITHER "
              "confirmed NOR contradicted by this source -- recorded as an open item, not silently assumed "
              "unchanged. What IS newly and directly confirmed from the regulation text: (1) APPLICANT "
              "GATE -- applicants must be Kentucky-based companies (a genuine correction to the DISCOVERY "
              "entry's requires_local_entity=False); (2) BUT-FOR TEST -- the applicant must affirm the "
              "production would not film or produce in Kentucky but for the incentive; (3) FINANCING-PROOF "
              "GATE -- 50% of project funds must be shown as committed (bonds, payroll statements, bank "
              "statements, financing contracts, or commitment letters with 25% held in escrow) as part of "
              "the application -- a distinct concept from min_local_spend_usd and not modeled as one; (4) "
              "QUALIFYING EXPENDITURE CATEGORIES -- nine categories under KRS 154.61-010(25), each only "
              "counted when paid to a Kentucky vendor; (5) CERTIFIED AUDIT REQUIRED -- per the program's "
              "own Certified Audit Guidelines; (6) FEE STRUCTURE -- application fee USD 250-1,000 tiered "
              "by project budget, administrative fee 0.5% of estimated incentives sought (minimum USD "
              "500), and a nonrefundable USD 2,000 agreement fee; (7) ECONOMIC ANALYSIS SCORING -- "
              "applications scoring below 60 points are denied; applications scoring above 90 points AND "
              "with USD 7,500,000+ in qualifying expenditures qualify for a 'high-impact' designation -- "
              "this is a genuinely new, previously-unknown structural fact establishing the program as "
              "discretionary/scored rather than a pure entitlement, contradicting no prior record (none of "
              "the three prior internal records disclosed an allocation_type); (8) REVIEW TIMELINE -- the "
              "Cabinet has 20 calendar days to notify an applicant of receipt and initial eligibility "
              "determination. The USD 75,000,000 annual cap was INDEPENDENTLY RE-CONFIRMED as still "
              "current via FilmKentucky.org (Kentucky Film Office's own site, fetched 2026-07-26: '$75 "
              "Million Available Annually', '270+ Productions Incentivized', '$795M Spent in Kentucky' "
              "since 2022) -- this figure survives the SB 324 rewrite unchanged. The USD 250,000 / USD "
              "20,000 minimum-spend figures were NOT independently re-confirmed against the post-SB-324 "
              "regulation text and are carried forward from the pre-existing internal record with that "
              "caveat now made explicit rather than silently assumed current.",
    ),
    additional_facts={
        "applicant_gate": "Must be a Kentucky-based company (307 KAR 1:080E) -- corrects the prior DISCOVERY-tier requires_local_entity=False.",
        "but_for_test": "Applicant must affirm the production would not film or produce in Kentucky but for the incentive.",
        "financing_proof_gate": "50% of project funds must be shown as committed via bonds, payroll statements, bank statements, financing contracts, or commitment letters, with 25% held in escrow.",
        "qualifying_expenditure_categories": "Nine categories under KRS 154.61-010(25); only counted when paid to a Kentucky vendor.",
        "fee_structure": "Application fee USD 250-1,000 (tiered by project budget); administrative fee 0.5% of estimated incentives sought (min USD 500); nonrefundable agreement fee USD 2,000.",
        "economic_analysis_scoring": "Applications scoring below 60 points are denied. Applications scoring above 90 points AND with USD 7,500,000+ in qualifying expenditures qualify as 'high-impact.'",
        "review_timeline": "Cabinet has 20 calendar days to notify an applicant of receipt and initial eligibility determination.",
        "rate_uplift_from_internal_discovery_record": "The +5% uplift (30% to 35%) applies when Kentucky local companies provide goods/services to the production -- resolved from this repository's own pre-existing DISCOVERY-tier note, not re-derived externally.",
        "recent_statutory_change": "2026 Ky. Acts ch. 194, secs. 2-6 (2026 SB 324) amended the program; the Cabinet filed emergency + ordinary amendments to 307 KAR 1:080, effective 2026-07-15 -- 11 days before this profile was written. The rate/percentage structure was not restated in the regulation text retrieved and is neither confirmed nor contradicted by this source.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_md_film_production_activity_credit", jurisdiction_code="US-MD",
    local_entity_required=False,       # not stated as a gate on commerce.maryland.gov or in Tax-General Sec. 10-730; the "Maryland Small Film" alternate track requires Maryland organization/activity, but that is a category-specific condition, not a blanket applicant gate
    cultural_test_required=False,      # not mentioned in the official page or the statute section reviewed
    preapproval_mandatory=True,        # "Before beginning ANY work" an Application for Qualification must be submitted and a Letter of Qualification received
    expenditure_before_approval_qualifies=False,  # application must be submitted prior to any production activity in the state; principal photography must begin within 120 days of the Letter of Qualification
    min_shoot_days=None,               # not published as a distinct gate
    allocation_type=AllocationType.FIRST_COME_FIRST_SERVED,  # confirmed directly ("first-come, first-served basis") -- CORRECTS this repository's own DISCOVERY-tier note, which had guessed "competitive"
    application_deadline=TimingFact(
        value="Application for Qualification must be submitted before any production activity "
              "begins in Maryland. The Department issues a Letter of Qualification (or denial) "
              "within 30 days of a complete application. Principal photography must begin within "
              "120 days of receiving the Letter of Qualification (extendable for circumstances "
              "beyond the applicant's control).",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    audit_or_final_certification_deadline=TimingFact(
        value="Final certification must be requested no later than 180 days after the production "
              "activity's completion date (extendable at the Department's discretion). Productions "
              "with authorized direct costs exceeding USD 250,000 require an independent "
              "third-party CPA audit using Agreed-Upon Procedures, with a Department-approved "
              "draft engagement letter in place before principal photography concludes. Maryland "
              "Small Films are exempt from the audit requirement.",
        basis=TimingBasis.STATUTORY_DEADLINE,
    ),
    audit_required=True,               # for standard productions (>USD 250,000); Small Film category is exempt -- recorded as a general True with the exemption disclosed in additional_facts, consistent with how format-specific exceptions are handled elsewhere in this registry
    cpa_or_approved_auditor_required=True,
    refundable=True,                   # "if the tax credit allowed in any taxable year exceeds the total tax otherwise payable... the film production entity may claim a refund"
    transferable=False,                # no transferability mechanism found in any source reviewed; consistent with all three pre-existing internal records
    evidence=EvidenceRecord(
        source_title="Film Production Activity Tax Credit — official program page",
        source_url="https://commerce.maryland.gov/fund/film-production-activity-tax-credit",
        issuing_authority="Maryland Department of Commerce",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST (per standing instruction): this repository already "
              "carried a DISCOVERY-tier entry (global_inventory_extended.py: up to 27%, min spend "
              "USD 500,000, annual cap USD 25,000,000, noted as 'competitive') and a PARSED "
              "JurisdictionIncentiveProfile + rate rule already corrected once from a stale 25% to "
              "28% via this same commerce.maryland.gov page (annual cap USD 12,000,000 for FY2026). "
              "The jurisdiction_comparison.py profile carried an explicit data_gaps note flagging "
              "that no ProgramRequirementsProfile existed and a primary-source pass was needed -- "
              "this profile fulfills that flagged gap directly. KNOWLEDGE RECONCILIATION PERFORMED "
              "AT THE APPROPRIATE LEVEL (per standing instruction): re-fetching the SAME official "
              "page surfaced material ADDITIVE facts not previously on record anywhere in this "
              "repository, which were propagated to the PARSED-tier artifacts that already trusted "
              "this source (program_rate_rules_worldwide.py US_MD_DOCTRINE gained a new 30% "
              "television-series tier and a 'Maryland Small Film' alternate-qualification tier; "
              "jurisdiction_comparison.py's _US_MARYLAND profile's max_rate/min_spend_local/notes "
              "were updated and its now-resolved data_gaps entry was replaced) -- this is a "
              "same-source refinement, not a conflicting Material Discrepancy, so it was not left "
              "unresolved. The DISCOVERY-tier catalog entry (global_inventory_extended.py) was "
              "deliberately left untouched, consistent with the Discovery Provenance Ledger's frozen "
              "classification of that layer; its 'competitive' guess is now known to be incorrect "
              "(the program is first-come-first-served) and that correction lives in the PARSED-tier "
              "artifacts instead. NEW FACTS CONFIRMED FOR THIS PROFILE SPECIFICALLY: TWO-TIER RATE "
              "-- standard productions up to 28%, television series up to 30% (a format-specific "
              "uplift, not a discretionary band); MARYLAND SMALL FILM alternate track -- min spend "
              "USD 25,000 (vs USD 250,000 standard), credit capped at USD 125,000 total, exempt "
              "from the independent-CPA-audit requirement, but gated on the applicant being "
              "independently owned, having 25 or fewer full-time employees, not being dominant in "
              "its field, and having been organized and active in Maryland for at least 3 months; "
              "PREAPPROVAL MECHANICS -- Application for Qualification must be filed before any "
              "production activity begins in Maryland; Department issues a Letter of Qualification "
              "(or denial) within 30 days; principal photography must commence within 120 days of "
              "that letter (extendable for circumstances beyond the applicant's control); FINAL "
              "CERTIFICATION -- must be requested within 180 days of the completion date "
              "(Department-extendable); AUDIT -- productions over USD 250,000 require an "
              "independent third-party CPA audit under Agreed-Upon Procedures, with a "
              "Department-approved draft engagement letter in place before principal photography "
              "concludes; ALLOCATION MECHANISM -- confirmed first-come-first-served against the "
              "FY2027 USD 12,000,000 certification cap (not competitive scoring); MIN SPEND -- USD "
              "250,000 standard, independently corroborated via Tax-General Article Sec. 10-730 "
              "(law.justia.com). No sunset date and no content-type restriction were found in any "
              "source reviewed. All USD figures are natively published in USD by the authority "
              "(Maryland is a US state); no currency conversion involved.",
    ),
    additional_facts={
        "rate_structure": "Standard productions: up to 28% of authorized direct costs. Television series: up to 30%. Maryland Small Film category: up to 28%, but credit capped at USD 125,000 total regardless of rate.",
        "maryland_small_film_track": "Alternate qualification track: min spend USD 25,000 (vs USD 250,000 standard), credit capped at USD 125,000, exempt from independent CPA audit. Requires independently-owned applicant, <=25 FTEs, not dominant in its field, organized/active in Maryland 3+ months.",
        "preapproval_process": "Application for Qualification filed before any production activity begins; Letter of Qualification (or denial) issued within 30 days; principal photography must begin within 120 days of that letter.",
        "final_certification": "Must be requested within 180 days of completion date (Department-extendable).",
        "audit_mechanics": "Productions over USD 250,000: independent third-party CPA audit under Agreed-Upon Procedures, with a Department-approved draft engagement letter in place before principal photography concludes. Maryland Small Films exempt.",
        "allocation_mechanism": "First-come-first-served against the FY2027 USD 12,000,000 certification cap -- corrects this repository's own prior DISCOVERY-tier 'competitive' guess.",
        "min_spend_corroboration": "USD 250,000 standard minimum independently corroborated via Tax-General Article Sec. 10-730 (law.justia.com), in addition to the official commerce.maryland.gov page.",
        "knowledge_reconciliation_note": "Same-source additive refinement of commerce.maryland.gov also propagated to program_rate_rules_worldwide.py (US_MD_DOCTRINE: added TV-series and Small-Film tiers) and jurisdiction_comparison.py (_US_MARYLAND: max_rate/min_spend_local/notes updated, resolved data_gaps entry replaced) -- not merely recorded in this Requirements Profile alone.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="us_mn_film_production_credit", jurisdiction_code="US-MN",
    local_entity_required=False,       # not stated as a gate on revenue.state.mn.us
    cultural_test_required=False,      # not mentioned in the official page; consistent with all pre-existing internal records
    preapproval_mandatory=True,        # applicants apply through Explore Minnesota Film for eligibility determination and credit allocation before claiming
    allocation_type=AllocationType.FIRST_COME_FIRST_SERVED,
    transferable=True,                 # "assignable income tax credit"; certificate holders may assign to another taxpayer -- CORRECTS this repository's own prior None/False guesses across all three existing internal records
    transfer_approval_required=True,   # "the credit must be assigned prior to claiming any portion of the credit" -- a sequencing gate on the assignment itself, recorded as an approval-like precondition rather than a free market transfer
    evidence=EvidenceRecord(
        source_title="Film Production Tax Credit — official program page",
        source_url="https://www.revenue.state.mn.us/film-production-credit",
        issuing_authority="Minnesota Department of Revenue; Explore Minnesota Film",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-07-26",
        notes="REPOSITORY RECONCILIATION FIRST (per standing instruction): this repository already "
              "carried a DISCOVERY-tier entry (global_inventory_wave2.py: 25%, min spend USD "
              "1,000,000, annual cap USD 25,000,000, refundable=True, transferable=False) whose own "
              "source_url WAS this exact revenue.state.mn.us page -- but the PARSED-tier rate rule "
              "and jurisdiction_comparison.py profile had only ever cited greenslate.com (a secondary "
              "aggregator) for the regional-add-on disclosure, never fetching the DISCOVERY entry's "
              "own cited official page directly. This profile closes that gap by fetching it. "
              "KNOWLEDGE RECONCILIATION PERFORMED AT THE APPROPRIATE LEVEL (per standing instruction): "
              "the direct fetch surfaced a genuine CORRECTION -- Minnesota's credit is explicitly an "
              "'assignable income tax credit' and 'certificate holders may assign their credit to "
              "another taxpayer' -- i.e. TRANSFERABLE, contradicting the DISCOVERY entry's "
              "is_transferable=False guess (which was never corroborated at the PARSED tier either, "
              "both PARSED records left is_transferable=None). This correction was propagated to "
              "program_rate_rules_worldwide.py (US_MN_DOCTRINE: is_transferable=True, min_spend_usd "
              "and annual_cap_usd now populated) and jurisdiction_comparison.py (_US_MINNESOTA: same "
              "fields updated, authority_name corrected from 'Minnesota Film & TV Board' to 'Explore "
              "Minnesota Film' -- the page confirms applications now run through Explore Minnesota "
              "Film's own portal, mnfilmtv.org, which has evidently superseded the previously-cited "
              "nonprofit board as the administering body). CONFIRMED DIRECTLY: min spend USD "
              "1,000,000 in any 12 consecutive months (matches and confirms the DISCOVERY figure); "
              "annual cap USD 25,000,000 (matches and confirms the DISCOVERY figure); allocation is "
              "first-come-first-served (a new fact, not previously recorded anywhere in this "
              "repository); the assignment of the credit must occur BEFORE any portion of it is "
              "claimed -- a genuine sequencing constraint on transfer, recorded as "
              "transfer_approval_required=True since it functions as a procedural precondition on the "
              "transfer rather than a free-market resale. REGIONAL ADD-ON REBATES (carried forward, "
              "not independently modeled): Iron Range Regional Production Incentive Program, St. "
              "Louis County local film rebate, City of Duluth Production Incentive Program, Incredible "
              "Austin Minnesota Film Rebate, and Maple Lake Film Rebate -- too granular/local for a "
              "single Requirements Profile; disclosed in additional_facts rather than silently dropped. "
              "REFUNDABILITY was NOT explicitly stated on the official page (the DISCOVERY entry's "
              "refundable=True claim remains uncorroborated at the PARSED/PRIMARY tier) -- left as None "
              "on this profile rather than asserted, and the resulting gap recorded in "
              "jurisdiction_comparison.py's data_gaps rather than silently inherited as fact. No sunset "
              "date and no eligible-expenditure-category detail were found on the page reviewed.",
    ),
    additional_facts={
        "rate_and_thresholds": "25% assignable income tax credit. Min spend USD 1,000,000 in any 12 consecutive months. Annual cap USD 25,000,000, first-come-first-served.",
        "transferability_correction": "Confirmed 'assignable income tax credit'; credit must be assigned before any portion is claimed. Corrects this repository's own prior is_transferable=False (DISCOVERY) / None (PARSED) records.",
        "administering_authority_correction": "Applications now run through Explore Minnesota Film (mnfilmtv.org), which has superseded the previously-cited 'Minnesota Film & TV Board' in this repository's records.",
        "regional_addon_rebates_not_modeled": "Iron Range Regional Production Incentive Program, St. Louis County local film rebate, City of Duluth Production Incentive Program, Incredible Austin Minnesota Film Rebate, Maple Lake Film Rebate -- too granular/local to model individually.",
        "refundability_unconfirmed": "The official page did not explicitly state refundability; this repository's DISCOVERY-tier refundable=True claim remains uncorroborated at the PRIMARY tier.",
    },
))

register(ProgramRequirementsProfile(
    program_slug="at_fisa_plus", jurisdiction_code="AT",
    local_entity_required=False,       # not stated as a blanket gate by any source reviewed; FISA+ explicitly supports "international films and series (service productions)" as well as Austrian productions, implying foreign applicants can qualify directly rather than only through a mandatory Austrian entity
    cultural_test_required=True,       # points-based Cultural Test conducted by Location Austria -- resolves this repository's own internal inconsistency (DISCOVERY catalog said True, the pre-existing PARSED rate rule and jurisdiction_comparison.py profile both incorrectly said False; both corrected this session)
    cultural_test_points=80,           # maximum obtainable across Parts A+B+C (Annex 3), confirmed 2026-08-19 from the official FISA+ Funding Guidelines for Service Productions 2025-2027 PDF
    cultural_test_threshold=40,        # feature film/fictional series minimum (40 of 80); other formats have lower thresholds -- see additional_facts for the full per-format table
    preapproval_mandatory=True,        # applications submitted via the AWS Funding Manager platform before/during production, consistent with a rebate program requiring approval rather than automatic post-hoc claim
    refundable=True,
    transferable=False,
    evidence=EvidenceRecord(
        source_title="FISA+ Funding Guidelines for Service Productions 2025-2027 (official PDF, Annex 3 Cultural Test) plus independently-converging industry summaries for rate/administration facts",
        source_url="https://api.fisaplus.com/fileadmin/user_upload/FISA__SRL_Serviceproduktionen_2025-2027_EN.pdf",
        issuing_authority="Austria Wirtschaftsservice Gesellschaft mbH (aws), under the Federal Ministry of Labor, Economy, Energy and Tourism; FILM in AUSTRIA (Austrian Film Commission) as first point of contact",
        source_type=SourceType.PRIMARY, status=RecordStatus.CURRENT, access_date="2026-08-19",
        notes="REPOSITORY RECONCILIATION FIRST (per standing instruction): this repository already "
              "carried FOUR internal Austria records before external research began -- a DISCOVERY "
              "entry for FISA+ itself (global_inventory_extended.py: 25%, cultural test required, "
              "min spend EUR 600,000, annual budget ~EUR 20,000,000) plus TWO SEPARATE, correctly "
              "distinguished Austrian programs (ORF Film/Fernseh-Abkommen co-production fund, and "
              "Austrian Film Institute/OFI selective production support) that were positively NOT "
              "conflated with FISA+ here (Jurisdiction Isolation Rule), and a PARSED rate rule + "
              "jurisdiction_comparison.py profile for FISA+ itself, both explicitly self-labelled as "
              "'carried forward unchallenged... not independently re-confirmed' and both carrying "
              "requires_cultural_test=False -- an INTERNAL INCONSISTENCY against the DISCOVERY entry's "
              "own True, never previously reconciled. KNOWLEDGE RECONCILIATION PERFORMED AT THE "
              "APPROPRIATE LEVEL (per standing instruction): external research found the pre-existing "
              "25% figure is STALE and the cultural-test omission was simply wrong -- both corrected "
              "here AND propagated to program_rate_rules_worldwide.py (AT_DOCTRINE: two new tiers, "
              "30% base / 35% with green-filming bonus; requires_cultural_test=True) and "
              "jurisdiction_comparison.py (_AUSTRIA: base_rate/max_rate/requires_cultural_test/"
              "authority_name/notes updated) rather than left isolated in this profile alone. RATE: "
              "the FISA+ scheme was overhauled to a 30% base cash rebate with a +5% green-filming "
              "bonus (35% ceiling) -- confirmed via THREE independently converging secondary sources "
              "(needafixer.com's 2026 rates comparison, progressiveproductions.eu's Austria incentive "
              "page, and Variety's 2023 'Austria Changes the Game With New Incentives' article), all "
              "agreeing on the 30%/35% structure and specifically NOT the 25% this repository had "
              "carried forward. MINIMUM SPEND: EUR 150,000 fiction/feature films, EUR 80,000 "
              "documentaries, EUR 25,000 for animation/VFX/film-music productions -- a genuine "
              "format-tiered structure, also superseding the DISCOVERY entry's single EUR 600,000 "
              "figure (which itself was flagged as a data gap, min_spend_usd, by the catalog's own "
              "unknown_fields list). CULTURAL TEST (RESOLVED 2026-08-19, Worldwide Program Qualification "
              "Completion, Queue B): the exact points threshold WAS found -- the official "
              "'FISA+ Funding Guidelines for Service Productions 2025-2027' PDF "
              "(api.fisaplus.com/fileadmin/user_upload/FISA__SRL_Serviceproduktionen_2025-2027_EN.pdf, "
              "issued pursuant to section 7 of the 2023 Film Location Act of the Austrian Federal "
              "Minister of Economy, Energy and Tourism, in agreement with the Federal Minister of "
              "Finance) was read in full and its Annex 3 ('Cultural Test for International Productions "
              "of Films, Series and Episodes', pp. 56-60) contains the complete, exact point table: "
              "minimum score (of a maximum 80, Parts A-C combined) is 40 for feature film/fictional "
              "series, 35 for animated feature film/fictional series, 28 for documentary film/series "
              "(incl. animated), 25 for production parts with no live-action/digital shooting days. "
              "Part A 'Cultural Content' (max 30 points): Austrian/EEA/Council-of-Europe setting (4), "
              "fictitious-place setting (2), Austrian/European objects filmed (3), Austrian/European "
              "shooting locations (3), Austrian/EEA/CoE main character (3, max 3 combined with the "
              "non-attributable-nationality alternative worth 1), Austrian/European plot source (3), "
              "pre-existing-work basis (2), art-themed plot (1), contemporary non-film artist in a key "
              "role (1), real/fictional public figure plot (2), historic-event plot (2), socio-cultural/ "
              "religious/philosophical topic (3), scientific/natural-phenomena topic (3). Part B 'Film "
              "Professionals' (max 38 points): Austrian/EEA/CoE nationals in listed head-of-department, "
              "acting/performance, VFX/animation-lead, audio-post, visual-post, and music-recording "
              "roles at 2 points/person (24 max); female film professionals in screenwriting/directing/ "
              "cinematography/production at 2 points/person (8 max); trainees at 1 point/trainee (6 "
              "max). Part C 'Production': shooting-days/animation-spend/post-production-spend tiers in "
              "Austria (points vary by category and spend threshold, e.g. 3-9 shooting days = 4 points "
              "up to 15+ days = 6 points; EUR 25,000-100,000+ tiers for animation/VFX/post-production "
              "at 8-12 points each). This directly supersedes the prior session's own note that the "
              "threshold 'is NOT recorded as a Structured Unknown... no source indicates the threshold "
              "is a fixed, determinable public figure' -- it is exactly that, and is now on file. "
              "ADMINISTRATION (elevated to PRIMARY confidence via direct official "
              "fetch, unlike the rate/min-spend/cultural-test figures which remain secondary): "
              "administered by aws (Austria Wirtschaftsservice Gesellschaft mbH) under the Federal "
              "Ministry of Labor, Economy, Energy and Tourism, with FILM in AUSTRIA (the Austrian Film "
              "Commission) as the first and central point of contact for international productions; "
              "applications run through the AWS Funding Manager platform, live since 2023-01-02. "
              "OVERALL SOURCE TYPE: recorded as SECONDARY (not PRIMARY) because the rate, min-spend "
              "and cultural-test facts -- the substantive eligibility terms -- come from converging "
              "industry aggregators, not a directly-fetched fisaplus.com/fisa-plus.at page (the "
              "fisa-plus.at domain returned a DNS resolution failure at access time; fisaplus.com was "
              "reached directly but did not itself publish the rate/threshold figures, only "
              "administrative/contact information). A future primary-verification pass should retry "
              "fisa-plus.at or search for the FISA+ funding guidelines PDF directly. Annual budget cap "
              "(~EUR 20,000,000 per the DISCOVERY entry) was NOT independently re-confirmed this "
              "session and is not asserted on this profile.",
    ),
    additional_facts={
        "rate_structure": "30% base cash rebate on eligible Austrian spend, +5% green-filming bonus (35% ceiling). Supersedes the repository's stale 25% figure.",
        "min_spend_by_format_eur": "Fiction/feature films: EUR 150,000. Documentaries: EUR 80,000. Animation/VFX/film-music: EUR 25,000.",
        "cultural_test": "Points-based Cultural Test (Annex 3 of the official FISA+ Service Productions Guidelines): max 80 points across Parts A (Cultural Content, max 30), B (Film Professionals, max 38), C (Production, remainder). Minimum passing score: 40 (feature film/fictional series), 35 (animated feature/fictional series), 28 (documentary), 25 (no-shooting-days production parts).",
        "administering_bodies": "Austria Wirtschaftsservice Gesellschaft mbH (aws), under the Federal Ministry of Labor, Economy, Energy and Tourism. FILM in AUSTRIA (Austrian Film Commission) is the first point of contact for international productions. Applications via the AWS Funding Manager platform (live since 2023-01-02).",
        "distinct_austrian_programs_not_modeled_here": "This profile covers FISA+ only. ORF Film/Fernseh-Abkommen (broadcaster co-production fund, ~EUR 16,000,000/year) and Austrian Film Institute (OFI) selective/automatic production support are separate Austrian programs, positively not conflated with FISA+.",
        "primary_source_status": "fisa-plus.at returned a DNS resolution failure at access time (2026-07-26); fisaplus.com and filminaustria.com were reached directly and confirm administration/application-portal facts, but not the rate/threshold figures, which remain secondary-sourced pending a retry.",
    },
))
