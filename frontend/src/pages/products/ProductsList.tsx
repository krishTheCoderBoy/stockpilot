import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Package } from "lucide-react";
import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { Table } from "../../components/ui/Table";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { Modal } from "../../components/ui/Modal";
import { api } from "../../lib/api";
import { type Product } from "../../lib/queries";
import { ProductForm } from "./ProductForm";
import { useAuth } from "../../context/AuthContext";

export function ProductsList() {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const { role } = useAuth();
  const canWrite = role === "ADMIN" || role === "INVENTORY_MANAGER";

  const { data: products, isLoading, refetch } = useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: async () => (await api.get("/products/")).data,
  });

  return (
    <AppShell breadcrumb="Inventory / Products">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-medium text-text">Products</h1>
        {canWrite && (
          <Button onClick={() => setIsFormOpen(true)}>
            <Plus size={16} /> Add product
          </Button>
        )}
      </div>

      <Card className="p-0">
        <Table<Product>
          isLoading={isLoading}
          data={products ?? []}
          keyExtractor={(p) => p.id}
          emptyState={
            <EmptyState
              icon={Package}
              title="No products yet"
              description="Add your first product to start tracking inventory."
              actionLabel={canWrite ? "Add product" : undefined}
              onAction={canWrite ? () => setIsFormOpen(true) : undefined}
            />
          }
          columns={[
            { header: "SKU", accessor: (p) => <span className="font-mono">{p.sku}</span> },
            { header: "Name", accessor: (p) => p.name },
            { header: "Unit Price", accessor: (p) => <span className="font-mono">₹{p.unit_price}</span> },
            { header: "Reorder Point", accessor: (p) => <span className="font-mono">{p.reorder_point}</span> },
            {
              header: "Status",
              accessor: (p) => <Badge tone={p.is_active ? "flow" : "neutral"}>{p.is_active ? "ACTIVE" : "INACTIVE"}</Badge>,
            },
          ]}
        />
      </Card>

      <Modal isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} title="Add product">
        <ProductForm
          onSuccess={() => {
            setIsFormOpen(false);
            refetch();
          }}
        />
      </Modal>
    </AppShell>
  );
}