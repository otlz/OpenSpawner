"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Mail, AlertCircle, Package } from "lucide-react";

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
      setError("Please enter your email address");
      return;
    }

    setIsSubmitting(true);
    const result = await signup(email);

    if (result.success) {
      setEmailSent(true);
    } else {
      setError(result.message || "Request failed");
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
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
                      <h1 className="text-2xl font-bold">Check your email</h1>
                      <p className="text-balance text-sm text-muted-foreground">
                        We sent a magic link to <strong>{email}</strong>
                      </p>
                    </div>
                    <div className="rounded-md border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-950">
                      <div className="flex items-start gap-3">
                        <Mail className="mt-0.5 h-5 w-5 text-green-600 dark:text-green-400" />
                        <div className="space-y-1">
                          <p className="text-sm font-medium text-green-800 dark:text-green-200">
                            Email sent!
                          </p>
                          <p className="text-sm text-green-700 dark:text-green-300">
                            Click the link in your inbox to continue.
                          </p>
                          <p className="text-xs text-green-600 dark:text-green-400">
                            The link is valid for 15 minutes.
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
                      Request new link
                    </Button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit}>
                    <div className="flex flex-col gap-6">
                      <div className="flex flex-col items-center gap-2 text-center">
                        <h1 className="text-2xl font-bold">Welcome back</h1>
                        <p className="text-balance text-sm text-muted-foreground">
                          Enter your email to sign in or create an account
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
                        <Label htmlFor="email">Email</Label>
                        <Input
                          id="email"
                          type="email"
                          placeholder="you@example.com"
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
                            Sending magic link...
                          </>
                        ) : (
                          "Continue with Email"
                        )}
                      </Button>
                      <p className="text-center text-sm text-muted-foreground">
                        No password needed — we&apos;ll send you a magic link.
                      </p>
                    </div>
                  </form>
                )}
              </div>
              <div className="relative hidden bg-primary md:flex md:flex-col md:items-center md:justify-center">
                <div className="flex flex-col items-center gap-4 p-8 text-primary-foreground">
                  <Package className="h-16 w-16" />
                  <div className="text-center">
                    <h2 className="text-2xl font-bold">OpenSpawner</h2>
                    <p className="mt-2 text-sm text-primary-foreground/80">
                      Your personal container platform
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
