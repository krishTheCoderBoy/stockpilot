import { useSyncExternalStore } from "react";

// The full experience (pinned scenes, WebGL) needs a desktop-sized screen and a visitor who
// has not asked for reduced motion. Everything else gets the static layout.
const FULL_MOTION_QUERY = "(min-width: 768px) and (prefers-reduced-motion: no-preference)";

function subscribe(onChange: () => void): () => void {
  const query = window.matchMedia(FULL_MOTION_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/** True when scenes may pin, scrub and use WebGL. Re-evaluates when the window or setting changes. */
export function useFullMotion(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(FULL_MOTION_QUERY).matches,
    () => false
  );
}

let webglSupport: boolean | null = null;

/** Whether this browser can create a WebGL context (checked once). */
export function hasWebGL(): boolean {
  if (webglSupport === null) {
    try {
      const canvas = document.createElement("canvas");
      webglSupport = Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
    } catch {
      webglSupport = false;
    }
  }
  return webglSupport;
}
