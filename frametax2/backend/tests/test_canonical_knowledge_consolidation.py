"""
test_canonical_knowledge_consolidation.py

CINEGLOBE — Canonical Knowledge Consolidation, Sections 8/11/20.

THE FAILURE CLASS THIS FILE EXISTS TO PREVENT
---------------------------------------------
Real, already-acquired program knowledge gets recorded in a NONCANONICAL
location (a jurisdiction-comparison profile's prose `notes`/`data_gaps`,
a validation document, a code comment) and is explicitly flagged there as
"not modeled". No canonical representation is ever created. The served
optimizer therefore cannot see it, and a later agent re-researches it
from scratch -- or, worse, reports it as missing.

Three real instances were found and recovered:
  - us_ny_film_credit's "Production Plus" uplift  (NY control)
  - ca_bc_dave        (BC's 16% animation/VFX/post credit)
  - au_pdv_offset     (Australia's 30% PDV Offset)

Each was already documented, verbatim and correctly, in
jurisdiction_comparison.py -- and each was invisible to the served path.

These tests lock in (1) that those three specific recoveries stay
canonical, and (2) the generic structural invariant that runtime legal/
economic truth is read from canonical knowledge only, never from
validation artifacts or research documents.
"""
from __future__ import annotations

import ast
import inspect

import pytest

from app.data.program_rate_rules import _RULES_BY_PROGRAM, resolve_program_rate


# ── Section 11: the three recovered stranded-knowledge programs ──────────

_BC_DAVE_FACTS = dict(
    evidenced_facts=frozenset({"ca_bc_dave_eligible_activity_confirmed"}),
    amount_facts={"ca_bc_dave_qualified_labour_usd": 500_000.0},
)


def test_recovered_stranded_program_is_canonically_registered():
    """RESTATED to the current primary rule (705d368f amount-gated discovery; BC DAVE is 16% of QUALIFIED BC LABOUR only, and only for genuine
    animation/VFX/post activity). ca_bc_dave stays registered and resolves through the SAME canonical rate path every program uses, but the tier is gated
    on two producer facts, so with neither supplied nothing is priced (never the segment's total QPE); with both supplied it resolves 16% on the stated
    labour amount, not on the 2,000,000 QPE."""
    assert "ca_bc_dave" in _RULES_BY_PROGRAM, "ca_bc_dave lost its canonical registration"
    assert resolve_program_rate("ca_bc_dave", production_type="feature_film", qpe_usd=2_000_000) is None, "no producer facts: must not price"
    r = resolve_program_rate("ca_bc_dave", production_type="feature_film", qpe_usd=2_000_000, **_BC_DAVE_FACTS)
    assert r is not None, "ca_bc_dave must resolve a real rate once its two producer facts are evidenced"
    assert r.modeled_rate == 0.16
    assert r.qpe_basis_used == 500_000.0, "the base is the stated qualified BC labour, never the 2,000,000 QPE"


@pytest.mark.parametrize("facts", [
    dict(evidenced_facts=frozenset({"ca_bc_dave_eligible_activity_confirmed"})),
    dict(amount_facts={"ca_bc_dave_qualified_labour_usd": 500_000.0}),
    dict(evidenced_facts=frozenset({"ca_bc_dave_eligible_activity_confirmed"}), amount_facts={"ca_bc_dave_qualified_labour_usd": 0.0}),
])
def test_bc_dave_needs_both_the_activity_and_a_positive_labour_amount(facts):
    assert resolve_program_rate("ca_bc_dave", production_type="feature_film", qpe_usd=2_000_000, **facts) is None


def test_au_pdv_offset_registration_superseded_by_b1_fail_closed_ruling():
    """RESTATED to the current ruling. The B1 fail-closed entry for au_pdv_offset was removed in 594c903a (authority coverage registry 1.8.0) on Codex's
    32-program primary-source reconciliation: a real, current, non-discretionary 30% rate with an official citation. The earlier fail-closed oracle is
    therefore stale. Current rule: no economic block; the 30% prices; the two eligibility conditions it cannot evidence (activity scope and the
    unrecorded minimum QAPE) hold it at USER_FACT_REQUIRED in the next test, so it prices without ever becoming a deterministic winner."""
    from app.data.authority_coverage_registry import economic_block_for_program

    assert "au_pdv_offset" in _RULES_BY_PROGRAM
    assert economic_block_for_program("au_pdv_offset") is None
    r = resolve_program_rate("au_pdv_offset", production_type="feature_film", qpe_usd=2_000_000)
    assert r is not None and r.modeled_rate == 0.30 and r.floor_rate == 0.30


@pytest.mark.parametrize("slug", ["ca_bc_dave", "au_pdv_offset"])
def test_recovered_program_carries_structured_provenance(slug):
    """Recovery is only complete if the authority came with it -- a
    recovered program with no provenance would just relocate the problem."""
    rules = _RULES_BY_PROGRAM[slug]
    assert rules
    for rule in rules:
        assert rule.provenance is not None, f"{slug}/{rule.tier_id} has no SourceProvenance"
        assert rule.provenance.issuing_authority


def test_recovered_program_cannot_silently_become_recommended():
    """RESTATED. ca_bc_dave depends on facts this engine does not collect, so the current rule is stronger than USER_FACT_REQUIRED: without the activity
    and labour facts the program does not resolve a rate at all, hence it can never reach a Recommended state; with both facts evidenced its conditions are
    satisfied and the qualification impact is None (the producer's statement, not an assumption, admits it)."""
    from app.services.canonical_evaluation import _rate_condition_qualification_impact

    assert resolve_program_rate("ca_bc_dave", production_type="feature_film", qpe_usd=2_000_000) is None
    r = resolve_program_rate("ca_bc_dave", production_type="feature_film", qpe_usd=2_000_000, **_BC_DAVE_FACTS)
    assert _rate_condition_qualification_impact(r) is None


def test_au_pdv_offset_cannot_become_recommended_superseded_by_b1_fail_closed():
    """RESTATED to the original CBA-002 oracle (the B1 fail-closed ruling it was superseded by was itself removed in 594c903a): PDV resolves its 30% but
    depends on project facts this engine does not collect (genuine PDV activity; the unrecorded minimum QAPE), so it is held at USER_FACT_REQUIRED -
    priced and disclosed, never a deterministic Recommended winner on unverified eligibility."""
    from app.calculators.canonical_qualification_result import QUAL_USER_FACT_REQUIRED
    from app.services.canonical_evaluation import _QUALIFICATION_ADMITS_RECOMMENDED, _rate_condition_qualification_impact

    r = resolve_program_rate("au_pdv_offset", production_type="feature_film", qpe_usd=2_000_000)
    impact = _rate_condition_qualification_impact(r)
    assert impact is not None, "au_pdv_offset's eligibility conditions must reach qualification"
    state, culprits = impact
    assert state == QUAL_USER_FACT_REQUIRED and state not in _QUALIFICATION_ADMITS_RECOMMENDED
    assert set(culprits) == {"au-pdv-activity-scope", "au-pdv-min-qape-not-recorded"}


def test_au_pdv_is_an_alternative_to_location_offset_never_an_addition():
    """Screen Australia: 'These three offsets are mutually exclusive.' The PDV Offset must never read as stackable with the Location Offset. RESTATED:
    with the fail-closed block gone, the guarantee is carried by the resolution itself - the mutually-exclusive condition is evaluated on the resolved
    rate and is disclosure-only (it must not price a combination), and it is also present on the canonical RateRule."""
    rule = _RULES_BY_PROGRAM["au_pdv_offset"][0]
    assert "mutually_exclusive_alternative_program" in {c.kind for c in rule.conditions}
    r = resolve_program_rate("au_pdv_offset", production_type="feature_film", qpe_usd=2_000_000)
    exclusive = [c for c in r.conditions_evaluated if c.kind == "mutually_exclusive_alternative_program"]
    assert len(exclusive) == 1 and exclusive[0].condition_state == "DISCLOSURE_ONLY"


def test_au_pdv_did_not_inherit_location_offsets_threshold():
    """PDV's real minimum QAPE is materially lower than the Location
    Offset's AUD $20M and is NOT recorded in this project. Borrowing the
    Location Offset's threshold in any form would wrongly exclude eligible
    productions.

    Codex final runtime remediation (au_location_offset, P0): the prior
    USD $10,000,000 conservative-bound surrogate is gone -- min_qpe_usd is
    now None and the real AUD 20,000,000 threshold is evaluated natively
    via a caller-evidenced amount fact (RateCondition.amount_fact_key/
    amount_fact_min), never a guessed USD conversion. PDV must still carry
    neither the old surrogate NOR the new native gate -- confirming no
    cross-program leakage in either representation."""
    location = _RULES_BY_PROGRAM["au_location_offset"][0]
    pdv = _RULES_BY_PROGRAM["au_pdv_offset"][0]
    assert location.min_qpe_usd is None
    location_native_condition = next(
        c for c in location.conditions if c.condition_id == "au-min-qape-native-aud"
    )
    assert location_native_condition.amount_fact_key == "au_location_qape_aud"
    assert location_native_condition.amount_fact_min == 20_000_000.0
    assert pdv.min_qpe_usd is None
    assert not any(c.amount_fact_key == "au_location_qape_aud" for c in pdv.conditions)


# ── Section 8/20: runtime reads canonical knowledge, never research docs ──

#: The served evaluation path. Legal/economic truth must come from
#: canonical data modules -- never from a validation/research artifact.
_SERVED_RUNTIME_MODULES = (
    "app.services.canonical_evaluation",
    "app.services.canonical_production_view",
    "app.calculators.allocation_pricing",
    "app.calculators.production_discovery",
    "app.calculators.canonical_role_qualification_bridge",
    "app.calculators.canonical_opportunity_bridge",
    "app.data.program_rate_rules",
    "app.data.program_authority_provenance",
)

#: Substrings that would indicate a runtime module reading a research or
#: validation artifact as production truth.
_RESEARCH_ARTIFACT_MARKERS = (
    "docs/validation",
    "CODEX_",
    "GEMINI_",
    "_CLOSEOUT.json",
    "VALIDATION_",
)


def test_served_runtime_never_opens_a_validation_or_research_artifact():
    """Section 8: research artifacts are evidence INPUTS to consolidation,
    never runtime truth stores. A served module may *cite* one in a
    comment (that is provenance); it may never `open()` one.

    Detected structurally (AST), not by string-matching the whole file, so
    a docstring reference like 'see docs/validation/...' stays legal while
    an actual file read does not."""
    import importlib

    for module_name in _SERVED_RUNTIME_MODULES:
        module = importlib.import_module(module_name)
        tree = ast.parse(inspect.getsource(module))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name not in ("open", "read_text", "load", "loads"):
                continue
            for arg in ast.walk(node):
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    for marker in _RESEARCH_ARTIFACT_MARKERS:
                        assert marker not in arg.value, (
                            f"{module_name} reads research/validation artifact "
                            f"{arg.value!r} at runtime -- canonical knowledge "
                            f"must be the only runtime truth source."
                        )


def test_every_registered_program_resolves_through_one_canonical_path():
    """Section 5: no program may exist in the registry yet be unreachable
    through the single canonical resolution function. Guards against a
    second, parallel knowledge path being introduced."""
    unreachable = []
    for slug, rules in _RULES_BY_PROGRAM.items():
        if not rules:
            unreachable.append(slug)
            continue
        production_types = {pt for r in rules for pt in r.production_types}
        if not production_types:
            unreachable.append(slug)
    assert not unreachable, f"programs with no resolvable canonical rule: {unreachable}"
