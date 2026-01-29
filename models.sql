CREATE TABLE IF NOT EXISTS pastes (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    expires_at BIGINT,
    max_views INTEGER,
    view_count INTEGER DEFAULT 0
);
