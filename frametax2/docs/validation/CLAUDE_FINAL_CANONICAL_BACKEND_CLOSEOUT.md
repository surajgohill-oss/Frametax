# Final Canonical Backend Closeout — Policy Correction + Provenance Recovery

Summary only. Prior artifact `CLAUDE_PROMPT16_AUTHORITY_DISPOSITION.json` (and its
now-superseded closeout MD) documents the state before this pass; this document
records the correction and the new terminal state.

## The correction

Prompt 16's fail-closed quarantine conflated two independent dimensions:
**economic determinism** (can the rate/base/cap/conditions be calculated) and
**provenance completeness** (is that rate/base/cap backed by a structured,
normalized primary-authority record). Treating incomplete structured provenance
as an automatic economic kill switch made 58 previously-accepted, real programs
non-priceable even though none of them had a genuinely unresolved rate — every
one already carried a real `RateRule` this project had previously adjudicated to
one usable figure.

**The fix is a single policy change, not 58 special cases:**
`AUTHORITY_UNRESOLVED_NON_PRICEABLE` was removed from
`authority_coverage_registry.py`'s `BLOCKING_STATES`. It remains a real, reported
state — `program_authority_provenance.py` still classifies and surfaces it — but
it no longer suppresses economics. A program genuinely blocked for a *different*,
real economic reason (material rule unresolved, superseded, non-economic,
selective/competitive) is unaffected and still fails closed by every route.

## Internal provenance recovery — 23 of 58 promoted, zero new research

Before applying the policy correction, a genuine internal recovery pass was run
across the fixed 58-program cohort. It found a **second existing canonical
provenance store** — `program_requirements.py`'s `EvidenceRecord` objects,
attached to `ProgramRequirementsProfile` — that Prompt 16 had never
cross-referenced against `program_rate_rules`'s own `SourceProvenance`. 23 of the
58 already carried a `SourceType.PRIMARY` `EvidenceRecord` there: real government
agencies (Belgium's FPS Finance, Chile's Corfo, Denmark's Slots- og
Kulturstyrelsen, Malaysia's FINAS, Thailand's TFO, and 18 others), most with a
real source document title and URL. That data was copied — never re-derived or
guessed — into a `SourceProvenance` object on every affected `RateRule` tier.

One case deserved a closer look before trusting it: `be_tax_shelter`'s FPS
Finance source describes a "310% of investor deposits" exemption, while the
modeled `RateRule` prices a 42–44% producer-net rate — a mismatch a much older
comment in `authority_coverage_registry.py` had flagged and left unresolved. The
same `EvidenceRecord` this pass found also contains a later, dated (2026-07-26)
reconciliation note: the 310% investor-side exemption and the 42–44%
producer-net figure are two sides of the *same* mechanism (investor exemption vs.
what the production nets through the intermediary structure) and are explicitly
confirmed non-contradictory. The old flag was stale, already resolved by
knowledge this project already held; this pass only needed to find it.

**Result: 88 of 123 programs now `AUTHORITY_VERIFIED_PRICEABLE`** (up from 65),
**35 remain `AUTHORITY_UNRESOLVED_NON_PRICEABLE`** — a real, disclosed, non-blocking
provenance-completeness gap, not an economic block.

## Economic-state accounting (the axis that matters for pricing)

| Economic state | Count |
|---|---|
| `DETERMINISTIC_PRICEABLE` | 108 |
| `CONDITIONAL_NONDETERMINISTIC` (competitive/selective, or ceiling-only tiers) | 12 |
| `MATERIAL_ECONOMIC_RULE_UNRESOLVED` | 2 |
| `SUPERSEDED` | 1 |

`108 + 12 + 2 + 1 = 123`. Only **6 programs remain economically blocked** —
exactly the original 6 non-served programs (`us_or_opif`, `jo_rfc_rebate`,
`kr_kofic_location_incentive`, `jp_vipo_location_incentive`,
`kz_investment_subsidy`, `ae_dxb_dpip`), each for its own real, pre-existing
reason, unrelated to structured provenance and unchanged by this pass.

Two of those six (`us_or_opif`, `jp_vipo_location_incentive`) happened to also be
in the internally-recovered 23 — their provenance was genuinely promoted to
`AUTHORITY_VERIFIED_PRICEABLE`, but they remain economically blocked for their own
separate, pre-existing reason. That is the intended shape of two independent
axes, not a bug: recovering a program's provenance is real, correct work even
when a different gap still legitimately blocks it economically.

## Controls — zero economic delta

| Control | Before | After | Change |
|---|---|---|---|
| LU NPC | $3,057,794.90 | $3,057,794.90 | **$0** |
| FVD NPC | $3,072,027.16 | $3,072,027.16 | **$0** |
| LU candidate count | 201 | 201 | **0** |

Neither Mauritius (LU) nor Greece (FVD) was among the 58, so the controls are
correctly unaffected. Restoration was verified directly against real candidates
that *were* affected: Italy, Belgium, Malta and Poland relocation candidates in
LU's own served structure list moved from `npc = None` (quarantined) to real
priced NPCs ($4,046,114.60 / $4,039,970.68 / $3,906,254.20 / $4,289,684.00
respectively) — proof the restoration reaches the actual served path, not just
the classifier.

## Safety preserved

- `test_economically_blocked_program_cannot_price_via_direct_price_segment` —
  the six genuinely-blocked programs still cannot price via the direct-call
  route that bypasses discovery.
- `test_economically_blocked_programs_never_appear_in_served_ranking_with_economics`
  — 301 real priced segments inspected in the live LU structure list; zero
  blocked programs carry incentive value.
- `test_a_program_can_be_provenance_unresolved_yet_economically_priceable` —
  proven against real registry programs, not a synthetic example.
- No qualification, stacking, co-production, or ranking logic was touched.

## Tests

Full backend suite: **4455 passed, 0 failed, 1 skipped** (up from 4450 — 5 new
tests covering the corrected policy; two pre-existing tests updated to match the
corrected model rather than weakened: one now checks provenance-vs-economic
independence directly instead of assuming verified implies unblocked; the other
recognizes `AUTHORITY_UNRESOLVED_NON_PRICEABLE` as a valid non-blocking registry
state).

`tests/test_prompt16_authority_disposition.py` was rewritten (not deleted) to
test the corrected policy: `AUTHORITY_UNRESOLVED_NON_PRICEABLE` structurally
absent from `BLOCKING_STATES`; the substantive-classifier tests (hollow object,
anchor-less authority, secondary-source authority all still fail to verify)
carried forward unchanged; the direct-`price_segment`-bypass and ranking-safety
tests re-scoped to the genuinely-blocked six; the 23 internally-recovered
programs individually asserted `AUTHORITY_VERIFIED_PRICEABLE` and
`PROVENANCE_RECOVERED`.
