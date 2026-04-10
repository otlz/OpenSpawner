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
        loadingTitle: "Verifying...",
        loadingText: "Please wait, verifying your account...",
        successTitle: "Account created!",
        successDescription: "Your account has been created and verified",
        errorTitle: "Verification failed",
        errorFallbackText: "Verification failed. Please request a new link.",
        errorLinkText: "Back to Login",
        errorLinkHref: "/login",
      }}
    />
  );
}
