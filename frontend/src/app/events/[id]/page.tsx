'use client';
import { useParams, useRouter } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { fmt$, fmtDate, fmtRelative } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EntityLogo } from '@/components/ui/EntityLogo';
import { getEntityImage } from '@/lib/entityImages';
import VenueHeatmap from '@/components/venue/VenueHeatmap';
import PriceHistoryChart from '@/components/charts/PriceHistoryChart';
import SectionPriceBar from '@/components/charts/SectionPriceBar';
import InventoryChart from '@/components/charts/InventoryChart';
import { useFollowed } from '@/hooks/useFollowed';
import { useMyEvents } from '@/hooks/useMyEvents';
import { useHiddenEvents } from '@/hooks/useHiddenEvents';
import { Star, Bell, BellOff, EyeOff, Eye, PowerOff, Power } from 'lucide-react';
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';

// ── Entity theming (mirrors dashboard) ───────────────────────────────────────

function getEventEntityTheme(title: string) {
  const n = (title || '').toLowerCase();
  const isNFL = /49ers|rams|chargers|raiders|chiefs|cowboys|eagles|packers|bears|seahawks|broncos|steelers/.test(n);
  const isMLB = /rangers|angels|dodgers|giants|padres|yankees|cubs|red sox|astros|braves/.test(n);
  const isNBA = /lakers|clippers|warriors|celtics|heat|bulls|nets|knicks/.test(n);
  if (isNFL)  return { accent: '#E50914', accentRgb: '229,9,20',    gradFrom: '#2A0000', gradMid: '#180000' };
  if (isMLB)  return { accent: '#F97316', accentRgb: '249,115,22',  gradFrom: '#1A0E00', gradMid: '#100800' };
  if (isNBA)  return { accent: '#3B82F6', accentRgb: '59,130,246',  gradFrom: '#00101A', gradMid: '#000A12' };
  return               { accent: '#E50914', accentRgb: '229,9,20',   gradFrom: '#2A0000', gradMid: '#160000' };
}

// ── Inventory Accounting types ────────────────────────────────────────────────

interface MarketplaceAccounting {
  marketplace_slug: string;
  raw_rows: number;
  active_rows: number;
  stale_rows: number;
  reactivated_rows: number;
  estimated_ticket_count: number;
  deduplicated_rows: number;
  dedup_ticket_count: number;
  duplicate_ratio: number;
  low_ask: number | null;
  median_ask: number | null;
  health_flags: string[];
}

interface CrossMarketReconciliation {
  marketplace_slugs: string[];
  total_unique_seat_blocks: number;
  mirrored_blocks: number;
  mirrored_ratio: number;
  only_on: Record<string, number>;
}

interface InventorySanity {
  venue_capacity: number | null;
  estimated_ticket_count: number;
  cross_market_unique_blocks: number;
  capacity_ratio: number | null;
  flags: string[];
}

interface InventoryAccounting {
  event_id: number;
  per_marketplace: MarketplaceAccounting[];
  cross_market: CrossMarketReconciliation;
  sanity: InventorySanity;
}

const MARKETPLACES = [
  { slug: 'stubhub',    label: 'StubHub',     color: 'indigo' },
  { slug: 'tickpick',   label: 'TickPick',    color: 'green'  },
  { slug: 'gametime',   label: 'Gametime',    color: 'orange' },
  { slug: 'vividseats', label: 'Vivid Seats', color: 'pink'   },
] as const;

type MarketplaceSlug = 'stubhub' | 'tickpick' | 'gametime' | 'vividseats';

const MP_BADGE: Record<string, 'indigo' | 'blue' | 'green' | 'orange' | 'default'> = {
  stubhub:    'indigo',
  tickpick:   'green',
  gametime:   'orange',
  vividseats: 'blue',
};

interface PollRun {
  id: number;
  tracked_event_id: number;
  started_at: string;
  completed_at: string | null;
  listings_found: number;
  new_listings: number;
  reactivated_listings: number;
  disappeared_listings: number;
  status: string;
  error_message: string | null;
}

const MP_COLORS: Record<string, string> = {
  stubhub:    'text-indigo-400',
  tickpick:   'text-green-400',
  gametime:   'text-orange-400',
  vividseats: 'text-pink-400',
};

// ── Helper utilities ──────────────────────────────────────────────────────────

function daysUntil(iso: string): number {
  const diff = new Date(iso).getTime() - Date.now();
  return Math.ceil(diff / 86_400_000);
}

interface MarketStatus { label: string; cssClass: string; }
function getMarketStatus(price: number | null): MarketStatus {
  if (!price) return { label: '—', cssClass: 'status-value' };
  if (price < 60)  return { label: 'Value',   cssClass: 'status-value'   };
  if (price < 150) return { label: 'Active',  cssClass: 'status-active'  };
  if (price < 300) return { label: 'Hot',     cssClass: 'status-hot'     };
  return              { label: 'Premium', cssClass: 'status-premium' };
}

// ── Key art URL helpers ───────────────────────────────────────────────────────

/** Build Ticketmaster CDN artwork URL when external_event_id looks like a TM numeric ID. */
function getTmArtworkUrl(extId: string | null | undefined): string | null {
  if (!extId) return null;
  // TM IDs are typically numeric strings like "Z7r9jZ1AdeXvk"  or pure numeric "59007A0"
  // Use the standard TM image endpoint pattern
  const clean = String(extId).trim();
  if (clean.length < 4) return null;
  return `https://s1.ticketmaster.com/dbimages/arena/events/${clean}.jpg`;
}

/** Return the best available artwork URL for an event, or null if none. */
function getEventArtworkUrl(event: any): string | null {
  return event?.image_url || event?.poster_url || getTmArtworkUrl(event?.external_event_id) || null;
}

// ── Section 1: Editorial Split Hero ──────────────────────────────────────────

function EventHero({
  event,
  lowestAsk,
  totalListings,
  canonicalCount,
  mirrorRate,
  baseline,
  invSummary,
  onPoll,
  pollLoading,
  onBack,
}: {
  event: any;
  lowestAsk: number | null;
  totalListings: number;
  canonicalCount: number;
  mirrorRate?: number | null;
  baseline?: any;
  invSummary?: any;
  onPoll: () => void;
  pollLoading: boolean;
  onBack: () => void;
}) {
  const [artErr, setArtErr] = useState(false);
  const ms = getMarketStatus(lowestAsk);
  const title = event.title || '';
  const initial = (event.artist || title || '?')[0].toUpperCase();
  const isCompleted = event.status === 'completed' || event.status === 'archived';
  const days = event.event_date ? daysUntil(event.event_date) : null;
  const theme = getEventEntityTheme(title);
  const imgCfg = getEntityImage(title);
  const accent = imgCfg.accent ?? theme.accent;
  const accentRgb = theme.accentRgb;

  // Key art fallback chain: event.image_url → event.poster_url → TM CDN → entity logo → null
  const artworkUrl = artErr ? null : getEventArtworkUrl(event);
  const entityLogoUrl = !artworkUrl ? (imgCfg.logo ?? null) : null;

  const venueName = event.venue_slug
    ? event.venue_slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())
    : null;
  const venueInitial = venueName ? venueName[0].toUpperCase() : 'V';

  // Derive category chip label
  const catLabel = (() => {
    const n = title.toLowerCase();
    if (/49ers|rams|chargers|raiders|chiefs|cowboys|eagles|packers|bears|seahawks|broncos|steelers/.test(n)) return 'NFL';
    if (/rangers|angels|dodgers|giants|padres|yankees|cubs|red sox|astros|braves/.test(n)) return 'MLB';
    if (/lakers|clippers|warriors|celtics|heat|bulls|nets|knicks/.test(n)) return 'NBA';
    return 'Live Event';
  })();

  // Value signal
  const isValue = lowestAsk != null && lowestAsk < 100;
  const isHot   = lowestAsk != null && lowestAsk >= 100 && lowestAsk < 160;

  // Ticket-centric hero metrics derived from baseline + invSummary (no new API calls)
  const bCur   = baseline?.current;
  const bD7    = baseline?.deltas_7d;
  const curAsk     = lowestAsk             ?? bCur?.lowest_ask;
  const askDelta   = bD7?.low_ask?.absolute ?? null;
  const askPct     = bD7?.low_ask?.pct      ?? null;
  const origAsk    = (curAsk != null && askDelta != null) ? curAsk - askDelta : null;

  const curTickets  = invSummary?.unique_tickets_available ?? bCur?.unique_tickets ?? null;
  const tickDelta   = bD7?.unique_tickets?.absolute ?? null;
  const tickPct     = bD7?.unique_tickets?.pct      ?? null;
  const origTickets = (curTickets != null && tickDelta != null) ? curTickets - tickDelta : null;

  const depth = baseline?.history_depth_days ?? 0;
  const histLow = event?.historical_lowest_price ?? null;

  return (
    <div className="relative overflow-hidden" style={{ background: '#06000A' }}>
      {/* ── Breadcrumb topnav ──────────────────────────────────────────────── */}
      <div className="relative z-20 max-w-6xl mx-auto px-6 pt-5 pb-0">
        <div className="flex items-center gap-2 text-[11px] text-gray-700">
          <button
            onClick={onBack}
            className="flex items-center gap-1 hover:text-gray-400 transition-colors font-medium"
          >
            ← Back
          </button>
          <span className="text-gray-800">·</span>
          <span className="text-gray-700">My Events</span>
          <span className="text-gray-800">·</span>
          <span className="text-gray-600 truncate max-w-xs">{title || 'Event'}</span>
        </div>
      </div>

      {/* ── Editorial Split grid ───────────────────────────────────────────── */}
      <div
        className="relative"
        style={{
          display: 'grid',
          gridTemplateColumns: '1.25fr 1fr',
          minHeight: '420px',
        }}
      >
        {/* ── LEFT: Visual Atmosphere Panel ──────────────────────────────── */}
        <div className="relative overflow-hidden" style={{
          background: `linear-gradient(145deg, ${theme.gradFrom}FF 0%, ${theme.gradMid}F0 45%, rgba(8,2,14,1) 100%)`,
        }}>
          {/* Triple radial atmospheric glows */}
          <div className="absolute inset-0 pointer-events-none" style={{ background: `
            radial-gradient(ellipse 70% 90% at 15% 60%, rgba(${accentRgb},0.30) 0%, transparent 55%),
            radial-gradient(ellipse 50% 65% at 85% 15%, rgba(${accentRgb},0.14) 0%, transparent 50%),
            radial-gradient(ellipse 40% 50% at 50% 100%, rgba(${accentRgb},0.10) 0%, transparent 45%)
          ` }} />

          {/* Animated breathing orb */}
          <div
            className="atmosphere-orb absolute rounded-full pointer-events-none"
            style={{
              width: 500,
              height: 500,
              top: '-20%',
              left: '-10%',
              background: `radial-gradient(circle, rgba(${accentRgb},0.13) 0%, transparent 70%)`,
            }}
          />

          {/* Dot grid texture */}
          <div className="absolute inset-0 opacity-[0.045] pointer-events-none" style={{
            backgroundImage: `radial-gradient(circle, ${accent} 1px, transparent 1px)`,
            backgroundSize: '28px 28px',
          }} />

          {/* Key art image (when available) or entity logo or watermark initial */}
          {artworkUrl ? (
            <div className="absolute inset-0 flex items-center justify-end pointer-events-none select-none" aria-hidden>
              <div className="absolute inset-0" style={{
                background: 'linear-gradient(to right, rgba(6,0,10,0.92) 0%, rgba(6,0,10,0.5) 40%, rgba(6,0,10,0.15) 80%)',
              }} />
              <img
                src={artworkUrl}
                alt={title}
                onError={() => setArtErr(true)}
                style={{
                  position: 'absolute', inset: 0, width: '100%', height: '100%',
                  objectFit: 'cover', objectPosition: 'center top',
                  opacity: 0.55, filter: 'saturate(1.15) brightness(0.85)',
                }}
              />
            </div>
          ) : entityLogoUrl ? (
            <div className="absolute inset-0 flex items-center justify-end pr-8 pointer-events-none select-none" aria-hidden>
              <div className="absolute inset-0" style={{
                background: 'linear-gradient(to right, rgba(6,0,10,0.95) 0%, rgba(6,0,10,0.4) 50%, transparent 80%)',
              }} />
              <img
                src={entityLogoUrl}
                alt={title}
                style={{ width: '44%', height: '80%', objectFit: 'contain', objectPosition: 'center right', opacity: 0.65,
                  filter: 'drop-shadow(0 0 40px rgba(0,0,0,0.7))', position: 'relative', zIndex: 1 }}
              />
            </div>
          ) : (
            /* Watermark letter fallback */
            <div
              className="absolute inset-0 flex items-center justify-end pr-6 select-none pointer-events-none"
              aria-hidden
            >
              <span className="font-black" style={{
                fontSize: '280px',
                lineHeight: 1,
                color: `rgba(${accentRgb}, 0.10)`,
                WebkitTextStrokeWidth: '1px',
                WebkitTextStrokeColor: `rgba(${accentRgb}, 0.16)`,
                fontFamily: 'system-ui, -apple-system, sans-serif',
                letterSpacing: '-0.06em',
              }}>
                {initial}
              </span>
            </div>
          )}

          {/* Right edge fade into data panel */}
          <div
            className="absolute top-0 right-0 bottom-0 w-24 pointer-events-none"
            style={{ background: 'linear-gradient(to right, transparent, #06000A)' }}
          />

          {/* Content: logo top-left, title + chips bottom */}
          <div className="relative z-10 flex flex-col justify-between h-full p-7" style={{ minHeight: 420 }}>
            {/* Entity logo — top left */}
            <div>
              <EntityLogo
                entity={title}
                initial={initial}
                accent={accent}
                gradFrom={theme.gradFrom}
                gradMid={theme.gradMid}
                size={64}
              />
            </div>

            {/* Title + category chips — bottom */}
            <div>
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                <span
                  className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider"
                  style={{
                    background: `rgba(${accentRgb}, 0.12)`,
                    border: `1px solid rgba(${accentRgb}, 0.25)`,
                    color: accent,
                  }}
                >
                  {catLabel}
                </span>
                <span
                  className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider"
                  style={{
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    color: 'rgba(255,255,255,0.4)',
                  }}
                >
                  ◈ Event Intelligence
                </span>
              </div>
              <h1
                className="text-3xl sm:text-4xl font-black text-white leading-tight"
                style={{ letterSpacing: '-0.025em', textShadow: `0 2px 24px rgba(${accentRgb},0.3)` }}
              >
                {title || 'Unnamed Event'}
              </h1>
            </div>
          </div>

          {/* Bottom fade to background */}
          <div
            className="absolute bottom-0 left-0 right-0 h-12 pointer-events-none"
            style={{ background: 'linear-gradient(transparent, #06000A)' }}
          />
        </div>

        {/* ── RIGHT: Venue Card + Metrics Panel ──────────────────────────── */}
        <div
          className="relative flex flex-col"
          style={{
            background: 'rgba(6,0,10,0.97)',
            borderLeft: '1px solid rgba(255,255,255,0.05)',
          }}
        >
          {/* Subtle top accent line */}
          <div
            className="absolute top-0 left-0 right-0 h-[1px]"
            style={{ background: `linear-gradient(to right, transparent, rgba(${accentRgb},0.35), transparent)` }}
          />

          {/* ── VENUE CARD ────────────────────────────────────────────────── */}
          <div
            className="relative overflow-hidden flex-shrink-0"
            style={{
              minHeight: 190,
              background: `linear-gradient(145deg, rgba(${accentRgb},0.07) 0%, rgba(6,0,10,0.5) 100%)`,
              borderBottom: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            <div className="absolute inset-0 pointer-events-none" style={{
              background: `radial-gradient(ellipse 80% 80% at 15% 85%, rgba(${accentRgb},0.11) 0%, transparent 60%)`,
            }} />
            <div className="absolute right-4 top-0 bottom-0 flex items-center pointer-events-none select-none" aria-hidden>
              <span style={{
                fontSize: '130px', fontWeight: 900, lineHeight: 1,
                color: `rgba(${accentRgb},0.06)`,
                WebkitTextStrokeWidth: '1px',
                WebkitTextStrokeColor: `rgba(${accentRgb},0.10)`,
                letterSpacing: '-0.06em',
              }}>{venueInitial}</span>
            </div>
            <div className="relative z-10 p-6 flex flex-col justify-between" style={{ minHeight: 190 }}>
              <div>
                <div className="text-[9px] font-bold uppercase tracking-widest mb-2.5" style={{ color: `rgba(${accentRgb},0.45)` }}>
                  📍 Venue
                </div>
                <div className="font-black text-white leading-tight mb-1"
                  style={{ fontSize: venueName && venueName.length > 22 ? '17px' : '21px', letterSpacing: '-0.025em' }}>
                  {venueName || 'Venue TBD'}
                </div>
                {event.city && (
                  <div className="text-sm font-medium mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
                    {event.city}
                  </div>
                )}
              </div>
              {event.event_date && (
                <div className="mt-4">
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold"
                    style={{ background: `rgba(${accentRgb},0.1)`, border: `1px solid rgba(${accentRgb},0.2)`, color: accent }}>
                    {fmtDate(event.event_date)}
                    {days != null && days > 0 && <span className="opacity-60">· {days}d away</span>}
                    {days === 0 && <span className="opacity-60">· Today</span>}
                  </div>
                  {isCompleted && (
                    <span className="ml-2 text-[10px] px-2 py-1 rounded font-bold"
                      style={{ background: 'rgba(255,255,255,0.04)', color: '#6B7280' }}>
                      {event.status === 'archived' ? '🗄 Archived' : '✓ Past'}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* ── METRICS (compact grid) + CTAs ─────────────────────────────── */}
          <div className="flex flex-col flex-1 p-5 gap-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl p-3.5" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div className="text-[9px] font-bold uppercase tracking-widest text-gray-600 mb-1.5">Floor Ask</div>
                <div className="font-black text-white leading-none tabular-nums" style={{ fontSize: '26px', letterSpacing: '-0.04em' }}>
                  {curAsk != null ? fmt$(curAsk) : '—'}
                </div>
                {askPct != null && askPct !== 0 && (
                  <div className="text-[10px] font-bold mt-1 tabular-nums" style={{ color: askPct < 0 ? '#22c55e' : '#EF4444' }}>
                    {askPct > 0 ? '+' : ''}{askPct.toFixed(1)}% 7d
                  </div>
                )}
                {isValue && <div className="text-[9px] text-green-400 mt-0.5">↑ Value signal</div>}
              </div>
              <div className="rounded-xl p-3.5" style={{ background: 'rgba(167,139,250,0.05)', border: '1px solid rgba(167,139,250,0.14)' }}>
                <div className="text-[9px] font-bold uppercase tracking-widest text-gray-600 mb-1.5">Net Tickets</div>
                <div className="font-black leading-none tabular-nums" style={{ fontSize: '26px', letterSpacing: '-0.04em', color: '#A78BFA' }}>
                  {curTickets != null ? curTickets.toLocaleString() : '—'}
                </div>
                {tickPct != null && tickPct !== 0 && (
                  <div className="text-[10px] font-bold mt-1 tabular-nums" style={{ color: tickPct < 0 ? '#22c55e' : '#F59E0B' }}>
                    {tickPct > 0 ? '+' : ''}{tickPct.toFixed(1)}% 7d
                  </div>
                )}
                {depth > 0 && !tickPct && <div className="text-[9px] text-gray-700 mt-0.5">{depth}d window</div>}
              </div>
            </div>

          <div className="flex flex-col gap-5">

            {/* Spacer — category label */}
            <div className="flex items-center gap-1.5">
              <span className="text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded"
                style={{ background: `rgba(${accentRgb},0.1)`, color: accent }}>{catLabel}</span>
              {histLow != null && (
                <span className="text-[9px] text-amber-500 font-mono">All-time low: {fmt$(histLow)}</span>
              )}
            </div>

          </div>

          {/* ── CTAs + last updated ──────────────────────────────────────── */}
          <div className="flex flex-col gap-2 mt-auto">
            {!isCompleted && (
              <button
                onClick={onPoll}
                disabled={pollLoading}
                className="w-full py-2.5 rounded-xl text-sm font-bold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                style={{
                  background: pollLoading ? `rgba(${accentRgb},0.3)` : `rgba(${accentRgb},0.85)`,
                  color: 'white',
                  border: `1px solid rgba(${accentRgb},0.4)`,
                }}
              >
                {pollLoading ? '⟳  Refreshing...' : '↻  Refresh Now'}
              </button>
            )}
            {event.last_polled_at && (
              <div className="text-[10px] text-gray-700 text-center">
                Last updated {fmtRelative(event.last_polled_at)} ago
              </div>
            )}
          </div>
          </div>{/* end flex-col flex-1 p-5 */}
        </div>
      </div>

      {/* Bottom fade to content */}
      <div
        className="absolute bottom-0 left-0 right-0 h-10 pointer-events-none"
        style={{ background: 'linear-gradient(transparent, #06000A)' }}
      />
    </div>
  );
}

// ── Market Movement Section ───────────────────────────────────────────────────
// Primary story: original → current change in price + tickets.
// No new API calls — derives from already-loaded event + baseline.

type MovWindow = 'last_poll' | '24h' | '7d' | 'all';
const MOV_WINDOWS: { key: MovWindow; label: string }[] = [
  { key: 'last_poll', label: 'Last Poll' },
  { key: '24h',       label: '24h' },
  { key: '7d',        label: '7d' },
  { key: 'all',       label: 'All Time' },
];

function MarketMovementSection({ event, baseline, invSummary }: {
  event: any; baseline: any | null; invSummary: any | null;
}) {
  const [window_, setWindow] = useState<MovWindow>('7d');

  const f$   = (v: number) => `$${Math.round(v).toLocaleString()}`;
  const fmtD = (iso: string) => new Date(iso).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });

  const trackingStarted = event?.created_at ? fmtD(event.created_at) : null;
  const histLow         = event?.historical_lowest_price ?? null;
  const cur             = baseline?.current;
  const depth           = baseline?.history_depth_days ?? 0;

  // Pick deltas for selected window
  const deltas = window_ === '24h' ? baseline?.deltas_24h
               : window_ === '7d'  ? baseline?.deltas_7d
               : null; // last_poll and all handled specially

  const curTickets  = invSummary?.unique_tickets_available ?? cur?.unique_tickets ?? null;
  const liveAsk = invSummary?.per_marketplace?.length
    ? Math.min(...invSummary.per_marketplace
        .map((m: any) => m.normalized_lowest_ask)
        .filter((v: any) => v != null && v > 0))
    : null;
  const curAsk = (liveAsk != null && isFinite(liveAsk) ? liveAsk : null) ?? cur?.lowest_ask ?? null;

  // Delta values for chosen window
  const tickDelta   = deltas?.unique_tickets?.absolute ?? null;
  const tickPct     = deltas?.unique_tickets?.pct      ?? null;
  const askDelta    = deltas?.low_ask?.absolute ?? null;
  const askPct      = deltas?.low_ask?.pct      ?? null;

  // For "All Time" window: use histLow as original ask
  const askPctAll = (window_ === 'all' && histLow != null && curAsk != null && histLow > 0)
    ? ((curAsk - histLow) / histLow) * 100 : null;

  const displayAskPct     = window_ === 'all' ? askPctAll : askPct;
  const displayAskOrig    = window_ === 'all' ? histLow   : (curAsk != null && askDelta != null ? curAsk - askDelta : null);
  const displayTickOrig   = curTickets != null && tickDelta != null ? curTickets - tickDelta : null;
  const displayTickPct    = tickPct;

  if (!trackingStarted && curTickets == null && curAsk == null) return null;

  function MovementBlock({ label, origVal, curVal, pct, curColor, invertPct = false }: {
    label: string; origVal: string | null; curVal: string | null;
    pct: number | null; curColor: string; invertPct?: boolean;
  }) {
    const pctPositive = pct != null && (invertPct ? pct < 0 : pct > 0);
    const pctColor = pct == null || pct === 0 ? '#4B5563'
      : pctPositive ? '#22c55e' : '#EF4444';
    return (
      <div className="flex-1 rounded-xl p-4" style={{ background:'rgba(255,255,255,0.025)', border:'1px solid rgba(255,255,255,0.06)' }}>
        <div className="text-[9px] font-bold uppercase tracking-widest text-gray-600 mb-3">{label}</div>
        <div className="flex items-end gap-3 flex-wrap">
          {origVal && (
            <div>
              <div className="text-[9px] text-gray-700 uppercase tracking-wider mb-0.5">Original</div>
              <div className="text-lg font-bold text-gray-600 tabular-nums leading-none">{origVal}</div>
            </div>
          )}
          {origVal && <span className="text-gray-700 text-xs mb-0.5">→</span>}
          <div>
            {origVal && <div className="text-[9px] text-gray-700 uppercase tracking-wider mb-0.5">Now</div>}
            <div className="tabular-nums leading-none font-black" style={{ fontSize:'28px', color: curColor, letterSpacing:'-0.03em' }}>
              {curVal ?? '—'}
            </div>
          </div>
          {pct != null && pct !== 0 && (
            <div className="mb-0.5">
              <div className="text-[9px] text-gray-700 uppercase tracking-wider mb-0.5">Change</div>
              <div className="text-sm font-bold tabular-nums" style={{ color: pctColor }}>
                {pct > 0 ? '+' : ''}{pct.toFixed(1)}%
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Window selector tabs */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {MOV_WINDOWS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setWindow(key)}
            className="px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
            style={window_ === key
              ? { background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.18)', color: '#fff' }
              : { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', color: '#4B5563' }
            }
          >
            {label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-3 text-[10px]">
          {trackingStarted && (
            <span className="text-gray-700">Since {trackingStarted}</span>
          )}
          {depth > 0 && (
            <span className="text-gray-700">{depth}d history</span>
          )}
          {histLow != null && (
            <span className="text-amber-500 font-mono font-semibold">All-time low: {f$(histLow)}</span>
          )}
        </div>
      </div>

      {/* Movement blocks */}
      <div className="flex gap-3 flex-wrap sm:flex-nowrap">
        <MovementBlock
          label={`Floor Ask${window_ === 'all' ? ' vs All-time Low' : window_ === 'last_poll' ? '' : ` (${window_})`}`}
          origVal={displayAskOrig != null ? f$(displayAskOrig) : null}
          curVal={curAsk != null ? f$(curAsk) : null}
          pct={displayAskPct}
          curColor="#fff"
          invertPct
        />
        <MovementBlock
          label={`Net Tickets${window_ === 'last_poll' ? '' : ` (${window_})`}`}
          origVal={displayTickOrig != null ? displayTickOrig.toLocaleString() : null}
          curVal={curTickets != null ? curTickets.toLocaleString() : null}
          pct={displayTickPct}
          curColor="#A78BFA"
          invertPct
        />
      </div>

      {window_ === 'last_poll' && (
        <p className="text-[10px] text-gray-600 italic px-1">Last Poll: showing current values — per-poll delta not available in snapshot data.</p>
      )}
      {depth === 0 && window_ !== 'last_poll' && (
        <p className="text-[10px] text-gray-700 italic px-1">Snapshot window not yet available — movement data will appear after the next poll run.</p>
      )}
    </div>
  );
}

// ── Market Baseline Section ───────────────────────────────────────────────────
// Source: /api/analytics/events/{id}/baseline  (canonical_inventory_snapshots)
// Read-only. No predictions. No buy/wait signals.

function MarketBaselineSection({ baseline }: { baseline: any }) {
  if (!baseline) return null;
  const cur = baseline.current;
  if (!cur) return null;

  const depth = baseline.history_depth_days ?? 0;
  const snapshotAt = cur.snapshot_at
    ? new Date(cur.snapshot_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    : null;

  function DeltaChip({ delta, unit = '' }: { delta: any; unit?: string }) {
    if (!delta || delta.reason) {
      return <span className="text-[10px] text-gray-600">—</span>;
    }
    const abs = delta.absolute;
    const pct = delta.pct;
    if (abs === null || abs === undefined) return <span className="text-[10px] text-gray-600">—</span>;
    const pos = abs > 0;
    const neg = abs < 0;
    const color = pos ? 'text-emerald-400' : neg ? 'text-red-400' : 'text-gray-500';
    const sign = pos ? '+' : '';
    const pctStr = pct != null ? ` (${pos ? '+' : ''}${pct.toFixed(1)}%)` : '';
    return (
      <span className={`text-[10px] font-mono tabular-nums ${color}`}>
        {sign}{typeof abs === 'number' ? (unit === '$' ? `$${Math.abs(abs).toFixed(2)}` : abs.toLocaleString()) : abs}{unit !== '$' ? unit : ''}{pctStr}
      </span>
    );
  }

  const rows = [
    {
      label: 'Listings',
      current: cur.raw_listings?.toLocaleString() ?? '—',
      d24: baseline.deltas_24h?.raw_listings,
      d7d: baseline.deltas_7d?.raw_listings,
      unit: '',
    },
    {
      label: 'Unique Tickets',
      current: cur.unique_tickets?.toLocaleString() ?? '—',
      d24: baseline.deltas_24h?.unique_tickets,
      d7d: baseline.deltas_7d?.unique_tickets,
      unit: '',
    },
    {
      label: 'Lowest Ask',
      current: cur.lowest_ask != null ? `$${cur.lowest_ask.toFixed(2)}` : '—',
      d24: baseline.deltas_24h?.low_ask,
      d7d: baseline.deltas_7d?.low_ask,
      unit: '$',
    },
    {
      label: 'Mirror Rate',
      current: cur.mirror_rate != null ? `${(cur.mirror_rate * 100).toFixed(1)}%` : '—',
      d24: baseline.deltas_24h?.mirror_rate,
      d7d: baseline.deltas_7d?.mirror_rate,
      unit: '',
    },
  ];

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-widest">Historical Snapshot Trends</span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider"
            style={{ background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.18)', color: '#FCD34D' }}>
            Snapshot · Not Live
          </span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {snapshotAt && (
            <span className="text-[10px] text-amber-600/80 font-mono">as of {snapshotAt}</span>
          )}
          <span className="text-[10px] text-gray-600">{depth}d history</span>
        </div>
      </div>
      <div className="text-[10px] text-gray-700 mb-3">
        Stored snapshot data — values may lag live inventory by up to several hours. For current figures see Live Inventory above.
      </div>

      {/* Top-level trend table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-600 border-b border-white/5">
              <th className="text-left pb-1.5 pr-4 font-normal">Metric</th>
              <th className="text-right pb-1.5 pr-4 font-normal text-amber-700/70">Snapshot</th>
              <th className="text-right pb-1.5 pr-4 font-normal">24h Δ</th>
              <th className="text-right pb-1.5 font-normal">7d Δ</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(row => (
              <tr key={row.label} className="border-b border-white/[0.04] last:border-0">
                <td className="py-1.5 pr-4 text-gray-400">{row.label}</td>
                <td className="py-1.5 pr-4 text-right font-mono tabular-nums text-gray-200">{row.current}</td>
                <td className="py-1.5 pr-4 text-right"><DeltaChip delta={row.d24} unit={row.unit} /></td>
                <td className="py-1.5 text-right"><DeltaChip delta={row.d7d} unit={row.unit} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Per-marketplace breakdown (compact) */}
      {baseline.per_marketplace?.length > 0 && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <div className="text-[10px] text-gray-600 mb-2 uppercase tracking-widest">By Marketplace</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {baseline.per_marketplace.map((mp: any) => {
              const c24 = mp.listings_change_24h;
              const c7d = mp.listings_change_7d;
              const has24 = c24 && c24.reason === null && c24.absolute !== null;
              const has7d = c7d && c7d.reason === null && c7d.absolute !== null;
              return (
                <div key={mp.marketplace_slug} className="rounded-lg bg-white/[0.04] px-2.5 py-2">
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{mp.marketplace_slug}</div>
                  <div className="text-sm font-bold text-gray-200">{(mp.current_listings ?? 0).toLocaleString()}</div>
                  {mp.current_lowest_ask != null && (
                    <div className="text-[10px] text-gray-500">${mp.current_lowest_ask.toFixed(2)} ask</div>
                  )}
                  <div className="flex gap-2 mt-0.5">
                    {has24 && (
                      <span className={`text-[9px] font-mono tabular-nums ${c24.absolute > 0 ? 'text-emerald-400' : c24.absolute < 0 ? 'text-red-400' : 'text-gray-600'}`}>
                        {c24.absolute > 0 ? '+' : ''}{c24.absolute} 24h
                      </span>
                    )}
                    {has7d && (
                      <span className={`text-[9px] font-mono tabular-nums ${c7d.absolute > 0 ? 'text-emerald-400' : c7d.absolute < 0 ? 'text-red-400' : 'text-gray-600'}`}>
                        {c7d.absolute > 0 ? '+' : ''}{c7d.absolute} 7d
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-2 text-[9px] text-gray-700">
        Data source: canonical_inventory_snapshots · No predictions
      </div>
    </div>
  );
}

// ── Section 2: Market Overview ────────────────────────────────────────────────

type MpFilter = 'all' | 'stubhub' | 'tickpick' | 'gametime' | 'vividseats';

interface InvMovement {
  original_listings: number;
  current_listings: number;
  net_difference: number;
  normalized_blocks: number;
  duplicate_listings: number;
  website_comparable_count: number;
  total_relists: number;
  inferred_exits: number;
  likely_sold: number;
  low_ask: number | null;
  avg_ask: number | null;
  median_ask: number | null;
  high_ask: number | null;
  avg_ask_delta_pct: number | null;
  price_trend_pct: number | null;
  inventory_trend_pct: number | null;
  relist_rate_pct: number | null;
}

// Data source: invSummary.per_marketplace (Priority 1 — full DB count, not capped).
// inventory-movement and inventory-accounting endpoints do not exist in production (404).
// This component does NOT depend on those endpoints.
function MarketOverviewPanel({
  invSummary,
  canonical,
}: {
  invSummary: any;
  canonical: CanonicalInventory | null;
}) {
  const [mpFilter, setMpFilter] = useState<MpFilter>('all');

  const MP_TABS: { key: MpFilter; label: string; color: string }[] = [
    { key: 'all',        label: 'All Markets', color: 'text-white'      },
    { key: 'stubhub',    label: 'StubHub',     color: 'text-indigo-400' },
    { key: 'tickpick',   label: 'TickPick',    color: 'text-green-400'  },
    { key: 'gametime',   label: 'Gametime',    color: 'text-orange-400' },
    { key: 'vividseats', label: 'Vivid',       color: 'text-pink-400'   },
  ];

  const MP_META: Record<string, { label: string; dot: string; colorCls: string }> = {
    stubhub:    { label: 'StubHub',     dot: '#818CF8', colorCls: 'text-indigo-400' },
    tickpick:   { label: 'TickPick',    dot: '#4ADE80', colorCls: 'text-green-400'  },
    gametime:   { label: 'Gametime',    dot: '#FB923C', colorCls: 'text-orange-400' },
    vividseats: { label: 'Vivid Seats', dot: '#F472B6', colorCls: 'text-pink-400'   },
  };

  // Per-marketplace data from invSummary (Priority 1 source — full DB counts)
  const perMp: any[] = invSummary?.per_marketplace ?? [];
  const totalListings: number = invSummary?.raw_listings ?? 0;

  // For "all" view — aggregate across all marketplaces
  const allLowest = perMp.length > 0
    ? Math.min(...perMp.map((m: any) => m.normalized_lowest_ask ?? Infinity).filter(isFinite))
    : null;

  // For single-marketplace view
  const mpData = mpFilter !== 'all'
    ? perMp.find((m: any) => m.marketplace_slug === mpFilter) ?? null
    : null;

  const hasData = invSummary != null;

  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      {/* Tab bar */}
      <div className="flex items-center gap-1 px-5 pt-4 pb-3 border-b border-white/6">
        {MP_TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setMpFilter(t.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mpFilter === t.key
                ? `bg-white/10 ${t.color} border border-white/15`
                : 'text-gray-600 hover:text-gray-400 hover:bg-white/5'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Data grid */}
      <div className="p-5">
        {mpFilter === 'all' ? (
          /* ── ALL MARKETS view ─────────────────────────────────────────── */
          <div className="space-y-5">
            {/* Summary row — net tickets primary */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-1">Net Unique Tickets</div>
                <div className="text-xl font-bold text-violet-400 tabular-nums">
                  {invSummary?.unique_tickets_available != null ? invSummary.unique_tickets_available.toLocaleString() : '—'}
                </div>
                {invSummary?.raw_tickets != null && (
                  <div className="text-[10px] text-gray-700 mt-0.5 tabular-nums">
                    {invSummary.raw_tickets.toLocaleString()} gross
                  </div>
                )}
              </div>
              <div>
                <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-1">Lowest Ask</div>
                <div className="text-xl font-bold text-emerald-400">{allLowest != null && isFinite(allLowest) ? fmt$(allLowest) : '—'}</div>
              </div>
              <div>
                <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-1">Gross Listings</div>
                <div className="text-xl font-bold text-gray-400 tabular-nums">{hasData ? totalListings.toLocaleString() : '—'}</div>
                {invSummary?.mirror_rate != null && (
                  <div className="text-[10px] text-gray-700 mt-0.5">
                    {(invSummary.mirror_rate * 100).toFixed(1)}% mirror rate
                  </div>
                )}
              </div>
            </div>

            {/* Ticket reconciliation row — explains Unique Available vs gross marketplace totals */}
            {invSummary?.raw_tickets != null && invSummary?.unique_tickets_available != null && (
              <div
                className="rounded-xl px-4 py-3 flex items-center gap-4 text-xs flex-wrap"
                style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.12)' }}
              >
                <span className="text-gray-500 font-bold uppercase tracking-widest text-[9px] shrink-0">Ticket Reconciliation</span>
                <span className="flex items-center gap-1.5 text-gray-400">
                  <span className="font-mono font-bold text-white">{invSummary.raw_tickets.toLocaleString()}</span>
                  <span className="text-gray-600">gross marketplace tickets</span>
                </span>
                <span className="text-gray-700">−</span>
                <span className="flex items-center gap-1.5 text-gray-400">
                  <span className="font-mono font-bold text-amber-400">
                    {(invSummary.raw_tickets - invSummary.unique_tickets_available).toLocaleString()}
                  </span>
                  <span className="text-gray-600">mirror/duplicate deduction</span>
                </span>
                <span className="text-gray-700">=</span>
                <span className="flex items-center gap-1.5">
                  <span className="font-mono font-bold text-emerald-400">{invSummary.unique_tickets_available.toLocaleString()}</span>
                  <span className="text-gray-500">unique tickets available</span>
                </span>
                <span
                  className="ml-auto text-[9px] text-gray-600 hidden sm:block"
                  title="Each seat block listed on multiple platforms is counted once in the unique total"
                >
                  Same seats on multiple platforms → counted once
                </span>
              </div>
            )}

            {/* Per-marketplace breakdown table */}
            {perMp.length > 0 ? (
              <div className="space-y-2">
                <div className="flex items-center gap-4 mb-1">
                  <span className="text-[10px] font-bold text-gray-600 uppercase tracking-widest">By Marketplace</span>
                  <span className="ml-auto flex items-center gap-5 text-[9px] font-bold text-gray-700 uppercase tracking-wider pr-1">
                    <span className="w-20 text-right">Gross Listings</span>
                    <span className="w-20 text-right">Gross Tickets</span>
                    <span className="w-10 text-right">Share</span>
                    <span className="w-16 text-right">Low Ask</span>
                  </span>
                </div>
                <div className="space-y-1.5">
                  {['stubhub','tickpick','gametime','vividseats'].map(slug => {
                    const m = perMp.find((x: any) => x.marketplace_slug === slug);
                    const meta = MP_META[slug];
                    const count = m?.raw_listings ?? 0;
                    const tickets = m?.raw_tickets ?? 0;
                    const sharePct = totalListings > 0 ? (count / totalListings * 100) : 0;
                    return (
                      <div key={slug} className="flex items-center gap-3">
                        <span style={{ color: meta.dot }} className="text-[10px]">●</span>
                        <span className="text-sm text-gray-400 w-24">{meta.label}</span>
                        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${Math.min(sharePct, 100)}%`, backgroundColor: meta.dot, opacity: 0.7 }}
                          />
                        </div>
                        <span className={`text-sm font-semibold tabular-nums w-20 text-right ${meta.colorCls}`}>
                          {m ? count.toLocaleString() : '—'}
                        </span>
                        <span className="text-sm tabular-nums w-20 text-right text-gray-500">
                          {m && tickets > 0 ? tickets.toLocaleString() : '—'}
                        </span>
                        <span className="text-xs text-gray-600 w-10 text-right">
                          {m ? `${sharePct.toFixed(0)}%` : '—'}
                        </span>
                        <span className="text-sm font-semibold text-emerald-400 w-16 text-right tabular-nums">
                          {m?.normalized_lowest_ask != null ? fmt$(m.normalized_lowest_ask) : '—'}
                        </span>
                      </div>
                    );
                  })}
                  {/* Placeholders */}
                  {[
                    { slug: 'seatgeek', label: 'SeatGeek', badge: 'DEFERRED' },
                    { slug: 'ticketmaster', label: 'Ticketmaster', badge: 'PLANNED' },
                  ].map(p => (
                    <div key={p.slug} className="flex items-center gap-3 opacity-35">
                      <span className="text-[10px] text-gray-700">●</span>
                      <span className="text-sm text-gray-600 w-24">{p.label}</span>
                      <div className="flex-1 h-1 bg-white/5 rounded-full" />
                      <span className="text-xs text-gray-700 w-20 text-right">—</span>
                      <span className="text-xs text-gray-700 w-10 text-right">—</span>
                      <span className="text-[9px] text-gray-600 w-16 text-right font-mono">{p.badge}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : hasData ? (
              <div className="text-sm text-gray-600">No per-marketplace data available.</div>
            ) : (
              <div className="text-sm text-gray-600">Loading market data…</div>
            )}

            {/* Canonical inventory row if available */}
            {canonical && (
              <div className="pt-3 border-t border-white/5 grid grid-cols-3 gap-4">
                <div>
                  <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-1">Canonical Blocks</div>
                  <div className="text-base font-bold text-indigo-300">{canonical.total_canonical_blocks.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-1">Shared Blocks</div>
                  <div className="text-base font-semibold text-amber-400">{canonical.mirrored_block_count.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-1">Exclusive Blocks</div>
                  <div className="text-base font-semibold text-emerald-400">{(canonical.total_canonical_blocks - canonical.mirrored_block_count).toLocaleString()}</div>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* ── SINGLE MARKETPLACE view ──────────────────────────────────── */
          <div className="space-y-4">
            {mpData ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-3">Inventory</div>
                  <div className="space-y-2.5">
                    <div className="flex justify-between items-baseline">
                      <span className="text-sm text-gray-400">Listings</span>
                      <span className={`text-base font-bold tabular-nums ${MP_META[mpFilter]?.colorCls ?? 'text-white'}`}>
                        {mpData.raw_listings?.toLocaleString() ?? '—'}
                      </span>
                    </div>
                    <div className="flex justify-between items-baseline">
                      <span className="text-sm text-gray-400">Market Share</span>
                      <span className="text-sm font-semibold text-gray-300">
                        {totalListings > 0 && mpData.raw_listings != null
                          ? `${(mpData.raw_listings / totalListings * 100).toFixed(1)}%`
                          : '—'}
                      </span>
                    </div>
                    <div className="flex justify-between items-baseline">
                      <span className="text-sm text-gray-400">Status</span>
                      <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                        mpData.raw_listings > 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-gray-800 text-gray-500'
                      }`}>
                        {mpData.raw_listings > 0 ? 'LIVE' : 'EMPTY'}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-3">Pricing</div>
                  <div className="space-y-2.5">
                    <div className="flex justify-between items-baseline">
                      <span className="text-sm text-gray-400">Lowest Ask</span>
                      <span className="text-base font-bold text-emerald-400">
                        {mpData.normalized_lowest_ask != null ? fmt$(mpData.normalized_lowest_ask) : '—'}
                      </span>
                    </div>
                    <div className="flex justify-between items-baseline">
                      <span className="text-sm text-gray-400">Source</span>
                      <span className="text-xs text-gray-600">inventory-summary</span>
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-3">Cross-Market</div>
                  <div className="space-y-2.5">
                    <div className="flex justify-between items-baseline">
                      <span className="text-sm text-gray-400">All Markets Low</span>
                      <span className="text-sm font-semibold text-gray-300">
                        {allLowest != null && isFinite(allLowest) ? fmt$(allLowest) : '—'}
                      </span>
                    </div>
                    <div className="flex justify-between items-baseline">
                      <span className="text-sm text-gray-400">All Markets Total</span>
                      <span className="text-sm font-semibold text-gray-300">{totalListings.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : hasData ? (
              <div className="text-sm text-gray-500">No listings found for {MP_META[mpFilter]?.label ?? mpFilter} on this event.</div>
            ) : (
              <div className="text-sm text-gray-600">Loading…</div>
            )}
          </div>
        )}

        {/* Footer note */}
        <div className="mt-4 pt-3 border-t border-white/5 text-[10px] text-gray-700">
          {mpFilter === 'all'
            ? 'Data source: inventory-summary (full DB counts). Counts are not capped. Share % = marketplace listings ÷ total raw listings.'
            : 'Data source: inventory-summary.per_marketplace. Lowest ask is normalized (all-in price).'}
        </div>
      </div>
    </div>
  );
}

// ── Section 4: Premium Marketplace Cards ──────────────────────────────────────

const MP_ACCENT: Record<string, { accent: string; glow: string; dot: string }> = {
  stubhub:    { accent: 'rgba(99,102,241,0.9)',  glow: 'rgba(99,102,241,0.12)',  dot: '#818CF8' },
  tickpick:   { accent: 'rgba(34,197,94,0.9)',   glow: 'rgba(34,197,94,0.10)',   dot: '#4ADE80' },
  gametime:   { accent: 'rgba(249,115,22,0.9)',  glow: 'rgba(249,115,22,0.10)',  dot: '#FB923C' },
  vividseats: { accent: 'rgba(244,114,182,0.9)', glow: 'rgba(244,114,182,0.10)', dot: '#F472B6' },
};

function PremiumMpCard({
  mp,
  listings,
  run,
  movementData,
  invMp,
  acctMp,
}: {
  mp: typeof MARKETPLACES[number];
  listings: any[];
  run: PollRun | null;
  movementData?: InvMovement | null;
  invMp?: any;
  acctMp?: MarketplaceAccounting | null;
}) {
  const mpListings = listings.filter((l: any) => l.marketplace_slug === mp.slug);
  // Prefer full-DB counts from invSummary/accounting over the capped listings array
  const listingCount =
    invMp?.raw_listings ??
    acctMp?.active_rows ??
    ((movementData?.website_comparable_count || 0) > 0
      ? movementData!.website_comparable_count
      : (movementData?.normalized_blocks || 0) > 0
        ? movementData!.normalized_blocks
        : mpListings.length);
  const lowest =
    invMp?.normalized_lowest_ask ??
    acctMp?.low_ask ??
    movementData?.low_ask ??
    (mpListings.length > 0 ? Math.min(...mpListings.map((l: any) => l.price_each)) : null);
  const theme = MP_ACCENT[mp.slug] ?? { accent: 'rgba(255,255,255,0.5)', glow: 'rgba(0,0,0,0)', dot: '#9ca3af' };

  const isOk = run?.status === 'success' || (!run && listingCount > 0);
  const isErr = run?.status === 'error';
  const isNoData = run?.status === 'no_data';
  const statusDot = isOk ? theme.dot : isErr ? '#EF4444' : isNoData ? '#FBBF24' : '#4B5563';
  const statusLabel = isOk ? 'Live' : isErr ? 'Error' : isNoData ? 'No data' : !run ? (listingCount > 0 ? 'Live' : 'No data') : run.status;

  // Error type parsing
  let failureType: string | null = null;
  if (run?.error_message) {
    const m = run.error_message.match(/classification=(\S+)/);
    if (m) failureType = m[1].replace(/_/g, ' ');
  }

  return (
    <div className="mp-card p-5 relative overflow-hidden" style={{ boxShadow: `0 0 48px ${theme.glow}` }}>
      {/* Accent bar */}
      <div className="absolute top-0 left-0 right-0 h-[1.5px]" style={{ background: theme.accent }} />

      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="text-sm font-bold text-white tracking-wide">{mp.label}</div>
          <div className="flex items-center gap-1.5 mt-1">
            <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: statusDot }} />
            <span className="text-xs text-gray-500">{statusLabel}</span>
            {failureType && <span className="text-xs text-red-400">· {failureType}</span>}
          </div>
        </div>
        <div className="text-right">
          {lowest != null ? (
            <>
              <div className="text-2xl font-black text-white" style={{ letterSpacing: '-0.02em' }}>{fmt$(lowest)}</div>
              <div className="text-[10px] text-gray-600 mt-0.5">from / ticket</div>
            </>
          ) : (
            <div className="text-2xl font-black text-gray-700">—</div>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="glass-dark rounded-xl px-2 py-2.5 text-center">
          <div className="text-base font-bold text-white">{listingCount.toLocaleString()}</div>
          <div className="stat-label">Listings</div>
        </div>
        <div className="glass-dark rounded-xl px-2 py-2.5 text-center">
          <div className="text-base font-bold text-emerald-400">+{run?.new_listings ?? 0}</div>
          <div className="stat-label">New</div>
        </div>
        <div className="glass-dark rounded-xl px-2 py-2.5 text-center">
          <div className="text-base font-bold text-red-400">−{run?.disappeared_listings ?? 0}</div>
          <div className="stat-label">Gone</div>
        </div>
      </div>

      {/* Last updated */}
      {run?.completed_at && (
        <div className="text-[10px] text-gray-700 border-t border-white/5 pt-3">
          Updated {fmtRelative(run.completed_at)} ago
        </div>
      )}
      {!run && (
        <div className="text-[10px] text-gray-700 border-t border-white/5 pt-3 italic">
          Never polled
        </div>
      )}
    </div>
  );
}

// ── Inventory Accounting Panel (Advanced) ─────────────────────────────────────

function DupeRatioBar({ ratio }: { ratio: number }) {
  const pct = Math.round(ratio * 100);
  const color = ratio < 0.10 ? 'bg-green-500' : ratio < 0.30 ? 'bg-yellow-500' : 'bg-orange-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
      <span className={`text-xs font-mono tabular-nums ${ratio > 0.30 ? 'text-orange-400' : 'text-gray-300'}`}>
        {pct}%
      </span>
    </div>
  );
}

function InventoryAccountingPanel({ accounting }: { accounting: InventoryAccounting | null }) {
  if (!accounting) return null;
  const { per_marketplace, cross_market, sanity } = accounting;
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {per_marketplace.map(mp => {
          const deduped = mp.deduplicated_rows;
          const extra = mp.active_rows - deduped;
          const mpColor = MP_COLORS[mp.marketplace_slug] || 'text-gray-300';
          return (
            <div key={mp.marketplace_slug} className="glass-dark hover-shimmer rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-semibold uppercase tracking-wider ${mpColor}`}>
                  {mp.marketplace_slug}
                </span>
                {mp.health_flags.length > 0 && (
                  <span className="text-xs text-orange-400 bg-orange-900/30 px-2 py-0.5 rounded-full">
                    ⚠ {mp.health_flags[0].replace(/_/g, ' ')}
                  </span>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <div className="text-gray-500 mb-0.5">Active listings</div>
                  <div className="text-white font-semibold text-base">{mp.active_rows.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-gray-500 mb-0.5">Unique seat blocks</div>
                  <div className="text-white font-semibold text-base">{deduped.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-gray-500 mb-0.5">Est. tickets (raw)</div>
                  <div className="text-gray-300 font-medium">{mp.estimated_ticket_count.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-gray-500 mb-0.5">Est. unique tickets</div>
                  <div className="text-gray-300 font-medium">{mp.dedup_ticket_count.toLocaleString()}</div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-500">Duplicate sellers</span>
                  <span className="text-gray-400">{extra > 0 ? `+${extra} extra rows` : 'none'}</span>
                </div>
                <DupeRatioBar ratio={mp.duplicate_ratio} />
              </div>
              <div className="flex justify-between text-xs pt-1 border-t border-white/5">
                <div>
                  <span className="text-gray-500">Low ask </span>
                  <span className="text-green-400 font-medium">{mp.low_ask != null ? fmt$(mp.low_ask) : '—'}</span>
                </div>
                <div>
                  <span className="text-gray-500">Median </span>
                  <span className="text-gray-300">{mp.median_ask != null ? fmt$(mp.median_ask) : '—'}</span>
                </div>
                <div>
                  <span className="text-gray-500">Stale </span>
                  <span className="text-gray-400">{mp.stale_rows.toLocaleString()}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {cross_market.marketplace_slugs.length > 1 && (
        <div className="glass-panel rounded-xl p-4">
          <div className="text-xs font-semibold text-gray-300 mb-3 uppercase tracking-wider">Cross-Market Reconciliation</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div>
              <div className="text-gray-500 mb-1">Unique seat blocks</div>
              <div className="text-white font-semibold text-lg">{cross_market.total_unique_seat_blocks.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-gray-500 mb-1">Mirrored blocks</div>
              <div className="text-yellow-400 font-semibold text-lg">{cross_market.mirrored_blocks.toLocaleString()}</div>
              <div className="text-gray-500">{Math.round(cross_market.mirrored_ratio * 100)}% on 2+ markets</div>
            </div>
            {cross_market.marketplace_slugs.map(slug => (
              <div key={slug}>
                <div className="text-gray-500 mb-1 capitalize">{slug} exclusive</div>
                <div className={`font-semibold text-lg ${MP_COLORS[slug] || 'text-gray-300'}`}>
                  {(cross_market.only_on[slug] ?? 0).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="glass-panel rounded-xl p-4">
        <div className="text-xs font-semibold text-gray-300 mb-3 uppercase tracking-wider">Inventory Sanity</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div>
            <div className="text-gray-500 mb-1">Venue capacity</div>
            <div className="text-white font-medium">{sanity.venue_capacity != null ? sanity.venue_capacity.toLocaleString() : 'Unknown'}</div>
          </div>
          <div>
            <div className="text-gray-500 mb-1">Est. tickets listed</div>
            <div className="text-white font-medium">{sanity.estimated_ticket_count.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-gray-500 mb-1">Capacity utilization</div>
            <div className={`font-medium ${sanity.capacity_ratio != null && sanity.capacity_ratio > 1.5 ? 'text-red-400' : 'text-gray-300'}`}>
              {sanity.capacity_ratio != null ? `${(sanity.capacity_ratio * 100).toFixed(1)}%` : '—'}
            </div>
          </div>
          <div>
            <div className="text-gray-500 mb-1">Health</div>
            {sanity.flags.length === 0 ? (
              <div className="text-green-400 font-medium">✓ No issues</div>
            ) : (
              <div className="space-y-1">
                {sanity.flags.map(f => <div key={f} className="text-orange-400 text-xs">{f.replace(/_/g, ' ')}</div>)}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Canonical Inventory Panel (Advanced) ──────────────────────────────────────

interface CanonicalBlock {
  block_id: string;
  section_id: string;
  row: string | null;
  quantity: number;
  seller_count: number;
  marketplace_slugs: string[];
  low_ask: number;
  high_ask: number;
  median_ask: number;
  price_spread_pct: number;
  confidence_score: number;
  confidence_factors: Record<string, number | string>;
  last_seen_at: string | null;
  freshness_label: 'fresh' | 'aging' | 'stale';
  is_mirrored: boolean;
  duplicate_explanation: string;
}

interface CanonicalInventory {
  event_id: number;
  as_of: string;
  total_canonical_blocks: number;
  total_raw_listings: number;
  global_duplicate_ratio: number;
  mirrored_block_count: number;
  mirrored_ratio: number;
  by_marketplace: Record<string, number>;
  mean_confidence: number;
  high_confidence_blocks: number;
  low_confidence_blocks: number;
  canonical_blocks: CanonicalBlock[];
}

const FRESHNESS_DOT: Record<string, string> = {
  fresh: 'bg-emerald-400',
  aging: 'bg-amber-400',
  stale: 'bg-red-400',
};

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.80 ? 'bg-emerald-500' : score >= 0.50 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono tabular-nums text-gray-300 w-8 text-right">{pct}%</span>
    </div>
  );
}

type BlockSortKey = 'price' | 'confidence' | 'spread' | 'freshness' | 'quantity' | 'sellers';

function sortBlocks(blocks: CanonicalBlock[], sort: BlockSortKey): CanonicalBlock[] {
  const sorted = [...blocks];
  switch (sort) {
    case 'price':      return sorted.sort((a, b) => a.low_ask - b.low_ask);
    case 'confidence': return sorted.sort((a, b) => b.confidence_score - a.confidence_score);
    case 'spread':     return sorted.sort((a, b) => b.price_spread_pct - a.price_spread_pct);
    case 'quantity':   return sorted.sort((a, b) => b.quantity - a.quantity);
    case 'sellers':    return sorted.sort((a, b) => b.seller_count - a.seller_count);
    case 'freshness':  {
      const order = { fresh: 0, aging: 1, stale: 2 };
      return sorted.sort((a, b) => (order[a.freshness_label] ?? 1) - (order[b.freshness_label] ?? 1));
    }
    default: return sorted;
  }
}

function CanonicalInventoryPanel({ canonical }: { canonical: CanonicalInventory | null }) {
  const [blockFilter, setBlockFilter] = useState<'all' | 'mirrored' | 'exclusive' | 'high' | 'low'>('all');
  const [blockSort, setBlockSort] = useState<BlockSortKey>('price');

  if (!canonical) return null;

  const {
    total_canonical_blocks, total_raw_listings, global_duplicate_ratio,
    mirrored_block_count, mirrored_ratio, by_marketplace,
    mean_confidence, high_confidence_blocks, low_confidence_blocks, canonical_blocks,
  } = canonical;

  const brokerDupeCount = total_raw_listings - total_canonical_blocks;
  const brokerDupePct = Math.round(global_duplicate_ratio * 100);
  const exclusiveCount = total_canonical_blocks - mirrored_block_count;
  const estUniqueTickets = canonical_blocks.reduce((s, b) => s + b.quantity, 0);

  const filteredBlocks = sortBlocks(
    canonical_blocks.filter(b => {
      if (blockFilter === 'mirrored') return b.is_mirrored;
      if (blockFilter === 'exclusive') return !b.is_mirrored;
      if (blockFilter === 'high') return b.confidence_score >= 0.80;
      if (blockFilter === 'low') return b.confidence_score < 0.50;
      return true;
    }),
    blockSort,
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="glass-dark rounded-xl p-4 space-y-1">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Normalized Inventory</div>
          <div className="text-2xl font-bold text-white">{total_canonical_blocks.toLocaleString()}</div>
          <div className="text-xs text-gray-400">{total_raw_listings.toLocaleString()} raw → <span className="text-emerald-400">−{brokerDupeCount.toLocaleString()} dupes</span></div>
        </div>
        <div className="glass-dark rounded-xl p-4 space-y-1">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Broker Dupe Rate</div>
          <div className="text-2xl font-bold text-amber-400">{brokerDupePct}%</div>
          <div className="text-xs text-gray-400">same seat, different sellers</div>
        </div>
        <div className="glass-dark rounded-xl p-4 space-y-1">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Cross-Market Mirrors</div>
          <div className="text-2xl font-bold text-indigo-400">{mirrored_block_count.toLocaleString()}</div>
          <div className="text-xs text-gray-400">{exclusiveCount.toLocaleString()} single-market exclusive</div>
        </div>
        <div className="glass-dark rounded-xl p-4 space-y-1">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Est. Unique Tickets</div>
          <div className="text-2xl font-bold text-white">{estUniqueTickets.toLocaleString()}</div>
          <div className="text-xs text-gray-400">
            <span className="text-emerald-400">{high_confidence_blocks} high</span> · <span className="text-red-400">{low_confidence_blocks} low</span> conf.
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Filter:</span>
          {([
            ['all', `All (${total_canonical_blocks})`],
            ['mirrored', `Mirrored (${mirrored_block_count})`],
            ['exclusive', `Exclusive (${exclusiveCount})`],
            ['high', `High conf. (${high_confidence_blocks})`],
            ['low', `Low conf. (${low_confidence_blocks})`],
          ] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setBlockFilter(key)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                blockFilter === key ? 'bg-indigo-600/80 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10 border border-white/8'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <span className="text-xs text-gray-500">Sort:</span>
          {([['price', 'Price ↑'], ['confidence', 'Confidence ↓'], ['spread', 'Spread ↓'], ['freshness', 'Freshness'], ['quantity', 'Qty ↓'], ['sellers', 'Sellers ↓']] as const).map(([key, label]) => (
            <button key={key} onClick={() => setBlockSort(key)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${blockSort === key ? 'bg-emerald-700/60 text-emerald-200' : 'text-gray-500 hover:text-gray-300'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-panel rounded-xl overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-white/8">
              <th className="px-3 py-3 text-left text-gray-400 font-medium">Section</th>
              <th className="px-3 py-3 text-left text-gray-400 font-medium">Row</th>
              <th className="px-3 py-3 text-right text-gray-400 font-medium">Qty</th>
              <th className="px-3 py-3 text-right text-gray-400 font-medium">Low Ask</th>
              <th className="px-3 py-3 text-right text-gray-400 font-medium">Spread</th>
              <th className="px-3 py-3 text-center text-gray-400 font-medium">Sellers</th>
              <th className="px-3 py-3 text-left text-gray-400 font-medium">Markets</th>
              <th className="px-3 py-3 text-left text-gray-400 font-medium w-40">Confidence</th>
              <th className="px-3 py-3 text-center text-gray-400 font-medium">Fresh</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filteredBlocks.slice(0, 150).map((block) => (
              <tr key={block.block_id} className={`hover:bg-white/3 transition-colors ${block.is_mirrored ? 'bg-indigo-950/10' : ''}`}>
                <td className="px-3 py-2.5 text-white font-medium">{block.section_id || '—'}</td>
                <td className="px-3 py-2.5 text-gray-300">{block.row || '—'}</td>
                <td className="px-3 py-2.5 text-right text-gray-300">{block.quantity}</td>
                <td className="px-3 py-2.5 text-right font-mono text-emerald-400">{fmt$(block.low_ask)}</td>
                <td className="px-3 py-2.5 text-right text-gray-400">{block.price_spread_pct > 0 ? `${block.price_spread_pct.toFixed(1)}%` : '—'}</td>
                <td className="px-3 py-2.5 text-center">
                  {block.seller_count > 1 ? <span className="text-amber-400 font-medium">{block.seller_count}×</span> : <span className="text-gray-600">1</span>}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex gap-1 flex-wrap">
                    {block.marketplace_slugs.map(mp => <span key={mp} className={`text-xs ${MP_COLORS[mp] || 'text-gray-400'}`}>{mp}</span>)}
                  </div>
                </td>
                <td className="px-3 py-2.5 w-40"><ConfidenceBar score={block.confidence_score} /></td>
                <td className="px-3 py-2.5 text-center">
                  <span className={`inline-block w-2 h-2 rounded-full ${FRESHNESS_DOT[block.freshness_label] || 'bg-gray-500'}`} title={block.freshness_label} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredBlocks.length === 0 && <p className="text-center py-8 text-gray-400">No blocks match current filter.</p>}
        {filteredBlocks.length > 150 && (
          <div className="px-4 py-3 border-t border-white/8 text-xs text-gray-400 text-center">
            Showing 150 of {filteredBlocks.length.toLocaleString()} blocks
          </div>
        )}
      </div>
      <div className="text-xs text-gray-500 text-right">As of {new Date(canonical.as_of).toLocaleTimeString()}</div>
    </div>
  );
}

// ── Collapsible Advanced Section ──────────────────────────────────────────────

function AdvancedSection({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="glass-dark rounded-2xl overflow-hidden border border-white/6">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/3 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-gray-600 uppercase tracking-widest">Advanced · Technical Intelligence</span>
          <span className="text-[10px] text-gray-700">Canonical inventory · Accounting · Diagnostics</span>
        </div>
        <span className="text-gray-600 text-sm">{open ? '↑' : '↓'}</span>
      </button>
      {open && (
        <div className="px-5 pb-6 space-y-6 border-t border-white/5">
          {children}
        </div>
      )}
    </div>
  );
}

// ── Marketplace Snapshot Row ──────────────────────────────────────────────────

const SNAPSHOT_MARKETPLACES = [
  { slug: 'stubhub',      label: 'StubHub',      dot: '#818CF8', live: true  },
  { slug: 'tickpick',     label: 'TickPick',      dot: '#4ADE80', live: true  },
  { slug: 'gametime',     label: 'Gametime',      dot: '#FB923C', live: true  },
  { slug: 'vividseats',   label: 'Vivid Seats',   dot: '#F472B6', live: true  },
  { slug: 'seatgeek',     label: 'SeatGeek',      dot: '#6B7280', live: false, status: 'DEFERRED', msg: 'Deferred / blocked'  },
  { slug: 'ticketmaster', label: 'Ticketmaster',  dot: '#4B5563', live: false, status: 'PLANNED',  msg: 'Planned marketplace' },
] as const;

function MarketplaceSnapshotCards({
  invSummary,
  lastPolledAt,
  mpLatestRun,
}: {
  invSummary: any;
  lastPolledAt?: string;
  mpLatestRun: Record<string, PollRun | null>;
}) {
  return (
    <div className="space-y-3">
      {/* Net ticket summary strip */}
      <div className="flex items-center gap-5 px-1 flex-wrap">
        {invSummary?.unique_tickets_available != null && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-gray-600">Net Unique Tickets</span>
            <span className="text-sm font-bold text-violet-400 tabular-nums">
              {invSummary.unique_tickets_available.toLocaleString()}
            </span>
            <span className="text-[9px] text-gray-700">cross-market deduped</span>
          </div>
        )}
        {invSummary?.raw_tickets != null && invSummary?.unique_tickets_available != null && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-gray-600">Gross Tickets</span>
            <span className="text-sm font-bold text-gray-500 tabular-nums line-through decoration-white/20">
              {invSummary.raw_tickets.toLocaleString()}
            </span>
            <span className="text-[9px] text-amber-500 tabular-nums">
              −{(invSummary.raw_tickets - invSummary.unique_tickets_available).toLocaleString()} dupes
            </span>
          </div>
        )}
        <div className="flex items-center gap-1.5 text-[9px] text-gray-700 italic">
          <span>Per-marketplace net tickets</span>
          <span className="px-1.5 py-0.5 rounded bg-gray-800/60 text-gray-500 not-italic font-bold text-[8px] uppercase tracking-wider">coming soon</span>
        </div>
        {lastPolledAt && (
          <span className="ml-auto text-[10px] text-gray-700">
            Data as of {fmtRelative(lastPolledAt)} ago
          </span>
        )}
      </div>

      {/* Six cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {SNAPSHOT_MARKETPLACES.map(mp => {
          if (!mp.live) {
            return (
              <div
                key={mp.slug}
                className="rounded-xl p-4 border border-white/5"
                style={{ background: 'rgba(255,255,255,0.015)' }}
              >
                <div className="flex items-center gap-1.5 mb-2">
                  <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: mp.dot }} />
                  <span className="text-xs font-bold text-gray-500">{mp.label}</span>
                </div>
                <div className="mb-2">
                  <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-gray-800 text-gray-500">
                    {mp.status}
                  </span>
                </div>
                <div className="text-[10px] text-gray-600 leading-snug">{mp.msg}</div>
              </div>
            );
          }

          // Live marketplace — source: invSummary.per_marketplace (full DB count, never capped)
          const invMp      = invSummary?.per_marketplace?.find((m: any) => m.marketplace_slug === mp.slug);
          const listingCount = invMp?.raw_listings ?? 0;
          const lowestAsk    = invMp?.normalized_lowest_ask ?? null;
          const totalRaw     = invSummary?.raw_listings ?? 0;
          const sharePct     = totalRaw > 0 && listingCount > 0 ? (listingCount / totalRaw * 100) : null;
          const isLive       = listingCount > 0;
          const theme        = MP_ACCENT[mp.slug] ?? { accent: 'rgba(255,255,255,0.3)', glow: 'rgba(0,0,0,0)', dot: '#9ca3af' };
          const run          = mpLatestRun[mp.slug] ?? null;

          return (
            <div
              key={mp.slug}
              className="relative rounded-xl p-4 border border-white/6 transition-colors hover:border-white/10"
              style={{ background: 'rgba(255,255,255,0.025)', boxShadow: isLive ? `0 0 20px ${theme.glow}` : 'none' }}
            >
              {/* Accent top line */}
              {isLive && (
                <div className="absolute top-0 left-0 right-0 h-[1.5px] rounded-t-xl" style={{ background: theme.accent }} />
              )}
              {/* Header row */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: isLive ? mp.dot : '#4B5563' }} />
                  <span className="text-xs font-bold text-white">{mp.label}</span>
                </div>
                <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                  isLive ? 'bg-emerald-900/40 text-emerald-400' : 'bg-gray-800 text-gray-500'
                }`}>
                  {isLive ? 'LIVE' : 'EMPTY'}
                </span>
              </div>
              {/* Price */}
              {lowestAsk != null ? (
                <div className="mb-2">
                  <div className="text-xl font-black text-white" style={{ letterSpacing: '-0.02em' }}>{fmt$(lowestAsk)}</div>
                  <div className="text-[10px] text-gray-600">from / ticket</div>
                </div>
              ) : (
                <div className="text-xl font-black text-gray-700 mb-2">—</div>
              )}
              {/* Gross listings + gross tickets — clearly labeled */}
              <div className="space-y-0.5">
                <div className="text-[11px] text-gray-500">
                  {listingCount > 0
                    ? <><span className="text-gray-400 font-semibold tabular-nums">{listingCount.toLocaleString()}</span> <span className="text-gray-600">gross listings</span></>
                    : <span className="text-gray-600">No data</span>}
                  {sharePct != null && (
                    <span className="text-gray-700 ml-1.5">· {sharePct.toFixed(0)}%</span>
                  )}
                </div>
                {invMp?.raw_tickets != null && invMp.raw_tickets > 0 && (
                  <div className="text-[10px] text-gray-600">
                    <span className="text-gray-500 tabular-nums">{invMp.raw_tickets.toLocaleString()}</span>
                    <span className="text-gray-700"> gross tickets</span>
                  </div>
                )}
                <div className="text-[9px] text-gray-800 italic mt-0.5">net per-site coming soon</div>
              </div>
              {/* Freshness */}
              {run?.completed_at ? (
                <div className="text-[10px] text-gray-700 mt-1.5 border-t border-white/5 pt-1.5">
                  {fmtRelative(run.completed_at)} ago
                </div>
              ) : !run && isLive ? (
                <div className="text-[10px] text-gray-700 mt-1.5 border-t border-white/5 pt-1.5 italic">Poll pending</div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Market Structure Section ──────────────────────────────────────────────────
// Shows gross/net/duplicate breakdown + mirror rate in a scannable grid.

function MarketStructureSection({ invSummary, canonical }: { invSummary: any; canonical: any }) {
  if (!invSummary) {
    return (
      <div className="glass-dark rounded-2xl p-5 flex items-center justify-center h-20 text-gray-700 text-xs italic">
        Loading market structure…
      </div>
    );
  }
  const gross   = invSummary.raw_tickets ?? null;
  const net     = invSummary.unique_tickets_available ?? null;
  const dupes   = gross != null && net != null ? gross - net : null;
  const mirror  = invSummary.mirror_rate ?? null;
  const grossL  = invSummary.raw_listings ?? null;
  const canBlks = canonical?.total_canonical_blocks ?? null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {[
        { label: 'Gross Tickets',  value: gross  != null ? gross.toLocaleString()  : '—', sub: 'across all markets',   color: '#9CA3AF' },
        { label: 'Duplicate Tickets', value: dupes != null ? dupes.toLocaleString() : '—', sub: 'same seat, 2+ sites', color: dupes && dupes > 0 ? '#F59E0B' : '#6B7280' },
        { label: 'Net Unique',     value: net    != null ? net.toLocaleString()    : '—', sub: 'estimated real supply', color: '#A78BFA' },
        { label: 'Gross Listings', value: grossL != null ? grossL.toLocaleString() : '—', sub: 'raw listing count',    color: '#6B7280' },
        { label: 'Canonical Blocks', value: canBlks != null ? canBlks.toLocaleString() : '—', sub: 'unique seat blocks', color: '#818CF8' },
        { label: 'Mirror Rate',    value: mirror != null ? `${(mirror * 100).toFixed(1)}%` : '—', sub: 'cross-site overlap', color: mirror && mirror > 0.15 ? '#F59E0B' : '#6B7280' },
      ].map(({ label, value, sub, color }) => (
        <div key={label} className="glass-dark rounded-xl p-4">
          <div className="text-[9px] font-bold uppercase tracking-widest text-gray-600 mb-1.5">{label}</div>
          <div className="text-xl font-black tabular-nums" style={{ color, letterSpacing: '-0.02em' }}>{value}</div>
          <div className="text-[9px] text-gray-700 mt-0.5">{sub}</div>
        </div>
      ))}
    </div>
  );
}

// ── Market Activity Section ───────────────────────────────────────────────────
// Prominent attribution-driven section: sold / relisted / new / withdrawn / repriced.

function MarketActivitySection({ attribution, inventoryMovement }: { attribution: any; inventoryMovement: any }) {
  const hasAttribution = attribution && !attribution.error && attribution.classification_summary;
  const hasMov = inventoryMovement && !inventoryMovement.error;

  if (!hasAttribution && !hasMov) {
    return (
      <div className="glass-dark rounded-2xl p-5 flex items-center justify-center h-20 text-gray-700 text-xs italic">
        Activity data builds as snapshot history accumulates — poll a few times to unlock.
      </div>
    );
  }

  const cs = attribution?.classification_summary ?? {};
  const sc = attribution?.sold_confidence_breakdown ?? {};
  const mov = inventoryMovement ?? {};

  const activities = [
    {
      label: 'Sold',
      value: cs.likely_sold ?? mov.likely_sold ?? 0,
      sub: sc.high ? `${sc.high} high-conf` : 'estimated',
      color: '#EF4444',
      bg: 'rgba(239,68,68,0.08)',
      border: 'rgba(239,68,68,0.18)',
    },
    {
      label: 'New Listings',
      value: cs.new_listing ?? mov.new_listings ?? 0,
      sub: 'appeared',
      color: '#22C55E',
      bg: 'rgba(34,197,94,0.07)',
      border: 'rgba(34,197,94,0.15)',
    },
    {
      label: 'Relisted',
      value: cs.likely_relisted ?? mov.likely_relisted ?? 0,
      sub: 'reappeared',
      color: '#A78BFA',
      bg: 'rgba(167,139,250,0.07)',
      border: 'rgba(167,139,250,0.15)',
    },
    {
      label: 'Withdrawn',
      value: cs.withdrawn ?? 0,
      sub: '>14d before event',
      color: '#F97316',
      bg: 'rgba(249,115,22,0.07)',
      border: 'rgba(249,115,22,0.15)',
    },
    {
      label: 'Repriced',
      value: cs.price_changed ?? mov.price_changed ?? 0,
      sub: 'price changed',
      color: '#38BDF8',
      bg: 'rgba(56,189,248,0.07)',
      border: 'rgba(56,189,248,0.15)',
    },
    {
      label: 'Disappeared',
      value: cs.disappeared ?? mov.disappeared ?? 0,
      sub: 'unknown reason',
      color: '#6B7280',
      bg: 'rgba(107,114,128,0.06)',
      border: 'rgba(107,114,128,0.12)',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Activity grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {activities.map(({ label, value, sub, color, bg, border }) => (
          <div key={label} className="rounded-xl p-4" style={{ background: bg, border: `1px solid ${border}` }}>
            <div className="text-[9px] font-bold uppercase tracking-widest mb-1.5" style={{ color: `${color}99` }}>{label}</div>
            <div className="text-2xl font-black tabular-nums" style={{ color: value > 0 ? color : '#374151', letterSpacing: '-0.03em' }}>
              {value}
            </div>
            <div className="text-[9px] mt-0.5" style={{ color: '#4B5563' }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* Per-marketplace breakdown (if attribution available) */}
      {hasAttribution && attribution.by_marketplace && attribution.by_marketplace.length > 0 && (
        <div className="glass-dark rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 border-b border-white/5 flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-widest text-gray-600">Per Marketplace</span>
            <span className="text-[10px] text-gray-700">{attribution.snapshot_windows_analyzed ?? '?'} snapshot windows analyzed</span>
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-white/5">
                <th className="px-4 py-2 text-left text-gray-600 font-medium">Market</th>
                <th className="px-4 py-2 text-right text-red-700 font-medium">Sold</th>
                <th className="px-4 py-2 text-right text-orange-700 font-medium">Withdrawn</th>
                <th className="px-4 py-2 text-right text-emerald-700 font-medium">New</th>
                <th className="px-4 py-2 text-right text-violet-700 font-medium">Relisted</th>
                <th className="px-4 py-2 text-right text-sky-700 font-medium">Repriced</th>
                <th className="px-4 py-2 text-right text-gray-700 font-medium">Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {attribution.by_marketplace.map((mp: any) => (
                <tr key={mp.marketplace} className="hover:bg-white/3 transition-colors">
                  <td className="px-4 py-2 text-gray-300 font-medium capitalize">{mp.marketplace}</td>
                  <td className="px-4 py-2 text-right tabular-nums" style={{ color: mp.likely_sold > 0 ? '#EF4444' : '#374151' }}>{mp.likely_sold}</td>
                  <td className="px-4 py-2 text-right tabular-nums" style={{ color: mp.withdrawn > 0 ? '#F97316' : '#374151' }}>{mp.withdrawn}</td>
                  <td className="px-4 py-2 text-right tabular-nums" style={{ color: mp.new_listing > 0 ? '#22C55E' : '#374151' }}>{mp.new_listing}</td>
                  <td className="px-4 py-2 text-right tabular-nums" style={{ color: mp.likely_relisted > 0 ? '#A78BFA' : '#374151' }}>{mp.likely_relisted}</td>
                  <td className="px-4 py-2 text-right tabular-nums" style={{ color: mp.price_changed > 0 ? '#38BDF8' : '#374151' }}>{mp.price_changed}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-gray-600">{mp.active}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = Number(params.id);

  const [event, setEvent] = useState<any>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [pollRuns, setPollRuns] = useState<PollRun[]>([]);
  const [accounting, setAccounting] = useState<InventoryAccounting | null>(null);
  const [canonical, setCanonical] = useState<CanonicalInventory | null>(null);
  const [marketIntel, setMarketIntel] = useState<any>(null);
  const [inventoryMovement, setInventoryMovement] = useState<any>(null);
  const [sectionLiquidity, setSectionLiquidity] = useState<any>(null);
  const [canonicalHistory, setCanonicalHistory] = useState<any[]>([]);
  const [invSummary, setInvSummary] = useState<any>(null);
  const [baseline, setBaseline] = useState<any>(null);
  const [attribution, setAttribution] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [pollLoading, setPollLoading] = useState(false);

  // ── My Event / Follow / Hidden state (via hooks) ─────────────────────────
  const { myEvents, toggle: toggleMyEventSet }    = useMyEvents();
  const { followed, toggle: toggleFollowSet }      = useFollowed();
  const { hiddenEvents, toggle: toggleHiddenSet }  = useHiddenEvents();
  const isMyEvent   = myEvents.has(eventId);
  const isFollowing = followed.has(eventId);
  const isHidden    = hiddenEvents.has(eventId);
  const toggleMyEvent  = useCallback(() => toggleMyEventSet(eventId),  [eventId, toggleMyEventSet]);
  const toggleFollow   = useCallback(() => toggleFollowSet(eventId),   [eventId, toggleFollowSet]);
  const toggleHidden   = useCallback(() => toggleHiddenSet(eventId),   [eventId, toggleHiddenSet]);

  // Listings drilldown expanded state
  const [listingsExpanded, setListingsExpanded] = useState(true);
  const [excludeParking, setExcludeParking] = useState(false);
  const [hiddenListings, setHiddenListings] = useState<Set<number>>(new Set());

  // Filters
  const [marketplace, setMarketplace] = useState<string>('');
  const [sectionFilter, setSectionFilter] = useState<string>('');
  const [rowFilter, setRowFilter] = useState<string>('');
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [minQty, setMinQty] = useState<string>('');
  const [sort, setSort] = useState<string>('price_asc');
  const [listingView, setListingView] = useState<'raw' | 'canonical' | 'mirrored'>('raw');

  useEffect(() => { loadEvent(); }, [eventId]);
  useEffect(() => {
    if (event) {
      loadListings(); loadPollRuns(); loadAccounting();
      loadCanonical(); loadMarketIntel(); loadInventoryMovement();
      loadSectionLiquidity(); loadCanonicalHistory(); loadInvSummary(); loadBaseline();
      loadAttribution();
    }
  }, [event]);

  useEffect(() => {
    if (event) loadListings();
  }, [marketplace, sectionFilter, rowFilter, minPrice, maxPrice, minQty, sort]);

  async function loadEvent() {
    try {
      const data = await api.events.get(eventId);
      setEvent(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function loadListings() {
    try {
      const data = await api.listings.byEventFiltered(eventId, {
        marketplace:  marketplace  || undefined,
        section_id:   sectionFilter || undefined,
        row:          rowFilter    || undefined,
        minPrice:     minPrice     || undefined,
        maxPrice:     maxPrice     || undefined,
        minQuantity:  minQty       || undefined,
        sort:         sort         || undefined,
      });
      setListings(data);
    } catch (e) { console.error(e); }
  }

  async function loadPollRuns() {
    try { setPollRuns(await api.poll.runs(eventId)); }
    catch (e) { console.error(e); }
  }

  async function loadAccounting() {
    try { setAccounting(await api.analytics.inventoryAccounting(eventId)); }
    catch (e) { console.error('inventory-accounting error:', e); }
  }

  async function loadCanonical() {
    try { setCanonical(await api.analytics.canonicalInventory(eventId)); }
    catch (e) { console.error('canonical-inventory error:', e); }
  }

  async function loadMarketIntel() {
    try { setMarketIntel(await api.analytics.marketIntelligence(eventId)); }
    catch (e) { console.error('market-intelligence error:', e); }
  }

  async function loadInventoryMovement() {
    try { setInventoryMovement(await api.analytics.inventoryMovement(eventId)); }
    catch (e) { console.error('inventory-movement error:', e); }
  }

  async function loadInvSummary() {
    try { setInvSummary(await api.analytics.inventorySummary(eventId)); }
    catch (e) { console.error('inventory-summary error:', e); }
  }

  async function loadBaseline() {
    try { setBaseline(await api.analytics.baseline(eventId)); }
    catch (e) { console.error('baseline error:', e); }
  }

  async function loadAttribution() {
    try { setAttribution(await api.analytics.attribution(eventId)); }
    catch (e) { console.error('attribution error:', e); }
  }

  async function loadSectionLiquidity() {
    try { setSectionLiquidity(await api.analytics.sectionLiquidity(eventId)); }
    catch (e) { console.error('section-liquidity error:', e); }
  }

  async function loadCanonicalHistory() {
    try {
      const data = await api.analytics.canonicalHistory(eventId, 48);
      setCanonicalHistory(Array.isArray(data) ? data : []);
    } catch (e) { console.error('canonical-history error:', e); }
  }

  async function triggerPoll() {
    setPollLoading(true);
    try {
      await api.poll.trigger(eventId);
      await new Promise(r => setTimeout(r, 4000));
      await Promise.all([
        loadEvent(), loadListings(), loadPollRuns(), loadAccounting(),
        loadCanonical(), loadMarketIntel(), loadInventoryMovement(),
        loadSectionLiquidity(), loadCanonicalHistory(), loadInvSummary(), loadBaseline(),
        loadAttribution(),
      ]);
    } finally {
      setPollLoading(false);
    }
  }

  async function toggleActive() {
    if (!event) return;
    await api.events.update(eventId, { is_active: !event.is_active });
    await loadEvent();
  }

  // ── Loading / not found states ──────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600" />
      </div>
    );
  }

  if (!event) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
          style={{ background: 'rgba(229,9,20,0.07)', border: '1px solid rgba(229,9,20,0.15)' }}>
          <span style={{ fontSize: 28, opacity: 0.4 }}>?</span>
        </div>
        <div className="text-center">
          <p className="text-gray-300 font-semibold text-base">Event not found</p>
          <p className="text-gray-600 text-sm mt-1">This event may have been removed or the ID is invalid.</p>
        </div>
        <button onClick={() => router.back()} className="text-red-400 hover:text-red-300 text-sm">← Go back</button>
      </div>
    );
  }

  // ── Derived values ──────────────────────────────────────────────────────────

  // Per-marketplace latest poll run.
  // Match runs to marketplaces using accounting active_rows counts as a heuristic,
  // then fall back to assigning successful runs in order to unmatched marketplaces.
  const latestByTracked = new Map<number, PollRun>();
  for (const run of pollRuns) {
    if (!latestByTracked.has(run.tracked_event_id)) latestByTracked.set(run.tracked_event_id, run);
  }
  const mpLatestRun: Record<string, PollRun | null> = {
    stubhub: null, tickpick: null, gametime: null, vividseats: null,
  };
  // Build per-marketplace listing counts from accounting (full DB counts, not capped)
  const acctBySlug: Record<string, number> = {};
  if (accounting) {
    for (const m of accounting.per_marketplace) {
      acctBySlug[m.marketplace_slug] = m.active_rows;
    }
  }
  // Try to match each run to a marketplace by its listings_found count
  const assignedTeIds = new Set<number>();
  for (const [teId, run] of latestByTracked.entries()) {
    if (run.status !== 'success' && run.status !== 'no_data') continue;
    for (const slug of ['stubhub', 'tickpick', 'gametime', 'vividseats'] as const) {
      if (mpLatestRun[slug]) continue;
      const expected = acctBySlug[slug];
      if (expected != null && Math.abs(run.listings_found - expected) <= 5) {
        mpLatestRun[slug] = run;
        assignedTeIds.add(teId);
        break;
      }
    }
  }
  // For any marketplace still unmatched, assign remaining successful runs in order
  for (const [teId, run] of latestByTracked.entries()) {
    if (assignedTeIds.has(teId)) continue;
    if (run.status !== 'success' && run.status !== 'no_data') continue;
    for (const slug of ['stubhub', 'tickpick', 'gametime', 'vividseats'] as const) {
      if (!mpLatestRun[slug]) { mpLatestRun[slug] = run; assignedTeIds.add(teId); break; }
    }
  }

  // ── SOURCE OF TRUTH HIERARCHY ────────────────────────────────────────────────
  // Priority 1 (counts/prices): invSummary.per_marketplace — full DB, never capped
  // Priority 2 (freshness):     pollRuns / event.last_polled_at
  // Drilldown only:             listings array — capped at 500 by byEventFiltered, NOT used for summary totals
  const invPerMp: any[] = invSummary?.per_marketplace ?? [];
  const _invLowest = invPerMp.length > 0
    ? Math.min(...invPerMp.map((m: any) => m.normalized_lowest_ask ?? Infinity).filter(isFinite))
    : Infinity;
  const heroLowestAsk: number | null = isFinite(_invLowest) ? _invLowest
    : (listings.length > 0 ? Math.min(...listings.map((l: any) => l.price_each)) : null);
  const heroTotalListings: number = invSummary?.raw_listings ?? listings.length;
  const heroUniqueTickets: number | null = invSummary?.unique_tickets_available ?? null;
  const heroMirrorRate: number | null = invSummary?.mirror_rate ?? null;

  // Legacy aliases — keep for drilldown/canonical panel which legitimately use listings array
  const totalListings = listings.length;   // drilldown display only — not used in summary hero
  const lowestAskRaw = heroLowestAsk;      // unified
  const canonicalCount = canonical?.total_canonical_blocks ?? 0;

  // Canonical / mirrored key sets for view-mode filtering
  const sellerCounts = new Map<string, number>();
  for (const l of listings) {
    const key = `${(l.section_id || '').toUpperCase()}|${(l.row || '').toUpperCase()}|${l.quantity}`;
    sellerCounts.set(key, (sellerCounts.get(key) || 0) + 1);
  }
  const canonicalKeys = new Set<string>();
  const mirroredKeys  = new Set<string>();
  if (canonical?.canonical_blocks) {
    for (const b of canonical.canonical_blocks) {
      const key = `${(b.section_id || '').toUpperCase()}|${(b.row || '').toUpperCase()}|${b.quantity}`;
      canonicalKeys.add(key);
      if (b.is_mirrored) mirroredKeys.add(key);
    }
  }
  const viewFilteredListings = listings.filter(l => {
    if (hiddenListings.has(l.id)) return false;
    if (listingView === 'raw') return true;
    const key = `${(l.section_id || '').toUpperCase()}|${(l.row || '').toUpperCase()}|${l.quantity}`;
    if (listingView === 'canonical') return canonicalKeys.has(key);
    if (listingView === 'mirrored')  return mirroredKeys.has(key);
    return true;
  });

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div>
      {/* ── SECTION 1: Executive Hero ───────────────────────────────────────── */}
      <EventHero
        event={event}
        lowestAsk={heroLowestAsk}
        totalListings={heroTotalListings}
        canonicalCount={heroUniqueTickets ?? canonicalCount}
        mirrorRate={heroMirrorRate}
        baseline={baseline}
        invSummary={invSummary}
        onPoll={triggerPoll}
        pollLoading={pollLoading}
        onBack={() => router.back()}
      />

      {/* ── No-inventory banner (shown when event has zero listings across all markets) */}
      {invSummary != null && heroTotalListings === 0 && (
        <div
          className="mx-4 sm:mx-6 mt-3 rounded-xl px-4 py-3 flex items-center gap-3"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
        >
          <span className="text-yellow-500/70 text-sm shrink-0">⚠</span>
          <div className="text-xs text-gray-500">
            <span className="font-semibold text-gray-400">No current inventory</span>
            {' — '}
            {event.is_active === false
              ? 'Event is inactive. Reactivate to resume tracking.'
              : invSummary == null
                ? 'Inventory data is loading or not yet available.'
                : 'No listings found across tracked marketplaces. Refresh to pull latest data.'}
          </div>
        </div>
      )}

      {/* ── Quick actions bar ────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 px-1 mt-3 mb-1 flex-wrap">
        {/* My Event */}
        <button
          onClick={toggleMyEvent}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
          style={isMyEvent
            ? { background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.4)', color: '#F59E0B' }
            : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#6B7280' }
          }
        >
          <Star size={11} fill={isMyEvent ? '#F59E0B' : 'none'} stroke={isMyEvent ? '#F59E0B' : 'currentColor'}/>
          {isMyEvent ? 'My Event' : 'Mark as Mine'}
        </button>

        {/* Follow */}
        <button
          onClick={toggleFollow}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
          style={isFollowing
            ? { background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.4)', color: '#8B5CF6' }
            : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#6B7280' }
          }
        >
          {isFollowing ? <Bell size={11}/> : <BellOff size={11}/>}
          {isFollowing ? 'Following' : 'Follow'}
        </button>

        {/* Hide from Dashboard — continues polling */}
        <button
          onClick={toggleHidden}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
          style={isHidden
            ? { background: 'rgba(107,114,128,0.15)', border: '1px solid rgba(107,114,128,0.4)', color: '#9CA3AF' }
            : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#6B7280' }
          }
          title="Hide from dashboard — polling continues"
        >
          {isHidden ? <Eye size={11}/> : <EyeOff size={11}/>}
          {isHidden ? 'Restore' : 'Hide'}
        </button>

        {/* Archive — soft-delete, retains history */}
        {event.status !== 'archived' && (
          <button
            onClick={async () => {
              if (!confirm('Archive this event? Polling stops but all history is retained.')) return;
              await api.events.delete(eventId);
              router.back();
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', color: '#6B7280' }}
            title="Archive event — retains all history, stops polling"
          >
            🗄 Archive
          </button>
        )}

        {/* Stop Tracking / Reactivate */}
        <button
          onClick={toggleActive}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ml-auto"
          style={event.is_active === false
            ? { background: 'rgba(34,197,94,0.10)', border: '1px solid rgba(34,197,94,0.3)', color: '#22C55E' }
            : { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', color: '#4B5563' }
          }
          title={event.is_active === false ? "Reactivate — resumes data collection" : "Stop Tracking — pauses data collection"}
        >
          {event.is_active === false ? <Power size={11}/> : <PowerOff size={11}/>}
          {event.is_active === false ? 'Reactivate' : 'Stop Tracking'}
        </button>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 space-y-10 py-8">

        {/* ── SECTION 2: Marketplace Snapshot ─────────────────────────────── */}
        <section>
          <div className="section-label mb-3">⊡ Live Marketplace Inventory</div>
          <MarketplaceSnapshotCards
            invSummary={invSummary}
            lastPolledAt={event.last_polled_at}
            mpLatestRun={mpLatestRun}
          />
        </section>

        {/* ── SECTION 3: Market Structure ──────────────────────────────────── */}
        <section>
          <div className="section-label mb-3">◈ Market Structure</div>
          <MarketStructureSection invSummary={invSummary} canonical={canonical} />
        </section>

        {/* ── SECTION 4: Market Activity (attribution) ─────────────────────── */}
        <section>
          <div className="section-label mb-3">⚡ Market Activity</div>
          <MarketActivitySection attribution={attribution} inventoryMovement={inventoryMovement} />
        </section>

        {/* ── SECTION 5: Movement Delta ────────────────────────────────────── */}
        <section>
          <div className="section-label mb-3">↗ Market Movement</div>
          <MarketMovementSection event={event} baseline={baseline} invSummary={invSummary} />
        </section>

        {/* ── SECTION 6: Historical Charts ─────────────────────────────────── */}
        <section className="space-y-4">
          <div className="section-label mb-1">📈 Historical Trends</div>

          {/* ── Canonical Snapshot Trend (canonical-history endpoint) ──────── */}
          {(() => {
            // Deduplicate by timestamp — multiple per-marketplace rows collapse to one
            const dedupMap = new Map<string, any>();
            for (const snap of canonicalHistory) {
              const key = snap.snapshot_at;
              if (!dedupMap.has(key) || snap.total_canonical_blocks > (dedupMap.get(key)?.total_canonical_blocks ?? 0)) {
                dedupMap.set(key, snap);
              }
            }
            const chartData = Array.from(dedupMap.values())
              .sort((a, b) => new Date(a.snapshot_at).getTime() - new Date(b.snapshot_at).getTime())
              .map(s => ({
                ts: new Date(s.snapshot_at).getTime(),
                blocks: s.total_canonical_blocks,
                low_ask: s.low_ask != null ? Number(s.low_ask.toFixed(0)) : null,
                conf: s.mean_confidence != null ? Number((s.mean_confidence * 100).toFixed(1)) : null,
              }));

            if (chartData.length === 0) {
              return (
                <div className="glass-dark rounded-2xl p-5">
                  <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-3">Snapshot Trend</div>
                  <div className="flex items-center justify-center h-16 text-gray-600 text-xs italic">
                    No snapshot history yet — data builds automatically as polls run.
                  </div>
                </div>
              );
            }

            const fmtTime = (ms: number) => {
              const d = new Date(ms);
              return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' +
                     d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
            };

            return (
              <div className="glass-dark rounded-2xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Snapshot Trend</div>
                  <div className="flex items-center gap-4 text-[10px] text-gray-600">
                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-0.5 bg-indigo-400" />Canonical blocks</span>
                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-0.5 bg-emerald-400" />Floor ask</span>
                    <span className="text-gray-700">{chartData.length} snapshots</span>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <ComposedChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis
                      dataKey="ts"
                      type="number"
                      scale="time"
                      domain={['dataMin', 'dataMax']}
                      tickFormatter={fmtTime}
                      tick={{ fill: '#4B5563', fontSize: 10 }}
                      tickLine={false}
                      axisLine={{ stroke: 'rgba(255,255,255,0.05)' }}
                    />
                    <YAxis
                      yAxisId="blocks"
                      orientation="left"
                      tick={{ fill: '#4B5563', fontSize: 10 }}
                      tickLine={false}
                      axisLine={false}
                      width={36}
                      tickFormatter={(v: number) => v.toLocaleString()}
                    />
                    <YAxis
                      yAxisId="price"
                      orientation="right"
                      tick={{ fill: '#4B5563', fontSize: 10 }}
                      tickLine={false}
                      axisLine={false}
                      width={44}
                      tickFormatter={(v: number) => `$${v}`}
                    />
                    <Tooltip
                      contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11, color: '#e5e7eb' }}
                      labelFormatter={(v: number) => fmtTime(v)}
                      formatter={(value: number, name: string) =>
                        name === 'blocks' ? [value.toLocaleString(), 'Canonical blocks']
                        : name === 'low_ask' ? [`$${value}`, 'Floor ask']
                        : [`${value}%`, 'Confidence']
                      }
                    />
                    <Area
                      yAxisId="blocks"
                      type="monotone"
                      dataKey="blocks"
                      stroke="#818CF8"
                      fill="rgba(129,140,248,0.08)"
                      strokeWidth={2}
                      dot={false}
                      connectNulls
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="low_ask"
                      stroke="#34D399"
                      strokeWidth={2}
                      dot={false}
                      connectNulls
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            );
          })()}

          {/* ── Gross vs Net Ticket Trend ──────────────────────────── */}
          {(() => {
            const dedupMap2 = new Map<string, any>();
            for (const snap of canonicalHistory) {
              const key = snap.snapshot_at;
              if (!dedupMap2.has(key) || snap.total_canonical_blocks > (dedupMap2.get(key)?.total_canonical_blocks ?? 0)) {
                dedupMap2.set(key, snap);
              }
            }
            const chartData2 = Array.from(dedupMap2.values())
              .sort((a, b) => new Date(a.snapshot_at).getTime() - new Date(b.snapshot_at).getTime())
              .map(s => ({
                ts: new Date(s.snapshot_at).getTime(),
                gross: s.total_raw_listings ?? null,
                net: s.total_canonical_blocks ?? null,
                dupes: (s.total_raw_listings != null && s.total_canonical_blocks != null)
                  ? s.total_raw_listings - s.total_canonical_blocks : null,
              }))
              .filter(d => d.gross != null || d.net != null);

            if (chartData2.length < 2) return null;
            const fmtTime2 = (ms: number) => new Date(ms).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

            return (
              <div className="glass-dark rounded-2xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Gross vs Net Inventory Trend</div>
                  <div className="flex items-center gap-4 text-[10px] text-gray-600">
                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-0.5 bg-gray-500" />Gross listings</span>
                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-0.5 bg-violet-400" />Net canonical blocks</span>
                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-0.5 bg-amber-400" />Duplicates</span>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={200}>
                  <ComposedChart data={chartData2} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="ts" type="number" scale="time" domain={['dataMin','dataMax']}
                      tickFormatter={fmtTime2} tick={{ fill:'#4B5563', fontSize:10 }} tickLine={false}
                      axisLine={{ stroke:'rgba(255,255,255,0.05)' }} />
                    <YAxis tick={{ fill:'#4B5563', fontSize:10 }} tickLine={false} axisLine={false} width={36}
                      tickFormatter={(v:number) => v.toLocaleString()} />
                    <Tooltip
                      contentStyle={{ background:'#111827', border:'1px solid rgba(255,255,255,0.08)', borderRadius:8, fontSize:11, color:'#e5e7eb' }}
                      labelFormatter={(v:number) => fmtTime2(v)}
                      formatter={(value:number, name:string) =>
                        name === 'gross' ? [value.toLocaleString(), 'Gross listings']
                        : name === 'net'  ? [value.toLocaleString(), 'Net canonical blocks']
                        : [value.toLocaleString(), 'Duplicate listings']
                      }
                    />
                    <Area type="monotone" dataKey="gross" stroke="#6B7280" fill="rgba(107,114,128,0.08)" strokeWidth={1.5} dot={false} connectNulls />
                    <Area type="monotone" dataKey="net" stroke="#A78BFA" fill="rgba(167,139,250,0.08)" strokeWidth={2} dot={false} connectNulls />
                    <Line type="monotone" dataKey="dupes" stroke="#F59E0B" strokeWidth={1.5} dot={false} connectNulls strokeDasharray="4 3" />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            );
          })()}

          {/* ── Duplicate Rate Trend ───────────────────────────────── */}
          {(() => {
            const dedupMap3 = new Map<string, any>();
            for (const snap of canonicalHistory) {
              const key = snap.snapshot_at;
              if (!dedupMap3.has(key) || snap.total_canonical_blocks > (dedupMap3.get(key)?.total_canonical_blocks ?? 0)) {
                dedupMap3.set(key, snap);
              }
            }
            const chartData3 = Array.from(dedupMap3.values())
              .sort((a, b) => new Date(a.snapshot_at).getTime() - new Date(b.snapshot_at).getTime())
              .map(s => ({
                ts: new Date(s.snapshot_at).getTime(),
                dupRate: s.global_duplicate_ratio != null ? Number((s.global_duplicate_ratio * 100).toFixed(1)) : null,
                mirrorRate: s.mirrored_ratio != null ? Number((s.mirrored_ratio * 100).toFixed(1)) : null,
              }))
              .filter(d => d.dupRate != null || d.mirrorRate != null);

            if (chartData3.length < 2) return null;
            const fmtTime3 = (ms: number) => new Date(ms).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

            return (
              <div className="glass-dark rounded-2xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Duplicate &amp; Mirror Rate Trend</div>
                  <div className="flex items-center gap-4 text-[10px] text-gray-600">
                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-0.5 bg-amber-400" />Duplicate rate %</span>
                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-0.5 bg-sky-400" />Mirror rate %</span>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={160}>
                  <ComposedChart data={chartData3} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="ts" type="number" scale="time" domain={['dataMin','dataMax']}
                      tickFormatter={fmtTime3} tick={{ fill:'#4B5563', fontSize:10 }} tickLine={false}
                      axisLine={{ stroke:'rgba(255,255,255,0.05)' }} />
                    <YAxis tick={{ fill:'#4B5563', fontSize:10 }} tickLine={false} axisLine={false} width={36}
                      tickFormatter={(v:number) => `${v}%`} />
                    <Tooltip
                      contentStyle={{ background:'#111827', border:'1px solid rgba(255,255,255,0.08)', borderRadius:8, fontSize:11, color:'#e5e7eb' }}
                      labelFormatter={(v:number) => fmtTime3(v)}
                      formatter={(value:number, name:string) =>
                        name === 'dupRate' ? [`${value}%`, 'Duplicate rate']
                        : [`${value}%`, 'Mirror rate']
                      }
                    />
                    <Line type="monotone" dataKey="dupRate" stroke="#F59E0B" strokeWidth={2} dot={false} connectNulls />
                    <Line type="monotone" dataKey="mirrorRate" stroke="#38BDF8" strokeWidth={2} dot={false} connectNulls />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            );
          })()}

          <div className="chart-container">
            <PriceHistoryChart eventId={eventId} />
          </div>
          <div className="chart-container">
            <InventoryChart eventId={eventId} />
          </div>
          {/* SectionPriceBar removed — low-value horizontal bar above venue, replaced by listings table */}
          {event.venue_slug && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Venue Map</span>
                <span
                  className="px-2 py-0.5 rounded-full text-[10px] font-medium cursor-not-allowed"
                  style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', color: '#374151' }}
                  title="Click-to-filter venue map in development"
                >
                  Interactive Venue Map — Coming Soon
                </span>
              </div>
              <VenueHeatmap venueSlug={event.venue_slug} listings={listings} mode="price" />
            </div>
          )}
        </section>

        {/* Section divider */}
        <div className="section-divider" />

        {/* ── SECTION 7: Listings Drilldown ───────────────────────────────── */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="section-label">≡ Listings Drilldown</div>
              <span className="text-xs text-gray-600">{heroTotalListings.toLocaleString()} listings</span>
            </div>
            <button
              onClick={() => setListingsExpanded(o => !o)}
              className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
            >
              {listingsExpanded ? 'Collapse ↑' : 'Expand ↓'}
            </button>
          </div>

          {listingsExpanded && (
            <div className="space-y-4">
              {/* Filter bar */}
              <div className="glass-panel rounded-2xl p-4 space-y-3">
                {/* Row 1: Marketplace */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-gray-600 w-16 shrink-0 font-medium">Market</span>
                  {([['', 'All'], ...MARKETPLACES.map(m => [m.slug, m.label])] as [string,string][]).map(([val, label]) => (
                    <button
                      key={val}
                      onClick={() => setMarketplace(val as string)}
                      className={`filter-chip ${marketplace === val ? 'active' : ''}`}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                {/* Row 2: Section + Row */}
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-xs text-gray-600 w-16 shrink-0 font-medium">Section</span>
                  <select
                    value={sectionFilter}
                    onChange={e => setSectionFilter(e.target.value)}
                    className="bg-white/5 text-gray-200 text-xs rounded-lg px-2 py-1.5 border border-white/10 focus:border-red-800 outline-none min-w-[120px]"
                  >
                    <option value="">All sections</option>
                    {Array.from(new Set(
                      listings.map(l => l.section_id).filter(Boolean)
                        .sort((a: string, b: string) => {
                          const na = Number(a), nb = Number(b);
                          return !isNaN(na) && !isNaN(nb) ? na - nb : a.localeCompare(b);
                        })
                    )).map((sid: any) => <option key={sid} value={sid}>{sid}</option>)}
                  </select>
                  <span className="text-xs text-gray-600 font-medium">Row</span>
                  <input
                    type="text"
                    placeholder="e.g. K"
                    value={rowFilter}
                    onChange={e => setRowFilter(e.target.value.toUpperCase())}
                    className="w-16 bg-white/5 text-gray-200 text-xs rounded-lg px-2 py-1.5 border border-white/10 focus:border-red-800 outline-none uppercase"
                  />
                </div>

                {/* Row 3: Price / Qty / Sort */}
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-xs text-gray-600 w-16 shrink-0 font-medium">Price</span>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-700">$</span>
                    <input type="number" placeholder="min" value={minPrice} onChange={e => setMinPrice(e.target.value)}
                      className="w-20 bg-white/5 text-gray-200 text-xs rounded-lg px-2 py-1.5 border border-white/10 focus:border-red-800 outline-none" />
                    <span className="text-gray-700 text-xs">–</span>
                    <input type="number" placeholder="max" value={maxPrice} onChange={e => setMaxPrice(e.target.value)}
                      className="w-20 bg-white/5 text-gray-200 text-xs rounded-lg px-2 py-1.5 border border-white/10 focus:border-red-800 outline-none" />
                  </div>
                  <span className="text-xs text-gray-600 font-medium">Min qty</span>
                  <input type="number" placeholder="1" value={minQty} onChange={e => setMinQty(e.target.value)}
                    className="w-16 bg-white/5 text-gray-200 text-xs rounded-lg px-2 py-1.5 border border-white/10 focus:border-red-800 outline-none" />
                  <span className="text-xs text-gray-600 font-medium">Sort</span>
                  <select value={sort} onChange={e => setSort(e.target.value)}
                    className="bg-white/5 text-gray-200 text-xs rounded-lg px-2 py-1.5 border border-white/10 focus:border-red-800 outline-none">
                    <option value="price_asc">Price ↑</option>
                    <option value="price_desc">Price ↓</option>
                    <option value="quantity_desc">Qty ↓</option>
                    <option value="quantity_asc">Qty ↑</option>
                    <option value="section">Section</option>
                    <option value="newest">Newest</option>
                  </select>
                  {(minPrice || maxPrice || minQty || marketplace || sectionFilter || rowFilter) && (
                    <button
                      onClick={() => { setMinPrice(''); setMaxPrice(''); setMinQty(''); setMarketplace(''); setSectionFilter(''); setRowFilter(''); }}
                      className="text-xs text-red-500 hover:text-red-400 underline ml-1"
                    >
                      Clear all
                    </button>
                  )}
                </div>

                {/* Row 4: View mode */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-gray-600 w-16 shrink-0 font-medium">View</span>
                  {([
                    ['raw',       `Raw (${totalListings.toLocaleString()})`,             'text-gray-200'],
                    ['canonical', `Canonical (${canonicalKeys.size.toLocaleString()})`,  'text-indigo-300'],
                    ['mirrored',  `Mirrored (${mirroredKeys.size.toLocaleString()})`,    'text-amber-300'],
                  ] as const).map(([val, label, color]) => (
                    <button
                      key={val}
                      onClick={() => setListingView(val)}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                        listingView === val
                          ? `bg-white/15 ${color} border border-white/20`
                          : 'bg-white/5 text-gray-500 hover:bg-white/10 hover:text-gray-300 border border-white/8'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                  <span className="ml-auto text-xs text-gray-600">
                    {viewFilteredListings.length.toLocaleString()} shown
                    {listingView !== 'raw' && ` · ${listingView} filter`}
                  </span>
                </div>
              </div>

              {/* Exclude parking toggle */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-600 w-16 shrink-0 font-medium">Filter</span>
                <label className="flex items-center gap-1.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={excludeParking}
                    onChange={e => setExcludeParking(e.target.checked)}
                    className="rounded accent-red-600"
                  />
                  <span className="text-xs text-gray-500">Hide parking / shuttle listings</span>
                </label>
              </div>

              {/* Listings table */}
              <div className="glass-panel rounded-2xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/8">
                      <th className="px-4 py-3 text-left text-gray-500 font-medium text-xs uppercase tracking-wider">Section</th>
                      <th className="px-4 py-3 text-left text-gray-500 font-medium text-xs uppercase tracking-wider">Row</th>
                      <th className="px-4 py-3 text-right text-gray-500 font-medium text-xs uppercase tracking-wider">Price</th>
                      <th className="px-4 py-3 text-right text-gray-500 font-medium text-xs uppercase tracking-wider">All-in</th>
                      <th className="px-4 py-3 text-right text-gray-500 font-medium text-xs uppercase tracking-wider">Qty</th>
                      <th className="px-4 py-3 text-left text-gray-500 font-medium text-xs uppercase tracking-wider">Market</th>
                      <th className="px-4 py-3 text-right text-gray-500 font-medium text-xs uppercase tracking-wider">×</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {viewFilteredListings
                      .filter((l: any) => !excludeParking || !l.is_parking)
                      .slice(0, 200)
                      .map((listing: any) => {
                      const seatKey = `${(listing.section_id || '').toUpperCase()}|${(listing.row || '').toUpperCase()}|${listing.quantity}`;
                      const nSellers = sellerCounts.get(seatKey) || 1;
                      const isMirrored = mirroredKeys.has(seatKey);
                      return (
                        <tr key={listing.id} className={`group hover:bg-white/3 transition-colors ${isMirrored ? 'bg-indigo-950/10' : ''}`}>
                          <td className="px-4 py-2.5 text-white">
                            {listing.section_name || '—'}
                            {isMirrored && <span className="ml-1.5 text-[10px] text-indigo-400">↔</span>}
                            {listing.is_parking && <span className="ml-1.5 text-[9px] text-amber-600 font-bold uppercase tracking-wide">P</span>}
                          </td>
                          <td className="px-4 py-2.5 text-gray-300">{listing.row || '—'}</td>
                          <td className="px-4 py-2.5 text-right font-mono font-bold text-emerald-400">{fmt$(listing.price_each)}</td>
                          <td className="px-4 py-2.5 text-right font-mono text-emerald-300 text-xs">
                            {listing.all_in_price ? fmt$(listing.all_in_price) : '—'}
                          </td>
                          <td className="px-4 py-2.5 text-right text-gray-300">{listing.quantity}</td>
                          <td className="px-4 py-2.5">
                            <Badge variant={(MP_BADGE as any)[listing.marketplace_slug] || 'default'}>
                              {listing.marketplace_slug}
                            </Badge>
                            {nSellers > 1 && <span className="ml-1.5 text-[9px] text-amber-500">{nSellers}×</span>}
                          </td>
                          <td className="px-4 py-2.5 text-right">
                            <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => setHiddenListings(prev => new Set([...prev, listing.id]))}
                                className="text-[10px] px-1.5 py-0.5 rounded text-gray-600 hover:text-gray-300 hover:bg-white/10 transition-colors"
                                title="Hide this listing"
                              >
                                Hide
                              </button>
                              <button
                                onClick={() => {
                                  const sec = listing.section_name || listing.section_id || '';
                                  if (sec && !confirm(`Mark "${sec}" as parking/non-ticket? This affects all listings in this section.`)) return;
                                  // Local-only for now: flag via section name pattern awareness
                                  alert(`Noted. "${sec}" marked as parking locally. Backend integration coming soon.`);
                                }}
                                className="text-[10px] px-1.5 py-0.5 rounded text-gray-700 hover:text-amber-400 hover:bg-amber-500/10 transition-colors"
                                title="Mark as parking/non-ticket listing"
                              >
                                🅿
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {viewFilteredListings.length === 0 && (
                  <div className="py-10 flex flex-col items-center gap-2">
                    {heroTotalListings === 0 ? (
                      <>
                        <div className="text-gray-600 text-sm font-medium">No inventory yet</div>
                        <div className="text-gray-700 text-xs text-center max-w-xs">
                          {event.is_active === false
                            ? 'This event is inactive. Reactivate to resume polling.'
                            : invSummary == null
                              ? 'Inventory data is loading or not yet available.'
                              : 'No listings found across tracked marketplaces. Try refreshing.'}
                        </div>
                      </>
                    ) : (
                      <p className="text-gray-500 text-sm">No listings match current filters.</p>
                    )}
                  </div>
                )}
                {viewFilteredListings.length > 200 && (
                  <div className="px-4 py-3 border-t border-white/8 text-xs text-gray-500 text-center">
                    Showing 200 of {viewFilteredListings.length.toLocaleString()} — narrow filters to see more
                  </div>
                )}
              </div>
            </div>
          )}
        </section>

        {/* ── Inventory Accounting ─────────────────────────────────────────── */}
        {invSummary && (
          <section className="glass-dark rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Inventory Accounting</h2>
              <span className="text-[10px] text-gray-700">All marketplaces · duplicate-adjusted</span>
            </div>

            {/* Plain-language explanation */}
            <p className="text-[11px] text-gray-600 leading-relaxed">
              Marketplace inventory often appears on multiple sites simultaneously. Duplicate tickets are removed to estimate actual supply.
            </p>

            {/* Ticket-centric three-step breakdown */}
            {invSummary.raw_tickets != null && invSummary.unique_tickets_available != null && (
              <div className="flex items-center gap-3 flex-wrap">
                <div className="glass-panel rounded-xl px-4 py-3 flex flex-col gap-0.5">
                  <div className="text-[9px] font-bold text-gray-600 uppercase tracking-wider">Gross Tickets</div>
                  <div className="text-xl font-black text-white tabular-nums">{invSummary.raw_tickets.toLocaleString()}</div>
                  <div className="text-[9px] text-gray-700">across all marketplaces</div>
                </div>
                <div className="text-gray-700 text-lg font-thin">−</div>
                <div className="glass-panel rounded-xl px-4 py-3 flex flex-col gap-0.5">
                  <div className="text-[9px] font-bold text-gray-600 uppercase tracking-wider">Duplicates Removed</div>
                  <div className="text-xl font-black text-amber-500 tabular-nums">
                    {(invSummary.raw_tickets - invSummary.unique_tickets_available).toLocaleString()}
                  </div>
                  <div className="text-[9px] text-gray-700">same ticket on multiple sites</div>
                </div>
                <div className="text-gray-700 text-lg font-thin">=</div>
                <div className="glass-panel rounded-xl px-4 py-3 flex flex-col gap-0.5" style={{ border:'1px solid rgba(167,139,250,0.2)' }}>
                  <div className="text-[9px] font-bold text-gray-600 uppercase tracking-wider">Unique Available</div>
                  <div className="text-xl font-black text-violet-400 tabular-nums">{invSummary.unique_tickets_available.toLocaleString()}</div>
                  <div className="text-[9px] text-gray-700">estimated actual supply</div>
                </div>
              </div>
            )}

            {/* Reconciliation detail — secondary */}
            {invSummary.mirror_rate != null && (
              <div className="flex items-center gap-3 pt-1 border-t border-white/5 text-[10px] text-gray-700">
                <span>Mirror rate:</span>
                <span className={invSummary.mirror_rate > 0.15 ? 'text-amber-400 font-semibold' : 'text-gray-500'}>
                  {(invSummary.mirror_rate * 100).toFixed(1)}%
                </span>
                {invSummary.exclusive_listings != null && (
                  <><span>·</span><span>{invSummary.exclusive_listings.toLocaleString()} exclusive listings</span></>
                )}
              </div>
            )}
          </section>
        )}

        {/* ── Duplicate Monitor ────────────────────────────────────────────── */}
        <section className="glass-dark rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Duplicate Monitor</h2>
            <span className="text-[10px] text-gray-700">Cross-marketplace overlap</span>
          </div>

          {/* Three-tier ticket breakdown */}
          {invSummary?.raw_tickets != null && invSummary?.unique_tickets_available != null ? (
            <div className="flex items-center gap-3 flex-wrap">
              <div className="glass-panel rounded-xl px-4 py-3 flex flex-col gap-0.5 min-w-[110px]">
                <div className="text-[9px] font-bold text-gray-600 uppercase tracking-wider">Gross Tickets</div>
                <div className="text-xl font-black text-gray-400 tabular-nums">{invSummary.raw_tickets.toLocaleString()}</div>
                <div className="text-[9px] text-gray-700">raw across all markets</div>
              </div>
              <div className="text-gray-600 text-base font-thin">−</div>
              <div className="glass-panel rounded-xl px-4 py-3 flex flex-col gap-0.5 min-w-[110px]">
                <div className="text-[9px] font-bold text-gray-600 uppercase tracking-wider">Duplicates Removed</div>
                <div className="text-xl font-black text-amber-400 tabular-nums">
                  {(invSummary.raw_tickets - invSummary.unique_tickets_available).toLocaleString()}
                </div>
                <div className="text-[9px] text-gray-700">same seat on 2+ sites</div>
              </div>
              <div className="text-gray-600 text-base font-thin">=</div>
              <div className="glass-panel rounded-xl px-4 py-3 flex flex-col gap-0.5 min-w-[110px]" style={{ border: '1px solid rgba(167,139,250,0.2)' }}>
                <div className="text-[9px] font-bold text-gray-600 uppercase tracking-wider">Net Unique Tickets</div>
                <div className="text-xl font-black text-violet-400 tabular-nums">{invSummary.unique_tickets_available.toLocaleString()}</div>
                <div className="text-[9px] text-gray-700">estimated real supply</div>
              </div>
            </div>
          ) : invSummary != null ? (
            <p className="text-[11px] text-gray-700 italic">Ticket breakdown data not yet available for this event.</p>
          ) : null}

          {/* Cross-site pairwise overlap */}
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '14px' }}>
            <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-3">Cross-Site Pairwise Overlap</div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {[
                { a: 'StubHub',   dotA: '#818CF8', b: 'TickPick',    dotB: '#4ADE80' },
                { a: 'StubHub',   dotA: '#818CF8', b: 'Gametime',    dotB: '#FB923C' },
                { a: 'StubHub',   dotA: '#818CF8', b: 'Vivid Seats', dotB: '#F472B6' },
                { a: 'TickPick',  dotA: '#4ADE80', b: 'Gametime',    dotB: '#FB923C' },
                { a: 'TickPick',  dotA: '#4ADE80', b: 'Vivid Seats', dotB: '#F472B6' },
                { a: 'Gametime',  dotA: '#FB923C', b: 'Vivid Seats', dotB: '#F472B6' },
              ].map(({ a, dotA, b, dotB }) => (
                <div
                  key={`${a}-${b}`}
                  className="flex items-center justify-between rounded-lg px-3 py-2"
                  style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}
                >
                  <div className="flex items-center gap-1.5 text-[10px] text-gray-500">
                    <span style={{ color: dotA }}>●</span>
                    <span>{a}</span>
                    <span className="text-gray-700">↔</span>
                    <span style={{ color: dotB }}>●</span>
                    <span>{b}</span>
                  </div>
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded ml-2"
                    style={{ background: 'rgba(255,255,255,0.04)', color: '#4B5563', border: '1px solid rgba(255,255,255,0.06)' }}>
                    Soon
                  </span>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-gray-700 italic mt-2">
              Cross-marketplace overlap detail coming soon. Will show % of seats listed on both platforms.
            </p>
          </div>
        </section>

        {/* ── Advanced Technical Intelligence (collapsed) ─────────────────── */}
        <AdvancedSection>
          {/* Inventory Movement */}
          {inventoryMovement && !inventoryMovement.error && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 pt-6">Inventory Movement</div>
              <div className="glass-panel rounded-xl p-4">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 text-xs">
                  {[
                    { label: 'New Listings',   val: inventoryMovement.new_listings,   color: 'text-emerald-400' },
                    { label: 'Disappeared',    val: inventoryMovement.disappeared,     color: 'text-orange-400' },
                    { label: 'Likely Sold',    val: inventoryMovement.likely_sold,     color: 'text-red-400'    },
                    { label: 'Price Changed',  val: inventoryMovement.price_changed,   color: 'text-sky-400'    },
                    { label: 'Relisted',       val: inventoryMovement.likely_relisted, color: 'text-violet-400' },
                  ].map(({ label, val, color }) => (
                    <div key={label} className="glass-dark rounded-lg px-3 py-2">
                      <div className="text-gray-600 mb-0.5">{label}</div>
                      <div className={`text-base font-bold tabular-nums ${val > 0 ? color : 'text-gray-700'}`}>{val ?? '—'}</div>
                    </div>
                  ))}
                </div>
                {(inventoryMovement.window_prev || inventoryMovement.window_curr) && (
                  <div className="text-[10px] text-gray-700 mt-2 italic">
                    Window: {inventoryMovement.window_prev ? new Date(inventoryMovement.window_prev).toLocaleString() : '?'} → {inventoryMovement.window_curr ? new Date(inventoryMovement.window_curr).toLocaleString() : '?'}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Attribution Intelligence */}
          {attribution && !attribution.error && attribution.classification_summary && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Attribution Intelligence</div>
              <div className="glass-panel rounded-xl p-4 space-y-3">
                {/* Summary counts */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  {[
                    { label: 'Likely Sold',   val: attribution.classification_summary.likely_sold   ?? 0, color: 'text-red-400'    },
                    { label: 'Withdrawn',     val: attribution.classification_summary.withdrawn     ?? 0, color: 'text-orange-400' },
                    { label: 'New Listings',  val: attribution.classification_summary.new_listing   ?? 0, color: 'text-emerald-400'},
                    { label: 'Relisted',      val: attribution.classification_summary.likely_relisted ?? 0, color: 'text-violet-400'},
                  ].map(({ label, val, color }) => (
                    <div key={label} className="glass-dark rounded-lg px-3 py-2">
                      <div className="text-gray-600 mb-0.5">{label}</div>
                      <div className={`text-base font-bold tabular-nums ${val > 0 ? color : 'text-gray-700'}`}>{val}</div>
                    </div>
                  ))}
                </div>
                {/* Sold confidence breakdown */}
                {attribution.sold_confidence_breakdown && (
                  <div className="flex items-center gap-4 text-[11px] border-t border-white/5 pt-2">
                    <span className="text-gray-600 uppercase tracking-wider text-[9px] font-bold">Sold confidence</span>
                    {(['high','medium','low'] as const).map(c => (
                      <span key={c} className={`${c === 'high' ? 'text-red-400' : c === 'medium' ? 'text-orange-400' : 'text-gray-500'}`}>
                        {c}: <span className="font-bold tabular-nums">{attribution.sold_confidence_breakdown[c] ?? 0}</span>
                      </span>
                    ))}
                  </div>
                )}
                {/* Per-marketplace breakdown */}
                {attribution.by_marketplace && attribution.by_marketplace.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-[11px]">
                      <thead>
                        <tr className="border-b border-white/5">
                          <th className="px-2 py-1.5 text-left text-gray-600 font-medium">Market</th>
                          <th className="px-2 py-1.5 text-right text-gray-600 font-medium">Sold</th>
                          <th className="px-2 py-1.5 text-right text-gray-600 font-medium">Withdrawn</th>
                          <th className="px-2 py-1.5 text-right text-gray-600 font-medium">New</th>
                          <th className="px-2 py-1.5 text-right text-gray-600 font-medium">Relisted</th>
                          <th className="px-2 py-1.5 text-right text-gray-600 font-medium">Price Δ</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {attribution.by_marketplace.map((mp: any) => (
                          <tr key={mp.marketplace} className="hover:bg-white/3">
                            <td className="px-2 py-1.5 text-gray-300 font-medium">{mp.marketplace}</td>
                            <td className="px-2 py-1.5 text-right text-red-400 tabular-nums">{mp.likely_sold ?? 0}</td>
                            <td className="px-2 py-1.5 text-right text-orange-400 tabular-nums">{mp.withdrawn ?? 0}</td>
                            <td className="px-2 py-1.5 text-right text-emerald-400 tabular-nums">{mp.new_listing ?? 0}</td>
                            <td className="px-2 py-1.5 text-right text-violet-400 tabular-nums">{mp.likely_relisted ?? 0}</td>
                            <td className="px-2 py-1.5 text-right text-sky-400 tabular-nums">{mp.price_changed ?? 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                <div className="text-[10px] text-gray-700 italic">{attribution.note}</div>
              </div>
            </div>
          )}

          {/* Section Liquidity */}
          {sectionLiquidity?.sections && sectionLiquidity.sections.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 pt-6">Section Liquidity</div>
              <div className="glass-panel rounded-xl overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-white/5">
                      <th className="px-3 py-2 text-left text-gray-500 font-medium">Section</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Blocks</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Tickets</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Low Ask</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Median</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Mirrored</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {sectionLiquidity.sections
                      .sort((a: any, b: any) => b.active_blocks - a.active_blocks)
                      .slice(0, 20)
                      .map((sec: any) => (
                      <tr key={sec.section_id} className="hover:bg-white/3 transition-colors">
                        <td className="px-3 py-2 text-white font-medium">{sec.section_id}</td>
                        <td className="px-3 py-2 text-right text-gray-300">{sec.active_blocks}</td>
                        <td className="px-3 py-2 text-right text-gray-400">{sec.active_tickets}</td>
                        <td className="px-3 py-2 text-right font-mono text-emerald-400">{fmt$(sec.low_ask)}</td>
                        <td className="px-3 py-2 text-right font-mono text-gray-400">{fmt$(sec.median_ask)}</td>
                        <td className="px-3 py-2 text-right">
                          {sec.mirrored_pct > 0 ? <span className="text-indigo-400">{Math.round(sec.mirrored_pct * 100)}%</span> : <span className="text-gray-700">—</span>}
                        </td>
                        <td className="px-3 py-2 text-right">
                          <span className={sec.high_confidence_pct > 0.5 ? 'text-emerald-400' : sec.high_confidence_pct > 0.2 ? 'text-amber-400' : 'text-gray-500'}>
                            {Math.round(sec.high_confidence_pct * 100)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Inventory Accounting */}
          {accounting && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Inventory Accounting</div>
              <InventoryAccountingPanel accounting={accounting} />
            </div>
          )}

          {/* Market Intelligence */}
          {marketIntel && !marketIntel.error && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Market Intelligence</div>
              <div className="glass-panel rounded-xl p-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                  {marketIntel.total_canonical_blocks != null && (
                    <div>
                      <div className="text-gray-500 mb-1">Canonical Blocks</div>
                      <div className="text-base font-bold text-white">{marketIntel.total_canonical_blocks.toLocaleString()}</div>
                      <div className="text-gray-600">unique seat blocks</div>
                    </div>
                  )}
                  {marketIntel.low_ask != null && (
                    <div>
                      <div className="text-gray-500 mb-1">Low Ask</div>
                      <div className="text-base font-bold text-emerald-400">{fmt$(marketIntel.low_ask)}</div>
                      <div className="text-gray-600">canonical floor</div>
                    </div>
                  )}
                  {marketIntel.mirrored_ratio != null && (
                    <div>
                      <div className="text-gray-500 mb-1">Mirrored</div>
                      <div className={`text-base font-bold ${marketIntel.mirrored_ratio > 0.5 ? 'text-amber-400' : 'text-gray-300'}`}>
                        {Math.round(marketIntel.mirrored_ratio * 100)}%
                      </div>
                      <div className="text-gray-600">cross-site duplicates</div>
                    </div>
                  )}
                  {marketIntel.mean_confidence != null && (
                    <div>
                      <div className="text-gray-500 mb-1">Confidence</div>
                      <div className={`text-base font-bold ${marketIntel.mean_confidence >= 0.8 ? 'text-emerald-400' : marketIntel.mean_confidence >= 0.5 ? 'text-amber-400' : 'text-red-400'}`}>
                        {Math.round(marketIntel.mean_confidence * 100)}%
                      </div>
                      <div className="text-gray-600">canonical match</div>
                    </div>
                  )}
                </div>
                {marketIntel.note && (
                  <div className="text-[10px] text-gray-700 mt-3 border-t border-white/5 pt-2 italic">{marketIntel.note}</div>
                )}
              </div>
            </div>
          )}

          {/* Canonical inventory */}
          {canonical && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Normalized Inventory Intelligence</div>
                <button
                  onClick={() => { loadCanonical(); loadMarketIntel(); loadSectionLiquidity(); loadCanonicalHistory(); }}
                  className="text-xs text-indigo-400 hover:text-indigo-300 px-3 py-1.5 glass-dark rounded-lg border border-white/10"
                >
                  Refresh
                </button>
              </div>
              <CanonicalInventoryPanel canonical={canonical} />
            </div>
          )}

          {/* Canonical snapshot history */}
          {canonicalHistory.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Snapshot History</div>
              <div className="glass-panel rounded-xl overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-white/5">
                      <th className="px-3 py-2 text-left text-gray-500 font-medium">Time</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Blocks</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Raw</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Dupe%</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Mirrored</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Confidence</th>
                      <th className="px-3 py-2 text-right text-gray-500 font-medium">Low Ask</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {[...canonicalHistory].reverse().map((snap: any) => (
                      <tr key={snap.snapshot_id} className="hover:bg-white/3 transition-colors">
                        <td className="px-3 py-2 text-gray-400">{fmtRelative(snap.snapshot_at)}</td>
                        <td className="px-3 py-2 text-right text-white font-medium">{snap.total_canonical_blocks.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right text-gray-500">{snap.total_raw_listings.toLocaleString()}</td>
                        <td className="px-3 py-2 text-right text-amber-400">{Math.round(snap.global_duplicate_ratio * 100)}%</td>
                        <td className="px-3 py-2 text-right text-indigo-400">{snap.mirrored_block_count}</td>
                        <td className="px-3 py-2 text-right">
                          <span className={snap.mean_confidence >= 0.8 ? 'text-emerald-400' : snap.mean_confidence >= 0.5 ? 'text-amber-400' : 'text-red-400'}>
                            {Math.round(snap.mean_confidence * 100)}%
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-emerald-400">
                          {snap.low_ask != null ? fmt$(snap.low_ask) : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Poll run diagnostics */}
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Poll Run History</div>
            <div className="glass-panel rounded-xl overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/8 text-gray-500">
                    <th className="px-3 py-2 text-left">Run</th>
                    <th className="px-3 py-2 text-left">TE</th>
                    <th className="px-3 py-2 text-left">Started</th>
                    <th className="px-3 py-2 text-left">Duration</th>
                    <th className="px-3 py-2 text-right">Found</th>
                    <th className="px-3 py-2 text-right text-emerald-600">New</th>
                    <th className="px-3 py-2 text-right text-sky-600">React</th>
                    <th className="px-3 py-2 text-right text-orange-600">Gone</th>
                    <th className="px-3 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {pollRuns.map(run => {
                    const durMs = run.completed_at && run.started_at
                      ? new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()
                      : null;
                    const durStr = durMs == null ? '…' : durMs < 1000 ? `${durMs}ms` : `${(durMs/1000).toFixed(1)}s`;
                    const statusColor = run.status === 'success' ? 'text-emerald-400' : run.status === 'error' ? 'text-red-400' : run.status === 'no_data' ? 'text-amber-400' : 'text-gray-400';
                    return (
                      <tr key={run.id} className="hover:bg-white/3 transition-colors">
                        <td className="px-3 py-2 text-gray-500">#{run.id}</td>
                        <td className="px-3 py-2 text-gray-400">te={run.tracked_event_id}</td>
                        <td className="px-3 py-2 text-gray-400">{fmtRelative(run.started_at)} ago</td>
                        <td className="px-3 py-2 text-gray-500">{durStr}</td>
                        <td className="px-3 py-2 text-right text-white">{run.listings_found}</td>
                        <td className="px-3 py-2 text-right text-emerald-400">+{run.new_listings}</td>
                        <td className="px-3 py-2 text-right text-sky-400">↺{run.reactivated_listings}</td>
                        <td className="px-3 py-2 text-right text-orange-400">−{run.disappeared_listings}</td>
                        <td className="px-3 py-2">
                          <span className={`font-medium ${statusColor}`}>{run.status}</span>
                          {run.error_message && (
                            <span className="ml-2 text-gray-600 truncate max-w-xs block" title={run.error_message}>
                              {run.error_message.slice(0, 80)}{run.error_message.length > 80 ? '…' : ''}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {pollRuns.length === 0 && <p className="text-center py-6 text-gray-500">No poll runs recorded.</p>}
            </div>
          </div>
        </AdvancedSection>

        {/* Bottom padding */}
        <div className="h-8" />
      </div>
    </div>
  );
}
