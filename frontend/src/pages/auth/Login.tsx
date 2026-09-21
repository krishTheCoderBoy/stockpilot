import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Package, ArrowRight } from "lucide-react";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { api, extractErrorMessage } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.post("/auth/login", { email, password });
      if (res.data.otp_required) {
        navigate("/verify-login-otp", { state: { email } });
      } else {
        login(res.data.access_token);
        navigate("/dashboard");
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-surface p-12 lg:flex">
        <span className="font-mono text-lg text-accent">StockPilot</span>
        <div>
          <Package size={28} className="text-accent" />
          <h2 className="mt-4 max-w-sm text-2xl font-medium text-text">
            Every unit accounted for, every movement on record.
          </h2>
          <p className="mt-3 max-w-sm text-sm text-text-muted">
            Sign in to manage products, warehouses, and purchase orders across your operation.
          </p>
        </div>
        <p className="text-xs text-text-muted">© {new Date().getFullYear()} StockPilot</p>
      </div>

      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <h1 className="mb-1 text-xl font-medium text-text">Sign in</h1>
          <p className="mb-6 text-sm text-text-muted">Welcome back — enter your details to continue</p>

          {error && (
            <div className="mb-4">
              <Alert tone="danger">{error}</Alert>
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <div className="flex justify-end">
              <Link to="/forgot-password" className="text-xs text-accent hover:underline">
                Forgot password?
              </Link>
            </div>
            <Button type="submit" disabled={loading} className="justify-center">
              {loading ? "Signing in..." : <>Sign in <ArrowRight size={16} /></>}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-text-muted">
            Forgot your username?{" "}
            <Link to="/forgot-username" className="text-accent hover:underline">
              Recover it
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}