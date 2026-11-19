import { useCustomCursor } from "../hooks/useCustomCursor";

// 24px outline ring that follows the pointer. See useCustomCursor for behaviour.
export function CustomCursor() {
  const ref = useCustomCursor();
  return (
    <div ref={ref} className="lp-cursor is-hidden" aria-hidden>
      <span className="lp-cursor__ring" />
    </div>
  );
}
