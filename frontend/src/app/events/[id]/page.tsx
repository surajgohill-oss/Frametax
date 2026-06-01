"use client";
import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { fmt$, fmtDate } from "@/lib/utils";
import { MapPin, CalendarDays, RefreshCw, ChevronLeft, Ticket, Star, Map, AlertTriangle } from "lucide-react";
import { useFollowed } from "@/hooks/useFollowed";
import type { MarketplaceFreshness, FreshnessStatus } from "@/lib/types";

function groupByMarketplace(listings: any[]): Record<string, any[]> {
  return listings.reduce((acc, l) => {
    (acc[l.marketplace_slug] ??= []).push(l);
    return acc;
  }, {} as Record<string, any[]>);
}

const MP_LABEL: Record<string, string> = {
  stubhub: "StubHub",
  seatgeek: "SeatGeek",
  ticketmaster: "Ticketmaster",
  tickpick: "TickPick",
  gametime: "GameTime",
  vividseats: "Vivid Seats",
};

const MP_COLOR: Record<string, string> = {
  stubhub:      "bg-blue-500/10  text-blue-400  border-blue-500/30",
  seatgeek:     "bg-green-500/10 text-green-400 border-green-500/30",
  ticketmaster: "bg-sky-500/10   text-sky-400   border-sky-500/30",
  tickpick:     "bg-orange-500/10 text-orange-400 border-orange-500/30",
  gametime:     "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  vividseats:   "bg-red-500/10   text-red-400   border-red-500/30",
};

const FRESHNESS_BADGE: Record<FreshnessStatus, { label: string; className: string }> = {
  fresh:  { label: "LIVE",  className: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" },
  late:   { label: "LATE",  className: "bg-yellow-500/15  text-yellow-400  border border-yellow-500/30"  },
  stale:  { label: "STALE", className: "bg-orange-500/15  text-orange-400  border border-orange-500/30"  },
  dead:   { label: "DEAD",  className: "bg-red-500/15     text-red-400     border border-red-500/30"     },
};

function FreshnessBadge({ freshness }: { freshness: MarketplaceFreshness | undefined }) {
  if (!freshness) return null;
  const { label, className } = FRESHNESS_BADGE[freshness.freshness_status] ?? FRESHNESS_BADGE.stale;
  const title = freshness.age_minutes != null
    ? `Last collected ${Math.round(freshness.age_minutes / 60)}h ago${freshness.stale_reason ? ` · ${freshness.stale_reason}` : ""}`
    : freshness.stale_reason ?? "";
  return (
    <span
      className={`ml-2 text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${className}`}
      title={title}
    >
      {label}
    </span>
  );
}

function StaleWarning({ freshness, mp }: { freshness: MarketplaceFreshness; mp: string }) {
  const ageH = freshness.age_minutes != null ? Math.round(freshness.age_minutes / 60) : null;
  const lastSeen = freshness.last_success_at
    ? new Date(freshness.last_success_at).toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
    : "never";
  return (
    <div className="px-4 py-2 text-xs text-orange-400/80 bg-orange-500/5 border-t border-orange-500/20 flex items-center gap-1.5">
      <AlertTriangle size={11} className="shrink-0" />
      <span>
        Stale data — last collected {ageH != null ? `${ageH}h ago` : "unknown"} ({lastSeen}).
        Prices may not reflect the current market.
      </span>
    </div>
  );
}

function ListingTable({ listings }: { listings: any[] }) {
  if (listings.length === 0) return null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-slate-500 border-b border-[#2a3145]">
            <th className="pb-2 pr-4 font-medium">Section</th>
            <th className="pb-2 pr-4 font-medium">Row</th>
            <th className="pb-2 pr-4 font-medium text-right">Price</th>
            <th className="pb-2 font-medium text-right">Qty</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1e2535]">
          {listings.slice(0, 30).map((l) => (
            <tr key={l.id} className="hover:bg-[#1a2030]">
              <td className="py-2 pr-4 text-slate-200">{l.section_name}</td>
              <td className="py-2 pr-4 text-slate-400">{l.row || "—"}</td>
              <td className="py-2 pr-4 text-right font-mono text-green-400">{fmt$(l.price_each)}</td>
              <td className="py-2 text-right text-slate-400">{l.quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {listings.length > 30 && (
        <p className="text-xs text-slate-600 mt-2 text-center">+{listings.length - 30} more listings</p>
      )}
    </div>
  );
}

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = Number(params.id);

  const [event, setEvent] = useState<any>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);
  const { followed, toggle } = useFollowed();

  const isFollowed = followed.has(eventId);

  useEffect(() => {
    Promise.all([api.events.get(eventId), api.listings.byEvent(eventId)])
      .then(([ev, ls]) => { setEvent(ev); setListings(ls); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [eventId]);

  async function handlePoll() {
    setPolling(true);
    try {
      await api.poll.trigger(eventId);
      await new Promise((r) => setTimeout(r, 3000));
      const [ev, ls] = await Promise.all([api.events.get(eventId), api.listings.byEvent(eventId)]);
      setEvent(ev); setListings(ls);
    } catch (e) { console.error(e); }
    finally { setPolling(false); }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (!event) {
    return (
      <div className="text-center py-16">
        <p className="text-slate-400 mb-4">Event not found.</p>
        <button onClick={() => router.back()} className="text-blue-400 hover:text-blue-300 text-sm">← Go back</button>
      </div>
    );
  }

  const grouped = groupByMarketplace(listings);
  const marketplaces = Object.keys(grouped).sort();
  // Use the backend-computed fresh price floor (stale marketplaces excluded)
  // Fall back to historical price only if no fresh data exists (for context)
  const lowestOverall = event.lowest_price ?? null;
  const historicalFloor = event.historical_lowest_price ?? null;
  const freshness = event.marketplace_freshness ?? {};

  return (
    <div className="max-w-4xl mx-auto space-y-8">

      {/* ── Header ─────────────────────────────────────────── */}
      <div>
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-300 mb-4 transition-colors"
        >
          <ChevronLeft size={16} /> Back
        </button>

        <div className="bg-[#161b27] border border-[#2a3145] rounded-2xl p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl font-bold text-white leading-tight">{event.title}</h1>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 mt-2 text-sm text-slate-400">
                <span className="flex items-center gap-1.5">
                  <MapPin size={14} className="shrink-0" />
                  {event.venue_name || event.venue_slug}
                </span>
                <span className="flex items-center gap-1.5">
                  <CalendarDays size={14} className="shrink-0" />
                  {fmtDate(event.event_date)}
                </span>
              </div>
              {lowestOverall != null ? (
                <p className="mt-3 text-slate-400 text-sm">
                  From <span className="text-white font-bold text-xl">{fmt$(lowestOverall)}</span>
                  <span className="ml-2 text-[10px] text-emerald-500/70 uppercase tracking-wide">live</span>
                </p>
              ) : historicalFloor != null ? (
                <p className="mt-3 text-slate-400 text-sm">
                  <span className="text-orange-400/70 text-xs uppercase tracking-wide mr-1">stale</span>
                  <span className="text-slate-500 line-through">{fmt$(historicalFloor)}</span>
                  <span className="ml-2 text-xs text-slate-600">· no fresh data</span>
                </p>
              ) : null}
            </div>

            <div className="flex flex-col items-end gap-2 shrink-0">
              <button
                onClick={() => toggle(eventId)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                  isFollowed
                    ? "border-blue-500 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20"
                    : "border-[#2a3145] text-slate-400 hover:border-slate-400 hover:text-white"
                }`}
              >
                <Star size={15} fill={isFollowed ? "currentColor" : "none"} />
                {isFollowed ? "Following" : "Follow"}
              </button>
              <button
                onClick={handlePoll}
                disabled={polling}
                className="flex items-center gap-2 px-4 py-2 bg-[#1e2535] hover:bg-[#252d3d] border border-[#2a3145] rounded-lg text-sm text-slate-300 disabled:opacity-50 transition-colors"
              >
                <RefreshCw size={14} className={polling ? "animate-spin" : ""} />
                {polling ? "Polling…" : "Refresh"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Listings ───────────────────────────────────────── */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Ticket size={16} className="text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Tickets</h2>
          <span className="text-xs text-slate-600">({listings.length} listings)</span>
        </div>

        {listings.length === 0 ? (
          <div className="bg-[#161b27] border border-[#2a3145] rounded-xl p-8 text-center text-slate-500">
            <p>No listings available.</p>
            <button onClick={handlePoll} className="text-blue-400 hover:text-blue-300 text-sm mt-2">
              Try polling now →
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {marketplaces.map((mp) => {
              const mpFreshness = freshness[mp] as MarketplaceFreshness | undefined;
              const isStale = mpFreshness && !["fresh", "late"].includes(mpFreshness.freshness_status);
              return (
                <div key={mp} className={`border rounded-xl overflow-hidden ${MP_COLOR[mp] ?? "border-[#2a3145]"}`}>
                  <div className={`px-4 py-3 border-b flex items-center justify-between ${MP_COLOR[mp] ?? "border-[#2a3145]"}`}>
                    <span className="text-sm font-semibold flex items-center">
                      {MP_LABEL[mp] ?? mp}
                      <FreshnessBadge freshness={mpFreshness} />
                    </span>
                    <span className="text-xs opacity-70">
                      {grouped[mp].length} listings · from {fmt$(grouped[mp][0]?.price_each)}
                    </span>
                  </div>
                  {isStale && mpFreshness && (
                    <StaleWarning freshness={mpFreshness} mp={mp} />
                  )}
                  <div className="bg-[#161b27] px-4 py-3">
                    <ListingTable listings={grouped[mp]} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Highlights placeholder ─────────────────────────── */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Star size={16} className="text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Highlights</h2>
        </div>
        <div className="bg-[#161b27] border border-[#2a3145] rounded-xl p-8 text-center text-slate-600">
          <p className="text-sm">Price drops, deal alerts, and trends will appear here.</p>
          <p className="text-xs mt-1 text-slate-700">Coming soon</p>
        </div>
      </section>

      {/* ── Venue Map placeholder ──────────────────────────── */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Map size={16} className="text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Venue Map</h2>
        </div>
        <div className="bg-[#161b27] border border-[#2a3145] border-dashed rounded-xl p-12 text-center text-slate-600">
          <Map size={32} className="mx-auto mb-3 opacity-20" />
          <p className="text-sm">Interactive seat map coming soon.</p>
        </div>
      </section>

    </div>
  );
}
