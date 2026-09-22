import { useState } from "react";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";
import { type Product, type Warehouse } from "../../lib/queries";

const MOVEMENT_TYPES = ["RECEIVE", "ISSUE", "ADJUSTMENT_INCREASE", "ADJUSTMENT_DECREASE"] as const;

interface Props {
  products: Product[];
  warehouses: Warehouse[];
  onSuccess: () => void;
}

export function MovementForm({ products, warehouses, onSuccess }: Props) {
  const [form, setForm] = useState({
    product_id: "",
    warehouse_id: "",
    movement_type: "RECEIVE" as (typeof MOVEMENT_TYPES)[number],
    quantity: "",
    unit_cost: "",
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
    setLoading(true);
    try {
      await api.post("/inventory-movements/", {
        product_id: form.product_id,
        warehouse_id: form.warehouse_id,
        movement_type: form.movement_type,
        quantity: Number(form.quantity),
        unit_cost: form.unit_cost ? Number(form.unit_cost) : null,
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

      <div className="flex flex-col gap-1.5">
        <label className="text-sm text-text-muted">Warehouse</label>
        <select
          value={form.warehouse_id}
          onChange={(e) => update("warehouse_id", e.target.value)}
          required
          className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
        >
          <option value="">Select warehouse</option>
          {warehouses.map((w) => (
            <option key={w.id} value={w.id}>{w.name}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-sm text-text-muted">Movement type</label>
        <select
          value={form.movement_type}
          onChange={(e) => update("movement_type", e.target.value as (typeof MOVEMENT_TYPES)[number])}
          className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
        >
          {MOVEMENT_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <Input id="quantity" label="Quantity" type="number" step="0.01" value={form.quantity} onChange={(e) => update("quantity", e.target.value)} required />

      {form.movement_type === "RECEIVE" && (
        <Input id="unit-cost" label="Unit cost" type="number" step="0.01" value={form.unit_cost} onChange={(e) => update("unit_cost", e.target.value)} />
      )}

      <Input id="notes" label="Notes" value={form.notes} onChange={(e) => update("notes", e.target.value)} />

      <Button type="submit" disabled={loading}>
        {loading ? "Recording..." : "Record movement"}
      </Button>
    </form>
  );
}