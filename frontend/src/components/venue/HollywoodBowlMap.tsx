"use client";

/**
 * HollywoodBowlMap
 * Schematic amphitheater map for the Hollywood Bowl.
 * Fan-shaped layout: stage at bottom center, tiers fanning out upward.
 * Sections ordered from closest (H) to furthest (X1).
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
    case "inventory": return m.listing_count != null ? clamp(m.listing_count / 30, 0, 1) : null;
    case "price_trend": return m.price_delta_pct_24h == null ? 0.5 : clamp(0.5 + m.price_delta_pct_24h / 40, 0, 1);
  }
}

function Sec({
  sec, label, mode, selected, onClick,
  x, y, w, h, rx = 4,
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
        stroke={selected ? "#ffffff" : "rgba(255,255,255,0.1)"}
        strokeWidth={selected ? 2 : 0.5}
        opacity={sec ? 1 : 0.3}
      />
      {w > 14 && (
        <text x={x+w/2} y={y+h/2+1} textAnchor="middle" dominantBaseline="middle"
          fill={hasData ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.3)"}
          fontSize={Math.min(w / label.length * 1.4, 9)}
          fontFamily="monospace" fontWeight={selected ? "700" : "400"}
        >{label}</text>
      )}
    </g>
  );
}

interface Props {
  sections: VenueSection[];
  mode: VenueMode;
  selectedId: string | null;
  onSelectSection: (id: string) => void;
}

export default function HollywoodBowlMap({ sections, mode, selectedId, onSelectSection }: Props) {
  const byId = Object.fromEntries(sections.map((s) => [s.section_id, s]));
  const S = (id: string) => byId[id];
  const T = (id: string) => () => onSelectSection(id);
  const sel = (id: string) => selectedId === id;
  const hasAnyMetrics = sections.some((s) => s.metrics != null);

  // Canvas 480 × 460, stage at bottom center
  // Tiers fan upward from stage. Each tier = a curved row of section tiles.

  return (
    <div className="rounded-xl border border-white/8 bg-[#0c1421] overflow-hidden">
      {!hasAnyMetrics && (
        <p className="text-[10px] text-slate-600 text-center px-4 pt-3">
          Metrics compute as listings are collected
        </p>
      )}
      <svg viewBox="0 0 480 440" className="w-full" aria-label="Hollywood Bowl seating map">

        {/* Background fan shape */}
        <path d="M240 420 L20 40 Q240 -20 460 40 Z" fill="#0a1220" stroke="rgba(255,255,255,0.04)" strokeWidth={1} />

        {/* Stage */}
        <rect x={192} y={390} width={96} height={26} rx={4}
          fill="#1d2d44" stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
        <text x={240} y={406} textAnchor="middle" dominantBaseline="middle"
          fill="rgba(255,255,255,0.5)" fontSize={9} fontFamily="sans-serif" letterSpacing={1.5}>STAGE</text>

        {/* ── Row 1: H (front orchestra) ── wide center strip */}
        <Sec sec={S("H")} label="H" mode={mode} selected={sel("H")} onClick={T("H")}
          x={168} y={348} w={144} h={32} />

        {/* ── Row 2: P1 (premium center), W1 (west box), [east box mirror] ── */}
        <Sec sec={S("W1")} label="W1" mode={mode} selected={sel("W1")} onClick={T("W1")}
          x={86} y={312} w={52} h={28} />
        <Sec sec={S("P1")} label="P1" mode={mode} selected={sel("P1")} onClick={T("P1")}
          x={146} y={308} w={148} h={32} />
        {/* East mirror box */}
        <Sec sec={undefined} label="" mode={mode} selected={false} onClick={()=>{}}
          x={302} y={312} w={52} h={28} />

        {/* ── Row 3: W2, G2 (garden center), side boxes ── */}
        <Sec sec={S("W2")} label="W2" mode={mode} selected={sel("W2")} onClick={T("W2")}
          x={62} y={278} w={52} h={26} />
        <Sec sec={S("G2")} label="G2" mode={mode} selected={sel("G2")} onClick={T("G2")}
          x={122} y={274} w={164} h={30} />
        <Sec sec={S("GARDEN")} label="Garden" mode={mode} selected={sel("GARDEN")} onClick={T("GARDEN")}
          x={294} y={278} w={64} h={26} />

        {/* ── Row 4: W3, M1 (mid orchestra) ── */}
        <Sec sec={S("W3")} label="W3" mode={mode} selected={sel("W3")} onClick={T("W3")}
          x={42} y={244} w={50} h={26} />
        <Sec sec={S("M1")} label="M1" mode={mode} selected={sel("M1")} onClick={T("M1")}
          x={100} y={240} w={186} h={30} />
        {/* east filler */}
        <Sec sec={undefined} label="" mode={mode} selected={false} onClick={()=>{}}
          x={294} y={244} w={50} h={26} />

        {/* ── Row 5: M2, N1 ── */}
        <Sec sec={S("M2")} label="M2" mode={mode} selected={sel("M2")} onClick={T("M2")}
          x={78} y={208} w={82} h={26} />
        <Sec sec={S("N1")} label="N1" mode={mode} selected={sel("N1")} onClick={T("N1")}
          x={168} y={208} w={144} h={26} />
        <Sec sec={undefined} label="" mode={mode} selected={false} onClick={()=>{}}
          x={320} y={208} w={52} h={26} />

        {/* ── Row 6: F2, F3 (rear orchestra / terrace transition) ── */}
        <Sec sec={S("F2")} label="F2" mode={mode} selected={sel("F2")} onClick={T("F2")}
          x={62} y={174} w={88} h={26} />
        <Sec sec={S("F3")} label="F3" mode={mode} selected={sel("F3")} onClick={T("F3")}
          x={158} y={174} w={164} h={26} />
        <Sec sec={undefined} label="" mode={mode} selected={false} onClick={()=>{}}
          x={330} y={174} w={70} h={26} />

        {/* ── Row 7: J1, J2 (terrace low) ── */}
        <Sec sec={S("J1")} label="J1" mode={mode} selected={sel("J1")} onClick={T("J1")}
          x={48} y={140} w={84} h={26} />
        <Sec sec={S("J2")} label="J2" mode={mode} selected={sel("J2")} onClick={T("J2")}
          x={140} y={140} w={180} h={26} />
        <Sec sec={S("K2")} label="K2" mode={mode} selected={sel("K2")} onClick={T("K2")}
          x={328} y={140} w={80} h={26} />

        {/* ── Row 8: L1, Q1, Q2 (terrace mid) ── */}
        <Sec sec={S("L1")} label="L1" mode={mode} selected={sel("L1")} onClick={T("L1")}
          x={34} y={106} w={78} h={26} />
        <Sec sec={S("Q1")} label="Q1" mode={mode} selected={sel("Q1")} onClick={T("Q1")}
          x={120} y={106} w={108} h={26} />
        <Sec sec={S("Q2")} label="Q2" mode={mode} selected={sel("Q2")} onClick={T("Q2")}
          x={236} y={106} w={108} h={26} />
        <Sec sec={undefined} label="" mode={mode} selected={false} onClick={()=>{}}
          x={352} y={106} w={66} h={26} />

        {/* ── Row 9: T1, T2, U1 (terrace high) ── */}
        <Sec sec={S("T1")} label="T1" mode={mode} selected={sel("T1")} onClick={T("T1")}
          x={50} y={72} w={82} h={26} />
        <Sec sec={S("T2")} label="T2" mode={mode} selected={sel("T2")} onClick={T("T2")}
          x={140} y={72} w={200} h={26} />
        <Sec sec={S("U1")} label="U1" mode={mode} selected={sel("U1")} onClick={T("U1")}
          x={348} y={72} w={64} h={26} />

        {/* ── Row 10: X1 (extreme upper / back) ── */}
        <Sec sec={S("X1")} label="X1" mode={mode} selected={sel("X1")} onClick={T("X1")}
          x={62} y={38} w={356} h={26} />

        {/* ── Zone labels ── */}
        <text x={240} y={366} textAnchor="middle" fill="rgba(255,255,255,0.25)" fontSize={8} fontFamily="sans-serif" letterSpacing={1}>FRONT ORCHESTRA</text>
        <text x={60} y={248} textAnchor="middle" fill="rgba(255,255,255,0.12)" fontSize={7} fontFamily="sans-serif">BOX</text>
        <text x={240} y={224} textAnchor="middle" fill="rgba(255,255,255,0.12)" fontSize={7} fontFamily="sans-serif">MID ORCHESTRA</text>
        <text x={240} y={122} textAnchor="middle" fill="rgba(255,255,255,0.12)" fontSize={7} fontFamily="sans-serif">TERRACE</text>
        <text x={240} y={52} textAnchor="middle" fill="rgba(255,255,255,0.12)" fontSize={7} fontFamily="sans-serif">UPPER</text>
      </svg>
    </div>
  );
}
