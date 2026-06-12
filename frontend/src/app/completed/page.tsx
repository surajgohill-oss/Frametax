"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { RawEvent } from "@/lib/types";
import { CheckCircle2, TrendingUp, Package, Calendar, ChevronRight, BarChart3 } from "lucide-react";

const fmt$ = (v: number | null | undefined) =>
  v == null ? "—" : `$${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

const fmtDate = (iso: string) => {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" });
};

const venueShort = (slug: string | undefined) => {
  if (!slug) return "";
  const map: Record<string, string> = {
    "sofi-stadium": "SoFi Stadium",
    "crypto-com-arena": "Crypto.com Arena",
    "kia-forum": "Kia Forum",
    "hollywood-bowl": "Hollywood Bowl",
    "greek-theatre": "Greek Theatre LA",
    "oakland-arena": "Oakland Arena",
  };
  return map[slug] ?? slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
};

export default function CompletedPage() {
  const [events, setEvents] = useState<RawEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.events.all().then((all) => {
      const now = new Date();
      const past = all.filter((e) => new Date(e.event_date) < now);
      // Sort newest first
      past.sort((a, b) => new Date(b.event_date).getTime() - new Date(a.event_date).getTime());
      setEvents(past);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="w-4 h-4 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={18} className="text-slate-400" />
          <h1 className="text-lg font-semibold text-white">Completed Events</h1>
        </div>
        <span className="text-xs text-slate-500 bg-white/5 rounded-full px-2 py-0.5">
          {events.length} {events.length === 1 ? "event" : "events"}
        </span>
      </div>

      <p className="text-sm text-slate-500 -mt-3">
        Final market reports for past events. Data reflects the last collected snapshot before the event date.
      </p>

      {events.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center py-20 text-center space-y-3">
          <BarChart3 size={36} className="text-white/15" />
          <p className="text-slate-400 font-medium">No completed events yet</p>
          <p className="text-sm text-slate-600 max-w-xs">
            Events will appear here after their date has passed.
            Currently tracking active events on the{" "}
            <Link href="/" className="text-blue-400 hover:underline">dashboard</Link>.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {events.map((ev) => (
            <CompletedEventCard key={ev.id} event={ev} />
          ))}
        </div>
      )}
    </div>
  );
}

function CompletedEventCard({ event: ev }: { event: RawEvent }) {
  const hasData = (ev.historical_lowest_price ?? 0) > 0 || (ev.total_listings ?? 0) > 0;
  const marketplaces = Object.keys(ev.all_marketplace_prices ?? {});

  return (
    <Link href={`/events/${ev.id}`} className="block group">
      <div className="relative rounded-xl border border-white/8 bg-white/3 hover:bg-white/5 hover:border-white/12 transition-all p-4 space-y-3">
        {/* Completed badge */}
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500 bg-white/5 rounded-full px-2 py-0.5">
            <CheckCircle2 size={9} />
            Completed
          </span>
          <ChevronRight size={14} className="text-white/20 group-hover:text-white/40 transition-colors" />
        </div>

        {/* Title */}
        <div>
          <p className="text-sm font-semibold text-white leading-tight line-clamp-2">{ev.title}</p>
          <p className="text-xs text-slate-500 mt-0.5">{venueShort(ev.venue_slug)}</p>
        </div>

        {/* Date */}
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Calendar size={11} />
          <span>{fmtDate(ev.event_date)}</span>
        </div>

        {/* Market outcome */}
        {hasData ? (
          <div className="grid grid-cols-2 gap-2 pt-1">
            <div className="bg-black/20 rounded-lg p-2">
              <p className="text-[9px] text-white/30 uppercase tracking-wide mb-0.5">Final Low Ask</p>
              <p className="text-sm font-semibold text-white tabular-nums">
                {fmt$(ev.historical_lowest_price)}
              </p>
            </div>
            <div className="bg-black/20 rounded-lg p-2">
              <p className="text-[9px] text-white/30 uppercase tracking-wide mb-0.5">Total Listings</p>
              <p className="text-sm font-semibold text-white tabular-nums">
                {(ev.total_listings ?? 0).toLocaleString()}
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-black/20 rounded-lg p-2.5 text-center">
            <p className="text-xs text-slate-600">No market data collected</p>
          </div>
        )}

        {/* Marketplace chips */}
        {marketplaces.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-0.5">
            {marketplaces.map((mp) => (
              <span key={mp} className="text-[10px] text-slate-600 bg-white/4 rounded px-1.5 py-0.5">
                {mp}
              </span>
            ))}
          </div>
        )}

        {/* View report link */}
        <div className="flex items-center gap-1 text-[11px] text-blue-400/70 group-hover:text-blue-400 transition-colors">
          <BarChart3 size={11} />
          <span>View Final Report</span>
        </div>
      </div>
    </Link>
  );
}
