"use client";

/** Signup-Token-Verifizierungsseite — dünner Wrapper um VerifyTokenPage. */

import { useAuth } from "@/hooks/use-auth";
import VerifyTokenPage from "@/components/verify-token-page";

export default function VerifySignupPage() {
  const { verifySignup } = useAuth();

  return (
    <VerifyTokenPage
      config={{
        verifyFn: verifySignup,
        loadingTitle: "Verifizierung läuft...",
        loadingText: "Bitte warten, dein Konto wird verifiziert...",
        successTitle: "Konto erstellt!",
        successDescription: "Dein Konto wurde erstellt und verifiziert",
        errorTitle: "Verifizierung fehlgeschlagen",
        errorFallbackText: "Verifizierung fehlgeschlagen. Bitte fordere einen neuen Link an.",
        errorLinkText: "Zurück zum Login",
        errorLinkHref: "/login",
      }}
    />
  );
}
