"""
Hollywood Bowl — Canonical Section Catalog
==========================================

Physical layout (open-air amphitheater facing NE, stage at south):
  Stage shells face audience in a natural hillside bowl (Cahuenga Pass).
  Seating flows from front (closest to stage) to back (hillside top).

Section naming convention at Hollywood Bowl:
  H       : Front orchestra rows (best in house)
  W1-W3   : West box sections (left side when facing stage)
  G2      : Garden box section (center-left area)
  P1      : Pool section / premium center
  M1-M2   : Mid-orchestra
  N1      : Near / 2nd mid section
  F2-F3   : Further mid (terrace transition)
  J1-J2   : Rear terrace, lower
  K2      : Rear terrace, mid
  L1      : Rear terrace, lower-right
  Q1-Q2   : High terrace
  T1-T2   : Top of terrace
  U1      : Upper section
  X1      : Extreme upper / bench
  GARDEN  : Garden boxes (side)

Quality score model:
  H (front orchestra): 90–95
  P (premium center):  85–90
  W/G boxes:           76–82
  M, N:                68–78
  F sections:          60–68
  J, K, L:             52–62
  Q sections:          44–52
  T, U:                36–44
  X, extreme back:     28–36
"""

from __future__ import annotations
from typing import TypedDict, Optional

VENUE_SLUG  = "hollywood-bowl"
VENUE_NAME  = "Hollywood Bowl"
VENUE_CITY  = "Los Angeles"
VENUE_STATE = "CA"
VENUE_CAPACITY = 17500


class SectionDef(TypedDict):
    section_id: str
    display_name: str
    tier: str
    level: str
    zone: str
    side: str
    quality_score: int
    is_premium: bool
    future_map_key: str


_TIER_BASE = {
    "FRONT_ORCH":    92,  # Section H
    "PREMIUM_BOX":   82,  # W, G, P boxes
    "MID_ORCH":      72,  # M, N
    "REAR_ORCH":     62,  # F
    "TERRACE_LOW":   54,  # J, K, L
    "TERRACE_HIGH":  44,  # Q, T
    "UPPER":         34,  # U, X
}

def _q(tier: str, bonus: int = 0) -> int:
    return max(1, min(100, _TIER_BASE[tier] + bonus))


SECTIONS: list[SectionDef] = [

    # ── H — Front Orchestra (closest to stage) ────────────────────────────────
    {"section_id": "H", "display_name": "Section H", "tier": "FRONT_ORCH",
     "level": "orchestra", "zone": "front_center", "side": "center",
     "quality_score": _q("FRONT_ORCH", 0), "is_premium": True, "future_map_key": "bowl_H"},

    # ── Premium center / pool section ─────────────────────────────────────────
    {"section_id": "P1", "display_name": "Section P1", "tier": "PREMIUM_BOX",
     "level": "orchestra", "zone": "premium_center", "side": "center",
     "quality_score": _q("PREMIUM_BOX", 6), "is_premium": True, "future_map_key": "bowl_P1"},

    # ── West box sections (left facing stage) ─────────────────────────────────
    {"section_id": "W1", "display_name": "Section W1", "tier": "PREMIUM_BOX",
     "level": "box", "zone": "box_west", "side": "west",
     "quality_score": _q("PREMIUM_BOX", 2), "is_premium": True, "future_map_key": "bowl_W1"},

    {"section_id": "W2", "display_name": "Section W2", "tier": "PREMIUM_BOX",
     "level": "box", "zone": "box_west", "side": "west",
     "quality_score": _q("PREMIUM_BOX", 0), "is_premium": True, "future_map_key": "bowl_W2"},

    {"section_id": "W3", "display_name": "Section W3", "tier": "PREMIUM_BOX",
     "level": "box", "zone": "box_west", "side": "west",
     "quality_score": _q("PREMIUM_BOX", -2), "is_premium": False, "future_map_key": "bowl_W3"},

    # ── Garden box ────────────────────────────────────────────────────────────
    {"section_id": "G2", "display_name": "Section G2", "tier": "PREMIUM_BOX",
     "level": "box", "zone": "box_center", "side": "center",
     "quality_score": _q("PREMIUM_BOX", 0), "is_premium": True, "future_map_key": "bowl_G2"},

    {"section_id": "GARDEN", "display_name": "Garden Boxes", "tier": "PREMIUM_BOX",
     "level": "box", "zone": "box_side", "side": "west",
     "quality_score": _q("PREMIUM_BOX", -4), "is_premium": True, "future_map_key": "bowl_GARDEN"},

    # ── M sections — mid-orchestra ─────────────────────────────────────────────
    {"section_id": "M1", "display_name": "Section M1", "tier": "MID_ORCH",
     "level": "orchestra", "zone": "mid_center", "side": "center",
     "quality_score": _q("MID_ORCH", 4), "is_premium": False, "future_map_key": "bowl_M1"},

    {"section_id": "M2", "display_name": "Section M2", "tier": "MID_ORCH",
     "level": "orchestra", "zone": "mid_center", "side": "center",
     "quality_score": _q("MID_ORCH", 0), "is_premium": False, "future_map_key": "bowl_M2"},

    # ── N section ─────────────────────────────────────────────────────────────
    {"section_id": "N1", "display_name": "Section N1", "tier": "MID_ORCH",
     "level": "orchestra", "zone": "mid_center", "side": "center",
     "quality_score": _q("MID_ORCH", -2), "is_premium": False, "future_map_key": "bowl_N1"},

    # ── F sections — further mid / terrace transition ──────────────────────────
    {"section_id": "F2", "display_name": "Section F2", "tier": "REAR_ORCH",
     "level": "orchestra", "zone": "rear_center", "side": "center",
     "quality_score": _q("REAR_ORCH", 2), "is_premium": False, "future_map_key": "bowl_F2"},

    {"section_id": "F3", "display_name": "Section F3", "tier": "REAR_ORCH",
     "level": "orchestra", "zone": "rear_center", "side": "center",
     "quality_score": _q("REAR_ORCH", 0), "is_premium": False, "future_map_key": "bowl_F3"},

    # ── J sections — terrace lower ─────────────────────────────────────────────
    {"section_id": "J1", "display_name": "Section J1", "tier": "TERRACE_LOW",
     "level": "terrace", "zone": "terrace_low_center", "side": "center",
     "quality_score": _q("TERRACE_LOW", 4), "is_premium": False, "future_map_key": "bowl_J1"},

    {"section_id": "J2", "display_name": "Section J2", "tier": "TERRACE_LOW",
     "level": "terrace", "zone": "terrace_low_center", "side": "center",
     "quality_score": _q("TERRACE_LOW", 2), "is_premium": False, "future_map_key": "bowl_J2"},

    # ── K section ─────────────────────────────────────────────────────────────
    {"section_id": "K2", "display_name": "Section K2", "tier": "TERRACE_LOW",
     "level": "terrace", "zone": "terrace_low_right", "side": "east",
     "quality_score": _q("TERRACE_LOW", 0), "is_premium": False, "future_map_key": "bowl_K2"},

    # ── L section ─────────────────────────────────────────────────────────────
    {"section_id": "L1", "display_name": "Section L1", "tier": "TERRACE_LOW",
     "level": "terrace", "zone": "terrace_low_right", "side": "east",
     "quality_score": _q("TERRACE_LOW", -2), "is_premium": False, "future_map_key": "bowl_L1"},

    # ── Q sections — high terrace ──────────────────────────────────────────────
    {"section_id": "Q1", "display_name": "Section Q1", "tier": "TERRACE_HIGH",
     "level": "terrace", "zone": "terrace_high_center", "side": "center",
     "quality_score": _q("TERRACE_HIGH", 4), "is_premium": False, "future_map_key": "bowl_Q1"},

    {"section_id": "Q2", "display_name": "Section Q2", "tier": "TERRACE_HIGH",
     "level": "terrace", "zone": "terrace_high_center", "side": "center",
     "quality_score": _q("TERRACE_HIGH", 0), "is_premium": False, "future_map_key": "bowl_Q2"},

    # ── T sections — top of terrace ────────────────────────────────────────────
    {"section_id": "T1", "display_name": "Section T1", "tier": "TERRACE_HIGH",
     "level": "terrace", "zone": "terrace_top", "side": "center",
     "quality_score": _q("TERRACE_HIGH", -2), "is_premium": False, "future_map_key": "bowl_T1"},

    {"section_id": "T2", "display_name": "Section T2", "tier": "TERRACE_HIGH",
     "level": "terrace", "zone": "terrace_top", "side": "center",
     "quality_score": _q("TERRACE_HIGH", -4), "is_premium": False, "future_map_key": "bowl_T2"},

    # ── U section — upper ──────────────────────────────────────────────────────
    {"section_id": "U1", "display_name": "Section U1", "tier": "UPPER",
     "level": "upper", "zone": "upper_center", "side": "center",
     "quality_score": _q("UPPER", 2), "is_premium": False, "future_map_key": "bowl_U1"},

    # ── X section — extreme upper ──────────────────────────────────────────────
    {"section_id": "X1", "display_name": "Section X1", "tier": "UPPER",
     "level": "upper", "zone": "upper_far", "side": "center",
     "quality_score": _q("UPPER", -2), "is_premium": False, "future_map_key": "bowl_X1"},
]


# ── Aliases ────────────────────────────────────────────────────────────────────
class _Alias(TypedDict):
    section_id: str
    marketplace_id: Optional[int]
    alias: str

ALIASES: list[_Alias] = []

def _a(sid: str, mp_id: Optional[int], alias: str):
    ALIASES.append({"section_id": sid, "marketplace_id": mp_id, "alias": alias})


# Helper: for each section, generate "X", "Section X", "Sec X"
def _aliases_for(sid: str, letter: str):
    _a(sid, None, letter)
    _a(sid, None, letter.upper())
    _a(sid, None, f"Section {letter}")
    _a(sid, None, f"Section {letter.upper()}")
    _a(sid, None, f"Sec {letter}")
    _a(sid, None, f"Sec {letter.upper()}")
    _a(sid, None, f"Row {letter}")
    _a(sid, None, f"Row {letter.upper()}")


_aliases_for("H", "H")
_aliases_for("P1", "P1")
_aliases_for("W1", "W1")
_aliases_for("W2", "W2")
_aliases_for("W3", "W3")
_aliases_for("G2", "G2")

for _alias in ["Garden", "GARDEN", "Garden Boxes", "GARDEN BOXES", "Garden Box",
               "Section Garden", "Garden (Boxes)", "Garden Terrace"]:
    _a("GARDEN", None, _alias)

_aliases_for("M1", "M1")
_aliases_for("M2", "M2")
_aliases_for("N1", "N1")
_aliases_for("F2", "F2")
_aliases_for("F3", "F3")
_aliases_for("J1", "J1")
_aliases_for("J2", "J2")
_aliases_for("K2", "K2")
_aliases_for("L1", "L1")
_aliases_for("Q1", "Q1")
_aliases_for("Q2", "Q2")
_aliases_for("T1", "T1")
_aliases_for("T2", "T2")
_aliases_for("U1", "U1")
_aliases_for("X1", "X1")


# ── Build lookup tables ────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    return s.strip().lower()

SECTION_BY_ID: dict[str, SectionDef] = {s["section_id"]: s for s in SECTIONS}
ALIAS_LOOKUP: dict[tuple[int | None, str], str] = {}
for _a_def in ALIASES:
    ALIAS_LOOKUP[(_a_def["marketplace_id"], _norm(_a_def["alias"]))] = _a_def["section_id"]
