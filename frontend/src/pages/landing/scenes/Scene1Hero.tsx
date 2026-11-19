import { lazy, Suspense, useRef } from "react";
import globeFallback from "../../../assets/landing/hero-globe-fallback.svg";
import type { SceneApi } from "../hooks/useScrollScene";
import { hasWebGL, useFullMotion } from "../lib/mode";
import { REVEAL } from "../lib/reveal";
import { useInView } from "../lib/useInView";
import { MaskedLines } from "../ui/MaskedLines";
import { sceneMeta } from "./data";
import { heroState } from "./hero/heroState";
import { MiniNav } from "./hero/MiniNav";
import { Ticker } from "./hero/Ticker";
import { SceneShell, type BuildResult } from "./SceneShell";

// three.js and react-three-fiber load only for visitors who get the 3D hero.
const GlobeCanvas = lazy(() => import("./hero/GlobeCanvas"));

const meta = sceneMeta(1);

/**
 * The scroll story: the globe dollies toward the camera and the ring sweeps (both driven by
 * heroState.progress inside WebGL), the headline lifts away, and a white wash takes the
 * background from navy to white, ready for the next scene.
 */
function buildHeroTimeline({ gsap, scope }: SceneApi): BuildResult {
  const q = gsap.utils.selector(scope);
  const copy = q('[data-hero="copy"]');
  const chrome = q('[data-hero="chrome"]');
  const wash = q('[data-hero="wash"]');
  const stage = q('[data-hero="stage"]');

  const timeline = gsap.timeline({
    paused: true,
    defaults: { ease: "none" },
    onUpdate: () => {
      // The cursor flips to its dark ring once the background has gone white.
      scope.dataset.sceneTheme = timeline.progress() > 0.7 ? "light" : "dark";
    },
  });

  // The whole move is over by 0.85 of the scene's length, with the white wash finishing just
  // before it: scene 2 takes over at the very end, so there is no blank page in between.
  timeline
    .to(heroState, { progress: 1, duration: 0.85 }, 0)
    .to(copy, { yPercent: -30, opacity: 0, duration: 0.24, ease: "power2.in" }, 0.08)
    .to(chrome, { opacity: 0, duration: 0.17 }, 0.08)
    .to(wash, { opacity: 1, duration: 0.3, ease: "power1.inOut" }, 0.55)
    .to(stage, { opacity: 0, duration: 0.1 }, 0.75);

  return {
    timeline,
    cleanup: () => {
      heroState.progress = 0;
      scope.dataset.sceneTheme = "dark";
    },
  };
}

// On load: the label fades up and the headline lines slide up out of their masks.
function setupHero({ gsap, scope, motion }: SceneApi) {
  if (!motion) return;
  gsap.from(scope.querySelector('[data-hero="label"]'), { opacity: 0, y: 12, duration: 0.9, ease: "expo.out", delay: 2.2 });
  gsap.from(scope.querySelectorAll(REVEAL.selector), {
    yPercent: REVEAL.yPercent,
    duration: 1.3,
    ease: REVEAL.ease,
    stagger: REVEAL.stagger,
    delay: 2.3,
  });
}

export function Scene1Hero() {
  const stageRef = useRef<HTMLDivElement>(null);
  const show3d = useFullMotion() && hasWebGL();
  const inView = useInView(stageRef);

  return (
    <SceneShell
      index={meta.index}
      name={meta.name}
      theme={meta.theme}
      pinLength="250%"
      className="lp-hero"
      build={buildHeroTimeline}
      setup={setupHero}
    >
      <div ref={stageRef} className="lp-hero__stage" data-hero="stage">
        {/* Static stand-in for mobile and reduced motion. On desktop the canvas plays its own intro,
            a flat world map that curls up into the globe, so this stays hidden. */}
        <img
          src={globeFallback}
          alt=""
          className={`lp-hero__fallback${show3d ? " is-hidden" : ""}`}
          draggable={false}
        />
        {show3d && (
          <Suspense fallback={null}>
            <GlobeCanvas active={inView} />
          </Suspense>
        )}
      </div>
      <div className="lp-hero__vignette" aria-hidden />

      <Ticker />
      <MiniNav />

      <div className="lp-hero__copy" data-hero="copy">
        <p className="lp-label lp-hero__eyebrow" data-hero="label">
          One platform
        </p>
        <h1 className="lp-display lp-hero__title">
          <MaskedLines
            lines={[<span className="lp-red">Every unit</span>, "Of the stock"]}
          />
        </h1>
      </div>

      <div className="lp-hero__wash" data-hero="wash" aria-hidden />
    </SceneShell>
  );
}
