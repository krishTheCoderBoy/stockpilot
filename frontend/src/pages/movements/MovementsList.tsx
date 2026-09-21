import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeftRight, Plus, ArrowRightLeft } from "lucide-react";
import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { Table } from "../../components/ui/Table";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { Modal } from "../../components/ui/Modal";
import { api } from "../../lib/api";
import { type Movement, type Product, type Warehouse } from "../../lib/queries";
import { MovementForm } from "./MovementForm";
import { TransferForm } from "./TransferForm";
import { useAuth } from "../../context/AuthContext";

const TYPE_TONE: Record<string, "flow" | "danger" | "accent"> = {
  RECEIVE: "flow",
  TRANSFER_IN: "flow",
  ISSUE: "danger",
  TRANSFER_OUT: "danger",
  ADJUSTMENT_INCREASE: "accent",
  ADJUSTMENT_DECREASE: "accent",
};

export function MovementsList() {
  const [isMovementFormOpen, setIsMovementFormOpen] = useState(false);
  const [isTransferFormOpen, setIsTransferFormOpen] = useState(false);
  const { role } = useAuth();
  const canWrite = role === "ADMIN" || role === "INVENTORY_MANAGER";

  const { data: movements, isLoading, refetch } = useQuery<Movement[]>({
    queryKey: ["movements"],
    queryFn: async () => (await api.get("/inventory-movements/")).data,
  });

  const { data: products } = useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: async () => (await api.get("/products/")).data,
  });

  const { data: warehouses } = useQuery<Warehouse[]>({
    queryKey: ["warehouses"],
    queryFn: async () => (await api.get("/warehouses/")).data,
  });

  const productMap = useMemo(() => new Map((products ?? []).map((p) => [p.id, p])), [products]);
  const warehouseMap = useMemo(() => new Map((warehouses ?? []).map((w) => [w.id, w])), [warehouses]);

  function closeAndRefresh() {
    setIsMovementFormOpen(false);
    setIsTransferFormOpen(false);
    refetch();
  }

  return (
    <AppShell breadcrumb="Inventory / Movements">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-medium text-text">Movements</h1>
        {canWrite && (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setIsTransferFormOpen(true)}>
              <ArrowRightLeft size={16} /> Transfer stock
            </Button>
            <Button onClick={() => setIsMovementFormOpen(true)}>
              <Plus size={16} /> Record movement
            </Button>
          </div>
        )}
      </div>

      <Card className="p-0">
        <Table<Movement>
          isLoading={isLoading}
          data={movements ?? []}
          keyExtractor={(m) => m.id}
          emptyState={
            <EmptyState
              icon={ArrowLeftRight}
              title="No movements yet"
              description="Record a movement to start tracking inventory changes."
              actionLabel={canWrite ? "Record movement" : undefined}
              onAction={canWrite ? () => setIsMovementFormOpen(true) : undefined}
            />
          }
          columns={[
            {
              header: "Date",
              accessor: (m) => <span className="text-text-muted text-xs">{new Date(m.created_at).toLocaleString()}</span>,
            },
            {
              header: "Product",
              accessor: (m) => productMap.get(m.product_id)?.name ?? "Unknown",
            },
            {
              header: "Warehouse",
              accessor: (m) => warehouseMap.get(m.warehouse_id)?.name ?? "Unknown",
            },
            {
              header: "Type",
              accessor: (m) => <Badge tone={TYPE_TONE[m.movement_type]}>{m.movement_type}</Badge>,
            },
            {
              header: "Quantity",
              accessor: (m) => <span className="font-mono">{m.quantity}</span>,
            },
            {
              header: "Reference",
              accessor: (m) => <Badge tone="neutral">{m.reference_type}</Badge>,
            },
            {
              header: "Notes",
              accessor: (m) => <span className="text-text-muted text-xs">{m.notes ?? "—"}</span>,
            },
          ]}
        />
      </Card>

      <Modal isOpen={isMovementFormOpen} onClose={() => setIsMovementFormOpen(false)} title="Record movement">
        <MovementForm products={products ?? []} warehouses={warehouses ?? []} onSuccess={closeAndRefresh} />
      </Modal>

      <Modal isOpen={isTransferFormOpen} onClose={() => setIsTransferFormOpen(false)} title="Transfer stock">
        <TransferForm products={products ?? []} warehouses={warehouses ?? []} onSuccess={closeAndRefresh} />
      </Modal>
    </AppShell>
  );
}