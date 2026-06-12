"""
Greek Theatre (Los Angeles) — Canonical Section Catalog
=======================================================

Physical layout (outdoor amphitheater, Griffith Park):
  Open-air hillside venue, stage at south end facing audience on slope.
  Capacity ~5,900. Intimate venue with strong proximity to stage.

Section layout (front to back):
  Pit            : GA standing directly in front of stage (no seat)
  VIP Boxes      : Premium box seating on left/right flanks at stage level
  Reserved A     : Closest fixed seating, rows A-front (center / full width)
  Reserved B     : Mid-orchestra seating
  Reserved C     : Rear orchestra seating
  Terrace        : Upper hillside section (stone steps/bleacher-style)
  Benches        : Rear bench seating (lawn-like)

Quality score model:
  Pit:          92 (closest to performer, GA)
  VIP Boxes:    85 (premium sight-lines from sides)
  Reserved A:   76 (front orchestra, center)
  Reserved B:   65 (mid)
  Reserved C:   54 (rear orchestra)
  Terrace:      44 (upper hillside)
  Benches:      34 (farthest back)
"""

from __future__ import annotations
from typing import TypedDict, Optional

VENUE_SLUG  = "greek-theatre"
VENUE_NAME  = "Greek Theatre"
VENUE_CITY  = "Los Angeles"
VENUE_STATE = "CA"
VENUE_CAPACITY = 5900


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


SECTIONS: list[SectionDef] = [
    # ── Pit — GA in front of stage ────────────────────────────────────────────
    {"section_id": "pit",        "display_name": "Pit",         "tier": "PIT",
     "level": "floor", "zone": "pit", "side": "center",
     "quality_score": 92, "is_premium": True, "future_map_key": "greek_pit"},

    # ── VIP Boxes — left/right flank at stage level ────────────────────────────
    {"section_id": "vip-boxes",  "display_name": "VIP Boxes",   "tier": "VIP_BOX",
     "level": "floor", "zone": "vip_box", "side": "side",
     "quality_score": 85, "is_premium": True, "future_map_key": "greek_vip_boxes"},

    # ── Reserved A — front orchestra ───────────────────────────────────────────
    {"section_id": "reserved-a", "display_name": "Reserved A",  "tier": "RESERVED_A",
     "level": "orchestra", "zone": "front_center", "side": "center",
     "quality_score": 76, "is_premium": False, "future_map_key": "greek_reserved_a"},

    # ── Reserved B — mid orchestra ─────────────────────────────────────────────
    {"section_id": "reserved-b", "display_name": "Reserved B",  "tier": "RESERVED_B",
     "level": "orchestra", "zone": "mid_center", "side": "center",
     "quality_score": 65, "is_premium": False, "future_map_key": "greek_reserved_b"},

    # ── Reserved C — rear orchestra ────────────────────────────────────────────
    {"section_id": "reserved-c", "display_name": "Reserved C",  "tier": "RESERVED_C",
     "level": "orchestra", "zone": "rear_center", "side": "center",
     "quality_score": 54, "is_premium": False, "future_map_key": "greek_reserved_c"},

    # ── Terrace — upper hillside ───────────────────────────────────────────────
    {"section_id": "terrace",    "display_name": "Terrace",      "tier": "TERRACE",
     "level": "terrace", "zone": "upper_center", "side": "center",
     "quality_score": 44, "is_premium": False, "future_map_key": "greek_terrace"},

    # ── Benches — rear bench seating ──────────────────────────────────────────
    {"section_id": "benches",    "display_name": "Benches",      "tier": "BENCH",
     "level": "terrace", "zone": "rear_upper", "side": "center",
     "quality_score": 34, "is_premium": False, "future_map_key": "greek_benches"},
]


# ── Aliases ────────────────────────────────────────────────────────────────────
class _Alias(TypedDict):
    section_id: str
    marketplace_id: Optional[int]
    alias: str

ALIASES: list[_Alias] = []

def _a(sid: str, mp_id: Optional[int], alias: str):
    ALIASES.append({"section_id": sid, "marketplace_id": mp_id, "alias": alias})


# ── Pit aliases ───────────────────────────────────────────────────────────────
for _alias in ["Pit", "PIT", "pit", "GA Pit", "GA PIT", "General Admission Pit",
               "Floor Pit", "Floor GA", "GA Floor"]:
    _a("pit", None, _alias)

# ── VIP Box aliases ───────────────────────────────────────────────────────────
for _alias in ["VIP Boxes", "VIP BOX", "VIP BOXES", "VIP Box", "Vip Boxes",
               "VIP PRIVATE BOX", "VIP Private Box", "VIP Private Boxes",
               "ELITE", "Elite", "Elite Box", "ELITE BOX",
               "Private Box", "PRIVATE BOX", "Private VIP",
               "Premium Box", "PREMIUM BOX"]:
    _a("vip-boxes", None, _alias)

# ── Reserved A aliases ────────────────────────────────────────────────────────
for _alias in [
    "Reserved A", "RESERVED A", "Reserved A Center", "Reserved A Left", "Reserved A Right",
    "Section A", "SECTION A", "SEC A", "Sec A",
    "A", "A CENTER", "AC", "AL", "AR",
    "A Left", "A LEFT", "A Right", "A RIGHT", "A Center",
    "Sec. A", "Section A Center", "Section A Left", "Section A Right",
    "RES A", "Res A", "RESERVED-A",
]:
    _a("reserved-a", None, _alias)

# ── Reserved B aliases ────────────────────────────────────────────────────────
for _alias in [
    "Reserved B", "RESERVED B", "Reserved B Center",
    "Section B", "SECTION B", "SEC B", "Sec B",
    "B", "BC", "BL", "BR",
    "B Left", "B RIGHT", "B Center",
    "RES B", "Res B", "RESERVED-B",
]:
    _a("reserved-b", None, _alias)

# ── Reserved C aliases ────────────────────────────────────────────────────────
for _alias in [
    "Reserved C", "RESERVED C",
    "Section C", "SECTION C", "SEC C", "Sec C",
    "C", "Rear C", "REAR C", "C Rear",
    "RES C", "Res C", "RESERVED-C",
]:
    _a("reserved-c", None, _alias)

# ── Terrace aliases ───────────────────────────────────────────────────────────
for _alias in [
    "Terrace", "TERRACE", "TERRAC",
    "South Terrace", "SOUTH TERRACE",
    "Upper Terrace", "UPPER TERRACE",
    "Terrace Level", "TERRACE LEVEL",
    "Hillside", "HILLSIDE",
]:
    _a("terrace", None, _alias)

# ── Bench aliases ─────────────────────────────────────────────────────────────
for _alias in [
    "Benches", "BENCHES", "Bench", "BENCH",
    "Rear Benches", "REAR BENCHES",
    "Upper Benches", "UPPER BENCHES",
    "Lawn", "LAWN",
]:
    _a("benches", None, _alias)


# ── Build lookup tables ────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    return s.strip().lower()

SECTION_BY_ID: dict[str, SectionDef] = {s["section_id"]: s for s in SECTIONS}
ALIAS_LOOKUP: dict[tuple[int | None, str], str] = {}
for _a_def in ALIASES:
    ALIAS_LOOKUP[(_a_def["marketplace_id"], _norm(_a_def["alias"]))] = _a_def["section_id"]
