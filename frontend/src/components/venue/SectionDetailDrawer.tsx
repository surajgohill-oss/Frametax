"use client";

import { X, TrendingDown, TrendingUp, Minus, BarChart2, Package } from "lucide-react";
import type { VenueSection } from "@/lib/types";
import type { VenueMode } from "./SofiVenueMap";
import { cn } from "@/lib/utils";

interface Props {
  section: VenueSection;
  mode: VenueMode;
  onClose: () => void;
}

export default function SectionDetailDrawer({ section, mode, onClose }: Props) {
  const m = section.metrics;
  const f$ = (v: number | null | undefined) =>
    v != null ? `$${Math.round(v).toLocaleString()}` : "—";
  const fn = (v: number | null | undefined) =>
    v != null ? v.toLocaleString() : "—";

  const tierLabel = section.tier?.replace(/_/g, " ") ?? "";
  const levelLabel = section.level?.replace(/_/g, " ") ?? "";
  const zoneLabel = section.zone?.replace(/_/g, " ") ?? "";

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 leading-tight">{section.display_name}</h3>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {tierLabel && (
              <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/6 text-slate-400 border border-white/8">
                {tierLabel}
              </span>
            )}
            {levelLabel && levelLabel !== tierLabel && (
              <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/6 text-slate-500 border border-white/8">
                {levelLabel}
              </span>
            )}
            {zoneLabel && (
              <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/6 text-slate-500 border border-white/8">
                {zoneLabel}
              </span>
            )}
            {section.is_premium && (
              <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/20">
                Premium
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-white/8 text-slate-500 hover:text-slate-300 transition-colors flex-shrink-0 mt-0.5"
        >
          <X size={13} />
        </button>
      </div>

      {!m ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center py-8">
          <Package size={24} className="text-slate-700 mb-3" />
          <p className="text-xs text-slate-500">No active listings for this section</p>
          <p className="text-[10px] text-slate-700 mt-1">Check back when sellers list tickets here.</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-4 min-h-0">

          {/* Price block */}
          <div className="rounded-xl bg-white/4 border border-white/6 p-3">
            <p className="text-[9px] uppercase tracking-wider text-slate-500 mb-2.5">Pricing</p>
            <div className="grid grid-cols-3 gap-2">
              <PriceCell label="Low"    val={f$(m.low_ask)}    accent="text-emerald-400" />
              <PriceCell label="Median" val={f$(m.median_ask)} accent="text-slate-100" bold />
              <PriceCell label="High"   val={f$(m.high_ask)}   accent="text-red-400" />
            </div>
            {(m.p25_ask != null || m.p75_ask != null) && (
              <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between text-[10px]">
                <span className="text-slate-500">P25–P75</span>
                <span className="text-slate-400 tabular-nums">
                  {f$(m.p25_ask)} – {f$(m.p75_ask)}
                </span>
              </div>
            )}
          </div>

          {/* Scores */}
          <div className="space-y-2">
            {m.value_score != null && (
              <ScoreBar
                label="Value Score"
                value={m.value_score}
                color="#10b981"
                active={mode === "opportunity"}
              />
            )}
            {m.demand_score != null && (
              <ScoreBar
                label="Demand Score"
                value={m.demand_score}
                color="#ef4444"
                active={mode === "demand"}
              />
            )}
            {m.deal_score != null && (
              <ScoreBar
                label="Deal Score"
                value={m.deal_score}
                color="#3b82f6"
                active={false}
              />
            )}
          </div>

          {/* Inventory */}
          <div className="rounded-xl bg-white/4 border border-white/6 p-3">
            <p className="text-[9px] uppercase tracking-wider text-slate-500 mb-2">Inventory</p>
            <div className="grid grid-cols-2 gap-2">
              <InfoCell label="Listings" val={fn(m.listing_count)} />
              <InfoCell label="Tickets"  val={fn(m.ticket_count)} />
            </div>
            {m.inventory_delta_24h != null && (
              <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between text-[10px]">
                <span className="text-slate-500">Change 24h</span>
                <span className={cn(
                  "font-medium tabular-nums flex items-center gap-0.5",
                  m.inventory_delta_24h < 0 ? "text-red-400" :
                  m.inventory_delta_24h > 0 ? "text-emerald-400" : "text-slate-500"
                )}>
                  {m.inventory_delta_24h > 0 ? <TrendingUp size={9} /> :
                   m.inventory_delta_24h < 0 ? <TrendingDown size={9} /> :
                   <Minus size={9} />}
                  {m.inventory_delta_24h > 0 ? "+" : ""}{m.inventory_delta_24h}
                </span>
              </div>
            )}
          </div>

          {/* Price movement */}
          {(m.price_delta_24h != null || m.price_delta_pct_24h != null) && (
            <div className="rounded-xl bg-white/4 border border-white/6 p-3">
              <p className="text-[9px] uppercase tracking-wider text-slate-500 mb-2">Price Movement</p>
              <div className="grid grid-cols-2 gap-2">
                {m.price_delta_24h != null && (
                  <InfoCell
                    label="24h Change"
                    val={`${m.price_delta_24h > 0 ? "+" : ""}$${Math.abs(Math.round(m.price_delta_24h))}`}
                    accent={m.price_delta_24h < 0 ? "text-emerald-400" : m.price_delta_24h > 0 ? "text-red-400" : undefined}
                  />
                )}
                {m.price_delta_pct_24h != null && (
                  <InfoCell
                    label="24h %"
                    val={`${m.price_delta_pct_24h > 0 ? "+" : ""}${m.price_delta_pct_24h.toFixed(1)}%`}
                    accent={m.price_delta_pct_24h < 0 ? "text-emerald-400" : m.price_delta_pct_24h > 0 ? "text-red-400" : undefined}
                  />
                )}
              </div>
            </div>
          )}

          {/* Vs tier / venue medians */}
          {(m.price_vs_tier_median != null || m.price_vs_venue_median != null) && (
            <div className="rounded-xl bg-white/4 border border-white/6 p-3">
              <p className="text-[9px] uppercase tracking-wider text-slate-500 mb-2">Relative Pricing</p>
              <div className="grid grid-cols-2 gap-2">
                {m.price_vs_tier_median != null && (
                  <InfoCell
                    label="vs Tier Median"
                    val={`${m.price_vs_tier_median > 0 ? "+" : ""}${m.price_vs_tier_median.toFixed(1)}%`}
                    accent={m.price_vs_tier_median < 0 ? "text-emerald-400" : "text-slate-400"}
                  />
                )}
                {m.price_vs_venue_median != null && (
                  <InfoCell
                    label="vs Venue Median"
                    val={`${m.price_vs_venue_median > 0 ? "+" : ""}${m.price_vs_venue_median.toFixed(1)}%`}
                    accent={m.price_vs_venue_median < 0 ? "text-emerald-400" : "text-slate-400"}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function PriceCell({
  label,
  val,
  accent,
  bold,
}: {
  label: string;
  val: string;
  accent?: string;
  bold?: boolean;
}) {
  return (
    <div className="text-center">
      <p className="text-[9px] text-slate-600 uppercase tracking-wide mb-0.5">{label}</p>
      <p className={cn("text-sm tabular-nums", accent, bold && "font-semibold")}>{val}</p>
    </div>
  );
}

function InfoCell({
  label,
  val,
  accent,
}: {
  label: string;
  val: string;
  accent?: string;
}) {
  return (
    <div>
      <p className="text-[9px] text-slate-600 mb-0.5">{label}</p>
      <p className={cn("text-xs tabular-nums text-slate-300 font-medium", accent)}>{val}</p>
    </div>
  );
}

function ScoreBar({
  label,
  value,
  color,
  active,
}: {
  label: string;
  value: number;
  color: string;
  active: boolean;
}) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={cn(
      "rounded-lg p-2.5 border transition-colors",
      active ? "bg-white/5 border-white/10" : "bg-white/2 border-white/5",
    )}>
      <div className="flex items-center justify-between mb-1.5 text-[10px]">
        <span className="text-slate-500">{label}</span>
        <span
          className="font-semibold tabular-nums"
          style={{ color: active ? color : undefined }}
        >
          {value}/100
        </span>
      </div>
      <div className="h-1 bg-white/6 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: active ? color : "#334155" }}
        />
      </div>
    </div>
  );
}
