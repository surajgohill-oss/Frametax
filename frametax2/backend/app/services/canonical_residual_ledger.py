"""
canonical_residual_ledger.py

Canonical authority substrate, Task 5 — a deterministic residual-question
ledger derived from the field-consolidation view
(canonical_program_consolidation.py).

For every canonical program whose consolidation is not fully PRESENT on
every required dimension, this module states EXACTLY which executable
dimensions remain unresolved and why (each dimension's own `source`
string, verbatim). This becomes the future targeted-research backlog Codex
asked for — it does not answer any question itself, and it performs no
research.

The ledger exists specifically so that no external disposition label
(AUTHORITY_CLOSED, STALE, CORRECT, ...) can conceal an incomplete
executable field again: it is generated purely from the consolidation
view, which itself reads only runtime pricing-relevant registries — never
any research/validation-status metadata. See canonical_publication_contract.py
(Task 6) for the enforcement half of that same separation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from app.services.canonical_program_consolidation import (
    REQUIRED_DIMENSIONS,
    UNRESOLVED_FOR_AUTHORITY_COMPLETENESS,
    ProgramConsolidation,
    consolidate,
)
from app.services.canonical_program_identity import CanonicalProgramIdentity, resolve_identity

RESIDUAL_LEDGER_VERSION = "authority-substrate-1.1.0"

#: A dimension counts as a residual question whenever authority
#: completeness has not actually resolved it — PARTIAL (a real but
#: non-executable signal exists), MISSING (nothing captured), or CONFLICT
#: (two registries disagree). PRESENT, NOT_APPLICABLE, and
#: AUTHORITATIVE_SILENCE_CONFIRMED are the only genuinely closed states.
#: Reuses canonical_program_consolidation's own classification so the
#: ledger and the authority_completeness() publication gate can never
#: silently drift apart.
_UNRESOLVED_STATUSES = UNRESOLVED_FOR_AUTHORITY_COMPLETENESS


@dataclass(frozen=True)
class ResidualQuestion:
    dimension: str
    status: str
    detail: str


@dataclass(frozen=True)
class ProgramResidualLedgerEntry:
    canonical_program_id: str
    jurisdiction_code: str
    program_name: str
    residual_questions: tuple[ResidualQuestion, ...]

    @property
    def is_fully_resolved(self) -> bool:
        return not self.residual_questions

    def as_dict(self) -> dict:
        return {
            "canonical_program_id": self.canonical_program_id,
            "jurisdiction_code": self.jurisdiction_code,
            "program_name": self.program_name,
            "residual_questions": [asdict(q) for q in self.residual_questions],
        }


def residual_questions_for(consolidation: ProgramConsolidation) -> tuple[ResidualQuestion, ...]:
    """The deterministic residual-question list for one consolidation —
    one entry per REQUIRED_DIMENSIONS status that is not PRESENT."""
    out = []
    for dim in REQUIRED_DIMENSIONS:
        status = consolidation.status_for(dim)
        if status in _UNRESOLVED_STATUSES:
            state = next(d for d in consolidation.dimensions if d.dimension == dim)
            out.append(ResidualQuestion(dimension=dim, status=status, detail=state.source))
    return tuple(out)


def ledger_entry_for(canonical_program_id: str) -> ProgramResidualLedgerEntry | None:
    identity: CanonicalProgramIdentity | None = resolve_identity(canonical_program_id)
    if identity is None:
        return None
    consolidation = consolidate(identity.canonical_program_id)
    return ProgramResidualLedgerEntry(
        canonical_program_id=identity.canonical_program_id,
        jurisdiction_code=identity.jurisdiction_code,
        program_name=identity.program_name,
        residual_questions=residual_questions_for(consolidation),
    )


def full_residual_ledger(canonical_program_ids: list[str]) -> tuple[ProgramResidualLedgerEntry, ...]:
    """The ledger for an explicit list of programs — callers supply the
    scope (e.g. the P0 authority-gap set already established by Codex);
    this module invents no new program list of its own."""
    entries = []
    for pid in canonical_program_ids:
        entry = ledger_entry_for(pid)
        if entry is not None:
            entries.append(entry)
    return tuple(entries)
