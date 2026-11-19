import type { ReactNode } from "react";

/**
 * One masked wrapper per line, so a line can slide up from below its own baseline
 * (REVEAL in lib/reveal.ts). Lines are written out by hand rather than detected, which keeps
 * the headline breaks exactly as designed.
 */
export function MaskedLines({ lines }: { lines: ReactNode[] }) {
  return (
    <>
      {lines.map((line, i) => (
        <span key={i} className="lp-line">
          <span className="lp-line__inner" data-reveal-line>
            {line}
          </span>
        </span>
      ))}
    </>
  );
}
