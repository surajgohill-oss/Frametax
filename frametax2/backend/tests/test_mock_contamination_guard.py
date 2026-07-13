"""
test_mock_contamination_guard.py

Regression guard for the confirmed mock-contamination defect (introduced
by commit dee6c2b's "Seam C" rewiring, fixed by restoring the original
primary/research separation):

  1. MockConnector/legal research output must never alter the primary
     production register, QPE, structures, scenarios or recommendations.
  2. No mock/demo citation may ever be classified as EXPLICIT_STATUTE.
  3. The API distinguishes authoritative evidence from mock research.
"""
from __future__ import annotations

import pytest

from app.calculators.optimization_engine import RiskCase
from app.calculators.qualification_model import (
    AccountQualification,
    AuthorityBasis,
    GreyAreaItem,
    GreyAreaStatus,
    QualificationConfidence,
    QualificationState,
    apply_grey_area_resolution,
    build_little_utopia_real_register,
    is_authoritative_citation,
    resolve_grey_area,
)


def _synthetic_grey_register_and_item():
    """A minimal, fixture-independent grey-area account + matching
    GreyAreaItem, used only to exercise the provenance-guard mechanism
    itself — decoupled from whichever accounts happen to be grey in the
    current Little Utopia register (which changes as statutory rules are
    corrected; see test_qualification_model.py for the current, real
    grey-area state)."""
    register = [AccountQualification(
        account_code="TEST-01", description="Synthetic grey-area account",
        amount_usd=10_000.0, state=QualificationState.GREY_AREA_REQUIRES_AUTHORITY,
        confidence=QualificationConfidence.LOW, authority_basis=AuthorityBasis.ABSENCE_OF_AUTHORITY,
        reason="No category in the primary source covers this spend.",
        financial_impact_usd=10_000.0,
    )]
    item = GreyAreaItem(
        item_id="GA-TEST", account_codes=("TEST-01",), amount_usd=10_000.0,
        jurisdiction_code="MU", authority_to_ask="Test Authority",
        resolving_evidence="Test evidence request.",
    )
    return register, item


@pytest.fixture(scope="module")
def state():
    from app.demo.little_utopia_state import get_state, reset_fact_answers
    reset_fact_answers()
    return get_state()


class TestPrimaryPipelineIsMockFree:
    def test_served_register_equals_raw_statutory_register(self, state):
        """The served register must be byte-equivalent in state/basis to a
        fresh raw derivation — no legal-cycle reclassification applied."""
        raw = build_little_utopia_real_register()
        assert [(a.account_code, a.state, a.authority_basis) for a in state.register] == \
               [(a.account_code, a.state, a.authority_basis) for a in raw]

    def test_served_qpe_excludes_mock_resolved_amounts(self, state):
        served_qpe = sum(a.amount_usd for a in state.register if a.state == QualificationState.QUALIFIES)
        raw_qpe = sum(
            a.amount_usd
            for a in build_little_utopia_real_register()
            if a.state == QualificationState.QUALIFIES
        )
        assert served_qpe == raw_qpe  # mock cycle adds nothing

    def test_served_register_never_shows_mock_in_any_reason(self, state):
        """No served account's reason text may reference mock/demo
        research — the primary register is statute-and-fact only. (Which
        specific accounts are grey at any moment depends on the current
        statutory rules; see test_qualification_model.py for the current
        real grey-area state — this test asserts the mock-free INVARIANT,
        not a specific account's classification.)"""
        for a in state.register:
            assert "mock" not in a.reason.lower()

    def test_composition_and_ranking_reconcile_to_raw_register(self, state):
        raw_qpe = sum(
            a.amount_usd
            for a in build_little_utopia_real_register()
            if a.state == QualificationState.QUALIFIES
        )
        mu = next(c for c in state.composition.candidates if c.candidate_id == "PSC-MU")
        assert mu.cases[RiskCase.CONSERVATIVE].qpe_usd == pytest.approx(raw_qpe, abs=0.01)
        rank1 = state.scenario_ranking.ranks[0]
        scen = next(s for s in state.scenario_ranking.structures if s.structure_id == rank1.structure_id)
        assert scen.cases[RiskCase.CONSERVATIVE].qpe_usd == pytest.approx(raw_qpe, abs=0.01)

    def test_mock_cycle_runs_but_never_auto_resolves_genuine_grey(self, state):
        """The research cycle still runs (questions detected/staged) but,
        per Part 5 of the production-economics phase, it NEVER auto-verifies,
        approves, or commits the genuine GA-INKIND-FMV grey via mock. The
        grey stays OPEN with its resolution paths exposed; mock evidence
        must never resolve a genuine grey or alter a headline number."""
        assert state.legal_cycle is not None
        assert len(state.legal_cycle.questions) > 0  # cycle ran
        assert state.legal_commit is None             # nothing mock-committed
        # the primary grey areas were never touched by that cycle
        for g in state.grey_areas_baseline:
            assert g.status == GreyAreaStatus.OPEN


class TestProvenanceGuard:
    def test_mock_citation_is_not_authoritative(self):
        assert not is_authoritative_citation("Mock retrieval: TASK-X")
        assert not is_authoritative_citation("mock://mu/TASK-X")
        assert not is_authoritative_citation("MOCK CONNECTOR — no live retrieval performed")
        assert not is_authoritative_citation(None)
        assert not is_authoritative_citation("")
        assert is_authoritative_citation("EDB Ruling FRS-2026-0412")

    def test_mock_resolution_never_upgrades_to_explicit_statute(self):
        register, ga = _synthetic_grey_register_and_item()
        resolved = resolve_grey_area(ga, GreyAreaStatus.RESOLVED_INCLUDE,
                                     ruling_citation="Mock retrieval: TASK-GA-TEST")
        updated = apply_grey_area_resolution(register, resolved)
        for code in ("TEST-01",):
            a = next(x for x in updated if x.account_code == code)
            assert a.authority_basis != AuthorityBasis.EXPLICIT_STATUTE
            assert a.authority_basis == AuthorityBasis.ABSENCE_OF_AUTHORITY  # prior basis kept
            assert a.confidence == QualificationConfidence.LOW
            assert a.reason.startswith("NON-AUTHORITATIVE")

    def test_authoritative_resolution_still_upgrades(self):
        """Real citations keep the original upgrade behavior — the guard
        gates provenance, it does not disable resolution."""
        register, ga = _synthetic_grey_register_and_item()
        resolved = resolve_grey_area(ga, GreyAreaStatus.RESOLVED_INCLUDE,
                                     ruling_citation="EDB Ruling FRS-2026-0412")
        updated = apply_grey_area_resolution(register, resolved)
        for code in ("TEST-01",):
            a = next(x for x in updated if x.account_code == code)
            assert a.state == QualificationState.QUALIFIES
            assert a.authority_basis == AuthorityBasis.EXPLICIT_STATUTE
            assert a.confidence == QualificationConfidence.HIGH
