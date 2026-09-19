import { type LucideIcon } from "lucide-react";
import { Button } from "./Button";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ icon: Icon, title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <Icon size={32} className="text-text-muted" />
      <div>
        <p className="text-sm font-medium text-text">{title}</p>
        <p className="mt-1 text-sm text-text-muted">{description}</p>
      </div>
      {actionLabel && onAction && (
        <Button variant="secondary" onClick={onAction} className="mt-2">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}