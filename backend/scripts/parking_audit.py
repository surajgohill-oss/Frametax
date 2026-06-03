"""
Parking Audit — Production DB
==============================
Answers all 7 questions from the parking audit request.
Read-only. No data modifications.
"""

import psycopg2
import psycopg2.extras

DB_URL = (
    "postgresql://postgres:jOhylgsBSCdUhFXUChzNfkEvBAmuGsIP"
    "@switchback.proxy.rlwy.net:43266/railway"
)

# Postgres regex patterns matching the Python parking filter
PARKING_WHERE = r"""
    (
        l.section ~* '\mparking\M'
     OR l.section ~* '\mgarage\M'
     OR l.section ~* '\btailgate\b'
     OR l.section ~* '\bpass\s+only\b'
     OR l.section ~* '\blot\s*[A-Z0-9]+'
     OR l.section ~* '\b(blue|green|orange|brown|red|yellow|gold|purple|white|black|silver|gray|grey|flower|retail)\s+(zone\s+)?lot\b'
     OR (l.row IS NOT NULL AND upper(l.row) ~ '^PRK')
    )
"""


def main():
    conn = psycopg2.connect(DB_URL)
    conn.set_session(readonly=True, autocommit=True)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    print("=" * 70)
    print("PARKING AUDIT — PRODUCTION DB")
    print("=" * 70)

    # ── Q7: How many active parking listings by marketplace ───────────────
    print("\n[Q7] Active parking listings by marketplace")
    cur.execute(f"""
        SELECT
            m.slug                              AS marketplace,
            COUNT(*)                            AS parking_count,
            MIN(l.price)                        AS min_price,
            MAX(l.price)                        AS max_price,
            MIN(l.first_seen_at)                AS earliest_first_seen,
            MAX(l.first_seen_at)                AS latest_first_seen,
            MAX(l.last_seen_at)                 AS latest_last_seen
        FROM listings l
        JOIN marketplaces m ON l.marketplace_id = m.id
        WHERE l.is_active = true
          AND {PARKING_WHERE}
        GROUP BY m.slug
        ORDER BY parking_count DESC
    """)
    parking_rows = cur.fetchall()
    if parking_rows:
        for r in parking_rows:
            print(f"  {r['marketplace']:12s}: {r['parking_count']:5d} active parking listings")
            print(f"    price range:       ${r['min_price']} – ${r['max_price']}")
            print(f"    earliest ingested: {r['earliest_first_seen']}")
            print(f"    latest ingested:   {r['latest_first_seen']}")
            print(f"    latest refreshed:  {r['latest_last_seen']}")
    else:
        print("  NONE — no active parking listings found")

    # ── Total active listings context ─────────────────────────────────────
    print("\n[Context] Total active listings by marketplace")
    cur.execute("""
        SELECT m.slug, COUNT(*) AS total
        FROM listings l JOIN marketplaces m ON l.marketplace_id = m.id
        WHERE l.is_active = true
        GROUP BY m.slug ORDER BY total DESC
    """)
    totals = {r['slug']: r['total'] for r in cur.fetchall()}
    for slug, total in totals.items():
        parking = next((r['parking_count'] for r in parking_rows if r['marketplace'] == slug), 0)
        pct = 100 * parking / total if total > 0 else 0
        print(f"  {slug:12s}: {total:6d} total  {parking:4d} parking ({pct:.1f}%)")

    # ── Parking by event+marketplace ──────────────────────────────────────
    print("\n[Detail] Active parking count by event + marketplace")
    cur.execute(f"""
        SELECT
            e.id            AS event_id,
            e.title         AS event_title,
            m.slug          AS marketplace,
            COUNT(*)        AS parking_count,
            MIN(l.price)    AS min_price,
            MAX(l.price)    AS max_price
        FROM listings l
        JOIN marketplaces m ON l.marketplace_id = m.id
        JOIN events e ON l.event_id = e.id
        WHERE l.is_active = true
          AND {PARKING_WHERE}
        GROUP BY e.id, e.title, m.slug
        ORDER BY parking_count DESC
    """)
    for r in cur.fetchall():
        print(f"  event={r['event_id']:2d} {r['marketplace']:10s} count={r['parking_count']:4d} "
              f"price=${r['min_price']}–${r['max_price']}  {r['event_title'][:45]}")

    # ── Examples: sample parking listings ────────────────────────────────
    print("\n[Examples] Sample active parking listings (up to 20)")
    cur.execute(f"""
        SELECT
            l.id,
            e.id            AS event_id,
            e.title         AS event_title,
            m.slug          AS marketplace,
            l.section,
            l.row,
            l.quantity,
            l.price,
            l.external_listing_id,
            l.first_seen_at,
            l.last_seen_at
        FROM listings l
        JOIN marketplaces m ON l.marketplace_id = m.id
        JOIN events e ON l.event_id = e.id
        WHERE l.is_active = true
          AND {PARKING_WHERE}
        ORDER BY l.price ASC
        LIMIT 20
    """)
    examples = cur.fetchall()
    for r in examples:
        print(f"  [{r['marketplace']:10s}] event={r['event_id']:2d}  section={r['section']!r:35s}  "
              f"row={r['row']!r:12s}  qty={r['quantity']}  ${r['price']}  "
              f"ext={r['external_listing_id']}")

    # ── Distinct parking section names across all marketplaces ────────────
    print("\n[Sections] Distinct parking section names in active listings")
    cur.execute(f"""
        SELECT DISTINCT m.slug AS marketplace, l.section, COUNT(*) AS n
        FROM listings l
        JOIN marketplaces m ON l.marketplace_id = m.id
        WHERE l.is_active = true
          AND {PARKING_WHERE}
        GROUP BY m.slug, l.section
        ORDER BY m.slug, n DESC
    """)
    for r in cur.fetchall():
        print(f"  {r['marketplace']:12s}: section={r['section']!r:40s} count={r['n']}")

    # ── Distinct parking row names across all marketplaces ────────────────
    print("\n[Rows] Distinct parking row names (where row is set)")
    cur.execute(f"""
        SELECT DISTINCT m.slug AS marketplace, l.row, COUNT(*) AS n
        FROM listings l
        JOIN marketplaces m ON l.marketplace_id = m.id
        WHERE l.is_active = true
          AND {PARKING_WHERE}
          AND l.row IS NOT NULL AND l.row != ''
        GROUP BY m.slug, l.row
        ORDER BY m.slug, n DESC
        LIMIT 40
    """)
    for r in cur.fetchall():
        print(f"  {r['marketplace']:12s}: row={r['row']!r:25s} count={r['n']}")

    # ── Parking listings ingested AFTER 2026-05-31 (filter implementation date) ──
    print("\n[Timing] Parking listings first seen AFTER 2026-05-31 (filter live date)")
    cur.execute(f"""
        SELECT m.slug, COUNT(*) AS post_filter_count,
               MIN(l.first_seen_at) AS earliest
        FROM listings l
        JOIN marketplaces m ON l.marketplace_id = m.id
        WHERE l.is_active = true
          AND {PARKING_WHERE}
          AND l.first_seen_at >= '2026-05-31'
        GROUP BY m.slug
        ORDER BY post_filter_count DESC
    """)
    post_filter = cur.fetchall()
    if post_filter:
        for r in post_filter:
            print(f"  {r['slug']:12s}: {r['post_filter_count']} listings ingested after filter date  (earliest {r['earliest']})")
    else:
        print("  None — all parking listings predate 2026-05-31")

    cur.execute(f"""
        SELECT m.slug, COUNT(*) AS pre_filter_count
        FROM listings l
        JOIN marketplaces m ON l.marketplace_id = m.id
        WHERE l.is_active = true
          AND {PARKING_WHERE}
          AND (l.first_seen_at < '2026-05-31' OR l.first_seen_at IS NULL)
        GROUP BY m.slug
    """)
    pre_filter = cur.fetchall()
    if pre_filter:
        for r in pre_filter:
            print(f"  {r['slug']:12s}: {r['pre_filter_count']} legacy parking listings (before 2026-05-31)")

    # ── Non-TickPick section names that look parking-adjacent ─────────────
    print("\n[Non-TickPick] Any section names on StubHub/Gametime/SeatGeek that contain 'lot', 'parking', etc.")
    cur.execute("""
        SELECT DISTINCT m.slug, l.section, COUNT(*) AS n
        FROM listings l
        JOIN marketplaces m ON l.marketplace_id = m.id
        WHERE l.is_active = true
          AND m.slug != 'tickpick'
          AND (
              l.section ~* '\mparking\M'
           OR l.section ~* '\mgarage\M'
           OR l.section ~* '\blot\s*[A-Z0-9]+'
           OR l.section ~* '\btailgate\b'
          )
        GROUP BY m.slug, l.section
        ORDER BY m.slug, n DESC
        LIMIT 30
    """)
    non_tp = cur.fetchall()
    if non_tp:
        for r in non_tp:
            print(f"  {r['slug']:12s}: section={r['section']!r:40s} count={r['n']}")
    else:
        print("  NONE — no parking-pattern sections on StubHub, Gametime, or SeatGeek")

    print(f"\n{'='*70}")
    print("AUDIT COMPLETE")
    print(f"{'='*70}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
