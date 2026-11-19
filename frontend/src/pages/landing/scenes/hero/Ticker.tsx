const ITEMS = [
  "Live ledger",
  "Every movement recorded",
  "Real-time stock",
  "One source of truth",
  "Forecast-ready history",
];

// A slow one-line marquee, top-left. The list is doubled so the loop is seamless, and the
// motion is a CSS transform (stopped for reduced motion in landing.css). Decorative only.
export function Ticker() {
  return (
    <div className="lp-ticker lp-label" data-hero="chrome" aria-hidden="true">
      <div className="lp-ticker__track">
        {[...ITEMS, ...ITEMS].map((item, i) => (
          <span key={i} className="lp-ticker__item">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
