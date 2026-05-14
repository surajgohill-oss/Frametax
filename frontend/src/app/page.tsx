"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { fmtDate, fmtRelative, fmt$ } from "@/lib/utils";
import { Activity, TrendingDown, Clock, ListMusic, AlertCircle } from "lucide-react";

export default function DashboardPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.events.list(), api.analytics.summary()])
      .then(([evts, sum]) => { setEvents(evts); setSummary(sum); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const activeEvents = events.filter((e) => e.is_active);
  const dueEvents = events.filter((e) => e.next_poll_at && new Date(e.next_poll_at) <= new Date());

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-500">Loading dashboard…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 text-sm mt-1">LA concert ticket price intelligence</p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4"><div className="flex items-center gap-3"><div className="p-2 rounded-lg bg-blue-500/10"><ListMusic className="w-5 h-5 text-blue-400" /></div><div><div className="text-2xl font-bold text-white">{activeEvents.length}</div><div className="text-xs text-slate-400">Tracked Events</div></div></div></Card>
        <Card className="p-4"><div className="flex items-center gap-3"><div className="p-2 rounded-lg bg-amber-500/10"><Clock className="w-5 h-5 text-amber-400" /></div><div><div className="text-2xl font-bold text-white">{dueEvents.length}</div><div className="text-xs text-slate-400">Due for Poll</div></div></div></Card>
        <Card className="p-4"><div className="flex items-center gap-3"><div className="p-2 rounded-lg bg-green-500/10"><TrendingDown className="w-5 h-5 text-green-400" /></div><div><div className="text-2xl font-bold text-white">{summary?.avg_lowest_ask != null ? fmt$(summary.avg_lowest_ask) : "—"}</div><div className="text-xs text-slate-400">Avg Lowest Ask</div></div></div></Card>
        <Card className="p-4"><div className="flex items-center gap-3"><div className="p-2 rounded-lg bg-purple-500/10"><Activity className="w-5 h-5 text-purple-400" /></div><div><div className="text-2xl font-bold text-white">{summary?.total_listings ?? "—"}</div><div className="text-xs text-slate-400">Total Listings</div></div></div></Card>
      </div>
      <Card>
        <div className="p-4 border-b border-[#2a3145] flex items-center justify-between">
          <h2 className="font-semibold text-white">Watchlist</h2>
          <Link href="/events/new" className="text-xs text-blue-400 hover:text-blue-300">+ Add Event</Link>
        </div>
        {activeEvents.length === 0 ? (
          <div className="p-8 text-center text-slate-500"><ListMusic className="w-8 h-8 mx-auto mb-2 opacity-30" /><p>No events tracked yet.</p><Link href="/events/new" className="text-blue-400 hover:text-blue-300 text-sm mt-1 inline-block">Add your first event →</Link></div>
        ) : (
          <div className="divide-y divide-[#2a3145]">
            {activeEvents.slice(0, 10).map((ev) => (
              <Link key={ev.id} href={`/events/${ev.id}`} className="flex items-center gap-4 px-4 py-3 hover:bg-[#1e2535] transition-colors">
                <div className="flex-1 min-w-0"><div className="font-medium text-white text-sm truncate">{ev.title}</div><div className="text-xs text-slate-400">{ev.venue_slug?.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase())} · {fmtDate(ev.event_date)}</div></div>
                <div className="flex items-center gap-2 shrink-0">
                  {ev.lowest_ask_stubhub != null && <Badge variant="default" className="text-xs">SH {fmt$(ev.lowest_ask_stubhub)}</Badge>}
                  {ev.lowest_ask_seatgeek != null && <Badge variant="secondary" className="text-xs">SG {fmt$(ev.lowest_ask_seatgeek)}</Badge>}
                  {ev.next_poll_at && <span className="text-xs text-slate-500">{fmtRelative(ev.next_poll_at)}</span>}
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>
      {summary?.recent_errors > 0 && (
        <Card className="border-amber-500/30"><div className="p-4 flex items-center gap-3"><AlertCircle className="w-5 h-5 text-amber-400 shrink-0" /><span className="text-sm text-amber-300 flex-1">{summary.recent_errors} scraper error{summary.recent_errors !== 1 ? "s" : ""} in the last 24h</span><Link href="/debug" className="text-xs text-amber-400 hover:text-amber-300">View Debug →</Link></div></Card>
      )}
    </div>
  );
}
