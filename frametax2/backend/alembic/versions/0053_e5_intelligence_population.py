"""0053 — Phase E5: Intelligence population — treaty requirements, stacking rules,
fund economics classification.

Populates:
  - fund_economics.notes with recoupment/equity classification for key programs
  - fund_economics rows for German regional funds (DE-BB, DE-BW, DE-HH, DE-MDM)
    that may have been missed if program_name_fragment matching in 0051 failed
  - Additional stacking rules for Canadian provincial + federal combinations
  - Additional stacking rules for Australian state + federal combinations
  - Additional stacking rules for Italian/Spanish regional + national combinations

Revision ID: 0053
Revises: 0052
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0053"
down_revision: Union[str, None] = "0052"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# fund_economics completions: economics classification notes
# ---------------------------------------------------------------------------

_FUND_ECON_NOTES: list[tuple[str, dict]] = [
    # (program_name_fragment, updates dict)
    ("canada media fund", {
        "notes": (
            "CMF equity investment: pari-passu recoupment from gross receipts. "
            "Government assistance under ITA §125.4 — reduces CPTC/OFTTC qualified labour."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 2_750_000,
        "stackable_with_incentives": True,
    }),
    ("telefilm canada", {
        "notes": (
            "Telefilm equity: first-position recoupment from gross receipts. "
            "Government assistance under ITA §125.4 — reduces CPTC qualified labour."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 550_000,
        "stackable_with_incentives": True,
    }),
    ("screen australia", {
        "notes": (
            "Screen Australia equity: pari-passu recoupment from gross receipts. "
            "Government financial assistance under ITAA97 §376-170 — reduces QAPE for offsets."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 2_750_000,
        "stackable_with_incentives": True,
    }),
    ("bfi film fund", {
        "notes": (
            "BFI equity: pari-passu recoupment. NOT government assistance for AVEC — "
            "treated as co-financing. AVEC qualifying spend not reduced."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 1_100_000,
        "stackable_with_incentives": True,
    }),
    ("eurimages", {
        "notes": (
            "Eurimages: non-repayable up to recoupment point; corridor participation in net profits. "
            "NOT government assistance for any national incentive — qualifying spend not reduced."
        ),
        "is_repayable": False,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_650_000,
        "stackable_with_incentives": True,
    }),
    ("northern ontario heritage", {
        "notes": (
            "NOHFC discretionary grant. Government assistance under ITA §125.4 and Ontario CTA — "
            "reduces CPTC and OFTTC qualified labour expenditure."
        ),
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 500_000,
        "stackable_with_incentives": True,
    }),
    ("creative scotland", {
        "notes": (
            "Creative Scotland equity: pari-passu recoupment. "
            "NOT government assistance for AVEC (co-financing arrangement per HMRC BIM65500)."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 550_000,
        "stackable_with_incentives": True,
    }),
    ("creative wales", {
        "notes": (
            "Creative Wales equity: pari-passu recoupment. "
            "NOT government assistance for AVEC."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 550_000,
        "stackable_with_incentives": True,
    }),
    ("northern ireland screen", {
        "notes": (
            "Northern Ireland Screen equity: pari-passu recoupment. "
            "NOT government assistance for AVEC."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 1_100_000,
        "stackable_with_incentives": True,
    }),
    ("screen yorkshire", {
        "notes": (
            "Screen Yorkshire equity: recoupable, pari-passu. "
            "NOT government assistance for AVEC."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 550_000,
        "stackable_with_incentives": True,
    }),
    ("screenwest", {
        "notes": (
            "Screenwest WA: government financial assistance under ITAA97 §376-170 — "
            "reduces qualifying Australian production expenditure (QAPE) for Location and Producer Offsets."
        ),
        "is_repayable": False,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_100_000,
        "stackable_with_incentives": True,
    }),
    ("wallimage", {
        "notes": (
            "Wallimage: repayable advance, subordinated recoupment from gross receipts. "
            "NOT government assistance for Belgian tax shelter calculation."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 550_000,
        "stackable_with_incentives": True,
    }),
    ("vaf flanders", {
        "notes": (
            "VAF: repayable advance, subordinated recoupment. "
            "NOT government assistance for Belgian tax shelter."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 825_000,
        "stackable_with_incentives": True,
    }),
    ("avances sur recettes", {
        "notes": (
            "CNC Avances sur Recettes: repayable from first gross receipts. "
            "Government support — interactions with tax crédit cinéma may apply."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_100_000,
        "stackable_with_incentives": True,
    }),
    ("filmfernsehfonds", {
        "notes": (
            "FFF Bayern: repayable loan, subordinated recoupment. "
            "NOT government assistance for DFFF calculation. Stackable with DFFF."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 1_650_000,
        "stackable_with_incentives": True,
    }),
    ("medienstiftung nrw", {
        "notes": (
            "Filmstiftung NRW: repayable loan, subordinated recoupment. Stackable with DFFF."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": False,
        "typical_max_award_usd": 2_200_000,
        "stackable_with_incentives": True,
    }),
    ("danish film institute", {
        "notes": (
            "DFI: equity investment recouped pari-passu from gross receipts. "
            "Government assistance in Denmark — reduces qualifying spend for Danish incentives."
        ),
        "is_repayable": True,
        "is_recoupable": True,
        "has_equity_participation": True,
        "typical_max_award_usd": 1_650_000,
        "stackable_with_incentives": True,
    }),
    ("south australian film corporation", {
        "notes": (
            "SAFC: government financial assistance reducing QAPE for Location and Producer Offsets."
        ),
        "is_repayable": False,
        "is_recoupable": False,
        "has_equity_participation": False,
        "typical_max_award_usd": 825_000,
        "stackable_with_incentives": True,
    }),
]


# ---------------------------------------------------------------------------
# Additional stacking rules for E3 completeness
# ---------------------------------------------------------------------------

_STACKING_RULES: list[tuple[str, str, str, str]] = [
    # Canada federal + provincial supplementals
    ("canada media fund", "ontario film and television", "spend_reduction",
     "CMF is government assistance under Ontario CTA; reduces OFTTC qualifying labour."),
    ("canada media fund", "film and television production tax credit",
     "spend_reduction",
     "CMF is government assistance under QC CTA; reduces SODEC credit qualifying labour."),
    ("telefilm canada", "ontario film and television", "spend_reduction",
     "Telefilm equity is government assistance; reduces OFTTC qualifying labour."),
    ("telefilm canada", "film and television production tax credit", "spend_reduction",
     "Telefilm equity is government assistance; reduces QC SODEC credit qualifying labour."),
    ("bell fund", "canada production tax credit", "spend_reduction",
     "Bell Fund grants are government assistance under ITA §125.4; reduces CPTC qualified labour."),
    # Australia supplementals
    ("south australian film corporation", "producer offset", "spend_reduction",
     "SAFC financial assistance is government assistance reducing QAPE for Producer Offset."),
    ("south australian film corporation", "location offset", "spend_reduction",
     "SAFC financial assistance is government assistance reducing QAPE for Location Offset."),
    # Italian regional + MiC national supplementals
    ("lazio cinema international", "italian tax credit", "allowed",
     "Lazio regional fund and MiC national tax credit operate on independent tracks."),
    ("sicilia film commission", "italian tax credit", "allowed",
     "Sicilia Film Commission and MiC national credit operate on independent tracks."),
    ("film commission campania", "italian tax credit", "allowed",
     "Campania Film Commission and MiC national credit operate on independent tracks."),
    ("film commission toscana", "italian tax credit", "allowed",
     "Tuscany Film Commission and MiC national credit operate on independent tracks."),
    # Spanish regional + national supplementals
    ("icec", "audiovisual production incentive", "allowed",
     "Catalonia ICEC and ICAA national deduction operate on independent tracks."),
    ("andalucia film commission", "audiovisual production incentive", "allowed",
     "Andalusia Film Commission and ICAA national deduction operate on independent tracks."),
    ("agadic", "audiovisual production incentive", "allowed",
     "Galicia AGADIC and ICAA national deduction operate on independent tracks."),
    ("institut valencià de cultura", "audiovisual production incentive", "allowed",
     "Valencia IVC and ICAA national deduction operate on independent tracks."),
    # Eurimages + national supplementals
    ("eurimages", "tax credit cinéma", "allowed",
     "Eurimages support does not reduce French tax crédit cinéma qualifying spend."),
    ("eurimages", "greece cash rebate", "allowed",
     "Eurimages support does not reduce Greek cash rebate qualifying spend."),
    ("eurimages", "norwegian film institute", "allowed",
     "Eurimages support does not reduce NFI qualifying spend."),
    ("eurimages", "finnish film foundation", "allowed",
     "Eurimages support does not reduce Finnish Film Foundation qualifying spend."),
    # BFI + devolved supplementals
    ("bfi film fund", "creative scotland", "allowed",
     "BFI and Creative Scotland both provide equity co-financing on independent terms."),
    ("bfi film fund", "northern ireland screen", "allowed",
     "BFI and Northern Ireland Screen both provide equity co-financing."),
    ("bfi film fund", "screen yorkshire", "allowed",
     "BFI Film Fund and Screen Yorkshire both provide equity co-financing."),
]


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Update fund_economics notes + classifications
    for frag, updates in _FUND_ECON_NOTES:
        prog_row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs WHERE LOWER(program_name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{frag.lower()}%"},
        ).fetchone()
        if not prog_row:
            continue
        prog_id = prog_row[0]

        # Ensure fund_economics row exists (may not exist for all programs)
        existing = conn.execute(
            sa.text("SELECT 1 FROM fund_economics WHERE program_id = :pid"),
            {"pid": prog_id},
        ).fetchone()

        if existing:
            set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
            conn.execute(
                sa.text(f"UPDATE fund_economics SET {set_clauses} WHERE program_id = :program_id"),
                {"program_id": prog_id, **updates},
            )
        else:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO fund_economics (
                        program_id,
                        is_repayable, is_recoupable, has_equity_participation,
                        typical_max_award_usd, stackable_with_incentives, notes
                    ) VALUES (
                        :program_id,
                        :is_repayable, :is_recoupable, :has_equity_participation,
                        :typical_max_award_usd, :stackable_with_incentives, :notes
                    )
                    ON CONFLICT (program_id) DO UPDATE SET notes = EXCLUDED.notes
                    """
                ),
                {
                    "program_id": prog_id,
                    "is_repayable": updates.get("is_repayable", False),
                    "is_recoupable": updates.get("is_recoupable", False),
                    "has_equity_participation": updates.get("has_equity_participation", False),
                    "typical_max_award_usd": updates.get("typical_max_award_usd"),
                    "stackable_with_incentives": updates.get("stackable_with_incentives", True),
                    "notes": updates.get("notes"),
                },
            )

    # 2. Insert additional stacking rules
    def find_pid(fragment: str) -> object | None:
        row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs WHERE LOWER(program_name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{fragment.lower()}%"},
        ).fetchone()
        return row[0] if row else None

    for frag_a, frag_b, rule_type, condition_text in _STACKING_RULES:
        pid_a = find_pid(frag_a)
        pid_b = find_pid(frag_b)
        if pid_a is None or pid_b is None:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO legal_stacking_rules
                    (program_a_id, program_b_id, rule_type, condition_text, confidence_tier)
                VALUES
                    (:a, :b, :rule_type, :condition_text, 'PARSED')
                ON CONFLICT DO NOTHING
                """
            ),
            {"a": pid_a, "b": pid_b, "rule_type": rule_type, "condition_text": condition_text},
        )


def downgrade() -> None:
    conn = op.get_bind()

    def find_pid(fragment: str) -> object | None:
        row = conn.execute(
            sa.text(
                "SELECT id FROM incentive_programs WHERE LOWER(program_name) LIKE :frag LIMIT 1"
            ),
            {"frag": f"%{fragment.lower()}%"},
        ).fetchone()
        return row[0] if row else None

    for frag_a, frag_b, _rt, _ct in _STACKING_RULES:
        pid_a = find_pid(frag_a)
        pid_b = find_pid(frag_b)
        if pid_a is None or pid_b is None:
            continue
        conn.execute(
            sa.text(
                "DELETE FROM legal_stacking_rules "
                "WHERE (program_a_id = :a AND program_b_id = :b) "
                "   OR (program_a_id = :b AND program_b_id = :a)"
            ),
            {"a": pid_a, "b": pid_b},
        )
