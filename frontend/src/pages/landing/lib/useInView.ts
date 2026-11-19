import { useEffect, useState, type RefObject } from "react";

/** Whether the element is (nearly) on screen. Used to pause WebGL while a scene is off screen. */
export function useInView(ref: RefObject<Element | null>, rootMargin = "200px"): boolean {
  const [inView, setInView] = useState(true);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const observer = new IntersectionObserver(([entry]) => setInView(entry.isIntersecting), { rootMargin });
    observer.observe(element);
    return () => observer.disconnect();
  }, [ref, rootMargin]);

  return inView;
}
