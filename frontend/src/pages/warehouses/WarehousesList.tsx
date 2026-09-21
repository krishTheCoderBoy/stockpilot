import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Warehouse as WarehouseIcon } from "lucide-react";
import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { Table } from "../../components/ui/Table";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { Modal } from "../../components/ui/Modal";
import { api } from "../../lib/api";
import { type Warehouse } from "../../lib/queries";
import { WarehouseForm } from "./WarehouseForm";
import { useAuth } from "../../context/AuthContext";

const TYPE_TONE: Record<string, "accent" | "flow" | "neutral"> = {
  MAIN: "accent",
  REGIONAL: "flow",
  TRANSIT: "neutral",
};

export function WarehousesList() {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const { role } = useAuth();
  const canWrite = role === "ADMIN";

  const { data: warehouses, isLoading, refetch } = useQuery<Warehouse[]>({
    queryKey: ["warehouses"],
    queryFn: async () => (await api.get("/warehouses/")).data,
  });

  return (
    <AppShell breadcrumb="Inventory / Warehouses">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-medium text-text">Warehouses</h1>
        {canWrite && (
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus size={16} /> Add warehouse
          </Button>
        )}
      </div>

      <Card className="p-0">
        <Table<Warehouse>
          isLoading={isLoading}
          data={warehouses ?? []}
          keyExtractor={(w) => w.id}
          emptyState={
            <EmptyState
              icon={WarehouseIcon}
              title="No warehouses yet"
              description="Add a warehouse to start tracking stock locations."
              actionLabel={canWrite ? "Add warehouse" : undefined}
              onAction={canWrite ? () => setIsFormOpen(true) : undefined}
            />
          }
          columns={[
            { header: "Code", accessor: (w) => <span className="font-mono">{w.code}</span> },
            { header: "Name", accessor: (w) => w.name },
            { header: "Location", accessor: (w) => `${w.city}, ${w.state}` },
            { header: "Type", accessor: (w) => <Badge tone={TYPE_TONE[w.warehouse_type]}>{w.warehouse_type}</Badge> },
            {
              header: "Capacity",
              accessor: (w) => <span className="font-mono">{w.capacity ?? "—"}</span>,
            },
            {
              header: "Status",
              accessor: (w) => <Badge tone={w.is_active ? "flow" : "neutral"}>{w.is_active ? "ACTIVE" : "INACTIVE"}</Badge>,
            },
          ]}
        />
      </Card>

      <Modal isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} title="Add warehouse">
        <WarehouseForm
          onSuccess={() => {
            setIsFormOpen(false);
            refetch();
          }}
        />
      </Modal>
    </AppShell>
  );
}