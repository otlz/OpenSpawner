# OpenSpawner

Flask + Next.js Anwendung, die automatisch isolierte Docker-Container pro Benutzer bereitstellt. Jeder Benutzer bekommt eigene Container mit personalisierter URL, verwaltet über ein Web-Dashboard.

## Was macht OpenSpawner?

- Benutzer registrieren sich per Magic Link (passwortlos, kein Passwort nötig)
- Jeder Benutzer kann Docker-Container aus fertigen Templates starten
- Container sind automatisch per Web erreichbar
- Admins verwalten Benutzer und Container über ein Dashboard

## Schnellstart (Docker Desktop)

Funktioniert auf **Windows** und **Linux** gleich — Docker Desktop muss installiert sein.

```bash
git clone https://github.com/otlz/OpenSpawner.git
cd OpenSpawner
cp .env.example .env
docker compose --profile build build   # Template-Images bauen
docker compose up --build              # Anwendung starten
```

Dann öffnen: [http://localhost:3000](http://localhost:3000)

> **Wichtig:** Der erste registrierte Benutzer wird automatisch Admin.

> **Ohne E-Mail-Server:** Magic Links erscheinen in den Backend-Logs:
> ```bash
> docker compose logs spawner
> ```

## Architektur

```
Browser
  |
  +---> Frontend (Next.js)     :3000
  |       |
  |       +---> /api/* Proxy
  |               |
  +---> Backend (Flask API)    :5000
          |
          +---> Docker Engine
                  |
                  +---> User Container A
                  +---> User Container B
                  +---> ...
```

**Tech-Stack:**

| Komponente | Technologie |
|------------|-------------|
| Backend | Flask, SQLAlchemy, JWT Auth, Docker SDK |
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Radix UI |
| Datenbank | SQLite (Standard) |
| Auth | Passwortlose Magic Links + JWT Tokens |

## Konfiguration

Alle Einstellungen in `.env` (Vorlage: `.env.example`). Die wichtigsten:

| Variable | Standard | Beschreibung |
|----------|----------|-------------|
| `SECRET_KEY` | `dev-secret-...` | Flask Secret Key (in Produktion ändern!) |
| `BASE_DOMAIN` | `localhost` | Domain |
| `TRAEFIK_ENABLED` | `false` | Traefik Reverse Proxy aktivieren |
| `USER_TEMPLATE_IMAGES` | alle Templates | Semikolon-getrennte Liste der Templates |
| `DEFAULT_MEMORY_LIMIT` | `512m` | RAM-Limit pro Container |
| `DEFAULT_CPU_QUOTA` | `50000` | CPU-Limit (50000 = 0.5 CPU) |

Alle Optionen sind in [.env.example](.env.example) dokumentiert.

## Templates

OpenSpawner kommt mit fertigen Container-Templates:

| Template | Beschreibung |
|----------|-------------|
| `user-template-01` | Nginx Basic — einfache statische Seite |
| `user-template-02` | Nginx Advanced |
| `user-template-next` | Next.js React-Anwendung |
| `user-template-dictionary` | Python Flask Dictionary App |
| `user-template-vcoder` | Web IDE mit PlatformIO für ESP8266 |

### Eigenes Template erstellen

1. Verzeichnis `templates/user-template-xyz/` mit `Dockerfile` anlegen (muss Port **8080** exposen)
2. In `.env` zu `USER_TEMPLATE_IMAGES` hinzufügen
3. Metadaten in `templates.json` eintragen
4. Bauen: `docker compose --profile build build`

## Produktion (mit Traefik)

Für Produktion mit HTTPS und Domain-Routing:

```bash
# In .env anpassen:
BASE_DOMAIN=deine-domain.de
SPAWNER_SUBDOMAIN=coder
TRAEFIK_ENABLED=true
TRAEFIK_NETWORK=web
TRAEFIK_CERTRESOLVER=lets-encrypt
TRAEFIK_ENTRYPOINT=websecure
```

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Voraussetzung: Ein laufender [Traefik](https://traefik.io/) Reverse Proxy mit Docker Provider.

## API-Dokumentation

Swagger UI ist verfügbar unter [http://localhost:5000/swagger](http://localhost:5000/swagger).

## Autoren

- **Rainer Wieland** — Karl Kübel Schule Bensheim
- **Navin Dass** — Karl Kübel Schule Bensheim

## Lizenz

MIT — siehe [LICENSE](LICENSE)
