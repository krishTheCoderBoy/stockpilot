import plane from "../../../assets/landing/plane-cargo-top.webp";
import type { SceneApi } from "../hooks/useScrollScene";
import { useFullMotion } from "../lib/mode";
import { REVEAL } from "../lib/reveal";
import { MaskedLines } from "../ui/MaskedLines";
import { sceneMeta } from "./data";
import { CloudLayer } from "./ocean/CloudLayer";
import { applyClouds } from "./ocean/clouds";
import { OceanBackdrop } from "./ocean/OceanBackdrop";
import { oceanState } from "./ocean/oceanState";
import { SceneShell, type BuildResult } from "./SceneShell";

const meta = sceneMeta(6);

// Where the plane comes to rest, as a fraction of the screen width from the left edge (CSS: .lp-air__plane).
const REST_LEFT = 0.29;

function buildAirTimeline({ gsap, scope }: SceneApi): BuildResult | void {
  const planeEl = scope.querySelector<HTMLElement>('[data-air="plane"]');
  const water = scope.querySelector('[data-ocean]');
  const lines = scope.querySelectorAll(REVEAL.selector);
  const label = scope.querySelector('[data-air="label"]');
  const clouds = scope.querySelector<HTMLElement>('[data-clouds]');
  // starts exactly where scene 5 left the clouds
  const cloudRig = { drift: 1, alpha: 1 };
  if (!planeEl) return;

  // x is measured from where the plane rests, so the layout (CSS) decides the resting place
  const planeWidth = () => planeEl.getBoundingClientRect().width;
  const startX = () => -(window.innerWidth * REST_LEFT + planeWidth() + 80);

  gsap.set(planeEl, { yPercent: -50 });
  gsap.set(lines, { yPercent: REVEAL.yPercent });
  gsap.set(label, { opacity: 0 });

  applyClouds(clouds, cloudRig.drift, cloudRig.alpha);
  const timeline = gsap.timeline({
    paused: true,
    defaults: { ease: "none" },
    onUpdate: () => {
      applyClouds(clouds, cloudRig.drift, cloudRig.alpha);
      // the white ring cursor would vanish once the water has gone
      scope.dataset.progress = String(timeline.progress());
      scope.dataset.sceneTheme = timeline.progress() < 0.45 ? "teal" : "light";
    },
  });

  timeline
    // the plane flies in from the left over open water, slowing as it settles
    .fromTo(planeEl, { x: startX }, { x: 0, duration: 0.62, ease: "power2.out" }, 0)
    // the camera keeps travelling, so the water keeps moving under it
    .to(oceanState, { offset: 1.5, duration: 0.7 }, 0)
    // the clouds keep sliding past under the plane, then thin out as the page goes to white
    .to(cloudRig, { drift: 2.1, duration: 0.7 }, 0)
    .to(cloudRig, { alpha: 0, duration: 0.22, ease: "sine.inOut" }, 0.34)
    // then the water fades away to white
    .to(water, { opacity: 0, duration: 0.2 }, 0.34)
    // the headline appears once the page is white, partly behind the wings
    .to(label, { opacity: 1, duration: 0.05 }, 0.52)
    .to(lines, { yPercent: 0, duration: 0.09, stagger: 0.025, ease: "expo.out" }, 0.54)
    // the plane keeps drifting after it arrives
    .to(planeEl, { x: () => window.innerWidth * 0.035, duration: 0.38 }, 0.62);

  return {
    timeline,
    cleanup: () => {
      oceanState.offset = 0;
      applyClouds(clouds, 0, 0);
      scope.dataset.sceneTheme = meta.theme;
      delete scope.dataset.progress;
    },
  };
}

export function Scene6Air() {
  const full = useFullMotion();

  return (
    <SceneShell
      index={meta.index}
      name={meta.name}
      theme={meta.theme}
      pinLength="400%"
      className={`lp-air ${full ? "lp-handoff" : "is-static"}`}
      handoff={full}
      build={buildAirTimeline}
    >
      {/* the same water as scene 5, so the hand-off is the same picture; the timeline fades it out */}
      {full && <OceanBackdrop dataKey="scene6" />}
      {full && <CloudLayer dataKey="scene6" />}

      <div className="lp-air__copy">
        <p className="lp-label lp-air__label" data-air="label">
          Reorder planning
        </p>
        <h2 className="lp-display lp-air__title">
          <MaskedLines lines={["Reorder", "before it", <span className="lp-red">runs out.</span>]} />
        </h2>
      </div>

      <img src={plane} alt="" className="lp-air__plane" data-air="plane" width={1800} height={1213} loading="lazy" decoding="async" draggable={false} />
    </SceneShell>
  );
}
