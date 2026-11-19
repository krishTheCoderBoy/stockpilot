import { sceneMeta } from "./data";
import { SceneShell } from "./SceneShell";

const meta = sceneMeta(7);

interface Insight {
  date: string;
  iso: string;
  title: string;
  tag: string;
}

// Placeholder content: realistic, but not real data.
const INSIGHTS: Insight[] = [
  { date: "06 Nov 2026", iso: "2026-11-06", title: "Cold-chain packaging cover falls below nine days", tag: "Low stock" },
  { date: "04 Nov 2026", iso: "2026-11-04", title: "PO-2291 received in full, three days ahead of promise", tag: "Procurement" },
  { date: "31 Oct 2026", iso: "2026-10-31", title: "Transfer from Rotterdam to Leeds cleared the dock in 40 minutes", tag: "Movement" },
  { date: "28 Oct 2026", iso: "2026-10-28", title: "Bay C cycle count closed with zero variance", tag: "Audit" },
];

// Plain and static on purpose: no pin, no scroll effects, nothing that moves.
export function Scene7Insights() {
  return (
    <SceneShell index={meta.index} name={meta.name} theme={meta.theme} pin={false} className="lp-in">
      <div className="lp-in__inner">
        <p className="lp-label lp-in__eyebrow">Insights</p>

        <h2 className="lp-display lp-in__title">
          <span className="lp-in__row">What&apos;s moving</span>
          <span className="lp-in__row">in your</span>
          <span className="lp-in__row lp-in__hot">stock</span>
        </h2>

        <ul className="lp-in__list">
          {INSIGHTS.map((item) => (
            <li key={item.iso} className="lp-in__row-item">
              <div className="lp-in__link">
                <time className="lp-label lp-in__date" dateTime={item.iso}>
                  {item.date}
                </time>
                <h3 className="lp-in__item">{item.title}</h3>
                <span className="lp-label lp-in__tag">{item.tag}</span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </SceneShell>
  );
}
