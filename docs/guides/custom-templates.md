# Custom Templates - Vollständige Anleitung

## 📋 Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Template-System Architektur](#template-system-architektur)
3. [Anforderungen an Templates](#anforderungen-an-templates)
4. [Neues Template erstellen](#neues-template-erstellen)
5. [Template-Beispiele](#template-beispiele)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Überblick

Das Container Spawner System verwendet ein **dynamisches Template-System**, das beliebig viele User-Templates unterstützt:

- **Automatische Erkennung**: `install.sh` findet und baut alle `user-template-*` Verzeichnisse
- **Flexible Konfiguration**: Templates werden in `.env` definiert (semikolon-getrennt)
- **Metadaten-Driven**: Display-Namen und Beschreibungen kommen aus `templates.json`
- **Multi-Container Support**: Jeder User kann beliebig viele Container verschiedener Typen erstellen

**Standardtemplates:**
- `template-01`: Nginx Basic - Einfacher statischer Webserver
- `template-02`: Nginx Advanced - Nginx mit erweiterten Features
- `template-next`: Next.js Production - React-App mit Shadcn/UI

**Custom Templates hinzufügen:** Beliebig viele eigene Templates erstellen (Python, Node.js, etc.)

---

## Template-System Architektur

### Wie das System funktioniert

```
1. install.sh durchsucht Verzeichnis
   ↓
2. Findet alle user-template-* Ordner
   ↓
3. Baut Docker Images automatisch
   ↓
4. Backend lädt Template-Liste aus .env
   ↓
5. Metadaten werden aus templates.json geladen
   ↓
6. Dashboard zeigt alle verfügbaren Templates
   ↓
7. User klickt "Erstellen" → Container spawnt
```

### Dateien im System

| Datei/Ordner | Zweck |
|--------------|-------|
| `user-template-xyz/` | Template-Verzeichnis (Dockerfile + Assets) |
| `.env` → `USER_TEMPLATE_IMAGES` | Liste aller verfügbaren Images |
| `templates.json` | Metadaten (Display-Name, Beschreibung) |
| `config.py` | Lädt Templates dynamisch beim Start |
| `container_manager.py` | Spawnt Container aus Templates |

### Template-Namen → Typ-Mapping

Das System extrahiert automatisch den Container-Typ aus dem Image-Namen:

```python
# Beispiele:
'user-template-01:latest'    → Typ: 'template-01'
'user-template-next:latest'  → Typ: 'template-next'
'user-template-python:latest' → Typ: 'template-python'
'custom-nginx:v1.0'          → Typ: 'custom-nginx'
```

**Regel:** Image-Name ohne `user-` Prefix und ohne Tag (`:latest`) = Container-Typ

---

## Anforderungen an Templates

### Pflicht-Anforderungen

Jedes Template **MUSS**:

1. **Port 8080 exposen** (unprivileged, kein root)
   ```dockerfile
   EXPOSE 8080
   ```

2. **Webserver auf Port 8080 laufen lassen**
   - Nginx: `listen 8080;`
   - Node.js: `app.listen(8080)`
   - Flask: `app.run(port=8080, host='0.0.0.0')`

3. **Als unprivileged User laufen** (Sicherheit)
   ```dockerfile
   USER nginx  # oder node, www-data, etc.
   ```

4. **HTTP-Server bereitstellen** (Traefik routet HTTP-Traffic)

### Optionale Features

Templates **KÖNNEN**:

- Datenbank-Container integrieren (via Docker Compose in Template)
- Umgebungsvariablen nutzen (via ENV in Dockerfile)
- Volume-Mounts für persistente Daten (via docker-compose.yml)
- Build-Args für Konfiguration (z.B. `ARG NODE_VERSION=18`)

### Was NICHT funktioniert

Templates **KÖNNEN NICHT**:

- Andere Ports als 8080 nutzen (Traefik-Konfiguration)
- Root-Rechte benötigen (Security Policy)
- Direkten Zugriff auf Docker Socket (Isolation)
- Andere Container spawnen (nur eigener Container)

---

## Neues Template erstellen

### Schritt 1: Verzeichnis erstellen

```bash
cd /path/to/spawner
mkdir user-template-myapp
cd user-template-myapp
```

**Namenskonvention:** `user-template-<name>`
- `<name>`: Eindeutiger Identifier (lowercase, keine Sonderzeichen außer `-`)
- Beispiele: `user-template-python`, `user-template-django`, `user-template-flask`

### Schritt 2: Dockerfile erstellen

**Basis-Vorlage (Nginx):**
```dockerfile
FROM nginx:alpine

# Expose Port 8080 (unprivileged)
EXPOSE 8080

# Kopiere statische Dateien
COPY index.html /usr/share/nginx/html/

# Nginx auf Port 8080 konfigurieren
RUN sed -i 's/listen       80;/listen       8080;/' /etc/nginx/conf.d/default.conf

# Run as unprivileged user
USER nginx

CMD ["nginx", "-g", "daemon off;"]
```

**Erweiterte Vorlage (Node.js):**
```dockerfile
FROM node:18-alpine

# Working Directory
WORKDIR /app

# Install Dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy Application Code
COPY . .

# Expose Port 8080
EXPOSE 8080

# Run as unprivileged user
USER node

# Start Application
CMD ["node", "server.js"]
```

**Wichtig:** Port 8080 ist Pflicht!

### Schritt 3: Template-Assets hinzufügen

**Beispiel: Nginx mit statischer index.html**
```bash
cat > index.html <<'EOF'
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Mein Custom Template</title>
</head>
<body>
    <h1>Willkommen zu meinem Custom Container!</h1>
    <p>Dieser Container läuft auf Port 8080.</p>
</body>
</html>
EOF
```

**Beispiel: Node.js mit server.js**
```bash
cat > server.js <<'EOF'
const express = require('express');
const app = express();
const PORT = 8080;

app.get('/', (req, res) => {
    res.send('<h1>Node.js Template</h1><p>Läuft auf Port 8080</p>');
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server läuft auf Port ${PORT}`);
});
EOF
```

### Schritt 4: `.env` aktualisieren

Öffne die `.env` Datei im Hauptverzeichnis:
```bash
nano .env
```

Füge dein Template zur `USER_TEMPLATE_IMAGES` Liste hinzu:
```bash
# Vorher:
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-02:latest;user-template-next:latest"

# Nachher:
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-02:latest;user-template-next:latest;user-template-myapp:latest"
```

**Wichtig:** Semikolon-getrennt, keine Leerzeichen, mit `:latest` Tag!

### Schritt 5: `templates.json` aktualisieren

Öffne `templates.json`:
```bash
nano templates.json
```

Füge Metadaten für dein Template hinzu:
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
      "description": "Nginx mit erweiterten Features"
    },
    {
      "type": "template-next",
      "image": "user-template-next:latest",
      "display_name": "Next.js Production",
      "description": "React-App mit Shadcn/UI"
    },
    {
      "type": "template-myapp",
      "image": "user-template-myapp:latest",
      "display_name": "Meine Custom App",
      "description": "Mein eigenes Template mit Node.js"
    }
  ]
}
```

**Felder:**
- `type`: Muss mit extrahiertem Typ übereinstimmen (`template-myapp`)
- `image`: Vollständiger Image-Name mit Tag
- `display_name`: Name im Dashboard (beliebig)
- `description`: Kurze Beschreibung für User

### Schritt 6: Template lokal bauen

```bash
cd /path/to/spawner
docker build -t user-template-myapp:latest user-template-myapp/
```

**Überprüfung:**
```bash
docker images | grep user-template-myapp
# Expected: user-template-myapp   latest   abc123def456   5 seconds ago   150MB
```

### Schritt 7: Template testen

Starte einen Test-Container:
```bash
docker run -d -p 8080:8080 --name test-myapp user-template-myapp:latest
```

Teste im Browser:
```bash
curl http://localhost:8080
# Expected: HTML-Output deines Templates
```

Cleanup:
```bash
docker stop test-myapp
docker rm test-myapp
```

### Schritt 8: Änderungen committen

```bash
git add user-template-myapp/ .env templates.json
git commit -m "feat: add custom template-myapp"
git push
```

---

## Template-Beispiele

### Beispiel 1: Python Flask Template

**Verzeichnisstruktur:**
```
user-template-flask/
├── Dockerfile
├── requirements.txt
└── app.py
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application
COPY app.py .

# Expose Port 8080
EXPOSE 8080

# Run as unprivileged user
RUN useradd -m appuser
USER appuser

# Start Flask
CMD ["python", "app.py"]
```

**requirements.txt:**
```
Flask==3.0.0
gunicorn==21.2.0
```

**app.py:**
```python
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Flask Template</h1><p>Läuft auf Port 8080</p>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

**In `.env` hinzufügen:**
```bash
USER_TEMPLATE_IMAGES="...;user-template-flask:latest"
```

**In `templates.json` hinzufügen:**
```json
{
  "type": "template-flask",
  "image": "user-template-flask:latest",
  "display_name": "Python Flask",
  "description": "Flask Web-Framework für Python"
}
```

### Beispiel 2: Static Site Generator (Hugo)

**Verzeichnisstruktur:**
```
user-template-hugo/
├── Dockerfile
├── config.toml
└── content/
    └── _index.md
```

**Dockerfile:**
```dockerfile
FROM klakegg/hugo:alpine AS builder

WORKDIR /src
COPY . .
RUN hugo --minify

FROM nginx:alpine

# Copy built site
COPY --from=builder /src/public /usr/share/nginx/html

# Nginx on Port 8080
RUN sed -i 's/listen       80;/listen       8080;/' /etc/nginx/conf.d/default.conf

EXPOSE 8080
USER nginx

CMD ["nginx", "-g", "daemon off;"]
```

**config.toml:**
```toml
baseURL = "/"
languageCode = "de-de"
title = "Hugo Template"
theme = "ananke"
```

### Beispiel 3: Database-Backed Template (Node.js + PostgreSQL)

**Hinweis:** Für Multi-Container-Templates (mit DB) nutze `docker-compose.yml` **innerhalb** des Templates.

**Verzeichnisstruktur:**
```
user-template-node-db/
├── Dockerfile
├── docker-compose.yml
├── package.json
└── server.js
```

**Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 8080
USER node

CMD ["node", "server.js"]
```

**docker-compose.yml (wird vom Container genutzt):**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

**Wichtig:** Spawner erstellt nur den Main-Container. Für Multi-Container nutze einen Wrapper-Script oder starte via `docker-compose` im Container.

---

## Deployment

### Lokale Entwicklung

```bash
# 1. Template erstellen
mkdir user-template-xyz
cd user-template-xyz
# ... Dockerfile erstellen ...

# 2. .env und templates.json aktualisieren
nano ../.env
nano ../templates.json

# 3. Template bauen
docker build -t user-template-xyz:latest .

# 4. Spawner neu starten
cd ..
docker-compose restart spawner

# 5. Dashboard öffnen
# Template sollte jetzt sichtbar sein
```

### Production Deployment (Server)

**Schritt 1: Code committen**
```bash
git add user-template-xyz/ .env templates.json
git commit -m "feat: add template-xyz"
git push
```

**Schritt 2: Auf Server deployen**
```bash
# SSH zum Server
ssh user@server

# Navigiere zum Spawner-Verzeichnis
cd /volume1/docker/spawner

# Pull neueste Änderungen
git pull

# Baue neues Template
docker build -t user-template-xyz:latest user-template-xyz/

# Kopiere aktualisierte Config-Dateien in Container
docker cp .env spawner:/app/.env
docker cp templates.json spawner:/app/templates.json

# Restart Spawner (lädt neue Konfiguration)
docker-compose restart spawner
```

**Schritt 3: Verifikation**
```bash
# Überprüfe ob Template geladen wurde
docker-compose logs spawner | grep "template-xyz"

# Teste via Debug-API
curl -H "X-Debug-Token: <token>" \
  "http://localhost:5000/api/admin/debug?action=info"

# Dashboard öffnen und neues Template prüfen
```

### Automatisiertes Deployment (install.sh)

Das `install.sh` Script baut **automatisch alle** `user-template-*` Verzeichnisse:

```bash
# Auf Server:
cd /volume1/docker/spawner
git pull
bash install.sh
```

**Was install.sh macht:**
1. Findet alle `user-template-*` Verzeichnisse
2. Baut Docker Images für jedes Template
3. Startet Services neu
4. Templates erscheinen automatisch im Dashboard

**Vorteil:** Keine manuellen Docker-Builds nötig!

---

## Troubleshooting

### Problem: Template erscheint nicht im Dashboard

**Symptom:** Neues Template ist nicht in der Container-Liste sichtbar

**Lösung:**
```bash
# 1. Überprüfe .env im Container
docker exec spawner cat /app/.env | grep USER_TEMPLATE_IMAGES

# 2. Überprüfe templates.json im Container
docker exec spawner cat /app/templates.json

# 3. Überprüfe Backend-Logs
docker-compose logs spawner | grep -i template

# 4. Falls nicht aktualisiert, kopiere Dateien manuell:
docker cp .env spawner:/app/.env
docker cp templates.json spawner:/app/templates.json
docker-compose restart spawner
```

### Problem: Container spawnt nicht / Fehler beim Start

**Symptom:** Klick auf "Erstellen" → Fehler "Container konnte nicht erstellt werden"

**Lösung:**
```bash
# 1. Überprüfe ob Image existiert
docker images | grep user-template-xyz

# 2. Falls nicht vorhanden, baue neu:
docker build -t user-template-xyz:latest user-template-xyz/

# 3. Teste Image manuell
docker run -d -p 8080:8080 --name test-xyz user-template-xyz:latest

# 4. Überprüfe Logs
docker logs test-xyz

# 5. Cleanup
docker stop test-xyz && docker rm test-xyz

# 6. Überprüfe Spawner-Logs
docker-compose logs spawner | tail -50
```

### Problem: Port 8080 nicht erreichbar

**Symptom:** Container läuft, aber `curl http://localhost:8080` gibt Timeout

**Lösung:**
```bash
# 1. Überprüfe ob Container wirklich auf 8080 hört
docker exec <container-id> netstat -tlnp | grep 8080

# 2. Überprüfe Dockerfile
cat user-template-xyz/Dockerfile | grep EXPOSE
# Expected: EXPOSE 8080

# 3. Überprüfe Webserver-Konfiguration
# Nginx: listen 8080;
# Node.js: app.listen(8080, '0.0.0.0')
# Flask: app.run(port=8080, host='0.0.0.0')

# 4. Rebuilde Template mit korrektem Port
docker build -t user-template-xyz:latest user-template-xyz/
```

### Problem: Traefik routet nicht zum Container

**Symptom:** URL öffnet, aber zeigt 404 oder Timeout

**Lösung:**
```bash
# 1. Überprüfe Container-Labels
docker inspect user-<slug>-<type>-<id> | grep -A10 traefik

# 2. Überprüfe Traefik Dashboard
# http://<server>:8080 → HTTP Routers

# 3. Überprüfe StripPrefix Middleware
curl http://localhost:8080/api/http/middlewares | jq . | grep user

# 4. Überprüfe Traefik Logs
docker-compose logs traefik | grep user-<slug>

# 5. Starte Traefik neu
docker-compose restart traefik
```

### Problem: Datei-Änderungen werden nicht übernommen

**Symptom:** Dockerfile geändert, aber Container nutzt alte Version

**Lösung:**
```bash
# 1. IMMER --no-cache beim Rebuild verwenden
docker build --no-cache -t user-template-xyz:latest user-template-xyz/

# 2. Alte Container entfernen
docker ps -a | grep user-template-xyz | awk '{print $1}' | xargs docker rm -f

# 3. Neue Container spawnen (via Dashboard oder API)

# 4. Überprüfe Image-Erstellungsdatum
docker images | grep user-template-xyz
# Should show recent timestamp
```

---

## Best Practices

### Sicherheit

1. **Unprivileged Users verwenden**
   ```dockerfile
   # NICHT als root laufen
   USER nginx  # oder node, www-data, appuser, etc.
   ```

2. **Minimale Base Images**
   ```dockerfile
   # Bevorzuge alpine-Varianten
   FROM node:18-alpine  # statt node:18
   FROM python:3.11-slim  # statt python:3.11
   ```

3. **Keine Secrets im Image**
   ```dockerfile
   # ❌ FALSCH
   ENV API_KEY=secret123

   # ✅ RICHTIG - Via Runtime-Env
   # Secrets werden vom Spawner injiziert
   ```

### Performance

1. **Multi-Stage Builds nutzen**
   ```dockerfile
   # Build Stage
   FROM node:18-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci
   COPY . .
   RUN npm run build

   # Runtime Stage
   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   ```

2. **Layer Caching optimieren**
   ```dockerfile
   # Dependencies zuerst (ändern sich selten)
   COPY package*.json ./
   RUN npm ci

   # Code danach (ändert sich oft)
   COPY . .
   ```

3. **Image-Größe minimieren**
   ```dockerfile
   # Cleanup in einer RUN-Anweisung
   RUN apt-get update && \
       apt-get install -y pkg1 pkg2 && \
       apt-get clean && \
       rm -rf /var/lib/apt/lists/*
   ```

### Wartbarkeit

1. **Versionierung nutzen**
   ```bash
   # Statt :latest auch spezifische Versionen taggen
   docker build -t user-template-xyz:v1.0.0 .
   docker tag user-template-xyz:v1.0.0 user-template-xyz:latest
   ```

2. **README.md pro Template**
   ```markdown
   # Template XYZ

   ## Was macht dieses Template?
   - Beschreibung
   - Features
   - Use Cases

   ## Konfiguration
   - Umgebungsvariablen
   - Volumes
   - Ports

   ## Entwicklung
   - Lokales Setup
   - Tests
   - Debugging
   ```

3. **Dokumentierte Umgebungsvariablen**
   ```dockerfile
   # ENV-Variablen mit Defaults
   ENV NODE_ENV=production \
       PORT=8080 \
       LOG_LEVEL=info
   ```

### Testing

1. **Health Checks definieren**
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:8080/health || exit 1
   ```

2. **Test-Script erstellen**
   ```bash
   #!/bin/bash
   # test-template.sh

   IMAGE="user-template-xyz:latest"
   CONTAINER="test-xyz"

   # Build
   docker build -t $IMAGE .

   # Run
   docker run -d -p 8080:8080 --name $CONTAINER $IMAGE

   # Wait
   sleep 5

   # Test
   curl -f http://localhost:8080 || exit 1

   # Cleanup
   docker stop $CONTAINER && docker rm $CONTAINER

   echo "✅ Template funktioniert!"
   ```

3. **Automatisierte Tests (optional)**
   ```bash
   # CI/CD Pipeline (GitHub Actions, GitLab CI)
   # .github/workflows/test-templates.yml

   name: Test Templates
   on: [push]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Test Template XYZ
           run: bash user-template-xyz/test-template.sh
   ```

---

## Zusammenfassung

### Schnell-Anleitung

```bash
# 1. Verzeichnis erstellen
mkdir user-template-myapp

# 2. Dockerfile erstellen (Port 8080, unprivileged user)
nano user-template-myapp/Dockerfile

# 3. Assets hinzufügen
cp index.html user-template-myapp/

# 4. .env aktualisieren
# USER_TEMPLATE_IMAGES="...;user-template-myapp:latest"

# 5. templates.json aktualisieren
# { "type": "template-myapp", "image": "...", ... }

# 6. Bauen & Testen
docker build -t user-template-myapp:latest user-template-myapp/
docker run -d -p 8080:8080 --name test user-template-myapp:latest
curl http://localhost:8080
docker stop test && docker rm test

# 7. Committen
git add user-template-myapp/ .env templates.json
git commit -m "feat: add template-myapp"
git push

# 8. Auf Server deployen
ssh user@server
cd /volume1/docker/spawner
git pull
docker build -t user-template-myapp:latest user-template-myapp/
docker cp .env spawner:/app/.env
docker cp templates.json spawner:/app/templates.json
docker-compose restart spawner
```

### Checkliste

- [ ] Template-Verzeichnis `user-template-<name>/` erstellt
- [ ] Dockerfile mit Port 8080 und unprivileged user
- [ ] Template lokal gebaut und getestet
- [ ] `.env` → `USER_TEMPLATE_IMAGES` aktualisiert
- [ ] `templates.json` mit Metadaten erweitert
- [ ] Änderungen committed und gepusht
- [ ] Auf Server deployed (git pull + docker cp + restart)
- [ ] Dashboard überprüft (Template sichtbar?)
- [ ] Container erfolgreich erstellt und erreichbar

---

## Support & Weitere Informationen

- **Hauptdokumentation**: `docs/install/DEPLOYMENT_GUIDE.md`
- **Architektur**: `CLAUDE.md`
- **Troubleshooting**: `docs/install/DEPLOYMENT_GUIDE.md#troubleshooting`
- **API-Dokumentation**: `docs/api/` (falls vorhanden)

Bei Fragen: Issue auf GitHub/Gitea erstellen oder Admin kontaktieren.
