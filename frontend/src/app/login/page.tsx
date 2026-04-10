"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2, Mail, AlertCircle, PackageOpen } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { signup, user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [user, isLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email) {
      setError("Bitte gib deine E-Mail-Adresse ein");
      return;
    }

    setIsSubmitting(true);
    const result = await signup(email);

    if (result.success) {
      setEmailSent(true);
    } else {
      setError(result.message || "Anfrage fehlgeschlagen");
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-svh flex-col items-center justify-center bg-muted p-6 md:p-10">
        <div className="w-full max-w-sm md:max-w-4xl">
          <div className="flex flex-col gap-6">
            <Card className="overflow-hidden p-0">
              <CardContent className="grid p-0 md:grid-cols-2">
                <div className="p-6 md:p-8">
                  <div className="flex flex-col gap-6">
                    <div className="flex flex-col items-center gap-2">
                      <Skeleton className="h-8 w-32" />
                      <Skeleton className="h-4 w-64" />
                    </div>
                    <div className="grid gap-2">
                      <Skeleton className="h-4 w-12" />
                      <Skeleton className="h-10 w-full rounded-md" />
                    </div>
                    <Skeleton className="h-10 w-full rounded-md" />
                    <Skeleton className="h-4 w-72 mx-auto" />
                  </div>
                </div>
                <div className="relative hidden bg-primary md:flex md:flex-col md:items-center md:justify-center">
                  <div className="flex flex-col items-center gap-4 p-8">
                    <Skeleton className="h-16 w-16 rounded bg-primary-foreground/20" />
                    <div className="flex flex-col items-center gap-2">
                      <Skeleton className="h-8 w-40 bg-primary-foreground/20" />
                      <Skeleton className="h-4 w-56 bg-primary-foreground/20" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-muted p-6 md:p-10">
      <div className="w-full max-w-sm md:max-w-4xl">
        <div className="flex flex-col gap-6">
          <Card className="overflow-hidden p-0">
            <CardContent className="grid p-0 md:grid-cols-2">
              <div className="p-6 md:p-8">
                {emailSent ? (
                  <div className="flex flex-col gap-6">
                    <div className="flex flex-col items-center gap-2 text-center">
                      <h1 className="text-2xl font-bold">Prüfe dein Postfach</h1>
                      <p className="text-balance text-sm text-muted-foreground">
                        Wir haben einen Anmelde-Link an <strong>{email}</strong> gesendet
                      </p>
                    </div>
                    <div className="rounded-md border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-950">
                      <div className="flex items-start gap-3">
                        <Mail className="mt-0.5 h-5 w-5 text-green-600 dark:text-green-400" />
                        <div className="space-y-1">
                          <p className="text-sm font-medium text-green-800 dark:text-green-200">
                            E-Mail gesendet!
                          </p>
                          <p className="text-sm text-green-700 dark:text-green-300">
                            Klicke auf den Link in deinem Postfach, um fortzufahren.
                          </p>
                          <p className="text-xs text-green-600 dark:text-green-400">
                            Der Link ist 15 Minuten gültig.
                          </p>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => {
                        setEmailSent(false);
                        setEmail("");
                        setIsSubmitting(false);
                      }}
                    >
                      Neuen Link anfordern
                    </Button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit}>
                    <div className="flex flex-col gap-6">
                      <div className="flex flex-col items-center gap-2 text-center">
                        <h1 className="text-2xl font-bold">Willkommen</h1>
                        <p className="text-balance text-sm text-muted-foreground">
                          E-Mail eingeben, um dich anzumelden oder zu registrieren
                        </p>
                      </div>
                      {error && (
                        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                          <div className="flex items-start gap-2">
                            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                            <span>{error}</span>
                          </div>
                        </div>
                      )}
                      <div className="grid gap-2">
                        <Label htmlFor="email">E-Mail</Label>
                        <Input
                          id="email"
                          type="email"
                          placeholder="du@beispiel.de"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          required
                          autoComplete="email"
                          disabled={isSubmitting}
                        />
                      </div>
                      <Button
                        type="submit"
                        className="w-full"
                        disabled={isSubmitting}
                      >
                        {isSubmitting ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Anmelde-Link wird gesendet...
                          </>
                        ) : (
                          "Weiter mit E-Mail"
                        )}
                      </Button>
                      <p className="text-center text-sm text-muted-foreground">
                        Kein Passwort nötig, wir senden dir einen Anmelde-Link.
                      </p>
                    </div>
                  </form>
                )}
              </div>
              <div className="relative hidden bg-primary md:flex md:flex-col md:items-center md:justify-center">
                <div className="flex flex-col items-center gap-4 p-8 text-primary-foreground">
                  <PackageOpen className="h-16 w-16" />
                  <div className="text-center">
                    <h2 className="text-2xl font-bold">OpenSpawner</h2>
                    <p className="mt-2 text-sm text-primary-foreground/80">
                      Deine persönliche Container-Plattform
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
