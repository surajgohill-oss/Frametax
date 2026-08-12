"""
authority_coverage_registry.py

Consolidated Global Remediation, Phase C: an explicit, deterministic
coverage-status record for the 25 canonical identities the distributed
validation gate (docs/validation/GLOBAL_VALIDATION_GATE.md) adjudicated
UNPRICEABLE_AUTHORITY_INSUFFICIENT, plus the 4 EXCLUDE_NON_ECONOMIC
identities (facilitation/market-access bodies, not producer economic
incentives) — see docs/validation/GLOBAL_REMEDIATION_INPUT.json's
`coverage_limitations` and the four EXCLUDE_NON_ECONOMIC implementation
items.

Before this module, "not priceable" was only an IMPLICIT fact — these
jurisdictions' GlobalProgramEntry rows (global_inventory*.py) simply
have confidence_tier=DISCOVERY and no program_slug, so no RateRule/
DoctrineRecord exists and the executable pricing path has nothing to
join to (see executable_jurisdiction_registry.py's DoctrineRecord and
the ledger's own finding: "a missing statutory rate still blocks — no
rule can supply a number that does not exist"). That implicit fact
already made pricing/ranking safe; nothing here changes that. What was
missing was an EXPLICIT record of *why*, distinguishing "not yet
examined" from "examined and confirmed authority-insufficient" or
"examined and confirmed non-economic" — required for honest reporting
and for a future reactivation pass to know exactly what remains to be
sourced, per the remediation's own Phase C requirement ("preserve
enough metadata for future authority refresh/reactivation").

This module adds NO rate, NO threshold, NO synthetic economics. It is
read by tests only (see tests/data/test_authority_coverage_registry.py)
and is safe to consult from a future coverage/gap UI surface. It is
NOT imported by any calculator, discovery, pricing, or ranking module —
consult get_coverage_status()/is_covered_unpriceable() before adding
such an import, and if you do, the correct behavior is EXCLUSION, never
substitution with a default/generic rate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CoverageDisposition = Literal[
    "UNPRICEABLE_AUTHORITY_INSUFFICIENT",
    "NON_ECONOMIC_CONFIRMED",
]


@dataclass(frozen=True)
class AuthorityCoverageRecord:
    program_slug: str
    jurisdiction_code: str | None
    jurisdiction_name: str
    disposition: CoverageDisposition
    reason: str
    source_artifact: str
    reactivation_note: str


# jurisdiction_code left None where the canonical research pass did not
# pin a specific ISO code to the slug (all of these are single-country
# jurisdictions identifiable by jurisdiction_name in ALL_PROGRAMS today).
_UNPRICEABLE: tuple[tuple[str, str, str], ...] = (
    ("bh_film_incentive", "BH", "Bahrain"),
    ("bd_film_incentive", "BD", "Bangladesh"),
    ("eg_film_incentive", "EG", "Egypt"),
    ("et_film_commission", "ET", "Ethiopia"),
    ("ga_film_incentive", "GA", "Gabon"),
    ("gh_film_incentive", "GH", "Ghana"),
    ("id_film_incentive", "ID", "Indonesia"),
    ("kz_film_incentive", "KZ", "Kazakhstan"),
    ("ke_film_incentive", "KE", "Kenya"),
    ("kw_film_incentive", "KW", "Kuwait"),
    ("mv_film_incentive", "MV", "Maldives"),
    ("mn_film_commission", "MN", "Mongolia"),
    ("mz_film_incentive", "MZ", "Mozambique"),
    ("ng_film_incentive", "NG", "Nigeria"),
    ("om_film_commission", "OM", "Oman"),
    ("pk_pfc_rebate", "PK", "Pakistan"),
    ("qa_film_incentive", "QA", "Qatar"),
    ("sn_film_incentive", "SN", "Senegal"),
    ("sc_film_incentive", "SC", "Seychelles"),
    ("lk_film_incentive", "LK", "Sri Lanka"),
    ("ug_film_commission", "UG", "Uganda"),
    ("uz_film_incentive", "UZ", "Uzbekistan"),
    ("vn_film_incentive", "VN", "Vietnam"),
    ("zm_film_commission", "ZM", "Zambia"),
    ("zw_film_commission", "ZW", "Zimbabwe"),
)

_NON_ECONOMIC: tuple[tuple[str, str, str], ...] = (
    ("bw_film_commission", "BW", "Botswana"),
    ("kh_film_incentive", "KH", "Cambodia"),
    ("cn_film_incentive", "CN", "China"),
    ("tz_film_incentive", "TZ", "Tanzania"),
)

_REASON_UNPRICEABLE = (
    "Distributed three-lane primary-authority research (Codex/Gemini/Claude) "
    "reached at least one direct search attempt but could not confirm a "
    "current, citable rate/mechanism sufficient for deterministic pricing "
    "-- either no program was locatable at all, a real program exists but "
    "its rate/formula is unconfirmed, or sources directly conflict on "
    "whether any current incentive exists. Adjudicated "
    "UNPRICEABLE_AUTHORITY_INSUFFICIENT at the final distributed gate "
    "(docs/validation/GLOBAL_VALIDATION_GATE.md), not "
    "NO_CURRENT_PRODUCER_INCENTIVE_CONFIRMED and not TRUE_BLOCKING_RULE_GAP."
)

_REASON_NON_ECONOMIC = (
    "Research confirmed the jurisdiction's national film body is a "
    "facilitation / market-access / co-production-registration authority "
    "(e.g. permits, location scouting, official co-production status) "
    "rather than a producer-facing rebate, tax credit or grant -- there is "
    "no economic instrument to price. Excluded from optimizer candidacy by "
    "design, not because authority is insufficient."
)

_SOURCE_UNPRICEABLE = "docs/validation/GLOBAL_REMEDIATION_INPUT.json:coverage_limitations"
_SOURCE_NON_ECONOMIC = "docs/validation/GLOBAL_REMEDIATION_INPUT.json:implementation_items[EXCLUDE_NON_ECONOMIC]"

_REACTIVATION_NOTE = (
    "To reactivate: locate the matching GlobalProgramEntry in "
    "app/data/global_inventory*.py by jurisdiction_name (program_slug is "
    "None today -- these were never promoted to executable), source a "
    "current primary-authority rate/rule, add a DoctrineRecord to "
    "executable_jurisdiction_registry.py via register_rate_rules(), THEN "
    "remove the record from this registry. Never skip the DoctrineRecord "
    "step -- setting program_slug alone does not create a priceable rule."
)

COVERAGE_REGISTRY: dict[str, AuthorityCoverageRecord] = {}

for _slug, _code, _name in _UNPRICEABLE:
    COVERAGE_REGISTRY[_slug] = AuthorityCoverageRecord(
        program_slug=_slug,
        jurisdiction_code=_code,
        jurisdiction_name=_name,
        disposition="UNPRICEABLE_AUTHORITY_INSUFFICIENT",
        reason=_REASON_UNPRICEABLE,
        source_artifact=_SOURCE_UNPRICEABLE,
        reactivation_note=_REACTIVATION_NOTE,
    )

for _slug, _code, _name in _NON_ECONOMIC:
    COVERAGE_REGISTRY[_slug] = AuthorityCoverageRecord(
        program_slug=_slug,
        jurisdiction_code=_code,
        jurisdiction_name=_name,
        disposition="NON_ECONOMIC_CONFIRMED",
        reason=_REASON_NON_ECONOMIC,
        source_artifact=_SOURCE_NON_ECONOMIC,
        reactivation_note=_REACTIVATION_NOTE,
    )

del _slug, _code, _name


def get_coverage_status(program_slug: str) -> AuthorityCoverageRecord | None:
    """None means either fully covered/priceable, or not yet examined --
    this registry only holds CONFIRMED exclusions, never a default."""
    return COVERAGE_REGISTRY.get(program_slug)


def is_covered_unpriceable(program_slug: str) -> bool:
    rec = COVERAGE_REGISTRY.get(program_slug)
    return rec is not None and rec.disposition in (
        "UNPRICEABLE_AUTHORITY_INSUFFICIENT",
        "NON_ECONOMIC_CONFIRMED",
    )
