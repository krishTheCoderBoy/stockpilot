/**
 * Geometry and kinematics for the warehouse scene, all in one 1600 x 900 stage.
 *
 * The reach stacker is a set of photograph layers (scenes/art). Its boom swings about the real
 * hinge, the lift cylinder is re-aimed between its two pins so it always joins them, the spreader
 * hangs level from the boom tip, and the container hangs from the spreader, found from the boom's
 * angle, so it never drifts off. At the end the machine turns to its front view (the beam raised
 * on its mast, the container held high and drawn larger), which scene 3 carries on from.
 *
 * theta = 0 is the boom as photographed; positive tips the spreader down, negative lifts it.
 */
import { CONTAINER, FRONT_PX, FRONT_SCALE, SIDE_PX, SIDE_SCALE, ZOOM } from "../art/dims";

export { CONTAINER, ZOOM };
export const STAGE = { width: 1600, height: 900, floorY: 820 } as const;

const rad = (deg: number) => (deg * Math.PI) / 180;
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const S = SIDE_SCALE;

export const CENTER_X = STAGE.width / 2;

// Boom angles in degrees from the photographed pose.
export const TRAVEL_THETA = -15; // while driving in, boom raised well clear of the stack
export const LIFT_THETA = -13; // lifted high, container centred above the machine

// The stack: four containers, two high. The red one on top of the teal is the one we take.
const BASE_X = 960;
const GAP = 12;
const BASE_Y = STAGE.floorY - CONTAINER.h;
export const STACK = {
  teal: { x: BASE_X, y: BASE_Y },
  orange: { x: BASE_X + CONTAINER.w + GAP, y: BASE_Y },
  red: { x: BASE_X, y: BASE_Y - CONTAINER.h },
  grey: { x: BASE_X + CONTAINER.w + GAP, y: BASE_Y - CONTAINER.h },
} as const;

const GRIP_X = CONTAINER.w / 2;

interface Pt {
  x: number;
  y: number;
}

const { pivot, swivel, fork, cylBottom, cylTop } = SIDE_PX;

/** Rotates a layer point about the hinge by `thetaDeg`. Layer pixels in, layer pixels out. */
function aboutPivot(p: Pt, thetaDeg: number): Pt {
  const c = Math.cos(rad(thetaDeg));
  const s = Math.sin(rad(thetaDeg));
  const dx = p.x - pivot.x;
  const dy = p.y - pivot.y;
  return { x: pivot.x + dx * c - dy * s, y: pivot.y + dx * s + dy * c };
}

/** Where the twist-locks are, in stage coordinates, for a machine whose rear is at x = teleX. */
export function forkPoint(teleX: number, thetaDeg: number): Pt {
  const sw = aboutPivot(swivel, thetaDeg);
  const px = sw.x + (fork.x - swivel.x);
  const py = sw.y + (fork.y - swivel.y);
  return { x: teleX + px * S, y: STAGE.floorY + (py - SIDE_PX.ground) * S };
}

/** Transforms for the machine's moving layers (inside the machine's layer-pixel space). */
export function sideParts(thetaDeg: number) {
  const sw = aboutPivot(swivel, thetaDeg);
  const top = aboutPivot(cylTop, thetaDeg);
  const v0 = { x: cylTop.x - cylBottom.x, y: cylTop.y - cylBottom.y };
  const v1 = { x: top.x - cylBottom.x, y: top.y - cylBottom.y };
  const turn = (Math.atan2(v1.y, v1.x) - Math.atan2(v0.y, v0.x)) * (180 / Math.PI);
  const stretch = Math.hypot(v1.x, v1.y) / Math.hypot(v0.x, v0.y);
  return {
    boom: `rotate(${thetaDeg.toFixed(3)} ${pivot.x} ${pivot.y})`,
    spreader: `translate(${(sw.x - swivel.x).toFixed(2)} ${(sw.y - swivel.y).toFixed(2)})`,
    cyl: `translate(${cylBottom.x} ${cylBottom.y}) rotate(${turn.toFixed(3)}) scale(${stretch.toFixed(4)}) translate(${-cylBottom.x} ${-cylBottom.y})`,
  };
}

/** The machine position and boom angle at which the spreader is exactly on the red container's roof. */
export function solveGrabPose(): { teleX: number; theta: number } {
  const target = { x: STACK.red.x + GRIP_X, y: STACK.red.y };
  let low = -70;
  let high = 50;
  for (let i = 0; i < 60; i++) {
    const mid = (low + high) / 2;
    if (forkPoint(0, mid).y < target.y) low = mid;
    else high = mid;
  }
  const theta = (low + high) / 2;
  return { theta, teleX: target.x - forkPoint(0, theta).x };
}

/** Where the machine ends up so the carried container is centred horizontally on the stage. */
export function solveLiftTeleX(): number {
  return CENTER_X - forkPoint(0, LIFT_THETA).x;
}

/** How far left the machine must start to be fully off screen, whatever the screen's shape. */
export function offscreenStartX(svg: SVGSVGElement): number {
  const { width, height } = svg.getBoundingClientRect();
  const reach = SIDE_PX.size.w * S + 60;
  if (!width || !height) return -(reach + 200);
  const scale = Math.min(width / STAGE.width, height / STAGE.height);
  const band = Math.max(0, (width / scale - STAGE.width) / 2);
  return -(band + reach);
}

export interface RigState {
  teleX: number;
  theta: number;
  /** 0 = container resting on the stack, 1 = carried by the spreader. */
  attach: number;
  /** How far the counting numbers have got, 0 to 1. */
  stat: number;
  /** Machine nose-dip while braking, in degrees (positive dips the front). */
  pitch: number;
  /** Container swing about the spreader, in degrees. */
  sway: number;
  /** Container jolt as the twist-locks bite, in stage units, downward. */
  bump: number;
  /** 0 = the machine is seen from the side, 1 = from the front. */
  front: number;
  /** 0 = the container is drawn at carried size, 1 = zoomed and held by the front view's beam. */
  zoom: number;
}

// ---- front view ----
const FS = FRONT_SCALE;
export const FRONT_ORIGIN = {
  x: CENTER_X - FRONT_PX.centerX * FS,
  y: STAGE.floorY - FRONT_PX.ground * FS,
} as const;
/** Height of the twist-locks above the ground when the beam is at the photographed height. */
const FRONT_LOCK_Y = FRONT_ORIGIN.y + FRONT_PX.lockY * FS;

/** The raised beam: high enough for the truck's cab to pass under the container. */
export const FRONT_LIFT = 254;

/** Container top-centre while the front view's beam holds it `lift` stage units above the photographed height. */
export function frontHold(lift: number): Pt {
  return { x: CENTER_X, y: FRONT_LOCK_Y - lift };
}

/** The beam lift at which a zoomed container's bottom just touches a truck deck of the given height. */
export function frontLiftForDeck(deckTopY: number): number {
  return FRONT_LOCK_Y + CONTAINER.h * ZOOM - deckTopY;
}

/** The container's top-centre where the side view carries it, once lifted. */
export function liftedContainer(): Pt {
  const fork = forkPoint(solveLiftTeleX(), LIFT_THETA);
  return { x: fork.x, y: fork.y };
}

/** The rig as scene 2 leaves it (container lifted, machine seen from the front), for scene 3 to pick up. */
export function finalRig(): RigState {
  return { teleX: solveLiftTeleX(), theta: LIFT_THETA, attach: 1, stat: 1, pitch: 0, sway: 0, bump: 0, front: 1, zoom: 1 };
}

export function staticRig(): RigState {
  const grab = solveGrabPose();
  return { teleX: grab.teleX, theta: grab.theta, attach: 0, stat: 1, pitch: 0, sway: 0, bump: 0, front: 0, zoom: 0 };
}

export const FRONT_X = FRONT_ORIGIN.x;

/** Writes the front view's beam height: the spreader layer rises and the mast strip stretches up to it. */
export function setLift(group: SVGGElement, lift: number): void {
  const d = Math.max(0, lift / FS);
  group.querySelector('[data-front="spr"]')?.setAttribute("transform", `translate(0 ${(-d).toFixed(2)})`);
  const ext = group.querySelector('[data-front="ext"]');
  ext?.setAttribute("y", (FRONT_PX.split - d).toFixed(2));
  ext?.setAttribute("height", (d + FRONT_PX.slice.h).toFixed(2));
}

export interface RigElements {
  tele: SVGGElement;
  boom: SVGElement;
  spr: SVGElement;
  cyl: SVGElement;
  red: SVGGElement;
  side: SVGGElement;
  front: SVGGElement;
  /** The counting numbers; each carries data-target, data-decimals and data-suffix. */
  stats: HTMLElement[];
}

/** Where the container's top-centre is for a rig state: resting on the stack, carried, or held by the front beam. */
export function containerAnchor(rig: RigState): Pt {
  const fork = forkPoint(rig.teleX, rig.theta);
  const rest = { x: STACK.red.x + GRIP_X, y: STACK.red.y };
  const carried = { x: lerp(rest.x, fork.x, rig.attach), y: lerp(rest.y, fork.y, rig.attach) + rig.bump };
  const held = frontHold(FRONT_LIFT);
  return { x: lerp(carried.x, held.x, rig.zoom), y: lerp(carried.y, held.y, rig.zoom) };
}

/** The transform of a container whose top-centre is `at`, drawn at `scale`, swinging by `sway` degrees. */
export function containerTransform(at: Pt, scale: number, sway = 0): string {
  return `translate(${at.x.toFixed(2)} ${at.y.toFixed(2)}) rotate(${sway.toFixed(3)}) scale(${scale.toFixed(4)}) translate(${-CONTAINER.w / 2} 0)`;
}

/** Writes the rig state to the DOM. Only SVG transforms, opacity and the counter text change. */
export function applyRig(els: RigElements, rig: RigState): void {
  els.tele.setAttribute(
    "transform",
    `translate(${rig.teleX.toFixed(2)} ${STAGE.floorY}) rotate(${rig.pitch.toFixed(3)} ${(SIDE_PX.size.w * S) / 2} 0) scale(${S}) translate(0 ${-SIDE_PX.ground})`
  );
  const parts = sideParts(rig.theta);
  els.boom.setAttribute("transform", parts.boom);
  els.spr.setAttribute("transform", parts.spreader);
  els.cyl.setAttribute("transform", parts.cyl);
  const anchor = containerAnchor(rig);
  els.red.setAttribute("transform", containerTransform(anchor, lerp(1, ZOOM, rig.zoom), rig.sway * rig.attach * (1 - rig.zoom)));
  els.side.style.opacity = String(1 - rig.front);
  els.front.style.opacity = String(rig.front);
  for (const el of els.stats) {
    el.textContent = formatStat(Number(el.dataset.target), Number(el.dataset.decimals), el.dataset.suffix ?? "", rig.stat);
  }
}

/** A counting number at `fraction` (0 to 1) of its target, e.g. 2,785+ or 99.9%. */
export function formatStat(target: number, decimals: number, suffix: string, fraction: number): string {
  const value = target * Math.min(1, Math.max(0, fraction));
  return `${value.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;
}
