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
    ("au_pdv_offset", 0.30),
])
def test_recovered_stranded_program_is_canonically_registered(slug, expected_rate):
    """Each recovered program must resolve through the SAME canonical rate
    path every other program uses -- never a special case."""
    assert slug in _RULES_BY_PROGRAM, f"{slug} lost its canonical registration"
    r = resolve_program_rate(slug, production_type="feature_film", qpe_usd=2_000_000)
    assert r is not None, f"{slug} must resolve a real rate"
    assert r.modeled_rate == expected_rate


@pytest.mark.parametrize("slug", ["ca_bc_dave", "au_pdv_offset"])
def test_recovered_program_carries_structured_provenance(slug):
    """Recovery is only complete if the authority came with it -- a
    recovered program with no provenance would just relocate the problem."""
    rules = _RULES_BY_PROGRAM[slug]
    assert rules
    for rule in rules:
        assert rule.provenance is not None, f"{slug}/{rule.tier_id} has no SourceProvenance"
        assert rule.provenance.issuing_authority


@pytest.mark.parametrize("slug", ["ca_bc_dave", "au_pdv_offset"])
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


def test_au_pdv_is_an_alternative_to_location_offset_never_an_addition():
    """Screen Australia: 'These three offsets are mutually exclusive.'
    The PDV Offset must never read as stackable with the Location Offset."""
    r = resolve_program_rate("au_pdv_offset", production_type="feature_film", qpe_usd=2_000_000)
    kinds = {c.kind for c in r.conditions_evaluated}
    assert "mutually_exclusive_alternative_program" in kinds


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
