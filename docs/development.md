# Development

Related: [architecture](architecture.md), [configuration](configuration.md).

## Repository layout

```
server/
  app/
    api/             routes/, deps.py (auth + ownership dependencies), container.py (picks concrete adapters)
    services/        business flows: auth, profile, projects, chat sessions, chat, ingestion, code review
    agent/           LangChain agent and its tools (tools/)
    domain/          models.py (dataclasses) and ports/ (Protocol interfaces)
    infrastructure/  adapters: storage/ (SQLite, disk), vectorstore/ (Chroma), embeddings/, llm/, chat_models/,
                     captioning/, documents/ (file readers), linting/ (ESLint helper), auth/ (JWT, bcrypt)
    ingestion/       chunker, chunk ids, filename rules
    schemas/         request/response models
    core/            settings, errors
  lint/              Node ESLint helper for code review
  scripts/           create_user.py
  tests/
client/src/
  app/               routes: login, signup, and (app)/ with dashboard, ask, code-review, account + layout providers
  components/        atoms/, molecules/, organisms/, templates/
  hooks/             feature hooks (chat, code review, profile, login, signup, logout)
  lib/api/           one function per endpoint, all through http.ts
  config/            navigation, labels and other static lists
  types/             shared types
  mocks/             sample data for screens not wired yet (Dashboard)
  proxy.ts           redirects to /login when there is no session cookie
docs/                this documentation
```

## Adding code

- **Backend:** services import ports (`app.domain.ports`), never adapters or SDKs. A new external system gets a port
  plus an adapter, wired in `api/container.py`. A new provider is an adapter plus one line in its `registry.py`. A new
  agent tool implements the `Tool` port and is added in `Container.tool_registry_for`. Routes stay thin; anything
  project-scoped goes under `/projects/{project_id}` and takes `OwnedProjectDep` / `OwnedSessionDep`. Errors are
  `AppError` subclasses in `core/exceptions.py`.
- **Frontend:** lower component levels never import higher ones; components are presentational and get data through
  props; fetching lives in hooks and `lib/api/`. Colours come from the tokens in `app/globals.css`. Current project,
  documents and chat session come from the providers in `app/(app)/`, not from new fetches.
- This Next.js version has breaking changes from older releases; check `client/node_modules/next/dist/docs/` before
  using an unfamiliar API.

## Tests

```bash
cd server && pytest && ruff check .
cd client && npm run lint && npm run typecheck && npm run build
```

- Server tests never touch the network or a real API key: they run on the `fake` providers, plain-class fakes of the
  ports (`tests/helpers.py`), and a temporary data folder per test (`tests/conftest.py`).
- Tests that run the real ESLint helper are marked `requires_linter` and are skipped if `server/lint/node_modules` is
  missing.
- Route tests use `TestClient(create_app(settings))`; `conftest.py` has fixtures for a logged-in client, a seeded
  project and a seeded chat session.
- The client has no automated tests yet; lint, type checking and a production build are its checks.

## CI

`.github/workflows/ci.yml` runs on pushes to `main` and `dev` and on pull requests to `main`:

- **Server:** Python 3.12, `pip install -r requirements-dev.txt`, Node 22 + `npm ci` in `server/lint`, `ruff check .`,
  `pytest`.
- **Client:** Node 22, `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`.

No secrets are used in CI.

## Branches

Work happens on `dev`. `main` is protected: it changes only through a pull request from `dev` with both CI checks green,
opened once a feature set is complete and verified.
