"use client";

import { TrendingDown, TrendingUp, Zap, BarChart2, Star, Package } from "lucide-react";
import type { VenueClassificationsResponse, ClassificationEntry } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  data: VenueClassificationsResponse;
  onSelectSection: (id: string) => void;
  selectedId: string | null;
}

type BucketKey = keyof VenueClassificationsResponse["classifications"];

const BUCKETS: {
  key: BucketKey;
  label: string;
  icon: React.ElementType;
  accent: string;
  scoreKey: keyof ClassificationEntry;
  scoreLabel: string;
  scoreColor: string;
}[] = [
  {
    key: "best_value",
    label: "Best Value",
    icon: Star,
    accent: "text-emerald-400",
    scoreKey: "value_score",
    scoreLabel: "value",
    scoreColor: "#10b981",
  },
  {
    key: "highest_demand",
    label: "Highest Demand",
    icon: BarChart2,
    accent: "text-red-400",
    scoreKey: "demand_score",
    scoreLabel: "demand",
    scoreColor: "#ef4444",
  },
  {
    key: "fastest_price_drops",
    label: "Price Dropping",
    icon: TrendingDown,
    accent: "text-blue-400",
    scoreKey: "seller_pressure",
    scoreLabel: "pressure",
    scoreColor: "#3b82f6",
  },
  {
    key: "most_active",
    label: "Most Active",
    icon: Zap,
    accent: "text-amber-400",
    scoreKey: "inventory",
    scoreLabel: "listings",
    scoreColor: "#f59e0b",
  },
  {
    key: "inventory_building",
    label: "Inventory Rising",
    icon: TrendingUp,
    accent: "text-violet-400",
    scoreKey: "inventory",
    scoreLabel: "listings",
    scoreColor: "#8b5cf6",
  },
  {
    key: "inventory_depleting",
    label: "Selling Fast",
    icon: Package,
    accent: "text-orange-400",
    scoreKey: "inventory",
    scoreLabel: "listings",
    scoreColor: "#fb923c",
  },
];

export default function SectionOpportunityBoard({ data, onSelectSection, selectedId }: Props) {
  const cls = data.classifications;
  const activeBuckets = BUCKETS.filter((b) => (cls[b.key]?.length ?? 0) > 0);

  if (activeBuckets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <BarChart2 size={24} className="text-slate-700 mb-3" />
        <p className="text-xs text-slate-500">No classifications available yet.</p>
        <p className="text-[10px] text-slate-700 mt-1">Intelligence computes when listings are active.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activeBuckets.map((bucket) => {
        const entries = cls[bucket.key] ?? [];
        const Icon = bucket.icon;
        return (
          <div key={bucket.key}>
            <div className="flex items-center gap-1.5 mb-2">
              <Icon size={11} className={bucket.accent} />
              <h4 className={cn("text-[10px] font-semibold uppercase tracking-wider", bucket.accent)}>
                {bucket.label}
              </h4>
              <span className="text-[9px] text-slate-700 ml-auto">{entries.length}</span>
            </div>
            <div className="space-y-1">
              {entries.slice(0, 5).map((entry) => {
                const isSelected = selectedId === entry.section_id;
                const score = entry[bucket.scoreKey];
                const scoreNum = typeof score === "number" ? score : null;
                const pctVal = entry.price_vs_tier_median;

                return (
                  <button
                    key={entry.section_id}
                    onClick={() => onSelectSection(entry.section_id)}
                    className={cn(
                      "w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-left transition-colors",
                      isSelected
                        ? "bg-white/10 border border-white/15"
                        : "bg-white/3 border border-white/6 hover:bg-white/6 hover:border-white/10",
                    )}
                  >
                    {/* section name */}
                    <span className="flex-1 min-w-0 text-[11px] text-slate-300 font-medium truncate">
                      {entry.display_name}
                    </span>

                    {/* median price */}
                    {entry.median_ask != null && (
                      <span className="text-[10px] text-slate-400 tabular-nums flex-shrink-0">
                        ${Math.round(entry.median_ask).toLocaleString()}
                      </span>
                    )}

                    {/* vs tier */}
                    {pctVal != null && (
                      <span
                        className={cn(
                          "text-[9px] tabular-nums flex-shrink-0 font-medium",
                          pctVal < 0 ? "text-emerald-500" : "text-slate-600",
                        )}
                      >
                        {pctVal < 0 ? "" : "+"}
                        {pctVal.toFixed(0)}%
                      </span>
                    )}

                    {/* score badge */}
                    {scoreNum != null && (
                      <span
                        className="text-[9px] font-semibold tabular-nums flex-shrink-0 px-1 py-0.5 rounded"
                        style={{
                          color: bucket.scoreColor,
                          background: `${bucket.scoreColor}18`,
                        }}
                      >
                        {bucket.scoreLabel === "listings"
                          ? scoreNum.toLocaleString()
                          : `${Math.round(scoreNum)}`}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
