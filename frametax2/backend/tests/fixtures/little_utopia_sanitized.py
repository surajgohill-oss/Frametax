"""
little_utopia_sanitized.py

Sanitized budget fixture for THE LITTLE UTOPIA (Mauritius, v1.1, June 2025).

SANITIZATION RULES:
  - Account totals only.  No raw line items, no cast names, no personal data.
  - Amounts are representative of the production's budget structure.
  - Currency: USD (converted from MUR at 46 MUR/USD, EUR at 51.55 MUR/USD).
  - Memo lines (non-recoverable VAT, finance cost placeholders) are flagged
    is_memo_line=True and excluded from gross spend calculations.

QPE SCENARIO FLAGS (per account):
  conservative_qualifies — clearly Mauritius-sourced, non-contested
  base_qualifies         — includes accommodation/per diems and Frogsquad through MU SPV
  optimistic_qualifies   — includes ATL fees and all plausible MU BTL spend

MARINE FLAGS:
  is_marine=True — vessel charter, safety boats, dive/underwater team,
                   marine equipment, marine fuel

Finance cost note:
  Budget lines 82-00 Finance Costs / Bridge Interest show $0.
  Estimated real cost: ~$70K-$77K at 8% p.a. on ~$1.1M rebate for ~9 months.
  Not reflected in any account here — modeled separately by QPE calculator.

This fixture is used by tests/test_qpe_calculator.py and
tests/test_little_utopia_fixture.py.
"""
from __future__ import annotations

from app.calculators.qpe_calculator import QPEAccount

# ─── Gross budget totals (all non-memo accounts) ────────────────────────────
GROSS_BUDGET_USD = 4_364_393.0
ATL_TOTAL_USD = 538_444.0
MARINE_CLUSTER_USD = 415_000.0   # accounts flagged is_marine=True

# ─── QPE targets (expected calculator output for validation) ─────────────────
# These are derived from independent analysis of the gross budget.
# They are NOT taken from the budget's own "EDB Rebate" line.
QPE_CONSERVATIVE_TARGET = 1_550_000.0   # only confirmed MU-sourced BTL spend
QPE_BASE_TARGET = 2_500_000.0           # + accommodation/per diem + Frogsquad via SPV
QPE_OPTIMISTIC_TARGET = 3_060_000.0     # + ATL partial + remaining plausible BTL

# Expected rebate range at 35% (rounded to nearest $1K for fixture tolerance)
REBATE_CONSERVATIVE_35 = QPE_CONSERVATIVE_TARGET * 0.35   # ~$542,500
REBATE_BASE_35 = QPE_BASE_TARGET * 0.35                   # ~$875,000
REBATE_OPTIMISTIC_35 = QPE_OPTIMISTIC_TARGET * 0.35       # ~$1,071,000

# ─── Account definitions ─────────────────────────────────────────────────────

ACCOUNTS: list[QPEAccount] = [

    # ── Above The Line (10-19) ─────────────────────────────────────────────
    # ATL qualifying scope unconfirmed from EDB source.
    # Optimistic scenario assumes ATL fees paid through MU SPV may qualify.
    QPEAccount(
        account_code="10-00",
        description="Story & Screenplay Development",
        department="Above The Line",
        amount_usd=85_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=True,
        notes="ATL — qualifying scope unknown; excluded conservative/base",
    ),
    QPEAccount(
        account_code="11-00",
        description="Director Fee",
        department="Above The Line",
        amount_usd=175_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=True,
        notes="ATL — qualifying scope unknown; excluded conservative/base",
    ),
    QPEAccount(
        account_code="12-00",
        description="Producer Fees",
        department="Above The Line",
        amount_usd=148_444.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=True,
        notes="ATL — qualifying scope unknown; excluded conservative/base",
    ),
    QPEAccount(
        account_code="13-00",
        description="Lead Cast Agreements",
        department="Above The Line",
        amount_usd=130_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,  # Cast fees excluded even optimistic — strongest uncertainty
        notes="ATL cast — no indication cast fees qualify under EDB program",
    ),

    # ── BTL Production — Core Crew (20-29) ────────────────────────────────
    QPEAccount(
        account_code="20-00",
        description="Production Manager & Production Staff",
        department="Production",
        amount_usd=155_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="MU-resident production staff routed through MU entity",
    ),
    QPEAccount(
        account_code="21-00",
        description="Director of Photography",
        department="Production",
        amount_usd=95_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=True,
        notes="Imported HOD — qualifying depends on MU employer routing",
    ),
    QPEAccount(
        account_code="22-00",
        description="Camera Department & Equipment Rental",
        department="Production",
        amount_usd=185_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Equipment from MU vendor + local camera crew",
    ),
    QPEAccount(
        account_code="23-00",
        description="Sound Department",
        department="Production",
        amount_usd=65_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=True,
        notes="Imported sound team; routing unconfirmed",
    ),
    QPEAccount(
        account_code="24-00",
        description="Lighting & Electrical",
        department="Production",
        amount_usd=145_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Equipment rental + local MU electricians",
    ),
    QPEAccount(
        account_code="25-00",
        description="Grip Department",
        department="Production",
        amount_usd=82_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Equipment sourced MU + local grip operators",
    ),
    QPEAccount(
        account_code="26-00",
        description="Art Department / Production Design",
        department="Production",
        amount_usd=168_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Materials and labor sourced in Mauritius",
    ),
    QPEAccount(
        account_code="27-00",
        description="Wardrobe & Costume",
        department="Production",
        amount_usd=72_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Local sourcing + MU seamstresses",
    ),
    QPEAccount(
        account_code="28-00",
        description="Hair & Makeup",
        department="Production",
        amount_usd=55_000.0,
        conservative_qualifies=False,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Imported HOD; local MU trainees — base includes MU portion",
    ),
    QPEAccount(
        account_code="29-00",
        description="Location Fees & Permits (Mauritius)",
        department="Production",
        amount_usd=95_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Paid to MU authorities; confirmed qualifying",
    ),

    # ── BTL Production — Logistics (30-39) ────────────────────────────────
    QPEAccount(
        account_code="30-00",
        description="Transport & Ground Vehicles (Mauritius)",
        department="Production",
        amount_usd=112_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Local MU vehicle hire and drivers",
    ),

    # ── BTL Production — Marine Cluster (31-35) ───────────────────────────
    QPEAccount(
        account_code="31-00",
        description="Marine Unit — Vessel Charter",
        department="Production",
        amount_usd=165_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        is_marine=True,
        notes="Vessel chartered from MU operator; confirmed in budget QPE",
    ),
    QPEAccount(
        account_code="32-00",
        description="Marine Unit — Safety & Support Boats",
        department="Production",
        amount_usd=35_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        is_marine=True,
        notes="MU-based safety boat operator; confirmed in budget QPE",
    ),
    QPEAccount(
        account_code="33-00",
        description="Marine Unit — Frogsquad (SA Dive Package)",
        department="Production",
        amount_usd=99_837.0,
        conservative_qualifies=False,
        base_qualifies=True,
        optimistic_qualifies=True,
        is_marine=True,
        notes=(
            "SA-based marine/dive team (Frogsquad). "
            "Conservative: excluded — payment to SA entity, no MU routing confirmed. "
            "Base: included — assumes routed through MU SPV. "
            "Largest single QPE routing uncertainty (~$72K-$100K swing)."
        ),
    ),
    QPEAccount(
        account_code="34-00",
        description="Marine Equipment Rental (incl. underwater camera housing)",
        department="Production",
        amount_usd=93_163.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        is_marine=True,
        notes="Equipment rented from MU/regional supplier; treated as qualifying",
    ),
    QPEAccount(
        account_code="35-00",
        description="Marine Fuel & Consumables",
        department="Production",
        amount_usd=22_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        is_marine=True,
        notes="Fuel purchased in Mauritius; qualifying BTL spend",
    ),

    # ── BTL Production — Unit Costs (36-44) ───────────────────────────────
    QPEAccount(
        account_code="36-00",
        description="Catering & Craft Services (Mauritius unit)",
        department="Production",
        amount_usd=88_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Local MU catering company; confirmed MU spend",
    ),
    QPEAccount(
        account_code="37-00",
        description="HOD & International Crew Accommodation (Mauritius)",
        department="Production",
        amount_usd=159_783.0,
        conservative_qualifies=False,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes=(
            "Accommodation in Mauritius for imported HODs. "
            "Spent in MU but qualifying treatment unconfirmed. "
            "Conservative: excluded pending EDB confirmation."
        ),
    ),
    QPEAccount(
        account_code="38-00",
        description="Local Crew Accommodation & Per Diems (Mauritius)",
        department="Production",
        amount_usd=114_130.0,
        conservative_qualifies=False,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes=(
            "Per diems for 50 local crew × 42 days at 2,500 MUR/day. "
            "MU spend but per-diem qualifying treatment unconfirmed. "
            "Conservative: excluded pending EDB confirmation."
        ),
    ),
    QPEAccount(
        account_code="39-00",
        description="International Travel & Airfares",
        department="Production",
        amount_usd=143_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="International airfares — outside Mauritius; excluded all scenarios",
    ),
    QPEAccount(
        account_code="40-00",
        description="Supporting Artists (Extras) — Mauritius",
        department="Production",
        amount_usd=42_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Local MU talent; confirmed qualifying spend",
    ),
    QPEAccount(
        account_code="41-00",
        description="Payroll Services & PAYE / Employer Contributions",
        department="Production",
        amount_usd=68_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="MU payroll tax and employer NICs on local crew",
    ),
    QPEAccount(
        account_code="42-00",
        description="Stunts & Physical Special Effects",
        department="Production",
        amount_usd=48_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=True,
        notes="Imported stunt team; qualifying uncertain",
    ),
    QPEAccount(
        account_code="43-00",
        description="Unit Publicist & Production Stills",
        department="Production",
        amount_usd=24_000.0,
        conservative_qualifies=True,
        base_qualifies=True,
        optimistic_qualifies=True,
        notes="Local MU publicist",
    ),

    # ── Non-Recoverable VAT (Memo line — excluded from QPE) ───────────────
    QPEAccount(
        account_code="44-00",
        description="Non-Recoverable VAT @ 15% (Mauritius — Memo)",
        department="Production",
        amount_usd=92_439.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        is_memo_line=True,
        notes=(
            "Mauritius 15% VAT is non-recoverable for foreign film productions. "
            "Embedded in gross budget as memo line. Excluded from QPE all scenarios. "
            "Confirmed: $92,439 in gross budget."
        ),
    ),

    # ── Post Production (50-55) ────────────────────────────────────────────
    # Post work performed outside Mauritius — excluded from MU QPE all scenarios.
    QPEAccount(
        account_code="50-00",
        description="Editing — Offline Cut",
        department="Post Production",
        amount_usd=78_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Post performed outside Mauritius",
    ),
    QPEAccount(
        account_code="51-00",
        description="Color Grading & Mastering",
        department="Post Production",
        amount_usd=45_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Post performed outside Mauritius",
    ),
    QPEAccount(
        account_code="52-00",
        description="Sound Design & Final Mix",
        department="Post Production",
        amount_usd=62_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Post performed outside Mauritius",
    ),
    QPEAccount(
        account_code="53-00",
        description="Music Score & Licensing",
        department="Post Production",
        amount_usd=55_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Post performed outside Mauritius",
    ),
    QPEAccount(
        account_code="54-00",
        description="VFX / Digital Effects",
        department="Post Production",
        amount_usd=95_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="VFX outside Mauritius",
    ),
    QPEAccount(
        account_code="55-00",
        description="Deliverables & DCP Mastering",
        department="Post Production",
        amount_usd=28_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Post performed outside Mauritius",
    ),

    # ── Other / Finance / Insurance / Bond / Contingency (60-82) ──────────
    QPEAccount(
        account_code="60-00",
        description="Production Insurance (E&O + Liability)",
        department="Other",
        amount_usd=185_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Insurance excluded from incentive QPE per standard rules",
    ),
    QPEAccount(
        account_code="70-00",
        description="Legal & Accounting",
        department="Other",
        amount_usd=78_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Finance/legal costs excluded",
    ),
    QPEAccount(
        account_code="71-00",
        description="Audit & Incentive Submission Fees",
        department="Other",
        amount_usd=35_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Submission and audit fees not included in QPE",
    ),
    QPEAccount(
        account_code="80-00",
        description="Completion Bond Premium",
        department="Other",
        amount_usd=145_000.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Completion bond excluded from QPE",
    ),
    QPEAccount(
        account_code="81-00",
        description="Contingency Reserve",
        department="Other",
        amount_usd=596_597.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes="Contingency excluded from QPE",
    ),
    QPEAccount(
        account_code="82-00",
        description="Finance Costs / Bridge Interest on Rebate Receivable",
        department="Other",
        amount_usd=0.0,
        conservative_qualifies=False,
        base_qualifies=False,
        optimistic_qualifies=False,
        notes=(
            "Budget shows $0. Estimated real cost: ~$70K-$77K at 8% p.a. "
            "on ~$1.1M rebate for ~39 weeks. Not in budget — model separately."
        ),
    ),
]


# ─── Derived summary values for test assertions ───────────────────────────────

def get_marine_accounts() -> list[QPEAccount]:
    return [a for a in ACCOUNTS if a.is_marine]


def get_atl_accounts() -> list[QPEAccount]:
    return [a for a in ACCOUNTS if "above the line" in a.department.lower()]


def get_non_memo_accounts() -> list[QPEAccount]:
    return [a for a in ACCOUNTS if not a.is_memo_line]


def computed_gross_budget() -> float:
    """Grand total including memo/informational lines — matches reported gross."""
    return sum(a.amount_usd for a in ACCOUNTS)


def computed_non_memo_budget() -> float:
    """Total excluding memo lines — what the QPE calculator reports as gross_budget_usd."""
    return sum(a.amount_usd for a in get_non_memo_accounts())


def computed_marine_cluster() -> float:
    return sum(a.amount_usd for a in get_marine_accounts())


def computed_qpe(scenario: str) -> float:
    flag = f"{scenario}_qualifies"
    return sum(
        a.amount_usd for a in get_non_memo_accounts()
        if getattr(a, flag, False)
    )
