"""0012 — Add Australia and New Zealand; seed global local cost benchmarks.

New jurisdictions:
  AU — Australia (Location Offset + PDV Offset, DISCOVERY)
  NZ — New Zealand (NZSPG International, DISCOVERY)

Local cost benchmarks:
  All 17 target jurisdictions seeded (DISCOVERY tier, LA-relative multipliers).
  Benchmarks reference existing jurisdiction rows by code.

Revision ID: 0012
Revises: 0011
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Union
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels = None
depends_on = None

NOW = datetime.now(timezone.utc).isoformat()

# Stable namespace for 0012
_NS = uuid.UUID("a1000000-0012-0000-0001-000000000000")


def _uid(seed: str) -> str:
    return str(uuid.uuid5(_NS, seed))


AU_JUR_ID = _uid("jur:AU")
NZ_JUR_ID = _uid("jur:NZ")
AU_PROG_ID = _uid("prog:au_location_offset")
NZ_PROG_ID = _uid("prog:nz_spg_international")


# ---------------------------------------------------------------------------
# Benchmark data — multipliers relative to Los Angeles baseline (1.0)
# category_overrides_json carries marine_vessel, lodging, per_diem
# ---------------------------------------------------------------------------
_BENCHMARK_SOURCE = (
    "Production market knowledge — not verified from primary labour cost surveys "
    "(AICP, BECTU, regional film office surveys). "
    "Confidence tier: DISCOVERY. Promote to PARSED after reviewing primary sources."
)
_AS_OF = "2025-06"

BENCHMARKS = [
    # (jur_code, crew, equip, stage, loc, post, vfx, catering, travel, overrides_json)
    ("US", 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 350.0,
     {"marine_vessel_multiplier": 1.00, "lodging_daily_usd": 250.0, "per_diem_daily_usd": 100.0}),
    ("CA", 0.78, 0.75, 0.72, 0.65, 0.75, 0.72, 0.70, 280.0,
     {"marine_vessel_multiplier": 0.75, "lodging_daily_usd": 190.0, "per_diem_daily_usd": 85.0}),
    ("GB", 0.90, 0.85, 0.88, 0.95, 0.90, 0.85, 0.80, 380.0,
     {"marine_vessel_multiplier": 0.85, "lodging_daily_usd": 280.0, "per_diem_daily_usd": 110.0}),
    ("IE", 0.80, 0.78, 0.75, 0.70, 0.78, 0.75, 0.72, 350.0,
     {"marine_vessel_multiplier": 0.80, "lodging_daily_usd": 220.0, "per_diem_daily_usd": 95.0}),
    ("MT", 0.55, 0.60, 0.65, 0.45, 0.65, 0.65, 0.50, 280.0,
     {"marine_vessel_multiplier": 0.60, "lodging_daily_usd": 140.0, "per_diem_daily_usd": 70.0}),
    ("GR", 0.50, 0.55, 0.55, 0.40, 0.60, 0.60, 0.45, 270.0,
     {"marine_vessel_multiplier": 0.55, "lodging_daily_usd": 130.0, "per_diem_daily_usd": 65.0}),
    ("CY", 0.45, 0.50, 0.50, 0.38, 0.55, 0.55, 0.42, 260.0,
     {"marine_vessel_multiplier": 0.50, "lodging_daily_usd": 120.0, "per_diem_daily_usd": 60.0}),
    ("MU", 0.35, 0.55, None, 0.30, 0.60, 0.65, 0.38, 380.0,
     {"marine_vessel_multiplier": 0.50, "lodging_daily_usd": 110.0, "per_diem_daily_usd": 55.0}),
    ("FR", 0.85, 0.82, 0.85, 0.90, 0.85, 0.82, 0.80, 360.0,
     {"marine_vessel_multiplier": 0.82, "lodging_daily_usd": 240.0, "per_diem_daily_usd": 105.0}),
    ("ES", 0.65, 0.68, 0.65, 0.60, 0.70, 0.70, 0.62, 300.0,
     {"marine_vessel_multiplier": 0.65, "lodging_daily_usd": 170.0, "per_diem_daily_usd": 80.0}),
    ("IT", 0.70, 0.72, 0.70, 0.68, 0.72, 0.72, 0.65, 320.0,
     {"marine_vessel_multiplier": 0.70, "lodging_daily_usd": 185.0, "per_diem_daily_usd": 85.0}),
    ("HR", 0.45, 0.50, 0.45, 0.35, 0.55, 0.55, 0.42, 260.0,
     {"marine_vessel_multiplier": 0.48, "lodging_daily_usd": 120.0, "per_diem_daily_usd": 60.0}),
    ("HU", 0.45, 0.50, 0.55, 0.38, 0.55, 0.55, 0.42, 260.0,
     {"marine_vessel_multiplier": None, "lodging_daily_usd": 120.0, "per_diem_daily_usd": 60.0}),
    ("BE", 0.85, 0.82, 0.80, 0.80, 0.82, 0.80, 0.78, 360.0,
     {"marine_vessel_multiplier": 0.80, "lodging_daily_usd": 230.0, "per_diem_daily_usd": 100.0}),
    ("DE", 0.85, 0.82, 0.85, 0.80, 0.85, 0.82, 0.78, 360.0,
     {"marine_vessel_multiplier": 0.80, "lodging_daily_usd": 225.0, "per_diem_daily_usd": 100.0}),
    ("AU", 0.75, 0.72, 0.70, 0.65, 0.72, 0.70, 0.68, 480.0,
     {"marine_vessel_multiplier": 0.72, "lodging_daily_usd": 200.0, "per_diem_daily_usd": 90.0}),
    ("NZ", 0.65, 0.65, 0.60, 0.55, 0.65, 0.65, 0.60, 500.0,
     {"marine_vessel_multiplier": 0.65, "lodging_daily_usd": 170.0, "per_diem_daily_usd": 75.0}),
]


def upgrade() -> None:
    jur_tbl = sa.table(
        "jurisdictions",
        sa.column("id"), sa.column("parent_id"), sa.column("name"),
        sa.column("code"), sa.column("iso_code"), sa.column("level"),
        sa.column("currency_code"), sa.column("country_code"),
        sa.column("is_active"), sa.column("notes"), sa.column("metadata_json"),
        sa.column("created_at"), sa.column("updated_at"),
    )

    op.bulk_insert(jur_tbl, [
        {
            "id": AU_JUR_ID, "parent_id": None,
            "name": "Australia", "code": "AU", "iso_code": "AU",
            "level": "country", "currency_code": "AUD", "country_code": "AU",
            "is_active": True, "notes": None, "metadata_json": None,
            "created_at": NOW, "updated_at": NOW,
        },
        {
            "id": NZ_JUR_ID, "parent_id": None,
            "name": "New Zealand", "code": "NZ", "iso_code": "NZ",
            "level": "country", "currency_code": "NZD", "country_code": "NZ",
            "is_active": True, "notes": None, "metadata_json": None,
            "created_at": NOW, "updated_at": NOW,
        },
    ])

    prog_tbl = sa.table(
        "incentive_programs",
        sa.column("id"), sa.column("jurisdiction_id"), sa.column("source_document_id"),
        sa.column("name"), sa.column("slug"), sa.column("program_type"),
        sa.column("credit_basis"), sa.column("base_rate"), sa.column("max_rate"),
        sa.column("is_refundable"), sa.column("is_transferable"),
        sa.column("transferable_value_pct"), sa.column("is_competitive"),
        sa.column("annual_cap_local"), sa.column("fixed_grant_amount_usd"),
        sa.column("requires_cultural_test"), sa.column("cultural_test_id"),
        sa.column("requires_local_entity"), sa.column("effective_from"),
        sa.column("effective_until"), sa.column("confidence_tier"),
        sa.column("review_status"), sa.column("authority_url"),
        sa.column("last_verified_date"), sa.column("notes"),
        sa.column("created_at"), sa.column("updated_at"),
    )

    op.bulk_insert(prog_tbl, [
        {
            "id": AU_PROG_ID,
            "jurisdiction_id": AU_JUR_ID,
            "source_document_id": None,
            "name": "Australia Location Offset / PDV Offset",
            "slug": "au_location_offset",
            "program_type": "tax_credit",
            "credit_basis": "qualifying_spend",
            "base_rate": 0.165,
            "max_rate": 0.40,
            "is_refundable": True,
            "is_transferable": False,
            "transferable_value_pct": None,
            "is_competitive": False,
            "annual_cap_local": None,
            "fixed_grant_amount_usd": None,
            "requires_cultural_test": False,
            "cultural_test_id": None,
            "requires_local_entity": False,
            "effective_from": "2021-01-01",
            "effective_until": None,
            "confidence_tier": "DISCOVERY",
            "review_status": "pending",
            "authority_url": "https://www.screenaustralia.gov.au",
            "last_verified_date": None,
            "notes": (
                "Location Offset: 16.5% on QAPE (min A$20M QAPE). "
                "PDV Offset: 30% on qualifying post/VFX spend (min A$500K). "
                "State rebates can top-up: NSW (+10%), VIC (+13.5%). "
                "High minimum spend limits applicability for sub-$20M budgets. "
                "Data gaps: state top-up stacking rules, QAPE ATL inclusion, "
                "WHT on cast, AUD/USD risk, processing timeline."
            ),
            "created_at": NOW, "updated_at": NOW,
        },
        {
            "id": NZ_PROG_ID,
            "jurisdiction_id": NZ_JUR_ID,
            "source_document_id": None,
            "name": "New Zealand Screen Production Grant (International)",
            "slug": "nz_spg_international",
            "program_type": "cash_rebate",
            "credit_basis": "qualifying_spend",
            "base_rate": 0.20,
            "max_rate": 0.25,
            "is_refundable": True,
            "is_transferable": False,
            "transferable_value_pct": None,
            "is_competitive": False,
            "annual_cap_local": None,
            "fixed_grant_amount_usd": None,
            "requires_cultural_test": False,
            "cultural_test_id": None,
            "requires_local_entity": False,
            "effective_from": "2018-01-01",
            "effective_until": None,
            "confidence_tier": "DISCOVERY",
            "review_status": "pending",
            "authority_url": "https://www.nzfilm.co.nz/resources/nz-screen-production-grant",
            "last_verified_date": None,
            "notes": (
                "International: 20% on qualifying NZ expenditure (min NZ$16M QNZPE). "
                "Uplift: additional 5% for significant economic benefit. "
                "NZ has hosted major productions (LOTR, Avatar). "
                "Data gaps: uplift criteria, QNZPE ATL inclusion, NZD/USD cap equivalents, "
                "WHT on cast, processing timeline, annual programme cap."
            ),
            "created_at": NOW, "updated_at": NOW,
        },
    ])

    # ------------------------------------------------------------------
    # Seed local_cost_benchmarks for all 17 jurisdictions via subselects
    # ------------------------------------------------------------------
    import json

    for (code, crew, equip, stage, loc, post, vfx, catering, travel, overrides) in BENCHMARKS:
        op.execute(
            sa.text("""
                INSERT INTO local_cost_benchmarks (
                    id, jurisdiction_id,
                    crew_rate_multiplier, equipment_rental_multiplier,
                    stage_facility_multiplier, location_fees_multiplier,
                    post_production_multiplier, vfx_multiplier, catering_multiplier,
                    key_crew_daily_travel_usd, category_overrides_json,
                    data_source, as_of_date, confidence_tier, notes, created_at, updated_at
                )
                SELECT
                    gen_random_uuid(),
                    j.id,
                    :crew, :equip, :stage, :loc, :post, :vfx, :catering,
                    :travel, CAST(:overrides AS jsonb),
                    :source, :as_of, :tier, :notes, :now, :now
                FROM jurisdictions j
                WHERE j.code = :code
                LIMIT 1
            """),
            {
                "code": code,
                "crew": crew,
                "equip": equip,
                "stage": stage,
                "loc": loc,
                "post": post,
                "vfx": vfx,
                "catering": catering,
                "travel": travel,
                "overrides": json.dumps(overrides),
                "source": _BENCHMARK_SOURCE,
                "as_of": _AS_OF,
                "tier": "DISCOVERY",
                "notes": f"LA-relative cost multipliers for {code}. All values DISCOVERY tier.",
                "now": NOW,
            },
        )


def downgrade() -> None:
    # Remove benchmarks by code lookup
    for (code, *_) in BENCHMARKS:
        op.execute(
            sa.text("""
                DELETE FROM local_cost_benchmarks
                WHERE jurisdiction_id = (
                    SELECT id FROM jurisdictions WHERE code = :code LIMIT 1
                )
            """),
            {"code": code},
        )

    op.execute(
        sa.text("DELETE FROM incentive_programs WHERE id IN (:au, :nz)"),
        {"au": AU_PROG_ID, "nz": NZ_PROG_ID},
    )
    op.execute(
        sa.text("DELETE FROM jurisdictions WHERE id IN (:au, :nz)"),
        {"au": AU_JUR_ID, "nz": NZ_JUR_ID},
    )
