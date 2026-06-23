"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { List, Calendar, ChevronRight, CheckCircle2, Activity, Pin, Archive, EyeOff } from "lucide-react";
import { format, parseISO, differenceInDays } from "date-fns";
import { api } from "@/lib/api";
import type { RawEvent } from "@/lib/types";
import { fmt$$ } from "@/lib/utils";
import { getEventGradient } from "@/lib/entityimages";
import { useArtistImage } from "@/hooks/useArtistImage";
import { useHeadlineEvent } from "@/hooks/useHeadlineEvent";
import { useArchivedEvents } from "@/hooks/useArchivedEvents";
import { useHiddenEvents } from "@/hooks/useHiddenEvents";
import { getBrand } from "@/components/MarketplaceBadge";

// ── Per-row component so useArtistImage hook is legal ────────────────────────
function EventRow({
  ev, now, pinnedId, archivedEvents, hiddenEvents,
  onPin, onClearPin, onToggleArchive, onToggleHide,
}: {
  ev: RawEvent;
  now: Date;
  pinnedId: number | null;
  archivedEvents: Set<number>;
  hiddenEvents: Set<number>;
  onPin: (id: number) => void;
  onClearPin: () => void;
  onToggleArchive: (id: number) => void;
  onToggleHide: (id: number) => void;
}) {
  const past   = new Date(ev.event_date).getTime() + 24 * 3600 * 1000 < now.getTime();
  const evId   = ev.id;
  const isPin  = pinnedId === evId;
  const isArch = archivedEvents.has(evId);
  const isHide = hiddenEvents.has(evId);

  let daysOut: number | null = null;
  let dateLabel = "";
  try {
    const d = parseISO(ev.event_date);
    daysOut = differenceInDays(d, now);
    dateLabel = format(d, "MMM d, yyyy");
  } catch {}

  const prices     = ev.all_marketplace_prices ?? ev.marketplace_prices ?? {};
  const gradient   = getEventGradient(ev.artist, ev.title);
  const artworkUrl = useArtistImage(ev.artist, ev.title);
  const floorPrice = ev.lowest_price ??
    (Object.values(prices).filter((p): p is number => p != null).sort((a, b) => a - b)[0] ?? null);

  return (
    <tr
      className={`border-b border-white/4 last:border-0 hover:bg-white/2 transition-colors
        ${isHide ? "opacity-40" : ""} ${isArch ? "bg-amber-500/3" : ""}`}
    >
      {/* Event identity */}
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-3">
          {/* Artwork thumbnail */}
          <div
            className="flex-shrink-0 w-9 h-9 rounded-lg overflow-hidden"
            style={{ background: `linear-gradient(145deg, ${gradient[0]}cc, ${gradient[1]}88)` }}
          >
            {artworkUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={artworkUrl} alt="" className="w-full h-full object-cover object-top"
                onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
            ) : (
              <span className="w-full h-full flex items-center justify-center text-sm font-bold text-white/40 select-none">
                {(ev.artist ?? ev.title).slice(0, 1).toUpperCase()}
              </span>
            )}
          </div>

          {isPin && (
            <div className="w-1 h-7 rounded-sm flex-shrink-0 bg-amber-500" />
          )}

          <div className="min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <Link href={`/events/${evId}`}
                className="font-medium text-slate-100 hover:text-blue-300 transition-colors line-clamp-1">
                {ev.title}
              </Link>
              {isPin && (
                <span className="flex-shrink-0 text-[9px] text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded px-1 py-0.5 font-bold uppercase tracking-wider">
                  Headline
                </span>
              )}
              {isArch && (
                <span className="flex-shrink-0 text-[9px] text-amber-500/60 border border-amber-500/15 rounded px-1 py-0.5">
                  Archived
                </span>
              )}
              {past ? (
                <span className="flex-shrink-0 inline-flex items-center gap-0.5 text-[9px] text-slate-500 bg-white/5 rounded px-1 py-0.5">
                  <CheckCircle2 size={7} /> done
                </span>
              ) : daysOut != null && daysOut <= 7 ? (
                <span className="flex-shrink-0 text-[9px] text-amber-500 bg-amber-500/10 rounded px-1 py-0.5">
                  {daysOut === 0 ? "Today" : `${daysOut}d`}
                </span>
              ) : null}
            </div>
            {ev.artist && (
              <p className="text-[10px] text-slate-600 mt-0.5">{ev.artist}</p>
            )}
          </div>
        </div>
      </td>

      {/* Date */}
      <td className="px-3 py-2.5 text-slate-500 hidden sm:table-cell whitespace-nowrap text-xs">
        {dateLabel}
      </td>

      {/* Venue */}
      <td className="px-3 py-2.5 text-slate-500 hidden md:table-cell max-w-[140px] truncate text-xs">
        {ev.venue_name ?? "—"}
      </td>

      {/* Floor */}
      <td className="px-3 py-2.5 text-right">
        <span className="font-semibold text-slate-200 tabular-nums text-sm">{fmt$$(floorPrice)}</span>
      </td>

      {/* Listings */}
      <td className="px-3 py-2.5 text-right text-slate-500 tabular-nums hidden sm:table-cell text-xs">
        {ev.fresh_total_listings ?? ev.total_listings ?? "—"}
      </td>

      {/* Marketplace strip */}
      <td className="px-3 py-2.5 hidden lg:table-cell">
        <div className="flex items-center gap-1">
          {Object.entries(prices)
            .filter(([, p]) => p != null)
            .sort(([, a], [, b]) => (a as number) - (b as number))
            .map(([slug, price]) => {
              const b = getBrand(slug);
              return (
                <div key={slug} className="flex flex-col items-center rounded px-1.5 py-0.5 border"
                  style={{ background: b.bg, borderColor: b.border }}>
                  <span className="text-[8px] font-bold uppercase tracking-wide" style={{ color: b.textColor }}>
                    {b.short}
                  </span>
                  <span className="text-[10px] text-white/60 tabular-nums font-medium">
                    {fmt$$(price as number)}
                  </span>
                </div>
              );
            })}
        </div>
      </td>

      {/* Action buttons */}
      <td className="px-3 py-2.5 hidden xl:table-cell">
        <div className="flex items-center gap-1">
          <button onClick={() => isPin ? onClearPin() : onPin(evId)}
            title={isPin ? "Unpin headline" : "Set as headline"}
            className="p-1 rounded hover:bg-white/10 transition-colors">
            {isPin
              ? <Pin size={11} className="text-amber-400 fill-amber-400" />
              : <Pin size={11} className="text-slate-600 hover:text-slate-400" />}
          </button>
          <button onClick={() => onToggleArchive(evId)}
            title={isArch ? "Restore from archive" : "Archive"}
            className="p-1 rounded hover:bg-white/10 transition-colors">
            <Archive size={11} className={isArch ? "text-amber-400" : "text-slate-600 hover:text-slate-400"} />
          </button>
          <button onClick={() => onToggleHide(evId)}
            title={isHide ? "Unhide" : "Hide from dashboard"}
            className="p-1 rounded hover:bg-white/10 transition-colors">
            <EyeOff size={11} className={isHide ? "text-slate-300" : "text-slate-600 hover:text-slate-400"} />
          </button>
        </div>
      </td>

      {/* Chevron */}
      <td className="px-3 py-2.5">
        <Link href={`/events/${evId}`} className="text-slate-600 hover:text-slate-300 transition-colors">
          <ChevronRight size={14} />
        </Link>
      </td>
    </tr>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function AllEventsPage() {
  const [events, setEvents] = useState<RawEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "active" | "completed">("all");

  const { pinnedId, pin, clear: clearPin } = useHeadlineEvent();
  const { archivedEvents, toggle: toggleArchive } = useArchivedEvents();
  const { hiddenEvents, toggle: toggleHide } = useHiddenEvents();

  useEffect(() => {
    api.events.all().then((all) => {
      all.sort((a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime());
      setEvents(all);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const now = new Date();
  // +24h grace mirrors backend: event_dates stored as midnight UTC = 5 PM PDT prior day.
  // An event is "past" only after event_date + 24h has elapsed.
  const isPast = (dateStr: string) => new Date(dateStr).getTime() + 24 * 3600 * 1000 < now.getTime();
  const filtered = events.filter((e) => {
    const past = isPast(e.event_date);
    if (filter === "active") return !past;
    if (filter === "completed") return past;
    return true;
  });

  const activeCount    = events.filter((e) => !isPast(e.event_date)).length;
  const completedCount = events.filter((e) => isPast(e.event_date)).length;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <List size={16} className="text-slate-400" />
            <h1 className="text-lg font-semibold text-white">All Events</h1>
            {!loading && (
              <span className="text-xs text-slate-500 bg-white/5 rounded-full px-2 py-0.5">
                {filtered.length} events
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500">Complete inventory catalog — everything tracked.</p>
        </div>

        <div className="flex rounded-lg border border-white/7 overflow-hidden text-xs">
          {(["all", "active", "completed"] as const).map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 capitalize transition-colors ${
                filter === f ? "bg-white/10 text-slate-200" : "text-slate-500 hover:text-slate-300 hover:bg-white/5"
              }`}>
              {f === "all" ? `All (${events.length})` : f === "active" ? `Active (${activeCount})` : `Completed (${completedCount})`}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-14 rounded-xl border border-white/5 bg-[#161b27] animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center space-y-3">
          <Activity size={32} className="text-white/15" />
          <p className="text-slate-500">No events in this category</p>
        </div>
      ) : (
        <div className="rounded-xl border border-white/8 overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-white/5 bg-white/2">
                <th className="text-left px-4 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium">Event</th>
                <th className="text-left px-3 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium hidden sm:table-cell">Date</th>
                <th className="text-left px-3 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium hidden md:table-cell">Venue</th>
                <th className="text-right px-3 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium">Floor</th>
                <th className="text-right px-3 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium hidden sm:table-cell">Listings</th>
                <th className="text-left px-3 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium hidden lg:table-cell">Marketplaces</th>
                <th className="px-3 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium hidden xl:table-cell w-24">Actions</th>
                <th className="px-3 py-2.5 w-8" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((ev) => (
                <EventRow
                  key={ev.id}
                  ev={ev}
                  now={now}
                  pinnedId={pinnedId}
                  archivedEvents={archivedEvents}
                  hiddenEvents={hiddenEvents}
                  onPin={pin}
                  onClearPin={clearPin}
                  onToggleArchive={toggleArchive}
                  onToggleHide={toggleHide}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
