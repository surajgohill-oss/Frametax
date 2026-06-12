"use client";

/**
 * GenericVenueMap
 *
 * A tier-grouped section heat-map that works for any venue.
 * Groups sections by tier, renders each as a clickable tile with a colour
 * derived from the active VenueMode metric.
 */

import type { VenueSection } from "@/lib/types";
import type { VenueMode } from "./SofiVenueMap";
import { cn } from "@/lib/utils";

// ── Colour helpers ────────────────────────────────────────────────────────────

const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * clamp(t, 0, 1);
}

/** 0–1 score → hex colour for each mode */
function modeColor(mode: VenueMode, score: number | null): string {
  if (score == null) return "#1a2333";
  const t = clamp(score, 0, 1);
  switch (mode) {
    case "opportunity": {
      // grey → emerald
      const r = Math.round(lerp(0x1e, 0x10, t));
      const g = Math.round(lerp(0x3a, 0xb9, t));
      const b = Math.round(lerp(0x5f, 0x81, t));
      return `rgb(${r},${g},${b})`;
    }
    case "demand": {
      // dark → red
      const r = Math.round(lerp(0x1a, 0xef, t));
      const g = Math.round(lerp(0x1a, 0x44, t));
      const b = Math.round(lerp(0x2e, 0x44, t));
      return `rgb(${r},${g},${b})`;
    }
    case "inventory": {
      // near-black → blue
      const r = Math.round(lerp(0x0f, 0x3b, t));
      const g = Math.round(lerp(0x17, 0x82, t));
      const b = Math.round(lerp(0x2a, 0xf6, t));
      return `rgb(${r},${g},${b})`;
    }
    case "price_trend": {
      // red (dropping) → grey (flat) → green (rising)
      // score 0=dropping, 0.5=flat, 1=rising
      if (t < 0.5) {
        const u = t / 0.5;
        const r = Math.round(lerp(0xef, 0x47, u));
        const g = Math.round(lerp(0x44, 0x55, u));
        const b = Math.round(lerp(0x44, 0x69, u));
        return `rgb(${r},${g},${b})`;
      } else {
        const u = (t - 0.5) / 0.5;
        const r = Math.round(lerp(0x47, 0x05, u));
        const g = Math.round(lerp(0x55, 0x96, u));
        const b = Math.round(lerp(0x69, 0x69, u));
        return `rgb(${r},${g},${b})`;
      }
    }
  }
}

function getModeScore(mode: VenueMode, section: VenueSection): number | null {
  const m = section.metrics;
  if (!m) return null;
  switch (mode) {
    case "opportunity": return m.value_score != null ? m.value_score / 100 : m.deal_score;
    case "demand":      return m.demand_score;
    case "inventory": {
      if (m.listing_count == null) return null;
      return clamp(m.listing_count / 30, 0, 1);
    }
    case "price_trend": {
      const pct = m.price_delta_pct_24h;
      if (pct == null) return 0.5;
      return clamp(0.5 + pct / 40, 0, 1);
    }
  }
}

// ── Tier normalisation ────────────────────────────────────────────────────────
const TIER_ORDER: Record<string, number> = {
  floor: 0, pit: 0,
  "lower bowl": 1, lower: 1, "200s": 1,
  club: 2, "club level": 2,
  "upper bowl": 3, upper: 3, "300s": 3, "400s": 3, terrace: 3,
  suite: 4, premium: 4,
  ga: 5, "general admission": 5,
  other: 99,
};

function normTier(tier: string | null): string {
  if (!tier) return "Other";
  const t = tier.toLowerCase();
  // Return the canonical display name
  if (t.includes("floor") || t.includes("pit")) return "Floor / Pit";
  if (t.includes("lower")) return "Lower Bowl";
  if (t.includes("club")) return "Club Level";
  if (t.includes("upper")) return "Upper Bowl";
  if (t.includes("terrace")) return "Terrace";
  if (t.includes("suite") || t.includes("premium")) return "Premium";
  if (t.includes("ga") || t.includes("general")) return "General Admission";
  return tier;
}

function tierSortKey(tier: string): number {
  return TIER_ORDER[tier.toLowerCase()] ?? TIER_ORDER[normTier(tier).toLowerCase()] ?? 50;
}

// ── Component ─────────────────────────────────────────────────────────────────
interface Props {
  sections: VenueSection[];
  mode: VenueMode;
  selectedId: string | null;
  onSelectSection: (id: string) => void;
  venueName?: string;
}

export default function GenericVenueMap({
  sections,
  mode,
  selectedId,
  onSelectSection,
  venueName,
}: Props) {
  // Group by tier
  const groups = new Map<string, VenueSection[]>();
  for (const s of sections) {
    const t = normTier(s.tier);
    if (!groups.has(t)) groups.set(t, []);
    groups.get(t)!.push(s);
  }

  // Sort tiers by importance
  const sortedTiers = [...groups.entries()].sort(
    ([a], [b]) => tierSortKey(a) - tierSortKey(b)
  );

  const hasAnyMetrics = sections.some((s) => s.metrics != null);

  return (
    <div className="rounded-xl border border-white/8 bg-[#0c1421] p-4 space-y-4">
      {!hasAnyMetrics && (
        <div className="text-center py-4">
          <p className="text-xs text-slate-600">
            Section metrics compute as listings are collected.
            Colors will appear once data is available.
          </p>
        </div>
      )}

      {sortedTiers.map(([tierName, tierSections]) => (
        <div key={tierName} className="space-y-2">
          <p className="text-[9px] font-semibold uppercase tracking-widest text-slate-600">
            {tierName}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {tierSections
              .sort((a, b) => (a.display_name ?? "").localeCompare(b.display_name ?? ""))
              .map((sec) => {
                const score = getModeScore(mode, sec);
                const bg = modeColor(mode, score);
                const isSelected = selectedId === sec.section_id;
                const hasMetrics = sec.metrics != null;

                return (
                  <button
                    key={sec.section_id}
                    onClick={() => onSelectSection(sec.section_id)}
                    title={sec.display_name}
                    className={cn(
                      "relative rounded px-2 py-1 text-[10px] font-medium transition-all border",
                      isSelected
                        ? "ring-2 ring-white/50 border-white/30 scale-105"
                        : "border-transparent hover:border-white/20 hover:scale-105",
                      hasMetrics ? "text-white/90" : "text-white/30"
                    )}
                    style={{
                      backgroundColor: bg,
                      minWidth: "2.5rem",
                    }}
                  >
                    {sec.display_name.replace(/^section\s+/i, "").replace(/^sec\s+/i, "")}
                  </button>
                );
              })}
          </div>
        </div>
      ))}

      {sections.length === 0 && (
        <div className="flex items-center justify-center py-12 text-slate-600 text-xs">
          No sections configured for this venue.
        </div>
      )}
    </div>
  );
}
