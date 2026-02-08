# Rallly User-Template Integration (Single-Container mit SQLite)

## Übersicht

**Ziel:** Rallly als neues User-Template hinzufügen, kompatibel mit dem aktuellen Single-Container-System.

**Ansatz:** Rallly-Container mit SQLite-Datenbank (statt PostgreSQL aus dem Original-Compose-File).

**Use-Case:**
1. **Angemeldeter Spawner-User** erstellt Rallly-Container
2. **Spawner-User richtet Rallly ein** (wird Rallly-Admin beim ersten Setup)
3. **Öffentlicher Zugriff** - jeder mit URL kann Rallly nutzen (OHNE Spawner-Login)
4. **Rallly-eigene Authentifizierung** - Rallly hat eigenes User-Management

**Vorteile:**
- ✅ Keine Architektur-Änderungen am Spawner-System
- ✅ Passt ins bestehende Template-System
- ✅ Automatisches Build via `install.sh`
- ✅ Traefik-Routing funktioniert sofort (öffentlich zugänglich)
- ✅ Keine Service-Dependencies
- ✅ Rallly verwaltet eigene Benutzer

---

## Zugriffs-Model & Authentifizierung

### Wie funktioniert der öffentliche Zugriff?

**Container-URL-Format:**
```
https://coder.domain.com/{user-slug}-template-rallly
```

**Zugriffskontrolle:**

1. **Spawner-Ebene (Container erstellen):**
   - ✅ Nur angemeldete Spawner-User können Container erstellen
   - ✅ User muss JWT-Token haben

2. **Traefik-Routing (Container aufrufen):**
   - ✅ **KEINE Authentifizierung** - öffentlich zugänglich
   - ✅ Jeder mit URL kann zugreifen
   - ✅ Traefik routet direkt zum Container

3. **Rallly-Ebene (App-Nutzung):**
   - ✅ **Rallly-eigene Authentifizierung** (optional)
   - ✅ Spawner-User wird beim ersten Setup zu Rallly-Admin
   - ✅ Rallly kann öffentlich oder mit Passwort genutzt werden

### Rallly Setup-Flow

**Beim ersten Container-Start:**

1. User öffnet: `https://coder.domain.com/{slug}-template-rallly`
2. Rallly zeigt **Setup-Wizard**:
   - Admin-Account erstellen (Spawner-User Email)
   - Passwort setzen
   - Optionale Einstellungen

3. **Nach Setup:**
   - Rallly-Admin kann Events erstellen
   - Events können öffentlich geteilt werden (URL)
   - Teilnehmer brauchen KEINEN Rallly-Account (je nach Settings)

### Environment-Variablen für öffentlichen Zugriff

**Im Dockerfile setzen:**

```bash
# Öffentlicher Zugriff erlauben (keine Registrierung erforderlich für Teilnehmer)
ENV NEXT_PUBLIC_ENABLE_SELF_REGISTRATION=false

# Base URL für Rallly (für Link-Generierung)
ENV NEXT_PUBLIC_BASE_URL="https://coder.domain.com/{slug}-template-rallly"

# Session-Secret (wird pro Container generiert)
ENV SECRET_PASSWORD=$(openssl rand -base64 32)
```

**Wichtig:** Der Spawner-User richtet Rallly nur EINMAL ein. Danach ist Rallly unabhängig nutzbar.

---

## Phase 1: Rallly Dockerfile erstellen

### Dateien erstellen

**Verzeichnis:** `user-template-rallly/`

#### 1.1 Dockerfile

**Datei:** `C:\Users\Micro\OneDrive\Dokumente\spawner\user-template-rallly\Dockerfile`

```dockerfile
FROM lukevella/rallly:latest

# Setze Environment für SQLite (statt PostgreSQL)
ENV DATABASE_URL="file:/data/rallly.db"

# Session-Secret generieren (wird pro Build neu generiert)
# In Production sollte das pro Container-Instance individuell sein
ENV SECRET_PASSWORD="change-this-in-production"

# Öffentlicher Zugriff: Teilnehmer brauchen keinen Account
ENV NEXT_PUBLIC_ENABLE_SELF_REGISTRATION=false

# Support Email (optional, für Rallly-Footer)
ENV SUPPORT_EMAIL=""

# Erstelle Datenverzeichnis
RUN mkdir -p /data && chown -R node:node /data

# Volume für SQLite-Datenbank
VOLUME ["/data"]

# Port 3000 (Standard Rallly)
EXPOSE 3000

# Start Command (nutzt Original-Entrypoint)
CMD ["npm", "start"]
```

**Wichtige Environment-Variablen:**

| Variable | Wert | Beschreibung |
|----------|------|--------------|
| `DATABASE_URL` | `file:/data/rallly.db` | SQLite-Datenbank statt PostgreSQL |
| `SECRET_PASSWORD` | Auto-generiert | Session-Verschlüsselung (sollte pro Container unique sein) |
| `NEXT_PUBLIC_ENABLE_SELF_REGISTRATION` | `false` | Nur Admin kann Accounts erstellen (Event-Teilnehmer brauchen keinen Account) |
| `SUPPORT_EMAIL` | leer | Optional: Support-Email im Footer |

**Hinweis SECRET_PASSWORD:**
Idealerweise sollte `SECRET_PASSWORD` pro Container unique sein. Das kann später in `container_manager.py` beim Spawn injiziert werden:

```python
# In container_manager.py (optional)
import secrets
environment = {
    'SECRET_PASSWORD': secrets.token_urlsafe(32)
}
```

**Hinweise:**
- Rallly unterstützt SQLite nativ (Prisma ORM)
- `DATABASE_URL="file:/data/rallly.db"` aktiviert SQLite
- Volume `/data` persistiert Daten
- Port 3000 wird von Traefik geroutet

#### 1.2 .dockerignore (optional)

**Datei:** `C:\Users\Micro\OneDrive\Dokumente\spawner\user-template-rallly\.dockerignore`

```
node_modules
.git
.env
*.log
```

---

## Phase 2: Template-Konfiguration

### 2.1 templates.json erweitern

**Datei:** `C:\Users\Micro\OneDrive\Dokumente\spawner\templates.json`

**Änderung:** Füge neuen Eintrag hinzu:

```json
{
  "templates": [
    {
      "type": "template-01",
      "image": "user-template-01:latest",
      "display_name": "Nginx Basic",
      "description": "Einfacher Nginx-Server mit statischen Dateien"
    },
    {
      "type": "template-02",
      "image": "user-template-02:latest",
      "display_name": "Nginx Advanced",
      "description": "Erweiterter Nginx-Server mit Custom-Config"
    },
    {
      "type": "template-next",
      "image": "user-template-next:latest",
      "display_name": "Next.js App",
      "description": "Next.js Production Build mit Shadcn UI"
    },
    {
      "type": "template-rallly",
      "image": "user-template-rallly:latest",
      "display_name": "Rallly Scheduler",
      "description": "Termin-Abstimmung und Planung mit Rallly"
    }
  ]
}
```

### 2.2 .env aktualisieren

**Datei:** `C:\Users\Micro\OneDrive\Dokumente\spawner\.env`

**Änderung:** Erweitere `USER_TEMPLATE_IMAGES`:

```bash
# ALT:
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-02:latest;user-template-next:latest"

# NEU:
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-02:latest;user-template-next:latest;user-template-rallly:latest"
```

**Wichtig:** Semikolon-getrennte Liste ohne Leerzeichen!

### 2.3 .env.example aktualisieren (Dokumentation)

**Datei:** `C:\Users\Micro\OneDrive\Dokumente\spawner\.env.example`

**Änderung:** Gleiche Anpassung wie in `.env`:

```bash
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-02:latest;user-template-next:latest;user-template-rallly:latest"
```

---

## Phase 3: Image bauen

### 3.1 Automatischer Build mit install.sh

Das `install.sh` Script erkennt automatisch neue Templates aus `USER_TEMPLATE_IMAGES`.

**Kommando (lokal testen):**

```bash
cd C:\Users\Micro\OneDrive\Dokumente\spawner

# Build nur Rallly-Template
docker build -t user-template-rallly:latest ./user-template-rallly

# ODER: Alle Templates neu bauen
bash install.sh
```

**Was install.sh macht:**
1. Liest `USER_TEMPLATE_IMAGES` aus `.env`
2. Extrahiert Template-Namen (z.B. `user-template-rallly`)
3. Baut Docker Image: `docker build -t user-template-rallly:latest ./user-template-rallly`
4. Zeigt Warnings wenn Verzeichnis fehlt

### 3.2 Verification nach Build

```bash
# Image prüfen
docker images | grep rallly
# Sollte zeigen: user-template-rallly:latest

# Container-Test (optional)
docker run -d --name test-rallly -p 3000:3000 user-template-rallly:latest
docker logs -f test-rallly

# Öffne Browser: http://localhost:3000
# Sollte: Rallly-Setup-Page zeigen

# Cleanup
docker stop test-rallly && docker rm test-rallly
```

---

## Phase 4: Spawner-System Deployment

### 4.1 Code committen

**Neue Dateien:**
- `user-template-rallly/Dockerfile`
- `user-template-rallly/.dockerignore` (optional)

**Geänderte Dateien:**
- `templates.json`
- `.env` (Server)
- `.env.example` (Dokumentation)

**Commit:**

```bash
cd C:\Users\Micro\OneDrive\Dokumente\spawner

git add user-template-rallly/ templates.json .env.example
git commit -m "feat: Add Rallly user-template with SQLite

- Rallly Scheduler als neues User-Template
- Single-Container mit SQLite-Datenbank (statt PostgreSQL)
- Volume /data für Datenpersistenz
- Port 3000 exponiert für Traefik-Routing
- Templates.json und .env.example aktualisiert"

git push origin main
```

### 4.2 Server Deployment

**Auf dem Synology NAS / Server:**

```bash
cd /volume1/docker/spawner

# Code pullen
git pull origin main

# .env aktualisieren (USER_TEMPLATE_IMAGES erweitern)
nano .env
# Füge hinzu: ;user-template-rallly:latest

# install.sh ausführen (baut neue Templates)
bash install.sh

# Spawner neu starten (lädt neue templates.json)
docker-compose up -d --build spawner
```

**Wichtig:** `install.sh` baut automatisch alle Templates aus `USER_TEMPLATE_IMAGES`.

---

## Phase 5: Testing & Verification

### 5.1 Frontend-Check

1. **Admin-Dashboard öffnen:** `https://coder.domain.com/admin`
2. **Prüfe:** Wird "Rallly Scheduler" als Template angezeigt?
   - Falls nicht: Server-Logs prüfen (`docker logs spawner`)

### 5.2 User-Dashboard Test

1. **User-Dashboard öffnen:** `https://coder.domain.com/dashboard`
2. **Container-Grid prüfen:**
   - Sollte "Rallly Scheduler" als Option zeigen
   - Description: "Termin-Abstimmung und Planung mit Rallly"

### 5.3 Container Launch

1. **Klicke:** "Erstellen & Öffnen" bei Rallly
2. **Erwartetes Verhalten:**
   - Container wird erstellt (`user-{slug}-template-rallly-{id}`)
   - Traefik-Route wird konfiguriert
   - Browser öffnet: `https://coder.domain.com/{slug}-template-rallly`

### 5.4 Rallly Setup (Spawner-User als Admin)

**Erster Besuch (als Spawner-User):**

1. Öffne: `https://coder.domain.com/{slug}-template-rallly`
2. Rallly zeigt **Setup-Wizard**
3. Erstelle Admin-Account:
   - Email: Spawner-User Email
   - Name: Spawner-User Name
   - Passwort: Wählen
4. Setup abschließen
5. SQLite-Datenbank wird erstellt: `/data/rallly.db`

**Rallly ist jetzt eingerichtet!**

### 5.5 Öffentlichen Zugriff testen

**Test 1: Event erstellen (als Admin)**

1. Login als Rallly-Admin
2. Erstelle neues Event: "Team Meeting"
3. Event-URL wird generiert: `https://coder.domain.com/{slug}-template-rallly/p/{event-id}`
4. Kopiere URL

**Test 2: Event öffnen (öffentlich, OHNE Login)**

1. **Öffne Incognito/Private Browser** (kein Spawner-Login!)
2. Navigiere zu Event-URL: `https://coder.domain.com/{slug}-template-rallly/p/{event-id}`
3. **Erwartetes Verhalten:**
   - ✅ Event wird angezeigt
   - ✅ KEIN Spawner-Login erforderlich
   - ✅ KEIN Rallly-Login erforderlich
   - ✅ Teilnehmer kann Name eingeben und abstimmen

**Test 3: Öffentliche Nutzung ohne Spawner-Account**

1. Teile Event-URL mit jemandem der KEINEN Spawner-Account hat
2. Person öffnet URL
3. **Erwartetes Verhalten:**
   - ✅ Event ist zugänglich
   - ✅ Teilnahme möglich
   - ✅ Kein Spawner-Redirect

**Daten-Persistenz prüfen:**

```bash
# Container stoppen
docker stop user-{slug}-template-rallly-{id}

# Container neu starten
docker start user-{slug}-template-rallly-{id}

# Sollte: Daten sind noch da (SQLite Volume)
# - Admin-Account vorhanden
# - Events vorhanden
# - Teilnehmer-Antworten erhalten
```

### 5.5 Logs prüfen

```bash
# Rallly-Container-Logs
docker logs user-{slug}-template-rallly-{id}

# Sollte zeigen:
# - Prisma Migration erfolgreich
# - Server listening on port 3000
# - Keine Fehler

# Spawner-Logs
docker logs spawner | grep rallly

# Sollte zeigen:
# - Container erfolgreich erstellt
# - Traefik-Labels gesetzt
```

---

## Kritische Dateien

| Datei | Status | Beschreibung |
|-------|--------|--------------|
| `user-template-rallly/Dockerfile` | ✅ NEU | Rallly mit SQLite-Config |
| `user-template-rallly/.dockerignore` | ⚠️ OPTIONAL | Build-Optimierung |
| `templates.json` | ✏️ ÄNDERN | Rallly-Template-Metadaten |
| `.env` | ✏️ ÄNDERN (Server) | USER_TEMPLATE_IMAGES erweitern |
| `.env.example` | ✏️ ÄNDERN | Dokumentation |

---

## Häufige Probleme & Lösungen

### Problem 1: Template erscheint nicht im Dashboard

**Symptom:** Rallly wird nicht in Container-Grid angezeigt.

**Lösung:**

```bash
# 1. Prüfe templates.json
cat templates.json | grep rallly
# Sollte Eintrag zeigen

# 2. Prüfe Config-Laden
docker logs spawner | grep "CONTAINER_TEMPLATES"

# 3. Spawner neu starten
docker-compose restart spawner
```

### Problem 2: Container startet nicht

**Symptom:** "Container konnte nicht erstellt werden" Error.

**Lösung:**

```bash
# 1. Image prüfen
docker images | grep rallly
# Sollte: user-template-rallly:latest

# 2. Manueller Container-Test
docker run -d --name test-rallly \
  -e DATABASE_URL="file:/data/rallly.db" \
  -p 3000:3000 \
  user-template-rallly:latest

docker logs test-rallly
# Sollte: Keine Fehler

# 3. Traefik-Netzwerk prüfen
docker network ls | grep web
# Sollte existieren
```

### Problem 3: SQLite-Daten gehen verloren

**Symptom:** Nach Container-Restart sind Daten weg.

**Ursache:** Volume nicht korrekt gemountet.

**Lösung:**

```bash
# Prüfe Volume
docker inspect user-{slug}-template-rallly-{id} | grep -A10 "Mounts"

# Sollte zeigen:
# - Source: /var/lib/docker/volumes/...
# - Destination: /data

# Falls nicht: container_manager.py anpassen
# Füge Volume-Mount hinzu in spawn_multi_container()
```

**Fix in container_manager.py (falls nötig):**

```python
# Zeile ~200 in spawn_multi_container()
volumes = {
    f'rallly-data-{user_id}': {'bind': '/data', 'mode': 'rw'}
}

container = self._get_client().containers.run(
    image=image,
    volumes=volumes,  # NEU
    # ... rest of config
)
```

### Problem 4: Port-Konflikt mit anderem Service

**Symptom:** Container startet aber ist nicht erreichbar.

**Lösung:**

```bash
# Prüfe Traefik-Labels
docker inspect user-{slug}-template-rallly-{id} | grep -A20 "Labels"

# Sollte zeigen:
# - traefik.http.routers.user{id}.rule = Host(...) && PathPrefix(...)
# - traefik.http.services.user{id}.loadbalancer.server.port = 3000

# Falls Port falsch: container_manager.py nutzt Port 8080 als Default
# Rallly braucht Port 3000
```

**Fix (falls Port nicht 3000):**

Rallly-Dockerfile anpassen:

```dockerfile
# Am Ende des Dockerfile:
EXPOSE 3000

# ODER: Traefik-Port explizit setzen
ENV TRAEFIK_PORT=3000
```

---

## Alternativen (falls SQLite nicht ausreicht)

### Option A: Shared PostgreSQL (später)

Falls SQLite Performance-Probleme hat:

1. Erstelle einen zentralen PostgreSQL-Container
2. Jeder User bekommt eigene Database + Credentials
3. Rallly-Container bekommt `DATABASE_URL` per Environment

**Aufwand:** ~2-3 Stunden
**Vorteil:** Bessere Performance, Multi-User-Ready

### Option B: Externe PostgreSQL-Anbindung

Falls bereits PostgreSQL-Server existiert:

1. Rallly-Dockerfile: Entferne SQLite-Config
2. `DATABASE_URL` per Environment injizieren
3. Credentials per User generieren

**Aufwand:** ~1 Stunde
**Vorteil:** Professionelle DB-Infrastruktur

---

## Zusammenfassung

**Was implementiert wird:**
1. ✅ Neues User-Template: `user-template-rallly`
2. ✅ Rallly mit SQLite-Datenbank (Single-Container)
3. ✅ Automatisches Build via `install.sh`
4. ✅ Integration ins Dashboard (templates.json)
5. ✅ Traefik-Routing (Port 3000)

**Keine Breaking Changes:**
- ✅ Bestehende Templates unverändert
- ✅ Keine Architektur-Änderungen
- ✅ Keine DB-Migration erforderlich

**Geschätzter Aufwand:**
- Dockerfile erstellen: 10 Minuten
- Templates.json + .env: 5 Minuten
- Build + Test: 15 Minuten
- Deployment: 10 Minuten
- **Total: ~40 Minuten**

**Nächste Schritte nach Approval:**
1. Erstelle `user-template-rallly/Dockerfile`
2. Aktualisiere `templates.json` und `.env.example`
3. Build Image mit `install.sh`
4. Test Container lokal
5. Commit + Push
6. Server-Deployment

---

## Traefik-Routing & Öffentlicher Zugriff

### Wie Traefik das Routing handhabt

**Aktuelles System (container_manager.py):**

```python
# Traefik-Labels beim Container-Spawn
labels = {
    'traefik.enable': 'true',
    f'traefik.http.routers.user{user_id}.rule': f'Host(`{spawner_domain}`) && PathPrefix(`/{slug_with_suffix}`)',
    f'traefik.http.routers.user{user_id}.entrypoints': Config.TRAEFIK_ENTRYPOINT,
    f'traefik.http.services.user{user_id}.loadbalancer.server.port': '3000',  # Rallly-Port
    # WICHTIG: Kein Traefik-Auth-Middleware!
}
```

**Routing-Flow:**

1. Request: `https://coder.domain.com/{slug}-template-rallly/p/{event-id}`
2. Traefik prüft: Host + PathPrefix Match?
3. ✅ Route zu Container (Port 3000)
4. ✅ **KEINE Authentifizierung** auf Traefik-Ebene
5. Container beantwortet Request

**Wichtig:** Das Spawner-System hat **keine JWT-Auth für Container-Zugriffe**. Nur für API-Endpoints!

### Unterschied: API vs. Container

| Endpoint | Auth erforderlich? | Beschreibung |
|----------|-------------------|--------------|
| `/api/user/containers` | ✅ JWT Token | Spawner API - Container-Liste abrufen |
| `/api/container/launch` | ✅ JWT Token | Spawner API - Container erstellen |
| `/{slug}-template-rallly/*` | ❌ KEINE Auth | User-Container - öffentlich via Traefik |

### Sicherheits-Überlegungen

**Gut für Rallly:**
- ✅ Events sollen öffentlich teilbar sein
- ✅ Teilnehmer brauchen keinen Spawner-Account
- ✅ Rallly hat eigene Admin-Authentifizierung

**Potentielle Bedenken:**
- ⚠️ Jeder mit URL kann Container nutzen (aber das ist gewollt!)
- ⚠️ Rate-Limiting nur via Traefik (nicht per User)
- ⚠️ Rallly-Admin sollte starkes Passwort setzen

**Empfohlene Rallly-Settings (für Admin):**
- Admin-Passwort: Stark & unique
- Self-Registration: Disabled (nur Admin erstellt Events)
- Event-Visibility: Optional private Events

---

## Verification Checklist

### Setup & Deployment
- [ ] `user-template-rallly/Dockerfile` erstellt
- [ ] `templates.json` erweitert (type: template-rallly)
- [ ] `.env.example` aktualisiert
- [ ] Image gebaut (`docker images | grep rallly`)
- [ ] Lokaler Container-Test erfolgreich
- [ ] Code committed & pushed
- [ ] Server `.env` aktualisiert
- [ ] `install.sh` auf Server ausgeführt
- [ ] Spawner neu gestartet

### Funktionalität
- [ ] Dashboard zeigt "Rallly Scheduler"
- [ ] Container launch erfolgreich
- [ ] Rallly erreichbar unter User-URL
- [ ] Setup-Wizard erscheint beim ersten Start
- [ ] Admin-Account erstellt (Spawner-User)
- [ ] SQLite-Daten persistiert nach Restart

### Öffentlicher Zugriff (WICHTIG!)
- [ ] Event erstellt als Rallly-Admin
- [ ] Event-URL generiert
- [ ] **Incognito-Browser:** Event ohne Spawner-Login erreichbar
- [ ] **Incognito-Browser:** Teilnahme ohne Rallly-Account möglich
- [ ] Person OHNE Spawner-Account kann Event öffnen
- [ ] Traefik routet korrekt (keine 401/403 Errors)
- [ ] Teilnehmer-Antworten werden gespeichert
