import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { Modal } from "../../components/ui/Modal";
import { api, extractErrorMessage } from "../../lib/api";
import { type PurchaseOrder, type Product, type Supplier, type Warehouse } from "../../lib/queries";
import { ReceiveForm } from "./ReceiveForm";
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

export function PODetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { role } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [isReceiveOpen, setIsReceiveOpen] = useState(false);

  const canWrite = role === "ADMIN" || role === "PROCUREMENT_MANAGER";
  const canApprove = role === "ADMIN";

  const { data: po, isLoading, refetch } = useQuery<PurchaseOrder>({
    queryKey: ["purchase-order", id],
    queryFn: async () => (await api.get(`/purchase-orders/${id}`)).data,
  });

  const { data: products } = useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: async () => (await api.get("/products/")).data,
  });

  const { data: suppliers } = useQuery<Supplier[]>({
    queryKey: ["suppliers"],
    queryFn: async () => (await api.get("/suppliers/")).data,
  });

  const { data: warehouses } = useQuery<Warehouse[]>({
    queryKey: ["warehouses"],
    queryFn: async () => (await api.get("/warehouses/")).data,
  });

  const productMap = new Map((products ?? []).map((p) => [p.id, p]));
  const supplierMap = new Map((suppliers ?? []).map((s) => [s.id, s.name]));
  const warehouseMap = new Map((warehouses ?? []).map((w) => [w.id, w.name]));

  async function performAction(action: "submit" | "approve" | "mark-ordered" | "close") {
    setError(null);
    setActionLoading(true);
    try {
      await api.post(`/purchase-orders/${id}/${action}`);
      refetch();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  }

  if (isLoading || !po) {
    return (
      <AppShell breadcrumb="Procurement / Purchase Orders">
        <p className="text-text-muted">Loading...</p>
      </AppShell>
    );
  }

  return (
    <AppShell breadcrumb={`Procurement / Purchase Orders / ${po.po_number}`}>
      <button onClick={() => navigate("/purchase-orders")} className="mb-4 text-sm text-accent hover:underline">
        ← Back to purchase orders
      </button>

      <Card className="mb-4">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="font-mono text-lg text-text">{po.po_number}</h1>
            <p className="text-sm text-text-muted">
              {supplierMap.get(po.supplier_id)} → {warehouseMap.get(po.warehouse_id)}
            </p>
          </div>
          <Badge tone={STATUS_TONE[po.status]}>{po.status}</Badge>
        </div>

        {error && (
          <div className="mb-4">
            <Alert tone="danger">{error}</Alert>
          </div>
        )}

        {po.notes && <p className="mb-4 text-sm text-text-muted">{po.notes}</p>}

        {canWrite && (
          <div className="flex flex-wrap gap-2">
            {po.status === "DRAFT" && (
              <Button disabled={actionLoading} onClick={() => performAction("submit")}>
                Submit for approval
              </Button>
            )}
            {po.status === "SUBMITTED" && canApprove && (
              <Button disabled={actionLoading} onClick={() => performAction("approve")}>
                Approve
              </Button>
            )}
            {po.status === "SUBMITTED" && !canApprove && (
              <p className="text-xs text-text-muted">Waiting for admin approval.</p>
            )}
            {po.status === "APPROVED" && (
              <Button disabled={actionLoading} onClick={() => performAction("mark-ordered")}>
                Mark as ordered
              </Button>
            )}
            {(po.status === "ORDERED" || po.status === "PARTIALLY_RECEIVED") && (
              <Button disabled={actionLoading} onClick={() => setIsReceiveOpen(true)}>
                Receive items
              </Button>
            )}
            {po.status === "RECEIVED" && (
              <Button disabled={actionLoading} onClick={() => performAction("close")}>
                Close purchase order
              </Button>
            )}
          </div>
        )}
      </Card>

      <Card className="p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface">
              <th className="px-4 py-3 text-left font-medium text-text-muted">Product</th>
              <th className="px-4 py-3 text-left font-medium text-text-muted">Ordered</th>
              <th className="px-4 py-3 text-left font-medium text-text-muted">Received</th>
              <th className="px-4 py-3 text-left font-medium text-text-muted">Unit Price</th>
            </tr>
          </thead>
          <tbody>
            {po.items.map((item) => {
              const product = productMap.get(item.product_id);
              return (
                <tr key={item.id} className="border-b border-border last:border-0">
                  <td className="px-4 py-3 text-text">
                    {product?.name ?? "Unknown"}{" "}
                    <span className="font-mono text-xs text-text-muted">{product?.sku}</span>
                  </td>
                  <td className="px-4 py-3 font-mono text-text">{item.ordered_quantity}</td>
                  <td className="px-4 py-3 font-mono text-text-muted">{item.received_quantity}</td>
                  <td className="px-4 py-3 font-mono text-text">₹{item.unit_price}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      <Modal isOpen={isReceiveOpen} onClose={() => setIsReceiveOpen(false)} title="Receive items">
        <ReceiveForm
          po={po}
          productMap={productMap}
          onSuccess={() => {
            setIsReceiveOpen(false);
            refetch();
          }}
        />
      </Modal>
    </AppShell>
  );
}