"""
Shared listing normalisation helpers.

is_parking_listing()
    Marketplace-agnostic parking filter.  Evaluated at the _process_result()
    ingestion choke-point in app/scheduler.py so every source (Railway
    collectors, Mac-host manual-ingest scripts, future marketplaces) is
    covered by a single implementation.

Design notes
------------
* All patterns are compiled once at import time (module-level).
* The function accepts **kwargs so callers can pass extra fields without
  breaking the signature as the schema evolves.
* False-positive guard: section="G" / row="GA" is General Admission floor
  seating, NOT parking.  "GA" is intentionally absent from the row exact-
  match set; only the PRK* row prefix is matched row-only.
* "VP" in the exact-match row set = Valet Pass abbreviation (TickPick).
  Confirmed via full-catalog audit: 12/12 VP-row listings across 3951 active
  TickPick records were parking passes, none were real seat rows.
* "GA" as a row value is only treated as parking when the section already
  matches a parking keyword (handled automatically because the section check
  fires first and returns True before the row check is ever reached).
"""

from __future__ import annotations

import re

# ── Tier 1: section keyword patterns ─────────────────────────────────────────
# Any match on the section field → parking, regardless of row.

_SEC_PARKING_RE = re.compile(r"\bparking\b", re.IGNORECASE)
_SEC_GARAGE_RE  = re.compile(r"\bgarage\b",  re.IGNORECASE)
_SEC_TAILGATE_RE = re.compile(r"\btailgate\b", re.IGNORECASE)
_SEC_PASS_ONLY_RE = re.compile(r"\bpass\s+only\b", re.IGNORECASE)
_SEC_PARKING_ONLY_RE = re.compile(r"\bparking\s+only\b", re.IGNORECASE)

# Any word "lot" in the section — covers "LOT C", "LOT G", "SEC LOT F",
# "BROWN ZONE LOT", "SOUTH PARK LOT", "THE FORUM LOT", etc.
_SEC_LOT_RE = re.compile(r"\blot\b", re.IGNORECASE)

# "LOT" concatenated with identifier, no space: "LOTC", "LOTA", "LOT1", etc.
# TickPick sometimes omits the space between LOT and the lot letter/number.
_SEC_LOT_CONCAT_RE = re.compile(r"\bLOT[A-Z0-9]+\b", re.IGNORECASE)

# Valet parking passes
_SEC_VALET_RE = re.compile(r"\bvalet\b", re.IGNORECASE)

# Colour + zone/lot combos — covers "GREEN ZONE", "BROWN ZONE", "ORANGE ZONE",
# "BLUE LOT", "PINK LOT", "GOLD LOT", "FLOWER ST LOT", etc.
_SEC_COLOR_ZONE_RE = re.compile(
    r"\b(?:blue|green|orange|brown|red|yellow|gold|purple|white|black|"
    r"silver|gray|grey|pink|teal|maroon|crimson|flower|retail)\s+(?:zone|lot)\b",
    re.IGNORECASE,
)

# Bare colour name that IS the entire section field.
# "BROWN" alone = Brown Zone parking lot at SoFi/Crypto.com area venues.
# Seating sections never use a bare colour word as their sole identifier
# (they say "Blue Level", "Green Club", "Gold Circle", etc.).
_SEC_BARE_COLOR_RE = re.compile(
    r"^\s*(?:blue|green|orange|brown|red|yellow|gold|purple|white|black|"
    r"silver|gray|grey|pink|teal|maroon|crimson)\s*$",
    re.IGNORECASE,
)

# Known TickPick parking abbreviations that contain no generic parking keyword.
#   PREFRD = Preferred Parking
_SEC_KNOWN_ABBREV_RE = re.compile(
    r"^\s*PREFRD\s*$",
    re.IGNORECASE,
)

# Parking Structure shorthand: PS-2, PS-3, etc.
_SEC_PS_RE = re.compile(r"\bPS-\d+\b", re.IGNORECASE)

# Building name sections — "FREEMAN MEDICAL BUILDING", "PARKING STRUCTURE BUILDING B"
# No legitimate seating section uses "BUILDING" as part of its name.
# This catches TickPick parking passes listed under nearby building addresses.
_SEC_BUILDING_RE = re.compile(r"\bBUILDING\b", re.IGNORECASE)

# Entrance sections — "PRAIRIE ENTRANCE", "SOUTH ENTRANCE", "PARKING STRUCTURE ENTRANCE B"
# No legitimate seating section uses "ENTRANCE" as part of its name.
# This catches TickPick parking passes listed under venue entrance/gate addresses.
_SEC_ENTRANCE_RE = re.compile(r"\bENTRANCE\b", re.IGNORECASE)

# Nearby property sections — "HOPE & FLOWER APARTMENTS", "HOTEL FIG", etc.
# TickPick lists parking/proximity passes under the names of hotels and apartment
# buildings adjacent to the venue.  No seating section is ever named after a hotel
# or apartment complex.
_SEC_APARTMENTS_RE = re.compile(r"\bAPARTMENTS?\b", re.IGNORECASE)
_SEC_HOTEL_RE      = re.compile(r"\bHOTEL\b",       re.IGNORECASE)

# School / church / named-landmark sections used by TickPick for nearby parking lots.
# "WILLIAM KELSO ELEMENTARY SCHOOL" is a Hollywood Bowl adjacent parking lot sold as
# a parking pass on TickPick.  No seating section at any venue is ever named after a
# school, church, or religious institution.
# Covers: "KELSO ELEMENTARY SCHOOL", "WILSHIRE TEMPLE", "FIRST METHODIST CHURCH", etc.
_SEC_SCHOOL_RE = re.compile(
    r"\b(?:school|elementary|middle\s+school|high\s+school|church|temple|synagogue|mosque)\b",
    re.IGNORECASE,
)

# Shuttle / transportation pass sections.
# "HOLLYWOOD BOWL SHUTTLE", "SHUTTLE BUS", "EXPRESS SHUTTLE", "COACH BUS", etc.
# No seating section is ever named after a shuttle or bus service.
# Using \bSHUTTLE\b catches compound names; \bCOACH\s+BUS\b is more precise to
# avoid false-positives on "Coach" (a section name abbreviation at some venues).
_SEC_SHUTTLE_RE = re.compile(r"\bSHUTTLE\b", re.IGNORECASE)
_SEC_COACH_BUS_RE = re.compile(r"\bCOACH\s+BUS\b", re.IGNORECASE)
_SEC_TRANSPORT_PASS_RE = re.compile(
    r"\bTRANSPORT(?:ATION)?\s+PASS\b", re.IGNORECASE
)

# Distance patterns that appear in TickPick parking-lot section names:
#   "0.47 MI AWAY", "0.6 MI FROM VENUE", "6 MINUTE WALK", "14 MIN WALK"
_SEC_DISTANCE_RE = re.compile(
    # Handles both "0.47 MI AWAY" and "1.2mi away" (no space before unit)
    r"\b\d+(?:\.\d+)?\s*(?:mi(?:le)?s?\s+(?:away|from)|min(?:ute)?s?\s+walk)\b",
    re.IGNORECASE,
)

# Street address sections: "323 N PRAIRIE AVE.", "1415 S. HILL ST.",
# "725 GRAND AVE", "200 W PICO BLVD", etc.
# Pattern: starts with house number → optional cardinal → street name →
#          ends with a recognised street-type abbreviation.
# Guards: seating sections are bare numbers ("101"), letters ("A", "Floor"),
#         or shorthand codes ("4SE 1A") — none end with a street-type word.
_SEC_STREET_ADDR_RE = re.compile(
    r"^\d+\s+(?:[NSEWnsew]\.?\s+)?"          # house number + optional N/S/E/W
    r"[A-Za-z]"                               # street name starts with a letter
    r".*\b(?:st|ave|blvd|dr|rd|ln|way|pkwy|hwy|ct|pl)\b\.?\s*$",
    re.IGNORECASE,
)

# All section patterns as a tuple for a single loop
_SECTION_PATTERNS: tuple[re.Pattern, ...] = (
    _SEC_PARKING_RE,
    _SEC_GARAGE_RE,
    _SEC_TAILGATE_RE,
    _SEC_PASS_ONLY_RE,
    _SEC_PARKING_ONLY_RE,
    _SEC_LOT_RE,
    _SEC_LOT_CONCAT_RE,
    _SEC_VALET_RE,
    _SEC_COLOR_ZONE_RE,
    _SEC_BARE_COLOR_RE,
    _SEC_KNOWN_ABBREV_RE,
    _SEC_PS_RE,
    _SEC_DISTANCE_RE,
    _SEC_STREET_ADDR_RE,
    _SEC_BUILDING_RE,
    _SEC_ENTRANCE_RE,
    _SEC_APARTMENTS_RE,
    _SEC_HOTEL_RE,
    _SEC_SCHOOL_RE,
    _SEC_SHUTTLE_RE,
    _SEC_COACH_BUS_RE,
    _SEC_TRANSPORT_PASS_RE,
)

# ── Tier 2: row keyword search ────────────────────────────────────────────────
# Catches rows that CONTAIN "parking" but are not exact matches:
#   "PARKING WITHIN 1 MILE", "ONSITE PARKING", "PARKING WI" (truncated), etc.
_ROW_PARKING_WORD_RE = re.compile(r"\bparking\b", re.IGNORECASE)

# Catches rows containing "shuttle" — "SHUTTLE PASS", "SHUTTLE BUS PASS", etc.
_ROW_SHUTTLE_WORD_RE = re.compile(r"\bshuttle\b", re.IGNORECASE)

# ── Tier 2b: row exact-match set ─────────────────────────────────────────────
# Matches when the *entire* normalised row value is one of these tokens.
# "ga" is deliberately excluded — see module docstring.
_PARKING_ROW_EXACT: frozenset[str] = frozenset(
    {
        "parking",
        "park",
        "prk",
        "prk1",
        "prk2",
        "prk3",
        "lot",
        "valet",
        "vp",   # Valet Pass abbreviation used by TickPick (confirmed via audit: 12/12 VP-row
                # listings across 3951 TickPick records are parking, never a real row letter)
        "shuttle",
        "shuttle pass",
        "bus pass",
        "transport pass",
        "transportation pass",
    }
)

# ── Tier 3: row prefix pattern ────────────────────────────────────────────────
# Rows beginning with "PRK" (e.g. "PRK1", "PRK-A", "PRKG") are unambiguously
# parking regardless of section content.
_ROW_PRK_PREFIX_RE = re.compile(r"^PRK", re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────

def is_parking_listing(
    section: str | None,
    row: str | None,
    **_kwargs,
) -> bool:
    """Return True if this listing is a parking pass rather than a concert seat.

    Parameters
    ----------
    section:
        The listing's section field (may be None or empty).
    row:
        The listing's row field (may be None or empty).
    **_kwargs:
        Future fields (notes, listing_url, …) accepted but ignored so callers
        can pass the full listing dict without breaking the signature.

    Examples
    --------
    >>> is_parking_listing("PARKING PASS", None)
    True
    >>> is_parking_listing("GREEN ZONE", "GA")
    True
    >>> is_parking_listing("CIRCA GARAGE", "GA")
    True
    >>> is_parking_listing("SEC LOT F", "GA")
    True
    >>> is_parking_listing("G", "PRK")
    True
    >>> is_parking_listing("A", "PARKING")
    True
    >>> is_parking_listing("101", "12")
    False
    >>> is_parking_listing("Pit", "GA")
    False
    >>> is_parking_listing("G", "GA")     # General Admission floor, NOT parking
    False
    >>> is_parking_listing("Floor", "GA")  # GA floor ticket, NOT parking
    False
    >>> is_parking_listing("JJ", "ONSITE PARKING")   # row word match
    True
    >>> is_parking_listing("323 N PRAIRIE AVE.", "GA")  # street address section
    True
    >>> is_parking_listing("323 N PRAIRIE AVE.", "PARKING WITHIN 1 MILE")
    True
    """
    sec = (section or "").strip()
    rw  = (row or "").strip()

    # ── Tier 1: section keyword wins unconditionally ──────────────────────────
    for pattern in _SECTION_PATTERNS:
        if pattern.search(sec):
            return True

    # ── Tier 2: row contains "parking" or "shuttle" ──────────────────────────
    # Catches "PARKING WITHIN 1 MILE", "ONSITE PARKING", "SHUTTLE PASS", etc.
    if _ROW_PARKING_WORD_RE.search(rw):
        return True
    if _ROW_SHUTTLE_WORD_RE.search(rw):
        return True

    # ── Tier 2b: row exact-match (unambiguous non-ticket values) ─────────────
    if rw.lower() in _PARKING_ROW_EXACT:
        return True

    # ── Tier 3: row PRK* prefix ───────────────────────────────────────────────
    if _ROW_PRK_PREFIX_RE.match(rw):
        return True

    return False
