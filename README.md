# Container Spawner

Ein Flask-basierter Service zur automatischen Bereitstellung von isolierten Docker-Containern pro Benutzer mit Traefik-Integration. Benutzer registrieren sich, erhalten einen eigenen Container und eine personalisierte Subdomain.

## Features

- **User-Management**: Registrierung und Login mit sicherer Passwort-Speicherung
- **Automatisches Container-Spawning**: Jeder User erhaelt einen eigenen Docker-Container
- **Dynamisches Routing**: Traefik routet automatisch zu den User-Containern via Subdomain
- **Resource-Management**: CPU- und RAM-Limits pro Container
- **Lifecycle-Management**: Starten, Stoppen und Neustarten von User-Containern
- **Template-basiert**: Neue User-Container aus vorgefertigten Images

## Schnellstart

```bash
# Installation mit einem Befehl
curl -sSL https://gitea.iotxs.de/RainerWieland/spawner/raw/branch/main/install.sh | bash
```

Nach der Installation `.env` anpassen und erneut ausfuehren:

```bash
cp .env.example .env
nano .env  # Werte anpassen
bash install.sh
```

## Voraussetzungen

- Docker 20.10+
- Docker Compose 2.0+
- Traefik 2.x oder 3.x (laufend)
- Bestehendes Docker-Netzwerk fuer Traefik

## Dokumentation

| Dokument | Beschreibung |
|----------|--------------|
| [Installation](docs/install/README.md) | Installationsanleitung und Updates |
| [Architektur](docs/architecture/README.md) | Technische Architektur und Komponenten |
| [Sicherheit](docs/security/README.md) | Sicherheitsrisiken und Massnahmen |
| [Versionen](docs/versions/README.md) | Changelog und Versionierung |
| [Bekannte Bugs](docs/bugs/README.md) | Bekannte Probleme und Workarounds |
| [Best Practices](docs/dos-n-donts/README.md) | Dos and Don'ts |

## Projektstruktur

```
spawner/
├── app.py                 # Flask-Hauptanwendung
├── auth.py                # Authentifizierungs-Blueprint
├── container_manager.py   # Docker-Container-Management
├── models.py              # SQLAlchemy User-Modell
├── config.py              # Konfigurationsklassen
├── templates/             # Jinja2-Templates (Legacy)
├── frontend/              # Next.js Frontend
├── user-template/         # Docker-Template fuer User-Container
└── docs/                  # Dokumentation
```

## Konfiguration

Alle Einstellungen erfolgen ueber Umgebungsvariablen in `.env`:

| Variable | Beschreibung |
|----------|--------------|
| `SECRET_KEY` | Flask Session Secret (generieren!) |
| `BASE_DOMAIN` | Haupt-Domain (z.B. example.com) |
| `SPAWNER_SUBDOMAIN` | Subdomain fuer Spawner-UI |
| `TRAEFIK_NETWORK` | Docker-Netzwerk fuer Traefik |
| `USER_TEMPLATE_IMAGE` | Docker-Image fuer User-Container |

Siehe [.env.example](.env.example) fuer alle Optionen.

## Lizenz

MIT License - siehe Dokumentation fuer Details.

---

**Version**: 0.1.0
**Repository**: https://gitea.iotxs.de/RainerWieland/spawner
