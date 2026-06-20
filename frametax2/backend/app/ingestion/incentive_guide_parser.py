"""
incentive_guide_parser.py

Lightweight deterministic parser for film production incentive guide text.

Extracts structured data from unstructured incentive guide / statute text
that has been converted to plain text (e.g. via pdf_extractor).

No LLM calls. Pattern-matched extraction only.
Missing or ambiguous fields are left None with an extraction_note.
Results are DISCOVERY tier until manually reviewed against the source.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


PARSER_VERSION = "0.1.0"


@dataclass
class IncentiveGuideParseResult:
    """
    Structured data extracted from one incentive guide text.

    All fields default to None (unknown) rather than 0 or False.
    confidence_tier starts at DISCOVERY — caller must promote after review.
    """
    source_title: str
    jurisdiction_code: str          # ISO 3166-1 alpha-2
    confidence_tier: str = "DISCOVERY"

    # --- Rates ---
    base_rate: Optional[float] = None
    max_rate: Optional[float] = None
    is_cash_rebate: Optional[bool] = None
    is_tax_credit: Optional[bool] = None

    # --- Qualification scope ---
    atl_qualifies: Optional[bool] = None
    btl_qualifies: Optional[bool] = None
    vessel_marine_qualifies: Optional[bool] = None
    accommodation_qualifies: Optional[bool] = None
    per_diem_qualifies: Optional[bool] = None
    insurance_excluded: Optional[bool] = None
    contingency_excluded: Optional[bool] = None
    finance_costs_excluded: Optional[bool] = None
    international_travel_excluded: Optional[bool] = None
    foreign_labor_qualifies: Optional[bool] = None

    # --- Thresholds ---
    min_spend_local: Optional[float] = None
    min_spend_currency: Optional[str] = None
    annual_cap_local: Optional[float] = None
    requires_cultural_test: Optional[bool] = None

    # --- Cashflow ---
    cashflow_timing_weeks: Optional[int] = None
    is_refundable: Optional[bool] = None
    is_transferable: Optional[bool] = None

    # --- Extraction metadata ---
    rate_mentions: list[str] = field(default_factory=list)
    atl_mentions: list[str] = field(default_factory=list)
    marine_mentions: list[str] = field(default_factory=list)
    accommodation_mentions: list[str] = field(default_factory=list)
    exclusion_mentions: list[str] = field(default_factory=list)
    extraction_notes: list[str] = field(default_factory=list)
    parse_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Extraction patterns
# ---------------------------------------------------------------------------

_RATE_RE = re.compile(
    r"(\d{1,3}(?:\.\d{1,2})?)\s*%\s*"
    r"(?:cash\s+rebate|tax\s+credit|rebate|credit|incentive|relief|refund)",
    re.IGNORECASE,
)

_RATE_REVERSE_RE = re.compile(
    r"(?:cash\s+rebate|tax\s+credit|rebate|credit|incentive|relief)\s+of\s+"
    r"(\d{1,3}(?:\.\d{1,2})?)\s*%",
    re.IGNORECASE,
)

_MIN_SPEND_RE = re.compile(
    r"minimum\s+(?:qualifying\s+)?(?:spend|expenditure|production\s+spend)\s+of\s+"
    r"(?:EUR|USD|GBP|MUR|€|\$|£)\s*([\d,]+(?:\.\d{0,2})?)",
    re.IGNORECASE,
)

_MIN_SPEND_ALT_RE = re.compile(
    r"(?:EUR|USD|GBP|MUR|€|\$|£)\s*([\d,]+(?:\.\d{0,2})?)\s+"
    r"minimum",
    re.IGNORECASE,
)

_ATL_QUALIFY_RE = re.compile(
    r"(?:above.the.line|director|writer|producer|cast)\s+(?:fees?\s+)?(?:are\s+)?"
    r"(?:eligible|qualifying|included|qualify)",
    re.IGNORECASE,
)

_ATL_EXCLUDE_RE = re.compile(
    r"(?:above.the.line|director|writer|producer|cast)\s+(?:fees?\s+)?(?:are\s+)?"
    r"(?:not\s+eligible|excluded|not\s+qualifying|do\s+not\s+qualify)",
    re.IGNORECASE,
)

_MARINE_QUALIFY_RE = re.compile(
    r"(?:vessel|yacht|charter|boat|marine|underwater|diving|nautical)\s+"
    r"(?:hire|rental|charter|equipment|support|costs?|expenditure)?"
    r"\s*(?:are\s+)?(?:eligible|qualifying|included|qualify)",
    re.IGNORECASE,
)

_ACCOMMODATION_QUALIFY_RE = re.compile(
    r"(?:accommodation|hotel|lodging|per\s+diem|per-diem|daily\s+allowance)\s+"
    r"(?:costs?\s+)?(?:are\s+)?(?:eligible|qualifying|included|qualify)",
    re.IGNORECASE,
)

_INSURANCE_EXCLUDE_RE = re.compile(
    r"insurance\s+(?:costs?\s+)?(?:are\s+)?(?:not\s+)?(?:eligible|included|qualifying|excluded)",
    re.IGNORECASE,
)

_CONTINGENCY_EXCLUDE_RE = re.compile(
    r"contingency\s+(?:are\s+)?(?:not\s+)?(?:eligible|included|qualifying|excluded)",
    re.IGNORECASE,
)

_CASH_REBATE_RE = re.compile(r"cash\s+rebate", re.IGNORECASE)
_TAX_CREDIT_RE = re.compile(r"tax\s+credit", re.IGNORECASE)
_REFUNDABLE_RE = re.compile(r"refundable|refund(?:ed|able)\s+tax\s+credit", re.IGNORECASE)
_TRANSFERABLE_RE = re.compile(r"assignable|transferable|sold\s+to", re.IGNORECASE)
_CULTURAL_TEST_RE = re.compile(r"cultural\s+test|cultural\s+contribution|cultural\s+certification", re.IGNORECASE)

_WEEKS_RE = re.compile(r"(\d{1,3})\s+(?:working\s+)?weeks?", re.IGNORECASE)
_DAYS_WEEKS_RE = re.compile(r"(\d{1,3})\s+(?:working\s+)?days?", re.IGNORECASE)

_FOREIGN_LABOR_RE = re.compile(
    r"(?:foreign|non.resident|international|imported)\s+"
    r"(?:crew|labor|labour|personnel|cast)\s+"
    r"(?:costs?\s+)?(?:are\s+)?(?:eligible|qualifying|included|qualify)",
    re.IGNORECASE,
)

_CURRENCY_RE = re.compile(r"(EUR|USD|GBP|MUR|€|\$|£)", re.IGNORECASE)


def _extract_rate(text: str) -> tuple[Optional[float], list[str]]:
    mentions = []
    rates = []
    for m in _RATE_RE.finditer(text):
        mentions.append(m.group(0).strip())
        rates.append(float(m.group(1)) / 100.0)
    for m in _RATE_REVERSE_RE.finditer(text):
        mentions.append(m.group(0).strip())
        rates.append(float(m.group(1)) / 100.0)
    if not rates:
        return None, mentions
    return min(rates), mentions  # base = lowest mentioned


def _extract_max_rate(rates_found: list[float]) -> Optional[float]:
    if not rates_found:
        return None
    return max(rates_found)


def _extract_min_spend(text: str) -> tuple[Optional[float], Optional[str]]:
    for pattern in (_MIN_SPEND_RE, _MIN_SPEND_ALT_RE):
        m = pattern.search(text)
        if m:
            amt_str = m.group(1).replace(",", "")
            try:
                amt = float(amt_str)
            except ValueError:
                continue
            currency_m = _CURRENCY_RE.search(m.group(0))
            currency = currency_m.group(1) if currency_m else None
            return amt, currency
    return None, None


def _extract_cashflow_weeks(text: str) -> Optional[int]:
    for m in _WEEKS_RE.finditer(text):
        if int(m.group(1)) <= 104:  # sanity check: ≤ 2 years
            return int(m.group(1))
    for m in _DAYS_WEEKS_RE.finditer(text):
        days = int(m.group(1))
        if days <= 365:
            return max(1, round(days / 7))
    return None


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def parse_incentive_guide(
    text: str,
    source_title: str,
    jurisdiction_code: str,
) -> IncentiveGuideParseResult:
    """
    Extract structured incentive program data from unstructured text.

    Parameters
    ----------
    text              : full text of the incentive guide (UTF-8)
    source_title      : human-readable title of the source document
    jurisdiction_code : ISO 3166-1 alpha-2 country code

    Returns
    -------
    IncentiveGuideParseResult at DISCOVERY tier.
    Caller must manually verify and promote to PARSED/VERIFIED.
    """
    result = IncentiveGuideParseResult(
        source_title=source_title,
        jurisdiction_code=jurisdiction_code,
        confidence_tier="DISCOVERY",
    )

    # --- Rate extraction ---
    all_rates = []
    for m in _RATE_RE.finditer(text):
        result.rate_mentions.append(m.group(0).strip()[:120])
        all_rates.append(float(m.group(1)) / 100.0)
    for m in _RATE_REVERSE_RE.finditer(text):
        snippet = m.group(0).strip()[:120]
        if snippet not in result.rate_mentions:
            result.rate_mentions.append(snippet)
        all_rates.append(float(m.group(1)) / 100.0)

    if all_rates:
        result.base_rate = min(all_rates)
        result.max_rate = max(all_rates)
        if result.base_rate == result.max_rate:
            result.max_rate = result.base_rate
    else:
        result.extraction_notes.append("No rate percentage found in text")

    # --- Program type ---
    if _CASH_REBATE_RE.search(text):
        result.is_cash_rebate = True
    if _TAX_CREDIT_RE.search(text):
        result.is_tax_credit = True
    if result.is_cash_rebate is None and result.is_tax_credit is None:
        result.extraction_notes.append("Program type (rebate vs credit) not detected")

    # --- ATL treatment ---
    atl_qual = bool(_ATL_QUALIFY_RE.search(text))
    atl_excl = bool(_ATL_EXCLUDE_RE.search(text))
    for m in _ATL_QUALIFY_RE.finditer(text):
        result.atl_mentions.append(m.group(0).strip()[:120])
    if atl_qual and not atl_excl:
        result.atl_qualifies = True
    elif atl_excl and not atl_qual:
        result.atl_qualifies = False
    elif atl_qual and atl_excl:
        result.atl_qualifies = None
        result.extraction_notes.append("Conflicting ATL signals — manual review required")

    # --- Marine/vessel treatment ---
    for m in _MARINE_QUALIFY_RE.finditer(text):
        result.marine_mentions.append(m.group(0).strip()[:120])
    if result.marine_mentions:
        result.vessel_marine_qualifies = True

    # --- Accommodation/per diem treatment ---
    for m in _ACCOMMODATION_QUALIFY_RE.finditer(text):
        result.accommodation_mentions.append(m.group(0).strip()[:120])
    if result.accommodation_mentions:
        result.accommodation_qualifies = True
        result.per_diem_qualifies = True

    # --- Exclusions ---
    ins_m = _INSURANCE_EXCLUDE_RE.search(text)
    if ins_m:
        result.exclusion_mentions.append(ins_m.group(0).strip()[:120])
        snippet = ins_m.group(0).lower()
        result.insurance_excluded = "not" in snippet or "exclud" in snippet

    cont_m = _CONTINGENCY_EXCLUDE_RE.search(text)
    if cont_m:
        result.exclusion_mentions.append(cont_m.group(0).strip()[:120])
        snippet = cont_m.group(0).lower()
        result.contingency_excluded = "not" in snippet or "exclud" in snippet

    # --- Foreign labor ---
    if _FOREIGN_LABOR_RE.search(text):
        result.foreign_labor_qualifies = True

    # --- Minimum spend ---
    result.min_spend_local, result.min_spend_currency = _extract_min_spend(text)

    # --- Cashflow timing ---
    result.cashflow_timing_weeks = _extract_cashflow_weeks(text)

    # --- Refundability / transferability ---
    if _REFUNDABLE_RE.search(text):
        result.is_refundable = True
    if _TRANSFERABLE_RE.search(text):
        result.is_transferable = True

    # --- Cultural test ---
    if _CULTURAL_TEST_RE.search(text):
        result.requires_cultural_test = True
        result.extraction_notes.append("Cultural test requirement detected — verify scope")

    # --- BTL assumed True if any qualifying spend is mentioned ---
    if result.atl_qualifies or result.vessel_marine_qualifies:
        result.btl_qualifies = True

    return result
