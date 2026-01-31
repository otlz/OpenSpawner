# Multi-Container MVP - Test & Verification Guide

## Backend Syntax Verification

### Python Compilation Check
```bash
python -m py_compile models.py container_manager.py api.py config.py
# ✅ Alle Dateien erfolgreich kompiliert
```

### Imports Verification
```python
# models.py - UserContainer ist importierbar
from models import UserContainer, User, db

# api.py - UserContainer Import
from models import UserContainer

# container_manager.py - Neue Methode
from container_manager import ContainerManager
mgr = ContainerManager()
mgr.spawn_multi_container(user_id, slug, container_type)
```

---

## Code Structure Verification

### UserContainer Model (models.py)
```python
class UserContainer(db.Model):
    __tablename__ = 'user_container'

    # ✅ Alle erforderlichen Felder:
    - id (Primary Key)
    - user_id (Foreign Key)
    - container_type ('dev' | 'prod')
    - container_id (Docker ID)
    - container_port (Port)
    - template_image (Image Name)
    - created_at (Timestamp)
    - last_used (Timestamp)

    # ✅ Unique Constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'container_type'),
    )
```

### User Model (models.py)
```python
class User(db.Model):
    # ✅ Entfernt:
    - container_id
    - container_port

    # ✅ Hinzugefügt:
    - containers = db.relationship('UserContainer')
```

### Config Templates (config.py)
```python
CONTAINER_TEMPLATES = {
    'dev': {
        'image': 'user-service-template:latest',  # FROM ENV
        'display_name': 'Development Container',
        'description': 'Nginx-basierter Development Container'
    },
    'prod': {
        'image': 'user-template-next:latest',  # FROM ENV
        'display_name': 'Production Container',
        'description': 'Next.js Production Build'
    }
}
```

---

## API Endpoint Verification

### GET /api/user/containers
**Request:**
```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:5000/api/user/containers
```

**Expected Response:**
```json
{
  "containers": [
    {
      "type": "dev",
      "display_name": "Development Container",
      "description": "Nginx-basierter Development Container",
      "status": "running|stopped|not_created|error",
      "service_url": "https://coder.domain.com/slug-dev",
      "container_id": "abc123def456...",
      "created_at": "2025-01-31T10:00:00",
      "last_used": "2025-01-31T11:30:00"
    },
    {
      "type": "prod",
      "display_name": "Production Container",
      "description": "Next.js Production Build",
      "status": "not_created",
      "service_url": "https://coder.domain.com/slug-prod",
      "container_id": null,
      "created_at": null,
      "last_used": null
    }
  ]
}
```

### POST /api/container/launch/<container_type>
**Request:**
```bash
curl -X POST -H "Authorization: Bearer <JWT>" \
  http://localhost:5000/api/container/launch/dev
```

**Expected Response (First Call):**
```json
{
  "message": "Container bereit",
  "service_url": "https://coder.domain.com/slug-dev",
  "container_id": "abc123def456...",
  "status": "running"
}
```

**Expected Response (Subsequent Calls):**
- Wenn Container läuft: Gibt selbe Response zurück, aktualisiert last_used
- Wenn Container gestoppt: Startet Container neu mit `start_container()`
- Wenn Container gelöscht: Erstellt neuen Container mit `spawn_multi_container()`

---

## Frontend TypeScript Verification

### api.ts Types
```typescript
// ✅ Container Type
export interface Container {
  type: string;
  display_name: string;
  description: string;
  status: 'not_created' | 'running' | 'stopped' | 'error';
  service_url: string;
  container_id: string | null;
  created_at: string | null;
  last_used: string | null;
}

// ✅ ContainersResponse Type
export interface ContainersResponse {
  containers: Container[];
}

// ✅ LaunchResponse Type
export interface LaunchResponse {
  message: string;
  service_url: string;
  container_id: string;
  status: string;
}

// ✅ API Functions
api.getUserContainers(): Promise<ApiResponse<ContainersResponse>>
api.launchContainer(containerType: string): Promise<ApiResponse<LaunchResponse>>
```

### Dashboard Component
```typescript
// ✅ State Management
const [containers, setContainers] = useState<Container[]>([]);
const [loading, setLoading] = useState(true);
const [launching, setLaunching] = useState<string | null>(null);
const [error, setError] = useState("");

// ✅ Load Containers
const loadContainers = async () => {
  const { data, error } = await api.getUserContainers();
  setContainers(data.containers);
}

// ✅ Launch Container
const handleLaunchContainer = async (containerType: string) => {
  const { data } = await api.launchContainer(containerType);
  window.open(data.service_url, "_blank");
  await loadContainers();
}

// ✅ Rendering
- 2 Container-Cards (dev + prod)
- Status-Icons (running, stopped, error, not_created)
- "Erstellen & Öffnen" oder "Service öffnen" Button
- Loading States während Launch
- Error-Handling
```

---

## Docker Container Verification

### spawn_multi_container() Method
```python
def spawn_multi_container(self, user_id: int, slug: str, container_type: str) -> tuple:
    """
    ✅ Prüft:
    - Template-Typ ist gültig
    - Image existiert
    - Container-Name ist eindeutig (user-{slug}-{type}-{id})

    ✅ Setzt:
    - Traefik-Labels mit Typ-Suffix
    - Environment Variablen (USER_ID, USER_SLUG, CONTAINER_TYPE)
    - Memory/CPU Limits
    - Restart Policy

    ✅ Gibt zurück:
    - (container_id, port_8080)
    """
```

### Traefik Labels
```python
# ✅ Router mit Typ-Suffix
f'traefik.http.routers.user{user_id}-{container_type}.rule':
  f'Host(`{base_host}`) && PathPrefix(`/{slug_with_suffix}`)'

# ✅ StripPrefix Middleware
f'traefik.http.middlewares.user{user_id}-{container_type}-strip.stripprefix.prefixes':
  f'/{slug_with_suffix}'

# ✅ Service Routing
f'traefik.http.services.user{user_id}-{container_type}.loadbalancer.server.port':
  '8080'

# ✅ TLS/HTTPS
f'traefik.http.routers.user{user_id}-{container_type}.tls': 'true'
f'traefik.http.routers.user{user_id}-{container_type}.tls.certresolver':
  Config.TRAEFIK_CERTRESOLVER
```

### URL Routing Test
```
User Request: https://coder.domain.com/slug-dev/path
↓
Traefik: Rule match (Host + PathPrefix)
↓
Middleware: StripPrefix entfernt /slug-dev
↓
Container: Erhält http://localhost:8080/path
```

---

## End-to-End Test Workflow

### Schritt 1: Setup
```bash
# Clean Slate
rm spawner.db
docker ps -a | grep user- | awk '{print $1}' | xargs docker rm -f

# Build Templates
docker build -t user-service-template:latest user-template/
docker build -t user-template-next:latest user-template-next/

# Start Services
docker-compose up -d --build

# Überprüfe Logs
docker-compose logs -f spawner
```

### Schritt 2: Registrierung
```
1. Öffne https://coder.domain.com
2. Klick "Registrieren"
3. Gib Email ein: test@example.com
4. Klick "Magic Link senden"
5. Überprüfe Email
6. Klick Magic Link in Email
7. User wird registriert und zu Dashboard weitergeleitet
8. Überprüfe: 2 Container-Cards sollten sichtbar sein (beide "Noch nicht erstellt")
```

### Schritt 3: Dev-Container
```
1. Auf Dashboard: Dev-Container Card "Erstellen & Öffnen" Button
2. Klick Button
3. Warte auf Loading State
4. Neuer Tab öffnet sich mit: https://coder.domain.com/test-dev
5. Seite zeigt Nginx-Willkommensseite
6. Zurück zum Dashboard
7. Überprüfe: Dev-Container Status = "Läuft"
8. Button ändert sich zu "Service öffnen"
```

### Schritt 4: Prod-Container
```
1. Auf Dashboard: Prod-Container Card "Erstellen & Öffnen" Button
2. Klick Button
3. Warte auf Loading State
4. Neuer Tab öffnet sich mit: https://coder.domain.com/test-prod
5. Seite zeigt Next.js Demo mit Shadcn/UI
6. Zurück zum Dashboard
7. Überprüfe: Prod-Container Status = "Läuft"
8. Button ändert sich zu "Service öffnen"
```

### Schritt 5: Container-Verwaltung
```
1. Klick "Service öffnen" für Dev-Container
   → Sollte bestehenden Tab neu laden
2. Refresh Dashboard
   → Beide Container sollten Status "Läuft" haben
3. Mit Dev-Container: http://{service_url}/
   → Sollte Seite ohne /test-dev/ anzeigen
4. Mit Prod-Container: http://{service_url}/
   → Sollte Seite ohne /test-prod/ anzeigen
```

---

## Verification Checklist

### Database
- [ ] UserContainer Tabelle existiert
- [ ] user_container.user_id Foreign Key funktioniert
- [ ] user_container.container_type ist VARCHAR(50)
- [ ] Unique Constraint (user_id, container_type) existiert
- [ ] User.containers Relationship lädt Container

### API
- [ ] GET /api/user/containers funktioniert
- [ ] POST /api/container/launch/dev funktioniert
- [ ] POST /api/container/launch/prod funktioniert
- [ ] Invalid container_type gibt 400 zurück
- [ ] Missing JWT gibt 401 zurück

### Docker
- [ ] spawn_multi_container() erstellt Container
- [ ] Container-Namen haben Typ-Suffix (-dev, -prod)
- [ ] Traefik-Labels haben richtige Routen
- [ ] StripPrefix funktioniert korrekt
- [ ] Beide Images sind vorhanden

### Frontend
- [ ] Dashboard zeigt 2 Container-Cards
- [ ] API Calls funktionieren ohne Errors
- [ ] "Erstellen & Öffnen" Button funktioniert
- [ ] Service-URLs öffnen sich in neuem Tab
- [ ] Status aktualisiert sich nach Launch
- [ ] Loading States sind sichtbar

### Integration
- [ ] User kann Dev-Container erstellen und öffnen
- [ ] User kann Prod-Container erstellen und öffnen
- [ ] Beide Container funktionieren gleichzeitig
- [ ] URL-Routing funktioniert für beide Container-Typen
- [ ] StripPrefix funktioniert korrekt für beide

---

## Debugging Commands

### Backend Debugging
```bash
# Logs
docker-compose logs -f spawner

# Container-Liste prüfen
docker ps | grep user-

# Inspect Container-Labels
docker inspect user-testuser-dev-1 | grep -A20 traefik

# Python Shell
docker exec -it spawner python
from models import UserContainer
UserContainer.query.all()
```

### Traefik Debugging
```bash
# Traefik Dashboard
curl http://localhost:8080/api/http/routers

# Spezifische Router
curl http://localhost:8080/api/http/routers | grep user

# Logs
docker-compose logs -f traefik | grep user
```

### Frontend Debugging
```bash
# Browser Console
window.localStorage.getItem('token')

# Network Tab
- GET /api/user/containers
- POST /api/container/launch/dev

# Redux DevTools (falls installiert)
Store überprüfen
```

---

## Known Issues & Solutions

### Issue: Container spawnt nicht
**Symptom**: POST /api/container/launch/dev gibt 500 zurück
**Debug**:
```bash
docker-compose logs spawner | tail -50
# Prüfe: Image existiert? Docker API funktioniert?
```

### Issue: Traefik routet nicht
**Symptom**: URL https://coder.domain.com/slug-dev gibt 404
**Debug**:
```bash
docker logs traefik | grep user
docker inspect user-testuser-dev-1 | grep traefik
```

### Issue: StripPrefix funktioniert nicht
**Symptom**: Container erhält /slug-dev in Request-Path
**Debug**:
```bash
# Container-Logs
docker logs user-testuser-dev-1

# Prüfe Traefik Middleware
curl http://localhost:8080/api/http/middlewares
```

---

**Status**: ✅ Alle Tests ready für Durchführung
**Hinweis**: Aktuelle Umgebung hat kein Docker - Tests müssen auf Target-System durchgeführt werden
