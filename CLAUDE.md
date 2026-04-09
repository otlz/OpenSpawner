# CLAUDE.md

## Project Overview

**OpenSpawner** — Flask + Next.js service that auto-provisions isolated Docker containers per user. Each user gets a personal container with a unique URL route. Passwordless auth via magic links.

- **Backend:** Flask (Python 3.11+), SQLAlchemy, JWT Auth (HttpOnly Cookie), Docker SDK
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Shadcn/Radix UI
- **Infra:** Docker Compose (local dev + production), Traefik (reverse proxy, production only)

## Commands

### Local Dev (Docker Desktop — no Traefik needed)

```bash
docker compose up --build              # Start API (5000) + Frontend (3000)
docker compose --profile build build   # Build user template images
docker compose logs -f spawner         # Backend logs
docker compose logs -f frontend        # Frontend logs
curl http://localhost:5000/health      # Health check
```

### Production (with Traefik)

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f
```

### Backend Dev

```bash
python run.py                          # Dev server on port 5000
ruff check . && ruff format .          # Lint + format
mypy run.py config.py app/             # Type check
pytest                                 # Tests
```

### Frontend Dev

```bash
cd frontend
npm run dev                            # Dev server on port 3000
npm run build                          # Production build
npm run lint                           # ESLint
npx tsc --noEmit                       # Type check
```

### Docker Debug

```bash
docker ps | grep user-                 # Find user containers
docker logs user-<slug>-<id>           # User container logs
docker inspect user-<slug>-<id> | grep -A20 Labels  # Check Traefik labels
```

## Docker Setup (Dual Compose)

Two compose files for different environments:

| File | Purpose | Network | Traefik |
|------|---------|---------|---------|
| `docker-compose.yml` | **Local dev** (Docker Desktop) | `openspawner` (bridge) | `TRAEFIK_ENABLED=false` |
| `docker-compose.prod.yml` | **Production** | `web` (external, shared with Traefik) | `TRAEFIK_ENABLED=true` |

- **Local dev:** Direct port access — `localhost:3000` (frontend), `localhost:5000` (API)
- **Production:** Traefik routes via `Host + PathPrefix` labels. Priority: API (200) > Health (100) > Frontend (50)
- **Template builds:** Use `--profile build` to build user template images. They're not started as services — they're spawned per-user at runtime.

## Backend Structure

```
app/                          # Flask application package
├── __init__.py               # App factory (create_app)
├── extensions.py             # db, jwt, login_manager instances
├── models.py                 # SQLAlchemy models
├── decorators.py             # @admin_required, @verified_required
├── routes/
│   ├── auth.py               # Auth redirects (auth_bp)
│   ├── api.py                # Main API (api_bp, /api/*)
│   └── admin.py              # Admin API (admin_bp, /api/admin/*)
└── services/
    ├── container_manager.py  # Docker orchestration
    └── email_service.py      # Magic link emails
config.py                     # Configuration (root level)
run.py                        # Entry point
templates/                    # User container template images
```

## Architecture

```
# Local Dev:
Browser → localhost:3000 (Frontend) → localhost:5000 (API)

# Production:
Browser → Traefik → /api/*   → Spawner Backend (Flask)
                  → /        → Frontend (Next.js)
                  → /<slug>  → User Container (dynamic)
```

**Auth Flow (Passwordless):**
1. User enters email → backend sends magic link token (15 min expiry, one-time use)
2. User clicks link → token verified → JWT issued as **HttpOnly Cookie** (`spawner_token`)
3. User container spawns automatically, receives `JWT_SECRET` via env var
4. Container validates JWT cookie on every request (no token = 403)

**User states:** `registered` → `verified` → `active`

## Template System

Templates defined in `.env` as semicolon-separated list:
```
USER_TEMPLATE_IMAGES="user-template-01:latest;user-template-next:latest;user-template-vcoder:latest"
```

Type extraction: `user-template-01:latest` → type `template-01`
Metadata (display names, descriptions) in `templates.json`.

### Adding a New Template

1. Create `templates/user-template-xyz/Dockerfile` (must expose port **8080**)
2. Add to `.env`: append `;user-template-xyz:latest` to `USER_TEMPLATE_IMAGES`
3. Add metadata to `templates.json`
4. Build: `docker compose --profile build build`
5. Restart spawner: `docker compose restart spawner`

## Gotchas

- **Docker network:** After `containers.run()`, you MUST call `network.connect(container)` explicitly. The `network=` parameter in `containers.run()` does NOT work.
- **Traefik labels:** Router must reference its service explicitly: `traefik.http.routers.*.service=*`. Missing this breaks routing silently.
- **JWT storage:** Token is HttpOnly Cookie, NOT localStorage. Frontend cannot read it directly — it's sent automatically with requests.
- **Container auth:** Each user container validates JWT independently. `JWT_SECRET` is passed from spawner via environment variable.
- **Rate limiting:** Max 3 magic links per email per hour.
- **Container cleanup:** Old containers with same `user_id + type` are auto-deleted before spawning new ones.
- **Unprivileged containers:** All user containers run on port 8080 (not 80).

## Conventions

- **Language:** German for UI text and user-facing messages. English for code, variable names, comments.
- **API errors:** Always `{'error': 'message'}, status_code`
- **Logging:** Prefix container operations with `[SPAWNER]`, use `current_app.logger`
- **Config:** All env vars documented in `.env.example` — that's the source of truth
- **Frontend imports:** Use `@/` path alias (`@/components/ui/button`)
- **Styling:** Tailwind CSS + `cn()` helper for conditional classes
