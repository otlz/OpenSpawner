# Kritische Fixes - März 2026

Diese Datei dokumentiert wichtige Bugfixes und Verbesserungen, die seit März 2026 implementiert wurden.

## 1. Traefik Network Routing Fix ✅

**Problem:** User-Container wurden nicht im `web`-Netzwerk registriert, obwohl Labels vorhanden waren.

**Ursache:** Docker SDK Parameter `network=` funktioniert nicht korrekt bei `containers.run()`.

**Lösung:** Explizite Netzwerk-Verbindung nach Container-Start mit `network.connect()`.

```python
# Vorher (funktioniert nicht):
container = client.containers.run(..., network=Config.TRAEFIK_NETWORK)

# Nachher (funktioniert):
container = client.containers.run(...)  # Ohne network-Parameter
network = client.networks.get(Config.TRAEFIK_NETWORK)
network.connect(container)
```

**Commits:**
- `65a2a6e`: Connect containers to Traefik network using network.connect()

**Betroffen:** `container_manager.py` - Beide `spawn_container()` und `spawn_multi_container()`

---

## 2. Traefik Router Service-Labels Fix ✅

**Problem:** Traefik erkannte neue Container-Routes nicht, obwohl Labels korrekt waren.

**Ursache:** Router-Labels fehlte die Referenz zum Service. Traefik wusste nicht, zu welchem Service die Route führen soll.

**Lösung:** Router-Labels mit `.service` Claim hinzufügen, die auf den Service zeigen.

```python
# Vorher (unvollständig):
'traefik.http.routers.user1-template-dict.rule': '...',
'traefik.http.services.user1-template-dict.loadbalancer.server.port': '8080'

# Nachher (komplett):
'traefik.http.routers.user1-template-dict.rule': '...',
'traefik.http.routers.user1-template-dict.service': 'user1-template-dict',  # ← Wichtig!
'traefik.http.services.user1-template-dict.loadbalancer.server.port': '8080'
```

**Commits:**
- `45bd329`: Add missing router.service labels

**Betroffen:** `container_manager.py` - Labels-Konfiguration

---

## 3. Cookie-basierte JWT-Authentication ✅

**Problem:** User-Container waren öffentlich zugänglich - jeder konnte URL nutzen ohne Login.

**Lösung:** JWT-Token als HttpOnly Cookie, validiert in jedem Container.

**Implementierung:**

### Backend (api.py)
- JWT-Token wird als HttpOnly Cookie nach Login gespeichert
- Cookie wird automatisch bei jedem Request mitgesendet
- Logout löscht den Cookie

```python
def create_auth_response(access_token, user_data, expires_in):
    response = make_response(jsonify(response_data))
    response.set_cookie(
        'spawner_token',
        access_token,
        max_age=expires_in,
        httponly=True,      # JavaScript-zugriff blockiert
        secure=True,        # Nur über HTTPS
        samesite='Lax'      # CSRF-Schutz
    )
    return response
```

### Container (z.B. Dictionary-Template)
- `before_request` Hook validiert JWT im Cookie
- Ohne gültigen Token: `403 Forbidden`
- JWT_SECRET wird vom Spawner als Environment-Variable übergeben

```python
@app.before_request
def validate_jwt_token():
    # GET / und /health sind öffentlich
    if request.path == '/' or request.path == '/health':
        return

    # Alle API-Calls brauchen gültigen Token
    token = request.cookies.get('spawner_token')
    if not token:
        return jsonify({'error': 'Authentifizierung erforderlich'}), 401

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        g.user_id = payload.get('sub')
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token ungültig'}), 401
```

**Commits:**
- `436b1c0`: Add cookie-based JWT authentication for user containers

**Betroffen:**
- `api.py` - JWT-Cookie setzen/löschen
- `container_manager.py` - JWT_SECRET als Environment-Variable
- `user-template-dictionary/app.py` - JWT-Validierung
- `user-template-dictionary/requirements.txt` - PyJWT hinzugefügt

---

## 4. install.sh Improvements ✅

### 4a. Git-Pull Auto-Fix für Synology

**Problem:** Auf Synology schlugen `git pull` Befehle fehl wegen Dateiberechtigungen.

**Lösung:**
```bash
git config core.filemode false    # Ignoriere Berechtigungsbits
git reset --hard origin/main      # Force-Sync mit Remote
```

**Commits:**
- `7111d7a`: Auto-fix git pull with core.filemode

### 4b. Update-and-Re-Exec Mechanism

**Problem:** Wenn `install.sh` selbst aktualisiert wird, lädt bash die alte Version weiter.

**Lösung:** Nach `git pull` Checksumme vergleichen und Script neu starten mit `exec bash`.

```bash
BEFORE_HASH=$(md5sum install.sh)
# ... git pull ...
AFTER_HASH=$(md5sum install.sh)

if [ "$BEFORE_HASH" != "$AFTER_HASH" ]; then
    export ALREADY_REEXECED="true"
    exec bash install.sh
fi
```

**Commits:**
- `bb25750`: Add update-and-re-exec mechanism

### 4c. Alte Container Auto-Cleanup

**Problem:** Nach Code-Updates blieben alte Container und verursachten Traefik-Konflikte.

**Lösung:** `install.sh` löscht alle alten User-Container vor Restart.

```bash
# install.sh Sektion 8:
docker rm -f $(docker ps -a | grep "user-" | awk '{print $1}')
```

**Commits:**
- `7beb1d0`: Add detailed output for old container cleanup

**Betroffen:** `install.sh`

---

## 5. Dictionary Template Routing Fix ✅

**Problem:** `/api/words` Requests return 404 weil Traefik den Pfad-Prefix nicht entfernt.

**Lösung:** API-Base-Pfad aus `window.location.pathname` berechnen.

```javascript
// Vorher (falsch):
const response = await fetch('/api/words')

// Nachher (richtig):
const apiBase = window.location.pathname.replace(/\/$/, '');  // z.B. "/e220dd278a12-template-dictionary"
const response = await fetch(`${apiBase}/api/words`)
```

**Commits:**
- `20a4d60`: Fix API paths in Dictionary template for Traefik routing

**Betroffen:** `user-template-dictionary/templates/index.html`

---

## Zusammengefasst

| Fix | Status | Commits | Wichtigkeit |
|-----|--------|---------|-------------|
| Traefik Network (network.connect) | ✅ | 65a2a6e | 🔴 KRITISCH |
| Traefik Router Service-Labels | ✅ | 45bd329 | 🔴 KRITISCH |
| JWT-Cookie-Auth | ✅ | 436b1c0 | 🔴 KRITISCH (Security) |
| install.sh Git-Fix | ✅ | 7111d7a | 🟡 Wichtig |
| install.sh Re-Exec | ✅ | bb25750 | 🟡 Wichtig |
| install.sh Container-Cleanup | ✅ | 7beb1d0 | 🟡 Wichtig |
| Dictionary API-Paths | ✅ | 20a4d60 | 🟡 Wichtig |

---

## Deployment-Schritte

Nach diesen Fixes sollte auf der Synology folgende Procedure ausgeführt werden:

```bash
bash install.sh
```

Das führt automatisch aus:
1. `git pull` mit Auto-Fix für Berechtigungen
2. Falls install.sh sich geändert hat: Neu starten
3. Alte User-Container löschen (Traefik-Konflikt-Prävention)
4. Alle Templates aus .env bauen
5. Docker-Compose mit neuen Containern starten

---

## Testen nach Deployment

1. **User-Authentication testen:**
   ```bash
   # Mit Browser: https://spawner.wieland.org/
   # Login mit Magic Link
   ```

2. **Container-Routing testen:**
   ```bash
   # Container sollte im web-Netzwerk sein
   docker network inspect web | grep user-
   ```

3. **JWT-Protection testen:**
   ```bash
   # Versuche direkten Container-Zugriff OHNE Login
   curl https://spawner.wieland.org/e220dd278a12-template-dictionary/api/words
   # → Sollte 401 Unauthorized zurückgeben
   ```

4. **JWT-Cookie testen:**
   ```bash
   # Nach erfolgreichem Login:
   # Browser-DevTools → Application → Cookies
   # → spawner_token sollte vorhanden und HttpOnly markiert sein
   ```
