import { useEffect, useRef, type RefObject } from "react";
import { gsap, prefersReducedMotion } from "../lib/gsap";

const HOVER_TARGETS = 'a, button, [role="button"], [data-cursor="hover"], input, textarea, select, summary';

/**
 * Drives the custom ring cursor. The returned ref goes on the cursor element, which the
 * hook moves and toggles two classes on:
 *   is-hover     the pointer is over something clickable (the ring grows)
 *   is-inverted  the pointer is over a white section (the ring turns navy)
 * Touch and coarse-pointer devices keep the native cursor and the element is hidden.
 */
export function useCustomCursor(): RefObject<HTMLDivElement | null> {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const cursor = ref.current;
    if (!cursor) return;

    const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
    if (!finePointer.matches) {
      cursor.style.display = "none";
      return;
    }

    const root = cursor.closest<HTMLElement>(".lp-root");
    root?.classList.add("lp-has-cursor");

    gsap.set(cursor, { xPercent: -50, yPercent: -50 });
    const reduced = prefersReducedMotion();
    const moveX = reduced ? null : gsap.quickTo(cursor, "x", { duration: 0.18, ease: "power3.out" });
    const moveY = reduced ? null : gsap.quickTo(cursor, "y", { duration: 0.18, ease: "power3.out" });

    let frame = 0;
    let pointer = { x: 0, y: 0 };

    // Which theme is under the pointer is checked at most once per frame.
    const syncTheme = () => {
      frame = 0;
      const theme = document
        .elementFromPoint(pointer.x, pointer.y)
        ?.closest<HTMLElement>("[data-scene-theme]")?.dataset.sceneTheme;
      cursor.classList.toggle("is-inverted", theme === "light");
    };

    const onMove = (event: PointerEvent) => {
      pointer = { x: event.clientX, y: event.clientY };
      cursor.classList.remove("is-hidden");
      if (moveX && moveY) {
        moveX(pointer.x);
        moveY(pointer.y);
      } else {
        gsap.set(cursor, { x: pointer.x, y: pointer.y });
      }
      if (!frame) frame = requestAnimationFrame(syncTheme);
    };

    const onOver = (event: PointerEvent) => {
      const target = event.target as Element | null;
      cursor.classList.toggle("is-hover", Boolean(target?.closest(HOVER_TARGETS)));
    };

    const onLeaveWindow = () => cursor.classList.add("is-hidden");

    window.addEventListener("pointermove", onMove, { passive: true });
    document.addEventListener("pointerover", onOver, { passive: true });
    document.documentElement.addEventListener("mouseleave", onLeaveWindow);

    return () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerover", onOver);
      document.documentElement.removeEventListener("mouseleave", onLeaveWindow);
      root?.classList.remove("lp-has-cursor");
    };
  }, []);

  return ref;
}
