"""
program_authority_provenance.py

CBA-010 — durable, structured authority provenance for the served
program-rate universe. This is a BACKFILL/DURABILITY/CLASSIFICATION
module, not a new research pass: it reads ONLY fields that already exist
on every registered RateRule (confidence_tier, citation, source_ref,
provenance) and structures them into a queryable, honest accounting.
Nothing here fabricates an issuing_authority, a URL, or a date that isn't
already present in the source data — where the structured SourceProvenance
object has not yet been individually backfilled for a rule, that rule is
reported as an explicit, exact residual, never silently dropped and never
guessed.

── Two separate axes (never conflated) ──────────────────────────────────
AUTHORITY CLASS — what KIND of source this is, used to decide whether a
proposition can establish deterministic eligibility (PRIMARY_AUTHORITY/
OFFICIAL_GUIDANCE only) or merely inform structuring/risk (PROFESSIONAL_
PRACTICE/ACADEMIC_POLICY/CASE_STUDY never do). Derived here from the
EXISTING, already-reviewed confidence_tier field (VERIFIED/PARSED/
DISCOVERY) as a disclosed, honest proxy for source reliability — not a
fresh legal re-classification of each citation's text.

PROVENANCE STATUS — whether this rule's authority has been indexed into
the structured SourceProvenance object (queryable programmatically) or
still exists only as the free-text citation/source_ref every rule has
always carried. A rule with PARTIAL status is NOT missing authority (the
citation/source_ref text is real and present) — it is missing the
structured INDEX over that authority. This is the "exact authority
residual" Section 7 of the governing spec requires be reported precisely,
never summarized away.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.data.program_rate_rules import RateRule, _RULES_BY_PROGRAM

PROGRAM_AUTHORITY_PROVENANCE_VERSION = "1.0.0"

# ── Authority class vocabulary (Section 5/6 of the governing spec) ──────
AUTHORITY_CLASS_PRIMARY_AUTHORITY = "PRIMARY_AUTHORITY"
AUTHORITY_CLASS_OFFICIAL_GUIDANCE = "OFFICIAL_GUIDANCE"
AUTHORITY_CLASS_PROFESSIONAL_PRACTICE = "PROFESSIONAL_PRACTICE"
AUTHORITY_CLASS_ACADEMIC_POLICY = "ACADEMIC_POLICY"
AUTHORITY_CLASS_CASE_STUDY = "CASE_STUDY"

#: confidence_tier -> authority_class. VERIFIED rules were individually
#: confirmed against a primary/official document this project's own audit
#: trail cites; PARSED rules were extracted from a real official/practice
#: source but not independently re-verified; DISCOVERY rules are early,
#: single-source findings not yet corroborated -- reported as CASE_STUDY
#: (informative, never sufficient alone to establish deterministic
#: eligibility) rather than silently upgraded.
_CONFIDENCE_TIER_TO_AUTHORITY_CLASS = {
    "VERIFIED": AUTHORITY_CLASS_PRIMARY_AUTHORITY,
    "PARSED": AUTHORITY_CLASS_OFFICIAL_GUIDANCE,
    "DISCOVERY": AUTHORITY_CLASS_CASE_STUDY,
}

#: Only these two classes may establish deterministic legal eligibility
#: (Section 5: "Only legally appropriate authority establishes
#: deterministic eligibility"). PROFESSIONAL_PRACTICE/ACADEMIC_POLICY/
#: CASE_STUDY may inform structuring/risk but never substitute for this.
AUTHORITY_CLASSES_ESTABLISH_ELIGIBILITY = frozenset({
    AUTHORITY_CLASS_PRIMARY_AUTHORITY, AUTHORITY_CLASS_OFFICIAL_GUIDANCE,
})

# ── Provenance status vocabulary (Section 7) ─────────────────────────────
PROVENANCE_STATUS_STRUCTURED_COMPLETE = "STRUCTURED_PROVENANCE_COMPLETE"
PROVENANCE_STATUS_PARTIAL_WITH_RESIDUAL = "STRUCTURED_PROVENANCE_PARTIAL_WITH_EXACT_AUTHORITY_RESIDUAL"
#: Never actually assigned by classify_program_provenance() below -- every
#: registered rule always carries a real, non-empty citation/source_ref
#: (required fields on RateRule), so no program can be "not connected" to
#: any authority at all. Kept as a named constant so callers/tests can
#: assert its absence explicitly, per Section 7: "No profile may remain
#: PROVENANCE_NOT_CONNECTED."
PROVENANCE_STATUS_NOT_CONNECTED = "PROVENANCE_NOT_CONNECTED"

# ── Prompt 16 terminal authority dispositions ───────────────────────────
#: PROJECT_RULES.md's final authority-safety gate: before a production-
#: accepted build, every program must reach exactly one of these two.
AUTHORITY_VERIFIED_PRICEABLE = "AUTHORITY_VERIFIED_PRICEABLE"
AUTHORITY_UNRESOLVED_NON_PRICEABLE = "AUTHORITY_UNRESOLVED_NON_PRICEABLE"
#: The forbidden middle state -- a program that is still PRICEABLE while
#: only partially supported. The acceptance invariant is that the count of
#: programs in this state is ZERO.
PROVENANCE_INCOMPLETE_EXISTING_RECORD = "PROVENANCE_INCOMPLETE_EXISTING_RECORD"

#: Substrings that, appearing in an `issuing_authority`, indicate a
#: SECONDARY source (law firm, consultancy, production-service company,
#: aggregator, trade press). PROJECT_RULES.md §4: secondary sources may
#: locate an official source but may never independently justify continued
#: deterministic pricing -- so naming one as the issuing authority can
#: never satisfy the verified disposition.
_SECONDARY_AUTHORITY_MARKERS = (
    "law firm", "llp", " llc", "consult", "advisor", "advisory", "fixer",
    "production service", "productionservice", "aggregator", "blog",
    "variety", "deadline", "screendaily", "hollywood reporter", "kpmg",
    "baker mckenzie", "greenberg", "rodriques", "shamelstudio",
    "thereactionlab", "northbridge", "camaleon", "mbrella", "vitrina",
    "celluloid", "needafixer", "hellodarwin", "atlasfilm", "innovires",
)


def _is_substantively_supported(rule) -> bool:
    """Substantive authority test (PROJECT_RULES.md §6: the classifier must
    inspect substantive fields and source authority, NOT merely test that a
    SourceProvenance object is non-null).

    A rule is substantively supported only when its provenance:
      1. exists at all;
      2. names an `issuing_authority` -- the body that actually administers
         or enacted the rule;
      3. that authority is not a secondary source; and
      4. carries a `citation_detail` -- the specific proposition anchor
         (quoted rate/threshold/section), not just a bare authority name.

    A bare object, an empty authority, or an authority with no proposition
    anchor all FAIL -- exactly the "non-null is not proof" defect this
    replaces.
    """
    p = getattr(rule, "provenance", None)
    if p is None:
        return False
    authority = (p.issuing_authority or "").strip()
    detail = (p.citation_detail or "").strip()
    if not authority or not detail:
        return False
    lowered = authority.lower()
    return not any(marker in lowered for marker in _SECONDARY_AUTHORITY_MARKERS)


def authority_disposition(program_slug: str) -> str:
    """The program's TERMINAL Prompt 16 disposition.

    AUTHORITY_VERIFIED_PRICEABLE      -- every runtime tier is substantively
        supported (so the program may price deterministically).
    AUTHORITY_UNRESOLVED_NON_PRICEABLE -- it is not, AND the canonical
        economic-candidacy registry blocks it, so it contributes no
        economics anywhere (fail-closed, per PROJECT_RULES.md).
    PROVENANCE_INCOMPLETE_EXISTING_RECORD -- the FORBIDDEN state: partially
        supported yet still priceable. The acceptance invariant requires
        zero programs here.

    Note the conjunction: a program is only "unresolved non-priceable" when
    the quarantine is ACTUALLY ENFORCED in the canonical registry. Marking a
    record unresolved without blocking it would leave it priceable, which is
    precisely the unsafe state this function exists to detect.
    """
    from app.data.authority_coverage_registry import blocks_economic_candidacy

    rules = _RULES_BY_PROGRAM.get(program_slug)
    if not rules:
        return AUTHORITY_UNRESOLVED_NON_PRICEABLE
    if all(_is_substantively_supported(r) for r in rules):
        return AUTHORITY_VERIFIED_PRICEABLE
    if blocks_economic_candidacy(program_slug):
        return AUTHORITY_UNRESOLVED_NON_PRICEABLE
    return PROVENANCE_INCOMPLETE_EXISTING_RECORD


def authority_disposition_report() -> dict:
    """Full terminal accounting over the LIVE registry. The acceptance
    invariant is `priceable_partial_authority == 0`."""
    verified, unresolved, partial = [], [], []
    for slug in _RULES_BY_PROGRAM:
        d = authority_disposition(slug)
        if d == AUTHORITY_VERIFIED_PRICEABLE:
            verified.append(slug)
        elif d == AUTHORITY_UNRESOLVED_NON_PRICEABLE:
            unresolved.append(slug)
        else:
            partial.append(slug)
    return {
        "registered": len(_RULES_BY_PROGRAM),
        "authority_verified_priceable": len(verified),
        "authority_unresolved_non_priceable": len(unresolved),
        "priceable_partial_authority": len(partial),
        "priceable_partial_authority_slugs": sorted(partial),
        "verified_slugs": sorted(verified),
        "unresolved_slugs": sorted(unresolved),
    }


@dataclass(frozen=True)
class RuleProvenanceRecord:
    program_slug: str
    tier_id: str
    authority_class: str
    provenance_status: str
    citation: str
    source_ref: str
    has_structured_provenance: bool


@dataclass(frozen=True)
class ProgramProvenanceSummary:
    program_slug: str
    status: str   # PROVENANCE_STATUS_STRUCTURED_COMPLETE | _PARTIAL_WITH_RESIDUAL
    rules: tuple[RuleProvenanceRecord, ...]
    residual_tier_ids: tuple[str, ...]   # exact tier_ids still lacking a structured SourceProvenance


def classify_rule_authority_class(rule: RateRule) -> str:
    """Honest, disclosed proxy: derives authority_class from the rule's
    own, already-reviewed confidence_tier. Never re-reads or re-judges
    the citation text itself -- that judgment was already made when
    confidence_tier was originally assigned."""
    return _CONFIDENCE_TIER_TO_AUTHORITY_CLASS.get(rule.confidence_tier, AUTHORITY_CLASS_CASE_STUDY)


def classify_rule_provenance(rule: RateRule) -> RuleProvenanceRecord:
    has_structured = rule.provenance is not None
    return RuleProvenanceRecord(
        program_slug=rule.program_slug,
        tier_id=rule.tier_id,
        authority_class=classify_rule_authority_class(rule),
        provenance_status=(
            PROVENANCE_STATUS_STRUCTURED_COMPLETE if has_structured
            else PROVENANCE_STATUS_PARTIAL_WITH_RESIDUAL
        ),
        citation=rule.citation,
        source_ref=rule.source_ref,
        has_structured_provenance=has_structured,
    )


def classify_program_provenance(program_slug: str) -> ProgramProvenanceSummary | None:
    """Returns None only if the program has no registered rate rules at
    all (a genuinely different, pre-existing condition RATE_FAILURE_NO_
    RULES already reports elsewhere -- never conflated with a provenance
    gap on a program that DOES have rules)."""
    rules = _RULES_BY_PROGRAM.get(program_slug)
    if not rules:
        return None
    records = tuple(classify_rule_provenance(r) for r in rules)
    residual = tuple(r.tier_id for r in records if not r.has_structured_provenance)
    status = (
        PROVENANCE_STATUS_STRUCTURED_COMPLETE if not residual
        else PROVENANCE_STATUS_PARTIAL_WITH_RESIDUAL
    )
    return ProgramProvenanceSummary(
        program_slug=program_slug, status=status, rules=records, residual_tier_ids=residual,
    )


def classify_all_programs_provenance() -> dict[str, ProgramProvenanceSummary]:
    """Walks the LIVE registry (_RULES_BY_PROGRAM), never a manually
    copied static list -- exactly the same discipline CBA-002's own
    global regression test requires. Every registered program appears;
    none can silently disappear from this accounting."""
    out: dict[str, ProgramProvenanceSummary] = {}
    for slug in _RULES_BY_PROGRAM:
        summary = classify_program_provenance(slug)
        if summary is not None:
            out[slug] = summary
    return out


def provenance_coverage_report() -> dict:
    """Real, computed-not-fabricated top-line numbers for the served
    registry: total programs, how many are fully structured vs partial,
    and the exact residual (program_slug, tier_id) pairs still needing a
    SourceProvenance backfill. Zero programs may report
    PROVENANCE_STATUS_NOT_CONNECTED -- asserted, not assumed, by the
    regression test that accompanies this module."""
    all_summaries = classify_all_programs_provenance()
    complete = [s for s in all_summaries.values() if s.status == PROVENANCE_STATUS_STRUCTURED_COMPLETE]
    partial = [s for s in all_summaries.values() if s.status == PROVENANCE_STATUS_PARTIAL_WITH_RESIDUAL]
    disconnected = [s for s in all_summaries.values() if s.status == PROVENANCE_STATUS_NOT_CONNECTED]
    return {
        "total_programs": len(all_summaries),
        "structured_complete": len(complete),
        "partial_with_residual": len(partial),
        "disconnected": len(disconnected),
        "residual_detail": {
            s.program_slug: list(s.residual_tier_ids) for s in partial
        },
    }
