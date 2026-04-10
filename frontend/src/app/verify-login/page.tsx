"use client";

/** Login-Token-Verifizierungsseite — dünner Wrapper um VerifyTokenPage. */

import { useAuth } from "@/hooks/use-auth";
import VerifyTokenPage from "@/components/verify-token-page";

export default function VerifyLoginPage() {
  const { verifyLogin } = useAuth();

  return (
    <VerifyTokenPage
      config={{
        verifyFn: verifyLogin,
        loadingTitle: "Anmeldung läuft...",
        loadingText: "Bitte warten, du wirst angemeldet...",
        successTitle: "Anmeldung erfolgreich!",
        successDescription: "Weiterleitung zum Dashboard",
        errorTitle: "Anmeldung fehlgeschlagen",
        errorFallbackText: "Anmeldung fehlgeschlagen. Bitte fordere einen neuen Link an.",
        errorLinkText: "Neuen Link anfordern",
        errorLinkHref: "/login",
      }}
    />
  );
}
