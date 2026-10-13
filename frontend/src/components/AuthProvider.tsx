import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import * as api from "../api/auth";
import type { UserRead } from "../api/auth";

type Mode = "reader" | "writer";

interface AuthContextValue {
  user: UserRead | null;
  mode: Mode;
  loading: boolean;
  register: typeof api.register;
  login: typeof api.login;
  logout: () => Promise<{ ok: boolean }>;
  setMode: (mode: Mode) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [mode, setMode] = useState<Mode>("reader");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void api.me().then((u) => {
      setUser(u);
      setLoading(false);
    });
  }, []);

  async function register(username: string, password: string) {
    const res = await api.register(username, password);
    if (res.ok) {
      setUser(res.user);
      setMode("reader");
    }
    return res;
  }

  async function login(username: string, password: string) {
    const res = await api.login(username, password);
    if (res.ok) {
      setUser(res.user);
      setMode("reader");
    }
    return res;
  }

  async function logout() {
    const res = await api.logout();
    if (res.ok) setUser(null);
    return res;
  }

  return (
    <AuthContext.Provider value={{ user, mode, loading, register, login, logout, setMode }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
