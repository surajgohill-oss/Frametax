"""
canonical_publication_contract.py

Canonical authority substrate, Task 6 — the minimum publication/
completeness contract.

A deterministic/formulaic incentive is `EXECUTABLE_COMPLETE` only when
every dimension in `EXECUTABLE_COMPLETENESS_REQUIRED_DIMENSIONS` reports
PRESENT on the field-consolidation view (canonical_program_consolidation.py)
for that canonical program — the fields the served pricing pipeline
(discover_executable_jurisdictions -> derive_qualification_register ->
resolve_program_rate -> price_allocated_structure) actually consumes to
produce a defensible rate/QPE/NPC.

CRITICAL SEPARATION, enforced structurally, not just by convention:

    AUTHORITY_CLOSED != EXECUTABLE_COMPLETE

`AUTHORITY_CLOSED` is a research/validation-status label that exists only
in external validation artifacts (docs/validation/*.json) — this module
never imports, reads, or references any such artifact, any
authority_coverage_registry disposition string, or any other research-
status metadata. `executable_completeness()` is computed ENTIRELY from
`canonical_program_consolidation.consolidate()`, which itself reads only
the runtime registries the pricing pipeline actually calls
(program_rate_rules, program_spend_rules, global_inventory). A program can
therefore be labeled AUTHORITY_CLOSED in every external validation
document ever written and this contract will still, correctly and
independently, report NOT_EXECUTABLE_COMPLETE if its executable fields are
not actually present at the VERIFIED confidence tier the pricing pipeline
requires. There is no code path by which a research-closure label can
promote a program to executable-complete here.

Preserves authority_coverage_registry.py's existing PRICEABLE_VALIDATED /
UNPRICEABLE_AUTHORITY_INSUFFICIENT / etc. states untouched, for the same
reason: that registry is the existing, already-served ECONOMIC-CANDIDACY
veto (unchanged by this repair — see canonical_evaluation.py). This
contract is a SEPARATE, additional, read-only completeness classification
for the future authority-research phase; it does not replace, override, or
feed back into the existing veto.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from app.services.canonical_program_consolidation import PRESENT, ProgramConsolidation, consolidate
from app.services.canonical_program_identity import CanonicalProgramIdentity, resolve_identity

PUBLICATION_CONTRACT_VERSION = "authority-substrate-1.0.0"

EXECUTABLE_COMPLETE = "EXECUTABLE_COMPLETE"
NOT_EXECUTABLE_COMPLETE = "NOT_EXECUTABLE_COMPLETE"
UNKNOWN_PROGRAM = "UNKNOWN_PROGRAM"

#: The dimensions confirmed, by reading program_rate_rules.py's own
#: resolve_program_rate(), to be the TRUE hard blockers for this served
#: pipeline: a RateRule with an empty production_types tuple can never
#: match ANY production_type (`production_type not in rule.production_types`
#: is unconditionally True for an empty tuple), and no VERIFIED RateRule at
#: all means resolve_program_rate() returns None outright — either one
#: means canonical_evaluation.py._price_candidate() cannot produce a
#: pricing result for this program, for any production, ever.
#:
#: QPE_DEFINITION and TERRITORIALITY are deliberately NOT required here,
#: even though Task 4/5 still track and disclose them: derive_
#: qualification_register() never fails or blocks on their absence — the
#: canonical QPE rule ("an item is included unless authoritative program
#: language explicitly excludes it") and each program's own doctrine
#: (OPEN_DEFAULT_INCLUDE / CLOSED_POSITIVE_LIST / HYBRID_CONDITIONAL)
#: supply a defensible fallback either way. Proof: Greece's own accepted,
#: PRICEABLE_VALIDATED program has zero explicit category SpendRules
#: (QPE_DEFINITION=PARTIAL) and no territorial_only rule
#: (TERRITORIALITY=MISSING) today, and prices correctly in the live served
#: FVD/LU universe regardless — treating those as hard blockers here would
#: incorrectly fail this system's own already-accepted, already-working
#: economics. MINIMUM_SPEND and CAP are excluded for the same reason as
#: QPE_DEFINITION/TERRITORIALITY plus one more: many real programs
#: genuinely have neither, so their absence alone must never block
#: publication (that would be inventing a requirement no primary source
#: establishes).
EXECUTABLE_COMPLETENESS_REQUIRED_DIMENSIONS: tuple[str, ...] = (
    "RATE_OR_AWARD_BASIS",
    "ELIGIBLE_PRODUCTION_TYPE",
)


@dataclass(frozen=True)
class PublicationResult:
    canonical_program_id: str
    gate: str
    unresolved_required_dimensions: tuple[str, ...]

    @property
    def is_executable_complete(self) -> bool:
        return self.gate == EXECUTABLE_COMPLETE

    def as_dict(self) -> dict:
        return asdict(self)


def executable_completeness(canonical_program_id: str) -> PublicationResult:
    """The atomic publication gate for one canonical program. Reads ONLY
    canonical_program_consolidation.consolidate() — no research/validation
    artifact, no authority_coverage_registry disposition, no external
    "closed" label is consulted anywhere in this function."""
    identity: CanonicalProgramIdentity | None = resolve_identity(canonical_program_id)
    if identity is None:
        return PublicationResult(
            canonical_program_id=canonical_program_id,
            gate=UNKNOWN_PROGRAM,
            unresolved_required_dimensions=tuple(EXECUTABLE_COMPLETENESS_REQUIRED_DIMENSIONS),
        )
    consolidation: ProgramConsolidation = consolidate(identity.canonical_program_id)
    unresolved = tuple(
        dim for dim in EXECUTABLE_COMPLETENESS_REQUIRED_DIMENSIONS
        if consolidation.status_for(dim) != PRESENT
    )
    gate = EXECUTABLE_COMPLETE if not unresolved else NOT_EXECUTABLE_COMPLETE
    return PublicationResult(
        canonical_program_id=identity.canonical_program_id,
        gate=gate,
        unresolved_required_dimensions=unresolved,
    )
