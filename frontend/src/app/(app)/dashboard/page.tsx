"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { api, type Container } from "@/lib/api";
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
  ExternalLink,
  Loader2,
  Play,
  CheckCircle,
  AlertCircle,
  Container as ContainerIcon,
  ShieldAlert,
} from "lucide-react";
import { toast } from "sonner";

/** Zeigt den passenden Aktions-Button für einen Container an (gesperrt/öffnen/starten). */
function ContainerActionButton({
  container,
  isBlocked,
  launching,
  onLaunch,
}: {
  container: Container;
  isBlocked: boolean;
  launching: string | null;
  onLaunch: (type: string) => void;
}) {
  if (isBlocked) {
    return (
      <Button className="flex-1" variant="destructive" disabled>
        <ShieldAlert className="mr-2 h-4 w-4" />
        Gesperrt
      </Button>
    );
  }

  if (container.status === "running") {
    return (
      <Button className="flex-1" onClick={() => window.open(container.service_url, "_blank")}>
        <ExternalLink className="mr-2 h-4 w-4" />
        Service öffnen
      </Button>
    );
  }

  return (
    <Button className="flex-1" onClick={() => onLaunch(container.type)} disabled={launching === container.type}>
      {launching === container.type ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Wird gestartet...
        </>
      ) : (
        <>
          <Play className="mr-2 h-4 w-4" />
          {container.status === "not_created" ? "Erstellen & Öffnen" : "Starten & Öffnen"}
        </>
      )}
    </Button>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout, isLoading: authLoading } = useAuth();
  const [containers, setContainers] = useState<Container[]>([]);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState<string | null>(null);
  const [error, setError] = useState("");

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
      } else if (apiError) {
        setError(apiError);
      }
    } catch (err) {
      setError("Fehler beim Laden der Container");
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchContainer = async (containerType: string) => {
    setLaunching(containerType);
    setError("");
    try {
      const { data, error: apiError } = await api.launchContainer(
        containerType
      );
      if (data) {
        // Container erfolgreich gestartet - öffne in neuem Tab
        window.open(data.service_url, "_blank");
        // Reload Container-Liste
        await loadContainers();
      } else if (apiError) {
        // Prüfe auf Blocking-Fehler
        if (apiError.includes("Administrator")) {
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "stopped":
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case "error":
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "running":
        return "Läuft";
      case "stopped":
        return "Gestoppt";
      case "error":
        return "Fehler";
      case "not_created":
        return "Noch nicht erstellt";
      default:
        return status;
    }
  };

  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Deine Container</h2>
        <p className="text-muted-foreground">
          Verwalte deine Development- und Production-Container
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {containers.map((container) => {
            const isBlocked = container.is_blocked === true;  // Phase 7

            return (
            <Card
              key={container.type}
              className={`relative transition-all ${
                isBlocked ? "border-red-500 bg-red-50" : ""
              }`}
            >
              {/* Blocked Badge */}
              {isBlocked && (
                <div className="absolute top-3 right-3">
                  <Badge variant="destructive" className="text-xs">
                    <ShieldAlert className="mr-1 h-3 w-3" />
                    Gesperrt
                  </Badge>
                </div>
              )}

              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <ContainerIcon className="h-5 w-5" />
                      {container.display_name}
                    </CardTitle>
                    <CardDescription>
                      {isBlocked ? (
                        <span className="text-destructive font-semibold">
                          Dieser Container wurde von einem Administrator gesperrt
                        </span>
                      ) : (
                        container.description
                      )}
                    </CardDescription>
                  </div>
                  {!isBlocked && getStatusIcon(container.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-sm">
                    <p className="text-muted-foreground">Status:</p>
                    <p className="font-medium">
                      {isBlocked ? "Gesperrt von Admin" : getStatusText(container.status)}
                    </p>
                  </div>

                  {container.last_used && (
                    <div className="text-sm">
                      <p className="text-muted-foreground">Zuletzt verwendet:</p>
                      <p className="font-medium">
                        {new Date(container.last_used).toLocaleString("de-DE")}
                      </p>
                    </div>
                  )}

                  {isBlocked && container.blocked_at && (
                    <div className="text-sm text-destructive">
                      <p className="text-muted-foreground">Gesperrt am:</p>
                      <p className="font-medium">
                        {new Date(container.blocked_at).toLocaleString("de-DE")}
                      </p>
                    </div>
                  )}

                  {/* Aktions-Button je nach Status */}
                  <div className="flex gap-2">
                    <ContainerActionButton
                      container={container}
                      isBlocked={isBlocked}
                      launching={launching}
                      onLaunch={handleLaunchContainer}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
            );
          })}
        </div>
      )}
    </>
  );
}
