import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Alert } from "../ui/Alert";
import { Button } from "../ui/Button";
import { type PendingState } from "../../lib/chatTypes";

interface Props {
  pending: PendingState;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmationCard({ pending, onConfirm, onCancel }: Props) {
  const { action, status, message } = pending;
  const expiresAt = new Date(action.expires_at).getTime();
  const [now, setNow] = useState(() => Date.now());

  // Re-check once when the token runs out so the buttons disable themselves.
  useEffect(() => {
    if (status !== "awaiting") return;
    const remaining = expiresAt - Date.now();
    if (remaining <= 0) return;
    const timer = setTimeout(() => setNow(Date.now()), remaining + 250);
    return () => clearTimeout(timer);
  }, [status, expiresAt]);

  const expired = status === "awaiting" && now >= expiresAt;

  return (
    <div className="mt-2 rounded-md border border-accent/30 bg-accent/5 p-3">
      <div className="mb-2 flex items-center gap-2 text-xs font-medium text-accent">
        <ShieldCheck size={14} /> Needs your confirmation
      </div>
      <p className="text-sm text-text">{action.summary}</p>

      <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
        {Object.entries(action.details).map(([label, value]) => (
          <div key={label} className="contents">
            <dt className="text-text-muted">{label}</dt>
            <dd className="break-words text-text">{value}</dd>
          </div>
        ))}
      </dl>

      {(status === "awaiting" || status === "confirming") && (
        <div className="mt-3 flex items-center gap-2">
          <Button onClick={onConfirm} disabled={status === "confirming" || expired}>
            {status === "confirming" ? "Confirming..." : "Confirm"}
          </Button>
          <Button variant="ghost" onClick={onCancel} disabled={status === "confirming"}>
            Cancel
          </Button>
          {expired && <span className="text-xs text-danger">Expired. Ask me to prepare it again.</span>}
        </div>
      )}

      {status === "confirmed" && (
        <div className="mt-3">
          <Alert tone="success">{message}</Alert>
        </div>
      )}
      {status === "failed" && (
        <div className="mt-3">
          <Alert tone="danger">{message}</Alert>
        </div>
      )}
      {status === "cancelled" && <p className="mt-3 text-xs text-text-muted">{message}</p>}
    </div>
  );
}
