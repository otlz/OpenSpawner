import type { Locale } from "./config";

// German is the source of truth: its shape defines the Dictionary type, so the
// English dictionary below is type-checked to contain exactly the same keys.
// Icons, URLs and the brand name stay in the components, not here, because they
// do not change between languages.
const de = {
  metaDescription:
    "OpenSpawner ist eine selbst gehostete Open-Source-Plattform, die isolierte Docker-Container pro Nutzer bereitstellt: passwortloser Login, Vorlagen-Katalog und automatisches Aufräumen.",

  nav: {
    switchLanguage: "Sprache wechseln",
  },

  hero: {
    titleLine1: "Eine eigene Umgebung für jeden Nutzer.",
    titleLine2: "Gestartet per Klick, erreichbar unter eigener Subdomain.",
    body: "OpenSpawner startet für jeden angemeldeten Nutzer einen eigenen Docker-Container. Die Anmeldung läuft über einen Link per E-Mail, ganz ohne Passwort. Vorlage aus dem Katalog wählen und loslegen.",
    cta: "Auf GitHub ansehen",
  },

  preview: {
    imageAlt:
      "Das OpenSpawner-Dashboard mit dem Vorlagen-Katalog, gruppiert nach Anwendungen, Betriebssystemen und Datenbanken.",
  },

  features: {
    heading: "Was OpenSpawner kann",
    intro:
      "OpenSpawner kümmert sich um den ganzen Ablauf, von der Anmeldung bis zum Aufräumen alter Container.",
    items: {
      passwordless: {
        title: "Passwortloser Login",
        description:
          "Die Anmeldung läuft über einen Magic Link per E-Mail. Kein Passwort, kein OAuth-Anbieter, kein zusätzliches Konto.",
      },
      isolated: {
        title: "Isolierte Container",
        description:
          "Jeder Nutzer arbeitet in seinem eigenen Docker-Container unter einer eigenen Subdomain, getrennt von allen anderen.",
      },
      catalog: {
        title: "Vorlagen-Katalog",
        description:
          "Fertige Vorlagen für VS Code, Next.js, MariaDB, LibreOffice, einen Linux-Desktop und die ESP8266-Entwicklung mit PlatformIO.",
      },
      cleanup: {
        title: "Automatisches Aufräumen",
        description:
          "Container, die niemand mehr nutzt, werden automatisch gestoppt und entfernt. Die Daten der Nutzer bleiben erhalten.",
      },
      production: {
        title: "Bereit für die Produktion",
        description:
          "Traefik übernimmt das Routing, Let's Encrypt die Zertifikate. HTTPS und Subdomains sind ab Werk eingerichtet.",
      },
      openSource: {
        title: "Open Source und selbst gehostet",
        description:
          "OpenSpawner steht unter der MIT-Lizenz und läuft auf deiner eigenen Infrastruktur. Daten und Nutzer bleiben bei dir.",
      },
    },
  },

  cta: {
    heading: "Bereit für die erste eigene Umgebung?",
    body: "Der komplette Quellcode liegt auf GitHub. Repository klonen, die .env anpassen und mit Docker Compose starten. Nach ein paar Minuten läuft die erste Instanz.",
    button: "Zum Repository auf GitHub",
  },

  footer: {
    tagline:
      "Isolierte Docker-Container für jeden Nutzer, selbst gehostet und Open Source.",
    project: "Projekt",
    legal: "Rechtliches",
    imprint: "Impressum",
    license: "MIT-Lizenz",
  },

  theme: {
    toggle: "Theme wechseln",
    light: "Hell",
    dark: "Dunkel",
    system: "System",
  },
};

// Derived from the German dictionary above (no `as const`, so values are typed
// as `string`). The English dictionary is annotated `: Dictionary`, which forces
// it to provide exactly these keys, no more and no fewer.
export type Dictionary = typeof de;

const en: Dictionary = {
  metaDescription:
    "OpenSpawner is a self-hosted, open-source platform that provisions an isolated Docker container per user: passwordless login, a template catalog, and automatic cleanup.",

  nav: {
    switchLanguage: "Switch language",
  },

  hero: {
    titleLine1: "A dedicated environment for every user.",
    titleLine2: "Launched in one click, reachable on its own subdomain.",
    body: "OpenSpawner starts a dedicated Docker container for every signed-in user. Sign-in works through a link sent by email, with no password at all. Pick a template from the catalog and get going.",
    cta: "View on GitHub",
  },

  preview: {
    imageAlt:
      "The OpenSpawner dashboard showing the template catalog, grouped by applications, operating systems, and databases.",
  },

  features: {
    heading: "What OpenSpawner does",
    intro:
      "OpenSpawner handles the entire flow, from sign-in to cleaning up old containers.",
    items: {
      passwordless: {
        title: "Passwordless login",
        description:
          "Sign-in works through a magic link sent by email. No password, no OAuth provider, no extra account.",
      },
      isolated: {
        title: "Isolated containers",
        description:
          "Every user works in their own Docker container on a dedicated subdomain, separated from everyone else.",
      },
      catalog: {
        title: "Template catalog",
        description:
          "Ready-made templates for VS Code, Next.js, MariaDB, LibreOffice, a Linux desktop, and ESP8266 development with PlatformIO.",
      },
      cleanup: {
        title: "Automatic cleanup",
        description:
          "Containers that nobody uses anymore are stopped and removed automatically. User data is preserved.",
      },
      production: {
        title: "Production ready",
        description:
          "Traefik handles routing, Let's Encrypt handles certificates. HTTPS and subdomains are set up out of the box.",
      },
      openSource: {
        title: "Open source and self-hosted",
        description:
          "OpenSpawner is MIT-licensed and runs on your own infrastructure. Your data and your users stay with you.",
      },
    },
  },

  cta: {
    heading: "Ready for your first environment?",
    body: "The complete source code is on GitHub. Clone the repository, adjust the .env, and start it with Docker Compose. Your first instance is running within a few minutes.",
    button: "Go to the repository on GitHub",
  },

  footer: {
    tagline:
      "Isolated Docker containers for every user, self-hosted and open source.",
    project: "Project",
    legal: "Legal",
    imprint: "Imprint",
    license: "MIT License",
  },

  theme: {
    toggle: "Toggle theme",
    light: "Light",
    dark: "Dark",
    system: "System",
  },
};

export const dictionaries: Record<Locale, Dictionary> = { de, en };

export function getDictionary(locale: Locale): Dictionary {
  return dictionaries[locale];
}
