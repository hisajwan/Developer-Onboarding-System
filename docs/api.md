# API reference

Base path `/api/v1`. The browser reaches it through the Next.js proxy at `/api/backend/*`. Interactive docs (OpenAPI)
are served by the running server at http://localhost:8000/docs.

Related: [architecture](architecture.md), [database design](database.md).

## Conventions

- **Auth:** a successful signup or login sets an HttpOnly `session` cookie (signed JWT). Every route except `health`,
  `signup`, `login` and `logout` requires it; without a valid one the response is `401 not_authenticated`.
- **Ownership:** routes under `/projects/{id}` only work for the project's owner. Anyone else gets `404 not_found`, the
  same as for an id that doesn't exist.
- **Errors:** every error has the same body:

  ```json
  { "error": { "code": "not_found", "message": "Project not found." } }
  ```

  Request validation errors (wrong types, missing fields, length limits) are FastAPI's standard `422` body instead.
- **Times** are ISO 8601 in UTC.

| Status | `code` | When |
|---|---|---|
| 401 | `not_authenticated` | No session cookie, or it is invalid or expired |
| 401 | `invalid_credentials` | Wrong username/password, or wrong current password when changing it |
| 404 | `not_found` | Unknown or not-owned project, session or document |
| 409 | `account_already_exists` | Signup with a username or email already in use |
| 413 | `document_too_large` | Upload over `MAX_UPLOAD_BYTES` (10 MB default) |
| 422 | `invalid_document` | Unsupported, empty, unreadable or text-free file |
| 429 | `model_rate_limited` | The model provider's rate limit or daily quota was hit (after trying the fallback model and any `LLM_FALLBACK_PROVIDER`) |
| 500 | `configuration_error` | Server misconfigured: `AUTH_SECRET` missing, a provider key missing, lint helper not installed |
| 502 | `linter_failed` | The ESLint helper crashed, timed out or returned unreadable output |
| 502 | `model_provider_error` | The model provider failed: key rejected, unknown model, outage or invalid request |

## Health

`GET /health` → `200 {status: "ok", app, version, environment}`

## Auth

| Route | Body | Response |
|---|---|---|
| `POST /signup` | `{first_name, last_name, email, username, password}` | `201 {username, last_project_id}` + cookie |
| `POST /login` | `{username, password}` | `200 {username, last_project_id}` + cookie |
| `POST /logout` | | `204`, clears the cookie |
| `GET /session` | | `200 {username, last_project_id}` |

Signup rules: names 1 to 100 characters; `username` 3 to 50 characters of letters, digits, `_`, `.`, `-`; a valid-looking
`email`; `password` at least 8 characters. `last_project_id` is the project the user last selected (or `null`).

## Profile

| Route | Body | Response |
|---|---|---|
| `GET /me` | | `200 {username, first_name, last_name, email}` |
| `PATCH /me` | `{first_name, last_name}` | `200` the updated profile |
| `POST /me/change-password` | `{current_password, new_password}` | `204`; `401 invalid_credentials` if the current one is wrong |

Username and email cannot be changed. There is no password-reset endpoint; `server/scripts/create_user.py` resets one
from the command line.

## Projects

`Project` = `{id, name, created_at, updated_at}`

| Route | Body | Response |
|---|---|---|
| `GET /projects` | | `200 {projects: [Project]}`, the caller's own projects, newest first |
| `POST /projects` | `{name}` (1 to 200 chars) | `201 Project`; also creates the project's first chat session, "Session 1" (if that fails, the project is removed again and the error is returned) |
| `PATCH /projects/{id}` | `{name}` | `200 Project` |
| `POST /projects/{id}/select` | | `200 Project`; remembered as `last_project_id` for the next login |

## Documents

`Document` = `{filename, chunk_count, indexed_at}`

| Route | Body | Response |
|---|---|---|
| `POST /projects/{id}/documents` | multipart, field `file` | `200 {document: Document, status: "indexed" \| "unchanged", chunks_embedded}` |
| `GET /projects/{id}/documents` | | `200 {documents: [Document]}`, newest first |
| `DELETE /projects/{id}/documents/{filename}` | | `204`; removes the file, its chunks and its registry row |

Accepted files: `.md`, `.markdown`, `.txt`, `.pdf`, and images `.png`, `.jpg`, `.jpeg`, `.webp`. Images inside PDFs,
and standalone images at least `MIN_IMAGE_DIMENSION_PX` (100) on their shortest side, are captioned and indexed as text.
Uploading identical content again returns `status: "unchanged"` with `chunks_embedded: 0`; a changed file with the same
name replaces the old one, embedding only its new chunks.

## Chat sessions

`ChatSession` = `{id, name, created_at}`

| Route | Body | Response |
|---|---|---|
| `GET /projects/{id}/sessions` | | `200 {sessions: [ChatSession]}`, oldest first |
| `POST /projects/{id}/sessions` | `{name?}` (default "New session") | `201 ChatSession` |

## Chat

| Route | Body | Response |
|---|---|---|
| `POST /projects/{id}/sessions/{session_id}/chat` | `{message}` (1 to 8000 chars) | `200 {reply, sources: [filename], tools_used: [tool name], retrieved_sources: [filename]}` |
| `GET /projects/{id}/sessions/{session_id}/chat/history` | | `200 {messages: [{role: "user" \| "assistant", content, created_at, sources}]}`, the latest 50, oldest first |

The agent picks one tool per message: `retrieve_and_answer` (answers from the project's documents in Markdown;
`sources` lists only the files the answer used, and is empty when the documents don't cover the question;
`retrieved_sources` lists every file retrieval returned, cited or not) or `review_code` (a pasted snippet or diff; the
reply lists the review findings as text, `sources` is empty). Both the message and the reply are saved to the session,
and its latest 50 messages are sent to the agent as memory. Each message also counts on the dashboard: a question, or
a review when `review_code` was used.

## Code review

`POST /projects/{id}/reviews`

Request:

```json
{ "code": "function Card({ src }) {\n  return <img src={src} />;\n}", "language": "tsx" }
```

`code` is 1 to 20,000 characters; `language` is one of `tsx` (default), `ts`, `jsx`, `js`. If `code` is a unified
diff (a `diff --git` or `---`/`+++` header plus `@@` hunks), it is reviewed as one: each `.js`, `.jsx`, `.ts` or `.tsx`
file's hunks are linted, only findings on added or changed lines are kept, and other files are skipped with a note.

Response `200`:

```json
{
  "findings": [
    {
      "category": "accessibility",
      "message": "img elements must have an alt prop, either with meaningful text, or an empty string for decorative images.",
      "severity": "error",
      "source": "eslint",
      "line": 2,
      "rule_id": "jsx-a11y/alt-text",
      "file": null
    }
  ],
  "summary": "ESLint found 1 issue(s). The model's review was not available.",
  "judgement_available": false,
  "parse_error": null,
  "kind": "snippet",
  "notes": []
}
```

| Field | Meaning |
|---|---|
| `category` | `accessibility`, `security`, `test` or `style`. ESLint's `jsx-a11y/*` rules are accessibility; `no-eval`, `no-implied-eval`, `no-new-func`, `no-script-url`, `react/no-danger`, `react/jsx-no-script-url` and `react/jsx-no-target-blank` are security; its other rules are style. `test` comes only from the model |
| `severity` | `error` / `warning` for ESLint findings, `suggestion` for the model's |
| `source` | `eslint` or `model` |
| `line`, `rule_id` | May be `null` (the model's findings have no rule) |
| `judgement_available` | `false` when the model's reply could not be read as a review; the findings are then ESLint-only |
| `parse_error` | Set when the snippet is not valid code, or a diff changes no JS/TS file: no findings, and the model is not called |
| `kind` | `snippet` or `diff` |
| `file` | The changed file a finding is in (diffs only); `line` is then the line in the new version of that file |
| `notes` | What a diff review skipped, e.g. non-JS files, or a hunk ESLint couldn't parse on its own (left to the model) |

The review itself is not stored; one activity row (title, summary, finding count) is recorded for the dashboard.

## Dashboard

`GET /projects/{id}/stats` → `200`:

```json
{
  "questions_this_week": 12,
  "reviews_this_week": 3,
  "questions_total": 40,
  "reviews_total": 9,
  "documents_indexed": 5,
  "recent": [
    {
      "kind": "review",
      "source": "code_review_screen",
      "title": "Reviewed: export function Card({ src }) {",
      "detail": "ESLint found 1 issue(s).",
      "finding_count": 1,
      "created_at": "2026-09-25T10:12:00Z"
    }
  ]
}
```

"This week" is the last 7 days. `recent` holds the latest 10 events, newest first; `kind` is `question` or `review`,
`source` is `ask` (chat) or `code_review_screen`, and `finding_count` is set only for reviews from the Code review
screen.
