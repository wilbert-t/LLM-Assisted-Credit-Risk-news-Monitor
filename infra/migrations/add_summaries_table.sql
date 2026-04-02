-- Migration: Add summaries table for LLM-generated credit risk summaries
-- Purpose: Cache summaries by obligor/date/article_hash to minimize Groq API calls

CREATE TABLE IF NOT EXISTS summaries (
    id SERIAL PRIMARY KEY,
    obligor_id INT NOT NULL REFERENCES obligors(id) ON DELETE CASCADE,
    cache_date DATE NOT NULL,
    article_hash VARCHAR(64) NOT NULL,
    summary_json JSON NOT NULL,
    model_used VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_summaries_obligor_date_hash UNIQUE(obligor_id, cache_date, article_hash)
);

CREATE INDEX IF NOT EXISTS idx_summaries_obligor_date ON summaries(obligor_id, cache_date);
CREATE INDEX IF NOT EXISTS idx_summaries_created_at ON summaries(created_at);
