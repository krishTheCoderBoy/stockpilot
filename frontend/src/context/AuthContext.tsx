import { createContext, useContext, useState, type ReactNode } from "react";
import { decodeToken } from "../lib/jwt";

interface AuthContextValue {
  token: string | null;
  role: string | null;
  login: (token: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));

  function login(newToken: string) {
    localStorage.setItem("access_token", newToken);
    setToken(newToken);
  }

  function logout() {
    localStorage.removeItem("access_token");
    setToken(null);
  }

  const role = token ? decodeToken(token)?.role ?? null : null;

  return (
    <AuthContext.Provider value={{ token, role, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}