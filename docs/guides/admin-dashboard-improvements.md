# Admin-Dashboard: Verbesserte Container- und User-Löschung

**Datum:** 02.02.2026
**Version:** 2.0
**Status:** ✅ Vollständig implementiert

---

## 📋 Übersicht

Diese Dokumentation beschreibt die Verbesserungen des Admin-Dashboards:

1. **Multi-Container-Deletion** - Alle Container eines Users löschen (nicht nur Primary)
2. **Toast-Benachrichtigungen** - Modernes UI statt primitiver Alerts
3. **Bulk-Operations** - Mehrere User gleichzeitig verwalten (Sperren, Löschen, etc.)
4. **DSGVO-Compliance** - Vollständige Datenlöschung (MagicLinkToken, AdminTakeoverSession)

---

## 🔧 Technische Änderungen

### 1. Backend - Multi-Container & DSGVO

**Datei:** `admin_api.py`

#### DELETE `/api/admin/users/<id>/container` (aktualisiert)
Löscht alle Docker-Container eines Users (nicht nur Primary Container):

```python
# Vorher (begrenzt auf Primary):
if user.container_id:
    container_mgr.stop_container(user.container_id)
    container_mgr.remove_container(user.container_id)

# Nachher (alle Container):
for container in user.containers:
    if container.container_id:
        container_mgr.stop_container(container.container_id)
        container_mgr.remove_container(container.container_id)
        db.session.delete(container)
```

**Response:**
```json
{
  "message": "Alle 3 Container von user@example.com wurden gelöscht",
  "deleted": 3,
  "failed": []
}
```

#### DELETE `/api/admin/users/<id>` (aktualisiert - DSGVO)
Löscht einen User komplett mit allen Daten:

```python
# 1. Docker-Container löschen
# 2. MagicLinkToken löschen (DSGVO: IP-Adressen)
# 3. AdminTakeoverSession löschen (als Target-User)
# 4. User-Account löschen (CASCADE löscht UserContainer)
```

**Response mit DSGVO-Summary:**
```json
{
  "message": "User test@example.com wurde vollständig gelöscht",
  "summary": {
    "containers_deleted": 3,
    "containers_failed": [],
    "magic_tokens_deleted": 5,
    "takeover_sessions_deleted": 0
  }
}
```

### 2. Datenbank - CASCADE DELETE

**Datei:** `models.py`

**MagicLinkToken (Zeile 110-118):**
```python
user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
user = db.relationship('User', backref=db.backref('magic_tokens', lazy=True, cascade='all, delete-orphan'))
```

**AdminTakeoverSession (Zeile 171-180):**
```python
admin_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
target_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

admin = db.relationship('User', foreign_keys=[admin_id],
                       backref=db.backref('takeover_sessions_as_admin', lazy=True))
target_user = db.relationship('User', foreign_keys=[target_user_id],
                             backref=db.backref('takeover_sessions_as_target', lazy=True, cascade='all, delete-orphan'))
```

**Warum:**
- `admin_id: SET NULL` - Erhält Audit-Log auch wenn Admin gelöscht wird
- `target_user_id: CASCADE` - Session wird gelöscht wenn User gelöscht wird
- Verhindert Foreign-Key-Constraint-Fehler

### 3. Frontend - Toast-System & Bulk-Operations

**Datei:** `frontend/package.json`
```json
{
  "dependencies": {
    "sonner": "^1.7.2"
  }
}
```

**Datei:** `frontend/src/app/layout.tsx`
```tsx
import { Toaster } from "sonner";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
```

**Datei:** `frontend/src/app/admin/page.tsx` - Neue Features:

#### Toast-Nachrichten statt primitiver Alerts:
```typescript
// Vorher
setSuccessMessage(message);
setTimeout(() => setSuccessMessage(""), 3000);

// Nachher
toast.success(message);  // Modern, stackbar, dunkler
toast.error(`Fehler: ${error}`);
toast.loading("Lösche User...", { id: "delete" });
```

#### Bulk-Selection UI:
- User-Checkboxen pro Zeile (nicht Admin/CurrentUser)
- "Select All" Checkbox für gefilterte User
- Bulk-Action-Bar mit 4 Aktionen:
  - Sperren / Entsperren
  - Container löschen
  - User löschen (mit Zwei-Schritt-Bestätigung)

#### Zwei-Schritt-Bestätigung bei kritischen Aktionen:
```typescript
// Schritt 1: Vorschau mit Warnung
if (!confirm(`⚠️ WARNUNG: 3 User löschen?\n\nDies löscht:\n- User-Accounts\n- Alle Container\n- Alle Tokens`)) {
  return;
}

// Schritt 2: Numerische Bestätigung
const confirmation = prompt(`Geben Sie die Anzahl ein (3):`);
if (confirmation !== "3") {
  toast.error("Abgebrochen");
  return;
}
```

---

## 🚀 Deployment

### Vorbereitungen:

1. **Backend:**
   ```bash
   # Syntax-Check
   python -m py_compile admin_api.py models.py
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install  # Installiert sonner
   npm run build
   npx tsc --noEmit  # TypeScript-Check
   ```

### Deployment-Befehle:

```bash
# Lokal/Entwicklung
cd /volume1/docker/spawner
git pull
docker-compose up -d --build
```

### Nach Deployment:

```bash
# Logs checken
docker-compose logs -f spawner

# Admin-Dashboard testen
# 1. Einen User mit Containern erstellen
# 2. Container löschen → Toast sollte erscheinen
# 3. User löschen → Toast mit Summary
```

---

## 🧪 Test-Szenarien

### Test 1: Multi-Container-Deletion
```bash
# Voraussetzung: User mit 3 Containern (template-01, template-02, template-next)

# 1. Admin-Dashboard öffnen
# 2. Container-Icon klicken
# 3. Toast: "3 Container gelöscht"
# 4. Verify: docker ps | grep user- → Keine Container
```

### Test 2: DSGVO-Compliance
```bash
# 1. User mit Magic Links erstellen
# 2. Admin: User löschen → Zwei-Schritt-Bestätigung
# 3. Toast mit Summary:
#    - 3 Container deleted
#    - 5 Magic Tokens deleted
#    - 0 Takeover Sessions deleted

# 4. Verify in DB:
docker exec spawner python3 -c "
from app import app, db
from models import MagicLinkToken
with app.app_context():
    tokens = MagicLinkToken.query.filter_by(user_id=123).count()
    print(f'Tokens für User 123: {tokens}')
"
# Expected: 0
```

### Test 3: Toast-Benachrichtigungen
```
1. Admin-Dashboard öffnen
2. Mehrere Aktionen schnell:
   - Container löschen
   - User sperren
   - User entsperren
3. Erwartung: Toasts stacken oben-rechts, jeder mit X zum Schließen
```

### Test 4: Bulk-Operations
```
1. 3 User mit Checkboxen auswählen
2. Bulk-Action-Bar erscheint
3. "Sperren" Button → Confirm → Toast "3 User gesperrt"
4. "Select All" Checkbox → Alle (außer Admin) ausgewählt
5. "User löschen" → Zwei-Schritt-Bestätigung → Toast mit Summary
```

---

## 📊 API-Response-Format

### Single Container-Deletion:
```bash
curl -X DELETE \
  http://localhost:5000/api/admin/users/123/container \
  -H "Authorization: Bearer $TOKEN"
```

**Response (Success):**
```json
{
  "message": "Alle 3 Container von user@example.com wurden gelöscht",
  "deleted": 3,
  "failed": []
}
```

**Response (Partial Failure - Status 207):**
```json
{
  "message": "2 Container gelöscht, 1 fehlgeschlagen",
  "deleted": 2,
  "failed": ["a1b2c3d4"]
}
```

### Single User-Deletion:
```bash
curl -X DELETE \
  http://localhost:5000/api/admin/users/123 \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "message": "User user@example.com wurde vollständig gelöscht",
  "summary": {
    "containers_deleted": 3,
    "containers_failed": [],
    "magic_tokens_deleted": 5,
    "takeover_sessions_deleted": 1
  }
}
```

---

## ⚠️ Wichtige Hinweise

### Breaking Change: CASCADE DELETE
- Foreign Key Constraints wurden aktualisiert
- **DB-Migration erforderlich** (siehe unten)
- Alte Constraints verursachen Fehler

### Datenbank-Migration:

#### Option 1: Mit Alembic (falls installiert)
```bash
cd backend
flask db migrate -m "Add CASCADE DELETE for DSGVO"
flask db upgrade
```

#### Option 2: Manuell für SQLite
```sql
-- Backup zuerst machen!
.backup /app/spawner.db.backup

-- MagicLinkToken
ALTER TABLE magic_link_token
  DROP CONSTRAINT IF EXISTS magic_link_token_user_id_fkey;
ALTER TABLE magic_link_token
  ADD CONSTRAINT magic_link_token_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE;

-- AdminTakeoverSession
ALTER TABLE admin_takeover_session
  DROP CONSTRAINT IF EXISTS admin_takeover_session_admin_id_fkey;
ALTER TABLE admin_takeover_session
  DROP CONSTRAINT IF EXISTS admin_takeover_session_target_user_id_fkey;

ALTER TABLE admin_takeover_session
  ADD CONSTRAINT admin_takeover_session_admin_id_fkey
  FOREIGN KEY (admin_id) REFERENCES user(id) ON DELETE SET NULL;
ALTER TABLE admin_takeover_session
  ADD CONSTRAINT admin_takeover_session_target_user_id_fkey
  FOREIGN KEY (target_user_id) REFERENCES user(id) ON DELETE CASCADE;
```

### Backwards Compatibility:
- ✅ Alte API-Clients funktionieren (neue Felder sind optional)
- ✅ Bestehende User-Daten bleiben erhalten
- ⚠️ Nur neue Deletes sind DSGVO-konform

---

## 🔍 Troubleshooting

### Problem: Toasts erscheinen nicht
```bash
# 1. Prüfe ob sonner installiert ist
cd frontend
npm list sonner

# 2. Browser-Console (F12) auf Fehler prüfen
# 3. Cache leeren: Ctrl+Shift+Del
```

### Problem: Container-Löschung funktioniert nicht
```bash
# Logs prüfen
docker-compose logs spawner 2>&1 | tail -100

# Docker-Socket-Permissions
docker exec spawner ls -la /var/run/docker.sock

# Container manuell löschen
docker ps -a | grep user-
docker rm -f user-xyz-123
```

### Problem: Multi-Container nicht sichtbar
```bash
# DB-Abfrage
docker exec spawner python3 -c "
from app import app, db
from models import User
with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    print(f'User {user.email} hat {len(user.containers)} Container')
    for c in user.containers:
        print(f'  - Type: {c.container_type}, ID: {c.container_id}')
"
```

---

## 📚 Weitere Ressourcen

- [Container Spawner Architektur](../architecture/README.md)
- [Deployment Guide](../install/DEPLOYMENT_GUIDE.md)
- [Custom Templates](./custom-templates.md)
- [Security Dokumentation](../security/README.md)

---

## 📝 Änderungshistorie

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 2.0 | 02.02.2026 | Multi-Container, Toast-System, Bulk-Operations, DSGVO |
| 1.0 | ≤01.02.2026 | Ursprüngliches Admin-Dashboard |

---

**Fragen?** Siehe [Troubleshooting](#-troubleshooting) oder Logs prüfen: `docker-compose logs spawner`
