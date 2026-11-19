import type { SceneApi } from "../hooks/useScrollScene";
import { useFullMotion } from "../lib/mode";
import { REVEAL } from "../lib/reveal";
import { MaskedLines } from "../ui/MaskedLines";
import { sceneMeta } from "./data";
import { SceneShell, type BuildResult } from "./SceneShell";
import {
  LIFT_THETA,
  TRAVEL_THETA,
  applyRig,
  formatStat,
  offscreenStartX,
  solveGrabPose,
  solveLiftTeleX,
  staticRig,
  type RigElements,
  type RigState,
} from "./warehouse/warehouseRig";
import { WarehouseStage } from "./warehouse/WarehouseStage";

const meta = sceneMeta(2);

// Placeholder figures: replace them with your real numbers.
const STATS = [
  { target: 2785, decimals: 0, suffix: "+", label: "Stock movements a day" },
  { target: 99.9, decimals: 1, suffix: "%", label: "Stock accuracy" },
  { target: 5, decimals: 0, suffix: "+", label: "Warehouses in one view" },
] as const;

function findElements(scope: HTMLElement): { els: RigElements; svg: SVGSVGElement } | null {
  const q = <T extends Element>(name: string) => scope.querySelector<T>(`[data-wh="${name}"]`);
  const svg = q<SVGSVGElement>("stage");
  const tele = q<SVGGElement>("tele");
  const boom = q<SVGElement>("boom");
  const spr = q<SVGElement>("spr");
  const cyl = q<SVGElement>("cyl");
  const red = q<SVGGElement>("red");
  const side = q<SVGGElement>("side");
  const front = q<SVGGElement>("front");
  if (!svg || !tele || !boom || !spr || !cyl || !red || !side || !front) return null;
  return {
    svg,
    els: { tele, boom, spr, cyl, red, side, front, stats: Array.from(scope.querySelectorAll<HTMLElement>('[data-wh="stat"]')) },
  };
}

/**
 * The scroll story, in order: the numbers count up, the reach stacker drives in, lowers its boom onto
 * the red container on the stack, locks on and lifts it clear. It then turns to face us with its beam
 * raised and the container held up high in the middle of the page (scene 3 carries on from there).
 */
function buildWarehouseTimeline({ gsap, scope }: SceneApi): BuildResult | void {
  const found = findElements(scope);
  if (!found) return;
  const { els, svg } = found;

  const grab = solveGrabPose();
  const rig: RigState = {
    teleX: offscreenStartX(svg),
    theta: TRAVEL_THETA,
    attach: 0,
    stat: 0,
    pitch: 0,
    sway: 0,
    bump: 0,
    front: 0,
    zoom: 0,
  };
  const render = () => applyRig(els, rig);
  // the stack and its top container come into the picture once the words have cleared
  const yard = scope.querySelectorAll('[data-yard="wh"], [data-wh="red"]');
  gsap.set(yard, { opacity: 0 });

  const timeline = gsap.timeline({ paused: true, defaults: { ease: "none" }, onUpdate: render });
  const liftX = solveLiftTeleX();

  timeline
    // 0.02 - 0.17: the numbers count up on the white page, before anything else moves
    .to(rig, { stat: 1, duration: 0.15, ease: "power2.out" }, 0.02)
    // 0.18 - 0.28: the words clear away, so the machine works over a clean white page (as in the
    // reference). Scene 3 then picks up from the lifted container.
    .to(scope.querySelectorAll(".lp-wh__copy, .lp-wh__right"), { opacity: 0, duration: 0.1, ease: "power1.in" }, 0.18)
    .to(yard, { opacity: 1, duration: 0.1, ease: "sine.inOut" }, 0.24)
    // 0.16 - 0.40: the machine drives in from the left, easing to a stop (start is re-measured on every refresh)
    .fromTo(rig, { teleX: () => offscreenStartX(svg) }, { teleX: grab.teleX, duration: 0.24, ease: "power3.out" }, 0.16)
    // a gentle nose-dip as it brakes, easing back as it settles
    .to(rig, { pitch: 0.6, duration: 0.07, ease: "sine.inOut" }, 0.32)
    .to(rig, { pitch: 0, duration: 0.1, ease: "sine.inOut" }, 0.39)
    // 0.42 - 0.58: the boom comes down in one slow, smooth arc and meets the roof at almost no speed
    .to(rig, { theta: grab.theta, duration: 0.16, ease: "sine.inOut" }, 0.42)
    // 0.58 - 0.62: the twist-locks bite
    .to(rig, { attach: 1, duration: 0.02 }, 0.58)
    .to(rig, { bump: 2, duration: 0.02, ease: "sine.out" }, 0.58)
    .to(rig, { bump: 0, duration: 0.03, ease: "sine.inOut" }, 0.6)
    // 0.62 - 0.84: lift clear of the stack and reverse away; the load sways a little and settles
    .to(rig, { theta: LIFT_THETA, teleX: liftX, duration: 0.22, ease: "sine.inOut" }, 0.62)
    .to(rig, { sway: -2, duration: 0.07, ease: "sine.inOut" }, 0.65)
    .to(rig, { sway: 1.3, duration: 0.07, ease: "sine.inOut" }, 0.72)
    .to(rig, { sway: 0, duration: 0.06, ease: "sine.inOut" }, 0.79)
    // 0.86 - 0.97: the machine turns to face us, beam up, and the container grows as it is held high in the middle
    .to(rig, { front: 1, duration: 0.1, ease: "sine.inOut" }, 0.86)
    .to(rig, { zoom: 1, duration: 0.11, ease: "sine.inOut" }, 0.86)
    .to({}, { duration: 0 }, 1);

  render();

  return {
    timeline,
    // back to the static pose if the layout switches to mobile or reduced motion
    cleanup: () => applyRig(els, staticRig()),
  };
}

// Runs in every mode: the headline slides up out of its masks, and the paragraph and numbers fade up,
// the moment the scene appears (on desktop that is right as the hero's white wash completes, so there
// is no blank page between them). Scrolling back reverses it.
function setupWarehouse({ gsap, scope, motion, desktop }: SceneApi) {
  if (!motion) return;
  const scrollTrigger = { trigger: scope, start: desktop ? "top top" : "top 75%", toggleActions: "play none none reverse" };
  gsap.from(scope.querySelectorAll(REVEAL.selector), {
    yPercent: REVEAL.yPercent,
    duration: 1.2,
    ease: REVEAL.ease,
    stagger: REVEAL.stagger,
    scrollTrigger,
  });
  gsap.from(scope.querySelectorAll(".lp-wh__lede, .lp-wh__stats li"), {
    opacity: 0,
    y: 28,
    duration: 1,
    ease: REVEAL.ease,
    stagger: 0.1,
    delay: 0.25,
    scrollTrigger,
  });
}

export function Scene2Warehouse() {
  const full = useFullMotion();

  return (
    <SceneShell
      index={meta.index}
      name={meta.name}
      theme={meta.theme}
      pinLength="400%"
      className={`lp-wh${full ? " lp-handoff" : ""}`}
      handoff={full}
      build={buildWarehouseTimeline}
      setup={setupWarehouse}
    >
      <div className="lp-wh__copy">
        <p className="lp-label lp-wh__eyebrow">Warehouse operations</p>
        <h2 className="lp-display lp-wh__title">
          <MaskedLines
            lines={["We stock it.", <>
              <span className="lp-red">We answer</span> for it.
            </>]}
          />
        </h2>
      </div>

      <div className="lp-wh__right">
        <p className="lp-wh__lede">
          One platform keeps every unit counted, every order traceable and every supplier accountable, so the stock on screen
          is the stock on the shelf.
        </p>
        <ul className="lp-wh__stats">
          {STATS.map((stat) => (
            <li key={stat.label}>
              {/* the final value is the default, so the static layout needs no animation */}
              <span
                className="lp-wh__stat-value"
                data-wh="stat"
                data-target={stat.target}
                data-decimals={stat.decimals}
                data-suffix={stat.suffix}
              >
                {formatStat(stat.target, stat.decimals, stat.suffix, 1)}
              </span>
              <span className="lp-label">{stat.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <WarehouseStage />
    </SceneShell>
  );
}
