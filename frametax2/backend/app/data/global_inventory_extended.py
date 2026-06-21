"""
global_inventory_extended.py

Extended GlobalProgramEntry and CostBenchmarkEntry records for ~43 additional
jurisdictions beyond the 17 seeded in global_inventory.py.

All entries are DISCOVERY tier — rates from market knowledge, not verified
against primary official sources. Unknown values are None, never guessed.

Jurisdiction codes:
  US states: US-OR, US-WA, US-IL, US-NC, US-SC, US-MA, US-TX, US-CT,
             US-PA, US-MD, US-VA, US-CO, US-TN, US-OK, US-AL, US-KY
  CA provinces: CA-AB, CA-MB, CA-NS, CA-NB
  Europe: NL, AT, CZ, RO, PT, RS, IS, GB-SCT, GB-WLS
  Asia-Pacific: SG, AU-NSW, AU-VIC, AU-QLD
  Latin America: CO, DO, UY, AR, BR
  Middle East: AE, SA, JO
  Africa: MA, ZA
"""
from __future__ import annotations

from app.data.global_inventory import CostBenchmarkEntry, GlobalProgramEntry

_DISC = "DISCOVERY"
_BM_SOURCE = (
    "Production market knowledge — not verified from primary labour cost surveys. "
    "Confidence tier: DISCOVERY."
)
_BM_DATE = "2025-06"


# ---------------------------------------------------------------------------
# US STATES
# ---------------------------------------------------------------------------

_EXTENDED_PROGRAMS: list[GlobalProgramEntry] = [

    GlobalProgramEntry(
        jurisdiction_code="US-OR",
        jurisdiction_name="United States — Oregon",
        program_name="Oregon Production Investment Fund (OPIF)",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.20,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=750_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Oregon Film Office — OPIF programme summary",
        source_url="https://oregonfilm.org/incentives/",
        effective_from="2009-01-01",
        notes=(
            "20% cash rebate on Oregon-sourced goods and services; "
            "10% rebate on Oregon resident wages. Min $750K Oregon spend. "
            "Annual fund is competitive/capped. "
            "Data gaps: annual cap amount, ATL inclusion, payment timeline."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-WA",
        jurisdiction_name="United States — Washington",
        program_name="Washington State Motion Picture Competitiveness Program",
        program_type="cash_rebate",
        base_rate=0.15,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=500_000,
        annual_cap_usd=3_500_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Washington Filmworks — incentive overview",
        source_url="https://washingtonfilmworks.com/funding/motion-picture-competitiveness-program/",
        effective_from="2009-01-01",
        notes=(
            "Competitive rebate administered by Washington Filmworks. "
            "Base ~15%; total award up to 35% depending on Washington spend composition. "
            "Annual fund: ~$3.5M; competitive and frequently oversubscribed. "
            "Data gaps: exact tier thresholds, current fund size, ATL scope."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "atl_inclusion"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-IL",
        jurisdiction_name="United States — Illinois",
        program_name="Illinois Film Tax Credit",
        program_type="tax_credit",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=True,
        min_spend_usd=50_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Illinois Film Office — tax credit overview",
        source_url="https://www.illinois.gov/business/film-production",
        effective_from="2008-01-01",
        notes=(
            "30% on Illinois production spending + Illinois resident wages. "
            "Refundable or transferable credit. No annual cap. "
            "Chicago is a major production hub. "
            "Data gaps: ATL cap, foreign crew inclusion, exact QPE definition."
        ),
        unknown_fields=["atl_inclusion", "foreign_crew_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-NC",
        jurisdiction_name="United States — North Carolina",
        program_name="North Carolina Film & Entertainment Grant",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=250_000,
        annual_cap_usd=31_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="North Carolina Film Office — grant overview",
        source_url="https://www.filmnc.com/incentives",
        effective_from="2014-01-01",
        notes=(
            "25% cash grant on qualifying NC expenditures. "
            "Annual cap $31M (historically). Competitive. "
            "Data gaps: current cap, ATL inclusion, processing timeline."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-SC",
        jurisdiction_name="United States — South Carolina",
        program_name="South Carolina Film Production Credit",
        program_type="tax_credit",
        base_rate=0.20,
        max_rate=0.30,
        is_refundable=False,
        is_transferable=True,
        min_spend_usd=1_000_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="South Carolina Department of Commerce — film incentives",
        source_url="https://sc.gov/government/agencies/film-commission",
        effective_from="2005-01-01",
        notes=(
            "Up to 30% on SC qualifying expenditures. Transferable credit. "
            "SC resident payroll uplift available. "
            "Data gaps: exact base vs uplift thresholds, ATL treatment."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-MA",
        jurisdiction_name="United States — Massachusetts",
        program_name="Massachusetts Film Tax Credit",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=True,
        min_spend_usd=50_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Massachusetts Film Office — tax credit overview",
        source_url="https://www.mafilm.org/tax-incentives/",
        effective_from="2006-01-01",
        notes=(
            "25% on Massachusetts payroll + 25% on production costs. "
            "No annual cap. Refundable or transferable. "
            "Data gaps: ATL inclusion, transfer market discount, exact QPE."
        ),
        unknown_fields=["atl_inclusion", "transfer_market_discount", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-TX",
        jurisdiction_name="United States — Texas",
        program_name="Texas Moving Image Industry Incentive Program (MIIP)",
        program_type="cash_rebate",
        base_rate=0.05,
        max_rate=0.225,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=250_000,
        annual_cap_usd=95_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Texas Film Commission — MIIP overview",
        source_url="https://gov.texas.gov/film/page/incentives",
        effective_from="2007-01-01",
        notes=(
            "Base 5% on Texas spend. Uplift for Texas cast/crew: total up to 22.5%. "
            "Annual cap ~$95M. Competitive. "
            "Texas lacks strong enough incentives for major features vs GA/LA. "
            "Data gaps: current cap, uplift criteria, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-CT",
        jurisdiction_name="United States — Connecticut",
        program_name="Connecticut Film Tax Credit",
        program_type="tax_credit",
        base_rate=0.10,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=True,
        min_spend_usd=100_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Connecticut Office of Film, Television & Digital Media",
        source_url="https://portal.ct.gov/DECD/Content/Film-television-Creative-Services",
        effective_from="2006-01-01",
        notes=(
            "Tiered: 10% below $1M CT spend, 15% $1M–$500M, 30% over $500M. "
            "Refundable or transferable. No annual cap. "
            "Data gaps: current tier thresholds, ATL treatment, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-PA",
        jurisdiction_name="United States — Pennsylvania",
        program_name="Pennsylvania Film Production Tax Credit",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=False,
        is_transferable=True,
        min_spend_usd=None,
        annual_cap_usd=100_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Pennsylvania Film Office — tax credit",
        source_url="https://dced.pa.gov/programs/pa-film-office/",
        effective_from="2004-01-01",
        notes=(
            "25% on PA qualifying spend. Transferable (not refundable). "
            "Annual cap ~$100M; competitive. "
            "Data gaps: current cap, ATL scope, secondary market discount, timeline."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "transfer_market_discount"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-MD",
        jurisdiction_name="United States — Maryland",
        program_name="Maryland Film Production Activity Tax Credit",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.27,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=500_000,
        annual_cap_usd=25_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Maryland Film Office — tax credit overview",
        source_url="https://www.marylandfilm.org/resources/tax-incentives",
        effective_from="2011-01-01",
        notes=(
            "Up to 27% on Maryland qualifying expenditures. "
            "Annual cap ~$25M. Competitive. "
            "Data gaps: exact rate, current cap, ATL inclusion, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-VA",
        jurisdiction_name="United States — Virginia",
        program_name="Virginia Motion Picture Production Tax Credit",
        program_type="tax_credit",
        base_rate=0.15,
        max_rate=0.20,
        is_refundable=False,
        is_transferable=True,
        min_spend_usd=250_000,
        annual_cap_usd=6_500_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Virginia Film Office — incentives",
        source_url="https://www.film.virginia.org/production/incentives",
        effective_from="2010-01-01",
        notes=(
            "15% base; +5% for Virginia resident cast/crew. Transferable. "
            "Annual cap ~$6.5M — heavily oversubscribed. Weak for major features. "
            "Data gaps: current cap, current rate, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-CO",
        jurisdiction_name="United States — Colorado",
        program_name="Colorado Film Incentive",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.20,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=100_000,
        annual_cap_usd=750_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Colorado Office of Film, Television & Media",
        source_url="https://oedit.colorado.gov/colorado-office-of-film-tv-and-media",
        effective_from="2012-01-01",
        notes=(
            "20% on Colorado qualifying spend. Annual cap ~$750K — very limited. "
            "Colorado landscape attractive for location work despite small cap. "
            "Data gaps: current cap, processing timeline."
        ),
        unknown_fields=["annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-TN",
        jurisdiction_name="United States — Tennessee",
        program_name="Tennessee Film, Entertainment & Music Commission Incentives",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.25,
        is_refundable=None,
        is_transferable=None,
        min_spend_usd=200_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Tennessee Department of Tourist Development — film incentives",
        source_url="https://www.tnfilm.com/incentives",
        effective_from=None,
        notes=(
            "Tennessee offers location-specific cash grants and sales tax exemptions. "
            "Programme structure has changed significantly; rates unconfirmed. "
            "Nashville is a growing production hub. "
            "Data gaps: current programme structure, base rate, cap, timeline."
        ),
        unknown_fields=["confirmed_rate", "base_rate", "annual_cap", "program_structure", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-OK",
        jurisdiction_name="United States — Oklahoma",
        program_name="Oklahoma Film Enhancement Rebate",
        program_type="cash_rebate",
        base_rate=0.35,
        max_rate=0.37,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=25_000,
        annual_cap_usd=5_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Oklahoma Film + Music Office — rebate overview",
        source_url="https://www.oklahomafilm.org/incentives",
        effective_from="2001-01-01",
        notes=(
            "35% on Oklahoma cast/crew wages + goods; +2% if script relates to Oklahoma. "
            "Annual cap ~$5M. Small cap limits large productions. "
            "Data gaps: current cap, QPE definition, processing timeline."
        ),
        unknown_fields=["annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-AL",
        jurisdiction_name="United States — Alabama",
        program_name="Alabama Film Incentive",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=500_000,
        annual_cap_usd=20_000_000,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Alabama Film Office — incentive overview",
        source_url="https://www.alabamafilm.org/incentives",
        effective_from="2009-01-01",
        notes=(
            "25% on Alabama qualifying spend; up to 35% with Alabama resident payroll. "
            "Annual cap ~$20M. "
            "Data gaps: exact tier thresholds, current cap, ATL scope, timeline."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="US-KY",
        jurisdiction_name="United States — Kentucky",
        program_name="Kentucky Entertainment Industry Incentive Act (KEIIA)",
        program_type="tax_credit",
        base_rate=0.30,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=500_000,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Kentucky Film Office — incentives",
        source_url="https://kyfilmoffice.com/production-incentives/",
        effective_from="2009-01-01",
        notes=(
            "30% refundable tax credit on KY qualifying expenditures; "
            "+5% if KY local companies provide goods/services. "
            "No annual cap. "
            "Data gaps: ATL inclusion, processing timeline, QPE exact definition."
        ),
        unknown_fields=["atl_inclusion", "processing_timeline"],
    ),

    # ---------------------------------------------------------------------------
    # CANADIAN PROVINCES
    # ---------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="CA-AB",
        jurisdiction_name="Canada — Alberta",
        program_name="Alberta Film and Television Tax Credit (FTTC)",
        program_type="tax_credit",
        base_rate=0.22,
        max_rate=0.22,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Alberta Media Production Industries Association (AMPIA)",
        source_url="https://www.ampia.org/alberta-film-tv-tax-credit/",
        effective_from="2020-01-01",
        notes=(
            "22% refundable tax credit on eligible Alberta labour costs. "
            "Combines with federal CPTC. Cultural test applies for domestic productions. "
            "No annual cap. "
            "Data gaps: non-resident labour treatment, exact QPE definition, combined effective rate."
        ),
        unknown_fields=["non_resident_labour_treatment", "combined_rate_with_cptc", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-MB",
        jurisdiction_name="Canada — Manitoba",
        program_name="Manitoba Film & Video Production Tax Credit",
        program_type="tax_credit",
        base_rate=0.45,
        max_rate=0.65,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Manitoba Film & Music — tax credit",
        source_url="https://www.mbfilmmusic.ca/en/production-tax-credits",
        effective_from="1997-01-01",
        notes=(
            "45% base on Manitoba labour (domestic). "
            "Bonuses for Winnipeg location (+10%), frequent-use (+5%), etc. "
            "Can reach 65% on labour. High labour-basis credit — not on total budget. "
            "Data gaps: foreign production rate, non-labour QPE, exact bonus thresholds."
        ),
        unknown_fields=["foreign_production_rate", "confirmed_rate", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-NS",
        jurisdiction_name="Canada — Nova Scotia",
        program_name="Nova Scotia Film & Television Production Incentive Fund",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.50,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Nova Scotia Business Inc. — film incentives",
        source_url="https://www.novascotiabusiness.com/export/film",
        effective_from="2015-01-01",
        notes=(
            "25% base on Nova Scotia eligible expenditures; "
            "up to 50% with resident crew + production bonuses. "
            "Combined with federal CPTC. "
            "Data gaps: foreign production rate, exact bonus structure, processing timeline."
        ),
        unknown_fields=["foreign_production_rate", "confirmed_rate", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CA-NB",
        jurisdiction_name="Canada — New Brunswick",
        program_name="New Brunswick Film Tax Credit",
        program_type="tax_credit",
        base_rate=0.25,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Opportunities NB — film incentives",
        source_url="https://opportunitiesnb.com",
        effective_from="2010-01-01",
        notes=(
            "~25–30% on NB labour costs. Combines with federal CPTC. "
            "Small production market. "
            "Data gaps: exact rate, foreign production rate, QPE definition, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "foreign_production_rate", "annual_cap", "processing_timeline"],
    ),

    # ---------------------------------------------------------------------------
    # EUROPE (non-existing)
    # ---------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="NL",
        jurisdiction_name="Netherlands",
        program_name="Netherlands Film Production Incentive (NFPI)",
        program_type="cash_rebate",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="Netherlands Film Fund — NFPI",
        source_url="https://www.filmfund.nl/en/subsidies/netherlands-film-production-incentive",
        effective_from="2014-01-01",
        notes=(
            "30% cash rebate on qualifying Dutch expenditures. "
            "Cultural test (Dutchness points) required. "
            "Dutch entity required. Annual budget capped (~€30M historically). "
            "Data gaps: current annual cap, exact QPE definition, ATL treatment, processing timeline."
        ),
        unknown_fields=["annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AT",
        jurisdiction_name="Austria",
        program_name="FISA+ Film Production Support Austria",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="FISA+ — Austrian Film Institute",
        source_url="https://www.fisa-plus.at/en/",
        effective_from="2016-01-01",
        notes=(
            "25% cash rebate on Austrian qualifying expenditures. "
            "Minimum €600K Austrian spend. Cultural points test required. "
            "Annual budget ~€20M. "
            "Data gaps: current cap, exact QPE, ATL treatment, processing timeline."
        ),
        unknown_fields=["annual_cap", "min_spend_usd", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="CZ",
        jurisdiction_name="Czech Republic",
        program_name="Czech Film Incentive",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.20,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Czech Film Commission — incentive programme",
        source_url="https://www.filmcommission.cz/incentives/",
        effective_from="2010-01-01",
        notes=(
            "20% cash rebate on qualifying Czech expenditures. "
            "No cultural test for foreign co-productions. "
            "Barrandov Studios is a major international production hub. "
            "Data gaps: min spend, annual cap, ATL inclusion, processing timeline."
        ),
        unknown_fields=["min_spend_usd", "annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="RO",
        jurisdiction_name="Romania",
        program_name="Romanian Film Office Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.35,
        max_rate=0.45,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Romanian Film Centre (CNC) — cash rebate",
        source_url="https://www.cnc.ro/en",
        effective_from="2016-01-01",
        notes=(
            "35% base; up to 45% with Romanian crew bonus. "
            "Low production costs + significant rebate = strong value proposition. "
            "Data gaps: min spend, annual cap, exact QPE, processing timeline, current status."
        ),
        unknown_fields=["confirmed_rate", "min_spend_usd", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="PT",
        jurisdiction_name="Portugal",
        program_name="Portugal Film Commission Incentive / IAPMEI",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Portugal Film Commission — incentives",
        source_url="https://www.filmportugal.com/incentives",
        effective_from="2013-01-01",
        notes=(
            "~25–30% rebate on Portuguese qualifying expenditures. "
            "Cultural test (cultural points) required. "
            "Growing production market; Lisbon/Algarve popular locations. "
            "Data gaps: confirmed rate, min spend, annual cap, exact QPE, timeline."
        ),
        unknown_fields=["confirmed_rate", "min_spend_usd", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="RS",
        jurisdiction_name="Serbia",
        program_name="Serbia Film Commission Cash Rebate",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Film Center Serbia — incentives",
        source_url="https://www.filmcentar.rs",
        effective_from="2016-01-01",
        notes=(
            "Up to 30% on qualifying Serbian expenditures. "
            "Low production costs. Growing international production hub. "
            "Data gaps: confirmed rate, min spend, annual cap, programme status, timeline."
        ),
        unknown_fields=["confirmed_rate", "min_spend_usd", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="IS",
        jurisdiction_name="Iceland",
        program_name="Icelandic Film Reimbursement Scheme",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Invest in Iceland — film incentives",
        source_url="https://www.invest.is/doing-business/incentives/film-incentive/",
        effective_from="1999-01-01",
        notes=(
            "25% reimbursement on Icelandic qualifying expenditures. "
            "Unique landscape attracts major productions (GOT, Star Wars, Bond). "
            "Remote access costs can offset incentive benefit. "
            "Data gaps: min spend, annual cap, ATL inclusion, processing timeline."
        ),
        unknown_fields=["min_spend_usd", "annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="GB-SCT",
        jurisdiction_name="United Kingdom — Scotland",
        program_name="Screen Scotland Production Growth Fund",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Screen Scotland — production support",
        source_url="https://www.screen.scot/funding-and-support/screen-scotland-funding/",
        effective_from="2019-01-01",
        notes=(
            "Screen Scotland Production Growth Fund tops up BFI/HMRC UK tax relief. "
            "UK 20% credit applies; Screen Scotland fund adds uplift for Scotland-based spend. "
            "Scotland locations: Highlands, Edinburgh, Glasgow. "
            "Data gaps: current fund size, exact top-up rate, interaction with HETV relief."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "interaction_with_uk_relief", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="GB-WLS",
        jurisdiction_name="United Kingdom — Wales",
        program_name="Wales Screen Production Fund (Ffilm Cymru Wales)",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Wales Screen / Creative Wales — production funding",
        source_url="https://www.creativewales.wales/en/screen/",
        effective_from="2017-01-01",
        notes=(
            "Wales/Creative Wales fund tops up UK HMRC tax relief for Welsh productions. "
            "Dragon Studios + major BBC Wales output (Doctor Who). "
            "Data gaps: current fund size, exact top-up rate, QPE, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "interaction_with_uk_relief", "processing_timeline"],
    ),

    # ---------------------------------------------------------------------------
    # ASIA-PACIFIC
    # ---------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="SG",
        jurisdiction_name="Singapore",
        program_name="Singapore Film Commission (SFC) — Production Assistance",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.30,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Info-communications Media Development Authority (IMDA) — incentives",
        source_url="https://www.imda.gov.sg/regulations-and-licensing-listing/fia",
        effective_from=None,
        notes=(
            "Singapore offers discretionary grants/rebates via IMDA/SFC for international productions. "
            "Up to 30% rebate reported for qualifying spend. "
            "No formal rebate law; support is discretionary project-by-project. "
            "Singapore is a major APAC financial hub but not a traditional film incentive market. "
            "Data gaps: current programme structure, exact rate, min spend, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "base_rate", "programme_structure", "min_spend_usd", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU-NSW",
        jurisdiction_name="Australia — New South Wales",
        program_name="NSW Government Screen Incentive (via Create NSW)",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.35,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Create NSW — screen incentives",
        source_url="https://www.create.nsw.gov.au/funding-and-support/screen/",
        effective_from="2010-01-01",
        notes=(
            "NSW tops up federal Location Offset with state incentive (~10% uplift on NSW spend). "
            "Combined federal + state can reach 35%+ for qualifying productions. "
            "Sydney has major studio infrastructure (Fox Studios). "
            "Data gaps: confirmed state rate, interaction with federal offset, annual cap, timeline."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "interaction_with_federal_offset", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU-VIC",
        jurisdiction_name="Australia — Victoria",
        program_name="VicScreen Production Investment",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.335,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="VicScreen — production investment",
        source_url="https://vicscreen.vic.gov.au/funding/production-investment",
        effective_from="2012-01-01",
        notes=(
            "VicScreen tops up federal Location Offset with 13.5% state uplift on Victorian spend. "
            "Combined federal + state can reach ~33.5% on qualifying Victorian expenditures. "
            "Melbourne is Australia's #2 production hub. "
            "Data gaps: confirmed state rate, interaction with federal offset, annual cap, timeline."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "interaction_with_federal_offset", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AU-QLD",
        jurisdiction_name="Australia — Queensland",
        program_name="Screen Queensland Production Attraction Strategy",
        program_type="cash_rebate",
        base_rate=0.15,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Screen Queensland — production support",
        source_url="https://screenqueensland.com.au/get-funding/production-attraction/",
        effective_from="2014-01-01",
        notes=(
            "Screen Queensland cash incentive on Queensland qualifying expenditures. "
            "Tops up federal Location Offset. Village Roadshow Studios (Gold Coast) nearby. "
            "Data gaps: confirmed state rate, annual cap, interaction with federal offset, timeline."
        ),
        unknown_fields=["confirmed_rate", "annual_cap", "interaction_with_federal_offset", "processing_timeline"],
    ),

    # ---------------------------------------------------------------------------
    # LATIN AMERICA
    # ---------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="CO",
        jurisdiction_name="Colombia",
        program_name="Colombia Film Commission — Film In Colombia",
        program_type="cash_rebate",
        base_rate=0.40,
        max_rate=0.40,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="ProColombia — film production incentives",
        source_url="https://procolombia.co/en/opportunities-industries/film-sector",
        effective_from="2013-01-01",
        notes=(
            "40% services tax refund (VAT/IVA) on eligible Colombian expenditures. "
            "Up to ~35% on income tax withholdings. "
            "Cartagena, Bogotá, and the Andes offer diverse locations. "
            "Data gaps: exact mechanism (VAT vs income tax), min spend, annual cap, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "programme_mechanism", "min_spend_usd", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="DO",
        jurisdiction_name="Dominican Republic",
        program_name="Dominican Republic Film Commission Incentive",
        program_type="cash_rebate",
        base_rate=0.25,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Dominican Republic Film Commission",
        source_url="https://www.drfilmcommission.com",
        effective_from="2010-01-01",
        notes=(
            "25% rebate on qualifying Dominican expenditures. "
            "Caribbean locations; Pinewood Dominican Republic studio. "
            "Data gaps: confirmed rate, min spend, annual cap, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "min_spend_usd", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="UY",
        jurisdiction_name="Uruguay",
        program_name="Uruguay XXI Film Incentive",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.20,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Uruguay XXI — audiovisual sector",
        source_url="https://www.uruguayxxi.gub.uy",
        effective_from=None,
        notes=(
            "Uruguay offers tax-based rebates and exemptions for international productions. "
            "Growing production market; Montevideo as LATAM base. "
            "Data gaps: confirmed rate, programme structure, min spend, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "base_rate", "programme_structure", "min_spend_usd", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="AR",
        jurisdiction_name="Argentina",
        program_name="INCAA — Argentine Film Institute Incentives",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.25,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="INCAA — Instituto Nacional de Cine y Artes Audiovisuales",
        source_url="https://www.incaa.gov.ar",
        effective_from=None,
        notes=(
            "INCAA administers Argentine film incentives. "
            "VAT exemptions + rebate for qualifying international co-productions. "
            "Currency/FX risk significant. Buenos Aires is a major LATAM production hub. "
            "Data gaps: confirmed rate, programme structure, min spend, FX treatment, timeline."
        ),
        unknown_fields=["confirmed_rate", "base_rate", "programme_structure", "fx_treatment", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="BR",
        jurisdiction_name="Brazil",
        program_name="ANCINE — Brazilian Film Commission Tax Incentives",
        program_type="tax_credit",
        base_rate=None,
        max_rate=0.40,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="ANCINE — Brazilian National Film Agency",
        source_url="https://www.ancine.gov.br",
        effective_from=None,
        notes=(
            "Brazil offers Rouanet Law + ANCINE incentives. Reported up to 40% for co-productions. "
            "Brazilian entity (BRASA) required. São Paulo and Rio de Janeiro major hubs. "
            "Bureaucratic complexity + political risk + FX risk. "
            "Data gaps: confirmed rate, mechanism, min spend, annual cap, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "base_rate", "programme_mechanism", "min_spend_usd", "processing_timeline"],
    ),

    # ---------------------------------------------------------------------------
    # MIDDLE EAST
    # ---------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="AE",
        jurisdiction_name="United Arab Emirates",
        program_name="Dubai Film Commission — Dubai Production Incentive (DPIP)",
        program_type="cash_rebate",
        base_rate=0.30,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Dubai Film Commission — production incentive",
        source_url="https://www.dubaifilmcommission.com/incentives",
        effective_from="2022-01-01",
        notes=(
            "Dubai Production Incentive Programme (DPIP): 30% cashback on Dubai qualifying spend. "
            "UAE has no income or corporate tax (except for MNEs under Pillar Two). "
            "Production-friendly environment; desert + modern city locations. "
            "Also: Abu Dhabi Film Commission has separate incentive (~30%). "
            "Data gaps: confirmed rate, min spend, annual cap, ATL treatment, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "min_spend_usd", "annual_cap", "atl_inclusion", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="SA",
        jurisdiction_name="Saudi Arabia",
        program_name="Saudi Film Commission (SFC) — Production Rebate",
        program_type="cash_rebate",
        base_rate=None,
        max_rate=0.40,
        is_refundable=None,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Saudi Film Commission — incentives",
        source_url="https://saudifi.com",
        effective_from="2020-01-01",
        notes=(
            "Saudi Arabia emerging as major production market under Vision 2030. "
            "Saudi Film Commission offering rebates reportedly up to 40% for qualifying productions. "
            "Programme structure still evolving; content restrictions apply. "
            "Data gaps: confirmed rate, min spend, cap, content restrictions, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "base_rate", "programme_structure", "content_restrictions", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="JO",
        jurisdiction_name="Jordan",
        program_name="Royal Film Commission Jordan — Production Rebate",
        program_type="cash_rebate",
        base_rate=0.10,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="Royal Film Commission Jordan — rebate",
        source_url="https://www.rfc.jo/en/incentives",
        effective_from="2008-01-01",
        notes=(
            "~10–25% rebate on Jordanian qualifying expenditures. "
            "Petra, Wadi Rum, Aqaba major location assets (Lawrence of Arabia, The Martian, Dune). "
            "Content review required. "
            "Data gaps: confirmed rate, min spend, annual cap, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "min_spend_usd", "annual_cap", "processing_timeline"],
    ),

    # ---------------------------------------------------------------------------
    # AFRICA
    # ---------------------------------------------------------------------------

    GlobalProgramEntry(
        jurisdiction_code="MA",
        jurisdiction_name="Morocco",
        program_name="Centre Cinématographique Marocain (CCM) — Production Rebate",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.30,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier=_DISC,
        source_title="CCM Morocco — foreign production support",
        source_url="https://www.ccm.ma",
        effective_from="2013-01-01",
        notes=(
            "~20–30% rebate on Moroccan qualifying expenditures. "
            "Ouarzazate / Atlas Studios: one of Africa's largest studio complexes. "
            "Morocco requires local Moroccan production company (SOTAP). "
            "Strong track record: Gladiator, Game of Thrones, many major productions. "
            "Data gaps: confirmed rate, min spend, annual cap, exact QPE, processing timeline."
        ),
        unknown_fields=["confirmed_rate", "min_spend_usd", "annual_cap", "processing_timeline"],
    ),

    GlobalProgramEntry(
        jurisdiction_code="ZA",
        jurisdiction_name="South Africa",
        program_name="NFVF / Department of Trade & Industry (DTI) — Foreign Film & TV Production Rebate",
        program_type="cash_rebate",
        base_rate=0.20,
        max_rate=0.25,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=False,
        requires_local_entity=False,
        confidence_tier=_DISC,
        source_title="National Film and Video Foundation (NFVF) — foreign rebate",
        source_url="https://www.nfvf.co.za",
        effective_from="2004-01-01",
        notes=(
            "~20–25% rebate on South African qualifying expenditures. "
            "Cape Town is Africa's primary international production hub. "
            "Favourable USD/ZAR exchange rate enhances real benefit. "
            "Data gaps: confirmed rate, min spend, annual cap, processing timeline, DTI vs NFVF split."
        ),
        unknown_fields=["confirmed_rate", "min_spend_usd", "annual_cap", "processing_timeline"],
    ),
]


# ---------------------------------------------------------------------------
# COST BENCHMARKS — all DISCOVERY, relative to LA (1.0)
# ---------------------------------------------------------------------------

_EXTENDED_BENCHMARKS: list[CostBenchmarkEntry] = [

    # US states — generally 0.70–0.85 vs LA, except for regional markets
    CostBenchmarkEntry(
        jurisdiction_code="US-OR",
        crew_rate_multiplier=0.78,
        equipment_rental_multiplier=0.75,
        stage_facility_multiplier=0.72,
        location_fees_multiplier=0.68,
        post_production_multiplier=0.78,
        vfx_multiplier=0.80,
        catering_multiplier=0.75,
        key_crew_daily_travel_usd=340.0,
        marine_vessel_multiplier=0.70,
        lodging_daily_usd=200.0,
        per_diem_daily_usd=90.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Portland/Oregon LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-WA",
        crew_rate_multiplier=0.82,
        equipment_rental_multiplier=0.78,
        stage_facility_multiplier=0.75,
        location_fees_multiplier=0.72,
        post_production_multiplier=0.82,
        vfx_multiplier=0.85,
        catering_multiplier=0.78,
        key_crew_daily_travel_usd=350.0,
        marine_vessel_multiplier=0.75,
        lodging_daily_usd=210.0,
        per_diem_daily_usd=95.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Seattle/Washington LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-IL",
        crew_rate_multiplier=0.88,
        equipment_rental_multiplier=0.82,
        stage_facility_multiplier=0.80,
        location_fees_multiplier=0.85,
        post_production_multiplier=0.85,
        vfx_multiplier=0.88,
        catering_multiplier=0.82,
        key_crew_daily_travel_usd=360.0,
        marine_vessel_multiplier=0.75,
        lodging_daily_usd=230.0,
        per_diem_daily_usd=100.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Chicago/Illinois LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-NC",
        crew_rate_multiplier=0.72,
        equipment_rental_multiplier=0.68,
        stage_facility_multiplier=0.65,
        location_fees_multiplier=0.60,
        post_production_multiplier=0.72,
        vfx_multiplier=0.75,
        catering_multiplier=0.68,
        key_crew_daily_travel_usd=300.0,
        marine_vessel_multiplier=0.65,
        lodging_daily_usd=175.0,
        per_diem_daily_usd=80.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="North Carolina LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-SC",
        crew_rate_multiplier=0.70,
        equipment_rental_multiplier=0.65,
        stage_facility_multiplier=0.62,
        location_fees_multiplier=0.55,
        post_production_multiplier=0.70,
        vfx_multiplier=0.72,
        catering_multiplier=0.65,
        key_crew_daily_travel_usd=290.0,
        marine_vessel_multiplier=0.62,
        lodging_daily_usd=165.0,
        per_diem_daily_usd=78.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="South Carolina LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-MA",
        crew_rate_multiplier=0.90,
        equipment_rental_multiplier=0.85,
        stage_facility_multiplier=0.82,
        location_fees_multiplier=0.90,
        post_production_multiplier=0.88,
        vfx_multiplier=0.90,
        catering_multiplier=0.85,
        key_crew_daily_travel_usd=370.0,
        marine_vessel_multiplier=0.80,
        lodging_daily_usd=250.0,
        per_diem_daily_usd=105.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Boston/Massachusetts LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-TX",
        crew_rate_multiplier=0.78,
        equipment_rental_multiplier=0.75,
        stage_facility_multiplier=0.72,
        location_fees_multiplier=0.70,
        post_production_multiplier=0.78,
        vfx_multiplier=0.80,
        catering_multiplier=0.75,
        key_crew_daily_travel_usd=320.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=190.0,
        per_diem_daily_usd=88.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Texas (Austin/Dallas/Houston) LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-CT",
        crew_rate_multiplier=0.88,
        equipment_rental_multiplier=0.82,
        stage_facility_multiplier=0.80,
        location_fees_multiplier=0.85,
        post_production_multiplier=0.85,
        vfx_multiplier=0.88,
        catering_multiplier=0.82,
        key_crew_daily_travel_usd=360.0,
        marine_vessel_multiplier=0.80,
        lodging_daily_usd=230.0,
        per_diem_daily_usd=100.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Connecticut LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-PA",
        crew_rate_multiplier=0.82,
        equipment_rental_multiplier=0.78,
        stage_facility_multiplier=0.75,
        location_fees_multiplier=0.80,
        post_production_multiplier=0.80,
        vfx_multiplier=0.82,
        catering_multiplier=0.78,
        key_crew_daily_travel_usd=340.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=205.0,
        per_diem_daily_usd=92.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Philadelphia/Pennsylvania LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-MD",
        crew_rate_multiplier=0.85,
        equipment_rental_multiplier=0.80,
        stage_facility_multiplier=0.78,
        location_fees_multiplier=0.82,
        post_production_multiplier=0.82,
        vfx_multiplier=0.85,
        catering_multiplier=0.80,
        key_crew_daily_travel_usd=350.0,
        marine_vessel_multiplier=0.78,
        lodging_daily_usd=220.0,
        per_diem_daily_usd=95.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Maryland LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-VA",
        crew_rate_multiplier=0.80,
        equipment_rental_multiplier=0.76,
        stage_facility_multiplier=0.72,
        location_fees_multiplier=0.75,
        post_production_multiplier=0.78,
        vfx_multiplier=0.80,
        catering_multiplier=0.76,
        key_crew_daily_travel_usd=330.0,
        marine_vessel_multiplier=0.72,
        lodging_daily_usd=200.0,
        per_diem_daily_usd=88.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Virginia LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-CO",
        crew_rate_multiplier=0.78,
        equipment_rental_multiplier=0.75,
        stage_facility_multiplier=0.70,
        location_fees_multiplier=0.68,
        post_production_multiplier=0.78,
        vfx_multiplier=0.80,
        catering_multiplier=0.75,
        key_crew_daily_travel_usd=320.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=195.0,
        per_diem_daily_usd=88.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Denver/Colorado LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-TN",
        crew_rate_multiplier=0.70,
        equipment_rental_multiplier=0.68,
        stage_facility_multiplier=0.65,
        location_fees_multiplier=0.60,
        post_production_multiplier=0.70,
        vfx_multiplier=0.72,
        catering_multiplier=0.68,
        key_crew_daily_travel_usd=290.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=170.0,
        per_diem_daily_usd=78.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Nashville/Tennessee LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-OK",
        crew_rate_multiplier=0.65,
        equipment_rental_multiplier=0.62,
        stage_facility_multiplier=0.60,
        location_fees_multiplier=0.50,
        post_production_multiplier=0.65,
        vfx_multiplier=0.68,
        catering_multiplier=0.62,
        key_crew_daily_travel_usd=275.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=150.0,
        per_diem_daily_usd=70.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Oklahoma LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-AL",
        crew_rate_multiplier=0.65,
        equipment_rental_multiplier=0.62,
        stage_facility_multiplier=0.58,
        location_fees_multiplier=0.50,
        post_production_multiplier=0.65,
        vfx_multiplier=0.68,
        catering_multiplier=0.60,
        key_crew_daily_travel_usd=275.0,
        marine_vessel_multiplier=0.60,
        lodging_daily_usd=150.0,
        per_diem_daily_usd=70.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Alabama LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="US-KY",
        crew_rate_multiplier=0.68,
        equipment_rental_multiplier=0.65,
        stage_facility_multiplier=0.62,
        location_fees_multiplier=0.55,
        post_production_multiplier=0.68,
        vfx_multiplier=0.70,
        catering_multiplier=0.65,
        key_crew_daily_travel_usd=280.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=155.0,
        per_diem_daily_usd=72.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Kentucky LA-relative cost benchmark. DISCOVERY tier.",
    ),

    # Canadian provinces
    CostBenchmarkEntry(
        jurisdiction_code="CA-AB",
        crew_rate_multiplier=0.72,
        equipment_rental_multiplier=0.70,
        stage_facility_multiplier=0.68,
        location_fees_multiplier=0.60,
        post_production_multiplier=0.72,
        vfx_multiplier=0.72,
        catering_multiplier=0.68,
        key_crew_daily_travel_usd=300.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=185.0,
        per_diem_daily_usd=85.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Calgary/Alberta LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="CA-MB",
        crew_rate_multiplier=0.65,
        equipment_rental_multiplier=0.62,
        stage_facility_multiplier=0.60,
        location_fees_multiplier=0.52,
        post_production_multiplier=0.65,
        vfx_multiplier=0.65,
        catering_multiplier=0.60,
        key_crew_daily_travel_usd=270.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=155.0,
        per_diem_daily_usd=72.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Winnipeg/Manitoba LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="CA-NS",
        crew_rate_multiplier=0.65,
        equipment_rental_multiplier=0.62,
        stage_facility_multiplier=0.60,
        location_fees_multiplier=0.55,
        post_production_multiplier=0.65,
        vfx_multiplier=0.65,
        catering_multiplier=0.62,
        key_crew_daily_travel_usd=280.0,
        marine_vessel_multiplier=0.65,
        lodging_daily_usd=160.0,
        per_diem_daily_usd=75.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Halifax/Nova Scotia LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="CA-NB",
        crew_rate_multiplier=0.62,
        equipment_rental_multiplier=0.60,
        stage_facility_multiplier=0.58,
        location_fees_multiplier=0.50,
        post_production_multiplier=0.62,
        vfx_multiplier=0.62,
        catering_multiplier=0.58,
        key_crew_daily_travel_usd=265.0,
        marine_vessel_multiplier=0.60,
        lodging_daily_usd=150.0,
        per_diem_daily_usd=70.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="New Brunswick LA-relative cost benchmark. DISCOVERY tier.",
    ),

    # European entries
    CostBenchmarkEntry(
        jurisdiction_code="NL",
        crew_rate_multiplier=0.88,
        equipment_rental_multiplier=0.85,
        stage_facility_multiplier=0.82,
        location_fees_multiplier=0.90,
        post_production_multiplier=0.88,
        vfx_multiplier=0.85,
        catering_multiplier=0.82,
        key_crew_daily_travel_usd=370.0,
        marine_vessel_multiplier=0.82,
        lodging_daily_usd=240.0,
        per_diem_daily_usd=100.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Amsterdam/Netherlands LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="AT",
        crew_rate_multiplier=0.85,
        equipment_rental_multiplier=0.82,
        stage_facility_multiplier=0.80,
        location_fees_multiplier=0.88,
        post_production_multiplier=0.85,
        vfx_multiplier=0.82,
        catering_multiplier=0.80,
        key_crew_daily_travel_usd=360.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=225.0,
        per_diem_daily_usd=98.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Vienna/Austria LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="CZ",
        crew_rate_multiplier=0.45,
        equipment_rental_multiplier=0.50,
        stage_facility_multiplier=0.55,
        location_fees_multiplier=0.40,
        post_production_multiplier=0.55,
        vfx_multiplier=0.55,
        catering_multiplier=0.45,
        key_crew_daily_travel_usd=260.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=130.0,
        per_diem_daily_usd=65.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Prague/Czech Republic LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="RO",
        crew_rate_multiplier=0.38,
        equipment_rental_multiplier=0.42,
        stage_facility_multiplier=0.45,
        location_fees_multiplier=0.32,
        post_production_multiplier=0.48,
        vfx_multiplier=0.50,
        catering_multiplier=0.38,
        key_crew_daily_travel_usd=240.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=110.0,
        per_diem_daily_usd=58.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Bucharest/Romania LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="PT",
        crew_rate_multiplier=0.60,
        equipment_rental_multiplier=0.62,
        stage_facility_multiplier=0.60,
        location_fees_multiplier=0.58,
        post_production_multiplier=0.65,
        vfx_multiplier=0.65,
        catering_multiplier=0.58,
        key_crew_daily_travel_usd=290.0,
        marine_vessel_multiplier=0.60,
        lodging_daily_usd=165.0,
        per_diem_daily_usd=78.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Lisbon/Portugal LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="RS",
        crew_rate_multiplier=0.35,
        equipment_rental_multiplier=0.40,
        stage_facility_multiplier=0.42,
        location_fees_multiplier=0.30,
        post_production_multiplier=0.45,
        vfx_multiplier=0.48,
        catering_multiplier=0.35,
        key_crew_daily_travel_usd=235.0,
        marine_vessel_multiplier=None,
        lodging_daily_usd=105.0,
        per_diem_daily_usd=55.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Belgrade/Serbia LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="IS",
        crew_rate_multiplier=0.95,
        equipment_rental_multiplier=0.90,
        stage_facility_multiplier=0.85,
        location_fees_multiplier=0.70,
        post_production_multiplier=0.90,
        vfx_multiplier=0.88,
        catering_multiplier=0.88,
        key_crew_daily_travel_usd=450.0,
        marine_vessel_multiplier=0.85,
        lodging_daily_usd=280.0,
        per_diem_daily_usd=115.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Reykjavik/Iceland LA-relative cost benchmark. High base costs offset by 25% incentive. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="GB-SCT",
        crew_rate_multiplier=0.85,
        equipment_rental_multiplier=0.82,
        stage_facility_multiplier=0.80,
        location_fees_multiplier=0.85,
        post_production_multiplier=0.85,
        vfx_multiplier=0.82,
        catering_multiplier=0.78,
        key_crew_daily_travel_usd=370.0,
        marine_vessel_multiplier=0.80,
        lodging_daily_usd=230.0,
        per_diem_daily_usd=100.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Edinburgh/Glasgow/Scotland LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="GB-WLS",
        crew_rate_multiplier=0.82,
        equipment_rental_multiplier=0.80,
        stage_facility_multiplier=0.78,
        location_fees_multiplier=0.78,
        post_production_multiplier=0.82,
        vfx_multiplier=0.80,
        catering_multiplier=0.75,
        key_crew_daily_travel_usd=360.0,
        marine_vessel_multiplier=0.78,
        lodging_daily_usd=215.0,
        per_diem_daily_usd=95.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Cardiff/Wales LA-relative cost benchmark. DISCOVERY tier.",
    ),

    # Asia-Pacific
    CostBenchmarkEntry(
        jurisdiction_code="SG",
        crew_rate_multiplier=0.72,
        equipment_rental_multiplier=0.70,
        stage_facility_multiplier=0.68,
        location_fees_multiplier=0.80,
        post_production_multiplier=0.72,
        vfx_multiplier=0.70,
        catering_multiplier=0.65,
        key_crew_daily_travel_usd=380.0,
        marine_vessel_multiplier=0.68,
        lodging_daily_usd=220.0,
        per_diem_daily_usd=90.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Singapore LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="AU-NSW",
        crew_rate_multiplier=0.80,
        equipment_rental_multiplier=0.75,
        stage_facility_multiplier=0.72,
        location_fees_multiplier=0.70,
        post_production_multiplier=0.75,
        vfx_multiplier=0.72,
        catering_multiplier=0.70,
        key_crew_daily_travel_usd=490.0,
        marine_vessel_multiplier=0.75,
        lodging_daily_usd=215.0,
        per_diem_daily_usd=95.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Sydney/NSW LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="AU-VIC",
        crew_rate_multiplier=0.78,
        equipment_rental_multiplier=0.74,
        stage_facility_multiplier=0.70,
        location_fees_multiplier=0.68,
        post_production_multiplier=0.74,
        vfx_multiplier=0.70,
        catering_multiplier=0.68,
        key_crew_daily_travel_usd=480.0,
        marine_vessel_multiplier=0.72,
        lodging_daily_usd=205.0,
        per_diem_daily_usd=92.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Melbourne/Victoria LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="AU-QLD",
        crew_rate_multiplier=0.74,
        equipment_rental_multiplier=0.70,
        stage_facility_multiplier=0.68,
        location_fees_multiplier=0.65,
        post_production_multiplier=0.70,
        vfx_multiplier=0.68,
        catering_multiplier=0.65,
        key_crew_daily_travel_usd=475.0,
        marine_vessel_multiplier=0.70,
        lodging_daily_usd=195.0,
        per_diem_daily_usd=88.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Gold Coast/Brisbane/Queensland LA-relative cost benchmark. DISCOVERY tier.",
    ),

    # Latin America
    CostBenchmarkEntry(
        jurisdiction_code="CO",
        crew_rate_multiplier=0.38,
        equipment_rental_multiplier=0.42,
        stage_facility_multiplier=0.40,
        location_fees_multiplier=0.30,
        post_production_multiplier=0.45,
        vfx_multiplier=0.48,
        catering_multiplier=0.35,
        key_crew_daily_travel_usd=250.0,
        marine_vessel_multiplier=0.38,
        lodging_daily_usd=110.0,
        per_diem_daily_usd=55.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Bogotá/Cartagena Colombia LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="DO",
        crew_rate_multiplier=0.35,
        equipment_rental_multiplier=0.40,
        stage_facility_multiplier=0.45,
        location_fees_multiplier=0.28,
        post_production_multiplier=0.42,
        vfx_multiplier=0.45,
        catering_multiplier=0.32,
        key_crew_daily_travel_usd=260.0,
        marine_vessel_multiplier=0.40,
        lodging_daily_usd=105.0,
        per_diem_daily_usd=52.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Santo Domingo/Dominican Republic LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="UY",
        crew_rate_multiplier=0.42,
        equipment_rental_multiplier=0.45,
        stage_facility_multiplier=0.42,
        location_fees_multiplier=0.35,
        post_production_multiplier=0.48,
        vfx_multiplier=0.50,
        catering_multiplier=0.40,
        key_crew_daily_travel_usd=255.0,
        marine_vessel_multiplier=0.42,
        lodging_daily_usd=115.0,
        per_diem_daily_usd=58.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Montevideo/Uruguay LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="AR",
        crew_rate_multiplier=0.28,
        equipment_rental_multiplier=0.35,
        stage_facility_multiplier=0.38,
        location_fees_multiplier=0.25,
        post_production_multiplier=0.38,
        vfx_multiplier=0.40,
        catering_multiplier=0.28,
        key_crew_daily_travel_usd=240.0,
        marine_vessel_multiplier=0.32,
        lodging_daily_usd=90.0,
        per_diem_daily_usd=45.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Buenos Aires/Argentina LA-relative cost benchmark. FX-volatile; ARS-based costs. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="BR",
        crew_rate_multiplier=0.40,
        equipment_rental_multiplier=0.45,
        stage_facility_multiplier=0.45,
        location_fees_multiplier=0.35,
        post_production_multiplier=0.48,
        vfx_multiplier=0.50,
        catering_multiplier=0.38,
        key_crew_daily_travel_usd=265.0,
        marine_vessel_multiplier=0.40,
        lodging_daily_usd=120.0,
        per_diem_daily_usd=60.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="São Paulo/Rio/Brazil LA-relative cost benchmark. FX-volatile; BRL-based costs. DISCOVERY tier.",
    ),

    # Middle East
    CostBenchmarkEntry(
        jurisdiction_code="AE",
        crew_rate_multiplier=0.72,
        equipment_rental_multiplier=0.70,
        stage_facility_multiplier=0.72,
        location_fees_multiplier=0.75,
        post_production_multiplier=0.68,
        vfx_multiplier=0.65,
        catering_multiplier=0.65,
        key_crew_daily_travel_usd=420.0,
        marine_vessel_multiplier=0.68,
        lodging_daily_usd=260.0,
        per_diem_daily_usd=105.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Dubai/Abu Dhabi UAE LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="SA",
        crew_rate_multiplier=0.68,
        equipment_rental_multiplier=0.65,
        stage_facility_multiplier=0.65,
        location_fees_multiplier=0.55,
        post_production_multiplier=0.62,
        vfx_multiplier=0.60,
        catering_multiplier=0.58,
        key_crew_daily_travel_usd=400.0,
        marine_vessel_multiplier=0.60,
        lodging_daily_usd=240.0,
        per_diem_daily_usd=95.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Riyadh/Neom/Saudi Arabia LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="JO",
        crew_rate_multiplier=0.40,
        equipment_rental_multiplier=0.45,
        stage_facility_multiplier=0.42,
        location_fees_multiplier=0.35,
        post_production_multiplier=0.48,
        vfx_multiplier=0.50,
        catering_multiplier=0.38,
        key_crew_daily_travel_usd=280.0,
        marine_vessel_multiplier=0.40,
        lodging_daily_usd=130.0,
        per_diem_daily_usd=62.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Amman/Petra/Wadi Rum Jordan LA-relative cost benchmark. DISCOVERY tier.",
    ),

    # Africa
    CostBenchmarkEntry(
        jurisdiction_code="MA",
        crew_rate_multiplier=0.32,
        equipment_rental_multiplier=0.38,
        stage_facility_multiplier=0.42,
        location_fees_multiplier=0.28,
        post_production_multiplier=0.42,
        vfx_multiplier=0.45,
        catering_multiplier=0.30,
        key_crew_daily_travel_usd=240.0,
        marine_vessel_multiplier=0.35,
        lodging_daily_usd=100.0,
        per_diem_daily_usd=52.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Ouarzazate/Marrakech/Casablanca Morocco LA-relative cost benchmark. DISCOVERY tier.",
    ),
    CostBenchmarkEntry(
        jurisdiction_code="ZA",
        crew_rate_multiplier=0.35,
        equipment_rental_multiplier=0.40,
        stage_facility_multiplier=0.42,
        location_fees_multiplier=0.30,
        post_production_multiplier=0.45,
        vfx_multiplier=0.48,
        catering_multiplier=0.32,
        key_crew_daily_travel_usd=255.0,
        marine_vessel_multiplier=0.38,
        lodging_daily_usd=110.0,
        per_diem_daily_usd=55.0,
        confidence_tier=_DISC,
        data_source=_BM_SOURCE,
        as_of_date=_BM_DATE,
        notes="Cape Town/Johannesburg/South Africa LA-relative cost benchmark. DISCOVERY tier.",
    ),
]


# Public exports — concatenate in global_inventory.py
EXTENDED_PROGRAMS: list[GlobalProgramEntry] = _EXTENDED_PROGRAMS
EXTENDED_BENCHMARKS: list[CostBenchmarkEntry] = _EXTENDED_BENCHMARKS
