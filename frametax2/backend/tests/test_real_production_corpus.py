"""
Script Analyzer SA-1.5 — real-production corpus and holdout-guard tests.

These lock in the two properties the corpus exists to guarantee:

  1. Every fixture points at authoritative Company Library records and
     reconciles its budget against the SOURCE, not against a written-in oracle.
  2. Held-out actual data is mechanically unreachable from a prediction path.
"""
import pytest

from app.validation.holdout_guard import (
    HELD_OUT_FIELDS,
    HoldoutViolation,
    PredictionSession,
    assert_no_leakage,
)
from app.validation.real_production_corpus import (
    CORPUS,
    FIXTURES,
    MaterialStatus,
    ReconciliationStatus,
    ValidationMode,
    deep_fixtures,
    fixtures_for_mode,
    get_fixture,
    resolved_fixtures,
)

EXPECTED_KEYS = {"little_utopia", "fvd", "lips_like_sugar",
                 "underwater", "the_system", "tetrad"}


# ── registry shape ─────────────────────────────────────────────────────────

def test_all_six_named_projects_are_accounted_for():
    assert set(FIXTURES) == EXPECTED_KEYS
    assert len(CORPUS) == 6


def test_five_resolved_one_unresolved_and_the_gap_is_honest():
    resolved = {f.fixture_key for f in resolved_fixtures()}
    assert resolved == EXPECTED_KEYS - {"tetrad"}
    tetrad = get_fixture("tetrad")
    assert tetrad.resolved is False
    assert tetrad.project_id is None
    assert tetrad.validation_modes == ()
    assert tetrad.holdout_eligible is False
    # its externally-declared figures must NOT be presented as reconciled
    assert tetrad.budget_reconciliation.status is ReconciliationStatus.NO_BUDGET
    assert tetrad.budget_reconciliation.source_declared_total_usd is None


def test_every_resolved_fixture_references_authoritative_document_versions():
    for f in resolved_fixtures():
        assert f.project_id
        available = [m for m in f.materials if m.status == MaterialStatus.AVAILABLE]
        assert available, f"{f.fixture_key} has no available materials"
        for m in available:
            assert m.document_version_id, f"{f.fixture_key}/{m.category} lacks a DocumentVersion id"
            assert m.filename
            assert m.checksum_prefix


def test_no_fixture_duplicates_source_content():
    """The registry references; it never copies. No field may carry document text."""
    for f in CORPUS:
        for m in f.materials:
            assert not hasattr(m, "raw_text")
            assert not hasattr(m, "content")


# ── budget reconciliation (Part C) ─────────────────────────────────────────

def test_every_resolved_fixture_declares_its_oracle_from_the_source():
    """The acceptance oracle must be independently present in the document."""
    for f in resolved_fixtures():
        r = f.budget_reconciliation
        assert r.acceptance_oracle_usd is not None
        assert r.source_declared_total_usd == r.acceptance_oracle_usd, (
            f"{f.fixture_key}: the source's own declared total must equal the oracle"
        )
        assert r.basis and r.evidence


def test_reconciliation_statuses_are_the_verified_ones():
    assert get_fixture("fvd").budget_reconciliation.status is ReconciliationStatus.RECONCILED_EXACT
    assert (get_fixture("little_utopia").budget_reconciliation.status
            is ReconciliationStatus.RECONCILED_SOURCE_ROUNDING)
    for key in ("lips_like_sugar", "underwater", "the_system"):
        assert (get_fixture(key).budget_reconciliation.status
                is ReconciliationStatus.RECONCILED_DECLARED_TOTAL_LEAF_GAP)


def test_little_utopia_variance_is_the_known_two_dollar_source_rounding():
    r = get_fixture("little_utopia").budget_reconciliation
    assert r.leaf_gap_usd == 2.0
    assert r.parsed_leaf_sum_usd - r.acceptance_oracle_usd == 2.0


def test_underwater_oracle_reconciles_from_its_own_component_totals():
    """The strongest case: every component of the oracle is in the source."""
    h = get_fixture("underwater").held_out
    total = (h.atl_total_usd + h.btl_total_usd + h.fringes_usd
             + h.contingency_usd + h.completion_bond_usd)
    assert total == h.gross_budget_usd == 7998944.0


def test_leaf_gaps_are_quantified_not_hidden():
    for key in ("lips_like_sugar", "underwater", "the_system"):
        r = get_fixture(key).budget_reconciliation
        assert r.leaf_gap_usd and r.leaf_gap_usd > 0
        assert r.parsed_leaf_sum_usd + r.leaf_gap_usd == r.acceptance_oracle_usd


# ── validation modes (Part H) ──────────────────────────────────────────────

def test_little_utopia_is_the_optimizer_regression_fixture_and_not_holdout():
    lu = get_fixture("little_utopia")
    assert lu.supports(ValidationMode.OPTIMIZER_REGRESSION)
    assert lu.holdout_eligible is False


def test_modes_match_the_materials_a_fixture_actually_has():
    for f in resolved_fixtures():
        if f.supports(ValidationMode.SCRIPT_BREAKDOWN_VALIDATION):
            assert f.status_of("screenplay") == MaterialStatus.AVAILABLE
        # no fixture may claim schedule validation without a schedule
        if f.supports(ValidationMode.SCHEDULE_VALIDATION):
            assert f.status_of("schedule") == MaterialStatus.AVAILABLE


def test_no_fixture_claims_a_future_engine_mode_yet():
    """BUDGET_ESTIMATION_VALIDATION / SCHEDULE_VALIDATION await their engines."""
    assert fixtures_for_mode(ValidationMode.BUDGET_ESTIMATION_VALIDATION) == ()
    assert fixtures_for_mode(ValidationMode.SCHEDULE_VALIDATION) == ()


# ── The System deep fixture (Part I) ───────────────────────────────────────

def test_the_system_is_the_deep_multi_document_fixture():
    deep = deep_fixtures()
    assert [f.fixture_key for f in deep] == ["the_system"]
    ts = get_fixture("the_system")
    for cat in ("screenplay", "budget", "schedule", "dood"):
        assert ts.status_of(cat) == MaterialStatus.AVAILABLE
    # schedule and DOOD are the same artefact serving two roles
    assert ts.material("schedule").document_version_id == ts.material("dood").document_version_id
    assert ts.held_out.shoot_days == 20
    assert "Mississippi" in (ts.held_out.production_geography or "")


def test_missing_finance_plan_is_recorded_as_missing_not_invented():
    ts = get_fixture("the_system")
    assert ts.status_of("finance_plan") == MaterialStatus.MISSING
    assert ts.held_out.qpe_usd is None  # not fabricated from external knowledge


# ── FVD (Part K) ───────────────────────────────────────────────────────────

def test_fvd_is_verified_with_greece_supported_by_source_evidence():
    fvd = get_fixture("fvd")
    assert fvd.resolved
    assert fvd.budget_reconciliation.status is ReconciliationStatus.RECONCILED_EXACT
    assert fvd.budget_reconciliation.acceptance_oracle_usd == 4517687.0
    assert fvd.held_out.production_geography == "Greece"
    assert "V-BRAT_V8_Greece" in fvd.material("budget").filename
    assert fvd.script_side.parsed is True
    assert fvd.script_side.scene_count == 99


# ── holdout guard (Part G) ─────────────────────────────────────────────────

def test_prediction_inputs_expose_only_script_side_data():
    s = PredictionSession(get_fixture("fvd"))
    inputs = s.prediction_inputs()
    for held in ("gross_budget_usd", "shoot_days", "production_geography"):
        assert not hasattr(inputs, held)


def test_actuals_cannot_be_revealed_before_a_prediction_is_recorded():
    s = PredictionSession(get_fixture("the_system"))
    with pytest.raises(HoldoutViolation):
        s.reveal_actuals()
    s.close_prediction({"predicted_shoot_days": 22})
    actuals = s.reveal_actuals()
    assert actuals.shoot_days == 20


def test_reading_an_undeclared_held_out_field_raises():
    s = PredictionSession(get_fixture("underwater"))
    with pytest.raises(HoldoutViolation):
        s.user_input("gross_budget_usd")


def test_an_explicitly_declared_user_input_is_allowed():
    s = PredictionSession(get_fixture("underwater"), user_provided={"shoot_days"})
    assert s.user_input("shoot_days") == 30
    with pytest.raises(HoldoutViolation):
        s.user_input("gross_budget_usd")   # still guarded


def test_declaring_a_non_held_out_field_is_rejected():
    with pytest.raises(ValueError):
        PredictionSession(get_fixture("fvd"), user_provided={"not_a_real_field"})


def test_a_non_holdout_fixture_cannot_be_used_for_prediction_evaluation():
    with pytest.raises(HoldoutViolation):
        PredictionSession(get_fixture("little_utopia"))
    with pytest.raises(HoldoutViolation):
        PredictionSession(get_fixture("tetrad"))


def test_leakage_detector_catches_an_actual_value_hidden_in_a_payload():
    fvd = get_fixture("fvd")
    clean = {"scene_count": 99, "characters": 38, "notes": "script-derived only"}
    assert_no_leakage(clean, fvd)  # must not raise

    leaked = {"scene_count": 99, "estimate": {"nested": {"total": 4517687.0}}}
    with pytest.raises(HoldoutViolation):
        assert_no_leakage(leaked, fvd)


def test_leakage_detector_catches_a_leaked_geography_string():
    fvd = get_fixture("fvd")
    with pytest.raises(HoldoutViolation):
        assert_no_leakage({"basis": "shot in Greece"}, fvd)


def test_leakage_detector_respects_an_allowed_producer_input():
    uw = get_fixture("underwater")
    payload = {"atl_estimate": 2731485.0}
    with pytest.raises(HoldoutViolation):
        assert_no_leakage(payload, uw)
    assert_no_leakage(payload, uw, allowed=frozenset({"atl_total_usd"}))


def test_held_out_field_set_covers_every_actual():
    for name in ("gross_budget_usd", "atl_total_usd", "btl_total_usd", "fringes_usd",
                 "contingency_usd", "completion_bond_usd", "shoot_days",
                 "production_geography", "qpe_usd", "cast_role_count",
                 "schedule_document_version_id", "dood_document_version_id"):
        assert name in HELD_OUT_FIELDS


# ── generic project execution (Part J) ─────────────────────────────────────

def test_fixtures_are_data_and_need_no_project_specific_runner():
    """Every fixture is consumed through the same generic accessors."""
    for f in CORPUS:
        assert isinstance(f.fixture_key, str)
        assert get_fixture(f.fixture_key) is f
    # no per-project branching exists in the registry module itself
    import inspect

    from app.validation import real_production_corpus as mod
    src = inspect.getsource(mod)
    for banned in ("def run_lips_like_sugar", "def run_the_system",
                   "def run_underwater", "def run_fvd"):
        assert banned not in src
