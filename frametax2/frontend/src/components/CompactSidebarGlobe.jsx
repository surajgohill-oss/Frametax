import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { GLOBE_THEME } from "../lib/globeVisualTokens";

// The 80px sidebar globe: the SAME product as the Company / Project Globe at a smaller scale. It shares the Globe's visual
// tokens (lib/globeVisualTokens.js: near-black navy stage with its maritime bloom, deep ocean, graphite land with a hairline
// boundary, cool limb and atmosphere, upper-left key light) but deliberately does NOT mount the heavyweight Globe3D engine:
// no three-globe, no polygon layers, no CSS2D hit targets, no handlers. One baked equirectangular texture (ocean, land,
// boundaries, plus the highlighted territories), a Phong sphere, two thin Fresnel shells and a handful of dots and lines.
//
// FROZEN subsystem (2026-07-28), unlocked by the user 2026-10-08 for the leading-structure/portfolio overlay and for the
// Globe visual-language alignment. Do not import Globe3D or share scene/material objects with it.
function webglAvailable() {
  try {
    const c = document.createElement("canvas");
    const gl = c.getContext("webgl2") || c.getContext("webgl") || c.getContext("experimental-webgl");
    if (!gl) return false;
    const lose = gl.getExtension("WEBGL_lose_context");
    if (lose) lose.loseContext();
    return true;
  } catch {
    return false;
  }
}

const currentTheme = () => (document.documentElement.getAttribute("data-theme") === "night" ? GLOBE_THEME.night : GLOBE_THEME.day);

// At 80px, small islands degenerate into stray pixels. Rings whose bounding box is smaller than this fraction of the texture
// are dropped, leaving the major landmasses that read as Earth at this scale.
const MIN_RING_EXTENT_FRAC = 0.012;

const projectPoint = (lon, lat, w, h) => [((lon + 180) / 360) * w, ((90 - lat) / 180) * h];

// Breaks the path at antimeridian-crossing jumps instead of drawing a streak across the whole texture.
function tracePath(ctx, rings, w, h) {
  for (const ring of rings) {
    let started = false;
    let prevLon = null;
    for (const [lon, lat] of ring) {
      const [x, y] = projectPoint(lon, lat, w, h);
      if (!started) { ctx.moveTo(x, y); started = true; }
      else if (prevLon != null && Math.abs(lon - prevLon) > 180) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      prevLon = lon;
    }
    ctx.closePath();
  }
}

function ringIsSignificant(ring) {
  let minLon = Infinity, maxLon = -Infinity, minLat = Infinity, maxLat = -Infinity;
  for (const [lon, lat] of ring) {
    if (lon < minLon) minLon = lon;
    if (lon > maxLon) maxLon = lon;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
  }
  return (maxLon - minLon) / 360 > MIN_RING_EXTENT_FRAC || (maxLat - minLat) / 180 > MIN_RING_EXTENT_FRAC;
}

const polygonsOf = (feat) => {
  const g = feat?.geometry;
  if (!g) return [];
  return g.type === "Polygon" ? [g.coordinates] : g.type === "MultiPolygon" ? g.coordinates : [];
};

// Same feature -> country key rule the Globe uses (ISO_A2, with the two Natural Earth -99 fixes).
const ISO_A2_FIX_BY_ADM0_A3 = { FRA: "FR", NOR: "NO" };
const isoOf = (feat) => {
  const raw = feat?.properties?.ISO_A2;
  return raw && raw !== "-99" ? raw : ISO_A2_FIX_BY_ADM0_A3[feat?.properties?.ADM0_A3] || raw;
};

// The world geometry is fetched once per page session (own promise, never shared with Globe3D's load state).
let geoPromise = null;
const loadGeo = () => {
  if (!geoPromise) {
    geoPromise = fetch("/geo/world-110m.geojson")
      .then((r) => (r.ok ? r.json() : { features: [] }))
      .catch(() => ({ features: [] }))
      .then((geo) => (geo.features || []).map((f) => ({ iso: isoOf(f), polys: polygonsOf(f).filter((rings) => rings.length && ringIsSignificant(rings[0])) })));
  }
  return geoPromise;
};

const W = 1024;
const H = 512;
const mixToward = (hex, toward, t) => {
  const a = parseInt(hex.slice(1), 16); const b = parseInt(toward.slice(1), 16);
  const ch = (i) => Math.round(((a >> i) & 255) + (((b >> i) & 255) - ((a >> i) & 255)) * t).toString(16).padStart(2, "0");
  return `#${ch(16)}${ch(8)}${ch(0)}`;
};

// Paints the texture: Globe ocean, graphite land, hairline boundary, then the overlay's territories (principal at full
// strength with a lighter edge; participants a muted step toward the land colour) -- the Company/Project Globe hierarchy.
function paintTexture(ctx, features, theme, territories) {
  ctx.fillStyle = theme.ocean;
  ctx.fillRect(0, 0, W, H);
  ctx.lineJoin = "round";
  const fillAndEdge = (rings, fill, edge, edgeAlpha, lineWidth) => {
    ctx.beginPath();
    for (const ring of rings) tracePath(ctx, [ring], W, H);
    ctx.fillStyle = fill;
    ctx.fill("evenodd");
    ctx.globalAlpha = edgeAlpha;
    ctx.strokeStyle = edge;
    ctx.lineWidth = lineWidth;
    ctx.stroke();
    ctx.globalAlpha = 1;
  };
  for (const f of features) for (const rings of f.polys) fillAndEdge(rings, theme.land, theme.stroke, 0.45, 1);
  const byIso = new Map();
  for (const t of territories || []) if (!byIso.has(t.code) || t.principal) byIso.set(t.code, t);
  for (const f of features) {
    const t = byIso.get(f.iso);
    if (!t) continue;
    const fill = t.principal ? t.color : mixToward(t.color, theme.land, 0.3);
    const edge = t.principal ? "#ffffff" : mixToward(t.color, "#ffffff", 0.5);
    for (const rings of f.polys) fillAndEdge(rings, fill, edge, t.principal ? 0.95 : 0.7, t.principal ? 2.4 : 1.6);
  }
}

// Same equirectangular mapping SphereGeometry uses for its UVs (u = (lon + 180) / 360), so markers sit on the geography.
function surfacePoint(lat, lng, r = 1) {
  const phi = ((lng + 180) * Math.PI) / 180;
  const theta = ((90 - lat) * Math.PI) / 180;
  return new THREE.Vector3(-r * Math.cos(phi) * Math.sin(theta), r * Math.cos(theta), r * Math.sin(phi) * Math.sin(theta));
}

const NEUTRAL_ROUTE = "#e8dfc8";

// Rebuilds the overlay group's children from { markers, routes }: thin, restrained routes; the principal a larger dot on a
// white backing, participants smaller dots. Arcs stay below radius 1.07 so nothing reaches the canvas edge.
function buildOverlay(group, overlay) {
  for (const child of [...group.children]) {
    group.remove(child);
    child.geometry?.dispose();
    child.material?.dispose();
  }
  if (!overlay) return;
  for (const r of overlay.routes) {
    const a = surfacePoint(r.from.lat, r.from.lng, 1.006);
    const b = surfacePoint(r.to.lat, r.to.lng, 1.006);
    const lift = Math.min(1.07, 1.01 + a.distanceTo(b) * 0.05);
    const mid = a.clone().add(b).normalize().multiplyScalar(lift);
    const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
    group.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(curve.getPoints(24)),
      new THREE.LineBasicMaterial({ color: r.color || NEUTRAL_ROUTE, transparent: true, opacity: 0.8 }),
    ));
  }
  for (const m of overlay.markers) {
    const pos = surfacePoint(m.lat, m.lng, 1.012);
    if (m.principal) {
      const backing = new THREE.Mesh(new THREE.SphereGeometry(0.04, 12, 12), new THREE.MeshBasicMaterial({ color: "#ffffff" }));
      backing.position.copy(pos);
      group.add(backing);
    }
    const dot = new THREE.Mesh(
      new THREE.SphereGeometry(m.principal ? 0.03 : 0.024, 12, 12),
      new THREE.MeshBasicMaterial({ color: m.color || NEUTRAL_ROUTE }),
    );
    dot.position.copy(surfacePoint(m.lat, m.lng, m.principal ? 1.034 : 1.012));
    group.add(dot);
  }
}

// Soft Fresnel shell (additive, back faces): the Globe's cool limb, kept thin and restrained at this scale.
function fresnelShell(radius, color, power, intensity) {
  return new THREE.Mesh(
    new THREE.SphereGeometry(radius, 40, 40),
    new THREE.ShaderMaterial({
      uniforms: { uColor: { value: new THREE.Color(color) }, uPower: { value: power }, uIntensity: { value: intensity } },
      vertexShader: "varying vec3 vN; varying vec3 vV; void main(){ vN = normalize(normalMatrix * normal); vec4 mv = modelViewMatrix * vec4(position,1.0); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }",
      fragmentShader: "uniform vec3 uColor; uniform float uPower; uniform float uIntensity; varying vec3 vN; varying vec3 vV; void main(){ float f = pow(1.0 - abs(dot(vN, vV)), uPower); gl_FragColor = vec4(uColor, f * uIntensity); }",
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      transparent: true,
      depthWrite: false,
    }),
  );
}

/**
 * Compact brand-mark globe for the sidebar identity slot. With an `overlay` (lib/globeStructure.js::miniGlobeOverlay on a
 * project route, lib/companyScene.js::buildPortfolioMiniOverlay on company routes) it shows the active structure(s) the way
 * the full Globe does: territories in the structure's colour (selected-structure status colour on project routes, production
 * stage colour on company routes), principal vs participant hierarchy, restrained routes. null keeps the neutral globe.
 *
 * One render loop only, and only while it is useful: while on screen, tab visible and reduced motion off; otherwise frames
 * are drawn on demand (texture load, overlay or theme change).
 */
export default function CompactSidebarGlobe({ size = 80, className = "", overlay = null }) {
  const mountRef = useRef(null);
  const stateRef = useRef({});
  const [failed, setFailed] = useState(false);
  const [themeKey, setThemeKey] = useState(() => document.documentElement.getAttribute("data-theme") || "day");

  // The app theme switch changes the Globe's tokens; follow it.
  useEffect(() => {
    const mo = new MutationObserver(() => setThemeKey(document.documentElement.getAttribute("data-theme") || "day"));
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => mo.disconnect();
  }, []);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    if (!webglAvailable()) { setFailed(true); return; }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    // d = R / tan(fov/2) with a small margin, so the full circle sits centered with no edge clipping at any size.
    camera.position.set(0, 0, 2.65);

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      setFailed(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(size, size);
    mount.innerHTML = "";
    mount.appendChild(renderer.domElement);

    // Upper-left warm-ivory key light and a cool maritime fill from the lower right -- the Globe's light direction. Its own
    // THREE.Light instances, never shared with Globe3D.jsx.
    scene.add(new THREE.AmbientLight(0xffffff, 0.92));
    const key = new THREE.DirectionalLight(0xfff1dc, 0.7);
    key.position.set(-2.2, 1.7, 2.2);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x7f96b0, 0.22);
    fill.position.set(2, -1, -1.5);
    scene.add(fill);

    const group = new THREE.Group();
    group.rotation.x = -0.22; // gentle fixed tilt so it reads as a sphere at rest
    scene.add(group);

    const theme = currentTheme();
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(1, 48, 48),
      new THREE.MeshPhongMaterial({
        color: 0xffffff,
        emissive: new THREE.Color(theme.oceanEmissive).multiplyScalar(0.7),
        shininess: 140,
        specular: new THREE.Color("#26354b"),
      }),
    );
    group.add(sphere);
    const overlayGroup = new THREE.Group();
    group.add(overlayGroup);
    // Cool limb + faint atmosphere, as the Globe's rim shell and atmosphere, thin at this scale (outside the spinning group).
    const rim = fresnelShell(1.035, theme.rim, 3.2, 0.34);
    const atmosphere = fresnelShell(1.1, theme.atmosphere, 4.6, 0.3);
    scene.add(rim);
    scene.add(atmosphere);

    const canvas = document.createElement("canvas");
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext("2d");
    const texture = new THREE.CanvasTexture(canvas);
    // The canvas is authored in sRGB; without this the map is sampled as linear and washes out.
    texture.colorSpace = THREE.SRGBColorSpace;
    // 1024px texture on an 80px sphere: anisotropy keeps coastlines from shimmering into mush near the limb.
    texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
    sphere.material.map = texture;
    // Pre-geometry: just the ocean, so the sphere is never a white ball.
    ctx.fillStyle = theme.ocean;
    ctx.fillRect(0, 0, W, H);
    texture.needsUpdate = true;

    const render = () => renderer.render(scene, camera);
    let cancelled = false;
    const repaint = () => {
      const { features } = stateRef.current;
      if (!features) return;
      const t = currentTheme();
      paintTexture(ctx, features, t, stateRef.current.territories);
      sphere.material.emissive.set(t.oceanEmissive).multiplyScalar(0.7);
      rim.material.uniforms.uColor.value.set(t.rim);
      atmosphere.material.uniforms.uColor.value.set(t.atmosphere);
      texture.needsUpdate = true;
      render();
    };
    loadGeo().then((features) => {
      if (cancelled) return;
      stateRef.current.features = features;
      repaint();
    });

    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    let onScreen = true;
    let frameId = null;
    const loop = () => {
      group.rotation.y += 0.0022;
      render();
      frameId = requestAnimationFrame(loop);
    };
    const sync = () => {
      const animate = onScreen && !document.hidden && !motionQuery.matches;
      if (animate && frameId == null) frameId = requestAnimationFrame(loop);
      if (!animate && frameId != null) { cancelAnimationFrame(frameId); frameId = null; render(); }
    };
    const observer = new IntersectionObserver(([entry]) => { onScreen = entry.isIntersecting; sync(); });
    observer.observe(mount);
    document.addEventListener("visibilitychange", sync);
    motionQuery.addEventListener("change", sync);
    render();
    sync();

    stateRef.current = { ...stateRef.current, renderer, group, overlayGroup, render, repaint };

    return () => {
      cancelled = true;
      if (frameId != null) cancelAnimationFrame(frameId);
      observer.disconnect();
      document.removeEventListener("visibilitychange", sync);
      motionQuery.removeEventListener("change", sync);
      buildOverlay(overlayGroup, null);
      renderer.dispose();
      sphere.geometry.dispose();
      sphere.material.dispose();
      rim.geometry.dispose(); rim.material.dispose();
      atmosphere.geometry.dispose(); atmosphere.material.dispose();
      texture.dispose();
      // dispose() alone leaves the WebGL context lingering until GC; this component mounts on every route alongside a
      // production Globe, so the same zombie-context ceiling applies here.
      try { renderer.forceContextLoss(); } catch { /* context already lost */ }
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      stateRef.current = {};
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [size]);

  // Overlay and theme changes reuse the existing renderer (no new context, no new loop). A new principal is turned to
  // face the viewer so the selection is visible at once, including under reduced motion.
  const overlayKey = overlay?.key || null;
  useEffect(() => {
    const { group, overlayGroup, render, repaint } = stateRef.current;
    if (!overlayGroup) return;
    stateRef.current.territories = overlay?.territories || [];
    buildOverlay(overlayGroup, overlay);
    const principal = overlay?.focus || overlay?.markers.find((m) => m.principal);
    if (principal) {
      const p = surfacePoint(principal.lat, principal.lng);
      group.rotation.y = -Math.atan2(p.x, p.z);
      // Tilt toward the principal's latitude (bounded) so a high-latitude territory is not left on the limb.
      group.rotation.x = Math.max(-0.6, Math.min(0.6, (principal.lat * Math.PI) / 180 * 0.8));
    } else {
      group.rotation.x = -0.22;
    }
    if (repaint) repaint(); else render();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [overlayKey, failed, themeKey]);

  const theme = themeKey === "night" ? GLOBE_THEME.night : GLOBE_THEME.day;
  // The Globe's stage: near-black navy with the localized maritime bloom directly behind the sphere.
  const stage = {
    width: size, height: size, borderRadius: 14, overflow: "hidden",
    background: `radial-gradient(circle at 50% 50%, ${theme.bloom}e6 0%, ${theme.bloom}66 36%, ${theme.backdrop[0]} 74%)`,
    boxShadow: "inset 0 0 0 0.5px rgba(244, 236, 217, 0.12)",
  };

  // Same static CSS fallback Globe3D.jsx uses when WebGL is unavailable.
  if (failed) {
    return (
      <div className="globe-canvas globe-static" style={{ width: size, height: size }} role="img" aria-label="CineGlobe">
        <div className="globe-static-sphere" />
      </div>
    );
  }

  return (
    <div
      ref={mountRef}
      className={`compact-sidebar-globe ${className}`.trim()}
      style={stage}
      role="img"
      aria-label={overlay ? (overlay.portfolio ? "CineGlobe: the active portfolio" : "CineGlobe: this project's leading structure") : "CineGlobe"}
      data-principal={overlay?.markers.find((m) => m.principal)?.code || ""}
      data-projects={overlay?.portfolio ? new Set(overlay.markers.map((m) => m.projectId)).size : ""}
      data-participants={overlay ? overlay.markers.map((m) => m.code).join(",") : ""}
      data-routes={overlay ? overlay.routes.length : 0}
    />
  );
}
