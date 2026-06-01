/**
 * Domain types for the Ticket App frontend.
 *
 * These types enforce strict separation between:
 *   - Event (canonical, rendered as cards)
 *   - TrackedEvent (marketplace relation, NEVER rendered as a card)
 *   - Listing (price row, nested inside event detail only)
 *   - UIEvent (projection layer for rendering)
 *
 * INVARIANT: Only Event[] may be passed to event card components.
 * TrackedEvent[] must never flow into a component that renders event cards.
 */

/** Freshness status for a single (marketplace, event) pair. */
export type FreshnessStatus = "fresh" | "late" | "stale" | "dead";

export interface MarketplaceFreshness {
  freshness_status: FreshnessStatus;
  last_success_at: string | null;
  age_minutes: number | null;
  consecutive_failures: number;
  stale_reason: string | null;
  expected_interval_minutes: number;
}

/** A marketplace tracking relation embedded inside an Event API response. */
export interface TrackedEvent {
  id: number;
  marketplace_slug: string;
  external_event_id: string | null;
  external_url: string;
  is_active: boolean;
  poll_interval_minutes: number;
  last_polled_at: string | null;
  next_poll_at: string | null;
  // Freshness fields (injected by backend)
  freshness_status?: FreshnessStatus;
  last_success_at?: string | null;
  age_minutes?: number | null;
  consecutive_failures?: number;
  stale_reason?: string | null;
  expected_interval_minutes?: number;
}

/** A canonical event as returned by GET /api/events/. */
export interface Event {
  id: number;
  canonical_id: string;
  title: string;
  artist: string | null;
  venue_id: number;
  venue_name: string | null;
  venue_slug: string | null;
  event_date: string;
  is_active: boolean;
  stubhub_url: string | null;
  seatgeek_url: string | null;
  /** Fresh/late price floor for StubHub (null when stale — not current market truth). */
  lowest_ask_stubhub: number | null;
  /** Fresh/late price floor for SeatGeek (null when stale — not current market truth). */
  lowest_ask_seatgeek: number | null;
  /** Current market floor — fresh/late marketplaces only. */
  lowest_price: number | null;
  /** Historical floor including stale data (display reference only, NOT market truth). */
  historical_lowest_price: number | null;
  /** All active listings count (stale-inclusive, for marketplace breakdown). */
  total_listings: number | null;
  /** Fresh+late listings count (for current summary display). */
  fresh_total_listings: number | null;
  /** Fresh/late marketplace prices only (current market truth). */
  marketplace_prices: Record<string, number> | null;
  /** All marketplace prices including stale (for breakdown display). */
  all_marketplace_prices: Record<string, number> | null;
  /** Per-marketplace freshness classification. */
  marketplace_freshness: Record<string, MarketplaceFreshness> | null;
  next_poll_at: string | null;
  created_at: string | null;
  /** Marketplace tracking relations. Present on the API object but MUST NOT be
   *  iterated as events. Use api.listings.byEvent() for listing data. */
  tracked_events: TrackedEvent[];
}

/** A single ticket listing as returned by GET /api/listings/events/{id}. */
export interface Listing {
  id: number;
  external_listing_id: string;
  section: string | null;
  section_name: string;
  section_id: string | null;
  row: string | null;
  quantity: number;
  price: number;
  price_each: number;
  fees: number | null;
  all_in_price: number | null;
  listing_url: string | null;
  marketplace_slug: string;
  market_segment: string | null;
  is_active: boolean;
  first_seen_at: string | null;
  last_seen_at: string | null;
}

/** Opaque brand: only Event[] may flow into event-card render paths.
 *  Deliberately excludes tracked_events so the compiler rejects any attempt
 *  to pass a TrackedEvent where an EventCardInput is expected. */
export type EventCardInput = Pick<
  Event,
  "id" | "canonical_id" | "title" | "artist" | "venue_name" | "venue_slug"
  | "event_date" | "lowest_ask_stubhub" | "lowest_ask_seatgeek" | "is_active"
  | "total_listings" | "lowest_price"
>;

export type EventState = "POPULATED" | "PARTIAL" | "EMPTY" | "BLOCKED";

/** Derives a display state from event data returned by the API. */
export function deriveEventState(event: Pick<Event, "is_active" | "total_listings" | "lowest_ask_stubhub" | "lowest_ask_seatgeek">): EventState {
  if (!event.is_active) return "BLOCKED";
  const count = event.total_listings ?? 0;
  if (count === 0) return "EMPTY";
  const hasStubhub = event.lowest_ask_stubhub != null;
  const hasSeatgeek = event.lowest_ask_seatgeek != null;
  if (hasStubhub && hasSeatgeek) return "POPULATED";
  return "PARTIAL";
}

// ── Runtime guards ────────────────────────────────────────────────────────────

/** Throws if `value` is not a plain object with the minimum fields of an Event.
 *  Use at API response boundaries to catch shape regressions early. */
export function assertIsEvent(value: unknown): asserts value is Event {
  if (
    typeof value !== "object" ||
    value === null ||
    typeof (value as Record<string, unknown>).id !== "number" ||
    typeof (value as Record<string, unknown>).canonical_id !== "string" ||
    typeof (value as Record<string, unknown>).title !== "string"
  ) {
    throw new Error(
      `STATE_INTEGRITY_VIOLATION: value is not a canonical Event — got ${JSON.stringify(value)}`
    );
  }
}

/** Asserts that the rendered event count equals the API-returned count.
 *  Call after sectionize() to guarantee no cards were added or dropped. */
export function assertEventCardinality(
  apiCount: number,
  renderedCount: number
): void {
  if (renderedCount !== apiCount) {
    throw new Error(
      `STATE_INTEGRITY_VIOLATION: UI event cardinality (${renderedCount}) ` +
      `does not match API event count (${apiCount}). ` +
      `A merge, fallback, or flatMap path introduced extra events.`
    );
  }
}
