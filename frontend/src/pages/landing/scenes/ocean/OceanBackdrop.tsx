import { lazy, Suspense, useRef, useState } from "react";
import { hasWebGL, useFullMotion } from "../../lib/mode";
import { useInView } from "../../lib/useInView";
import { OCEAN_VIDEO_SRC } from "./oceanSlot";

const OceanCanvas = lazy(() => import("./OceanCanvas"));

/**
 * The water behind scenes 5 and 6: a looping video if one is slotted in (see oceanSlot.ts),
 * otherwise the animated shader. Mobile, reduced motion and no-WebGL get the still photo, which
 * also shows while the shader loads.
 */
export function OceanBackdrop({ dataKey }: { dataKey: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref);
  const [ready, setReady] = useState(false);
  const animated = useFullMotion() && hasWebGL();

  return (
    <div ref={ref} className="lp-ocean" data-ocean={dataKey} aria-hidden="true">
      <div className={`lp-ocean__still${animated && ready ? " is-hidden" : ""}`} />
      {OCEAN_VIDEO_SRC && animated ? (
        <video className="lp-ocean__video" src={OCEAN_VIDEO_SRC} autoPlay muted loop playsInline />
      ) : (
        animated && (
          <Suspense fallback={null}>
            <OceanCanvas active={inView} onReady={() => setReady(true)} />
          </Suspense>
        )
      )}
    </div>
  );
}
