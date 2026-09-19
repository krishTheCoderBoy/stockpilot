import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  Warehouse,
  Boxes,
  ArrowLeftRight,
  Truck,
  ClipboardList,
  Settings,
  ChevronsLeft,
} from "lucide-react";

const NAV_SECTIONS = [
  {
    label: "Inventory",
    items: [
      { to: "/", label: "Dashboard", icon: LayoutDashboard },
      { to: "/products", label: "Products", icon: Package },
      { to: "/warehouses", label: "Warehouses", icon: Warehouse },
      { to: "/inventory", label: "Stock", icon: Boxes },
      { to: "/movements", label: "Movements", icon: ArrowLeftRight },
    ],
  },
  {
    label: "Procurement",
    items: [
      { to: "/suppliers", label: "Suppliers", icon: Truck },
      { to: "/purchase-orders", label: "Purchase Orders", icon: ClipboardList },
    ],
  },
  {
    label: "System",
    items: [{ to: "/settings", label: "Settings", icon: Settings }],
  },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`flex h-screen flex-col border-r border-border bg-surface transition-[width] duration-200 ${
        collapsed ? "w-16" : "w-60"
      }`}
    >
      <div className="flex items-center justify-between px-4 py-4">
        {!collapsed && (
          <span className="font-mono text-sm font-medium text-accent">StockPilot</span>
        )}
        <button
          onClick={() => setCollapsed((v) => !v)}
          aria-label="Toggle sidebar"
          className="text-text-muted hover:text-text transition-colors"
        >
          <ChevronsLeft
            size={16}
            className={`transition-transform duration-200 ${collapsed ? "rotate-180" : ""}`}
          />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-2">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label} className="mb-4">
            {!collapsed && (
              <p className="px-3 py-2 text-xs text-text-muted">{section.label}</p>
            )}
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-sm px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? "bg-accent/10 text-accent"
                      : "text-text-muted hover:bg-ink hover:text-text"
                  }`
                }
              >
                <item.icon size={16} className="shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}