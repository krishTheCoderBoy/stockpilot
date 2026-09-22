import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";

export function ResetPassword() {
  const location = useLocation();
  const navigate = useNavigate();
  const prefillEmail = (location.state as { email?: string })?.email ?? "";
  const [email, setEmail] = useState(prefillEmail);
  const [otpCode, setOtpCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post("/auth/reset-password", { email, otp_code: otpCode, new_password: newPassword });
      navigate("/login");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-1 font-mono text-lg text-accent">Set new password</h1>
        <p className="mb-6 text-sm text-text-muted">Enter the code and your new password</p>

        {error && (
          <div className="mb-4">
            <Alert tone="danger">{error}</Alert>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input id="email" label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input id="otp-code" label="OTP code" value={otpCode} onChange={(e) => setOtpCode(e.target.value)} maxLength={6} required />
          <Input id="new-password" label="New password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
          <Button type="submit" disabled={loading}>
            {loading ? "Resetting..." : "Reset password"}
          </Button>
        </form>
      </Card>
    </div>
  );
}