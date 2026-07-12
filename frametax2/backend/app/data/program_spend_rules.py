"""
program_spend_rules.py

Pure-Python mirror of the per-program spend-treatment rules seeded by
migrations 0021 (ProgramSpendTreatment for the remaining Tier-1 programs)
and 0025 (source-backed UNKNOWN resolution), in the same discipline
treaty_engine.py already uses ("Static treaty data mirrors migrations
0047-0049"). Nothing here is invented: every row's qualifies flag,
confidence tier, and citation text is copied from the migration that
established it, and the migration revision is recorded on the row.

Vocabulary: rows are keyed by the SpendCategory string vocabulary that
classify_budget_line_items.py emits (the migrations' labor_type
vocabulary maps onto it: atl_cast_principal/atl_cast_supporting ->
atl_cast; btl_crew_resident/non_resident/foreign -> btl_crew_labor;
accommodation_lodging -> lodging; marine_vessel -> vessel_marine).

qualifies semantics (same tri-state as ProgramSpendTreatment.qualifies):
  True  — qualifies under the program
  False — excluded under the program
  None  — unconfirmed from primary source (absence of authority)
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
# Migration 0025 resolved these from the EDB Film Rebate Scheme / MCCI
# documentation: QPE = "transport, accommodation, manpower, catering and
# the hiring of equipment and premises in Mauritius". PARSED tier —
# secondary-source backed, not yet verified from EDB primary statute text
# (0025's own framing). Categories 0025 explicitly did NOT resolve (vfx,
# post_production, music, sound, insurance, completion_bond,
# legal_accounting) remain None per its "Fields NOT updated" list.

_MU_MANPOWER_NOTE = (
    "Manpower costs incurred in Mauritius are explicitly listed as "
    "Qualifying Production Expenditure (QPE) under the Mauritius EDB Film "
    "Rebate Scheme. Source: EDB Mauritius Film Rebate Scheme; MCCI documentation."
)
_MU_TRANSPORT_NOTE = (
    "Transport expenditure (including marine/vessel) incurred in Mauritius is "
    "explicitly listed as Qualifying Production Expenditure (QPE) under the "
    "Mauritius EDB Film Rebate Scheme. "
    "Source: EDB Mauritius Film Rebate Scheme; MCCI documentation."
)
_MU_ACCOMMODATION_NOTE = (
    "Accommodation incurred in Mauritius is explicitly listed as Qualifying "
    "Production Expenditure (QPE) under the Mauritius EDB Film Rebate Scheme. "
    "Source: EDB Mauritius Film Rebate Scheme; MCCI documentation."
)
_MU_CATERING_NOTE = (
    "Catering/per diem incurred in Mauritius is explicitly listed as "
    "Qualifying Production Expenditure (QPE) under the Mauritius EDB Film "
    "Rebate Scheme. Source: EDB Mauritius Film Rebate Scheme; MCCI documentation."
)
_MU_EQUIPMENT_PREMISES_NOTE = (
    "The hiring of equipment and premises in Mauritius is explicitly listed "
    "in the QPE definition ('transport, accommodation, manpower, catering and "
    "the hiring of equipment and premises in Mauritius'). "
    "Source: EDB Mauritius Film Rebate Scheme; MCCI documentation."
)
_MU_UNCONFIRMED = "treatment under Mauritius EDB rebate unconfirmed from primary source."
_CONTINGENCY_NOTE = (
    "Contingency is never a qualifying spend category — only actual expenditure qualifies."
)


def _mu(cat: str, qualifies: bool | None, notes: str, tier: str, rev: str) -> SpendRule:
    return SpendRule(
        program_slug="mu_edb_incentive", spend_category=cat, qualifies=qualifies,
        territorial_only=True, confidence_tier=tier, notes=notes, source_ref=rev,
    )


MU_EDB_RULES: tuple[SpendRule, ...] = (
    # 0025: manpower (ATL all five labor types + BTL crew all three residencies)
    _mu("atl_writer", True, _MU_MANPOWER_NOTE, "PARSED", "0025"),
    _mu("atl_director", True, _MU_MANPOWER_NOTE, "PARSED", "0025"),
    _mu("atl_producer", True, _MU_MANPOWER_NOTE, "PARSED", "0025"),
    _mu("atl_cast", True, _MU_MANPOWER_NOTE, "PARSED", "0025"),
    _mu("btl_crew_labor", True, _MU_MANPOWER_NOTE, "PARSED", "0025"),
    _mu("btl_resident_labor", True, _MU_MANPOWER_NOTE, "PARSED", "0025"),
    _mu("btl_nonresident_labor", True, _MU_MANPOWER_NOTE, "PARSED", "0025"),
    # Employer payroll contributions are a direct component of the same
    # manpower cost the QPE definition lists (same citation).
    _mu("payroll_fringes", True, _MU_MANPOWER_NOTE, "PARSED", "0025"),
    # 0025: transport / marine
    _mu("travel", True, _MU_TRANSPORT_NOTE, "PARSED", "0025"),
    _mu("btl_transportation", True, _MU_TRANSPORT_NOTE, "PARSED", "0025"),
    _mu("vessel_marine", True, _MU_TRANSPORT_NOTE, "PARSED", "0025"),
    # 0025: accommodation / catering
    _mu("lodging", True, _MU_ACCOMMODATION_NOTE, "PARSED", "0025"),
    _mu("btl_catering", True, _MU_CATERING_NOTE, "PARSED", "0025"),
    # QPE definition: "hiring of equipment and premises in Mauritius"
    _mu("btl_equipment_rental", True, _MU_EQUIPMENT_PREMISES_NOTE, "PARSED", "0025"),
    _mu("btl_location_fees", True, _MU_EQUIPMENT_PREMISES_NOTE, "PARSED", "0025"),
    _mu("btl_stage_facility", True, _MU_EQUIPMENT_PREMISES_NOTE, "PARSED", "0025"),
    _mu("btl_set_construction", True, _MU_EQUIPMENT_PREMISES_NOTE, "PARSED", "0025"),
    # 0021: contingency never qualifies (PARSED)
    _mu("contingency", False, _CONTINGENCY_NOTE, "PARSED", "0021"),
    # 0021/0025 "Fields NOT updated": unconfirmed from primary source
    _mu("vfx", None, "VFX " + _MU_UNCONFIRMED, "DISCOVERY", "0021"),
    _mu("post_production", None, "Post-production " + _MU_UNCONFIRMED, "DISCOVERY", "0021"),
    _mu("music", None, "Music " + _MU_UNCONFIRMED, "DISCOVERY", "0021"),
    _mu("sound", None, "Sound post " + _MU_UNCONFIRMED, "DISCOVERY", "0021"),
    _mu("insurance", None, "Insurance " + _MU_UNCONFIRMED, "DISCOVERY", "0021"),
    _mu("completion_bond", None, "Completion bond " + _MU_UNCONFIRMED, "DISCOVERY", "0021"),
    _mu("legal_accounting", None, "Legal and accounting " + _MU_UNCONFIRMED, "DISCOVERY", "0021"),
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
