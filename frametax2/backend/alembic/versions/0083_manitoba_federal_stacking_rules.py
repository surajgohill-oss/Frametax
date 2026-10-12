"""0083 - seed the Manitoba film credit stacking rules with the federal CPTC and PSTC (code registry stacking_rules 1.7.0).

Manitoba Film & Music TC-2 Cost of Production Tax Credit Guidelines (Revised June 2024): the Manitoba credit "is compatible with the Canadian Film or Video Production
Tax Credit (CPTC) and the Film or Video Production Services Tax Credit (PSTC)", and Manitoba's own "government assistance" excludes any film and video production tax
credit under the Manitoba or federal Act. The Manitoba credit is assistance to the federal credits: it lowers the production cost behind the CPTC 60% cap (CRA RC4164)
and, to the extent it relates to labour, the PSTC qualified Canadian labour expenditure (ITA 125.5(1)); the whole credit is the conservative reduction until the labour
share is stated. Rows are inserted only when both programs exist in incentive_programs. Applying this migration is a database change left to an authorized upgrade.

Revision ID: 0083
Revises: 0082
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0083"
down_revision = "0082"
branch_labels = None
depends_on = None

_NS = uuid.UUID("a1000000-0022-0000-0001-000000000000")
PSTC_MB_ID = str(uuid.uuid5(_NS, "rule:pstc+mb_film:spend_reduction"))
CPTC_MB_ID = str(uuid.uuid5(_NS, "rule:cptc+mb_film:spend_reduction"))
ROWS = (
    (PSTC_MB_ID, "ca_federal_pstc", "ca_mb_film_video_credit",
     "Manitoba TC-2 guidelines (June 2024): compatible with the federal PSTC; the Manitoba credit is assistance that reduces the PSTC labour expenditure to the extent it relates to "
     "labour (ITA 125.5(1)); the whole credit, bounded by the federal labour, is the conservative reduction until the labour share is stated."),
    (CPTC_MB_ID, "ca_federal_cptc", "ca_mb_film_video_credit",
     "Manitoba TC-2 guidelines (June 2024): compatible with the federal CPTC; the Manitoba credit is assistance that reduces the production cost behind the 60% CPTC cap "
     "(CRA RC4164 lines 421-430); labour itself is not reduced."),
)


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc).isoformat()
    for rule_id, slug_a, slug_b, text in ROWS:
        conn.execute(sa.text("""
            INSERT INTO legal_stacking_rules (id, program_a_id, program_b_id, rule_type, condition_text, statutory_reference, confidence_tier, notes, created_at, updated_at)
            SELECT :id, (SELECT id FROM incentive_programs WHERE slug = :a LIMIT 1), (SELECT id FROM incentive_programs WHERE slug = :b LIMIT 1),
                   'spend_reduction', :cond, 'Manitoba Film & Music TC-2 guidelines (Revised June 2024); ITA 125.5(1); CRA RC4164', 'PARSED',
                   'Closeout pass: Manitoba credit compatible with the federal credits and assistance to them.', :now, :now
            WHERE NOT EXISTS (SELECT 1 FROM legal_stacking_rules WHERE id = :id ::uuid)
              AND (SELECT id FROM incentive_programs WHERE slug = :a LIMIT 1) IS NOT NULL
              AND (SELECT id FROM incentive_programs WHERE slug = :b LIMIT 1) IS NOT NULL
        """), {"id": rule_id, "a": slug_a, "b": slug_b, "cond": text, "now": now})


def downgrade() -> None:
    conn = op.get_bind()
    for rule_id, *_ in ROWS:
        conn.execute(sa.text("DELETE FROM legal_stacking_rules WHERE id = :id"), {"id": rule_id})
