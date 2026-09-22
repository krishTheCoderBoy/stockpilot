import { useState } from "react";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";

export function SupplierForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState({
    code: "",
    name: "",
    contact_person: "",
    email: "",
    phone: "",
    address: "",
    lead_time_days: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post("/suppliers/", {
        code: form.code,
        name: form.name,
        contact_person: form.contact_person || null,
        email: form.email || null,
        phone: form.phone || null,
        address: form.address || null,
        lead_time_days: form.lead_time_days ? Number(form.lead_time_days) : null,
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

      <Input id="code" label="Code" value={form.code} onChange={(e) => update("code", e.target.value)} required />
      <Input id="name" label="Name" value={form.name} onChange={(e) => update("name", e.target.value)} required />
      <Input id="contact-person" label="Contact person" value={form.contact_person} onChange={(e) => update("contact_person", e.target.value)} />

      <div className="grid grid-cols-2 gap-3">
        <Input id="email" label="Email" type="email" value={form.email} onChange={(e) => update("email", e.target.value)} />
        <Input id="phone" label="Phone" value={form.phone} onChange={(e) => update("phone", e.target.value)} />
      </div>

      <Input id="address" label="Address" value={form.address} onChange={(e) => update("address", e.target.value)} />
      <Input id="lead-time-days" label="Lead time (days)" type="number" value={form.lead_time_days} onChange={(e) => update("lead_time_days", e.target.value)} />

      <Button type="submit" disabled={loading}>
        {loading ? "Saving..." : "Save supplier"}
      </Button>
    </form>
  );
}