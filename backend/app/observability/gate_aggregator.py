#!/usr/bin/env python3
"""
Gate Aggregator — authoritative system gate state.

Runs each validation gate as a subprocess. Status is derived from:
  1. GATE_REPORT_JSON= line emitted on stdout (preferred, authoritative)
  2. Exit code only (fallback when JSON line absent)

No string parsing of log content. No inference from human-readable output.

Usage (inside container):
  python /app/app/observability/gate_aggregator.py              # all gates
  python /app/app/observability/gate_aggregator.py db-invariants  # one gate

Exit: 0 if system_status=PASS, 1 if system_status=FAIL
"""
import json
import subprocess
import sys
import time
from typing import Optional

sys.path.insert(0, "/app")

from app.observability.gate_schema import (
    GATE_REPORT_PREFIX,
    GateReport,
    GateStatus,
    SystemGateReport,
    make_summary,
)

_PY = sys.executable

_ALL_GATES: list[tuple[str, list[str]]] = [
    ("lifecycle-time-sim-test", [_PY, "/shared_scripts/test_lifecycle_time_sim.py"]),
    ("discovery-dedupe-test",   [_PY, "/shared_scripts/test_discovery_dedupe.py"]),
    ("e2e-discovery-test",      [_PY, "/shared_scripts/test_e2e_discovery.py"]),
    ("db-invariants",           [_PY, "/shared_scripts/test_invariants.py"]),
]

_GATE_TIMEOUT = 180   # seconds per gate

_GREEN  = "\033[32m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_RESET  = "\033[0m"


def _run_gate(name: str, cmd: list[str]) -> GateReport:
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=_GATE_TIMEOUT,
        )
        measured_ms = int((time.monotonic() - t0) * 1000)

        # Prefer structured JSON report from test script (authoritative)
        stdout = (proc.stdout or b"").decode(errors="replace")
        for line in reversed(stdout.splitlines()):
            stripped = line.strip()
            if stripped.startswith(GATE_REPORT_PREFIX):
                payload = stripped[len(GATE_REPORT_PREFIX):]
                try:
                    data = json.loads(payload)
                    return GateReport(
                        gate_name=data.get("gate_name", name),
                        status=data["status"],
                        duration_ms=data.get("duration_ms", measured_ms),
                        details=data.get("details"),
                    )
                except (json.JSONDecodeError, KeyError):
                    break  # malformed JSON — fall through to exit-code path

        # Fallback: exit code only
        ok = proc.returncode == 0
        details: Optional[dict] = None
        if not ok:
            stderr = (proc.stderr or b"").decode(errors="replace").strip()
            lines = [l for l in stderr.splitlines() if l.strip()][-5:]
            details = {"error": "\n".join(lines) if lines else f"exit {proc.returncode}"}

        return GateReport(
            gate_name=name,
            status="PASS" if ok else "FAIL",
            duration_ms=measured_ms,
            details=details,
        )

    except subprocess.TimeoutExpired:
        return GateReport(
            gate_name=name,
            status="FAIL",
            duration_ms=_GATE_TIMEOUT * 1000,
            details={"error": f"timeout after {_GATE_TIMEOUT}s"},
        )
    except Exception as exc:
        return GateReport(
            gate_name=name,
            status="FAIL",
            duration_ms=None,
            details={"error": str(exc)},
        )


def get_system_gate_report(gate_filter: Optional[list[str]] = None) -> SystemGateReport:
    """
    Public API — importable by other modules.

    gate_filter: if provided, run only gates whose name is in the list.
    """
    active = [
        (name, cmd) for name, cmd in _ALL_GATES
        if gate_filter is None or name in gate_filter
    ]
    results = [_run_gate(name, cmd) for name, cmd in active]
    summary = make_summary(results)
    all_pass = summary["failed"] == 0 and summary["total"] > 0
    return SystemGateReport(
        system_status="PASS" if all_pass else "FAIL",
        gates=results,
        summary=summary,
    )


def _print_report(report: SystemGateReport) -> None:
    sys_color = _GREEN if report.system_status == "PASS" else _RED
    s = report.summary

    print()
    print("══════════════════════════════════════════")
    print("  SYSTEM GATE STATUS")
    print("══════════════════════════════════════════")
    print(f"  SYSTEM_STATUS: {sys_color}{report.system_status}{_RESET}")
    print(
        f"  TOTAL: {s['total']} | "
        f"PASS: {s['passed']} | "
        f"FAIL: {s['failed']} | "
        f"SKIP: {s['skipped']}"
    )
    print()
    print("  GATES:")
    for gate in report.gates:
        color  = _GREEN if gate.status == "PASS" else (_YELLOW if gate.status == "SKIP" else _RED)
        symbol = "✓" if gate.status == "PASS" else ("~" if gate.status == "SKIP" else "✗")
        dur    = f" ({gate.duration_ms}ms)" if gate.duration_ms is not None else ""
        print(f"  {color}{symbol}{_RESET}  {gate.gate_name}: {color}{gate.status}{_RESET}{dur}")
        if gate.details and gate.status != "PASS":
            err = gate.details.get("error", "")
            if err:
                for line in err.splitlines()[-3:]:
                    print(f"       {line}")
    print("══════════════════════════════════════════")
    print()


def main() -> int:
    requested = sys.argv[1:] or None
    report = get_system_gate_report(gate_filter=requested)
    _print_report(report)
    return 0 if report.system_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
