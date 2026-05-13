"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { VenueHeatmap } from "@/components/venue/VenueHeatmap";
import { PriceHistoryChart } from "@/components/charts/PriceHistoryChart";
import { SectionPriceBar } from "@/components/charts/SectionPriceBar";
import { fmtDate, fmt$, fmtRelative } from "@/lib/utils";
import { RefreshCw, ExternalLink, ArrowLeft } from "lucide-react";

type Tab = "overview" | "sections" | "history";

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [event, setEvent] = useState<any>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [tab, setTab] = useState<Tab>("overview");
  const [marketplace, setMarketplace] = useState<"stubhub" | "seatgeek" | "all">("all");
  const [colorMode, setColorMode] = useState<"price" | "inventory">("price");
  const [polling, setPolling] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      api.events.get(Number(id)),
      api.listings.byEvent(Number(id)),
      api.analytics.priceHistory(Number(id)),
    ])
      .then(([ev, lst, hist]) => {
        setEvent(ev);
        setListings(lst);
        setHistory(hist);
        return api.venues.sections(ev.venue_slug);
      })
      .then(setSections)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  async function handlePoll() {
    setPolling(true);
    try {
      await api.poll.trigger(Number(id));
      setTimeout(() => {
        Promise.all([
          api.events.get(Number(id)),
          api.listings.byEvent(Number(id)),
        ]).then(([ev, lst]) => { setEvent(ev); setListings(lst); });
        setPolling(false);
      }, 4000);
    } catch {
      setPolling(false);
    }
  }

  const filteredListings = listings.filter(
    (l) => marketplace === "all" || l.marketplace === marketplace
  );

  const sectionPrices = sections.map((sec: any) => {
    const matched = filteredListings.filter((l) => l.section_id === sec.section_id);
    const asks = matched.map((l) => l.price ?? l.lowest_ask).filter((v) => v != null);
    return {
      section_id: sec.section_id,
      display_name: sec.display_name,
      lowest_ask: asks.length ? Math.min(...asks) : undefined,
      listing_count: matched.length || undefined,
    };
  });

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-500">Loading…</div>;
  if (!event) return <div className="text-slate-500 p-8">Event not found.</div>;

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "sections", label: "Section Heatmap" },
    { id: "history", label: "Price History" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <button onClick={() => router.back()} className="mt-1 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#1e2535] transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-white truncate">{event.title}</h1>
          <div className="text-slate-400 text-sm mt-1">
            {event.venue_slug?.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase())} · {fmtDate(event.event_date)}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handlePoll}
            disabled={polling}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1e2535] border border-[#2a3145] text-slate-300 text-sm rounded-lg hover:bg-[#2a3145] transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${polling ? "animate-spin" : ""}`} />
            {polling ? "Polling…" : "Poll Now"}
          </button>
          {event.stubhub_url && (
            <a href={event.stubhub_url} target="_blank" rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1e2535] border border-[#2a3145] text-slate-300 text-sm rounded-lg hover:bg-[#2a3145] transition-colors">
              <ExternalLink className="w-3.5 h-3.5" /> StubHub
            </a>
          )}
          {event.seatgeek_url && (
            <a href={event.seatgeek_url} target="_blank" rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1e2535] border border-[#2a3145] text-slate-300 text-sm rounded-lg hover:bg-[#2a3145] transition-colors">
              <ExternalLink className="w-3.5 h-3.5" /> SeatGeek
            </a>
          )}
        </div>
      </div>

      {/* Price Summary Badges */}
      <div className="flex gap-4">
        {event.lowest_ask_stubhub != null && (
          <Card className="px-4 py-3 flex items-center gap-3">
            <div className="text-xs text-slate-400">StubHub Lowest Ask</div>
            <div className="text-xl font-bold text-white font-mono">{fmt$(event.lowest_ask_stubhub)}</div>
          </Card>
        )}
        {event.lowest_ask_seatgeek != null && (
          <Card className="px-4 py-3 flex items-center gap-3">
            <div className="text-xs text-slate-400">SeatGeek Lowest Ask</div>
            <div className="text-xl font-bold text-white font-mono">{fmt$(event.lowest_ask_seatgeek)}</div>
          </Card>
        )}
        {event.next_poll_at && (
          <Card className="px-4 py-3 flex items-center gap-3">
            <div className="text-xs text-slate-400">Next Poll</div>
            <div className="text-sm text-slate-300">{fmtRelative(event.next_poll_at)}</div>
          </Card>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#2a3145]">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm rounded-t-lg transition-colors ${
              tab === t.id
                ? "text-white bg-[#1e2535] border-b-2 border-blue-500"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Marketplace filter */}
      <div className="flex gap-2">
        {(["all", "stubhub", "seatgeek"] as const).map((mp) => (
          <button
            key={mp}
            onClick={() => setMarketplace(mp)}
            className={`px-3 py-1 text-xs rounded-full border transition-colors ${
              marketplace === mp
                ? "bg-blue-600 border-blue-500 text-white"
                : "border-[#2a3145] text-slate-400 hover:text-white"
            }`}
          >
            {mp === "all" ? "All" : mp === "stubhub" ? "StubHub" : "SeatGeek"}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === "overview" && (
        <Card>
          <div className="p-4 border-b border-[#2a3145] flex items-center justify-between">
            <h2 className="font-semibold text-white">Section Prices</h2>
          </div>
          <div className="p-4">
            <SectionPriceBar sections={sectionPrices.filter((s) => s.lowest_ask != null)} />
          </div>
        </Card>
      )}

      {tab === "sections" && (
        <Card>
          <div className="p-4 border-b border-[#2a3145] flex items-center justify-between">
            <h2 className="font-semibold text-white">Venue Heatmap</h2>
            <div className="flex gap-2">
              {(["price", "inventory"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setColorMode(mode)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                    colorMode === mode
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "border-[#2a3145] text-slate-400 hover:text-white"
                  }`}
                >
                  {mode === "price" ? "Price" : "Inventory"}
                </button>
              ))}
            </div>
          </div>
          <div className="p-4">
            <VenueHeatmap
              sections={sections}
              prices={sectionPrices}
              colorMode={colorMode}
            />
          </div>
        </Card>
      )}

      {tab === "history" && (
        <Card>
          <div className="p-4 border-b border-[#2a3145]">
            <h2 className="font-semibold text-white">Price History</h2>
          </div>
          <div className="p-4">
            <PriceHistoryChart data={history} />
          </div>
        </Card>
      )}
    </div>
  );
}
