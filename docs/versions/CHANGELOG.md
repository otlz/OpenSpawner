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

## [0.3.0] - 2026-01-31

### Hinzugefuegt
- **Admin-Dashboard**: Vollstaendige Benutzerverwaltung fuer Admins
  - Benutzer sperren/entsperren
  - Passwoerter zuruecksetzen (sendet Email)
  - Benutzer-Container loeschen
  - Benutzer loeschen
  - Verifizierungs-Emails erneut senden
- **Email-Verifizierung**: Neue Benutzer muessen Email bestaetigen
  - Verifizierungs-Email bei Registrierung
  - OneTimeToken-basierte Verifizierung
  - verify-success und verify-error Seiten
- **Erster User wird Admin**: Der erste registrierte Benutzer erhaelt Admin-Rechte
- **Benutzer-States**: registered → verified → active
- **Aktivitaetstracking**: `last_used` Feld fuer letzten Container-Zugriff
- **Farbcodierte Benutzerliste** im Admin-Dashboard:
  - Gruen: Aktiv, kuerzlich genutzt
  - Gelb: Warnung (unverifiziert/inaktiv)
  - Rot: Kritisch (lange unverifiziert/sehr lange inaktiv)
- **SMTP-Konfiguration**: Email-Versand fuer Verifizierung und Passwort-Reset
- **Admin-API Endpoints**:
  - `GET /api/admin/users` - Alle Benutzer auflisten
  - `POST /api/admin/users/{id}/block` - Benutzer sperren
  - `POST /api/admin/users/{id}/unblock` - Benutzer entsperren
  - `POST /api/admin/users/{id}/reset-password` - Passwort zuruecksetzen
  - `POST /api/admin/users/{id}/resend-verification` - Verifizierungs-Email senden
  - `DELETE /api/admin/users/{id}/container` - Container loeschen
  - `DELETE /api/admin/users/{id}` - Benutzer loeschen
  - `POST /api/admin/users/{id}/takeover` - Container-Zugriff (Dummy, Phase 2)
- **Neue Backend-Dateien**:
  - `admin_api.py` - Admin-Blueprint mit Endpoints
  - `decorators.py` - @admin_required und @verified_required Decorator
  - `email_service.py` - Email-Versand-Service
- **Neue Frontend-Seiten**:
  - `/admin` - Admin-Dashboard
  - `/verify-success` - Email-Verifizierung erfolgreich
  - `/verify-error` - Email-Verifizierung fehlgeschlagen

### Geaendert
- `models.py`: Neue Felder (is_admin, is_blocked, state, last_used, verification_token), UserState Enum, AdminTakeoverSession Model
- `config.py`: SMTP-Konfiguration, FRONTEND_URL
- `api.py`: Signup sendet Verifizierungs-Email (kein Auto-Login mehr), Login prueft Blockade und Verifizierung
- `app.py`: Admin-Blueprint registriert
- `.env.example`: SMTP-Variablen hinzugefuegt
- Frontend `api.ts`: Admin-API-Funktionen
- Frontend `use-auth.tsx`: User-Interface mit is_admin und state
- Frontend `signup/page.tsx`: Zeigt Verifizierungs-Hinweise nach Registrierung
- Frontend `login/page.tsx`: Option zum erneuten Senden der Verifizierungs-Email
- Frontend `dashboard/page.tsx`: Admin-Link fuer Admins

### Sicherheit
- Blockierte Benutzer koennen sich nicht mehr anmelden
- Unverifizierte Benutzer koennen sich nicht anmelden
- Admins koennen sich nicht selbst sperren oder loeschen
- Admins koennen andere Admins nicht loeschen
- Verification-Token ist einmalig verwendbar (OneTimeToken)

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
