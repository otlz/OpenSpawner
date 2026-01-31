"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import { adminApi, AdminUser } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import {
  Container,
  Users,
  Shield,
  ShieldOff,
  Trash2,
  Mail,
  RefreshCw,
  LogOut,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  ArrowLeft,
  Search,
  Monitor,
} from "lucide-react";

type StatusColor = "green" | "yellow" | "red";

function getStatusColor(user: AdminUser): StatusColor {
  const now = new Date();
  const lastUsed = user.last_used ? new Date(user.last_used) : null;
  const createdAt = user.created_at ? new Date(user.created_at) : now;

  // Berechne Tage seit letzter Nutzung oder Erstellung
  const referenceDate = lastUsed || createdAt;
  const daysSince = (now.getTime() - referenceDate.getTime()) / (1000 * 60 * 60 * 24);

  switch (user.state) {
    case "registered":
      // Unverifiziert: gelb < 1 Tag, rot >= 1 Tag
      return daysSince >= 1 ? "red" : "yellow";
    case "verified":
      // Verifiziert aber nie genutzt: gruen < 1 Tag, gelb >= 1 Tag, rot >= 7 Tage
      if (daysSince >= 7) return "red";
      if (daysSince >= 1) return "yellow";
      return "green";
    case "active":
      // Aktiv: gruen < 7 Tage, gelb >= 7 Tage, rot >= 30 Tage
      if (daysSince >= 30) return "red";
      if (daysSince >= 7) return "yellow";
      return "green";
    default:
      return "yellow";
  }
}

function getStatusBadgeColor(color: StatusColor) {
  switch (color) {
    case "green":
      return "bg-green-100 text-green-800 border-green-200";
    case "yellow":
      return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "red":
      return "bg-red-100 text-red-800 border-red-200";
  }
}

function getStateLabel(state: string) {
  switch (state) {
    case "registered":
      return "Unverifiziert";
    case "verified":
      return "Verifiziert";
    case "active":
      return "Aktiv";
    default:
      return state;
  }
}

function formatDate(dateString: string | null) {
  if (!dateString) return "-";
  return new Date(dateString).toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AdminPage() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    const { data, error } = await adminApi.getUsers();
    if (data) {
      setUsers(data.users);
    } else if (error) {
      setError(error);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(""), 3000);
  };

  const handleBlock = async (userId: number) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.blockUser(userId);
    if (error) {
      setError(error);
    } else {
      showSuccess(data?.message || "User gesperrt");
      fetchUsers();
    }
    setActionLoading(null);
  };

  const handleUnblock = async (userId: number) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.unblockUser(userId);
    if (error) {
      setError(error);
    } else {
      showSuccess(data?.message || "User entsperrt");
      fetchUsers();
    }
    setActionLoading(null);
  };

  const handleResendVerification = async (userId: number) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.resendVerification(userId);
    if (error) {
      setError(error);
    } else {
      showSuccess(data?.message || "Verifizierungs-Email gesendet");
    }
    setActionLoading(null);
  };

  const handleDeleteContainer = async (userId: number) => {
    if (!confirm("Container wirklich loeschen? Der User kann einen neuen Container starten.")) {
      return;
    }
    setActionLoading(userId);
    const { data, error } = await adminApi.deleteUserContainer(userId);
    if (error) {
      setError(error);
    } else {
      showSuccess(data?.message || "Container geloescht");
      fetchUsers();
    }
    setActionLoading(null);
  };

  const handleDeleteUser = async (userId: number, username: string) => {
    if (!confirm(`User "${username}" wirklich loeschen? Diese Aktion kann nicht rueckgaengig gemacht werden!`)) {
      return;
    }
    setActionLoading(userId);
    const { data, error } = await adminApi.deleteUser(userId);
    if (error) {
      setError(error);
    } else {
      showSuccess(data?.message || "User geloescht");
      fetchUsers();
    }
    setActionLoading(null);
  };

  const handleTakeover = async (userId: number) => {
    const reason = prompt("Grund fuer den Zugriff (optional):");
    if (reason === null) return; // Abgebrochen

    setActionLoading(userId);
    const { data, error } = await adminApi.startTakeover(userId, reason);
    if (error) {
      setError(error);
    } else {
      alert(data?.note || "Takeover gestartet (Dummy)");
    }
    setActionLoading(null);
  };

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  // Gefilterte Users
  const filteredUsers = users.filter(
    (u) =>
      u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Statistiken
  const stats = {
    total: users.length,
    active: users.filter((u) => u.state === "active").length,
    verified: users.filter((u) => u.state === "verified").length,
    unverified: users.filter((u) => u.state === "registered").length,
    blocked: users.filter((u) => u.is_blocked).length,
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/50">
      {/* Header */}
      <header className="border-b bg-background">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Dashboard
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <Shield className="h-6 w-6 text-primary" />
              <span className="text-lg font-semibold">Admin</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs">
                  {user?.username.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium">{user?.username}</span>
              <Badge variant="secondary" className="text-xs">
                Admin
              </Badge>
            </div>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Abmelden
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto p-4 md:p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Benutzerverwaltung</h1>
          <p className="text-muted-foreground">
            Verwalte alle registrierten Benutzer
          </p>
        </div>

        {/* Nachrichten */}
        {error && (
          <div className="mb-6 rounded-md bg-destructive/10 p-4 text-sm text-destructive">
            {error}
            <button
              onClick={() => setError("")}
              className="ml-2 underline"
            >
              Schliessen
            </button>
          </div>
        )}

        {successMessage && (
          <div className="mb-6 rounded-md bg-green-100 p-4 text-sm text-green-800">
            {successMessage}
          </div>
        )}

        {/* Statistiken */}
        <div className="mb-6 grid gap-4 md:grid-cols-5">
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <Users className="h-8 w-8 text-muted-foreground" />
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-xs text-muted-foreground">Gesamt</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <CheckCircle2 className="h-8 w-8 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{stats.active}</p>
                <p className="text-xs text-muted-foreground">Aktiv</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <Clock className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{stats.verified}</p>
                <p className="text-xs text-muted-foreground">Verifiziert</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <AlertCircle className="h-8 w-8 text-yellow-500" />
              <div>
                <p className="text-2xl font-bold">{stats.unverified}</p>
                <p className="text-xs text-muted-foreground">Unverifiziert</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <ShieldOff className="h-8 w-8 text-red-500" />
              <div>
                <p className="text-2xl font-bold">{stats.blocked}</p>
                <p className="text-xs text-muted-foreground">Gesperrt</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Suche */}
        <div className="mb-6 flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Benutzer suchen..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" onClick={fetchUsers}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Aktualisieren
          </Button>
        </div>

        {/* Benutzerliste */}
        <Card>
          <CardHeader>
            <CardTitle>Benutzer</CardTitle>
            <CardDescription>
              {filteredUsers.length} von {users.length} Benutzern
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredUsers.map((u) => {
                const statusColor = getStatusColor(u);
                const isCurrentUser = u.id === user?.id;

                return (
                  <div
                    key={u.id}
                    className={`flex items-center justify-between rounded-lg border p-4 ${
                      u.is_blocked ? "bg-red-50 border-red-200" : ""
                    }`}
                  >
                    {/* User Info */}
                    <div className="flex items-center gap-4">
                      <Avatar>
                        <AvatarFallback
                          className={`${
                            u.is_blocked
                              ? "bg-red-200 text-red-800"
                              : u.is_admin
                              ? "bg-primary text-primary-foreground"
                              : ""
                          }`}
                        >
                          {u.username.slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{u.username}</span>
                          {u.is_admin && (
                            <Badge variant="secondary" className="text-xs">
                              Admin
                            </Badge>
                          )}
                          {u.is_blocked && (
                            <Badge variant="destructive" className="text-xs">
                              Gesperrt
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">{u.email}</p>
                        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                          <span
                            className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 ${getStatusBadgeColor(
                              statusColor
                            )}`}
                          >
                            {statusColor === "green" && (
                              <CheckCircle2 className="h-3 w-3" />
                            )}
                            {statusColor === "yellow" && (
                              <AlertCircle className="h-3 w-3" />
                            )}
                            {statusColor === "red" && (
                              <XCircle className="h-3 w-3" />
                            )}
                            {getStateLabel(u.state)}
                          </span>
                          <span>|</span>
                          <span>
                            Letzte Aktivitaet: {formatDate(u.last_used)}
                          </span>
                          {u.container_id && (
                            <>
                              <span>|</span>
                              <span className="flex items-center gap-1">
                                <Container className="h-3 w-3" />
                                {u.container_id.slice(0, 8)}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Aktionen */}
                    <div className="flex items-center gap-2">
                      {actionLoading === u.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          {/* Verifizierungs-Email */}
                          {u.state === "registered" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleResendVerification(u.id)}
                              title="Verifizierungs-Email erneut senden"
                            >
                              <Mail className="h-4 w-4" />
                            </Button>
                          )}

                          {/* Login-Link erneut senden */}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleResendVerification(u.id)}
                            title="Login-Link erneut senden"
                          >
                            <Mail className="h-4 w-4" />
                          </Button>

                          {/* Container loeschen */}
                          {u.container_id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteContainer(u.id)}
                              title="Container loeschen"
                            >
                              <Container className="h-4 w-4" />
                            </Button>
                          )}

                          {/* Takeover (Dummy) */}
                          {u.container_id && !isCurrentUser && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleTakeover(u.id)}
                              title="Container-Zugriff (Phase 2)"
                              disabled
                            >
                              <Monitor className="h-4 w-4" />
                            </Button>
                          )}

                          {/* Sperren/Entsperren */}
                          {!isCurrentUser && !u.is_admin && (
                            <>
                              {u.is_blocked ? (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleUnblock(u.id)}
                                  title="Entsperren"
                                >
                                  <Shield className="h-4 w-4 text-green-600" />
                                </Button>
                              ) : (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleBlock(u.id)}
                                  title="Sperren"
                                >
                                  <ShieldOff className="h-4 w-4 text-red-600" />
                                </Button>
                              )}
                            </>
                          )}

                          {/* Loeschen */}
                          {!isCurrentUser && !u.is_admin && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteUser(u.id, u.username)}
                              title="Benutzer loeschen"
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                );
              })}

              {filteredUsers.length === 0 && (
                <div className="py-8 text-center text-muted-foreground">
                  Keine Benutzer gefunden
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
