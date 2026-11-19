import { getLenis } from "../hooks/useLenis";
import { ScrollTrigger } from "./gsap";

/**
 * Scroll to the start of a scene. Pinned scenes live inside pin-spacers, so the element's
 * own offset is wrong; the ScrollTrigger that pins it knows the real start position.
 */
export function scrollToScene(index: number): void {
  const id = `scene-${index}`;
  const trigger = ScrollTrigger.getAll().find((t) => t.trigger instanceof HTMLElement && t.trigger.id === id);
  const element = document.getElementById(id);
  const top = trigger ? trigger.start : element ? element.getBoundingClientRect().top + window.scrollY : null;
  if (top === null) return;

  const lenis = getLenis();
  if (lenis) lenis.scrollTo(top, { duration: 1.6 });
  else window.scrollTo({ top, behavior: "smooth" });
}
