"""
Machine-readable rule-coverage report (Final Backend Closeout — Phase 5).

The canonical backend roadmap: what qualification, pricing, and optimizer
rules are implemented, what is disclosed-only, what is missing, what is
hard-coded, and which jurisdictions/programs remain incomplete.

Built ENTIRELY from data already loaded in the repository — the canonical
executable registry, the statutory rate rules, the requirements profiles, and
the rule-provenance matrix. No research, no network, no provider calls, no
fabricated figures. Running it twice yields identical output (a determinism
test asserts this).

    python -m app.optimization.rule_coverage_report        # prints JSON
    python -m app.optimization.rule_coverage_report --write # writes the JSON
                                                            # doc alongside the
                                                            # capability ledger
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any

REPORT_VERSION = "closeout-phase5-v1"


# Real, code-documented assumptions the served engine makes. Each is grounded
# in a specific, greppable location — none is invented for this report.
HARD_CODED_ASSUMPTIONS: tuple[dict[str, str], ...] = (
    {
        "assumption": "Financing cost is $0 unless a producer explicitly supplies financing inputs.",
        "location": "app/calculators/allocation_pricing.py (financing_cost_usd default)",
        "kind": "conservative_default",
    },
    {
        "assumption": "Exactly one incentive program is priced per jurisdiction segment; "
                      "additional-program stacks enter only via enumerate_segment_program_stacks() "
                      "when real multi-program knowledge exists.",
        "location": "app/calculators/allocation_pricing.py (stacking_note)",
        "kind": "structural_invariant",
    },
    {
        "assumption": "min_qpe_usd (minimum spend) is the ONLY qualification condition that "
                      "machine-excludes a rate tier; all other conditions are recorded but never gate.",
        "location": "app/data/program_rate_rules.py::resolve_program_rate tier-selection loop",
        "kind": "enforcement_boundary",
    },
    {
        "assumption": "The off-budget Mauritius in-kind post FMV is never QPE and never a budget "
                      "line; it enters economics only as a replacement-cost normalization when a "
                      "structure moves that work out of Mauritius.",
        "location": "app/calculators/allocation_pricing.py (inkind_note)",
        "kind": "modeling_normalization",
    },
    {
        "assumption": "The controlling gross budget is the source document's stated Grand Total "
                      "($4,364,393), not the $4,364,395 leaf-account sum; the $2 variance is disclosed.",
        "location": "app/data/little_utopia_real_budget.py (RECONCILIATION_NOTE)",
        "kind": "disclosed_source_variance",
    },
    {
        "assumption": "Belgium tax-shelter cap and Spain Canary-Islands rate are left UNKNOWN on "
                      "unresolved source conflicts rather than guessed.",
        "location": "docs/architecture/CAPABILITY_LEDGER.md (BE/ES entries)",
        "kind": "disclosed_unknown",
    },
)


# The optimizer capabilities that ARE implemented in the served path — each a
# real, tested engine, listed so the roadmap shows what freezes at this point.
IMPLEMENTED_OPTIMIZER_RULES: tuple[str, ...] = (
    "single-jurisdiction baseline structure generation",
    "full-relocation structure family (every executable alternative)",
    "component-relocation structure family (post/VFX/music routing)",
    "treaty co-production structure composition on election (priced only when a real "
    "treaty instrument covers the pair; UNAVAILABLE otherwise, never forced)",
    "account->jurisdiction allocation with conservation checks",
    "per-segment QPE derivation from statutory spend rules",
    "statutory rate resolution (floor + modeled ceiling; min_qpe_usd gating)",
    "NPC computation (verified / with-adjustments / conservative floor)",
    "travel, FX, local-cost, in-kind replacement normalizations",
    "conditional (non-priceable) funding-avenue surfacing without entering NPC",
    "structure compatibility engine (mutual-exclusivity, membership gates)",
    "deterministic NPC-primary ranking with pursuable-avenue tie-break",
    "recommendation-confidence status (CONFIRMED/CONDITIONAL/PRICED/"
    "PRICED_BUT_QUALIFICATION_PENDING/UNAVAILABLE/UNKNOWN)",
    "first-class contingency treatment",
)


def build_rule_coverage_report() -> dict[str, Any]:
    """Compute the full report from already-loaded data. Pure/deterministic."""
    import app.data.program_rate_rules  # circular-import order warm-up
    from app.bridge.provenance import (
        RULE_FIELDS,
        build_provenance_matrix,
        hard_gate_unknown_programs,
    )
    from app.data.canonical_executable_registry import canonical_executable_jurisdictions
    from app.data.program_rate_rules import get_rate_rules
    from app.data.program_requirements import get_program_requirements
    from app.optimization.recommendation_confidence import HARD_GATE_FIELDS

    executable = canonical_executable_jurisdictions()

    # ── Pricing-rule coverage ──────────────────────────────────────────────
    priceable = 0
    profiled = 0
    jurisdictions_without_profile: list[str] = []
    for code, entry in sorted(executable.items()):
        slug = entry.primary_program_slug
        if get_rate_rules(slug):
            priceable += 1
        if get_program_requirements(slug) is not None:
            profiled += 1
        else:
            jurisdictions_without_profile.append(code)

    # ── Qualification-rule coverage (from the provenance matrix) ────────────
    matrix = build_provenance_matrix()
    per_field: dict[str, Counter] = defaultdict(Counter)
    for record in matrix:
        per_field[record.rule_field][record.gap_classification.value] += 1

    machine_enforced_fields = sorted({
        r.rule_field for r in matrix if r.machine_enforced
    })
    disclosed_only_fields = sorted({
        r.rule_field for r in matrix
        if not r.machine_enforced and r.disclosed_in_ui
    })
    never_implemented_fields = sorted(
        f for f in RULE_FIELDS
        if all(r.gap_classification.value == "missing"
               for r in matrix if r.rule_field == f)
    )

    hard_gate_unknown = hard_gate_unknown_programs()

    # ── Global catalog completeness ────────────────────────────────────────
    try:
        from app.data.global_inventory import ALL_PROGRAMS
        total_catalog_programs = len(ALL_PROGRAMS)
    except Exception:  # pragma: no cover - inventory always importable in practice
        total_catalog_programs = None

    discovery_only = (
        total_catalog_programs - priceable
        if total_catalog_programs is not None else None
    )

    return {
        "report_version": REPORT_VERSION,
        "generated_from": "already-loaded repository data only — no research, no network, no provider calls",
        "summary": {
            "executable_jurisdictions": len(executable),
            "priceable_primary_programs": priceable,
            "primary_programs_with_requirements_profile": profiled,
            "primary_programs_without_requirements_profile": len(jurisdictions_without_profile),
            "total_catalog_programs": total_catalog_programs,
            "discovery_only_programs_estimate": discovery_only,
            "machine_enforced_qualification_fields": machine_enforced_fields,
        },
        "pricing_rules": {
            "executable_jurisdictions_all_price": priceable == len(executable),
            "priceable_primary_programs": priceable,
            "sole_machine_enforced_qualification_gate": "min_qpe_usd (minimum spend)",
            "note": "Every executable jurisdiction's primary program resolves a statutory "
                    "rate for a real production type + QPE. Rates never come from a budget's "
                    "own rebate line (Rule 2); conflicts are reported, not absorbed (Rule 5).",
        },
        "qualification_rules": {
            "rule_fields": list(RULE_FIELDS),
            "per_field_gap_distribution": {f: dict(per_field[f]) for f in RULE_FIELDS},
            "machine_enforced_fields": machine_enforced_fields,
            "disclosed_only_fields": disclosed_only_fields,
            "never_implemented_fields": never_implemented_fields,
            "hard_gate_fields_used_for_confidence": list(HARD_GATE_FIELDS),
            "programs_with_at_least_one_unknown_hard_gate": len(hard_gate_unknown),
        },
        "optimizer_rules": {
            "implemented": list(IMPLEMENTED_OPTIMIZER_RULES),
            "deterministic": True,
        },
        "incomplete": {
            "jurisdictions_without_requirements_profile_count": len(jurisdictions_without_profile),
            "jurisdictions_without_requirements_profile": jurisdictions_without_profile,
            "discovery_only_programs_estimate": discovery_only,
        },
        "hard_coded_assumptions": [dict(a) for a in HARD_CODED_ASSUMPTIONS],
        "roadmap": [
            "Populate requirements profiles for the "
            f"{len(jurisdictions_without_profile)} executable jurisdictions that have none, "
            "so cultural-test / preapproval / local-entity / timing gates become disclosed "
            "(and, where representable, enforced) rather than unknown.",
            "Promote DISCOVERY-only catalog programs to executable by sourcing a statutory "
            "RateRule per primary source (the completed 110 set is the model).",
            "If a jurisdiction's mandatory hard gate can be machine-evaluated from production "
            "facts (as min_qpe_usd already is), wire it into resolve_program_rate so CONDITIONAL "
            "can graduate to CONFIRMED for that program.",
            "Resolve the disclosed UNKNOWNs (Belgium cap, Spain Canary-Islands rate) when a "
            "non-conflicting primary source becomes available.",
        ],
    }


def _write_report(report: dict[str, Any]) -> str:
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    # backend/app/optimization -> repo docs/architecture
    dest = os.path.normpath(os.path.join(
        here, "..", "..", "..", "docs", "architecture", "RULE_COVERAGE_REPORT.json"))
    with open(dest, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return dest


if __name__ == "__main__":
    import sys

    report = build_rule_coverage_report()
    if "--write" in sys.argv:
        path = _write_report(report)
        print(f"Wrote {path}")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
