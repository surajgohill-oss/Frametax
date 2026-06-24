"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Eye, RefreshCw, TrendingUp, TrendingDown, Minus, AlertCircle,
  ChevronDown, ChevronRight, Bookmark,
  ArrowUpRight, ArrowDownRight, Pin, Music,
  Pause, Play, Volume2, VolumeX,
} from "lucide-react";
import { differenceInDays, parseISO, format } from "date-fns";
import { api } from "@/lib/api";
import type { EventSummary, EventMeta } from "@/lib/types";
import { fmt$$, fmtNum, fmtPct, signalToAction, actionColors, signalDescription, cn, parseEventDate } from "@/lib/utils";
import { getEventGradient, gradientBg, extractGroupKey, getSpotifyData } from "@/lib/entityimages";
import { useArtistImage } from "@/hooks/useArtistImage";
import { useHiddenEvents } from "@/hooks/useHiddenEvents";
import { useWatchlist } from "@/hooks/useWatchlist";
import { useHeadlineEvent } from "@/hooks/useHeadlineEvent";
import { useNflAudio } from "@/hooks/useNflAudio";
import { isNflEvent } from "@/lib/audioConfig";
import { getBrand } from "@/components/MarketplaceBadge";
import EventCard from "@/components/EventCard";

type SortKey = "date" | "opportunity" | "signal" | "price" | "inventory" | "seller_drop" | "closest";
const SIGNAL_ORDER = ["deepening", "capitulating", "mixed", "stable", "loosening"];

type MetaMap = Record<number, EventMeta & { title?: string; venue_name?: string; venue_slug?: string; event_date?: string; artist?: string }>;

const MP_SHORT: Record<string, string> = {
  stubhub: "SH",
  gametime: "GT",
  tickpick: "TP",
  vividseats: "VS",
};

// ── Small delta chip ─────────────────────────────────────────────────────────
function DeltaChip({ pct, abs }: { pct?: number | null; abs?: number | null }) {
  const n = pct ?? abs ?? null;
  if (n == null) return <span className="text-white/25 text-[10px]">—</span>;
  const up = n > 0;
  const Icon = up ? TrendingUp : n < 0 ? TrendingDown : Minus;
  return (
    <span className={`inline-flex items-center gap-0.5 text-[10px] font-semibold tabular-nums ${up ? "text-emerald-400" : n < 0 ? "text-red-400" : "text-white/40"}`}>
      <Icon size={9} />{pct != null ? fmtPct(pct) : (n > 0 ? `+${n}` : `${n}`)}
    </span>
  );
}

// ── Featured Event Hero ───────────────────────────────────────────────────────
// One event. Compact identity row + 3-col intelligence: Current Market | Absorption | Seller Behavior.
// Target height 180–240px. BUY chip is small secondary only.
function FeaturedEventHero({
  event, meta, isWatched, onToggleWatch, isPinned, onTogglePin,
}: {
  event: EventSummary;
  meta: MetaMap[number] | undefined;
  isWatched: boolean;
  onToggleWatch: () => void;
  isPinned: boolean;
  onTogglePin: () => void;
}) {
  const title      = meta?.title ?? event.title;
  const venue      = meta?.venue_name;
  const dateStr    = meta?.event_date;
  const artist     = meta?.artist;
  const artworkUrl = useArtistImage(artist, title);
  const gradient   = getEventGradient(artist, title);
  const action     = signalToAction(event.signal);
  const aColors    = actionColors(action);
  const invDelta   = event.changes?.h24?.inventory_delta ?? null;

  let daysOut: number | null = null;
  let dateLabel = "";
  if (dateStr) {
    try {
      const d = parseEventDate(dateStr);
      daysOut = differenceInDays(d, new Date());
      dateLabel = format(d, "EEE, MMM d");
    } catch {}
  }

  // Tracking since from meta.created_at
  const trackingSince = (() => {
    const ca = meta?.created_at;
    if (!ca) return null;
    try {
      const d = parseISO(ca);
      const days = Math.round((Date.now() - d.getTime()) / 86400000);
      return { formatted: format(d, "MMM d, yyyy"), days };
    } catch { return null; }
  })();

  // Freshness label
  const freshLabel = (() => {
    const entries = Object.values(meta?.marketplace_freshness ?? {});
    if (!entries.length) return null;
    const ages = entries.map((e: unknown) => ((e as { age_minutes?: number }).age_minutes ?? 0)).filter(Boolean);
    if (!ages.length) return null;
    const maxAge = Math.max(...ages);
    return maxAge < 60 ? `${maxAge}m ago` : `${Math.round(maxAge / 60)}h ago`;
  })();

  const marketsCount = Object.keys(meta?.marketplace_freshness ?? {}).filter(
    k => (meta?.marketplace_freshness?.[k] as { freshness_status?: string } | undefined)?.freshness_status !== "dead"
  ).length;
  const feedsCount = meta?.tracked_events?.filter(t => t.is_active).length ?? 0;

  return (
    <div className="rounded-xl border border-white/8 bg-[#0f1420] overflow-hidden mb-3">
      {/* Identity row — left: artwork + center: identity + right: tracking stats */}
      <div className="flex items-center gap-4 px-4 py-3 border-b border-white/6"
        style={{ background: `linear-gradient(90deg, ${gradient[0]}12, transparent 60%)` }}>
        {/* Artwork */}
        <div className="flex-shrink-0 w-20 h-20 rounded-xl overflow-hidden"
          style={{ background: `linear-gradient(145deg, ${gradient[0]}, ${gradient[1]})` }}>
          {artworkUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={artworkUrl} alt={artist ?? title}
              className="w-full h-full object-cover object-top"
              onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-xl font-black text-white/60 select-none">
              {(artist ?? title).slice(0, 1).toUpperCase()}
            </div>
          )}
        </div>
        {/* Identity — only show artist label when it differs from event title */}
        <div className="flex-1 min-w-0">
          {artist && artist !== title && <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold truncate mb-0.5">{artist}</p>}
          <Link href={`/events/${event.event_id}`}>
            <span className="text-base font-bold text-white truncate block hover:text-blue-300 transition-colors">{title}</span>
          </Link>
          <div className="flex items-center gap-2.5 mt-1 flex-wrap">
            {venue && <span className="text-xs text-slate-500 truncate">{venue}</span>}
            {dateLabel && <span className="text-xs text-slate-500">{dateLabel}</span>}
            {daysOut != null && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                style={{ color: aColors.text, background: aColors.bg + "50", border: `1px solid ${aColors.border}` }}>
                {daysOut <= 0 ? "Today" : daysOut === 1 ? "Tomorrow" : `${daysOut}d away`}
              </span>
            )}
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border"
              style={{ color: aColors.text, borderColor: aColors.border + "80", background: aColors.bg + "25" }}>
              {action}
            </span>
          </div>
        </div>
        {/* RIGHT — Market Health chips + action buttons */}
        <div className="hidden sm:flex items-center gap-4 flex-shrink-0">
          {/* Market Health */}
          <div className="text-right space-y-1">
            <p className="text-[9px] text-slate-600 uppercase tracking-wider mb-1">Marketplace Freshness</p>
            {meta?.marketplace_freshness
              ? Object.entries(meta.marketplace_freshness)
                  .filter(([slug]) => ['stubhub', 'tickpick', 'gametime', 'vividseats'].includes(slug))
                  .map(([slug, f]) => {
                  const fEntry = f as { freshness_status: string; age_minutes: number | null };
                  const status = fEntry.freshness_status;
                  const age = fEntry.age_minutes;
                  const ageStr = age == null ? null : age < 60 ? `${age}m` : `${Math.round(age / 60)}h`;
                  const cfg: Record<string, { dot: string; text: string }> = {
                    fresh:   { dot: "bg-emerald-400", text: "text-emerald-400" },
                    late:    { dot: "bg-amber-400",   text: "text-amber-400"  },
                    stale:   { dot: "bg-orange-500",  text: "text-orange-400" },
                    dead:    { dot: "bg-red-500",     text: "text-red-400"    },
                    no_data: { dot: "bg-slate-500",   text: "text-slate-400"  },
                  };
                  const c = cfg[status] ?? { dot: "bg-slate-600", text: "text-slate-500" };
                  return (
                    <div key={slug} className="flex items-center gap-1 justify-end">
                      <span className="text-[9px] text-slate-500 capitalize">{slug}</span>
                      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${c.dot}`} />
                      <span className={`text-[9px] font-semibold ${c.text} w-7 text-left tabular-nums`}>{ageStr ?? status}</span>
                    </div>
                  );
                })
              : <p className="text-[9px] text-slate-600">No feeds</p>
            }
          </div>
          {/* Action buttons */}
          <div className="flex flex-col gap-1">
            <button onClick={onToggleWatch} title={isWatched ? "Unwatch" : "Watch"}
              className={cn("inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg border transition-all",
                isWatched ? "border-blue-500/40 bg-blue-500/10 text-blue-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300")}>
              <Bookmark size={9} className={isWatched ? "fill-blue-400" : ""} /> {isWatched ? "Watching" : "Watch"}
            </button>
            <button onClick={onTogglePin} title={isPinned ? "Unpin" : "Pin as headline"}
              className={cn("inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg border transition-all",
                isPinned ? "border-amber-500/40 bg-amber-500/10 text-amber-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300")}>
              <Pin size={9} className={isPinned ? "fill-amber-400" : ""} /> Pin
            </button>
          </div>
        </div>
      </div>

      {/* Intelligence columns */}
      <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-white/6"
        style={{ gridTemplateColumns: "1fr 1.2fr 1fr" }}>

        {/* Col 1: Current Market */}
        <div className="p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">Current Market</p>
            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded border border-white/10 text-slate-500 bg-white/3">24H ▾</span>
          </div>
          <div className="space-y-0">
            {[
              { label: "Low",    val: fmt$$(event.price?.low_ask),    cls: "text-emerald-300" },
              { label: "Median", val: fmt$$(event.price?.median_ask), cls: "text-white" },
              { label: "High",   val: fmt$$(event.price?.high_ask),   cls: "text-slate-300" },
            ].map(({ label, val, cls }) => (
              <div key={label} className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0">
                <span className="text-xs text-slate-400">{label}</span>
                <span className={`text-sm font-bold tabular-nums ${cls}`}>{val ?? "—"}</span>
              </div>
            ))}
            <div className="flex items-center justify-between py-1.5">
              <span className="text-xs text-slate-400">Inventory</span>
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-bold text-slate-200 tabular-nums">
                  {fmtNum(event.inventory?.total_listings) ?? "—"}
                </span>
                {invDelta != null && (
                  <span className={`text-[11px] font-semibold tabular-nums ${invDelta > 0 ? "text-emerald-400" : "text-red-400"}`}>
                    ({invDelta > 0 ? "+" : ""}{invDelta})
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Col 2: Absorption */}
        <div className="p-4 bg-white/[0.02]">
          <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mb-2">Absorption</p>
          <div className="mb-2 pb-2 border-b border-white/8">
            <p className="text-[10px] text-slate-500 mb-0.5">Estimated Avg Sale Price</p>
            <p className="text-base font-black text-amber-300 tabular-nums">—</p>
            <p className="text-[10px] text-slate-600 italic">Tracking</p>
          </div>
          <div className="space-y-0">
            {["Tickets Sold", "24H Sold", "7D Sold", "Since Tracking"].map(label => (
              <div key={label} className="flex items-center justify-between py-1 border-b border-white/5 last:border-0">
                <span className="text-xs text-slate-400">{label}</span>
                <span className="text-[11px] text-slate-600">—</span>
              </div>
            ))}
          </div>
        </div>

        {/* Col 3: Seller Behavior */}
        <div className="p-4">
          <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mb-2">Seller Behavior</p>
          <div className="space-y-0">
            {["Relist Price Change", "Price Drops", "Repriced Listings", "Seller Mood"].map(label => (
              <div key={label} className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0">
                <span className="text-xs text-slate-400">{label}</span>
                <span className="text-[11px] text-slate-600">—</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Portfolio Snapshot ────────────────────────────────────────────────────────
// Compact aggregate strip — below the featured event hero, NOT the hero itself.
function PortfolioSnapshot({ events }: { events: EventSummary[] }) {
  const floors    = events.map(e => e.price?.low_ask).filter((v): v is number => v != null);
  const highs     = events.map(e => e.price?.high_ask).filter((v): v is number => v != null);
  const invTotals = events.map(e => e.inventory?.total_listings).filter((v): v is number => v != null);
  const invDeltas = events.map(e => e.changes?.h24?.inventory_delta).filter((v): v is number => v != null);
  const aggLow    = floors.length > 0 ? Math.min(...floors) : null;
  const aggHigh   = highs.length > 0 ? Math.max(...highs) : null;
  const totalInv  = invTotals.reduce((s, v) => s + v, 0);
  const totalDelta = invDeltas.length > 0 ? invDeltas.reduce((s, v) => s + v, 0) : null;
  const signalDist: Record<string, number> = {};
  events.forEach(e => {
    const a = signalToAction(e.signal);
    signalDist[a] = (signalDist[a] ?? 0) + 1;
  });
  const signalEntries = Object.entries(signalDist).sort((a, b) => b[1] - a[1]);

  return (
    <div className="rounded-xl border border-white/6 bg-[#08090e] px-4 py-2.5 flex items-center gap-5 flex-wrap mb-4">
      <span className="text-[10px] text-white/20 uppercase tracking-widest font-bold flex-shrink-0">Portfolio Snapshot</span>
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-slate-600">Events</span>
        <span className="text-xs font-bold text-slate-400">{events.length}</span>
      </div>
      {totalInv > 0 && (
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-slate-600">Inventory</span>
          <span className="text-xs font-bold text-slate-400 tabular-nums">{fmtNum(totalInv)}</span>
          {totalDelta != null && (
            <span className={`text-[10px] font-semibold tabular-nums ${totalDelta > 0 ? "text-emerald-500" : "text-red-500"}`}>
              ({totalDelta > 0 ? "+" : ""}{totalDelta})
            </span>
          )}
        </div>
      )}
      {aggLow != null && (
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-slate-600">Range</span>
          <span className="text-xs font-bold text-slate-400 tabular-nums">{fmt$$(aggLow)}–{fmt$$(aggHigh)}</span>
        </div>
      )}
      <div className="flex items-center gap-1.5 flex-wrap ml-auto">
        {signalEntries.map(([act, cnt]) => {
          const c = actionColors(act as Parameters<typeof actionColors>[0]);
          return (
            <span key={act} className="text-[10px] font-bold px-1.5 py-0.5 rounded-full"
              style={{ color: c.text, background: c.bg + "40", border: `1px solid ${c.border}` }}>
              {act} ×{cnt}
            </span>
          );
        })}
      </div>
    </div>
  );
}

// ── Artist / Team group row ───────────────────────────────────────────────────
function EventGroup({
  groupKey,
  events,
  metas,
  depths,
  onHide,
  onSelect,
  selectedId,
  watchedIds,
  onToggleWatch,
  onNflClick,
  nflAudioState,
}: {
  groupKey: string;
  events: EventSummary[];
  metas: MetaMap;
  depths: Record<number, number | null>;
  onHide: (id: number) => void;
  onSelect: (id: number) => void;
  selectedId: number | null;
  watchedIds: Set<number>;
  onToggleWatch: (id: number) => void;
  onNflClick?: () => void;
  nflAudioState?: {
    playing: boolean; blocked: boolean; muted: boolean; errorMsg: string | null;
    onPlay: () => void; onPause: () => void; onToggleMute: () => void;
  };
}) {
  const [collapsed, setCollapsed] = useState(true);
  const router = useRouter();
  const isSingle = events.length === 1;

  const topAction = signalToAction(events[0]?.signal);
  const topColors = actionColors(topAction);
  const lowestPrice = events.reduce<number | null>((min, e) => {
    const p = e.price?.low_ask;
    return p != null ? (min == null ? p : Math.min(min, p)) : min;
  }, null);
  const medianPrices = events.map(e => e.price?.median_ask).filter((p): p is number => p != null);
  const medianRange = medianPrices.length > 0
    ? medianPrices.length === 1
      ? fmt$$(medianPrices[0])
      : `${fmt$$(Math.min(...medianPrices))}–${fmt$$(Math.max(...medianPrices))}`
    : null;
  const maxDepth = events.reduce<number | null>((max, e) => {
    const d = depths[e.event_id];
    return d != null ? (max == null ? d : Math.max(max, d)) : max;
  }, null);

  // Inventory delta across all events in group
  const totalInvDelta = events.reduce<number | null>((sum, e) => {
    const d = e.changes?.h24?.inventory_delta;
    return d != null ? (sum ?? 0) + d : sum;
  }, null);

  const firstMeta = metas[events[0]?.event_id];
  const gradient = getEventGradient(firstMeta?.artist, firstMeta?.title ?? events[0]?.title ?? groupKey);
  const artworkUrl = useArtistImage(firstMeta?.artist ?? groupKey, firstMeta?.title);
  const spotify = getSpotifyData(firstMeta?.artist ?? groupKey);

  // Aggregate marketplace floors across all events in group
  const mpAgg: Record<string, number | null> = {};
  for (const e of events) {
    const prices = metas[e.event_id]?.all_marketplace_prices ?? metas[e.event_id]?.marketplace_prices ?? {};
    for (const [slug, price] of Object.entries(prices)) {
      if (price == null) continue;
      if (mpAgg[slug] == null || price < (mpAgg[slug] as number)) mpAgg[slug] = price;
    }
  }
  const mpEntries = Object.entries(mpAgg)
    .filter(([, p]) => p != null)
    .sort(([, a], [, b]) => (a as number) - (b as number));

  // Is any event in group watched?
  const groupWatched = events.some((e) => watchedIds.has(e.event_id));

  return (
    <div className="mb-2.5">
      {/* Collapsed summary row */}
      <div className="relative">
        <button
          onClick={() => {
            if (isSingle) {
              router.push(`/events/${events[0].event_id}`);
              return;
            }
            setCollapsed(v => !v);
            if (isNflEvent(groupKey, firstMeta?.artist)) onNflClick?.();
          }}
          className="w-full text-left rounded-xl border border-white/10 overflow-hidden transition-all hover:border-white/18 focus:outline-none relative"
          style={{ background: gradientBg(gradient, "low"), backdropFilter: "blur(8px)" }}
        >
          <div className="relative flex items-center gap-4 px-5 py-6 min-h-[120px]">
            {/* Artist avatar thumbnail */}
            <div className="flex-shrink-0 relative">
              {artworkUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={artworkUrl}
                  alt={groupKey}
                  className="w-20 h-20 rounded-xl object-cover object-top border-2 border-white/20 shadow-lg"
                  loading="lazy"
                  onError={e => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              ) : (
                <div
                  className="w-20 h-20 rounded-xl border-2 border-white/15 flex items-center justify-center text-2xl font-black shadow-lg"
                  style={{ background: `linear-gradient(135deg, ${gradient[0]}, ${gradient[1]})`, color: "rgba(255,255,255,0.85)" }}
                >
                  {groupKey.slice(0, 1).toUpperCase()}
                </div>
              )}
              {/* Spotify indicator dot */}
              {spotify.spotifyArtistUrl && (
                <a
                  href={spotify.spotifyArtistUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={e => e.stopPropagation()}
                  className="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full bg-[#1db954] border border-[#0e1117] flex items-center justify-center"
                  title="Open in Spotify"
                >
                  <Music size={8} className="text-black" />
                </a>
              )}
            </div>

            {/* identity + stats — two readable lines */}
            <div className="flex-1 min-w-0">
              {/* LINE 1: name, signal badge, event count, history */}
              <div className="flex items-center gap-2.5 mb-2">
                <p className="text-lg font-bold text-slate-100 truncate">{groupKey}</p>
                <span
                  className="text-[11px] font-black tracking-widest px-2.5 py-0.5 rounded-md border flex-shrink-0"
                  style={{ color: topColors.text, background: topColors.bg, borderColor: topColors.border }}
                >
                  {topAction}
                </span>
                <span className="text-xs text-slate-500 flex-shrink-0">{events.length} {events.length === 1 ? "event" : "events"}</span>
                {maxDepth != null && (
                  <span className={`text-xs flex-shrink-0 ${maxDepth >= 7 ? "text-emerald-500" : "text-amber-500"}`}>
                    {maxDepth >= 1 ? `${Math.round(maxDepth)}d history` : "live only"}
                  </span>
                )}
              </div>
              {/* LINE 2: floor, median, inventory, best marketplace */}
              <div className="flex items-center gap-5 flex-wrap">
                {lowestPrice != null && (
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Low</span>
                    <span className="text-base font-bold text-emerald-300 tabular-nums">{fmt$$(lowestPrice)}</span>
                  </div>
                )}
                {medianRange && (
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Median</span>
                    <span className="text-base text-slate-300 tabular-nums font-semibold">{medianRange}</span>
                  </div>
                )}
                {totalInvDelta != null && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Inv Δ</span>
                    <span className={`text-sm font-bold flex items-center gap-0.5 tabular-nums ${totalInvDelta > 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {totalInvDelta > 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                      {totalInvDelta > 0 ? "+" : ""}{totalInvDelta}
                    </span>
                  </div>
                )}
                {mpEntries.length > 0 && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Best</span>
                    <span className="text-sm font-bold text-blue-400 uppercase">{MP_SHORT[mpEntries[0][0]] ?? mpEntries[0][0]}</span>
                    <span className="text-sm font-semibold text-slate-200 tabular-nums">{fmt$$(mpEntries[0][1] as number)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* right: marketplace snapshot */}
            <div className="flex items-center gap-3 flex-shrink-0">
              {/* Marketplace snapshot — branded badges */}
              {mpEntries.length > 0 && (
                <div className="hidden md:flex items-center gap-1.5">
                  {(["stubhub", "tickpick", "gametime", "vividseats"] as const).map((slug) => {
                    const price = mpAgg[slug];
                    const b = getBrand(slug);
                    return (
                      <div key={slug} className="flex flex-col items-center rounded-lg px-2.5 py-2 border min-w-[52px]"
                        style={{ background: b.bg, borderColor: b.border }}>
                        <span className="text-[10px] font-black uppercase tracking-wide" style={{ color: b.textColor }}>{b.short}</span>
                        <span className="text-sm text-white/80 tabular-nums font-bold mt-0.5">
                          {price != null ? fmt$$(price) : "—"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}

              {!isSingle && (
                <span className="text-slate-600">
                  {collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                </span>
              )}
            </div>
          </div>
        </button>

        {/* Watch toggle — outside button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            // Toggle watch on all events in group
            events.forEach((ev) => onToggleWatch(ev.event_id));
          }}
          className="absolute right-9 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-white/10 transition-colors z-10"
          title={groupWatched ? "Remove from watchlist" : "Add to watchlist"}
        >
          <Bookmark
            size={12}
            className={groupWatched ? "text-blue-400 fill-blue-400" : "text-slate-600 hover:text-slate-300"}
          />
        </button>
      </div>

      {/* Intelligence row — readable text strip */}
      <div className="flex items-center gap-5 px-5 py-2.5 rounded-b-xl border border-t-0 border-white/5 bg-[#08090e] -mt-px flex-wrap">
        <span className="text-[10px] text-white/25 uppercase tracking-widest font-bold flex-shrink-0">Intel</span>
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-slate-600 uppercase tracking-wider">Trend</span>
          <span className="text-xs text-amber-500/60 italic">Pending</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-slate-600 uppercase tracking-wider">Buy Window</span>
          <span className="text-xs text-amber-500/60 italic">Pending</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-slate-600 uppercase tracking-wider">Signal</span>
          <span className="text-xs text-amber-500/60 italic">Pending</span>
        </div>
      </div>

      {/* NFL audio chip — inline, always visible for NFL groups */}
      {isNflEvent(groupKey, firstMeta?.artist) && nflAudioState && (
        <div className="flex items-center gap-2.5 px-4 py-2.5 mt-1 rounded-xl border border-amber-500/20 bg-amber-500/5">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${nflAudioState.playing ? "bg-amber-400 animate-pulse" : nflAudioState.errorMsg ? "bg-red-400" : "bg-amber-400/40"}`} />
          <span className="text-[10px] font-bold text-white/50 uppercase tracking-widest">NFL Theme</span>
          {nflAudioState.errorMsg ? (
            <span className="text-[10px] text-red-400/80">{nflAudioState.errorMsg}</span>
          ) : nflAudioState.playing ? (
            <span className="text-[10px] text-amber-400 font-medium">Playing</span>
          ) : nflAudioState.blocked ? (
            <button onClick={nflAudioState.onPlay} className="text-[10px] text-amber-400 border border-amber-500/30 rounded px-2 py-0.5 bg-amber-500/8 hover:bg-amber-500/15 transition-colors">Tap to play</button>
          ) : (
            <span className="text-[10px] text-white/25">Click row to play</span>
          )}
          <div className="ml-auto flex items-center gap-1">
            <button onClick={nflAudioState.playing ? nflAudioState.onPause : nflAudioState.onPlay}
              className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-white/40 hover:text-white">
              {nflAudioState.playing ? <Pause size={11} /> : <Play size={11} />}
            </button>
            <button onClick={nflAudioState.onToggleMute}
              className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-white/40 hover:text-white">
              {nflAudioState.muted ? <VolumeX size={11} /> : <Volume2 size={11} />}
            </button>
          </div>
        </div>
      )}

      {/* Expanded event cards */}
      {!collapsed && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-3">
          {events.map((event) => (
            <EventCard
              key={event.event_id}
              event={event}
              meta={metas[event.event_id]}
              dataDepthDays={depths[event.event_id]}
              onHide={onHide}
              isSelected={event.event_id === selectedId}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Dashboard page ────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [metas, setMetas] = useState<MetaMap>({});
  const [depths, setDepths] = useState<Record<number, number | null>>({});
  const [sort, setSort] = useState<SortKey>("opportunity");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showHidden, setShowHidden] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { hiddenEvents, hide, unhide, mounted } = useHiddenEvents();
  const { watched, toggle: toggleWatch } = useWatchlist();
  const { pinnedId, isPinned, toggle: togglePin } = useHeadlineEvent();
  const nflAudio = useNflAudio();

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.events.list();
      const evts = data.events ?? [];
      setEvents(evts);

      if (selectedId === null && evts.length > 0) {
        const best = [...evts].sort((a, b) => (b.opportunity_score ?? 0) - (a.opportunity_score ?? 0))[0];
        setSelectedId(best.event_id);
      }

      const metaResults = await Promise.allSettled(evts.map((e) => api.events.meta(e.event_id)));
      const metaMap: MetaMap = {};
      evts.forEach((e, i) => {
        const r = metaResults[i];
        if (r.status === "fulfilled") {
          metaMap[e.event_id] = r.value;
        }
      });
      setMetas(metaMap);

      const depthMap: Record<number, number | null> = {};
      evts.forEach((e) => {
        depthMap[e.event_id] = e.history_hours != null ? e.history_hours / 24 : null;
      });
      setDepths(depthMap);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const visible = useMemo(() => {
    const base = mounted && !showHidden
      ? events.filter((e) => !hiddenEvents.has(e.event_id))
      : events;

    return [...base].sort((a, b) => {
      if (sort === "opportunity") return (b.opportunity_score ?? 0) - (a.opportunity_score ?? 0);
      if (sort === "signal") return SIGNAL_ORDER.indexOf(a.signal) - SIGNAL_ORDER.indexOf(b.signal);
      if (sort === "price") return (a.price?.low_ask ?? 999999) - (b.price?.low_ask ?? 999999);
      if (sort === "inventory") return (a.inventory?.total_listings ?? 99999) - (b.inventory?.total_listings ?? 99999);
      if (sort === "seller_drop") return (b.changes?.h24?.inventory_delta ?? 0) - (a.changes?.h24?.inventory_delta ?? 0);
      if (sort === "closest") {
        const da2 = metas[a.event_id]?.event_date ?? "";
        const db2 = metas[b.event_id]?.event_date ?? "";
        return da2.localeCompare(db2);
      }
      const da = metas[a.event_id]?.event_date ?? "";
      const db = metas[b.event_id]?.event_date ?? "";
      return da.localeCompare(db);
    });
  }, [events, metas, sort, hiddenEvents, showHidden, mounted]);

  const groups = useMemo(() => {
    const map: Record<string, EventSummary[]> = {};
    for (const e of visible) {
      const meta = metas[e.event_id];
      const key = extractGroupKey(meta?.artist, meta?.title ?? e.title);
      if (!map[key]) map[key] = [];
      map[key].push(e);
    }
    return Object.entries(map).sort(([, ae], [, be]) => {
      const aScore = Math.max(...ae.map(e => e.opportunity_score ?? 0));
      const bScore = Math.max(...be.map(e => e.opportunity_score ?? 0));
      return bScore - aScore;
    });
  }, [visible, metas]);

  // Prefer pinned event as headline; fall back to selected or best-score
  const headlineId = pinnedId ?? selectedId;
  const selectedEvent = useMemo(
    () => events.find((e) => e.event_id === headlineId) ?? events[0] ?? null,
    [events, headlineId],
  );

  const hiddenCount = mounted ? hiddenEvents.size : 0;

  return (
    <div>
      {/* UI CLOSEOUT BUILD MARKER — remove after screenshot verification */}
      <div className="fixed top-2 right-2 z-50 text-[9px] font-mono bg-amber-400 text-black px-2 py-0.5 rounded opacity-80 pointer-events-none select-none">
        UI BUILD {new Date().toISOString().slice(0,16).replace("T"," ")}
      </div>

      {/* page header */}
      <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-100">Active Markets</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {loading ? "Loading…" : `${events.length} events · ${groups.length} artists`}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg border border-white/7 text-xs text-slate-500 bg-white/[0.01]">
            <span className="text-slate-600 select-none">Sort</span>
            <select
              value={sort}
              onChange={e => setSort(e.target.value as SortKey)}
              className="bg-transparent text-slate-300 text-xs outline-none cursor-pointer hover:text-slate-100 transition-colors"
            >
              <option value="opportunity">Opportunity</option>
              <option value="price">Lowest Price</option>
              <option value="inventory">Lowest Inventory</option>
              <option value="seller_drop">Highest Seller Drop</option>
              <option value="closest">Closest Event</option>
              <option value="date">Date</option>
              <option value="signal">Signal</option>
            </select>
          </div>
          {hiddenCount > 0 && (
            <button
              onClick={() => setShowHidden(v => !v)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/7 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors"
            >
              <Eye size={12} />
              {showHidden ? "Hide hidden" : `${hiddenCount} hidden`}
            </button>
          )}
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/7 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors disabled:opacity-40"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-4">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      {loading && events.length === 0 && (
        <div className="space-y-6">
          <div className="h-64 rounded-2xl border border-white/5 bg-[#161b27] animate-pulse" />
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-16 rounded-xl border border-white/5 bg-[#161b27] animate-pulse" />
            ))}
          </div>
        </div>
      )}

      {!loading && visible.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-slate-500">
          <TrendingUp size={32} className="mb-3 opacity-30" />
          <p className="text-sm">No events</p>
        </div>
      )}

      {visible.length > 0 && (
        <>
          {/* Featured Event Hero — one event, event-level intelligence */}
          {selectedEvent && (
            <FeaturedEventHero
              event={selectedEvent}
              meta={metas[selectedEvent.event_id]}
              isWatched={watched.has(selectedEvent.event_id)}
              onToggleWatch={() => toggleWatch(selectedEvent.event_id)}
              isPinned={isPinned(selectedEvent.event_id)}
              onTogglePin={() => togglePin(selectedEvent.event_id)}
            />
          )}
          {/* Portfolio Snapshot — compact aggregate strip below hero */}
          <PortfolioSnapshot events={visible} />

          {/* Market groups */}
          {groups.map(([groupKey, groupEvents]) => (
            <EventGroup
              key={groupKey}
              groupKey={groupKey}
              events={groupEvents}
              metas={metas}
              depths={depths}
              onHide={(id) => { if (showHidden) unhide(id); else hide(id); }}
              onSelect={(id) => setSelectedId(id)}
              selectedId={selectedId}
              watchedIds={watched}
              onToggleWatch={toggleWatch}
              onNflClick={nflAudio.triggerFromUserAction}
              nflAudioState={{
                playing: nflAudio.playing,
                blocked: nflAudio.blocked,
                muted: nflAudio.muted,
                errorMsg: nflAudio.errorMsg,
                onPlay: nflAudio.play,
                onPause: nflAudio.pause,
                onToggleMute: () => nflAudio.setMuted(!nflAudio.muted),
              }}
            />
          ))}
        </>
      )}

    </div>
  );
}
