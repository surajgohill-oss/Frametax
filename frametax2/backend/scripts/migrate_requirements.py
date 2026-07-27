"""
migrate_requirements.py — Pass A reconciliation report.

The actual migration (9 profiles: mu_edb_incentive, mt_mfc_rebate,
gr_cash_rebate, us_or_opif, ma_ccm_rebate, kr_kofic_location_incentive,
fj_film_rebate, my_finas_rebate, lt_film_centre_cash_rebate) is permanent,
loaded at import time from app/data/program_requirements.py itself (same
place, same pattern as every other profile in this registry) — not from
running this script. This script is the read-only AUDIT TRAIL: it re-runs
the reconciliation survey that justified the migration, confirms the 9
profiles are live, and confirms every still-unprofiled jurisdiction's gap
is documented in jurisdiction_comparison.ALL_PROFILES[code].data_gaps.

RECONCILIATION PERFORMED BEFORE THE MIGRATION WAS WRITTEN:

1. program_rate_rules.py / program_rate_rules_worldwide.py — RateCondition
   records. Surveyed all condition `kind`s across the 88 executable
   jurisdictions that lacked a requirements profile. Only 3 kinds carry
   information within the ProgramRequirementsProfile's domain:
     - min_qpe_usd            -> min_local_spend_usd (direct, unambiguous)
     - cultural_test_required -> cultural_test_required (direct, unambiguous)
     - min_spend_pct_of_total_budget / discretionary_band -> read case by
       case; only asserted where the condition's own quote UNAMBIGUOUSLY
       states the fact in the requirements-profile's terms (FJ: "locally
       registered company" -> local_entity_required; MU: CEO "shall
       approve projects" -> preapproval_mandatory + DISCRETIONARY
       allocation; US-OR: fund cap + "not guaranteed even if criteria are
       met" -> DISCRETIONARY allocation). No free-text pattern-matching
       was run over the other 42 discretionary_band conditions — each was
       read individually; the overwhelming majority describe RATE-BAND
       uncertainty (guaranteed floor vs. modeled ceiling), not program-
       level allocation scarcity, so asserting a field from those would be
       an unsupported inference, not a migration.
   The remaining condition kinds (discretionary_band in the ordinary
   rate-ceiling sense, material_funding_risk_not_modeled,
   no_sponsorship_in_qpe, production_type, rate_base_narrower_than_qpe,
   graduated_bracket_applied) correspond to NO ProgramRequirementsProfile
   field — they are pricing/QPE-derivation facts, a different data domain
   by this module's own design (see program_requirements.py's docstring).

2. program_spend_rules.py — SpendRule's fields are (program_slug,
   spend_category, qualifies, territorial_only, confidence_tier, notes,
   source_ref). This is a QPE-INCLUSION registry (does spend category X
   count as qualifying spend), a structurally DIFFERENT question from
   ProgramRequirementsProfile's eligibility/operational facts. Zero
   fields migrated from this module — doing so would be a category error.

3. Existing requirements profiles / evidence records / executable
   registry / generated registries: already fully connected (0 orphans,
   110/110 reachable, verified in the prior closeout pass).

4. "Legacy FrameTax data still present in the repository": searched for
   any module matching *frametax*/*legacy* under app/ — none found.

RESULT: 9 jurisdictions gained a genuinely new, internally-sourced
ProgramRequirementsProfile. The other 79 (of 88) got NOTHING invented —
no hollow all-None profile object was created for them, because doing so
would fabricate an evidence citation for a profile with no real evidence
behind it (the schema requires one EvidenceRecord per profile; there is
no honest way to cite "nothing" as SourceType.PRIMARY or SECONDARY).
Their gaps are documented as free-text notes in jurisdiction_comparison.
ALL_PROFILES[code].data_gaps — pre-existing for most; a factual gap note
("no ProgramRequirementsProfile exists yet ... Pass A migration found
nothing internally derivable") was added for the 7 that had an empty list
(BG, CA-MB, CA-NB, DO, SK, US-MA, US-MD).

Run with:
    cd backend && source .venv/bin/activate && python scripts/migrate_requirements.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.data.program_rate_rules  # noqa: F401 - circular-import warm-up
from app.calculators.jurisdiction_comparison import ALL_PROFILES
from app.data.canonical_executable_registry import canonical_executable_jurisdictions
from app.data.program_rate_rules import get_rate_rules
from app.data.program_requirements import _REGISTRY, get_program_requirements

MIGRATED_SLUGS = [
    "mu_edb_incentive", "mt_mfc_rebate", "gr_cash_rebate", "us_or_opif",
    "ma_ccm_rebate", "kr_kofic_location_incentive", "fj_film_rebate",
    "my_finas_rebate", "lt_film_centre_cash_rebate",
]


def survey_condition_kinds(missing_codes: dict) -> dict:
    tally: dict[str, int] = {}
    for code, e in missing_codes.items():
        for r in get_rate_rules(e.primary_program_slug) or []:
            for cond in r.conditions:
                tally[cond.kind] = tally.get(cond.kind, 0) + 1
    return tally


if __name__ == "__main__":
    ex = canonical_executable_jurisdictions()

    print("=== Pass A verification ===")
    for slug in MIGRATED_SLUGS:
        p = get_program_requirements(slug)
        status = "PRESENT" if p is not None else "MISSING (migration not loaded!)"
        print(f"  {slug:32} {status}")

    still_missing = {code: e for code, e in ex.items()
                      if get_program_requirements(e.primary_program_slug) is None}
    print()
    print(f"Requirements registry size: {len(_REGISTRY)}")
    print(f"Executable jurisdictions still unprofiled: {len(still_missing)}")

    kind_tally = survey_condition_kinds(still_missing)
    in_domain = {"min_qpe_usd", "cultural_test_required"}
    out_of_domain = sorted(set(kind_tally) - in_domain -
                            {"min_spend_pct_of_total_budget", "discretionary_band"})
    print(f"Condition kinds remaining across unprofiled jurisdictions: {kind_tally}")
    print(f"Out-of-domain kinds (no ProgramRequirementsProfile field exists for these): "
          f"{out_of_domain}")

    print()
    undocumented = [code for code in still_missing
                    if not getattr(ALL_PROFILES.get(code), "data_gaps", None)]
    print(f"Still-unprofiled jurisdictions with NO data_gaps documentation: {undocumented}")
    if not undocumented:
        print("None — every remaining jurisdiction's gap is documented in "
              "jurisdiction_comparison.ALL_PROFILES[code].data_gaps.")
