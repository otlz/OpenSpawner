# OpenSpawner Landing Page

Standalone marketing site for OpenSpawner (Next.js, Tailwind CSS v4, shadcn/ui). It lives in this subfolder of the main repo but is deployed as a **separate Dokploy application** with its own domains. It has no dependency on the OpenSpawner backend and is not part of the docker-compose setup.

Canonical domain: `https://openspawner.de`. All other domains (`openspawner.com`, `.org`, `.net` and the `www.` variants) permanently redirect there via `next.config.ts`.

The only outbound link is the GitHub repository, defined in `src/lib/site.ts`. No environment variables are required.

## Local Development

```bash
npm install        # once, also generates package-lock.json
npm run dev        # http://localhost:3000
npm run lint       # ESLint
npx tsc --noEmit   # Type check
npm run build      # Production build (standalone output)
```

## Docker

Same Dockerfile and context that Dokploy uses:

```bash
docker build -t openspawner-landing -f landing/Dockerfile landing   # from repo root
docker run --rm -p 3000:3000 openspawner-landing
```

## Dokploy Deployment

Create a **new application** in Dokploy (separate from the OpenSpawner app), pointing at the same GitHub repo:

| Setting | Value |
|---|---|
| Provider | GitHub, repo `otlz/OpenSpawner`, branch `main` |
| Build Type | `Dockerfile` |
| Docker File | `landing/Dockerfile` |
| Docker Context Path | `landing` |
| Watch Paths | `landing/**` |
| Environment | none |

With Watch Paths set to `landing/**`, pushes that only touch the backend or frontend will not redeploy the landing page. Conversely, the existing OpenSpawner application should not watch `landing/**`.

### Domains

Add one domain entry per host, each with container port `3000`, HTTPS enabled and Let's Encrypt as certificate provider:

- `openspawner.de` (canonical)
- `www.openspawner.de`
- `openspawner.com` and `www.openspawner.com`
- `openspawner.org` and `www.openspawner.org`
- `openspawner.net` and `www.openspawner.net`

All hosts route to the same container; the app itself answers everything except `openspawner.de` with a permanent redirect (308) to the canonical domain. Every host still needs its own domain entry so Traefik obtains a certificate for it.

DNS prerequisite: A records for `@` and `www` of every zone must point to the server IP before Let's Encrypt can issue certificates.
