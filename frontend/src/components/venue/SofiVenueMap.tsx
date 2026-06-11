"use client";

import { useMemo, useState, useRef } from "react";
import type { VenueSection, VenueSectionMetrics } from "@/lib/types";

export type VenueMode = "opportunity" | "demand" | "inventory" | "price_trend";

interface Props {
  sections: VenueSection[];
  mode: VenueMode;
  selectedId: string | null;
  onSelectSection: (id: string) => void;
}

// ── Map geometry ──────────────────────────────────────────────────────────────
const CX = 190, CY = 190;
const RADIUS = 190; // SVG is 380×380
const GAP_DEG = 0.7;

// Rings keyed by level string
const RING: Record<string, { inner: number; outer: number }> = {
  lower:     { inner: 96,  outer: 120 },
  club:      { inner: 126, outer: 146 },
  upper_mid: { inner: 152, outer: 170 },
  upper_top: { inner: 176, outer: 194 },
  suite:     { inner: 96,  outer: 120 },
  arcade:    { inner: 152, outer: 170 },
};

// Clockwise zone order starting from North
const ZONE_ORDER = [
  "endzone_north",
  "corner_ne",
  "sideline_east",
  "corner_se",
  "endzone_south",
  "corner_sw",
  "sideline_west",
  "corner_nw",
] as const;

type Zone = typeof ZONE_ORDER[number];

// ── SVG path helpers ──────────────────────────────────────────────────────────
function pt(cx: number, cy: number, r: number, deg: number) {
  const rad = ((deg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arcPath(
  cx: number,
  cy: number,
  innerR: number,
  outerR: number,
  startDeg: number,
  endDeg: number,
): string {
  const span = endDeg - startDeg;
  if (span < 0.05) return "";
  const large = span > 180 ? 1 : 0;
  const o1 = pt(cx, cy, outerR, startDeg);
  const o2 = pt(cx, cy, outerR, endDeg);
  const i1 = pt(cx, cy, innerR, startDeg);
  const i2 = pt(cx, cy, innerR, endDeg);
  return [
    `M ${o1.x.toFixed(2)} ${o1.y.toFixed(2)}`,
    `A ${outerR} ${outerR} 0 ${large} 1 ${o2.x.toFixed(2)} ${o2.y.toFixed(2)}`,
    `L ${i2.x.toFixed(2)} ${i2.y.toFixed(2)}`,
    `A ${innerR} ${innerR} 0 ${large} 0 ${i1.x.toFixed(2)} ${i1.y.toFixed(2)}`,
    "Z",
  ].join(" ");
}

// ── Color helpers ─────────────────────────────────────────────────────────────
function lerp(a: number, b: number, t: number) {
  return Math.round(a + (b - a) * Math.max(0, Math.min(1, t)));
}
function hexColor(r: number, g: number, b: number) {
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}
function blendHex(from: string, to: string, t: number) {
  const fr = parseInt(from.slice(1, 3), 16);
  const fg = parseInt(from.slice(3, 5), 16);
  const fb = parseInt(from.slice(5, 7), 16);
  const tr = parseInt(to.slice(1, 3), 16);
  const tg = parseInt(to.slice(3, 5), 16);
  const tb = parseInt(to.slice(5, 7), 16);
  return hexColor(lerp(fr, tr, t), lerp(fg, tg, t), lerp(fb, tb, t));
}

const NO_DATA = "#1a2333";
const DIM     = "#1e293b";

function sectionColor(mode: VenueMode, m: VenueSectionMetrics | null): string {
  if (!m) return NO_DATA;
  switch (mode) {
    case "opportunity":
      if (m.value_score == null) return DIM;
      return blendHex("#1e3a5f", "#10b981", m.value_score / 100);
    case "demand":
      if (m.demand_score == null) return DIM;
      return blendHex("#1a1a2e", "#ef4444", m.demand_score / 100);
    case "inventory": {
      const cnt = m.listing_count ?? 0;
      const t = Math.min(cnt / 35, 1);
      return blendHex("#0f172a", "#3b82f6", t);
    }
    case "price_trend": {
      const pct = m.price_delta_pct_24h;
      if (pct == null) return DIM;
      if (pct <= -8)  return "#059669";
      if (pct <= -2)  return "#34d399";
      if (pct <=  2)  return "#475569";
      if (pct <=  8)  return "#fb923c";
      return "#ef4444";
    }
  }
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function SofiVenueMap({ sections, mode, selectedId, onSelectSection }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [tipPos, setTipPos] = useState<{ x: number; y: number } | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Group mapped sections by zone, skip unknown zones and un-ringable levels
  const zoneGroups = useMemo(() => {
    const groups: Partial<Record<Zone, Map<string, VenueSection[]>>> = {};
    for (const z of ZONE_ORDER) groups[z] = new Map();

    for (const s of sections) {
      const z = s.zone as Zone | null;
      const ring = s.level ?? "";
      if (!z || !ZONE_ORDER.includes(z) || !RING[ring]) continue;
      const zmap = groups[z]!;
      if (!zmap.has(ring)) zmap.set(ring, []);
      zmap.get(ring)!.push(s);
    }
    // Sort each ring group by numeric section_id
    for (const z of ZONE_ORDER) {
      for (const [, arr] of groups[z]!) {
        arr.sort((a, b) => {
          const na = parseInt(a.section_id), nb = parseInt(b.section_id);
          return isNaN(na) || isNaN(nb) ? a.section_id.localeCompare(b.section_id) : na - nb;
        });
      }
    }
    return groups;
  }, [sections]);

  // Compute zone angular spans (proportional to section count, equal visual section size)
  const zoneAngles = useMemo(() => {
    // Count sections per zone (all rings combined)
    const counts: Partial<Record<Zone, number>> = {};
    let total = 0;
    for (const z of ZONE_ORDER) {
      let c = 0;
      for (const [, arr] of zoneGroups[z]!) c += arr.length;
      counts[z] = c;
      total += c;
    }
    if (total === 0) return {} as Partial<Record<Zone, { start: number; end: number }>>;

    // Distribute 360° proportionally, starting from North (−22.5° of endzone_north center = 0°)
    const angles: Partial<Record<Zone, { start: number; end: number }>> = {};
    let cursor = -(counts["endzone_north"]! / total) * 180; // center endzone_north at 0°
    for (const z of ZONE_ORDER) {
      const span = (counts[z]! / total) * 360;
      angles[z] = { start: cursor, end: cursor + span };
      cursor += span;
    }
    return angles;
  }, [zoneGroups]);

  // Build arc paths for every visible section
  const paths = useMemo(() => {
    const result: Array<{
      id: string;
      path: string;
      section: VenueSection;
    }> = [];

    for (const z of ZONE_ORDER) {
      const za = zoneAngles[z];
      if (!za) continue;
      const zmap = zoneGroups[z]!;

      for (const [ring, arr] of zmap) {
        const { inner, outer } = RING[ring] ?? RING.lower;
        const n = arr.length;
        const usableSpan = za.end - za.start - GAP_DEG * (n + 1);
        if (usableSpan <= 0) continue;
        const segW = usableSpan / n;

        for (let i = 0; i < n; i++) {
          const s = arr[i];
          const startDeg = za.start + GAP_DEG * (i + 1) + segW * i;
          const endDeg   = startDeg + segW;
          const path = arcPath(CX, CY, inner, outer, startDeg, endDeg);
          if (path) result.push({ id: s.section_id, path, section: s });
        }
      }
    }
    return result;
  }, [zoneGroups, zoneAngles]);

  const hoveredSection = hoveredId ? sections.find((s) => s.section_id === hoveredId) ?? null : null;

  function onMouseEnter(e: React.MouseEvent, id: string) {
    setHoveredId(id);
    const rect = svgRef.current?.getBoundingClientRect();
    if (rect) setTipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }
  function onMouseMove(e: React.MouseEvent) {
    const rect = svgRef.current?.getBoundingClientRect();
    if (rect) setTipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }

  return (
    <div className="relative select-none">
      <svg
        ref={svgRef}
        viewBox="0 0 380 380"
        className="w-full"
        style={{ maxHeight: 400 }}
        onMouseLeave={() => { setHoveredId(null); setTipPos(null); }}
      >
        {/* Background */}
        <rect width="380" height="380" fill="#0c1421" rx="12" />

        {/* Outer ring guide */}
        <circle cx={CX} cy={CY} r={196} fill="none" stroke="#1e293b" strokeWidth="0.5" />

        {/* Field (football oval) */}
        <ellipse cx={CX} cy={CY} rx={60} ry={82} fill="#14532d" stroke="#166534" strokeWidth="0.75" />
        <line x1={CX} y1={CY - 72} x2={CX} y2={CY + 72} stroke="#166534" strokeWidth="0.4" opacity="0.5" />
        <text
          x={CX}
          y={CY}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#166534"
          fontSize="7"
          letterSpacing="2"
          opacity="0.55"
        >
          FIELD
        </text>

        {/* Ring separators */}
        {Object.values(RING).filter((r, i, a) => a.findIndex(x => x.outer === r.outer) === i).map((r, i) => (
          <circle key={i} cx={CX} cy={CY} r={r.outer + 1} fill="none" stroke="#1e293b" strokeWidth="0.4" opacity="0.4" />
        ))}

        {/* Section arcs */}
        {paths.map(({ id, path, section }) => {
          const isSelected = selectedId === id;
          const isHovered  = hoveredId === id;
          const color      = sectionColor(mode, section.metrics);
          const hasData    = !!section.metrics;

          return (
            <path
              key={id}
              d={path}
              fill={color}
              opacity={hasData ? 1 : 0.4}
              stroke={
                isSelected
                  ? "#f1f5f9"
                  : isHovered
                  ? "rgba(255,255,255,0.35)"
                  : "#0c1421"
              }
              strokeWidth={isSelected ? 1.5 : isHovered ? 0.8 : 0.4}
              style={{ cursor: "pointer", transition: "fill 0.12s" }}
              onMouseEnter={(e) => onMouseEnter(e, id)}
              onMouseMove={onMouseMove}
              onMouseLeave={() => { setHoveredId(null); setTipPos(null); }}
              onClick={() => onSelectSection(id)}
            />
          );
        })}

        {/* Compass labels */}
        <text x={CX} y={12}    textAnchor="middle" fill="#475569" fontSize="7.5">N</text>
        <text x={CX} y={373}   textAnchor="middle" fill="#475569" fontSize="7.5">S</text>
        <text x={10}  y={CY}   dominantBaseline="middle" fill="#475569" fontSize="7.5">W</text>
        <text x={370} y={CY}   dominantBaseline="middle" fill="#475569" fontSize="7.5">E</text>

        {/* Ring labels (bottom-left) */}
        <text x={22} y={286} fill="#334155" fontSize="6" textAnchor="middle">L</text>
        <text x={22} y={266} fill="#334155" fontSize="6" textAnchor="middle">C</text>
        <text x={22} y={246} fill="#334155" fontSize="6" textAnchor="middle">U</text>
      </svg>

      {/* Floating tooltip */}
      {hoveredSection && tipPos && (
        <SectionTooltip section={hoveredSection} mode={mode} x={tipPos.x} y={tipPos.y} />
      )}
    </div>
  );
}

// ── Tooltip ───────────────────────────────────────────────────────────────────
function SectionTooltip({
  section,
  mode,
  x,
  y,
}: {
  section: VenueSection;
  mode: VenueMode;
  x: number;
  y: number;
}) {
  const m = section.metrics;
  const f$ = (v: number | null | undefined) => (v != null ? `$${Math.round(v)}` : "—");
  const fn = (v: number | null | undefined) => (v != null ? v.toString() : "—");
  const score = (v: number | null | undefined) => (v != null ? `${Math.round(v)}/100` : "—");

  // Offset tooltip to avoid edge clipping
  const left = x > 260 ? x - 172 : x + 14;
  const top  = y > 260 ? y - 130 : y + 14;

  return (
    <div
      className="absolute z-30 pointer-events-none min-w-[160px] rounded-xl bg-slate-950 border border-white/10 shadow-2xl p-3"
      style={{ left, top }}
    >
      <p className="text-[11px] font-semibold text-slate-100 mb-0.5">{section.display_name}</p>
      {section.tier && (
        <p className="text-[9px] text-slate-500 uppercase tracking-wider mb-2">
          {section.tier.replace(/_/g, " ")}
        </p>
      )}
      {m ? (
        <div className="space-y-1">
          <Row label="Median"   val={f$(m.median_ask)}       accent="text-slate-200 font-medium" />
          <Row label="Low"      val={f$(m.low_ask)}          accent="text-slate-300" />
          <Row label="Listings" val={fn(m.listing_count)}    accent="text-slate-300" />
          {mode === "opportunity" && <Row label="Value"   val={score(m.value_score)}   accent="text-emerald-400 font-medium" />}
          {mode === "demand"      && <Row label="Demand"  val={score(m.demand_score)}  accent="text-red-400 font-medium" />}
          {mode === "price_trend" && m.price_delta_pct_24h != null && (
            <Row
              label="24h Δ"
              val={`${m.price_delta_pct_24h > 0 ? "+" : ""}${m.price_delta_pct_24h.toFixed(1)}%`}
              accent={m.price_delta_pct_24h < 0 ? "text-emerald-400 font-medium" : "text-red-400 font-medium"}
            />
          )}
          {m.price_vs_tier_median != null && (
            <Row
              label="vs tier"
              val={`${m.price_vs_tier_median > 0 ? "+" : ""}${m.price_vs_tier_median.toFixed(1)}%`}
              accent={m.price_vs_tier_median < 0 ? "text-emerald-400" : "text-slate-400"}
            />
          )}
        </div>
      ) : (
        <p className="text-[10px] text-slate-600">No active listings</p>
      )}
    </div>
  );
}

function Row({ label, val, accent }: { label: string; val: string; accent?: string }) {
  return (
    <div className="flex justify-between gap-4 text-[10px]">
      <span className="text-slate-500">{label}</span>
      <span className={accent ?? "text-slate-300 tabular-nums"}>{val}</span>
    </div>
  );
}
