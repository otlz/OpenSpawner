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

function VerifySignupContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { verifySignup } = useAuth();

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");

    if (!token) {
      setStatus("error");
      setError("No token found");
      return;
    }

    const verify = async () => {
      const maxRetries = 5;
      const retryDelay = 2000;
      const maxTimeout = 10000;

      let attempt = 0;
      const startTime = Date.now();

      while (attempt < maxRetries) {
        if (Date.now() - startTime > maxTimeout) {
          setStatus("error");
          setError("Verification timed out. Please try again.");
          return;
        }

        const result = await verifySignup(token);

        if (result.success) {
          setStatus("success");
          setTimeout(() => {
            router.push("/dashboard");
          }, 2000);
          return;
        }

        attempt++;
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
      }

      setStatus("error");
      setError("Verification failed. Please request a new link.");
    };

    verify();
  }, [searchParams, verifySignup, router]);

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
                Verifying...
              </CardTitle>
            </>
          )}

          {status === "success" && (
            <>
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle className="text-2xl font-bold">
                Account created!
              </CardTitle>
              <CardDescription>
                Your account has been created and verified
              </CardDescription>
            </>
          )}

          {status === "error" && (
            <>
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertCircle className="h-6 w-6 text-destructive" />
              </div>
              <CardTitle className="text-2xl font-bold">
                Verification failed
              </CardTitle>
            </>
          )}
        </CardHeader>

        <CardContent>
          {status === "loading" && (
            <p className="text-center text-muted-foreground">
              Please wait, verifying your account...
            </p>
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
                <Link href="/login">Back to Login</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function VerifySignupPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-muted/50 p-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </div>
      }
    >
      <VerifySignupContent />
    </Suspense>
  );
}
