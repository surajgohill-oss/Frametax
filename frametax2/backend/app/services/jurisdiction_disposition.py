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
        recon: dict[str, int] = {}
        for r in marker_rows:
            c = r if "disposition" in r else {**r, **classify_jurisdiction_disposition(r)}
            disp[c["disposition"]] = disp.get(c["disposition"], 0) + 1
            causes[c["blocked_cause"]] += 1
            rc = (c.get("blocker_detail") or {}).get("reconciliation_class")
            if rc:
                recon[rc] = recon.get(rc, 0) + 1
        return {"disposition": disp, "causes": causes, "reconciliation": recon, "exact": True, "rows": expected}
    return {"disposition": disposition_totals(by_reason), "causes": cause_totals(by_reason), "exact": False, "rows": expected}


# ── EXACT PROGRAM BLOCKER (2026-10-02) ───────────────────────────────────────────────────────
# A served blocked row used to carry only the engine's generic sentence. The canonical registries already say
# precisely WHY a program is not guaranteed: the B1 discretionary ruling / authority-coverage state
# (economic_block_for_program), the program's own RateRule tiers and RateConditions (with the fact key each one
# needs), and the project's stored facts. This reads them -- no new rule data, no calculation -- and serves the
# exact unresolved proposition(s), the stored value found for each, and the stated rate ceiling, so a producer
# sees "Creative Saskatchewan awards are discretionary", never "authority uncertainty".

DETAIL_DISCRETIONARY_AWARD = "DISCRETIONARY_AWARD_NOT_CONFIRMED"
DETAIL_AWARD_CEILING_NO_FLOOR = "RATE_CEILING_WITH_NO_GUARANTEED_FLOOR"
DETAIL_PROJECT_FACTS_REQUIRED = "PROJECT_FACTS_REQUIRED_BY_RATE_RULE"
DETAIL_AUTHORITY_EXHAUSTED = "AUTHORITY_EXHAUSTED_FAIL_CLOSED"
DETAIL_NO_DEFENSIBLE_RATE = "NO_DEFENSIBLE_CURRENT_RATE_OR_AWARD_BASIS"
DETAIL_SUPERSEDED = "PROGRAM_SUPERSEDED"
DETAIL_QUALIFICATION = "MANDATORY_QUALIFICATION_GATE_FAILED"


def _program_label(slug: str | None) -> str:
    from app.data.executable_jurisdiction_registry import get_doctrine

    doctrine = get_doctrine(slug) if slug else None
    return (doctrine.program_name if doctrine and doctrine.program_name else (slug or "program").replace("_", " "))


#: ProjectFact storage prefixes (canonical_project_economics): a boolean RateCondition fact is stored as
#: "evidenced_program_fact:<key>", a numeric one as "amount_fact:<key>". Kept as literals only to avoid importing the
#: heavy evaluator module here; test_jurisdiction_disposition pins them to the canonical constants.
EVIDENCED_PREFIX = "evidenced_program_fact:"
AMOUNT_PREFIX = "amount_fact:"


def discretionary_award_fact_key(slug: str) -> str:
    """Stored (prefixed) ProjectFact key of a producer's confirmation that a discretionary award was granted."""
    return f"{EVIDENCED_PREFIX}{slug}__discretionary_award_confirmed"


def rate_rule_fact_keys(slug: str | None) -> set[str]:
    """Every STORED ProjectFact key (prefixed exactly as the evaluator reads it) the program's RateConditions /
    awarded-rate tiers depend on."""
    from app.data.program_rate_rules import get_rate_rules

    keys: set[str] = set()
    for rule in get_rate_rules(slug) if slug else ():
        if getattr(rule, "awarded_rate_fact_key", None):
            keys.add(AMOUNT_PREFIX + rule.awarded_rate_fact_key)
        for c in rule.conditions:
            if c.required_boolean_fact_key:
                keys.add(EVIDENCED_PREFIX + c.required_boolean_fact_key)
            if c.amount_fact_key:
                keys.add(AMOUNT_PREFIX + c.amount_fact_key)
    return keys


def _propositions(slug: str, facts: dict[str, str]) -> tuple[list[dict], list[str]]:
    from app.data.program_rate_rules import get_rate_rules

    props: list[dict] = []
    found: list[str] = []
    for rule in get_rate_rules(slug):
        if getattr(rule, "awarded_rate_fact_key", None):
            k = rule.awarded_rate_fact_key
            props.append({
                "condition_id": f"{rule.tier_id}-awarded-rate",
                "description": "The exact rate awarded to THIS production (the statutory figure is a ceiling, not an entitlement)",
                "kind": "awarded_rate_fact", "fact_key": k, "stored_value": facts.get(AMOUNT_PREFIX + k),
                "requirement": f"between {rule.awarded_rate_min} and {rule.awarded_rate_max}",
            })
        for c in rule.conditions:
            key = c.required_boolean_fact_key or c.amount_fact_key
            stored_key = (EVIDENCED_PREFIX + c.required_boolean_fact_key) if c.required_boolean_fact_key else (
                (AMOUNT_PREFIX + c.amount_fact_key) if c.amount_fact_key else None)
            stored = facts.get(stored_key) if stored_key else None
            if key and stored is not None:
                found.append(f"{key}={stored}")
            props.append({
                "condition_id": c.condition_id, "description": c.description, "kind": c.kind,
                "fact_key": key, "stored_value": stored,
                "amount_min": c.amount_fact_min, "local_labour_basis": getattr(c, "local_labour_basis", None),
                "requirement": (
                    f">= {c.amount_fact_min}" if c.amount_fact_min is not None
                    else "confirmed" if c.required_boolean_fact_key else None
                ),
            })
    return props, found


def _rate_summary(slug: str) -> dict:
    from app.data.program_rate_rules import get_rate_rules
    from app.data.executable_jurisdiction_registry import get_doctrine

    rules = get_rate_rules(slug)
    floors = [r.rate for r in rules if not r.is_band_ceiling]
    ceilings = [r.rate for r in rules if r.is_band_ceiling]
    doctrine = get_doctrine(slug)
    return {
        "stated_floor_rate": max(floors) if floors else None,
        "stated_ceiling_rate": max(ceilings) if ceilings else (max(floors) if floors else None),
        "has_guaranteed_floor_tier": bool(floors),
        "rate_rule_confidence": rules[0].confidence_tier if rules else None,
        "program_cap_usd": doctrine.annual_cap_usd if doctrine else None,
    }


NOT_APPLICABLE = "NOT_APPLICABLE"

# Reconciliation classes (runtime/fact-consumption reconciliation of every blocked row).
RECON_HARD = "GENUINE_HARD_FAILURE"
RECON_CEILING_NO_FLOOR = "CONDITIONAL_CEILING_NO_VALID_FLOOR"
RECON_MISSING_FACT = "MISSING_PROJECT_FACT"
RECON_DISCRETIONARY = "DISCRETIONARY_AWARD_ZERO_GUARANTEED"
RECON_AUTHORITY_EXHAUSTED = "AUTHORITY_EXHAUSTED_RATERULE_RETAINED"
RECON_NOT_APPLICABLE = "NOT_APPLICABLE_PRODUCTION_TYPE"
RECON_DISCONNECTED = "DISCONNECTED_EXISTING_FACT"
RECON_MISSING_CAPABILITY = "MISSING_CAPABILITY"
RECON_SLATE = "VALID_REFERENCE_ALTERNATIVE"


DETAIL_MIN_QPE = "MINIMUM_QUALIFYING_SPEND_NOT_MET"


def enrich_row_with_program_detail(row: dict, program_slug: str | None, facts: dict[str, str],
                                   production_type: str | None = None, qpe_usd: float | None = None,
                                   threshold_unreachable_reason: str | None = None) -> dict:
    """Adds the exact, registry-derived blocker to one already-classified row (mutates and returns it)."""
    from app.data.authority_coverage_registry import get_coverage_status
    from app.data.program_rate_rules import economic_block_for_program, get_rate_rules

    row["program_slug"] = program_slug
    row["program_name"] = _program_label(program_slug) if program_slug else None
    if not program_slug:
        row["blocker_detail"] = None
        return row
    block = economic_block_for_program(program_slug)
    coverage = get_coverage_status(program_slug)
    rates = _rate_summary(program_slug)
    props, found = _propositions(program_slug, facts)
    cls = row.get("rejection_reason_class") or ""
    status = row.get("candidate_status") or ""
    detail = None
    headline = None
    unresolved: list[dict] = []
    if status == "QUALIFICATION_HARD_FAIL":
        detail = DETAIL_QUALIFICATION
        headline = f"{row['program_name']}: a mandatory qualification gate failed (HARD_FAIL) -- see the role/qualification findings."
    elif block is not None and block.classification == "SUPERSEDED":
        detail = DETAIL_SUPERSEDED
        headline = f"{row['program_name']} is superseded by a current program and must not price as current."
    elif block is not None and block.classification in ("DISPLAY_ONLY_ZERO_GUARANTEED", "NON_GUARANTEED_SELECTIVE"):
        detail = DETAIL_DISCRETIONARY_AWARD
        unresolved = [p for p in props if p["kind"] == "discretionary_band"] or list(props)
        if not unresolved:
            # The rate rule states no condition at all: the only open proposition is the award itself.
            _k = f"{program_slug}__discretionary_award_confirmed"
            unresolved = [{
                "condition_id": "discretionary-award", "kind": "discretionary_award_confirmation",
                "description": "The program authority must confirm a discretionary award for THIS production, and its rate",
                "fact_key": _k, "stored_value": facts.get(EVIDENCED_PREFIX + _k), "requirement": "confirmed",
            }]
        streams = ""
        if rates["stated_floor_rate"] and rates["stated_ceiling_rate"] and rates["stated_floor_rate"] != rates["stated_ceiling_rate"]:
            streams = f" Stated rates: {rates['stated_floor_rate']:.0%} to {rates['stated_ceiling_rate']:.0%}."
        headline = (
            f"{row['program_name']} is a discretionary / selective award: whether this production receives an award "
            f"(and at what rate) is not established, so its guaranteed incentive is zero by the canonical ruling "
            f"({block.classification}).{streams}"
        )
    elif block is not None and block.classification == "FAIL_CLOSED":
        detail = DETAIL_AUTHORITY_EXHAUSTED
        headline = (
            f"{row['program_name']}: the accepted primary authority is exhausted -- it cannot state this program's "
            f"award or rate basis deterministically, so automatic pricing is off (existing RateRule retained, "
            f"{rates['rate_rule_confidence']} confidence)."
        )
    elif block is not None and block.classification == "UNPRICEABLE_AUTHORITY_INSUFFICIENT":
        detail = DETAIL_NO_DEFENSIBLE_RATE
        headline = f"{row['program_name']}: the primary-authority corpus captured no defensible current rate or award basis."
    elif cls == "PRICING_BLOCKED" and not rates["has_guaranteed_floor_tier"] and rates["stated_ceiling_rate"]:
        detail = DETAIL_AWARD_CEILING_NO_FLOOR
        unresolved = props
        headline = (
            f"{row['program_name']} states only an 'up to {rates['stated_ceiling_rate']:.0%}' ceiling with no "
            f"guaranteed floor tier; this production's award/qualifying conditions are not established."
        )
    elif cls == "PRICING_BLOCKED" and props:
        detail = DETAIL_PROJECT_FACTS_REQUIRED
        unresolved = [p for p in props if p["stored_value"] is None]
        headline = f"{row['program_name']}: its rate rule needs project facts that are not on file."
    elif cls == "STATUTORY_CONDITIONS_UNMET" and block is None and threshold_unreachable_reason:
        # Mandatory threshold(s) this production cannot reach even if EVERY project fact were confirmed.
        detail = DETAIL_MIN_QPE
        headline = f"{row['program_name']}: {threshold_unreachable_reason}"
        row["disposition"] = HARD_BLOCK
        row["blocked_cause"] = CAUSE_LEGAL_INELIGIBILITY
        row["hard_block_reason"] = headline
        row["engine_reason"] = row.get("missing_facts_reason")
        row["missing_facts_reason"] = None
    elif cls == "STATUTORY_CONDITIONS_UNMET" and block is None and production_type and qpe_usd is not None and any(
        r.min_qpe_usd is not None for r in get_rate_rules(program_slug)
    ) and qpe_usd < min(r.min_qpe_usd for r in get_rate_rules(program_slug)
                        if production_type in (r.production_types or ()) and r.min_qpe_usd is not None):
        # A mandatory minimum-QPE threshold the production's canonical qualifying spend does not reach: a confirmed
        # failed gate (the same class the evaluator already treats as hard), with the exact numbers.
        threshold = min(r.min_qpe_usd for r in get_rate_rules(program_slug)
                        if production_type in (r.production_types or ()) and r.min_qpe_usd is not None)
        detail = DETAIL_MIN_QPE
        headline = (
            f"{row['program_name']} requires at least ${threshold:,.2f} of qualifying spend; this production's "
            f"canonical qualifying spend is ${qpe_usd:,.2f}."
        )
        row["disposition"] = HARD_BLOCK
        row["blocked_cause"] = CAUSE_LEGAL_INELIGIBILITY
        row["hard_block_reason"] = headline
        row["engine_reason"] = row.get("missing_facts_reason")
        row["missing_facts_reason"] = None
    elif cls == "STATUTORY_CONDITIONS_UNMET" and block is None and any(p["stored_value"] is None for p in props):
        detail = DETAIL_PROJECT_FACTS_REQUIRED
        unresolved = [p for p in props if p["stored_value"] is None]
        headline = f"{row['program_name']}: its rate rule needs project facts that are not on file."
    # A program whose RateRule tiers are ALL scoped to other production types (e.g. an animation-only record on a
    # live-action feature) is not applicable to this production: a valid, non-blocking fact, never RED or AMBER.
    from app.data.program_rate_rules import get_rate_rules as _rules

    _prules = _rules(program_slug)
    if (
        production_type and _prules and block is None and detail is None
        and all(production_type not in (r.production_types or ()) for r in _prules)
    ):
        detail = "PROGRAM_NOT_APPLICABLE_TO_PRODUCTION_TYPE"
        applicable = sorted({t for r in _prules for t in (r.production_types or ())})
        headline = (
            f"{row['program_name']} applies only to {', '.join(applicable)} productions; this production is "
            f"{production_type}. Not a blocker for this production."
        )
        row["disposition"] = NOT_APPLICABLE
        row["blocked_cause"] = CAUSE_OTHER
        row["engine_reason"] = row.get("missing_facts_reason")
        row["missing_facts_reason"] = None
        row["hard_block_reason"] = None
    recon = {
        DETAIL_QUALIFICATION: RECON_HARD, DETAIL_SUPERSEDED: RECON_HARD, DETAIL_MIN_QPE: RECON_HARD,
        DETAIL_DISCRETIONARY_AWARD: RECON_DISCRETIONARY, DETAIL_AWARD_CEILING_NO_FLOOR: RECON_CEILING_NO_FLOOR,
        DETAIL_PROJECT_FACTS_REQUIRED: RECON_MISSING_FACT, DETAIL_AUTHORITY_EXHAUSTED: RECON_AUTHORITY_EXHAUSTED,
        DETAIL_NO_DEFENSIBLE_RATE: RECON_AUTHORITY_EXHAUSTED,
        "PROGRAM_NOT_APPLICABLE_TO_PRODUCTION_TYPE": RECON_NOT_APPLICABLE,
    }.get(detail)
    row["blocker_detail"] = {
        "reconciliation_class": recon,
        "kind": detail,
        "headline": headline,
        "canonical_disposition": block.classification if block is not None else None,
        "coverage_state": coverage.state if coverage is not None else None,
        "unresolved_propositions": unresolved,
        "stored_facts_found": found,
        "guaranteed_floor": (
            "none (canonical ruling: guaranteed value is zero for a discretionary award)"
            if detail == DETAIL_DISCRETIONARY_AWARD
            else "none (the RateRule states only an 'up to' ceiling)" if not rates["has_guaranteed_floor_tier"]
            else f"{rates['stated_floor_rate']:.0%} stated, not priced (blocked above)"
        ),
        "potential_ceiling_rate": rates["stated_ceiling_rate"],
        "ceiling_unlocked_by": [p["condition_id"] for p in unresolved],
        "stated_rates": rates,
        "provenance_axis": (
            f"RateRule confidence {rates['rate_rule_confidence']}"
            + ("; its structured provenance is incomplete, which is a production-acceptance warning only and is NOT what blocks this program"
               if rates["rate_rule_confidence"] != "VERIFIED" else "; provenance is not the cause of this disposition")
        ),
    }
    if headline and row.get("disposition") == NEEDS_FACTS:
        row["engine_reason"] = row.get("missing_facts_reason")
        row["missing_facts_reason"] = headline
        if detail == DETAIL_DISCRETIONARY_AWARD:
            row["blocked_cause"] = CAUSE_MISSING_FACT
        elif detail == DETAIL_AWARD_CEILING_NO_FLOOR or detail == DETAIL_PROJECT_FACTS_REQUIRED:
            row["blocked_cause"] = CAUSE_MISSING_FACT
        elif detail in (DETAIL_AUTHORITY_EXHAUSTED, DETAIL_NO_DEFENSIBLE_RATE):
            row["blocked_cause"] = CAUSE_AUTHORITY
    return row
