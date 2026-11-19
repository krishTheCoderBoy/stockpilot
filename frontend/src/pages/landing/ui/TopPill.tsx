import { Link } from "react-router-dom";

// Small white pill, top-right on every scene. Points at /login: there is no public sign-up,
// accounts are created by an admin.
export function TopPill() {
  return (
    <Link to="/login" className="lp-pill">
      Sign in
      <span aria-hidden>→</span>
    </Link>
  );
}
