"""LLS-SPECIFIC PERFORMANCE REPAIR (2026-10-01) -- focused tests for the
diagnostic sink (app/services/_lls_profile_sink.py), kept per the cleanup
rule's "converted into a clean, generally useful, default-disabled diagnostic
with focused tests" exception. Proves the sink is genuinely zero-cost when
disabled (the state every real evaluate_project call runs under) and behaves
correctly when a diagnostic run enables it."""
from __future__ import annotations

import app.services._lls_profile_sink as prof


def test_disabled_by_default_and_ticks_are_no_ops():
    assert prof.ENABLED is False
    prof.reset()
    prof.tick("anything")
    prof.set_phase("should not record")
    assert prof.COUNTERS == {}
    assert prof.PHASE == "not started"
    assert prof.PHASE_HISTORY == []


def test_enabled_tick_and_set_phase_record_state():
    prof.ENABLED = True
    try:
        prof.reset()
        prof.tick("foo")
        prof.tick("foo")
        prof.tick("bar", 5)
        assert prof.COUNTERS == {"foo": 2, "bar": 5}
        prof.set_phase("phase one")
        prof.set_phase("phase two")
        assert prof.PHASE == "phase two"
        assert [p for _, p in prof.PHASE_HISTORY] == ["phase one", "phase two"]
    finally:
        prof.ENABLED = False


def test_reset_clears_prior_state():
    prof.ENABLED = True
    try:
        prof.reset()
        prof.tick("stale")
        prof.set_phase("stale phase")
        prof.reset()
        assert prof.COUNTERS == {}
        assert prof.PHASE_HISTORY == []
        assert prof.PHASE == "not started"
    finally:
        prof.ENABLED = False


def test_dump_includes_phase_and_counters():
    prof.ENABLED = True
    try:
        prof.reset()
        prof.tick("widgets", 3)
        prof.set_phase("doing the thing")
        text = prof.dump("TEST LABEL")
        assert "TEST LABEL" in text
        assert "doing the thing" in text
        assert "widgets = 3" in text
    finally:
        prof.ENABLED = False


def test_maybe_print_is_a_no_op_when_disabled(capsys):
    assert prof.ENABLED is False
    prof.reset()
    prof.maybe_print(0.0)
    captured = capsys.readouterr()
    assert captured.out == ""
