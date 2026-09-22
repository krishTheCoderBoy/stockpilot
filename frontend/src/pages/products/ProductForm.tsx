import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";
import { type Category } from "../../lib/queries";

export function ProductForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState({
    sku: "",
    name: "",
    description: "",
    category_id: "",
    unit_price: "",
    unit_of_measure: "unit",
    reorder_point: "0",
    min_order_quantity: "1",
    max_stock_level: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { data: categories } = useQuery<Category[]>({
    queryKey: ["product-categories"],
    queryFn: async () => (await api.get("/product-categories/")).data,
  });

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post("/products/", {
        ...form,
        category_id: form.category_id || null,
        unit_price: Number(form.unit_price),
        reorder_point: Number(form.reorder_point),
        min_order_quantity: Number(form.min_order_quantity),
        max_stock_level: form.max_stock_level ? Number(form.max_stock_level) : null,
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

     <Input id="sku" label="SKU" value={form.sku} onChange={(e) => update("sku", e.target.value)} required />
      <Input id="name" label="Name" value={form.name} onChange={(e) => update("name", e.target.value)} required />
      <Input id="description" label="Description" value={form.description} onChange={(e) => update("description", e.target.value)} />

      <div className="flex flex-col gap-1.5">
        <label className="text-sm text-text-muted">Category</label>
        <select
          value={form.category_id}
          onChange={(e) => update("category_id", e.target.value)}
          className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
        >
          <option value="">None</option>
          {categories?.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Input id="unit_price" label="Unit price" type="number" step="0.01" value={form.unit_price} onChange={(e) => update("unit_price", e.target.value)} required />
        <Input id="unit_of_measure" label="Unit of measure" value={form.unit_of_measure} onChange={(e) => update("unit_of_measure", e.target.value)} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Input id="reorder_point" label="Reorder point" type="number" value={form.reorder_point} onChange={(e) => update("reorder_point", e.target.value)} />
        <Input id="min_order_quantity" label="Min order qty" type="number" value={form.min_order_quantity} onChange={(e) => update("min_order_quantity", e.target.value)} />
      </div>

      <Input id="max_stock_level" label="Max stock level" type="number" value={form.max_stock_level} onChange={(e) => update("max_stock_level", e.target.value)} />

      <Button type="submit" disabled={loading}>
        {loading ? "Saving..." : "Save product"}
      </Button>
    </form>
  );
}