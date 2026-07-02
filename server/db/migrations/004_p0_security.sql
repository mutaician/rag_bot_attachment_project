-- P0 security: conversation visibility + document ownership

ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS visibility TEXT NOT NULL DEFAULT 'team'
        CHECK (visibility IN ('team', 'private'));

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS uploaded_by_user_id UUID REFERENCES users(id);

CREATE INDEX IF NOT EXISTS conversations_visibility_idx
    ON conversations (visibility);

CREATE INDEX IF NOT EXISTS documents_uploaded_by_idx
    ON documents (uploaded_by_user_id);
