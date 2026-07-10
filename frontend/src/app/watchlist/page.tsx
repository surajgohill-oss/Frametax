"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Bookmark, BookmarkX, Calendar, TrendingUp, TrendingDown, Minus,
  AlertCircle, Pin, PinOff, Archive, EyeOff, Music, ArrowUpRight, Clock,
} from "lucide-react";
import { format, parseISO, differenceInDays } from "date-fns";
import { api } from "@/lib/api";
import type { EventSummary, EventMeta, EventSnapshotResponse, SellerResponse, VelocityWindowsResponse } from "@/lib/types";
import { fmt$$, fmt$$signed, fmtPct, fmtNum, signalToAction, actionColors, cn, parseEventDate } from "@/lib/utils";
import { getEventGradient, gradientBg, getSpotifyData } from "@/lib/entityimages";
import { useArtistImage } from "@/hooks/useArtistImage";
import { useWatchlist } from "@/hooks/useWatchlist";
import { useHeadlineEvent } from "@/hooks/useHeadlineEvent";
import { useArchivedEvents } from "@/hooks/useArchivedEvents";
import MarketRow from "@/components/MarketRow";
import { venueCity } from "@/lib/venueGeo";
import { useHiddenEvents } from "@/hooks/useHiddenEvents";

const MP_SHORT: Record<string, string> = {
  stubhub: "SH", gametime: "GT", tickpick: "TP", vividseats: "VS",
};

const MP_META: Record<string, { label: string; short: string; color: string; logoBg: string }> = {
  stubhub:    { label: "StubHub",     short: "SH", color: "#e8704a", logoBg: "#e8704a" },
  tickpick:   { label: "TickPick",    short: "TP", color: "#2dd4bf", logoBg: "#0d9488" },
  gametime:   { label: "Gametime",    short: "GT", color: "#4ade80", logoBg: "#16a34a" },
  vividseats: { label: "Vivid Seats", short: "VS", color: "#a78bfa", logoBg: "#7c3aed" },
};

const FRESHNESS_CFG: Record<string, { dot: string; text: string }> = {
  fresh:   { dot: "bg-emerald-400", text: "text-emerald-400" },
  late:    { dot: "bg-amber-400",   text: "text-amber-400"  },
  stale:   { dot: "bg-orange-500",  text: "text-orange-400" },
  dead:    { dot: "bg-red-500",     text: "text-red-400"    },
  no_data: { dot: "bg-slate-500",   text: "text-slate-500"  },
};

function DeltaChip({ pct, abs, invert = false }: { pct?: number | null; abs?: number | null; invert?: boolean }) {
  const n = pct ?? abs ?? null;
  if (n == null) return <span className="text-white/25 text-[11px]">—</span>;
  const Icon = n > 0 ? TrendingUp : n < 0 ? TrendingDown : Minus;
  // invert=true for price rows: lower = green (good), higher = red (bad)
  const isGood = invert ? n < 0 : n > 0;
  const isBad  = invert ? n > 0 : n < 0;
  return (
    <span className={cn(
      "inline-flex items-center gap-0.5 text-[13px] font-semibold tabular-nums px-1.5 py-0.5 rounded",
      isGood ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
      : isBad ? "text-red-400 bg-red-500/10 border border-red-500/20"
      : "text-slate-500 bg-white/5 border border-white/10"
    )}>
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

  // Fetch meta only for the hero event (avoid N+1 calls for all watched events)
  useEffect(() => {
    if (!heroEvent) return;
    api.events.meta(heroEvent.event_id)
      .then((m) => setMetas((prev) => ({ ...prev, [heroEvent.event_id]: m })))
      .catch(() => {});
  }, [heroEvent?.event_id]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Bookmark size={16} className="text-slate-400" />
            <h1 className="text-2xl font-bold tracking-tight text-white">Watchlist</h1>
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
                <p className="text-[11px] text-slate-500 uppercase tracking-[0.18em]">Other watched events</p>
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
  const title      = event.title;
  const venue      = event.venue_name ?? meta?.venue_name;
  const dateStr    = event.event_date ?? meta?.event_date;
  const artist          = event.artist ?? meta?.artist;
  const gradient        = getEventGradient(artist, title);
  const autoArtworkUrl  = useArtistImage(artist, title);
  const artworkUrl      = event.custom_artwork_url ?? meta?.custom_artwork_url ?? autoArtworkUrl;
  const [marketWindow, setMarketWindow] = useState<"tracking" | "24h" | "12h" | "6h" | "7d">("tracking");
  const [snap, setSnap]     = useState<EventSnapshotResponse | null>(null);
  const [seller, setSeller] = useState<SellerResponse | null>(null);
  const [vel, setVel]       = useState<VelocityWindowsResponse | null>(null);
  const [lcSummary, setLcSummary] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const eid = event.event_id;
    setSnap(null); setSeller(null); setVel(null); setLcSummary(null);
    api.events.snapshot(eid).then(setSnap).catch(() => {});
    api.events.seller(eid).then(setSeller).catch(() => {});
    api.analytics.velocityWindows(eid).then(setVel).catch(() => {});
    api.events.lifecycle(eid).then(d => setLcSummary(d.summary)).catch(() => {});
  }, [event.event_id]);

  const action          = signalToAction(event.signal);
  const colors          = actionColors(action);
  const mpPrices        = event.marketplace_prices ?? meta?.all_marketplace_prices ?? meta?.marketplace_prices ?? {};
  const invDelta        = event.changes?.h24?.inventory_delta ?? null;
  const invCurrent      = event.inventory?.total_listings ?? null;
  const invPrev         = (invCurrent != null && invDelta != null) ? invCurrent - invDelta : null;
  const invPct          = (invPrev != null && invPrev !== 0 && invDelta != null) ? (invDelta / invPrev) * 100 : null;

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
    <div className="rounded-xl border border-white/10 bg-[#080a10] overflow-hidden" style={{ boxShadow: `0 0 80px ${gradient[0]}10, 0 0 0 1px rgba(255,255,255,0.03)` }}>
      {/* Hero — art + identity + live market */}
      <div className="relative border-b border-white/6" style={{ minHeight: 200 }}>
        {/* Atmosphere bloom */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true"
          style={{ background: `linear-gradient(115deg, ${gradient[0]}25 0%, ${gradient[0]}08 42%, transparent 72%)` }} />

        {/* Artwork — absolute, full height left */}
        <div className="absolute inset-y-0 left-0 w-[120px] sm:w-[190px] overflow-hidden"
          style={{ background: `linear-gradient(145deg, ${gradient[0]}cc, ${gradient[1]}aa)` }}>
          {artworkUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={artworkUrl} alt={artist ?? title}
              className="w-full h-full object-cover object-top"
              onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-4xl font-black text-white/40 select-none">
                {(artist ?? title).slice(0, 1).toUpperCase()}
              </span>
            </div>
          )}
          <div className="absolute inset-y-0 right-0 w-12 sm:w-20"
            style={{ background: `linear-gradient(to right, transparent, #080a10)` }} />
        </div>

        {/* Content offset by artwork */}
        <div className="relative flex items-end justify-between pl-[120px] sm:pl-[190px] p-5 gap-4" style={{ minHeight: 200 }}>

          {/* Identity */}
          <div className="flex-1 min-w-0">
            {isPinned && <Pin size={9} className="text-amber-400/60 mb-1" />}
            {artist && artist !== title && <p className="text-[11px] text-slate-500 uppercase tracking-[0.2em] font-semibold truncate mb-1">{artist}</p>}
            <Link href={`/events/${event.event_id}`}>
              <span className="text-[24px] sm:text-[30px] font-black text-white block hover:text-blue-300 transition-colors leading-none truncate">{title}</span>
            </Link>
            <div className="flex items-center gap-1.5 mt-2 text-[13px] text-slate-400">
              {venue && <span className="truncate">{venue}{venueCity(event.venue_slug) && <span className="text-slate-600"> · {venueCity(event.venue_slug)}</span>}</span>}
              {venue && dateLabel && <span className="text-slate-600">·</span>}
              {dateLabel && <span>{dateLabel}</span>}
            </div>
            <div className="flex items-center gap-2 mt-3 flex-wrap">
              {daysOut != null && (
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full"
                  style={{ color: colors.text, background: colors.bg + "50", border: `1px solid ${colors.border}` }}>
                  {daysOut <= 0 ? "Today" : daysOut === 1 ? "Tomorrow" : `${daysOut}d away`}
                </span>
              )}
              <span className="text-[11px] font-bold px-2 py-0.5 rounded border"
                style={{ color: colors.text, borderColor: colors.border + "80", background: colors.bg + "25" }}>
                {action}
              </span>
            </div>
          </div>

          {/* RIGHT: Live market — mirrors event page hero hierarchy */}
          <div className="hidden sm:flex items-end gap-5 flex-shrink-0">
            {/* Live Market Snapshot */}
            <div className="flex flex-col items-end">
              <p className="text-[11px] text-white/30 uppercase tracking-[0.22em] font-semibold mb-1">Median</p>
              <p className="text-[44px] font-black text-white/90 tabular-nums leading-none">
                {fmt$$(event.price?.median_ask) ?? "—"}
              </p>
              {event.changes?.h24?.price_delta_pct != null && (
                <div className="mt-1"><DeltaChip pct={event.changes.h24.price_delta_pct} invert /></div>
              )}
              <div className="flex items-center gap-4 mt-3 pt-3 border-t border-white/[0.1] w-full justify-end">
                <div className="text-right">
                  <p className="text-[11px] text-white/28 uppercase tracking-wide mb-0.5">Inventory</p>
                  <p className="text-[18px] font-bold text-blue-300/80 tabular-nums leading-none">
                    {fmtNum(event.inventory?.total_listings) ?? "—"}
                  </p>
                  {invDelta != null && (
                    <p className={`text-[10px] tabular-nums mt-0.5 ${invDelta > 0 ? "text-red-400" : invDelta < 0 ? "text-emerald-400" : "text-slate-500"}`}>
                      {invDelta > 0 ? "+" : ""}{fmtNum(invDelta)}
                      {invPct != null ? ` (${invPct > 0 ? "+" : ""}${invPct.toFixed(1)}%)` : ""}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-[11px] text-white/28 uppercase tracking-wide mb-0.5">Duplicate %</p>
                  <p className="text-[18px] font-bold text-violet-300/70 tabular-nums leading-none">
                    {snap?.duplicates?.dup_pct != null ? `${snap.duplicates.dup_pct.toFixed(1)}%` : "—"}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[11px] text-white/28 uppercase tracking-wide mb-0.5">Low</p>
                  <p className="text-[18px] font-bold text-emerald-300 tabular-nums leading-none">
                    {fmt$$(event.price?.low_ask) ?? "—"}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[11px] text-white/28 uppercase tracking-wide mb-0.5">High</p>
                  <p className="text-[18px] font-bold text-white/40 tabular-nums leading-none">
                    {fmt$$((event.price as Record<string, number | null> | undefined)?.high_ask ?? (event.price as Record<string, number | null> | undefined)?.p75_ask) ?? "—"}
                  </p>
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex flex-col gap-1.5 pb-1">
              {isPinned && (
                <button onClick={onClearPin} title="Unpin"
                  className="inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded-lg border border-amber-500/40 bg-amber-500/10 text-amber-400 transition-colors">
                  <PinOff size={9} /> Unpin
                </button>
              )}
              <button onClick={onToggleArchive} title={isArchived ? "Restore" : "Archive"}
                className={cn("inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded-lg border transition-all",
                  isArchived ? "border-amber-500/40 bg-amber-500/10 text-amber-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300")}>
                <Archive size={9} /> {isArchived ? "Restore" : "Archive"}
              </button>
              <button onClick={onRemove} title="Remove from watchlist"
                className="inline-flex items-center gap-1 text-[11px] px-2 py-1 rounded-lg border border-blue-500/40 bg-blue-500/10 text-blue-400 transition-colors">
                <Bookmark size={9} className="fill-blue-400" /> Watching
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Status bar: tracking meta + per-marketplace freshness dots */}
      {(() => {
        const wlFreshEntries = (['stubhub', 'tickpick', 'gametime', 'vividseats'] as const)
          .filter(slug => meta?.marketplace_freshness?.[slug]);
        const wlFreshCount = wlFreshEntries.filter(slug => {
          const s = (meta?.marketplace_freshness?.[slug] as { freshness_status?: string })?.freshness_status;
          return s === "fresh" || s === "late";
        }).length;
        return (
      <div className="border-t border-white/[0.07] bg-black/20 px-5 py-2.5 flex items-center gap-4 flex-wrap">
        {trackingSince && (
          <span className="text-[11px] text-white/28 flex items-center gap-1.5">
            <Clock size={10} />
            <span className="text-white/20 uppercase tracking-[0.1em] text-[10px]">Tracking Since</span>
            <span className="text-white/40">{trackingSince.formatted}</span>
          </span>
        )}
        {freshLabel && (
          <span className="text-[11px] text-white/28 flex items-center gap-1.5">
            <span className="text-white/20 uppercase tracking-[0.1em] text-[10px]">Last Update</span>
            <span className="text-white/40">{freshLabel}</span>
          </span>
        )}
        {wlFreshEntries.length > 0 && (
          <span className="text-[11px] text-white/28 flex items-center gap-1.5">
            <span className="text-white/20 uppercase tracking-[0.1em] text-[10px]">Feeds Fresh</span>
            <span className="text-white/40">{wlFreshCount}/{wlFreshEntries.length}</span>
          </span>
        )}
        <div className="flex items-center gap-4 ml-auto flex-wrap">
          {wlFreshEntries
            .map(slug => {
              const f = meta!.marketplace_freshness![slug] as { freshness_status?: string; age_minutes?: number };
              const status = f?.freshness_status ?? "no_data";
              const age = f?.age_minutes;
              const ageStr = age == null ? null : age < 60 ? `${age}m` : `${Math.round(age / 60)}h`;
              const cfg = FRESHNESS_CFG[status] ?? FRESHNESS_CFG.no_data;
              const info = MP_META[slug];
              return (
                <div key={slug} className="flex items-center gap-1.5">
                  {info && (
                    <div className="rounded flex items-center justify-center font-black text-white flex-shrink-0"
                      style={{ width: 16, height: 16, background: info.logoBg, fontSize: 7 }}>
                      {info.short}
                    </div>
                  )}
                  <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
                  <span className="text-[11px] font-medium" style={{ color: info?.color ?? "rgba(255,255,255,0.38)" }}>{info?.label ?? slug}</span>
                  <span className={`text-[11px] tabular-nums ${cfg.text}`}>{ageStr ?? "—"}</span>
                </div>
              );
            })}
        </div>
      </div>
        );
      })()}

      {/* Intelligence columns — 3-col */}
      <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-white/6"
        style={{ gridTemplateColumns: "1fr 1.2fr 1fr" }}>

        {/* Col 1: Current Market */}
        <div className="p-5">
          <div className="flex items-center justify-between mb-4">
            <p className="text-[11px] text-slate-400 uppercase tracking-[0.18em] font-semibold">Current Market</p>
            <div className="flex items-center gap-0.5">
              {(["tracking", "24h", "12h", "6h", "7d"] as const).map(w => (
                <button key={w} onClick={() => setMarketWindow(w)}
                  className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded transition-colors uppercase",
                    marketWindow === w
                      ? "bg-white/10 text-slate-200 border border-white/15"
                      : "text-slate-600 hover:text-slate-400")}>
                  {w === "tracking" ? "Tracking" : w}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-0">
            {/* Median */}
            {(() => {
              const cur = event.price?.median_ask ?? null;
              const pct = event.changes?.h24?.price_delta_pct ?? null;
              const orig = (cur != null && pct != null) ? Math.round(cur / (1 + pct / 100)) : null;
              const abs  = (cur != null && orig != null) ? cur - orig : null;
              return (
                <MarketRow label="Median"
                  baseline={orig != null ? fmt$$(orig) : null}
                  current={cur != null ? fmt$$(cur) : "—"}
                  delta={abs != null && abs !== 0 ? fmt$$signed(abs) : null}
                  deltaCls={abs != null && abs < 0 ? "text-emerald-400" : "text-red-400"}
                  tail={pct != null ? <DeltaChip pct={pct} invert /> : <span className="text-[13px] text-slate-700">—</span>}
                />
              );
            })()}
            {/* Note: Low/High baselines not in EventSummary type — deltas shown as — */}
            <MarketRow label="Low"
              current={event.price?.low_ask != null ? fmt$$(event.price.low_ask) : "—"}
              currentCls="text-emerald-300"
              tail={<span className="text-[13px] text-slate-700">—</span>}
            />
            <MarketRow label="High"
              current={event.price?.high_ask != null ? fmt$$(event.price.high_ask) : "—"}
              currentCls="text-slate-300"
              tail={<span className="text-[13px] text-slate-700">—</span>}
            />
            {(() => {
              const cur = invCurrent;
              const abs = invDelta;
              const absPct = abs != null && cur != null && (cur - abs) > 0 ? (abs / (cur - abs)) * 100 : null;
              return (
                <MarketRow label="Inventory"
                  current={cur != null ? fmtNum(cur) : "—"}
                  currentCls="text-blue-300/80"
                  delta={abs != null ? `${abs > 0 ? "+" : ""}${fmtNum(abs)}` : null}
                  deltaCls={abs != null && abs > 0 ? "text-red-400" : abs != null && abs < 0 ? "text-emerald-400" : "text-slate-500"}
                  tail={absPct != null ? <DeltaChip pct={absPct} invert /> : <span className="text-[13px] text-slate-700">—</span>}
                />
              );
            })()}
            <MarketRow label="Dup %" last
              current={snap?.duplicates?.dup_pct_reliable === false ? "—" : snap?.duplicates?.dup_pct != null ? `${snap.duplicates.dup_pct.toFixed(1)}%` : "—"}
              currentCls="text-violet-300/70"
              tail={snap?.duplicates?.dup_pct_reliable === false ? <span className="text-[13px] italic text-amber-500/70">Not reliable</span> : null}
            />
          </div>
        </div>

        {/* Col 2: Absorption */}
        <div className="p-5 bg-white/[0.02]">
          <p className="text-[11px] text-slate-400 uppercase tracking-[0.18em] font-semibold mb-4">Absorption</p>
          {(() => {
            const avgImpliedSalePrice = (() => {
              const v = (lcSummary as Record<string, unknown> | null)?.avg_implied_sale_price;
              return typeof v === "number" ? v : null;
            })();
            const absRows: { label: string; num: number | null; emptyLabel: string }[] = [
              { label: "Tickets Sold",   num: vel?.windows?.since_tracking?.implied_sale_tickets ?? null,  emptyLabel: vel != null ? "No disappearances" : "No lifecycle yet" },
              { label: "24H Sold",       num: vel?.windows?.["24h"]?.implied_sale_listings ?? null,        emptyLabel: vel != null ? "No disappearances" : "No lifecycle yet" },
              { label: "7D Sold",        num: vel?.windows?.["7d"]?.implied_sale_listings ?? null,         emptyLabel: vel != null ? "No disappearances" : "No lifecycle yet" },
              { label: "Since Tracking", num: vel?.windows?.since_tracking?.implied_sale_listings ?? null, emptyLabel: vel != null ? "No disappearances" : "No lifecycle yet" },
            ];
            return (
              <>
                <div className="mb-3 pb-3 border-b border-white/[0.04]">
                  <p className="text-[11px] text-slate-500 mb-1 uppercase tracking-[0.12em]">Est. Avg Sale Price</p>
                  {avgImpliedSalePrice != null ? (
                    <span className="text-[36px] font-black text-amber-300 tabular-nums leading-none">${Math.round(avgImpliedSalePrice)}</span>
                  ) : lcSummary != null ? (
                    <span className="text-[11px] italic text-slate-600">No disappearances yet</span>
                  ) : (
                    <span className="text-[11px] italic text-slate-700">No lifecycle yet</span>
                  )}
                </div>
                <div>
                  {absRows.map(({ label, num, emptyLabel }) => (
                    <div key={label} className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0">
                      <span className="text-[11px] text-slate-400">{label}</span>
                      {num != null && num > 0 ? (
                        <span className={`text-[12px] font-semibold tabular-nums ${label === "Tickets Sold" ? "text-amber-300" : "text-slate-300"}`}>
                          {label === "Tickets Sold" ? fmtNum(num) : num}
                        </span>
                      ) : num === 0 ? (
                        <span className="text-[11px] italic text-slate-600">{emptyLabel}</span>
                      ) : (
                        <span className="text-[11px] text-slate-700">No data</span>
                      )}
                    </div>
                  ))}
                </div>
              </>
            );
          })()}
        </div>

        {/* Col 3: Seller Behavior */}
        <div className="p-5">
          <p className="text-[11px] text-slate-400 uppercase tracking-[0.18em] font-semibold mb-4">Seller Behavior</p>
          {(() => {
            const relistDelta = seller?.median_reprice_delta ?? null;
            const drops       = seller?.price_drops_24h ?? null;
            const repriced    = seller?.repriced_24h ?? null;
            const mood = (() => {
              if (!seller) return null;
              const cap  = seller.capitulation_score ?? 0;
              const agg  = seller.seller_aggression ?? 0;
              const dr   = drops != null && repriced != null && repriced > 0 ? drops / repriced : null;
              if (cap > 0.6)  return "Seller capitulation increasing";
              if (agg > 0.6)  return "Sellers holding firm";
              if (dr != null && dr > 0.7) return "Heavy price dropping";
              if (agg > 0.4)  return "Mild seller confidence";
              return "Mixed seller signals";
            })();
            return (
              <div>
                <div className="flex items-center justify-between py-2.5 border-b border-white/[0.04]">
                  <span className="text-[11px] text-slate-400">Relist Price Chg</span>
                  {relistDelta != null ? (
                    <span className={`text-[12px] font-semibold tabular-nums ${relistDelta < 0 ? "text-emerald-400" : relistDelta > 0 ? "text-red-400" : "text-slate-400"}`}>
                      {fmt$$signed(relistDelta)}
                    </span>
                  ) : (
                    <span className="text-[11px] italic text-slate-600">{seller != null ? "No relist activity" : "Not enough history"}</span>
                  )}
                </div>
                <div className="flex items-center justify-between py-2.5 border-b border-white/[0.04]">
                  <span className="text-[11px] text-slate-400">Price Drops</span>
                  {drops != null ? (
                    drops > 0
                      ? <span className="text-[12px] font-semibold text-red-400 tabular-nums">{drops}</span>
                      : <span className="text-[11px] italic text-slate-600">No price drops</span>
                  ) : (
                    <span className="text-[11px] italic text-slate-600">Not enough history</span>
                  )}
                </div>
                <div className="flex items-center justify-between py-2.5 border-b border-white/[0.04]">
                  <span className="text-[11px] text-slate-400">Repriced Listings</span>
                  {repriced != null ? (
                    repriced > 0
                      ? <span className="text-[12px] font-semibold text-slate-300 tabular-nums">{repriced}</span>
                      : <span className="text-[11px] italic text-slate-600">No repricing detected</span>
                  ) : (
                    <span className="text-[11px] italic text-slate-600">Not enough history</span>
                  )}
                </div>
                <div className="flex items-start justify-between py-2.5">
                  <span className="text-[11px] text-slate-500">Seller Mood</span>
                  {mood ? (
                    <span className="text-[11px] font-medium italic text-slate-300 text-right max-w-[140px]">{mood}</span>
                  ) : (
                    <span className="text-[11px] italic text-slate-600">{seller != null ? "No seller movement yet" : "Not enough history"}</span>
                  )}
                </div>
              </div>
            );
          })()}
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
  const title      = event.title;
  const venue      = event.venue_name ?? meta?.venue_name;
  const dateStr    = event.event_date ?? meta?.event_date;
  const artist          = event.artist ?? meta?.artist;
  const gradient        = getEventGradient(artist, title);
  const autoArtworkUrl  = useArtistImage(artist, title);
  const artworkUrl      = event.custom_artwork_url ?? meta?.custom_artwork_url ?? autoArtworkUrl;
  const action          = signalToAction(event.signal);
  const colors          = actionColors(action);
  const spotify         = getSpotifyData(artist);
  const mpPrices   = event.marketplace_prices ?? meta?.all_marketplace_prices ?? meta?.marketplace_prices ?? {};
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
            <span className="text-[11px] font-bold tracking-widest px-2 py-0.5 rounded border"
              style={{ color: colors.text, background: colors.bg, borderColor: colors.border }}>
              {action}
            </span>
            {isArchived && (
              <span className="text-[11px] text-amber-500/60 border border-amber-500/15 rounded px-1.5 py-0.5">Archived</span>
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
        {artist && <p className="text-[11px] text-white/50 uppercase tracking-[0.12em] mb-0.5">{artist}</p>}
        <Link href={`/events/${event.event_id}`}>
          <h3 className="text-[13px] font-bold text-white leading-tight mb-1 hover:text-blue-300 transition-colors line-clamp-2">{title}</h3>
        </Link>
        {venue && <p className="text-[11px] text-slate-500 mb-0.5 truncate">{venue}{venueCity(event.venue_slug) && <span className="text-slate-600"> · {venueCity(event.venue_slug)}</span>}</p>}
        {dateStr && (
          <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mb-3">
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
            { label: "Low",    val: fmt$$(event.price?.low_ask),             cls: "text-emerald-300 font-bold text-[13px]" },
            { label: "Median", val: fmt$$(event.price?.median_ask),          cls: "text-white/80 font-semibold text-[12px]" },
            { label: "Inv",    val: fmtNum(event.inventory?.total_listings), cls: "text-white/55 font-medium text-[11px]" },
          ].map(({ label, val, cls }) => (
            <div key={label} className="bg-black/20 rounded px-2 py-1.5 border border-white/5">
              <p className="text-[11px] text-white/30 uppercase tracking-[0.12em] mb-0.5">{label}</p>
              <p className={`tabular-nums leading-none ${cls}`}>{val}</p>
            </div>
          ))}
        </div>

        {/* MP chips — quieter, no "best" text, lowest price in emerald */}
        {mpEntries.length > 0 && (
          <div className="flex items-center gap-1 flex-wrap mb-2.5">
            {mpEntries.slice(0, 4).map(([slug, price], i) => (
              <div key={slug} className="flex items-center gap-1 rounded px-1.5 py-0.5 border text-[11px]"
                style={{ borderColor: ((MP_META[slug]?.color ?? "#888888") ?? "#888") + "25", background: ((MP_META[slug]?.color ?? "#888888") ?? "#888") + "06" }}>
                <span className="font-semibold" style={{ color: ((MP_META[slug]?.color ?? "#888888") ?? "#aaa") + (i === 0 ? "" : "cc") }}>
                  {MP_SHORT[slug] ?? slug.slice(0, 2).toUpperCase()}
                </span>
                <span className={i === 0 ? "text-emerald-300 font-semibold tabular-nums" : "text-white/40 tabular-nums"}>
                  {fmt$$(price as number)}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Bottom: delta + follow status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {h24Pct != null && <DeltaChip pct={h24Pct} />}
            {invDelta != null && (
              <span className="text-[11px] text-slate-500">
                {invDelta > 0 ? "+" : ""}{invDelta} inv
              </span>
            )}
          </div>
          {spotify.spotifyArtistUrl && (
            <a href={spotify.spotifyArtistUrl} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded border border-[#1db954]/25 bg-[#1db954]/8 text-[#1db954]">
              <Music size={8} /> Spotify
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
