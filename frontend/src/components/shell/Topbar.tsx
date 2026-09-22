import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { Bell, Search, Sun, Moon } from "lucide-react";
import { Dropdown } from "../ui/Dropdown";
import { useTheme } from "../../context/ThemeContext";
import { useAuth } from "../../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";

interface TopbarProps {
  breadcrumb: string;
  onOpenCommandPalette: () => void;
}

interface Notification {
  type: string;
  message: string;
}

const ROLE_LABEL: Record<string, string> = {
  ADMIN: "Admin",
  INVENTORY_MANAGER: "Inventory Manager",
  PROCUREMENT_MANAGER: "Procurement Manager",
};

export function Topbar({ breadcrumb }: TopbarProps) {
  const { theme, toggleTheme } = useTheme();
  const { role, logout } = useAuth();
  const navigate = useNavigate();
  const [notifOpen, setNotifOpen] = useState(false);

  const { data: notifications } = useQuery<Notification[]>({
    queryKey: ["notifications"],
    queryFn: async () => (await api.get("/dashboard/notifications")).data,
    refetchInterval: 60000,
  });

  const initials = role ? role.slice(0, 2) : "?";

  function handleLogout() {
    logout();
    navigate("/login");
  }

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

        <button onClick={toggleTheme} aria-label="Toggle theme" className="text-text-muted hover:text-text transition-colors">
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <div className="relative">
          <button
            onClick={() => setNotifOpen((v) => !v)}
            aria-label="Notifications"
            className="relative text-text-muted hover:text-text transition-colors"
          >
            <Bell size={18} />
            {notifications && notifications.length > 0 && (
              <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full bg-accent" />
            )}
          </button>
          <AnimatePresence>
            {notifOpen && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.12 }}
                className="absolute right-0 z-40 mt-2 w-72 rounded-sm border border-border bg-surface/95 backdrop-blur-md py-2 shadow-xl"
              >
                <p className="px-3 pb-2 text-xs text-text-muted">Notifications</p>
                {notifications && notifications.length > 0 ? (
                  notifications.map((n, i) => (
                    <div key={i} className="border-t border-border px-3 py-2 text-xs text-text">
                      {n.message}
                    </div>
                  ))
                ) : (
                  <p className="px-3 py-2 text-xs text-text-muted">Nothing to report</p>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <Dropdown
          trigger={
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/10 text-xs font-medium text-accent">
                {initials}
              </span>
              <span className="hidden text-xs text-text-muted sm:block">
                {role ? ROLE_LABEL[role] : ""}
              </span>
            </div>
          }
          items={[
            { label: "Profile", onClick: () => navigate("/profile") },
            { label: "Settings", onClick: () => navigate("/settings") },
            { label: "Sign out", onClick: handleLogout, danger: true },
          ]}
        />
      </div>
    </header>
  );
}