/**
 * VIDEO SLOT: swap the animated shader water for a looping WebM.
 *
 * 1. Put the file at  frontend/public/landing/ocean-loop.webm  (any seamless top-down loop).
 * 2. Set OCEAN_VIDEO_SRC below to "/landing/ocean-loop.webm".
 *
 * While this is null the water is rendered by the shader in OceanCanvas.tsx, using
 * the CSS gradient (--lp-sea). The video replaces both the shader and the still.
 */
export const OCEAN_VIDEO_SRC: string | null = null;
