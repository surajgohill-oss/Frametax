"""
enumerate_structures.py — Structure candidate generator (Phase E / Phase 2).

Given a set of candidate jurisdiction codes, enumerates all valid production
structure combinations from the GlobalProgramEntry inventory:

  - Single-jurisdiction: primary incentive + eligible grants + eligible regional
  - Grant-stack: primary + multiple grants from compatible international funds
  - Split-jurisdiction: two primaries from different jurisdictions (different spend pools)

Does NOT score or filter — pure enumeration. Returns StructureCandidate objects.

No DB access. No AI calls. Deterministic.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

from app.data.global_inventory import ALL_PROGRAMS, GlobalProgramEntry
from app.optimization.types import StructureCandidate

# ---------------------------------------------------------------------------
# Program type classification
# ---------------------------------------------------------------------------

_PRIMARY_TYPES = frozenset({"tax_credit", "cash_rebate"})
_GRANT_TYPES = frozenset({
    "direct_grant", "co_production_fund", "development_fund",
})
_REGIONAL_TYPES = frozenset({"discretionary_fund", "regional_fund"})

# ---------------------------------------------------------------------------
# Grant eligibility — which jurisdiction codes can access which funds
# ---------------------------------------------------------------------------

# EU member/associated states (Creative Europe / Eurimages eligible)
_EU_ELIGIBLE = frozenset({
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE",
    "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT",
    "RO", "SK", "SI", "ES", "SE", "GB",  # UK still in Eurimages
    # Associated / observer
    "NO", "IS", "TR", "RS", "UA", "AL", "BA", "ME", "MK", "MD", "GE",
})

# Nordic eligible (Nordisk Film & TV Fond)
_NORDIC_ELIGIBLE = frozenset({"DK", "FI", "IS", "NO", "SE", "EE", "LV", "LT"})

# IBERO eligible
_IBERO_ELIGIBLE = frozenset({
    "ES", "PT", "AR", "BO", "BR", "CL", "CO", "CR", "CU", "DO", "EC",
    "SV", "GT", "HN", "MX", "NI", "PA", "PY", "PE", "UY", "VE",
})

# Open funds — available to any jurisdiction (subject to content/artistic criteria)
_OPEN_FUND_SLUGS = frozenset({
    "nl_hbf",           # Hubert Bals Fund — Global South filmmakers
    "qa_dfi_fund",      # Doha Film Institute — international focus
    "us_sundance_doc",  # Sundance Documentary Fund — documentary only
    "us_itvs_fund",     # ITVS — documentary, PBS-linked
})

# ACP eligible (Africa, Caribbean, Pacific)
_ACP_ELIGIBLE = frozenset({
    "ZA", "NG", "KE", "GH", "SN", "CI", "CM", "ET", "TZ", "UG", "MZ",
    "ZM", "ZW", "MW", "BW", "NA", "LS", "SZ", "RW", "BI", "TG", "BJ",
    "GW", "GN", "SL", "LR", "ML", "BF", "NE", "MR", "CV", "ST", "GQ",
    "GA", "CG", "CF", "TD", "SS", "SD", "ER", "DJ", "SO", "MG", "MU",
    "SC", "KM", "JM", "TT", "BB", "BS", "GD", "LC", "VC", "AG", "DM",
    "KN", "SB", "VU", "PG", "FJ", "WS", "TO",
})


def _grant_eligible_for_jurisdiction(
    grant: GlobalProgramEntry,
    target_jur: str,
) -> bool:
    """
    True if `grant` is accessible to a production primarily in `target_jur`.
    """
    grant_jur = grant.jurisdiction_code
    target_top = target_jur.split("-")[0]

    # Jurisdiction-specific grants
    if grant_jur == target_jur:
        return True

    # Country-level match (e.g., grant is CA, target is CA-ON)
    if grant_jur == target_top:
        return True

    # EU supranational funds
    if grant_jur == "EU" and target_top in _EU_ELIGIBLE:
        return True

    # Nordic fund
    if grant_jur == "NORDIC" and target_top in _NORDIC_ELIGIBLE:
        return True

    # IBERO fund
    if grant_jur == "IBERO" and target_top in _IBERO_ELIGIBLE:
        return True

    # ACP fund
    if grant_jur == "ACP" and target_top in _ACP_ELIGIBLE:
        return True

    # Open funds — available to all
    from app.optimization.stacking_rules import infer_slug
    slug = infer_slug(grant)
    if slug in _OPEN_FUND_SLUGS:
        return True

    return False


# ---------------------------------------------------------------------------
# Primary program selection
# ---------------------------------------------------------------------------

def _get_primary_programs_for_jurisdiction(
    jur_code: str,
    all_programs: list[GlobalProgramEntry],
) -> list[GlobalProgramEntry]:
    """Return all primary (tax_credit / cash_rebate) programs for a jurisdiction."""
    return [
        p for p in all_programs
        if p.jurisdiction_code == jur_code
        and p.program_type in _PRIMARY_TYPES
    ]


def _get_eligible_grants(
    target_jurisdictions: list[str],
    all_programs: list[GlobalProgramEntry],
) -> list[GlobalProgramEntry]:
    """Return grants/funds eligible for at least one of the target jurisdictions."""
    eligible: list[GlobalProgramEntry] = []
    for p in all_programs:
        if p.program_type not in _GRANT_TYPES:
            continue
        for jur in target_jurisdictions:
            if _grant_eligible_for_jurisdiction(p, jur):
                eligible.append(p)
                break
    return eligible


def _get_eligible_regional(
    target_jurisdictions: list[str],
    all_programs: list[GlobalProgramEntry],
) -> list[GlobalProgramEntry]:
    """
    Return regional/sub-national fund programs for target jurisdictions.
    Includes any program whose jurisdiction_code is a sub-national code of a
    target jurisdiction (e.g., ES-EUS for target ES), regardless of program_type.
    """
    result: list[GlobalProgramEntry] = []
    for p in all_programs:
        # Include if it's a regional/discretionary fund OR if its jurisdiction code
        # is sub-national (contains "-") relative to a target jurisdiction
        is_regional_type = p.program_type in _REGIONAL_TYPES
        is_subnational = "-" in p.jurisdiction_code
        if not (is_regional_type or is_subnational):
            continue
        for jur in target_jurisdictions:
            if p.jurisdiction_code == jur:
                result.append(p)
                break
            # Sub-national match: ES-EUS matches target ES
            if is_subnational and p.jurisdiction_code.startswith(jur + "-"):
                result.append(p)
                break
    return result


def _make_structure_id(
    primaries: list[GlobalProgramEntry],
    grants: list[GlobalProgramEntry],
    regionals: list[GlobalProgramEntry],
) -> str:
    parts = []
    for p in sorted(primaries, key=lambda x: x.jurisdiction_code):
        parts.append(f"{p.jurisdiction_code}:{p.program_name[:20].replace(' ', '_')}")
    for g in sorted(grants, key=lambda x: x.jurisdiction_code):
        parts.append(f"{g.jurisdiction_code}:{g.program_name[:12].replace(' ', '_')}")
    for r in sorted(regionals, key=lambda x: x.jurisdiction_code):
        parts.append(f"{r.jurisdiction_code}:{r.program_name[:12].replace(' ', '_')}")
    return "+".join(parts) or "empty"


# ---------------------------------------------------------------------------
# Main enumeration function
# ---------------------------------------------------------------------------

def enumerate_structures(
    jurisdiction_codes: list[str],
    all_programs: list[GlobalProgramEntry] | None = None,
    max_grants_per_structure: int = 3,
    include_split_jurisdictions: bool = True,
) -> list[StructureCandidate]:
    """
    Enumerate all valid production structure candidates for the given jurisdictions.

    Parameters
    ----------
    jurisdiction_codes          Target jurisdictions (ISO codes or custom like EU, NORDIC)
    all_programs                GlobalProgramEntry list; defaults to ALL_PROGRAMS
    max_grants_per_structure    Maximum number of grant programs per structure (default 3)
    include_split_jurisdictions Include 2-jurisdiction split structures (default True)

    Returns
    -------
    List of StructureCandidate objects (not yet filtered or scored).
    """
    if all_programs is None:
        all_programs = ALL_PROGRAMS

    candidates: list[StructureCandidate] = []
    seen_ids: set[str] = set()

    # Collect eligible grants for all target jurisdictions
    all_eligible_grants = _get_eligible_grants(jurisdiction_codes, all_programs)
    all_eligible_regional = _get_eligible_regional(jurisdiction_codes, all_programs)

    # Deduplicate grants by program_name (same fund may appear multiple times)
    seen_grant_names: set[str] = set()
    unique_grants: list[GlobalProgramEntry] = []
    for g in all_eligible_grants:
        if g.program_name not in seen_grant_names:
            seen_grant_names.add(g.program_name)
            unique_grants.append(g)

    seen_regional_names: set[str] = set()
    unique_regional: list[GlobalProgramEntry] = []
    for r in all_eligible_regional:
        if r.program_name not in seen_regional_names:
            seen_regional_names.add(r.program_name)
            unique_regional.append(r)

    # Grant power set (0..max_grants_per_structure)
    def grant_combos(grants: list[GlobalProgramEntry], max_n: int):
        for n in range(0, min(max_n, len(grants)) + 1):
            yield from itertools.combinations(grants, n)

    # ---------------------------------------------------------------------------
    # 1. Single-jurisdiction structures
    # ---------------------------------------------------------------------------
    for jur in jurisdiction_codes:
        primaries = _get_primary_programs_for_jurisdiction(jur, all_programs)
        if not primaries:
            # Some jurisdictions have only grants; still enumerate grant-only
            # structures for co-production scenarios
            for g_combo in grant_combos(
                [g for g in unique_grants if _grant_eligible_for_jurisdiction(g, jur)],
                max_grants_per_structure,
            ):
                if not g_combo:
                    continue
                sid = _make_structure_id([], list(g_combo), [])
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    candidates.append(StructureCandidate(
                        structure_id=sid,
                        primary_programs=[],
                        grant_programs=list(g_combo),
                        regional_programs=[],
                        jurisdiction_codes=[jur],
                        structure_type="grant_stack",
                        notes=[f"No primary incentive for {jur}; grant-only structure."],
                    ))
            continue

        jur_grants = [g for g in unique_grants if _grant_eligible_for_jurisdiction(g, jur)]
        jur_regional = [r for r in unique_regional if r.jurisdiction_code.startswith(jur)]

        for primary in primaries:
            # With 0..max grant combinations
            for g_combo in grant_combos(jur_grants, max_grants_per_structure):
                # With 0 or 1 regional fund
                for r_combo in [(), *[(r,) for r in jur_regional]]:
                    sid = _make_structure_id(
                        [primary], list(g_combo), list(r_combo)
                    )
                    if sid in seen_ids:
                        continue
                    seen_ids.add(sid)
                    candidates.append(StructureCandidate(
                        structure_id=sid,
                        primary_programs=[primary],
                        grant_programs=list(g_combo),
                        regional_programs=list(r_combo),
                        jurisdiction_codes=sorted({
                            jur, *[g.jurisdiction_code for g in g_combo],
                            *[r.jurisdiction_code for r in r_combo],
                        }),
                        structure_type="single",
                    ))

    # ---------------------------------------------------------------------------
    # 2. Split-jurisdiction structures (2 primary jurisdictions)
    # ---------------------------------------------------------------------------
    if include_split_jurisdictions and len(jurisdiction_codes) >= 2:
        for jur_a, jur_b in itertools.combinations(jurisdiction_codes, 2):
            primaries_a = _get_primary_programs_for_jurisdiction(jur_a, all_programs)
            primaries_b = _get_primary_programs_for_jurisdiction(jur_b, all_programs)
            if not primaries_a or not primaries_b:
                continue

            # For splits, take best (highest base_rate) from each jurisdiction
            best_a = max(
                primaries_a,
                key=lambda p: (p.base_rate or 0.0),
            )
            best_b = max(
                primaries_b,
                key=lambda p: (p.base_rate or 0.0),
            )

            split_jurs = [jur_a, jur_b]
            combined_grants = [
                g for g in unique_grants
                if any(_grant_eligible_for_jurisdiction(g, j) for j in split_jurs)
            ]

            for g_combo in grant_combos(combined_grants, min(2, max_grants_per_structure)):
                sid = _make_structure_id([best_a, best_b], list(g_combo), [])
                if sid in seen_ids:
                    continue
                seen_ids.add(sid)
                candidates.append(StructureCandidate(
                    structure_id=sid,
                    primary_programs=[best_a, best_b],
                    grant_programs=list(g_combo),
                    regional_programs=[],
                    jurisdiction_codes=sorted({
                        jur_a, jur_b,
                        *[g.jurisdiction_code for g in g_combo],
                    }),
                    structure_type="split",
                    notes=[
                        f"Split production: ~50% qualifying spend in {jur_a}, "
                        f"~50% in {jur_b}. Each incentive applies only to its jurisdiction's spend."
                    ],
                ))

    return candidates
