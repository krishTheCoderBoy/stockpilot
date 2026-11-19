import { getLenis } from "../hooks/useLenis";

// Simple red wordmark, top-left on every scene. Clicking scrolls back to the top.
export function Logo() {
  function scrollToTop() {
    const lenis = getLenis();
    if (lenis) lenis.scrollTo(0, { duration: 1.4 });
    else window.scrollTo({ top: 0 });
  }

  return (
    <button type="button" onClick={scrollToTop} aria-label="StockPilot, back to top" className="lp-logo">
      STOCKPILOT
    </button>
  );
}
