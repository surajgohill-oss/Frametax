"use client";

/**
 * GreekTheatreMap
 * Schematic amphitheater map for the Greek Theatre (Los Angeles).
 * Small intimate venue (~5,900). Fan-shaped, stage at bottom.
 * Sections: Pit → VIP Boxes → Reserved A → Reserved B → Reserved C → Terrace → Benches
 */

import type { VenueSection } from "@/lib/types";
import type { VenueMode } from "./SofiVenueMap";

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

function modeColor(mode: VenueMode, score: number | null): string {
  if (score == null) return "#1a2535";
  const t = clamp(score, 0, 1);
  function lerp(a: number, b: number) { return Math.round(a + (b - a) * t); }
  switch (mode) {
    case "opportunity": return `rgb(${lerp(0x1e,0x10)},${lerp(0x3a,0xb9)},${lerp(0x5f,0x81)})`;
    case "demand":      return `rgb(${lerp(0x1a,0xef)},${lerp(0x1a,0x44)},${lerp(0x2e,0x44)})`;
    case "inventory":   return `rgb(${lerp(0x0f,0x3b)},${lerp(0x17,0x82)},${lerp(0x2a,0xf6)})`;
    case "price_trend": {
      if (t < 0.5) {
        const u = t / 0.5;
        const l2 = (a: number, b: number) => Math.round(a + (b - a) * u);
        return `rgb(${l2(0xef,0x47)},${l2(0x44,0x55)},${l2(0x44,0x69)})`;
      }
      const u = (t - 0.5) / 0.5;
      const l2 = (a: number, b: number) => Math.round(a + (b - a) * u);
      return `rgb(${l2(0x47,0x05)},${l2(0x55,0x96)},${l2(0x69,0x69)})`;
    }
  }
}

function getModeScore(mode: VenueMode, s: VenueSection): number | null {
  const m = s.metrics;
  if (!m) return null;
  switch (mode) {
    case "opportunity": return m.value_score != null ? m.value_score / 100 : m.deal_score;
    case "demand": return m.demand_score;
    case "inventory": return m.listing_count != null ? clamp(m.listing_count / 20, 0, 1) : null;
    case "price_trend": return m.price_delta_pct_24h == null ? 0.5 : clamp(0.5 + m.price_delta_pct_24h / 40, 0, 1);
  }
}

function Sec({
  sec, label, mode, selected, onClick,
  x, y, w, h, rx = 5,
}: {
  sec?: VenueSection; label: string; mode: VenueMode;
  selected: boolean; onClick: () => void;
  x: number; y: number; w: number; h: number; rx?: number;
}) {
  const score = sec ? getModeScore(mode, sec) : null;
  const fill  = sec ? modeColor(mode, score) : "#111827";
  const hasData = sec?.metrics != null;
  return (
    <g onClick={onClick} style={{ cursor: "pointer", userSelect: "none" }}>
      <rect x={x} y={y} width={w} height={h} rx={rx}
        fill={fill}
        stroke={selected ? "#ffffff" : "rgba(255,255,255,0.12)"}
        strokeWidth={selected ? 2.5 : 0.75}
        opacity={sec ? 1 : 0.3}
      />
      <text x={x+w/2} y={y+h/2+1} textAnchor="middle" dominantBaseline="middle"
        fill={hasData ? "rgba(255,255,255,0.95)" : "rgba(255,255,255,0.3)"}
        fontSize={Math.min(w / label.length * 1.5, 11)}
        fontFamily="system-ui, sans-serif"
        fontWeight={selected ? "700" : "500"}
      >{label}</text>
    </g>
  );
}

interface Props {
  sections: VenueSection[];
  mode: VenueMode;
  selectedId: string | null;
  onSelectSection: (id: string) => void;
}

export default function GreekTheatreMap({ sections, mode, selectedId, onSelectSection }: Props) {
  const byId = Object.fromEntries(sections.map((s) => [s.section_id, s]));
  const S = (id: string) => byId[id];
  const T = (id: string) => () => onSelectSection(id);
  const sel = (id: string) => selectedId === id;
  const hasAnyMetrics = sections.some((s) => s.metrics != null);

  // Canvas 480 × 440, stage at bottom
  // Intimate venue — sections are large and readable

  return (
    <div className="rounded-xl border border-white/8 bg-[#0c1421] overflow-hidden">
      {!hasAnyMetrics && (
        <p className="text-[10px] text-slate-600 text-center px-4 pt-3">
          Metrics compute as listings are collected
        </p>
      )}
      <svg viewBox="0 0 480 430" className="w-full" aria-label="Greek Theatre seating map">

        {/* Background hillside fan */}
        <path d="M240 418 L30 50 Q240 10 450 50 Z" fill="#0a1220" stroke="rgba(255,255,255,0.04)" strokeWidth={1} />

        {/* Stage */}
        <rect x={178} y={384} width={124} height={28} rx={5}
          fill="#1d2d44" stroke="rgba(255,255,255,0.2)" strokeWidth={1} />
        <text x={240} y={401} textAnchor="middle" dominantBaseline="middle"
          fill="rgba(255,255,255,0.55)" fontSize={10} fontFamily="sans-serif" letterSpacing={1.5}>STAGE</text>

        {/* ── PIT (GA in front of stage) ── */}
        <Sec sec={S("pit")} label="PIT" mode={mode} selected={sel("pit")} onClick={T("pit")}
          x={176} y={342} w={128} h={34} rx={6} />

        {/* ── VIP Boxes (sides at stage level) ── */}
        <Sec sec={S("vip-boxes")} label="VIP" mode={mode} selected={sel("vip-boxes")} onClick={T("vip-boxes")}
          x={80} y={348} w={88} h={28} rx={5} />
        <Sec sec={S("vip-boxes")} label="VIP" mode={mode} selected={sel("vip-boxes")} onClick={T("vip-boxes")}
          x={312} y={348} w={88} h={28} rx={5} />

        {/* ── Reserved A (front orchestra) ── */}
        <Sec sec={S("reserved-a")} label="Reserved A" mode={mode} selected={sel("reserved-a")} onClick={T("reserved-a")}
          x={96} y={296} w={288} h={38} />

        {/* Reserved A label row */}
        <text x={240} y={320} textAnchor="middle" dominantBaseline="middle"
          fill={S("reserved-a")?.metrics ? "rgba(255,255,255,0.0)" : "rgba(255,255,255,0.0)"} fontSize={0} />

        {/* ── Reserved B (mid orchestra) ── */}
        <Sec sec={S("reserved-b")} label="Reserved B" mode={mode} selected={sel("reserved-b")} onClick={T("reserved-b")}
          x={72} y={248} w={336} h={38} />

        {/* ── Reserved C (rear orchestra) ── */}
        <Sec sec={S("reserved-c")} label="Reserved C" mode={mode} selected={sel("reserved-c")} onClick={T("reserved-c")}
          x={52} y={200} w={376} h={38} />

        {/* ── Terrace (upper hillside) ── */}
        <Sec sec={S("terrace")} label="Terrace" mode={mode} selected={sel("terrace")} onClick={T("terrace")}
          x={36} y={150} w={408} h={40} />

        {/* ── Benches (rear bench seating) ── */}
        <Sec sec={S("benches")} label="Benches" mode={mode} selected={sel("benches")} onClick={T("benches")}
          x={22} y={100} w={436} h={40} />

        {/* ── Top label ── */}
        <text x={240} y={68} textAnchor="middle" fill="rgba(255,255,255,0.12)" fontSize={8} fontFamily="sans-serif" letterSpacing={1.5}>GREEK THEATRE · GRIFFITH PARK</text>

        {/* Proximity arrows */}
        <text x={22} y={376} fill="rgba(255,255,255,0.2)" fontSize={8} fontFamily="sans-serif">← closest</text>
        <text x={22} y={115} fill="rgba(255,255,255,0.2)" fontSize={8} fontFamily="sans-serif">← farthest</text>
      </svg>
    </div>
  );
}
