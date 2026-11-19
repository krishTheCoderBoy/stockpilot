import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import type { AxiosInstance } from "axios";
import { inventoryApi, procurementApi } from "../../lib/api";
import {
  type Movement,
  type Product,
  type PurchaseOrder,
  type Supplier,
  type Warehouse,
} from "../../lib/queries";

interface CommandItem {
  label: string;
  path: string;
}

interface PaletteItem {
  key: string;
  label: string;
  hint?: string;
  path: string;
}

interface PaletteSection {
  title: string;
  items: PaletteItem[];
}

const COMMANDS: CommandItem[] = [
  { label: "Dashboard", path: "/" },
  { label: "Products", path: "/products" },
  { label: "Warehouses", path: "/warehouses" },
  { label: "Stock", path: "/inventory" },
  { label: "Movements", path: "/movements" },
  { label: "Suppliers", path: "/suppliers" },
  { label: "Purchase Orders", path: "/purchase-orders" },
  { label: "Planning", path: "/planning" },
  { label: "Settings", path: "/settings" },
];

const DEBOUNCE_MS = 250;
// Below two characters a full-text query matches too broadly to be useful.
const MIN_QUERY_LENGTH = 2;
const RESULTS_PER_GROUP = 5;

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

// One independent query per entity: a failing service only empties its own group.
function useEntitySearch<T>(entity: string, client: AxiosInstance, path: string, term: string) {
  return useQuery<T[]>({
    queryKey: ["palette-search", entity, term],
    queryFn: async () => (await client.get(path, { params: { q: term, limit: RESULTS_PER_GROUP } })).data,
    enabled: term.length >= MIN_QUERY_LENGTH,
    staleTime: 30_000,
    retry: false,
  });
}

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen((v) => !v);
      }
      if (e.key === "Escape") setIsOpen(false);
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // The dialog only exists while open, so its query and selection reset on every open
  // and nothing is fetched while it is closed.
  return <AnimatePresence>{isOpen && <PaletteDialog onClose={() => setIsOpen(false)} />}</AnimatePresence>;
}

function PaletteDialog({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState({ index: 0, keys: "" });
  const navigate = useNavigate();
  const prefersReducedMotion = useReducedMotion();

  const term = useDebouncedValue(query.trim(), DEBOUNCE_MS);

  const products = useEntitySearch<Product>("products", inventoryApi, "/products/search", term);
  const warehouses = useEntitySearch<Warehouse>("warehouses", inventoryApi, "/warehouses/search", term);
  const suppliers = useEntitySearch<Supplier>("suppliers", procurementApi, "/suppliers/search", term);
  const purchaseOrders = useEntitySearch<PurchaseOrder>("purchase-orders", procurementApi, "/purchase-orders/search", term);
  const movements = useEntitySearch<Movement>("movements", inventoryApi, "/inventory-movements/search", term);

  // A movement only carries ids; reuse the lists the pages already cache (same keys) to
  // show names, and only fetch them once there is a movement to label.
  const hasMovementResults = (movements.data?.length ?? 0) > 0;
  const { data: productList } = useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: async () => (await inventoryApi.get("/products/")).data,
    enabled: hasMovementResults,
    retry: false,
  });
  const { data: warehouseList } = useQuery<Warehouse[]>({
    queryKey: ["warehouses"],
    queryFn: async () => (await inventoryApi.get("/warehouses/")).data,
    enabled: hasMovementResults,
    retry: false,
  });

  const sections = useMemo<PaletteSection[]>(() => {
    const productNames = new Map((productList ?? []).map((p) => [p.id, p.name]));
    const warehouseNames = new Map((warehouseList ?? []).map((w) => [w.id, w.name]));
    const needle = query.trim().toLowerCase();

    const result: PaletteSection[] = [
      {
        title: "Navigate",
        items: COMMANDS.filter((c) => c.label.toLowerCase().includes(needle)).map((c) => ({
          key: `nav-${c.path}`,
          label: c.label,
          path: c.path,
        })),
      },
      {
        title: "Products",
        items: (products.data ?? []).map((p) => ({
          key: `product-${p.id}`,
          label: p.name,
          hint: p.sku,
          path: "/products",
        })),
      },
      {
        title: "Warehouses",
        items: (warehouses.data ?? []).map((w) => ({
          key: `warehouse-${w.id}`,
          label: w.name,
          hint: `${w.code} · ${w.city}`,
          path: "/warehouses",
        })),
      },
      {
        title: "Suppliers",
        items: (suppliers.data ?? []).map((s) => ({
          key: `supplier-${s.id}`,
          label: s.name,
          hint: s.code,
          path: "/suppliers",
        })),
      },
      {
        title: "Purchase orders",
        items: (purchaseOrders.data ?? []).map((po) => ({
          key: `po-${po.id}`,
          label: po.po_number,
          hint: po.status,
          path: `/purchase-orders/${po.id}`,
        })),
      },
      {
        title: "Movements",
        items: (movements.data ?? []).map((m) => ({
          key: `movement-${m.id}`,
          label: `${m.movement_type} · ${m.quantity}`,
          hint: [productNames.get(m.product_id), warehouseNames.get(m.warehouse_id), m.notes]
            .filter(Boolean)
            .join(" · "),
          path: "/movements",
        })),
      },
    ];
    return result.filter((section) => section.items.length > 0);
  }, [query, products.data, warehouses.data, suppliers.data, purchaseOrders.data, movements.data, productList, warehouseList]);

  const flatItems = useMemo(() => sections.flatMap((section) => section.items), [sections]);
  const itemKeys = flatItems.map((item) => item.key).join("|");

  const searches = [products, warehouses, suppliers, purchaseOrders, movements];
  const isSearching = term.length >= MIN_QUERY_LENGTH && searches.some((s) => s.isFetching);
  const hasFailure = term.length >= MIN_QUERY_LENGTH && searches.some((s) => s.isError);

  // Results stream in and reorder under the cursor; an index chosen for an older result
  // set is ignored, so the highlight restarts at the top without an effect.
  const activeIndex = active.keys === itemKeys ? active.index : 0;

  useEffect(() => {
    document.getElementById(`palette-option-${activeIndex}`)?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  function selectItem(item: PaletteItem) {
    navigate(item.path);
    onClose();
  }

  function handleInputKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (flatItems.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive({ index: (activeIndex + 1) % flatItems.length, keys: itemKeys });
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive({ index: (activeIndex - 1 + flatItems.length) % flatItems.length, keys: itemKeys });
    } else if (e.key === "Enter") {
      e.preventDefault();
      selectItem(flatItems[activeIndex]);
    }
  }

  const overlayMotion = prefersReducedMotion
    ? { initial: { opacity: 1 }, animate: { opacity: 1 }, exit: { opacity: 1 }, transition: { duration: 0 } }
    : { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } };
  const panelMotion = prefersReducedMotion
    ? { initial: { opacity: 1 }, animate: { opacity: 1 }, exit: { opacity: 1 }, transition: { duration: 0 } }
    : {
        initial: { opacity: 0, scale: 0.97, y: -8 },
        animate: { opacity: 1, scale: 1, y: 0 },
        exit: { opacity: 0, scale: 0.97, y: -8 },
        transition: { duration: 0.15 },
      };

  let runningIndex = -1;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24">
      <motion.div
        {...overlayMotion}
        className="absolute inset-0 bg-ink/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div
        {...panelMotion}
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        className="relative w-full max-w-lg rounded-md border border-border bg-surface/95 backdrop-blur-md shadow-2xl"
      >
        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
          <Search size={16} className="text-text-muted" />
          <input
            autoFocus
            role="combobox"
            aria-expanded="true"
            aria-controls="palette-listbox"
            aria-activedescendant={flatItems.length > 0 ? `palette-option-${activeIndex}` : undefined}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder="Jump to, or search products, orders, suppliers..."
            className="w-full bg-transparent text-sm text-text outline-none placeholder:text-text-muted"
          />
        </div>
        <div id="palette-listbox" role="listbox" className="max-h-80 overflow-y-auto py-1">
          {sections.map((section) => (
            <div key={section.title} role="group" aria-label={section.title}>
              <p className="px-4 pb-1 pt-2 text-[11px] font-medium uppercase tracking-wide text-text-muted">
                {section.title}
              </p>
              {section.items.map((item) => {
                runningIndex += 1;
                const index = runningIndex;
                const isActive = index === activeIndex;
                return (
                  <button
                    key={item.key}
                    id={`palette-option-${index}`}
                    role="option"
                    aria-selected={isActive}
                    onClick={() => selectItem(item)}
                    onMouseMove={() => {
                        if (index !== activeIndex) setActive({ index, keys: itemKeys });
                      }}
                    className={`flex w-full items-baseline justify-between gap-3 px-4 py-2 text-left text-sm text-text transition-colors ${
                      isActive ? "bg-ink" : ""
                    }`}
                  >
                    <span className="truncate">{item.label}</span>
                    {item.hint && (
                      <span className="truncate font-mono text-xs text-text-muted">{item.hint}</span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
          {flatItems.length === 0 && !isSearching && (
            <p className="px-4 py-3 text-sm text-text-muted">No matches</p>
          )}
        </div>
        {(isSearching || hasFailure) && (
          <p className="border-t border-border px-4 py-2 text-xs text-text-muted" role="status">
            {isSearching ? "Searching..." : "Some results are unavailable right now."}
          </p>
        )}
      </motion.div>
    </div>
  );
}
