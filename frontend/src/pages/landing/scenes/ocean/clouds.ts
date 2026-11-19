import cloud1 from "../../../../assets/landing/cloud-1.webp";
import cloud2 from "../../../../assets/landing/cloud-2.webp";
import cloud3 from "../../../../assets/landing/cloud-3.webp";
import cloud4 from "../../../../assets/landing/cloud-4.webp";

export interface Cloud {
  src: string;
  /** Position and width, as a percentage of the screen. */
  left: number;
  top: number;
  width: number;
  /** How fast this cloud drifts compared with the others (nearer clouds move more). */
  depth: number;
}

// Placeholder art: soft procedural puffs (cloud-1 to cloud-4.webp). Swap in photographed cloud cut-outs if you like.
export const CLOUDS: Cloud[] = [
  { src: cloud1, left: -12, top: -8, width: 62, depth: 1.0 },
  { src: cloud2, left: 46, top: -4, width: 56, depth: 0.7 },
  { src: cloud3, left: 8, top: 28, width: 70, depth: 1.25 },
  { src: cloud4, left: 56, top: 34, width: 62, depth: 0.9 },
  { src: cloud1, left: 22, top: 62, width: 76, depth: 1.4 },
  { src: cloud2, left: -8, top: 66, width: 52, depth: 0.8 },
  { src: cloud3, left: 60, top: 70, width: 58, depth: 1.1 },
];

/** Both scenes that show clouds call this with the same numbers at the hand-off, so the picture matches. */
export function applyClouds(root: HTMLElement | null, drift: number, alpha: number): void {
  if (!root) return;
  root.style.opacity = String(Math.max(0, Math.min(1, alpha)));
  const items = root.children;
  for (let i = 0; i < items.length; i++) {
    const depth = CLOUDS[i]?.depth ?? 1;
    const el = items[i] as HTMLElement;
    // the camera moves on, so the clouds slide down and back past it
    el.style.transform = `translate(${(-drift * 16 * depth).toFixed(2)}vw, ${(drift * 34 * depth).toFixed(2)}vh)`;
  }
}
