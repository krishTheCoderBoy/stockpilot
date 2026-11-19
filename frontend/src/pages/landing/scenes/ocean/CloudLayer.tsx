import { CLOUDS } from "./clouds";

/** The cloud sprites; `applyClouds` (clouds.ts) moves and fades them. */
export function CloudLayer({ dataKey }: { dataKey: string }) {
  return (
    <div className="lp-clouds" data-clouds={dataKey} aria-hidden="true" style={{ opacity: 0 }}>
      {CLOUDS.map((cloud, i) => (
        <img
          key={i}
          src={cloud.src}
          alt=""
          draggable={false}
          loading="lazy"
          decoding="async"
          style={{ left: `${cloud.left}vw`, top: `${cloud.top}vh`, width: `${cloud.width}vw` }}
        />
      ))}
    </div>
  );
}
