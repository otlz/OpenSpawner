# LibreOffice (Writer, Calc, Impress) in the browser via KasmVNC
FROM linuxserver/libreoffice:latest

# Remap KasmVNC web port to 8080 (spawner expects this)
ENV CUSTOM_PORT=8080

# Run as unprivileged user
ENV PUID=1000
ENV PGID=1000

EXPOSE 8080
