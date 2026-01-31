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
  LogOut,
  Shield,
  Container as ContainerIcon,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import Link from "next/link";

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
        setError(apiError);
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

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  if (authLoading || !user) {
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
          <div className="flex items-center gap-2">
            <ContainerIcon className="h-6 w-6 text-primary" />
            <span className="text-lg font-semibold">Container Spawner</span>
          </div>
          <div className="flex items-center gap-4">
            {/* Admin-Link */}
            {user.is_admin && (
              <Link href="/admin">
                <Button variant="outline" size="sm">
                  <Shield className="mr-2 h-4 w-4" />
                  Admin
                </Button>
              </Link>
            )}
            <div className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs">
                  {user.email.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium">{user.email}</span>
              {user.is_admin && (
                <Badge variant="secondary" className="text-xs">
                  Admin
                </Badge>
              )}
            </div>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Abmelden
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Dashboard</h1>
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
            {containers.map((container) => (
              <Card key={container.type} className="relative">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <ContainerIcon className="h-5 w-5" />
                        {container.display_name}
                      </CardTitle>
                      <CardDescription>{container.description}</CardDescription>
                    </div>
                    {getStatusIcon(container.status)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="text-sm">
                      <p className="text-muted-foreground">Status:</p>
                      <p className="font-medium">{getStatusText(container.status)}</p>
                    </div>

                    {container.last_used && (
                      <div className="text-sm">
                        <p className="text-muted-foreground">Zuletzt verwendet:</p>
                        <p className="font-medium">
                          {new Date(container.last_used).toLocaleString("de-DE")}
                        </p>
                      </div>
                    )}

                    <div className="flex gap-2">
                      {container.status === "running" ? (
                        <Button
                          className="flex-1"
                          onClick={() =>
                            window.open(container.service_url, "_blank")
                          }
                        >
                          <ExternalLink className="mr-2 h-4 w-4" />
                          Service öffnen
                        </Button>
                      ) : (
                        <Button
                          className="flex-1"
                          onClick={() => handleLaunchContainer(container.type)}
                          disabled={launching === container.type}
                        >
                          {launching === container.type ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Wird gestartet...
                            </>
                          ) : (
                            <>
                              <Play className="mr-2 h-4 w-4" />
                              {container.status === "not_created"
                                ? "Erstellen & Öffnen"
                                : "Starten & Öffnen"}
                            </>
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
