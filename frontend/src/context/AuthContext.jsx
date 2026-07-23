import { createContext, useContext, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    const saved = localStorage.getItem("auth");
    return saved ? JSON.parse(saved) : null;
  });

  async function login(username, password) {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Login failed");
    }
    const data = await res.json();
    return storeSession(data);
  }

  async function signup(payload) {
    const res = await fetch(`${API_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Signup failed");
    }
    const data = await res.json();
    return storeSession(data);
  }

  function storeSession(data) {
    const session = { token: data.access_token, role: data.role, fullName: data.full_name };
    localStorage.setItem("auth", JSON.stringify(session));
    setAuth(session);
    return session;
  }

  function logout() {
    localStorage.removeItem("auth");
    setAuth(null);
  }

  return <AuthContext.Provider value={{ auth, login, signup, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

export { API_URL };
