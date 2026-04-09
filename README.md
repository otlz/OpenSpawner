# OpenSpawner

A Flask + Next.js application that automatically provisions isolated Docker containers per user. Each user gets their own container with a personalized URL, managed through a web dashboard.

## What It Does

- Users register via passwordless magic link authentication
- Each user can launch one or more Docker containers from pre-built templates
- Containers are automatically routed and accessible via the web
- Admins can manage users, block/unblock accounts, and monitor containers

## Quick Start (Docker Desktop)

```bash
git clone https://github.com/YOUR_USERNAME/OpenSpawner.git
cd OpenSpawner
cp .env.example .env
docker compose --profile build build   # build user container templates
docker compose up --build              # start the application
```

Then open [http://localhost:3000](http://localhost:3000).

> The first user to register automatically becomes an admin.

> **Note:** Magic link emails require SMTP configuration. For local development without email, check the backend logs (`docker compose logs spawner`) to find the magic link URL.

## Architecture

```
Browser
  |
  +---> Frontend (Next.js)     :3000
  |       |
  |       +---> /api/* proxy
  |               |
  +---> Backend (Flask API)    :5000
          |
          +---> Docker Engine
                  |
                  +---> User Container A  :random-port
                  +---> User Container B  :random-port
                  +---> ...
```

**Tech Stack:**
- **Backend:** Flask, SQLAlchemy, JWT Auth, Docker SDK
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, Radix UI
- **Database:** SQLite (default), PostgreSQL (production)
- **Auth:** Passwordless magic links + JWT tokens

## Configuration

All settings are in `.env` (copy from `.env.example`). Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-...` | Flask secret key (change in production!) |
| `BASE_DOMAIN` | `localhost` | Your domain |
| `TRAEFIK_ENABLED` | `false` | Enable Traefik reverse proxy mode |
| `USER_TEMPLATE_IMAGES` | all templates | Semicolon-separated list of templates to build |
| `DEFAULT_MEMORY_LIMIT` | `512m` | RAM limit per user container |
| `DEFAULT_CPU_QUOTA` | `50000` | CPU quota (50000 = 0.5 CPU) |

See [.env.example](.env.example) for all options.

## User Templates

OpenSpawner ships with pre-built container templates:

| Template | Description |
|----------|-------------|
| `user-template-01` | Nginx Basic - simple static site |
| `user-template-02` | Nginx Advanced |
| `user-template-next` | Next.js React application |
| `user-template-dictionary` | Python Flask dictionary app |
| `user-template-vcoder` | Web IDE with PlatformIO for ESP8266 |

### Adding a Custom Template

1. Create a directory `user-template-myname/` with a `Dockerfile` (must expose port 8080)
2. Add the image to `USER_TEMPLATE_IMAGES` in `.env`
3. Add metadata to `templates.json`
4. Rebuild: `docker compose up --build`

## Production Deployment (with Traefik)

For production with HTTPS and domain-based routing:

```bash
# Set up your .env for production
BASE_DOMAIN=yourdomain.com
SPAWNER_SUBDOMAIN=coder
TRAEFIK_ENABLED=true
TRAEFIK_NETWORK=web

# Use the production compose file
docker compose -f docker-compose.prod.yml up -d --build
```

This requires a running [Traefik](https://traefik.io/) instance with Docker provider enabled.

## Development

```bash
# Backend (Flask)
pip install -r requirements.txt
python app.py

# Frontend (Next.js)
cd frontend
npm install
npm run dev

# Linting
ruff check .          # Backend
cd frontend && npm run lint  # Frontend
```

## API Documentation

When running, Swagger UI is available at [http://localhost:5000/swagger](http://localhost:5000/swagger).

## License

MIT License - see [LICENSE](LICENSE) for details.
