"""Legacy stacking-rule seed for the ten NA pairs that had no named rule (NA-RECONCILIATION-12).

The canonical evaluator reads the code registry (app/optimization/stacking_rules.py, 1.10.0); the legacy database rows (read by run_full_analysis and the structures API) must agree.
Applied only where both program rows exist; downgrade removes exactly these rows.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0086"
down_revision = "0085"
branch_labels = None
depends_on = None

_NS = uuid.UUID("a1000000-0024-0000-0001-000000000000")
CPTC_SIDE = "provincial assistance lowers the production cost setting the 60% CPTC cap (CRA RC4164, Part 5 lines 421-430); CPTC labour is not reduced"
PSTC_SIDE = "assistance reasonably in respect of Canadian labour lowers PSTC labour (ITA 125.5(1)(b); CRA RC4385)"
ROWS = (
    ("ab+cptc", "ca_ab_fttc", "ca_federal_cptc", "spend_reduction",
     "Alberta FTTC Guidelines (June 2026, s.2.4.7, Appendix I): claimable with the CPTC and not reduced by it; " + CPTC_SIDE + "."),
    ("ab+pstc", "ca_ab_fttc", "ca_federal_pstc", "spend_reduction",
     "Alberta FTTC Guidelines (June 2026, s.2.4.7, Appendix I): claimable with the PSTC and not reduced by it; " + PSTC_SIDE + "; all-spend credit, labour share rate x PSTC labour (disclosed assumption, whole credit as lower bound)."),
    ("dave+pstc", "ca_bc_dave", "ca_federal_pstc", "spend_reduction",
     "Income Tax Act (BC) s.79(1), s.82.3: the federal PSTC is not BC assistance; DAVE is a labour-only credit and " + PSTC_SIDE + ", in full."),
    ("dave+cptc", "ca_bc_dave", "ca_federal_cptc", "conditional",
     "Income Tax Act (BC) s.82.3(1)(a), s.81.2, s.80: DAVE is tied to a BC credit the planner does not hold; no primary text states the DAVE-with-CPTC combination: unresolved."),
    ("nb+cptc", "ca_nb_film_tax_credit", "ca_federal_cptc", "spend_reduction",
     "New Brunswick THC guidelines: discretionary incentive, text silent on federal credits; federal side: " + CPTC_SIDE + ". Only an awarded amount is assistance."),
    ("nb+pstc", "ca_nb_film_tax_credit", "ca_federal_pstc", "spend_reduction",
     "New Brunswick THC guidelines: discretionary incentive, text silent on federal credits; federal side: " + PSTC_SIDE + "; labour share rate x PSTC labour (disclosed assumption). Only an awarded amount is assistance."),
    ("ns+cptc", "ca_ns_production_incentive_fund", "ca_federal_cptc", "spend_reduction",
     "Nova Scotia Production Incentive Fund Guidelines (April 2024, s.3.2): federal credit calculations may be financing, no federal-reduction clause; federal side: " + CPTC_SIDE + ". Only an awarded amount is assistance."),
    ("ns+pstc", "ca_ns_production_incentive_fund", "ca_federal_pstc", "spend_reduction",
     "Nova Scotia Production Incentive Fund Guidelines (April 2024, s.3.2): federal credit calculations may be financing, no federal-reduction clause; federal side: " + PSTC_SIDE + "; labour share rate x PSTC labour (disclosed assumption). Only an awarded amount is assistance."),
    ("sk+pstc", "ca_sk_creative_saskatchewan_grant", "ca_federal_pstc", "spend_reduction",
     "Creative Saskatchewan FY 2026/27 guidelines: discretionary assessed grant, federal credits may be financing; federal side: " + PSTC_SIDE + "; labour share rate x PSTC labour (disclosed assumption). Only an awarded amount is assistance."),
    ("ofttc+pstc", "on_ofttc", "ca_federal_pstc", "conditional",
     "No primary text states the OFTTC-with-PSTC combination (Ontario Creates OFTTC page and the PSTC guidelines are silent); the CPTC-exclusion route is an inference: unresolved."),
)

def _rule_id(key: str) -> str:
    return str(uuid.uuid5(_NS, f"rule:{key}"))

def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc).isoformat()
    for key, slug_a, slug_b, rule_type, text in ROWS:
        conn.execute(sa.text("""
            INSERT INTO legal_stacking_rules (id, program_a_id, program_b_id, rule_type, condition_text, statutory_reference, confidence_tier, notes, created_at, updated_at)
            SELECT :id, (SELECT id FROM incentive_programs WHERE slug = :a LIMIT 1), (SELECT id FROM incentive_programs WHERE slug = :b LIMIT 1),
                   :rt, :cond, 'ITA 125.5(1); CRA RC4385 and RC4164', 'PARSED',
                   'NA-RECONCILIATION-12: previously unruled NA pair.', :now, :now
            WHERE NOT EXISTS (SELECT 1 FROM legal_stacking_rules WHERE id = :id ::uuid)
              AND (SELECT id FROM incentive_programs WHERE slug = :a LIMIT 1) IS NOT NULL
              AND (SELECT id FROM incentive_programs WHERE slug = :b LIMIT 1) IS NOT NULL
        """), {"id": _rule_id(key), "a": slug_a, "b": slug_b, "rt": rule_type, "cond": text, "now": now})

def downgrade() -> None:
    conn = op.get_bind()
    for key, *_ in ROWS:
        conn.execute(sa.text("DELETE FROM legal_stacking_rules WHERE id = :id"), {"id": _rule_id(key)})
