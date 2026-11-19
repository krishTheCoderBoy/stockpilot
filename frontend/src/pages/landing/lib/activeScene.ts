// Which scene is currently in view. A tiny external store instead of React context:
// ScrollTrigger callbacks live outside React, and only the counter needs to re-render.
import { useSyncExternalStore } from "react";

let active = 1;
const listeners = new Set<() => void>();

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function setActiveScene(index: number): void {
  if (index === active) return;
  active = index;
  listeners.forEach((listener) => listener());
}

export function useActiveScene(): number {
  return useSyncExternalStore(subscribe, () => active, () => 1);
}
