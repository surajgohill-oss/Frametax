import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

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
const COMPACT_OCEAN_DIFFUSE = "#221c14"; // baked into the texture; non-zero
// so the lit hemisphere still shows a subtle gradient, not a flat hole.
const COMPACT_OCEAN_EMISSIVE = "#161208"; // guaranteed floor brightness, same
// technique as the production ocean fix — a lit sphere's diffuse base alone
// cannot exceed itself in brightness, so emissive carries the "not black"
// floor here too.
const COMPACT_LAND = "#8f7b57"; // warm brass/ivory, muted for small-size legibility

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

function drawPolygon(ctx, rings, w, h) {
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

/**
 * Fully decoupled compact brand-mark globe for the sidebar identity slot.
 * NOT the production Globe engine: no three-globe, no polygon/point/arc
 * layers, no CSS2D hit targets, no click/hover handlers, no Inspector
 * awareness, no Admin-1 detail. A lightweight lit sphere with a baked
 * continent-silhouette texture — visually stable at 80px, meant to read as
 * a premium engraved emblem rather than an interactive instrument.
 */
export default function CompactSidebarGlobe({ size = 80, className = "" }) {
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

    // Same warm key/fill pairing family as the production rig, but its own
    // instances — never the same THREE.Light objects, never mutated by
    // Globe3D.jsx's selection/status effects.
    scene.add(new THREE.AmbientLight(0x332b22, 0.8));
    const key = new THREE.DirectionalLight(0xf2ead9, 1.0);
    key.position.set(2, 1.4, 2);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x8a7860, 0.35);
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
        specular: new THREE.Color("#2c2318"),
      }),
    );
    group.add(sphere);

    let cancelled = false;
    getBakedLandCanvas().then((canvas) => {
      if (cancelled) return;
      const texture = new THREE.CanvasTexture(canvas);
      sphere.material.map = texture;
      sphere.material.needsUpdate = true;
      stateRef.current.texture = texture;
    });

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let frameId;
    const animate = () => {
      if (!prefersReducedMotion) group.rotation.y += 0.0022;
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();

    stateRef.current.renderer = renderer;

    return () => {
      cancelled = true;
      cancelAnimationFrame(frameId);
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
      aria-label="CineGlobe"
    />
  );
}
