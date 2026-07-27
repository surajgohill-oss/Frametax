# CineGlobe DISCOVERY Provenance Ledger

Generated 2026-07-26 by `backend/scripts/audit_discovery_provenance.py` (`discovery-provenance-audit-v1`). Read-only audit — zero web calls, zero new statutory facts, zero calculation/optimizer/rate-rule changes. Every classification below is grounded in a field already present on the catalog record itself (program_type, base_rate, min_spend_usd, notes, source_url/source_title) or a direct cross-check against `canonical_executable_jurisdictions()` / `get_rate_rules()`.

## Executive summary

- **Final DISCOVERY count (deduplicated):** 116
- **Raw catalog entries inspected:** 303 (across 15 source modules)
- **Entries already covered by an executable jurisdiction:** 187 (secondary/regional catalog entries for a country whose primary program is already wired — not part of the DISCOVERY population this ledger accounts for)
- **Malformed join-key entries (blank jurisdiction_code/program_name):** 0
- **Intra-DISCOVERY duplicate keys:** 0

**Count by classification:**

| Status | Count |
|---|---|
| MALFORMED_OR_DUPLICATE (Malformed or duplicate) | 4 |
| TREATY_OR_STRUCTURAL_REFERENCE (Treaty or structural reference) | 5 |
| DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic) | 94 |
| UNVERIFIED_POLICY_LEAD (Unverified policy lead) | 13 |
| INACTIVE_EXPIRED_OR_HISTORICAL (Inactive, expired, or historical) | 0 |
| REFERENCE_CATALOG_PLACEHOLDER (Reference catalog placeholder) | 0 |
| UNRESOLVED_ORIGIN (Unresolved origin) | 0 |
| **Total** | **116** |

- **Count requiring future primary-source research:** 13 (UNVERIFIED_POLICY_LEAD)
- **Count structurally non-executable:** 99 (DISCRETIONARY_NONDETERMINISTIC + TREATY_OR_STRUCTURAL_REFERENCE — cannot become a deterministic rate rule regardless of research effort, by the nature of the mechanism)
- **Count historical/inactive:** 0
- **Count malformed/duplicate:** 4
- **Count unresolved:** 0

## Explanation of DISCOVERY

> DISCOVERY is a reference and research classification, not an assertion that an executable incentive pathway is partially implemented. A DISCOVERY record means the catalog is aware a program exists (jurisdiction, program name, and usually a source) but no statutory `RateRule` has been sourced and verified for it. This ledger resolves *why* — for every single record — rather than leaving the reason implicit.

## Freeze implications

- **Do not block backend freeze:** DISCRETIONARY_NONDETERMINISTIC, TREATY_OR_STRUCTURAL_REFERENCE, MALFORMED_OR_DUPLICATE, INACTIVE_EXPIRED_OR_HISTORICAL. None of these represent an incomplete implementation — they represent mechanisms the optimizer's deterministic rate-rule model was never meant to price, or catalog hygiene issues with no bearing on served output.
- **Remain valid future data-acquisition work:** UNVERIFIED_POLICY_LEAD (13 records) — genuine candidates for a future primary-source research pass, the same process used for the 110 already-executable jurisdictions.
- **Should never be promoted into deterministic incentive calculations:** DISCRETIONARY_NONDETERMINISTIC and TREATY_OR_STRUCTURAL_REFERENCE records. Awards from selective grants/funds and treaty/structural mechanisms are not a production-claimable statutory rate; forcing one into a RateRule would fabricate a certainty that does not exist.
- **Require cleanup rather than research:** MALFORMED_OR_DUPLICATE (4 records) — the bare-`AE` Dubai/Abu Dhabi duplicates and the `US` multi-state aggregate placeholder should be removed or merged at the next catalog touch; the `Emirates Airline` entry should be removed as a non-jurisdiction record. No runtime behavior depends on any of the four.

## Full record inventory

One row per deduplicated DISCOVERY record. `Det. rate` / `Min spend` / `Source` columns are yes/no presence flags on the record's own fields; `Qual. spend` is always "no" because no `SpendRule` exists for any DISCOVERY-tier program (SpendRule is keyed by program_slug, which is `None` for every raw catalog entry — see totals above).

| ID | Jurisdiction | Program | Source module | Status | Det. rate | Min spend | Qual. spend | Source | Disposition | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| DISC-001-US | US | State Film Tax Credits (Multi-State) | `app/data/global_inventory.py (seed)` | MALFORMED_OR_DUPLICATE | no | no | no | yes | remove or merge as malformed/duplicate | HIGH |
| DISC-002-GB-SCT | GB-SCT | Screen Scotland Production Growth Fund | `app/data/global_inventory_extended.py` | UNVERIFIED_POLICY_LEAD | yes | no | no | yes | retain as future research lead | MEDIUM |
| DISC-003-GB-WLS | GB-WLS | Wales Screen Production Fund (Ffilm Cymru Wales) | `app/data/global_inventory_extended.py` | UNVERIFIED_POLICY_LEAD | yes | no | no | yes | retain as future research lead | MEDIUM |
| DISC-004-AU-VIC | AU-VIC | VicScreen Production Investment | `app/data/global_inventory_extended.py` | UNVERIFIED_POLICY_LEAD | yes | no | no | yes | retain as future research lead | MEDIUM |
| DISC-005-UY | UY | Uruguay XXI Film Incentive | `app/data/global_inventory_extended.py` | UNVERIFIED_POLICY_LEAD | no | no | no | yes | retain as future research lead | MEDIUM |
| DISC-006-AR | AR | INCAA — Argentine Film Institute Incentives | `app/data/global_inventory_extended.py` | UNVERIFIED_POLICY_LEAD | no | no | no | yes | retain as future research lead | MEDIUM |
| DISC-007-BR | BR | ANCINE — Brazilian Film Commission Tax Incentives | `app/data/global_inventory_extended.py` | UNVERIFIED_POLICY_LEAD | no | no | no | yes | retain as future research lead | MEDIUM |
| DISC-008-AE | AE | Dubai Film Commission — Dubai Production Incentive (DPIP) | `app/data/global_inventory_extended.py` | MALFORMED_OR_DUPLICATE | yes | no | no | yes | remove or merge as malformed/duplicate | HIGH |
| DISC-009-TR | TR | Turkey Cinema General Directorate Film Production Support | `app/data/global_inventory_wave2.py` | UNVERIFIED_POLICY_LEAD | no | no | no | yes | retain as future research lead | MEDIUM |
| DISC-010-IN | IN | India National Film Development Corporation (NFDC) and State Incentives | `app/data/global_inventory_wave2.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-011-LK | LK | Sri Lanka Film Commission Production Incentive | `app/data/global_inventory_wave2.py` | UNVERIFIED_POLICY_LEAD | no | no | no | yes | retain as future research lead | MEDIUM |
| DISC-012-JM | JM | Jamaica Entertainment Industry Incentive Programme | `app/data/global_inventory_wave2.py` | UNVERIFIED_POLICY_LEAD | yes | no | no | yes | retain as future research lead | MEDIUM |
| DISC-013-TN | TN | Tunisia National Centre for Cinema and Image (CNCI) Cash Rebate | `app/data/global_inventory_wave2.py` | UNVERIFIED_POLICY_LEAD | yes | no | no | yes | retain as future research lead | MEDIUM |
| DISC-014-KE | KE | Kenya Film Commission (KFC) Production Incentive | `app/data/global_inventory_wave2.py` | UNVERIFIED_POLICY_LEAD | no | no | no | yes | retain as future research lead | MEDIUM |
| DISC-015-NG | NG | National Film and Video Censors Board / Creative Economy Incentive | `app/data/global_inventory_wave2.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-016-EU | EU | Eurimages — Council of Europe Co-production Fund | `app/data/global_inventory_grants.py` | TREATY_OR_STRUCTURAL_REFERENCE | no | no | no | yes | retain as treaty/structural reference | HIGH |
| DISC-017-EU | EU | Creative Europe MEDIA Programme | `app/data/global_inventory_grants.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-018-NORDIC | NORDIC | Nordisk Film & TV Fond | `app/data/global_inventory_grants.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-019-US | US | Sundance Institute — Documentary Fund | `app/data/global_inventory_grants.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-020-BS | BS | Bahamas Film Commission Production Support | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-021-BB | BB | Barbados Film and Entertainment Production Incentives | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-022-PE | PE | Peru DAFO Film Production Support | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-023-EC | EC | Ecuador Film Commission Production Facilitation | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-024-RW | RW | Rwanda Development Board Film Production Support | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-025-TZ | TZ | Tanzania Film Board Production Facilitation | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-026-SN | SN | Senegal Bureau d'Accueil des Tournages Film Support | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-027-KW | KW | Kuwait Film Committee Production Support | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-028-BH | BH | Bahrain Film Commission Production Support | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-029-AM | AM | National Cinema Centre of Armenia Production Support | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-030-VN | VN | Vietnam Cinema Department Production Facilitation | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-031-ID | ID | Indonesian Film Commission Production Facilitation | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-032-KH | KH | Cambodia Ministry of Culture Film Production Facilitation | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-033-HK | HK | Create Hong Kong (CreateHK) Production Support | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-034-BA | BA | Film Centre Bosnia and Herzegovina Production Support | `app/data/global_inventory_wave3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | HIGH |
| DISC-035-IBERO | IBERO | IBERMEDIA Programme for Ibero-American Co-productions | `app/data/global_inventory_grants2.py` | TREATY_OR_STRUCTURAL_REFERENCE | no | no | no | yes | retain as treaty/structural reference | HIGH |
| DISC-036-DE-BY | DE-BY | FilmFernsehFonds Bayern (FFF Bayern) | `app/data/global_inventory_grants2.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-037-DE-NW | DE-NW | Film und Medienstiftung NRW | `app/data/global_inventory_grants2.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-038-HK | HK | Hong Kong Film Development Fund (FDF) | `app/data/global_inventory_grants2.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-039-IN | IN | NFDC International Co-production Development Fund | `app/data/global_inventory_grants2.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-040-SE-VG | SE-VG | Film i Väst — Regional Co-production Fund | `app/data/global_inventory_grants2.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-041-ACP | ACP | ACP Films — EU-ACP Cultural Film Co-production Fund | `app/data/global_inventory_grants2.py` | TREATY_OR_STRUCTURAL_REFERENCE | no | no | no | yes | retain as treaty/structural reference | HIGH |
| DISC-042-US | US | ITVS International Documentary Fund | `app/data/global_inventory_grants2.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-043-AZ | AZ | Azerbaijan Film Fund Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-044-OM | OM | Oman Film Commission Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-045-LB | LB | Centre du Cinéma Libanais (CCL) Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-046-VE | VE | CNAC Venezuela Film Production Fund | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-047-GY | GY | Guyana Tourism Authority Film Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-048-GT | GT | Guatemala Film Commission (INGUAT) Production Facilitation | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-049-NA | NA | Namibia Film Commission Production Incentive | `app/data/global_inventory_wave4.py` | UNVERIFIED_POLICY_LEAD | no | no | no | yes | retain as future research lead | MEDIUM |
| DISC-050-BW | BW | Botswana Film Commission Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-051-ET | ET | Ethiopian Film Commission Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-052-CI | CI | Centre National de Cinéma de Côte d'Ivoire (CNCI) Film Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-053-CM | CM | Cameroon Centre National de la Cinématographie (CNC-Cameroon) | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-054-AO | AO | Angola Instituto do Cinema e Audiovisual (ICA) Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-055-UG | UG | Uganda Film Commission Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-056-MZ | MZ | Mozambique Instituto do Cinema Film Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-057-ZM | ZM | Zambia Film Commission Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-058-ZW | ZW | Zimbabwe Film and Broadcasting Authority Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-059-CN | CN | China Film Administration Domestic Co-production Support | `app/data/global_inventory_wave4.py` | TREATY_OR_STRUCTURAL_REFERENCE | no | no | no | yes | retain as treaty/structural reference | HIGH |
| DISC-060-MO | MO | Macau Cultural Industries Fund Film Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-061-BD | BD | Bangladesh Film Development Corporation (BFDC) Production Support | `app/data/global_inventory_wave4.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-062-RU | RU | Russian Cinema Fund (Fond Kino) Production Support | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-063-BY | BY | Belarusfilm National Film Studio Production Support | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-064-MD | MD | National Centre for Cinematography Moldova (NCFM) | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-065-CU | CU | ICAIC Cuba Film Production Support | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-066-IR | IR | Farabi Cinema Foundation Film Production Support | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-067-DZ | DZ | Centre Algérien pour le Développement du Cinéma (CADC) Film Support | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-068-GA | GA | Gabon Ministry of Culture Film Commission Support | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-069-SC | SC | Seychelles Tourism Board Film Production Support | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-070-MV | MV | Maldives Marketing and PR Corporation (MMPRC) Film Facilitation | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-071-BT | BT | Bhutan Film Commission / Tourism Council Production Facilitation | `app/data/global_inventory_wave5.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-072-GB-NIR | GB-NIR | Northern Ireland Screen — Production Fund | `app/data/global_inventory_regional.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-073-DE-MDM | DE-MDM | Mitteldeutsche Medienförderung (MDM) — Film Production Fund | `app/data/global_inventory_regional.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-074-IT-APU | IT-APU | Apulia Film Commission — Film Fund | `app/data/global_inventory_regional.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-075-IT-PIE | IT-PIE | Film Commission Torino Piemonte — Production Support | `app/data/global_inventory_regional.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-076-ES-EUS | ES-EUS | Basque Audiovisual — Eusko Jaurlaritza Film Production Support | `app/data/global_inventory_regional.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-077-AU-WA | AU-WA | Screenwest WA — Production Attraction Strategy (PAS) | `app/data/global_inventory_wave6.py` | UNVERIFIED_POLICY_LEAD | yes | yes | no | yes | retain as future research lead | MEDIUM |
| DISC-078-DE-BB | DE-BB | Medienboard Berlin-Brandenburg (MBB) — Film Production Fund | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-079-DE-HH | DE-HH | Film- und Medienstiftung Hamburg Schleswig-Holstein | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-080-DE-BW | DE-BW | MFG Medien- und Filmgesellschaft Baden-Württemberg | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-081-IT-LAZ | IT-LAZ | Lazio Cinema International — Film Fund | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-082-IT-SIC | IT-SIC | Sicilia Film Commission — Film Fund | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-083-IT-CAM | IT-CAM | Film Commission Campania — Production Fund | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-084-IT-TOS | IT-TOS | Film Commission Toscana — Production Support | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-085-ES-CAT | ES-CAT | ICEC — Institut Català de les Empreses Culturals Film Support | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-086-ES-AND | ES-AND | Andalucia Film Commission — Audiovisual Production Incentive | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-087-ES-GAL | ES-GAL | Agadic — Axencia Galega das Industrias Culturais Film Production Fund | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-088-ES-VAL | ES-VAL | Institut Valencià de Cultura (IVC) — Audiovisual Production Fund | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-089-AE | AE | Abu Dhabi Film Commission (ADFC) — Production Rebate | `app/data/global_inventory_wave6.py` | MALFORMED_OR_DUPLICATE | yes | no | no | yes | remove or merge as malformed/duplicate | HIGH |
| DISC-090-GB-YRK | GB-YRK | Screen Yorkshire — Yorkshire Content Fund | `app/data/global_inventory_wave6.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-091-EU | EU | Torino Film Lab — International Development and Production Grants | `app/data/global_inventory_grants3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-092-US | US | Tribeca Film Institute — Documentary and Narrative Development Grants | `app/data/global_inventory_grants3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-093-BF | BF | FESPACO — Festival Pan-Africain du Cinéma et de la Télévision de Ouagadougou | `app/data/global_inventory_grants3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-094-AR | AR | INCAA — Foprocine Development and Production Grants | `app/data/global_inventory_grants3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-095-BR | BR | ANCINE — FSA (Fundo Setorial do Audiovisual) Development Fund | `app/data/global_inventory_grants3.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-096-FR-IDF | FR-IDF | Île-de-France Cinema Regional Aid | `app/data/global_inventory_phase_c.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-097-FR-NAQ | FR-NAQ | Nouvelle-Aquitaine Regional Cinema Aid | `app/data/global_inventory_phase_c.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-098-FR-ARA | FR-ARA | Auvergne-Rhône-Alpes Cinema Regional Aid | `app/data/global_inventory_phase_c.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-099-FR-OCC | FR-OCC | Occitanie Cinema Regional Aid | `app/data/global_inventory_phase_c.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-100-BE-WAL | BE-WAL | Wallimage Co-production Fund | `app/data/global_inventory_phase_c.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-101-BE-VLG | BE-VLG | VAF Flanders Audiovisual Fund | `app/data/global_inventory_phase_c.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-102-BE-BRU | BE-BRU | Screen.Brussels Production Support | `app/data/global_inventory_phase_c.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-103-DE-NI | DE-NI | nordmedia Film und Mediengesellschaft | `app/data/global_inventory_phase_c.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-104-EU | EU | EU AVMS Directive — Local Content Investment Obligations (Streamers) | `app/data/global_inventory_special_categories.py` | TREATY_OR_STRUCTURAL_REFERENCE | no | no | no | yes | retain as treaty/structural reference | HIGH |
| DISC-105-AE | AE | Emirates Airline — Film Production Partnerships and In-Kind Support | `app/data/global_inventory_special_categories.py` | MALFORMED_OR_DUPLICATE | no | no | no | yes | remove or merge as malformed/duplicate | HIGH |
| DISC-106-SA-KSA | SA-KSA | Saudi Film Commission — Production Grants and Selective Support | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-107-TR | TR | Ministry of Culture and Tourism (KÜLTÜR) — Film Production Grants | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-108-SE-SK | SE-SK | Film i Skåne — Regional Co-production Fund (Scania) | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-109-SE-AB | SE-AB | Filmregion Stockholm-Mälardalen — Regional Co-production Fund | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-110-NO-ROG | NO-ROG | Vestnorsk Filmsenter — Western Norway Regional Film Centre | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-111-NO-TRO | NO-TRO | Nord Norsk Filmsenter — Northern Norway Regional Film Centre | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-112-DK-CPH | DK-CPH | Copenhagen Film Fund — Regional Co-production Support | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-113-AU-TAS | AU-TAS | Screen Tasmania — Production Support | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-114-AU-NT | AU-NT | Territory Screen — Northern Territory Production Support | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-115-GB-LON | GB-LON | Film London — Production Finance Market and Support | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |
| DISC-116-CA-PE | CA-PE | Film PEI — Prince Edward Island Production Support | `app/data/global_inventory_special_categories.py` | DISCRETIONARY_NONDETERMINISTIC | no | no | no | yes | retain as catalog reference | MEDIUM |

## Reason-not-executable detail (per record)

Full-text reason and future action for every record, since the table above cannot fit them legibly.

### DISC-001-US — US: State Film Tax Credits (Multi-State)

- **Status:** MALFORMED_OR_DUPLICATE (Malformed or duplicate)
- **Origin:** Catalog entry from global_inventory.py (seed) (program_type=tax_credit, confidence_tier=PARSED).
- **Reason not executable:** Aggregate placeholder record: no jurisdiction-specific rate, no min_spend, no source_url — source_title is the generic 'Various state film office program summaries'. Not a legitimate standalone program; the real US state programs (Georgia, New York, New Mexico, Louisiana, Mississippi, California, Oregon) are each already catalogued and, where sourced, executable in their own right.
- **Recommended disposition:** remove or merge as malformed/duplicate
- **Future action:** None — not a legitimate standalone program; recommend removal/merge at next catalog cleanup.
- **Confidence:** HIGH

### DISC-002-GB-SCT — GB-SCT: Screen Scotland Production Growth Fund

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_extended.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-003-GB-WLS — GB-WLS: Wales Screen Production Fund (Ffilm Cymru Wales)

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_extended.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-004-AU-VIC — AU-VIC: VicScreen Production Investment

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_extended.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-005-UY — UY: Uruguay XXI Film Incentive

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_extended.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-006-AR — AR: INCAA — Argentine Film Institute Incentives

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_extended.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-007-BR — BR: ANCINE — Brazilian Film Commission Tax Incentives

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_extended.py (program_type=tax_credit, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='tax_credit' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-008-AE — AE: Dubai Film Commission — Dubai Production Incentive (DPIP)

- **Status:** MALFORMED_OR_DUPLICATE (Malformed or duplicate)
- **Origin:** Catalog entry from global_inventory_extended.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** Duplicate of the ALREADY-EXECUTABLE program at jurisdiction_code AE-DXB (ae_dxb_dpip), filed under the legacy/inconsistent bare 'AE' key. Confirmed via get_rate_rules('ae_dxb_dpip'): the executable, verified rate is 40% — this catalog record's 30% is a stale, superseded figure from before AE-DXB was properly keyed and verified. Not a new opportunity.
- **Recommended disposition:** remove or merge as malformed/duplicate
- **Future action:** None — not a legitimate standalone program; recommend removal/merge at next catalog cleanup.
- **Confidence:** HIGH

### DISC-009-TR — TR: Turkey Cinema General Directorate Film Production Support

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_wave2.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-010-IN — IN: India National Film Development Corporation (NFDC) and State Incentives

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave2.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-011-LK — LK: Sri Lanka Film Commission Production Incentive

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_wave2.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-012-JM — JM: Jamaica Entertainment Industry Incentive Programme

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_wave2.py (program_type=tax_credit, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='tax_credit' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-013-TN — TN: Tunisia National Centre for Cinema and Image (CNCI) Cash Rebate

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_wave2.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-014-KE — KE: Kenya Film Commission (KFC) Production Incentive

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_wave2.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-015-NG — NG: National Film and Video Censors Board / Creative Economy Incentive

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave2.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-016-EU — EU: Eurimages — Council of Europe Co-production Fund

- **Status:** TREATY_OR_STRUCTURAL_REFERENCE (Treaty or structural reference)
- **Origin:** Catalog entry from global_inventory_grants.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** Eurimages is the Council of Europe's own intergovernmental co-production support fund, established by and operating under the Council of Europe's co-production convention — a treaty-level instrument, not a unilateral jurisdiction rate rebate a production can claim outright.
- **Recommended disposition:** retain as treaty/structural reference
- **Future action:** None — represents a treaty/structural mechanism, not a unilaterally priceable rate.
- **Confidence:** HIGH

### DISC-017-EU — EU: Creative Europe MEDIA Programme

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** A regional/selective co-production financing fund — discretionary award, not a deterministic statutory rate.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-018-NORDIC — NORDIC: Nordisk Film & TV Fond

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** A regional/selective co-production financing fund — discretionary award, not a deterministic statutory rate.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-019-US — US: Sundance Institute — Documentary Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants.py (program_type=development_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='development_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-020-BS — BS: Bahamas Film Commission Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-021-BB — BB: Barbados Film and Entertainment Production Incentives

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-022-PE — PE: Peru DAFO Film Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-023-EC — EC: Ecuador Film Commission Production Facilitation

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-024-RW — RW: Rwanda Development Board Film Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-025-TZ — TZ: Tanzania Film Board Production Facilitation

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-026-SN — SN: Senegal Bureau d'Accueil des Tournages Film Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-027-KW — KW: Kuwait Film Committee Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-028-BH — BH: Bahrain Film Commission Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-029-AM — AM: National Cinema Centre of Armenia Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-030-VN — VN: Vietnam Cinema Department Production Facilitation

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-031-ID — ID: Indonesian Film Commission Production Facilitation

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-032-KH — KH: Cambodia Ministry of Culture Film Production Facilitation

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-033-HK — HK: Create Hong Kong (CreateHK) Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-034-BA — BA: Film Centre Bosnia and Herzegovina Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave3.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** HIGH

### DISC-035-IBERO — IBERO: IBERMEDIA Programme for Ibero-American Co-productions

- **Status:** TREATY_OR_STRUCTURAL_REFERENCE (Treaty or structural reference)
- **Origin:** Catalog entry from global_inventory_grants2.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** IBERMEDIA is an intergovernmental co-production support programme established by agreement among Ibero-American states — a treaty-level co-production pathway, not a single jurisdiction's deterministic rebate.
- **Recommended disposition:** retain as treaty/structural reference
- **Future action:** None — represents a treaty/structural mechanism, not a unilaterally priceable rate.
- **Confidence:** HIGH

### DISC-036-DE-BY — DE-BY: FilmFernsehFonds Bayern (FFF Bayern)

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants2.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-037-DE-NW — DE-NW: Film und Medienstiftung NRW

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants2.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-038-HK — HK: Hong Kong Film Development Fund (FDF)

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants2.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-039-IN — IN: NFDC International Co-production Development Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants2.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** A regional/selective co-production financing fund — discretionary award, not a deterministic statutory rate.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-040-SE-VG — SE-VG: Film i Väst — Regional Co-production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants2.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** A regional/selective co-production financing fund — discretionary award, not a deterministic statutory rate.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-041-ACP — ACP: ACP Films — EU-ACP Cultural Film Co-production Fund

- **Status:** TREATY_OR_STRUCTURAL_REFERENCE (Treaty or structural reference)
- **Origin:** Catalog entry from global_inventory_grants2.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** Operates under the EU-ACP (Cotonou Agreement) cultural-cooperation framework — a treaty/framework-based co-production mechanism, not a jurisdiction rate rule.
- **Recommended disposition:** retain as treaty/structural reference
- **Future action:** None — represents a treaty/structural mechanism, not a unilaterally priceable rate.
- **Confidence:** HIGH

### DISC-042-US — US: ITVS International Documentary Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants2.py (program_type=development_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='development_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-043-AZ — AZ: Azerbaijan Film Fund Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-044-OM — OM: Oman Film Commission Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-045-LB — LB: Centre du Cinéma Libanais (CCL) Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-046-VE — VE: CNAC Venezuela Film Production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-047-GY — GY: Guyana Tourism Authority Film Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-048-GT — GT: Guatemala Film Commission (INGUAT) Production Facilitation

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-049-NA — NA: Namibia Film Commission Production Incentive

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-050-BW — BW: Botswana Film Commission Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-051-ET — ET: Ethiopian Film Commission Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-052-CI — CI: Centre National de Cinéma de Côte d'Ivoire (CNCI) Film Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-053-CM — CM: Cameroon Centre National de la Cinématographie (CNC-Cameroon)

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-054-AO — AO: Angola Instituto do Cinema e Audiovisual (ICA) Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-055-UG — UG: Uganda Film Commission Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-056-MZ — MZ: Mozambique Instituto do Cinema Film Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-057-ZM — ZM: Zambia Film Commission Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-058-ZW — ZW: Zimbabwe Film and Broadcasting Authority Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-059-CN — CN: China Film Administration Domestic Co-production Support

- **Status:** TREATY_OR_STRUCTURAL_REFERENCE (Treaty or structural reference)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes describe this as conferring official co-production status and Chinese domestic-market access — a structural/co-production-pathway mechanism, not a cash rebate or tax credit with a claimable rate.
- **Recommended disposition:** retain as treaty/structural reference
- **Future action:** None — represents a treaty/structural mechanism, not a unilaterally priceable rate.
- **Confidence:** HIGH

### DISC-060-MO — MO: Macau Cultural Industries Fund Film Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-061-BD — BD: Bangladesh Film Development Corporation (BFDC) Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave4.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-062-RU — RU: Russian Cinema Fund (Fond Kino) Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-063-BY — BY: Belarusfilm National Film Studio Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** In-kind state studio infrastructure (facilities, equipment, crew) — no cash rebate/rate exists, consistent with the production_support default. Distinctly flagged from other facilitation-only records because the entry's OWN notes state: 'international sanctions since 2020 and 2022 significantly limit Western co-operation with Belarusian entities. Verify compliance implications before any engagement.' This is a real, internally-documented geopolitical-risk caveat, not merely an unresearched rate.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-064-MD — MD: National Centre for Cinematography Moldova (NCFM)

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-065-CU — CU: ICAIC Cuba Film Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-066-IR — IR: Farabi Cinema Foundation Film Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-067-DZ — DZ: Centre Algérien pour le Développement du Cinéma (CADC) Film Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-068-GA — GA: Gabon Ministry of Culture Film Commission Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-069-SC — SC: Seychelles Tourism Board Film Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-070-MV — MV: Maldives Marketing and PR Corporation (MMPRC) Film Facilitation

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-071-BT — BT: Bhutan Film Commission / Tourism Council Production Facilitation

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave5.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** The record's own notes state no confirmed formal cash rebate/rate exists — this is location/permit/logistics facilitation, not a monetary incentive, so it cannot be deterministically priced from published rules.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-072-GB-NIR — GB-NIR: Northern Ireland Screen — Production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_regional.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-073-DE-MDM — DE-MDM: Mitteldeutsche Medienförderung (MDM) — Film Production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_regional.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-074-IT-APU — IT-APU: Apulia Film Commission — Film Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_regional.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-075-IT-PIE — IT-PIE: Film Commission Torino Piemonte — Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_regional.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-076-ES-EUS — ES-EUS: Basque Audiovisual — Eusko Jaurlaritza Film Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_regional.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-077-AU-WA — AU-WA: Screenwest WA — Production Attraction Strategy (PAS)

- **Status:** UNVERIFIED_POLICY_LEAD (Unverified policy lead)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='cash_rebate' names a real monetary incentive mechanism, but no statutory RateRule is wired for this jurisdiction — rate/threshold/eligibility facts are not yet confirmed from a primary source.
- **Recommended disposition:** retain as future research lead
- **Future action:** Primary-source research to confirm exact rate/threshold/eligibility, then wire a RateRule.
- **Confidence:** MEDIUM

### DISC-078-DE-BB — DE-BB: Medienboard Berlin-Brandenburg (MBB) — Film Production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-079-DE-HH — DE-HH: Film- und Medienstiftung Hamburg Schleswig-Holstein

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-080-DE-BW — DE-BW: MFG Medien- und Filmgesellschaft Baden-Württemberg

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-081-IT-LAZ — IT-LAZ: Lazio Cinema International — Film Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-082-IT-SIC — IT-SIC: Sicilia Film Commission — Film Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-083-IT-CAM — IT-CAM: Film Commission Campania — Production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-084-IT-TOS — IT-TOS: Film Commission Toscana — Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-085-ES-CAT — ES-CAT: ICEC — Institut Català de les Empreses Culturals Film Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-086-ES-AND — ES-AND: Andalucia Film Commission — Audiovisual Production Incentive

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-087-ES-GAL — ES-GAL: Agadic — Axencia Galega das Industrias Culturais Film Production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-088-ES-VAL — ES-VAL: Institut Valencià de Cultura (IVC) — Audiovisual Production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-089-AE — AE: Abu Dhabi Film Commission (ADFC) — Production Rebate

- **Status:** MALFORMED_OR_DUPLICATE (Malformed or duplicate)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=cash_rebate, confidence_tier=DISCOVERY).
- **Reason not executable:** Duplicate of the ALREADY-EXECUTABLE program at jurisdiction_code AE-AD (ae_ad_film_rebate), filed under the legacy/inconsistent bare 'AE' key. Confirmed via get_rate_rules('ae_ad_film_rebate'): the executable, verified rate band is 35-50% — this catalog record's flat 30% is a stale, superseded figure from before AE-AD was properly keyed and verified. Not a new opportunity.
- **Recommended disposition:** remove or merge as malformed/duplicate
- **Future action:** None — not a legitimate standalone program; recommend removal/merge at next catalog cleanup.
- **Confidence:** HIGH

### DISC-090-GB-YRK — GB-YRK: Screen Yorkshire — Yorkshire Content Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_wave6.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-091-EU — EU: Torino Film Lab — International Development and Production Grants

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants3.py (program_type=development_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='development_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-092-US — US: Tribeca Film Institute — Documentary and Narrative Development Grants

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants3.py (program_type=development_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='development_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-093-BF — BF: FESPACO — Festival Pan-Africain du Cinéma et de la Télévision de Ouagadougou

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants3.py (program_type=development_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='development_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-094-AR — AR: INCAA — Foprocine Development and Production Grants

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants3.py (program_type=development_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='development_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-095-BR — BR: ANCINE — FSA (Fundo Setorial do Audiovisual) Development Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_grants3.py (program_type=development_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='development_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-096-FR-IDF — FR-IDF: Île-de-France Cinema Regional Aid

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_phase_c.py (program_type=regional_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='regional_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-097-FR-NAQ — FR-NAQ: Nouvelle-Aquitaine Regional Cinema Aid

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_phase_c.py (program_type=regional_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='regional_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-098-FR-ARA — FR-ARA: Auvergne-Rhône-Alpes Cinema Regional Aid

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_phase_c.py (program_type=regional_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='regional_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-099-FR-OCC — FR-OCC: Occitanie Cinema Regional Aid

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_phase_c.py (program_type=regional_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='regional_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-100-BE-WAL — BE-WAL: Wallimage Co-production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_phase_c.py (program_type=regional_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='regional_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-101-BE-VLG — BE-VLG: VAF Flanders Audiovisual Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_phase_c.py (program_type=regional_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='regional_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-102-BE-BRU — BE-BRU: Screen.Brussels Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_phase_c.py (program_type=regional_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='regional_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-103-DE-NI — DE-NI: nordmedia Film und Mediengesellschaft

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_phase_c.py (program_type=regional_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='regional_fund' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-104-EU — EU: EU AVMS Directive — Local Content Investment Obligations (Streamers)

- **Status:** TREATY_OR_STRUCTURAL_REFERENCE (Treaty or structural reference)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** A regulatory content-investment quota imposed on streaming platforms operating in the EU — a structural/regulatory reference a production does not itself claim as an incentive; fundamentally different in kind from every rate-rebate record in this catalog.
- **Recommended disposition:** retain as treaty/structural reference
- **Future action:** None — represents a treaty/structural mechanism, not a unilaterally priceable rate.
- **Confidence:** HIGH

### DISC-105-AE — AE: Emirates Airline — Film Production Partnerships and In-Kind Support

- **Status:** MALFORMED_OR_DUPLICATE (Malformed or duplicate)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=production_support, confidence_tier=DISCOVERY).
- **Reason not executable:** Not a jurisdiction-government incentive program at all — this is a corporate/airline commercial and in-kind partnership (reduced airfare, cargo handling, logistics), structurally different from every other record in this catalog. Should not be counted as an unpromoted jurisdiction incentive lead.
- **Recommended disposition:** remove or merge as malformed/duplicate
- **Future action:** None — not a legitimate standalone program; recommend removal/merge at next catalog cleanup.
- **Confidence:** HIGH

### DISC-106-SA-KSA — SA-KSA: Saudi Film Commission — Production Grants and Selective Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-107-TR — TR: Ministry of Culture and Tourism (KÜLTÜR) — Film Production Grants

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-108-SE-SK — SE-SK: Film i Skåne — Regional Co-production Fund (Scania)

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** A regional/selective co-production financing fund — discretionary award, not a deterministic statutory rate.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-109-SE-AB — SE-AB: Filmregion Stockholm-Mälardalen — Regional Co-production Fund

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** A regional/selective co-production financing fund — discretionary award, not a deterministic statutory rate.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-110-NO-ROG — NO-ROG: Vestnorsk Filmsenter — Western Norway Regional Film Centre

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-111-NO-TRO — NO-TRO: Nord Norsk Filmsenter — Northern Norway Regional Film Centre

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-112-DK-CPH — DK-CPH: Copenhagen Film Fund — Regional Co-production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** A regional/selective co-production financing fund — discretionary award, not a deterministic statutory rate.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-113-AU-TAS — AU-TAS: Screen Tasmania — Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-114-AU-NT — AU-NT: Territory Screen — Northern Territory Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-115-GB-LON — GB-LON: Film London — Production Finance Market and Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=co_production_fund, confidence_tier=DISCOVERY).
- **Reason not executable:** A regional/selective co-production financing fund — discretionary award, not a deterministic statutory rate.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM

### DISC-116-CA-PE — CA-PE: Film PEI — Prince Edward Island Production Support

- **Status:** DISCRETIONARY_NONDETERMINISTIC (Discretionary / non-deterministic)
- **Origin:** Catalog entry from global_inventory_special_categories.py (program_type=direct_grant, confidence_tier=DISCOVERY).
- **Reason not executable:** program_type='direct_grant' is a selective, application-based public fund by design — awards are discretionary/competitive, not a deterministic statutory rate a production can calculate in advance.
- **Recommended disposition:** retain as catalog reference
- **Future action:** None — structurally non-deterministic; no future rate-rule research applies.
- **Confidence:** MEDIUM
