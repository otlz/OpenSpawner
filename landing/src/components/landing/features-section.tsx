"use client";

import {
  Container,
  LayoutGrid,
  MailCheck,
  Server,
  ShieldCheck,
  TimerOff,
  type LucideIcon,
} from "lucide-react";

import {
  FadeInView,
  StaggerContainer,
  StaggerItem,
} from "@/components/animation/fade-in-view";

type Feature = {
  title: string;
  description: string;
  Icon: LucideIcon;
};

const features: Feature[] = [
  {
    title: "Passwortloser Login",
    description:
      "Anmeldung per Magic Link: Nutzer erhalten einen Link per E-Mail, ganz ohne Passwort und ohne externen OAuth-Anbieter.",
    Icon: MailCheck,
  },
  {
    title: "Isolierte Container",
    description:
      "Jeder Nutzer bekommt einen eigenen Docker-Container mit eigener Subdomain, sauber getrennt von allen anderen.",
    Icon: Container,
  },
  {
    title: "Vorlagen-Katalog",
    description:
      "Fertige Templates für VS Code, Next.js, MariaDB, Linux Mint, LibreOffice und die ESP8266-Entwicklung, startklar per Klick.",
    Icon: LayoutGrid,
  },
  {
    title: "Automatisches Aufräumen",
    description:
      "Inaktive Container werden automatisch gestoppt und entfernt, die Daten der Nutzer bleiben dabei erhalten.",
    Icon: TimerOff,
  },
  {
    title: "Bereit für die Produktion",
    description:
      "Traefik als Reverse Proxy und Let's Encrypt für HTTPS sind vorbereitet, inklusive automatischer Zertifikate.",
    Icon: ShieldCheck,
  },
  {
    title: "Open Source und selbst gehostet",
    description:
      "MIT-lizenziert und komplett auf eigener Infrastruktur betrieben: volle Kontrolle über Daten, Nutzer und Umgebung.",
    Icon: Server,
  },
];

function FeatureCard({ feature }: { feature: Feature }) {
  const { Icon } = feature;

  return (
    <div className="flex h-full flex-col rounded-xl border border-border/50 bg-card p-6 shadow-sm transition-colors hover:border-border">
      <span className="mb-4 inline-flex size-11 items-center justify-center rounded-lg bg-muted text-foreground">
        <Icon className="size-5" />
      </span>
      <h3 className="text-base font-medium">{feature.title}</h3>
      <p className="mt-2 flex-1 text-sm text-muted-foreground">
        {feature.description}
      </p>
    </div>
  );
}

export function FeaturesSection() {
  return (
    <section id="features" className="scroll-mt-20 py-16 md:py-24">
      <div className="mx-auto w-full max-w-7xl px-4 lg:px-8">
        <FadeInView className="mb-12 max-w-2xl">
          <h2 className="mb-4 text-2xl font-semibold tracking-tight md:text-3xl">
            Was OpenSpawner kann
          </h2>
          <p className="text-muted-foreground">
            Von der Anmeldung bis zum Aufräumen: OpenSpawner übernimmt den
            kompletten Lebenszyklus der Nutzer-Container.
          </p>
        </FadeInView>

        <StaggerContainer
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
          staggerDelay={0.1}
        >
          {features.map((feature) => (
            <StaggerItem key={feature.title}>
              <FeatureCard feature={feature} />
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  );
}
