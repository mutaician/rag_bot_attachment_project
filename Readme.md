# Interactive Internal Knowledge Base (RAG Bot)

Monorepo: `server/` (FastAPI) + `client/` (React). Upload, ingest, hybrid search, and agentic chat with team auth.

**Requires:** Docker, Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 20+, [pnpm](https://pnpm.io/), [Ollama](https://ollama.com/) with `embeddinggemma` (+ `gemma4` for local chat)

## Local development

**Database:**

```bash
docker compose up -d
```

If the Postgres volume already existed before auth, apply migrations:

```bash
docker compose exec -T postgres psql -U rag_user -d rag_db < server/db/migrations/002_users_sessions.sql
docker compose exec -T postgres psql -U rag_user -d rag_db < server/db/migrations/003_chat_attribution.sql
docker compose exec -T postgres psql -U rag_user -d rag_db < server/db/migrations/004_p0_security.sql
```

**Create a user** (no public registration):

```bash
cd server && uv run python -m app.cli create-user --username admin --display-name "Admin" --password 'your-password'
```

**Backend** (terminal 1):

```bash
cd server && uv sync && uv run uvicorn app.main:app --reload --port 8000
```

**Frontend** (terminal 2):

```bash
cd client && pnpm install && pnpm dev
```

- App: http://localhost:5173 — sign in, upload PDF/md/txt, ask questions
- API docs: http://localhost:8000/docs

**Preflight** (DB + Ollama embeddings):

```bash
cd server && uv run python -m app.cli preflight
```

## Docker full stack

Runs Postgres, Ollama, API, and nginx web UI on port 8080:

```bash
docker compose --profile full up -d --build
```

Pull models inside the Ollama container:

```bash
docker compose exec ollama ollama pull embeddinggemma
docker compose exec ollama ollama pull gemma4
```

Create the first user against the API container:

```bash
docker compose exec api uv run python -m app.cli create-user --username admin --display-name "Admin" --password 'your-password'
```

Open http://localhost:8080

## Environment (server/.env)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection string |
| `OLLAMA_BASE_URL` | Local Ollama for embeddings + local chat |
| `OLLAMA_EMBED_MODEL` | Embedding model (default `embeddinggemma:latest`) |
| `OLLAMA_LLM_MODE` | Startup chat mode: `local` or `cloud` |
| `OLLAMA_LOCAL_CHAT_MODEL` | Local chat model (e.g. `gemma4`) |
| `OLLAMA_CLOUD_CHAT_MODEL` | Cloud chat model (e.g. `gemma4:31b`) |
| `OLLAMA_CLOUD_API_KEY` | Required for cloud chat |
| `SESSION_SECRET` | Session cookie signing (change in production) |
| `COOKIE_SECURE` | `true` when serving over HTTPS |
| `CORS_ORIGINS` | Comma-separated dev origins (default `http://localhost:5173`) |
| `MAX_UPLOAD_BYTES` | Max upload size in bytes (default 25 MB) |
| `MAX_PDF_PAGES` | Max PDF pages to parse (default 200) |
| `LOGIN_MAX_ATTEMPTS` | Failed logins before lockout (default 5) |
| `LOGIN_RATE_WINDOW_SECONDS` | Rate limit window in seconds (default 300) |

Chat LLM mode can be switched at runtime by any signed-in user via **Ask → Chat model (team)** — one setting per deployment.

**Authorization model:** Documents and team threads are shared library-wide. Private threads are visible only to their starter. Only the uploader may delete a document; only the thread starter may delete a conversation.

Run security regression tests:

```bash
cd server && uv run pytest tests/ -v
```

## Verify

1. Sign in at http://localhost:5173
2. Upload a PDF on Library — status should reach **ready**
3. Ask a question on Ask — answers cite library passages
4. Unauthenticated API calls return **401**
