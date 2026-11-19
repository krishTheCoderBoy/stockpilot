export type SceneTheme = "dark" | "light" | "teal";

export interface SceneMeta {
  index: number;
  name: string;
  /** Background family of the scene; the cursor and chrome react to it. */
  theme: SceneTheme;
}

// Order and themes follow docs/landing-spec.md (SCENE LIST).
export const SCENES: readonly SceneMeta[] = [
  { index: 1, name: "Hero", theme: "dark" },
  { index: 2, name: "Warehouse", theme: "light" },
  { index: 3, name: "Truck", theme: "light" },
  { index: 4, name: "Curved road", theme: "light" },
  { index: 5, name: "Ocean", theme: "teal" },
  { index: 6, name: "Air", theme: "teal" },
  { index: 7, name: "Insights", theme: "dark" },
  { index: 8, name: "FAQ", theme: "light" },
  { index: 9, name: "Final CTA", theme: "dark" },
];

export const SCENE_COUNT = SCENES.length;

export function sceneMeta(index: number): SceneMeta {
  const meta = SCENES.find((scene) => scene.index === index);
  if (!meta) throw new Error(`Unknown landing scene ${index}`);
  return meta;
}
