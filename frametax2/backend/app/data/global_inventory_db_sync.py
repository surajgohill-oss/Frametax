"""
global_inventory_db_sync.py — DB-seeded programs synced to Python optimizer path.

These programs were seeded to the database via Alembic migrations (0002, 0007)
but were absent from the pure-Python GlobalProgramEntry inventory. Adding them
here ensures the pure-Python optimizer (which uses ALL_PROGRAMS) can see and
evaluate them alongside the rest of the 229-program inventory.

No rates are invented: base_rate=None is preserved where DB migrations left it None.
"""
from __future__ import annotations

from app.data.global_inventory import GlobalProgramEntry

DB_SYNC_PROGRAMS: list[GlobalProgramEntry] = [
    # -----------------------------------------------------------------------
    # NOHFC — Northern Ontario Heritage Fund Corporation Production Fund
    # Seeded by migration 0007. discretionary_fund; fixed grant, not rate-based.
    # annual_cap_usd=500_000 reflects the illustrative per-project grant cited in 0007.
    # -----------------------------------------------------------------------
    GlobalProgramEntry(
        jurisdiction_code="CA-ON",
        jurisdiction_name="Ontario, Canada",
        program_name="Northern Ontario Heritage Fund — Production Fund",
        program_type="discretionary_fund",
        base_rate=None,          # Fixed grant, no rate
        max_rate=None,
        is_refundable=True,      # Cash grant
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=500_000,  # Illustrative per-project amount per 0007
        requires_cultural_test=False,
        requires_local_entity=True,
        confidence_tier="PARSED",
        source_title="NOHFC Production Fund Program Guidelines",
        source_url="https://www.nohfc.ca",
        effective_from=None,
        notes=(
            "Discretionary production fund for projects shooting in Northern Ontario. "
            "Grant must be deducted from qualifying expenditure base for CPTC and OFTTC "
            "per CRA T4283 and OMDC guidelines. Synced from migration 0007."
        ),
        unknown_fields=["confirmed_rate", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # OFTTC — Ontario Film and Television Tax Credit (domestic content)
    # Seeded by migration 0002. Domestic Canadian content track only.
    # Not to be confused with OPSTC (foreign service). Mutually exclusive with OPSTC.
    # -----------------------------------------------------------------------
    GlobalProgramEntry(
        jurisdiction_code="CA-ON",
        jurisdiction_name="Ontario, Canada",
        program_name="Ontario Film and Television Tax Credit (OFTTC)",
        program_type="tax_credit",
        base_rate=None,           # Rate not verified in 0002; DISCOVERY
        max_rate=None,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Ontario Film and Television Tax Credit",
        source_url="https://www.ontario.ca/page/ontario-film-and-television-tax-credit",
        effective_from=None,
        notes=(
            "Ontario domestic Canadian content tax credit. Requires CAVCO certification. "
            "Mutually exclusive with OPSTC (foreign service track). "
            "OFTTC amount is government assistance reducing CPTC qualified labour (ITA §125.4). "
            "Synced from migration 0002."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "processing_timeline"],
    ),

    # -----------------------------------------------------------------------
    # QC Film Production — Quebec Film and Television Production Tax Credit
    # Seeded by migration 0002. SODEC domestic content track.
    # Separate from QPRDP (wave6) which covers foreign service productions.
    # -----------------------------------------------------------------------
    GlobalProgramEntry(
        jurisdiction_code="CA-QC",
        jurisdiction_name="Quebec, Canada",
        program_name="Quebec Film and Television Production Tax Credit (SODEC)",
        program_type="tax_credit",
        base_rate=None,           # Rate not verified in 0002; DISCOVERY
        max_rate=None,
        is_refundable=True,
        is_transferable=False,
        min_spend_usd=None,
        annual_cap_usd=None,
        requires_cultural_test=True,
        requires_local_entity=True,
        confidence_tier="DISCOVERY",
        source_title="Quebec Film and Television Production Tax Credit",
        source_url="https://www.sodec.gouv.qc.ca/en/",
        effective_from=None,
        notes=(
            "SODEC Quebec domestic content tax credit. Requires Quebec content certification. "
            "This credit is government assistance reducing CPTC qualified labour under ITA §125.4. "
            "Separate from QPRDP (foreign service track). Synced from migration 0002."
        ),
        unknown_fields=["base_rate", "confirmed_rate", "annual_cap", "processing_timeline"],
    ),
]
