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
  X,
  ChevronDown,
} from "lucide-react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

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

function formatDate(dateString: string | null | undefined) {
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
  const [selectedUserIds, setSelectedUserIds] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<"users" | "containers">("users");
  const [selectedContainerIds, setSelectedContainerIds] = useState<Set<number>>(new Set());
  const [expandedUserIds, setExpandedUserIds] = useState<Set<number>>(new Set());
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deleteDialogData, setDeleteDialogData] = useState<{
    containerIds: number[];
    userSummary: { email: string; count: number }[];
  } | null>(null);

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

  // Expand/Collapse Helper
  const toggleUserExpand = (userId: number) => {
    const newExpanded = new Set(expandedUserIds);
    if (newExpanded.has(userId)) {
      newExpanded.delete(userId);
    } else {
      newExpanded.add(userId);
    }
    setExpandedUserIds(newExpanded);
  };

  // Dialog Helper für Bulk-Delete
  const openBulkDeleteDialog = () => {
    if (selectedContainerIds.size === 0) {
      toast.error("Keine Container ausgewählt");
      return;
    }

    // Erstelle Zusammenfassung nach User
    const userMap = new Map<number, { email: string; count: number }>();

    for (const containerId of selectedContainerIds) {
      const user = users.find(u =>
        u.containers?.some(c => c.id === containerId)
      );
      if (user) {
        const existing = userMap.get(user.id) || { email: user.email, count: 0 };
        existing.count++;
        userMap.set(user.id, existing);
      }
    }

    setDeleteDialogData({
      containerIds: Array.from(selectedContainerIds),
      userSummary: Array.from(userMap.values())
    });
    setIsDeleteDialogOpen(true);
  };

  // Bestätigte Bulk-Delete
  const handleConfirmBulkDelete = async () => {
    if (!deleteDialogData) return;

    setIsDeleteDialogOpen(false);
    toast.loading(
      `Lösche ${deleteDialogData.containerIds.length} Container...`,
      { id: "bulk-delete-containers" }
    );

    // Gruppiere Container nach User-ID
    const containersByUser = new Map<number, number[]>();

    for (const containerId of deleteDialogData.containerIds) {
      const user = users.find(u =>
        u.containers?.some(c => c.id === containerId)
      );
      if (user) {
        if (!containersByUser.has(user.id)) {
          containersByUser.set(user.id, []);
        }
        containersByUser.get(user.id)!.push(containerId);
      }
    }

    let totalDeleted = 0;
    let totalFailed = 0;

    // Lösche Container pro User
    for (const [userId, containerIds] of containersByUser) {
      const { data, error } = await adminApi.deleteUserContainer(userId, containerIds);

      if (error) {
        totalFailed += containerIds.length;
      } else if (data) {
        // Parse Response-Body (nach Backend-Fix)
        totalDeleted += data.deleted || 0;
        totalFailed += (data.failed?.length || 0);
      }
    }

    toast.success(`${totalDeleted} Container gelöscht`, {
      id: "bulk-delete-containers",
      description: totalFailed > 0 ? `${totalFailed} fehlgeschlagen` : undefined,
    });

    fetchUsers();
    setSelectedContainerIds(new Set());
    setDeleteDialogData(null);
  };

  // Bulk-Selection Helpers
  const toggleUserSelection = (userId: number) => {
    const newSelection = new Set(selectedUserIds);
    if (newSelection.has(userId)) {
      newSelection.delete(userId);
    } else {
      newSelection.add(userId);
    }
    setSelectedUserIds(newSelection);
  };

  const selectAllFiltered = () => {
    const selectableIds = filteredUsers
      .filter((u) => u.id !== user?.id && !u.is_admin)
      .map((u) => u.id);
    setSelectedUserIds(new Set(selectableIds));
  };

  const deselectAll = () => {
    setSelectedUserIds(new Set());
  };

  // Single Actions
  const handleBlock = async (userId: number) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.blockUser(userId);
    if (error) {
      toast.error(`Fehler: ${error}`);
    } else {
      toast.success(data?.message || "User gesperrt");
      fetchUsers();
    }
    setActionLoading(null);
  };

  const handleUnblock = async (userId: number) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.unblockUser(userId);
    if (error) {
      toast.error(`Fehler: ${error}`);
    } else {
      toast.success(data?.message || "User entsperrt");
      fetchUsers();
    }
    setActionLoading(null);
  };

  const handleResendVerification = async (userId: number) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.resendVerification(userId);
    if (error) {
      toast.error(`Fehler: ${error}`);
    } else {
      toast.success(data?.message || "Verifizierungs-Email gesendet");
    }
    setActionLoading(null);
  };

  const handleDeleteUser = async (userId: number, userEmail: string) => {
    if (!confirm(
      `⚠️ ACHTUNG: User "${userEmail}" VOLLSTAENDIG loeschen?\n\n` +
      `Dies löscht:\n` +
      `- User-Account und alle Daten\n` +
      `- Alle Docker-Container\n` +
      `- Alle Magic Link Tokens\n` +
      `- Alle Takeover-Sessions\n\n` +
      `Diese Aktion kann NICHT rueckgaengig gemacht werden!`
    )) {
      return;
    }
    setActionLoading(userId);
    const { data, error } = await adminApi.deleteUser(userId);
    if (error) {
      toast.error(`Fehler: ${error}`);
    } else {
      toast.success(`User gelöscht: ${userEmail}`, {
        description: data?.summary
          ? `${data.summary.containers_deleted} Container, ${data.summary.magic_tokens_deleted} Tokens entfernt`
          : undefined,
        duration: 5000,
      });
      fetchUsers();
    }
    setActionLoading(null);
  };

  const handleTakeover = async (userId: number) => {
    const reason = prompt("Grund fuer den Zugriff (optional):");
    if (reason === null) return;

    setActionLoading(userId);
    const { data, error } = await adminApi.startTakeover(userId, reason);
    if (error) {
      toast.error(`Fehler: ${error}`);
    } else {
      toast.info(data?.note || "Takeover gestartet (Dummy)", { duration: 4000 });
    }
    setActionLoading(null);
  };

  // Bulk Actions
  const handleBulkBlock = async () => {
    if (!confirm(`${selectedUserIds.size} User sperren?`)) {
      return;
    }

    toast.loading(`Sperre ${selectedUserIds.size} User...`, { id: "bulk-block" });

    let success = 0;
    let failed = 0;

    for (const userId of selectedUserIds) {
      const { error } = await adminApi.blockUser(userId);
      if (error) {
        failed++;
      } else {
        success++;
      }
    }

    toast.success(`${success} User gesperrt`, {
      id: "bulk-block",
      description: failed > 0 ? `${failed} fehlgeschlagen` : undefined,
    });

    fetchUsers();
    deselectAll();
  };

  const handleBulkUnblock = async () => {
    if (!confirm(`${selectedUserIds.size} User entsperren?`)) {
      return;
    }

    toast.loading(`Entsperre ${selectedUserIds.size} User...`, { id: "bulk-unblock" });

    let success = 0;
    let failed = 0;

    for (const userId of selectedUserIds) {
      const { error } = await adminApi.unblockUser(userId);
      if (error) {
        failed++;
      } else {
        success++;
      }
    }

    toast.success(`${success} User entsperrt`, {
      id: "bulk-unblock",
      description: failed > 0 ? `${failed} fehlgeschlagen` : undefined,
    });

    fetchUsers();
    deselectAll();
  };

  const handleBulkDeleteUsers = async () => {
    const selectedUsers = Array.from(selectedUserIds)
      .map((id) => users.find((u) => u.id === id))
      .filter(Boolean) as AdminUser[];

    const userList = selectedUsers.map((u) => u.email).join("\n");

    // Schritt 1: Vorschau
    if (!confirm(
      `⚠️ WARNUNG: ${selectedUserIds.size} User VOLLSTAENDIG löschen?\n\n` +
      `Betroffene User:\n${userList}\n\n` +
      `Dies löscht:\n` +
      `- User-Accounts und alle Daten\n` +
      `- Alle Docker-Container\n` +
      `- Alle Magic Link Tokens\n` +
      `- Alle Takeover-Sessions\n\n` +
      `Klicken Sie OK für finalen Bestätigungsschritt.`
    )) {
      return;
    }

    // Schritt 2: Finale Bestätigung
    const confirmation = prompt(
      `FINALE BESTAETIGUNG:\n\n` +
      `Geben Sie die Anzahl der zu löschenden User ein (${selectedUserIds.size}):`
    );

    if (confirmation !== String(selectedUserIds.size)) {
      toast.error("Bulk-Delete abgebrochen (falsche Bestätigung)");
      return;
    }

    toast.loading(`Lösche ${selectedUserIds.size} User...`, { id: "bulk-delete-users" });

    let success = 0;
    let failed = 0;
    const errors: string[] = [];

    for (const userId of selectedUserIds) {
      const selectedUser = selectedUsers.find((u) => u.id === userId);
      const { error } = await adminApi.deleteUser(userId);

      if (error) {
        failed++;
        errors.push(`${selectedUser?.email}: ${error}`);
      } else {
        success++;
      }
    }

    toast.success(`${success} User gelöscht`, {
      id: "bulk-delete-users",
      description: failed > 0 ? `${failed} fehlgeschlagen. Siehe Logs.` : "Alle Daten vollständig entfernt",
      duration: 8000,
    });

    if (errors.length > 0) {
      console.error("Bulk-Delete Errors:", errors);
    }

    fetchUsers();
    deselectAll();
  };

  // Container Actions (Phase 7)
  const toggleContainerSelection = (containerId: number) => {
    const newSelection = new Set(selectedContainerIds);
    if (newSelection.has(containerId)) {
      newSelection.delete(containerId);
    } else {
      newSelection.add(containerId);
    }
    setSelectedContainerIds(newSelection);
  };

  const handleBlockContainer = async (containerId: number, containerType: string) => {
    if (!confirm(`Container "${containerType}" sperren?\n\nDer Container wird gestoppt und kann vom User nicht neu gestartet werden.`)) {
      return;
    }

    setActionLoading(containerId);
    const { error } = await adminApi.blockContainer(containerId);
    if (error) {
      toast.error(`Fehler: ${error}`);
    } else {
      toast.success(`Container ${containerType} gesperrt`);
      fetchUsers();
    }
    setActionLoading(null);
  };

  const handleUnblockContainer = async (containerId: number, containerType: string) => {
    setActionLoading(containerId);
    const { error } = await adminApi.unblockContainer(containerId);
    if (error) {
      toast.error(`Fehler: ${error}`);
    } else {
      toast.success(`Container ${containerType} entsperrt`, {
        description: "User kann Container jetzt manuell starten",
      });
      fetchUsers();
    }
    setActionLoading(null);
  };

  const handleBulkBlockContainers = async () => {
    if (!confirm(`${selectedContainerIds.size} Container sperren?`)) {
      return;
    }

    toast.loading(`Sperre ${selectedContainerIds.size} Container...`, { id: "bulk-block-containers" });

    let success = 0;
    let failed = 0;

    for (const containerId of selectedContainerIds) {
      const { error } = await adminApi.blockContainer(containerId);
      if (error) {
        failed++;
      } else {
        success++;
      }
    }

    toast.success(`${success} Container gesperrt`, {
      id: "bulk-block-containers",
      description: failed > 0 ? `${failed} fehlgeschlagen` : undefined,
    });

    fetchUsers();
    setSelectedContainerIds(new Set());
  };

  const handleBulkUnblockContainers = async () => {
    if (!confirm(`${selectedContainerIds.size} Container entsperren?`)) {
      return;
    }

    toast.loading(`Entsperre ${selectedContainerIds.size} Container...`, { id: "bulk-unblock-containers" });

    let success = 0;
    let failed = 0;

    for (const containerId of selectedContainerIds) {
      const { error } = await adminApi.unblockContainer(containerId);
      if (error) {
        failed++;
      } else {
        success++;
      }
    }

    toast.success(`${success} Container entsperrt`, {
      id: "bulk-unblock-containers",
      description: failed > 0 ? `${failed} fehlgeschlagen` : undefined,
    });

    fetchUsers();
    setSelectedContainerIds(new Set());
  };

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  // Gefilterte Users
  const filteredUsers = users.filter(
    (u) =>
      u.slug.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase())
  ).sort((a, b) => (b.created_at ? new Date(b.created_at).getTime() : 0) - (a.created_at ? new Date(a.created_at).getTime() : 0));

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
                  {user?.email.slice(0, 1).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium">{user?.email}</span>
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
          <h1 className="text-3xl font-bold">
            {activeTab === "users" ? "Benutzerverwaltung" : "Container-Verwaltung"}
          </h1>
          <p className="text-muted-foreground">
            {activeTab === "users" ? "Verwalte alle registrierten Benutzer" : "Verwalte alle Benutzer-Container"}
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6 flex gap-2 border-b">
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === "users"
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => {
              setActiveTab("users");
              setSelectedContainerIds(new Set());
            }}
          >
            <Users className="mr-2 inline-block h-4 w-4" />
            User-Verwaltung
          </button>
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === "containers"
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => {
              setActiveTab("containers");
              setSelectedUserIds(new Set());
            }}
          >
            <Container className="mr-2 inline-block h-4 w-4" />
            Container-Verwaltung
          </button>
        </div>

        {/* Fehler-Alert (Fallback, Toasts sind Primary) */}
        {error && (
          <div className="mb-6 rounded-md bg-destructive/10 p-4 text-sm text-destructive flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={() => setError("")}
              className="ml-2 underline text-xs"
            >
              Schliessen
            </button>
          </div>
        )}

        {activeTab === "users" && (
          <>
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

        {/* Bulk-Action Bar */}
        {selectedUserIds.size > 0 && (
          <div className="mb-4 rounded-lg border border-primary bg-primary/5 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="font-medium">
                  {selectedUserIds.size} User ausgewählt
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={deselectAll}
                  className="text-xs"
                >
                  Auswahl aufheben
                </Button>
              </div>

              <div className="flex items-center gap-2">
                {/* Bulk-Block */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBulkBlock}
                  disabled={actionLoading !== null}
                >
                  <ShieldOff className="mr-2 h-4 w-4" />
                  Sperren
                </Button>

                {/* Bulk-Unblock */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBulkUnblock}
                  disabled={actionLoading !== null}
                >
                  <Shield className="mr-2 h-4 w-4" />
                  Entsperren
                </Button>

                {/* Bulk-Delete-Container */}
                {selectedContainerIds.size > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={openBulkDeleteDialog}
                    disabled={actionLoading !== null}
                  >
                    <Container className="mr-2 h-4 w-4" />
                    Container löschen ({selectedContainerIds.size})
                  </Button>
                )}

                {/* Bulk-Delete User */}
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleBulkDeleteUsers}
                  disabled={actionLoading !== null}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  User löschen
                </Button>
              </div>
            </div>
          </div>
        )}

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

        {/* Select-All Checkbox */}
        {filteredUsers.length > 0 && (
          <div className="mb-4 flex items-center gap-2">
            <input
              type="checkbox"
              checked={
                selectedUserIds.size > 0 &&
                selectedUserIds.size ===
                  filteredUsers.filter(u => u.id !== user?.id && !u.is_admin).length
              }
              onChange={(e) => {
                if (e.target.checked) {
                  selectAllFiltered();
                } else {
                  deselectAll();
                }
              }}
              className="h-4 w-4 rounded border-gray-300"
            />
            <span className="text-sm text-muted-foreground">
              Alle{" "}
              {filteredUsers.filter((u) => u.id !== user?.id && !u.is_admin).length}{" "}
              User auswählen
            </span>
          </div>
        )}

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
                const isSelectable = !isCurrentUser && !u.is_admin;
                const isSelected = selectedUserIds.has(u.id);

                return (
                  <div
                    key={u.id}
                    className="border rounded-lg overflow-hidden"
                  >
                    {/* Main User Row */}
                    <div
                      className={`flex items-center justify-between p-4 ${
                        u.is_blocked ? "bg-red-50 border-b border-red-200" : "border-b"
                      } ${isSelected ? "bg-primary/5" : ""}`}
                    >
                    {/* Checkbox + User Info */}
                    <div className="flex items-center gap-4">
                      {/* Expand Icon */}
                      {u.containers && u.containers.length > 0 && (
                        <button
                          onClick={() => toggleUserExpand(u.id)}
                          className="p-0 h-4 w-4 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
                          title={expandedUserIds.has(u.id) ? "Container ausblenden" : "Container anzeigen"}
                        >
                          <ChevronDown
                            className={`h-4 w-4 transition-transform ${
                              expandedUserIds.has(u.id) ? "rotate-180" : ""
                            }`}
                          />
                        </button>
                      )}

                      {isSelectable && (
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleUserSelection(u.id)}
                          className="h-4 w-4 rounded border-gray-300"
                        />
                      )}
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
                          {u.email.slice(0, 1).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{u.email}</span>
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
                              onClick={() => handleDeleteUser(u.id, u.email)}
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

                    {/* Expandable Container List */}
                    {expandedUserIds.has(u.id) && u.containers && u.containers.length > 0 && (
                      <div className="border-t bg-muted/30 p-4">
                        <div className="space-y-2">
                          {u.containers.map(container => (
                            <div
                              key={container.id}
                              className="flex items-center gap-3 p-3 rounded border bg-background hover:bg-accent/50 transition-colors"
                            >
                              {/* Checkbox für Container */}
                              <input
                                type="checkbox"
                                checked={selectedContainerIds.has(container.id)}
                                onChange={() => toggleContainerSelection(container.id)}
                                className="h-4 w-4 rounded border-gray-300"
                              />

                              {/* Container Icon + Info */}
                              <Container className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-sm">{container.container_type}</span>
                                  {container.is_blocked && (
                                    <Badge variant="destructive" className="text-xs">
                                      Gesperrt
                                    </Badge>
                                  )}
                                </div>
                                <span className="text-xs text-muted-foreground">
                                  {container.container_id ? "Running" : "Stopped"} • {formatDate(container.created_at)}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
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
          </>
        )}

        {activeTab === "containers" && (
          <>
            {/* Container Bulk-Action Bar */}
            {selectedContainerIds.size > 0 && (
              <div className="mb-4 rounded-lg border border-primary bg-primary/5 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className="font-medium">
                      {selectedContainerIds.size} Container ausgewählt
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedContainerIds(new Set())}
                      className="text-xs"
                    >
                      Auswahl aufheben
                    </Button>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleBulkBlockContainers}
                      disabled={actionLoading !== null}
                    >
                      <ShieldOff className="mr-2 h-4 w-4" />
                      Sperren
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleBulkUnblockContainers}
                      disabled={actionLoading !== null}
                    >
                      <Shield className="mr-2 h-4 w-4" />
                      Entsperren
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Suche */}
            <div className="mb-6 flex items-center gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Container oder User suchen..."
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

            {/* Container Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {users.flatMap(u =>
                (u.containers || []).map(container => (
                  u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                  container.container_type.toLowerCase().includes(searchTerm.toLowerCase())
                ) ? (
                  <Card
                    key={container.id}
                    className={`relative overflow-hidden transition-all ${
                      container.is_blocked
                        ? "border-red-500 bg-red-50"
                        : ""
                    } ${
                      selectedContainerIds.has(container.id)
                        ? "border-primary bg-primary/5"
                        : ""
                    }`}
                  >
                    {/* Checkbox */}
                    <div className="absolute top-2 left-2">
                      <input
                        type="checkbox"
                        checked={selectedContainerIds.has(container.id)}
                        onChange={() => toggleContainerSelection(container.id)}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                    </div>

                    {/* Blocked Badge */}
                    {container.is_blocked && (
                      <div className="absolute top-2 right-2">
                        <Badge variant="destructive" className="text-xs">
                          Gesperrt
                        </Badge>
                      </div>
                    )}

                    <CardHeader className="pt-10">
                      <CardTitle className="text-lg">{container.container_type}</CardTitle>
                      <CardDescription className="text-sm">
                        User: {u.email}
                      </CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-3">
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Status:</span>
                          <span className="font-medium">
                            {container.container_id ? "Running" : "Stopped"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">erstellt:</span>
                          <span className="font-mono text-xs">
                            {container.created_at
                              ? new Date(container.created_at).toLocaleDateString("de-DE")
                              : "-"}
                          </span>
                        </div>
                        {container.is_blocked && container.blocked_at && (
                          <div className="flex justify-between text-destructive">
                            <span className="text-muted-foreground">Gesperrt:</span>
                            <span className="font-mono text-xs">
                              {new Date(container.blocked_at).toLocaleString("de-DE")}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-2 pt-2">
                        {container.is_blocked ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              handleUnblockContainer(container.id, container.container_type)
                            }
                            disabled={actionLoading === container.id}
                            className="flex-1 text-xs"
                          >
                            {actionLoading === container.id ? (
                              <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                            ) : (
                              <Shield className="mr-2 h-3 w-3" />
                            )}
                            Entsperren
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() =>
                              handleBlockContainer(container.id, container.container_type)
                            }
                            disabled={actionLoading === container.id}
                            className="flex-1 text-xs"
                          >
                            {actionLoading === container.id ? (
                              <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                            ) : (
                              <ShieldOff className="mr-2 h-3 w-3" />
                            )}
                            Sperren
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ) : null
              ))}
            </div>

            {users.flatMap(u => (u.containers || []).length).reduce((a, b) => a + b, 0) === 0 && (
              <div className="py-12 text-center text-muted-foreground">
                Keine Container gefunden
              </div>
            )}
          </>
        )}
      </main>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Container wirklich löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteDialogData && (
                <>
                  <p className="mb-3">
                    Du bist dabei, <strong>{deleteDialogData.containerIds.length} Container</strong> von{" "}
                    <strong>{deleteDialogData.userSummary.length} Benutzer(n)</strong> zu löschen.
                  </p>
                  <div className="mt-3 space-y-1 text-sm bg-muted/50 p-3 rounded">
                    <p className="font-semibold text-foreground">Betroffene Benutzer:</p>
                    <ul className="space-y-1 ml-2">
                      {deleteDialogData.userSummary.map((user, idx) => (
                        <li key={idx} className="text-sm">
                          • <span className="font-medium">{user.email}</span> ({user.count} Container)
                        </li>
                      ))}
                    </ul>
                  </div>
                  <p className="mt-4 text-xs text-muted-foreground">
                    Die Benutzer können danach neue Container erstellen.
                  </p>
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmBulkDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Jetzt löschen
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
