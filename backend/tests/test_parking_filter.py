"""
Phase 1E-C — Regression tests for is_parking_listing().

Coverage:
  1. True-positive cases (real parking section names from production DB)
  2. Row-only signals (row=PRK*, PARKING, PARK without section keyword)
  3. False-positive guards (real concert seat sections that must NOT be filtered)
  4. Edge cases (None inputs, mixed case, whitespace)

All section/row values were sourced directly from the 2026-06-03 production
parking audit.  Do not change expected results without cross-checking against
that audit output.
"""

import pytest
from app.collectors.normalize import is_parking_listing


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def parking(section, row=None):
    """Assert is_parking_listing returns True."""
    assert is_parking_listing(section, row), (
        f"Expected parking=True for section={section!r} row={row!r}"
    )


def not_parking(section, row=None):
    """Assert is_parking_listing returns False."""
    assert not is_parking_listing(section, row), (
        f"Expected parking=False for section={section!r} row={row!r}"
    )


# ────────────────────────────────────────────────────────────────────────────
# 1. Section keyword matches (Tier 1)
# ────────────────────────────────────────────────────────────────────────────

class TestSectionKeywords:

    def test_parking_word_exact(self):
        parking("PARKING PASS")

    def test_parking_word_in_phrase(self):
        parking("PREFERRED PARKING")
        parking("PRAIRIE - PARKING LOT")
        parking("FORUM PARKING")
        parking("VIP WEST GARAGE")

    def test_garage_word(self):
        parking("CIRCA GARAGE")
        parking("7TH & FIG GARAGE")
        parking("PS-2 GARAGE")
        parking("725 S. GRAND AVE. GARAGE")
        parking("865 S. FIGUEROA ST. GARAGE 0.3 MI FROM VENUE")

    def test_tailgate(self):
        parking("TAILGATE ZONE")
        parking("TAILGATE PASS")

    def test_pass_only(self):
        parking("PASS ONLY")
        parking("VIP PASS ONLY")

    def test_parking_only(self):
        parking("MOTORCYCLE PARKING ONLY")
        parking("PARKING ONLY - LOT B")

    def test_lot_word(self):
        # Any occurrence of the word "lot"
        parking("LOT C")
        parking("LOT G")
        parking("LOT 1")
        parking("BROWN ZONE LOT")
        parking("SEC LOT F")
        parking("THE FORUM LOT")
        parking("SOUTH PARK LOT")
        parking("601 S. PRAIRIE AVE. LOT")
        parking("OUTDOOR LOT")
        parking("PINK LOT")

    def test_valet(self):
        parking("VALET")
        parking("1023 S. GRAND AVE. LOT - VALET")
        parking("KAREEM SOUTH ENTRANCE - KIA FORUM LOT")

    def test_color_zone(self):
        parking("GREEN ZONE")
        parking("BROWN ZONE")
        parking("ORANGE ZONE")
        parking("BLUE ZONE")
        parking("PINK ZONE")
        parking("BROWN ZONE LOT")
        parking("HYUNDAI ORANGE ZONE VARUS DR ENTRY")
        parking("BLUE LOT")
        parking("FLOWER ST LOT")

    def test_parking_structure_ps(self):
        parking("PS-2")
        parking("PS-3")
        parking("PS-4 GARAGE")
        parking("PS-2 GARAGE")

    def test_distance_pattern(self):
        parking("0.47 MI AWAY")
        parking("1017 S. HILL ST. LOT - 0.47 MI AWAY")
        parking("865 S. FIGUEROA ST. GARAGE 0.3 MI FROM VENUE")
        parking("KELSO ELEMENTARY SCHOOL LOT - 0.18 MI AWAY")
        parking("WILLIAM KELSO ELEMENTARY SCHOOL LOT - 6 MINUTE WALK")
        parking("14 MIN WALK")

    def test_case_insensitive(self):
        parking("parking pass")
        parking("Preferred Parking")
        parking("Circa Garage")
        parking("Green Zone")
        parking("Blue Lot")


# ────────────────────────────────────────────────────────────────────────────
# 2. Row-only signals (Tier 2 & 3)
# ────────────────────────────────────────────────────────────────────────────

class TestRowSignals:

    def test_row_parking_exact(self):
        # Section has no parking keyword — row carries the signal
        parking("A",       "PARKING")     # single-letter section + PARKING row
        parking("G",       "PARKING")
        parking("301 N PRAIRIE AVE", "PARKING")
        parking("BROWN ZONE",        "PARKING")  # color zone + row (belt-and-suspenders)
        parking("GREEN ZONE",        "PARKING")

    def test_row_park_exact(self):
        parking("KELSO ELEMENTARY",   "PARK")
        parking("G,GG,FF",            "PARK")
        parking("323 N PRAIRIE AVE",  "PARK")

    def test_row_prk_prefix(self):
        # "G" section, row="PRK" — production case (n=16)
        parking("G",   "PRK")
        parking("F",   "PRK")
        parking("LOT", "PRK1")
        parking("",    "PRK-A")
        parking(None,  "PRKG")

    def test_row_lot_exact(self):
        parking("INDOOR GARAGE", "lot")    # case-insensitive exact

    def test_row_valet_exact(self):
        parking("VALET AREA",   "valet")

    def test_row_case_insensitive(self):
        parking("A", "parking")
        parking("A", "Park")
        parking("G", "prk")
        parking("G", "Prk1")


# ────────────────────────────────────────────────────────────────────────────
# 3. False-positive guards — MUST return False
# ────────────────────────────────────────────────────────────────────────────

class TestFalsePositiveGuards:

    def test_numeric_section_and_row(self):
        """Normal numbered seating sections."""
        not_parking("101", "11")
        not_parking("102", "3")
        not_parking("Floor", "5")

    def test_pit_general_admission(self):
        """Pit / GA sections are concert floor tickets, not parking."""
        not_parking("Pit",     "GA")
        not_parking("GA Pit",  "GA")
        not_parking("POOL GA", "GA")
        not_parking("Pool Circle GA", "GA")

    def test_section_g_row_ga(self):
        """section='G' row='GA' → General Admission floor — NOT parking.
        This is the canonical false-positive case.  The filter must never
        activate on a normal GA floor ticket.
        """
        not_parking("G",     "GA")
        not_parking("Floor", "GA")

    def test_box_and_suite(self):
        not_parking("Box 17",   "GA")
        not_parking("Suite 42", "7")

    def test_alphanumeric_section_no_parking_row(self):
        not_parking("4SE 1A",  "GA")
        not_parking("101",     "12")
        not_parking("Balcony", "A")

    def test_gametime_pit(self):
        not_parking("PIT",  "GA")    # Gametime Pit section (real production data)

    def test_orchestra_and_mezzanine(self):
        not_parking("ORCHESTRA",  "A")
        not_parking("MEZZANINE",  "B")

    def test_reserved_row_ga_not_caught(self):
        """section='RESERVED' row='GA' is ambiguous; we choose NOT to filter
        it to avoid false positives on legitimate reserved-seating tickets."""
        not_parking("RESERVED", "GA")

    def test_none_inputs(self):
        not_parking(None, None)
        not_parking("",   None)
        not_parking(None, "")
        not_parking("",   "")

    def test_whitespace_only(self):
        not_parking("   ", "   ")

    def test_normal_ga_row_numeric_section(self):
        """Numeric section with GA row is still a concert seat."""
        not_parking("100",     "GA")
        not_parking("FLOOR 1", "GA")


# ────────────────────────────────────────────────────────────────────────────
# 4. Production-sourced combo cases (section + row from real DB rows)
# ────────────────────────────────────────────────────────────────────────────

class TestProductionCombos:

    def test_address_lot_ga_row(self):
        parking("1023 S. GRAND AVE. LOT - VALET",      "GA")
        parking("601 S. PRAIRIE AVE. LOT",              "GA")
        parking("KAREEM SOUTH ENTRANCE - KIA FORUM LOT","GA")
        parking("PRAIRIE ENTRANCE - KIA FORUM LOT",     "GA")

    def test_garage_ga_row(self):
        parking("CIRCA GARAGE",         "GA")
        parking("725 S. GRAND AVE. GARAGE", "GA")
        parking("VIP WEST GARAGE",      "GA")
        parking("INDOOR GARAGE",        "GA")
        parking("7TH & FIG GARAGE",     "GA")
        parking("HOPE STREET GARAGE",   "GA")

    def test_parking_phrase_ga_row(self):
        parking("PARKING PASS",          "GA")
        parking("PREFERRED PARKING",     "GA")
        parking("GENERAL PARKING - 0.5 MI AWAY", "GA")

    def test_color_zone_ga_row(self):
        parking("BLUE ZONE",   "GA")
        parking("ORANGE ZONE", "GA")
        parking("GREEN ZONE",  "GA")
        parking("BROWN ZONE",  "GA")
        parking("BROWN ZONE LOT", "GA")

    def test_address_parking_row(self):
        parking("10117 S. PRAIRIE AVE",                            "PARKING")
        parking("10117 S. PRAIRIE AVE. WEST GARAGE-0.6MI AWAY",    "PARKING")
        parking("1013 W OLYMPIC BLVD. - LOT",                      "PARKING")

    def test_lot_parking_row(self):
        parking("LOT C",  "PARKING")
        parking("LOT G",  "PARKING")
        parking("LOT C",  "PARK")

    def test_section_g_prk_row(self):
        """n=16 in production — single-letter section + PRK row."""
        parking("G", "PRK")
        parking("F", "PRK")

    def test_section_a_parking_row(self):
        """n=1 in production — single-letter section + PARKING row."""
        parking("A", "PARKING")

    def test_hollywood_park_casino_garage(self):
        parking("HOLLYWOOD PARK CASINO GARAGE", "GA")

    def test_alta_dena_express_lot(self):
        parking("ALTA DENA EXPRESS LOT", "GA")

    def test_ps_garage_parking(self):
        parking("PS-2 GARAGE",  "PARKING")
        parking("PS-4 GARAGE",  "GA")

    def test_forum_lot(self):
        parking("KAREEM SOUTH ENTRANCE - KIA FORUM LOT", "GA")
        parking("LOT G",  "PARKING")

    def test_row_parking_word_not_exact(self):
        """Row contains 'parking' as a word but is not the bare word 'PARKING'."""
        parking("323 N PRAIRIE AVE.",   "PARKING WITHIN 1 MILE")
        parking("PRAIRIE AVE.",         "PARKING WI")        # truncated row value
        parking("JJ",                   "ONSITE PARKING")
        parking("N PRAIRIE AVE.",       "PARKING WITHIN 0.5 MILES")

    def test_street_address_section(self):
        """Sections that are street addresses = parking lots."""
        parking("323 N PRAIRIE AVE.",   "GA")
        parking("301 N PRAIRIE AVE",    "GA")
        parking("310 N. PRAIRIE AVE.",  "GA")
        parking("1415 S. HILL ST.",     "GA")
        parking("1611 S. HOPE ST.",     "GA")
        parking("725 GRAND AVE",        "GA")
        parking("200 W PICO BLVD",      "GA")
        parking("945 W. 8TH ST.",       "GA")

    def test_distance_no_space_before_unit(self):
        """Distance pattern: '1.2mi away' without space between number and 'mi'."""
        parking("323 N. PRAIRIE AVE. 1.2mi away",  "GA")
        parking("720 S GRAND AVE 0.5mi from venue", "GA")

    def test_street_addr_false_positive_guards(self):
        """Alphanumeric section designators must NOT be caught by street addr pattern."""
        not_parking("4SE 1A",   "GA")   # section code, not a street address
        not_parking("101",      "12")   # pure numeric section
        not_parking("100",      "GA")   # normal numbered section with GA row

    def test_lot_concatenated(self):
        """LOTC, LOTA, LOT1 — parking lot identifier with no space."""
        parking("LOTC",  "GA0")
        parking("LOTA",  "GA")
        parking("LOTB",  "PARKING")
        parking("LOT1",  "GA")

    def test_bare_color_section(self):
        """Bare colour name as entire section = parking zone (not a seating level)."""
        parking("BROWN",   "GA")
        parking("BROWN",   "C2")    # SoFi Brown Zone row C2
        parking("GREEN",   "GA")
        parking("ORANGE",  "GA")
        parking("BLUE",    "GA")
        # Section 'BROWN' alone is parking; 'BROWN SECTION' or 'BROWN LEVEL' might not be
        not_parking("BROWN LEVEL",   "GA")   # seating level (falls through; no bare-color match)

    def test_known_abbreviations(self):
        """PREFRD = Preferred Parking — TickPick-specific abbreviation."""
        parking("PREFRD", "GA")
        parking("PREFRD", None)
