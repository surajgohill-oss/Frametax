"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Bookmark, BookmarkX, Calendar, TrendingUp, TrendingDown, Minus,
  AlertCircle, Pin, PinOff, Archive, EyeOff, Music, ArrowUpRight,
} from "lucide-react";
import { format, parseISO, differenceInDays } from "date-fns";
import { api } from "@/lib/api";
import type { EventSummary, EventMeta } from "@/lib/types";
import { fmt$$, fmtPct, fmtNum, signalToAction, actionColors, cn, parseEventDate } from "@/lib/utils";
import { getEventGradient, gradientBg, getSpotifyData } from "@/lib/entityimages";
import { useArtistImage } from "@/hooks/useArtistImage";
import { useWatchlist } from "@/hooks/useWatchlist";
import { useHeadlineEvent } from "@/hooks/useHeadlineEvent";
import { useArchivedEvents } from "@/hooks/useArchivedEvents";
import { useHiddenEvents } from "@/hooks/useHiddenEvents";

const MP_SHORT: Record<string, string> = {
  stubhub: "SH", gametime: "GT", tickpick: "TP", vividseats: "VS",
};
const MP_COLOR: Record<string, string> = {
  stubhub: "#1c64f2", gametime: "#0ea5e9", tickpick: "#7c3aed", vividseats: "#059669",
};

function DeltaChip({ pct, abs }: { pct?: number | null; abs?: number | null }) {
  const n = pct ?? abs ?? null;
  if (n == null) return <span className="text-white/25 text-[10px]">—</span>;
  const up = n > 0;
  const Icon = up ? TrendingUp : n < 0 ? TrendingDown : Minus;
  return (
    <span className={`inline-flex items-center gap-0.5 text-[10px] font-semibold tabular-nums ${up ? "text-emerald-400" : n < 0 ? "text-red-400" : "text-white/40"}`}>
      <Icon size={9} />{pct != null ? fmtPct(pct) : (n > 0 ? `+${n}` : String(n))}
    </span>
  );
}

export default function WatchlistPage() {
  const { watched, remove, mounted }           = useWatchlist();
  const { pinnedId, pin, clear: clearPin }     = useHeadlineEvent();
  const { archivedEvents, toggle: toggleArchive } = useArchivedEvents();
  const { hiddenEvents,   toggle: toggleHide } = useHiddenEvents();
  const [events, setEvents]   = useState<EventSummary[]>([]);
  const [metas, setMetas]     = useState<Record<number, EventMeta>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!mounted) return;
    if (watched.size === 0) { setLoading(false); return; }
    async function loadWatched() {
      setLoading(true);
      try {
        const data = await api.events.list();
        const watchedEvents = (data.events ?? []).filter((e) => watched.has(e.event_id));
        setEvents(watchedEvents);
        const metaResults = await Promise.allSettled(watchedEvents.map((e) => api.events.meta(e.event_id)));
        const metaMap: Record<number, EventMeta> = {};
        watchedEvents.forEach((e, i) => {
          const r = metaResults[i];
          if (r.status === "fulfilled") metaMap[e.event_id] = r.value;
        });
        setMetas(metaMap);
      } catch {}
      setLoading(false);
    }
    loadWatched();
  }, [mounted, watched.size]); // eslint-disable-line react-hooks/exhaustive-deps

  const pinnedEvent = events.find((e) => e.event_id === pinnedId) ?? null;
  // Hero: pinned event if in watchlist, otherwise best by opportunity_score
  const heroEvent = pinnedEvent ?? (
    events.length > 0
      ? events.reduce((best, e) =>
          (e.opportunity_score ?? 0) > (best.opportunity_score ?? 0) ? e : best
        , events[0])
      : null
  );
  const otherEvents = events.filter((e) => e.event_id !== heroEvent?.event_id);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Bookmark size={16} className="text-slate-400" />
            <h1 className="text-lg font-semibold text-white">Watchlist</h1>
            {mounted && watched.size > 0 && (
              <span className="text-xs text-slate-500 bg-white/5 rounded-full px-2 py-0.5">
                {watched.size} {watched.size === 1 ? "event" : "events"}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500">Monitored portfolio — your tracked markets.</p>
        </div>
      </div>

      {!mounted || loading ? (
        <div className="space-y-4">
          <div className="h-48 rounded-2xl border border-white/5 bg-[#161b27] animate-pulse" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-52 rounded-xl border border-white/5 bg-[#161b27] animate-pulse" />
            ))}
          </div>
        </div>
      ) : watched.size === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center space-y-3">
          <BookmarkX size={36} className="text-white/15" />
          <p className="text-slate-400 font-medium">No events in your watchlist</p>
          <p className="text-sm text-slate-600 max-w-xs">
            Bookmark events from the <Link href="/" className="text-blue-400 hover:underline">dashboard</Link>{" "}
            using the <Bookmark size={11} className="inline" /> icon.
          </p>
        </div>
      ) : events.length === 0 ? (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
          <AlertCircle size={14} />
          Bookmarked events are no longer in active tracking. They may have completed or been removed.
        </div>
      ) : (
        <>
          {/* ── Hero card — pinned or best event ── */}
          {heroEvent && (
            <HeadlineCard
              event={heroEvent}
              meta={metas[heroEvent.event_id]}
              isPinned={!!pinnedEvent}
              onClearPin={pinnedEvent ? clearPin : () => {}}
              onRemove={() => remove(heroEvent.event_id)}
              isArchived={archivedEvents.has(heroEvent.event_id)}
              onToggleArchive={() => toggleArchive(heroEvent.event_id)}
            />
          )}

          {/* ── Portfolio grid ── */}
          {otherEvents.length > 0 && (
            <>
              {heroEvent && (
                <p className="text-[10px] text-slate-600 uppercase tracking-widest">Other watched events</p>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {otherEvents.map((event) => (
                  <WatchlistCard
                    key={event.event_id}
                    event={event}
                    meta={metas[event.event_id]}
                    isPinned={false}
                    isArchived={archivedEvents.has(event.event_id)}
                    isHidden={hiddenEvents.has(event.event_id)}
                    onRemove={() => remove(event.event_id)}
                    onPin={() => pin(event.event_id)}
                    onToggleArchive={() => toggleArchive(event.event_id)}
                    onToggleHide={() => toggleHide(event.event_id)}
                  />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

// ── Headline Event Hero — compact 3-col intelligence model ────────────────────
// Identical structure to FeaturedEventHero on Active Markets page.
// Target height 180–240px. Signal chip is small secondary only (no dominant badge).
function HeadlineCard({
  event, meta, onClearPin, onRemove, isArchived, onToggleArchive, isPinned = true,
}: {
  event: EventSummary;
  meta: EventMeta | undefined;
  onClearPin: () => void;
  onRemove: () => void;
  isArchived: boolean;
  onToggleArchive: () => void;
  isPinned?: boolean;
}) {
  const title      = meta?.title ?? event.title;
  const venue      = meta?.venue_name;
  const dateStr    = meta?.event_date;
  const artist     = meta?.artist;
  const gradient   = getEventGradient(artist, title);
  const artworkUrl = useArtistImage(artist, title);
  const action     = signalToAction(event.signal);
  const colors     = actionColors(action);
  const mpPrices   = meta?.all_marketplace_prices ?? meta?.marketplace_prices ?? {};
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

  const trackingSince = (() => {
    const ca = meta?.created_at;
    if (!ca) return null;
    try {
      const d = parseISO(ca);
      const days = Math.round((Date.now() - d.getTime()) / 86400000);
      return { formatted: format(d, "MMM d, yyyy"), days };
    } catch { return null; }
  })();

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

  const mpEntries = (Object.entries(mpPrices) as [string, number | null][])
    .filter(([, p]) => p != null)
    .sort(([, a], [, b]) => (a as number) - (b as number));

  return (
    <div className="rounded-xl border border-white/8 bg-[#0f1420] overflow-hidden">
      {/* Identity row */}
      <div className="flex items-center gap-4 px-4 py-3 border-b border-white/6"
        style={{ background: `linear-gradient(90deg, ${gradient[0]}12, transparent 60%)` }}>
        {/* Compact artwork */}
        <div className="flex-shrink-0 w-14 h-14 rounded-xl overflow-hidden"
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

        {/* Identity */}
        <div className="flex-1 min-w-0">
          {/* Pin / Best Watched label */}
          <div className="flex items-center gap-1.5 mb-0.5">
            {isPinned ? (
              <><Pin size={8} className="text-amber-400" />
              <span className="text-[8px] font-bold text-amber-400 uppercase tracking-widest">Headline</span></>
            ) : (
              <span className="text-[8px] font-bold text-blue-400 uppercase tracking-widest">Best Watched</span>
            )}
          </div>
          {artist && artist !== title && <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold truncate">{artist}</p>}
          <Link href={`/events/${event.event_id}`}>
            <span className="text-base font-bold text-white truncate block hover:text-blue-300 transition-colors">{title}</span>
          </Link>
          <div className="flex items-center gap-2.5 mt-0.5 flex-wrap">
            {venue && <span className="text-xs text-slate-500 truncate">{venue}</span>}
            {dateLabel && <span className="text-xs text-slate-500">{dateLabel}</span>}
            {daysOut != null && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                style={{ color: colors.text, background: colors.bg + "50", border: `1px solid ${colors.border}` }}>
                {daysOut <= 0 ? "Today" : daysOut === 1 ? "Tomorrow" : `${daysOut}d away`}
              </span>
            )}
            {/* BUY/WAIT/MONITOR — small chip only */}
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border"
              style={{ color: colors.text, borderColor: colors.border + "80", background: colors.bg + "25" }}>
              {action}
            </span>
          </div>
        </div>

        {/* RIGHT — Market Health chips + action buttons */}
        <div className="hidden sm:flex items-center gap-3 flex-shrink-0">
          <div className="text-right space-y-1">
            <p className="text-[9px] text-slate-600 uppercase tracking-wider mb-1">Market Health</p>
            {meta?.marketplace_freshness
              ? Object.entries(meta.marketplace_freshness).map(([slug, f]) => {
                  const fEntry = f as { freshness_status: string; age_minutes: number | null };
                  const status = fEntry.freshness_status;
                  const age = fEntry.age_minutes;
                  const ageStr = age == null ? null : age < 60 ? `${age}m` : `${Math.round(age / 60)}h`;
                  const cfg: Record<string, { dot: string; text: string }> = {
                    fresh: { dot: "bg-emerald-400", text: "text-emerald-400" },
                    late:  { dot: "bg-amber-400",   text: "text-amber-400"  },
                    stale: { dot: "bg-orange-500",  text: "text-orange-400" },
                    dead:  { dot: "bg-red-500",     text: "text-red-400"    },
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
          <div className="flex flex-col gap-1">
            {isPinned && (
              <button onClick={onClearPin} title="Unpin"
                className="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg border border-amber-500/40 bg-amber-500/10 text-amber-400 transition-colors">
                <PinOff size={9} /> Unpin
              </button>
            )}
            <button onClick={onToggleArchive} title={isArchived ? "Restore" : "Archive"}
              className={cn("inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg border transition-all",
                isArchived ? "border-amber-500/40 bg-amber-500/10 text-amber-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300")}>
              <Archive size={9} /> {isArchived ? "Restore" : "Archive"}
            </button>
            <button onClick={onRemove} title="Remove from watchlist"
              className="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg border border-blue-500/40 bg-blue-500/10 text-blue-400 transition-colors">
              <Bookmark size={9} className="fill-blue-400" /> Watching
            </button>
          </div>
        </div>
      </div>

      {/* Intelligence columns — 3-col */}
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
          {/* Marketplace strip under Current Market */}
          {mpEntries.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-3 pt-2.5 border-t border-white/5">
              {mpEntries.slice(0, 4).map(([slug, price], i) => (
                <div key={slug} className="flex items-center gap-1 rounded px-1.5 py-0.5"
                  style={{ background: (MP_COLOR[slug] ?? "#888") + "15", border: `1px solid ${(MP_COLOR[slug] ?? "#888")}25` }}>
                  <span className="text-[9px] font-black uppercase" style={{ color: MP_COLOR[slug] ?? "#aaa" }}>{MP_SHORT[slug] ?? slug.slice(0, 2).toUpperCase()}</span>
                  <span className="text-[11px] font-bold text-white/70 tabular-nums">{fmt$$(price as number)}</span>
                  {i === 0 && <span className="text-[8px] font-black text-emerald-400">best</span>}
                </div>
              ))}
            </div>
          )}
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

// ── Portfolio card ─────────────────────────────────────────────────────────────
function WatchlistCard({
  event, meta, isPinned, isArchived, isHidden,
  onRemove, onPin, onToggleArchive, onToggleHide,
}: {
  event: EventSummary;
  meta: EventMeta | undefined;
  isPinned: boolean;
  isArchived: boolean;
  isHidden: boolean;
  onRemove: () => void;
  onPin: () => void;
  onToggleArchive: () => void;
  onToggleHide: () => void;
}) {
  const title      = meta?.title ?? event.title;
  const venue      = meta?.venue_name;
  const dateStr    = meta?.event_date;
  const artist     = meta?.artist;
  const gradient   = getEventGradient(artist, title);
  const artworkUrl = useArtistImage(artist, title);
  const action     = signalToAction(event.signal);
  const colors     = actionColors(action);
  const spotify    = getSpotifyData(artist);
  const mpPrices   = meta?.all_marketplace_prices ?? meta?.marketplace_prices ?? {};
  const mpEntries  = (Object.entries(mpPrices) as [string, number | null][])
    .filter(([, p]) => p != null)
    .sort(([, a], [, b]) => (a as number) - (b as number));

  let daysOut: number | null = null;
  let dateLabel = "";
  if (dateStr) {
    try {
      const d = parseEventDate(dateStr);
      daysOut = differenceInDays(d, new Date());
      dateLabel = format(d, "EEE MMM d");
    } catch {}
  }

  const h24Pct   = event.changes?.h24?.price_delta_pct ?? null;
  const invDelta = event.changes?.h24?.inventory_delta ?? null;

  return (
    <div
      className={`relative rounded-xl border overflow-hidden transition-all hover:border-white/15 ${isHidden ? "opacity-50" : ""}`}
      style={{
        background: gradientBg(gradient, "low"),
        borderColor: isArchived ? "rgba(245,158,11,0.25)" : "rgba(255,255,255,0.08)",
      }}
    >
      {/* Artwork strip */}
      {artworkUrl && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={artworkUrl} alt="" className="absolute inset-0 w-full h-full object-cover object-top opacity-[0.08]" loading="lazy"
          onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
      )}

      <div className="relative p-4">
        {/* Top row: signal + actions */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] font-black tracking-widest px-2 py-0.5 rounded border"
              style={{ color: colors.text, background: colors.bg, borderColor: colors.border }}>
              {action}
            </span>
            {isArchived && (
              <span className="text-[9px] text-amber-500/60 border border-amber-500/15 rounded px-1.5 py-0.5">Archived</span>
            )}
          </div>
          <div className="flex items-center gap-0.5 flex-shrink-0">
            <button onClick={onPin} title="Set as headline"
              className="p-1 rounded hover:bg-white/10 transition-colors">
              <Pin size={11} className="text-slate-600 hover:text-amber-400" />
            </button>
            <button onClick={onToggleArchive} title={isArchived ? "Restore" : "Archive"}
              className="p-1 rounded hover:bg-white/10 transition-colors">
              <Archive size={11} className={isArchived ? "text-amber-400" : "text-slate-600 hover:text-slate-400"} />
            </button>
            <button onClick={onToggleHide} title={isHidden ? "Unhide" : "Hide"}
              className="p-1 rounded hover:bg-white/10 transition-colors">
              <EyeOff size={11} className={isHidden ? "text-slate-300" : "text-slate-600 hover:text-slate-400"} />
            </button>
            <button onClick={onRemove} title="Remove from watchlist"
              className="p-1 rounded hover:bg-white/10 transition-colors">
              <Bookmark size={11} className="text-blue-400 fill-blue-400" />
            </button>
          </div>
        </div>

        {/* Identity */}
        {artist && <p className="text-[10px] text-white/40 uppercase tracking-widest mb-0.5">{artist}</p>}
        <Link href={`/events/${event.event_id}`}>
          <h3 className="text-sm font-semibold text-white leading-tight mb-1 hover:text-blue-300 transition-colors line-clamp-2">{title}</h3>
        </Link>
        {venue && <p className="text-[10px] text-slate-500 mb-0.5 truncate">{venue}</p>}
        {dateStr && (
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500 mb-3">
            <Calendar size={9} />
            <span>{dateLabel}</span>
            {daysOut != null && daysOut >= 0 && (
              <span className="text-slate-600">· {daysOut === 0 ? "Today" : `${daysOut}d`}</span>
            )}
          </div>
        )}

        {/* Price grid */}
        <div className="grid grid-cols-3 gap-1.5 mb-3">
          {[
            { label: "Low",    val: fmt$$(event.price?.low_ask),    cls: "text-white font-bold" },
            { label: "Median", val: fmt$$(event.price?.median_ask), cls: "text-white/75 font-semibold" },
            { label: "Inv",    val: fmtNum(event.inventory?.total_listings), cls: "text-white/60 font-medium" },
          ].map(({ label, val, cls }) => (
            <div key={label} className="bg-black/20 rounded px-2 py-1.5 border border-white/5">
              <p className="text-[8px] text-white/30 uppercase tracking-wide mb-0.5">{label}</p>
              <p className={`text-xs tabular-nums ${cls}`}>{val}</p>
            </div>
          ))}
        </div>

        {/* MP chips */}
        {mpEntries.length > 0 && (
          <div className="flex items-center gap-1 flex-wrap mb-2.5">
            {mpEntries.slice(0, 4).map(([slug, price], i) => (
              <div key={slug} className="flex items-center gap-1 rounded px-1.5 py-0.5 border text-[9px]"
                style={{ borderColor: (MP_COLOR[slug] ?? "#888") + "30", background: (MP_COLOR[slug] ?? "#888") + "08" }}>
                <span className="font-bold" style={{ color: MP_COLOR[slug] ?? "#aaa" }}>{MP_SHORT[slug] ?? slug.slice(0, 2).toUpperCase()}</span>
                <span className="text-white/50 tabular-nums">{fmt$$(price as number)}</span>
                {i === 0 && <span className="text-emerald-500 text-[8px]">best</span>}
              </div>
            ))}
          </div>
        )}

        {/* Bottom: delta + follow status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {h24Pct != null && <DeltaChip pct={h24Pct} />}
            {invDelta != null && (
              <span className="text-[10px] text-slate-600">
                {invDelta > 0 ? "+" : ""}{invDelta} inv
              </span>
            )}
          </div>
          {spotify.spotifyArtistUrl && (
            <a href={spotify.spotifyArtistUrl} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded border border-[#1db954]/25 bg-[#1db954]/8 text-[#1db954]">
              <Music size={8} /> Spotify
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
