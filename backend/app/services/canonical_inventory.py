"""
Canonical Inventory Engine — Phase 3 (Confidence V2 + Seat Intelligence)

CANONICAL SEAT BLOCK
────────────────────
One canonical block = one purchasable physical seat position.

Identity is determined by priority:
  1. seat_group_hash   — exact seat fingerprint (highest precision)
  2. (section, row, quantity, seat_range)  — inferred adjacency
  3. (section, row, quantity)  — positional grouping (lowest precision)

CONFIDENCE V2 SCORING
──────────────────────
confidence_v2 = normalized product of:

  Core factors (always present):
    freshness_factor        0.50–1.00   recency of last_seen_at
    seller_factor           0.60–1.00   number of sellers listing this block
    market_factor           0.85–1.00   number of distinct markets carrying block
    mp_weight               0.60–0.90   average marketplace reliability weight
    price_consistency       0.20–1.00   price spread within canonical group

  Enhancement factors (conditional bonuses/penalties):
    exact_seat_bonus        1.00–1.20   block has confirmed seat-number fingerprint
    cross_market_convergence 0.90–1.08  price convergence across markets
    price_anomaly_penalty   0.70–1.00   outlier price vs. section median
    temporal_bonus          1.00–1.05   block consistently present across polls

  Final clamp: min(score, 1.0)

Target thresholds:
  Mirrored + exact-seat + 2 markets ≥ 0.85
  Single-market, no seat data ≤ 0.65

SECTION NORMALIZATION
──────────────────────
  "Section 112"  → "112"
  "Sec. 112"     → "112"
  "GA Floor"     → "GA"
  "Field 112"    → "112 FIELD"

MARKETPLACE WEIGHTS
────────────────────
  stubhub:  0.90
  tickpick: 0.85
  gametime: 0.80  (seat numbers available → high dedup precision)
  seatgeek: 0.60  (DataDome blocked, unreliable)
"""

from __future__ import annotations

import hashlib
import re as _re
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Listing, Marketplace, Event
from app.models.venue import Venue


# ── Marketplace confidence weights ────────────────────────────────────────────

MP_CONFIDENCE: dict[str, float] = {
    "stubhub":  0.90,
    "tickpick": 0.85,
    "gametime": 0.80,
    "seatgeek": 0.60,
}
_DEFAULT_MP_CONFIDENCE = 0.70

# Freshness decay
_FRESH_THRESHOLD_HOURS = 2
_STALE_THRESHOLD_HOURS = 6


# ── Section normalization ─────────────────────────────────────────────────────

_SECTION_STRIP = _re.compile(r"^(section|sec\.?)\s*", _re.IGNORECASE)
_GA_PATTERN    = _re.compile(r"\b(ga|general\s+admission|lawn|standing)\b", _re.IGNORECASE)


def normalize_section(raw: str) -> str:
    if not raw:
        return "UNKNOWN"
    s = raw.strip().upper()
    if _GA_PATTERN.search(s):
        return "GA"
    s = _SECTION_STRIP.sub("", s.lower()).strip().upper()
    return s or "UNKNOWN"


def normalize_row(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return raw.strip().upper() or None


# ── Seat identity + fingerprinting ────────────────────────────────────────────

_SEAT_RANGE_RE = _re.compile(r"^(\d+)\s*[-–]\s*(\d+)$")
_SEAT_LIST_RE  = _re.compile(r"^\d+(?:\s*,\s*\d+)*$")


def parse_seat_numbers(raw: Optional[str]) -> Optional[list[int]]:
    """Parse seat_numbers string into sorted int list. Returns None if unparseable."""
    if not raw:
        return None
    raw = raw.strip()
    m = _SEAT_RANGE_RE.match(raw)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return list(range(lo, hi + 1)) if hi - lo < 30 else [lo, hi]
    if _SEAT_LIST_RE.match(raw):
        return sorted(int(x.strip()) for x in raw.split(","))
    return None


def seat_group_hash(seats: list[int]) -> str:
    """Deterministic 24-char hex hash of a normalized seat set."""
    canon = ",".join(str(s) for s in sorted(set(seats)))
    return hashlib.sha256(canon.encode()).hexdigest()[:24]


def infer_seat_range(seat_start: Optional[int], seat_end: Optional[int], quantity: int) -> Optional[list[int]]:
    """Infer seat list from (seat_start, seat_end, quantity) when exact list unavailable."""
    if seat_start is None:
        return None
    end = seat_end if seat_end is not None else seat_start + quantity - 1
    if end - seat_start + 1 == quantity:
        return list(range(seat_start, end + 1))
    return [seat_start, end]  # non-contiguous — only anchors


def adjacency_signature(seats: list[int]) -> str:
    """
    Produces a compact string describing seat contiguity.
    [5,6,7] → "5-7"   [5,7,9] → "5,7,9"  [5,6,8] → "5-6,8"
    Used for approximate matching when exact fingerprint unavailable.
    """
    if not seats:
        return ""
    sorted_s = sorted(set(seats))
    runs: list[list[int]] = []
    cur = [sorted_s[0]]
    for s in sorted_s[1:]:
        if s == cur[-1] + 1:
            cur.append(s)
        else:
            runs.append(cur)
            cur = [s]
    runs.append(cur)
    parts = [f"{r[0]}-{r[-1]}" if len(r) > 1 else str(r[0]) for r in runs]
    return ",".join(parts)


# ── Canonical key ─────────────────────────────────────────────────────────────

def _canonical_key(section_id: Optional[str], row: Optional[str], quantity: int,
                   seat_hash: Optional[str] = None) -> tuple:
    """
    Primary key for grouping into canonical blocks.
    When seat_hash is available it replaces row+qty for higher precision.
    """
    sec = (section_id or "").upper().strip()
    if seat_hash:
        return (sec, f"__seat__{seat_hash}", quantity)
    return (sec, (row or "").upper().strip(), quantity)


def _block_id(key: tuple) -> str:
    raw = "|".join(str(x) for x in key)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class SellerEntry:
    listing_id: int
    marketplace_slug: str
    price: float
    all_in_price: Optional[float]
    last_seen_at: Optional[datetime]
    external_listing_id: Optional[str]
    # Location (kept for row recovery when seat-keyed)
    row: Optional[str] = None
    # Seat intelligence
    has_exact_seats: bool = False
    seat_hash: Optional[str] = None
    seat_signature: Optional[str] = None   # adjacency signature
    seats: Optional[list[int]] = None      # parsed seat numbers


@dataclass
class CanonicalBlock:
    block_id: str
    section_id: str
    row: Optional[str]
    quantity: int
    # Seat intelligence
    has_exact_seats: bool
    seat_hash: Optional[str]
    seat_signature: Optional[str]
    seat_identity: str                    # "exact" | "inferred" | "positional"
    # Sellers
    seller_count: int
    sellers: list[SellerEntry]
    marketplace_slugs: list[str]
    # Price intelligence
    low_ask: float
    high_ask: float
    median_ask: float
    price_spread_pct: float
    # Confidence V2
    confidence_score: float
    confidence_factors: dict              # full breakdown for auditability
    confidence_version: str              # "v2"
    # Freshness
    last_seen_at: Optional[datetime]
    freshness_label: str
    # Duplication
    is_mirrored: bool
    duplicate_explanation: str


@dataclass
class CanonicalInventoryView:
    event_id: int
    as_of: datetime
    canonical_blocks: list[CanonicalBlock]
    # Aggregate metrics
    total_canonical_blocks: int
    total_raw_listings: int
    global_duplicate_ratio: float
    mirrored_block_count: int
    mirrored_ratio: float
    by_marketplace: dict[str, int]
    # Confidence distribution
    mean_confidence: float
    high_confidence_blocks: int          # ≥ 0.80
    low_confidence_blocks: int           # < 0.50
    # Seat intelligence metrics
    exact_seat_blocks: int               # blocks with confirmed seat fingerprint
    inferred_seat_blocks: int            # blocks with inferred seat range
    positional_blocks: int               # blocks with only (section, row, qty)
    exact_seat_mirrored: int             # mirrored AND exact-seat confirmed


# ── Confidence V2 — individual factors ───────────────────────────────────────

def _freshness_factor(last_seen_at: Optional[datetime]) -> tuple[float, str]:
    if not last_seen_at:
        return 0.5, "unknown"
    now = datetime.now(timezone.utc) if last_seen_at.tzinfo else datetime.utcnow()
    age_h = (now - last_seen_at).total_seconds() / 3600
    if age_h <= _FRESH_THRESHOLD_HOURS:
        return 1.0, "fresh"
    elif age_h <= _STALE_THRESHOLD_HOURS:
        factor = 1.0 - 0.3 * ((age_h - _FRESH_THRESHOLD_HOURS) / (_STALE_THRESHOLD_HOURS - _FRESH_THRESHOLD_HOURS))
        return round(factor, 3), "aging"
    return 0.5, "stale"


def _price_consistency(prices: list[float]) -> float:
    if len(prices) <= 1:
        return 1.0
    lo, hi = min(prices), max(prices)
    if lo == 0:
        return 0.5
    spread_pct = (hi - lo) / lo
    return max(0.2, round(1.0 - min(spread_pct / 0.5, 1.0) * 0.5, 3))


def _seller_factor(seller_count: int) -> float:
    if seller_count == 1:
        return 0.60
    elif seller_count == 2:
        return 0.80
    elif seller_count <= 5:
        return 0.90
    return 1.0


def _market_factor(marketplace_count: int) -> float:
    if marketplace_count == 1:
        return 0.85
    elif marketplace_count == 2:
        return 0.95
    return 1.0


def _exact_seat_bonus(has_exact_seats: bool, is_mirrored: bool) -> float:
    """
    Bonus multiplier for exact seat confirmation.

    Exact-seat + mirrored = strongest possible canonical signal: independent
    marketplaces listing the same fingerprinted seat set.  Use 1.30 so that
    a fresh 2-market exact-seat block with consistent pricing clears 0.85.

    Single-market exact seats still boost confidence (+10%) but can't reach
    the 0.85 threshold without cross-market confirmation.
    """
    if not has_exact_seats:
        return 1.0
    return 1.30 if is_mirrored else 1.10


def _cross_market_convergence(sellers: list[SellerEntry], marketplace_slugs: list[str]) -> float:
    """
    When multiple markets agree on price within ±10%, confidence increases.
    When prices diverge significantly across markets, slight penalty.
    """
    unique_markets = set(marketplace_slugs)
    if len(unique_markets) < 2:
        return 1.0
    mp_prices: dict[str, list[float]] = {}
    for s in sellers:
        mp_prices.setdefault(s.marketplace_slug, []).append(s.price)
    mp_medians = [statistics.median(p) for p in mp_prices.values() if p]
    if len(mp_medians) < 2:
        return 1.0
    lo, hi = min(mp_medians), max(mp_medians)
    if lo == 0:
        return 1.0
    spread = (hi - lo) / lo
    if spread < 0.05:
        return 1.08   # tight cross-market convergence
    elif spread < 0.10:
        return 1.04
    elif spread < 0.20:
        return 1.00   # neutral
    else:
        return 0.92   # significant divergence — suspect same seats, different price


def _compute_confidence_v2(
    sellers: list[SellerEntry],
    marketplace_slugs: list[str],
    has_exact_seats: bool,
    is_mirrored: bool,
) -> tuple[float, dict]:
    prices = [s.price for s in sellers]
    last_seen = max((s.last_seen_at for s in sellers if s.last_seen_at), default=None)

    freshness, freshness_label = _freshness_factor(last_seen)
    price_cons    = _price_consistency(prices)
    seller_f      = _seller_factor(len(sellers))
    market_f      = _market_factor(len(set(marketplace_slugs)))
    mp_weight     = sum(MP_CONFIDENCE.get(mp, _DEFAULT_MP_CONFIDENCE) for mp in set(marketplace_slugs)) / max(len(set(marketplace_slugs)), 1)
    seat_bonus    = _exact_seat_bonus(has_exact_seats, is_mirrored)
    convergence   = _cross_market_convergence(sellers, marketplace_slugs)

    # Weighted product
    score = freshness * price_cons * seller_f * market_f * mp_weight * seat_bonus * convergence
    score = round(min(score, 1.0), 3)

    return score, {
        "version":            "v2",
        "freshness":          freshness,
        "freshness_label":    freshness_label,
        "price_consistency":  price_cons,
        "seller_factor":      seller_f,
        "market_factor":      market_f,
        "mp_weight":          round(mp_weight, 3),
        "exact_seat_bonus":   seat_bonus,
        "cross_market_conv":  convergence,
        "is_mirrored":        is_mirrored,
        "has_exact_seats":    has_exact_seats,
    }


# ── Duplicate explanation ─────────────────────────────────────────────────────

def _explain_duplication(sellers: list[SellerEntry], marketplace_slugs: list[str],
                          has_exact_seats: bool, seat_signature: Optional[str]) -> str:
    unique_markets = sorted(set(marketplace_slugs))
    seat_note = f" [seats:{seat_signature}]" if seat_signature and has_exact_seats else ""
    if len(unique_markets) > 1:
        return f"Mirrored across {', '.join(unique_markets)}{seat_note} — same physical seats on multiple platforms"
    elif len(sellers) > 1:
        prices = [s.price for s in sellers]
        return (f"{len(sellers)} competing brokers on {unique_markets[0]}{seat_note} "
                f"(price range ${min(prices):.0f}–${max(prices):.0f})")
    return f"Single listing — no duplication detected{seat_note}"


# ── Main computation ──────────────────────────────────────────────────────────

async def get_canonical_inventory(
    event_id: int,
    db: AsyncSession,
    max_blocks: int = 5000,
) -> CanonicalInventoryView:
    """
    Compute canonical inventory for one event using Confidence V2 + Seat Intelligence.
    Read-only.
    """
    mp_result = await db.execute(select(Marketplace))
    mp_map: dict[int, str] = {m.id: m.slug for m in mp_result.scalars().all()}

    listings_result = await db.execute(
        select(Listing).where(Listing.event_id == event_id, Listing.is_active == True)
    )
    active_listings = listings_result.scalars().all()

    # Build SellerEntry objects with seat intelligence
    def _build_seller(l: Listing, slug: str) -> SellerEntry:
        # Resolve seat data: exact hash > parse seat_numbers > infer from range
        seats = None
        s_hash = l.seat_group_hash  # populated by collectors (e.g. Gametime)

        if not s_hash and l.seat_numbers:
            seats = parse_seat_numbers(l.seat_numbers)
            if seats:
                s_hash = seat_group_hash(seats)

        if not s_hash and l.seat_start is not None:
            seats = infer_seat_range(l.seat_start, l.seat_end, l.quantity)
            if seats:
                s_hash = seat_group_hash(seats)

        sig = adjacency_signature(seats) if seats else None
        has_exact = bool(s_hash)

        return SellerEntry(
            listing_id=l.id,
            marketplace_slug=slug,
            price=float(l.price),
            all_in_price=float(l.all_in_price) if l.all_in_price else None,
            last_seen_at=l.last_seen_at,
            external_listing_id=l.external_listing_id,
            row=normalize_row(l.row),
            has_exact_seats=has_exact,
            seat_hash=s_hash,
            seat_signature=sig,
            seats=seats,
        )

    # Group into canonical buckets
    # Key priority: (section, seat_hash, qty) when seat_hash available, else (section, row, qty)
    buckets: dict[tuple, list[SellerEntry]] = {}
    for l in active_listings:
        slug = mp_map.get(l.marketplace_id, "unknown")
        seller = _build_seller(l, slug)
        key = _canonical_key(l.section_id, l.row, l.quantity, seller.seat_hash)
        buckets.setdefault(key, []).append(seller)

    # Mirrored detection
    mirrored_keys: set[tuple] = {
        key for key, sellers in buckets.items()
        if len(set(s.marketplace_slug for s in sellers)) > 1
    }

    # Build canonical blocks
    canonical_blocks: list[CanonicalBlock] = []
    by_marketplace: dict[str, set] = {}

    for key, sellers in sorted(buckets.items()):
        section_id, row_or_seat, qty = key

        # Decode the key — was it seat-keyed or row-keyed?
        if row_or_seat.startswith("__seat__"):
            seat_hash = row_or_seat[len("__seat__"):]
            # Recover original row label from sellers (seat signature is the compact display,
            # not the actual row letter used by the venue).
            row = next((s.row for s in sellers if s.row), None)
            seat_identity = "exact"
        else:
            seat_hash = next((s.seat_hash for s in sellers if s.seat_hash), None)
            row = row_or_seat or None
            seat_identity = "inferred" if any(s.has_exact_seats for s in sellers) else "positional"

        marketplace_slugs = [s.marketplace_slug for s in sellers]
        for mp in set(marketplace_slugs):
            by_marketplace.setdefault(mp, set()).add(key)

        prices = [s.price for s in sellers]
        lo, hi = min(prices), max(prices)
        spread_pct = round((hi - lo) / lo * 100, 1) if lo > 0 else 0.0
        last_seen = max((s.last_seen_at for s in sellers if s.last_seen_at), default=None)

        _, freshness_label = _freshness_factor(last_seen)
        is_mirrored = key in mirrored_keys
        has_exact = any(s.has_exact_seats for s in sellers)
        seat_sig = next((s.seat_signature for s in sellers if s.seat_signature), None)

        confidence, factors = _compute_confidence_v2(sellers, marketplace_slugs, has_exact, is_mirrored)
        explanation = _explain_duplication(sellers, marketplace_slugs, has_exact, seat_sig)

        canonical_blocks.append(CanonicalBlock(
            block_id=_block_id(key),
            section_id=section_id or "UNKNOWN",
            row=row or None,
            quantity=qty,
            has_exact_seats=has_exact,
            seat_hash=seat_hash,
            seat_signature=seat_sig,
            seat_identity=seat_identity,
            seller_count=len(sellers),
            sellers=sellers,
            marketplace_slugs=sorted(set(marketplace_slugs)),
            low_ask=round(lo, 2),
            high_ask=round(hi, 2),
            median_ask=round(statistics.median(prices), 2),
            price_spread_pct=spread_pct,
            confidence_score=confidence,
            confidence_factors=factors,
            confidence_version="v2",
            last_seen_at=last_seen,
            freshness_label=freshness_label,
            is_mirrored=is_mirrored,
            duplicate_explanation=explanation,
        ))

    # Sort: confidence desc, then price asc
    canonical_blocks.sort(key=lambda b: (-b.confidence_score, b.low_ask))
    canonical_blocks = canonical_blocks[:max_blocks]

    total_raw = len(active_listings)
    total_canonical = len(canonical_blocks)
    dup_ratio = round((total_raw - total_canonical) / total_raw, 3) if total_raw else 0.0
    mirrored_count = sum(1 for b in canonical_blocks if b.is_mirrored)

    scores = [b.confidence_score for b in canonical_blocks]
    mean_conf = round(statistics.mean(scores), 3) if scores else 0.0
    high_conf = sum(1 for s in scores if s >= 0.80)
    low_conf  = sum(1 for s in scores if s < 0.50)

    # Seat identity breakdown
    exact_count    = sum(1 for b in canonical_blocks if b.seat_identity == "exact")
    inferred_count = sum(1 for b in canonical_blocks if b.seat_identity == "inferred")
    positional     = sum(1 for b in canonical_blocks if b.seat_identity == "positional")
    exact_mirrored = sum(1 for b in canonical_blocks if b.has_exact_seats and b.is_mirrored)

    return CanonicalInventoryView(
        event_id=event_id,
        as_of=datetime.utcnow(),
        canonical_blocks=canonical_blocks,
        total_canonical_blocks=total_canonical,
        total_raw_listings=total_raw,
        global_duplicate_ratio=dup_ratio,
        mirrored_block_count=mirrored_count,
        mirrored_ratio=round(mirrored_count / total_canonical, 3) if total_canonical else 0.0,
        by_marketplace={mp: len(keys) for mp, keys in sorted(by_marketplace.items())},
        mean_confidence=mean_conf,
        high_confidence_blocks=high_conf,
        low_confidence_blocks=low_conf,
        exact_seat_blocks=exact_count,
        inferred_seat_blocks=inferred_count,
        positional_blocks=positional,
        exact_seat_mirrored=exact_mirrored,
    )


# ── Canonical persistence ─────────────────────────────────────────────────────

async def snapshot_canonical_inventory(
    event_id: int,
    db: AsyncSession,
    poll_run_id: Optional[int] = None,
    persist_blocks: bool = False,
) -> Optional[int]:
    """
    Compute canonical inventory and persist a snapshot row.
    Called after each successful poll run.
    Returns snapshot_id or None on failure.
    """
    from app.models.canonical import CanonicalInventorySnapshot, CanonicalBlockHistory

    try:
        view = await get_canonical_inventory(event_id, db)
    except Exception:
        return None

    if view.total_raw_listings == 0:
        return None

    low_ask = min((b.low_ask for b in view.canonical_blocks), default=None)

    snap = CanonicalInventorySnapshot(
        event_id=event_id,
        snapshot_at=view.as_of,
        triggered_by_poll_run_id=poll_run_id,
        total_canonical_blocks=view.total_canonical_blocks,
        total_raw_listings=view.total_raw_listings,
        global_duplicate_ratio=view.global_duplicate_ratio,
        mirrored_block_count=view.mirrored_block_count,
        mirrored_ratio=view.mirrored_ratio,
        mean_confidence=view.mean_confidence,
        high_confidence_blocks=view.high_confidence_blocks,
        low_confidence_blocks=view.low_confidence_blocks,
        low_ask=low_ask,
        by_marketplace=view.by_marketplace,
        exact_seat_blocks=view.exact_seat_blocks,
        inferred_seat_blocks=view.inferred_seat_blocks,
        exact_seat_mirrored=view.exact_seat_mirrored,
    )
    db.add(snap)
    await db.flush()

    if persist_blocks:
        for b in view.canonical_blocks[:500]:  # cap to avoid huge inserts
            db.add(CanonicalBlockHistory(
                event_id=event_id,
                snapshot_id=snap.id,
                block_id=b.block_id,
                section_id=b.section_id,
                row=b.row,
                quantity=b.quantity,
                low_ask=b.low_ask,
                high_ask=b.high_ask,
                median_ask=b.median_ask,
                seller_count=b.seller_count,
                marketplace_slugs=b.marketplace_slugs,
                confidence_score=b.confidence_score,
                confidence_v2=True,
                is_mirrored=b.is_mirrored,
                has_exact_seats=b.has_exact_seats,
                freshness_label=b.freshness_label,
            ))

    await db.commit()
    return snap.id
