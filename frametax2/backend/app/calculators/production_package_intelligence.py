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

from app.calculators.classify_budget_line_items import (
    ENGINE_VERSION as CLASSIFY_ENGINE_VERSION,
    classify_atl_btl_split,
)
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
    confirmed. value is only meaningful when state != UNKNOWN."""
    state: FactKnowledgeState
    value: Optional[str] = None
    notes: str = ""

    @property
    def is_actionable(self) -> bool:
        """True only for a value a downstream engine could safely use
        today. VERIFICATION_REQUIRED carries a value but is deliberately
        NOT actionable — the same discipline evidence_graph.py enforces
        for an unchained Rule."""
        return self.state == FactKnowledgeState.KNOWN and self.value is not None


def _fact(value: Optional[str], verification_required: bool = False, notes: str = "") -> AttributeFact:
    if verification_required:
        return AttributeFact(state=FactKnowledgeState.VERIFICATION_REQUIRED, value=value, notes=notes)
    if value:
        return AttributeFact(state=FactKnowledgeState.KNOWN, value=value, notes=notes)
    return AttributeFact(state=FactKnowledgeState.UNKNOWN, value=None, notes=notes)


# ── Budget Intelligence ───────────────────────────────────────────────────────

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


def build_budget_intelligence(parse_result: Optional[BudgetParseResult]) -> BudgetIntelligence:
    """Reshapes an existing BudgetParseResult through the existing
    classify_atl_btl_split() — no new classification. known=False (not a
    zeroed-out budget) is how 'no budget was supplied at all' is
    represented; it is never conflated with 'a budget with $0 line
    items'."""
    if parse_result is None or not parse_result.line_items:
        return BudgetIntelligence(
            known=False, filename=None, currency_code=None, total_budget_usd=None,
            line_item_count=0, atl_total_usd=0.0, btl_total_usd=0.0, post_total_usd=0.0,
            other_total_usd=0.0, fixed_atl_usd=0.0, variable_btl_usd=0.0, labor_usd=0.0,
            non_labor_usd=0.0, totals_by_spend_category_usd={}, parse_warnings=(),
            engine_version=CLASSIFY_ENGINE_VERSION,
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
    )


# ── Script Intelligence ──────────────────────────────────────────────────────

# The exact set of production-relevant script attributes Phase 7E is asked
# to represent. None of these are extracted by screenplay_parser.py's
# deterministic step 1 today — every one starts UNKNOWN unless the caller
# supplies it via known_attributes. This module performs no LLM pass; a
# future one may populate these keys, at which point this exact set of
# names is already the contract it would fill in.
SCRIPT_ATTRIBUTE_KEYS: tuple[str, ...] = (
    "language", "setting", "period", "countries", "cultural_themes",
    "source_material", "historical_events", "marine_usage", "vfx_intensity",
    "animation", "documentary", "childrens_content", "indigenous_content",
    "qualifying_cultural_elements",
)


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
) -> ScriptIntelligence:
    """known_attributes lets a caller (producer intake, or a future LLM
    pass) supply any of SCRIPT_ATTRIBUTE_KEYS explicitly. Every key not
    supplied stays UNKNOWN — this function never infers 'documentary' or
    'vfx_intensity' from scene headings or word count."""
    known_attributes = known_attributes or {}
    attributes = {key: _fact(str(known_attributes[key]) if key in known_attributes else None) for key in SCRIPT_ATTRIBUTE_KEYS}

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
    return PersonProfile(
        person_id=intake.person_id,
        name=intake.name,
        role=intake.role,
        nationality=_fact(intake.nationality, intake.nationality_verification_required),
        residency=_fact(intake.residency, intake.residency_verification_required),
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
    return EntityProfile(
        entity_id=intake.entity_id,
        name=intake.name,
        entity_type=intake.entity_type,
        registered_jurisdiction=_fact(
            intake.registered_jurisdiction, intake.registered_jurisdiction_verification_required,
        ),
        ownership_nationality=_fact(
            intake.ownership_nationality, intake.ownership_nationality_verification_required,
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
    records = tuple(
        LocationRecord(
            location_id=intake.location_id,
            role=intake.role,
            jurisdiction=_fact(intake.jurisdiction_code, intake.jurisdiction_verification_required),
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
