import { type ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { CommandPalette } from "../ui/CommandPalette";

export function AppShell({ children, breadcrumb }: { children: ReactNode; breadcrumb: string }) {
  return (
    <div className="flex h-screen bg-ink">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar breadcrumb={breadcrumb} onOpenCommandPalette={() => {}} />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
      <CommandPalette />
    </div>
  );
}