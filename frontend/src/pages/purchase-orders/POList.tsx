import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Plus, ClipboardList } from "lucide-react";
import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { Table } from "../../components/ui/Table";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { Modal } from "../../components/ui/Modal";
import { api } from "../../lib/api";
import { type PurchaseOrder, type Supplier, type Warehouse } from "../../lib/queries";
import { POForm } from "./POForm";
import { useAuth } from "../../context/AuthContext";

const STATUS_TONE: Record<string, "neutral" | "accent" | "flow" | "danger"> = {
  DRAFT: "neutral",
  SUBMITTED: "accent",
  APPROVED: "accent",
  ORDERED: "flow",
  PARTIALLY_RECEIVED: "accent",
  RECEIVED: "flow",
  CLOSED: "neutral",
};

export function POList() {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const navigate = useNavigate();
  const { role } = useAuth();
  const canWrite = role === "ADMIN" || role === "PROCUREMENT_MANAGER";

  const { data: pos, isLoading, refetch } = useQuery<PurchaseOrder[]>({
    queryKey: ["purchase-orders"],
    queryFn: async () => (await api.get("/purchase-orders/")).data,
  });

  const { data: suppliers } = useQuery<Supplier[]>({
    queryKey: ["suppliers"],
    queryFn: async () => (await api.get("/suppliers/")).data,
  });

  const { data: warehouses } = useQuery<Warehouse[]>({
    queryKey: ["warehouses"],
    queryFn: async () => (await api.get("/warehouses/")).data,
  });

  const supplierMap = new Map((suppliers ?? []).map((s) => [s.id, s.name]));
  const warehouseMap = new Map((warehouses ?? []).map((w) => [w.id, w.name]));

  return (
    <AppShell breadcrumb="Procurement / Purchase Orders">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-medium text-text">Purchase Orders</h1>
        {canWrite && (
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus size={16} /> New purchase order
          </Button>
        )}
      </div>

      <Card className="p-0">
        <Table<PurchaseOrder>
          isLoading={isLoading}
          data={pos ?? []}
          keyExtractor={(po) => po.id}
          emptyState={
            <EmptyState
              icon={ClipboardList}
              title="No purchase orders yet"
              description="Create a purchase order to start procuring stock."
              actionLabel={canWrite ? "New purchase order" : undefined}
              onAction={canWrite ? () => setIsFormOpen(true) : undefined}
            />
          }
          columns={[
            { header: "PO Number", accessor: (po) => <span className="font-mono">{po.po_number}</span> },
            { header: "Supplier", accessor: (po) => supplierMap.get(po.supplier_id) ?? "Unknown" },
            { header: "Warehouse", accessor: (po) => warehouseMap.get(po.warehouse_id) ?? "Unknown" },
            { header: "Items", accessor: (po) => <span className="font-mono">{po.items.length}</span> },
            { header: "Status", accessor: (po) => <Badge tone={STATUS_TONE[po.status]}>{po.status}</Badge> },
            {
              header: "",
              accessor: (po) => (
                <button
                  onClick={() => navigate(`/purchase-orders/${po.id}`)}
                  className="text-xs text-accent hover:underline"
                >
                  View
                </button>
              ),
            },
          ]}
        />
      </Card>

      <Modal isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} title="New purchase order">
        <POForm
          suppliers={suppliers ?? []}
          warehouses={warehouses ?? []}
          onSuccess={() => {
            setIsFormOpen(false);
            refetch();
          }}
        />
      </Modal>
    </AppShell>
  );
}