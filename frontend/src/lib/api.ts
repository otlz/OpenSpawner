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

// ============================================================
// Auth Interfaces
// ============================================================

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: number;
    username: string;
    email: string;
    is_admin: boolean;
    state: "registered" | "verified" | "active";
  };
}

export interface SignupResponse {
  message: string;
  user: {
    id: number;
    username: string;
    email: string;
    is_admin: boolean;
  };
  email_sent: boolean;
}

export interface UserResponse {
  user: {
    id: number;
    username: string;
    email: string;
    is_admin: boolean;
    state: "registered" | "verified" | "active";
    last_used: string | null;
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

// ============================================================
// Admin Interfaces
// ============================================================

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  is_blocked: boolean;
  blocked_at: string | null;
  state: "registered" | "verified" | "active";
  last_used: string | null;
  created_at: string | null;
  container_id: string | null;
}

export interface AdminUsersResponse {
  users: AdminUser[];
  total: number;
}

export interface AdminUserResponse {
  user: AdminUser & {
    container_status: string;
  };
}

export interface AdminActionResponse {
  message: string;
  user?: AdminUser;
  email_sent?: boolean;
}

export interface TakeoverResponse {
  message: string;
  session_id: number;
  status: string;
  note?: string;
}

export interface TakeoverSession {
  id: number;
  admin_id: number;
  admin_username: string | null;
  target_user_id: number;
  target_username: string | null;
  started_at: string | null;
  reason: string | null;
}

export interface ActiveTakeoversResponse {
  sessions: TakeoverSession[];
  total: number;
}

// ============================================================
// API Functions
// ============================================================

export const api = {
  // Auth
  login: (username: string, password: string) =>
    fetchApi<LoginResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  signup: (username: string, email: string, password: string) =>
    fetchApi<SignupResponse>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    }),

  logout: () =>
    fetchApi<{ message: string }>("/api/auth/logout", {
      method: "POST",
    }),

  resendVerification: (email: string) =>
    fetchApi<{ message: string; email_sent: boolean }>(
      "/api/auth/resend-verification",
      {
        method: "POST",
        body: JSON.stringify({ email }),
      }
    ),

  // User
  getUser: () => fetchApi<UserResponse>("/api/user/me"),

  // Container
  getContainerStatus: () =>
    fetchApi<ContainerStatusResponse>("/api/container/status"),

  restartContainer: () =>
    fetchApi<ContainerRestartResponse>("/api/container/restart", {
      method: "POST",
    }),
};

// ============================================================
// Admin API Functions
// ============================================================

export const adminApi = {
  // Users
  getUsers: () => fetchApi<AdminUsersResponse>("/api/admin/users"),

  getUser: (id: number) =>
    fetchApi<AdminUserResponse>(`/api/admin/users/${id}`),

  // Block/Unblock
  blockUser: (id: number) =>
    fetchApi<AdminActionResponse>(`/api/admin/users/${id}/block`, {
      method: "POST",
    }),

  unblockUser: (id: number) =>
    fetchApi<AdminActionResponse>(`/api/admin/users/${id}/unblock`, {
      method: "POST",
    }),

  // Password Reset
  resetPassword: (id: number, password?: string) =>
    fetchApi<AdminActionResponse>(`/api/admin/users/${id}/reset-password`, {
      method: "POST",
      body: JSON.stringify(password ? { password } : {}),
    }),

  // Verification
  resendVerification: (id: number) =>
    fetchApi<AdminActionResponse>(`/api/admin/users/${id}/resend-verification`, {
      method: "POST",
    }),

  // Container
  deleteUserContainer: (id: number) =>
    fetchApi<AdminActionResponse>(`/api/admin/users/${id}/container`, {
      method: "DELETE",
    }),

  // Delete User
  deleteUser: (id: number) =>
    fetchApi<AdminActionResponse>(`/api/admin/users/${id}`, {
      method: "DELETE",
    }),

  // Takeover (Phase 2 - Dummy)
  startTakeover: (id: number, reason?: string) =>
    fetchApi<TakeoverResponse>(`/api/admin/users/${id}/takeover`, {
      method: "POST",
      body: JSON.stringify({ reason: reason || "" }),
    }),

  endTakeover: (sessionId: number) =>
    fetchApi<{ message: string; session_id: number }>(
      `/api/admin/takeover/${sessionId}/end`,
      {
        method: "POST",
      }
    ),

  getActiveTakeovers: () =>
    fetchApi<ActiveTakeoversResponse>("/api/admin/takeover/active"),
};
