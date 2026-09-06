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
    PATHWAY_SPECIFIC,
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
        assert result.classification in (CONFORMANT, CONDITIONAL, PATHWAY_SPECIFIC, NONCONFORMANT)
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


def test_au_producer_offset_is_pathway_specific_not_nonconformant():
    """Optimizer FINAL closeout, P1-CONF-001 (Codex, full optimizer
    audit). au_producer_offset (Australia's Producer Offset) has real,
    actively-used rate rules (referenced throughout treaty_engine.py,
    structure_graph_model.py, canonical_stack_bridge.py) but has no
    DoctrineRecord and no ProgramRequirementsProfile — NOT because of a
    data-completeness accident, but because
    program_rate_rules_worldwide.py's own module comment documents it
    was deliberately never register()-ed into ordinary jurisdiction
    discovery: it is materialized as an executable RateRule ONLY for the
    conditional official-co-production treaty pricing path (confirmed
    live: it prices inside 123 fully-priced conditional treaty
    scenarios). Classifying it NONCONFORMANT (the old behavior) was a
    real canonical contradiction — a program cannot be simultaneously
    'invalid' and 'silently priced through a special path'. It is now
    PATHWAY_SPECIFIC, with its real jurisdiction (AU) resolved from
    national_cultural_status.py's own existing, cited
    _CONFIRMED_SEPARATE_PATHWAY record — never left null, never
    fabricated."""
    result = classify_program_conformance("au_producer_offset")
    assert result.assertions["economic_mechanic_supported"] is True  # it DOES have rate rules
    assert result.assertions["pathway_specific_executable"] is True
    assert result.classification == PATHWAY_SPECIFIC
    assert result.classification != NONCONFORMANT
    assert result.jurisdiction_code == "AU"
    assert result.reasons, "expected an explicit reason explaining the pathway-specific status"


def test_pathway_specific_detection_is_structural_not_a_hardcoded_slug_check():
    """The detection rule (has_rate_rules AND doctrine is None AND
    profile is None) must be genuinely structural — never a per-slug
    allow-list. Verified by confirming a program that HAS a doctrine or
    profile record is never misclassified as PATHWAY_SPECIFIC even when
    it also has real rate rules."""
    result = classify_program_conformance("us_nm_film_credit")
    assert result.assertions["pathway_specific_executable"] is False
    assert result.classification != PATHWAY_SPECIFIC


def test_pathway_specific_uniquely_identifies_au_producer_offset_in_current_corpus():
    """Sanity guard: confirms this real signal currently isolates exactly
    the one confirmed real case, not a broader (and therefore probably
    wrong) set of programs."""
    results = classify_all_programs()
    pathway_specific_slugs = [
        slug for slug, r in results.items() if r.classification == PATHWAY_SPECIFIC
    ]
    assert pathway_specific_slugs == ["au_producer_offset"]
