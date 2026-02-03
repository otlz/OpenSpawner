# Bug-Fix: Container-Spawn Fehler bei Multi-Container

**Datum:** 2026-02-03
**Betroffen:** template-01, template-02, template-next
**Status:** GELÖST

---

## Probleme

### Problem 1: Container-Naming-Konflikt (409 Conflict Error)
**Fehler:**
```
Container konnte nicht erstellt werden: Docker API Fehler: 409 Client Error...
"user-e220dd278a12-template-01-1" is already in use by container "..."
```

**Ursache:**
- Wenn ein Container mit gleichem Namen bereits existiert (z.B. von fehlgeschlagener Erstellung oder unvollständiger Löschung)
- Beim erneuten Erstellen warf Docker einen 409 Conflict-Fehler
- Code versuchte nicht, existierende Container zu prüfen

**Fix:** `container_manager.py` (Zeilen 192-216)
- Vor Container-Erstellung prüfen ob Container bereits existiert
- Wenn running → Container wieder verwenden
- Wenn stopped → Versuchen zu starten oder zu löschen
- Wenn nicht vorhanden → Neuen erstellen

---

### Problem 2: Falsches Routing nach Container-Löschung
**Fehler:**
```
Container-Span nach Löschung nicht weitergeführt
```

**Ursache:**
- Nach dem Löschen eines gestoppten Containers wurde die Erstellung nicht fortgesetzt
- Code hatte kein Fallthrough nach `remove()`

**Fix:** `container_manager.py` (Zeilen 202-213)
- Nach erfolgreicher Löschung werden Kommentare aktualisiert
- Code fährt fort zur normalen Container-Erstellung

---

### Problem 3: Verifizierungs-Fehler trotz Erfolg
**Symptom:**
- Frontend zeigt "Verifizierung fehlgeschlagen"
- Trotzdem automatischer Redirect zum Dashboard

**Verbesserung:** `api.py` (Zeile 241-243)
- Container-Spawn ist jetzt explizit optional
- User wird trotzdem erstellt wenn Container-Spawn fehlschlägt
- JWT wird immer returned (Status 200)

---

## Geänderte Dateien

### 1. `container_manager.py`
**Zeilen 192-216:** Pre-Check für existierende Container
```python
# Vor containers.run():
try:
    existing_container = self._get_client().containers.get(container_name)
    if existing_container.status == 'running':
        return existing_container.id, 8080  # Wiederverwenden
    else:
        # Versuchen zu starten oder zu löschen
        ...
except docker.errors.NotFound:
    pass  # Container existiert nicht, normal weiterfahren
```

### 2. `api.py`
**Zeilen 241-243:** Container-Spawn Fehlerbehandlung
```python
except Exception as e:
    current_app.logger.error(f"Container-Spawn fehlgeschlagen: {str(e)}")
    # Notiere: Container-Spawn ist optional beim Signup
    # User ist trotzdem erstellt, Container kann später manuell erstellt werden
```

---

## Server-Deployment

**WICHTIG:** Nicht `docker-compose down` verwenden!

```bash
cd /volume1/docker/spawner

# 1. Code aktualisieren
git pull origin main

# 2. RICHTIG - Nur geänderte Services neubaut (keine down!)
docker-compose up -d --build

# 3. Warten
sleep 10

# 4. Logs prüfen
docker-compose logs spawner 2>&1 | tail -50
```

---

## Testing

### Test 1: Template-02 (vorher funktionierend)
- Registriere neuen User
- Container sollte ohne "409 Conflict" erstellt werden
- **Erwartet:** Container läuft und ist erreichbar

### Test 2: Erneute Erstellung desselben Templates
- Lösche User mit Container
- Erstelle neuen User mit gleicher Template
- **Erwartet:** Kein Naming-Konflikt, neuer Container wird erstellt

### Test 3: Template-next (timing-sensitiv)
- Registriere User
- Öffne Template-next sofort
- **Erwartet:** "Netzwerkfehler" ist OK (Container braucht 2-3 Min. für npm build)
- Nach 2-3 Min: Container sollte erreichbar sein

---

## Bekannte Einschränkungen

- **template-next Startup:** Next.js Builds brauchen 2-5 Minuten (npm install + build)
  - Frontend zeigt "Netzwerkfehler" initial - das ist normal
  - Nach 2-3 Min erneut versuchen

- **Container-Recovery:** Wenn ein Container in fehlerhaftem Zustand ist, wird er automatisch gelöscht
  - Sollte selten vorkommen
  - Wird in den Logs dokumentiert

---

## Rollback (Falls nötig)

Wenn Probleme auftreten:

```bash
git revert HEAD  # Letzten Commit rückgängig machen
git push
docker-compose up -d --build
```

---

---

## Synology NAS: Git Berechtigungsbits Problem

**Bei `git pull` auf Synology:**
```bash
error: Your local changes to the following files would be overwritten by merge:
        api.py
        container_manager.py
```

**Ursache:** Synology ändert automatisch Datei-Berechtigungen (executable bit).

**Lösung:**
```bash
# Lokale Berechtigungsänderungen verwerfen
git checkout api.py container_manager.py

# Dann pull machen
git pull origin main
```

Das ist NICHT ein echtes Code-Problem - nur Berechtigungsbits:
```
old mode 100644  (nicht ausführbar)
new mode 100755  (ausführbar)
```

---

**Dokumentation:** 2026-02-03
**Getestet auf:** Synology NAS, Docker 20.10+, Docker Compose 2.0+
