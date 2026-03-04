import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

interface User {
  id: string;
  name: string;
  email: string;
  role: "patient" | "pharmacist";
  patient_id?: string;
  staff_id?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (data: RegisterData) => Promise<boolean>;
  logout: () => void;
  apiHeaders: () => Record<string, string>;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
  role: "patient" | "pharmacist";
  age?: number;
  gender?: string;
  pharmacistCode?: string;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  // Restore session from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("dhanvan_token");
    const savedUser = localStorage.getItem("dhanvan_user");
    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem("dhanvan_token");
        localStorage.removeItem("dhanvan_user");
      }
    }
  }, []);

  const apiHeaders = useCallback(() => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return headers;
  }, [token]);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) return false;
      const data = await res.json();

      const userData: User = {
        id: data.patient_id || data.staff_id || "",
        name: data.name,
        email,
        role: data.role,
        patient_id: data.role === "patient" ? data.patient_id : undefined,
        staff_id: data.role === "pharmacist" ? data.patient_id : undefined,
      };

      setToken(data.access_token);
      setUser(userData);
      localStorage.setItem("dhanvan_token", data.access_token);
      localStorage.setItem("dhanvan_user", JSON.stringify(userData));
      return true;
    } catch (err) {
      console.error("Login error:", err);
      return false;
    }
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    try {
      const endpoint = data.role === "pharmacist"
        ? "/api/auth/register/pharmacist"
        : "/api/auth/register/patient";

      const body: Record<string, unknown> = {
        name: data.name,
        email: data.email,
        password: data.password,
      };
      if (data.role === "patient") {
        body.age = data.age || 30;
        body.gender = data.gender || "Unknown";
      } else {
        body.pharmacist_code = data.pharmacistCode;
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) return false;

      // Auto-login after registration
      return await login(data.email, data.password);
    } catch (err) {
      console.error("Register error:", err);
      return false;
    }
  }, [login]);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("dhanvan_token");
    localStorage.removeItem("dhanvan_user");
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!user, login, register, logout, apiHeaders }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
