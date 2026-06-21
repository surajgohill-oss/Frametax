"""0022 — LegalStackingRules expansion.

Adds source-backed stacking rules beyond the two NOHFC rules in 0007.

New rules:
  1. CPTC + OFTTC: spend_reduction — OFTTC is government assistance; reduces CPTC QCLE.
  2. CPTC + OPSTC: mutually_exclusive — domestic content vs foreign service production types.
  3. OFTTC + OPSTC: mutually_exclusive — domestic content vs foreign service production types.
  4. NOHFC + OPSTC: spend_reduction — same government assistance principle as NOHFC+CPTC/OFTTC.
  5. CPTC + BC PSTC: mutually_exclusive — domestic vs foreign service production types.
  6. CPTC + QC (domestic): spend_reduction — QC credit as government assistance reduces CPTC base.
  7. UK AVEC + IE S481: allowed — different territory spend; commonly stacked for UK/Ireland co-productions.

Sources:
  ITA § 125.4(1)(b) — government assistance definition for CPTC
  CRA T4283 Guide — QCLE calculation instructions
  Ontario Creates OFTTC guidelines — mutual exclusivity with OPSTC
  Creative BC PSTC guidelines — mutual exclusivity with CPTC
  HMRC Brief / Revenue Ireland joint guidance — AVEC + S481 stacking

Revision ID: 0022
Revises: 0021
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()
_NS = uuid.UUID("a1000000-0022-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


# Rule IDs (deterministic)
_RULE_IDS = {
    "cptc_ofttc_reduction":   _uid("rule:cptc+ofttc:spend_reduction"),
    "cptc_opstc_exclusive":   _uid("rule:cptc+opstc:mutually_exclusive"),
    "ofttc_opstc_exclusive":  _uid("rule:ofttc+opstc:mutually_exclusive"),
    "nohfc_opstc_reduction":  _uid("rule:nohfc+opstc:spend_reduction"),
    "cptc_bcpstc_exclusive":  _uid("rule:cptc+bc_pstc:mutually_exclusive"),
    "cptc_qc_reduction":      _uid("rule:cptc+qc_film:spend_reduction"),
    "uk_avec_ie_s481_allowed": _uid("rule:uk_avec+ie_s481:allowed"),
}

# Stacking rule definitions
# (rule_key, slug_a, slug_b, rule_type, condition_text, statutory_reference, confidence_tier, notes)
_STACKING_RULES = [
    (
        "cptc_ofttc_reduction",
        "ca_federal_cptc",
        "on_ofttc",
        "spend_reduction",
        "OFTTC tax credit is 'government assistance' under ITA § 125.4(1)(b) and must be "
        "deducted from Qualified Canadian Labour Expenditure (QCLE) before computing CPTC. "
        "Net QCLE = gross QCLE minus OFTTC amount received or receivable.",
        "Income Tax Act § 125.4(1)(b) — definition of 'government assistance'; "
        "CRA T4283 Guide — QCLE calculation, line 115",
        "PARSED",
        "spend_reduction: OFTTC received/receivable reduces CPTC qualifying labour base. "
        "CPTC and OFTTC are commonly stacked on Ontario Canadian content productions — "
        "this is the most important Canadian stacking interaction.",
    ),
    (
        "cptc_opstc_exclusive",
        "ca_federal_cptc",
        "on_opstc",
        "mutually_exclusive",
        "CPTC applies only to 'Canadian film or video productions' (domestic Canadian content). "
        "OPSTC applies only to 'accredited film or video productions' (foreign service productions). "
        "A production cannot simultaneously qualify for both CPTC and OPSTC — "
        "the production type is mutually exclusive.",
        "Income Tax Act § 125.4 (CPTC — Canadian productions); "
        "Income Tax Act § 125.5 (PSTC — foreign service productions)",
        "PARSED",
        "mutually_exclusive: CPTC (domestic content) and OPSTC (foreign service) cannot be "
        "claimed for the same production. Production must elect one track.",
    ),
    (
        "ofttc_opstc_exclusive",
        "on_ofttc",
        "on_opstc",
        "mutually_exclusive",
        "OFTTC applies to Ontario domestic Canadian content productions. "
        "OPSTC applies to foreign service productions using Ontario. "
        "A production cannot be both a domestic content production (OFTTC) and a foreign "
        "service production (OPSTC) simultaneously.",
        "Ontario Creates OFTTC guidelines; Ontario Creates OPSTC guidelines — "
        "production type definitions are mutually exclusive",
        "PARSED",
        "mutually_exclusive: OFTTC (Ontario domestic content) and OPSTC (Ontario foreign service) "
        "cannot be claimed for the same production. Production type determines eligibility.",
    ),
    (
        "nohfc_opstc_reduction",
        "nohfc_production_fund",
        "on_opstc",
        "spend_reduction",
        "NOHFC grant (government assistance) must be deducted from Ontario eligible production "
        "service expenditure base before computing OPSTC credit. "
        "Net Ontario qualifying spend = gross OEPE minus NOHFC grant received or receivable.",
        "Ontario Reg 37/09 under Corporations Tax Act; "
        "Ontario Creates OPSTC guidelines — government assistance deduction",
        "PARSED",
        "spend_reduction: NOHFC grant reduces OPSTC qualifying expenditure base. "
        "Same government assistance principle as NOHFC+OFTTC (already in 0007) and NOHFC+CPTC.",
    ),
    (
        "cptc_bcpstc_exclusive",
        "ca_federal_cptc",
        "bc_pstc",
        "mutually_exclusive",
        "CPTC applies to Canadian domestic content productions. "
        "BC PSTC applies to accredited foreign service productions. "
        "Production type is mutually exclusive — cannot claim both for the same production.",
        "Income Tax Act § 125.4 (CPTC); "
        "BC Film Incentive Act — PSTC eligibility (accredited foreign production)",
        "PARSED",
        "mutually_exclusive: CPTC (federal domestic content) and BC PSTC (BC foreign service) "
        "cannot be claimed for the same production.",
    ),
    (
        "cptc_qc_reduction",
        "ca_federal_cptc",
        "qc_film_production",
        "spend_reduction",
        "Quebec film production credit is 'government assistance' under ITA § 125.4(1)(b). "
        "QC credit amount must be deducted from QCLE before computing CPTC. "
        "This applies to Quebec domestic content productions that claim both QC and CPTC.",
        "Income Tax Act § 125.4(1)(b) — 'government assistance' definition; "
        "CRA T4283 Guide — QCLE deductions for provincial assistance",
        "PARSED",
        "spend_reduction: QC film production credit reduces CPTC qualifying labour base for "
        "productions claiming both federal CPTC and Quebec provincial credit.",
    ),
    (
        "uk_avec_ie_s481_allowed",
        "uk_avec",
        "ie_section_481",
        "allowed",
        "UK AVEC and IE Section 481 can both be claimed for the same production when "
        "qualifying expenditure is incurred in both the UK and Ireland. "
        "Each credit applies only to its own territory's qualifying spend — no double-counting. "
        "UK/Ireland co-productions and productions shooting in both territories commonly stack.",
        "HMRC Corporation Tax Creative Industries guidance (AVEC); "
        "Revenue Commissioners Ireland S481 guidance — "
        "both programmes explicitly permit multi-territory productions",
        "PARSED",
        "allowed: UK AVEC and IE S481 are stackable for the same production provided "
        "UK expenditure is claimed under AVEC and Irish expenditure under S481. "
        "UK/Ireland co-productions are a common use case for this combination.",
    ),
]


def upgrade() -> None:
    conn = op.get_bind()

    for (rule_key, slug_a, slug_b, rule_type,
         condition_text, statutory_ref, tier, notes) in _STACKING_RULES:
        rule_id = _RULE_IDS[rule_key]
        conn.execute(
            sa.text("""
                INSERT INTO legal_stacking_rules (
                    id, program_a_id, program_b_id, rule_type,
                    condition_text, statutory_reference,
                    confidence_tier, notes
                )
                SELECT
                    :id,
                    (SELECT id FROM incentive_programs WHERE slug = :slug_a LIMIT 1),
                    (SELECT id FROM incentive_programs WHERE slug = :slug_b LIMIT 1),
                    :rule_type, :cond, :stat, :tier, :notes
                WHERE NOT EXISTS (
                    SELECT 1 FROM legal_stacking_rules WHERE id = :id
                )
                  AND (SELECT id FROM incentive_programs WHERE slug = :slug_a LIMIT 1) IS NOT NULL
                  AND (SELECT id FROM incentive_programs WHERE slug = :slug_b LIMIT 1) IS NOT NULL
            """),
            {
                "id": rule_id, "slug_a": slug_a, "slug_b": slug_b,
                "rule_type": rule_type, "cond": condition_text,
                "stat": statutory_ref, "tier": tier, "notes": notes,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for rule_key, *_ in _STACKING_RULES:
        conn.execute(
            sa.text("DELETE FROM legal_stacking_rules WHERE id = :id"),
            {"id": _RULE_IDS[rule_key]},
        )
