"use client";
/**
 * RepricingTimelineChart
 * Shows repriced-up and repriced-down counts per snapshot window over time.
 * Data source: attribution API transitions (price_changed classification with price_delta).
 */
import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { format } from "date-fns";

interface RepricingPoint {
  window: string;      // ISO timestamp of the snapshot window
  repriced_up: number;
  repriced_down: number;
}

export default function RepricingTimelineChart({
  transitions,
  height = 200,
}: {
  /** Raw transitions array from attribution API */
  transitions: any[] | null | undefined;
  height?: number;
}) {
  const chartData: RepricingPoint[] = useMemo(() => {
    if (!transitions?.length) return [];
    const byWindow: Record<string, { up: number; down: number }> = {};
    for (const t of transitions) {
      if (t.classification !== "price_changed") continue;
      const w = t.window_prev ?? t.window_curr;
      if (!w) continue;
      if (!byWindow[w]) byWindow[w] = { up: 0, down: 0 };
      const delta = t.price_delta ?? 0;
      if (delta > 0) byWindow[w].up++;
      else if (delta < 0) byWindow[w].down++;
    }
    return Object.entries(byWindow)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([window, counts]) => ({
        window,
        repriced_up:   counts.up,
        repriced_down: counts.down,
      }));
  }, [transitions]);

  if (!chartData.length) {
    return (
      <div style={{ height }} className="flex items-center justify-center text-slate-600 text-sm">
        No repricing timeline data available.
      </div>
    );
  }

  const tickFmt = (v: string) => {
    try { return format(new Date(v), "MM/dd"); } catch { return v; }
  };

  return (
    <div>
      <div className="flex items-center gap-4 px-4 pb-2">
        <span className="flex items-center gap-1 text-[11px]" style={{ color: "#F87171" }}>
          <span className="inline-block w-3 h-3 rounded-sm" style={{ background: "#F87171", opacity: 0.8 }} />
          Repriced Up
        </span>
        <span className="flex items-center gap-1 text-[11px]" style={{ color: "#34D399" }}>
          <span className="inline-block w-3 h-3 rounded-sm" style={{ background: "#34D399", opacity: 0.8 }} />
          Repriced Down
        </span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }} barSize={8}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey="window"
            tickFormatter={tickFmt}
            tick={{ fill: "#4B5563", fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: "rgba(255,255,255,0.05)" }}
          />
          <YAxis
            tick={{ fill: "#4B5563", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={30}
          />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "12px", color: "#e2e8f0" }}
            labelFormatter={(v) => { try { return format(new Date(v as string), "MMM d, HH:mm"); } catch { return v; } }}
          />
          <Bar dataKey="repriced_up"   name="Repriced Up"   fill="#F87171" fillOpacity={0.8} radius={[2, 2, 0, 0]} />
          <Bar dataKey="repriced_down" name="Repriced Down" fill="#34D399" fillOpacity={0.8} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
