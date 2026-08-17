"""
canonical_publication_contract.py

Authority completeness contract correction (commit 770006b follow-up).

This module now answers TWO permanently independent questions, never
conflated:

    1. `priceability()`      — RUNTIME PRICEABILITY. Can the EXISTING
                                pricing engine currently produce a
                                defensible economic calculation for this
                                program? Gated on exactly the two
                                dimensions confirmed, by reading
                                program_rate_rules.py's own
                                resolve_program_rate(), to be true hard
                                blockers for THIS implementation.

    2. `authority_completeness()` — AUTHORITY COMPLETENESS. Has the
                                governing incentive authority actually been
                                resolved across ALL material program
                                dimensions? Gated on all 14 tracked
                                dimensions, using
                                canonical_program_consolidation.
                                RESOLVED_FOR_AUTHORITY_COMPLETENESS.

A program MAY legitimately be PRICEABLE and AUTHORITY_INCOMPLETE at the
same time — that is not a contradiction, it is the expected, common case.
CineGlobe's canonical QPE doctrine (every budget line is included unless
authoritative program language explicitly excludes it) lets the pricing
engine produce a number from a DOCTRINE FALLBACK even when most of a
program's authority dimensions were never actually reviewed — DEFAULT
INCLUSION IS NOT THE SAME THING AS AUTHORITY COMPLETENESS. The previous
version of this module (`EXECUTABLE_COMPLETE`) answered only question 1
and left question 2 unaddressed — this correction adds question 2 as a
genuinely separate contract rather than repurposing the old name to mean
something it never computed.

CRITICAL SEPARATION, enforced structurally, not just by convention:

    AUTHORITY_CLOSED != AUTHORITY_COMPLETE

`AUTHORITY_CLOSED` is a research/validation-status label that exists only
in external validation artifacts (docs/validation/*.json) — this module
never imports, reads, or references any such artifact, any
authority_coverage_registry disposition string, or any other research-
status metadata. Both `priceability()` and `authority_completeness()` are
computed ENTIRELY from `canonical_program_consolidation.consolidate()`,
which itself reads only the runtime registries the pricing pipeline
actually calls. A program can therefore be labeled AUTHORITY_CLOSED in
every external validation document ever written and this module will
still, correctly and independently, report AUTHORITY_INCOMPLETE if its
material dimensions are not actually resolved. There is no code path by
which a research-closure label can promote a program to complete here.

Preserves authority_coverage_registry.py's existing PRICEABLE_VALIDATED /
UNPRICEABLE_AUTHORITY_INSUFFICIENT / etc. states untouched — that registry
is the existing, already-served ECONOMIC-CANDIDACY veto (unchanged by this
correction — see canonical_evaluation.py). This module is a SEPARATE,
additional, read-only classification layer; it does not replace, override,
or feed back into the existing veto, and it changes no pricing/discovery
behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from app.services.canonical_program_consolidation import (
    PRESENT,
    REQUIRED_DIMENSIONS,
    RESOLVED_FOR_AUTHORITY_COMPLETENESS,
    ProgramConsolidation,
    consolidate,
)
from app.services.canonical_program_identity import CanonicalProgramIdentity, resolve_identity

PUBLICATION_CONTRACT_VERSION = "authority-substrate-1.1.0"

UNKNOWN_PROGRAM = "UNKNOWN_PROGRAM"

# ── 1. Runtime priceability (unchanged logic; renamed for clarity) ─────────

PRICEABLE = "PRICEABLE"
UNPRICEABLE = "UNPRICEABLE"

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
#: even though the consolidation view still tracks and discloses them:
#: derive_qualification_register() never fails or blocks on their absence
#: — the canonical QPE rule ("an item is included unless authoritative
#: program language explicitly excludes it") and each program's own
#: doctrine (OPEN_DEFAULT_INCLUDE / CLOSED_POSITIVE_LIST /
#: HYBRID_CONDITIONAL) supply a defensible fallback either way. Proof:
#: Greece's own accepted, PRICEABLE_VALIDATED program has zero explicit
#: category SpendRules (QPE_DEFINITION=PARTIAL) and no territorial_only
#: rule (TERRITORIALITY=MISSING) today, and prices correctly in the live
#: served FVD/LU universe regardless. This is EXACTLY the "default
#: inclusion is not authority completeness" distinction this correction
#: exists to enforce: Greece is PRICEABLE via that fallback, and — see
#: authority_completeness() below — separately, correctly,
#: AUTHORITY_INCOMPLETE, because most of its 14 material dimensions were
#: never actually resolved by primary-source review.
PRICEABILITY_REQUIRED_DIMENSIONS: tuple[str, ...] = (
    "RATE_OR_AWARD_BASIS",
    "ELIGIBLE_PRODUCTION_TYPE",
)


@dataclass(frozen=True)
class PriceabilityResult:
    canonical_program_id: str
    gate: str
    unresolved_required_dimensions: tuple[str, ...]

    @property
    def is_priceable(self) -> bool:
        return self.gate == PRICEABLE

    def as_dict(self) -> dict:
        return asdict(self)


def priceability(canonical_program_id: str) -> PriceabilityResult:
    """Runtime priceability only: can the EXISTING engine currently price
    this program? Never a statement about authority completeness — see
    authority_completeness() below for that separate question."""
    identity: CanonicalProgramIdentity | None = resolve_identity(canonical_program_id)
    if identity is None:
        return PriceabilityResult(
            canonical_program_id=canonical_program_id,
            gate=UNKNOWN_PROGRAM,
            unresolved_required_dimensions=tuple(PRICEABILITY_REQUIRED_DIMENSIONS),
        )
    consolidation: ProgramConsolidation = consolidate(identity.canonical_program_id)
    unresolved = tuple(
        dim for dim in PRICEABILITY_REQUIRED_DIMENSIONS
        if consolidation.status_for(dim) != PRESENT
    )
    gate = PRICEABLE if not unresolved else UNPRICEABLE
    return PriceabilityResult(
        canonical_program_id=identity.canonical_program_id,
        gate=gate,
        unresolved_required_dimensions=unresolved,
    )


# ── 2. Authority completeness (new — the actual correction) ────────────────

AUTHORITY_COMPLETE = "AUTHORITY_COMPLETE"
AUTHORITY_INCOMPLETE = "AUTHORITY_INCOMPLETE"


@dataclass(frozen=True)
class AuthorityCompletenessResult:
    canonical_program_id: str
    gate: str
    unresolved_material_dimensions: tuple[str, ...]

    @property
    def is_authority_complete(self) -> bool:
        return self.gate == AUTHORITY_COMPLETE

    def as_dict(self) -> dict:
        return asdict(self)


def authority_completeness(canonical_program_id: str) -> AuthorityCompletenessResult:
    """Whether the governing incentive authority has actually been
    resolved across ALL material dimensions (REQUIRED_DIMENSIONS, all 14)
    — independent of whether the current engine can already price the
    program via a doctrine fallback. A dimension resolves this gate only
    when its consolidation status is PRESENT, NOT_APPLICABLE, or
    AUTHORITATIVE_SILENCE_CONFIRMED (see canonical_program_consolidation.
    RESOLVED_FOR_AUTHORITY_COMPLETENESS) — PARTIAL/MISSING/CONFLICT always
    leave the program AUTHORITY_INCOMPLETE, regardless of priceability.

    Reads ONLY canonical_program_consolidation.consolidate() — no
    research/validation artifact, no authority_coverage_registry
    disposition, no external "closed" label is consulted anywhere in this
    function."""
    identity: CanonicalProgramIdentity | None = resolve_identity(canonical_program_id)
    if identity is None:
        return AuthorityCompletenessResult(
            canonical_program_id=canonical_program_id,
            gate=UNKNOWN_PROGRAM,
            unresolved_material_dimensions=tuple(REQUIRED_DIMENSIONS),
        )
    consolidation: ProgramConsolidation = consolidate(identity.canonical_program_id)
    unresolved = tuple(
        dim for dim in REQUIRED_DIMENSIONS
        if consolidation.status_for(dim) not in RESOLVED_FOR_AUTHORITY_COMPLETENESS
    )
    gate = AUTHORITY_COMPLETE if not unresolved else AUTHORITY_INCOMPLETE
    return AuthorityCompletenessResult(
        canonical_program_id=identity.canonical_program_id,
        gate=gate,
        unresolved_material_dimensions=unresolved,
    )
