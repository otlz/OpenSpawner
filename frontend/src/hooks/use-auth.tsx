"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { api, LoginResponse, UserResponse } from "@/lib/api";

export interface User {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  state: "registered" | "verified" | "active";
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (
    username: string,
    password: string
  ) => Promise<{ success: boolean; error?: string; needsVerification?: boolean }>;
  signup: (
    username: string,
    email: string,
    password: string
  ) => Promise<{ success: boolean; error?: string; message?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (storedToken) {
      setToken(storedToken);
      fetchUser(storedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchUser = async (accessToken?: string) => {
    const currentToken = accessToken || token;
    if (!currentToken) {
      setIsLoading(false);
      return;
    }

    const { data, error } = await api.getUser();
    if (data && !error) {
      setUser({
        id: data.user.id,
        username: data.user.username,
        email: data.user.email,
        is_admin: data.user.is_admin,
        state: data.user.state,
      });
    } else {
      localStorage.removeItem("token");
      setToken(null);
      setUser(null);
    }
    setIsLoading(false);
  };

  const login = async (
    username: string,
    password: string
  ): Promise<{ success: boolean; error?: string; needsVerification?: boolean }> => {
    const { data, error } = await api.login(username, password);

    if (error || !data) {
      // Pruefe ob Verifizierung erforderlich
      const needsVerification = error?.includes("nicht verifiziert");
      return {
        success: false,
        error: error || "Login fehlgeschlagen",
        needsVerification
      };
    }

    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
    setUser({
      id: data.user.id,
      username: data.user.username,
      email: data.user.email,
      is_admin: data.user.is_admin,
      state: data.user.state,
    });
    return { success: true };
  };

  const signup = async (
    username: string,
    email: string,
    password: string
  ): Promise<{ success: boolean; error?: string; message?: string }> => {
    const { data, error } = await api.signup(username, email, password);

    if (error || !data) {
      return { success: false, error: error || "Registrierung fehlgeschlagen" };
    }

    // Nach Signup wird kein Token mehr zurueckgegeben
    // User muss erst Email verifizieren
    return {
      success: true,
      message: data.message
    };
  };

  const logout = async () => {
    await api.logout();
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  return (
    <AuthContext.Provider
      value={{ user, token, isLoading, login, signup, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
