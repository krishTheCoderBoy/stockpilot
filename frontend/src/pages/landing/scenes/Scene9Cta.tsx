import { Link } from "react-router-dom";
import { sceneMeta } from "./data";
import { SceneShell } from "./SceneShell";

const meta = sceneMeta(9);

// Plain and static on purpose: no reveal, no distortion, nothing that moves.
export function Scene9Cta() {
  return (
    <SceneShell index={meta.index} name={meta.name} theme={meta.theme} pin={false} className="lp-cta">
      <div className="lp-cta__inner">
        <h2 className="lp-display lp-cta__title">
          <span className="lp-cta__row">Ready to</span>
          <span className="lp-cta__row">move it</span>
          <span className="lp-cta__row lp-red">properly?</span>
        </h2>

        <p className="lp-label lp-cta__line">Inventory · Procurement · Suppliers, in one place</p>

        <div className="lp-cta__actions">
          <Link to="/login" className="lp-cta__btn lp-cta__btn--primary">
            Sign in
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>
    </SceneShell>
  );
}
