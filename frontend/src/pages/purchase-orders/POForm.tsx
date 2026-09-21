import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Trash2, Plus } from "lucide-react";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";
import { type Product, type Supplier, type Warehouse } from "../../lib/queries";

interface LineItem {
  product_id: string;
  ordered_quantity: string;
  unit_price: string;
}

interface Props {
  suppliers: Supplier[];
  warehouses: Warehouse[];
  onSuccess: () => void;
}

export function POForm({ suppliers, warehouses, onSuccess }: Props) {
  const [supplierId, setSupplierId] = useState("");
  const [warehouseId, setWarehouseId] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<LineItem[]>([{ product_id: "", ordered_quantity: "", unit_price: "" }]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { data: products } = useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: async () => (await api.get("/products/")).data,
  });

  function updateItem(index: number, field: keyof LineItem, value: string) {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)));
  }

  function addItem() {
    setItems((prev) => [...prev, { product_id: "", ordered_quantity: "", unit_price: "" }]);
  }

  function removeItem(index: number) {
    setItems((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (items.length === 0) {
      setError("At least one line item is required.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/purchase-orders/", {
        supplier_id: supplierId,
        warehouse_id: warehouseId,
        notes: notes || null,
        items: items.map((item) => ({
          product_id: item.product_id,
          ordered_quantity: Number(item.ordered_quantity),
          unit_price: Number(item.unit_price),
        })),
      });
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

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm text-text-muted">Supplier</label>
          <select
            value={supplierId}
            onChange={(e) => setSupplierId(e.target.value)}
            required
            className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
          >
            <option value="">Select</option>
            {suppliers.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm text-text-muted">Warehouse</label>
          <select
            value={warehouseId}
            onChange={(e) => setWarehouseId(e.target.value)}
            required
            className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
          >
            <option value="">Select</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <label className="text-sm text-text-muted">Line items</label>
          <button type="button" onClick={addItem} className="flex items-center gap-1 text-xs text-accent hover:underline">
            <Plus size={12} /> Add item
          </button>
        </div>

        {items.map((item, index) => (
          <div key={index} className="flex items-end gap-2 rounded-sm border border-border p-2">
            <div className="flex-1">
              <select
                value={item.product_id}
                onChange={(e) => updateItem(index, "product_id", e.target.value)}
                required
                className="w-full rounded-sm bg-ink border border-border px-2 py-1.5 text-xs text-text outline-none focus:border-accent"
              >
                <option value="">Product</option>
                {products?.map((p) => (
                  <option key={p.id} value={p.id}>{p.sku}</option>
                ))}
              </select>
            </div>
            <input
              type="number"
              placeholder="Qty"
              value={item.ordered_quantity}
              onChange={(e) => updateItem(index, "ordered_quantity", e.target.value)}
              required
              className="w-20 rounded-sm bg-ink border border-border px-2 py-1.5 text-xs text-text outline-none focus:border-accent"
            />
            <input
              type="number"
              step="0.01"
              placeholder="Price"
              value={item.unit_price}
              onChange={(e) => updateItem(index, "unit_price", e.target.value)}
              required
              className="w-24 rounded-sm bg-ink border border-border px-2 py-1.5 text-xs text-text outline-none focus:border-accent"
            />
            {items.length > 1 && (
              <button type="button" onClick={() => removeItem(index)} className="p-1.5 text-danger hover:opacity-80">
                <Trash2 size={14} />
              </button>
            )}
          </div>
        ))}
      </div>

      <Input label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />

      <Button type="submit" disabled={loading}>
        {loading ? "Creating..." : "Create purchase order"}
      </Button>
    </form>
  );
}