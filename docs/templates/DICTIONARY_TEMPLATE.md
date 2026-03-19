# 📚 Wörterbuch Template - Vollständige Dokumentation

## Übersicht

Das **Wörterbuch Template** (`user-template-dictionary`) ist eine Flask-basierte Web-Anwendung, die es Benutzern ermöglicht, persönliche Wörterbuch-Einträge zu speichern und zu verwalten. Jeder Eintrag besteht aus einem **Wort** und seiner **Bedeutung**, die in einer **SQLite-Datenbank** persistiert werden.

### Features
- ✅ **Persönliche Wörterbuch-Datenbank** pro Benutzer
- ✅ **SQLite-Persistierung** - Daten bleiben erhalten nach Container-Neustart
- ✅ **REST API** für Verwaltung (GET, POST, PUT, DELETE)
- ✅ **Moderne HTML/CSS/JS Frontend** mit Fehlerbehandlung
- ✅ **Health Checks** für Monitoring
- ✅ **Vollständige Fehlerbehandlung** und Logging
- ✅ **Docker Volume Support** für Datenpersistierung

---

## Architektur

### High-Level Diagramm

```
Browser Request
     ↓
Flask Backend (Port 8080)
     ↓
SQLite Database (/data/app.db)
     ↓
Docker Volume (/volumes/{user-id})
     ↓
Persistente Speicherung
```

### Komponenten

**Frontend (HTML/CSS/JavaScript):**
- `templates/index.html` - Single Page Application mit React-ähnlichem State Management
- Responsive Design (Mobile-freundlich)
- Real-time UI Updates
- Benutzerfreundliche Fehlerbehandlung

**Backend (Flask + SQLite):**
- `app.py` - Python Flask Anwendung
- SQLite Datenbank in `/data/app.db`
- REST API Endpoints
- Logging und Health Checks

**Containerisierung:**
- `Dockerfile` - Python 3.11 slim Image
- `requirements.txt` - Python Dependencies (Flask, Werkzeug)
- Unprivileged User (Port 8080)
- Health Check Endpoint

---

## Installation & Setup

### Schritt 1: Template in `.env` registrieren

Bearbeite `.env` und füge das Dictionary Template hinzu:

```bash
# .env
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-02:latest;user-template-next:latest;user-template-dictionary:latest"
```

**Wichtig:** Nur hier definierte Templates werden von `bash install.sh` gebaut!

### Schritt 2: Metadaten in `templates.json` aktualisieren

Das Template ist bereits in `templates.json` registriert:

```json
{
  "type": "dictionary",
  "image": "user-template-dictionary:latest",
  "display_name": "📚 Wörterbuch",
  "description": "Persönliches Wörterbuch mit Datenbank - Speichern Sie Wörter und Bedeutungen"
}
```

### Schritt 3: Build & Deploy

```bash
# Alle Templates bauen (inkl. dictionary)
bash install.sh

# Docker Compose neu starten
docker-compose up -d --build
```

---

## REST API Referenz

### Base URL
```
http://localhost:8080
```

### Endpoints

#### 1. Frontend abrufen
```http
GET /
```
**Response:** HTML-Seite mit Interface

---

#### 2. Alle Wörter abrufen
```http
GET /api/words
```

**Response (200 OK):**
```json
{
  "words": [
    {
      "id": 1,
      "word": "Serendipität",
      "meaning": "Das glückliche Finden von etwas Ungesucht",
      "created_at": "2026-03-18T10:30:45"
    },
    {
      "id": 2,
      "word": "Wanderlust",
      "meaning": "Starkes Verlangen zu reisen und die Welt zu erkunden",
      "created_at": "2026-03-18T11:15:20"
    }
  ],
  "count": 2
}
```

---

#### 3. Neues Wort hinzufügen
```http
POST /api/words
Content-Type: application/json

{
  "word": "Schadenfreude",
  "meaning": "Freude über das Unglück anderer"
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "word": "Schadenfreude",
  "meaning": "Freude über das Unglück anderer",
  "created_at": "2026-03-18T12:00:00"
}
```

**Error Response (409 Conflict):**
```json
{
  "error": "Das Wort \"Schadenfreude\" existiert bereits"
}
```

---

#### 4. Wort aktualisieren
```http
PUT /api/words/{id}
Content-Type: application/json

{
  "word": "Schadenfreude",
  "meaning": "Böse Freude über Missgeschick eines anderen"
}
```

**Response (200 OK):**
```json
{
  "id": 3,
  "word": "Schadenfreude",
  "meaning": "Böse Freude über Missgeschick eines anderen",
  "created_at": "2026-03-18T12:00:00"
}
```

---

#### 5. Wort löschen
```http
DELETE /api/words/{id}
```

**Response (204 No Content):**
(Leerer Body, nur Status 204)

---

#### 6. Statistiken abrufen
```http
GET /api/stats
```

**Response (200 OK):**
```json
{
  "total_words": 2,
  "last_added": "2026-03-18T11:15:20",
  "database": "sqlite3",
  "storage": "/data/app.db"
}
```

---

#### 7. Health Check
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "database": "connected"
}
```

**Error Response (500):**
```json
{
  "status": "error",
  "message": "database connection failed"
}
```

---

## Datapersistierung

### Docker Volumes

Die Datenbank wird in einem **Docker Volume** gespeichert, damit Daten bei Container-Neustarts erhalten bleiben.

### Automatische Konfiguration (via `container_manager.py`)

Das Spawner Backend sollte automatisch Volumes mounten:

```python
volumes = {
    f"/volumes/{user_id}": {
        "bind": "/data",
        "mode": "rw"
    }
}
```

**Ergebnis:**
- Jeder User erhält ein eigenes Verzeichnis `/volumes/{user_id}`
- Die SQLite DB wird gespeichert in `/volumes/{user_id}/app.db`
- Der Container sieht dies als `/data/app.db`
- Beim Container-Restart bleiben Daten erhalten

### Manuelles Testen

```bash
# Container starten
docker run -v /volumes/user-123:/data -p 8080:8080 user-template-dictionary:latest

# Datenbank inspizieren
sqlite3 /volumes/user-123/app.db "SELECT * FROM words;"

# Container stoppen und neustart
docker stop <container-id>
docker start <container-id>

# Daten sollten noch da sein!
sqlite3 /volumes/user-123/app.db "SELECT * FROM words;"
```

---

## Datenbankschema

### Tabelle: `words`

```sql
CREATE TABLE words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    meaning TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Spalten:**
- `id` - Eindeutige ID (Auto-Increment)
- `word` - Das Wort (UNIQUE - keine Duplikate!)
- `meaning` - Bedeutung/Definition
- `created_at` - Erstellungsdatum
- `updated_at` - Letztes Update

**Constraints:**
- `word` ist UNIQUE - kann nicht doppelt vorkommen
- Maximale Länge: 255 Zeichen für Wort, 2000 für Bedeutung

---

## Sicherheit

### Input Validation

- ✅ Wort und Bedeutung sind erforderlich
- ✅ Maximale Längen: 255 Zeichen (Wort), 2000 Zeichen (Bedeutung)
- ✅ HTML-Escaping in Frontend (XSS-Schutz)
- ✅ SQL-Injection-Schutz via Prepared Statements

### Error Handling

- ✅ Konsistente JSON-Error-Responses
- ✅ Aussagekräftige Error-Messages
- ✅ HTTP Status Codes korrekt gesetzt
- ✅ Logging aller Fehler

### Docker Security

- ✅ Unprivileged User (nicht Root)
- ✅ Port 8080 (nicht privilegierter Port)
- ✅ SQLite für Single-User (keine Multi-Client Issues)

---

## Monitoring & Debugging

### Logs anschauen

```bash
# Live Logs des Containers
docker logs -f user-dictionary-abc123

# Beispiel Log Output:
# [DICTIONARY] Database path: /data/app.db
# [DICTIONARY] Table 'words' already exists
# [DICTIONARY] Retrieved 2 words
# [DICTIONARY] Word added: 'Serendipität'
```

### Health Check

```bash
# In Chrome DevTools oder terminal:
curl http://localhost:8080/health

# Antwort:
# {"status": "ok", "database": "connected"}
```

### Database Debugging

```bash
# Mit der Python Shell in den Container gehen
docker exec -it <container-id> python

# Dann:
import sqlite3
conn = sqlite3.connect('/data/app.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM words')
print(cursor.fetchall())
```

### Statistiken

```bash
curl http://localhost:8080/api/stats

# Antwort:
# {"total_words": 5, "last_added": "2026-03-18T...", "database": "sqlite3", "storage": "/data/app.db"}
```

---

## Performance & Limits

### Empfehlungen

- **SQLite Limit:** ~1 Million Zeilen problemlos
- **Typical Use:** Bis zu 10.000 Wörter problemlos
- **Query Time:** < 10ms für typische Abfragen
- **Database Size:** ~1KB pro Wort

### Resource Limits (via `.env`)

```bash
# In .env definieren:
DEFAULT_MEMORY_LIMIT=512m      # RAM pro Container
DEFAULT_CPU_QUOTA=50000        # 0.5 CPU
```

### Skalierung

Falls die Anwendung wächst:
1. **PostgreSQL verwenden** statt SQLite (für Multi-User)
2. **Redis Caching** für häufige Abfragen
3. **Elasticsearch** für Full-Text Suche in Bedeutungen

---

## 🔒 Sicherheit & Authentifizierung

### JWT-Cookie Validierung

Das Dictionary-Template ist **obligatorisch geschützt** mit JWT-Token-Validierung:

1. **HttpOnly Cookie `spawner_token`** wird vom Spawner gesetzt
2. **Vor jedem API-Request** wird der Token validiert
3. **Ohne gültigen Token: 403 Forbidden**

### How It Works

```
User Login
   ↓
Spawner setzt HttpOnly Cookie: spawner_token=<JWT>
   ↓
Browser sendet Cookie automatisch bei jedem Request
   ↓
Dictionary-Template validiert JWT in: app.before_request()
   ↓
Gültig? → Erlauben API-Zugriff
Ungültig? → 403 Forbidden (Authentifizierung erforderlich)
```

### Implementation Details

**Token-Validierung in `app.py`:**
```python
@app.before_request
def validate_jwt_token():
    # Öffentliche Endpoints (GET / und /health)
    if request.path == '/' or request.path == '/health':
        return

    # Alle API-Calls brauchen gültigen JWT
    token = request.cookies.get('spawner_token')
    if not token:
        return jsonify({'error': 'Authentifizierung erforderlich'}), 401

    # Dekodiere und validiere JWT
    payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    g.user_id = payload.get('sub')
```

### Sicherheits-Features

- ✅ **HttpOnly Cookies** - JavaScript kann Token nicht auslesen
- ✅ **Secure Flag** - Nur über HTTPS übertragen
- ✅ **SameSite=Lax** - CSRF-Schutz
- ✅ **Token Expiration** - Standard: 1 Stunde (konfigurierbar)
- ✅ **JWT_SECRET** - Wird vom Spawner übergeben
- ✅ **Logout** - Cookie wird beim Logout gelöscht

### Testing der Sicherheit

```bash
# 1. Versuche direkten Zugriff OHNE Login
curl https://spawner.wieland.org/e220dd278a12-template-dictionary/api/words
# → Sollte 401 Unauthorized zurückgeben

# 2. Nach erfolgreichem Login
curl -b "spawner_token=<JWT>" https://spawner.wieland.org/e220dd278a12-template-dictionary/api/words
# → Sollte Wörter-Liste zurückgeben

# 3. Überprüfe Cookie im Browser
# Browser DevTools → Application → Cookies
# → spawner_token sollte HttpOnly markiert sein
```

---

## Troubleshooting

### Problem: "Datenbankfehler beim Abrufen"

```
Mögliche Ursachen:
1. Volume nicht gemountet
2. /data Verzeichnis nicht vorhanden
3. Datenbank-Datei korrupt
4. Permissionen falsch

Lösung:
docker exec container-id ls -la /data
docker exec container-id sqlite3 /data/app.db "SELECT 1"
```

### Problem: "Wort existiert bereits" beim Hinzufügen

```
Das ist normal! Die Anwendung verhindert Duplikate.
Wörter sind eindeutig (UNIQUE Constraint).

Wenn das Problem ist: Bearbeiten statt Hinzufügen nutzen.
Oder: Wort löschen und neu hinzufügen.
```

### Problem: Daten nach Restart weg

```
Ursache: Volume nicht korrekt gemountet.

Prüfen:
docker inspect <container-id> | grep -A10 Mounts

Sollte zeigen:
"Mounts": [
  {
    "Type": "bind",
    "Source": "/volumes/user-123",
    "Destination": "/data"
  }
]
```

### Problem: Container startet nicht

```bash
# Logs prüfen
docker logs <container-id> 2>&1 | tail -50

# Python Syntax prüfen
docker build -t test . --no-cache

# Dockerfile validieren
docker run --rm -it user-template-dictionary:latest python app.py
```

---

## Wartung & Updates

### Backup der Datenbank

```bash
# Einzelnen User-Backup
tar -czf backup-user-123.tar.gz /volumes/user-123/

# Alle User-Datenbanken
tar -czf backup-all-users.tar.gz /volumes/
```

### Datenbank Upgrade

Falls die Tabelle erweitert werden soll:

```python
# In app.py - init_db() Methode:
cursor.execute('''
    ALTER TABLE words ADD COLUMN
    category TEXT DEFAULT 'general'
''')
```

### Logs archivieren

```bash
# Logs rotieren
docker logs --timestamps user-dictionary-abc > logs.txt
```

---

## Integration mit Spawner

### Automatischer Container-Spawn

Wenn ein Benutzer dieses Template wählt:

1. Spawner erstellt Container mit Template `user-template-dictionary:latest`
2. Mountet Volume: `/volumes/{user-id}:/data`
3. Traefik routet Request zu Container unter `https://coder.domain.com/{user-slug}`
4. Benutzer sieht Wörterbuch-Interface
5. Datenbank wird in `/volumes/{user-id}/app.db` erstellt
6. Bei nächstem Login: Gleicher Container + Gleiche Datenbank = Gleiche Wörter!

### Admin-Dashboard Integration

Im Admin-Dashboard können Admins:
- ✅ Container starten/stoppen
- ✅ Container löschen (löscht auch Datenbank!)
- ✅ Logs ansehen
- ✅ Container-Status prüfen

---

## Weitere Verbesserungen (Optional)

### Mögliche Features für Zukunft

1. **Kategorien** - Wörter in Kategorien organisieren
2. **Export/Import** - CSV/JSON Download
3. **Suche** - Volltext-Suche in Wörtern/Bedeutungen
4. **Tags** - Flexible Kategorisierung
5. **Statistiken** - Graphen, Lernfortschritt
6. **Multi-Language** - Übersetzungen hinzufügen
7. **Phonetik** - Audio-Aussprache
8. **Spaced Repetition** - Lern-Algorithmus

---

## Datenschutz & DSGVO

- ✅ Daten werden lokal in Containern gespeichert
- ✅ Keine Daten an Dritte übertragen
- ✅ Benutzer hat vollständige Kontrolle
- ✅ Einfaches Löschen möglich (Container löschen)

---

## Support & Issues

Bei Problemen:

1. Logs prüfen: `docker logs container-id`
2. Health Check testen: `curl http://localhost:8080/health`
3. Datenbank prüfen: `sqlite3 /data/app.db ".tables"`
4. API testen: `curl http://localhost:8080/api/words`

---

## Version & Changelog

**Version:** 1.0.0 (2026-03-18)

### Features
- ✅ Wort hinzufügen/löschen/bearbeiten
- ✅ SQLite Persistierung
- ✅ REST API
- ✅ Modern HTML/CSS/JS Frontend
- ✅ Health Checks
- ✅ Fehlerbehandlung

---

## Lizenz & Attribution

**Template:** Container Spawner
**Autor:** Rainer Wieland
**Lizenz:** MIT oder ähnlich

---

## Letzte Aktualisierung

- **Datum:** 2026-03-18
- **Version:** 1.0.0
- **Status:** Production Ready ✅
