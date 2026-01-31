"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CheckCircle2, Container, Loader2 } from "lucide-react";

export default function VerifySuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [isVerifying, setIsVerifying] = useState(!!token);
  const [verified, setVerified] = useState(!token);

  useEffect(() => {
    // Wenn ein Token in der URL ist, wurde der User vom Backend hierher redirected
    // und die Verifizierung ist bereits erfolgt
    if (token) {
      // Kurze Verzoegerung fuer bessere UX
      const timer = setTimeout(() => {
        setIsVerifying(false);
        setVerified(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [token]);

  if (isVerifying) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-muted/50 px-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="mt-4 text-center text-muted-foreground">
              Email wird verifiziert...
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          </div>
          <CardTitle className="text-2xl">Email verifiziert!</CardTitle>
          <CardDescription>
            Deine Email-Adresse wurde erfolgreich bestaetigt.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-center text-sm text-muted-foreground">
            Du kannst dich jetzt mit deinen Zugangsdaten anmelden und deinen
            Container nutzen.
          </p>
          <div className="flex flex-col gap-2">
            <Button asChild className="w-full">
              <Link href="/login">
                <Container className="mr-2 h-4 w-4" />
                Zum Login
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
