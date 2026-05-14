"use client";
import { useState, useMemo, useEffect } from "react";
import { api } from "@/lib/api";

interface Section { section_id: string; display_name: string; x: number; y: number; width: number; height: number; shape?: string; shape_data?: any; }
interface SectionPrice { section_id: string; display_name: string; lowest_ask?: number; listing_count?: number; }
interface Props {
  sections?: Section[];
  prices?: SectionPrice[];
  mapWidth?: number;
  mapHeight?: number;
  colorMode?: "price" | "inventory";
  onSectionClick?: (sectionId: string, displayName: string) => void;
  selectedSection?: string | null;
  venueSlug?: string;
  listings?: any[];
  mode?: "price" | "inventory";
}

function priceColor(value: number, min: number, max: number): string {
  if (max === min) return "rgb(100,140,220)";
  const t = (value - min) / (max - min);
  return `rgb(${Math.round(t * 220)},${Math.round((1 - t) * 180)},60)`;
}

function inventoryColor(count: number, max: number): string {
  if (max === 0) return "#2a3145";
  const t = Math.min(count / max, 1);
  return `rgb(${Math.round(20 + t * 30)},${Math.round(80 + t * 140)},${Math.round(200 + t * 55)})`;
}

export function VenueHeatmap({ sections: sectionsProp, prices: pricesProp, mapWidth = 800, mapHeight = 600, colorMode, onSectionClick, selectedSection, venueSlug, listings, mode }: Props) {
  const [hovered, setHovered] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; label: string } | null>(null);
  const [fetchedSections, setFetchedSections] = useState<Section[]>([]);

  useEffect(() => {
    if (venueSlug) api.venues.sections(venueSlug).then(setFetchedSections).catch(() => {});
  }, [venueSlug]);

  const sections: Section[] = sectionsProp ?? fetchedSections;
  const effectiveColorMode = colorMode ?? mode ?? "price";

  const prices: SectionPrice[] = pricesProp ?? (() => {
    if (!listings) return [];
    const map = new Map<string, { lowest_ask: number; count: number; display_name: string }>();
    for (const l of listings) {
      const sid = l.section_id ?? l.section ?? "";
      if (!sid) continue;
      const prev = map.get(sid);
      const ask = Number(l.price ?? l.lowest_ask ?? 0);
      if (!prev || ask < prev.lowest_ask) map.set(sid, { lowest_ask: ask, count: (prev?.count ?? 0) + 1, display_name: l.section ?? sid });
      else prev.count += 1;
    }
    return Array.from(map.entries()).map(([sid, v]) => ({ section_id: sid, display_name: v.display_name, lowest_ask: v.lowest_ask, listing_count: v.count }));
  })();

  const priceMap = useMemo(() => { const m = new Map<string, SectionPrice>(); for (const p of prices) m.set(p.section_id, p); return m; }, [prices]);
  const { minPrice, maxPrice, maxInventory } = useMemo(() => {
    const vals = prices.filter((p) => p.lowest_ask != null).map((p) => p.lowest_ask!);
    const counts = prices.filter((p) => p.listing_count != null).map((p) => p.listing_count!);
    return { minPrice: vals.length ? Math.min(...vals) : 0, maxPrice: vals.length ? Math.max(...vals) : 0, maxInventory: counts.length ? Math.max(...counts) : 0 };
  }, [prices]);

  function getFill(sec: Section): string {
    const p = priceMap.get(sec.section_id);
    if (!p) return "#1e2535";
    if (effectiveColorMode === "inventory" && p.listing_count != null) return inventoryColor(p.listing_count, maxInventory);
    if (p.lowest_ask != null) return priceColor(p.lowest_ask, minPrice, maxPrice);
    return "#1e2535";
  }

  function handleMouseMove(e: React.MouseEvent<SVGElement>, sec: Section) {
    const p = priceMap.get(sec.section_id);
    const svgRect = (e.currentTarget.closest("svg") as SVGSVGElement)?.getBoundingClientRect();
    if (!svgRect) return;
    const relX = ((e.clientX - svgRect.left) / svgRect.width) * mapWidth;
    const relY = ((e.clientY - svgRect.top) / svgRect.height) * mapHeight;
    let label = sec.display_name;
    if (p?.lowest_ask != null) label += ` · $${p.lowest_ask.toFixed(0)}`;
    if (p?.listing_count != null) label += ` · ${p.listing_count} listings`;
    setTooltip({ x: relX, y: relY, label });
    setHovered(sec.section_id);
  }

  function renderShape(sec: Section) {
    const fill = getFill(sec);
    const isActive = hovered === sec.section_id || selectedSection === sec.section_id;
    const stroke = isActive ? "#60a5fa" : "#0d1117";
    const opacity = priceMap.has(sec.section_id) ? 1 : 0.35;
    const common = { fill, stroke, strokeWidth: isActive ? 2 : 0.5, opacity, style: { cursor: "pointer", transition: "fill 0.15s" }, onMouseMove: (e: React.MouseEvent<SVGElement>) => handleMouseMove(e, sec), onMouseLeave: () => { setHovered(null); setTooltip(null); }, onClick: () => onSectionClick?.(sec.section_id, sec.display_name) };
    if (sec.shape === "polygon" && sec.shape_data?.points) return <polygon key={sec.section_id} points={sec.shape_data.points} {...common} />;
    return <rect key={sec.section_id} x={sec.x} y={sec.y} width={sec.width} height={sec.height} rx={3} {...common} />;
  }

  function renderLabel(sec: Section) {
    if (sec.width < 22 || sec.height < 14) return null;
    return <text key={`lbl-${sec.section_id}`} x={sec.x + sec.width / 2} y={sec.y + sec.height / 2} textAnchor="middle" dominantBaseline="middle" fontSize={Math.min(9, sec.width / 5)} fill="#ffffff" opacity={0.7} style={{ pointerEvents: "none", userSelect: "none" }}>{sec.display_name.replace(/^Section\s*/i, "")}</text>;
  }

  return (
    <div className="relative w-full select-none">
      <svg viewBox={`0 0 ${mapWidth} ${mapHeight}`} className="w-full rounded-lg bg-[#0d1117] border border-[#2a3145]" style={{ aspectRatio: `${mapWidth} / ${mapHeight}` }}>
        {sections.map((sec) => renderShape(sec))}
        {sections.map((sec) => renderLabel(sec))}
        {tooltip && (
          <g style={{ pointerEvents: "none" }}>
            <rect x={Math.min(tooltip.x + 8, mapWidth - 180)} y={Math.max(tooltip.y - 28, 4)} width={tooltip.label.length * 6.5 + 12} height={22} rx={4} fill="#1e2535" stroke="#2a3145" strokeWidth={1} />
            <text x={Math.min(tooltip.x + 14, mapWidth - 174)} y={Math.max(tooltip.y - 12, 18)} fontSize={11} fill="#e2e8f0">{tooltip.label}</text>
          </g>
        )}
      </svg>
      <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
        {effectiveColorMode === "price" && prices.some((p) => p.lowest_ask != null) ? (<><span>${minPrice.toFixed(0)}</span><div className="flex-1 h-2 rounded" style={{ background: "linear-gradient(to right, rgb(0,180,60), rgb(220,0,60))" }} /><span>${maxPrice.toFixed(0)}</span></>) : effectiveColorMode === "inventory" && prices.some((p) => p.listing_count != null) ? (<><span>0</span><div className="flex-1 h-2 rounded" style={{ background: "linear-gradient(to right, rgb(20,80,200), rgb(50,220,255))" }} /><span>{maxInventory}</span></>) : (<span className="text-slate-600">No pricing data available</span>)}
        <div className="flex items-center gap-1 ml-4"><div className="w-3 h-3 rounded bg-[#1e2535] border border-[#2a3145]" /><span>No data</span></div>
      </div>
    </div>
  );
}
