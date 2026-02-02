# DEBUG-API Swagger/OpenAPI Dokumentation

**Status:** ✅ Vollständig dokumentiert mit Flasgger
**Zugänglich unter:** `http://localhost:5000/swagger` (UI) oder `http://localhost:5000/openapi.json` (JSON)

---

## 🚀 Schnellstart

### Swagger UI öffnen:
```
http://localhost:5000/swagger
```

### OpenAPI JSON herunterladen:
```
http://localhost:5000/openapi.json
```

---

## 📚 DEBUG-API Endpoints

### 1️⃣ VIEW-LOGS: Letzte 100 Log-Zeilen anzeigen

**Endpoint:** `GET /api/admin/debug?action=view-logs`

**Authentifizierung:**
```bash
# Option 1: Mit DEBUG_TOKEN Header
curl -H "X-Debug-Token: your-secret-token" \
  "http://localhost:5000/api/admin/debug?action=view-logs"

# Option 2: Mit Admin JWT Token
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=view-logs"
```

**Response (200 OK):**
```json
{
  "action": "view-logs",
  "source": "Flask Log File",
  "total_lines": 1234,
  "displayed_lines": 100,
  "logs": "[2026-02-02 17:30:45] User test@example.com registered..."
}
```

**Response (404 Not Found):**
```json
{
  "error": "Log-Datei nicht gefunden: /app/logs/spawner.log"
}
```

---

### 2️⃣ CLEAR-LOGS: Log-Datei leeren

**Endpoint:** `GET|POST /api/admin/debug?action=clear-logs`

**Authentifizierung:** (wie oben)

**Response (200 OK):**
```json
{
  "action": "clear-logs",
  "message": "Log-Datei wurde geleert",
  "log_file": "/app/logs/spawner.log"
}
```

---

### 3️⃣ LIST-USERS: Alle registrierten User auflisten

**Endpoint:** `GET /api/admin/debug?action=list-users`

**Authentifizierung:** (wie oben)

**Response (200 OK):**
```json
{
  "action": "list-users",
  "users": [
    {
      "id": 1,
      "email": "admin@example.com",
      "slug": "u-a1b2c3d4",
      "state": "active",
      "is_admin": true,
      "is_blocked": false,
      "created_at": "2026-01-15T10:30:00",
      "last_used": "2026-02-02T17:30:00"
    },
    {
      "id": 2,
      "email": "user@example.com",
      "slug": "u-e5f6g7h8",
      "state": "verified",
      "is_admin": false,
      "is_blocked": false,
      "created_at": "2026-02-01T14:00:00",
      "last_used": null
    }
  ],
  "total": 2
}
```

---

### 4️⃣ DELETE-EMAIL: User und alle Daten löschen

**Endpoint:** `GET|POST /api/admin/debug?action=delete-email&email=test@example.com`

⚠️ **ACHTUNG:** Dies löscht den User und alle zugehörigen Daten (Container, Tokens, etc.) **komplett**!

**Authentifizierung:** (wie oben)

**Parameter:**
- `email` (required): Email-Adresse des zu löschenden Users

**cURL Beispiel:**
```bash
curl -H "X-Debug-Token: your-secret-token" \
  "http://localhost:5000/api/admin/debug?action=delete-email&email=test@example.com"
```

**Response (200 OK):**
```json
{
  "action": "delete-email",
  "message": "User test@example.com wurde gelöscht",
  "user_id": 123
}
```

**Response (404 Not Found):**
```json
{
  "error": "User test@example.com nicht gefunden"
}
```

**Response (500 Error):**
```json
{
  "error": "Fehler beim Löschen: Docker container not found"
}
```

---

### 5️⃣ DELETE-TOKEN: Magic Link Tokens für User löschen

**Endpoint:** `GET|POST /api/admin/debug?action=delete-token&email=test@example.com`

Entfernt alle Magic Link Tokens für einen User (nützlich bei Token-Spam).

**Authentifizierung:** (wie oben)

**Parameter:**
- `email` (required): Email-Adresse des Users

**cURL Beispiel:**
```bash
curl -H "X-Debug-Token: your-secret-token" \
  "http://localhost:5000/api/admin/debug?action=delete-token&email=test@example.com"
```

**Response (200 OK):**
```json
{
  "action": "delete-token",
  "message": "5 Tokens für test@example.com gelöscht",
  "tokens_deleted": 5
}
```

---

### 6️⃣ INFO: Hilfe und verfügbare Actions

**Endpoint:** `GET /api/admin/debug` oder `GET /api/admin/debug?action=info`

Zeigt diese Hilfe mit allen verfügbaren Actions an.

**Response (200 OK):**
```json
{
  "endpoint": "/api/admin/debug",
  "auth": "X-Debug-Token Header oder Admin JWT",
  "actions": {
    "view-logs": "Zeigt letzte 100 Zeilen der Logs",
    "clear-logs": "Löscht alle Logs",
    "list-users": "Listet alle registrierten User auf",
    "delete-email": "Löscht User (Parameter: email=...)",
    "delete-token": "Löscht Magic Link Tokens (Parameter: email=...)",
    "info": "Diese Hilfe"
  },
  "examples": [...]
}
```

---

## 🔐 Authentifizierung

Die DEBUG-API unterstützt zwei Authentifizierungsmethoden:

### Methode 1: DEBUG_TOKEN (Empfohlen)

```bash
curl -H "X-Debug-Token: your-secret-token" \
  "http://localhost:5000/api/admin/debug?action=list-users"
```

**Konfigurieren in `.env`:**
```bash
DEBUG_TOKEN=your-super-secret-token-here
```

**In Docker:**
```bash
docker exec spawner cat /app/.env | grep DEBUG_TOKEN
```

### Methode 2: JWT Admin Token

```bash
# 1. JWT Token von Admin abrufen
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com"}'

# Magic Link Token klicken/kopieren...

# 2. Mit JWT Token DEBUG-API aufrufen
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=list-users"
```

---

## 📋 Swagger API Spezifikation

### Automatisch generiert:

Flasgger generiert automatisch OpenAPI 3.0 Spezifikation aus den Python-Docstrings.

**Verfügbar unter:**
- **UI:** `http://localhost:5000/swagger`
- **JSON:** `http://localhost:5000/openapi.json`
- **YAML:** `http://localhost:5000/apispec.json`

### Herunterladen & Importieren:

```bash
# OpenAPI JSON herunterladen
curl http://localhost:5000/openapi.json > swagger.json

# In Postman importieren:
# 1. Postman öffnen
# 2. File → Import
# 3. swagger.json wählen
```

---

## 🧪 Test-Beispiele

### Test 1: Logs anzeigen
```bash
DEBUG_TOKEN=secret123
curl -H "X-Debug-Token: $DEBUG_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=view-logs" | jq '.logs | head -20'
```

### Test 2: User auflisten
```bash
curl -H "X-Debug-Token: $DEBUG_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=list-users" | jq '.users[] | {email, state, is_blocked}'
```

### Test 3: User löschen (Vorsicht!)
```bash
curl -H "X-Debug-Token: $DEBUG_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=delete-email&email=test@example.com"
```

### Test 4: Tokens für User löschen
```bash
curl -H "X-Debug-Token: $DEBUG_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=delete-token&email=spam@example.com"
```

---

## ⚠️ Wichtige Hinweise

### DEBUG_TOKEN in Production

**Sicherheit:**
- ✅ Verwende starken, zufälligen Token (min. 32 Zeichen)
- ✅ Speichere Token **nicht** im Git-Repo
- ✅ Nur `.env` hat den Token (in `.gitignore`)
- ⚠️ DEBUG-Endpoints sind nur für Admin/Development
- ❌ Nicht in produktiven URLs exponieren

**Best Practice:**
```bash
# Generiere sicheren Token
python3 -c "import secrets; print(secrets.token_hex(32))"

# In .env speichern (nicht committen!)
DEBUG_TOKEN=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### Datenschutz (DSGVO)

Die DEBUG-API kann User komplett löschen (inkl. Containers, Tokens, Sessions).

**Protokollierung:**
```bash
# Admin-Aktion wird geloggt
[2026-02-02 17:30:45] User test@example.com vollständig gelöscht von Admin admin@example.com
```

**Verifikation:**
```bash
# Prüfe ob User gelöscht wurde
docker exec spawner python3 -c "
from app import app, db
from models import User
with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    print('User found!' if user else 'User deleted ✓')
"
```

---

## 🔗 Integration in Tools

### Postman
```
1. File → Import
2. Link: http://localhost:5000/openapi.json
3. Collection erstellt mit allen Endpoints
```

### Swagger Editor
```
1. https://editor.swagger.io öffnen
2. File → Import URL
3. http://localhost:5000/openapi.json eintragen
```

### Insomnia
```
1. Application → Preferences → Data
2. "Import Data"
3. URL: http://localhost:5000/openapi.json
```

---

## 📊 OpenAPI Spezifikation

**Version:** 3.0.0
**Title:** Container Spawner API
**Version:** 2.0.0
**Base Path:** `/api/admin`

### Security Schemes:
- `jwt`: Bearer Token (JWT)
- `debug_token`: X-Debug-Token Header

### Endpoint Tags:
- `Debug` - DEBUG-API Endpoints
- `Admin` - Admin-Management Endpoints
- `Auth` - Authentifizierung

---

## 🐛 Troubleshooting

### Problem: Swagger UI zeigt 404

```bash
# Prüfe ob Flasgger installiert ist
docker exec spawner pip list | grep flasgger

# Falls nicht installiert:
docker exec spawner pip install flasgger==0.9.7.1
docker-compose restart spawner
```

### Problem: DEBUG_TOKEN wird nicht erkannt

```bash
# Prüfe ob DEBUG_TOKEN in .env definiert ist
docker exec spawner cat /app/.env | grep DEBUG_TOKEN

# Falls leer, füge hinzu:
# DEBUG_TOKEN=your-secret-token
docker-compose down
docker-compose up -d
```

### Problem: OpenAPI JSON ist leer

```bash
# Prüfe Flasgger-Version
docker exec spawner pip show flasgger

# Falls veraltete Version:
docker exec spawner pip install --upgrade flasgger
docker-compose restart spawner
```

---

## 📝 Dokumentation aktualisieren

Bei neuen DEBUG-Endpoints:

1. **Python-Docstring mit YAML aktualisieren**
   ```python
   @admin_bp.route('/debug/new-action', methods=['GET'])
   def new_action():
       """
       Neue Aktion
       ---
       tags:
         - Debug
       parameters:
         - name: param
           in: query
           type: string
       responses:
         200:
           description: Erfolg
       """
   ```

2. **Diese Dokumentation updaten** (guides/debug-api-swagger.md)

3. **Flasgger generiert UI automatisch** unter `/swagger`

---

**Zuletzt aktualisiert:** 2026-02-02
**Flasgger-Version:** 0.9.7.1
**OpenAPI-Version:** 3.0.0
