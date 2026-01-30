# Changelog

Alle nennenswerten Aenderungen werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [Unreleased]

### Hinzugefuegt
- Dokumentationsstruktur mit mehreren Kategorien
- Automatisches Installationsskript (`install.sh`)
- `.env.example` Vorlage

### Geaendert
- `doc/` Verzeichnis umbenannt zu `docs/`
- README.md ueberarbeitet mit Schnellstart-Anleitung

---

## [0.2.0] - 2026-01-31

### Hinzugefuegt
- Synology NAS / BusyBox Kompatibilitaet im Installationsskript
- Automatische Docker-Version Pruefung (>= 20.10)
- Automatische Docker Compose Version Pruefung (>= 2.0)
- Traefik-Laufzeit-Pruefung im Installationsskript
- Traefik-Netzwerk-Verbindungspruefung
- Build-Fortschrittsanzeige mit gefilterten Logs
- Automatische `git safe.directory` Konfiguration fuer NAS-Umgebungen

### Geaendert
- `auth.py`: Redirect zum Frontend statt Jinja2-Templates
- `docker-compose.yml`: Legacy-Router entfernt (verhindert Redirect-Loop)
- Dockerfiles: Fallback auf `npm install` wenn `package-lock.json` fehlt
- `--progress=plain` Flag entfernt (nicht kompatibel mit aelteren Docker-Versionen)
- Build-Verifikation prueft jetzt Exit-Code UND Image-Existenz

### Behoben
- Redirect-Loop bei `/login` und `/signup` behoben
- `@/lib/utils` Module-Not-Found Fehler in Next.js Projekten
- `.gitignore` blockierte `frontend/src/lib/` und `user-template-next/src/lib/`
- `tsconfig.json` fehlte `baseUrl` fuer TypeScript Path Aliases
- Docker Build meldete faelschlicherweise "OK" bei Fehlern

### Entfernt
- `templates/` Verzeichnis (alte Jinja2 Templates, ersetzt durch Next.js Frontend)

### Sicherheit
- Keine sensiblen Dateien (`.env`, `CLAUDE.md`) werden ins Repository kopiert

---

## [0.1.0] - 2026-01-30

### Hinzugefuegt
- Flask-Anwendung mit User-Management
- Docker-Container-Spawning pro User
- Traefik-Integration via Labels
- SQLite-Datenbank fuer User-Daten
- Next.js Frontend
- REST-API fuer Container-Management
- User-Template (nginx-basiert)
- Health-Check Endpoint
- Docker-Compose Setup

### Sicherheit
- Passwort-Hashing mit Werkzeug
- Session-Cookies mit HttpOnly/Secure
- Resource-Limits fuer Container

---

## [0.0.1] - 2026-01-27

### Hinzugefuegt
- Initiales Projekt-Setup
- Grundlegende Dokumentation

---

## Legende

- **Hinzugefuegt**: Neue Features
- **Geaendert**: Aenderungen an bestehenden Features
- **Veraltet**: Features die bald entfernt werden
- **Entfernt**: Entfernte Features
- **Behoben**: Bugfixes
- **Sicherheit**: Sicherheitsrelevante Aenderungen

---

[Unreleased]: https://gitea.iotxs.de/RainerWieland/spawner/compare/v0.1.0...HEAD
[0.1.0]: https://gitea.iotxs.de/RainerWieland/spawner/releases/tag/v0.1.0
[0.0.1]: https://gitea.iotxs.de/RainerWieland/spawner/releases/tag/v0.0.1
