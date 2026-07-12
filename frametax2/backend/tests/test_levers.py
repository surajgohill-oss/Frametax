"""
test_levers.py

Targeted tests for the Phase 4 Lever abstraction (levers.py) —
generalizes StructuringPath without modifying it or
optimization_engine.py.
"""
from __future__ import annotations

import pytest

from app.calculators.qualification_model import (
    AuthorityBasis,
    QualificationConfidence,
    build_little_utopia_qualification_register,
)
from app.calculators.structuring_paths import (
    REPRESENTATIVE_ROUTING_SETUP_COST_USD,
    PathStatus,
    StructuringPath,
    derive_structuring_paths,
    is_recommended,
)
from app.calculators.levers import (
    LEVERS_VERSION,
    RECOMMEND_UPSIDE_TO_COST_RATIO,
    Lever,
    LeverStatus,
    LeverType,
    derive_levers,
    derive_levers_from_structuring_paths,
    is_lever_recommended,
    lever_to_structuring_path,
    structuring_path_to_lever,
)

MU_RATE = 0.40


@pytest.fixture(scope="module")
def register():
    return build_little_utopia_qualification_register(mu_rate=MU_RATE)


@pytest.fixture()
def paths(register):
    return derive_structuring_paths(register, rate=MU_RATE)


@pytest.fixture()
def levers(register):
    return derive_levers(register, rate=MU_RATE)


# ── Module constants ─────────────────────────────────────────────────────────

class TestModuleConstants:
    def test_version(self):
        assert LEVERS_VERSION == "1.0.0"

    def test_six_lever_types(self):
        assert len(LeverType) == 6
        names = {t.value for t in LeverType}
        assert names == {"structuring", "treaty", "stacking", "reinvestment", "normalization", "timing"}

    def test_lever_status_is_path_status(self):
        """LeverStatus is PathStatus, not a parallel enum — the two
        lifecycles cannot drift apart."""
        assert LeverStatus is PathStatus

    def test_recommend_ratio_matches_structuring_paths_default(self):
        assert RECOMMEND_UPSIDE_TO_COST_RATIO == 3.0


# ── StructuringPath behavior preserved ────────────────────────────────────────

class TestStructuringPathUnaffected:
    def test_derive_structuring_paths_unchanged(self, paths):
        codes = {p.account_code for p in paths}
        assert codes == {"21-00", "23-00", "42-00"}

    def test_is_recommended_unchanged(self, paths):
        p21 = next(p for p in paths if p.account_code == "21-00")
        p23 = next(p for p in paths if p.account_code == "23-00")
        p42 = next(p for p in paths if p.account_code == "42-00")
        assert is_recommended(p21) is True
        assert is_recommended(p23) is True
        assert is_recommended(p42) is False

    def test_implementation_cost_constant_unchanged(self):
        assert REPRESENTATIVE_ROUTING_SETUP_COST_USD == 8_000.0


# ── Imported crew paths convert to LeverType.STRUCTURING ────────────────────

class TestConversionToStructuringLever:
    def test_all_derived_levers_are_structuring_type(self, levers):
        assert len(levers) == 3
        assert all(l.lever_type == LeverType.STRUCTURING for l in levers)

    def test_imported_crew_accounts_present_as_levers(self, levers):
        codes = {l.affected_accounts[0] for l in levers}
        assert codes == {"21-00", "23-00", "42-00"}

    def test_lever_carries_structuring_dependent_authority_basis(self, levers):
        for l in levers:
            assert l.authority_basis == AuthorityBasis.STRUCTURING_DEPENDENT

    def test_lever_preserves_amounts_and_cost(self, paths, levers):
        by_code = {l.affected_accounts[0]: l for l in levers}
        for p in paths:
            l = by_code[p.account_code]
            assert l.current_value_usd == p.current_amount_usd
            assert l.achievable_value_usd == p.structured_amount_usd
            assert l.implementation_cost_usd == p.implementation_cost_usd
            assert l.upside_incentive_usd == p.upside_incentive_usd

    def test_upside_value_usd_property(self, levers):
        l21 = next(l for l in levers if l.affected_accounts[0] == "21-00")
        assert l21.upside_value_usd == pytest.approx(95_000.0, abs=0.01)


# ── Recommendation threshold unchanged ────────────────────────────────────────

class TestRecommendationThresholdParity:
    def test_lever_recommendation_matches_path_recommendation(self, paths, levers):
        by_code_path = {p.account_code: p for p in paths}
        by_code_lever = {l.affected_accounts[0]: l for l in levers}
        for code in ("21-00", "23-00", "42-00"):
            assert is_lever_recommended(by_code_lever[code]) == is_recommended(by_code_path[code])

    def test_dp_and_sound_recommended_stunts_not(self, levers):
        by_code = {l.affected_accounts[0]: l for l in levers}
        assert is_lever_recommended(by_code["21-00"]) is True   # 38,000 / 8,000 = 4.75x
        assert is_lever_recommended(by_code["23-00"]) is True   # 26,000 / 8,000 = 3.25x
        assert is_lever_recommended(by_code["42-00"]) is False  # 19,200 / 8,000 = 2.4x — below 3x, still visible

    def test_stunts_lever_still_visible_though_not_recommended(self, levers):
        stunts = next(l for l in levers if l.affected_accounts[0] == "42-00")
        assert stunts.upside_incentive_usd > 0  # present, just not recommended

    def test_low_confidence_lever_not_recommended_regardless_of_ratio(self):
        lever = Lever(
            lever_id="LV-TEST", lever_type=LeverType.STRUCTURING, affected_accounts=("99-00",),
            description="test", mechanism="test", current_value_usd=0, achievable_value_usd=100_000,
            implementation_cost_usd=1_000, confidence=QualificationConfidence.LOW,
            complexity="LOW", required_documents=(), jurisdiction_code="MU",
            upside_incentive_usd=100_000,
        )
        assert is_lever_recommended(lever) is False  # huge ratio but LOW confidence


# ── Lever supports all planned types ──────────────────────────────────────────

class TestAllLeverTypesInstantiable:
    @pytest.mark.parametrize("lever_type", list(LeverType))
    def test_every_lever_type_constructible(self, lever_type):
        lever = Lever(
            lever_id=f"LV-{lever_type.value}", lever_type=lever_type, affected_accounts=(),
            description="d", mechanism="m", current_value_usd=0.0, achievable_value_usd=0.0,
            implementation_cost_usd=0.0, confidence=QualificationConfidence.LOW,
            complexity="LOW", required_documents=(), jurisdiction_code="MU",
        )
        assert lever.lever_type == lever_type
        assert lever.status == LeverStatus.PROPOSED  # default

    def test_only_structuring_has_active_discovery(self, levers):
        assert all(l.lever_type == LeverType.STRUCTURING for l in levers)
        # no discovery function exists yet for the other five types — this
        # is intentional per Phase 4 scope, not an oversight
        import app.calculators.levers as levers_module
        assert not hasattr(levers_module, "derive_treaty_levers")
        assert not hasattr(levers_module, "derive_reinvestment_levers")


# ── Lifecycle statuses preserved ──────────────────────────────────────────────

class TestLifecyclePreserved:
    def test_default_status_is_proposed(self, levers):
        assert all(l.status == PathStatus.PROPOSED for l in levers)

    def test_lever_status_transitions_mirror_path_status(self):
        path = StructuringPath(
            path_id="SP-X", account_code="21-00", description="d", mechanism="m",
            current_amount_usd=0, structured_amount_usd=95_000, implementation_cost_usd=8_000,
            complexity="MEDIUM", confidence=QualificationConfidence.MEDIUM, required_documents=(),
            status=PathStatus.EXECUTED, evidence_bound=True, upside_incentive_usd=38_000,
        )
        lever = structuring_path_to_lever(path)
        assert lever.status == PathStatus.EXECUTED
        assert lever.evidence_bound is True

    def test_round_trip_preserves_status_and_evidence_bound(self):
        path = StructuringPath(
            path_id="SP-Y", account_code="23-00", description="d", mechanism="m",
            current_amount_usd=0, structured_amount_usd=65_000, implementation_cost_usd=8_000,
            complexity="MEDIUM", confidence=QualificationConfidence.MEDIUM, required_documents=(),
            status=PathStatus.APPROVED, evidence_bound=False, upside_incentive_usd=26_000,
        )
        lever = structuring_path_to_lever(path)
        back = lever_to_structuring_path(lever)
        assert back == path


# ── Round-trip / conversion correctness ───────────────────────────────────────

class TestConversionRoundTrip:
    def test_structuring_path_to_lever_to_structuring_path_is_lossless(self, paths):
        for p in paths:
            lever = structuring_path_to_lever(p)
            back = lever_to_structuring_path(lever)
            assert back == p

    def test_derive_levers_from_structuring_paths_matches_direct_derive(self, paths, levers):
        via_paths = derive_levers_from_structuring_paths(paths)
        for a, b in zip(via_paths, levers):
            assert a == b

    def test_lever_to_structuring_path_rejects_non_structuring_type(self):
        lever = Lever(
            lever_id="LV-T", lever_type=LeverType.TREATY, affected_accounts=("21-00",),
            description="d", mechanism="m", current_value_usd=0, achievable_value_usd=0,
            implementation_cost_usd=0, confidence=QualificationConfidence.LOW,
            complexity="LOW", required_documents=(), jurisdiction_code="MU",
        )
        with pytest.raises(ValueError, match="only STRUCTURING"):
            lever_to_structuring_path(lever)

    def test_lever_to_structuring_path_rejects_multi_account(self):
        lever = Lever(
            lever_id="LV-M", lever_type=LeverType.STRUCTURING, affected_accounts=("21-00", "23-00"),
            description="d", mechanism="m", current_value_usd=0, achievable_value_usd=0,
            implementation_cost_usd=0, confidence=QualificationConfidence.LOW,
            complexity="LOW", required_documents=(), jurisdiction_code="MU",
        )
        with pytest.raises(ValueError, match="exactly one"):
            lever_to_structuring_path(lever)

    def test_jurisdiction_code_defaults_to_mu(self, paths):
        lever = structuring_path_to_lever(paths[0])
        assert lever.jurisdiction_code == "MU"

    def test_jurisdiction_code_overridable(self, paths):
        lever = structuring_path_to_lever(paths[0], jurisdiction_code="MT")
        assert lever.jurisdiction_code == "MT"


# ── No optimizer output changes for Little Utopia ────────────────────────────

class TestNoOptimizerImpact:
    def test_optimization_engine_still_consumes_structuring_path_directly(self, register, paths):
        """Confirms optimization_engine.py's build_risk_cases still works
        unmodified and untouched by levers.py's existence."""
        from app.calculators.optimization_engine import RiskCase, build_risk_cases
        result = build_risk_cases(
            register=register, gross_budget_usd=4_364_393.0, rate=MU_RATE,
            structuring_paths=paths,
        )
        cons = result.cases[RiskCase.CONSERVATIVE]
        assert cons.qpe_usd == pytest.approx(2_846_357.0, abs=1.0)
        assert cons.incentive_usd == pytest.approx(1_138_542.8, abs=1.0)

    def test_levers_module_does_not_import_optimization_engine(self):
        """levers.py must carry no import dependency on
        optimization_engine.py — it is a pure StructuringPath-adjacent
        abstraction this phase. (The module docstring mentions the
        filename in prose explaining the design decision, so this checks
        actual import statements rather than the whole source text.)"""
        import ast
        import inspect

        import app.calculators.levers as levers_module

        source = inspect.getsource(levers_module)
        tree = ast.parse(source)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        assert not any("optimization_engine" in m for m in imported_modules)
