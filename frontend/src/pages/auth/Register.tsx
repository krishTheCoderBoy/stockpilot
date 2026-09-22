import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";
import { AppShell } from "../../components/shell/AppShell";

export function Register() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    mobile_no: "",
    address: "",
    full_name: "",
    password: "",
    role: "INVENTORY_MANAGER",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
        try {
      await api.post("/users/", form);
      navigate("/settings/users");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell breadcrumb="Settings / Add User">
      <Card className="w-full max-w-md">
        <h1 className="mb-1 font-mono text-lg text-accent">Create account</h1>
        <p className="mb-6 text-sm text-text-muted">Register a new StockPilot user</p>

        {error && (
          <div className="mb-4">
            <Alert tone="danger">{error}</Alert>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input id="full-name" label="Full name" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} required />
          <Input id="username" label="Username" value={form.username} onChange={(e) => update("username", e.target.value)} required />
          <Input id="email" label="Email" type="email" value={form.email} onChange={(e) => update("email", e.target.value)} required />
          <Input id="mobile-no" label="Mobile number" value={form.mobile_no} onChange={(e) => update("mobile_no", e.target.value)} required />
          <Input id="address" label="Address" value={form.address} onChange={(e) => update("address", e.target.value)} />
          <Input id="password" label="Password" type="password" value={form.password} onChange={(e) => update("password", e.target.value)} required />
          <Button type="submit" disabled={loading}>
            {loading ? "Creating account..." : "Create account"}
          </Button>
        </form>
      </Card>
    </AppShell>
  );
}