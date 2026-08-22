# Prompt 16 — Final Authority Disposition + Co-production / Stacking Closeout

Summary only. The per-record detail is the authoritative artifact:
`CLAUDE_PROMPT16_AUTHORITY_DISPOSITION.json`.

## What this phase was

`PROVENANCE_INCOMPLETE_EXISTING_RECORD` — "the rule exists and was researched, but
its retained primary-source metadata is incomplete" — is acceptable during
development and **not** acceptable for a program that still prices in a
production-accepted build. This phase drove every such residual to one of two
terminal dispositions and made the unsafe middle state structurally impossible.

**No external web research was performed.** Every disposition came from
re-reading what this repository already retains.

## Terminal accounting

| | count |
|---|---|
| Registered programs | 123 |
| AUTHORITY_VERIFIED_PRICEABLE | 65 |
| AUTHORITY_UNRESOLVED_NON_PRICEABLE | 58 |
| **Priceable with partial authority** | **0** |
| Disconnected | 0 |

`65 + 58 = 123`. Frozen residual set: `61 = 3 verified + 58 quarantined`.

## The three recoveries

Each was already fully researched and retained — only the *structured* provenance
was missing. None required new research.

- **`mt_mfc_rebate`** — the real Malta Film Commission *Cash Rebate Guidelines*
  (Official Document, Jan 2019, 28pp) had already been retrieved and its true text
  extracted via `pypdf` by a prior session, superseding an earlier hallucinated
  placeholder parse. Cited to section **S.3.2.1**. Provenance attached to all four
  runtime tiers. Malta is a calibration anchor, so this recovery also preserves an
  existing regression control on real authority rather than on grandfathering.
- **`gb_iftc_enhanced_avec`** — primary authority on both limbs: **Finance (No. 2)
  Act 2024 s.14** (statute) for entitlement and **HMRC's own Creative Industries
  Expenditure Credit Manual CREC021110/CREC021120** for mechanics. The ~39.75% net
  figure is recorded as this engine's own net-of-corporation-tax conversion of the
  53% gross rate, not as a figure the source states.
- **`au_sa_pdv_rebate`** — `safilm.com.au` is the South Australian Film
  Corporation's own site, i.e. the administering agency, and is the source of the
  10% PDV figure.

## The 58 quarantines

Each cites only secondary material — production-service sites, aggregators,
law-firm notes, trade press, and in one case a general news portal. `PROJECT_RULES.md`
§4 permits such sources to *locate* an official source but never to justify
deterministic pricing on their own.

**This is not a finding that these programs do not exist or are worthless.** It is
a finding that CineGlobe cannot currently price them defensibly. Fifteen sibling
programs were verified in earlier passes of this same effort precisely because
their retained citations already named the administering body or its own domain.
These 58 do not, and inventing an issuing authority from general knowledge absent
from this repository's audit trail would be fabrication, not verification.

Each remains fully visible as an unresolved knowledge opportunity while
contributing zero incentive, NPC, stacking and ranking value. **Promotion path:**
retain the administering authority's own current source for each
calculation-driving proposition and attach structured provenance to every runtime
tier; the quarantine row then comes out. The classifier verifies substantively, so
a bare `SourceProvenance` object will not promote a program.

## Enforcement

Quarantine is expressed **once**, in the existing canonical owner
(`authority_coverage_registry.py`, new state `AUTHORITY_UNRESOLVED_NON_PRICEABLE`
added to `BLOCKING_STATES`). No parallel registry, engine or code path was created.
That single state is already consulted by all three economic routes:

| Route | Enforcement point |
|---|---|
| Discovery | `production_discovery.py:180` |
| **Direct `price_segment`** (bypasses discovery) | `allocation_pricing.py:297`, checked *before* rate resolution |
| Publication contract | `canonical_publication_contract.py:205` |

Existing adjudications were preserved: the six residuals already carrying a
justified state (`SUPERSEDED`, `NON_GUARANTEED_SELECTIVE`,
`UNPRICEABLE_AUTHORITY_INSUFFICIENT`) keep it — Prompt 16 rows are added with
`setdefault`, never overriding.

## Classifier repair

The prior classifier tested `rule.provenance is not None`. That is exactly the
defect that let partially supported programs read as complete. `_is_substantively_supported`
now requires, per runtime tier: provenance exists, names an `issuing_authority`,
that authority is not a secondary source, **and** carries a `citation_detail`
proposition anchor. Regression tests prove a hollow object, an authority with no
anchor, and a law-firm-named authority all fail to verify.

## Controls — zero economic delta

| Control | Before | After | Change |
|---|---|---|---|
| LU NPC | $3,057,794.90 | $3,057,794.90 | **$0** |
| FVD NPC | $3,072,027.16 | $3,072,027.16 | **$0** |
| LU candidate count | 201 | 201 | **0** |

LU's contingency election remains project data at 100%; no Mauritius hard-code was
introduced. Both projects still return `top_result: None` — unchanged, and correct,
because their own cultural-test applicability is genuinely unresolved.

Candidate count is unchanged because quarantined programs are not *dropped* from
the structure list — they remain visible with `npc`/`incentive` of `None`. This is
the intended shape: the opportunity stays discoverable, the economics do not exist.

## Ranking safety

Verified non-vacuously. Ranked entries and structures carry no `program_slug` of
their own — program identity lives on each structure's **segments**. An earlier
draft of the ranking test read `entry["program_slug"]`, matched nothing and proved
nothing; it now resolves ranked entry → structure → segments and asserts a non-zero
number of segments was inspected, so it cannot silently go vacuous again.
**301 priced segments inspected; 0 quarantined programs carrying incentive.**

## Tests

Full backend suite: **4450 passed, 0 failed, 1 skipped.**

New: `tests/test_prompt16_authority_disposition.py` (12 tests) — the acceptance
invariant, terminal-disposition coverage, registry-wide accounting reconciliation,
substantive-classifier proofs, quarantine enforcement including the direct
`price_segment` bypass route, ranking safety, a verified-but-still-quarantined
consistency guard, and LU/FVD baseline-authority checks.

One pre-existing test was updated rather than weakened:
`test_every_canonical_non_ready_record_is_represented_in_the_registry` asserted
that earlier promotion exemptions were all still needed. Seven of those programs
were promoted under the older "citation claims a direct government fetch" bar and
fail Prompt 16's stricter structured-provenance bar, so they are correctly back in
the registry as quarantines. The test now recognises a Prompt 16 re-quarantine as a
legitimate later, stricter adjudication superseding an earlier looser one — and
still fails if a row returns for any *other* reason.
