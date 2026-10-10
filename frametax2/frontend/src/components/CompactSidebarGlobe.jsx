import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { GLOBE_THEME } from "../lib/globeVisualTokens";
import marbleUrl from "../assets/earth/blue-marble-1024.jpg"; // NASA Blue Marble, see assets/earth/ATTRIBUTION.md

// The 80px sidebar globe is a DECORATIVE CineGlobe identity object -- brand, geography and atmosphere -- a restrained optical view of
// Earth: NASA Blue Marble imagery (bundled locally, 1024px; no remote imagery, no API key), a soft ocean specular response, a
// warm upper-left key light, a cool atmospheric limb, a separate translucent cloud shell drifting faster than the Earth turns,
// and a very slow rotation. It deliberately does NOT reproduce data layers (no boundaries, routes, labels or marker clusters;
// those belong to the Company and Project Globes). Project routes may add ONE extremely quiet glow at the principal.
//
// Independent of the heavyweight Globe3D engine. One renderer per mount; the decoded image and the derived ocean mask / cloud
// canvases are cached at module level, so a remount only uploads textures to its own context. Animation runs at ~30fps only
// while on screen, tab visible and reduced motion off; otherwise single frames are drawn on demand.
//
// FROZEN subsystem (2026-07-28), unlocked by the user 2026-10-08. Do not import Globe3D or share scene objects with it.
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

const themeOf = (key) => (key === "night" ? GLOBE_THEME.night : GLOBE_THEME.day);

// Decoded Blue Marble image + the ocean specular mask derived from it (blue-dominant pixels = water), cached per page session.
let marblePromise = null;
const loadMarble = () => {
  if (!marblePromise) {
    marblePromise = new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = 512; c.height = 256;
        const g = c.getContext("2d");
        g.drawImage(img, 0, 0, 512, 256);
        const d = g.getImageData(0, 0, 512, 256);
        for (let i = 0; i < d.data.length; i += 4) {
          const r = d.data[i]; const gg = d.data[i + 1]; const b = d.data[i + 2];
          const ocean = b > r + 10 && b >= gg - 6 && r < 110;
          const v = ocean ? 255 : 0;
          d.data[i] = v; d.data[i + 1] = v; d.data[i + 2] = v; d.data[i + 3] = 255;
        }
        g.putImageData(d, 0, 0);
        resolve({ img, spec: c });
      };
      img.onerror = reject;
      img.src = marbleUrl;
    });
  }
  return marblePromise;
};

let cloudCanvas = null;
// Fibrous satellite cloud deck: hundreds of fine strokes along the ITCZ and the mid-latitude storm tracks, a tight Southern Ocean
// vortex, and a clear Sahara. Seeded, so every load draws the same sky.
function bakeClouds() {
  if (cloudCanvas) return cloudCanvas;
  let seed = 20260705;
  const rand = () => { seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const c = document.createElement("canvas");
  c.width = 512; c.height = 256;
  const ctx = c.getContext("2d");
  // Opaque black ground, white clouds: the canvas is used as an ALPHA map (grey level = cloud density). An RGBA texture with
  // transparent-black texels filters toward black at every cloud edge, which is what drew the dark halo around the clouds.
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, 512, 256);

  // Cloud systems: 22 masses at random places along the weather belts (random belt, random longitude, random size, shape, tilt and
  // density), so the deck reads as weather rather than a pattern. No soft base under them (it read as a haze); the strokes are the cloud.
  const bandY = [120, 180, 65, 150, 95];
  const gauss = () => (rand() + rand() + rand() - 1.5) / 1.5;
  const centers = [];
  for (let attempts = 0; centers.length < 22 && attempts < 400; attempts += 1) {
    const cy = bandY[Math.floor(rand() * bandY.length)] + (rand() - 0.5) * 44;
    const cx = rand() * 512;
    if (cx > 205 && cx < 295 && cy > 70 && cy < 135) continue; // Sahara stays visible
    if (centers.some(([x, y]) => Math.hypot(x - cx, (y - cy) * 1.6) < 26)) continue;
    centers.push([cx, cy]);
  }
  centers.forEach(([cx, cy]) => {
    const rad = 10 + rand() * 24;
    const tilt = (rand() - 0.5) * 0.6;
    const squash = 0.35 + rand() * 0.5;
    const count = 14 + Math.floor(rand() * 26);
    for (let i = 0; i < count; i += 1) {
      const gx = gauss() * rad * 1.5;
      const gy = gauss() * rad * squash;
      ctx.save();
      ctx.translate(cx + gx * Math.cos(tilt) - gy * Math.sin(tilt), cy + gx * Math.sin(tilt) + gy * Math.cos(tilt));
      ctx.rotate(tilt + (rand() - 0.5) * 0.6);
      ctx.fillStyle = `rgba(255, 255, 255, ${0.4 + rand() * 0.5})`;
      ctx.beginPath();
      ctx.ellipse(0, 0, 2.5 + rand() * 8, 1 + rand() * 2.8, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  });

  ctx.save();
  ctx.translate(270, 205);
  for (let a = 0; a < Math.PI * 4; a += 0.08) {
    const r = a * 3.2;
    ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0, 0.75 - a * 0.06)})`;
    ctx.beginPath();
    ctx.arc(Math.cos(a) * r, Math.sin(a) * r * 0.5, 0.9 + rand() * 1.1, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
  cloudCanvas = c;
  return c;
}

// Positive x tilts the north pole toward the camera, so North America sits across the middle of the disk.
const BASE_TILT = 0.55;

// Same equirectangular mapping SphereGeometry uses for its UVs (u = (lon + 180) / 360).
function surfacePoint(lat, lng, r = 1) {
  const phi = ((lng + 180) * Math.PI) / 180;
  const theta = ((90 - lat) * Math.PI) / 180;
  return new THREE.Vector3(-r * Math.cos(phi) * Math.sin(theta), r * Math.cos(theta), r * Math.sin(phi) * Math.sin(theta));
}

/**
 * Decorative identity globe. `overlay` is { key, focus?: {lat,lng}, pulse?: {lat,lng,color}, accent?: hex }:
 *   - company routes pass { accent } (aggregate stage colour, tinting only the atmosphere);
 *   - project routes pass { focus, pulse } (turn to the principal, one quiet glow there);
 *   - null keeps the plain Earth.
 */
export default function CompactSidebarGlobe({ size = 80, className = "", overlay = null }) {
  const mountRef = useRef(null);
  const stateRef = useRef({});
  const [failed, setFailed] = useState(false);
  const [themeKey, setThemeKey] = useState(() => document.documentElement.getAttribute("data-theme") || "day");

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
    camera.position.set(0, 0, 2.58); // the planet slightly overfills the circle, so no sliver of backdrop shows at the rim

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      setFailed(true);
      return;
    }
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(size, size);
    mount.innerHTML = "";
    mount.appendChild(renderer.domElement);

    // Warm upper-left key, cool lower-right fill. Its own lights, never shared with Globe3D.
    const ambient = new THREE.AmbientLight(0xffffff, 1.3);
    scene.add(ambient);
    const key = new THREE.DirectionalLight(0xffffff, 1.8);
    key.position.set(0.1, 0.2, 4.0);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x6f96c0, 0.28);
    fill.position.set(2.2, -1.2, -1.2);
    scene.add(fill);

    const group = new THREE.Group();
    group.rotation.x = BASE_TILT;
    { const face = surfacePoint(40, -98); group.rotation.y = -Math.atan2(face.x, face.z); } // opens on North America
    scene.add(group);
    const earth = new THREE.Mesh(
      new THREE.SphereGeometry(1, 56, 56),
      new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.85, metalness: 0, emissive: new THREE.Color(0x1655a0), emissiveIntensity: 0.35 }),
    );
    group.add(earth);
    const clouds = new THREE.Mesh(
      new THREE.SphereGeometry(1.004, 48, 48),
      new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: 0.8, depthWrite: false, emissive: new THREE.Color(0x333333) }),
    );
    group.add(clouds);
    const glow = new THREE.Mesh(
      new THREE.SphereGeometry(0.04, 16, 16),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.3, blending: THREE.AdditiveBlending, depthWrite: false }),
    );
    glow.visible = false;
    group.add(glow);

    const cloudTex = new THREE.CanvasTexture(bakeClouds());
    clouds.material.alphaMap = cloudTex;
    clouds.material.needsUpdate = true;
    let earthTex = null;
    const render = () => renderer.render(scene, camera);
    let cancelled = false;

    // Theme: light levels and a slightly cooler Earth at night. The Earth/ocean-mask textures are uploaded ONCE per
    // mount (when the cached image resolves); a theme or overlay change never re-uploads or re-bakes anything.
    const applyTheme = () => {
      const night = document.documentElement.getAttribute("data-theme") === "night";
      ambient.intensity = night ? 0.7 : 1.3;
      key.intensity = night ? 0.9 : 1.8;
      earth.material.color.set(night ? "#c9d6ea" : "#ffffff");
      render();
    };
    loadMarble().then(({ img }) => {
      if (cancelled) return;
      earthTex = new THREE.Texture(img);
      earthTex.colorSpace = THREE.SRGBColorSpace;
      earthTex.anisotropy = renderer.capabilities.getMaxAnisotropy();
      earthTex.needsUpdate = true;
      earth.material.map = earthTex;
      earth.material.needsUpdate = true;
      render();
    }).catch(() => { /* imagery unavailable: the plain lit sphere stays, nothing else breaks */ });

    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    let onScreen = true;
    let frameId = null;
    let last = 0;
    const loop = (now) => {
      frameId = requestAnimationFrame(loop);
      if (now - last < 33) return; // ~30fps is plenty at 80px
      const dt = last ? Math.min(100, now - last) : 33;
      last = now;
      group.rotation.y += 0.0000524 * dt;         // one full turn of the Earth in ~2 minutes (speed LOCKED by the user, 2026-10-10)
      clouds.rotation.y += 0.00002 * dt;           // the cloud deck drifts ahead of the Earth (on-screen ~0.0000724/ms, about a 1.4 min lap; LOCKED 2026-10-10)
      key.position.x = 0.1 + Math.sin(now / 9000) * 0.28; // slow light response across the ocean specular
      key.position.y = 0.2 + Math.cos(now / 11000) * 0.12;
      if (glow.visible) {
        const p = 0.5 + 0.5 * Math.sin(now / 1500);
        glow.scale.setScalar(1 + 0.3 * p);
        glow.material.opacity = 0.3 - 0.16 * p;
      }
      render();
    };
    const sync = () => {
      const animate = onScreen && !document.hidden && !motionQuery.matches;
      if (animate && frameId == null) { last = 0; frameId = requestAnimationFrame(loop); }
      if (!animate && frameId != null) { cancelAnimationFrame(frameId); frameId = null; render(); }
    };
    const observer = new IntersectionObserver(([entry]) => { onScreen = entry.isIntersecting; sync(); });
    observer.observe(mount);
    document.addEventListener("visibilitychange", sync);
    motionQuery.addEventListener("change", sync);
    render();
    sync();

    stateRef.current = { ...stateRef.current, renderer, group, glow, render, applyTheme };

    return () => {
      cancelled = true;
      if (frameId != null) cancelAnimationFrame(frameId);
      observer.disconnect();
      document.removeEventListener("visibilitychange", sync);
      motionQuery.removeEventListener("change", sync);
      renderer.dispose();
      for (const m of [earth, clouds, glow]) { m.geometry.dispose(); m.material.dispose(); }
      earthTex?.dispose(); cloudTex.dispose();
      // dispose() alone leaves the WebGL context lingering until GC; this mounts on every route alongside a production Globe.
      try { renderer.forceContextLoss(); } catch { /* context already lost */ }
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      stateRef.current = {};
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [size]);

  // Overlay and theme changes reuse the renderer (no new context or loop). A project's principal is turned to face the viewer
  // so the selection is visible at once, including under reduced motion.
  const overlayKey = overlay?.key || null;
  useEffect(() => {
    const { group, glow, render, applyTheme } = stateRef.current;
    if (!group) return;
    stateRef.current.accent = overlay?.accent || null;
    const f = overlay?.focus;
    if (f) {
      const p = surfacePoint(f.lat, f.lng);
      group.rotation.y = -Math.atan2(p.x, p.z);
      group.rotation.x = Math.max(-0.6, Math.min(0.6, (f.lat * Math.PI) / 180 * 0.8));
    } else {
      group.rotation.x = BASE_TILT;
    }
    if (overlay?.pulse) {
      glow.position.copy(surfacePoint(overlay.pulse.lat, overlay.pulse.lng, 1.02));
      glow.material.color.set(overlay.pulse.color || "#ffffff");
      glow.visible = true;
    } else {
      glow.visible = false;
    }
    applyTheme();
    render();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [overlayKey, failed, themeKey]);

  const theme = themeOf(themeKey);
  // The brand stage: near-black navy with the localized maritime bloom directly behind the sphere.
  const accentRim = /^#[0-9a-f]{6}$/i.test(overlay?.accent || "") ? `${overlay.accent}55` : "rgba(50, 130, 240, 0.22)";
  // The clipped inner stage keeps the planet's edge razor-clean; the glow, edge shade and stage tint live on the unclipped frame
  // and on a non-interactive overlay above the canvas, so the sphere sits in the rail instead of reading as a cut-out.
  const frame = {
    width: size, height: size, position: "relative", boxSizing: "border-box", borderRadius: "50%",
    border: "1px solid rgba(255, 255, 255, 0.03)",
    boxShadow: "0 0 28px rgba(30, 90, 160, 0.18)",
  };
  const stage = {
    position: "absolute", inset: 0, borderRadius: "50%", overflow: "hidden",
    // A vector circle mask, its own stacking context and a GPU layer: the planet meets the sidebar with a clean edge.
    clipPath: "circle(50% at 50% 50%)", WebkitClipPath: "circle(50% at 50% 50%)", isolation: "isolate", transform: "translateZ(0)",
    background: `radial-gradient(circle at 50% 50%, ${theme.bloom}e6 0%, ${theme.bloom}66 36%, ${theme.backdrop[0]} 74%)`,
  };
  const edge = {
    position: "absolute", inset: 0, borderRadius: "50%", pointerEvents: "none",
    boxShadow: `inset 0 0 16px rgba(0, 0, 0, 0.7), inset 0 0 8px ${accentRim}`,
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
      className={`compact-sidebar-globe ${className}`.trim()}
      style={frame}
      role="img"
      aria-label={overlay?.portfolio ? "CineGlobe: the active portfolio" : overlay?.pulse ? "CineGlobe: this project's location" : "CineGlobe"}
      data-principal={overlay?.principalCode || ""}
      data-projects={overlay?.portfolio ? overlay.projects : ""}
      data-accent={overlay?.accent || ""}
    >
      <div ref={mountRef} style={stage} />
      <div style={edge} />
    </div>
  );
}
