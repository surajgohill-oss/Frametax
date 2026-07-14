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
}


def get_program_doctrine(program_slug: str) -> QualificationDoctrine | None:
    """The program's qualification doctrine, or None if the program's legal
    regime has not yet been classified (an explicit modeling gap, surfaced
    by the derivation ladder — never treated as a silent default)."""
    return PROGRAM_DOCTRINE.get(program_slug)


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


# ── Registry ────────────────────────────────────────────────────────────────

_ALL_RULES: dict[str, dict[str, SpendRule]] = {}
for _rule in MU_EDB_RULES:
    _ALL_RULES.setdefault(_rule.program_slug, {})[_rule.spend_category] = _rule


def get_program_rules(program_slug: str) -> dict[str, SpendRule]:
    """Category -> SpendRule map for one program; empty dict when the
    program has no mirrored rules yet (absence, not an error)."""
    return dict(_ALL_RULES.get(program_slug, {}))


def get_rule(program_slug: str, spend_category: str) -> SpendRule | None:
    return _ALL_RULES.get(program_slug, {}).get(spend_category)
