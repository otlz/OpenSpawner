const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

interface FetchApiOptions extends RequestInit {
  queryParams?: Record<string, string>;
}

async function fetchApi<T>(
  endpoint: string,
  options: FetchApiOptions = {}
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

  let url = `${API_BASE}${endpoint}`;

  // Query-Parameter anhängen
  if (options.queryParams) {
    const params = new URLSearchParams(options.queryParams);
    url += `?${params.toString()}`;
  }

  try {
    const response = await fetch(url, {
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

export interface User {
  id: number;
  email: string;
  slug: string;
  is_admin: boolean;
  state: "registered" | "verified" | "active";
  last_used?: string | null;
  created_at?: string | null;
  container_id?: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface SignupResponse {
  message: string;
}

export interface MagicLinkMessage {
  message: string;
}

export interface UserResponse {
  user: User;
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

export interface Container {
  type: string;
  display_name: string;
  description: string;
  status: 'not_created' | 'running' | 'stopped' | 'error';
  service_url: string;
  container_id: string | null;
  created_at: string | null;
  last_used: string | null;
}

export interface ContainersResponse {
  containers: Container[];
}

export interface LaunchResponse {
  message: string;
  service_url: string;
  container_id: string;
  status: string;
}

// ============================================================
// Admin Interfaces
// ============================================================

export interface AdminUser extends User {
  is_blocked: boolean;
  blocked_at: string | null;
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
  deleted?: number;
  failed?: string[];
  summary?: {
    containers_deleted: number;
    containers_failed: string[];
    magic_tokens_deleted: number;
    takeover_sessions_deleted: number;
  };
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
  admin_email: string | null;
  target_user_id: number;
  target_email: string | null;
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
  auth: {
    // Magic Link Login
    login: (email: string) =>
      fetchApi<MagicLinkMessage>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),

    // Magic Link Signup
    signup: (email: string) =>
      fetchApi<MagicLinkMessage>("/api/auth/signup", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),

    // Verify Signup Token
    verifySignup: (token: string) =>
      fetchApi<LoginResponse>("/api/auth/verify-signup", {
        method: "GET",
        queryParams: { token },
      }),

    // Verify Login Token
    verifyLogin: (token: string) =>
      fetchApi<LoginResponse>("/api/auth/verify-login", {
        method: "GET",
        queryParams: { token },
      }),

    // Logout
    logout: () =>
      fetchApi<{ message: string }>("/api/auth/logout", {
        method: "POST",
      }),
  },

  // User
  getUser: () => fetchApi<UserResponse>("/api/user/me"),

  // Container
  getContainerStatus: () =>
    fetchApi<ContainerStatusResponse>("/api/container/status"),

  restartContainer: () =>
    fetchApi<ContainerRestartResponse>("/api/container/restart", {
      method: "POST",
    }),

  // Multi-Container Support
  getUserContainers: () =>
    fetchApi<ContainersResponse>("/api/user/containers"),

  launchContainer: (containerType: string) =>
    fetchApi<LaunchResponse>(`/api/container/launch/${containerType}`, {
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

  // Resend Magic Link (for admins to resend login links)
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

  // Bulk Delete Users
  bulkDeleteUsers: (user_ids: number[]) =>
    fetchApi<AdminActionResponse>("/api/admin/users/bulk-delete", {
      method: "POST",
      body: JSON.stringify({ user_ids }),
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
