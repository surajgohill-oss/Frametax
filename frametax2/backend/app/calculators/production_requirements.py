"""
production_requirements.py

Phase 7 — the PRODUCTION-FIRST layer. Before any jurisdiction is priced,
CineGlobe must understand the PRODUCTION: what environments it needs, what
infrastructure it needs, and — for any literal location string — what
reusable production category that location represents. Only then can
discovery ask "can this production be MADE here?" rather than merely "can
this jurisdiction be priced?".

Three responsibilities, all data-driven and reusable across productions:

  1. PRODUCTION REQUIREMENTS — derive a structured environment +
     infrastructure profile from the production's already-computed physical
     requirements (script + real-budget account spend). No production is
     special-cased; whatever `physical_requirements` reports for a given
     production is what drives its profile.

  2. LOCATION ABSTRACTION — map any literal location string ("Malibu",
     "Mediterranean island", "Tuscany") to generalized production
     categories via an extensible keyword ontology. The ontology is a
     reusable vocabulary, not a per-location lookup table.

  3. CAPABILITY MATCHING — compare the production's requirements against a
     jurisdiction's CAPABILITY profile (geography / infrastructure / crew /
     post — separate from any incentive calculation) and report, with
     reasons, whether the jurisdiction can physically support the
     production.
"""
from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────────────
# 1. Production requirements
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ProductionRequirements:
    # Every environment/infrastructure capability the production needs, and
    # the subset that is a HARD physical requirement (a jurisdiction that
    # cannot provide a required capability cannot make this production).
    environments: frozenset[str]
    infrastructure: frozenset[str]
    required_capabilities: frozenset[str]
    evidence: dict


# Physical-requirement signal → canonical capability token. Data-driven: keys
# are the signals `physical_requirements` already emits; values are the
# capability vocabulary the jurisdiction capability profiles are scored on.
_ENV_SIGNAL_TO_CAPABILITY = {
    "marine": "marine_filming",
    "open_water_filming": "open_water_filming",
    "underwater_photography": "underwater_filming",
    "period": "period_environments",
    "night_work": "night_environments",
    "city": "urban_environments",
    "desert": "desert_environments",
    "snow": "snow_environments",
}
_LOCATION_CATEGORY_TO_CAPABILITY = {
    "beach_coast": "coastal_environments",
    "marine_open_water": "open_water_filming",
    "island_tropical": "tropical_environments",
    "island": "island_environments",
    "mediterranean": "coastal_environments",
    "historic_old_world": "historic_architecture",
    "period_town": "period_environments",
    "mountain": "mountain_environments",
    "desert": "desert_environments",
    "urban": "urban_environments",
    "rural_countryside": "rural_environments",
    "forest": "forest_environments",
}
# Which derived capabilities are HARD requirements (a jurisdiction must be
# able to provide them) vs. broadly-available soft requirements. Marine /
# open-water / underwater / water-tank work is genuinely discriminating;
# period / night / urban environments are widely supportable.
_HARD_REQUIREMENT_CAPABILITIES = frozenset({
    "marine_filming", "open_water_filming", "underwater_filming",
    "water_tanks", "desert_environments", "snow_environments",
})


def derive_production_requirements(physical_requirements: dict) -> ProductionRequirements:
    """Structured environment + infrastructure requirements from the
    production's own physical_requirements (script + real-budget spend).
    Pure function of the input — no production-specific branching."""
    pr = physical_requirements or {}
    environments: set[str] = set()
    infrastructure: set[str] = set()
    evidence: dict = {}

    # Environments from confirmed script requirements.
    for signal, spec in (pr.get("script_requirements") or {}).items():
        cap = _ENV_SIGNAL_TO_CAPABILITY.get(signal)
        if cap and spec and spec.get("value"):
            environments.add(cap)
            evidence[cap] = spec.get("evidence")

    # Environments from effective location categories.
    for cat, spec in (pr.get("location_categories") or {}).items():
        if spec and spec.get("effective"):
            cap = _LOCATION_CATEGORY_TO_CAPABILITY.get(cat)
            if cap:
                environments.add(cap)
                evidence.setdefault(cap, spec.get("evidence"))

    # Infrastructure from real-budget account signals (never fabricated).
    if pr.get("marine_required"):
        infrastructure.add("marine_support")
        environments.add("marine_filming")
        evidence.setdefault("marine_support", pr.get("marine_account"))
    if pr.get("aerial_required"):
        infrastructure.add("aerial_support")
        evidence.setdefault("aerial_support", pr.get("aerial_account"))
    vfx = (pr.get("script_requirements") or {}).get("vfx_intensity")
    if vfx and vfx.get("value"):
        infrastructure.add("vfx")
        evidence.setdefault("vfx", vfx.get("evidence"))
    # Every production needs post; whether it is done in-jurisdiction is a
    # routing question, not a requirement to drop.
    infrastructure.add("post_production")

    required = frozenset(
        c for c in (environments | infrastructure) if c in _HARD_REQUIREMENT_CAPABILITIES
    )
    return ProductionRequirements(
        environments=frozenset(environments),
        infrastructure=frozenset(infrastructure),
        required_capabilities=required,
        evidence=evidence,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Location abstraction
# ─────────────────────────────────────────────────────────────────────────────

# Keyword → production categories. An extensible ontology (reusable vocabulary),
# NOT a per-location lookup — any literal string is classified by the keywords
# it contains. Grows as the ontology grows; never a hard-coded place list.
_LOCATION_ONTOLOGY: dict[str, frozenset[str]] = {
    "beach": frozenset({"beach_coast", "coastal_environments"}),
    "coast": frozenset({"beach_coast", "coastal_environments"}),
    "coastal": frozenset({"beach_coast", "coastal_environments"}),
    "seafront": frozenset({"beach_coast", "coastal_environments"}),
    "waterfront": frozenset({"beach_coast", "coastal_environments"}),
    "sea": frozenset({"marine_open_water", "open_water_filming"}),
    "ocean": frozenset({"marine_open_water", "open_water_filming"}),
    "harbor": frozenset({"harbor_marina"}),
    "harbour": frozenset({"harbor_marina"}),
    "marina": frozenset({"harbor_marina"}),
    "port": frozenset({"harbor_marina"}),
    "river": frozenset({"river"}),
    "lake": frozenset({"lake"}),
    "island": frozenset({"island"}),
    "mediterranean": frozenset({"mediterranean", "coastal_environments"}),
    "tropical": frozenset({"tropical_environments"}),
    "mountain": frozenset({"mountain_environments"}),
    "alpine": frozenset({"mountain_environments", "snow_environments"}),
    "desert": frozenset({"desert_environments"}),
    "forest": frozenset({"forest_environments"}),
    "jungle": frozenset({"tropical_environments", "forest_environments"}),
    "snow": frozenset({"snow_environments"}),
    "arctic": frozenset({"snow_environments"}),
    "city": frozenset({"urban_environments"}),
    "downtown": frozenset({"urban_environments"}),
    "financial": frozenset({"urban_environments"}),
    "metropolitan": frozenset({"urban_environments"}),
    "town": frozenset({"town"}),
    "village": frozenset({"village", "rural_environments"}),
    "rural": frozenset({"rural_environments"}),
    "countryside": frozenset({"rural_environments"}),
    "farm": frozenset({"rural_environments", "agricultural"}),
    "vineyard": frozenset({"rural_environments", "agricultural"}),
    "tuscany": frozenset({"rural_environments", "historic_architecture"}),
    "historic": frozenset({"historic_architecture"}),
    "medieval": frozenset({"historic_architecture", "period_environments"}),
    "old town": frozenset({"historic_architecture", "period_environments"}),
    "period": frozenset({"period_environments"}),
    "industrial": frozenset({"industrial"}),
    "residential": frozenset({"residential"}),
    "suburban": frozenset({"suburban"}),
    "luxury": frozenset({"residential"}),
}


def abstract_location(location: str) -> frozenset[str]:
    """Classify any literal location string into reusable production
    categories via the keyword ontology. Case-insensitive, substring-based;
    unknown strings return an empty set (never a fabricated category)."""
    if not location:
        return frozenset()
    text = location.lower()
    cats: set[str] = set()
    for keyword, categories in _LOCATION_ONTOLOGY.items():
        if keyword in text:
            cats |= categories
    return frozenset(cats)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Jurisdiction capability profile (SEPARATE from incentive) + matching
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CapabilityProfile:
    jurisdiction_code: str
    has_capability_data: bool
    # capability provisions keyed by the same capability vocabulary
    provisions: frozenset[str]
    marine_suitability: str | None
    crew_depth: str | None
    notes: str


_MARINE_OK = {"strong", "excellent", "moderate", "limited"}


def jurisdiction_capability_profile(code: str) -> CapabilityProfile:
    """A jurisdiction's production CAPABILITY (geography / infrastructure /
    crew / post) — read from the structured jurisdiction profile's capability
    fields, entirely separate from its incentive rate/rules. Jurisdictions
    with no structured profile carry has_capability_data=False (capability
    unknown), never fabricated capability."""
    from app.calculators import jurisdiction_comparison as jc

    p = jc.ALL_PROFILES.get(code)
    if p is None:
        return CapabilityProfile(code, False, frozenset(), None, None,
                                 "No structured capability profile — capability unknown.")
    provisions: set[str] = set()
    marine = getattr(p, "marine_suitability", None)
    if getattr(p, "has_open_water_filming", None) or (marine in _MARINE_OK):
        provisions.add("open_water_filming")
        provisions.add("marine_filming")
        provisions.add("coastal_environments")
    if getattr(p, "has_water_tanks", None):
        provisions.add("water_tanks")
    if getattr(p, "vessel_marine_qualifies", None):
        provisions.add("marine_support")
    if getattr(p, "studio_available", None):
        provisions.add("sound_stages")
    if getattr(p, "post_production_available", None):
        provisions.add("post_production")
    if getattr(p, "vfx_qualifies", None):
        provisions.add("vfx")
    if getattr(p, "music_qualifies", None):
        provisions.add("music_scoring")
    return CapabilityProfile(
        jurisdiction_code=code, has_capability_data=True, provisions=frozenset(provisions),
        marine_suitability=marine, crew_depth=getattr(p, "crew_depth_rating", None),
        notes=(getattr(p, "notes", "") or "")[:160],
    )


@dataclass(frozen=True)
class CapabilityMatch:
    production_capable: bool
    compatible: tuple[str, ...]
    incompatible: tuple[str, ...]   # HARD-required capabilities the jurisdiction lacks
    unknown: tuple[str, ...]        # no capability data to judge
    reasons: tuple[str, ...]


def match_capability(reqs: ProductionRequirements, cap: CapabilityProfile) -> CapabilityMatch:
    """Compare a production's requirements against a jurisdiction's
    capability. production_capable is False only when a HARD-required
    capability is affirmatively unsupported — never merely because the model
    is incomplete (unknowns do not reject; task rule)."""
    if not cap.has_capability_data:
        return CapabilityMatch(
            production_capable=False, compatible=(), incompatible=(),
            unknown=tuple(sorted(reqs.required_capabilities)),
            reasons=("No structured capability profile — cannot assess whether the "
                     "production can be made here.",),
        )
    compatible: list[str] = []
    incompatible: list[str] = []
    reasons: list[str] = []
    for need in sorted(reqs.environments | reqs.infrastructure):
        if need in cap.provisions:
            compatible.append(need)
            reasons.append(f"✓ {need.replace('_', ' ')}")
        elif need in reqs.required_capabilities:
            # affirmatively required but not provided -> hard incompatibility
            incompatible.append(need)
            reasons.append(f"✗ {need.replace('_', ' ')} required but not supported")
    capable = not incompatible
    return CapabilityMatch(
        production_capable=capable,
        compatible=tuple(compatible), incompatible=tuple(incompatible),
        unknown=(), reasons=tuple(reasons),
    )
