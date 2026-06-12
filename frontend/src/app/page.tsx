"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Eye, RefreshCw, TrendingUp, TrendingDown, Minus, AlertCircle, ChevronDown, ChevronRight, BarChart2 } from "lucide-react";
import { format, parseISO, differenceInDays } from "date-fns";
import { api } from "@/lib/api";
import type { EventSummary, HistoryResponse } from "@/lib/types";
import { fmt$$, fmtNum, signalToAction, actionColors, signalDescription } from "@/lib/utils";
import { getEventGradient, gradientBg, extractGroupKey } from "@/lib/entityimages";
import { useHiddenEvents } from "@/hooks/useHiddenEvents";
import EventCard from "@/components/EventCard";

type SortKey = "date" | "opportunity" | "signal";
const SIGNAL_ORDER = ["deepening", "capitulating", "mixed", "stable", "loosening"];

// Depth cache
const depthCache: Record<number, number | null> = {};
async function fetchDepth(id: number): Promise<number | null> {
  if (id in depthCache) return depthCache[id];
  try {
    const r: HistoryResponse = await api.events.history(id, "all");
    depthCache[id] = r.data_depth_days ?? null;
    return depthCache[id];
  } catch {
    depthCache[id] = null;
    return null;
  }
}

type MetaMap = Record<number, { title?: string; venue_name?: string; venue_slug?: string; event_date?: string; artist?: string }>;

// ── Headline featured event ───────────────────────────────────────────────────
function HeadlineEvent({
  event,
  meta,
  depth,
}: {
  event: EventSummary;
  meta: MetaMap[number] | undefined;
  depth: number | null | undefined;
}) {
  const title = meta?.title ?? event.title;
  const venue = meta?.venue_name;
  const dateStr = meta?.event_date;
  const artist = meta?.artist;

  const action = signalToAction(event.signal);
  const colors = actionColors(action);
  const gradient = getEventGradient(artist, title);

  let daysOut: number | null = null;
  let dateLabel = "";
  if (dateStr) {
    try {
      const d = parseISO(dateStr);
      daysOut = differenceInDays(d, new Date());
      dateLabel = format(d, "EEEE, MMMM d, yyyy");
    } catch {}
  }

  const desc = signalDescription(event.signal);
  const priceLow = event.price?.low_ask;
  const priceMed = event.price?.median_ask;
  const priceHigh = event.price?.high_ask;

  return (
    <Link href={`/events/${event.event_id}`}>
      <div
        className="relative w-full rounded-2xl overflow-hidden border border-white/8 mb-8"
        style={{ minHeight: 220, background: gradientBg(gradient, "high") }}
      >
        {/* dark overlay for readability */}
        <div
          className="absolute inset-0"
          style={{
            background: "linear-gradient(to right, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0.3) 50%, rgba(0,0,0,0.65) 100%)",
          }}
        />

        {/* content grid */}
        <div className="relative z-10 flex flex-col sm:flex-row items-stretch p-6 gap-6">

          {/* LEFT — event info */}
          <div className="flex-1 flex flex-col justify-center">
            {artist && (
              <p className="text-[11px] text-white/50 uppercase tracking-widest font-medium mb-1">{artist}</p>
            )}
            <h2 className="text-2xl font-bold text-white leading-tight mb-2">{title}</h2>
            {venue && <p className="text-sm text-white/60 mb-1">{venue}</p>}
            {dateLabel && <p className="text-sm text-white/50">{dateLabel}</p>}
            {daysOut != null && (
              <div className="mt-3">
                <span
                  className="text-xs font-semibold px-2.5 py-1 rounded-full border"
                  style={{ color: colors.text, background: colors.bg, borderColor: colors.border }}
                >
                  {daysOut === 0 ? "Today" : daysOut === 1 ? "Tomorrow" : `${daysOut} days away`}
                </span>
              </div>
            )}
          </div>

          {/* CENTER — action signal */}
          <div className="flex flex-col items-center justify-center flex-shrink-0 px-4">
            <div
              className="px-8 py-4 rounded-2xl border mb-2"
              style={{
                background: colors.bg,
                borderColor: colors.border,
                boxShadow: `0 0 40px ${colors.glow}`,
              }}
            >
              <span
                className="text-5xl font-black tracking-[0.2em]"
                style={{ color: colors.text }}
              >
                {action}
              </span>
            </div>
            <p className="text-[11px] text-white/50 text-center max-w-[180px] leading-relaxed">{desc}</p>
          </div>

          {/* RIGHT — prices + inventory */}
          <div className="flex flex-col justify-center gap-3 flex-shrink-0 sm:text-right">
            {/* Price grid */}
            <div>
              <p className="text-[10px] text-white/40 uppercase tracking-wider mb-2">Price Range</p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 sm:text-right">
                <div>
                  <p className="text-[9px] text-white/35 uppercase tracking-wide">Lowest Price</p>
                  <p className="text-xl font-bold text-white tabular-nums">{fmt$$(priceLow)}</p>
                </div>
                <div>
                  <p className="text-[9px] text-white/35 uppercase tracking-wide">Median Price</p>
                  <p className="text-xl font-bold text-white/80 tabular-nums">{fmt$$(priceMed)}</p>
                </div>
              </div>
              {priceHigh != null && (
                <p className="text-[10px] text-white/30 mt-1 tabular-nums sm:text-right">
                  high {fmt$$(priceHigh)}
                </p>
              )}
            </div>
            <div className="pt-2 border-t border-white/10">
              <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Inventory</p>
              <p className="text-sm font-semibold text-white/80">
                <BarChart2 size={11} className="inline mr-1 opacity-50" />
                {fmtNum(event.inventory?.total_listings)} listings
              </p>
              <p className="text-[10px] text-white/35 mt-0.5">
                {fmtNum(event.inventory?.total_tickets)} tickets
              </p>
              {depth != null && (
                <p className={`text-[10px] mt-1 font-medium ${depth >= 7 ? "text-emerald-400" : "text-amber-400"}`}>
                  {depth >= 1 ? `${Math.round(depth)}d of history` : "Live data only"}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}

// ── Artist group ──────────────────────────────────────────────────────────────
function EventGroup({
  groupKey,
  events,
  metas,
  depths,
  onHide,
  onSelect,
  selectedId,
}: {
  groupKey: string;
  events: EventSummary[];
  metas: MetaMap;
  depths: Record<number, number | null>;
  onHide: (id: number) => void;
  onSelect: (id: number) => void;
  selectedId: number | null;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const topAction = signalToAction(events[0]?.signal);
  const topColors = actionColors(topAction);

  return (
    <div className="mb-6">
      <button
        onClick={() => setCollapsed(v => !v)}
        className="flex items-center gap-2 mb-3 group"
      >
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">{groupKey}</span>
        <span className="text-[10px] text-slate-600 font-normal">
          {events.length} {events.length === 1 ? "event" : "events"}
        </span>
        <span
          className="text-[9px] font-black tracking-widest px-1.5 py-0.5 rounded border ml-1"
          style={{ color: topColors.text, background: topColors.bg, borderColor: topColors.border }}
        >
          {topAction}
        </span>
        <span className="text-slate-600 ml-1">
          {collapsed ? <ChevronRight size={12} /> : <ChevronDown size={12} />}
        </span>
      </button>

      {!collapsed && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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

// ── Page ──────────────────────────────────────────────────────────────────────
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

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.events.list();
      const evts = data.events ?? [];
      setEvents(evts);

      // default selection = highest opportunity_score
      if (selectedId === null && evts.length > 0) {
        const best = [...evts].sort((a, b) => (b.opportunity_score ?? 0) - (a.opportunity_score ?? 0))[0];
        setSelectedId(best.event_id);
      }

      // Fetch metadata (title, venue, date, artist)
      const metaResults = await Promise.allSettled(evts.map((e) => api.events.meta(e.event_id)));
      const metaMap: MetaMap = {};
      evts.forEach((e, i) => {
        const r = metaResults[i];
        if (r.status === "fulfilled") {
          metaMap[e.event_id] = {
            title: r.value.title,
            venue_name: r.value.venue_name,
            venue_slug: r.value.venue_slug,
            event_date: r.value.event_date,
            artist: r.value.artist,
          };
        }
      });
      setMetas(metaMap);

      // Fetch data depths in background
      const depthResults = await Promise.allSettled(evts.map((e) => fetchDepth(e.event_id)));
      const depthMap: Record<number, number | null> = {};
      evts.forEach((e, i) => {
        const r = depthResults[i];
        depthMap[e.event_id] = r.status === "fulfilled" ? r.value : null;
      });
      setDepths(depthMap);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Build sorted, filtered event list
  const visible = useMemo(() => {
    const base = mounted && !showHidden
      ? events.filter((e) => !hiddenEvents.has(e.event_id))
      : events;

    return [...base].sort((a, b) => {
      if (sort === "opportunity") return (b.opportunity_score ?? 0) - (a.opportunity_score ?? 0);
      if (sort === "signal") return SIGNAL_ORDER.indexOf(a.signal) - SIGNAL_ORDER.indexOf(b.signal);
      const da = metas[a.event_id]?.event_date ?? "";
      const db = metas[b.event_id]?.event_date ?? "";
      return da.localeCompare(db);
    });
  }, [events, metas, sort, hiddenEvents, showHidden, mounted]);

  // Group by artist
  const groups = useMemo(() => {
    const map: Record<string, EventSummary[]> = {};
    for (const e of visible) {
      const key = extractGroupKey(metas[e.event_id]?.artist, metas[e.event_id]?.title ?? e.title);
      if (!map[key]) map[key] = [];
      map[key].push(e);
    }
    // Sort groups: groups with BUY signal first, then by max opportunity_score
    return Object.entries(map).sort(([, ae], [, be]) => {
      const aScore = Math.max(...ae.map(e => e.opportunity_score ?? 0));
      const bScore = Math.max(...be.map(e => e.opportunity_score ?? 0));
      return bScore - aScore;
    });
  }, [visible, metas]);

  const selectedEvent = useMemo(
    () => events.find((e) => e.event_id === selectedId) ?? events[0] ?? null,
    [events, selectedId],
  );

  const hiddenCount = mounted ? hiddenEvents.size : 0;

  return (
    <div>
      {/* page header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-lg font-semibold text-slate-100">Watchlist</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {loading ? "Loading…" : `${events.length} events · ${groups.length} artists`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-white/7 overflow-hidden text-xs">
            {(["opportunity", "date", "signal"] as SortKey[]).map((k) => (
              <button
                key={k}
                onClick={() => setSort(k)}
                className={`px-3 py-1.5 capitalize transition-colors ${
                  sort === k ? "bg-white/10 text-slate-200" : "text-slate-500 hover:text-slate-300 hover:bg-white/5"
                }`}
              >
                {k}
              </button>
            ))}
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

      {/* error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-4">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      {/* loading skeleton */}
      {loading && events.length === 0 && (
        <div className="space-y-6">
          <div className="h-56 rounded-2xl border border-white/5 bg-[#161b27] animate-pulse" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-48 rounded-xl border border-white/5 bg-[#161b27] animate-pulse" />
            ))}
          </div>
        </div>
      )}

      {/* empty */}
      {!loading && visible.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-slate-500">
          <TrendingUp size={32} className="mb-3 opacity-30" />
          <p className="text-sm">No events</p>
        </div>
      )}

      {/* headline + groups */}
      {visible.length > 0 && (
        <>
          {/* Featured headline */}
          {selectedEvent && (
            <HeadlineEvent
              event={selectedEvent}
              meta={metas[selectedEvent.event_id]}
              depth={depths[selectedEvent.event_id]}
            />
          )}

          {/* Event groups */}
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
            />
          ))}
        </>
      )}
    </div>
  );
}
