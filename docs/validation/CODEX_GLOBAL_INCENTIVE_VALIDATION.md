# Codex Global Incentive Database Validation

Date: 2026-08-09

## Conclusion

CineGlobe is not yet a comprehensive, authoritative worldwide incentive universe. It has broad discovery coverage, but its rule layer is too sparse and unevenly sourced for consolidated optimizer remediation without reconciliation. Principal risks are superseded economics, unmodeled hard gates, non-canonical territoriality, duplicate/non-economic candidates, and incomplete treaty coverage.

This validates the database as stored and changes no CineGlobe data. Completed MU / MT / GR / GB / AU calibration was not re-audited; those records were preserved except where the global database still omits or conflates a separate material program.

## Inventory and source-first pass

| Measure | Result |
|---|---:|
| Active jurisdictions | 187 (129 countries; 58 subjurisdictions) |
| Existing programs | 262 |
| Stored source documents | 17 |
| Distinct program authority URLs | 191 |
| Citation records checked/triaged | 208 |
| URL endpoints returning 2xx | 92 |
| URL endpoints returning 4xx | 33 |
| URL endpoints blocked/unreachable | 66 |
| Stored treaties / participant rows | 38 / 109 |

A blocked endpoint is not proof of staleness; a 2xx response is not proof that a page supports a rule. The JSON preserves this distinction. Stored citations were followed first; only material conflicts and gaps received targeted current official research.

## Classification

| Status | Existing programs |
|---|---:|
| VERIFIED | 8 |
| INCORRECT | 15 |
| INCOMPLETE | 179 |
| STALE | 17 |
| UNRESOLVED | 43 |

VERIFIED is deliberately narrow. INCOMPLETE means a program may be real and its headline rate may be right, but at least one material canonical rule is absent. Project facts are listed separately and do not hide missing canonical rules.

## Structural correction set

- 242 of 262 programs have no structured hard-rule record.
- 239 have no qualifying-spend categories; 62 have no labour/spend treatments.
- 67 have neither an authority URL nor source-document URL; the global database has only 17 source documents.
- No program-wide territoriality predicate exists. Local-SPV payment cannot replace vendor, residence, performance, use/consumption or incurrence tests.
- Generic production support, content obligations, tourism and airline partnerships are mixed with computable incentives.
- Treaty data is a seed, not a complete universe. The [BFI current list](https://www.bfi.org.uk/apply-british-certification-expenditure-credits/co-production/), [CNC agreements index](https://www.cnc.fr/professionnels/etudes-et-rapports/accords-internationaux/accords-de-coproduction-internationale_1115696), [Screen Australia](https://www.screenaustralia.gov.au/co-production-program) and [Telefilm Canada](https://telefilm.ca/en/financing/coproduction) show broader current pathways. Treaty existence does not itself create an incentive benefit.

## Confirmed high-value mismatches

| Jurisdiction | CineGlobe program | Status | Authoritative result | Required remediation |
|---|---|---|---|---|
| Australia | Australia Location Offset / PDV Offset | STALE | Location Offset is 30% of QAPE; Producer and PDV Offsets are distinct statutory pathways. | Split Producer, Location and PDV and preserve already-calibrated QAPE rules. |
| Australia | Australian Content Standard (Streamers) | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| Australia | Tourism Australia Film and Production Support | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| Canada — British Columbia | BC Production Services Tax Credit | STALE | Current BC production-services credit uses an increased basic labour rate plus regional and DAVE components. | Update the basic rate and all labour/regional/digital conditions from current BC authority. |
| Canada | Canadian Film or Video Production Tax Credit | INCORRECT | 25% qualified Canadian labour, subject to statutory 60%-of-net-production-cost labour ceiling and Canadian-content/ownership/personnel rules. | Remove false minimum and encode the ceiling and CAVCO gates. |
| Canada | CRTC Online Streaming Act Local Content Obligation | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| Czech Republic | Czech Film Incentive | STALE | 25% traditional production; 35% animation/digital; CZK450m project cap; eligible basis no more than 80% of budget. | Replace rates, basis/project caps, cultural test, minimums and Czech expenditure rules. |
| European Union — European Union | AVMSD Streamer Local Content Obligation | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| France | SVOD Chronologie des Médias Local Content Obligation | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| France | Tax Rebate for International Productions (TRIP) | INCOMPLETE | TRIP generally 30%; qualifying high-VFX fiction can receive 40% when the official French digital-treatment threshold is met. | Add the official 40% condition and complete caps, cultural test and expenditure rules. |
| Germany | German Federal Film Fund (DFFF/GFFF) | STALE | DFFF and GMPF rose to 30% of recognized German production expenditure with higher caps. | Update DFFF and add distinct GMPF. |
| Iceland | Iceland Post-Production, Visual Effects and Animation Incentive | STALE | Official material substantiates a national reimbursement framework, not a separate uncited flat 25% post/VFX program. | Retire or link to the national scheme unless distinct primary authority is obtained. |
| Iceland | Icelandic Film Reimbursement Scheme | STALE | 35% is available when enhanced statutory spend, days and staffing conditions are met; otherwise the lower tier remains relevant. | Encode the 35% tier and consolidate any non-distinct post/VFX duplicate. |
| India | India NFDC and State Incentives | STALE | Up to 40% of qualifying Indian expenditure, capped at INR300m, for foreign productions and official co-productions through an Indian services company. | Replace type/economics and encode applicant, approval, QPE and co-production gates. |
| Japan | Japan Film Commission Location Incentive (JLOC) | STALE | Current large-scale location support is a competitive 1/2 subsidy, up to JPY1.5bn, with fiscal-year domestic-spend/financing/market criteria. | Replace with current fiscal-year grant and hard gates. |
| Morocco | CCM Morocco — Production Rebate | STALE | 30% eligible Moroccan expenditure; generally MAD10m minimum and 18 Moroccan production days, prior approval and fund availability. | Set 30% current rate and encode minimum, days, formats, local incurrence and preapproval. |
| Netherlands | Netherlands Film Production Incentive (NFPI) | STALE | 35% of qualifying Dutch costs, subject to points/independence tests, caps and format thresholds. | Update to 35% and encode applicant, points, financing, release, thresholds and caps. |
| New Zealand | Air New Zealand Film Production Support | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| New Zealand | Tourism New Zealand Film and Production Support | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| South Africa | NFVF / DTI — South Africa Foreign Film & TV Production Rebate | STALE | Foreign location production: 25% QSAPE plus conditioned 5%; post-only: 25% plus additions; production cap R25m and detailed gates. | Rename to dtic program and encode production/post tiers, QSAPE/QSAPPE, SPCV, financing, B-BBEE and procurement. |
| Spain | Spanish Tax Credit for Foreign Productions | INCORRECT | Mainland foreign production: 30% first EUR1m and 25% thereafter; Canary, Navarre and Basque are separate regimes. | Correct mainland tiers/caps and create separate regional programs. |
| Thailand | Thailand BOI Film Production Incentive | STALE | Foreign productions may receive 15%–30% under current tiers/additions, without a maximum rebate cap. | Update tiers, minimum spend, bonuses, no-cap treatment and preapproval. |
| United Arab Emirates | Dubai Film Commission — Dubai Production Incentive (DPIP) | INCORRECT | Substantiated UAE rebate is Abu Dhabi: 35% standard and 37.5%–50% enhanced points pathway. | Retire/hold Dubai unless primary authority obtained; add Abu Dhabi. |
| United Arab Emirates | Emirates Airline Film Production Partnership | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| United States — California | California Film & Television Tax Credit Program 3.0 | STALE | Program 4.0: generally 35%; relocating TV 40%; independent films 35% on up to $20m qualified spend; most other projects up to $120m qualified spend; specified uplifts. | Replace Program 3.0 economics, gates, caps and uplifts with effective-dated Program 4.0. |
| United States — Georgia | Georgia Entertainment Industry Investment Act | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| United States — Louisiana | Louisiana Motion Picture Production Tax Credit | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| United States — New Mexico | New Mexico Film Production Tax Credit | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| United States — New York | New York State Film Tax Credit | STALE | Current production credit is generally 30%, with conditioned regional additions. | Retire duplicate and retain one current production-credit record. |
| United States — New York | New York State Film Tax Credit Program | STALE | Production and post-production credits are generally 30%, with separately conditioned regional uplifts. | Update production rules, remove duplicate, add separate official post and independent-film programs. |
| United States — Oregon | Oregon Production Investment Fund (OPIF) | INCORRECT | Stored metadata is insufficient for a complete canonical rule. | Complete official-source capture before optimization. |
| United States — United States — Texas | Texas Moving Image Industry Incentive Program (MIIP) | STALE | TMIIIP can reach 31%; SB22 provides $300m per biennium through 2035; resident thresholds are phased. | Update tiers, biennial funding, effective dates and resident-workforce gates. |

## Material missing programs discovered

| Jurisdiction | Missing program | Type | Current economics/status | Official source |
|---|---|---|---|---|
| Canada | Film or Video Production Services Tax Credit (PSTC) | refundable_tax_credit | 16% qualified Canadian labour; refundable; no credit cap. | [official source](https://www.canada.ca/en/canadian-heritage/services/funding/cavco-tax-credits/film-video-production-services.html) |
| Canada — British Columbia | Film Incentive BC (FIBC) | refundable_tax_credit | Distinct domestic/Canadian-content BC labour credit with regional/DAVE components. | [official source](https://www2.gov.bc.ca/gov/content/taxes/income-taxes/corporate/credits/film-tv/film-incentive) |
| Canada — Quebec | Refundable Tax Credit for Film Production Services | refundable_tax_credit | Separate Quebec services credit with basic and VFX/animation components. | [official source](https://sodec.gouv.qc.ca/en/program/tax-credit-for-film-production-services/) |
| United States — New Jersey | Garden State Film and Digital Media Jobs Act — Film Credit | transferable_refundable_tax_credit | 35% generally; 30% within 30-mile NYC radius; diversity bonus up to 4%. | [official source](https://www.nj.gov/njfilm/incentives-credit.shtml) |
| United States — New York | Film Tax Credit — Post-Production | refundable_tax_credit | 30% qualified post; conditioned additional 5% upstate. | [official source](https://esd.ny.gov/new-york-state-film-tax-credit-program-post-production) |
| United States — New York | Empire State Independent Film Production Credit | refundable_tax_credit | 30% qualified costs with separately conditioned 10% additions. | [official source](https://www.tax.ny.gov/pit/credits/empire-state-independent-film-production-credit.htm) |
| United States — Ohio | Ohio Motion Picture Tax Credit | refundable_tax_credit | 30% eligible expenditure. | [official source](https://codes.ohio.gov/ohio-revised-code/section-122.85) |
| United States — Arkansas | Digital Product and Motion Picture Industry Incentive | rebate_or_transferable_tax_credit | Current AEDC: 25% base plus 10% qualified resident/veteran payroll or veteran-owned vendors. | [official source](https://www.arkansasedc.com/why-arkansas/business-climate/incentives/pages/film-production-incentives) |
| United States — West Virginia | West Virginia Film Production Tax Credit | transferable_tax_credit | 27% base plus 4% resident-hire gate; agency states no current project/fiscal cap. | [official source](https://westvirginia.gov/filmincentives/) |
| United States — Missouri | Motion Media Production Tax Credit | tax_credit | Current program; statutory additions depend on project/workforce attributes. | [official source](https://ded.mo.gov/programs/business-workforce/motion-media-production-tax-credit-program) |
| United States — Montana | MEDIA Tax Credit | transferable_tax_credit | 20% base, additions up to 35%; intake paused and first available credit stated as 2031. | [official source](https://commerce.mt.gov/Business/Programs-and-Services/Montana-Film-Office/Incentives/MEDIA-Tax-Credit) |
| Australia | Producer Offset (separate statutory program) | refundable_tax_offset | Separate Producer Offset; rates differ by format from Location/PDV. | [official source](https://www.screenaustralia.gov.au/funding-and-support/producer-offset) |
| United Kingdom | Enhanced AVEC / Independent Film Tax Credit (IFTC) | payable_expenditure_credit | 53% rate; up to GBP15m relevant global expenditure counted. | [official source](https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual/crec021110) |
| United Kingdom | UK Global Screen Fund — International Co-production | nonrecoupable_grant | Competitive non-recoupable grants up to GBP300,000. | [official source](https://www.bfi.org.uk/get-funding-support/create-films-tv-or-new-formats-storytelling/international-co-productions) |
| Germany | German Motion Picture Fund (GMPF) | grant | 30% recognized German expenditure with current caps. | [official source](https://www.ffa.de/files/ffa/av-info-publikationen-downloads/26_DFFF_GMPF_At_A_Glance_2025_EN.pdf) |
| United Arab Emirates — Abu Dhabi | Abu Dhabi 35++ Production Rebate | cash_rebate | 35% standard; enhanced 37.5%–50% by points. | [official source](https://www.film.gov.ae/35-rebate) |
| Colombia | CINA Audiovisual Investment Certificate | transferable_tax_certificate | 35% qualifying audiovisual/logistical services as marketable certificate. | [official source](https://www.proimagenescolombia.com/secciones/pantalla_colombia/breves_plantilla.php?id_noticia=13599) |
| Spain — Canary Islands | Canary Islands Foreign Production Tax Deduction | tax_credit | 54% first EUR1m; 45% thereafter; caps EUR36m/EUR18m per episode. | [official source](https://www.investinspain.org/content/dam/icex-invest/documentos/publicaciones/sectores/industria-audiovisual/ICEX-Invest%20in%20Spain.%20Audiovisual.pdf) |
| Spain — Navarre | Navarre Audiovisual Production Tax Credit | tax_credit | Up to 50%, subject to current conditions. | [official source](https://www.investinspain.org/content/dam/icex-invest/documentos/publicaciones/sectores/industria-audiovisual/ICEX-Invest%20in%20Spain.%20Audiovisual.pdf) |
| Spain — Basque Country | Basque Provincial Audiovisual Tax Credits | tax_credit | Province-specific: Biscay up to 70%; Gipuzkoa/Álava differ. | [official source](https://www.investinspain.org/content/dam/icex-invest/documentos/publicaciones/who-is-who-shooting/24/FEDERATION.pdf) |
| South Africa | South African Film and Television Production / Co-production Incentive | cash_grant | 35% QSAPE plus conditioned 5%; cap R50m. | [official source](https://www.thedtic.gov.za/south-african-film-and-television-production-incentive-2/) |
| Netherlands | Netherlands Film Production Incentive — High-End Series | cash_rebate_grant | 35% qualifying Dutch costs under distinct series regulation. | [official source](https://www.filmfonds.nl/en/rules-and-regulations) |
| Thailand | Foreign Digital Content Production Incentive | cash_rebate | 20% qualifying contract production fees. | [official source](https://thailand.prd.go.th/en/content/category/detail/id/2078/iid/472682) |

## Treaty and stacking result

CineGlobe's treaty data must be rebuilt from current competent-authority lists, preserving contribution thresholds, nationality/creative rules, preapproval and the difference between national treatment and actual program eligibility. Stacking edges must state whether assistance reduces QPE, whether state-aid intensity applies, and whether benefits are mutually exclusive.

## Global jurisdiction scorecard

| Jurisdiction | Existing | V | I | Incomplete | Stale | Unresolved | Missing | Treaty | Regional | VFX/post | Funds/grants | Overall |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| Albania | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Algeria | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Angola | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | PRESENT/INCOMPLETE | PRESENT/INCOMPLETE | UNVERIFIED |
| Argentina | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Armenia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Australia | 9 | 1 | 2 | 5 | 1 | 0 | 1 | PARTIAL (8 stored) | PARTIAL | PRESENT/INCOMPLETE | PRESENT/INCOMPLETE | MATERIAL GAPS |
| Austria | 3 | 0 | 0 | 3 | 0 | 0 | 0 | PARTIAL (3 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Azerbaijan | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Bahamas | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Bahrain | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Bangladesh | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Barbados | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Belarus | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Belgium | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (4 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Bhutan | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Bosnia and Herzegovina | 1 | 0 | 0 | 0 | 0 | 1 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Botswana | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Brazil | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Bulgaria | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Cambodia | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Cameroon | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Canada | 19 | 0 | 2 | 16 | 1 | 0 | 3 | PARTIAL (13 stored) | PARTIAL | PRESENT/INCOMPLETE | PRESENT/INCOMPLETE | MATERIAL GAPS |
| Chile | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| China | 1 | 0 | 0 | 0 | 0 | 1 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Colombia | 1 | 0 | 0 | 1 | 0 | 0 | 1 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | MATERIAL GAPS |
| Costa Rica | 1 | 0 | 0 | 0 | 0 | 1 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Côte d'Ivoire | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Croatia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Cuba | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Cyprus | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Czech Republic | 2 | 0 | 0 | 1 | 1 | 0 | 0 | PARTIAL (3 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | MATERIAL GAPS |
| Denmark | 2 | 0 | 0 | 2 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Dominican Republic | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Ecuador | 1 | 0 | 0 | 0 | 0 | 1 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Egypt | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Estonia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Ethiopia | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Faroe Islands | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Fiji | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | PRESENT/INCOMPLETE | GAP/UNVERIFIED | UNVERIFIED |
| Finland | 2 | 0 | 0 | 2 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| France | 7 | 0 | 1 | 6 | 0 | 0 | 0 | PARTIAL (8 stored) | NONE/UNVERIFIED | PRESENT/INCOMPLETE | PRESENT/INCOMPLETE | MATERIAL GAPS |
| Gabon | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Georgia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Germany | 6 | 0 | 0 | 5 | 1 | 0 | 1 | PARTIAL (11 stored) | PARTIAL | GAP/UNVERIFIED | PRESENT/INCOMPLETE | MATERIAL GAPS |
| Ghana | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Greece | 2 | 1 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | PARTIAL |
| Greenland | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Guatemala | 1 | 0 | 0 | 0 | 0 | 1 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Guyana | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Hong Kong SAR | 2 | 0 | 0 | 1 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Hungary | 2 | 0 | 0 | 2 | 0 | 0 | 0 | PARTIAL (3 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Iceland | 2 | 0 | 0 | 0 | 2 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | PRESENT/INCOMPLETE | GAP/UNVERIFIED | MATERIAL GAPS |
| India | 2 | 0 | 0 | 1 | 1 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | MATERIAL GAPS |
| Indonesia | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Iran | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Ireland | 4 | 0 | 0 | 3 | 0 | 1 | 0 | PARTIAL (5 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Isle of Man | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (11 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Israel | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Italy | 3 | 0 | 0 | 3 | 0 | 0 | 0 | PARTIAL (5 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Jamaica | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Japan | 2 | 0 | 0 | 0 | 1 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | PRESENT/INCOMPLETE | GAP/UNVERIFIED | MATERIAL GAPS |
| Jordan | 2 | 0 | 0 | 1 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Kazakhstan | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Kenya | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Kosovo | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Kuwait | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Latvia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Lebanon | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Lithuania | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Luxembourg | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Macau SAR | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Malaysia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Maldives | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Malta | 1 | 1 | 0 | 0 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | COMPLETE |
| Mauritius | 1 | 1 | 0 | 0 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | COMPLETE |
| Mexico | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Moldova | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Mongolia | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Montenegro | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Morocco | 2 | 0 | 0 | 0 | 1 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | MATERIAL GAPS |
| Mozambique | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Namibia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Netherlands | 3 | 0 | 0 | 2 | 1 | 0 | 1 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | MATERIAL GAPS |
| New Zealand | 4 | 0 | 2 | 2 | 0 | 0 | 0 | PARTIAL (3 stored) | NONE/UNVERIFIED | PRESENT/INCOMPLETE | GAP/UNVERIFIED | MATERIAL GAPS |
| Nigeria | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| North Macedonia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Norway | 2 | 0 | 0 | 2 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Oman | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Pakistan | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Panama | 1 | 0 | 0 | 0 | 0 | 1 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Paraguay | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Peru | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Philippines | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Poland | 2 | 0 | 0 | 2 | 0 | 0 | 0 | PARTIAL (3 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Portugal | 2 | 0 | 0 | 2 | 0 | 0 | 0 | PARTIAL (3 stored) | NONE/UNVERIFIED | PRESENT/INCOMPLETE | PRESENT/INCOMPLETE | UNVERIFIED |
| Qatar | 2 | 0 | 0 | 2 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Romania | 1 | 0 | 0 | 0 | 1 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | MATERIAL GAPS |
| Russia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Rwanda | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Saudi Arabia | 2 | 0 | 0 | 2 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Senegal | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Serbia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Seychelles | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Singapore | 3 | 0 | 0 | 2 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Slovakia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | PRESENT/INCOMPLETE | GAP/UNVERIFIED | UNVERIFIED |
| Slovenia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| South Africa | 2 | 0 | 0 | 1 | 1 | 0 | 1 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | MATERIAL GAPS |
| South Korea | 3 | 0 | 0 | 2 | 0 | 1 | 0 | PARTIAL (3 stored) | NONE/UNVERIFIED | PRESENT/INCOMPLETE | PRESENT/INCOMPLETE | UNVERIFIED |
| Spain | 2 | 0 | 1 | 1 | 0 | 0 | 3 | PARTIAL (4 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | MATERIAL GAPS |
| Sri Lanka | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Sweden | 3 | 0 | 0 | 3 | 0 | 0 | 0 | PARTIAL (2 stored) | PARTIAL | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Switzerland | 2 | 0 | 0 | 2 | 0 | 0 | 0 | PARTIAL (3 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Taiwan | 2 | 0 | 0 | 2 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | PRESENT/INCOMPLETE | PRESENT/INCOMPLETE | UNVERIFIED |
| Tanzania | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Thailand | 1 | 0 | 0 | 0 | 1 | 0 | 1 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | MATERIAL GAPS |
| Trinidad & Tobago | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Tunisia | 1 | 0 | 0 | 1 | 0 | 0 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Turkey | 2 | 0 | 0 | 2 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Uganda | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Ukraine | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (2 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| United Arab Emirates | 2 | 0 | 2 | 0 | 0 | 0 | 1 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | MATERIAL GAPS |
| United Kingdom | 8 | 0 | 0 | 7 | 0 | 1 | 2 | PARTIAL (11 stored) | PARTIAL | PRESENT/INCOMPLETE | PRESENT/INCOMPLETE | MATERIAL GAPS |
| United States | 36 | 4 | 4 | 24 | 4 | 0 | 8 | NONE/UNVERIFIED | PARTIAL | GAP/UNVERIFIED | PRESENT/INCOMPLETE | MATERIAL GAPS |
| Uruguay | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Uzbekistan | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Venezuela | 1 | 0 | 0 | 1 | 0 | 0 | 0 | PARTIAL (1 stored) | NONE/UNVERIFIED | GAP/UNVERIFIED | PRESENT/INCOMPLETE | UNVERIFIED |
| Vietnam | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Zambia | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |
| Zimbabwe | 1 | 0 | 0 | 0 | 0 | 1 | 0 | NONE/UNVERIFIED | NONE/UNVERIFIED | GAP/UNVERIFIED | GAP/UNVERIFIED | UNVERIFIED |

## Handoff

The JSON contains all 262 existing records, 23 missing-program records, the jurisdiction scorecard and all 38 stored treaty records. Implementation should start only after Codex/Gemini reconciliation selects canonical primary sources and resolves UNRESOLVED items.

