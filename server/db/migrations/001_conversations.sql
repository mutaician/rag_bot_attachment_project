-- Apply on existing Postgres volumes (init.sql only runs on first volume create).
-- docker compose exec postgres psql -U rag_user -d rag_db -f - < server/db/migrations/001_conversations.sql

CREATE TABLE IF NOT EXISTS conversations (
    id          UUID PRIMARY KEY,
    title       TEXT NOT NULL DEFAULT 'New conversation',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id               UUID PRIMARY KEY,
    conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             TEXT NOT NULL,
    content          TEXT NOT NULL,
    citations        JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS conversation_messages_conversation_idx
    ON conversation_messages (conversation_id, created_at);
