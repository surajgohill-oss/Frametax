"""0052 — Phase D.5: expanded stacking interaction graph.

Adds legal_stacking_rules DB rows for:
  - UK devolved regions (Scotland, Wales, NIR, Yorkshire) + AVEC: allowed
  - German regional funds (FFF Bayern, Filmstiftung NRW, nordmedia) + DFFF: allowed
  - Italian regional funds + MiC national credit: allowed
  - Belgian tax shelter + regional funds (Wallimage, VAF, Screen.Brussels): allowed
  - Eurimages + DFFF: allowed
  - Eurimages + Belgian tax shelter: allowed
  - French national + French regional funds: allowed

Revision ID: 0052
Revises: 0051
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0052"
down_revision: Union[str, None] = "0051"
branch_labels = None
depends_on = None


# Each rule is: (program_a_name_fragment, program_b_name_fragment, rule_type, condition_text)
_RULES: list[tuple[str, str, str, str]] = [
    # -------------------------------------------------------------------------
    # UK devolved regions + AVEC
    # -------------------------------------------------------------------------
    (
        "creative scotland",
        "audio visual expenditure",
        "allowed",
        "Creative Scotland equity is co-financing, not government assistance. "
        "Does not reduce AVEC qualifying UK expenditure (HMRC BIM65500).",
    ),
    (
        "creative wales",
        "audio visual expenditure",
        "allowed",
        "Creative Wales equity is co-financing, not government assistance. "
        "Does not reduce AVEC qualifying UK expenditure.",
    ),
    (
        "northern ireland screen",
        "audio visual expenditure",
        "allowed",
        "Northern Ireland Screen funding is co-financing, not government assistance. "
        "Does not reduce AVEC qualifying UK expenditure.",
    ),
    (
        "screen yorkshire",
        "audio visual expenditure",
        "allowed",
        "Screen Yorkshire equity is co-financing, not government assistance. "
        "Does not reduce AVEC qualifying UK expenditure.",
    ),
    # -------------------------------------------------------------------------
    # German regional funds + DFFF
    # -------------------------------------------------------------------------
    (
        "filmfernsehfonds",
        "german federal film fund",
        "allowed",
        "FFF Bayern and DFFF operate on separate application tracks. "
        "Both may be claimed when production qualifies under each fund's criteria independently. "
        "Combined funding typically capped at 50% of production budget.",
    ),
    (
        "medienstiftung nrw",
        "german federal film fund",
        "allowed",
        "Filmstiftung NRW and DFFF operate on separate application tracks. "
        "Both may be claimed for the same production when qualifying criteria are met independently.",
    ),
    (
        "nordmedia",
        "german federal film fund",
        "allowed",
        "nordmedia (Lower Saxony / Bremen) and DFFF operate on separate application tracks. "
        "Both may be claimed for the same production.",
    ),
    # -------------------------------------------------------------------------
    # Italian regional funds + MiC national credit
    # -------------------------------------------------------------------------
    (
        "lazio film commission",
        "italian tax credit",
        "allowed",
        "Lazio Film Commission regional grants and Italian MiC national tax credit "
        "operate on independent tracks. Both claimable on qualifying Italian spend.",
    ),
    (
        "sicilia film commission",
        "italian tax credit",
        "allowed",
        "Sicilia Film Commission regional support and MiC national tax credit "
        "operate on independent tracks.",
    ),
    (
        "tuscany film commission",
        "italian tax credit",
        "allowed",
        "Tuscany Film Commission regional support and MiC national tax credit "
        "operate on independent tracks.",
    ),
    (
        "campania film commission",
        "italian tax credit",
        "allowed",
        "Campania Film Commission regional support and MiC national tax credit "
        "operate on independent tracks.",
    ),
    (
        "piemonte",
        "italian tax credit",
        "allowed",
        "Piemonte (Piedmont) regional support and MiC national tax credit "
        "operate on independent tracks.",
    ),
    (
        "apulia film fund",
        "italian tax credit",
        "allowed",
        "Apulia Film Fund regional support and MiC national tax credit "
        "operate on independent tracks.",
    ),
    # -------------------------------------------------------------------------
    # Belgian tax shelter + regional funds
    # -------------------------------------------------------------------------
    (
        "wallimage",
        "belgian tax shelter",
        "allowed",
        "Belgian tax shelter and Wallimage operate on independent tracks. "
        "Tax shelter is a financing instrument (investors buy tax shelter certificates); "
        "Wallimage is a regional production fund. "
        "Both may be used on the same production with Wallonia qualifying spend.",
    ),
    (
        "vaf flanders",
        "belgian tax shelter",
        "allowed",
        "Belgian tax shelter and VAF Flanders operate on independent tracks. "
        "Tax shelter is a financing instrument; VAF is a regional production fund. "
        "Both may be used on the same production with Flanders qualifying spend.",
    ),
    (
        "screen.brussels",
        "belgian tax shelter",
        "allowed",
        "Belgian tax shelter and Screen.Brussels operate on independent tracks. "
        "Both may be used on the same production with Brussels qualifying spend.",
    ),
    # -------------------------------------------------------------------------
    # Eurimages + DFFF
    # -------------------------------------------------------------------------
    (
        "eurimages",
        "german federal film fund",
        "allowed",
        "Eurimages support allocated to German co-producers does not reduce "
        "German qualifying expenditure for DFFF. Each fund applies to its own "
        "national qualifying spend independently.",
    ),
    # -------------------------------------------------------------------------
    # Eurimages + Belgian tax shelter
    # -------------------------------------------------------------------------
    (
        "eurimages",
        "belgian tax shelter",
        "allowed",
        "Eurimages support allocated to Belgian co-producers does not reduce "
        "Belgian tax shelter qualifying eligible expenditure. "
        "Both are available for the same official European co-production.",
    ),
    # -------------------------------------------------------------------------
    # French national + French regional funds
    # -------------------------------------------------------------------------
    (
        "avances sur recettes",
        "île-de-france",
        "allowed",
        "Île-de-France regional aid and CNC Avances sur Recettes operate on independent tracks. "
        "Both may be claimed for the same production with qualifying Paris-region spend.",
    ),
    (
        "avances sur recettes",
        "nouvelle-aquitaine",
        "allowed",
        "Nouvelle-Aquitaine regional aid and CNC national support operate on independent tracks.",
    ),
    (
        "avances sur recettes",
        "auvergne",
        "allowed",
        "Auvergne-Rhône-Alpes regional aid and CNC national support operate on independent tracks.",
    ),
    (
        "avances sur recettes",
        "occitanie",
        "allowed",
        "Occitanie regional aid and CNC national support operate on independent tracks.",
    ),
]


def upgrade() -> None:
    conn = op.get_bind()

    def find_program_id(fragment: str) -> object | None:
        row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs "
                "WHERE LOWER(name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{fragment.lower()}%"},
        ).fetchone()
        return row[0] if row else None

    inserted = 0
    skipped = 0
    for frag_a, frag_b, rule_type, condition_text in _RULES:
        pid_a = find_program_id(frag_a)
        pid_b = find_program_id(frag_b)
        if pid_a is None or pid_b is None:
            skipped += 1
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO legal_stacking_rules
                    (id, program_a_id, program_b_id, rule_type, condition_text, confidence_tier,
                     created_at, updated_at)
                VALUES
                    (gen_random_uuid(), :a, :b, :rule_type, :condition_text, 'PARSED',
                     now(), now())
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "a": pid_a,
                "b": pid_b,
                "rule_type": rule_type,
                "condition_text": condition_text,
            },
        )
        inserted += 1


def downgrade() -> None:
    conn = op.get_bind()

    def find_program_id(fragment: str) -> object | None:
        row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs "
                "WHERE LOWER(name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{fragment.lower()}%"},
        ).fetchone()
        return row[0] if row else None

    for frag_a, frag_b, _rule_type, _condition in _RULES:
        pid_a = find_program_id(frag_a)
        pid_b = find_program_id(frag_b)
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
