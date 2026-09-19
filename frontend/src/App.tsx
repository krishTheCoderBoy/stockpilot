import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AppShell } from "./components/shell/AppShell";
import { Login } from "./pages/auth/Login";
import { Register } from "./pages/auth/Register";
import { VerifyRegistrationOtp } from "./pages/auth/VerifyRegistrationOtp";
import { VerifyLoginOtp } from "./pages/auth/VerifyLoginOtp";
import { ForgotPassword } from "./pages/auth/ForgotPassword";
import { ResetPassword } from "./pages/auth/ResetPassword";

function DashboardPage() {
  return (
    <AppShell breadcrumb="Dashboard">
      <p className="text-text-muted">Dashboard content coming in Milestone 22.</p>
    </AppShell>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-otp" element={<VerifyRegistrationOtp />} />
          <Route path="/verify-login-otp" element={<VerifyLoginOtp />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}