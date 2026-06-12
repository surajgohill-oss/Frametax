"use client";

import { useState, useEffect, useCallback } from "react";
import {
  RefreshCw,
  AlertCircle,
  Star,
  BarChart2,
  TrendingDown,
  Zap,
  Map,
  ChevronLeft,
} from "lucide-react";
import { api } from "@/lib/api";
import type { VenueIntelligenceResponse, VenueClassificationsResponse } from "@/lib/types";
import { cn } from "@/lib/utils";
import SofiVenueMap, { type VenueMode } from "./SofiVenueMap";
import GenericVenueMap from "./GenericVenueMap";
import SectionDetailDrawer from "./SectionDetailDrawer";
import SectionOpportunityBoard from "./SectionOpportunityBoard";

// ── Mode selector ─────────────────────────────────────────────────────────────
const MODES: { id: VenueMode; label: string; icon: React.ElementType; color: string }[] = [
  { id: "opportunity", label: "Value",    icon: Star,         color: "#10b981" },
  { id: "demand",      label: "Demand",   icon: BarChart2,    color: "#ef4444" },
  { id: "inventory",   label: "Supply",   icon: Zap,          color: "#3b82f6" },
  { id: "price_trend", label: "Trend",    icon: TrendingDown, color: "#f59e0b" },
];

function ModeLegend({ mode }: { mode: VenueMode }) {
  const cfg = {
    opportunity: [
      { label: "No data", color: "#1a2333" },
      { label: "Low value", color: "#1e3a5f" },
      { label: "High value", color: "#10b981" },
    ],
    demand: [
      { label: "No data", color: "#1a2333" },
      { label: "Low demand", color: "#1a1a2e" },
      { label: "High demand", color: "#ef4444" },
    ],
    inventory: [
      { label: "No listings", color: "#0f172a" },
      { label: "Few", color: "#1e40af" },
      { label: "Many", color: "#3b82f6" },
    ],
    price_trend: [
      { label: "↓ Dropping", color: "#059669" },
      { label: "Flat", color: "#475569" },
      { label: "↑ Rising", color: "#ef4444" },
    ],
  }[mode];

  return (
    <div className="flex items-center gap-3">
      {cfg.map(({ label, color }) => (
        <div key={label} className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm flex-shrink-0" style={{ backgroundColor: color }} />
          <span className="text-[9px] text-slate-600">{label}</span>
        </div>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
interface Props {
  eventId: number;
  venueSlug?: string | null;
  venueName?: string;
}

export default function VenueIntelligence({ eventId, venueSlug, venueName }: Props) {
  const isSoFi = venueSlug === "sofi-stadium";
  const slug = venueSlug ?? "sofi-stadium";

  const [intelligence, setIntelligence] = useState<VenueIntelligenceResponse | null>(null);
  const [classifications, setClassifications] = useState<VenueClassificationsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [mode, setMode] = useState<VenueMode>("opportunity");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [intel, cls] = await Promise.allSettled([
        api.venues.intelligence(slug, eventId),
        api.venues.classifications(slug, eventId),
      ]);
      if (intel.status === "fulfilled") setIntelligence(intel.value);
      if (cls.status === "fulfilled") setClassifications(cls.value);
      if (intel.status === "rejected") setError(String(intel.reason));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [eventId, slug]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      if (!isSoFi && intelligence && intelligence.sections_total === 0) {
        // Seed sections from listing data first, then compute
        await api.venues.seedFromListings(slug, eventId);
      }
      await api.venues.compute(slug, eventId);
      await loadData();
    } catch {
      await loadData();
    } finally {
      setRefreshing(false);
    }
  };

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <RefreshCw size={18} className="animate-spin text-slate-500" />
      </div>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────────
  if (error && !intelligence) {
    return (
      <div className="flex flex-col items-center gap-3 py-12 text-center">
        <div className="flex items-center gap-2 text-red-400 text-sm">
          <AlertCircle size={14} />
          <span>Failed to load venue intelligence</span>
        </div>
        <button
          onClick={loadData}
          className="text-xs text-slate-500 hover:text-slate-300 underline underline-offset-2"
        >
          Try again
        </button>
      </div>
    );
  }

  // ── No data ──────────────────────────────────────────────────────────────
  if (!intelligence) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Map size={28} className="text-slate-700 mb-3" />
        <p className="text-sm font-medium text-slate-400 mb-1">
          {venueName ?? "Venue"} Intelligence
        </p>
        <p className="text-xs text-slate-600 max-w-xs">
          Section data is being prepared for this venue.
        </p>
      </div>
    );
  }

  const selectedSection = selectedId
    ? intelligence.sections.find((s) => s.section_id === selectedId) ?? null
    : null;

  const sectionsWithMetrics = intelligence.sections_with_metrics;
  const venueDisplayName = isSoFi ? "SoFi Stadium" : (venueName ?? slug);

  return (
    <div className="space-y-4">
      {/* Header row */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            {venueDisplayName} Intelligence
          </h3>
          {sectionsWithMetrics > 0 ? (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-500 border border-emerald-500/20">
              {sectionsWithMetrics} sections live
            </span>
          ) : (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-slate-500 border border-white/8">
              {intelligence.sections_total} sections · awaiting data
            </span>
          )}
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 text-[10px] text-slate-500 hover:text-slate-300 transition-colors disabled:opacity-40"
        >
          <RefreshCw size={10} className={refreshing ? "animate-spin" : ""} />
          {refreshing ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {/* Mode selector */}
      <div className="flex gap-1">
        {MODES.map(({ id, label, icon: Icon, color }) => (
          <button
            key={id}
            onClick={() => setMode(id)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all border",
              mode === id
                ? "border-white/15 bg-white/8 text-slate-100"
                : "border-white/6 bg-white/2 text-slate-500 hover:text-slate-300 hover:bg-white/5",
            )}
          >
            <Icon size={10} style={{ color: mode === id ? color : undefined }} />
            {label}
          </button>
        ))}
      </div>

      {/* Map + right panel */}
      <div className="flex gap-4 items-start">
        {/* Map */}
        <div className="flex-shrink-0 w-full md:w-[55%]">
          {isSoFi && sectionsWithMetrics === 0 ? (
            <div className="rounded-xl border border-white/8 bg-[#0c1421] flex flex-col items-center justify-center py-16 text-center">
              <Map size={24} className="text-slate-700 mb-3" />
              <p className="text-xs text-slate-500">No section metrics available.</p>
              <p className="text-[10px] text-slate-700 mt-1">
                Data computes when tickets are listed.
              </p>
              <button
                onClick={handleRefresh}
                className="mt-4 text-[10px] text-slate-500 hover:text-slate-300 underline underline-offset-2"
              >
                Compute now
              </button>
            </div>
          ) : isSoFi ? (
            <SofiVenueMap
              sections={intelligence.sections}
              mode={mode}
              selectedId={selectedId}
              onSelectSection={(id) =>
                setSelectedId((prev) => (prev === id ? null : id))
              }
            />
          ) : (
            <GenericVenueMap
              sections={intelligence.sections}
              mode={mode}
              selectedId={selectedId}
              onSelectSection={(id) =>
                setSelectedId((prev) => (prev === id ? null : id))
              }
              venueName={venueName}
            />
          )}
          {/* Legend */}
          <div className="mt-2 pl-1">
            <ModeLegend mode={mode} />
          </div>
        </div>

        {/* Right panel — section detail OR opportunity board */}
        <div className="hidden md:flex flex-1 flex-col min-h-[340px] max-h-[400px] rounded-xl border border-white/8 bg-[#111827] p-3">
          {selectedSection ? (
            <SectionDetailDrawer
              section={selectedSection}
              mode={mode}
              onClose={() => setSelectedId(null)}
            />
          ) : classifications ? (
            <SectionOpportunityBoard
              data={classifications}
              onSelectSection={(id) => setSelectedId(id)}
              selectedId={selectedId}
            />
          ) : null}
        </div>
      </div>

      {/* Mobile: section detail below map */}
      {selectedSection && (
        <div className="md:hidden rounded-xl border border-white/8 bg-[#111827] p-4">
          <button
            onClick={() => setSelectedId(null)}
            className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-300 mb-3"
          >
            <ChevronLeft size={11} />
            Back to map
          </button>
          <SectionDetailDrawer
            section={selectedSection}
            mode={mode}
            onClose={() => setSelectedId(null)}
          />
        </div>
      )}

      {/* Mobile: opportunity board */}
      {!selectedSection && classifications && (
        <div className="md:hidden rounded-xl border border-white/8 bg-[#111827] p-3">
          <SectionOpportunityBoard
            data={classifications}
            onSelectSection={(id) => setSelectedId(id)}
            selectedId={selectedId}
          />
        </div>
      )}

      {/* Coverage note */}
      <p className="text-[10px] text-slate-700 text-center">
        {intelligence.sections_total} sections · {isSoFi ? "Tap" : "Click"} a section for detail
      </p>
    </div>
  );
}
