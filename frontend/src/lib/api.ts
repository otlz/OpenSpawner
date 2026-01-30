const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      return { error: data.error || "Ein Fehler ist aufgetreten" };
    }

    return { data };
  } catch (error) {
    return { error: "Netzwerkfehler - Server nicht erreichbar" };
  }
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: number;
    username: string;
    email: string;
  };
}

export interface UserResponse {
  user: {
    id: number;
    username: string;
    email: string;
    created_at: string | null;
  };
  container: {
    id: string | null;
    port: number | null;
    status: string;
    service_url: string;
  };
}

export interface ContainerStatusResponse {
  container_id: string | null;
  status: string;
}

export interface ContainerRestartResponse {
  message: string;
  container_id: string;
  status: string;
}

export const api = {
  login: (username: string, password: string) =>
    fetchApi<LoginResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  signup: (username: string, email: string, password: string) =>
    fetchApi<LoginResponse>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    }),

  logout: () =>
    fetchApi<{ message: string }>("/api/auth/logout", {
      method: "POST",
    }),

  getUser: () => fetchApi<UserResponse>("/api/user/me"),

  getContainerStatus: () =>
    fetchApi<ContainerStatusResponse>("/api/container/status"),

  restartContainer: () =>
    fetchApi<ContainerRestartResponse>("/api/container/restart", {
      method: "POST",
    }),
};
