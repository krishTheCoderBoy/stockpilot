import "lenis/dist/lenis.css";
import "./landing.css";
import { useEffect, useRef } from "react";
import { useLenis } from "./hooks/useLenis";
import { watchWaterChrome } from "./lib/chrome";
import { ScrollTrigger } from "./lib/gsap";
import { Scene1Hero } from "./scenes/Scene1Hero";
import { Scene2Warehouse } from "./scenes/Scene2Warehouse";
import { Scene3Truck } from "./scenes/Scene3Truck";
import { Scene4CurvedRoad } from "./scenes/Scene4CurvedRoad";
import { Scene5Ocean } from "./scenes/Scene5Ocean";
import { Scene6Air } from "./scenes/Scene6Air";
import { Scene7Insights } from "./scenes/Scene7Insights";
import { Scene8Faq } from "./scenes/Scene8Faq";
import { Scene9Cta } from "./scenes/Scene9Cta";
import { CustomCursor } from "./ui/CustomCursor";
import { Logo } from "./ui/Logo";
import { TopPill } from "./ui/TopPill";

// Public landing page, shown at "/" to visitors who are not signed in (App.tsx redirects
// signed-in users to /dashboard). Spec: docs/landing-spec.md
export function Landing() {
  const rootRef = useRef<HTMLDivElement>(null);
  useLenis();

  useEffect(() => (rootRef.current ? watchWaterChrome(rootRef.current) : undefined), []);

  useEffect(() => {
    const previousTitle = document.title;
    document.title = "StockPilot";
    return () => {
      document.title = previousTitle;
    };
  }, []);

  useEffect(() => {
    // Pin positions depend on text size; measure again once the display fonts have loaded.
    let cancelled = false;
    void document.fonts?.ready.then(() => {
      if (!cancelled) ScrollTrigger.refresh();
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div ref={rootRef} className="lp-root">
      <Logo />
      <TopPill />
      <CustomCursor />

      <main>
        <Scene1Hero />
        <Scene2Warehouse />
        <Scene3Truck />
        <Scene4CurvedRoad />
        <Scene5Ocean />
        <Scene6Air />
        <Scene7Insights />
        <Scene8Faq />
        <Scene9Cta />
      </main>
    </div>
  );
}
