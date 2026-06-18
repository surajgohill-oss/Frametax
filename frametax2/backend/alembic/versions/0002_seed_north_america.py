"""seed North America jurisdiction + incentive program placeholders

Revision ID: 0002
Revises: 0001
Create Date: 2025-06-18

NOTE ON RATES:
All base_rate values here are NULL or provisional (confidence_tier=DISCOVERY).
Do not promote any rate to VERIFIED without reviewing against a primary source document.
Sources are listed as notes; source_document_id will be linked when PDFs are ingested.
"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOW = datetime.now(timezone.utc).isoformat()


def _uid() -> str:
    return str(uuid.uuid4())


# Pre-assigned IDs so programs can reference jurisdictions
US_ID = _uid()
CA_COUNTRY_ID = _uid()
GB_ID = _uid()
CA_FEDERAL_ID = _uid()
US_CA_ID = _uid()
US_GA_ID = _uid()
US_NY_ID = _uid()
US_NM_ID = _uid()
US_LA_ID = _uid()
CA_ON_ID = _uid()
CA_BC_ID = _uid()
CA_QC_ID = _uid()

# Program IDs
PROG_CA_FILM30_ID = _uid()
PROG_GA_EIIA_ID = _uid()
PROG_NY_STATE_ID = _uid()
PROG_NM_FILM_ID = _uid()
PROG_LA_FILM_ID = _uid()
PROG_CA_OPSTC_ID = _uid()
PROG_CA_OFTTC_ID = _uid()
PROG_BC_PSTC_ID = _uid()
PROG_QC_CREDIT_ID = _uid()
PROG_CA_CPTC_ID = _uid()
PROG_UK_AVEC_ID = _uid()

# Qualification test IDs
UK_BFI_TEST_ID = _uid()
CAVCO_TEST_ID = _uid()


def upgrade() -> None:
    j = op.get_bind().execute  # shorthand not needed — use op.execute

    jurisdictions_table = sa.table(
        "jurisdictions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("parent_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("code", sa.String),
        sa.column("iso_code", sa.String),
        sa.column("level", sa.String),
        sa.column("currency_code", sa.String),
        sa.column("country_code", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("notes", sa.Text),
        sa.column("metadata_json", postgresql.JSONB),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    def jrow(id_, parent_id, name, code, iso, level, currency, country, notes=""):
        return {
            "id": id_, "parent_id": parent_id, "name": name, "code": code,
            "iso_code": iso, "level": level, "currency_code": currency,
            "country_code": country, "is_active": True,
            "notes": notes, "metadata_json": None,
            "created_at": NOW, "updated_at": NOW,
        }

    op.bulk_insert(jurisdictions_table, [
        jrow(US_ID, None, "United States", "US", "US", "country", "USD", "US"),
        jrow(CA_COUNTRY_ID, None, "Canada", "CA", "CA", "country", "CAD", "CA"),
        jrow(GB_ID, None, "United Kingdom", "GB", "GB", "country", "GBP", "GB"),
        jrow(US_CA_ID, US_ID, "California", "US-CA", "US-CA", "state", "USD", "US",
             "Los Angeles baseline jurisdiction for BTL cost benchmarks"),
        jrow(US_GA_ID, US_ID, "Georgia", "US-GA", "US-GA", "state", "USD", "US"),
        jrow(US_NY_ID, US_ID, "New York", "US-NY", "US-NY", "state", "USD", "US"),
        jrow(US_NM_ID, US_ID, "New Mexico", "US-NM", "US-NM", "state", "USD", "US"),
        jrow(US_LA_ID, US_ID, "Louisiana", "US-LA", "US-LA", "state", "USD", "US"),
        jrow(CA_ON_ID, CA_COUNTRY_ID, "Ontario", "CA-ON", "CA-ON", "province", "CAD", "CA"),
        jrow(CA_BC_ID, CA_COUNTRY_ID, "British Columbia", "CA-BC", "CA-BC", "province", "CAD", "CA"),
        jrow(CA_QC_ID, CA_COUNTRY_ID, "Quebec", "CA-QC", "CA-QC", "province", "CAD", "CA"),
    ])

    # Qualification Tests
    qt_table = sa.table(
        "qualification_tests",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("description", sa.Text),
        sa.column("jurisdiction_id", postgresql.UUID(as_uuid=True)),
        sa.column("total_available_points", sa.Integer),
        sa.column("minimum_pass_points", sa.Integer),
        sa.column("has_section_minimums", sa.Boolean),
        sa.column("section_minimums_json", postgresql.JSONB),
        sa.column("authority_url", sa.String),
        sa.column("confidence_tier", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(qt_table, [
        {
            "id": UK_BFI_TEST_ID, "name": "UK BFI Cultural Test",
            "slug": "uk_bfi_cultural_test", "jurisdiction_id": GB_ID,
            "description": "British Film Institute Cultural Test. 31 available points, 18 required. "
                           "Combined Section C+D must score at least 4 points.",
            "total_available_points": 31, "minimum_pass_points": 18,
            "has_section_minimums": True,
            "section_minimums_json": {"C+D": 4},
            "authority_url": "https://www.bfi.org.uk/industry-data-insights/film-forever/british-cultural-test",
            "confidence_tier": "DISCOVERY",
            "created_at": NOW, "updated_at": NOW,
        },
        {
            "id": CAVCO_TEST_ID, "name": "CAVCO Canadian Content Test",
            "slug": "cavco_canadian_content_test", "jurisdiction_id": CA_COUNTRY_ID,
            "description": "Canadian Audio-Visual Certification Office test for determining "
                           "Canadian-controlled productions eligible for federal tax credits.",
            "total_available_points": 10, "minimum_pass_points": 6,
            "has_section_minimums": False, "section_minimums_json": None,
            "authority_url": "https://www.canada.ca/en/canadian-heritage/services/funding/cavco.html",
            "confidence_tier": "DISCOVERY",
            "created_at": NOW, "updated_at": NOW,
        },
    ])

    # Incentive Programs — ALL confidence_tier=DISCOVERY, base_rate=NULL until verified
    prog_table = sa.table(
        "incentive_programs",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("jurisdiction_id", postgresql.UUID(as_uuid=True)),
        sa.column("source_document_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("program_type", sa.String),
        sa.column("credit_basis", sa.String),
        sa.column("base_rate", sa.Numeric),
        sa.column("max_rate", sa.Numeric),
        sa.column("is_refundable", sa.Boolean),
        sa.column("is_transferable", sa.Boolean),
        sa.column("transferable_value_pct", sa.Numeric),
        sa.column("is_competitive", sa.Boolean),
        sa.column("annual_cap_local", sa.Numeric),
        sa.column("requires_cultural_test", sa.Boolean),
        sa.column("cultural_test_id", postgresql.UUID(as_uuid=True)),
        sa.column("requires_local_entity", sa.Boolean),
        sa.column("effective_from", sa.String),
        sa.column("effective_until", sa.String),
        sa.column("confidence_tier", sa.String),
        sa.column("review_status", sa.String),
        sa.column("authority_url", sa.String),
        sa.column("last_verified_date", sa.String),
        sa.column("notes", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    def prog(id_, jid, name, slug, ptype, basis, base_r, max_r, refund, transfer,
             transfer_pct, competitive, cap, cult_test, cult_test_id, local_entity,
             url, notes_):
        return {
            "id": id_, "jurisdiction_id": jid, "source_document_id": None,
            "name": name, "slug": slug, "program_type": ptype, "credit_basis": basis,
            "base_rate": base_r, "max_rate": max_r,
            "is_refundable": refund, "is_transferable": transfer,
            "transferable_value_pct": transfer_pct,
            "is_competitive": competitive, "annual_cap_local": cap,
            "requires_cultural_test": cult_test, "cultural_test_id": cult_test_id,
            "requires_local_entity": local_entity,
            "effective_from": None, "effective_until": None,
            "confidence_tier": "DISCOVERY", "review_status": "pending",
            "authority_url": url, "last_verified_date": None,
            "notes": notes_,
            "created_at": NOW, "updated_at": NOW,
        }

    op.bulk_insert(prog_table, [
        prog(PROG_CA_FILM30_ID, US_CA_ID,
             "California Film & Television Tax Credit Program 3.0",
             "ca_film_30", "tax_credit", "qualifying_spend",
             None, None,  # rates unverified
             False, True, None,  # non-refundable, transferable
             True,   # COMPETITIVE ALLOCATION
             None, False, None, False,
             "https://film.ca.gov/tax-credit/",
             "DISCOVERY — rates not verified. Competitive annual allocation. "
             "Base rate approx 20%, 25% for independent films. Must verify from CDTFA."),
        prog(PROG_GA_EIIA_ID, US_GA_ID,
             "Georgia Entertainment Industry Investment Act",
             "georgia_eiia", "tax_credit", "qualifying_spend",
             None, None,
             False, True, None,
             False, None, False, None, True,
             "https://www.georgia.org/film-in-georgia",
             "DISCOVERY — rates not verified. Base rate approx 20%, +10% with Georgia logo. "
             "Transferable at ~88-92 cents on dollar. Min budget $500K. Verify from DOR."),
        prog(PROG_NY_STATE_ID, US_NY_ID,
             "New York State Film Tax Credit",
             "ny_state_film", "tax_credit", "qualifying_spend",
             None, None,
             True, False, None,
             False, None, False, None, True,
             "https://esd.ny.gov/ny-film-tax-credit",
             "DISCOVERY — rates not verified. Base rate approx 25%, +5% NYC area. "
             "Refundable. Min budget $1M. 75% NY spend or 40% NY shooting days. Verify from ESD."),
        prog(PROG_NM_FILM_ID, US_NM_ID,
             "New Mexico Film Production Tax Credit",
             "nm_film_production", "tax_credit", "qualifying_spend",
             None, None,
             True, False, None,
             False, None, False, None, True,
             "https://nmfilm.com/tax-incentives/",
             "DISCOVERY — rates not verified. Refundable credit. Verify from NM Taxation and Revenue."),
        prog(PROG_LA_FILM_ID, US_LA_ID,
             "Louisiana Motion Picture Production Tax Credit",
             "la_film_production", "tax_credit", "qualifying_spend",
             None, None,
             True, True, None,
             False, None, False, None, True,
             "https://www.louisianaentertainment.gov/film",
             "DISCOVERY — rates not verified. Verify from Louisiana Entertainment."),
        prog(PROG_CA_OPSTC_ID, CA_ON_ID,
             "Ontario Production Services Tax Credit",
             "on_opstc", "tax_credit", "qualifying_spend",
             None, None,
             True, False, None,
             False, None, False, None, False,
             "https://www.ontario.ca/page/ontario-film-and-television-tax-credit",
             "DISCOVERY — rates not verified. For foreign productions. "
             "Approx 21.5% on Ontario qualifying spend. Verify from Ontario Creates."),
        prog(PROG_CA_OFTTC_ID, CA_ON_ID,
             "Ontario Film and Television Tax Credit",
             "on_ofttc", "tax_credit", "qualifying_spend",
             None, None,
             True, False, None,
             False, None, False, CAVCO_TEST_ID, True,
             "https://www.ontario.ca/page/ontario-film-and-television-tax-credit",
             "DISCOVERY — for domestic Canadian productions. Requires CAVCO certification. "
             "Stacking rules with CPTC must be verified."),
        prog(PROG_BC_PSTC_ID, CA_BC_ID,
             "BC Production Services Tax Credit",
             "bc_pstc", "tax_credit", "qualifying_spend",
             None, None,
             True, False, None,
             False, None, False, None, False,
             "https://www.creativbc.com/tax-credits/",
             "DISCOVERY — rates not verified. For foreign productions. Verify from Creative BC."),
        prog(PROG_QC_CREDIT_ID, CA_QC_ID,
             "Quebec Film and Television Production Tax Credit",
             "qc_film_production", "tax_credit", "qualifying_spend",
             None, None,
             True, False, None,
             False, None, False, None, True,
             "https://www.sodec.gouv.qc.ca/en/",
             "DISCOVERY — rates not verified. Verify from SODEC."),
        prog(PROG_CA_CPTC_ID, CA_COUNTRY_ID,
             "Canadian Film or Video Production Tax Credit",
             "ca_federal_cptc", "tax_credit", "qualifying_labor",
             None, None,
             True, False, None,
             False, None, False, CAVCO_TEST_ID, True,
             "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/corporations/film-video-production.html",
             "DISCOVERY — federal credit for Canadian-controlled productions. "
             "Requires CAVCO certification. Approx 25% on Canadian labor. Verify from CRA."),
        prog(PROG_UK_AVEC_ID, GB_ID,
             "UK Audio Visual Expenditure Credit",
             "uk_avec", "tax_credit", "qualifying_spend",
             None, None,
             True, False, None,
             False, None, True, UK_BFI_TEST_ID, True,
             "https://www.gov.uk/guidance/uk-creative-industry-tax-reliefs",
             "DISCOVERY — rates not verified. Replaced BFTC in 2024. "
             "Approx 34% credit on qualifying UK spend (capped at 80% of total). "
             "Must pass BFI cultural test or qualify as official co-production. "
             "Min 10% UK qualifying expenditure. Verify from HMRC."),
    ])


def downgrade() -> None:
    op.execute("DELETE FROM incentive_programs WHERE confidence_tier = 'DISCOVERY' "
               "AND slug IN ('ca_film_30','georgia_eiia','ny_state_film','nm_film_production',"
               "'la_film_production','on_opstc','on_ofttc','bc_pstc','qc_film_production',"
               "'ca_federal_cptc','uk_avec')")
    op.execute("DELETE FROM qualification_tests WHERE slug IN "
               "('uk_bfi_cultural_test','cavco_canadian_content_test')")
    op.execute(f"DELETE FROM jurisdictions WHERE id IN ({','.join(repr(x) for x in [US_ID, CA_COUNTRY_ID, GB_ID, US_CA_ID, US_GA_ID, US_NY_ID, US_NM_ID, US_LA_ID, CA_ON_ID, CA_BC_ID, CA_QC_ID])})")
