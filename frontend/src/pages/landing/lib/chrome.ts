import { gsap } from "./gsap";

/**
 * The red logo and counter are unreadable over the teal water, so the persistent UI turns white
 * while the water is on screen (CSS: .lp-root[data-chrome="water"]).
 *
 * Scenes 5 and 6 only publish facts about themselves: `data-live` (set by SceneShell) and
 * `data-progress` (written by their timelines). This watcher turns those into one decision, every
 * frame, so the answer is right whatever order a fast scroll updates the scenes in.
 */
export function watchWaterChrome(root: HTMLElement): () => void {
  const read = (id: string) => {
    const scene = root.querySelector<HTMLElement>(id);
    return { live: scene?.hasAttribute("data-live") ?? false, p: Number(scene?.dataset.progress ?? 0) };
  };

  const tick = () => {
    const s4 = read("#scene-4");
    const s5 = read("#scene-5");
    const s6 = read("#scene-6");
    // the sea rises over the end of scene 4's road, so the logo turns white a little before scene 5
    const onWater = s6.live ? s6.p < 0.45 : s5.live || (s4.live && s4.p > 0.86);
    if (onWater) root.dataset.chrome = "water";
    else delete root.dataset.chrome;
  };

  gsap.ticker.add(tick);
  return () => {
    gsap.ticker.remove(tick);
    delete root.dataset.chrome;
  };
}
