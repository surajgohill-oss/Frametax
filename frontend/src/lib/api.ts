import type {
  EventsListResponse,
  RawEvent,
  HeroResponse,
  MarketResponse,
  HistoryResponse,
  HistoryWindow,
  SectionsResponse,
  SellerResponse,
  EventMeta,
  VenueIntelligenceResponse,
  VenueClassificationsResponse,
  BaselineResponse,
  Listing,
  EventSnapshotResponse,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "https://backend-production-509f.up.railway.app";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  events: {
    list: () => get<EventsListResponse>("/api/intelligence/events"),
    all: () => get<RawEvent[]>("/api/events/"),
    meta: (id: number) => get<EventMeta>(`/api/events/${id}`),
    hero: (id: number) => get<HeroResponse>(`/api/intelligence/events/${id}/hero`),
    market: (id: number) => get<MarketResponse>(`/api/intelligence/events/${id}/market`),
    history: (id: number, window: HistoryWindow = "7d") =>
      get<HistoryResponse>(`/api/intelligence/events/${id}/history?window=${window}&metric=price`),
    sections: (id: number) => get<SectionsResponse>(`/api/intelligence/events/${id}/sections`),
    seller: (id: number) => get<SellerResponse>(`/api/intelligence/events/${id}/seller`),
    snapshot: (id: number) => get<EventSnapshotResponse>(`/api/intelligence/events/${id}/snapshot`),
    listings: (id: number, limit = 8) => get<Listing[]>(`/api/listings/events/${id}?limit=${limit}&sort=price`),
    create: (body: { stubhub_url?: string; seatgeek_url?: string; title?: string; venue?: string; event_date?: string }) =>
      fetch(`${BASE}/api/events/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        cache: "no-store",
      }).then((r) => r.json()),
    addTracked: (eventId: number, body: { marketplace_slug: string; external_url: string }) =>
      fetch(`${BASE}/api/events/${eventId}/tracked`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        cache: "no-store",
      }).then((r) => r.json()),
  },
  analytics: {
    baseline: (id: number) => get<BaselineResponse>(`/api/analytics/events/${id}/baseline`),
  },
  venues: {
    intelligence: (slug: string, eventId: number) =>
      get<VenueIntelligenceResponse>(`/api/venues/${slug}/intelligence?event_id=${eventId}`),
    classifications: (slug: string, eventId: number) =>
      get<VenueClassificationsResponse>(`/api/venues/${slug}/classifications?event_id=${eventId}`),
    compute: (slug: string, eventId: number): Promise<{ sections_computed: number }> =>
      fetch(`${BASE}/api/venues/${slug}/compute?event_id=${eventId}`, {
        method: "POST",
        cache: "no-store",
      }).then((r) => r.json()),
    seedFromListings: (slug: string, eventId: number): Promise<{ sections_seeded: number }> =>
      fetch(`${BASE}/api/venues/${slug}/seed-from-listings?event_id=${eventId}`, {
        method: "POST",
        cache: "no-store",
      }).then((r) => r.json()),
    seedFromCatalog: (slug: string): Promise<{ sections_seeded: number }> =>
      fetch(`${BASE}/api/venues/${slug}/seed-from-catalog`, {
        method: "POST",
        cache: "no-store",
      }).then((r) => r.json()),
  },
};
