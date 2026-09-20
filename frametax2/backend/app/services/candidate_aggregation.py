"""
Bounded candidate accounting: candidates that are NOT retained as detailed rows are COUNTED EXACTLY.

Enumeration cardinality must never define persistence cardinality. The engine evaluates every candidate
(FVD: 526,155; Lips Like Sugar: >500K), but CineGlobe serves a bounded decision set (see
services/candidate_retention.py). Every candidate outside that set -- plain RULE_REJECTED permutations,
PRICED candidates that fall outside the retained top sets, and any capped high-volume status -- is folded,
while it is generated, into an aggregate group keyed by its canonical identity:

    (original candidate status, structure family/type, reason class,
     primary jurisdiction + participant jurisdiction set, program / component / treaty family)

Each group keeps: the exact ``candidate_count``; min/max NPC and incentive (where the candidates carry
them); the best (lowest-NPC) economic identity; the generation sequence of its first member; ONE
representative (the first member's structure identity, full trace and warnings) sufficient to reconstruct
what the group is; and -- for PRICED groups -- a reference to the RETAINED detailed row that dominates
every member (the best retained candidate of the same structure type). Groups are persisted as narrow rows
in evaluation_candidate_aggregates in the same transaction as the detailed rows.

The number of groups is itself bounded: the first ``FINE_GROUP_CAP`` distinct fine identities keep their
full participant/program sets; every later candidate whose fine identity is new folds into a COARSE group
(status, family/type, reason class, primary jurisdiction, component family). Counts stay exact either way.

The accounting invariant enforced by the bulk writer at commit (fail closed on any mismatch):

    candidates generated == detailed rows persisted + sum(candidate aggregate counts)
"""
from __future__ import annotations

import hashlib
import json
import zlib
from typing import Any, Iterator

REJECTED_STATUS = "RULE_REJECTED"
PRICED_STATUS = "PRICED"

#: Distinct FINE aggregate identities kept before new identities fold into coarse groups.
FINE_GROUP_CAP = 5000


def _strings(*values: Any) -> list[str]:
    """Sorted unique non-empty strings from scalars and lists of scalars."""
    out: set[str] = set()
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set, frozenset)):
            out.update(str(v) for v in value if v not in (None, ""))
        elif value != "":
            out.add(str(value))
    return sorted(out)


def candidate_group_identity(status: str | None, structure_type: str | None, trace: dict,
                             claimed_program_ids, *, coarse: bool = False) -> dict:
    """The canonical, order-independent identity of the group a candidate belongs to.

    Every field is read from what the candidate already carries; nothing is inferred."""
    allocations = [a for a in (trace.get("component_allocations") or []) if isinstance(a, dict)]
    primary = trace.get("primary_jurisdiction") or trace.get("anchor_jurisdiction") or ""
    identity = {
        "candidate_status": status or "",
        "structure_type": structure_type or trace.get("structure_type") or "",
        "structural_family": trace.get("structural_family") or "",
        "reason_class": trace.get("rejection_reason_class") or "",
        "primary_jurisdiction": str(primary),
        "component_family": _strings(trace.get("component_types"), [a.get("component") for a in allocations]),
    }
    if coarse:
        identity["coarse"] = True
        identity["jurisdiction_codes"] = []
        identity["program_slugs"] = []
        identity["treaty_family"] = ""
    else:
        identity["jurisdiction_codes"] = _strings(
            trace.get("jurisdiction_codes"), trace.get("primary_jurisdiction"), trace.get("anchor_jurisdiction"),
            [a.get("jurisdiction_code") for a in allocations],
        )
        identity["program_slugs"] = _strings(
            trace.get("program_slugs"), trace.get("program_slug"), trace.get("anchor_program"), claimed_program_ids,
        )
        identity["treaty_family"] = str(trace.get("treaty_slug") or trace.get("treaty_or_framework_id") or "")
    return identity


def candidate_group_key(identity: dict) -> str:
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class _Group:
    __slots__ = ("ordinal", "identity", "count", "first_seq", "representative_z",
                 "min_npc", "max_npc", "min_inc", "max_inc", "best_identity", "best_key")

    def __init__(self, ordinal: int, identity: dict, first_seq: int, representative_z: bytes) -> None:
        self.ordinal = ordinal
        self.identity = identity
        self.count = 0
        self.first_seq = first_seq
        self.representative_z = representative_z
        self.min_npc = self.max_npc = self.min_inc = self.max_inc = None
        self.best_identity = None
        self.best_key = None


class CandidateAggregator:
    """Accumulates the exact aggregate groups of ONE evaluation. Holds one compressed representative per
    group (not per candidate), so memory follows the number of distinct groups (capped)."""

    def __init__(self, fine_group_cap: int | None = None) -> None:
        self._groups: dict[str, _Group] = {}
        self._fine_cap = FINE_GROUP_CAP if fine_group_cap is None else fine_group_cap
        self._fine_groups = 0
        self.total = 0
        self.priced_total = 0

    @property
    def group_count(self) -> int:
        return len(self._groups)

    def observe(self, seq: int, *, status: str, structure_type, trace: dict, warnings, structure,
                npc: float | None = None, incentive: float | None = None, identity: str | None = None) -> str:
        """Fold one candidate in. ``seq`` is its 1-based position in generation order. Returns the group key."""
        claimed = getattr(structure, "claimed_program_ids", None)
        ident = candidate_group_identity(status, structure_type, trace, claimed)
        key = candidate_group_key(ident)
        group = self._groups.get(key)
        if group is None:
            if self._fine_groups >= self._fine_cap:
                ident = candidate_group_identity(status, structure_type, trace, claimed, coarse=True)
                key = candidate_group_key(ident)
                group = self._groups.get(key)
            else:
                self._fine_groups += 1
        if group is None:
            representative = {
                "structure": {
                    "name": getattr(structure, "name", None),
                    "description": getattr(structure, "description", None),
                    "claimed_program_ids": claimed,
                    "jurisdiction_allocations": getattr(structure, "jurisdiction_allocations", None),
                },
                "structure_type": structure_type,
                "trace": trace,
                "warnings": warnings,
            }
            blob = zlib.compress(json.dumps(representative, separators=(",", ":"), default=str).encode("utf-8"), 1)
            group = self._groups[key] = _Group(len(self._groups) + 1, ident, seq, blob)
        group.count += 1
        self.total += 1
        if npc is not None:
            self.priced_total += 1
            group.min_npc = npc if group.min_npc is None else min(group.min_npc, npc)
            group.max_npc = npc if group.max_npc is None else max(group.max_npc, npc)
            candidate_key = (npc, identity or "")
            if group.best_key is None or candidate_key < group.best_key:
                group.best_key, group.best_identity = candidate_key, identity
        if incentive is not None:
            group.min_inc = incentive if group.min_inc is None else min(group.min_inc, incentive)
            group.max_inc = incentive if group.max_inc is None else max(group.max_inc, incentive)
        return key

    def counted(self) -> int:
        """Sum of every group's count, computed from the groups themselves (not from ``total``), so the
        writer can check the two independent tallies against each other."""
        return sum(g.count for g in self._groups.values())

    def rows(self, dominating_by_type: dict[str, Any] | None = None) -> Iterator[dict]:
        """One persistence row per group, in group_ordinal (first-seen) order. ``dominating_by_type`` maps a
        structure_type to the id of the RETAINED detailed row that dominates every PRICED member of that type."""
        dominating_by_type = dominating_by_type or {}
        for key, g in self._groups.items():
            ident = g.identity
            yield {
                "group_ordinal": g.ordinal,
                "group_key": key,
                "candidate_status": ident["candidate_status"],
                "structure_type": ident["structure_type"],
                "structural_family": ident["structural_family"] or None,
                "reason_class": ident["reason_class"] or None,
                "primary_jurisdiction": ident["primary_jurisdiction"] or None,
                "jurisdiction_codes": ident["jurisdiction_codes"],
                "program_slugs": ident["program_slugs"],
                "component_family": ident["component_family"],
                "treaty_family": ident["treaty_family"] or None,
                "candidate_count": g.count,
                "min_npc_usd": g.min_npc, "max_npc_usd": g.max_npc,
                "min_incentive_usd": g.min_inc, "max_incentive_usd": g.max_inc,
                "best_economic_identity": g.best_identity,
                "dominating_structure_id": (
                    dominating_by_type.get(ident["structure_type"]) if ident["candidate_status"] == PRICED_STATUS else None
                ),
                "first_candidate_seq": g.first_seq,
                "representative": json.loads(zlib.decompress(g.representative_z)),
            }

    def counts_by_status_family_reason(self) -> dict[tuple[str, str, str], int]:
        out: dict[tuple[str, str, str], int] = {}
        for g in self._groups.values():
            k = (g.identity["candidate_status"], g.identity["structure_type"], g.identity["reason_class"])
            out[k] = out.get(k, 0) + g.count
        return out
