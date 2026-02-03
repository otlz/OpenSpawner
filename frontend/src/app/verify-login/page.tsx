"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";

function VerifyLoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { verifyLogin } = useAuth();

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");

    if (!token) {
      setStatus("error");
      setError("Kein Token gefunden");
      return;
    }

    const verify = async () => {
      const maxRetries = 5;
      const retryDelay = 2000; // 2 Sekunden
      const maxTimeout = 10000; // 10 Sekunden Gesamtzeit

      let attempt = 0;
      const startTime = Date.now();

      while (attempt < maxRetries) {
        // Prüfe ob Timeout überschritten
        if (Date.now() - startTime > maxTimeout) {
          setStatus("error");
          setError("Login hat zu lange gedauert. Bitte versuche es später erneut.");
          return;
        }

        const result = await verifyLogin(token);

        if (result.success) {
          setStatus("success");
          // Redirect nach 1 Sekunde zum Dashboard
          setTimeout(() => {
            router.push("/dashboard");
          }, 1000);
          return;
        }

        // Fehler - Versuche erneut (außer beim letzten Versuch)
        attempt++;
        if (attempt < maxRetries) {
          // Warte vor nächstem Versuch
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
      }

      // Alle Versuche fehlgeschlagen
      setStatus("error");
      setError("Login fehlgeschlagen. Bitte versuche den Link erneut anzufordern.");
    };

    verify();
  }, [searchParams, verifyLogin, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          {status === "loading" && (
            <>
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
              <CardTitle className="text-2xl font-bold">
                Login läuft...
              </CardTitle>
            </>
          )}

          {status === "success" && (
            <>
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle className="text-2xl font-bold">
                Login erfolgreich!
              </CardTitle>
              <CardDescription>
                Du wirst zum Dashboard weitergeleitet
              </CardDescription>
            </>
          )}

          {status === "error" && (
            <>
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertCircle className="h-6 w-6 text-destructive" />
              </div>
              <CardTitle className="text-2xl font-bold">
                Login fehlgeschlagen
              </CardTitle>
            </>
          )}
        </CardHeader>

        <CardContent>
          {status === "loading" && (
            <p className="text-center text-muted-foreground">
              Bitte warten, du wirst eingeloggt...
            </p>
          )}

          {status === "success" && (
            <div className="space-y-4">
              <p className="text-center text-muted-foreground">
                Du wirst automatisch zum Dashboard weitergeleitet.
              </p>
              <Button className="w-full" onClick={() => router.push("/dashboard")}>
                Zum Dashboard
              </Button>
            </div>
          )}

          {status === "error" && (
            <div className="space-y-4">
              <p className="text-center text-destructive">{error}</p>
              <Button variant="outline" className="w-full" asChild>
                <Link href="/login">Neuen Login-Link anfordern</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function VerifyLoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-muted/50 p-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </div>
      }
    >
      <VerifyLoginContent />
    </Suspense>
  );
}
