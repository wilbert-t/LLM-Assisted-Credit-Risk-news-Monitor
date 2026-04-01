-- Enable pgvector extension (requires pgvector/pgvector:pg15 image)
CREATE EXTENSION IF NOT EXISTS vector;

-- Embeddings table: stores one row per article chunk
CREATE TABLE IF NOT EXISTS embeddings (
    id          SERIAL PRIMARY KEY,
    article_id  INT REFERENCES articles(id) ON DELETE CASCADE,
    chunk_text  TEXT NOT NULL,
    embedding   vector(384) NOT NULL,
    chunk_index INT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_embeddings_article_id ON embeddings (article_id);

-- IVFFlat index for approximate cosine similarity search.
-- Only effective with 1000+ rows. Safe to create with fewer rows but won't speed things up.
CREATE INDEX IF NOT EXISTS ix_embeddings_ivfflat
    ON embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
