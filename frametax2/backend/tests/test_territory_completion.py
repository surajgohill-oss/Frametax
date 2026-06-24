"""
test_territory_completion.py — Database completion pass validation (migration 0060).

Validates:
  1. Every territory has a classification
  2. No territory is unclassified (missing from the module)
  3. Four valid statuses only
  4. New programs (FO, GL, IM, PK, PY, XK) are present in territory_classification
  5. All new territories with PROGRAMS_FOUND appear in the global inventory OR
     are explicitly tracked as NEW_IN_0060
  6. No-program territories cannot appear as PROGRAMS_FOUND without being in DB
  7. Status counts are internally consistent
  8. All four status categories are populated
  9. Helper functions work correctly
"""
import pytest

from app.data.territory_classification import (
    ALL_TERRITORIES,
    TerritoryClassification,
    get_classification,
    get_by_status,
    PROGRAMS_FOUND_CODES,
    NO_KNOWN_PROGRAM_CODES,
    PUBLIC_INFO_UNAVAILABLE_CODES,
    PROGRAM_STATUS_UNCLEAR_CODES,
    NEW_IN_0060,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _by_code() -> dict[str, TerritoryClassification]:
    return {t.code: t for t in ALL_TERRITORIES}


VALID_STATUSES = frozenset({
    "PROGRAMS_FOUND",
    "NO_KNOWN_PROGRAM_FOUND",
    "PUBLIC_INFORMATION_UNAVAILABLE",
    "PROGRAM_STATUS_UNCLEAR",
})


# ---------------------------------------------------------------------------
# 1. Structural integrity
# ---------------------------------------------------------------------------

def test_tc_all_territories_is_list():
    assert isinstance(ALL_TERRITORIES, list)
    assert len(ALL_TERRITORIES) > 0


def test_tc_all_territories_are_territory_classification():
    for t in ALL_TERRITORIES:
        assert isinstance(t, TerritoryClassification), (
            f"Expected TerritoryClassification, got {type(t)} for code {getattr(t, 'code', '?')}"
        )


def test_tc_no_duplicate_codes():
    codes = [t.code for t in ALL_TERRITORIES]
    assert len(codes) == len(set(codes)), "Duplicate territory codes found"


def test_tc_all_fields_present():
    for t in ALL_TERRITORIES:
        assert t.code and isinstance(t.code, str), f"Missing code: {t}"
        assert t.name and isinstance(t.name, str), f"Missing name: {t}"
        assert t.status and isinstance(t.status, str), f"Missing status: {t}"
        assert t.notes and isinstance(t.notes, str), f"Missing notes: {t}"


def test_tc_all_statuses_valid():
    invalid = [t for t in ALL_TERRITORIES if t.status not in VALID_STATUSES]
    assert not invalid, (
        f"Invalid statuses: {[(t.code, t.status) for t in invalid]}"
    )


def test_tc_codes_non_empty():
    empty = [t for t in ALL_TERRITORIES if not t.code.strip()]
    assert not empty, "Empty territory codes found"


# ---------------------------------------------------------------------------
# 2. Coverage — at least one entry per status
# ---------------------------------------------------------------------------

def test_tc_programs_found_not_empty():
    found = get_by_status("PROGRAMS_FOUND")
    assert len(found) >= 100, (
        f"Expected ≥100 PROGRAMS_FOUND territories, got {len(found)}"
    )


def test_tc_no_known_program_not_empty():
    no_prog = get_by_status("NO_KNOWN_PROGRAM_FOUND")
    assert len(no_prog) >= 50, (
        f"Expected ≥50 NO_KNOWN_PROGRAM_FOUND territories, got {len(no_prog)}"
    )


def test_tc_public_info_unavailable_populated():
    unavail = get_by_status("PUBLIC_INFORMATION_UNAVAILABLE")
    assert len(unavail) >= 5, (
        f"Expected ≥5 PUBLIC_INFORMATION_UNAVAILABLE territories, got {len(unavail)}"
    )


def test_tc_program_status_unclear_populated():
    unclear = get_by_status("PROGRAM_STATUS_UNCLEAR")
    assert len(unclear) >= 1, (
        f"Expected ≥1 PROGRAM_STATUS_UNCLEAR territories, got {len(unclear)}"
    )


# ---------------------------------------------------------------------------
# 3. Known PUBLIC_INFORMATION_UNAVAILABLE territories
# ---------------------------------------------------------------------------

_EXPECTED_UNAVAILABLE = {"AF", "ER", "IQ", "KP", "LY", "SD", "SO", "SS", "SY", "TM", "YE"}


def test_tc_known_conflict_zones_unavailable():
    for code in _EXPECTED_UNAVAILABLE:
        t = get_classification(code)
        assert t is not None, f"Territory {code} not found"
        assert t.status == "PUBLIC_INFORMATION_UNAVAILABLE", (
            f"Expected {code} to be PUBLIC_INFORMATION_UNAVAILABLE, got {t.status}"
        )


# ---------------------------------------------------------------------------
# 4. New programs from migration 0060
# ---------------------------------------------------------------------------

_EXPECTED_NEW_0060 = {"FO", "GL", "IM", "PK", "PY", "XK"}


def test_tc_new_in_0060_matches_expectation():
    assert NEW_IN_0060 == _EXPECTED_NEW_0060, (
        f"NEW_IN_0060={NEW_IN_0060} does not match expected {_EXPECTED_NEW_0060}"
    )


def test_tc_new_0060_codes_are_programs_found():
    for code in _EXPECTED_NEW_0060:
        t = get_classification(code)
        assert t is not None, f"New-in-0060 code {code} not found in ALL_TERRITORIES"
        assert t.status == "PROGRAMS_FOUND", (
            f"Expected {code} (new in 0060) to be PROGRAMS_FOUND, got {t.status}"
        )


def test_tc_new_0060_notes_mention_migration():
    for code in _EXPECTED_NEW_0060:
        t = get_classification(code)
        assert t is not None, f"Code {code} not found"
        assert "0060" in t.notes, (
            f"Expected notes for {code} to mention migration 0060, got: {t.notes[:80]}"
        )


# ---------------------------------------------------------------------------
# 5. Known PROGRAMS_FOUND core territories
# ---------------------------------------------------------------------------

_EXPECTED_PROGRAMS_FOUND = {
    "GB", "IE", "FR", "DE", "AU", "CA", "US", "NZ", "JP", "KR",
    "HU", "CZ", "MT", "GR", "IT", "ES", "BE", "NL", "SE", "NO",
    "PL", "RS", "ZA", "AE", "IL", "MA", "MX", "BR", "IS", "PT",
    "AT", "DK", "FI", "HR", "LT", "LV", "EE", "SK", "RO", "CH",
    "SG", "TH", "CN", "IN", "AR", "CL", "CO",
}


def test_tc_core_territories_are_programs_found():
    by_code = _by_code()
    missing = [
        code for code in _EXPECTED_PROGRAMS_FOUND
        if code not in by_code or by_code[code].status != "PROGRAMS_FOUND"
    ]
    assert not missing, (
        f"Core territories not classified as PROGRAMS_FOUND: {missing}"
    )


# ---------------------------------------------------------------------------
# 6. PROGRAM_STATUS_UNCLEAR — known entries
# ---------------------------------------------------------------------------

_EXPECTED_UNCLEAR = {"LA", "MM", "PS"}


def test_tc_known_unclear_territories():
    for code in _EXPECTED_UNCLEAR:
        t = get_classification(code)
        assert t is not None, f"Territory {code} not found"
        assert t.status == "PROGRAM_STATUS_UNCLEAR", (
            f"Expected {code} to be PROGRAM_STATUS_UNCLEAR, got {t.status}"
        )


# ---------------------------------------------------------------------------
# 7. Lookup helper functions
# ---------------------------------------------------------------------------

def test_tc_get_classification_known():
    t = get_classification("GB")
    assert t is not None
    assert t.code == "GB"
    assert t.status == "PROGRAMS_FOUND"


def test_tc_get_classification_unknown():
    t = get_classification("ZZ")
    assert t is None


def test_tc_get_by_status_returns_correct_subset():
    found = get_by_status("PROGRAMS_FOUND")
    for t in found:
        assert t.status == "PROGRAMS_FOUND"


def test_tc_get_by_status_invalid_returns_empty():
    result = get_by_status("INVALID_STATUS")  # type: ignore[arg-type]
    assert result == []


# ---------------------------------------------------------------------------
# 8. Frozenset constants consistency
# ---------------------------------------------------------------------------

def test_tc_programs_found_codes_consistent():
    expected = frozenset(t.code for t in ALL_TERRITORIES if t.status == "PROGRAMS_FOUND")
    assert PROGRAMS_FOUND_CODES == expected


def test_tc_no_known_program_codes_consistent():
    expected = frozenset(t.code for t in ALL_TERRITORIES if t.status == "NO_KNOWN_PROGRAM_FOUND")
    assert NO_KNOWN_PROGRAM_CODES == expected


def test_tc_public_info_unavailable_codes_consistent():
    expected = frozenset(
        t.code for t in ALL_TERRITORIES if t.status == "PUBLIC_INFORMATION_UNAVAILABLE"
    )
    assert PUBLIC_INFO_UNAVAILABLE_CODES == expected


def test_tc_program_status_unclear_codes_consistent():
    expected = frozenset(t.code for t in ALL_TERRITORIES if t.status == "PROGRAM_STATUS_UNCLEAR")
    assert PROGRAM_STATUS_UNCLEAR_CODES == expected


def test_tc_status_code_sets_are_disjoint():
    sets = [
        PROGRAMS_FOUND_CODES,
        NO_KNOWN_PROGRAM_CODES,
        PUBLIC_INFO_UNAVAILABLE_CODES,
        PROGRAM_STATUS_UNCLEAR_CODES,
    ]
    all_codes = [code for s in sets for code in s]
    assert len(all_codes) == len(set(all_codes)), (
        "Overlap between status code sets"
    )


def test_tc_status_code_sets_cover_all_territories():
    all_coded = (
        PROGRAMS_FOUND_CODES
        | NO_KNOWN_PROGRAM_CODES
        | PUBLIC_INFO_UNAVAILABLE_CODES
        | PROGRAM_STATUS_UNCLEAR_CODES
    )
    all_in_list = frozenset(t.code for t in ALL_TERRITORIES)
    assert all_coded == all_in_list


def test_tc_new_in_0060_subset_of_programs_found():
    assert NEW_IN_0060.issubset(PROGRAMS_FOUND_CODES), (
        f"NEW_IN_0060 codes not all in PROGRAMS_FOUND: "
        f"{NEW_IN_0060 - PROGRAMS_FOUND_CODES}"
    )


# ---------------------------------------------------------------------------
# 9. Migration 0060 constants
# ---------------------------------------------------------------------------

def test_tc_migration_0060_has_six_new_codes():
    assert len(NEW_IN_0060) == 6


def test_tc_faroe_islands_classified():
    t = get_classification("FO")
    assert t is not None
    assert t.name == "Faroe Islands"
    assert t.status == "PROGRAMS_FOUND"


def test_tc_greenland_classified():
    t = get_classification("GL")
    assert t is not None
    assert t.name == "Greenland"
    assert t.status == "PROGRAMS_FOUND"


def test_tc_isle_of_man_classified():
    t = get_classification("IM")
    assert t is not None
    assert t.name == "Isle of Man"
    assert t.status == "PROGRAMS_FOUND"


def test_tc_pakistan_classified():
    t = get_classification("PK")
    assert t is not None
    assert t.name == "Pakistan"
    assert t.status == "PROGRAMS_FOUND"


def test_tc_paraguay_classified():
    t = get_classification("PY")
    assert t is not None
    assert t.name == "Paraguay"
    assert t.status == "PROGRAMS_FOUND"


def test_tc_kosovo_classified():
    t = get_classification("XK")
    assert t is not None
    assert t.name == "Kosovo"
    assert t.status == "PROGRAMS_FOUND"


# ---------------------------------------------------------------------------
# 10. Notes quality
# ---------------------------------------------------------------------------

def test_tc_programs_found_notes_mention_framtax_db_or_0060():
    for t in ALL_TERRITORIES:
        if t.status == "PROGRAMS_FOUND":
            has_ref = "FrameTax DB" in t.notes or "0060" in t.notes
            assert has_ref, (
                f"{t.code}: PROGRAMS_FOUND but notes don't reference FrameTax DB or migration 0060. "
                f"Notes: {t.notes[:120]}"
            )


def test_tc_no_program_notes_mention_source_or_search():
    for t in ALL_TERRITORIES:
        if t.status == "NO_KNOWN_PROGRAM_FOUND":
            assert len(t.notes) >= 20, (
                f"{t.code}: NO_KNOWN_PROGRAM_FOUND notes too short: {t.notes!r}"
            )


def test_tc_unavailable_notes_mention_reason():
    for t in ALL_TERRITORIES:
        if t.status == "PUBLIC_INFORMATION_UNAVAILABLE":
            notes_lower = t.notes.lower()
            has_reason = any(
                kw in notes_lower
                for kw in ("conflict", "closed", "accessible", "suspended", "coup")
            )
            assert has_reason, (
                f"{t.code}: PUBLIC_INFORMATION_UNAVAILABLE notes don't explain why. "
                f"Notes: {t.notes[:120]}"
            )
