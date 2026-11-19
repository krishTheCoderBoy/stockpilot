import { Fragment, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, LineChart as ChartIcon, ShoppingCart, TrendingUp } from "lucide-react";
import { AppShell } from "../../components/shell/AppShell";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Modal } from "../../components/ui/Modal";
import { Skeleton } from "../../components/ui/Skeleton";
import { useAuth } from "../../context/AuthContext";
import { extractErrorMessage, inventoryApi, procurementApi } from "../../lib/api";
import {
  type Recommendation,
  type RecommendationPage,
  type RiskLevel,
  type Supplier,
  type Warehouse,
} from "../../lib/queries";
import { DraftPoForm } from "./DraftPoForm";
import { ForecastChart } from "./ForecastChart";

const PAGE_SIZE = 25;

const RISK_TONE: Record<RiskLevel, "flow" | "accent" | "danger"> = {
  OK: "flow",
  LOW: "accent",
  STOCKOUT_RISK: "danger",
};

const RISK_LABEL: Record<RiskLevel, string> = {
  OK: "OK",
  LOW: "LOW",
  STOCKOUT_RISK: "STOCKOUT RISK",
};

const COLUMN_COUNT = 10;

const selectClass =
  "rounded-sm bg-surface border border-border px-3 py-1.5 text-sm text-text outline-none focus:border-accent";

export function PlanningPage() {
  const { role } = useAuth();
  const canOrder = role === "ADMIN" || role === "PROCUREMENT_MANAGER";

  const [risk, setRisk] = useState<RiskLevel | "">("");
  const [supplierId, setSupplierId] = useState("");
  const [warehouseId, setWarehouseId] = useState("");
  const [mode, setMode] = useState<"auto" | "rules">("auto");
  const [page, setPage] = useState(0);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [chartFor, setChartFor] = useState<Recommendation | null>(null);
  const [draftFor, setDraftFor] = useState<Recommendation | null>(null);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery<RecommendationPage>({
    queryKey: ["planning-recommendations", risk, supplierId, warehouseId, mode, page],
    queryFn: async () =>
      (
        await procurementApi.get("/planning/recommendations", {
          params: {
            risk: risk || undefined,
            supplier_id: supplierId || undefined,
            warehouse_id: warehouseId || undefined,
            mode,
            skip: page * PAGE_SIZE,
            limit: PAGE_SIZE,
          },
        })
      ).data,
    retry: false,
  });

  const { data: suppliers } = useQuery<Supplier[]>({
    queryKey: ["suppliers"],
    queryFn: async () => (await procurementApi.get("/suppliers/")).data,
  });
  const { data: warehouses } = useQuery<Warehouse[]>({
    queryKey: ["warehouses"],
    queryFn: async () => (await inventoryApi.get("/warehouses/")).data,
  });

  function changeFilter(update: () => void) {
    update();
    setPage(0);
    setExpanded(null);
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <AppShell breadcrumb="Procurement / Planning">
      <div className="mb-4">
        <h1 className="text-lg font-medium text-text">Reorder recommendations</h1>
        <p className="text-sm text-text-muted">
          What to order, based on available stock, inbound purchase orders, safety stock and forecast demand.
        </p>
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-text-muted">
          Risk
          <select value={risk} onChange={(e) => changeFilter(() => setRisk(e.target.value as RiskLevel | ""))} className={selectClass}>
            <option value="">All</option>
            <option value="STOCKOUT_RISK">Stockout risk</option>
            <option value="LOW">Low</option>
            <option value="OK">OK</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-text-muted">
          Supplier
          <select value={supplierId} onChange={(e) => changeFilter(() => setSupplierId(e.target.value))} className={selectClass}>
            <option value="">All suppliers</option>
            {(suppliers ?? []).map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-text-muted">
          Warehouse
          <select value={warehouseId} onChange={(e) => changeFilter(() => setWarehouseId(e.target.value))} className={selectClass}>
            <option value="">All warehouses</option>
            {(warehouses ?? []).map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-text-muted">
          Forecast
          <select value={mode} onChange={(e) => changeFilter(() => setMode(e.target.value as "auto" | "rules"))} className={selectClass}>
            <option value="auto">Statistical model (auto)</option>
            <option value="rules">Simple average</option>
          </select>
        </label>
      </div>

      {isError && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex-1">
            <Alert tone="danger">{extractErrorMessage(error)}</Alert>
          </div>
          <Button variant="secondary" onClick={() => refetch()}>Retry</Button>
        </div>
      )}

      <Card className="p-0">
        {isLoading ? (
          <div className="flex flex-col gap-2 p-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full motion-reduce:animate-none" />
            ))}
          </div>
        ) : data && data.items.length === 0 ? (
          <EmptyState
            icon={TrendingUp}
            title="No recommendations"
            description="Nothing matches these filters, or there are no active products yet."
          />
        ) : (
          data && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-surface">
                    {["", "Product", "Risk", "Available", "Incoming", "Safety stock", "Forecast", "Order", "Lead time", ""].map(
                      (header, i) => (
                        <th key={i} className="px-4 py-3 text-left font-medium text-text-muted">{header}</th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className={isFetching ? "opacity-70" : ""}>
                  {data.items.map((item) => {
                    const isOpen = expanded === item.product_id;
                    return (
                      <Fragment key={item.product_id}>
                        <tr className="border-b border-border last:border-0 hover:bg-surface/60">
                          <td className="px-2 py-3">
                            <button
                              onClick={() => setExpanded(isOpen ? null : item.product_id)}
                              aria-expanded={isOpen}
                              aria-label={isOpen ? "Hide explanation" : "Show explanation"}
                              className="text-text-muted hover:text-text"
                            >
                              {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                            </button>
                          </td>
                          <td className="px-4 py-3">
                            <p className="text-text">{item.product_name}</p>
                            <p className="font-mono text-xs text-text-muted">{item.sku}</p>
                          </td>
                          <td className="px-4 py-3"><Badge tone={RISK_TONE[item.risk]}>{RISK_LABEL[item.risk]}</Badge></td>
                          <td className="px-4 py-3 font-mono">
                            {item.current_available}
                            {item.days_of_cover && (
                              <span className="block text-xs text-text-muted">{item.days_of_cover} days</span>
                            )}
                          </td>
                          <td className="px-4 py-3 font-mono">{item.incoming}</td>
                          <td className="px-4 py-3 font-mono">{item.safety_stock}</td>
                          <td className="px-4 py-3 font-mono">
                            {item.forecast_demand}
                            <span className="block text-xs text-text-muted">{item.horizon_days} days</span>
                          </td>
                          <td className="px-4 py-3 font-mono text-text">{item.recommended_order}</td>
                          <td className="px-4 py-3">
                            <span className="font-mono">{item.lead_time_days}d</span>
                            <span className="block text-xs text-text-muted">
                              {item.supplier_name ?? "no supplier"}
                              {item.lead_time_source === "default" && " (default)"}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex justify-end gap-1">
                              <Button variant="ghost" onClick={() => setChartFor(item)} aria-label={`Forecast for ${item.product_name}`}>
                                <ChartIcon size={14} /> Forecast
                              </Button>
                              {canOrder && Number(item.recommended_order) > 0 && (
                                <Button variant="secondary" onClick={() => setDraftFor(item)}>
                                  <ShoppingCart size={14} /> Draft PO
                                </Button>
                              )}
                            </div>
                          </td>
                        </tr>
                        {isOpen && (
                          <tr className="border-b border-border bg-ink/40">
                            <td colSpan={COLUMN_COUNT} className="px-6 py-4">
                              <p className="mb-2 text-sm text-text">{item.explanation}</p>
                              <ul className="list-disc space-y-1 pl-5 text-xs text-text-muted">
                                {item.reasons.map((reason, i) => (
                                  <li key={i}>{reason}</li>
                                ))}
                              </ul>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )
        )}
      </Card>

      {data && data.total > PAGE_SIZE && (
        <div className="mt-3 flex items-center justify-between text-sm text-text-muted">
          <span>
            Page {page + 1} of {totalPages} · {data.total} products
          </span>
          <div className="flex gap-2">
            <Button variant="secondary" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>Previous</Button>
            <Button variant="secondary" disabled={page + 1 >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</Button>
          </div>
        </div>
      )}

      <Modal
        isOpen={chartFor !== null}
        onClose={() => setChartFor(null)}
        title={chartFor ? `Forecast: ${chartFor.product_name}` : "Forecast"}
        widthClass="max-w-3xl"
      >
        {chartFor && <ForecastChart productId={chartFor.product_id} warehouseId={warehouseId || null} />}
      </Modal>

      <Modal isOpen={draftFor !== null} onClose={() => setDraftFor(null)} title="Create draft purchase order">
        {draftFor && (
          <DraftPoForm
            recommendation={draftFor}
            warehouses={warehouses ?? []}
            defaultWarehouseId={warehouseId}
            onCreated={() => setDraftFor(null)}
          />
        )}
      </Modal>
    </AppShell>
  );
}
