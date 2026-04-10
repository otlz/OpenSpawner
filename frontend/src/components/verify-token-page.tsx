"use client";

/**
 * Gemeinsame Komponente für Token-Verifizierung (Login und Signup).
 * Verarbeitet den Token aus der URL und zeigt Lade-/Erfolgs-/Fehlerstatus an.
 */

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
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

interface VerifyTokenPageConfig {
  verifyFn: (token: string) => Promise<{ success: boolean }>;
  loadingTitle: string;
  loadingText: string;
  successTitle: string;
  successDescription: string;
  errorTitle: string;
  errorFallbackText: string;
  errorLinkText: string;
  errorLinkHref: string;
}

function VerifyTokenContent({ config }: { config: VerifyTokenPageConfig }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [error, setError] = useState("");
  const verifiedRef = useRef(false);

  useEffect(() => {
    if (verifiedRef.current) return;

    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setError("No token found");
      return;
    }

    verifiedRef.current = true;

    const verify = async () => {
      const result = await config.verifyFn(token);
      if (result.success) {
        setStatus("success");
        setTimeout(() => router.push("/dashboard"), 1000);
      } else {
        setStatus("error");
        setError(config.errorFallbackText);
      }
    };

    verify();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          {status === "loading" && (
            <>
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
              <CardTitle className="text-2xl font-bold">{config.loadingTitle}</CardTitle>
            </>
          )}

          {status === "success" && (
            <>
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle className="text-2xl font-bold">{config.successTitle}</CardTitle>
              <CardDescription>{config.successDescription}</CardDescription>
            </>
          )}

          {status === "error" && (
            <>
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertCircle className="h-6 w-6 text-destructive" />
              </div>
              <CardTitle className="text-2xl font-bold">{config.errorTitle}</CardTitle>
            </>
          )}
        </CardHeader>

        <CardContent>
          {status === "loading" && (
            <p className="text-center text-muted-foreground">{config.loadingText}</p>
          )}

          {status === "success" && (
            <div className="space-y-4">
              <p className="text-center text-muted-foreground">
                You will be redirected to the dashboard automatically.
              </p>
              <Button className="w-full" onClick={() => router.push("/dashboard")}>
                Go to Dashboard
              </Button>
            </div>
          )}

          {status === "error" && (
            <div className="space-y-4">
              <p className="text-center text-destructive">{error}</p>
              <Button variant="outline" className="w-full" asChild>
                <Link href={config.errorLinkHref}>{config.errorLinkText}</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function VerifyTokenPage({ config }: { config: VerifyTokenPageConfig }) {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-muted/50 p-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </div>
      }
    >
      <VerifyTokenContent config={config} />
    </Suspense>
  );
}
