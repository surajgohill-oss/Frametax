"""Legacy stacking-rule seed for the federal PSTC with the BC PSTC, the Quebec PSTC and OCASE, and for the CPTC with OCASE (NA-RECONCILIATION-09).

The canonical evaluator reads the code registry (app/optimization/stacking_rules.py, 1.8.0); the legacy database rows (read by run_full_analysis and the structures API) must agree.
Applied only where both program rows exist; downgrade removes exactly these rows.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0084"
down_revision = "0083"
branch_labels = None
depends_on = None

_NS = uuid.UUID("a1000000-0022-0000-0001-000000000000")
OCASE = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
ROWS = (
    ("pstc+bc_pstc", "ca_federal_pstc", "ca_bc_pstc",
     "BC production services tax credit is computed on qualified BC labour, so the whole credit is assistance in respect of labour to the federal PSTC (ITA 125.5(1); CRA RC4385) and reduces its labour "
     "expenditure; the federal PSTC is not assistance to the BC credit (Income Tax Act (BC) s.79(1) 'assistance' excludes amounts deemed paid under ITA 125.5(3))."),
    ("pstc+qc_pstc", "ca_federal_pstc", "ca_qc_pstc",
     "Quebec services credit (25% of all-spend production costs; SODEC fact sheet March 2026) is not reduced by the federal PSTC (Revenu Quebec CO-1029.8.36.SP note 7) and is assistance to the PSTC "
     "only to the extent reasonably in respect of labour (rate x labour, bounded by the credit; ITA 125.5(1))."),
    ("pstc+ocase", "ca_federal_pstc", OCASE,
     "OCASE (18% of eligible Ontario labour) is assistance wholly in respect of labour to the federal PSTC (OPSTC Guidelines s.1.05(E); CRA RC4385); federal credits are not assistance to OCASE."),
    ("cptc+ocase", "ca_federal_cptc", OCASE,
     "OCASE is a provincial credit and assistance that reduces the production cost setting the 60% CPTC cap (CRA RC4164 lines 421-430); CPTC labour is not reduced."),
)


def _rule_id(key: str) -> str:
    return str(uuid.uuid5(_NS, f"rule:{key}:spend_reduction"))


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc).isoformat()
    for key, slug_a, slug_b, text in ROWS:
        conn.execute(sa.text("""
            INSERT INTO legal_stacking_rules (id, program_a_id, program_b_id, rule_type, condition_text, statutory_reference, confidence_tier, notes, created_at, updated_at)
            SELECT :id, (SELECT id FROM incentive_programs WHERE slug = :a LIMIT 1), (SELECT id FROM incentive_programs WHERE slug = :b LIMIT 1),
                   'spend_reduction', :cond, 'ITA 125.5(1); CRA RC4385 and RC4164; provincial and Ontario Creates sources named in the condition', 'PARSED',
                   'NA-RECONCILIATION-09: provincial credit as assistance to the federal credits.', :now, :now
            WHERE NOT EXISTS (SELECT 1 FROM legal_stacking_rules WHERE id = :id ::uuid)
              AND (SELECT id FROM incentive_programs WHERE slug = :a LIMIT 1) IS NOT NULL
              AND (SELECT id FROM incentive_programs WHERE slug = :b LIMIT 1) IS NOT NULL
        """), {"id": _rule_id(key), "a": slug_a, "b": slug_b, "cond": text, "now": now})


def downgrade() -> None:
    conn = op.get_bind()
    for key, *_ in ROWS:
        conn.execute(sa.text("DELETE FROM legal_stacking_rules WHERE id = :id"), {"id": _rule_id(key)})
