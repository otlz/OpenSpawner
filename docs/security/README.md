# Sicherheit

Sicherheitsrisiken und Gegenmassnahmen fuer den Container Spawner.

## Inhaltsverzeichnis

- [Docker Socket Risiko](#docker-socket-risiko)
- [Container Isolation](#container-isolation)
- [Session-Sicherheit](#session-sicherheit)
- [Input-Validierung](#input-validierung)
- [Secrets Management](#secrets-management)
- [Netzwerksicherheit](#netzwerksicherheit)
- [Sicherheits-Checkliste](#sicherheits-checkliste)

---

## Docker Socket Risiko

### Problem

Der Spawner benoetigt Zugriff auf `/var/run/docker.sock` um Container zu erstellen. Dies entspricht Root-Privilegien auf dem Host-System.

### Risiken

- Ein kompromittierter Spawner kann alle Container kontrollieren
- Potenzieller Container-Escape moeglich
- Zugriff auf Host-Dateisystem via Volume-Mounts

### Gegenmassnahmen

**Option 1: Docker Socket Proxy (Empfohlen fuer Produktion)**

```yaml
services:
  docker-proxy:
    image: tecnativa/docker-socket-proxy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      CONTAINERS: 1    # Container-Operationen erlauben
      NETWORKS: 1      # Netzwerk-Operationen erlauben
      SERVICES: 0      # Swarm-Services blockieren
      SWARM: 0         # Swarm-Operationen blockieren
      VOLUMES: 0       # Volume-Operationen blockieren
      IMAGES: 1        # Image-Operationen erlauben
    networks:
      - internal

  spawner:
    environment:
      DOCKER_HOST: tcp://docker-proxy:2375
    networks:
      - internal
      - web

networks:
  internal:
    internal: true  # Kein externer Zugriff
```

**Option 2: Minimale Permissions**

```bash
# User-Namespace aktivieren (in /etc/docker/daemon.json)
{
  "userns-remap": "default"
}
```

---

## Container Isolation

### Aktuelle Massnahmen

| Massnahme | Status | Beschreibung |
|-----------|--------|--------------|
| Memory-Limit | Aktiv | Standard 512m pro Container |
| CPU-Quota | Aktiv | Standard 0.5 CPU pro Container |
| Restart-Policy | Aktiv | `unless-stopped` |
| Network-Isolation | Teilweise | Alle im gleichen Traefik-Netzwerk |

### Empfehlungen

**Read-Only Filesystem**

```python
# In container_manager.py
container = client.containers.run(
    read_only=True,
    tmpfs={'/tmp': 'size=100M,noexec'}
)
```

**Security Options**

```python
container = client.containers.run(
    security_opt=['no-new-privileges:true'],
    cap_drop=['ALL'],
    cap_add=['NET_BIND_SERVICE']  # Nur wenn noetig
)
```

**Separate Netzwerke pro User** (Fuer hohe Isolation)

```python
# Dediziertes Netzwerk pro User
user_network = f"user-{username}-network"
client.networks.create(user_network, driver='bridge', internal=True)
```

---

## Session-Sicherheit

### Aktuelle Konfiguration

```python
SESSION_COOKIE_SECURE = True       # Nur HTTPS (Produktion)
SESSION_COOKIE_HTTPONLY = True     # Kein JavaScript-Zugriff
SESSION_COOKIE_SAMESITE = 'Lax'    # CSRF-Schutz
PERMANENT_SESSION_LIFETIME = 3600  # 1h Timeout
```

### Empfehlungen

- **SECRET_KEY**: Mindestens 32 Bytes, zufaellig generiert
- **HTTPS erzwingen**: Immer in Produktion
- **Session-Rotation**: Nach Login neue Session-ID

```python
# Session-Rotation nach Login
from flask import session
session.regenerate()
```

---

## Input-Validierung

### Aktuelle Risiken

- Username wird direkt in Container-Namen verwendet
- Minimale Validierung bei Registrierung

### Empfohlene Validierung

```python
import re

def validate_username(username):
    """Validiert Username gegen Injection-Angriffe"""
    if not username:
        return False, "Username erforderlich"

    if len(username) < 3 or len(username) > 20:
        return False, "Username muss 3-20 Zeichen lang sein"

    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Nur Buchstaben, Zahlen und Unterstriche erlaubt"

    # Reservierte Namen
    reserved = ['admin', 'root', 'system', 'spawner', 'traefik']
    if username.lower() in reserved:
        return False, "Dieser Username ist reserviert"

    return True, None

# Container-Name sicher erstellen
def safe_container_name(username, user_id):
    """Erstellt sicheren Container-Namen"""
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', username)
    return f"user-{safe_name}-{user_id}"
```

---

## Secrets Management

### Entwicklung vs. Produktion

| Umgebung | Methode |
|----------|---------|
| Entwicklung | `.env` Datei (nie committen!) |
| Produktion | Docker Secrets oder Vault |

### Docker Secrets (Produktion)

```bash
# Secret erstellen
echo "supersecretkey" | docker secret create flask_secret -

# In docker-compose.yml
services:
  spawner:
    secrets:
      - flask_secret
    environment:
      SECRET_KEY_FILE: /run/secrets/flask_secret

secrets:
  flask_secret:
    external: true
```

### Environment-Variable Sicherheit

```bash
# .env NIEMALS committen
echo ".env" >> .gitignore

# Sensible Werte nicht in Logs
LOG_LEVEL=INFO  # Nicht DEBUG in Produktion
```

---

## Netzwerksicherheit

### Traefik-Konfiguration

**HTTPS erzwingen**

```yaml
# In container_manager.py Labels
labels={
    'traefik.http.routers.user{id}.entrypoints': 'websecure',
    'traefik.http.routers.user{id}.tls': 'true',
    'traefik.http.routers.user{id}.tls.certresolver': 'letsencrypt',

    # HTTP zu HTTPS Redirect
    'traefik.http.middlewares.redirect-https.redirectscheme.scheme': 'https',
    'traefik.http.routers.user{id}-http.middlewares': 'redirect-https'
}
```

**Rate-Limiting via Traefik**

```yaml
labels={
    'traefik.http.middlewares.ratelimit.ratelimit.average': '100',
    'traefik.http.middlewares.ratelimit.ratelimit.burst': '50',
    'traefik.http.routers.spawner.middlewares': 'ratelimit'
}
```

### Firewall-Empfehlungen

```bash
# Nur Traefik-Ports oeffentlich
ufw allow 80/tcp
ufw allow 443/tcp

# Docker-Socket NIE oeffentlich!
# Port 5000 nur intern (ueber Traefik)
```

---

## Sicherheits-Checkliste

### Vor Go-Live

- [ ] SECRET_KEY generiert (32+ Bytes)
- [ ] `.env` nicht im Repository
- [ ] HTTPS konfiguriert und getestet
- [ ] Docker Socket Proxy aktiviert (Produktion)
- [ ] Resource-Limits angemessen
- [ ] Input-Validierung implementiert
- [ ] Rate-Limiting aktiv
- [ ] Logs auf sensible Daten geprueft
- [ ] Backup-Strategie implementiert

### Regelmaessig pruefen

- [ ] Container auf Vulnerabilities scannen
- [ ] Dependencies aktualisieren
- [ ] Logs auf verdaechtige Aktivitaeten pruefen
- [ ] Unbefugte Container entfernen

### Vulnerability Scanning

```bash
# Mit Trivy scannen
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image spawner:latest

docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image user-service-template:latest
```

---

## Incident Response

### Bei Verdacht auf Kompromittierung

1. **Spawner stoppen**: `docker-compose down`
2. **Alle User-Container stoppen**: `docker stop $(docker ps -q --filter 'label=spawner.managed=true')`
3. **Logs sichern**: `docker-compose logs > incident-logs.txt`
4. **Secrets rotieren**: Neue SECRET_KEY generieren
5. **Analyse durchfuehren**
6. **Behobene Version deployen**

### Kontakt

Bei Sicherheitsproblemen: Issue im Repository erstellen (privat falls sensibel)

---

Zurueck zur [Dokumentations-Uebersicht](../README.md)
