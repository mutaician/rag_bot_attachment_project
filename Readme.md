# Interactive Internal Knowledge Base (RAG Bot)

Monorepo: `server/` (FastAPI) + `client/` (React). Milestone 1 — mock API + frontend wired.

**Requires:** Python 3.12+, [uv](https://docs.astral.sh/uv/), Node 20+, [pnpm](https://pnpm.io/)

## Run

**Backend** (terminal 1):

```bash
cd server && uv sync && uv run uvicorn app.main:app --reload --port 8000
```

**Frontend** (terminal 2):

```bash
cd client && pnpm install && pnpm dev
```

- API: http://localhost:8000 (docs at `/docs`)
- App: http://localhost:5173

API URL is set in `client/.env` (`VITE_API_URL=http://localhost:8000`).

## Verify

Open http://localhost:5173 → devtools console → should log `Mock documents: (3) [...]`.
