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

// ── procedural tonal variation (tileable in longitude) ──────────────────────────────────────────
const hash = (x, y) => { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); };
function valueNoise(u, v, cellsX, cellsY) {
  const x = u * cellsX; const y = v * cellsY;
  const x0 = Math.floor(x); const y0 = Math.floor(y);
  const fx = x - x0; const fy = y - y0;
  const sx = fx * fx * (3 - 2 * fx); const sy = fy * fy * (3 - 2 * fy);
  const xa = ((x0 % cellsX) + cellsX) % cellsX; const xb = (xa + 1) % cellsX;
  const a = hash(xa, y0); const b = hash(xb, y0); const c = hash(xa, y0 + 1); const d = hash(xb, y0 + 1);
  return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy;
}
const fbm = (u, v, cx, cy, octaves) => {
  let amp = 0.5; let sum = 0; let norm = 0;
  for (let o = 0; o < octaves; o += 1) {
    sum += amp * valueNoise(u, v, cx * 2 ** o, cy * 2 ** o);
    norm += amp; amp *= 0.5;
  }
  return sum / norm;
};

const mix = (a, b, t) => {
  const A = parseInt(a.slice(1), 16); const B = parseInt(b.slice(1), 16);
  const ch = (i) => Math.round(((A >> i) & 255) + (((B >> i) & 255) - ((A >> i) & 255)) * t).toString(16).padStart(2, "0");
  return `#${ch(16)}${ch(8)}${ch(0)}`;
};

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
function bakeClouds() {
  if (cloudCanvas) return cloudCanvas;
  const w = 512; const h = 256;
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const g = c.getContext("2d");
  const img = g.createImageData(w, h);
  for (let y = 0; y < h; y += 1) {
    const lat = (0.5 - y / h) * Math.PI; // more cover in the mid-latitude bands and the ITCZ, less over the subtropics
    const band = 0.55 + 0.45 * Math.cos(lat * 3.0 + 0.4) ** 2;
    for (let x = 0; x < w; x += 1) {
      const n = fbm(x / w, y / h, 5, 3, 5);
      const a = Math.max(0, Math.min(1, (n * band - 0.44) / 0.2));
      const i = (y * w + x) * 4;
      img.data[i] = 255; img.data[i + 1] = 255; img.data[i + 2] = 255;
      img.data[i + 3] = Math.round(255 * a * a * (3 - 2 * a) * 0.6);
    }
  }
  g.putImageData(img, 0, 0);
  cloudCanvas = c;
  return c;
}

// Same equirectangular mapping SphereGeometry uses for its UVs (u = (lon + 180) / 360).
function surfacePoint(lat, lng, r = 1) {
  const phi = ((lng + 180) * Math.PI) / 180;
  const theta = ((90 - lat) * Math.PI) / 180;
  return new THREE.Vector3(-r * Math.cos(phi) * Math.sin(theta), r * Math.cos(theta), r * Math.sin(phi) * Math.sin(theta));
}

// Fresnel limb shell (additive, back faces): warm ivory toward the upper-left key light, cool maritime toward the lower right.
function limbShell(radius, cool, warm, power, intensity) {
  return new THREE.Mesh(
    new THREE.SphereGeometry(radius, 40, 40),
    new THREE.ShaderMaterial({
      uniforms: { uCool: { value: new THREE.Color(cool) }, uWarm: { value: new THREE.Color(warm) }, uPower: { value: power }, uIntensity: { value: intensity } },
      vertexShader: "varying vec3 vN; varying vec3 vV; void main(){ vN = normalize(normalMatrix * normal); vec4 mv = modelViewMatrix * vec4(position,1.0); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }",
      fragmentShader: "uniform vec3 uCool; uniform vec3 uWarm; uniform float uPower; uniform float uIntensity; varying vec3 vN; varying vec3 vV; void main(){ float f = pow(1.0 - abs(dot(vN, vV)), uPower); float w = smoothstep(-0.2, 0.8, dot(normalize(vN.xy + vec2(1e-4)), normalize(vec2(-0.62, 0.78)))); gl_FragColor = vec4(mix(uCool, uWarm, w), f * uIntensity); }",
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      transparent: true,
      depthWrite: false,
    }),
  );
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
    camera.position.set(0, 0, 2.85); // frames the whole circle, halo included, with a small margin

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

    // Warm upper-left key, cool lower-right fill. Its own lights, never shared with Globe3D.
    const ambient = new THREE.AmbientLight(0xffffff, 0.66);
    scene.add(ambient);
    const key = new THREE.DirectionalLight(0xfff0d8, 1.4);
    key.position.set(-2.2, 1.7, 2.2);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x6f96c0, 0.28);
    fill.position.set(2.2, -1.2, -1.2);
    scene.add(fill);

    const group = new THREE.Group();
    group.rotation.x = -0.28;
    scene.add(group);
    const earth = new THREE.Mesh(
      new THREE.SphereGeometry(1, 56, 56),
      new THREE.MeshPhongMaterial({ color: 0xffffff, shininess: 150, specular: new THREE.Color("#2b3d57"), emissive: new THREE.Color("#ffffff"), emissiveIntensity: 0.3 }),
    );
    group.add(earth);
    const clouds = new THREE.Mesh(
      new THREE.SphereGeometry(1.014, 48, 48),
      new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: 0.82, depthWrite: false }),
    );
    group.add(clouds);
    const glow = new THREE.Mesh(
      new THREE.SphereGeometry(0.04, 16, 16),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.3, blending: THREE.AdditiveBlending, depthWrite: false }),
    );
    glow.visible = false;
    group.add(glow);
    const t0 = themeOf(document.documentElement.getAttribute("data-theme"));
    const rim = limbShell(1.03, t0.rim, "#f4ead6", 3.4, 0.3);
    const halo = limbShell(1.11, t0.atmosphere, "#f4ead6", 4.6, 0.24);
    scene.add(rim);
    scene.add(halo);

    const cloudTex = new THREE.CanvasTexture(bakeClouds());
    cloudTex.colorSpace = THREE.SRGBColorSpace;
    clouds.material.map = cloudTex;
    let earthTex = null;
    let specTex = null;
    const render = () => renderer.render(scene, camera);
    let cancelled = false;

    // Theme: atmosphere tint, light levels and a slightly cooler Earth at night. The Earth/ocean-mask textures are uploaded ONCE per
    // mount (when the cached image resolves); a theme or overlay change never re-uploads or re-bakes anything.
    const applyTheme = () => {
      const night = document.documentElement.getAttribute("data-theme") === "night";
      const t = themeOf(night ? "night" : "day");
      rim.material.uniforms.uCool.value.set(t.rim);
      halo.material.uniforms.uCool.value.set(stateRef.current.accent ? mix(t.atmosphere, stateRef.current.accent, 0.4) : t.atmosphere);
      ambient.intensity = night ? 0.6 : 0.78;
      key.intensity = night ? 0.85 : 1.0;
      earth.material.color.set(night ? "#c9d6ea" : "#ffffff");
      render();
    };
    loadMarble().then(({ img, spec }) => {
      if (cancelled) return;
      earthTex = new THREE.Texture(img);
      earthTex.colorSpace = THREE.SRGBColorSpace;
      earthTex.anisotropy = renderer.capabilities.getMaxAnisotropy();
      earthTex.needsUpdate = true;
      specTex = new THREE.CanvasTexture(spec);
      earth.material.map = earthTex;
      earth.material.emissiveMap = earthTex; // self-lit floor so the ocean never collapses to black on the dark stage
      earth.material.specularMap = specTex;
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
      group.rotation.y += 0.000012 * dt;          // very slow turn of the Earth (~9 min per revolution)
      clouds.rotation.y += 0.00003 * dt;          // the cloud deck drifts ahead of it, independently (~3.5 min per lap)
      key.position.x = -2.2 + Math.sin(now / 9000) * 0.28; // slow light response across the ocean specular
      key.position.y = 1.7 + Math.cos(now / 11000) * 0.12;
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
      for (const m of [earth, clouds, glow, rim, halo]) { m.geometry.dispose(); m.material.dispose(); }
      earthTex?.dispose(); specTex?.dispose(); cloudTex.dispose();
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
      group.rotation.x = -0.28;
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
      aria-label={overlay?.portfolio ? "CineGlobe: the active portfolio" : overlay?.pulse ? "CineGlobe: this project's location" : "CineGlobe"}
      data-principal={overlay?.principalCode || ""}
      data-projects={overlay?.portfolio ? overlay.projects : ""}
      data-accent={overlay?.accent || ""}
    />
  );
}
