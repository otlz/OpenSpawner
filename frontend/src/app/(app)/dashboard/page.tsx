"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { useHeartbeat } from "@/hooks/use-heartbeat";
import { api, type Container, type Category } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
import {
  ExternalLink,
  Loader2,
  Play,
  CheckCircle,
  AlertCircle,
  ShieldAlert,
  RefreshCw,
  Square,
  Trash2,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { getContainerIcon } from "@/lib/container-icons";

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout, isLoading: authLoading } = useAuth();
  const [containers, setContainers] = useState<Container[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState<string | null>(null);
  const [stopping, setStopping] = useState<string | null>(null);
  const [restarting, setRestarting] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [error, setError] = useState("");

  // Send heartbeats for all running containers
  const runningTypes = useMemo(
    () => containers.filter((c) => c.status === "running").map((c) => c.type),
    [containers]
  );
  useHeartbeat(runningTypes);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
      return;
    }

    if (user) {
      loadContainers();
    }
  }, [user, authLoading, router]);

  const loadContainers = async () => {
    try {
      setError("");
      const { data, error: apiError } = await api.getUserContainers();
      if (data) {
        setContainers(data.containers);
        setCategories(data.categories || []);
      } else if (apiError) {
        setError(apiError);
      }
    } catch (err) {
      setError("Fehler beim Laden der Container");
    } finally {
      setLoading(false);
    }
  };

  const isActionInProgress = (type: string) =>
    launching === type || stopping === type || restarting === type || deleting === type;

  const handleLaunchContainer = async (containerType: string) => {
    setLaunching(containerType);
    setError("");
    try {
      const { data, error: apiError } = await api.launchContainer(containerType);
      if (data) {
        window.open(data.service_url, "_blank");
        await loadContainers();
      } else if (apiError) {
        if (apiError.includes("blocked")) {
          toast.error("Dieser Container wurde von einem Administrator gesperrt", {
            description: "Kontaktiere einen Administrator für mehr Informationen",
          });
        } else {
          setError(apiError);
        }
      }
    } catch (err) {
      setError("Fehler beim Starten des Containers");
    } finally {
      setLaunching(null);
    }
  };

  const handleStopContainer = async (containerType: string) => {
    setStopping(containerType);
    try {
      const { data, error: apiError } = await api.stopContainer(containerType);
      if (data) {
        toast.success("Container gestoppt");
        await loadContainers();
      } else if (apiError) {
        toast.error(apiError);
      }
    } catch (err) {
      toast.error("Fehler beim Stoppen des Containers");
    } finally {
      setStopping(null);
    }
  };

  const handleRestartContainer = async (containerType: string) => {
    setRestarting(containerType);
    try {
      const { data, error: apiError } = await api.restartContainerByType(containerType);
      if (data) {
        toast.success("Container neugestartet");
        await loadContainers();
      } else if (apiError) {
        toast.error(apiError);
      }
    } catch (err) {
      toast.error("Fehler beim Neustarten des Containers");
    } finally {
      setRestarting(null);
    }
  };

  const handleDeleteContainer = async (containerType: string) => {
    setDeleting(containerType);
    try {
      const { data, error: apiError } = await api.deleteContainer(containerType);
      if (data) {
        toast.success("Container gelöscht");
        await loadContainers();
      } else if (apiError) {
        toast.error(apiError);
      }
    } catch (err) {
      toast.error("Fehler beim Löschen des Containers");
    } finally {
      setDeleting(null);
      setDeleteTarget(null);
    }
  };

  const getStatusBadge = (status: string, isBlocked: boolean) => {
    if (isBlocked) {
      return (
        <Badge variant="destructive" className="text-xs">
          <ShieldAlert className="mr-1 h-3 w-3" />
          Gesperrt
        </Badge>
      );
    }
    switch (status) {
      case "running":
        return (
          <Badge className="bg-green-100 text-green-700 hover:bg-green-100 text-xs">
            <CheckCircle className="mr-1 h-3 w-3" />
            Läuft
          </Badge>
        );
      case "stopped":
        return (
          <Badge className="bg-yellow-100 text-yellow-700 hover:bg-yellow-100 text-xs">
            <AlertCircle className="mr-1 h-3 w-3" />
            Gestoppt
          </Badge>
        );
      case "error":
        return (
          <Badge variant="destructive" className="text-xs">
            <AlertCircle className="mr-1 h-3 w-3" />
            Fehler
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" className="text-xs">
            Nicht erstellt
          </Badge>
        );
    }
  };

  if (authLoading || !user) {
    return (
      <>
        <div className="mb-6">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-80" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="p-4 pb-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-5 w-5 shrink-0 rounded" />
                    <Skeleton className="h-5 w-28" />
                  </div>
                  <Skeleton className="h-5 w-16 rounded-full" />
                </div>
                <Skeleton className="h-3 w-full mt-2" />
              </CardHeader>
              <CardContent className="p-4 pt-2">
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                    <Skeleton className="h-3 w-20" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                  <Skeleton className="h-3 w-36" />
                  <div className="flex gap-1.5 pt-1">
                    <Skeleton className="h-7 w-20 rounded" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </>
    );
  }

  const skeletonGrid = (
    <div className="mb-8">
      <Skeleton className="h-6 w-36 mb-4" />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="p-4 pb-2">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-5 w-5 shrink-0 rounded" />
                  <Skeleton className="h-5 w-28" />
                </div>
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
              <Skeleton className="h-3 w-full mt-2" />
            </CardHeader>
            <CardContent className="p-4 pt-2">
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="h-3 w-24" />
                </div>
                <Skeleton className="h-3 w-36" />
                <div className="flex gap-1.5 pt-1">
                  <Skeleton className="h-7 w-20 rounded" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  return (
    <>
      {error && (
        <div className="mb-6 rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading ? (
        <>
          {skeletonGrid}
          {skeletonGrid}
        </>
      ) : (
        <>
          {[...categories].sort((a, b) => a.order - b.order).map((category) => {
            const categoryContainers = containers.filter(
              (c) => c.category === category.id
            );
            if (categoryContainers.length === 0) return null;
            return (
              <div key={category.id} className="mb-8">
                <h2 className="text-xl font-semibold mb-4">{category.display_name}</h2>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {categoryContainers.map((container) => {
            const isBlocked = container.is_blocked === true;
            const busy = isActionInProgress(container.type);

            return (
              <Card
                key={container.type}
                className={`relative transition-all flex flex-col ${
                  isBlocked ? "border-red-500 bg-red-50" : ""
                }`}
              >
                <CardHeader className="p-4 pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="shrink-0 text-muted-foreground">
                        {getContainerIcon(container.icon, "h-5 w-5")}
                      </div>
                      <CardTitle className="text-base font-semibold truncate">
                        {container.display_name}
                      </CardTitle>
                    </div>
                    {getStatusBadge(container.status, isBlocked)}
                  </div>
                  <CardDescription className="text-xs mt-1">
                    {isBlocked ? (
                      <span className="text-destructive font-semibold">
                        Dieser Container wurde von einem Administrator gesperrt
                      </span>
                    ) : (
                      container.description
                    )}
                  </CardDescription>
                </CardHeader>

                <CardContent className="p-4 pt-2 flex-1 flex flex-col">
                  <div className="space-y-3">
                    {/* Metadata */}
                    {(container.os || container.software) && (
                      <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-xs text-muted-foreground">
                        {container.os && (
                          <div>
                            <span className="font-medium text-foreground">OS:</span>{" "}
                            {container.os}
                          </div>
                        )}
                        {container.software && (
                          <div>
                            <span className="font-medium text-foreground">Software:</span>{" "}
                            {container.software}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Last used */}
                    {container.last_used && (
                      <div className="text-xs text-muted-foreground">
                        <span className="font-medium text-foreground">Zuletzt verwendet:</span>{" "}
                        {new Date(container.last_used).toLocaleString("de-DE")}
                      </div>
                    )}

                    {/* Blocked date */}
                    {isBlocked && container.blocked_at && (
                      <div className="text-xs text-destructive">
                        <span className="font-medium">Gesperrt am:</span>{" "}
                        {new Date(container.blocked_at).toLocaleString("de-DE")}
                      </div>
                    )}
                  </div>

                    {/* Action buttons */}
                    <div className="flex flex-wrap gap-1.5 pt-3 mt-auto">
                      {isBlocked ? (
                        <Button size="xs" variant="destructive" disabled>
                          <ShieldAlert className="h-4 w-4" />
                          Gesperrt
                        </Button>
                      ) : container.status === "not_created" ? (
                        <Button
                          size="xs"
                          onClick={() => handleLaunchContainer(container.type)}
                          disabled={busy}
                        >
                          {launching === container.type ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Wird erstellt...
                            </>
                          ) : (
                            <>
                              <Play className="h-4 w-4" />
                              Erstellen
                            </>
                          )}
                        </Button>
                      ) : (
                        <>
                          {container.status === "running" && (
                            <Button
                              size="xs"
                              onClick={() => window.open(container.service_url, "_blank")}
                              disabled={busy}
                            >
                              <ExternalLink className="h-4 w-4" />
                              Öffnen
                            </Button>
                          )}

                          {container.status !== "running" && (
                            <Button
                              size="xs"
                              onClick={() => handleLaunchContainer(container.type)}
                              disabled={busy}
                            >
                              {launching === container.type ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Play className="h-4 w-4" />
                              )}
                              Starten
                            </Button>
                          )}

                          {container.status === "running" && (
                            <Button
                              size="xs"
                              variant="outline"
                              onClick={() => handleRestartContainer(container.type)}
                              disabled={busy}
                            >
                              {restarting === container.type ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <RefreshCw className="h-4 w-4" />
                              )}
                              Neustarten
                            </Button>
                          )}

                          {container.status === "running" && (
                            <Button
                              size="xs"
                              variant="outline"
                              onClick={() => handleStopContainer(container.type)}
                              disabled={busy}
                            >
                              {stopping === container.type ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Square className="h-4 w-4" />
                              )}
                              Stoppen
                            </Button>
                          )}

                          {container.status === "error" && (
                            <Button
                              size="xs"
                              variant="outline"
                              onClick={() => handleRestartContainer(container.type)}
                              disabled={busy}
                            >
                              {restarting === container.type ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <RefreshCw className="h-4 w-4" />
                              )}
                              Neustarten
                            </Button>
                          )}

                          <Button
                            size="xs"
                            variant="outline"
                            className="text-destructive border-destructive/30 hover:text-destructive hover:bg-destructive/10"
                            onClick={() => setDeleteTarget(container.type)}
                            disabled={busy}
                          >
                            {deleting === container.type ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                            Löschen
                          </Button>
                        </>
                      )}
                    </div>
                </CardContent>
              </Card>
            );
          })}
                </div>
              </div>
            );
          })}
        </>
      )}

      {/* Delete confirmation dialog */}
      <AlertDialog open={deleteTarget !== null} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Container wirklich löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              Der Container und alle enthaltenen Daten werden unwiderruflich gelöscht.
              Du kannst den Container jederzeit neu erstellen.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting !== null}>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteTarget && handleDeleteContainer(deleteTarget)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleting !== null}
            >
              {deleting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              Endgültig löschen
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
