ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS started_by_user_id UUID REFERENCES users(id);

ALTER TABLE conversation_messages
    ADD COLUMN IF NOT EXISTS author_user_id UUID REFERENCES users(id);
