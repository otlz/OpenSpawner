#!/bin/bash
set -e

# ============================================================
# OpenSpawner - Installation Script
# https://github.com/otlz/OpenSpawner
# ============================================================

REPO_URL="https://github.com/otlz/OpenSpawner.git"
RAW_URL="https://raw.githubusercontent.com/otlz/OpenSpawner/main"
INSTALL_DIR="${PWD}"

# ============================================================
# UPDATE & RE-EXEC: Wenn install.sh aktualisiert wird, neu starten
# ============================================================
SCRIPT_PATH="${BASH_SOURCE[0]}"
if [ -f "${SCRIPT_PATH}" ]; then
    # Speichere Checksumme VOR git pull
    BEFORE_HASH=$(md5sum "${SCRIPT_PATH}" 2>/dev/null | awk '{print $1}' || echo "")
    ALREADY_REEXECED="${ALREADY_REEXECED:-false}"
fi
# VERSION automatisch aus Git-Tags bestimmen (z.B. v0.1.0, v0.2.1)
# Fallback auf "dev" wenn keine Tags vorhanden
VERSION=$(git describe --tags --always 2>/dev/null | sed 's/^v//' || echo "dev")
LOG_FILE="${INSTALL_DIR}/spawner-install.log"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Mindestversionen
MIN_DOCKER_VERSION="20.10"
MIN_COMPOSE_VERSION="2.0"

# ============================================================
# Hilfsfunktion: Versionen vergleichen (BusyBox/Synology kompatibel)
# Gibt 0 zurück wenn $1 >= $2, sonst 1
# ============================================================
version_gte() {
    # Vergleiche zwei Versionen (z.B. "20.10.21" >= "20.10")
    # Kompatibel mit BusyBox (kein sort -V)
    local ver1="$1"
    local ver2="$2"

    # Extrahiere Major.Minor.Patch (fuege .0 hinzu falls nötig)
    local v1_major v1_minor v1_patch
    local v2_major v2_minor v2_patch

    v1_major=$(echo "$ver1" | cut -d. -f1)
    v1_minor=$(echo "$ver1" | cut -d. -f2)
    v1_patch=$(echo "$ver1" | cut -d. -f3)
    v1_minor=${v1_minor:-0}
    v1_patch=${v1_patch:-0}

    v2_major=$(echo "$ver2" | cut -d. -f1)
    v2_minor=$(echo "$ver2" | cut -d. -f2)
    v2_patch=$(echo "$ver2" | cut -d. -f3)
    v2_minor=${v2_minor:-0}
    v2_patch=${v2_patch:-0}

    # Vergleiche Major
    if [ "$v1_major" -gt "$v2_major" ] 2>/dev/null; then
        return 0
    elif [ "$v1_major" -lt "$v2_major" ] 2>/dev/null; then
        return 1
    fi

    # Major gleich, vergleiche Minor
    if [ "$v1_minor" -gt "$v2_minor" ] 2>/dev/null; then
        return 0
    elif [ "$v1_minor" -lt "$v2_minor" ] 2>/dev/null; then
        return 1
    fi

    # Minor gleich, vergleiche Patch
    if [ "$v1_patch" -ge "$v2_patch" ] 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

echo ""
echo "============================================================"
echo "  OpenSpawner Installation v${VERSION}"
echo "============================================================"
echo ""

# Log-Datei initialisieren
echo "=== Spawner Installation $(date) ===" > "${LOG_FILE}"
echo "" >> "${LOG_FILE}"

# ============================================================
# 1. Prüfe .env
# ============================================================
if [ ! -f "${INSTALL_DIR}/.env" ]; then
    echo -e "${YELLOW}HINWEIS: Keine .env-Datei gefunden!${NC}"
    echo ""

    # Erstelle .env.example aus Repository
    echo "Lade .env.example herunter..."
    if command -v curl >/dev/null 2>&1; then
        curl -sSL "${RAW_URL}/.env.example" -o "${INSTALL_DIR}/.env.example"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "${RAW_URL}/.env.example" -O "${INSTALL_DIR}/.env.example"
    else
        echo -e "${RED}Fehler: Weder curl noch wget gefunden!${NC}"
        exit 1
    fi

    echo -e "${GREEN}Vorlage erstellt: .env.example${NC}"
    echo ""
    echo "Nächste Schritte:"
    echo "  1. Kopiere die Vorlage:  cp .env.example .env"
    echo "  2. Passe die Werte an:   nano .env"
    echo "     - SECRET_KEY generieren (siehe Kommentar in .env)"
    echo "     - BASE_DOMAIN setzen"
    echo "     - TRAEFIK_NETWORK prüfen"
    echo "  3. Führe erneut aus:    bash install.sh"
    echo ""
    exit 0
fi

echo -e "${GREEN}.env-Datei gefunden${NC}"

# Lade .env Variablen
set -a
source "${INSTALL_DIR}/.env"
set +a

# ============================================================
# 2. Prüfe Voraussetzungen
# ============================================================
echo ""
echo "Prüfe Voraussetzungen..."

# Docker - Existenz und Version prüfen
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}Fehler: Docker nicht gefunden!${NC}"
    echo "Installiere Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Docker Version extrahieren (z.B. "20.10.21" aus "Docker version 20.10.21, build baeda1f")
# BusyBox-kompatibel (kein grep -P)
DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || \
    docker version 2>/dev/null | grep -i "version" | head -1 | sed 's/.*version[: ]*\([0-9.]*\).*/\1/')
if [ -z "$DOCKER_VERSION" ]; then
    echo -e "${YELLOW}Warnung: Docker-Version konnte nicht ermittelt werden${NC}"
    echo -e "  Docker:         ${YELLOW}OK${NC} (Version unbekannt, min. ${MIN_DOCKER_VERSION} empfohlen)"
elif version_gte "$DOCKER_VERSION" "$MIN_DOCKER_VERSION"; then
    echo -e "  Docker:         ${GREEN}OK${NC} (v${DOCKER_VERSION})"
else
    echo -e "${RED}Fehler: Docker-Version ${DOCKER_VERSION} ist zu alt!${NC}"
    echo "Mindestversion: ${MIN_DOCKER_VERSION}"
    echo "Aktualisiere Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Docker Compose - Existenz und Version prüfen
# BusyBox-kompatibel (kein grep -P)
COMPOSE_VERSION=""
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    # Version extrahieren (z.B. "2.21.0" aus "Docker Compose version v2.21.0")
    COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || \
        docker compose version 2>/dev/null | sed 's/[^0-9.]*\([0-9][0-9.]*\).*/\1/' | head -1)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
    COMPOSE_VERSION=$(docker-compose version --short 2>/dev/null || \
        docker-compose version 2>/dev/null | sed 's/[^0-9.]*\([0-9][0-9.]*\).*/\1/' | head -1)
else
    echo -e "${RED}Fehler: Docker Compose nicht gefunden!${NC}"
    echo "Docker Compose ist Teil von Docker Desktop oder kann separat installiert werden."
    exit 1
fi

if [ -z "$COMPOSE_VERSION" ]; then
    echo -e "  Docker Compose: ${YELLOW}OK${NC} (${COMPOSE_CMD}, Version unbekannt)"
elif version_gte "$COMPOSE_VERSION" "$MIN_COMPOSE_VERSION"; then
    echo -e "  Docker Compose: ${GREEN}OK${NC} (v${COMPOSE_VERSION})"
else
    echo -e "${RED}Fehler: Docker Compose Version ${COMPOSE_VERSION} ist zu alt!${NC}"
    echo "Mindestversion: ${MIN_COMPOSE_VERSION}"
    echo "Aktualisiere Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Git
if ! command -v git >/dev/null 2>&1; then
    echo -e "${RED}Fehler: Git nicht gefunden!${NC}"
    exit 1
fi
echo -e "  Git:            ${GREEN}OK${NC}"

# ============================================================
# 3. Prüfe ob bereits installiert (Update vs. Neuinstallation)
# ============================================================
echo ""

# Git safe.directory setzen (für NAS/Container-Umgebungen)
git config --global --add safe.directory "${INSTALL_DIR}" 2>/dev/null || true

if [ -d "${INSTALL_DIR}/.git" ]; then
    echo -e "${YELLOW}Update erkannt - hole neueste Änderungen...${NC}"

    cd "${INSTALL_DIR}"

    # WICHTIG: Auf Synology gibt es Berechtigungsbits-Unterschiede (old mode 100644 vs new mode 100755)
    # Diese sind KEINE echten Code-Änderungen, daher einfach die Remote-Version nehmen
    git fetch origin 2>/dev/null || true

    # Versuche git pull
    if git pull origin main 2>/dev/null; then
        echo -e "${GREEN}Repository aktualisiert${NC}"
    else
        echo -e "${YELLOW}Git-Pull fehlgeschlagen, versuche Reset...${NC}"
        # Wenn pull fehlschlaegt: Berechtigungen korrigieren und Hard Reset machen
        git config core.filemode false  # Ignoriere Berechtigungsbits
        git reset --hard HEAD 2>/dev/null || true
        git fetch origin 2>/dev/null || true

        if git reset --hard origin/main 2>/dev/null; then
            echo -e "${GREEN}Hard Reset zu origin/main erfolgreich${NC}"
        else
            echo -e "${YELLOW}Git-Update fehlgeschlagen, fahre mit lokalen Dateien fort...${NC}"
        fi
    fi

    # ============================================================
    # Prüfe ob install.sh selbst aktualisiert wurde - wenn ja, neu starten
    # ============================================================
    if [ "${ALREADY_REEXECED}" = "false" ] && [ -f "${SCRIPT_PATH}" ]; then
        AFTER_HASH=$(md5sum "${SCRIPT_PATH}" 2>/dev/null | awk '{print $1}' || echo "")
        if [ -n "${BEFORE_HASH}" ] && [ -n "${AFTER_HASH}" ] && [ "${BEFORE_HASH}" != "${AFTER_HASH}" ]; then
            echo ""
            echo -e "${BLUE}install.sh wurde aktualisiert - starte Skript neu...${NC}"
            sleep 1
            export ALREADY_REEXECED="true"
            exec bash "${SCRIPT_PATH}"
            exit $?
        fi
    fi
else
    echo "Neuinstallation - klone Repository..."

    # Temporaeres Verzeichnis für Clone
    TEMP_DIR=$(mktemp -d)

    if git clone "${REPO_URL}" "${TEMP_DIR}"; then
        # Kopiere Dateien (ueberschreibt nicht .env)
        shopt -s dotglob 2>/dev/null || true
        for item in "${TEMP_DIR}"/*; do
            basename_item=$(basename "$item")
            if [ "$basename_item" != ".env" ] && [ "$basename_item" != ".git" ]; then
                cp -r "$item" "${INSTALL_DIR}/"
            fi
        done

        # .git Verzeichnis kopieren für Updates
        cp -r "${TEMP_DIR}/.git" "${INSTALL_DIR}/"

        rm -rf "${TEMP_DIR}"
        echo -e "${GREEN}Repository geklont${NC}"
    else
        echo -e "${RED}Fehler: Repository konnte nicht geklont werden!${NC}"
        echo "URL: ${REPO_URL}"
        rm -rf "${TEMP_DIR}"
        exit 1
    fi
fi

# ============================================================
# 4. Verzeichnisse und Rechte setzen
# ============================================================
echo ""
echo "Setze Verzeichnisse und Berechtigungen..."

# Verzeichnisse erstellen falls nicht vorhanden
mkdir -p "${INSTALL_DIR}/data"
mkdir -p "${INSTALL_DIR}/logs"

# Berechtigungen setzen (rwx für Owner, rx für Group/Other)
chmod 755 "${INSTALL_DIR}/data"
chmod 755 "${INSTALL_DIR}/logs"

# Fuer Docker: Verzeichnisse muessen vom Container beschreibbar sein
# Option 1: Wenn Container als root läuft (Standard) - 755 reicht
# Option 2: Wenn Container als non-root läuft - 777 oder chown nötig

# Pruefen ob wir als root laufen (für chown)
if [ "$(id -u)" = "0" ]; then
    # Als root: Owner auf aktuellen User setzen (oder Docker-User)
    # Standard: belassen wie es ist (root kann alles)
    echo -e "  data/:  ${GREEN}OK${NC} (755, root)"
    echo -e "  logs/:  ${GREEN}OK${NC} (755, root)"
else
    # Als normaler User: Verzeichnisse muessen beschreibbar sein
    # Docker-Container läuft meist als root, daher 755 ausreichend
    # Falls Container als non-root läuft, auf 777 setzen:
    # chmod 777 "${INSTALL_DIR}/data" "${INSTALL_DIR}/logs"
    echo -e "  data/:  ${GREEN}OK${NC} (755)"
    echo -e "  logs/:  ${GREEN}OK${NC} (755)"
fi

# .env Datei schuetzen (nur Owner kann lesen/schreiben)
if [ -f "${INSTALL_DIR}/.env" ]; then
    chmod 600 "${INSTALL_DIR}/.env"
    echo -e "  .env:   ${GREEN}OK${NC} (600, nur Owner)"
fi

# install.sh ausfuehrbar machen
if [ -f "${INSTALL_DIR}/install.sh" ]; then
    chmod +x "${INSTALL_DIR}/install.sh"
fi

# ============================================================
# 5. Docker-Netzwerk prüfen/erstellen
# ============================================================
echo ""
NETWORK="${TRAEFIK_NETWORK:-web}"
echo "Prüfe Docker-Netzwerk: ${NETWORK}"

if docker network inspect "${NETWORK}" >/dev/null 2>&1; then
    echo -e "  Netzwerk '${NETWORK}': ${GREEN}existiert${NC}"
else
    echo -e "${RED}Fehler: Docker-Netzwerk '${NETWORK}' existiert nicht!${NC}"
    echo ""
    echo "Das Netzwerk muss von Traefik erstellt werden oder bereits existieren."
    echo "Stelle sicher, dass Traefik läuft und das Netzwerk '${NETWORK}' verwendet."
    echo ""
    echo "Optionen:"
    echo "  1. Starte Traefik zuerst (empfohlen)"
    echo "  2. Erstelle das Netzwerk manuell: docker network create ${NETWORK}"
    echo ""
    echo "Erstelle Netzwerk automatisch..."
    docker network create "${NETWORK}" 2>/dev/null || true
    echo -e "  Netzwerk '${NETWORK}': ${GREEN}erstellt/vorhanden${NC}"
fi

# ============================================================
# 6. Prüfe ob Traefik läuft
# ============================================================
echo ""
echo "Prüfe Traefik..."

# Suche nach laufenden Traefik-Containern
TRAEFIK_CONTAINER=$(docker ps --filter "name=traefik" --filter "status=running" --format "{{.Names}}" 2>/dev/null | head -1)

# Falls nicht nach Name gefunden, suche nach Image
if [ -z "$TRAEFIK_CONTAINER" ]; then
    TRAEFIK_CONTAINER=$(docker ps --filter "ancestor=traefik" --filter "status=running" --format "{{.Names}}" 2>/dev/null | head -1)
fi

# Falls immer noch nicht gefunden, suche nach Label (traefik.enable=true auf sich selbst)
if [ -z "$TRAEFIK_CONTAINER" ]; then
    TRAEFIK_CONTAINER=$(docker ps --filter "status=running" --format "{{.Names}}" 2>/dev/null | while read name; do
        if docker inspect "$name" 2>/dev/null | grep -q '"traefik.http.routers\|"com.docker.compose.service": "traefik"'; then
            echo "$name"
            break
        fi
    done)
fi

if [ -n "$TRAEFIK_CONTAINER" ]; then
    # Prüfe Traefik-Version (BusyBox-kompatibel)
    TRAEFIK_VERSION=$(docker exec "$TRAEFIK_CONTAINER" traefik version 2>/dev/null | \
        grep -i "version" | head -1 | sed 's/.*Version[: ]*\([0-9.]*\).*/\1/' || echo "unbekannt")
    [ -z "$TRAEFIK_VERSION" ] && TRAEFIK_VERSION="unbekannt"
    echo -e "  Traefik:        ${GREEN}läuft${NC} (Container: ${TRAEFIK_CONTAINER}, v${TRAEFIK_VERSION})"

    # Prüfe ob Traefik am gleichen Netzwerk haengt
    TRAEFIK_NETWORKS=$(docker inspect "$TRAEFIK_CONTAINER" --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>/dev/null)
    if echo "$TRAEFIK_NETWORKS" | grep -q "$NETWORK"; then
        echo -e "  Traefik-Netzwerk: ${GREEN}OK${NC} (verbunden mit '${NETWORK}')"
    else
        echo -e "  ${YELLOW}Warnung: Traefik ist nicht mit Netzwerk '${NETWORK}' verbunden${NC}"
        echo "  Traefik-Netzwerke: ${TRAEFIK_NETWORKS}"
        echo "  Stelle sicher, dass TRAEFIK_NETWORK in .env korrekt konfiguriert ist."
    fi
else
    echo -e "  ${YELLOW}Warnung: Kein laufender Traefik-Container gefunden!${NC}"
    echo ""
    echo "  Traefik wird für das Routing der User-Container benötigt."
    echo "  Der Spawner kann ohne Traefik gestartet werden, aber:"
    echo "    - User-Container sind nur lokal erreichbar"
    echo "    - Kein automatisches HTTPS"
    echo "    - Kein Subdomain-Routing"
    echo ""
    echo -e "  ${YELLOW}Fortfahren ohne Traefik...${NC}"
fi

# ============================================================
# 7. Docker-Images bauen
# ============================================================
echo ""
echo "Baue Docker-Images (Dynamisches Template-System)..."
echo ""

# Stoppe laufende Container
${COMPOSE_CMD} down 2>/dev/null || true

# Lese USER_TEMPLATE_IMAGES aus .env
USER_TEMPLATE_IMAGES=""
if [ -f "${INSTALL_DIR}/.env" ]; then
    # Extrahiere USER_TEMPLATE_IMAGES (mit oder ohne Quotes)
    USER_TEMPLATE_IMAGES=$(grep "^USER_TEMPLATE_IMAGES=" "${INSTALL_DIR}/.env" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
fi

# Fallback auf .env.example wenn .env nicht existiert
if [ -z "$USER_TEMPLATE_IMAGES" ] && [ -f "${INSTALL_DIR}/.env.example" ]; then
    echo -e "${YELLOW}⚠️  .env nicht gefunden oder USER_TEMPLATE_IMAGES nicht definiert${NC}"
    echo "  Nutze .env.example als Fallback..."
    USER_TEMPLATE_IMAGES=$(grep "^USER_TEMPLATE_IMAGES=" "${INSTALL_DIR}/.env.example" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
fi

# Fallback: Wenn noch immer leer, baue alle Templates (rückwärtskompatibel)
if [ -z "$USER_TEMPLATE_IMAGES" ]; then
    echo -e "${YELLOW}⚠️  USER_TEMPLATE_IMAGES nicht konfiguriert${NC}"
    echo "  Fallback: Baue alle user-template-* Verzeichnisse (alte Logik)..."
    echo ""

    BUILT_TEMPLATES=0
    TEMPLATE_DIRS=$(find "${INSTALL_DIR}/templates" -maxdepth 1 -type d -name "user-template*" 2>/dev/null | wc -l)
    TOTAL_BUILDS=$((2 + TEMPLATE_DIRS))
    BUILD_STEP=$((BUILD_STEP + 1))

    for template_dir in "${INSTALL_DIR}"/templates/user-template*; do
        [ -d "$template_dir" ] || continue
        template_name=$(basename "$template_dir")
        image_name="${template_name}:latest"

        echo "  [$BUILD_STEP/$TOTAL_BUILDS] Baue ${template_name}..."

        if [[ "$template_name" == *"next"* ]]; then
            echo -e "        ${BLUE}Dies kann 2-5 Minuten dauern (npm install + build)...${NC}"
        fi

        echo ""
        BUILD_LOG="${LOG_FILE}"
        echo "" >> "${LOG_FILE}"
        echo "=== Build: ${template_name} ===" >> "${LOG_FILE}"

        docker build --no-cache -t "${image_name}" "${template_dir}/" >> "${BUILD_LOG}" 2>&1
        BUILD_EXIT=$?
        grep -E "(Step |#[0-9]+ |Successfully|ERROR|error:|COPY|RUN|FROM)" "${BUILD_LOG}" 2>/dev/null | sed 's/^/        /' || true

        if [ $BUILD_EXIT -eq 0 ] && docker image inspect "${image_name}" >/dev/null 2>&1; then
            echo ""
            echo -e "  ${template_name}: ${GREEN}OK${NC}"
            BUILT_TEMPLATES=$((BUILT_TEMPLATES + 1))
        else
            echo ""
            echo -e "  ${template_name}: ${RED}FEHLER${NC}"
            echo "  Siehe Build-Log: ${LOG_FILE}"
            tail -50 "${BUILD_LOG}"
            exit 1
        fi

        BUILD_STEP=$((BUILD_STEP + 1))
    done

    if [ $BUILT_TEMPLATES -eq 0 ]; then
        echo -e "${RED}FEHLER: Keine Template-Verzeichnisse gefunden!${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}Alle ${BUILT_TEMPLATES} Template(s) erfolgreich gebaut.${NC}"
else
    # .env-basiertes Building (neue Logik)
    echo "  Baue Templates aus .env Konfiguration..."
    echo ""

    # Konvertiere zu Array (split by ;)
    IFS=';' read -ra TEMPLATE_IMAGES <<< "$USER_TEMPLATE_IMAGES"

    # Zähle Templates für Fortschrittsanzeige
    TOTAL_TEMPLATES=${#TEMPLATE_IMAGES[@]}
    TOTAL_BUILDS=$((2 + TOTAL_TEMPLATES))
    BUILD_STEP=$((BUILD_STEP + 1))

    BUILT_TEMPLATES=0

    for image_with_tag in "${TEMPLATE_IMAGES[@]}"; do
        # Entferne Whitespace
        image_with_tag=$(echo "$image_with_tag" | xargs)

        [ -z "$image_with_tag" ] && continue

        # Extrahiere Verzeichnisnamen (vor dem :)
        template_dir_name="${image_with_tag%%:*}"

        # Extrahiere Tag (nach dem :)
        template_tag="${image_with_tag##*:}"

        # Fallback auf :latest wenn kein Tag
        [ -z "$template_tag" ] && template_tag="latest"

        # Vollständiger Pfad zum Template-Verzeichnis
        template_dir="${INSTALL_DIR}/${template_dir_name}"

        echo "  [$BUILD_STEP/$TOTAL_BUILDS] Baue Template: ${template_dir_name}:${template_tag}"

        # Prüfe ob Verzeichnis existiert
        if [ ! -d "$template_dir" ]; then
            echo -e "        ${RED}❌ Fehler: Template-Verzeichnis nicht gefunden${NC}"
            echo "        Definiert in .env: USER_TEMPLATE_IMAGES"
            echo "        Erwartetes Verzeichnis: ${template_dir}"
            echo "        Überspringe dieses Template."
            echo ""
            BUILD_STEP=$((BUILD_STEP + 1))
            continue
        fi

        # Dockerfile vorhanden?
        if [ ! -f "${template_dir}/Dockerfile" ]; then
            echo -e "        ${RED}❌ Fehler: Kein Dockerfile gefunden${NC}"
            echo "        Pfad: ${template_dir}/Dockerfile"
            echo "        Überspringe dieses Template."
            echo ""
            BUILD_STEP=$((BUILD_STEP + 1))
            continue
        fi

        # Special handling für Next.js Templates
        if [[ "$template_dir_name" == *"next"* ]]; then
            echo -e "        ${BLUE}Dies kann 2-5 Minuten dauern (npm install + build)...${NC}"
        fi

        echo ""

        BUILD_LOG="${LOG_FILE}"
        echo "" >> "${LOG_FILE}"
        echo "=== Build: ${template_dir_name}:${template_tag} ===" >> "${LOG_FILE}"

        docker build --no-cache -t "${template_dir_name}:${template_tag}" "${template_dir}/" >> "${BUILD_LOG}" 2>&1
        BUILD_EXIT=$?

        # Gefilterten Output anzeigen
        grep -E "(Step |#[0-9]+ |Successfully|ERROR|error:|COPY|RUN|FROM)" "${BUILD_LOG}" 2>/dev/null | sed 's/^/        /' || true

        # Prüfe ob Build erfolgreich UND Image existiert
        if [ $BUILD_EXIT -eq 0 ] && docker image inspect "${template_dir_name}:${template_tag}" >/dev/null 2>&1; then
            echo ""
            echo -e "        ${template_dir_name}: ${GREEN}OK${NC}"
            BUILT_TEMPLATES=$((BUILT_TEMPLATES + 1))
        else
            echo ""
            echo -e "        ${template_dir_name}: ${RED}FEHLER${NC}"
            echo "        Siehe Build-Log: ${LOG_FILE}"
            echo "        Letzte 50 Zeilen:"
            tail -50 "${BUILD_LOG}"
            exit 1
        fi

        echo ""
        BUILD_STEP=$((BUILD_STEP + 1))
    done

    if [ $BUILT_TEMPLATES -eq 0 ]; then
        echo -e "${RED}FEHLER: Keine Templates aus USER_TEMPLATE_IMAGES gebaut!${NC}"
        echo "Prüfe .env: USER_TEMPLATE_IMAGES"
        exit 1
    fi

    echo -e "${GREEN}✅ ${BUILT_TEMPLATES}/${TOTAL_TEMPLATES} Template(s) erfolgreich gebaut.${NC}"

    # Warne bei ungenutzten Template-Verzeichnissen
    echo ""
    echo "  Prüfe auf ungekonfigurierte Template-Verzeichnisse..."
    UNUSED_COUNT=0

    for template_dir in "${INSTALL_DIR}"/templates/user-template*; do
        [ -d "$template_dir" ] || continue
        template_name=$(basename "$template_dir")

        # Ist dieses Template in USER_TEMPLATE_IMAGES definiert?
        if [[ ! "$USER_TEMPLATE_IMAGES" =~ "$template_name" ]]; then
            if [ $UNUSED_COUNT -eq 0 ]; then
                echo -e "  ${YELLOW}⚠️  Ungekonfigurierte Template-Verzeichnisse:${NC}"
            fi
            echo "        - ${template_name} (nicht in USER_TEMPLATE_IMAGES definiert)"
            UNUSED_COUNT=$((UNUSED_COUNT + 1))
        fi
    done

    if [ $UNUSED_COUNT -gt 0 ]; then
        echo "  Hinweis: Diese Templates wurden NICHT gebaut."
        echo "  Um sie zu bauen, füge sie zu .env hinzu: USER_TEMPLATE_IMAGES=...;${template_name}:latest"
    fi
    echo ""
fi

# Spawner Backend Image bauen
echo "  [$BUILD_STEP/$TOTAL_BUILDS] Baue Spawner API (Flask Backend)..."
echo ""

BUILD_LOG="${LOG_FILE}"
echo "" >> "${LOG_FILE}"
echo "=== Build: spawner-api ===" >> "${LOG_FILE}"
docker build --no-cache -t spawner:latest "${INSTALL_DIR}/" >> "${BUILD_LOG}" 2>&1
BUILD_EXIT=$?

grep -E "(Step |#[0-9]+ |Successfully|ERROR|error:|COPY|RUN|FROM)" "${BUILD_LOG}" 2>/dev/null | sed 's/^/        /' || true

if [ $BUILD_EXIT -eq 0 ] && docker image inspect spawner:latest >/dev/null 2>&1; then
    echo ""
    echo -e "  spawner-api: ${GREEN}OK${NC}"
else
    echo ""
    echo -e "  spawner-api: ${RED}FEHLER${NC}"
    echo "  Siehe Build-Log: ${LOG_FILE}"
    echo "  Letzte 50 Zeilen:"
    tail -50 "${BUILD_LOG}"
    exit 1
fi
BUILD_STEP=$((BUILD_STEP + 1))

# Frontend Image bauen
if [ -d "${INSTALL_DIR}/frontend" ]; then
    echo "  [$BUILD_STEP/$TOTAL_BUILDS] Baue Frontend (Next.js)..."
    echo -e "        ${BLUE}Dies kann 2-5 Minuten dauern (npm install + build)...${NC}"
    echo ""

    BUILD_LOG="${LOG_FILE}"
    echo "" >> "${LOG_FILE}"
    echo "=== Build: spawner-frontend ===" >> "${LOG_FILE}"
    docker build --no-cache -t spawner-frontend:latest "${INSTALL_DIR}/frontend/" >> "${BUILD_LOG}" 2>&1
    BUILD_EXIT=$?

    grep -E "(Step |#[0-9]+ |Successfully|ERROR|error:|COPY|RUN|FROM)" "${BUILD_LOG}" 2>/dev/null | sed 's/^/        /' || true

    if [ $BUILD_EXIT -eq 0 ] && docker image inspect spawner-frontend:latest >/dev/null 2>&1; then
        echo ""
        echo -e "  spawner-frontend: ${GREEN}OK${NC}"
    else
        echo ""
        echo -e "  spawner-frontend: ${RED}FEHLER${NC}"
        echo "  Siehe Build-Log: ${LOG_FILE}"
        echo "  Letzte 50 Zeilen:"
        tail -50 "${BUILD_LOG}"
        exit 1
    fi
    BUILD_STEP=$((BUILD_STEP + 1))
fi

echo ""
echo "Alle erforderlichen Images erfolgreich gebaut."

# ============================================================
# 8. Alte User-Container aufräumen (Traefik-Konflikt Prävention)
# ============================================================
echo ""
echo "Räume alte User-Container auf..."

# Liste und lösche alte Container mit detaillierter Ausgabe
OLD_CONTAINER_LIST=$(docker ps -a 2>/dev/null | grep "user-" | awk '{print $NF}' || true)
OLD_CONTAINER_COUNT=$(echo "$OLD_CONTAINER_LIST" | grep -c . || true)

if [ "$OLD_CONTAINER_COUNT" -gt 0 ]; then
    echo -e "  ${YELLOW}Gefunden: ${OLD_CONTAINER_COUNT} alte User-Container:${NC}"
    echo "$OLD_CONTAINER_LIST" | while read container_name; do
        [ -z "$container_name" ] && continue
        echo "    • $container_name"
    done

    echo ""
    echo "  Lösche Container..."
    docker rm -f $(docker ps -a | grep "user-" | awk '{print $1}') 2>/dev/null || true
    echo -e "  ${GREEN}✓ Alle alten Container gelöscht${NC}"
else
    echo "  ✓ Keine alten Container vorhanden"
fi

# ============================================================
# 9. Container starten
# ============================================================
echo ""
echo "Starte Container..."
${COMPOSE_CMD} up -d

# Warte auf Health-Check
echo ""
echo "Warte auf Spawner-Start..."
sleep 5

# Health-Check für API
SPAWNER_URL="http://localhost:${SPAWNER_PORT:-5000}/health"
if curl -sf "${SPAWNER_URL}" >/dev/null 2>&1; then
    echo -e "  API Health-Check:      ${GREEN}OK${NC}"
else
    echo -e "  API Health-Check:      ${YELLOW}Noch nicht bereit (normal beim ersten Start)${NC}"
fi

# Health-Check für Frontend
if curl -sf "http://localhost:3000/" >/dev/null 2>&1; then
    echo -e "  Frontend Health-Check: ${GREEN}OK${NC}"
else
    echo -e "  Frontend Health-Check: ${YELLOW}Noch nicht bereit (normal beim ersten Start)${NC}"
fi

# ============================================================
# 9. Fertig
# ============================================================
echo ""
echo "============================================================"
echo -e "  ${GREEN}Installation abgeschlossen!${NC}"
echo "============================================================"
echo ""
echo "Installations-Log: ${LOG_FILE}"

# URLs anzeigen
SCHEME="https"
if [ "${BASE_DOMAIN:-localhost}" = "localhost" ]; then
    SCHEME="http"
fi
FULL_URL="${SCHEME}://${SPAWNER_SUBDOMAIN:-coder}.${BASE_DOMAIN:-localhost}"

echo "Zugriff:"
echo "  Frontend:    ${FULL_URL}"
echo "  API:         ${FULL_URL}/api"
echo "  Health:      ${FULL_URL}/health"
echo ""
echo "Lokaler Zugriff (ohne Traefik):"
echo "  API:         http://localhost:${SPAWNER_PORT:-5000}"
echo "  Frontend:    http://localhost:3000"
echo ""
echo "Nützliche Befehle:"
echo "  Status:      ${COMPOSE_CMD} ps"
echo "  Logs API:    ${COMPOSE_CMD} logs -f spawner"
echo "  Logs FE:     ${COMPOSE_CMD} logs -f frontend"
echo "  Neustart:    ${COMPOSE_CMD} restart"
echo "  Stoppen:     ${COMPOSE_CMD} down"
echo ""
echo "WICHTIG - Multi-Container MVP:"
echo "  - Jeder User erhält 2 Container: Development und Production"
echo "  - Dev Container:  https://${SPAWNER_SUBDOMAIN}.${BASE_DOMAIN}/{slug}-dev"
echo "  - Prod Container: https://${SPAWNER_SUBDOMAIN}.${BASE_DOMAIN}/{slug}-prod"
echo ""
echo "WICHTIG - Passwordless Auth:"
echo "  Das System nutzt Magic Links (Email-basiert)!"
echo "  - SMTP konfigurieren: .env Datei anpassen"
echo "  - Datenbank wird automatisch mit allen Tabellen erstellt"
echo ""
echo "Template Configuration (.env):"
echo "  USER_TEMPLATE_IMAGE_DEV=user-service-template:latest"
echo "  USER_TEMPLATE_IMAGE_PROD=user-template-next:latest"
echo ""
