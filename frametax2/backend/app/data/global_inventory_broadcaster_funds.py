"""
global_inventory_broadcaster_funds.py — Phase A closeout: broadcaster and
additional development / co-production fund programs.

Covers:
  - UK broadcaster funds (BBC Films, Channel 4 Film / Film4)
  - German/Franco-German broadcaster funds (ZDF, Arte, WDR/ARD)
  - French broadcaster fund (CANAL+)
  - Nordic broadcaster funds (SVT, NRK, DR, YLE)
  - Irish broadcaster fund (RTÉ)
  - Italian broadcaster fund (RAI Cinema)
  - Spanish broadcaster fund (RTVE)
  - Austrian broadcaster fund (ORF Film/Fernseh-Abkommen)
  - Dutch broadcaster fund (VPRO/NPO)
  - Additional development/co-production funds filling coverage gaps

All entries are DISCOVERY tier unless primary source data is directly encoded.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

BROADCASTER_FUND_PROGRAMS: list[GlobalProgramEntry] = [

    # -------------------------------------------------------------------------
    # United Kingdom broadcaster funds
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="GB",
        jurisdiction_name="United Kingdom",
        program_name="BBC Films — Co-production and Development Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="BBC Films — About BBC Films",
        source_url=None,
        effective_from=None,
        notes=(
            "BBC Films finances and co-produces theatrical feature films. "
            "Typical contribution £500k–£3M as co-investor. "
            "BBC Films participation does not reduce AVEC qualifying expenditure (co-financing arrangement). "
            "Scripts must have UK qualifying status. "
            "UNKNOWN: current annual slate budget, per-project cap, commissioning call schedule."
        ),
        unknown_fields=["budget_range", "commissioning_criteria", "per_project_cap", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="GB",
        jurisdiction_name="United Kingdom",
        program_name="Channel 4 Film / Film4 — Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Film4 Productions — About Film4",
        source_url=None,
        effective_from=None,
        notes=(
            "Film4 (Channel 4's film division) co-produces and pre-buys UK theatrical features. "
            "Contribution typically £300k–£2M. "
            "Film4 participation does not reduce AVEC qualifying expenditure. "
            "Combines with BFI Film Fund, Screen agencies, and international co-production partners. "
            "UNKNOWN: per-project cap, annual slate budget, commissioning rounds."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    # -------------------------------------------------------------------------
    # German broadcaster funds
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="DE",
        jurisdiction_name="Germany",
        program_name="ZDF / Das Kleine Fernsehspiel — Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="ZDF — Das Kleine Fernsehspiel",
        source_url=None,
        effective_from=None,
        notes=(
            "ZDF's Das Kleine Fernsehspiel commissions and co-produces international art-house films and documentaries. "
            "Per-project contributions typically €50k–€500k. "
            "ZDF participation does not reduce DFFF/GFFF qualifying spend. "
            "Often combined with Eurimages, national film institutes, and German regional funds. "
            "UNKNOWN: current annual budget, per-project cap."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DE",
        jurisdiction_name="Germany",
        program_name="WDR / ARD — Film and Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="ARD/WDR — Film co-production",
        source_url=None,
        effective_from=None,
        notes=(
            "ARD/WDR co-produces theatrical and prestige TV films, often in combination with "
            "Arte and German regional funds. Contributions typically €100k–€1M. "
            "Broadcaster participation does not reduce DFFF qualifying spend. "
            "UNKNOWN: current annual budget, per-project cap, commissioning criteria."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    # -------------------------------------------------------------------------
    # Franco-German broadcaster fund (Arte)
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="FR",
        jurisdiction_name="France",
        program_name="Arte France Cinéma — Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Arte France Cinéma",
        source_url=None,
        effective_from=None,
        notes=(
            "Arte France Cinéma co-produces theatrical films, documentaries, and short films. "
            "Operates across France and Germany (GmbH arm). Per-project: typically €100k–€800k. "
            "Arte contributions do not reduce CNC tax crédit cinéma qualifying spend. "
            "Frequently combined with Eurimages, CNC, and German regional funds. "
            "UNKNOWN: current annual slate budget, per-project cap."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap"],
    ),

    # -------------------------------------------------------------------------
    # French broadcaster fund (CANAL+)
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="FR",
        jurisdiction_name="France",
        program_name="CANAL+ — Obligation de Contribution à la Production Française",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="CANAL+ — Obligations de financement du cinéma",
        source_url=None,
        effective_from=None,
        notes=(
            "CANAL+ is required by French law to invest a fixed percentage of its subscription revenues "
            "in French film production (Chronologie des médias). Typically €60M–€200M per year total. "
            "CANAL+ pre-purchase/co-production contribution does not reduce CNC tax credit qualifying spend. "
            "UNKNOWN: per-project minimums/maximums, current year total obligation."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    # -------------------------------------------------------------------------
    # Scandinavian broadcaster funds
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="SE",
        jurisdiction_name="Sweden",
        program_name="SVT — Swedish Television Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="SVT — Co-production",
        source_url=None,
        effective_from=None,
        notes=(
            "SVT (Sweden's public broadcaster) co-produces films and TV drama with Swedish focus. "
            "Per-project contributions typically SEK 1M–15M. "
            "Combines with Swedish Film Institute support. "
            "UNKNOWN: current per-project cap, annual budget, commissioning criteria."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="NO",
        jurisdiction_name="Norway",
        program_name="NRK — Norwegian Broadcasting Corporation Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="NRK — Co-production policy",
        source_url=None,
        effective_from=None,
        notes=(
            "NRK co-produces theatrical features and documentary films with Norwegian content focus. "
            "Per-project contributions typically NOK 1M–10M. "
            "Combines with NFI selective support and Eurimages. "
            "UNKNOWN: current per-project cap, annual budget."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DK",
        jurisdiction_name="Denmark",
        program_name="DR — Danish Broadcasting Corporation Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="DR — Filmfund og co-produktion",
        source_url=None,
        effective_from=None,
        notes=(
            "DR (Denmark's public broadcaster) co-produces films and prestige TV drama. "
            "Often co-produces with DFI (Danish Film Institute). "
            "UNKNOWN: per-project cap, annual budget, commissioning criteria."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="FI",
        jurisdiction_name="Finland",
        program_name="YLE — Finnish Broadcasting Company Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="YLE — Elokuvatuotanto (Film Production)",
        source_url=None,
        effective_from=None,
        notes=(
            "YLE co-produces films and prestige TV with Finnish content focus. "
            "Per-project contributions typically €50k–€500k. "
            "YLE contribution does not reduce SES (Finnish Film Foundation) qualifying spend. "
            "UNKNOWN: current per-project cap, annual budget."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap"],
    ),

    # -------------------------------------------------------------------------
    # Irish broadcaster fund
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="IE",
        jurisdiction_name="Ireland",
        program_name="RTÉ — Broadcasting Authority of Ireland Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="RTÉ — Commissioning and co-production",
        source_url=None,
        effective_from=None,
        notes=(
            "RTÉ (Ireland's public broadcaster) co-produces Irish-focus films and TV drama, "
            "often in combination with Section 481 Film Tax Credit. "
            "RTÉ co-investment does not reduce Section 481 qualifying expenditure. "
            "Sound & Vision Scheme (BAI) provides complementary funding. "
            "UNKNOWN: per-project cap, commissioning criteria, annual budget."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    # -------------------------------------------------------------------------
    # Italian broadcaster fund
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="IT",
        jurisdiction_name="Italy",
        program_name="RAI Cinema — Co-production and Acquisition Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="RAI Cinema — Co-produzioni",
        source_url=None,
        effective_from=None,
        notes=(
            "RAI Cinema co-produces and pre-buys Italian theatrical features, obligated by MISE/MiC to invest "
            "a percentage of revenues in Italian production. Per-project: typically €200k–€2M. "
            "RAI contributions do not reduce MiC tax credit qualifying spend. "
            "UNKNOWN: current per-project cap, annual obligation percentage, commissioning criteria."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    # -------------------------------------------------------------------------
    # Spanish broadcaster fund
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="ES",
        jurisdiction_name="Spain",
        program_name="RTVE — Radio Televisión Española Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="RTVE — Cine español",
        source_url=None,
        effective_from=None,
        notes=(
            "RTVE is legally obligated to invest a percentage of revenues in Spanish film production. "
            "Pre-purchase and co-production contributions typically €100k–€1.5M per project. "
            "RTVE contributions do not reduce ICAA audiovisual production deduction. "
            "UNKNOWN: current per-project cap, annual investment obligation."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    # -------------------------------------------------------------------------
    # Austrian broadcaster fund
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="AT",
        jurisdiction_name="Austria",
        program_name="ORF Film/Fernseh-Abkommen — Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="ORF — Film/Fernseh-Abkommen (Austrian Film/TV Agreement)",
        source_url=None,
        effective_from=None,
        notes=(
            "ORF (Austrian public broadcaster) is party to the Film/Fernseh-Abkommen, a formal agreement "
            "between ORF, the Austrian Film Institute (ÖFI), and the federal government. "
            "ORF commits ~€16M/year to Austrian film production. Per-project: typically €200k–€800k. "
            "ORF contribution does not reduce Austrian Film Institute qualifying spend. "
            "UNKNOWN: per-project cap, annual commitment revision cycle."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    # -------------------------------------------------------------------------
    # Dutch broadcaster fund
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="NL",
        jurisdiction_name="Netherlands",
        program_name="NPO / VPRO — Dutch Public Broadcaster Co-production Fund",
        program_type="broadcaster_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="NPO — Coproductie en programmering",
        source_url=None,
        effective_from=None,
        notes=(
            "NPO (Netherlands Public Broadcasting) and its members (VPRO, KRO-NCRV, etc.) "
            "co-produce theatrical films and prestige TV. Per-project: typically €100k–€600k. "
            "Often combined with Netherlands Film Fund (NFF) and Eurimages. "
            "UNKNOWN: per-project cap, annual budget."
        ),
        unknown_fields=["budget_range", "per_project_cap", "annual_cap", "commissioning_criteria"],
    ),

    # -------------------------------------------------------------------------
    # Additional co-production / development fund gaps
    # -------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="AT",
        jurisdiction_name="Austria",
        program_name="Austrian Film Institute (ÖFI) — Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=1_000_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Österreichisches Filminstitut (ÖFI)",
        source_url=None,
        effective_from=None,
        notes=(
            "ÖFI provides selective and automatic production grants for Austrian films. "
            "Maximum grant typically €1M for selective support; ÖFI also administers automatic support "
            "based on cinema admissions. Requires Austrian producer and cultural test. "
            "UNKNOWN: current maximum, automatic support rate, ATL/BTL treatment."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CH",
        jurisdiction_name="Switzerland",
        program_name="MEDIA Desk Switzerland / Succès Cinéma — Automatic Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=500_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Federal Office of Culture — Succès Cinéma",
        source_url=None,
        effective_from=None,
        notes=(
            "Swiss automatic support (Succès Cinéma) based on box office receipts. "
            "BAK (Federal Office of Culture) provides selective support for Swiss feature films. "
            "Combines with cantonal film offices (Zurich Film Fund, ZFF, Bern, etc.). "
            "UNKNOWN: base rate, per-project cap, ATL/BTL treatment."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="PL",
        jurisdiction_name="Poland",
        program_name="Polish Film Institute (PISF) — Production Grant",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=1_100_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Polski Instytut Sztuki Filmowej (PISF)",
        source_url=None,
        effective_from=None,
        notes=(
            "PISF provides selective production grants for Polish feature films and co-productions. "
            "Maximum selective grant typically up to PLN 5M (~€1.1M). "
            "Eurimages member — eligible for Eurimages co-production grants. "
            "UNKNOWN: base rate, confirmed maximum, ATL/BTL treatment."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CZ",
        jurisdiction_name="Czech Republic",
        program_name="Czech Film Fund — Production Support",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=1_100_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Státní fond kinematografie — Czech Film Fund",
        source_url=None,
        effective_from=None,
        notes=(
            "Czech Film Fund (Státní fond kinematografie) supports Czech film production via selective grants. "
            "Also administers the Czech Republic Audiovisual Industry Support (cash rebate). "
            "UNKNOWN: base rate, confirmed maximum, ATL/BTL treatment."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="HU",
        jurisdiction_name="Hungary",
        program_name="National Film Institute (NFI Hungary) — Production Grant",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=1_100_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Nemzeti Filmintézet (NFI) — Hungary",
        source_url=None,
        effective_from=None,
        notes=(
            "NFI Hungary supports Hungarian film production via selective grants and automatic support. "
            "Hungary also operates a 30% cash rebate for foreign productions. "
            "Selective grants typically up to HUF 400M (~€1.1M). "
            "UNKNOWN: confirmed maximum, ATL/BTL treatment."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="PT",
        jurisdiction_name="Portugal",
        program_name="ICA — Instituto do Cinema e Audiovisual — Production Grants",
        program_type="direct_grant",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=550_000,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="ICA — Instituto do Cinema e Audiovisual",
        source_url=None,
        effective_from=None,
        notes=(
            "ICA provides selective and automatic production grants for Portuguese film. "
            "Automatic support calculated on box-office receipts. "
            "Selective maximum typically €500k. Eurimages member. "
            "UNKNOWN: current maximum, base rate."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),

]
