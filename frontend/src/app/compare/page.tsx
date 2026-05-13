"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { fmt$ } from "@/lib/utils";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";

export default function ComparePage() {
  const [events, setEvents] = useState<any[]>([]);
  const [eventId, setEventId] = useState<number | null>(null);
  const [comparison, setComparison] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.events.list().then((evts) => {
      setEvents(evts.filter((e: any) => e.is_active));
      if (evts.length > 0) setEventId(evts[0].id);
    });
  }, []);

  useEffect(() => {
    if (!eventId) { setComparison([]); return; }
    setLoading(true);
    api.analytics.compare(eventId)
      .then(setComparison)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [eventId]);

  const selectedEvent = events.find((e) => e.id === eventId);
  const stubhub = comparison.filter((r) => r.marketplace === "stubhub");
  const seatgeek = comparison.filter((r) => r.marketplace === "seatgeek");

  const allSectionIds = Array.from(
    new Set([...stubhub, ...seatgeek].map((r) => r.section_id))
  );

  const stubhubMap = Object.fromEntries(stubhub.map((r) => [r.section_id, r]));
  const seatgeekMap = Object.fromEntries(seatgeek.map((r) => [r.section_id, r]));

  function priceDiff(sh?: number, sg?: number) {
    if (sh == null || sg == null) return null;
    return ((sh - sg) / sg) * 100;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Marketplace Compare</h1>
        <p className="text-slate-400 text-sm mt-1">StubHub vs SeatGeek section-by-section pricing</p>
      </div>

      <Card className="p-4">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Event</label>
          <select
            value={eventId ?? ""}
            onChange={(e) => setEventId(Number(e.target.value))}
            className="px-3 py-1.5 bg-[#0d1117] border border-[#2a3145] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
          >
            {events.map((e) => (
              <option key={e.id} value={e.id}>{e.title}</option>
            ))}
          </select>
        </div>
      </Card>

      {selectedEvent && (
        <div className="grid grid-cols-3 gap-4">
          <Card className="p-4 text-center">
            <div className="text-xs text-slate-400 mb-1">StubHub Lowest</div>
            <div className="text-2xl font-bold font-mono text-white">
              {selectedEvent.lowest_ask_stubhub != null ? fmt$(selectedEvent.lowest_ask_stubhub) : "—"}
            </div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-xs text-slate-400 mb-1">SeatGeek Lowest</div>
            <div className="text-2xl font-bold font-mono text-white">
              {selectedEvent.lowest_ask_seatgeek != null ? fmt$(selectedEvent.lowest_ask_seatgeek) : "—"}
            </div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-xs text-slate-400 mb-1">Price Difference</div>
            <div className="text-2xl font-bold font-mono text-white">
              {selectedEvent.lowest_ask_stubhub != null && selectedEvent.lowest_ask_seatgeek != null ? (
                <span className={
                  selectedEvent.lowest_ask_stubhub > selectedEvent.lowest_ask_seatgeek
                    ? "text-red-400" : "text-green-400"
                }>
                  {priceDiff(selectedEvent.lowest_ask_stubhub, selectedEvent.lowest_ask_seatgeek)?.toFixed(1)}%
                </span>
              ) : "—"}
            </div>
          </Card>
        </div>
      )}

      <Card>
        <div className="p-4 border-b border-[#2a3145]">
          <h2 className="font-semibold text-white">Section-by-Section Comparison</h2>
        </div>
        {loading ? (
          <div className="p-8 text-center text-slate-500">Loading…</div>
        ) : allSectionIds.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            No comparison data available. Poll this event first.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#2a3145]">
                  <th className="text-left px-4 py-3 text-slate-400 font-medium">Section</th>
                  <th className="text-right px-4 py-3 text-slate-400 font-medium">StubHub</th>
                  <th className="text-right px-4 py-3 text-slate-400 font-medium">SeatGeek</th>
                  <th className="text-right px-4 py-3 text-slate-400 font-medium">Diff</th>
                  <th className="text-right px-4 py-3 text-slate-400 font-medium">Better</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2a3145]">
                {allSectionIds.map((sid) => {
                  const sh = stubhubMap[sid];
                  const sg = seatgeekMap[sid];
                  const diff = priceDiff(sh?.lowest_ask, sg?.lowest_ask);
                  const shCheaper = diff != null && diff < 0;
                  const sgCheaper = diff != null && diff > 0;
                  return (
                    <tr key={sid} className="hover:bg-[#1e2535] transition-colors">
                      <td className="px-4 py-2.5 text-white">
                        {sh?.display_name ?? sg?.display_name ?? sid}
                      </td>
                      <td className={`px-4 py-2.5 text-right font-mono ${shCheaper ? "text-green-400" : "text-white"}`}>
                        {sh?.lowest_ask != null ? fmt$(sh.lowest_ask) : <span className="text-slate-600">—</span>}
                      </td>
                      <td className={`px-4 py-2.5 text-right font-mono ${sgCheaper ? "text-green-400" : "text-white"}`}>
                        {sg?.lowest_ask != null ? fmt$(sg.lowest_ask) : <span className="text-slate-600">—</span>}
                      </td>
                      <td className={`px-4 py-2.5 text-right font-mono text-xs ${
                        diff == null ? "text-slate-600" : diff < 0 ? "text-green-400" : diff > 0 ? "text-red-400" : "text-slate-400"
                      }`}>
                        {diff == null ? "—" : `${diff > 0 ? "+" : ""}${diff.toFixed(1)}%`}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        {diff == null ? (
                          <span className="text-slate-600 text-xs">—</span>
                        ) : Math.abs(diff) < 0.5 ? (
                          <span className="text-slate-400 text-xs flex justify-end"><Minus className="w-3 h-3" /></span>
                        ) : shCheaper ? (
                          <span className="text-xs text-green-400 flex items-center justify-end gap-1">
                            <TrendingDown className="w-3 h-3" /> SH
                          </span>
                        ) : (
                          <span className="text-xs text-green-400 flex items-center justify-end gap-1">
                            <TrendingDown className="w-3 h-3" /> SG
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
