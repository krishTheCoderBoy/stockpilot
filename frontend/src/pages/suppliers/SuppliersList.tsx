import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Truck } from "lucide-react";
import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { Table } from "../../components/ui/Table";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { Modal } from "../../components/ui/Modal";
import { api } from "../../lib/api";
import { type Supplier } from "../../lib/queries";
import { SupplierForm } from "./SupplierForm";
import { useAuth } from "../../context/AuthContext";

export function SuppliersList() {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const { role } = useAuth();
  const canWrite = role === "ADMIN" || role === "PROCUREMENT_MANAGER";

  const { data: suppliers, isLoading, refetch } = useQuery<Supplier[]>({
    queryKey: ["suppliers"],
    queryFn: async () => (await api.get("/suppliers/")).data,
  });

  return (
    <AppShell breadcrumb="Procurement / Suppliers">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-medium text-text">Suppliers</h1>
        {canWrite && (
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus size={16} /> Add supplier
          </Button>
        )}
      </div>

      <Card className="p-0">
        <Table<Supplier>
          isLoading={isLoading}
          data={suppliers ?? []}
          keyExtractor={(s) => s.id}
          emptyState={
            <EmptyState
              icon={Truck}
              title="No suppliers yet"
              description="Add a supplier to start creating purchase orders."
              actionLabel={canWrite ? "Add supplier" : undefined}
              onAction={canWrite ? () => setIsFormOpen(true) : undefined}
            />
          }
          columns={[
            { header: "Code", accessor: (s) => <span className="font-mono">{s.code}</span> },
            { header: "Name", accessor: (s) => s.name },
            { header: "Contact", accessor: (s) => s.contact_person ?? "—" },
            { header: "Email", accessor: (s) => s.email ?? "—" },
            {
              header: "Lead Time",
              accessor: (s) => <span className="font-mono">{s.lead_time_days != null ? `${s.lead_time_days}d` : "—"}</span>,
            },
            {
              header: "Status",
              accessor: (s) => <Badge tone={s.is_active ? "flow" : "neutral"}>{s.is_active ? "ACTIVE" : "INACTIVE"}</Badge>,
            },
          ]}
        />
      </Card>

      <Modal isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} title="Add supplier">
        <SupplierForm
          onSuccess={() => {
            setIsFormOpen(false);
            refetch();
          }}
        />
      </Modal>
    </AppShell>
  );
}