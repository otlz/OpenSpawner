"use client";

import { Button } from "@/components/ui/button";
import { FadeInView } from "@/components/animation/fade-in-view";
import { GithubIcon } from "@/components/landing/github-icon";
import { GITHUB_URL } from "@/lib/site";

export function HeroSection() {
  return (
    <section className="relative pt-28 pb-12 md:pt-40 md:pb-16">
      <div className="mx-auto w-full max-w-7xl px-4 lg:px-8">
        <FadeInView className="max-w-5xl">
          <h1 className="text-3xl leading-[1.1] font-semibold tracking-tight md:text-4xl lg:text-5xl">
            Eine eigene Umgebung für jeden Nutzer.
            <br />
            <span className="text-muted-foreground">
              Gestartet per Klick, erreichbar unter eigener Subdomain.
            </span>
          </h1>

          <p className="mt-6 max-w-2xl text-lg text-muted-foreground">
            OpenSpawner startet für jeden angemeldeten Nutzer einen eigenen
            Docker-Container. Die Anmeldung läuft über einen Link per E-Mail,
            ganz ohne Passwort. Vorlage aus dem Katalog wählen und loslegen.
          </p>

          <div className="mt-8">
            <Button size="lg" asChild>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
                <GithubIcon />
                Auf GitHub ansehen
              </a>
            </Button>
          </div>
        </FadeInView>
      </div>
    </section>
  );
}
