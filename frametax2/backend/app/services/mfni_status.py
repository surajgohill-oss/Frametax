"""MFNI (regional production-cost normalization) status for a served structure.

Cost benchmarks (``app.data.location_cost_benchmarks``) exist only per COUNTRY ("US", "CA", "MX" among the North American codes); no state or province has one, so
``get_profile_or_fallback`` serves a LOW-confidence placeholder for every subnational candidate. A missing benchmark must leave MFNI UNMODELED, disclosed, never silently
suppress the incentive scenario (the candidate keeps its real qualifying spend, incentive and NPC; comparability is gated separately by ``is_directly_comparable``) and never be
presented as modelled. This module only reports that state at serving time; it changes no economics and is deliberately outside the pricing-digest modules.
"""
from __future__ import annotations

MODELED = "MODELED"
UNMODELED = "UNMODELED_NO_BENCHMARK"
NOT_APPLICABLE = "NOT_APPLICABLE_BASELINE"


def mfni_disclosure(*, is_baseline: bool, jurisdiction_codes: list[str], home_code: str | None) -> dict:
    from app.data.location_cost_benchmarks import list_supported_jurisdictions

    if is_baseline:
        return {"status": NOT_APPLICABLE, "unmodeled_jurisdictions": [], "note": "The production's own base needs no relocation-cost normalization."}
    supported = set(list_supported_jurisdictions())
    codes = sorted({c for c in (jurisdiction_codes or []) if c and c != home_code})
    missing = [c for c in codes if c.upper() not in supported]
    if not missing:
        return {"status": MODELED, "unmodeled_jurisdictions": [], "note": "A cost benchmark exists for every destination jurisdiction."}
    return {
        "status": UNMODELED, "unmodeled_jurisdictions": missing,
        "note": ("Regional production-cost normalization (MFNI) is UNMODELED for " + ", ".join(missing) + ": no cost benchmark exists below country level, so the relocation-cost "
                 "delta is a zero placeholder, not an estimate. The incentive scenario keeps its real qualifying spend, incentive and net cost; it is not ranked against the base until "
                 "relocation completeness is evidenced."),
    }
