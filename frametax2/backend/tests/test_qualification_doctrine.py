"""
test_qualification_doctrine.py

Validates the global qualification doctrine (Qualification Engine Final
Validation, Parts 1, 4, 6).

The permanent architectural guarantee: a budget line whose category has
NO explicit rule follows the program's QualificationDoctrine — never the
implementation artifact of a missing rule row. This is verified across
all three doctrines using a second, non-Mauritius jurisdiction so the
behavior is proven to be architecture, not Mauritius-specific tuning.
"""
from __future__ import annotations

import pytest

from app.calculators.qualification_derivation import (
    BudgetLine,
    ProductionFacts,
    derive_qualification_register,
)
from app.calculators.qualification_model import (
    GreyReason,
    QualificationState,
    build_little_utopia_real_register,
)
from app.data.program_spend_rules import (
    QualificationDoctrine,
    get_program_doctrine,
)


# A budget with categories that have NO rule row in ANY program (these are
# deliberately unfamiliar labels — the exact situation that previously
# collapsed to GREY). No jurisdiction has rules for a program slug we
# invent per-test, so EVERY line here hits the "no rule" terminal branch.
def _foreign_budget() -> list[BudgetLine]:
    return [
        BudgetLine("2000", "PRODUCTION CREW", 500_000.0, spend_category="btl_crew_labor_xx"),
        BudgetLine("1400", "PRINCIPAL CAST", 300_000.0, spend_category="cast_xx"),
        BudgetLine("3100", "CAMERA PACKAGE", 200_000.0, spend_category="camera_xx"),
        BudgetLine("7000", "STUDIO OVERHEAD", 100_000.0, spend_category="overhead_xx"),
    ]


def _derive(doctrine: QualificationDoctrine | None):
    return derive_qualification_register(
        _foreign_budget(),
        program_slug="zz_second_jurisdiction",
        facts=ProductionFacts(jurisdiction_code="ZZ"),
        rate=0.30,
        rules={},          # no rules for this program — every line is unmatched
        doctrine=doctrine,
    )


class TestOpenDoctrine:
    def test_unmatched_categories_are_included(self):
        reg = _derive(QualificationDoctrine.OPEN_DEFAULT_INCLUDE)
        assert all(a.state == QualificationState.QUALIFIES for a in reg)
        assert not any(a.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY for a in reg)

    def test_no_grey_reason_when_included(self):
        reg = _derive(QualificationDoctrine.OPEN_DEFAULT_INCLUDE)
        assert all(a.grey_reason is None for a in reg)


class TestClosedDoctrine:
    def test_unmatched_categories_are_excluded(self):
        reg = _derive(QualificationDoctrine.CLOSED_POSITIVE_LIST)
        assert all(a.state == QualificationState.EXCLUDED for a in reg)
        # The omission itself is the exclusion authority — no grey.
        assert not any(a.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY for a in reg)


class TestHybridDoctrine:
    def test_unmatched_categories_are_genuine_legal_interpretation_grey(self):
        reg = _derive(QualificationDoctrine.HYBRID_CONDITIONAL)
        assert all(a.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY for a in reg)
        # A grey under HYBRID is genuine (E: legal interpretation), never an
        # implementation-artifact "no rule row" grey.
        assert all(a.grey_reason == GreyReason.REQUIRES_LEGAL_INTERPRETATION for a in reg)


class TestUnclassifiedProgramFallsToCanonicalRule:
    """An unclassified program is resolved under the module's CANONICAL QPE
    RULE — "every actual budget item is included unless authoritative
    program language explicitly excludes it" — rather than being treated as
    unqualifiable.

    This REPLACES the former assertion that an unclassified doctrine sent
    100% of the budget to GREY. That behavior made an ABSENCE OF
    CLASSIFICATION operate as a prohibition, which is the precise inversion
    of the canonical rule, and it was the binding constraint that left only
    4 of 110 fully rate-modeled jurisdictions priceable. The protection the
    old test provided — nothing is ever silently decided — is preserved
    below by asserting that the resolution always states its own basis.
    """

    def test_unclassified_program_resolves_to_canonical_default_inclusion(self):
        from app.data.program_spend_rules import (
            CANONICAL_DEFAULT_DOCTRINE,
            DoctrineBasis,
            resolve_program_doctrine,
        )

        resolution = resolve_program_doctrine("a_program_never_classified")
        assert resolution.doctrine == CANONICAL_DEFAULT_DOCTRINE
        assert resolution.basis is DoctrineBasis.CANONICAL_DEFAULT
        # Never silent: the resolution always explains itself.
        assert "CANONICAL QPE RULE" in resolution.explanation

    def test_derivation_under_no_explicit_doctrine_includes_rather_than_greys(self):
        reg = _derive(None)
        assert all(a.state == QualificationState.QUALIFIES for a in reg)
        assert not any(
            a.grey_reason == GreyReason.PROGRAM_REGIME_UNCLASSIFIED for a in reg
        ), "absence of classification must no longer manufacture a modeling-gap grey"

    def test_recorded_contrary_evidence_overrides_the_default_downward(self):
        """The default applies only where nothing contradicts it. A program
        with recorded evidence of a narrower construction resolves to
        HYBRID_CONDITIONAL, so unmatched lines become genuine legal-
        interpretation greys — never silent inclusions.

        As of the Worldwide Incentive Engine Closeout phase,
        DOCTRINE_EXAMINED_NOT_CLASSIFIED is legitimately EMPTY: every
        program once deferred there (BE/DE/HR/HU/IT/US-NM, plus CY/ES/
        US-GA/US-NY deferred separately) has had its primary-source
        qualifying-expenditure text read and classified. Spain
        (es_tax_credit_foreign) is the current real example of the
        downward-override mechanism this test protects — verified directly
        below instead of iterating an empty register."""
        from app.data.program_spend_rules import (
            DoctrineBasis,
            QualificationDoctrine as QD,
            resolve_program_doctrine,
        )

        resolution = resolve_program_doctrine("es_tax_credit_foreign")
        assert resolution.doctrine == QD.HYBRID_CONDITIONAL
        assert resolution.basis is DoctrineBasis.EXPLICIT
        assert resolution.explanation  # never silent
        # Explicit here (Spain's HYBRID classification is itself primary-
        # source-read and recorded in PROGRAM_DOCTRINE, not merely inferred
        # from a deferred-evidence note) — still the same downward-from-
        # default outcome this test exists to protect: HYBRID_CONDITIONAL,
        # not a silent OPEN_DEFAULT_INCLUDE, because Spain's ATL creative-
        # personnel category is genuinely EEA-residency-conditioned (see the
        # PROGRAM_DOCTRINE comment for es_tax_credit_foreign).
        from app.data.program_spend_rules import PROGRAM_DOCTRINE
        assert "es_tax_credit_foreign" in PROGRAM_DOCTRINE

    def test_explicit_classification_always_wins(self):
        from app.data.program_spend_rules import (
            PROGRAM_DOCTRINE,
            DoctrineBasis,
            resolve_program_doctrine,
        )

        for slug, doctrine in PROGRAM_DOCTRINE.items():
            resolution = resolve_program_doctrine(slug)
            assert resolution.doctrine == doctrine
            assert resolution.basis is DoctrineBasis.EXPLICIT


class TestNoDefaultToGreyRegression:
    def test_a_rule_less_program_no_longer_all_greys_under_a_real_doctrine(self):
        """The exact prior failure: a jurisdiction with no rule rows sent
        100% of its budget to GREY. With a doctrine selected, that no
        longer happens — behavior follows the doctrine."""
        open_reg = _derive(QualificationDoctrine.OPEN_DEFAULT_INCLUDE)
        closed_reg = _derive(QualificationDoctrine.CLOSED_POSITIVE_LIST)
        assert not any(a.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY for a in open_reg)
        assert not any(a.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY for a in closed_reg)


class TestMauritiusDoctrineAssignment:
    def test_mauritius_is_hybrid_conditional(self):
        assert get_program_doctrine("mu_edb_incentive") == QualificationDoctrine.HYBRID_CONDITIONAL

    def test_real_register_has_no_invalid_greys(self):
        """Every grey in the real Little Utopia register carries a genuine
        A-F reason; none is an implementation artifact, and no MATERIAL
        on-budget grey remains (only $0 legal-interpretation lines)."""
        reg = build_little_utopia_real_register()
        greys = [a for a in reg if a.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY]
        assert all(a.grey_reason is not None for a in greys)
        material_greys = [a for a in greys if a.amount_usd >= 1.0]
        assert material_greys == []  # 7000/7100 now qualify; only $0 music/marketing remain grey
