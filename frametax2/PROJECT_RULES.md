# CineGlobe Project Rules

## Canonical knowledge before research

This repository has already completed broad worldwide incentive research. Co-production, stacking, component-routing, and optimizer work must begin from the current canonical knowledge and must not restart jurisdiction research by default.

### Required workflow

1. Search the canonical runtime registries, tests, capability ledger, and Git history before using external research.
2. Classify an apparent gap as exactly one of:
   - `CANONICAL_AND_CONSUMED`
   - `EXISTS_BUT_DISCONNECTED`
   - `CANONICAL_DATA_MISSING`
   - `OPTIMIZER_CAPABILITY_MISSING`
   - `PROVENANCE_INCOMPLETE_EXISTING_RECORD`
3. For co-production/stacking work, solve connection, eligibility, combination, and ranking defects from existing data first. Do not reopen a worldwide jurisdiction audit or use provenance cleanup as a substitute for the requested optimizer exercise.
4. External research is permitted only when the user explicitly requests it or when one specific, decision-critical proposition is absent from every canonical registry and recoverable repository artifact. Research must be bounded to that proposition; never restart the country/program universe.
5. `PROVENANCE_INCOMPLETE_EXISTING_RECORD` means the rule already exists and was previously researched but its retained primary-source metadata is incomplete. It is a database-maintenance residual, not an “unresearched jurisdiction,” and does not block co-production/stacking unless the missing proposition is required for the exact decision being made.
6. Validation documents, model reports, comments, and free-text notes are evidence/recovery inputs only. They are never runtime truth. If valid doctrine is found there, migrate it into the appropriate canonical owner and add a recurrence test.
7. Do not create a parallel registry, optimizer, or calculation path. Extend the existing canonical owner and served bridge.
8. Do not treat historical population counts such as 71, 84, or 121 as completion truth. Derive counts from the current live canonical registry and explain any movement by program and structure type.
9. Candidate-count changes must be fully attributed. For a recovered program, identify each added `full_relocation`, `component_relocation`, stack, or co-production candidate and prove why it exists.
10. Broad research, broad validation, and provenance backfill require a separate explicit task. They are not implicit follow-ons to a bounded co-production/stacking prompt.

### Canonical data ownership map

The knowledge base is consolidated by domain, not forced into one oversized file:

| Domain | Canonical owner / served entry |
|---|---|
| Program identity and rate doctrine | `backend/app/data/executable_jurisdiction_registry.py`, populated by `backend/app/data/program_rate_rules_worldwide.py` and resolved only through `backend/app/data/program_rate_rules.py` |
| QPE category and territorial treatment | `backend/app/data/program_spend_rules.py` |
| Program qualification, timing, compliance, and monetization facts | `backend/app/data/program_requirements.py` |
| Role/nationality and cultural qualification | `backend/app/data/cultural_qualification_model.py` and `backend/app/data/cultural_point_tables.py`, consumed through `backend/app/calculators/canonical_role_qualification_bridge.py` |
| National/cultural status | `backend/app/data/national_cultural_status.py` |
| Treaty and official co-production frameworks | `backend/app/calculators/treaty_engine.py`, consumed through `backend/app/calculators/canonical_treaty_bridge.py` |
| Stacking compatibility and adjustments | `backend/app/optimization/stacking_rules.py`, consumed through `backend/app/calculators/canonical_stack_bridge.py` |
| Economic-candidacy exclusions | `backend/app/data/authority_coverage_registry.py` |
| Structured authority coverage classification | `backend/app/data/program_authority_provenance.py` |
| Served project evaluation and admission | `backend/app/services/canonical_evaluation.py` |
| Served publication/view | `backend/app/services/canonical_production_view.py` |
| Historical decisions and deferred work | `docs/architecture/CAPABILITY_LEDGER.md` — documentary only, never runtime truth |

The recurrence guard is `backend/tests/test_canonical_knowledge_consolidation.py`. Any new canonical program or recovered doctrine must resolve through the existing rate/qualification/served path, carry the best recoverable structured provenance, and remain excluded from deterministic recommendation while required eligibility facts are unresolved.
