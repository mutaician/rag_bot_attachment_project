# Implementation Plan — Internal Knowledge Base (RAG Agent)

## Goal

A local-first internal tool where anyone in an organization can upload, edit, and query organizational documents through an AI agent. Documents stay editable; any change triggers re-indexing. Conversations are persisted per user. Fully offline using open-source models via Ollama.

---

## Scope (v1)

**In**
- Multi-format ingestion: PDF (basic), Markdown (editable in-app), DOCX, HTML, 
- Multi-file upload; handle same name uploads by versioning, handle empty files 
- Agentic RAG: LLM agent decides when/how to query the knowledge base (not fixed retrieve-then-generate)
- Streaming chat, multi-turn conversations, per-user history
- Source citations on every grounded answer
- Document dashboard with indexing status
- Local deployment (laptop); models and vector DB run locally

**Out (v1)**
- Cloud LLM/embedding providers
- Production hosting / multi-machine deployment
- Auth beyond session-per-user
- API versioning
- Hybrid/BM25 search, rerankers, automated eval suites

---

## Architecture

```
┌─────────────┐     REST/SSE      ┌──────────────┐
│  React UI   │ ◄──────────────►  │   FastAPI    │
│  (Tailwind) │                   │   API        │
└─────────────┘                   └──────┬───────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
            ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
            │  Worker      │   │  Vector DB   │   │  SQLite/PG   │
            │  (ingestion) │   │  (local)     │   │  (metadata,  │
            └──────────────┘   └──────────────┘   │   sessions)  │
                    │                             └──────────────┘
                    ▼
            ┌──────────────┐
            │  Ollama      │
            │  embeddings  │
            │  + LLM       │
            └──────────────┘
```

| Layer | Choice |
|-------|--------|
| Repo | Monorepo (`server/` FastAPI, `client/` React) |
| API | REST + SSE streaming |
| Ingestion | Separate worker process (async jobs on upload/edit) |
| Embeddings | Ollama — `embeddinggemma` or `qwen3-embedding` |
| Generation | Ollama — `gemma3` or `qwen3.5` |
| Vector store | Local (e.g. Chroma) |
| Similarity | Cosine |
| Metadata DB | SQLite for local dev |

---

## API (core endpoints)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/documents/upload` | Multi-file upload (multipart) |
| `GET` | `/documents` | List documents + indexing status |
| `GET` | `/documents/{id}` | Document metadata |
| `PUT` | `/documents/{id}` | Edit Markdown content (triggers re-index) |
| `DELETE` | `/documents/{id}` | Remove document + vectors |
| `POST` | `/chat` | Multi-turn query; streams SSE response |
| `GET` | `/conversations` | User's conversation list |
| `GET` | `/conversations/{id}` | Conversation history |
| `DELETE` | `/conversations/{id}` | Clear a conversation |

**Chat response shape** (streamed): answer text (markdown) + citation objects `{ document_id, filename, chunk_text, page? }`.

**Agent behavior**: system prompt includes inventory of available documents. Agent uses a `search_documents` tool to retrieve chunks on demand rather than blind top-K on every message. Strict grounding — cite sources; if context is insufficient, respond helpfully (e.g. *"I don't have enough context for that, but I can help with questions about X"*).

---

## Document pipeline

1. **Upload** → store raw file → enqueue indexing job
2. **Worker** → extract text (PDF basic, DOCX, HTML, OCR for images) → chunk (fixed-size + overlap, tunable) → embed via Ollama → upsert to vector DB
3. **Edit (MD only in v1)** → save → delete old vectors → re-index
4. **Override** → same filename replaces prior document record and vectors

Chunking defaults: ~500 tokens, ~50-token overlap. Adjust based on manual testing.

---

## Frontend

- **Stack**: React + Tailwind CSS, multipage (Dashboard, Chat, Document Editor)
- **Dashboard**: drag-and-drop multi-upload, status badges (pending / indexing / ready / failed)
- **Chat**: message bubbles, markdown rendering, streaming tokens, collapsible citation cards beneath AI replies
- **Editor**: in-browser Markdown edit for `.md` documents
- **UX**: dark mode, premium feel — clean typography, subtle borders/shadows; no gradients, no generic card grids
- **State**: TanStack Query for API calls; conversation history persisted server-side per user session

---

## Constraints

- **Offline-only models** — no external API calls for embeddings or generation
- **Local-first** — single-machine Docker Compose or bare-metal; hosting deferred
- **Hardware-dependent** — model choice (gemma vs qwen families)
- **Basic PDF** — text extraction only; no advanced layout/table handling in v1
- **Manual eval** — no automated retrieval benchmarks; test with real org-style docs
- **Monorepo, feature branches, PRs** — per project brief

---

## Milestones (aligned to brief)

| # | Target | Deliverable |
|---|--------|-------------|
| 1 | Wk 1–2 | API contract + mock endpoints; React scaffold; frontend hits backend |
| 2 | Wk 3–4 | Worker ingestion pipeline; upload UI; real file indexed in vector DB |
| 3 | Wk 5–6 | Agentic chat with streaming, citations, multi-turn history |
| 4 | Wk 7–8 | Edge-case prompts, error handling, UI polish, docs, demo prep |

---

## Future steps

- Production hosting (Docker, reverse proxy, process supervision)
- Full auth (SSO / role-based upload vs read-only)
- Additional formats and richer PDF parsing
- Hybrid search (BM25 + vectors) and reranking
- Click citation → jump to source in document viewer
- Automated retrieval eval dataset
- Incremental re-indexing (diff-based, not full rebuild)
