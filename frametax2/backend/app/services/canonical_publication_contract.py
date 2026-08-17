"""
canonical_publication_contract.py

Authority completeness contract correction (commit 770006b follow-up),
CORRECTED by the Global Priceability Optimizer Restoration task per the
Codex optimizer-doctrine/priceability lineage trace (docs/validation/
CODEX_OPTIMIZER_DOCTRINE_PRICEABILITY_LINEAGE.json).

WHAT WAS WRONG (fixed in this pass): `priceability()` was a read-only
classifier over `canonical_program_consolidation.consolidate()`'s
VERIFIED-tier-gated dimensions — but that is NOT what actually determines
whether the served engine (`production_discovery.discover_executable_
jurisdictions()` / `canonical_evaluation._price_candidate()`) will price a
program. The served engine never reads consolidation or confidence tiers
at all; it checks, in order: (1) `authority_coverage_registry.
blocks_economic_candidacy()`, (2) whether a doctrine resolves
(`program_spend_rules.resolve_program_doctrine()`), (3) whether at least
one `RateRule` exists (`program_rate_rules.get_rate_rules()`, ANY
confidence tier — PARSED/DISCOVERY included), and (4) whether at least one
of those rules carries an eligible production type. Across the 126
formulaic programs this produced 27 false negatives (served-priceable
programs the old classifier called UNPRICEABLE because their real,
executable RateRules were PARSED/DISCOVERY tier, not VERIFIED) and one
false positive (`us_ga_film_credit`, which the OLD classifier called
PRICEABLE while the served coverage-registry veto — since corrected, see
authority_coverage_registry.py — actually blocked it).

THE FIX: `priceability()` now delegates to the SAME four predicates the
served engine calls, not a separately-maintained approximation. This is
the "one coherent semantic contract for PRICEABLE" the restoration task
required — the publication label and the served runtime can no longer
structurally disagree, because they read the same functions. `priceability
()` intentionally does NOT call `resolve_program_rate()` itself (that
needs a real project's production_type/QPE, which this program-level,
project-independent function does not have) — it answers the
project-independent question Codex calls "intrinsic priceability": would
SOME real project stand a chance of pricing here, before any
project-specific threshold/type mismatch is even evaluated. A specific
project can still receive `RULE_REJECTED` downstream for real
type/minimum-QPE conditions this function cannot see.

This module still answers TWO permanently independent questions, never
conflated:

    1. `priceability()`      — RUNTIME PRICEABILITY. Can the EXISTING
                                pricing engine currently produce a
                                defensible economic calculation for this
                                program, independent of any one project?
                                Gated on the same coverage/doctrine/rate/
                                eligible-type predicates the served engine
                                itself calls — see THE FIX above.

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
#: Retained ONLY as PriceabilityResult.unresolved_required_dimensions'
#: legacy shape for callers that still read that field name — the actual
#: gating logic no longer consults canonical_program_consolidation at all
#: (see THE FIX in the module docstring). Do not extend this tuple; it is
#: a display label set, not a real requirement list any more.
PRICEABILITY_REQUIRED_DIMENSIONS: tuple[str, ...] = (
    "RATE_OR_AWARD_BASIS",
    "ELIGIBLE_PRODUCTION_TYPE",
)

#: The exact first-blocker classification vocabulary Codex's optimizer
#: lineage trace uses (formulaic_program_first_blocker in
#: CODEX_OPTIMIZER_DOCTRINE_PRICEABILITY_LINEAGE.json) — surfaced here so
#: a caller can distinguish WHY a program is UNPRICEABLE without a second
#: lookup. `None` when PRICEABLE.
COVERAGE_REGISTRY_VETO = "COVERAGE_REGISTRY_VETO"
NO_DOCTRINE_RESOLVES = "NO_DOCTRINE_RESOLVES"
NO_RATE_RULES = "NO_RATE_RULES"
NO_ELIGIBLE_PRODUCTION_TYPE = "NO_ELIGIBLE_PRODUCTION_TYPE"


@dataclass(frozen=True)
class PriceabilityResult:
    canonical_program_id: str
    gate: str
    unresolved_required_dimensions: tuple[str, ...]
    blocker: str | None = None

    @property
    def is_priceable(self) -> bool:
        return self.gate == PRICEABLE

    def as_dict(self) -> dict:
        return asdict(self)


def priceability(canonical_program_id: str) -> PriceabilityResult:
    """Runtime priceability only: would the EXISTING served engine
    (production_discovery.discover_executable_jurisdictions() /
    canonical_evaluation._price_candidate()) stand a chance of pricing
    this program for SOME project, before any project-specific type/
    threshold condition is evaluated? Delegates to the exact same four
    predicates the served engine itself calls — see THE FIX in this
    module's docstring for why this replaced the old VERIFIED-tier
    consolidation-based classifier. Never a statement about authority
    completeness — see authority_completeness() below for that separate,
    permanently independent question."""
    from app.data.authority_coverage_registry import blocks_economic_candidacy
    from app.data.program_rate_rules import get_rate_rules
    from app.data.program_spend_rules import resolve_program_doctrine

    identity: CanonicalProgramIdentity | None = resolve_identity(canonical_program_id)
    if identity is None:
        return PriceabilityResult(
            canonical_program_id=canonical_program_id,
            gate=UNKNOWN_PROGRAM,
            unresolved_required_dimensions=tuple(PRICEABILITY_REQUIRED_DIMENSIONS),
            blocker=None,
        )
    slug = identity.canonical_program_id

    if blocks_economic_candidacy(slug):
        return PriceabilityResult(
            canonical_program_id=slug, gate=UNPRICEABLE,
            unresolved_required_dimensions=tuple(PRICEABILITY_REQUIRED_DIMENSIONS),
            blocker=COVERAGE_REGISTRY_VETO,
        )
    if resolve_program_doctrine(slug) is None:
        return PriceabilityResult(
            canonical_program_id=slug, gate=UNPRICEABLE,
            unresolved_required_dimensions=("RATE_OR_AWARD_BASIS",),
            blocker=NO_DOCTRINE_RESOLVES,
        )
    rate_rules = get_rate_rules(slug)
    if not rate_rules:
        return PriceabilityResult(
            canonical_program_id=slug, gate=UNPRICEABLE,
            unresolved_required_dimensions=("RATE_OR_AWARD_BASIS",),
            blocker=NO_RATE_RULES,
        )
    if not any(r.production_types for r in rate_rules):
        return PriceabilityResult(
            canonical_program_id=slug, gate=UNPRICEABLE,
            unresolved_required_dimensions=("ELIGIBLE_PRODUCTION_TYPE",),
            blocker=NO_ELIGIBLE_PRODUCTION_TYPE,
        )
    return PriceabilityResult(
        canonical_program_id=slug, gate=PRICEABLE,
        unresolved_required_dimensions=(), blocker=None,
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
