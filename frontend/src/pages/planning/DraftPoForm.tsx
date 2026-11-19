import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { extractErrorMessage, procurementApi } from "../../lib/api";
import { type PurchaseOrder, type Recommendation, type Warehouse } from "../../lib/queries";

interface Props {
  recommendation: Recommendation;
  warehouses: Warehouse[];
  defaultWarehouseId: string;
  onCreated: () => void;
}

export function DraftPoForm({ recommendation, warehouses, defaultWarehouseId, onCreated }: Props) {
  const navigate = useNavigate();
  const [warehouseId, setWarehouseId] = useState(defaultWarehouseId);
  const [quantity, setQuantity] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await procurementApi.post<PurchaseOrder>(
        `/planning/recommendations/${recommendation.product_id}/draft-po`,
        { warehouse_id: warehouseId, quantity: quantity ? Number(quantity) : null }
      );
      onCreated();
      navigate(`/purchase-orders/${res.data.id}`);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {error && <Alert tone="danger">{error}</Alert>}
      <p className="text-sm text-text-muted">
        Creates a draft purchase order for <span className="text-text">{recommendation.product_name}</span> with{" "}
        {recommendation.supplier_name ?? "its default supplier"}. You can review it before submitting.
      </p>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="draft-warehouse" className="text-sm text-text-muted">Deliver to warehouse</label>
        <select
          id="draft-warehouse"
          value={warehouseId}
          onChange={(e) => setWarehouseId(e.target.value)}
          required
          className="rounded-sm bg-surface border border-border px-3 py-2 text-sm text-text outline-none focus:border-accent"
        >
          <option value="">Select warehouse</option>
          {warehouses.map((w) => (
            <option key={w.id} value={w.id}>{w.name}</option>
          ))}
        </select>
      </div>

      <Input
        id="draft-quantity"
        label="Quantity"
        type="number"
        step="0.01"
        min="0"
        placeholder={`Leave empty to use the recommendation for this warehouse`}
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
      />

      <Button type="submit" disabled={loading || !warehouseId}>
        {loading ? "Creating..." : "Create draft purchase order"}
      </Button>
    </form>
  );
}
