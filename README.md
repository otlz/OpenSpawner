---
tags: SPAWNER unter Docker
---

# DAS SPAWNER-PROJEKT V0.1
*27.01.2026 rwd*
![](https://hedgedoc.wieland.org/uploads/7aaace93-f7d9-4fe9-9553-94b2fa2e7031.png)


---

## Inhaltsverzeichnis

1. [Projektübersicht](#projektübersicht)
2. [Architektur](#architektur)
3. [Voraussetzungen](#voraussetzungen)
4. [Installation](#installation)
5. [Konfiguration](#konfiguration)
6. [Dateistruktur](#dateistruktur)
7. [Komponenten im Detail](#komponenten-im-detail)
8. [Workflow](#workflow)
9. [Traefik-Integration](#traefik-integration)
10. [Sicherheit](#sicherheit)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)
13. [Erweiterungen](#erweiterungen)
14. [Best Practices](#best-practices)

---

## Projektübersicht

Der **Docker Container Spawner** ist eine leichtgewichtige Lösung zum automatischen Bereitstellen von isolierten Docker-Containern für einzelne Benutzer. Nach erfolgreicher Authentifizierung erhält jeder Benutzer einen eigenen Container mit einem dedizierten Webdienst, der über eine personalisierte Subdomain erreichbar ist.

Das System basiert auf einer Flask-Architektur, die nach einer erfolgreichen Anmeldung automatisch dedizierte Container aus vordefinierten Vorlagen erstellt. Die Anbindung erfolgt über den **Reverse-Proxy Traefik**, der den Datenverkehr dynamisch über personalisierte Subdomains an die jeweiligen Dienste weiterleitet. Zu den Sicherheitsmerkmalen gehören strikte Ressourcenlimits für RAM und CPU sowie eine verschlüsselte Nutzerverwaltung via SQLite. Die Dokumentation beschreibt zudem umfassende Wartungsfunktionen wie das Lifecycle-Management von Containern und Best Practices für den produktiven Einsatz. 

Anwendungsgebiete finden sich vor allem in der Bereitstellung von
- Lernumgebungen
- Sandboxes
- SaaS-Plattformen

---


### Hauptfunktionen

- **User-Management**: Registrierung und Login mit sicherer Passwort-Speicherung
- **Automatisches Container-Spawning**: Jeder User erhält einen eigenen Docker-Container
- **Dynamisches Routing**: Traefik routet automatisch zu den User-Containern
- **Resource-Management**: CPU- und RAM-Limits pro Container
- **Lifecycle-Management**: Starten, Stoppen und Neustarten von User-Containern
- **Template-basiert**: Neue User-Container aus vorgefertigten Images

### Use Cases

- **Entwicklungsumgebungen**: Isolierte Dev-Spaces für Entwickler
- **SaaS-Anwendungen**: Multi-Tenant-Webservices
- **Lernplattformen**: Übungsumgebungen für Schulungen
- **CI/CD-Pipelines**: On-Demand Build-Umgebungen
- **Sandbox-Umgebungen**: Sichere Test-Environments

---

## Architektur

### Komponenten-Übersicht

```flow
st=>start: Browser
e=>end: End
op=>operation: Traefik
:80 / :443
op2=>operation: Spawner Service
Flask + Docker SDK
:5000 
op3=>operation: Docker Daemon
op4=>operation: User Containers 
USER-I | USER-II | USER-III | USER-nnn|

st->op->op2->op3->op4
```

### Datenfluss

1. **Login**: User meldet sich über Web-UI an
2. **Authentication**: Flask validiert Credentials gegen SQLite-DB
3. **Container-Spawn**: Docker SDK startet neuen Container aus Template
4. **Label-Injection**: Traefik-Labels werden beim Container-Start gesetzt
5. **Auto-Discovery**: Traefik erkennt neuen Container und erstellt Route
6. **Redirect**: User wird zu persönlicher Subdomain weitergeleitet

### Netzwerk-Architektur

Alle Services laufen im gleichen Docker-Netzwerk (\`traefik-network\`), damit Traefik die User-Container erreichen kann:

```
traefik-network (bridge)
├── traefik (Reverse Proxy)
├── spawner (Management Service)
├── user-alice-1 (User Container)
├── user-bob-2 (User Container)
└── user-charlie-3 (User Container)
```

---

## Voraussetzungen

### Hardware

- **Min. 2 GB RAM**: Für Spawner + mehrere User-Container
- **Min. 20 GB Disk**: Für Images und Container-Volumes
- **Multi-Core CPU**: Empfohlen für parallele Container

### Software

- **Docker**: Version 20.10+ 
- **Docker Compose**: Version 2.0+
- **Python**: 3.11+ (im Container enthalten)
- **Traefik**: Version 2.x oder 3.x (optional, aber empfohlen)

### Netzwerk

- **Port 5000**: Spawner Web-UI (oder via Traefik)
- **Port 80/443**: Traefik (für User-Container-Routing)
- **Wildcard-DNS** oder \`/etc/hosts\`-Einträge für Subdomains

---

## Installation

### Schritt 1: Projekt-Setup

```bash
# Repository erstellen
mkdir docker-spawner
cd docker-spawner

# Verzeichnisstruktur anlegen
mkdir -p spawner/{templates,user-template,data}
cd spawner
```

### Schritt 2: Dateien erstellen

Erstelle alle Dateien aus der Projektstruktur (siehe [Dateistruktur](#dateistruktur)).

### Schritt 3: Traefik-Netzwerk erstellen

```bash
docker network create traefik-network
```

### Schritt 4: User-Template-Image bauen

```bash
cd user-template
docker build -t user-service-template:latest .
cd ..
```

### Schritt 5: Spawner starten

```bash
docker-compose up -d --build
```

### Schritt 6: Traefik starten (falls noch nicht vorhanden)

```bash
# Minimal Traefik docker-compose.yml
cat > traefik-compose.yml <<EOF
version: '3.8'
services:
  traefik:
    image: traefik:v3.0
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command:
      - --api.insecure=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
    networks:
      - traefik-network

networks:
  traefik-network:
    external: true
EOF

docker-compose -f traefik-compose.yml up -d
```

### Schritt 7: DNS konfigurieren (lokal)

```bash
# Für lokale Tests: /etc/hosts bearbeiten
sudo nano /etc/hosts

# Hinzufügen:
127.0.0.1 spawner.localhost
127.0.0.1 testuser.localhost
127.0.0.1 alice.localhost
```

### Schritt 8: Zugriff testen

Browser öffnen: \`http://spawner.localhost\` (oder \`http://localhost:5000\`)

---

## Konfiguration

### Environment-Variablen

Die Konfiguration erfolgt über \`.env\` oder \`docker-compose.yml\`:

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| \`SECRET_KEY\` | \`dev-secret-key\` | Flask Session Secret (ÄNDERN in Produktion!) |
| \`BASE_DOMAIN\` | \`localhost\` | Domain für User-Subdomains |
| \`TRAEFIK_NETWORK\` | \`traefik-network\` | Docker-Netzwerk für Traefik |
| \`USER_TEMPLATE_IMAGE\` | \`user-service-template:latest\` | Docker-Image für User-Container |
| \`DOCKER_SOCKET\` | \`unix://var/run/docker.sock\` | Docker-API-Socket |

### .env Beispiel

```bash
SECRET_KEY=supersecret123changeme
BASE_DOMAIN=example.com
TRAEFIK_NETWORK=traefik-network
USER_TEMPLATE_IMAGE=user-service-template:latest
```

### Produktions-Konfiguration

In \`config.py\` anpassen:

```python
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@db:5432/spawner'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

---

## Dateistruktur

```
spawner/
├── Dockerfile                 # Container für Spawner-Service
├── docker-compose.yml         # Orchestrierung
├── requirements.txt           # Python-Dependencies
├── .env                       # Environment-Variablen (nicht committen!)
│
├── app.py                     # Flask-Hauptanwendung
├── auth.py                    # Authentifizierungs-Blueprint
├── container_manager.py       # Docker-Container-Management
├── models.py                  # SQLAlchemy User-Modell
├── config.py                  # Konfigurationsklassen
│
├── templates/                 # Jinja2-Templates
│   ├── login.html
│   ├── signup.html
│   └── dashboard.html
│
├── user-template/             # Template für User-Container
│   └── Dockerfile
│
├── data/                      # Persistente Daten
│   └── users.db              # SQLite-Datenbank (auto-generiert)
│
└── logs/                      # Logs (optional)
    └── spawner.log
```

---

## Komponenten im Detail

### 1. app.py - Flask-Hauptanwendung

**Funktion**: Einstiegspunkt, registriert Blueprints, initialisiert Extensions

**Wichtige Routen**:

- \`/\`: Redirect zu Dashboard oder Login
- \`/dashboard\`: Zeigt Container-Status und Service-URL
- \`/container/restart\`: Neustart des User-Containers

**Flask-Extensions**:

- \`Flask-Login\`: Session-Management
- \`Flask-SQLAlchemy\`: Datenbank-ORM
- \`Flask-WTF\`: CSRF-Protection (optional)

### 2. auth.py - Authentifizierung

**Routes**:

- \`/login\` (GET/POST): User-Login
- \`/signup\` (GET/POST): Neue User-Registrierung
- \`/logout\`: Session beenden

**Workflow bei Login**:

1. Credentials validieren gegen DB
2. Flask-Login Session erstellen
3. Container spawnen falls noch nicht vorhanden
4. Redirect zu Dashboard

**Workflow bei Signup**:

1. Username/Email-Uniqueness prüfen
2. Passwort hashen (bcrypt via werkzeug)
3. User in DB speichern
4. Container aus Template spawnen
5. Container-ID in User-Record speichern
6. Auto-Login

### 3. container_manager.py - Docker-Management

**Klasse**: \`ContainerManager\`

**Methoden**:

```python
spawn_container(user_id, username)
# Startet neuen Container mit Traefik-Labels
# Returns: (container_id, port)

stop_container(container_id)
# Stoppt Container graceful (10s timeout)

remove_container(container_id)
# Entfernt Container komplett

get_container_status(container_id)
# Returns: 'running' | 'exited' | 'not_found'

build_template_for_user(username)
# Baut user-spezifisches Image (optional)
```

**Docker-SDK Features**:

- \`from_env()\`: Automatische Socket-Erkennung
- \`containers.run()\`: Container starten
- \`labels={}\`: Traefik-Routing-Config
- \`mem_limit\`, \`cpu_quota\`: Resource-Limits
- \`restart_policy\`: Auto-Restart bei Absturz

### 4. models.py - Datenbank-Schema

**User-Modell**:

```python
class User:
    id: int                    # Primary Key
    username: str              # Unique
    email: str                 # Unique
    password_hash: str         # bcrypt Hash
    container_id: str          # Docker Container ID
    container_port: int        # Service-Port im Container
    created_at: datetime       # Registration Timestamp
```

**Methoden**:

- \`set_password(password)\`: Hash-Generierung
- \`check_password(password)\`: Validierung
- \`UserMixin\`: Flask-Login Integration

### 5. config.py - Zentrale Konfiguration

**Config-Klasse**:

Enthält alle konfigurierbaren Parameter:

- Datenbank-URI
- Docker-Socket-Pfad
- Template-Image-Name
- Domain-Konfiguration
- Netzwerk-Settings

**Verwendung**:

```python
from config import Config
app.config.from_object(Config)
```

### 6. templates/ - Web-UI

**login.html**:

- Einfaches Login-Formular
- Flash-Messages für Fehler
- Link zu Signup

**signup.html**:

- Registrierungsformular
- Username, Email, Password
- Validation-Hinweise

**dashboard.html**:

- Container-Status-Anzeige
- Link zum User-Service
- Container-Restart-Button
- Logout-Link

---

## Workflow

### User-Registrierung

```
1. User öffnet /signup
2. Füllt Formular aus (Username, Email, Passwort)
3. POST zu /signup
4. Backend:
   a. Validiert Input
   b. Prüft auf Duplikate
   c. Erstellt User-Record mit Hash
   d. Spawnt Container aus Template
   e. Speichert Container-ID
   f. Loggt User automatisch ein
5. Redirect zu /dashboard
6. User sieht Link zu seinem Service
```

### User-Login (existing user)

```
1. User öffnet /login
2. Gibt Credentials ein
3. POST zu /login
4. Backend:
   a. Findet User in DB
   b. Validiert Passwort-Hash
   c. Prüft ob Container existiert
   d. Falls nein: Spawnt neuen Container
   e. Flask-Login Session erstellen
5. Redirect zu /dashboard
6. User klickt auf Service-URL
7. Traefik routet zu User-Container
```

### Container-Lifecycle

```
[User Login]
     │
     ▼
[Container existiert?]
     │
     ├─ Ja ──► [Status prüfen] ──► [Running?]
     │                                 │
     │                                 ├─ Ja ──► [Redirect zu Service]
     │                                 └─ Nein ─► [Container starten]
     │
     └─ Nein ─► [spawn_container()]
                     │
                     ├─ Image pullen
                     ├─ Container erstellen
                     ├─ Labels setzen (Traefik)
                     ├─ Netzwerk verbinden
                     ├─ Resource-Limits setzen
                     └─ Container starten
                            │
                            ▼
                     [Container läuft]
                            │
                            ▼
                     [Traefik entdeckt Container]
                            │
                            ▼
                     [Route wird erstellt]
                            │
                            ▼
                     [Service erreichbar unter subdomain]
```

---

## Traefik-Integration

### Label-basiertes Routing

Bei jedem Container-Start werden Traefik-Labels gesetzt:

```python
labels={
    # Container für Traefik sichtbar machen
    'traefik.enable': 'true',

    # Router-Definition
    'traefik.http.routers.user123.rule': 'Host(\`alice.example.com\`)',
    'traefik.http.routers.user123.entrypoints': 'web',

    # Service-Definition (Backend)
    'traefik.http.services.user123.loadbalancer.server.port': '8080',

    # Custom Labels für Spawner
    'spawner.user_id': '123',
    'spawner.username': 'alice'
}
```

### Traefik-Konfiguration

Minimal \`traefik.yml\`:

```yaml
entryPoints:
  web:
    address: ":80"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false  # Nur Container mit traefik.enable=true
    network: traefik-network

api:
  insecure: true  # Dashboard auf :8080 (nur dev!)
```

### Automatische Service-Discovery

Traefik überwacht Docker-Events:

```
1. Container startet mit Labels
2. Traefik empfängt Docker-Event
3. Traefik parsed Labels
4. Router + Service werden erstellt
5. Route ist sofort aktiv (< 1 Sekunde)
```

### HTTPS mit Let's Encrypt (optional)

Für Produktion in \`traefik.yml\` ergänzen:

```yaml
entryPoints:
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web
```

Labels anpassen:

```python
'traefik.http.routers.user123.entrypoints': 'websecure',
'traefik.http.routers.user123.tls.certresolver': 'letsencrypt'
```

---

## Sicherheit

### Passwort-Sicherheit

- **Hashing**: Werkzeug's \`generate_password_hash()\` (pbkdf2:sha256)
- **Salt**: Automatisch pro Passwort
- **Keine Plaintext-Speicherung**: Nur Hashes in DB

### Container-Isolation

- **User-Namespaces**: Jeder Container läuft mit eigenem UID-Mapping
- **Resource-Limits**: CPU/RAM-Beschränkung verhindert Denial-of-Service
- **Network-Isolation**: Container können sich gegenseitig nicht erreichen (außer via Traefik)
- **Read-only Filesystem** (optional):

```python
container = client.containers.run(
    read_only=True,
    tmpfs={'/tmp': 'size=100M'}
)
```

### Docker-Socket-Sicherheit

**Problem**: Spawner benötigt Zugriff auf \`/var/run/docker.sock\` (Root-Privilegien!)

**Risiken**:
- Container kann alle anderen Container kontrollieren
- Potenzieller Container-Escape

**Mitigations**:

1. **Docker-Socket-Proxy** (empfohlen für Produktion):

```yaml
services:
  docker-proxy:
    image: tecnativa/docker-socket-proxy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      CONTAINERS: 1
      NETWORKS: 1
      SERVICES: 0
      SWARM: 0
      VOLUMES: 0

  spawner:
    environment:
      DOCKER_HOST: tcp://docker-proxy:2375
```

2. **Least Privilege**: Nur notwendige Docker-API-Calls erlauben

3. **Audit-Logging**: Alle Container-Operationen loggen

### Session-Sicherheit

```python
# In config.py
SESSION_COOKIE_SECURE = True      # Nur HTTPS
SESSION_COOKIE_HTTPONLY = True    # Kein JS-Zugriff
SESSION_COOKIE_SAMESITE = 'Lax'   # CSRF-Schutz
PERMANENT_SESSION_LIFETIME = 3600 # 1h Timeout
```

### Input-Validation

```python
# Username: Nur alphanumerisch + underscore
import re
if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
    raise ValueError("Invalid username")

# Container-Name-Injection verhindern
container_name = f"user-{username}-{user_id}".replace('/', '-')
```

### Secrets-Management

**Für Produktion**: Keine Secrets in \`docker-compose.yml\`!

```bash
# Docker Secrets verwenden
echo "supersecretkey" | docker secret create flask_secret -

# In compose:
secrets:
  - flask_secret

services:
  spawner:
    secrets:
      - flask_secret
```

---

## Deployment

### Entwicklung

```bash
# Mit Auto-Reload
docker-compose up

# Logs verfolgen
docker-compose logs -f spawner
```

### Staging

```bash
# .env.staging erstellen
cp .env .env.staging

# Mit staging-Config starten
docker-compose --env-file .env.staging up -d

# Health-Check
curl http://spawner.staging.example.com/health
```

### Produktion

```bash
# Produktions-Image bauen
docker build -t spawner:1.0.0 .

# Mit PostgreSQL statt SQLite
docker-compose -f docker-compose.prod.yml up -d

# Monitoring einbinden
docker-compose -f docker-compose.prod.yml -f monitoring.yml up -d
```

### Multi-Host Deployment (Docker Swarm)

```yaml
# docker-compose.swarm.yml
version: '3.8'
services:
  spawner:
    image: spawner:1.0.0
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.role == manager  # Wegen Docker-Socket
      restart_policy:
        condition: on-failure
```

```bash
docker stack deploy -c docker-compose.swarm.yml spawner-stack
```

### Kubernetes (fortgeschritten)

Für K8s benötigst du:

- **Docker-in-Docker** (DinD) oder
- **Kubernetes-API** statt Docker-SDK
- **Custom Spawner-Logic** für Pods statt Container

Beispiel: JupyterHub's KubeSpawner als Referenz.

---

## Troubleshooting

### Container startet nicht

**Symptom**: \`spawn_container()\` wirft Exception

**Debug**:

```bash
# Spawner-Logs prüfen
docker logs spawner

# Docker-Events live verfolgen
docker events

# Manuell Container starten (Test)
docker run --rm -it user-service-template:latest sh
```

**Häufige Ursachen**:

- Image nicht gefunden: \`docker images | grep user-service-template\`
- Netzwerk existiert nicht: \`docker network ls\`
- Port-Konflikt: Ports bereits belegt
- Keine Docker-Socket-Berechtigung: Volume-Mount prüfen

### Traefik routet nicht

**Symptom**: 404 bei \`http://alice.localhost\`

**Debug**:

```bash
# Traefik-Dashboard öffnen
firefox http://localhost:8080

# Unter "HTTP Routers" prüfen ob user-Route existiert

# Container-Labels prüfen
docker inspect user-alice-1 | jq '.[0].Config.Labels'

# Netzwerk prüfen
docker network inspect traefik-network
```

**Fixes**:

- Container läuft nicht im richtigen Netzwerk: \`network\` in \`spawn_container()\` prüfen
- Labels falsch: Syntax in \`container_manager.py\` korrigieren
- DNS-Problem: \`/etc/hosts\` prüfen

### Datenbank-Fehler

**Symptom**: \`OperationalError: no such table: user\`

**Fix**:

```bash
# In Container einsteigen
docker exec -it spawner bash

# Python-Shell öffnen
python

# DB initialisieren
from app import app, db
with app.app_context():
    db.create_all()
```

### Performance-Probleme

**Symptom**: System langsam bei vielen Usern

**Analyse**:

```bash
# Container-Stats
docker stats

# Ressourcen pro Container
docker ps -q | xargs docker inspect | jq '.[].HostConfig.Memory'
```

**Optimierungen**:

- Resource-Limits anpassen
- Container automatisch stoppen nach Inaktivität
- Shared Volumes statt Copy-on-Write
- Redis für Session-Storage

### Memory-Leak

**Symptom**: Spawner-Container wächst stetig

**Debug**:

```python
# Memory-Profiling aktivieren
import tracemalloc
tracemalloc.start()

# In app.py nach Requests:
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
```

**Häufige Ursache**: Docker-Client-Objekte nicht geschlossen

**Fix**:

```python
# context manager verwenden
with docker.from_env() as client:
    client.containers.run(...)
```

---

## Erweiterungen

### 1. Container-Timeout (Auto-Shutdown)

**Ziel**: Container nach 1h Inaktivität stoppen

```python
# In models.py
class User(db.Model):
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

# Cronjob in app.py
from apscheduler.schedulers.background import BackgroundScheduler

def cleanup_inactive_containers():
    timeout = timedelta(hours=1)
    inactive_users = User.query.filter(
        User.last_activity < datetime.utcnow() - timeout
    ).all()

    for user in inactive_users:
        if user.container_id:
            container_mgr.stop_container(user.container_id)

scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_inactive_containers, 'interval', minutes=15)
scheduler.start()
```

### 2. Volume-Persistenz

**Ziel**: User-Daten überleben Container-Neustarts

```python
# In spawn_container()
volumes = {
    f'/data/users/{username}': {
        'bind': '/app/data',
        'mode': 'rw'
    }
}

container = client.containers.run(
    volumes=volumes,
    # ...
)
```

### 3. Resource-Quotas pro User

```python
# In models.py
class User(db.Model):
    cpu_quota = db.Column(db.Integer, default=50000)  # 0.5 CPU
    memory_limit = db.Column(db.String, default='512m')

# In spawn_container()
container = client.containers.run(
    cpu_quota=user.cpu_quota,
    mem_limit=user.memory_limit,
    # ...
)
```

### 4. Multi-Template-Support

```python
# In models.py
class User(db.Model):
    template_type = db.Column(db.String, default='basic')

TEMPLATES = {
    'basic': 'user-service-template:latest',
    'python': 'user-python-env:latest',
    'node': 'user-node-env:latest'
}

# In spawn_container()
image = TEMPLATES.get(user.template_type, TEMPLATES['basic'])
```

### 5. WebSocket-Support für Logs

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app)

@socketio.on('stream_logs')
def stream_container_logs(container_id):
    container = client.containers.get(container_id)
    for line in container.logs(stream=True):
        emit('log_line', {'data': line.decode()})
```

### 6. Admin-Dashboard

```python
# In models.py
class User(db.Model):
    is_admin = db.Column(db.Boolean, default=False)

# Neue Route in app.py
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)

    users = User.query.all()
    containers = client.containers.list(all=True)

    return render_template('admin.html', users=users, containers=containers)
```

### 7. API-Endpoints

```python
# RESTful API für externe Integration
@app.route('/api/container/start', methods=['POST'])
@api_key_required
def api_start_container():
    data = request.json
    user = User.query.get(data['user_id'])

    container_id, port = container_mgr.spawn_container(user.id, user.username)

    return jsonify({
        'container_id': container_id,
        'url': f'http://{user.username}.{Config.BASE_DOMAIN}'
    })
```

### 8. Metrics & Monitoring

```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)

# Custom Metrics
active_containers = Gauge('spawner_active_containers', 'Number of running user containers')

@metrics.counter('spawner_logins', 'Login attempts')
def login():
    # ...
```

---

## Best Practices

### 1. Container-Images optimieren

```dockerfile
# Multi-stage Build
FROM python:3.11 AS builder
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Non-root User
RUN useradd -m appuser
USER appuser
```

### 2. Health-Checks implementieren

```python
# In app.py
@app.route('/health')
def health():
    # DB-Check
    try:
        db.session.execute('SELECT 1')
    except:
        return jsonify({'status': 'unhealthy', 'db': 'down'}), 503

    # Docker-Check
    try:
        client.ping()
    except:
        return jsonify({'status': 'unhealthy', 'docker': 'down'}), 503

    return jsonify({'status': 'healthy'})
```

```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 3. Logging strukturieren

```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        })

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
app.logger.addHandler(handler)
```

### 4. Graceful Shutdown

```python
import signal
import sys

def cleanup(signum, frame):
    print("Shutting down gracefully...")

    # Alle aktiven Container stoppen
    containers = client.containers.list(filters={'label': 'spawner.managed=true'})
    for container in containers:
        container.stop(timeout=30)

    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)
```

### 5. Rate-Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # ...
```

### 6. Backups

```bash
# Cronjob für DB-Backup
0 2 * * * docker exec spawner sqlite3 /app/data/users.db ".backup '/app/data/backup-$(date +\%Y\%m\%d).db'"

# Backup-Rotation (7 Tage)
0 3 * * * find /path/to/backups -name "backup-*.db" -mtime +7 -delete
```

### 7. CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy Spawner

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Image
        run: docker build -t spawner:${{ github.sha }} .

      - name: Push to Registry
        run: docker push spawner:${{ github.sha }}

      - name: Deploy to Production
        run: |
          ssh user@server "docker pull spawner:${{ github.sha }}"
          ssh user@server "docker service update --image spawner:${{ github.sha }} spawner"
```

### 8. Tests

```python
# tests/test_container_manager.py
import pytest
from container_manager import ContainerManager

@pytest.fixture
def manager():
    return ContainerManager()

def test_spawn_container(manager):
    container_id, port = manager.spawn_container(1, 'testuser')
    assert container_id is not None
    assert port == 8080

    # Cleanup
    manager.remove_container(container_id)

def test_container_resource_limits(manager):
    container_id, _ = manager.spawn_container(2, 'testuser2')
    container = manager.client.containers.get(container_id)

    assert container.attrs['HostConfig']['Memory'] == 536870912  # 512 MB
    assert container.attrs['HostConfig']['CpuQuota'] == 50000
```

---

## FAQ

### Kann ich bestehende Container wiederverwenden?

Ja! In \`spawn_container()\` wird geprüft ob ein Container bereits existiert:

```python
existing = self._get_user_container(username)
if existing and existing.status == 'running':
    return existing.id, self._get_container_port(existing)
```

### Wie viele User kann das System handhaben?

Abhängig von Hardware und User-Container-Ressourcen:

- **8 GB RAM**: ~10-15 User (bei 512 MB pro Container)
- **16 GB RAM**: ~25-30 User
- **32 GB RAM**: ~60+ User

Für >100 User: Kubernetes mit Horizontal Pod Autoscaling empfohlen.

### Kann ich verschiedene Services pro User bereitstellen?

Ja! Erweitere das User-Modell um \`service_type\` und verwende verschiedene Template-Images.

### Funktioniert das auch ohne Traefik?

Ja! Alternativen:

- **Nginx mit dynamischer Config-Generation**
- **HAProxy mit Runtime-API**
- **Caddy mit JSON-API**

### Wie sichere ich den Docker-Socket ab?

Verwende \`tecnativa/docker-socket-proxy\` mit eingeschränkten Permissions (siehe [Sicherheit](#sicherheit)).

### Kann ich existierende User-Daten migrieren?

Ja! Volume-Mounts verwenden und bei Migration Volumes kopieren:

```bash
docker run --rm -v old-user-data:/from -v new-user-data:/to alpine sh -c "cp -av /from/* /to/"
```

---

## Ressourcen

### Docker SDK Documentation

- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [Docker Engine API](https://docs.docker.com/engine/api/)

### Flask & Security

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-Login](https://flask-login.readthedocs.io/)
- [OWASP Security Guidelines](https://owasp.org/www-project-web-security-testing-guide/)

### Traefik

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Docker Provider](https://doc.traefik.io/traefik/providers/docker/)

### Alternatives & Inspiration

- [JupyterHub](https://github.com/jupyterhub/jupyterhub)
- [Code-Server](https://github.com/coder/code-server)
- [Gitpod](https://www.gitpod.io/)

---

## Lizenz & Support

Dieses Projekt ist ein Beispiel-Setup. Für Produktions-Einsatz:

- **Security-Audit** durchführen
- **Load-Tests** mit erwarteter User-Anzahl
- **Backup-Strategie** implementieren
- **Monitoring** mit Prometheus/Grafana

---

**Version**: 1.0.0  
**Erstellt**: Januar 2026  
**Zielgruppe**: DevOps, Platform Engineers, SaaS-Entwickler


---


## Verzeichnisstruktur

```
spawner/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app.py
├── auth.py
├── container_manager.py
├── models.py
├── config.py
├── templates/
│   ├── login.html
│   └── dashboard.html
└── user-template/
    └── Dockerfile
```

## Dockerfile (Spawner-Service)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System-Dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Python-Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application-Code
COPY . .

# Daten-Verzeichnisse
RUN mkdir -p /app/data /app/logs && \
    chmod 755 /app/data /app/logs

EXPOSE 5000

# Health-Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]
```

## requirements.txt

```txt
flask==3.0.0
flask-login==0.6.3
flask-sqlalchemy==3.1.1
werkzeug==3.0.1
docker==7.0.0
PyJWT==2.8.0
python-dotenv==1.0.0
```

## config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ========================================
    # Sicherheit
    # ========================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Session-Sicherheit
    SESSION_COOKIE_SECURE = os.getenv('BASE_DOMAIN', 'localhost') != 'localhost'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 Stunde
    
    # ========================================
    # Datenbank
    # ========================================
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///data/users.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ========================================
    # Docker-Konfiguration
    # ========================================
    DOCKER_SOCKET = os.getenv('DOCKER_SOCKET', 'unix://var/run/docker.sock')
    USER_TEMPLATE_IMAGE = os.getenv('USER_TEMPLATE_IMAGE', 'user-service-template:latest')
    
    # ========================================
    # Traefik/Domain-Konfiguration
    # ========================================
    BASE_DOMAIN = os.getenv('BASE_DOMAIN', 'localhost')
    SPAWNER_SUBDOMAIN = os.getenv('SPAWNER_SUBDOMAIN', 'spawner')  # ← FEHLTE!
    TRAEFIK_NETWORK = os.getenv('TRAEFIK_NETWORK', 'web')
    
    # Vollständige Spawner-URL
    SPAWNER_URL = f"{SPAWNER_SUBDOMAIN}.{BASE_DOMAIN}"
    
    # ========================================
    # Application-Settings
    # ========================================
    # HTTPS automatisch für Nicht-Localhost
    PREFERRED_URL_SCHEME = 'https' if BASE_DOMAIN != 'localhost' else 'http'
    
    # Spawner-Port (nur für Debugging wichtig)
    SPAWNER_PORT = int(os.getenv('SPAWNER_PORT', 5000))
    
    # ========================================
    # Optionale Einstellungen
    # ========================================
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/spawner.log')
    
    # Container-Limits (für container_manager.py)
    DEFAULT_MEMORY_LIMIT = os.getenv('DEFAULT_MEMORY_LIMIT', '512m')
    DEFAULT_CPU_QUOTA = int(os.getenv('DEFAULT_CPU_QUOTA', 50000))  # 0.5 CPU
    
    # Container-Cleanup
    CONTAINER_IDLE_TIMEOUT = int(os.getenv('CONTAINER_IDLE_TIMEOUT', 3600))  # 1h in Sekunden


class DevelopmentConfig(Config):
    """Konfiguration für Entwicklung"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Konfiguration für Produktion"""
    DEBUG = False
    TESTING = False
    
    # Strikte Session-Sicherheit
    SESSION_COOKIE_SECURE = True
    
    # Optional: PostgreSQL statt SQLite
    # SQLALCHEMY_DATABASE_URI = os.getenv(
    #     'DATABASE_URL',
    #     'postgresql://spawner:password@postgres:5432/spawner'
    # )


class TestingConfig(Config):
    """Konfiguration für Tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Config-Dict für einfaches Laden
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

```

## models.py

```python
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    container_id = db.Column(db.String(100), nullable=True)
    container_port = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

## container_manager.py

```python
import docker
from config import Config

class ContainerManager:
    def __init__(self):
        self.client = docker.from_env()

    def spawn_container(self, user_id, username):
        """Spawnt einen neuen Container für den User"""
        try:
            existing = self._get_user_container(username)
            if existing and existing.status == 'running':
                return existing.id, self._get_container_port(existing)

            # User-Container-Subdomain (OHNE spawner-subdomain!)
            user_domain = f"{username}.{Config.BASE_DOMAIN}"

            container = self.client.containers.run(
                Config.USER_TEMPLATE_IMAGE,
                name=f"user-{username}-{user_id}",
                detach=True,
                network=Config.TRAEFIK_NETWORK,
                labels={
                    'traefik.enable': 'true',

                    # HTTP Router
                    f'traefik.http.routers.user{user_id}.rule':
                        f'Host(`{user_domain}`)',
                    f'traefik.http.routers.user{user_id}.entrypoints': 'web',

                    # HTTPS Router (auskommentiert für initiale Tests)
                    # f'traefik.http.routers.user{user_id}-secure.rule':
                    #     f'Host(`{user_domain}`)',
                    # f'traefik.http.routers.user{user_id}-secure.entrypoints': 'websecure',
                    # f'traefik.http.routers.user{user_id}-secure.tls.certresolver': 'hetzner',

                    # Service
                    f'traefik.http.services.user{user_id}.loadbalancer.server.port': '8080',

                    # Metadata
                    'spawner.user_id': str(user_id),
                    'spawner.username': username,
                    'spawner.managed': 'true'
                },
                environment={
                    'USER_ID': str(user_id),
                    'USERNAME': username
                },
                restart_policy={'Name': 'unless-stopped'},
                mem_limit=Config.DEFAULT_MEMORY_LIMIT,
                cpu_quota=Config.DEFAULT_CPU_QUOTA
            )

            return container.id, 8080

        except docker.errors.ImageNotFound:
            raise Exception(f"Template-Image '{Config.USER_TEMPLATE_IMAGE}' nicht gefunden")
        except docker.errors.APIError as e:
            raise Exception(f"Docker API Fehler: {str(e)}")

    def stop_container(self, container_id):
        """Stoppt einen User-Container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            return True
        except docker.errors.NotFound:
            return False

    def remove_container(self, container_id):
        """Entfernt einen User-Container komplett"""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
            return True
        except docker.errors.NotFound:
            return False

    def get_container_status(self, container_id):
        """Gibt Status eines Containers zurück"""
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except docker.errors.NotFound:
            return 'not_found'

    def _get_user_container(self, username):
        """Findet existierenden Container für User"""
        filters = {'label': f'spawner.username={username}'}
        containers = self.client.containers.list(all=True, filters=filters)
        return containers[0] if containers else None

    def _get_container_port(self, container):
        """Extrahiert Port aus Container-Config"""
        return 8080
```

## auth.py

```python
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from container_manager import ContainerManager

auth_bp = Blueprint('auth', __name__)
container_mgr = ContainerManager()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User-Login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)

            # Container spawnen wenn noch nicht vorhanden
            if not user.container_id:
                try:
                    container_id, port = container_mgr.spawn_container(user.id, user.username)
                    user.container_id = container_id
                    user.container_port = port
                    db.session.commit()
                except Exception as e:
                    flash(f'Container-Start fehlgeschlagen: {str(e)}', 'error')
                    return redirect(url_for('auth.login'))

            flash('Login erfolgreich!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Ungültige Anmeldedaten', 'error')

    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User-Registrierung"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Prüfe ob User existiert
        if User.query.filter_by(username=username).first():
            flash('Username bereits vergeben', 'error')
            return redirect(url_for('auth.signup'))

        if User.query.filter_by(email=email).first():
            flash('Email bereits registriert', 'error')
            return redirect(url_for('auth.signup'))

        # Neuen User anlegen
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Container aus Template bauen und starten
        try:
            container_id, port = container_mgr.spawn_container(user.id, user.username)
            user.container_id = container_id
            user.container_port = port
            db.session.commit()

            flash('Registrierung erfolgreich! Container wird gestartet...', 'success')
            login_user(user)
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.delete(user)
            db.session.commit()
            flash(f'Registrierung fehlgeschlagen: {str(e)}', 'error')

    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User-Logout"""
    logout_user()
    flash('Erfolgreich abgemeldet', 'success')
    return redirect(url_for('auth.login'))
```

## app.py

```python
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from models import db, User
from auth import auth_bp
from config import Config
from container_manager import ContainerManager

# Flask-App initialisieren
app = Flask(__name__)
app.config.from_object(Config)

# Datenbank initialisieren
db.init_app(app)

# Flask-Login initialisieren
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bitte melde dich an, um auf diese Seite zuzugreifen.'
login_manager.login_message_category = 'error'

# Blueprint registrieren
app.register_blueprint(auth_bp)

@login_manager.user_loader
def load_user(user_id):
    """Lädt User für Flask-Login"""
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Startseite - Redirect zu Dashboard oder Login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - zeigt Container-Status und Service-URL"""
    container_mgr = ContainerManager()
    container_status = 'unknown'

    if current_user.container_id:
        container_status = container_mgr.get_container_status(current_user.container_id)

    # Service-URL für den User
    scheme = app.config['PREFERRED_URL_SCHEME']
    service_url = f"{scheme}://{current_user.username}.{app.config['BASE_DOMAIN']}"

    return render_template('dashboard.html',
                         user=current_user,
                         service_url=service_url,
                         container_status=container_status)

@app.route('/container/restart')
@login_required
def restart_container():
    """Startet Container des Users neu"""
    container_mgr = ContainerManager()

    # Alten Container stoppen falls vorhanden
    if current_user.container_id:
        container_mgr.stop_container(current_user.container_id)
        container_mgr.remove_container(current_user.container_id)

    # Neuen Container starten
    try:
        container_id, port = container_mgr.spawn_container(current_user.id, current_user.username)
        current_user.container_id = container_id
        current_user.container_port = port
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Container-Restart fehlgeschlagen: {str(e)}")

    return redirect(url_for('dashboard'))

@app.route('/health')
def health():
    """Health-Check für Docker und Monitoring"""
    try:
        # DB-Check
        db.session.execute('SELECT 1')
        db_status = 'ok'
    except Exception as e:
        db_status = f'error: {str(e)}'

    try:
        # Docker-Check
        container_mgr = ContainerManager()
        container_mgr.client.ping()
        docker_status = 'ok'
    except Exception as e:
        docker_status = f'error: {str(e)}'

    status_code = 200 if db_status == 'ok' and docker_status == 'ok' else 503

    return {
        'status': 'healthy' if status_code == 200 else 'unhealthy',
        'database': db_status,
        'docker': docker_status,
        'version': '1.0.0'
    }, status_code

# Datenbank-Tabellen erstellen beim ersten Start
with app.app_context():
    db.create_all()
    app.logger.info('Datenbank-Tabellen erstellt')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

## docker-compose.yml

```yaml
version: '3.8'

services:
  spawner:
    build: .
    container_name: spawner
    restart: unless-stopped

    ports:
      - "5000:5000"  # Optional: Direktzugriff für Debugging

    volumes:
      # Docker-Socket für Container-Management
      - /var/run/docker.sock:/var/run/docker.sock:rw
      # Persistente Daten
      - ./data:/app/data
      # Logs
      - ./logs:/app/logs

    environment:
      # Aus .env-Datei
      - SECRET_KEY=${SECRET_KEY}
      - BASE_DOMAIN=${BASE_DOMAIN}
      - TRAEFIK_NETWORK=${TRAEFIK_NETWORK}
      - USER_TEMPLATE_IMAGE=${USER_TEMPLATE_IMAGE:-user-service-template:latest}
      - SPAWNER_SUBDOMAIN=${SPAWNER_SUBDOMAIN:-spawner}

    networks:
      - web  # ⚠️ Dein bestehendes Traefik-Netzwerk!

    labels:
      # Traefik aktivieren
      - "traefik.enable=true"

      # HTTP Router
      - "traefik.http.routers.spawner.rule=Host(`${SPAWNER_SUBDOMAIN}.${BASE_DOMAIN}`)"
      - "traefik.http.routers.spawner.entrypoints=web"
      - "traefik.http.services.spawner.loadbalancer.server.port=5000"

      # Metadata für Management
      - "spawner.managed=true"
      - "spawner.version=1.0.0"
      - "spawner.type=management-service"

    # Health-Check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

# Externes Netzwerk (von deinem Traefik bereits vorhanden)
networks:
  web:
    external: true
```

## user-template/Dockerfile (Template für User-Container)

```dockerfile
FROM nginxinc/nginx-unprivileged:alpine

# Beispiel: Einfacher Webserver pro User
# HTML direkt in den Container schreiben
RUN echo '<h1>Dein persönlicher Service</h1>' > /usr/share/nginx/html/index.html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
```

**Hinweis**: Verwende `nginx-unprivileged` statt `nginx` für bessere Sicherheit (kein root-Prozess).
Container läuft auf Port 8080 (als unprivileged user).

## templates/login.html

```html
<!DOCTYPE html>
<html>
<head>
    <title>Login - Spawner</title>
</head>
<body>
    <h2>Login</h2>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <p style="color: red;">{{ message }}</p>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required><br>
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">Login</button>
    </form>
    <p>Noch kein Account? <a href="{{ url_for('auth.signup') }}">Registrieren</a></p>
</body>
</html>
```

## templates/dashboard.html

```html
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - {{ user.username }}</title>
</head>
<body>
    <h2>Willkommen, {{ user.username }}!</h2>
    
    <p>Container-Status: <strong>{{ container_status }}</strong></p>
    <p>Dein Service: <a href="{{ service_url }}" target="_blank">{{ service_url }}</a></p>
    
    <a href="{{ url_for('restart_container') }}">Container neu starten</a><br>
    <a href="{{ url_for('auth.logout') }}">Logout</a>
</body>
</html>
```

## Starten

```bash
# Im spawner/ Verzeichnis:
docker-compose up --build
```

Die Lösung enthält:
- **Vollständige Authentifizierung** mit Flask-Login und gehashten Passwörtern
- **Automatisches Container-Spawning** via Docker SDK [docs.docker](https://docs.docker.com/reference/api/engine/sdk/examples/)
- **Traefik-Integration** über Labels [brunoscheufler](https://brunoscheufler.com/blog/2022-04-17-routing-traffic-for-dynamic-deployments-using-traefik)
- **Resource-Limits** (RAM/CPU) pro User-Container
- **Persistente Datenbank** für User-Management
- **Template-System** für neue User-Container

Der Spawner-Service benötigt Zugriff auf `/var/run/docker.sock`, um Container zu steuern.

---

# SPAWNER Integration in bestehende Traefik-Umgebung
## Step-by-Step Implementierungsplan

---

## 🎯 Zielsetzung

Integration des SPAWNER-Systems in eine bestehende Docker-Infrastruktur mit Traefik als Reverse Proxy, ohne bestehende Services zu beeinträchtigen.

---

## 📋 Voraussetzungen prüfen

### ✅ Checkliste vor Start

- [ ] Traefik läuft und ist erreichbar
- [ ] Docker-Version ≥ 20.10
- [ ] Freier Port für Spawner (Standard: 5000)
- [ ] Mindestens 2 GB freier RAM
- [ ] Wildcard-DNS oder manuelle DNS-Einträge möglich
- [ ] Zugriff auf `/var/run/docker.sock`
- [ ] Git installiert (zum Klonen/Erstellen der Dateien)

---

## Phase 1: Analyse der bestehenden Umgebung

### Step 1.1: Traefik-Konfiguration ermitteln

**Aktion**: Bestehende Traefik-Setup analysieren

```bash
# Traefik-Container finden
docker ps | grep traefik

# Traefik-Konfiguration anzeigen
docker inspect <traefik-container-name> | jq '.[0].Config.Labels'
docker inspect <traefik-container-name> | jq '.[0].HostConfig.Binds'

# Verwendetes Netzwerk ermitteln
docker inspect <traefik-container-name> | jq '.[0].NetworkSettings.Networks'
```

**Dokumentieren**:
- Traefik-Version: _______________
- Netzwerk-Name: _______________
- EntryPoints: _______________
- Zertifikats-Resolver (falls HTTPS): _______________

```bash=1
 docker ps | grep traefik
81e0f2d0f8c0   traefik:v3.6.5
```
```config=1
docker inspect 81e0f2d0f8c0 | jq '.[0].Config.Labels'
{
  "com.docker.compose.config-hash": "aeb95d30dd87fd499dd7207ef416f97a6c325227615a2ccdae20278b5f70f51c",
  "com.docker.compose.container-number": "1",
  "com.docker.compose.depends_on": "",
  "com.docker.compose.image": "sha256:0fb158a64eaac3b411525e180705dbb4e120d078150b6a795e120e6b80e81b02",
  "com.docker.compose.oneoff": "False",
  "com.docker.compose.project": "traefik",
  "com.docker.compose.project.config_files": "/volume1/docker/traefik/docker-compose.yml",
  "com.docker.compose.project.working_dir": "/volume1/docker/traefik",
  "com.docker.compose.service": "traefik",
  "com.docker.compose.version": "2.20.1",
  "org.opencontainers.image.description": "A modern reverse-proxy",
  "org.opencontainers.image.documentation": "https://docs.traefik.io",
  "org.opencontainers.image.source": "https://github.com/traefik/traefik",
  "org.opencontainers.image.title": "Traefik",
  "org.opencontainers.image.url": "https://traefik.io",
  "org.opencontainers.image.vendor": "Traefik Labs",
  "org.opencontainers.image.version": "v3.6.5"
}
```

```config=1
docker inspect 81e0f2d0f8c0 | jq '.[0].HostConfig.Binds'
[
  "/var/run/docker.sock:/var/run/docker.sock:rw",
  "/volume1/docker/traefik/traefik.toml:/traefik.toml:rw",
  "/volume1/docker/traefik/traefik_dynamic.toml:/traefik_dynamic.toml:rw",
  "/volume1/docker/traefik/acme.json:/acme.json:rw"
]
```

```config=1
docker inspect 81e0f2d0f8c0 | jq '.[0].NetworkSettings.Networks'
{
  "web": {
    "IPAMConfig": null,
    "Links": null,
    "Aliases": [
      "traefik",
      "traefik",
      "81e0f2d0f8c0"
    ],
    "NetworkID": "79c8e53a1b0d38b655e769918c2ecfccf049461f0e1fe276362ccc1c13869aa3",
    "EndpointID": "95e639cc48ced9bb06d58fd501bbf850bbe64e6050d5de75700ded13bdb1c4d4",
    "Gateway": "192.168.16.1",
    "IPAddress": "192.168.16.6",
    "IPPrefixLen": 24,
    "IPv6Gateway": "",
    "GlobalIPv6Address": "",
    "GlobalIPv6PrefixLen": 0,
    "MacAddress": "02:42:c0:a8:10:06",
    "DriverOpts": null
  }
}
```

### Step 1.2: Netzwerk-Topologie verstehen

```bash
# Alle Docker-Netzwerke auflisten
docker network ls

# Netzwerk-Details des Traefik-Netzwerks
docker network inspect <traefik-network-name>

# Welche Container sind bereits angeschlossen?
docker network inspect <traefik-network-name> | jq '.[0].Containers'
```

```bash=1
docker network ls
NETWORK ID     NAME                       DRIVER    SCOPE
37f47c9e1943   bridge                     bridge    local
3ab114f137fa   dokploy_dokploy_internal   bridge    local
04ae90e99953   host                       host      local
208dfb8d38b0   jupyterhub                 bridge    local
ed620451f21c   none                       null      local
79c8e53a1b0d   web                        bridge    local
```

**Entscheidung**: 
- Existierendes Netzwerk nutzen: **Ja** ☐ / **Nein** ☐
- Netzwerk-Name: `_______________`

:::success
**Existierendes Netzwerk nutzen:** ✔
**Netzwerk-Name: web**
:::
### Step 1.3: Domain-Strategie festlegen

**Optionen**:

**A) Subdomains pro User** (empfohlen)
```
alice.spawner.example.com
bob.spawner.example.com
charlie.spawner.example.com
```

**B) Path-basiert**
```
spawner.example.com/alice
spawner.example.com/bob
spawner.example.com/charlie
```


**Gewählte Strategie**: ☐ A  ☐ B
:::success
**B) Path-basiert**
:::
**Base-Domain**: `_______________`
:::success
**Base-Domain: coder.wieland.org**
:::
### Step 1.4: Traefik-Dashboard prüfen

```bash
# Ist Dashboard aktiviert?
docker exec <traefik-container> cat /etc/traefik/traefik.yml | grep -A5 "api:"

# Dashboard-URL (Standard: Port 8080)
firefox http://<traefik-host>:8080
```

**Notiz**: Dashboard-URL für Monitoring: `_______________`

---

## Phase 2: Projekt-Setup

### Step 2.1: Projektverzeichnis erstellen

```bash
# Zu deinem Docker-Projekten-Verzeichnis wechseln
cd /path/to/docker/projects  # z.B. ~/docker oder /opt/docker

# Spawner-Verzeichnis erstellen
mkdir -p spawner/{templates,user-template,data,logs}
cd spawner

# Berechtigungen setzen
chmod 755 .
```

**Pfad dokumentieren**: `_______________`

### Step 2.2: Core-Dateien erstellen

```bash
# Python-Dateien
touch app.py auth.py container_manager.py models.py config.py

# Docker-Dateien
touch Dockerfile docker-compose.yml .env .dockerignore

# Templates
touch templates/login.html templates/signup.html templates/dashboard.html

# User-Template
touch user-template/Dockerfile

# README
touch README.md
```

### Step 2.3: .dockerignore erstellen

```bash
cat > .dockerignore << 'EOF'
__pycache__
*.pyc
*.pyo
*.pyd
.Python
.env
.venv
venv/
data/*.db
logs/*.log
.git
.gitignore
.DS_Store
*.md
EOF
```

### Step 2.4: requirements.txt erstellen

```bash
cat > requirements.txt << 'EOF'
flask==3.0.0
flask-login==0.6.3
flask-sqlalchemy==3.1.1
werkzeug==3.0.1
docker==7.0.0
PyJWT==2.8.0
python-dotenv==1.0.0
EOF
```

---

## Phase 3: Anpassung an deine Umgebung

### Step 3.1: .env-Datei konfigurieren

Erstelle `.env` mit folgenden Variablen (anpassen!):

```
SECRET_KEY=ÄNDERE_MICH_ZU_RANDOM_STRING
BASE_DOMAIN=spawner.example.com
TRAEFIK_NETWORK=traefik-network
USER_TEMPLATE_IMAGE=user-service-template:latest
SPAWNER_PORT=5000
```

SECRET_KEY generieren:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3.2: docker-compose.yml erstellen

Vollständiges Beispiel mit Traefik-Labels - siehe Dokumentation.

**Wichtige Anpassungen**:
- Netzwerk-Name
- EntryPoint-Name
- Domain-Name
- Port-Konflikte prüfen

### Step 3.3: Traefik-Konfiguration erweitern

Prüfe ob Docker-Provider aktiviert:

```bash
docker exec <traefik-container> cat /etc/traefik/traefik.yml
```

Falls Docker-Provider fehlt, ergänzen und Traefik neu starten.

---

---

## Phase 4: User-Template vorbereiten

### Step 4.1: Template-Dockerfile erstellen

Im Verzeichnis `user-template/`:

```dockerfile
FROM nginxinc/nginx-unprivileged:alpine

# HTML kopieren UND Ownership setzen
COPY --chown=nginx:nginx index.html /usr/share/nginx/html/index.html

EXPOSE 8080
```

### Step 4.2: Beispiel index.html

Erstelle eine einfache HTML-Seite für User-Container.

### Step 4.3: Template-Image bauen

```bash
cd user-template
docker build -t user-service-template:latest .

# Test
docker run -d -p 8080:8080 --name test-user user-service-template:latest
curl http://localhost:8080
docker stop test-user && docker rm test-user

cd ..
```

---

## Phase 5: Spawner bauen und testen

### Step 5.1: Alle Python-Dateien erstellen

Kopiere die Code-Beispiele aus der Dokumentation:
- config.py
- models.py
- container_manager.py
- auth.py
- app.py

### Step 5.2: Dockerfile erstellen

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs && chmod 755 /app/data /app/logs

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]
```

### Step 5.3: Spawner bauen

```bash
docker-compose build
```

### Step 5.4: Test-Start

```bash
docker-compose up -d
docker-compose logs -f spawner

# Health-Check
curl http://localhost:5000/health

# Login-Seite
curl http://localhost:5000/login
```

### Step 5.5: Erste Test-Registrierung

```bash
firefox http://localhost:5000
```

Registriere einen Test-User und prüfe ob Container spawnt:

```bash
docker ps | grep user-
docker inspect user-testuser-1 | jq '.[0].Config.Labels'
```

---

## Phase 6: Traefik-Integration aktivieren

### Step 6.1: Netzwerk verbinden

```bash
# Falls noch nicht verbunden
docker network connect traefik-network spawner

# Verifizieren
docker network inspect traefik-network | grep spawner
```

### Step 6.2: DNS konfigurieren

**Lokal testen** (Option A):
```bash
sudo nano /etc/hosts

# Hinzufügen:
127.0.0.1 spawner.localhost
127.0.0.1 testuser.localhost
```

**Produktion** (Option B):
- Wildcard-DNS-Eintrag erstellen: `*.spawner.example.com → <server-ip>`
- DNS-Propagation abwarten

### Step 6.3: Traefik-Routing testen

```bash
# Traefik-Dashboard öffnen
firefox http://<traefik-host>:8080

# Routes prüfen unter HTTP → Routers

# Mit curl testen
curl -H "Host: spawner.localhost" http://localhost/
curl -H "Host: testuser.localhost" http://localhost/
```

### Step 6.4: End-to-End Test

1. Spawner-UI aufrufen
2. Neuen User registrieren
3. Zum Dashboard navigieren
4. Service-Link klicken → User-Container sollte erreichbar sein

---

## Phase 7: HTTPS aktivieren (optional)

### Step 7.1: Let's Encrypt konfigurieren

Prüfe Traefik-Config für certificatesResolvers.

### Step 7.2: Labels für HTTPS anpassen

In `docker-compose.yml` und `container_manager.py` HTTPS-Labels ergänzen:
- entrypoints: websecure
- tls.certresolver: letsencrypt

### Step 7.3: Spawner neu starten

```bash
docker-compose down
docker-compose up -d --build
```

### Step 7.4: HTTPS testen

```bash
firefox https://spawner.example.com

# Zertifikat prüfen
openssl s_client -connect spawner.example.com:443
```

---

## Phase 8: Monitoring & Observability

### Step 8.1: Logging aktivieren

Strukturiertes Logging in app.py implementieren.

### Step 8.2: Monitoring-Script

```bash
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== SPAWNER Statistics ==="
docker stats spawner --no-stream
docker ps --filter "label=spawner.user_id"
docker stats $(docker ps --filter "label=spawner.user_id" -q) --no-stream
EOF

chmod +x monitor.sh
./monitor.sh
```

### Step 8.3: Backup-Strategie

```bash
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/spawner"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
docker exec spawner sqlite3 /app/data/users.db ".backup '/app/data/backup_${DATE}.db'"
cp data/backup_${DATE}.db $BACKUP_DIR/
find $BACKUP_DIR -name "backup_*.db" -mtime +7 -delete
EOF

chmod +x backup.sh

# Cronjob
crontab -e
# 0 2 * * * /path/to/spawner/backup.sh
```

---

## Phase 9: Produktions-Optimierung

### Step 9.1: Ressourcen-Limits anpassen

In `container_manager.py` basierend auf deiner Hardware.

### Step 9.2: Container-Cleanup

Script für automatisches Aufräumen alter Container.

### Step 9.3: PostgreSQL statt SQLite

Für Produktion docker-compose.yml um PostgreSQL erweitern.

### Step 9.4: Rate-Limiting

Flask-Limiter installieren und konfigurieren.

---

## Phase 10: Go-Live

### Step 10.1: Load-Test

```bash
ab -n 1000 -c 10 http://spawner.example.com/login

# Multi-User Test
for i in {1..10}; do
    curl -X POST http://spawner.example.com/signup \
      -d "username=loadtest${i}&email=test${i}@example.com&password=test123"
    sleep 2
done
```

### Step 10.2: Security-Audit

- SECRET_KEY stark
- HTTPS erzwungen
- Rate-Limiting aktiv
- Container-Isolation
- Non-Root-User

```bash
# Vulnerability-Scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image spawner:latest
```

### Step 10.3: Go-Live Checklist

- [ ] Alle Services erreichbar
- [ ] HTTPS funktioniert
- [ ] DNS korrekt
- [ ] Backups laufen
- [ ] Monitoring aktiv
- [ ] Logs werden geschrieben
- [ ] Load-Tests bestanden
- [ ] Security-Audit durchgeführt
- [ ] Team informiert

```bash
# Finaler Health-Check
curl -f https://spawner.example.com/health

# Container-Count
docker ps --filter 'label=spawner.managed=true' -q | wc -l
```

**🎉 GO-LIVE!**

---

## 🚨 Troubleshooting

### Traefik findet Spawner nicht
- Netzwerk-Verbindung prüfen
- Labels verifizieren
- Traefik-Logs checken

### User-Container startet nicht
- Template-Image existiert?
- Docker-Socket-Permissions
- Netzwerk vorhanden?

### DNS funktioniert nicht
- Wildcard-DNS konfiguriert?
- /etc/hosts für lokale Tests
- DNS-Propagation abwarten

### Container-Spawn schlägt fehl
- Docker-API-Zugriff testen
- Socket-Mount prüfen
- Permissions checken

---

## 📊 Post-Integration

### Wöchentliches Monitoring

```bash
# Container-Anzahl
docker ps --filter "label=spawner.managed=true"

# Ressourcen
docker stats --no-stream

# Disk-Space
docker system df
```

### Metriken

- Anzahl User
- Aktive Container
- CPU/RAM-Auslastung
- Netzwerk-Traffic

---

## 🎓 Next Steps

1. User-Feedback sammeln
2. Templates erweitern (Python, Node.js)
3. Admin-Dashboard entwickeln
4. Auto-Shutdown implementieren
5. Volume-Persistenz aktivieren
6. Multi-Region deployment

---

**Integration abgeschlossen!** 🚀

Bei Fragen:
- Logs: `docker-compose logs -f`
- Traefik: `http://<host>:8080`
- Health: `curl https://spawner.example.com/health`
