import { useLayoutEffect, type DependencyList, type RefObject } from "react";
import { gsap, ScrollTrigger } from "../lib/gsap";

export interface SceneApi {
  gsap: typeof gsap;
  ScrollTrigger: typeof ScrollTrigger;
  /** The scene's root element; query inside it with gsap.utils.selector(scope). */
  scope: HTMLElement;
  /** False when the visitor prefers reduced motion: build a static layout instead. */
  motion: boolean;
  /** False below 768px: no pinning and no WebGL, use the static fallback. */
  desktop: boolean;
}

/**
 * Runs `setup` inside a GSAP matchMedia scope for one scene.
 *
 * Everything created in `setup` (timelines, ScrollTriggers) is reverted automatically when
 * the component unmounts or the media conditions change, so scenes never leak triggers
 * (including under React StrictMode's double mount). `setup` may return its own cleanup.
 */
export function useScrollScene(
  ref: RefObject<HTMLElement | null>,
  setup: (api: SceneApi) => void | (() => void),
  deps: DependencyList = []
): void {
  useLayoutEffect(() => {
    const scope = ref.current;
    if (!scope) return;

    const mm = gsap.matchMedia();
    mm.add(
      { motion: "(prefers-reduced-motion: no-preference)", desktop: "(min-width: 768px)" },
      (context) => {
        const conditions = (context.conditions ?? {}) as { motion?: boolean; desktop?: boolean };
        return setup({
          gsap,
          ScrollTrigger,
          scope,
          motion: Boolean(conditions.motion),
          desktop: Boolean(conditions.desktop),
        });
      },
      scope
    );
    return () => mm.revert();
    // `setup` is intentionally not a dependency: callers pass an inline function.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
