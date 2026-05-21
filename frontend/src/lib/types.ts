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
  lowest_ask_stubhub: number | null;
  lowest_ask_seatgeek: number | null;
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

/** Opaque brand: only Event[] may flow into event-card render paths. */
export type EventCardInput = Pick<
  Event,
  "id" | "canonical_id" | "title" | "artist" | "venue_name" | "venue_slug"
  | "event_date" | "lowest_ask_stubhub" | "lowest_ask_seatgeek" | "is_active"
>;
