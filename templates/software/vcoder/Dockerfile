# Web IDE with PlatformIO for ESP8266 development
# Based on code-server with clangd and PlatformIO extensions
FROM codercom/code-server:latest

USER root
ENV DEBIAN_FRONTEND=noninteractive

# Install system packages (Python 3, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-dev python3-pip \
      curl ca-certificates unzip net-tools clangd socat \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/bin/python

# Install setuptools (distutils, removed in Python 3.12+) and PlatformIO Core
# system-wide so any Python can `import platformio` during extension checks.
RUN pip install --break-system-packages setuptools platformio

# Verify the modules the PlatformIO extension checks at runtime
RUN python3 -c "import ensurepip; import venv; import platformio; print('Python module check OK')"

# Download PlatformIO IDE VSIX (not on Open VSX registry)
ARG PIO_VER=3.3.4
RUN curl -fsSL -o /tmp/platformio.vsix \
      "https://github.com/platformio/platformio-vscode-ide/releases/download/v${PIO_VER}/platformio-ide-${PIO_VER}.vsix" \
 && unzip -t /tmp/platformio.vsix >/dev/null

# Download cpptools v1.24.4 (last version compatible with code-server)
# Required as a dependency by PlatformIO IDE
ARG CPPTOOLS_VER=1.24.4
ARG CPPTOOLS_ARCH=linux-x64
RUN curl -fsSL -o /tmp/cpptools.vsix \
      "https://github.com/microsoft/vscode-cpptools/releases/download/v${CPPTOOLS_VER}/cpptools-${CPPTOOLS_ARCH}.vsix" \
 && unzip -t /tmp/cpptools.vsix >/dev/null

# Prepare code-server data directories and .platformio with correct ownership
# (Docker copies these permissions into new named volumes on first mount)
RUN mkdir -p /home/coder/.local/share/code-server/extensions \
             /home/coder/.local/share/code-server/User \
             /home/coder/.platformio \
 && chown -R coder:coder /home/coder/.local/share/code-server \
                         /home/coder/.platformio

# Install extensions as user "coder"
USER coder
RUN code-server --install-extension /tmp/cpptools.vsix \
      --extensions-dir /home/coder/.local/share/code-server/extensions \
 && code-server --install-extension /tmp/platformio.vsix \
      --extensions-dir /home/coder/.local/share/code-server/extensions \
 && code-server --install-extension llvm-vs-code-extensions.vscode-clangd \
      --extensions-dir /home/coder/.local/share/code-server/extensions \
 && code-server --install-extension ms-python.python \
      --extensions-dir /home/coder/.local/share/code-server/extensions

# Pre-install PlatformIO Core into penv at build time.
# Docker copies this into new named volumes on first mount, so
# containers start instantly without runtime installation.
RUN mkdir -p /home/coder/.platformio/python3/bin \
             /home/coder/.platformio/.cache/tmp \
 && ln -sf /usr/bin/python3 /home/coder/.platformio/python3/bin/python3 \
 && python3 -m venv /home/coder/.platformio/penv \
 && /home/coder/.platformio/penv/bin/pip install -U platformio \
 && /home/coder/.platformio/penv/bin/python -c "\
import json, platform, time; \
open('/home/coder/.platformio/penv/state.json','w').write(json.dumps({ \
  'created_on': int(time.time()), \
  'python': {'path':'/home/coder/.platformio/penv/bin/python','version':platform.python_version()}, \
  'installer_version':'1.2.2', \
  'platform':{'platform':platform.platform(),'release':platform.release()} \
}))" \
 && /home/coder/.platformio/penv/bin/platformio --version

# Cleanup and entrypoint setup
USER root
RUN rm -f /tmp/platformio.vsix /tmp/cpptools.vsix
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Use default PlatformIO settings (useBuiltinPIOCore: true, useBuiltinPython: true).
# The entrypoint symlinks system Python into ~/.platformio/python3/bin/ where
# the extension checks first, and pre-installs PlatformIO Core into ~/.platformio/penv/.
RUN printf '{}\n' > /home/coder/.local/share/code-server/User/settings.json

# Start as root so entrypoint can fix volume ownership, then drops to coder
USER root

WORKDIR /home/coder/project

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
