"""0055 — Phase A-D closeout: stacking rules completion.

Adds remaining legal_stacking_rules DB rows for:
  - UK broadcaster funds + AVEC/BFI (BBC Films, Film4)
  - German broadcaster funds + DFFF (ZDF, Arte, WDR)
  - French broadcaster + CNC/TRIP (CANAL+, Arte)
  - Nordic broadcaster + national grant (SVT, NRK, DR, YLE)
  - Irish broadcaster + Section 481 (RTÉ)
  - Italian broadcaster + MiC credit (RAI Cinema)
  - Spanish broadcaster + ICAA (RTVE)
  - Australian state fund mutual exclusivity (Screenwest × SAFC)
  - Italian regional × regional (conditional stacking)
  - Spanish regional × regional (mutually exclusive)
  - French regional × regional (conditional)
  - French TRIP × French regional (allowed)
  - Eurimages + additional national funds (DK, PL, CZ, HU, PT, AT)
  - Film i Väst + SVT/Nordic Fund

Revision ID: 0055
Revises: 0054
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0055"
down_revision: Union[str, None] = "0054"
branch_labels = None
depends_on = None


_STACKING_RULES: list[tuple[str, str, str, str, str]] = [
    # (frag_a, frag_b, rule_type, condition_text, confidence_tier)

    # UK broadcaster + AVEC
    ("bbc films", "audio visual expenditure",
     "allowed",
     "BBC Films co-financing is not government assistance for AVEC. Does not reduce UK qualifying expenditure.",
     "PARSED"),
    ("channel 4 film", "audio visual expenditure",
     "allowed",
     "Film4/C4 co-financing is not government assistance for AVEC. Does not reduce UK qualifying expenditure.",
     "PARSED"),
    ("bbc films", "bfi film fund",
     "allowed",
     "BBC Films and BFI Film Fund both provide independent equity co-financing for the same production.",
     "PARSED"),
    ("channel 4 film", "bfi film fund",
     "allowed",
     "Film4 and BFI Film Fund both provide independent equity co-financing for the same production.",
     "PARSED"),
    ("bbc films", "creative scotland",
     "allowed",
     "BBC Films and Creative Scotland both provide co-financing independently.",
     "PARSED"),
    ("bbc films", "northern ireland screen",
     "allowed",
     "BBC Films and Northern Ireland Screen both provide co-financing independently.",
     "PARSED"),
    ("bbc films", "creative wales",
     "allowed",
     "BBC Films and Creative Wales both provide co-financing independently.",
     "PARSED"),
    ("channel 4 film", "creative scotland",
     "allowed",
     "Film4 and Creative Scotland both provide co-financing independently.",
     "PARSED"),
    ("channel 4 film", "northern ireland screen",
     "allowed",
     "Film4 and Northern Ireland Screen both provide co-financing independently.",
     "PARSED"),

    # German broadcaster + DFFF
    ("zdf", "german federal film fund",
     "allowed",
     "ZDF co-production does not reduce German qualifying spend for DFFF. Both available for same production.",
     "PARSED"),
    ("wdr / ard", "german federal film fund",
     "allowed",
     "WDR/ARD co-production does not reduce German qualifying spend for DFFF.",
     "PARSED"),
    ("arte france", "german federal film fund",
     "allowed",
     "Arte co-production does not reduce German qualifying spend for DFFF.",
     "PARSED"),
    ("arte france", "filmförderungsanstalt",
     "allowed",
     "Arte and FFA (German national) operate on independent tracks.",
     "PARSED"),
    ("arte france", "eurimages",
     "allowed",
     "Arte co-production and Eurimages both operate on independent financing tracks.",
     "PARSED"),

    # French broadcaster + CNC
    ("canal+", "avances sur recettes",
     "allowed",
     "CANAL+ pre-purchase does not reduce CNC avance sur recettes eligibility.",
     "PARSED"),
    ("canal+", "tax rebate for international",
     "allowed",
     "CANAL+ pre-purchase does not reduce qualifying French spend for TRIP.",
     "PARSED"),
    ("arte france", "avances sur recettes",
     "allowed",
     "Arte co-production does not reduce CNC avance sur recettes eligibility.",
     "PARSED"),
    ("arte france", "tax rebate for international",
     "allowed",
     "Arte co-production does not reduce qualifying French spend for TRIP.",
     "PARSED"),

    # Irish broadcaster + Section 481
    ("rtÉ", "section 481",
     "allowed",
     "RTÉ co-investment is not government assistance reducing Irish qualifying expenditure for Section 481.",
     "PARSED"),
    ("rtÉ", "eurimages",
     "allowed",
     "RTÉ co-investment and Eurimages both operate on independent financing tracks.",
     "PARSED"),

    # Italian broadcaster + MiC credit
    ("rai cinema", "italian tax credit for foreign",
     "allowed",
     "RAI Cinema obligation does not reduce qualifying Italian expenditure for the MiC tax credit.",
     "PARSED"),
    ("rai cinema", "eurimages",
     "allowed",
     "RAI Cinema and Eurimages both operate on independent financing tracks.",
     "PARSED"),

    # Spanish broadcaster + ICAA
    ("rtve", "audiovisual production incentive",
     "allowed",
     "RTVE investment obligation does not reduce qualifying Spanish expenditure for ICAA audiovisual deduction.",
     "PARSED"),
    ("rtve", "eurimages",
     "allowed",
     "RTVE and Eurimages both operate on independent financing tracks.",
     "PARSED"),
    ("rtve", "ibermedia",
     "allowed",
     "RTVE and Ibermedia both operate on independent financing tracks.",
     "PARSED"),

    # Nordic broadcasters + national grants
    ("svt — swedish", "eurimages",
     "allowed",
     "SVT co-production and Eurimages both operate on independent financing tracks.",
     "PARSED"),
    ("nrk — norwegian", "norwegian film institute",
     "allowed",
     "NRK broadcaster commission does not reduce NFI selective grant qualifying spend.",
     "PARSED"),
    ("nrk — norwegian", "eurimages",
     "allowed",
     "NRK and Eurimages both operate on independent financing tracks.",
     "PARSED"),
    ("dr — danish", "danish film institute",
     "allowed",
     "DR broadcaster commission does not reduce DFI selective grant qualifying spend.",
     "PARSED"),
    ("dr — danish", "eurimages",
     "allowed",
     "DR and Eurimages both operate on independent financing tracks.",
     "PARSED"),
    ("yle — finnish", "finnish film foundation",
     "allowed",
     "YLE broadcaster commission does not reduce SES (Finnish Film Foundation) qualifying spend.",
     "PARSED"),
    ("yle — finnish", "eurimages",
     "allowed",
     "YLE and Eurimages both operate on independent financing tracks.",
     "PARSED"),

    # Australian state funds — mutually exclusive
    ("screenwest", "south australian film corporation",
     "mutually_exclusive",
     "Screenwest WA and SAFC SA are generally mutually exclusive — competing territorial spend requirements.",
     "PARSED"),

    # Italian regional × regional (conditional)
    ("lazio cinema", "sicilia film",
     "conditional",
     "Multiple Italian regional funds stackable if qualifying spend incurred in each region. Requires separate applications.",
     "DISCOVERY"),
    ("lazio cinema", "film commission campania",
     "conditional",
     "Lazio and Campania regional funds stackable if qualifying spend in each region.",
     "DISCOVERY"),
    ("lazio cinema", "film commission torino piemonte",
     "conditional",
     "Lazio and Piemonte regional funds stackable if qualifying spend in each region.",
     "DISCOVERY"),
    ("lazio cinema", "apulia film",
     "conditional",
     "Lazio and Apulia regional funds stackable if qualifying spend in each region.",
     "DISCOVERY"),
    ("lazio cinema", "film commission toscana",
     "conditional",
     "Lazio and Tuscany regional funds stackable if qualifying spend in each region.",
     "DISCOVERY"),
    ("sicilia film", "film commission campania",
     "conditional",
     "Sicilia and Campania regional funds stackable if qualifying spend in each region.",
     "DISCOVERY"),

    # Spanish regional × regional (mutually exclusive — competing territories)
    ("icec", "andalucia film commission",
     "mutually_exclusive",
     "Catalonia ICEC and Andalusia Film Commission are generally mutually exclusive by territorial spend.",
     "PARSED"),
    ("icec", "agadic",
     "mutually_exclusive",
     "Catalonia ICEC and Galicia AGADIC are generally mutually exclusive by territorial spend.",
     "PARSED"),
    ("icec", "institut valencià",
     "mutually_exclusive",
     "Catalonia ICEC and Valencia IVC are generally mutually exclusive by territorial spend.",
     "PARSED"),
    ("icec", "basque audiovisual",
     "mutually_exclusive",
     "Catalonia ICEC and Basque Audiovisual are generally mutually exclusive by territorial spend.",
     "PARSED"),
    ("andalucia film commission", "agadic",
     "mutually_exclusive",
     "Andalusia and Galicia regional funds are generally mutually exclusive by territorial spend.",
     "PARSED"),
    ("andalucia film commission", "institut valencià",
     "mutually_exclusive",
     "Andalusia Film Commission and Valencia IVC are generally mutually exclusive by territorial spend.",
     "PARSED"),
    ("agadic", "institut valencià",
     "mutually_exclusive",
     "Galicia AGADIC and Valencia IVC are generally mutually exclusive by territorial spend.",
     "PARSED"),

    # French regional × regional (conditional)
    ("île-de-france", "nouvelle-aquitaine",
     "conditional",
     "French regional funds IDF and Nouvelle-Aquitaine conditionally stackable with qualifying spend in each region.",
     "DISCOVERY"),
    ("île-de-france", "auvergne",
     "conditional",
     "IDF and Auvergne-Rhône-Alpes regional funds conditionally stackable with qualifying spend in each.",
     "DISCOVERY"),
    ("île-de-france", "occitanie",
     "conditional",
     "IDF and Occitanie regional funds conditionally stackable with qualifying spend in each.",
     "DISCOVERY"),
    ("nouvelle-aquitaine", "auvergne",
     "conditional",
     "Nouvelle-Aquitaine and Auvergne-Rhône-Alpes regional funds conditionally stackable.",
     "DISCOVERY"),
    ("nouvelle-aquitaine", "occitanie",
     "conditional",
     "Nouvelle-Aquitaine and Occitanie regional funds conditionally stackable.",
     "DISCOVERY"),

    # TRIP + French regional
    ("tax rebate for international", "île-de-france",
     "allowed",
     "TRIP (foreign rebate) and IDF regional fund operate on independent tracks.",
     "PARSED"),
    ("tax rebate for international", "nouvelle-aquitaine",
     "allowed",
     "TRIP and Nouvelle-Aquitaine regional fund operate on independent tracks.",
     "PARSED"),
    ("tax rebate for international", "auvergne",
     "allowed",
     "TRIP and Auvergne-Rhône-Alpes regional fund operate on independent tracks.",
     "PARSED"),
    ("tax rebate for international", "occitanie",
     "allowed",
     "TRIP and Occitanie regional fund operate on independent tracks.",
     "PARSED"),

    # Eurimages + additional national funds
    ("eurimages", "danish film institute",
     "allowed",
     "Eurimages support does not reduce DFI (Danish Film Institute) qualifying spend.",
     "PARSED"),
    ("eurimages", "île-de-france",
     "allowed",
     "Eurimages support does not reduce IDF regional qualifying spend.",
     "PARSED"),
    ("eurimages", "nouvelle-aquitaine",
     "allowed",
     "Eurimages support does not reduce Nouvelle-Aquitaine regional qualifying spend.",
     "PARSED"),
    ("eurimages", "medienboard",
     "allowed",
     "Eurimages support does not reduce Medienboard Berlin-Brandenburg qualifying spend.",
     "PARSED"),
    ("eurimages", "wallimage",
     "allowed",
     "Eurimages support does not reduce Wallimage qualifying spend.",
     "PARSED"),
    ("eurimages", "vaf flanders",
     "allowed",
     "Eurimages support does not reduce VAF Flanders qualifying spend.",
     "PARSED"),
    ("eurimages", "film commission campania",
     "allowed",
     "Eurimages support does not reduce Campania regional qualifying spend.",
     "PARSED"),
    ("eurimages", "film commission torino piemonte",
     "allowed",
     "Eurimages support does not reduce Piemonte regional qualifying spend.",
     "PARSED"),
    ("eurimages", "apulia film",
     "allowed",
     "Eurimages support does not reduce Apulia regional qualifying spend.",
     "PARSED"),
    ("eurimages", "polski instytut",
     "allowed",
     "Eurimages support does not reduce PISF (Polish Film Institute) qualifying spend.",
     "PARSED"),
    ("eurimages", "czech film fund",
     "allowed",
     "Eurimages support does not reduce Czech Film Fund qualifying spend.",
     "PARSED"),
    ("eurimages", "national film institute (nfi hungary)",
     "allowed",
     "Eurimages support does not reduce NFI Hungary qualifying spend.",
     "PARSED"),
    ("eurimages", "instituto do cinema",
     "allowed",
     "Eurimages support does not reduce ICA Portugal qualifying spend.",
     "PARSED"),
    ("eurimages", "austrian film institute",
     "allowed",
     "Eurimages support does not reduce ÖFI (Austrian Film Institute) qualifying spend.",
     "PARSED"),
    ("eurimages", "film i väst",
     "allowed",
     "Eurimages support does not reduce Film i Väst (Sweden) qualifying spend.",
     "PARSED"),

    # Ibermedia + regional Spanish
    ("ibermedia", "icec",
     "allowed",
     "Ibermedia grant and Catalonia ICEC both operate on independent tracks.",
     "PARSED"),
    ("ibermedia", "basque audiovisual",
     "allowed",
     "Ibermedia grant and Basque Audiovisual fund operate on independent tracks.",
     "PARSED"),
    ("ibermedia", "agadic",
     "allowed",
     "Ibermedia grant and Galicia AGADIC operate on independent tracks.",
     "PARSED"),
    ("ibermedia", "instituto do cinema",
     "allowed",
     "Ibermedia grant and ICA Portugal grant operate on independent tracks.",
     "PARSED"),

    # Film i Väst + national
    ("film i väst", "svt — swedish",
     "allowed",
     "Film i Väst and SVT both operate as co-production sources on independent tracks.",
     "PARSED"),
    ("film i väst", "nordisk film",
     "allowed",
     "Film i Väst and Nordic Film & TV Fond operate on independent tracks.",
     "PARSED"),
]


def upgrade() -> None:
    conn = op.get_bind()

    def find_pid(fragment: str) -> object | None:
        row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs WHERE LOWER(name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{fragment.lower()}%"},
        ).fetchone()
        return row[0] if row else None

    for frag_a, frag_b, rule_type, condition_text, confidence_tier in _STACKING_RULES:
        pid_a = find_pid(frag_a)
        pid_b = find_pid(frag_b)
        if pid_a is None or pid_b is None:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO legal_stacking_rules
                    (id, program_a_id, program_b_id, rule_type, condition_text, confidence_tier,
                     created_at, updated_at)
                VALUES
                    (gen_random_uuid(), :a, :b, :rule_type, :condition_text, :confidence_tier,
                     now(), now())
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "a": pid_a,
                "b": pid_b,
                "rule_type": rule_type,
                "condition_text": condition_text,
                "confidence_tier": confidence_tier,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()

    def find_pid(fragment: str) -> object | None:
        row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs WHERE LOWER(name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{fragment.lower()}%"},
        ).fetchone()
        return row[0] if row else None

    for frag_a, frag_b, _rt, _ct, _conf in _STACKING_RULES:
        pid_a = find_pid(frag_a)
        pid_b = find_pid(frag_b)
        if pid_a is None or pid_b is None:
            continue
        conn.execute(
            sa.text(
                "DELETE FROM legal_stacking_rules "
                "WHERE (program_a_id = :a AND program_b_id = :b) "
                "   OR (program_a_id = :b AND program_b_id = :a)"
            ),
            {"a": pid_a, "b": pid_b},
        )
