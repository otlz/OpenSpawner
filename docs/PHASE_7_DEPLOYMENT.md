# Phase 7 Deployment Guide: Container-Level Blocking

**Zielgruppe:** DevOps / System Administrators
**Zeitaufwand:** ~15-20 Minuten
**Schwierigkeit:** Mittel (Database Migration erforderlich)

---

## ⚠️ Pre-Deployment Checklist

- [ ] Systemzugang (SSH/Server)
- [ ] Docker Compose kenntnis
- [ ] SQLite/Database Backup Tool verfügbar
- [ ] Downtime-Fenster geplant (optional, ~2 Minuten)
- [ ] Rollback-Plan vorhanden

---

## 🔄 Step-by-Step Deployment

### Step 1: Backup erstellen (⚠️ WICHTIG!)

```bash
# Login auf Server
ssh user@spawner.domain.com
cd /volume1/docker/spawner

# Backup der Database
docker exec spawner sqlite3 /app/spawner.db ".backup /app/spawner.db.backup-phase7-$(date +%Y%m%d_%H%M%S)"

# Backup bestätigen
docker exec spawner ls -la /app/spawner.db.backup*
```

**Output Beispiel:**
```
-rw-r--r-- 1 root root 32768 Feb  4 10:15 /app/spawner.db.backup-phase7-20260204_101500
```

### Step 2: Code Update

```bash
# Repository updaten
git pull origin main

# Neue Datei
ls -la migrate_container_blocking.py
# output: -rw-r--r-- 1 ... migrate_container_blocking.py
```

**Veränderte Dateien:**
- ✅ admin_api.py
- ✅ api.py
- ✅ models.py
- ✅ migrate_container_blocking.py (NEU)
- ✅ frontend/src/lib/api.ts
- ✅ frontend/src/app/admin/page.tsx
- ✅ frontend/src/app/dashboard/page.tsx

### Step 3: Database Migration

#### 3a: Migration Script ausführen

```bash
# Migration mit Python
docker exec spawner python migrate_container_blocking.py
```

**Erwarteter Output:**
```
[MIGRATION] Starte Container Blocking Migration...
[ADD] Füge Spalte 'is_blocked' hinzu...
✅ Spalte 'is_blocked' erstellt
[ADD] Füge Spalte 'blocked_at' hinzu...
✅ Spalte 'blocked_at' erstellt
[ADD] Füge Spalte 'blocked_by' hinzu...
✅ Spalte 'blocked_by' erstellt

[SUCCESS] Migration abgeschlossen!
[INFO] Folgende Änderungen wurden durchgeführt:
  - is_blocked BOOLEAN DEFAULT 0
  - blocked_at DATETIME
  - blocked_by INTEGER FK zu user(id)
```

#### 3b: Migration verifikation

```bash
# Neue Spalten prüfen
docker exec spawner sqlite3 /app/spawner.db ".schema user_container"
```

**Sollte folgende Spalten enthalten:**
```
is_blocked  BOOLEAN  DEFAULT 0  NOT NULL
blocked_at  DATETIME
blocked_by  INTEGER  REFERENCES user(id)
```

#### 3c: Fallback (bei Fehler)

```bash
# Falls Script fehlschlägt - manuell über Docker
docker exec -it spawner sqlite3 /app/spawner.db

# In SQLite:
ALTER TABLE user_container ADD COLUMN is_blocked BOOLEAN DEFAULT 0 NOT NULL;
ALTER TABLE user_container ADD COLUMN blocked_at DATETIME;
ALTER TABLE user_container ADD COLUMN blocked_by INTEGER REFERENCES user(id) ON DELETE SET NULL;

# Exit: .quit
```

### Step 4: Docker Rebuild

```bash
# Frontend neu bauen
docker-compose down

# Neue Images builden
docker-compose up -d --build

# Container starten
docker-compose logs -f spawner
```

**Erwarteter Output (spawner Log):**
```
* Serving Flask app 'app'
 * Running on http://0.0.0.0:5000
 * Press CTRL+C to quit
WARNING: This is a development server. Do not use it in production directly.
```

### Step 5: Health Check

```bash
# API Health
curl -s http://localhost:5000/health | jq .
# Sollte: {"status": "ok"}

# Admin API Test (mit JWT Token)
JWT_TOKEN="your_admin_token_here"
curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:5000/api/admin/users | jq '.total'
# Sollte: [positive Zahl]

# Container Endpoint
curl -s -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:5000/api/user/containers | jq '.containers[0].is_blocked'
# Sollte: false (für nicht blockierte Container)
```

### Step 6: Frontend Verifikation

```bash
# Browser öffnen: https://spawner.domain.com/admin

# Prüfe:
# 1. Admin-Dashboard hat "Container-Verwaltung" Tab? ✓
# 2. Container-Tab zeigt Container-Grid? ✓
# 3. Block/Unblock Buttons sichtbar? ✓
```

---

## 🧪 Post-Deployment Testing

### Test 1: Admin Container blockieren

```bash
# Admin-Dashboard öffnen
# Container auswählen -> "Sperren"

# Verifizierung
docker exec spawner sqlite3 /app/spawner.db \
  "SELECT id, container_type, is_blocked FROM user_container LIMIT 1;"
# Sollte: is_blocked = 1
```

### Test 2: User sieht Blocked-Status

```bash
# User-Dashboard öffnen
# Blockierte Container sollte rot sein
# Button sollte "Gesperrt" sagen

# Backend Logs
docker logs spawner | grep "blockiert"
# Sollte Log-Einträge zeigen
```

### Test 3: Launch-Protection

```bash
# Blockierten Container starten versuchen
# Sollte 403 Error geben

# Log-Beispiel
docker logs spawner | grep "Administrator gesperrt"
```

### Test 4: Bulk-Operations

```bash
# Admin-Dashboard -> mehrere Container auswählen
# Bulk-Block -> Confirm
# Sollte mehrere Container gleichzeitig sperren
```

---

## 🔄 Rollback Procedure

### Falls Probleme auftreten:

```bash
# Option 1: Docker Restart (schneller Fix)
docker-compose down
docker-compose up -d

# Option 2: Zu letztem Commit zurück
git revert a4f85df  # Phase 7 Commit
git push origin main

# Option 3: Database Restore
docker exec spawner sqlite3 /app/spawner.db \
  ".restore /app/spawner.db.backup-phase7-20260204_101500"

# Option 4: Vollständiger Rollback
git reset --hard HEAD~1
docker-compose down
docker-compose up -d --build
```

---

## 📊 Monitoring

### Log-File

```bash
# Backend Logs monitoren
docker logs -f spawner | grep -i "block"

# Beispiel-Output
2026-02-04 10:30:15,123 INFO Container 42 (template-01) gesperrt von Admin 1
2026-02-04 10:31:00,456 WARNING Dieser Container wurde von einem Administrator gesperrt
```

### Database Monitoring

```bash
# Container-Stats
docker exec spawner sqlite3 /app/spawner.db \
  "SELECT COUNT(*) as total, COUNT(CASE WHEN is_blocked THEN 1 END) as blocked FROM user_container;"

# Output: total|blocked
# Beispiel: 15|3
```

### Performance Check

```bash
# Admin-Dashboard Load-Zeit
time curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/admin/users | wc -l

# Sollte < 1 Sekunde sein
```

---

## 🐛 Häufige Probleme

### Problem 1: Migration schlägt fehl mit "ALTER TABLE not allowed"

**Symptom:**
```
ALTER TABLE user_container ADD COLUMN is_blocked BOOLEAN DEFAULT 0;
Error: near "0": syntax error
```

**Lösung:**
```bash
# SQLite erlaubt kein DEFAULT 0 in ALTER TABLE
# Manuell durchführen
docker exec -it spawner sqlite3 /app/spawner.db
> PRAGMA table_info(user_container);
# Sollte is_blocked Spalte ohne DEFAULT zeigen

# Später mit UPDATE füllen:
> UPDATE user_container SET is_blocked = 0 WHERE is_blocked IS NULL;
```

### Problem 2: Admin-Tab zeigt keine Container

**Symptom:**
```
Container-Tab ist leer, obwohl User Container haben
```

**Lösung:**
```bash
# 1. Browser Cache leeren (Ctrl+Shift+Del)
# 2. Prüfe API-Antwort
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/admin/users | jq '.users[0].containers'
# Sollte Array mit Containers sein

# 3. Prüfe Backend-Code
docker exec spawner grep -n "containers" admin_api.py | head -10
```

### Problem 3: Frontend-Build schlägt fehl

**Symptom:**
```
npm run build
> ERROR next build
SyntaxError in admin/page.tsx
```

**Lösung:**
```bash
# 1. Syntax-Fehler prüfen
cd frontend && npm run lint

# 2. Dependencies aktualisieren
rm -rf node_modules package-lock.json
npm install

# 3. Rebuild
npm run build
```

### Problem 4: Blockierte Container lassen sich nicht starten

**Symptom:**
```
Button ist deaktiviert aber ist_blocked = 0 in DB
```

**Lösung:**
```bash
# Frontend-Cache
localStorage.clear()
location.reload()

# API prüfen
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/user/containers | jq '.containers[].is_blocked'

# Falls DB korrekt, Docker neustarten
docker-compose restart spawner
```

---

## 📈 Performance Impact

### Database
- **Neue Spalten:** +3 Spalten (je ~1-4 bytes)
- **Index:** `is_blocked` ist indexed (schnelle Abfragen)
- **Impact:** Vernachlässigbar (~1% größere DB)

### API Response
- **GET /api/admin/users:** +2 neue Felder pro Container
- **Größe:** +~10% bei Usern mit vielen Containern
- **Performance:** < 10ms extra (negligible)

### Frontend
- **Rendering:** +2 extra DOM-Elemente pro Container
- **Performance:** < 5% extra bei 100+ Containern

---

## ✅ Deployment Checklist (Final)

### Vor Deployment:
- [ ] Backup erstellt und verifiziert
- [ ] Team benachrichtigt
- [ ] Maintenance Window eingeplant
- [ ] Rollback-Plan dokumentiert

### Während Deployment:
- [ ] Code gepullt
- [ ] Migration erfolgreich
- [ ] Docker Rebuild erfolgreich
- [ ] Health Checks bestanden

### Nach Deployment:
- [ ] Admin-Tab funktioniert
- [ ] User sehen Blocked-Status
- [ ] Launch-Protection funktioniert
- [ ] Logs zeigen Block-Events
- [ ] Performance ist normal
- [ ] Keine Fehler in Browser-Console

### Langfristig:
- [ ] Monitoring konfiguriert
- [ ] Backups regelmäßig
- [ ] Logs regelmäßig rotiert
- [ ] Performance monitoren

---

## 📞 Support

### Im Fehlerfall:

1. **Logs sammeln:**
   ```bash
   docker logs spawner > spawner_logs.txt
   docker logs traefik > traefik_logs.txt
   docker exec spawner sqlite3 /app/spawner.db ".dump" > db_dump.sql
   ```

2. **Status prüfen:**
   ```bash
   docker ps
   docker-compose logs -f
   curl http://localhost:5000/health
   ```

3. **Rollback wenn nötig:**
   ```bash
   git reset --hard HEAD~1
   docker-compose down
   docker-compose up -d --build
   ```

---

**Deployment durch:** DevOps Team
**Dokumentation:** 2026-02-04
**Kontakt:** admin@domain.com
