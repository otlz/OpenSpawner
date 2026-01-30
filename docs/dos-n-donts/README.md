# Best Practices - Dos and Don'ts

Empfehlungen fuer den sicheren und effizienten Betrieb des Container Spawners.

## Inhaltsverzeichnis

- [Produktions-Checkliste](#produktions-checkliste)
- [Dos - Empfohlene Praktiken](#dos---empfohlene-praktiken)
- [Don'ts - Zu vermeiden](#donts---zu-vermeiden)
- [Haeufige Fehler](#haeufige-fehler)

---

## Produktions-Checkliste

### Vor dem Go-Live

| Kategorie | Aufgabe | Status |
|-----------|---------|--------|
| **Sicherheit** | SECRET_KEY generiert (min. 32 Bytes) | [ ] |
| | `.env` nicht im Repository | [ ] |
| | HTTPS aktiviert | [ ] |
| | Docker Socket Proxy konfiguriert | [ ] |
| **Konfiguration** | BASE_DOMAIN korrekt | [ ] |
| | TRAEFIK_NETWORK existiert | [ ] |
| | Resource-Limits angemessen | [ ] |
| **Infrastruktur** | DNS-Eintraege (Wildcard) | [ ] |
| | Traefik laeuft stabil | [ ] |
| | Firewall konfiguriert | [ ] |
| **Monitoring** | Health-Check funktioniert | [ ] |
| | Logs werden geschrieben | [ ] |
| | Backup-Strategie | [ ] |
| **Testing** | Login/Signup funktioniert | [ ] |
| | Container wird erstellt | [ ] |
| | Subdomain erreichbar | [ ] |

---

## Dos - Empfohlene Praktiken

### Konfiguration

**DO: SECRET_KEY sicher generieren**

```bash
# Guter Key (32 Bytes = 64 Hex-Zeichen)
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**DO: Umgebungsvariablen fuer sensible Daten**

```bash
# In .env (nie committen!)
SECRET_KEY=abc123...
DATABASE_URL=postgresql://...
```

**DO: Resource-Limits setzen**

```bash
# In .env
DEFAULT_MEMORY_LIMIT=512m
DEFAULT_CPU_QUOTA=50000
```

---

### Deployment

**DO: Docker Compose fuer Orchestrierung**

```bash
# Nicht einzelne docker run Befehle
docker-compose up -d
docker-compose logs -f
docker-compose down
```

**DO: Images taggen**

```bash
# Versionierte Tags statt :latest in Produktion
docker build -t spawner:0.1.0 .
docker build -t spawner:latest .
```

**DO: Health-Checks nutzen**

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

### Monitoring

**DO: Logs zentralisieren**

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**DO: Regelmaessige Backups**

```bash
# Cronjob fuer taegliches Backup
0 2 * * * /pfad/zu/spawner/backup.sh
```

**DO: Disk-Space ueberwachen**

```bash
# Docker-Ressourcen pruefen
docker system df
docker system prune -f  # Vorsicht in Produktion!
```

---

### Sicherheit

**DO: HTTPS erzwingen**

```yaml
# Traefik-Labels
- "traefik.http.routers.spawner.entrypoints=websecure"
- "traefik.http.routers.spawner.tls=true"
```

**DO: Minimale Berechtigungen**

```yaml
# Docker Socket Proxy statt direktem Zugriff
DOCKER_HOST: tcp://docker-proxy:2375
```

**DO: Container als Non-Root**

```dockerfile
# Im User-Template
USER nginx
# oder
RUN useradd -m appuser && chown -R appuser /app
USER appuser
```

---

## Don'ts - Zu vermeiden

### Konfiguration

**DON'T: Hardcoded Secrets**

```python
# NIEMALS!
SECRET_KEY = "supersecret123"
```

**DON'T: Debug-Mode in Produktion**

```python
# NIEMALS in Produktion!
app.run(debug=True)
FLASK_DEBUG=1
```

**DON'T: Schwache Keys**

```bash
# ZU KURZ / ZU EINFACH
SECRET_KEY=test
SECRET_KEY=12345
```

---

### Deployment

**DON'T: Manuelles Container-Management**

```bash
# Vermeiden - besser docker-compose
docker run -d --name spawner ...
docker stop spawner
docker rm spawner
```

**DON'T: Unversionierte Images in Produktion**

```bash
# Vermeiden
USER_TEMPLATE_IMAGE=user-service-template:latest

# Besser
USER_TEMPLATE_IMAGE=user-service-template:0.1.0
```

**DON'T: Ohne Health-Checks deployen**

---

### Sicherheit

**DON'T: Docker Socket direkt exponieren**

```yaml
# NIEMALS!
ports:
  - "2375:2375"  # Docker API oeffentlich
```

**DON'T: .env committen**

```bash
# .gitignore MUSS enthalten:
.env
*.db
```

**DON'T: Container ohne Resource-Limits**

```python
# Vermeiden - DoS-Risiko
container = client.containers.run(image)

# Besser
container = client.containers.run(
    image,
    mem_limit='512m',
    cpu_quota=50000
)
```

**DON'T: Root-Container in Produktion**

---

### Wartung

**DON'T: Logs ignorieren**

```bash
# Regelmaessig pruefen!
docker-compose logs --tail=100 spawner
```

**DON'T: Backups vergessen**

**DON'T: Updates aufschieben**

```bash
# Regelmaessig aktualisieren
git pull origin main
docker-compose build
docker-compose up -d
```

---

## Haeufige Fehler

### 1. "Connection refused" beim Health-Check

**Ursache**: Container noch nicht bereit

**Loesung**: Warten oder start_period erhoehen:

```yaml
healthcheck:
  start_period: 30s
```

---

### 2. "Network not found"

**Ursache**: Traefik-Netzwerk existiert nicht

**Loesung**:

```bash
docker network create web
# Oder TRAEFIK_NETWORK in .env anpassen
```

---

### 3. "Permission denied" bei Docker Socket

**Ursache**: Spawner-Container hat keinen Zugriff

**Loesung**:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:rw
```

Oder Docker-Gruppe:

```bash
sudo usermod -aG docker $USER
```

---

### 4. "Image not found"

**Ursache**: User-Template nicht gebaut

**Loesung**:

```bash
docker build -t user-service-template:latest ./user-template/
```

---

### 5. Subdomain nicht erreichbar

**Ursache**: DNS oder Traefik-Konfiguration

**Diagnose**:

```bash
# DNS pruefen
nslookup username.example.com

# Traefik-Routes pruefen (Dashboard)
# Container-Labels pruefen
docker inspect user-xxx | jq '.[0].Config.Labels'
```

---

### 6. "Database locked"

**Ursache**: SQLite-Konkurrenzzugriff

**Loesung fuer Produktion**: PostgreSQL verwenden:

```bash
DATABASE_URL=postgresql://spawner:pass@postgres:5432/spawner
```

---

### 7. Container startet, aber Service nicht erreichbar

**Ursache**: Falscher Port in Labels

**Loesung**: Port in `container_manager.py` pruefen:

```python
# Muss mit EXPOSE im Dockerfile uebereinstimmen
f'traefik.http.services.user{user_id}.loadbalancer.server.port': '8080'
```

---

## Quick Reference

### Nuetzliche Befehle

```bash
# Status
docker-compose ps
docker ps --filter 'label=spawner.managed=true'

# Logs
docker-compose logs -f spawner
docker logs user-xxx-1

# Neustart
docker-compose restart spawner

# Komplett neu
docker-compose down
docker-compose up -d --build

# Cleanup
docker system prune -f
docker volume prune -f
```

### Debugging

```bash
# In Container einsteigen
docker exec -it spawner bash

# Python-Shell
docker exec -it spawner python

# Datenbank
docker exec spawner sqlite3 /app/data/users.db ".tables"
```

---

Zurueck zur [Dokumentations-Uebersicht](../README.md)
