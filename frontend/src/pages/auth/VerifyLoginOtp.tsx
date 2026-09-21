import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";

export function VerifyLoginOtp() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();
  const email = (location.state as { email?: string })?.email ?? "";
  const [otpCode, setOtpCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [resendMessage, setResendMessage] = useState<string | null>(null);

  async function handleResend() {
    setResending(true);
    setResendMessage(null);
    try {
      await api.post("/auth/resend-login-otp", { email });
      setResendMessage("A new code has been sent.");
    } finally {
      setResending(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.post("/auth/verify-login-otp", { email, otp_code: otpCode });
      login(res.data.access_token);
      navigate("/");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-1 font-mono text-lg text-accent">Verification required</h1>
        <p className="mb-6 text-sm text-text-muted">
          Enter the code sent to {email || "your email"}
        </p>

        {error && (
          <div className="mb-4">
            <Alert tone="danger">{error}</Alert>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            label="OTP code"
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value)}
            maxLength={6}
            required
          />
          <Button type="submit" disabled={loading}>
            {loading ? "Verifying..." : "Verify and sign in"}
          </Button>
        </form>

        {resendMessage && (
          <p className="mt-3 text-center text-xs text-flow">{resendMessage}</p>
        )}
        <button
          onClick={handleResend}
          disabled={resending}
          className="mt-3 w-full text-center text-xs text-accent hover:underline disabled:opacity-50"
        >
          {resending ? "Sending..." : "Resend code"}
        </button>
      </Card>
    </div>
  );
}