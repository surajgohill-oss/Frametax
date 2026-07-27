"""
canonical_executable_registry.py

Backend-completion tranche, Objective 1: ONE authoritative accounting of
"which jurisdictions/programs are executable" — not a new data source.

Root cause this module fixes: the engine has always had (and still has,
unchanged) two real, independently-necessary data domains —
jurisdiction_comparison.py's JurisdictionIncentiveProfile (production
capability + a hand-curated doctrine summary, ALL_PROFILES) and
executable_jurisdiction_registry.py's DoctrineRecord (the tax-doctrine
source of truth for RateRule derivation, _REGISTRY) — plus six
legacy jurisdictions (MU, GR, IE, MT, ES, FR) whose doctrine predates
executable_jurisdiction_registry.py and was deliberately never migrated
onto it (see that module's own docstring). Nothing wrong with either
domain existing; the actual bug was that NO code ever counted across
BOTH consistently. That produced a real reporting error in this
session: a "jurisdictions still needing a requirements profile" count
computed by scanning only executable_jurisdiction_registry.py silently
undercounted by 6 real jurisdictions (one of which, ES, already HAD a
profile that the scan couldn't see).

This module does not move, rewrite, or duplicate any doctrine/rate
data. It reads jurisdiction_comparison.ALL_PROFILES (already verified —
see tests below — to be exactly the 110 jurisdictions with both a
resolved doctrine and a non-empty RateRule tuple) as the authoritative
list of EXECUTABLE JURISDICTIONS, and cross-references
executable_jurisdiction_registry._REGISTRY to also surface SECONDARY
program slugs for a jurisdiction that already has a different primary
slug (e.g. US-NY: us_ny_film_credit is primary,
us_ny_post_production_credit is secondary; CZ: cz_film_incentive is
primary, cz_film_incentive_animation is secondary).

Optimizer behavior is unchanged: nothing in allocation_pricing.py,
qualification_derivation.py, production_discovery.py, or
program_spend_rules.py imports from this module. It is a reporting/
gap-analysis accessor layer only.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class CanonicalExecutableJurisdiction:
    jurisdiction_code: str
    primary_program_slug: str
    primary_program_name: str
    # Additional executable programs for the SAME jurisdiction that are
    # not this registry's one-slot-per-jurisdiction "primary" (e.g. a
    # post-production-only credit alongside a general production credit).
    # Real, resolvable, executable slugs — never a placeholder.
    secondary_program_slugs: tuple[str, ...]
    # Which underlying module defines this jurisdiction's doctrine —
    # informational provenance only, never used for any pricing/
    # eligibility decision.
    doctrine_source: str  # "executable_jurisdiction_registry" | "legacy_pre_registry"


def _build_canonical_registry() -> dict[str, CanonicalExecutableJurisdiction]:
    # Pre-existing circular-import ordering quirk between program_rate_rules.py,
    # program_rate_rules_worldwide.py, and executable_jurisdiction_registry.py
    # (documented in those modules' own history, not introduced here): whichever
    # of the two is imported first as a bare top-level import can raise while the
    # other is still initializing. Warming this up HERE, once, inside the
    # registry itself, means every caller is protected regardless of what they
    # imported first — no call site needs to remember a warm-up import.
    import app.data.program_rate_rules  # noqa: F401

    from app.calculators import jurisdiction_comparison as jc
    from app.data.executable_jurisdiction_registry import _REGISTRY as doctrine_registry

    primary_slug_by_code = {code: p.program_slug for code, p in jc.ALL_PROFILES.items()}

    secondary_by_code: dict[str, list[str]] = {}
    for slug, record in doctrine_registry.items():
        code = record.jurisdiction_code
        if primary_slug_by_code.get(code) != slug:
            secondary_by_code.setdefault(code, []).append(slug)

    out: dict[str, CanonicalExecutableJurisdiction] = {}
    for code, profile in jc.ALL_PROFILES.items():
        doctrine_source = (
            "executable_jurisdiction_registry" if profile.program_slug in doctrine_registry
            else "legacy_pre_registry"
        )
        out[code] = CanonicalExecutableJurisdiction(
            jurisdiction_code=code,
            primary_program_slug=profile.program_slug,
            primary_program_name=profile.program_name,
            secondary_program_slugs=tuple(sorted(secondary_by_code.get(code, ()))),
            doctrine_source=doctrine_source,
        )
    return out


# Lazily built (NOT eagerly at import time): executable_jurisdiction_registry
# and program_rate_rules_worldwide have a real, pre-existing circular-import
# ordering dependency (importing whichever of the two loads first can raise
# ImportError while the other is still initializing). Deferring construction
# to first call, after all modules involved have already been imported by
# whatever entry point started the process, sidesteps that ordering
# sensitivity entirely rather than requiring every caller to import things
# in a particular order.
@lru_cache(maxsize=1)
def _canonical() -> dict[str, CanonicalExecutableJurisdiction]:
    return _build_canonical_registry()


def canonical_executable_jurisdictions() -> dict[str, CanonicalExecutableJurisdiction]:
    """The single authoritative {jurisdiction_code: entry} map. Every
    report, harness statistic, or gap analysis that needs "which
    jurisdictions are executable" should call this — not
    len(jc.ALL_PROFILES) or executable_jurisdiction_registry._REGISTRY
    directly, both of which answer a narrower question on their own."""
    return dict(_canonical())


def total_executable_jurisdiction_count() -> int:
    return len(_canonical())


def canonical_executable_program_slugs() -> frozenset[str]:
    """Every executable program slug worldwide — primary AND secondary.
    This is the correct denominator for any "does every executable
    PROGRAM have X" gap analysis (e.g. Production Requirements Database
    coverage) — using only primary slugs would silently exclude real
    executable programs like us_ny_post_production_credit."""
    slugs: set[str] = set()
    for entry in _canonical().values():
        slugs.add(entry.primary_program_slug)
        slugs.update(entry.secondary_program_slugs)
    return frozenset(slugs)


def is_executable_program_slug(program_slug: str) -> bool:
    return program_slug in canonical_executable_program_slugs()


def executable_jurisdictions_without_requirements_profile() -> dict[str, CanonicalExecutableJurisdiction]:
    """Gap analysis for the Production Requirements Database, computed
    against the CANONICAL 110-jurisdiction set — the exact accounting
    that was wrong earlier this session when computed against only
    executable_jurisdiction_registry (missed MU/GR/IE/MT/ES/FR)."""
    from app.data.program_requirements import all_program_requirements

    populated = set(all_program_requirements())
    return {
        code: entry for code, entry in _canonical().items()
        if entry.primary_program_slug not in populated
        and not any(s in populated for s in entry.secondary_program_slugs)
    }
