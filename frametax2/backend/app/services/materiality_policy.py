"""ONE canonical owner of the CineGlobe optimizer materiality policy constant.

CANONICAL OPTIMIZER RECOMMENDATION METHODOLOGY CLOSEOUT (2026-09-30), item 6
("Consolidate all materiality logic into one canonical owner"): before this
module existed, `MATERIALITY_THRESHOLD_PER_ADDITIONAL_JURISDICTION_USD` was
defined once in canonical_production_view.py, and a second, independent
literal `100_000.0` was hardcoded directly in
structural_archetype_generator.py's `generate_structural_candidate` (its own
internal, disclosure-only `materiality_recommended` search signal). The two
values happened to agree, but nothing prevented them from silently
diverging — a future change to one would not touch the other. Both modules
now import the SAME constant from here; canonical_production_view.py's own
`materiality_recommendation_threshold_usd()` (the one function that actually
computes the served, jurisdiction-count-scaled recommendation threshold)
remains there, since it is served-view logic, not a raw constant, and moving
it here would not change which module owns the actual recommendation
decision. This module exists only so the raw dollar constant itself can
never fork.

`app/calculators/structural_archetype_generator.py` is imported by
`canonical_evaluation.py` (backend/service layer) and must never import
`canonical_production_view.py` (a higher, view-serving layer) directly --
this tiny, dependency-free module is the shared leaf both can import without
risk of a circular import.
"""

MATERIALITY_THRESHOLD_PER_ADDITIONAL_JURISDICTION_USD = 100_000.0
