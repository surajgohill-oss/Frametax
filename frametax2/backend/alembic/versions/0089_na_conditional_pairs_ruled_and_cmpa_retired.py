"""Legacy stacking-rule parity for NA-RECONCILIATION-13 (stacking rules 1.15.0).

The canonical evaluator reads the code registry (app/optimization/stacking_rules.py); the legacy database rows (read by run_full_analysis and the structures API) must agree.
- The two rows 0086 seeded as `conditional` (BC DAVE + CPTC, OFTTC + federal PSTC) become `spend_reduction`: no statute bars either combination (O. Reg. 37/09 s.29(4); Income Tax Regulations s.9300;
  ITA (BC) s.79(1), s.81.2(1)(a)), and the provincial credit is assistance to the federal credit.
- The BC film and television credit + federal PSTC row is inserted as `spend_reduction` where both program rows exist.
- The rows touching the retired "ca_cmpa_foreign" spelling are deleted: the Canadian Media Producers Association issues no certificate, and the "OFTTC needs no Canadian content certification" premise of the OFTTC row is
  contradicted by O. Reg. 37/09 s.27.1 para 7. The federal service-production credit is the PSTC.
Downgrade restores the two 0086 rows to their `conditional` text and removes the inserted row; the deleted CMPA rows are not restored (they rested on an unofficial credit name).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0089"
down_revision = "0088"
branch_labels = None
depends_on = None

_NS = uuid.UUID("a1000000-0024-0000-0001-000000000000")


def _rule_id(key: str) -> str:
    return str(uuid.uuid5(_NS, f"rule:{key}"))


_RULED = {
    "dave+cptc": (
        "spend_reduction",
        "BC DAVE is provincial assistance to the federal CPTC (it lowers the production cost that sets the 60% cap, CRA RC4164 Part 5 lines 421-430); no text bars the combination (ITA (BC) s.79(1), s.81.2(1)(a)). "
        "DAVE is claimable only with its host credit (s.80, or s.82.1 for the services credit).",
    ),
    "ofttc+pstc": (
        "spend_reduction",
        "O. Reg. 37/09 s.29(4): ITA 125.5 assistance is not OFTTC assistance; Income Tax Regulations s.9300 gives the accredited production no Canadian-content test; CAVCO bars the PSTC only where the CPTC was received. "
        "The OFTTC is labour-only and nets the PSTC labour in full (ITA 125.5(1) paragraph (b)).",
    ),
}
_OLD = {
    "dave+cptc": ("conditional", "Income Tax Act (BC) s.82.3(1)(a), s.81.2, s.80: DAVE is tied to a BC credit the planner does not hold; no primary text states the DAVE-with-CPTC combination: unresolved."),
    "ofttc+pstc": ("conditional", "No primary text states the OFTTC-with-PSTC combination (Ontario Creates OFTTC page and the PSTC guidelines are silent); the CPTC-exclusion route is an inference: unresolved."),
}
_INSERT_KEY = "bcfilmtv+pstc"
_INSERT = ("ca_bc_film_tv_tax_credit", "ca_federal_pstc", "spend_reduction",
           "Income Tax Act (BC) s.79(1) excludes the federal credits from BC assistance and s.80 states no PSTC bar; Income Tax Regulations s.9300 gives the accredited production no Canadian-content test. "
           "The BC credit is labour-only and nets the PSTC labour in full (ITA 125.5(1) paragraph (b)).")


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc).isoformat()
    for key, (rt, text) in _RULED.items():
        conn.execute(sa.text("UPDATE legal_stacking_rules SET rule_type = :rt, condition_text = :t, updated_at = :now WHERE id = :id"),
                     {"rt": rt, "t": text, "now": now, "id": _rule_id(key)})
    a, b, rt, text = _INSERT
    conn.execute(sa.text("""
        INSERT INTO legal_stacking_rules (id, program_a_id, program_b_id, rule_type, condition_text, statutory_reference, confidence_tier, notes, created_at, updated_at)
        SELECT :id, (SELECT id FROM incentive_programs WHERE slug = :a LIMIT 1), (SELECT id FROM incentive_programs WHERE slug = :b LIMIT 1),
               :rt, :cond, 'ITA 125.5(1); ITA (BC) s.79(1), s.80', 'PARSED', 'NA-RECONCILIATION-13: previously conditional pair.', :now, :now
        WHERE NOT EXISTS (SELECT 1 FROM legal_stacking_rules WHERE id = :id ::uuid)
          AND (SELECT id FROM incentive_programs WHERE slug = :a LIMIT 1) IS NOT NULL
          AND (SELECT id FROM incentive_programs WHERE slug = :b LIMIT 1) IS NOT NULL
    """), {"id": _rule_id(_INSERT_KEY), "a": a, "b": b, "rt": rt, "cond": text, "now": now})
    conn.execute(sa.text("""
        DELETE FROM legal_stacking_rules
        WHERE program_a_id IN (SELECT id FROM incentive_programs WHERE slug = 'ca_cmpa_foreign')
           OR program_b_id IN (SELECT id FROM incentive_programs WHERE slug = 'ca_cmpa_foreign')
    """))


def downgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc).isoformat()
    for key, (rt, text) in _OLD.items():
        conn.execute(sa.text("UPDATE legal_stacking_rules SET rule_type = :rt, condition_text = :t, updated_at = :now WHERE id = :id"),
                     {"rt": rt, "t": text, "now": now, "id": _rule_id(key)})
    conn.execute(sa.text("DELETE FROM legal_stacking_rules WHERE id = :id"), {"id": _rule_id(_INSERT_KEY)})
