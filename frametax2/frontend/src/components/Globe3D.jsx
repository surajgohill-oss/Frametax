import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { CSS2DRenderer } from "three/examples/jsm/renderers/CSS2DRenderer.js";
import ThreeGlobe from "three-globe";

const TIER_HEX = {
  gold: "#d8b569",
  jade: "#7fae94",
  silver: "#9aa2ab",
  amber: "#c99a4d",
  red: "#b8654f",
  charcoal: "#4c483f",
};

/**
 * A reusable "Luxury Glass Globe" instance — smoked-obsidian material
 * sphere (no satellite texture, no topographic realism, per spec),
 * warm key light + cool silver fill, restrained fresnel rim. Points and
 * arcs are supplied by the caller (Company Globe passes one Little
 * Utopia marker; Production Globe passes the composed candidates'
 * jurisdictions) — this component owns no business logic, only render.
 */
export default function Globe3D({ points = [], arcs = [], onPointClick, onPointHover, height = 520 }) {
  const mountRef = useRef(null);
  const globeRef = useRef(null);
  const stateRef = useRef({});

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    // clientWidth can read 0/incorrect on first paint inside a flex/grid
    // parent whose own size isn't settled yet — fall back to the mount's
    // own parent width, and let the ResizeObserver below correct it the
    // instant real layout is available.
    const width = mount.clientWidth || mount.parentElement?.clientWidth || 600;
    const h = height;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#14120f");

    const camera = new THREE.PerspectiveCamera(50, width / h, 0.1, 2000);
    camera.position.set(0, 0, 340);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, h);
    mount.innerHTML = "";
    mount.style.position = "relative";
    mount.appendChild(renderer.domElement);

    // CSS2DRenderer: three-globe's htmlElementsData layer (used for
    // click/hover hit-targets — the WebGL Points layer has no callback
    // of its own) renders via CSS2DObject, which requires this second
    // renderer overlaid on the WebGL canvas.
    const cssRenderer = new CSS2DRenderer();
    cssRenderer.setSize(width, h);
    cssRenderer.domElement.style.position = "absolute";
    cssRenderer.domElement.style.top = "0";
    cssRenderer.domElement.style.left = "0";
    cssRenderer.domElement.style.pointerEvents = "none";
    mount.appendChild(cssRenderer.domElement);

    // Lighting: warm key + cool silver fill, per spec.
    scene.add(new THREE.AmbientLight(0x3a352c, 0.9));
    const key = new THREE.DirectionalLight(0xd8b569, 1.1);
    key.position.set(200, 120, 200);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x9aa2ab, 0.55);
    fill.position.set(-200, -80, -150);
    scene.add(fill);

    const globe = new ThreeGlobe()
      .showGlobe(true)
      .showAtmosphere(true)
      .atmosphereColor("#c9b98a")
      .atmosphereAltitude(0.12)
      .pointsData(points)
      .pointLat("lat")
      .pointLng("lng")
      .pointColor((d) => TIER_HEX[d.tier] || TIER_HEX.charcoal)
      .pointAltitude(0.015)
      .pointRadius((d) => (d.tier === "gold" ? 0.55 : 0.4))
      .pointResolution(24)
      .arcsData(arcs)
      .arcColor((d) => TIER_HEX[d.tier] || TIER_HEX.silver)
      .arcAltitude(0.25)
      .arcStroke(0.35)
      .arcDashLength(0.6)
      .arcDashGap(0.3)
      .arcDashAnimateTime(3000)
      // three-globe's Points layer (WebGL) has no click/hover callback —
      // interaction is handled via a matching HTML-elements layer of
      // invisible hit-targets, positioned by three-globe's own lat/lng
      // projection, using plain DOM events (pixel-accurate, no raycasting).
      .htmlElementsData(points)
      .htmlLat("lat")
      .htmlLng("lng")
      .htmlAltitude(0.02)
      .htmlElement((d) => {
        const el = document.createElement("div");
        el.className = "globe-hit-target";
        el.setAttribute("role", "button");
        el.setAttribute("tabindex", "0");
        el.setAttribute("aria-label", d.name || d.id || "jurisdiction marker");
        el.style.width = "28px";
        el.style.height = "28px";
        el.style.cursor = "pointer";
        el.style.pointerEvents = "auto";
        if (onPointClick) {
          el.addEventListener("click", (ev) => { ev.stopPropagation(); onPointClick(d); });
          el.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); onPointClick(d); } });
        }
        if (onPointHover) {
          el.addEventListener("mouseenter", () => onPointHover(d));
          el.addEventListener("mouseleave", () => onPointHover(null));
        }
        return el;
      });

    // Smoked-obsidian material — matte, no image texture, restrained sheen.
    const material = globe.globeMaterial();
    material.color = new THREE.Color("#1c1712");
    material.emissive = new THREE.Color("#0c0a08");
    material.shininess = 18;
    material.specular = new THREE.Color("#5a4f3a");

    scene.add(globe);
    globeRef.current = globe;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.4;
    // Idle rotation is the one intentional continuous motion this product
    // allows (Luxury Glass Globe ambience) — still gated behind the
    // user's reduced-motion preference, and slow/weighted rather than lively.
    controls.autoRotate = points.length <= 1 && !prefersReducedMotion;
    controls.autoRotateSpeed = 0.22;
    controls.minDistance = 180;
    controls.maxDistance = 560;
    controls.enablePan = false;

    let frameId;
    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      cssRenderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();

    const applySize = (w) => {
      if (!w) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      cssRenderer.setSize(w, h);
    };

    // ResizeObserver — the robust fix for canvases inside flex/grid
    // parents: fires the instant the container's real size is known,
    // not just on window resize (which never fires for layout-driven
    // sizing changes).
    const resizeObserver = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect?.width;
      if (w) applySize(Math.round(w));
    });
    resizeObserver.observe(mount);

    stateRef.current = { renderer, controls, frameId };

    return () => {
      cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      controls.dispose();
      renderer.dispose();
      // dispose() frees GPU resources but does NOT release the underlying
      // WebGL context — it lingers on the detached canvas until GC. With a
      // persistent sidebar globe plus route globes mounting/unmounting (and
      // StrictMode's dev double-mount), those zombie contexts accumulate
      // past the browser's hard ~16-context limit, after which every new
      // THREE.WebGLRenderer fails with "Error creating WebGL context".
      // forceContextLoss() releases the context immediately so it can't leak.
      try { renderer.forceContextLoss(); } catch { /* context already lost */ }
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      if (mount.contains(cssRenderer.domElement)) mount.removeChild(cssRenderer.domElement);
      globeRef.current = null;
      stateRef.current = {};
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update points/arcs on data change without re-mounting the whole scene.
  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.pointsData(points);
      globeRef.current.htmlElementsData(points);
      globeRef.current.arcsData(arcs);
    }
  }, [points, arcs]);

  return <div ref={mountRef} className="globe-canvas" style={{ height }} />;
}
