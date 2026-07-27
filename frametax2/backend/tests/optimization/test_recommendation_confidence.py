from __future__ import annotations

"""Phase 2 (Final Backend Closeout) — recommendation-confidence status.

Pins the deterministic classification and, critically, the invariant the
whole phase exists to guarantee: a fully-priced structure whose participating
program asserts a mandatory statutory gate, or that is gated on outstanding
confirmations, must NOT read as a clean CONFIRMED recommendation — even when it
is the lowest-NPC (leading) option.
"""

from app.optimization.recommendation_confidence import (
    ConfidenceStatus,
    derive_confidence_status,
)
from app.demo.little_utopia_state import build_allocated_structures, get_state


class TestDerivation:
    def test_unpriced_is_unavailable(self):
        status, reasons = derive_confidence_status(
            is_fully_priced=False, gated=True, incentive_program_slugs=("x",))
        assert status is ConfidenceStatus.UNAVAILABLE
        assert reasons

    def test_asserted_hard_gate_is_conditional_even_when_priced_and_ungated(self):
        # fr_trip has cultural_test_required=True and preapproval_mandatory=True
        status, reasons = derive_confidence_status(
            is_fully_priced=True, gated=False, incentive_program_slugs=("fr_trip",))
        assert status is ConfidenceStatus.CONDITIONAL
        assert "cultural test" in reasons[0]

    def test_priced_and_gated_without_known_gate_is_pending(self):
        # al_cash_rebate (Albania) has no requirements profile -> no asserted
        # hard gate; gated True must yield the pending status, not CONFIRMED.
        status, _ = derive_confidence_status(
            is_fully_priced=True, gated=True, incentive_program_slugs=("al_cash_rebate",))
        assert status is ConfidenceStatus.PRICED_QUALIFICATION_PENDING

    def test_priced_ungated_but_profile_missing_is_priced_not_confirmed(self):
        status, _ = derive_confidence_status(
            is_fully_priced=True, gated=False, incentive_program_slugs=("al_cash_rebate",))
        assert status is ConfidenceStatus.PRICED

    def test_confirmed_requires_positive_clearance(self):
        # A program whose every hard gate is explicitly False, priced, ungated.
        # us_ga_film_credit sets cultural_test_required=False; but preapproval
        # is unstated (None) -> still not CONFIRMED (never overstate).
        status, _ = derive_confidence_status(
            is_fully_priced=True, gated=False, incentive_program_slugs=("us_ga_film_credit",))
        assert status is not ConfidenceStatus.CONFIRMED

    def test_deterministic(self):
        a = derive_confidence_status(is_fully_priced=True, gated=False, incentive_program_slugs=("fr_trip",))
        b = derive_confidence_status(is_fully_priced=True, gated=False, incentive_program_slugs=("fr_trip",))
        assert a == b


class TestServedPayloadCarriesStatus:
    def test_every_structure_has_a_valid_confidence_status(self):
        d = build_allocated_structures(get_state())
        valid = {s.value for s in ConfidenceStatus}
        for s in d["structures"]:
            assert s["confidence_status"] in valid, s["structure_id"]
            assert isinstance(s["confidence_reasons"], list)

    def test_leading_structure_does_not_overstate_certainty(self):
        """The single most important guarantee of Phase 2: the rank-1
        (leading) structure must not read as CONFIRMED when the engine cannot
        actually confirm its mandatory qualification. For Little Utopia the
        leading is the Mauritius baseline, whose program has no requirements
        profile, so its honest status is PRICED — never CONFIRMED."""
        d = build_allocated_structures(get_state())
        rank1 = next(r for r in d["ranking"] if r["rank"] == 1)
        leading = next(s for s in d["structures"] if s["structure_id"] == rank1["structure_id"])
        assert leading["confidence_status"] != ConfidenceStatus.CONFIRMED.value

    def test_no_structure_is_confirmed_while_its_qualification_is_unverified(self):
        """Systemic honesty check: because only minimum_spend is machine-
        enforced (Phase 1), no served structure should currently be able to
        claim CONFIRMED. If this ever fails, a program gained a fully-cleared
        requirements profile — verify that is real before relaxing this."""
        d = build_allocated_structures(get_state())
        confirmed = [s["structure_id"] for s in d["structures"]
                     if s["confidence_status"] == ConfidenceStatus.CONFIRMED.value]
        assert confirmed == [], f"Unexpected CONFIRMED structures: {confirmed}"
