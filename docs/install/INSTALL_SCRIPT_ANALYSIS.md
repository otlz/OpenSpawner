# Install.sh - Umfassende Dokumentation

**Datei:** `install.sh` (695 Zeilen)
**Zweck:** Vollautomatische Installation und Konfiguration des Container Spawner Systems
**Kompatibilität:** Bash, BusyBox (Synology NAS), Docker ≥ 20.10, Docker Compose ≥ 2.0

---

## Übersicht der Phasen

Das Script läuft **11 sequenzielle Phasen** durch:

1. **Startup & Konfiguration** - Logging, Farben, Mindestversionen definieren
2. **.env Prüfung** - Konfigurationsdatei vorhanden?
3. **Voraussetzungen prüfen** - Docker, Compose, Git Versionen validieren
4. **Update vs. Neuinstallation** - Git Repository klonen oder aktualisieren
5. **Verzeichnisse & Rechte** - data/, logs/ erstellen, Berechtigungen setzen
6. **Docker-Netzwerk** - Traefik-Netzwerk erstellen/prüfen
7. **Traefik Prüfung** - Ist Traefik-Container laufend?
8. **Docker Images bauen** - User-Templates und Spawner-Images kompilieren
9. **Container starten** - Docker Compose up, Health-Checks
10. **Fertig-Nachricht** - URLs anzeigen, nützliche Befehle listen

---

## Phase 1: Startup & Konfiguration (Zeilen 1-25)

### Zweck
Initialisierung des Scripts, Definition globaler Variablen und Logging-Setup.

### Zeilen 1-2: Shebang & Error Handling
```bash
#!/bin/bash
set -e
```
- `#!/bin/bash` - Bash-Interpreter aufrufen (nicht sh/dash/ash)
- `set -e` - **KRITISCH**: Beende Script sofort bei erstem Fehler (exit code ≠ 0)
- Verhindert, dass fehlerhafte Befehle ignoriert werden und weitere Schritte ausgeführt werden

### Zeilen 4-13: Repositoriums- & Installationsvariablen
```bash
REPO_URL="https://gitea.iotxs.de/RainerWieland/spawner.git"
RAW_URL="https://gitea.iotxs.de/RainerWieland/spawner/raw/branch/main"
INSTALL_DIR="${PWD}"
VERSION="0.1.0"
LOG_FILE="${INSTALL_DIR}/spawner-install.log"
```
- `REPO_URL` - Git Repository für klonen/pull (https, kein SSH)
- `RAW_URL` - Rohe Datei-Downloads (für .env.example)
- `INSTALL_DIR="${PWD}"` - **WICHTIG**: Installiert im aktuellen Verzeichnis (not hardcoded)
- `VERSION` - Script-Version (für Logs)
- `LOG_FILE` - Alle Build-Logs werden hier gesammelt

**Voraussetzungen:**
- Bash >= 4.0
- PWD muss beschreibbar sein (chmod 755 mindestens)

### Zeilen 15-20: Farben für Terminal-Output
```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
```
- ANSI Escape Codes für farbige Konsolen-Ausgabe
- Hilft bei Fehler/Success-Anzeige
- Kompatibel mit BusyBox (einfache Codes)

### Zeilen 22-24: Mindestversionen
```bash
MIN_DOCKER_VERSION="20.10"
MIN_COMPOSE_VERSION="2.0"
```
- Definieren Minimum-Versionen für Voraussetzungs-Check
- Docker < 20.10: Kein Docker Compose v2 Support
- Compose < 2.0: Alte `docker-compose` CLI (veraltet)

**Voraussetzungen:**
- Docker 20.10+ installiert
- Docker Compose 2.0+ installiert (integriert in Docker Desktop oder separat)

---

## Phase 2: Version-Vergleich Hilfsfunktion (Zeilen 30-72)

### Zweck
BusyBox-kompatible Versionierung (Synology NAS nutzt BusyBox, kein `sort -V` vorhanden).

### Zeilen 30-35: Funktions-Definition
```bash
version_gte() {
    local ver1="$1"
    local ver2="$2"
```
- `version_gte "20.10.21" "20.10"` → return 0 (true, >= erfüllt)
- `version_gte "20.0" "20.10"` → return 1 (false, < Minimum)
- **Warum**: `sort -V` existiert in BusyBox nicht

### Zeilen 40-50: Major/Minor/Patch Parsing
```bash
v1_major=$(echo "$ver1" | cut -d. -f1)
v1_minor=$(echo "$ver1" | cut -d. -f2)
v1_patch=$(echo "$ver1" | cut -d. -f3)
```
- Teile Version "20.10.21" auf:
  - v1_major=20, v1_minor=10, v1_patch=21
  - Verwende 0 als Default wenn Feld fehlt (`${v1_minor:-0}`)

### Zeilen 52-71: Vergleich Logic
1. **Major vergleichen** (Zeile 53-57)
   - Wenn v1_major > v2_major → return 0 (erfüllt)
   - Wenn v1_major < v2_major → return 1 (nicht erfüllt)
   - Wenn gleich → weiter zu Minor

2. **Minor vergleichen** (Zeile 60-63)
   - Analog Major-Vergleich

3. **Patch vergleichen** (Zeile 67-70)
   - `version_patch >= version_patch` → return 0

**Beispiele:**
- `version_gte "20.10.21" "20.10"` → 20==20, 10==10, 21>=0 → **TRUE**
- `version_gte "20.9.0" "20.10"` → 20==20, 9<10 → **FALSE**
- `version_gte "21.0" "20.10"` → 21>20 → **TRUE**

**Voraussetzungen:**
- cut, echo Commands vorhanden (in BusyBox)

---

## Phase 3: .env Datei Prüfung (Zeilen 74-115)

### Zweck
Prüfe ob .env existiert. Wenn nicht → Download .env.example und beende Script.

### Zeilen 74-82: Willkommens-Banner & Log-Init
```bash
echo "============================================================"
echo "  Container Spawner Installation v${VERSION}"
echo "============================================================"
```
- Zeige Script-Version an
- Initialisiere Log-Datei mit Timestamp

### Zeilen 87-100: .env Existenz-Check
```bash
if [ ! -f "${INSTALL_DIR}/.env" ]; then
    echo "Lade .env.example herunter..."
    if command -v curl >/dev/null 2>&1; then
        curl -sSL "${RAW_URL}/.env.example" -o "${INSTALL_DIR}/.env.example"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "${RAW_URL}/.env.example" -O "${INSTALL_DIR}/.env.example"
```

**Logik:**
- Existiert `.env` NICHT?
  1. Versuche `.env.example` herunterzuladen (über curl oder wget)
  2. Speichere in `${INSTALL_DIR}/.env.example`
  3. **Stoppe Script mit exit 0** → Zeige Anleitung zur manuellen Konfiguration

**Warum .env nicht automatisch kopieren?**
- `.env` enthält Secrets (SECRET_KEY, SMTP_PASSWORD etc.)
- Admin muss Werte bewusst setzen (BASE_DOMAIN, TRAEFIK_NETWORK etc.)
- Verhindert Sicherheitslücken durch Auto-Configuration

### Zeilen 104-111: Konfigurationsanleitung
```bash
echo "Naechste Schritte:"
echo "  1. Kopiere die Vorlage:  cp .env.example .env"
echo "  2. Passe die Werte an:   nano .env"
echo "  3. Fuehre erneut aus:    bash install.sh"
```

**Voraussetzungen:**
- curl ODER wget installiert
- Internet-Zugriff zu Gitea-Server
- `.env.example` im Repository vorhanden

---

## Phase 4: Voraussetzungen Prüfung (Zeilen 122-185)

### Zweck
Validiere dass alle erforderlichen Tools verfügbar und aktuelle Versionen sind.

### Zeilen 128-149: Docker Version Check
```bash
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}Fehler: Docker nicht gefunden!${NC}"
    exit 1
fi

DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || \
    docker version 2>/dev/null | grep -i "version" | head -1 | sed 's/.*version[: ]*\([0-9.]*\).*/\1/')
```

**Logic:**
1. Prüfe ob `docker` command existiert
   - `command -v` ist POSIX-kompatibel (funktioniert auch in BusyBox/ash)
2. Extrahiere Docker Server-Version:
   - Versuche `docker version --format` (moderne Syntax)
   - Fallback zu regex parsing (für ältere Docker Versionen)
3. Vergleiche gegen MIN_DOCKER_VERSION="20.10" mit `version_gte()` Funktion

**Fehlerbehandlung:**
```bash
if [ -z "$DOCKER_VERSION" ]; then
    echo "Version unbekannt (OK, mit Warnung fortfahren)"
elif version_gte "$DOCKER_VERSION" "$MIN_DOCKER_VERSION"; then
    echo "OK (v${DOCKER_VERSION})"
else
    echo "FEHLER: Version ${DOCKER_VERSION} zu alt"
    exit 1
fi
```

**Voraussetzungen:**
- `docker` executable vorhanden (PATH)
- Docker Server läuft (für version --format)

### Zeilen 151-178: Docker Compose Check
```bash
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"  # Neue Syntax (v2)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"  # Alte Syntax (v1)
else
    echo -e "${RED}Fehler: Docker Compose nicht gefunden!${NC}"
    exit 1
fi
```

**Logic:**
1. Prüfe ob `docker compose` vorhanden (Docker Desktop oder separate Installation)
2. Fallback zu `docker-compose` (veraltet aber noch unterstützt)
3. Speichere in `COMPOSE_CMD` Variable für später

**Wichtig:** `${COMPOSE_CMD}` wird später überall verwendet (Zeile 371, 626 etc.)

**Voraussetzungen:**
- Docker Compose v2+ oder `docker-compose` command vorhanden

### Zeilen 180-185: Git Check
```bash
if ! command -v git >/dev/null 2>&1; then
    echo -e "${RED}Fehler: Git nicht gefunden!${NC}"
    exit 1
fi
```

**Benötigt für:**
- Clone Repository bei Neuinstallation (Zeile 220)
- Pull Updates bei bestehender Installation (Zeile 209)
- Versionskontrolle

**Voraussetzungen:**
- `git` executable vorhanden (mindestens Git 2.0)

---

## Phase 5: Update vs. Neuinstallation (Zeilen 188-241)

### Zweck
Prüfe ob bereits Installation existiert. Wenn ja → update via git pull. Wenn nein → clone repository.

### Zeilen 192-193: Git Safe Directory (Synology-Workaround)
```bash
git config --global --add safe.directory "${INSTALL_DIR}" 2>/dev/null || true
```

**Warum?**
- Synology NAS: Docker Container läuft oft als root, Host-Verzeichnis ist root-owned
- Git misstraut Verzeichnissen mit unterschiedlichem Owner
- Fehler: `fatal: detected dubious ownership in repository at ...`
- Lösung: `safe.directory` erlaubt Repository trotzdem

**Syntax:**
- `2>/dev/null || true` - Ignoriere Fehler (akzeptabel wenn git zu alt)

### Zeilen 195-213: Update-Branch (Existierende Installation)
```bash
if [ -d "${INSTALL_DIR}/.git" ]; then
    echo "Update erkannt - hole neueste Aenderungen..."
    cd "${INSTALL_DIR}"

    # Sichere lokale Aenderungen
    if git diff --quiet 2>/dev/null; then
        : # Keine Aenderungen
    else
        git stash 2>/dev/null || true
    fi

    # Update durchfuehren
    if git fetch origin && git pull origin main 2>/dev/null; then
        echo "Repository aktualisiert"
    else
        echo "Git-Update fehlgeschlagen, fahre mit lokalen Dateien fort..."
    fi
```

**Logik:**
1. Existiert `.git` Verzeichnis? → Installation vorhanden
2. Prüfe auf lokale Änderungen mit `git diff --quiet`
3. Falls Änderungen → `git stash` (temporär speichern)
4. `git fetch` + `git pull origin main` (Update durchführen)
5. Falls fehlgeschlagen → Warnung aber nicht abbrechen (fahre mit lokalen Dateien fort)

**Warum stash?**
- User hat möglicherweise Dateien lokal angepasst (z.B. api.py Bugfixes)
- `git pull` würde MERGE CONFLICT verursachen
- `git stash` speichert lokale Änderungen sicher → Merge ist sauber

**Voraussetzungen:**
- `.git` Verzeichnis existiert (= Installation bereits vorhanden)
- `origin` Remote existiert (Standard bei clone)

### Zeilen 214-240: Clone-Branch (Neuinstallation)
```bash
else
    echo "Neuinstallation - klone Repository..."

    TEMP_DIR=$(mktemp -d)

    if git clone "${REPO_URL}" "${TEMP_DIR}"; then
        shopt -s dotglob 2>/dev/null || true
        for item in "${TEMP_DIR}"/*; do
            basename_item=$(basename "$item")
            if [ "$basename_item" != ".env" ] && [ "$basename_item" != ".git" ]; then
                cp -r "$item" "${INSTALL_DIR}/"
            fi
        done

        cp -r "${TEMP_DIR}/.git" "${INSTALL_DIR}/"
        rm -rf "${TEMP_DIR}"
```

**Logik:**
1. Keine `.git` Verzeichnis → Neuinstallation
2. Clone in **temporäres Verzeichnis** (nicht direkt nach INSTALL_DIR)
3. Kopiere Dateien (außer `.env` und `.git`)
4. Kopiere `.git` Verzeichnis nachträglich (für zukünftige Updates)
5. Räume Temp-Verzeichnis auf

**Warum nicht direkt klonen?**
- `git clone` würde `.env` überschreiben (wenn Admin bereits angepasst hat)
- Temporärer Clone als Workaround

**Voraussetzungen:**
- `git clone` funktioniert (Internet, SSH-Key oder HTTPS)
- mktemp Command vorhanden (POSIX-kompatibel)

---

## Phase 6: Verzeichnisse & Berechtigungen (Zeilen 244-285)

### Zweck
Erstelle erforderliche Verzeichnisse und setze Berechtigungen für Docker-Zugriff.

### Zeilen 249-255: Verzeichnisse erstellen
```bash
mkdir -p "${INSTALL_DIR}/data"
mkdir -p "${INSTALL_DIR}/logs"

chmod 755 "${INSTALL_DIR}/data"
chmod 755 "${INSTALL_DIR}/logs"
```

**Warum diese Verzeichnisse?**
- `data/` - Persistente Datenbank + Konfiguration
- `logs/` - Installations- und Anwendungs-Logs

**Berechtigungen (755 = rwxr-xr-x):**
- Owner: read + write + execute
- Group: read + execute (nur)
- Others: read + execute (nur)

**Kompatibilität:**
- Docker Container als root: 755 ausreichend
- Docker Container als non-root: Könnten 777 brauchen (kommentiert Zeile 271)

### Zeilen 262-274: Root-Check
```bash
if [ "$(id -u)" = "0" ]; then
    # Als root: 755 reicht
    echo "755 (root)"
else
    # Als normaler User: 755 auch OK
    echo "755"
fi
```

**Warum Root-Check?**
- Synology NAS: Installation oft als root
- Docker-Container: Läuft auch als root
- User-Scripts (z.B. cron): Könnten als normaler User laufen

**Regel:**
- Root + Docker-Root: 755 OK
- Normaler User + Docker-Root: 755 auch OK
- Normaler User + Docker-NonRoot: 777 nötig (siehe Kommentar)

### Zeilen 277-279: .env schützen
```bash
if [ -f "${INSTALL_DIR}/.env" ]; then
    chmod 600 "${INSTALL_DIR}/.env"
    echo ".env: OK (600, nur Owner)"
```

**Berechtigungen (600 = rw-------):**
- Nur Owner: read + write
- Group/Others: kein Zugriff

**WICHTIG:** Secrets in .env:
- `SECRET_KEY` - Flask Session Secret
- `SMTP_PASSWORD` - Email-Authentifizierung
- Darf nicht für alle lesbar sein!

### Zeilen 282-284: install.sh auführbar machen
```bash
if [ -f "${INSTALL_DIR}/install.sh" ]; then
    chmod +x "${INSTALL_DIR}/install.sh"
```

**Warum?**
- Nach git pull/clone könnte execute-bit verloren gehen
- Stelle sicher dass `bash install.sh` immer funktioniert

**Voraussetzungen:**
- chmod Command vorhanden (POSIX)
- Berechtigungen änderbar (nicht in read-only Filesystem)

---

## Phase 7: Docker-Netzwerk Prüfung (Zeilen 288-309)

### Zweck
Prüfe dass Traefik-Netzwerk existiert. Wenn nicht → Erstelle automatisch.

### Zeilen 291-292: Netzwerk aus .env lesen
```bash
NETWORK="${TRAEFIK_NETWORK:-web}"
echo "Pruefe Docker-Netzwerk: ${NETWORK}"
```

- Lese `TRAEFIK_NETWORK` Variable aus .env
- Fallback zu "web" wenn nicht definiert

### Zeilen 294-309: Netzwerk-Logik
```bash
if docker network inspect "${NETWORK}" >/dev/null 2>&1; then
    echo "Netzwerk '${NETWORK}': existiert"
else
    echo "Fehler: Docker-Netzwerk '${NETWORK}' existiert nicht!"

    # Automatische Erstellung (vorher: interaktive Frage)
    docker network create "${NETWORK}" 2>/dev/null || true
    echo "Netzwerk '${NETWORK}': erstellt/vorhanden"
fi
```

**Logik:**
1. Prüfe ob Netzwerk existiert mit `docker network inspect`
   - Erfolgreich → Netzwerk vorhanden, weitermachen
   - Fehler → Netzwerk nicht vorhanden

2. **Automatische Erstellung** (Zeile 307)
   - Erstelle Netzwerk: `docker network create "${NETWORK}"`
   - `2>/dev/null || true` - Ignoriere Fehler (z.B. bereits vorhanden)
   - Dadurch war das Script nicht mehr blockiert (früher: `read -p "...?"`)

**Warum dieses Netzwerk?**
- Traefik + Spawner müssen im **gleichen Netzwerk** sein
- Nur so können Traefik die User-Container entdecken und routen
- Name definiert in `.env` → `TRAEFIK_NETWORK=web` (oder custom)

**Voraussetzungen:**
- Docker Daemon läuft
- Benutzer hat docker Zugriff (sudo oder docker-Gruppe)
- Netzwerk nicht durch andere Tools belegt

---

## Phase 8: Traefik Prüfung (Zeilen 312-361)

### Zweck
Prüfe ob Traefik-Container läuft. Falls ja → Validiere dass es im richtigen Netzwerk ist.

### Zeilen 318-333: Traefik-Container Suche (3 Versuche)

**Versuch 1 (Zeile 318): Nach Name suchen**
```bash
TRAEFIK_CONTAINER=$(docker ps --filter "name=traefik" --filter "status=running" \
    --format "{{.Names}}" 2>/dev/null | head -1)
```
- Suche nach Container mit "traefik" im Namen
- `--filter "status=running"` - Nur laufende Container
- `--format "{{.Names}}"` - Nur Container-Name ausgeben
- `head -1` - Nimm ersten (falls mehrere)

**Versuch 2 (Zeile 322): Nach Image suchen**
```bash
if [ -z "$TRAEFIK_CONTAINER" ]; then
    TRAEFIK_CONTAINER=$(docker ps --filter "ancestor=traefik" \
        --filter "status=running" --format "{{.Names}}" 2>/dev/null | head -1)
fi
```
- Falls Name-Suche leer → Suche nach `ancestor=traefik` (Image-Name)
- Findungschance: Container könnte anders benannt sein, aber vom traefik Image stammen

**Versuch 3 (Zeile 327-332): Nach Label suchen**
```bash
if [ -z "$TRAEFIK_CONTAINER" ]; then
    TRAEFIK_CONTAINER=$(docker ps ... | while read name; do
        if docker inspect "$name" 2>/dev/null | grep -q '"traefik.http.routers\|com.docker.compose.service": "traefik"'; then
            echo "$name"
            break
        fi
    done)
fi
```
- Falls noch immer nicht gefunden → Prüfe Labels
- Traefik setzt typischerweise: `com.docker.compose.service=traefik`

### Zeilen 335-361: Traefik-Status Ausgabe

**Falls gefunden (Zeile 335-350):**
```bash
if [ -n "$TRAEFIK_CONTAINER" ]; then
    TRAEFIK_VERSION=$(docker exec "$TRAEFIK_CONTAINER" traefik version 2>/dev/null | ...)
    echo "Traefik: OK (Container: ${TRAEFIK_CONTAINER}, v${TRAEFIK_VERSION})"

    # Prüfe ob im richtigen Netzwerk
    TRAEFIK_NETWORKS=$(docker inspect "$TRAEFIK_CONTAINER" \
        --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}')
    if echo "$TRAEFIK_NETWORKS" | grep -q "$NETWORK"; then
        echo "Traefik-Netzwerk: OK (verbunden mit '${NETWORK}')"
    else
        echo "WARNUNG: Traefik nicht mit Netzwerk '${NETWORK}' verbunden"
        echo "Traefik-Netzwerke: ${TRAEFIK_NETWORKS}"
    fi
fi
```

**Checks:**
1. `traefik version` - Zeige Traefik-Version an
2. `docker inspect` - Prüfe Netzwerk-Verbindungen
3. Regex-Match gegen `${NETWORK}` - Sind Traefik und Spawner im gleichen Netzwerk?

**Falls nicht gefunden (Zeile 352-361):**
```bash
else
    echo "WARNUNG: Kein laufender Traefik-Container gefunden!"
    echo "Traefik wird fuer das Routing benoetigt, aber Script faehrt fort..."
```

- **WARNUNG nicht FEHLER** → Script bricht nicht ab
- Spawner funktioniert auch ohne Traefik:
  - Nur lokal erreichbar (localhost:5000)
  - Keine automatischen Subdomains
  - Keine User-Container Routing

**Voraussetzungen:**
- Docker Daemon läuft und antwortet
- Traefik-Container läuft (optional, mit Warnung weitergemacht)

---

## Phase 9: Docker Images Bauen (Zeilen 364-563)

### Zweck
Baue alle erforderlichen Docker Images:
1. **User-Templates** (template-01, template-02, template-next etc.)
2. **Spawner API** (Flask Backend)
3. **Spawner Frontend** (Next.js)

### Zeilen 370-378: USER_TEMPLATE_IMAGES aus .env auslesen
```bash
USER_TEMPLATE_IMAGES=""
if [ -f "${INSTALL_DIR}/.env" ]; then
    USER_TEMPLATE_IMAGES=$(grep "^USER_TEMPLATE_IMAGES=" "${INSTALL_DIR}/.env" | \
        cut -d'=' -f2- | tr -d '"' | tr -d "'")
fi
```

**Parse-Logic:**
1. `grep "^USER_TEMPLATE_IMAGES="` - Finde genau diese Zeile (nicht commented)
2. `cut -d'=' -f2-` - Alles nach dem `=` Zeichen
3. `tr -d '"' | tr -d "'"` - Entferne Quotes (USER_TEMPLATE_IMAGES="...;...;...")

**Beispiel:**
```bash
# In .env
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-02:latest;user-template-next:latest"

# Nach Parsing
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-02:latest;user-template-next:latest"
```

### Zeilen 380-385: Fallback auf .env.example
```bash
if [ -z "$USER_TEMPLATE_IMAGES" ] && [ -f "${INSTALL_DIR}/.env.example" ]; then
    echo "⚠️  USER_TEMPLATE_IMAGES nicht definiert"
    echo "  Nutze .env.example als Fallback..."
    USER_TEMPLATE_IMAGES=$(grep "^USER_TEMPLATE_IMAGES=" "${INSTALL_DIR}/.env.example" | ...)
fi
```

- Wenn `.env` USER_TEMPLATE_IMAGES nicht hat → Versuche `.env.example`
- Erlaubt Test-Installation ohne .env Anpassung

### Zeilen 387-437: Fallback-Modus (Keine .env Konfiguration)
```bash
if [ -z "$USER_TEMPLATE_IMAGES" ]; then
    echo "⚠️  USER_TEMPLATE_IMAGES nicht konfiguriert"
    echo "  Fallback: Baue alle user-template-* Verzeichnisse..."

    for template_dir in "${INSTALL_DIR}"/user-template*; do
        [ -d "$template_dir" ] || continue
        template_name=$(basename "$template_dir")
        image_name="${template_name}:latest"

        docker build --no-cache -t "${image_name}" "${template_dir}/" >> "${BUILD_LOG}" 2>&1
```

**Logik (Rückwärtskompatibilität):**
- Wenn USER_TEMPLATE_IMAGES leer → Auto-Detection
- Suche alle `user-template-*` Verzeichnisse
- Baue jedes als Docker Image

**Beispiel:**
```
user-template-01/
user-template-02/
user-template-next/

→ Baue: user-template-01:latest, user-template-02:latest, user-template-next:latest
```

**Warum Fallback?**
- Alte Installationen ohne .env Konfiguration müssen auch funktionieren
- Neue Installationen verwenden .env-basiertes System

### Zeilen 440-562: .env-basiertes Building (NEUE LOGIK)
```bash
else
    echo "  Baue Templates aus .env Konfiguration..."

    # Split by Semicolon
    IFS=';' read -ra TEMPLATE_IMAGES <<< "$USER_TEMPLATE_IMAGES"

    TOTAL_TEMPLATES=${#TEMPLATE_IMAGES[@]}

    for image_with_tag in "${TEMPLATE_IMAGES[@]}"; do
        image_with_tag=$(echo "$image_with_tag" | xargs)  # Trim whitespace
        [ -z "$image_with_tag" ] && continue

        # Extract directory name (vor dem :)
        template_dir_name="${image_with_tag%%:*}"

        # Extract tag (nach dem :)
        template_tag="${image_with_tag##*:}"
        [ -z "$template_tag" ] && template_tag="latest"

        template_dir="${INSTALL_DIR}/${template_dir_name}"
```

**Parse-Logik für "user-template-01:latest":**
1. Split Array by `;`
   - `"user-template-01:latest;user-template-02:latest"`
   - → `["user-template-01:latest", "user-template-02:latest"]`

2. Trim Whitespace mit `xargs`
   - `"  user-template-01:latest  "` → `"user-template-01:latest"`

3. Extrahiere Image-Name und Tag
   - `${image%%:*}` - Alles VOR dem ersten `:` (user-template-01)
   - `${image##*:}` - Alles NACH dem letzten `:` (latest)

**Validation (Zeilen 475-493):**
```bash
# Prüfe ob Verzeichnis existiert
if [ ! -d "$template_dir" ]; then
    echo "❌ Fehler: Template-Verzeichnis nicht gefunden"
    echo "  Definiert in .env: USER_TEMPLATE_IMAGES"
    echo "  Erwartetes Verzeichnis: ${template_dir}"
    continue  # Überspringe dieses Template
fi

# Dockerfile vorhanden?
if [ ! -f "${template_dir}/Dockerfile" ]; then
    echo "❌ Fehler: Kein Dockerfile gefunden"
    continue
fi
```

- Nicht-existente Verzeichnisse → WARNUNG + continue (nicht FEHLER)
- So können einzelne Templates fehlschlagen, andere funktionieren weiterhin

**Build-Logik (Zeilen 507-527):**
```bash
docker build --no-cache -t "${template_dir_name}:${template_tag}" "${template_dir}/" >> "${BUILD_LOG}" 2>&1
BUILD_EXIT=$?

# Zeige gefilterten Output
grep -E "(Step |#[0-9]+ |Successfully|ERROR|error:|COPY|RUN|FROM)" "${BUILD_LOG}" | sed 's/^/        /'

# Prüfe ob erfolgreich
if [ $BUILD_EXIT -eq 0 ] && docker image inspect "${template_dir_name}:${template_tag}" >/dev/null 2>&1; then
    echo "✅ ${template_name}: OK"
    BUILT_TEMPLATES=$((BUILT_TEMPLATES + 1))
else
    echo "❌ ${template_name}: FEHLER"
    tail -50 "${BUILD_LOG}"
    exit 1  # Breche ab
fi
```

**Build-Logik:**
1. Führe `docker build` aus, leite Output zu Log-Datei
2. Zeige gefilterte Build-Schritte (Step, FROM, RUN, COPY, ERROR)
3. Prüfe ob erfolgreich:
   - Exit-Code = 0?
   - `docker image inspect` findet das Image?
4. Beide Bedingungen erfüllt → OK
5. Sonst → FEHLER, zeige last 50 Zeilen, beende Script

**Spezieller Handling für Next.js (Zeile 497-498):**
```bash
if [[ "$template_dir_name" == *"next"* ]]; then
    echo "${BLUE}Dies kann 2-5 Minuten dauern (npm install + build)...${NC}"
fi
```

- Next.js Templates brauchen länger (npm install + npm run build)
- Warnung damit Admin nicht denkt Installation ist hänggeblieben

**Ungekonfigurierte Templates Warnung (Zeilen 539-561):**
```bash
echo "  Prüfe auf ungekonfigurierte Template-Verzeichnisse..."

for template_dir in "${INSTALL_DIR}"/user-template*; do
    template_name=$(basename "$template_dir")

    # Ist dieses Template in USER_TEMPLATE_IMAGES definiert?
    if [[ ! "$USER_TEMPLATE_IMAGES" =~ "$template_name" ]]; then
        echo "  ⚠️  ${template_name} (nicht in USER_TEMPLATE_IMAGES definiert)"
    fi
done
```

- Hilft Admin zu sehen, welche Templates **nicht** gebaut wurden
- Z.B. Template existiert lokal, aber nicht in .env → wird ignoriert

### Zeilen 565-616: Spawner API & Frontend bauen

**Spawner API (Flask Backend) - Zeilen 565-587:**
```bash
echo "  Baue Spawner API (Flask Backend)..."

docker build --no-cache -t spawner:latest "${INSTALL_DIR}/" >> "${BUILD_LOG}" 2>&1
BUILD_EXIT=$?

if [ $BUILD_EXIT -eq 0 ] && docker image inspect spawner:latest >/dev/null 2>&1; then
    echo "  spawner-api: ${GREEN}OK${NC}"
else
    echo "  spawner-api: ${RED}FEHLER${NC}"
    tail -50 "${BUILD_LOG}"
    exit 1
fi
```

- Baut Image aus Dockerfile im **root directory** (nicht frontend/)
- Image-Name: `spawner:latest`
- **Muss erfolgreich sein** (exit 1 bei Fehler)

**Spawner Frontend (Next.js) - Zeilen 590-616:**
```bash
if [ -d "${INSTALL_DIR}/frontend" ]; then
    echo "  Baue Frontend (Next.js)..."
    echo "${BLUE}Dies kann 2-5 Minuten dauern (npm install + build)...${NC}"

    docker build --no-cache -t spawner-frontend:latest "${INSTALL_DIR}/frontend/" >> "${BUILD_LOG}" 2>&1
    ...
fi
```

- **Optional Check**: Falls `frontend/` Verzeichnis nicht vorhanden → überspringe
- Image-Name: `spawner-frontend:latest`
- Warnung dass npm build lange dauert

**Voraussetzungen:**
- `docker build` Command funktioniert
- Ausreichend Disk-Space für Images
- Internetzugriff (für npm install, pip install etc.)
- Dockerfile(s) syntaktisch korrekt

---

## Phase 10: Container Starten (Zeilen 621-646)

### Zweck
Starte Docker Compose Services (Spawner API, Frontend, optional Traefik) und prüfe Health.

### Zeilen 625-626: Compose Up
```bash
echo ""
echo "Starte Container..."
${COMPOSE_CMD} up -d
```

- `${COMPOSE_CMD}` ist entweder `docker compose` oder `docker-compose` (aus Phase 4)
- `-d` Flag: Detached Mode (laufen im Hintergrund)

**Was wird gestartet?** (Definiert in docker-compose.yml)
- spawner (API, Port 5000)
- spawner-frontend (Next.js, Port 3000)
- Optional: traefik, database etc. (je nach Konfiguration)

### Zeilen 631-646: Health-Checks
```bash
echo "Warte auf Spawner-Start..."
sleep 5

SPAWNER_URL="http://localhost:${SPAWNER_PORT:-5000}/health"
if curl -sf "${SPAWNER_URL}" >/dev/null 2>&1; then
    echo "  API Health-Check:      ${GREEN}OK${NC}"
else
    echo "  API Health-Check:      ${YELLOW}Noch nicht bereit (normal beim ersten Start)${NC}"
fi

if curl -sf "http://localhost:3000/" >/dev/null 2>&1; then
    echo "  Frontend Health-Check: ${GREEN}OK${NC}"
else
    echo "  Frontend Health-Check: ${YELLOW}Noch nicht bereit${NC}"
fi
```

**Logik:**
1. Warte 5 Sekunden (Container brauchen Zeit zu starten)
2. Prüfe API: `curl -sf http://localhost:5000/health`
   - `-s` Silent mode
   - `-f` Fail silently auf HTTP-Error
3. Prüfe Frontend: `curl -sf http://localhost:3000/`

**Status:**
- Beide OK → ✅ Alles funktioniert
- Eine/beide nicht bereit → ⚠️ Normal beim ersten Start (DB wird initialisiert etc.)

**Voraussetzungen:**
- curl Command verfügbar
- Container haben Zeit zu starten
- Ports 5000 und 3000 lokal verfügbar

---

## Phase 11: Fertig-Nachricht (Zeilen 648-695)

### Zweck
Zeige Erfolgs-Nachricht und nützliche Informationen für Admin.

### Zeilen 652-656: Success Banner
```bash
echo "============================================================"
echo -e "  ${GREEN}Installation abgeschlossen!${NC}"
echo "============================================================"
echo ""
echo "Installations-Log: ${LOG_FILE}"
```

- Zeige Erfolgs-Banner
- Link zu Log-Datei (für Debugging)

### Zeilen 659-668: URLs anzeigen
```bash
SCHEME="https"
if [ "${BASE_DOMAIN:-localhost}" = "localhost" ]; then
    SCHEME="http"
fi
FULL_URL="${SCHEME}://${SPAWNER_SUBDOMAIN:-coder}.${BASE_DOMAIN:-localhost}"

echo "Zugriff:"
echo "  Frontend:    ${FULL_URL}"
echo "  API:         ${FULL_URL}/api"
echo "  Health:      ${FULL_URL}/health"
```

**Logic:**
- Lese `BASE_DOMAIN` und `SPAWNER_SUBDOMAIN` aus .env
- Falls localhost → nutze http:// (kein HTTPS)
- Sonst → nutze https:// (erwartet Let's Encrypt)

**Beispiel .env:**
```
BASE_DOMAIN=wieland.org
SPAWNER_SUBDOMAIN=coder
```

→ URLs:
- Frontend: https://coder.wieland.org
- API: https://coder.wieland.org/api
- Health: https://coder.wieland.org/health

### Zeilen 670-678: Lokale URLs & Befehle
```bash
echo ""
echo "Lokaler Zugriff (ohne Traefik):"
echo "  API:         http://localhost:${SPAWNER_PORT:-5000}"
echo "  Frontend:    http://localhost:3000"
echo ""
echo "Nützliche Befehle:"
echo "  Status:      ${COMPOSE_CMD} ps"
echo "  Logs API:    ${COMPOSE_CMD} logs -f spawner"
echo "  Logs FE:     ${COMPOSE_CMD} logs -f frontend"
```

- Zeige wie man Services ohne Traefik zugreift
- Zeige häufige Wartungs-Befehle

### Zeilen 681-695: Wichtige Informationen
```bash
echo "WICHTIG - Multi-Container MVP:"
echo "  - Jeder User erhält 2 Container: Development und Production"
echo "  - Dev Container:  https://${SPAWNER_SUBDOMAIN}.${BASE_DOMAIN}/{slug}-dev"
echo "  - Prod Container: https://${SPAWNER_SUBDOMAIN}.${BASE_DOMAIN}/{slug}-prod"
echo ""
echo "WICHTIG - Passwordless Auth:"
echo "  Das System nutzt Magic Links (Email-basiert)!"
echo "  - SMTP konfigurieren: .env Datei anpassen"
echo "  - Datenbank wird automatisch mit allen Tabellen erstellt"
```

- Erkläre Multi-Container Feature
- Erkläre Passwordless Authentication
- Hinweis auf SMTP Konfiguration

---

## Zusammenfassung der Abhängigkeiten

### Externe Tools (müssen vorhanden sein)
| Tool | Min-Version | Zweck | Fallback |
|------|-------------|-------|---------|
| docker | 20.10 | Container management | Keine |
| docker compose | 2.0 | Service orchestration | docker-compose (v1) |
| git | 2.0+ | Repository management | Keine |
| curl/wget | - | Download .env.example | curl ODER wget |
| bash | 4.0+ | Script interpreter | Nur bash (nicht sh) |
| grep, cut, tr, sed | - | Text parsing | BusyBox kompatibel |

### Umgebungsvariablen (.env)
| Variable | Beispiel | Zweck | Required |
|----------|---------|-------|----------|
| `SECRET_KEY` | `abc123...` | Flask session secret | Ja |
| `BASE_DOMAIN` | `wieland.org` | Hauptdomain | Ja |
| `SPAWNER_SUBDOMAIN` | `coder` | Subdomain prefix | Ja |
| `TRAEFIK_NETWORK` | `web` | Docker network für Traefik | Ja |
| `USER_TEMPLATE_IMAGES` | `user-template-01:latest;...` | Templates zum bauen | Optional (Fallback) |
| `SPAWNER_PORT` | `5000` | Backend Port | Optional |

### Dateisystem-Anforderungen
- **Disk-Space**: 3-5 GB (für Docker Images)
- **Verzeichnisse**:
  - `.env` - Konfiguration (chmod 600)
  - `data/` - Datenbank (chmod 755)
  - `logs/` - Installation/App Logs (chmod 755)
  - `frontend/` - Frontend Code (optional)
  - `user-template-*/` - Template Dockerfiles

### Netzwerk-Anforderungen
- **Internet**: Zum downloaden .env.example, docker images, npm/pip packages
- **Docker Daemon**: Lokal erreichbar (Unix Socket oder TCP)
- **Docker Network**: `${TRAEFIK_NETWORK}` darf nicht existieren (oder wird geteilt mit Traefik)

### Sicherheits-Anforderungen
- `.env` muss **before** Installation vorhanden sein (mit SECRET_KEY gesetzt)
- Docker Socket nur für vertrauenswürdige Benutzer zugänglich
- SMTP-Credentials (wenn konfiguriert) müssen sicher sein

---

## Fehlerbehandlung & Logging

### Log-Datei: `spawner-install.log`

Alle Build-Outputs werden geloggt:
```
=== Spawner Installation 2026-02-03 10:00:00 ===

=== Build: user-template-01 ===
Step 1/5 : FROM nginx:latest
 ---> ...
Step 2/5 : COPY index.html /usr/share/nginx/html/
...
Successfully built abc123

=== Build: spawner-api ===
...
```

### Fehler-Handling mit `set -e`

**Reihenfolge:**
1. Script stoppt sofort bei erstem Fehler (`set -e`)
2. Zuletzt erfolgreich durchgeführte Zeile wird gezeigt
3. Admin kann Log-Datei prüfen: `tail spawner-install.log`

**Beispiel:**
```bash
# Fehler: Docker nicht installiert
$ bash install.sh
Fehler: Docker nicht gefunden!
→ exit 1 (Script stoppt)
→ install.sh log nicht weitergehe
```

### Recovery-Strategien

**Fehler: Zu alte Docker Version**
```bash
→ Installiere Docker ≥ 20.10
→ Starte install.sh erneut
```

**Fehler: .env nicht gefunden**
```bash
→ cp .env.example .env
→ nano .env  (setze SECRET_KEY, BASE_DOMAIN etc.)
→ bash install.sh
```

**Fehler: Template-Image Build fehlt**
```bash
→ Prüfe docker build Fehler in Log
→ Ursache meist: Dockerfile Syntax, Base Image nicht vorhanden
→ Korrigiere Dockerfile
→ Starte install.sh erneut (re-baut Imagen)
```

**Fehler: Git Clone fehlgeschlagen**
```bash
→ Prüfe Internet-Zugriff: curl https://gitea.iotxs.de
→ Prüfe Git SSH/HTTPS Keys (falls SSH)
→ Starte install.sh erneut
```

---

## Tipps für Synology NAS

### BusyBox-Kompatibilität

Install.sh läuft auf Synology mit BusyBox-Shell. Wichtige Unterschiede:

| Bash | BusyBox | Workaround in install.sh |
|------|---------|-------------------------|
| `sort -V` | Nicht vorhanden | Eigene `version_gte()` Funktion |
| `grep -P` (Perl) | Nicht vorhanden | Nutze Basic `grep` |
| `shopt` | Teilweise | `2>/dev/null \|\| true` (ignore error) |

### Docker auf Synology

```bash
# Docker läuft meist als root
id -u  # → 0 (root)

# Berechtigungen daher 755 OK (nicht 777 nötig)

# Git safe.directory Workaround
git config --global --add safe.directory /volume1/docker/spawner
```

### Disk-Space prüfen

```bash
# Vor Installation
df -h /volume1/docker/

# Braucht ~5 GB für alle Images
# Bei < 10 GB verfügbar → Warnung geben
```

---

## Neue Features (März 2026)

### 1. Git-Pull Auto-Fix für Synology

**Problem:** `git pull` schlägt fehl wegen Dateiberechtigungen.

**Lösung:**
```bash
git config core.filemode false  # Ignoriere Berechtigungsbits
git reset --hard origin/main    # Force-Sync mit Remote
```

**Automatisch aktiviert** wenn `git pull` fehlschlägt.

### 2. Update-and-Re-Exec Mechanism

**Problem:** Wenn `install.sh` selbst aktualisiert wird, lädt bash die alte Version weiter.

**Lösung:**
```bash
# Vor git pull: Checksumme von install.sh speichern
BEFORE_HASH=$(md5sum install.sh)

# Nach git pull: Checksumme vergleichen
AFTER_HASH=$(md5sum install.sh)

# Wenn geändert: Script mit exec neu starten
if [ "$BEFORE_HASH" != "$AFTER_HASH" ]; then
    export ALREADY_REEXECED="true"
    exec bash install.sh  # Neu starten mit neuem Code
fi
```

### 3. Alte User-Container Cleanup

**Problem:** Nach Code-Updates bleiben alte Container und verursachen Traefik-Konflikte.

**Lösung:** Automatisches Löschen aller alten User-Container vor Docker-Compose Restart.

```bash
# Phase 8 in install.sh
docker ps -a | grep "user-" | awk '{print $NF}'  # Zeige Container-Namen
docker rm -f $(docker ps -a | grep "user-" | awk '{print $1}')  # Lösche alle
```

**Ausgabe:**
```
Räume alte User-Container auf...
  Gefunden: 3 alte User-Container:
    • user-e220dd278a12-template-dictionary-1
    • user-abc123-template-01-2
    • user-xyz789-template-next-3

  Lösche Container...
  ✓ Alle alten Container gelöscht
```

---

## Häufige Fragen

**F: Kann ich install.sh mehrmals hintereinander ausführen?**
A: Ja. Script erkennt bestehende Installation (`.git` Verzeichnis) und führt `git pull` aus statt zu klonen.

**F: Was passiert bei Netzwerk-Fehler während Download?**
A: Script stoppt mit Fehler (set -e). Nach Netzwerk-Reparatur kann man `bash install.sh` erneut ausführen.

**F: Kann ich nur bestimmte Templates bauen?**
A: Ja. Ändere `.env`: `USER_TEMPLATE_IMAGES="user-template-01:latest"` (nur template-01)

**F: Wie debugge ich Build-Fehler?**
A: Prüfe spawner-install.log: `cat spawner-install.log | grep -A 20 "ERROR\|FEHLER"`

**F: Können User-Container nach Installation noch hinzugefügt werden?**
A: Ja. Neue `user-template-*` Ordner + .env update + `docker build` manuell oder nächster install.sh run.

---

**Stand:** 2026-02-03
**Version:** install.sh v0.1.0
**Kompatibilität:** Bash 4.0+, BusyBox, Docker 20.10+, Docker Compose 2.0+
