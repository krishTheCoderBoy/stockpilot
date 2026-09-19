import { Bell, Search } from "lucide-react";
import { Dropdown } from "../ui/Dropdown";

interface TopbarProps {
  breadcrumb: string;
  onOpenCommandPalette: () => void;
}

export function Topbar({ breadcrumb }: TopbarProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border px-6">
      <p className="text-sm text-text-muted">{breadcrumb}</p>

      <div className="flex items-center gap-4">
        <button
          onClick={() => document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}
          className="flex items-center gap-2 rounded-sm border border-border bg-surface px-3 py-1.5 text-xs text-text-muted transition-colors hover:border-accent/50"
        >
          <Search size={14} />
          <span>Search</span>
          <kbd className="font-mono text-[10px] text-text-muted/70">⌘K</kbd>
        </button>

        <button aria-label="Notifications" className="relative text-text-muted hover:text-text transition-colors">
          <Bell size={18} />
          <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full bg-accent" />
        </button>

        <Dropdown
          trigger={
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/10 text-xs font-medium text-accent">
              KD
            </span>
          }
          items={[
            { label: "Profile", onClick: () => {} },
            { label: "Sign out", onClick: () => {}, danger: true },
          ]}
        />
      </div>
    </header>
  );
}