# Session Log
# Keep only last 5 sessions.

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

