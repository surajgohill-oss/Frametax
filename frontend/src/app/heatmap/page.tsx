"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { VenueHeatmap } from "@/components/venue/VenueHeatmap";
import { fmt$ } from "@/lib/utils";

const VENUES = [
  { value: "hollywood_bowl", label: "Hollywood Bowl" },
  { value: "kia_forum", label: "Kia Forum" },
  { value: "crypto_arena", label: "Crypto.com Arena" },
  { value: "greek_theatre", label: "Greek Theatre" },
  { value: "sofi_stadium", label: "SoFi Stadium" },
];

export default function HeatmapPage() {
  const [venueSlug, setVenueSlug] = useState("hollywood_bowl");
  const [eventId, setEventId] = useState<number | null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [listings, setListings] = useState<any[]>([]);
  const [marketplace, setMarketplace] = useState<"all" | "stubhub" | "seatgeek">("all");
  const [colorMode, setColorMode] = useState<"price" | "inventory">("price");
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [loadingSections, setLoadingSections] = useState(false);

  useEffect(() => {
    api.events.list().then((evts) => {
      setEvents(evts);
      const first = evts.find((e: any) => e.venue_slug === venueSlug);
      if (first) setEventId(first.id);
    });
  }, []);

  useEffect(() => {
    setLoadingSections(true);
    api.venues.sections(venueSlug)
      .then(setSections)
      .catch(console.error)
      .finally(() => setLoadingSections(false));
  }, [venueSlug]);

  useEffect(() => {
    if (!eventId) { setListings([]); return; }
    api.listings.byEvent(eventId).then(setListings).catch(console.error);
  }, [eventId]);

  const venueEvents = events.filter((e) => e.venue_slug === venueSlug);

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

  const selectedPrices = selectedSection
    ? sectionPrices.find((s) => s.section_id === selectedSection)
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Venue Heatmap</h1>
        <p className="text-slate-400 text-sm mt-1">Section-level pricing visualization</p>
      </div>

      {/* Controls */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Venue</label>
            <select
              value={venueSlug}
              onChange={(e) => {
                setVenueSlug(e.target.value);
                setEventId(null);
                setSelectedSection(null);
              }}
              className="px-3 py-1.5 bg-[#0d1117] border border-[#2a3145] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
            >
              {VENUES.map((v) => (
                <option key={v.value} value={v.value}>{v.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Event</label>
            <select
              value={eventId ?? ""}
              onChange={(e) => setEventId(e.target.value ? Number(e.target.value) : null)}
              className="px-3 py-1.5 bg-[#0d1117] border border-[#2a3145] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="">— no event —</option>
              {venueEvents.map((e) => (
                <option key={e.id} value={e.id}>{e.title}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Marketplace</label>
            <div className="flex gap-1">
              {(["all", "stubhub", "seatgeek"] as const).map((mp) => (
                <button
                  key={mp}
                  onClick={() => setMarketplace(mp)}
                  className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                    marketplace === mp
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "border-[#2a3145] text-slate-400 hover:text-white"
                  }`}
                >
                  {mp === "all" ? "All" : mp === "stubhub" ? "StubHub" : "SeatGeek"}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Color</label>
            <div className="flex gap-1">
              {(["price", "inventory"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setColorMode(mode)}
                  className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
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
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2">
          <Card className="p-4">
            {loadingSections ? (
              <div className="h-80 flex items-center justify-center text-slate-500">Loading sections…</div>
            ) : (
              <VenueHeatmap
                sections={sections}
                prices={sectionPrices}
                colorMode={colorMode}
                selectedSection={selectedSection}
                onSectionClick={(sid) => setSelectedSection(sid === selectedSection ? null : sid)}
              />
            )}
          </Card>
        </div>

        {/* Section Detail */}
        <div className="space-y-4">
          {selectedPrices ? (
            <Card className="p-4">
              <div className="font-semibold text-white mb-3">{selectedPrices.display_name}</div>
              <div className="space-y-2 text-sm">
                {selectedPrices.lowest_ask != null && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Lowest Ask</span>
                    <span className="text-white font-mono">{fmt$(selectedPrices.lowest_ask)}</span>
                  </div>
                )}
                {selectedPrices.listing_count != null && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Listings</span>
                    <span className="text-white">{selectedPrices.listing_count}</span>
                  </div>
                )}
              </div>
              <button
                onClick={() => setSelectedSection(null)}
                className="mt-3 text-xs text-slate-500 hover:text-slate-300"
              >
                Deselect
              </button>
            </Card>
          ) : (
            <Card className="p-4 text-slate-500 text-sm">
              Click a section on the map to see details.
            </Card>
          )}

          {/* Top sections table */}
          <Card>
            <div className="p-3 border-b border-[#2a3145] text-xs font-medium text-slate-300">
              Cheapest Sections
            </div>
            <div className="divide-y divide-[#2a3145]">
              {sectionPrices
                .filter((s) => s.lowest_ask != null)
                .sort((a, b) => (a.lowest_ask ?? 0) - (b.lowest_ask ?? 0))
                .slice(0, 8)
                .map((s) => (
                  <button
                    key={s.section_id}
                    onClick={() => setSelectedSection(s.section_id === selectedSection ? null : s.section_id)}
                    className={`w-full flex justify-between items-center px-3 py-2 text-xs hover:bg-[#1e2535] transition-colors ${
                      selectedSection === s.section_id ? "bg-[#1e2535]" : ""
                    }`}
                  >
                    <span className="text-slate-300 truncate">{s.display_name}</span>
                    <span className="text-white font-mono ml-2">{fmt$(s.lowest_ask!)}</span>
                  </button>
                ))}
              {sectionPrices.filter((s) => s.lowest_ask != null).length === 0 && (
                <div className="p-4 text-slate-500 text-xs text-center">No pricing data</div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
