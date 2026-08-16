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

    PRESENT          a defensible executable value exists in a runtime
                      registry the pricing pipeline actually reads
    PARTIAL          a related signal exists (e.g. a stored discovery-only
                      value, or a bare boolean flag) but not the full
                      executable rule the pricing pipeline would consult
    MISSING          no runtime registry carries anything for this
                      dimension for this program
    NOT_APPLICABLE   never asserted by this module — no dimension here is
                      confirmed inapplicable without primary-source
                      research, so this status is reserved for future,
                      research-backed use and never produced automatically
    CONFLICT         never asserted by this module in its current form —
                      reserved for a future pass that cross-checks two
                      registries disagreeing; today's registries do not
                      overlap enough to detect this safely without
                      research, so it is never produced automatically

plus a `source` string naming the exact function/field the status came
from, so a human can verify it in seconds.

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

CONSOLIDATION_VERSION = "authority-substrate-1.0.0"

PRESENT = "PRESENT"
PARTIAL = "PARTIAL"
MISSING = "MISSING"
NOT_APPLICABLE = "NOT_APPLICABLE"
CONFLICT = "CONFLICT"

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
    # on a non-VERIFIED rule is real but not yet executable).
    min_spend_rules = [r for r in verified_rate_rules if r.min_qpe_usd is not None]
    if min_spend_rules:
        dims.append(DimensionState("MINIMUM_SPEND", PRESENT,
                                    f"{len(min_spend_rules)} VERIFIED RateRule(s) carry an explicit min_qpe_usd"))
    elif any(r.min_qpe_usd is not None for r in rate_rules):
        dims.append(DimensionState("MINIMUM_SPEND", PARTIAL,
                                    "a min_qpe_usd exists on a non-VERIFIED RateRule only"))
    else:
        dims.append(DimensionState("MINIMUM_SPEND", MISSING,
                                    "no RateRule carries min_qpe_usd"))

    # CAP — the executable QPE-cap rule.
    if qpe_cap is not None:
        dims.append(DimensionState("CAP", PRESENT, "program_rate_rules.get_qpe_cap() returned a QpeCapRule"))
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

    # CULTURAL_OR_CONTENT_TEST — global_inventory's stated flag. A bare
    # boolean, never the actual test criteria, so PRESENT is never claimed
    # here — only whether even that much is on file.
    if gi_entry is not None and gi_entry.requires_cultural_test is not None:
        dims.append(DimensionState("CULTURAL_OR_CONTENT_TEST", PARTIAL,
                                    f"global_inventory states requires_cultural_test={gi_entry.requires_cultural_test} "
                                    "(a flag only, not the test's own criteria)"))
    else:
        dims.append(DimensionState("CULTURAL_OR_CONTENT_TEST", MISSING,
                                    "no global_inventory entry states requires_cultural_test"))

    # UPLIFT_RULES — no executable uplift-rate structure exists anywhere in
    # the current registries for any program; jurisdiction_comparison's
    # resident_labor_uplift_available (when present) is a bare flag only.
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

    # MONETIZATION / REFUNDABILITY / TRANSFERABILITY — global_inventory's
    # stated flags (bare booleans, not fixed transfer-cost terms).
    is_refundable = gi_entry.is_refundable if gi_entry is not None else None
    is_transferable = gi_entry.is_transferable if gi_entry is not None else None
    if is_refundable is not None or is_transferable is not None:
        dims.append(DimensionState("MONETIZATION", PARTIAL,
                                    f"global_inventory states is_refundable={is_refundable}, "
                                    f"is_transferable={is_transferable}"))
    else:
        dims.append(DimensionState("MONETIZATION", MISSING, "no global_inventory refundability/transferability flags"))
    dims.append(DimensionState(
        "REFUNDABILITY",
        PARTIAL if is_refundable is not None else MISSING,
        f"global_inventory.is_refundable={is_refundable}" if is_refundable is not None
        else "no global_inventory is_refundable flag",
    ))
    dims.append(DimensionState(
        "TRANSFERABILITY",
        PARTIAL if is_transferable is not None else MISSING,
        f"global_inventory.is_transferable={is_transferable}" if is_transferable is not None
        else "no global_inventory is_transferable flag",
    ))

    # APPLICATION_TIMING — no runtime field exists anywhere in the current
    # registries (rate rules, spend rules, global_inventory, jurisdiction
    # profiles) for preapproval/application-window timing. Honestly MISSING
    # for every program rather than reading a source that doesn't exist.
    dims.append(DimensionState("APPLICATION_TIMING", MISSING,
                                "no runtime registry field captures application/preapproval timing"))

    return ProgramConsolidation(canonical_program_id=slug, dimensions=tuple(dims))
