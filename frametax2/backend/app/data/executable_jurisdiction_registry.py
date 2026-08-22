"""
executable_jurisdiction_registry.py

The single canonical source for a jurisdiction+program's DOCTRINE facts
(rate, bands, thresholds, caps, refundability, citation, confidence) —
built to close the scalability bottleneck identified in the worldwide
jurisdiction population phase (see docs/architecture/CAPABILITY_LEDGER.md):

  global_inventory.py's GlobalProgramEntry (the 211-jurisdiction catalog)
  had no stable join key to program_rate_rules.py's RateRule (program_slug),
  and jurisdiction_comparison.py's JurisdictionIncentiveProfile duplicated
  every doctrine field (base_rate, max_rate, min_spend, cap, confidence_tier,
  citation) that RateRule ALSO carries — both hand-authored independently
  per jurisdiction. That is the actual duplication this module removes.

This does NOT redesign the calculation engine. RateRule, RateCondition,
resolve_program_rate(), and JurisdictionIncentiveProfile are all
UNCHANGED in shape (RateRule only gained the additive, optional
graduated_brackets field — see program_rate_rules.py). This module is a
thin data-to-engine repair: one canonical record per program_slug,
consumed to DERIVE the RateRule tuple, so the tier-level detail (rate,
band, threshold, citation) is written exactly once per program.

jurisdiction_comparison.py's JurisdictionIncentiveProfile still carries
real fields this registry does not model — marine/crew/studio capability,
VAT/WHT/payroll structural facts — because those are a genuinely
different data domain (production capability, not tax doctrine) sourced
independently. Only the OVERLAPPING doctrine fields are unified here.

Usage for a new jurisdiction:
    1. Define one DoctrineRecord below (or in a per-region module that
       imports this file) with real, cited rate tiers.
    2. Call `rate_rules_for(record)` from program_rate_rules.py to get the
       RateRule tuple — do not hand-write a parallel RateRule tuple.
    3. Read `record.base_rate` / `record.max_rate` / `record.min_spend_usd`
       / `record.annual_cap_usd` / `record.confidence_tier` directly when
       constructing the jurisdiction_comparison.py profile, instead of
       retyping the same numbers.

Existing MU/GR/IE/MT/ES/FR entries are NOT retroactively migrated onto
this registry (would touch tested, shipped code for no functional gain —
see CAPABILITY_LEDGER.md's reconciliation discipline). Every jurisdiction
added from this point forward should use it.
"""
from __future__ import annotations

#: OH-001 fix: included in canonical_evaluation._compute_fingerprint()
#: so a change to the doctrine-record registry (a new/changed program,
#: e.g. ca_bc_dave/au_pdv_offset's addition) invalidates cached served
#: evaluations rather than being silently omitted from an already-cached
#: candidate universe. Bump on any material change.
EXECUTABLE_JURISDICTION_REGISTRY_VERSION = "1.1.0"

from dataclasses import dataclass, field

from app.data.program_rate_rules import (
    RateCondition,
    RateRule,
    SourceProvenance,
    get_rate_rules,
)


@dataclass(frozen=True)
class DoctrineRateTier:
    """One tier of a DoctrineRecord's rate structure — mirrors the tier-
    level fields of RateRule so a DoctrineRecord can carry more than one
    tier (base + ceiling, or a single flat tier)."""
    tier_id: str
    rate: float
    is_band_ceiling: bool = False
    min_qpe_usd: float | None = None
    conditions: tuple[RateCondition, ...] = ()
    graduated_brackets: tuple[tuple[float, float], ...] | None = None


@dataclass(frozen=True)
class DoctrineRecord:
    """One canonical doctrine record per program_slug. This is the single
    source of truth for a program's rate/threshold/cap/citation facts —
    both the executable RateRule tuple and the jurisdiction_comparison.py
    profile's doctrine fields should read FROM this, not duplicate it."""
    jurisdiction_code: str
    program_slug: str
    program_name: str
    confidence_tier: str            # DISCOVERY | PARSED | VERIFIED
    incentive_type: str             # tax_credit | cash_rebate | grant | regional_fund
    is_refundable: bool | None
    is_transferable: bool | None
    min_spend_usd: float | None
    annual_cap_usd: float | None
    requires_cultural_test: bool
    citation: str                   # full quoted-source citation text
    source_ref: str                 # short stable reference id
    production_types: tuple[str, ...] = ("feature_film",)
    tiers: tuple[DoctrineRateTier, ...] = ()
    provenance: SourceProvenance | None = None   # structured provenance —
                                                  # see program_rate_rules.
                                                  # SourceProvenance. Threaded
                                                  # onto every derived RateRule
                                                  # by rate_rules_for() below.

    @property
    def base_rate(self) -> float | None:
        non_ceiling = [t.rate for t in self.tiers if not t.is_band_ceiling]
        return min(non_ceiling) if non_ceiling else (self.tiers[0].rate if self.tiers else None)

    @property
    def max_rate(self) -> float | None:
        return max((t.rate for t in self.tiers), default=None)


def rate_rules_for(record: DoctrineRecord) -> tuple[RateRule, ...]:
    """Derives the executable RateRule tuple from a DoctrineRecord — the
    ONE place tier data becomes a RateRule, so a new jurisdiction never
    needs a hand-written parallel RateRule tuple."""
    return tuple(
        RateRule(
            program_slug=record.program_slug,
            tier_id=tier.tier_id,
            rate=tier.rate,
            is_band_ceiling=tier.is_band_ceiling,
            production_types=record.production_types,
            min_qpe_usd=tier.min_qpe_usd,
            conditions=tier.conditions,
            confidence_tier=record.confidence_tier,
            citation=record.citation,
            source_ref=record.source_ref,
            graduated_brackets=tier.graduated_brackets,
            provenance=record.provenance,
        )
        for tier in record.tiers
    )


# Registry of every DoctrineRecord defined via this module, keyed by
# program_slug — lets program_rate_rules.py and jurisdiction_comparison.py
# both pull the same canonical record without a circular import (both
# import FROM here; this module imports from neither).
_REGISTRY: dict[str, DoctrineRecord] = {}


def register(record: DoctrineRecord) -> DoctrineRecord:
    """Registers a DoctrineRecord and returns it unchanged (so call sites
    can do `MY_RECORD = register(DoctrineRecord(...))`)."""
    _REGISTRY[record.program_slug] = record
    return record


def get_doctrine(program_slug: str) -> DoctrineRecord | None:
    return _REGISTRY.get(program_slug)


def all_doctrine_records() -> tuple[DoctrineRecord, ...]:
    return tuple(_REGISTRY.values())


def get_provenance(program_slug: str) -> SourceProvenance | None:
    """Programmatic trace PROGRAM -> EXECUTABLE RULE -> SOURCE PROVENANCE.

    Most programs go through a DoctrineRecord (the single source of truth
    rate_rules_for() derives every RateRule from), so the DoctrineRecord's
    own provenance is checked first. A small number of programs
    (es_tax_credit_foreign, fr_trip) are defined as raw RateRule tuples
    directly in program_rate_rules.py with no DoctrineRecord — for those,
    falls back to the first executable RateRule's own provenance field,
    so the trace is complete regardless of which of the two authoring
    patterns a program uses. Returns None only when neither path has a
    recorded provenance — never fabricates a value."""
    record = get_doctrine(program_slug)
    if record is not None and record.provenance is not None:
        return record.provenance
    rules = get_rate_rules(program_slug)
    return rules[0].provenance if rules else None
