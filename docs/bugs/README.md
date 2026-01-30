# Bekannte Bugs und Limitationen

Aktuelle bekannte Probleme und moegliche Workarounds.

## Inhaltsverzeichnis

- [Bekannte Limitationen](#bekannte-limitationen)
- [Bekannte Bugs](#bekannte-bugs)
- [Workarounds](#workarounds)
- [Issue Tracker](#issue-tracker)

---

## Bekannte Limitationen

### Container Auto-Shutdown nicht implementiert

**Status**: Geplant fuer v0.2.0

**Beschreibung**: Die Variable `CONTAINER_IDLE_TIMEOUT` ist definiert, aber die Logik zum automatischen Stoppen inaktiver Container fehlt noch.

**Auswirkung**: Container laufen unbegrenzt weiter, auch bei Inaktivitaet.

**Workaround**: Manuelles Aufraumen mit Cron-Job:

```bash
# cleanup-idle.sh
#!/bin/bash
# Container die aelter als 24h sind und keinen Traffic haben
docker ps --filter 'label=spawner.managed=true' \
    --format '{{.ID}} {{.RunningFor}}' | \
    grep -E 'days|weeks' | \
    awk '{print $1}' | \
    xargs -r docker stop
```

---

### Keine Volume-Persistenz

**Status**: Geplant fuer v0.2.0

**Beschreibung**: User-Daten in Containern gehen bei Neustart verloren.

**Auswirkung**: Alle Dateien die ein User im Container erstellt werden bei Restart geloescht.

**Workaround**: Volume-Mounts manuell in `container_manager.py` hinzufuegen:

```python
# In spawn_container()
volumes = {
    f'/data/users/{username}': {
        'bind': '/app/data',
        'mode': 'rw'
    }
}
```

---

### Kein Multi-Template-Support

**Status**: Geplant fuer v1.0.0

**Beschreibung**: Alle User erhalten das gleiche Container-Template.

**Auswirkung**: Keine Moeglichkeit verschiedene Umgebungen anzubieten (z.B. Python, Node.js).

**Workaround**: Mehrere Spawner-Instanzen mit unterschiedlichen `USER_TEMPLATE_IMAGE` Werten.

---

### Minimale Input-Validierung

**Status**: Bekannt

**Beschreibung**: Username und Email werden nur minimal validiert.

**Auswirkung**: Potenzielle Injection-Risiken bei speziellen Zeichen.

**Workaround**: Siehe [Sicherheits-Dokumentation](../security/README.md#input-validierung)

---

### Kein Rate-Limiting

**Status**: Geplant fuer v1.0.0

**Beschreibung**: Keine Begrenzung von Login-Versuchen oder API-Aufrufen.

**Auswirkung**: Anfaellig fuer Brute-Force-Angriffe.

**Workaround**: Rate-Limiting via Traefik:

```yaml
# In docker-compose.yml Labels
labels:
  - "traefik.http.middlewares.ratelimit.ratelimit.average=10"
  - "traefik.http.middlewares.ratelimit.ratelimit.burst=20"
  - "traefik.http.routers.spawner.middlewares=ratelimit"
```

---

### Kein Admin-Dashboard

**Status**: Geplant fuer v0.2.0

**Beschreibung**: Keine Web-UI zum Verwalten von Usern und Containern.

**Workaround**: Direkte Datenbank-/Docker-Befehle:

```bash
# User auflisten
docker exec spawner sqlite3 /app/data/users.db "SELECT id, username, email FROM user"

# Container auflisten
docker ps --filter 'label=spawner.managed=true'

# Container eines Users stoppen
docker stop user-<username>-<id>
```

---

## Bekannte Bugs

### BUG-001: Health-Check schlaegt bei erstem Start fehl

**Schweregrad**: Niedrig

**Beschreibung**: Der Health-Check kann beim allerersten Start fehlschlagen, bevor die Datenbank initialisiert ist.

**Schritte zum Reproduzieren**:
1. Frische Installation ohne existierende DB
2. `docker-compose up -d`
3. Sofortiger Health-Check: `curl http://localhost:5000/health`

**Erwartetes Verhalten**: 200 OK

**Tatsaechliches Verhalten**: 503 oder Connection Refused

**Workaround**: 5-10 Sekunden warten nach Start.

**Status**: Akzeptiert (normales Verhalten bei Kaltstart)

---

### BUG-002: Container-Neustart loescht Container-ID nicht bei Fehler

**Schweregrad**: Mittel

**Beschreibung**: Wenn ein Container-Spawn fehlschlaegt, bleibt die alte Container-ID im User-Record.

**Schritte zum Reproduzieren**:
1. User hat laufenden Container
2. Admin loescht Container manuell: `docker rm -f user-xxx`
3. User klickt "Neustart" im Dashboard
4. Spawn schlaegt fehl (z.B. Image nicht gefunden)
5. Container-ID zeigt auf nicht-existierenden Container

**Workaround**: Container-ID manuell zuruecksetzen:

```bash
docker exec spawner sqlite3 /app/data/users.db \
    "UPDATE user SET container_id=NULL WHERE username='<username>'"
```

**Status**: Fix geplant

---

## Workarounds

### Alle User-Container auflisten

```bash
docker ps --filter 'label=spawner.managed=true' \
    --format 'table {{.Names}}\t{{.Status}}\t{{.RunningFor}}'
```

### Container-Ressourcen pruefen

```bash
docker stats --filter 'label=spawner.managed=true' --no-stream
```

### Verwaiste Container aufraumen

```bash
# Container ohne zugehoerigen User finden
for container in $(docker ps -q --filter 'label=spawner.managed=true'); do
    username=$(docker inspect $container --format '{{index .Config.Labels "spawner.username"}}')
    exists=$(docker exec spawner sqlite3 /app/data/users.db \
        "SELECT COUNT(*) FROM user WHERE username='$username'")
    if [ "$exists" = "0" ]; then
        echo "Verwaist: $container ($username)"
        # docker rm -f $container  # Zum Loeschen auskommentieren
    fi
done
```

### Datenbank-Backup manuell erstellen

```bash
docker exec spawner sqlite3 /app/data/users.db ".backup '/app/data/backup-$(date +%Y%m%d).db'"
docker cp spawner:/app/data/backup-*.db ./backups/
```

---

## Issue Tracker

Neue Bugs oder Feature-Requests bitte hier melden:

**Repository Issues**: https://gitea.iotxs.de/RainerWieland/spawner/issues

### Issue erstellen - Vorlage

```markdown
## Beschreibung
[Kurze Beschreibung des Problems]

## Schritte zum Reproduzieren
1. [Erster Schritt]
2. [Zweiter Schritt]
3. [...]

## Erwartetes Verhalten
[Was sollte passieren]

## Tatsaechliches Verhalten
[Was passiert stattdessen]

## Umgebung
- Spawner Version: [z.B. 0.1.0]
- Docker Version: [z.B. 24.0.5]
- OS: [z.B. Ubuntu 22.04]

## Logs
\`\`\`
[Relevante Log-Ausgaben]
\`\`\`
```

---

Zurueck zur [Dokumentations-Uebersicht](../README.md)
