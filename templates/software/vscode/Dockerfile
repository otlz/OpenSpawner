# Clean VS Code (code-server) — no pre-installed extensions
# Pinned: `latest` stays cached on the build host and silently keeps old versions
ARG CODE_SERVER_VERSION=4.144.0
FROM codercom/code-server:${CODE_SERVER_VERSION}

# GitHub CLI from GitHub's signed repository (Debian ships a much older gh).
# Git comes with the base image. Students cannot add tools themselves:
# no-new-privileges blocks sudo. The hash pins the signing key published in
# cli/cli docs/install_linux.md. No version pin: the repository only keeps the
# latest release.
USER root
ARG GH_KEYRING_SHA256=6084d5d7bd8e288441e0e94fc6275570895da18e6751f70f057485dc2d1a811b
RUN curl -fsSL -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
      https://cli.github.com/packages/githubcli-archive-keyring.gpg \
 && echo "${GH_KEYRING_SHA256}  /usr/share/keyrings/githubcli-archive-keyring.gpg" | sha256sum -c - \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list \
 && apt-get update && apt-get install -y --no-install-recommends gh \
 && rm -rf /var/lib/apt/lists/* \
 && git --version && gh --version

USER coder

# ~/.config is a volume (templates.json), so the gh login and the git identity
# survive a recreated container. Creating it here gives the volume the right
# owner; the empty file makes `git config --global` write here, not ~/.gitconfig.
RUN mkdir -p /home/coder/.config/git && touch /home/coder/.config/git/config

WORKDIR /home/coder/project

EXPOSE 8080

CMD ["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none", "--ignore-last-opened", "/home/coder/project"]
