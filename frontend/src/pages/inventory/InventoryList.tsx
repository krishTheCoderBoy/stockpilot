import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Boxes, AlertTriangle } from "lucide-react";
import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { Table } from "../../components/ui/Table";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { api } from "../../lib/api";
import { type InventoryRow, type Product, type Warehouse } from "../../lib/queries";

export function InventoryList() {
  const [warehouseFilter, setWarehouseFilter] = useState<string>("");

  const { data: inventory, isLoading } = useQuery<InventoryRow[]>({
    queryKey: ["inventory"],
    queryFn: async () => (await api.get("/inventory/")).data,
  });

  const { data: products } = useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: async () => (await api.get("/products/")).data,
  });

  const { data: warehouses } = useQuery<Warehouse[]>({
    queryKey: ["warehouses"],
    queryFn: async () => (await api.get("/warehouses/")).data,
  });

  const productMap = useMemo(
    () => new Map((products ?? []).map((p) => [p.id, p])),
    [products]
  );
  const warehouseMap = useMemo(
    () => new Map((warehouses ?? []).map((w) => [w.id, w])),
    [warehouses]
  );

  const filteredInventory = useMemo(() => {
    if (!inventory) return [];
    if (!warehouseFilter) return inventory;
    return inventory.filter((row) => row.warehouse_id === warehouseFilter);
  }, [inventory, warehouseFilter]);

  return (
    <AppShell breadcrumb="Inventory / Stock">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-medium text-text">Stock</h1>
        <select
          value={warehouseFilter}
          onChange={(e) => setWarehouseFilter(e.target.value)}
          className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
        >
          <option value="">All warehouses</option>
          {warehouses?.map((w) => (
            <option key={w.id} value={w.id}>{w.name}</option>
          ))}
        </select>
      </div>

      <Card className="p-0">
        <Table<InventoryRow>
          isLoading={isLoading}
          data={filteredInventory}
          keyExtractor={(row) => row.id}
          emptyState={
            <EmptyState
              icon={Boxes}
              title="No stock recorded yet"
              description="Stock appears here once inventory movements are recorded."
            />
          }
          columns={[
            {
              header: "Product",
              accessor: (row) => {
                const product = productMap.get(row.product_id);
                return (
                  <div>
                    <p className="text-text">{product?.name ?? "Unknown"}</p>
                    <p className="font-mono text-xs text-text-muted">{product?.sku}</p>
                  </div>
                );
              },
            },
            {
              header: "Warehouse",
              accessor: (row) => warehouseMap.get(row.warehouse_id)?.name ?? "Unknown",
            },
            {
              header: "On Hand",
              accessor: (row) => <span className="font-mono">{row.on_hand_quantity}</span>,
            },
            {
              header: "Reserved",
              accessor: (row) => <span className="font-mono text-text-muted">{row.reserved_quantity}</span>,
            },
            {
              header: "Available",
              accessor: (row) => <span className="font-mono text-flow">{row.available_quantity}</span>,
            },
            {
              header: "Avg Cost",
              accessor: (row) => <span className="font-mono">₹{row.average_unit_cost}</span>,
            },
            {
              header: "Status",
              accessor: (row) => {
                const product = productMap.get(row.product_id);
                const isLow = product && Number(row.on_hand_quantity) <= Number(product.reorder_point);
                return isLow ? (
                  <Badge tone="danger">
                    <AlertTriangle size={11} className="mr-1 inline" />
                    LOW STOCK
                  </Badge>
                ) : (
                  <Badge tone="flow">OK</Badge>
                );
              },
            },
          ]}
        />
      </Card>
    </AppShell>
  );
}