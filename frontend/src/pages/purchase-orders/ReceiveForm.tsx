import { useState } from "react";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";
import { type PurchaseOrder, type Product } from "../../lib/queries";

interface Props {
  po: PurchaseOrder;
  productMap: Map<string, Product>;
  onSuccess: () => void;
}

export function ReceiveForm({ po, productMap, onSuccess }: Props) {
  const remainingItems = po.items.filter(
    (item) => Number(item.received_quantity) < Number(item.ordered_quantity)
  );
  const [quantities, setQuantities] = useState<Record<string, string>>(
    Object.fromEntries(remainingItems.map((item) => [item.id, ""]))
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const items = remainingItems
      .filter((item) => quantities[item.id] && Number(quantities[item.id]) > 0)
      .map((item) => ({ po_item_id: item.id, quantity: Number(quantities[item.id]) }));

    if (items.length === 0) {
      setError("Enter a quantity for at least one item.");
      return;
    }

    setLoading(true);
    try {
      await api.post(`/purchase-orders/${po.id}/receive`, { items });
      onSuccess();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {error && <Alert tone="danger">{error}</Alert>}

      {remainingItems.map((item) => {
        const product = productMap.get(item.product_id);
        const remaining = Number(item.ordered_quantity) - Number(item.received_quantity);
        return (
          <div key={item.id} className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm text-text">{product?.name ?? "Unknown"}</p>
              <p className="text-xs text-text-muted">Remaining: {remaining}</p>
            </div>
            <input
              type="number"
              max={remaining}
              placeholder="Qty"
              value={quantities[item.id]}
              onChange={(e) => setQuantities((prev) => ({ ...prev, [item.id]: e.target.value }))}
              className="w-24 rounded-sm bg-surface border border-border px-2 py-1.5 text-sm text-text outline-none focus:border-accent"
            />
          </div>
        );
      })}

      <Button type="submit" disabled={loading}>
        {loading ? "Receiving..." : "Confirm receipt"}
      </Button>
    </form>
  );
}