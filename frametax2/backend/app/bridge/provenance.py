"""
Rule-provenance matrix (spec section 10).

Built ENTIRELY from data already in the repository — no new research, no
provider calls. Per the spec: "Do not bulk-research all programs solely
for this matrix."

Two real, already-verified mechanisms determine `machine_enforced`:
  1. program_rate_rules.py::resolve_program_rate()'s tier-selection loop
     (lines ~742-748) — the ONLY RateCondition kind that actually
     excludes a tier from `eligible` is "min_qpe_usd". Every other kind
     (cultural_test_required, min_spend_pct_of_total_budget,
     discretionary_band, no_sponsorship_in_qpe, ...) falls into the
     function's own generic `else`/`satisfied=None` branch — recorded
     as a disclosed condition/citation, never gating. Confirmed by
     reading that function directly this session, not assumed.
  2. Whether app/calculators/cultural_test_rules.py,
     creative_qualification_engine.py, or evaluate_qualification_tests.py
     are imported anywhere in the served path (qualification_derivation.py,
     allocation_pricing.py, little_utopia_state.py, production_discovery.py)
     — confirmed via grep this session: they are NOT. Cultural-test
     verification exists as dormant, unwired calculators; the served
     pipeline does not enforce it anywhere.

`disclosed_in_ui` is true only for a field a populated
ProgramRequirementsProfile actually sets (None means "not stated",
which Inspector.jsx already renders as such — see Task 93's UI wiring).
"""
from __future__ import annotations

from app.bridge.schema import ProvenanceGapClassification, RuleProvenanceRecord

# rule_field -> RateCondition kind(s) that, if present on the program's
# rate rules, represent that fact being DISCLOSED at the pricing-engine
# level (not necessarily enforced — see MACHINE_ENFORCED_KINDS below).
_DISCLOSING_CONDITION_KINDS: dict[str, tuple[str, ...]] = {
    "minimum_spend": ("min_qpe_usd", "min_spend_pct_of_total_budget"),
    "cultural_test": ("cultural_test_required",),
    "stacking_restriction": ("mutually_exclusive_alternative_program",),
}

# The ONLY RateCondition kind confirmed (by reading resolve_program_rate's
# tier-selection loop) to actually exclude a tier — i.e. genuinely gate
# pricing, not just get recorded in the evaluation trace.
MACHINE_ENFORCED_CONDITION_KINDS: frozenset[str] = frozenset({"min_qpe_usd"})

# ProgramRequirementsProfile field(s) that back each spec rule_field, for
# the disclosed_in_ui check.
_PROFILE_FIELDS: dict[str, tuple[str, ...]] = {
    "application_timing": ("application_deadline",),
    "preapproval": ("preapproval_mandatory",),
    "local_entity": ("local_entity_required",),
    "cultural_test": ("cultural_test_required", "cultural_test_threshold"),
    "minimum_spend": ("min_local_spend_usd", "min_total_budget_usd"),
    "filing_deadline": ("audit_or_final_certification_deadline",),
    "audit": ("audit_required", "cpa_or_approved_auditor_required"),
    "transfer_monetization": ("refundable", "transferable"),
    "stacking_restriction": ("additional_facts",),  # no dedicated field yet — see notes
}

RULE_FIELDS: tuple[str, ...] = tuple(_PROFILE_FIELDS.keys())


def _profile_discloses(profile, field_names: tuple[str, ...]) -> bool:
    if profile is None:
        return False
    for name in field_names:
        value = getattr(profile, name, None)
        if name == "additional_facts":
            continue  # never counted as disclosure on its own — too unstructured to assert
        if value is not None:
            return True
    return False


def build_provenance_matrix() -> list[RuleProvenanceRecord]:
    """One record per (executable jurisdiction, rule_field) — 110 x 9 =
    990 records, all computed from already-loaded, already-verified data."""
    import app.data.program_rate_rules  # circular-import order warm-up (documented codebase quirk)
    from app.data.canonical_executable_registry import canonical_executable_jurisdictions
    from app.data.program_rate_rules import get_rate_rules
    from app.data.program_requirements import get_program_requirements

    records: list[RuleProvenanceRecord] = []
    for code, entry in canonical_executable_jurisdictions().items():
        slug = entry.primary_program_slug
        rules = get_rate_rules(slug)
        present_kinds = {c.kind for r in rules for c in r.conditions}
        profile = get_program_requirements(slug)

        for field_name in RULE_FIELDS:
            disclosing_kinds = _DISCLOSING_CONDITION_KINDS.get(field_name, ())
            kind_present = bool(present_kinds & set(disclosing_kinds))
            machine_enforced = bool(present_kinds & MACHINE_ENFORCED_CONDITION_KINDS & set(disclosing_kinds))
            disclosed = _profile_discloses(profile, _PROFILE_FIELDS[field_name])
            changes_qpe = field_name in ("minimum_spend",) and machine_enforced
            changes_pricing = machine_enforced

            if field_name == "minimum_spend" and "min_qpe_usd" in present_kinds:
                gap = (
                    ProvenanceGapClassification.ENFORCED_AND_DISCLOSED if disclosed
                    else ProvenanceGapClassification.ENFORCED_NOT_DISCLOSED
                )
            elif kind_present or disclosed:
                gap = ProvenanceGapClassification.DISCLOSED_NOT_ENFORCED
            else:
                gap = ProvenanceGapClassification.MISSING

            records.append(RuleProvenanceRecord(
                program_slug=slug, jurisdiction_code=code, rule_field=field_name,
                stored_where=(
                    ("program_rate_rules.py (RateCondition)" if kind_present else "")
                    + (", " if kind_present and disclosed else "")
                    + ("program_requirements.py" if disclosed else "")
                ) or None,
                machine_enforced=machine_enforced,
                failure_disqualifies=(
                    True if (field_name == "minimum_spend" and machine_enforced) else None
                ),
                changes_qpe=changes_qpe,
                changes_pricing=changes_pricing,
                warning_only=kind_present and not machine_enforced,
                disclosed_in_ui=disclosed,
                source_confidence=profile.evidence.source_type.value if (profile and profile.evidence) else None,
                gap_classification=gap,
            ))
    return records


def hard_gate_unknown_programs(matrix: list[RuleProvenanceRecord] | None = None) -> dict[str, list[str]]:
    """Spec: 'Explicitly determine whether any of the remaining 93
    programs can be recommended despite missing [hard gate fields]' —
    a program appears here if ANY of its hard-gate-relevant fields
    (preapproval, local_entity, cultural_test, minimum_spend,
    stacking_restriction) is classified MISSING (neither enforced nor
    disclosed) — never silently assumed benign."""
    matrix = matrix if matrix is not None else build_provenance_matrix()
    hard_gate_fields = {"preapproval", "local_entity", "cultural_test", "minimum_spend", "stacking_restriction"}
    out: dict[str, list[str]] = {}
    for r in matrix:
        if r.rule_field in hard_gate_fields and r.gap_classification == ProvenanceGapClassification.MISSING:
            out.setdefault(r.program_slug, []).append(r.rule_field)
    return out


def provenance_summary(matrix: list[RuleProvenanceRecord] | None = None) -> dict[str, int]:
    matrix = matrix if matrix is not None else build_provenance_matrix()
    out: dict[str, int] = {}
    for r in matrix:
        out[r.gap_classification.value] = out.get(r.gap_classification.value, 0) + 1
    return out
