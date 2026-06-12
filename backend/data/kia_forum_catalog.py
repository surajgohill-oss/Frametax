"""
Kia Forum — Canonical Section Catalog
======================================

Physical layout (concert configuration, stage at south end):
  Floor (Pit) : Letter sections A–H (GA / reserved, closest to stage)
  Lower bowl  : Sections 101–130 (100s ring, single tier)
  Upper bowl  : Sections 201–234 (200s ring, upper tier)
  Special     : UPPER BOWL HOT SEAT, LOWER BOWL FIRST 25 VIP

Sections rotate clockwise: stage-adjacent south → west → north (opposite) → east → back to south.

Quality score model (1–100):
  Floor/Pit letters (stage):    85–92
  Lower bowl stage-side (100s): 72–82
  Lower bowl side (100s):       65–75
  Lower bowl opp (100s):        55–65
  Upper bowl stage-side (200s): 50–58
  Upper bowl side (200s):       42–52
  Upper bowl opp (200s):        34–42
"""

from __future__ import annotations
from typing import TypedDict, Optional

VENUE_SLUG  = "kia-forum"
VENUE_NAME  = "Kia Forum"
VENUE_CITY  = "Inglewood"
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
    "FLOOR":        88,
    "LOWER_STAGE":  76,
    "LOWER_SIDE":   68,
    "LOWER_OPP":    58,
    "UPPER_STAGE":  52,
    "UPPER_SIDE":   46,
    "UPPER_OPP":    36,
    "SPECIAL":      72,
}

def _q(tier: str, bonus: int = 0) -> int:
    return max(1, min(100, _TIER_BASE[tier] + bonus))


SECTIONS: list[SectionDef] = [

    # ── Floor / Pit letter sections (concert GA or reserved floor) ────────────
    # A = directly in front of stage; B-D mid-floor; E-H far floor

    {"section_id": "floor-a", "display_name": "Floor A", "tier": "FLOOR",
     "level": "floor", "zone": "floor_stage", "side": "south",
     "quality_score": _q("FLOOR", 4),  "is_premium": True, "future_map_key": "kia_floor_a"},

    {"section_id": "floor-b", "display_name": "Floor B", "tier": "FLOOR",
     "level": "floor", "zone": "floor_stage", "side": "south",
     "quality_score": _q("FLOOR", 2),  "is_premium": False, "future_map_key": "kia_floor_b"},

    {"section_id": "floor-c", "display_name": "Floor C", "tier": "FLOOR",
     "level": "floor", "zone": "floor_mid", "side": "center",
     "quality_score": _q("FLOOR", 0),  "is_premium": False, "future_map_key": "kia_floor_c"},

    {"section_id": "floor-d", "display_name": "Floor D", "tier": "FLOOR",
     "level": "floor", "zone": "floor_mid", "side": "center",
     "quality_score": _q("FLOOR", 0),  "is_premium": False, "future_map_key": "kia_floor_d"},

    {"section_id": "floor-e", "display_name": "Floor E", "tier": "FLOOR",
     "level": "floor", "zone": "floor_far", "side": "north",
     "quality_score": _q("FLOOR", -2), "is_premium": False, "future_map_key": "kia_floor_e"},

    {"section_id": "floor-f", "display_name": "Floor F", "tier": "FLOOR",
     "level": "floor", "zone": "floor_far", "side": "north",
     "quality_score": _q("FLOOR", -4), "is_premium": False, "future_map_key": "kia_floor_f"},

    {"section_id": "floor-g", "display_name": "Floor G", "tier": "FLOOR",
     "level": "floor", "zone": "floor_far", "side": "north",
     "quality_score": _q("FLOOR", -6), "is_premium": False, "future_map_key": "kia_floor_g"},

    {"section_id": "floor-h", "display_name": "Floor H", "tier": "FLOOR",
     "level": "floor", "zone": "floor_far", "side": "north",
     "quality_score": _q("FLOOR", -8), "is_premium": False, "future_map_key": "kia_floor_h"},

    # ── Special floor designations ────────────────────────────────────────────
    {"section_id": "lower-bowl-vip", "display_name": "Lower Bowl VIP", "tier": "SPECIAL",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("SPECIAL", 8), "is_premium": True, "future_map_key": "kia_lower_vip"},

    {"section_id": "upper-bowl-hot-seat", "display_name": "Upper Bowl Hot Seat", "tier": "SPECIAL",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("SPECIAL", 0), "is_premium": True, "future_map_key": "kia_upper_hot"},

    # ── Lower bowl — 100s ─────────────────────────────────────────────────────
    # Sections 101-120 approximate stage-side; 121-130 rotate around

    {"section_id": "101", "display_name": "Section 101", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 6),  "is_premium": False, "future_map_key": "kia_101"},

    {"section_id": "102", "display_name": "Section 102", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 4),  "is_premium": False, "future_map_key": "kia_102"},

    {"section_id": "103", "display_name": "Section 103", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 2),  "is_premium": False, "future_map_key": "kia_103"},

    {"section_id": "104", "display_name": "Section 104", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 6),   "is_premium": False, "future_map_key": "kia_104"},

    {"section_id": "105", "display_name": "Section 105", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 4),   "is_premium": False, "future_map_key": "kia_105"},

    {"section_id": "106", "display_name": "Section 106", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 4),   "is_premium": False, "future_map_key": "kia_106"},

    {"section_id": "107", "display_name": "Section 107", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 6),   "is_premium": False, "future_map_key": "kia_107"},

    {"section_id": "108", "display_name": "Section 108", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 2),   "is_premium": False, "future_map_key": "kia_108"},

    {"section_id": "109", "display_name": "Section 109", "tier": "LOWER_OPP",
     "level": "lower", "zone": "lower_opp", "side": "north",
     "quality_score": _q("LOWER_OPP", 4),    "is_premium": False, "future_map_key": "kia_109"},

    {"section_id": "110", "display_name": "Section 110", "tier": "LOWER_OPP",
     "level": "lower", "zone": "lower_opp", "side": "north",
     "quality_score": _q("LOWER_OPP", 2),    "is_premium": False, "future_map_key": "kia_110"},

    {"section_id": "111", "display_name": "Section 111", "tier": "LOWER_OPP",
     "level": "lower", "zone": "lower_opp", "side": "north",
     "quality_score": _q("LOWER_OPP", 0),    "is_premium": False, "future_map_key": "kia_111"},

    {"section_id": "112", "display_name": "Section 112", "tier": "LOWER_OPP",
     "level": "lower", "zone": "lower_opp", "side": "north",
     "quality_score": _q("LOWER_OPP", 0),    "is_premium": False, "future_map_key": "kia_112"},

    {"section_id": "113", "display_name": "Section 113", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 2),   "is_premium": False, "future_map_key": "kia_113"},

    {"section_id": "114", "display_name": "Section 114", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 4),   "is_premium": False, "future_map_key": "kia_114"},

    {"section_id": "115", "display_name": "Section 115", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 4),   "is_premium": False, "future_map_key": "kia_115"},

    {"section_id": "116", "display_name": "Section 116", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 6),   "is_premium": False, "future_map_key": "kia_116"},

    {"section_id": "117", "display_name": "Section 117", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 2),  "is_premium": False, "future_map_key": "kia_117"},

    {"section_id": "118", "display_name": "Section 118", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 4),  "is_premium": False, "future_map_key": "kia_118"},

    {"section_id": "119", "display_name": "Section 119", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 6),  "is_premium": False, "future_map_key": "kia_119"},

    {"section_id": "120", "display_name": "Section 120", "tier": "LOWER_STAGE",
     "level": "lower", "zone": "lower_stage", "side": "south",
     "quality_score": _q("LOWER_STAGE", 4),  "is_premium": False, "future_map_key": "kia_120"},

    # Sections 124-130 (behind stage-adjacent wrap)
    {"section_id": "124", "display_name": "Section 124", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_124"},

    {"section_id": "125", "display_name": "Section 125", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_125"},

    {"section_id": "126", "display_name": "Section 126", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_west", "side": "west",
     "quality_score": _q("LOWER_SIDE", 2),   "is_premium": False, "future_map_key": "kia_126"},

    {"section_id": "127", "display_name": "Section 127", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 2),   "is_premium": False, "future_map_key": "kia_127"},

    {"section_id": "128", "display_name": "Section 128", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_128"},

    {"section_id": "129", "display_name": "Section 129", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_129"},

    {"section_id": "130", "display_name": "Section 130", "tier": "LOWER_SIDE",
     "level": "lower", "zone": "lower_side_east", "side": "east",
     "quality_score": _q("LOWER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_130"},

    # ── Upper bowl — 200s ─────────────────────────────────────────────────────

    {"section_id": "201", "display_name": "Section 201", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 4),  "is_premium": False, "future_map_key": "kia_201"},

    {"section_id": "202", "display_name": "Section 202", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 4),  "is_premium": False, "future_map_key": "kia_202"},

    {"section_id": "203", "display_name": "Section 203", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 2),  "is_premium": False, "future_map_key": "kia_203"},

    {"section_id": "204", "display_name": "Section 204", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 4),   "is_premium": False, "future_map_key": "kia_204"},

    {"section_id": "205", "display_name": "Section 205", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 2),   "is_premium": False, "future_map_key": "kia_205"},

    {"section_id": "206", "display_name": "Section 206", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 2),   "is_premium": False, "future_map_key": "kia_206"},

    {"section_id": "207", "display_name": "Section 207", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 4),   "is_premium": False, "future_map_key": "kia_207"},

    {"section_id": "208", "display_name": "Section 208", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 2),   "is_premium": False, "future_map_key": "kia_208"},

    {"section_id": "209", "display_name": "Section 209", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 4),    "is_premium": False, "future_map_key": "kia_209"},

    {"section_id": "210", "display_name": "Section 210", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 2),    "is_premium": False, "future_map_key": "kia_210"},

    {"section_id": "211", "display_name": "Section 211", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 0),    "is_premium": False, "future_map_key": "kia_211"},

    {"section_id": "212", "display_name": "Section 212", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 0),    "is_premium": False, "future_map_key": "kia_212"},

    {"section_id": "213", "display_name": "Section 213", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", 0),    "is_premium": False, "future_map_key": "kia_213"},

    {"section_id": "214", "display_name": "Section 214", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 2),   "is_premium": False, "future_map_key": "kia_214"},

    {"section_id": "215", "display_name": "Section 215", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 4),   "is_premium": False, "future_map_key": "kia_215"},

    {"section_id": "216", "display_name": "Section 216", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 2),   "is_premium": False, "future_map_key": "kia_216"},

    {"section_id": "217", "display_name": "Section 217", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 4),   "is_premium": False, "future_map_key": "kia_217"},

    {"section_id": "218", "display_name": "Section 218", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 2),  "is_premium": False, "future_map_key": "kia_218"},

    {"section_id": "219", "display_name": "Section 219", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 4),  "is_premium": False, "future_map_key": "kia_219"},

    {"section_id": "220", "display_name": "Section 220", "tier": "UPPER_STAGE",
     "level": "upper", "zone": "upper_stage", "side": "south",
     "quality_score": _q("UPPER_STAGE", 4),  "is_premium": False, "future_map_key": "kia_220"},

    {"section_id": "224", "display_name": "Section 224", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_224"},

    {"section_id": "225", "display_name": "Section 225", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_west", "side": "west",
     "quality_score": _q("UPPER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_225"},

    {"section_id": "226", "display_name": "Section 226", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", -2),   "is_premium": False, "future_map_key": "kia_226"},

    {"section_id": "227", "display_name": "Section 227", "tier": "UPPER_OPP",
     "level": "upper", "zone": "upper_opp", "side": "north",
     "quality_score": _q("UPPER_OPP", -2),   "is_premium": False, "future_map_key": "kia_227"},

    {"section_id": "229", "display_name": "Section 229", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_229"},

    {"section_id": "232", "display_name": "Section 232", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_232"},

    {"section_id": "233", "display_name": "Section 233", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_233"},

    {"section_id": "234", "display_name": "Section 234", "tier": "UPPER_SIDE",
     "level": "upper", "zone": "upper_side_east", "side": "east",
     "quality_score": _q("UPPER_SIDE", 0),   "is_premium": False, "future_map_key": "kia_234"},
]


# ── Aliases ────────────────────────────────────────────────────────────────────
class _Alias(TypedDict):
    section_id: str
    marketplace_id: Optional[int]
    alias: str

ALIASES: list[_Alias] = []

def _a(sid: str, mp_id: Optional[int], alias: str):
    ALIASES.append({"section_id": sid, "marketplace_id": mp_id, "alias": alias})

# Floor letter sections — many listing variants
for _letter, _sid in [("A","floor-a"),("B","floor-b"),("C","floor-c"),("D","floor-d"),
                       ("E","floor-e"),("F","floor-f"),("G","floor-g"),("H","floor-h")]:
    for _pfx in ["", "Floor ", "Section ", "Pit ", "GA "]:
        _a(_sid, None, f"{_pfx}{_letter}")
        _a(_sid, None, f"{_pfx}{_letter}".upper())

# Special sections
for _alias in ["UPPER BOWL HOT SEAT", "Upper Bowl Hot Seat", "Hot Seat", "HOTSEAT"]:
    _a("upper-bowl-hot-seat", None, _alias)
for _alias in ["LOWER BOWL FIRST 25 VIP", "Lower Bowl First 25 VIP",
               "LOWER BOWL VIP", "Lower Bowl VIP", "First 25 VIP", "FIRST 25 VIP"]:
    _a("lower-bowl-vip", None, _alias)

# Numbered lower bowl 100s
for _n in range(101, 131):
    _a(str(_n), None, f"Section {_n}")
    _a(str(_n), None, str(_n))
    _a(str(_n), None, f"Sec {_n}")

# Numbered upper bowl 200s
for _n in [201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,
           218,219,220,224,225,226,227,229,232,233,234]:
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
