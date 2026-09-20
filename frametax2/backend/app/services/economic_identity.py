"""
Canonical economic identity of a persisted evaluation candidate.

Why this exists
---------------
Every candidate evaluate_project() persists gets a fresh random ``uuid4`` as its
ProductionStructure id, so ``structure_id`` is different in every generation of
the SAME economics. Anything ordered or paginated by it (equal-NPC ties in the
ranking, a cursor over the rejection universe) is therefore not reproducible
across regenerations. ``canonical_economic_identity`` is the stable replacement:
a SHA-256 over the routing/program/treaty fields that DEFINE the candidate, and
nothing that is per-run (no ids, no timestamps, no amounts, no display name --
the display name lists components in search-traversal order, which is
deterministic but not canonical).

The same function is written to ``structure_calculation_results.economic_identity``
by evaluate_project()'s bulk writer at persistence time, and a frozen copy of it
backfills historical rows in migration 0077. tests/test_economic_identity.py
pins that the two agree and that the identity is invariant under list/routing
order and sensitive to every routing dimension.

It is deliberately status-independent: the same routing is the same economic
structure whether it was priced or rejected; the disposition is a separate,
first-class ordering key alongside it.
"""
from __future__ import annotations

import hashlib

_SEP = "\x1f"


def _s(value) -> str:
    return "" if value is None else str(value)


def _sorted_list(value) -> str:
    if not isinstance(value, (list, tuple)):
        return ""
    return ",".join(sorted(_s(item) for item in value))


def canonical_economic_identity(structure_type: str | None, trace: dict | None) -> str:
    t = trace or {}
    routing = ";".join(sorted(
        f"{_s(c.get('component'))}>{_s(c.get('jurisdiction_code'))}/{_s(c.get('program_slug'))}"
        for c in (t.get("component_allocations") or [])
        if isinstance(c, dict)
    ))
    partners = ",".join(sorted(
        _s(p.get("jurisdiction_code"))
        for p in (t.get("coproduction_partners") or [])
        if isinstance(p, dict)
    ))
    parts = [
        _s(structure_type),
        _s(t.get("structural_family") or t.get("discovery_classification")),
        _s(t.get("anchor_jurisdiction")),
        _s(t.get("anchor_program")),
        _s(t.get("primary_jurisdiction")),
        _s(t.get("program_slug")),
        _sorted_list(t.get("program_slugs")),
        _sorted_list(t.get("jurisdiction_codes")),
        _sorted_list(t.get("component_subset")),
        _sorted_list(t.get("component_types")),
        routing,
        _s(t.get("treaty_slug") or t.get("treaty_or_framework_id")),
        partners,
        _s(t.get("structural_generator_structure_id")),
    ]
    return hashlib.sha256(_SEP.join(parts).encode("utf-8")).hexdigest()


def candidate_status_of(trace: dict | None) -> str:
    """The disposition, as the empty string when a trace carries none (the
    denormalized column is NOT NULL so keyset comparisons never see a NULL)."""
    return _s((trace or {}).get("candidate_status"))


def rejection_reason_class_of(trace: dict | None) -> str:
    return _s((trace or {}).get("rejection_reason_class"))
