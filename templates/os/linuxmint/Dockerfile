# Linux Desktop (Ubuntu XFCE) in the browser via KasmVNC
FROM lscr.io/linuxserver/webtop:ubuntu-xfce

# Remap KasmVNC web port to 8080 (spawner expects this)
ENV CUSTOM_PORT=8080

# Run as unprivileged user
ENV PUID=1000
ENV PGID=1000

EXPOSE 8080
