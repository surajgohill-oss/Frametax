# AG 32 PROGRAM PRIMARY SOURCE RESEARCH (V2)

## Methodology
The strict anti-fabrication rules prohibited the use of generic templates, inherited database structures, and assumed administrative characteristics. Automated retrieval was attempted for the 32 programs using `cURL`. 16 sources successfully loaded, and their properties were extracted. The remaining 16 resulted in timeouts or 403 blocks and were explicitly marked `PRIMARY_SOURCE_UNRESOLVED`. No prohibited placeholders were used.

## Source Counts
- Primary Sources Targeted: 32
- Primary Sources Opened successfully: 16

## Completed vs Unresolved
- Completed Programs (PRIMARY_SOURCE_RESOLVED): 16
- Unresolved Programs (PRIMARY_SOURCE_UNRESOLVED): 16

## Handoff
16 programs were successfully verified against their primary legislative or film commission portals. 16 were left unresolved in `AG_32_UNRESOLVED_EVIDENCE.csv`. The `PRIMARY_RESEARCH_INCOMPLETE` signal is intentionally returned to mandate manual review of the blocked sources.
