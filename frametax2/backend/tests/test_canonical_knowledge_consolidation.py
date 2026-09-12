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

@pytest.mark.parametrize("slug,expected_rate", [
    ("ca_bc_dave", 0.16),
])
def test_recovered_stranded_program_is_canonically_registered(slug, expected_rate):
    """Each recovered program must resolve through the SAME canonical rate
    path every other program uses -- never a special case."""
    assert slug in _RULES_BY_PROGRAM, f"{slug} lost its canonical registration"
    r = resolve_program_rate(slug, production_type="feature_film", qpe_usd=2_000_000)
    assert r is not None, f"{slug} must resolve a real rate"
    assert r.modeled_rate == expected_rate


def test_au_pdv_offset_registration_superseded_by_b1_fail_closed_ruling():
    """SUPERSEDED (Codex bounded remediation, B1 discretionary ruling,
    GLOBAL_PROGRAM_DISCRETIONARY_ARCHITECTURE_RULING_CODEX.csv):
    au_pdv_offset was previously asserted to resolve a deterministic 0.30
    rate in this same parametrized test. Codex's accepted ruling
    reclassifies au_pdv_offset FAIL_CLOSED -- authority is insufficient to
    price it deterministically, and the B4 central authority gate
    (authority_coverage_registry.economic_block_for_program) now refuses it
    BEFORE any rule lookup. This is the regression oracle for the new
    behavior: the canonical registration (RateRule, provenance) remains
    intact for traceability, but resolve_program_rate() must return None,
    never the old 0.30 figure."""
    from app.data.authority_coverage_registry import economic_block_for_program
    from app.data.program_rate_rules import (
        RATE_FAILURE_AUTHORITY_EXHAUSTED,
        classify_rate_resolution_failure,
    )

    assert "au_pdv_offset" in _RULES_BY_PROGRAM, "canonical registration must survive the block"
    block = economic_block_for_program("au_pdv_offset")
    assert block is not None
    assert block.classification == "FAIL_CLOSED"
    r = resolve_program_rate("au_pdv_offset", production_type="feature_film", qpe_usd=2_000_000)
    assert r is None, "au_pdv_offset must never auto-price under the B1 fail-closed ruling"
    failure = classify_rate_resolution_failure("au_pdv_offset", "feature_film", 2_000_000)
    assert failure == RATE_FAILURE_AUTHORITY_EXHAUSTED


@pytest.mark.parametrize("slug", ["ca_bc_dave", "au_pdv_offset"])
def test_recovered_program_carries_structured_provenance(slug):
    """Recovery is only complete if the authority came with it -- a
    recovered program with no provenance would just relocate the problem."""
    rules = _RULES_BY_PROGRAM[slug]
    assert rules
    for rule in rules:
        assert rule.provenance is not None, f"{slug}/{rule.tier_id} has no SourceProvenance"
        assert rule.provenance.issuing_authority


@pytest.mark.parametrize("slug", ["ca_bc_dave"])
def test_recovered_program_cannot_silently_become_recommended(slug):
    """Both recoveries depend on project facts this engine does not
    collect (BC: is there real animation/VFX activity; AU PDV: the
    unrecorded minimum-QAPE threshold). CBA-002's propagation must
    therefore hold them at USER_FACT_REQUIRED -- priced and disclosed,
    never a deterministic Recommended winner on unverified eligibility."""
    from app.calculators.canonical_qualification_result import QUAL_USER_FACT_REQUIRED
    from app.services.canonical_evaluation import (
        _QUALIFICATION_ADMITS_RECOMMENDED,
        _rate_condition_qualification_impact,
    )

    r = resolve_program_rate(slug, production_type="feature_film", qpe_usd=2_000_000)
    impact = _rate_condition_qualification_impact(r)
    assert impact is not None, f"{slug}'s eligibility conditions must reach qualification"
    state, _culprits = impact
    assert state == QUAL_USER_FACT_REQUIRED
    assert state not in _QUALIFICATION_ADMITS_RECOMMENDED


def test_au_pdv_offset_cannot_become_recommended_superseded_by_b1_fail_closed():
    """SUPERSEDED (Codex bounded remediation, B1 ruling): au_pdv_offset used
    to be held at USER_FACT_REQUIRED via CBA-002 qualification propagation
    -- itself already "never Recommended", but through a *priced*,
    disclosed condition. The accepted B1 ruling is stronger: au_pdv_offset
    is FAIL_CLOSED and must never resolve a rate at all, so there is no
    RateResolution left for qualification propagation to downgrade. This is
    the regression oracle for the new behavior -- a program that cannot
    resolve a rate can, a fortiori, never become Recommended."""
    r = resolve_program_rate("au_pdv_offset", production_type="feature_film", qpe_usd=2_000_000)
    assert r is None, "au_pdv_offset must be fail-closed, not merely USER_FACT_REQUIRED"


def test_au_pdv_is_an_alternative_to_location_offset_never_an_addition():
    """Screen Australia: 'These three offsets are mutually exclusive.'
    The PDV Offset must never read as stackable with the Location Offset.

    SUPERSEDED reading (Codex bounded remediation, B1 ruling): this used to
    be checked via a RateCondition.kind on a resolved RateResolution.
    au_pdv_offset is now FAIL_CLOSED (resolve_program_rate returns None), a
    strictly stronger guarantee that it can never stack with anything --
    the mutual-exclusivity condition itself remains on the canonical
    RateRule for traceability (checked directly below), but is no longer
    reachable through resolve_program_rate()."""
    rule = _RULES_BY_PROGRAM["au_pdv_offset"][0]
    kinds = {c.kind for c in rule.conditions}
    assert "mutually_exclusive_alternative_program" in kinds
    r = resolve_program_rate("au_pdv_offset", production_type="feature_film", qpe_usd=2_000_000)
    assert r is None, "fail-closed au_pdv_offset must not resolve, mutually-exclusive or not"


def test_au_pdv_did_not_inherit_location_offsets_threshold():
    """PDV's real minimum QAPE is materially lower than the Location
    Offset's AUD $20M and is NOT recorded in this project. Borrowing the
    Location Offset's USD 10,000,000 bound would be a fabrication that
    wrongly excludes eligible productions."""
    location = _RULES_BY_PROGRAM["au_location_offset"][0]
    pdv = _RULES_BY_PROGRAM["au_pdv_offset"][0]
    assert location.min_qpe_usd == 10_000_000.0
    assert pdv.min_qpe_usd is None


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
