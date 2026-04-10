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

# Install setuptools (provides distutils, removed in Python 3.12+)
# and pre-install PlatformIO Core for faster first launch
RUN pip install --break-system-packages setuptools platformio

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

# Prepare code-server data directories
RUN mkdir -p /home/coder/.local/share/code-server/extensions \
             /home/coder/.local/share/code-server/User \
 && chown -R coder:coder /home/coder/.local/share/code-server \
    /home/coder/.platformio 2>/dev/null || true

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

# Cleanup
USER root
RUN rm -f /tmp/platformio.vsix /tmp/cpptools.vsix

# Configure PlatformIO to use system Python (not built-in)
RUN printf '{\n\
    "platformio-ide.useBuiltinPython": false,\n\
    "platformio-ide.useBuiltinPIOCore": false\n\
}\n' > /home/coder/.local/share/code-server/User/settings.json

USER coder

WORKDIR /home/coder/project

EXPOSE 8080

CMD ["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none"]
