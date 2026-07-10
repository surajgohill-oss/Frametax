"""
production_package_intelligence.py

Phase 7E of CineGlobe: the Production Package Intelligence Engine.

Every downstream engine (qualification_model, optimization_engine,
opportunity_discovery, production_structure_composer,
production_recommendation_engine, legal_authority_acquisition,
cultural_test_rules) consumes already-structured production facts — a
register, a rate, a gross budget, a jurisdiction code, a production_details
dict. Nothing in this codebase turns an actual production (a budget file,
a screenplay, a cast list, a set of shoot locations) into those inputs.
This module is that translation layer, and only that layer.

This module:

- extracts nothing new. Budget Intelligence is a thin reshaping of
  app.ingestion.budget_parser.BudgetParseResult through the existing
  app.calculators.classify_budget_line_items.classify_atl_btl_split() —
  the exact ATL/BTL/POST/OTHER split and SpendCategory taxonomy
  (VFX, MUSIC, SOUND, POST_PRODUCTION, VESSEL_MARINE,
  BTL_EQUIPMENT_RENTAL, TRAVEL, LODGING, PAYROLL_FRINGES, CONTINGENCY,
  FINANCE_COSTS, ...) that module already defines. Script Intelligence
  wraps app.ingestion.screenplay_parser.ScreenplayParseResult's
  deterministic step-1 output (scene headings, locations, character
  names) unchanged. No new classification rule, no new parsing regex,
  no new incentive math is introduced here.
- never fabricates a fact. Every person/entity/location attribute this
  module cannot derive from an already-parsed source or an explicit
  caller-supplied intake value is represented as an honest UNKNOWN or
  VERIFICATION_REQUIRED FactKnowledgeState — never silently defaulted,
  never guessed. Script attributes (language, period, cultural themes,
  source material, VFX intensity, and the rest) that no deterministic
  parser in this codebase currently extracts are represented the same
  way: UNKNOWN unless the caller explicitly supplies them.
- performs no live lookups. DiscoveryHook objects describe WHAT could be
  enriched and FROM WHICH kind of source (IMDb, TMDb, StudioSystem,
  LinkedIn, Wikipedia, official biographies, company registries, film
  commission databases) — none of them make a network call, and no
  function in this module does either.
- makes no optimization, pricing, or legal decision. ProductionPackage
  is pure structured intelligence: no incentive value, no NPC, no
  qualification verdict, no recommendation. CrewMovement records are
  shaped field-for-field to match travel_model.estimate_travel_cost()'s
  parameters exactly, so a downstream caller can pass one straight into
  that existing function — this module never calls it itself, since
  that would be pricing.
- never mutates its inputs. Every builder function here is pure: it
  reads a ParseResult / intake list and returns new dataclasses.

The Question Engine (generate_missing_inputs) is the other half of this
module's job: given the ProductionPackage components already built, it
deterministically enumerates exactly which facts are still needed before
each downstream engine can run at full strength, each carrying which
engine needs it, whether it blocks that engine entirely, and which kind
of source could plausibly resolve it (a description only, never a call).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional

from app.calculators import treaty_engine as te
from app.calculators.classify_budget_line_items import (
    ENGINE_VERSION as CLASSIFY_ENGINE_VERSION,
    classify_atl_btl_split,
)
from app.calculators.production_recommendation_engine import CULTURAL_TEST_REGISTRY
from app.calculators.qualification_model import QualificationConfidence
from app.ingestion.budget_parser import BudgetParseResult
from app.ingestion.screenplay_parser import ScreenplayParseResult

PRODUCTION_PACKAGE_INTELLIGENCE_VERSION = "1.0.0"


class FactKnowledgeState(str, enum.Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    VERIFICATION_REQUIRED = "verification_required"


@dataclass(frozen=True)
class AttributeFact:
    """One fact this engine either has, doesn't have, or has but hasn't
    confirmed. value is only meaningful when state != UNKNOWN.

    confidence is always exposed (Phase 7 Part A/C requirement) — never
    fabricated: a caller-supplied value defaults to MEDIUM (stated, not
    independently verified) unless the caller asserts otherwise, and
    UNKNOWN is always NOT_APPLICABLE, never a guessed number.
    possible_discovery_sources names WHICH kind of future enrichment
    source could resolve this fact — pure description, never a call
    (Part C: 'future enrichment source' modeled, never performed)."""
    state: FactKnowledgeState
    value: Optional[str] = None
    confidence: QualificationConfidence = QualificationConfidence.NOT_APPLICABLE
    notes: str = ""
    possible_discovery_sources: tuple["DiscoverySourceKind", ...] = field(default_factory=tuple)

    @property
    def is_actionable(self) -> bool:
        """True only for a value a downstream engine could safely use
        today. VERIFICATION_REQUIRED carries a value but is deliberately
        NOT actionable — the same discipline evidence_graph.py enforces
        for an unchained Rule."""
        return self.state == FactKnowledgeState.KNOWN and self.value is not None


def _fact(
    value: Optional[str],
    verification_required: bool = False,
    notes: str = "",
    confidence: Optional[QualificationConfidence] = None,
    possible_discovery_sources: tuple["DiscoverySourceKind", ...] = (),
) -> AttributeFact:
    if verification_required:
        return AttributeFact(
            state=FactKnowledgeState.VERIFICATION_REQUIRED, value=value,
            confidence=confidence or QualificationConfidence.LOW, notes=notes,
            possible_discovery_sources=possible_discovery_sources,
        )
    if value:
        # A KNOWN fact needs no future enrichment source — discovery
        # hooks are only meaningful for a real gap.
        return AttributeFact(
            state=FactKnowledgeState.KNOWN, value=value,
            confidence=confidence or QualificationConfidence.MEDIUM, notes=notes,
        )
    return AttributeFact(
        state=FactKnowledgeState.UNKNOWN, value=None,
        confidence=QualificationConfidence.NOT_APPLICABLE, notes=notes,
        possible_discovery_sources=possible_discovery_sources,
    )


# ── Budget Intelligence ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class OpportunityHint:
    """A deterministic, non-priced signal derived purely from the budget's
    own classified totals — never a recommendation, never a dollar
    estimate of value unlocked (that is production_recommendation_engine's
    job, and only once real opportunities/candidates exist). This is
    strictly 'here is a pattern in the numbers worth a human look'."""
    hint_id: str
    category: str
    description: str
    amount_usd: Optional[float]
    affected_spend_categories: tuple[str, ...]
    confidence: QualificationConfidence


# Movable = the WORK could plausibly be routed/relocated without moving
# the physical shoot (creative fees, VFX, music, sound, post). Fixed =
# tied to wherever principal photography physically happens. Categories
# absent from both (travel, payroll fringes, finance costs, contingency,
# ...) are deliberately left unclassified rather than guessed at either
# way — same discipline as opportunity_discovery's routing classifier.
MOVABLE_SPEND_CATEGORIES: frozenset[str] = frozenset({
    "vfx", "music", "sound", "post_production",
    "atl_director", "atl_writer", "atl_producer", "atl_cast",
})
JURISDICTION_FIXED_SPEND_CATEGORIES: frozenset[str] = frozenset({
    "btl_stage_facility", "btl_location_fees", "btl_set_construction",
    "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor",
    "vessel_marine", "btl_catering", "btl_transportation",
})

# Named policy thresholds — same style as MATERIAL_RATE_ADVANTAGE /
# HIGH_IMPACT_APPROVAL_THRESHOLD_USD elsewhere: fixed, auditable, never
# per-item invented.
DEPARTMENT_CONCENTRATION_THRESHOLD_PCT = 0.30
TRAVEL_CONCENTRATION_THRESHOLD_PCT = 0.15
PAYROLL_HEAVY_THRESHOLD_PCT = 0.40
HIGH_COST_CATEGORY_COUNT = 5


def _budget_opportunity_hints(
    by_category: dict[str, float],
    classified_items: list[dict],
    totals: dict[str, float],
) -> tuple[OpportunityHint, ...]:
    grand_total = totals["atl_total_usd"] + totals["btl_total_usd"] + totals["post_total_usd"] + totals["other_total_usd"]
    hints: list[OpportunityHint] = []

    if grand_total <= 0:
        return ()

    # Movable / jurisdiction-sensitive spend summary
    movable_usd = round(sum(amt for cat, amt in by_category.items() if cat in MOVABLE_SPEND_CATEGORIES), 2)
    if movable_usd > 0:
        movable_cats = tuple(sorted(c for c in by_category if c in MOVABLE_SPEND_CATEGORIES))
        hints.append(OpportunityHint(
            hint_id="HINT-MOVABLE-SPEND",
            category="movable_spend",
            description=f"${movable_usd:,.2f} across {len(movable_cats)} categor(ies) is routable work (VFX/music/sound/post/creative fees) not physically tied to the shoot location.",
            amount_usd=movable_usd,
            affected_spend_categories=movable_cats,
            confidence=QualificationConfidence.MEDIUM,
        ))

    fixed_usd = round(sum(amt for cat, amt in by_category.items() if cat in JURISDICTION_FIXED_SPEND_CATEGORIES), 2)
    if fixed_usd > 0:
        fixed_cats = tuple(sorted(c for c in by_category if c in JURISDICTION_FIXED_SPEND_CATEGORIES))
        hints.append(OpportunityHint(
            hint_id="HINT-JURISDICTION-FIXED-SPEND",
            category="jurisdiction_fixed_spend",
            description=f"${fixed_usd:,.2f} across {len(fixed_cats)} categor(ies) is tied to the physical shoot location and will not move independently of it.",
            amount_usd=fixed_usd,
            affected_spend_categories=fixed_cats,
            confidence=QualificationConfidence.MEDIUM,
        ))

    # Qualifying-spend candidate (everything except OTHER: finance/
    # insurance/completion bond/contingency, which classify_line_item's
    # own comment already notes is excluded from most incentive programs)
    qualifying_candidate_usd = round(totals["atl_total_usd"] + totals["btl_total_usd"] + totals["post_total_usd"], 2)
    hints.append(OpportunityHint(
        hint_id="HINT-QUALIFYING-SPEND-CANDIDATE",
        category="qualifying_spend_candidate",
        description=f"${qualifying_candidate_usd:,.2f} of ${grand_total:,.2f} total is ATL/BTL/POST spend — a candidate qualifying-spend basis before any program-specific rule is applied.",
        amount_usd=qualifying_candidate_usd,
        affected_spend_categories=(),
        confidence=QualificationConfidence.LOW,
    ))

    # Department concentration
    by_department: dict[str, float] = {}
    for item in classified_items:
        dept = item.get("department") or "UNSPECIFIED"
        by_department[dept] = by_department.get(dept, 0.0) + float(item.get("amount_usd") or 0.0)
    for dept in sorted(by_department):
        pct = by_department[dept] / grand_total
        if pct >= DEPARTMENT_CONCENTRATION_THRESHOLD_PCT:
            hints.append(OpportunityHint(
                hint_id=f"HINT-DEPT-CONCENTRATION-{dept.upper().replace(' ', '_')}",
                category="department_concentration",
                description=f"Department '{dept}' represents {pct:.0%} of total budget (${round(by_department[dept], 2):,.2f}) — a concentration worth structuring/routing review.",
                amount_usd=round(by_department[dept], 2),
                affected_spend_categories=(),
                confidence=QualificationConfidence.LOW,
            ))

    # Duplicate line-item description candidates
    desc_counts: dict[str, int] = {}
    for item in classified_items:
        desc = (item.get("description") or "").strip().lower()
        if desc:
            desc_counts[desc] = desc_counts.get(desc, 0) + 1
    duplicates = tuple(sorted(d for d, c in desc_counts.items() if c > 1))
    if duplicates:
        hints.append(OpportunityHint(
            hint_id="HINT-DUPLICATE-LINE-ITEMS",
            category="duplicate_vendor_candidate",
            description=f"{len(duplicates)} line-item description(s) appear more than once — possible duplicate entries or genuinely split vendor billings worth reconciling: {', '.join(duplicates[:5])}{'...' if len(duplicates) > 5 else ''}.",
            amount_usd=None,
            affected_spend_categories=(),
            confidence=QualificationConfidence.LOW,
        ))

    # High-cost / high-value-optimization categories
    high_cost = tuple(cat for cat, _ in sorted(by_category.items(), key=lambda kv: (-kv[1], kv[0]))[:HIGH_COST_CATEGORY_COUNT])
    if high_cost:
        hints.append(OpportunityHint(
            hint_id="HINT-HIGH-COST-CATEGORIES",
            category="high_cost_categories",
            description=f"Highest-cost spend categories: {', '.join(high_cost)}.",
            amount_usd=round(sum(by_category[c] for c in high_cost), 2),
            affected_spend_categories=high_cost,
            confidence=QualificationConfidence.LOW,
        ))
    high_value_optimization = tuple(c for c in high_cost if c in MOVABLE_SPEND_CATEGORIES)
    if high_value_optimization:
        hints.append(OpportunityHint(
            hint_id="HINT-HIGH-VALUE-OPTIMIZATION-CATEGORIES",
            category="high_value_optimization_categories",
            description=f"Movable categories among the highest-cost: {', '.join(high_value_optimization)} — worth checking against Opportunity Discovery's structuring/normalization passes.",
            amount_usd=round(sum(by_category[c] for c in high_value_optimization), 2),
            affected_spend_categories=high_value_optimization,
            confidence=QualificationConfidence.LOW,
        ))

    # Payroll assumption hint
    payroll_pct = totals["labor_usd"] / grand_total
    if payroll_pct >= PAYROLL_HEAVY_THRESHOLD_PCT:
        hints.append(OpportunityHint(
            hint_id="HINT-PAYROLL-HEAVY",
            category="payroll_assumption",
            description=f"Labor spend is {payroll_pct:.0%} of budget (${round(totals['labor_usd'], 2):,.2f}) — payroll routing/EOR structuring is likely a material lever, not a minor one.",
            amount_usd=round(totals["labor_usd"], 2),
            affected_spend_categories=(),
            confidence=QualificationConfidence.LOW,
        ))

    # Travel concentration
    travel_usd = round(by_category.get("travel", 0.0) + by_category.get("lodging", 0.0), 2)
    travel_pct = travel_usd / grand_total
    if travel_pct >= TRAVEL_CONCENTRATION_THRESHOLD_PCT:
        hints.append(OpportunityHint(
            hint_id="HINT-TRAVEL-CONCENTRATION",
            category="travel_concentration",
            description=f"Travel + lodging is {travel_pct:.0%} of budget (${travel_usd:,.2f}) — a material candidate for travel normalization.",
            amount_usd=travel_usd,
            affected_spend_categories=tuple(c for c in ("travel", "lodging") if c in by_category),
            confidence=QualificationConfidence.LOW,
        ))

    # Production (ATL) concentration
    atl_pct = totals["atl_total_usd"] / grand_total
    hints.append(OpportunityHint(
        hint_id="HINT-PRODUCTION-CONCENTRATION",
        category="production_concentration",
        description=f"Above-the-line creative fees are {atl_pct:.0%} of budget (${round(totals['atl_total_usd'], 2):,.2f}).",
        amount_usd=round(totals["atl_total_usd"], 2),
        affected_spend_categories=(),
        confidence=QualificationConfidence.LOW,
    ))

    return tuple(sorted(hints, key=lambda h: h.hint_id))


@dataclass
class BudgetIntelligence:
    known: bool
    filename: Optional[str]
    currency_code: Optional[str]
    total_budget_usd: Optional[float]
    line_item_count: int
    atl_total_usd: float
    btl_total_usd: float
    post_total_usd: float
    other_total_usd: float
    fixed_atl_usd: float
    variable_btl_usd: float
    labor_usd: float
    non_labor_usd: float
    totals_by_spend_category_usd: dict[str, float]
    parse_warnings: tuple[str, ...]
    engine_version: str
    opportunity_hints: tuple[OpportunityHint, ...] = ()


def build_budget_intelligence(parse_result: Optional[BudgetParseResult]) -> BudgetIntelligence:
    """Reshapes an existing BudgetParseResult through the existing
    classify_atl_btl_split() — no new classification. known=False (not a
    zeroed-out budget) is how 'no budget was supplied at all' is
    represented; it is never conflated with 'a budget with $0 line
    items'. opportunity_hints (Phase 7 Part B) are deterministic signals
    over the already-classified totals only — no pricing, no new
    incentive math."""
    if parse_result is None or not parse_result.line_items:
        return BudgetIntelligence(
            known=False, filename=None, currency_code=None, total_budget_usd=None,
            line_item_count=0, atl_total_usd=0.0, btl_total_usd=0.0, post_total_usd=0.0,
            other_total_usd=0.0, fixed_atl_usd=0.0, variable_btl_usd=0.0, labor_usd=0.0,
            non_labor_usd=0.0, totals_by_spend_category_usd={}, parse_warnings=(),
            engine_version=CLASSIFY_ENGINE_VERSION, opportunity_hints=(),
        )

    items = [
        {"description": li.description, "department": li.department, "amount_usd": li.amount_usd or 0.0}
        for li in parse_result.line_items
    ]
    split = classify_atl_btl_split(items)
    by_category: dict[str, float] = {}
    for classified in split["classified_items"]:
        key = classified["spend_category"]
        by_category[key] = round(by_category.get(key, 0.0) + float(classified.get("amount_usd") or 0.0), 2)

    totals = split["totals"]
    return BudgetIntelligence(
        known=True,
        filename=parse_result.filename,
        currency_code=parse_result.currency_code,
        total_budget_usd=parse_result.total_budget_raw,
        line_item_count=len(parse_result.line_items),
        atl_total_usd=round(totals["atl_total_usd"], 2),
        btl_total_usd=round(totals["btl_total_usd"], 2),
        post_total_usd=round(totals["post_total_usd"], 2),
        other_total_usd=round(totals["other_total_usd"], 2),
        fixed_atl_usd=round(totals["fixed_atl_usd"], 2),
        variable_btl_usd=round(totals["variable_btl_usd"], 2),
        labor_usd=round(totals["labor_usd"], 2),
        non_labor_usd=round(totals["non_labor_usd"], 2),
        totals_by_spend_category_usd=dict(sorted(by_category.items())),
        parse_warnings=tuple(parse_result.parse_warnings),
        engine_version=split["engine_version"],
        opportunity_hints=_budget_opportunity_hints(by_category, split["classified_items"], totals),
    )


# ── Script Intelligence ──────────────────────────────────────────────────────

# The exact set of production-relevant script attributes Phase 7E is asked
# to represent. None of these are extracted by screenplay_parser.py's
# deterministic step 1 today — every one starts UNKNOWN unless the caller
# supplies it via known_attributes. This module performs no LLM pass; a
# future one may populate these keys, at which point this exact set of
# names is already the contract it would fill in.
SCRIPT_ATTRIBUTE_KEYS: tuple[str, ...] = (
    "language", "setting", "period", "period_classification", "countries",
    "cities", "regions", "cultural_themes", "indigenous_themes",
    "source_material", "historical_events", "marine_usage", "underwater",
    "aviation", "military", "sports", "vfx_intensity", "stunt_intensity",
    "animation", "documentary", "childrens_content", "indigenous_content",
    "music_heavy", "qualifying_cultural_elements",
)

# period_classification is a controlled vocabulary, not free text — kept
# as a fixed, named set so callers/tests know exactly what's valid rather
# than guessing at strings this module might accept.
PERIOD_CLASSIFICATIONS: tuple[str, ...] = ("historical", "contemporary", "future")


@dataclass
class ScriptIntelligence:
    known: bool
    filename: Optional[str]
    page_count: Optional[int]
    word_count: Optional[int]
    locations_mentioned: tuple[str, ...]
    character_names: tuple[str, ...]
    attributes: dict[str, AttributeFact]
    parse_warnings: tuple[str, ...]


def build_script_intelligence(
    parse_result: Optional[ScreenplayParseResult],
    known_attributes: Optional[dict[str, Any]] = None,
    attribute_confidence: Optional[dict[str, QualificationConfidence]] = None,
) -> ScriptIntelligence:
    """known_attributes lets a caller (producer intake, or a future LLM
    pass) supply any of SCRIPT_ATTRIBUTE_KEYS explicitly. Every key not
    supplied stays UNKNOWN — this function never infers 'documentary' or
    'vfx_intensity' from scene headings or word count. attribute_confidence
    lets the caller assert a specific confidence per key (e.g. LOW for an
    inference the producer isn't sure of); anything not specified defaults
    to MEDIUM for a supplied value, matching _fact()'s general rule."""
    known_attributes = known_attributes or {}
    attribute_confidence = attribute_confidence or {}
    attributes = {
        key: _fact(
            str(known_attributes[key]) if key in known_attributes else None,
            confidence=attribute_confidence.get(key),
        )
        for key in SCRIPT_ATTRIBUTE_KEYS
    }

    if parse_result is None:
        return ScriptIntelligence(
            known=False, filename=None, page_count=None, word_count=None,
            locations_mentioned=(), character_names=(), attributes=attributes, parse_warnings=(),
        )

    locations = tuple(sorted({
        el.value for el in parse_result.extracted_elements if el.element_type == "location"
    }))
    return ScriptIntelligence(
        known=True,
        filename=parse_result.filename,
        page_count=parse_result.page_count,
        word_count=parse_result.word_count,
        locations_mentioned=locations,
        character_names=tuple(parse_result.character_names),
        attributes=attributes,
        parse_warnings=tuple(parse_result.parse_warnings),
    )


# ── Package Intelligence (people / entities) ─────────────────────────────────

class PersonRole(str, enum.Enum):
    DIRECTOR = "director"
    WRITER = "writer"
    PRODUCER = "producer"
    CAST = "cast"
    DEPARTMENT_HEAD = "department_head"


@dataclass
class PersonIntake:
    person_id: str
    name: str
    role: PersonRole
    nationality: Optional[str] = None
    residency: Optional[str] = None
    nationality_verification_required: bool = False
    residency_verification_required: bool = False
    imdb_id: Optional[str] = None
    department: Optional[str] = None


@dataclass
class PersonProfile:
    person_id: str
    name: str
    role: PersonRole
    nationality: AttributeFact
    residency: AttributeFact
    imdb_id: Optional[str] = None
    department: Optional[str] = None


def _person_profile(intake: PersonIntake) -> PersonProfile:
    # _PERSON_DISCOVERY_HOOKS is defined later in this module (Question
    # Engine section) and resolved at call time, not def time — safe.
    person_sources = tuple(h.source for h in _PERSON_DISCOVERY_HOOKS)
    return PersonProfile(
        person_id=intake.person_id,
        name=intake.name,
        role=intake.role,
        nationality=_fact(
            intake.nationality, intake.nationality_verification_required,
            possible_discovery_sources=person_sources,
        ),
        residency=_fact(
            intake.residency, intake.residency_verification_required,
            possible_discovery_sources=person_sources,
        ),
        imdb_id=intake.imdb_id,
        department=intake.department,
    )


@dataclass
class EntityIntake:
    entity_id: str
    name: str
    entity_type: str  # "production_company" | "vendor" | "vfx_vendor" | "post_vendor" | ...
    registered_jurisdiction: Optional[str] = None
    ownership_nationality: Optional[str] = None
    registered_jurisdiction_verification_required: bool = False
    ownership_nationality_verification_required: bool = False


@dataclass
class EntityProfile:
    entity_id: str
    name: str
    entity_type: str
    registered_jurisdiction: AttributeFact
    ownership_nationality: AttributeFact


def _entity_profile(intake: EntityIntake) -> EntityProfile:
    entity_sources = tuple(h.source for h in _ENTITY_DISCOVERY_HOOKS)
    return EntityProfile(
        entity_id=intake.entity_id,
        name=intake.name,
        entity_type=intake.entity_type,
        registered_jurisdiction=_fact(
            intake.registered_jurisdiction, intake.registered_jurisdiction_verification_required,
            possible_discovery_sources=entity_sources,
        ),
        ownership_nationality=_fact(
            intake.ownership_nationality, intake.ownership_nationality_verification_required,
            possible_discovery_sources=entity_sources,
        ),
    )


@dataclass
class PackageIntelligence:
    directors: tuple[PersonProfile, ...]
    writers: tuple[PersonProfile, ...]
    producers: tuple[PersonProfile, ...]
    cast: tuple[PersonProfile, ...]
    department_heads: tuple[PersonProfile, ...]
    production_companies: tuple[EntityProfile, ...]
    vendors: tuple[EntityProfile, ...]

    @property
    def all_people(self) -> tuple[PersonProfile, ...]:
        return self.directors + self.writers + self.producers + self.cast + self.department_heads

    @property
    def all_entities(self) -> tuple[EntityProfile, ...]:
        return self.production_companies + self.vendors


_ROLE_TO_BUCKET: dict[PersonRole, str] = {
    PersonRole.DIRECTOR: "directors",
    PersonRole.WRITER: "writers",
    PersonRole.PRODUCER: "producers",
    PersonRole.CAST: "cast",
    PersonRole.DEPARTMENT_HEAD: "department_heads",
}


def build_package_intelligence(
    people: Optional[list[PersonIntake]] = None,
    production_companies: Optional[list[EntityIntake]] = None,
    vendors: Optional[list[EntityIntake]] = None,
) -> PackageIntelligence:
    buckets: dict[str, list[PersonProfile]] = {b: [] for b in _ROLE_TO_BUCKET.values()}
    for intake in sorted(people or [], key=lambda p: p.person_id):
        buckets[_ROLE_TO_BUCKET[intake.role]].append(_person_profile(intake))

    return PackageIntelligence(
        directors=tuple(buckets["directors"]),
        writers=tuple(buckets["writers"]),
        producers=tuple(buckets["producers"]),
        cast=tuple(buckets["cast"]),
        department_heads=tuple(buckets["department_heads"]),
        production_companies=tuple(
            _entity_profile(e) for e in sorted(production_companies or [], key=lambda e: e.entity_id)
        ),
        vendors=tuple(_entity_profile(e) for e in sorted(vendors or [], key=lambda e: e.entity_id)),
    )


# Single-jurisdiction country code -> cultural_test_rules.py test_slug.
# Fixed, explicit lookup — no new test theory, and every value is
# validated (below) to be a real key of production_recommendation_engine's
# own CULTURAL_TEST_REGISTRY, so this table can never suggest a test slug
# that doesn't exist.
_SINGLE_COUNTRY_CULTURAL_TEST: dict[str, str] = {
    "FR": "fr_cnc_cultural_test",
    "IE": "ie_section_481_test",
    "CA": "ca_content_test",
    "AU": "au_content_test",
}
assert set(_SINGLE_COUNTRY_CULTURAL_TEST.values()) <= set(CULTURAL_TEST_REGISTRY.keys())

# Multilateral treaty membership checks (reused directly from
# treaty_engine.py, never reimplemented) -> the cultural test their
# co-production framework requires.
_MULTILATERAL_CULTURAL_TEST: tuple[tuple[str, Any], ...] = (
    ("eu_eurimages_test", te.is_eurimages_member),
    ("ibermedia_test", te.is_ibermedia_member),
    ("eu_european_convention_test", te.is_european_convention_signatory),
)
assert all(slug in CULTURAL_TEST_REGISTRY for slug, _ in _MULTILATERAL_CULTURAL_TEST)


def derive_likely_cultural_test_categories(known_jurisdiction_codes: tuple[str, ...]) -> tuple[str, ...]:
    """
    Deterministic suggestion of which cultural_test_rules.py tests are
    plausibly relevant given the jurisdictions this ProductionPackage
    already knows about (person nationalities, entity domiciles, location
    jurisdictions — whatever the caller passes in). This is a lookup over
    already-known facts against already-registered test slugs and
    treaty_engine's own membership checks — it never invents a new test
    or a new eligibility theory, and an empty input yields an empty
    result rather than a guess.
    """
    codes = {c.upper() for c in known_jurisdiction_codes}
    likely: set[str] = set()
    for code in codes:
        slug = _SINGLE_COUNTRY_CULTURAL_TEST.get(code)
        if slug:
            likely.add(slug)
    if len(codes) >= 2:
        for slug, checker in _MULTILATERAL_CULTURAL_TEST:
            if sum(1 for code in codes if checker(code)) >= 2:
                likely.add(slug)
    return tuple(sorted(likely))


# ── Location Intelligence ────────────────────────────────────────────────────

class LocationRole(str, enum.Enum):
    PRINCIPAL_PHOTOGRAPHY = "principal_photography"
    SECOND_UNIT = "second_unit"
    POST = "post"
    VFX = "vfx"
    MUSIC = "music"
    SOUND = "sound"
    DI = "di"
    ANIMATION = "animation"
    VIRTUAL_PRODUCTION = "virtual_production"


@dataclass
class LocationIntake:
    location_id: str
    role: LocationRole
    jurisdiction_code: Optional[str] = None
    city: Optional[str] = None
    jurisdiction_verification_required: bool = False
    vendor_entity_id: Optional[str] = None
    notes: str = ""


@dataclass(frozen=True)
class LocationRecord:
    location_id: str
    role: LocationRole
    jurisdiction: AttributeFact
    city: Optional[str] = None
    vendor_entity_id: Optional[str] = None
    notes: str = ""


@dataclass
class LocationIntelligence:
    locations: tuple[LocationRecord, ...]
    jurisdiction_codes_known: tuple[str, ...]
    graph_refs: tuple[str, ...]

    def of_role(self, role: LocationRole) -> tuple[LocationRecord, ...]:
        return tuple(loc for loc in self.locations if loc.role == role)


def build_location_intelligence(locations: Optional[list[LocationIntake]] = None) -> LocationIntelligence:
    location_sources = tuple(h.source for h in _LOCATION_DISCOVERY_HOOKS)
    records = tuple(
        LocationRecord(
            location_id=intake.location_id,
            role=intake.role,
            jurisdiction=_fact(
                intake.jurisdiction_code, intake.jurisdiction_verification_required,
                possible_discovery_sources=location_sources,
            ),
            city=intake.city,
            vendor_entity_id=intake.vendor_entity_id,
            notes=intake.notes,
        )
        for intake in sorted(locations or [], key=lambda loc: loc.location_id)
    )
    known_codes = tuple(sorted({loc.jurisdiction.value for loc in records if loc.jurisdiction.is_actionable}))
    # Same "country:<code>" convention opportunity_discovery.py and
    # production_structure_composer.py already use for Jurisdiction Graph
    # node references — reused, not reinvented.
    graph_refs = tuple(f"country:{code}" for code in known_codes)
    return LocationIntelligence(locations=records, jurisdiction_codes_known=known_codes, graph_refs=graph_refs)


# ── Travel Intelligence ──────────────────────────────────────────────────────

@dataclass
class CrewMovementIntake:
    movement_id: str
    home_base: Optional[str] = None
    destination_jurisdiction: Optional[str] = None
    business_class_seats: Optional[int] = None
    premium_economy_seats: Optional[int] = None
    economy_seats: Optional[int] = None
    travel_frequency_per_year: Optional[int] = None
    hotel_nights: Optional[int] = None
    per_diem_days: Optional[int] = None


@dataclass(frozen=True)
class CrewMovement:
    """
    Field-for-field aligned with travel_model.estimate_travel_cost()'s
    parameters (home_base, destination_jurisdiction, business_class_seats,
    premium_economy_seats, economy_seats, travel_frequency_per_year,
    hotel_nights, per_diem_days) so a caller with real production numbers
    can pass movement.to_travel_model_kwargs() straight into that existing
    function. This module never calls it — that is a cost estimate
    (pricing), out of scope here.
    """
    movement_id: str
    home_base: AttributeFact
    destination_jurisdiction: AttributeFact
    business_class_seats: Optional[int] = None
    premium_economy_seats: Optional[int] = None
    economy_seats: Optional[int] = None
    travel_frequency_per_year: Optional[int] = None
    hotel_nights: Optional[int] = None
    per_diem_days: Optional[int] = None

    @property
    def is_priceable(self) -> bool:
        return self.home_base.is_actionable and self.destination_jurisdiction.is_actionable

    def to_travel_model_kwargs(self) -> dict[str, Any]:
        """Only meaningful when is_priceable is True — the caller decides
        what to do with an incomplete movement; this module doesn't guess
        defaults on its behalf."""
        kwargs: dict[str, Any] = {
            "home_base": self.home_base.value,
            "destination_jurisdiction": self.destination_jurisdiction.value,
        }
        for field_name in (
            "business_class_seats", "premium_economy_seats", "economy_seats",
            "travel_frequency_per_year", "hotel_nights", "per_diem_days",
        ):
            value = getattr(self, field_name)
            if value is not None:
                kwargs[field_name] = value
        return kwargs


@dataclass
class TravelIntelligence:
    movements: tuple[CrewMovement, ...]

    @property
    def priceable_movements(self) -> tuple[CrewMovement, ...]:
        return tuple(m for m in self.movements if m.is_priceable)


def build_travel_intelligence(crew_movements: Optional[list[CrewMovementIntake]] = None) -> TravelIntelligence:
    movements = tuple(
        CrewMovement(
            movement_id=intake.movement_id,
            home_base=_fact(intake.home_base),
            destination_jurisdiction=_fact(intake.destination_jurisdiction),
            business_class_seats=intake.business_class_seats,
            premium_economy_seats=intake.premium_economy_seats,
            economy_seats=intake.economy_seats,
            travel_frequency_per_year=intake.travel_frequency_per_year,
            hotel_nights=intake.hotel_nights,
            per_diem_days=intake.per_diem_days,
        )
        for intake in sorted(crew_movements or [], key=lambda m: m.movement_id)
    )
    return TravelIntelligence(movements=movements)


# ── Question Engine ───────────────────────────────────────────────────────────

class DownstreamEngine(str, enum.Enum):
    QUALIFICATION_MODEL = "qualification_model"
    OPTIMIZATION_ENGINE = "optimization_engine"
    OPPORTUNITY_DISCOVERY = "opportunity_discovery"
    PRODUCTION_STRUCTURE_COMPOSER = "production_structure_composer"
    PRODUCTION_RECOMMENDATION_ENGINE = "production_recommendation_engine"
    LEGAL_AUTHORITY_ACQUISITION = "legal_authority_acquisition"
    CULTURAL_TEST_RULES = "cultural_test_rules"
    TRAVEL_MODEL = "travel_model"


class OptimizerValue(str, enum.Enum):
    """Qualitative importance only — never a dollar figure. An unanswered
    question has no known value at stake; assigning one would be exactly
    the kind of invented figure this codebase refuses to produce."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DiscoverySourceKind(str, enum.Enum):
    IMDB = "imdb"
    TMDB = "tmdb"
    STUDIO_SYSTEM = "studio_system"
    LINKEDIN = "linkedin"
    WIKIPEDIA = "wikipedia"
    OFFICIAL_BIOGRAPHY = "official_biography"
    COMPANY_REGISTRY = "company_registry"
    FILM_COMMISSION_DATABASE = "film_commission_database"


@dataclass(frozen=True)
class DiscoveryHook:
    """Describes a possible future enrichment source and what it could
    resolve — nothing here executes a lookup. There is no HTTP client,
    no API key, and no network call anywhere in this module."""
    source: DiscoverySourceKind
    description: str


_PERSON_DISCOVERY_HOOKS: tuple[DiscoveryHook, ...] = (
    DiscoveryHook(DiscoverySourceKind.IMDB, "IMDb credit/bio pages may list nationality or country of residence."),
    DiscoveryHook(DiscoverySourceKind.TMDB, "TMDb person records may carry a place-of-birth field."),
    DiscoveryHook(DiscoverySourceKind.STUDIO_SYSTEM, "StudioSystem talent records may have verified nationality/residency."),
    DiscoveryHook(DiscoverySourceKind.LINKEDIN, "LinkedIn profiles may state current residency/work location."),
    DiscoveryHook(DiscoverySourceKind.WIKIPEDIA, "Wikipedia biography infoboxes often carry nationality."),
    DiscoveryHook(DiscoverySourceKind.OFFICIAL_BIOGRAPHY, "A publicist- or agency-supplied official bio may confirm nationality/residency directly."),
)
_ENTITY_DISCOVERY_HOOKS: tuple[DiscoveryHook, ...] = (
    DiscoveryHook(DiscoverySourceKind.COMPANY_REGISTRY, "A national company registry can confirm registered jurisdiction and ownership."),
)
_LOCATION_DISCOVERY_HOOKS: tuple[DiscoveryHook, ...] = (
    DiscoveryHook(DiscoverySourceKind.FILM_COMMISSION_DATABASE, "The relevant film commission's vendor/location database may confirm jurisdiction."),
)


@dataclass(frozen=True)
class MissingInput:
    identifier: str
    question: str
    why_it_matters: str
    downstream_engines: tuple[DownstreamEngine, ...]
    optimizer_value: OptimizerValue
    blocking: bool
    discovery_hooks: tuple[DiscoveryHook, ...] = ()


# Fixed, named production-level facts the Question Engine knows how to
# ask about beyond what Budget/Script/Package/Location/Travel Intelligence
# already model structurally. A caller supplies what's known via
# production_facts; anything absent from that dict is asked about here —
# this module never infers financing timing, payroll structure, treaty
# partner, or spend allocation from anything else.
_PRODUCTION_FACT_QUESTIONS: tuple[dict[str, Any], ...] = (
    {
        "key": "financing_timing",
        "identifier": "MISSING-FINANCING-TIMING",
        "question": "When does each financing tranche (equity, gap, pre-sales, incentive bridge) actually fund?",
        "why_it_matters": "Financing timing drives bridge/finance cost — optimization_engine's finance_cost_usd depends on it.",
        "downstream_engines": (DownstreamEngine.OPTIMIZATION_ENGINE,),
        "optimizer_value": OptimizerValue.MEDIUM,
        "blocking": False,
    },
    {
        "key": "payroll_structure",
        "identifier": "MISSING-PAYROLL-STRUCTURE",
        "question": "How will cast/crew payroll be routed — direct, loan-out, EOR, or payroll company?",
        "why_it_matters": "Payroll routing determines which structuring Levers apply and which jurisdiction's labor rules govern.",
        "downstream_engines": (DownstreamEngine.OPPORTUNITY_DISCOVERY, DownstreamEngine.PRODUCTION_RECOMMENDATION_ENGINE),
        "optimizer_value": OptimizerValue.MEDIUM,
        "blocking": False,
    },
    {
        "key": "treaty_partner",
        "identifier": "MISSING-TREATY-PARTNER",
        "question": "Is a co-production treaty partner country intended, and if so which one?",
        "why_it_matters": "Treaty opportunities (nationality unlocks, fund access) cannot be discovered without at least a candidate partner country.",
        "downstream_engines": (DownstreamEngine.OPPORTUNITY_DISCOVERY, DownstreamEngine.PRODUCTION_STRUCTURE_COMPOSER),
        "optimizer_value": OptimizerValue.HIGH,
        "blocking": False,
    },
    {
        "key": "local_spend_allocation_pct",
        "identifier": "MISSING-LOCAL-SPEND-ALLOCATION",
        "question": "What percentage of qualifying spend is expected to land in each candidate jurisdiction?",
        "why_it_matters": "Jurisdiction-spend-percentage thresholds gate several program RuleTypes; without an allocation estimate those tests cannot run.",
        "downstream_engines": (DownstreamEngine.QUALIFICATION_MODEL,),
        "optimizer_value": OptimizerValue.HIGH,
        "blocking": False,
    },
)


def _person_missing_inputs(person: PersonProfile) -> list[MissingInput]:
    out: list[MissingInput] = []
    if person.nationality.state != FactKnowledgeState.KNOWN:
        out.append(MissingInput(
            identifier=f"MISSING-NATIONALITY-{person.person_id}",
            question=f"What is {person.name}'s ({person.role.value}) nationality?",
            why_it_matters="Director/writer/producer/cast nationality drives cultural-test scoring and treaty nationality unlocks.",
            downstream_engines=(DownstreamEngine.CULTURAL_TEST_RULES, DownstreamEngine.OPPORTUNITY_DISCOVERY),
            optimizer_value=OptimizerValue.HIGH if person.role in (PersonRole.DIRECTOR, PersonRole.WRITER) else OptimizerValue.MEDIUM,
            blocking=False,
            discovery_hooks=_PERSON_DISCOVERY_HOOKS,
        ))
    if person.residency.state != FactKnowledgeState.KNOWN:
        out.append(MissingInput(
            identifier=f"MISSING-RESIDENCY-{person.person_id}",
            question=f"What is {person.name}'s ({person.role.value}) tax/legal residency?",
            why_it_matters="Residency affects labor-credit qualification and payroll structuring recommendations.",
            downstream_engines=(DownstreamEngine.QUALIFICATION_MODEL, DownstreamEngine.PRODUCTION_RECOMMENDATION_ENGINE),
            optimizer_value=OptimizerValue.MEDIUM,
            blocking=False,
            discovery_hooks=_PERSON_DISCOVERY_HOOKS,
        ))
    return out


def _entity_missing_inputs(entity: EntityProfile) -> list[MissingInput]:
    out: list[MissingInput] = []
    if entity.registered_jurisdiction.state != FactKnowledgeState.KNOWN:
        out.append(MissingInput(
            identifier=f"MISSING-ENTITY-JURISDICTION-{entity.entity_id}",
            question=f"In which jurisdiction is '{entity.name}' registered?",
            why_it_matters="Program RuleType.REQUIRED_ENTITY_TYPE tests and SPV/EOR structuring both depend on entity domicile.",
            downstream_engines=(DownstreamEngine.QUALIFICATION_MODEL, DownstreamEngine.OPPORTUNITY_DISCOVERY),
            optimizer_value=OptimizerValue.HIGH,
            blocking=False,
            discovery_hooks=_ENTITY_DISCOVERY_HOOKS,
        ))
    return out


def _location_missing_inputs(location: LocationRecord) -> list[MissingInput]:
    if location.jurisdiction.state == FactKnowledgeState.KNOWN:
        return []
    blocking = location.role in (LocationRole.VFX, LocationRole.POST)
    return [MissingInput(
        identifier=f"MISSING-LOCATION-{location.location_id}",
        question=f"Which jurisdiction is the {location.role.value.replace('_', ' ')} location in?",
        why_it_matters="Location jurisdiction determines which program(s) apply to that segment of spend and routes travel/normalization opportunities.",
        downstream_engines=(DownstreamEngine.OPPORTUNITY_DISCOVERY, DownstreamEngine.PRODUCTION_STRUCTURE_COMPOSER),
        optimizer_value=OptimizerValue.HIGH if blocking else OptimizerValue.MEDIUM,
        blocking=blocking,
        discovery_hooks=_LOCATION_DISCOVERY_HOOKS,
    )]


def generate_missing_inputs(
    budget: BudgetIntelligence,
    script: ScriptIntelligence,
    package: PackageIntelligence,
    location: LocationIntelligence,
    production_facts: Optional[dict[str, Any]] = None,
) -> list[MissingInput]:
    """
    Deterministic gap scan across everything this module has already
    built, plus the fixed production-fact question set. Order is fixed
    (budget/script presence, then people, then entities, then locations,
    then production facts, each internally sorted by identifier) so two
    runs over identical inputs produce identical output.
    """
    missing: list[MissingInput] = []

    if not budget.known:
        missing.append(MissingInput(
            identifier="MISSING-BUDGET",
            question="What is the production budget (chart of accounts / line items)?",
            why_it_matters="Every downstream engine — qualification, optimization, composer, recommendation — requires a gross budget and qualifying-spend register to compute anything.",
            downstream_engines=(
                DownstreamEngine.QUALIFICATION_MODEL, DownstreamEngine.OPTIMIZATION_ENGINE,
                DownstreamEngine.PRODUCTION_STRUCTURE_COMPOSER, DownstreamEngine.PRODUCTION_RECOMMENDATION_ENGINE,
            ),
            optimizer_value=OptimizerValue.HIGH,
            blocking=True,
        ))

    if not script.known:
        missing.append(MissingInput(
            identifier="MISSING-SCRIPT",
            question="Is a screenplay, treatment, or outline available?",
            why_it_matters="Cultural-test scoring (language, setting, source material) and location/VFX-intensity signals depend on script content.",
            downstream_engines=(DownstreamEngine.CULTURAL_TEST_RULES,),
            optimizer_value=OptimizerValue.MEDIUM,
            blocking=False,
        ))
    else:
        for key in SCRIPT_ATTRIBUTE_KEYS:
            if script.attributes[key].state != FactKnowledgeState.KNOWN:
                missing.append(MissingInput(
                    identifier=f"MISSING-SCRIPT-{key.upper()}",
                    question=f"What is the production's {key.replace('_', ' ')}?",
                    why_it_matters="Cultural-test qualification points and qualifying-content determinations depend on this attribute.",
                    downstream_engines=(DownstreamEngine.CULTURAL_TEST_RULES,),
                    optimizer_value=OptimizerValue.LOW,
                    blocking=False,
                ))

    for person in sorted(package.all_people, key=lambda p: p.person_id):
        missing.extend(_person_missing_inputs(person))
    for entity in sorted(package.all_entities, key=lambda e: e.entity_id):
        missing.extend(_entity_missing_inputs(entity))
    for loc in sorted(location.locations, key=lambda l: l.location_id):
        missing.extend(_location_missing_inputs(loc))

    facts = production_facts or {}
    for question in _PRODUCTION_FACT_QUESTIONS:
        if facts.get(question["key"]) in (None, ""):
            missing.append(MissingInput(
                identifier=question["identifier"],
                question=question["question"],
                why_it_matters=question["why_it_matters"],
                downstream_engines=question["downstream_engines"],
                optimizer_value=question["optimizer_value"],
                blocking=question["blocking"],
            ))

    return missing


# ── Top-level ProductionPackage ───────────────────────────────────────────────

@dataclass
class ProductionPackage:
    production_id: str
    budget: BudgetIntelligence
    script: ScriptIntelligence
    package: PackageIntelligence
    location: LocationIntelligence
    travel: TravelIntelligence
    missing_inputs: tuple[MissingInput, ...]
    known_facts: dict[str, Any]
    unknown_facts: tuple[str, ...]
    confidence: QualificationConfidence
    graph_refs: tuple[str, ...]
    engine_version: str = PRODUCTION_PACKAGE_INTELLIGENCE_VERSION

    @property
    def blocking_missing_inputs(self) -> tuple[MissingInput, ...]:
        return tuple(m for m in self.missing_inputs if m.blocking)

    @property
    def is_ready_for_downstream_engines(self) -> bool:
        """True only when nothing blocking remains — never a claim that
        every fact is known, only that nothing HARD-blocks a downstream
        engine from running (they may still run at reduced confidence)."""
        return not self.blocking_missing_inputs


def _overall_confidence(missing: list[MissingInput]) -> QualificationConfidence:
    if any(m.blocking for m in missing):
        return QualificationConfidence.LOW
    if missing:
        return QualificationConfidence.MEDIUM
    return QualificationConfidence.HIGH


def _known_and_unknown_facts(
    budget: BudgetIntelligence, script: ScriptIntelligence, package: PackageIntelligence,
    location: LocationIntelligence, production_facts: Optional[dict[str, Any]],
) -> tuple[dict[str, Any], tuple[str, ...]]:
    known: dict[str, Any] = {}
    unknown: list[str] = []

    known["budget_known"] = budget.known
    known["script_known"] = script.known
    for key, fact in sorted(script.attributes.items()):
        if fact.is_actionable:
            known[f"script.{key}"] = fact.value
        else:
            unknown.append(f"script.{key}")

    for person in sorted(package.all_people, key=lambda p: p.person_id):
        if person.nationality.is_actionable:
            known[f"person.{person.person_id}.nationality"] = person.nationality.value
        else:
            unknown.append(f"person.{person.person_id}.nationality")
        if person.residency.is_actionable:
            known[f"person.{person.person_id}.residency"] = person.residency.value
        else:
            unknown.append(f"person.{person.person_id}.residency")

    for entity in sorted(package.all_entities, key=lambda e: e.entity_id):
        if entity.registered_jurisdiction.is_actionable:
            known[f"entity.{entity.entity_id}.registered_jurisdiction"] = entity.registered_jurisdiction.value
        else:
            unknown.append(f"entity.{entity.entity_id}.registered_jurisdiction")

    for loc in sorted(location.locations, key=lambda l: l.location_id):
        if loc.jurisdiction.is_actionable:
            known[f"location.{loc.location_id}.jurisdiction"] = loc.jurisdiction.value
        else:
            unknown.append(f"location.{loc.location_id}.jurisdiction")

    facts = production_facts or {}
    for question in _PRODUCTION_FACT_QUESTIONS:
        key = question["key"]
        if facts.get(key) not in (None, ""):
            known[key] = facts[key]
        else:
            unknown.append(key)

    return known, tuple(sorted(unknown))


def build_production_package(
    production_id: str,
    budget_parse_result: Optional[BudgetParseResult] = None,
    screenplay_parse_result: Optional[ScreenplayParseResult] = None,
    script_known_attributes: Optional[dict[str, Any]] = None,
    people: Optional[list[PersonIntake]] = None,
    production_companies: Optional[list[EntityIntake]] = None,
    vendors: Optional[list[EntityIntake]] = None,
    locations: Optional[list[LocationIntake]] = None,
    crew_movements: Optional[list[CrewMovementIntake]] = None,
    production_facts: Optional[dict[str, Any]] = None,
) -> ProductionPackage:
    """
    Top-level Phase 7E entry point: builds every intelligence bucket,
    runs the Question Engine over the result, and assembles one
    deterministic ProductionPackage. Performs no optimization, no
    pricing, no legal conclusion, and does not touch any existing
    engine — it only produces the structured inputs a caller can pass
    into qualification_model / optimization_engine / opportunity_discovery /
    production_structure_composer / production_recommendation_engine /
    legal_authority_acquisition / cultural_test_rules afterward.
    """
    budget = build_budget_intelligence(budget_parse_result)
    script = build_script_intelligence(screenplay_parse_result, script_known_attributes)
    package = build_package_intelligence(people, production_companies, vendors)
    location = build_location_intelligence(locations)
    travel = build_travel_intelligence(crew_movements)

    missing = generate_missing_inputs(budget, script, package, location, production_facts)
    known_facts, unknown_facts = _known_and_unknown_facts(budget, script, package, location, production_facts)

    return ProductionPackage(
        production_id=production_id,
        budget=budget,
        script=script,
        package=package,
        location=location,
        travel=travel,
        missing_inputs=tuple(sorted(missing, key=lambda m: m.identifier)),
        known_facts=known_facts,
        unknown_facts=unknown_facts,
        confidence=_overall_confidence(missing),
        graph_refs=location.graph_refs,
    )


# ── Engine integration bridges (Phase 7 closeout, Part G) ────────────────────
#
# These functions perform no discovery, composition, pricing, or
# recommendation logic of their own — each one only reshapes already-built
# ProductionPackage fields into the exact parameter shape an existing,
# frozen engine already accepts. This is the "one source of truth" half of
# Part G: opportunity_discovery.py, production_structure_composer.py, and
# production_recommendation_engine.py are never modified or duplicated —
# only fed.

def production_package_to_known_jurisdiction_codes(package: ProductionPackage) -> tuple[str, ...]:
    """Every jurisdiction code this package actually knows about, from
    any source (locations, entity domicile, person residency) — feeds
    opportunity_discovery.discover_treaty_opportunities(country_codes) /
    discover_reinvestment_opportunities(country_codes), both of which
    accept exactly this shape (list[str] of ISO-ish country codes)."""
    codes: set[str] = set(package.location.jurisdiction_codes_known)
    for entity in package.package.all_entities:
        if entity.registered_jurisdiction.is_actionable:
            codes.add(entity.registered_jurisdiction.value)
    for person in package.package.all_people:
        if person.residency.is_actionable:
            codes.add(person.residency.value)
    return tuple(sorted(codes))


def production_package_to_extra_jurisdiction_sets(package: ProductionPackage) -> list[tuple[str, ...]]:
    """One candidate set per known jurisdiction — feeds
    production_structure_composer.compose_production_structures(...,
    extra_jurisdiction_sets=...) exactly as that parameter is already
    documented to accept (a list of explicit jurisdiction-code tuples).
    This never enumerates combinatorially; the composer's own Pass-1
    logic already does the baseline-alone / baseline-plus-partner
    expansion — this bridge only supplies the additional single-code
    sets a ProductionPackage's own location data actually names."""
    return [(code,) for code in production_package_to_known_jurisdiction_codes(package)]


def production_package_to_relevant_cultural_test_slugs(package: ProductionPackage) -> tuple[str, ...]:
    """Feeds production_recommendation_engine.generate_cultural_recommendations() /
    generate_production_recommendations()'s relevant_cultural_test_slugs
    parameter — reuses derive_likely_cultural_test_categories() (Part A)
    unchanged rather than a second jurisdiction-to-test mapping."""
    return derive_likely_cultural_test_categories(production_package_to_known_jurisdiction_codes(package))


def production_package_to_cultural_test_inputs(package: ProductionPackage) -> dict[str, dict[str, Any]]:
    """
    Best-effort, honest bridge into generate_cultural_recommendations()'s
    cultural_test_inputs parameter: only the input_keys this module can
    populate WITHOUT guessing (currently: nationality-flavored boolean
    keys for a role this package actually has a KNOWN person for, checked
    against the exact country code the test's own rule text names — never
    an EEA/EU membership inference this module has no canonical source
    for). Every key this can't honestly answer is simply absent from the
    returned dict — generate_cultural_recommendations() already turns an
    absent key into a REQUIRED_INPUT recommendation rather than assuming
    a default, so nothing is silently guessed here either.
    """
    director = package.package.directors[0] if package.package.directors else None
    writer = package.package.writers[0] if package.package.writers else None
    inputs: dict[str, dict[str, Any]] = {}

    if director and director.nationality.is_actionable:
        inputs.setdefault("fr_cnc_cultural_test", {})["director_french_or_eea"] = director.nationality.value == "FR"
        inputs.setdefault("ca_content_test", {})["director_canadian"] = director.nationality.value == "CA"
        inputs.setdefault("au_content_test", {})["director_australian"] = director.nationality.value == "AU"
    if writer and writer.nationality.is_actionable:
        inputs.setdefault("fr_cnc_cultural_test", {})["writer_french_or_eea"] = writer.nationality.value == "FR"
        inputs.setdefault("ca_content_test", {})["writer_canadian"] = writer.nationality.value == "CA"

    if package.package.production_companies:
        company = package.package.production_companies[0]
        if company.registered_jurisdiction.is_actionable:
            inputs.setdefault("fr_cnc_cultural_test", {})["producer_french"] = company.registered_jurisdiction.value == "FR"
            inputs.setdefault("au_content_test", {})["producer_australian"] = company.registered_jurisdiction.value == "AU"

    return inputs
