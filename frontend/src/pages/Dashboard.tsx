import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Package, Wallet, ShoppingCart, AlertTriangle } from "lucide-react";
import { AppShell } from "../components/shell/AppShell";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Skeleton } from "../components/ui/Skeleton";
import { api } from "../lib/api";

interface Summary {
  total_products: number;
  total_inventory_value: string;
  pending_purchase_orders: number;
  low_stock_items: number;
}

interface TrendPoint {
  period: string;
  stock_in: string;
  stock_out: string;
}

interface RecentMovement {
  product_name: string;
  movement_type: string;
  quantity: string;
  warehouse_name: string;
  created_at: string;
}

const MOVEMENT_TONE: Record<string, "flow" | "danger" | "accent"> = {
  RECEIVE: "flow",
  TRANSFER_IN: "flow",
  ISSUE: "danger",
  TRANSFER_OUT: "danger",
  ADJUSTMENT_INCREASE: "accent",
  ADJUSTMENT_DECREASE: "accent",
};

function StatCard({ icon: Icon, label, value, tone = "default" }: { icon: React.ElementType; label: string; value: string; tone?: "default" | "danger" }) {
  return (
    <Card>
      <div className="flex items-center gap-3">
        <div className={`flex h-9 w-9 items-center justify-center rounded-sm ${tone === "danger" ? "bg-danger/10 text-danger" : "bg-accent/10 text-accent"}`}>
          <Icon size={18} />
        </div>
        <div>
          <p className="text-xs text-text-muted">{label}</p>
          <p className="font-mono text-lg text-text">{value}</p>
        </div>
      </div>
    </Card>
  );
}

export function Dashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery<Summary>({
    queryKey: ["dashboard-summary"],
    queryFn: async () => (await api.get("/dashboard/summary")).data,
  });

  const { data: trend, isLoading: trendLoading } = useQuery<TrendPoint[]>({
    queryKey: ["dashboard-trend"],
    queryFn: async () => (await api.get("/dashboard/inventory-trend")).data,
  });

  const { data: movements, isLoading: movementsLoading } = useQuery<RecentMovement[]>({
    queryKey: ["dashboard-movements"],
    queryFn: async () => (await api.get("/dashboard/recent-movements")).data,
  });

  return (
    <AppShell breadcrumb="Dashboard">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryLoading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)
        ) : (
          <>
            <StatCard icon={Package} label="Total Products" value={String(summary?.total_products ?? 0)} />
            <StatCard icon={Wallet} label="Inventory Value" value={`₹${Number(summary?.total_inventory_value ?? 0).toLocaleString()}`} />
            <StatCard icon={ShoppingCart} label="Pending Purchase Orders" value={String(summary?.pending_purchase_orders ?? 0)} />
            <StatCard icon={AlertTriangle} label="Low Stock Items" value={String(summary?.low_stock_items ?? 0)} tone={summary && summary.low_stock_items > 0 ? "danger" : "default"} />
          </>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="mb-4 text-sm font-medium text-text">Inventory Trend</h2>
          {trendLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trend}>
                <CartesianGrid stroke="#232838" strokeDasharray="3 3" />
                <XAxis dataKey="period" stroke="#8B93A7" fontSize={12} />
                <YAxis stroke="#8B93A7" fontSize={12} />
                <RechartsTooltip
                  contentStyle={{ backgroundColor: "#12161F", border: "1px solid #232838", borderRadius: 6, fontSize: 12 }}
                />
                <Line type="monotone" dataKey="stock_in" stroke="#4FB7B3" strokeWidth={2} dot={false} name="Stock In" />
                <Line type="monotone" dataKey="stock_out" stroke="#D9A441" strokeWidth={2} dot={false} name="Stock Out" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card>
          <h2 className="mb-4 text-sm font-medium text-text">Recent Movements</h2>
          {movementsLoading ? (
            <div className="flex flex-col gap-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : movements && movements.length > 0 ? (
            <div className="flex flex-col gap-3">
              {movements.map((m, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <div>
                    <p className="text-text">{m.product_name}</p>
                    <p className="text-xs text-text-muted">{m.warehouse_name}</p>
                  </div>
                  <div className="text-right">
                    <Badge tone={MOVEMENT_TONE[m.movement_type] ?? "neutral"}>{m.movement_type}</Badge>
                    <p className="mt-1 font-mono text-xs text-text-muted">{m.quantity}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-muted">No movements yet.</p>
          )}
        </Card>
      </div>
    </AppShell>
  );
}