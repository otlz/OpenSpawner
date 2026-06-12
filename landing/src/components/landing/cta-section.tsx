"use client";

import { Button } from "@/components/ui/button";
import { FadeInView } from "@/components/animation/fade-in-view";
import { GithubIcon } from "@/components/landing/github-icon";
import { GITHUB_URL } from "@/lib/site";

export function CTASection() {
  return (
    <section className="py-16 md:py-24">
      <div className="mx-auto w-full max-w-7xl px-4 lg:px-8">
        <FadeInView>
          <div className="rounded-2xl border bg-card p-8 text-center shadow-sm md:p-14">
            <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
              Bereit, OpenSpawner auszuprobieren?
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              Der gesamte Quellcode liegt auf GitHub. Klonen, konfigurieren und
              in wenigen Minuten die erste Umgebung starten.
            </p>
            <div className="mt-8">
              <Button size="lg" asChild>
                <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
                  <GithubIcon />
                  Zum GitHub-Repository
                </a>
              </Button>
            </div>
          </div>
        </FadeInView>
      </div>
    </section>
  );
}
