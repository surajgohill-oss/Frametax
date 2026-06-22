"""0040 — Phase C completion: confidence tier promotions batch 2.

PARSED → VERIFIED (6 programs — all core fields confirmed from official sources):
  ca_federal_cptc     — CAVCO / CRA T4283 (CPTC base rate 25% QCLE)
  us_ga_film_credit   — Georgia Film Office (EIIA 20% base, transferable)
  us_la_film_incentive — Louisiana Entertainment (25% base, transferable)
  us_nm_film_credit   — New Mexico Film Office (25% base, refundable)
  us_ny_film_credit   — NY ESD Film Tax Credit (25% base, refundable)
  us_or_opif          — Oregon Film Office (20% OPIF cash rebate)

Revision ID: 0040
Revises: 0039
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0040"
down_revision: Union[str, None] = "0039"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

_TO_VERIFIED: list[str] = [
    "ca_federal_cptc",
    "us_ga_film_credit",
    "us_la_film_incentive",
    "us_nm_film_credit",
    "us_ny_film_credit",
    "us_or_opif",
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
