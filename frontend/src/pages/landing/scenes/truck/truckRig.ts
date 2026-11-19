/**
 * Geometry for the truck scene. It shares scene 2's stage (same viewBox and floor), so its first
 * frame is exactly scene 2's last frame: the reach stacker seen from the front, its beam raised and
 * the container held high. A truck pulls in underneath, the beam lowers the container onto the
 * trailer, and the truck drives away carrying it. The container is one object the whole time.
 */
import { CONTAINER, TRUCK_SCALE, TRUCK_SIDE, ZOOM } from "../art/dims";
import {
  CENTER_X,
  FRONT_LIFT,
  STAGE,
  containerTransform,
  frontHold,
  frontLiftForDeck,
  setLift,
} from "../warehouse/warehouseRig";

// The truck drives in the foreground lane, a little nearer the camera than the reach stacker.
const LANE_OFFSET = 20;
export const TRUCK = { ...TRUCK_SIDE, ground: STAGE.floorY + LANE_OFFSET, scale: TRUCK_SCALE } as const;

/** Where the truck stops so the container (centred on the stage) sits on the middle of the deck. */
export const TRUCK_HOLD_X = CENTER_X - TRUCK.bedCenterX;

const DECK_TOP = TRUCK.ground - TRUCK.deckHeight;
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

export interface TruckRig {
  truckX: number;
  /** How far the beam is above its photographed height, in stage units. */
  lift: number;
  /** 1 = the container hangs from the beam, 0 = it rides on the truck. */
  carry: number;
  /** Container jolt, in stage units, downward. */
  bump: number;
  /** Opacity of the reach stacker (it fades once the truck has the container). */
  machine: number;
}

/** Scene 2's last frame: container held up by the beam, truck not yet in. */
export function startRig(truckX: number): TruckRig {
  return { truckX, lift: FRONT_LIFT, carry: 1, bump: 0, machine: 1 };
}

/** The beam height at which the hanging container just touches the deck. */
export function loweredLift(): number {
  return frontLiftForDeck(DECK_TOP);
}

/** Container top-centre when it hangs from the beam, and when it rides on the deck. */
function containerAnchor(rig: TruckRig) {
  const onBeam = frontHold(rig.lift);
  const onTruck = { x: rig.truckX + TRUCK.bedCenterX, y: DECK_TOP - CONTAINER.h * ZOOM };
  return { x: lerp(onTruck.x, onBeam.x, rig.carry), y: lerp(onTruck.y, onBeam.y, rig.carry) + rig.bump };
}

/** Extra width the stage shows on wide screens, in stage units, on each side. */
function sideBand(svg: SVGSVGElement): number {
  const { width, height } = svg.getBoundingClientRect();
  if (!width || !height) return 0;
  const scale = Math.min(width / STAGE.width, height / STAGE.height);
  return Math.max(0, (width / scale - STAGE.width) / 2);
}

export const truckEnterX = (svg: SVGSVGElement) => -(sideBand(svg) + TRUCK.length + 40);
export const truckExitX = (svg: SVGSVGElement) => STAGE.width + sideBand(svg) + 60;

export interface TruckElements {
  truck: SVGGElement;
  red: SVGGElement;
  front: SVGGElement;
}

/** SVG transform strings for the moving parts of a rig state. */
export function truckTransforms(rig: TruckRig) {
  return {
    truck: `translate(${rig.truckX.toFixed(2)} ${TRUCK.ground})`,
    red: containerTransform(containerAnchor(rig), ZOOM),
  };
}

/** Writes the rig to the DOM: SVG transforms, the beam's height and opacity only. */
export function applyTruckRig(els: TruckElements, rig: TruckRig): void {
  const t = truckTransforms(rig);
  els.truck.setAttribute("transform", t.truck);
  els.red.setAttribute("transform", t.red);
  setLift(els.front, rig.lift);
  els.front.style.opacity = String(rig.machine);
}
