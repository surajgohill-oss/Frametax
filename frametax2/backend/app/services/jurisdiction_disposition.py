"""SHARED JURISDICTION DISPOSITION (2026-10-01) -- the one served classification of a blocked /
unpriced optimizer jurisdiction row into the two producer-facing outcomes the Globe, Inspector and
counters must agree on:

  HARD_BLOCK   (RED / Unavailable)       -- a CONFIRMED hard prohibition or a FAILED mandatory gate.
  NEEDS_FACTS  (AMBER / Needs more facts) -- anything unresolved: missing facts, preapproval,
                                            discretionary/competitive award, rate/ceiling
                                            confirmation, unresolved eligibility or authority.

It is a pure reader of the already-persisted candidate status / rejection class / engine reason
(no new calculation, no jurisdiction-specific branch). Red requires affirmative evidence in the
row; absence of resolution is never red. Serving-time only (outside the fingerprint digest).
"""
from __future__ import annotations

HARD_BLOCK = "HARD_BLOCK"
NEEDS_FACTS = "NEEDS_FACTS"

# Exactly one cause per blocked disposition (the audit taxonomy).
CAUSE_USER_EXCLUSION = "USER_LOCATION_EXCLUSION"
CAUSE_LEGAL_INELIGIBILITY = "CONFIRMED_LEGAL_PROGRAM_INELIGIBILITY"
CAUSE_MISSING_FACT = "MISSING_PROJECT_FACT_OR_CONFIRMATION"
CAUSE_FIT_CONFLICT = "SCRIPT_PRODUCTION_FIT_CONFLICT"
CAUSE_MISSING_CAPABILITY = "MISSING_LOCATION_CAPABILITY_DATA"
CAUSE_AUTHORITY = "AUTHORITY_PROVENANCE_UNCERTAINTY"
CAUSE_MAPPING_DEFECT = "MAPPING_SERVING_DEFECT"
CAUSE_OTHER = "OTHER"
ALL_CAUSES = (CAUSE_USER_EXCLUSION, CAUSE_LEGAL_INELIGIBILITY, CAUSE_MISSING_FACT, CAUSE_FIT_CONFLICT,
              CAUSE_MISSING_CAPABILITY, CAUSE_AUTHORITY, CAUSE_MAPPING_DEFECT, CAUSE_OTHER)

_NEEDS_CAUSE_BY_KIND = {
    "discretionary_or_competitive_award": CAUSE_MISSING_FACT,
    "rate_or_award_confirmation_required": CAUSE_MISSING_FACT,
    "preapproval_required": CAUSE_MISSING_FACT,
    "unresolved_eligibility_or_authority": CAUSE_AUTHORITY,
    "authority_insufficient_to_price": CAUSE_AUTHORITY,
    "pricing_input_unavailable": CAUSE_OTHER,   # exact reason is carried verbatim (e.g. an FX input not sourced)
}

#: Candidate statuses that are themselves a failed mandatory gate.
_HARD_STATUSES = {
    "QUALIFICATION_HARD_FAIL": "A mandatory qualification gate failed (HARD_FAIL).",
}

#: Rejection classes that are an affirmative prohibition / failed mandatory gate.
_HARD_CLASSES = {
    "SUPERSEDED": "The program is superseded per the canonical authority-coverage registry and cannot be used.",
    "PAIRWISE_INCOMPATIBLE": "A prohibited program combination (mutually exclusive programs).",
    "MUTUALLY_EXCLUSIVE_MEMBER_PAIR": "A prohibited program combination (mutually exclusive programs).",
    "MINIMUM_SPEND_FAIL": "A mandatory minimum-spend threshold is not met.",
    "THRESHOLD_NOT_MET": "A mandatory program threshold is not met.",
    "QUALIFICATION_HARD_FAIL": "A mandatory qualification gate failed (HARD_FAIL).",
}

#: Producer-readable kind for the NEEDS_FACTS outcomes (engine reason always carried verbatim).
_NEEDS_KIND_BY_CLASS = {
    "NON_GUARANTEED_SELECTIVE": "discretionary_or_competitive_award",
    "AUTHORITY_UNRESOLVED_NON_PRICEABLE": "unresolved_eligibility_or_authority",
    "UNPRICEABLE_AUTHORITY_INSUFFICIENT": "authority_insufficient_to_price",
    "UNRESOLVED_NO_AUTHORITY": "authority_insufficient_to_price",
    "STATUTORY_CONDITIONS_UNMET": "unresolved_eligibility_or_authority",
}


def _needs_kind(candidate_status: str, cls: str, text: str) -> str:
    if cls in _NEEDS_KIND_BY_CLASS:
        return _NEEDS_KIND_BY_CLASS[cls]
    low = text.lower()
    if "rate ceiling" in low or "award condition" in low or "not guaranteed" in low:
        return "rate_or_award_confirmation_required"
    if "preapproval" in low or "pre-approval" in low:
        return "preapproval_required"
    if "cannot be safely converted" in low or "no sourced fx" in low:
        return "pricing_input_unavailable"
    if "eligibility" in low or "minimum-spend" in low or "did not resolve" in low:
        return "unresolved_eligibility_or_authority"
    return "unresolved_eligibility_or_authority"


def classify_jurisdiction_disposition(row: dict) -> dict:
    """Return the served disposition fields for one blocked/unpriced row (never mutates it)."""
    status = row.get("candidate_status") or ""
    cls = row.get("rejection_reason_class") or ""
    text = " ".join(str(row.get("reason") or "").split())
    if status in _HARD_STATUSES or cls in _HARD_CLASSES:
        why = _HARD_STATUSES.get(status) or _HARD_CLASSES[cls]
        return {
            "disposition": HARD_BLOCK,
            "blocked_cause": CAUSE_LEGAL_INELIGIBILITY,
            "disposition_kind": (cls or status).lower(),
            "hard_block_reason": f"{why}" + (f" Engine: {text}" if text else ""),
            "missing_facts_reason": None,
        }
    kind = _needs_kind(status, cls, text)
    low = text.lower()
    cause = CAUSE_MISSING_CAPABILITY if ("capability" in low and ("missing" in low or "not assessable" in low or "no capability" in low)) \
        else _NEEDS_CAUSE_BY_KIND.get(kind, CAUSE_OTHER)
    return {
        "disposition": NEEDS_FACTS,
        "blocked_cause": cause,
        "disposition_kind": kind,
        "hard_block_reason": None,
        "missing_facts_reason": text or "Not enough established facts to price or confirm this jurisdiction.",
    }


def annotate_rows(rows: list[dict]) -> list[dict]:
    for r in rows:
        r.update(classify_jurisdiction_disposition(r))
    return rows


#: by_reason groups that are never a jurisdiction marker (search accounting / opportunities / the
#: summarized plain-rejection mass).
_NOT_A_MARKER = {"CO_PRO_OPPORTUNITY", "DOMINATED_WITH_PROOF", "RULE_REJECTED"}


def disposition_totals(by_reason: list[dict]) -> dict[str, int]:
    """Exact HARD_BLOCK / NEEDS_FACTS totals over the retained blocked groups, from the generation
    summary's own (status, class) counts -- the same classifier, so counters equal the rows."""
    totals = {HARD_BLOCK: 0, NEEDS_FACTS: 0}
    for g in by_reason or []:
        if g.get("candidate_status") in _NOT_A_MARKER:
            continue
        d = classify_jurisdiction_disposition(
            {"candidate_status": g.get("candidate_status"), "rejection_reason_class": g.get("rejection_reason_class")}
        )["disposition"]
        totals[d] += int(g.get("count") or 0)
    return totals


def cause_totals(by_reason: list[dict]) -> dict[str, int]:
    """Exact blocked-row totals per single cause, from the generation summary's (status, class) counts."""
    totals = {c: 0 for c in ALL_CAUSES}
    for g in by_reason or []:
        if g.get("candidate_status") in _NOT_A_MARKER:
            continue
        c = classify_jurisdiction_disposition(
            {"candidate_status": g.get("candidate_status"), "rejection_reason_class": g.get("rejection_reason_class")}
        )["blocked_cause"]
        totals[c] += int(g.get("count") or 0)
    return totals


def blocked_totals(rows: list[dict], by_reason: list[dict]) -> dict:
    """Exact HARD_BLOCK / NEEDS_FACTS and per-cause totals. The retained blocked rows are the
    authoritative source (the classification reads the engine's reason text); they are used whenever
    the served page demonstrably contains EVERY retained blocked group (row count == the generation
    summary's exact group counts). Otherwise the (status, class)-level counts are served and flagged
    `exact: False`."""
    marker_rows = [r for r in rows if r.get("candidate_status") not in _NOT_A_MARKER]
    expected = sum(int(g.get("count") or 0) for g in (by_reason or []) if g.get("candidate_status") not in _NOT_A_MARKER)
    if len(marker_rows) == expected:
        disp = {HARD_BLOCK: 0, NEEDS_FACTS: 0}
        causes = {c: 0 for c in ALL_CAUSES}
        for r in marker_rows:
            c = r if "disposition" in r else {**r, **classify_jurisdiction_disposition(r)}
            disp[c["disposition"]] += 1
            causes[c["blocked_cause"]] += 1
        return {"disposition": disp, "causes": causes, "exact": True, "rows": expected}
    return {"disposition": disposition_totals(by_reason), "causes": cause_totals(by_reason), "exact": False, "rows": expected}
