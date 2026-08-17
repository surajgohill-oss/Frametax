"""
historical_program_type_recovery.py

Codex authority delta recovery, Task 3 — a small, program_slug-keyed
registry of program-type dispositions recovered from EXACT source-linked
propositions in docs/validation/CODEX_HISTORICAL_AUTHORITY_SOURCE_CROSS_
REFERENCE.json's `program_type_recovery.explicit_candidates` (itself
sourced from GLOBAL_REMEDIATION_EXECUTABLE_DATA.json exact canonical-ID
matches and app.data.global_inventory.ALL_PROGRAMS unique exact
normalized full-name matches). No type here was inferred from a program
name; every entry traces to one or more exact-match source records.

This registry deliberately does NOT import or replicate any validation
artifact wholesale — only the specific type proposition for each program,
after adjudication, is recorded here. See the closeout artifact
(docs/validation/CODEX_AUTHORITY_DELTA_RECOVERY_CLOSEOUT.md) for the full
per-program adjudication reasoning, including which of the 45 Codex
candidates were left unresolved and why.

Classification rule applied uniformly:
  - cash_rebate / rebate / tax_credit / direct_grant (non-conflicting) ->
    FORMULAIC (an automatic-entitlement cash-flow mechanism; direct_grant
    maps to the same AUTOMATIC_FORMULA_GRANT-equivalent bucket the rest of
    the canonical universe already uses for formulaic dispositions).
  - development_fund / co_production_fund (non-conflicting) ->
    NON_ECONOMIC_SUPPORT (development/co-production funding is not a
    production tax incentive).
  - production_support (bare, non-conflicting) -> left unresolved: too
    ambiguous on its own to distinguish a formulaic cash program from a
    discretionary support scheme without reading the underlying rule text
    (new research, out of scope).
  - Two-type CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION records -> left
    unresolved UNLESS both conflicting type strings describe the exact
    same underlying economic mechanism under a different label (the only
    case found: "cash_rebate" vs "rebate" — a terminology variance, not a
    genuine disagreement about the financial instrument). All other
    conflicts (direct_grant vs equity/loan, grant vs production_support,
    advance vs direct_grant/co_production_fund, discretionary_fund vs
    grant) describe genuinely different instruments and are left
    unresolved, per the source instruction to preserve CONFLICT rather
    than guess.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RecoveredDisposition = Literal["FORMULAIC", "NON_ECONOMIC_SUPPORT"]


@dataclass(frozen=True)
class RecoveredProgramType:
    canonical_program_id: str
    disposition: RecoveredDisposition
    historical_type: str
    provenance: str


_RECOVERED: dict[str, RecoveredProgramType] = {}


def _register(canonical_program_id: str, disposition: RecoveredDisposition, historical_type: str, provenance: str) -> None:
    _RECOVERED[canonical_program_id] = RecoveredProgramType(canonical_program_id, disposition, historical_type, provenance)


def recovered_program_type(canonical_program_id: str) -> RecoveredProgramType | None:
    return _RECOVERED.get(canonical_program_id)


def all_recovered_program_types() -> dict[str, RecoveredProgramType]:
    return dict(_RECOVERED)


# ── Non-conflicting EXPLICIT_RECOVERY_CANDIDATE records: cash_rebate /
# rebate / tax_credit / direct_grant -> FORMULAIC ───────────────────────

for _slug, _type in (
    ("ar_incaa_incentive", "cash_rebate"),
    ("au_qld_screen_qld", "cash_rebate"),
    ("bc_interactive_digital_media_tax_credit_idmtc", "tax_credit"),
    ("br_ancine_incentive", "tax_credit"),
    ("ca_federal_cptc", "tax_credit"),
    ("ca_nl_production_fund", "tax_credit"),
    ("dk_film_incentive", "direct_grant"),
    ("gb_sct_screen_fund", "cash_rebate"),
    ("gb_wls_screen_fund", "cash_rebate"),
    ("in_national_film", "direct_grant"),
    ("jm_film_incentive", "tax_credit"),
    ("mx_eficine_incentive", "tax_credit"),
    ("new_zealand_screen_production_grant_—_international_post_vfx", "cash_rebate"),
    ("on_ofttc", "tax_credit"),
    ("ontario_computer_animation_and_special_effects_tax_credit_ocase", "tax_credit"),
    ("pe_film_incentive", "direct_grant"),
    ("qc_film_production", "tax_credit"),
    ("uy_xxi_incentive", "cash_rebate"),
):
    _register(
        _slug, "FORMULAIC", _type,
        "CODEX_HISTORICAL_AUTHORITY_SOURCE_CROSS_REFERENCE.json program_type_recovery.explicit_candidates "
        f"(EXPLICIT_RECOVERY_CANDIDATE, single non-conflicting type={_type!r}, GLOBAL_REMEDIATION_EXECUTABLE_DATA.json "
        "exact canonical_id match + global_inventory unique exact normalized full-name match)",
    )

# ── Non-conflicting EXPLICIT_RECOVERY_CANDIDATE records: development_fund
# / co_production_fund -> NON_ECONOMIC_SUPPORT ──────────────────────────

for _slug, _type in (
    ("in_nfdc_coproduction", "co_production_fund"),
    ("us_itvs_fund", "development_fund"),
    ("us_sundance_doc", "development_fund"),
):
    _register(
        _slug, "NON_ECONOMIC_SUPPORT", _type,
        "CODEX_HISTORICAL_AUTHORITY_SOURCE_CROSS_REFERENCE.json program_type_recovery.explicit_candidates "
        f"(EXPLICIT_RECOVERY_CANDIDATE, single non-conflicting type={_type!r}; development/co-production funding "
        "is not a production tax incentive)",
    )

# ── CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION records resolved as a
# terminology variance, not a genuine disagreement: "cash_rebate" vs
# "rebate" both describe the same cash-rebate mechanism -> FORMULAIC ───

for _slug in ("au_nsw_screen", "au_vic_vicscreen", "pt_film_incentive"):
    _register(
        _slug, "FORMULAIC", "cash_rebate/rebate",
        "CODEX_HISTORICAL_AUTHORITY_SOURCE_CROSS_REFERENCE.json program_type_recovery.explicit_candidates "
        "(CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION resolved: GLOBAL_REMEDIATION_EXECUTABLE_DATA.json says "
        "'cash_rebate', a second source says 'rebate' -- both name the identical cash-flow mechanism under "
        "different label granularity, not a genuine instrument-type disagreement)",
    )
