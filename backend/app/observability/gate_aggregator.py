#!/usr/bin/env python3
"""
Gate Aggregator — authoritative system gate state.

Runs each validation gate as a subprocess and aggregates by exit code only.
No string parsing. No inference. Exit code 0 = PASS, non-zero = FAIL.

Usage (inside container):
  python /app/app/observability/gate_aggregator.py

Exit: 0 if SYSTEM_STATUS=PASS, 1 if SYSTEM_STATUS=FAIL
"""
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from typing import Optional

_PY = sys.executable

_GATES: list[tuple[str, list[str]]] = [
    ("lifecycle-time-sim-test", [_PY, "/shared_scripts/test_lifecycle_time_sim.py"]),
    ("discovery-dedupe-test",   [_PY, "/shared_scripts/test_discovery_dedupe.py"]),
    ("e2e-discovery-test",      [_PY, "/shared_scripts/test_e2e_discovery.py"]),
    ("db-invariants",           [_PY, "/shared_scripts/test_invariants.py"]),
]

_GREEN  = "\033[32m"
_RED    = "\033[31m"
_RESET  = "\033[0m"
_GATE_TIMEOUT = 180   # seconds per gate


@dataclass
class GateResult:
    name:      str
    status:    str            # "PASS" | "FAIL"
    exit_code: int
    details:   Optional[str]  # last few stderr lines on failure; None on pass


@dataclass
class SystemGateState:
    system_status: str        # "PASS" | "FAIL"
    all_gates:     str        # "PASSED" | "FAILED"
    gates:         list       # list[GateResult]


def _run_gate(name: str, cmd: list[str]) -> GateResult:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=_GATE_TIMEOUT,
        )
        ok = proc.returncode == 0
        details = None
        if not ok:
            raw = (proc.stderr or proc.stdout or b"").decode(errors="replace").strip()
            # Limit to last 5 non-empty lines to keep output compact
            lines = [l for l in raw.splitlines() if l.strip()][-5:]
            details = "\n".join(lines) if lines else f"exit {proc.returncode}"
        return GateResult(
            name=name,
            status="PASS" if ok else "FAIL",
            exit_code=proc.returncode,
            details=details,
        )
    except subprocess.TimeoutExpired:
        return GateResult(name=name, status="FAIL", exit_code=-1,
                          details=f"timeout after {_GATE_TIMEOUT}s")
    except Exception as exc:
        return GateResult(name=name, status="FAIL", exit_code=-1, details=str(exc))


def _aggregate(results: list[GateResult]) -> SystemGateState:
    all_pass = all(r.status == "PASS" for r in results)
    return SystemGateState(
        system_status="PASS" if all_pass else "FAIL",
        all_gates="PASSED" if all_pass else "FAILED",
        gates=results,
    )


def _print_state(state: SystemGateState) -> None:
    sys_color = _GREEN if state.system_status == "PASS" else _RED

    print()
    print("══════════════════════════════════════════")
    print("  SYSTEM GATE STATUS")
    print("══════════════════════════════════════════")
    print(f"  SYSTEM_STATUS: {sys_color}{state.system_status}{_RESET}")
    print(f"  ALL_GATES:     {sys_color}{state.all_gates}{_RESET}")
    print()
    print("  GATES:")
    for gate in state.gates:
        color  = _GREEN if gate.status == "PASS" else _RED
        symbol = "✓" if gate.status == "PASS" else "✗"
        print(f"    {color}{symbol}{_RESET}  {gate.name}: {color}{gate.status}{_RESET}")
        if gate.details:
            for line in gate.details.splitlines():
                print(f"         {line}")
    print("══════════════════════════════════════════")
    print()


def get_system_gate_state() -> SystemGateState:
    """Public API for import by other modules."""
    results = [_run_gate(name, cmd) for name, cmd in _GATES]
    return _aggregate(results)


def main() -> int:
    state = get_system_gate_state()
    _print_state(state)
    return 0 if state.system_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
