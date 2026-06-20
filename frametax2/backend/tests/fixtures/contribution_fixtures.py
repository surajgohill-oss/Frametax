"""
contribution_fixtures.py

Synthetic ContributionInput fixtures for five canonical production economics scenarios:

1. vendor_equity_post_deal     — post house takes equity instead of cash
2. deferred_producer_fee       — producer defers fee to backend
3. government_grant            — non-repayable government grant (Mauritius MFDC)
4. free_facility_use           — resort provides location free in exchange for credit
5. equipment_sponsorship       — camera vendor provides gear for product placement

Each fixture includes rationale for every field.
"""
from __future__ import annotations

from app.calculators.production_economics import ContributionInput

# ---------------------------------------------------------------------------
# 1. Vendor equity post deal
#    Post-production house (colour, grade, DCP) offers services in exchange
#    for an equity stake instead of their normal cash fee.
# ---------------------------------------------------------------------------
vendor_equity_post_deal = ContributionInput(
    contribution_type="equity",
    provider="Chromatic Post Ltd",
    amount=150_000.0,           # Equity stake face value agreed in deal memo
    fair_market_value=90_000.0, # Risk-adjusted FMV: equity ≠ guaranteed payment;
                                # discounted ~40% for delivery/recoupment risk
    replacement_cost=150_000.0, # What you'd pay a market-rate post house in cash
    jurisdiction_code="MT",     # Malta post facility
    jurisdiction_specific=True,
    qualifies_for_incentive=False,  # Equity arrangements are not qualifying QPE spend
    is_conditional=True,        # Equity only vests if film is delivered and sold
    condition_notes="Equity stake vests only upon verified theatrical release",
    confidence_tier="PARSED",
    notes=(
        "Chromatic Post holds a 2% equity stake in place of their standard cash fee. "
        "FMV discounted from $150K face to $90K on 40% risk-adjusted delivery haircut. "
        "Replacement cost = market-rate Malta post house cash fee if deal collapses."
    ),
)

# ---------------------------------------------------------------------------
# 2. Deferred producer fee
#    Producer defers their negotiated fee until first recoupment.
# ---------------------------------------------------------------------------
deferred_producer_fee = ContributionInput(
    contribution_type="deferred",
    provider="Sarah Ndao (Producer)",
    amount=125_000.0,           # Full market-rate producer fee being deferred
    fair_market_value=125_000.0, # No discount — deferred, not forgiven; same face value
    replacement_cost=125_000.0,  # Cost to hire equivalent market-rate producer
    jurisdiction_code="MU",
    jurisdiction_specific=True,
    qualifies_for_incentive=True,   # Producer fee may qualify as ATL QPE in some jurisdictions
                                     # (MU ATL scope unknown, but optimistic inclusion)
    is_conditional=False,
    confidence_tier="PARSED",
    notes=(
        "Producer fee of $125,000 deferred to backend. "
        "No interest; subordinated to gap lender recoupment. "
        "qualifies_for_incentive=True reflects optimistic ATL inclusion assumption; "
        "MU ATL qualifying scope is currently UNKNOWN — treat as uncertain until confirmed."
    ),
)

# ---------------------------------------------------------------------------
# 3. Government grant
#    Non-repayable production support grant from Mauritius Film Development Corp.
# ---------------------------------------------------------------------------
government_grant = ContributionInput(
    contribution_type="government_support",
    provider="Mauritius Film Development Corporation (MFDC)",
    amount=50_000.0,
    fair_market_value=50_000.0,     # Grant = cash equivalent; FMV = face value
    replacement_cost=50_000.0,
    jurisdiction_code="MU",
    jurisdiction_specific=True,
    qualifies_for_incentive=False,  # Grant is a benefit; not qualifying spend
                                     # (it reduces net cost, not adds to QPE)
    is_conditional=True,
    condition_notes="Grant conditioned on minimum 20 Mauritius shooting days and final delivery",
    confidence_tier="DISCOVERY",
    notes=(
        "MFDC discretionary production support grant. "
        "No confirmed grant programme exists at this amount — DISCOVERY tier. "
        "Excludes from QPE: government grants reduce net cost but are not qualifying expenditure."
    ),
)

# ---------------------------------------------------------------------------
# 4. Free facility use (in-kind)
#    Beachfront resort provides filming access and accommodation block
#    in exchange for brand placement in the film.
# ---------------------------------------------------------------------------
free_facility_use = ContributionInput(
    contribution_type="in_kind",
    provider="Tamarin Bay Resort",
    amount=0.0,                  # No cash exchanged
    fair_market_value=45_000.0,  # Commercial rate for equivalent location rental
                                  # + accommodation block (3 weeks)
    replacement_cost=45_000.0,
    jurisdiction_code="MU",
    jurisdiction_specific=True,
    qualifies_for_incentive=None,  # Uncertain: in-kind may qualify if treated as
                                    # deemed expenditure at FMV in some jurisdictions
    is_conditional=False,
    confidence_tier="DISCOVERY",
    notes=(
        "Resort provides: exclusive use of beachfront and villa block (3 weeks), "
        "valued at $45,000 commercial rate. "
        "Contractual: brand/logo placement in end credits and two key scenes. "
        "qualifies_for_incentive=None: in-kind qualifying treatment under EDB unknown."
    ),
)

# ---------------------------------------------------------------------------
# 5. Equipment sponsorship
#    Camera vendor provides camera package in exchange for product placement.
# ---------------------------------------------------------------------------
equipment_sponsorship = ContributionInput(
    contribution_type="sponsorship",
    provider="StellarOptics GmbH",
    amount=35_000.0,             # Declared sponsorship value in deal
    fair_market_value=35_000.0,  # Verified against standard camera rental rates
    replacement_cost=35_000.0,   # What it would cost to rent same package commercially
    jurisdiction_code=None,      # Equipment origin: Germany; not jurisdiction-specific
    jurisdiction_specific=False,
    qualifies_for_incentive=None,  # Depends on programme: some treat sponsorship as
                                    # non-cash qualifying spend; others exclude it
    is_conditional=False,
    confidence_tier="PARSED",
    notes=(
        "4-week camera package (2× bodies, lenses, accessories) at $35,000 declared value. "
        "Verified against market rate: comparable rental = $33,000-$38,000. "
        "Product placement: logo visible in 3 scenes; camera bodies un-logoed per DOP request. "
        "qualifies_for_incentive=None: jurisdiction-specific; not Mauritius-specific spend."
    ),
)

# ---------------------------------------------------------------------------
# Canonical scenario set (use in tests)
# ---------------------------------------------------------------------------
ALL_FIXTURES: list[ContributionInput] = [
    vendor_equity_post_deal,
    deferred_producer_fee,
    government_grant,
    free_facility_use,
    equipment_sponsorship,
]

# Gross budget for fixture-level tests (non-memo total from Little Utopia fixture)
FIXTURE_GROSS_BUDGET_USD = 4_271_954.0

# Expected derived values (computed from fixture design above)
EXPECTED_CASH_BUDGET = 0.0                     # No CASH contributions in this fixture set
EXPECTED_CONTRIBUTION_VALUE = (
    90_000.0    # equity FMV
    + 125_000.0 # deferred
    + 50_000.0  # government grant
    + 45_000.0  # in-kind FMV
    + 35_000.0  # sponsorship
)  # = 345_000.0
EXPECTED_REPLACEMENT_COST = (
    150_000.0   # post house equity → replacement is cash fee
    + 125_000.0 # producer fee
    + 50_000.0  # grant
    + 45_000.0  # facility
    + 35_000.0  # equipment
)  # = 405_000.0
EXPECTED_INCENTIVE_QUALIFYING = 125_000.0       # only deferred_producer_fee qualifies
EXPECTED_UNCERTAIN = 45_000.0 + 35_000.0       # free_facility + equipment_sponsorship = 80_000.0
EXPECTED_CONDITIONAL_EXPOSURE = (
    90_000.0    # vendor_equity (conditional)
    + 50_000.0  # government_grant (conditional)
)  # = 140_000.0
