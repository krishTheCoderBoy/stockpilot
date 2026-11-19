import Lenis from "lenis";
import { useEffect } from "react";
import { gsap, prefersReducedMotion, ScrollTrigger } from "../lib/gsap";

let instance: Lenis | null = null;

/** The running Lenis instance, or null (reduced motion, or the landing page is not mounted). */
export function getLenis(): Lenis | null {
  return instance;
}

/**
 * Smooth scrolling, driven by GSAP's ticker so Lenis and ScrollTrigger share one clock.
 * With prefers-reduced-motion the page keeps native scrolling.
 */
export function useLenis(): void {
  useEffect(() => {
    if (prefersReducedMotion()) return;

    const lenis = new Lenis({
      duration: 1.15,
      // expo.out, to match the text-reveal easing
      easing: (t: number) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });
    instance = lenis;

    lenis.on("scroll", ScrollTrigger.update);
    const tick = (time: number) => lenis.raf(time * 1000);
    gsap.ticker.add(tick);
    // Lenis already smooths motion; GSAP's lag smoothing would make scrubbed scenes jump.
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(tick);
      gsap.ticker.lagSmoothing(500, 33); // GSAP's defaults
      lenis.destroy();
      // destroy() leaves its base class on <html>; the dashboard should not inherit it
      document.documentElement.classList.remove("lenis", "lenis-smooth", "lenis-scrolling", "lenis-stopped");
      if (instance === lenis) instance = null;
    };
  }, []);
}
