/**
 * Sizes of the photographed vehicles and containers, in the 1600 x 900 stage the scenes share.
 * The photos are cut into layers by a script (see src/assets/landing/README.md); every number
 * below was measured on those layers.
 */

// ---- containers (straight-on photo, 900 x 420) ----
export const CONTAINER_PX = { w: 900, h: 420 } as const;
/** A container as the side-view stacker carries it: as wide as the spreader. */
export const CONTAINER = { w: 258, h: Math.round((258 * 420) / 900) } as const;
/** How much larger the container is drawn once the machine has turned to face us. */
export const ZOOM = 1.7;

// ---- reach stacker, side view (layers are 1400 x 880 px; ground at y = GROUND) ----
export const SIDE_PX = {
  size: { w: 1400, h: 880 },
  ground: 856.1,
  /** Where the boom hinges. */
  pivot: { x: 195.1, y: 391.5 },
  /** The swivel under the boom tip. */
  swivel: { x: 1208.0, y: 242.8 },
  /** The twist-lock underside of the spreader. */
  fork: { x: 1219.1, y: 408.8 },
  /** The lift cylinder: lower pin on the body, upper pin on the boom (in the photo's pose). */
  cylBottom: { x: 721.7, y: 622.6 },
  cylTop: { x: 458.4, y: 232.3 },
  spreaderWidth: 330.8,
} as const;
/** Stage units per layer pixel: the spreader is exactly one container wide. */
export const SIDE_SCALE = CONTAINER.w / SIDE_PX.spreaderWidth;

// ---- reach stacker, front view (layers are 1400 x 1273 px) ----
export const FRONT_PX = {
  size: { w: 1400, h: 1273 },
  ground: 1262.1,
  /** Middle of the beam. */
  centerX: 806,
  /** The twist-locks' row, where the container's roof sits. */
  lockY: 471.7,
  lockSpan: 1380.8 - 229.1,
  /** Everything above this row rides with the spreader. */
  split: 470,
  /** A strip of the body just under the split, stretched to make the mast reach the raised beam. */
  slice: { x: 600, y: 480, w: 410, h: 14 },
} as const;
/** Stage units per layer pixel: the front spreader is exactly one zoomed container wide. */
export const FRONT_SCALE = (CONTAINER.w * ZOOM) / FRONT_PX.lockSpan;

// ---- flatbed truck, side view, facing right (1600 x 483 px) ----
export const TRUCK_PX = { w: 1600, h: 483, ground: 476, deck: 315, deckLeft: 6, deckRight: 962 } as const;
/** Chosen so the deck is exactly as high as the front-view locks sit above the ground. */
export const TRUCK_SCALE = 0.72;
export const TRUCK_SIDE = {
  length: TRUCK_PX.w * TRUCK_SCALE,
  deckHeight: (TRUCK_PX.ground - TRUCK_PX.deck) * TRUCK_SCALE,
  /** The middle of the flat deck, where a container sits. */
  bedCenterX: ((TRUCK_PX.deckLeft + TRUCK_PX.deckRight) / 2) * TRUCK_SCALE,
} as const;
