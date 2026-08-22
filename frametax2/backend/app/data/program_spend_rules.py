"""
program_spend_rules.py

Pure-Python mirror of the per-program spend-treatment rules. The
Mauritius rows are grounded in the actual EDB primary source — "Film
Rebate Scheme — Submission Procedures" (Economic Development Board,
citing the Film Rebate Scheme Regulation 2018; document dated 31 Jan
2020), specifically its "List of Qualifying Production Expenditures
(QPE) for Motion Pictures" — an illustrative list of 33 spend
categories. QPE is defined as expenses "incurred locally" with respect
to that list.

CANONICAL QPE RULE (governs every qualifies=False row below): every
actual budget item is included unless authoritative program language
explicitly excludes it. Silence, uncertainty, industry convention, and
engineering interpretation are never exclusions. In particular, an item
not being named among the 33 illustrative categories is NOT, by itself,
an explicit exclusion — the primary source states an express "the
following expenditures are excluded" clause only for Digital Animation
projects, not for Motion Pictures. A qualifies=False row here therefore
requires either (a) a quoted clause that actually excludes the item, or
(b) an explicit statutory requirement ("incurred locally") applied
against a KNOWN, evidenced production fact (e.g. work confirmed
performed outside Mauritius) — never an inference from what the
illustrative list happens not to mention.

Vocabulary: rows are keyed by the SpendCategory string vocabulary that
classify_budget_line_items.py emits (the migrations' labor_type
vocabulary maps onto it: atl_cast_principal/atl_cast_supporting ->
atl_cast; btl_crew_resident/non_resident/foreign -> btl_crew_labor;
accommodation_lodging -> lodging; marine_vessel -> vessel_marine).

qualifies semantics (same tri-state as ProgramSpendTreatment.qualifies):
  True  — included (the default; no explicit exclusion applies)
  False — EXPLICITLY excluded (a quoted clause, or an explicit
          territorial requirement applied against a known contrary
          fact — see the canonical rule above)
  None  — a genuine, disclosed gap: no category in the primary source
          plausibly covers this spend at all. Preserved as a visible
          grey area (GREY_AREA_REQUIRES_AUTHORITY), never silently
          resolved in either direction — not zeroed out, and not
          assumed to qualify without any textual basis.
"""
from __future__ import annotations

#: OH-001 fix: included in canonical_evaluation._compute_fingerprint()
#: so a QPE-category/territorial-treatment change invalidates cached
#: served evaluations. Bump on any material change.
PROGRAM_SPEND_RULES_VERSION = "1.0.0"

import enum
from dataclasses import dataclass


# ── Global qualification doctrine ────────────────────────────────────────────
# Every incentive program is classified into exactly one doctrine. The
# doctrine — NOT any internal implementation artifact — governs what the
# derivation ladder does with a budget line whose category has no explicit
# rule. This is the permanent fix for "unknown category defaults to GREY":
# an unmatched line follows the program's doctrine, never a missing rule row.
class QualificationDoctrine(str, enum.Enum):
    # Any locally-incurred spend qualifies unless an explicit exclusion
    # clause names it. Silence = inclusion. Unmatched category -> INCLUDED.
    OPEN_DEFAULT_INCLUDE = "open_default_include"
    # An exhaustive positive enumeration with no catch-alls / illustrative
    # language. Only listed categories qualify; omission is itself the
    # exclusion authority. Unmatched category -> EXCLUDED.
    CLOSED_POSITIVE_LIST = "closed_positive_list"
    # A positive list, but with broad / illustrative ("such as") categories,
    # catch-alls, and conditions (e.g. territorial). A line that maps to a
    # listed category (incl. catch-alls) qualifies subject to conditions; a
    # line that maps to NO category even under a broad reading is a GENUINE
    # legal-interpretation grey area — never an implementation artifact.
    HYBRID_CONDITIONAL = "hybrid_conditional"


# Per-program doctrine. A program absent from this map has not yet been
# classified — get_program_doctrine() returns None and the ladder surfaces
# that as an explicit modeling gap (a real "program regime unclassified"
# grey), never a silent include or a silent all-grey register.
PROGRAM_DOCTRINE: dict[str, QualificationDoctrine] = {
    # Mauritius EDB Film Rebate Scheme, Motion Pictures: positive-list
    # definitional construction ("QPE refer to the expenses incurred
    # locally ... with respect to the list of qualifying production
    # categories defined as follows") with broad/illustrative categories
    # ("Professional services (such as insurance and accounting services)",
    # "Production service company fees", "Labour costs (including
    # non-nationals)") and a territorial condition ("incurred locally").
    # Decisive contrast: Digital Animation carries an explicit exclusions
    # clause (marketing, admin salaries, office/utilities/telecom) that
    # Motion Pictures does NOT — and Motion Pictures LISTS office/
    # utilities/telecom as qualifying. Therefore HYBRID_CONDITIONAL.
    # Source: EDB Film Rebate Scheme — Submission Procedures (31 Jan 2020),
    # QPE lists for Motion Pictures vs. Digital Film Animation Projects.
    "mu_edb_incentive": QualificationDoctrine.HYBRID_CONDITIONAL,

    # Malta Film Commission Cash Rebate: jurisdiction_comparison.py's own
    # PARSED-tier profile states "Base 25% on all qualifying Malta
    # expenditure" with ATL/BTL/VFX/music/marine ALL explicitly True and
    # "No cultural test required for foreign productions" — a broad,
    # unqualified positive statement with NO stated exclusions clause of
    # any kind (unlike Mauritius's Digital-Animation contrast). Silence =
    # inclusion. Source: jurisdiction_comparison.py MALTA profile notes.
    "mt_mfc_rebate": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Greece Cash Rebate: same pattern — "ATL and BTL costs qualify as
    # eligible Greek expenditure. Vessel charter and marine support
    # qualify as production expenditure," no cultural test, no stated
    # exclusions clause. Source: jurisdiction_comparison.py GREECE profile.
    "gr_cash_rebate": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Ireland Section 481: ATL/BTL/VFX/music/marine ALL explicitly True in
    # the PARSED-tier profile, no stated spend-category exclusions clause
    # (the 80%-of-budget/EUR70M figure is a CAP on qualifying spend, not a
    # category exclusion — see program_rate_rules.py's IE_RATE_RULES,
    # disclosed as unenforced). The cultural test (Irish Qualifying Test)
    # is a THRESHOLD eligibility gate (cultural_qualification_model.py's
    # ie_section_481 required rows), not a spend-category doctrine
    # question. Source: jurisdiction_comparison.py IRELAND profile.
    "ie_section_481": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # ── Optimizer-integration phase additions ───────────────────────────────
    # Added when the optimizer-integration phase surfaced that only 4 of the
    # 110 executable jurisdictions could be PRICED, because doctrine — not
    # rate data — was the binding constraint. Every profile carrying the
    # SAME evidentiary pattern that justified Malta/Greece/Ireland above
    # (an affirmative, unqualified statement that BOTH ATL and BTL qualify,
    # with no stated exclusions clause and no unresolved doctrine gap) was
    # re-examined. Exactly two cleared that bar; both are recorded here with
    # their own basis. The examined-and-REJECTED set is documented below —
    # a deliberate audit trail, because "we looked and it did not qualify"
    # is a finding, not an omission.

    # Dominican Republic: the profile states, without qualification, "25%
    # freely-transferable tax credit on ALL above and below the line
    # eligible expenditures for foreign film and television productions"
    # (vitrina.ai, confirmed exactly) — ATL and BTL both affirmatively
    # covered, no exclusions clause, and the profile carries NO unresolved
    # data gaps at all. Same construction as Malta/Greece: silence =
    # inclusion. Source: jurisdiction_comparison.py DOMINICAN REPUBLIC
    # profile (atl_qualifies=True, btl_qualifies=True, data_gaps=[]).
    "do_film_commission_incentive": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Slovakia AVF: "33% cash rebate which can be applied to both above-
    # and below-the-line talents" (camaleonrental.com, confirmed exactly) —
    # an explicitly broad-scoped positive statement covering both labor
    # classes, no exclusions clause, and no unresolved data gaps on the
    # profile. Source: jurisdiction_comparison.py SLOVAKIA profile
    # (atl_qualifies=True, btl_qualifies=True, data_gaps=[]).
    "sk_avf_production_incentive": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # ── Final-closeout phase: primary-source QPE classification of the 5
    # programs that resolved to EVIDENCE_CONSTRAINED and therefore priced at
    # $0 QPE (everything greying). Each program's primary-source
    # qualifying-expenditure definition was read directly; the concern that
    # deferred each one is resolved below. The three programs whose primary
    # source shows a broad "all local production spend qualifies" construction
    # are OPEN_DEFAULT_INCLUDE; Georgia adds explicit exclusion rows for its
    # named exclusions; Spain is HYBRID with explicit BTL inclusion rows (its
    # ATL "creative personnel" category is genuinely conditioned on EEA tax
    # residence, unconfirmed for this production, so ATL stays grey).

    # Croatia HAVC: Invest Croatia (official investcroatia.gov.hr): "Qualified
    # spend consists of the costs of goods and services purchased in Croatia
    # AND wages paid to Croatian tax residents (both cast and crew) for
    # services carried out in Croatia." Broad all-local-spend construction,
    # ATL and BTL both named, only FORMAT exclusions (commercials/reality/
    # game shows) — no spend-CATEGORY exclusions. The prior "unconfirmed VFX/
    # music treatment" gap is resolved: goods and services purchased in
    # Croatia are all qualifying, VFX/music included. Silence = inclusion.
    "hr_cash_rebate": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Cyprus Film Scheme: Invest Cyprus (film.investcyprus.org.cy, official):
    # ATL "includes costs for the producer, director, scriptwriters, casting
    # directors and up to three leading roles, capped at 30% of total eligible
    # expenditure"; BTL "covers ALL OTHER production costs, including crew
    # salaries, accommodation, transportation, props, set design, and
    # post-production services conducted in Cyprus." The prior "ATL scope
    # unconfirmed" gap is resolved: ATL DOES qualify (subject to the 30% cap,
    # disclosed but not per-person-enforceable here), BTL is all-inclusive.
    "cy_film_rebate": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # New York Film Tax Credit: Empire State Development (esd.ny.gov,
    # official): "Qualified costs include certain above-the-line wages
    # subject to a cap, below-the-line wages, and production costs directly
    # related to the production." The prior "ATL only under a 40%-of-other-
    # costs cap" gap is resolved: capped is NOT excluded — ATL qualifies
    # subject to the cap (disclosed, not enforceable without a per-line ATL/
    # BTL ratio), BTL and production costs qualify broadly. Named cost
    # exclusions (story/script rights) are added as explicit rows below.
    "us_ny_film_credit": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Georgia Film Tax Credit: Georgia DOR (dor.georgia.gov, official):
    # "costs for pre-production, production, and post-production related to
    # filming in Georgia are qualified expenditures" — broad inclusion — with
    # an EXPRESS exclusions clause: "Development costs, promotion, marketing,
    # story rights, and legal fees are NOT qualified." An express exclusions
    # clause over a broad-inclusion base is the OPEN_DEFAULT_INCLUDE pattern
    # (silence = inclusion; the statute names what is OUT). The per-person
    # $500K ATL cap is disclosed but not per-person-enforceable here. Explicit
    # qualifies=False rows for the named exclusions are added below.
    "us_ga_film_credit": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Germany DFFF: FFA/BKM guidelines (ffa.de, official) — "the grant consists
    # of up to 30% of German production costs," a broad-inclusion base, with an
    # EXPRESS non-qualifying list: "pre-production costs, costs for rights to
    # content and other existing works, materials/services provided free or at
    # reduced charge, deferred fees, deferred overhead, and contingency funds
    # unless dissolved in the final cost report." Broad inclusion + named
    # exclusions = OPEN_DEFAULT_INCLUDE; the contingency exclusion (conditional
    # on non-dissolution) is added as an explicit row below.
    "de_dfff": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Italy tax credit (foreign): italianfilmcommissions.it / mestierecinema.it
    # — "40% of eligible expenses incurred within Italian territory," a broad
    # inclusion. Conditions (51% of BTL must be EU nationals; overhead capped
    # at 7.5%; ATL outside the EEA at a reduced 30% rate) are threshold/rate
    # conditions, not spend-category exclusions, and are disclosed on the rate
    # side. Broad local-spend inclusion → OPEN_DEFAULT_INCLUDE.
    "it_tax_credit_foreign": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Hungary NFI: nfi.hu (official) — "30% rebate based on all the DIRECT
    # film production costs spent in the country," explicitly listing
    # pre/post-production, crew wages, location fees, rentals, travel,
    # producer fees, royalties, financing. Broad direct-cost inclusion; the
    # per-category sub-caps (royalties 4%, producer fees 4%, advertising 2%)
    # are disclosed conditions, not category exclusions → OPEN_DEFAULT_INCLUDE.
    "hu_hipa_rebate": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # New Mexico: tax.newmexico.gov FYI-370 (official) — "qualified
    # expenditures are DIRECT production and post-production expenses made in
    # New Mexico subject to NM taxation," covering wages to cast/crew and
    # physical production expenses (equipment, facilities, goods). Broad
    # direct-spend inclusion → OPEN_DEFAULT_INCLUDE. Nonresident-BTL limits
    # are disclosed rate-side conditions, not category exclusions.
    "us_nm_film_credit": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Belgium Tax Shelter: hub.info / scopeinvest.be (production-consultancy
    # secondary sources, corroborating each other): "All production-related
    # expenses qualifying as Belgian taxable income are eligible... shoot
    # and/or post-production including VFX are eligible." Eligibility test is
    # a TERRITORIAL/PAYEE test (paid to an individual/company subject to
    # Belgian tax), not a positive category enumeration — the same
    # construction as Mauritius's own "incurred locally" test. Administrative
    # expenses are capped at 30% of the total (a PROPORTION condition,
    # disclosed but not enforced here — same treatment as Italy's 7.5%
    # overhead cap and Georgia's per-person ATL cap) — not a category
    # exclusion. Broad inclusion, no category exclusions found →
    # OPEN_DEFAULT_INCLUDE.
    "be_tax_shelter": QualificationDoctrine.OPEN_DEFAULT_INCLUDE,

    # Spain Art. 36.2 LIS: Agencia Tributaria (official) — the deduction base
    # is "expenses incurred in Spanish territory directly related to
    # production, including (1) expenses of CREATIVE PERSONNEL with tax
    # residence in Spain or the EEA (max EUR 50,000 per person), and (2)
    # expenses deriving from the use of TECHNICAL INDUSTRIES and other
    # suppliers." Category (2) is a broad BTL/technical inclusion; category
    # (1) (ATL/creative) is conditioned on EEA tax residence, which is NOT
    # confirmed for this production's talent. Therefore HYBRID_CONDITIONAL
    # (not OPEN): the technical/BTL categories are explicitly included below,
    # and ATL creative-personnel categories correctly fall to a genuine grey
    # (EEA-residency-dependent) rather than a silent inclusion.
    "es_tax_credit_foreign": QualificationDoctrine.HYBRID_CONDITIONAL,
}

# ── Examined for doctrine classification and DELIBERATELY NOT classified ────
# These programs share the surface pattern (atl_qualifies=True and
# btl_qualifies=True) but each carries a specific, recorded reason that the
# OPEN_DEFAULT_INCLUDE reasoning does NOT transfer. Classifying them would
# be a guess with high leverage: doctrine governs how EVERY unmatched budget
# line is treated, so a wrong doctrine silently mis-qualifies a whole
# register. Each stays unclassified — the derivation ladder surfaces that as
# an explicit modeling gap, and the jurisdiction is retained as
# production-capable/incentive-pending rather than priced at a guess.
# NOTE (final-closeout phase): es_tax_credit_foreign, cy_film_rebate,
# us_ny_film_credit, us_ga_film_credit, and hr_cash_rebate were REMOVED from
# this register after their primary-source qualifying-expenditure definitions
# were read directly and classified in PROGRAM_DOCTRINE above (with explicit
# SpendRule rows below where the statute names exclusions or conditions). The
# entries remaining here are the programs whose governing QPE text still has
# NOT been read from primary source — genuinely deferred, not yet resolvable.
# Empty as of the Worldwide Incentive Engine Closeout phase: every program
# that was previously deferred here (BE, DE, HR, HU, IT, US-NM, plus CY/ES/
# US-GA/US-NY which were deferred separately in the optimizer-integration
# phase) has had its primary-source qualifying-expenditure text read and
# classified in PROGRAM_DOCTRINE above. This register is NOT deleted — it
# remains the correct tier-2 mechanism (resolve_program_doctrine) for any
# FUTURE program whose primary source shows the open-default reasoning does
# not transfer. An empty dict here means zero such programs currently exist,
# not that the mechanism is unused.
DOCTRINE_EXAMINED_NOT_CLASSIFIED: dict[str, str] = {}


def get_program_doctrine(program_slug: str) -> QualificationDoctrine | None:
    """The program's EXPLICITLY CLASSIFIED qualification doctrine, or None
    when no primary-source classification has been recorded.

    This accessor deliberately still returns None for unclassified
    programs: callers that report modeling provenance (how much of a
    result is read-from-statute vs. resolved under the canonical rule)
    depend on that distinction. Callers that need to EXECUTE should use
    resolve_program_doctrine(), which applies the canonical rule below."""
    return PROGRAM_DOCTRINE.get(program_slug)


# ── Canonical doctrine resolution (execution path) ──────────────────────────
# The CANONICAL QPE RULE stated at the top of this module — "every actual
# budget item is included unless authoritative program language explicitly
# excludes it; silence, uncertainty, industry convention, and engineering
# interpretation are never exclusions" — IS, definitionally,
# OPEN_DEFAULT_INCLUDE. It was written as the governing rule for the whole
# module, not as a Mauritius-only convention.
#
# For a long time the engine nonetheless refused to price any program whose
# doctrine had not been hand-classified, because every execution gate tested
# `get_program_doctrine(slug) is not None`. That made an ABSENCE OF
# CLASSIFICATION behave as a prohibition — the precise inversion the
# canonical rule forbids, and the reason only 4 of 110 fully rate-modeled
# jurisdictions could be priced. Doctrine, not legal knowledge, was the
# binding constraint.
#
# Resolution is therefore three-tiered, strongest evidence first:
#
#   1. EXPLICIT           — a doctrine read from the program's own primary
#                           source (PROGRAM_DOCTRINE). Always wins.
#   2. EVIDENCE_CONSTRAINED — the program has recorded evidence that the
#                           open-default reasoning does NOT transfer (a
#                           statutory ATL cap, a closed two-category
#                           enumeration, an unread ministerial order). The
#                           canonical default is overridden DOWNWARD to
#                           HYBRID_CONDITIONAL, so a line matching no
#                           category becomes a genuine legal-interpretation
#                           grey requiring authority — never a silent
#                           inclusion and never a silent exclusion.
#   3. CANONICAL_DEFAULT  — no contrary evidence exists, so the module's own
#                           canonical rule governs: include unless explicitly
#                           excluded.
#
# Tier 2 is what keeps tier 3 honest: the default applies only where nothing
# is known to contradict it, exactly as the canonical rule requires.
CANONICAL_DEFAULT_DOCTRINE = QualificationDoctrine.OPEN_DEFAULT_INCLUDE


class DoctrineBasis(str, enum.Enum):
    EXPLICIT = "explicit_classification"
    EVIDENCE_CONSTRAINED = "evidence_constrained_hybrid"
    CANONICAL_DEFAULT = "canonical_default_inclusion"


@dataclass(frozen=True)
class DoctrineResolution:
    """The doctrine the engine will execute under, plus WHY — so a served
    result can always state whether its qualification treatment was read
    from statute or resolved under the canonical rule."""
    program_slug: str
    doctrine: QualificationDoctrine
    basis: DoctrineBasis
    explanation: str

    @property
    def is_explicit(self) -> bool:
        return self.basis is DoctrineBasis.EXPLICIT


def resolve_program_doctrine(program_slug: str) -> DoctrineResolution:
    """The executable doctrine for a program. Never returns None: under the
    canonical QPE rule, absence of an explicit classification is not a
    prohibition. See the three-tier commentary above."""
    explicit = PROGRAM_DOCTRINE.get(program_slug)
    if explicit is not None:
        return DoctrineResolution(
            program_slug=program_slug,
            doctrine=explicit,
            basis=DoctrineBasis.EXPLICIT,
            explanation=(
                f"Doctrine '{explicit.value}' was classified directly from this "
                "program's own primary source — see PROGRAM_DOCTRINE."
            ),
        )

    contrary = DOCTRINE_EXAMINED_NOT_CLASSIFIED.get(program_slug)
    if contrary is not None:
        return DoctrineResolution(
            program_slug=program_slug,
            doctrine=QualificationDoctrine.HYBRID_CONDITIONAL,
            basis=DoctrineBasis.EVIDENCE_CONSTRAINED,
            explanation=(
                "The canonical default-inclusion rule is NOT applied here: this "
                "program carries recorded evidence that its qualifying-expenditure "
                "construction is narrower than silence-equals-inclusion. Resolved "
                "to HYBRID_CONDITIONAL, so a line matching no listed category "
                "becomes a genuine legal-interpretation grey requiring authority, "
                f"never a silent inclusion. Evidence: {contrary}"
            ),
        )

    return DoctrineResolution(
        program_slug=program_slug,
        doctrine=CANONICAL_DEFAULT_DOCTRINE,
        basis=DoctrineBasis.CANONICAL_DEFAULT,
        explanation=(
            "No primary-source doctrine classification and no evidence of a "
            "narrower construction. The module's CANONICAL QPE RULE governs: "
            "every actual budget item is included unless authoritative program "
            "language explicitly excludes it — silence, uncertainty and "
            "convention are never exclusions. Qualification remains subject to "
            "the program's territorial requirement and its statutory rate "
            "conditions, which are enforced separately."
        ),
    )


@dataclass(frozen=True)
class SpendRule:
    program_slug: str
    spend_category: str
    qualifies: bool | None
    territorial_only: bool          # spend must be incurred in-jurisdiction
    confidence_tier: str            # DISCOVERY | PARSED | VERIFIED
    notes: str                      # citation / source text from the migration
    source_ref: str                 # migration revision the row mirrors


# ── Mauritius EDB Film Rebate Scheme ────────────────────────────────────────
# Primary source: EDB "Film Rebate Scheme — Submission Procedures" (31 Jan
# 2020, citing the Film Rebate Scheme Regulation 2018), "List of Qualifying
# Production Expenditures (QPE) for Motion Pictures" — a closed 33-category
# list. QPE = expenses "incurred locally" within one of the 33 categories.
# VERIFIED tier below means: read directly from this primary document in
# this session, not inferred from a secondary source. Migration 0021/0025's
# PARSED-tier rows are superseded where the primary document resolves what
# they left as "Fields NOT updated" (insurance, post-production, VFX,
# sound) or corrects the citation basis (contingency, completion bond).

_MU_LABOR_NOTE = (
    "Explicit QPE category: 'Remuneration for cast and crew' / 'Labour costs "
    "(including non-nationals)'. No above-scale-cast carve-out and no "
    "ATL/BTL distinction appears anywhere in the category list — the "
    "category covers all cast and crew labor without qualification. "
    "Source: EDB Film Rebate Scheme — Submission Procedures (31 Jan 2020), "
    "QPE list for Motion Pictures, items 'Remuneration for cast and crew' "
    "and 'Labour costs (including non-nationals)'."
)
_MU_TRANSPORT_NOTE = (
    "Explicit QPE category: 'Travel to Mauritius (flight and marine travel)' "
    "and marine/vessel/ground-transport categories. Source: EDB Film Rebate "
    "Scheme — Submission Procedures (31 Jan 2020), QPE list for Motion Pictures."
)
_MU_ACCOMMODATION_NOTE = (
    "Explicit QPE category: 'Accommodation in Mauritius'. Source: EDB Film "
    "Rebate Scheme — Submission Procedures (31 Jan 2020), QPE list for "
    "Motion Pictures."
)
_MU_CATERING_NOTE = (
    "Explicit QPE category: 'Catering'. Source: EDB Film Rebate Scheme — "
    "Submission Procedures (31 Jan 2020), QPE list for Motion Pictures."
)
_MU_EQUIPMENT_PREMISES_NOTE = (
    "Explicit QPE categories covering hiring of equipment, locations, and "
    "studio/stage premises in Mauritius (e.g. 'Location fees', 'Hiring of "
    "equipment'). Source: EDB Film Rebate Scheme — Submission Procedures "
    "(31 Jan 2020), QPE list for Motion Pictures."
)
_MU_PROFESSIONAL_SERVICES_NOTE = (
    "Explicit QPE category: 'Professional services (such as insurance and "
    "accounting services)'. Insurance and accounting are named examples, not "
    "an exhaustive list, but both are unambiguously covered by their own "
    "names. Source: EDB Film Rebate Scheme — Submission Procedures (31 Jan "
    "2020), QPE list for Motion Pictures."
)
_MU_PRODUCTION_SERVICE_FEES_NOTE = (
    "Explicit QPE category: 'Production service company fees', plus the "
    "'Professional services (such as insurance and accounting services)' and "
    "'Telecommunications' and 'Rental of offices, office furniture and "
    "equipment' categories. Covers the local production-services company's "
    "fee and the production's locally-incurred administrative overhead "
    "(accounting/audit — including the EDB-required rebate audit — company "
    "setup, tax administration, telecom, office). Contrast: the express "
    "exclusions clause for Digital Animation (office/utilities/telecom, "
    "administrative salaries) does NOT apply to Motion Pictures, which "
    "affirmatively LISTS these as qualifying. Source: EDB Film Rebate "
    "Scheme — Submission Procedures (31 Jan 2020), QPE list for Motion "
    "Pictures."
)
_MU_TELECOM_NOTE = (
    "Explicit QPE category: 'Telecommunications'. Source: EDB Film Rebate "
    "Scheme — Submission Procedures (31 Jan 2020), QPE list for Motion "
    "Pictures."
)
_MU_POST_NOTE = (
    "Explicit QPE category: 'Post production services (picture and sound)'. "
    "Covered as a category — whether a given account qualifies still turns "
    "on the separate 'incurred locally' territorial requirement (QPE = "
    "expenses incurred locally); work performed outside Mauritius fails on "
    "territorial grounds regardless of category membership. Source: EDB "
    "Film Rebate Scheme — Submission Procedures (31 Jan 2020), QPE list for "
    "Motion Pictures."
)
_MU_VFX_NOTE = (
    "Explicit QPE category: 'Visual effects services'. Same territorial "
    "caveat as post-production applies. Source: EDB Film Rebate Scheme — "
    "Submission Procedures (31 Jan 2020), QPE list for Motion Pictures."
)
_MU_MUSIC_UNRESOLVED_NOTE = (
    "No QPE category in the primary 33-item list names music composition, "
    "scoring, or licensing; 'Post production services (picture and sound)' "
    "may or may not extend to a music score depending on EDB's reading of "
    "'sound' — genuinely unresolved from the text available. Independently, "
    "this account's own work is incurred outside Mauritius, which fails "
    "territorial nexus regardless of category outcome. Source: EDB Film "
    "Rebate Scheme — Submission Procedures (31 Jan 2020), QPE list for "
    "Motion Pictures (absence noted against the full 33-item list)."
)
_MU_CONTINGENCY_NOTE = (
    "CANONICAL QPE RULE: no clause in the primary source excludes a "
    "contingency reserve. Its absence from the 33-item illustrative list "
    "is silence, not an explicit exclusion (the express 'the following "
    "expenditures are excluded' clause applies only to Digital Animation "
    "projects, not to this Motion Picture). Included. Disclosed, non-"
    "excluding caveat from the SAME primary source's claim procedures: 'a "
    "certified report by the local auditors ... providing details of the "
    "amount of expenditures, and the amount of the qualified production "
    "expenditures, incurred in Mauritius' is required at claim time — so "
    "only the portion of this reserve actually drawn down and spent by "
    "wrap will appear in that certification. This is a claim-timing note, "
    "not a qualification exclusion. Source: EDB Film Rebate Scheme — "
    "Submission Procedures (31 Jan 2020), QPE list for Motion Pictures + "
    "Application and Claim Procedures (auditor certification requirement)."
)
_MU_COMPLETION_BOND_NOTE = (
    "CANONICAL QPE RULE: no clause in the primary source excludes a "
    "completion bond premium. Its absence from the 33-item illustrative "
    "list is silence, not an explicit exclusion (see contingency note for "
    "the same reasoning). Included; the category match is not itself "
    "certain (no illustrative item is an obvious analogue), which is "
    "disclosed as a genuine open question for EDB confirmation rather "
    "than withheld from QPE. Source: EDB Film Rebate Scheme — Submission "
    "Procedures (31 Jan 2020), full QPE list for Motion Pictures (no "
    "exclusion found)."
)
_MU_LEGAL_ACCOUNTING_NOTE = (
    "Explicit QPE category: 'Professional services (such as insurance and "
    "accounting services)'. 'Such as' is illustrative, not exhaustive — the "
    "named category is 'Professional services' generally; insurance and "
    "accounting are examples, not the full scope. No clause in the primary "
    "source excludes legal fees, audit fees, or incentive-application/"
    "submission costs from 'Professional services'. CANONICAL QPE RULE: "
    "absent an explicit exclusion, the full account is included — no $ "
    "split is required because there is no authority-backed reason to "
    "withhold any portion. Source: EDB Film Rebate Scheme — Submission "
    "Procedures (31 Jan 2020), QPE list for Motion Pictures, item "
    "'Professional services (such as insurance and accounting services)'."
)


def _mu(cat: str, qualifies: bool | None, notes: str, tier: str, rev: str) -> SpendRule:
    return SpendRule(
        program_slug="mu_edb_incentive", spend_category=cat, qualifies=qualifies,
        territorial_only=True, confidence_tier=tier, notes=notes, source_ref=rev,
    )


MU_EDB_RULES: tuple[SpendRule, ...] = (
    # Labor — cast and crew, all types, no ATL/BTL distinction in the source.
    _mu("atl_writer", True, _MU_LABOR_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("atl_director", True, _MU_LABOR_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("atl_producer", True, _MU_LABOR_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("atl_cast", True, _MU_LABOR_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("btl_crew_labor", True, _MU_LABOR_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("btl_resident_labor", True, _MU_LABOR_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("btl_nonresident_labor", True, _MU_LABOR_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Employer payroll contributions are a direct component of the same
    # labor cost the QPE list names (same citation).
    _mu("payroll_fringes", True, _MU_LABOR_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Transport / travel to Mauritius / marine.
    _mu("travel", True, _MU_TRANSPORT_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("btl_transportation", True, _MU_TRANSPORT_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("vessel_marine", True, _MU_TRANSPORT_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Accommodation / catering.
    _mu("lodging", True, _MU_ACCOMMODATION_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("btl_catering", True, _MU_CATERING_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Equipment / locations / premises.
    _mu("btl_equipment_rental", True, _MU_EQUIPMENT_PREMISES_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("btl_location_fees", True, _MU_EQUIPMENT_PREMISES_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("btl_stage_facility", True, _MU_EQUIPMENT_PREMISES_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("btl_set_construction", True, _MU_EQUIPMENT_PREMISES_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Professional services — insurance and accounting explicitly named.
    _mu("insurance", True, _MU_PROFESSIONAL_SERVICES_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Production service company fees / production administration overhead —
    # explicit 'Production service company fees' category + professional
    # services + telecom + office. Covers lumped "administrative expenses"
    # whose detail is production admin (see little_utopia_real_budget).
    _mu("production_service_fees", True, _MU_PRODUCTION_SERVICE_FEES_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("telecommunications", True, _MU_TELECOM_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Post-production / VFX — explicit categories, subject to territorial nexus.
    _mu("post_production", True, _MU_POST_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("sound", True, _MU_POST_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("vfx", True, _MU_VFX_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Music — genuinely unresolved category coverage (independently also
    # fails territorial nexus for this production).
    _mu("music", None, _MU_MUSIC_UNRESOLVED_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Contingency — no explicit exclusion found; included per the canonical
    # QPE rule, with a disclosed (non-excluding) claim-timing caveat.
    _mu("contingency", True, _MU_CONTINGENCY_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Completion bond premium — no explicit exclusion found; included.
    _mu("completion_bond", True, _MU_COMPLETION_BOND_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Legal & accounting — "Professional services" is the named category;
    # insurance/accounting are non-exhaustive examples. No explicit
    # exclusion of legal fees or submission costs exists. Included in full.
    _mu("legal_accounting", True, _MU_LEGAL_ACCOUNTING_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
)


# ── Germany DFFF — explicit exclusion rows ──────────────────────────────────
# Germany is OPEN_DEFAULT_INCLUDE (broad "German production costs" base), but
# the FFA/BKM guidelines (ffa.de, official) EXPRESSLY exclude "contingency
# funds UNLESS they can be dissolved in the final cost report in favor of
# goods and services eligible for the grant." This is the opposite default
# from Mauritius's contingency treatment (included absent an exclusion) —
# Germany excludes by default, conditionally un-excluding only on dissolution
# evidence this production does not have. Modeled as EXCLUDED, not grey:
# the statute states a clear default (excluded) and the condition for
# reversal (dissolution) is a known, absent fact, not an unresolved question.
_DE_CONTINGENCY_EXCLUSION_NOTE = (
    "FFA/BKM DFFF Guidelines (ffa.de, official): 'contingency funds' are "
    "excluded from German production costs 'unless they can be dissolved in "
    "the final cost report in favor of goods and services eligible for the "
    "grant.' No dissolution evidence exists for this production's "
    "contingency reserve, so the statute's default (excluded) applies. "
    "Source: FFA DFFF Guidelines of the BKM (ffa.de/guidelines-dfff)."
)
DE_DFFF_RULES: tuple[SpendRule, ...] = (
    SpendRule(program_slug="de_dfff", spend_category="contingency",
              qualifies=False, territorial_only=True, confidence_tier="PARSED",
              notes=_DE_CONTINGENCY_EXCLUSION_NOTE, source_ref="FFA-DFFF-Guidelines-BKM"),
)

# ── Georgia Film Tax Credit — explicit exclusion rows ───────────────────────
# Georgia is OPEN_DEFAULT_INCLUDE (broad "pre/production/post costs qualify"),
# so the ONLY rows needed are the statute's EXPRESS exclusions. Source:
# Georgia DOR (dor.georgia.gov), "Development costs, promotion, marketing,
# story rights, and legal fees are not qualified expenditures." Of the
# Little Utopia spend vocabulary, only 'legal_accounting' intersects an
# express exclusion ("legal fees") — modeled as EXCLUDED, disclosing that the
# statute's exclusion is specifically of legal fees (the accounting portion
# of a combined legal/accounting account would qualify, but this engine has
# no legal-vs-accounting split, so the conservative whole-account exclusion
# is applied). Every other category follows the open-default (qualifies).
_GA_LEGAL_EXCLUSION_NOTE = (
    "Georgia DOR: 'legal fees are not qualified expenditures.' This engine's "
    "'legal_accounting' category is a combined account; Georgia excludes the "
    "legal-fees portion expressly (accounting/audit fees for the production "
    "would qualify). With no legal-vs-accounting split available, the whole "
    "combined account is conservatively EXCLUDED rather than silently "
    "included. Source: dor.georgia.gov Film Tax Credit list of expenditures."
)
US_GA_RULES: tuple[SpendRule, ...] = (
    SpendRule(program_slug="us_ga_film_credit", spend_category="legal_accounting",
              qualifies=False, territorial_only=True, confidence_tier="PARSED",
              notes=_GA_LEGAL_EXCLUSION_NOTE, source_ref="GA-DOR-Film-Expenditures-List"),
)

# ── New York Film Tax Credit — explicit exclusion rows ──────────────────────
# New York is OPEN_DEFAULT_INCLUDE for below-the-line + production costs +
# capped ATL. Source: esd.ny.gov. NY qualified production costs exclude
# story/script RIGHTS acquisition costs, but 'atl_writer' in this vocabulary
# is writer LABOR (a capped ATL wage that DOES qualify), not a rights
# purchase — so no Little Utopia category maps to NY's story-rights
# exclusion, and no exclusion row is required. ATL wages qualify subject to
# the disclosed 40%-of-qualified-BTL cap (not per-line enforceable here),
# consistent with how the rate-rule conditions are disclosed-but-unenforced.
US_NY_RULES: tuple[SpendRule, ...] = ()

# ── Spain Art. 36.2 LIS — explicit inclusion rows for the technical/BTL and
# supplier categories the statute names, so that under HYBRID_CONDITIONAL the
# broad category-(2) spend qualifies while the ATL creative-personnel
# categories (category (1), EEA-tax-residence-conditioned) correctly fall to a
# genuine grey rather than a silent inclusion. Source: Agencia Tributaria
# (official), Art. 36.2 LIS: base = "expenses... deriving from the use of
# TECHNICAL INDUSTRIES and other suppliers" (cameras/lighting/sound/SFX/
# wardrobe/equipment/locations/sets/post/transport/etc.).
_ES_TECHNICAL_NOTE = (
    "Spain Art. 36.2 LIS names 'expenses deriving from the use of technical "
    "industries and other suppliers' as an eligible category — a broad "
    "below-the-line/technical inclusion covering equipment, cameras, "
    "lighting, sound, SFX, wardrobe, locations, sets, transport, post and "
    "supplier services incurred in Spain. Source: Agencia Tributaria "
    "(sede.agenciatributaria.gob.es), Art. 36.2 LIS deduction base."
)
_ES_CREATIVE_NOTE = (
    "Spain Art. 36.2 LIS: 'creative personnel' expenses qualify ONLY where "
    "the person has tax residence in Spain or the EEA (max EUR 50,000 per "
    "person). This production's creative-personnel EEA tax residency is NOT "
    "confirmed, so these ATL categories are a genuine grey (EEA-residency-"
    "dependent), never a silent inclusion. Source: Agencia Tributaria, "
    "Art. 36.2 LIS."
)
def _es_tech(cat: str) -> SpendRule:
    return SpendRule(program_slug="es_tax_credit_foreign", spend_category=cat,
                     qualifies=True, territorial_only=True, confidence_tier="PARSED",
                     notes=_ES_TECHNICAL_NOTE, source_ref="ES-AEAT-Art36.2-LIS")
def _es_creative(cat: str) -> SpendRule:
    return SpendRule(program_slug="es_tax_credit_foreign", spend_category=cat,
                     qualifies=None, territorial_only=True, confidence_tier="PARSED",
                     notes=_ES_CREATIVE_NOTE, source_ref="ES-AEAT-Art36.2-LIS")
ES_RULES: tuple[SpendRule, ...] = (
    # Category (2): technical industries + suppliers — broad BTL inclusion.
    _es_tech("btl_crew_labor"), _es_tech("btl_resident_labor"), _es_tech("btl_nonresident_labor"),
    _es_tech("btl_equipment_rental"), _es_tech("btl_location_fees"), _es_tech("btl_stage_facility"),
    _es_tech("btl_set_construction"), _es_tech("btl_transportation"), _es_tech("btl_catering"),
    _es_tech("vessel_marine"), _es_tech("travel"), _es_tech("lodging"), _es_tech("insurance"),
    _es_tech("production_service_fees"), _es_tech("telecommunications"),
    _es_tech("post_production"), _es_tech("sound"), _es_tech("vfx"), _es_tech("music"),
    _es_tech("payroll_fringes"), _es_tech("contingency"), _es_tech("completion_bond"),
    _es_tech("legal_accounting"),
    # Category (1): creative personnel — ATL, EEA-tax-residence-conditioned → grey.
    _es_creative("atl_writer"), _es_creative("atl_director"),
    _es_creative("atl_producer"), _es_creative("atl_cast"),
)


# ── Registry ────────────────────────────────────────────────────────────────

_ALL_RULES: dict[str, dict[str, SpendRule]] = {}
for _rule in (*MU_EDB_RULES, *US_GA_RULES, *US_NY_RULES, *ES_RULES, *DE_DFFF_RULES):
    _ALL_RULES.setdefault(_rule.program_slug, {})[_rule.spend_category] = _rule


def get_program_rules(program_slug: str) -> dict[str, SpendRule]:
    """Category -> SpendRule map for one program; empty dict when the
    program has no mirrored rules yet (absence, not an error)."""
    return dict(_ALL_RULES.get(program_slug, {}))


def get_rule(program_slug: str, spend_category: str) -> SpendRule | None:
    return _ALL_RULES.get(program_slug, {}).get(spend_category)
