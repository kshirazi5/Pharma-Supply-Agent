"use client";

import { useState, useCallback, createContext, useContext, ReactNode } from "react";
import { loginUser, getToken } from "@/lib/api";

interface AuthCtx {
  token: string | null;
  login: (u: string, p: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx>({
  token: null,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);

  const login = useCallback(async (username: string, password: string) => {
    const tok = await loginUser(username, password);
    setTokenState(tok);
  }, []);

  const logout = useCallback(() => setTokenState(null), []);

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
