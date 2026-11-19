import shipWake from "../../../assets/landing/ship-wake.svg";
import shipTop from "../../../assets/landing/ship-topdown.svg";
import type { SceneApi } from "../hooks/useScrollScene";
import { useFullMotion } from "../lib/mode";
import { sceneMeta } from "./data";
import { CloudLayer } from "./ocean/CloudLayer";
import { applyClouds } from "./ocean/clouds";
import { OceanBackdrop } from "./ocean/OceanBackdrop";
import { oceanState } from "./ocean/oceanState";
import { SceneShell, type BuildResult } from "./SceneShell";

const meta = sceneMeta(5);

// One stage for the ship, same shape as the other scenes' stages.
const STAGE = { width: 1600, height: 900 } as const;
// art: ship-topdown.svg is 220 x 960 with the bow at (110, 952) and the stern at the top;
// ship-wake.svg is 520 x 1500 with the stern at its bottom centre.
const SHIP = { width: 220, height: 960, bowX: 110, bowY: 952, sternX: 110, sternY: 10 } as const;
const WAKE = { width: 520, height: 1500 } as const;
const BASE = 0.78; // stage units per art pixel at zoom 1: the whole ship fits the screen
const LANE_X = STAGE.width / 2;

interface Callout {
  tag: string;
  text: string;
  side: "left" | "right";
  /** Where on the screen the card sits, as a percentage of the viewport height. */
  top: number;
  /** Scroll point (0 to 1) at which the card appears. */
  at: number;
}

const CALLOUTS: Callout[] = [
  { tag: "Alerts", text: "Low-stock alerts that fire early", side: "left", top: 16, at: 0.6 },
  { tag: "Pricing", text: "Purchase prices with no small print", side: "right", top: 32, at: 0.67 },
  { tag: "Movements", text: "Every movement in plain sight", side: "left", top: 52, at: 0.74 },
  { tag: "Approvals", text: "Approvals that clear fast", side: "right", top: 68, at: 0.81 },
];
const CARD_HOLD = 0.13;

/**
 * The ship points up the page. `z` is how close the camera is (a multiple of the whole-ship fit)
 * and `bowY` is where the bow is on screen; the group is scaled about the bow, so zooming out
 * pulls the whole ship into view behind it.
 */
function shipTransform(z: number, bowY: number): string {
  return `translate(${LANE_X} ${bowY.toFixed(2)}) rotate(180) scale(${(BASE * z).toFixed(4)}) translate(${-SHIP.bowX} ${-SHIP.bowY})`;
}

const ZOOM_ENTER = { z: 7.5, bowY: 1200 } as const; // the bow still below the page
const ZOOM_START = { z: 7.5, bowY: 340 } as const; // the bow fills the frame
const ZOOM_DECK = { z: 2.7, bowY: 190 } as const; // rows of containers
const ZOOM_FULL = { z: 1, bowY: 70 } as const; // the whole ship

/**
 * The scroll story. The page opens on the sea that rose at the end of the road, with the bow
 * of a ship filling the frame. The camera pulls back over the deck until the whole ship is in
 * view, glass cards float in around it, and then it sails off the top of the page so the plane
 * can come in over open water.
 */
function buildOceanTimeline({ gsap, scope }: SceneApi): BuildResult | void {
  const svg = scope.querySelector<SVGSVGElement>('[data-oc="stage"]');
  const ship = scope.querySelector<SVGGElement>('[data-oc="ship"]');
  const wake = scope.querySelector('[data-oc="wake"]');
  const cards = scope.querySelectorAll<HTMLElement>('[data-oc="card"]');
  if (!svg || !ship) return;

  const clouds = scope.querySelector<HTMLElement>('[data-clouds]');
  const cloudRig = { drift: 0, alpha: 0 };
  const rig = { z: ZOOM_ENTER.z, bowY: ZOOM_ENTER.bowY };
  const render = () => {
    ship.setAttribute("transform", shipTransform(rig.z, rig.bowY));
    applyClouds(clouds, cloudRig.drift, cloudRig.alpha);
  };
  gsap.set(cards, { opacity: 0 });

  const timeline = gsap.timeline({ paused: true, defaults: { ease: "none" }, onUpdate: render });
  timeline
    // 0.00 - 0.10: the bow rises up into the frame out of the water that just covered the road
    .to(rig, { bowY: ZOOM_START.bowY, duration: 0.1, ease: "power2.out" }, 0)
    // 0.08 - 0.34: then from the bow, back over the deck
    .to(rig, { z: ZOOM_DECK.z, bowY: ZOOM_DECK.bowY, duration: 0.26, ease: "sine.inOut" }, 0.08)
    // 0.30 - 0.58: and out until the whole ship is in view
    .to(rig, { z: ZOOM_FULL.z, bowY: ZOOM_FULL.bowY, duration: 0.24, ease: "sine.inOut" }, 0.34)
    // 0.90 - 1.00: the ship sails off the top of the page, wake and all
    .to(rig, { bowY: -(SHIP.bowY * BASE) - 60, duration: 0.1, ease: "sine.in" }, 0.9)
    .to(wake, { opacity: 0, duration: 0.06 }, 0.94)
    // clouds roll in over the water as the ship leaves: scene 6 carries on from exactly this picture
    .to(cloudRig, { drift: 1, duration: 0.3, ease: "sine.inOut" }, 0.7)
    .to(cloudRig, { alpha: 1, duration: 0.22, ease: "sine.inOut" }, 0.72)
    // the water streams past the whole time, as the ship moves up through it
    .to(oceanState, { offset: 1.3, duration: 1 }, 0);

  cards.forEach((card, i) => {
    const { at, side } = CALLOUTS[i];
    const dir = side === "left" ? -1 : 1;
    timeline
      .fromTo(card, { opacity: 0, x: 28 * dir, y: 24 }, { opacity: 1, x: 0, y: 0, duration: 0.05, ease: "power2.out" }, at)
      .to(card, { opacity: 0, y: -18, duration: 0.04, ease: "power2.in" }, Math.min(at + CARD_HOLD, 0.93));
  });

  render();

  return {
    timeline,
    cleanup: () => {
      oceanState.offset = 0;
      ship.setAttribute("transform", shipTransform(ZOOM_FULL.z, ZOOM_FULL.bowY));
      applyClouds(clouds, 0, 0);
    },
  };
}

export function Scene5Ocean() {
  const full = useFullMotion();
  const initial = full ? ZOOM_ENTER : ZOOM_FULL;

  return (
    <SceneShell
      index={meta.index}
      name={meta.name}
      theme={meta.theme}
      pinLength="450%"
      className={`lp-oc ${full ? "lp-handoff" : "is-static"}`}
      handoff={full}
      build={buildOceanTimeline}
    >
      <OceanBackdrop dataKey="scene5" />

      <svg
        className="lp-oc__stage"
        data-oc="stage"
        viewBox={`0 0 ${STAGE.width} ${STAGE.height}`}
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
        focusable="false"
      >
        <g data-oc="ship" transform={shipTransform(initial.z, initial.bowY)}>
          <image
            data-oc="wake"
            href={shipWake}
            x={SHIP.sternX - WAKE.width / 2}
            y={SHIP.sternY - WAKE.height}
            width={WAKE.width}
            height={WAKE.height}
          />
          <image href={shipTop} width={SHIP.width} height={SHIP.height} />
        </g>
      </svg>

      {full && <CloudLayer dataKey="scene5" />}

      <div className="lp-oc__cards">
        {CALLOUTS.map((callout) => (
          <article
            key={callout.tag}
            className={`lp-oc__card lp-oc__card--${callout.side}`}
            style={{ top: `${callout.top}svh` }}
            data-oc="card"
          >
            <p className="lp-label lp-oc__tag">{callout.tag}</p>
            <h2 className="lp-oc__text">{callout.text}</h2>
          </article>
        ))}
      </div>
    </SceneShell>
  );
}
