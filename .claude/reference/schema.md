# Database Schema & Environment

## Schema
```sql
articles(id, title, content, url, source, published_at, fetched_at,
         language, raw_json JSON)

obligors(id, name, ticker, lei, sector, country)

article_obligors(article_id FK→articles, obligor_id FK→obligors)  -- many-to-many

processed_articles(id, article_id FK→articles UNIQUE,
                   cleaned_text, entities JSON,
                   sentiment_score FLOAT, sentiment_label,
                   is_credit_relevant BOOL, event_types ARRAY(String))

alerts(id, obligor_id FK→obligors, triggered_at, severity,
       summary TEXT, event_types JSON, article_ids JSON, extra_data JSON)

obligor_daily_signals(id, obligor_id FK→obligors, date,
                      neg_article_count INT, avg_sentiment FLOAT,
                      credit_relevant_count INT)
```

Notes:
- `entities` format: `{"ORG": [{"text": "Apple Inc.", "start": 0, "end": 10}], ...}`
- `severity` values: low / medium / high / critical (see rules.md)
- `event_types` in processed_articles: PostgreSQL ARRAY(String); in alerts: JSON array
- All tables except `article_obligors` include `created_at` / `updated_at` auto-timestamps

## Environment Variables
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/credit_risk
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/credit_risk_test
NEWSAPI_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=credit_risk_embeddings
BATCH_SIZE=50
LOG_LEVEL=INFO
```
