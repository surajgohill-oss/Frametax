# Core MFNI Independent Research and AG–Codex Acceptance

**Research date:** 2026-09-06  
**Canonical repository:** `surajgohill-oss/Frametax`  
**Canonical branch:** `claude/audit-frametax-features-NZcX5`  
**AG comparison commit:** `af1a66041ea3778866e065c3adc0e50476ed6a6b`

## Verdict

**Acceptance status: NOT ACCEPTED.** The bounded research execution is complete: the 207-jurisdiction, 621 jurisdiction-category universe has been expanded into 3,312 explicit field records and no unsupported numeric value is approved for automatic economics. Acceptance is withheld because 126 material AG–Codex conflicts and five canonical identity/scope conflicts remain.

**Safe for canonical economic consolidation: NO.** The evidence supports geographic identities and a limited set of statutory/framework rules. It does not support deterministic production labor, construction, security, medical, or safety cost values across the universe. Five canonical identity labels conflict with their coded scopes, and AG's 18 production-agreement rows are not independently reproducible from their citations because the committed CSV provides no source URL or canonical document identifier.

This is a completed fail-closed research result, not permission to synthesize or implement missing values.

## Scope and denominators

| Measure | Count |
|---|---:|
| Jurisdictions | 207 |
| Jurisdiction-category cells | 621 |
| Independent field records | 3,312 |
| Labor fields | 1,449 |
| Construction/material fields | 828 |
| Security/medical/safety fields | 828 |
| Geographic identity fields | 207 |

The 621-cell denominator is exactly 207 jurisdictions × the three Core MFNI economic categories in AG's committed artifact. Geographic identity is separately tested once for every jurisdiction, producing the 3,312-field denominator: `(207 × 7 labor) + (207 × 4 construction) + (207 × 4 safety/security) + (207 × 1 identity)`.

## Independent disposition counts

| Status | Count |
|---|---:|
| `VERIFIED_VALUE` | 200 |
| `VERIFIED_RULE_ONLY` | 378 |
| `VERIFIED_NOT_APPLICABLE` | 2 |
| `INSUFFICIENT_EVIDENCE_FAIL_CLOSED` | 2,727 |
| `IDENTITY_OR_SCOPE_CONFLICT` | 5 |
| `AUTHORITY_BLOCKED` | 0 |
| `OUT_OF_SCOPE` | 0 |
| **Total** | **3,312** |

The 200 verified values are geographic identities, not economic inputs. The 378 verified rules are statutory or framework rules and remain `fail_closed=TRUE`; none is a complete production rate card or measurable automatic cost value.

## Evidence findings

### Labor/workday/overtime

The official ILO working-conditions source is useful for discovery but expressly covers 159 countries, not this 207-identity universe, and it does not establish the current occupation, collective agreement, subnational overlay, or employer-charge value for every field. Codex independently verified limited rule-only floors/frameworks for the United States, United Kingdom, Australia, and EU-member scopes. These establish such matters as federal weekly overtime floors or maximum-hours frameworks; they do not establish a production standard day, applicable guild agreement, fringes, or a priceable crew cost.

AG's 18 `AGREEMENT_DEPENDENT` rows identify plausible agreement names and summaries, but all 18 omit a source URL/canonical document identifier. Each row affects seven labor fields, producing 126 material field conflicts. The canonical resolution is to retrieve the current agreement, verify coverage and effective dates, and map its provisions field by field. Until then, AG's production-specific values must not flow automatically.

### Construction/materials

AG's blanket insufficient-evidence result is justified for automatic production economics. The World Bank ICP is authoritative, but its 2021 construction survey concerns national annual-average inputs for typical residential, non-residential and civil works. It is neither a current film-set construction quote nor a production labor rate, and it does not resolve subnational variation. All 828 construction fields therefore fail closed.

### Security/medical/safety

AG's blanket insufficient-evidence result is justified for measurable production costs, but incomplete as a description of law. Codex independently found official rule-only occupational-safety/first-aid frameworks in US, UK, Australian and EU-member scopes. Those rules can establish a duty or assessment requirement, but not a universal staffing quantity or price. Of 828 fields, 130 are rule-only and 698 fail closed; all cost inputs remain blocked.

### Identity and scope

All 13 AG blockers were independently addressed. Nine have terminal research dispositions: seven are accepted as coded physical scopes, `SA-KSA` is a duplicate sovereign alias, and `DE-MDM` is a multi-state funding territory rather than a single physical cost market. Four other AG blocker codes reveal canonical label/scope conflicts that must be normalized before economic use:

- `DE-NI`: the code denotes Lower Saxony, while the library label combines Lower Saxony/Bremen.
- `DE-BB`: the code denotes Brandenburg, while the library label combines Berlin-Brandenburg.
- `DE-HH`: the code denotes Hamburg, while the library label combines Hamburg/Schleswig-Holstein.
- `NO-ROG`: the code denotes Rogaland, while the library label combines Rogaland/Vestland.

An additional conflict was detected at `GB-YRK`: ONS uses **Yorkshire and The Humber**; the nonstandard `Yorkshire` key/label requires a defined scope.

All 14 required exact keys are present and their geographic identities are independently verified: `AU-NSW`, `AU-QLD`, `US-GA`, `US-NY`, `DE-BY`, `CA-BC`, `CA-ON`, `CA-QC`, `US-CA`, `IT-LAZ`, `IT-TOS`, `ES-CAT`, `SE-AB`, `DK-CPH`. This does not mean every economic field for those keys is verified. Exact-key production labor values remain fail closed unless a current retrievable agreement or primary rule supports them.

## AG–Codex reconciliation

| Reconciliation status | Count |
|---|---:|
| `EXACT_AGREEMENT` | 0 |
| `NON_MATERIAL_DIFFERENCE` | 0 |
| `CODEX_HAS_STRONGER_EVIDENCE` | 347 |
| `AG_HAS_STRONGER_EVIDENCE` | 0 |
| `MATERIAL_CONFLICT` | 126 |
| `AG_RECORD_MISSING` | 207 |
| `CODEX_RECORD_MISSING` | 0 |
| `IDENTITY_MISMATCH` | 0 |
| `BOTH_INSUFFICIENT_FAIL_CLOSED` | 2,632 |
| **Total** | **3,312** |

`AG_RECORD_MISSING` covers the 207 identity fields because AG's 621-row completion CSV contains only the three economic categories; AG's separate 13-row identity artifact is addressed in the identity analysis above. `CODEX_HAS_STRONGER_EVIDENCE` means Codex found an official rule where AG recorded category-level insufficient evidence; it does not mean Codex found a priceable value.

## Acceptance questions

1. **Did Codex independently research the complete Core MFNI universe?** Yes. All 207 identities, 621 economic cells and 3,312 defined fields have explicit evidence or documented fail-closed dispositions.
2. **Do the jurisdiction/category denominators reconcile?** Yes: 207 × 3 = 621. The field denominator independently reconciles to 3,312.
3. **Are all 13 identity/scope blockers independently resolved?** No. All 13 were independently addressed, but only 9 have terminal dispositions; 4 remain canonical label/scope conflicts requiring normalization.
4. **Are all 14 subnational keys independently verified?** Yes for identity and presence. No blanket claim is made that all their economic fields are verified.
5. **Is AG's labor evidence accepted, corrected, or incomplete?** Incomplete. The 18 agreement summaries lack retrievable citations and cannot be accepted as field-level canonical evidence.
6. **Is the blanket construction/materials insufficient-evidence classification justified?** Yes for current automatic production economics.
7. **Is the blanket security/medical/safety insufficient-evidence classification justified?** Yes for measurable costs; official framework duties exist in some scopes and are recorded as rule-only.
8. **Are there material AG–Codex conflicts?** Yes, 126 field comparisons, all tied to AG's 18 uncited production-agreement summaries.
9. **Are any usable values synthetic, inferred, stale, or unsupported?** No economic value is designated usable. Geographic identities come from official standards/statistical authorities. Rule-only findings cannot flow as prices.
10. **Is the combined research safe for canonical consolidation and later Claude implementation?** No. Only the verified identity layer and explicit fail-closed controls are safe. Economic implementation must wait for the remaining authorities/quotes and identity normalization.

## Principal authorities

- ILO, Working Conditions Laws/TRAVAIL database overview: <https://www.ilo.org/resource/key-ilo-databases-and-sources>
- ILO, LEGOSH global occupational-safety legislation database: <https://www.ilo.org/resource/global-database-occupational-safety-and-health-legislation>
- World Bank, ICP methodology: <https://www.worldbank.org/en/programs/icp/methodology>
- US Department of Labor, FLSA overtime: <https://www.dol.gov/agencies/whd/fact-sheets/23-flsa-overtime-pay>
- UK Government, maximum weekly hours: <https://www.gov.uk/maximum-weekly-working-hours>
- Australian Fair Work Ombudsman, award/agreement-free conditions: <https://www.fairwork.gov.au/employment-conditions/awards/award-and-agreement-free-wages-and-conditions>
- European Commission, Working Time Directive: <https://employment-social-affairs.ec.europa.eu/policies-and-activities/rights-work/labour-law/working-conditions/working-time-directive_en>
- US OSHA, 29 CFR 1910.151: <https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.151>
- UK HSE, workplace first aid: <https://www.hse.gov.uk/simple-health-safety/firstaid/>
- Safe Work Australia, model first-aid code: <https://www.safeworkaustralia.gov.au/doc/model-code-practice-first-aid-workplace>
- EUR-Lex, Directive 89/391/EEC: <https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A31989L0391>
- ISO 3166 country/subdivision framework: <https://www.iso.org/iso-3166-country-codes.html>

The independent CSV records the precise authority, URL, effective/version date, access date, scope, evidence tier, confidence, search channel and fail-closed reason for every field.

## Remaining canonical blockers

- Retrieve and authenticate the current primary agreement/rate-card documents for AG's 18 labor hubs; verify occupation, signatory, production type, budget tier, geography and effective period field by field.
- Obtain current jurisdiction- and production-specific employer charges where they belong in Core MFNI.
- Obtain authoritative local production-construction schedules/indices or project quotes; do not convert ICP data into a film-set factor.
- Obtain local production security/medical requirements and measurable quotes/official fee schedules where applicable.
- Normalize the five identity/scope conflicts before attaching economic data.

The complete actionable queue is in `MFNI_CORE_RESEARCH_REMAINING_ITEMS_CODEX.csv`.
