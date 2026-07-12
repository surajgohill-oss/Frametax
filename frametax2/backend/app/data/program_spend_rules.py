"""
program_spend_rules.py

Pure-Python mirror of the per-program spend-treatment rules. The
Mauritius rows are grounded in the actual EDB primary source — "Film
Rebate Scheme — Submission Procedures" (Economic Development Board,
citing the Film Rebate Scheme Regulation 2018; document dated 31 Jan
2020), specifically its "List of Qualifying Production Expenditures
(QPE) for Motion Pictures" — a CLOSED, enumerated list of 33 spend
categories. QPE is defined as expenses "incurred locally" falling
within one of those categories; nothing outside the enumerated list is
QPE, and there is no separate general exclusions clause for motion
pictures (only Digital Animation projects carry their own exclusions
list, which does not apply here). Rows not resolvable from that closed
list still mirror migrations 0021/0025 where those pre-date it.

Vocabulary: rows are keyed by the SpendCategory string vocabulary that
classify_budget_line_items.py emits (the migrations' labor_type
vocabulary maps onto it: atl_cast_principal/atl_cast_supporting ->
atl_cast; btl_crew_resident/non_resident/foreign -> btl_crew_labor;
accommodation_lodging -> lodging; marine_vessel -> vessel_marine).

qualifies semantics (same tri-state as ProgramSpendTreatment.qualifies):
  True  — qualifies under the program
  False — excluded under the program
  None  — unconfirmed from primary source (absence of authority, OR a
          missing production fact needed to apply an otherwise-known
          rule — see FACT_SPLIT_CATEGORIES in qualification_derivation.py)
"""
from __future__ import annotations

from dataclasses import dataclass


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
    "Contingency reserve does not appear anywhere in the closed 33-category "
    "QPE list, and QPE is by definition expenditure 'incurred' — an unspent "
    "reserve is not incurred cost until drawn down against an actual line "
    "item. Two independent grounds, both from primary source: (1) closed-list "
    "omission, (2) not yet incurred. Source: EDB Film Rebate Scheme — "
    "Submission Procedures (31 Jan 2020), full QPE list for Motion Pictures."
)
_MU_COMPLETION_BOND_NOTE = (
    "Completion bond premium does not appear anywhere in the closed "
    "33-category QPE list for Motion Pictures, and no category (including "
    "'Professional services') plausibly extends to a bond premium. This is "
    "a closed-list omission, not an absence-of-authority gap: the "
    "regulation affirmatively enumerates what qualifies, and a bond premium "
    "is not among the enumerated items. Source: EDB Film Rebate Scheme — "
    "Submission Procedures (31 Jan 2020), full QPE list for Motion Pictures."
)
_MU_LEGAL_ACCOUNTING_NOTE = (
    "'Professional services (such as insurance and accounting services)' "
    "names accounting explicitly but not legal fees; 'such as' signals "
    "non-exhaustive examples, so whether legal fees fall within 'professional "
    "services' is a genuine interpretive question, not resolved by this "
    "text. Distinct from the category question: this account combines "
    "legal and accounting costs (and, for the audit/submission-fee "
    "account, audit and incentive-application-filing costs) in one line "
    "with no $ breakdown — the accounting/audit portion is confirmed QPE, "
    "the legal/submission-fee portion is not, and the split amount is not "
    "known from the budget as given. Source: EDB Film Rebate Scheme — "
    "Submission Procedures (31 Jan 2020), QPE list for Motion Pictures, "
    "item 'Professional services (such as insurance and accounting services)'."
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
    # Post-production / VFX — explicit categories, subject to territorial nexus.
    _mu("post_production", True, _MU_POST_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("sound", True, _MU_POST_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    _mu("vfx", True, _MU_VFX_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Music — genuinely unresolved category coverage (independently also
    # fails territorial nexus for this production).
    _mu("music", None, _MU_MUSIC_UNRESOLVED_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Contingency — closed-list omission + not-yet-incurred (dual ground).
    _mu("contingency", False, _MU_CONTINGENCY_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Completion bond premium — closed-list omission.
    _mu("completion_bond", False, _MU_COMPLETION_BOND_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
    # Legal & accounting — accounting confirmed, legal/submission-fee portion
    # genuinely mixed; the account as booked has no $ breakdown (fact gap,
    # not authority gap — see FACT_SPLIT_CATEGORIES in qualification_derivation.py).
    _mu("legal_accounting", None, _MU_LEGAL_ACCOUNTING_NOTE, "VERIFIED", "EDB-2020-QPE-List"),
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
