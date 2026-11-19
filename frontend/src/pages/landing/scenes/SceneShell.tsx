import { useRef, type ReactNode } from "react";
import { useScrollScene, type SceneApi } from "../hooks/useScrollScene";
import { setActiveScene } from "../lib/activeScene";
import { SCENE_COUNT, type SceneTheme } from "./data";

export interface BuildResult {
  /** Created with `paused: true`; the shell scrubs it with the scroll position. */
  timeline: ReturnType<SceneApi["gsap"]["timeline"]>;
  /** Undo anything done outside GSAP's own bookkeeping (text, attributes, shared state). */
  cleanup?: () => void;
}

interface SceneShellProps {
  index: number;
  name: string;
  theme: SceneTheme;
  /** How much scroll the pinned scene lasts, e.g. "250%" of the viewport height. */
  pinLength?: string;
  className?: string;
  /**
   * Take over from the previous scene instead of scrolling in below it. The scene overlaps the
   * previous one's last screen (CSS: .lp-handoff), stays invisible until its pin begins, and
   * then shows a first frame that matches the previous scene's last frame. Desktop motion only.
   */
  handoff?: boolean;
  /** False for scenes that scroll normally (no pin, no scrubbed timeline). Defaults to true. */
  pin?: boolean;
  /** Builds the scroll-scrubbed timeline. Runs only when the scene is pinned (desktop, motion allowed). */
  build?: (api: SceneApi) => BuildResult | void;
  /** Extra setup that runs in every mode (load animations, static layout). */
  setup?: (api: SceneApi) => void | (() => void);
  children?: ReactNode;
}

/**
 * The frame every scene shares: a full-height section that pins while its timeline is
 * scrubbed and reports itself as the active scene (for the red counter). Mobile and
 * reduced-motion visitors get the same markup as a plain, unpinned section.
 */
export function SceneShell({
  index,
  name,
  theme,
  pinLength = "100%",
  className = "",
  handoff = false,
  pin = true,
  build,
  setup,
  children,
}: SceneShellProps) {
  const ref = useRef<HTMLElement>(null);

  useScrollScene(ref, (api) => {
    const { ScrollTrigger, scope, motion, desktop } = api;
    const pinned = motion && desktop && pin;
    const built = pinned ? build?.(api) || undefined : undefined;

    // A handed-over scene is "live" (visible, opaque) from the moment its pin starts.
    const sync = (self: { scroll(): number; start: number }) =>
      scope.toggleAttribute("data-live", self.scroll() >= self.start);

    if (pinned) {
      ScrollTrigger.create({
        trigger: scope,
        start: "top top",
        end: `+=${pinLength}`,
        pin: true,
        animation: built?.timeline,
        scrub: built ? true : undefined,
        invalidateOnRefresh: true,
        ...(handoff ? { onEnter: sync, onLeaveBack: sync, onRefresh: sync } : {}),
      });
    }

    // The counter follows the scene that is entering, not just the one that is pinned: a
    // pinned scene releases and scrolls away for another screen height, and the label should
    // already have moved on. onRefresh covers reloads and resizes at a scroll position that
    // is already past this scene's start.
    ScrollTrigger.create({
      trigger: scope,
      // a handed-over scene is only on screen once its pin starts
      start: handoff ? "top top" : "top 60%",
      onEnter: () => setActiveScene(index),
      onLeaveBack: () => setActiveScene(Math.max(1, index - 1)),
      onRefresh: (self) => {
        if (self.scroll() >= self.start) setActiveScene(index);
      },
    });

    const extra = setup?.(api);
    return () => {
      scope.removeAttribute("data-live");
      built?.cleanup?.();
      extra?.();
    };
  });

  const label = `Scene ${String(index).padStart(2, "0")} / ${String(SCENE_COUNT).padStart(2, "0")}`;

  return (
    <section
      ref={ref}
      id={`scene-${index}`}
      data-scene={index}
      data-scene-theme={theme}
      className={`lp-scene lp-${theme} ${className}`.trim()}
      aria-label={name}
    >
      {children ?? (
        <>
          <p className="lp-label">{label}</p>
          <h2 className="lp-display">{name}</h2>
        </>
      )}
    </section>
  );
}
