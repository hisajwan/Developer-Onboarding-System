# Onboarding Platform

AI-powered developer onboarding assistant. Monorepo with a FastAPI backend and a Next.js frontend.

```
server/   FastAPI. api -> services -> domain ports <- infrastructure
client/   Next.js + Tailwind. atoms -> molecules -> organisms -> templates -> pages
```

## Run it

Requires Node 20+ and Python 3.11+.

Backend (terminal 1):

```bash
cd server
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # then set your own AUTH_PASSWORD and AUTH_SECRET (login); API keys stay server-only
uvicorn app.main:app --reload --port 8000
```

Frontend (terminal 2):

```bash
cd client
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000. Health check: http://localhost:8000/api/v1/health.

## Checks

```bash
cd server && pytest && ruff check .
cd client && npm run lint && npm run typecheck && npm run build
```

The same checks run in CI on every push to `main` and `dev` (`.github/workflows/ci.yml`).
