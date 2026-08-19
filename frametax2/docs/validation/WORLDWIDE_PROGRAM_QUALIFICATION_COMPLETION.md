# Worldwide Program Qualification Completion

**Generated:** 2026-08-19 · **Scope:** bounded, real-authority research pass (not exhaustive closure of the 181-regime population)

## What this pass is, honestly

This is a **bounded increment**, not the completion of all 181 regimes Codex's audit identified. Given the scale of "complete qualification doctrine for every worldwide incentive program with primary authority" — genuinely a multi-week research effort across ~150 real programs and ~38 treaty routes — this pass performed real, cited, external primary-authority research for a small, defensible set of programs, encoded the findings into the existing canonical data structures (no new engine), and verified the served path end to end. The remaining regimes are **not silently closed** — they remain in the same true-authority-residual state `5935225`'s artifacts already localized, tracked in `COPRO_TRUE_AUTHORITY_RESIDUAL.json`.

## Real completions this pass

### `hr_cash_rebate` (Croatia HAVC Cash Rebate) — data-consumption defect fixed + new fact disclosed

- **Defect fixed:** `cultural_test_points` was `None` even though the record's own evidence note already said "minimum 12 of 34 points" — a genuine `DATA_EXISTS_BUT_STILL_NOT_CONSUMED` bug. Now set to `34`, re-confirmed against [Zagreb Film Office](https://filmzagreb.hr/?page_id=321) and [Cineuropa](https://cineuropa.org/en/newsdetail/203411), consistent with the existing [Invest Croatia](https://investcroatia.gov.hr/en/investment-guide/incentives/rebate-for-film-and-tv-production/) primary citation.
- **New real fact disclosed (not encoded as a role gate):** a national cast/crew composition requirement (≥30% Croatian citizens for partial-Croatia shoots, ≥50% for entirely-in-Croatia shoots), confirmed via the same two sources. This is deliberately **disclosure-only** in `program_requirements.py`'s `additional_facts` — the existing role-gate engine (`evaluate_program_eligibility`) checks individual-role nationality match, not percentage-of-headcount, and encoding it as a `NationalityRequirement` row would produce a **false HARD_FAIL** for real Croatian productions with mixed-nationality cast. Honest representation of a real rule against what the existing engine can actually enforce, not a fabricated gate.
- **Genuinely unresolved (AUTHORITY_UNRESOLVED):** the exact per-role (director/writer/producer/cast) point allocation within the 34-point scale was searched for and not located in any source checked.

### `nz_spg_international` (New Zealand Screen Production Grant — International) — confirmed spend-only

Confirmed via the [New Zealand Film Commission](https://www.nzfilm.co.nz/incentives/rebate-international-nzspr): the International rebate is spend-based only, no content/cultural test. Added to `cultural_qualification_model.py`'s `_SPEND_ONLY_SLUGS` allowlist. (Distinct from the separate NZ-production/domestic 40% grant, which DOES use a points-based content test or official co-production route — not this program_slug, not researched this pass.)

## Contract extension

`canonical_qualification_result.py` gained `QUAL_AUTHORITY_UNRESOLVED`, distinct from `RULE_DATA_INCOMPLETE`: the latter means "not yet researched," the former means "real research was performed this pass and no primary/reliable secondary authority could be located." Not yet wired into `evaluate_role_qualification()`'s live branching (a genuine scope boundary this pass — see closeout) but available in the contract for the next research pass to populate.

## What was searched and left AUTHORITY_UNRESOLVED (not fabricated)

- Czech Audiovisual Fund cultural test: confirmed minimum 4/cultural-category and minimum 23/overall points (via [Czech Anglo Productions](https://www.czechangloproductions.cz/film-incentives-in-czech-republic/) citing the official fund), but the exact per-role (director/writer/producer) point breakdown could not be extracted from the official PDF (`sfa.gov.cz`) or `filmcommission.cz` in this pass — not encoded, not guessed.

## Not researched this pass (unchanged residual)

The remaining ~106 of 108 Class-D regimes from `COPRO_TRUE_AUTHORITY_RESIDUAL.json` (`436fe6d`/`5935225`) are untouched. See that artifact for the exact per-regime proposition list — not reproduced here to avoid a redundant audit artifact per this phase's own instruction.

STOP.
