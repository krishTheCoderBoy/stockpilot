import { FRONT_SCALE, SIDE_PX, SIDE_SCALE } from "../art/dims";
import { ContainerPhoto, ReachFrontLayers, ReachSideLayers } from "../art/RealArt";
import {
  FRONT_LIFT,
  FRONT_ORIGIN,
  STACK,
  STAGE,
  containerAnchor,
  containerTransform,
  setLift,
  sideParts,
  solveGrabPose,
} from "./warehouseRig";

// Drawn in the pose the page falls back to (mobile, reduced motion): the spreader just over the
// container, ready to lift. The scroll timeline takes over from here on desktop.
const GRAB = solveGrabPose();

/** The containers the red one is stacked with. Shared with scene 3, which opens on the same picture. */
export function StackBase({ opacityHook }: { opacityHook?: string }) {
  return (
    <g data-yard={opacityHook}>
      {(["teal", "orange", "grey"] as const).map((colour) => (
        <g key={colour} transform={`translate(${STACK[colour].x} ${STACK[colour].y})`}>
          <ContainerPhoto colour={colour} />
        </g>
      ))}
    </g>
  );
}

/** The machine from the front, with its beam raised to hold the container. Scene 3 reuses it. */
export function FrontMachine({ hook, opacity }: { hook: string; opacity: number }) {
  return (
    <g
      data-wh={hook === "wh" ? "front" : undefined}
      data-tr={hook === "tr" ? "front" : undefined}
      transform={`translate(${FRONT_ORIGIN.x} ${FRONT_ORIGIN.y}) scale(${FRONT_SCALE})`}
      style={{ opacity }}
      ref={(group) => {
        if (group) setLift(group, FRONT_LIFT);
      }}
    >
      <ReachFrontLayers />
    </g>
  );
}

// The machine, the red container and the stack are moved by GSAP through the data-wh hooks.
export function WarehouseStage() {
  const parts = sideParts(GRAB.theta);
  const at = containerAnchor({ teleX: GRAB.teleX, theta: GRAB.theta, attach: 0, stat: 1, pitch: 0, sway: 0, bump: 0, front: 0, zoom: 0 });
  const machine = `translate(${GRAB.teleX} ${STAGE.floorY}) scale(${SIDE_SCALE}) translate(0 ${-SIDE_PX.ground})`;

  return (
    <svg
      className="lp-wh__stage"
      data-wh="stage"
      viewBox={`0 0 ${STAGE.width} ${STAGE.height}`}
      preserveAspectRatio="xMidYMax meet"
      aria-hidden="true"
      focusable="false"
    >
      {/* floor, extended well past the viewBox so wide screens do not show an edge */}
      <rect x={-3000} y={STAGE.floorY} width={7600} height={400} fill="#eef0f5" />
      <rect x={-3000} y={STAGE.floorY - 1} width={7600} height={3} fill="#d5d9e3" />

      <StackBase opacityHook="wh" />

      {/* the machine seen from the side: working the stack */}
      <g data-wh="side">
        <g data-wh="tele" transform={machine}>
          <ReachSideLayers parts={parts} />
        </g>
      </g>

      {/* the same machine from the front, beam up: fades in as the container is lifted clear */}
      <FrontMachine hook="wh" opacity={0} />

      {/* the red container is drawn last, in front of the boom and the beam */}
      <g data-wh="red" transform={containerTransform(at, 1)}>
        <ContainerPhoto colour="red" />
      </g>
    </svg>
  );
}
