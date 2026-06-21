"""
global_inventory_grants2.py

Wave-3 grant/fund GlobalProgramEntry records: 10 additional grants and funds
covering IBERMEDIA (Ibero-America), German regional funds (Bayern, NRW),
Hong Kong Film Development Fund, NFDC India, IMDA Singapore, TAICCA Taiwan,
Film i Väst (Sweden), ACP Films (EU-ACP), and ITVS (US documentary).

All entries are DISCOVERY tier.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

_DISC = "DISCOVERY"


GRANTS2_PROGRAMS: list[GlobalProgramEntry] = [

    GlobalProgramEntry(
        jurisdiction_code="IBERO",
        jurisdiction_name="Ibero-American Region (SEGIB)",
        program_name="IBERMEDIA Programme for Ibero-American Co-productions",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=150_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="IBERMEDIA Programme — Ibero-American Audiovisual Co-production Fund",
        source_url="https://programaibermedia.com/",
        effective_from="1997-01-01",
        notes=(
            "IBERMEDIA supports co-production, development, and distribution of Ibero-American audiovisual works. "
            "~16 member countries: Spain, Portugal, and Latin American nations. "
            "Grants up to EUR 150,000 per development project; higher for production co-financing. "
            "Data gaps: confirmed current grant amounts, eligibility thresholds, member country list."
        ),
        unknown_fields=["current_amounts", "eligibility_thresholds", "member_country_list"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DE-BY",
        jurisdiction_name="Germany — Bavaria",
        program_name="FilmFernsehFonds Bayern (FFF Bayern)",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="FilmFernsehFonds Bayern (FFF Bayern) — Regional Film Fund",
        source_url="https://www.fff-bayern.de/",
        effective_from="1996-01-01",
        notes=(
            "FFF Bayern is Germany's largest regional film fund (~EUR 52M/year). "
            "Supports feature films, TV, documentaries with a Bavaria location/spend requirement. "
            "Cultural or regional connection required. Selective application process. "
            "Data gaps: confirmed grant amounts, spending obligation percentage, processing timeline."
        ),
        unknown_fields=["grant_amounts", "spending_obligation", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DE-NW",
        jurisdiction_name="Germany — North Rhine-Westphalia",
        program_name="Film und Medienstiftung NRW",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Film und Medienstiftung NRW — North Rhine-Westphalia Film Fund",
        source_url="https://www.filmstiftung.de/",
        effective_from="1991-01-01",
        notes=(
            "Film und Medienstiftung NRW is one of Germany's major regional film funds (~EUR 40M/year). "
            "Supports feature, TV, documentary, and new media with NRW spending commitment. "
            "International co-productions eligible; cultural connection required. "
            "Data gaps: confirmed grant amounts, spending obligation percentage, current guidelines."
        ),
        unknown_fields=["grant_amounts", "spending_obligation", "current_guidelines"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="HK",
        jurisdiction_name="Hong Kong SAR",
        program_name="Hong Kong Film Development Fund (FDF)",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Film Development Council of Hong Kong — Film Development Fund",
        source_url="https://www.fdc.gov.hk/",
        effective_from="2007-01-01",
        notes=(
            "Hong Kong Film Development Fund (HKD 400M+) supports local and co-production films. "
            "Grant streams: First Feature Film Initiative, Script Development, Production Financing Scheme. "
            "Primarily supports HK local productions and HKSAR-China co-productions. "
            "Data gaps: eligibility for international co-productions, current grant amounts."
        ),
        unknown_fields=["international_eligibility", "grant_amounts", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IN",
        jurisdiction_name="India",
        program_name="NFDC International Co-production Development Fund",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="National Film Development Corporation (NFDC) India — International Co-production",
        source_url="https://www.nfdcindia.com/",
        effective_from=None,
        notes=(
            "NFDC India supports international co-productions and development projects. "
            "India has bilateral co-production treaties with 15+ countries. "
            "Separate from state-level rebates (captured in in_national_film). "
            "Data gaps: confirmed fund amounts, current co-production treaty list, eligibility."
        ),
        unknown_fields=["fund_amounts", "treaty_countries", "eligibility_criteria"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SG",
        jurisdiction_name="Singapore",
        program_name="IMDA Singapore — Feature Film Production Grant",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Infocomm Media Development Authority (IMDA) — Singapore Feature Film Production",
        source_url="https://www.imda.gov.sg/",
        effective_from=None,
        notes=(
            "IMDA Singapore administers feature film production grants distinct from SFC production rebate. "
            "Supports Singapore-based productions with cultural or economic content. "
            "Grant-based (not percentage rebate); primarily for Singapore-resident productions. "
            "Data gaps: confirmed grant amounts, eligibility for international co-productions."
        ),
        unknown_fields=["grant_amounts", "international_eligibility", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="TW",
        jurisdiction_name="Taiwan",
        program_name="Taiwan Creative Content Agency (TAICCA) International Co-production Fund",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Taiwan Creative Content Agency (TAICCA) — International Co-production",
        source_url="https://www.taicca.tw/",
        effective_from="2019-01-01",
        notes=(
            "TAICCA supports international co-productions with Taiwan content elements. "
            "Separate from the TFAI cash rebate (tw_film_incentive); this is co-production grant support. "
            "Focus on Taiwan cultural content, cross-border streaming and theatrical productions. "
            "Data gaps: confirmed grant amounts, eligibility criteria, co-production terms."
        ),
        unknown_fields=["grant_amounts", "eligibility", "co_production_terms"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SE-VG",
        jurisdiction_name="Sweden — Västra Götaland",
        program_name="Film i Väst — Regional Co-production Fund",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Film i Väst — Regional Film Fund, Västra Götaland Region",
        source_url="https://www.filmivast.se/",
        effective_from="1992-01-01",
        notes=(
            "Film i Väst is one of Europe's most active regional co-production companies. "
            "Has co-produced international features including von Trier, Loach, and Haneke films. "
            "Requires significant production activity in Västra Götaland region (Gothenburg area). "
            "Data gaps: confirmed current investment levels, co-production terms, spending requirements."
        ),
        unknown_fields=["investment_amounts", "co_production_terms", "spending_requirements"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ACP",
        jurisdiction_name="African, Caribbean and Pacific Group",
        program_name="ACP Films — EU-ACP Cultural Film Co-production Fund",
        program_type="co_production_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="ACP Films — EU-ACP Cultural Fund",
        source_url="https://www.acpfilms.eu/",
        effective_from="2008-01-01",
        notes=(
            "ACP Films supports co-productions between EU and African, Caribbean and Pacific (ACP) countries. "
            "Funded under the European Development Fund (EDF). "
            "Programme may have been restructured; verify current status before application. "
            "Data gaps: current programme status, confirmed grant amounts, eligibility criteria."
        ),
        unknown_fields=["programme_status", "current_amounts", "eligibility_criteria"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US",
        jurisdiction_name="United States",
        program_name="ITVS International Documentary Fund",
        program_type="development_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="ITVS (Independent Television Service) — International Documentary Fund",
        source_url="https://itvs.org/funding/",
        effective_from="1991-01-01",
        notes=(
            "ITVS provides development and production grants for documentary films "
            "intended for public television broadcast in the United States. "
            "International co-productions eligible through co-financing arrangements. "
            "Data gaps: confirmed current grant amounts, international eligibility, application cycles."
        ),
        unknown_fields=["current_amounts", "international_eligibility", "application_cycles"],
    ),

]
