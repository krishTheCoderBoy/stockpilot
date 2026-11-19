import truckTopDown from "../../../assets/landing/truck-topdown.webp";
import type { SceneApi } from "../hooks/useScrollScene";
import { useFullMotion } from "../lib/mode";
import { MaskedLines } from "../ui/MaskedLines";
import { ROAD_D, ROAD_WIDTH } from "./road/roadGeometry";
import { sceneMeta } from "./data";
import { SceneShell, type BuildResult } from "./SceneShell";

const meta = sceneMeta(4);

// One stage for the road and the truck. The road is a straight, vertical run down the middle of
// the page; it starts above and ends below the 1600 x 900 view so the truck is never seen popping
// in or out, even on very tall screens. At its end the sea rises to meet it (the next scene).
const STAGE = { width: 1600, height: 900 } as const;
// art: truck-topdown.webp is 900 x 305 (cab on the right), drawn here at 300 x 102. The cone is
// drawn in code; the unseen rect behind balances the group's box so the truck, not the cone,
// is what rides the path.
const TRUCK = { width: 300, height: 102 } as const;
const CONE_LENGTH = 190;
const CONE_SPREAD = 52;
const CONE_POINTS = [
  [TRUCK.width, TRUCK.height * 0.3],
  [TRUCK.width + CONE_LENGTH, -CONE_SPREAD],
  [TRUCK.width + CONE_LENGTH, TRUCK.height + CONE_SPREAD],
  [TRUCK.width, TRUCK.height * 0.7],
]
  .map((point) => point.join(","))
  .join(" ");
// Where the truck sits when nothing is scrolling it (mobile, reduced motion).
const STATIC_TRANSFORM = `translate(800 450) rotate(90) translate(${-TRUCK.width / 2} ${-TRUCK.height / 2})`;

interface Panel {
  lines: ReactNodeLine[];
  text: string;
  side: "left" | "right";
}
type ReactNodeLine = string | { red: string };

const PANELS: Panel[] = [
  {
    lines: ["Reliable", "at every", { red: "stop" }],
    text: "Every pickup and drop-off is confirmed where it happens, so nothing moves without a record.",
    side: "left",
  },
  {
    lines: ["Live", { red: "stock" }, "tracking"],
    text: "Watch quantities change as goods ship and arrive, with no waiting for an overnight count.",
    side: "right",
  },
  {
    lines: ["A network", "on every", { red: "lane" }],
    text: "Suppliers, warehouses and carriers sit in one place, so each route has a name beside it.",
    side: "left",
  },
  {
    lines: ["People,", "round the", { red: "clock" }],
    text: "Real people watching the floor day and night, ready to step in when a shipment needs one.",
    side: "right",
  },
];

// The truck crosses the screen between about 0.2 and 0.8 of the scene; the four panels share that
// stretch, and the sea rises over the rest.
const PANELS_END = 0.8;
const PANEL_SPAN = PANELS_END / PANELS.length;

function buildRoadTimeline({ gsap, scope }: SceneApi): BuildResult | void {
  const truck = scope.querySelector('[data-rd="truck"]');
  const path = scope.querySelector<SVGPathElement>('[data-rd="path"]');
  const sea = scope.querySelector('[data-rd="sea"]');
  const foam = scope.querySelector('[data-rd="foam"]');
  if (!truck || !path) return;

  const panels = Array.from(scope.querySelectorAll<HTMLElement>('[data-rd="panel"]'));

  panels.forEach((panel) => {
    gsap.set(panel.querySelectorAll("[data-reveal-line]"), { yPercent: 110 });
    gsap.set(panel.querySelectorAll('[data-rd="text"], [data-rd="bar"]'), { opacity: 0 });
    gsap.set(panel.querySelector('[data-rd="fill"]'), { scaleY: 0 });
  });
  gsap.set(sea, { yPercent: 100 });

  const timeline = gsap.timeline({
    paused: true,
    defaults: { ease: "none" },
    // published for lib/chrome.ts, which turns the logo white once the sea covers the page
    onUpdate: () => {
      scope.dataset.progress = String(timeline.progress());
    },
  });
  timeline
    // the truck follows the path; the cone and the body turn with it
    .to(
      truck,
      {
        motionPath: { path, align: path, alignOrigin: [0.5, 0.5], autoRotate: true },
        duration: 1,
      },
      0
    );

  panels.forEach((panel, i) => {
    const start = i * PANEL_SPAN;
    const last = i === panels.length - 1;
    const lines = panel.querySelectorAll("[data-reveal-line]");
    const fill = panel.querySelector('[data-rd="fill"]');
    const rest = panel.querySelectorAll('[data-rd="text"], [data-rd="bar"]');

    timeline
      .to(lines, { yPercent: 0, duration: 0.05, stagger: 0.012, ease: "expo.out" }, start + 0.01)
      .to(rest, { opacity: 1, duration: 0.04, ease: "power2.out" }, start + 0.035)
      .to(fill, { scaleY: 1, duration: PANEL_SPAN - 0.04 }, start + 0.03);

    if (!last) {
      const out = start + PANEL_SPAN - 0.035;
      timeline
        .to(lines, { yPercent: -110, duration: 0.03, stagger: 0.008, ease: "power2.in" }, out)
        .to(rest, { opacity: 0, duration: 0.025 }, out);
    }
  });

  // Hand-off to scene 5: the last words clear, then the sea rises from the bottom edge where the road
  // ends, covering everything. Scene 5 opens on that same water.
  timeline
    .to(scope.querySelectorAll('[data-rd="panel"]'), { opacity: 0, duration: 0.03, ease: "power1.in" }, 0.8)
    .to(sea, { yPercent: 0, duration: 0.16, ease: "sine.inOut" }, 0.82)
    // the foam along its leading edge drifts sideways as the water climbs
    .fromTo(foam, { xPercent: 0 }, { xPercent: -8, duration: 0.16, ease: "none" }, 0.82)
    .to({}, { duration: 0 }, 1);

  return {
    timeline,
    // static layout if the visitor switches to mobile or reduced motion
    cleanup: () => {
      delete scope.dataset.progress;
      gsap.set(truck, { clearProps: "all" });
    },
  };
}

function renderLine(line: ReactNodeLine) {
  return typeof line === "string" ? line : <span className="lp-red">{line.red}</span>;
}

export function Scene4CurvedRoad() {
  const full = useFullMotion();

  return (
    <SceneShell
      index={meta.index}
      name={meta.name}
      theme={meta.theme}
      pinLength="500%"
      className={`lp-rd ${full ? "lp-handoff" : "is-static"}`}
      handoff={full}
      build={buildRoadTimeline}
    >
      <svg
        className="lp-rd__stage"
        viewBox={`0 0 ${STAGE.width} ${STAGE.height}`}
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
        focusable="false"
      >
        <g data-rd="road">
          <path d={ROAD_D} fill="none" stroke="#dfe3ec" strokeWidth={ROAD_WIDTH + 14} strokeLinecap="butt" />
          <path data-rd="path" d={ROAD_D} fill="none" stroke="#0b0e17" strokeWidth={ROAD_WIDTH} strokeLinecap="butt" />
          <path d={ROAD_D} fill="none" stroke="#ffffff" strokeOpacity={0.8} strokeWidth={5} strokeDasharray="36 28" />
        </g>

        <g data-rd="truck" transform={full ? undefined : STATIC_TRANSFORM}>
          <defs>
            <linearGradient id="lp-rd-cone" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0" stopColor="#ffd84a" stopOpacity="0.7" />
              <stop offset="1" stopColor="#ffd84a" stopOpacity="0" />
            </linearGradient>
          </defs>
          {/* never painted: balances the cone so the truck is the centre of the group */}
          <rect x={-CONE_LENGTH} y={-CONE_SPREAD} width={CONE_LENGTH} height={TRUCK.height + CONE_SPREAD * 2} fill="none" />
          <polygon points={CONE_POINTS} fill="url(#lp-rd-cone)" />
          <image href={truckTopDown} width={TRUCK.width} height={TRUCK.height} />
        </g>
      </svg>

      {/* the sea that rises at the end of the road */}
      {full && (
        <div className="lp-rd__sea" data-rd="sea" aria-hidden="true">
          {/* foam and a soft shallow-water edge along the top, so the sea arrives as a wave, not a hard line */}
          <svg className="lp-rd__foam" data-rd="foam" viewBox="0 0 1600 140" preserveAspectRatio="none" focusable="false">
            <defs>
              <linearGradient id="lp-foam-a" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#ffffff" stopOpacity="0" />
                <stop offset="0.55" stopColor="#ffffff" stopOpacity="0.9" />
                <stop offset="1" stopColor="#bff3ef" stopOpacity="0.55" />
              </linearGradient>
              <linearGradient id="lp-foam-b" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#d8fbf7" stopOpacity="0" />
                <stop offset="1" stopColor="#d8fbf7" stopOpacity="0.7" />
              </linearGradient>
            </defs>
            <path
              d="M-200 140 V74 Q-100 36 0 70 T200 70 T400 70 T600 70 T800 70 T1000 70 T1200 70 T1400 70 T1600 70 T1800 70 V140 Z"
              fill="url(#lp-foam-b)"
            />
            <path
              d="M-200 140 V96 Q-120 62 -40 92 T120 92 T280 92 T440 92 T600 92 T760 92 T920 92 T1080 92 T1240 92 T1400 92 T1560 92 T1720 92 V140 Z"
              fill="url(#lp-foam-a)"
            />
          </svg>
        </div>
      )}

      <div className="lp-rd__panels">
        {PANELS.map((panel, i) => (
          <article key={i} className={`lp-rd__panel lp-rd__panel--${panel.side}`} data-rd="panel">
            <span className="lp-rd__bar" data-rd="bar" aria-hidden="true">
              <i data-rd="fill" />
            </span>
            <h2 className="lp-display lp-rd__title">
              <MaskedLines lines={panel.lines.map(renderLine)} />
            </h2>
            <p className="lp-rd__text" data-rd="text">
              {panel.text}
            </p>
          </article>
        ))}
      </div>
    </SceneShell>
  );
}

