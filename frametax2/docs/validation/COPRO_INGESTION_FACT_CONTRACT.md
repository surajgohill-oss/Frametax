# Co-production Ingestion Fact Contract

Canonical Co-production Qualification Reconnection, Task 15/16. Reuses Codex's own "Script Analyzer contract delta" findings (`CODEX_COPRO_ROLE_QUALIFICATION_COMPLETENESS.md`) verbatim — no new research performed. Distinguishes PROJECT/USER facts (collected now, before any Script Analyzer work) from SCRIPT-DERIVED facts (supplied later by a future Script Analyzer phase) from PROPOSED-STRUCTURE facts (never Script Analyzer facts).

**All facts below allow UNKNOWN.** Regime-specific qualification (`canonical_role_qualification_bridge.py`) requests them only when a real regime's own rule data actually needs them — never a blanket global requirement.

## Project / user facts needed now

- Elected program/test/treaty and certification route.
- Applicant and each co-producer legal entity: registration, tax/legal residence, accreditation, member-state status.
- Named writer, director, producer, composer, editor, cast, department heads, key creatives — role, attachment/confirmation status, nationality and legal residency kept SEPARATE (never conflated). This is exactly what `ProjectPerson` → `TalentProfile` already persists (`primary_nationality`, `known_residencies`) and `canonical_role_qualification_bridge.role_known_codes_from_project()` now reads into the canonical served path.
- Cast-day/crew-day totals by qualifying nationality/residency where a test uses percentages.
- Per-country finance contribution, production-spend contribution, rights share, ownership/control, recoupment, territorial exploitation rights.
- Actual/planned principal-photography jurisdictions, shoot days/percentages; actual/planned post, VFX, animation, edit, sound, music work locations.
- Production type, total budget, local qualifying spend, co-producer count, majority/minority election, formal co-production approval status.
- Known cultural-certificate answers supplied by producer/counsel, with source and review status.

Two new `ProjectFact` keys this pass's treaty-bridge repair now reads (never invented, absent = None, never assumed compliant): `coproduction_majority_pct`, `coproduction_minority_pct`, `coproduction_cultural_test_passed`.

## Script-derived facts needed later (future Script Analyzer phase)

- Story setting and geographic/national locus.
- Lead-character identity where the official test scores character nationality/residency (not performer nationality).
- Subject matter, cultural themes, heritage, diversity, identity, artistic/cultural contribution.
- Original dialogue and production-language proportions.
- Underlying work/source-material and rights provenance where a test scores them.
- Scene-derived location, practical-effects, VFX, animation, post-production scope — not the eventual vendor or work location.

These map to `screen_analyzer_fact_contract.py`'s existing `fact_key` registry (added in the prior Proactive Opportunity Discovery phase).

## Proposed-structure facts, never Script Analyzer facts

- Proposed attachment/substitution of a qualifying creative role.
- Proposed treaty partner, co-producer count, finance/spend/rights-share rebalance.
- Proposed entity, ownership, control, copyright allocation.
- Proposed relocation of shooting, post, VFX, animation, edit, sound, music.

## Known naming-drift note (Task 16), not corrected this pass

Codex's own audit surfaces the canonical product name as **Script Analyzer**; the existing module from the prior phase is named `app/calculators/screen_analyzer_fact_contract.py`. Per this phase's explicit instruction ("do not undertake a broad rename of functioning code... unless a newly-created UNUSED module can be renamed safely"), this module is already consumed by `canonical_opportunity_bridge.discover_cultural_test_gap_opportunity()` — not unused — so it is **not renamed this pass**. Flagged here for a future phase's disclosure, not silently fixed.

STOP.
