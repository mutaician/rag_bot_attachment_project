# Interactive Internal Knowledge Base (RAG Bot)

Monorepo: `server/` (FastAPI) + `client/` (React). Milestone 2 — upload, ingest, index in Postgres.

**Requires:** Docker, Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 20+, [pnpm](https://pnpm.io/), [Ollama](https://ollama.com/) with `embeddinggemma`

## Run

**Database:**

```bash
docker compose up -d
```

**Backend** (terminal 1 — API + indexing worker):

```bash
cd server && uv sync && uv run uvicorn app.main:app --reload --port 8000
```

**Frontend** (terminal 2):

```bash
cd client && pnpm install && pnpm dev
```

- App: http://localhost:5173 — upload PDF/md/txt, watch status go `pending` → `indexing` → `ready`
- API docs: http://localhost:8000/docs

## Verify (Milestone 2)

1. Open http://localhost:5173
2. Drag a PDF onto the upload zone
3. Status badge should become **ready** (Ollama must be running)
4. `docker compose exec postgres psql -U rag_user -d rag_db -c "SELECT COUNT(*) FROM document_chunks;"`
