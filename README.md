# Onboarding Platform

AI-powered developer onboarding assistant. Monorepo with a FastAPI backend and a Next.js frontend.

```
server/        FastAPI. api -> services -> domain ports <- infrastructure
server/lint/   small Node helper that lints a pasted snippet with ESLint (used by code review)
client/        Next.js + Tailwind. atoms -> molecules -> organisms -> templates -> pages
```

## Features

- **Accounts**: sign up, log in, edit your name and change your password on the Account page.
- **Projects**: each user has their own projects. A project's documents and answers never mix with another project's.
- **Project docs**: upload Markdown, text, PDF or image files per project; they are chunked, embedded and indexed
  (images and PDF diagrams are captioned first). Re-uploading an unchanged file is skipped; files can be deleted.
- **Ask**: chat about the project's docs, with the source files cited. Each project can have several chat sessions;
  they share the project's docs but keep separate history. Pasting code into the chat routes it to code review.
- **Code review**: paste a React / TypeScript / JavaScript snippet and get categorised feedback (accessibility, test,
  style) from ESLint plus the model's judgement.
- **Dashboard**: usage overview (sample data for now).

## Run it

Requires Python 3.11+ and Node 20+.

Backend (terminal 1):

```bash
cd server
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
(cd lint && npm install)      # ESLint helper for code review
cp .env.example .env          # then set AUTH_SECRET (signs the login cookie); see the comments in the file
uvicorn app.main:app --reload --port 8000
```

Frontend (terminal 2):

```bash
cd client
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000 and sign up. API docs: http://localhost:8000/docs. Health check:
http://localhost:8000/api/v1/health.

To create an account or reset a password from the command line instead (there is no password reset in the app), run
`python scripts/create_user.py` from `server/` with the venv active.

### Model providers

By default every provider is `fake` (`LLM_PROVIDER`, `EMBEDDING_PROVIDER`, `CAPTION_PROVIDER` in `server/.env`): no API
keys and no network. Answers and captions are placeholders, and code review shows ESLint results only. To use real models,
set a provider (`gemini`, `groq` or `openrouter` for the LLM; `gemini` for embeddings and captions) and its API key in
`server/.env`. Keys stay on the server; never put them in `client/`.

## API

All routes are under `/api/v1`. Everything except health and the auth routes needs the login cookie; a project or
session you don't own returns 404.

| Area | Routes |
|---|---|
| Auth | `POST /signup`, `POST /login`, `POST /logout`, `GET /session` |
| Profile | `GET /me`, `PATCH /me`, `POST /me/change-password` |
| Projects | `GET /projects`, `POST /projects`, `PATCH /projects/{id}`, `POST /projects/{id}/select` |
| Documents | `GET /projects/{id}/documents`, `POST /projects/{id}/documents`, `DELETE /projects/{id}/documents/{filename}` |
| Chat sessions | `GET /projects/{id}/sessions`, `POST /projects/{id}/sessions` |
| Chat | `POST /projects/{id}/sessions/{session_id}/chat`, `GET /projects/{id}/sessions/{session_id}/chat/history` |
| Code review | `POST /projects/{id}/reviews` |

## Checks

```bash
cd server && pytest && ruff check .
cd client && npm run lint && npm run typecheck && npm run build
```

The ESLint tests are skipped if `server/lint` has not been installed. The same checks run in CI on every push to `main`
and `dev` (`.github/workflows/ci.yml`).
