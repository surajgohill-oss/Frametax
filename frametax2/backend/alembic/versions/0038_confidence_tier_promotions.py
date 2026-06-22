"""0038 — Phase C confidence tier promotions.

PARSED → VERIFIED (5 programs — all core fields confirmed from primary sources):
  uk_avec           — HMRC Creative Industries guidance (AVEC)
  ie_section_481    — Revenue Commissioners Section 481 guidance
  gr_cash_rebate    — Enterprise Greece / EKOME official programme
  fr_trip           — CNC TRIP official programme page
  it_tax_credit_foreign — MiC/DGCinema official programme page

DISCOVERY → PARSED (12 programs — source URL confirmed, base rate non-null):
  Wave-3 US states: us_ga_film_credit, us_la_film_incentive,
                    us_nm_film_credit, us_ny_film_credit
  Extended:         us_or_opif, es_tax_credit_foreign, de_dfff,
                    be_tax_shelter, hu_hipa_rebate, hr_cash_rebate,
                    au_location_offset, nz_spg_international

Revision ID: 0038
Revises: 0037
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0038"
down_revision: Union[str, None] = "0037"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

_TO_VERIFIED: list[str] = [
    "uk_avec",
    "ie_section_481",
    "gr_cash_rebate",
    "fr_trip",
    "it_tax_credit_foreign",
]

_TO_PARSED: list[str] = [
    # Wave-3 US states
    "us_ga_film_credit",
    "us_la_film_incentive",
    "us_nm_film_credit",
    "us_ny_film_credit",
    # Extended programs
    "us_or_opif",
    "es_tax_credit_foreign",
    "de_dfff",
    "be_tax_shelter",
    "hu_hipa_rebate",
    "hr_cash_rebate",
    "au_location_offset",
    "nz_spg_international",
]


def upgrade() -> None:
    conn = op.get_bind()
    for slug in _TO_VERIFIED:
        conn.execute(
            sa.text("""
                UPDATE incentive_programs
                SET confidence_tier = 'VERIFIED', updated_at = :now
                WHERE slug = :slug
            """),
            {"slug": slug, "now": NOW},
        )
    for slug in _TO_PARSED:
        conn.execute(
            sa.text("""
                UPDATE incentive_programs
                SET confidence_tier = 'PARSED', updated_at = :now
                WHERE slug = :slug
                  AND confidence_tier = 'DISCOVERY'
            """),
            {"slug": slug, "now": NOW},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for slug in _TO_VERIFIED:
        conn.execute(
            sa.text("""
                UPDATE incentive_programs
                SET confidence_tier = 'PARSED', updated_at = :now
                WHERE slug = :slug
            """),
            {"slug": slug, "now": NOW},
        )
    for slug in _TO_PARSED:
        conn.execute(
            sa.text("""
                UPDATE incentive_programs
                SET confidence_tier = 'DISCOVERY', updated_at = :now
                WHERE slug = :slug
            """),
            {"slug": slug, "now": NOW},
        )
