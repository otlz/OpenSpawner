#!/bin/bash
set -e

# ============================================================
# Container Spawner - Installationsskript
# https://gitea.iotxs.de/RainerWieland/spawner
# ============================================================

REPO_URL="https://gitea.iotxs.de/RainerWieland/spawner.git"
RAW_URL="https://gitea.iotxs.de/RainerWieland/spawner/raw/branch/main"
INSTALL_DIR="${PWD}"
VERSION="0.1.0"

# Farben fuer Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "============================================================"
echo "  Container Spawner Installation v${VERSION}"
echo "============================================================"
echo ""

# ============================================================
# 1. Pruefe .env
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
    echo "Naechste Schritte:"
    echo "  1. Kopiere die Vorlage:  cp .env.example .env"
    echo "  2. Passe die Werte an:   nano .env"
    echo "     - SECRET_KEY generieren (siehe Kommentar in .env)"
    echo "     - BASE_DOMAIN setzen"
    echo "     - TRAEFIK_NETWORK pruefen"
    echo "  3. Fuehre erneut aus:    bash install.sh"
    echo ""
    exit 0
fi

echo -e "${GREEN}.env-Datei gefunden${NC}"

# Lade .env Variablen
set -a
source "${INSTALL_DIR}/.env"
set +a

# ============================================================
# 2. Pruefe Voraussetzungen
# ============================================================
echo ""
echo "Pruefe Voraussetzungen..."

# Docker
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}Fehler: Docker nicht gefunden!${NC}"
    echo "Installiere Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "  Docker:         ${GREEN}OK${NC}"

# Docker Compose
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}Fehler: docker-compose nicht gefunden!${NC}"
    exit 1
fi
echo -e "  Docker Compose: ${GREEN}OK${NC} (${COMPOSE_CMD})"

# Git
if ! command -v git >/dev/null 2>&1; then
    echo -e "${RED}Fehler: Git nicht gefunden!${NC}"
    exit 1
fi
echo -e "  Git:            ${GREEN}OK${NC}"

# ============================================================
# 3. Pruefe ob bereits installiert (Update vs. Neuinstallation)
# ============================================================
echo ""
if [ -d "${INSTALL_DIR}/.git" ]; then
    echo -e "${YELLOW}Update erkannt - hole neueste Aenderungen...${NC}"

    # Sichere lokale Aenderungen
    if ! git diff --quiet 2>/dev/null; then
        echo "Lokale Aenderungen gefunden, erstelle Stash..."
        git stash
    fi

    git fetch origin
    git pull origin main

    echo -e "${GREEN}Repository aktualisiert${NC}"
else
    echo "Neuinstallation - klone Repository..."

    # Temporaeres Verzeichnis fuer Clone
    TEMP_DIR=$(mktemp -d)
    git clone "${REPO_URL}" "${TEMP_DIR}"

    # Kopiere Dateien (ueberschreibt nicht .env)
    shopt -s dotglob
    for item in "${TEMP_DIR}"/*; do
        basename_item=$(basename "$item")
        if [ "$basename_item" != ".env" ] && [ "$basename_item" != ".git" ]; then
            cp -r "$item" "${INSTALL_DIR}/"
        fi
    done

    # .git Verzeichnis kopieren fuer Updates
    cp -r "${TEMP_DIR}/.git" "${INSTALL_DIR}/"

    rm -rf "${TEMP_DIR}"
    echo -e "${GREEN}Repository geklont${NC}"
fi

# ============================================================
# 4. Verzeichnisse und Rechte setzen
# ============================================================
echo ""
echo "Setze Verzeichnisse und Berechtigungen..."

# Verzeichnisse erstellen falls nicht vorhanden
mkdir -p "${INSTALL_DIR}/data"
mkdir -p "${INSTALL_DIR}/logs"

# Berechtigungen setzen (rwx fuer Owner, rx fuer Group/Other)
chmod 755 "${INSTALL_DIR}/data"
chmod 755 "${INSTALL_DIR}/logs"

# Fuer Docker: Verzeichnisse muessen vom Container beschreibbar sein
# Option 1: Wenn Container als root laeuft (Standard) - 755 reicht
# Option 2: Wenn Container als non-root laeuft - 777 oder chown noetig

# Pruefen ob wir als root laufen (fuer chown)
if [ "$(id -u)" = "0" ]; then
    # Als root: Owner auf aktuellen User setzen (oder Docker-User)
    # Standard: belassen wie es ist (root kann alles)
    echo -e "  data/:  ${GREEN}OK${NC} (755, root)"
    echo -e "  logs/:  ${GREEN}OK${NC} (755, root)"
else
    # Als normaler User: Verzeichnisse muessen beschreibbar sein
    # Docker-Container laeuft meist als root, daher 755 ausreichend
    # Falls Container als non-root laeuft, auf 777 setzen:
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
# 5. Docker-Netzwerk pruefen/erstellen
# ============================================================
echo ""
NETWORK="${TRAEFIK_NETWORK:-web}"
echo "Pruefe Docker-Netzwerk: ${NETWORK}"

if docker network inspect "${NETWORK}" >/dev/null 2>&1; then
    echo -e "  Netzwerk '${NETWORK}': ${GREEN}existiert${NC}"
else
    echo -e "  ${YELLOW}Netzwerk '${NETWORK}' nicht gefunden - erstelle...${NC}"
    docker network create "${NETWORK}"
    echo -e "  Netzwerk '${NETWORK}': ${GREEN}erstellt${NC}"
fi

# ============================================================
# 6. Docker-Images bauen
# ============================================================
echo ""
echo "Baue Docker-Images..."

# Stoppe laufende Container
${COMPOSE_CMD} down 2>/dev/null || true

# User-Template Image bauen (fuer User-Container)
if [ -d "${INSTALL_DIR}/user-template" ]; then
    echo "  [1/4] Baue user-service-template (User-Container)..."
    if docker build --no-cache -t user-service-template:latest "${INSTALL_DIR}/user-template/" > /dev/null 2>&1; then
        echo -e "  user-service-template: ${GREEN}OK${NC}"
    else
        echo -e "  user-service-template: ${RED}FEHLER${NC}"
        echo "  Versuche mit detaillierter Ausgabe..."
        docker build --no-cache -t user-service-template:latest "${INSTALL_DIR}/user-template/"
        exit 1
    fi
fi

# User-Template-Next Image bauen (alternatives Template, optional)
if [ -d "${INSTALL_DIR}/user-template-next" ]; then
    echo "  [2/4] Baue user-template-next (alternatives Template)..."
    if docker build -t user-template-next:latest "${INSTALL_DIR}/user-template-next/" > /dev/null 2>&1; then
        echo -e "  user-template-next: ${GREEN}OK${NC}"
    else
        echo -e "  user-template-next: ${YELLOW}WARNUNG - Build fehlgeschlagen (optional)${NC}"
    fi
fi

# Spawner Backend Image bauen
echo "  [3/4] Baue Spawner API (Flask Backend)..."
if docker build -t spawner:latest "${INSTALL_DIR}/" > /dev/null 2>&1; then
    echo -e "  spawner-api: ${GREEN}OK${NC}"
else
    echo -e "  spawner-api: ${RED}FEHLER${NC}"
    docker build -t spawner:latest "${INSTALL_DIR}/"
    exit 1
fi

# Frontend Image bauen
if [ -d "${INSTALL_DIR}/frontend" ]; then
    echo "  [4/4] Baue Frontend (Next.js)..."
    echo "        Dies kann einige Minuten dauern (npm install + build)..."
    if docker build -t spawner-frontend:latest "${INSTALL_DIR}/frontend/" 2>&1 | grep -E "(error|Error|ERROR)" > /dev/null; then
        echo -e "  spawner-frontend: ${RED}FEHLER${NC}"
        echo "  Versuche mit detaillierter Ausgabe..."
        docker build -t spawner-frontend:latest "${INSTALL_DIR}/frontend/"
        exit 1
    else
        docker build -t spawner-frontend:latest "${INSTALL_DIR}/frontend/" > /dev/null 2>&1
        echo -e "  spawner-frontend: ${GREEN}OK${NC}"
    fi
fi

echo ""
echo "Alle Images erfolgreich gebaut."

# ============================================================
# 7. Container starten
# ============================================================
echo ""
echo "Starte Container..."
${COMPOSE_CMD} up -d

# Warte auf Health-Check
echo ""
echo "Warte auf Spawner-Start..."
sleep 5

# Health-Check fuer API
SPAWNER_URL="http://localhost:${SPAWNER_PORT:-5000}/health"
if curl -sf "${SPAWNER_URL}" >/dev/null 2>&1; then
    echo -e "  API Health-Check:      ${GREEN}OK${NC}"
else
    echo -e "  API Health-Check:      ${YELLOW}Noch nicht bereit (normal beim ersten Start)${NC}"
fi

# Health-Check fuer Frontend
if curl -sf "http://localhost:3000/" >/dev/null 2>&1; then
    echo -e "  Frontend Health-Check: ${GREEN}OK${NC}"
else
    echo -e "  Frontend Health-Check: ${YELLOW}Noch nicht bereit (normal beim ersten Start)${NC}"
fi

# ============================================================
# 8. Fertig
# ============================================================
echo ""
echo "============================================================"
echo -e "  ${GREEN}Installation abgeschlossen!${NC}"
echo "============================================================"
echo ""

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
echo "Nuetzliche Befehle:"
echo "  Status:      ${COMPOSE_CMD} ps"
echo "  Logs API:    ${COMPOSE_CMD} logs -f spawner"
echo "  Logs FE:     ${COMPOSE_CMD} logs -f frontend"
echo "  Neustart:    ${COMPOSE_CMD} restart"
echo "  Stoppen:     ${COMPOSE_CMD} down"
echo ""
