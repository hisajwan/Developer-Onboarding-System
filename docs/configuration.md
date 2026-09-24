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
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Text model for answers, review judgement, the agent's tool choice and image captions. Must support function calling and image input |
| `GEMINI_FALLBACK_MODEL` | `gemini-3.1-flash-lite` | Tried once when the main model is rate-limited (its own free quota). Empty disables it |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Embedding model. Changing it starts a new, empty index (re-upload documents) |
| `GEMINI_EMBEDDING_TOKENS_PER_MINUTE` | `30000` | Embedding requests are grouped and paced under this limit |
| `GEMINI_TIMEOUT_SECONDS` | `60` | Per-request timeout |
| `GEMINI_MAX_RETRIES` | `1` | Attempts per request before giving up (or moving to the fallback model) |
| `MAX_UPLOAD_BYTES` | `10485760` (10 MB) | Largest accepted upload |
| `CHUNK_MAX_TOKENS` / `CHUNK_OVERLAP_TOKENS` | `500` / `50` | Chunk size and overlap. Changing either re-indexes a file on its next upload |
| `MIN_IMAGE_DIMENSION_PX` | `100` | Images smaller than this on their shortest side are skipped (icons, avatars, spacers) |
| `MAX_IMAGES_PER_DOCUMENT` | `20` | Cap on images captioned per file |
| `RETRIEVAL_TOP_K` | `4` | Chunks given to the model per question |
| `LINT_DIR` | `server/lint` | Folder of the ESLint helper (must have `node_modules` installed) |
| `NODE_BINARY` | `node` | Node.js executable used to run the helper |
| `LINT_TIMEOUT_SECONDS` | `20` | Longest a single lint may take before `502 linter_failed` |

`gemini` is implemented for all three provider settings; `groq` and `openrouter` are not yet (see
[architecture](architecture.md#model-providers-current-status)). Check which models your key can use, and their free
limits, at https://aistudio.google.com/rate-limit; model IDs change over time, so set them here rather than in code.
Free-tier Gemini inputs may be used by Google to improve its products, so upload only non-confidential documents.

## Client (`client/.env.local`)

| Variable | Default | Purpose |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8000` | Where the Next.js proxy forwards `/api/backend/*`. Server-side only |

Never put API keys in the client, and never prefix a secret with `NEXT_PUBLIC_` (those are shipped to the browser).
Restart `npm run dev` after editing.

## ESLint helper (`server/lint/`)

Its rules are in `server/lint/lint-snippet.mjs`, and its package versions are pinned in `server/lint/package.json`
(kept in line with the client's ESLint setup). Install with `npm install` (or `npm ci`) in that folder.
