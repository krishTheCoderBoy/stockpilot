import containerGreen from "../../../../assets/landing/container-green.webp";
import containerGrey from "../../../../assets/landing/container-grey.webp";
import containerOrange from "../../../../assets/landing/container-orange.webp";
import containerRed from "../../../../assets/landing/container-red.webp";
import containerTeal from "../../../../assets/landing/container-teal.webp";
import frontBody from "../../../../assets/landing/front-body.webp";
import frontSpreader from "../../../../assets/landing/front-spreader.webp";
import reachBody from "../../../../assets/landing/reach-body.webp";
import reachBoom from "../../../../assets/landing/reach-boom.webp";
import reachCylinder from "../../../../assets/landing/reach-cylinder.webp";
import reachSpreader from "../../../../assets/landing/reach-spreader.webp";
import truckFlatbed from "../../../../assets/landing/truck-flatbed.webp";
import { CONTAINER, FRONT_PX, SIDE_PX, TRUCK_PX } from "./dims";

export type BoxColour = "red" | "teal" | "orange" | "green" | "grey";

const BOX_SRC: Record<BoxColour, string> = {
  red: containerRed,
  teal: containerTeal,
  orange: containerOrange,
  green: containerGreen,
  grey: containerGrey,
};

/** A container photo, top-left at the origin, one carried-container wide. */
export function ContainerPhoto({ colour }: { colour: BoxColour }) {
  return <image href={BOX_SRC[colour]} width={CONTAINER.w} height={CONTAINER.h} />;
}

const SIDE_SIZE = SIDE_PX.size;

/**
 * The four layers of the side view share one 1400 x 880 frame, so they line up by construction.
 * The rig moves the boom, the cylinder and the spreader; the body stays put.
 */
export function ReachSideLayers({ parts }: { parts: { boom: string; spreader: string; cyl: string } }) {
  return (
    <>
      <image href={reachBody} width={SIDE_SIZE.w} height={SIDE_SIZE.h} />
      <image data-wh="cyl" transform={parts.cyl} href={reachCylinder} width={SIDE_SIZE.w} height={SIDE_SIZE.h} />
      <image data-wh="boom" transform={parts.boom} href={reachBoom} width={SIDE_SIZE.w} height={SIDE_SIZE.h} />
      <image data-wh="spr" transform={parts.spreader} href={reachSpreader} width={SIDE_SIZE.w} height={SIDE_SIZE.h} />
    </>
  );
}

/**
 * The reach stacker head-on: a fixed body, a strip of the mast stretched up to the raised beam, and
 * the spreader (boom head, beam and twist-locks) that the rig lifts. Local units are layer pixels.
 */
export function ReachFrontLayers() {
  const { size, slice } = FRONT_PX;
  return (
    <>
      <image href={frontBody} width={size.w} height={size.h} />
      <svg data-front="ext" x={slice.x} y={FRONT_PX.split} width={slice.w} height={slice.h} viewBox={`${slice.x} ${slice.y} ${slice.w} ${slice.h}`} preserveAspectRatio="none">
        <image href={frontBody} width={size.w} height={size.h} />
      </svg>
      <image data-front="spr" href={frontSpreader} width={size.w} height={size.h} />
    </>
  );
}

/** A flatbed truck facing right; the origin is the rear of the trailer, on the ground. */
export function TruckPhoto({ scale }: { scale: number }) {
  return (
    <image
      href={truckFlatbed}
      x={0}
      y={-TRUCK_PX.ground * scale}
      width={TRUCK_PX.w * scale}
      height={TRUCK_PX.h * scale}
    />
  );
}
