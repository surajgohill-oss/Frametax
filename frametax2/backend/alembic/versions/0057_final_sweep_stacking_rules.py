"""Phase A-D Final Sweep: stacking rules for new programs.

Revision ID: 0057
Revises: 0056
Create Date: 2026-06-23

Adds stacking interaction rules for:
- VFX/post incentives × national incentives
- Regional funds × national funds (NO, SE, DK, AU state, UK, CA provincial)
- Tourism support × national incentives
- Export/workforce × national incentives
- Cash rebates (new jurisdictions) × Eurimages/Ibermedia
- Film commission facilitation × national incentives (all allowed)
- Streamer obligations × broadcaster co-production programs
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "0057"
down_revision = "0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Stacking rules: (slug_a, slug_b, rule_type, condition_text, confidence_tier)
    _RULES = [
        # ------------------------------------------------------------------
        # VFX/Post × national tax credits / rebates
        # ------------------------------------------------------------------
        ("au_pdv_offset", "au_location_offset",
         "conditional",
         "AU PDV Offset and AU Location Offset may be combined if expenditure "
         "categories are distinct. PDV rebate is govt assistance reducing QAPE basis "
         "for Location Offset. Specialist accounting required.",
         "PARSED"),
        ("au_pdv_offset", "au_producer_offset",
         "conditional",
         "AU PDV Offset is govt assistance — reduces QAPE for AU Producer Offset calculation. "
         "Cannot double-count the same expenditure across both programs.",
         "PARSED"),
        ("au_pdv_offset", "au_screen_production",
         "conditional",
         "PDV Offset is govt assistance reducing basis for Screen Australia production grants. "
         "Separate accounting required for PDV vs principal photography spend.",
         "DISCOVERY"),
        ("nz_pdv_rebate", "nz_nzspg",
         "conditional",
         "NZ PDV rebate and NZ International SPGI may be combined if spend basis is distinct. "
         "UNKNOWN: whether PDV-only applications preclude NZSPG on same project.",
         "DISCOVERY"),
        ("ca_on_ocase", "on_ofttc",
         "conditional",
         "Ontario OCASE and OFTTC can be combined: OCASE covers animation/VFX labour; "
         "OFTTC covers broader production labour. OCASE is govt assistance — reduces OFTTC labour basis.",
         "PARSED"),
        ("ca_on_ocase", "ca_federal_cptc",
         "conditional",
         "Ontario OCASE (18% animation/VFX) stacks with federal CPTC. "
         "OCASE is govt assistance — reduces qualifying labour for CPTC calculation.",
         "PARSED"),
        ("ca_bc_idmtc", "ca_bc_pstc",
         "conditional",
         "BC IDMTC (interactive digital media/VFX) and BC PSTC (production) may be combined "
         "if qualifying expenditure categories are distinct. IDMTC is govt assistance.",
         "PARSED"),
        ("ca_bc_idmtc", "ca_federal_cptc",
         "conditional",
         "BC IDMTC stacks with federal CPTC. IDMTC is govt assistance — reduces CPTC labour basis.",
         "PARSED"),
        ("is_post_rebate", "is_film_rebate",
         "conditional",
         "Iceland post/VFX rebate and location rebate may be combined on same project "
         "if expenditure categories are distinct. Both are govt assistance.",
         "DISCOVERY"),
        ("fr_cnc_animation", "fr_trip",
         "spend_reduction",
         "French CNC animation fund is govt assistance — reduces TRIP qualifying expenditure basis. "
         "Net TRIP value reduced by CNC animation award amount.",
         "PARSED"),
        ("fr_cnc_animation", "fr_cnc_production",
         "conditional",
         "CNC animation fund and CNC general production fund (COSIP) are administered separately. "
         "May be combined for animation-heavy co-productions. CNC allocates by program type.",
         "DISCOVERY"),
        ("sg_imda_digital", "sg_sfc_production",
         "conditional",
         "Singapore IMDA digital fund and SFC production rebate may be available on same project "
         "for qualifying digital content productions. Separate application tracks.",
         "DISCOVERY"),
        ("kr_kocca_animation", "kr_kofic_location",
         "conditional",
         "Korea KOCCA animation and KOFIC location incentive may both be available for "
         "animation productions with Korean filming. UNKNOWN: mutual exclusivity rules.",
         "DISCOVERY"),
        ("jp_vipo_animation", "jp_jloc_incentive",
         "conditional",
         "Japan VIPO animation support and JLOC location incentive may both apply to "
         "animation co-productions with Japan. UNKNOWN: interaction details.",
         "DISCOVERY"),
        # ------------------------------------------------------------------
        # Norwegian regional × national
        # ------------------------------------------------------------------
        ("no_vgn_viken", "no_nfi_grants",
         "allowed",
         "Viken Film regional grant stacks with NFI national grants. Regional spend triggers "
         "regional eligibility; national grant is assessed separately by NFI.",
         "PARSED"),
        ("no_inl_midtnorsk", "no_nfi_grants",
         "allowed",
         "Midtnorsk Filmsenter regional grant stacks with NFI national grants.",
         "PARSED"),
        ("no_rog_vestnorsk", "no_nfi_grants",
         "allowed",
         "Vestnorsk Filmsenter regional grant stacks with NFI national grants.",
         "PARSED"),
        ("no_tro_nordnorsk", "no_nfi_grants",
         "allowed",
         "Nord Norsk Filmsenter regional grant stacks with NFI national grants.",
         "PARSED"),
        ("no_mro_film3", "no_nfi_grants",
         "allowed",
         "Film3 regional grant stacks with NFI national grants.",
         "PARSED"),
        ("no_vgn_viken", "no_film_incentive",
         "allowed",
         "Viken Film regional grant stacks with Norway film rebate (location incentive).",
         "DISCOVERY"),
        ("no_inl_midtnorsk", "no_film_incentive",
         "allowed",
         "Midtnorsk regional grant stacks with Norway film rebate.",
         "DISCOVERY"),
        ("no_rog_vestnorsk", "no_film_incentive",
         "allowed",
         "Vestnorsk regional grant stacks with Norway film rebate.",
         "DISCOVERY"),
        ("no_tro_nordnorsk", "no_film_incentive",
         "allowed",
         "Nord Norsk regional grant stacks with Norway film rebate.",
         "DISCOVERY"),
        ("no_mro_film3", "no_film_incentive",
         "allowed",
         "Film3 regional grant stacks with Norway film rebate.",
         "DISCOVERY"),
        ("no_nrk", "no_nfi_grants",
         "allowed",
         "NRK broadcaster co-production and NFI national grants are complementary. "
         "NRK is broadcaster; NFI is public funder — standard stacking in Norwegian film.",
         "PARSED"),
        ("no_nrk", "no_film_incentive",
         "conditional",
         "NRK co-production and Norway film rebate: rebate is for qualifying foreign/domestic "
         "spend; NRK is broadcaster equity. Not mutually exclusive but NRK advance may affect rebate basis.",
         "DISCOVERY"),
        # ------------------------------------------------------------------
        # Swedish regional × national
        # ------------------------------------------------------------------
        ("se_sk_film_skane", "no_nfi_grants",
         "allowed",
         "Film i Skåne (SE regional) and NFI grants are in different jurisdictions — allowed.",
         "DISCOVERY"),
        ("se_sk_film_skane", "se_svt",
         "allowed",
         "Film i Skåne and SVT broadcaster co-production are complementary in Swedish film financing.",
         "PARSED"),
        ("se_ab_filmstockholm", "se_svt",
         "allowed",
         "Filmregion Stockholm and SVT broadcaster co-production are complementary.",
         "PARSED"),
        ("se_sk_film_skane", "film_i_vast",
         "mutually_exclusive",
         "Film i Skåne and Film i Väst are both Swedish regional funds. Spend must primarily qualify "
         "in one region; producers typically apply to the region where principal photography occurs.",
         "DISCOVERY"),
        ("se_ab_filmstockholm", "film_i_vast",
         "mutually_exclusive",
         "Filmregion Stockholm and Film i Väst: Swedish regional funds are mutually exclusive "
         "for the same qualifying expenditure.",
         "DISCOVERY"),
        ("se_sk_film_skane", "se_ab_filmstockholm",
         "mutually_exclusive",
         "Film i Skåne and Filmregion Stockholm are both Swedish regional funds. "
         "Same qualifying expenditure cannot be claimed by both regions.",
         "DISCOVERY"),
        # ------------------------------------------------------------------
        # Danish regional × national
        # ------------------------------------------------------------------
        ("dk_cph_film_fund", "dk_dfi_support",
         "allowed",
         "Copenhagen Film Fund regional grants and DFI national grants are complementary. "
         "Standard stacking in Danish film financing.",
         "PARSED"),
        ("dk_fyn_film", "dk_dfi_support",
         "allowed",
         "Film Fyn regional grants and DFI national grants are complementary.",
         "PARSED"),
        ("dk_cph_film_fund", "dk_dr",
         "allowed",
         "Copenhagen Film Fund and DR broadcaster co-production are complementary.",
         "PARSED"),
        ("dk_fyn_film", "dk_dr",
         "allowed",
         "Film Fyn and DR broadcaster co-production are complementary.",
         "PARSED"),
        ("dk_cph_film_fund", "dk_fyn_film",
         "mutually_exclusive",
         "Copenhagen Film Fund and Film Fyn are both Danish regional funds. "
         "Same qualifying expenditure cannot be claimed by both regions.",
         "DISCOVERY"),
        # ------------------------------------------------------------------
        # Australian state × national offsets
        # ------------------------------------------------------------------
        ("au_vic_film_victoria", "au_producer_offset",
         "conditional",
         "VicScreen/Film Victoria grants are govt assistance — may reduce QAPE for AU Producer Offset. "
         "Separate accounting for Victoria-spend vs other qualifying expenditure.",
         "PARSED"),
        ("au_tas_screen", "au_producer_offset",
         "conditional",
         "Screen Tasmania grants are govt assistance — may reduce QAPE for AU Producer Offset.",
         "DISCOVERY"),
        ("au_nt_territory", "au_producer_offset",
         "conditional",
         "Territory Screen Office grants are govt assistance — may reduce QAPE for AU Producer Offset.",
         "DISCOVERY"),
        ("au_vic_film_victoria", "au_location_offset",
         "conditional",
         "VicScreen grants are govt assistance — may reduce QAPE for AU Location Offset.",
         "PARSED"),
        ("au_qld_screen", "au_location_offset",
         "conditional",
         "Screen QLD attraction incentive is govt assistance — reduces QAPE for AU Location Offset.",
         "PARSED"),
        ("au_nsw_screen", "au_location_offset",
         "conditional",
         "Screen NSW fund is govt assistance — reduces QAPE for AU Location Offset.",
         "PARSED"),
        ("au_nsw_screen", "au_producer_offset",
         "conditional",
         "Screen NSW fund is govt assistance — may reduce QAPE for AU Producer Offset.",
         "PARSED"),
        # ------------------------------------------------------------------
        # UK regional × UK AVEC
        # ------------------------------------------------------------------
        ("gb_lon_film_london", "uk_avec",
         "conditional",
         "Film London grant is govt assistance — reduces qualifying UK expenditure basis for AVEC. "
         "Net AVEC rate applied to reduced basis.",
         "PARSED"),
        ("gb_film_hub_midlands", "uk_avec",
         "conditional",
         "Film Hub Midlands (BFI Network) grant is govt assistance — reduces qualifying UK expenditure basis for AVEC.",
         "PARSED"),
        ("gb_sct_screen_production", "uk_avec",
         "conditional",
         "Screen Scotland Production Growth Fund is govt assistance — reduces AVEC qualifying basis.",
         "PARSED"),
        ("gb_wls_film_fund", "uk_avec",
         "conditional",
         "Wales Film Fund (Creative Wales) is govt assistance — reduces AVEC qualifying basis.",
         "PARSED"),
        # ------------------------------------------------------------------
        # Canadian provincial × federal CPTC
        # ------------------------------------------------------------------
        ("ca_pe_film_pei", "ca_federal_cptc",
         "conditional",
         "Film PEI grant is govt assistance — reduces qualifying labour for federal CPTC calculation.",
         "DISCOVERY"),
        ("ca_mb_film_mb", "ca_federal_cptc",
         "conditional",
         "Manitoba Film & Music grants are govt assistance — reduces CPTC qualifying labour basis.",
         "PARSED"),
        ("ca_nb_film_nb", "ca_federal_cptc",
         "conditional",
         "NB Film grants are govt assistance — reduces CPTC qualifying labour basis.",
         "DISCOVERY"),
        ("ca_nl_film_nl", "ca_federal_cptc",
         "conditional",
         "NL Film Corp grants are govt assistance — reduces CPTC qualifying labour basis.",
         "DISCOVERY"),
        ("ca_ns_film_incentive", "ca_federal_cptc",
         "conditional",
         "Nova Scotia incentive is govt assistance — reduces CPTC qualifying labour basis.",
         "PARSED"),
        # ------------------------------------------------------------------
        # Tourism support × national incentives (allowed — different categories)
        # ------------------------------------------------------------------
        ("au_tourism_film", "au_location_offset",
         "allowed",
         "Tourism Australia film support and AU Location Offset are complementary. "
         "Tourism support is separate non-production grant; does not reduce QAPE.",
         "DISCOVERY"),
        ("nz_tourism_film", "nz_nzspg",
         "allowed",
         "Tourism NZ support and NZ International SPGI are complementary. "
         "Tourism support is separate facilitation fund.",
         "DISCOVERY"),
        ("ie_tourism_film", "ie_section_481",
         "conditional",
         "Tourism Ireland/Fáilte support may constitute govt assistance — could reduce "
         "Section 481 qualifying basis. Legal opinion recommended.",
         "DISCOVERY"),
        ("jo_rfc_tourism", "jo_rfc_rebate",
         "conditional",
         "Jordan RFC tourism facilitation and RFC cash rebate are both administered by RFC. "
         "Tourism facilitation is services; rebate is financial. May be combined.",
         "DISCOVERY"),
        # ------------------------------------------------------------------
        # Export/workforce × national (all allowed — non-financial)
        # ------------------------------------------------------------------
        ("gb_bfi_international", "uk_avec",
         "allowed",
         "BFI International export support and UK AVEC are complementary — different categories.",
         "DISCOVERY"),
        ("fr_unifrance", "fr_trip",
         "allowed",
         "UniFrance export support and TRIP tax rebate are complementary — different categories.",
         "DISCOVERY"),
        ("ca_telefilm_export", "ca_federal_cptc",
         "conditional",
         "Telefilm export grant is govt assistance — may reduce CPTC qualifying basis. "
         "Typically treated as separate category; confirm with CRA.",
         "DISCOVERY"),
        ("au_screen_international", "au_producer_offset",
         "conditional",
         "Screen Australia International grants are govt assistance — may reduce AU Producer Offset QAPE.",
         "DISCOVERY"),
        ("gb_screenskills", "uk_avec",
         "allowed",
         "ScreenSkills (industry-funded) and AVEC are complementary. ScreenSkills not govt assistance.",
         "DISCOVERY"),
        ("ie_screen_ireland_dev", "ie_section_481",
         "conditional",
         "Screen Ireland development grants are govt assistance — reduce Section 481 qualifying basis.",
         "PARSED"),
        # ------------------------------------------------------------------
        # New EU/MENA/APAC/LATAM rebates × Eurimages
        # ------------------------------------------------------------------
        ("cy_film_rebate", "eu_eurimages",
         "allowed",
         "Cyprus cash rebate and Eurimages grant are complementary. Cyprus is Eurimages member.",
         "PARSED"),
        ("ro_film_rebate", "eu_eurimages",
         "allowed",
         "Romania 35% rebate and Eurimages grant are complementary. Romania is Eurimages member.",
         "PARSED"),
        ("si_sfc_rebate", "eu_eurimages",
         "allowed",
         "Slovenia 25% rebate and Eurimages grant are complementary. Slovenia is Eurimages member.",
         "PARSED"),
        ("al_anca_rebate", "eu_eurimages",
         "allowed",
         "Albania rebate and Eurimages grant are complementary. Albania is Eurimages member.",
         "PARSED"),
        ("me_film_rebate", "eu_eurimages",
         "allowed",
         "Montenegro rebate and Eurimages grant are complementary. Montenegro is Eurimages observer.",
         "DISCOVERY"),
        ("ge_gnfc_rebate", "eu_eurimages",
         "allowed",
         "Georgia rebate and Eurimages grant are complementary. Georgia is Eurimages member.",
         "DISCOVERY"),
        ("at_fisa_plus", "eu_eurimages",
         "allowed",
         "Austria FISA+ and Eurimages grant are complementary. Austria is Eurimages member.",
         "PARSED"),
        ("nl_nfpi", "eu_eurimages",
         "allowed",
         "Netherlands NFPI 30% rebate and Eurimages grant are complementary. NL is Eurimages member.",
         "PARSED"),
        ("ee_film_estonia", "eu_eurimages",
         "allowed",
         "Estonia 30% rebate and Eurimages grant are complementary. Estonia is Eurimages member.",
         "PARSED"),
        ("lt_lcc_rebate", "eu_eurimages",
         "allowed",
         "Lithuania 30% rebate and Eurimages grant are complementary. Lithuania is Eurimages member.",
         "PARSED"),
        ("lv_nkmp_rebate", "eu_eurimages",
         "allowed",
         "Latvia 30% rebate and Eurimages grant are complementary. Latvia is Eurimages member.",
         "PARSED"),
        ("sk_avf_incentive", "eu_eurimages",
         "allowed",
         "Slovakia AVF 33% and Eurimages grant are complementary. Slovakia is Eurimages member.",
         "PARSED"),
        ("mk_mfa_rebate", "eu_eurimages",
         "allowed",
         "North Macedonia rebate and Eurimages grant are complementary. N. Macedonia is Eurimages member.",
         "PARSED"),
        ("ba_film_centre", "eu_eurimages",
         "allowed",
         "Bosnia BHFF grants and Eurimages are complementary. Bosnia is Eurimages member.",
         "PARSED"),
        # ------------------------------------------------------------------
        # New EU rebates × MEDIA fund
        # ------------------------------------------------------------------
        ("cy_film_rebate", "eu_media_fund",
         "allowed",
         "Cyprus rebate and EU MEDIA fund are complementary — different mechanisms.",
         "PARSED"),
        ("nl_nfpi", "eu_media_fund",
         "allowed",
         "Netherlands NFPI and EU MEDIA fund are complementary.",
         "PARSED"),
        ("at_fisa_plus", "eu_media_fund",
         "allowed",
         "Austria FISA+ and EU MEDIA fund are complementary.",
         "PARSED"),
        ("ee_film_estonia", "eu_media_fund",
         "allowed",
         "Estonia rebate and EU MEDIA fund are complementary.",
         "PARSED"),
        # ------------------------------------------------------------------
        # New EU rebates × Ibermedia
        # ------------------------------------------------------------------
        ("pt_film_incentive", "ibermedia_programme",
         "allowed",
         "Portugal film incentive and Ibermedia are complementary. Portugal is Ibermedia member.",
         "PARSED"),
        # ------------------------------------------------------------------
        # Streamer obligations × broadcaster co-production
        # ------------------------------------------------------------------
        ("streamer_uk_local", "gb_bbc_films",
         "conditional",
         "UK streamer local content spend and BBC Films co-production can overlap: "
         "a BBC co-produced film may satisfy part of streamer obligation. Separate accounting required.",
         "DISCOVERY"),
        ("streamer_uk_local", "gb_film4",
         "conditional",
         "UK streamer obligation and Film4 co-production: a Film4 title acquired by a streamer "
         "may partially satisfy content obligation. Separate accounting required.",
         "DISCOVERY"),
        ("streamer_uk_local", "uk_avec",
         "allowed",
         "UK streamer content obligation and AVEC are complementary. AVEC available on "
         "qualifying UK content regardless of whether it satisfies streaming obligation.",
         "PARSED"),
        # ------------------------------------------------------------------
        # New MENA/APAC/LATAM rebates × each other (jurisdictional independence)
        # ------------------------------------------------------------------
        ("ae_dxb_dpi", "ae_adfc_rebate",
         "mutually_exclusive",
         "Dubai DPI and Abu Dhabi ADFC are both UAE rebate programs. "
         "A production can only qualify for one emirate's rebate on the same qualifying spend.",
         "PARSED"),
        ("ae_dxb_dpi", "ae_emirates_support",
         "allowed",
         "Dubai DPI rebate and Emirates Airline in-kind support are complementary — different categories.",
         "DISCOVERY"),
        ("ae_adfc_rebate", "ae_emirates_support",
         "allowed",
         "Abu Dhabi ADFC rebate and Emirates Airline in-kind support are complementary.",
         "DISCOVERY"),
        # ------------------------------------------------------------------
        # Airline support × tourism support (all allowed — different categories)
        # ------------------------------------------------------------------
        ("nz_air_production", "nz_tourism_film",
         "allowed",
         "Air New Zealand in-kind support and Tourism NZ film support are complementary facilitation programs.",
         "DISCOVERY"),
        ("nz_air_production", "nz_nzspg",
         "allowed",
         "Air New Zealand in-kind support and NZ SPGI financial rebate are complementary.",
         "DISCOVERY"),
        ("ae_emirates_support", "ae_dxb_dpi",
         "allowed",
         "Emirates Airline support and Dubai DPI rebate are complementary — different categories.",
         "DISCOVERY"),
    ]

    for (slug_a, slug_b, rule_type, condition_text, confidence) in _RULES:
        conn.execute(text("""
            INSERT INTO legal_stacking_rules
                (id, program_a_id, program_b_id, rule_type, condition_text,
                 confidence_tier, created_at, updated_at)
            SELECT gen_random_uuid(),
                (SELECT id FROM incentive_programs WHERE slug = :a ::varchar LIMIT 1),
                (SELECT id FROM incentive_programs WHERE slug = :b ::varchar LIMIT 1),
                :rt, :ct, :conf, now(), now()
            WHERE (SELECT id FROM incentive_programs WHERE slug = :a ::varchar LIMIT 1) IS NOT NULL
              AND (SELECT id FROM incentive_programs WHERE slug = :b ::varchar LIMIT 1) IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM legal_stacking_rules
                  WHERE program_a_id = (SELECT id FROM incentive_programs WHERE slug = :a ::varchar LIMIT 1)
                    AND program_b_id = (SELECT id FROM incentive_programs WHERE slug = :b ::varchar LIMIT 1)
              )
        """), {
            "a": slug_a, "b": slug_b, "rt": rule_type,
            "ct": condition_text, "conf": confidence,
        })


def downgrade() -> None:
    pass
