"""0082 - correct the seeded Ontario OPSTC stacking rules (NA-CODEX-08).

Migration 0022 seeded CPTC + OPSTC as mutually_exclusive. The Ontario Creates OPSTC Guidelines (May 2025) s.1.01 say the OPSTC "may be claimed alone, or in
addition to a federal Film or Video Production Services Tax Credit (or a Canadian Film or Video Production Tax Credit)". The mutual exclusivity is between the two
FEDERAL credits (CPTC / PSTC) and between the domestic OFTTC and the service OPSTC; it is not between the OPSTC and either federal credit.

  * CPTC + OPSTC becomes spend_reduction: the provincial credit is assistance that lowers the production cost behind the CPTC 60% cap (CRA RC4164, T1131 lines
    421-430); labour itself is not reduced.
  * Federal PSTC + OPSTC is added as spend_reduction: only the LABOUR portion of the OPSTC is assistance to the PSTC (OPSTC Guidelines s.3.02).
  * OFTTC + OPSTC (0022) and CPTC + PSTC stay mutually_exclusive.

The canonical evaluator reads the code registry (app/optimization/stacking_rules.py, version 1.6.0); this keeps the legacy database table in agreement. Applying this
migration is a database change and is left to an authorized upgrade.

Revision ID: 0082
Revises: 0081
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0082"
down_revision = "0081"
branch_labels = None
depends_on = None

_NS = uuid.UUID("a1000000-0022-0000-0001-000000000000")          # the 0022 namespace: the corrected row keeps its id
CPTC_OPSTC_ID = str(uuid.uuid5(_NS, "rule:cptc+opstc:mutually_exclusive"))
PSTC_OPSTC_ID = str(uuid.uuid5(_NS, "rule:pstc+opstc:spend_reduction"))

CPTC_OPSTC_TEXT = (
    "Ontario Creates OPSTC Guidelines (May 2025) s.1.01 permit the OPSTC to be claimed in addition to the federal CPTC. CRA RC4164 (Form T1131 guide, lines "
    "421-430): the provincial credit is assistance that reduces the PRODUCTION COST which sets the CPTC cap: qualified labour expenditure = the lesser of the labour "
    "expenditure and 60% x (production cost - assistance); labour itself is not reduced."
)
PSTC_OPSTC_TEXT = (
    "Ontario Creates OPSTC Guidelines (May 2025) s.1.01 permit the OPSTC in addition to the federal PSTC; s.3.02: provincial tax credits are assistance but only the "
    "LABOUR portion of the OPSTC constitutes assistance, which reduces the PSTC labour expenditure. Federal credits are not assistance to the OPSTC."
)
_OLD_TYPE = "mutually_exclusive"
_OLD_TEXT = (
    "CPTC applies only to 'Canadian film or video productions' (domestic Canadian content). OPSTC applies only to 'accredited film or video productions' "
    "(foreign service productions). A production cannot simultaneously qualify for both CPTC and OPSTC — the production type is mutually exclusive."
)


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(sa.text(
        "UPDATE legal_stacking_rules SET rule_type = 'spend_reduction', condition_text = :cond, "
        "statutory_reference = 'Ontario Creates OPSTC Guidelines (May 2025) s.1.01; CRA RC4164 (T1131 guide) lines 421-430', "
        "notes = 'NA-CODEX-08: allowed with spend_reduction (assistance lowers the CPTC 60% cost cap); corrects the 0022 mutually_exclusive seed.', updated_at = :now "
        "WHERE id = :id"), {"id": CPTC_OPSTC_ID, "cond": CPTC_OPSTC_TEXT, "now": now})
    conn.execute(sa.text("""
        INSERT INTO legal_stacking_rules (id, program_a_id, program_b_id, rule_type, condition_text, statutory_reference, confidence_tier, notes, created_at, updated_at)
        SELECT :id, (SELECT id FROM incentive_programs WHERE slug = 'ca_federal_pstc' LIMIT 1), (SELECT id FROM incentive_programs WHERE slug = 'on_opstc' LIMIT 1),
               'spend_reduction', :cond, 'Ontario Creates OPSTC Guidelines (May 2025) s.1.01 and s.3.02', 'PARSED',
               'NA-CODEX-08: only the labour portion of the OPSTC is assistance to the federal PSTC.', :now, :now
        WHERE NOT EXISTS (SELECT 1 FROM legal_stacking_rules WHERE id = :id ::uuid)
          AND (SELECT id FROM incentive_programs WHERE slug = 'ca_federal_pstc' LIMIT 1) IS NOT NULL
          AND (SELECT id FROM incentive_programs WHERE slug = 'on_opstc' LIMIT 1) IS NOT NULL
    """), {"id": PSTC_OPSTC_ID, "cond": PSTC_OPSTC_TEXT, "now": now})


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM legal_stacking_rules WHERE id = :id"), {"id": PSTC_OPSTC_ID})
    conn.execute(sa.text("UPDATE legal_stacking_rules SET rule_type = :t, condition_text = :c WHERE id = :id"),
                 {"id": CPTC_OPSTC_ID, "t": _OLD_TYPE, "c": _OLD_TEXT})
