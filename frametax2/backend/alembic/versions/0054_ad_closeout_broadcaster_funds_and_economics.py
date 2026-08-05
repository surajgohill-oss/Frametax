"""0054 — Phase A-D closeout: broadcaster fund programs and fund economics completion.

Populates:
  - incentive_programs + fund_economics rows for broadcaster funds
    (BBC Films, Film4, ZDF, Arte, WDR/ARD, Canal+, SVT, NRK, DR, YLE, RTÉ, RAI Cinema, RTVE, ORF, NPO/VPRO)
  - Additional national film institutes (ÖFI Austria, PISF Poland, Czech Film Fund,
    NFI Hungary, ICA Portugal)
  - fund_economics rows for tax credits and cash rebates that had no fund_economics
    (uk_avec, ie_section_481, ca_federal_cptc, ca_bc_pstc, on_ofttc, on_opstc,
    qc_film_production, ca_qc_qprdp, fr_trip, it_tax_credit_foreign, au_location_offset,
    gr_cash_rebate, hr_cash_rebate, bg_cash_rebate, mt_mfc_rebate, mu_edb_incentive,
    au_sa_safc, ca_bell_fund, ca_nsi_fund, de_berlinale_wcf, fi_ses_grants, no_nfi_grants,
    de_dfff, gb_creative_england, film_i_vast, Spanish/Italian regionals)
  - fund_economics rows for broadcaster fund programs

Revision ID: 0054
Revises: 0053
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0054"
down_revision: Union[str, None] = "0053"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Broadcaster fund programs to insert
# ---------------------------------------------------------------------------

_BROADCASTER_PROGRAMS: list[dict] = [
    # UK
    {
        "jurisdiction_fragment": "United Kingdom",
        "program_name": "BBC Films — Co-production and Development Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "BBC Films co-investment. Not government assistance for AVEC. UNKNOWN: per-project cap.",
    },
    {
        "jurisdiction_fragment": "United Kingdom",
        "program_name": "Channel 4 Film / Film4 — Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "Film4/C4 co-investment. Not government assistance for AVEC. UNKNOWN: per-project cap.",
    },
    # Germany
    {
        "jurisdiction_fragment": "Germany",
        "program_name": "ZDF / Das Kleine Fernsehspiel — Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "ZDF broadcaster co-production. Not government assistance for DFFF. UNKNOWN: per-project cap.",
    },
    {
        "jurisdiction_fragment": "Germany",
        "program_name": "WDR / ARD — Film and Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "WDR/ARD broadcaster co-production. Not government assistance for DFFF. UNKNOWN: per-project cap.",
    },
    # France / Franco-German
    {
        "jurisdiction_fragment": "France",
        "program_name": "Arte France Cinéma — Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "Arte (FR/DE broadcaster) co-production. Not government assistance for CNC or DFFF. UNKNOWN: per-project cap.",
    },
    {
        "jurisdiction_fragment": "France",
        "program_name": "CANAL+ — Obligation de Contribution à la Production Française",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "CANAL+ mandatory investment in French film. Not government assistance for CNC tax credit. UNKNOWN: per-project cap.",
    },
    # Scandinavia
    {
        "jurisdiction_fragment": "Sweden",
        "program_name": "SVT — Swedish Television Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "SVT broadcaster co-production. Not government assistance for Swedish Film Institute. UNKNOWN: per-project cap.",
    },
    {
        "jurisdiction_fragment": "Norway",
        "program_name": "NRK — Norwegian Broadcasting Corporation Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "NRK broadcaster co-production. Not government assistance for NFI grants. UNKNOWN: per-project cap.",
    },
    {
        "jurisdiction_fragment": "Denmark",
        "program_name": "DR — Danish Broadcasting Corporation Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "DR broadcaster co-production. Not government assistance for DFI. UNKNOWN: per-project cap.",
    },
    {
        "jurisdiction_fragment": "Finland",
        "program_name": "YLE — Finnish Broadcasting Company Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "YLE broadcaster co-production. Not government assistance for SES grants. UNKNOWN: per-project cap.",
    },
    # Ireland
    {
        "jurisdiction_fragment": "Ireland",
        "program_name": "RTÉ — Broadcasting Authority of Ireland Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "RTÉ broadcaster co-production. Not government assistance for Section 481. UNKNOWN: per-project cap.",
    },
    # Italy
    {
        "jurisdiction_fragment": "Italy",
        "program_name": "RAI Cinema — Co-production and Acquisition Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "RAI Cinema broadcaster investment obligation. Not government assistance for MiC tax credit. UNKNOWN: per-project cap.",
    },
    # Spain
    {
        "jurisdiction_fragment": "Spain",
        "program_name": "RTVE — Radio Televisión Española Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "RTVE broadcaster investment obligation. Not government assistance for ICAA deduction. UNKNOWN: per-project cap.",
    },
    # Austria
    {
        "jurisdiction_fragment": "Austria",
        "program_name": "ORF Film/Fernseh-Abkommen — Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "ORF Film/TV Agreement co-investment. Not government assistance for ÖFI. UNKNOWN: per-project cap.",
    },
    {
        "jurisdiction_fragment": "Austria",
        "program_name": "Austrian Film Institute (ÖFI) — Production Support",
        "program_type": "direct_grant",
        "base_rate": None,
        "notes": "ÖFI selective production grants. Eurimages member. UNKNOWN: current maximum grant.",
    },
    # Netherlands
    {
        "jurisdiction_fragment": "Netherlands",
        "program_name": "NPO / VPRO — Dutch Public Broadcaster Co-production Fund",
        "program_type": "broadcaster_fund",
        "base_rate": None,
        "notes": "NPO/VPRO broadcaster co-production. Not government assistance for Netherlands Film Fund. UNKNOWN: per-project cap.",
    },
    # Additional national institutes
    {
        "jurisdiction_fragment": "Poland",
        "program_name": "Polish Film Institute (PISF) — Production Grant",
        "program_type": "direct_grant",
        "base_rate": None,
        "notes": "PISF selective production grants up to PLN 5M. Eurimages member. UNKNOWN: USD-equivalent maximum.",
    },
    {
        "jurisdiction_fragment": "Czech Republic",
        "program_name": "Czech Film Fund — Production Support",
        "program_type": "direct_grant",
        "base_rate": None,
        "notes": "Czech Film Fund selective grants. Eurimages member. Also administers Czech cash rebate. UNKNOWN: current maximum.",
    },
    {
        "jurisdiction_fragment": "Hungary",
        "program_name": "National Film Institute (NFI Hungary) — Production Grant",
        "program_type": "direct_grant",
        "base_rate": None,
        "notes": "NFI Hungary selective grants. Hungary also has 30% cash rebate for foreign productions. UNKNOWN: current maximum.",
    },
    {
        "jurisdiction_fragment": "Portugal",
        "program_name": "ICA — Instituto do Cinema e Audiovisual — Production Grants",
        "program_type": "direct_grant",
        "base_rate": None,
        "notes": "ICA selective and automatic grants. Eurimages and Ibermedia member. UNKNOWN: current maximum.",
    },
    {
        "jurisdiction_fragment": "Switzerland",
        "program_name": "MEDIA Desk Switzerland / Succès Cinéma — Automatic Support",
        "program_type": "direct_grant",
        "base_rate": None,
        "notes": "BAK/Succès Cinéma Swiss automatic + selective grants. UNKNOWN: base rate, per-project cap.",
    },
]


# ---------------------------------------------------------------------------
# Fund economics entries for programs that lacked them
# (keyed by program_name fragment → economics data)
# ---------------------------------------------------------------------------

_ECON_BY_NAME_FRAGMENT: list[tuple[str, dict]] = [
    # UK
    ("audio visual expenditure", {
        "classification": "tax_credit",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "AVEC 34% film / 39% HETV. Not government assistance for other funds.",
    }),
    ("section 481", {
        "classification": "tax_credit",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 7_000_000,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Section 481: 32% of qualifying Irish expenditure. Max €70M qualifying spend.",
    }),
    ("canada production tax credit", {
        "classification": "tax_credit",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "CPTC: 25% of QCLE net of government assistance. Canadian content (CAVCO) required.",
    }),
    ("bc production services", {
        "classification": "tax_credit",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "BC PSTC: 28% of qualifying BC labour for foreign service productions. Mutually exclusive with CPTC.",
    }),
    ("ontario film and television", {
        "classification": "tax_credit",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "OFTTC: 35% of qualifying Ontario labour. Government assistance reduces qualifying basis.",
    }),
    ("ontario production services", {
        "classification": "tax_credit",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "OPSTC: 21.5% of qualifying Ontario expenditure for foreign service productions.",
    }),
    ("film and television production tax credit", {
        "classification": "tax_credit",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Quebec SODEC: 28-36% of qualifying Quebec labour. Government assistance reduces basis.",
    }),
    ("quebec production tax credit — foreign", {
        "classification": "tax_credit",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Quebec QPRDP: 20-28% of qualifying Quebec labour for foreign/treaty productions.",
    }),
    ("tax rebate for international", {
        "classification": "rebate",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 3_000_000,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "TRIP: 30% of qualifying French spend for foreign productions. Cap €30M credit.",
    }),
    ("italian tax credit for foreign", {
        "classification": "rebate",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 6_000_000,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "MiC Italian Tax Credit for Foreign Productions: 40% of qualifying spend. Max €20M credit.",
    }),
    ("location offset", {
        "classification": "rebate",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "AU Location Offset: 16.5% of QAPE. Government assistance reduces QAPE. Mutually exclusive with Producer Offset.",
    }),
    ("south australian film corporation", {
        "classification": "rebate",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": True,
        "notes": "SAFC: government financial assistance reducing QAPE for Location/Producer Offsets.",
    }),
    ("greece cash rebate", {
        "classification": "rebate",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Greece Cash Rebate: 40% of qualifying Greek spend. Does not reduce Eurimages qualifying spend.",
    }),
    ("croatia film cash rebate", {
        "classification": "rebate",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Croatia Cash Rebate: up to 25% of qualifying Croatian spend (HAVC). Does not reduce Eurimages spend.",
    }),
    ("bulgarian film industry", {
        "classification": "rebate",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Bulgaria Film Cash Rebate: 25% of qualifying Bulgarian spend. Does not reduce Eurimages spend.",
    }),
    ("malta film commission cash rebate", {
        "classification": "rebate",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Malta Film Commission Cash Rebate: 40% of qualifying spend + up to 5% digital media bonus.",
    }),
    ("mauritius edb", {
        "classification": "rebate",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Mauritius EDB Film Rebate: up to 40% of qualifying spend.",
    }),
    ("bell fund", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 500_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": True,
        "notes": "Bell Fund: government assistance (ITA §125.4). Reduces CPTC/OFTTC qualifying labour.",
    }),
    ("national screen institute", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 75_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": True,
        "notes": "NSI grants: government assistance (ITA §125.4). Reduces CPTC qualifying labour.",
    }),
    ("berlinale world cinema fund", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 220_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Berlinale WCF: €10k-€200k non-repayable grants. Not government assistance for DFFF.",
    }),
    ("finnish film foundation", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "SES selective grants up to €750k. Combines with Eurimages, YLE, Nordic Fund.",
    }),
    ("norwegian film institute", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "NFI selective grants up to NOK 8M. Also administers Norwegian 25% cash rebate. Not govt assistance for Eurimages.",
    }),
    ("german federal film fund", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 6_500_000,
        "is_competitive": False,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "DFFF/GFFF: automatic 25% of qualifying German spend. Max €25M per project. Stackable with all German regional funds.",
    }),
    ("creative england", {
        "classification": "equity",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 550_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Creative England: recoupable equity co-financing. Not government assistance for AVEC.",
    }),
    ("film i väst", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Film i Väst: repayable advances. Major European co-production hub. Subordinated recoupment.",
    }),
    ("lazio cinema", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 220_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Lazio Cinema International: regional grants. Stackable with MiC tax credit.",
    }),
    ("sicilia film", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 165_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Sicilia Film Commission: regional grants. Stackable with MiC tax credit.",
    }),
    ("film commission campania", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 165_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Campania Film Commission: regional grants. Stackable with MiC tax credit.",
    }),
    ("film commission toscana", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 165_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Film Commission Toscana: regional grants. Stackable with MiC tax credit.",
    }),
    ("film commission torino piemonte", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 165_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Film Commission Torino Piemonte: regional grants. Stackable with MiC tax credit.",
    }),
    ("apulia film", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 165_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Apulia Film Commission Film Fund: regional grants. Stackable with MiC tax credit.",
    }),
    ("icec", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 275_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "ICEC Catalonia: grants. Stackable with ICAA national deduction.",
    }),
    ("andalucia film commission", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 165_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Andalusia Film Commission: grants. Stackable with ICAA national deduction.",
    }),
    ("agadic", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 165_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "AGADIC Galicia: grants. Stackable with ICAA national deduction.",
    }),
    ("institut valencià", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 165_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "IVC Valencia: grants. Stackable with ICAA national deduction.",
    }),
    ("basque audiovisual", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 275_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Basque Audiovisual (Eusko Jaurlaritza): grants. Stackable with ICAA national deduction.",
    }),
    ("california film", {
        "classification": "tax_credit",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "CA Film & TV Tax Credit 3.0: 20-25% of qualifying CA expenditure. Transferable. Competitive allocation.",
    }),
    # Broadcaster funds economics
    ("bbc films", {
        "classification": "equity",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 3_850_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "BBC Films: co-financing equity; not government assistance for AVEC.",
    }),
    ("channel 4 film", {
        "classification": "equity",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 2_750_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Film4/Channel 4: co-financing equity; not government assistance for AVEC.",
    }),
    ("zdf", {
        "classification": "equity",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 550_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "ZDF co-production: does not reduce DFFF qualifying spend.",
    }),
    ("wdr / ard", {
        "classification": "equity",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_100_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "WDR/ARD co-production: does not reduce DFFF qualifying spend.",
    }),
    ("arte france", {
        "classification": "equity",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Arte (FR/DE broadcaster): does not reduce DFFF or CNC qualifying spend.",
    }),
    ("canal+", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": None,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "CANAL+ pre-purchase/MG against TV rights. Does not reduce CNC tax credit.",
    }),
    ("svt — swedish", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_650_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "SVT: broadcaster commission; does not reduce Swedish Film Institute qualifying spend.",
    }),
    ("nrk — norwegian", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_100_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "NRK: broadcaster commission; does not reduce NFI qualifying spend.",
    }),
    ("dr — danish", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_100_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "DR: broadcaster commission; does not reduce DFI qualifying spend.",
    }),
    ("yle — finnish", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 550_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "YLE: broadcaster commission; does not reduce SES qualifying spend.",
    }),
    ("rtÉ", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 550_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "RTÉ: broadcaster commission; does not reduce Section 481 qualifying spend.",
    }),
    ("rai cinema", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 2_200_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "RAI Cinema: broadcaster obligation; does not reduce MiC tax credit.",
    }),
    ("rtve", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_650_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "RTVE: broadcaster obligation; does not reduce ICAA deduction.",
    }),
    ("orf film", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "ORF Film/Fernseh-Abkommen: broadcaster co-investment; does not reduce ÖFI qualifying spend.",
    }),
    ("npo / vpro", {
        "classification": "advance",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 660_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "NPO/VPRO: broadcaster co-production; does not reduce Netherlands Film Fund qualifying spend.",
    }),
    ("austrian film institute", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_100_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "ÖFI selective grants. Not government assistance for Eurimages. Eurimages member.",
    }),
    ("polski instytut", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_100_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "PISF selective grants. Eurimages member. Not govt assistance for EU funds.",
    }),
    ("czech film fund", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_100_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Czech Film Fund selective grants. Eurimages member. Also administers Czech cash rebate.",
    }),
    ("national film institute (nfi hungary)", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_100_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "NFI Hungary selective grants. Hungary also has 30% cash rebate for foreign productions.",
    }),
    ("instituto do cinema", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 550_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "ICA Portugal: selective and automatic grants. Eurimages and Ibermedia member.",
    }),
    ("succès cinéma", {
        "classification": "grant",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 500_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "is_government_assistance": False,
        "notes": "Swiss BAK / Succès Cinéma: automatic + selective grants. Eurimages member.",
    }),
]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Insert broadcaster/additional fund programs
    for prog in _BROADCASTER_PROGRAMS:
        # Find jurisdiction by name fragment
        jur_row = conn.execute(
            sa.text(
                "SELECT id FROM jurisdictions WHERE LOWER(name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{prog['jurisdiction_fragment'].lower()}%"},
        ).fetchone()
        if not jur_row:
            continue
        jur_id = jur_row[0]

        # Insert program (idempotent on name)
        existing = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs WHERE jurisdiction_id = :jid AND "
                "LOWER(name) = :name LIMIT 1"
            ),
            {"jid": jur_id, "name": prog["program_name"].lower()},
        ).fetchone()
        if existing:
            prog_id = existing[0]
        else:
            slug = prog["program_name"].lower().replace(" ", "_").replace("-", "_").replace("'", "").replace("—", "_")
            result = conn.execute(
                sa.text(
                    """
                    INSERT INTO incentive_programs
                        (id, jurisdiction_id, name, slug, program_type, credit_basis,
                         base_rate, notes, confidence_tier, created_at, updated_at)
                    VALUES
                        (gen_random_uuid(), :jid, :name, :slug, :ptype, 'qualifying_spend',
                         :base_rate, :notes, 'DISCOVERY', now(), now())
                    RETURNING id
                    """
                ),
                {
                    "jid": jur_id,
                    "name": prog["program_name"],
                    "slug": slug,
                    "ptype": prog["program_type"],
                    "base_rate": prog.get("base_rate"),
                    "notes": prog.get("notes"),
                },
            )
            prog_id = result.fetchone()[0]

        # Insert fund_economics skeleton
        econ_existing = conn.execute(
            sa.text("SELECT 1 FROM fund_economics WHERE program_id = :pid"),
            {"pid": prog_id},
        ).fetchone()
        if not econ_existing:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO fund_economics
                        (program_id, is_repayable, is_recoupable, has_equity_participation,
                         stackable_with_incentives, is_competitive, notes)
                    VALUES
                        (:pid, FALSE, FALSE, FALSE, TRUE, TRUE, :notes)
                    ON CONFLICT (program_id) DO NOTHING
                    """
                ),
                {"pid": prog_id, "notes": prog.get("notes")},
            )

    # 2. Update/insert fund_economics for existing programs by name fragment
    for frag, econ in _ECON_BY_NAME_FRAGMENT:
        prog_row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs WHERE LOWER(name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{frag.lower()}%"},
        ).fetchone()
        if not prog_row:
            continue
        prog_id = prog_row[0]

        existing_econ = conn.execute(
            sa.text("SELECT 1 FROM fund_economics WHERE program_id = :pid"),
            {"pid": prog_id},
        ).fetchone()

        if existing_econ:
            conn.execute(
                sa.text(
                    """
                    UPDATE fund_economics SET
                        is_repayable = :is_repayable,
                        is_recoupable = :is_recoupable,
                        has_equity_participation = :has_equity_participation,
                        typical_max_award_usd = :typical_max_award_usd,
                        is_competitive = :is_competitive,
                        stackable_with_incentives = :stackable_with_incentives,
                        notes = :notes
                    WHERE program_id = :pid
                    """
                ),
                {
                    "pid": prog_id,
                    "is_repayable": econ.get("is_repayable", False),
                    "is_recoupable": econ.get("is_recoupable", False),
                    "has_equity_participation": econ.get("has_equity_participation", False),
                    "typical_max_award_usd": econ.get("typical_max_award_usd"),
                    "is_competitive": econ.get("is_competitive", False),
                    "stackable_with_incentives": econ.get("stackable_with_incentives", True),
                    "notes": econ.get("notes"),
                },
            )
        else:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO fund_economics (
                        program_id, is_repayable, is_recoupable, has_equity_participation,
                        typical_max_award_usd, is_competitive, stackable_with_incentives, notes
                    ) VALUES (
                        :pid, :is_repayable, :is_recoupable, :has_equity_participation,
                        :typical_max_award_usd, :is_competitive, :stackable_with_incentives, :notes
                    )
                    ON CONFLICT (program_id) DO UPDATE SET notes = EXCLUDED.notes
                    """
                ),
                {
                    "pid": prog_id,
                    "is_repayable": econ.get("is_repayable", False),
                    "is_recoupable": econ.get("is_recoupable", False),
                    "has_equity_participation": econ.get("has_equity_participation", False),
                    "typical_max_award_usd": econ.get("typical_max_award_usd"),
                    "is_competitive": econ.get("is_competitive", False),
                    "stackable_with_incentives": econ.get("stackable_with_incentives", True),
                    "notes": econ.get("notes"),
                },
            )


def downgrade() -> None:
    conn = op.get_bind()
    # Remove inserted broadcaster programs
    for prog in _BROADCASTER_PROGRAMS:
        conn.execute(
            sa.text(
                "DELETE FROM incentive_programs WHERE LOWER(name) = :name"
            ),
            {"name": prog["program_name"].lower()},
        )
