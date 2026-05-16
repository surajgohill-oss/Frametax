"""
Canonical gate report schema — v1.

This module defines the ONLY valid intermediate representation for gate
state across the system. All gate scripts, the aggregator, and consumers
(debug-snapshot, CI) must produce and consume these types.

Authoritativeness rule: if two outputs disagree, the JSON-serialised
GateReport (emitted as GATE_REPORT_JSON=...) wins over log text.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, Optional

GateStatus = Literal["PASS", "FAIL", "SKIP"]


@dataclass
class GateReport:
    gate_name:   str
    status:      GateStatus
    duration_ms: Optional[int] = None
    details:     Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "gate_name":   self.gate_name,
            "status":      self.status,
            "duration_ms": self.duration_ms,
            "details":     self.details,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, d: dict) -> GateReport:
        return cls(
            gate_name=d["gate_name"],
            status=d["status"],
            duration_ms=d.get("duration_ms"),
            details=d.get("details"),
        )

    @classmethod
    def from_json(cls, s: str) -> GateReport:
        return cls.from_dict(json.loads(s))


@dataclass
class SystemGateReport:
    system_status: Literal["PASS", "FAIL"]
    gates:         list[GateReport]
    summary:       dict   # {total, passed, failed, skipped}

    def to_dict(self) -> dict:
        return {
            "system_status": self.system_status,
            "gates":         [g.to_dict() for g in self.gates],
            "summary":       self.summary,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def make_summary(gates: list[GateReport]) -> dict:
    passed  = sum(1 for g in gates if g.status == "PASS")
    failed  = sum(1 for g in gates if g.status == "FAIL")
    skipped = sum(1 for g in gates if g.status == "SKIP")
    return {"total": len(gates), "passed": passed, "failed": failed, "skipped": skipped}


# Wire prefix used by all test scripts when emitting structured output.
GATE_REPORT_PREFIX = "GATE_REPORT_JSON="
