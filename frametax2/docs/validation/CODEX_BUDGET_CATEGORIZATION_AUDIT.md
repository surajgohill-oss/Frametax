# Budget categorization and embedded-incentive audit

Status: IMPLEMENTED IN BRANCH; real-project ingestion refresh and served verification pending. Calculation acceptance remains open.

Scope: LU, FVD, BH, LLS; Movie Magic first, CSV/XLSX parity. Prior total reconciliation is preserved. No jurisdiction expansion or UI redesign.

## Source preservation

Original PDFs were reparsed read-only through the canonical parser/classifier. Account counts remain 44/34/34/46 (158). Declared gross budgets remain $4,364,393 / $4,517,687 / $2,482,023 / $11,983,654. LU retains its authored $2 leaf-total difference. Incentive estimates remain separate: LU +$1,275,411; FVD -$518,804; LLS -$1,503,074. BH has no source incentive line in this export.

`FOUR_ANCHOR_SOURCE_DETAIL_EVIDENCE.json` retains source paths/hashes, every account, classification, and captured authored subaccounts. LLS has 40 exactly conserving detail groups. Other exports have zero exactly conserving groups under this parser: no detail allocation is invented.

CSV/XLSX previously counted incentive/net rows as spending; CSV also lost leading minus signs. Shared separation now preserves incentive estimates outside gross cost and removes net totals from spend. Credit financing/application/audit fees remain costs. Generic text exports retain incentive estimates. Net totals are excluded, not newly persisted as reconciliation metadata.

## Categorization boundary

The current canonical classifier correctly maps LU publicity $24,348 to general administration; persisted LU still maps it to crew labour. Fifteen other LU categories also differ from today's classifier, including production staff, wardrobe, electrical, camera and locations. Their curated category provenance must be recovered before a blanket refresh can replace them. This is not a corrected live-project claim. FVD/BH/LLS stored categories matched the current classifier in the read-only comparison.

## Source-detail treatment

Authored Movie Magic detail totals are metadata on the parent cost, never additional costs. Storage, canonical input assembly, allocation, pricing, served budget drill-down and calculation fingerprints preserve them. California splits a mixed account only when unique finite nonnegative child totals conserve its parent exactly; incomplete detail remains conditional. Zero accounts retain identity. ATL fringes require linkage to eligible underlying compensation.

Source-shaped independent LLS writing control: $300,000 writer fee + $12,500 publication fees excluded; $1,350 research + $303 duplication qualify under the retained January 2026 CFC chart. The $151,198 line-producer control retains at most $100,000 as conditional eligible BTL services, with $51,198 excluded. These do not establish the historical application's program or actual territorial eligibility.

## Verification

27 new controls passed across netting/signs, source detail, actual pricing caps, eligible-subset uplifts, 16 qualification-rule mutation checks, isolated persistence and fingerprint changes. Existing targeted parser checks: 55 passed. Allocation/classification checks: 42 passed. Green nodes were not repeated; failed nodes were repaired and rerun individually. Test database only: frametax2_pytest, migration 0081. Persistence used a synthetic temporary table and rolled back. No cold project evaluation, live backend restart, or acceptance database mutation occurred.

The four-anchor issue register owns remaining dispositions. These checks prove bounded implementation behavior, not exact legal QPE or served-project acceptance.

## Recovered category history

The existing `backend/app/data/little_utopia_real_budget.py:LITTLE_UTOPIA_REAL_SPEND_CATEGORY` explains the curated crew/equipment/location classifications that a fresh generic parse can lose. Its comments explicitly leave publicity without an override for legal qualification, so it does not justify the persisted crew classification. This historical map is evidence, not a new production-specific calculator or permission to infer every mixed account's legal QPE. Refresh must preserve reviewed source categories with their provenance and separately correct publicity; a blind delete/reclassify is not accepted.

The canonical material-routing refresh now retains an existing recognized category only when the new parser falls back to miscellaneous on a unique source-identical description/amount/currency row. Explicit fresh classifications win, so publicity is corrected. Changed amounts and ambiguous duplicate identities never borrow a category. Retention is recorded in budget-document notes. Synthetic preservation/correction/change-of-source control passed; no live refresh occurred.
