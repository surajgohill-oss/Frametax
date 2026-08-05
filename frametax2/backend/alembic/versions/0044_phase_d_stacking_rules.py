"""0044 — Phase D stacking rules: fund/credit interactions.

Seeds LegalStackingRule entries for major fund-vs-incentive interactions
identified in Phase D intelligence gathering.

Rules added:
  fr_cnc_production  + fr_trip          → allowed
  gb_bfi_production  + uk_avec          → allowed
  eu_eurimages       + uk_avec          → allowed
  eu_eurimages       + ie_section_481   → allowed
  au_screen_production + au_location_offset → spend_reduction
  ca_cmf             + ca_federal_cptc  → spend_reduction (conditional)

Revision ID: 0044
Revises: 0043
"""
from __future__ import annotations

import uuid
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0044"
down_revision: Union[str, None] = "0043"
branch_labels = None
depends_on = None


def _uid(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"frametax.stacking.phased.{key}")


_RULES = [
    {
        "id": _uid("fr_cnc_fr_trip"),
        "slug_a": "fr_cnc_production",
        "slug_b": "fr_trip",
        "rule_type": "allowed",
        "condition_text": (
            "CNC avance sur recettes (domestic support) and TRIP (rebate for international "
            "productions) operate under different eligibility tracks. A production claiming "
            "TRIP is typically a foreign-majority production and would not also claim CNC avance, "
            "but co-productions may access both under treaty arrangements."
        ),
        "statutory_reference": "CNC TRIP Decree No. 2009-1271; CNC Avances sur Recettes statutory basis",
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: CNC avance and TRIP are legally separate instruments with distinct eligibility criteria.",
    },
    {
        "id": _uid("gb_bfi_uk_avec"),
        "slug_a": "gb_bfi_production",
        "slug_b": "uk_avec",
        "rule_type": "allowed",
        "condition_text": (
            "BFI Film Fund equity investment does not reduce UK qualifying expenditure (QE) "
            "for AVEC purposes. BFI investment is treated as co-financing, not government "
            "assistance reducing the AVEC credit base."
        ),
        "statutory_reference": "UK Finance Act 2022 s.1179A (AVEC); BFI Film Fund guidelines",
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: BFI equity and AVEC are compatible; no spend-reduction interaction identified.",
    },
    {
        "id": _uid("eu_eurimages_uk_avec"),
        "slug_a": "eu_eurimages",
        "slug_b": "uk_avec",
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support is allocated to individual co-producers in their respective territories. "
            "The UK co-producer's share of Eurimages does not reduce UK qualifying expenditure "
            "for AVEC, as Eurimages is not classified as UK government assistance."
        ),
        "statutory_reference": "UK Finance Act 2022 s.1179A (AVEC); Eurimages Convention",
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: Eurimages and UK AVEC have been used together in major UK-European co-productions.",
    },
    {
        "id": _uid("eu_eurimages_ie_section_481"),
        "slug_a": "eu_eurimages",
        "slug_b": "ie_section_481",
        "rule_type": "allowed",
        "condition_text": (
            "Eurimages support allocated to Irish co-producers does not reduce Irish-qualifying "
            "expenditure for Section 481 purposes. Section 481 relief applies to Irish expenditure "
            "in the co-production; Eurimages co-production support is separate financing."
        ),
        "statutory_reference": "Irish TCA 1997 s.481; Eurimages Convention; Revenue guidance",
        "confidence_tier": "DISCOVERY",
        "notes": "allowed: Irish-European co-productions regularly access both Eurimages and Section 481.",
    },
    {
        "id": _uid("au_screen_au_location"),
        "slug_a": "au_screen_production",
        "slug_b": "au_location_offset",
        "rule_type": "spend_reduction",
        "condition_text": (
            "Screen Australia equity investment is government financial assistance. "
            "Under the Australian Location Offset rules, government financial assistance received "
            "in respect of a production reduces qualifying Australian production expenditure (QAPE) "
            "by the amount of the assistance before computing the offset percentage."
        ),
        "statutory_reference": (
            "Income Tax Assessment Act 1997 s.376-170 (Location Offset); "
            "Screen Australia government assistance reduction rules"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "spend_reduction: Screen Australia equity reduces QAPE basis for Location Offset calculation.",
    },
    {
        "id": _uid("ca_cmf_ca_cptc"),
        "slug_a": "ca_cmf",
        "slug_b": "ca_federal_cptc",
        "rule_type": "spend_reduction",
        "condition_text": (
            "CMF grants and contributions are government assistance under the Income Tax Act. "
            "Pursuant to ITA §125.4(1) and CRA T4283, government assistance received or receivable "
            "must be deducted from Qualified Labour Expenditure (QLE) before computing the "
            "Canadian Production Tax Credit (CPTC). Amount of CMF contribution reduces CPTC base."
        ),
        "statutory_reference": (
            "Income Tax Act §125.4(1) definition of 'qualified labour expenditure'; "
            "CRA T4283 Guide: Canadian Film or Video Production Tax Credit"
        ),
        "confidence_tier": "DISCOVERY",
        "notes": "spend_reduction: CMF is government assistance that reduces CPTC qualifying labour base.",
    },
]


def upgrade() -> None:
    conn = op.get_bind()

    for rule in _RULES:
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
                     condition_text, statutory_reference, confidence_tier, notes,
                     created_at, updated_at)
                VALUES
                    (:id, :a, :b, :rule_type,
                     :condition_text, :statutory_reference, :confidence_tier, :notes,
                     now(), now())
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
