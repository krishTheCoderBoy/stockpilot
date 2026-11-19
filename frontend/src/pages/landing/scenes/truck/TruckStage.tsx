import { ContainerPhoto, TruckPhoto } from "../art/RealArt";
import { ROAD_D, ROAD_WIDTH } from "../road/roadGeometry";
import { STAGE } from "../warehouse/warehouseRig";
import { FrontMachine, StackBase } from "../warehouse/WarehouseStage";
import { TRUCK, TRUCK_HOLD_X, startRig, truckTransforms } from "./truckRig";

/**
 * Same stage as scene 2 (same viewBox and alignment), so the two scenes line up exactly.
 * `full` draws scene 2's last frame as the starting point; otherwise (mobile, reduced motion)
 * only the loaded truck is drawn.
 */
export function TruckStage({ full }: { full: boolean }) {
  // Initial transforms come from the same function the timeline uses.
  const rig = full ? startRig(-2000) : { ...startRig(TRUCK_HOLD_X), carry: 0 };
  const t = truckTransforms(rig);

  return (
    <svg
      className="lp-tr__stage"
      data-tr="stage"
      viewBox={`0 0 ${STAGE.width} ${STAGE.height}`}
      preserveAspectRatio="xMidYMax meet"
      aria-hidden="true"
      focusable="false"
    >
      <g data-tr="floor">
        <rect x={-3000} y={STAGE.floorY} width={7600} height={400} fill="#eef0f5" />
        <rect x={-3000} y={STAGE.floorY - 1} width={7600} height={3} fill="#d5d9e3" />
      </g>

      {/* scene 4's road, fading in behind the truck as it drives away (see Scene3Truck) */}
      {full && (
        <g data-tr="road" opacity={0}>
          <path d={ROAD_D} fill="none" stroke="#dfe3ec" strokeWidth={ROAD_WIDTH + 14} strokeLinecap="butt" />
          <path d={ROAD_D} fill="none" stroke="#0b0e17" strokeWidth={ROAD_WIDTH} strokeLinecap="butt" />
          <path d={ROAD_D} fill="none" stroke="#ffffff" strokeOpacity={0.8} strokeWidth={5} strokeDasharray="36 28" />
        </g>
      )}

      {full && (
        <>
          <StackBase opacityHook="tr" />
          <FrontMachine hook="tr" opacity={1} />
        </>
      )}

      {/* the truck drives in the lane nearest the camera, in front of the reach stacker */}
      <g data-tr="truck" transform={t.truck}>
        <TruckPhoto scale={TRUCK.scale} />
      </g>

      {/* the container is one object from the stack to the road: hung from the beam, then riding the deck */}
      <g data-tr="red" transform={t.red}>
        <ContainerPhoto colour="red" />
      </g>
    </svg>
  );
}
