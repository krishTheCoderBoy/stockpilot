/**
 * Shared by scenes 5 and 6 so the water is one continuous picture across the hand-off.
 * `offset` is how far the "camera" has travelled (the timelines write it, the shader reads it);
 * the water's own ripple runs off the wall clock, so both scenes' canvases agree on every frame.
 */
export const oceanState = { offset: 0 };
