"""
Co-Pro Conditional Pricing Data Reconnection — focused unit tests.

Narrow Final Wiring Pass: closes ONE remaining data-reconnection class in
the Co-Pro Conditional Pricing Bridge (see test_copro_conditional_pricing_
bridge.py for the bridge itself, unchanged this pass). Three real fixes,
no new engine:

  1. au_producer_offset materialized as an executable RateRule from
     already-cited canonical knowledge (national_cultural_status.py's AU
     JurisdictionNationalStatus record: 40% feature / 30% other formats,
     screenaustralia.gov.au) -- priceable ONLY through the conditional
     official-co-production bridge, deliberately never registered into
     ordinary jurisdiction discovery (Section 4's "do not substitute
     service treatment for domestic/national treatment").
  2. Treaty-unlock slug spellings are now resolved through the existing
     canonical-slug alias table before pricing (see
     test_copro_conditional_pricing_bridge.py's alias-reconnection test
     for the generic proof).
  3. ca_cmf / fr_tax_credit_cinema / fr_cnc_production confirmed
     genuinely non-formulaic (competitive, recoupable funds -- see
     fund_economics_model.py / authority_coverage_registry.py) and left
     as disclosed CANONICAL_DATA_GAP, not silently "fixed".
"""
from __future__ import annotations

from app.data.fund_economics_model import get_fund_economics
from app.data.program_rate_rules import _RULES_BY_PROGRAM, resolve_program_rate
from app.data.executable_jurisdiction_registry import all_doctrine_records


def test_au_producer_offset_prices_through_the_canonical_kernel():
    rr_feature = resolve_program_rate("au_producer_offset", production_type="feature_film", qpe_usd=5_000_000.0)
    assert rr_feature is not None
    assert rr_feature.modeled_rate == 0.40

    rr_tv = resolve_program_rate("au_producer_offset", production_type="tv_series", qpe_usd=5_000_000.0)
    assert rr_tv is not None
    assert rr_tv.modeled_rate == 0.30


def test_au_producer_offset_never_leaks_into_ordinary_jurisdiction_discovery():
    """The real correctness guarantee this reconnection depends on:
    Producer Offset requires the Significant Australian Content test,
    which an ordinary (non-co-production) candidate can never satisfy.
    Registering it as an executable RateRule must NOT make it an ordinary
    discoverable AU candidate -- discover_executable_jurisdictions() reads
    all_doctrine_records(), not _RULES_BY_PROGRAM, for candidate
    construction, so au_producer_offset is deliberately absent from the
    former while present in the latter."""
    assert "au_producer_offset" in _RULES_BY_PROGRAM
    assert not any(r.program_slug == "au_producer_offset" for r in all_doctrine_records())


def test_au_location_and_pdv_offset_remain_ordinary_discoverable_candidates():
    """Control: the reconnection must not have disturbed the two AU
    programs that ARE meant to be ordinary discoverable candidates."""
    registered_slugs = {r.program_slug for r in all_doctrine_records()}
    assert "au_location_offset" in registered_slugs
    assert "au_pdv_offset" in registered_slugs


def test_ca_cmf_and_fr_funds_remain_genuinely_non_formulaic_not_fixed():
    """Section 8 control: ca_cmf / fr_cnc_production are real, competitive,
    recoupable/repayable funds (equity investment / advance against
    receipts) with no statutory percentage-of-QPE rate -- confirmed via
    their own existing fund_economics_model.py records. They must remain
    disclosed CANONICAL_DATA_GAP, never materialized as a RateRule (doing
    so would invent a rate the source doctrine does not state)."""
    for slug in ("ca_cmf", "fr_cnc_production"):
        assert slug not in _RULES_BY_PROGRAM, (
            f"{slug} must stay unpriced -- it is a competitive/recoupable "
            "fund, not a formulaic rate program"
        )
        entry = get_fund_economics(slug)
        assert entry is not None, f"{slug} must still carry its real fund_economics_model.py record"
        assert entry.is_competitive is True
        assert entry.is_repayable is True


def test_fr_tax_credit_cinema_remains_a_disclosed_genuine_gap():
    """fr_tax_credit_cinema has no citation anywhere in this project's
    canonical knowledge (unlike au_producer_offset, which had a real,
    cited rate sitting in national_cultural_status.py) -- a genuine
    CANONICAL_ECONOMIC_DATA_NOT_PRESENT case, not reconnected this pass,
    and must not have been silently invented to close it out."""
    assert "fr_tax_credit_cinema" not in _RULES_BY_PROGRAM
