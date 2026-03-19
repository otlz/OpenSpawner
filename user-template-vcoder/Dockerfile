# ./user-template-vcoder/Dockerfile
# Basiert auf backlog/vcoder/ide/Dockerfile mit Anpassungen für Spawner-Integration
FROM codercom/code-server:latest

# Systempakete (Python 3 + venv) und Tools für VSIX
USER root
ENV DEBIAN_FRONTEND=noninteractiv
ENV PATH="/home/coder/.platformio/penv/bin:${PATH}"

RUN echo "deb http://ftp.de.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    echo "deb http://ftp.de.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-distutils python3-dev python3.11-dev \
      curl ca-certificates unzip net-tools clang \
    && rm -rf /var/lib/apt/lists/*

# Symbolischer Link für python3-config
RUN ln -sf /usr/bin/python3.11-config /usr/bin/python3-config

RUN python3 -m venv /home/coder/.platformio/penv
RUN [ -f /home/coder/.platformio/penv/bin/python ] || ln -sf /home/coder/.platformio/penv/bin/python3 /home/coder/.platformio/penv/bin/python
RUN apt-get update && apt-get install -y clangd

# Versionen/Architektur
ARG CPDTOOLS_VER=1.29.0
ARG CPDTOOLS_ARCH=linux-x64
ARG PIO_VER=3.3.4

# Microsoft C/C++ (cpptools) VSIX laden und prüfen
RUN curl -fsSL -o /tmp/cpptools.vsix \
      "https://github.com/microsoft/vscode-cpptools/releases/download/v${CPDTOOLS_VER}/cpptools-${CPDTOOLS_ARCH}.vsix" \
 && unzip -t /tmp/cpptools.vsix >/dev/null

# PlatformIO IDE VSIX laden und prüfen
RUN curl -fsSL -o /tmp/platformio.vsix \
      "https://github.com/platformio/platformio-vscode-ide/releases/download/v${PIO_VER}/platformio-ide-${PIO_VER}.vsix" \
 && unzip -t /tmp/platformio.vsix >/dev/null

# code-server Datenverzeichnis und User-Settings vorbereiten
RUN mkdir -p /home/coder/.local/share/code-server/extensions \
             /home/coder/.local/share/code-server/User \
 && chown -R coder:coder /home/coder/.local/share/code-server

# Extensions als Nutzer "coder" installieren (VSIX + Registry)
USER coder
RUN code-server --install-extension /tmp/cpptools.vsix \
      --extensions-dir /home/coder/.local/share/code-server/extensions \
 && code-server --install-extension /tmp/platformio.vsix \
      --extensions-dir /home/coder/.local/share/code-server/extensions \
 && code-server --install-extension llvm-vs-code-extensions.vscode-clangd \
      --extensions-dir /home/coder/.local/share/code-server/extensions

# Aufräumen temporärer Dateien
USER root
RUN rm -f /tmp/cpptools.vsix /tmp/platformio.vsix

# socat für Port-Tunneling installieren (PIO Home reverse proxy)
RUN apt-get update && apt-get install -y socat nginx && rm -rf /var/lib/apt/lists/*

# nginx als Reverse Proxy für code-server (fixiert Subpath-Routing)
RUN printf 'server {\n\
    listen 8080;\n\
    server_name localhost;\n\
    location / {\n\
        proxy_pass http://localhost:8081;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade $http_upgrade;\n\
        proxy_set_header Connection "upgrade";\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n\
        proxy_set_header X-Forwarded-Proto $scheme;\n\
    }\n\
}\n' > /etc/nginx/sites-available/default && rm -f /etc/nginx/sites-enabled/default

# Entrypoint-Script - startet nginx + socat + code-server
RUN printf '#!/bin/bash\n\
socat TCP-LISTEN:8008,reuseaddr,fork TCP:localhost:9009 &\n\
nginx -g "daemon off;" &\n\
exec "$@"\n' > /entrypoint.sh && chmod +x /entrypoint.sh

USER coder

WORKDIR /home/coder/project

ENTRYPOINT ["/entrypoint.sh"]
CMD ["code-server", "--bind-addr", "127.0.0.1:8081", "--auth", "none"]
