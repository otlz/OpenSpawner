# Container Spawner - Deployment Guide

## 🎯 Überblick

Das System unterstützt **beliebig viele User-Templates** über ein dynamisches Konfigurationssystem:
- Templates werden in `.env` definiert (semikolon-getrennt)
- Metadaten (Namen, Beschreibungen) kommen aus `templates.json`
- `install.sh` baut **nur** die in `.env` unter `USER_TEMPLATE_IMAGES` definierten Templates
- Jeder Benutzer kann beliebig viele Container verschiedener Typen erstellen

**Standardtemplates (können beliebig erweitert werden):**
- **template-01**: Nginx Basic - Einfacher Nginx-Server mit statischen Dateien
- **template-02**: Nginx Advanced - Nginx mit erweiterten Features
- **template-next**: Next.js Production - React-App mit Shadcn/UI

---

## 📋 Voraussetzungen

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (für Frontend)
- Traefik als Reverse Proxy mit Docker Provider

---

## 🚀 Deployment-Anleitung

### Phase 1: Vorbereitung (15 Minuten)

#### 1.1 Code auschecken
```bash
git pull origin main
```

#### 1.2 Alte Daten bereinigen (CLEAN SLATE)
```bash
# Alle alten User-Container stoppen
docker ps -a | grep "user-" | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# Alte Datenbank löschen
rm -f spawner.db

# Logs löschen
rm -rf logs/*
```

#### 1.3 Templates konfigurieren (ZUERST!)
```bash
# Überprüfung der verfügbaren Template-Verzeichnisse:
ls -d user-template*

# Expected output:
# user-template-01  user-template-02  user-template-next

# WICHTIG: .env MUSS zuerst konfiguriert werden!
# install.sh baut NUR die in USER_TEMPLATE_IMAGES definierten Templates
```

**WICHTIG:**
- Das `install.sh`-Script baut **nur** die in `.env` → `USER_TEMPLATE_IMAGES` definierten Templates
- **Ohne `.env`-Eintrag werden Templates NICHT gebaut!**
- Daher: `.env` konfigurieren BEVOR `install.sh` ausführen!

#### 1.4 Environment konfigurieren
```bash
# Copy beispiel Datei
cp .env.example .env

# Bearbeite .env und passe an:
nano .env
```

**Erforderliche Änderungen in .env:**
```bash
# Pflichtfelder
SECRET_KEY=<generiert mit: python3 -c "import secrets; print(secrets.token_hex(32))">
BASE_DOMAIN=yourdomain.com
SPAWNER_SUBDOMAIN=coder
TRAEFIK_NETWORK=web
TRAEFIK_CERTRESOLVER=lets-encrypt
TRAEFIK_ENTRYPOINT=websecure

# Dynamische Template-Konfiguration (Semikolon-getrennt)
# Liste aller verfügbaren Container-Images
# Metadaten (Namen, Beschreibungen) werden aus templates.json geladen
USER_TEMPLATE_IMAGES=user-template-01:latest;user-template-02:latest;user-template-next:latest

# Optional: SMTP für Magic Links
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=password
SMTP_FROM=noreply@example.com
FRONTEND_URL=https://coder.yourdomain.com
```

**Hinweis:** Behalte alle anderen Einstellungen aus `.env.example` (CORS, JWT, etc.)

### Phase 2: Services starten (10 Minuten)

#### 2.1 Docker Compose starten
```bash
docker-compose up -d --build

# Warte bis Services bereit sind
sleep 10

# Überprüfe Status
docker-compose ps
```

**Erwartet Output:**
```
NAME                STATUS              PORTS
spawner             Up X seconds        5000/tcp
frontend            Up X seconds        3000/tcp
traefik             Up X seconds        80/tcp, 443/tcp, 8080/tcp
```

#### 2.2 Logs prüfen
```bash
# Backend Logs
docker-compose logs spawner | tail -20

# Frontend Logs
docker-compose logs frontend | tail -20

# Traefik Logs
docker-compose logs traefik | tail -20
```

**Wichtig:** Suche nach ERROR-Meldungen. Häufige Fehler:
- `docker.errors.ImageNotFound`: Template-Images nicht gebaut
- `ConnectionRefusedError`: Backend nicht erreichbar
- `CORS error`: CORS_ORIGINS nicht konfiguriert

#### 2.3 Health Check
```bash
# Backend Health
curl -s http://localhost:5000/health | jq .

# Frontend (falls lokal erreichbar)
curl -s http://localhost:3000 | head -20
```

### Phase 3: Erste Registrierung (5 Minuten)

#### 3.1 Öffne Dashboard
```
https://coder.yourdomain.com
```

#### 3.2 Registrierung
1. Klick auf "Registrieren"
2. Gib Email-Adresse ein: `test@yourdomain.com`
3. Klick "Magic Link senden"
4. Überprüfe Email (oder Logs für Magic Link Token wenn SMTP nicht konfiguriert)
5. Klick auf Magic Link in Email
6. Du wirst zum Dashboard weitergeleitet

#### 3.3 Dashboard überprüfen
- [ ] N Container-Cards sichtbar (entsprechend USER_TEMPLATE_IMAGES)
  - Standardmäßig: template-01, template-02, template-next
- [ ] Alle haben Status "Noch nicht erstellt"
- [ ] Jede Card zeigt Display-Namen und Beschreibung aus `templates.json`
- [ ] Buttons zeigen "Erstellen & Öffnen"

### Phase 4: Teste beide Container (10 Minuten)

#### 4.1 Development Container erstellen
```
Dashboard: Dev Container Card → Click "Erstellen & Öffnen"

Erwartet:
1. Loading-Spinner erscheint
2. Neuer Browser-Tab öffnet sich
3. URL: https://coder.yourdomain.com/test-dev (mit deinem slug)
4. Nginx-Willkommensseite wird angezeigt
```

#### 4.2 Dashboard aktualisieren
```
Zurück zum Spawner-Tab

Erwartet:
1. Dev-Container Status = "Läuft"
2. Button ändert sich zu "Service öffnen"
3. Last-Used Timestamp wird angezeigt
```

#### 4.3 Production Container erstellen
```
Dashboard: Prod Container Card → Click "Erstellen & Öffnen"

Erwartet:
1. Loading-Spinner erscheint
2. Neuer Browser-Tab öffnet sich
3. URL: https://coder.yourdomain.com/test-prod (mit deinem slug)
4. Next.js Demo-Seite mit Shadcn/UI wird angezeigt
```

#### 4.4 Beide Containers öffnen
```
Dashboard: Click "Service öffnen" für Dev-Container
→ Öffnet Dev-Container in bestehendem/neuem Tab

Dashboard: Click "Service öffnen" für Prod-Container
→ Öffnet Prod-Container in bestehendem/neuem Tab

Beide sollten funktionieren, ohne /dev oder /prod in der URL!
```

---

## 🔍 Verification Checklist

### Backend
- [ ] spawner Container läuft (`docker ps | grep spawner`)
- [ ] Flask Server startet ohne Fehler (`docker-compose logs spawner | grep "Running on"`)
- [ ] UserContainer Tabelle existiert (`docker exec spawner sqlite3 /app/data/users.db ".schema user_container"`)
- [ ] GET /api/user/containers gibt 2 Containers zurück (mit Status "not_created")
- [ ] POST /api/container/launch/dev funktioniert und erstellt Container

### Frontend
- [ ] Dashboard lädt beide Container-Cards
- [ ] API-Calls funktionieren (Browser DevTools → Network Tab)
- [ ] Buttons sind nicht disabled
- [ ] Loading State erscheint beim Klick
- [ ] URLs öffnen sich in neuem Tab

### Docker & Traefik
- [ ] `docker ps | grep user-` zeigt 2 Container nach Launch
- [ ] Traefik Dashboard zeigt 2 HTTP Routers (für dev und prod)
- [ ] StripPrefix entfernt /{slug}-{type} korrekt
- [ ] Beide Containers sind erreichbar ohne /dev oder /prod in der URL

### URLs
- [ ] `https://coder.yourdomain.com/{slug}-dev` → Dev-Container
- [ ] `https://coder.yourdomain.com/{slug}-prod` → Prod-Container
- [ ] Keine 404 oder CORS-Fehler in Browser Console

---

## 🐛 Troubleshooting

### Problem: Container spawnt nicht

**Symptom**: Klick auf "Erstellen & Öffnen" → Fehler "Container konnte nicht erstellt werden"

**Lösung**:
```bash
# 1. Überprüfe Logs
docker-compose logs spawner | tail -50

# 2. Überprüfe ob Images existieren
docker images | grep user-

# 3. Falls nicht vorhanden, baue neu:
docker build -t user-service-template:latest user-template/
docker build -t user-template-next:latest user-template-next/

# 4. Starte Services neu
docker-compose restart spawner
```

### Problem: URL öffnet nicht / 404 Error

**Symptom**: Browser zeigt 404 oder Timeout beim Klick "Service öffnen"

**Lösung**:
```bash
# 1. Überprüfe Container läuft
docker ps | grep user-testuser-dev

# 2. Überprüfe Traefik Dashboard
curl http://localhost:8080/api/http/routers | grep user

# 3. Überprüfe Container-Labels
docker inspect user-testuser-dev-1 | grep -A5 "traefik"

# 4. Falls Labels falsch, starte Services neu
docker-compose restart

# 5. Überprüfe Traefik Logs
docker-compose logs traefik | grep user
```

### Problem: StripPrefix funktioniert nicht

**Symptom**: Container erhält Path mit /{slug}-dev noch darin

**Lösung**:
```bash
# 1. Prüfe Traefik Middleware
curl http://localhost:8080/api/http/middlewares | jq . | grep -A10 "user"

# 2. Container sollte bei / landen, nicht bei /{slug}-dev
curl -H "Host: coder.yourdomain.com" \
  "http://localhost:8080/testuser-dev/this/is/a/test"
# Sollte zu Container weitergeleitet werden mit Path: /this/is/a/test

# 3. Falls Problem persistiert, rebuild Traefik
docker-compose down
docker-compose up -d --build traefik
```

### Problem: Magic Link funktioniert nicht

**Symptom**: Email wird nicht empfangen oder Link funktioniert nicht

**Lösung**:
```bash
# 1. Überprüfe SMTP Konfiguration
docker-compose logs spawner | grep -i smtp

# 2. Falls SMTP nicht konfiguriert, überprüfe Logs für Token
docker-compose logs spawner | grep "Magic Link" | tail -5

# 3. Kopiere Token manuell aus Logs und öffne URL:
# https://coder.yourdomain.com/verify-signup?token=ABC123...

# 4. Zum Testen ohne SMTP:
# Setze SMTP_HOST=localhost im .env
# Tokens werden dann nur in Logs ausgegeben
```

### Problem: Frontend kann nicht mit Backend kommunizieren

**Symptom**: CORS-Fehler oder "Netzwerkfehler"

**Lösung**:
```bash
# 1. Überprüfe CORS_ORIGINS in Backend
docker exec spawner grep CORS_ORIGINS /app/.env

# 2. Sollte enthalten: https://coder.yourdomain.com (oder http://localhost:3000 in Dev)

# 3. Falls nicht richtig gesetzt:
# Bearbeite .env und setze:
CORS_ORIGINS=https://coder.yourdomain.com

# 4. Restart Backend
docker-compose restart spawner

# 5. Browser Cache löschen und Seite neu laden
```

---

## 📊 Monitoring

### Logs überwachen
```bash
# Alle Services
docker-compose logs -f

# Nur Backend
docker-compose logs -f spawner

# Traefik
docker-compose logs -f traefik

# Frontend
docker-compose logs -f frontend
```

### Container Status
```bash
# Alle Container
docker ps

# Mit Filter
docker ps | grep user-

# Detailed Info
docker inspect user-testuser-dev-1
```

### Traefik Status
```bash
# Routers
curl http://localhost:8080/api/http/routers

# Middlewares
curl http://localhost:8080/api/http/middlewares

# Services
curl http://localhost:8080/api/http/services
```

### Datenbank prüfen
```bash
# Container-Liste
docker exec spawner sqlite3 /app/data/users.db \
  "SELECT id, user_id, container_type, container_id FROM user_container LIMIT 10;"

# User-Liste
docker exec spawner sqlite3 /app/data/users.db \
  "SELECT id, email, slug, state FROM user LIMIT 10;"
```

---

## ⚙️ Häufige Konfigurationsänderungen nach Deployment

**WICHTIG:** Die `.env` Datei wird als **Volume in den Container gemountet**. Das bedeutet:
- Änderungen in `.env` werden **zur Laufzeit** gelesen
- Du brauchst **kein Docker-Rebuild** für Konfigurationsänderungen
- Nur `docker-compose down` + `docker-compose up -d` reicht

### SMTP/Email-Anmeldedaten ändern

Falls du die Email-Anmeldedaten später ändern musst (z.B. Passwort aktualisiert):

```bash
# 1. Bearbeite .env
nano .env

# Ändere diese Zeilen:
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=deine-email@gmail.com
# SMTP_PASSWORD=neues-passwort
# SMTP_FROM=noreply@domain.com

# 2. Stoppe Container komplett und starte neu
docker-compose down
docker-compose up -d spawner

# 3. Überprüfe ob neue Credentials geladen wurden
docker exec spawner cat /app/.env | grep SMTP_HOST
```

**Hinweis:** `docker-compose restart spawner` reicht auch aus (schneller), aber `down`/`up` ist sicherer.

### Domain oder Base URL ändern

Falls du die Domain oder Subdomain ändern möchtest:

```bash
# 1. Bearbeite .env
nano .env

# Ändere diese Zeilen:
# BASE_DOMAIN=neudomain.com
# SPAWNER_SUBDOMAIN=coder (oder etwas anderes)
# FRONTEND_URL=https://coder.neudomain.com

# 2. Starte Services neu
docker-compose down
docker-compose up -d spawner frontend

# 3. Überprüfe Config (sollte neue Domain zeigen)
docker exec spawner cat /app/.env | grep BASE_DOMAIN
```

### Magic Link Token Expiration ändern

Standardmäßig haben Magic Links 15 Minuten Gültigkeitsdauer. Wenn du das ändern möchtest:

```bash
# 1. Bearbeite .env
nano .env

# Ändere diese Zeilen:
# MAGIC_LINK_TOKEN_EXPIRY=900  (in Sekunden, default: 15 Min)
# MAGIC_LINK_RATE_LIMIT=3      (max. 3 Links pro Stunde)

# 2. Starte Backend neu
docker-compose restart spawner
# oder sicherer:
# docker-compose down
# docker-compose up -d spawner
```

### JWT Token Expiration ändern

Standardmäßig verfallen JWT Tokens nach 1 Stunde:

```bash
# 1. Bearbeite .env
nano .env

# Ändere diese Zeile:
# JWT_ACCESS_TOKEN_EXPIRES=3600  (in Sekunden)

# 2. Starte Backend neu
docker-compose restart spawner
```

### Container-Resource-Limits ändern

Wenn deine Server-Hardware unterschiedlich ist, passe die Limits an:

```bash
# 1. Bearbeite .env
nano .env

# Ändere diese Zeilen:
# DEFAULT_MEMORY_LIMIT=512m     (RAM pro Container)
# DEFAULT_CPU_QUOTA=50000       (CPU: 50000 = 0.5 CPU, 100000 = 1 CPU)

# 2. Starte Backend neu
docker-compose restart spawner

# Info: Neue Container verwenden sofort die neuen Limits
# Laufende Container behalten alte Limits (bis Neustart)
```

### Logging Level ändern

```bash
# 1. Bearbeite .env
nano .env

# Ändere diese Zeile:
# LOG_LEVEL=INFO  (Options: DEBUG, INFO, WARNING, ERROR)

# 2. Starte Backend neu
docker-compose restart spawner
```

### Überprüfe welche Werte der Container tatsächlich nutzt

Falls du unsicher bist, ob die neuen Konfigurationswerte geladen wurden:

```bash
# Zeige die .env Werte, die der Container sieht
docker exec spawner cat /app/.env | grep SMTP

# Alle SMTP-Einstellungen anzeigen:
docker exec spawner cat /app/.env | grep SMTP

# Überprüfe mit Python, ob die Werte korrekt geladen sind:
docker exec spawner python3 << 'EOF'
from config import Config
print(f"SMTP_HOST: {Config.SMTP_HOST}")
print(f"SMTP_USER: {Config.SMTP_USER}")
print(f"SMTP_PORT: {Config.SMTP_PORT}")
EOF
```

**Wichtig:**
- `cat /app/.env | grep SMTP` zeigt die **aktuellen** Werte aus der `.env` Datei
- `docker exec spawner env` zeigt Shell-Variablen, nicht Python-Variablen!
- Python lädt die Werte mit `load_dotenv()` - überprüfe mit Python-Code ob sie korrekt geladen sind

---

## 🐛 Debug-API für Administratoren

**Neue Feature:** Admin-API zum Debuggen und Bereinigen von Logs und Datenbanken

### Vorbereitung: DEBUG_TOKEN generieren

```bash
# 1. Token generieren
python3 -c "import secrets; print(secrets.token_hex(32))"

# Beispiel-Output:
# a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

# 2. In .env eintragen
nano .env
# DEBUG_TOKEN=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

# 3. Backend neustarten
docker-compose restart spawner
```

### Debug-API Endpoints

**Base:** `/api/admin/debug`

**Authentifizierung via Header:**
```bash
curl -H "X-Debug-Token: your-token-here" "http://localhost:5000/api/admin/debug?action=..."
```

Oder mit **Admin JWT Token:**
```bash
curl -H "Authorization: Bearer your-jwt-token" "http://localhost:5000/api/admin/debug?action=..."
```

### Verfügbare Actions

#### 1. Logs anzeigen (view-logs)

```bash
curl -H "X-Debug-Token: xxx" \
  "http://localhost:5000/api/admin/debug?action=view-logs"
```

Zeigt die **letzten 100 Zeilen** der Flask Log-Datei (`/app/logs/spawner.log`). Enthält alle API-Anfragen, Fehler und Debug-Meldungen.

#### 2. Logs löschen (clear-logs)

```bash
curl -H "X-Debug-Token: xxx" \
  "http://localhost:5000/api/admin/debug?action=clear-logs"
```

Löscht die Log-Datei komplett. Um Logs zu löschen, nutze auch direkt im Container:

```bash
docker exec spawner rm /app/logs/spawner.log
```

Nach dem Löschen werden neue Logs ab der nächsten Aktion geschrieben.

#### 3. User entfernen (delete-email)

```bash
curl -H "X-Debug-Token: xxx" \
  "http://localhost:5000/api/admin/debug?action=delete-email&email=test@example.com"
```

Entfernt einen **User komplett** aus der Datenbank:
- User-Profil gelöscht
- Container gelöscht (falls existiert)
- Alle Token gelöscht
- Alle Datenbank-Einträge entfernt

**WARNUNG:** Das ist **nicht rückgängig zu machen**!

#### 4. Magic Link Tokens entfernen (delete-token)

```bash
curl -H "X-Debug-Token: xxx" \
  "http://localhost:5000/api/admin/debug?action=delete-token&email=test@example.com"
```

Löscht **nur die Magic Link Tokens** für eine Email. Der User bleibt bestehen!

Nützlich wenn:
- Rate-Limiting blockiert den User
- Tokens sind fehlerhaft
- User neue Tokens anfordern soll

#### 5. Hilfe anzeigen (info)

```bash
curl -H "X-Debug-Token: xxx" \
  "http://localhost:5000/api/admin/debug?action=info"
```

Zeigt alle verfügbaren Actions und Beispiele.

### Praktische Beispiele

**Problem: User kann sich nicht anmelden (Rate Limit)**

```bash
# 1. Lösche alle Tokens für diese Email
curl -H "X-Debug-Token: xxx" \
  "http://localhost:5000/api/admin/debug?action=delete-token&email=user@example.com"

# 2. User kann jetzt neu anfragen
```

**Problem: Alte Test-User in der Datenbank**

```bash
# Lösche kompletten User
curl -H "X-Debug-Token: xxx" \
  "http://localhost:5000/api/admin/debug?action=delete-email&email=test@example.com"
```

**Problem: Logs sind zu groß**

```bash
# Lösche alle Logs
curl -H "X-Debug-Token: xxx" \
  "http://localhost:5000/api/admin/debug?action=clear-logs"
```

**Problem: Brauche die letzten Fehler zum Debuggen**

```bash
# Hole letzten 100 Zeilen
curl -H "X-Debug-Token: xxx" \
  "http://localhost:5000/api/admin/debug?action=view-logs"
```

### Bash-Alias für schnellen Zugriff

Füge dies in `~/.bashrc` ein für schnellere Befehle:

```bash
export SPAWNER_DEBUG_TOKEN="dein-token-hier"
export SPAWNER_URL="http://localhost:5000"

alias spawner-logs="curl -H 'X-Debug-Token: $SPAWNER_DEBUG_TOKEN' '$SPAWNER_URL/api/admin/debug?action=view-logs'"
alias spawner-clear-logs="curl -H 'X-Debug-Token: $SPAWNER_DEBUG_TOKEN' '$SPAWNER_URL/api/admin/debug?action=clear-logs'"
alias spawner-delete-email="curl -H 'X-Debug-Token: $SPAWNER_DEBUG_TOKEN' '$SPAWNER_URL/api/admin/debug?action=delete-email&email="
```

Dann:
```bash
# Logs anzeigen
spawner-logs

# User löschen
spawner-delete-email=test@example.com"
```

---

## 🔐 Security Checklist

- [ ] SECRET_KEY ist generiert und komplex
- [ ] JWT_SECRET_KEY ist gesetzt (oder nutzt SECRET_KEY)
- [ ] CORS_ORIGINS ist auf richtige Domain gesetzt
- [ ] SMTP_PASSWORD ist nicht im .env.example hart-codiert
- [ ] Database-URL nutzt keine Standardpasswörter (für Production)
- [ ] Traefik Let's Encrypt Email ist gesetzt
- [ ] TLS ist aktiviert für alle Routes
- [ ] Container-Ressource Limits sind gesetzt (Memory, CPU)

---

## 📈 Scaling & Performance

### Single User Multiple Containers
- Pro User können 2 Container laufen (dev und prod)
- Jeder Container: 512MB RAM, 0.5 CPU (konfigurierbar)
- Für 100 User: Max 1GB RAM pro Container = 200GB total (nicht realistisch!)

### Production Empfehlungen
- **Datenbank**: Wechsel auf PostgreSQL (in config.py kommentiert)
- **Storage**: Persistente Volumes für Container-Daten
- **Backups**: Regelmäßige Backups der Datenbank und User-Volumes
- **Monitoring**: Prometheus + Grafana für Metrics
- **Logging**: Centralized Logging (ELK, Loki)

### Load Testing
```bash
# Einfacher Test mit 10 gleichzeitigen Containern
for i in {1..10}; do
  docker run -d \
    --network web \
    --label "test=true" \
    user-service-template:latest
done

# Überwachen
docker stats | grep "test"

# Cleanup
docker ps --filter "label=test=true" | xargs docker rm -f
```

---

## 🎓 Nächste Schritte

### Phase 1: MVP Live ✅
- [x] 2 Container-Typen (dev, prod)
- [x] On-Demand Erstellung
- [x] Multi-Container Dashboard
- [x] Status-Tracking

### Phase 2: Enhancements (Optional)
- [ ] Container-Logs im Dashboard
- [ ] Container-Restart pro Type
- [ ] Resource-Monitoring
- [ ] Container-Cleanup (Idle Timeout)
- [ ] Custom Templates vom User

### Phase 3: Admin Features (Optional)
- [ ] Container-Management im Admin-Panel
- [ ] User-Quotas pro Container-Typ
- [ ] Template-Updates ohne Service-Restart
- [ ] Audit Logging für Container-Events

---

## 📞 Support & Dokumentation

### Wichtige Dateien
- **IMPLEMENTATION_SUMMARY.md** - Detaillierte Feature-Liste
- **TEST_VERIFICATION.md** - Test-Anleitung
- **CLAUDE.md** - Projekt-Übersicht
- **docker-compose.yml** - Service-Konfiguration
- **.env.example** - Environment-Template

### Häufig benötigte Commands
```bash
# Status überprüfen
docker-compose ps

# Logs anschauen
docker-compose logs -f [service]

# Services neu starten
docker-compose restart [service]

# Container in Python Shell bearbeiten
docker exec -it spawner python

# Datenbank migrieren
docker exec spawner flask db migrate
docker exec spawner flask db upgrade

# Admin-User erstellen
docker exec -it spawner python <<EOF
from app import app, db
from models import User
with app.app_context():
    user = User(email='admin@example.com', slug='admin')
    user.is_admin = True
    user.state = 'verified'
    db.session.add(user)
    db.session.commit()
EOF
```

---

**Version**: 1.0.0 (MVP)
**Deployment Date**: 2025-01-31
**Last Updated**: 2025-02-01
**Status**: ✅ Ready for Production
