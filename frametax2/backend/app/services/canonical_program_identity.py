"""
canonical_program_identity.py

Canonical authority substrate, Task 3 — the smallest identity substrate the
next authority-research phase needs (per the Codex authority-lineage
finding's required sequence: IDENTITY MANIFEST -> FIELD CONSOLIDATION ->
RESIDUAL-QUESTION LEDGER -> ATOMIC PUBLICATION CONTRACT -> TARGETED
RESEARCH). This module implements only the first step.

ONE stable canonical identity per incentive program, addressable regardless
of which existing registry (authority_coverage_registry,
jurisdiction_comparison, global_inventory, program_spend_rules,
program_rate_rules) a caller starts from.

This module assigns NO new economics and duplicates none — it is a pure
identity/lookup layer over EXISTING runtime data:

  - jurisdiction_comparison.ALL_PROFILES     (richly-profiled programs)
  - global_inventory.ALL_PROGRAMS            (catalog entries, some not yet
                                               promoted to a program_slug)
  - authority_coverage_registry.COVERAGE_REGISTRY (adjudicated rows)
  - authority_coverage_registry.CANONICAL_RUNTIME_SLUG_BINDINGS (known
                                               canonical-corpus-spelling
                                               aliases)
  - program_slug_aliases.PROGRAM_SLUG_ALIASES (known variant-slug aliases)

`canonical_program_id` / `canonical_slug` are the program's own existing,
already-stable `program_slug`. CineGlobe has never had two different
economic engines disagree about what a program_slug means, so inventing a
SEPARATE numbering scheme would only add a second identity to reconcile,
not remove one. What was actually missing (per the Codex lineage finding)
was a single ADDRESSABLE layer that resolves every known alias spelling to
that one slug and reports, for each, what the separate registries know —
that is Task 4 (field consolidation, canonical_program_consolidation.py),
built on top of this identity layer.

No authority data is migrated, researched, or changed. No existing
registry is deleted or modified.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.calculators import jurisdiction_comparison as _jc
from app.data import global_inventory as _gi
from app.data.authority_coverage_registry import (
    CANONICAL_RUNTIME_SLUG_BINDINGS,
    COVERAGE_REGISTRY,
    coverage_state,
)
from app.data.program_slug_aliases import PROGRAM_SLUG_ALIASES

CANONICAL_IDENTITY_VERSION = "authority-substrate-1.0.0"

STATE_CURRENT = "CURRENT"
STATE_SUPERSEDED = "SUPERSEDED"
STATE_DUPLICATE = "DUPLICATE"


@dataclass(frozen=True)
class CanonicalProgramIdentity:
    """One program's stable canonical identity. Never carries an economic
    value (rate, QPE, cap, etc.) — see canonical_program_consolidation.py
    for that."""

    canonical_program_id: str
    canonical_slug: str
    jurisdiction_code: str
    program_name: str
    program_type: str | None
    current_or_superseded_state: str
    aliases: tuple[str, ...] = field(default_factory=tuple)


def _known_slugs() -> set[str]:
    """Every program_slug any existing registry actually knows about.
    global_inventory entries with program_slug=None ("not yet promoted to
    the executable layer") are deliberately excluded — they have no stable
    executable identity to assign yet, and assigning one would be
    inventing an identity ahead of the promotion that hasn't happened."""
    slugs = set(COVERAGE_REGISTRY.keys())
    slugs.update(p.program_slug for p in _jc.ALL_PROFILES.values() if p.program_slug)
    slugs.update(p.program_slug for p in _gi.ALL_PROGRAMS if p.program_slug)
    return slugs


def _aliases_for(slug: str) -> tuple[str, ...]:
    aliases = {k for k, v in CANONICAL_RUNTIME_SLUG_BINDINGS.items() if v == slug}
    aliases.update(k for k, v in PROGRAM_SLUG_ALIASES.items() if v == slug)
    return tuple(sorted(aliases))


def _jurisdiction_name_type(slug: str) -> tuple[str | None, str | None, str | None]:
    """(jurisdiction_code, program_name, program_type), read from whichever
    existing registry knows this slug — jurisdiction_comparison first (the
    richest profile), then global_inventory, then the coverage registry's
    own bare jurisdiction/program_name fields. Never inferred, never
    defaulted to a guess."""
    for p in _jc.ALL_PROFILES.values():
        if p.program_slug == slug:
            return p.jurisdiction_code, p.program_name, p.incentive_type
    for p in _gi.ALL_PROGRAMS:
        if p.program_slug == slug:
            return p.jurisdiction_code, p.program_name, p.program_type
    row = COVERAGE_REGISTRY.get(slug)
    if row is not None:
        return None, row.program_name, None
    return None, None, None


def _state_for(slug: str) -> str:
    state = coverage_state(slug)
    if state == "SUPERSEDED":
        return STATE_SUPERSEDED
    if state == "DUPLICATE":
        return STATE_DUPLICATE
    return STATE_CURRENT


def resolve_identity(slug_or_alias: str) -> CanonicalProgramIdentity | None:
    """Resolve ANY known slug or alias spelling to its one canonical
    identity. Returns None only when the spelling is not known to any
    existing registry — never a fabricated identity."""
    slug = CANONICAL_RUNTIME_SLUG_BINDINGS.get(slug_or_alias, slug_or_alias)
    slug = PROGRAM_SLUG_ALIASES.get(slug, slug)
    if slug not in _known_slugs():
        return None
    jurisdiction_code, program_name, program_type = _jurisdiction_name_type(slug)
    return CanonicalProgramIdentity(
        canonical_program_id=slug,
        canonical_slug=slug,
        jurisdiction_code=jurisdiction_code or "",
        program_name=program_name or slug,
        program_type=program_type,
        current_or_superseded_state=_state_for(slug),
        aliases=_aliases_for(slug),
    )


def all_canonical_identities() -> tuple[CanonicalProgramIdentity, ...]:
    """Every DISTINCT canonical identity known to any existing registry,
    deduplicated by canonical_program_id — several raw slugs in
    `_known_slugs()` are themselves alias spellings that `resolve_identity()`
    maps to the SAME canonical program (e.g. both an old and current
    spelling of one program can independently appear as rows across the
    underlying registries); each canonical program must appear exactly
    once here. Deterministic order (sorted by canonical_program_id)."""
    seen: dict[str, CanonicalProgramIdentity] = {}
    for slug in sorted(_known_slugs()):
        identity = resolve_identity(slug)
        if identity is not None:
            seen.setdefault(identity.canonical_program_id, identity)
    return tuple(seen[cid] for cid in sorted(seen))
