"""Phase D1/D2/D4/D5: Seed cultural qualification rules, test definitions, structure graph, financing interactions.

Revision ID: 0059
Revises: 0058
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "0059"
down_revision = "0058"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # D2: Cultural test definitions
    # ------------------------------------------------------------------
    _TEST_DEFS = [
        ("uk_bfi_cultural_test", "UK BFI Cultural Test", "uk_avec",
         "points", 31, 18, '{"C+D": 4}',
         "BFI cultural test: 31 points available across 4 sections. Must score ≥18 overall AND ≥4 from sections C+D combined."),
        ("fr_cnc_cultural_test", "French CNC Cultural Qualification", "fr_cnc_production",
         "threshold", 7, 4, None,
         "French CNC test: French producer required, ≥50% French spend, plus director or writer French/EEA."),
        ("ie_section_481_test", "Irish Section 481 Qualification Checklist", "ie_section_481",
         "checklist", 5, 3, None,
         "Section 481 checklist: Irish entity + qualifying spend + qualifying production type all required."),
        ("eu_eurimages_test", "Eurimages Co-production Eligibility Test", "eu_eurimages",
         "checklist", 5, 4, None,
         "Eurimages: ≥2 member countries, all co-producers from member states, each 10-80% of budget."),
        ("ibermedia_test", "Ibermedia Co-production Eligibility Test", "ibermedia_programme",
         "checklist", 4, 4, None,
         "Ibermedia: ≥2 Ibero-American member countries, each 10-80% of budget."),
        ("ca_content_test", "Canadian Content Point Test", "ca_federal_cptc",
         "points", 10, 6, '{"dir_or_wrt": 1}',
         "CRTC/Telefilm Canadian content: 10 points available, need ≥6. Director or writer MUST score."),
        ("au_content_test", "Australian Content Test", "au_producer_offset",
         "points", 16, 8, None,
         "Australian content: 16 points available, need ≥8 (50%). Script, director, producer highest value."),
        ("eu_european_convention_test", "European Convention on Cinematographic Co-production",
         "eu_media_fund", "checklist", 5, 5, None,
         "European Convention: ≥2 signatory countries, each 10-80%, director or writer from signatory state."),
    ]

    for row in _TEST_DEFS:
        slug, name, prog_slug, ttype, total, minimum, sec_mins, notes = row
        conn.execute(text("""
            INSERT INTO cultural_test_definitions
                (test_slug, test_name, program_slug, test_type, total_available_points,
                 minimum_pass_points, section_minimums, notes, confidence_tier)
            VALUES (:slug, :name, :prog, :ttype, :total, :minimum, :sec, :notes, 'PARSED')
            ON CONFLICT (test_slug) DO UPDATE SET
                minimum_pass_points = EXCLUDED.minimum_pass_points,
                notes = EXCLUDED.notes
        """), {"slug": slug, "name": name, "prog": prog_slug, "ttype": ttype,
               "total": total, "minimum": minimum, "sec": sec_mins, "notes": notes})

    # ------------------------------------------------------------------
    # D2: Seed BFI Cultural Test criteria (from evaluate_qualification_tests.py hardcoded rules)
    # ------------------------------------------------------------------
    _BFI_CRITERIA = [
        ("A1", "A", "Cultural Content", "Film set in UK", 4, "boolean", "uk_setting", None,
         "Set in UK = 4 pts", False),
        ("A2", "A", "Cultural Content", "Lead characters British citizens or residents", 4,
         "boolean", "lead_characters_british", None, "British lead characters = 4 pts", False),
        ("A3", "A", "Cultural Content", "Film based on British subject matter or underlying material", 4,
         "boolean", "british_subject_matter", None, "British subject matter = 4 pts", False),
        ("A4", "A", "Cultural Content",
         "Original dialogue recorded mainly in English/Welsh/Scottish Gaelic/Irish", 4,
         "boolean", "english_language_variant", None, "English language variant = 4 pts", False),
        ("B1", "B", "Cultural Contribution",
         "Film reflects British creativity, heritage, or diversity", 4,
         "boolean", "british_cultural_contribution", None, "British cultural contribution = 4 pts", False),
        ("C1", "C", "Cultural Hubs",
         "At least 50% of principal photography in UK", 2,
         "percentage", "uk_shoot_pct", 0.5, ">=50% UK shoot = 2 pts", False),
        ("C2", "C", "Cultural Hubs", "VFX work performed in UK", 1,
         "boolean", "uk_vfx", None, "UK VFX = 1 pt", False),
        ("D1", "D", "Cultural Practitioners", "Director British national or resident", 1,
         "boolean", "director_british", None, "British director = 1 pt", False),
        ("D2", "D", "Cultural Practitioners", "Writer British national or resident", 1,
         "boolean", "writer_british", None, "British writer = 1 pt", False),
        ("D3", "D", "Cultural Practitioners", "Producer British national or resident", 1,
         "boolean", "producer_british", None, "British producer = 1 pt", False),
        ("D4", "D", "Cultural Practitioners", "Composer British national or resident", 1,
         "boolean", "composer_british", None, "British composer = 1 pt", False),
        ("D5", "D", "Cultural Practitioners", "Lead actor British national or resident", 1,
         "boolean", "lead_actor_british", None, "British lead actor = 1 pt", False),
        ("D6", "D", "Cultural Practitioners", "Second lead actor British national or resident", 1,
         "boolean", "second_lead_british", None, "British second lead = 1 pt", False),
        ("D7", "D", "Cultural Practitioners",
         "At least 50% of cast days performed by British nationals or residents", 1,
         "percentage", "british_cast_days_pct", 0.5, ">=50% British cast days = 1 pt", False),
        ("D8", "D", "Cultural Practitioners",
         "At least 50% of crew days performed by British nationals or residents", 1,
         "percentage", "british_crew_days_pct", 0.5, ">=50% British crew days = 1 pt", False),
    ]

    for row in _BFI_CRITERIA:
        code, sec, sec_name, desc, pts, itype, ikey, thresh, logic, req = row
        conn.execute(text("""
            INSERT INTO cultural_test_criteria
                (test_slug, criterion_code, section, section_name, description, max_points,
                 input_type, input_key, threshold_value, scoring_logic, is_required)
            VALUES ('uk_bfi_cultural_test', :code, :sec, :sname, :desc, :pts,
                    :itype, :ikey, :thresh, :logic, :req)
        """), {"code": code, "sec": sec, "sname": sec_name, "desc": desc, "pts": pts,
               "itype": itype, "ikey": ikey, "thresh": thresh, "logic": logic, "req": req})

    # Canadian content criteria
    _CA_CRITERIA = [
        ("CA_D1", "A", "Key Creative", "Director Canadian", 2, "boolean", "director_ca", None,
         "Canadian director = 2 pts", True),
        ("CA_D2", "B", "Key Creative", "Screenwriter Canadian", 2, "boolean", "writer_ca", None,
         "Canadian writer = 2 pts", False),
        ("CA_D3", "C", "Performance", "Lead performer Canadian", 1, "boolean", "lead_cast_ca", None,
         "Canadian lead = 1 pt", False),
        ("CA_D4", "D", "Performance", "Second lead Canadian", 1, "boolean", "second_lead_ca", None,
         "Canadian second lead = 1 pt", False),
        ("CA_D5", "E", "Crew", "Director of Photography Canadian", 1, "boolean", "dop_ca", None,
         "Canadian DoP = 1 pt", False),
        ("CA_D6", "F", "Crew", "Art Director Canadian", 1, "boolean", "art_director_ca", None,
         "Canadian art director = 1 pt", False),
        ("CA_D7", "G", "Crew", "Music Director/Composer Canadian", 1, "boolean", "composer_ca", None,
         "Canadian composer = 1 pt", False),
        ("CA_D8", "H", "Crew", "Picture Editor Canadian", 1, "boolean", "editor_ca", None,
         "Canadian editor = 1 pt", False),
    ]
    for row in _CA_CRITERIA:
        code, sec, sec_name, desc, pts, itype, ikey, thresh, logic, req = row
        conn.execute(text("""
            INSERT INTO cultural_test_criteria
                (test_slug, criterion_code, section, section_name, description, max_points,
                 input_type, input_key, threshold_value, scoring_logic, is_required)
            VALUES ('ca_content_test', :code, :sec, :sname, :desc, :pts,
                    :itype, :ikey, :thresh, :logic, :req)
        """), {"code": code, "sec": sec, "sname": sec_name, "desc": desc, "pts": pts,
               "itype": itype, "ikey": ikey, "thresh": thresh, "logic": logic, "req": req})

    # Australian content criteria
    _AU_CRITERIA = [
        ("AU_A", "A", "Content Rights", "Australian script/underlying rights", 3,
         "boolean", "australian_underlying_rights", None, "AU underlying rights = 3 pts", False),
        ("AU_B", "B", "Key Creative", "Director Australian", 3,
         "boolean", "director_au", None, "Australian director = 3 pts", False),
        ("AU_C", "C", "Key Creative", "Producer Australian", 3,
         "boolean", "producer_au", None, "Australian producer = 3 pts", False),
        ("AU_D", "D", "Performance", "Lead actor Australian", 2,
         "boolean", "lead_cast_au", None, "Australian lead actor = 2 pts", False),
        ("AU_E", "E", "Performance", "Supporting cast ≥50% Australian", 2,
         "percentage", "au_cast_days_pct", 0.5, ">=50% AU cast days = 2 pts", False),
        ("AU_F", "F", "Crew", "Australian composer/music", 1,
         "boolean", "composer_au", None, "Australian composer = 1 pt", False),
        ("AU_G", "G", "Post", "Post-production in Australia", 2,
         "boolean", "post_production_au", None, "Australian post = 2 pts", False),
    ]
    for row in _AU_CRITERIA:
        code, sec, sec_name, desc, pts, itype, ikey, thresh, logic, req = row
        conn.execute(text("""
            INSERT INTO cultural_test_criteria
                (test_slug, criterion_code, section, section_name, description, max_points,
                 input_type, input_key, threshold_value, scoring_logic, is_required)
            VALUES ('au_content_test', :code, :sec, :sname, :desc, :pts,
                    :itype, :ikey, :thresh, :logic, :req)
        """), {"code": code, "sec": sec, "sname": sec_name, "desc": desc, "pts": pts,
               "itype": itype, "ikey": ikey, "thresh": thresh, "logic": logic, "req": req})

    # ------------------------------------------------------------------
    # D1: Cultural qualification rules (nationality requirements per program)
    # ------------------------------------------------------------------
    _QUAL_RULES = [
        # UK AVEC / BFI
        ("uk_avec", "uk_bfi_cultural_test", "director", "GB", "weighted", 0.033, None,
         "BFI D1: British director = 1pt/31 total. Optional but weighted.", "PARSED"),
        ("uk_avec", "uk_bfi_cultural_test", "writer", "GB", "weighted", 0.033, None,
         "BFI D2: British writer = 1pt/31. Optional but weighted.", "PARSED"),
        ("uk_avec", "uk_bfi_cultural_test", "producer", "GB", "weighted", 0.033, None,
         "BFI D3: British producer = 1pt/31. Optional but weighted.", "PARSED"),
        ("uk_avec", "uk_bfi_cultural_test", "composer", "GB", "weighted", 0.033, None,
         "BFI D4: British composer = 1pt/31. Optional but weighted.", "PARSED"),
        ("uk_avec", "uk_bfi_cultural_test", "lead_cast", "GB", "weighted", 0.033, None,
         "BFI D5: British lead actor = 1pt/31. Optional but weighted.", "PARSED"),
        ("uk_avec", "uk_bfi_cultural_test", "supporting_cast", "GB", "weighted", 0.033, None,
         "BFI D6/D7: British supporting cast contributes to cast-day percentage. Optional.", "PARSED"),
        ("uk_avec", "uk_bfi_cultural_test", "vfx_supervisor", "GB", "optional", None, None,
         "BFI C2: VFX work in UK = 1pt/31. Optional but efficient.", "PARSED"),
        # Ireland Section 481
        ("ie_section_481", "ie_section_481_test", "entity", "IE", "required", None, None,
         "Section 481: Irish-resident or EEA qualifying production company required.", "VERIFIED"),
        ("ie_section_481", "ie_section_481_test", "producer", "IE", "optional", None, None,
         "Irish producer strengthens Section 481 application. Not strictly required.", "PARSED"),
        # France CNC
        ("fr_cnc_production", "fr_cnc_cultural_test", "producer", "FR", "required", None, None,
         "CNC: French producer required for CNC selective support.", "VERIFIED"),
        ("fr_cnc_production", "fr_cnc_cultural_test", "director", "FR", "weighted", 0.286, None,
         "CNC: French/EEA director strengthens cultural qualification (2pts/7).", "PARSED"),
        ("fr_cnc_production", "fr_cnc_cultural_test", "writer", "FR", "weighted", 0.286, None,
         "CNC: French/EEA writer contributes to cultural qualification (2pts/7).", "PARSED"),
        # Canada CPTC
        ("ca_federal_cptc", "ca_content_test", "director", "CA", "weighted", 0.2, None,
         "CPTC: Canadian director = 2pts/10. Director or writer must score.", "VERIFIED"),
        ("ca_federal_cptc", "ca_content_test", "writer", "CA", "weighted", 0.2, None,
         "CPTC: Canadian writer = 2pts/10. Director or writer must score.", "VERIFIED"),
        ("ca_federal_cptc", "ca_content_test", "lead_cast", "CA", "weighted", 0.1, None,
         "CPTC: Canadian lead performer = 1pt/10.", "VERIFIED"),
        ("ca_federal_cptc", "ca_content_test", "producer", "CA", "required", None, None,
         "CPTC: Canadian producer required (must be majority owner of production company).", "VERIFIED"),
        ("ca_federal_cptc", "ca_content_test", "composer", "CA", "weighted", 0.1, None,
         "CPTC: Canadian composer = 1pt/10.", "VERIFIED"),
        ("ca_federal_cptc", "ca_content_test", "editor", "CA", "weighted", 0.1, None,
         "CPTC: Canadian picture editor = 1pt/10.", "VERIFIED"),
        # Canada CMF
        ("ca_cmf", "ca_content_test", "director", "CA", "required", None, None,
         "CMF: Canadian director required for CMF eligibility.", "VERIFIED"),
        ("ca_cmf", "ca_content_test", "producer", "CA", "required", None, None,
         "CMF: Canadian producer required.", "VERIFIED"),
        # Eurimages
        ("eu_eurimages", "eu_eurimages_test", "producer", "EU", "required", None, None,
         "Eurimages: each co-producer must be from Eurimages member state.", "VERIFIED"),
        ("eu_eurimages", "eu_eurimages_test", "entity", "EU", "required", None, None,
         "Eurimages: all companies must be legally established in member states.", "VERIFIED"),
        # Ibermedia
        ("ibermedia_programme", "ibermedia_test", "producer", None, "required", None, None,
         "Ibermedia: producers must be from Ibero-American member countries.", "VERIFIED"),
        ("ibermedia_programme", "ibermedia_test", "entity", None, "required", None, None,
         "Ibermedia: all production entities from Ibermedia member states.", "VERIFIED"),
        # Australia Producer Offset
        ("au_producer_offset", "au_content_test", "director", "AU", "weighted", 0.1875, None,
         "AU content test: Australian director = 3pts/16.", "VERIFIED"),
        ("au_producer_offset", "au_content_test", "producer", "AU", "weighted", 0.1875, None,
         "AU content test: Australian producer = 3pts/16.", "VERIFIED"),
        ("au_producer_offset", "au_content_test", "lead_cast", "AU", "weighted", 0.125, None,
         "AU content test: Australian lead actor = 2pts/16.", "VERIFIED"),
        ("au_producer_offset", "au_content_test", "composer", "AU", "weighted", 0.0625, None,
         "AU content test: Australian composer = 1pt/16.", "VERIFIED"),
        ("au_producer_offset", "au_content_test", "post_supervisor", "AU", "weighted", 0.125, None,
         "AU content test: Post-production in Australia = 2pts/16.", "VERIFIED"),
        # German DFFF
        ("de_dfff", None, "director", "DE", "optional", None, None,
         "DFFF Fachgutachten: German-language or German cultural connection. Director nationality weighted.", "PARSED"),
        ("de_dfff", None, "producer", "DE", "required", None, None,
         "DFFF: German producer (Förderungsgesellschaft) required as majority co-producer.", "PARSED"),
        # Netherlands HBF
        ("nl_hbf", None, "director", "NL", "required", None, None,
         "NFF: Dutch director or Dutch treaty director required for project support.", "PARSED"),
        ("nl_hbf", None, "producer", "NL", "required", None, None,
         "NFF: Dutch producer required as majority or minority co-producer.", "PARSED"),
        # Nordic FTVF
        ("nordic_ftvf", None, "director", None, "required", None, None,
         "Film i Väst/Nordic fund: Nordic national director required (Sweden/Norway/Denmark/Finland/Iceland).", "PARSED"),
        ("nordic_ftvf", None, "producer", None, "required", None, None,
         "Nordic fund: Nordic-registered production company required.", "PARSED"),
        # Danish DFI
        ("dk_dfi_support", None, "director", "DK", "weighted", None, None,
         "DFI: Danish director strengthens application. Majority Danish creative elements preferred.", "PARSED"),
        ("dk_dfi_support", None, "writer", "DK", "weighted", None, None,
         "DFI: Danish writer/screenplay strengthens application.", "PARSED"),
        # Norwegian NFI
        ("no_nfi_grants", None, "director", "NO", "weighted", None, None,
         "NFI: Norwegian director preferred. Creative Norwegian elements key to selection.", "PARSED"),
        ("no_nfi_grants", None, "writer", "NO", "weighted", None, None,
         "NFI: Norwegian writer/screenplay strengthens application.", "PARSED"),
        # Finnish SES
        ("fi_ses_grants", None, "director", "FI", "weighted", None, None,
         "SES: Finnish director preferred. Finnish creative elements key.", "PARSED"),
        ("fi_ses_grants", None, "producer", "FI", "required", None, None,
         "SES: Finnish production company required.", "PARSED"),
        # Polish PISF
        ("pl_pisf_grants", None, "director", "PL", "weighted", None, None,
         "PISF: Polish director or Polish screenplay essential for selection.", "PARSED"),
        ("pl_pisf_grants", None, "writer", "PL", "weighted", None, None,
         "PISF: Polish screenwriter contributes to qualification.", "PARSED"),
        ("pl_pisf_grants", None, "producer", "PL", "required", None, None,
         "PISF: Polish producer required as majority or minority co-producer.", "PARSED"),
        # Czech Film Fund
        ("cz_czech_film_fund", None, "producer", "CZ", "required", None, None,
         "Czech Film Fund: Czech production company required.", "PARSED"),
        ("cz_czech_film_fund", None, "director", "CZ", "weighted", None, None,
         "Czech Film Fund: Czech creative elements (director, writer) weighted in selection.", "PARSED"),
        # Hungarian NFI
        ("hu_nfi_grants", None, "producer", "HU", "required", None, None,
         "NFI Hungary: Hungarian production company required.", "PARSED"),
        # Austrian ÖFI
        ("at_ofi_grants", None, "producer", "AT", "required", None, None,
         "ÖFI: Austrian production company required.", "PARSED"),
        # Portuguese ICA
        ("pt_ica_grants", None, "producer", "PT", "required", None, None,
         "ICA Portugal: Portuguese production company required.", "PARSED"),
        # Greek GFC
        ("gr_gnf_grants", None, "producer", "GR", "required", None, None,
         "Greek Film Centre: Greek production company required.", "PARSED"),
        # Bosnia BHFF
        ("ba_film_centre", None, "producer", "BA", "required", None, None,
         "Bosnia BHFF: Bosnian production company required as majority co-producer.", "PARSED"),
        # EU MEDIA Fund
        ("eu_media_fund", "eu_european_convention_test", "producer", "EU", "required", None, None,
         "EU MEDIA: production company must be from EEA/signatory state.", "VERIFIED"),
        ("eu_media_fund", "eu_european_convention_test", "entity", "EU", "required", None, None,
         "EU MEDIA: legal entity established in EEA/Creative Europe programme country.", "VERIFIED"),
        # Swedish Göteborg Fund
        ("se_goteborg_fund", None, "director", "SE", "weighted", None, None,
         "Göteborg Film Fund: Swedish/Nordic creative elements weighted.", "PARSED"),
        ("se_goteborg_fund", None, "producer", "SE", "required", None, None,
         "Göteborg Film Fund: Swedish production company required.", "PARSED"),
    ]

    for row in _QUAL_RULES:
        (prog_slug, test_slug, role, jcode, status, weight, min_pct, notes, conf) = row
        conn.execute(text("""
            INSERT INTO cultural_qualification_rules
                (program_slug, test_slug, role, jurisdiction_code, status, weight,
                 min_pct, notes, confidence_tier)
            VALUES (:prog, :test, :role, :jcode, :status, :weight, :min_pct, :notes, :conf)
        """), {"prog": prog_slug, "test": test_slug, "role": role, "jcode": jcode,
               "status": status, "weight": weight, "min_pct": min_pct, "notes": notes,
               "conf": conf})

    # ------------------------------------------------------------------
    # D4: Structure graph edges
    # ------------------------------------------------------------------
    _GRAPH_EDGES = [
        # Treaty → Program (unlocks)
        ("treaty", "uk-ca-bilateral", "unlocks", "program", "uk_avec", "UK majority in UK-Canada co-production", None, "PARSED"),
        ("treaty", "uk-ca-bilateral", "unlocks", "program", "ca_federal_cptc", "CA majority in UK-Canada co-production", None, "PARSED"),
        ("treaty", "uk-ie-bilateral", "unlocks", "program", "uk_avec", "UK majority in UK-Ireland co-production", None, "PARSED"),
        ("treaty", "uk-ie-bilateral", "unlocks", "program", "ie_section_481", "IE majority in UK-Ireland co-production", None, "PARSED"),
        ("treaty", "ca-fr-bilateral", "unlocks", "program", "ca_federal_cptc", "CA majority in CA-France co-production", None, "PARSED"),
        ("treaty", "ca-fr-bilateral", "unlocks", "program", "fr_trip", "FR majority in CA-France co-production", None, "PARSED"),
        ("treaty", "ca-au-bilateral", "unlocks", "program", "ca_federal_cptc", "CA majority in CA-Australia co-production", None, "PARSED"),
        ("treaty", "ca-au-bilateral", "unlocks", "program", "au_producer_offset", "AU majority in CA-Australia co-production", None, "PARSED"),
        ("treaty", "fr-de-bilateral", "unlocks", "program", "fr_trip", "FR majority in France-Germany co-production", None, "PARSED"),
        ("treaty", "fr-de-bilateral", "unlocks", "program", "de_dfff", "DE majority in France-Germany co-production", None, "PARSED"),
        ("treaty", "uk-au-bilateral", "unlocks", "program", "uk_avec", "UK majority in UK-Australia co-production", None, "PARSED"),
        ("treaty", "uk-au-bilateral", "unlocks", "program", "au_producer_offset", "AU majority in UK-Australia co-production", None, "PARSED"),
        ("treaty", "it-fr-bilateral", "unlocks", "program", "it_tax_credit_foreign", "IT majority in Italy-France co-production", None, "PARSED"),
        ("treaty", "it-fr-bilateral", "unlocks", "program", "fr_trip", "FR majority in Italy-France co-production", None, "PARSED"),
        # Treaty → Fund (unlocks)
        ("treaty", "eu_eurimages_membership", "unlocks", "fund", "eu_eurimages", "Eurimages membership unlocks grant access", None, "PARSED"),
        ("treaty", "ibermedia_membership", "unlocks", "fund", "ibermedia_programme", "Ibermedia membership unlocks fund access", None, "PARSED"),
        ("treaty", "eu_european_convention", "unlocks", "fund", "eu_media_fund", "European Convention signatory unlocks MEDIA fund", None, "PARSED"),
        # Program → Test (requires)
        ("program", "uk_avec", "requires", "test", "uk_bfi_cultural_test", None, None, "PARSED"),
        ("program", "ca_federal_cptc", "requires", "test", "ca_content_test", None, None, "PARSED"),
        ("program", "ca_cmf", "requires", "test", "ca_content_test", None, None, "PARSED"),
        ("program", "au_producer_offset", "requires", "test", "au_content_test", None, None, "PARSED"),
        ("program", "eu_eurimages", "requires", "test", "eu_eurimages_test", None, None, "PARSED"),
        ("program", "ibermedia_programme", "requires", "test", "ibermedia_test", None, None, "PARSED"),
        ("program", "fr_cnc_production", "requires", "test", "fr_cnc_cultural_test", None, None, "PARSED"),
        ("program", "eu_media_fund", "requires", "test", "eu_european_convention_test", None, None, "PARSED"),
        # Program → Program (improves)
        ("program", "eu_eurimages", "improves", "program", "at_ofi_grants", "Eurimages member improves ÖFI application competitiveness", 0.2, "DISCOVERY"),
        ("program", "eu_eurimages", "improves", "program", "pl_pisf_grants", "Eurimages + PISF standard Polish co-production stack", 0.2, "PARSED"),
        ("program", "eu_eurimages", "improves", "program", "cz_czech_film_fund", "Eurimages + Czech Film Fund standard European co-production", 0.2, "PARSED"),
        ("program", "eu_eurimages", "improves", "program", "hu_nfi_grants", "Eurimages + NFI Hungary standard co-production", 0.2, "PARSED"),
        ("program", "film_i_vast", "improves", "program", "se_svt", "Film i Väst regional attracts SVT broadcaster interest", 0.15, "PARSED"),
        ("program", "ca_cmf", "improves", "program", "ca_federal_cptc", "Certified Canadian content qualifies for both CMF and CPTC", 0.1, "PARSED"),
        ("program", "ca_bell_fund", "improves", "program", "ca_cmf", "Bell Fund certified productions competitive for CMF", 0.1, "DISCOVERY"),
        ("program", "ca_nsi_fund", "improves", "program", "ca_federal_cptc", "NSI certified productions qualify for CPTC", 0.05, "DISCOVERY"),
        # Program → Program (reduces)
        ("program", "ie_screen_ireland_dev", "reduces", "program", "ie_section_481",
         "Screen Ireland development grants are govt assistance — reduces Section 481 qualifying basis", 0.05, "PARSED"),
        ("program", "gb_lon_film_london", "reduces", "program", "uk_avec",
         "Film London grant reduces AVEC qualifying UK expenditure basis", 0.05, "PARSED"),
        ("program", "au_tourism_film", "reduces", "program", "au_producer_offset",
         "Tourism Australia grant may constitute govt assistance reducing QAPE", 0.02, "DISCOVERY"),
        ("program", "ca_telefilm_export", "reduces", "program", "ca_federal_cptc",
         "Telefilm export grant is govt assistance potentially reducing CPTC basis", 0.03, "DISCOVERY"),
        ("program", "au_pdv_offset", "reduces", "program", "au_location_offset",
         "PDV Offset is govt assistance — reduces QAPE for Location Offset if combined", 0.10, "PARSED"),
        ("program", "au_pdv_offset", "reduces", "program", "au_producer_offset",
         "PDV Offset is govt assistance — reduces QAPE for Producer Offset if combined", 0.10, "PARSED"),
        ("program", "fr_cnc_animation", "reduces", "program", "fr_trip",
         "CNC animation fund is govt assistance reducing TRIP qualifying expenditure", 0.05, "PARSED"),
        # Program → Program (incompatible_with)
        ("program", "au_location_offset", "incompatible_with", "program", "au_producer_offset",
         "Same production cannot claim both AU Location Offset and AU Producer Offset — different tracks", None, "PARSED"),
        ("program", "se_sk_film_skane", "incompatible_with", "program", "se_ab_filmstockholm",
         "Swedish regional funds mutually exclusive for same qualifying spend", None, "DISCOVERY"),
        ("program", "dk_cph_film_fund", "incompatible_with", "program", "dk_fyn_film",
         "Danish regional funds mutually exclusive for same qualifying spend", None, "DISCOVERY"),
        ("program", "ae_dxb_dpi", "incompatible_with", "program", "ae_adfc_rebate",
         "Dubai and Abu Dhabi rebates cannot both apply to same qualifying spend", None, "PARSED"),
        # Broadcaster → Incentive (improves)
        ("program", "gb_bbc_films", "improves", "program", "uk_avec",
         "BBC co-production strengthens BFI cultural test British creative element score", 0.1, "PARSED"),
        ("program", "gb_film4", "improves", "program", "uk_avec",
         "Film4 co-production demonstrates UK cultural commitment", 0.1, "PARSED"),
        ("program", "fr_canal_plus", "improves", "program", "fr_trip",
         "CANAL+ co-production provides evidence of French creative commitment for TRIP", 0.05, "PARSED"),
        ("program", "se_svt", "improves", "program", "no_nfi_grants",
         "SVT broadcaster involvement demonstrates Nordic market; improves NFI application competitiveness", 0.1, "DISCOVERY"),
        ("program", "no_nrk", "improves", "program", "no_nfi_grants",
         "NRK broadcaster co-production improves NFI application", 0.1, "PARSED"),
        ("program", "dk_dr", "improves", "program", "dk_dfi_support",
         "DR broadcaster co-production improves DFI application", 0.1, "PARSED"),
        ("program", "fi_yle", "improves", "program", "fi_ses_grants",
         "YLE broadcaster co-production improves SES grants application", 0.1, "PARSED"),
        # Regional → National (requires / improves)
        ("program", "no_vgn_viken", "requires", "program", "no_nfi_grants",
         "Viken Film typically requires NFI national project to qualify for regional co-funding", None, "PARSED"),
        ("program", "no_rog_vestnorsk", "requires", "program", "no_nfi_grants",
         "Vestnorsk requires NFI national project", None, "PARSED"),
        ("program", "no_tro_nordnorsk", "requires", "program", "no_nfi_grants",
         "Nord Norsk requires NFI national project", None, "PARSED"),
        ("program", "no_inl_midtnorsk", "requires", "program", "no_nfi_grants",
         "Midtnorsk requires NFI national project", None, "PARSED"),
        ("program", "film_i_vast", "improves", "program", "se_svt",
         "Västra Götaland-based production demonstrates regional cultural value to SVT", 0.1, "PARSED"),
        ("program", "gb_lon_film_london", "improves", "program", "uk_avec",
         "Film London increases AVEC qualifying UK spend concentration", 0.05, "PARSED"),
        ("program", "gb_sct_screen_production", "improves", "program", "uk_avec",
         "Screen Scotland improves AVEC by increasing UK qualifying spend", 0.05, "PARSED"),
        ("program", "gb_wls_film_fund", "improves", "program", "uk_avec",
         "Creative Wales improves AVEC by increasing qualifying UK spend in Wales", 0.05, "PARSED"),
        ("program", "au_vic_film_victoria", "improves", "program", "au_producer_offset",
         "VicScreen support increases Australian content credentials for Producer Offset", 0.05, "PARSED"),
        ("program", "au_tas_screen", "improves", "program", "au_producer_offset",
         "Screen Tasmania support increases AU content credentials", 0.03, "DISCOVERY"),
        ("program", "au_nt_territory", "improves", "program", "au_producer_offset",
         "Territory Screen Office support increases AU content credentials", 0.03, "DISCOVERY"),
        # Streamer → Incentive (unlocks)
        ("program", "streamer_uk_local", "unlocks", "program", "uk_avec",
         "Content commissioned to satisfy UK streamer obligation typically qualifies for AVEC", None, "PARSED"),
        ("program", "streamer_uk_local", "unlocks", "program", "gb_bbc_films",
         "Streamer-commissioned content may include BBC co-production", None, "DISCOVERY"),
    ]

    for row in _GRAPH_EDGES:
        src_type, src_slug, edge_type, tgt_type, tgt_slug, condition, magnitude, conf = row
        conn.execute(text("""
            INSERT INTO structure_graph_edges
                (source_type, source_slug, edge_type, target_type, target_slug,
                 condition, magnitude, confidence_tier)
            VALUES (:st, :ss, :et, :tt, :ts, :cond, :mag, :conf)
        """), {"st": src_type, "ss": src_slug, "et": edge_type, "tt": tgt_type,
               "ts": tgt_slug, "cond": condition, "mag": magnitude, "conf": conf})

    # ------------------------------------------------------------------
    # D5: Financing interactions
    # ------------------------------------------------------------------
    _FIN_INTERACTIONS = [
        # UK government assistance
        ("gb_lon_film_london", "uk_avec", "govt_assistance", 1.0, None, "GB", True,
         "Film London grant reduces AVEC qualifying basis £ for £."),
        ("gb_sct_screen_production", "uk_avec", "govt_assistance", 1.0, None, "GB", True,
         "Screen Scotland grant is govt assistance reducing AVEC basis."),
        ("gb_wls_film_fund", "uk_avec", "govt_assistance", 1.0, None, "GB", True,
         "Wales Film Fund grant is govt assistance reducing AVEC basis."),
        ("gb_creative_england", "uk_avec", "govt_assistance", 1.0, None, "GB", True,
         "Creative England grant is govt assistance reducing AVEC basis."),
        # Ireland
        ("ie_screen_ireland_dev", "ie_section_481", "govt_assistance", 1.0, None, "IE", True,
         "Screen Ireland grants reduce Section 481 qualifying Irish expenditure basis."),
        # France
        ("fr_cnc_production", "fr_trip", "govt_assistance", 1.0, None, "FR", True,
         "CNC advance reduces TRIP qualifying French expenditure basis."),
        ("fr_cnc_animation", "fr_trip", "govt_assistance", 1.0, None, "FR", True,
         "CNC animation advance reduces TRIP qualifying basis."),
        ("fr_ara_regional", "fr_trip", "govt_assistance", 1.0, None, "FR", True,
         "French regional funds reduce TRIP qualifying basis."),
        ("fr_idf_regional", "fr_trip", "govt_assistance", 1.0, None, "FR", True,
         "Île-de-France fund reduces TRIP qualifying basis."),
        ("fr_naq_regional", "fr_trip", "govt_assistance", 1.0, None, "FR", True,
         "Nouvelle-Aquitaine fund reduces TRIP qualifying basis."),
        ("fr_occ_regional", "fr_trip", "govt_assistance", 1.0, None, "FR", True,
         "Occitanie fund reduces TRIP qualifying basis."),
        # Canada
        ("ca_cmf", "ca_federal_cptc", "govt_assistance", 1.0, None, "CA", True,
         "CMF grants reduce CPTC qualifying labour basis."),
        ("ca_bell_fund", "ca_federal_cptc", "govt_assistance", 1.0, None, "CA", True,
         "Bell Fund grants reduce CPTC qualifying labour basis."),
        ("ca_nsi_fund", "ca_federal_cptc", "govt_assistance", 1.0, None, "CA", True,
         "NSI grants reduce CPTC qualifying labour basis."),
        ("ca_telefilm_dev", "ca_federal_cptc", "govt_assistance", 1.0, None, "CA", True,
         "Telefilm development advances reduce CPTC basis."),
        ("ca_on_ocase", "ca_federal_cptc", "govt_assistance", 1.0, None, "CA-ON", True,
         "Ontario OCASE reduces CPTC qualifying labour basis."),
        ("ca_bc_idmtc", "ca_federal_cptc", "govt_assistance", 1.0, None, "CA-BC", True,
         "BC IDMTC reduces CPTC qualifying labour basis."),
        # Australia
        ("au_pdv_offset", "au_location_offset", "govt_assistance", 1.0, None, "AU", True,
         "AU PDV Offset is govt financial assistance reducing Location Offset QAPE."),
        ("au_pdv_offset", "au_producer_offset", "govt_assistance", 1.0, None, "AU", True,
         "AU PDV Offset is govt financial assistance reducing Producer Offset QAPE."),
        ("au_screen_production", "au_producer_offset", "govt_assistance", 1.0, None, "AU", True,
         "Screen Australia investment is govt assistance reducing Producer Offset QAPE."),
        ("au_vic_film_victoria", "au_producer_offset", "govt_assistance", 1.0, None, "AU-VIC", True,
         "VicScreen grants are govt assistance reducing Producer Offset QAPE."),
        # Stacking ceilings
        ("eu_eurimages", "eu_media_fund", "stacking_ceiling", None, 0.50, "EU", False,
         "Eurimages + EU MEDIA combined ceiling: ~50% of production budget from EU/CoE funds."),
        ("uk_avec", "gb_bfi_production", "stacking_ceiling", None, 0.60, "GB", True,
         "AVEC + BFI Production Fund combined: max 60% of total budget (BFI internal policy)."),
        # Recoupment
        ("gb_bfi_production", "gb_bbc_films", "recoupment", None, None, "GB", True,
         "BFI first recoupment position; BBC Films subordinated in UK waterfall."),
        ("fr_cnc_production", "fr_canal_plus", "recoupment", None, None, "FR", True,
         "CNC advance subordinated to CANAL+ MG in French co-production waterfall."),
        ("eu_eurimages", "eu_media_fund", "recoupment", None, None, "EU", True,
         "Eurimages pari passu with national fund; MEDIA grant at back end."),
    ]

    for row in _FIN_INTERACTIONS:
        sa, sb, itype, red_pct, ceil_pct, jur, confirmed, notes = row
        conn.execute(text("""
            INSERT INTO financing_interactions
                (slug_a, slug_b, interaction_type, reduction_pct, ceiling_pct,
                 jurisdiction, is_confirmed, notes)
            VALUES (:sa, :sb, :it, :red, :ceil, :jur, :conf, :notes)
        """), {"sa": sa, "sb": sb, "it": itype, "red": red_pct, "ceil": ceil_pct,
               "jur": jur, "conf": confirmed, "notes": notes})


def downgrade() -> None:
    pass
