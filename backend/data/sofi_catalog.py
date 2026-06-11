"""
SoFi Stadium — Canonical Section Catalog
=========================================

Physical layout (all configurations):
  Lower Level  (100s): main lower bowl, field-adjacent
  Club Level   (200s): premium club / suite level
  Upper Level  (300s): upper bowl prime rows
  Upper Top    (400s): upper bowl top / expanded capacity
  Special      (M / C / FLOOR / ARCADE): premium, suite, concert-floor sections

Quality score model (1–100):
  - Based on level (lower > club > upper), sideline/endzone proximity, and premium status
  - Deterministic formula: base_level + midfield_bonus - endzone_penalty
  - Lower sideline midfield (105–113): 80–92
  - Club sideline midfield (207–217):  65–78
  - Upper sideline prime  (307–318):   42–55
  - Endzone sections at each level:    base - 18 penalty
  - Suite / premium sections:          70–88 (access-dependent)
  - Concert floor:                     88–96

Zone model:
  SoFi runs east–west. For NFL/soccer the field runs north–south inside the bowl.
  Sections 101–119 sweep the west sideline from south (101) to north (119).
  Sections 124–128 are east/south endzone lower bowl.
  Sections 201–221 mirror the west club sweep; 228–232 are club endzone.
  Sections 301–350 sweep the full upper bowl ring.
  Sections 407–444 are the upper-top ring (expanded seating).

Alias normalization rules (applied by venue_intelligence.normalize_section):
  1. lowercase + strip whitespace
  2. remove prefix tokens: "section", "sec", level descriptors
  3. extract trailing integer or token as section_id
  4. M-sections and C-sections kept as-is (M32, C11)
  5. FLOOR variants: FLOOR / FLOOR A / FLOOR B / FLOOR C → FLOOR, FLOOR_A, FLOOR_B, FLOOR_C

Marketplace IDs (from Railway marketplaces table):
  2 = VividSeats
  5 = Gametime
  (StubHub, SeatGeek, Ticketmaster, TickPick mapped via aliases when added)
"""

from __future__ import annotations
from typing import TypedDict, Optional

VENUE_SLUG = "sofi_stadium"
VENUE_NAME = "SoFi Stadium"
VENUE_CITY = "Inglewood"
VENUE_STATE = "CA"
VENUE_CAPACITY = 70240


class SectionDef(TypedDict):
    section_id: str       # canonical key used everywhere
    display_name: str     # human-readable label
    tier: str             # tier name (LOWER_SIDELINE, CLUB_ENDZONE, …)
    level: str            # lower | club | upper_mid | upper_top | floor | suite | arcade
    zone: str             # sideline_west | sideline_east | endzone_south | endzone_north |
                          # corner_sw | corner_se | corner_nw | corner_ne | floor | suite
    side: str             # west | east | north | south | center
    quality_score: int    # 1–100, deterministic
    is_premium: bool
    future_map_key: str   # sofi_NNN — stable key for future SVG/heatmap


# ── Tier quality score baselines ────────────────────────────────────────────
# Each tier has a base score; position within the tier adds/subtracts up to 12.
# Formula: score = clamp(base + midfield_bonus, 1, 100)

_TIER_BASE = {
    "FIELD_CLUB":     90,
    "LOWER_SIDELINE": 80,
    "LOWER_CORNER":   64,
    "LOWER_ENDZONE":  54,
    "CLUB_SIDELINE":  68,
    "CLUB_ENDZONE":   50,
    "UPPER_PRIME":    44,
    "UPPER_CORNER":   32,
    "UPPER_ENDZONE":  20,
    "SUITE":          76,
    "FLOOR":          90,
    "ARCADE":         35,
}

def _q(tier: str, bonus: int = 0) -> int:
    return max(1, min(100, _TIER_BASE[tier] + bonus))


# ── Canonical SoFi sections ──────────────────────────────────────────────────

SECTIONS: list[SectionDef] = [

    # ── Lower Level — West Sideline (prime lower bowl) ───────────────────────
    # Sections 101–119 sweep west sideline south-to-north.
    # 101–104: south corner/endzone-adjacent (lower quality)
    # 105–113: midfield premium (highest lower quality)
    # 114–119: north corner/endzone-adjacent

    {"section_id": "101", "display_name": "Section 101", "tier": "LOWER_CORNER",
     "level": "lower", "zone": "corner_sw", "side": "west",
     "quality_score": _q("LOWER_CORNER", 0),  "is_premium": False, "future_map_key": "sofi_101"},

    {"section_id": "102", "display_name": "Section 102", "tier": "LOWER_CORNER",
     "level": "lower", "zone": "corner_sw", "side": "west",
     "quality_score": _q("LOWER_CORNER", 2),  "is_premium": False, "future_map_key": "sofi_102"},

    {"section_id": "103", "display_name": "Section 103", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", -4), "is_premium": False, "future_map_key": "sofi_103"},

    {"section_id": "104", "display_name": "Section 104", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", -2), "is_premium": False, "future_map_key": "sofi_104"},

    {"section_id": "105", "display_name": "Section 105", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", 4),  "is_premium": False, "future_map_key": "sofi_105"},

    {"section_id": "106", "display_name": "Section 106", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", 8),  "is_premium": True,  "future_map_key": "sofi_106"},

    {"section_id": "107", "display_name": "Section 107", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", 10), "is_premium": False, "future_map_key": "sofi_107"},

    {"section_id": "108", "display_name": "Section 108", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", 12), "is_premium": False, "future_map_key": "sofi_108"},

    {"section_id": "109", "display_name": "Section 109", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", 12), "is_premium": False, "future_map_key": "sofi_109"},

    {"section_id": "110", "display_name": "Section 110", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", 10), "is_premium": False, "future_map_key": "sofi_110"},

    {"section_id": "111", "display_name": "Section 111", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", 8),  "is_premium": False, "future_map_key": "sofi_111"},

    {"section_id": "112", "display_name": "Section 112", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", 6),  "is_premium": False, "future_map_key": "sofi_112"},

    {"section_id": "113", "display_name": "Section 113", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", 4),  "is_premium": False, "future_map_key": "sofi_113"},

    {"section_id": "114", "display_name": "Section 114", "tier": "LOWER_SIDELINE",
     "level": "lower", "zone": "sideline_west", "side": "west",
     "quality_score": _q("LOWER_SIDELINE", -2), "is_premium": False, "future_map_key": "sofi_114"},

    {"section_id": "115", "display_name": "Section 115", "tier": "LOWER_CORNER",
     "level": "lower", "zone": "corner_nw", "side": "west",
     "quality_score": _q("LOWER_CORNER", 4),  "is_premium": False, "future_map_key": "sofi_115"},

    {"section_id": "116", "display_name": "Section 116", "tier": "LOWER_CORNER",
     "level": "lower", "zone": "corner_nw", "side": "west",
     "quality_score": _q("LOWER_CORNER", 2),  "is_premium": False, "future_map_key": "sofi_116"},

    {"section_id": "117", "display_name": "Section 117", "tier": "LOWER_CORNER",
     "level": "lower", "zone": "corner_nw", "side": "west",
     "quality_score": _q("LOWER_CORNER", 0),  "is_premium": False, "future_map_key": "sofi_117"},

    {"section_id": "118", "display_name": "Section 118", "tier": "LOWER_CORNER",
     "level": "lower", "zone": "corner_nw", "side": "west",
     "quality_score": _q("LOWER_CORNER", -1), "is_premium": False, "future_map_key": "sofi_118"},

    {"section_id": "119", "display_name": "Section 119", "tier": "LOWER_CORNER",
     "level": "lower", "zone": "corner_nw", "side": "west",
     "quality_score": _q("LOWER_CORNER", -2), "is_premium": False, "future_map_key": "sofi_119"},

    # ── Lower Level — East Endzone / Corner ──────────────────────────────────
    # 124–128: east side lower bowl (endzone/corner area)

    {"section_id": "124", "display_name": "Section 124", "tier": "LOWER_ENDZONE",
     "level": "lower", "zone": "endzone_north", "side": "north",
     "quality_score": _q("LOWER_ENDZONE", 4),  "is_premium": False, "future_map_key": "sofi_124"},

    {"section_id": "125", "display_name": "Section 125", "tier": "LOWER_ENDZONE",
     "level": "lower", "zone": "endzone_north", "side": "north",
     "quality_score": _q("LOWER_ENDZONE", 2),  "is_premium": False, "future_map_key": "sofi_125"},

    {"section_id": "126", "display_name": "Section 126", "tier": "LOWER_ENDZONE",
     "level": "lower", "zone": "endzone_north", "side": "north",
     "quality_score": _q("LOWER_ENDZONE", 0),  "is_premium": False, "future_map_key": "sofi_126"},

    {"section_id": "127", "display_name": "Section 127", "tier": "LOWER_ENDZONE",
     "level": "lower", "zone": "endzone_south", "side": "south",
     "quality_score": _q("LOWER_ENDZONE", 2),  "is_premium": False, "future_map_key": "sofi_127"},

    {"section_id": "128", "display_name": "Section 128", "tier": "LOWER_ENDZONE",
     "level": "lower", "zone": "endzone_south", "side": "south",
     "quality_score": _q("LOWER_ENDZONE", 0),  "is_premium": False, "future_map_key": "sofi_128"},

    # ── Lower Level — Additional (infrequent / special config) ───────────────
    {"section_id": "140", "display_name": "Section 140", "tier": "LOWER_ENDZONE",
     "level": "lower", "zone": "endzone_south", "side": "south",
     "quality_score": _q("LOWER_ENDZONE", -2), "is_premium": False, "future_map_key": "sofi_140"},

    {"section_id": "147", "display_name": "Section 147", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 0), "is_premium": False, "future_map_key": "sofi_147"},

    {"section_id": "149", "display_name": "Section 149", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 0), "is_premium": False, "future_map_key": "sofi_149"},

    {"section_id": "150", "display_name": "Section 150", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 0), "is_premium": False, "future_map_key": "sofi_150"},

    # ── Arcade Level (concert-specific) ──────────────────────────────────────
    {"section_id": "ARCADE_145", "display_name": "Arcade 145", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 4), "is_premium": False, "future_map_key": "sofi_ARCADE_145"},

    {"section_id": "ARCADE_146", "display_name": "Arcade 146", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 4), "is_premium": False, "future_map_key": "sofi_ARCADE_146"},

    {"section_id": "ARCADE_147", "display_name": "Arcade 147", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 4), "is_premium": False, "future_map_key": "sofi_ARCADE_147"},

    {"section_id": "ARCADE_148", "display_name": "Arcade 148", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 4), "is_premium": False, "future_map_key": "sofi_ARCADE_148"},

    {"section_id": "ARCADE_149", "display_name": "Arcade 149", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 4), "is_premium": False, "future_map_key": "sofi_ARCADE_149"},

    {"section_id": "ARCADE_150", "display_name": "Arcade 150", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 4), "is_premium": False, "future_map_key": "sofi_ARCADE_150"},

    {"section_id": "ARCADE_151", "display_name": "Arcade 151", "tier": "ARCADE",
     "level": "arcade", "zone": "endzone_south", "side": "south",
     "quality_score": _q("ARCADE", 4), "is_premium": False, "future_map_key": "sofi_ARCADE_151"},

    # ── Club Level — West Sideline (201–221) ──────────────────────────────────
    # Mirrors lower bowl numbering: 201 = south corner, ~207–215 = midfield, 221 = north corner

    {"section_id": "201", "display_name": "Section 201", "tier": "CLUB_ENDZONE",
     "level": "club", "zone": "corner_sw", "side": "west",
     "quality_score": _q("CLUB_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_201"},

    {"section_id": "202", "display_name": "Section 202", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", -4), "is_premium": False, "future_map_key": "sofi_202"},

    {"section_id": "203", "display_name": "Section 203", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", -2), "is_premium": False, "future_map_key": "sofi_203"},

    {"section_id": "204", "display_name": "Section 204", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 4),  "is_premium": False, "future_map_key": "sofi_204"},

    {"section_id": "205", "display_name": "Section 205", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 6),  "is_premium": False, "future_map_key": "sofi_205"},

    {"section_id": "206", "display_name": "Section 206", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 6),  "is_premium": False, "future_map_key": "sofi_206"},

    {"section_id": "207", "display_name": "Section 207", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 8),  "is_premium": False, "future_map_key": "sofi_207"},

    {"section_id": "209", "display_name": "Section 209", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 8),  "is_premium": True,  "future_map_key": "sofi_209"},

    {"section_id": "210", "display_name": "Section 210", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 8),  "is_premium": False, "future_map_key": "sofi_210"},

    {"section_id": "211", "display_name": "Section 211", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 10), "is_premium": True,  "future_map_key": "sofi_211"},

    {"section_id": "212", "display_name": "Section 212", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 8),  "is_premium": False, "future_map_key": "sofi_212"},

    {"section_id": "213", "display_name": "Section 213", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 6),  "is_premium": False, "future_map_key": "sofi_213"},

    {"section_id": "214", "display_name": "Section 214", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 4),  "is_premium": False, "future_map_key": "sofi_214"},

    {"section_id": "215", "display_name": "Section 215", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 2),  "is_premium": False, "future_map_key": "sofi_215"},

    {"section_id": "216", "display_name": "Section 216", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 0),  "is_premium": False, "future_map_key": "sofi_216"},

    {"section_id": "217", "display_name": "Section 217", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", -2), "is_premium": False, "future_map_key": "sofi_217"},

    {"section_id": "218", "display_name": "Section 218", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", -4), "is_premium": False, "future_map_key": "sofi_218"},

    {"section_id": "219", "display_name": "Section 219", "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "corner_nw", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", -6), "is_premium": False, "future_map_key": "sofi_219"},

    {"section_id": "220", "display_name": "Section 220", "tier": "CLUB_ENDZONE",
     "level": "club", "zone": "corner_nw", "side": "west",
     "quality_score": _q("CLUB_ENDZONE", 2),  "is_premium": False, "future_map_key": "sofi_220"},

    {"section_id": "221", "display_name": "Section 221", "tier": "CLUB_ENDZONE",
     "level": "club", "zone": "corner_nw", "side": "west",
     "quality_score": _q("CLUB_ENDZONE", 0),  "is_premium": False, "future_map_key": "sofi_221"},

    # ── Club Level — East Endzone / Corner (228–232) ──────────────────────────

    {"section_id": "228", "display_name": "Section 228", "tier": "CLUB_ENDZONE",
     "level": "club", "zone": "endzone_south", "side": "south",
     "quality_score": _q("CLUB_ENDZONE", 0),  "is_premium": False, "future_map_key": "sofi_228"},

    {"section_id": "229", "display_name": "Section 229", "tier": "CLUB_ENDZONE",
     "level": "club", "zone": "endzone_south", "side": "south",
     "quality_score": _q("CLUB_ENDZONE", 2),  "is_premium": False, "future_map_key": "sofi_229"},

    {"section_id": "230", "display_name": "Section 230", "tier": "CLUB_ENDZONE",
     "level": "club", "zone": "endzone_south", "side": "south",
     "quality_score": _q("CLUB_ENDZONE", 2),  "is_premium": False, "future_map_key": "sofi_230"},

    {"section_id": "231", "display_name": "Section 231", "tier": "CLUB_ENDZONE",
     "level": "club", "zone": "endzone_south", "side": "south",
     "quality_score": _q("CLUB_ENDZONE", 0),  "is_premium": False, "future_map_key": "sofi_231"},

    {"section_id": "232", "display_name": "Section 232", "tier": "CLUB_ENDZONE",
     "level": "club", "zone": "corner_se", "side": "east",
     "quality_score": _q("CLUB_ENDZONE", -2), "is_premium": False, "future_map_key": "sofi_232"},

    # ── Upper Bowl — Prime Ring (300–350) ─────────────────────────────────────
    # 301–320: upper sideline prime
    # 321–340: upper corner / transition
    # 341–350: upper endzone

    {"section_id": "301", "display_name": "Section 301", "tier": "UPPER_CORNER",
     "level": "upper_mid", "zone": "corner_sw", "side": "west",
     "quality_score": _q("UPPER_CORNER", 4),  "is_premium": False, "future_map_key": "sofi_301"},

    {"section_id": "302", "display_name": "Section 302", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -4), "is_premium": False, "future_map_key": "sofi_302"},

    {"section_id": "303", "display_name": "Section 303", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -2), "is_premium": False, "future_map_key": "sofi_303"},

    {"section_id": "304", "display_name": "Section 304", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 0),  "is_premium": False, "future_map_key": "sofi_304"},

    {"section_id": "305", "display_name": "Section 305", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 2),  "is_premium": False, "future_map_key": "sofi_305"},

    {"section_id": "306", "display_name": "Section 306", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 4),  "is_premium": False, "future_map_key": "sofi_306"},

    {"section_id": "307", "display_name": "Section 307", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 6),  "is_premium": False, "future_map_key": "sofi_307"},

    {"section_id": "308", "display_name": "Section 308", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 8),  "is_premium": False, "future_map_key": "sofi_308"},

    {"section_id": "309", "display_name": "Section 309", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 10), "is_premium": False, "future_map_key": "sofi_309"},

    {"section_id": "310", "display_name": "Section 310", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 10), "is_premium": False, "future_map_key": "sofi_310"},

    {"section_id": "311", "display_name": "Section 311", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 8),  "is_premium": False, "future_map_key": "sofi_311"},

    {"section_id": "312", "display_name": "Section 312", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 6),  "is_premium": False, "future_map_key": "sofi_312"},

    {"section_id": "313", "display_name": "Section 313", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 4),  "is_premium": False, "future_map_key": "sofi_313"},

    {"section_id": "314", "display_name": "Section 314", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 2),  "is_premium": False, "future_map_key": "sofi_314"},

    {"section_id": "315", "display_name": "Section 315", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 0),  "is_premium": False, "future_map_key": "sofi_315"},

    {"section_id": "316", "display_name": "Section 316", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -2), "is_premium": False, "future_map_key": "sofi_316"},

    {"section_id": "317", "display_name": "Section 317", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -4), "is_premium": False, "future_map_key": "sofi_317"},

    {"section_id": "318", "display_name": "Section 318", "tier": "UPPER_CORNER",
     "level": "upper_mid", "zone": "corner_nw", "side": "west",
     "quality_score": _q("UPPER_CORNER", 4),  "is_premium": False, "future_map_key": "sofi_318"},

    {"section_id": "319", "display_name": "Section 319", "tier": "UPPER_CORNER",
     "level": "upper_mid", "zone": "corner_nw", "side": "west",
     "quality_score": _q("UPPER_CORNER", 2),  "is_premium": False, "future_map_key": "sofi_319"},

    {"section_id": "320", "display_name": "Section 320", "tier": "UPPER_CORNER",
     "level": "upper_mid", "zone": "corner_nw", "side": "north",
     "quality_score": _q("UPPER_CORNER", 0),  "is_premium": False, "future_map_key": "sofi_320"},

    {"section_id": "321", "display_name": "Section 321", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 6), "is_premium": False, "future_map_key": "sofi_321"},

    {"section_id": "322", "display_name": "Section 322", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 4), "is_premium": False, "future_map_key": "sofi_322"},

    {"section_id": "323", "display_name": "Section 323", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 2), "is_premium": False, "future_map_key": "sofi_323"},

    {"section_id": "324", "display_name": "Section 324", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_324"},

    {"section_id": "325", "display_name": "Section 325", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_325"},

    {"section_id": "326", "display_name": "Section 326", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_326"},

    {"section_id": "327", "display_name": "Section 327", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_327"},

    {"section_id": "328", "display_name": "Section 328", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_328"},

    {"section_id": "329", "display_name": "Section 329", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_329"},

    {"section_id": "330", "display_name": "Section 330", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_330"},

    {"section_id": "331", "display_name": "Section 331", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_331"},

    {"section_id": "332", "display_name": "Section 332", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_332"},

    {"section_id": "333", "display_name": "Section 333", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_333"},

    {"section_id": "334", "display_name": "Section 334", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_334"},

    {"section_id": "335", "display_name": "Section 335", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_335"},

    {"section_id": "336", "display_name": "Section 336", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_336"},

    {"section_id": "337", "display_name": "Section 337", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_337"},

    {"section_id": "338", "display_name": "Section 338", "tier": "UPPER_ENDZONE",
     "level": "upper_mid", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_338"},

    {"section_id": "339", "display_name": "Section 339", "tier": "UPPER_CORNER",
     "level": "upper_mid", "zone": "corner_se", "side": "east",
     "quality_score": _q("UPPER_CORNER", 0), "is_premium": False, "future_map_key": "sofi_339"},

    {"section_id": "340", "display_name": "Section 340", "tier": "UPPER_CORNER",
     "level": "upper_mid", "zone": "corner_se", "side": "east",
     "quality_score": _q("UPPER_CORNER", 0), "is_premium": False, "future_map_key": "sofi_340"},

    {"section_id": "341", "display_name": "Section 341", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", -4), "is_premium": False, "future_map_key": "sofi_341"},

    {"section_id": "342", "display_name": "Section 342", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", -2), "is_premium": False, "future_map_key": "sofi_342"},

    {"section_id": "343", "display_name": "Section 343", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 0), "is_premium": False, "future_map_key": "sofi_343"},

    {"section_id": "344", "display_name": "Section 344", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 2), "is_premium": False, "future_map_key": "sofi_344"},

    {"section_id": "345", "display_name": "Section 345", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 4), "is_premium": False, "future_map_key": "sofi_345"},

    {"section_id": "346", "display_name": "Section 346", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 4), "is_premium": False, "future_map_key": "sofi_346"},

    {"section_id": "347", "display_name": "Section 347", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 2), "is_premium": False, "future_map_key": "sofi_347"},

    {"section_id": "348", "display_name": "Section 348", "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 0), "is_premium": False, "future_map_key": "sofi_348"},

    {"section_id": "349", "display_name": "Section 349", "tier": "UPPER_CORNER",
     "level": "upper_mid", "zone": "corner_ne", "side": "east",
     "quality_score": _q("UPPER_CORNER", 2), "is_premium": False, "future_map_key": "sofi_349"},

    {"section_id": "350", "display_name": "Section 350", "tier": "UPPER_CORNER",
     "level": "upper_mid", "zone": "corner_ne", "side": "east",
     "quality_score": _q("UPPER_CORNER", 0), "is_premium": False, "future_map_key": "sofi_350"},

    # ── Upper Top Ring (400s) — expanded/concert capacity ────────────────────
    # 407–421: one side upper top
    # 429–444: other side upper top

    {"section_id": "407", "display_name": "Section 407", "tier": "UPPER_ENDZONE",
     "level": "upper_top", "zone": "corner_sw", "side": "west",
     "quality_score": _q("UPPER_ENDZONE", 4), "is_premium": False, "future_map_key": "sofi_407"},

    {"section_id": "408", "display_name": "Section 408", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -8), "is_premium": False, "future_map_key": "sofi_408"},

    {"section_id": "409", "display_name": "Section 409", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -6), "is_premium": False, "future_map_key": "sofi_409"},

    {"section_id": "410", "display_name": "Section 410", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -4), "is_premium": False, "future_map_key": "sofi_410"},

    {"section_id": "411", "display_name": "Section 411", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -2), "is_premium": False, "future_map_key": "sofi_411"},

    {"section_id": "412", "display_name": "Section 412", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 0), "is_premium": False, "future_map_key": "sofi_412"},

    {"section_id": "413", "display_name": "Section 413", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 2), "is_premium": False, "future_map_key": "sofi_413"},

    {"section_id": "414", "display_name": "Section 414", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 2), "is_premium": False, "future_map_key": "sofi_414"},

    {"section_id": "416", "display_name": "Section 416", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 0), "is_premium": False, "future_map_key": "sofi_416"},

    {"section_id": "417", "display_name": "Section 417", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -2), "is_premium": False, "future_map_key": "sofi_417"},

    {"section_id": "418", "display_name": "Section 418", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", -4), "is_premium": False, "future_map_key": "sofi_418"},

    {"section_id": "419", "display_name": "Section 419", "tier": "UPPER_CORNER",
     "level": "upper_top", "zone": "corner_nw", "side": "west",
     "quality_score": _q("UPPER_CORNER", -2), "is_premium": False, "future_map_key": "sofi_419"},

    {"section_id": "420", "display_name": "Section 420", "tier": "UPPER_CORNER",
     "level": "upper_top", "zone": "corner_nw", "side": "west",
     "quality_score": _q("UPPER_CORNER", -4), "is_premium": False, "future_map_key": "sofi_420"},

    {"section_id": "421", "display_name": "Section 421", "tier": "UPPER_ENDZONE",
     "level": "upper_top", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 2), "is_premium": False, "future_map_key": "sofi_421"},

    {"section_id": "429", "display_name": "Section 429", "tier": "UPPER_ENDZONE",
     "level": "upper_top", "zone": "endzone_south", "side": "south",
     "quality_score": _q("UPPER_ENDZONE", 2), "is_premium": False, "future_map_key": "sofi_429"},

    {"section_id": "430", "display_name": "Section 430", "tier": "UPPER_CORNER",
     "level": "upper_top", "zone": "corner_se", "side": "east",
     "quality_score": _q("UPPER_CORNER", -4), "is_premium": False, "future_map_key": "sofi_430"},

    {"section_id": "431", "display_name": "Section 431", "tier": "UPPER_CORNER",
     "level": "upper_top", "zone": "corner_se", "side": "east",
     "quality_score": _q("UPPER_CORNER", -2), "is_premium": False, "future_map_key": "sofi_431"},

    {"section_id": "432", "display_name": "Section 432", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", -4), "is_premium": False, "future_map_key": "sofi_432"},

    {"section_id": "433", "display_name": "Section 433", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", -2), "is_premium": False, "future_map_key": "sofi_433"},

    {"section_id": "434", "display_name": "Section 434", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 0), "is_premium": False, "future_map_key": "sofi_434"},

    {"section_id": "435", "display_name": "Section 435", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 2), "is_premium": False, "future_map_key": "sofi_435"},

    {"section_id": "436", "display_name": "Section 436", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 2), "is_premium": False, "future_map_key": "sofi_436"},

    {"section_id": "437", "display_name": "Section 437", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", 0), "is_premium": False, "future_map_key": "sofi_437"},

    {"section_id": "438", "display_name": "Section 438", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", -2), "is_premium": False, "future_map_key": "sofi_438"},

    {"section_id": "439", "display_name": "Section 439", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", -4), "is_premium": False, "future_map_key": "sofi_439"},

    {"section_id": "440", "display_name": "Section 440", "tier": "UPPER_PRIME",
     "level": "upper_top", "zone": "sideline_east", "side": "east",
     "quality_score": _q("UPPER_PRIME", -6), "is_premium": False, "future_map_key": "sofi_440"},

    {"section_id": "441", "display_name": "Section 441", "tier": "UPPER_CORNER",
     "level": "upper_top", "zone": "corner_ne", "side": "east",
     "quality_score": _q("UPPER_CORNER", -2), "is_premium": False, "future_map_key": "sofi_441"},

    {"section_id": "442", "display_name": "Section 442", "tier": "UPPER_CORNER",
     "level": "upper_top", "zone": "corner_ne", "side": "east",
     "quality_score": _q("UPPER_CORNER", -2), "is_premium": False, "future_map_key": "sofi_442"},

    {"section_id": "443", "display_name": "Section 443", "tier": "UPPER_ENDZONE",
     "level": "upper_top", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 2), "is_premium": False, "future_map_key": "sofi_443"},

    {"section_id": "444", "display_name": "Section 444", "tier": "UPPER_ENDZONE",
     "level": "upper_top", "zone": "endzone_north", "side": "north",
     "quality_score": _q("UPPER_ENDZONE", 0), "is_premium": False, "future_map_key": "sofi_444"},

    # ── Suite / Premium Zones ─────────────────────────────────────────────────
    # M-sections: premium club/suite areas observed in VividSeats and Gametime
    # C-sections: premium box variants

    {"section_id": "M4",  "display_name": "M4 Club",  "tier": "SUITE",
     "level": "suite", "zone": "sideline_west", "side": "west",
     "quality_score": _q("SUITE", 0), "is_premium": True, "future_map_key": "sofi_M4"},

    {"section_id": "M11", "display_name": "M11 Club", "tier": "SUITE",
     "level": "suite", "zone": "sideline_west", "side": "west",
     "quality_score": _q("SUITE", 4), "is_premium": True, "future_map_key": "sofi_M11"},

    {"section_id": "M32", "display_name": "M32 Club", "tier": "SUITE",
     "level": "suite", "zone": "sideline_west", "side": "west",
     "quality_score": _q("SUITE", 4), "is_premium": True, "future_map_key": "sofi_M32"},

    {"section_id": "M33", "display_name": "M33 Club", "tier": "SUITE",
     "level": "suite", "zone": "sideline_west", "side": "west",
     "quality_score": _q("SUITE", 2), "is_premium": True, "future_map_key": "sofi_M33"},

    {"section_id": "M43", "display_name": "M43 Club", "tier": "SUITE",
     "level": "suite", "zone": "endzone_south", "side": "south",
     "quality_score": _q("SUITE", -4), "is_premium": True, "future_map_key": "sofi_M43"},

    {"section_id": "M45", "display_name": "M45 Club", "tier": "SUITE",
     "level": "suite", "zone": "endzone_south", "side": "south",
     "quality_score": _q("SUITE", -4), "is_premium": True, "future_map_key": "sofi_M45"},

    {"section_id": "C7",  "display_name": "C7 Box",  "tier": "SUITE",
     "level": "suite", "zone": "sideline_west", "side": "west",
     "quality_score": _q("SUITE", 6), "is_premium": True, "future_map_key": "sofi_C7"},

    {"section_id": "C11", "display_name": "C11 Box", "tier": "SUITE",
     "level": "suite", "zone": "sideline_west", "side": "west",
     "quality_score": _q("SUITE", 8), "is_premium": True, "future_map_key": "sofi_C11"},

    {"section_id": "C23", "display_name": "C23 Box", "tier": "SUITE",
     "level": "suite", "zone": "sideline_west", "side": "west",
     "quality_score": _q("SUITE", 4), "is_premium": True, "future_map_key": "sofi_C23"},

    {"section_id": "FB104", "display_name": "Field Box 104", "tier": "FIELD_CLUB",
     "level": "field_club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("FIELD_CLUB", 0), "is_premium": True, "future_map_key": "sofi_FB104"},

    {"section_id": "CONCOURSE_SUITE_23", "display_name": "Concourse Suite 23", "tier": "SUITE",
     "level": "suite", "zone": "suite", "side": "center",
     "quality_score": _q("SUITE", -6), "is_premium": True, "future_map_key": "sofi_CONCOURSE_SUITE_23"},

    {"section_id": "LEXUS_DUGOUT_CLUB", "display_name": "Lexus Dugout Club", "tier": "FIELD_CLUB",
     "level": "field_club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("FIELD_CLUB", 8), "is_premium": True, "future_map_key": "sofi_LEXUS_DUGOUT_CLUB"},

    # ── Concert Floor (stage configurations) ──────────────────────────────────

    {"section_id": "FLOOR",   "display_name": "Floor",     "tier": "FLOOR",
     "level": "floor", "zone": "floor", "side": "center",
     "quality_score": _q("FLOOR", -2), "is_premium": False, "future_map_key": "sofi_FLOOR"},

    {"section_id": "FLOOR_A", "display_name": "Floor A",   "tier": "FLOOR",
     "level": "floor", "zone": "floor", "side": "center",
     "quality_score": _q("FLOOR", 6),  "is_premium": False, "future_map_key": "sofi_FLOOR_A"},

    {"section_id": "FLOOR_B", "display_name": "Floor B",   "tier": "FLOOR",
     "level": "floor", "zone": "floor", "side": "center",
     "quality_score": _q("FLOOR", 4),  "is_premium": False, "future_map_key": "sofi_FLOOR_B"},

    {"section_id": "FLOOR_C", "display_name": "Floor C",   "tier": "FLOOR",
     "level": "floor", "zone": "floor", "side": "center",
     "quality_score": _q("FLOOR", 2),  "is_premium": False, "future_map_key": "sofi_FLOOR_C"},

    # ── Broad area labels (catch-all) ─────────────────────────────────────────

    {"section_id": "CLUB",  "display_name": "Club Level",  "tier": "CLUB_SIDELINE",
     "level": "club", "zone": "sideline_west", "side": "west",
     "quality_score": _q("CLUB_SIDELINE", 0), "is_premium": True, "future_map_key": "sofi_CLUB"},

    {"section_id": "A",     "display_name": "Area A",      "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 0), "is_premium": False, "future_map_key": "sofi_A"},

    {"section_id": "C",     "display_name": "Area C",      "tier": "UPPER_PRIME",
     "level": "upper_mid", "zone": "sideline_west", "side": "west",
     "quality_score": _q("UPPER_PRIME", 0), "is_premium": False, "future_map_key": "sofi_C"},
]


# ── Alias definitions ─────────────────────────────────────────────────────────
# Each alias maps (marketplace_id, raw_section_string) → section_id.
# marketplace_id = None means the alias applies across all marketplaces.
# event_type = None means the alias applies regardless of event type.
#
# Addition protocol for new marketplaces:
#   1. Add alias rows below (or insert directly via bootstrap script)
#   2. No other files need to change

class AliasDef(TypedDict):
    section_id: str       # canonical section_id to map to
    marketplace_id: int | None
    alias: str            # raw string from marketplace
    event_type: str | None


ALIASES: list[AliasDef] = []

def _a(section_id: str, mp: int | None, alias: str, event_type: str | None = None) -> None:
    ALIASES.append({"section_id": section_id, "marketplace_id": mp, "alias": alias, "event_type": event_type})


# ── Universal aliases (no marketplace constraint) ────────────────────────────
# Plain integers and "Section NNN" / "Sec NNN" format — these are universal
for _s in SECTIONS:
    sid = _s["section_id"]
    # If section_id is a plain integer string
    if sid.isdigit():
        _a(sid, None, sid)                          # "232"
        _a(sid, None, f"Section {sid}")             # "Section 232"
        _a(sid, None, f"Sec {sid}")                 # "Sec 232"
        _a(sid, None, f"SEC {sid}")
        _a(sid, None, f"SECTION {sid}")

# ── VividSeats (marketplace_id = 2) ─────────────────────────────────────────
# VividSeats typically sends bare integers or "Section NNN" format.
# Special VividSeats labels observed in production:

_a("FLOOR",              2, "FLOOR")
_a("FLOOR_A",            2, "FLOOR A")
_a("FLOOR_B",            2, "FLOOR B")
_a("FLOOR_C",            2, "FLOOR C")
_a("CLUB",               2, "CLUB")
_a("CONCOURSE_SUITE_23", 2, "CONCOURSE SUITE 23")
_a("FB104",              2, "FB104")
_a("LEXUS_DUGOUT_CLUB",  2, "LEXUS DUGOUT CLUB")
_a("M4",                 2, "M4")
_a("M11",                2, "M11")
_a("M32",                2, "M32")
_a("M33",                2, "M33")
_a("M43",                2, "M43")
_a("M45",                2, "M45")
_a("C7",                 2, "C7")
_a("C11",                2, "C11")
_a("C23",                2, "C23")
_a("A",                  2, "A")
_a("C",                  2, "C")

# ── Gametime (marketplace_id = 5) ────────────────────────────────────────────
# Gametime uses descriptive level+position+number format for concerts.
# Level-prefix aliases map to the same canonical section numbers.

# FIELD CLUB INFIELD NNN → NNN (concert, stage-facing)
for _n in [107, 108, 109, 110, 112, 113, 115, 117, 119, 121, 122, 123, 124]:
    _a(str(_n), 5, f"FIELD CLUB INFIELD {_n}", "concert")

# PREMIUM FIELD CLUB NNN → NNN
for _n in [107, 108, 109, 110, 113, 115, 117, 119, 122, 123, 124]:
    _a(str(_n), 5, f"PREMIUM FIELD CLUB {_n}", "concert")

# LOWER BOX NNN → NNN
for _n in [105, 106, 107, 108, 109, 110, 112, 113, 118, 119, 121, 122, 123, 124, 125, 126]:
    _a(str(_n), 5, f"LOWER BOX {_n}",         "concert")
    _a(str(_n), 5, f"LOWER BOX  {_n}",        "concert")  # double-space variant observed
    _a(str(_n), 5, f"PREMIUM LOWER BOX {_n}", "concert")

# LOWER OUTFIELD NNN → NNN (away from stage)
for _n in [101, 102, 103, 104, 127, 128, 129, 130]:
    _a(str(_n), 5, f"LOWER OUTFIELD {_n}", "concert")

# LOWER LEFT FIELD NNN → NNN
for _n in [131, 132, 133, 134, 135]:
    _a(str(_n), 5, f"LOWER LEFT FIELD {_n}", "concert")

# LEFT FIELD BLEACHER NNN → NNN
for _n in [136, 137, 138, 139, 140, 141, 142]:
    _a(str(_n), 5, f"LEFT FIELD BLEACHER {_n}", "concert")

# CENTER FIELD BLEACHER NNN → NNN
for _n in [143, 144]:
    _a(str(_n), 5, f"CENTER FIELD BLEACHER {_n}", "concert")

# ARCADE NNN → ARCADE_NNN
for _n in [145, 146, 147, 148, 149, 150, 151]:
    _a(f"ARCADE_{_n}", 5, f"ARCADE {_n}", "concert")

# CLUB INFIELD NNN → NNN
for _n in [207, 208, 209, 210, 211, 212, 215, 216, 217, 219, 220, 221, 222, 223, 224, 225]:
    _a(str(_n), 5, f"CLUB INFIELD {_n}", "concert")

# CLUB OUTFIELD NNN → NNN
for _n in [202, 203, 204, 205, 226, 227, 228, 229, 230, 231]:
    _a(str(_n), 5, f"CLUB OUTFIELD {_n}", "concert")

# CLUB LEFT FIELD NNN → NNN
for _n in [232]:
    _a(str(_n), 5, f"CLUB LEFT FIELD {_n}", "concert")

# VIEW BOX NNN and VIEW BOX VB NNN → NNN
for _n in [304, 305, 307, 308, 310, 311, 312, 313, 314, 315, 317, 318, 319, 320,
           321, 323, 324, 325, 326, 328, 330, 331, 335]:
    _a(str(_n), 5, f"VIEW BOX {_n}",    "concert")
_a("311", 5, "VIEW BOX VB311", "concert")

# VIEW INFIELD NNN → NNN
for _n in [308, 310, 311, 312, 313, 314, 315, 317, 318, 319, 320, 321, 323, 324]:
    _a(str(_n), 5, f"VIEW INFIELD {_n}", "concert")

# VIEW OUTFIELD NNN → NNN
for _n in [325, 326, 327, 328, 330, 331]:
    _a(str(_n), 5, f"VIEW OUTFIELD {_n}", "concert")

# VIEW LEFT FIELD NNN → NNN
for _n in [332, 333, 334, 335, 336]:
    _a(str(_n), 5, f"VIEW LEFT FIELD {_n}", "concert")

# VIEW RIGHT FIELD NNN → NNN
for _n in [302, 304, 305, 307]:
    _a(str(_n), 5, f"VIEW RIGHT FIELD {_n}", "concert")

# Gametime special labels
_a("FLOOR_A",            5, "FLOOR A")
_a("FLOOR_C",            5, "FLOOR C")
_a("CLUB",               5, "CLUB")
_a("CONCOURSE_SUITE_23", 5, "CONCOURSE SUITE 23")
_a("M32",                5, "M32")
_a("M33",                5, "M33")
_a("M45",                5, "M45")
_a("C7",                 5, "C7")
_a("C11",                5, "C11")

# ── StubHub (marketplace_id = 3, placeholder) ────────────────────────────────
# StubHub uses "Section NNN" format — covered by the universal aliases above.
# Add StubHub-specific aliases here if/when data is ingested.

# ── SeatGeek (marketplace_id = 4, placeholder) ───────────────────────────────
# SeatGeek uses "Section NNN" format — covered by universal aliases above.

# ── Ticketmaster (marketplace_id = 6, placeholder) ───────────────────────────
# Add when Ticketmaster data is available.

# ── TickPick (marketplace_id = 7, placeholder) ───────────────────────────────
# Add when TickPick data is available.


# ── Build lookup table ────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    return s.strip().lower()

# section_id → SectionDef
SECTION_BY_ID: dict[str, SectionDef] = {s["section_id"]: s for s in SECTIONS}

# (marketplace_id_or_None, normalized_alias) → section_id
ALIAS_LOOKUP: dict[tuple[int | None, str], str] = {}
for _a_def in ALIASES:
    ALIAS_LOOKUP[(_a_def["marketplace_id"], _norm(_a_def["alias"]))] = _a_def["section_id"]
