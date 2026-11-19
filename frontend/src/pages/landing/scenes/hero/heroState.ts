/**
 * Scroll progress of the pinned hero, 0 to 1. The GSAP timeline writes it, the WebGL scene
 * reads it every frame, so the 3D camera and the DOM overlays scrub on the same clock.
 */
export const heroState = {
  progress: 0,
  /**
   * 0 = the dots lie flat as a world map, 1 = they have curled up into the globe. The canvas plays
   * this on load; the default of 1 is for anything that renders without that intro.
   */
  morph: 1,
};

export function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

export function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
