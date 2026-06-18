-- Runs once when Postgres first creates the data volume (docker compose up on empty volume).
-- Mounted from docker-compose.yml → /docker-entrypoint-initdb.d/

-- pgvector: stores embedding vectors for semantic search (Milestone 2+)
CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- documents: one row per uploaded file version (metadata + indexing status)
-- ---------------------------------------------------------------------------
CREATE TABLE documents (
    id            UUID PRIMARY KEY,
    filename      TEXT NOT NULL,
    version       INT NOT NULL,                    -- 1, 2, 3… per filename
    status        TEXT NOT NULL,                   -- pending | indexing | ready | failed
    storage_path  TEXT NOT NULL,                   -- path to raw file on disk
    error_message TEXT,                            -- set when status = failed
    deleted_at    TIMESTAMPTZ,                     -- soft delete: non-null = hidden
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (filename, version)
);

-- ---------------------------------------------------------------------------
-- document_chunks: text segments + embedding + keyword index (hybrid-ready M3)
-- ---------------------------------------------------------------------------
CREATE TABLE document_chunks (
    id            UUID PRIMARY KEY,
    document_id   UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version       INT NOT NULL,
    chunk_index   INT NOT NULL,                    -- order within the document
    chunk_text    TEXT NOT NULL,
    page          INT,                             -- PDF page number, if known
    -- 768 dims for embeddinggemma — verify after first embed if inserts fail
    embedding     vector(768),
    search_vector TSVECTOR,                        -- filled on insert for keyword search leg
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW index: fast approximate nearest-neighbor search on embeddings (cosine distance)
CREATE INDEX document_chunks_embedding_idx
    ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- GIN index: fast full-text / keyword search on search_vector
CREATE INDEX document_chunks_search_idx
    ON document_chunks USING gin (search_vector);

-- ---------------------------------------------------------------------------
-- indexing_jobs: worker polls rows with status = 'pending'
-- ---------------------------------------------------------------------------
CREATE TABLE indexing_jobs (
    id            UUID PRIMARY KEY,
    document_id   UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status        TEXT NOT NULL,                   -- pending | processing | done | failed
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX indexing_jobs_pending_idx
    ON indexing_jobs (status)
    WHERE status = 'pending';

-- ---------------------------------------------------------------------------
-- conversations + messages (Milestone 3 chat history)
-- ---------------------------------------------------------------------------
CREATE TABLE conversations (
    id          UUID PRIMARY KEY,
    title       TEXT NOT NULL DEFAULT 'New conversation',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE conversation_messages (
    id               UUID PRIMARY KEY,
    conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             TEXT NOT NULL,   -- user | assistant
    content          TEXT NOT NULL,
    citations        JSONB,           -- assistant messages only
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX conversation_messages_conversation_idx
    ON conversation_messages (conversation_id, created_at);
