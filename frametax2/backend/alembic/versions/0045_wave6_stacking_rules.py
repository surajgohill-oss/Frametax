"""0045 — Wave-6 stacking rules: Canadian provincial + Eurimages + Screenwest.

Adds new LegalStackingRule entries for:
  CA-BC PSTC  + CPTC            → allowed (additive tax credits)
  CA-ON OPSTC + CPTC            → allowed (additive tax credits)
  CA-QC QPRDP + CPTC            → allowed (additive tax credits)
  CA-BC PSTC  + CMF             → spend_reduction
  CA-ON OPSTC + CMF             → spend_reduction
  NOHFC       + CA-ON OPSTC     → spend_reduction
  Eurimages   + IT tax credit   → allowed
  Eurimages   + MT rebate       → allowed
  Eurimages   + HR rebate       → allowed
  Screenwest  + AU Location Offset → spend_reduction
  Screenwest  + Screen Australia   → spend_reduction

Revision ID: 0045
Revises: 0044
"""
from __future__ import annotations

import uuid
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0045"
down_revision: Union[str, None] = "0044"
branch_labels = None
depends_on = None


def _uid(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"frametax.stacking.wave6.{key}")


_RULES = [
    {
        "id": _uid("ca_bc_pstc_cptc"),
        "slug_a": "ca_bc_pstc",
        "slug_b": "ca_federal_cptc",
        "rule_type": "allowed",
        "condition_text": (
            "BC PSTC and federal CPTC are independent tax credits both applied to qualifying "
            "labour expenditure. They are additive — PSTC does not constitute government assistance "
            "under ITA §125.4 and does not reduce CPTC qualified labour expenditure."
        ),
        "statutory_reference": (
            "ITA §125.4 (CPTC); BC Income Tax Act — Production Services Tax Credit regulations"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: BC PSTC and CPTC are additive; Vancouver productions routinely combine both.",
    },
    {
        "id": _uid("ca_on_opstc_cptc"),
        "slug_a": "ca_on_opstc",
        "slug_b": "ca_federal_cptc",
        "rule_type": "allowed",
        "condition_text": (
            "Ontario OPSTC and federal CPTC are independent refundable tax credits both applied to "
            "qualifying Ontario labour. Additive, not mutually exclusive. "
            "OPSTC is a provincial tax credit and does not constitute government assistance under ITA §125.4."
        ),
        "statutory_reference": (
            "ITA §125.4 (CPTC); Ontario Taxation Act — Production Services Tax Credit"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: Toronto productions routinely combine Ontario OPSTC with CPTC.",
    },
    {
        "id": _uid("ca_qc_qprdp_cptc"),
        "slug_a": "ca_qc_qprdp",
        "slug_b": "ca_federal_cptc",
        "rule_type": "allowed",
        "condition_text": (
            "Quebec QPRDP and federal CPTC are independent refundable tax credits. "
            "QPRDP is a provincial tax credit issued by Revenu Québec on certification by SODEC; "
            "it does not reduce CPTC qualified labour under ITA §125.4."
        ),
        "statutory_reference": (
            "ITA §125.4 (CPTC); Quebec Taxation Act — Production Tax Credit for Foreign Productions"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: Montreal VFX/animation productions combine QPRDP (up to 28% for animation) with CPTC.",
    },
    {
        "id": _uid("ca_cmf_bc_pstc"),
        "slug_a": "ca_cmf",
        "slug_b": "ca_bc_pstc",
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under provincial income tax statutes. "
            "The amount of CMF assistance reduces qualifying BC labour expenditure before "
            "computing the PSTC credit percentage."
        ),
        "statutory_reference": (
            "BC Income Tax Act — PSTC qualified labour definition; "
            "CRA T4283 government assistance reduction principles"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "spend_reduction: CMF assistance reduces PSTC qualifying basis analogous to CPTC reduction.",
    },
    {
        "id": _uid("ca_cmf_on_opstc"),
        "slug_a": "ca_cmf",
        "slug_b": "ca_on_opstc",
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF contributions are government assistance under the Ontario Taxation Act. "
            "The CMF amount reduces qualifying Ontario labour expenditure before computing OPSTC."
        ),
        "statutory_reference": (
            "Ontario Taxation Act — OPSTC qualified labour expenditure definition; "
            "CRA government assistance principles"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "spend_reduction: CMF reduces OPSTC qualifying basis (analogous to CPTC reduction).",
    },
    {
        "id": _uid("nohfc_ca_on_opstc"),
        "slug_a": "nohfc_production_fund",
        "slug_b": "ca_on_opstc",
        "rule_type": "spend_reduction",
        "condition_text": (
            "NOHFC grants are government assistance under the Ontario Taxation Act. "
            "The NOHFC amount reduces qualifying Ontario labour expenditure for OPSTC "
            "(consistent with OMDC guidelines for OFTTC interaction)."
        ),
        "statutory_reference": (
            "Ontario Taxation Act — OPSTC qualifying labour; OMDC NOHFC Guidelines"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "spend_reduction: NOHFC reduces OPSTC basis (parallel to OFTTC interaction already documented).",
    },
    {
        "id": _uid("eu_eurimages_it_taxcredit"),
        "slug_a": "eu_eurimages",
        "slug_b": "it_tax_credit_foreign",
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Italian co-producers does not reduce "
            "Italian qualifying expenditure for the MiC tax credit for foreign productions (Decreto MiC). "
            "Eurimages is Council of Europe support, not Italian government financial assistance."
        ),
        "statutory_reference": (
            "Italian tax credit Decreto MiC (art. 15 D.Lgs 60/2024); Eurimages Convention"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: Italian-European co-productions accessing Eurimages plus the Italian 40% tax credit.",
    },
    {
        "id": _uid("eu_eurimages_mt_rebate"),
        "slug_a": "eu_eurimages",
        "slug_b": "mt_mfc_rebate",
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Maltese co-producers does not reduce "
            "qualifying expenditure for Malta Film Commission cash rebate purposes. "
            "Eurimages is not Maltese government assistance."
        ),
        "statutory_reference": (
            "MFC Cash Rebate Programme Guidelines; Eurimages Convention"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: Malta is an Eurimages member; co-productions can access both.",
    },
    {
        "id": _uid("eu_eurimages_hr_rebate"),
        "slug_a": "eu_eurimages",
        "slug_b": "hr_cash_rebate",
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Croatian co-producers does not reduce "
            "Croatian qualifying expenditure for HAVC cash rebate purposes. "
            "Eurimages is Council of Europe support, not Croatian government assistance."
        ),
        "statutory_reference": (
            "HAVC Croatia Cash Rebate Programme Guidelines; Eurimages Convention"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: Croatia is an Eurimages member; co-productions can access both.",
    },
    {
        "id": _uid("au_screenwest_au_location"),
        "slug_a": "au_screenwest",
        "slug_b": "au_location_offset",
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screenwest WA financial assistance is government financial assistance. "
            "Under the Australian Location Offset rules, government financial assistance in respect of "
            "a production reduces qualifying Australian production expenditure (QAPE) before computing "
            "the offset percentage."
        ),
        "statutory_reference": (
            "Income Tax Assessment Act 1997 s.376-170 (Location Offset); Screenwest PAS Guidelines"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "spend_reduction: Screenwest WA assistance reduces QAPE for Location Offset.",
    },
    {
        "id": _uid("au_screenwest_au_screen"),
        "slug_a": "au_screenwest",
        "slug_b": "au_screen_production",
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screenwest WA financial assistance reduces qualifying expenditure for "
            "Screen Australia grant eligibility and matching calculations."
        ),
        "statutory_reference": (
            "Screen Australia Agency Act 2008; Screenwest PAS Guidelines"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "spend_reduction: Screenwest reduces Screen Australia qualifying spend in combined applications.",
    },
]


def upgrade() -> None:
    conn = op.get_bind()

    for rule in _RULES:
        rule = dict(rule)
        slug_a = rule.pop("slug_a")
        slug_b = rule.pop("slug_b")

        row_a = conn.execute(
            sa.text("SELECT id FROM incentive_programs WHERE slug = :slug"),
            {"slug": slug_a},
        ).fetchone()
        row_b = conn.execute(
            sa.text("SELECT id FROM incentive_programs WHERE slug = :slug"),
            {"slug": slug_b},
        ).fetchone()

        if row_a is None or row_b is None:
            continue  # prerequisite not yet seeded; skip gracefully

        conn.execute(
            sa.text("""
                INSERT INTO legal_stacking_rules
                    (id, program_a_id, program_b_id, rule_type,
                     condition_text, statutory_reference, confidence_tier, notes)
                VALUES
                    (:id, :a, :b, :rule_type,
                     :condition_text, :statutory_reference, :confidence_tier, :notes)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                **rule,
                "a": row_a[0],
                "b": row_b[0],
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for rule in _RULES:
        conn.execute(
            sa.text("DELETE FROM legal_stacking_rules WHERE id = :id"),
            {"id": rule["id"]},
        )
