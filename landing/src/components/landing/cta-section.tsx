"use client";

import { Button } from "@/components/ui/button";
import { FadeInView } from "@/components/animation/fade-in-view";
import { GithubIcon } from "@/components/landing/github-icon";
import { GITHUB_URL } from "@/lib/site";

export function CTASection() {
  return (
    <section className="relative py-32 md:py-48">
      {/* Full-width background that fades up into the page, like the reference
          landing page. Separate images per theme keep the band subtle in both. */}
      <div className="absolute inset-0 left-1/2 w-screen -translate-x-1/2 overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center dark:hidden"
          style={{ backgroundImage: "url('/branding/cta-background-light.png')" }}
        />
        <div
          className="absolute inset-0 hidden bg-cover bg-center dark:block"
          style={{ backgroundImage: "url('/branding/cta-background-dark.png')" }}
        />
        <div className="absolute inset-x-0 top-0 h-5/6 bg-gradient-to-b from-background via-background/70 to-transparent" />
      </div>

      <div className="relative mx-auto w-full max-w-7xl px-4 lg:px-8">
        <FadeInView className="max-w-2xl">
          <h2 className="mb-4 text-2xl font-semibold tracking-tight md:text-3xl">
            Bereit für die erste eigene Umgebung?
          </h2>
          <p className="text-muted-foreground">
            Der komplette Quellcode liegt auf GitHub. Repository klonen, die
            .env anpassen und mit Docker Compose starten. Nach ein paar Minuten
            läuft die erste Instanz.
          </p>
          <div className="mt-8">
            <Button size="lg" asChild>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
                <GithubIcon />
                Zum Repository auf GitHub
              </a>
            </Button>
          </div>
        </FadeInView>
      </div>
    </section>
  );
}
