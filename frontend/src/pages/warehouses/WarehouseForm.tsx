import { useState } from "react";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";

const WAREHOUSE_TYPES = ["MAIN", "REGIONAL", "TRANSIT"] as const;

export function WarehouseForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState({
    code: "",
    name: "",
    city: "",
    state: "",
    country: "",
    capacity: "",
    warehouse_type: "MAIN" as (typeof WAREHOUSE_TYPES)[number],
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
      await api.post("/warehouses/", {
        ...form,
        capacity: form.capacity ? Number(form.capacity) : null,
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

      <Input label="Code" value={form.code} onChange={(e) => update("code", e.target.value)} required />
      <Input label="Name" value={form.name} onChange={(e) => update("name", e.target.value)} required />

      <div className="grid grid-cols-2 gap-3">
        <Input label="City" value={form.city} onChange={(e) => update("city", e.target.value)} required />
        <Input label="State" value={form.state} onChange={(e) => update("state", e.target.value)} required />
      </div>

      <Input label="Country" value={form.country} onChange={(e) => update("country", e.target.value)} required />

      <div className="flex flex-col gap-1.5">
        <label className="text-sm text-text-muted">Warehouse type</label>
        <select
          value={form.warehouse_type}
          onChange={(e) => update("warehouse_type", e.target.value as (typeof WAREHOUSE_TYPES)[number])}
          className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
        >
          {WAREHOUSE_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <Input label="Capacity" type="number" value={form.capacity} onChange={(e) => update("capacity", e.target.value)} />

      <Button type="submit" disabled={loading}>
        {loading ? "Saving..." : "Save warehouse"}
      </Button>
    </form>
  );
}