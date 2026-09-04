"""
Final non-Globe canonical core closeout (2026-09-04), Item C.

Pure-logic tests for app/services/program_onboarding_conformance.py —
no DB session needed for most assertions (the module accepts an optional
known_jurisdiction_codes set precisely so it can run standalone). Proves
the module is genuinely data-driven (walks the LIVE registries, never a
hardcoded per-program allow-list) by classifying REAL registered
programs and asserting the classification matches what those real
registries actually contain.
"""
from __future__ import annotations

from app.services.program_onboarding_conformance import (
    CONDITIONAL,
    CONFORMANT,
    NONCONFORMANT,
    all_optimizer_visible_program_slugs,
    classify_all_programs,
    classify_program_conformance,
)


def test_all_optimizer_visible_program_slugs_is_derived_from_the_live_registry_not_hardcoded():
    slugs = all_optimizer_visible_program_slugs()
    assert len(slugs) > 50, "expected the real worldwide rate-rule registry, not a short hand list"
    assert "sa_film_commission_rebate" in slugs
    assert "us_nm_film_credit" in slugs
    # Sorted, deterministic — a stable ordering for any report built on top.
    assert slugs == tuple(sorted(slugs))


def test_a_program_with_full_data_is_conformant():
    # us_nm_film_credit: real rate rules, real ProgramRequirementsProfile,
    # real jurisdiction — used as the F#K/Bad Hombres rank-1 program
    # elsewhere in this test suite, so its data completeness is already
    # independently exercised.
    result = classify_program_conformance("us_nm_film_credit")
    assert result.jurisdiction_code == "US-NM"
    assert result.classification in (CONFORMANT, CONDITIONAL)  # never NONCONFORMANT for a real, priceable program
    assert result.assertions["economic_mechanic_supported"] is True
    assert result.assertions["valid_jurisdiction"] is True
    assert result.assertions["qpe_doctrine_available"] is True  # structurally always true


def test_a_program_with_no_registered_rate_rules_at_all_is_nonconformant():
    result = classify_program_conformance("this_program_slug_does_not_exist_anywhere")
    assert result.classification == NONCONFORMANT
    assert result.assertions["economic_mechanic_supported"] is False
    assert any("no registered RateRule" in r for r in result.reasons)


def test_classify_all_programs_never_silently_admits_a_nonconformant_program():
    """Section 6's own requirement: 'If a program cannot satisfy the
    contract: DO NOT silently allow it into optimizer execution.
    Classify it explicitly.' Asserts every classification is one of the
    three named states, with reasons attached whenever it is not fully
    CONFORMANT."""
    results = classify_all_programs()
    assert results, "expected the real worldwide program registry to be non-empty"
    for slug, result in results.items():
        assert result.classification in (CONFORMANT, CONDITIONAL, NONCONFORMANT)
        if result.classification != CONFORMANT:
            assert result.reasons, f"{slug}: {result.classification} must carry at least one named reason"


def test_jurisdiction_check_accepts_real_db_style_codes_and_subnational_suffixes():
    known = frozenset({"US", "SA", "MU"})
    # A program whose own jurisdiction_code is a plain top-level code.
    result = classify_program_conformance("sa_film_commission_rebate", known_jurisdiction_codes=known)
    assert result.assertions["valid_jurisdiction"] is True

    # A program whose jurisdiction_code is a real DB-seeded subnational
    # code should also pass when known_jurisdiction_codes carries the
    # exact subnational code (not just the country prefix).
    known_with_subnational = frozenset({"US", "US-NM"})
    result2 = classify_program_conformance("us_nm_film_credit", known_jurisdiction_codes=known_with_subnational)
    assert result2.assertions["valid_jurisdiction"] is True


def test_program_with_registered_rate_rules_but_no_jurisdiction_or_profile_is_a_real_disclosed_gap():
    """au_producer_offset (Australia's Producer Offset) has real,
    actively-used rate rules (referenced throughout treaty_engine.py,
    structure_graph_model.py, canonical_stack_bridge.py) but currently
    has no DoctrineRecord and no ProgramRequirementsProfile — a real,
    pre-existing data-completeness gap this module is designed to
    surface honestly, not paper over. This test locks in that the
    module reports it as NONCONFORMANT with named reasons rather than
    silently passing it — fixing the underlying data gap is out of
    scope for this closeout (a data-completeness item, not wiring)."""
    result = classify_program_conformance("au_producer_offset")
    assert result.assertions["economic_mechanic_supported"] is True  # it DOES have rate rules
    assert result.classification == NONCONFORMANT
    assert result.jurisdiction_code is None
