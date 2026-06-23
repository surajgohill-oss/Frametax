"""0051 — Phase D fund economics completion.

Adds fund_economics records for programs that previously lacked them:
  - DE-BB (Medienboard Berlin-Brandenburg)
  - DE-BW (MFG Baden-Württemberg)
  - DE-HH (Film Hamburg)
  - DE-MDM (Mitteldeutsche Medienförderung MDM)
  - DK (Danish Film Institute)
  - CA-SK (Creative Saskatchewan)
  - GB-NIR (Northern Ireland Screen)
  - GB-YRK (Screen Yorkshire)
  - IT regional (Lazio, Sicily, Tuscany, Campania, Piedmont, Apulia)
  - ES regional (Andalusia, Catalonia, Basque Country, Galicia, Valencia)

Revision ID: 0051
Revises: 0050
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0051"
down_revision: Union[str, None] = "0050"
branch_labels = None
depends_on = None


# fmt: off
_FUND_ECONOMICS: list[dict] = [
    # -------------------------------------------------------------------------
    # German regional funds
    # -------------------------------------------------------------------------
    {
        "program_name_fragment": "medienboard berlin",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 1_100_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Medienboard Berlin-Brandenburg: loans/grants up to €1M. Stackable with DFFF.",
    },
    {
        "program_name_fragment": "mfg baden",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "MFG Baden-Württemberg: loans up to €750k. Stackable with DFFF and FFA.",
    },
    {
        "program_name_fragment": "film hamburg",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 550_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Film Hamburg: repayable loans up to €500k. Stackable with DFFF.",
    },
    {
        "program_name_fragment": "mitteldeutsche",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "MDM Mitteldeutsche Medienförderung: loans up to €750k. Stackable with DFFF.",
    },
    # -------------------------------------------------------------------------
    # Danish Film Institute
    # -------------------------------------------------------------------------
    {
        "program_name_fragment": "danish film institute",
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": False,
        "typical_max_award_usd": 1_650_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "DFI: equity investment up to ~DKK 11M (~€1.5M). Recoupable from revenues.",
    },
    # -------------------------------------------------------------------------
    # Canadian provincial
    # -------------------------------------------------------------------------
    {
        "program_name_fragment": "creative saskatchewan",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": False,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 400_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Creative Saskatchewan: grants up to CAD ~$500k. Stackable with CPTC.",
    },
    # -------------------------------------------------------------------------
    # UK devolved nations
    # -------------------------------------------------------------------------
    {
        "program_name_fragment": "northern ireland screen",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": True,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 1_100_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Northern Ireland Screen: equity up to £1M. Stackable with AVEC.",
    },
    {
        "program_name_fragment": "screen yorkshire",
        "is_repayable": False,
        "is_recoupable": True,
        "has_equity_participation": True,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 550_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Screen Yorkshire: equity up to £500k recoupable. Stackable with AVEC.",
    },
    # -------------------------------------------------------------------------
    # Italian regional funds
    # -------------------------------------------------------------------------
    {
        "program_name_fragment": "lazio film commission",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 550_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Lazio Film Commission grants up to €500k. Stackable with MiC national credit.",
    },
    {
        "program_name_fragment": "sicilia film commission",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 330_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Sicilia Film Commission: grants. Stackable with MiC credit.",
    },
    {
        "program_name_fragment": "tuscany film commission",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 330_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Tuscany Film Commission: grants. Stackable with MiC credit.",
    },
    {
        "program_name_fragment": "campania film commission",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 275_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Campania Film Commission. Stackable with MiC credit.",
    },
    {
        "program_name_fragment": "piemonte",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 275_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Piemonte (Piedmont) Film Commission. Stackable with MiC credit.",
    },
    {
        "program_name_fragment": "apulia film fund",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 330_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Apulia Film Fund: grants. Stackable with MiC credit.",
    },
    # -------------------------------------------------------------------------
    # Spanish regional funds
    # -------------------------------------------------------------------------
    {
        "program_name_fragment": "andalusia film commission",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 275_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Andalusia film rebate/grant. Stackable with national ICAA credit.",
    },
    {
        "program_name_fragment": "catalonia film commission",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 275_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Catalonia (ICEC) film support. Stackable with national ICAA credit.",
    },
    {
        "program_name_fragment": "basque country film",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 330_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Basque Country film support (Kimuak). Stackable with national ICAA credit.",
    },
    {
        "program_name_fragment": "galicia film",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 220_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Galicia film support. Stackable with national ICAA credit.",
    },
    {
        "program_name_fragment": "valencia film commission",
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 220_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
        "notes": "Valencia film support. Stackable with national ICAA credit.",
    },
]
# fmt: on


def upgrade() -> None:
    conn = op.get_bind()
    for rec in _FUND_ECONOMICS:
        fragment = rec["program_name_fragment"]
        row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs WHERE LOWER(program_name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{fragment}%"},
        ).fetchone()
        if not row:
            continue
        program_id = row[0]
        conn.execute(
            sa.text(
                """
                INSERT INTO fund_economics (
                    program_id,
                    is_repayable, is_recoupable, has_equity_participation,
                    has_matching_requirement, has_territorial_spend_requirement,
                    typical_max_award_usd, is_competitive, stackable_with_incentives,
                    notes
                ) VALUES (
                    :program_id,
                    :is_repayable, :is_recoupable, :has_equity_participation,
                    :has_matching_requirement, :has_territorial_spend_requirement,
                    :typical_max_award_usd, :is_competitive, :stackable_with_incentives,
                    :notes
                )
                ON CONFLICT (program_id) DO UPDATE SET
                    is_repayable = EXCLUDED.is_repayable,
                    is_recoupable = EXCLUDED.is_recoupable,
                    has_equity_participation = EXCLUDED.has_equity_participation,
                    has_matching_requirement = EXCLUDED.has_matching_requirement,
                    has_territorial_spend_requirement = EXCLUDED.has_territorial_spend_requirement,
                    typical_max_award_usd = EXCLUDED.typical_max_award_usd,
                    is_competitive = EXCLUDED.is_competitive,
                    stackable_with_incentives = EXCLUDED.stackable_with_incentives,
                    notes = EXCLUDED.notes
                """
            ),
            {
                "program_id": program_id,
                "is_repayable": rec["is_repayable"],
                "is_recoupable": rec["is_recoupable"],
                "has_equity_participation": rec["has_equity_participation"],
                "has_matching_requirement": rec["has_matching_requirement"],
                "has_territorial_spend_requirement": rec["has_territorial_spend_requirement"],
                "typical_max_award_usd": rec["typical_max_award_usd"],
                "is_competitive": rec["is_competitive"],
                "stackable_with_incentives": rec["stackable_with_incentives"],
                "notes": rec.get("notes"),
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for rec in _FUND_ECONOMICS:
        fragment = rec["program_name_fragment"]
        row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs WHERE LOWER(program_name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{fragment}%"},
        ).fetchone()
        if not row:
            continue
        conn.execute(
            sa.text("DELETE FROM fund_economics WHERE program_id = :pid"),
            {"pid": row[0]},
        )
