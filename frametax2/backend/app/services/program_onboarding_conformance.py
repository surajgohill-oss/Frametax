"""
program_onboarding_conformance.py

Final non-Globe canonical core closeout, Item C (2026-09-04).

The task: a verified new program that uses an EXISTING economic mechanic
should enter the optimizer

    CANONICAL PROGRAM RECORD + AUTHORITY/RULES
    -> CONFORMANCE -> ELIGIBILITY -> STRUCTURE CAPABILITY -> ALLOCATION
    -> QPE -> ECONOMIC MECHANIC -> CANONICAL SCENARIO
    -> SELECTION / OPTIMIZER CONSUMPTION

WITHOUT requiring bespoke edits to allocation_pricing.py, canonical
served API wiring, ranking, Overview, Workspace, or Reports.

This module does NOT re-implement any stage of that pipeline. Every
stage already IS generic, keyed only by program_slug, in the files that
already exist:

  CANONICAL PROGRAM RECORD  app.data.program_requirements.get_program_requirements
  DOCTRINE RECORD           app.data.executable_jurisdiction_registry.get_doctrine
  ECONOMIC MECHANIC         app.data.program_rate_rules.get_rate_rules /
                             resolve_program_rate — generic RateRule resolution,
                             no per-program branch.
  AUTHORITY / PROVENANCE    app.data.program_authority_provenance.classify_program_provenance
  QPE DOCTRINE               app.data.program_spend_rules.resolve_program_doctrine —
                             NEVER returns None; a program with no explicit
                             classification resolves under the canonical
                             default-inclusion rule automatically.
  ELIGIBILITY GATES          app.calculators.canonical_requirements_gate_bridge
                             .evaluate_requirements_gate — reads the profile's
                             own eligibility fields generically; enforced for
                             EVERY program by allocation_pricing.py (P0-1),
                             never opted in per program.
  DISCRETIONARY/CERTAINTY    app.services.canonical_evaluation
                             ._is_discretionary_program / _competitive_
                             allocation_disclosure — read allocation_type
                             generically; a program with no allocation_type
                             set is treated as an ordinary deterministic
                             entitlement automatically (no registration
                             needed).
  PROJECT MODELING POLICY    app.services.canonical_evaluation Item B —
                             applies to ANY program with allocation_type ==
                             DISCRETIONARY automatically.
  STRUCTURE CAPABILITY       app.calculators.structure_compatibility — keyed
                             by structure_type, not by program_slug.
  CANONICAL SCENARIO /
  SELECTION                  app.services.canonical_production_view — fully
                             generic; Item A's canonical_selected_structure_id
                             applies to every served structure regardless of
                             program.

What THIS module adds is the missing piece: a single, executable
CLASSIFICATION over that already-generic pipeline, so a program can be
told CONFORMANT / CONDITIONAL / NONCONFORMANT before it is trusted in
optimizer output — never a silent admission, and never a per-program
hardcoded allow-list. A brand-new program_slug that registers a RateRule
(and, ideally, a ProgramRequirementsProfile) is classified automatically
the next time this runs, with ZERO code change to this module or to any
of the files listed above.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CONFORMANT = "CONFORMANT"
CONDITIONAL = "CONDITIONAL"
NONCONFORMANT = "NONCONFORMANT"
#: Optimizer FINAL closeout, P1-CONF-001 (Codex, full optimizer audit):
#: a program that is genuinely, deliberately never register()-ed into
#: ordinary jurisdiction discovery (no doctrine, no
#: ProgramRequirementsProfile) but DOES carry a real, cited, executable
#: RateRule for a specific conditional/treaty pricing pathway. This is
#: not a data-quality gap (NONCONFORMANT would misrepresent it as one)
#: and it is not an ordinary program (CONFORMANT would misrepresent it
#: as always independently priceable). See `classify_program_conformance`
#: for the exact, generic, non-hardcoded detection rule.
PATHWAY_SPECIFIC = "PATHWAY_SPECIFIC"


@dataclass(frozen=True)
class ProgramConformanceResult:
    program_slug: str
    classification: str  # CONFORMANT | CONDITIONAL | NONCONFORMANT
    jurisdiction_code: str | None
    #: Minimum assertions from the closeout brief, each True/False/None
    #: (None = not applicable / structurally guaranteed by the generic
    #: engine rather than checked per-program here — see the module
    #: docstring for which stages are structural-always-true by
    #: construction vs. genuinely per-program-variable).
    assertions: dict[str, bool | None] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


def _valid_jurisdiction_code(code: str | None, known_jurisdiction_codes: frozenset[str] | None) -> bool:
    """A jurisdiction code is valid if it is non-empty AND, when a real
    set of known codes is supplied (from the live Jurisdiction table),
    either appears there directly OR is one of the documented special-
    cased subnational/administrative codes this engine already resolves
    outside the Jurisdiction table (see canonical_program_identity.
    canonical_jurisdiction_name — AE-AD, AE-DXB, AU-SA, US-* state codes,
    etc. all follow the same two-letter-country-dash-suffix shape)."""
    if not code:
        return False
    if known_jurisdiction_codes is None:
        return True  # format-only check when no DB session is available
    if code in known_jurisdiction_codes:
        return True
    # Subnational/administrative codes follow COUNTRY-SUFFIX (e.g.
    # AE-DXB, US-CA, AU-NSW) — the country prefix being known is real
    # evidence of a resolvable jurisdiction even when the exact
    # subnational row isn't separately seeded.
    if "-" in code:
        country_prefix = code.split("-", 1)[0]
        return country_prefix in known_jurisdiction_codes
    return False


def classify_program_conformance(
    program_slug: str,
    known_jurisdiction_codes: frozenset[str] | None = None,
) -> ProgramConformanceResult:
    """The one executable classification for a single program_slug. Pure
    function over the existing registries — no DB write, no pricing run.
    `known_jurisdiction_codes` is optional (pass the live Jurisdiction
    table's codes for a real DB-backed jurisdiction check; omit for a
    format-only check, e.g. in a unit test with no database)."""
    from app.data.executable_jurisdiction_registry import get_doctrine
    from app.data.program_authority_provenance import classify_program_provenance
    from app.data.program_rate_rules import get_rate_rules
    from app.data.program_requirements import get_program_requirements
    from app.data.program_spend_rules import resolve_program_doctrine

    reasons: list[str] = []
    assertions: dict[str, bool | None] = {}

    # ── 1. Canonical program record ────────────────────────────────────
    profile = get_program_requirements(program_slug)
    doctrine = get_doctrine(program_slug)
    assertions["unique_canonical_program_id"] = bool(program_slug and program_slug.strip())

    # ── 3 (moved ahead of 2 — needed to detect pathway-specific status
    # before jurisdiction resolution). Economic mechanic supported ──────
    rate_rules = get_rate_rules(program_slug)
    has_rate_rules = bool(rate_rules)
    assertions["economic_mechanic_supported"] = has_rate_rules
    if not has_rate_rules:
        reasons.append("no registered RateRule — program cannot be priced/executed at all")

    # Optimizer FINAL closeout, P1-CONF-001 (Codex): a program with a real,
    # executable RateRule but NEITHER a doctrine record NOR a
    # ProgramRequirementsProfile has no ordinary-discovery identity at
    # all — never a data-quality accident here, since every such RateRule
    # is only ever materialized deliberately for a specific conditional/
    # treaty pricing pathway (see program_rate_rules_worldwide.py's own
    # module comment for the confirmed real case, au_producer_offset:
    # "deliberately not register()-ed into ordinary jurisdiction
    # discovery... Materialized as an executable RateRule ONLY for the
    # conditional official-co-production pricing path"). This is a
    # purely structural signal — no program_slug is referenced by name —
    # so a future program with the same real shape is classified
    # identically with zero code change here.
    is_pathway_specific = has_rate_rules and doctrine is None and profile is None
    assertions["pathway_specific_executable"] = is_pathway_specific

    # ── 2. Valid jurisdiction ───────────────────────────────────────────
    jurisdiction_code = (
        doctrine.jurisdiction_code if doctrine is not None
        else (profile.jurisdiction_code if profile is not None else None)
    )
    if jurisdiction_code is None and is_pathway_specific:
        # The real jurisdiction is already known, cited canonical
        # knowledge (national_cultural_status.py's own
        # _CONFIRMED_SEPARATE_PATHWAY record) — it was simply never
        # reachable through the ordinary doctrine/profile path because
        # this program was deliberately excluded from that path.
        from app.data.national_cultural_status import get_jurisdiction_code_for_linked_program
        jurisdiction_code = get_jurisdiction_code_for_linked_program(program_slug)
    valid_jurisdiction = _valid_jurisdiction_code(jurisdiction_code, known_jurisdiction_codes)
    assertions["valid_jurisdiction"] = valid_jurisdiction
    if not valid_jurisdiction:
        reasons.append(f"jurisdiction_code={jurisdiction_code!r} is missing or unresolvable")

    # ── 4. Authoritative provenance present ─────────────────────────────
    provenance_summary = classify_program_provenance(program_slug)
    has_provenance = provenance_summary is not None
    provenance_complete = bool(has_provenance and not provenance_summary.residual_tier_ids)
    assertions["authoritative_provenance_present"] = has_provenance
    assertions["authoritative_provenance_complete"] = provenance_complete if has_provenance else None
    if has_provenance and not provenance_complete:
        reasons.append(
            f"provenance is PARTIAL — {len(provenance_summary.residual_tier_ids)} rate tier(s) "
            "still lack a structured SourceProvenance object (citation/source_ref text is present; "
            "only the structured index is missing)"
        )
    elif not has_provenance:
        reasons.append("no provenance record at all — implies no rate rules either")

    # ── 5. Eligibility gates represented ────────────────────────────────
    eligibility_fields = (
        "local_entity_required", "local_coproducer_required",
        "treaty_or_official_coproduction_required", "cultural_test_required",
        "min_total_budget_usd", "min_local_spend_usd",
    )
    has_eligibility_signal = bool(profile is not None and any(
        getattr(profile, f, None) is not None for f in eligibility_fields
    ))
    assertions["eligibility_gates_represented"] = has_eligibility_signal if profile is not None else None
    if profile is None:
        reasons.append(
            "no ProgramRequirementsProfile — eligibility gates are represented only by "
            "structural defaults (canonical_requirements_gate_bridge never fails a program "
            "into PRICED without a real check, but no PROGRAM-SPECIFIC eligibility fact is on file)"
        )
    elif not has_eligibility_signal:
        reasons.append("ProgramRequirementsProfile exists but has zero eligibility fields set")

    # ── 6. QPE doctrine available — structurally ALWAYS true; the
    # canonical default-inclusion rule means resolve_program_doctrine()
    # never returns None. Reported for visibility, never a fail cause.
    doctrine_resolution = resolve_program_doctrine(program_slug)
    assertions["qpe_doctrine_available"] = True
    assertions["qpe_doctrine_is_explicit"] = doctrine_resolution.is_explicit

    # ── 7-10. Structurally guaranteed by the generic engine for EVERY
    # program with no per-program registration required — see module
    # docstring. Reported as None (not applicable to per-program
    # classification) rather than fabricated True, but these are the
    # exact stages the "without bespoke edits" requirement is about.
    assertions["mandatory_failed_cannot_price"] = None       # engine-level (P0-1), structural
    assertions["certainty_vs_potential_separated"] = None    # engine-level (Section 5), structural
    assertions["policy_behavior_represented"] = None         # engine-level (Item B), structural
    assertions["structure_capabilities_explicit"] = None     # engine-level, structure_type-keyed
    assertions["serialization_valid"] = None                 # engine-level, canonical_production_view
    assertions["canonical_scenario_compatibility_valid"] = None  # engine-level, same pipeline

    # ── 11. Optimizer relevance explicit ────────────────────────────────
    try:
        from app.data.authority_coverage_registry import get_coverage_status
        coverage = get_coverage_status(program_slug)
    except Exception:  # pragma: no cover - import cycle safety
        coverage = None
    assertions["optimizer_relevance_explicit"] = coverage is not None

    # ── Overall classification ──────────────────────────────────────────
    # Optimizer FINAL closeout, P1-CONF-001: a pathway-specific program is
    # classified in its OWN coherent branch, checked before the ordinary
    # NONCONFORMANT test — its missing doctrine/profile is the deliberate,
    # documented design (see `is_pathway_specific` above), never a real
    # data gap, so it must never fall into NONCONFORMANT merely because
    # `profile is None` also happens to be true of it. A pathway-specific
    # program whose real jurisdiction still can't be resolved (no
    # `_CONFIRMED_SEPARATE_PATHWAY` record either) remains NONCONFORMANT —
    # this branch only reclassifies the case that IS coherently resolved.
    if is_pathway_specific and valid_jurisdiction:
        classification = PATHWAY_SPECIFIC
        reasons.append(
            "no ordinary doctrine/ProgramRequirementsProfile record exists BY DESIGN — this "
            "program is executable ONLY through a specific conditional/treaty pricing pathway "
            "(never ordinary single/full_relocation discovery); see program_rate_rules_worldwide.py's "
            "own module comment for the confirmed real case and reasoning"
        )
    elif not has_rate_rules or not valid_jurisdiction:
        classification = NONCONFORMANT
    elif not has_provenance or not provenance_complete or profile is None or not has_eligibility_signal:
        classification = CONDITIONAL
    else:
        classification = CONFORMANT

    return ProgramConformanceResult(
        program_slug=program_slug,
        classification=classification,
        jurisdiction_code=jurisdiction_code,
        assertions=assertions,
        reasons=tuple(reasons),
    )


def all_optimizer_visible_program_slugs() -> tuple[str, ...]:
    """Every program_slug this engine could ever generate a candidate
    for — the real, structural definition of "optimizer-visible": it has
    at least one registered RateRule (get_rate_rules non-empty). Walks
    the LIVE registry, never a manually maintained list, so a newly
    registered program appears automatically — same discipline
    classify_all_programs_provenance() already uses."""
    from app.data.program_rate_rules import _RULES_BY_PROGRAM

    return tuple(sorted(_RULES_BY_PROGRAM.keys()))


def classify_all_programs(known_jurisdiction_codes: frozenset[str] | None = None) -> dict[str, ProgramConformanceResult]:
    """Runs classify_program_conformance for every optimizer-visible
    program. This is the function the Canonical Integrity Gate's
    PROGRAM ONBOARDING CONFORMANCE invariant calls."""
    return {
        slug: classify_program_conformance(slug, known_jurisdiction_codes)
        for slug in all_optimizer_visible_program_slugs()
    }
