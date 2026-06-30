"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Eye, RefreshCw, TrendingUp, TrendingDown, Minus, AlertCircle,
  ChevronDown, ChevronRight, Bookmark,
  ArrowUpRight, ArrowDownRight, Pin, Music,
  Pause, Play, Volume2, VolumeX, Clock,
} from "lucide-react";
import { differenceInDays, parseISO, format } from "date-fns";
import { api } from "@/lib/api";
import type { EventSummary, EventMeta, SellerResponse, VelocityWindowsResponse, EventSnapshotResponse } from "@/lib/types";
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

const MP_META: Record<string, { label: string; short: string; color: string; logoBg: string }> = {
  stubhub:    { label: "StubHub",     short: "SH", color: "#e8704a", logoBg: "#e8704a" },
  tickpick:   { label: "TickPick",    short: "TP", color: "#2dd4bf", logoBg: "#0d9488" },
  gametime:   { label: "Gametime",    short: "GT", color: "#4ade80", logoBg: "#16a34a" },
  vividseats: { label: "Vivid Seats", short: "VS", color: "#a78bfa", logoBg: "#7c3aed" },
};

// ── Small delta chip ─────────────────────────────────────────────────────────
function DeltaChip({ pct, abs, invert = false }: { pct?: number | null; abs?: number | null; invert?: boolean }) {
  const n = pct ?? abs ?? null;
  if (n == null) return <span className="text-white/25 text-[11px]">—</span>;
  const Icon = n > 0 ? TrendingUp : n < 0 ? TrendingDown : Minus;
  // invert=true for price rows: lower = green (good), higher = red (bad)
  const isGood = invert ? n < 0 : n > 0;
  const isBad  = invert ? n > 0 : n < 0;
  return (
    <span className={cn(
      "inline-flex items-center gap-0.5 text-[11px] font-bold tabular-nums px-1.5 py-0.5 rounded",
      isGood ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
      : isBad ? "text-red-400 bg-red-500/10 border border-red-500/20"
      : "text-slate-500 bg-white/5 border border-white/10"
    )}>
      <Icon size={9} />{pct != null ? fmtPct(pct) : (n > 0 ? `+${n}` : `${n}`)}
    </span>
  );
}

// ── Featured Event Hero ───────────────────────────────────────────────────────
// Full-height artwork + identity strip + 4-col intelligence row.
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
  const artist          = meta?.artist;
  const autoArtworkUrl  = useArtistImage(artist, title);
  const artworkUrl      = meta?.custom_artwork_url ?? autoArtworkUrl;
  const gradient        = getEventGradient(artist, title);
  const [marketWindow, setMarketWindow] = useState<"tracking" | "24h" | "12h" | "6h" | "7d">("tracking");
  const action     = signalToAction(event.signal);
  const aColors    = actionColors(action);
  const invDelta   = event.changes?.h24?.inventory_delta ?? null;
  const priceDeltaPct = event.changes?.h24?.price_delta_pct ?? null;
  const invCurrent = event.inventory?.total_listings ?? null;
  const invPrev    = (invCurrent != null && invDelta != null) ? invCurrent - invDelta : null;
  const invPct     = (invPrev != null && invPrev !== 0 && invDelta != null) ? (invDelta / invPrev) * 100 : null;

  // Intelligence data for panels — fetched per featured event
  const [snap, setSnap]   = useState<EventSnapshotResponse | null>(null);
  const [seller, setSeller] = useState<SellerResponse | null>(null);
  const [vel, setVel]     = useState<VelocityWindowsResponse | null>(null);
  const [lcSummary, setLcSummary] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    const eid = event.event_id;
    setSnap(null); setSeller(null); setVel(null); setLcSummary(null);
    api.events.snapshot(eid).then(setSnap).catch(() => {});
    api.events.seller(eid).then(setSeller).catch(() => {});
    api.analytics.velocityWindows(eid).then(setVel).catch(() => {});
    api.events.lifecycle(eid).then(d => setLcSummary(d.summary)).catch(() => {});
  }, [event.event_id]);

  let daysOut: number | null = null;
  let dateLabel = "";
  if (dateStr) {
    try {
      const d = parseEventDate(dateStr);
      daysOut = differenceInDays(d, new Date());
      dateLabel = format(d, "EEE, MMM d, yyyy");
    } catch {}
  }

  // Tracking since from meta.created_at
  const trackingSince = (() => {
    const ca = meta?.created_at;
    if (!ca) return null;
    try {
      const d = parseISO(ca);
      const totalH = Math.round((Date.now() - d.getTime()) / 3600000);
      const days = Math.floor(totalH / 24);
      const hrs  = totalH % 24;
      return {
        label: days > 0 ? `${days}d ${hrs}h` : `${hrs}h`,
        formatted: format(d, "MMM d, yyyy"),
      };
    } catch { return null; }
  })();

  // Freshness label (most recent update)
  const freshLabel = (() => {
    const entries = Object.values(meta?.marketplace_freshness ?? {});
    if (!entries.length) return null;
    const ages = entries
      .map((e: unknown) => ((e as { age_minutes?: number }).age_minutes ?? null))
      .filter((a): a is number => a != null);
    if (!ages.length) return null;
    const minAge = Math.min(...ages);
    return minAge < 60 ? `${minAge}m ago` : `${Math.round(minAge / 60)}h ago`;
  })();

  const MP_SLUGS_HERO = ['stubhub', 'tickpick', 'gametime', 'vividseats'];
  const freshEntries = Object.entries(meta?.marketplace_freshness ?? {})
    .filter(([slug]) => MP_SLUGS_HERO.includes(slug));
  const marketsCount = freshEntries.filter(
    ([, f]) => (f as { freshness_status?: string })?.freshness_status !== "dead"
  ).length;

  // Feeds fresh % (based on fresh+late statuses)
  const freshPct = (() => {
    const total = freshEntries.length;
    if (!total) return null;
    const good = freshEntries.filter(([, f]) => {
      const s = (f as { freshness_status?: string })?.freshness_status;
      return s === "fresh" || s === "late";
    }).length;
    return Math.round((good / total) * 100);
  })();

  // Market signal confidence (proxy from opportunity_score)
  const confidence = (() => {
    const s = event.opportunity_score ?? 0;
    if (s >= 0.7) return { label: "High",   bars: 5 };
    if (s >= 0.45) return { label: "Medium", bars: 3 };
    return               { label: "Low",    bars: 1 };
  })();

  const fCfg: Record<string, { dot: string; text: string }> = {
    fresh:   { dot: "bg-emerald-400", text: "text-emerald-400" },
    late:    { dot: "bg-amber-400",   text: "text-amber-400"  },
    stale:   { dot: "bg-orange-500",  text: "text-orange-400" },
    dead:    { dot: "bg-red-500",     text: "text-red-400"    },
    no_data: { dot: "bg-slate-500",   text: "text-slate-400"  },
  };

  const MP_LABELS: Record<string, string> = {
    stubhub: "StubHub", tickpick: "TickPick", gametime: "Gametime", vividseats: "Vivid Seats",
  };

  return (
    <div className="rounded-xl border border-white/10 bg-[#080a10] overflow-hidden mb-3" style={{ boxShadow: `0 0 80px ${gradient[0]}12, 0 0 0 1px rgba(255,255,255,0.03)` }}>
      {/* ── Hero: art-bloom + artwork + identity + live market ── */}
      <div className="relative border-b border-white/6" style={{ minHeight: 240 }}>
        {/* Art-colored atmosphere bloom */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true"
          style={{ background: `linear-gradient(115deg, ${gradient[0]}28 0%, ${gradient[0]}08 42%, transparent 72%)` }} />

        {/* Artwork panel — absolute, full height left */}
        <div className="absolute inset-y-0 left-0 w-[140px] sm:w-[220px] overflow-hidden"
          style={{ background: `linear-gradient(145deg, ${gradient[0]}cc, ${gradient[1]}aa)` }}>
          {artworkUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={artworkUrl} alt={artist ?? title}
              className="w-full h-full object-cover object-top"
              onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-5xl font-black text-white/40 select-none">
                {(artist ?? title).slice(0, 1).toUpperCase()}
              </span>
            </div>
          )}
          {/* Right edge fade */}
          <div className="absolute inset-y-0 right-0 w-16 sm:w-24"
            style={{ background: `linear-gradient(to right, transparent, #080a10)` }} />
        </div>

        {/* Content area offset by artwork */}
        <div className="relative flex flex-col justify-between pl-[140px] sm:pl-[220px]" style={{ minHeight: 240 }}>
          {/* Identity + live market */}
          <div className="flex items-end justify-between gap-4 p-5 pb-4 flex-1">

            {/* Identity */}
            <div className="flex-1 min-w-0">
              {artist && artist !== title &&
                <p className="text-[11px] text-slate-500 uppercase tracking-[0.2em] font-semibold mb-1 truncate">{artist}</p>}
              <Link href={`/events/${event.event_id}`}>
                <span className="text-[28px] sm:text-[34px] font-black text-white block hover:text-blue-300 transition-colors leading-none truncate">{title}</span>
              </Link>
              {(venue || dateLabel) && (
                <p className="text-[13px] text-slate-400 mt-1.5 truncate">
                  {[venue, dateLabel].filter(Boolean).join(" · ")}
                </p>
              )}
              <div className="flex items-center gap-2 mt-3 flex-wrap">
                {daysOut != null && (
                  <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full"
                    style={{ color: aColors.text, background: aColors.bg + "60", border: `1px solid ${aColors.border}` }}>
                    {daysOut <= 0 ? "Today" : `${daysOut}d away`}
                  </span>
                )}
                <span className="text-[11px] font-black tracking-widest px-2.5 py-0.5 rounded border"
                  style={{ color: aColors.text, borderColor: aColors.border, background: aColors.bg }}>
                  {action}
                </span>
                <button onClick={onToggleWatch}
                  className={cn("inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded border transition-all",
                    isWatched ? "border-blue-500/40 bg-blue-500/10 text-blue-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300")}>
                  <Bookmark size={9} className={isWatched ? "fill-blue-400" : ""} />
                  {isWatched ? "Watching" : "Monitor"}
                </button>
                <button onClick={onTogglePin}
                  className={cn("inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded border transition-all",
                    isPinned ? "border-amber-500/40 bg-amber-500/10 text-amber-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300")}>
                  <Pin size={9} className={isPinned ? "fill-amber-400" : ""} />
                  {isPinned ? "Pinned" : "Pin"}
                </button>
              </div>
            </div>

            {/* Live Market Snapshot — Median dominant per spec */}
            <div className="hidden sm:flex flex-col items-end gap-0 flex-shrink-0 pr-2">
              <p className="text-[11px] text-slate-500 uppercase tracking-[0.14em] mb-1.5">Median</p>
              <p className="text-[44px] font-black text-white/90 tabular-nums leading-none">
                {fmt$$(event.price?.median_ask) ?? "—"}
              </p>
              <div className="flex items-center gap-2 mt-1">
                {priceDeltaPct != null && <DeltaChip pct={priceDeltaPct} invert />}
                <span className="text-[11px] text-slate-500 font-semibold">24H</span>
              </div>
              <div className="flex items-center gap-5 mt-3 pt-2 border-t border-white/[0.08]">
                <div className="text-right">
                  <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-1">Inventory</p>
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
                  <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-1">Duplicate %</p>
                  <p className="text-[18px] font-bold text-violet-300/70 tabular-nums leading-none">
                    {snap?.duplicates?.dup_pct != null ? `${snap.duplicates.dup_pct.toFixed(1)}%` : "—"}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-1">Low</p>
                  <p className="text-[18px] font-bold text-emerald-300 tabular-nums leading-none">
                    {fmt$$(event.price?.low_ask) ?? "—"}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-1">High</p>
                  <p className="text-[18px] font-semibold text-white/40 tabular-nums leading-none">
                    {fmt$$(event.price?.high_ask) ?? "—"}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Status bar: tracking meta + per-marketplace freshness dots */}
          <div className="border-t border-white/[0.05] bg-white/[0.012] px-5 py-2.5 flex items-center gap-4 flex-wrap">
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
            {freshEntries.length > 0 && (
              <span className="text-[11px] text-white/28 flex items-center gap-1.5">
                <span className="text-white/20 uppercase tracking-[0.1em] text-[10px]">Feeds Fresh</span>
                <span className="text-white/40">{freshEntries.filter(([,f]) => { const s = (f as {freshness_status?:string})?.freshness_status; return s === "fresh" || s === "late"; }).length}/{freshEntries.length}</span>
              </span>
            )}
            <div className="flex items-center gap-4 ml-auto flex-wrap">
              {freshEntries.length > 0
                ? freshEntries.map(([slug, f]) => {
                    const fr = f as { freshness_status?: string; age_minutes?: number };
                    const status = fr?.freshness_status ?? "no_data";
                    const age = fr?.age_minutes;
                    const ageStr = age == null ? null : age < 60 ? `${age}m` : `${Math.round(age / 60)}h`;
                    const cfg = fCfg[status] ?? fCfg.no_data;
                    const info = (MP_META as Record<string, { label: string; short: string; color: string; logoBg: string } | undefined>)[slug];
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
                  })
                : <span className="text-[11px] text-white/25">No feeds</span>
              }
            </div>
          </div>
        </div>
      </div>

      {/* ── Intelligence columns — 3 panels ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-white/6">

        {/* Panel 1: Current Market */}
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
          {/* Rows: Median / Low / High / Inventory / Dup % */}
          <div className="space-y-0">
            {/* Median */}
            {(() => {
              const cur = event.price?.median_ask ?? null;
              const pct = event.changes?.h24?.price_delta_pct ?? null;
              const orig = (cur != null && pct != null) ? Math.round(cur / (1 + pct / 100)) : null;
              const abs  = (cur != null && orig != null) ? cur - orig : null;
              return (
                <div className="flex items-center justify-between py-2 border-b border-white/[0.04]">
                  <span className="text-[12px] text-slate-400 font-semibold w-16 flex-shrink-0">Median</span>
                  <div className="flex items-center gap-1.5 tabular-nums">
                    {orig != null ? <span className="text-[11px] text-slate-600">{fmt$$(orig)} →</span> : null}
                    <span className="text-[13px] font-bold text-white">{cur != null ? fmt$$(cur) : "—"}</span>
                    {abs != null && abs !== 0 && <span className="text-[11px] text-slate-500">{abs > 0 ? `+${fmt$$(abs)}` : fmt$$(abs)}</span>}
                    {pct != null ? <DeltaChip pct={pct} invert /> : <span className="text-[11px] text-slate-700">—</span>}
                  </div>
                </div>
              );
            })()}
            {/* Low — no baseline on EventSummary; show current + — */}
            <div className="flex items-center justify-between py-2 border-b border-white/[0.04]">
              <span className="text-[12px] text-slate-500 w-16 flex-shrink-0">Low</span>
              <div className="flex items-center gap-1.5 tabular-nums">
                <span className="text-[13px] font-semibold text-emerald-300">{event.price?.low_ask != null ? fmt$$(event.price.low_ask) : "—"}</span>
                <span className="text-[11px] text-slate-700">—</span>
              </div>
            </div>
            {/* High — no baseline; show current + — */}
            <div className="flex items-center justify-between py-2 border-b border-white/[0.04]">
              <span className="text-[12px] text-slate-500 w-16 flex-shrink-0">High</span>
              <div className="flex items-center gap-1.5 tabular-nums">
                <span className="text-[13px] font-semibold text-slate-400">{event.price?.high_ask != null ? fmt$$(event.price.high_ask) : "—"}</span>
                <span className="text-[11px] text-slate-700">—</span>
              </div>
            </div>
            {/* Inventory */}
            {(() => {
              const cur = invCurrent;
              const abs = invDelta;
              const absPct = abs != null && cur != null && (cur - abs) > 0 ? (abs / (cur - abs)) * 100 : null;
              return (
                <div className="flex items-center justify-between py-2 border-b border-white/[0.04]">
                  <span className="text-[12px] text-slate-500 w-16 flex-shrink-0">Inventory</span>
                  <div className="flex items-center gap-2 tabular-nums">
                    <span className="text-[13px] font-semibold text-blue-300/80">{cur != null ? fmtNum(cur) : "—"}</span>
                    {abs != null ? (
                      <span className={cn("text-[11px] font-medium", abs > 0 ? "text-red-400" : abs < 0 ? "text-emerald-400" : "text-slate-500")}>
                        {abs > 0 ? "+" : ""}{abs}
                        {absPct != null ? ` (${absPct > 0 ? "+" : ""}${absPct.toFixed(1)}%)` : ""}
                      </span>
                    ) : <span className="text-[11px] text-slate-700">—</span>}
                  </div>
                </div>
              );
            })()}
            {/* Dup % */}
            <div className="flex items-center justify-between py-2">
              <span className="text-[12px] text-slate-500 w-16 flex-shrink-0">Dup %</span>
              <span className="text-[11px] text-slate-400 tabular-nums">
                {snap?.duplicates?.dup_pct != null ? `${snap.duplicates.dup_pct.toFixed(1)}%` : "—"}
              </span>
            </div>
          </div>
        </div>

        {/* Panel 2: Absorption */}
        {(() => {
          const avgSale = (lcSummary?.avg_implied_sale_price as number | null) ?? null;
          const sold24  = vel?.windows?.["24h"]?.implied_sale_listings ?? null;
          const sold7d  = vel?.windows?.["7d"]?.implied_sale_listings ?? null;
          const tixSold = vel?.windows?.since_tracking?.implied_sale_tickets ?? null;
          const invSince = (lcSummary?.assumed_sales as number | null) ?? null;
          const rows = [
            { label: "Tickets Sold", val: tixSold },
            { label: "24H Sold",     val: sold24  },
            { label: "7D Sold",      val: sold7d  },
            { label: "Since Tracking", val: invSince },
          ];
          return (
            <div className="p-5 bg-white/[0.02]">
              <p className="text-[11px] text-slate-400 uppercase tracking-[0.18em] font-semibold mb-4">
                Absorption <span className="normal-case tracking-normal font-normal text-slate-500">(Sales Driven)</span>
              </p>
              <div className="mb-4 pb-3 border-b border-white/[0.06]">
                <p className="text-[11px] text-slate-500 mb-2 uppercase tracking-[0.12em]">Est. Avg Sale Price</p>
                {avgSale != null ? (
                  <p className="text-[36px] font-black text-amber-300 tabular-nums leading-none">{fmt$$(avgSale)}</p>
                ) : (
                  <>
                    <p className="text-[18px] font-semibold text-slate-600 italic leading-none">
                      {lcSummary != null ? "No disappearances yet" : "Collecting data…"}
                    </p>
                  </>
                )}
              </div>
              <div>
                {rows.map(({ label, val }) => (
                  <div key={label} className="flex items-center justify-between py-2.5 border-b border-white/[0.05] last:border-0">
                    <span className="text-[11px] text-slate-400">{label}</span>
                    {val != null && val > 0
                      ? <span className="text-[12px] font-semibold text-emerald-400 tabular-nums">{fmtNum(val)}</span>
                      : val === 0
                      ? <span className="text-[11px] italic text-slate-600">No disappearances</span>
                      : <span className="text-[11px] italic text-slate-700">—</span>}
                  </div>
                ))}
              </div>
            </div>
          );
        })()}

        {/* Panel 3: Seller Behavior */}
        {(() => {
          const repriceDelta = seller?.median_reprice_delta ?? null;
          const repriced24   = seller?.repriced_24h ?? null;
          const drops24      = seller?.price_drops_24h ?? null;
          const churn        = seller?.churn_rate ?? null;
          // Seller mood from capitulation + aggression
          const cap  = seller?.capitulation_score ?? null;
          const aggr = seller?.seller_aggression ?? null;
          const drops    = seller?.price_drops_24h ?? 0;
          const repriced = seller?.repriced_24h ?? 0;
          const dropRatio = repriced > 0 ? drops / repriced : 0;
          const mood = cap == null ? null
            : cap > 0.70 ? "Seller capitulation increasing"
            : cap > 0.55 || (aggr != null && aggr > 0.65) ? "Repricing accelerating"
            : cap > 0.40 || dropRatio > 0.55 ? "Aggressive repricing"
            : cap > 0.25 && dropRatio < 0.3 ? "Price cuts slowing"
            : cap <= 0.20 ? "Holding firm"
            : "Stable seller behavior";
          const moodCls = mood === "Seller capitulation increasing" || mood === "Repricing accelerating" ? "text-red-300"
            : mood === "Aggressive repricing" ? "text-amber-300"
            : mood === "Price cuts slowing" ? "text-amber-300/70"
            : mood === "Holding firm" || mood === "Stable seller behavior" ? "text-emerald-300"
            : "text-slate-500";
          return (
            <div className="p-5">
              <p className="text-[11px] text-slate-400 uppercase tracking-[0.18em] font-semibold mb-4">
                Seller Behavior <span className="normal-case tracking-normal font-normal text-slate-500">(24H)</span>
              </p>
              <div>
                <div className="flex items-center justify-between py-2.5 border-b border-white/[0.05]">
                  <span className="text-[11px] text-slate-400">Relist Price Chg</span>
                  {repriceDelta != null
                    ? <span className={cn("text-[13px] font-bold tabular-nums", repriceDelta < 0 ? "text-red-300" : "text-emerald-300")}>
                        {repriceDelta > 0 ? "+" : ""}{fmt$$(repriceDelta)}
                      </span>
                    : <span className="text-[11px] italic text-slate-600">{seller ? "No relist activity" : "—"}</span>}
                </div>
                <div className="flex items-center justify-between py-2.5 border-b border-white/[0.05]">
                  <span className="text-[11px] text-slate-400">Price Drops</span>
                  {drops24 != null
                    ? drops24 > 0
                      ? <span className="text-[12px] font-semibold text-red-400 tabular-nums">{fmtNum(drops24)}</span>
                      : <span className="text-[11px] italic text-slate-600">No price drops</span>
                    : <span className="text-[11px] italic text-slate-700">—</span>}
                </div>
                <div className="flex items-center justify-between py-2.5 border-b border-white/[0.05]">
                  <span className="text-[11px] text-slate-400">Repriced Listings</span>
                  {repriced24 != null
                    ? repriced24 > 0
                      ? <span className="text-[12px] font-semibold text-amber-400 tabular-nums">{fmtNum(repriced24)}</span>
                      : <span className="text-[11px] italic text-slate-600">No repricing detected</span>
                    : <span className="text-[11px] italic text-slate-700">—</span>}
                </div>
                <div className="flex items-start justify-between py-2.5 border-l-2 border-slate-600/40 pl-2.5 -ml-2.5 mt-0.5">
                  <span className="text-[11px] text-slate-400">Seller Mood</span>
                  <span className={cn("text-[12px] font-medium italic text-right max-w-[55%]", moodCls)}>
                    {mood ?? (seller ? "No seller movement yet" : "Not enough history")}
                  </span>
                </div>
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
}

// ── Marketplace Health Strip ──────────────────────────────────────────────────
// Answers: "Can I trust today's market data?" — aggregate market confidence signal
function MarketplaceHealthStrip({ events }: { events: EventSummary[] }) {
  if (events.length === 0) return null;

  const withPrice  = events.filter(e => e.price?.low_ask != null).length;
  const withInv    = events.filter(e => e.inventory?.total_listings > 0).length;
  const freshCov   = events.filter(e => (e.inventory?.fresh_total_listings ?? 0) > 0).length;
  const coverage   = Math.round((withPrice / events.length) * 100);

  const floors     = events.map(e => e.price?.low_ask).filter((v): v is number => v != null);
  const highs      = events.map(e => e.price?.high_ask).filter((v): v is number => v != null);
  const totalInv   = events.reduce((s, e) => s + (e.inventory?.total_listings ?? 0), 0);
  const invDeltas  = events.map(e => e.changes?.h24?.inventory_delta).filter((v): v is number => v != null);
  const netDelta   = invDeltas.length > 0 ? invDeltas.reduce((s, v) => s + v, 0) : null;

  const health     = coverage >= 80 ? "live" : coverage >= 50 ? "partial" : "sparse";
  const healthCls  = health === "live" ? "text-emerald-400" : health === "partial" ? "text-amber-400" : "text-slate-500";
  const dotCls     = health === "live" ? "bg-emerald-400" : health === "partial" ? "bg-amber-400" : "bg-slate-500";

  const statItems = [
    { label: "Events", val: String(events.length), sub: null },
    { label: "Live Coverage", val: `${coverage}%`, sub: health === "live" ? "fresh" : health === "partial" ? "partial" : "sparse" },
    { label: "Total Inventory", val: fmtNum(totalInv), sub: netDelta != null ? (netDelta >= 0 ? `+${netDelta} 24h` : `${netDelta} 24h`) : null },
    { label: "Price Range", val: floors.length > 0 ? `${fmt$$(Math.min(...floors))}–${fmt$$(Math.max(...highs || [Math.min(...floors)]))}` : "—", sub: null },
    { label: "Fresh Data", val: `${freshCov}/${events.length}`, sub: "events" },
  ];

  return (
    <div className="rounded-xl border border-white/[0.06] bg-[#07080d] px-6 py-3.5 mb-4">
      <div className="flex items-center gap-8 flex-wrap">
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className={`w-1.5 h-1.5 rounded-full ${dotCls} ${health === "live" ? "animate-pulse" : ""}`} />
          <span className={`text-[12px] font-bold uppercase tracking-[0.18em] ${healthCls}`}>
            {health === "live" ? "Live" : health === "partial" ? "Partial" : "Sparse"}
          </span>
          <span className="text-[11px] text-white/20 hidden sm:block">market data</span>
        </div>
        <div className="w-px h-5 bg-white/[0.06] hidden sm:block" />
        {statItems.slice(1).map(({ label, val, sub }) => (
          <div key={label} className="flex flex-col gap-0.5">
            <span className="text-[11px] text-white/22 uppercase tracking-[0.14em]">{label}</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-[14px] font-bold text-white/65 tabular-nums">{val}</span>
              {sub && <span className="text-[11px] text-white/25">{sub}</span>}
            </div>
          </div>
        ))}
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

  const firstMeta      = metas[events[0]?.event_id];
  const gradient       = getEventGradient(firstMeta?.artist, firstMeta?.title ?? events[0]?.title ?? groupKey);
  const autoArtworkUrl = useArtistImage(firstMeta?.artist ?? groupKey, firstMeta?.title);
  const artworkUrl     = firstMeta?.custom_artwork_url ?? autoArtworkUrl;
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
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Low</span>
                    <span className="text-base font-bold text-emerald-300 tabular-nums">{fmt$$(lowestPrice)}</span>
                  </div>
                )}
                {medianRange && (
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Median</span>
                    <span className="text-base text-slate-300 tabular-nums font-semibold">{medianRange}</span>
                  </div>
                )}
                {totalInvDelta != null && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">Inv Δ</span>
                    <span className={`text-sm font-bold flex items-center gap-0.5 tabular-nums ${totalInvDelta > 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {totalInvDelta > 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                      {totalInvDelta > 0 ? "+" : ""}{totalInvDelta}
                    </span>
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
                        <span className="text-[11px] font-bold uppercase tracking-wide" style={{ color: b.textColor }}>{b.short}</span>
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
        <span className="text-[11px] text-white/25 uppercase tracking-[0.22em] font-bold flex-shrink-0">Intel</span>
        <div className="flex items-center gap-1">
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">Trend</span>
          <span className="text-xs text-white/25">—</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">Buy Window</span>
          <span className="text-xs text-white/25">—</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">Signal</span>
          <span className="text-xs text-white/25">—</span>
        </div>
      </div>

      {/* NFL audio chip — inline, always visible for NFL groups */}
      {isNflEvent(groupKey, firstMeta?.artist) && nflAudioState && (
        <div className="flex items-center gap-2.5 px-4 py-2.5 mt-1 rounded-xl border border-amber-500/20 bg-amber-500/5">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${nflAudioState.playing ? "bg-amber-400 animate-pulse" : nflAudioState.errorMsg ? "bg-red-400" : "bg-amber-400/40"}`} />
          <span className="text-[11px] font-bold text-white/50 uppercase tracking-widest">NFL Theme</span>
          {nflAudioState.errorMsg ? (
            <span className="text-[11px] text-red-400/80">{nflAudioState.errorMsg}</span>
          ) : nflAudioState.playing ? (
            <span className="text-[11px] text-amber-400 font-medium">Playing</span>
          ) : nflAudioState.blocked ? (
            <button onClick={nflAudioState.onPlay} className="text-[11px] text-amber-400 border border-amber-500/30 rounded px-2 py-0.5 bg-amber-500/8 hover:bg-amber-500/15 transition-colors">Tap to play</button>
          ) : (
            <span className="text-[11px] text-white/25">Click row to play</span>
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

      const depthMap: Record<number, number | null> = {};
      evts.forEach((e) => {
        depthMap[e.event_id] = e.history_hours != null ? e.history_hours / 24 : null;
      });
      setDepths(depthMap);

      // Render immediately — meta calls load in background without blocking
      setLoading(false);

      Promise.allSettled(evts.map((e) => api.events.meta(e.event_id))).then((results) => {
        const metaMap: MetaMap = {};
        evts.forEach((e, i) => {
          const r = results[i];
          if (r.status === "fulfilled") metaMap[e.event_id] = r.value;
        });
        setMetas(metaMap);
      });
    } catch (e) {
      setError(String(e));
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
          <h1 className="text-2xl font-bold tracking-tight text-white">Active Markets</h1>
          <p className="text-xs text-slate-500 mt-1">
            {loading ? "Loading…" : `${events.length} events · ${groups.length} artists`}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg border border-white/[0.07] text-xs text-slate-500 bg-white/[0.01]">
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
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/[0.07] text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors"
            >
              <Eye size={12} />
              {showHidden ? "Hide hidden" : `${hiddenCount} hidden`}
            </button>
          )}
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/[0.07] text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors disabled:opacity-40"
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
          {/* Marketplace Health Strip — per-MP data quality signal */}
          <MarketplaceHealthStrip events={visible} />

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
