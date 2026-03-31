# Session Log
# Keep only last 5 sessions.

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

