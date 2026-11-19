import type { SceneApi } from "../hooks/useScrollScene";
import { useFullMotion } from "../lib/mode";
import { sceneMeta } from "./data";
import { SceneShell, type BuildResult } from "./SceneShell";
import { TruckStage } from "./truck/TruckStage";
import {
  TRUCK_HOLD_X,
  applyTruckRig,
  loweredLift,
  startRig,
  truckEnterX,
  truckExitX,
  type TruckElements,
} from "./truck/truckRig";

const meta = sceneMeta(3);

function findElements(scope: HTMLElement): { els: TruckElements; svg: SVGSVGElement } | null {
  const svg = scope.querySelector<SVGSVGElement>('[data-tr="stage"]');
  const truck = scope.querySelector<SVGGElement>('[data-tr="truck"]');
  const red = scope.querySelector<SVGGElement>('[data-tr="red"]');
  const front = scope.querySelector<SVGGElement>('[data-tr="front"]');
  if (!svg || !truck || !red || !front) return null;
  return { svg, els: { truck, red, front } };
}

/**
 * The scroll story. It opens on scene 2's last frame (the container held up by the reach stacker's
 * beam), then: a truck pulls in underneath, the beam lowers the container onto the trailer, the
 * beam lifts away, the reach stacker fades, and the truck carries the container left to right while
 * the ghost word slides the other way. As it drives off, the road scene 4 follows fades in behind it.
 */
function buildTruckTimeline({ gsap, scope }: SceneApi): BuildResult | void {
  const found = findElements(scope);
  if (!found) return;
  const { els, svg } = found;

  const rig = startRig(truckEnterX(svg));
  const render = () => applyTruckRig(els, rig);
  const lowered = loweredLift();

  const watermark = scope.querySelector('[data-tr="watermark"]');
  const yard = scope.querySelector('[data-yard="tr"]');
  const floor = scope.querySelector('[data-tr="floor"]');
  const road = scope.querySelector('[data-tr="road"]');

  gsap.set(watermark, { opacity: 0 });
  gsap.set(road, { opacity: 0 });

  const timeline = gsap.timeline({ paused: true, defaults: { ease: "none" }, onUpdate: render });
  timeline
    // the stack of containers behind drops out of the picture
    .to(yard, { opacity: 0, duration: 0.12 }, 0)
    // watermark: fades in and drifts right to left for the whole drive, against the truck
    .to(watermark, { opacity: 1, duration: 0.1 }, 0.02)
    .fromTo(watermark, { xPercent: 4 }, { xPercent: -38, duration: 0.88 }, 0.02)
    // 0.02 - 0.24: the truck pulls in (start is re-measured on every refresh)
    .fromTo(rig, { truckX: () => truckEnterX(svg) }, { truckX: TRUCK_HOLD_X, duration: 0.22, ease: "power2.out" }, 0.02)
    // 0.26 - 0.40: the beam lowers the container onto the deck in one smooth movement, slowing to
    // a gentle landing
    .to(rig, { lift: lowered, duration: 0.14, ease: "sine.inOut" }, 0.26)
    // touchdown: the weight settles on the trailer
    .to(rig, { bump: 2, duration: 0.012, ease: "sine.out" }, 0.4)
    .to(rig, { bump: 0, duration: 0.02, ease: "sine.inOut" }, 0.412)
    // 0.41: the locks open; the container now rides with the truck (positions match, no jump)
    .to(rig, { carry: 0, duration: 0.01 }, 0.41)
    // 0.41 - 0.47: the beam lifts clear, then the reach stacker fades away behind the truck
    .to(rig, { lift: lowered + 70, duration: 0.06, ease: "sine.inOut" }, 0.41)
    .to(rig, { machine: 0, duration: 0.08, ease: "sine.inOut" }, 0.47)
    // 0.50 - 0.93: the loaded truck runs on, at full size, a long way across the screen: it eases up
    // to speed and carries on until it has left the page
    .to(rig, { truckX: () => truckExitX(svg), duration: 0.43, ease: "sine.in" }, 0.5)
    // 0.78 - 0.92: while it is still driving away, the road that scene 4 follows fades in behind it
    // (scene 4 opens on exactly this picture, so the truck seen from above simply drives on)
    .to(road, { opacity: 1, duration: 0.14, ease: "sine.inOut" }, 0.78)
    // the floor strip and the ghost word clear as the road comes up
    .to([watermark, floor], { opacity: 0, duration: 0.12, ease: "sine.inOut" }, 0.82);

  render();

  return {
    timeline,
    cleanup: () => applyTruckRig(els, startRig(TRUCK_HOLD_X)),
  };
}

export function Scene3Truck() {
  const full = useFullMotion();

  return (
    <SceneShell
      index={meta.index}
      name={meta.name}
      theme={meta.theme}
      pinLength="500%"
      className={`lp-tr ${full ? "lp-handoff" : "is-static"}`}
      handoff={full}
      build={buildTruckTimeline}
    >
      <div className="lp-tr__watermark" data-tr="watermark" aria-hidden="true">
        STOCK
      </div>

      <TruckStage full={full} />
    </SceneShell>
  );
}
