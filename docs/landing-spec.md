# StockPilot landing page spec

The specification below is reproduced verbatim from the brief. Notes on how it maps onto this codebase are at the end, under "Implementation notes", and are not part of the spec.

## DESIGN LANGUAGE

- Palette: navy #050B1F, white #FFFFFF, signal red #E5171F (single brand accent), teal #19B5B0 (water scenes), red→magenta→blue neon gradient only on the hero ring.
- Type: ultra-bold wide/extended grotesk for headlines (Unbounded or similar), ALL CAPS, tight leading, mixed white + red words in one headline. Tiny uppercase monospace labels (tracking +0.1em). Inter for body.
- Dark sections alternate with pure white sections. Flat vector illustrated vehicles on white, top-down photoreal ocean in water scenes.
- Persistent UI on every scene: logo wordmark top-left, small white pill CTA top-right, a small red scroll/section counter near top-left, custom ring cursor (24px outline, grows on hover, inverts on white sections).
- Motion: Lenis smooth scroll + GSAP ScrollTrigger, pinned scenes, scrub-driven (scrolling back reverses). Text reveals: split by line, masked, translateY(110%)→0, stagger 0.08, expo.out. Only animate transform/opacity. Respect prefers-reduced-motion. Mobile: no WebGL, static fallbacks.

## SCENE LIST

1 Hero (dark): dotted 3D globe + neon ring, headline "EVERY UNIT / OF THE STOCK", vertical mini-nav, ticker.

2 Warehouse (white): yellow telehandler lifts a red STOCKPILOT container, big red stat counter.

3 Truck (white + dark strip): truck carries container across screen, ghost watermark word parallax, 3 service columns.

4 Curved road (white): top-down truck follows an SVG path via MotionPath; 4 big text panels.

5 Ocean (teal): top-down ship, wake, frosted-glass callout cards.

6 Air (ocean→white): top-down cargo plane, headline partly behind wings.

7 Insights (dark): giant headline with RGB-split/velocity skew, 4 news rows.

8 FAQ (white): giant "ANSWERS", accordion, huge footer wordmark.

9 Final CTA (dark): "READY TO MOVE IT PROPERLY?", 3D/extruded look, a single Sign in button to /login (there is no public registration: an admin creates accounts).

## RULES

- Only touch the landing page and its components. Do not modify backend, auth logic, API clients, dashboard pages, or other routes. Keep /login working.
- No third-party branding. Use the StockPilot name and a simple red wordmark.
- Placeholder assets go in src/assets/landing/ with clear filenames so I can swap in generated art.

---

## Implementation notes (not part of the spec)

**Where things live**

- `src/pages/landing/Landing.tsx` composes the scenes and the persistent UI. `App.tsx` imports it for the `/` route; logged-in users are still redirected to `/dashboard` first.
- `src/pages/landing/landing.css` holds the landing-only design tokens (`--lp-*`), the Unbounded and Inter imports, and scene and cursor styles. Nothing is added to `tailwind.config.js`, `index.html` or `index.css`.
- `src/pages/landing/scenes/` has `Scene1Hero` to `Scene9Cta`, built on one shared `SceneShell` (pin, active-scene tracking). Replace a scene's body when you build it; keep using `useScrollScene` for its animation.
- `src/pages/landing/hooks/`: `useLenis` (smooth scroll wired into ScrollTrigger), `useScrollScene` (scoped, reduced-motion-aware, desktop/mobile-aware GSAP setup), `useCustomCursor`.
- `src/pages/landing/ui/`: `Logo`, `TopPill`, `SceneCounter`, `CustomCursor`.
- `src/assets/landing/`: placeholder art goes here; see its README for the expected filenames.
- The previous `src/pages/Landing.tsx` (Spline version) is left in place but no longer routed, so it can be restored by changing one import.

**Behaviour decisions**

- **Reduced motion:** Lenis is not started (native scroll), scenes are not pinned, and the cursor follows the pointer without easing. Scenes stack as plain sections.
- **Mobile (under 768px) and touch:** scenes use their static layout, no WebGL, and the custom cursor is not rendered.
- **Cursor inversion** is decided from the element under the pointer (`data-scene-theme`), not from the active scene, so the dark strip in scene 3 inverts correctly.
- **Animation rule:** only `transform` and `opacity`.

- **Hand-off scenes (3 and 4).** A scene marked `handoff` overlaps the last screen of the scene before it (`.lp-handoff`, margin-top -100svh). It stays transparent and invisible until its own pin starts, then shows a first frame identical to the previous scene's last frame, and the previous scene scrolls away unseen underneath. Scene 2 fades its words out at the end, and scene 3 redraws its last frame (floor, stack, telehandler, container) from the same rig functions. Scene 3 ends on clear white, so scene 4 starts from the same white page.
- **Scene 3** reuses scene 2's stage geometry; scene 4 follows `ROAD_D` with GSAP MotionPath (registered in `lib/gsap.ts`).

- **Scenes 5 and 6** share one water picture. `scenes/ocean/` holds the shader (`OceanCanvas.tsx`), the shared offset (`oceanState.ts`) and the WebM slot (`oceanSlot.ts`). Both scenes draw the same shader off the wall clock and the same offset, so the 5 to 6 hand-off is an identical frame. Scene 4 clears to white at its end and scene 5 fades the water in from white. The red logo and counter switch to white over the water (`lib/chrome.ts`).

- **Scenes 7-9** scroll normally except scene 7, which pins briefly while its rows rise in. `SceneShell` takes `pin={false}` for scenes 8 and 9. Scene 7's colour split and skew are driven by `trackScrollVelocity` (`lib/velocity.ts`, Lenis velocity, desktop only). The FAQ accordion follows the WAI-ARIA accordion pattern (`scenes/faq/Accordion.tsx`).
- **Polish pass:** `App.tsx` loads the landing page as a lazy chunk; the globe and water canvases are lazy chunks inside it. Water chrome (white logo and counter over the sea) is decided once per frame by `watchWaterChrome` in `lib/chrome.ts`.

**Registration**

There is no public sign-up: an admin creates accounts (`/settings/users/new`, behind `AdminRoute`). The landing page therefore only links to `/login`; the final CTA is a single Sign in button.

**Dependencies**

`gsap`, `lenis`, `three`, `@react-three/fiber`, `@react-three/drei`, plus `@types/three`. `framer-motion` was not added: the `motion` package already installed is the same library under its newer name (`motion/react`), so a second copy would only add weight.
