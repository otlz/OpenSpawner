FROM nginxinc/nginx-unprivileged:alpine

# Wechsel zu root um Pakete zu installieren
USER root

# gettext für envsubst installieren
RUN apk add --no-cache gettext

# HTML-Template kopieren
COPY index.html /usr/share/nginx/html/index.html.template

# Nginx-Konfiguration kopieren
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Entrypoint Script kopieren und executable machen
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && \
    chmod 777 /usr/share/nginx/html

EXPOSE 8080

# Entrypoint Script starten (läuft als root, startet Nginx)
ENTRYPOINT ["/entrypoint.sh"]