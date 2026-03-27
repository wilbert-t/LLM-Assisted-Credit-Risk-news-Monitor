# Database Schema & Environment

## Schema
```sql
articles(id, title, content, url, source, published_at, fetched_at, ticker)
obligors(id, name, ticker, lei, sector, country)
processed_articles(id, article_id, cleaned_text, entities JSONB,
                   sentiment_score FLOAT, sentiment_label, is_credit_relevant BOOL)
alerts(id, obligor_id, triggered_at, severity, summary, event_types JSONB,
       article_ids JSONB, metadata JSONB)
embeddings(id, article_id, chunk_text, embedding vector(1536), chunk_index)
obligor_daily_signals(id, obligor_id, date, neg_article_count,
                      avg_sentiment, credit_relevant_count)
```

## Environment Variables
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/credit_risk
NEWSAPI_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=credit_risk_embeddings
```