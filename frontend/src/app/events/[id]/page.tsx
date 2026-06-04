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

// ── Section 1: Editorial Split Hero ──────────────────────────────────────────

function EventHero({
  event,
  lowestAsk,
  totalListings,
  canonicalCount,
  mirrorRate,
  onPoll,
  pollLoading,
  onBack,
}: {
  event: any;
  lowestAsk: number | null;
  totalListings: number;
  canonicalCount: number;
  mirrorRate?: number | null;
  onPoll: () => void;
  pollLoading: boolean;
  onBack: () => void;
}) {
  const ms = getMarketStatus(lowestAsk);
  const title = event.title || '';
  const initial = (event.artist || title || '?')[0].toUpperCase();
  const isCompleted = event.status === 'completed' || event.status === 'archived';
  const days = event.event_date ? daysUntil(event.event_date) : null;
  const theme = getEventEntityTheme(title);
  const imgCfg = getEntityImage(title);
  const accent = imgCfg.accent ?? theme.accent;
  const accentRgb = theme.accentRgb;

  const venueName = event.venue_slug
    ? event.venue_slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())
    : null;

  // Derive category chip label
  const catLabel = (() => {
    const n = title.toLowerCase();
    if (/49ers|rams|chargers|raiders|chiefs|cowboys|eagles|packers|bears|seahawks|broncos|steelers/.test(n)) return 'NFL';
    if (/rangers|angels|dodgers|giants|padres|yankees|cubs|red sox|astros|braves/.test(n)) return 'MLB';
    if (/lakers|clippers|warriors|celtics|heat|bulls|nets|knicks/.test(n)) return 'NBA';
    return 'Live Event';
  })();

  // Value signal: price notably below average (use $150 as soft avg proxy)
  const isValue = lowestAsk != null && lowestAsk < 100;
  const isHot   = lowestAsk != null && lowestAsk >= 100 && lowestAsk < 160;

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

          {/* Large watermark initial */}
          <div
            className="absolute inset-0 flex items-center justify-end pr-6 select-none pointer-events-none"
            aria-hidden
          >
            <span className="font-black" style={{
              fontSize: '280px',
              lineHeight: 1,
              color: `rgba(${accentRgb}, 0.045)`,
              WebkitTextStrokeWidth: '1px',
              WebkitTextStrokeColor: `rgba(${accentRgb}, 0.07)`,
              fontFamily: 'system-ui, -apple-system, sans-serif',
              letterSpacing: '-0.06em',
            }}>
              {initial}
            </span>
          </div>

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

        {/* ── RIGHT: Data Panel ───────────────────────────────────────────── */}
        <div
          className="relative flex flex-col justify-between"
          style={{
            background: 'rgba(6,0,10,0.97)',
            borderLeft: '1px solid rgba(255,255,255,0.05)',
            padding: '28px 32px',
          }}
        >
          {/* Subtle top accent line */}
          <div
            className="absolute top-0 left-0 right-0 h-[1px]"
            style={{ background: `linear-gradient(to right, transparent, rgba(${accentRgb},0.35), transparent)` }}
          />

          <div className="flex flex-col gap-5">
            {/* ── Dominant price block ──────────────────────────────────── */}
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-gray-700 mb-1">
                Lowest Ask
              </div>
              {lowestAsk != null ? (
                <>
                  <div
                    className="font-black text-white leading-none"
                    style={{ fontSize: '52px', letterSpacing: '-0.04em' }}
                  >
                    {fmt$(lowestAsk)}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">per ticket · all-in price may vary</div>
                </>
              ) : (
                <div
                  className="font-black text-gray-700 leading-none"
                  style={{ fontSize: '52px', letterSpacing: '-0.04em' }}
                >
                  —
                </div>
              )}

              {/* Value / Hot signal box */}
              {isValue && (
                <div
                  className="mt-3 flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
                  style={{
                    background: 'rgba(34,197,94,0.06)',
                    border: '1px solid rgba(34,197,94,0.18)',
                  }}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full shrink-0"
                    style={{ background: '#22c55e', boxShadow: '0 0 6px rgba(34,197,94,0.6)' }}
                  />
                  <div>
                    <div className="text-[11px] font-bold text-green-400">Value Signal</div>
                    <div className="text-[10px] text-gray-600 mt-0.5">Below typical market range — strong entry point</div>
                  </div>
                </div>
              )}
              {isHot && !isValue && (
                <div
                  className="mt-3 flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
                  style={{
                    background: 'rgba(249,115,22,0.06)',
                    border: '1px solid rgba(249,115,22,0.18)',
                  }}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full shrink-0"
                    style={{ background: '#f97316', boxShadow: '0 0 6px rgba(249,115,22,0.5)' }}
                  />
                  <div>
                    <div className="text-[11px] font-bold text-orange-400">Watch Signal</div>
                    <div className="text-[10px] text-gray-600 mt-0.5">Active market — prices may shift</div>
                  </div>
                </div>
              )}
            </div>

            {/* ── Stats grid ───────────────────────────────────────────── */}
            <div
              className="grid grid-cols-2 gap-2"
              style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px' }}
            >
              {[
                { label: 'Listings',      value: totalListings > 0 ? totalListings.toLocaleString() : '—', accent: '#3B82F6' },
                { label: 'Unique Seats',  value: canonicalCount > 0 ? canonicalCount.toLocaleString() : '—', accent: '#8B5CF6' },
                { label: 'Mirror Rate',   value: mirrorRate != null ? `${(mirrorRate * 100).toFixed(1)}%` : '—', accent: mirrorRate != null && mirrorRate > 0.15 ? '#F59E0B' : '#6B7280' },
                { label: 'Days Away',     value: days != null && days > 0 ? `${days}d` : days === 0 ? 'Today' : days != null && days < 0 ? 'Past' : '—', accent: '#E50914' },
              ].map(({ label, value, accent: a }) => (
                <div
                  key={label}
                  className="rounded-lg px-3 py-2.5"
                  style={{ background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.05)' }}
                >
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-700">{label}</div>
                  <div className="text-sm font-bold mt-0.5" style={{ color: a }}>{value}</div>
                </div>
              ))}
            </div>

            {/* ── Event details rows ────────────────────────────────────── */}
            <div className="space-y-2" style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '14px' }}>
              {event.event_date && (
                <div className="flex items-baseline justify-between">
                  <span className="text-[11px] text-gray-700 uppercase tracking-wider font-bold">Date</span>
                  <span className="text-[12px] text-gray-300 font-medium">{fmtDate(event.event_date)}</span>
                </div>
              )}
              {venueName && (
                <div className="flex items-baseline justify-between">
                  <span className="text-[11px] text-gray-700 uppercase tracking-wider font-bold">Venue</span>
                  <span className="text-[12px] text-gray-300 font-medium truncate max-w-[180px] text-right">{venueName}</span>
                </div>
              )}
              {event.city && (
                <div className="flex items-baseline justify-between">
                  <span className="text-[11px] text-gray-700 uppercase tracking-wider font-bold">City</span>
                  <span className="text-[12px] text-gray-300 font-medium">{event.city}</span>
                </div>
              )}
              <div className="flex items-baseline justify-between">
                <span className="text-[11px] text-gray-700 uppercase tracking-wider font-bold">Category</span>
                <span className="text-[12px] font-semibold" style={{ color: accent }}>{catLabel}</span>
              </div>
            </div>
          </div>

          {/* ── CTAs + last updated ──────────────────────────────────────── */}
          <div className="flex flex-col gap-2 mt-2">
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
            {isCompleted && (
              <div
                className="w-full py-2.5 rounded-xl text-xs flex items-center justify-center gap-2"
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.35)' }}
              >
                <span className={event.status === 'archived' ? 'text-gray-500' : 'text-amber-500/70'}>
                  {event.status === 'archived' ? '🗄 Archived' : '✓ Completed'}
                </span>
                <span className="text-gray-700">·</span>
                <span>Historical view</span>
              </div>
            )}
            {event.last_polled_at && (
              <div className="text-[10px] text-gray-700 text-center">
                Last updated {fmtRelative(event.last_polled_at)} ago
              </div>
            )}
          </div>
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

// ── Market Baseline Section ───────────────────────────────────────────────────
// Source: /api/analytics/events/{id}/baseline  (canonical_inventory_snapshots)
// Read-only. No predictions. No buy/wait signals.

function MarketBaselineSection({ baseline }: { baseline: any }) {
  if (!baseline) return null;
  const cur = baseline.current;
  if (!cur) return null;

  const depth = baseline.history_depth_days ?? 0;

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
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-widest">Historical Snapshot Trends</span>
        <span className="text-[10px] text-gray-600">{depth}d history · from snapshots</span>
      </div>
      <div className="text-[10px] text-gray-700 mb-3 italic">
        Historical baseline comes from stored snapshots and may lag live inventory.
      </div>

      {/* Top-level trend table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-600 border-b border-white/5">
              <th className="text-left pb-1.5 pr-4 font-normal">Metric</th>
              <th className="text-right pb-1.5 pr-4 font-normal">Current</th>
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
            {/* Summary row */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-1">Listings</div>
                <div className="text-xl font-bold text-white">{hasData ? totalListings.toLocaleString() : '—'}</div>
                {invSummary?.exclusive_listings != null && (
                  <div className="text-[10px] text-gray-600 mt-0.5">{invSummary.exclusive_listings.toLocaleString()} excl · {invSummary.mirror_listings?.toLocaleString()} mirrors</div>
                )}
              </div>
              <div>
                <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-1">Lowest Ask</div>
                <div className="text-xl font-bold text-emerald-400">{allLowest != null && isFinite(allLowest) ? fmt$(allLowest) : '—'}</div>
              </div>
              <div>
                <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-1">Mirror Rate</div>
                <div className={`text-xl font-bold ${invSummary?.mirror_rate > 0.15 ? 'text-amber-400' : 'text-gray-300'}`}>
                  {invSummary?.mirror_rate != null ? `${(invSummary.mirror_rate * 100).toFixed(1)}%` : '—'}
                </div>
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
                    <span className="w-14 text-right">Listings</span>
                    <span className="w-14 text-right">Tickets</span>
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
                        <span className={`text-sm font-semibold tabular-nums w-14 text-right ${meta.colorCls}`}>
                          {m ? count.toLocaleString() : '—'}
                        </span>
                        <span className="text-sm tabular-nums w-14 text-right text-gray-500">
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
                      <span className="text-xs text-gray-700 w-14 text-right">—</span>
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
      {/* Duplication visibility strip */}
      <div className="flex items-center gap-5 px-1 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-600">Mirror Rate</span>
          <span className={`text-sm font-bold tabular-nums ${invSummary?.mirror_rate > 0.15 ? 'text-amber-400' : 'text-gray-300'}`}>
            {invSummary?.mirror_rate != null
              ? `${(invSummary.mirror_rate * 100).toFixed(1)}%`
              : '—'}
          </span>
          {invSummary?.mirror_listings != null && (
            <span className="text-xs text-indigo-400 tabular-nums">
              ({invSummary.mirror_listings.toLocaleString()} mirrored listings)
            </span>
          )}
        </div>
        {invSummary?.unique_tickets_available != null && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-gray-600">Unique Available</span>
            <span className="text-sm font-bold text-emerald-400 tabular-nums">
              {invSummary.unique_tickets_available.toLocaleString()}
            </span>
          </div>
        )}
        {/* Pairwise overlap: shows which pair of platforms mirrors the most */}
        <div className="flex items-center gap-1.5 text-[10px] text-gray-700 italic">
          <span>Pairwise overlap detail</span>
          <span className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-500 not-italic font-bold text-[9px] uppercase tracking-wider">COMING LATER</span>
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
              {/* Listings + Gross Tickets + share */}
              <div className="space-y-0.5">
                <div className="text-[11px] text-gray-500">
                  {listingCount > 0
                    ? <><span className="text-gray-300 font-semibold">{listingCount.toLocaleString()}</span> <span className="text-gray-600">listings</span></>
                    : <span className="text-gray-600">No data</span>}
                  {sharePct != null && (
                    <span className="text-gray-700 ml-1.5">· {sharePct.toFixed(0)}% share</span>
                  )}
                </div>
                {invMp?.raw_tickets != null && invMp.raw_tickets > 0 && (
                  <div className="text-[10px] text-gray-600">
                    <span className="text-gray-500 tabular-nums">{invMp.raw_tickets.toLocaleString()}</span> gross tickets
                  </div>
                )}
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
  const [loading, setLoading] = useState(true);
  const [pollLoading, setPollLoading] = useState(false);

  // ── My Event / Follow state (localStorage) ─────────────────────────────────
  const [isMyEvent,   setIsMyEvent]   = useState(false);
  const [isFollowing, setIsFollowing] = useState(false);

  useEffect(() => {
    if (!eventId) return;
    try {
      const me = new Set(JSON.parse(localStorage.getItem('my_events') ?? '[]'));
      setIsMyEvent(me.has(eventId));
      const fw = new Set(JSON.parse(localStorage.getItem('followed_events') ?? '[]'));
      setIsFollowing(fw.has(eventId));
    } catch {}
  }, [eventId]);

  const toggleMyEvent = useCallback(() => {
    setIsMyEvent(prev => {
      const next = !prev;
      try {
        const s = new Set<number>(JSON.parse(localStorage.getItem('my_events') ?? '[]'));
        if (next) s.add(eventId); else s.delete(eventId);
        localStorage.setItem('my_events', JSON.stringify([...s]));
      } catch {}
      return next;
    });
  }, [eventId]);

  const toggleFollow = useCallback(() => {
    setIsFollowing(prev => {
      const next = !prev;
      try {
        const s = new Set<number>(JSON.parse(localStorage.getItem('followed_events') ?? '[]'));
        if (next) s.add(eventId); else s.delete(eventId);
        localStorage.setItem('followed_events', JSON.stringify([...s]));
      } catch {}
      return next;
    });
  }, [eventId]);

  // Listings drilldown expanded state
  const [listingsExpanded, setListingsExpanded] = useState(true);

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
              : event.tracked_events?.length === 0
                ? 'No marketplaces are being tracked for this event.'
                : 'No listings found across tracked marketplaces. Refresh to pull latest data.'}
          </div>
        </div>
      )}

      {/* ── Quick actions: My Event + Follow ─────────────────────────────────── */}
      <div className="flex items-center gap-2 px-1 mt-3 mb-1">
        <button
          onClick={toggleMyEvent}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
          style={isMyEvent
            ? { background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.4)', color: '#F59E0B' }
            : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#6B7280' }
          }
          title={isMyEvent ? "Remove from My Events" : "Mark as My Event"}
        >
          <span style={{ fontSize: 11 }}>{isMyEvent ? '★' : '☆'}</span>
          {isMyEvent ? 'My Event' : 'Mark as Mine'}
        </button>
        <button
          onClick={toggleFollow}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
          style={isFollowing
            ? { background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.4)', color: '#8B5CF6' }
            : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#6B7280' }
          }
          title={isFollowing ? "Unfollow alerts" : "Follow for price alerts (coming soon)"}
        >
          <span style={{ fontSize: 11 }}>{isFollowing ? '🔔' : '🔕'}</span>
          {isFollowing ? 'Following' : 'Follow'}
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

        {/* ── SECTION 3a: Historical Snapshot Trends ──────────────────────── */}
        {baseline?.current && (
          <section>
            <div className="section-label mb-3">⟳ Historical Snapshot Trends</div>
            <MarketBaselineSection baseline={baseline} />
          </section>
        )}

        {/* ── SECTION 3b: Market Overview ─────────────────────────────────── */}
        <section>
          <div className="section-label mb-3">◈ Live Market Breakdown</div>
          <MarketOverviewPanel
            invSummary={invSummary}
            canonical={canonical}
          />
        </section>

        {/* ── SECTION 4: Market Movement / Charts ─────────────────────────── */}
        <section className="space-y-4">
          <div className="section-label mb-1">↗ Market Movement</div>
          <div className="chart-container">
            <PriceHistoryChart eventId={eventId} />
          </div>
          <div className="chart-container">
            <InventoryChart eventId={eventId} />
          </div>
          {/* SectionPriceBar removed — low-value horizontal bar above venue, replaced by listings table */}
          {/* TODO: Replace generic VenueHeatmap with real SVG venue maps:
                - preserve hover stats
                - click section → filter in-app listings
                - add external marketplace deep links per section
                Currently showing placeholder heatmap. */}
          {event.venue_slug && (
            <VenueHeatmap venueSlug={event.venue_slug} listings={listings} mode="price" />
          )}
        </section>

        {/* Section divider */}
        <div className="section-divider" />

        {/* ── SECTION 5: Listings Drilldown ───────────────────────────────── */}
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

              {/* TODO: Add parking-pass toggle — hide/show listings where is_parking=true
                    once backend exposes is_parking flag per listing.  Filter is already
                    applied at ingest; this would let power users see the raw catalog. */}

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
                      <th className="px-4 py-3 text-left text-gray-500 font-medium text-xs uppercase tracking-wider">Sellers</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {viewFilteredListings.slice(0, 200).map((listing: any) => {
                      const seatKey = `${(listing.section_id || '').toUpperCase()}|${(listing.row || '').toUpperCase()}|${listing.quantity}`;
                      const nSellers = sellerCounts.get(seatKey) || 1;
                      const isMirrored = mirroredKeys.has(seatKey);
                      return (
                        <tr key={listing.id} className={`hover:bg-white/3 transition-colors ${isMirrored ? 'bg-indigo-950/10' : ''}`}>
                          <td className="px-4 py-2.5 text-white">
                            {listing.section_name || '—'}
                            {isMirrored && <span className="ml-1.5 text-[10px] text-indigo-400">↔</span>}
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
                          </td>
                          <td className="px-4 py-2.5">
                            {nSellers > 1
                              ? <span className="text-xs text-amber-500 tabular-nums">{nSellers}×</span>
                              : <span className="text-xs text-gray-700">—</span>}
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

        {/* ── Phase 1E-F: Normalization Layer ─────────────────────────────── */}
        {invSummary && (
          <section className="glass-dark rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Normalization Layer</h2>
              <span className="text-[10px] text-gray-700">Phase 1E-F · Mirror dedup · All marketplaces</span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="glass-panel rounded-xl p-4">
                <div className="text-[10px] font-bold text-gray-600 uppercase tracking-wider mb-1">Unique Tickets Available</div>
                <div className="text-2xl font-bold text-emerald-400">{invSummary.unique_tickets_available?.toLocaleString() ?? '—'}</div>
                <div className="text-xs text-gray-600 mt-0.5">after mirror dedup</div>
              </div>
              <div className="glass-panel rounded-xl p-4">
                <div className="text-[10px] font-bold text-gray-600 uppercase tracking-wider mb-1">Listings Available</div>
                <div className="text-2xl font-bold text-white">{invSummary.raw_listings?.toLocaleString() ?? '—'}</div>
                <div className="text-xs text-gray-600 mt-0.5">{invSummary.exclusive_listings?.toLocaleString()} excl · {invSummary.mirror_listings?.toLocaleString()} mirrors</div>
              </div>
              <div className="glass-panel rounded-xl p-4">
                <div className="text-[10px] font-bold text-gray-600 uppercase tracking-wider mb-1">Mirror Rate</div>
                <div className={`text-2xl font-bold ${invSummary.mirror_rate > 0.15 ? 'text-amber-400' : 'text-gray-300'}`}>
                  {invSummary.mirror_rate != null ? `${(invSummary.mirror_rate * 100).toFixed(1)}%` : '—'}
                </div>
                <div className="text-xs text-gray-600 mt-0.5">cross-marketplace</div>
              </div>
            </div>
            {invSummary.per_marketplace?.length > 0 && (
              <div className="flex flex-wrap gap-4 pt-1 border-t border-white/5">
                {invSummary.per_marketplace.map((mp: any) => (
                  <div key={mp.marketplace_slug} className="flex items-center gap-2 text-xs">
                    <span className="font-bold text-gray-400 uppercase tracking-wide">{mp.marketplace_slug}</span>
                    <span className="text-gray-600">{mp.raw_listings?.toLocaleString()} listings</span>
                    {mp.normalized_lowest_ask != null && (
                      <span className="text-emerald-500 font-mono tabular-nums">${mp.normalized_lowest_ask.toFixed(0)}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* ── Advanced Technical Intelligence (collapsed) ─────────────────── */}
        <AdvancedSection>
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

          {/* Market Intelligence primitives */}
          {marketIntel?.primitives && (
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Market Intelligence</div>
              <div className="glass-panel rounded-xl p-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                  <div>
                    <div className="text-gray-500 mb-1">Stale Inventory</div>
                    <div className={`text-base font-bold ${marketIntel.primitives.stale_inventory_rate > 0.5 ? 'text-amber-400' : 'text-gray-300'}`}>
                      {Math.round(marketIntel.primitives.stale_inventory_rate * 100)}%
                    </div>
                    <div className="text-gray-600">{marketIntel.primitives.stale_active_blocks} blocks</div>
                  </div>
                  <div>
                    <div className="text-gray-500 mb-1">Broker Duplication</div>
                    <div className={`text-base font-bold ${marketIntel.primitives.broker_duplication_rate > 0.1 ? 'text-orange-400' : 'text-gray-300'}`}>
                      {(marketIntel.primitives.broker_duplication_rate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 mb-1">Blocks Ever Seen</div>
                    <div className="text-base font-bold text-white">{marketIntel.primitives.total_blocks_ever}</div>
                    <div className="text-gray-600">{marketIntel.primitives.disappeared_blocks} disappeared</div>
                  </div>
                  <div>
                    <div className="text-gray-500 mb-1">Time Tracked</div>
                    <div className="text-base font-bold text-white">
                      {marketIntel.primitives.hours_tracked < 1
                        ? `${Math.round(marketIntel.primitives.hours_tracked * 60)}m`
                        : `${marketIntel.primitives.hours_tracked.toFixed(1)}h`}
                    </div>
                    <div className="text-gray-600">{marketIntel.primitives.snapshot_count} snapshots</div>
                  </div>
                </div>
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
