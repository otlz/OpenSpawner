#!/bin/sh
set -e

# Umgebungsvariablen in die HTML-Datei einfügen
envsubst < /usr/share/nginx/html/index.html.template > /usr/share/nginx/html/index.html

# Nginx starten
exec nginx -g "daemon off;"
