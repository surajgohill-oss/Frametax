#!/usr/bin/env python3
"""
Lifecycle + Polling Policy Time Simulation Test
================================================
Tests compute_poll_interval_minutes() and compute_lifecycle_phase() with
injected datetime values at exact policy boundaries.

No DB access. No external calls. No sleep().
The functions under test are pure with respect to datetime.utcnow() — we
construct event_date values at precise offsets from the call instant to
exercise every tier and every boundary condition.

Exit: 0 = PASS, 1 = FAIL
"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/app")

from app.scheduler import compute_poll_interval_minutes, compute_lifecycle_phase

# ── Helpers ───────────────────────────────────────────────────────────────────

_GREEN = "\033[32m"
_RED   = "\033[31m"
_RESET = "\033[0m"
_failures: list[str] = []
_passed = 0


def check(label: str, got, expected, note: str = "") -> None:
    global _passed
    suffix = f"  [{note}]" if note else ""
    if got == expected:
        print(f"  {_GREEN}PASS{_RESET}  {label}  →  {got!r}{suffix}")
        _passed += 1
    else:
        print(f"  {_RED}FAIL{_RESET}  {label}  expected={expected!r}  got={got!r}{suffix}")
        _failures.append(label)


def at(**kwargs) -> datetime:
    """Return event_date = now + timedelta(**kwargs). Negative values = past."""
    return datetime.utcnow() + timedelta(**kwargs)


# ── Polling policy assertions ─────────────────────────────────────────────────

print()
print("══════════════════════════════════════════")
print("  LIFECYCLE + POLLING POLICY TIME-SIM")
print("══════════════════════════════════════════")
print()
print("── Deactivation zone (> 5 min past start) ──────────────────")

check(">5 min past  → None",  compute_poll_interval_minutes(at(minutes=-6)),      None)
check(">1 h past    → None",  compute_poll_interval_minutes(at(hours=-1)),         None)
check(">3 h past    → None",  compute_poll_interval_minutes(at(hours=-3)),         None)
check(">1 day past  → None",  compute_poll_interval_minutes(at(days=-1)),          None)

print()
print("── In-progress zone (0 → +5 min) ──────────────────────────")

check("4 min past   → 5",     compute_poll_interval_minutes(at(minutes=-4)),      5)
check("1 min past   → 5",     compute_poll_interval_minutes(at(minutes=-1)),      5)

print()
print("── < 8 h zone ──────────────────────────────────────────────")

check("1 min before → 15",    compute_poll_interval_minutes(at(minutes=1)),       15)
check("30 min before → 15",   compute_poll_interval_minutes(at(minutes=30)),      15)
check("4 h before  → 15",     compute_poll_interval_minutes(at(hours=4)),         15)
check("7h59m before → 15",    compute_poll_interval_minutes(at(hours=7, minutes=59)), 15)

print()
print("── Boundary: exactly 8 h (NOT < 8h → falls to 60 min tier) ")

check("8h exact     → 60",    compute_poll_interval_minutes(at(hours=8)),         60,
      "8h = 28800s, NOT < 28800s")
check("8h + 1 s     → 60",    compute_poll_interval_minutes(at(hours=8, seconds=1)), 60)
check("8h - 1 s     → 15",    compute_poll_interval_minutes(at(hours=8) - timedelta(seconds=1)), 15)

print()
print("── 8 h → 2 d zone ──────────────────────────────────────────")

check("12 h before  → 60",    compute_poll_interval_minutes(at(hours=12)),        60)
check("1 day before → 60",    compute_poll_interval_minutes(at(days=1)),          60)
check("47h59m before → 60",   compute_poll_interval_minutes(at(hours=47, minutes=59)), 60)

print()
print("── Boundary: exactly 2 d (NOT < 2d → falls to 240 min tier)")

check("2d exact     → 240",   compute_poll_interval_minutes(at(days=2)),          240,
      "2d = 172800s, NOT < 172800s")
check("2d + 1 s     → 240",   compute_poll_interval_minutes(at(days=2, seconds=1)), 240)
check("2d - 1 s     → 60",    compute_poll_interval_minutes(at(days=2) - timedelta(seconds=1)), 60)

print()
print("── 2 d → 10 d zone ─────────────────────────────────────────")

check("3 d before   → 240",   compute_poll_interval_minutes(at(days=3)),          240)
check("7 d before   → 240",   compute_poll_interval_minutes(at(days=7)),          240)
check("9d23h before → 240",   compute_poll_interval_minutes(at(days=9, hours=23)), 240)

print()
print("── Boundary: exactly 10 d (NOT < 10d → 1440 min tier) ─────")

check("10d exact    → 1440",  compute_poll_interval_minutes(at(days=10)),         1440,
      "10d = 864000s, NOT < 864000s")
check("10d + 1 s    → 1440",  compute_poll_interval_minutes(at(days=10, seconds=1)), 1440)
check("10d - 1 s    → 240",   compute_poll_interval_minutes(at(days=10) - timedelta(seconds=1)), 240)

print()
print("── ≥ 10 d zone ─────────────────────────────────────────────")

check("11 d before  → 1440",  compute_poll_interval_minutes(at(days=11)),         1440)
check("30 d before  → 1440",  compute_poll_interval_minutes(at(days=30)),         1440)
check("90 d before  → 1440",  compute_poll_interval_minutes(at(days=90)),         1440)

# ── Monotonicity ──────────────────────────────────────────────────────────────

print()
print("── Monotonicity: interval never increases as event approaches ")

_sequence = [
    (at(days=30),                  1440),
    (at(days=10),                  1440),   # boundary — still 1440
    (at(days=10) - timedelta(seconds=1), 240),
    (at(days=5),                    240),
    (at(days=2),                    240),   # boundary — still 240
    (at(days=2)  - timedelta(seconds=1),  60),
    (at(hours=20),                   60),
    (at(hours=8),                    60),   # boundary — still 60
    (at(hours=8)  - timedelta(seconds=1), 15),
    (at(hours=4),                    15),
    (at(minutes=1),                  15),
    (at(minutes=-1),                  5),
    (at(minutes=-4),                  5),
    (at(minutes=-6),               None),
    (at(hours=-3),                 None),
]

prev_label = None
for event_date, expected in _sequence:
    secs = (event_date - datetime.utcnow()).total_seconds()
    label = f"t={secs/3600:+.2f}h → {expected!r}"
    check(label, compute_poll_interval_minutes(event_date), expected)

# ── Lifecycle phase assertions ─────────────────────────────────────────────────

print()
print("── compute_lifecycle_phase ─────────────────────────────────")

check(">5 min past   → completed",     compute_lifecycle_phase(at(minutes=-6)),   "completed")
check("1 h past      → completed",     compute_lifecycle_phase(at(hours=-1)),      "completed")
check("4 min past    → in_progress",   compute_lifecycle_phase(at(minutes=-4)),   "in_progress")
check("1 min past    → in_progress",   compute_lifecycle_phase(at(minutes=-1)),   "in_progress")
check("1 h before    → active",        compute_lifecycle_phase(at(hours=1)),      "active")
check("15 d before   → active",        compute_lifecycle_phase(at(days=15)),      "active")
check("20d23h before → active",        compute_lifecycle_phase(at(days=20, hours=23)), "active")

print()
print("── Boundary: exactly 21 d (NOT < 21d → pre_admission) ─────")

check("21d exact     → pre_admission", compute_lifecycle_phase(at(days=21)),      "pre_admission",
      "21d = 1814400s, NOT < 1814400s")
check("21d + 1 s     → pre_admission", compute_lifecycle_phase(at(days=21, seconds=1)), "pre_admission")
check("21d - 1 s     → active",        compute_lifecycle_phase(at(days=21) - timedelta(seconds=1)), "active")
check("30 d before   → pre_admission", compute_lifecycle_phase(at(days=30)),      "pre_admission")
check("90 d before   → pre_admission", compute_lifecycle_phase(at(days=90)),      "pre_admission")

# ── Summary ───────────────────────────────────────────────────────────────────

total = _passed + len(_failures)
print()
print("══════════════════════════════════════════")
if _failures:
    print(f"  RESULT: {_RED}FAIL{_RESET} — {len(_failures)}/{total} assertion(s) failed")
    for f in _failures:
        print(f"    ✗ {f}")
    sys.exit(1)
else:
    print(f"  RESULT: {_GREEN}PASS{_RESET} — all {total} assertions correct")
    print("  Polling policy and lifecycle phase behave deterministically")
    print("  at all boundaries with no oscillation.")
    sys.exit(0)
