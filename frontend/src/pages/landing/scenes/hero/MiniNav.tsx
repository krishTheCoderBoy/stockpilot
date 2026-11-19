import { scrollToScene } from "../../lib/scrollToScene";

// Vertical mini-nav on the right edge. Scenes 3 to 9 are still placeholders, so the items
// point at the scenes they will eventually describe.
const ITEMS = [
  { label: "Product", scene: 2 },
  { label: "Inventory", scene: 3 },
  { label: "Procurement", scene: 5 },
  { label: "Analytics", scene: 7 },
  { label: "Contact", scene: 9 },
];

export function MiniNav() {
  return (
    <nav className="lp-mininav" data-hero="chrome" aria-label="Sections">
      <ul>
        {ITEMS.map(({ label, scene }, i) => (
          <li key={label}>
            <button type="button" className="lp-label lp-mininav__item" onClick={() => scrollToScene(scene)}>
              <span className="lp-mininav__index">{String(i + 1).padStart(2, "0")}</span>
              {label}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
