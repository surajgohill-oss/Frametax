export type Signal =
  | "deepening"
  | "loosening"
  | "stable"
  | "capitulating"
  | "mixed"
  | "tightening"
  | "unknown";

// ── /api/intelligence/events ──────────────────────────────────────────────────
export interface EventSummary {
  event_id: number;
  title: string;
  artist?: string | null;
  venue_name?: string | null;
  venue_slug?: string | null;
  custom_artwork_url?: string | null;
  event_date?: string | null;
  signal: Signal;
  opportunity_score: number;
  price: {
    low_ask: number | null;
    median_ask: number | null;
    high_ask: number | null;
  };
  changes?: {
    h24?: {
      price_delta?: number | null;
      price_delta_pct?: number | null;
      inventory_delta?: number | null;
    };
    first_tracked?: {
      first_median?: number | null;
      price_delta_pct?: number | null;
    } | null;
  };
  inventory: {
    total_listings: number;
    fresh_total_listings?: number;
    total_tickets: number;
  };
  marketplace_prices?: Record<string, number>;
  history_hours?: number | null;
}

export interface EventsListResponse {
  event_count: number;
  events: EventSummary[];
}

// ── /api/events/{id} ──────────────────────────────────────────────────────────
export interface MarketplaceFreshness {
  freshness_status: "fresh" | "late" | "stale" | "dead";
  last_success_at: string | null;
  age_minutes: number | null;
  consecutive_failures: number;
}

export interface TrackedEventEntry {
  marketplace_slug: string;
  external_url: string | null;
  freshness_status: "fresh" | "late" | "stale" | "dead";
  last_success_at: string | null;
  is_active: boolean;
}

export interface EventMeta {
  id: number;
  title: string;
  artist?: string;
  venue_name?: string;
  venue?: string;
  venue_slug?: string;
  event_date?: string;
  performers?: string;
  created_at?: string;
  custom_artwork_url?: string | null;
  // marketplace data from backend
  marketplace_prices?: Record<string, number | null>;
  all_marketplace_prices?: Record<string, number | null>;
  marketplace_freshness?: Record<string, MarketplaceFreshness>;
  tracked_events?: TrackedEventEntry[];
  lowest_price?: number | null;
}

// ── /api/analytics/events/{id}/baseline ──────────────────────────────────────
export interface MarketplaceBaseline {
  marketplace_slug: string;
  current_listings: number;
  current_lowest_ask: number | null;
  listings_change_24h: { absolute: number | null; pct: number | null; reason: string | null };
  listings_change_7d:  { absolute: number | null; pct: number | null; reason: string | null };
}

export interface BaselineResponse {
  event_id: number;
  history_depth_days: number;
  current: {
    snapshot_at: string;
    raw_listings: number;
    lowest_ask: number | null;
  } | null;
  deltas_24h: {
    low_ask: { absolute: number | null; pct: number | null; reason: string | null };
    raw_listings: { absolute: number | null; pct: number | null; reason: string | null };
  } | null;
  deltas_7d: {
    low_ask: { absolute: number | null; pct: number | null; reason: string | null };
    raw_listings: { absolute: number | null; pct: number | null; reason: string | null };
  } | null;
  per_marketplace: MarketplaceBaseline[];
}

// ── /api/analytics/events/{id}/marketplace-baselines ────────────────────────
export interface MarketplaceFirstTracked {
  marketplace_slug: string;
  first_tracked_at: string | null;
  first_raw_listings: number;
  first_tickets: number;
  current_raw_listings: number;
  current_tickets: number;
  delta_listings: number;
  delta_tickets: number;
  delta_listings_pct: number | null;
}

export interface MarketplaceBaselinesResponse {
  event_id: number;
  unit: string;
  per_marketplace: MarketplaceFirstTracked[];
  event_first_tracked_at: string | null;
  event_baseline_total_listings: number;
  event_baseline_total_tickets: number;
  current_total_listings: number;
  current_total_tickets: number;
  inv_since_tracking: number | null;
  tickets_since_tracking: number | null;
}

// ── /api/events/{id}/alerts ──────────────────────────────────────────────────
export interface AlertRecord {
  type: string;
  severity: "RED" | "YELLOW";
  marketplace: string | null;
  message: string;
}

export interface AlertResponse {
  event_id: number;
  alert_count: number;
  has_critical: boolean;
  alerts: AlertRecord[];
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
    fresh_total_listings?: number;
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

// ── /api/events/ (raw list) ───────────────────────────────────────────────────
export interface RawEvent {
  id: number;
  title: string;
  stubhub_url?: string | null;
  artist?: string;
  venue_name?: string;
  venue_slug?: string;
  event_date: string;
  is_active: boolean;
  lowest_price?: number | null;
  historical_lowest_price?: number | null;
  total_listings?: number;
  fresh_total_listings?: number;
  marketplace_prices?: Record<string, number | null>;
  all_marketplace_prices?: Record<string, number | null>;
  tracked_events?: TrackedEventEntry[];
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
  by_marketplace: { marketplace: string; new_24h: number; removed_24h: number; net_24h: number; poll_count_24h: number }[];
  largest_price_drops: { listing_id?: number; marketplace?: string; section?: string; row?: string; current_price?: number; first_price_24h?: number; old_price?: number; new_price?: number; delta: number; delta_pct?: number }[];
  largest_price_gains: { listing_id?: number; marketplace?: string; section?: string; row?: string; current_price?: number; first_price_24h?: number; old_price?: number; new_price?: number; delta: number; delta_pct?: number }[];
  aggressive_sections: { section: string; score: number }[];
}

// ── /api/listings/events/{id} ─────────────────────────────────────────────────
export interface Listing {
  id: number;
  external_listing_id: string;
  section: string | null;
  section_name: string | null;
  row: string | null;
  quantity: number;
  price: number;
  price_each: number;
  fees: number | null;
  all_in_price: number | null;
  marketplace_slug: string;
  is_active: boolean;
  listing_url: string | null;
}

// ── /api/analytics/events/{id}/velocity-windows ───────────────────────────────
export interface VelocityWindow {
  window_start: string | null;
  window_end: string | null;
  implied_sale_listings: number;
  implied_sale_tickets: number;
  avg_implied_sale_price: number | null;
  appeared_listings: number;
}

export interface VelocityWindowsResponse {
  event_id: number;
  event_date: string | null;
  computed_at: string;
  note: string;
  windows: {
    since_tracking?: VelocityWindow;
    "7d"?: VelocityWindow;
    "24h"?: VelocityWindow;
    "48h"?: VelocityWindow;
    "6h"?: VelocityWindow;
    "1h"?: VelocityWindow;
  };
}

// ── /api/intelligence/events/{id}/snapshot ────────────────────────────────────
export interface MarketplaceTrend {
  floor_now: number | null;
  floor_change: number | null;
  floor_change_pct: number | null;
  median_now: number | null;
  median_change: number | null;
  listings_now: number | null;
  listings_change: number | null;
  window_hours: number | null;
}

export interface EventSnapshotResponse {
  event_id: number;
  computed_at: string | null;
  hours_of_data: number | null;
  data_note: string | null;
  price: {
    floor_now: number | null;
    floor_24h_change: number | null;
    floor_7d_change: number | null;
    median_now: number | null;
    median_24h_change: number | null;
    median_24h_change_pct: number | null;
    median_7d_change: number | null;
    median_7d_change_pct: number | null;
    high_now: number | null;
    high_24h_change: number | null;
    high_7d_change: number | null;
    high_start: number | null;
    high_start_change: number | null;
    high_start_change_pct: number | null;
  };
  duplicates?: {
    dup_pct: number | null;
    dup_pct_reliable?: boolean;
    dup_mirror_pct: number | null;
    raw_listings: number | null;
    canonical_blocks: number | null;
    per_marketplace?: Record<string, number>;
    per_marketplace_low_confidence?: string[];
    note: string;
  };
  inventory: {
    inventory_now: number | null;
    inventory_24h_change: number | null;
    inventory_7d_change: number | null;
  };
  velocity: {
    inventory_removed_24h: number | null;
    inventory_added_24h: number | null;
    net_inventory_change: number | null;
  };
  marketplace: {
    marketplace_leading_price_drop: string | null;
    marketplace_leading_inventory_loss: string | null;
    marketplace_lowest_floor: string | null;
  };
  classification: string | null;
  classification_confidence: number | null;
  per_marketplace_trends: Record<string, MarketplaceTrend>;
}
