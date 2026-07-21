"""
test_canonical_recompute_stamp.py

Regression tests for the canonical recomputation stamp — the
computation_version / computed_at pair that identifies THIS computed
state on LittleUtopiaState (and is served under `computation` on the
/production API).

The stamp is a deterministic fingerprint over EVERY effective input
store: facts, people, location overrides, and economics controls. It
must:
  * be a pure function of those inputs (same inputs -> same version),
  * change whenever any one store changes,
  * return EXACTLY to the prior version when the change is reverted,
  * advance computed_at on every real recomputation,
and every one of the four stores must invalidate the cached state so the
stamp never reports a fingerprint that no longer matches live inputs
(the economics store previously did not invalidate — guarded here).
"""
from __future__ import annotations

import pytest

from app.demo.little_utopia_state import (
    apply_economics_controls,
    apply_fact_answers,
    apply_location_overrides,
    apply_people_facts,
    canonical_input_fingerprint,
    get_state,
    reset_fact_answers,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_fact_answers()
    yield
    reset_fact_answers()


def _stamp():
    s = get_state()
    return s.computation_version, s.computed_at


class TestStampPresence:
    def test_state_carries_version_and_timestamp(self):
        ver, at = _stamp()
        assert isinstance(ver, str) and len(ver) == 16  # sha256[:16]
        # ISO-8601 UTC timestamp, whole seconds
        assert "T" in at and at.endswith("+00:00")

    def test_version_matches_input_fingerprint(self):
        # The served version is exactly the fingerprint sha of the four stores.
        assert get_state().computation_version == canonical_input_fingerprint()["sha"]

    def test_fingerprint_covers_all_four_stores(self):
        assert set(canonical_input_fingerprint()["sources"]) == {
            "facts", "people", "locations", "economics",
        }


class TestDeterministicRoundTrips:
    """Every canonical store: change -> version moves; revert -> version
    returns to the exact baseline (pure function of inputs)."""

    def test_facts_round_trip(self):
        base, _ = _stamp()
        apply_fact_answers({"component_route_post": "GR"})
        changed, _ = _stamp()
        assert changed != base
        apply_fact_answers({"component_route_post": None})
        assert _stamp()[0] == base

    def test_people_round_trip(self):
        base, _ = _stamp()
        apply_people_facts({"producer_nationality": "FR"})
        changed, _ = _stamp()
        assert changed != base
        apply_people_facts({"producer_nationality": None})
        assert _stamp()[0] == base

    def test_location_round_trip(self):
        base, _ = _stamp()
        apply_location_overrides({"desert_arid": True})
        changed, _ = _stamp()
        assert changed != base
        apply_location_overrides({"desert_arid": None})
        assert _stamp()[0] == base

    def test_economics_round_trip(self):
        base, _ = _stamp()
        apply_economics_controls({"awarded_rate": 0.40})
        changed, _ = _stamp()
        assert changed != base
        apply_economics_controls({"awarded_rate": None})
        assert _stamp()[0] == base


class TestInvalidation:
    def test_economics_change_invalidates_cached_state(self):
        """The economics store must invalidate the cached state so the stamp
        recomputes — regression guard for the missing cache_clear that made
        the version stale on an economics-only change."""
        before_ver, before_at = _stamp()
        apply_economics_controls({"awarded_rate": 0.40})
        after_ver, after_at = _stamp()
        assert after_ver != before_ver           # fingerprint moved
        assert after_at >= before_at              # rebuilt (fresh timestamp)

    def test_distinct_inputs_produce_distinct_versions(self):
        seen = {get_state().computation_version}
        for fact in ("GR", "MT", "IE"):
            apply_fact_answers({"component_route_post": fact})
            seen.add(get_state().computation_version)
        assert len(seen) == 4  # baseline + 3 distinct routes

    def test_version_stable_across_reads_without_mutation(self):
        v1 = get_state().computation_version
        v2 = get_state().computation_version
        assert v1 == v2
