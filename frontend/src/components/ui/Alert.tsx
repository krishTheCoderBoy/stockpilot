import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";

type AlertTone = "info" | "success" | "warning" | "danger";

const config: Record<AlertTone, { icon: React.ElementType; classes: string }> = {
  info: { icon: Info, classes: "border-flow/30 bg-flow/5 text-flow" },
  success: { icon: CheckCircle2, classes: "border-flow/30 bg-flow/5 text-flow" },
  warning: { icon: AlertTriangle, classes: "border-accent/30 bg-accent/5 text-accent" },
  danger: { icon: XCircle, classes: "border-danger/30 bg-danger/5 text-danger" },
};

export function Alert({ tone = "info", children }: { tone?: AlertTone; children: React.ReactNode }) {
  const { icon: Icon, classes } = config[tone];
  return (
    <div className={`flex items-start gap-3 rounded-sm border px-4 py-3 text-sm ${classes}`}>
      <Icon size={18} className="mt-0.5 shrink-0" />
      <div className="text-text">{children}</div>
    </div>
  );
}