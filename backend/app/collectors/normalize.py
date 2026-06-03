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

# Valet parking passes
_SEC_VALET_RE = re.compile(r"\bvalet\b", re.IGNORECASE)

# Colour + zone/lot combos — covers "GREEN ZONE", "BROWN ZONE", "ORANGE ZONE",
# "BLUE LOT", "PINK LOT", "GOLD LOT", "FLOWER ST LOT", etc.
_SEC_COLOR_ZONE_RE = re.compile(
    r"\b(?:blue|green|orange|brown|red|yellow|gold|purple|white|black|"
    r"silver|gray|grey|pink|teal|maroon|crimson|flower|retail)\s+(?:zone|lot)\b",
    re.IGNORECASE,
)

# Parking Structure shorthand: PS-2, PS-3, etc.
_SEC_PS_RE = re.compile(r"\bPS-\d+\b", re.IGNORECASE)

# Distance patterns that appear in TickPick parking-lot section names:
#   "0.47 MI AWAY", "0.6 MI FROM VENUE", "6 MINUTE WALK", "14 MIN WALK"
_SEC_DISTANCE_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s+(?:mi(?:le)?s?\s+(?:away|from)|min(?:ute)?s?\s+walk)\b",
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
    _SEC_VALET_RE,
    _SEC_COLOR_ZONE_RE,
    _SEC_PS_RE,
    _SEC_DISTANCE_RE,
)

# ── Tier 2: row exact-match set ───────────────────────────────────────────────
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
    """
    sec = (section or "").strip()
    rw  = (row or "").strip()

    # ── Tier 1: section keyword wins unconditionally ──────────────────────────
    for pattern in _SECTION_PATTERNS:
        if pattern.search(sec):
            return True

    # ── Tier 2: row exact-match (unambiguous parking-only values) ─────────────
    if rw.lower() in _PARKING_ROW_EXACT:
        return True

    # ── Tier 3: row PRK* prefix ───────────────────────────────────────────────
    if _ROW_PRK_PREFIX_RE.match(rw):
        return True

    return False
