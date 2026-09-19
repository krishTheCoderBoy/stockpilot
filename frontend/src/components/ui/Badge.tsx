type BadgeTone = "neutral" | "accent" | "flow" | "danger";

interface BadgeProps {
  children: React.ReactNode;
  tone?: BadgeTone;
}

const toneStyles: Record<BadgeTone, string> = {
  neutral: "bg-surface border-border text-text-muted",
  accent: "bg-accent/10 border-accent/30 text-accent",
  flow: "bg-flow/10 border-flow/30 text-flow",
  danger: "bg-danger/10 border-danger/30 text-danger",
};

export function Badge({ children, tone = "neutral" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-sm border px-2 py-0.5 font-mono text-xs ${toneStyles[tone]}`}
    >
      {children}
    </span>
  );
}