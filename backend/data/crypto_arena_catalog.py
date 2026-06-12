"""
Crypto.com Arena — Canonical Section Catalog
============================================

Physical layout (concert configuration):
  Floor sections  : Floor 1–12 (numbered from stage end)
  Lower bowl      : Sections 101–119 (sweeps full ring; 100s)
  Suite level     : Not tracked — no active listings
  Upper bowl      : Sections 301–333 (sweeps full ring; 300s)
  Premium Row     : PR 1–PR 20 (press-row adjacent premium seating)

Concert stage typically placed at south end (tunnel end).
Sections closest to stage = highest quality at each level.

Quality score model (1–100):
  Floor (close to stage): 90–95
  Lower bowl (stage-adjacent): 78–86
  Lower bowl (mid-bowl):       70–78
  Lower bowl (far/opposite):   60–70
  PR sections:                 68–75
  Upper bowl (stage-adjacent): 52–60
  Upper bowl (mid-bowl):       44–52
  Upper bowl (far/opposite):   36–44

Marketplace IDs (from Railway marketplaces table):
  2 = VividSeats
  5 = Gametime
  3 = StubHub
  7 = TickPick
"""

from __future__ import annotations
from typing import TypedDict, Optional

VENUE_SLUG = "crypto-arena"
VENUE_NAME = "Crypto.com Arena"
VENUE_CITY = "Los Angeles"
VENUE_STATE = "CA"
VENUE_CAPACITY = 20000


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
    "FLOOR":         90,
    "LOWER_STAGE":   82,
    "LOWER_SIDE":    72,
    "LOWER_OPP":     62,
    "PREMIUM_ROW":   70,
    "UPPER_STAGE":   56,
    "UPPER_SIDE":    46,
    "UPPER_OPP":     36,
}

def _q(tier: str, bonus: int = 0) -> int:
    return max(1, min(100, _TIER_BASE[tier] + bonus))


SECTIONS: list[SectionDef] = [

    # ── Floor sections (concert floor, numbered from stage end) ─────────────────
    # Floor 1–4: closest to stage (south)
    # Floor 5–8: mid-floor
    # Floor 9–12: far floor (opposite stage)

    {"section_id": "floor-1",  "display_name": "Floor 1",  "tier": "FLOOR",
     "level": "floor", "zone": "floor_stage", "side": "south",
     "quality_score": _q("FLOOR", 5),  "is_premium": True, "future_map_key": "crypto_floor_1"},

    {"section_id": "floor-2",  "display_name": "Floor 2",  "tier": "FLOOR",
     "level": "floor", "zone": "floor_stage", "side": "south",
     "quality_score": _q("FLOOR", 5),  "is_premium": True, "future_map_key": "crypto_floor_2"},

    {"section_id": "floor-3",  "display_name": "Floor 3",  "tier": "FLOOR",
     "level": "floor", "zone": "floor_stage", "side": "south",
     "quality_score": _q("FLOOR", 4),  "is_premium": True, "future_map_key": "crypto_floor_3"},

    {"section_id": "floor-4",  "display_name": "Floor 4",  "tier": "FLOOR",
     "level": "floor", "zone": "floor_mid", "side": "south",
     "quality_score": _q("FLOOR", 2),  "is_premium": False, "future_map_key": "crypto_floor_4"},

    {"section_id": "floor-5",  "display_name": "Floor 5",  "tier": "FLOOR",
     "level": "floor", "zone": "floor_mid", "side": "center",
     "quality_score": _q("FLOOR", 0),  "is_premium": False, "future_map_key": "crypto_floor_5"},

    {"section_id": "floor-6",  "display_name": "Floor 6",  "tier": "FLOOR",
     "level": "floor", "zone": "floor_mid", "side": "center",
     "quality_score": _q("FLOOR", 0),  "is_premium": False, "future_map_key": "crypto_floor_6"},

    {"section_id": "floor-7",  "display_name": "Floor 7",  "tier": "FLOOR",
     "level": "floor", "zone": "floor_far", "side": "north",
     "quality_score": _q("FLOOR", -2), "is_premium": False, "future_map_key": "crypto_floor_7"},

    {"section_id": "floor-8",  "display_name": "Floor 8",  "tier": "FLOOR",
     "level": "floor", "zone": "floor_far", "side": "north",
     "quality_score": _q("FLOOR", -4), "is_premium": False, "future_map_key": "crypto_floor_8"},

    # ── Lower bowl — Stage end (101–107 approximate) ────────────────────────────
    # South/stage adjacent sections — highest lower bowl quality

    {"section_id": "101", "display_name": "Section 101", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 4),  "is_premium": False, "future_map_key": "crypto_101"},

    {"section_id": "102", "display_name": "Section 102", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 4),  "is_premium": False, "future_map_key": "crypto_102"},

    {"section_id": "103", "display_name": "Section 103", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 2),  "is_premium": False, "future_map_key": "crypto_103"},

    {"section_id": "104", "display_name": "Section 104", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 0),  "is_premium": False, "future_map_key": "crypto_104"},

    {"section_id": "105", "display_name": "Section 105", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 4),   "is_premium": False, "future_map_key": "crypto_105"},

    {"section_id": "106", "display_name": "Section 106", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 6),   "is_premium": True,  "future_map_key": "crypto_106"},

    {"section_id": "107", "display_name": "Section 107", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 4),   "is_premium": False, "future_map_key": "crypto_107"},

    {"section_id": "108", "display_name": "Section 108", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 8),   "is_premium": True,  "future_map_key": "crypto_108"},

    {"section_id": "109", "display_name": "Section 109", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 6),   "is_premium": False, "future_map_key": "crypto_109"},

    {"section_id": "110", "display_name": "Section 110", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 4),   "is_premium": False, "future_map_key": "crypto_110"},

    {"section_id": "111", "display_name": "Section 111", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 2),   "is_premium": False, "future_map_key": "crypto_111"},

    {"section_id": "112", "display_name": "Section 112", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 4),   "is_premium": False, "future_map_key": "crypto_112"},

    {"section_id": "113", "display_name": "Section 113", "tier": "LOWER_OPP",
     "level": "lower", "zone": "lower_opp", "side": "north",
     "quality_score": _q("LOWER_OPP", 2),    "is_premium": False, "future_map_key": "crypto_113"},

    {"section_id": "114", "display_name": "Section 114", "tier": "LOWER_OPP",
     "level": "lower", "zone": "lower_opp", "side": "north",
     "quality_score": _q("LOWER_OPP", 0),    "is_premium": False, "future_map_key": "crypto_114"},

    {"section_id": "115", "display_name": "Section 115", "tier": "LOWER_OPP",
     "level": "lower", "zone": "lower_opp", "side": "north",
     "quality_score": _q("LOWER_OPP", 0),    "is_premium": False, "future_map_key": "crypto_115"},

    {"section_id": "116", "display_name": "Section 116", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", -2),  "is_premium": False, "future_map_key": "crypto_116"},

    {"section_id": "117", "display_name": "Section 117", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 0),   "is_premium": False, "future_map_key": "crypto_117"},

    {"section_id": "118", "display_name": "Section 118", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 2),   "is_premium": False, "future_map_key": "crypto_118"},

    {"section_id": "119", "display_name": "Section 119", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 4),   "is_premium": False, "future_map_key": "crypto_119"},

    # ── Premium Row (PR) sections — court/floor adjacent ───────────────────────
    {"section_id": "pr-1",  "display_name": "PR 1",  "tier": "PREMIUM_ROW",
     "level": "floor", "zone": "premium_row", "side": "west",
     "quality_score": _q("PREMIUM_ROW", 5),  "is_premium": True, "future_map_key": "crypto_pr1"},

    {"section_id": "pr-2",  "display_name": "PR 2",  "tier": "PREMIUM_ROW",
     "level": "floor", "zone": "premium_row", "side": "west",
     "quality_score": _q("PREMIUM_ROW", 5),  "is_premium": True, "future_map_key": "crypto_pr2"},

    {"section_id": "pr-3",  "display_name": "PR 3",  "tier": "PREMIUM_ROW",
     "level": "floor", "zone": "premium_row", "side": "west",
     "quality_score": _q("PREMIUM_ROW", 4),  "is_premium": True, "future_map_key": "crypto_pr3"},

    {"section_id": "pr-4",  "display_name": "PR 4",  "tier": "PREMIUM_ROW",
     "level": "floor", "zone": "premium_row", "side": "east",
     "quality_score": _q("PREMIUM_ROW", 4),  "is_premium": True, "future_map_key": "crypto_pr4"},

    {"section_id": "pr-5",  "display_name": "PR 5",  "tier": "PREMIUM_ROW",
     "level": "floor", "zone": "premium_row", "side": "east",
     "quality_score": _q("PREMIUM_ROW", 3),  "is_premium": True, "future_map_key": "crypto_pr5"},

    {"section_id": "pr-15", "display_name": "PR 15", "tier": "PREMIUM_ROW",
     "level": "floor", "zone": "premium_row", "side": "south",
     "quality_score": _q("PREMIUM_ROW", 2),  "is_premium": True, "future_map_key": "crypto_pr15"},

    # ── Upper bowl — Stage end (301–308 approximate) ────────────────────────────
    {"section_id": "301", "display_name": "Section 301", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 4),  "is_premium": False, "future_map_key": "crypto_301"},

    {"section_id": "303", "display_name": "Section 303", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 4),  "is_premium": False, "future_map_key": "crypto_303"},

    {"section_id": "304", "display_name": "Section 304", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 2),  "is_premium": False, "future_map_key": "crypto_304"},

    {"section_id": "305", "display_name": "Section 305", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 4),   "is_premium": False, "future_map_key": "crypto_305"},

    {"section_id": "308", "display_name": "Section 308", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 6),   "is_premium": False, "future_map_key": "crypto_308"},

    {"section_id": "315", "display_name": "Section 315", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 4),   "is_premium": False, "future_map_key": "crypto_315"},

    {"section_id": "316", "display_name": "Section 316", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 2),   "is_premium": False, "future_map_key": "crypto_316"},

    {"section_id": "317", "display_name": "Section 317", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 2),    "is_premium": False, "future_map_key": "crypto_317"},

    {"section_id": "318", "display_name": "Section 318", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 0),    "is_premium": False, "future_map_key": "crypto_318"},

    {"section_id": "319", "display_name": "Section 319", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 0),    "is_premium": False, "future_map_key": "crypto_319"},

    {"section_id": "320", "display_name": "Section 320", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 0),    "is_premium": False, "future_map_key": "crypto_320"},

    {"section_id": "321", "display_name": "Section 321", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 0),    "is_premium": False, "future_map_key": "crypto_321"},

    {"section_id": "323", "display_name": "Section 323", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", -2),   "is_premium": False, "future_map_key": "crypto_323"},

    {"section_id": "325", "display_name": "Section 325", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 0),   "is_premium": False, "future_map_key": "crypto_325"},

    {"section_id": "327", "display_name": "Section 327", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 2),   "is_premium": False, "future_map_key": "crypto_327"},

    {"section_id": "330", "display_name": "Section 330", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 4),   "is_premium": False, "future_map_key": "crypto_330"},

    {"section_id": "331", "display_name": "Section 331", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 6),   "is_premium": False, "future_map_key": "crypto_331"},

    {"section_id": "332", "display_name": "Section 332", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 4),   "is_premium": False, "future_map_key": "crypto_332"},

    {"section_id": "333", "display_name": "Section 333", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 0),  "is_premium": False, "future_map_key": "crypto_333"},
]


# ── Aliases ────────────────────────────────────────────────────────────────────
# Maps raw marketplace strings → canonical section_id
# Format: (marketplace_id_or_None, normalized_raw) → section_id

class _Alias(TypedDict):
    section_id: str
    marketplace_id: Optional[int]
    alias: str

ALIASES: list[_Alias] = []

def _a(sid: str, mp_id: Optional[int], alias: str):
    ALIASES.append({"section_id": sid, "marketplace_id": mp_id, "alias": alias})


# ── Universal aliases (None = any marketplace) ────────────────────────────────

# Floor sections — "Floor N" and "Floor N" variants
for _n in range(1, 13):
    _a(f"floor-{_n}", None, f"Floor {_n}")
    _a(f"floor-{_n}", None, f"Section Floor {_n}")
    _a(f"floor-{_n}", None, f"Floor Section {_n}")

# Numbered lower bowl — "Section NNN" and bare "NNN"
for _n in range(101, 120):
    _a(str(_n), None, f"Section {_n}")
    _a(str(_n), None, str(_n))
    _a(str(_n), None, f"Sec {_n}")

# PR sections — "PR N" and bare
for _n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
    _a(f"pr-{_n}", None, f"PR {_n}")
    _a(f"pr-{_n}", None, f"PR{_n}")
    _a(f"pr-{_n}", None, f"Press Row {_n}")
    _a(f"pr-{_n}", None, f"Premium Row {_n}")

# Numbered upper bowl — "Section NNN" and bare "NNN"
for _n in [301, 303, 304, 305, 308, 315, 316, 317, 318, 319, 320, 321, 323, 325, 327, 330, 331, 332, 333]:
    _a(str(_n), None, f"Section {_n}")
    _a(str(_n), None, str(_n))
    _a(str(_n), None, f"Sec {_n}")


# ── Build lookup tables ────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    return s.strip().lower()

SECTION_BY_ID: dict[str, SectionDef] = {s["section_id"]: s for s in SECTIONS}
ALIAS_LOOKUP: dict[tuple[int | None, str], str] = {}
for _a_def in ALIASES:
    ALIAS_LOOKUP[(_a_def["marketplace_id"], _norm(_a_def["alias"]))] = _a_def["section_id"]
