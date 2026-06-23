"""Phase A-D Final Sweep: special category programs and extended fund economics.

Revision ID: 0056
Revises: 0055
Create Date: 2026-06-23

Adds:
- 42 new programs from global_inventory_special_categories (VFX/post, export,
  workforce, streamers, tourism, airline, cultural ministry, special regional)
- 154 new fund_economics records covering all slugs without prior coverage
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = "0056"
down_revision = "0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. New programs (UPSERT by jurisdiction_code + program_name)
    # ------------------------------------------------------------------
    _NEW_PROGRAMS = [
        # VFX / Post / Animation
        ("AU", "Australia", "Post, Digital and Visual Effects (PDV) Offset",
         "cash_rebate", 30.0, 30.0, True, False, 500_000, None, False, True, "PARSED"),
        ("NZ", "New Zealand", "New Zealand Screen Production Grant — International Post/VFX",
         "cash_rebate", 20.0, 25.0, True, False, None, None, False, True, "DISCOVERY"),
        ("CA-ON", "Ontario, Canada", "Ontario Computer Animation and Special Effects Tax Credit (OCASE)",
         "tax_credit", 18.0, 18.0, True, False, None, None, False, True, "PARSED"),
        ("CA-BC", "British Columbia, Canada", "BC Interactive Digital Media Tax Credit (IDMTC)",
         "tax_credit", 17.5, 17.5, True, False, None, None, False, True, "PARSED"),
        ("IS", "Iceland", "Iceland Post-Production, Visual Effects and Animation Incentive",
         "cash_rebate", 25.0, 25.0, True, False, None, None, False, True, "DISCOVERY"),
        ("SG", "Singapore", "Singapore IMDA Digital Media Development Fund",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("KR", "South Korea", "Korea KOCCA Animation Production Support",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("FR", "France", "CNC Animation Production Fund",
         "co_production_fund", None, None, False, False, None, None, True, True, "DISCOVERY"),
        ("JP", "Japan", "VIPO Animation and Content Support",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        # Export Promotion
        ("GB", "United Kingdom", "BFI International Export Fund",
         "direct_grant", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("FR", "France", "UniFrance International Export Support",
         "direct_grant", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("DE", "Germany", "German Films International Market Development",
         "direct_grant", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("IT", "Italy", "ANICA/MiC International Export Support",
         "direct_grant", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("CA", "Canada", "Telefilm Canada Export Development Program",
         "direct_grant", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("KR", "South Korea", "KOFIC International Promotion and Export",
         "direct_grant", None, None, False, False, None, None, False, False, "DISCOVERY"),
        # Workforce / Training
        ("GB", "United Kingdom", "ScreenSkills Production Workforce Development",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("AU", "Australia", "Screen Australia Talent Fund",
         "direct_grant", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("IE", "Ireland", "Screen Ireland Development and Talent Fund",
         "direct_grant", None, None, False, False, None, None, True, True, "DISCOVERY"),
        # Streamer Obligations
        ("EU", "European Union", "AVMSD Streamer Local Content Obligation",
         "production_support", None, None, False, False, None, None, False, False, "PARSED"),
        ("FR", "France", "SVOD Chronologie des Médias Local Content Obligation",
         "production_support", None, None, False, False, None, None, False, False, "PARSED"),
        ("AU", "Australia", "Australian Content Standard (Streamers)",
         "production_support", None, None, False, False, None, None, False, False, "PARSED"),
        ("CA", "Canada", "CRTC Online Streaming Act Local Content Obligation",
         "production_support", None, None, False, False, None, None, False, False, "PARSED"),
        # Tourism Board Support
        ("AU", "Australia", "Tourism Australia Film and Production Support",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("NZ", "New Zealand", "Tourism New Zealand Film and Production Support",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("IE", "Ireland", "Tourism Ireland / Fáilte Ireland Production Support",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("JO", "Jordan", "Royal Film Commission Tourism Film Support",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("MA", "Morocco", "CCM Tourism Film Facilitation",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        # Airline Support
        ("AE", "United Arab Emirates", "Emirates Airline Film Production Partnership",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("NZ", "New Zealand", "Air New Zealand Film Production Support",
         "production_support", None, None, False, False, None, None, False, False, "DISCOVERY"),
        # Cultural Ministry Grants (remaining)
        ("GR", "Greece", "Greek Film Centre — National Production Grants",
         "direct_grant", None, None, False, False, None, None, True, True, "DISCOVERY"),
        ("SA", "Saudi Arabia", "Saudi Film Commission Development Grants",
         "direct_grant", None, None, False, False, None, None, False, False, "DISCOVERY"),
        ("TR", "Turkey", "Turkey Ministry of Culture Cinema Support Fund",
         "direct_grant", None, None, False, False, None, None, False, False, "DISCOVERY"),
        # Special Regional
        ("SE-SK", "Skåne, Sweden", "Film i Skåne Regional Production Fund",
         "regional_fund", None, None, False, False, None, 550_000, False, False, "DISCOVERY"),
        ("SE-AB", "Stockholm, Sweden", "Filmregion Stockholm-Mälardalen",
         "regional_fund", None, None, False, False, None, 550_000, False, False, "DISCOVERY"),
        ("NO-ROG", "Rogaland, Norway", "Vestnorsk Filmsenter",
         "regional_fund", None, None, False, False, None, 400_000, False, False, "DISCOVERY"),
        ("NO-TRO", "Troms, Norway", "Nord Norsk Filmsenter",
         "regional_fund", None, None, False, False, None, 400_000, False, False, "DISCOVERY"),
        ("DK-CPH", "Copenhagen, Denmark", "Copenhagen Film Fund",
         "regional_fund", None, None, False, False, None, 550_000, False, False, "DISCOVERY"),
        ("AU-TAS", "Tasmania, Australia", "Screen Tasmania",
         "regional_fund", None, None, False, False, None, 300_000, False, True, "DISCOVERY"),
        ("AU-NT", "Northern Territory, Australia", "Territory Screen Office",
         "regional_fund", None, None, False, False, None, 300_000, False, True, "DISCOVERY"),
        ("GB-LON", "London, United Kingdom", "Film London Production Fund",
         "regional_fund", None, None, False, False, None, 550_000, False, False, "DISCOVERY"),
        ("CA-PE", "Prince Edward Island, Canada", "Film PEI Production Support",
         "regional_fund", None, None, False, False, None, None, False, True, "DISCOVERY"),
        ("CA-MB", "Manitoba, Canada", "Manitoba Film & Music Production Support Grants",
         "direct_grant", None, None, False, False, None, 550_000, False, False, "DISCOVERY"),
    ]

    for row in _NEW_PROGRAMS:
        (jcode, jname, pname, ptype, brate, mrate, refund, transfer,
         mspend, acap, cult_test, local_ent, conf) = row
        conn.execute(text("""
            INSERT INTO incentive_programs
                (jurisdiction_code, jurisdiction_name, program_name, program_type,
                 base_rate, max_rate, is_refundable, is_transferable,
                 min_spend_usd, annual_cap_usd, requires_cultural_test,
                 requires_local_entity, confidence_tier)
            VALUES
                (:jcode, :jname, :pname, :ptype,
                 :brate, :mrate, :refund, :transfer,
                 :mspend, :acap, :cult, :local_ent, :conf)
            ON CONFLICT (jurisdiction_code, program_name) DO UPDATE SET
                program_type = EXCLUDED.program_type,
                base_rate = EXCLUDED.base_rate,
                max_rate = EXCLUDED.max_rate,
                is_refundable = EXCLUDED.is_refundable,
                confidence_tier = EXCLUDED.confidence_tier
        """), {
            "jcode": jcode, "jname": jname, "pname": pname, "ptype": ptype,
            "brate": brate, "mrate": mrate, "refund": refund, "transfer": transfer,
            "mspend": mspend, "acap": acap, "cult": cult_test,
            "local_ent": local_ent, "conf": conf,
        })

    # ------------------------------------------------------------------
    # 2. Fund economics UPSERT for all new slugs
    # ------------------------------------------------------------------
    # Format: (slug, classification, is_repayable, is_recoupable,
    #          has_equity, is_soft_money, is_govt_assistance, typical_max_usd, notes)
    _FUND_ECON = [
        # Cash rebates
        ("cy_film_rebate", "rebate", False, False, False, True, True, 3_500_000, "Cyprus 35% rebate. Govt assistance."),
        ("hu_hipa_rebate", "rebate", False, False, False, True, True, None, "Hungary HIPA 30% rebate. Govt assistance."),
        ("nz_nzspg", "rebate", False, False, False, True, True, None, "NZ NZSPG 20%+5%. Govt assistance."),
        ("nz_pdv_rebate", "rebate", False, False, False, True, True, None, "NZ PDV post rebate. Govt assistance."),
        ("au_nsw_screen", "rebate", False, False, False, True, True, 4_000_000, "Screen NSW attraction fund. Govt assistance."),
        ("au_nsw_screen_fund", "rebate", False, False, False, True, True, 4_000_000, "Screen NSW production fund. Govt assistance."),
        ("au_vic_vicscreen", "rebate", False, False, False, True, True, 3_000_000, "VicScreen production investment. Govt assistance."),
        ("au_qld_screen", "rebate", False, False, False, True, True, 2_500_000, "Screen QLD attraction. Govt assistance."),
        ("nl_nfpi", "rebate", False, False, False, True, True, None, "Netherlands NFPI 30%. Govt assistance."),
        ("at_fisa_plus", "rebate", False, False, False, True, True, 4_000_000, "Austria FISA+ 25-35%. Govt assistance."),
        ("cz_film_incentive", "rebate", False, False, False, True, True, None, "Czech Incentive 20%. Govt assistance."),
        ("ro_film_rebate", "rebate", False, False, False, True, True, None, "Romania 35% rebate. Govt assistance."),
        ("pt_film_incentive", "rebate", False, False, False, True, True, None, "Portugal 25% incentive. Govt assistance."),
        ("rs_film_rebate", "rebate", False, False, False, True, True, None, "Serbia 25% rebate. Govt assistance."),
        ("is_film_rebate", "rebate", False, False, False, True, True, None, "Iceland 25% rebate. Govt assistance."),
        ("is_post_rebate", "rebate", False, False, False, True, True, None, "Iceland post/VFX 25% rebate. Govt assistance."),
        ("gb_sct_screen_production", "rebate", False, False, False, True, True, 2_000_000, "Screen Scotland location fund. Govt assistance."),
        ("gb_wls_film_fund", "rebate", False, False, False, True, True, 1_200_000, "Wales Film Fund. Govt assistance."),
        ("se_film_rebate", "rebate", False, False, False, True, True, None, "Sweden SFI 25% rebate. Govt assistance."),
        ("no_film_incentive", "rebate", False, False, False, True, True, None, "Norway NFI 25% rebate. Govt assistance."),
        ("ee_film_estonia", "rebate", False, False, False, True, True, None, "Estonia 30% rebate. Govt assistance."),
        ("lt_lcc_rebate", "rebate", False, False, False, True, True, None, "Lithuania 30% rebate. Govt assistance."),
        ("lv_nkmp_rebate", "rebate", False, False, False, True, True, None, "Latvia 30% rebate. Govt assistance."),
        ("sk_avf_incentive", "rebate", False, False, False, True, True, None, "Slovakia AVF 33% rebate. Govt assistance."),
        ("si_sfc_rebate", "rebate", False, False, False, True, True, None, "Slovenia 25% rebate. Govt assistance."),
        ("al_anca_rebate", "rebate", False, False, False, True, True, None, "Albania ANCA rebate. Rate UNKNOWN."),
        ("me_film_rebate", "rebate", False, False, False, True, True, None, "Montenegro rebate. Rate UNKNOWN."),
        ("mk_mfa_rebate", "rebate", False, False, False, True, True, None, "N. Macedonia rebate. Rate UNKNOWN."),
        ("ge_gnfc_rebate", "rebate", False, False, False, True, True, None, "Georgia rebate. Rate UNKNOWN."),
        ("tr_cinema_support", "rebate", False, False, False, True, True, None, "Turkey cinema support. Rate UNKNOWN."),
        ("ae_dxb_dpi", "rebate", False, False, False, True, True, None, "Dubai DPI 30% rebate. Govt assistance."),
        ("ae_adfc_rebate", "rebate", False, False, False, True, True, None, "Abu Dhabi ADFC 30% rebate. Govt assistance."),
        ("sa_sfc_rebate", "rebate", False, False, False, True, True, None, "Saudi SFC rebate. Rate UNKNOWN."),
        ("jo_rfc_rebate", "rebate", False, False, False, True, True, None, "Jordan RFC 15% rebate. Govt assistance."),
        ("qa_film_rebate", "rebate", False, False, False, True, True, None, "Qatar film support. Rate UNKNOWN."),
        ("il_maslool_rebate", "rebate", False, False, False, True, True, None, "Israel Maslool 30% rebate. Govt assistance."),
        ("ma_ccm_rebate", "rebate", False, False, False, True, True, None, "Morocco CCM rebate. Rate UNKNOWN."),
        ("tn_cnci_rebate", "rebate", False, False, False, True, True, None, "Tunisia CNCI rebate. Rate UNKNOWN."),
        ("ke_kfc_rebate", "rebate", False, False, False, True, True, None, "Kenya KFC rebate. Rate UNKNOWN."),
        ("za_dti_film_rebate", "rebate", False, False, False, True, True, None, "South Africa DTI 20-25% rebate. Govt assistance."),
        ("na_nfc_rebate", "rebate", False, False, False, True, True, None, "Namibia NFC incentive. Rate UNKNOWN."),
        ("sg_sfc_production", "rebate", False, False, False, True, True, None, "Singapore SFC rebate. Rate UNKNOWN."),
        ("my_finas_rebate", "rebate", False, False, False, True, True, None, "Malaysia FINAS rebate. Rate UNKNOWN."),
        ("ph_fdcp_incentive", "rebate", False, False, False, True, True, None, "Philippines FDCP incentive. Rate UNKNOWN."),
        ("kr_kofic_location", "rebate", False, False, False, True, True, None, "Korea KOFIC location incentive. Rate UNKNOWN."),
        ("tw_tfai_rebate", "rebate", False, False, False, True, True, None, "Taiwan TFAI rebate. Rate UNKNOWN."),
        ("lk_film_rebate", "rebate", False, False, False, True, True, None, "Sri Lanka film rebate. Rate UNKNOWN."),
        ("th_boi_film", "rebate", False, False, False, True, True, None, "Thailand BOI 20% rebate. Govt assistance."),
        ("jp_jloc_incentive", "rebate", False, False, False, True, True, None, "Japan JLOC up to 25%. Govt assistance."),
        ("ar_incaa_rebate", "rebate", False, False, False, True, True, None, "Argentina INCAA rebate. Rate UNKNOWN."),
        ("cl_corfo_rebate", "rebate", False, False, False, True, True, None, "Chile CORFO 30% rebate. Govt assistance."),
        ("co_film_rebate", "rebate", False, False, False, True, True, None, "Colombia ~20% rebate. Govt assistance."),
        ("do_film_rebate", "rebate", False, False, False, True, True, None, "Dominican Republic 25% rebate. Govt assistance."),
        ("uy_film_rebate", "rebate", False, False, False, True, True, None, "Uruguay ICAU rebate. Rate UNKNOWN."),
        ("ca_ns_film_incentive", "rebate", False, False, False, True, True, None, "Nova Scotia 25% rebate. Govt assistance."),
        # US states
        ("us_or_opif", "rebate", False, False, False, True, True, 14_000_000, "Oregon OPIF 20%. Govt assistance."),
        ("us_wa_mpcp", "rebate", False, False, False, True, True, 3_500_000, "Washington MPCP 15-30%. Govt assistance."),
        ("us_nc_film_grant", "rebate", False, False, False, True, True, 31_000_000, "North Carolina grant 25%. Govt assistance."),
        ("us_tx_miip", "rebate", False, False, False, True, True, 22_500_000, "Texas MIIP 5-22.5%. Govt assistance."),
        ("us_co_film_incentive", "rebate", False, False, False, True, True, 5_000_000, "Colorado 20% incentive. Govt assistance."),
        ("us_tn_film_incentive", "rebate", False, False, False, True, True, None, "Tennessee 25% incentive. Govt assistance."),
        ("us_ok_film_rebate", "rebate", False, False, False, True, True, 8_000_000, "Oklahoma 35-37% rebate. Govt assistance."),
        ("us_ut_film_incentive", "rebate", False, False, False, True, True, None, "Utah 20-25% incentive. Govt assistance."),
        ("us_az_film_incentive", "rebate", False, False, False, True, True, None, "Arizona 15-20% tax credit. Govt assistance."),
        # VFX / animation
        ("au_pdv_offset", "rebate", False, False, False, True, True, None, "AU PDV Offset 30%. Govt assistance."),
        ("ca_on_ocase", "tax_credit", False, False, False, True, True, None, "Ontario OCASE 18%. Govt assistance."),
        ("ca_bc_idmtc", "tax_credit", False, False, False, True, True, None, "BC IDMTC 17.5%. Govt assistance."),
        ("sg_imda_digital", "grant", False, False, False, True, True, 500_000, "Singapore IMDA digital fund. Govt assistance."),
        ("kr_kocca_animation", "grant", False, False, False, True, True, 500_000, "Korea KOCCA animation. Govt assistance."),
        ("fr_cnc_animation", "grant", True, True, False, True, True, 1_200_000, "CNC animation fund. Recoupable. Govt assistance."),
        ("jp_vipo_animation", "grant", False, False, False, True, True, 200_000, "Japan VIPO animation. Govt assistance."),
        # Export
        ("gb_bfi_international", "grant", False, False, False, True, False, 100_000, "BFI International export. Not govt assistance."),
        ("fr_unifrance", "grant", False, False, False, True, False, 150_000, "UniFrance export. Not govt assistance."),
        ("de_german_films", "grant", False, False, False, True, False, 100_000, "German Films export. Not govt assistance."),
        ("it_anica_export", "grant", False, False, False, True, False, 100_000, "ANICA/MiC export. Not govt assistance."),
        ("ca_telefilm_export", "grant", False, False, False, True, True, 200_000, "Telefilm export. Govt assistance."),
        ("au_screen_international", "grant", False, False, False, True, True, 150_000, "Screen Australia International. Govt assistance."),
        ("es_icaa_export", "grant", False, False, False, True, False, 100_000, "Spain ICAA export. Not govt assistance."),
        ("kr_kofic_export", "grant", False, False, False, True, True, 150_000, "KOFIC export. Govt assistance."),
        # Workforce
        ("gb_screenskills", "grant", False, False, False, True, False, 50_000, "ScreenSkills UK. Not govt assistance."),
        ("au_screen_talent", "grant", False, False, False, True, True, 100_000, "Screen Australia Talent. Govt assistance."),
        ("ie_screen_ireland_dev", "grant", False, False, False, True, True, 100_000, "Screen Ireland dev/talent. Govt assistance."),
        # Tourism
        ("au_tourism_film", "grant", False, False, False, True, True, 500_000, "Tourism Australia film support. Govt assistance."),
        ("nz_tourism_film", "grant", False, False, False, True, True, 500_000, "Tourism NZ film support. Govt assistance."),
        ("ie_tourism_film", "grant", False, False, False, True, True, 300_000, "Tourism Ireland/Fáilte. Govt assistance."),
        ("jo_rfc_tourism", "grant", False, False, False, True, True, 200_000, "Jordan RFC tourism support. Govt assistance."),
        ("mv_tourism_film", "grant", False, False, False, True, True, 100_000, "Maldives tourism film. Govt assistance."),
        ("sc_tourism_film", "grant", False, False, False, True, True, 100_000, "Seychelles tourism film. Govt assistance."),
        ("fj_tourism_film", "grant", False, False, False, True, True, 100_000, "Fiji tourism film. Govt assistance."),
        # Airline
        ("ae_emirates_support", "grant", False, False, False, True, False, None, "Emirates airline support. Non-financial. Not govt assistance."),
        ("nz_air_production", "grant", False, False, False, True, False, None, "Air NZ support. Non-financial. Not govt assistance."),
        # National/cultural remaining
        ("gr_gnf_grants", "grant", False, False, False, True, False, 550_000, "Greek Film Centre grants. Eurimages member."),
        ("sa_sfc_grants", "grant", False, False, False, True, True, None, "Saudi SFC grants. Govt assistance."),
        ("it_mic_national", "grant", True, True, False, True, True, 2_000_000, "Italy MiC national fund. Recoupable. Govt assistance."),
        ("de_ffa", "loan", True, True, False, False, True, 1_500_000, "German FFA reference fund. Repayable. Govt assistance."),
        ("de_wdr_ard", "advance", True, True, False, True, False, 1_000_000, "WDR/ARD broadcaster advance. Soft. Not govt assistance."),
        ("fi_business_finland", "grant", False, False, False, True, True, 500_000, "Business Finland AV grant. Govt assistance."),
        ("hk_createhk", "grant", False, False, False, True, True, 500_000, "HK CreateHK grant. Govt assistance."),
        ("cn_film_coproduction", "grant", False, False, False, True, True, None, "China NRTA co-production. Govt assistance. Treaty only."),
        ("streamer_uk_local", "grant", False, False, False, True, False, None, "UK streamer obligation. Regulatory spend requirement."),
        # Norwegian regional
        ("no_vgn_viken", "grant", False, False, False, True, False, 550_000, "Viken Film regional grant."),
        ("no_inl_midtnorsk", "grant", False, False, False, True, False, 400_000, "Midtnorsk Filmsenter grant."),
        ("no_rog_vestnorsk", "grant", False, False, False, True, False, 400_000, "Vestnorsk Filmsenter grant."),
        ("no_tro_nordnorsk", "grant", False, False, False, True, False, 400_000, "Nord Norsk Filmsenter grant."),
        ("no_mro_film3", "grant", False, False, False, True, False, 350_000, "Film3 regional grant."),
        # Swedish/Danish regional
        ("se_sk_film_skane", "grant", False, False, False, True, False, 550_000, "Film i Skåne regional grant."),
        ("se_ab_filmstockholm", "grant", False, False, False, True, False, 550_000, "Filmregion Stockholm regional grant."),
        ("dk_cph_film_fund", "grant", False, False, False, True, False, 550_000, "Copenhagen Film Fund regional grant."),
        ("dk_fyn_film", "grant", False, False, False, True, False, 350_000, "Film Fyn regional grant."),
        # Australian state
        ("au_vic_film_victoria", "grant", False, False, False, True, True, 1_000_000, "Film Victoria/VicScreen grants. Govt assistance."),
        ("au_tas_screen", "grant", False, False, False, True, True, 300_000, "Screen Tasmania grants. Govt assistance."),
        ("au_nt_territory", "grant", False, False, False, True, True, 300_000, "Territory Screen Office grants. Govt assistance."),
        ("au_miff_premiere", "grant", False, False, False, True, False, 100_000, "MIFF Premiere Fund. Not govt assistance."),
        # UK regional
        ("gb_lon_film_london", "grant", False, False, False, True, True, 550_000, "Film London fund. Govt assistance."),
        ("gb_film_hub_midlands", "grant", False, False, False, True, True, 100_000, "Film Hub Midlands. Govt assistance."),
        # Canadian provincial
        ("ca_pe_film_pei", "rebate", False, False, False, True, True, None, "Film PEI rebate/grant. Govt assistance."),
        ("ca_mb_film_mb", "grant", False, False, False, True, True, 550_000, "Manitoba Film & Music grants. Govt assistance."),
        ("ca_nb_film_nb", "grant", False, False, False, True, True, 300_000, "NB Film grants. Govt assistance."),
        ("ca_nl_film_nl", "grant", False, False, False, True, True, 300_000, "NL Film Corp grants. Govt assistance."),
        # Film commission facilitation
        ("bs_film_commission", "grant", False, False, False, True, False, None, "Bahamas Film Commission. Facilitation only."),
        ("bb_film_commission", "grant", False, False, False, True, False, None, "Barbados Film Commission. Facilitation only."),
        ("pa_film_commission", "grant", False, False, False, True, False, None, "Panama Film Commission. Facilitation only."),
        ("cr_film_commission", "grant", False, False, False, True, False, None, "Costa Rica Film Commission. Facilitation only."),
        ("ec_film_commission", "grant", False, False, False, True, False, None, "Ecuador Film Commission. Facilitation only."),
        ("eg_film_commission", "grant", False, False, False, True, False, None, "Egypt Film Commission. Facilitation only."),
        ("gh_film_commission", "grant", False, False, False, True, False, None, "Ghana Film Authority. Facilitation only."),
        ("rw_film_commission", "grant", False, False, False, True, False, None, "Rwanda Film Commission. Facilitation only."),
        ("tz_film_commission", "grant", False, False, False, True, False, None, "Tanzania Film Board. Facilitation only."),
        ("sn_film_commission", "grant", False, False, False, True, False, None, "Senegal film bureau. Facilitation only."),
        ("kw_film_commission", "grant", False, False, False, True, False, None, "Kuwait film bureau. Facilitation only."),
        ("bh_film_commission", "grant", False, False, False, True, False, None, "Bahrain film support. Facilitation only."),
        ("kz_film_commission", "grant", False, False, False, True, False, None, "Kazakhstan/Kazakhfilm. Facilitation only."),
        ("vn_film_commission", "grant", False, False, False, True, False, None, "Vietnam Film Dept. Facilitation only."),
        ("id_film_commission", "grant", False, False, False, True, False, None, "Indonesia BPIFB. Facilitation only."),
        ("kh_film_commission", "grant", False, False, False, True, False, None, "Cambodia Dept of Cinema. Facilitation only."),
        ("fj_film_commission", "grant", False, False, False, True, False, None, "Fiji Audio Visual Commission. Facilitation only."),
        ("uz_film_commission", "grant", False, False, False, True, False, None, "Uzbekistan/Uzbekkino. Facilitation only."),
        ("om_film_commission", "grant", False, False, False, True, False, None, "Oman Film Centre. Facilitation only."),
        ("gy_film_commission", "grant", False, False, False, True, False, None, "Guyana film commission. Facilitation only."),
        ("gt_film_commission", "grant", False, False, False, True, False, None, "Guatemala film commission. Facilitation only."),
        ("bw_film_commission", "grant", False, False, False, True, False, None, "Botswana film commission. Facilitation only."),
        ("et_film_commission", "grant", False, False, False, True, False, None, "Ethiopia Film Commission. Facilitation only."),
        ("ug_film_commission", "grant", False, False, False, True, False, None, "Uganda Film Commission. Facilitation only."),
        ("mz_film_commission", "grant", False, False, False, True, False, None, "Mozambique film commission. Facilitation only."),
        ("zm_film_commission", "grant", False, False, False, True, False, None, "Zambia NAC film. Facilitation only."),
        ("zw_film_commission", "grant", False, False, False, True, False, None, "Zimbabwe ZFTA. Facilitation only."),
        ("ga_film_commission", "grant", False, False, False, True, False, None, "Gabon film commission. Facilitation only."),
        ("sc_film_commission", "grant", False, False, False, True, False, None, "Seychelles film commission. Facilitation only."),
        ("mn_film_commission", "grant", False, False, False, True, False, None, "Mongolia film commission. Facilitation only."),
        ("bd_film_commission", "grant", False, False, False, True, False, None, "Bangladesh BFDC. Facilitation only."),
        ("by_film_commission", "grant", False, False, False, True, False, None, "Belarus/Belarusfilm. Facilitation only."),
        ("bt_film_commission", "grant", False, False, False, True, False, None, "Bhutan film commission. Facilitation only."),
        ("mv_film_commission", "grant", False, False, False, True, False, None, "Maldives film commission. Facilitation only."),
        ("ba_film_centre", "grant", False, False, False, True, False, 300_000, "Bosnia BHFF grants. Eurimages member."),
        ("hk_createhk", "grant", False, False, False, True, True, 500_000, "HK CreateHK. Govt assistance."),
        ("cn_film_coproduction", "grant", False, False, False, True, True, None, "China NRTA co-production. Govt assistance."),
    ]

    for row in _FUND_ECON:
        (slug, classif, repayable, recoup, equity, soft, govt_assist, max_usd, notes_txt) = row
        conn.execute(text("""
            INSERT INTO fund_economics
                (program_slug, classification, is_repayable, is_recoupable,
                 has_equity_participation, is_soft_money, is_government_assistance,
                 typical_max_award_usd, notes)
            VALUES
                (:slug, :cls, :repay, :recoup, :equity, :soft, :govt, :maxusd, :notes)
            ON CONFLICT (program_slug) DO UPDATE SET
                classification = EXCLUDED.classification,
                is_repayable = EXCLUDED.is_repayable,
                is_government_assistance = EXCLUDED.is_government_assistance,
                typical_max_award_usd = EXCLUDED.typical_max_award_usd,
                notes = EXCLUDED.notes
        """), {
            "slug": slug, "cls": classif, "repay": repayable, "recoup": recoup,
            "equity": equity, "soft": soft, "govt": govt_assist,
            "maxusd": max_usd, "notes": notes_txt,
        })


def downgrade() -> None:
    pass
