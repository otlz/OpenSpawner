# 💻 ESP8266 IDE Template - Vollständige Dokumentation

## Übersicht

Das **ESP8266 IDE Template** (`user-template-vcoder`) ist eine vollständige Web-basierte Entwicklungsumgebung für ESP8266/Wemos-Mikrocontroller-Projekte. Es kombiniert **code-server** (VS Code Web IDE) mit **PlatformIO** für embedded Systems-Entwicklung.

### Features

- ✅ **Code-Server Web IDE** - VS Code im Browser
- ✅ **PlatformIO Extension** - Embedded Systems Entwicklung
- ✅ **C/C++ Tools** - cpptools + clangd für Code Completion
- ✅ **Workspace Persistierung** - Projekte bleiben erhalten
- ✅ **PlatformIO Cache** - Toolchains werden gecacht
- ✅ **Port 8080** - Standardisiert für Spawner Integration
- ✅ **Authentication deaktiviert** - Spawner JWT übernimmt Schutz

---

## Architektur

### High-Level Diagramm

```
Browser Request
     ↓
code-server Web IDE (Port 8080)
     ↓
     ├─ /home/coder/project (Workspace - Volume)
     ├─ /home/coder/.platformio (Cache - Volume)
     └─ Extensions (cpptools, PlatformIO IDE, clangd)
     ↓
Persistente Speicherung (Docker Volumes)
```

### Komponenten

**code-server:**
- VS Code Server im Browser
- Port 8080
- `--auth=none` (Spawner JWT übernimmt den Schutz)
- Automatische Extension-Installation

**PlatformIO:**
- Venv unter `/home/coder/.platformio/penv`
- Unterstützt ESP8266, Wemos D1 Mini, etc.
- Toolchains werden gecacht für schnelle Builds

**Extensions:**
- **cpptools** (Microsoft C/C++) - IntelliSense, Debugging
- **platformio-ide** (PlatformIO IDE) - Build, Upload, Monitor
- **clangd** (LLVM) - C/C++ Language Server

**Volumes (Persistent):**
- `/home/coder/project` → Workspace + Projekte
- `/home/coder/.platformio` → Toolchains, Dependencies

---

## Installation & Setup

### Schritt 1: Template in `.env` registrieren

Bearbeite `.env` und füge das vcoder Template hinzu:

```bash
# .env
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-02:latest;user-template-next:latest;user-template-dictionary:latest;user-template-vcoder:latest"
```

**Wichtig:** Nur hier definierte Templates werden von `bash install.sh` gebaut!

### Schritt 2: Metadaten in `templates.json` aktualisieren

Das Template ist bereits in `templates.json` registriert:

```json
{
  "type": "vcoder",
  "image": "user-template-vcoder:latest",
  "display_name": "💻 ESP8266 IDE",
  "description": "Web-IDE mit PlatformIO für ESP8266/Wemos Entwicklung"
}
```

### Schritt 3: Build & Deploy

```bash
# Alle Templates bauen (inkl. vcoder)
# Das buildiert automatisch user-template-vcoder/
bash install.sh

# Docker Compose neu starten
docker-compose up -d --build
```

**⚠️ Build-Zeit:** Der vcoder-Build kann 5-10 Minuten dauern (Extensions werden von GitHub geladen: ~60MB).

---

## Workspace Management

### Erste Verwendung

Wenn ein Benutzer das Template wählt:

1. Spawner erstellt Container mit `user-template-vcoder:latest`
2. Mountet zwei Volumes:
   - `/data/users/{user_id}/vcoder/workspace` → `/home/coder/project`
   - `/data/users/{user_id}/vcoder/platformio` → `/home/coder/.platformio`
3. code-server startet auf Port 8080
4. User erhält Zugang via `https://coder.domain.com/{user-slug}`
5. Workspace ist leer (Benutzer erstellt neue Projekte)

### PlatformIO Projekt erstellen

Im IDE:

1. **View** → **Command Palette** (Ctrl+Shift+P)
2. **PlatformIO: Create Project**
3. Wähle Board (ESP8266, Wemos D1 Mini, etc.)
4. Wähle Speicherort (z.B. `/home/coder/project/my-esp8266-project`)
5. PlatformIO initialiert `platformio.ini` + `src/main.cpp`

### Bestehendes Projekt importieren

```bash
# Wenn ein Git-Repo vorhanden ist:
cd /home/coder/project
git clone <repo-url>
cd <project-name>
# PlatformIO erkennt platformio.ini automatisch
```

---

## Build & Upload

### Build im Terminal

```bash
cd /home/coder/project/my-project
pio run -e <ENVIRONMENT>
```

**Verfügbare Environments (Beispiele):**
- `esp8266` - Generischer ESP8266
- `d1_mini` - Wemos D1 Mini
- `d1_mini_lite` - Wemos D1 Mini Lite

### Upload zur Hardware

```bash
# Lokale Verbindung (wenn Host über USB angebunden)
pio run -e d1_mini -t upload
```

**Hinweis:** Upload funktioniert nur wenn der Host USB-Zugriff hat. Für Remote-Uploading externe Tools nutzen.

### Serial Monitor

```bash
pio device monitor -e d1_mini
# CTRL+] zum Beenden
```

---

## Datapersistierung

### Docker Volumes

Zwei Volumes pro User:

1. **Workspace Volume:**
   - Host: `/data/users/{user_id}/vcoder/workspace`
   - Container: `/home/coder/project`
   - Enthält: Benutzer-Projekte, Code-Dateien

2. **PlatformIO Cache Volume:**
   - Host: `/data/users/{user_id}/vcoder/platformio`
   - Container: `/home/coder/.platformio`
   - Enthält: Toolchains (~200MB), Abhängigkeiten, Cache

### Automatische Konfiguration

Das Backend (`container_manager.py`) mountet Volumes automatisch:

```python
if container_type == 'vcoder':
    data_path = f"/data/users/{user_id}/vcoder"
    volumes = {
        f"{data_path}/workspace": {'bind': '/home/coder/project', 'mode': 'rw'},
        f"{data_path}/platformio": {'bind': '/home/coder/.platformio', 'mode': 'rw'},
    }
```

### Persistierungs-Verhalten

- ✅ Projekte bleiben nach Container-Neustart erhalten
- ✅ Toolchains werden nicht erneut heruntergeladen (Cache)
- ✅ Extensions bleiben erhalten
- ✅ VS Code Settings bleiben erhalten

### Manuelles Testen

```bash
# Container starten
docker run -v /data/users/123/vcoder/workspace:/home/coder/project \
           -v /data/users/123/vcoder/platformio:/home/coder/.platformio \
           -p 8080:8080 user-template-vcoder:latest

# Dateistruktur prüfen
ls -la /data/users/123/vcoder/workspace/
ls -la /data/users/123/vcoder/platformio/

# Container stoppen und neustart
docker stop <container-id>
docker start <container-id>

# Daten sollten noch da sein!
```

---

## Sicherheit

### JWT-Cookie Validierung

Das vcoder-Template ist **geschützt durch Spawner JWT-Token**:

1. **HttpOnly Cookie `spawner_token`** wird vom Spawner gesetzt
2. **Traefik** validiert den Cookie vor Request-Weiterleitung
3. **code-server läuft mit `--auth=none`** (Vertrauen auf Traefik-Auth)

### How It Works

```
User Login → Spawner JWT-Cookie
   ↓
Browser sendet Cookie bei jedem Request
   ↓
Traefik validiert Cookie
   ↓
Gültig? → code-server erhält Request
Ungültig? → 403 Forbidden (Traefik-Level)
```

### Sicherheits-Features

- ✅ **HttpOnly Cookies** - JavaScript kann Token nicht auslesen
- ✅ **Secure Flag** - Nur über HTTPS übertragen
- ✅ **SameSite=Lax** - CSRF-Schutz
- ✅ **Token Expiration** - Standard: 1 Stunde (konfigurierbar)
- ✅ **code-server `--auth=none`** - Vertraut auf Traefik-Layer

### Isolation

- ✅ Jeder User hat eigenen Container
- ✅ Workspace-Volumes sind pro User isoliert
- ✅ Keine Zugriff auf Docker Socket
- ✅ Resource Limits (CPU/RAM) via `container_manager.py`

---

## Ports & Networking

### Port-Nutzung

| Port | Service | Beschreibung |
|------|---------|--------------|
| 8080 | code-server | Web IDE |
| 8008 | PIO Home Proxy | Über socat-Tunnel |
| 9009 | PIO Home (intern) | Von PlatformIO |

### socat Tunnel

Das Entrypoint-Script startet einen socat-Tunnel:

```bash
socat TCP-LISTEN:8008,reuseaddr,fork TCP:localhost:9009 &
```

Dies ermöglicht PlatformIO Home auf Port 8008 zu erreichbar (intern läuft es auf 9009).

### Traefik Integration

Spawner konfiguriert automatisch:
- **Host:** `coder.domain.com`
- **PathPrefix:** `/{user-slug}-vcoder`
- **StripPrefix Middleware:** Entfernt Prefix bevor Request zum Container
- **Port:** 8080

---

## Performance & Ressourcen

### Empfehlungen

- **RAM:** 512 MB minimum (Default aus `.env`)
- **CPU:** 0.5 CPU minimum (Default aus `.env`)
- **Workspace Size:** < 1 GB empfohlen für schnelle Sync
- **PlatformIO Cache:** ~200 MB (einmalig beim ersten Build)

### Resource Limits

In `.env` konfigurierbar:

```bash
DEFAULT_MEMORY_LIMIT=512m      # RAM pro Container
DEFAULT_CPU_QUOTA=50000        # 0.5 CPU = 50000 micro-cpu units
```

### Skalierung für größere Projekte

Wenn Projekte wachsen:

```bash
# .env anpassen
DEFAULT_MEMORY_LIMIT=1024m     # 1 GB
DEFAULT_CPU_QUOTA=100000       # 1 CPU full
```

---

## Monitoring & Debugging

### Logs anschauen

```bash
# Live Logs des Containers
docker logs -f user-<slug>-vcoder-<user_id>

# Beispiel Log Output:
# [SPAWNER] Creating vcoder container...
# [SPAWNER] Volumes für vcoder:
# [SPAWNER]   /data/users/123/vcoder/workspace -> /home/coder/project
# [SPAWNER]   /data/users/123/vcoder/platformio -> /home/coder/.platformio
```

### IDE Access prüfen

```bash
# Teste Erreichbarkeit
curl -k https://coder.domain.com/user-slug-vcoder/

# Sollte HTML von code-server zurückgeben
```

### Workspace-Status

```bash
# Im Container prüfen
docker exec <container-id> ls -la /home/coder/project/

# Projekte auflisten
docker exec <container-id> find /home/coder/project -name "platformio.ini"
```

### PlatformIO Status

```bash
# Boards auflisten
docker exec <container-id> pio boards | head -20

# Installed Platforms
docker exec <container-id> pio platform list

# Cache-Status
docker exec <container-id> du -sh /home/coder/.platformio/
```

---

## Troubleshooting

### Problem: "IDE lädt nicht / 503 Fehler"

```
Mögliche Ursachen:
1. Container startet nicht
2. Port 8080 wird nicht exponiert
3. Traefik erkennt Container nicht
4. Extensions werden noch heruntergeladen

Lösung:
docker logs user-<slug>-vcoder-<id>
docker inspect user-<slug>-vcoder-<id> | grep State

Wenn Extensions installiert werden:
Warte 2-3 Minuten für erste IDE-Erreichbarkeit
```

### Problem: "Workspace ist leer nach Neustart"

```
Mögliche Ursachen:
1. Volume nicht korrekt gemountet
2. Pfad-Berechtigungen falsch

Lösung:
docker inspect <container-id> | grep -A10 Mounts

Sollte zeigen:
"Mounts": [
  {
    "Type": "bind",
    "Source": "/data/users/123/vcoder/workspace",
    "Destination": "/home/coder/project"
  }
]
```

### Problem: "PlatformIO Build fehlgeschlagen"

```
Häufige Fehler:
1. Toolchain nicht heruntergeladen
2. platformio.ini Fehler
3. Missing Dependencies

Lösung im Terminal:
pio run -e d1_mini -v  # Verbose output
pio platform install espressif8266
pio lib list
```

### Problem: "Code Completion funktioniert nicht"

```
Ursache: cpptools/clangd-Extension wird noch heruntergeladen

Lösung:
1. IDE neuladen (F5)
2. View → Extensions - cpptools sollte installiert sein
3. Falls nicht: Command Palette → Install Extension "ms-vscode.cpptools"
4. Warte bis Symbol "[Installing]" weg ist
```

### Problem: "Build dauert sehr lange beim ersten Mal"

```
Das ist normal! Beim ersten Build:
1. Toolchains werden heruntergeladen (~50-200 MB je nach Board)
2. Dependencies werden kompiliert
3. Cache wird aufgebaut

Nächste Builds sind viel schneller (Cache wird reused).

Symptom:
- Erste Build: 2-5 Minuten
- Nächste Builds: 10-30 Sekunden
```

---

## Entwicklungs-Workflow

### Neue Projekte

```
1. IDE öffnen (https://coder.domain.com/...)
2. Terminal: Command Palette → PlatformIO: Create Project
3. Board auswählen (z.B. "Wemos D1 Mini")
4. Speicherpfad: /home/coder/project/mein-projekt
5. platformio.ini + src/main.cpp werden generiert
6. Beginne mit Code-Schreiben!
```

### Bestehendes Projekt klonen

```
1. IDE öffnen
2. Terminal öffnen (View → Terminal)
3. cd /home/coder/project
4. git clone <repo-url>
5. cd <project-name>
6. pio run -e d1_mini  # Test Build
```

### Debugging

```
1. In src/main.cpp Breakpoint setzen
2. Run → Start Debugging (F5)
3. Verbindung zum Board muss vorhanden sein (Hardware-Debugger)
4. Breakpoints sollten pausieren
```

---

## Integration mit Spawner

### Automatischer Container-Spawn

Wenn ein Benutzer das vcoder-Template wählt:

1. Spawner erstellt Container mit `user-template-vcoder:latest`
2. Mountet Volumes für Workspace + PlatformIO Cache
3. Traefik routet Request zu Container unter `https://coder.domain.com/{user-slug}-vcoder`
4. Benutzer sieht code-server IDE
5. Workspace + Cache bleiben erhalten nach Neustart!

### Admin-Dashboard Integration

Im Admin-Dashboard können Admins:
- ✅ Container starten/stoppen
- ✅ Container löschen (auch Workspace!)
- ✅ Logs ansehen
- ✅ Container-Status prüfen

---

## Wartung & Updates

### Backup des Workspaces

```bash
# Einzelnen User-Backup
tar -czf backup-vcoder-user-123.tar.gz /data/users/123/vcoder/

# Alle vcoder Workspaces
tar -czf backup-all-vcoder.tar.gz /data/users/*/vcoder/
```

### Cleanup (Cache leeren)

```bash
# Toolchains löschen (wird beim nächsten Build neu heruntergeladen)
docker exec <container-id> rm -rf /home/coder/.platformio/packages/

# Kompletter Cache-Reset
docker exec <container-id> pio system prune --force
```

### Updates für PlatformIO

Das Template ist mit festen Versionen konfiguriert:
- cpptools: 1.29.0
- platformio-ide: 3.3.4

Zum Update von Versionen:

```dockerfile
# In user-template-vcoder/Dockerfile ändern:
ARG CPDTOOLS_VER=1.30.0  # Neue Version
ARG PIO_VER=3.4.0        # Neue Version

# Dann rebuild:
bash install.sh
docker-compose up -d --build
```

---

## Weitere Verbesserungen (Optional)

### Mögliche Features für Zukunft

1. **Project Templates** - Vorlagen für verschiedene Board-Typen
2. **Library Management UI** - GUI für Abhängigkeiten
3. **Serial Monitor Integration** - Im IDE integriert
4. **Remote Upload** - Upload-Gateway für Remote-Hardware
5. **Device Manager** - Konfiguration von angebundenen Boards
6. **Firmware Comparison** - Diff-Tool für Firmware-Versionen
7. **Dokumentation Browser** - Offline Arduino/ESP8266 Docs

---

## Datenschutz & DSGVO

- ✅ Workspace-Dateien werden lokal in Containern gespeichert
- ✅ Keine Daten an Dritte übertragen
- ✅ Benutzer hat vollständige Kontrolle
- ✅ Einfaches Löschen möglich (Container + Volumes löschen)
- ✅ Extensions werden lokal im Container gecacht (kein Telemetrie)

---

## Support & Issues

Bei Problemen:

1. **Logs prüfen:** `docker logs container-id`
2. **IDE Erreichbarkeit:** Browser auf `https://coder.domain.com/...`
3. **Workspace:** `docker exec container-id ls -la /home/coder/project`
4. **PlatformIO:** `docker exec container-id pio --version`
5. **Build Fehler:** Terminal in IDE nutzen für detailliertes Output

---

## Version & Changelog

**Version:** 1.0.0 (2026-03-19)

### Features
- ✅ code-server Web IDE mit Syntax Highlighting
- ✅ PlatformIO IDE Extension für Embedded Development
- ✅ C/C++ IntelliSense (cpptools + clangd)
- ✅ Workspace Persistierung (Docker Volumes)
- ✅ PlatformIO Toolchain Caching
- ✅ socat Port-Tunneling für PIO Home
- ✅ Spawner JWT Integration (--auth=none)

---

## Lizenz & Attribution

**Template:** Container Spawner / vcoder Integration
**Basiert auf:** codercom/code-server + PlatformIO
**Autor:** Rainer Wieland
**Lizenz:** MIT oder ähnlich

---

## Letzte Aktualisierung

- **Datum:** 2026-03-19
- **Version:** 1.0.0
- **Status:** Production Ready ✅
