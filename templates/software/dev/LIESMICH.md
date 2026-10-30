# Willkommen in deiner Coding-Umgebung

Alles in `/home/coder` bleibt gespeichert, auch wenn der Container gestoppt wird.

## KI-Agenten

Melde dich mit **deinem eigenen** Konto an. Die Anmeldung gilt nur für deinen Container.

| Agent | Terminal | Anmeldung |
|-------|----------|-----------|
| GitHub Copilot | `copilot` | Konto-Symbol unten links in VS Code, im Terminal `/login` |
| Claude Code | `claude` | Link öffnen, Code zurück ins Terminal kopieren |
| Codex | `codex login --device-auth` | Gerätecode auf der angezeigten Seite eingeben |
| OpenCode | `opencode auth login` | Anbieter wählen (z. B. GitHub Copilot) |

Die Agenten gibt es auch als Erweiterung in der Seitenleiste.

## Vorschau deiner App

Starte den Entwicklungsserver im Terminal und öffne die Adresse dieses Fensters mit dem passenden Pfad:

| Projekt | Starten | Vorschau |
|---------|---------|----------|
| PHP | `php -S 0.0.0.0:8000` | `…/proxy/8000/` |
| Python (Flask) | `flask run --host 0.0.0.0 --port 5000` | `…/proxy/5000/` |
| Next.js | `npm run dev` | `…/absproxy/3000/` |

Für Next.js braucht `next.config.ts` einmalig diesen Eintrag:

```ts
const nextConfig = {
  basePath: `${process.env.PREVIEW_BASE ?? ""}/3000`,
};
```
