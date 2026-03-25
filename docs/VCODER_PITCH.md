# 💻 vcoder: Cloud IDE für Maker & Embedded Developers

## 🎯 Vision

**Stell dir vor:** Jeder Maker bekommt seine eigene **Cloud-IDE für ESP8266-Entwicklung** – persistenter Workspace, PlatformIO vorinstalliert, direkt im Browser, geschützt durch JWT.

Keine lokale Installation. Keine Komplikationen. Einfach Login und coden.

---

## 🏗️ Architektur: Das Spawner Ökosystem

### Was ist Container Spawner?

Ein **Production-Stack** für persönliche Developer-Umgebungen:

```
┌─────────────────────────────────────────────────────────┐
│                    Browser / Nutzer                      │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────────┐
         │   Traefik Reverse    │
         │      Proxy (SSL)     │
         └──────────┬───────────┘
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │ user1  │ │ user2  │ │ user3  │
    │ IDE    │ │ Docs   │ │ Chat   │  ← Isolierte Container
    │ vcoder │ │ Wiki   │ │ API    │     pro User
    └────────┘ └────────┘ └────────┘
         │          │          │
         └──────────┼──────────┘
                    ▼
      ┌─────────────────────────┐
      │  Docker Volumes (Daten) │
      │  /data/users/{id}/      │
      └─────────────────────────┘
```

**Kernfeatures:**
- ✅ **Passwordless Auth**: Magic Links per Email (keine Passwörter!)
- ✅ **Multi-Template System**: Templates sind einfach Docker Images
- ✅ **Persistent Data**: User-Daten bleiben über Container-Restarts erhalten
- ✅ **JWT Security**: HttpOnly Cookies, CSRF-Schutz
- ✅ **Skalierbar**: Jeden User in eigenem Container isolieren

### Die Template-Architektur

Ein **Template** = ein Docker Image mit einer speziellen Applikation:

| Template | Beschreibung | Status |
|----------|------------|--------|
| `template-01` | Nginx Basic | ✅ Stable |
| `template-next` | Next.js React App | ✅ Stable |
| `dictionary` | Persönliches Wörterbuch (Flask) | ✅ Working |
| **`vcoder`** | **ESP8266 IDE (code-server + PlatformIO)** | 🟡 Beta |

Jeder User **wählt sein Template im Dashboard** → Spawner startet automatisch einen isolierten Container → User erhält eigene URL: `https://spawner.domain.com/<slug>-<template>`

---

## 🚀 Was ist vcoder?

### Features

**code-server** (VS Code im Browser):
- 💬 Full IntelliSense & Code-Completion
- 🎨 Syntax Highlighting für alle Sprachen
- 📦 Extension-Marketplace (OpenVSX)
- 🔌 Terminal integriert
- 💾 File Explorer & Git Integration
- 🌙 Dark Mode

**PlatformIO** (Embedded Development IDE):
- 🎯 One-Click Project Creation (wähle Board → Template generiert)
- 🔨 Build & Compile für ESP8266, Wemos, Arduino, STM32, etc.
- ⬆️ Upload-Tool (USB via Host, oder Remote-API)
- 📊 Serial Monitor für Debugging
- 📚 Intellisense für 100+ Boards/Plattformen
- 🛠️ Package Manager (automatisches Herunterladen von Toolchains)

**Persistenz:**
- 💾 **Workspace Volume**: `/home/coder/project/` bleibt nach Restart erhalten
- 📦 **Toolchain Cache**: `/home/coder/.platformio/` (200MB) wird nicht jedes Mal neu heruntergeladen

**Security:**
- 🔐 **Spawner JWT-Cookie**: Automatische Authentifizierung (kein separates Login für IDE)
- 🛡️ **Unprivileged User**: code-server läuft als `coder`, nicht root
- 🚫 **Isolated Container**: Kein Zugriff auf Docker Socket oder Host

---

## ✅ Was ist bereits fertig?

- ✅ **Dockerfile** basiert auf `codercom/code-server:latest` + PlatformIO
  - cpptools (Microsoft C/C++) heruntergeladen & installiert
  - platformio-ide Extension installiert
  - clangd für Language-Server Protocol

- ✅ **Spawner Integration**
  - Template in `templates.json` registriert
  - Volumes für Workspace + PlatformIO Cache konfiguriert
  - Container-Spawn mit JWT automatisiert
  - Dashboard zeigt "💻 ESP8266 IDE" Template

- ✅ **Traefik Routing**
  - `https://spawner.domain.com/<slug>-vcoder` → Container automatisch geroutet
  - StripPrefix Middleware entfernt `/<slug>-vcoder` bevor Request zum Container

- ✅ **Dokumentation**
  - Vollständiges Setup & Deployment Guide
  - REST API Specs wenn nötig
  - Troubleshooting-Kapitel

---

## 🔴 Offene Baustellen (Die Challenges)

### 1. **Subpath-Problem: Code-Server Asset Loading (KRITISCH)**

**Problem:**
```
GET /e220dd278a12-template-vcoder (200 OK - HTML)
  ├─ GET /stable-a6d80dc434b8774c92d0c7b548a24a35b8ac4a45/static/out/workbench.css (404 NOT FOUND) ❌
  ├─ GET /stable-a6d80dc434b8774c92d0c7b548a24a35b8ac4a45/static/out/nls.messages.js (404 NOT FOUND) ❌
  └─ GET /manifest.json (404 NOT FOUND) ❌
```

**Root Cause:**
- Traefik StripPrefix entfernt `/<slug>-vcoder` aus dem Request Path
- code-server erwartet aber, dass Assets unter `/<prefix>/` liegen (relative URLs)
- Stattdessen lädt code-server `/stable.../static/...` von der Root

**Lösungsansätze:**
1. **nginx Reverse Proxy im Container** (current attempt):
   - nginx auf Port 8080 (public)
   - code-server auf Port 8081 (internal)
   - nginx proxy-passiert alles zu code-server
   - Problem: Permission-Fehler (unprivileged user kann `/var/log/nginx/` nicht schreiben)

2. **code-server Configuration (ideal):**
   - `code-server` hat `--base-path` Flag? (Nein, unterstützt nicht in v4.111.0)
   - Custom Proxy-Headers in Traefik? (Komplex)

3. **Traefik Middleware (hacky):**
   - RewritePathRegex Middleware URLs umschreiben?
   - Plugin für Path-Injection?

**Status:** 🔴 **BLOCKIERT** - Subpath-Routing funktioniert nicht

---

### 2. **nginx Permissions: Unprivileged User (TECHNIK)**

**Problem:**
```bash
[emerg] 8#8: "daemon" directive is duplicate in /etc/nginx/nginx.conf:1
[emerg] 8#8: open() "/var/log/nginx/error.log" failed (13: Permission denied)
```

**Root Cause:**
- code-server läuft als `coder` User (unprivileged, sicherer)
- nginx Default-Config braucht root-Privilegien oder `/var/log/nginx/` Schreibrecht
- `/var/log/nginx/` hat Permissions `755` (nur root kann schreiben)

**Lösungsansätze:**
1. **Logs nach `/tmp` umleiten:**
   ```nginx
   error_log /tmp/nginx-error.log;
   access_log /tmp/nginx-access.log;
   daemon off;  # Nicht doppelt definieren!
   ```

2. **Minimal nginx Config schreiben** (kein root-User-Direktive)
3. **Alpine Linux nutzen** (kleineres Footprint)
4. **supervisord statt nginx** (optional, weniger Dependencies)

**Status:** 🟡 **IN PROGRESS** - Technical fix nötig

---

### 3. **JWT-Cookie Authentifizierung (SICHERHEIT)**

**Problem:**
- Dictionary-Template validiert JWT im `before_request` Hook
- vcoder braucht gleiches Verhalten (falls API-Endpoints hinzukommen)
- Aktuell: Cookie wird **nicht automatisch** vom Container validiert

**Lösungsansatz:**
- code-server exponiert keine API (ist pure WebUI)
- WebSocket-Connection (`wss://`) braucht evtl. Cookie-Validierung auf Proxy-Ebene
- Traefik-Middleware kann Cookie prüfen, bevor Request zum Container kommt

**Status:** 🟡 **OPTIONAL** - Nur wichtig wenn APIs später hinzukommen

---

### 4. **PlatformIO Home Proxy (UNTESTED)**

**Problem:**
- PlatformIO startet intern einen "Home" Server auf Port 9009
- Sollte über nginx zu Port 8008 tunnelt werden (socat)
- Noch nicht getestet ob das funktioniert

**Lösungsansatz:**
```bash
socat TCP-LISTEN:8008,reuseaddr,fork TCP:localhost:9009 &
```

**Status:** 🟡 **UNGETESTET** - Braucht Test auf echtem System

---

## 📋 Konkrete Aufgaben für Entwickler

### Task 1: Fix nginx Permissions (⏱️ ~2h, 🟡 Mittel)

**Was tun:**
1. `user-template-vcoder/Dockerfile` updaten
2. nginx Config schreiben ohne `daemon` Duplizierung
3. Logs zu `/tmp` umleiten
4. Build testen: `docker build -t user-template-vcoder:latest ./user-template-vcoder/`
5. Logs prüfen: `docker logs <container>` sollte **kein emerg Error** mehr zeigen

**Dateien:**
- `user-template-vcoder/Dockerfile` (Zeilen 62-77)

**Acceptance Criteria:**
- ✅ nginx startet ohne Permission-Fehler
- ✅ `docker logs <container>` zeigt "code-server listening on http://127.0.0.1:8081"

---

### Task 2: Löse code-server Asset-Loading Problem (⏱️ ~4h, 🔴 Schwer)

**Was tun:**
1. Verstehe warum code-server Assets von `/stable.../` lädt (schaue HTML)
2. Prüfe ob nginx Reverse Proxy jetzt funktioniert (nach Task 1)
3. Falls nicht: Implementiere alternative Lösung (z.B. Traefik Middleware)
4. Test im Browser: `https://spawner.domain.com/<slug>-vcoder/` sollte **vollständig geladen** sein

**Dateien:**
- `user-template-vcoder/Dockerfile` (nginx Config)
- Optional: `container_manager.py` (Traefik Labels)

**Acceptance Criteria:**
- ✅ IDE lädt komplett (keine 404-Fehler in Network-Tab)
- ✅ CSS & JavaScript ist vorhanden (IDE sieht nicht weiß aus)
- ✅ Code-Completion funktioniert

---

### Task 3: JWT-Cookie & Dictionary-Style Auth (⏱️ ~2h, 🟡 Leicht)

**Was tun:**
1. Schaue wie `user-template-dictionary/app.py` JWT validiert
2. Implementiere ähnliche Validierung im vcoder Container (falls API nötig wird)
3. Teste mit curl: `curl -b "spawner_token=..." https://spawner.domain.com/<slug>-vcoder/api/...`

**Dateien:**
- `user-template-dictionary/app.py` (Zeilen 63-103, JWT-Validierung)

**Acceptance Criteria:**
- ✅ Ohne gültigen Token: 401 Unauthorized
- ✅ Mit gültigem Token: API-Zugriff funktioniert

---

### Task 4: PlatformIO Home Proxy testen (⏱️ ~1h, 🟡 Leicht)

**Was tun:**
1. IDE starten (Task 2 muss funktionieren)
2. PlatformIO IDE Extension öffnen
3. PlatformIO Home sollte auf Port 8008 erreichbar sein (über socat Tunnel)
4. Test: Neue PlatformIO Project erstellen über UI

**Dateien:**
- `user-template-vcoder/Dockerfile` (Zeilen 80-83, Entrypoint)

**Acceptance Criteria:**
- ✅ PlatformIO Home lädt ohne Fehler
- ✅ "Create Project" Button funktioniert
- ✅ Board-Auswahl lädt korrekt

---

### Task 5: ESP8266 Test-Projekt Dokumentieren (⏱️ ~1h, 🟡 Leicht)

**Was tun:**
1. IDE starten & neues PlatformIO Projekt für "Wemos D1 Mini" erstellen
2. Hello-World Firmware schreiben (Serial Output)
3. Dokumentation schreiben: `docs/examples/VCODER_HELLOWORLD.md`
4. Schritt-für-Schritt Guide (Setup → Build → Upload)

**Dateien:**
- `docs/examples/VCODER_HELLOWORLD.md` (neu)

**Acceptance Criteria:**
- ✅ Guide ist reproduzierbar von zero
- ✅ Code-Beispiel enthalten
- ✅ Troubleshooting Section

---

## 🛠️ Tech Stack & Einstieg

### Tech Stack
```
Frontend Layer:       Traefik (Reverse Proxy, SSL)
                      ↓
Web Server:           nginx (in vcoder Container)
                      ↓
App Server:           code-server (VS Code)
                      ↓
IDE Extensions:       PlatformIO IDE, cpptools, clangd
                      ↓
Toolchain:            PlatformIO (ESP8266 SDK, esptool, etc.)
                      ↓
Persistenz:           Docker Volumes (/data/users/{id}/vcoder)

Orchestration:        Docker + docker-compose
CI/CD:                GitHub/Gitea + git
Lang:                 Python (Spawner), JavaScript (code-server), C++ (Firmware)
```

### Schnelleinstieg

**1. Repo klonen:**
```bash
git clone https://gitea.iotxs.de/RainerWieland/spawner.git
cd spawner
```

**2. Lokal bauen & testen:**
```bash
docker build -t user-template-vcoder:latest ./user-template-vcoder/
docker run --rm -p 8080:8080 user-template-vcoder:latest &
curl http://localhost:8080/  # Sollte HTML zurückgeben
```

**3. Wichtigste Dateien:**
- `user-template-vcoder/Dockerfile` - Container Definition
- `container_manager.py` - Spawner Integration (Volumes, Traefik Labels)
- `docs/templates/VCODER_TEMPLATE.md` - Vollständige Doku

**4. Slack/Discord Channel:**
- Link zum Team-Chat (falls vorhanden)
- Fragen? → Hier anschreiben!

---

## 💡 Warum mitmachen?

### Für dein Portfolio
- 🚀 **Production Stack**: Nicht nur Tutorial-Code, sondern **echte Nutzer** auf Synology NAS
- 📚 **Modern Tech**: Docker, Traefik, code-server, PlatformIO, JWT, Next.js
- 🎓 **Full-Stack**: Backend (Python), Frontend (React), Infrastructure (Docker)
- 🌍 **Open Source Feel**: Clean Code, Git-based Workflow, Dokumentation

### Für die Community
- 👥 **Maker-Community profitiert direkt** von der IDE
- 🎉 **Educational Value**: Perfect für Workshops & Teaching
- 🚀 **Low Barrier to Entry**: Keine lokale Installation, nur Browser
- 💾 **Persistent Data**: Deine Projekte bleiben dir erhalten

### Für die Technologie
- 🔧 **Container Orchestration**: Hands-on mit Docker & Traefik
- 🔐 **Security**: JWT, CORS, Unprivileged Users, Isolation
- ⚡ **Performance**: WebSocket Proxying, Asset Caching, Subpath Routing
- 📊 **Scalability**: Spawn unbegrenzt viele User-Container

---

## 📞 Kontakt & Support

**Repo:** https://gitea.iotxs.de/RainerWieland/spawner

**Doku:**
- Installation: `docs/install/DEPLOYMENT_GUIDE.md`
- vcoder Spezifisch: `docs/templates/VCODER_TEMPLATE.md`
- Architektur: `docs/architecture/` (falls vorhanden)

**Issues & PRs:**
- Nutze GitHub Issues für Bugs
- PRs für neue Features (bitte vorher absprechen!)
- Commit-Messages: Deutsch oder Englisch (egal, aber consistent)

**Fragen?**
- Kontaktiere: @RainerWieland (GitHub/Gitea)
- Oder: Schreib eine Issue mit Label `question`

---

## 🎯 Nächste Schritte

1. **Schnelleinstieg:** Task 1 beginnen (nginx Permissions)
2. **Dann:** Task 2 (Asset Loading) - das ist die Hauptchallenge
3. **Testing:** Task 4 (PlatformIO Home)
4. **Dokumentation:** Task 5 (Hello World)

**Timeline:** 2-3 Tage für alles (mit regulärem Job machbar)

Viel Spaß! 🚀

---

## Version & Changelog

**Pitch Version:** 1.0.0 (2026-03-19)
**vcoder Template Version:** 0.1.0-beta
**Status:** 🟡 Beta - Bereit für Community Contributions

---

**Made with ❤️ for Makers & Embedded Developers**
