export type Signal =
  | "deepening"
  | "loosening"
  | "stable"
  | "capitulating"
  | "mixed";

// ── /api/intelligence/events ──────────────────────────────────────────────────
export interface EventSummary {
  event_id: number;
  title: string;
  signal: Signal;
  opportunity_score: number;
  price: {
    low_ask: number | null;
    median_ask: number | null;
    high_ask: number | null;
  };
  inventory: {
    total_listings: number;
    total_tickets: number;
  };
}

export interface EventsListResponse {
  event_count: number;
  events: EventSummary[];
}

// ── /api/events/{id} ──────────────────────────────────────────────────────────
export interface EventMeta {
  id: number;
  title: string;
  artist?: string;
  venue_name?: string;
  venue?: string;
  venue_slug?: string;
  event_date?: string;
  performers?: string;
}

// ── /api/intelligence/events/{id}/hero ────────────────────────────────────────
export interface HeroResponse {
  event_id: number;
  signal: Signal;
  opportunity_score: number;
  days_until_event: number | null;
  price: {
    low_ask: number | null;
    median_ask: number | null;
    high_ask: number | null;
    p25_ask: number | null;
    p75_ask: number | null;
  };
  changes: {
    h24?: { price_delta?: number | null; price_delta_pct: number | null; inventory_delta: number | null };
    d7?: { price_delta?: number | null; price_delta_pct: number | null; inventory_delta: number | null };
    d14?: { price_delta?: number | null; price_delta_pct: number | null; inventory_delta: number | null };
    d30?: { price_delta?: number | null; price_delta_pct: number | null; inventory_delta: number | null };
  };
  inventory: {
    total_listings: number;
    total_tickets: number;
  };
  market: {
    tightness: number | null;
    seller_aggression: number | null;
    seller_confidence: number | null;
    capitulation_score: number | null;
    velocity: number | null;
  };
  rates: {
    reprice_rate: number | null;
    churn_rate: number | null;
    listing_survival?: number | null;
  };
  history_context?: {
    hours_available: number | null;
    data_note: string | null;
  };
}

// ── /api/intelligence/events/{id}/market ─────────────────────────────────────
export interface MarketplaceBreakdown {
  name: string;
  low_ask: number | null;
  median_ask: number | null;
  high_ask: number | null;
  listings: number;
  tickets: number;
  share_of_inventory: number | null;
  liquidity_score: number | null;
}

export interface MarketResponse {
  marketplaces: MarketplaceBreakdown[];
  spreads: Record<string, number | null>;
  trends: {
    price_trend: string | null;
    inventory_trend: string | null;
    signal: Signal | null;
    velocity: number | null;
    price_change_24h_pct: number | null;
  };
  inventory_movement: {
    new_24h: number | null;
    removed_24h: number | null;
    net_change_24h: number | null;
  };
  market_stress: {
    composite_score: number | null;
    tightness: number | null;
    capitulation: number | null;
  };
  price_distribution: {
    p10: number | null;
    p25: number | null;
    p50: number | null;
    p75: number | null;
    p90: number | null;
  };
}

// ── /api/intelligence/events/{id}/history ─────────────────────────────────────
export interface HistoryPoint {
  ts: string;
  low_ask: number | null;
  median_ask: number | null;
  high_ask: number | null;
  p25_ask: number | null;
  p75_ask: number | null;
  listings: number | null;
  tickets: number | null;
}

export type HistoryWindow = "24h" | "7d" | "14d" | "30d" | "all";

export interface HistoryResponse {
  series: HistoryPoint[];
  source: "live" | "archive_aggregate" | "combined";
  oldest_timestamp: string | null;
  newest_timestamp: string | null;
  data_depth_days: number | null;
  archive_bucket_count: number;
  point_count: number;
  window_start: string | null;
  window_end: string | null;
  bucket_size: string | null;
}

// ── /api/intelligence/events/{id}/sections ────────────────────────────────────
export interface SectionRow {
  section_id: number | null;
  display_name: string;
  tier: string | null;
  listings: number;
  tickets: number;
  low_ask: number | null;
  median_ask: number | null;
  high_ask: number | null;
  price_range: number | null;
  value_score: number | null;
  activity_score: number | null;
}

export interface SectionsResponse {
  sections: SectionRow[];
}

// ── /api/events/{id} (extended) ──────────────────────────────────────────────
// venue_slug is returned by the backend and used to route to the correct venue UI

// ── /api/venues/{slug}/intelligence?event_id=N ────────────────────────────────
export interface VenueSectionMetrics {
  computed_at: string;
  low_ask: number | null;
  median_ask: number | null;
  high_ask: number | null;
  p25_ask: number | null;
  p75_ask: number | null;
  listing_count: number | null;
  ticket_count: number | null;
  inventory_delta_24h: number | null;
  price_delta_24h: number | null;
  price_delta_pct_24h: number | null;
  deal_score: number | null;
  demand_score: number | null;
  seller_pressure: number | null;
  value_score: number | null;
  price_vs_tier_median: number | null;
  price_vs_venue_median: number | null;
}

export interface VenueSection {
  section_id: string;
  display_name: string;
  tier: string | null;
  level: string | null;
  zone: string | null;
  side: string | null;
  is_premium: boolean;
  quality_score: number | null;
  future_map_key: string | null;
  metrics: VenueSectionMetrics | null;
}

export interface VenueIntelligenceResponse {
  venue_slug: string;
  event_id: number;
  sections_total: number;
  sections_with_metrics: number;
  sections: VenueSection[];
}

export interface ClassificationEntry {
  section_id: string;
  display_name: string;
  tier: string | null;
  quality_score: number | null;
  median_ask: number | null;
  deal_score: number | null;
  demand_score: number | null;
  value_score: number | null;
  seller_pressure: number | null;
  price_vs_tier_median: number | null;
  inventory: number | null;
}

export interface VenueClassificationsResponse {
  venue_slug: string;
  event_id: number;
  classifications: {
    best_value: ClassificationEntry[];
    highest_demand: ClassificationEntry[];
    fastest_price_drops: ClassificationEntry[];
    inventory_building: ClassificationEntry[];
    inventory_depleting: ClassificationEntry[];
    most_active: ClassificationEntry[];
  };
}

// ── /api/intelligence/events/{id}/seller ──────────────────────────────────────
export interface SellerResponse {
  new_listings_24h: number | null;
  removed_listings_24h: number | null;
  repriced_24h: number | null;
  price_drops_24h: number | null;
  price_gains_24h: number | null;
  median_reprice_delta: number | null;
  seller_aggression: number | null;
  seller_confidence: number | null;
  capitulation_score: number | null;
  reprice_rate: number | null;
  churn_rate: number | null;
  listing_survival: number | null;
  by_marketplace: { name: string; repriced: number; drops: number; gains: number }[];
  largest_price_drops: { section: string; old_price: number; new_price: number; delta: number }[];
  largest_price_gains: { section: string; old_price: number; new_price: number; delta: number }[];
  aggressive_sections: { section: string; score: number }[];
}
