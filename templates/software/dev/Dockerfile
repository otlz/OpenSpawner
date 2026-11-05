# VS Code (code-server) for coding with AI agents: Next.js, PHP and Python.
# Preinstalled agents: GitHub Copilot (bundled in code-server), Claude Code,
# Codex and OpenCode, each as CLI and as VS Code extension.
# Students sign in with their own accounts; nothing is baked into the image.
ARG CODE_SERVER_VERSION=4.144.0
ARG NODE_VERSION=24

FROM node:${NODE_VERSION}-trixie-slim AS node

FROM codercom/code-server:${CODE_SERVER_VERSION}

USER root
ENV DEBIAN_FRONTEND=noninteractive

# Node.js LTS from the official image (Debian's nodejs is too old for current
# Next.js and the agent CLIs)
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && node --version && npm --version

# Python, PHP (with Composer) and the tools agents expect (ripgrep, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip python-is-python3 \
      php-cli php-mbstring php-xml php-curl php-sqlite3 php-mysql php-zip php-intl composer \
      build-essential ripgrep sqlite3 unzip procps less \
    && rm -rf /var/lib/apt/lists/*

# GitHub CLI from GitHub's signed repository (Debian ships a much older gh).
# Git comes with the base image. The hash pins the signing key published in
# cli/cli docs/install_linux.md. No version pin: the repository only keeps the
# latest release.
ARG GH_KEYRING_SHA256=6084d5d7bd8e288441e0e94fc6275570895da18e6751f70f057485dc2d1a811b
RUN curl -fsSL -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
      https://cli.github.com/packages/githubcli-archive-keyring.gpg \
 && echo "${GH_KEYRING_SHA256}  /usr/share/keyrings/githubcli-archive-keyring.gpg" | sha256sum -c - \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list \
 && apt-get update && apt-get install -y --no-install-recommends gh \
 && rm -rf /var/lib/apt/lists/* \
 && git --version && gh --version

# Agent CLIs, installed system-wide so they survive the home volume and are
# updated by rebuilding the image (students cannot write to /usr/local)
ARG CLAUDE_CODE_VERSION=2.1.314
ARG CODEX_VERSION=0.166.0
ARG OPENCODE_VERSION=1.19.5
ARG COPILOT_CLI_VERSION=1.0.105
RUN npm install -g \
      @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} \
      @openai/codex@${CODEX_VERSION} \
      opencode-ai@${OPENCODE_VERSION} \
      @github/copilot@${COPILOT_CLI_VERSION} \
    && npm cache clean --force \
    && claude --version && codex --version && opencode --version && copilot --version

# Self-updates would fail anyway (read-only /usr/local for students).
# pip installs into ~/.local (persisted) instead of failing with PEP 668.
ENV DISABLE_AUTOUPDATER=1 \
    OPENCODE_DISABLE_AUTOUPDATE=true \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PATH=/home/coder/.local/bin:$PATH

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

# Extensions and defaults land in /home/coder, which the spawner mounts as a
# named volume. Docker copies this content into the volume on first start.
USER coder
RUN for ext in \
      Anthropic.claude-code \
      openai.chatgpt \
      sst-dev.opencode \
      ms-python.python \
      bmewburn.vscode-intelephense-client \
      dbaeumer.vscode-eslint \
      esbenp.prettier-vscode \
      bradlc.vscode-tailwindcss; do \
      code-server --install-extension "$ext" || exit 1; \
    done \
 && rm -rf /home/coder/.cache /home/coder/.local/share/code-server/CachedExtensionVSIXs

COPY --chown=coder:coder settings.json /home/coder/.local/share/code-server/User/settings.json
COPY --chown=coder:coder codex-config.toml /home/coder/.codex/config.toml
COPY --chown=coder:coder LIESMICH.md /home/coder/project/LIESMICH.md

WORKDIR /home/coder/project
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
