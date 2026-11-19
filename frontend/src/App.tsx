import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AdminRoute } from "./components/AdminRoute";
import { Login } from "./pages/auth/Login";
import { Register } from "./pages/auth/Register";
import { VerifyRegistrationOtp } from "./pages/auth/VerifyRegistrationOtp";
import { VerifyLoginOtp } from "./pages/auth/VerifyLoginOtp";
import { ForgotPassword } from "./pages/auth/ForgotPassword";
import { ResetPassword } from "./pages/auth/ResetPassword";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "./pages/Dashboard";
import { ProductsList } from "./pages/products/ProductsList";
import { WarehousesList } from "./pages/warehouses/WarehousesList";
import { InventoryList } from "./pages/inventory/InventoryList";
import { MovementsList } from "./pages/movements/MovementsList";
import { SuppliersList } from "./pages/suppliers/SuppliersList";
import { POList } from "./pages/purchase-orders/POList";
import { PODetail } from "./pages/purchase-orders/PODetail";
import { ThemeProvider } from "./context/ThemeContext";
import { Profile } from "./pages/profile/Profile";
import { Settings } from "./pages/settings/Settings";
import { PlanningPage } from "./pages/planning/PlanningPage";
import { ChatProvider } from "./context/ChatContext";
import { ForgotUsername } from "./pages/auth/ForgotUsername";


const queryClient = new QueryClient();

// The landing page (GSAP, Lenis, three.js) is a separate chunk, so the dashboard never pays for it.
const Landing = lazy(() => import("./pages/landing/Landing").then((m) => ({ default: m.Landing })));

function RootRoute() {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return (
    <Suspense fallback={<div style={{ minHeight: "100vh", background: "#050b1f" }} />}>
      <Landing />
    </Suspense>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ChatProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<RootRoute />} />
              <Route path="/login" element={<Login />} />
              <Route
                path="/settings/users/new"
                element={
                  <AdminRoute>
                    <Register />
                  </AdminRoute>
                }
              />
              <Route path="/verify-otp" element={<VerifyRegistrationOtp />} />
              <Route path="/verify-login-otp" element={<VerifyLoginOtp />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/forgot-username" element={<ForgotUsername />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/products"
                element={
                  <ProtectedRoute>
                    <ProductsList />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/warehouses"
                element={
                  <ProtectedRoute>
                    <WarehousesList />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/inventory"
                element={
                  <ProtectedRoute>
                    <InventoryList />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/movements"
                element={
                  <ProtectedRoute>
                    <MovementsList />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/suppliers"
                element={
                  <ProtectedRoute>
                    <SuppliersList />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/purchase-orders"
                element={
                  <ProtectedRoute>
                    <POList />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/purchase-orders/:id"
                element={
                  <ProtectedRoute>
                    <PODetail />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/planning"
                element={
                  <ProtectedRoute>
                    <PlanningPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <Profile />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <Settings />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </BrowserRouter>
          </ChatProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}