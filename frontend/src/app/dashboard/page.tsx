"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { api, UserResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Container,
  ExternalLink,
  RefreshCw,
  LogOut,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from "lucide-react";

export default function DashboardPage() {
  const { user, logout, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [userData, setUserData] = useState<UserResponse | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [error, setError] = useState("");

  const fetchUserData = useCallback(async () => {
    const { data, error } = await api.getUser();
    if (data) {
      setUserData(data);
    } else if (error) {
      setError(error);
    }
  }, []);

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login");
    } else if (user) {
      fetchUserData();
    }
  }, [user, authLoading, router, fetchUserData]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchUserData();
    setIsRefreshing(false);
  };

  const handleRestart = async () => {
    setIsRestarting(true);
    setError("");

    const { data, error } = await api.restartContainer();

    if (error) {
      setError(error);
    } else {
      await fetchUserData();
    }

    setIsRestarting(false);
  };

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return (
          <Badge variant="success" className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Lauft
          </Badge>
        );
      case "exited":
      case "stopped":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Gestoppt
          </Badge>
        );
      case "no_container":
        return (
          <Badge variant="warning" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Kein Container
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            {status}
          </Badge>
        );
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
    <div className="min-h-screen bg-muted/50">
      {/* Header */}
      <header className="border-b bg-background">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Container className="h-6 w-6 text-primary" />
            <span className="text-lg font-semibold">Container Spawner</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs">
                  {user.username.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium">{user.username}</span>
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
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Verwalte deinen personlichen Container
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-md bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          {/* Container Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Container className="h-5 w-5" />
                Container Status
              </CardTitle>
              <CardDescription>
                Informationen zu deinem personlichen Container
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status</span>
                {userData ? (
                  getStatusBadge(userData.container.status)
                ) : (
                  <Loader2 className="h-4 w-4 animate-spin" />
                )}
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">
                  Container ID
                </span>
                <code className="rounded bg-muted px-2 py-1 text-xs">
                  {userData?.container.id?.slice(0, 12) || "-"}
                </code>
              </div>
              <Separator />
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                >
                  {isRefreshing ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-2 h-4 w-4" />
                  )}
                  Aktualisieren
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleRestart}
                  disabled={isRestarting}
                >
                  {isRestarting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-2 h-4 w-4" />
                  )}
                  Neu starten
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Service URL Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ExternalLink className="h-5 w-5" />
                Dein Service
              </CardTitle>
              <CardDescription>
                Zugriff auf deinen personlichen Bereich
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-md border bg-muted/50 p-4">
                <p className="mb-2 text-sm text-muted-foreground">
                  Deine Service-URL:
                </p>
                {userData?.container.service_url ? (
                  <a
                    href={userData.container.service_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-primary hover:underline"
                  >
                    {userData.container.service_url}
                    <ExternalLink className="h-4 w-4" />
                  </a>
                ) : (
                  <span className="text-muted-foreground">Laden...</span>
                )}
              </div>
              <Button
                className="w-full"
                asChild
                disabled={
                  !userData?.container.service_url ||
                  userData?.container.status !== "running"
                }
              >
                <a
                  href={userData?.container.service_url || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Service offnen
                </a>
              </Button>
              {userData?.container.status !== "running" && (
                <p className="text-center text-sm text-muted-foreground">
                  Container muss laufen, um den Service zu nutzen
                </p>
              )}
            </CardContent>
          </Card>

          {/* User Info Card */}
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Kontoinformationen</CardTitle>
              <CardDescription>Deine personlichen Daten</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-sm text-muted-foreground">Benutzername</p>
                  <p className="font-medium">{user.username}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">E-Mail</p>
                  <p className="font-medium">{user.email}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Registriert</p>
                  <p className="font-medium">
                    {userData?.user.created_at
                      ? new Date(userData.user.created_at).toLocaleDateString(
                          "de-DE"
                        )
                      : "-"}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
