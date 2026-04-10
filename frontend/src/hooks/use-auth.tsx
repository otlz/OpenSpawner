"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { api, User as ApiUser } from "@/lib/api";

export type User = ApiUser;

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: (email: string) => Promise<{ success: boolean; message?: string }>;
  signup: (email: string) => Promise<{ success: boolean; message?: string }>;
  verifySignup: (token: string) => Promise<{ success: boolean }>;
  verifyLogin: (token: string) => Promise<{ success: boolean }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchUser();
  }, []);

  const fetchUser = async () => {
    const { data, error: apiError } = await api.getUser();
    if (data && !apiError) {
      setUser(data.user);
      setError(null);
    } else {
      setUser(null);
    }
    setIsLoading(false);
  };

  const login = async (email: string): Promise<{ success: boolean; message?: string }> => {
    try {
      setError(null);
      const { data, error: apiError } = await api.auth.login(email);

      if (apiError) {
        setError(apiError);
        return { success: false };
      }

      return { success: true, message: data?.message };
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Login fehlgeschlagen";
      setError(errorMsg);
      return { success: false };
    }
  };

  const signup = async (email: string): Promise<{ success: boolean; message?: string }> => {
    try {
      setError(null);
      const { data, error: apiError } = await api.auth.signup(email);

      if (apiError) {
        setError(apiError);
        return { success: false };
      }

      return { success: true, message: data?.message };
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Registrierung fehlgeschlagen";
      setError(errorMsg);
      return { success: false };
    }
  };

  const verifySignup = async (signupToken: string): Promise<{ success: boolean }> => {
    try {
      setError(null);
      const { data, error: apiError } = await api.auth.verifySignup(signupToken);

      if (apiError) {
        setError(apiError);
        return { success: false };
      }

      if (data) {
        setUser(data.user);
        return { success: true };
      }

      return { success: false };
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Verifizierung fehlgeschlagen";
      setError(errorMsg);
      return { success: false };
    }
  };

  const verifyLogin = async (loginToken: string): Promise<{ success: boolean }> => {
    try {
      setError(null);
      const { data, error: apiError } = await api.auth.verifyLogin(loginToken);

      if (apiError) {
        setError(apiError);
        return { success: false };
      }

      if (data) {
        setUser(data.user);
        return { success: true };
      }

      return { success: false };
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Login fehlgeschlagen";
      setError(errorMsg);
      return { success: false };
    }
  };

  const logout = async () => {
    await api.auth.logout();
    setUser(null);
    setError(null);
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        error,
        login,
        signup,
        verifySignup,
        verifyLogin,
        logout,
        refreshUser,
      }}
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
