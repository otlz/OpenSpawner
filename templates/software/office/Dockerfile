# LibreOffice (Writer, Calc, Impress) in the browser via KasmVNC
FROM linuxserver/libreoffice:latest

# Remap KasmVNC web port to 8080 (spawner expects this)
ENV CUSTOM_PORT=8080

# Run as unprivileged user
ENV PUID=1000
ENV PGID=1000

# Clean up stale VNC/X11 lock files on container restart
# Without this, KasmVNC fails to bind after docker stop + start
RUN mkdir -p /custom-cont-init.d && \
    printf '#!/bin/bash\nrm -f /tmp/.X*-lock /tmp/.X11-unix/X* /run/lock/vnc-*\n' \
    > /custom-cont-init.d/cleanup-vnc.sh && \
    chmod +x /custom-cont-init.d/cleanup-vnc.sh

EXPOSE 8080
