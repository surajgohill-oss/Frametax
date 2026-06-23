"""0050 — Seed Phase C regional funds: FR/BE/DE regional programs.

Adds 8 new programs to the DB:
  - FR-IDF (Île-de-France Cinema)
  - FR-NAQ (Nouvelle-Aquitaine)
  - FR-ARA (Auvergne-Rhône-Alpes)
  - FR-OCC (Occitanie)
  - BE-WAL (Wallimage)
  - BE-VLG (VAF Flanders)
  - BE-BRU (Screen.Brussels)
  - DE-NI (nordmedia)

Also ensures matching jurisdiction rows exist.
Seeds fund_economics records for each new program.

Revision ID: 0050
Revises: 0049
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0050"
down_revision: Union[str, None] = "0049"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Jurisdiction rows to ensure
# ---------------------------------------------------------------------------
_JURISDICTIONS = [
    {"code": "FR-IDF", "name": "Île-de-France, France",       "region": "Europe", "country_code": "FR"},
    {"code": "FR-NAQ", "name": "Nouvelle-Aquitaine, France",   "region": "Europe", "country_code": "FR"},
    {"code": "FR-ARA", "name": "Auvergne-Rhône-Alpes, France", "region": "Europe", "country_code": "FR"},
    {"code": "FR-OCC", "name": "Occitanie, France",            "region": "Europe", "country_code": "FR"},
    {"code": "BE-WAL", "name": "Wallonia, Belgium",            "region": "Europe", "country_code": "BE"},
    {"code": "BE-VLG", "name": "Flanders, Belgium",            "region": "Europe", "country_code": "BE"},
    {"code": "BE-BRU", "name": "Brussels-Capital, Belgium",    "region": "Europe", "country_code": "BE"},
    {"code": "DE-NI",  "name": "Lower Saxony / Bremen, Germany", "region": "Europe", "country_code": "DE"},
]

# ---------------------------------------------------------------------------
# Incentive programs
# ---------------------------------------------------------------------------
_PROGRAMS = [
    {
        "jurisdiction_code": "FR-IDF",
        "program_name": "Île-de-France Cinema Regional Aid",
        "program_type": "regional_fund",
        "base_rate": None,
        "description": (
            "Région Île-de-France supports feature films and documentaries with a "
            "significant production footprint in the Paris region. "
            "Grant amounts vary; typically €50k–€300k per project."
        ),
        "confidence_tier": "DISCOVERY",
    },
    {
        "jurisdiction_code": "FR-NAQ",
        "program_name": "Nouvelle-Aquitaine Regional Cinema Aid",
        "program_type": "regional_fund",
        "base_rate": None,
        "description": (
            "Région Nouvelle-Aquitaine supports film and audiovisual productions "
            "filmed in the region (Bordeaux, Dordogne, Basque Country). "
            "Grant typically €30k–€200k."
        ),
        "confidence_tier": "DISCOVERY",
    },
    {
        "jurisdiction_code": "FR-ARA",
        "program_name": "Auvergne-Rhône-Alpes Cinema Regional Aid",
        "program_type": "regional_fund",
        "base_rate": None,
        "description": (
            "Région Auvergne-Rhône-Alpes supports feature films and series. "
            "Grant typically €30k–€200k per project."
        ),
        "confidence_tier": "DISCOVERY",
    },
    {
        "jurisdiction_code": "FR-OCC",
        "program_name": "Occitanie Cinema Regional Aid",
        "program_type": "regional_fund",
        "base_rate": None,
        "description": (
            "Région Occitanie supports productions with a spend footprint in "
            "southern France. Grant amounts €20k–€150k."
        ),
        "confidence_tier": "DISCOVERY",
    },
    {
        "jurisdiction_code": "BE-WAL",
        "program_name": "Wallimage Co-production Fund",
        "program_type": "regional_fund",
        "base_rate": None,
        "description": (
            "Wallimage is the Wallonia regional film fund. "
            "Provides repayable advances and grants to productions with "
            "a significant spend in Wallonia. Typical investment €100k–€500k."
        ),
        "confidence_tier": "DISCOVERY",
    },
    {
        "jurisdiction_code": "BE-VLG",
        "program_name": "VAF Flanders Audiovisual Fund",
        "program_type": "regional_fund",
        "base_rate": None,
        "description": (
            "VAF (Vlaams Audiovisueel Fonds) is the Flemish regional film fund. "
            "Production support typically €100k–€750k per project."
        ),
        "confidence_tier": "DISCOVERY",
    },
    {
        "jurisdiction_code": "BE-BRU",
        "program_name": "Screen.Brussels Production Support",
        "program_type": "regional_fund",
        "base_rate": None,
        "description": (
            "Screen.Brussels is the Brussels-Capital Region film fund. "
            "Grants €20k–€200k. Stackable with Belgian tax shelter and VAF/Wallimage."
        ),
        "confidence_tier": "DISCOVERY",
    },
    {
        "jurisdiction_code": "DE-NI",
        "program_name": "nordmedia Film und Mediengesellschaft",
        "program_type": "regional_fund",
        "base_rate": None,
        "description": (
            "nordmedia is the regional media fund for Lower Saxony and Bremen. "
            "Provides production funding (typically 15–25% of German qualifying spend "
            "up to €750k per project). Stackable with DFFF and FFA."
        ),
        "confidence_tier": "DISCOVERY",
    },
]

# ---------------------------------------------------------------------------
# Fund economics for Phase C programs
# ---------------------------------------------------------------------------
_FUND_ECONOMICS = {
    "Île-de-France Cinema Regional Aid": {
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 330_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
    },
    "Nouvelle-Aquitaine Regional Cinema Aid": {
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 220_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
    },
    "Auvergne-Rhône-Alpes Cinema Regional Aid": {
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 220_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
    },
    "Occitanie Cinema Regional Aid": {
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 165_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
    },
    "Wallimage Co-production Fund": {
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 550_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
    },
    "VAF Flanders Audiovisual Fund": {
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
    },
    "Screen.Brussels Production Support": {
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 220_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
    },
    "nordmedia Film und Mediengesellschaft": {
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "has_matching_requirement": True,
        "has_territorial_spend_requirement": True,
        "typical_max_award_usd": 825_000,
        "is_competitive": True,
        "stackable_with_incentives": True,
    },
}


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Ensure jurisdiction rows exist
    for j in _JURISDICTIONS:
        conn.execute(
            sa.text(
                """
                INSERT INTO jurisdictions (code, name, region, country_code)
                VALUES (:code, :name, :region, :country_code)
                ON CONFLICT (code) DO NOTHING
                """
            ),
            j,
        )

    # 2. Insert incentive_programs and capture IDs
    program_ids: dict[str, object] = {}
    for p in _PROGRAMS:
        row = conn.execute(
            sa.text(
                """
                INSERT INTO incentive_programs
                    (jurisdiction_code, program_name, program_type, base_rate,
                     description, confidence_tier)
                VALUES
                    (:jurisdiction_code, :program_name, :program_type, :base_rate,
                     :description, :confidence_tier)
                ON CONFLICT DO NOTHING
                RETURNING id
                """
            ),
            p,
        ).fetchone()
        if row:
            program_ids[p["program_name"]] = row[0]
        else:
            row2 = conn.execute(
                sa.text(
                    "SELECT id FROM incentive_programs WHERE program_name = :name"
                ),
                {"name": p["program_name"]},
            ).fetchone()
            if row2:
                program_ids[p["program_name"]] = row2[0]

    # 3. Insert fund_economics
    for prog_name, econ in _FUND_ECONOMICS.items():
        prog_id = program_ids.get(prog_name)
        if not prog_id:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO fund_economics (
                    program_id,
                    is_repayable, is_recoupable, has_equity_participation,
                    has_matching_requirement, has_territorial_spend_requirement,
                    typical_max_award_usd, is_competitive, stackable_with_incentives
                ) VALUES (
                    :program_id,
                    :is_repayable, :is_recoupable, :has_equity_participation,
                    :has_matching_requirement, :has_territorial_spend_requirement,
                    :typical_max_award_usd, :is_competitive, :stackable_with_incentives
                )
                ON CONFLICT (program_id) DO NOTHING
                """
            ),
            {"program_id": prog_id, **econ},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for p in _PROGRAMS:
        conn.execute(
            sa.text(
                "DELETE FROM incentive_programs WHERE program_name = :name"
            ),
            {"name": p["program_name"]},
        )
    for j in _JURISDICTIONS:
        conn.execute(
            sa.text("DELETE FROM jurisdictions WHERE code = :code"),
            {"code": j["code"]},
        )
