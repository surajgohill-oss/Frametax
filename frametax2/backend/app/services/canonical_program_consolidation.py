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
# Historical authority source recovery: two more program_slug-keyed
# registries already exist in the repo and were never consulted here.
# app.data.program_requirements — a 71-profile, program_slug-keyed
# "requirements" database (eligibility/application-timing/compliance/
# funding-availability/monetization facts) with its own per-profile
# EvidenceRecord (SourceType PRIMARY/SECONDARY, RecordStatus CURRENT/
# EXPIRED/PROPOSED/SUSPENDED/UNCERTAIN) and per-fact TimingBasis
# (STATUTORY_DEADLINE/OFFICIAL_TARGET/REPORTED_PRACTICAL/ESTIMATE/UNKNOWN)
# — this module's own docstring states it was built to sit "ALONGSIDE"
# DoctrineRecord without duplicating it, but nothing ever read it here.
# app.calculators.jurisdiction_comparison — a 110-profile
# JurisdictionIncentiveProfile registry (its own confidence_tier per
# profile) that this module previously read ONLY for one bare boolean
# (resident_labor_uplift_available); it independently carries base_rate/
# max_rate/is_refundable/is_transferable/annual_cap_local/min_spend_local/
# requires_cultural_test for 105 of the 105 programs that were
# FORMULAIC_AUTHORITY_INCOMPLETE before this recovery pass.
from app.data.program_requirements import (
    RecordStatus,
    TimingBasis,
    VerificationState,
    get_program_requirements,
    verification_state as requirements_verification_state,
)
from app.calculators import jurisdiction_comparison as _jc

CONSOLIDATION_VERSION = "authority-substrate-1.4.0"

#: Task: permanent prevention against a recognized authority-bearing
#: source silently becoming orphaned from consolidation again (the exact
#: defect class this recovery pass fixed for executable_jurisdiction_
#: registry, program_requirements, and jurisdiction_comparison). Each
#: entry is (module dotted path, one-line reason it is authority-bearing).
#: A focused test greps this file's own import lines for every module
#: named here — see test_no_recognized_authority_source_is_orphaned in
#: tests/test_canonical_authority_substrate.py. Add a new module here the
#: same commit it is wired in; do not let this list drift ahead of imports.
RECOGNIZED_AUTHORITY_SOURCE_MODULES: tuple[tuple[str, str], ...] = (
    ("app.data.global_inventory", "discovery-tier base_rate/max_rate/cap/refundable/transferable/cultural-test flags"),
    ("app.data.program_rate_rules", "executable RateRule tiers + QpeCapRule, confidence-tiered"),
    ("app.data.program_spend_rules", "category SpendRule + program doctrine basis"),
    ("app.data.executable_jurisdiction_registry", "DoctrineRecord: confidence-tiered refundable/transferable/min_spend/cap/cultural_test"),
    ("app.data.program_requirements", "program_slug-keyed eligibility/application-timing/compliance/monetization profiles with EvidenceRecord"),
    ("app.calculators.jurisdiction_comparison", "JurisdictionIncentiveProfile: confidence-tiered rate/cap/spend/refundable/transferable/cultural-test/uplift facts"),
)

#: RateCondition.kind -> the specific authority dimension(s) that exact
#: condition kind proves, per docs/validation/CODEX_HISTORICAL_AUTHORITY_
#: SOURCE_CROSS_REFERENCE.json's rate_condition_cross_reference (Codex's
#: exact 15-kind enumeration). program_rate_rules.py's RateRule.conditions
#: was already read for RATE_OR_AWARD_BASIS/MINIMUM_SPEND/CAP/ELIGIBLE_
#: PRODUCTION_TYPE at the RULE level (min_qpe_usd, production_types), but
#: the CONDITION-level propositions inside `conditions` were never mapped
#: to a dimension — a RateRule could carry a `cultural_test_required`
#: condition, for example, that CULTURAL_OR_CONTENT_TEST never saw. Only
#: the condition kinds Codex explicitly enumerated are mapped; any other
#: kind is left unmapped (never inferred). "material_funding_risk_not_
#: modeled" and "discretionary_band"/"graduated_bracket_applied" are
#: deliberately excluded from CAP/RATE_OR_AWARD_BASIS promotion below —
#: they are advisory/risk annotations about the RATE's reliability, not an
#: independent proposition proving a dimension resolved; promoting a
#: dimension FROM a risk disclosure would invert its own meaning.
RATE_CONDITION_KIND_TO_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "alternate_qualification_track": ("ELIGIBLE_PRODUCTION_TYPE",),
    "cultural_test_required": ("CULTURAL_OR_CONTENT_TEST",),
    "min_qpe_usd": ("MINIMUM_SPEND",),
    "min_spend_currency_not_convertible": ("MINIMUM_SPEND",),
    "min_spend_pct_of_total_budget": ("MINIMUM_SPEND",),
    "no_sponsorship_in_qpe": ("QPE_DEFINITION",),
    "production_type": ("ELIGIBLE_PRODUCTION_TYPE",),
    "production_type_uplift": ("ELIGIBLE_PRODUCTION_TYPE", "UPLIFT_RULES"),
    "sustainability_uplift": ("UPLIFT_RULES",),
}

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


_STATUS_RANK: dict[str, int] = {MISSING: 0, PARTIAL: 1, PRESENT: 2}


def _upgrade(dims: list[DimensionState], name: str, candidate: "DimensionState | None") -> None:
    """Replace the existing entry for `name` with `candidate` only if
    `candidate` is strictly higher-ranked (PRESENT > PARTIAL > MISSING).
    Never downgrades — a dimension already resolved by one source stays
    resolved even if a later-checked source has nothing to add. Used by
    the historical-authority-source-recovery pass below to fold
    program_requirements.py / jurisdiction_comparison.py evidence into the
    same 14 dimensions without duplicating each dimension's own primary
    read logic above."""
    if candidate is None:
        return
    for i, d in enumerate(dims):
        if d.dimension == name:
            if _STATUS_RANK[candidate.status] > _STATUS_RANK[d.status]:
                dims[i] = candidate
            return


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

    # program_requirements.py — gated on BOTH the profile's evidence
    # source_type (PRIMARY vs SECONDARY, via verification_state()) AND its
    # RecordStatus (a stale/superseded/uncertain record must never promote
    # a dimension to PRESENT, regardless of how the original research was
    # sourced — Task 7 currentness). A field is only "req_primary_current"
    # when both hold; anything else registered is at most PARTIAL evidence.
    req = get_program_requirements(slug)
    req_state = requirements_verification_state(slug)
    req_record_current = (
        req is not None and req.evidence is not None and req.evidence.status == RecordStatus.CURRENT
    )
    req_primary_current = req_state == VerificationState.PRIMARY_VERIFIED and req_record_current
    req_registered = req is not None

    # jurisdiction_comparison.py — same PARSED/DISCOVERY/VERIFIED tier
    # vocabulary as DoctrineRecord, carried directly on the profile.
    jc_profile = next((p for p in _jc.ALL_PROFILES.values() if p.program_slug == slug), None)
    jc_verified = jc_profile is not None and jc_profile.confidence_tier == "VERIFIED"
    jc_partial = jc_profile is not None and jc_profile.confidence_tier in ("PARSED", "DISCOVERY")

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
    elif jc_profile is not None and jc_profile.resident_labor_uplift_available:
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

    # APPLICATION_TIMING — no field existed anywhere for this dimension
    # before this recovery pass; program_requirements.py's application_
    # deadline/preapproval_mandatory fields are the first (and, as of this
    # pass, only) source. Default MISSING; see recovery pass below.
    dims.append(DimensionState("APPLICATION_TIMING", MISSING,
                                "no runtime registry field captures application/preapproval timing"))

    # ─────────────────────────────────────────────────────────────────────
    # Historical authority source recovery pass — folds program_
    # requirements.py and jurisdiction_comparison.py evidence into the
    # dimensions above via _upgrade() (never downgrades an existing
    # PRESENT/PARTIAL from the primary read logic above). Both sources are
    # gated on their OWN confidence signal, never silently promoted:
    #   program_requirements: PRESENT only when verification_state() is
    #     PRIMARY_VERIFIED AND the record's RecordStatus is CURRENT
    #     (req_primary_current) — a stale/expired/proposed/uncertain
    #     record, or a secondary-sourced one, is PARTIAL at most.
    #   jurisdiction_comparison: PRESENT only when the profile's own
    #     confidence_tier is VERIFIED; PARSED/DISCOVERY is PARTIAL.
    # ─────────────────────────────────────────────────────────────────────

    def _req_dim(name: str, req_value, jc_value=None, *, criteria_present: bool = False) -> DimensionState | None:
        """One dimension's candidate from program_requirements + (optionally)
        a jurisdiction_comparison fallback. `criteria_present=True` means the
        req field is the rule's OWN criteria (e.g. cultural_test_points), not
        just a bare flag — still gated by the same currentness/tier rules,
        but documented distinctly since a bare flag is real evidence, just
        weaker evidence, matching the existing PRESENT/PARTIAL vocabulary
        used above for doctrine records."""
        if req_value is not None:
            kind = "criteria" if criteria_present else "flag"
            if req_primary_current:
                return DimensionState(name, PRESENT,
                                       f"PRIMARY_VERIFIED, CURRENT program_requirements.{name.lower()}"
                                       f" {kind}={req_value} ({req.evidence.source_title})")
            return DimensionState(name, PARTIAL,
                                   f"program_requirements {req_state.value} or non-CURRENT record, "
                                   f"{kind}={req_value}")
        if jc_value is not None:
            if jc_verified:
                return DimensionState(name, PRESENT,
                                       f"VERIFIED jurisdiction_comparison profile value={jc_value}")
            if jc_partial:
                return DimensionState(name, PARTIAL,
                                       f"non-VERIFIED jurisdiction_comparison profile value={jc_value}")
        return None

    if req_registered or jc_profile is not None:
        # RATE_OR_AWARD_BASIS — jurisdiction_comparison's base_rate/max_rate,
        # gated the same way as every other jc-sourced dimension. Codex's
        # cross-reference flagged this as one of two jc dimensions this
        # module deliberately left unread in the prior pass (the other
        # being QPE_DEFINITION below) to avoid conflating a discovery-tier
        # rate with an executable one; both are now wired with the same
        # VERIFIED/PARSED confidence gate already used for every other jc
        # field, so a bare jc rate can promote MINIMUM_SPEND/CAP/etc but
        # never silently overrides a real RateRule-sourced VERIFIED status
        # (via _upgrade()'s never-downgrade rule).
        if jc_profile is not None and (jc_profile.base_rate is not None or jc_profile.max_rate is not None):
            _rate_val = jc_profile.base_rate if jc_profile.base_rate is not None else jc_profile.max_rate
            if jc_verified:
                _upgrade(dims, "RATE_OR_AWARD_BASIS", DimensionState(
                    "RATE_OR_AWARD_BASIS", PRESENT,
                    f"VERIFIED jurisdiction_comparison base_rate/max_rate={_rate_val}"))
            elif jc_partial:
                _upgrade(dims, "RATE_OR_AWARD_BASIS", DimensionState(
                    "RATE_OR_AWARD_BASIS", PARTIAL,
                    f"non-VERIFIED jurisdiction_comparison base_rate/max_rate={_rate_val}"))
        # QPE_DEFINITION — jurisdiction_comparison's per-category
        # qualification flags (atl_qualifies/btl_qualifies/vfx_qualifies/
        # music_qualifies). Any one populated flag is real category-scope
        # evidence but not the full QPE category schedule a SpendRule set
        # would carry, so it is capped the same way a bare boolean is
        # elsewhere in this module — VERIFIED profile -> PRESENT (a
        # reviewed determination, true or false), PARSED/DISCOVERY ->
        # PARTIAL.
        _qpe_flags = [jc_profile.atl_qualifies, jc_profile.btl_qualifies,
                      jc_profile.vfx_qualifies, jc_profile.music_qualifies] if jc_profile else []
        if any(f is not None for f in _qpe_flags):
            if jc_verified:
                _upgrade(dims, "QPE_DEFINITION", DimensionState(
                    "QPE_DEFINITION", PRESENT,
                    f"VERIFIED jurisdiction_comparison atl/btl/vfx/music_qualifies={_qpe_flags}"))
            elif jc_partial:
                _upgrade(dims, "QPE_DEFINITION", DimensionState(
                    "QPE_DEFINITION", PARTIAL,
                    f"non-VERIFIED jurisdiction_comparison atl/btl/vfx/music_qualifies={_qpe_flags}"))

        _upgrade(dims, "MINIMUM_SPEND", _req_dim(
            "MINIMUM_SPEND",
            req.min_local_spend_usd if req else None,
            jc_profile.min_spend_local if jc_profile else None,
        ) or _req_dim(
            "MINIMUM_SPEND",
            req.min_total_budget_usd if req else None,
        ))
        _upgrade(dims, "CAP", _req_dim(
            "CAP",
            req.annual_program_cap_usd if req else None,
            jc_profile.annual_cap_local if jc_profile else None,
        ) or _req_dim(
            "CAP",
            req.per_project_cap_usd if req else None,
        ))
        _upgrade(dims, "CULTURAL_OR_CONTENT_TEST", _req_dim(
            "CULTURAL_OR_CONTENT_TEST",
            req.cultural_test_points if req and req.cultural_test_points is not None else None,
            criteria_present=True,
        ) or _req_dim(
            "CULTURAL_OR_CONTENT_TEST",
            req.cultural_test_required if req else None,
            jc_profile.requires_cultural_test if jc_profile else None,
        ))
        _upgrade(dims, "REFUNDABILITY", _req_dim(
            "REFUNDABILITY",
            req.refundable if req else None,
            jc_profile.is_refundable if jc_profile else None,
        ))
        _upgrade(dims, "TRANSFERABILITY", _req_dim(
            "TRANSFERABILITY",
            req.transferable if req else None,
            jc_profile.is_transferable if jc_profile else None,
        ))
        # TERRITORIALITY — scoped strictly to the co-production/treaty
        # territorial-nexus fact (req.treaty_or_official_coproduction_
        # required). Deliberately does NOT read local_entity_required /
        # local_coproducer_required: those are entity-structure facts
        # (whether a local SPV must be formed), which the canonical local-
        # SPV assumption already treats as a non-blocking given, not a
        # territorial-spend predicate — reading them here would conflate
        # two different dimensions.
        _upgrade(dims, "TERRITORIALITY", _req_dim(
            "TERRITORIALITY",
            req.treaty_or_official_coproduction_required if req else None,
        ))
        # UPLIFT_RULES — jurisdiction_comparison's resident_labor_uplift_
        # available flag, promoted to the same VERIFIED/PARSED tiering as
        # every other jc-sourced dimension (previously read as an unconditional
        # PARTIAL regardless of the profile's own confidence_tier).
        if jc_profile is not None and jc_profile.resident_labor_uplift_available:
            if jc_verified:
                _upgrade(dims, "UPLIFT_RULES", DimensionState(
                    "UPLIFT_RULES", PRESENT,
                    "VERIFIED jurisdiction_comparison states resident_labor_uplift_available=True"))
            else:
                _upgrade(dims, "UPLIFT_RULES", DimensionState(
                    "UPLIFT_RULES", PARTIAL,
                    "jurisdiction_comparison states resident_labor_uplift_available=True "
                    "(a flag only, not the uplift's own rate/conditions)"))
        # APPLICATION_TIMING — Codex historical-authority cross-reference
        # (docs/validation/CODEX_HISTORICAL_AUTHORITY_SOURCE_CROSS_
        # REFERENCE.json, application_timing_recovery) found the prior
        # pass's application_deadline/preapproval_mandatory-only read left
        # four more program_requirements timing facts unconsumed:
        # audit_or_final_certification_deadline, payment_timing (both
        # TimingFact, same basis vocabulary as application_deadline),
        # expenditure_before_approval_qualifies (bool), and sunset_date
        # (ISO date string, no TimingBasis wrapper). Per Codex Task 5:
        # "Do NOT collapse unrelated timing concepts into one boolean" —
        # every distinct sub-fact found is named individually in the
        # `source` string rather than reduced to a single flag, while the
        # dimension's own PRESENT/PARTIAL/MISSING status still follows the
        # single strongest sub-fact found (the 14-dimension contract is
        # unchanged; only the survived provenance detail is widened).
        _timing_facts: list[tuple[str, str]] = []  # (label, rank: "present"|"partial")
        if req is not None:
            for _field_name in ("application_deadline", "audit_or_final_certification_deadline", "payment_timing"):
                _fact = getattr(req, _field_name)
                if _fact is None:
                    continue
                if _fact.basis in (TimingBasis.STATUTORY_DEADLINE, TimingBasis.OFFICIAL_TARGET) and req_primary_current:
                    _timing_facts.append((f"{_field_name}(basis={_fact.basis.value})", "present"))
                else:
                    _timing_facts.append((f"{_field_name}(basis={_fact.basis.value})", "partial"))
            if req.preapproval_mandatory is not None:
                _timing_facts.append((f"preapproval_mandatory={req.preapproval_mandatory}", "partial"))
            if req.expenditure_before_approval_qualifies is not None:
                _timing_facts.append((f"expenditure_before_approval_qualifies={req.expenditure_before_approval_qualifies}", "partial"))
            if req.sunset_date is not None:
                _timing_facts.append((f"sunset_date={req.sunset_date}", "partial"))
        if _timing_facts:
            _best_rank = "present" if any(r == "present" for _, r in _timing_facts) else "partial"
            _facts_str = ", ".join(label for label, _ in _timing_facts)
            if _best_rank == "present":
                _upgrade(dims, "APPLICATION_TIMING", DimensionState(
                    "APPLICATION_TIMING", PRESENT,
                    f"PRIMARY_VERIFIED, CURRENT program_requirements timing facts: {_facts_str} "
                    f"({req.evidence.source_title})"))
            else:
                _upgrade(dims, "APPLICATION_TIMING", DimensionState(
                    "APPLICATION_TIMING", PARTIAL,
                    f"program_requirements timing facts (non-statutory/non-official, or record not "
                    f"PRIMARY_VERIFIED+CURRENT): {_facts_str}"))

        # MONETIZATION was originally derived from refund_dim/xfer_dim
        # BEFORE this recovery pass could upgrade REFUNDABILITY/
        # TRANSFERABILITY above — recompute it from the dims list's final
        # (post-upgrade) values so it never goes stale relative to its own
        # two component dimensions. Deliberately NOT routed through
        # _upgrade(): this is a full recompute of a derived dimension from
        # its own two authoritative inputs, not another candidate source —
        # _upgrade()'s never-downgrade rule would (and, before this fix,
        # did) leave a STALE MONETIZATION source string in place whenever
        # the recomputed status happened to rank equal to the original
        # pre-recovery status (e.g. PARTIAL-before vs PARTIAL-after, where
        # only the underlying REFUNDABILITY/TRANSFERABILITY reasoning
        # text, not the rank, had actually changed). Direct index
        # replacement always reflects the true final component states.
        final_refund = next(d for d in dims if d.dimension == "REFUNDABILITY")
        final_xfer = next(d for d in dims if d.dimension == "TRANSFERABILITY")
        _monetization_idx = next(i for i, d in enumerate(dims) if d.dimension == "MONETIZATION")
        if final_refund.status == PRESENT and final_xfer.status == PRESENT:
            dims[_monetization_idx] = DimensionState(
                "MONETIZATION", PRESENT,
                "REFUNDABILITY and TRANSFERABILITY both PRESENT after historical-source recovery")
        elif final_refund.status != MISSING or final_xfer.status != MISSING:
            dims[_monetization_idx] = DimensionState(
                "MONETIZATION", PARTIAL,
                f"refundability={final_refund.status}, transferability={final_xfer.status}")

    # RateRule.conditions[*].kind -> dimension mapping (Codex Task 2).
    # rate_rules already exists from the top-of-function read used for
    # RATE_OR_AWARD_BASIS/MINIMUM_SPEND/CAP/ELIGIBLE_PRODUCTION_TYPE — this
    # walks the same rules a second time, but at the CONDITION level, only
    # for the explicit kinds in RATE_CONDITION_KIND_TO_DIMENSIONS. A single
    # RateRule's own confidence_tier still governs PRESENT-vs-PARTIAL for
    # every condition it carries (RateCondition has no independent tier) —
    # never a blanket promotion of the whole rule, only the dimension(s)
    # that specific condition kind actually proves.
    for _rule in rate_rules:
        for _condition in _rule.conditions:
            _target_dims = RATE_CONDITION_KIND_TO_DIMENSIONS.get(_condition.kind)
            if not _target_dims:
                continue
            _status = PRESENT if _rule.confidence_tier == "VERIFIED" else PARTIAL
            _tier_word = "VERIFIED" if _status == PRESENT else _rule.confidence_tier
            for _dim_name in _target_dims:
                _upgrade(dims, _dim_name, DimensionState(
                    _dim_name, _status,
                    f"{_tier_word} RateRule condition kind={_condition.kind!r}: {_condition.description} "
                    f"({_condition.quote[:120]})"))

    return ProgramConsolidation(canonical_program_id=slug, dimensions=tuple(dims))
