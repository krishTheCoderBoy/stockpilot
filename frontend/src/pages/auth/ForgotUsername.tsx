import { useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api } from "../../lib/api";

export function ForgotUsername() {
  const [identifier, setIdentifier] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await api.post("/auth/forgot-username", { identifier });
    setLoading(false);
    setSent(true);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-1 font-mono text-lg text-accent">Recover username</h1>
        <p className="mb-6 text-sm text-text-muted">
          Enter your email or mobile number and we'll send you your username
        </p>

        {sent && (
          <div className="mb-4">
            <Alert tone="success">If that identifier is registered, your username has been emailed.</Alert>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            id="identifier"
            label="Email or mobile number"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
          />
          <Button type="submit" disabled={loading}>
            {loading ? "Sending..." : "Recover username"}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-text-muted">
          <Link to="/login" className="text-accent hover:underline">
            Back to sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}