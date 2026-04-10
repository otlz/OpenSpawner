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
        loadingTitle: "Logging in...",
        loadingText: "Please wait, logging you in...",
        successTitle: "Login successful!",
        successDescription: "Redirecting to dashboard",
        errorTitle: "Login failed",
        errorFallbackText: "Login failed. Please request a new link.",
        errorLinkText: "Request new link",
        errorLinkHref: "/login",
      }}
    />
  );
}
