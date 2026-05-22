"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { fmtDate, fmtRelative, fmt$ } from "@/lib/utils";
import { RefreshCw, Plus, Trash2, ExternalLink } from "lucide-react";
import { deriveEventState } from "@/lib/types";
import type { Event, EventState } from "@/lib/types";

const STATE_BORDER: Record<EventState, string> = {
  POPULATED: "border-l-4 border-l-emerald-500",
  PARTIAL:   "border-l-4 border-l-yellow-500",
  EMPTY:     "border-l-4 border-l-slate-600",
  BLOCKED:   "border-l-4 border-l-red-500",
};

const STATE_BADGE: Record<EventState, { label: string; variant: "green" | "yellow" | "secondary" | "red" }> = {
  POPULATED: { label: "LIVE",        variant: "green" },
  PARTIAL:   { label: "LIMITED",     variant: "yellow" },
  EMPTY:     { label: "NO DATA",     variant: "secondary" },
  BLOCKED:   { label: "UNAVAILABLE", variant: "red" },
};

const STATE_PRICE_COLOR: Record<EventState, string> = {
  POPULATED: "text-white",
  PARTIAL:   "text-yellow-400",
  EMPTY:     "text-slate-500",
  BLOCKED:   "text-slate-500",
};

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState<Record<string, boolean>>({});

  const load = () => api.events.list().then(setEvents).catch(console.error).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  async function handlePoll(id: number) {
    setPolling((p) => ({ ...p, [id]: true }));
    try { await api.poll.trigger(id); setTimeout(load, 3000); }
    catch (e) { console.error(e); }
    finally { setPolling((p) => ({ ...p, [id]: false })); }
  }

  async function handleDelete(id: number) {
    if (!confirm("Remove this event from the watchlist?")) return;
    await api.events.delete(id); load();
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-500">Loading…</div>;
  if (!Array.isArray(events)) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-white">Events</h1><p className="text-slate-400 text-sm mt-1">{events.length} / 30 slots used</p></div>
        <Link href="/events/new" className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"><Plus className="w-4 h-4" /> Add Event</Link>
      </div>
      {events.length === 0 ? (
        <Card className="p-12 text-center"><p className="text-slate-500">No events yet.</p><Link href="/events/new" className="text-blue-400 hover:text-blue-300 text-sm mt-2 inline-block">Add your first event →</Link></Card>
      ) : (
        <div className="space-y-2">
          {events.map((ev) => {
            const state = deriveEventState(ev);
            const { label: badgeLabel, variant: badgeVariant } = STATE_BADGE[state];
            const priceColor = STATE_PRICE_COLOR[state];
            const lowestPrice = ev.lowest_price ?? Math.min(ev.lowest_ask_stubhub ?? Infinity, ev.lowest_ask_seatgeek ?? Infinity);
            const hasPrice = isFinite(lowestPrice);
            return (
              <Card key={ev.id} className={`p-4 ${STATE_BORDER[state]}`}>
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Link href={`/events/${ev.id}`} className="font-medium text-white hover:text-blue-300 transition-colors">{ev.title}</Link>
                      <Badge variant={badgeVariant} className="text-[10px] px-1.5 py-0">{badgeLabel}</Badge>
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">{ev.venue_slug?.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase())} · {fmtDate(ev.event_date)}</div>
                    <div className="flex items-center gap-3 mt-2">
                      {hasPrice
                        ? (
                          <>
                            <span className="text-xs">
                              <span className="text-slate-500">Floor </span>
                              <span className={`font-mono font-semibold ${priceColor}`}>{fmt$(lowestPrice)}</span>
                            </span>
                            {ev.lowest_ask_stubhub != null && (
                              <span className="text-xs"><span className="text-slate-500">SH </span><span className={`font-mono ${priceColor}`}>{fmt$(ev.lowest_ask_stubhub)}</span></span>
                            )}
                            {ev.lowest_ask_seatgeek != null && (
                              <span className="text-xs"><span className="text-slate-500">SG </span><span className={`font-mono ${priceColor}`}>{fmt$(ev.lowest_ask_seatgeek)}</span></span>
                            )}
                          </>
                        )
                        : <span className="text-xs text-slate-500 italic">No listings</span>
                      }
                      {ev.next_poll_at && <span className="text-xs text-slate-500">Next poll {fmtRelative(ev.next_poll_at)}</span>}
                      {ev.total_listings != null && ev.total_listings > 0 && (
                        <span className="text-xs text-slate-500">{ev.total_listings} listings</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button onClick={() => handlePoll(ev.id)} disabled={polling[ev.id]} className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#2a3145] transition-colors disabled:opacity-50"><RefreshCw className={`w-4 h-4 ${polling[ev.id] ? "animate-spin" : ""}`} /></button>
                    {ev.stubhub_url && <a href={ev.stubhub_url} target="_blank" rel="noreferrer" className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#2a3145] transition-colors"><ExternalLink className="w-4 h-4" /></a>}
                    <button onClick={() => handleDelete(ev.id)} className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-[#2a3145] transition-colors"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
