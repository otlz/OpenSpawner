"use client";

/**
 * Admin-Seite: Benutzer- und Container-Verwaltung.
 * Aufgeteilt in Sub-Komponenten (StatsCards, ContainerTab, DeleteDialog).
 */

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/hooks/use-auth";
import { adminApi, AdminUser, UserRole } from "@/lib/api";
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
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Search,
  Monitor,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

import { Skeleton } from "@/components/ui/skeleton";
import StatsCards from "./components/stats-cards";
import ContainerTab from "./components/container-tab";
import DeleteDialog from "./components/delete-dialog";
import EmailRulesTab from "./components/email-rules-tab";
import {
  getStatusColor,
  getStatusBadgeColor,
  getStateLabel,
  formatDate,
  getRoleLabel,
  getRoleBadgeColor,
} from "./components/admin-utils";

export default function AdminPage() {
  const { user } = useAuth();

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedUserIds, setSelectedUserIds] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<"users" | "containers" | "email-rules">("users");
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
    if (data) setUsers(data.users);
    else if (error) setError(error);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // ============================================================
  // Auswahl-Verwaltung
  // ============================================================

  const toggleUserExpand = (userId: number) => {
    const next = new Set(expandedUserIds);
    next.has(userId) ? next.delete(userId) : next.add(userId);
    setExpandedUserIds(next);
  };

  const toggleUserSelection = (userId: number) => {
    const next = new Set(selectedUserIds);
    next.has(userId) ? next.delete(userId) : next.add(userId);
    setSelectedUserIds(next);
  };

  const toggleContainerSelection = (containerId: number) => {
    const next = new Set(selectedContainerIds);
    next.has(containerId) ? next.delete(containerId) : next.add(containerId);
    setSelectedContainerIds(next);
  };

  const selectAllFiltered = () => {
    const ids = filteredUsers
      .filter((u) => u.id !== user?.id && u.role !== 'admin')
      .map((u) => u.id);
    setSelectedUserIds(new Set(ids));
  };

  const deselectAll = () => setSelectedUserIds(new Set());

  // ============================================================
  // Einzelaktionen
  // ============================================================

  const handleBlock = async (userId: number) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.blockUser(userId);
    error ? toast.error(`Fehler: ${error}`) : toast.success(data?.message || "User gesperrt");
    if (!error) fetchUsers();
    setActionLoading(null);
  };

  const handleUnblock = async (userId: number) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.unblockUser(userId);
    error ? toast.error(`Fehler: ${error}`) : toast.success(data?.message || "User entsperrt");
    if (!error) fetchUsers();
    setActionLoading(null);
  };

  const handleResendVerification = async (userId: number) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.resendVerification(userId);
    error ? toast.error(`Fehler: ${error}`) : toast.success(data?.message || "Verifizierungs-Email gesendet");
    setActionLoading(null);
  };

  const handleDeleteUser = async (userId: number, userEmail: string) => {
    if (!confirm(
      `ACHTUNG: User "${userEmail}" VOLLSTÄNDIG löschen?\n\n` +
      `Dies löscht:\n` +
      `- User-Account und alle Daten\n` +
      `- Alle Docker-Container\n` +
      `- Alle Magic Link Tokens\n` +
      `- Alle Takeover-Sessions\n\n` +
      `Diese Aktion kann NICHT rückgängig gemacht werden!`
    )) return;

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

  const handleChangeRole = async (userId: number, newRole: UserRole) => {
    setActionLoading(userId);
    const { data, error } = await adminApi.changeRole(userId, newRole);
    error ? toast.error(`Fehler: ${error}`) : toast.success(data?.message || "Rolle geändert");
    if (!error) fetchUsers();
    setActionLoading(null);
  };

  const handleTakeover = async (userId: number) => {
    const reason = prompt("Grund für den Zugriff (optional):");
    if (reason === null) return;

    setActionLoading(userId);
    const { data, error } = await adminApi.startTakeover(userId, reason);
    error ? toast.error(`Fehler: ${error}`) : toast.info(data?.note || "Takeover gestartet (Dummy)", { duration: 4000 });
    setActionLoading(null);
  };

  // ============================================================
  // Container-Aktionen
  // ============================================================

  const handleBlockContainer = async (containerId: number, containerType: string) => {
    if (!confirm(`Container "${containerType}" sperren?\n\nDer Container wird gestoppt und kann vom User nicht neu gestartet werden.`)) return;

    setActionLoading(containerId);
    const { error } = await adminApi.blockContainer(containerId);
    error ? toast.error(`Fehler: ${error}`) : toast.success(`Container ${containerType} gesperrt`);
    if (!error) fetchUsers();
    setActionLoading(null);
  };

  const handleUnblockContainer = async (containerId: number, containerType: string) => {
    setActionLoading(containerId);
    const { error } = await adminApi.unblockContainer(containerId);
    error
      ? toast.error(`Fehler: ${error}`)
      : toast.success(`Container ${containerType} entsperrt`, { description: "User kann Container jetzt manuell starten" });
    if (!error) fetchUsers();
    setActionLoading(null);
  };

  // ============================================================
  // Massenaktionen
  // ============================================================

  /** Führt eine Massenaktion auf ausgewählte User aus. */
  const runBulkUserAction = async (
    action: (userId: number) => Promise<{ error?: string | null }>,
    label: string,
    toastId: string
  ) => {
    if (!confirm(`${selectedUserIds.size} User ${label}?`)) return;

    toast.loading(`${label}: ${selectedUserIds.size} User...`, { id: toastId });
    let success = 0, failed = 0;

    for (const userId of Array.from(selectedUserIds)) {
      const { error } = await action(userId);
      error ? failed++ : success++;
    }

    toast.success(`${success} User ${label.toLowerCase()}`, {
      id: toastId,
      description: failed > 0 ? `${failed} fehlgeschlagen` : undefined,
    });
    fetchUsers();
    deselectAll();
  };

  const handleBulkBlock = () =>
    runBulkUserAction((id) => adminApi.blockUser(id), "sperren", "bulk-block");

  const handleBulkUnblock = () =>
    runBulkUserAction((id) => adminApi.unblockUser(id), "entsperren", "bulk-unblock");

  const handleBulkDeleteUsers = async () => {
    const selectedUsers = Array.from(selectedUserIds)
      .map((id) => users.find((u) => u.id === id))
      .filter(Boolean) as AdminUser[];

    const userList = selectedUsers.map((u) => u.email).join("\n");

    if (!confirm(
      `WARNUNG: ${selectedUserIds.size} User VOLLSTÄNDIG löschen?\n\n` +
      `Betroffene User:\n${userList}\n\n` +
      `Klicken Sie OK für finalen Bestätigungsschritt.`
    )) return;

    const confirmation = prompt(
      `FINALE BESTAETIGUNG:\nGeben Sie die Anzahl der zu loeschenden User ein (${selectedUserIds.size}):`
    );
    if (confirmation !== String(selectedUserIds.size)) {
      toast.error("Bulk-Delete abgebrochen (falsche Bestätigung)");
      return;
    }

    toast.loading(`Lösche ${selectedUserIds.size} User...`, { id: "bulk-delete-users" });
    let success = 0, failed = 0;

    for (const userId of Array.from(selectedUserIds)) {
      const { error } = await adminApi.deleteUser(userId);
      error ? failed++ : success++;
    }

    toast.success(`${success} User gelöscht`, {
      id: "bulk-delete-users",
      description: failed > 0 ? `${failed} fehlgeschlagen` : "Alle Daten vollständig entfernt",
      duration: 8000,
    });
    fetchUsers();
    deselectAll();
  };

  const handleBulkBlockContainers = async () => {
    if (!confirm(`${selectedContainerIds.size} Container sperren?`)) return;

    toast.loading(`Sperre ${selectedContainerIds.size} Container...`, { id: "bulk-block-containers" });
    let success = 0, failed = 0;

    for (const containerId of Array.from(selectedContainerIds)) {
      const { error } = await adminApi.blockContainer(containerId);
      error ? failed++ : success++;
    }

    toast.success(`${success} Container gesperrt`, {
      id: "bulk-block-containers",
      description: failed > 0 ? `${failed} fehlgeschlagen` : undefined,
    });
    fetchUsers();
    setSelectedContainerIds(new Set());
  };

  const handleBulkUnblockContainers = async () => {
    if (!confirm(`${selectedContainerIds.size} Container entsperren?`)) return;

    toast.loading(`Entsperre ${selectedContainerIds.size} Container...`, { id: "bulk-unblock-containers" });
    let success = 0, failed = 0;

    for (const containerId of Array.from(selectedContainerIds)) {
      const { error } = await adminApi.unblockContainer(containerId);
      error ? failed++ : success++;
    }

    toast.success(`${success} Container entsperrt`, {
      id: "bulk-unblock-containers",
      description: failed > 0 ? `${failed} fehlgeschlagen` : undefined,
    });
    fetchUsers();
    setSelectedContainerIds(new Set());
  };

  // Bulk-Delete Container Dialog
  const openBulkDeleteDialog = () => {
    if (selectedContainerIds.size === 0) {
      toast.error("Keine Container ausgewählt");
      return;
    }

    const userMap = new Map<number, { email: string; count: number }>();
    for (const containerId of Array.from(selectedContainerIds)) {
      const u = users.find((u) => u.containers?.some((c) => c.id === containerId));
      if (u) {
        const existing = userMap.get(u.id) || { email: u.email, count: 0 };
        existing.count++;
        userMap.set(u.id, existing);
      }
    }

    setDeleteDialogData({
      containerIds: Array.from(selectedContainerIds),
      userSummary: Array.from(userMap.values()),
    });
    setIsDeleteDialogOpen(true);
  };

  const handleConfirmBulkDelete = async () => {
    if (!deleteDialogData) return;
    setIsDeleteDialogOpen(false);

    toast.loading(`Lösche ${deleteDialogData.containerIds.length} Container...`, { id: "bulk-delete-containers" });

    // Container nach User-ID gruppieren
    const containersByUser = new Map<number, number[]>();
    for (const containerId of deleteDialogData.containerIds) {
      const u = users.find((u) => u.containers?.some((c) => c.id === containerId));
      if (u) {
        if (!containersByUser.has(u.id)) containersByUser.set(u.id, []);
        containersByUser.get(u.id)!.push(containerId);
      }
    }

    let totalDeleted = 0, totalFailed = 0;
    for (const [userId, containerIds] of containersByUser) {
      const { data, error } = await adminApi.deleteUserContainer(userId, containerIds);
      if (error) totalFailed += containerIds.length;
      else if (data) {
        totalDeleted += data.deleted || 0;
        totalFailed += data.failed?.length || 0;
      }
    }

    toast.success(`${totalDeleted} Container gelöscht`, {
      id: "bulk-delete-containers",
      description: totalFailed > 0 ? `${totalFailed} fehlgeschlagen` : undefined,
    });
    await fetchUsers();
    setSelectedContainerIds(new Set());
    setDeleteDialogData(null);
  };

  // ============================================================
  // Gefilterte Daten und Statistiken
  // ============================================================

  const filteredUsers = users
    .filter(
      (u) =>
        u.slug.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.email.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) =>
      (b.created_at ? new Date(b.created_at).getTime() : 0) -
      (a.created_at ? new Date(a.created_at).getTime() : 0)
    );

  const stats = {
    total: users.length,
    active: users.filter((u) => u.state === "active").length,
    verified: users.filter((u) => u.state === "verified").length,
    unverified: users.filter((u) => u.state === "registered").length,
    blocked: users.filter((u) => u.is_blocked).length,
  };

  // ============================================================
  // Render
  // ============================================================

  if (isLoading) {
    return (
      <>
        <div className="mb-6">
          <Skeleton className="h-8 w-44 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-10 w-[28rem] rounded-lg mb-6" />
        <div className="mb-6 grid gap-4 md:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="flex items-center gap-3 p-4">
                <Skeleton className="h-8 w-8 rounded" />
                <div>
                  <Skeleton className="h-7 w-10 mb-1" />
                  <Skeleton className="h-3 w-16" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="mb-6 flex items-center gap-4">
          <Skeleton className="h-10 flex-1 max-w-md rounded-md" />
          <Skeleton className="h-10 w-36 rounded-md" />
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-24 mb-1" />
            <Skeleton className="h-4 w-44" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Skeleton className="h-10 w-10 rounded-full" />
                      <div>
                        <Skeleton className="h-4 w-48 mb-2" />
                        <Skeleton className="h-3 w-64" />
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Skeleton className="h-8 w-8 rounded" />
                      <Skeleton className="h-8 w-8 rounded" />
                      <Skeleton className="h-8 w-8 rounded" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </>
    );
  }

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Administration</h2>
        <p className="text-muted-foreground">
          Benutzer- und Container-Verwaltung
        </p>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={(value) => {
          const tab = value as "users" | "containers" | "email-rules";
          setActiveTab(tab);
          if (tab === "users") {
            setSelectedContainerIds(new Set());
          } else {
            setSelectedUserIds(new Set());
          }
        }}
      >
        <TabsList className="mb-6 grid w-fit grid-cols-3">
          <TabsTrigger value="users">
            <Users className="mr-1.5 h-3.5 w-3.5" />
            User-Verwaltung
          </TabsTrigger>
          <TabsTrigger value="containers">
            <Container className="mr-1.5 h-3.5 w-3.5" />
            Container-Verwaltung
          </TabsTrigger>
          {user?.role === 'admin' && (
            <TabsTrigger value="email-rules">
              <Mail className="mr-1.5 h-3.5 w-3.5" />
              E-Mail-Regeln
            </TabsTrigger>
          )}
        </TabsList>

        {/* Fehler-Anzeige */}
        {error && (
          <div className="mb-6 rounded-md bg-destructive/10 p-4 text-sm text-destructive flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError("")} className="ml-2 underline text-xs">Schließen</button>
          </div>
        )}

        {/* User-Tab */}
        <TabsContent value="users">
          <StatsCards stats={stats} />

          {/* Bulk-Action Bar */}
          {selectedUserIds.size > 0 && (
            <div className="mb-4 rounded-lg border border-primary bg-primary/5 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="font-medium">{selectedUserIds.size} User ausgewählt</span>
                  <Button variant="outline" size="sm" onClick={deselectAll} className="text-xs">Auswahl aufheben</Button>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={handleBulkBlock} disabled={actionLoading !== null}>
                    <ShieldOff className="mr-2 h-4 w-4" />Sperren
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleBulkUnblock} disabled={actionLoading !== null}>
                    <Shield className="mr-2 h-4 w-4" />Entsperren
                  </Button>
                  {selectedContainerIds.size > 0 && (
                    <Button variant="outline" size="sm" onClick={openBulkDeleteDialog} disabled={actionLoading !== null}>
                      <Container className="mr-2 h-4 w-4" />Container löschen ({selectedContainerIds.size})
                    </Button>
                  )}
                  <Button variant="destructive" size="sm" onClick={handleBulkDeleteUsers} disabled={actionLoading !== null}>
                    <Trash2 className="mr-2 h-4 w-4" />User löschen
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Suche */}
          <div className="mb-6 flex items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Benutzer suchen..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" />
            </div>
            <Button variant="outline" onClick={fetchUsers}>
              <RefreshCw className="mr-2 h-4 w-4" />Aktualisieren
            </Button>
          </div>

          {/* Alle auswählen */}
          {filteredUsers.length > 0 && (
            <div className="mb-4 flex items-center gap-2">
              <input
                type="checkbox"
                checked={selectedUserIds.size > 0 && selectedUserIds.size === filteredUsers.filter((u) => u.id !== user?.id && u.role !== 'admin').length}
                onChange={(e) => e.target.checked ? selectAllFiltered() : deselectAll()}
                className="h-4 w-4 rounded border-gray-300"
              />
              <span className="text-sm text-muted-foreground">
                Alle {filteredUsers.filter((u) => u.id !== user?.id && u.role !== 'admin').length} User auswählen
              </span>
            </div>
          )}

          {/* Benutzerliste */}
          <Card>
            <CardHeader>
              <CardTitle>Benutzer</CardTitle>
              <CardDescription>{filteredUsers.length} von {users.length} Benutzern</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredUsers.map((u) => {
                  const statusColor = getStatusColor(u);
                  const isCurrentUser = u.id === user?.id;
                  const isSelectable = !isCurrentUser && u.role !== 'admin';
                  const isSelected = selectedUserIds.has(u.id);

                  return (
                    <div key={u.id} className="border rounded-lg overflow-hidden">
                      {/* User-Zeile */}
                      <div className={`flex items-center justify-between p-4 ${u.is_blocked ? "bg-red-50 border-b border-red-200" : "border-b"} ${isSelected ? "bg-primary/5" : ""}`}>
                        <div className="flex items-center gap-4">
                          {/* Aufklapp-Button */}
                          {u.containers && u.containers.length > 0 && (
                            <button onClick={() => toggleUserExpand(u.id)} className="p-0 h-4 w-4 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors" title={expandedUserIds.has(u.id) ? "Container ausblenden" : "Container anzeigen"}>
                              <ChevronDown className={`h-4 w-4 transition-transform ${expandedUserIds.has(u.id) ? "rotate-180" : ""}`} />
                            </button>
                          )}

                          {isSelectable && (
                            <input type="checkbox" checked={isSelected} onChange={() => toggleUserSelection(u.id)} className="h-4 w-4 rounded border-gray-300" />
                          )}

                          <Avatar>
                            <AvatarFallback className={u.is_blocked ? "bg-red-200 text-red-800" : u.role === 'admin' ? "bg-primary text-primary-foreground" : u.role === 'manager' ? "bg-blue-200 text-blue-800" : ""}>
                              {u.email.slice(0, 1).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>

                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{u.email}</span>
                              {u.role !== 'user' && (
                                <Badge variant="secondary" className={`text-xs ${getRoleBadgeColor(u.role)}`}>
                                  {getRoleLabel(u.role)}
                                </Badge>
                              )}
                              {u.is_blocked && <Badge variant="destructive" className="text-xs">Gesperrt</Badge>}
                              {/* Role Dropdown — nur für Admins sichtbar, nicht für sich selbst */}
                              {user?.role === 'admin' && !isCurrentUser && (
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="sm" className="h-6 px-2 text-xs text-muted-foreground">
                                      <ChevronRight className="h-3 w-3" />
                                    </Button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="start">
                                    {(['admin', 'manager', 'user'] as UserRole[]).map((role) => (
                                      <DropdownMenuItem
                                        key={role}
                                        onClick={() => handleChangeRole(u.id, role)}
                                        disabled={u.role === role}
                                        className={u.role === role ? "font-bold" : ""}
                                      >
                                        {getRoleLabel(role)}
                                      </DropdownMenuItem>
                                    ))}
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">{u.email}</p>
                            <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                              <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 ${getStatusBadgeColor(statusColor)}`}>
                                {statusColor === "green" && <CheckCircle2 className="h-3 w-3" />}
                                {statusColor === "yellow" && <AlertCircle className="h-3 w-3" />}
                                {statusColor === "red" && <XCircle className="h-3 w-3" />}
                                {getStateLabel(u.state)}
                              </span>
                              <span>|</span>
                              <span>Letzte Aktivität: {formatDate(u.last_used)}</span>
                              {u.container_id && (
                                <>
                                  <span>|</span>
                                  <span className="flex items-center gap-1">
                                    <Container className="h-3 w-3" />{u.container_id.slice(0, 8)}
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
                              {u.state === "registered" && (
                                <Button variant="ghost" size="sm" onClick={() => handleResendVerification(u.id)} title="Verifizierungs-Email erneut senden">
                                  <Mail className="h-4 w-4" />
                                </Button>
                              )}
                              <Button variant="ghost" size="sm" onClick={() => handleResendVerification(u.id)} title="Login-Link erneut senden">
                                <Mail className="h-4 w-4" />
                              </Button>
                              {u.container_id && !isCurrentUser && (
                                <Button variant="ghost" size="sm" onClick={() => handleTakeover(u.id)} title="Container-Zugriff (Phase 2)" disabled>
                                  <Monitor className="h-4 w-4" />
                                </Button>
                              )}
                              {!isCurrentUser && u.role !== 'admin' && (
                                u.is_blocked ? (
                                  <Button variant="ghost" size="sm" onClick={() => handleUnblock(u.id)} title="Entsperren">
                                    <Shield className="h-4 w-4 text-green-600" />
                                  </Button>
                                ) : (
                                  <Button variant="ghost" size="sm" onClick={() => handleBlock(u.id)} title="Sperren">
                                    <ShieldOff className="h-4 w-4 text-red-600" />
                                  </Button>
                                )
                              )}
                              {!isCurrentUser && u.role !== 'admin' && (
                                <Button variant="ghost" size="sm" onClick={() => handleDeleteUser(u.id, u.email)} title="Benutzer löschen" className="text-red-600 hover:text-red-700">
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </div>

                      {/* Aufklappbare Container-Liste */}
                      {expandedUserIds.has(u.id) && u.containers && u.containers.length > 0 && (
                        <div className="border-t bg-muted/30 p-4">
                          <div className="space-y-2">
                            {u.containers.map((container) => (
                              <div key={container.id} className="flex items-center gap-3 p-3 rounded border bg-background hover:bg-accent/50 transition-colors">
                                <input type="checkbox" checked={selectedContainerIds.has(container.id)} onChange={() => toggleContainerSelection(container.id)} className="h-4 w-4 rounded border-gray-300" />
                                <Container className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium text-sm">{container.container_type}</span>
                                    {container.is_blocked && <Badge variant="destructive" className="text-xs">Gesperrt</Badge>}
                                  </div>
                                  <span className="text-xs text-muted-foreground">
                                    {container.container_id ? "Läuft" : "Gestoppt"} - {formatDate(container.created_at)}
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
                  <div className="py-8 text-center text-muted-foreground">Keine Benutzer gefunden</div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Container-Tab */}
        <TabsContent value="containers">
          <ContainerTab
            users={users}
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            selectedContainerIds={selectedContainerIds}
            onToggleSelection={toggleContainerSelection}
            onClearSelection={() => setSelectedContainerIds(new Set())}
            actionLoading={actionLoading}
            onBlockContainer={handleBlockContainer}
            onUnblockContainer={handleUnblockContainer}
            onBulkBlock={handleBulkBlockContainers}
            onBulkUnblock={handleBulkUnblockContainers}
            onRefresh={fetchUsers}
          />
        </TabsContent>

        {/* E-Mail-Regeln-Tab */}
        {user?.role === 'admin' && (
          <TabsContent value="email-rules">
            <EmailRulesTab />
          </TabsContent>
        )}
      </Tabs>

      {/* Lösch-Dialog */}
      <DeleteDialog
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
        data={deleteDialogData}
        onConfirm={handleConfirmBulkDelete}
      />
    </>
  );
}
