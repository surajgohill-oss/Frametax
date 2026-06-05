"use client";
import { useState } from "react";
import { getEntityImage } from "@/lib/entityImages";

interface EntityLogoProps {
  entity: string;
  initial: string;
  accent: string;
  gradFrom: string;
  gradMid: string;
  size?: number;
  className?: string;
}

/**
 * EntityLogo — shows a real team logo from ESPN CDN when available,
 * gracefully falls back to a styled letter avatar.
 */
export function EntityLogo({
  entity,
  initial,
  accent,
  gradFrom,
  gradMid,
  size = 56,
  className = "",
}: EntityLogoProps) {
  const [imgError, setImgError] = useState(false);
  const imgConfig = getEntityImage(entity);
  const logoUrl = imgConfig.logo;
  const pad = Math.round(size * 0.1);

  // Base container — used for real logos
  const containerStyle: React.CSSProperties = {
    width: size,
    height: size,
    borderRadius: 14,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    border: "1px solid rgba(255,255,255,0.12)",
    boxShadow: "0 4px 16px rgba(0,0,0,0.45)",
    background: `linear-gradient(135deg, ${gradFrom} 0%, ${gradMid} 100%)`,
    overflow: "hidden",
  };

  if (logoUrl && !imgError) {
    return (
      <div style={containerStyle} className={className}>
        <img
          src={logoUrl}
          alt={entity}
          onError={() => setImgError(true)}
          style={{
            width: size - pad * 2,
            height: size - pad * 2,
            objectFit: "contain",
            imageRendering: "auto",
          }}
        />
      </div>
    );
  }

  // Letter avatar fallback — uses accent-tinted background so it's visible on dark page
  // Extract accent rgb for rgba usage (accent is a hex like "#A78BFA")
  const accentHex = accent.replace('#', '');
  const ar = parseInt(accentHex.slice(0, 2), 16);
  const ag = parseInt(accentHex.slice(2, 4), 16);
  const ab = parseInt(accentHex.slice(4, 6), 16);
  const accentRgb = `${ar},${ag},${ab}`;

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: 14,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        border: `1px solid rgba(${accentRgb}, 0.35)`,
        boxShadow: `0 4px 16px rgba(0,0,0,0.45), 0 0 0 1px rgba(${accentRgb}, 0.08) inset`,
        background: `linear-gradient(135deg, rgba(${accentRgb}, 0.18) 0%, rgba(${accentRgb}, 0.06) 100%)`,
        color: accent,
        fontWeight: 900,
        fontSize: size * 0.44,
        letterSpacing: "-0.05em",
        overflow: "hidden",
      }}
      className={className}
    >
      {initial}
    </div>
  );
}

/** Large version for the FeaturedHero / entity group header */
export function EntityLogoLarge({
  entity,
  initial,
  accent,
  gradFrom,
  gradMid,
}: Omit<EntityLogoProps, "size" | "className">) {
  return (
    <EntityLogo
      entity={entity}
      initial={initial}
      accent={accent}
      gradFrom={gradFrom}
      gradMid={gradMid}
      size={64}
    />
  );
}
