# Session Log
# Keep only last 5 sessions.

---

## Session 12 — 2026-04-02 (Week 5 Complete)

### Completed
- **Phase 5: LLM Summarization & Alerts** — full system merged to `main`, 246 tests passing (from 189)
  
  **Database:**
  - `infra/migrations/add_summaries_table.sql` — cache table (obligor_id, cache_date, article_hash) for LLM summaries
  - `src/db/models.py` — `Summaries` ORM model with TimestampMixin, unique constraint, indices
  
  **Summarizer (Groq API):**
  - `src/rag/summarizer.py` — `ObligorSummarizer` class with `summarize_obligor_risk(obligor_id, days=7)`
  - `has_new_articles_since()` — checks for new articles since last summary for cache invalidation
  - `call_groq_with_backoff()` — Groq API caller with intelligent retry (primary model, fallback on 429, exponential backoff)
  - Cache strategy: keyed by (obligor_id, cache_date, article_hash), TTL 230-350min per tier, invalidates on new articles
  - Response: `{company, summary, key_events, risk_level, concerns, positive_factors, confidence, model_used, cached}`
  - **9 unit tests** covering caching, fallback, Groq retries, empty results
  
  **Alert Rules Engine:**
  - `src/alerts/rules.py` — `AlertEngine` with 5 rule implementations
    1. Rule 1 (CRITICAL): Credit Event — fires on default/bankruptcy/fraud
    2. Rule 2 (HIGH): Covenant/Liquidity — fires on covenant_breach or liquidity_crisis
    3. Rule 3 (MEDIUM): Downgrade/Rating Watch — fires on downgrade or rating_watch
    4. Rule 4 (MEDIUM): Negative Sentiment Spike — fires when sentiment < -0.5 AND credit_relevant_count ≥ 3
    5. Rule 5 (HIGH): Multiple Events — fires when 2+ alerts triggered in past 48h
  - `AlertRule` class with evaluation + error handling
  - **12 unit tests** covering all rules, negative cases, no false positives
  
  **Alert Generator:**
  - `src/alerts/generator.py` — `generate_alerts(obligor_id)` orchestrates full flow
    - Fetch daily signals → check cache + new articles → get summary (fallback if Groq fails) → evaluate rules → create alerts
    - `check_all_obligors()` — batch processor with per-obligor error isolation
    - Deduplication: 24h window per rule, prevents alert spam
    - Fallback mode: creates rule-based alerts even if summarizer fails, marked with `fallback=True` flag
  - **8 unit tests** covering alert creation, dedup, fallback, early returns, batch processing
  
  **Scheduler (APScheduler):**
  - `src/alerts/scheduler.py` — `ScheduledAlertJob` class with two-tier alert cycles
    - `get_prioritized_obligors()` — assigns HIGH/NORMAL tiers based on 7-day alerts (≥2) or sentiment (<-0.4)
    - Job 1: `high_risk_alert_cycle()` — every 4 hours for HIGH tier
    - Job 2: `normal_alert_cycle()` — every 6 hours for NORMAL tier
    - Rate limit budget check: logs estimated calls vs remaining daily (1000/day limit)
    - Inter-call sleep: 15s between Groq calls to throttle rate limiting
    - Per-obligor error isolation: continues on individual failures
  - **10 unit tests** covering tier assignment, cycle execution, scheduling, sleep behavior, errors
  - `apscheduler>=3.10.0` added to requirements.txt
  
  **FastAPI Endpoints:**
  - `src/api/alerts.py` — REST API with 3 endpoints
    1. `GET /api/alerts` — list alerts with filters (severity, date_from, date_to, obligor_id), pagination
    2. `GET /api/alerts/{id}` — single alert details with source articles
    3. `GET /api/obligors/{id}/summary` — latest risk summary (generates or uses cached)
  - Pydantic models: `AlertResponse`, `AlertListResponse`, `SummaryResponse`
  - **10 unit tests** covering filtering, pagination, 404s, response schema validation
  
  **Integration Tests:**
  - `tests/integration/test_alerts_e2e.py` — 8 end-to-end tests
    - Full flow: articles → signals → summary → alert creation
    - Deduplication across multiple runs
    - Prioritized obligor tier assignment
    - Scheduler lifecycle
    - Both cycle execution
    - Alert field population
    - Summarizer fallback
    - Multi-obligor independence
  
  **Summary of Changes:**
  - 8 new modules (summarizer, rules, generator, scheduler, API + 3 test files)
  - 8 major git commits (one per task, TDD strict)
  - 57 new unit + integration tests
  - Constants file updated with 41 new definitions (Groq models, rule names, thresholds, scheduler timing)
  - Full test suite: **246 tests, all passing** (57 new from Week 5)
  - Database: `summaries` table operational, migration runner integrated
  - All Groq models configured (primary + fallback with retry logic)

### Blockers / Open Questions
- None — full Phase 5 delivered

### Next Steps
- Phase 6: Dashboard (Streamlit + Plotly)
  - Portfolio overview page: KPI cards, risk heatmap, 7-day trend
  - Alert feed: real-time, color-coded by severity
  - Company drill-down: sentiment chart, summary, events, alerts
  - Integration with FastAPI endpoints

---

## Session 11 — 2026-04-01 (Week 4 Complete)

### Completed
- **Phase 4: RAG System** — full pipeline merged to `main`, 189 tests passing
  - `docker-compose.yml` — swapped to `pgvector/pgvector:pg15`
  - `src/db/models.py` — `Embedding` ORM model with `Vector(384)`, `UniqueConstraint(article_id, chunk_index)`, IVFFlat index
  - `src/db/connection.py` + `tests/conftest.py` — enable vector extension before `create_all`
  - `infra/migrations/add_pgvector.sql` — reference migration
  - `src/models/embeddings.py` — `EmbeddingGenerator` (all-MiniLM-L6-v2, 384-dim, lazy-loaded)
  - `src/models/chunker.py` — `chunk_text(text, chunk_size=300, overlap=50) -> List[str]`
  - `src/models/embedding_pipeline.py` — `embed_and_store_articles(article_ids, db)` with dedup guard
  - `scripts/generate_embeddings.py` — CLI runner with `--limit`, idempotent
  - `src/rag/retriever.py` — `ArticleRetriever`: cosine search + obligor/date filter, IVFFlat probes fix
  - `notebooks/week4_rag_demo.ipynb` — 3-cell demo
  - **1,196 article chunks embedded** in `embeddings` table
  - Retriever smoke test: returns results with similarity ~0.58 for "bankruptcy liquidity crisis"

### Blockers / Open Questions
- Summarizer (LLM-synthesized credit risk summary from retrieved chunks) deferred to Week 5
- IVFFlat `lists=100` is oversized for current 1,196-row dataset; fine until production scale

### Next Step
- Phase 5: Alerts + Summarizer
  - LLM summarizer: prompt Claude/GPT-4 with top-K retrieved chunks → credit risk narrative
  - Alert rules: threshold on risk_score + sentiment triggers alert creation
  - FastAPI endpoints: GET /alerts, GET /obligors/{id}/summary
  - Scheduled job: nightly batch (score → embed → summarize → alert)

---

## Session 10 — 2026-03-31

### Completed
- **Task 5 [Optional]: LLM Classifier via Groq API**
  - `src/models/llm_classifier.py` — TDD implementation with graceful fallback
    - `classify_with_llm(text: str) -> Dict` — calls Groq API, returns `{"is_credit_relevant": bool, "event_types": List[str], "error": str|None}`
    - System prompt instructs classifier to return credit-relevant JSON with 15 event types (bankruptcy, downgrade, fraud, etc.)
    - Graceful error handling: API timeout, malformed JSON, missing API key → all return fallback with error message
    - No real API calls needed; all logic is robust
  - `tests/unit/test_llm_classifier.py` — 5 unit tests, all passing
    - Coverage: credit-relevant true/false, multiple event types, API error, malformed JSON
    - All tests mock `requests.post` at module level (important for patch path)
  - Full suite: **167 tests (162 + 5 new), all passing**
  - Commit: `42b8a7a`

### Blockers / Open Questions
- None

### Next Step
- Task 4: Week 3 integration tests (in progress)
  - Optional: Add end-to-end test for LLM classifier in the pipeline
  - Phase 4: RAG — chunk, embed, Qdrant, retriever + summarizer

---

## Session 9 — 2026-03-31

### Completed
- **Task 1: Risk Scorer Module**
  - `src/models/risk_scorer.py` — deterministic scorer for articles + obligors
    - `score_article_risk(article_dict) -> float [0.0, 1.0]`
    - Base: +0.5 if credit_relevant, +0.3 if sentiment < 0, +bonuses per event type
    - Event bonuses in `_EVENT_BONUSES`: default=0.30, bankruptcy=0.20, downgrade=0.20, fraud=0.15, etc. (15 types total)
    - Clamped to [0.0, 1.0]
  - `aggregate_obligor_risk(obligor_id, days, db=None)` — computes mean score for obligor over N days
  - `tests/unit/test_risk_scorer.py` — 11 unit tests, all passing
    - Covers: high/low risk articles, individual bonuses, stacking, None handling, bounds
  - Full suite: 153 tests (142 + 11 new), all passing

### Blockers / Open Questions
- None

### Next Step
- Task 2: Add `risk_score` column to DB schema
  - `src/db/models.py` — add `risk_score FLOAT` to `ProcessedArticle` table
  - Migration + seed script (populate with `score_article_risk()`)
  - Update pipeline to populate new column on each article
  - Tests

---

## Session 8 — 2026-03-31

### Completed
- **Day 15-16: FinBERT Sentiment Module**
  - `src/models/sentiment.py` — `FinBERTSentiment` class with lazy loading, `predict()` + `predict_batch()`
  - Model: `ProsusAI/finbert`, labels: positive/negative/neutral, score = positive_prob − negative_prob (−1.0 to 1.0)
  - GPU auto-detect, CPU fallback; model cached by HuggingFace after first download
  - `tests/unit/test_sentiment.py` — 10 mocked tests, all passing
- **Day 17: Credit-Relevance Classifier**
  - `src/models/classifier.py` — `is_credit_relevant(text) -> bool` + `classify_events(text) -> List[str]`
  - Pure keyword matching against `KEYWORDS` dict in `src/utils/constants.py` (15 event types)
  - `tests/unit/test_classifier.py` — 18 tests, all passing
  - `src/processors/pipeline.py` — updated to call classifier inline; populates `is_credit_relevant` + `event_types` on new articles
  - `scripts/score_sentiment.py` — batch scorer with `--batch-size` / `--limit` args
  - `requirements.txt` — added `transformers==4.40.0`, `torch==2.3.0`
- **Full suite: 142 tests, all passing**
- **Smoke tests on real data:**
  - Classifier: `is_credit_relevant` + `event_types` populated on pipeline-processed articles (e.g. `{bankruptcy, liquidity_crisis}`)
  - FinBERT: 10 articles scored; labels neutral/negative; scores in range −0.964 to +0.448

### Blockers / Open Questions
- None

### Next Step
- Score all remaining ~1,189 processed articles with FinBERT:
  `python -m scripts.score_sentiment --batch-size 50` (will take ~20 min on CPU)
- Rerun `aggregate_all_daily()` after sentiment is populated to get real `avg_sentiment` in `obligor_daily_signals`:
  `python -m scripts.aggregate_signals`
- Phase 4: RAG — chunk, embed, Qdrant, retriever + summarizer

---

## Session 7 — 2026-03-30

### Completed
- **Day 13a: Signal Aggregator**
  - `src/processors/signal_aggregator.py` — `aggregate_daily_signals(obligor_id, date, db=None)` + `aggregate_all_daily(db=None)`
  - ON CONFLICT DO UPDATE on `uq_obligor_daily_signals_obligor_date`
  - `neg_article_count` = total article count (placeholder until FinBERT)
  - `avg_sentiment` = NULL until sentiment_score populated
  - `scripts/aggregate_signals.py` — standalone runner
  - `tests/unit/test_signal_aggregator.py` — 9 tests, all passing
- **Day 13b: EDA Notebook**
  - `notebooks/week2_eda.ipynb` — 5 cells (load data, stats, obligor coverage, entity quality, timeline chart)
- **Day 14: Week 2 wrap**
  - `docs/DAILY_STANDUP_LOG.md` — Week 2 standups appended (Days 8–13 + summary)
- **Dependencies**: `jupyter==1.0.0`, `matplotlib==3.8.2` added to `requirements.txt`
- **Full suite: 114 tests, all passing**
- **Smoke test on real data:**
  - 52 (obligor, date) pairs upserted into `obligor_daily_signals`
  - Top: Apple Inc. 4 articles on 2026-03-27; Walt Disney 4 on 2026-03-26

### Blockers / Open Questions
- None

### Next Step
- Phase 3: FinBERT sentiment scoring (Day 15 per STARTUP_PLAN)
  - `pip install transformers torch` (CPU)
  - `src/processors/sentiment.py` — `score_sentiment(text) -> (label, score)`
    - Model: `ProsusAI/finbert`, labels: positive/negative/neutral, score: -1.0 to 1.0
  - Update `pipeline.py`: populate `sentiment_label` + `sentiment_score` per article
  - Rerun `aggregate_all_daily()` with real sentiment values

### Also discussed
- Week 8 backtesting: user considering OpenBB integration in `src/models/ground_truth.py`
  - OpenBB `obb.equity.price.historical()` via yfinance provider (no API key)
  - Rolling 30-day max → flag crash if drop > 20%, deduplicate to worst day per month
  - Pending: explore existing file before planning

---

## Session 6 — 2026-03-30

### Completed
- **Day 10: Entity Mapper**
  - `src/processors/entity_mapper.py` — `match_entity_to_obligor()` (exact ticker → exact name → rapidfuzz token_set_ratio ≥80%) + `map_articles_to_obligors()` (bulk upsert, in-memory dedup)
  - `scripts/map_entities.py` — standalone runner
  - `tests/unit/test_entity_mapper.py` — 16 tests passing
- **Day 11: Language Filter**
  - `src/processors/language_filter.py` — `detect_language()` + `filter_english_articles()`
  - `pipeline.py` updated — language guard (checks `article.language` first, fallback langdetect), new `skipped_language` counter
  - `tests/unit/test_language_filter.py` — 13 tests passing
- **Day 12: Integration Tests + Scripts**
  - `tests/integration/test_processing_pipeline.py` — 10 tests (single article, batch of 20, robustness, e2e with entity mapping)
  - `scripts/process_all_articles.py` — full pipeline runner
  - `tests/factories.py` — updated entity format to dict (text/start/end)
  - `requirements.txt` — added rapidfuzz 3.9.3, langdetect 1.0.9
- **Full suite: 105 tests, all passing**
- **Smoke test on real data:**
  - 1,189 of 2,253 articles processed (1,064 skipped — too short after cleaning)
  - 88 article-obligor links created in `article_obligors`
  - 1,194 total rows in `processed_articles`

### Blockers / Open Questions
- None

### Next Step
- Phase 3: FinBERT sentiment scoring (Day 13 per STARTUP_PLAN)
  - Install `transformers` + `torch` (CPU)
  - Create `src/processors/sentiment.py` — `score_sentiment(text) -> (label, score)`
    - Model: `ProsusAI/finbert`, labels: positive/negative/neutral, score: -1.0 to 1.0
  - Update `pipeline.py`: populate `sentiment_label` + `sentiment_score` per article
  - Update `obligor_daily_signals` aggregation after sentiment

---

## Session 5 — 2026-03-30

### Completed
- **Day 8: Text cleaning pipeline**
  - `src/processors/cleaner.py` — `clean_html()`, `normalize_text()`, `clean_article()`
  - `src/processors/pipeline.py` — `process_articles_batch()` with LEFT JOIN filter, bulk upsert, error skip
  - `tests/unit/test_cleaner.py` — 24 tests, all passing
- **Day 9: NER Extractor**
  - `src/processors/ner_extractor.py` — `extract_entities()` + `extract_companies_from_article()`
    - Lazy-loads `en_core_web_sm` once; returns `{"ORG": [{"text", "start", "end"}], ...}`
  - `src/processors/pipeline.py` — replaced placeholder with real `extract_entities()` call
  - `tests/unit/test_ner_extractor.py` — 18 tests, all passing
  - `requirements.txt` — spaCy 3.8.4, en-core-web-sm 3.8.0, pydantic 2.10.6, pydantic-settings 2.7.0
  - Full suite: **66 tests, all passing**
  - Smoke test: real entities in DB e.g. `{"ORG": [{"text": "Apple", "start": 50, "end": 55}], "DATE": [...]}`

### Blockers / Open Questions
- None

### Next Step
- Day 10: FinBERT sentiment scoring
  - Create `src/processors/sentiment.py` — `score_sentiment(text) -> (label, score)`
    - Model: `ProsusAI/finbert` from HuggingFace
    - Returns label ("positive"/"negative"/"neutral") + float score (-1.0 to 1.0)
  - Update `pipeline.py`: call `score_sentiment()`, populate `sentiment_label` + `sentiment_score`
  - Add `tests/unit/test_sentiment.py`

