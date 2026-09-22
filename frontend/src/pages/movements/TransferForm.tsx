import { useState } from "react";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";
import { type Product, type Warehouse } from "../../lib/queries";

interface Props {
  products: Product[];
  warehouses: Warehouse[];
  onSuccess: () => void;
}

export function TransferForm({ products, warehouses, onSuccess }: Props) {
  const [form, setForm] = useState({
    product_id: "",
    source_warehouse_id: "",
    destination_warehouse_id: "",
    quantity: "",
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update<K extends keyof typeof form>(field: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (form.source_warehouse_id === form.destination_warehouse_id) {
      setError("Source and destination warehouses must be different.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/inventory-movements/transfer", {
        product_id: form.product_id,
        source_warehouse_id: form.source_warehouse_id,
        destination_warehouse_id: form.destination_warehouse_id,
        quantity: Number(form.quantity),
        notes: form.notes || null,
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

      <div className="flex flex-col gap-1.5">
        <label className="text-sm text-text-muted">Product</label>
        <select
          value={form.product_id}
          onChange={(e) => update("product_id", e.target.value)}
          required
          className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
        >
          <option value="">Select product</option>
          {products.map((p) => (
            <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm text-text-muted">From warehouse</label>
          <select
            value={form.source_warehouse_id}
            onChange={(e) => update("source_warehouse_id", e.target.value)}
            required
            className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
          >
            <option value="">Select</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm text-text-muted">To warehouse</label>
          <select
            value={form.destination_warehouse_id}
            onChange={(e) => update("destination_warehouse_id", e.target.value)}
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

      <Input id="quantity" label="Quantity" type="number" step="0.01" value={form.quantity} onChange={(e) => update("quantity", e.target.value)} required />
      <Input id="notes" label="Notes" value={form.notes} onChange={(e) => update("notes", e.target.value)} />


      
      <Button type="submit" disabled={loading}>
        {loading ? "Transferring..." : "Transfer stock"}
      </Button>
    </form>
  );
}