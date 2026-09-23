# Configuration

Related: [architecture](architecture.md), [development](development.md).

## Server (`server/.env`)

Read once at startup by `app/core/config.py` (pydantic-settings). Names are case-insensitive; anything not set uses the
default below. Copy `server/.env.example` to start, and restart the server after editing. Never commit `.env`.

| Variable | Default | Purpose |
|---|---|---|
| `AUTH_SECRET` | none, **required** | Signs the session cookie (JWT, HS256). Login returns `500 configuration_error` without it. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `SESSION_TTL_MINUTES` | `480` | How long a login lasts |
| `ENVIRONMENT` | `development` | `development`, `test` or `production`; in `production` the cookie is `Secure` (HTTPS only) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON list of allowed browser origins (the proxy makes this rarely matter) |
| `DATA_DIR` | `data` | Root for `onboarding.db`, `chroma/` and `docs/`, relative to where the server is started |
| `LLM_PROVIDER` | `fake` | `fake`, `gemini`, `groq` or `openrouter`: answers, review judgement, and the agent's tool choice |
| `EMBEDDING_PROVIDER` | `fake` | `fake` or `gemini` |
| `CAPTION_PROVIDER` | `fake` | `fake` or `gemini` (image captions at ingestion) |
| `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY` | empty | Needed only by the matching provider; a blank value counts as missing |
| `MAX_UPLOAD_BYTES` | `10485760` (10 MB) | Largest accepted upload |
| `CHUNK_MAX_TOKENS` / `CHUNK_OVERLAP_TOKENS` | `500` / `50` | Chunk size and overlap. Changing either re-indexes a file on its next upload |
| `MIN_IMAGE_DIMENSION_PX` | `32` | Images smaller than this on their shortest side are skipped (icons, spacers) |
| `MAX_IMAGES_PER_DOCUMENT` | `20` | Cap on images captioned per file |
| `RETRIEVAL_TOP_K` | `4` | Chunks given to the model per question |
| `LINT_DIR` | `server/lint` | Folder of the ESLint helper (must have `node_modules` installed) |
| `NODE_BINARY` | `node` | Node.js executable used to run the helper |
| `LINT_TIMEOUT_SECONDS` | `20` | Longest a single lint may take before `502 linter_failed` |

Real provider adapters are not implemented yet, so today only `fake` works for the three provider settings (see
[architecture](architecture.md#model-providers-current-status)).

## Client (`client/.env.local`)

| Variable | Default | Purpose |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8000` | Where the Next.js proxy forwards `/api/backend/*`. Server-side only |

Never put API keys in the client, and never prefix a secret with `NEXT_PUBLIC_` (those are shipped to the browser).
Restart `npm run dev` after editing.

## ESLint helper (`server/lint/`)

Its rules are in `server/lint/lint-snippet.mjs`, and its package versions are pinned in `server/lint/package.json`
(kept in line with the client's ESLint setup). Install with `npm install` (or `npm ci`) in that folder.
