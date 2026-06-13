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
      "Die Anmeldung läuft über einen Magic Link per E-Mail. Kein Passwort, kein OAuth-Anbieter, kein zusätzliches Konto.",
    Icon: MailCheck,
  },
  {
    title: "Isolierte Container",
    description:
      "Jeder Nutzer arbeitet in seinem eigenen Docker-Container unter einer eigenen Subdomain, getrennt von allen anderen.",
    Icon: Container,
  },
  {
    title: "Vorlagen-Katalog",
    description:
      "Fertige Vorlagen für VS Code, Next.js, MariaDB, LibreOffice, einen Linux-Desktop und die ESP8266-Entwicklung mit PlatformIO.",
    Icon: LayoutGrid,
  },
  {
    title: "Automatisches Aufräumen",
    description:
      "Container, die niemand mehr nutzt, werden automatisch gestoppt und entfernt. Die Daten der Nutzer bleiben erhalten.",
    Icon: TimerOff,
  },
  {
    title: "Bereit für die Produktion",
    description:
      "Traefik übernimmt das Routing, Let's Encrypt die Zertifikate. HTTPS und Subdomains sind ab Werk eingerichtet.",
    Icon: ShieldCheck,
  },
  {
    title: "Open Source und selbst gehostet",
    description:
      "OpenSpawner steht unter der MIT-Lizenz und läuft auf deiner eigenen Infrastruktur. Daten und Nutzer bleiben bei dir.",
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
            OpenSpawner kümmert sich um den ganzen Ablauf, von der Anmeldung bis
            zum Aufräumen alter Container.
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
