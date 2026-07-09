"""
test_qualification_model.py

Targeted tests for the CineAtlas qualification-state model.

Covers:
- ATL accounts are explicit GREY_AREA_REQUIRES_AUTHORITY, never silently
  collapsed to EXCLUDED
- Imported-crew accounts are STRUCTURING_OPPORTUNITY with a mechanism
- Deterministic exclusions remain EXCLUDED with correct authority basis
- Off-budget in-kind is never present in the register / never deducted
- Register reconciles exactly against the real fixture's gross budget
- Reinvestment UNKNOWN is distinct from NOT_PERMITTED
"""
from __future__ import annotations

import pytest

from app.calculators.qualification_model import (
    QUALIFICATION_MODEL_VERSION,
    AccountQualification,
    AuthorityBasis,
    LITTLE_UTOPIA_INKIND_FMV_USD,
    QualificationConfidence,
    QualificationState,
    REINVESTMENT_REGISTRY,
    ReinvestmentCategory,
    ReinvestmentProfile,
    build_little_utopia_qualification_register,
    get_reinvestment_profile,
    summarize_register,
)
from tests.fixtures.little_utopia_sanitized import GROSS_BUDGET_USD, computed_qpe


@pytest.fixture(scope="module")
def register() -> list[AccountQualification]:
    return build_little_utopia_qualification_register()


def _get(register, code) -> AccountQualification:
    matches = [a for a in register if a.account_code == code]
    assert matches, f"Account {code} not found in register"
    return matches[0]


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert QUALIFICATION_MODEL_VERSION == "1.0.0"

    def test_five_states(self):
        assert len(QualificationState) == 5
        names = {s.value for s in QualificationState}
        assert names == {
            "qualifies", "excluded", "structuring_opportunity",
            "grey_area_requires_authority", "not_applicable",
        }

    def test_seven_reinvestment_categories(self):
        assert len(ReinvestmentCategory) == 7


# ── ATL: unknown must not silently become excluded ──────────────────────────

class TestATLGreyArea:
    @pytest.mark.parametrize("code", ["10-00", "11-00", "12-00"])
    def test_state_is_grey_area_not_excluded(self, register, code):
        a = _get(register, code)
        assert a.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY
        assert a.state != QualificationState.EXCLUDED

    @pytest.mark.parametrize("code", ["10-00", "11-00", "12-00"])
    def test_authority_basis_is_absence_not_fabricated(self, register, code):
        a = _get(register, code)
        assert a.authority_basis == AuthorityBasis.ABSENCE_OF_AUTHORITY

    @pytest.mark.parametrize("code", ["10-00", "11-00", "12-00"])
    def test_has_resolving_evidence_and_upside(self, register, code):
        a = _get(register, code)
        assert a.resolving_evidence is not None
        assert a.incentive_upside_usd == pytest.approx(a.amount_usd * 0.40, abs=0.01)

    def test_atl_grey_area_total(self, register):
        total = sum(_get(register, c).amount_usd for c in ["10-00", "11-00", "12-00"])
        assert total == pytest.approx(408_444.0, abs=0.01)


# ── Imported crew: structuring opportunity, not exclusion ───────────────────

class TestImportedCrewStructuring:
    @pytest.mark.parametrize("code", ["21-00", "23-00", "42-00"])
    def test_state_is_structuring_opportunity(self, register, code):
        a = _get(register, code)
        assert a.state == QualificationState.STRUCTURING_OPPORTUNITY
        assert a.state != QualificationState.EXCLUDED

    @pytest.mark.parametrize("code", ["21-00", "23-00", "42-00"])
    def test_authority_basis_is_structuring_dependent(self, register, code):
        a = _get(register, code)
        assert a.authority_basis == AuthorityBasis.STRUCTURING_DEPENDENT

    @pytest.mark.parametrize("code", ["21-00", "23-00", "42-00"])
    def test_has_mechanism_and_upside(self, register, code):
        a = _get(register, code)
        assert a.structuring_mechanism is not None
        assert "route" in a.structuring_mechanism.lower() or "rout" in a.structuring_mechanism.lower()
        assert a.incentive_upside_usd == pytest.approx(a.amount_usd * 0.40, abs=0.01)

    def test_structuring_opportunity_total(self, register):
        total = sum(_get(register, c).amount_usd for c in ["21-00", "23-00", "42-00"])
        assert total == pytest.approx(208_000.0, abs=0.01)
        upside = sum(_get(register, c).incentive_upside_usd for c in ["21-00", "23-00", "42-00"])
        assert upside == pytest.approx(83_200.0, abs=0.01)


# ── Deterministic exclusions remain excluded ─────────────────────────────────

class TestDeterministicExclusions:
    @pytest.mark.parametrize("code,basis", [
        ("39-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("50-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("51-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("52-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("53-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("54-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("55-00", AuthorityBasis.TERRITORIAL_NEXUS),
        ("60-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
        ("70-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
        ("71-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
        ("80-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
        ("81-00", AuthorityBasis.STRUCTURAL_DEFINITION),
        ("13-00", AuthorityBasis.CROSS_PROGRAM_CONVENTION),
    ])
    def test_excluded_with_correct_basis(self, register, code, basis):
        a = _get(register, code)
        assert a.state == QualificationState.EXCLUDED
        assert a.authority_basis == basis

    def test_post_production_exclusion_total(self, register):
        total = sum(_get(register, c).amount_usd for c in ["50-00", "51-00", "52-00", "53-00", "54-00", "55-00"])
        assert total == pytest.approx(363_000.0, abs=0.01)

    def test_not_applicable_accounts(self, register):
        fc = _get(register, "82-00")
        assert fc.state == QualificationState.NOT_APPLICABLE
        assert fc.amount_usd == 0.0
        vat = _get(register, "44-00")
        assert vat.state == QualificationState.NOT_APPLICABLE
        assert vat.amount_usd == pytest.approx(92_439.0, abs=0.01)


# ── Off-budget in-kind: never in the register, never deducted ───────────────

class TestOffBudgetInkind:
    def test_inkind_amount_constant(self):
        assert LITTLE_UTOPIA_INKIND_FMV_USD == 625_000.0

    def test_inkind_not_present_as_any_account_code(self, register):
        assert not any(a.amount_usd == 625_000.0 for a in register)

    def test_inkind_not_double_counted_in_totals(self, register):
        summary = summarize_register(register)
        total_all_states = sum(summary["amounts_by_state"].values())
        # Register total must equal gross budget WITHOUT the in-kind figure —
        # in-kind is off-budget and must never inflate this sum.
        assert total_all_states == pytest.approx(GROSS_BUDGET_USD, abs=0.01)
        assert total_all_states != pytest.approx(GROSS_BUDGET_USD + LITTLE_UTOPIA_INKIND_FMV_USD, abs=0.01)


# ── Register reconciliation ──────────────────────────────────────────────────

class TestRegisterReconciliation:
    def test_register_covers_every_fixture_account(self, register):
        assert len(register) == 41  # 40 non-memo + 1 memo (44-00)

    def test_total_reconciles_to_gross_budget(self, register):
        total = sum(a.amount_usd for a in register)
        assert total == pytest.approx(GROSS_BUDGET_USD, abs=0.01)

    def test_qualifies_state_matches_calculator_base_scenario_minus_reclassified(self, register):
        """QUALIFIES-state accounts are the calculator's base-scenario qualifying
        set minus the three accounts reclassified as STRUCTURING_OPPORTUNITY
        (21-00, 23-00, 42-00 were base_qualifies=False in the calculator, so
        they were never part of base QPE — this just confirms no double count)."""
        qualifies_total = sum(a.amount_usd for a in register if a.state == QualificationState.QUALIFIES)
        assert qualifies_total == pytest.approx(computed_qpe("base"), abs=0.01)

    def test_no_account_appears_twice(self, register):
        codes = [a.account_code for a in register]
        assert len(codes) == len(set(codes))

    def test_summarize_register_states_sum_to_gross(self, register):
        summary = summarize_register(register)
        assert sum(summary["amounts_by_state"].values()) == pytest.approx(GROSS_BUDGET_USD, abs=0.01)


# ── Reinvestment: UNKNOWN distinct from NOT_PERMITTED ────────────────────────

class TestReinvestmentModel:
    def test_mu_profile_is_unknown(self):
        profile = get_reinvestment_profile("MU")
        assert profile.category == ReinvestmentCategory.UNKNOWN

    def test_unknown_is_not_not_permitted(self):
        assert ReinvestmentCategory.UNKNOWN != ReinvestmentCategory.NOT_PERMITTED
        profile = get_reinvestment_profile("MU")
        assert profile.category != ReinvestmentCategory.NOT_PERMITTED

    def test_mu_profile_has_no_fabricated_evidence(self):
        profile = get_reinvestment_profile("MU")
        assert profile.evidence is None
        assert "no reinvestment" in profile.notes.lower() or "absence" in profile.notes.lower()

    def test_unregistered_jurisdiction_defaults_to_unknown_not_not_permitted(self):
        profile = get_reinvestment_profile("ZZ")
        assert profile.category == ReinvestmentCategory.UNKNOWN
        assert profile.category != ReinvestmentCategory.NOT_PERMITTED

    def test_registry_contains_mu(self):
        assert "MU" in REINVESTMENT_REGISTRY
        assert isinstance(REINVESTMENT_REGISTRY["MU"], ReinvestmentProfile)
