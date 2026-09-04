# CineGlobe Current Discretionary / Non-Formulaic Program Inventory — Codex

Audit date: 2026-09-03  
Repository baseline: f8b66972a59b2792d6e179a25f419484190dc7cc  
Mode: read-only canonical-library reconciliation; no external research; no application/data/rule changes

## 1. Executive result

**Exact current deduplicated count: 160 real program identities.**

| Category | Count |
|---|---:|
| SELECTIVE | 17 |
| DISCRETIONARY | 7 |
| NEGOTIATED | 0 |
| GRANT-FUND | 136 |
| OTHER NON-FORMULAIC PRODUCTION SUPPORT | 0 |
| **Total** | **160** |

No current record met a distinct NEGOTIATED or OTHER NON-FORMULAIC PRODUCTION SUPPORT classification once overlaps were resolved. “Conditionally modelable” means the formula can be calculated after a real selection/award fact exists; it is not a guaranteed expected value.

Economic-state totals: **142 NON-PRICEABLE**, **18 CONDITIONALLY MODELABLE**, **0 deterministically priceable as an award outcome**. Current visibility totals: **71 conditional annotations**, **17 current formula scenarios carrying a conditional award/selection gate**, **71 not visible to the current optimizer**, and **1 legacy-only NOHFC path**.

## 2. Boundary and reconciliation method

- Started from the live global inventory (303 records), conditional-program index (134 nodes), authority coverage registry (145 records; 24 raw NON_GUARANTEED_SELECTIVE rows), live requirements/allocation profiles, executable doctrine/RateRules, and structured-provenance classifier.
- Counted one real program once. Twelve authority-coverage identities duplicate conditional nodes and use the authority slug in this table. The Japan and Korea canonical/runtime slug pairs are aliases, not extra programs.
- Reconciled the generic `singapore_imda_digital_media_development_fund` identity to the current conditional IMDA Digital Media Content Programme rather than counting both. Reconciled the two ICA Portugal production-grant catalog rows as one real selective production-grant program; the separate ICA international co-production fund remains distinct.
- Excluded IBERMEDIA_MEMBERSHIP_AND_FRAMEWORK: membership/framework metadata is not itself a monetary award. The actual IBERMEDIA Programme remains counted.
- Excluded COND-CH-media-desk-switzerland-succ-s-cin-ma-automatic-support: the catalog itself calls Succès Cinéma automatic support, so it does not meet this audit boundary.
- Did not count ordinary formulaic application, certification, objective cultural tests, project-fact uplifts, or first-come allocation merely because the internal conservative-ceiling mechanism uses RateCondition.kind=discretionary_band.
- CURRENT below means a current, deduplicated identity represented by the current library. Authority quality is separate; all 132 counted conditional catalog nodes remain DISCOVERY tier and must not be mistaken for current primary-authority validation.

## 3. Counts by jurisdiction / subnational jurisdiction

| Jurisdiction code | Count |
|---|---:|
| GB | 7 |
| CA | 5 |
| DE | 4 |
| FR | 4 |
| NL | 4 |
| SG | 3 |
| AU | 3 |
| CH | 3 |
| DK | 3 |
| EU | 3 |
| KR | 3 |
| NO | 3 |
| PT | 2 |
| US | 3 |
| AT | 2 |
| FI | 2 |
| IE | 2 |
| IL | 2 |
| IN | 2 |
| IT | 2 |
| JP | 2 |
| SE | 2 |
| TW | 2 |
| ZA | 2 |
| ACP | 1 |
| AM | 1 |
| AO | 1 |
| AR | 1 |
| AU-NT | 1 |
| AU-QLD | 1 |
| AU-TAS | 1 |
| AZ | 1 |
| BE-BRU | 1 |
| BE-VLG | 1 |
| BE-WAL | 1 |
| BF | 1 |
| BR | 1 |
| BT | 1 |
| CA-MB | 1 |
| CA-ON | 1 |
| CA-PE | 1 |
| CA-SK | 1 |
| CI | 1 |
| CL | 1 |
| CM | 1 |
| CU | 1 |
| CZ | 1 |
| DE-BB | 1 |
| DE-BW | 1 |
| DE-BY | 1 |
| DE-HH | 1 |
| DE-MDM | 1 |
| DE-NI | 1 |
| DE-NW | 1 |
| DK-CPH | 1 |
| DZ | 1 |
| ES | 1 |
| ES-AND | 1 |
| ES-CAT | 1 |
| ES-EUS | 1 |
| ES-GAL | 1 |
| ES-VAL | 1 |
| FR-ARA | 1 |
| FR-IDF | 1 |
| FR-NAQ | 1 |
| FR-OCC | 1 |
| GB-LON | 1 |
| GB-NIR | 1 |
| GB-YRK | 1 |
| GR | 1 |
| HK | 1 |
| HU | 1 |
| IBERO | 1 |
| IR | 1 |
| IT-APU | 1 |
| IT-CAM | 1 |
| IT-LAZ | 1 |
| IT-PIE | 1 |
| IT-SIC | 1 |
| IT-TOS | 1 |
| JO | 1 |
| LB | 1 |
| LU | 1 |
| MA | 1 |
| MD | 1 |
| MO | 1 |
| MT | 1 |
| MU | 1 |
| MX | 1 |
| NA | 1 |
| NG | 1 |
| NO-ROG | 1 |
| NO-TRO | 1 |
| NORDIC | 1 |
| PE | 1 |
| PH | 1 |
| PL | 1 |
| QA | 1 |
| RU | 1 |
| RW | 1 |
| SA | 1 |
| SA-KSA | 1 |
| SE-AB | 1 |
| SE-SK | 1 |
| SE-VG | 1 |
| TN | 1 |
| TR | 1 |
| UA | 1 |
| US-CA | 1 |
| US-KY | 1 |
| US-OR | 1 |
| US-PA | 1 |
| US-WA | 1 |
| VE | 1 |

## 4. Exact current inventory

For conditional-library rows without a runtime program_slug, the stable COND-* node ID is the canonical identifier. Discoverable means production-discovery candidacy, not conditional annotation.

| Canonical slug / node ID | Exact program name | Jurisdiction | Category | State | Authority / provenance | Discoverable | Can generate scenario | Economics | Optimizer visibility | Material gates |
|---|---|---|---|---|---|---|---|---|---|---|
| acpfilms_fund | ACP Films — EU-ACP Cultural Film Co-production Fund | ACP | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | official co-production status; competitive/panel award; membership/eligible-country route; local entity; cultural test |
| COND-AM-national-cinema-centre-of-armenia-production-support | National Cinema Centre of Armenia Production Support | AM | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; cultural test |
| COND-AO-angola-instituto-do-cinema-e-audiovisual-ica-production-supp | Angola Instituto do Cinema e Audiovisual (ICA) Production Support | AO | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity |
| COND-AR-incaa-foprocine-development-and-production-grants | INCAA — Foprocine Development and Production Grants | AR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| COND-AT-austrian-film-institute-fi-production-support | Austrian Film Institute (ÖFI) — Production Support | AT | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-AT-orf-film-fernseh-abkommen-co-production-fund | ORF Film/Fernseh-Abkommen — Co-production Fund | AT | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; local entity; cultural test |
| COND-AU-melbourne-international-film-festival-miff-premiere-fund | Melbourne International Film Festival (MIFF) Premiere Fund | AU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-AU-screen-australia-production-funding | Screen Australia — Production Funding | AU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-AU-screen-australia-talent-and-business-development-programs | Screen Australia — Talent and Business Development Programs | AU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| COND-AU-NT-territory-screen-northern-territory-production-support | Territory Screen — Northern Territory Production Support | AU-NT | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in AU-NT |
| au_qld_screen_qld | Screen Queensland Production Attraction Strategy | AU-QLD | SELECTIVE | CURRENT | NON_GUARANTEED_SELECTIVE; no deterministic RateRule | NO | NO | NON-PRICEABLE | NO | competitive attraction-strategy award; Queensland production commitment |
| COND-AU-TAS-screen-tasmania-production-support | Screen Tasmania — Production Support | AU-TAS | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in AU-TAS |
| COND-AZ-azerbaijan-film-fund-production-support | Azerbaijan Film Fund Production Support | AZ | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award |
| COND-BE-BRU-screen-brussels-production-support | Screen.Brussels Production Support | BE-BRU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | regional qualifying spend; competitive/panel award; spend/participation in BE-BRU |
| COND-BE-VLG-vaf-flanders-audiovisual-fund | VAF Flanders Audiovisual Fund | BE-VLG | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | regional qualifying spend; competitive/panel award; spend/participation in BE-VLG |
| COND-BE-WAL-wallimage-co-production-fund | Wallimage Co-production Fund | BE-WAL | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | regional qualifying spend; competitive/panel award; spend/participation in BE-WAL |
| COND-BF-fespaco-festival-pan-africain-du-cin-ma-et-de-la-t-l-vision- | FESPACO — Festival Pan-Africain du Cinéma et de la Télévision de Ouagadougou | BF | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | editorial/competitive award; development-phase scope (not production NPC); cultural test |
| COND-BR-ancine-fsa-fundo-setorial-do-audiovisual-development-fund | ANCINE — FSA (Fundo Setorial do Audiovisual) Development Fund | BR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| bt_film_incentive | Bhutan Film Commission / Tourism Council Production Facilitation | BT | SELECTIVE | CURRENT | NON_GUARANTEED_SELECTIVE; no deterministic RateRule | NO | NO | NON-PRICEABLE | NO | selective domestic support; permits/content review; local cultural eligibility |
| COND-CA-bell-fund-broadcast-and-digital-content-development | Bell Fund — Broadcast and Digital Content Development | CA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| COND-CA-canada-media-fund-cmf-convergent-stream | Canada Media Fund (CMF) — Convergent Stream | CA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-CA-nsi-national-screen-institute-drama-prize-and-development-pr | NSI — National Screen Institute Drama Prize and Development Programs | CA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| COND-CA-telefilm-canada-canada-feature-film-fund-cfff | Telefilm Canada — Canada Feature Film Fund (CFFF) | CA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-CA-telefilm-canada-export-development-program | Telefilm Canada — Export Development Program | CA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| COND-CA-MB-manitoba-film-music-production-support-grants | Manitoba Film & Music — Production Support Grants | CA-MB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; spend/participation in CA-MB |
| nohfc_production_fund | Northern Ontario Heritage Fund — Production Fund | CA-ON | GRANT-FUND | CURRENT | PARSED catalog/migration; no current canonical RateRule | NO | LEGACY ONLY | CONDITIONALLY MODELABLE | LEGACY ONLY | discretionary application/award; Northern Ontario spend; local entity; actual award amount required |
| COND-CA-PE-film-pei-prince-edward-island-production-support | Film PEI — Prince Edward Island Production Support | CA-PE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in CA-PE |
| COND-CA-SK-creative-saskatchewan-film-and-tv-production-grant | Creative Saskatchewan Film and TV Production Grant | CA-SK | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; spend/participation in CA-SK; cultural test |
| COND-CH-bak-swiss-federal-office-of-culture-international-co-product | BAK Swiss Federal Office of Culture — International Co-production Support | CH | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | official co-production status; competitive/panel award; local entity; cultural test |
| COND-CH-swiss-federal-office-of-culture-foc-film-support | Swiss Federal Office of Culture (FOC) Film Support | CH | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| ch_pics_national_rebate | Switzerland PICS National Location Incentive | CH | SELECTIVE | CURRENT | AUTHORITY_UNRESOLVED_NON_PRICEABLE; STRUCTURED_PROVENANCE_PARTIAL_WITH_EXACT_AUTHORITY_RESIDUAL; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | competitive application; preapproval; international co-production focus; rate/award criteria unresolved |
| COND-CI-centre-national-de-cin-ma-de-c-te-d-ivoire-cnci-film-support | Centre National de Cinéma de Côte d'Ivoire (CNCI) Film Support | CI | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity |
| cl_corfo_incentive | Chile CORFO Film Incentive | CL | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | competitive application; preapproval; capped call/allocation |
| cm_film_incentive | Cameroon Centre National de la Cinématographie (CNC-Cameroon) | CM | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity |
| COND-CU-icaic-cuba-film-production-support | ICAIC Cuba Film Production Support | CU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity |
| COND-CZ-czech-film-fund-production-support | Czech Film Fund — Production Support | CZ | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-DE-berlinale-world-cinema-fund-wcf-development-and-production-g | Berlinale World Cinema Fund (WCF) — Development and Production Grants | DE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); cultural test |
| COND-DE-german-films-international-export-and-market-promotion | German Films International — Export and Market Promotion | DE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-DE-wdr-ard-film-and-co-production-fund | WDR / ARD — Film and Co-production Fund | DE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-DE-zdf-das-kleine-fernsehspiel-co-production-fund | ZDF / Das Kleine Fernsehspiel — Co-production Fund | DE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-DE-BB-medienboard-berlin-brandenburg-mbb-film-production-fund | Medienboard Berlin-Brandenburg (MBB) — Film Production Fund | DE-BB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in DE-BB; local entity; cultural test |
| COND-DE-BW-mfg-medien-und-filmgesellschaft-baden-w-rttemberg | MFG Medien- und Filmgesellschaft Baden-Württemberg | DE-BW | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in DE-BW; local entity; cultural test |
| COND-DE-BY-filmfernsehfonds-bayern-fff-bayern | FilmFernsehFonds Bayern (FFF Bayern) | DE-BY | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in DE-BY; cultural test |
| COND-DE-HH-film-und-medienstiftung-hamburg-schleswig-holstein | Film- und Medienstiftung Hamburg Schleswig-Holstein | DE-HH | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in DE-HH; local entity; cultural test |
| COND-DE-MDM-mitteldeutsche-medienf-rderung-mdm-film-production-fund | Mitteldeutsche Medienförderung (MDM) — Film Production Fund | DE-MDM | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in DE-MDM; local entity; cultural test |
| COND-DE-NI-nordmedia-film-und-mediengesellschaft | nordmedia Film und Mediengesellschaft | DE-NI | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | regional qualifying spend; competitive/panel award; spend/participation in DE-NI |
| COND-DE-NW-film-und-medienstiftung-nrw | Film und Medienstiftung NRW | DE-NW | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in DE-NW; cultural test |
| COND-DK-dr-danish-broadcasting-corporation-co-production-fund | DR — Danish Broadcasting Corporation Co-production Fund | DK | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-DK-danish-film-institute-production-support | Danish Film Institute Production Support | DK | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; cultural test |
| dk_production_rebate | Denmark Production Rebate | DK | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | two annual calls; points-ranked competition; fixed annual envelope; preapproval |
| COND-DK-CPH-copenhagen-film-fund-regional-co-production-support | Copenhagen Film Fund — Regional Co-production Support | DK-CPH | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | official co-production status; competitive/panel award; spend/participation in DK-CPH; cultural test |
| COND-DZ-centre-alg-rien-pour-le-d-veloppement-du-cin-ma-cadc-film-su | Centre Algérien pour le Développement du Cinéma (CADC) Film Support | DZ | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity |
| COND-ES-rtve-radio-televisi-n-espa-ola-co-production-fund | RTVE — Radio Televisión Española Co-production Fund | ES | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; local entity; cultural test |
| COND-ES-AND-andalucia-film-commission-audiovisual-production-incentive | Andalucia Film Commission — Audiovisual Production Incentive | ES-AND | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in ES-AND |
| COND-ES-CAT-icec-institut-catal-de-les-empreses-culturals-film-support | ICEC — Institut Català de les Empreses Culturals Film Support | ES-CAT | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in ES-CAT; local entity; cultural test |
| COND-ES-EUS-basque-audiovisual-eusko-jaurlaritza-film-production-support | Basque Audiovisual — Eusko Jaurlaritza Film Production Support | ES-EUS | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in ES-EUS; local entity; cultural test |
| COND-ES-GAL-agadic-axencia-galega-das-industrias-culturais-film-producti | Agadic — Axencia Galega das Industrias Culturais Film Production Fund | ES-GAL | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in ES-GAL; local entity; cultural test |
| COND-ES-VAL-institut-valenci-de-cultura-ivc-audiovisual-production-fund | Institut Valencià de Cultura (IVC) — Audiovisual Production Fund | ES-VAL | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in ES-VAL |
| COND-EU-creative-europe-media-programme | Creative Europe MEDIA Programme | EU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | official co-production status; competitive/panel award; membership/eligible-country route; local entity; cultural test |
| COND-EU-eurimages-council-of-europe-co-production-fund | Eurimages — Council of Europe Co-production Fund | EU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | official co-production status; competitive/panel award; membership/eligible-country route; local entity; cultural test |
| COND-EU-torino-film-lab-international-development-and-production-gra | Torino Film Lab — International Development and Production Grants | EU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | editorial/competitive award; development-phase scope (not production NPC); membership/eligible-country route; cultural test |
| COND-FI-finnish-film-foundation-ses-production-grants | Finnish Film Foundation (SES) — Production Grants | FI | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-FI-yle-finnish-broadcasting-company-co-production-fund | YLE — Finnish Broadcasting Company Co-production Fund | FI | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-FR-arte-france-cin-ma-co-production-fund | Arte France Cinéma — Co-production Fund | FR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-FR-canal-obligation-de-contribution-la-production-fran-aise | CANAL+ — Obligation de Contribution à la Production Française | FR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; local entity; cultural test |
| COND-FR-cnc-france-avances-sur-recettes-cinema-production-aid | CNC France — Avances sur Recettes (Cinema Production Aid) | FR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-FR-unifrance-international-distribution-and-promotion-support | UniFrance — International Distribution and Promotion Support | FR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-FR-ARA-auvergne-rh-ne-alpes-cinema-regional-aid | Auvergne-Rhône-Alpes Cinema Regional Aid | FR-ARA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | regional qualifying spend; competitive/panel award; spend/participation in FR-ARA |
| COND-FR-IDF-le-de-france-cinema-regional-aid | Île-de-France Cinema Regional Aid | FR-IDF | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | regional qualifying spend; competitive/panel award; spend/participation in FR-IDF |
| COND-FR-NAQ-nouvelle-aquitaine-regional-cinema-aid | Nouvelle-Aquitaine Regional Cinema Aid | FR-NAQ | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | regional qualifying spend; competitive/panel award; spend/participation in FR-NAQ |
| COND-FR-OCC-occitanie-cinema-regional-aid | Occitanie Cinema Regional Aid | FR-OCC | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | regional qualifying spend; competitive/panel award; spend/participation in FR-OCC |
| COND-GB-bbc-films-co-production-and-development-fund | BBC Films — Co-production and Development Fund | GB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-GB-bfi-film-fund-production-funding | BFI Film Fund — Production Funding | GB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-GB-bfi-international-export-development-and-distribution-suppor | BFI International — Export Development and Distribution Support | GB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-GB-channel-4-film-film4-co-production-fund | Channel 4 Film / Film4 — Co-production Fund | GB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-GB-creative-england-production-finance-english-regions | Creative England — Production Finance (English Regions) | GB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-GB-screenskills-production-training-fund | ScreenSkills — Production Training Fund | GB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| proposed_united_kingdom_uk_global_screen_fund_international_co_production | UK Global Screen Fund — International Co-production | GB | GRANT-FUND | CURRENT | NON_GUARANTEED_SELECTIVE; no deterministic RateRule | NO | NO | NON-PRICEABLE | NO | competitive call; eligible international co-production; panel award |
| COND-GB-LON-film-london-production-finance-market-and-support | Film London — Production Finance Market and Support | GB-LON | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | official co-production status; competitive/panel award; spend/participation in GB-LON; local entity; cultural test |
| COND-GB-NIR-northern-ireland-screen-production-fund | Northern Ireland Screen — Production Fund | GB-NIR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in GB-NIR; local entity; cultural test |
| COND-GB-YRK-screen-yorkshire-yorkshire-content-fund | Screen Yorkshire — Yorkshire Content Fund | GB-YRK | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in GB-YRK; cultural test |
| COND-GR-greek-film-centre-gfc-selective-production-grants | Greek Film Centre (GFC) — Selective Production Grants | GR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| hk_film_dev_fund | Hong Kong Film Development Fund (FDF) | HK | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity; cultural test |
| COND-HU-national-film-institute-nfi-hungary-production-grant | National Film Institute (NFI Hungary) — Production Grant | HU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| ibermedia_programme | IBERMEDIA Programme for Ibero-American Co-productions | IBERO | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | official co-production status; competitive/panel award; membership/eligible-country route; local entity; cultural test |
| COND-IE-rt-broadcasting-authority-of-ireland-co-production-fund | RTÉ — Broadcasting Authority of Ireland Co-production Fund | IE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-IE-screen-ireland-development-and-skills-programme | Screen Ireland — Development and Skills Programme | IE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| il_film_incentive | Israel Film Fund / Maslool Incentive | IL | GRANT-FUND | CURRENT | NON_GUARANTEED_SELECTIVE; no deterministic RateRule | NO | NO | NON-PRICEABLE | NO | competitive round/fixed fund; Israeli applicant; award decision |
| COND-IL-jerusalem-international-film-lab-development-grants | Jerusalem International Film Lab — Development Grants | IL | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC) |
| COND-IN-india-national-film-development-corporation-nfdc-and-state-i | India National Film Development Corporation (NFDC) and State Incentives | IN | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; cultural test |
| COND-IN-nfdc-international-co-production-development-fund | NFDC International Co-production Development Fund | IN | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | official co-production status; competitive/panel award; local entity; cultural test |
| COND-IR-farabi-cinema-foundation-film-production-support | Farabi Cinema Foundation Film Production Support | IR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity; cultural test |
| COND-IT-anica-mic-italian-film-international-distribution-support | ANICA / MiC — Italian Film International Distribution Support | IT | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-IT-rai-cinema-co-production-and-acquisition-fund | RAI Cinema — Co-production and Acquisition Fund | IT | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; local entity; cultural test |
| COND-IT-APU-apulia-film-commission-film-fund | Apulia Film Commission — Film Fund | IT-APU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in IT-APU |
| COND-IT-CAM-film-commission-campania-production-fund | Film Commission Campania — Production Fund | IT-CAM | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in IT-CAM |
| COND-IT-LAZ-lazio-cinema-international-film-fund | Lazio Cinema International — Film Fund | IT-LAZ | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in IT-LAZ |
| COND-IT-PIE-film-commission-torino-piemonte-production-support | Film Commission Torino Piemonte — Production Support | IT-PIE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in IT-PIE |
| COND-IT-SIC-sicilia-film-commission-film-fund | Sicilia Film Commission — Film Fund | IT-SIC | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in IT-SIC |
| COND-IT-TOS-film-commission-toscana-production-support | Film Commission Toscana — Production Support | IT-TOS | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in IT-TOS |
| jo_rfc_rebate | Jordan Royal Film Commission Production Rebate | JO | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_PARTIAL_WITH_EXACT_AUTHORITY_RESIDUAL; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | competitive selection; points assessment; local spend and cultural/economic criteria; preapproval |
| vipo_animation_and_content_support | VIPO — Visual Industry Promotion Organization Animation Support | JP | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | official co-production status; competitive/panel award; cultural test |
| jp_vipo_location_incentive | Japan Film Commission Location Incentive (JLOC) | JP | SELECTIVE | CURRENT | NON_GUARANTEED_SELECTIVE; no deterministic RateRule | NO | NO | NON-PRICEABLE | NO | competitive fiscal-year selection; preapproval; project-specific award |
| korea_kocca_animation_production_support | KOCCA — Korea Creative Content Agency Animation and VFX Support | KR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-KR-kofic-international-co-production-and-export-support | KOFIC — International Co-production and Export Support | KR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| kr_kofic_location_incentive | Korea Film Council (KOFIC) Location Incentive | KR | SELECTIVE | CURRENT | NON_GUARANTEED_SELECTIVE; no deterministic RateRule | NO | NO | NON-PRICEABLE | NO | selective location-support award; application; project-specific approval |
| COND-LB-centre-du-cin-ma-libanais-ccl-production-support | Centre du Cinéma Libanais (CCL) Production Support | LB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity; cultural test |
| lu_filmfund_tax_shelter_rebate | Film Fund Luxembourg (Filmfund) — Tax Shelter & Rebate | LU | DISCRETIONARY | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | Film Fund discretion; preapproval; local/cultural qualification; award decision |
| COND-MA-centre-cin-matographique-marocain-ccm-avance-sur-recettes | Centre Cinématographique Marocain (CCM) — Avance sur Recettes | MA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| COND-MD-national-centre-for-cinematography-moldova-ncfm | National Centre for Cinematography Moldova (NCFM) | MD | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity |
| COND-MO-macau-cultural-industries-fund-film-production-support | Macau Cultural Industries Fund Film Production Support | MO | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity |
| mt_mfc_rebate | Malta Film Commission Cash Rebate | MT | DISCRETIONARY | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; PRIMARY_AUTHORITY | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | Commissioner-discretionary uplift; provisional approval; local company/service coordinator; cultural test; audit |
| mu_edb_incentive | Mauritius Film Rebate Scheme | MU | DISCRETIONARY | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; PRIMARY_AUTHORITY | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | Film Rebate Committee assessment; CEO approval; local entity; preapproval; cultural/content and minimum-spend gates |
| COND-MX-imcine-instituto-mexicano-de-cinematograf-a-foprocine-fideci | IMCINE — Instituto Mexicano de Cinematografía — FOPROCINE / FIDECINE | MX | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| na_film_commission | Namibia Film Commission Production Incentive | NA | SELECTIVE | CURRENT | NON_GUARANTEED_SELECTIVE; no deterministic RateRule | NO | NO | NON-PRICEABLE | NO | agency selection; application; project-specific support decision |
| COND-NG-national-film-and-video-censors-board-creative-economy-incen | National Film and Video Censors Board / Creative Economy Incentive | NG | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award |
| COND-NL-hubert-bals-fund-iffr-development-and-production-fund | Hubert Bals Fund (IFFR) — Development and Production Fund | NL | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); cultural test |
| COND-NL-idfa-forum-international-documentary-co-financing-market | IDFA Forum — International Documentary Co-financing Market | NL | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC) |
| COND-NL-npo-vpro-dutch-public-broadcaster-co-production-fund | NPO / VPRO — Dutch Public Broadcaster Co-production Fund | NL | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| nl_film_production_incentive | Netherlands Film Production Incentive (NFPI) | NL | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | competitive rounds; limited envelope; preapproval; cultural/production qualification |
| COND-NO-nrk-norwegian-broadcasting-corporation-co-production-fund | NRK — Norwegian Broadcasting Corporation Co-production Fund | NO | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-NO-norwegian-film-institute-nfi-selective-production-grants | Norwegian Film Institute (NFI) — Selective Production Grants | NO | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| no_film_incentive | Norwegian Film Production Incentive | NO | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; PRIMARY_AUTHORITY | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | limited projects selected per round; fixed reimbursement envelope; preapproval |
| COND-NO-ROG-vestnorsk-filmsenter-western-norway-regional-film-centre | Vestnorsk Filmsenter — Western Norway Regional Film Centre | NO-ROG | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in NO-ROG; cultural test |
| COND-NO-TRO-nord-norsk-filmsenter-northern-norway-regional-film-centre | Nord Norsk Filmsenter — Northern Norway Regional Film Centre | NO-TRO | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in NO-TRO; cultural test |
| COND-NORDIC-nordisk-film-tv-fond | Nordisk Film & TV Fond | NORDIC | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | official co-production status; competitive/panel award; membership/eligible-country route; local entity; cultural test |
| COND-PE-peru-dafo-film-production-support | Peru DAFO Film Production Support | PE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; cultural test |
| ph_fdcp_flip | Philippines FDCP Film Location Incentive Program (FLIP) | PH | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | two annual award cycles; Notice/issuance before work; Philippine applicant/registry; cultural bonus; content approval |
| COND-PL-polish-film-institute-pisf-production-grant | Polish Film Institute (PISF) — Production Grant | PL | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| COND-PT-ica-instituto-do-cinema-e-audiovisual-international-co-produ | ICA — Instituto do Cinema e Audiovisual International Co-production Fund | PT | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | official co-production status; competitive/panel award; local entity; cultural test |
| COND-PT-ica-instituto-do-cinema-e-audiovisual-selective-production-g | ICA — Instituto do Cinema e Audiovisual Selective Production Grants | PT | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| qa_dfi_fund | Doha Film Institute — Grants for Filmmakers | QA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); cultural test |
| ru_film_incentive | Russian Cinema Fund (Fond Kino) Production Support | RU | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity |
| rw_film_incentive | Rwanda Development Board Film Production Support | RW | GRANT-FUND | CURRENT | NON_GUARANTEED_SELECTIVE; no deterministic RateRule | NO | NO | NON-PRICEABLE | NO | selective support/grant; local investment/approval requirements |
| sa_film_commission_rebate | Saudi Film Commission Production Rebate | SA | DISCRETIONARY | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; PRIMARY_AUTHORITY | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | discretionary award; Saudi entity/partner; preapproval; content/script clearance; minimum spend and shoot days |
| COND-SA-KSA-saudi-film-commission-production-grants-and-selective-suppor | Saudi Film Commission — Production Grants and Selective Support | SA-KSA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; spend/participation in SA-KSA; local entity; cultural test |
| COND-SE-g-teborg-film-festival-nordic-co-production-summit-grants | Göteborg Film Festival — Nordic Co-production Summit Grants | SE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC) |
| COND-SE-svt-swedish-television-co-production-fund | SVT — Swedish Television Co-production Fund | SE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | broadcaster commission/pre-buy/co-production; editorial selection; cultural test |
| COND-SE-AB-filmregion-stockholm-m-lardalen-regional-co-production-fund | Filmregion Stockholm-Mälardalen — Regional Co-production Fund | SE-AB | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | official co-production status; competitive/panel award; spend/participation in SE-AB; cultural test |
| COND-SE-SK-film-i-sk-ne-regional-co-production-fund-scania | Film i Skåne — Regional Co-production Fund (Scania) | SE-SK | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | official co-production status; competitive/panel award; spend/participation in SE-SK; cultural test |
| COND-SE-VG-film-i-v-st-regional-co-production-fund | Film i Väst — Regional Co-production Fund | SE-VG | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | official co-production status; competitive/panel award; spend/participation in SE-VG; cultural test |
| sg_made_with_singapore_rebate | Made-with-Singapore Cash Rebate | SG | DISCRETIONARY | CURRENT | AUTHORITY_UNRESOLVED_NON_PRICEABLE; STRUCTURED_PROVENANCE_PARTIAL_WITH_EXACT_AUTHORITY_RESIDUAL; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | IMDA discretion; Singapore company/partner; preapproval; market/finance/content criteria |
| sg_imda_film_fund | IMDA Singapore — Feature Film Production Grant | SG | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity; cultural test |
| singapore_imda_digital_media_development_fund | IMDA — Digital Media Content Programme (Animation/VFX) | SG | GRANT-FUND | CURRENT | NON_GUARANTEED_SELECTIVE; conditional catalog DISCOVERY; no deterministic RateRule | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | IMDA discretionary application; Singapore applicant/partner; animation/VFX content scope; award decision |
| tn_film_incentive | Tunisia CNCI Cash Rebate | TN | SELECTIVE | CURRENT | NON_GUARANTEED_SELECTIVE; no deterministic RateRule | NO | NO | NON-PRICEABLE | NO | annual selective support; Tunisian producer; panel/agency award |
| tr_film_incentive | Ministry of Culture and Tourism (KÜLTÜR) — Film Production Grants | TR | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL absent | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity; cultural test |
| COND-TW-taiwan-creative-content-agency-taicca-international-co-produ | Taiwan Creative Content Agency (TAICCA) International Co-production Fund | TW | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | official co-production status; competitive/panel award; local entity; cultural test |
| tw_bamid_rebate | Taiwan TFAI/BAMID Cash Rebate | TW | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | highly selective application; preapproval; Taiwan spend/minimum; origin and financing exclusions |
| COND-UA-ukrainian-state-film-agency-production-support | Ukrainian State Film Agency Production Support | UA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity |
| COND-US-itvs-international-documentary-fund | ITVS International Documentary Fund | US | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC) |
| COND-US-sundance-institute-documentary-fund | Sundance Institute — Documentary Fund | US | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC) |
| COND-US-tribeca-film-institute-documentary-and-narrative-development | Tribeca Film Institute — Documentary and Narrative Development Grants | US | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC) |
| us_ca_film_credit | California Film & Television Tax Credit Program 4.0 | US-CA | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; PRIMARY_AUTHORITY | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | competitive ranked allocation; application window; annual pool; preapproval |
| us_ky_keiia | Kentucky Entertainment Industry Incentive Act (KEIIA) | US-KY | DISCRETIONARY | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | agency/committee discretion; preapproval; annual appropriation exposure; unresolved uplift criteria |
| us_or_opif | Oregon Production Investment Fund (OPIF) | US-OR | DISCRETIONARY | CURRENT | UNPRICEABLE_AUTHORITY_INSUFFICIENT; STRUCTURED_PROVENANCE_COMPLETE; OFFICIAL_GUIDANCE | NO | NO | NON-PRICEABLE | NO | limited competitive fund; preapproval; annual cap; single project no more than 50% of fund |
| us_pa_film_production_credit | Pennsylvania Film Production Tax Credit | US-PA | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; PRIMARY_AUTHORITY | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | competitive annual-pool allocation; preapproval; project share limit; facility uplift facts |
| us_wa_motion_picture_competitiveness | Washington State Motion Picture Competitiveness Program | US-WA | SELECTIVE | CURRENT | STRUCTURED_PROVENANCE_COMPLETE; OFFICIAL_GUIDANCE | YES | YES | CONDITIONALLY MODELABLE | FORMULA SCENARIO (conditional award) | competitive oversubscribed fund; funding letter; annual pool; resident-key-person gate; preapproval |
| COND-VE-cnac-venezuela-film-production-fund | CNAC Venezuela Film Production Fund | VE | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | NO | competitive/discretionary application or panel award; local entity |
| za_dac_fund | Department of Arts and Culture (DAC) / NFVF Development Fund | ZA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | editorial/competitive award; development-phase scope (not production NPC); local entity; cultural test |
| COND-ZA-industrial-development-corporation-idc-film-and-television-i | Industrial Development Corporation (IDC) — Film and Television Investment Fund | ZA | GRANT-FUND | CURRENT | DISCOVERY catalog; source URL present | NO | NO | NON-PRICEABLE | CONDITIONAL ANNOTATION | competitive/discretionary application or panel award; local entity |

## 5. Programs represented in data but not current-optimizer-visible

There are **72** such identities: 61 conditional nodes cannot attach to any currently implemented profile/doctrine jurisdiction, 9 hard-blocked selective identities have no conditional-node duplicate, us_or_opif is hard-blocked for authority insufficiency, and NOHFC is connected only to the legacy scenario/stacking path.

| Slug / node ID | Program | Reason |
|---|---|---|
| COND-AM-national-cinema-centre-of-armenia-production-support | National Cinema Centre of Armenia Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-AO-angola-instituto-do-cinema-e-audiovisual-ica-production-supp | Angola Instituto do Cinema e Audiovisual (ICA) Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-AR-incaa-foprocine-development-and-production-grants | INCAA — Foprocine Development and Production Grants | conditional node has no currently reachable participant/membership attachment |
| COND-AU-NT-territory-screen-northern-territory-production-support | Territory Screen — Northern Territory Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-AU-TAS-screen-tasmania-production-support | Screen Tasmania — Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-AZ-azerbaijan-film-fund-production-support | Azerbaijan Film Fund Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-BE-BRU-screen-brussels-production-support | Screen.Brussels Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-BE-VLG-vaf-flanders-audiovisual-fund | VAF Flanders Audiovisual Fund | conditional node has no currently reachable participant/membership attachment |
| COND-BE-WAL-wallimage-co-production-fund | Wallimage Co-production Fund | conditional node has no currently reachable participant/membership attachment |
| COND-BF-fespaco-festival-pan-africain-du-cin-ma-et-de-la-t-l-vision- | FESPACO — Festival Pan-Africain du Cinéma et de la Télévision de Ouagadougou | conditional node has no currently reachable participant/membership attachment |
| COND-BR-ancine-fsa-fundo-setorial-do-audiovisual-development-fund | ANCINE — FSA (Fundo Setorial do Audiovisual) Development Fund | conditional node has no currently reachable participant/membership attachment |
| COND-CA-PE-film-pei-prince-edward-island-production-support | Film PEI — Prince Edward Island Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-CI-centre-national-de-cin-ma-de-c-te-d-ivoire-cnci-film-support | Centre National de Cinéma de Côte d'Ivoire (CNCI) Film Support | conditional node has no currently reachable participant/membership attachment |
| COND-CU-icaic-cuba-film-production-support | ICAIC Cuba Film Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-DE-BB-medienboard-berlin-brandenburg-mbb-film-production-fund | Medienboard Berlin-Brandenburg (MBB) — Film Production Fund | conditional node has no currently reachable participant/membership attachment |
| COND-DE-BW-mfg-medien-und-filmgesellschaft-baden-w-rttemberg | MFG Medien- und Filmgesellschaft Baden-Württemberg | conditional node has no currently reachable participant/membership attachment |
| COND-DE-BY-filmfernsehfonds-bayern-fff-bayern | FilmFernsehFonds Bayern (FFF Bayern) | conditional node has no currently reachable participant/membership attachment |
| COND-DE-HH-film-und-medienstiftung-hamburg-schleswig-holstein | Film- und Medienstiftung Hamburg Schleswig-Holstein | conditional node has no currently reachable participant/membership attachment |
| COND-DE-MDM-mitteldeutsche-medienf-rderung-mdm-film-production-fund | Mitteldeutsche Medienförderung (MDM) — Film Production Fund | conditional node has no currently reachable participant/membership attachment |
| COND-DE-NI-nordmedia-film-und-mediengesellschaft | nordmedia Film und Mediengesellschaft | conditional node has no currently reachable participant/membership attachment |
| COND-DE-NW-film-und-medienstiftung-nrw | Film und Medienstiftung NRW | conditional node has no currently reachable participant/membership attachment |
| COND-DK-CPH-copenhagen-film-fund-regional-co-production-support | Copenhagen Film Fund — Regional Co-production Support | conditional node has no currently reachable participant/membership attachment |
| COND-DZ-centre-alg-rien-pour-le-d-veloppement-du-cin-ma-cadc-film-su | Centre Algérien pour le Développement du Cinéma (CADC) Film Support | conditional node has no currently reachable participant/membership attachment |
| COND-ES-AND-andalucia-film-commission-audiovisual-production-incentive | Andalucia Film Commission — Audiovisual Production Incentive | conditional node has no currently reachable participant/membership attachment |
| COND-ES-CAT-icec-institut-catal-de-les-empreses-culturals-film-support | ICEC — Institut Català de les Empreses Culturals Film Support | conditional node has no currently reachable participant/membership attachment |
| COND-ES-EUS-basque-audiovisual-eusko-jaurlaritza-film-production-support | Basque Audiovisual — Eusko Jaurlaritza Film Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-ES-GAL-agadic-axencia-galega-das-industrias-culturais-film-producti | Agadic — Axencia Galega das Industrias Culturais Film Production Fund | conditional node has no currently reachable participant/membership attachment |
| COND-ES-VAL-institut-valenci-de-cultura-ivc-audiovisual-production-fund | Institut Valencià de Cultura (IVC) — Audiovisual Production Fund | conditional node has no currently reachable participant/membership attachment |
| COND-EU-creative-europe-media-programme | Creative Europe MEDIA Programme | conditional node has no currently reachable participant/membership attachment |
| COND-EU-torino-film-lab-international-development-and-production-gra | Torino Film Lab — International Development and Production Grants | conditional node has no currently reachable participant/membership attachment |
| COND-FR-ARA-auvergne-rh-ne-alpes-cinema-regional-aid | Auvergne-Rhône-Alpes Cinema Regional Aid | conditional node has no currently reachable participant/membership attachment |
| COND-FR-IDF-le-de-france-cinema-regional-aid | Île-de-France Cinema Regional Aid | conditional node has no currently reachable participant/membership attachment |
| COND-FR-NAQ-nouvelle-aquitaine-regional-cinema-aid | Nouvelle-Aquitaine Regional Cinema Aid | conditional node has no currently reachable participant/membership attachment |
| COND-FR-OCC-occitanie-cinema-regional-aid | Occitanie Cinema Regional Aid | conditional node has no currently reachable participant/membership attachment |
| COND-GB-LON-film-london-production-finance-market-and-support | Film London — Production Finance Market and Support | conditional node has no currently reachable participant/membership attachment |
| COND-GB-NIR-northern-ireland-screen-production-fund | Northern Ireland Screen — Production Fund | conditional node has no currently reachable participant/membership attachment |
| COND-GB-YRK-screen-yorkshire-yorkshire-content-fund | Screen Yorkshire — Yorkshire Content Fund | conditional node has no currently reachable participant/membership attachment |
| COND-IR-farabi-cinema-foundation-film-production-support | Farabi Cinema Foundation Film Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-IT-APU-apulia-film-commission-film-fund | Apulia Film Commission — Film Fund | conditional node has no currently reachable participant/membership attachment |
| COND-IT-CAM-film-commission-campania-production-fund | Film Commission Campania — Production Fund | conditional node has no currently reachable participant/membership attachment |
| COND-IT-LAZ-lazio-cinema-international-film-fund | Lazio Cinema International — Film Fund | conditional node has no currently reachable participant/membership attachment |
| COND-IT-PIE-film-commission-torino-piemonte-production-support | Film Commission Torino Piemonte — Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-IT-SIC-sicilia-film-commission-film-fund | Sicilia Film Commission — Film Fund | conditional node has no currently reachable participant/membership attachment |
| COND-IT-TOS-film-commission-toscana-production-support | Film Commission Toscana — Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-LB-centre-du-cin-ma-libanais-ccl-production-support | Centre du Cinéma Libanais (CCL) Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-MD-national-centre-for-cinematography-moldova-ncfm | National Centre for Cinematography Moldova (NCFM) | conditional node has no currently reachable participant/membership attachment |
| COND-MO-macau-cultural-industries-fund-film-production-support | Macau Cultural Industries Fund Film Production Support | conditional node has no currently reachable participant/membership attachment |
| COND-NG-national-film-and-video-censors-board-creative-economy-incen | National Film and Video Censors Board / Creative Economy Incentive | conditional node has no currently reachable participant/membership attachment |
| COND-NO-ROG-vestnorsk-filmsenter-western-norway-regional-film-centre | Vestnorsk Filmsenter — Western Norway Regional Film Centre | conditional node has no currently reachable participant/membership attachment |
| COND-NO-TRO-nord-norsk-filmsenter-northern-norway-regional-film-centre | Nord Norsk Filmsenter — Northern Norway Regional Film Centre | conditional node has no currently reachable participant/membership attachment |
| COND-NORDIC-nordisk-film-tv-fond | Nordisk Film & TV Fond | conditional node has no currently reachable participant/membership attachment |
| COND-SA-KSA-saudi-film-commission-production-grants-and-selective-suppor | Saudi Film Commission — Production Grants and Selective Support | conditional node has no currently reachable participant/membership attachment |
| COND-SE-AB-filmregion-stockholm-m-lardalen-regional-co-production-fund | Filmregion Stockholm-Mälardalen — Regional Co-production Fund | conditional node has no currently reachable participant/membership attachment |
| COND-SE-SK-film-i-sk-ne-regional-co-production-fund-scania | Film i Skåne — Regional Co-production Fund (Scania) | conditional node has no currently reachable participant/membership attachment |
| COND-SE-VG-film-i-v-st-regional-co-production-fund | Film i Väst — Regional Co-production Fund | conditional node has no currently reachable participant/membership attachment |
| COND-VE-cnac-venezuela-film-production-fund | CNAC Venezuela Film Production Fund | conditional node has no currently reachable participant/membership attachment |
| acpfilms_fund | ACP Films — EU-ACP Cultural Film Co-production Fund | conditional node has no currently reachable participant/membership attachment |
| au_qld_screen_qld | Screen Queensland Production Attraction Strategy | authority/disposition hard-block prevents candidacy and no conditional attachment exists |
| bt_film_incentive | Bhutan Film Commission / Tourism Council Production Facilitation | authority/disposition hard-block prevents candidacy and no conditional attachment exists |
| cm_film_incentive | Cameroon Centre National de la Cinématographie (CNC-Cameroon) | conditional node has no currently reachable participant/membership attachment |
| hk_film_dev_fund | Hong Kong Film Development Fund (FDF) | conditional node has no currently reachable participant/membership attachment |
| il_film_incentive | Israel Film Fund / Maslool Incentive | authority/disposition hard-block prevents candidacy and no conditional attachment exists |
| jp_vipo_location_incentive | Japan Film Commission Location Incentive (JLOC) | authority/disposition hard-block prevents candidacy and no conditional attachment exists |
| kr_kofic_location_incentive | Korea Film Council (KOFIC) Location Incentive | authority/disposition hard-block prevents candidacy and no conditional attachment exists |
| na_film_commission | Namibia Film Commission Production Incentive | authority/disposition hard-block prevents candidacy and no conditional attachment exists |
| proposed_united_kingdom_uk_global_screen_fund_international_co_production | UK Global Screen Fund — International Co-production | authority/disposition hard-block prevents candidacy and no conditional attachment exists |
| ru_film_incentive | Russian Cinema Fund (Fond Kino) Production Support | conditional node has no currently reachable participant/membership attachment |
| rw_film_incentive | Rwanda Development Board Film Production Support | authority/disposition hard-block prevents candidacy and no conditional attachment exists |
| tn_film_incentive | Tunisia CNCI Cash Rebate | authority/disposition hard-block prevents candidacy and no conditional attachment exists |
| tr_film_incentive | Ministry of Culture and Tourism (KÜLTÜR) — Film Production Grants | conditional node has no currently reachable participant/membership attachment |
| us_or_opif | Oregon Production Investment Fund (OPIF) | UNPRICEABLE_AUTHORITY_INSUFFICIENT hard block |
| nohfc_production_fund | Northern Ontario Heritage Fund — Production Fund | legacy generator/stacking fixtures only; absent from current canonical production discovery |

## 6. Optimizer-visible classifications requiring correction

| Program | Current classification/path | Why incorrect or incomplete |
|---|---|---|
| COND-CH-media-desk-switzerland-succ-s-cin-ma-automatic-support | conditional direct_grant / competitive-discretionary | The record itself says Automatic Support; excluded from the 160 total. |
| sa_film_commission_rebate | flat 60% deterministic RateRule plus discretionary warning | Requirements say discretionary/preapproved and retained authority says up to 60%; current deterministic award treatment overstates certainty. |
| ph_fdcp_flip | priceable formula; allocation_type=None | Requirements say two annual evaluation/announcement cycles and grant issuance before work; selection status is not structurally encoded. |
| nohfc_production_fund | legacy fixed USD 500,000 grant scenarios | A discretionary grant cannot use the illustrative cap as a guaranteed award without a project-specific award fact. |
| be_tax_shelter | discretionary_band | Its own condition says the 42–44% range is deal-cost economics, not a discretionary approval band. |
| fr_trip | discretionary_band | Its own condition says the 40% tier is an objective VFX-spend threshold, not a discretionary approval band. |
| jo_rfc_rebate | discretionary_band plus competitive profile | Its tier is an objective points assessment, not authority discretion over the base; selection and rate qualification are separate gates. |
| se_production_rebate | discretionary_band described as both competitive and first-come | Current requirements classify allocation first-come-first-served; the two labels conflict. |
| COND-GB-bfi-international-export-development-and-distribution-suppor | conditional production direct_grant | Export/distribution scope is routed as a production funding opportunity. |
| COND-FR-unifrance-international-distribution-and-promotion-support | conditional production direct_grant | Distribution/promotion scope is routed as a production funding opportunity. |
| COND-DE-german-films-international-export-and-market-promotion | conditional production direct_grant | Export/market-promotion scope is routed as a production funding opportunity. |
| COND-IT-anica-mic-italian-film-international-distribution-support | conditional production direct_grant | Distribution scope is routed as a production funding opportunity. |

Other factual uplifts under the overloaded discretionary_band condition kind were not counted as discretionary programs unless a separate allocation/selection record proved non-formulaic award behavior.

## 7. Historical 23 SELECTIVE_OR_DISCRETIONARY comparison

The historical **23** was one disposition count inside a 224-identity authority-recovery cohort, not a global grant/fund inventory. The current 160 total is broader by design.

| Reconciliation step | Delta | Running count |
|---|---:|---:|
| Historical authority-disposition cohort | — | 23 |
| Remove IBERMEDIA_MEMBERSHIP_AND_FRAMEWORK (framework, not a monetary program) | -1 | 22 |
| Add au_qld_screen_qld, now present as a real selective Screen Queensland strategy | +1 | 23 |
| Japan and Korea canonical/runtime alias rows | 0 | 23 |
| Jordan and Philippines moved out of the hard-blocked selective disposition but remain non-formulaic here because current requirements evidence competition/award cycles | 0 | 23 |
| Add 120 qualifying, deduplicated conditional grant/fund identities not already represented by those historical real programs | +120 | 143 |
| Add NOHFC, represented in catalog/legacy economics but absent from that cohort | +1 | 144 |
| Add 16 other current allocation/award identities outside the historical cohort | +16 | **160** |

Thus the exact delta is **+137**, fully explained as **+120 deduplicated conditional-library identities +1 NOHFC +16 other current allocation/award identities**, after the historical cohort’s one-for-one framework removal and Screen Queensland addition.

## 8. Canonical ownership and conclusion

- Identity/rate: executable doctrine and RateRules; allocation/eligibility: requirements profiles; candidacy exclusions: authority coverage registry; grant/fund visibility: conditional-program index; serving: canonical evaluation/production view.
- The library has two distinct non-formulaic paths: non-priceable conditional annotations and formula scenarios with conditional selection warnings. It lacks one normalized program-type field spanning both.
- The exact current inventory is **160**. This is not a claim that 160 programs are authority-verified, production-applicable, stackable, or awardable to any particular project.
