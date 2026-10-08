import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

// FROZEN (2026-07-28): this component's isolation from the production
// Globe engine is the whole point of it existing — do not import Globe3D
// or reuse its scene/material/lighting objects here for any reason. A
// future change to this file requires the user to explicitly unlock this
// subsystem first. (Unlocked 2026-10-08 by the user for the leading-structure
// overlay, offscreen pause and reduced-motion handling only.)
//
// Deliberately duplicated rather than imported from Globe3D.jsx — this
// component must never share a scene-light or material mutation path with
// the production Globe (2026-07-28 isolated material-correction pass,
// Section 1: "no shared scene-light mutations with the production Globe").
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

// Own small palette, tuned for legibility at 80px rather than reusing the
// production Globe's constants — a plain flat landmass silhouette with no
// internal borders reads as "noisy" at production hues/scale, so this is
// intentionally simpler and slightly higher-contrast.
// Smoked dark GLASS, not brown. The previous trio (#221c14 / #161208 /
// #8f7b57) was warm all the way through, which is why the emblem rendered as
// a muddy brown ball with beige smears instead of a premium mark.
// Note the narrower R->B spread than the production ocean: a small element
// reads its hue as MORE saturated than a large one, so the same slate that
// looks correctly neutral at 560px reads as navy at 80px.
const COMPACT_OCEAN_DIFFUSE = "#333940"; // baked into the texture; non-zero
// so the lit hemisphere still shows a subtle gradient, not a flat hole.
const COMPACT_OCEAN_EMISSIVE = "#22262b"; // guaranteed floor brightness, same
// technique as the production ocean fix — a lit sphere's diffuse base alone
// cannot exceed itself in brightness, so emissive carries the "not black"
// floor here too.
// The ONE warm element, and deliberately so: the brand mark's continents are
// its ivory/brass signature against the smoked sphere. Brighter than the old
// value because at 80px the landmass needs real contrast to read as
// geography rather than as noise.
const COMPACT_LAND = "#cbb692";

// At 80px, small islands and archipelagos degenerate into single stray
// pixels — the "beige fragments floating without recognizable geography"
// failure. Rings whose projected bounding box is smaller than this fraction
// of the texture are dropped, leaving only the major landmasses that
// actually read as Earth at emblem scale. This is the geometry-complexity
// reduction the compact component is supposed to own.
const MIN_RING_EXTENT_FRAC = 0.018;

function projectPoint(lon, lat, w, h) {
  return [((lon + 180) / 360) * w, ((90 - lat) / 180) * h];
}

// Breaks the path at antimeridian-crossing jumps instead of drawing a
// spurious horizontal streak across the whole texture (a handful of Natural
// Earth features, e.g. Russia/Fiji, cross ±180°).
function drawRing(ctx, ring, w, h) {
  let started = false;
  let prevLon = null;
  for (const pt of ring) {
    const [lon, lat] = pt;
    const [x, y] = projectPoint(lon, lat, w, h);
    if (!started) { ctx.moveTo(x, y); started = true; }
    else if (prevLon != null && Math.abs(lon - prevLon) > 180) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
    prevLon = lon;
  }
  ctx.closePath();
}

// True when a ring is large enough to be worth drawing at emblem scale.
// Measured on the ring's own lon/lat bounding box so it is independent of
// texture resolution.
function ringIsSignificant(ring) {
  let minLon = Infinity, maxLon = -Infinity, minLat = Infinity, maxLat = -Infinity;
  for (const [lon, lat] of ring) {
    if (lon < minLon) minLon = lon;
    if (lon > maxLon) maxLon = lon;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
  }
  return (maxLon - minLon) / 360 > MIN_RING_EXTENT_FRAC
    || (maxLat - minLat) / 180 > MIN_RING_EXTENT_FRAC;
}

function drawPolygon(ctx, rings, w, h) {
  // rings[0] is the outer ring; if the landmass itself is too small to read
  // at 80px, skip the whole polygon (holes included) rather than drawing a
  // speck.
  if (!rings.length || !ringIsSignificant(rings[0])) return;
  ctx.beginPath();
  for (const ring of rings) drawRing(ctx, ring, w, h);
  ctx.fill("evenodd");
}

// Bakes plain country silhouettes — no admin-1 detail, no border strokes,
// one flat landmass fill — into a single equirectangular canvas texture,
// once per page session. This is the "generated emblem derived from
// existing geography" approach: no static raster asset, no three-globe
// polygon layer, no per-country material cost at 80px. Independently
// fetched from the same public geo file Globe3D.jsx uses, but with its own
// promise/cache so the two components never share load state.
let bakedLandPromise = null;
function getBakedLandCanvas() {
  if (!bakedLandPromise) {
    bakedLandPromise = fetch("/geo/world-110m.geojson")
      .then((r) => (r.ok ? r.json() : { features: [] }))
      .catch(() => ({ features: [] }))
      .then((geo) => {
        const w = 1024, h = 512;
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = COMPACT_OCEAN_DIFFUSE;
        ctx.fillRect(0, 0, w, h);
        ctx.fillStyle = COMPACT_LAND;
        for (const feat of geo.features || []) {
          const geom = feat.geometry;
          if (!geom) continue;
          if (geom.type === "Polygon") drawPolygon(ctx, geom.coordinates, w, h);
          else if (geom.type === "MultiPolygon") for (const poly of geom.coordinates) drawPolygon(ctx, poly, w, h);
        }
        return canvas;
      });
  }
  return bakedLandPromise;
}

// Overlay colours: the principal reads as the leading jurisdiction (warm gold), the other participants and routes as
// a quiet ivory -- both well above the smoked ocean and the brass land at 80px.
const OVERLAY_PRINCIPAL = "#ffd980";
const OVERLAY_SECONDARY = "#eef2f6";
const OVERLAY_ROUTE = "#f3ead6";

// Same equirectangular mapping SphereGeometry uses for its UVs (u = (lon + 180) / 360), so markers sit exactly on the
// baked texture's geography.
function surfacePoint(lat, lng, r = 1) {
  const phi = ((lng + 180) * Math.PI) / 180;
  const theta = ((90 - lat) * Math.PI) / 180;
  return new THREE.Vector3(-r * Math.cos(phi) * Math.sin(theta), r * Math.cos(theta), r * Math.sin(phi) * Math.sin(theta));
}

// Rebuilds the overlay group's children from { markers, routes }. Arcs stay below radius 1.07 so nothing reaches the
// canvas edge (the camera frames radius ~1.1).
function buildOverlay(group, overlay) {
  for (const child of [...group.children]) {
    group.remove(child);
    child.geometry?.dispose();
    child.material?.dispose();
  }
  if (!overlay) return;
  for (const r of overlay.routes) {
    const a = surfacePoint(r.from.lat, r.from.lng, 1.005);
    const b = surfacePoint(r.to.lat, r.to.lng, 1.005);
    const lift = Math.min(1.07, 1.01 + a.distanceTo(b) * 0.05);
    const mid = a.clone().add(b).normalize().multiplyScalar(lift);
    const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
    group.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(curve.getPoints(24)),
      new THREE.LineBasicMaterial({ color: OVERLAY_ROUTE, transparent: true, opacity: 0.9 }),
    ));
  }
  for (const m of overlay.markers) {
    const dot = new THREE.Mesh(
      new THREE.SphereGeometry(m.principal ? 0.055 : 0.036, 12, 12),
      new THREE.MeshBasicMaterial({ color: m.principal ? OVERLAY_PRINCIPAL : OVERLAY_SECONDARY }),
    );
    dot.position.copy(surfacePoint(m.lat, m.lng, 1.01));
    group.add(dot);
  }
}

/**
 * Fully decoupled compact brand-mark globe for the sidebar identity slot.
 * NOT the production Globe engine: no three-globe, no polygon/point/arc
 * layers, no CSS2D hit targets, no click/hover handlers, no Inspector
 * awareness, no Admin-1 detail. A lightweight lit sphere with a baked
 * continent-silhouette texture -- visually stable at 80px. On a project
 * route it also carries a simplified overlay of that project's leading
 * structure (`overlay` from lib/globeStructure.js::miniGlobeOverlay):
 * principal marker, participant markers and route lines; null keeps the
 * neutral emblem (company routes, submitted projects).
 *
 * One render loop only, and only while it is useful: it runs while the
 * emblem is on screen, the tab is visible and reduced motion is off;
 * otherwise frames are drawn on demand (texture load, overlay change).
 */
export default function CompactSidebarGlobe({ size = 80, className = "", overlay = null }) {
  const mountRef = useRef(null);
  const stateRef = useRef({});
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    if (!webglAvailable()) { setFailed(true); return; }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    // d = R / tan(fov/2) with a small margin, so the full circle sits
    // centered with no bottom/edge clipping at any renderer size.
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

    // Neutral white, for the same reason as the production rig: tinted lights
    // multiply against every material and were a primary cause of this
    // emblem reading as a brown ball. Its own THREE.Light instances — never
    // shared with, or mutated by, Globe3D.jsx.
    scene.add(new THREE.AmbientLight(0xffffff, 0.88));
    const key = new THREE.DirectionalLight(0xffffff, 0.62);
    key.position.set(2, 1.4, 2);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x8890a0, 0.20);
    fill.position.set(-2, -0.8, -1.5);
    scene.add(fill);

    const group = new THREE.Group();
    // A gentle fixed axial tilt so the emblem reads as a sphere even at
    // rest, before any rotation has happened.
    group.rotation.x = -0.22;
    scene.add(group);

    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(1, 48, 48),
      new THREE.MeshPhongMaterial({
        color: 0xffffff,
        emissive: new THREE.Color(COMPACT_OCEAN_EMISSIVE),
        shininess: 42,
        specular: new THREE.Color("#232a33"),
      }),
    );
    group.add(sphere);
    const overlayGroup = new THREE.Group();
    group.add(overlayGroup);

    const render = () => renderer.render(scene, camera);

    let cancelled = false;
    getBakedLandCanvas().then((canvas) => {
      if (cancelled) return;
      const texture = new THREE.CanvasTexture(canvas);
      // The canvas is authored in sRGB; without this the map is sampled as
      // linear and the continents render washed out and desaturated.
      texture.colorSpace = THREE.SRGBColorSpace;
      // The emblem is only 80px but the texture is 1024px wide, so it is
      // heavily minified at a grazing angle near the limb — anisotropy is
      // what keeps the coastlines from shimmering into mush as it rotates.
      texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
      sphere.material.map = texture;
      sphere.material.needsUpdate = true;
      stateRef.current.texture = texture;
      render();
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

    stateRef.current = { ...stateRef.current, renderer, group, overlayGroup, render };

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
      stateRef.current.texture?.dispose();
      // See Globe3D.jsx's identical cleanup note — dispose() alone leaves
      // the WebGL context lingering until GC, and this component mounts on
      // every route alongside a production Globe, so the same zombie-
      // context ceiling applies here.
      try { renderer.forceContextLoss(); } catch { /* context already lost */ }
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      stateRef.current = {};
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [size]);

  // Overlay changes reuse the existing renderer (no new context, no new loop). A new principal is turned to face the
  // viewer so the selection is visible at once, including under reduced motion.
  const overlayKey = overlay?.key || null;
  useEffect(() => {
    const { group, overlayGroup, render } = stateRef.current;
    if (!overlayGroup) return;
    buildOverlay(overlayGroup, overlay);
    const principal = overlay?.markers.find((m) => m.principal);
    if (principal) {
      const p = surfacePoint(principal.lat, principal.lng);
      group.rotation.y = -Math.atan2(p.x, p.z);
      // Tilt toward the principal's latitude (bounded) so a high-latitude territory is not left on the limb.
      group.rotation.x = Math.max(-0.6, Math.min(0.6, (principal.lat * Math.PI) / 180 * 0.8));
    } else {
      group.rotation.x = -0.22;
    }
    render();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [overlayKey, failed]);

  // Same static CSS fallback Globe3D.jsx uses when WebGL is unavailable —
  // no new raster asset introduced.
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
      style={{ width: size, height: size }}
      role="img"
      aria-label={overlay ? "CineGlobe: this project's leading structure" : "CineGlobe"}
      data-principal={overlay?.markers.find((m) => m.principal)?.code || ""}
      data-participants={overlay ? overlay.markers.map((m) => m.code).join(",") : ""}
      data-routes={overlay ? overlay.routes.length : 0}
    />
  );
}
