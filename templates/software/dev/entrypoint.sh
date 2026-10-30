#!/bin/sh
# Starts code-server for the user container.
# Auth is handled in front of the container (Traefik forwardAuth via the spawner).
set -e

# Path prefix Traefik serves this container under, e.g. /3f2a9c1b7d4e-template-dev
# (empty in local mode, where the container has its own port)
BASE_PATH="${SUBFOLDER%/}"

# Dev servers are reachable through code-server's proxy:
#   relative URLs (PHP, Flask):  <container-url>/proxy/<port>/
#   Next.js / Vite:               <container-url>/absproxy/<port>/  with basePath "$PREVIEW_BASE/<port>"
export PREVIEW_BASE="${BASE_PATH}/absproxy"

mkdir -p "$HOME/project"

set -- --bind-addr 0.0.0.0:8080 --auth none \
    --disable-telemetry --disable-update-check --disable-workspace-trust \
    --ignore-last-opened
if [ -n "$BASE_PATH" ]; then
    set -- "$@" --abs-proxy-base-path "$BASE_PATH"
fi

exec code-server "$@" "$HOME/project"
