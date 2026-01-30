# Installation

Anleitung zur Installation und Aktualisierung des Container Spawner.

## Inhaltsverzeichnis

- [Voraussetzungen](#voraussetzungen)
- [Neuinstallation](#neuinstallation)
- [Update/Upgrade](#updateupgrade)
- [Umgebungsvariablen](#umgebungsvariablen)
- [Manuelle Installation](#manuelle-installation)
- [Troubleshooting](#troubleshooting)

---

## Voraussetzungen

### Hardware

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| RAM | 2 GB | 4+ GB |
| Disk | 20 GB | 50+ GB |
| CPU | 2 Cores | 4+ Cores |

### Software

- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Git**: Fuer Repository-Clone
- **Traefik**: Version 2.x oder 3.x (laufend)
- **curl** oder **wget**: Fuer Installationsskript

### Netzwerk

- **Port 5000**: Spawner-Service (intern)
- **Port 80/443**: Traefik Entrypoints
- **Docker-Netzwerk**: Traefik-Netzwerk muss existieren (Standard: `web`)
- **DNS**: Wildcard-DNS fuer Subdomains oder manuelle Eintraege

---

## Neuinstallation

### Schnellstart (Ein-Befehl-Installation)

```bash
# In ein leeres Verzeichnis wechseln
mkdir spawner && cd spawner

# Installationsskript ausfuehren
curl -sSL https://gitea.iotxs.de/RainerWieland/spawner/raw/branch/main/install.sh | bash
```

Das Skript erkennt automatisch, dass keine `.env` existiert und:
1. Laedt `.env.example` herunter
2. Gibt Anweisungen zur Konfiguration

### Konfiguration anpassen

```bash
# Vorlage kopieren
cp .env.example .env

# Werte anpassen
nano .env
```

**Wichtig**: Mindestens diese Werte anpassen:

```bash
# Secret-Key generieren
python3 -c "import secrets; print(secrets.token_hex(32))"

# In .env eintragen:
SECRET_KEY=<generierter-key>
BASE_DOMAIN=deine-domain.de
SPAWNER_SUBDOMAIN=coder
TRAEFIK_NETWORK=web  # Name deines Traefik-Netzwerks
```

### Installation abschliessen

```bash
bash install.sh
```

Das Skript:
1. Klont das Repository
2. Erstellt Verzeichnisse und setzt Berechtigungen (`data/`, `logs/`, `.env`)
3. Prueft/erstellt Docker-Netzwerk
4. Baut alle Docker-Images
5. Startet die Container

---

## Update/Upgrade

### Automatisches Update

```bash
cd /pfad/zu/spawner
bash install.sh
```

Das Skript erkennt automatisch ein bestehendes Git-Repository und:
1. Holt neueste Aenderungen (`git pull`)
2. Prueft/aktualisiert Verzeichnisrechte
3. Baut Images neu
4. Startet Container neu

### Manuelles Update

```bash
cd /pfad/zu/spawner

# Aenderungen holen
git fetch origin
git pull origin main

# Images neu bauen
docker-compose down
docker build --no-cache -t user-service-template:latest ./user-template/
docker-compose build

# Container starten
docker-compose up -d
```

### Rollback

```bash
# Zu spezifischer Version zurueck
git checkout v0.1.0
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Umgebungsvariablen

### Pflicht-Variablen

| Variable | Beschreibung | Beispiel |
|----------|--------------|----------|
| `SECRET_KEY` | Flask Session Secret | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `BASE_DOMAIN` | Haupt-Domain | `example.com` |
| `SPAWNER_SUBDOMAIN` | Subdomain fuer Spawner-UI | `coder` |
| `TRAEFIK_NETWORK` | Docker-Netzwerk fuer Traefik | `web` |

### Traefik-Variablen

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `TRAEFIK_CERTRESOLVER` | `lets-encrypt` | Name des Certificate Resolvers aus traefik.yml |
| `TRAEFIK_ENTRYPOINT` | `websecure` | HTTPS Entrypoint Name |

### Optionale Variablen

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `USER_TEMPLATE_IMAGE` | `user-service-template:latest` | Docker-Image fuer User-Container |
| `DEFAULT_MEMORY_LIMIT` | `512m` | RAM-Limit pro Container |
| `DEFAULT_CPU_QUOTA` | `50000` | CPU-Quota (50000 = 0.5 CPU) |
| `SPAWNER_PORT` | `5000` | Interner Port des Spawners |
| `LOG_LEVEL` | `INFO` | Log-Level (DEBUG, INFO, WARNING, ERROR) |
| `JWT_ACCESS_TOKEN_EXPIRES` | `3600` | JWT Token Gueltigkeitsdauer (Sekunden) |
| `CONTAINER_IDLE_TIMEOUT` | `3600` | Timeout in Sekunden (noch nicht implementiert) |

### User-Templates

Es stehen zwei Templates fuer User-Container zur Verfuegung:

| Image | Verzeichnis | Beschreibung |
|-------|-------------|--------------|
| `user-service-template:latest` | `user-template/` | Einfache nginx-Willkommensseite (Standard) |
| `user-template-next:latest` | `user-template-next/` | Moderne Next.js React-Anwendung |

Um ein anderes Template zu verwenden, aendere `USER_TEMPLATE_IMAGE` in `.env`:

```bash
USER_TEMPLATE_IMAGE=user-template-next:latest
```

### Produktions-Variablen

| Variable | Beschreibung |
|----------|--------------|
| `DATABASE_URL` | PostgreSQL-Verbindung (statt SQLite) |
| `JWT_SECRET_KEY` | Separater JWT-Secret |
| `CORS_ORIGINS` | Erlaubte CORS-Origins |
| `DOCKER_HOST` | Docker Socket Pfad (Standard: unix:///var/run/docker.sock) |

---

## Manuelle Installation

Falls das Installationsskript nicht verwendet werden kann:

```bash
# 1. Repository klonen
git clone https://gitea.iotxs.de/RainerWieland/spawner.git
cd spawner

# 2. Konfiguration erstellen
cp .env.example .env
nano .env  # Werte anpassen

# 3. Verzeichnisse und Rechte setzen
mkdir -p data logs
chmod 755 data logs
chmod 600 .env

# 4. Docker-Netzwerk pruefen
docker network ls | grep web
# Falls nicht vorhanden:
docker network create web

# 5. User-Template Images bauen
docker build -t user-service-template:latest ./user-template/
docker build -t user-template-next:latest ./user-template-next/  # Optional

# 6. Spawner bauen und starten
docker-compose build
docker-compose up -d

# 7. Logs pruefen
docker-compose logs -f spawner
```

---

## Troubleshooting

### Spawner startet nicht

```bash
# Logs pruefen
docker-compose logs spawner

# Health-Check
curl http://localhost:5000/health
```

**Haeufige Ursachen**:
- `.env` fehlt oder hat falsche Werte
- Docker-Socket nicht gemountet
- Netzwerk existiert nicht

### Container wird nicht erstellt

```bash
# Docker-Verbindung testen
docker ps

# Template-Image pruefen
docker images | grep user-service-template
```

**Haeufige Ursachen**:
- Template-Image nicht gebaut
- Netzwerk-Name falsch in `.env`

### Traefik routet nicht

```bash
# Traefik-Dashboard pruefen (falls aktiviert)
# Container-Labels pruefen
docker inspect spawner | jq '.[0].Config.Labels'

# Netzwerk-Verbindung pruefen
docker network inspect web | grep spawner
```

**Haeufige Ursachen**:
- Container nicht im Traefik-Netzwerk
- Labels falsch konfiguriert
- DNS nicht konfiguriert

### Datenbank-Fehler

```bash
# In Container einsteigen
docker exec -it spawner bash

# DB manuell initialisieren
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## Verzeichnisrechte

Das Installationsskript setzt die Berechtigungen automatisch. Bei manueller Installation muessen diese selbst gesetzt werden.

### Vom Skript automatisch gesetzt

| Pfad | Berechtigung | Zweck |
|------|--------------|-------|
| `./data/` | `755` | SQLite-Datenbank |
| `./logs/` | `755` | Log-Dateien |
| `./.env` | `600` | Sensible Konfiguration (nur Owner) |
| `./install.sh` | `+x` | Ausfuehrbar |

### Vom System benoetigt

| Pfad | Berechtigung | Zweck |
|------|--------------|-------|
| `/var/run/docker.sock` | `rw` | Docker-API-Zugriff |

### Manuelle Rechte setzen

```bash
# Verzeichnisse erstellen
mkdir -p data logs

# Berechtigungen setzen
chmod 755 data logs
chmod 600 .env
chmod +x install.sh
```

### Non-Root Container

Falls der Spawner-Container als non-root User laeuft, muessen die Verzeichnisse fuer diesen beschreibbar sein:

```bash
# Option 1: Volle Schreibrechte (einfach, aber weniger sicher)
chmod 777 data logs

# Option 2: Owner auf Container-UID setzen (empfohlen)
# UID des Container-Users ermitteln und setzen
chown 1000:1000 data logs
```

### Synology NAS Hinweis

Auf Synology NAS (DSM) kann es noetig sein, die Verzeichnisse dem Docker-User zuzuweisen:

```bash
# Als root auf der Synology
chown -R 1000:1000 /volume1/docker/spawner/data
chown -R 1000:1000 /volume1/docker/spawner/logs
```

---

Zurueck zur [Dokumentations-Uebersicht](../README.md)
