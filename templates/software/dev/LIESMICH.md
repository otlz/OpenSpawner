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
  basePath: process.env.NODE_ENV === "development" ? `${process.env.PREVIEW_BASE ?? ""}/3000` : "",
};
```

## Auf GitHub veröffentlichen

Einmalig anmelden. Wähle `GitHub.com`, `HTTPS` und `Login with a web browser`, dann gibst du den angezeigten Code auf der Webseite ein:

```bash
gh auth login
git config --global user.name "Dein Name"
git config --global user.email "deine-noreply-adresse@users.noreply.github.com"
```

Die `noreply`-Adresse findest du bei GitHub unter Settings, Emails. So bleibt deine echte Adresse privat.

Dann im Projektordner:

```bash
git init -b main
git add .
git commit -m "Erste Version"
gh repo create meine-app --private --source=. --push
```

Danach reichen `git add .`, `git commit -m "..."` und `git push`.

Prüfe vor dem ersten Commit deine `.gitignore`: `node_modules` und `.env` gehören nicht ins Repository. Passwörter und API-Schlüssel haben dort nichts verloren, auch nicht in einem privaten Repository.

Deine GitHub-Anmeldung liegt unverschlüsselt in deinem Container. Auch KI-Agenten können sie benutzen, lies also genau, was ein Agent tun will, bevor du es erlaubst.

## Auf Cloudflare Pages veröffentlichen

Verbinde dein Repository im Cloudflare-Dashboard: neues Pages-Projekt anlegen, `Connect to Git` wählen und das Repository auswählen. Ab dann baut Cloudflare nach jedem `git push` automatisch eine neue Version. Du musst dich dafür im Container nicht bei Cloudflare anmelden, deine Zugangsdaten bleiben also draußen.

| Projekt | Build-Befehl | Ausgabeordner |
|---------|--------------|---------------|
| HTML, CSS, JavaScript | leer lassen | `/` |
| Next.js | `npm run build` | `out` |

Next.js braucht dafür in `next.config.ts` zusätzlich `output: "export"`.

Cloudflare Pages liefert statische Seiten aus. PHP- und Flask-Apps laufen dort nicht.
