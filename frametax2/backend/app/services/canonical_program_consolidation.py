"""
canonical_program_consolidation.py

Canonical authority substrate, Task 4 — a READ-ONLY field-consolidation
view for one canonical program identity (canonical_program_identity.py).

Given a canonical_program_id, exposes the best CURRENTLY AVAILABLE internal
value/status for every executable dimension the served pricing pipeline
actually depends on, WITHOUT inventing a missing value. This is
CONSOLIDATION, not economic reinterpretation: every field read here is read
verbatim from an EXISTING registry function (get_rate_rules,
get_program_rules, resolve_program_doctrine, get_qpe_cap, ...) — the same
functions canonical_evaluation.py's own pricing path already calls. No new
rule, rate, threshold, or cap is computed or guessed.

Required executable dimensions (per the Codex authority-gap missing-rule
vocabulary):

    RATE_OR_AWARD_BASIS, QPE_DEFINITION, TERRITORIALITY, MINIMUM_SPEND,
    CAP, ELIGIBLE_PRODUCTION_TYPE, CULTURAL_OR_CONTENT_TEST, UPLIFT_RULES,
    RESIDENT_NONRESIDENT_TREATMENT, PAYROLL_TREATMENT, MONETIZATION,
    REFUNDABILITY, TRANSFERABILITY, APPLICATION_TIMING

Each dimension reports one of:

    PRESENT                       a defensible executable value exists in
                                   a runtime registry the pricing pipeline
                                   actually reads
    PARTIAL                       a related signal exists (e.g. a stored
                                   discovery-only value, or a bare boolean
                                   flag) but not the full executable rule
                                   the pricing pipeline would consult
    MISSING                       no runtime registry carries anything for
                                   this dimension for this program
    NOT_APPLICABLE                never asserted by this module — a
                                   dimension is confirmed inapplicable
                                   (e.g. "primary authority establishes no
                                   cap") only by primary-source research,
                                   which this module performs none of.
                                   Reserved for a future research pass to
                                   set, with its own citation; never
                                   produced automatically here
    AUTHORITATIVE_SILENCE_CONFIRMED  never asserted by this module — a
                                   deliberate, RESEARCHED confirmation that
                                   the primary source is silent on this
                                   dimension (distinct from NOT_APPLICABLE,
                                   which confirms the dimension genuinely
                                   does not apply; this confirms it applies
                                   but the source doesn't address it, and a
                                   researcher has verified that absence is
                                   itself the finding, not an oversight).
                                   Reserved for future research; never
                                   produced automatically here
    CONFLICT                       never asserted by this module in its
                                   current form — reserved for a future
                                   pass that cross-checks two registries
                                   disagreeing; today's registries do not
                                   overlap enough to detect this safely
                                   without research, so it is never
                                   produced automatically

plus a `source` string naming the exact function/field the status came
from, so a human can verify it in seconds.

`RESOLVED_FOR_AUTHORITY_COMPLETENESS` / `UNRESOLVED_FOR_AUTHORITY_
COMPLETENESS` classify these five statuses for the authority-completeness
contract (canonical_publication_contract.py, Task 2 of the authority
completeness contract correction): PRESENT, NOT_APPLICABLE, and
AUTHORITATIVE_SILENCE_CONFIRMED all represent a dimension a human has
actually resolved (with a defensible value, a confirmed non-applicability,
or a confirmed deliberate silence); PARTIAL, MISSING, and CONFLICT all
represent a dimension nobody has actually resolved yet, regardless of
whether the CURRENT pricing engine can still produce a number by falling
back to doctrine. Runtime priceability (whether the engine can currently
price a program) and authority completeness (whether the record is
actually resolved) are permanently independent questions — see
canonical_publication_contract.py's `priceability()` vs
`authority_completeness()`.

This module deliberately does NOT read authority_coverage_registry's
adjudication state, any AUTHORITY_CLOSED disposition, or any validation
artifact — see canonical_publication_contract.py (Task 6) for why that
separation is load-bearing.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from app.data import global_inventory as _gi
from app.data.program_rate_rules import get_qpe_cap, get_rate_rules
from app.data.program_spend_rules import get_program_doctrine, get_program_rules, resolve_program_doctrine
# Canonical global program universe completion: executable_jurisdiction_
# registry.DoctrineRecord is the single canonical source for a program's
# is_refundable/is_transferable/min_spend_usd/annual_cap_usd/requires_
# cultural_test facts (see that module's own docstring) -- this
# consolidation view previously read ONLY global_inventory for those
# fields, missing real, cited, sometimes VERIFIED-tier data already
# registered for 107+ programs via register(DoctrineRecord(...)) (e.g.
# Georgia's O.C.G.A. Section 48-7-40.26-cited, VERIFIED-tier record).
# Imported here, not at program_rate_rules.py's own top level, to match
# that module's own documented bottom-of-file import discipline (avoids
# the circular import between program_rate_rules.py and program_rate_
# rules_worldwide.py); by the time this module is imported, program_rate_
# rules.py has already fully executed its own bottom import and populated
# executable_jurisdiction_registry._REGISTRY.
from app.data.executable_jurisdiction_registry import get_doctrine

CONSOLIDATION_VERSION = "authority-substrate-1.2.0"

PRESENT = "PRESENT"
PARTIAL = "PARTIAL"
MISSING = "MISSING"
NOT_APPLICABLE = "NOT_APPLICABLE"
AUTHORITATIVE_SILENCE_CONFIRMED = "AUTHORITATIVE_SILENCE_CONFIRMED"
CONFLICT = "CONFLICT"

#: A dimension counts as RESOLVED for authority completeness only when a
#: human has actually closed the question — a real value, a confirmed
#: non-applicability, or a confirmed deliberate silence. It does NOT
#: include PARTIAL/MISSING, even though the current pricing engine may
#: still produce a number via doctrine fallback for those — that fallback
#: answers "can the engine price it today", never "is the record
#: complete." See canonical_publication_contract.py.
RESOLVED_FOR_AUTHORITY_COMPLETENESS: frozenset[str] = frozenset({
    PRESENT, NOT_APPLICABLE, AUTHORITATIVE_SILENCE_CONFIRMED,
})
#: The complement — PARTIAL, MISSING, and CONFLICT all mean nobody has
#: actually resolved this dimension yet.
UNRESOLVED_FOR_AUTHORITY_COMPLETENESS: frozenset[str] = frozenset({
    PARTIAL, MISSING, CONFLICT,
})

REQUIRED_DIMENSIONS: tuple[str, ...] = (
    "RATE_OR_AWARD_BASIS",
    "QPE_DEFINITION",
    "TERRITORIALITY",
    "MINIMUM_SPEND",
    "CAP",
    "ELIGIBLE_PRODUCTION_TYPE",
    "CULTURAL_OR_CONTENT_TEST",
    "UPLIFT_RULES",
    "RESIDENT_NONRESIDENT_TREATMENT",
    "PAYROLL_TREATMENT",
    "MONETIZATION",
    "REFUNDABILITY",
    "TRANSFERABILITY",
    "APPLICATION_TIMING",
)


@dataclass(frozen=True)
class DimensionState:
    dimension: str
    status: str
    source: str


@dataclass(frozen=True)
class ProgramConsolidation:
    canonical_program_id: str
    dimensions: tuple[DimensionState, ...]

    def status_for(self, dimension: str) -> str | None:
        for d in self.dimensions:
            if d.dimension == dimension:
                return d.status
        return None

    def as_dict(self) -> dict:
        return {
            "canonical_program_id": self.canonical_program_id,
            "dimensions": [asdict(d) for d in self.dimensions],
        }


def _global_inventory_entry(slug: str):
    return next((p for p in _gi.ALL_PROGRAMS if p.program_slug == slug), None)


def consolidate(canonical_program_id: str) -> ProgramConsolidation:
    """The field-consolidation view for one canonical program. Pure read —
    calls only existing, already-served registry functions."""
    slug = canonical_program_id
    rate_rules = get_rate_rules(slug)
    program_rules = get_program_rules(slug)
    doctrine_resolution = resolve_program_doctrine(slug)
    qpe_cap = get_qpe_cap(slug)
    gi_entry = _global_inventory_entry(slug)
    doctrine = get_doctrine(slug)
    doctrine_verified = doctrine is not None and doctrine.confidence_tier == "VERIFIED"
    doctrine_partial = doctrine is not None and doctrine.confidence_tier in ("PARSED", "DISCOVERY")

    dims: list[DimensionState] = []

    # RATE_OR_AWARD_BASIS — the executable rate-rule registry, the SAME
    # function canonical_evaluation.py._price_candidate() calls to resolve
    # a rate. RateRule.confidence_tier is the exact signal that separates a
    # verified, executable rate from a real-but-not-yet-accepted one: a
    # PARSED/DISCOVERY-tier RateRule (a genuine cited source, e.g. a BFI/
    # HMRC or canada.ca page) still exists for many P0 gap programs — it
    # proves the identity is not a blank placeholder, but it is NOT the
    # authority-adjudicated basis pricing is allowed to use, so it is
    # PARTIAL, never PRESENT.
    verified_rate_rules = [r for r in rate_rules if r.confidence_tier == "VERIFIED"]
    if verified_rate_rules:
        dims.append(DimensionState("RATE_OR_AWARD_BASIS", PRESENT,
                                    f"program_rate_rules.get_rate_rules() returned "
                                    f"{len(verified_rate_rules)} VERIFIED RateRule(s)"))
    elif rate_rules:
        tiers = sorted({r.confidence_tier for r in rate_rules})
        dims.append(DimensionState("RATE_OR_AWARD_BASIS", PARTIAL,
                                    f"{len(rate_rules)} RateRule(s) exist with confidence_tier {tiers} "
                                    "(cited but not VERIFIED) — not yet accepted as executable"))
    elif gi_entry is not None and (gi_entry.base_rate is not None or gi_entry.max_rate is not None):
        dims.append(DimensionState("RATE_OR_AWARD_BASIS", PARTIAL,
                                    "global_inventory stores a discovery-only base_rate/max_rate, "
                                    "not accepted into program_rate_rules' executable layer"))
    else:
        dims.append(DimensionState("RATE_OR_AWARD_BASIS", MISSING,
                                    "no RateRule registered in program_rate_rules"))

    # QPE_DEFINITION — structured per-category spend rules. A doctrine
    # resolved above the canonical-default tier (EXPLICIT or
    # EVIDENCE_CONSTRAINED) still governs unlisted categories, so it counts
    # as a PARTIAL executable basis even with zero explicit category rules;
    # the canonical-default tier alone (no evidence either way) is MISSING.
    if program_rules:
        dims.append(DimensionState("QPE_DEFINITION", PRESENT,
                                    f"program_spend_rules.get_program_rules() returned {len(program_rules)} "
                                    "category SpendRule(s)"))
    elif doctrine_resolution.basis.value != "canonical_default":
        dims.append(DimensionState("QPE_DEFINITION", PARTIAL,
                                    f"no explicit category rules, but doctrine basis is "
                                    f"{doctrine_resolution.basis.value} (not the unclassified default)"))
    else:
        dims.append(DimensionState("QPE_DEFINITION", MISSING,
                                    "zero category SpendRule(s) and doctrine is the unclassified canonical default"))

    # TERRITORIALITY — whether ANY category rule for this program is
    # flagged territorial_only, the ONLY structural signal
    # qualification_derivation.py's territorial-nexus step reads.
    territorial_rules = [r for r in program_rules.values() if r.territorial_only]
    if territorial_rules:
        dims.append(DimensionState("TERRITORIALITY", PRESENT,
                                    f"{len(territorial_rules)} category SpendRule(s) carry territorial_only=True"))
    else:
        dims.append(DimensionState("TERRITORIALITY", MISSING,
                                    "no category SpendRule carries territorial_only=True — vendor/residence/"
                                    "place-of-performance predicates are not structurally captured"))

    # MINIMUM_SPEND — a VERIFIED rate rule's min_qpe_usd (the same
    # confidence-tier standard as RATE_OR_AWARD_BASIS above; a min_qpe_usd
    # on a non-VERIFIED rule is real but not yet executable), OR the same
    # fact carried directly on a VERIFIED/PARSED DoctrineRecord.
    min_spend_rules = [r for r in verified_rate_rules if r.min_qpe_usd is not None]
    if min_spend_rules:
        dims.append(DimensionState("MINIMUM_SPEND", PRESENT,
                                    f"{len(min_spend_rules)} VERIFIED RateRule(s) carry an explicit min_qpe_usd"))
    elif doctrine_verified and doctrine.min_spend_usd is not None:
        dims.append(DimensionState("MINIMUM_SPEND", PRESENT,
                                    f"VERIFIED DoctrineRecord.min_spend_usd={doctrine.min_spend_usd} ({doctrine.source_ref})"))
    elif any(r.min_qpe_usd is not None for r in rate_rules) or (doctrine_partial and doctrine.min_spend_usd is not None):
        dims.append(DimensionState("MINIMUM_SPEND", PARTIAL,
                                    "a min_qpe_usd/min_spend_usd exists on a non-VERIFIED source only"))
    else:
        dims.append(DimensionState("MINIMUM_SPEND", MISSING,
                                    "no RateRule or DoctrineRecord carries a minimum-spend value"))

    # CAP — the executable QPE-cap rule, or a VERIFIED/PARSED
    # DoctrineRecord.annual_cap_usd. A DoctrineRecord field left None is
    # NOT treated as a confirmed absence here (this dataclass cannot
    # distinguish "confirmed no cap" from "not modeled") — that remains
    # MISSING until a dedicated NOT_APPLICABLE citation is recorded, never
    # inferred from a bare None.
    if qpe_cap is not None:
        dims.append(DimensionState("CAP", PRESENT, "program_rate_rules.get_qpe_cap() returned a QpeCapRule"))
    elif doctrine_verified and doctrine.annual_cap_usd is not None:
        dims.append(DimensionState("CAP", PRESENT,
                                    f"VERIFIED DoctrineRecord.annual_cap_usd={doctrine.annual_cap_usd} ({doctrine.source_ref})"))
    elif doctrine_partial and doctrine.annual_cap_usd is not None:
        dims.append(DimensionState("CAP", PARTIAL, "a non-VERIFIED DoctrineRecord carries an annual_cap_usd value"))
    else:
        dims.append(DimensionState("CAP", MISSING, "program_rate_rules.get_qpe_cap() returned None"))

    # ELIGIBLE_PRODUCTION_TYPE — whether any VERIFIED rate rule scopes
    # production_types (same confidence-tier standard as above).
    typed_rules = [r for r in verified_rate_rules if r.production_types]
    if typed_rules:
        dims.append(DimensionState("ELIGIBLE_PRODUCTION_TYPE", PRESENT,
                                    f"{len(typed_rules)} VERIFIED RateRule(s) carry an explicit production_types scope"))
    elif any(r.production_types for r in rate_rules):
        dims.append(DimensionState("ELIGIBLE_PRODUCTION_TYPE", PARTIAL,
                                    "a production_types scope exists on a non-VERIFIED RateRule only"))
    else:
        dims.append(DimensionState("ELIGIBLE_PRODUCTION_TYPE", MISSING,
                                    "no RateRule carries a production_types scope"))

    # CULTURAL_OR_CONTENT_TEST — a VERIFIED DoctrineRecord.requires_
    # cultural_test is a real, reviewed determination (True OR False both
    # count as PRESENT — "confirmed no test" is exactly as resolved as
    # "confirmed a test exists"); a non-VERIFIED DoctrineRecord or a bare
    # global_inventory flag is PARTIAL, never the test's own criteria.
    if doctrine_verified:
        dims.append(DimensionState("CULTURAL_OR_CONTENT_TEST", PRESENT,
                                    f"VERIFIED DoctrineRecord.requires_cultural_test={doctrine.requires_cultural_test} "
                                    f"({doctrine.source_ref})"))
    elif doctrine_partial or (gi_entry is not None and gi_entry.requires_cultural_test is not None):
        source = (f"non-VERIFIED DoctrineRecord.requires_cultural_test={doctrine.requires_cultural_test}"
                  if doctrine_partial else
                  f"global_inventory states requires_cultural_test={gi_entry.requires_cultural_test}")
        dims.append(DimensionState("CULTURAL_OR_CONTENT_TEST", PARTIAL,
                                    f"{source} (a flag only, not the test's own criteria)"))
    else:
        dims.append(DimensionState("CULTURAL_OR_CONTENT_TEST", MISSING,
                                    "no DoctrineRecord or global_inventory entry states requires_cultural_test"))

    # UPLIFT_RULES — more than one RateRule tier for a program IS a real
    # executable uplift/ceiling structure (the tier ABOVE the base rate,
    # with its own conditions) — the same tiers RATE_OR_AWARD_BASIS above
    # already reads, not a separate fabricated signal. A bare
    # jurisdiction_comparison.resident_labor_uplift_available flag (no
    # tier structure) is PARTIAL only.
    if len(verified_rate_rules) > 1:
        dims.append(DimensionState("UPLIFT_RULES", PRESENT,
                                    f"{len(verified_rate_rules)} VERIFIED RateRule tiers registered "
                                    "(base + uplift/ceiling structure)"))
    elif len(rate_rules) > 1:
        dims.append(DimensionState("UPLIFT_RULES", PARTIAL,
                                    f"{len(rate_rules)} non-VERIFIED RateRule tiers registered "
                                    "(a real tier structure, not yet accepted as executable)"))
    else:
        from app.calculators import jurisdiction_comparison as _jc
        jc_profile = next((p for p in _jc.ALL_PROFILES.values() if p.program_slug == slug), None)
        if jc_profile is not None and jc_profile.resident_labor_uplift_available:
            dims.append(DimensionState("UPLIFT_RULES", PARTIAL,
                                        "jurisdiction_comparison states resident_labor_uplift_available=True "
                                        "(a flag only, not the uplift's own rate/conditions)"))
        else:
            dims.append(DimensionState("UPLIFT_RULES", MISSING, "no uplift flag or rule found in any registry"))

    # RESIDENT_NONRESIDENT_TREATMENT — whether the labor categories that
    # actually distinguish residency (btl_resident_labor/btl_nonresident_labor)
    # have explicit category rules.
    residency_categories = {"btl_resident_labor", "btl_nonresident_labor"}
    if residency_categories & program_rules.keys():
        dims.append(DimensionState("RESIDENT_NONRESIDENT_TREATMENT", PRESENT,
                                    f"category rule(s) present for {sorted(residency_categories & program_rules.keys())}"))
    else:
        dims.append(DimensionState("RESIDENT_NONRESIDENT_TREATMENT", MISSING,
                                    "no btl_resident_labor/btl_nonresident_labor category rule"))

    # PAYROLL_TREATMENT — the payroll_fringes category rule.
    if "payroll_fringes" in program_rules:
        dims.append(DimensionState("PAYROLL_TREATMENT", PRESENT, "payroll_fringes category rule present"))
    else:
        dims.append(DimensionState("PAYROLL_TREATMENT", MISSING, "no payroll_fringes category rule"))

    # MONETIZATION / REFUNDABILITY / TRANSFERABILITY — prefer a VERIFIED
    # DoctrineRecord's is_refundable/is_transferable (a real, reviewed
    # determination -- False is exactly as resolved as True) over a bare
    # global_inventory flag; a non-VERIFIED DoctrineRecord or a bare
    # global_inventory flag is PARTIAL, never fixed transfer-cost terms.
    doctrine_refundable = doctrine.is_refundable if doctrine is not None else None
    doctrine_transferable = doctrine.is_transferable if doctrine is not None else None
    gi_refundable = gi_entry.is_refundable if gi_entry is not None else None
    gi_transferable = gi_entry.is_transferable if gi_entry is not None else None

    def _monetization_dim(name: str, doctrine_value, gi_value, gi_field: str) -> DimensionState:
        if doctrine_verified and doctrine_value is not None:
            return DimensionState(name, PRESENT,
                                   f"VERIFIED DoctrineRecord.{gi_field.replace('gi_', 'is_')}={doctrine_value} "
                                   f"({doctrine.source_ref})")
        if doctrine_partial and doctrine_value is not None:
            return DimensionState(name, PARTIAL, f"non-VERIFIED DoctrineRecord value={doctrine_value}")
        if gi_value is not None:
            return DimensionState(name, PARTIAL, f"global_inventory.{gi_field}={gi_value}")
        return DimensionState(name, MISSING, f"no DoctrineRecord or global_inventory {gi_field} value")

    refund_dim = _monetization_dim("REFUNDABILITY", doctrine_refundable, gi_refundable, "is_refundable")
    xfer_dim = _monetization_dim("TRANSFERABILITY", doctrine_transferable, gi_transferable, "is_transferable")
    dims.append(refund_dim)
    dims.append(xfer_dim)
    # MONETIZATION resolves only once BOTH its component facts do — a
    # program refundable but of unknown transferability (or vice versa)
    # has not actually had its monetization mechanism fully reviewed.
    if refund_dim.status == PRESENT and xfer_dim.status == PRESENT:
        dims.append(DimensionState("MONETIZATION", PRESENT,
                                    f"REFUNDABILITY and TRANSFERABILITY both PRESENT ({doctrine.source_ref})"))
    elif refund_dim.status != MISSING or xfer_dim.status != MISSING:
        dims.append(DimensionState("MONETIZATION", PARTIAL,
                                    f"refundability={refund_dim.status}, transferability={xfer_dim.status}"))
    else:
        dims.append(DimensionState("MONETIZATION", MISSING, "no refundability or transferability data on file"))

    # APPLICATION_TIMING — no runtime field exists anywhere in the current
    # registries (rate rules, spend rules, global_inventory, jurisdiction
    # profiles) for preapproval/application-window timing. Honestly MISSING
    # for every program rather than reading a source that doesn't exist.
    dims.append(DimensionState("APPLICATION_TIMING", MISSING,
                                "no runtime registry field captures application/preapproval timing"))

    return ProgramConsolidation(canonical_program_id=slug, dimensions=tuple(dims))
