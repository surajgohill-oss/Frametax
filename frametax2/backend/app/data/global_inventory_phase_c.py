"""
Phase C regional fund inventory — 8 new programs.

Covers French regional funds (IDF, NAQ, ARA, OCC), Belgian regional
funds (Wallimage, VAF, Screen.Brussels), and German nordmedia.

All programs start at DISCOVERY tier. Rates are published but
require verification against current-year funding guidelines.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

PHASE_C_PROGRAMS: list[GlobalProgramEntry] = [
    # -------------------------------------------------------------------------
    # French regional funds
    # -------------------------------------------------------------------------
    GlobalProgramEntry(
        jurisdiction_code="FR-IDF",
        jurisdiction_name="Île-de-France, France",
        program_name="Île-de-France Cinema Regional Aid",
        program_type="regional_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=500_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Région Île-de-France — Cinema and Audiovisual Support",
        source_url=None,
        effective_from=None,
        notes=(
            "Région Île-de-France supports feature films and documentaries with a "
            "significant production footprint in the Paris region. "
            "Grant amounts vary; typically €50k–€300k per project. "
            "Requires minimum spend in Île-de-France."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),
    GlobalProgramEntry(
        jurisdiction_code="FR-NAQ",
        jurisdiction_name="Nouvelle-Aquitaine, France",
        program_name="Nouvelle-Aquitaine Regional Cinema Aid",
        program_type="regional_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=300_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Film Commission Nouvelle-Aquitaine — Regional Production Support",
        source_url=None,
        effective_from=None,
        notes=(
            "Région Nouvelle-Aquitaine supports film and audiovisual productions "
            "filmed in the region (Bordeaux, Dordogne, Basque Country). "
            "Grant typically €30k–€200k. Administered by Film Commission Nouvelle-Aquitaine."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),
    GlobalProgramEntry(
        jurisdiction_code="FR-ARA",
        jurisdiction_name="Auvergne-Rhône-Alpes, France",
        program_name="Auvergne-Rhône-Alpes Cinema Regional Aid",
        program_type="regional_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=300_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Région Auvergne-Rhône-Alpes — Cinema Support",
        source_url=None,
        effective_from=None,
        notes=(
            "Région Auvergne-Rhône-Alpes supports feature films and series shot "
            "in the region (Lyon, Grenoble, Clermont-Ferrand). "
            "Grant typically €30k–€200k per project."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),
    GlobalProgramEntry(
        jurisdiction_code="FR-OCC",
        jurisdiction_name="Occitanie, France",
        program_name="Occitanie Cinema Regional Aid",
        program_type="regional_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=200_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Région Occitanie — Cinema and Audiovisual Support",
        source_url=None,
        effective_from=None,
        notes=(
            "Région Occitanie supports productions with a spend footprint in "
            "southern France (Toulouse, Montpellier). "
            "Grant amounts €20k–€150k. Stackable with CNC national aids."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),
    # -------------------------------------------------------------------------
    # Belgian regional funds
    # -------------------------------------------------------------------------
    GlobalProgramEntry(
        jurisdiction_code="BE-WAL",
        jurisdiction_name="Wallonia, Belgium",
        program_name="Wallimage Co-production Fund",
        program_type="regional_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=1_500_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Wallimage — Co-production Fund Guidelines",
        source_url=None,
        effective_from=None,
        notes=(
            "Wallimage is the Wallonia (French-speaking Belgium) regional film fund. "
            "Provides repayable advances (loans) and grants to productions with "
            "a significant spend in Wallonia. "
            "Typical investment €100k–€500k. Stackable with Belgian tax shelter."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),
    GlobalProgramEntry(
        jurisdiction_code="BE-VLG",
        jurisdiction_name="Flanders, Belgium",
        program_name="VAF Flanders Audiovisual Fund",
        program_type="regional_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=2_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="VAF — Vlaams Audiovisueel Fonds Production Support",
        source_url=None,
        effective_from=None,
        notes=(
            "VAF (Vlaams Audiovisueel Fonds) is the Flemish regional film fund. "
            "Supports development, production and distribution of Flemish productions. "
            "Production support typically €100k–€750k per project. "
            "Requires Flemish creative involvement and Flemish spend."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),
    GlobalProgramEntry(
        jurisdiction_code="BE-BRU",
        jurisdiction_name="Brussels-Capital, Belgium",
        program_name="Screen.Brussels Production Support",
        program_type="regional_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=False,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=500_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="Screen.Brussels — Production Support Programme",
        source_url=None,
        effective_from=None,
        notes=(
            "Screen.Brussels is the Brussels-Capital Region film fund. "
            "Supports productions with a significant shoot and/or post-production "
            "presence in Brussels. Grants €20k–€200k. "
            "Stackable with Belgian tax shelter and VAF/Wallimage."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),
    # -------------------------------------------------------------------------
    # German regional fund
    # -------------------------------------------------------------------------
    GlobalProgramEntry(
        jurisdiction_code="DE-NI",
        jurisdiction_name="Lower Saxony / Bremen, Germany",
        program_name="nordmedia Film und Mediengesellschaft",
        program_type="regional_fund",
        base_rate=None,
        max_rate=None,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=2_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier="DISCOVERY",
        source_title="nordmedia — Film und Mediengesellschaft Niedersachsen/Bremen",
        source_url=None,
        effective_from=None,
        notes=(
            "nordmedia is the regional media fund for Lower Saxony and Bremen. "
            "Provides production funding (typically 15–25% of German qualifying spend "
            "up to €750k per project). Requires regional spend in Lower Saxony / Bremen. "
            "Stackable with DFFF and FFA national support."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap"],
    ),
]
