"""
canonical_executable_conformance.py

Registry-wide CANONICAL -> EXECUTABLE structural conformance check.

MECHANICAL VALIDATION, NOT RESEARCH. This never invents, promotes or edits a
program rule. It walks the live canonical registries and asserts the one
structural invariant the economics repair is built on:

    every registered program must EITHER expose a coherent executable
    pricing contract, OR fail closed with an exact, stated reason.

A program that prices with an incoherent contract, or that fails without a
reason, is the defect class this check exists to make impossible to ship.

Dimensions checked per program (only where the program declares the concept --
absence is reported as such, never treated as a violation to be fixed by
inventing a rule):

  authority              canonical coverage disposition, fail-closed
  rate / floor           a resolvable rate, and whether a guaranteed floor exists
  conditional ceiling    "up to X%" with no floor and an unevaluable condition
  qualifying base        rate_base_narrower_than_qpe (labour-only bases)
  dollar caps            per_project / annual allocation caps
  substantive eligibility  requirement profile presence
  territorial scope      jurisdiction code resolvable to a display name
  trace provenance       doctrine resolves to a real qualification doctrine

Run:  .venv/bin/python scripts/canonical_executable_conformance.py
"""
from __future__ import annotations

import sys
from collections import Counter

sys.path.insert(0, ".")

from app.data import program_rate_rules as prr  # noqa: E402  (import-order guard)
from app.calculators.allocation_pricing import _resolve_incentive_dollar_cap  # noqa: E402
from app.data.authority_coverage_registry import (  # noqa: E402
    blocks_economic_candidacy,
    coverage_state,
)
from app.data.program_requirements import get_program_requirements  # noqa: E402
from app.data.program_spend_rules import resolve_program_doctrine  # noqa: E402
from app.services.canonical_program_identity import canonical_jurisdiction_name  # noqa: E402

PROBE_QPE_USD = 5_000_000.0
PROBE_PRODUCTION_TYPE = "feature_film"


def classify(slug: str) -> dict:
    """One program's structural conformance record."""
    record: dict = {"slug": slug, "reasons": []}

    # 1. Authority disposition -- decisive and checked first.
    state = coverage_state(slug)
    record["coverage_state"] = state
    if blocks_economic_candidacy(slug):
        record["disposition"] = "FAILS_CLOSED"
        record["reasons"].append(f"authority:{state}")
        return record

    # 2. Rate resolution.
    rules = prr.get_rate_rules(slug)
    if not rules:
        record["disposition"] = "FAILS_CLOSED"
        record["reasons"].append("rate:no_rate_rules")
        return record

    resolution = prr.resolve_program_rate(
        slug, production_type=PROBE_PRODUCTION_TYPE, qpe_usd=PROBE_QPE_USD,
    )
    if resolution is None:
        record["disposition"] = "FAILS_CLOSED"
        record["reasons"].append("rate:conditions_unmet_for_probe")
        return record

    record["modeled_rate"] = resolution.modeled_rate
    record["has_guaranteed_floor"] = resolution.has_guaranteed_floor

    # 3. Qualifying base -- a labour-only base the engine cannot derive.
    narrower = sorted({
        condition.condition_id
        for rule in rules
        for condition in rule.conditions
        if condition.kind == "rate_base_narrower_than_qpe"
    })
    if narrower:
        record["disposition"] = "FAILS_CLOSED"
        record["reasons"].append(f"qualifying_base:narrower_than_qpe:{','.join(narrower)}")
        return record

    # 4. Conditional ceiling with no guaranteed floor.
    unevaluable = sorted({
        e.condition_id for e in resolution.conditions_evaluated if e.satisfied is None
    })
    if not resolution.has_guaranteed_floor and unevaluable:
        record["disposition"] = "FAILS_CLOSED"
        record["reasons"].append(f"rate:ceiling_without_floor:{','.join(unevaluable)}")
        return record

    # ── Priceable. Record the rest of the contract for coherence. ────────
    record["disposition"] = "PRICEABLE"

    cap_usd, cap_type, cap_basis = _resolve_incentive_dollar_cap(slug)
    record["dollar_cap_usd"] = cap_usd
    record["dollar_cap_type"] = cap_type
    record["dollar_cap_basis"] = cap_basis

    profile = get_program_requirements(slug)
    record["has_requirements_profile"] = profile is not None

    doctrine_resolution = resolve_program_doctrine(slug)
    record["doctrine"] = (
        doctrine_resolution.doctrine.value if doctrine_resolution else None
    )
    record["doctrine_basis"] = (
        doctrine_resolution.basis.value if doctrine_resolution else None
    )

    jurisdictions = sorted({r.jurisdiction_code for r in _doctrine_codes(slug)})
    record["jurisdictions"] = jurisdictions
    record["unnamed_jurisdictions"] = [
        code for code in jurisdictions if not canonical_jurisdiction_name(code)
    ]
    return record


def _doctrine_codes(slug: str):
    from app.data.executable_jurisdiction_registry import all_doctrine_records

    return [r for r in all_doctrine_records() if r.program_slug == slug]


def incoherences(record: dict) -> list[str]:
    """Structural incoherences in a PRICEABLE contract. A priceable program
    must be able to state its rate, its doctrine and a named jurisdiction."""
    problems = []
    if record["disposition"] != "PRICEABLE":
        if not record["reasons"]:
            problems.append("fails closed WITHOUT a stated reason")
        return problems
    if not record.get("modeled_rate"):
        problems.append("priceable with no modeled rate")
    if not record.get("doctrine"):
        problems.append("priceable with no resolved qualification doctrine")
    if record.get("unnamed_jurisdictions"):
        problems.append(
            f"priceable with unnamed jurisdiction(s): {record['unnamed_jurisdictions']}"
        )
    return problems


def main() -> int:
    slugs = sorted(prr._RULES_BY_PROGRAM)
    records = [classify(s) for s in slugs]

    dispositions = Counter(r["disposition"] for r in records)
    reason_kinds = Counter(
        reason.split(":", 1)[0]
        for r in records if r["disposition"] == "FAILS_CLOSED"
        for reason in r["reasons"]
    )

    print("=" * 72)
    print("CANONICAL -> EXECUTABLE STRUCTURAL CONFORMANCE")
    print("=" * 72)
    print(f"programs with registered rate rules : {len(records)}")
    for disposition, count in dispositions.most_common():
        print(f"  {disposition:<14} {count}")
    print()
    print("fail-closed reasons by kind:")
    for kind, count in reason_kinds.most_common():
        print(f"  {kind:<18} {count}")
    print()

    print("fail-closed detail:")
    for r in records:
        if r["disposition"] == "FAILS_CLOSED":
            print(f"  {r['slug']:<46} {r['reasons'][0]}")
    print()

    priceable = [r for r in records if r["disposition"] == "PRICEABLE"]
    capped = [r for r in priceable if r.get("dollar_cap_usd")]
    with_profile = [r for r in priceable if r.get("has_requirements_profile")]
    print(f"priceable programs                  : {len(priceable)}")
    print(f"  ... declaring a dollar cap        : {len(capped)}")
    print(f"  ... with a requirements profile   : {len(with_profile)}")
    print()

    problems = [(r["slug"], p) for r in records for p in incoherences(r)]
    print(f"STRUCTURAL INCOHERENCES: {len(problems)}")
    for slug, problem in problems:
        print(f"  {slug:<46} {problem}")
    print()
    print("RESULT:", "PASS" if not problems else "FAIL")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
