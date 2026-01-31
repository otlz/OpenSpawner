"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { XCircle, RefreshCw, Mail, Loader2 } from "lucide-react";

function VerifyErrorContent() {
  const searchParams = useSearchParams();
  const reason = searchParams.get("reason");

  const getErrorMessage = () => {
    switch (reason) {
      case "missing_token":
        return "Der Verifizierungs-Link ist unvollstaendig.";
      case "invalid_token":
        return "Der Verifizierungs-Link ist ungueltig oder bereits verwendet worden.";
      case "expired_token":
        return "Der Verifizierungs-Link ist abgelaufen.";
      default:
        return "Bei der Verifizierung ist ein Fehler aufgetreten.";
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <XCircle className="h-8 w-8 text-red-600" />
          </div>
          <CardTitle className="text-2xl">Verifizierung fehlgeschlagen</CardTitle>
          <CardDescription>{getErrorMessage()}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-center text-sm text-muted-foreground">
            Moegliche Gruende:
          </p>
          <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
            <li>Der Link wurde bereits verwendet</li>
            <li>Der Link wurde nicht vollstaendig kopiert</li>
            <li>Du hast einen neueren Verifizierungs-Link erhalten</li>
          </ul>
          <div className="flex flex-col gap-2 pt-4">
            <Button asChild variant="outline" className="w-full">
              <Link href="/login">
                <RefreshCw className="mr-2 h-4 w-4" />
                Zum Login (neue Email anfordern)
              </Link>
            </Button>
            <Button asChild variant="ghost" className="w-full">
              <Link href="/signup">
                <Mail className="mr-2 h-4 w-4" />
                Neu registrieren
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function VerifyErrorPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-muted/50 px-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    }>
      <VerifyErrorContent />
    </Suspense>
  );
}
