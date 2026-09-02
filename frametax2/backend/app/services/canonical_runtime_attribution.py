"""
canonical_runtime_attribution.py

STALE-STATE PREVENTION (item 8) -- make semantic execution unable to disagree
silently with persisted or served results.

Two verification hazards were PROVEN during this repair, not hypothesised:

  1. A semantic pricing change shipped WITHOUT bumping a hand-maintained
     ENGINE_VERSION / *_VERSION constant. The evaluation reused persisted rows,
     the change never reached served output, and a full suite reported "zero
     regressions" -- against stale rows. (Commit d754b6a, cluster 5.)
  2. Stale Python bytecode served an older module than the file on disk, so a
     verification run measured code that was no longer the source of truth.

Both are the same class of defect: the chain

    SOURCE -> LOADED RUNTIME -> RULESET -> FINGERPRINT -> PERSISTED -> API

had a link that depended on a human remembering to bump a number. This module
removes that dependency by DERIVING the identity of what is actually loaded:

  canonical_ruleset_digest()   hashes the live canonical rule DATA (rate rules,
                               authority coverage, spend doctrine, program
                               requirements, stacking rules). Change a rule and
                               the digest changes -- no constant to forget.

  pricing_source_digest()      hashes the on-disk SOURCE of the modules that
                               actually decide economics. Change the logic and
                               the digest changes.

Both are folded into the canonical evaluation fingerprint, so a semantic change
of either kind invalidates persisted results AUTOMATICALLY. The existing
version constants are deliberately retained -- they are legitimate historical
metadata and a useful human-readable label -- they are simply no longer the
only thing standing between a semantic change and a stale served number.

  verify_loaded_source_matches_disk() detects hazard 2 directly: it compares
  each loaded module's __file__ contents against the module the interpreter is
  actually running, so a verification run cannot silently measure stale
  bytecode or an unexpected source tree.
"""
from __future__ import annotations

import hashlib
import inspect
from functools import lru_cache
from pathlib import Path

#: Modules whose SOURCE decides economics. A change to any of these changes
#: served numbers, so each must invalidate persisted results.
_SEMANTIC_PRICING_MODULES = (
    # The evaluation service itself. Its source decides not only economics
    # but the SHAPE of what gets persisted (calculation_trace_json), which is
    # served verbatim. ENGINE_VERSION was the only thing standing between a
    # trace-shape change and a stale served row, and it is hand-maintained --
    # exactly the dependency this module exists to remove. Including it means
    # any edit here invalidates persisted results. Over-invalidation is safe;
    # under-invalidation is what produced "zero regressions" against stale rows.
    "app.services.canonical_evaluation",
    "app.data.authority_coverage_registry",
    "app.calculators.allocation_pricing",
    "app.calculators.qualification_derivation",
    "app.calculators.canonical_requirements_gate_bridge",
    "app.calculators.canonical_stack_bridge",
    "app.data.program_rate_rules",
)

#: Callables returning the live canonical rule DATA. Hashing their repr binds
#: the fingerprint to the rules actually loaded, not to a version label.
def _ruleset_fragments() -> list[str]:
    fragments: list[str] = []

    from app.data.program_rate_rules import _RULES_BY_PROGRAM

    for slug in sorted(_RULES_BY_PROGRAM):
        for rule in _RULES_BY_PROGRAM[slug]:
            fragments.append(
                f"rate|{slug}|{rule.tier_id}|{rule.rate}|{rule.is_band_ceiling}|"
                f"{rule.min_qpe_usd}|{sorted(rule.production_types)}|"
                + ",".join(sorted(c.condition_id for c in rule.conditions))
            )

    from app.data.authority_coverage_registry import (
        BLOCKING_STATES,
        COVERAGE_REGISTRY,
        coverage_state,
    )
    from app.data.program_requirements import _REGISTRY as _REQUIREMENTS

    fragments.append("blocking|" + ",".join(sorted(BLOCKING_STATES)))
    # The EFFECTIVE disposition, not the raw registry row. A program's
    # coverage state can now be DERIVED from canonical requirement data
    # (authority_coverage_registry._derived_coverage -- e.g. an
    # AllocationType.COMPETITIVE program is NON_GUARANTEED_SELECTIVE even
    # with no explicit row). Hashing only COVERAGE_REGISTRY would leave that
    # derived half able to change a program's economic candidacy WITHOUT
    # invalidating persisted results -- the exact hazard this module exists
    # to remove. Union the two key sets so a derived-only program is covered.
    for slug in sorted(set(COVERAGE_REGISTRY) | set(_REQUIREMENTS)):
        fragments.append(f"coverage|{slug}|{coverage_state(slug)}")

    for slug in sorted(_REQUIREMENTS):
        profile = _REQUIREMENTS[slug]
        fragments.append(
            f"req|{slug}|{profile.min_total_budget_usd}|{profile.min_local_spend_usd}|"
            f"{profile.per_project_cap_usd}|{profile.annual_program_cap_usd}|"
            f"{profile.local_entity_required}|{profile.min_shoot_days}|"
            # allocation_type and preapproval_mandatory DECIDE candidacy via
            # the derivation above, so they belong in the digest.
            f"{getattr(profile, 'allocation_type', None)}|"
            f"{getattr(profile, 'preapproval_mandatory', None)}"
        )

    from app.optimization.stacking_rules import _SLUG_PAIR_RULES

    for pair in sorted(_SLUG_PAIR_RULES, key=lambda p: sorted(p)):
        fragments.append(f"stack|{sorted(pair)}|{_SLUG_PAIR_RULES[pair]}")

    return fragments


@lru_cache(maxsize=1)
def canonical_ruleset_digest() -> str:
    """A digest of the canonical rule DATA actually loaded in this process.

    Cached: the registries are import-time immutable, so this is computed once.
    A test that mutates a registry in-process should call
    canonical_ruleset_digest.cache_clear().
    """
    digest = hashlib.sha256()
    for fragment in _ruleset_fragments():
        digest.update(fragment.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


@lru_cache(maxsize=1)
def pricing_source_digest() -> str:
    """A digest of the ON-DISK source of the modules that decide economics."""
    digest = hashlib.sha256()
    for module_name in _SEMANTIC_PRICING_MODULES:
        source_path = _module_path(module_name)
        digest.update(module_name.encode("utf-8"))
        digest.update(source_path.read_bytes() if source_path else b"<missing>")
        digest.update(b"\x00")
    return digest.hexdigest()


def _module_path(module_name: str) -> Path | None:
    import importlib

    module = importlib.import_module(module_name)
    file_name = getattr(module, "__file__", None)
    if not file_name:
        return None
    path = Path(file_name)
    return path if path.exists() else None


def runtime_attribution() -> dict[str, str]:
    """The full identity of the runtime that produced a result. Persisted and
    served so any number can be attributed to the exact code + rules behind
    it."""
    from app.services.canonical_evaluation import ENGINE_VERSION

    return {
        "engine_version": ENGINE_VERSION,
        "ruleset_digest": canonical_ruleset_digest(),
        "pricing_source_digest": pricing_source_digest(),
    }


def verify_loaded_source_matches_disk() -> list[str]:
    """Detect hazard 2: a module whose LOADED code differs from the file on
    disk (stale bytecode, an unexpected source tree, a monkeypatched module).

    Returns a list of human-readable mismatches; empty means the runtime is
    executing exactly what the repository contains.
    """
    import importlib

    mismatches: list[str] = []
    for module_name in _SEMANTIC_PRICING_MODULES:
        module = importlib.import_module(module_name)
        path = _module_path(module_name)
        if path is None:
            mismatches.append(f"{module_name}: no source file on disk")
            continue
        try:
            loaded = inspect.getsource(module)
        except OSError:  # pragma: no cover - only when source is unreadable
            mismatches.append(f"{module_name}: loaded source unreadable")
            continue
        on_disk = path.read_text()
        if loaded != on_disk:
            mismatches.append(
                f"{module_name}: LOADED source differs from {path} -- the runtime "
                "is not executing the repository's current code"
            )
    return mismatches
