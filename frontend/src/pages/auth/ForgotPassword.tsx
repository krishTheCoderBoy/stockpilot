import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api } from "../../lib/api";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await api.post("/auth/forgot-password", { email });
    setLoading(false);
    setSent(true);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-1 font-mono text-lg text-accent">Reset password</h1>
        <p className="mb-6 text-sm text-text-muted">
          We'll email you a code if the address is registered
        </p>

        {sent && (
          <div className="mb-4">
            <Alert tone="success">
              If that email is registered, a code has been sent.{" "}
              <button
                onClick={() => navigate("/reset-password", { state: { email } })}
                className="underline"
              >
                Continue
              </button>
            </Alert>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Button type="submit" disabled={loading}>
            {loading ? "Sending..." : "Send reset code"}
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