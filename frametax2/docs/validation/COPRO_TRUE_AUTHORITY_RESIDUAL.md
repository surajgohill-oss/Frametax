# CoPro True Authority Residual
Mechanical transform of `CODEX_COPRO_ROLE_QUALIFICATION_COMPLETENESS.json` after the Canonical Co-production Qualification Reconnection pass. No new research performed — every field is either copied verbatim from Codex's own audit or computed from this session's actual reconnected code.
**Population:** 181 regimes (same denominator as Codex's audit, never reconstructed).
## What changed this pass
- **24 regimes** (the exact set covered by `cultural_qualification_model.py`'s real `NationalityRequirement` registry) now have their role/nationality hard-gate dimension genuinely consumed by the canonical served path (`canonical_role_qualification_bridge.py` → `canonical_evaluation._role_qualification_for_candidate()`).
- **37 bilateral/Eurimages treaty entries** now have real `majority_pct`/`minority_pct`/`cultural_test_passed` plumbing (read from `ProjectFact`) instead of the previous hardcoded `None`/`UNRESOLVED_FACTS` — the underlying creative-role rule data for these treaties was never captured in the first place (Codex's own finding: "no creative-role schema"), so this is a plumbing repair, not a data-completeness improvement.

## True residual classification (Task 13)
| Class | Count | Meaning |
|---|---:|---|
| A — DATA_EXISTS_AND_CONSUMED | 0 | Fully consumed regime (every captured dimension reaches canonical evaluation). None yet — role-gate consumption alone is not full consumption. |
| B — DATA_EXISTS_BUT_STILL_NOT_CONSUMED | 0 | Implementation defect requiring repair. Zero remaining after this pass — the 5 regimes Codex flagged `EXISTING_DATA_NOT_WIRED` are now wired for their role dimension. |
| C — DATA_PARTIAL | 73 | Real data exists and is now partially consumed (role dimension where covered); other dimensions (points/contribution/ownership/story/language/etc.) remain genuinely missing or unconsumed. |
| D — NO_ROLE_LEVEL_DATA | 108 | Untouched this pass. No role/nationality rule data exists anywhere in this codebase — genuine authority research required (propositions preserved from Codex's `targeted_research_set`, no new research performed here). |
| E — NOT_APPLICABLE | 0 | No additional rule needed (confirmed spend-only). |

## Canonical consumption after this pass
| State | Count |
|---|---:|
| UNCHANGED | 121 |
| ROLE_DIMENSION_CONSUMED_OTHER_DIMENSIONS_PARTIAL | 24 |
| TREATY_PLUMBING_REPAIRED_ROLE_DATA_STILL_MISSING | 36 |

## Regimes requiring genuine authority research (Class D)
108 regimes. Exact propositions per regime are preserved in `COPRO_TRUE_AUTHORITY_RESIDUAL.json`'s own `exact_missing_propositions` field (Codex's `targeted_research_set`, unchanged, no new research). Typical proposition set: `CULTURAL_TEST_APPLICABILITY_AND_CERTIFICATION_ROUTE`, `WRITER_STATUS_TREATMENT`, `DIRECTOR_STATUS_TREATMENT`, `PRODUCER_STATUS_TREATMENT`, `CAST_STATUS_TREATMENT`, `COMPOSER_EDITOR_AND_KEY_CREATIVE_TREATMENT`, `STORY_SETTING_SUBJECT_AND_LANGUAGE_CRITERIA`, `SHOOTING_POST_VFX_ACTIVITY_CRITERIA`, `OWNERSHIP_CONTROL_REQUIREMENTS`, `CONTRIBUTION_AND_COPRODUCER_SHARE_REQUIREMENTS`, `NATIONALITY_RESIDENCY_DEFINITIONS`, `COMPLETE_CRITERIA_POINTS_WEIGHTS_AND_PASS_THRESHOLD`.

## Regimes requiring NO additional research (role dimension resolved)
24 regimes' role/nationality hard-gate dimension is fully resolved by existing data (`cultural_qualification_model.py`) — no further authority research needed for THAT dimension specifically. Their other dimensions (points scoring, contribution, ownership) remain in Class C.

STOP.
