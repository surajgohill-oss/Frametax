"""Legacy stacking-rule seed for the NL All-Spend credit with the federal PSTC and CPTC (NA-RECONCILIATION-10).

The canonical evaluator reads the code registry (app/optimization/stacking_rules.py, 1.9.0); the legacy database rows (read by run_full_analysis and the structures API) must agree.
Applied only where both program rows exist; downgrade removes exactly these rows.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0085"
down_revision = "0084"
branch_labels = None
depends_on = None

_NS = uuid.UUID("a1000000-0023-0000-0001-000000000000")
OCASE = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
ROWS = (
    ("pstc+nl_all_spend", "ca_federal_pstc", "ca_nl_all_spend_credit",
     "NL All-Spend credit (Regulation 31/23 s.2(c): 40% of eligible production costs less government assistance) is not reduced by the federal PSTC (s.2(m) excludes credits under ITA 125.4 and 125.5 "
     "from government assistance) and is assistance to the federal PSTC only to the extent reasonably in respect of Canadian labour (ITA 125.5(1)(b); CRA RC4385): labour share rate x labour, bounded by the credit."),
    ("cptc+nl_all_spend", "ca_federal_cptc", "ca_nl_all_spend_credit",
     "NL All-Spend credit (Regulation 31/23) is not reduced by the federal CPTC (s.2(m)(ii)); it is provincial assistance that reduces the production cost setting the 60% CPTC cap (CRA RC4164 lines 421-430); "
     "CPTC labour is not reduced."),
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
                   'spend_reduction', :cond, 'ITA 125.5(1); CRA RC4385 and RC4164; NL Regulation 31/23 s.2(m)', 'PARSED',
                   'NA-RECONCILIATION-10: NL credit as assistance to the federal credits.', :now, :now
            WHERE NOT EXISTS (SELECT 1 FROM legal_stacking_rules WHERE id = :id ::uuid)
              AND (SELECT id FROM incentive_programs WHERE slug = :a LIMIT 1) IS NOT NULL
              AND (SELECT id FROM incentive_programs WHERE slug = :b LIMIT 1) IS NOT NULL
        """), {"id": _rule_id(key), "a": slug_a, "b": slug_b, "cond": text, "now": now})


def downgrade() -> None:
    conn = op.get_bind()
    for key, *_ in ROWS:
        conn.execute(sa.text("DELETE FROM legal_stacking_rules WHERE id = :id"), {"id": _rule_id(key)})
