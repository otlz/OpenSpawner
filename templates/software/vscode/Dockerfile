# Clean VS Code (code-server) — no pre-installed extensions
FROM codercom/code-server:latest

USER coder

WORKDIR /home/coder/project

EXPOSE 8080

CMD ["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none", "--ignore-last-opened", "/home/coder/project"]
